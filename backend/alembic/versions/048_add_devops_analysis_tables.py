"""Add DevOps Analysis tables - Week 97-98 Fase 14

Revision ID: 048_devops_analysis
Revises: 047_static_analysis
Create Date: 2025-12-23

GitHub/DevOps Analysis for repository intelligence:
- Repository analysis sessions
- Hot spots (high-change files)
- Contributor analysis (knowledge silos)
- PR patterns and review analysis
- CI/CD pipeline analysis
- Issue correlation
- Repository insights
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '048_devops_analysis'
down_revision = '047_static_analysis'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Repository Analyses table
    op.create_table(
        'repository_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('repository_url', sa.String(500), nullable=False),
        sa.Column('repository_name', sa.String(200), nullable=False),
        sa.Column('default_branch', sa.String(100), server_default='main'),
        sa.Column('analysis_depth', sa.String(50), server_default='standard'),
        sa.Column('include_forks', sa.Boolean(), server_default='false'),
        sa.Column('max_commits', sa.Integer(), server_default='1000'),
        sa.Column('max_prs', sa.Integer(), server_default='500'),
        sa.Column('total_commits', sa.Integer(), server_default='0'),
        sa.Column('total_prs', sa.Integer(), server_default='0'),
        sa.Column('total_issues', sa.Integer(), server_default='0'),
        sa.Column('total_contributors', sa.Integer(), server_default='0'),
        sa.Column('avg_pr_review_time_hours', sa.Float(), nullable=True),
        sa.Column('avg_pr_size_lines', sa.Float(), nullable=True),
        sa.Column('merge_conflict_rate', sa.Float(), nullable=True),
        sa.Column('test_coverage_percent', sa.Float(), nullable=True),
        sa.Column('build_success_rate', sa.Float(), nullable=True),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_repository_analyses_project_id', 'repository_analyses', ['project_id'])
    op.create_index('ix_repository_analyses_platform', 'repository_analyses', ['platform'])
    op.create_index('ix_repository_analyses_status', 'repository_analyses', ['status'])

    # Hot Spots table
    op.create_table(
        'hot_spots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_extension', sa.String(20), nullable=True),
        sa.Column('change_count', sa.Integer(), server_default='0'),
        sa.Column('lines_changed_total', sa.Integer(), server_default='0'),
        sa.Column('distinct_authors', sa.Integer(), server_default='0'),
        sa.Column('change_frequency_score', sa.Float(), server_default='0.0'),
        sa.Column('complexity_score', sa.Float(), nullable=True),
        sa.Column('risk_score', sa.Float(), server_default='0.0'),
        sa.Column('last_modified', sa.DateTime(), nullable=True),
        sa.Column('associated_bugs', sa.Integer(), server_default='0'),
        sa.ForeignKeyConstraint(['analysis_id'], ['repository_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_hot_spots_analysis_id', 'hot_spots', ['analysis_id'])
    op.create_index('ix_hot_spots_risk_score', 'hot_spots', ['risk_score'])

    # Contributor Analyses table
    op.create_table(
        'contributor_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('contributor_id', sa.String(100), nullable=False),
        sa.Column('contributor_name', sa.String(200), nullable=True),
        sa.Column('contributor_email', sa.String(200), nullable=True),
        sa.Column('total_commits', sa.Integer(), server_default='0'),
        sa.Column('total_prs', sa.Integer(), server_default='0'),
        sa.Column('total_reviews', sa.Integer(), server_default='0'),
        sa.Column('lines_added', sa.Integer(), server_default='0'),
        sa.Column('lines_removed', sa.Integer(), server_default='0'),
        sa.Column('primary_directories', sa.JSON(), server_default='[]'),
        sa.Column('primary_file_types', sa.JSON(), server_default='[]'),
        sa.Column('bus_factor_contribution', sa.Float(), server_default='0.0'),
        sa.Column('is_sole_maintainer_files', sa.Integer(), server_default='0'),
        sa.Column('first_commit_date', sa.DateTime(), nullable=True),
        sa.Column('last_commit_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['repository_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_contributor_analyses_analysis_id', 'contributor_analyses', ['analysis_id'])

    # PR Patterns table
    op.create_table(
        'pr_patterns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('pr_number', sa.Integer(), nullable=False),
        sa.Column('pr_title', sa.String(500), nullable=True),
        sa.Column('pr_state', sa.String(50), nullable=True),
        sa.Column('additions', sa.Integer(), server_default='0'),
        sa.Column('deletions', sa.Integer(), server_default='0'),
        sa.Column('changed_files', sa.Integer(), server_default='0'),
        sa.Column('review_count', sa.Integer(), server_default='0'),
        sa.Column('approval_count', sa.Integer(), server_default='0'),
        sa.Column('change_request_count', sa.Integer(), server_default='0'),
        sa.Column('comment_count', sa.Integer(), server_default='0'),
        sa.Column('time_to_first_review', sa.Float(), nullable=True),
        sa.Column('time_to_merge', sa.Float(), nullable=True),
        sa.Column('had_merge_conflicts', sa.Boolean(), server_default='false'),
        sa.Column('had_ci_failures', sa.Boolean(), server_default='false'),
        sa.Column('required_rework', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('merged_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['repository_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pr_patterns_analysis_id', 'pr_patterns', ['analysis_id'])

    # CI Pipeline Analyses table
    op.create_table(
        'ci_pipeline_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('pipeline_name', sa.String(200), nullable=False),
        sa.Column('pipeline_type', sa.String(50), nullable=True),
        sa.Column('total_runs', sa.Integer(), server_default='0'),
        sa.Column('successful_runs', sa.Integer(), server_default='0'),
        sa.Column('failed_runs', sa.Integer(), server_default='0'),
        sa.Column('avg_duration_minutes', sa.Float(), nullable=True),
        sa.Column('p95_duration_minutes', sa.Float(), nullable=True),
        sa.Column('success_rate', sa.Float(), server_default='0.0'),
        sa.Column('flaky_test_count', sa.Integer(), server_default='0'),
        sa.Column('triggers', sa.JSON(), server_default='[]'),
        sa.Column('stages', sa.JSON(), server_default='[]'),
        sa.Column('recent_runs', sa.JSON(), server_default='[]'),
        sa.ForeignKeyConstraint(['analysis_id'], ['repository_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ci_pipeline_analyses_analysis_id', 'ci_pipeline_analyses', ['analysis_id'])

    # Issue Correlations table
    op.create_table(
        'issue_correlations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('issue_number', sa.Integer(), nullable=False),
        sa.Column('issue_title', sa.String(500), nullable=True),
        sa.Column('issue_type', sa.String(50), nullable=True),
        sa.Column('issue_state', sa.String(50), nullable=True),
        sa.Column('labels', sa.JSON(), server_default='[]'),
        sa.Column('priority', sa.String(50), nullable=True),
        sa.Column('linked_pr_numbers', sa.JSON(), server_default='[]'),
        sa.Column('affected_files', sa.JSON(), server_default='[]'),
        sa.Column('suggested_epic', sa.String(200), nullable=True),
        sa.Column('suggested_work_type', sa.String(50), nullable=True),
        sa.Column('confidence_score', sa.Float(), server_default='0.5'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['repository_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_issue_correlations_analysis_id', 'issue_correlations', ['analysis_id'])

    # Repository Insights table
    op.create_table(
        'repository_insights',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('insight_type', sa.String(50), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.Float(), server_default='0.5'),
        sa.Column('evidence', sa.JSON(), server_default='{}'),
        sa.Column('affected_files', sa.JSON(), server_default='[]'),
        sa.Column('recommendations', sa.JSON(), server_default='[]'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['analysis_id'], ['repository_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_repository_insights_analysis_id', 'repository_insights', ['analysis_id'])
    op.create_index('ix_repository_insights_category', 'repository_insights', ['category'])


def downgrade() -> None:
    op.drop_table('repository_insights')
    op.drop_table('issue_correlations')
    op.drop_table('ci_pipeline_analyses')
    op.drop_table('pr_patterns')
    op.drop_table('contributor_analyses')
    op.drop_table('hot_spots')
    op.drop_table('repository_analyses')
