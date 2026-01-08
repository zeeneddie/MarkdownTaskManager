"""add quality gate config tables

Revision ID: 010
Revises: 009
Create Date: 2025-11-24 10:00:00.000000

Week 49 Day 1: Quality Gates Configuration UI
- QualityGateConfig: Main config per project
- QualityCategoryConfig: Category settings
- QualityCheckConfig: Individual check settings
- QualityWorkflowRules: Per-workflow blocking rules
- QualityConfigHistory: Audit trail
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums using raw SQL with IF NOT EXISTS
    op.execute("DO $$ BEGIN CREATE TYPE severity_level AS ENUM ('critical', 'high', 'medium', 'low'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE change_type AS ENUM ('category_update', 'check_update', 'workflow_update', 'reset', 'create'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE entity_type AS ENUM ('category', 'check', 'workflow', 'config'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")

    # 1. Create quality_gate_configs table (main config)
    op.create_table(
        'quality_gate_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),  # Optional: links to external project system
        sa.Column('name', sa.String(100), nullable=False, server_default='default'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'name', name='uq_quality_gate_config_project_name')
    )

    # 2. Create quality_category_configs table
    op.create_table(
        'quality_category_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', sa.String(50), nullable=False),
        sa.Column('category_name', sa.String(100), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('target_score', sa.Integer(), nullable=False, server_default='80'),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['config_id'], ['quality_gate_configs.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('config_id', 'category_id', name='uq_category_config_config_category'),
        sa.CheckConstraint('target_score >= 0 AND target_score <= 100', name='ck_category_target_score_range')
    )
    op.create_index('ix_quality_category_configs_config_id', 'quality_category_configs', ['config_id'])

    # 3. Create quality_check_configs table
    op.create_table(
        'quality_check_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('check_id', sa.String(100), nullable=False),
        sa.Column('check_name', sa.String(200), nullable=True),
        sa.Column('category_id', sa.String(50), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('severity', postgresql.ENUM('critical', 'high', 'medium', 'low', name='severity_level', create_type=False), nullable=False, server_default='medium'),
        sa.Column('threshold_value', sa.Float(), nullable=True),
        sa.Column('threshold_type', sa.String(20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('fix_suggestion', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['config_id'], ['quality_gate_configs.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('config_id', 'check_id', name='uq_check_config_config_check')
    )
    op.create_index('ix_quality_check_configs_config_id', 'quality_check_configs', ['config_id'])
    op.create_index('ix_quality_check_configs_category_id', 'quality_check_configs', ['category_id'])

    # 4. Create quality_workflow_rules table
    op.create_table(
        'quality_workflow_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_type', sa.String(50), nullable=False),
        sa.Column('blocking_severities', postgresql.ARRAY(sa.String()), nullable=False, server_default='{"critical"}'),
        sa.Column('required_coverage', sa.Integer(), nullable=False, server_default='80'),
        sa.Column('e2e_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('regression_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('documentation_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('max_iterations', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('stop_on_first_failure', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['config_id'], ['quality_gate_configs.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('config_id', 'workflow_type', name='uq_workflow_rules_config_workflow')
    )
    op.create_index('ix_quality_workflow_rules_config_id', 'quality_workflow_rules', ['config_id'])

    # 5. Create quality_config_history table (audit trail)
    op.create_table(
        'quality_config_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('changed_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('changed_by', sa.String(100), nullable=True),
        sa.Column('change_type', postgresql.ENUM('category_update', 'check_update', 'workflow_update', 'reset', 'create', name='change_type', create_type=False), nullable=False),
        sa.Column('entity_type', postgresql.ENUM('category', 'check', 'workflow', 'config', name='entity_type', create_type=False), nullable=True),
        sa.Column('entity_id', sa.String(100), nullable=True),
        sa.Column('old_value', postgresql.JSONB(), nullable=True),
        sa.Column('new_value', postgresql.JSONB(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['config_id'], ['quality_gate_configs.id'], ondelete='CASCADE')
    )
    op.create_index('ix_quality_config_history_config_id', 'quality_config_history', ['config_id'])
    op.create_index('ix_quality_config_history_changed_at', 'quality_config_history', ['changed_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('quality_config_history')
    op.drop_table('quality_workflow_rules')
    op.drop_table('quality_check_configs')
    op.drop_table('quality_category_configs')
    op.drop_table('quality_gate_configs')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS entity_type')
    op.execute('DROP TYPE IF EXISTS change_type')
    op.execute('DROP TYPE IF EXISTS severity_level')
