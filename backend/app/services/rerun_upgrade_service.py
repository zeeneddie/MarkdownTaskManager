"""
Re-Run Upgrade Service - Week 85

Handles tier upgrades and re-extraction with improved LLMs.
Tracks deltas between extraction runs for comparison.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class UpgradeReason(str, Enum):
    """Reason for re-running extraction."""
    TIER_UPGRADE = "tier_upgrade"  # User upgraded tier
    LOW_CONFIDENCE = "low_confidence"  # Original had low confidence
    HUMAN_REQUEST = "human_request"  # Human review requested re-run
    CODEBASE_CHANGED = "codebase_changed"  # Code changed since last run
    NEW_LLM_AVAILABLE = "new_llm_available"  # Better LLM available
    QUALITY_ISSUE = "quality_issue"  # Quality issues in original


class ExtractionTier(str, Enum):
    """Extraction tier levels."""
    FREE = "FREE"
    BASIC = "BASIC"
    STANDARD = "STANDARD"
    PROFESSIONAL = "PROFESSIONAL"
    PREMIUM = "PREMIUM"


TIER_HIERARCHY = {
    ExtractionTier.FREE: 0,
    ExtractionTier.BASIC: 1,
    ExtractionTier.STANDARD: 2,
    ExtractionTier.PROFESSIONAL: 3,
    ExtractionTier.PREMIUM: 4,
}

TIER_PRICING = {
    ExtractionTier.FREE: 0.0,
    ExtractionTier.BASIC: 5.0,
    ExtractionTier.STANDARD: 25.0,
    ExtractionTier.PROFESSIONAL: 75.0,
    ExtractionTier.PREMIUM: 150.0,
}

TIER_EXPECTED_CONFIDENCE = {
    ExtractionTier.FREE: 0.60,
    ExtractionTier.BASIC: 0.70,
    ExtractionTier.STANDARD: 0.80,
    ExtractionTier.PROFESSIONAL: 0.90,
    ExtractionTier.PREMIUM: 0.95,
}


@dataclass
class StoryDelta:
    """Difference in a single story between runs."""
    story_id: str
    change_type: str  # added, removed, modified, unchanged
    old_story: Optional[Dict[str, Any]] = None
    new_story: Optional[Dict[str, Any]] = None
    field_changes: Dict[str, Tuple[Any, Any]] = field(default_factory=dict)
    confidence_change: float = 0.0


@dataclass
class ExtractionDelta:
    """Complete delta between two extraction runs."""
    delta_id: str
    original_session_id: str
    rerun_session_id: str
    original_tier: ExtractionTier
    rerun_tier: ExtractionTier
    calculated_at: datetime

    # Story-level changes
    added_stories: List[Dict[str, Any]]
    removed_stories: List[Dict[str, Any]]
    modified_stories: List[StoryDelta]
    unchanged_stories: int

    # Aggregate metrics
    total_original_stories: int
    total_rerun_stories: int
    confidence_improvement: float
    coverage_improvement: float

    # Quality metrics
    invest_score_original: float
    invest_score_rerun: float
    quality_improvement: float

    # Recommendations
    recommendations: List[str] = field(default_factory=list)


@dataclass
class UpgradeQuote:
    """Quote for tier upgrade."""
    quote_id: str
    current_tier: ExtractionTier
    target_tier: ExtractionTier
    price_difference: float
    expected_confidence_gain: float
    expected_story_improvement: int
    estimated_duration_minutes: int
    valid_until: datetime
    project_id: int
    session_id: str


@dataclass
class RerunRequest:
    """Request to re-run extraction."""
    request_id: str
    project_id: int
    original_session_id: str
    target_tier: ExtractionTier
    reason: UpgradeReason
    requested_at: datetime
    requested_by: str
    quote_id: Optional[str] = None
    focus_areas: List[str] = field(default_factory=list)  # Specific areas to improve


@dataclass
class RerunResult:
    """Result of re-run extraction."""
    rerun_id: str
    request: RerunRequest
    new_session_id: str
    delta: ExtractionDelta
    completed_at: datetime
    duration_ms: int
    cost_incurred: float
    success: bool
    errors: List[str] = field(default_factory=list)


class RerunUpgradeService:
    """
    Service for tier upgrades and extraction re-runs.

    Features:
    - Quote generation for tier upgrades
    - Re-run extraction with upgraded tier
    - Delta calculation between runs
    - Merge strategies for combining results
    - Quality tracking across runs
    """

    def __init__(self, db=None, extraction_service=None):
        self.db = db
        self.extraction_service = extraction_service
        self._quotes: Dict[str, UpgradeQuote] = {}
        self._rerun_history: Dict[str, RerunResult] = {}

    async def generate_upgrade_quote(
        self,
        project_id: int,
        session_id: str,
        target_tier: str,
        original_result: Optional[Dict[str, Any]] = None,
    ) -> UpgradeQuote:
        """
        Generate a quote for tier upgrade.

        Args:
            project_id: Project ID
            session_id: Original extraction session ID
            target_tier: Target tier to upgrade to
            original_result: Optional original extraction result

        Returns:
            UpgradeQuote with pricing and expectations
        """
        target = ExtractionTier(target_tier.upper())

        # Determine current tier from original result
        current_tier = ExtractionTier.FREE
        if original_result:
            tier_str = original_result.get("tier", "FREE")
            current_tier = ExtractionTier(tier_str.upper())

        # Validate upgrade path
        if TIER_HIERARCHY[target] <= TIER_HIERARCHY[current_tier]:
            raise ValueError(
                f"Cannot upgrade from {current_tier.value} to {target.value}. "
                f"Target tier must be higher."
            )

        # Calculate price difference
        price_diff = TIER_PRICING[target] - TIER_PRICING[current_tier]

        # Expected improvements
        confidence_gain = (
            TIER_EXPECTED_CONFIDENCE[target] -
            TIER_EXPECTED_CONFIDENCE[current_tier]
        )

        # Estimate story improvement based on original result
        original_stories = 0
        if original_result:
            original_stories = original_result.get("total_stories", 0)

        # Higher tiers typically find 10-30% more stories
        tier_diff = TIER_HIERARCHY[target] - TIER_HIERARCHY[current_tier]
        estimated_improvement = int(original_stories * 0.1 * tier_diff)

        # Estimate duration based on tier
        estimated_duration = 5 + (tier_diff * 10)  # Base 5 min + 10 per tier level

        quote = UpgradeQuote(
            quote_id=str(uuid4()),
            current_tier=current_tier,
            target_tier=target,
            price_difference=price_diff,
            expected_confidence_gain=confidence_gain,
            expected_story_improvement=estimated_improvement,
            estimated_duration_minutes=estimated_duration,
            valid_until=datetime.utcnow().replace(
                hour=23, minute=59, second=59
            ),  # Valid until end of day
            project_id=project_id,
            session_id=session_id,
        )

        self._quotes[quote.quote_id] = quote
        return quote

    async def request_rerun(
        self,
        project_id: int,
        original_session_id: str,
        target_tier: str,
        reason: str,
        requested_by: str,
        quote_id: Optional[str] = None,
        focus_areas: Optional[List[str]] = None,
    ) -> RerunRequest:
        """
        Create a request for extraction re-run.

        Args:
            project_id: Project ID
            original_session_id: Original extraction session
            target_tier: Target tier for re-run
            reason: Reason for re-run
            requested_by: User requesting re-run
            quote_id: Optional quote ID if upgrading
            focus_areas: Specific areas to focus on

        Returns:
            RerunRequest
        """
        target = ExtractionTier(target_tier.upper())
        upgrade_reason = UpgradeReason(reason.lower())

        # Validate quote if provided
        if quote_id and quote_id in self._quotes:
            quote = self._quotes[quote_id]
            if quote.target_tier != target:
                raise ValueError("Quote tier doesn't match requested tier")
            if quote.session_id != original_session_id:
                raise ValueError("Quote session doesn't match requested session")

        request = RerunRequest(
            request_id=str(uuid4()),
            project_id=project_id,
            original_session_id=original_session_id,
            target_tier=target,
            reason=upgrade_reason,
            requested_at=datetime.utcnow(),
            requested_by=requested_by,
            quote_id=quote_id,
            focus_areas=focus_areas or [],
        )

        return request

    async def execute_rerun(
        self,
        request: RerunRequest,
        original_result: Dict[str, Any],
        repository_path: str,
    ) -> RerunResult:
        """
        Execute the extraction re-run.

        Args:
            request: RerunRequest
            original_result: Original extraction result
            repository_path: Path to repository

        Returns:
            RerunResult with delta analysis
        """
        start_time = datetime.utcnow()
        errors = []

        try:
            # Run new extraction with upgraded tier
            if self.extraction_service:
                new_result = await self.extraction_service.extract_hierarchical(
                    repository_path=repository_path,
                    tier=request.target_tier.value,
                )
                new_session_id = new_result.extraction_id
                new_result_dict = self._extraction_result_to_dict(new_result)
            else:
                # Mock for testing
                new_session_id = str(uuid4())
                new_result_dict = self._mock_improved_result(
                    original_result, request.target_tier
                )

            # Calculate delta
            delta = await self.calculate_delta(
                original_result=original_result,
                rerun_result=new_result_dict,
                original_tier=ExtractionTier(
                    original_result.get("tier", "FREE").upper()
                ),
                rerun_tier=request.target_tier,
            )

            # Calculate cost
            cost = self._calculate_rerun_cost(request, original_result)

            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            result = RerunResult(
                rerun_id=str(uuid4()),
                request=request,
                new_session_id=new_session_id,
                delta=delta,
                completed_at=end_time,
                duration_ms=duration_ms,
                cost_incurred=cost,
                success=True,
                errors=errors,
            )

            self._rerun_history[result.rerun_id] = result
            return result

        except Exception as e:
            logger.error(f"Re-run failed: {e}")
            errors.append(str(e))

            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            return RerunResult(
                rerun_id=str(uuid4()),
                request=request,
                new_session_id="",
                delta=self._empty_delta(request),
                completed_at=end_time,
                duration_ms=duration_ms,
                cost_incurred=0.0,
                success=False,
                errors=errors,
            )

    async def calculate_delta(
        self,
        original_result: Dict[str, Any],
        rerun_result: Dict[str, Any],
        original_tier: ExtractionTier,
        rerun_tier: ExtractionTier,
    ) -> ExtractionDelta:
        """
        Calculate the delta between two extraction runs.

        Args:
            original_result: Original extraction result
            rerun_result: Re-run extraction result
            original_tier: Original tier
            rerun_tier: Re-run tier

        Returns:
            ExtractionDelta with all changes
        """
        original_stories = self._extract_stories(original_result)
        rerun_stories = self._extract_stories(rerun_result)

        original_ids = {s.get("id") for s in original_stories}
        rerun_ids = {s.get("id") for s in rerun_stories}

        # Find added stories (in rerun but not original)
        added_ids = rerun_ids - original_ids
        added_stories = [s for s in rerun_stories if s.get("id") in added_ids]

        # Find removed stories (in original but not rerun)
        removed_ids = original_ids - rerun_ids
        removed_stories = [s for s in original_stories if s.get("id") in removed_ids]

        # Find modified stories (in both but different)
        common_ids = original_ids & rerun_ids
        modified_stories = []
        unchanged_count = 0

        original_by_id = {s.get("id"): s for s in original_stories}
        rerun_by_id = {s.get("id"): s for s in rerun_stories}

        for story_id in common_ids:
            old = original_by_id.get(story_id, {})
            new = rerun_by_id.get(story_id, {})

            changes = self._compare_stories(old, new)
            if changes:
                modified_stories.append(StoryDelta(
                    story_id=story_id,
                    change_type="modified",
                    old_story=old,
                    new_story=new,
                    field_changes=changes,
                    confidence_change=new.get("confidence", 0) - old.get("confidence", 0),
                ))
            else:
                unchanged_count += 1

        # Calculate aggregate metrics
        original_confidence = original_result.get("overall_confidence", 0.0)
        rerun_confidence = rerun_result.get("overall_confidence", 0.0)
        confidence_improvement = rerun_confidence - original_confidence

        original_coverage = original_result.get("coverage", 0.0)
        rerun_coverage = rerun_result.get("coverage", 0.0)
        coverage_improvement = rerun_coverage - original_coverage

        # Quality scores (placeholder - would use INVEST validator)
        invest_original = original_result.get("invest_score", 0.0)
        invest_rerun = rerun_result.get("invest_score", 0.0)
        quality_improvement = invest_rerun - invest_original

        # Generate recommendations
        recommendations = self._generate_delta_recommendations(
            added_stories,
            removed_stories,
            modified_stories,
            confidence_improvement,
        )

        return ExtractionDelta(
            delta_id=str(uuid4()),
            original_session_id=original_result.get("extraction_id", ""),
            rerun_session_id=rerun_result.get("extraction_id", ""),
            original_tier=original_tier,
            rerun_tier=rerun_tier,
            calculated_at=datetime.utcnow(),
            added_stories=added_stories,
            removed_stories=removed_stories,
            modified_stories=modified_stories,
            unchanged_stories=unchanged_count,
            total_original_stories=len(original_stories),
            total_rerun_stories=len(rerun_stories),
            confidence_improvement=confidence_improvement,
            coverage_improvement=coverage_improvement,
            invest_score_original=invest_original,
            invest_score_rerun=invest_rerun,
            quality_improvement=quality_improvement,
            recommendations=recommendations,
        )

    async def get_upgrade_recommendations(
        self,
        session_id: str,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Get recommendations for upgrading based on current results.

        Args:
            session_id: Current extraction session
            result: Current extraction result

        Returns:
            Recommendations for upgrade
        """
        current_tier = ExtractionTier(result.get("tier", "FREE").upper())
        current_confidence = result.get("overall_confidence", 0.0)

        recommendations = {
            "should_upgrade": False,
            "recommended_tier": None,
            "reasons": [],
            "expected_improvements": [],
            "estimated_cost": 0.0,
        }

        # Check if confidence is below expected
        expected = TIER_EXPECTED_CONFIDENCE[current_tier]
        if current_confidence < expected * 0.9:
            recommendations["should_upgrade"] = True
            recommendations["reasons"].append(
                f"Current confidence ({current_confidence:.0%}) below "
                f"expected for {current_tier.value} tier ({expected:.0%})"
            )

        # Check for quality issues
        low_quality_stories = sum(
            1 for s in self._extract_stories(result)
            if s.get("confidence", 0) < 0.6
        )
        total_stories = result.get("total_stories", 0)

        if total_stories > 0 and low_quality_stories / total_stories > 0.3:
            recommendations["should_upgrade"] = True
            recommendations["reasons"].append(
                f"{low_quality_stories} stories have low confidence"
            )

        # Recommend next tier if upgrade needed
        if recommendations["should_upgrade"]:
            next_tier = self._get_next_tier(current_tier)
            if next_tier:
                recommendations["recommended_tier"] = next_tier.value
                recommendations["estimated_cost"] = (
                    TIER_PRICING[next_tier] - TIER_PRICING[current_tier]
                )
                recommendations["expected_improvements"] = [
                    f"Confidence increase: +{(TIER_EXPECTED_CONFIDENCE[next_tier] - expected) * 100:.0f}%",
                    f"Better LLM coverage",
                    f"More accurate story extraction",
                ]

        return recommendations

    async def merge_results(
        self,
        original: Dict[str, Any],
        rerun: Dict[str, Any],
        strategy: str = "prefer_rerun",
    ) -> Dict[str, Any]:
        """
        Merge two extraction results.

        Strategies:
        - prefer_rerun: Keep rerun results, fill gaps from original
        - prefer_original: Keep original, add new from rerun
        - highest_confidence: Keep story with highest confidence
        - union: Keep all stories from both

        Args:
            original: Original extraction result
            rerun: Re-run extraction result
            strategy: Merge strategy

        Returns:
            Merged result
        """
        original_stories = self._extract_stories(original)
        rerun_stories = self._extract_stories(rerun)

        original_by_id = {s.get("id"): s for s in original_stories}
        rerun_by_id = {s.get("id"): s for s in rerun_stories}

        merged_stories = []

        if strategy == "prefer_rerun":
            # Start with rerun, add missing from original
            merged_stories = list(rerun_stories)
            for story_id, story in original_by_id.items():
                if story_id not in rerun_by_id:
                    merged_stories.append(story)

        elif strategy == "prefer_original":
            # Start with original, add new from rerun
            merged_stories = list(original_stories)
            for story_id, story in rerun_by_id.items():
                if story_id not in original_by_id:
                    merged_stories.append(story)

        elif strategy == "highest_confidence":
            # For each story, keep version with highest confidence
            all_ids = set(original_by_id.keys()) | set(rerun_by_id.keys())
            for story_id in all_ids:
                orig = original_by_id.get(story_id)
                new = rerun_by_id.get(story_id)

                if orig and new:
                    if new.get("confidence", 0) >= orig.get("confidence", 0):
                        merged_stories.append(new)
                    else:
                        merged_stories.append(orig)
                elif new:
                    merged_stories.append(new)
                elif orig:
                    merged_stories.append(orig)

        elif strategy == "union":
            # Keep all, prefer rerun for duplicates
            merged_stories = list(rerun_stories)
            for story_id, story in original_by_id.items():
                if story_id not in rerun_by_id:
                    merged_stories.append(story)

        # Create merged result
        merged = {
            **rerun,  # Base from rerun
            "stories": merged_stories,
            "total_stories": len(merged_stories),
            "merge_strategy": strategy,
            "merged_at": datetime.utcnow().isoformat(),
            "original_session_id": original.get("extraction_id"),
            "rerun_session_id": rerun.get("extraction_id"),
        }

        # Recalculate confidence
        if merged_stories:
            avg_confidence = sum(
                s.get("confidence", 0) for s in merged_stories
            ) / len(merged_stories)
            merged["overall_confidence"] = avg_confidence

        return merged

    # ==================== Private Methods ====================

    def _extract_stories(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract stories from extraction result."""
        stories = []

        # Direct stories
        if "stories" in result:
            stories.extend(result["stories"])

        # From hierarchy levels
        for level in ["function_level", "class_level", "module_level", "system_level"]:
            level_data = result.get(level, {})
            if isinstance(level_data, dict) and "stories" in level_data:
                stories.extend(level_data["stories"])

        return stories

    def _compare_stories(
        self,
        old: Dict[str, Any],
        new: Dict[str, Any],
    ) -> Dict[str, Tuple[Any, Any]]:
        """Compare two stories and return field changes."""
        changes = {}
        compare_fields = [
            "title", "description", "type", "priority",
            "confidence", "acceptance_criteria", "estimation",
        ]

        for field in compare_fields:
            old_val = old.get(field)
            new_val = new.get(field)
            if old_val != new_val:
                changes[field] = (old_val, new_val)

        return changes

    def _generate_delta_recommendations(
        self,
        added: List[Dict[str, Any]],
        removed: List[Dict[str, Any]],
        modified: List[StoryDelta],
        confidence_improvement: float,
    ) -> List[str]:
        """Generate recommendations based on delta analysis."""
        recommendations = []

        if added:
            recommendations.append(
                f"{len(added)} new stories discovered. Review for accuracy."
            )

        if removed:
            recommendations.append(
                f"{len(removed)} stories removed. Verify they're obsolete."
            )

        if modified:
            high_confidence_changes = [
                m for m in modified if m.confidence_change > 0.1
            ]
            if high_confidence_changes:
                recommendations.append(
                    f"{len(high_confidence_changes)} stories significantly improved."
                )

        if confidence_improvement > 0.15:
            recommendations.append(
                f"Significant confidence improvement ({confidence_improvement:.0%}). "
                "Consider accepting rerun results."
            )
        elif confidence_improvement < 0:
            recommendations.append(
                f"Confidence decreased ({confidence_improvement:.0%}). "
                "Review changes carefully."
            )

        return recommendations

    def _calculate_rerun_cost(
        self,
        request: RerunRequest,
        original_result: Dict[str, Any],
    ) -> float:
        """Calculate cost for re-run."""
        original_tier = ExtractionTier(
            original_result.get("tier", "FREE").upper()
        )
        return TIER_PRICING[request.target_tier] - TIER_PRICING[original_tier]

    def _get_next_tier(self, current: ExtractionTier) -> Optional[ExtractionTier]:
        """Get the next tier up from current."""
        current_level = TIER_HIERARCHY[current]
        for tier, level in TIER_HIERARCHY.items():
            if level == current_level + 1:
                return tier
        return None

    def _mock_improved_result(
        self,
        original: Dict[str, Any],
        target_tier: ExtractionTier,
    ) -> Dict[str, Any]:
        """Create mock improved result for testing."""
        stories = self._extract_stories(original)

        # Improve confidence
        for story in stories:
            story["confidence"] = min(
                story.get("confidence", 0.5) + 0.15,
                0.95
            )

        # Add some new stories
        new_story_count = max(1, len(stories) // 10)
        for i in range(new_story_count):
            stories.append({
                "id": f"new-{uuid4()}",
                "title": f"Discovered story {i + 1}",
                "type": "story",
                "confidence": TIER_EXPECTED_CONFIDENCE[target_tier],
            })

        return {
            "extraction_id": str(uuid4()),
            "tier": target_tier.value,
            "stories": stories,
            "total_stories": len(stories),
            "overall_confidence": TIER_EXPECTED_CONFIDENCE[target_tier],
        }

    def _empty_delta(self, request: RerunRequest) -> ExtractionDelta:
        """Create empty delta for failed re-run."""
        return ExtractionDelta(
            delta_id=str(uuid4()),
            original_session_id=request.original_session_id,
            rerun_session_id="",
            original_tier=ExtractionTier.FREE,
            rerun_tier=request.target_tier,
            calculated_at=datetime.utcnow(),
            added_stories=[],
            removed_stories=[],
            modified_stories=[],
            unchanged_stories=0,
            total_original_stories=0,
            total_rerun_stories=0,
            confidence_improvement=0.0,
            coverage_improvement=0.0,
            invest_score_original=0.0,
            invest_score_rerun=0.0,
            quality_improvement=0.0,
        )

    def _extraction_result_to_dict(self, result) -> Dict[str, Any]:
        """Convert extraction result to dict."""
        if hasattr(result, "__dict__"):
            return result.__dict__
        return dict(result) if result else {}


def get_rerun_upgrade_service(
    db=None,
    extraction_service=None,
) -> RerunUpgradeService:
    """Factory function for RerunUpgradeService."""
    return RerunUpgradeService(db, extraction_service)
