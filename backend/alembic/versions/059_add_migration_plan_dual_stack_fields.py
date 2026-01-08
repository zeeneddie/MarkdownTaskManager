"""Add dual-stack and brown paper integration fields to migration_plans

Revision ID: 059_dual_stack
Revises: 058_add_bert_model_metadata_tables
Create Date: 2025-12-31

Week 128: MigrationPlan extensions for:
- Brown Paper Enhanced integration (brown_paper_session_id)
- Source codebase info (source_path, source_loc, source_file_count)
- Foundation detection results (foundation_modules, business_modules, foundation_summary)
- Dual-stack support (target_stacks, evaluation_mode, evaluation_criteria, stack_comparison)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = '059_dual_stack'
down_revision = '058_add_bert_model_metadata'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Brown Paper Integration
    op.add_column('migration_plans', sa.Column('brown_paper_session_id', sa.String(100), nullable=True))
    op.add_column('migration_plans', sa.Column('project_name', sa.String(200), nullable=True))

    # Source codebase info
    op.add_column('migration_plans', sa.Column('source_path', sa.String(500), nullable=True))
    op.add_column('migration_plans', sa.Column('source_loc', sa.Integer(), nullable=True))
    op.add_column('migration_plans', sa.Column('source_file_count', sa.Integer(), nullable=True))

    # Foundation detection results
    op.add_column('migration_plans', sa.Column('foundation_modules', JSONB, server_default='[]'))
    op.add_column('migration_plans', sa.Column('business_modules', JSONB, server_default='[]'))
    op.add_column('migration_plans', sa.Column('foundation_summary', JSONB, server_default='{}'))

    # Dual-stack support
    op.add_column('migration_plans', sa.Column('target_stacks', JSONB, server_default='[]'))
    op.add_column('migration_plans', sa.Column('evaluation_mode', sa.String(20), server_default="'single'"))
    op.add_column('migration_plans', sa.Column('evaluation_criteria', JSONB, server_default='[]'))
    op.add_column('migration_plans', sa.Column('stack_comparison', JSONB, server_default='{}'))

    # Create index for brown_paper_session_id lookups
    op.create_index(
        'ix_migration_plans_brown_paper_session_id',
        'migration_plans',
        ['brown_paper_session_id']
    )

    # Create index for evaluation_mode filtering
    op.create_index(
        'ix_migration_plans_evaluation_mode',
        'migration_plans',
        ['evaluation_mode']
    )


def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_migration_plans_evaluation_mode', table_name='migration_plans')
    op.drop_index('ix_migration_plans_brown_paper_session_id', table_name='migration_plans')

    # Remove dual-stack columns
    op.drop_column('migration_plans', 'stack_comparison')
    op.drop_column('migration_plans', 'evaluation_criteria')
    op.drop_column('migration_plans', 'evaluation_mode')
    op.drop_column('migration_plans', 'target_stacks')

    # Remove foundation columns
    op.drop_column('migration_plans', 'foundation_summary')
    op.drop_column('migration_plans', 'business_modules')
    op.drop_column('migration_plans', 'foundation_modules')

    # Remove source columns
    op.drop_column('migration_plans', 'source_file_count')
    op.drop_column('migration_plans', 'source_loc')
    op.drop_column('migration_plans', 'source_path')

    # Remove brown paper columns
    op.drop_column('migration_plans', 'project_name')
    op.drop_column('migration_plans', 'brown_paper_session_id')
