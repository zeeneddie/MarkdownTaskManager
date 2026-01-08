"""Add debt to backlog linkage

Revision ID: 037_add_debt_backlog_linkage
Revises: 036_add_deep_extraction_tables
Create Date: 2025-12-19

Links technical debt items to backlog hierarchy (epic/feature/story)
for categorized issue tracking and statistics.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers
revision = '037'
down_revision = '036'
branch_labels = None
depends_on = None


def upgrade():
    # Add optional foreign keys to technical_debt_items for backlog linkage
    op.add_column('technical_debt_items',
        sa.Column('epic_id', UUID(as_uuid=True), nullable=True))
    op.add_column('technical_debt_items',
        sa.Column('feature_id', UUID(as_uuid=True), nullable=True))
    op.add_column('technical_debt_items',
        sa.Column('story_id', UUID(as_uuid=True), nullable=True))
    op.add_column('technical_debt_items',
        sa.Column('categorization_source', sa.String(50), nullable=True))  # auto, manual
    op.add_column('technical_debt_items',
        sa.Column('categorized_at', sa.DateTime, nullable=True))

    # Create indexes for faster lookups
    op.create_index('ix_technical_debt_items_epic_id', 'technical_debt_items', ['epic_id'])
    op.create_index('ix_technical_debt_items_feature_id', 'technical_debt_items', ['feature_id'])
    op.create_index('ix_technical_debt_items_story_id', 'technical_debt_items', ['story_id'])

    # Create foreign key constraints (optional, can fail if tables don't exist)
    try:
        op.create_foreign_key(
            'fk_debt_item_epic', 'technical_debt_items', 'task_epics',
            ['epic_id'], ['id'], ondelete='SET NULL'
        )
        op.create_foreign_key(
            'fk_debt_item_feature', 'technical_debt_items', 'task_features',
            ['feature_id'], ['id'], ondelete='SET NULL'
        )
        op.create_foreign_key(
            'fk_debt_item_story', 'technical_debt_items', 'task_stories',
            ['story_id'], ['id'], ondelete='SET NULL'
        )
    except Exception:
        # Foreign keys optional if task tables don't exist yet
        pass

    # Create mapping table for file path to backlog item links
    op.create_table(
        'file_backlog_mappings',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_pattern', sa.String(500), nullable=False),  # Glob pattern or exact path
        sa.Column('epic_id', UUID(as_uuid=True), nullable=True),
        sa.Column('feature_id', UUID(as_uuid=True), nullable=True),
        sa.Column('story_id', UUID(as_uuid=True), nullable=True),
        sa.Column('priority', sa.Integer, default=0),  # Higher = more specific match
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('metadata', sa.JSON, default=dict),
    )

    op.create_index('ix_file_backlog_mappings_project_id', 'file_backlog_mappings', ['project_id'])
    op.create_index('ix_file_backlog_mappings_file_pattern', 'file_backlog_mappings', ['file_pattern'])

    # Create table for backlog issue statistics (aggregated per epic/feature/story)
    op.create_table(
        'backlog_debt_stats',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('snapshot_id', sa.Integer, sa.ForeignKey('technical_debt_snapshots.id', ondelete='CASCADE'), nullable=True),
        sa.Column('backlog_type', sa.String(20), nullable=False),  # epic, feature, story
        sa.Column('backlog_id', UUID(as_uuid=True), nullable=False),
        sa.Column('backlog_title', sa.String(300), nullable=True),
        # Issue counts
        sa.Column('total_issues', sa.Integer, default=0),
        sa.Column('critical_count', sa.Integer, default=0),
        sa.Column('high_count', sa.Integer, default=0),
        sa.Column('medium_count', sa.Integer, default=0),
        sa.Column('low_count', sa.Integer, default=0),
        # Debt metrics
        sa.Column('total_principal', sa.Float, default=0.0),
        sa.Column('total_interest', sa.Float, default=0.0),
        # Issue type breakdown
        sa.Column('issues_by_type', sa.JSON, default=dict),
        # Health score (0-100, derived from issues)
        sa.Column('health_score', sa.Float, default=100.0),
        # Timestamps
        sa.Column('calculated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('metadata', sa.JSON, default=dict),
    )

    op.create_index('ix_backlog_debt_stats_project_id', 'backlog_debt_stats', ['project_id'])
    op.create_index('ix_backlog_debt_stats_backlog_type', 'backlog_debt_stats', ['backlog_type'])
    op.create_index('ix_backlog_debt_stats_backlog_id', 'backlog_debt_stats', ['backlog_id'])


def downgrade():
    # Drop stats table
    op.drop_table('backlog_debt_stats')

    # Drop mapping table
    op.drop_table('file_backlog_mappings')

    # Drop foreign keys (ignore if they don't exist)
    try:
        op.drop_constraint('fk_debt_item_story', 'technical_debt_items')
        op.drop_constraint('fk_debt_item_feature', 'technical_debt_items')
        op.drop_constraint('fk_debt_item_epic', 'technical_debt_items')
    except Exception:
        pass

    # Drop indexes
    op.drop_index('ix_technical_debt_items_story_id', 'technical_debt_items')
    op.drop_index('ix_technical_debt_items_feature_id', 'technical_debt_items')
    op.drop_index('ix_technical_debt_items_epic_id', 'technical_debt_items')

    # Drop columns
    op.drop_column('technical_debt_items', 'categorized_at')
    op.drop_column('technical_debt_items', 'categorization_source')
    op.drop_column('technical_debt_items', 'story_id')
    op.drop_column('technical_debt_items', 'feature_id')
    op.drop_column('technical_debt_items', 'epic_id')
