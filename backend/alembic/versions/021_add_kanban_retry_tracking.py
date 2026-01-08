"""Add kanban retry tracking tables

Revision ID: 021_kanban_retry
Revises: 020_bug_tracking
Create Date: 2025-12-01

Week 58: Retry tracking for Build ↔ Test lane transitions.
Tracks agent actions and escalations to Human Needed lane.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '021_kanban_retry'
down_revision = '020_bug_tracking'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Kanban Retry Logs - tracks Build ↔ Test transitions
    op.create_table(
        'kanban_retry_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', sa.String(100), nullable=False),
        sa.Column('item_type', sa.String(20), nullable=False),  # story, task, bug
        sa.Column('from_lane', sa.String(20), nullable=False),
        sa.Column('to_lane', sa.String(20), nullable=False),
        sa.Column('attempt', sa.Integer(), nullable=False, default=1),
        sa.Column('result', sa.String(20), nullable=False, default='pending'),  # pending, success, failed, escalated
        sa.Column('agent_used', sa.String(50), nullable=True),
        sa.Column('analysis', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_kanban_retry_logs_item_id', 'kanban_retry_logs', ['item_id'])
    op.create_index('ix_kanban_retry_logs_result', 'kanban_retry_logs', ['result'])
    op.create_index('ix_kanban_retry_logs_created_at', 'kanban_retry_logs', ['created_at'])

    # Kanban Agent Actions - tracks all agent actions per item
    op.create_table(
        'kanban_agent_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', sa.String(100), nullable=False),
        sa.Column('item_type', sa.String(20), nullable=False),
        sa.Column('lane', sa.String(20), nullable=False),
        sa.Column('agent_name', sa.String(50), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False, default=False),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_kanban_agent_actions_item_id', 'kanban_agent_actions', ['item_id'])
    op.create_index('ix_kanban_agent_actions_agent_name', 'kanban_agent_actions', ['agent_name'])
    op.create_index('ix_kanban_agent_actions_lane', 'kanban_agent_actions', ['lane'])
    op.create_index('ix_kanban_agent_actions_created_at', 'kanban_agent_actions', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_kanban_agent_actions_created_at', table_name='kanban_agent_actions')
    op.drop_index('ix_kanban_agent_actions_lane', table_name='kanban_agent_actions')
    op.drop_index('ix_kanban_agent_actions_agent_name', table_name='kanban_agent_actions')
    op.drop_index('ix_kanban_agent_actions_item_id', table_name='kanban_agent_actions')
    op.drop_table('kanban_agent_actions')

    op.drop_index('ix_kanban_retry_logs_created_at', table_name='kanban_retry_logs')
    op.drop_index('ix_kanban_retry_logs_result', table_name='kanban_retry_logs')
    op.drop_index('ix_kanban_retry_logs_item_id', table_name='kanban_retry_logs')
    op.drop_table('kanban_retry_logs')
