"""Add stability analysis tables

Fase 21: ASP Application Stability Analyzer Framework
Week 143-146

Tables:
- stability_scans: Project-level scan records
- stability_findings: Individual leak findings
- stability_metrics: Trend tracking over time

Revision ID: 069
Revises: 068
Create Date: 2026-01-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '069'
down_revision = '068'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Stability Scans table
    op.create_table(
        'stability_scans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('scan_timestamp', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('total_files_scanned', sa.Integer(), default=0),
        sa.Column('total_files_with_issues', sa.Integer(), default=0),
        sa.Column('categories_analyzed', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('languages_analyzed', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('overall_risk', sa.String(20), default='LOW'),
        sa.Column('overall_score', sa.Integer(), default=100),
        sa.Column('analysis_time_seconds', sa.Float(), default=0.0),
        sa.Column('base_path', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_by', sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_stability_scans_project_id', 'stability_scans', ['project_id'])
    op.create_index('ix_stability_scans_scan_timestamp', 'stability_scans', ['scan_timestamp'])

    # Stability Findings table
    op.create_table(
        'stability_findings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scan_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),  # ado_leaks, com_objects, etc.
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),  # database_connection, recordset, etc.
        sa.Column('variable_name', sa.String(255), nullable=True),
        sa.Column('leak_pattern', sa.String(50), nullable=False),  # never_closed, loop_leak, etc.
        sa.Column('severity', sa.String(20), nullable=False),  # CRITICAL, HIGH, MEDIUM, LOW
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('suggested_fix', sa.Text(), nullable=True),
        sa.Column('code_context', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('confidence', sa.Float(), default=1.0),
        # Tracking fields
        sa.Column('status', sa.String(20), default='open'),  # open, acknowledged, fixed, wontfix
        sa.Column('fixed_at', sa.DateTime(), nullable=True),
        sa.Column('fixed_by', sa.String(50), nullable=True),
        sa.Column('fix_commit_hash', sa.String(40), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['scan_id'], ['stability_scans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['fixed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_stability_findings_scan_id', 'stability_findings', ['scan_id'])
    op.create_index('ix_stability_findings_category', 'stability_findings', ['category'])
    op.create_index('ix_stability_findings_severity', 'stability_findings', ['severity'])
    op.create_index('ix_stability_findings_status', 'stability_findings', ['status'])
    op.create_index('ix_stability_findings_file_path', 'stability_findings', ['file_path'])

    # Stability Metrics table (for trend tracking)
    op.create_table(
        'stability_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('metric_date', sa.Date(), nullable=False),
        # Category counts
        sa.Column('ado_leak_count', sa.Integer(), default=0),
        sa.Column('com_leak_count', sa.Integer(), default=0),
        sa.Column('external_service_issues', sa.Integer(), default=0),
        sa.Column('memory_issues', sa.Integer(), default=0),
        sa.Column('file_leak_count', sa.Integer(), default=0),
        sa.Column('session_issues', sa.Integer(), default=0),
        sa.Column('exception_issues', sa.Integer(), default=0),
        sa.Column('sql_issues', sa.Integer(), default=0),
        # Aggregates
        sa.Column('total_findings', sa.Integer(), default=0),
        sa.Column('critical_count', sa.Integer(), default=0),
        sa.Column('high_count', sa.Integer(), default=0),
        sa.Column('medium_count', sa.Integer(), default=0),
        sa.Column('low_count', sa.Integer(), default=0),
        sa.Column('overall_score', sa.Integer(), default=100),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'metric_date', name='uq_stability_metrics_project_date')
    )
    op.create_index('ix_stability_metrics_project_id', 'stability_metrics', ['project_id'])
    op.create_index('ix_stability_metrics_metric_date', 'stability_metrics', ['metric_date'])

    # Category findings summary table (aggregated per scan)
    op.create_table(
        'stability_category_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scan_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('issues_found', sa.Integer(), default=0),
        sa.Column('critical_count', sa.Integer(), default=0),
        sa.Column('high_count', sa.Integer(), default=0),
        sa.Column('medium_count', sa.Integer(), default=0),
        sa.Column('low_count', sa.Integer(), default=0),
        sa.Column('severity_score', sa.Integer(), default=0),
        sa.Column('files_affected', sa.Integer(), default=0),
        sa.ForeignKeyConstraint(['scan_id'], ['stability_scans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scan_id', 'category', name='uq_stability_category_scan')
    )
    op.create_index('ix_stability_category_summaries_scan_id', 'stability_category_summaries', ['scan_id'])


def downgrade() -> None:
    op.drop_table('stability_category_summaries')
    op.drop_table('stability_metrics')
    op.drop_table('stability_findings')
    op.drop_table('stability_scans')
