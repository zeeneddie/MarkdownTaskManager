"""Add BMAD Sessions Table for Persistence

Revision ID: 067
Revises: 066
Create Date: 2026-01-04

Week 144 - Fase 28: BMAD Persistentie

Tables:
- bmad_sessions: BMAD 8-question workflow sessions with JSONB answers
- bmad_answers: Individual answers per session (normalized)

Features:
- Resume interrupted sessions
- Session history per project
- Answer versioning with timestamps
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '067'
down_revision = '066'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old bmad_sessions table from migration 003 (different schema)
    # The old table has: id INTEGER, project_id FK, session_type, chroma_document_id
    # The new table has: id UUID, customer_id FK, status, workflow_type, answers JSONB, etc.
    op.execute('DROP INDEX IF EXISTS ix_bmad_sessions_chroma')
    op.execute('DROP INDEX IF EXISTS ix_bmad_sessions_type')
    op.execute('DROP INDEX IF EXISTS ix_bmad_sessions_project')
    op.execute('DROP TABLE IF EXISTS bmad_sessions CASCADE')

    # Create new bmad_sessions table with comprehensive schema
    op.create_table(
        'bmad_sessions',
        sa.Column('id', sa.String(36), primary_key=True),  # UUID as string
        sa.Column('project_name', sa.String(255), nullable=False),
        sa.Column('project_path', sa.String(1024), nullable=True),
        sa.Column('customer_id', sa.Integer, sa.ForeignKey('customers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='questions'),
        sa.Column('current_question', sa.Integer, nullable=False, server_default='1'),
        sa.Column('workflow_type', sa.String(50), nullable=False, server_default='brown_paper'),  # brown_paper, green_paper

        # JSONB columns for complex data
        sa.Column('answers', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('migration_analysis', postgresql.JSONB, nullable=True),
        sa.Column('specification', postgresql.JSONB, nullable=True),
        sa.Column('tasks', postgresql.JSONB, nullable=True),
        sa.Column('enhanced_analysis', postgresql.JSONB, nullable=True),  # 6-phase analysis results

        # Metadata
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),

        # Tracking
        sa.Column('created_by', sa.String(255), nullable=True),  # User who started session
        sa.Column('last_modified_by', sa.String(255), nullable=True),
    )

    # Create indexes for bmad_sessions
    op.create_index('ix_bmad_sessions_project_name', 'bmad_sessions', ['project_name'])
    op.create_index('ix_bmad_sessions_customer_id', 'bmad_sessions', ['customer_id'])
    op.create_index('ix_bmad_sessions_status', 'bmad_sessions', ['status'])
    op.create_index('ix_bmad_sessions_workflow_type', 'bmad_sessions', ['workflow_type'])
    op.create_index('ix_bmad_sessions_created_at', 'bmad_sessions', ['created_at'])

    # Create bmad_answers table for normalized answer storage
    op.create_table(
        'bmad_answers',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('bmad_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_number', sa.Integer, nullable=False),
        sa.Column('question_text', sa.Text, nullable=False),
        sa.Column('answer', sa.Text, nullable=False),
        sa.Column('answered_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),  # For answer revisions
        sa.Column('is_current', sa.Boolean, nullable=False, server_default='true'),
    )

    # Create partial unique index for one current answer per question per session
    op.create_index(
        'uq_bmad_answers_session_question_current',
        'bmad_answers',
        ['session_id', 'question_number'],
        unique=True,
        postgresql_where=sa.text('is_current = true')
    )

    # Create indexes for bmad_answers
    op.create_index('ix_bmad_answers_session_id', 'bmad_answers', ['session_id'])
    op.create_index('ix_bmad_answers_question_number', 'bmad_answers', ['question_number'])
    op.create_index('ix_bmad_answers_is_current', 'bmad_answers', ['is_current'])

    # Create bmad_session_events table for audit trail
    op.create_table(
        'bmad_session_events',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('bmad_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),  # started, answer_submitted, analysis_started, etc.
        sa.Column('event_data', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(255), nullable=True),
    )

    # Create indexes for bmad_session_events
    op.create_index('ix_bmad_session_events_session_id', 'bmad_session_events', ['session_id'])
    op.create_index('ix_bmad_session_events_event_type', 'bmad_session_events', ['event_type'])
    op.create_index('ix_bmad_session_events_created_at', 'bmad_session_events', ['created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('bmad_session_events')
    op.drop_table('bmad_answers')
    op.drop_table('bmad_sessions')
