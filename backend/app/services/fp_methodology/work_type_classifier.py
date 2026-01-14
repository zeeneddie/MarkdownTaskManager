# Work Type Classifier
# Determines appropriate estimation method based on work type
#
# Key insight: Not all work has Function Points!
# - Analysis/audit work → Time & Materials
# - Development → Development FP
# - Enhancement → Enhancement FP
# - Maintenance → Support hours
#
# Architecture: docs/roadmap/phases/fase-22-fp-methodology.md
# Phase: Fase 22 (Week 146-147)

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class WorkType(Enum):
    """
    Types of work for estimation.

    NESMA terminology:
    - ANALYSIS = Analyse (NO FP - Time & Materials)
    - DEVELOPMENT = Nieuwe bouw (Development FP)
    - ENHANCEMENT = Verbouw (Enhancement FP)
    - REBUILD = Herbouw (Rebuild FP - special case)
    - MAINTENANCE = Onderhoud (Support Hours)
    """
    ANALYSIS = "analysis"        # Analyse - NO FP!
    DEVELOPMENT = "development"  # Nieuwe bouw
    ENHANCEMENT = "enhancement"  # Verbouw
    REBUILD = "rebuild"          # Herbouw
    MAINTENANCE = "maintenance"  # Onderhoud


class EstimationMethod(Enum):
    """
    Recommended estimation methods.

    NESMA methods:
    - TIME_AND_MATERIALS: For analysis (Analyse) - no FP
    - DEVELOPMENT_FP: Nieuwe bouw (New Development)
    - ENHANCEMENT_FP: Verbouw (Enhancement)
    - REBUILD_FP: Herbouw (Rebuild/Replacement)
    - SUPPORT_HOURS: Onderhoud (Maintenance)
    """
    TIME_AND_MATERIALS = "time_and_materials"  # Analyse
    DEVELOPMENT_FP = "development_fp"          # Nieuwe bouw
    ENHANCEMENT_FP = "enhancement_fp"          # Verbouw
    REBUILD_FP = "rebuild_fp"                  # Herbouw
    SUPPORT_HOURS = "support_hours"            # Onderhoud
    STORY_POINTS = "story_points"              # Agile alternative


@dataclass
class WorkTypeClassification:
    """Result of work type classification."""
    work_type: WorkType
    confidence: float  # 0.0 - 1.0
    fp_applicable: bool
    recommended_method: EstimationMethod
    description: str
    matched_keywords: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "work_type": self.work_type.value,
            "confidence": round(self.confidence, 2),
            "fp_applicable": self.fp_applicable,
            "recommended_method": self.recommended_method.value,
            "description": self.description,
            "matched_keywords": self.matched_keywords,
            "warnings": self.warnings,
        }


class WorkTypeClassifier:
    """
    Classify work to determine appropriate estimation method.

    CRITICAL: Not all work has Function Points!

    Work Types:
    - ANALYSIS: Code review, audit, documentation → NO FP (Time & Materials)
    - DEVELOPMENT: New software creation → Development FP
    - ENHANCEMENT: Changes to existing software → Enhancement FP
    - MAINTENANCE: Keeping software operational → Support Hours

    Usage:
        classifier = WorkTypeClassifier()

        # This returns FP_APPLICABLE = False
        result = classifier.classify(
            description="ADO leak audit and documentation"
        )
        # result.fp_applicable == False
        # result.recommended_method == TIME_AND_MATERIALS

        # This returns FP_APPLICABLE = True
        result = classifier.classify(
            description="Add new customer registration feature"
        )
        # result.fp_applicable == True
        # result.recommended_method == DEVELOPMENT_FP
    """

    # Work type definitions with keywords and patterns
    WORK_TYPE_DEFINITIONS = {
        WorkType.ANALYSIS: {
            "description": "Code review, audit, assessment, documentation (Analyse - GEEN FP!)",
            "fp_applicable": False,
            "recommended_method": EstimationMethod.TIME_AND_MATERIALS,
            "keywords": [
                "analyse", "onderzoek", "beoordeling",  # Dutch
                "audit", "review", "assess", "analyze", "analysis",
                "document", "documentation", "investigate", "research",
                "scan", "inspect", "evaluate", "examine", "study",
                "security review", "code review", "architecture review",
                "leak detection", "vulnerability scan", "compliance check",
                "brown paper", "assessment", "inventarisatie",
            ],
            "examples": [
                "ADO leak audit",
                "Security review",
                "Architecture assessment",
                "Code quality analysis",
                "Compliance documentation",
                "Brown Paper analyse",
            ],
        },
        WorkType.DEVELOPMENT: {
            "description": "New software creation, greenfield projects (Nieuwe bouw)",
            "fp_applicable": True,
            "recommended_method": EstimationMethod.DEVELOPMENT_FP,
            "keywords": [
                "nieuwe bouw", "nieuwbouw", "green paper",  # Dutch
                "new feature", "new module", "new system", "new application",
                "greenfield", "build new", "create new", "develop new",
                "implement new", "design new", "from scratch",
                "new project", "new product", "new service",
                "nieuw systeem", "nieuw project", "nieuw ontwikkeling",
            ],
            "examples": [
                "New customer portal",
                "New reporting module",
                "Greenfield project",
                "New API development",
                "Nieuwe bouw applicatie",
            ],
        },
        WorkType.ENHANCEMENT: {
            "description": "Changes to existing software, bug fixes, improvements (Verbouw)",
            "fp_applicable": True,
            "recommended_method": EstimationMethod.ENHANCEMENT_FP,
            "keywords": [
                "verbouw", "aanpassing", "uitbreiding", "wijziging",  # Dutch
                "fix", "bug", "enhance", "improve", "modify", "change",
                "update", "upgrade", "refactor", "optimize", "migrate",
                "add feature", "extend", "expand", "performance",
                "maintenance fix", "defect", "issue", "problem",
                "correction", "patch", "hotfix", "verbetering",
            ],
            "examples": [
                "Bug fixes",
                "Performance improvements",
                "Refactoring",
                "Feature enhancement",
                "System migration",
                "Verbouw bestaand systeem",
            ],
        },
        WorkType.REBUILD: {
            "description": "Complete rebuild/replacement of existing system (Herbouw)",
            "fp_applicable": True,
            "recommended_method": EstimationMethod.REBUILD_FP,
            "keywords": [
                "herbouw", "rebuild", "replace", "rewrite", "recreate",
                "replacement", "replatform", "re-engineer", "reengineering",
                "legacy replacement", "system replacement", "modernization",
                "platform migration", "technology upgrade", "complete rewrite",
                "from scratch replacement", "sunset and replace",
            ],
            "examples": [
                "Legacy system replacement",
                "Platform migration",
                "Complete system rebuild",
                "Technology modernization",
                "Replatforming project",
            ],
        },
        WorkType.MAINTENANCE: {
            "description": "Keeping software operational, support, monitoring (Onderhoud)",
            "fp_applicable": False,
            "recommended_method": EstimationMethod.SUPPORT_HOURS,
            "keywords": [
                "onderhoud", "beheer",  # Dutch
                "support", "maintain", "monitor", "operate", "run",
                "backup", "restore", "patch management", "user support",
                "helpdesk", "incident", "on-call", "deployment",
                "release management", "configuration",
            ],
            "examples": [
                "24/7 monitoring",
                "User support",
                "Incident management",
                "Patch deployment",
                "Applicatiebeheer",
            ],
        },
    }

    def classify(
        self,
        description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkTypeClassification:
        """
        Classify work based on description and context.

        Args:
            description: Work description
            context: Optional additional context (project type, etc.)

        Returns:
            WorkTypeClassification with recommended estimation method
        """
        description_lower = description.lower()
        scores: Dict[WorkType, float] = {wt: 0.0 for wt in WorkType}
        matched: Dict[WorkType, List[str]] = {wt: [] for wt in WorkType}

        # Score each work type based on keyword matches
        for work_type, definition in self.WORK_TYPE_DEFINITIONS.items():
            for keyword in definition["keywords"]:
                if keyword.lower() in description_lower:
                    # Weight multi-word keywords higher
                    weight = 1.0 + (keyword.count(" ") * 0.5)
                    scores[work_type] += weight
                    matched[work_type].append(keyword)

        # Find best match
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        total_score = sum(scores.values())

        # Calculate confidence
        if total_score > 0:
            confidence = best_score / total_score
        else:
            # No matches - default to enhancement with low confidence
            best_type = WorkType.ENHANCEMENT
            confidence = 0.3

        # Adjust confidence based on score magnitude
        if best_score < 1.0:
            confidence *= 0.5  # Low score = lower confidence

        definition = self.WORK_TYPE_DEFINITIONS[best_type]

        result = WorkTypeClassification(
            work_type=best_type,
            confidence=min(confidence, 1.0),
            fp_applicable=definition["fp_applicable"],
            recommended_method=definition["recommended_method"],
            description=definition["description"],
            matched_keywords=matched[best_type],
        )

        # Add warnings for common mistakes
        self._add_warnings(result, description_lower, scores)

        logger.info(
            f"Classified '{description[:50]}...' as {best_type.value} "
            f"(confidence: {result.confidence:.2f}, FP applicable: {result.fp_applicable})"
        )

        return result

    def _add_warnings(
        self,
        result: WorkTypeClassification,
        description: str,
        scores: Dict[WorkType, float],
    ):
        """Add warnings for potential misclassifications."""
        # Warning: Analysis work often miscounted with FP
        if result.work_type == WorkType.ANALYSIS:
            result.warnings.append(
                "Analysis work has NO Function Points in IFPUG methodology. "
                "Use Time & Materials estimation for audits, reviews, and assessments."
            )

        # Warning: Multiple work types detected
        non_zero_types = [wt for wt, score in scores.items() if score > 0]
        if len(non_zero_types) > 1:
            other_types = [wt.value for wt in non_zero_types if wt != result.work_type]
            result.warnings.append(
                f"Work may include multiple types: {', '.join(other_types)}. "
                "Consider breaking into separate estimates."
            )

        # Warning: Low confidence
        if result.confidence < 0.5:
            result.warnings.append(
                "Low classification confidence. Please verify work type manually."
            )

        # Warning: FP misuse patterns
        fp_misuse_patterns = [
            "source code", "source files", "asp files", "analyze code",
            "review code", "scan code", "inspect files",
        ]
        for pattern in fp_misuse_patterns:
            if pattern in description:
                result.warnings.append(
                    f"Pattern '{pattern}' detected. Analyzing/reviewing source code "
                    "is NOT software development and has no FP."
                )
                break

    def get_estimation_guidance(
        self,
        work_type: WorkType,
    ) -> Dict[str, Any]:
        """
        Get detailed estimation guidance for a work type.

        Args:
            work_type: The work type to get guidance for

        Returns:
            Detailed guidance including method, examples, and warnings
        """
        definition = self.WORK_TYPE_DEFINITIONS[work_type]

        guidance = {
            "work_type": work_type.value,
            "description": definition["description"],
            "fp_applicable": definition["fp_applicable"],
            "recommended_method": definition["recommended_method"].value,
            "examples": definition["examples"],
            "estimation_approach": self._get_estimation_approach(work_type),
        }

        return guidance

    def _get_estimation_approach(self, work_type: WorkType) -> Dict[str, Any]:
        """Get specific estimation approach for work type."""
        approaches = {
            WorkType.ANALYSIS: {
                "method": "Time & Materials - Analyse (GEEN FP!)",
                "formula": "Estimated Hours × Hourly Rate",
                "inputs": ["Scope of analysis", "Complexity", "Deliverables"],
                "fp_count": 0,
                "note": "Analysis produces documentation, not software. No FP applicable. "
                        "KRITISCH: Analyse werk (code review, audit, etc.) heeft GEEN functiepunten!",
            },
            WorkType.DEVELOPMENT: {
                "method": "Development FP (IFPUG CPM 4.3.1) - Nieuwe bouw",
                "formula": "UFP = Σ(ILF + EIF + EI + EO + EQ)",
                "inputs": ["Data files (ILF/EIF)", "Transactions (EI/EO/EQ)", "Complexity"],
                "fp_count": "Varies",
                "note": "Count all components. Use complexity matrices for FP values.",
            },
            WorkType.ENHANCEMENT: {
                "method": "Enhancement FP (IFPUG CPM 4.3.1) - Verbouw",
                "formula": "EFP = ADD + CHNG + DEL + CFP",
                "inputs": ["Functions added", "Functions changed", "Functions deleted"],
                "fp_count": "Varies",
                "note": "Count functions AFTER change. Deleted functions = 40% of original FP.",
            },
            WorkType.REBUILD: {
                "method": "Rebuild FP (IFPUG CPM 4.3.1) - Herbouw",
                "formula": "RFP = UFP_new + CFP (conversion)",
                "inputs": ["New system FP count", "Data conversion FP", "Interface changes"],
                "fp_count": "Varies",
                "note": "Count as new development FP + conversion FP. Legacy system FP is baseline only.",
            },
            WorkType.MAINTENANCE: {
                "method": "Support Hours - Onderhoud",
                "formula": "Monthly Hours × Duration × Rate",
                "inputs": ["SLA requirements", "System complexity", "User base"],
                "fp_count": 0,
                "note": "Operational work maintaining existing functionality. No FP applicable.",
            },
        }
        return approaches.get(work_type, {})

    def validate_fp_usage(
        self,
        description: str,
        fp_count: float,
    ) -> Tuple[bool, List[str]]:
        """
        Validate if FP should be used for this work.

        Args:
            description: Work description
            fp_count: FP count being proposed

        Returns:
            Tuple of (is_valid, list of issues)
        """
        classification = self.classify(description)
        issues = []

        if not classification.fp_applicable and fp_count > 0:
            issues.append(
                f"FP count of {fp_count} proposed for {classification.work_type.value} work. "
                f"This work type does not have Function Points. "
                f"Recommended method: {classification.recommended_method.value}"
            )

        if classification.fp_applicable and fp_count == 0:
            issues.append(
                f"No FP count for {classification.work_type.value} work. "
                f"This work type should be estimated using {classification.recommended_method.value}."
            )

        return len(issues) == 0, issues
