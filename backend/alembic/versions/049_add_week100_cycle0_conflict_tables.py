"""Add Week 100 Cycle 0 and Static-LLM Conflict tables

Revision ID: 049
Revises: 048_devops_analysis
Create Date: 2025-12-24

Week 100 - Fase 15b Pipeline Integration:
1. Add Cycle 0 (Static Analysis) fields to extraction_sessions
2. Create static_llm_conflicts table for Static vs LLM conflict tracking
3. Add conflict resolution tracking

Key features:
- cycle_0_completed_at timestamp
- Static analysis metrics (domain_coverage, nfr_coverage, compliance_score)
- Conflict detection with 72.5% threshold
- Human review workflow for conflict resolution
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = '049_add_week100_cycle0_conflict_tables'
down_revision = '048_devops_analysis'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # ADD CYCLE 0 FIELDS TO EXTRACTION_SESSIONS
    # =========================================================================

    # Cycle 0 timestamp (before cycle 1)
    op.add_column(
        'extraction_sessions',
        sa.Column('cycle_0_completed_at', sa.DateTime, nullable=True)
    )

    # Static analysis reference
    op.add_column(
        'extraction_sessions',
        sa.Column('static_analysis_id', sa.String(100), nullable=True)
    )

    # Static analysis metrics
    op.add_column(
        'extraction_sessions',
        sa.Column('static_domain_coverage', sa.Float, nullable=True)
    )
    op.add_column(
        'extraction_sessions',
        sa.Column('static_nfr_coverage', sa.Float, nullable=True)
    )
    op.add_column(
        'extraction_sessions',
        sa.Column('static_compliance_score', sa.Float, nullable=True)
    )

    # Static analysis counts
    op.add_column(
        'extraction_sessions',
        sa.Column('static_business_rules_count', sa.Integer, default=0)
    )
    op.add_column(
        'extraction_sessions',
        sa.Column('static_nfr_count', sa.Integer, default=0)
    )
    op.add_column(
        'extraction_sessions',
        sa.Column('static_compliance_violations_count', sa.Integer, default=0)
    )
    op.add_column(
        'extraction_sessions',
        sa.Column('static_high_confidence_count', sa.Integer, default=0)
    )
    op.add_column(
        'extraction_sessions',
        sa.Column('static_low_confidence_count', sa.Integer, default=0)
    )

    # Conflict summary (denormalized for quick access)
    op.add_column(
        'extraction_sessions',
        sa.Column('total_conflicts', sa.Integer, default=0)
    )
    op.add_column(
        'extraction_sessions',
        sa.Column('conflicts_auto_resolved', sa.Integer, default=0)
    )
    op.add_column(
        'extraction_sessions',
        sa.Column('conflicts_pending_review', sa.Integer, default=0)
    )
    op.add_column(
        'extraction_sessions',
        sa.Column('conflicts_human_resolved', sa.Integer, default=0)
    )

    # =========================================================================
    # CREATE STATIC_LLM_CONFLICTS TABLE
    # Week 100 - Tracking conflicts between Static Analysis and LLM results
    # =========================================================================
    op.create_table(
        'static_llm_conflicts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('extraction_sessions.id', ondelete='CASCADE'), nullable=False, index=True),

        # Item identification
        sa.Column('item_id', sa.String(100), nullable=False, index=True),
        sa.Column('item_type', sa.String(50), nullable=True),  # business_rule, nfr, compliance, etc.

        # Conflict classification
        sa.Column('conflict_type', sa.String(50), nullable=False),
        # Types: confidence_threshold, explicit_disagreement, classification_change,
        #        item_removal, priority_mismatch, scope_expansion, scope_reduction

        sa.Column('severity', sa.String(20), nullable=False, default='medium'),
        # Severity: low, medium, high, critical

        # Static Analysis side
        sa.Column('static_classification', sa.String(100), nullable=True),
        sa.Column('static_confidence', sa.Float, nullable=True),
        sa.Column('static_data', JSONB, nullable=True),
        sa.Column('static_source_file', sa.String(500), nullable=True),
        sa.Column('static_source_line', sa.Integer, nullable=True),

        # LLM Analysis side
        sa.Column('llm_classification', sa.String(100), nullable=True),
        sa.Column('llm_confidence', sa.Float, nullable=True),
        sa.Column('llm_data', JSONB, nullable=True),
        sa.Column('llm_provider', sa.String(100), nullable=True),
        sa.Column('llm_model', sa.String(100), nullable=True),

        # Conflict details
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('impact_assessment', sa.Text, nullable=True),
        sa.Column('recommendations', JSONB, nullable=True),  # List of recommendations

        # Resolution
        sa.Column('status', sa.String(20), nullable=False, default='pending', index=True),
        # Status: pending, auto_resolved, human_review, resolved, rejected

        sa.Column('resolution', sa.String(50), nullable=True),
        # Resolution: auto_accepted_static, auto_accepted_llm, human_selected_static,
        #             human_selected_llm, human_merged, human_rejected_both

        sa.Column('resolved_at', sa.DateTime, nullable=True),
        sa.Column('resolved_by', sa.String(100), nullable=True),  # "system" or user_id
        sa.Column('resolution_notes', sa.Text, nullable=True),

        # Final value (merged or selected)
        sa.Column('final_value', JSONB, nullable=True),
        sa.Column('final_classification', sa.String(100), nullable=True),
        sa.Column('final_confidence', sa.Float, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Index for efficient conflict queries
    op.create_index(
        'ix_static_llm_conflicts_status_severity',
        'static_llm_conflicts',
        ['status', 'severity']
    )
    op.create_index(
        'ix_static_llm_conflicts_session_status',
        'static_llm_conflicts',
        ['session_id', 'status']
    )

    # =========================================================================
    # CREATE CONFLICT_RESOLUTION_HISTORY TABLE
    # Tracks all actions taken on conflicts for audit
    # =========================================================================
    op.create_table(
        'conflict_resolution_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('conflict_id', UUID(as_uuid=True), sa.ForeignKey('static_llm_conflicts.id', ondelete='CASCADE'), nullable=False, index=True),

        # Action details
        sa.Column('action', sa.String(50), nullable=False),
        # Actions: created, viewed, assigned, resolved, reopened, escalated

        sa.Column('action_by', sa.String(100), nullable=False),  # "system" or user_id
        sa.Column('action_data', JSONB, nullable=True),  # Additional action context

        # Before/after state
        sa.Column('previous_status', sa.String(20), nullable=True),
        sa.Column('new_status', sa.String(20), nullable=True),
        sa.Column('previous_resolution', sa.String(50), nullable=True),
        sa.Column('new_resolution', sa.String(50), nullable=True),

        # Notes
        sa.Column('notes', sa.Text, nullable=True),

        # Timestamp
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )

    # =========================================================================
    # ADD CONFLICT REFERENCE TO EXTRACTION_CONSENSUS
    # Link consensus items to their source conflicts
    # =========================================================================
    op.add_column(
        'extraction_consensus',
        sa.Column('source_conflict_id', UUID(as_uuid=True),
                  sa.ForeignKey('static_llm_conflicts.id', ondelete='SET NULL'),
                  nullable=True)
    )
    op.add_column(
        'extraction_consensus',
        sa.Column('from_static_analysis', sa.String(1), default='N')  # Y/N
    )


def downgrade() -> None:
    # Remove consensus columns
    op.drop_column('extraction_consensus', 'from_static_analysis')
    op.drop_column('extraction_consensus', 'source_conflict_id')

    # Drop history table
    op.drop_table('conflict_resolution_history')

    # Drop conflicts table
    op.drop_index('ix_static_llm_conflicts_session_status', table_name='static_llm_conflicts')
    op.drop_index('ix_static_llm_conflicts_status_severity', table_name='static_llm_conflicts')
    op.drop_table('static_llm_conflicts')

    # Remove session columns
    op.drop_column('extraction_sessions', 'conflicts_human_resolved')
    op.drop_column('extraction_sessions', 'conflicts_pending_review')
    op.drop_column('extraction_sessions', 'conflicts_auto_resolved')
    op.drop_column('extraction_sessions', 'total_conflicts')
    op.drop_column('extraction_sessions', 'static_low_confidence_count')
    op.drop_column('extraction_sessions', 'static_high_confidence_count')
    op.drop_column('extraction_sessions', 'static_compliance_violations_count')
    op.drop_column('extraction_sessions', 'static_nfr_count')
    op.drop_column('extraction_sessions', 'static_business_rules_count')
    op.drop_column('extraction_sessions', 'static_compliance_score')
    op.drop_column('extraction_sessions', 'static_nfr_coverage')
    op.drop_column('extraction_sessions', 'static_domain_coverage')
    op.drop_column('extraction_sessions', 'static_analysis_id')
    op.drop_column('extraction_sessions', 'cycle_0_completed_at')
