"""Add kanban columns to items table

Revision ID: 050_add_item_kanban_columns
Revises: 049_add_week100_cycle0_conflict_tables
Create Date: 2024-12-24

Week 113: Add lane, tags, source_extraction_id to items table for kanban and extraction integration.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '050_add_item_kanban_columns'
down_revision = '049_add_week100_cycle0_conflict_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to items table
    op.add_column('items', sa.Column('lane', sa.String(30), nullable=True))
    op.add_column('items', sa.Column('tags', sa.Text(), nullable=True))
    op.add_column('items', sa.Column('source_extraction_id', sa.String(50), nullable=True))

    # Create indexes
    op.create_index('ix_items_lane', 'items', ['lane'])
    op.create_index('ix_items_source_extraction_id', 'items', ['source_extraction_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_items_source_extraction_id', 'items')
    op.drop_index('ix_items_lane', 'items')

    # Drop columns
    op.drop_column('items', 'source_extraction_id')
    op.drop_column('items', 'tags')
    op.drop_column('items', 'lane')
