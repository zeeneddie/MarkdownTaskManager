"""
Task Generation Pydantic Schemas
Week 23-24 Implementation

API request/response schemas for the Self-Questioning feature.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class GeneratedTaskType(str, Enum):
    FAILURE_RETRY = "FAILURE_RETRY"
    EDGE_CASE_TEST = "EDGE_CASE_TEST"
    SKILL_EXPANSION = "SKILL_EXPANSION"
    VALIDATION_TEST = "VALIDATION_TEST"
    PATTERN_PRACTICE = "PATTERN_PRACTICE"
    EXPLORATION = "EXPLORATION"


class TaskDifficulty(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class TaskSource(str, Enum):
    AGENT = "AGENT"
    ATTRIBUTION = "ATTRIBUTION"
    VALIDATION = "VALIDATION"
    EXPLORATION = "EXPLORATION"


class SkillGapSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    IMPORTANT = "IMPORTANT"
    MINOR = "MINOR"


class LessonType(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    INSIGHT = "INSIGHT"


class ImprovementTrend(str, Enum):
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DECLINING = "DECLINING"


class SkillGapEvidenceType(str, Enum):
    ATTRIBUTION_FAILURE = "ATTRIBUTION_FAILURE"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    PATTERN_MISSING = "PATTERN_MISSING"


# =============================================================================
# Nested Schemas
# =============================================================================

class TaskScenarioInput(BaseModel):
    """Scenario for a training task."""
    description: str
    context: Dict[str, Any] = Field(default_factory=dict)
    constraints: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list, alias="successCriteria")
    related_patterns: Optional[List[str]] = Field(default=None, alias="relatedPatterns")
    focus_areas: Optional[List[str]] = Field(default=None, alias="focusAreas")

    model_config = ConfigDict(populate_by_name=True)


class ExpectedOutcomeInput(BaseModel):
    """Expected outcome for a training task."""
    learning_objective: str = Field(alias="learningObjective")
    expected_success_rate: float = Field(default=0.7, alias="expectedSuccessRate", ge=0.0, le=1.0)
    target_skills: List[str] = Field(default_factory=list, alias="targetSkills")
    improvement_metrics: List[str] = Field(default_factory=list, alias="improvementMetrics")

    model_config = ConfigDict(populate_by_name=True)


class TrainingLessonInput(BaseModel):
    """A lesson learned from training."""
    lesson_id: str = Field(alias="lessonId")
    type: LessonType
    description: str
    applicable_scenarios: List[str] = Field(default_factory=list, alias="applicableScenarios")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    model_config = ConfigDict(populate_by_name=True)


class SkillGapEvidenceInput(BaseModel):
    """Evidence supporting a skill gap."""
    type: SkillGapEvidenceType
    source_id: str = Field(alias="sourceId")
    description: str
    timestamp: datetime

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# Training Task Schemas
# =============================================================================

class TrainingTaskCreate(BaseModel):
    """Create a new training task."""
    agent_id: str = Field(alias="agentId")
    agent_name: str = Field(alias="agentName")
    task_type: GeneratedTaskType = Field(alias="taskType")
    scenario: TaskScenarioInput
    expected_outcome: ExpectedOutcomeInput = Field(alias="expectedOutcome")
    difficulty: TaskDifficulty = TaskDifficulty.MEDIUM
    source: TaskSource
    parent_attribution_id: Optional[UUID] = Field(default=None, alias="parentAttributionId")
    parent_validation_id: Optional[str] = Field(default=None, alias="parentValidationId")
    skill_gap_id: Optional[UUID] = Field(default=None, alias="skillGapId")
    priority: int = Field(default=50, ge=0, le=100)
    estimated_duration_ms: int = Field(default=300000, alias="estimatedDurationMs")
    max_attempts: int = Field(default=3, alias="maxAttempts")

    model_config = ConfigDict(populate_by_name=True)


class TrainingTaskResponse(BaseModel):
    """Training task response."""
    id: UUID
    agent_id: str = Field(alias="agentId")
    agent_name: str = Field(alias="agentName")
    task_type: GeneratedTaskType = Field(alias="taskType")
    difficulty: TaskDifficulty
    source: TaskSource
    status: TaskStatus

    # Scenario (flattened for response)
    scenario_description: str = Field(alias="scenarioDescription")
    scenario_context: Dict[str, Any] = Field(alias="scenarioContext")
    scenario_constraints: List[str] = Field(alias="scenarioConstraints")
    scenario_success_criteria: List[str] = Field(alias="scenarioSuccessCriteria")

    # Expected outcome
    learning_objective: str = Field(alias="learningObjective")
    expected_success_rate: float = Field(alias="expectedSuccessRate")
    target_skills: List[str] = Field(alias="targetSkills")

    # Relationships
    parent_attribution_id: Optional[UUID] = Field(default=None, alias="parentAttributionId")
    skill_gap_id: Optional[UUID] = Field(default=None, alias="skillGapId")

    # Priority and estimation
    priority: int
    estimated_duration_ms: int = Field(alias="estimatedDurationMs")

    # Execution
    execution_attempts: int = Field(alias="executionAttempts")
    max_attempts: int = Field(alias="maxAttempts")

    # Timestamps
    created_at: datetime = Field(alias="createdAt")
    started_at: Optional[datetime] = Field(default=None, alias="startedAt")
    completed_at: Optional[datetime] = Field(default=None, alias="completedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# =============================================================================
# Task Result Schemas
# =============================================================================

class ActualOutcomeInput(BaseModel):
    """Actual outcome from executing a task."""
    learning_achieved: List[str] = Field(default_factory=list, alias="learningAchieved")
    skills_improved: List[str] = Field(default_factory=list, alias="skillsImproved")
    unexpected_learnings: List[str] = Field(default_factory=list, alias="unexpectedLearnings")

    model_config = ConfigDict(populate_by_name=True)


class TaskMetricsInput(BaseModel):
    """Metrics from task execution."""
    duration: int
    attempts: int = 1
    validation_passed: bool = Field(default=False, alias="validationPassed")
    confidence_score: float = Field(default=0.0, alias="confidenceScore", ge=0.0, le=1.0)

    model_config = ConfigDict(populate_by_name=True)


class TrainingTaskResultCreate(BaseModel):
    """Create a training task result."""
    task_id: UUID = Field(alias="taskId")
    agent_id: str = Field(alias="agentId")
    success: bool
    actual_outcome: ActualOutcomeInput = Field(alias="actualOutcome")
    metrics: TaskMetricsInput
    lessons: List[TrainingLessonInput] = Field(default_factory=list)
    follow_up_tasks: List[Dict[str, Any]] = Field(default_factory=list, alias="followUpTasks")
    attribution_id: Optional[UUID] = Field(default=None, alias="attributionId")

    model_config = ConfigDict(populate_by_name=True)


class TrainingTaskResultResponse(BaseModel):
    """Training task result response."""
    id: UUID
    task_id: UUID = Field(alias="taskId")
    agent_id: str = Field(alias="agentId")
    success: bool

    # Actual outcome
    learning_achieved: List[str] = Field(alias="learningAchieved")
    skills_improved: List[str] = Field(alias="skillsImproved")
    unexpected_learnings: List[str] = Field(alias="unexpectedLearnings")

    # Metrics
    duration_ms: int = Field(alias="durationMs")
    attempts: int
    validation_passed: bool = Field(alias="validationPassed")
    confidence_score: float = Field(alias="confidenceScore")

    # Lessons and follow-ups
    lessons: List[Dict[str, Any]]
    follow_up_tasks: List[Dict[str, Any]] = Field(alias="followUpTasks")

    attribution_id: Optional[UUID] = Field(default=None, alias="attributionId")
    completed_at: datetime = Field(alias="completedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# =============================================================================
# Skill Gap Schemas
# =============================================================================

class SkillGapCreate(BaseModel):
    """Create a new skill gap."""
    agent_id: str = Field(alias="agentId")
    agent_name: str = Field(alias="agentName")
    description: str
    area: str
    severity: SkillGapSeverity = SkillGapSeverity.IMPORTANT
    evidence: List[SkillGapEvidenceInput] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class SkillGapResponse(BaseModel):
    """Skill gap response."""
    id: UUID
    agent_id: str = Field(alias="agentId")
    agent_name: str = Field(alias="agentName")
    description: str
    area: str
    severity: SkillGapSeverity
    evidence: List[Dict[str, Any]]
    addressed: bool
    identified_at: datetime = Field(alias="identifiedAt")
    addressed_at: Optional[datetime] = Field(default=None, alias="addressedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# =============================================================================
# Metrics Schemas
# =============================================================================

class ImprovementMetricsResponse(BaseModel):
    """Improvement metrics for an agent."""
    id: UUID
    agent_id: str = Field(alias="agentId")

    # Period
    period_start: datetime = Field(alias="periodStart")
    period_end: datetime = Field(alias="periodEnd")

    # Task metrics
    tasks_generated: int = Field(alias="tasksGenerated")
    tasks_completed: int = Field(alias="tasksCompleted")
    tasks_successful: int = Field(alias="tasksSuccessful")
    tasks_failed: int = Field(alias="tasksFailed")

    # Learning metrics
    skill_gaps_identified: int = Field(alias="skillGapsIdentified")
    skill_gaps_addressed: int = Field(alias="skillGapsAddressed")
    lessons_learned: int = Field(alias="lessonsLearned")
    patterns_discovered: int = Field(alias="patternsDiscovered")

    # Performance changes
    success_rate_change: float = Field(alias="successRateChange")
    confidence_change: float = Field(alias="confidenceChange")
    estimation_accuracy_change: float = Field(alias="estimationAccuracyChange")

    trend: ImprovementTrend

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# =============================================================================
# Generation Strategy Schemas
# =============================================================================

class GenerationStrategyInput(BaseModel):
    """Input for updating generation strategy."""
    focus_areas: List[str] = Field(default_factory=list, alias="focusAreas")
    difficulty_preference: TaskDifficulty = Field(default=TaskDifficulty.MEDIUM, alias="difficultyPreference")
    max_tasks_per_session: int = Field(default=5, alias="maxTasksPerSession", ge=1, le=20)
    cooldown_period_ms: int = Field(default=3600000, alias="cooldownPeriodMs", ge=0)
    type_weights: Dict[GeneratedTaskType, float] = Field(default_factory=dict, alias="typeWeights")

    model_config = ConfigDict(populate_by_name=True)


class GenerationStrategyResponse(BaseModel):
    """Generation strategy response."""
    id: UUID
    agent_id: str = Field(alias="agentId")
    focus_areas: List[str] = Field(alias="focusAreas")
    difficulty_preference: TaskDifficulty = Field(alias="difficultyPreference")
    max_tasks_per_session: int = Field(alias="maxTasksPerSession")
    cooldown_period_ms: int = Field(alias="cooldownPeriodMs")
    type_weights: Dict[str, float] = Field(alias="typeWeights")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# =============================================================================
# API Request/Response Schemas
# =============================================================================

class GenerateTasksRequest(BaseModel):
    """Request to generate training tasks for an agent."""
    agent_id: str = Field(alias="agentId")
    strategy: Optional[GenerationStrategyInput] = None
    target_skill_gaps: Optional[List[UUID]] = Field(default=None, alias="targetSkillGaps")
    max_tasks: int = Field(default=5, alias="maxTasks", ge=1, le=20)

    model_config = ConfigDict(populate_by_name=True)


class GenerateTasksResponse(BaseModel):
    """Response from task generation."""
    tasks: List[TrainingTaskResponse]
    skill_gaps_targeted: List[SkillGapResponse] = Field(alias="skillGapsTargeted")
    estimated_training_time_ms: int = Field(alias="estimatedTrainingTimeMs")

    model_config = ConfigDict(populate_by_name=True)


class ExecuteTaskRequest(BaseModel):
    """Request to execute a training task."""
    task_id: UUID = Field(alias="taskId")
    max_attempts: int = Field(default=3, alias="maxAttempts", ge=1, le=10)

    model_config = ConfigDict(populate_by_name=True)


class ExecuteTaskResponse(BaseModel):
    """Response from task execution."""
    result: TrainingTaskResultResponse
    experience_updated: bool = Field(alias="experienceUpdated")
    follow_up_tasks_generated: int = Field(alias="followUpTasksGenerated")

    model_config = ConfigDict(populate_by_name=True)


class GetSkillGapsRequest(BaseModel):
    """Request to get skill gaps."""
    agent_id: str = Field(alias="agentId")
    min_severity: Optional[SkillGapSeverity] = Field(default=None, alias="minSeverity")
    include_addressed: bool = Field(default=False, alias="includeAddressed")

    model_config = ConfigDict(populate_by_name=True)


class GetSkillGapsResponse(BaseModel):
    """Response with skill gaps."""
    skill_gaps: List[SkillGapResponse] = Field(alias="skillGaps")
    total_gaps: int = Field(alias="totalGaps")
    critical_gaps: int = Field(alias="criticalGaps")
    addressed_gaps: int = Field(alias="addressedGaps")

    model_config = ConfigDict(populate_by_name=True)


class GetMetricsRequest(BaseModel):
    """Request to get improvement metrics."""
    agent_id: str = Field(alias="agentId")
    period_days: int = Field(default=7, alias="periodDays", ge=1, le=90)

    model_config = ConfigDict(populate_by_name=True)


class GetMetricsResponse(BaseModel):
    """Response with improvement metrics."""
    metrics: ImprovementMetricsResponse
    historical_metrics: List[ImprovementMetricsResponse] = Field(alias="historicalMetrics")

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# List/Query Schemas
# =============================================================================

class TrainingTaskQuery(BaseModel):
    """Query parameters for listing training tasks."""
    agent_id: Optional[str] = Field(default=None, alias="agentId")
    task_type: Optional[GeneratedTaskType] = Field(default=None, alias="taskType")
    status: Optional[TaskStatus] = None
    difficulty: Optional[TaskDifficulty] = None
    source: Optional[TaskSource] = None
    min_priority: int = Field(default=0, alias="minPriority", ge=0, le=100)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, alias="pageSize", ge=1, le=100)

    model_config = ConfigDict(populate_by_name=True)


class TrainingTaskListResponse(BaseModel):
    """Paginated list of training tasks."""
    items: List[TrainingTaskResponse]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")
    total_pages: int = Field(alias="totalPages")

    model_config = ConfigDict(populate_by_name=True)


class TaskGenerationSummary(BaseModel):
    """Summary of task generation activity."""
    total_tasks: int = Field(alias="totalTasks")
    pending_tasks: int = Field(alias="pendingTasks")
    completed_tasks: int = Field(alias="completedTasks")
    failed_tasks: int = Field(alias="failedTasks")
    success_rate: float = Field(alias="successRate")
    total_skill_gaps: int = Field(alias="totalSkillGaps")
    unaddressed_skill_gaps: int = Field(alias="unaddressedSkillGaps")
    agents_active: int = Field(alias="agentsActive")

    model_config = ConfigDict(populate_by_name=True)
