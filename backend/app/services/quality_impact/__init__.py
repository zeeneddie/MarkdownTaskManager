"""
Quality Impact Mapping Services.

Fase 29: Links quality issues to functionality (Epic/Feature/Story level).
Provides business impact visibility for security, performance, memory leaks,
duplication, and error handling issues.
"""

from .types import (
    IssueType,
    ImpactSeverity,
    RegulatoryRisk,
    QualityIssue,
    FunctionalityImpact,
    QualityImpactMapping,
    ImpactSummary,
    ProjectImpactReport,
)
from .code_to_functionality_mapper import CodeToFunctionalityMapper
from .security_impact_mapper import SecurityImpactMapper
from .performance_impact_mapper import PerformanceImpactMapper
from .memory_leak_impact_mapper import MemoryLeakImpactMapper
from .impact_score_calculator import ImpactScoreCalculator
from .quality_impact_service import (
    QualityImpactMappingService,
    create_quality_impact_service,
)

__all__ = [
    # Types
    "IssueType",
    "ImpactSeverity",
    "RegulatoryRisk",
    "QualityIssue",
    "FunctionalityImpact",
    "QualityImpactMapping",
    "ImpactSummary",
    "ProjectImpactReport",
    # Mappers
    "CodeToFunctionalityMapper",
    "SecurityImpactMapper",
    "PerformanceImpactMapper",
    "MemoryLeakImpactMapper",
    # Calculator
    "ImpactScoreCalculator",
    # Service
    "QualityImpactMappingService",
    "create_quality_impact_service",
]
