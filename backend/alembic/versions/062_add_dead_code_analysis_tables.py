"""Add dead code analysis tables for Week 132-133

Revision ID: 062
Revises: 061
Create Date: 2025-12-31

Tables:
- dead_code_analyses: Main analysis results
- dead_code_items: Individual dead code findings
- runtime_analyses: APM/runtime analysis results
- code_coverage_analyses: Coverage analysis results
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '062'
down_revision = '061'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Dead Code Analyses - main analysis sessions
    op.create_table(
        'dead_code_analyses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.String(255), nullable=False, index=True),
        sa.Column('project_path', sa.String(1024), nullable=False),
        sa.Column('analysis_type', sa.String(50), nullable=False),  # static, runtime, combined
        sa.Column('languages_detected', JSONB, nullable=True),  # ["typescript", "python", ...]
        sa.Column('total_files_scanned', sa.Integer, default=0),
        sa.Column('total_lines_scanned', sa.Integer, default=0),
        sa.Column('dead_code_count', sa.Integer, default=0),
        sa.Column('dead_lines_count', sa.Integer, default=0),
        sa.Column('dead_code_percentage', sa.Float, default=0.0),
        sa.Column('safe_removal_count', sa.Integer, default=0),
        sa.Column('risky_removal_count', sa.Integer, default=0),
        sa.Column('estimated_cleanup_hours', sa.Float, default=0.0),
        sa.Column('tools_used', JSONB, nullable=True),  # ["ts-prune", "vulture", ...]
        sa.Column('configuration', JSONB, nullable=True),
        sa.Column('summary', JSONB, nullable=True),
        sa.Column('recommendations', JSONB, nullable=True),
        sa.Column('duration_ms', sa.Integer, default=0),
        sa.Column('success', sa.Boolean, default=True),
        sa.Column('errors', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Dead Code Items - individual findings
    op.create_table(
        'dead_code_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('analysis_id', UUID(as_uuid=True), sa.ForeignKey('dead_code_analyses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('item_type', sa.String(50), nullable=False),  # function, class, variable, import, file, branch
        sa.Column('name', sa.String(512), nullable=False),
        sa.Column('file_path', sa.String(1024), nullable=False),
        sa.Column('line_start', sa.Integer, nullable=True),
        sa.Column('line_end', sa.Integer, nullable=True),
        sa.Column('lines_count', sa.Integer, default=1),
        sa.Column('language', sa.String(50), nullable=True),
        sa.Column('detection_method', sa.String(50), nullable=False),  # static, runtime, both
        sa.Column('detection_tool', sa.String(100), nullable=True),  # ts-prune, vulture, roslyn
        sa.Column('confidence', sa.Float, default=0.7),
        sa.Column('removal_risk', sa.String(20), nullable=False),  # safe, low, medium, high, critical
        sa.Column('reason', sa.Text, nullable=True),
        sa.Column('references', JSONB, nullable=True),  # Files that might reference this
        sa.Column('last_modified', sa.DateTime, nullable=True),
        sa.Column('last_accessed', sa.DateTime, nullable=True),  # From runtime analysis
        sa.Column('call_count', sa.Integer, nullable=True),  # From runtime analysis
        sa.Column('suggested_action', sa.String(50), nullable=True),  # remove, review, keep, refactor
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_dead_code_items_file_path', 'dead_code_items', ['file_path'])
    op.create_index('ix_dead_code_items_item_type', 'dead_code_items', ['item_type'])
    op.create_index('ix_dead_code_items_removal_risk', 'dead_code_items', ['removal_risk'])

    # Runtime Analyses - APM integration results
    op.create_table(
        'runtime_analyses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.String(255), nullable=False, index=True),
        sa.Column('project_path', sa.String(1024), nullable=False),
        sa.Column('apm_provider', sa.String(100), nullable=True),  # new_relic, datadog, jaeger, custom
        sa.Column('analysis_period_start', sa.DateTime, nullable=True),
        sa.Column('analysis_period_end', sa.DateTime, nullable=True),
        sa.Column('total_endpoints', sa.Integer, default=0),
        sa.Column('active_endpoints', sa.Integer, default=0),
        sa.Column('inactive_endpoints', sa.Integer, default=0),
        sa.Column('total_functions', sa.Integer, default=0),
        sa.Column('called_functions', sa.Integer, default=0),
        sa.Column('uncalled_functions', sa.Integer, default=0),
        sa.Column('hot_paths', JSONB, nullable=True),  # Most frequently executed paths
        sa.Column('cold_paths', JSONB, nullable=True),  # Never/rarely executed paths
        sa.Column('execution_traces', JSONB, nullable=True),
        sa.Column('performance_metrics', JSONB, nullable=True),
        sa.Column('coverage_percentage', sa.Float, default=0.0),
        sa.Column('duration_ms', sa.Integer, default=0),
        sa.Column('success', sa.Boolean, default=True),
        sa.Column('errors', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Code Coverage Analyses - coverage mapping
    op.create_table(
        'code_coverage_analyses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.String(255), nullable=False, index=True),
        sa.Column('project_path', sa.String(1024), nullable=False),
        sa.Column('coverage_source', sa.String(100), nullable=False),  # jest, pytest, dotcover, runtime
        sa.Column('total_lines', sa.Integer, default=0),
        sa.Column('covered_lines', sa.Integer, default=0),
        sa.Column('uncovered_lines', sa.Integer, default=0),
        sa.Column('line_coverage_percentage', sa.Float, default=0.0),
        sa.Column('total_branches', sa.Integer, default=0),
        sa.Column('covered_branches', sa.Integer, default=0),
        sa.Column('branch_coverage_percentage', sa.Float, default=0.0),
        sa.Column('total_functions', sa.Integer, default=0),
        sa.Column('covered_functions', sa.Integer, default=0),
        sa.Column('function_coverage_percentage', sa.Float, default=0.0),
        sa.Column('file_coverage', JSONB, nullable=True),  # Per-file coverage stats
        sa.Column('uncovered_files', JSONB, nullable=True),  # Files with 0% coverage
        sa.Column('critical_uncovered', JSONB, nullable=True),  # Important uncovered code
        sa.Column('coverage_trends', JSONB, nullable=True),  # Historical trends
        sa.Column('test_suites', JSONB, nullable=True),
        sa.Column('duration_ms', sa.Integer, default=0),
        sa.Column('success', sa.Boolean, default=True),
        sa.Column('errors', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('code_coverage_analyses')
    op.drop_table('runtime_analyses')
    op.drop_index('ix_dead_code_items_removal_risk', table_name='dead_code_items')
    op.drop_index('ix_dead_code_items_item_type', table_name='dead_code_items')
    op.drop_index('ix_dead_code_items_file_path', table_name='dead_code_items')
    op.drop_table('dead_code_items')
    op.drop_table('dead_code_analyses')
