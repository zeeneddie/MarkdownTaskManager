"""add_llm_council_tables

Revision ID: babf2cfd359e
Revises: 846bf79a97f4
Create Date: 2025-11-25 11:49:22.773414

Week 52: LLM Council Multi-Model Decision Making
Creates 4 tables for 3-stage consensus process: Response → Peer Review → Synthesis
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'babf2cfd359e'
down_revision: Union[str, None] = '846bf79a97f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create council_sessions table
    op.create_table(
        'council_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('decision_type', sa.String(length=50), nullable=False),
        sa.Column('agent_id', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'reviewing', 'complete')",
            name='ck_council_session_status'
        ),
        sa.CheckConstraint(
            "decision_type IN ('architecture', 'planning', 'quality', 'generation')",
            name='ck_council_session_decision_type'
        ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_council_session_agent_status', 'council_sessions', ['agent_id', 'status'])
    op.create_index(op.f('ix_council_sessions_agent_id'), 'council_sessions', ['agent_id'])

    # Create council_responses table
    op.create_table(
        'council_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            'confidence >= 0.0 AND confidence <= 1.0',
            name='ck_council_response_confidence'
        ),
        sa.ForeignKeyConstraint(['session_id'], ['council_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_council_response_session', 'council_responses', ['session_id'])

    # Create council_reviews table
    op.create_table(
        'council_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reviewer_model', sa.String(length=100), nullable=False),
        sa.Column('reviewed_response_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('accuracy_score', sa.Float(), nullable=False),
        sa.Column('completeness_score', sa.Float(), nullable=False),
        sa.Column('clarity_score', sa.Float(), nullable=False),
        sa.Column('feasibility_score', sa.Float(), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            'accuracy_score >= 0.0 AND accuracy_score <= 10.0',
            name='ck_council_review_accuracy'
        ),
        sa.CheckConstraint(
            'completeness_score >= 0.0 AND completeness_score <= 10.0',
            name='ck_council_review_completeness'
        ),
        sa.CheckConstraint(
            'clarity_score >= 0.0 AND clarity_score <= 10.0',
            name='ck_council_review_clarity'
        ),
        sa.CheckConstraint(
            'feasibility_score >= 0.0 AND feasibility_score <= 10.0',
            name='ck_council_review_feasibility'
        ),
        sa.ForeignKeyConstraint(['session_id'], ['council_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_response_id'], ['council_responses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_council_review_session', 'council_reviews', ['session_id'])
    op.create_index('idx_council_review_response', 'council_reviews', ['reviewed_response_id'])

    # Create council_decisions table
    op.create_table(
        'council_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chairman_model', sa.String(length=100), nullable=False),
        sa.Column('final_decision', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('consensus_level', sa.Float(), nullable=False),
        sa.Column('dissenting_opinions', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('synthesis_reasoning', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            'confidence >= 0.0 AND confidence <= 1.0',
            name='ck_council_decision_confidence'
        ),
        sa.CheckConstraint(
            'consensus_level >= 0.0 AND consensus_level <= 100.0',
            name='ck_council_decision_consensus'
        ),
        sa.ForeignKeyConstraint(['session_id'], ['council_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index('idx_council_decision_session', 'council_decisions', ['session_id'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_index('idx_council_decision_session', table_name='council_decisions')
    op.drop_table('council_decisions')

    op.drop_index('idx_council_review_response', table_name='council_reviews')
    op.drop_index('idx_council_review_session', table_name='council_reviews')
    op.drop_table('council_reviews')

    op.drop_index('idx_council_response_session', table_name='council_responses')
    op.drop_table('council_responses')

    op.drop_index(op.f('ix_council_sessions_agent_id'), table_name='council_sessions')
    op.drop_index('idx_council_session_agent_status', table_name='council_sessions')
    op.drop_table('council_sessions')
