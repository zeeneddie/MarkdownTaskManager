"""Add Week 131 research service tables

Revision ID: 061
Revises: 060
Create Date: 2025-12-31

Tables:
- background_jobs: Detected scheduled tasks and batch jobs
- load_estimations: Connection pool and capacity analysis
- documentation_rules: Business rules extracted from documentation

Part of Week 131: HCI-CRS Research Tasks
- Background jobs / scheduled tasks detection
- Load estimation (users/requests)
- Business rules from documentation extraction
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func


# revision identifiers
revision = '061'
down_revision = '060'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # background_jobs table - Detected scheduled tasks
    op.create_table(
        'background_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        sa.Column('job_id', sa.String(50), nullable=False),  # BGJ-001
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('job_type', sa.String(50), nullable=False),  # nightly, hourly, on_demand, cron
        sa.Column('schedule', sa.String(100), nullable=True),  # cron expression or description
        sa.Column('source_file', sa.String(500), nullable=False),
        sa.Column('source_line_start', sa.Integer, nullable=True),
        sa.Column('source_line_end', sa.Integer, nullable=True),
        sa.Column('entry_point', sa.String(200), nullable=True),  # Function/method name
        sa.Column('trigger_type', sa.String(50), nullable=True),  # timer, sql_agent, quartz, hangfire
        sa.Column('detection_method', sa.String(50), nullable=True),  # naming, config, code_pattern
        sa.Column('confidence', sa.Float, default=0.0),
        sa.Column('database_dependencies', JSONB, server_default='[]'),
        sa.Column('file_dependencies', JSONB, server_default='[]'),
        sa.Column('service_dependencies', JSONB, server_default='[]'),
        sa.Column('has_error_handling', sa.Boolean, default=False),
        sa.Column('error_handling_pattern', sa.String(100), nullable=True),
        sa.Column('has_logging', sa.Boolean, default=False),
        sa.Column('estimated_duration', sa.String(50), nullable=True),  # < 1 min, 1-10 min, > 10 min
        sa.Column('resource_intensity', sa.String(20), default='medium'),  # low, medium, high
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
    op.create_index('ix_background_jobs_project_id', 'background_jobs', ['project_id'])
    op.create_index('ix_background_jobs_job_type', 'background_jobs', ['job_type'])
    op.create_index('ix_background_jobs_trigger_type', 'background_jobs', ['trigger_type'])

    # load_estimations table - Capacity analysis results
    op.create_table(
        'load_estimations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),

        # Connection pool analysis
        sa.Column('connection_pools', JSONB, server_default='[]'),  # List of ConnectionPoolConfig
        sa.Column('total_sql_connections', sa.Integer, default=0),
        sa.Column('using_block_count', sa.Integer, default=0),  # SqlConnection Using blocks
        sa.Column('open_close_ratio', sa.Float, default=0.0),

        # Session state analysis
        sa.Column('session_config', JSONB, nullable=True),  # SessionStateConfig
        sa.Column('session_access_count', sa.Integer, default=0),
        sa.Column('session_variable_count', sa.Integer, default=0),

        # Query complexity analysis
        sa.Column('query_metrics', JSONB, nullable=True),  # QueryComplexityMetrics

        # Capacity estimation
        sa.Column('estimated_concurrent_users', sa.Integer, default=0),
        sa.Column('capacity_bottleneck', sa.String(100), nullable=True),
        sa.Column('bottleneck_details', sa.Text, nullable=True),
        sa.Column('recommendations', JSONB, server_default='[]'),

        # Metadata
        sa.Column('analysis_path', sa.String(500), nullable=True),
        sa.Column('files_analyzed', sa.Integer, default=0),
        sa.Column('duration_ms', sa.Integer, default=0),
        sa.Column('success', sa.Boolean, default=True),
        sa.Column('errors', JSONB, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
    )
    op.create_index('ix_load_estimations_project_id', 'load_estimations', ['project_id'])

    # documentation_rules table - Rules extracted from documentation
    op.create_table(
        'documentation_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        sa.Column('rule_id', sa.String(50), nullable=False),  # DOC-BR-001
        sa.Column('rule_type', sa.String(50), nullable=False),  # VALIDATION, AUTHORIZATION, etc.
        sa.Column('condition', sa.Text, nullable=True),  # IF part
        sa.Column('action', sa.Text, nullable=True),  # THEN part
        sa.Column('natural_language', sa.Text, nullable=True),  # Original text

        # Source tracking
        sa.Column('source_file', sa.String(500), nullable=False),
        sa.Column('source_section', sa.String(500), nullable=True),  # Heading path
        sa.Column('source_line', sa.Integer, nullable=True),

        # Extraction metadata
        sa.Column('extraction_pattern', sa.String(50), nullable=True),  # rule_prefix, numbered_list, table
        sa.Column('confidence', sa.Float, default=0.0),

        # Traceability
        sa.Column('related_code_rules', JSONB, server_default='[]'),  # Matched BR-xxx IDs
        sa.Column('conflicts', JSONB, server_default='[]'),  # Conflicting rules
        sa.Column('is_validated', sa.Boolean, default=False),
        sa.Column('validated_by', sa.String(100), nullable=True),
        sa.Column('validation_notes', sa.Text, nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
    op.create_index('ix_documentation_rules_project_id', 'documentation_rules', ['project_id'])
    op.create_index('ix_documentation_rules_rule_type', 'documentation_rules', ['rule_type'])
    op.create_index('ix_documentation_rules_confidence', 'documentation_rules', ['confidence'])


def downgrade() -> None:
    op.drop_index('ix_documentation_rules_confidence', table_name='documentation_rules')
    op.drop_index('ix_documentation_rules_rule_type', table_name='documentation_rules')
    op.drop_index('ix_documentation_rules_project_id', table_name='documentation_rules')
    op.drop_table('documentation_rules')

    op.drop_index('ix_load_estimations_project_id', table_name='load_estimations')
    op.drop_table('load_estimations')

    op.drop_index('ix_background_jobs_trigger_type', table_name='background_jobs')
    op.drop_index('ix_background_jobs_job_type', table_name='background_jobs')
    op.drop_index('ix_background_jobs_project_id', table_name='background_jobs')
    op.drop_table('background_jobs')
