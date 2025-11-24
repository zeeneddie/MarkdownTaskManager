"""add attribution tables

Revision ID: 008
Revises: 007
Create Date: 2025-01-22 10:00:00.000000

Week 21-22: Self-Attributing Agents
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create task_outcomes table
    op.create_table(
        'task_outcomes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', sa.String(100), nullable=False),
        sa.Column('workflow_id', sa.String(100), nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('outcome_type', sa.String(20), nullable=False),
        sa.Column('steps_data', sa.Text(), nullable=True),
        sa.Column('quality_gate_results', sa.Text(), nullable=True),
        sa.Column('validation_history', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_task_outcomes_task_id', 'task_outcomes', ['task_id'])
    op.create_index('ix_task_outcomes_workflow_id', 'task_outcomes', ['workflow_id'])
    op.create_index('ix_task_outcomes_agent_id', 'task_outcomes', ['agent_id'])

    # Create attributions table
    op.create_table(
        'attributions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', sa.String(100), nullable=False),
        sa.Column('workflow_id', sa.String(100), nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('outcome', sa.String(20), nullable=False),
        sa.Column('key_steps', sa.Text(), nullable=True),
        sa.Column('causal_factors', sa.Text(), nullable=True),
        sa.Column('quality_gate_results', sa.Text(), nullable=True),
        sa.Column('validation_history', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('confidence_level', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_attributions_task_id', 'attributions', ['task_id'])
    op.create_index('ix_attributions_workflow_id', 'attributions', ['workflow_id'])
    op.create_index('ix_attributions_agent_id', 'attributions', ['agent_id'])

    # Create attribution_feedback table
    op.create_table(
        'attribution_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attribution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('lessons', sa.Text(), nullable=True),
        sa.Column('recommended_adjustments', sa.Text(), nullable=True),
        sa.Column('delivered', sa.Boolean(), nullable=True, default=False),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_attribution_feedback_attribution_id', 'attribution_feedback', ['attribution_id'])
    op.create_index('ix_attribution_feedback_agent_id', 'attribution_feedback', ['agent_id'])

    # Create quality_gate_stats table
    op.create_table(
        'quality_gate_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gate_type', sa.String(50), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('total_checks', sa.Integer(), nullable=True, default=0),
        sa.Column('issues_caught', sa.Integer(), nullable=True, default=0),
        sa.Column('false_positives', sa.Integer(), nullable=True, default=0),
        sa.Column('false_negatives', sa.Integer(), nullable=True, default=0),
        sa.Column('effectiveness', sa.Float(), nullable=True, default=0.0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_quality_gate_stats_gate_type', 'quality_gate_stats', ['gate_type'])


def downgrade() -> None:
    op.drop_index('ix_quality_gate_stats_gate_type', table_name='quality_gate_stats')
    op.drop_table('quality_gate_stats')

    op.drop_index('ix_attribution_feedback_agent_id', table_name='attribution_feedback')
    op.drop_index('ix_attribution_feedback_attribution_id', table_name='attribution_feedback')
    op.drop_table('attribution_feedback')

    op.drop_index('ix_attributions_agent_id', table_name='attributions')
    op.drop_index('ix_attributions_workflow_id', table_name='attributions')
    op.drop_index('ix_attributions_task_id', table_name='attributions')
    op.drop_table('attributions')

    op.drop_index('ix_task_outcomes_agent_id', table_name='task_outcomes')
    op.drop_index('ix_task_outcomes_workflow_id', table_name='task_outcomes')
    op.drop_index('ix_task_outcomes_task_id', table_name='task_outcomes')
    op.drop_table('task_outcomes')
