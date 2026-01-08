"""
RL Training API

Week 64: ART Reinforcement Learning Foundation
FastAPI endpoints for RL training infrastructure.

Endpoints:
- /environments: Environment CRUD
- /training: Training run management
- /policies: Policy storage and deployment
- /performance: Agent performance tracking
- /dashboard: Statistics and visualization

Author: Claude Code (Week 64)
Date: 2025-12-12
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.rl_training_service import (
    RLTrainingService,
    get_rl_training_service,
    RLAlgorithm,
    RewardType,
    AgentType,
    TrainingConfig
)

router = APIRouter(prefix="/api/rl", tags=["RL Training"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class EnvironmentCreate(BaseModel):
    """Request model for creating an environment"""
    name: str = Field(..., min_length=1, max_length=100)
    agent_type: str = Field(..., description="Agent type (felix, quinn, betty, etc.)")
    description: Optional[str] = None
    state_space: Optional[Dict[str, Any]] = None
    action_space: Optional[Dict[str, Any]] = None
    reward_config: Optional[Dict[str, Any]] = None


class EnvironmentResponse(BaseModel):
    """Response model for environment"""
    id: int
    name: str
    description: Optional[str]
    agent_type: str
    state_space: Dict[str, Any]
    action_space: Dict[str, Any]
    reward_config: Dict[str, Any]
    is_active: bool
    created_at: Optional[str]
    training_runs_count: int = 0
    policies_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class RewardSignalCreate(BaseModel):
    """Request model for adding a reward signal"""
    name: str = Field(..., min_length=1, max_length=100)
    reward_type: str = Field(..., description="Type of reward (estimation_accuracy, code_quality, etc.)")
    description: Optional[str] = None
    weight: float = Field(default=1.0, ge=0.0, le=10.0)
    min_value: float = Field(default=-1.0)
    max_value: float = Field(default=1.0)
    calculation_formula: Optional[str] = None


class RewardSignalResponse(BaseModel):
    """Response model for reward signal"""
    id: int
    environment_id: int
    name: str
    description: Optional[str]
    reward_type: str
    weight: float
    min_value: float
    max_value: float
    calculation_formula: Optional[str]
    is_active: bool
    created_at: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class TrainingRunCreate(BaseModel):
    """Request model for starting a training run"""
    environment_id: int
    algorithm: str = Field(default="PPO", description="RL algorithm (PPO, DQN, A2C, etc.)")
    run_name: Optional[str] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    training_config: Optional[Dict[str, Any]] = None


class TrainingRunResponse(BaseModel):
    """Response model for training run"""
    id: int
    environment_id: int
    environment_name: Optional[str]
    run_name: Optional[str]
    algorithm: str
    hyperparameters: Dict[str, Any]
    status: str
    total_episodes: int
    total_steps: int
    best_reward: Optional[float]
    avg_reward: Optional[float]
    convergence_episode: Optional[int]
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: Optional[int]
    created_at: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class PolicyCreate(BaseModel):
    """Request model for saving a policy"""
    environment_id: int
    name: str = Field(..., min_length=1, max_length=200)
    algorithm: str
    training_run_id: Optional[int] = None
    policy_path: Optional[str] = None
    performance_score: Optional[float] = None
    validation_metrics: Optional[Dict[str, Any]] = None
    is_baseline: bool = False


class PolicyResponse(BaseModel):
    """Response model for policy"""
    id: int
    environment_id: int
    environment_name: Optional[str]
    training_run_id: Optional[int]
    name: str
    version: int
    algorithm: str
    policy_type: str
    has_policy_data: bool
    policy_path: Optional[str]
    performance_score: Optional[float]
    validation_metrics: Dict[str, Any]
    is_active: bool
    is_baseline: bool
    created_at: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class PerformanceRecord(BaseModel):
    """Request model for recording performance"""
    agent_type: str
    metric_name: str
    metric_value: float
    task_id: Optional[str] = None
    task_type: Optional[str] = None
    environment_id: Optional[int] = None
    policy_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None


class PerformanceResponse(BaseModel):
    """Response model for performance record"""
    id: int
    agent_type: str
    metric_name: str
    metric_value: float
    task_id: Optional[str]
    task_type: Optional[str]
    recorded_at: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class TrainRequest(BaseModel):
    """Request model for starting training"""
    max_episodes: int = Field(default=100, ge=1, le=10000)


class EpisodeStatsResponse(BaseModel):
    """Response model for episode statistics"""
    episode_count: int
    avg_reward: float
    max_reward: float
    min_reward: float
    reward_std: float
    avg_steps: float
    terminal_states: Dict[str, int]
    trend: str


class DashboardStatsResponse(BaseModel):
    """Response model for dashboard statistics"""
    environments: Dict[str, int]
    training_runs: Dict[str, int]
    total_episodes: int
    active_policies: int
    agent_performance_7d: Dict[str, float]
    timestamp: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_service(db: AsyncSession = Depends(get_db)) -> RLTrainingService:
    """Dependency for getting RLTrainingService"""
    return get_rl_training_service(db)


# ============================================================================
# ENVIRONMENT ENDPOINTS
# ============================================================================

@router.post("/environments", response_model=EnvironmentResponse)
async def create_environment(
    data: EnvironmentCreate,
    service: RLTrainingService = Depends(get_service)
):
    """Create a new RL environment"""
    env = await service.create_environment(
        name=data.name,
        agent_type=data.agent_type,
        description=data.description,
        state_space=data.state_space,
        action_space=data.action_space,
        reward_config=data.reward_config
    )
    return env.to_dict()


@router.get("/environments", response_model=Dict[str, Any])
async def list_environments(
    is_active: Optional[bool] = Query(None),
    agent_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: RLTrainingService = Depends(get_service)
):
    """List all RL environments"""
    environments, total = await service.list_environments(
        is_active=is_active,
        agent_type=agent_type,
        limit=limit,
        offset=offset
    )
    return {
        "items": [e.to_dict() for e in environments],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/environments/{environment_id}", response_model=EnvironmentResponse)
async def get_environment(
    environment_id: int,
    service: RLTrainingService = Depends(get_service)
):
    """Get a specific environment"""
    env = await service.get_environment(environment_id)
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    return env.to_dict()


@router.get("/environments/agent/{agent_type}", response_model=List[EnvironmentResponse])
async def get_environments_by_agent(
    agent_type: str,
    service: RLTrainingService = Depends(get_service)
):
    """Get all environments for an agent type"""
    environments = await service.get_environments_by_agent(agent_type)
    return [e.to_dict() for e in environments]


# ============================================================================
# REWARD SIGNAL ENDPOINTS
# ============================================================================

@router.post("/environments/{environment_id}/rewards", response_model=RewardSignalResponse)
async def add_reward_signal(
    environment_id: int,
    data: RewardSignalCreate,
    service: RLTrainingService = Depends(get_service)
):
    """Add a reward signal to an environment"""
    reward = await service.add_reward_signal(
        environment_id=environment_id,
        name=data.name,
        reward_type=data.reward_type,
        description=data.description,
        weight=data.weight,
        min_value=data.min_value,
        max_value=data.max_value,
        calculation_formula=data.calculation_formula
    )
    return reward.to_dict()


@router.get("/environments/{environment_id}/rewards", response_model=List[RewardSignalResponse])
async def get_rewards(
    environment_id: int,
    service: RLTrainingService = Depends(get_service)
):
    """Get all reward signals for an environment"""
    rewards = await service.get_rewards_for_environment(environment_id)
    return [r.to_dict() for r in rewards]


@router.get("/reward-types")
async def get_reward_types():
    """Get available reward types"""
    return {
        "types": [
            {"value": rt.value, "name": rt.name}
            for rt in RewardType
        ]
    }


# ============================================================================
# TRAINING RUN ENDPOINTS
# ============================================================================

@router.post("/training", response_model=TrainingRunResponse)
async def start_training_run(
    data: TrainingRunCreate,
    service: RLTrainingService = Depends(get_service)
):
    """Start a new training run"""
    run = await service.start_training_run(
        environment_id=data.environment_id,
        algorithm=data.algorithm,
        run_name=data.run_name,
        hyperparameters=data.hyperparameters,
        training_config=data.training_config
    )
    return run.to_dict()


@router.get("/training", response_model=Dict[str, Any])
async def list_training_runs(
    environment_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    algorithm: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: RLTrainingService = Depends(get_service)
):
    """List training runs"""
    runs, total = await service.list_training_runs(
        environment_id=environment_id,
        status=status,
        algorithm=algorithm,
        limit=limit,
        offset=offset
    )
    return {
        "items": [r.to_dict() for r in runs],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/training/{run_id}", response_model=TrainingRunResponse)
async def get_training_run(
    run_id: int,
    service: RLTrainingService = Depends(get_service)
):
    """Get a specific training run"""
    run = await service.get_training_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")
    return run.to_dict()


@router.post("/training/{run_id}/execute")
async def execute_training(
    run_id: int,
    data: TrainRequest,
    background_tasks: BackgroundTasks,
    service: RLTrainingService = Depends(get_service)
):
    """Execute a training run in the background"""
    run = await service.get_training_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")

    if run.status == "running":
        raise HTTPException(status_code=400, detail="Training already in progress")

    # Start training in background
    background_tasks.add_task(
        service.run_training,
        run_id,
        data.max_episodes
    )

    return {
        "message": "Training started",
        "run_id": run_id,
        "max_episodes": data.max_episodes
    }


@router.post("/training/{run_id}/cancel")
async def cancel_training(
    run_id: int,
    service: RLTrainingService = Depends(get_service)
):
    """Cancel an active training run"""
    success = await service.cancel_training(run_id)
    if not success:
        raise HTTPException(status_code=400, detail="Training run not active")
    return {"message": "Training cancellation requested", "run_id": run_id}


@router.get("/training/{run_id}/episodes/stats", response_model=EpisodeStatsResponse)
async def get_episode_stats(
    run_id: int,
    last_n: int = Query(100, ge=1, le=1000),
    service: RLTrainingService = Depends(get_service)
):
    """Get statistics for recent episodes"""
    stats = await service.get_episode_stats(run_id, last_n)
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    return stats


@router.get("/algorithms")
async def get_algorithms():
    """Get available RL algorithms"""
    return {
        "algorithms": [
            {
                "value": alg.value,
                "name": alg.name,
                "description": _get_algorithm_description(alg)
            }
            for alg in RLAlgorithm
        ]
    }


def _get_algorithm_description(alg: RLAlgorithm) -> str:
    """Get description for an algorithm"""
    descriptions = {
        RLAlgorithm.PPO: "Proximal Policy Optimization - stable, sample-efficient",
        RLAlgorithm.DQN: "Deep Q-Network - good for discrete actions",
        RLAlgorithm.A2C: "Advantage Actor-Critic - parallel training",
        RLAlgorithm.REINFORCE: "Policy Gradient - simple but high variance",
        RLAlgorithm.SAC: "Soft Actor-Critic - maximum entropy RL",
        RLAlgorithm.TD3: "Twin Delayed DDPG - continuous actions"
    }
    return descriptions.get(alg, "")


# ============================================================================
# POLICY ENDPOINTS
# ============================================================================

@router.post("/policies", response_model=PolicyResponse)
async def save_policy(
    data: PolicyCreate,
    service: RLTrainingService = Depends(get_service)
):
    """Save a learned policy"""
    policy = await service.save_policy(
        environment_id=data.environment_id,
        name=data.name,
        algorithm=data.algorithm,
        training_run_id=data.training_run_id,
        policy_path=data.policy_path,
        performance_score=data.performance_score,
        validation_metrics=data.validation_metrics,
        is_baseline=data.is_baseline
    )
    return policy.to_dict()


@router.get("/policies", response_model=Dict[str, Any])
async def list_policies(
    environment_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: RLTrainingService = Depends(get_service)
):
    """List policies"""
    policies, total = await service.list_policies(
        environment_id=environment_id,
        is_active=is_active,
        limit=limit,
        offset=offset
    )
    return {
        "items": [p.to_dict() for p in policies],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.post("/policies/{policy_id}/activate", response_model=PolicyResponse)
async def activate_policy(
    policy_id: int,
    service: RLTrainingService = Depends(get_service)
):
    """Set a policy as active"""
    policy = await service.activate_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy.to_dict()


@router.get("/environments/{environment_id}/active-policy", response_model=PolicyResponse)
async def get_active_policy(
    environment_id: int,
    service: RLTrainingService = Depends(get_service)
):
    """Get the active policy for an environment"""
    policy = await service.get_active_policy(environment_id)
    if not policy:
        raise HTTPException(status_code=404, detail="No active policy found")
    return policy.to_dict()


# ============================================================================
# PERFORMANCE ENDPOINTS
# ============================================================================

@router.post("/performance", response_model=PerformanceResponse)
async def record_performance(
    data: PerformanceRecord,
    service: RLTrainingService = Depends(get_service)
):
    """Record an agent performance metric"""
    record = await service.record_performance(
        agent_type=data.agent_type,
        metric_name=data.metric_name,
        metric_value=data.metric_value,
        task_id=data.task_id,
        task_type=data.task_type,
        environment_id=data.environment_id,
        policy_id=data.policy_id,
        context=data.context
    )
    return record.to_dict()


@router.get("/performance/{agent_type}/trend")
async def get_performance_trend(
    agent_type: str,
    metric_name: str,
    days: int = Query(30, ge=1, le=365),
    service: RLTrainingService = Depends(get_service)
):
    """Get performance trend for an agent"""
    trend = await service.get_performance_trend(agent_type, metric_name, days)
    return {
        "agent_type": agent_type,
        "metric_name": metric_name,
        "days": days,
        "data": trend
    }


@router.get("/performance/{agent_type}/summary")
async def get_performance_summary(
    agent_type: str,
    days: int = Query(30, ge=1, le=365),
    service: RLTrainingService = Depends(get_service)
):
    """Get performance summary for an agent"""
    summary = await service.get_agent_performance_summary(agent_type, days)
    return summary


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    service: RLTrainingService = Depends(get_service)
):
    """Get statistics for the RL dashboard"""
    stats = await service.get_dashboard_stats()
    return stats


@router.get("/agent-types")
async def get_agent_types():
    """Get available agent types"""
    return {
        "types": [
            {
                "value": at.value,
                "name": at.name,
                "description": _get_agent_description(at)
            }
            for at in AgentType
        ]
    }


def _get_agent_description(at: AgentType) -> str:
    """Get description for an agent type"""
    descriptions = {
        AgentType.FELIX: "Feature Architect - System design, API design",
        AgentType.QUINN: "Quality Inspector - Code review, security",
        AgentType.BETTY: "Bug Hunter - Debugging, root cause analysis",
        AgentType.ELIZA: "Estimation Engine - Function points, story points",
        AgentType.DIANA: "Documentation Writer - API docs, guides",
        AgentType.MARCUS: "Maintenance Specialist - Refactoring, tech debt",
        AgentType.TESSA: "Test Engineer - Unit tests, E2E tests",
        AgentType.MIGUEL: "Migration Architect - Tech stack migrations",
        AgentType.PETER: "Product Owner - User stories, prioritization",
        AgentType.PAUL: "Project Lead - Sprint planning, resource allocation"
    }
    return descriptions.get(at, "")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "rl_training",
        "timestamp": datetime.utcnow().isoformat()
    }
