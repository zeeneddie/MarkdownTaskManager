"""Fix workflow_checkpoints timestamp columns to include timezone.

Revision ID: 076_fix_checkpoint_timestamps_timezone
Revises: 075_add_unified_onboarding
Create Date: 2026-02-03

Fase 24.9: Fix timezone-naive vs timezone-aware mismatch.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '076'
down_revision = '075'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fix started_at to include timezone
    op.alter_column(
        'workflow_checkpoints',
        'started_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=False,
    )

    # Fix last_checkpoint_at to include timezone
    op.alter_column(
        'workflow_checkpoints',
        'last_checkpoint_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=True,
    )


def downgrade() -> None:
    # Revert started_at
    op.alter_column(
        'workflow_checkpoints',
        'started_at',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )

    # Revert last_checkpoint_at
    op.alter_column(
        'workflow_checkpoints',
        'last_checkpoint_at',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
