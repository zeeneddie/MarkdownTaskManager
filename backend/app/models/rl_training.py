"""
RL Training Models

Week 64: ART Reinforcement Learning Foundation
SQLAlchemy models for RL training infrastructure.

Models:
- RLEnvironment: RL environment configurations
- RLTrainingRun: Training session metadata
- RLEpisode: Individual training episodes
- RLPolicy: Learned policies
- RLReward: Reward signal definitions
- RLAgentPerformance: Performance tracking
- RLStepTransition: Detailed step transitions

Author: Claude Code (Week 64)
Date: 2025-12-12
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, LargeBinary, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class RLEnvironment(Base):
    """RL Environment configuration for agents"""
    __tablename__ = 'rl_environments'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    agent_type = Column(String(50), nullable=False)  # felix, quinn, betty, eliza, etc.
    state_space = Column(JSON, nullable=False)  # defines observation space
    action_space = Column(JSON, nullable=False)  # defines action space
    reward_config = Column(JSON, default=dict)  # reward function config
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    training_runs = relationship("RLTrainingRun", back_populates="environment", cascade="all, delete-orphan")
    policies = relationship("RLPolicy", back_populates="environment", cascade="all, delete-orphan")
    rewards = relationship("RLReward", back_populates="environment", cascade="all, delete-orphan")
    performance_records = relationship("RLAgentPerformance", back_populates="environment")

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type,
            "state_space": self.state_space,
            "action_space": self.action_space,
            "reward_config": self.reward_config,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "training_runs_count": 0,
            "policies_count": 0
        }
        # Only access relationships if already loaded (avoid lazy loading in async context)
        try:
            if 'training_runs' in self.__dict__:
                result["training_runs_count"] = len(self.training_runs) if self.training_runs else 0
            if 'policies' in self.__dict__:
                result["policies_count"] = len(self.policies) if self.policies else 0
        except Exception:
            pass
        return result


class RLTrainingRun(Base):
    """Training run metadata"""
    __tablename__ = 'rl_training_runs'

    id = Column(Integer, primary_key=True)
    environment_id = Column(Integer, ForeignKey('rl_environments.id', ondelete='CASCADE'), nullable=False)
    run_name = Column(String(200))
    algorithm = Column(String(50), nullable=False)  # PPO, DQN, A2C, REINFORCE, etc.
    hyperparameters = Column(JSON, default=dict)
    status = Column(String(50), default='pending')  # pending, running, completed, failed, cancelled
    total_episodes = Column(Integer, default=0)
    total_steps = Column(Integer, default=0)
    best_reward = Column(Float)
    avg_reward = Column(Float)
    convergence_episode = Column(Integer)  # episode where convergence detected
    training_config = Column(JSON, default=dict)
    metrics_history = Column(JSON, default=list)  # reward/loss over time
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    environment = relationship("RLEnvironment", back_populates="training_runs")
    episodes = relationship("RLEpisode", back_populates="training_run", cascade="all, delete-orphan")
    policies = relationship("RLPolicy", back_populates="training_run")

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "environment_id": self.environment_id,
            "environment_name": None,
            "run_name": self.run_name,
            "algorithm": self.algorithm,
            "hyperparameters": self.hyperparameters,
            "status": self.status,
            "total_episodes": self.total_episodes,
            "total_steps": self.total_steps,
            "best_reward": self.best_reward,
            "avg_reward": self.avg_reward,
            "convergence_episode": self.convergence_episode,
            "training_config": self.training_config,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        # Only access relationship if already loaded
        try:
            if 'environment' in self.__dict__ and self.environment:
                result["environment_name"] = self.environment.name
        except Exception:
            pass
        return result


class RLEpisode(Base):
    """Individual training episode"""
    __tablename__ = 'rl_episodes'

    id = Column(Integer, primary_key=True)
    training_run_id = Column(Integer, ForeignKey('rl_training_runs.id', ondelete='CASCADE'), nullable=False)
    episode_number = Column(Integer, nullable=False)
    total_reward = Column(Float, nullable=False)
    total_steps = Column(Integer, nullable=False)
    terminal_state = Column(String(50))  # success, failure, timeout
    initial_state = Column(JSON)
    final_state = Column(JSON)
    action_counts = Column(JSON, default=dict)  # action frequency
    reward_breakdown = Column(JSON, default=dict)  # reward components
    duration_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    training_run = relationship("RLTrainingRun", back_populates="episodes")
    transitions = relationship("RLStepTransition", back_populates="episode", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "training_run_id": self.training_run_id,
            "episode_number": self.episode_number,
            "total_reward": self.total_reward,
            "total_steps": self.total_steps,
            "terminal_state": self.terminal_state,
            "action_counts": self.action_counts,
            "reward_breakdown": self.reward_breakdown,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class RLPolicy(Base):
    """Learned policy"""
    __tablename__ = 'rl_policies'

    id = Column(Integer, primary_key=True)
    environment_id = Column(Integer, ForeignKey('rl_environments.id', ondelete='CASCADE'), nullable=False)
    training_run_id = Column(Integer, ForeignKey('rl_training_runs.id', ondelete='SET NULL'))
    name = Column(String(200), nullable=False)
    version = Column(Integer, default=1)
    algorithm = Column(String(50), nullable=False)
    policy_type = Column(String(50), default='neural')  # neural, tabular, rule-based
    policy_data = Column(LargeBinary)  # serialized policy weights
    policy_path = Column(String(500))  # file path if stored externally
    performance_score = Column(Float)
    validation_metrics = Column(JSON, default=dict)
    is_active = Column(Boolean, default=False)  # only one active per env
    is_baseline = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    environment = relationship("RLEnvironment", back_populates="policies")
    training_run = relationship("RLTrainingRun", back_populates="policies")
    performance_records = relationship("RLAgentPerformance", back_populates="policy")

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "environment_id": self.environment_id,
            "environment_name": None,
            "training_run_id": self.training_run_id,
            "name": self.name,
            "version": self.version,
            "algorithm": self.algorithm,
            "policy_type": self.policy_type,
            "has_policy_data": self.policy_data is not None,
            "policy_path": self.policy_path,
            "performance_score": self.performance_score,
            "validation_metrics": self.validation_metrics,
            "is_active": self.is_active,
            "is_baseline": self.is_baseline,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        # Only access relationship if already loaded
        try:
            if 'environment' in self.__dict__ and self.environment:
                result["environment_name"] = self.environment.name
        except Exception:
            pass
        return result


class RLReward(Base):
    """Reward signal definition"""
    __tablename__ = 'rl_rewards'

    id = Column(Integer, primary_key=True)
    environment_id = Column(Integer, ForeignKey('rl_environments.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    reward_type = Column(String(50), nullable=False)  # estimation_accuracy, code_quality, test_coverage, security, speed
    weight = Column(Float, default=1.0)  # weighting in composite reward
    min_value = Column(Float, default=-1.0)
    max_value = Column(Float, default=1.0)
    calculation_formula = Column(Text)  # Python expression or description
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    environment = relationship("RLEnvironment", back_populates="rewards")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "environment_id": self.environment_id,
            "name": self.name,
            "description": self.description,
            "reward_type": self.reward_type,
            "weight": self.weight,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "calculation_formula": self.calculation_formula,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class RLAgentPerformance(Base):
    """Performance tracking over time"""
    __tablename__ = 'rl_agent_performance'

    id = Column(Integer, primary_key=True)
    agent_type = Column(String(50), nullable=False)
    environment_id = Column(Integer, ForeignKey('rl_environments.id', ondelete='SET NULL'))
    policy_id = Column(Integer, ForeignKey('rl_policies.id', ondelete='SET NULL'))
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    task_id = Column(String(100))  # reference to actual task
    task_type = Column(String(50))  # work type
    context = Column(JSON, default=dict)  # additional context
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    environment = relationship("RLEnvironment", back_populates="performance_records")
    policy = relationship("RLPolicy", back_populates="performance_records")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_type": self.agent_type,
            "environment_id": self.environment_id,
            "policy_id": self.policy_id,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "task_id": self.task_id,
            "task_type": self.task_type,
            "context": self.context,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None
        }


class RLStepTransition(Base):
    """Detailed state transitions for debugging"""
    __tablename__ = 'rl_step_transitions'

    id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, ForeignKey('rl_episodes.id', ondelete='CASCADE'), nullable=False)
    step_number = Column(Integer, nullable=False)
    state = Column(JSON, nullable=False)
    action = Column(JSON, nullable=False)
    reward = Column(Float, nullable=False)
    next_state = Column(JSON)
    done = Column(Boolean, default=False)
    info = Column(JSON, default=dict)  # additional step info
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    episode = relationship("RLEpisode", back_populates="transitions")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "episode_id": self.episode_id,
            "step_number": self.step_number,
            "state": self.state,
            "action": self.action,
            "reward": self.reward,
            "next_state": self.next_state,
            "done": self.done,
            "info": self.info,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
