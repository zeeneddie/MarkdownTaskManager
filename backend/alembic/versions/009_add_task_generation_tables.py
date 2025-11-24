"""add task generation tables

Revision ID: 009
Revises: 008
Create Date: 2025-01-22 14:00:00.000000

Week 23-24: Self-Questioning Agents
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create skill_gaps table first (referenced by training_tasks)
    op.create_table(
        'skill_gaps',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('area', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, server_default='IMPORTANT'),
        sa.Column('evidence', postgresql.JSON(), nullable=True, server_default='[]'),
        sa.Column('addressed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('identified_at', sa.DateTime(), nullable=False),
        sa.Column('addressed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_skill_gaps_agent_id', 'skill_gaps', ['agent_id'])
    op.create_index('ix_skill_gaps_severity', 'skill_gaps', ['severity'])

    # Create training_tasks table
    op.create_table(
        'training_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('task_type', sa.String(30), nullable=False),
        sa.Column('difficulty', sa.String(20), nullable=False, server_default='MEDIUM'),
        sa.Column('source', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        # Scenario fields
        sa.Column('scenario_description', sa.Text(), nullable=False),
        sa.Column('scenario_context', postgresql.JSON(), nullable=True, server_default='{}'),
        sa.Column('scenario_constraints', postgresql.JSON(), nullable=True, server_default='[]'),
        sa.Column('scenario_success_criteria', postgresql.JSON(), nullable=True, server_default='[]'),
        sa.Column('scenario_related_patterns', postgresql.JSON(), nullable=True, server_default='[]'),
        sa.Column('scenario_focus_areas', postgresql.JSON(), nullable=True, server_default='[]'),
        # Expected outcome fields
        sa.Column('learning_objective', sa.Text(), nullable=True),
        sa.Column('expected_success_rate', sa.Float(), nullable=True, server_default='0.7'),
        sa.Column('target_skills', postgresql.JSON(), nullable=True, server_default='[]'),
        sa.Column('improvement_metrics', postgresql.JSON(), nullable=True, server_default='[]'),
        # Relationships
        sa.Column('parent_attribution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('parent_validation_id', sa.String(100), nullable=True),
        sa.Column('skill_gap_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Priority and estimation
        sa.Column('priority', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('estimated_duration_ms', sa.Integer(), nullable=False, server_default='300000'),
        # Execution tracking
        sa.Column('execution_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_attribution_id'], ['attributions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['skill_gap_id'], ['skill_gaps.id'], ondelete='SET NULL')
    )
    op.create_index('ix_training_tasks_agent_id', 'training_tasks', ['agent_id'])
    op.create_index('ix_training_tasks_status', 'training_tasks', ['status'])
    op.create_index('ix_training_tasks_task_type', 'training_tasks', ['task_type'])

    # Create training_task_results table
    op.create_table(
        'training_task_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='false'),
        # Actual outcome
        sa.Column('learning_achieved', postgresql.JSON(), nullable=True, server_default='[]'),
        sa.Column('skills_improved', postgresql.JSON(), nullable=True, server_default='[]'),
        sa.Column('unexpected_learnings', postgresql.JSON(), nullable=True, server_default='[]'),
        # Metrics
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('validation_passed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.0'),
        # Lessons and follow-ups
        sa.Column('lessons', postgresql.JSON(), nullable=True, server_default='[]'),
        sa.Column('follow_up_tasks', postgresql.JSON(), nullable=True, server_default='[]'),
        # Link to attribution
        sa.Column('attribution_id', postgresql.UUID(as_uuid=True), nullable=True),
        # Timestamp
        sa.Column('completed_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['task_id'], ['training_tasks.id'], ondelete='CASCADE')
    )
    op.create_index('ix_training_task_results_agent_id', 'training_task_results', ['agent_id'])
    op.create_index('ix_training_task_results_task_id', 'training_task_results', ['task_id'])

    # Create exploration_targets table
    op.create_table(
        'exploration_targets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('learning_value', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('explored', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('related_skill_gaps', postgresql.JSON(), nullable=True, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('explored_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_exploration_targets_target_type', 'exploration_targets', ['target_type'])

    # Create improvement_metrics table
    op.create_table(
        'improvement_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        # Task metrics
        sa.Column('tasks_generated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tasks_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tasks_successful', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tasks_failed', sa.Integer(), nullable=False, server_default='0'),
        # Learning metrics
        sa.Column('skill_gaps_identified', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skill_gaps_addressed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lessons_learned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('patterns_discovered', sa.Integer(), nullable=False, server_default='0'),
        # Performance changes
        sa.Column('success_rate_change', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('confidence_change', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('estimation_accuracy_change', sa.Float(), nullable=False, server_default='0.0'),
        # Trend
        sa.Column('trend', sa.String(20), nullable=False, server_default='STABLE'),
        # Timestamp
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_improvement_metrics_agent_id', 'improvement_metrics', ['agent_id'])
    op.create_index('ix_improvement_metrics_period', 'improvement_metrics', ['period_start', 'period_end'])

    # Create training_sessions table
    op.create_table(
        'training_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('task_ids', postgresql.JSON(), nullable=True, server_default='[]'),
        sa.Column('result_ids', postgresql.JSON(), nullable=True, server_default='[]'),
        sa.Column('skill_gaps_addressed', postgresql.JSON(), nullable=True, server_default='[]'),
        sa.Column('new_skill_gaps_identified', postgresql.JSON(), nullable=True, server_default='[]'),
        sa.Column('overall_success', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('metrics_before_session', postgresql.JSON(), nullable=True, server_default='{}'),
        sa.Column('metrics_after_session', postgresql.JSON(), nullable=True, server_default='{}'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_training_sessions_agent_id', 'training_sessions', ['agent_id'])

    # Create generation_strategies table
    op.create_table(
        'generation_strategies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(50), nullable=False, unique=True),
        sa.Column('focus_areas', postgresql.JSON(), nullable=True, server_default='[]'),
        sa.Column('difficulty_preference', sa.String(20), nullable=False, server_default='MEDIUM'),
        sa.Column('max_tasks_per_session', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('cooldown_period_ms', sa.Integer(), nullable=False, server_default='3600000'),
        sa.Column('type_weights', postgresql.JSON(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_generation_strategies_agent_id', 'generation_strategies', ['agent_id'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('generation_strategies')
    op.drop_table('training_sessions')
    op.drop_table('improvement_metrics')
    op.drop_table('exploration_targets')
    op.drop_table('training_task_results')
    op.drop_table('training_tasks')
    op.drop_table('skill_gaps')
