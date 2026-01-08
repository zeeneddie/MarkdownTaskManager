"""Add MigrationAnalyzer tables

Week 65: MigrationAnalyzer Multi-Agent System
Creates 8 tables for legacy code and database migration analysis.

Tables:
- migration_analyses: Main analysis sessions
- migration_modules: Detected code modules
- migration_db_schemas: Database schema analysis
- legacy_patterns: Pattern detections
- db_compatibility_issues: Database conversion issues
- migration_recommendations: Generated recommendations
- fp_breakdowns: Function Point details
- risk_assessments: Risk register

Revision ID: 027
Revises: 026
Create Date: 2025-12-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '027_migration_analyzer'
down_revision = '026_rl_training'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. migration_analyses - Main analysis record
    op.create_table(
        'migration_analyses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('repo_path', sa.String(500), nullable=False),
        sa.Column('repo_name', sa.String(200)),

        # Detected stacks
        sa.Column('source_stack', sa.String(50)),  # Primary: aspnet_webforms, java, php
        sa.Column('secondary_stacks', JSONB, default=[]),  # ["jquery", "angularjs"]

        # Target
        sa.Column('target_stack', sa.String(50)),  # dotnet8, python, nodejs
        sa.Column('target_db', sa.String(50)),  # postgresql, mysql

        # Code Metrics
        sa.Column('total_files', sa.Integer(), default=0),
        sa.Column('total_loc', sa.Integer(), default=0),
        sa.Column('total_modules', sa.Integer(), default=0),
        sa.Column('estimated_fp', sa.Integer()),
        sa.Column('complexity_score', sa.Float()),
        sa.Column('risk_score', sa.Float()),

        # Database Metrics
        sa.Column('db_type', sa.String(50)),  # oracle, sqlserver, mysql
        sa.Column('db_version', sa.String(20)),
        sa.Column('db_table_count', sa.Integer()),
        sa.Column('db_sp_count', sa.Integer()),
        sa.Column('db_migration_difficulty', sa.String(1)),  # A-E
        sa.Column('db_estimated_days', sa.Float()),

        # JSON summary fields
        sa.Column('file_inventory', JSONB, default={}),
        sa.Column('module_inventory', JSONB, default={}),
        sa.Column('dependency_graph', JSONB, default={}),
        sa.Column('pattern_summary', JSONB, default={}),
        sa.Column('risk_summary', JSONB, default={}),

        # Status
        sa.Column('status', sa.String(20), default='pending'),  # pending, running, completed, failed
        sa.Column('current_phase', sa.String(50)),  # detection, stack_analysis, db_analysis, cross_cutting, output
        sa.Column('progress_percent', sa.Integer(), default=0),
        sa.Column('error_message', sa.Text()),

        # Timestamps
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('idx_migration_analyses_status', 'migration_analyses', ['status'])
    op.create_index('idx_migration_analyses_source_stack', 'migration_analyses', ['source_stack'])

    # 2. migration_modules - Individual modules within analysis
    op.create_table(
        'migration_modules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('analysis_id', UUID(as_uuid=True), sa.ForeignKey('migration_analyses.id', ondelete='CASCADE'), nullable=False),

        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('module_type', sa.String(50)),  # page, service, model, controller, component
        sa.Column('stack_type', sa.String(50)),  # aspnet_webforms, angularjs, vue
        sa.Column('file_path', sa.String(500)),
        sa.Column('file_count', sa.Integer(), default=1),
        sa.Column('loc', sa.Integer(), default=0),

        # Complexity (from Lizard)
        sa.Column('cyclomatic_complexity', sa.Float()),
        sa.Column('cognitive_complexity', sa.Float()),
        sa.Column('max_complexity', sa.Float()),
        sa.Column('avg_complexity', sa.Float()),
        sa.Column('function_count', sa.Integer()),

        # Migration assessment
        sa.Column('estimated_fp', sa.Integer()),
        sa.Column('migration_difficulty', sa.String(20)),  # easy, medium, hard, complex
        sa.Column('migration_target', sa.String(100)),  # "Blazor component", "Vue 3"
        sa.Column('migration_notes', sa.Text()),
        sa.Column('dependencies', JSONB, default=[]),

        # Patterns
        sa.Column('legacy_patterns', JSONB, default=[]),
        sa.Column('pattern_count', sa.Integer(), default=0),
        sa.Column('pattern_multiplier', sa.Float(), default=1.0),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_migration_modules_analysis', 'migration_modules', ['analysis_id'])
    op.create_index('idx_migration_modules_stack', 'migration_modules', ['stack_type'])

    # 3. migration_db_schemas - Database schema analysis
    op.create_table(
        'migration_db_schemas',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('analysis_id', UUID(as_uuid=True), sa.ForeignKey('migration_analyses.id', ondelete='CASCADE'), nullable=False),

        # Source database
        sa.Column('source_type', sa.String(50), nullable=False),  # oracle, sqlserver, mysql
        sa.Column('source_version', sa.String(20)),
        sa.Column('connection_string_hash', sa.String(64)),  # For tracking without exposing credentials

        # Schema inventory
        sa.Column('table_count', sa.Integer(), default=0),
        sa.Column('view_count', sa.Integer(), default=0),
        sa.Column('stored_procedure_count', sa.Integer(), default=0),
        sa.Column('function_count', sa.Integer(), default=0),
        sa.Column('trigger_count', sa.Integer(), default=0),
        sa.Column('index_count', sa.Integer(), default=0),
        sa.Column('sequence_count', sa.Integer(), default=0),
        sa.Column('constraint_count', sa.Integer(), default=0),

        # Schema details
        sa.Column('tables', JSONB, default=[]),  # [{name, columns, pk, fks, indexes}]
        sa.Column('views', JSONB, default=[]),
        sa.Column('stored_procedures', JSONB, default=[]),  # [{name, params, complexity}]
        sa.Column('functions', JSONB, default=[]),
        sa.Column('triggers', JSONB, default=[]),

        # Stored procedure complexity
        sa.Column('sp_avg_complexity', sa.Float()),
        sa.Column('sp_max_complexity', sa.Float()),
        sa.Column('sp_high_complexity_count', sa.Integer()),
        sa.Column('sp_total_loc', sa.Integer()),

        # Migration assessment (Ora2Pg scale)
        sa.Column('migration_difficulty', sa.String(1)),  # A-E
        sa.Column('estimated_man_days', sa.Float()),
        sa.Column('auto_convertible_percent', sa.Float()),

        # Tool outputs
        sa.Column('ora2pg_report', JSONB, default={}),
        sa.Column('sqlines_report', JSONB, default={}),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_migration_db_schemas_analysis', 'migration_db_schemas', ['analysis_id'])

    # 4. legacy_patterns - Pattern detections
    op.create_table(
        'legacy_patterns',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('analysis_id', UUID(as_uuid=True), sa.ForeignKey('migration_analyses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('module_id', UUID(as_uuid=True), sa.ForeignKey('migration_modules.id', ondelete='CASCADE'), nullable=True),

        sa.Column('pattern_name', sa.String(100), nullable=False),  # viewstate, scope_usage, mysql_functions
        sa.Column('pattern_category', sa.String(50)),  # aspnet_webforms, angularjs, php_legacy
        sa.Column('file_path', sa.String(500)),
        sa.Column('line_number', sa.Integer()),
        sa.Column('code_snippet', sa.Text()),  # Matched code

        # Assessment
        sa.Column('risk_level', sa.String(20)),  # low, medium, high, critical
        sa.Column('fp_multiplier', sa.Float(), default=1.0),
        sa.Column('migration_note', sa.Text()),
        sa.Column('migration_target', sa.String(200)),  # What to replace with

        # Security flag
        sa.Column('is_security_issue', sa.Boolean(), default=False),
        sa.Column('owasp_category', sa.String(10)),  # A01-A10

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_legacy_patterns_analysis', 'legacy_patterns', ['analysis_id'])
    op.create_index('idx_legacy_patterns_category', 'legacy_patterns', ['pattern_category'])
    op.create_index('idx_legacy_patterns_risk', 'legacy_patterns', ['risk_level'])

    # 5. db_compatibility_issues - Database conversion issues
    op.create_table(
        'db_compatibility_issues',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('schema_id', UUID(as_uuid=True), sa.ForeignKey('migration_db_schemas.id', ondelete='CASCADE'), nullable=False),

        sa.Column('issue_type', sa.String(50), nullable=False),  # datatype, feature, procedural, syntax
        sa.Column('source_feature', sa.String(200), nullable=False),  # NVARCHAR, IDENTITY, T-SQL
        sa.Column('target_equivalent', sa.String(200)),  # VARCHAR, SERIAL, PL/pgSQL

        sa.Column('object_type', sa.String(50)),  # table, view, sp, function, trigger
        sa.Column('object_name', sa.String(200)),
        sa.Column('location', sa.String(500)),  # File or schema location

        # Assessment
        sa.Column('auto_convertible', sa.Boolean(), default=True),
        sa.Column('conversion_effort', sa.String(20)),  # low, medium, high
        sa.Column('conversion_note', sa.Text()),

        # Occurrences
        sa.Column('occurrence_count', sa.Integer(), default=1),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_db_compat_issues_schema', 'db_compatibility_issues', ['schema_id'])
    op.create_index('idx_db_compat_issues_type', 'db_compatibility_issues', ['issue_type'])

    # 6. migration_recommendations - Generated recommendations
    op.create_table(
        'migration_recommendations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('analysis_id', UUID(as_uuid=True), sa.ForeignKey('migration_analyses.id', ondelete='CASCADE'), nullable=False),

        sa.Column('category', sa.String(50), nullable=False),  # architecture, database, security, performance, testing
        sa.Column('priority', sa.String(20)),  # critical, high, medium, low
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text()),

        # Source
        sa.Column('source_agent', sa.String(50)),  # miguel, quinn, eliza, felix, diana
        sa.Column('related_modules', JSONB, default=[]),  # Module IDs
        sa.Column('related_patterns', JSONB, default=[]),  # Pattern IDs

        # Action items
        sa.Column('action_items', JSONB, default=[]),  # [{step, effort, dependency}]
        sa.Column('estimated_effort', sa.String(20)),  # hours, days, weeks
        sa.Column('estimated_fp_impact', sa.Integer()),

        # Status
        sa.Column('status', sa.String(20), default='pending'),  # pending, accepted, rejected, implemented

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_migration_recs_analysis', 'migration_recommendations', ['analysis_id'])
    op.create_index('idx_migration_recs_category', 'migration_recommendations', ['category'])
    op.create_index('idx_migration_recs_priority', 'migration_recommendations', ['priority'])

    # 7. fp_breakdowns - Function Point details
    op.create_table(
        'fp_breakdowns',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('analysis_id', UUID(as_uuid=True), sa.ForeignKey('migration_analyses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('module_id', UUID(as_uuid=True), sa.ForeignKey('migration_modules.id', ondelete='CASCADE'), nullable=True),

        # IFPUG components
        sa.Column('fp_type', sa.String(20), nullable=False),  # EI, EO, EQ, ILF, EIF
        sa.Column('fp_name', sa.String(200)),
        sa.Column('complexity_rating', sa.String(10)),  # low, average, high
        sa.Column('unadjusted_fp', sa.Integer()),

        # Adjustments
        sa.Column('pattern_multiplier', sa.Float(), default=1.0),
        sa.Column('legacy_multiplier', sa.Float(), default=1.0),  # 1.2-2.0x for legacy
        sa.Column('db_migration_multiplier', sa.Float(), default=1.0),
        sa.Column('adjusted_fp', sa.Float()),

        # Source
        sa.Column('source_file', sa.String(500)),
        sa.Column('detected_by', sa.String(50)),  # eliza, lizard, manual

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_fp_breakdowns_analysis', 'fp_breakdowns', ['analysis_id'])
    op.create_index('idx_fp_breakdowns_type', 'fp_breakdowns', ['fp_type'])

    # 8. risk_assessments - Risk register
    op.create_table(
        'risk_assessments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('analysis_id', UUID(as_uuid=True), sa.ForeignKey('migration_analyses.id', ondelete='CASCADE'), nullable=False),

        sa.Column('risk_id', sa.String(20)),  # R001, R002, etc.
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('category', sa.String(50)),  # technical, security, performance, business, resource

        # Assessment (FMEA style)
        sa.Column('probability', sa.Integer()),  # 1-5
        sa.Column('impact', sa.Integer()),  # 1-5
        sa.Column('detectability', sa.Integer()),  # 1-5
        sa.Column('risk_score', sa.Integer()),  # probability * impact * detectability

        # Status
        sa.Column('status', sa.String(20), default='identified'),  # identified, mitigating, mitigated, accepted

        # Mitigation
        sa.Column('mitigation_strategy', sa.Text()),
        sa.Column('mitigation_owner', sa.String(100)),
        sa.Column('mitigation_deadline', sa.DateTime(timezone=True)),

        # Related items
        sa.Column('related_modules', JSONB, default=[]),
        sa.Column('related_patterns', JSONB, default=[]),

        # Source
        sa.Column('identified_by', sa.String(50)),  # quinn, felix, eliza, manual

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('idx_risk_assessments_analysis', 'risk_assessments', ['analysis_id'])
    op.create_index('idx_risk_assessments_score', 'risk_assessments', ['risk_score'])
    op.create_index('idx_risk_assessments_category', 'risk_assessments', ['category'])


def downgrade() -> None:
    op.drop_table('risk_assessments')
    op.drop_table('fp_breakdowns')
    op.drop_table('migration_recommendations')
    op.drop_table('db_compatibility_issues')
    op.drop_table('legacy_patterns')
    op.drop_table('migration_db_schemas')
    op.drop_table('migration_modules')
    op.drop_table('migration_analyses')
