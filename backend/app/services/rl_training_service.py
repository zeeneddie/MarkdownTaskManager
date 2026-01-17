"""
RL Training Service

Week 64: ART Reinforcement Learning Foundation
Implements the ART (Agent Reinforcement Training) framework for optimizing agent behavior.

Core Features:
1. Environment Management: State/action space definitions per agent type
2. Training Orchestration: PPO, DQN, A2C algorithm support
3. Reward System: Multi-dimensional reward calculation
4. Policy Management: Store, load, and deploy learned policies
5. Performance Tracking: Continuous monitoring and analysis

Author: Claude Code (Week 64)
Date: 2025-12-12
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from enum import Enum
import uuid
import logging
import asyncio
import json
import math
import pickle
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.rl_training import (
    RLEnvironment,
    RLTrainingRun,
    RLEpisode,
    RLPolicy,
    RLReward,
    RLAgentPerformance,
    RLStepTransition
)

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class RLAlgorithm(str, Enum):
    """Supported RL algorithms"""
    PPO = "PPO"           # Proximal Policy Optimization
    DQN = "DQN"           # Deep Q-Network
    A2C = "A2C"           # Advantage Actor-Critic
    REINFORCE = "REINFORCE"  # Policy Gradient
    SAC = "SAC"           # Soft Actor-Critic
    TD3 = "TD3"           # Twin Delayed DDPG


class RewardType(str, Enum):
    """Types of reward signals"""
    ESTIMATION_ACCURACY = "estimation_accuracy"
    CODE_QUALITY = "code_quality"
    TEST_COVERAGE = "test_coverage"
    SECURITY_SCORE = "security_score"
    SPEED = "speed"
    USER_SATISFACTION = "user_satisfaction"
    TASK_COMPLETION = "task_completion"
    COST_EFFICIENCY = "cost_efficiency"


class AgentType(str, Enum):
    """Agent types for RL training"""
    FELIX = "felix"       # Feature Architect
    QUINN = "quinn"       # Quality Inspector
    BETTY = "betty"       # Bug Hunter
    ELIZA = "eliza"       # Estimation Engine
    DIANA = "diana"       # Documentation Writer
    MARCUS = "marcus"     # Maintenance Specialist
    TESSA = "tessa"       # Test Engineer
    MIGUEL = "miguel"     # Migration Architect
    PETER = "peter"       # Product Owner
    PAUL = "paul"         # Project Lead


# Default state spaces per agent type
DEFAULT_STATE_SPACES = {
    AgentType.FELIX: {
        "dimensions": ["task_complexity", "code_size", "dependencies_count", "tech_stack_familiarity"],
        "ranges": {"task_complexity": [0, 10], "code_size": [0, 100000], "dependencies_count": [0, 50], "tech_stack_familiarity": [0, 1]}
    },
    AgentType.QUINN: {
        "dimensions": ["code_quality_score", "test_coverage", "security_issues", "performance_metrics"],
        "ranges": {"code_quality_score": [0, 100], "test_coverage": [0, 100], "security_issues": [0, 50], "performance_metrics": [0, 100]}
    },
    AgentType.ELIZA: {
        "dimensions": ["task_description_length", "historical_accuracy", "complexity_indicators", "domain_familiarity"],
        "ranges": {"task_description_length": [0, 5000], "historical_accuracy": [0, 1], "complexity_indicators": [0, 10], "domain_familiarity": [0, 1]}
    }
}

# Default action spaces per agent type
DEFAULT_ACTION_SPACES = {
    AgentType.FELIX: {
        "actions": ["design_simple", "design_moderate", "design_complex", "request_clarification", "delegate_to_specialist"],
        "type": "discrete"
    },
    AgentType.QUINN: {
        "actions": ["approve", "request_changes", "reject", "escalate_security", "escalate_performance"],
        "type": "discrete"
    },
    AgentType.ELIZA: {
        "actions": ["estimate_low", "estimate_medium", "estimate_high", "request_more_context", "use_historical_baseline"],
        "type": "discrete"
    }
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class State:
    """RL state representation"""
    features: Dict[str, float]
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_vector(self) -> List[float]:
        """Convert to feature vector"""
        return list(self.features.values())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "features": self.features,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Action:
    """RL action representation"""
    action_id: str
    action_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "parameters": self.parameters,
            "confidence": self.confidence
        }


@dataclass
class Reward:
    """Reward signal"""
    total: float
    components: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "components": self.components,
            "explanation": self.explanation
        }


@dataclass
class Transition:
    """State transition tuple (s, a, r, s', done)"""
    state: State
    action: Action
    reward: Reward
    next_state: Optional[State]
    done: bool
    info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EpisodeResult:
    """Result of a training episode"""
    episode_id: int
    total_reward: float
    total_steps: int
    terminal_state: str  # success, failure, timeout
    transitions: List[Transition]
    action_distribution: Dict[str, int]
    reward_breakdown: Dict[str, float]
    duration_ms: int


@dataclass
class TrainingConfig:
    """Configuration for a training run"""
    algorithm: RLAlgorithm = RLAlgorithm.PPO
    learning_rate: float = 0.0003
    gamma: float = 0.99  # discount factor
    epsilon: float = 0.2  # PPO clip parameter
    batch_size: int = 64
    n_epochs: int = 10
    max_episodes: int = 1000
    max_steps_per_episode: int = 100
    early_stopping_patience: int = 50
    early_stopping_threshold: float = 0.01
    save_frequency: int = 100
    eval_frequency: int = 50


# ============================================================================
# REWARD CALCULATOR
# ============================================================================

class RewardCalculator:
    """Calculates rewards for agent actions"""

    def __init__(self, reward_configs: List[Dict[str, Any]]):
        self.reward_configs = {cfg["reward_type"]: cfg for cfg in reward_configs}

    def calculate(
        self,
        agent_type: AgentType,
        action: Action,
        outcome: Dict[str, Any]
    ) -> Reward:
        """Calculate composite reward from multiple signals"""
        components = {}
        explanations = []

        for reward_type, config in self.reward_configs.items():
            if not config.get("is_active", True):
                continue

            weight = config.get("weight", 1.0)
            min_val = config.get("min_value", -1.0)
            max_val = config.get("max_value", 1.0)

            # Calculate raw reward
            raw_reward = self._calculate_component(
                reward_type, agent_type, action, outcome
            )

            # Normalize and weight
            normalized = max(min_val, min(max_val, raw_reward))
            weighted = normalized * weight

            components[reward_type] = weighted
            explanations.append(f"{reward_type}: {weighted:.3f}")

        total = sum(components.values())

        return Reward(
            total=total,
            components=components,
            explanation="; ".join(explanations)
        )

    def _calculate_component(
        self,
        reward_type: str,
        agent_type: AgentType,
        action: Action,
        outcome: Dict[str, Any]
    ) -> float:
        """Calculate a single reward component"""

        if reward_type == RewardType.ESTIMATION_ACCURACY:
            # For Eliza: reward based on estimation accuracy
            if "actual_value" in outcome and "estimated_value" in outcome:
                actual = outcome["actual_value"]
                estimated = outcome["estimated_value"]
                if actual > 0:
                    error_ratio = abs(actual - estimated) / actual
                    return 1.0 - min(1.0, error_ratio)
            return 0.0

        elif reward_type == RewardType.CODE_QUALITY:
            # For Quinn/Felix: reward based on code quality score
            return outcome.get("quality_score", 0.5) / 100.0

        elif reward_type == RewardType.TEST_COVERAGE:
            # For Tessa: reward based on test coverage
            coverage = outcome.get("test_coverage", 0)
            target = 80  # Target coverage
            if coverage >= target:
                return 1.0
            return coverage / target

        elif reward_type == RewardType.SECURITY_SCORE:
            # For Quinn: reward based on security (inverse of issues)
            issues = outcome.get("security_issues", 0)
            if issues == 0:
                return 1.0
            return max(0, 1.0 - (issues * 0.1))

        elif reward_type == RewardType.SPEED:
            # Reward based on completion time
            time_taken = outcome.get("duration_seconds", 0)
            time_budget = outcome.get("time_budget", 300)
            if time_taken <= time_budget:
                return 1.0
            return max(0, 1.0 - (time_taken - time_budget) / time_budget)

        elif reward_type == RewardType.TASK_COMPLETION:
            # Binary reward for task completion
            return 1.0 if outcome.get("completed", False) else -0.5

        elif reward_type == RewardType.USER_SATISFACTION:
            # From user feedback
            return outcome.get("user_rating", 0.5)

        elif reward_type == RewardType.COST_EFFICIENCY:
            # Reward for using fewer tokens/resources
            tokens_used = outcome.get("tokens_used", 0)
            tokens_budget = outcome.get("tokens_budget", 10000)
            if tokens_used <= tokens_budget:
                return 1.0
            return max(0, 1.0 - (tokens_used - tokens_budget) / tokens_budget)

        return 0.0


# ============================================================================
# RL TRAINING SERVICE
# ============================================================================

class RLTrainingService:
    """
    Core RL Training Service for the ART Framework

    Manages:
    - Environment setup and configuration
    - Training run orchestration
    - Policy storage and deployment
    - Performance tracking
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.reward_calculator: Optional[RewardCalculator] = None
        self._active_training_runs: Dict[int, bool] = {}

    # ========================================================================
    # ENVIRONMENT MANAGEMENT
    # ========================================================================

    async def create_environment(
        self,
        name: str,
        agent_type: str,
        description: Optional[str] = None,
        state_space: Optional[Dict] = None,
        action_space: Optional[Dict] = None,
        reward_config: Optional[Dict] = None
    ) -> RLEnvironment:
        """Create a new RL environment for an agent type"""

        # Use defaults if not provided
        agent_enum = AgentType(agent_type) if agent_type in [a.value for a in AgentType] else None

        if state_space is None and agent_enum:
            state_space = DEFAULT_STATE_SPACES.get(agent_enum, {"dimensions": [], "ranges": {}})

        if action_space is None and agent_enum:
            action_space = DEFAULT_ACTION_SPACES.get(agent_enum, {"actions": [], "type": "discrete"})

        environment = RLEnvironment(
            name=name,
            description=description or f"RL environment for {agent_type}",
            agent_type=agent_type,
            state_space=state_space or {},
            action_space=action_space or {},
            reward_config=reward_config or {}
        )

        self.db.add(environment)
        await self.db.commit()
        await self.db.refresh(environment)

        logger.info(f"Created RL environment: {name} for agent {agent_type}")
        return environment

    async def get_environment(self, environment_id: int) -> Optional[RLEnvironment]:
        """Get environment by ID"""
        result = await self.db.execute(
            select(RLEnvironment)
            .options(selectinload(RLEnvironment.rewards))
            .where(RLEnvironment.id == environment_id)
        )
        return result.scalar_one_or_none()

    async def get_environments_by_agent(self, agent_type: str) -> List[RLEnvironment]:
        """Get all environments for an agent type"""
        result = await self.db.execute(
            select(RLEnvironment)
            .where(RLEnvironment.agent_type == agent_type)
            .where(RLEnvironment.is_active == True)
        )
        return result.scalars().all()

    async def list_environments(
        self,
        is_active: Optional[bool] = None,
        agent_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[RLEnvironment], int]:
        """List environments with filtering"""
        query = select(RLEnvironment)
        count_query = select(func.count(RLEnvironment.id))

        if is_active is not None:
            query = query.where(RLEnvironment.is_active == is_active)
            count_query = count_query.where(RLEnvironment.is_active == is_active)

        if agent_type:
            query = query.where(RLEnvironment.agent_type == agent_type)
            count_query = count_query.where(RLEnvironment.agent_type == agent_type)

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(RLEnvironment.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)

        return result.scalars().all(), total

    # ========================================================================
    # REWARD MANAGEMENT
    # ========================================================================

    async def add_reward_signal(
        self,
        environment_id: int,
        name: str,
        reward_type: str,
        description: Optional[str] = None,
        weight: float = 1.0,
        min_value: float = -1.0,
        max_value: float = 1.0,
        calculation_formula: Optional[str] = None
    ) -> RLReward:
        """Add a reward signal to an environment"""
        reward = RLReward(
            environment_id=environment_id,
            name=name,
            description=description,
            reward_type=reward_type,
            weight=weight,
            min_value=min_value,
            max_value=max_value,
            calculation_formula=calculation_formula
        )

        self.db.add(reward)
        await self.db.commit()
        await self.db.refresh(reward)

        logger.info(f"Added reward signal: {name} ({reward_type}) to env {environment_id}")
        return reward

    async def get_rewards_for_environment(self, environment_id: int) -> List[RLReward]:
        """Get all reward signals for an environment"""
        result = await self.db.execute(
            select(RLReward)
            .where(RLReward.environment_id == environment_id)
            .where(RLReward.is_active == True)
        )
        return result.scalars().all()

    # ========================================================================
    # TRAINING RUN MANAGEMENT
    # ========================================================================

    async def start_training_run(
        self,
        environment_id: int,
        algorithm: str = "PPO",
        run_name: Optional[str] = None,
        hyperparameters: Optional[Dict] = None,
        training_config: Optional[Dict] = None
    ) -> RLTrainingRun:
        """Start a new training run"""

        # Verify environment exists
        environment = await self.get_environment(environment_id)
        if not environment:
            raise ValueError(f"Environment {environment_id} not found")

        # Create training run
        training_run = RLTrainingRun(
            environment_id=environment_id,
            run_name=run_name or f"{environment.name}_{algorithm}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            algorithm=algorithm,
            hyperparameters=hyperparameters or TrainingConfig().__dict__,
            training_config=training_config or {},
            status="pending",
            created_at=datetime.now(timezone.utc)
        )

        self.db.add(training_run)
        await self.db.commit()
        await self.db.refresh(training_run)

        logger.info(f"Created training run: {training_run.run_name} (ID: {training_run.id})")
        return training_run

    async def update_training_status(
        self,
        run_id: int,
        status: str,
        metrics: Optional[Dict] = None,
        error_message: Optional[str] = None
    ) -> Optional[RLTrainingRun]:
        """Update training run status"""
        result = await self.db.execute(
            select(RLTrainingRun).where(RLTrainingRun.id == run_id)
        )
        training_run = result.scalar_one_or_none()

        if not training_run:
            return None

        training_run.status = status

        if status == "running" and not training_run.started_at:
            training_run.started_at = datetime.now(timezone.utc)

        if status in ["completed", "failed", "cancelled"]:
            training_run.completed_at = datetime.now(timezone.utc)
            if training_run.started_at:
                training_run.duration_seconds = int(
                    (training_run.completed_at - training_run.started_at).total_seconds()
                )

        if error_message:
            training_run.error_message = error_message

        if metrics:
            history = training_run.metrics_history or []
            history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **metrics
            })
            training_run.metrics_history = history

            if "best_reward" in metrics:
                if training_run.best_reward is None or metrics["best_reward"] > training_run.best_reward:
                    training_run.best_reward = metrics["best_reward"]

            if "avg_reward" in metrics:
                training_run.avg_reward = metrics["avg_reward"]

        await self.db.commit()
        return training_run

    async def get_training_run(self, run_id: int) -> Optional[RLTrainingRun]:
        """Get training run by ID"""
        result = await self.db.execute(
            select(RLTrainingRun)
            .options(selectinload(RLTrainingRun.environment))
            .options(selectinload(RLTrainingRun.episodes))
            .where(RLTrainingRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def list_training_runs(
        self,
        environment_id: Optional[int] = None,
        status: Optional[str] = None,
        algorithm: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[RLTrainingRun], int]:
        """List training runs with filtering"""
        query = select(RLTrainingRun)
        count_query = select(func.count(RLTrainingRun.id))

        if environment_id:
            query = query.where(RLTrainingRun.environment_id == environment_id)
            count_query = count_query.where(RLTrainingRun.environment_id == environment_id)

        if status:
            query = query.where(RLTrainingRun.status == status)
            count_query = count_query.where(RLTrainingRun.status == status)

        if algorithm:
            query = query.where(RLTrainingRun.algorithm == algorithm)
            count_query = count_query.where(RLTrainingRun.algorithm == algorithm)

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(RLTrainingRun.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)

        return result.scalars().all(), total

    # ========================================================================
    # EPISODE MANAGEMENT
    # ========================================================================

    async def record_episode(
        self,
        training_run_id: int,
        episode_number: int,
        result: EpisodeResult
    ) -> RLEpisode:
        """Record a completed training episode"""
        episode = RLEpisode(
            training_run_id=training_run_id,
            episode_number=episode_number,
            total_reward=result.total_reward,
            total_steps=result.total_steps,
            terminal_state=result.terminal_state,
            initial_state=result.transitions[0].state.to_dict() if result.transitions else None,
            final_state=result.transitions[-1].next_state.to_dict() if result.transitions and result.transitions[-1].next_state else None,
            action_counts=result.action_distribution,
            reward_breakdown=result.reward_breakdown,
            duration_ms=result.duration_ms
        )

        self.db.add(episode)
        await self.db.flush()

        # Optionally record transitions (can be disabled for large-scale training)
        if len(result.transitions) <= 100:  # Only store if reasonable size
            for i, trans in enumerate(result.transitions):
                step = RLStepTransition(
                    episode_id=episode.id,
                    step_number=i,
                    state=trans.state.to_dict(),
                    action=trans.action.to_dict(),
                    reward=trans.reward.total,
                    next_state=trans.next_state.to_dict() if trans.next_state else None,
                    done=trans.done,
                    info=trans.info
                )
                self.db.add(step)

        # Update training run stats
        result_run = await self.db.execute(
            select(RLTrainingRun).where(RLTrainingRun.id == training_run_id)
        )
        training_run = result_run.scalar_one_or_none()
        if training_run:
            training_run.total_episodes = episode_number
            training_run.total_steps = (training_run.total_steps or 0) + result.total_steps

        await self.db.commit()
        await self.db.refresh(episode)

        return episode

    async def get_episode_stats(
        self,
        training_run_id: int,
        last_n: int = 100
    ) -> Dict[str, Any]:
        """Get statistics for recent episodes"""
        result = await self.db.execute(
            select(RLEpisode)
            .where(RLEpisode.training_run_id == training_run_id)
            .order_by(RLEpisode.episode_number.desc())
            .limit(last_n)
        )
        episodes = result.scalars().all()

        if not episodes:
            return {"error": "No episodes found"}

        rewards = [ep.total_reward for ep in episodes]
        steps = [ep.total_steps for ep in episodes]

        return {
            "episode_count": len(episodes),
            "avg_reward": sum(rewards) / len(rewards),
            "max_reward": max(rewards),
            "min_reward": min(rewards),
            "reward_std": self._std(rewards),
            "avg_steps": sum(steps) / len(steps),
            "terminal_states": {
                state: sum(1 for ep in episodes if ep.terminal_state == state)
                for state in set(ep.terminal_state for ep in episodes if ep.terminal_state)
            },
            "trend": self._calculate_trend(rewards)
        }

    def _std(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 10:
            return "insufficient_data"

        first_half = values[len(values)//2:]
        second_half = values[:len(values)//2]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        diff = second_avg - first_avg
        if abs(diff) < 0.01:
            return "stable"
        return "improving" if diff > 0 else "declining"

    # ========================================================================
    # POLICY MANAGEMENT
    # ========================================================================

    async def save_policy(
        self,
        environment_id: int,
        name: str,
        algorithm: str,
        training_run_id: Optional[int] = None,
        policy_data: Optional[bytes] = None,
        policy_path: Optional[str] = None,
        performance_score: Optional[float] = None,
        validation_metrics: Optional[Dict] = None,
        is_baseline: bool = False
    ) -> RLPolicy:
        """Save a learned policy"""

        # Get current version
        result = await self.db.execute(
            select(func.max(RLPolicy.version))
            .where(RLPolicy.environment_id == environment_id)
            .where(RLPolicy.name == name)
        )
        max_version = result.scalar() or 0

        policy = RLPolicy(
            environment_id=environment_id,
            training_run_id=training_run_id,
            name=name,
            version=max_version + 1,
            algorithm=algorithm,
            policy_data=policy_data,
            policy_path=policy_path,
            performance_score=performance_score,
            validation_metrics=validation_metrics or {},
            is_baseline=is_baseline
        )

        self.db.add(policy)
        await self.db.commit()
        await self.db.refresh(policy)

        logger.info(f"Saved policy: {name} v{policy.version} for env {environment_id}")
        return policy

    async def activate_policy(self, policy_id: int) -> Optional[RLPolicy]:
        """Set a policy as active (only one active per environment)"""
        result = await self.db.execute(
            select(RLPolicy).where(RLPolicy.id == policy_id)
        )
        policy = result.scalar_one_or_none()

        if not policy:
            return None

        # Deactivate all other policies for this environment
        await self.db.execute(
            update(RLPolicy)
            .where(RLPolicy.environment_id == policy.environment_id)
            .where(RLPolicy.id != policy_id)
            .values(is_active=False)
        )

        # Activate the selected policy
        policy.is_active = True
        await self.db.commit()

        logger.info(f"Activated policy: {policy.name} v{policy.version}")
        return policy

    async def get_active_policy(self, environment_id: int) -> Optional[RLPolicy]:
        """Get the active policy for an environment"""
        result = await self.db.execute(
            select(RLPolicy)
            .where(RLPolicy.environment_id == environment_id)
            .where(RLPolicy.is_active == True)
        )
        return result.scalar_one_or_none()

    async def list_policies(
        self,
        environment_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[RLPolicy], int]:
        """List policies with filtering"""
        query = select(RLPolicy)
        count_query = select(func.count(RLPolicy.id))

        if environment_id:
            query = query.where(RLPolicy.environment_id == environment_id)
            count_query = count_query.where(RLPolicy.environment_id == environment_id)

        if is_active is not None:
            query = query.where(RLPolicy.is_active == is_active)
            count_query = count_query.where(RLPolicy.is_active == is_active)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        query = query.order_by(RLPolicy.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)

        return result.scalars().all(), total

    # ========================================================================
    # PERFORMANCE TRACKING
    # ========================================================================

    async def record_performance(
        self,
        agent_type: str,
        metric_name: str,
        metric_value: float,
        task_id: Optional[str] = None,
        task_type: Optional[str] = None,
        environment_id: Optional[int] = None,
        policy_id: Optional[int] = None,
        context: Optional[Dict] = None
    ) -> RLAgentPerformance:
        """Record agent performance metric"""
        performance = RLAgentPerformance(
            agent_type=agent_type,
            environment_id=environment_id,
            policy_id=policy_id,
            metric_name=metric_name,
            metric_value=metric_value,
            task_id=task_id,
            task_type=task_type,
            context=context or {}
        )

        self.db.add(performance)
        await self.db.commit()
        await self.db.refresh(performance)

        return performance

    async def get_performance_trend(
        self,
        agent_type: str,
        metric_name: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get performance trend for an agent"""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.db.execute(
            select(RLAgentPerformance)
            .where(RLAgentPerformance.agent_type == agent_type)
            .where(RLAgentPerformance.metric_name == metric_name)
            .where(RLAgentPerformance.recorded_at >= since)
            .order_by(RLAgentPerformance.recorded_at)
        )

        records = result.scalars().all()
        return [r.to_dict() for r in records]

    async def get_agent_performance_summary(
        self,
        agent_type: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get summary of agent performance"""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.db.execute(
            select(
                RLAgentPerformance.metric_name,
                func.avg(RLAgentPerformance.metric_value).label("avg"),
                func.min(RLAgentPerformance.metric_value).label("min"),
                func.max(RLAgentPerformance.metric_value).label("max"),
                func.count(RLAgentPerformance.id).label("count")
            )
            .where(RLAgentPerformance.agent_type == agent_type)
            .where(RLAgentPerformance.recorded_at >= since)
            .group_by(RLAgentPerformance.metric_name)
        )

        metrics = {}
        for row in result:
            metrics[row.metric_name] = {
                "avg": float(row.avg) if row.avg else 0,
                "min": float(row.min) if row.min else 0,
                "max": float(row.max) if row.max else 0,
                "count": row.count
            }

        return {
            "agent_type": agent_type,
            "period_days": days,
            "metrics": metrics
        }

    # ========================================================================
    # TRAINING LOOP (Simplified - Real RL would use external framework)
    # ========================================================================

    async def run_training_episode(
        self,
        environment: RLEnvironment,
        policy: Optional[RLPolicy] = None,
        max_steps: int = 100
    ) -> EpisodeResult:
        """
        Run a single training episode (simplified version)

        In production, this would interface with a proper RL framework like:
        - Stable Baselines3
        - RLlib
        - TensorFlow Agents
        """
        transitions = []
        action_counts: Dict[str, int] = {}
        reward_breakdown: Dict[str, float] = {}
        start_time = datetime.now(timezone.utc)

        # Initialize state
        state = State(
            features={dim: 0.5 for dim in environment.state_space.get("dimensions", [])},
            context={"episode_start": start_time.isoformat()}
        )

        # Initialize reward calculator
        rewards = await self.get_rewards_for_environment(environment.id)
        self.reward_calculator = RewardCalculator([r.to_dict() for r in rewards])

        total_reward = 0.0
        done = False
        step = 0

        while not done and step < max_steps:
            # Select action (random for now - would use policy in real implementation)
            action_space = environment.action_space
            actions = action_space.get("actions", ["default_action"])
            action_id = actions[step % len(actions)]  # Simple round-robin for demo

            action = Action(
                action_id=action_id,
                action_type=action_space.get("type", "discrete"),
                confidence=0.8
            )

            # Track action distribution
            action_counts[action_id] = action_counts.get(action_id, 0) + 1

            # Simulate environment step
            outcome = {
                "completed": step > max_steps * 0.7,  # 70% completion rate
                "quality_score": 70 + (step % 30),
                "test_coverage": 60 + (step % 40),
                "duration_seconds": step * 10,
                "time_budget": max_steps * 10
            }

            # Calculate reward
            reward = self.reward_calculator.calculate(
                AgentType(environment.agent_type) if environment.agent_type in [a.value for a in AgentType] else AgentType.FELIX,
                action,
                outcome
            )

            total_reward += reward.total

            # Accumulate reward breakdown
            for key, value in reward.components.items():
                reward_breakdown[key] = reward_breakdown.get(key, 0) + value

            # Generate next state
            next_state = State(
                features={dim: min(1.0, state.features.get(dim, 0) + 0.1)
                         for dim in environment.state_space.get("dimensions", [])},
                context={"step": step + 1}
            )

            # Check if done
            done = outcome.get("completed", False) or step >= max_steps - 1

            # Record transition
            transitions.append(Transition(
                state=state,
                action=action,
                reward=reward,
                next_state=next_state if not done else None,
                done=done,
                info=outcome
            ))

            state = next_state
            step += 1

        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        return EpisodeResult(
            episode_id=0,  # Will be set when recorded
            total_reward=total_reward,
            total_steps=step,
            terminal_state="success" if outcome.get("completed") else "timeout",
            transitions=transitions,
            action_distribution=action_counts,
            reward_breakdown=reward_breakdown,
            duration_ms=duration_ms
        )

    async def run_training(
        self,
        training_run_id: int,
        max_episodes: int = 100,
        callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Run a full training loop

        Args:
            training_run_id: ID of the training run
            max_episodes: Maximum number of episodes to run
            callback: Optional callback for progress updates

        Returns:
            Training results summary
        """
        training_run = await self.get_training_run(training_run_id)
        if not training_run:
            raise ValueError(f"Training run {training_run_id} not found")

        environment = training_run.environment
        if not environment:
            raise ValueError("Training run has no associated environment")

        # Mark as running
        await self.update_training_status(training_run_id, "running")
        self._active_training_runs[training_run_id] = True

        episode_rewards = []
        best_reward = float('-inf')

        try:
            for episode_num in range(1, max_episodes + 1):
                # Check if cancelled
                if not self._active_training_runs.get(training_run_id, False):
                    await self.update_training_status(
                        training_run_id, "cancelled",
                        error_message="Training cancelled by user"
                    )
                    break

                # Run episode
                result = await self.run_training_episode(environment)

                # Record episode
                await self.record_episode(training_run_id, episode_num, result)

                episode_rewards.append(result.total_reward)

                if result.total_reward > best_reward:
                    best_reward = result.total_reward

                # Update metrics periodically
                if episode_num % 10 == 0:
                    await self.update_training_status(
                        training_run_id, "running",
                        metrics={
                            "episode": episode_num,
                            "best_reward": best_reward,
                            "avg_reward": sum(episode_rewards[-100:]) / len(episode_rewards[-100:])
                        }
                    )

                    if callback:
                        callback({
                            "episode": episode_num,
                            "reward": result.total_reward,
                            "best": best_reward
                        })

                # Small delay to prevent blocking
                await asyncio.sleep(0.01)

            # Training complete
            avg_reward = sum(episode_rewards) / len(episode_rewards)
            await self.update_training_status(
                training_run_id, "completed",
                metrics={
                    "final_episode": len(episode_rewards),
                    "best_reward": best_reward,
                    "avg_reward": avg_reward
                }
            )

            # Save the final policy
            await self.save_policy(
                environment_id=environment.id,
                name=f"{environment.name}_policy",
                algorithm=training_run.algorithm,
                training_run_id=training_run_id,
                performance_score=avg_reward,
                validation_metrics={
                    "episodes": len(episode_rewards),
                    "best_reward": best_reward,
                    "avg_reward": avg_reward
                }
            )

            return {
                "status": "completed",
                "episodes": len(episode_rewards),
                "best_reward": best_reward,
                "avg_reward": avg_reward,
                "final_rewards": episode_rewards[-10:]
            }

        except Exception as e:
            logger.error(f"Training error: {e}")
            await self.update_training_status(
                training_run_id, "failed",
                error_message=str(e)
            )
            raise
        finally:
            self._active_training_runs.pop(training_run_id, None)

    async def cancel_training(self, training_run_id: int) -> bool:
        """Cancel an active training run"""
        if training_run_id in self._active_training_runs:
            self._active_training_runs[training_run_id] = False
            return True
        return False

    # ========================================================================
    # STATISTICS & DASHBOARD
    # ========================================================================

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get statistics for the RL dashboard"""
        # Count environments
        env_result = await self.db.execute(
            select(func.count(RLEnvironment.id))
        )
        total_environments = env_result.scalar()

        # Count active environments
        active_env_result = await self.db.execute(
            select(func.count(RLEnvironment.id))
            .where(RLEnvironment.is_active == True)
        )
        active_environments = active_env_result.scalar()

        # Training runs by status
        runs_result = await self.db.execute(
            select(RLTrainingRun.status, func.count(RLTrainingRun.id))
            .group_by(RLTrainingRun.status)
        )
        runs_by_status = {row[0]: row[1] for row in runs_result}

        # Total episodes
        episodes_result = await self.db.execute(
            select(func.count(RLEpisode.id))
        )
        total_episodes = episodes_result.scalar()

        # Active policies
        policies_result = await self.db.execute(
            select(func.count(RLPolicy.id))
            .where(RLPolicy.is_active == True)
        )
        active_policies = policies_result.scalar()

        # Recent performance by agent
        recent_perf = await self.db.execute(
            select(
                RLAgentPerformance.agent_type,
                func.avg(RLAgentPerformance.metric_value).label("avg_performance")
            )
            .where(RLAgentPerformance.recorded_at >= datetime.now(timezone.utc) - timedelta(days=7))
            .group_by(RLAgentPerformance.agent_type)
        )
        agent_performance = {row[0]: float(row[1]) for row in recent_perf}

        return {
            "environments": {
                "total": total_environments,
                "active": active_environments
            },
            "training_runs": runs_by_status,
            "total_episodes": total_episodes,
            "active_policies": active_policies,
            "agent_performance_7d": agent_performance,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# ============================================================================
# SERVICE FACTORY
# ============================================================================

def get_rl_training_service(db: AsyncSession) -> RLTrainingService:
    """Factory function for RLTrainingService"""
    return RLTrainingService(db)
