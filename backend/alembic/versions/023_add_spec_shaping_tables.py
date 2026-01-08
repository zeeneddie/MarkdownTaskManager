"""Add spec shaping tables for iteration loop

Week 59: Agent OS Integration - Spec Shaping Loop
Tracks specification iterations until quality gates pass.

Revision ID: 023
Revises: 022
Create Date: 2025-12-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '023'
down_revision = '022_project_agent_config'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Spec shaping sessions - tracks the overall shaping process
    op.create_table(
        'spec_shaping_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('workflow_type', sa.String(50), nullable=False),
        sa.Column('initial_description', sa.Text(), nullable=False),
        sa.Column('current_spec', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('iteration_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_iterations', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_spec_shaping_sessions_status', 'spec_shaping_sessions', ['status'])
    op.create_index('ix_spec_shaping_sessions_project_id', 'spec_shaping_sessions', ['project_id'])

    # Spec iterations - tracks each shape/verify cycle
    op.create_table(
        'spec_iterations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('iteration_number', sa.Integer(), nullable=False),
        sa.Column('input_spec', sa.Text(), nullable=False),
        sa.Column('output_spec', sa.Text(), nullable=True),
        sa.Column('shaping_prompt', sa.Text(), nullable=True),
        sa.Column('agent_used', sa.String(50), nullable=True),
        sa.Column('llm_model', sa.String(100), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['session_id'], ['spec_shaping_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_spec_iterations_session_id', 'spec_iterations', ['session_id'])

    # Spec verification results - tracks quality gate checks per iteration
    op.create_table(
        'spec_verifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('iteration_id', sa.Integer(), nullable=False),
        sa.Column('check_name', sa.String(100), nullable=False),
        sa.Column('check_category', sa.String(50), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('suggestions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['iteration_id'], ['spec_iterations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_spec_verifications_iteration_id', 'spec_verifications', ['iteration_id'])
    op.create_index('ix_spec_verifications_check_name', 'spec_verifications', ['check_name'])


def downgrade() -> None:
    op.drop_table('spec_verifications')
    op.drop_table('spec_iterations')
    op.drop_table('spec_shaping_sessions')
