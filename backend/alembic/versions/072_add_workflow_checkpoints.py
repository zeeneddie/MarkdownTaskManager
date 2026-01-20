"""Add Workflow Checkpoints Table for Restartable Workflows

Revision ID: 072
Revises: 071
Create Date: 2026-01-20

Week 158 - Fase 24.6: Restartable Workflows

Tables:
- workflow_checkpoints: Generic checkpoint/resume system for all workflow types

Features:
- Checkpoint after each stage
- Resume from failure point
- Idempotent stages (skip completed on resume)
- Error context for debugging
- Backward compatible (optional feature)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '072'
down_revision = '071'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create workflow_checkpoints table
    op.create_table(
        'workflow_checkpoints',
        sa.Column('id', sa.String(36), primary_key=True),  # UUID as string
        sa.Column('session_id', sa.String(36), nullable=False, index=True),
        sa.Column('workflow_type', sa.String(50), nullable=False),  # brown_paper, migration, green_paper, quality
        sa.Column('workflow_id', sa.String(36), nullable=False),

        # Progress tracking
        sa.Column('current_stage', sa.String(100), nullable=True),
        sa.Column('completed_stages', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('stage_results', postgresql.JSONB, nullable=False, server_default='{}'),

        # Context preservation
        sa.Column('shared_data', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('input_data', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('metadata', postgresql.JSONB, nullable=True),

        # Error tracking
        sa.Column('last_error', sa.Text, nullable=True),
        sa.Column('error_stage', sa.String(100), nullable=True),
        sa.Column('error_context', postgresql.JSONB, nullable=True),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),

        # Versioning & status
        sa.Column('checkpoint_version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('status', sa.String(50), nullable=False, server_default='running'),

        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('last_checkpoint_at', sa.DateTime, nullable=True),
    )

    # Create indexes for workflow_checkpoints
    op.create_index(
        'ix_workflow_checkpoints_session_type',
        'workflow_checkpoints',
        ['session_id', 'workflow_type']
    )
    op.create_index(
        'ix_workflow_checkpoints_status',
        'workflow_checkpoints',
        ['status']
    )
    op.create_index(
        'ix_workflow_checkpoints_workflow_id',
        'workflow_checkpoints',
        ['workflow_id']
    )
    op.create_index(
        'ix_workflow_checkpoints_created_at',
        'workflow_checkpoints',
        ['created_at']
    )

    # NOTE: Removed bmad_sessions column addition as this table may not exist
    # in all environments. The current_stage tracking is done via workflow_checkpoints.


def downgrade() -> None:
    # Drop workflow_checkpoints table
    op.drop_table('workflow_checkpoints')
