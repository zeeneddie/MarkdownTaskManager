# Contracts Module
# Clean interfaces for decoupling Brown Paper, Migration, and Quality workflows
#
# Architecture: docs/architecture/workflow-separation-plan.md
# Phase: Fase 21.5 (Week 145-146)

from .analysis_contract import (
    AnalysisContract,
    AnalysisSourceType,
    ProjectInfo,
    DomainSummary,
    ModuleSummary,
    EpicSummary,
    FeatureSummary,
    BusinessRuleSummary,
)
from .stability_contract import (
    StabilityInfo,
    StabilityCategorySummary,
    StabilityFindingSummary,
)
from .quality_contract import (
    QualityContract,
    QualityScanResult,
    QualityGateResult,
    QualityGateStatus,
    QualitySchedule,
    ScheduleType,
    QualityRuleViolation,
)

__all__ = [
    # Analysis Contract
    "AnalysisContract",
    "AnalysisSourceType",
    "ProjectInfo",
    "DomainSummary",
    "ModuleSummary",
    "EpicSummary",
    "FeatureSummary",
    "BusinessRuleSummary",
    # Stability Contract
    "StabilityInfo",
    "StabilityCategorySummary",
    "StabilityFindingSummary",
    # Quality Contract
    "QualityContract",
    "QualityScanResult",
    "QualityGateResult",
    "QualityGateStatus",
    "QualitySchedule",
    "ScheduleType",
    "QualityRuleViolation",
]
