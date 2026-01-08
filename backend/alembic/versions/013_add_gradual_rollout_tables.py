"""Add gradual rollout tables

Revision ID: c3d8e9f7a123
Revises: babf2cfd359e
Create Date: 2025-11-25 14:00:00.000000

Week 53 Day 4: Gradual Rollout System
Creates tables for managing gradual rollout of experiment winners with automatic rollback.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c3d8e9f7a123'
down_revision = 'babf2cfd359e'
branch_labels = None
depends_on = None


def upgrade():
    """Create gradual rollout tables."""

    # 1. Rollouts table - Main rollout configuration
    op.create_table(
        'rollouts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('feature_name', sa.String(200), nullable=False),
        sa.Column('current_stage', sa.Integer, nullable=False, server_default='0'),
        sa.Column('current_percentage', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('rolled_back_at', sa.DateTime, nullable=True),
        sa.Column('rollback_reason', sa.Text, nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),

        # Foreign keys
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['experiment_variants.id'], ondelete='CASCADE'),

        # Constraints
        sa.CheckConstraint('current_stage >= 0 AND current_stage <= 4', name='valid_stage'),
        sa.CheckConstraint('current_percentage >= 0.0 AND current_percentage <= 100.0', name='valid_percentage'),
        sa.CheckConstraint(
            "status IN ('PENDING', 'ACTIVE', 'PAUSED', 'COMPLETED', 'ROLLED_BACK')",
            name='valid_status'
        )
    )

    # Indexes
    op.create_index('idx_rollouts_experiment', 'rollouts', ['experiment_id'])
    op.create_index('idx_rollouts_agent', 'rollouts', ['agent_id'])
    op.create_index('idx_rollouts_status', 'rollouts', ['status'])
    op.create_index('idx_rollouts_created', 'rollouts', ['created_at'])

    # 2. Rollout stages table - Stage configuration and results
    op.create_table(
        'rollout_stages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('rollout_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stage_number', sa.Integer, nullable=False),
        sa.Column('traffic_percentage', sa.Float, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('duration_seconds', sa.Integer, nullable=True),
        sa.Column('success_rate', sa.Float, nullable=True),
        sa.Column('baseline_success_rate', sa.Float, nullable=True),
        sa.Column('performance_drop', sa.Float, nullable=True),
        sa.Column('total_requests', sa.Integer, nullable=False, server_default='0'),
        sa.Column('successful_requests', sa.Integer, nullable=False, server_default='0'),
        sa.Column('failed_requests', sa.Integer, nullable=False, server_default='0'),
        sa.Column('health_check_passed', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('rollback_triggered', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('rollback_reason', sa.Text, nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),

        # Foreign keys
        sa.ForeignKeyConstraint(['rollout_id'], ['rollouts.id'], ondelete='CASCADE'),

        # Constraints
        sa.CheckConstraint('stage_number >= 0 AND stage_number <= 4', name='valid_stage_number'),
        sa.CheckConstraint('traffic_percentage >= 0.0 AND traffic_percentage <= 100.0', name='valid_traffic'),
        sa.CheckConstraint(
            "status IN ('PENDING', 'ACTIVE', 'COMPLETED', 'FAILED', 'ROLLED_BACK')",
            name='valid_stage_status'
        ),
        sa.CheckConstraint('success_rate IS NULL OR (success_rate >= 0.0 AND success_rate <= 100.0)', name='valid_success_rate'),
        sa.UniqueConstraint('rollout_id', 'stage_number', name='unique_rollout_stage')
    )

    # Indexes
    op.create_index('idx_rollout_stages_rollout', 'rollout_stages', ['rollout_id'])
    op.create_index('idx_rollout_stages_status', 'rollout_stages', ['status'])
    op.create_index('idx_rollout_stages_health', 'rollout_stages', ['health_check_passed'])

    # 3. Rollout metrics table - Detailed metrics per stage
    op.create_table(
        'rollout_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('stage_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Float, nullable=False),
        sa.Column('metric_unit', sa.String(50), nullable=True),
        sa.Column('threshold_value', sa.Float, nullable=True),
        sa.Column('threshold_breached', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('metadata', postgresql.JSONB, nullable=True),

        # Foreign keys
        sa.ForeignKeyConstraint(['stage_id'], ['rollout_stages.id'], ondelete='CASCADE'),

        # Constraints
        sa.CheckConstraint(
            "metric_name IN ('success_rate', 'response_time', 'error_rate', 'throughput', 'cpu_usage', 'memory_usage', 'custom')",
            name='valid_metric_name'
        )
    )

    # Indexes
    op.create_index('idx_rollout_metrics_stage', 'rollout_metrics', ['stage_id'])
    op.create_index('idx_rollout_metrics_timestamp', 'rollout_metrics', ['timestamp'])
    op.create_index('idx_rollout_metrics_name', 'rollout_metrics', ['metric_name'])
    op.create_index('idx_rollout_metrics_breached', 'rollout_metrics', ['threshold_breached'])


def downgrade():
    """Drop gradual rollout tables."""
    op.drop_table('rollout_metrics')
    op.drop_table('rollout_stages')
    op.drop_table('rollouts')
