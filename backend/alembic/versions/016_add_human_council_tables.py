"""add_human_council_tables

Revision ID: 016_human_council
Revises: 015_add_observability_tables
Create Date: 2025-11-26 16:00:00.000000

Week 55: Human-in-the-Loop Council
Creates tables for human review workflow and document versioning:
- council_human_sessions: Extended sessions with human review capability
- council_consensus: Consensus documents with versioning and human feedback
- document_versions: MD files synced with database
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '016_human_council'
down_revision: Union[str, None] = '015_add_observability_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create council_human_sessions table
    # Extends the basic council session with human review workflow
    op.create_table(
        'council_human_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.Integer(), nullable=True),  # Can be null for platform-wide docs
        sa.Column('document_type', sa.String(length=50), nullable=False),  # 'onboarding', 'architecture', 'adr', 'specification'
        sa.Column('document_name', sa.String(length=200), nullable=True),  # Custom name for the document
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('providers_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.String(length=100), nullable=True),
        sa.Column('rejected_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_by', sa.String(length=100), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('draft', 'generating', 'peer_review', 'orchestrating', 'human_review', 'finalizing', 'approved', 'rejected')",
            name='ck_council_human_session_status'
        ),
        sa.CheckConstraint(
            "document_type IN ('onboarding', 'architecture', 'adr', 'specification', 'readme', 'api_docs', 'other')",
            name='ck_council_human_session_doc_type'
        ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_council_human_session_project', 'council_human_sessions', ['project_id'])
    op.create_index('idx_council_human_session_status', 'council_human_sessions', ['status'])
    op.create_index('idx_council_human_session_doc_type', 'council_human_sessions', ['document_type'])

    # Create council_provider_responses table
    # Stores individual provider responses for human review
    op.create_table(
        'council_provider_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),  # 'ollama/qwen2.5-coder', 'claude/sonnet', 'codex/gpt-5.1-max'
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('generation_time_ms', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['council_human_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_council_provider_response_session', 'council_provider_responses', ['session_id'])
    op.create_index('idx_council_provider_response_provider', 'council_provider_responses', ['provider_name'])

    # Create council_peer_reviews table
    # Stores peer reviews from round-robin evaluation
    op.create_table(
        'council_peer_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reviewer_provider', sa.String(length=100), nullable=False),  # Who reviewed
        sa.Column('reviewed_provider', sa.String(length=100), nullable=False),  # Who was reviewed
        sa.Column('score', sa.Integer(), nullable=False),  # 0-100
        sa.Column('strengths', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('weaknesses', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('suggestions', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('consensus_contribution', sa.Text(), nullable=True),  # What to keep in consensus
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            'score >= 0 AND score <= 100',
            name='ck_council_peer_review_score'
        ),
        sa.ForeignKeyConstraint(['session_id'], ['council_human_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_council_peer_review_session', 'council_peer_reviews', ['session_id'])

    # Create council_consensus table
    # Stores consensus documents with versioning and human feedback
    op.create_table(
        'council_consensus',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('consensus_content', sa.Text(), nullable=False),
        sa.Column('orchestrator_notes', sa.Text(), nullable=True),  # Orchestrator's synthesis reasoning
        sa.Column('human_feedback', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # Human corrections/additions
        sa.Column('human_marked_correct', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # Items marked correct per provider
        sa.Column('human_conflicts_resolved', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # How conflicts were resolved
        sa.Column('human_additions', sa.Text(), nullable=True),  # What human added that all LLMs missed
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['council_human_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'version', name='uq_council_consensus_session_version')
    )
    op.create_index('idx_council_consensus_session', 'council_consensus', ['session_id'])

    # Create document_versions table
    # Stores versioned documents synced with MD files
    op.create_table(
        'document_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),  # Can be null for platform docs
        sa.Column('document_path', sa.String(length=500), nullable=False),  # 'docs/ONBOARDING.md'
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=True),  # SHA256 for change detection
        sa.Column('council_session_id', postgresql.UUID(as_uuid=True), nullable=True),  # Link to council session if generated
        sa.Column('created_by', sa.String(length=100), nullable=True),  # 'council', 'human', 'sync'
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['council_session_id'], ['council_human_sessions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'document_path', 'version', name='uq_document_version')
    )
    op.create_index('idx_document_version_project', 'document_versions', ['project_id'])
    op.create_index('idx_document_version_path', 'document_versions', ['document_path'])
    op.create_index('idx_document_version_type', 'document_versions', ['document_type'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_index('idx_document_version_type', table_name='document_versions')
    op.drop_index('idx_document_version_path', table_name='document_versions')
    op.drop_index('idx_document_version_project', table_name='document_versions')
    op.drop_table('document_versions')

    op.drop_index('idx_council_consensus_session', table_name='council_consensus')
    op.drop_table('council_consensus')

    op.drop_index('idx_council_peer_review_session', table_name='council_peer_reviews')
    op.drop_table('council_peer_reviews')

    op.drop_index('idx_council_provider_response_provider', table_name='council_provider_responses')
    op.drop_index('idx_council_provider_response_session', table_name='council_provider_responses')
    op.drop_table('council_provider_responses')

    op.drop_index('idx_council_human_session_doc_type', table_name='council_human_sessions')
    op.drop_index('idx_council_human_session_status', table_name='council_human_sessions')
    op.drop_index('idx_council_human_session_project', table_name='council_human_sessions')
    op.drop_table('council_human_sessions')
