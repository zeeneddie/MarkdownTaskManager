"""
Agent Evolution API Endpoints

Provides REST API for:
- Experience management (CRUD)
- Successful pattern management
- Failure analysis tracking
- Guidance consultation (Self-Navigating)
- Learning task generation (Self-Questioning)
- Performance metrics
- Validation pipeline execution

Author: Claude Code (Week 17 Day 5)
Date: 2025-11-22
"""

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum
import logging

from app.services.experience_store_service import (
    get_experience_store,
    ExperienceStoreService,
    Experience,
    KeyDecision,
    SuccessfulPattern,
    FailureAnalysis,
    FailureType,
    EstimationAccuracy,
    QualityMetricsRecord,
    Complexity,
    WorkType,
    AgentRole,
    Outcome
)
import uuid
from app.services.agent_evolution_service import (
    get_evolution_service,
    AgentEvolutionService,
    TaskContext,
    Guidance,
    Attribution,
    LearningTask,
    PerformanceMetrics,
    EvolutionConfig
)
from app.services.validation_pipeline_service import (
    get_validation_service,
    ValidationPipelineService,
    ValidationResult,
    ValidationConfig,
    ValidationPhase,
    Language
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/evolution", tags=["agent-evolution"])


# ============================================================================
# Request/Response Models - Experiences
# ============================================================================

class AddExperienceRequest(BaseModel):
    """Request to add a new experience"""
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_role: str = Field(..., description="Agent role (felix, marcus, quinn, etc.)")
    work_type: str = Field(..., description="Type of work performed")
    task_description: str = Field(..., description="Description of the task")
    approach: str = Field(..., description="Approach taken to solve the task")
    outcome: str = Field(..., description="Outcome: success, partial, or failure")
    lessons_learned: List[str] = Field(default=[], description="Lessons learned")
    key_decisions: List[Dict[str, Any]] = Field(default=[], description="Key decisions made")
    duration: int = Field(..., description="Duration in seconds")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score 0-1")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")


class ExperienceResponse(BaseModel):
    """Response containing an experience"""
    id: str
    agent_id: str
    agent_role: str
    work_type: str
    task_description: str
    approach: str
    outcome: str
    lessons_learned: List[str]
    key_decisions: List[Dict[str, Any]]
    duration: int
    quality_score: float
    timestamp: datetime
    metadata: Dict[str, Any]


class SimilarExperiencesResponse(BaseModel):
    """Response with similar experiences"""
    experiences: List[Dict[str, Any]]
    query: str
    count: int


# ============================================================================
# Request/Response Models - Patterns
# ============================================================================

class AddPatternRequest(BaseModel):
    """Request to add a successful pattern"""
    pattern_name: str = Field(..., description="Name of the pattern")
    agent_role: str = Field(..., description="Agent role that discovered this")
    work_types: List[str] = Field(..., description="Applicable work types")
    context_keywords: List[str] = Field(..., description="Context keywords")
    description: str = Field(..., description="Pattern description")
    steps: List[str] = Field(..., description="Steps to apply the pattern")
    success_criteria: List[str] = Field(..., description="Success criteria")
    times_used: int = Field(default=0, description="Times this pattern was used")
    success_rate: float = Field(default=1.0, description="Success rate")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")


class PatternResponse(BaseModel):
    """Response containing a pattern"""
    id: str
    pattern_name: str
    agent_role: str
    work_types: List[str]
    context_keywords: List[str]
    description: str
    steps: List[str]
    success_criteria: List[str]
    times_used: int
    success_rate: float
    created_at: datetime
    metadata: Dict[str, Any]


# ============================================================================
# Request/Response Models - Failures
# ============================================================================

class AddFailureRequest(BaseModel):
    """Request to add a failure analysis"""
    agent_id: str = Field(..., description="Agent identifier")
    agent_role: str = Field(..., description="Agent role")
    work_type: str = Field(..., description="Work type")
    task_description: str = Field(..., description="Task that failed")
    failure_point: str = Field(..., description="Where the failure occurred")
    root_cause: str = Field(..., description="Root cause analysis")
    attempted_fixes: List[str] = Field(default=[], description="Fixes attempted")
    resolution: Optional[str] = Field(None, description="Final resolution if found")
    preventive_measures: List[str] = Field(default=[], description="Future prevention")
    severity: str = Field(default="medium", description="Severity: low, medium, high, critical")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")


class FailureResponse(BaseModel):
    """Response containing a failure analysis"""
    id: str
    agent_id: str
    agent_role: str
    work_type: str
    task_description: str
    failure_point: str
    root_cause: str
    attempted_fixes: List[str]
    resolution: Optional[str]
    preventive_measures: List[str]
    severity: str
    timestamp: datetime
    metadata: Dict[str, Any]


# ============================================================================
# Request/Response Models - Guidance & Learning
# ============================================================================

class GetGuidanceRequest(BaseModel):
    """Request for task guidance"""
    agent_id: str = Field(..., description="Agent identifier")
    agent_role: str = Field(..., description="Agent role")
    work_type: str = Field(..., description="Work type")
    task_description: str = Field(..., description="Task description")
    constraints: List[str] = Field(default=[], description="Task constraints")
    goals: List[str] = Field(default=[], description="Task goals")
    available_resources: List[str] = Field(default=[], description="Available resources")


class GuidanceResponse(BaseModel):
    """Response containing guidance"""
    confidence: float
    recommended_approach: str
    relevant_patterns: List[Dict[str, Any]]
    warnings: List[str]
    estimated_duration: int
    success_probability: float
    similar_experiences_count: int


class GenerateLearningTasksRequest(BaseModel):
    """Request to generate learning tasks"""
    agent_id: str = Field(..., description="Agent identifier")
    agent_role: str = Field(..., description="Agent role")
    max_tasks: int = Field(default=5, ge=1, le=20, description="Maximum tasks to generate")


class LearningTaskResponse(BaseModel):
    """Response containing a learning task"""
    task_id: str
    task_type: str
    description: str
    expected_outcome: str
    priority: str
    estimated_effort: int
    related_gap: str


# ============================================================================
# Request/Response Models - Outcome Analysis
# ============================================================================

class AnalyzeOutcomeRequest(BaseModel):
    """Request to analyze task outcome"""
    agent_id: str = Field(..., description="Agent identifier")
    agent_role: str = Field(..., description="Agent role")
    task_id: str = Field(..., description="Task identifier")
    steps_taken: List[Dict[str, Any]] = Field(..., description="Steps taken during task")
    outcome: str = Field(..., description="Outcome: success, partial, failure")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score")
    duration: int = Field(..., description="Duration in seconds")


class AttributionResponse(BaseModel):
    """Response containing outcome attribution"""
    task_id: str
    critical_steps: List[Dict[str, Any]]
    success_factors: List[str]
    improvement_areas: List[str]
    pattern_matches: List[Dict[str, Any]]
    overall_score: float
    recommendations: List[str]


# ============================================================================
# Request/Response Models - Performance Metrics
# ============================================================================

class PerformanceMetricsResponse(BaseModel):
    """Response containing performance metrics"""
    agent_id: str
    agent_role: str
    period_days: int
    total_tasks: int
    success_rate: float
    average_quality: float
    average_duration: int
    improvement_trend: float
    top_strengths: List[str]
    improvement_areas: List[str]
    estimation_accuracy: float


# ============================================================================
# Request/Response Models - Validation
# ============================================================================

class RunValidationRequest(BaseModel):
    """Request to run validation pipeline"""
    code: str = Field(..., description="Code to validate")
    language: str = Field(..., description="Language: python or typescript")
    phases: Optional[List[str]] = Field(None, description="Specific phases to run")
    max_iterations: int = Field(default=3, ge=1, le=10, description="Max fix iterations")
    stop_on_first_failure: bool = Field(default=False, description="Stop on first failure")
    required_coverage: Optional[float] = Field(None, ge=0.0, le=1.0, description="Required coverage")
    file_path: Optional[str] = Field(None, description="File path for tests")


class ValidationPhaseResultResponse(BaseModel):
    """Response for a single validation phase"""
    phase: str
    passed: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    duration: float
    tool_used: str
    output: Optional[str]


class ValidationResultResponse(BaseModel):
    """Response containing validation results"""
    overall_passed: bool
    phases_run: List[str]
    phase_results: List[ValidationPhaseResultResponse]
    total_errors: int
    total_warnings: int
    coverage: Optional[float]
    total_duration: float
    iterations: int


class IterateUntilValidRequest(BaseModel):
    """Request to iterate until code is valid"""
    code: str = Field(..., description="Code to validate and fix")
    language: str = Field(..., description="Language: python or typescript")
    max_iterations: int = Field(default=3, ge=1, le=10, description="Max iterations")


class IterateUntilValidResponse(BaseModel):
    """Response from iterate until valid"""
    final_code: str
    is_valid: bool
    iterations_used: int
    validation_result: ValidationResultResponse


# ============================================================================
# Experience Endpoints
# ============================================================================

@router.post("/experiences", response_model=ExperienceResponse, status_code=status.HTTP_201_CREATED)
async def add_experience(request: AddExperienceRequest):
    """
    Add a new experience to the store.

    This is part of Self-Attributing: logging outcomes for future learning.
    """
    try:
        store = get_experience_store()

        # Convert dict key_decisions to KeyDecision objects
        key_decisions = []
        for kd in request.key_decisions:
            key_decisions.append(KeyDecision(
                decision=kd.get("decision", ""),
                reasoning=kd.get("reasoning", kd.get("reason", "")),
                alternatives=kd.get("alternatives", []),
                outcome=kd.get("outcome", "neutral"),
                impact_score=kd.get("impact_score", 0.0)
            ))

        experience = Experience(
            id=str(uuid.uuid4()),
            agent_id=request.agent_id,
            agent_role=AgentRole(request.agent_role),
            work_type=WorkType(request.work_type),
            task_description=request.task_description,
            approach=request.approach,
            outcome=Outcome(request.outcome),
            lessons_learned=request.lessons_learned,
            key_decisions=key_decisions,
            duration=request.duration,
            quality_score=request.quality_score * 100,  # Convert 0-1 to 0-100
            timestamp=datetime.now(timezone.utc),
            metadata=request.metadata
        )

        experience_id = await store.add_experience(experience)

        # Retrieve and return the full experience
        saved = await store.get_experience(experience_id)
        if not saved:
            raise HTTPException(status_code=500, detail="Failed to retrieve saved experience")

        # Convert KeyDecision objects to dicts for response
        key_decisions_dicts = [
            {
                "decision": kd.decision,
                "reasoning": kd.reasoning,
                "alternatives": kd.alternatives,
                "outcome": kd.outcome,
                "impact_score": kd.impact_score
            }
            for kd in saved.key_decisions
        ]

        return ExperienceResponse(
            id=saved.id,
            agent_id=saved.agent_id,
            agent_role=saved.agent_role.value,
            work_type=saved.work_type.value,
            task_description=saved.task_description,
            approach=saved.approach,
            outcome=saved.outcome.value,
            lessons_learned=saved.lessons_learned,
            key_decisions=key_decisions_dicts,
            duration=saved.duration,
            quality_score=saved.quality_score / 100,  # Convert back to 0-1
            timestamp=saved.timestamp,
            metadata=saved.metadata
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding experience: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiences/{experience_id}", response_model=ExperienceResponse)
async def get_experience(experience_id: str):
    """Get a specific experience by ID"""
    try:
        store = get_experience_store()
        experience = await store.get_experience(experience_id)

        if not experience:
            raise HTTPException(status_code=404, detail="Experience not found")

        return ExperienceResponse(
            id=experience.id,
            agent_id=experience.agent_id,
            agent_role=experience.agent_role.value,
            work_type=experience.work_type.value,
            task_description=experience.task_description,
            approach=experience.approach,
            outcome=experience.outcome.value,
            lessons_learned=experience.lessons_learned,
            key_decisions=experience.key_decisions,
            duration=experience.duration,
            quality_score=experience.quality_score,
            timestamp=experience.timestamp,
            metadata=experience.metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting experience: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/experiences/search", response_model=SimilarExperiencesResponse)
async def search_similar_experiences(
    task_description: str,
    agent_role: Optional[str] = None,
    work_type: Optional[str] = None,
    limit: int = 10
):
    """
    Search for similar experiences using semantic search.

    This is part of Self-Navigating: finding relevant past experiences.
    """
    try:
        store = get_experience_store()

        role = AgentRole(agent_role) if agent_role else None
        wtype = WorkType(work_type) if work_type else None

        results = await store.find_similar_experiences(
            task_description=task_description,
            work_type=wtype,
            agent_role=role,
            limit=limit
        )

        experiences = []
        for exp, similarity in results:
            experiences.append({
                "id": exp.id,
                "agent_id": exp.agent_id,
                "agent_role": exp.agent_role.value,
                "work_type": exp.work_type.value,
                "task_description": exp.task_description,
                "approach": exp.approach,
                "outcome": exp.outcome.value,
                "quality_score": exp.quality_score,
                "similarity": similarity
            })

        return SimilarExperiencesResponse(
            experiences=experiences,
            query=task_description,
            count=len(experiences)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching experiences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/experiences/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experience(experience_id: str):
    """Delete an experience"""
    try:
        store = get_experience_store()
        await store.delete_experience(experience_id)
    except Exception as e:
        logger.error(f"Error deleting experience: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Pattern Endpoints
# ============================================================================

@router.post("/patterns", status_code=status.HTTP_201_CREATED)
async def add_pattern(request: AddPatternRequest):
    """Add a new successful pattern"""
    try:
        store = get_experience_store()
        now = datetime.now(timezone.utc)

        # Map API fields to service dataclass fields
        pattern = SuccessfulPattern(
            id=str(uuid.uuid4()),
            name=request.pattern_name,
            description=request.description,
            work_types=[WorkType(wt) for wt in request.work_types],
            applicable_contexts=request.context_keywords,
            steps=request.steps,
            success_count=request.times_used,
            failure_count=0,
            average_quality=request.success_rate * 100,  # Convert to 0-100
            created_at=now,
            last_used=now,
            created_by=request.agent_role  # Use agent_role as creator ID
        )

        pattern_id = await store.add_pattern(pattern)

        return {
            "id": pattern_id,
            "pattern_name": pattern.name,
            "agent_role": pattern.created_by,
            "work_types": [wt.value for wt in pattern.work_types],
            "context_keywords": pattern.applicable_contexts,
            "description": pattern.description,
            "steps": pattern.steps,
            "success_criteria": [],  # Not in service model
            "times_used": pattern.success_count,
            "success_rate": pattern.success_rate,
            "created_at": pattern.created_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/patterns/search")
async def search_applicable_patterns(
    context: str,
    work_type: str,
    limit: int = 5
):
    """Search for applicable patterns"""
    try:
        store = get_experience_store()
        wtype = WorkType(work_type)

        results = await store.find_applicable_patterns(
            context=context,
            work_type=wtype,
            limit=limit
        )

        patterns = []
        for pattern, similarity in results:
            patterns.append({
                "id": pattern.id,
                "pattern_name": pattern.name,  # Use 'name' field
                "description": pattern.description,
                "steps": pattern.steps,
                "success_rate": pattern.success_rate,
                "similarity": similarity
            })

        return {"patterns": patterns, "count": len(patterns)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Failure Analysis Endpoints
# ============================================================================

@router.post("/failures", status_code=status.HTTP_201_CREATED)
async def add_failure_analysis(request: AddFailureRequest):
    """Add a failure analysis for learning"""
    try:
        store = get_experience_store()

        # Map severity to FailureType
        severity_to_type = {
            "low": FailureType.LOGIC,
            "medium": FailureType.VALIDATION,
            "high": FailureType.QUALITY,
            "critical": FailureType.TIMEOUT
        }
        failure_type = severity_to_type.get(request.severity, FailureType.UNKNOWN)

        # Map API fields to service dataclass fields
        failure = FailureAnalysis(
            id=str(uuid.uuid4()),
            agent_id=request.agent_id,
            task_id=request.task_description[:50],  # Use truncated description as task_id
            work_type=WorkType(request.work_type),
            failure_type=failure_type,
            root_cause=request.root_cause,
            contributing_factors=request.attempted_fixes,  # Map attempted_fixes
            prevention_strategies=request.preventive_measures,
            similar_failures=[],
            timestamp=datetime.now(timezone.utc)
        )

        failure_id = await store.add_failure_analysis(failure)

        return {
            "id": failure_id,
            "agent_id": failure.agent_id,
            "agent_role": request.agent_role,  # Return original request value
            "work_type": failure.work_type.value,
            "task_description": request.task_description,
            "failure_point": request.failure_point,
            "root_cause": failure.root_cause,
            "attempted_fixes": failure.contributing_factors,
            "resolution": request.resolution,
            "preventive_measures": failure.prevention_strategies,
            "severity": request.severity,
            "timestamp": failure.timestamp
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/failures/search")
async def search_similar_failures(
    root_cause: str,
    work_type: Optional[str] = None,
    limit: int = 5
):
    """Search for similar failures"""
    try:
        store = get_experience_store()
        wtype = WorkType(work_type) if work_type else None

        results = await store.find_similar_failures(
            root_cause=root_cause,
            work_type=wtype,
            limit=limit
        )

        failures = []
        for failure, similarity in results:
            failures.append({
                "id": failure.id,
                "task_description": failure.task_id,  # Use task_id field
                "root_cause": failure.root_cause,
                "resolution": None,  # Not in service model
                "preventive_measures": failure.prevention_strategies,
                "similarity": similarity
            })

        return {"failures": failures, "count": len(failures)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching failures: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Guidance Endpoints (Self-Navigating)
# ============================================================================

@router.post("/guidance", response_model=GuidanceResponse)
async def get_guidance(request: GetGuidanceRequest):
    """
    Get guidance for a task based on past experiences.

    This is the Self-Navigating capability: "How did I do this before?"
    """
    try:
        evolution_service = get_evolution_service()

        context = TaskContext(
            work_type=WorkType(request.work_type),
            description=request.task_description,
            complexity=Complexity.MEDIUM,  # Default complexity
            constraints=request.constraints,
        )

        guidance = await evolution_service.consult_experience(
            agent_id=request.agent_id,
            agent_role=AgentRole(request.agent_role),
            context=context
        )

        return GuidanceResponse(
            confidence=guidance.confidence_score,
            recommended_approach=guidance.suggested_approach,
            relevant_patterns=[
                {
                    "name": p[0].pattern_name if hasattr(p[0], 'pattern_name') else str(p[0]),
                    "description": p[0].description if hasattr(p[0], 'description') else "",
                    "success_rate": p[1] if len(p) > 1 else 0.0
                }
                for p in guidance.pattern_matches
            ],
            warnings=guidance.warnings_from_past,
            estimated_duration=0,  # Not available in Guidance class
            success_probability=guidance.confidence_score,
            similar_experiences_count=len(guidance.relevant_experiences)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting guidance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Learning Task Endpoints (Self-Questioning)
# ============================================================================

@router.post("/learning-tasks", response_model=List[LearningTaskResponse])
async def generate_learning_tasks(request: GenerateLearningTasksRequest):
    """
    Generate learning tasks for an agent.

    This is the Self-Questioning capability: "What should I learn?"
    """
    try:
        evolution_service = get_evolution_service()

        tasks = await evolution_service.generate_learning_tasks(
            agent_id=request.agent_id,
            agent_role=AgentRole(request.agent_role),
            max_tasks=request.max_tasks
        )

        return [
            LearningTaskResponse(
                task_id=t.id,
                task_type=t.work_type.value if hasattr(t.work_type, 'value') else str(t.work_type),
                description=t.description,
                expected_outcome=t.learning_goal,
                priority=t.expected_difficulty.value if hasattr(t.expected_difficulty, 'value') else str(t.expected_difficulty),
                estimated_effort=1,  # Default effort
                related_gap=t.knowledge_gap
            )
            for t in tasks
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating learning tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Outcome Analysis Endpoints (Self-Attributing)
# ============================================================================

@router.post("/analyze-outcome", response_model=AttributionResponse)
async def analyze_outcome(request: AnalyzeOutcomeRequest):
    """
    Analyze task outcome and attribute success/failure factors.

    This is the Self-Attributing capability: "Which steps were crucial?"
    """
    try:
        evolution_service = get_evolution_service()

        attribution = await evolution_service.analyze_outcome(
            agent_id=request.agent_id,
            agent_role=AgentRole(request.agent_role),
            task_id=request.task_id,
            steps_taken=request.steps_taken,
            outcome=Outcome(request.outcome),
            quality_score=request.quality_score,
            duration=request.duration
        )

        return AttributionResponse(
            task_id=attribution.task_id,
            critical_steps=[
                {
                    "step_name": a.step_name,
                    "contribution": a.contribution,
                    "reasoning": a.reasoning
                }
                for a in attribution.attributions
            ],
            success_factors=attribution.key_success_factors,
            improvement_areas=attribution.key_failure_factors,
            pattern_matches=[],  # Not available in Attribution class
            overall_score=attribution.total_score,
            recommendations=attribution.recommendations
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing outcome: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Performance Metrics Endpoints
# ============================================================================

@router.get("/metrics/{agent_id}", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    agent_id: str,
    agent_role: str,
    days: int = 30
):
    """Get performance metrics for an agent"""
    try:
        evolution_service = get_evolution_service()

        metrics = await evolution_service.get_performance_metrics(
            agent_id=agent_id,
            agent_role=AgentRole(agent_role),
            days=days
        )

        # Calculate period_days from period_start and period_end
        period_days = (metrics.period_end - metrics.period_start).days if metrics.period_end and metrics.period_start else days

        return PerformanceMetricsResponse(
            agent_id=metrics.agent_id,
            agent_role=metrics.agent_role.value if hasattr(metrics.agent_role, 'value') else str(metrics.agent_role),
            period_days=period_days,
            total_tasks=metrics.total_tasks,
            success_rate=metrics.success_rate,
            average_quality=metrics.average_quality_score,
            average_duration=int(metrics.average_duration),
            improvement_trend=0.0,  # Calculate from quality_trend if needed
            top_strengths=[],  # Not available in PerformanceMetrics class
            improvement_areas=[],  # Not available in PerformanceMetrics class
            estimation_accuracy=0.0  # Not available in PerformanceMetrics class
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/adapt")
async def adapt_evolution_config(agent_id: str, agent_role: str):
    """
    Adapt evolution configuration based on performance.

    Returns optimized config based on agent's track record.
    """
    try:
        evolution_service = get_evolution_service()

        config = await evolution_service.adapt_config(
            agent_id=agent_id,
            agent_role=AgentRole(agent_role)
        )

        return {
            "agent_id": agent_id,
            "agent_role": agent_role,
            "adapted_config": {
                "learning_rate": config.learning_rate,
                "experience_weight": config.experience_weight,
                "exploration_rate": config.exploration_rate,
                "attribution_depth": config.attribution_depth,
                "min_experience_confidence": config.min_experience_confidence,
                "max_experiences_to_consider": config.max_experiences_to_consider
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adapting config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Estimation Accuracy Endpoints
# ============================================================================

@router.post("/estimation-accuracy", status_code=status.HTTP_201_CREATED)
async def add_estimation_accuracy(
    agent_id: str,
    agent_role: str,
    work_type: str,
    task_id: str,
    estimated_hours: float,
    actual_hours: float,
    estimation_method: str = "default",
    factors: Dict[str, Any] = {}
):
    """Record estimation accuracy for learning"""
    try:
        store = get_experience_store()

        estimation = EstimationAccuracy(
            id="",
            agent_id=agent_id,
            task_id=task_id,
            work_type=WorkType(work_type),
            estimated_hours=estimated_hours,
            actual_hours=actual_hours,
            estimated_complexity=Complexity.MEDIUM,  # Default
            actual_complexity=Complexity.MEDIUM,  # Default
            factors=list(factors.keys()) if factors else [],
            underestimated_aspects=[],
            overestimated_aspects=[],
            timestamp=datetime.now(timezone.utc)
        )

        estimation_id = await store.add_estimation_accuracy(estimation)

        return {"id": estimation_id, "accuracy_percent": estimation.accuracy_percent}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding estimation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estimation-stats/{agent_id}")
async def get_estimation_stats(
    agent_id: str,
    work_type: Optional[str] = None,
    days: int = 90
):
    """Get estimation statistics for an agent"""
    try:
        store = get_experience_store()

        wtype = WorkType(work_type) if work_type else None

        stats = await store.get_agent_estimation_stats(
            agent_id=agent_id,
            work_type=wtype
        )

        return stats
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting estimation stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Quality Metrics Endpoints
# ============================================================================

@router.post("/quality-metrics", status_code=status.HTTP_201_CREATED)
async def add_quality_metrics(
    agent_id: str,
    agent_role: str,
    work_type: str,
    task_id: str,
    code_quality_score: float,
    test_coverage: float,
    security_score: float,
    documentation_score: float,
    maintainability_score: float,
    issues_found: int = 0,
    issues_fixed: int = 0,
    metadata: Dict[str, Any] = {}
):
    """Record quality metrics for tracking"""
    try:
        store = get_experience_store()

        metrics = QualityMetricsRecord(
            id="",
            agent_id=agent_id,
            task_id=task_id,
            work_type=WorkType(work_type),
            code_quality_score=code_quality_score,
            test_coverage=test_coverage,
            linting_errors=issues_found,  # Map issues_found to linting_errors
            type_errors=0,
            security_issues=int(100 - security_score) if security_score else 0,  # Convert score to issues count
            performance_score=maintainability_score,  # Map maintainability to performance
            documentation_score=documentation_score,
            timestamp=datetime.now(timezone.utc)
        )

        metrics_id = await store.add_quality_metrics(metrics)

        return {"id": metrics_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding quality metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality-trend/{agent_id}")
async def get_quality_trend(
    agent_id: str,
    work_type: Optional[str] = None,
    days: int = 90
):
    """Get quality metrics trend for an agent"""
    try:
        store = get_experience_store()

        wtype = WorkType(work_type) if work_type else None

        trend = await store.get_quality_trend(
            agent_id=agent_id,
            work_type=wtype,
            days=days
        )

        return trend
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting quality trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Validation Pipeline Endpoints
# ============================================================================

validation_router = APIRouter(prefix="/api/validation", tags=["validation-pipeline"])


@validation_router.post("/run", response_model=ValidationResultResponse)
async def run_validation(request: RunValidationRequest):
    """
    Run validation pipeline on code.

    Executes configurable phases: linting, type checking, style, unit tests, e2e tests.
    """
    try:
        pipeline = get_validation_service()

        # Build config
        phases = None
        if request.phases:
            phases = [ValidationPhase(p) for p in request.phases]

        config = ValidationConfig(
            phases=phases or [
                ValidationPhase.LINTING,
                ValidationPhase.TYPE_CHECK,
                ValidationPhase.STYLE,
                ValidationPhase.UNIT_TESTS,
                ValidationPhase.E2E_TESTS
            ],
            max_iterations=request.max_iterations,
            stop_on_first_failure=request.stop_on_first_failure,
            required_coverage=request.required_coverage
        )

        language = Language(request.language)

        result = await pipeline.run_validation(
            code=request.code,
            language=language,
            config=config,
            file_path=request.file_path
        )

        return _convert_validation_result(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error running validation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@validation_router.post("/lint")
async def quick_lint(code: str, language: str):
    """Run quick lint check only"""
    try:
        pipeline = get_validation_service()
        result = await pipeline.quick_lint(code, Language(language))

        return {
            "phase": result.phase.value,
            "passed": result.passed,
            "errors": [{"message": e.message, "line": e.line, "column": getattr(e, 'column', None)} for e in result.errors],
            "warnings": [{"message": w.message, "line": w.line, "column": None} for w in result.warnings]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error running lint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@validation_router.post("/type-check")
async def quick_type_check(code: str, language: str):
    """Run quick type check only"""
    try:
        pipeline = get_validation_service()
        result = await pipeline.quick_type_check(code, Language(language))

        return {
            "phase": result.phase.value,
            "passed": result.passed,
            "errors": [{"message": e.message, "line": e.line, "column": getattr(e, 'column', None)} for e in result.errors],
            "warnings": [{"message": w.message, "line": w.line, "column": None} for w in result.warnings]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error running type check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@validation_router.post("/iterate", response_model=IterateUntilValidResponse)
async def iterate_until_valid(request: IterateUntilValidRequest):
    """
    Iterate validation and fixing until code is valid.

    This is the automated fix loop that agents use.
    """
    try:
        pipeline = get_validation_service()

        config = ValidationConfig(
            phases=[
                ValidationPhase.LINTING,
                ValidationPhase.TYPE_CHECK,
                ValidationPhase.STYLE
            ],
            max_iterations=request.max_iterations,
            stop_on_first_failure=False
        )

        final_code, result = await pipeline.iterate_until_valid(
            code=request.code,
            language=Language(request.language),
            config=config
        )

        return IterateUntilValidResponse(
            final_code=final_code,
            is_valid=result.overall_passed,
            iterations_used=result.iterations,
            validation_result=_convert_validation_result(result)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error iterating validation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _convert_validation_result(result: ValidationResult) -> ValidationResultResponse:
    """Convert internal ValidationResult to API response"""
    phase_results = []
    for pr in result.phases:
        phase_results.append(ValidationPhaseResultResponse(
            phase=pr.phase.value,
            passed=pr.passed,
            errors=[{"message": e.message, "line": e.line, "column": getattr(e, 'column', None), "code": e.code} for e in pr.errors],
            warnings=[{"message": w.message, "line": w.line, "column": None, "code": w.code} for w in pr.warnings],
            duration=pr.duration,
            tool_used=pr.phase.value,  # Use phase name as tool
            output=pr.raw_output if hasattr(pr, 'raw_output') else None
        ))

    return ValidationResultResponse(
        overall_passed=result.success,
        phases_run=[p.phase.value for p in result.phases],
        phase_results=phase_results,
        total_errors=result.total_errors,
        total_warnings=result.total_warnings,
        coverage=result.coverage_percent,
        total_duration=result.total_duration,
        iterations=result.iterations
    )


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def evolution_health():
    """Check evolution service health"""
    try:
        store = get_experience_store()
        evolution = get_evolution_service()
        pipeline = get_validation_service()

        return {
            "status": "healthy",
            "services": {
                "experience_store": "available" if store else "unavailable",
                "evolution_service": "available" if evolution else "unavailable",
                "validation_pipeline": "available" if pipeline else "unavailable"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Include validation router
router.include_router(validation_router)
