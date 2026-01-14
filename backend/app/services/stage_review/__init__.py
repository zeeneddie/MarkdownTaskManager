"""
Stage Review Service Module.

Fase 23.6: Stage-based LLM Council Review System.

Phase 24.1: Core service with multi-model reviews
Phase 24.2: Artifact improvement service
Phase 24.3: Confucius integration (StageReviewExtension)
Phase 24.4: Performance tracking and persistence

Provides multi-model code reviews at each development stage with
consensus calculation, threshold evaluation, and automatic improvement.
"""

from .types import (
    # Enums
    StageType,
    IssueSeverity,
    IssueCategory,
    ReviewStatus,
    ReviewDecision,
    ModelRole,
    # Data classes
    ParsedIssue,
    ModelReviewResult,
    ConsolidatedIssue,
    ReviewRoundResult,
    ReviewResult,
    StageCouncilConfig,
    ModelPerformance,
    StagePerformance,
)

from .stage_council_config import (
    STAGE_COUNCIL_CONFIGS,
    MODEL_PROVIDER_MAP,
    get_stage_config,
    get_models_for_stage,
    get_provider_for_model,
    get_all_stage_types,
    get_default_config,
)

from .stage_review_service import (
    StageReviewService,
    create_stage_review_service,
)

from .artifact_improvement_service import (
    ArtifactImprovementService,
    ImprovementStrategy,
    ImprovementResult,
    create_artifact_improvement_service,
)

from .performance_tracking_service import (
    PerformanceTrackingService,
    ModelPerformanceReport,
    StagePerformanceReport,
    OverallPerformanceReport,
    create_performance_tracking_service,
)


__all__ = [
    # Enums
    "StageType",
    "IssueSeverity",
    "IssueCategory",
    "ReviewStatus",
    "ReviewDecision",
    "ModelRole",
    # Data classes
    "ParsedIssue",
    "ModelReviewResult",
    "ConsolidatedIssue",
    "ReviewRoundResult",
    "ReviewResult",
    "StageCouncilConfig",
    "ModelPerformance",
    "StagePerformance",
    # Configuration
    "STAGE_COUNCIL_CONFIGS",
    "MODEL_PROVIDER_MAP",
    "get_stage_config",
    "get_models_for_stage",
    "get_provider_for_model",
    "get_all_stage_types",
    "get_default_config",
    # Service
    "StageReviewService",
    "create_stage_review_service",
    # Artifact Improvement (Phase 24.2)
    "ArtifactImprovementService",
    "ImprovementStrategy",
    "ImprovementResult",
    "create_artifact_improvement_service",
    # Performance Tracking (Phase 24.4)
    "PerformanceTrackingService",
    "ModelPerformanceReport",
    "StagePerformanceReport",
    "OverallPerformanceReport",
    "create_performance_tracking_service",
]
