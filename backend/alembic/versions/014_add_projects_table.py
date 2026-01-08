"""Add projects table

Revision ID: 014
Revises: 013_add_gradual_rollout_tables
Create Date: 2025-11-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '014_add_projects_table'
down_revision = 'c3d8e9f7a123'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create projects table for wizard-created projects."""
    # Skip if table already exists (created in earlier migration)
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'projects')"
    ))
    if result.scalar():
        return

    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(30), default='active', index=True),

        # Template and workflow
        sa.Column('template', sa.String(50), default='web-app'),
        sa.Column('workflow', sa.String(50), default='spec-kit'),

        # Tech stack
        sa.Column('language', sa.String(50)),
        sa.Column('framework', sa.String(50)),
        sa.Column('database', sa.String(50)),
        sa.Column('repo_url', sa.String(500)),

        # Team configuration
        sa.Column('sprint_duration', sa.Integer(), default=2),
        sa.Column('working_hours', sa.Integer(), default=8),

        # Quality settings
        sa.Column('quality_gates', sa.String(20), default='standard'),
        sa.Column('auto_assign', sa.Boolean(), default=True),

        # Team members as JSON
        sa.Column('team', JSONB, default=list),

        # Additional metadata
        sa.Column('metadata', JSONB, default=dict),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    """Drop projects table."""
    op.drop_table('projects')
