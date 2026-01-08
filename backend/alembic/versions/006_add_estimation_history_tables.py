"""Add estimation history tables for ML training

Revision ID: 006
Revises: 005
Create Date: 2025-11-21

Tables:
- estimation_projects: Project metadata for ML correlation
- function_point_estimates: Historical FP estimates with actuals
- story_point_estimates: Historical SP estimates with actuals
- ml_model_versions: ML model tracking and performance
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types (IF NOT EXISTS for idempotency)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE estimationtype AS ENUM (
                'function_points', 'story_points', 'combined'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE projectcomplexity AS ENUM (
                'simple', 'standard', 'complex', 'enterprise'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE techstack AS ENUM (
                'web_frontend', 'web_backend', 'fullstack',
                'mobile_native', 'mobile_hybrid', 'api_only',
                'microservices', 'data_pipeline', 'ml_ai',
                'embedded', 'other'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create estimation_projects table
    op.create_table(
        'estimation_projects',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('external_id', sa.String(100), nullable=True, index=True),

        # Project characteristics (ML features)
        # Use String instead of Enum to avoid auto-creation issues
        sa.Column('tech_stack', sa.String(50), nullable=True),
        sa.Column('team_size', sa.Integer(), nullable=True),
        sa.Column('experience_level', sa.Float(), nullable=True),
        sa.Column('domain_complexity', sa.Float(), nullable=True),
        sa.Column('has_legacy_integration', sa.Boolean(), default=False),
        sa.Column('has_external_apis', sa.Boolean(), default=False),
        sa.Column('is_greenfield', sa.Boolean(), default=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create function_point_estimates table
    op.create_table(
        'function_point_estimates',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('estimation_projects.id'), nullable=True),

        # Input features
        sa.Column('input_project_name', sa.String(255), nullable=False),

        # Component counts (key ML features)
        sa.Column('ilf_count', sa.Integer(), default=0),
        sa.Column('eif_count', sa.Integer(), default=0),
        sa.Column('ei_count', sa.Integer(), default=0),
        sa.Column('eo_count', sa.Integer(), default=0),
        sa.Column('eq_count', sa.Integer(), default=0),

        # Complexity distribution
        sa.Column('low_complexity_count', sa.Integer(), default=0),
        sa.Column('average_complexity_count', sa.Integer(), default=0),
        sa.Column('high_complexity_count', sa.Integer(), default=0),

        # Calculated results
        sa.Column('unadjusted_fp', sa.Integer(), nullable=False),
        sa.Column('vaf', sa.Float(), default=1.0),
        sa.Column('adjusted_fp', sa.Float(), nullable=False),

        # VAF breakdown
        sa.Column('vaf_applied', sa.Boolean(), default=False),
        sa.Column('gsc_ratings', JSON, nullable=True),

        # Full request/response
        sa.Column('full_request', JSON, nullable=True),
        sa.Column('full_response', JSON, nullable=True),

        # Actuals (for ML training)
        sa.Column('actual_effort_hours', sa.Float(), nullable=True),
        sa.Column('actual_person_days', sa.Float(), nullable=True),
        sa.Column('actual_duration_days', sa.Integer(), nullable=True),
        sa.Column('actual_team_size', sa.Integer(), nullable=True),
        sa.Column('actual_completion_date', sa.DateTime(), nullable=True),

        # Derived metrics
        sa.Column('estimation_accuracy', sa.Float(), nullable=True),

        # Metadata
        sa.Column('estimated_at', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('actuals_recorded_at', sa.DateTime(), nullable=True),
        sa.Column('source', sa.String(50), default='api'),
    )

    # Create story_point_estimates table
    op.create_table(
        'story_point_estimates',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('estimation_projects.id'), nullable=True),

        # Input features
        sa.Column('input_story_title', sa.String(500), nullable=False),
        sa.Column('input_story_description', sa.Text(), nullable=True),

        # Complexity factors (key ML features)
        sa.Column('technical_complexity', sa.Integer(), nullable=False),
        sa.Column('business_value', sa.Integer(), nullable=False),
        sa.Column('risk_level', sa.Integer(), nullable=False),
        sa.Column('uncertainty', sa.Integer(), nullable=False),
        sa.Column('dependencies', sa.Integer(), nullable=False),

        # PERT inputs
        sa.Column('pert_optimistic', sa.Float(), nullable=True),
        sa.Column('pert_most_likely', sa.Float(), nullable=True),
        sa.Column('pert_pessimistic', sa.Float(), nullable=True),
        sa.Column('pert_expected', sa.Float(), nullable=True),
        sa.Column('pert_std_dev', sa.Float(), nullable=True),

        # Calculated results
        sa.Column('story_points', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('confidence_range_low', sa.Integer(), nullable=True),
        sa.Column('confidence_range_high', sa.Integer(), nullable=True),

        # Risk assessment
        sa.Column('risk_factors', JSON, nullable=True),
        sa.Column('recommendations', JSON, nullable=True),

        # Full request/response
        sa.Column('full_request', JSON, nullable=True),
        sa.Column('full_response', JSON, nullable=True),

        # Actuals (for ML training)
        sa.Column('actual_effort_hours', sa.Float(), nullable=True),
        sa.Column('actual_person_days', sa.Float(), nullable=True),
        sa.Column('actual_duration_days', sa.Integer(), nullable=True),
        sa.Column('actual_story_points', sa.Integer(), nullable=True),
        sa.Column('actual_completion_date', sa.DateTime(), nullable=True),

        # Derived metrics
        sa.Column('estimation_accuracy', sa.Float(), nullable=True),
        sa.Column('velocity_factor', sa.Float(), nullable=True),

        # Metadata
        sa.Column('estimated_at', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('actuals_recorded_at', sa.DateTime(), nullable=True),
        sa.Column('source', sa.String(50), default='api'),
    )

    # Create ml_model_versions table
    op.create_table(
        'ml_model_versions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),

        # Model identification
        sa.Column('model_name', sa.String(100), nullable=False, index=True),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('model_type', sa.String(50), nullable=False),

        # Training metadata
        sa.Column('training_samples', sa.Integer(), nullable=False),
        sa.Column('training_date', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('features_used', JSON, nullable=False),
        sa.Column('hyperparameters', JSON, nullable=True),

        # Performance metrics
        sa.Column('mae', sa.Float(), nullable=True),
        sa.Column('rmse', sa.Float(), nullable=True),
        sa.Column('r2_score', sa.Float(), nullable=True),
        sa.Column('mape', sa.Float(), nullable=True),

        # Validation metrics
        sa.Column('cv_scores', JSON, nullable=True),
        sa.Column('test_mae', sa.Float(), nullable=True),
        sa.Column('test_rmse', sa.Float(), nullable=True),

        # Model state
        sa.Column('is_active', sa.Boolean(), default=False),
        sa.Column('model_path', sa.String(500), nullable=True),

        # Metadata
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('activated_at', sa.DateTime(), nullable=True),
        sa.Column('deactivated_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
    )

    # Create indexes for ML queries
    op.create_index(
        'idx_fp_estimates_estimated_at',
        'function_point_estimates',
        ['estimated_at']
    )
    op.create_index(
        'idx_sp_estimates_estimated_at',
        'story_point_estimates',
        ['estimated_at']
    )
    op.create_index(
        'idx_fp_estimates_has_actuals',
        'function_point_estimates',
        ['actual_effort_hours'],
        postgresql_where=sa.text('actual_effort_hours IS NOT NULL')
    )
    op.create_index(
        'idx_sp_estimates_has_actuals',
        'story_point_estimates',
        ['actual_effort_hours'],
        postgresql_where=sa.text('actual_effort_hours IS NOT NULL')
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_sp_estimates_has_actuals', 'story_point_estimates')
    op.drop_index('idx_fp_estimates_has_actuals', 'function_point_estimates')
    op.drop_index('idx_sp_estimates_estimated_at', 'story_point_estimates')
    op.drop_index('idx_fp_estimates_estimated_at', 'function_point_estimates')

    # Drop tables
    op.drop_table('ml_model_versions')
    op.drop_table('story_point_estimates')
    op.drop_table('function_point_estimates')
    op.drop_table('estimation_projects')

    # Drop enum types (IF EXISTS for safety)
    op.execute('DROP TYPE IF EXISTS techstack')
    op.execute('DROP TYPE IF EXISTS projectcomplexity')
    op.execute('DROP TYPE IF EXISTS estimationtype')
