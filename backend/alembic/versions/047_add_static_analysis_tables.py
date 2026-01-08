"""Add static analysis tables for Fase 15

Revision ID: 047_static_analysis
Revises: 046_add_design_os_tables
Create Date: 2025-12-23

Fase 15: Hybrid Static-LLM Extraction Pipeline
Week 97-98: Static Analysis Foundation
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = '047_static_analysis'
down_revision = '046'
branch_labels = None
depends_on = None


def upgrade():
    # Static Analysis Results table
    op.create_table(
        'static_analysis_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='completed'),
        sa.Column('total_files_analyzed', sa.Integer, nullable=False, default=0),
        sa.Column('total_lines_of_code', sa.Integer, nullable=False, default=0),
        sa.Column('domain_coverage', sa.Float, nullable=False, default=0.0),
        sa.Column('nfr_coverage', sa.Float, nullable=False, default=0.0),
        sa.Column('compliance_score', sa.Float, nullable=False, default=0.0),
        sa.Column('config', JSONB, nullable=True),  # StaticAnalysisConfig
        sa.Column('summary', JSONB, nullable=True),  # to_summary() output
        sa.Column('errors', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_static_analysis_results_project_id', 'static_analysis_results', ['project_id'])
    op.create_index('ix_static_analysis_results_started_at', 'static_analysis_results', ['started_at'])

    # Business Rules table
    op.create_table(
        'business_rules',
        sa.Column('id', sa.String(20), primary_key=True),  # BR-0001 format
        sa.Column('analysis_id', sa.String(36), sa.ForeignKey('static_analysis_results.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_type', sa.String(20), nullable=False),  # validation, calculation, etc.
        sa.Column('condition', sa.Text, nullable=False),
        sa.Column('action', sa.Text, nullable=False),
        sa.Column('source_file', sa.String(500), nullable=False),
        sa.Column('source_line_start', sa.Integer, nullable=False),
        sa.Column('source_line_end', sa.Integer, nullable=False),
        sa.Column('variables_involved', JSONB, nullable=True),
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('natural_language', sa.Text, nullable=False),
        sa.Column('compliance_tags', JSONB, nullable=True),
        sa.Column('llm_validated', sa.Boolean, default=False),
        sa.Column('llm_confidence', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_business_rules_analysis_id', 'business_rules', ['analysis_id'])
    op.create_index('ix_business_rules_rule_type', 'business_rules', ['rule_type'])
    op.create_index('ix_business_rules_source_file', 'business_rules', ['source_file'])

    # NFR Detections table
    op.create_table(
        'nfr_detections',
        sa.Column('id', sa.String(20), primary_key=True),  # NFR-0001 format
        sa.Column('analysis_id', sa.String(36), sa.ForeignKey('static_analysis_results.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.String(30), nullable=False),  # security, performance, etc.
        sa.Column('pattern_matched', sa.String(100), nullable=False),
        sa.Column('source_file', sa.String(500), nullable=False),
        sa.Column('source_line', sa.Integer, nullable=False),
        sa.Column('code_snippet', sa.Text, nullable=True),
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('recommendation', sa.Text, nullable=True),
        sa.Column('compliance_relevance', JSONB, nullable=True),
        sa.Column('llm_validated', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_nfr_detections_analysis_id', 'nfr_detections', ['analysis_id'])
    op.create_index('ix_nfr_detections_category', 'nfr_detections', ['category'])
    op.create_index('ix_nfr_detections_source_file', 'nfr_detections', ['source_file'])

    # Compliance Violations table
    op.create_table(
        'compliance_violations',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('analysis_id', sa.String(36), sa.ForeignKey('static_analysis_results.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requirement_id', sa.String(50), nullable=False),  # e.g., NEN7510-9.4.1
        sa.Column('framework', sa.String(20), nullable=False),  # NEN7510, ISO27001, etc.
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('violation_type', sa.String(20), nullable=False),  # missing, forbidden
        sa.Column('severity', sa.String(20), nullable=False),  # critical, high, medium, low
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('line_number', sa.Integer, nullable=True),
        sa.Column('code_snippet', sa.Text, nullable=True),
        sa.Column('remediation', sa.Text, nullable=False),
        sa.Column('resolved', sa.Boolean, default=False),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
        sa.Column('resolved_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_compliance_violations_analysis_id', 'compliance_violations', ['analysis_id'])
    op.create_index('ix_compliance_violations_framework', 'compliance_violations', ['framework'])
    op.create_index('ix_compliance_violations_severity', 'compliance_violations', ['severity'])
    op.create_index('ix_compliance_violations_resolved', 'compliance_violations', ['resolved'])

    # Variable Classifications table
    op.create_table(
        'variable_classifications',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('analysis_id', sa.String(36), sa.ForeignKey('static_analysis_results.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('variable_type', sa.String(20), nullable=False),  # domain, implementation, control
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('context', sa.Text, nullable=True),
        sa.Column('reasoning', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_variable_classifications_analysis_id', 'variable_classifications', ['analysis_id'])
    op.create_index('ix_variable_classifications_type', 'variable_classifications', ['variable_type'])

    # Program Slices table
    op.create_table(
        'program_slices',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('analysis_id', sa.String(36), sa.ForeignKey('static_analysis_results.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('line_number', sa.Integer, nullable=False),
        sa.Column('variable_name', sa.String(200), nullable=False),
        sa.Column('direction', sa.String(20), nullable=False),  # backward, forward, both
        sa.Column('statements', JSONB, nullable=True),  # List of line numbers
        sa.Column('variables', JSONB, nullable=True),  # Set of variables in slice
        sa.Column('functions_involved', JSONB, nullable=True),
        sa.Column('files_involved', JSONB, nullable=True),
        sa.Column('slice_size', sa.Integer, nullable=False),
        sa.Column('complexity_score', sa.Float, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_program_slices_analysis_id', 'program_slices', ['analysis_id'])
    op.create_index('ix_program_slices_file_path', 'program_slices', ['file_path'])

    # Static Analysis Conflict Detection table (for 72.5% threshold conflicts)
    op.create_table(
        'static_analysis_conflicts',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('analysis_id', sa.String(36), sa.ForeignKey('static_analysis_results.id', ondelete='CASCADE'), nullable=False),
        sa.Column('finding_type', sa.String(30), nullable=False),  # business_rule, nfr, compliance
        sa.Column('finding_id', sa.String(50), nullable=False),  # Reference to the finding
        sa.Column('static_confidence', sa.Float, nullable=False),
        sa.Column('llm_confidence', sa.Float, nullable=True),
        sa.Column('conflict_type', sa.String(30), nullable=False),  # disagreement, classification_change, removal
        sa.Column('static_result', JSONB, nullable=True),
        sa.Column('llm_result', JSONB, nullable=True),
        sa.Column('resolution', sa.String(30), nullable=True),  # accepted_static, accepted_llm, human_review
        sa.Column('resolved_by', sa.String(100), nullable=True),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_static_analysis_conflicts_analysis_id', 'static_analysis_conflicts', ['analysis_id'])
    op.create_index('ix_static_analysis_conflicts_conflict_type', 'static_analysis_conflicts', ['conflict_type'])
    op.create_index('ix_static_analysis_conflicts_resolution', 'static_analysis_conflicts', ['resolution'])


def downgrade():
    op.drop_table('static_analysis_conflicts')
    op.drop_table('program_slices')
    op.drop_table('variable_classifications')
    op.drop_table('compliance_violations')
    op.drop_table('nfr_detections')
    op.drop_table('business_rules')
    op.drop_table('static_analysis_results')
