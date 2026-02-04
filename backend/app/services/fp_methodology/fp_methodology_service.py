# FP Methodology Service
# Unified service for IFPUG/NESMA Function Point calculations
#
# Combines:
# - Work Type Classification (determine if FP applicable)
# - Component Validation (IFPUG CPM 4.3.1 rules)
# - Enhancement FP Calculation (ADD/CHNG/DEL/CFP)
#
# Architecture: docs/roadmap/phases/fase-22-fp-methodology.md
# Phase: Fase 22 (Week 146-147)

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging

from .work_type_classifier import (
    WorkTypeClassifier,
    WorkType,
    WorkTypeClassification,
    EstimationMethod,
)
from .validator import (
    FPComponentValidator,
    ValidationResult,
    ValidationSeverity,
)
from .enhancement_calculator import (
    EnhancementFPCalculator,
    EnhancementFPResult,
    EnhancementComponent,
    ChangeType,
    ComponentType,
    Complexity,
)

logger = logging.getLogger(__name__)


# IFPUG FP values for data functions
DATA_FP_VALUES = {
    "ILF": {"low": 7, "average": 10, "high": 15},
    "EIF": {"low": 5, "average": 7, "high": 10},
}

# IFPUG FP values for transactional functions
TRANSACTION_FP_VALUES = {
    "EI": {"low": 3, "average": 4, "high": 6},
    "EO": {"low": 4, "average": 5, "high": 7},
    "EQ": {"low": 3, "average": 4, "high": 6},
}


@dataclass
class FPCalculationResult:
    """Complete FP calculation result."""
    # Work type classification
    work_type: WorkType
    work_type_confidence: float
    fp_applicable: bool
    recommended_method: EstimationMethod

    # Function Point counts
    unadjusted_fp: float = 0.0
    adjusted_fp: float = 0.0
    vaf: float = 1.0  # Value Adjustment Factor (deprecated but supported)

    # Component breakdown
    ilf_count: int = 0
    ilf_fp: float = 0.0
    eif_count: int = 0
    eif_fp: float = 0.0
    ei_count: int = 0
    ei_fp: float = 0.0
    eo_count: int = 0
    eo_fp: float = 0.0
    eq_count: int = 0
    eq_fp: float = 0.0

    # Enhancement breakdown (if applicable)
    add_fp: float = 0.0
    change_fp: float = 0.0
    delete_fp: float = 0.0
    conversion_fp: float = 0.0

    # Validation
    validation_issues: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0

    # Metadata
    methodology: str = "NESMA"
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "work_type": self.work_type.value,
            "work_type_confidence": round(self.work_type_confidence, 2),
            "fp_applicable": self.fp_applicable,
            "recommended_method": self.recommended_method.value,
            "function_points": {
                "unadjusted": round(self.unadjusted_fp, 1),
                "adjusted": round(self.adjusted_fp, 1),
                "vaf": round(self.vaf, 2),
            },
            "breakdown": {
                "ILF": {"count": self.ilf_count, "fp": round(self.ilf_fp, 1)},
                "EIF": {"count": self.eif_count, "fp": round(self.eif_fp, 1)},
                "EI": {"count": self.ei_count, "fp": round(self.ei_fp, 1)},
                "EO": {"count": self.eo_count, "fp": round(self.eo_fp, 1)},
                "EQ": {"count": self.eq_count, "fp": round(self.eq_fp, 1)},
            },
            "enhancement": {
                "add": round(self.add_fp, 1),
                "change": round(self.change_fp, 1),
                "delete": round(self.delete_fp, 1),
                "conversion": round(self.conversion_fp, 1),
            },
            "validation_issues": self.validation_issues,
            "confidence": round(self.confidence, 2),
            "methodology": self.methodology,
            "calculated_at": self.calculated_at.isoformat(),
        }


class FPMethodologyService:
    """
    Unified Function Point Methodology Service.

    Provides complete FP calculation pipeline:
    1. Classify work type (determine if FP applicable)
    2. Validate components against IFPUG rules
    3. Calculate FP (Development or Enhancement)

    Usage:
        service = FPMethodologyService()

        # Calculate FP from context
        result = await service.calculate({
            "description": "Migrate patient records to new system",
            "components": [
                {"name": "PatientRecord", "type": "ILF", "dets": 25, "rets": 3},
                {"name": "CreatePatient", "type": "EI", "dets": 10, "ftrs": 2},
            ]
        })

        if result["fp_applicable"]:
            print(f"Function Points: {result['function_points']['adjusted']}")
        else:
            print(f"Use {result['recommended_method']} instead of FP")
    """

    def __init__(self, methodology: str = "NESMA"):
        """
        Initialize FP Methodology Service.

        Args:
            methodology: FP methodology to use (NESMA, IFPUG)
        """
        self.methodology = methodology
        self.work_type_classifier = WorkTypeClassifier()
        self.validator = FPComponentValidator()
        self.enhancement_calculator = EnhancementFPCalculator()

    async def calculate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Function Points from context.

        Args:
            context: Dictionary containing:
                - description: Work description for classification
                - components: List of FP components to count
                - methodology: Optional override for methodology
                - change_type: Optional for enhancement projects

        Returns:
            FPCalculationResult as dictionary
        """
        # Ensure description is a string (may be passed as dict in some contexts)
        description = context.get("description", "")
        if isinstance(description, dict):
            # Extract text from dict if present
            description = description.get("text", description.get("summary", str(description)))
        description = str(description) if description else ""

        components = context.get("components", [])
        methodology = context.get("methodology", self.methodology)
        change_type = context.get("change_type")

        # Step 1: Classify work type
        try:
            classification = self.work_type_classifier.classify(description)
        except Exception as e:
            logger.warning(f"Work type classification failed: {e}")
            # Default to development FP if classification fails
            from .work_type_classifier import WorkType, EstimationMethod
            classification = type('Classification', (), {
                'work_type': WorkType.DEVELOPMENT,
                'confidence': 0.5,
                'fp_applicable': True,
                'recommended_method': EstimationMethod.DEVELOPMENT_FP,
            })()

        result = FPCalculationResult(
            work_type=classification.work_type,
            work_type_confidence=classification.confidence,
            fp_applicable=classification.fp_applicable,
            recommended_method=classification.recommended_method,
            methodology=methodology,
        )

        # Step 2: If FP not applicable, return early with recommendation
        if not classification.fp_applicable:
            result.confidence = classification.confidence
            logger.info(
                f"FP not applicable for '{description[:50]}...'. "
                f"Recommended: {classification.recommended_method.value}"
            )
            return result.to_dict()

        # Step 3: Validate and count components
        validation_issues = []
        total_fp = 0.0

        for comp in components:
            comp_name = comp.get("name", "Unknown")
            comp_type = comp.get("type", "").upper()
            dets = comp.get("dets", 0)
            rets = comp.get("rets", 0)
            ftrs = comp.get("ftrs", 0)
            complexity = comp.get("complexity", "average").lower()

            # Validate component
            if comp_type in ("ILF", "EIF"):
                validation = self.validator.validate_data_function(
                    name=comp_name,
                    component_type=comp_type,
                    description=comp.get("description", ""),
                    dets=dets,
                    rets=rets,
                )
            elif comp_type in ("EI", "EO", "EQ"):
                validation = self.validator.validate_transaction(
                    name=comp_name,
                    component_type=comp_type,
                    description=comp.get("description", ""),
                    dets=dets,
                    ftrs=ftrs,
                )
            else:
                validation = ValidationResult(
                    is_valid=False,
                    component_name=comp_name,
                    component_type=comp_type,
                )
                validation.add_issue(
                    ValidationSeverity.ERROR,
                    f"Unknown component type: {comp_type}",
                    "IFPUG-TYPES"
                )

            validation_issues.extend(validation.issues)

            if not validation.is_valid:
                continue

            # Calculate FP for this component
            if comp_type == "ILF":
                fp_value = DATA_FP_VALUES["ILF"].get(complexity, 10)
                result.ilf_count += 1
                result.ilf_fp += fp_value
            elif comp_type == "EIF":
                fp_value = DATA_FP_VALUES["EIF"].get(complexity, 7)
                result.eif_count += 1
                result.eif_fp += fp_value
            elif comp_type == "EI":
                fp_value = TRANSACTION_FP_VALUES["EI"].get(complexity, 4)
                result.ei_count += 1
                result.ei_fp += fp_value
            elif comp_type == "EO":
                fp_value = TRANSACTION_FP_VALUES["EO"].get(complexity, 5)
                result.eo_count += 1
                result.eo_fp += fp_value
            elif comp_type == "EQ":
                fp_value = TRANSACTION_FP_VALUES["EQ"].get(complexity, 4)
                result.eq_count += 1
                result.eq_fp += fp_value
            else:
                fp_value = 0

            total_fp += fp_value

        # Step 4: Calculate totals
        result.unadjusted_fp = total_fp
        result.adjusted_fp = total_fp * result.vaf
        result.validation_issues = validation_issues

        # Step 5: Calculate confidence based on validation
        error_count = sum(1 for i in validation_issues if i.get("severity") == "error")
        warning_count = sum(1 for i in validation_issues if i.get("severity") == "warning")

        if error_count > 0:
            result.confidence = 0.3
        elif warning_count > 2:
            result.confidence = 0.6
        elif warning_count > 0:
            result.confidence = 0.8
        else:
            result.confidence = 0.95

        logger.info(
            f"FP calculated: {result.adjusted_fp:.1f} AFP "
            f"({result.ilf_count} ILF, {result.eif_count} EIF, "
            f"{result.ei_count} EI, {result.eo_count} EO, {result.eq_count} EQ), "
            f"confidence {result.confidence:.0%}"
        )

        return result.to_dict()

    def classify_work_type(self, description_or_context) -> Dict[str, Any]:
        """
        Classify work type to determine estimation method.

        Args:
            description_or_context: Work description string or context dict

        Returns:
            WorkTypeClassification as dictionary
        """
        # Handle both string and dict inputs
        if isinstance(description_or_context, dict):
            description = description_or_context.get("description", "")
            if isinstance(description, dict):
                description = description.get("text", description.get("summary", ""))
            description = str(description) if description else ""
        else:
            description = str(description_or_context) if description_or_context else ""

        try:
            classification = self.work_type_classifier.classify(description)
            return classification.to_dict()
        except Exception as e:
            logger.warning(f"Work type classification failed: {e}")
            return {
                "work_type": "development",
                "confidence": 0.5,
                "fp_applicable": True,
                "recommended_method": "development_fp",
                "description": "Default classification due to error",
                "matched_keywords": [],
                "warnings": [str(e)],
            }

    def validate_component(
        self,
        name: str,
        component_type: str,
        description: str = "",
        dets: int = 0,
        rets: int = 0,
        ftrs: int = 0,
    ) -> Dict[str, Any]:
        """
        Validate a single FP component.

        Args:
            name: Component name
            component_type: ILF, EIF, EI, EO, or EQ
            description: Component description
            dets: Data Element Types count
            rets: Record Element Types count (for data functions)
            ftrs: File Types Referenced (for transactions)

        Returns:
            ValidationResult as dictionary
        """
        comp_type = component_type.upper()

        if comp_type in ("ILF", "EIF"):
            result = self.validator.validate_data_function(
                name=name,
                component_type=comp_type,
                description=description,
                dets=dets,
                rets=rets,
            )
        elif comp_type in ("EI", "EO", "EQ"):
            result = self.validator.validate_transaction(
                name=name,
                component_type=comp_type,
                description=description,
                dets=dets,
                ftrs=ftrs,
            )
        else:
            result = ValidationResult(
                is_valid=False,
                component_name=name,
                component_type=comp_type,
            )
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Unknown component type: {comp_type}",
                "IFPUG-TYPES"
            )

        return result.to_dict()

    def calculate_enhancement_fp(
        self,
        components: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calculate Enhancement Function Points.

        Args:
            components: List of components with change_type:
                - change_type: add, change, delete, conversion
                - component_type: EI, EO, EQ
                - complexity: low, average, high
                - original_fp: For delete, the original FP value

        Returns:
            EnhancementFPResult as dictionary
        """
        return self.enhancement_calculator.calculate(components)


# Export for easy import
__all__ = [
    "FPMethodologyService",
    "FPCalculationResult",
]
