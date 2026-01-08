"""Add RL Training tables

Revision ID: 026_rl_training
Revises: 025_codewiki
Create Date: 2025-12-12

Week 64: ART Reinforcement Learning Foundation
- rl_environments: RL environment configurations
- rl_episodes: Training episodes with state/action/reward
- rl_policies: Learned policies per agent
- rl_rewards: Reward signal definitions
- rl_training_runs: Training run metadata
- rl_agent_performance: Performance metrics over time
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '026_rl_training'
down_revision = '025_codewiki'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # RL Environments - defines the state/action space for agents
    op.create_table(
        'rl_environments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text()),
        sa.Column('agent_type', sa.String(50), nullable=False),  # felix, quinn, betty, etc.
        sa.Column('state_space', sa.JSON(), nullable=False),  # defines observation space
        sa.Column('action_space', sa.JSON(), nullable=False),  # defines action space
        sa.Column('reward_config', sa.JSON(), default=dict),  # reward function config
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rl_environments_agent_type', 'rl_environments', ['agent_type'])
    op.create_index('ix_rl_environments_name', 'rl_environments', ['name'])

    # RL Training Runs - metadata for training sessions
    op.create_table(
        'rl_training_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('environment_id', sa.Integer(), nullable=False),
        sa.Column('run_name', sa.String(200)),
        sa.Column('algorithm', sa.String(50), nullable=False),  # PPO, DQN, A2C, etc.
        sa.Column('hyperparameters', sa.JSON(), default=dict),
        sa.Column('status', sa.String(50), default='pending'),  # pending, running, completed, failed
        sa.Column('total_episodes', sa.Integer(), default=0),
        sa.Column('total_steps', sa.Integer(), default=0),
        sa.Column('best_reward', sa.Float()),
        sa.Column('avg_reward', sa.Float()),
        sa.Column('convergence_episode', sa.Integer()),  # episode where convergence detected
        sa.Column('training_config', sa.JSON(), default=dict),
        sa.Column('metrics_history', sa.JSON(), default=list),  # reward/loss over time
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('duration_seconds', sa.Integer()),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['environment_id'], ['rl_environments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rl_training_runs_env_id', 'rl_training_runs', ['environment_id'])
    op.create_index('ix_rl_training_runs_status', 'rl_training_runs', ['status'])
    op.create_index('ix_rl_training_runs_algorithm', 'rl_training_runs', ['algorithm'])

    # RL Episodes - individual training episodes
    op.create_table(
        'rl_episodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('training_run_id', sa.Integer(), nullable=False),
        sa.Column('episode_number', sa.Integer(), nullable=False),
        sa.Column('total_reward', sa.Float(), nullable=False),
        sa.Column('total_steps', sa.Integer(), nullable=False),
        sa.Column('terminal_state', sa.String(50)),  # success, failure, timeout
        sa.Column('initial_state', sa.JSON()),
        sa.Column('final_state', sa.JSON()),
        sa.Column('action_counts', sa.JSON(), default=dict),  # action frequency
        sa.Column('reward_breakdown', sa.JSON(), default=dict),  # reward components
        sa.Column('duration_ms', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['training_run_id'], ['rl_training_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rl_episodes_run_id', 'rl_episodes', ['training_run_id'])
    op.create_index('ix_rl_episodes_number', 'rl_episodes', ['episode_number'])
    op.create_index('ix_rl_episodes_reward', 'rl_episodes', ['total_reward'])

    # RL Policies - learned policies
    op.create_table(
        'rl_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('environment_id', sa.Integer(), nullable=False),
        sa.Column('training_run_id', sa.Integer()),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('algorithm', sa.String(50), nullable=False),
        sa.Column('policy_type', sa.String(50), default='neural'),  # neural, tabular, rule-based
        sa.Column('policy_data', sa.LargeBinary()),  # serialized policy weights
        sa.Column('policy_path', sa.String(500)),  # file path if stored externally
        sa.Column('performance_score', sa.Float()),
        sa.Column('validation_metrics', sa.JSON(), default=dict),
        sa.Column('is_active', sa.Boolean(), default=False),  # only one active per env
        sa.Column('is_baseline', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['environment_id'], ['rl_environments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['training_run_id'], ['rl_training_runs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rl_policies_env_id', 'rl_policies', ['environment_id'])
    op.create_index('ix_rl_policies_active', 'rl_policies', ['is_active'])
    op.create_index('ix_rl_policies_name_version', 'rl_policies', ['name', 'version'])

    # RL Rewards - reward signal definitions and history
    op.create_table(
        'rl_rewards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('environment_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('reward_type', sa.String(50), nullable=False),  # estimation_accuracy, code_quality, test_coverage, security, speed
        sa.Column('weight', sa.Float(), default=1.0),  # weighting in composite reward
        sa.Column('min_value', sa.Float(), default=-1.0),
        sa.Column('max_value', sa.Float(), default=1.0),
        sa.Column('calculation_formula', sa.Text()),  # Python expression or description
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['environment_id'], ['rl_environments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rl_rewards_env_id', 'rl_rewards', ['environment_id'])
    op.create_index('ix_rl_rewards_type', 'rl_rewards', ['reward_type'])

    # RL Agent Performance - tracking performance over time
    op.create_table(
        'rl_agent_performance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('environment_id', sa.Integer()),
        sa.Column('policy_id', sa.Integer()),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('task_id', sa.String(100)),  # reference to actual task
        sa.Column('task_type', sa.String(50)),  # work type
        sa.Column('context', sa.JSON(), default=dict),  # additional context
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['environment_id'], ['rl_environments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['policy_id'], ['rl_policies.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rl_agent_performance_agent', 'rl_agent_performance', ['agent_type'])
    op.create_index('ix_rl_agent_performance_metric', 'rl_agent_performance', ['metric_name'])
    op.create_index('ix_rl_agent_performance_recorded', 'rl_agent_performance', ['recorded_at'])
    op.create_index('ix_rl_agent_performance_task', 'rl_agent_performance', ['task_id'])

    # RL Step Transitions - detailed state transitions (optional, for debugging)
    op.create_table(
        'rl_step_transitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('episode_id', sa.Integer(), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('state', sa.JSON(), nullable=False),
        sa.Column('action', sa.JSON(), nullable=False),
        sa.Column('reward', sa.Float(), nullable=False),
        sa.Column('next_state', sa.JSON()),
        sa.Column('done', sa.Boolean(), default=False),
        sa.Column('info', sa.JSON(), default=dict),  # additional step info
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['episode_id'], ['rl_episodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rl_step_transitions_episode', 'rl_step_transitions', ['episode_id'])
    op.create_index('ix_rl_step_transitions_step', 'rl_step_transitions', ['step_number'])


def downgrade() -> None:
    op.drop_table('rl_step_transitions')
    op.drop_table('rl_agent_performance')
    op.drop_table('rl_rewards')
    op.drop_table('rl_policies')
    op.drop_table('rl_episodes')
    op.drop_table('rl_training_runs')
    op.drop_table('rl_environments')
