"""Add Week 85 validation and delta tracking tables

Revision ID: 040
Revises: 039_hierarchical_extraction
Create Date: 2024-12-19

Week 85 - Validatie & Quality + Re-Run Capability:
- INVEST validation results
- Traceability matrix links
- Delta snapshots and events
- Re-run tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, ARRAY

revision = '040'
down_revision = '039_hierarchical_extraction'
branch_labels = None
depends_on = None


def upgrade():
    # INVEST Validation Results
    op.create_table(
        'invest_validation_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('story_id', sa.String(100), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('validation_level', sa.String(20), nullable=False),  # quick, standard, thorough
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('is_valid', sa.Boolean(), nullable=False),
        sa.Column('independent_score', sa.Float(), nullable=True),
        sa.Column('independent_status', sa.String(20), nullable=True),
        sa.Column('independent_feedback', sa.Text(), nullable=True),
        sa.Column('negotiable_score', sa.Float(), nullable=True),
        sa.Column('negotiable_status', sa.String(20), nullable=True),
        sa.Column('negotiable_feedback', sa.Text(), nullable=True),
        sa.Column('valuable_score', sa.Float(), nullable=True),
        sa.Column('valuable_status', sa.String(20), nullable=True),
        sa.Column('valuable_feedback', sa.Text(), nullable=True),
        sa.Column('estimable_score', sa.Float(), nullable=True),
        sa.Column('estimable_status', sa.String(20), nullable=True),
        sa.Column('estimable_feedback', sa.Text(), nullable=True),
        sa.Column('small_score', sa.Float(), nullable=True),
        sa.Column('small_status', sa.String(20), nullable=True),
        sa.Column('small_feedback', sa.Text(), nullable=True),
        sa.Column('testable_score', sa.Float(), nullable=True),
        sa.Column('testable_status', sa.String(20), nullable=True),
        sa.Column('testable_feedback', sa.Text(), nullable=True),
        sa.Column('recommendations', JSON, nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_invest_validation_project', 'invest_validation_results', ['project_id'])
    op.create_index('ix_invest_validation_story', 'invest_validation_results', ['story_id'])

    # SMART Validation Results (for tasks)
    op.create_table(
        'smart_validation_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(100), nullable=False),
        sa.Column('parent_story_id', sa.String(100), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('is_valid', sa.Boolean(), nullable=False),
        sa.Column('specific_score', sa.Float(), nullable=True),
        sa.Column('specific_feedback', sa.Text(), nullable=True),
        sa.Column('measurable_score', sa.Float(), nullable=True),
        sa.Column('measurable_feedback', sa.Text(), nullable=True),
        sa.Column('achievable_score', sa.Float(), nullable=True),
        sa.Column('achievable_feedback', sa.Text(), nullable=True),
        sa.Column('relevant_score', sa.Float(), nullable=True),
        sa.Column('relevant_feedback', sa.Text(), nullable=True),
        sa.Column('timebound_score', sa.Float(), nullable=True),
        sa.Column('timebound_feedback', sa.Text(), nullable=True),
        sa.Column('recommendations', JSON, nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_smart_validation_project', 'smart_validation_results', ['project_id'])
    op.create_index('ix_smart_validation_task', 'smart_validation_results', ['task_id'])

    # Traceability Links
    op.create_table(
        'traceability_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('link_id', sa.String(100), nullable=False, unique=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('code_element_id', sa.String(100), nullable=False),
        sa.Column('code_element_type', sa.String(50), nullable=False),
        sa.Column('code_element_path', sa.String(500), nullable=False),
        sa.Column('code_element_name', sa.String(200), nullable=False),
        sa.Column('story_id', sa.String(100), nullable=False),
        sa.Column('story_title', sa.String(500), nullable=True),
        sa.Column('story_type', sa.String(50), nullable=True),
        sa.Column('link_type', sa.String(50), nullable=False),  # implements, tests, documents, references
        sa.Column('confidence', sa.String(20), nullable=False),  # high, medium, low, manual
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('evidence', JSON, nullable=True),  # List of reasons
        sa.Column('verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_traceability_project', 'traceability_links', ['project_id'])
    op.create_index('ix_traceability_code', 'traceability_links', ['code_element_id'])
    op.create_index('ix_traceability_story', 'traceability_links', ['story_id'])
    op.create_index('ix_traceability_link_type', 'traceability_links', ['link_type'])

    # Delta Snapshots
    op.create_table(
        'delta_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snapshot_id', sa.String(100), nullable=False, unique=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('tier', sa.String(20), nullable=False),
        sa.Column('total_stories', sa.Integer(), nullable=False),
        sa.Column('total_epics', sa.Integer(), nullable=True),
        sa.Column('total_features', sa.Integer(), nullable=True),
        sa.Column('total_tasks', sa.Integer(), nullable=True),
        sa.Column('overall_confidence', sa.Float(), nullable=False),
        sa.Column('invest_score', sa.Float(), nullable=True),
        sa.Column('story_ids', JSON, nullable=True),  # Array of story IDs
        sa.Column('metadata', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_delta_snapshot_project', 'delta_snapshots', ['project_id'])
    op.create_index('ix_delta_snapshot_session', 'delta_snapshots', ['session_id'])
    op.create_index('ix_delta_snapshot_created', 'delta_snapshots', ['created_at'])

    # Delta Change Events
    op.create_table(
        'delta_change_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(100), nullable=False, unique=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('tier', sa.String(20), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),  # structural, refinement, discovery, removal, etc.
        sa.Column('entity_type', sa.String(50), nullable=False),  # story, epic, feature, task
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('entity_title', sa.String(500), nullable=True),
        sa.Column('change_description', sa.Text(), nullable=False),
        sa.Column('old_value', JSON, nullable=True),
        sa.Column('new_value', JSON, nullable=True),
        sa.Column('impact_score', sa.Float(), nullable=True),
        sa.Column('metadata', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_delta_event_project', 'delta_change_events', ['project_id'])
    op.create_index('ix_delta_event_session', 'delta_change_events', ['session_id'])
    op.create_index('ix_delta_event_entity', 'delta_change_events', ['entity_id'])
    op.create_index('ix_delta_event_category', 'delta_change_events', ['category'])
    op.create_index('ix_delta_event_created', 'delta_change_events', ['created_at'])

    # Re-Run Requests
    op.create_table(
        'rerun_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.String(100), nullable=False, unique=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('original_session_id', sa.String(100), nullable=False),
        sa.Column('target_tier', sa.String(20), nullable=False),
        sa.Column('reason', sa.String(50), nullable=False),
        sa.Column('quote_id', sa.String(100), nullable=True),
        sa.Column('focus_areas', JSON, nullable=True),
        sa.Column('requested_by', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rerun_request_project', 'rerun_requests', ['project_id'])
    op.create_index('ix_rerun_request_status', 'rerun_requests', ['status'])

    # Re-Run Results
    op.create_table(
        'rerun_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rerun_id', sa.String(100), nullable=False, unique=True),
        sa.Column('request_id', sa.String(100), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('original_session_id', sa.String(100), nullable=False),
        sa.Column('new_session_id', sa.String(100), nullable=True),
        sa.Column('original_tier', sa.String(20), nullable=False),
        sa.Column('rerun_tier', sa.String(20), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('cost_incurred', sa.Float(), nullable=True),
        sa.Column('stories_added', sa.Integer(), nullable=True),
        sa.Column('stories_removed', sa.Integer(), nullable=True),
        sa.Column('stories_modified', sa.Integer(), nullable=True),
        sa.Column('confidence_improvement', sa.Float(), nullable=True),
        sa.Column('errors', JSON, nullable=True),
        sa.Column('recommendations', JSON, nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rerun_result_project', 'rerun_results', ['project_id'])
    op.create_index('ix_rerun_result_request', 'rerun_results', ['request_id'])

    # Upgrade Quotes
    op.create_table(
        'upgrade_quotes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quote_id', sa.String(100), nullable=False, unique=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('current_tier', sa.String(20), nullable=False),
        sa.Column('target_tier', sa.String(20), nullable=False),
        sa.Column('price_difference', sa.Float(), nullable=False),
        sa.Column('expected_confidence_gain', sa.Float(), nullable=True),
        sa.Column('expected_story_improvement', sa.Integer(), nullable=True),
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, default=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_upgrade_quote_project', 'upgrade_quotes', ['project_id'])
    op.create_index('ix_upgrade_quote_valid', 'upgrade_quotes', ['valid_until'])

    # Human Review Sessions
    op.create_table(
        'human_review_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False, unique=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('extraction_session_id', sa.String(100), nullable=False),
        sa.Column('reviewer_id', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),  # pending, in_progress, completed
        sa.Column('total_stories', sa.Integer(), nullable=False),
        sa.Column('approved_count', sa.Integer(), nullable=False, default=0),
        sa.Column('rejected_count', sa.Integer(), nullable=False, default=0),
        sa.Column('pending_count', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_human_review_project', 'human_review_sessions', ['project_id'])
    op.create_index('ix_human_review_status', 'human_review_sessions', ['status'])

    # Human Review Decisions
    op.create_table(
        'human_review_decisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('decision_id', sa.String(100), nullable=False, unique=True),
        sa.Column('review_session_id', sa.String(100), nullable=False),
        sa.Column('story_id', sa.String(100), nullable=False),
        sa.Column('decision', sa.String(20), nullable=False),  # approved, rejected, needs_revision
        sa.Column('confidence_before', sa.Float(), nullable=True),
        sa.Column('invest_score_before', sa.Float(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('revision_notes', sa.Text(), nullable=True),
        sa.Column('decided_by', sa.String(100), nullable=False),
        sa.Column('decided_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_review_decision_session', 'human_review_decisions', ['review_session_id'])
    op.create_index('ix_review_decision_story', 'human_review_decisions', ['story_id'])
    op.create_index('ix_review_decision_result', 'human_review_decisions', ['decision'])


def downgrade():
    op.drop_table('human_review_decisions')
    op.drop_table('human_review_sessions')
    op.drop_table('upgrade_quotes')
    op.drop_table('rerun_results')
    op.drop_table('rerun_requests')
    op.drop_table('delta_change_events')
    op.drop_table('delta_snapshots')
    op.drop_table('traceability_links')
    op.drop_table('smart_validation_results')
    op.drop_table('invest_validation_results')
