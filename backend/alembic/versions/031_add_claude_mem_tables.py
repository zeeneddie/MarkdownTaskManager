"""Week 76: Add Claude-Mem Session Memory tables

Revision ID: 031_claude_mem
Revises: 030_graph_persistence
Create Date: 2025-12-16

Tables:
- claude_mem_observations: Session observations with tagging
- claude_mem_summaries: Compressed memory summaries
- claude_mem_sessions: Session metadata and endless mode tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

# revision identifiers
revision = '031_claude_mem'
down_revision = '030_graph_persistence'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Claude-Mem Sessions - session metadata and endless mode config
    op.create_table(
        'claude_mem_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', sa.String(100), nullable=False, unique=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        sa.Column('title', sa.String(255)),
        sa.Column('endless_mode', sa.Boolean, default=False),
        sa.Column('token_budget', sa.Integer, default=4000),  # Max tokens for context window
        sa.Column('compression_ratio', sa.Float, default=0.1),  # Target compression
        sa.Column('auto_tag', sa.Boolean, default=True),
        sa.Column('session_data', JSONB, default=dict),  # Session metadata
        sa.Column('last_activity', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Claude-Mem Observations - captured insights during sessions
    op.create_table(
        'claude_mem_observations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', sa.String(100), sa.ForeignKey('claude_mem_sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('tags', JSONB, default=list),  # ["decision", "bugfix", "architecture"]
        sa.Column('priority', sa.String(20), default='normal'),  # critical, high, normal, low
        sa.Column('observation_type', sa.String(50)),  # insight, decision, error, progress
        sa.Column('source_context', sa.Text),  # Where the observation came from
        sa.Column('related_files', JSONB, default=list),  # Related file paths
        sa.Column('embedding_status', sa.String(20), default='pending'),  # pending, computed, failed
        sa.Column('observation_data', JSONB, default=dict),  # Additional metadata
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Claude-Mem Summaries - compressed versions of observations
    op.create_table(
        'claude_mem_summaries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', sa.String(100), sa.ForeignKey('claude_mem_sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('original_count', sa.Integer, default=0),  # Number of observations summarized
        sa.Column('summary', sa.Text, nullable=False),
        sa.Column('compression_ratio', sa.Float),  # Actual compression achieved
        sa.Column('token_count', sa.Integer),  # Tokens in summary
        sa.Column('tags_summary', JSONB, default=dict),  # Tag frequency counts
        sa.Column('time_range_start', sa.DateTime),  # When first obs was captured
        sa.Column('time_range_end', sa.DateTime),  # When last obs was captured
        sa.Column('summary_data', JSONB, default=dict),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Claude-Mem Search Index - FTS and similarity search support
    op.create_table(
        'claude_mem_search_index',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('observation_id', UUID(as_uuid=True), sa.ForeignKey('claude_mem_observations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('search_text', sa.Text),  # Normalized text for FTS
        sa.Column('tsvector', sa.Text),  # PostgreSQL tsvector (computed on insert)
        sa.Column('chunk_number', sa.Integer, default=0),  # For long observations split into chunks
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Claude-Mem Context Windows - generated context for sessions
    op.create_table(
        'claude_mem_context_windows',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', sa.String(100), sa.ForeignKey('claude_mem_sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('context_text', sa.Text, nullable=False),  # Generated context
        sa.Column('token_count', sa.Integer),
        sa.Column('included_observations', JSONB, default=list),  # Observation IDs included
        sa.Column('included_summaries', JSONB, default=list),  # Summary IDs included
        sa.Column('generation_strategy', sa.String(50)),  # recent, priority, search
        sa.Column('context_data', JSONB, default=dict),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Indexes for performance
    op.create_index('ix_claude_mem_sessions_session_id', 'claude_mem_sessions', ['session_id'])
    op.create_index('ix_claude_mem_sessions_project', 'claude_mem_sessions', ['project_id'])
    op.create_index('ix_claude_mem_observations_session', 'claude_mem_observations', ['session_id'])
    op.create_index('ix_claude_mem_observations_priority', 'claude_mem_observations', ['priority'])
    op.create_index('ix_claude_mem_observations_created', 'claude_mem_observations', ['created_at'])
    op.create_index('ix_claude_mem_summaries_session', 'claude_mem_summaries', ['session_id'])
    op.create_index('ix_claude_mem_search_observation', 'claude_mem_search_index', ['observation_id'])
    op.create_index('ix_claude_mem_context_session', 'claude_mem_context_windows', ['session_id'])

    # Create GIN index for tags (JSONB array search)
    op.execute(
        "CREATE INDEX ix_claude_mem_observations_tags ON claude_mem_observations USING GIN (tags)"
    )


def downgrade() -> None:
    # Drop GIN index
    op.execute("DROP INDEX IF EXISTS ix_claude_mem_observations_tags")

    # Drop indexes
    op.drop_index('ix_claude_mem_context_session')
    op.drop_index('ix_claude_mem_search_observation')
    op.drop_index('ix_claude_mem_summaries_session')
    op.drop_index('ix_claude_mem_observations_created')
    op.drop_index('ix_claude_mem_observations_priority')
    op.drop_index('ix_claude_mem_observations_session')
    op.drop_index('ix_claude_mem_sessions_project')
    op.drop_index('ix_claude_mem_sessions_session_id')

    # Drop tables
    op.drop_table('claude_mem_context_windows')
    op.drop_table('claude_mem_search_index')
    op.drop_table('claude_mem_summaries')
    op.drop_table('claude_mem_observations')
    op.drop_table('claude_mem_sessions')
