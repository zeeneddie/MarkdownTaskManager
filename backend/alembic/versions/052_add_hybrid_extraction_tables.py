"""Add hybrid extraction tables

Revision ID: 052
Revises: 051
Create Date: 2025-12-27

Week 111-114 Phase 5: Hybrid Business Rule Extraction Pipeline - LLM Integration

Tables:
- hybrid_extraction_sessions: Track extraction sessions
- hybrid_extracted_rules: Store extracted business rules
- hybrid_extraction_metrics: Performance and cost metrics
- hybrid_workflow_correlations: Detected CRUD workflows
- hybrid_entity_mappings: Detected entities from rules
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '052_add_hybrid_extraction_tables'
down_revision = '051_add_traceability_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Hybrid Extraction Sessions
    op.create_table(
        'hybrid_extraction_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_path', sa.String(1000), nullable=False),
        sa.Column('extraction_tier', sa.String(20), nullable=False, default='STANDARD'),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('workflow_type', sa.String(30), nullable=True),  # BROWN_PAPER, MIGRATION, etc.

        # Metrics
        sa.Column('total_files', sa.Integer(), default=0),
        sa.Column('total_lines', sa.Integer(), default=0),
        sa.Column('total_rules', sa.Integer(), default=0),
        sa.Column('high_confidence_rules', sa.Integer(), default=0),
        sa.Column('average_confidence', sa.Float(), default=0.0),

        # LLM Statistics
        sa.Column('static_rules_extracted', sa.Integer(), default=0),
        sa.Column('llm_rules_extracted', sa.Integer(), default=0),
        sa.Column('rules_classified', sa.Integer(), default=0),
        sa.Column('rules_confirmed', sa.Integer(), default=0),
        sa.Column('rules_rejected', sa.Integer(), default=0),
        sa.Column('multi_llm_validated', sa.Integer(), default=0),
        sa.Column('consensus_reached', sa.Integer(), default=0),
        sa.Column('premium_synthesis_performed', sa.Boolean(), default=False),

        # Cost tracking
        sa.Column('total_tokens', sa.Integer(), default=0),
        sa.Column('total_cost_cents', sa.Float(), default=0.0),

        # Timing
        sa.Column('static_extraction_ms', sa.Integer(), default=0),
        sa.Column('llm_classification_ms', sa.Integer(), default=0),
        sa.Column('llm_extraction_ms', sa.Integer(), default=0),
        sa.Column('multi_llm_validation_ms', sa.Integer(), default=0),
        sa.Column('premium_synthesis_ms', sa.Integer(), default=0),
        sa.Column('total_ms', sa.Integer(), default=0),

        # Detected technologies
        sa.Column('detected_languages', JSONB, default=[]),
        sa.Column('detected_frameworks', JSONB, default=[]),
        sa.Column('database_patterns', JSONB, default=[]),

        # Premium synthesis result
        sa.Column('synthesis_result', JSONB, nullable=True),

        # Errors and warnings
        sa.Column('errors', JSONB, default=[]),
        sa.Column('warnings', JSONB, default=[]),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )

    # Hybrid Extracted Rules (from all 12 extractors)
    op.create_table(
        'hybrid_extracted_rules',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('hybrid_extraction_sessions.id', ondelete='CASCADE'), nullable=False),

        # Rule classification
        sa.Column('rule_type', sa.String(30), nullable=False),  # VALIDATION, AUTHORIZATION, etc.
        sa.Column('extraction_method', sa.String(20), nullable=False),  # AST, REGEX, LLM
        sa.Column('language', sa.String(30), nullable=False),  # VB.NET, Python, etc.

        # Rule content
        sa.Column('condition', sa.Text(), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('natural_language', sa.Text(), nullable=True),
        sa.Column('code_snippet', sa.Text(), nullable=True),

        # Source location
        sa.Column('source_file', sa.String(500), nullable=False),
        sa.Column('source_line_start', sa.Integer(), nullable=True),
        sa.Column('source_line_end', sa.Integer(), nullable=True),

        # Variables and entities
        sa.Column('variables_involved', JSONB, default=[]),
        sa.Column('entities_referenced', JSONB, default=[]),

        # Confidence
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('llm_validated', sa.Boolean(), default=False),
        sa.Column('llm_confidence', sa.Float(), nullable=True),
        sa.Column('validation_provider', sa.String(30), nullable=True),  # ollama, claude, etc.

        # Compliance
        sa.Column('compliance_tags', JSONB, default=[]),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Hybrid Workflow Correlations (CRUD patterns)
    op.create_table(
        'hybrid_workflow_correlations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('hybrid_extraction_sessions.id', ondelete='CASCADE'), nullable=False),

        # Workflow identification
        sa.Column('workflow_name', sa.String(200), nullable=False),
        sa.Column('workflow_type', sa.String(30), nullable=False),  # CRUD, STATE_MACHINE, APPROVAL
        sa.Column('primary_entity', sa.String(100), nullable=True),

        # Operations
        sa.Column('operations', JSONB, default=[]),  # CREATE, READ, UPDATE, DELETE
        sa.Column('total_rules', sa.Integer(), default=0),

        # Source
        sa.Column('source_files', JSONB, default=[]),
        sa.Column('auth_pattern', sa.String(100), nullable=True),

        # Confidence
        sa.Column('confidence', sa.Float(), nullable=False, default=0.7),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Hybrid Entity Mappings
    op.create_table(
        'hybrid_entity_mappings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('hybrid_extraction_sessions.id', ondelete='CASCADE'), nullable=False),

        # Entity identification
        sa.Column('entity_name', sa.String(200), nullable=False),
        sa.Column('entity_type', sa.String(30), nullable=False),  # TABLE, CLASS, MODULE

        # CRUD coverage
        sa.Column('rule_count', sa.Integer(), default=0),
        sa.Column('has_create', sa.Boolean(), default=False),
        sa.Column('has_read', sa.Boolean(), default=False),
        sa.Column('has_update', sa.Boolean(), default=False),
        sa.Column('has_delete', sa.Boolean(), default=False),
        sa.Column('crud_coverage', sa.String(10), nullable=True),  # e.g., "CRU-" for Create/Read/Update

        # Source
        sa.Column('files_referenced', JSONB, default=[]),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index('ix_hybrid_sessions_project', 'hybrid_extraction_sessions', ['project_id'])
    op.create_index('ix_hybrid_sessions_status', 'hybrid_extraction_sessions', ['status'])
    op.create_index('ix_hybrid_sessions_workflow', 'hybrid_extraction_sessions', ['workflow_type'])
    op.create_index('ix_hybrid_rules_session', 'hybrid_extracted_rules', ['session_id'])
    op.create_index('ix_hybrid_rules_type', 'hybrid_extracted_rules', ['rule_type'])
    op.create_index('ix_hybrid_rules_language', 'hybrid_extracted_rules', ['language'])
    op.create_index('ix_hybrid_rules_confidence', 'hybrid_extracted_rules', ['confidence'])
    op.create_index('ix_hybrid_workflows_session', 'hybrid_workflow_correlations', ['session_id'])
    op.create_index('ix_hybrid_entities_session', 'hybrid_entity_mappings', ['session_id'])


def downgrade() -> None:
    op.drop_index('ix_hybrid_entities_session')
    op.drop_index('ix_hybrid_workflows_session')
    op.drop_index('ix_hybrid_rules_confidence')
    op.drop_index('ix_hybrid_rules_language')
    op.drop_index('ix_hybrid_rules_type')
    op.drop_index('ix_hybrid_rules_session')
    op.drop_index('ix_hybrid_sessions_workflow')
    op.drop_index('ix_hybrid_sessions_status')
    op.drop_index('ix_hybrid_sessions_project')

    op.drop_table('hybrid_entity_mappings')
    op.drop_table('hybrid_workflow_correlations')
    op.drop_table('hybrid_extracted_rules')
    op.drop_table('hybrid_extraction_sessions')
