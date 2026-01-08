"""Add browser automation tables for Week 78

Revision ID: 033
Revises: 032_layered_analysis
Create Date: 2025-12-16

Tables:
- playwriter_sessions: Browser automation sessions
- playwriter_executions: Code execution history
- playwriter_tabs: Tab permission management
- bigagi_validations: Multi-model validation sessions
- bigagi_responses: Individual model responses
- bigagi_consensus: Consensus results
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '033'
down_revision = '032_layered_analysis'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Playwriter Sessions - Browser automation sessions
    op.create_table(
        'playwriter_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('browser_type', sa.String(50), default='chromium'),  # chromium, firefox, webkit
        sa.Column('headless', sa.Boolean, default=True),
        sa.Column('viewport_width', sa.Integer, default=1280),
        sa.Column('viewport_height', sa.Integer, default=720),
        sa.Column('status', sa.String(50), default='created'),  # created, active, closed, error
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('context_options', JSONB, default={}),  # Extra browser context options
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('closed_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_playwriter_sessions_status', 'playwriter_sessions', ['status'])

    # Playwriter Executions - Code execution history
    op.create_table(
        'playwriter_executions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('playwriter_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tab_id', sa.Integer, nullable=True),
        sa.Column('code', sa.Text, nullable=False),  # Playwright code to execute
        sa.Column('result', JSONB, nullable=True),  # Execution result
        sa.Column('screenshot_path', sa.String(500), nullable=True),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('execution_time_ms', sa.Integer, nullable=True),
        sa.Column('status', sa.String(50), default='pending'),  # pending, running, completed, failed
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_playwriter_executions_session', 'playwriter_executions', ['session_id'])
    op.create_index('ix_playwriter_executions_status', 'playwriter_executions', ['status'])

    # Playwriter Tabs - Tab permission management
    op.create_table(
        'playwriter_tabs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('playwriter_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tab_index', sa.Integer, nullable=False),
        sa.Column('url', sa.String(2000), nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('permitted', sa.Boolean, default=False),  # Has user granted permission?
        sa.Column('permitted_at', sa.DateTime, nullable=True),
        sa.Column('permitted_by', sa.String(100), nullable=True),
        sa.Column('last_accessed', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_playwriter_tabs_session', 'playwriter_tabs', ['session_id'])
    op.create_unique_constraint('uq_playwriter_tabs_session_index', 'playwriter_tabs', ['session_id', 'tab_index'])

    # BigAGI Validations - Multi-model validation sessions
    op.create_table(
        'bigagi_validations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('task', sa.Text, nullable=False),  # The task/question being validated
        sa.Column('primary_response', sa.Text, nullable=False),  # Primary model's response
        sa.Column('primary_model', sa.String(100), nullable=False),  # e.g., claude-3-sonnet
        sa.Column('validation_models', JSONB, nullable=False),  # List of models to validate with
        sa.Column('status', sa.String(50), default='pending'),  # pending, validating, completed, failed
        sa.Column('consensus_score', sa.Float, nullable=True),  # 0-1 agreement score
        sa.Column('consensus_reached', sa.Boolean, nullable=True),
        sa.Column('final_answer', sa.Text, nullable=True),
        sa.Column('session_metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_bigagi_validations_status', 'bigagi_validations', ['status'])
    op.create_index('ix_bigagi_validations_consensus', 'bigagi_validations', ['consensus_reached'])

    # BigAGI Responses - Individual model responses
    op.create_table(
        'bigagi_responses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('validation_id', UUID(as_uuid=True), sa.ForeignKey('bigagi_validations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),  # Model name
        sa.Column('provider', sa.String(50), nullable=False),  # ollama, claude, openai, etc.
        sa.Column('response', sa.Text, nullable=False),
        sa.Column('thinking', sa.Text, nullable=True),  # Extracted reasoning
        sa.Column('confidence', sa.Float, nullable=True),  # Self-reported confidence
        sa.Column('agreement_score', sa.Float, nullable=True),  # Agreement with primary
        sa.Column('tokens_used', sa.Integer, nullable=True),
        sa.Column('latency_ms', sa.Integer, nullable=True),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_bigagi_responses_validation', 'bigagi_responses', ['validation_id'])
    op.create_index('ix_bigagi_responses_model', 'bigagi_responses', ['model'])

    # BigAGI Consensus - Consensus calculation results
    op.create_table(
        'bigagi_consensus',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('validation_id', UUID(as_uuid=True), sa.ForeignKey('bigagi_validations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('method', sa.String(50), nullable=False),  # majority, weighted, unanimous
        sa.Column('agreement_matrix', JSONB, nullable=True),  # Model-to-model agreement
        sa.Column('key_agreements', JSONB, default=[]),  # Points all models agree on
        sa.Column('key_disagreements', JSONB, default=[]),  # Points of contention
        sa.Column('synthesis', sa.Text, nullable=True),  # Synthesized answer
        sa.Column('confidence', sa.Float, nullable=True),  # Overall confidence
        sa.Column('recommendation', sa.String(100), nullable=True),  # accept, review, reject
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_bigagi_consensus_validation', 'bigagi_consensus', ['validation_id'])


def downgrade() -> None:
    op.drop_table('bigagi_consensus')
    op.drop_table('bigagi_responses')
    op.drop_table('bigagi_validations')
    op.drop_table('playwriter_tabs')
    op.drop_table('playwriter_executions')
    op.drop_table('playwriter_sessions')
