"""Add Project Assessment tables

Week 69: Gestandaardiseerde Project Workflows
Creates 3 tables for standardized project analysis and migration planning.

Tables:
- project_assessments: Workflow 1 output - complete project health analysis
- migration_plans: Workflow 2 output - migration planning (requires assessment)
- assessment_phases: Phase execution tracking for both workflows

Revision ID: 028
Revises: 027
Create Date: 2025-12-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '028_project_assessment'
down_revision = '027_migration_analyzer'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. project_assessments - Workflow 1 Output
    op.create_table(
        'project_assessments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('application_id', sa.Integer(), sa.ForeignKey('applications.id', ondelete='SET NULL'), nullable=True),

        # Project identification
        sa.Column('project_name', sa.String(255), nullable=False),
        sa.Column('directory_path', sa.String(1024), nullable=False),

        # Assessment metadata
        sa.Column('assessment_date', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('assessment_version', sa.Integer(), default=1),

        # === Phase 1: Registration (ApplicationRegistry) ===
        sa.Column('detected_stacks', JSONB, default=[]),
        sa.Column('primary_stack', sa.String(50)),
        sa.Column('file_count', sa.Integer(), default=0),
        sa.Column('line_count', sa.Integer(), default=0),
        sa.Column('component_count', sa.Integer(), default=0),

        # === Phase 2: AS-IS Architecture (Miguel) ===
        sa.Column('as_is_architecture', JSONB, default={}),
        sa.Column('architecture_pattern', sa.String(50)),
        sa.Column('architecture_layers', JSONB, default=[]),
        sa.Column('architecture_components', JSONB, default=[]),
        sa.Column('architecture_score', sa.Integer()),
        sa.Column('architecture_issues', JSONB, default=[]),

        # === Phase 3: Code Analysis (CodeRAG) ===
        sa.Column('code_analysis', JSONB, default={}),
        sa.Column('code_patterns', JSONB, default=[]),
        sa.Column('code_dependencies', JSONB, default=[]),
        sa.Column('code_complexity', JSONB, default={}),
        sa.Column('code_duplication_percent', sa.Float()),
        sa.Column('code_test_coverage_percent', sa.Float()),

        # === Phase 4: Security Analysis (Quinn) ===
        sa.Column('security_findings', JSONB, default=[]),
        sa.Column('security_finding_count', sa.Integer(), default=0),
        sa.Column('security_critical_count', sa.Integer(), default=0),
        sa.Column('security_high_count', sa.Integer(), default=0),
        sa.Column('security_medium_count', sa.Integer(), default=0),
        sa.Column('security_low_count', sa.Integer(), default=0),
        sa.Column('security_risk_score', sa.Integer()),
        sa.Column('security_grade', sa.String(1)),
        sa.Column('owasp_coverage', JSONB, default={}),

        # === Phase 5: Quality Analysis (Quinn) ===
        sa.Column('quality_report', JSONB, default={}),
        sa.Column('quality_issues', JSONB, default=[]),
        sa.Column('quality_issue_count', sa.Integer(), default=0),
        sa.Column('tech_debt_hours', sa.Float()),
        sa.Column('code_smell_count', sa.Integer(), default=0),
        sa.Column('maintainability_index', sa.Float()),
        sa.Column('quality_score', sa.Integer()),
        sa.Column('quality_grade', sa.String(1)),

        # === Overall Assessment ===
        sa.Column('overall_health_score', sa.Integer()),
        sa.Column('overall_grade', sa.String(1)),
        sa.Column('health_summary', sa.Text()),

        # Recommendations
        sa.Column('recommendations', JSONB, default=[]),
        sa.Column('blockers', JSONB, default=[]),

        # === Workflow Status ===
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('current_phase', sa.String(50)),
        sa.Column('progress_percent', sa.Integer(), default=0),
        sa.Column('error_message', sa.Text()),

        # Timestamps
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('idx_project_assessments_status', 'project_assessments', ['status'])
    op.create_index('idx_project_assessments_grade', 'project_assessments', ['overall_grade'])
    op.create_index('idx_project_assessments_project', 'project_assessments', ['project_name'])

    # 2. migration_plans - Workflow 2 Output
    op.create_table(
        'migration_plans',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('assessment_id', UUID(as_uuid=True), sa.ForeignKey('project_assessments.id', ondelete='CASCADE'), nullable=False),

        # Target configuration
        sa.Column('target_technology', sa.String(50), nullable=False),
        sa.Column('target_database', sa.String(50)),
        sa.Column('target_frontend', sa.String(50)),

        # === Phase 7: FP Estimation (Eliza) ===
        sa.Column('unadjusted_fp', sa.Integer()),
        sa.Column('adjusted_fp', sa.Integer()),
        sa.Column('vaf', sa.Numeric(4, 2)),
        sa.Column('gsc_factors', JSONB, default={}),
        sa.Column('total_hours', sa.Integer()),
        sa.Column('total_days', sa.Integer()),
        sa.Column('total_weeks', sa.Integer()),
        sa.Column('phase_breakdown', JSONB, default=[]),
        sa.Column('team_size_recommended', sa.Integer()),
        sa.Column('team_composition', JSONB, default={}),

        # === Phase 8: Target Architecture (Felix) ===
        sa.Column('target_architecture', JSONB, default={}),
        sa.Column('architecture_pattern', sa.String(50)),
        sa.Column('architecture_layers', JSONB, default=[]),
        sa.Column('component_mapping', JSONB, default=[]),
        sa.Column('api_contracts', JSONB, default=[]),
        sa.Column('data_migration_plan', JSONB, default=[]),
        sa.Column('architecture_decisions', JSONB, default=[]),

        # === Phase 9: Migration Strategy (Felix) ===
        sa.Column('migration_strategy', sa.String(50)),
        sa.Column('migration_phases', JSONB, default=[]),
        sa.Column('timeline_weeks', sa.Integer()),
        sa.Column('milestones', JSONB, default=[]),
        sa.Column('prerequisites', JSONB, default=[]),
        sa.Column('external_dependencies', JSONB, default=[]),

        # Risks and blockers
        sa.Column('risks', JSONB, default=[]),
        sa.Column('blockers', JSONB, default=[]),
        sa.Column('recommendations', JSONB, default=[]),
        sa.Column('success_criteria', JSONB, default=[]),

        # Diana Report
        sa.Column('report_type', sa.String(50), default='full_migration_plan'),
        sa.Column('report_content', sa.Text()),
        sa.Column('report_metadata', JSONB, default={}),

        # Workflow Status
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('current_phase', sa.String(50)),
        sa.Column('progress_percent', sa.Integer(), default=0),
        sa.Column('error_message', sa.Text()),

        # Review
        sa.Column('reviewed_by', sa.String(100)),
        sa.Column('reviewed_at', sa.DateTime(timezone=True)),
        sa.Column('review_notes', sa.Text()),

        # Timestamps
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('idx_migration_plans_assessment', 'migration_plans', ['assessment_id'])
    op.create_index('idx_migration_plans_status', 'migration_plans', ['status'])
    op.create_index('idx_migration_plans_strategy', 'migration_plans', ['migration_strategy'])

    # 3. assessment_phases - Phase tracking for both workflows
    op.create_table(
        'assessment_phases',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('assessment_id', UUID(as_uuid=True), sa.ForeignKey('project_assessments.id', ondelete='CASCADE'), nullable=True),
        sa.Column('migration_plan_id', UUID(as_uuid=True), sa.ForeignKey('migration_plans.id', ondelete='CASCADE'), nullable=True),

        # Phase identification
        sa.Column('workflow', sa.String(20), nullable=False),
        sa.Column('phase_number', sa.Integer(), nullable=False),
        sa.Column('phase_name', sa.String(50), nullable=False),

        # Execution
        sa.Column('agent_name', sa.String(50)),
        sa.Column('status', sa.String(20), default='pending'),

        # Timing
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('duration_seconds', sa.Integer()),

        # Results
        sa.Column('result_summary', sa.Text()),
        sa.Column('result_data', JSONB, default={}),
        sa.Column('error_message', sa.Text()),

        # Metrics
        sa.Column('items_processed', sa.Integer()),
        sa.Column('items_found', sa.Integer()),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_assessment_phases_assessment', 'assessment_phases', ['assessment_id'])
    op.create_index('idx_assessment_phases_migration', 'assessment_phases', ['migration_plan_id'])
    op.create_index('idx_assessment_phases_workflow', 'assessment_phases', ['workflow'])
    op.create_index('idx_assessment_phases_status', 'assessment_phases', ['status'])


def downgrade() -> None:
    op.drop_table('assessment_phases')
    op.drop_table('migration_plans')
    op.drop_table('project_assessments')
