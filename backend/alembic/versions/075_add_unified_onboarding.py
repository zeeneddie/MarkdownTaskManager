"""Add unified_onboarding_sessions table and reconciliation_data column

Revision ID: 075
Revises: 074
Create Date: 2026-01-28

Unified Onboarding: 4e Brown Paper workflow that orchestrates the 3 existing
workflows and adds a Reconciliation step.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision = '075'
down_revision = '074'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create unified_onboarding_sessions table
    op.create_table(
        'unified_onboarding_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('marqed_session_id', sa.String(36), sa.ForeignKey('marqed_sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('brown_paper_session_id', UUID(as_uuid=True), sa.ForeignKey('brown_paper_sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('project_name', sa.String(255), nullable=False),
        sa.Column('project_path', sa.String(1024), nullable=True),
        sa.Column('status', sa.String(30), server_default='initialized', nullable=False),
        sa.Column('current_step', sa.Integer(), server_default='0'),
        sa.Column('step_1_result', JSONB, nullable=True),
        sa.Column('step_2_result', JSONB, nullable=True),
        sa.Column('step_3_result', JSONB, nullable=True),
        sa.Column('step_4_result', JSONB, nullable=True),
        sa.Column('step_5_result', JSONB, nullable=True),
        sa.Column('step_6_result', JSONB, nullable=True),
        sa.Column('step_7_result', JSONB, nullable=True),
        sa.Column('step_8_result', JSONB, nullable=True),
        sa.Column('unified_constitution_id', UUID(as_uuid=True), sa.ForeignKey('brown_paper_constitutions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('step_timings', JSONB, server_default='{}'),
        sa.Column('total_duration_ms', sa.Integer(), nullable=True),
        sa.Column('tier', sa.String(20), server_default='ENTERPRISE'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )

    # Indexes
    op.create_index('idx_unified_onboarding_marqed', 'unified_onboarding_sessions', ['marqed_session_id'])
    op.create_index('idx_unified_onboarding_status', 'unified_onboarding_sessions', ['status'])

    # Add reconciliation_data column to brown_paper_epics
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'brown_paper_epics' AND column_name = 'reconciliation_data'"
    ))
    if result.fetchone() is None:
        op.add_column('brown_paper_epics', sa.Column('reconciliation_data', JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column('brown_paper_epics', 'reconciliation_data')
    op.drop_index('idx_unified_onboarding_status', table_name='unified_onboarding_sessions')
    op.drop_index('idx_unified_onboarding_marqed', table_name='unified_onboarding_sessions')
    op.drop_table('unified_onboarding_sessions')
