"""Add function_points and story_points to brown_paper_epics

Revision ID: 074
Revises: 073
Create Date: 2026-01-28

Week 159: Add estimation columns for business-driven epic generation (Fase 24.10)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '074'
down_revision = '073'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'brown_paper_epics' AND column_name = 'function_points'"
    ))
    if result.fetchone() is None:
        op.add_column('brown_paper_epics', sa.Column('function_points', sa.Integer(), server_default='0', nullable=True))
        op.add_column('brown_paper_epics', sa.Column('story_points', sa.Integer(), server_default='0', nullable=True))


def downgrade() -> None:
    op.drop_column('brown_paper_epics', 'story_points')
    op.drop_column('brown_paper_epics', 'function_points')
