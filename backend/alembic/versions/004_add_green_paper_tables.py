"""Add green-paper workflow tables

Revision ID: 004
Revises: 003
Create Date: 2025-11-18

This migration adds the 4 green-paper workflow tables:
1. green_paper_sessions - BMAD 6-question session tracking
2. green_paper_answers - Individual answers to BMAD questions
3. green_paper_constitutions - Generated project constitutions (by Peter agent)
4. green_paper_specifications - Generated HLD specifications (by Felix agent)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create green_paper_sessions table
    op.create_table(
        'green_paper_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.String(50), nullable=False),
        sa.Column('session_type', sa.String(50), nullable=False, server_default='green-paper'),
        sa.Column('status', sa.String(20), nullable=False, server_default='in_progress'),
        sa.Column('current_question', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('total_questions', sa.Integer(), nullable=True, server_default='6'),
        sa.Column('progress_percentage', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['items.id'], ondelete='CASCADE'),
        sa.CheckConstraint("status IN ('in_progress', 'completed', 'abandoned')", name='check_session_status'),
    )

    # Create indexes for green_paper_sessions
    op.create_index('ix_green_paper_sessions_project_id', 'green_paper_sessions', ['project_id'])
    op.create_index('ix_green_paper_sessions_status', 'green_paper_sessions', ['status'])

    # Create green_paper_answers table
    op.create_table(
        'green_paper_answers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_number', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('is_required', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('max_length', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['green_paper_sessions.id'], ondelete='CASCADE'),
    )

    # Create indexes for green_paper_answers
    op.create_index('ix_green_paper_answers_session_id', 'green_paper_answers', ['session_id'])

    # Create green_paper_constitutions table
    op.create_table(
        'green_paper_constitutions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('content_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('content_markdown', sa.Text(), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('generated_by', sa.String(50), nullable=True, server_default='Peter'),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', sa.String(100), nullable=True),
        sa.Column('review_feedback', sa.Text(), nullable=True),
        sa.Column('generation_attempt', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['green_paper_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['items.id'], ondelete='CASCADE'),
        sa.CheckConstraint('generation_attempt >= 1 AND generation_attempt <= 3', name='check_constitution_generation_attempt'),
        sa.CheckConstraint("status IN ('draft', 'pending_review', 'approved', 'rejected')", name='check_constitution_status'),
    )

    # Create indexes for green_paper_constitutions
    op.create_index('ix_green_paper_constitutions_session_id', 'green_paper_constitutions', ['session_id'])
    op.create_index('ix_green_paper_constitutions_project_id', 'green_paper_constitutions', ['project_id'])
    op.create_index('ix_green_paper_constitutions_status', 'green_paper_constitutions', ['status'])

    # Create green_paper_specifications table
    op.create_table(
        'green_paper_specifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('constitution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('content_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('content_markdown', sa.Text(), nullable=False),
        sa.Column('generated_by', sa.String(50), nullable=True, server_default='Felix'),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', sa.String(100), nullable=True),
        sa.Column('review_feedback', sa.Text(), nullable=True),
        sa.Column('generation_attempt', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['constitution_id'], ['green_paper_constitutions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['items.id'], ondelete='CASCADE'),
        sa.CheckConstraint('generation_attempt >= 1 AND generation_attempt <= 3', name='check_specification_generation_attempt'),
        sa.CheckConstraint("status IN ('draft', 'pending_review', 'approved', 'rejected')", name='check_specification_status'),
    )

    # Create indexes for green_paper_specifications
    op.create_index('ix_green_paper_specifications_constitution_id', 'green_paper_specifications', ['constitution_id'])
    op.create_index('ix_green_paper_specifications_project_id', 'green_paper_specifications', ['project_id'])
    op.create_index('ix_green_paper_specifications_status', 'green_paper_specifications', ['status'])


def downgrade() -> None:
    # Drop green_paper_specifications table
    op.drop_index('ix_green_paper_specifications_status', table_name='green_paper_specifications')
    op.drop_index('ix_green_paper_specifications_project_id', table_name='green_paper_specifications')
    op.drop_index('ix_green_paper_specifications_constitution_id', table_name='green_paper_specifications')
    op.drop_table('green_paper_specifications')

    # Drop green_paper_constitutions table
    op.drop_index('ix_green_paper_constitutions_status', table_name='green_paper_constitutions')
    op.drop_index('ix_green_paper_constitutions_project_id', table_name='green_paper_constitutions')
    op.drop_index('ix_green_paper_constitutions_session_id', table_name='green_paper_constitutions')
    op.drop_table('green_paper_constitutions')

    # Drop green_paper_answers table
    op.drop_index('ix_green_paper_answers_session_id', table_name='green_paper_answers')
    op.drop_table('green_paper_answers')

    # Drop green_paper_sessions table
    op.drop_index('ix_green_paper_sessions_status', table_name='green_paper_sessions')
    op.drop_index('ix_green_paper_sessions_project_id', table_name='green_paper_sessions')
    op.drop_table('green_paper_sessions')
