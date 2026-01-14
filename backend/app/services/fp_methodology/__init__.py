# FP Methodology Module
# IFPUG CPM 4.3.1 compliant Function Point calculation
#
# Fixes fundamental methodology violations:
# - Component type validation (ILF/EIF/EI/EO/EQ rules)
# - Enhancement FP calculator for maintenance work
# - Work type classifier
# - VAF deprecation warnings
#
# Architecture: docs/roadmap/phases/fase-22-fp-methodology.md
# Phase: Fase 22 (Week 146-147)

from .validator import (
    FPComponentValidator,
    ValidationResult,
    ValidationSeverity,
)
from .enhancement_calculator import (
    EnhancementFPCalculator,
    EnhancementFPResult,
    ChangeType,
)
from .work_type_classifier import (
    WorkTypeClassifier,
    WorkType,
    WorkTypeClassification,
    EstimationMethod,
)

__all__ = [
    # Validator
    "FPComponentValidator",
    "ValidationResult",
    "ValidationSeverity",
    # Enhancement Calculator
    "EnhancementFPCalculator",
    "EnhancementFPResult",
    "ChangeType",
    # Work Type Classifier
    "WorkTypeClassifier",
    "WorkType",
    "WorkTypeClassification",
    "EstimationMethod",
]
