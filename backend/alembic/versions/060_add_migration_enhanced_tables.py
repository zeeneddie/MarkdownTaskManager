"""Add migration enhanced tables

Revision ID: 060
Revises: 059
Create Date: 2025-12-31

Week 130 - Fase 21: Migration Enhanced (7-Phase Execution Workflow)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '060'
down_revision = '059_dual_stack'
branch_labels = None
depends_on = None


def upgrade():
    # Migration Enhanced Sessions - Main workflow tracking table
    op.create_table(
        'migration_enhanced_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('brown_paper_session_id', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), default='not_started'),

        # Configuration
        sa.Column('target_technology', sa.String(50), default='dotnet8'),
        sa.Column('target_database', sa.String(50), default='postgresql'),
        sa.Column('migration_strategy', sa.String(50), default='strangler_fig'),
        sa.Column('deployment_strategy', sa.String(50), default='blue_green'),
        sa.Column('team_size', sa.Integer, default=3),
        sa.Column('parallel_execution', sa.Boolean, default=True),
        sa.Column('test_strategy', sa.String(50), default='auto'),
        sa.Column('test_coverage_target', sa.Numeric(4, 2), default=0.80),
        sa.Column('performance_tolerance', sa.Numeric(4, 2), default=1.10),

        # Phase 1: Preparation
        sa.Column('phase_1_status', sa.String(20), default='pending'),
        sa.Column('phase_1_started_at', sa.DateTime),
        sa.Column('phase_1_completed_at', sa.DateTime),
        sa.Column('phase_1_result', JSONB, default={}),

        # Phase 2: Code Transformation
        sa.Column('phase_2_status', sa.String(20), default='pending'),
        sa.Column('phase_2_started_at', sa.DateTime),
        sa.Column('phase_2_completed_at', sa.DateTime),
        sa.Column('phase_2_result', JSONB, default={}),

        # Phase 3: Data Migration
        sa.Column('phase_3_status', sa.String(20), default='pending'),
        sa.Column('phase_3_started_at', sa.DateTime),
        sa.Column('phase_3_completed_at', sa.DateTime),
        sa.Column('phase_3_result', JSONB, default={}),

        # Phase 4: Testing
        sa.Column('phase_4_status', sa.String(20), default='pending'),
        sa.Column('phase_4_started_at', sa.DateTime),
        sa.Column('phase_4_completed_at', sa.DateTime),
        sa.Column('phase_4_result', JSONB, default={}),
        sa.Column('phase_4_tests_passing', sa.Boolean, default=False),
        sa.Column('phase_4_coverage', sa.Numeric(5, 2), default=0.0),

        # Phase 5: Validation
        sa.Column('phase_5_status', sa.String(20), default='pending'),
        sa.Column('phase_5_started_at', sa.DateTime),
        sa.Column('phase_5_completed_at', sa.DateTime),
        sa.Column('phase_5_result', JSONB, default={}),
        sa.Column('functional_equivalence', sa.Boolean),
        sa.Column('data_integrity', sa.Boolean),
        sa.Column('performance_baseline', sa.Boolean),
        sa.Column('security_audit', sa.Boolean),

        # Phase 6: Acceptance
        sa.Column('phase_6_status', sa.String(20), default='pending'),
        sa.Column('phase_6_started_at', sa.DateTime),
        sa.Column('phase_6_completed_at', sa.DateTime),
        sa.Column('phase_6_result', JSONB, default={}),
        sa.Column('go_decision', sa.Boolean),
        sa.Column('stakeholder_signoffs', JSONB, default={}),

        # Phase 7: Deployment
        sa.Column('phase_7_status', sa.String(20), default='pending'),
        sa.Column('phase_7_started_at', sa.DateTime),
        sa.Column('phase_7_completed_at', sa.DateTime),
        sa.Column('phase_7_result', JSONB, default={}),
        sa.Column('staging_deployed_at', sa.DateTime),
        sa.Column('production_deployed_at', sa.DateTime),
        sa.Column('rollback_available', sa.Boolean, default=False),

        # Timing
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('total_duration_ms', sa.BigInteger, default=0),

        # Metadata
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('errors', JSONB, default=[]),
    )

    # Index for looking up by brown paper session
    op.create_index(
        'ix_migration_enhanced_brown_paper_session',
        'migration_enhanced_sessions',
        ['brown_paper_session_id']
    )

    # Index for status filtering
    op.create_index(
        'ix_migration_enhanced_status',
        'migration_enhanced_sessions',
        ['status']
    )

    # Migration Phase Events - Audit log of phase transitions
    op.create_table(
        'migration_phase_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('migration_enhanced_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('phase', sa.Integer, nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),  # started, completed, failed, skipped
        sa.Column('agent', sa.String(50)),
        sa.Column('details', JSONB, default={}),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Index for session event lookup
    op.create_index(
        'ix_migration_phase_events_session',
        'migration_phase_events',
        ['session_id', 'phase']
    )

    # Migration Acceptance Checklist - For Phase 6 tracking
    op.create_table(
        'migration_acceptance_checklist',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('migration_enhanced_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('item_id', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('category', sa.String(50), nullable=False),  # business_rule, user_story, stakeholder
        sa.Column('status', sa.String(20), default='pending'),  # pending, accepted, rejected
        sa.Column('verified_by', sa.String(100)),
        sa.Column('verified_at', sa.DateTime),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Index for checklist lookup
    op.create_index(
        'ix_migration_acceptance_checklist_session',
        'migration_acceptance_checklist',
        ['session_id', 'category']
    )


def downgrade():
    op.drop_index('ix_migration_acceptance_checklist_session')
    op.drop_table('migration_acceptance_checklist')
    op.drop_index('ix_migration_phase_events_session')
    op.drop_table('migration_phase_events')
    op.drop_index('ix_migration_enhanced_status')
    op.drop_index('ix_migration_enhanced_brown_paper_session')
    op.drop_table('migration_enhanced_sessions')
