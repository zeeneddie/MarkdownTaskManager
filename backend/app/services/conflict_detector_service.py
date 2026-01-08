# backend/app/services/conflict_detector_service.py
"""
Conflict Detector Service - Detects conflicts between Static Analysis and LLM results.

Part of Fase 15b: Pipeline Integration (Week 99-102)

Conflict Detection Rules:
1. Confidence Threshold: LLM confidence < 72.5% overrules static → Human Review
2. Explicit Disagreement: Static & LLM disagree on classification → Human Review
3. Classification Change: Item type changes (Epic→Feature) → Human Review
4. Item Removal: LLM wants to remove static-detected item → Human Review
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts between Static and LLM analysis."""
    CONFIDENCE_THRESHOLD = "confidence_threshold"  # LLM confidence < 72.5%
    EXPLICIT_DISAGREEMENT = "explicit_disagreement"  # Static & LLM disagree
    CLASSIFICATION_CHANGE = "classification_change"  # Type changed
    ITEM_REMOVAL = "item_removal"  # LLM removes static item
    PRIORITY_MISMATCH = "priority_mismatch"  # Different priorities
    SCOPE_EXPANSION = "scope_expansion"  # LLM significantly expands scope
    SCOPE_REDUCTION = "scope_reduction"  # LLM significantly reduces scope


class ConflictSeverity(Enum):
    """Severity level of conflicts."""
    LOW = "low"  # Auto-resolvable
    MEDIUM = "medium"  # Needs review but not blocking
    HIGH = "high"  # Blocking, requires human decision
    CRITICAL = "critical"  # Data integrity issue


class ConflictResolution(Enum):
    """How a conflict was resolved."""
    PENDING = "pending"
    AUTO_ACCEPTED_STATIC = "auto_accepted_static"
    AUTO_ACCEPTED_LLM = "auto_accepted_llm"
    HUMAN_SELECTED_STATIC = "human_selected_static"
    HUMAN_SELECTED_LLM = "human_selected_llm"
    HUMAN_MERGED = "human_merged"
    HUMAN_REJECTED_BOTH = "human_rejected_both"


@dataclass
class ConflictItem:
    """Represents a detected conflict between static and LLM analysis."""
    id: str
    session_id: str
    item_id: str  # Reference to extraction item
    conflict_type: ConflictType
    severity: ConflictSeverity

    # Static analysis data
    static_classification: Optional[str] = None
    static_confidence: float = 0.0
    static_data: Dict = field(default_factory=dict)

    # LLM analysis data
    llm_classification: Optional[str] = None
    llm_confidence: float = 0.0
    llm_data: Dict = field(default_factory=dict)
    llm_provider: Optional[str] = None

    # Conflict details
    description: str = ""
    impact_assessment: str = ""
    recommendations: List[str] = field(default_factory=list)

    # Resolution
    resolution: ConflictResolution = ConflictResolution.PENDING
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None  # "system" or user_id
    resolution_notes: str = ""
    final_value: Optional[Dict] = None

    created_at: datetime = field(default_factory=lambda: datetime.utcnow())


@dataclass
class ConflictDetectionResult:
    """Result of conflict detection for a session."""
    session_id: str
    total_items_analyzed: int
    conflicts_found: int
    conflicts_by_type: Dict[str, int]
    conflicts_by_severity: Dict[str, int]
    conflicts: List[ConflictItem]
    auto_resolved: int
    needs_human_review: int
    detection_time_ms: float


class ConflictDetectorService:
    """
    Detects and manages conflicts between Static Analysis (Cycle 0) and LLM results.

    Key threshold: 72.5% confidence
    - Below threshold: LLM result needs human review
    - Static analysis provides baseline for comparison
    """

    # Core threshold for triggering human review
    CONFIDENCE_THRESHOLD = 0.725  # 72.5%

    # Thresholds for other conflict types
    AGREEMENT_THRESHOLD = 0.80  # 80% agreement needed to auto-accept
    SCOPE_CHANGE_THRESHOLD = 0.30  # 30% change triggers review

    def __init__(self, db_session=None):
        """
        Initialize conflict detector.

        Args:
            db_session: Optional database session for persisting conflicts
        """
        self.db = db_session

    async def detect_conflicts(
        self,
        session_id: str,
        static_results: Dict[str, Any],
        llm_results: List[Dict[str, Any]]
    ) -> ConflictDetectionResult:
        """
        Detect conflicts between static analysis and LLM extraction results.

        Args:
            session_id: Extraction session ID
            static_results: Results from StaticAnalysisOrchestrator
            llm_results: Results from LLM extraction cycles

        Returns:
            ConflictDetectionResult with all detected conflicts
        """
        start_time = datetime.utcnow()
        conflicts = []

        # Index LLM results by item
        llm_by_item = self._index_llm_results(llm_results)

        # Get static items
        static_items = self._extract_static_items(static_results)

        logger.info(f"Detecting conflicts for session {session_id}")
        logger.info(f"Static items: {len(static_items)}, LLM items: {len(llm_by_item)}")

        # Check each static item against LLM results
        for item_id, static_item in static_items.items():
            llm_item = llm_by_item.get(item_id)

            if llm_item is None:
                # Item removal conflict
                conflict = self._create_removal_conflict(
                    session_id, item_id, static_item
                )
                conflicts.append(conflict)
            else:
                # Check for other conflict types
                item_conflicts = self._check_item_conflicts(
                    session_id, item_id, static_item, llm_item
                )
                conflicts.extend(item_conflicts)

        # Check for new items added by LLM (not in static)
        for item_id, llm_item in llm_by_item.items():
            if item_id not in static_items:
                if llm_item.get("confidence", 1.0) < self.CONFIDENCE_THRESHOLD:
                    # New item with low confidence
                    conflict = self._create_low_confidence_conflict(
                        session_id, item_id, llm_item
                    )
                    conflicts.append(conflict)

        # Calculate summary
        detection_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        conflicts_by_type = self._count_by_type(conflicts)
        conflicts_by_severity = self._count_by_severity(conflicts)

        # Auto-resolve where possible
        auto_resolved = await self._auto_resolve(conflicts)

        needs_human_review = sum(
            1 for c in conflicts
            if c.resolution == ConflictResolution.PENDING
        )

        result = ConflictDetectionResult(
            session_id=session_id,
            total_items_analyzed=len(static_items) + len(llm_by_item),
            conflicts_found=len(conflicts),
            conflicts_by_type=conflicts_by_type,
            conflicts_by_severity=conflicts_by_severity,
            conflicts=conflicts,
            auto_resolved=auto_resolved,
            needs_human_review=needs_human_review,
            detection_time_ms=detection_time
        )

        logger.info(f"Detected {len(conflicts)} conflicts, {auto_resolved} auto-resolved")

        return result

    def _index_llm_results(self, llm_results: List[Dict]) -> Dict[str, Dict]:
        """Index LLM results by item ID for quick lookup."""
        indexed = {}
        for result in llm_results:
            items = result.get("items", [])
            for item in items:
                item_id = item.get("id") or item.get("source_id")
                if item_id:
                    # Keep highest confidence version
                    if item_id not in indexed or item.get("confidence", 0) > indexed[item_id].get("confidence", 0):
                        indexed[item_id] = {
                            **item,
                            "provider": result.get("provider")
                        }
        return indexed

    def _extract_static_items(self, static_results: Dict) -> Dict[str, Dict]:
        """Extract items from static analysis results."""
        items = {}

        # Business rules
        for rule in static_results.get("business_rules", []):
            items[rule.get("id")] = {
                "id": rule.get("id"),
                "type": "business_rule",
                "classification": rule.get("type"),
                "confidence": rule.get("confidence", 0.8),
                "data": rule
            }

        # NFR detections
        for nfr in static_results.get("nfr_detections", []):
            items[nfr.get("id")] = {
                "id": nfr.get("id"),
                "type": "nfr",
                "classification": nfr.get("category"),
                "confidence": nfr.get("confidence", 0.8),
                "data": nfr
            }

        # Compliance violations
        for violation in static_results.get("compliance_violations", []):
            v_id = f"compliance_{violation.get('requirement_id')}"
            items[v_id] = {
                "id": v_id,
                "type": "compliance",
                "classification": violation.get("framework"),
                "confidence": 0.9,  # High confidence for compliance
                "data": violation
            }

        # High confidence findings
        for finding in static_results.get("high_confidence_findings", []):
            items[finding.get("id")] = {
                "id": finding.get("id"),
                "type": finding.get("type", "finding"),
                "classification": finding.get("classification"),
                "confidence": finding.get("confidence", 0.8),
                "data": finding
            }

        return items

    def _check_item_conflicts(
        self,
        session_id: str,
        item_id: str,
        static_item: Dict,
        llm_item: Dict
    ) -> List[ConflictItem]:
        """Check for conflicts between static and LLM versions of an item."""
        conflicts = []

        # 1. Confidence threshold check
        llm_confidence = llm_item.get("confidence", 0.5)
        if llm_confidence < self.CONFIDENCE_THRESHOLD:
            conflicts.append(ConflictItem(
                id=str(uuid4()),
                session_id=session_id,
                item_id=item_id,
                conflict_type=ConflictType.CONFIDENCE_THRESHOLD,
                severity=ConflictSeverity.HIGH,
                static_classification=static_item.get("classification"),
                static_confidence=static_item.get("confidence", 0.8),
                static_data=static_item.get("data", {}),
                llm_classification=llm_item.get("classification"),
                llm_confidence=llm_confidence,
                llm_data=llm_item,
                llm_provider=llm_item.get("provider"),
                description=f"LLM confidence ({llm_confidence:.1%}) below threshold ({self.CONFIDENCE_THRESHOLD:.1%})",
                impact_assessment="LLM result may override static analysis incorrectly",
                recommendations=[
                    "Review both static and LLM analysis",
                    "Consider additional LLM validation",
                    "Check source code context"
                ]
            ))

        # 2. Classification change check
        static_class = static_item.get("classification")
        llm_class = llm_item.get("classification")
        if static_class and llm_class and static_class != llm_class:
            conflicts.append(ConflictItem(
                id=str(uuid4()),
                session_id=session_id,
                item_id=item_id,
                conflict_type=ConflictType.CLASSIFICATION_CHANGE,
                severity=self._get_classification_change_severity(static_class, llm_class),
                static_classification=static_class,
                static_confidence=static_item.get("confidence", 0.8),
                static_data=static_item.get("data", {}),
                llm_classification=llm_class,
                llm_confidence=llm_confidence,
                llm_data=llm_item,
                llm_provider=llm_item.get("provider"),
                description=f"Classification changed from '{static_class}' to '{llm_class}'",
                impact_assessment="Item type change may affect hierarchy and estimation",
                recommendations=[
                    f"Verify if '{llm_class}' is more appropriate",
                    "Check business context",
                    "Consider scope implications"
                ]
            ))

        # 3. Explicit disagreement (different providers disagree)
        if self._has_explicit_disagreement(static_item, llm_item):
            conflicts.append(ConflictItem(
                id=str(uuid4()),
                session_id=session_id,
                item_id=item_id,
                conflict_type=ConflictType.EXPLICIT_DISAGREEMENT,
                severity=ConflictSeverity.MEDIUM,
                static_classification=static_class,
                static_confidence=static_item.get("confidence", 0.8),
                static_data=static_item.get("data", {}),
                llm_classification=llm_class,
                llm_confidence=llm_confidence,
                llm_data=llm_item,
                llm_provider=llm_item.get("provider"),
                description="Static and LLM analysis show significant disagreement",
                impact_assessment="Conflicting interpretations need resolution",
                recommendations=[
                    "Compare reasoning from both sources",
                    "Check for domain-specific context",
                    "Consider additional expert review"
                ]
            ))

        return conflicts

    def _create_removal_conflict(
        self,
        session_id: str,
        item_id: str,
        static_item: Dict
    ) -> ConflictItem:
        """Create conflict for items removed by LLM analysis."""
        return ConflictItem(
            id=str(uuid4()),
            session_id=session_id,
            item_id=item_id,
            conflict_type=ConflictType.ITEM_REMOVAL,
            severity=ConflictSeverity.HIGH,
            static_classification=static_item.get("classification"),
            static_confidence=static_item.get("confidence", 0.8),
            static_data=static_item.get("data", {}),
            description="Static-detected item not found in LLM results",
            impact_assessment="Potential loss of valid requirement",
            recommendations=[
                "Verify if removal is intentional",
                "Check if item was merged into another",
                "Review source code for context"
            ]
        )

    def _create_low_confidence_conflict(
        self,
        session_id: str,
        item_id: str,
        llm_item: Dict
    ) -> ConflictItem:
        """Create conflict for new LLM items with low confidence."""
        return ConflictItem(
            id=str(uuid4()),
            session_id=session_id,
            item_id=item_id,
            conflict_type=ConflictType.CONFIDENCE_THRESHOLD,
            severity=ConflictSeverity.MEDIUM,
            llm_classification=llm_item.get("classification"),
            llm_confidence=llm_item.get("confidence", 0.5),
            llm_data=llm_item,
            llm_provider=llm_item.get("provider"),
            description=f"New LLM item with low confidence ({llm_item.get('confidence', 0.5):.1%})",
            impact_assessment="New requirement may not be valid",
            recommendations=[
                "Verify requirement exists in codebase",
                "Check for supporting evidence",
                "Consider static analysis gap"
            ]
        )

    def _get_classification_change_severity(
        self,
        from_class: str,
        to_class: str
    ) -> ConflictSeverity:
        """Determine severity based on classification change type."""
        # Define hierarchy changes that are more severe
        major_changes = [
            ("epic", "story"),
            ("epic", "task"),
            ("feature", "task"),
            ("business_rule", "nfr"),
            ("nfr", "business_rule"),
        ]

        change = (from_class.lower(), to_class.lower())
        if change in major_changes or (change[1], change[0]) in major_changes:
            return ConflictSeverity.HIGH

        return ConflictSeverity.MEDIUM

    def _has_explicit_disagreement(
        self,
        static_item: Dict,
        llm_item: Dict
    ) -> bool:
        """Check if there's explicit disagreement between analyses."""
        # Compare key attributes
        static_data = static_item.get("data", {})
        llm_data = llm_item

        # Check scope/description similarity
        static_desc = static_data.get("description", "") or static_data.get("natural_language", "")
        llm_desc = llm_data.get("description", "") or llm_data.get("title", "")

        if static_desc and llm_desc:
            # Simple word overlap check
            static_words = set(static_desc.lower().split())
            llm_words = set(llm_desc.lower().split())

            if len(static_words) > 0 and len(llm_words) > 0:
                overlap = len(static_words & llm_words) / max(len(static_words), len(llm_words))
                if overlap < 0.3:  # Less than 30% overlap
                    return True

        return False

    def _count_by_type(self, conflicts: List[ConflictItem]) -> Dict[str, int]:
        """Count conflicts by type."""
        counts = {}
        for conflict in conflicts:
            type_name = conflict.conflict_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts

    def _count_by_severity(self, conflicts: List[ConflictItem]) -> Dict[str, int]:
        """Count conflicts by severity."""
        counts = {}
        for conflict in conflicts:
            severity = conflict.severity.value
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    async def _auto_resolve(self, conflicts: List[ConflictItem]) -> int:
        """Auto-resolve conflicts where safe to do so."""
        resolved = 0

        for conflict in conflicts:
            if conflict.severity == ConflictSeverity.LOW:
                # Auto-accept higher confidence result
                if conflict.static_confidence > conflict.llm_confidence:
                    conflict.resolution = ConflictResolution.AUTO_ACCEPTED_STATIC
                    conflict.final_value = conflict.static_data
                else:
                    conflict.resolution = ConflictResolution.AUTO_ACCEPTED_LLM
                    conflict.final_value = conflict.llm_data

                conflict.resolved_at = datetime.utcnow()
                conflict.resolved_by = "system"
                conflict.resolution_notes = "Auto-resolved based on confidence comparison"
                resolved += 1

            elif conflict.severity == ConflictSeverity.MEDIUM:
                # Auto-accept if LLM confidence is very high
                if conflict.llm_confidence >= 0.90:
                    conflict.resolution = ConflictResolution.AUTO_ACCEPTED_LLM
                    conflict.final_value = conflict.llm_data
                    conflict.resolved_at = datetime.utcnow()
                    conflict.resolved_by = "system"
                    conflict.resolution_notes = "Auto-resolved: LLM confidence >= 90%"
                    resolved += 1

        return resolved

    async def resolve_conflict(
        self,
        conflict_id: str,
        resolution: ConflictResolution,
        resolved_by: str,
        final_value: Optional[Dict] = None,
        notes: str = ""
    ) -> ConflictItem:
        """
        Manually resolve a conflict.

        Args:
            conflict_id: ID of conflict to resolve
            resolution: How the conflict was resolved
            resolved_by: User ID who resolved it
            final_value: The chosen final value
            notes: Resolution notes

        Returns:
            Updated ConflictItem
        """
        # In real implementation, fetch from database
        # For now, return updated conflict
        conflict = ConflictItem(
            id=conflict_id,
            session_id="",
            item_id="",
            conflict_type=ConflictType.EXPLICIT_DISAGREEMENT,
            severity=ConflictSeverity.MEDIUM,
            resolution=resolution,
            resolved_at=datetime.utcnow(),
            resolved_by=resolved_by,
            final_value=final_value,
            resolution_notes=notes
        )

        logger.info(f"Conflict {conflict_id} resolved by {resolved_by}: {resolution.value}")

        return conflict

    async def get_pending_conflicts(
        self,
        session_id: str
    ) -> List[ConflictItem]:
        """Get all pending conflicts for a session."""
        # In real implementation, fetch from database
        return []

    async def get_conflict_summary(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """Get conflict summary for a session."""
        # In real implementation, fetch from database
        return {
            "session_id": session_id,
            "total_conflicts": 0,
            "pending": 0,
            "auto_resolved": 0,
            "human_resolved": 0,
            "by_type": {},
            "by_severity": {}
        }

    def to_dict(self, conflict: ConflictItem) -> Dict[str, Any]:
        """Convert ConflictItem to dictionary for API response."""
        return {
            "id": conflict.id,
            "session_id": conflict.session_id,
            "item_id": conflict.item_id,
            "conflict_type": conflict.conflict_type.value,
            "severity": conflict.severity.value,
            "static_classification": conflict.static_classification,
            "static_confidence": conflict.static_confidence,
            "static_data": conflict.static_data,
            "llm_classification": conflict.llm_classification,
            "llm_confidence": conflict.llm_confidence,
            "llm_data": conflict.llm_data,
            "llm_provider": conflict.llm_provider,
            "description": conflict.description,
            "impact_assessment": conflict.impact_assessment,
            "recommendations": conflict.recommendations,
            "resolution": conflict.resolution.value,
            "resolved_at": conflict.resolved_at.isoformat() if conflict.resolved_at else None,
            "resolved_by": conflict.resolved_by,
            "resolution_notes": conflict.resolution_notes,
            "final_value": conflict.final_value,
            "created_at": conflict.created_at.isoformat(),
        }
