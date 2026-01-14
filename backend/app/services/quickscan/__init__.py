"""
Legacy Quickscan Service.

Fase 24 - A1: 15-minute automated legacy assessment tool.
Provides Go/No-Go decision for legacy modernization projects.
"""

from .models import (
    QuickscanConfig,
    QuickscanResult,
    TechnologyStack,
    ComplexityScore,
    RiskAssessment,
    EffortEstimate,
    Recommendation,
    ModernizationApproach,
    QuickscanReport,
)

from .service import (
    LegacyQuickscanService,
    create_quickscan_service,
)

__all__ = [
    # Models
    "QuickscanConfig",
    "QuickscanResult",
    "TechnologyStack",
    "ComplexityScore",
    "RiskAssessment",
    "EffortEstimate",
    "Recommendation",
    "ModernizationApproach",
    "QuickscanReport",
    # Service
    "LegacyQuickscanService",
    "create_quickscan_service",
]
