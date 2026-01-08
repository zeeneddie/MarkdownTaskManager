# Stability Analysis Framework
# Fase 21: ASP Application Stability Analyzer
# Week 143-146

from .types import (
    ResourceType,
    LeakPatternType,
    StabilityCategory,
    SeverityLevel,
    ResourceOperation,
    LeakFinding,
    LeakReport,
    CategoryFinding,
    StabilityReport,
)
from .base_detector import BaseResourceLeakDetector
from .detector_service import (
    ResourceLeakDetectorService,
    create_detector_service,
    analyze_with_all_analyzers,
)
from .brown_paper_integration import (
    BrownPaperStabilityIntegration,
    StabilityIntegrationResult,
    get_brown_paper_stability_integration,
)
from .quality_gate_integration import (
    StabilityQualityGateService,
    StabilityGateResult,
    StabilityGateStatus,
    StabilityThresholds,
    get_stability_quality_gate_service,
    WORKFLOW_STABILITY_THRESHOLDS,
)

__all__ = [
    # Enums
    "ResourceType",
    "LeakPatternType",
    "StabilityCategory",
    "SeverityLevel",
    "StabilityGateStatus",
    # Data classes
    "ResourceOperation",
    "LeakFinding",
    "LeakReport",
    "CategoryFinding",
    "StabilityReport",
    "StabilityThresholds",
    "StabilityGateResult",
    # Services
    "BaseResourceLeakDetector",
    "ResourceLeakDetectorService",
    "create_detector_service",
    "analyze_with_all_analyzers",
    # Brown Paper Integration
    "BrownPaperStabilityIntegration",
    "StabilityIntegrationResult",
    "get_brown_paper_stability_integration",
    # Quality Gate Integration
    "StabilityQualityGateService",
    "get_stability_quality_gate_service",
    "WORKFLOW_STABILITY_THRESHOLDS",
]
