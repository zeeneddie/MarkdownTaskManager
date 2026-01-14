"""Add workflow separation tables (analysis_contracts, quality_schedules)

Revision ID: 070
Revises: 069
Create Date: 2026-01-13

Fase 21.5: Workflow Separation
- analysis_contracts: Bridge between Brown Paper and Migration
- quality_schedules: Independent quality scan scheduling
- quality_scan_results: Quality scan audit trail
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '070'
down_revision = '069'
branch_labels = None
depends_on = None


def upgrade():
    # === Analysis Contracts Table ===
    # The bridge between Brown Paper and Migration
    op.create_table(
        'analysis_contracts',
        sa.Column('analysis_id', sa.String(36), primary_key=True),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_id', sa.String(255), nullable=True),
        sa.Column('project_id', sa.String(255), nullable=True),
        sa.Column('contract_data', postgresql.JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Indexes for analysis_contracts
    op.create_index('ix_analysis_contracts_source_type', 'analysis_contracts', ['source_type'])
    op.create_index('ix_analysis_contracts_source_id', 'analysis_contracts', ['source_id'])
    op.create_index('ix_analysis_contracts_project_id', 'analysis_contracts', ['project_id'])
    op.create_index('ix_analysis_contracts_source', 'analysis_contracts', ['source_type', 'source_id'])

    # === Quality Schedules Table ===
    # Independent quality scan scheduling
    op.create_table(
        'quality_schedules',
        sa.Column('schedule_id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(255), nullable=False),
        sa.Column('schedule_type', sa.String(20), nullable=False),
        sa.Column('schedule_config', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('focus_areas', postgresql.JSONB, server_default='[]'),
        sa.Column('enabled', sa.Boolean, server_default='true'),
        sa.Column('next_run_at', sa.DateTime, nullable=True),
        sa.Column('last_run_at', sa.DateTime, nullable=True),
        sa.Column('last_scan_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Indexes for quality_schedules
    op.create_index('ix_quality_schedules_project_id', 'quality_schedules', ['project_id'])
    op.create_index('ix_quality_schedules_next_run', 'quality_schedules', ['enabled', 'next_run_at'])

    # === Quality Scan Results Table ===
    # Audit trail for quality scans
    op.create_table(
        'quality_scan_results',
        sa.Column('scan_id', sa.String(36), primary_key=True),
        sa.Column('schedule_id', sa.String(36), nullable=True),
        sa.Column('project_id', sa.String(255), nullable=False),
        sa.Column('project_path', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('overall_score', sa.Integer, nullable=True),
        sa.Column('result_data', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('triggered_by', sa.String(50), server_default='\'manual\''),
        sa.Column('scan_duration_seconds', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Indexes for quality_scan_results
    op.create_index('ix_quality_scan_results_project_id', 'quality_scan_results', ['project_id'])
    op.create_index('ix_quality_scan_results_status', 'quality_scan_results', ['status'])

    # Foreign key for quality_scan_results -> quality_schedules
    op.create_foreign_key(
        'fk_quality_scan_results_schedule_id',
        'quality_scan_results', 'quality_schedules',
        ['schedule_id'], ['schedule_id'],
        ondelete='SET NULL'
    )


def downgrade():
    # Drop foreign key first
    op.drop_constraint('fk_quality_scan_results_schedule_id', 'quality_scan_results', type_='foreignkey')

    # Drop indexes
    op.drop_index('ix_quality_scan_results_status', table_name='quality_scan_results')
    op.drop_index('ix_quality_scan_results_project_id', table_name='quality_scan_results')
    op.drop_index('ix_quality_schedules_next_run', table_name='quality_schedules')
    op.drop_index('ix_quality_schedules_project_id', table_name='quality_schedules')
    op.drop_index('ix_analysis_contracts_source', table_name='analysis_contracts')
    op.drop_index('ix_analysis_contracts_project_id', table_name='analysis_contracts')
    op.drop_index('ix_analysis_contracts_source_id', table_name='analysis_contracts')
    op.drop_index('ix_analysis_contracts_source_type', table_name='analysis_contracts')

    # Drop tables in reverse order
    op.drop_table('quality_scan_results')
    op.drop_table('quality_schedules')
    op.drop_table('analysis_contracts')
