"""add hierarchical extraction tables

Revision ID: 039_hierarchical_extraction
Revises: 038
Create Date: 2024-12-19

Week 84: Hierarchical Story Extraction

Tables:
- hierarchical_extraction_sessions: Main extraction session tracking
- extracted_story_items: Individual extracted items (epics, features, stories, tasks)
- extraction_hierarchy_relations: Parent-child relationships
- extraction_level_metrics: Per-level statistics
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '039_hierarchical_extraction'
down_revision = '038'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE extraction_level AS ENUM ('function', 'class', 'module', 'system');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE story_item_type AS ENUM (
                'epic', 'feature', 'story', 'task', 'product_area', 'cross_cutting'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE story_confidence_level AS ENUM ('high', 'medium', 'low');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE extraction_session_status AS ENUM (
                'pending', 'running', 'completed', 'failed'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create hierarchical_extraction_sessions table
    op.create_table(
        'hierarchical_extraction_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),

        # Configuration
        sa.Column('repository_path', sa.String(1024), nullable=False),
        sa.Column('tier', sa.String(50), default='FREE'),
        sa.Column('primary_stack', sa.String(100), nullable=True),
        sa.Column('few_shot_template', sa.String(100), nullable=True),

        # Levels included
        sa.Column('include_function_level', sa.Boolean(), default=True),
        sa.Column('include_class_level', sa.Boolean(), default=True),
        sa.Column('include_module_level', sa.Boolean(), default=True),
        sa.Column('include_system_level', sa.Boolean(), default=True),

        # Status
        sa.Column('status', postgresql.ENUM('pending', 'running', 'completed', 'failed',
                                            name='extraction_session_status', create_type=False),
                  default='pending'),

        # Metrics
        sa.Column('total_epics', sa.Integer(), default=0),
        sa.Column('total_features', sa.Integer(), default=0),
        sa.Column('total_stories', sa.Integer(), default=0),
        sa.Column('total_tasks', sa.Integer(), default=0),
        sa.Column('overall_confidence', sa.Float(), default=0.0),

        # Cost and performance
        sa.Column('total_tokens', sa.Integer(), default=0),
        sa.Column('total_cost_usd', sa.Float(), default=0.0),
        sa.Column('duration_ms', sa.Integer(), default=0),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),

        # Errors
        sa.Column('errors', postgresql.JSONB(), default=[]),

        # Link to code analysis aggregation (Week 83)
        sa.Column('aggregation_id', postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Create extracted_story_items table
    op.create_table(
        'extracted_story_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('hierarchical_extraction_sessions.id', ondelete='CASCADE'),
                  nullable=False),

        # Type and level
        sa.Column('item_type', postgresql.ENUM('epic', 'feature', 'story', 'task',
                                               'product_area', 'cross_cutting',
                                               name='story_item_type', create_type=False),
                  nullable=False),
        sa.Column('extraction_level', postgresql.ENUM('function', 'class', 'module', 'system',
                                                      name='extraction_level', create_type=False),
                  nullable=False),

        # Content
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('acceptance_criteria', postgresql.JSONB(), default=[]),

        # Source context
        sa.Column('source_file', sa.String(1024), nullable=True),
        sa.Column('source_symbol', sa.String(255), nullable=True),
        sa.Column('source_line_start', sa.Integer(), nullable=True),
        sa.Column('source_line_end', sa.Integer(), nullable=True),

        # Hierarchy
        sa.Column('parent_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('extracted_story_items.id', ondelete='SET NULL'),
                  nullable=True),

        # Confidence
        sa.Column('confidence', sa.Float(), default=0.0),
        sa.Column('confidence_level', postgresql.ENUM('high', 'medium', 'low',
                                                       name='story_confidence_level', create_type=False),
                  default='low'),

        # Complexity
        sa.Column('complexity', sa.String(50), default='medium'),

        # Estimation
        sa.Column('story_points', sa.Integer(), nullable=True),
        sa.Column('function_points', sa.Float(), nullable=True),

        # Tags
        sa.Column('tags', postgresql.JSONB(), default=[]),

        # Extraction metadata
        sa.Column('extracted_by', sa.String(100), nullable=True),
        sa.Column('extracted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('raw_response', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Create extraction_hierarchy_relations table
    op.create_table(
        'extraction_hierarchy_relations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('extracted_story_items.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('child_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('extracted_story_items.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('relationship_type', sa.String(50), default='contains'),
        sa.Column('confidence', sa.Float(), default=1.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create extraction_level_metrics table
    op.create_table(
        'extraction_level_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('hierarchical_extraction_sessions.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('level', postgresql.ENUM('function', 'class', 'module', 'system',
                                           name='extraction_level', create_type=False),
                  nullable=False),

        # Counts
        sa.Column('story_count', sa.Integer(), default=0),
        sa.Column('feature_count', sa.Integer(), default=0),
        sa.Column('epic_count', sa.Integer(), default=0),
        sa.Column('task_count', sa.Integer(), default=0),
        sa.Column('total_items', sa.Integer(), default=0),

        # Quality
        sa.Column('avg_confidence', sa.Float(), default=0.0),
        sa.Column('high_confidence_count', sa.Integer(), default=0),
        sa.Column('medium_confidence_count', sa.Integer(), default=0),
        sa.Column('low_confidence_count', sa.Integer(), default=0),

        # Performance
        sa.Column('tokens_used', sa.Integer(), default=0),
        sa.Column('duration_ms', sa.Integer(), default=0),

        # Errors
        sa.Column('error_count', sa.Integer(), default=0),
        sa.Column('errors', postgresql.JSONB(), default=[]),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index('ix_hier_extract_sessions_project', 'hierarchical_extraction_sessions', ['project_id'])
    op.create_index('ix_hier_extract_sessions_status', 'hierarchical_extraction_sessions', ['status'])
    op.create_index('ix_extracted_story_items_session', 'extracted_story_items', ['session_id'])
    op.create_index('ix_extracted_story_items_type', 'extracted_story_items', ['item_type'])
    op.create_index('ix_extracted_story_items_level', 'extracted_story_items', ['extraction_level'])
    op.create_index('ix_extracted_story_items_parent', 'extracted_story_items', ['parent_id'])
    op.create_index('ix_extracted_story_items_confidence', 'extracted_story_items', ['confidence'])
    op.create_index('ix_extraction_relations_parent', 'extraction_hierarchy_relations', ['parent_id'])
    op.create_index('ix_extraction_relations_child', 'extraction_hierarchy_relations', ['child_id'])
    op.create_index('ix_extraction_level_metrics_session', 'extraction_level_metrics', ['session_id'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_extraction_level_metrics_session')
    op.drop_index('ix_extraction_relations_child')
    op.drop_index('ix_extraction_relations_parent')
    op.drop_index('ix_extracted_story_items_confidence')
    op.drop_index('ix_extracted_story_items_parent')
    op.drop_index('ix_extracted_story_items_level')
    op.drop_index('ix_extracted_story_items_type')
    op.drop_index('ix_extracted_story_items_session')
    op.drop_index('ix_hier_extract_sessions_status')
    op.drop_index('ix_hier_extract_sessions_project')

    # Drop tables
    op.drop_table('extraction_level_metrics')
    op.drop_table('extraction_hierarchy_relations')
    op.drop_table('extracted_story_items')
    op.drop_table('hierarchical_extraction_sessions')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS extraction_session_status")
    op.execute("DROP TYPE IF EXISTS story_confidence_level")
    op.execute("DROP TYPE IF EXISTS story_item_type")
    op.execute("DROP TYPE IF EXISTS extraction_level")
