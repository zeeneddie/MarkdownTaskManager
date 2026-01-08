"""Week 77: Add Layered Analysis Service tables

Revision ID: 032_layered_analysis
Revises: 031_claude_mem
Create Date: 2025-12-16

Tables:
- layered_analysis_sessions: Main analysis session tracking
- vbscript_analysis: Classic ASP/VBScript specific analysis
- stored_procedure_analysis: Database stored procedure analysis
- swot_analysis: SWOT matrix results
- improvement_items: Prioritized improvement backlog
- analysis_reports: Generated reports at different levels
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '032_layered_analysis'
down_revision = '031_claude_mem'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Layered Analysis Sessions - main orchestration table
    op.create_table(
        'layered_analysis_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        sa.Column('application_id', sa.Integer, sa.ForeignKey('applications.id', ondelete='CASCADE'), nullable=True),
        sa.Column('assessment_id', UUID(as_uuid=True), sa.ForeignKey('project_assessments.id', ondelete='SET NULL'), nullable=True),

        # Session metadata
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('source_path', sa.Text),  # Path to source code
        sa.Column('analysis_depth', sa.String(20), default='standard'),  # quick, standard, deep

        # Coverage metrics
        sa.Column('total_files', sa.Integer, default=0),
        sa.Column('analyzed_files', sa.Integer, default=0),
        sa.Column('total_lines', sa.Integer, default=0),
        sa.Column('analyzed_lines', sa.Integer, default=0),
        sa.Column('coverage_percentage', sa.Numeric(5, 2), default=0),  # Target: 100.00

        # Detected technologies
        sa.Column('detected_stack', JSONB, default=dict),  # {"frontend": [...], "backend": [...], "database": [...]}
        sa.Column('has_vbscript', sa.Boolean, default=False),
        sa.Column('has_stored_procedures', sa.Boolean, default=False),

        # Status
        sa.Column('status', sa.String(30), default='pending'),  # pending, analyzing, completed, failed
        sa.Column('current_phase', sa.String(50)),  # inventory, code_analysis, sp_analysis, swot, improvement
        sa.Column('error_message', sa.Text),

        # Timing
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # VBScript Analysis - Classic ASP/VBScript specific
    op.create_table(
        'vbscript_analysis',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('layered_analysis_sessions.id', ondelete='CASCADE'), nullable=False),

        # File inventory
        sa.Column('asp_files', sa.Integer, default=0),
        sa.Column('vbs_files', sa.Integer, default=0),
        sa.Column('inc_files', sa.Integer, default=0),
        sa.Column('total_lines', sa.Integer, default=0),

        # Extraction results
        sa.Column('functions_count', sa.Integer, default=0),
        sa.Column('subs_count', sa.Integer, default=0),
        sa.Column('includes_count', sa.Integer, default=0),
        sa.Column('com_objects_count', sa.Integer, default=0),
        sa.Column('sql_patterns_count', sa.Integer, default=0),

        # Detailed extractions
        sa.Column('functions', JSONB, default=list),  # [{name, params, file, line}]
        sa.Column('subs', JSONB, default=list),
        sa.Column('includes', JSONB, default=list),  # [{type, path, resolved_path, file, line}]
        sa.Column('com_objects', JSONB, default=list),  # [{progid, variable, file, line}]
        sa.Column('sql_patterns', JSONB, default=list),  # [{query_type, pattern, file, line, risk_level}]

        # Dependency graphs
        sa.Column('include_graph', JSONB, default=dict),  # {file: [included_files]}
        sa.Column('com_dependency_graph', JSONB, default=dict),  # {com_object: [usage_locations]}
        sa.Column('data_flow_graph', JSONB, default=dict),  # Request → Processing → Response

        # Security findings
        sa.Column('sql_injection_risks', JSONB, default=list),
        sa.Column('xss_risks', JSONB, default=list),
        sa.Column('session_issues', JSONB, default=list),
        sa.Column('error_handling_issues', JSONB, default=list),

        # Metrics
        sa.Column('complexity_score', sa.Integer),  # 0-100
        sa.Column('maintainability_score', sa.Integer),  # 0-100
        sa.Column('security_score', sa.Integer),  # 0-100

        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Stored Procedure Analysis - Database SP/Function analysis
    op.create_table(
        'stored_procedure_analysis',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('layered_analysis_sessions.id', ondelete='CASCADE'), nullable=False),

        # Database info
        sa.Column('database_type', sa.String(50)),  # sql_server, oracle, postgresql, mysql
        sa.Column('database_name', sa.String(255)),
        sa.Column('schema_name', sa.String(255)),

        # Inventory counts
        sa.Column('stored_procedures_count', sa.Integer, default=0),
        sa.Column('functions_count', sa.Integer, default=0),
        sa.Column('triggers_count', sa.Integer, default=0),
        sa.Column('views_count', sa.Integer, default=0),
        sa.Column('total_lines', sa.Integer, default=0),

        # Detailed inventory
        sa.Column('stored_procedures', JSONB, default=list),  # [{name, schema, params, returns, lines, complexity}]
        sa.Column('functions', JSONB, default=list),
        sa.Column('triggers', JSONB, default=list),  # [{name, table, event, timing}]
        sa.Column('views', JSONB, default=list),  # [{name, definition, dependencies}]

        # Dependency analysis
        sa.Column('sp_dependencies', JSONB, default=dict),  # {sp_name: [called_sps, tables_used]}
        sa.Column('table_usage', JSONB, default=dict),  # {table_name: {select: [], insert: [], update: [], delete: []}}
        sa.Column('cross_database_calls', JSONB, default=list),  # [{from_db, to_db, object}]

        # Business logic extraction
        sa.Column('business_rules', JSONB, default=list),  # [{sp_name, rule_description, confidence}]
        sa.Column('data_transformations', JSONB, default=list),  # [{sp_name, input, output, transformation}]
        sa.Column('validation_logic', JSONB, default=list),  # [{sp_name, field, validation_type}]

        # Complexity metrics
        sa.Column('complexity_distribution', JSONB, default=dict),  # {low: n, medium: n, high: n, critical: n}
        sa.Column('most_complex_sps', JSONB, default=list),  # Top 10 by cyclomatic complexity
        sa.Column('most_called_sps', JSONB, default=list),  # Top 10 by reference count

        # Migration indicators
        sa.Column('vendor_specific_features', JSONB, default=list),  # [{feature, sp_name, line}]
        sa.Column('deprecated_syntax', JSONB, default=list),
        sa.Column('performance_concerns', JSONB, default=list),  # [{sp_name, concern, recommendation}]

        # Scores
        sa.Column('overall_complexity_score', sa.Integer),  # 0-100
        sa.Column('migration_difficulty_score', sa.Integer),  # 0-100
        sa.Column('business_logic_coverage', sa.Integer),  # 0-100 (how much logic is in SPs vs app)

        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # SWOT Analysis - Strength/Weakness/Opportunity/Threat
    op.create_table(
        'swot_analysis',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('layered_analysis_sessions.id', ondelete='CASCADE'), nullable=False),

        # SWOT Matrix
        sa.Column('strengths', JSONB, default=list),  # [{category, title, description, evidence, impact}]
        sa.Column('weaknesses', JSONB, default=list),
        sa.Column('opportunities', JSONB, default=list),
        sa.Column('threats', JSONB, default=list),

        # Categorized findings
        sa.Column('architecture_findings', JSONB, default=dict),  # {strengths: [], weaknesses: []}
        sa.Column('code_quality_findings', JSONB, default=dict),
        sa.Column('security_findings', JSONB, default=dict),
        sa.Column('performance_findings', JSONB, default=dict),
        sa.Column('maintainability_findings', JSONB, default=dict),
        sa.Column('database_findings', JSONB, default=dict),  # SP and data layer specific

        # Prioritization
        sa.Column('prioritized_weaknesses', JSONB, default=list),  # [{weakness, priority, effort, impact, dependencies}]
        sa.Column('quick_wins', JSONB, default=list),  # Low effort, high impact
        sa.Column('strategic_items', JSONB, default=list),  # High effort, high impact

        # Summary scores
        sa.Column('overall_health_score', sa.Integer),  # 0-100
        sa.Column('technical_debt_score', sa.Integer),  # 0-100 (higher = more debt)
        sa.Column('modernization_readiness', sa.Integer),  # 0-100

        # Recommendations
        sa.Column('top_recommendations', JSONB, default=list),  # Top 5 prioritized recommendations
        sa.Column('risk_assessment', JSONB, default=dict),  # {level: "high/medium/low", factors: []}

        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Improvement Items - Prioritized backlog
    op.create_table(
        'improvement_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('layered_analysis_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('swot_id', UUID(as_uuid=True), sa.ForeignKey('swot_analysis.id', ondelete='CASCADE'), nullable=True),

        # Item details
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('category', sa.String(50)),  # architecture, security, performance, maintainability, database
        sa.Column('item_type', sa.String(30)),  # quick_win, strategic, technical_debt, security_fix

        # Source
        sa.Column('source_weakness', sa.String(255)),  # Which SWOT weakness this addresses
        sa.Column('affected_files', JSONB, default=list),
        sa.Column('affected_sps', JSONB, default=list),  # Affected stored procedures

        # Prioritization
        sa.Column('priority', sa.Integer),  # 1-5 (1 = highest)
        sa.Column('business_impact', sa.String(20)),  # critical, high, medium, low
        sa.Column('effort_days', sa.Numeric(5, 1)),  # Estimated effort
        sa.Column('risk_if_not_done', sa.String(20)),  # critical, high, medium, low

        # Dependencies
        sa.Column('depends_on', JSONB, default=list),  # [improvement_item_ids]
        sa.Column('blocks', JSONB, default=list),  # [improvement_item_ids]

        # Implementation hints
        sa.Column('implementation_notes', sa.Text),
        sa.Column('code_examples', JSONB, default=list),
        sa.Column('references', JSONB, default=list),  # Links to best practices, docs

        # Tracking
        sa.Column('status', sa.String(20), default='identified'),  # identified, planned, in_progress, completed, deferred
        sa.Column('assigned_to', sa.String(100)),

        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Analysis Reports - Generated reports at different levels
    op.create_table(
        'analysis_reports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('layered_analysis_sessions.id', ondelete='CASCADE'), nullable=False),

        # Report type
        sa.Column('report_level', sa.String(20), nullable=False),  # executive, management, technical
        sa.Column('report_format', sa.String(20), default='markdown'),  # markdown, html, pdf, json

        # Content
        sa.Column('title', sa.String(255)),
        sa.Column('content', sa.Text),  # Full report content
        sa.Column('sections', JSONB, default=list),  # [{title, content, order}]

        # Metrics included
        sa.Column('key_metrics', JSONB, default=dict),  # {metric_name: value}
        sa.Column('charts_data', JSONB, default=dict),  # Data for visualizations

        # Generation info
        sa.Column('generated_by', sa.String(50)),  # agent name or "system"
        sa.Column('generation_time_ms', sa.Integer),

        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Indexes for performance
    op.create_index('ix_layered_analysis_sessions_project', 'layered_analysis_sessions', ['project_id'])
    op.create_index('ix_layered_analysis_sessions_status', 'layered_analysis_sessions', ['status'])
    op.create_index('ix_vbscript_analysis_session', 'vbscript_analysis', ['session_id'])
    op.create_index('ix_stored_procedure_analysis_session', 'stored_procedure_analysis', ['session_id'])
    op.create_index('ix_swot_analysis_session', 'swot_analysis', ['session_id'])
    op.create_index('ix_improvement_items_session', 'improvement_items', ['session_id'])
    op.create_index('ix_improvement_items_priority', 'improvement_items', ['priority'])
    op.create_index('ix_improvement_items_category', 'improvement_items', ['category'])
    op.create_index('ix_analysis_reports_session', 'analysis_reports', ['session_id'])
    op.create_index('ix_analysis_reports_level', 'analysis_reports', ['report_level'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_analysis_reports_level')
    op.drop_index('ix_analysis_reports_session')
    op.drop_index('ix_improvement_items_category')
    op.drop_index('ix_improvement_items_priority')
    op.drop_index('ix_improvement_items_session')
    op.drop_index('ix_swot_analysis_session')
    op.drop_index('ix_stored_procedure_analysis_session')
    op.drop_index('ix_vbscript_analysis_session')
    op.drop_index('ix_layered_analysis_sessions_status')
    op.drop_index('ix_layered_analysis_sessions_project')

    # Drop tables
    op.drop_table('analysis_reports')
    op.drop_table('improvement_items')
    op.drop_table('swot_analysis')
    op.drop_table('stored_procedure_analysis')
    op.drop_table('vbscript_analysis')
    op.drop_table('layered_analysis_sessions')
