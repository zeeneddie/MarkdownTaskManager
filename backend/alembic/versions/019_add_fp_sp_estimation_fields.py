"""
Add Function Point and Story Point estimation fields.

Week 57: Brown Paper FP/SP integration

Revision ID: 019_add_fp_sp_estimation_fields
Revises: 018_add_brown_paper_tables
Create Date: 2025-11-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '019_add_fp_sp_estimation_fields'
down_revision = '018_brown_paper'
branch_labels = None
depends_on = None


def upgrade():
    """Add FP/SP estimation fields to brown paper tables."""

    # Add estimation fields to brown_paper_sessions
    op.add_column('brown_paper_sessions',
        sa.Column('total_function_points', sa.Integer(), nullable=True)
    )
    op.add_column('brown_paper_sessions',
        sa.Column('total_story_points', sa.Integer(), nullable=True)
    )
    op.add_column('brown_paper_sessions',
        sa.Column('vaf', sa.Float(), nullable=True, comment='Value Adjustment Factor')
    )
    op.add_column('brown_paper_sessions',
        sa.Column('fp_confidence_score', sa.Float(), nullable=True, comment='FP estimation confidence 0-100')
    )
    op.add_column('brown_paper_sessions',
        sa.Column('fp_analysis_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )

    # Add estimation fields to brown_paper_analyses
    op.add_column('brown_paper_analyses',
        sa.Column('fp_components', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='IFPUG components (ILF, EIF, EI, EO, EQ)')
    )
    op.add_column('brown_paper_analyses',
        sa.Column('fp_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='FP breakdown per component type')
    )
    op.add_column('brown_paper_analyses',
        sa.Column('gsc_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='General System Characteristics')
    )
    op.add_column('brown_paper_analyses',
        sa.Column('low_confidence_items', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Items requiring human review')
    )

    # Add estimation fields to brown_paper_epics
    op.add_column('brown_paper_epics',
        sa.Column('function_points', sa.Integer(), nullable=True)
    )
    op.add_column('brown_paper_epics',
        sa.Column('story_points', sa.Integer(), nullable=True)
    )
    op.add_column('brown_paper_epics',
        sa.Column('fp_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='FP breakdown for this epic')
    )
    op.add_column('brown_paper_epics',
        sa.Column('estimation_confidence', sa.Float(), nullable=True, comment='Estimation confidence 0-100')
    )

    # Add estimation fields to brown_paper_code_modules
    op.add_column('brown_paper_code_modules',
        sa.Column('function_points', sa.Integer(), nullable=True)
    )
    op.add_column('brown_paper_code_modules',
        sa.Column('story_points', sa.Integer(), nullable=True)
    )
    op.add_column('brown_paper_code_modules',
        sa.Column('fp_components', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    op.add_column('brown_paper_code_modules',
        sa.Column('estimation_confidence', sa.Float(), nullable=True)
    )

    # Add estimation fields to brown_paper_domains
    op.add_column('brown_paper_domains',
        sa.Column('function_points', sa.Integer(), nullable=True)
    )
    op.add_column('brown_paper_domains',
        sa.Column('story_points', sa.Integer(), nullable=True)
    )
    op.add_column('brown_paper_domains',
        sa.Column('fp_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )

    # Create new table for FP estimation history
    op.create_table('fp_estimation_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('brown_paper_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('application_id', sa.Integer(), nullable=False, index=True),

        # Estimation snapshots
        sa.Column('total_ufp', sa.Integer(), nullable=False, comment='Unadjusted Function Points'),
        sa.Column('total_afp', sa.Integer(), nullable=False, comment='Adjusted Function Points'),
        sa.Column('vaf', sa.Float(), nullable=False, comment='Value Adjustment Factor'),
        sa.Column('estimated_sp', sa.Integer(), nullable=False, comment='Estimated Story Points'),

        # Component counts
        sa.Column('ilf_count', sa.Integer(), default=0),
        sa.Column('eif_count', sa.Integer(), default=0),
        sa.Column('ei_count', sa.Integer(), default=0),
        sa.Column('eo_count', sa.Integer(), default=0),
        sa.Column('eq_count', sa.Integer(), default=0),

        # Quality metrics
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('low_confidence_count', sa.Integer(), default=0),
        sa.Column('requires_review', sa.Boolean(), default=False),

        # Full breakdown
        sa.Column('fp_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('gsc_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Metadata
        sa.Column('analyzed_paths', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('file_extensions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('analysis_duration_ms', sa.Integer(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for common queries
    op.create_index('ix_fp_estimation_history_app_created',
        'fp_estimation_history', ['application_id', 'created_at'])


def downgrade():
    """Remove FP/SP estimation fields."""

    # Drop new table
    op.drop_index('ix_fp_estimation_history_app_created', 'fp_estimation_history')
    op.drop_table('fp_estimation_history')

    # Remove columns from brown_paper_domains
    op.drop_column('brown_paper_domains', 'fp_breakdown')
    op.drop_column('brown_paper_domains', 'story_points')
    op.drop_column('brown_paper_domains', 'function_points')

    # Remove columns from brown_paper_code_modules
    op.drop_column('brown_paper_code_modules', 'estimation_confidence')
    op.drop_column('brown_paper_code_modules', 'fp_components')
    op.drop_column('brown_paper_code_modules', 'story_points')
    op.drop_column('brown_paper_code_modules', 'function_points')

    # Remove columns from brown_paper_epics
    op.drop_column('brown_paper_epics', 'estimation_confidence')
    op.drop_column('brown_paper_epics', 'fp_breakdown')
    op.drop_column('brown_paper_epics', 'story_points')
    op.drop_column('brown_paper_epics', 'function_points')

    # Remove columns from brown_paper_analyses
    op.drop_column('brown_paper_analyses', 'low_confidence_items')
    op.drop_column('brown_paper_analyses', 'gsc_scores')
    op.drop_column('brown_paper_analyses', 'fp_breakdown')
    op.drop_column('brown_paper_analyses', 'fp_components')

    # Remove columns from brown_paper_sessions
    op.drop_column('brown_paper_sessions', 'fp_analysis_result')
    op.drop_column('brown_paper_sessions', 'fp_confidence_score')
    op.drop_column('brown_paper_sessions', 'vaf')
    op.drop_column('brown_paper_sessions', 'total_story_points')
    op.drop_column('brown_paper_sessions', 'total_function_points')
