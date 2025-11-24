"""Add task hierarchy tables for Week 11

Revision ID: 005
Revises: 004
Create Date: 2025-11-19

This migration adds the 4 task hierarchy tables:
1. task_epics - High-level business capabilities from specifications
2. task_features - Specific user-facing capabilities within epics
3. task_stories - User stories with acceptance criteria
4. task_tasks - Technical work items for implementing stories

Hierarchy: Specification → Epic → Feature → Story → Task
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create task_epics table
    op.create_table(
        'task_epics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('specification_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('priority', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('business_value', sa.Text(), nullable=True),
        sa.Column('user_personas', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('acceptance_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('estimated_story_points', sa.Integer(), nullable=True),
        sa.Column('estimated_weeks', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('target_date', sa.DateTime(), nullable=True),
        sa.Column('completion_date', sa.DateTime(), nullable=True),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('progress_percentage', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('generated_by', sa.String(50), nullable=True, server_default='Felix'),
        sa.Column('generated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('generation_prompt', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['specification_id'], ['green_paper_specifications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['items.id'], ondelete='CASCADE'),
        sa.CheckConstraint("status IN ('draft', 'planned', 'in_progress', 'completed', 'on_hold', 'cancelled')", name='check_epic_status'),
        sa.CheckConstraint("priority IN ('critical', 'high', 'medium', 'low')", name='check_epic_priority'),
        sa.CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100', name='check_epic_progress'),
    )

    # Create indexes for task_epics
    op.create_index('ix_task_epics_specification_id', 'task_epics', ['specification_id'])
    op.create_index('ix_task_epics_project_id', 'task_epics', ['project_id'])
    op.create_index('ix_task_epics_status', 'task_epics', ['status'])
    op.create_index('ix_task_epics_title', 'task_epics', ['title'])

    # Create task_features table
    op.create_table(
        'task_features',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('epic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('priority', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('technical_approach', sa.Text(), nullable=True),
        sa.Column('api_endpoints', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('database_changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('dependencies', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('estimated_story_points', sa.Integer(), nullable=True),
        sa.Column('estimated_days', sa.Integer(), nullable=True),
        sa.Column('complexity', sa.String(20), nullable=True),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('progress_percentage', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('generated_by', sa.String(50), nullable=True, server_default='Felix'),
        sa.Column('generated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['epic_id'], ['task_epics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['items.id'], ondelete='CASCADE'),
        sa.CheckConstraint("status IN ('draft', 'planned', 'in_progress', 'completed', 'on_hold', 'cancelled')", name='check_feature_status'),
        sa.CheckConstraint("priority IN ('critical', 'high', 'medium', 'low')", name='check_feature_priority'),
        sa.CheckConstraint("complexity IN ('simple', 'moderate', 'complex')", name='check_feature_complexity'),
        sa.CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100', name='check_feature_progress'),
    )

    # Create indexes for task_features
    op.create_index('ix_task_features_epic_id', 'task_features', ['epic_id'])
    op.create_index('ix_task_features_project_id', 'task_features', ['project_id'])
    op.create_index('ix_task_features_status', 'task_features', ['status'])
    op.create_index('ix_task_features_title', 'task_features', ['title'])

    # Create task_stories table
    op.create_table(
        'task_stories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feature_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.String(50), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('user_type', sa.String(100), nullable=True),
        sa.Column('user_goal', sa.Text(), nullable=True),
        sa.Column('user_benefit', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('priority', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('acceptance_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('story_points', sa.Integer(), nullable=True),
        sa.Column('estimated_hours', sa.Float(), nullable=True),
        sa.Column('actual_hours', sa.Float(), nullable=True),
        sa.Column('sprint_id', sa.String(50), nullable=True),
        sa.Column('assigned_to', sa.String(100), nullable=True),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('is_blocked', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('blocked_reason', sa.Text(), nullable=True),
        sa.Column('generated_by', sa.String(50), nullable=True, server_default='Felix'),
        sa.Column('generated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['feature_id'], ['task_features.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['items.id'], ondelete='CASCADE'),
        sa.CheckConstraint("status IN ('draft', 'ready', 'in_progress', 'in_review', 'done', 'blocked')", name='check_story_status'),
        sa.CheckConstraint("priority IN ('critical', 'high', 'medium', 'low')", name='check_story_priority'),
        sa.CheckConstraint('story_points IN (1, 2, 3, 5, 8, 13, 21)', name='check_story_points_fibonacci'),
    )

    # Create indexes for task_stories
    op.create_index('ix_task_stories_feature_id', 'task_stories', ['feature_id'])
    op.create_index('ix_task_stories_project_id', 'task_stories', ['project_id'])
    op.create_index('ix_task_stories_status', 'task_stories', ['status'])
    op.create_index('ix_task_stories_title', 'task_stories', ['title'])
    op.create_index('ix_task_stories_sprint_id', 'task_stories', ['sprint_id'])

    # Create task_tasks table
    op.create_table(
        'task_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('story_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='todo'),
        sa.Column('priority', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('task_type', sa.String(50), nullable=True),
        sa.Column('technical_notes', sa.Text(), nullable=True),
        sa.Column('code_files', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('estimated_hours', sa.Float(), nullable=True),
        sa.Column('actual_hours', sa.Float(), nullable=True),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('assigned_to', sa.String(100), nullable=True),
        sa.Column('is_blocked', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('blocked_reason', sa.Text(), nullable=True),
        sa.Column('branch_name', sa.String(200), nullable=True),
        sa.Column('commit_sha', sa.String(40), nullable=True),
        sa.Column('pull_request_url', sa.String(500), nullable=True),
        sa.Column('generated_by', sa.String(50), nullable=True, server_default='Felix'),
        sa.Column('generated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['story_id'], ['task_stories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['items.id'], ondelete='CASCADE'),
        sa.CheckConstraint("status IN ('todo', 'in_progress', 'in_review', 'done', 'blocked')", name='check_task_status'),
        sa.CheckConstraint("priority IN ('critical', 'high', 'medium', 'low')", name='check_task_priority'),
        sa.CheckConstraint("task_type IN ('backend', 'frontend', 'database', 'testing', 'devops')", name='check_task_type'),
    )

    # Create indexes for task_tasks
    op.create_index('ix_task_tasks_story_id', 'task_tasks', ['story_id'])
    op.create_index('ix_task_tasks_project_id', 'task_tasks', ['project_id'])
    op.create_index('ix_task_tasks_status', 'task_tasks', ['status'])
    op.create_index('ix_task_tasks_title', 'task_tasks', ['title'])


def downgrade() -> None:
    # Drop task_tasks table
    op.drop_index('ix_task_tasks_title', table_name='task_tasks')
    op.drop_index('ix_task_tasks_status', table_name='task_tasks')
    op.drop_index('ix_task_tasks_project_id', table_name='task_tasks')
    op.drop_index('ix_task_tasks_story_id', table_name='task_tasks')
    op.drop_table('task_tasks')

    # Drop task_stories table
    op.drop_index('ix_task_stories_sprint_id', table_name='task_stories')
    op.drop_index('ix_task_stories_title', table_name='task_stories')
    op.drop_index('ix_task_stories_status', table_name='task_stories')
    op.drop_index('ix_task_stories_project_id', table_name='task_stories')
    op.drop_index('ix_task_stories_feature_id', table_name='task_stories')
    op.drop_table('task_stories')

    # Drop task_features table
    op.drop_index('ix_task_features_title', table_name='task_features')
    op.drop_index('ix_task_features_status', table_name='task_features')
    op.drop_index('ix_task_features_project_id', table_name='task_features')
    op.drop_index('ix_task_features_epic_id', table_name='task_features')
    op.drop_table('task_features')

    # Drop task_epics table
    op.drop_index('ix_task_epics_title', table_name='task_epics')
    op.drop_index('ix_task_epics_status', table_name='task_epics')
    op.drop_index('ix_task_epics_project_id', table_name='task_epics')
    op.drop_index('ix_task_epics_specification_id', table_name='task_epics')
    op.drop_table('task_epics')
