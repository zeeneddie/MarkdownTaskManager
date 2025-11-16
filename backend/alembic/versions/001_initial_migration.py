"""Initial migration - create items and sprints tables

Revision ID: 001
Revises:
Create Date: 2025-11-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create items table
    op.create_table(
        'items',
        sa.Column('id', sa.String(50), nullable=False),
        sa.Column('type', sa.Enum('EPIC', 'FEATURE', 'STORY', 'TASK', name='itemtype'), nullable=False),
        sa.Column('parent_id', sa.String(50), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('status', sa.String(30), nullable=True),
        sa.Column('priority', sa.String(20), nullable=True),
        sa.Column('owner', sa.String(100), nullable=True),
        sa.Column('assigned_to', sa.String(100), nullable=True),
        sa.Column('sp', sa.Integer(), nullable=True),
        sa.Column('sp_total', sa.Integer(), nullable=True, default=0),
        sa.Column('sp_completed', sa.Integer(), nullable=True, default=0),
        sa.Column('hours', sa.Integer(), nullable=True),
        sa.Column('sprint', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('target_date', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('markdown_full', sa.Text(), nullable=True),
        sa.Column('item_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['items.id'], ondelete='CASCADE'),
    )

    # Create indexes for items table
    op.create_index('ix_items_type', 'items', ['type'])
    op.create_index('ix_items_parent_id', 'items', ['parent_id'])
    op.create_index('ix_items_status', 'items', ['status'])
    op.create_index('ix_items_sprint', 'items', ['sprint'])

    # Create sprints table
    op.create_table(
        'sprints',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('goal', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, default='PLANNED'),
        sa.Column('total_sp', sa.Integer(), nullable=True, default=0),
        sa.Column('completed_sp', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # Create indexes for sprints table
    op.create_index('ix_sprints_name', 'sprints', ['name'])
    op.create_index('ix_sprints_status', 'sprints', ['status'])


def downgrade() -> None:
    op.drop_index('ix_sprints_status', table_name='sprints')
    op.drop_index('ix_sprints_name', table_name='sprints')
    op.drop_table('sprints')

    op.drop_index('ix_items_sprint', table_name='items')
    op.drop_index('ix_items_status', table_name='items')
    op.drop_index('ix_items_parent_id', table_name='items')
    op.drop_index('ix_items_type', table_name='items')
    op.drop_table('items')

    sa.Enum('EPIC', 'FEATURE', 'STORY', 'TASK', name='itemtype').drop(op.get_bind())
