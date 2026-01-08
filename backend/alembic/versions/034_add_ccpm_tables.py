"""Add CCPM tables for Week 79

Revision ID: 034
Revises: 033
Create Date: 2025-12-16

Tables:
- git_worktrees: Parallel agent workspaces
- github_issues_sync: GitHub issue synchronization
- prd_decompositions: PRD breakdown into tasks
- task_recommendations: Intelligent task prioritization
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = '034'
down_revision = '033'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Git Worktrees - Parallel agent workspaces
    op.create_table(
        'git_worktrees',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        sa.Column('agent_id', sa.String(100), nullable=False),  # Agent using this worktree
        sa.Column('worktree_path', sa.String(500), nullable=False),  # Local path
        sa.Column('base_branch', sa.String(200), nullable=False),  # e.g., main, develop
        sa.Column('work_branch', sa.String(200), nullable=False),  # Agent's working branch
        sa.Column('status', sa.String(50), default='active'),  # active, merged, abandoned, conflict
        sa.Column('commit_count', sa.Integer, default=0),
        sa.Column('files_changed', sa.Integer, default=0),
        sa.Column('last_commit_sha', sa.String(40), nullable=True),
        sa.Column('last_commit_message', sa.Text, nullable=True),
        sa.Column('merge_status', sa.String(50), nullable=True),  # pending, merged, conflict, rejected
        sa.Column('merge_target', sa.String(200), nullable=True),
        sa.Column('merged_at', sa.DateTime, nullable=True),
        sa.Column('merged_by', sa.String(100), nullable=True),
        sa.Column('worktree_metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_git_worktrees_agent', 'git_worktrees', ['agent_id'])
    op.create_index('ix_git_worktrees_status', 'git_worktrees', ['status'])
    op.create_index('ix_git_worktrees_project', 'git_worktrees', ['project_id'])

    # GitHub Issues Sync - Bidirectional synchronization
    op.create_table(
        'github_issues_sync',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        sa.Column('github_repo', sa.String(200), nullable=False),  # owner/repo format
        sa.Column('github_issue_number', sa.Integer, nullable=False),
        sa.Column('github_issue_id', sa.BigInteger, nullable=True),  # GitHub's internal ID
        sa.Column('local_task_id', UUID(as_uuid=True), nullable=True),  # Link to local task
        sa.Column('local_task_type', sa.String(50), nullable=True),  # epic, feature, story, task
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('body', sa.Text, nullable=True),
        sa.Column('state', sa.String(20), nullable=False),  # open, closed
        sa.Column('labels', JSONB, default=[]),
        sa.Column('assignees', JSONB, default=[]),
        sa.Column('milestone', sa.String(200), nullable=True),
        sa.Column('github_url', sa.String(500), nullable=True),
        sa.Column('sync_direction', sa.String(20), default='bidirectional'),  # github_to_local, local_to_github, bidirectional
        sa.Column('last_synced_at', sa.DateTime, nullable=True),
        sa.Column('github_updated_at', sa.DateTime, nullable=True),
        sa.Column('local_updated_at', sa.DateTime, nullable=True),
        sa.Column('sync_status', sa.String(50), default='synced'),  # synced, pending, conflict, error
        sa.Column('sync_error', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_github_issues_repo', 'github_issues_sync', ['github_repo'])
    op.create_index('ix_github_issues_number', 'github_issues_sync', ['github_repo', 'github_issue_number'], unique=True)
    op.create_index('ix_github_issues_local', 'github_issues_sync', ['local_task_id'])
    op.create_index('ix_github_issues_sync_status', 'github_issues_sync', ['sync_status'])

    # PRD Decompositions - Product Requirements Document breakdown
    op.create_table(
        'prd_decompositions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('prd_content', sa.Text, nullable=False),  # Original PRD text
        sa.Column('prd_hash', sa.String(64), nullable=True),  # SHA256 hash for change detection
        sa.Column('status', sa.String(50), default='pending'),  # pending, processing, completed, failed
        sa.Column('epics_count', sa.Integer, default=0),
        sa.Column('features_count', sa.Integer, default=0),
        sa.Column('stories_count', sa.Integer, default=0),
        sa.Column('tasks_count', sa.Integer, default=0),
        sa.Column('total_story_points', sa.Integer, nullable=True),
        sa.Column('total_function_points', sa.Float, nullable=True),
        sa.Column('decomposition_result', JSONB, default={}),  # Full hierarchical breakdown
        sa.Column('agent_used', sa.String(100), nullable=True),  # Which agent performed decomposition
        sa.Column('llm_model', sa.String(100), nullable=True),
        sa.Column('processing_time_ms', sa.Integer, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_prd_decompositions_project', 'prd_decompositions', ['project_id'])
    op.create_index('ix_prd_decompositions_status', 'prd_decompositions', ['status'])

    # Task Recommendations - Intelligent task prioritization
    op.create_table(
        'task_recommendations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        sa.Column('task_id', UUID(as_uuid=True), nullable=True),  # Recommended task
        sa.Column('task_type', sa.String(50), nullable=True),
        sa.Column('task_title', sa.String(500), nullable=False),
        sa.Column('priority_score', sa.Float, nullable=False),  # 0-100 priority score
        sa.Column('reasoning', sa.Text, nullable=True),  # Why this task is recommended
        sa.Column('factors', JSONB, default={}),  # Breakdown of scoring factors
        sa.Column('dependencies_met', sa.Boolean, default=True),
        sa.Column('blocked_by', JSONB, default=[]),  # List of blocking task IDs
        sa.Column('recommended_agent', sa.String(100), nullable=True),  # Best agent for this task
        sa.Column('estimated_effort_hours', sa.Float, nullable=True),
        sa.Column('impact_score', sa.Float, nullable=True),  # Business impact
        sa.Column('urgency_score', sa.Float, nullable=True),  # Time sensitivity
        sa.Column('complexity_score', sa.Float, nullable=True),  # Technical complexity
        sa.Column('status', sa.String(50), default='pending'),  # pending, accepted, rejected, completed
        sa.Column('accepted_at', sa.DateTime, nullable=True),
        sa.Column('accepted_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime, nullable=True),  # Recommendation validity
    )
    op.create_index('ix_task_recommendations_project', 'task_recommendations', ['project_id'])
    op.create_index('ix_task_recommendations_priority', 'task_recommendations', ['priority_score'])
    op.create_index('ix_task_recommendations_status', 'task_recommendations', ['status'])


def downgrade() -> None:
    op.drop_table('task_recommendations')
    op.drop_table('prd_decompositions')
    op.drop_table('github_issues_sync')
    op.drop_table('git_worktrees')
