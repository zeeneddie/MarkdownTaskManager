"""Add bug tracking tables

Revision ID: 020_bug_tracking
Revises: 019_fp_sp_estimation
Create Date: 2025-12-01

Week 58: Bug tracking tables for standalone issue management.
Bugs can be tracked on Kanban board alongside Stories and Tasks.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '020_bug_tracking'
down_revision = '019_add_fp_sp_estimation_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Bugs table - main bug tracking
    op.create_table(
        'bugs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bug_number', sa.String(20), nullable=False, unique=True),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),

        # Status & Priority
        sa.Column('status', sa.String(20), nullable=False, default='draft'),
        sa.Column('severity', sa.String(20), nullable=False, default='medium'),
        sa.Column('priority', sa.String(20), nullable=False, default='medium'),

        # Categorization
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('component', sa.String(100), nullable=True),
        sa.Column('tags', postgresql.JSONB(), nullable=True),

        # Reproduction
        sa.Column('reproduction_steps', sa.Text(), nullable=True),
        sa.Column('expected_behavior', sa.Text(), nullable=True),
        sa.Column('actual_behavior', sa.Text(), nullable=True),
        sa.Column('environment', postgresql.JSONB(), nullable=True),

        # Technical Analysis
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('affected_files', postgresql.JSONB(), nullable=True),
        sa.Column('related_bugs', postgresql.JSONB(), nullable=True),

        # Estimation
        sa.Column('story_points', sa.Integer(), nullable=True),
        sa.Column('function_points', sa.Integer(), nullable=True),
        sa.Column('estimated_hours', sa.Float(), nullable=True),
        sa.Column('actual_hours', sa.Float(), nullable=True),

        # Acceptance Criteria
        sa.Column('acceptance_criteria', postgresql.JSONB(), nullable=True),

        # Linking (optional)
        sa.Column('project_id', sa.String(50), nullable=True),
        sa.Column('application_id', sa.Integer(), nullable=True),
        sa.Column('epic_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('feature_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Assignment
        sa.Column('reporter', sa.String(100), nullable=True),
        sa.Column('assigned_to', sa.String(100), nullable=True),
        sa.Column('reviewer', sa.String(100), nullable=True),

        # Blocking
        sa.Column('is_blocked', sa.Boolean(), default=False),
        sa.Column('blocked_reason', sa.Text(), nullable=True),
        sa.Column('blocking_bugs', postgresql.JSONB(), nullable=True),

        # Git Integration
        sa.Column('branch_name', sa.String(200), nullable=True),
        sa.Column('commit_sha', sa.String(40), nullable=True),
        sa.Column('pull_request_url', sa.String(500), nullable=True),

        # Source
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('source_reference', sa.String(500), nullable=True),

        # Dates
        sa.Column('reported_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('analysis_started_at', sa.DateTime(), nullable=True),
        sa.Column('analysis_completed_at', sa.DateTime(), nullable=True),
        sa.Column('fix_started_at', sa.DateTime(), nullable=True),
        sa.Column('fixed_at', sa.DateTime(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),

        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),

        # Import metadata
        sa.Column('imported_from', sa.String(500), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['epic_id'], ['task_epics.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['feature_id'], ['task_features.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_bugs_bug_number', 'bugs', ['bug_number'], unique=True)
    op.create_index('ix_bugs_status', 'bugs', ['status'])
    op.create_index('ix_bugs_severity', 'bugs', ['severity'])
    op.create_index('ix_bugs_project_id', 'bugs', ['project_id'])
    op.create_index('ix_bugs_application_id', 'bugs', ['application_id'])
    op.create_index('ix_bugs_assigned_to', 'bugs', ['assigned_to'])

    # Bug Comments table
    op.create_table(
        'bug_comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bug_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author', sa.String(100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('comment_type', sa.String(20), default='comment'),
        sa.Column('old_status', sa.String(20), nullable=True),
        sa.Column('new_status', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['bug_id'], ['bugs.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_bug_comments_bug_id', 'bug_comments', ['bug_id'])


def downgrade() -> None:
    op.drop_index('ix_bug_comments_bug_id', table_name='bug_comments')
    op.drop_table('bug_comments')

    op.drop_index('ix_bugs_assigned_to', table_name='bugs')
    op.drop_index('ix_bugs_application_id', table_name='bugs')
    op.drop_index('ix_bugs_project_id', table_name='bugs')
    op.drop_index('ix_bugs_severity', table_name='bugs')
    op.drop_index('ix_bugs_status', table_name='bugs')
    op.drop_index('ix_bugs_bug_number', table_name='bugs')
    op.drop_table('bugs')
