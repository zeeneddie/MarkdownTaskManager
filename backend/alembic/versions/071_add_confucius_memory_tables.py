"""Add Confucius memory tables.

Revision ID: 071_add_confucius_memory_tables
Revises: 070_add_workflow_separation_tables
Create Date: 2026-01-13

Tables:
- confucius_sessions: Cross-task memory (permanent)
- confucius_entries: Per-task memory (30 days)
- confucius_runnables: Tool execution outputs (7 days)
- confucius_notes: Cross-session learning notes
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '071_add_confucius_memory_tables'
down_revision = '070_add_workflow_separation_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Confucius Sessions (cross-task memory, permanent)
    op.create_table(
        'confucius_sessions',
        sa.Column('session_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.String(255), nullable=False, index=True),
        sa.Column('insights', JSONB, server_default='[]'),
        sa.Column('patterns', JSONB, server_default='[]'),
        sa.Column('decisions', JSONB, server_default='[]'),
        sa.Column('preferences', JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Confucius Entries (per-task memory, 30 days retention)
    op.create_table(
        'confucius_entries',
        sa.Column('entry_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('confucius_sessions.session_id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('task', sa.Text, nullable=False),
        sa.Column('context_summary', sa.Text, server_default=''),
        sa.Column('results_summary', sa.Text, server_default=''),
        sa.Column('quality_score', sa.Float, server_default='0.0'),
        sa.Column('iterations_used', sa.Integer, server_default='1'),
        sa.Column('extensions_called', JSONB, server_default='[]'),
        sa.Column('metadata', JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), index=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )

    # Confucius Runnables (per-extension call, 7 days retention)
    op.create_table(
        'confucius_runnables',
        sa.Column('runnable_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('entry_id', UUID(as_uuid=True), sa.ForeignKey('confucius_entries.entry_id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('extension_name', sa.String(100), nullable=False, index=True),
        sa.Column('input_summary', sa.Text, server_default=''),
        sa.Column('output_summary', sa.Text, server_default=''),
        sa.Column('output_data', JSONB, server_default='{}'),
        sa.Column('duration_ms', sa.Integer, server_default='0'),
        sa.Column('success', sa.Boolean, server_default='true'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), index=True),
    )

    # Confucius Notes (cross-session learning)
    op.create_table(
        'confucius_notes',
        sa.Column('note_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('confucius_sessions.session_id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('note_type', sa.String(50), nullable=False, index=True),  # success, failure, insight, pattern, decision
        sa.Column('problem', sa.Text, nullable=False),
        sa.Column('solution', sa.Text, nullable=True),
        sa.Column('insights', JSONB, server_default='[]'),
        sa.Column('context_tags', JSONB, server_default='[]'),
        sa.Column('quality_score', sa.Float, server_default='0.0'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), index=True),
    )

    # Create indexes for efficient querying
    op.create_index(
        'ix_confucius_entries_quality_score',
        'confucius_entries',
        ['quality_score'],
    )
    op.create_index(
        'ix_confucius_notes_context_tags',
        'confucius_notes',
        ['context_tags'],
        postgresql_using='gin',
    )


def downgrade() -> None:
    op.drop_index('ix_confucius_notes_context_tags', table_name='confucius_notes')
    op.drop_index('ix_confucius_entries_quality_score', table_name='confucius_entries')
    op.drop_table('confucius_notes')
    op.drop_table('confucius_runnables')
    op.drop_table('confucius_entries')
    op.drop_table('confucius_sessions')
