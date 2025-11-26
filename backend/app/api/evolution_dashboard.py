"""
Evolution Dashboard REST API

Week 53: Continuous Evolution - Evolution Dashboard
Endpoints for real-time agent performance metrics, trends, and insights.

Author: Claude Code (Week 53 Day 1)
Date: 2025-11-25
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.evolution_dashboard_service import (
    EvolutionDashboardService,
    DashboardOverview,
    AgentPerformanceMetrics,
    ExperimentSummary,
    TimeRange,
    TrendDirection,
    PerformanceLevel
)


# ========== PYDANTIC SCHEMAS ==========

class AgentPerformanceResponse(BaseModel):
    """Response schema for agent performance metrics."""

    agent_id: str
    agent_role: str

    # Success metrics
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    success_rate: float

    # Trend analysis
    trend_direction: str
    improvement_rate: float
    learning_velocity: float

    # Experiment participation
    experiments_participated: int
    experiments_won: int
    win_rate: float

    # Quality metrics
    avg_code_quality: Optional[float]
    avg_estimation_accuracy: Optional[float]

    # Performance level
    performance_level: str

    # Time series data
    daily_success_rates: List[Dict[str, Any]]  # [{"date": "2025-11-25", "rate": 85.5}, ...]

    # Metadata
    last_activity: Optional[datetime]
    data_points: int

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "felix",
                "agent_role": "Feature Architect",
                "total_tasks": 150,
                "successful_tasks": 135,
                "failed_tasks": 15,
                "success_rate": 90.0,
                "trend_direction": "improving",
                "improvement_rate": 12.5,
                "learning_velocity": 2.3,
                "experiments_participated": 5,
                "experiments_won": 3,
                "win_rate": 60.0,
                "avg_code_quality": 88.5,
                "avg_estimation_accuracy": 82.3,
                "performance_level": "excellent",
                "daily_success_rates": [
                    {"date": "2025-11-25", "rate": 92.0},
                    {"date": "2025-11-24", "rate": 88.5}
                ],
                "last_activity": "2025-11-25T14:30:00Z",
                "data_points": 150
            }
        }


class DashboardOverviewResponse(BaseModel):
    """Response schema for dashboard overview."""

    # Global metrics
    total_experiments: int
    active_experiments: int
    completed_experiments: int

    # Agent metrics
    total_agents: int
    improving_agents: int
    stable_agents: int
    declining_agents: int

    # Performance metrics
    avg_success_rate: float
    avg_improvement_rate: float
    top_performer: Optional[str]

    # Learning metrics
    total_experiences_logged: int
    successful_patterns: int
    failure_analyses: int
    recent_milestones: int

    # Metadata
    time_range: str
    generated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "total_experiments": 25,
                "active_experiments": 5,
                "completed_experiments": 18,
                "total_agents": 10,
                "improving_agents": 7,
                "stable_agents": 2,
                "declining_agents": 1,
                "avg_success_rate": 82.5,
                "avg_improvement_rate": 8.3,
                "top_performer": "felix",
                "total_experiences_logged": 1250,
                "successful_patterns": 85,
                "failure_analyses": 42,
                "recent_milestones": 12,
                "time_range": "30d",
                "generated_at": "2025-11-25T14:30:00Z"
            }
        }


class ExperimentSummaryResponse(BaseModel):
    """Response schema for experiment summary."""

    experiment_id: str
    agent_id: str
    feature_name: str
    status: str

    # Timestamps
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_days: Optional[float]

    # Variants
    variant_count: int
    control_variant: str
    treatment_variants: List[str]

    # Results
    winner_variant: Optional[str]
    improvement_percentage: Optional[float]
    confidence_level: Optional[float]

    # Statistical metrics
    total_trials: int
    control_success_rate: Optional[float]
    treatment_success_rate: Optional[float]

    class Config:
        json_schema_extra = {
            "example": {
                "experiment_id": "123e4567-e89b-12d3-a456-426614174000",
                "agent_id": "felix",
                "feature_name": "enhanced_validation",
                "status": "COMPLETED",
                "created_at": "2025-11-20T10:00:00Z",
                "started_at": "2025-11-20T10:05:00Z",
                "completed_at": "2025-11-25T10:05:00Z",
                "duration_days": 5.0,
                "variant_count": 2,
                "control_variant": "baseline",
                "treatment_variants": ["enhanced_validation"],
                "winner_variant": "enhanced_validation",
                "improvement_percentage": 15.5,
                "confidence_level": 95.0,
                "total_trials": 200,
                "control_success_rate": 80.0,
                "treatment_success_rate": 92.4
            }
        }


class TrendsResponse(BaseModel):
    """Response schema for trends data (all agents)."""

    agents: List[AgentPerformanceResponse]
    time_range: str
    generated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "agents": [
                    {
                        "agent_id": "felix",
                        "agent_role": "Feature Architect",
                        "success_rate": 90.0,
                        "trend_direction": "improving"
                    }
                ],
                "time_range": "30d",
                "generated_at": "2025-11-25T14:30:00Z"
            }
        }


class ExperimentsResponse(BaseModel):
    """Response schema for experiments list."""

    experiments: List[ExperimentSummaryResponse]
    total_count: int
    active_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "experiments": [
                    {
                        "experiment_id": "123e4567-e89b-12d3-a456-426614174000",
                        "agent_id": "felix",
                        "feature_name": "enhanced_validation",
                        "status": "ACTIVE"
                    }
                ],
                "total_count": 5,
                "active_count": 3
            }
        }


# ========== ROUTER ==========

router = APIRouter(
    prefix="/api/evolution/dashboard",
    tags=["Evolution Dashboard"]
)


# ========== ENDPOINTS ==========

@router.get(
    "/overview",
    response_model=DashboardOverviewResponse,
    summary="Get Dashboard Overview",
    description="Get high-level metrics for the evolution dashboard including agent performance, experiments, and learning metrics."
)
async def get_dashboard_overview(
    time_range: TimeRange = Query(
        default=TimeRange.THIRTY_DAYS,
        description="Time range for analysis (7d, 30d, 90d, all)"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard overview with high-level metrics.

    Returns:
    - Total experiments (active/completed)
    - Agent performance summary (improving/stable/declining)
    - Average success rate and improvement rate
    - Top performing agent
    - Learning metrics (experiences, patterns, failures)
    - Recent milestones
    """
    service = EvolutionDashboardService(db)

    try:
        overview = await service.get_dashboard_overview(time_range=time_range)

        return DashboardOverviewResponse(
            total_experiments=overview.total_experiments,
            active_experiments=overview.active_experiments,
            completed_experiments=overview.completed_experiments,
            total_agents=overview.total_agents,
            improving_agents=overview.improving_agents,
            stable_agents=overview.stable_agents,
            declining_agents=overview.declining_agents,
            avg_success_rate=overview.avg_success_rate,
            avg_improvement_rate=overview.avg_improvement_rate,
            top_performer=overview.top_performer,
            total_experiences_logged=overview.total_experiences_logged,
            successful_patterns=overview.successful_patterns,
            failure_analyses=overview.failure_analyses,
            recent_milestones=overview.recent_milestones,
            time_range=overview.time_range.value,
            generated_at=overview.generated_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard overview: {str(e)}"
        )


@router.get(
    "/agent/{agent_id}",
    response_model=AgentPerformanceResponse,
    summary="Get Agent Performance",
    description="Get detailed performance metrics and trends for a specific agent."
)
async def get_agent_performance(
    agent_id: str,
    time_range: TimeRange = Query(
        default=TimeRange.THIRTY_DAYS,
        description="Time range for analysis (7d, 30d, 90d, all)"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get performance trends for a specific agent.

    Path Parameters:
    - agent_id: Agent identifier (felix, marcus, quinn, betty, eliza, tessa, miguel, diana, peter, paul)

    Query Parameters:
    - time_range: Time range for analysis (default: 30d)

    Returns:
    - Success rate and trend direction
    - Improvement rate and learning velocity
    - Experiment participation and win rate
    - Quality metrics (code quality, estimation accuracy)
    - Daily success rates for sparkline visualization
    """
    service = EvolutionDashboardService(db)

    # Validate agent_id
    valid_agents = ["felix", "marcus", "quinn", "betty", "eliza",
                    "tessa", "miguel", "diana", "peter", "paul"]
    if agent_id.lower() not in valid_agents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent_id. Must be one of: {', '.join(valid_agents)}"
        )

    try:
        metrics = await service.get_agent_performance_trends(
            agent_id=agent_id.lower(),
            time_range=time_range
        )

        # Convert daily success rates to dict format
        daily_rates_dict = [
            {"date": date, "rate": rate}
            for date, rate in metrics.daily_success_rates
        ]

        return AgentPerformanceResponse(
            agent_id=metrics.agent_id,
            agent_role=metrics.agent_role,
            total_tasks=metrics.total_tasks,
            successful_tasks=metrics.successful_tasks,
            failed_tasks=metrics.failed_tasks,
            success_rate=metrics.success_rate,
            trend_direction=metrics.trend_direction.value,
            improvement_rate=metrics.improvement_rate,
            learning_velocity=metrics.learning_velocity,
            experiments_participated=metrics.experiments_participated,
            experiments_won=metrics.experiments_won,
            win_rate=metrics.win_rate,
            avg_code_quality=metrics.avg_code_quality,
            avg_estimation_accuracy=metrics.avg_estimation_accuracy,
            performance_level=metrics.performance_level.value,
            daily_success_rates=daily_rates_dict,
            last_activity=metrics.last_activity,
            data_points=metrics.data_points
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent performance: {str(e)}"
        )


@router.get(
    "/trends",
    response_model=TrendsResponse,
    summary="Get Performance Trends",
    description="Get performance trends for all agents over the specified time range."
)
async def get_performance_trends(
    time_range: TimeRange = Query(
        default=TimeRange.THIRTY_DAYS,
        description="Time range for analysis (7d, 30d, 90d, all)"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get performance trends for all agents.

    Query Parameters:
    - time_range: Time range for analysis (default: 30d)

    Returns:
    - List of all 10 agents with performance metrics
    - Sorted by success rate (descending)
    - Includes trend direction and improvement rates
    - Daily success rates for sparkline charts
    """
    service = EvolutionDashboardService(db)

    try:
        all_metrics = await service.get_all_agents_performance(time_range=time_range)

        # Convert to response format
        agent_responses = []
        for metrics in all_metrics:
            daily_rates_dict = [
                {"date": date, "rate": rate}
                for date, rate in metrics.daily_success_rates
            ]

            agent_responses.append(
                AgentPerformanceResponse(
                    agent_id=metrics.agent_id,
                    agent_role=metrics.agent_role,
                    total_tasks=metrics.total_tasks,
                    successful_tasks=metrics.successful_tasks,
                    failed_tasks=metrics.failed_tasks,
                    success_rate=metrics.success_rate,
                    trend_direction=metrics.trend_direction.value,
                    improvement_rate=metrics.improvement_rate,
                    learning_velocity=metrics.learning_velocity,
                    experiments_participated=metrics.experiments_participated,
                    experiments_won=metrics.experiments_won,
                    win_rate=metrics.win_rate,
                    avg_code_quality=metrics.avg_code_quality,
                    avg_estimation_accuracy=metrics.avg_estimation_accuracy,
                    performance_level=metrics.performance_level.value,
                    daily_success_rates=daily_rates_dict,
                    last_activity=metrics.last_activity,
                    data_points=metrics.data_points
                )
            )

        return TrendsResponse(
            agents=agent_responses,
            time_range=time_range.value,
            generated_at=datetime.utcnow()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance trends: {str(e)}"
        )


@router.get(
    "/experiments",
    response_model=ExperimentsResponse,
    summary="Get Active Experiments",
    description="Get all active experiments with their current status and metrics."
)
async def get_active_experiments(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all active experiments.

    Returns:
    - List of active experiments
    - Experiment details (variants, status, duration)
    - Current metrics (trials, success rates)
    - Winner information (if completed)
    """
    service = EvolutionDashboardService(db)

    try:
        active_experiments = await service.get_active_experiments()

        # Convert to response format
        experiment_responses = []
        for exp in active_experiments:
            experiment_responses.append(
                ExperimentSummaryResponse(
                    experiment_id=exp.experiment_id,
                    agent_id=exp.agent_id,
                    feature_name=exp.feature_name,
                    status=exp.status,
                    created_at=exp.created_at,
                    started_at=exp.started_at,
                    completed_at=exp.completed_at,
                    duration_days=exp.duration_days,
                    variant_count=exp.variant_count,
                    control_variant=exp.control_variant,
                    treatment_variants=exp.treatment_variants,
                    winner_variant=exp.winner_variant,
                    improvement_percentage=exp.improvement_percentage,
                    confidence_level=exp.confidence_level,
                    total_trials=exp.total_trials,
                    control_success_rate=exp.control_success_rate,
                    treatment_success_rate=exp.treatment_success_rate
                )
            )

        return ExperimentsResponse(
            experiments=experiment_responses,
            total_count=len(experiment_responses),
            active_count=len([e for e in experiment_responses if e.status == "ACTIVE"])
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active experiments: {str(e)}"
        )


@router.get(
    "/experiment/{experiment_id}",
    response_model=ExperimentSummaryResponse,
    summary="Get Experiment Details",
    description="Get detailed information for a specific experiment."
)
async def get_experiment_details(
    experiment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information for a specific experiment.

    Path Parameters:
    - experiment_id: Experiment UUID

    Returns:
    - Complete experiment details
    - Variant configurations
    - Statistical results
    - Winner information
    """
    service = EvolutionDashboardService(db)

    try:
        experiment = await service.get_experiment_summary(experiment_id)

        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment {experiment_id} not found"
            )

        return ExperimentSummaryResponse(
            experiment_id=experiment.experiment_id,
            agent_id=experiment.agent_id,
            feature_name=experiment.feature_name,
            status=experiment.status,
            created_at=experiment.created_at,
            started_at=experiment.started_at,
            completed_at=experiment.completed_at,
            duration_days=experiment.duration_days,
            variant_count=experiment.variant_count,
            control_variant=experiment.control_variant,
            treatment_variants=experiment.treatment_variants,
            winner_variant=experiment.winner_variant,
            improvement_percentage=experiment.improvement_percentage,
            confidence_level=experiment.confidence_level,
            total_trials=experiment.total_trials,
            control_success_rate=experiment.control_success_rate,
            treatment_success_rate=experiment.treatment_success_rate
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get experiment details: {str(e)}"
        )
