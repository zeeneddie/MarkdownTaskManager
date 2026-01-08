"""
Continuous Learning API

Week 25-26: AgentEvolver Integration - Continuous Learning Endpoints
Based on: github.com/zeeneddie/AgentEvolver

API endpoints for:
- Threshold optimization
- Learning session management
- Learning metrics
- Auto-tuning

Author: Claude Code (Week 25 Day 2)
Date: 2025-11-22
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.continuous_learning_service import (
    ContinuousLearningService,
    get_continuous_learning_service,
    LearningSession,
    SessionResult,
    ThresholdUpdate,
    WeightUpdate,
    RetrainingCheck,
    LearningMetrics,
    LearningStatus,
    OptimizationType
)
from app.services.experience_store_service import WorkType

# Note: include_in_schema=False to avoid OpenAPI schema generation issues with dataclass imports
router = APIRouter(prefix="/api/continuous-learning", tags=["Continuous Learning"], include_in_schema=False)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class OptimizeThresholdsRequest(BaseModel):
    """Request to optimize thresholds for an agent"""
    work_type: Optional[str] = Field(None, description="Specific work type to optimize for")


class StartSessionRequest(BaseModel):
    """Request to start a learning session"""
    optimization_types: Optional[List[str]] = Field(
        None,
        description="Types of optimization to perform"
    )
    max_iterations: int = Field(10, ge=1, le=50, description="Maximum iterations")


class CompleteSessionRequest(BaseModel):
    """Request to complete a learning session"""
    outcomes: Dict[str, Any] = Field(default_factory=dict, description="Session outcomes")


class ThresholdUpdateResponse(BaseModel):
    """Response for threshold optimization"""
    agent_id: str
    optimization_type: str
    previous_values: Dict[str, Any]
    new_values: Dict[str, Any]
    improvement_expected: float
    confidence: float
    reasoning: str
    timestamp: str


class WeightUpdateResponse(BaseModel):
    """Response for weight update"""
    agent_id: str
    pattern_id: str
    pattern_name: str
    previous_weight: float
    new_weight: float
    success_rate: float
    usage_count: int
    reasoning: str
    timestamp: str


class LearningSessionResponse(BaseModel):
    """Response for learning session"""
    id: str
    agent_id: str
    agent_role: str
    status: str
    started_at: str
    ended_at: Optional[str]
    optimization_types: List[str]
    max_iterations: int
    current_iteration: int
    threshold_updates: List[Dict[str, Any]]
    weight_updates: List[Dict[str, Any]]
    total_improvements: float
    learnings: List[str]
    recommendations: List[str]


class SessionResultResponse(BaseModel):
    """Response for session result"""
    session_id: str
    agent_id: str
    success: bool
    total_duration: float
    improvements_made: int
    average_improvement: float
    new_success_rate: float
    learnings: List[str]
    recommendations: List[str]
    next_session_scheduled: Optional[str]


class RetrainingCheckResponse(BaseModel):
    """Response for retraining check"""
    agent_id: str
    retraining_needed: bool
    reasons: List[str]
    urgency: str
    metrics_summary: Dict[str, Any]
    recommendation: str


class LearningMetricsResponse(BaseModel):
    """Response for learning metrics"""
    agent_id: str
    agent_role: str
    total_sessions: int
    successful_sessions: int
    total_improvements: float
    average_improvement_per_session: float
    thresholds_optimized: int
    patterns_learned: int
    pattern_reuse_rate: float
    learning_streak: int
    improvement_trend: str


class AutoTuneResponse(BaseModel):
    """Response for auto-tune operation"""
    timestamp: str
    agents_tuned: int
    agents_skipped: int
    results: Dict[str, Any]


class SessionsListResponse(BaseModel):
    """Response for listing sessions"""
    count: int
    sessions: List[Dict[str, Any]]


class PatternWeightsResponse(BaseModel):
    """Response for pattern weights update"""
    agent_id: str
    updates_count: int
    updates: List[Dict[str, Any]]


class LearningRateResponse(BaseModel):
    """Response for learning rate adjustment"""
    agent_id: str
    new_learning_rate: float
    performance_metrics: Dict[str, Any]


class LearningStatusResponse(BaseModel):
    """Response for learning status"""
    agent_id: str
    current_session: Optional[Dict[str, Any]]
    metrics: Dict[str, Any]
    retraining_check: Dict[str, Any]
    last_optimization: Optional[str]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/optimize/{agent_id}", response_model=ThresholdUpdateResponse)
async def optimize_thresholds(
    agent_id: str,
    request: OptimizeThresholdsRequest = None
):
    """
    Trigger threshold optimization for an agent.

    Analyzes past experiences to find optimal validation thresholds.
    """
    try:
        service = await get_continuous_learning_service()

        work_type = None
        if request and request.work_type:
            try:
                work_type = WorkType(request.work_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid work type: {request.work_type}")

        result = await service.optimize_validation_thresholds(agent_id, work_type)

        return ThresholdUpdateResponse(
            agent_id=result.agent_id,
            optimization_type=result.optimization_type.value,
            previous_values=result.previous_values,
            new_values=result.new_values,
            improvement_expected=result.improvement_expected,
            confidence=result.confidence,
            reasoning=result.reasoning,
            timestamp=result.timestamp.isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{agent_id}", response_model=LearningStatusResponse)
async def get_learning_status(agent_id: str):
    """
    Get learning status for an agent.

    Includes current session, metrics, and retraining check.
    """
    try:
        service = await get_continuous_learning_service()

        # Get current session
        sessions = await service.get_agent_sessions(agent_id, limit=1)
        current_session = sessions[0].to_dict() if sessions else None

        # Get metrics
        metrics = await service.get_learning_metrics(agent_id)

        # Check retraining
        retraining_check = await service.check_retraining_needed(agent_id)

        return LearningStatusResponse(
            agent_id=agent_id,
            current_session=current_session,
            metrics=metrics.to_dict(),
            retraining_check=retraining_check.to_dict(),
            last_optimization=None  # TODO: Track this
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions", response_model=LearningSessionResponse)
async def start_learning_session(
    agent_id: str = Query(..., description="Agent ID"),
    request: StartSessionRequest = None
):
    """
    Start a new learning session for an agent.
    """
    try:
        service = await get_continuous_learning_service()

        # Parse optimization types
        optimization_types = None
        if request and request.optimization_types:
            optimization_types = []
            for ot in request.optimization_types:
                try:
                    optimization_types.append(OptimizationType(ot))
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid optimization type: {ot}")

        max_iterations = request.max_iterations if request else 10

        session = await service.start_learning_session(
            agent_id=agent_id,
            optimization_types=optimization_types,
            max_iterations=max_iterations
        )

        return LearningSessionResponse(**session.to_dict())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=LearningSessionResponse)
async def get_session(session_id: str):
    """
    Get a learning session by ID.
    """
    try:
        service = await get_continuous_learning_service()
        session = await service.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        return LearningSessionResponse(**session.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/complete", response_model=SessionResultResponse)
async def complete_session(
    session_id: str,
    request: CompleteSessionRequest = None
):
    """
    Complete a learning session and record outcomes.
    """
    try:
        service = await get_continuous_learning_service()

        outcomes = request.outcomes if request else {}
        result = await service.complete_learning_session(session_id, outcomes)

        return SessionResultResponse(
            session_id=result.session_id,
            agent_id=result.agent_id,
            success=result.success,
            total_duration=result.total_duration,
            improvements_made=result.improvements_made,
            average_improvement=result.average_improvement,
            new_success_rate=result.new_success_rate,
            learnings=result.learnings,
            recommendations=result.recommendations,
            next_session_scheduled=result.next_session_scheduled.isoformat() if result.next_session_scheduled else None
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=List[LearningMetricsResponse])
async def get_all_metrics():
    """
    Get learning metrics for all agents.
    """
    try:
        service = await get_continuous_learning_service()
        all_metrics = await service.get_all_learning_metrics()

        return [
            LearningMetricsResponse(
                agent_id=m.agent_id,
                agent_role=m.agent_role.value,
                total_sessions=m.total_sessions,
                successful_sessions=m.successful_sessions,
                total_improvements=m.total_improvements,
                average_improvement_per_session=m.average_improvement_per_session,
                thresholds_optimized=m.thresholds_optimized,
                patterns_learned=m.patterns_learned,
                pattern_reuse_rate=m.pattern_reuse_rate,
                learning_streak=m.learning_streak,
                improvement_trend=m.improvement_trend
            )
            for m in all_metrics
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{agent_id}", response_model=LearningMetricsResponse)
async def get_agent_metrics(agent_id: str):
    """
    Get learning metrics for a specific agent.
    """
    try:
        service = await get_continuous_learning_service()
        metrics = await service.get_learning_metrics(agent_id)

        return LearningMetricsResponse(
            agent_id=metrics.agent_id,
            agent_role=metrics.agent_role.value,
            total_sessions=metrics.total_sessions,
            successful_sessions=metrics.successful_sessions,
            total_improvements=metrics.total_improvements,
            average_improvement_per_session=metrics.average_improvement_per_session,
            thresholds_optimized=metrics.thresholds_optimized,
            patterns_learned=metrics.patterns_learned,
            pattern_reuse_rate=metrics.pattern_reuse_rate,
            learning_streak=metrics.learning_streak,
            improvement_trend=metrics.improvement_trend
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-tune", response_model=AutoTuneResponse)
async def auto_tune_all_agents():
    """
    Auto-tune all agents with a single call.

    Checks each agent for retraining needs and starts learning sessions
    for those that need it.
    """
    try:
        service = await get_continuous_learning_service()
        results = await service.auto_tune_all_agents()

        agents_tuned = sum(1 for r in results.values() if r.get("status") == "tuned")
        agents_skipped = sum(1 for r in results.values() if r.get("status") == "no_tuning_needed")

        return AutoTuneResponse(
            timestamp=datetime.now().isoformat(),
            agents_tuned=agents_tuned,
            agents_skipped=agents_skipped,
            results=results
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retraining-check/{agent_id}", response_model=RetrainingCheckResponse)
async def check_retraining_needed(agent_id: str):
    """
    Check if an agent needs retraining.
    """
    try:
        service = await get_continuous_learning_service()
        check = await service.check_retraining_needed(agent_id)

        return RetrainingCheckResponse(
            agent_id=check.agent_id,
            retraining_needed=check.retraining_needed,
            reasons=[r.value for r in check.reasons],
            urgency=check.urgency,
            metrics_summary=check.metrics_summary,
            recommendation=check.recommendation
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=SessionsListResponse)
async def list_sessions(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """
    List learning sessions with optional filtering.
    """
    try:
        service = await get_continuous_learning_service()

        if agent_id:
            sessions = await service.get_agent_sessions(agent_id, limit=limit)
        else:
            # Get all sessions (limited)
            sessions = list(service._sessions.values())
            sessions.sort(key=lambda s: s.started_at, reverse=True)
            sessions = sessions[:limit]

        # Filter by status if provided
        if status:
            try:
                status_filter = LearningStatus(status)
                sessions = [s for s in sessions if s.status == status_filter]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        return SessionsListResponse(
            count=len(sessions),
            sessions=[s.to_dict() for s in sessions]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pattern-weights/{agent_id}", response_model=PatternWeightsResponse)
async def update_pattern_weights(agent_id: str):
    """
    Update pattern weights for an agent.
    """
    try:
        service = await get_continuous_learning_service()
        updates = await service.update_pattern_weights(agent_id)

        return PatternWeightsResponse(
            agent_id=agent_id,
            updates_count=len(updates),
            updates=[u.to_dict() for u in updates]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning-rate/{agent_id}", response_model=LearningRateResponse)
async def adjust_learning_rate(agent_id: str):
    """
    Adjust learning rate for an agent based on performance.
    """
    try:
        from app.services.agent_evolution_service import get_evolution_service

        service = await get_continuous_learning_service()
        evolution_service = await get_evolution_service()

        # Get current performance
        metrics = await evolution_service.get_performance_metrics(
            agent_id=agent_id,
            period_days=7
        )

        if not metrics:
            raise HTTPException(status_code=404, detail=f"No metrics found for agent {agent_id}")

        new_rate = await service.adjust_learning_rate(agent_id, metrics)

        return LearningRateResponse(
            agent_id=agent_id,
            new_learning_rate=new_rate,
            performance_metrics={
                "success_rate": metrics.success_rate,
                "average_quality_score": metrics.average_quality_score
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
