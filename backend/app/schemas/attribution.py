"""
Attribution Pydantic Schemas
Week 21-22 Implementation
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID


# ============================================================================
# Enums
# ============================================================================

class OutcomeType(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"


class ImpactLevel(str, Enum):
    CRITICAL = "CRITICAL"
    IMPORTANT = "IMPORTANT"
    MINOR = "MINOR"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class CausalFactorType(str, Enum):
    PATTERN_REUSE = "PATTERN_REUSE"
    EARLY_VALIDATION = "EARLY_VALIDATION"
    CLEAR_SPECIFICATION = "CLEAR_SPECIFICATION"
    TEST_COVERAGE = "TEST_COVERAGE"
    SECURITY_SCAN = "SECURITY_SCAN"
    MISSING_EDGE_CASE = "MISSING_EDGE_CASE"
    INCOMPLETE_VALIDATION = "INCOMPLETE_VALIDATION"
    DEPENDENCY_ISSUE = "DEPENDENCY_ISSUE"
    AMBIGUOUS_REQUIREMENT = "AMBIGUOUS_REQUIREMENT"
    RESOURCE_CONSTRAINT = "RESOURCE_CONSTRAINT"


class FeedbackType(str, Enum):
    SUCCESS_REINFORCEMENT = "SUCCESS_REINFORCEMENT"
    FAILURE_CORRECTION = "FAILURE_CORRECTION"
    PATTERN_UPDATE = "PATTERN_UPDATE"


class LessonType(str, Enum):
    DO_MORE = "DO_MORE"
    DO_LESS = "DO_LESS"
    AVOID = "AVOID"
    TRY_ALTERNATIVE = "TRY_ALTERNATIVE"


class AdjustmentType(str, Enum):
    WEIGHT_UPDATE = "WEIGHT_UPDATE"
    PATTERN_ADD = "PATTERN_ADD"
    PATTERN_REMOVE = "PATTERN_REMOVE"
    THRESHOLD_CHANGE = "THRESHOLD_CHANGE"


class ValidationPhase(str, Enum):
    LINTING = "LINTING"
    TYPE_CHECK = "TYPE_CHECK"
    STYLE = "STYLE"
    UNIT_TEST = "UNIT_TEST"
    E2E_TEST = "E2E_TEST"


class ErrorSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


# ============================================================================
# Input Schemas
# ============================================================================

class StepDataInput(BaseModel):
    """Input data for a single step in task execution."""
    id: str
    name: str
    agent_id: str
    succeeded: bool
    duration: int  # milliseconds
    expected_duration: int
    retry_count: Optional[int] = 0
    experience_consulted: Optional[bool] = False
    pattern_used: Optional[str] = None
    is_critical_path: Optional[bool] = False


class QualityGateResultInput(BaseModel):
    """Input data for quality gate results."""
    gate_type: str
    gate_name: str
    passed: bool
    issues_caught: int = 0
    false_positives: Optional[int] = 0
    total_checks: int = 0


class ValidationErrorInput(BaseModel):
    """Input data for validation errors."""
    code: str
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    severity: ErrorSeverity = ErrorSeverity.ERROR


class ValidationResultInput(BaseModel):
    """Input data for validation results."""
    phase: str
    iteration: int
    passed: bool
    errors: List[ValidationErrorInput] = []
    fix_applied: Optional[str] = None
    time_to_fix: Optional[int] = None


class TaskOutcomeInput(BaseModel):
    """Input for recording a task outcome."""
    task_id: str
    workflow_id: str
    agent_id: str
    agent_name: str
    outcome_type: OutcomeType
    steps: List[StepDataInput]
    quality_gate_results: List[QualityGateResultInput] = []
    validation_history: List[ValidationResultInput] = []
    duration_ms: Optional[int] = None


# ============================================================================
# Response Schemas
# ============================================================================

class AttributedStepResponse(BaseModel):
    """Response schema for an attributed step."""
    model_config = ConfigDict(populate_by_name=True, ser_json_timedelta='iso8601')

    step_id: str = Field(alias="stepId", serialization_alias="step_id")
    step_name: str = Field(alias="stepName", serialization_alias="step_name")
    agent_id: str = Field(alias="agentId", serialization_alias="agent_id")
    impact: ImpactLevel
    impact_score: float = Field(alias="impactScore", serialization_alias="impact_score", ge=-1.0, le=1.0)
    reasoning: str
    duration: int
    retry_count: int = Field(alias="retryCount", serialization_alias="retry_count")
    experience_used: bool = Field(alias="experienceUsed", serialization_alias="experience_used")
    pattern_applied: Optional[str] = Field(None, alias="patternApplied", serialization_alias="pattern_applied")


class CausalFactorResponse(BaseModel):
    """Response schema for a causal factor."""
    model_config = ConfigDict(populate_by_name=True)

    factor_id: str = Field(alias="factorId", serialization_alias="factor_id")
    factor_type: CausalFactorType = Field(alias="factorType", serialization_alias="factor_type")
    description: str
    contribution: float = Field(ge=-1.0, le=1.0)
    evidence: List[str]
    related_steps: List[str] = Field(alias="relatedSteps", serialization_alias="related_steps")


class QualityGateAttributionResponse(BaseModel):
    """Response schema for quality gate attribution."""
    gate_type: str
    gate_name: str
    passed: bool
    issues_caught: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    total_checks: int = 0
    effectiveness: float = Field(default=0.0, ge=0.0, le=1.0)
    recommended_action: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Response schema for validation errors."""
    code: str
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    severity: ErrorSeverity


class ValidationAttributionResponse(BaseModel):
    """Response schema for validation attribution."""
    phase: ValidationPhase
    iteration: int
    passed: bool
    errors: List[ValidationErrorResponse] = []
    fix_applied: Optional[str] = None
    time_to_fix: Optional[int] = None


class AttributionResponse(BaseModel):
    """Full attribution analysis response."""
    id: str
    task_id: str
    workflow_id: str
    agent_id: str
    agent_name: str
    outcome: OutcomeType
    key_steps: List[AttributedStepResponse]
    causal_factors: List[CausalFactorResponse]
    quality_gate_results: List[QualityGateAttributionResponse]
    validation_history: List[ValidationAttributionResponse]
    confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    created_at: datetime
    analyzed_at: datetime

    class Config:
        from_attributes = True


class LessonResponse(BaseModel):
    """Response schema for a lesson learned."""
    lesson_id: str
    lesson_type: LessonType
    description: str
    context: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class AdjustmentResponse(BaseModel):
    """Response schema for recommended adjustments."""
    adjustment_type: AdjustmentType
    target: str
    current_value: str
    recommended_value: str
    reasoning: str


class AttributionFeedbackResponse(BaseModel):
    """Response schema for attribution feedback."""
    attribution_id: str
    agent_id: str
    feedback_type: FeedbackType
    lessons: List[LessonResponse]
    recommended_adjustments: List[AdjustmentResponse]
    delivered: bool
    delivered_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Statistics & Metrics Schemas
# ============================================================================

class RankedFactorResponse(BaseModel):
    """Response for ranked causal factors."""
    factor: CausalFactorType
    description: str
    frequency: int
    average_contribution: float
    rank: int


class QualityGateStatsResponse(BaseModel):
    """Response for quality gate statistics."""
    gate_type: str
    total_checks: int
    issues_caught: int
    false_positive_rate: float
    false_negative_rate: float
    effectiveness: float


class AgentPerformanceMetricsResponse(BaseModel):
    """Response for agent performance metrics."""
    agent_id: str
    agent_name: str
    period_start: datetime
    period_end: datetime
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    partial_tasks: int
    success_rate: float
    average_confidence: float
    top_success_factors: List[RankedFactorResponse]
    top_failure_patterns: List[RankedFactorResponse]
    quality_gate_effectiveness: List[QualityGateStatsResponse]
    improvement_trend: float


# ============================================================================
# List/Query Schemas
# ============================================================================

class AttributionListResponse(BaseModel):
    """Paginated list of attributions."""
    items: List[AttributionResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AttributionQuery(BaseModel):
    """Query parameters for attribution search."""
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    outcome: Optional[OutcomeType] = None
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class FeedbackQuery(BaseModel):
    """Query parameters for feedback search."""
    agent_id: Optional[str] = None
    feedback_type: Optional[FeedbackType] = None
    delivered: Optional[bool] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class BatchAnalyzeRequest(BaseModel):
    """Request for batch analysis."""
    outcome_ids: List[UUID]


class BatchDeliverFeedbackRequest(BaseModel):
    """Request for batch feedback delivery."""
    feedback_ids: Optional[List[UUID]] = None
    agent_id: Optional[str] = None


# ============================================================================
# Summary Schemas
# ============================================================================

class AttributionSummary(BaseModel):
    """Summary of attribution analysis."""
    total_attributions: int
    success_count: int
    failure_count: int
    partial_count: int
    average_confidence: float
    top_success_factor: Optional[str] = None
    top_failure_factor: Optional[str] = None


class AgentSummary(BaseModel):
    """Summary of agent attributions."""
    agent_id: str
    agent_name: str
    total_attributions: int
    success_count: int
    failure_count: int
    partial_count: int
    average_confidence: float
    pending_feedback: int
