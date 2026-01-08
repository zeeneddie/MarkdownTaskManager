"""Add engagement system tables - Week 119-120

Client Portal 2.0 Phase 3: Engagement
- Feedback loop (feature_feedback, feedback_requests)
- Gamification (badge_definitions, user_badges, user_levels, user_points)
- Personalized dashboard (dashboard_preferences, feature_recommendations)

Revision ID: 055_add_engagement_system_tables
Revises: 054_add_portal_enhancement_tables
Create Date: 2025-12-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '055_add_engagement_system_tables'
down_revision = '054_add_portal_enhancement_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============== FEEDBACK LOOP TABLES ==============

    # Feature feedback - post-release feedback from customers
    op.create_table(
        'feature_feedback',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('feature_request_id', sa.Integer, nullable=False, index=True),
        sa.Column('project_id', sa.Integer, nullable=True, index=True),
        sa.Column('customer_id', sa.String(100), nullable=False, index=True),
        # Feedback content
        sa.Column('rating', sa.Integer, nullable=False),  # 1-5 stars
        sa.Column('satisfaction_score', sa.Integer, nullable=True),  # 1-10 NPS-style
        sa.Column('meets_expectations', sa.Boolean, nullable=True),
        sa.Column('would_recommend', sa.Boolean, nullable=True),
        sa.Column('feedback_text', sa.Text, nullable=True),
        sa.Column('improvement_suggestions', sa.Text, nullable=True),
        # Categorization
        sa.Column('feedback_type', sa.String(50), nullable=False, default='general'),  # general, bug, enhancement, praise
        sa.Column('sentiment', sa.String(20), nullable=True),  # positive, neutral, negative
        sa.Column('tags', JSONB, nullable=True, default=[]),
        # Status
        sa.Column('status', sa.String(30), nullable=False, default='pending'),  # pending, reviewed, actioned, archived
        sa.Column('reviewed_by', sa.String(100), nullable=True),
        sa.Column('reviewed_at', sa.DateTime, nullable=True),
        sa.Column('action_taken', sa.Text, nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True, onupdate=sa.func.now()),
    )

    # Feedback requests - proactive feedback solicitation
    op.create_table(
        'feedback_requests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('feature_request_id', sa.Integer, nullable=False, index=True),
        sa.Column('project_id', sa.Integer, nullable=True, index=True),
        sa.Column('customer_id', sa.String(100), nullable=False, index=True),
        # Request details
        sa.Column('request_type', sa.String(50), nullable=False, default='post_release'),  # post_release, milestone, periodic
        sa.Column('trigger_event', sa.String(100), nullable=True),  # e.g., "feature_deployed", "30_days_active"
        sa.Column('message', sa.Text, nullable=True),
        # Status
        sa.Column('status', sa.String(30), nullable=False, default='pending'),  # pending, sent, responded, expired
        sa.Column('sent_at', sa.DateTime, nullable=True),
        sa.Column('responded_at', sa.DateTime, nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        # Link to response
        sa.Column('feedback_id', UUID(as_uuid=True), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # ============== GAMIFICATION TABLES ==============

    # Badge definitions - available badges
    op.create_table(
        'badge_definitions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(150), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('icon', sa.String(100), nullable=True),  # icon name or emoji
        sa.Column('color', sa.String(20), nullable=True),  # hex color
        # Category
        sa.Column('category', sa.String(50), nullable=False, default='general'),  # engagement, feedback, contribution, milestone
        sa.Column('tier', sa.String(20), nullable=False, default='bronze'),  # bronze, silver, gold, platinum, diamond
        # Earning criteria
        sa.Column('criteria_type', sa.String(50), nullable=False),  # count, threshold, action, custom
        sa.Column('criteria_target', sa.String(100), nullable=True),  # e.g., "features_requested", "feedback_given"
        sa.Column('criteria_value', sa.Integer, nullable=True),  # e.g., 10 for "10 features requested"
        sa.Column('criteria_config', JSONB, nullable=True),  # complex criteria
        # Points
        sa.Column('points_awarded', sa.Integer, nullable=False, default=10),
        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('is_secret', sa.Boolean, nullable=False, default=False),  # hidden until earned
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # User badges - earned badges
    op.create_table(
        'user_badges',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', sa.String(100), nullable=False, index=True),
        sa.Column('badge_id', UUID(as_uuid=True), nullable=False, index=True),
        # Earning details
        sa.Column('earned_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('earned_for', sa.Text, nullable=True),  # description of how it was earned
        sa.Column('progress_snapshot', JSONB, nullable=True),  # state when earned
        # Display
        sa.Column('is_displayed', sa.Boolean, nullable=False, default=True),  # show on profile
        sa.Column('display_order', sa.Integer, nullable=True),
        # Notification
        sa.Column('notified', sa.Boolean, nullable=False, default=False),
        sa.Column('notified_at', sa.DateTime, nullable=True),
        # Unique constraint
        sa.UniqueConstraint('customer_id', 'badge_id', name='uq_user_badge'),
    )

    # User levels - gamification levels
    op.create_table(
        'user_levels',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', sa.String(100), nullable=False, unique=True, index=True),
        # Level info
        sa.Column('current_level', sa.Integer, nullable=False, default=1),
        sa.Column('level_name', sa.String(50), nullable=False, default='Newcomer'),
        sa.Column('total_points', sa.Integer, nullable=False, default=0),
        sa.Column('points_to_next_level', sa.Integer, nullable=False, default=100),
        # Progress
        sa.Column('features_requested', sa.Integer, nullable=False, default=0),
        sa.Column('feedback_given', sa.Integer, nullable=False, default=0),
        sa.Column('votes_cast', sa.Integer, nullable=False, default=0),
        sa.Column('comments_made', sa.Integer, nullable=False, default=0),
        sa.Column('features_delivered', sa.Integer, nullable=False, default=0),
        # Streaks
        sa.Column('current_streak_days', sa.Integer, nullable=False, default=0),
        sa.Column('longest_streak_days', sa.Integer, nullable=False, default=0),
        sa.Column('last_activity_date', sa.Date, nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True, onupdate=sa.func.now()),
    )

    # User points history - point transactions
    op.create_table(
        'user_points_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', sa.String(100), nullable=False, index=True),
        # Transaction
        sa.Column('points', sa.Integer, nullable=False),  # positive = earned, negative = spent
        sa.Column('reason', sa.String(200), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),  # feature_request, feedback, vote, badge, bonus
        sa.Column('reference_id', sa.String(100), nullable=True),  # ID of related entity
        sa.Column('reference_type', sa.String(50), nullable=True),  # feature, feedback, badge
        # Balance
        sa.Column('balance_after', sa.Integer, nullable=False),
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # ============== PERSONALIZED DASHBOARD TABLES ==============

    # Dashboard preferences
    op.create_table(
        'dashboard_preferences',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', sa.String(100), nullable=False, unique=True, index=True),
        # Layout preferences
        sa.Column('layout', sa.String(20), nullable=False, default='default'),  # default, compact, detailed
        sa.Column('widgets_order', JSONB, nullable=True),  # ordered list of widget IDs
        sa.Column('hidden_widgets', JSONB, nullable=True),  # list of hidden widget IDs
        # Content preferences
        sa.Column('show_recommendations', sa.Boolean, nullable=False, default=True),
        sa.Column('show_trending', sa.Boolean, nullable=False, default=True),
        sa.Column('show_activity_feed', sa.Boolean, nullable=False, default=True),
        sa.Column('show_badges', sa.Boolean, nullable=False, default=True),
        sa.Column('show_stats', sa.Boolean, nullable=False, default=True),
        # Notification preferences
        sa.Column('email_digest', sa.String(20), nullable=False, default='weekly'),  # none, daily, weekly, monthly
        sa.Column('notify_feature_updates', sa.Boolean, nullable=False, default=True),
        sa.Column('notify_new_badges', sa.Boolean, nullable=False, default=True),
        sa.Column('notify_level_up', sa.Boolean, nullable=False, default=True),
        # Interest areas
        sa.Column('interest_tags', JSONB, nullable=True),  # preferred feature categories
        sa.Column('watched_features', JSONB, nullable=True),  # feature IDs being watched
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True, onupdate=sa.func.now()),
    )

    # Feature recommendations - personalized suggestions
    op.create_table(
        'feature_recommendations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', sa.String(100), nullable=False, index=True),
        sa.Column('feature_request_id', sa.Integer, nullable=False, index=True),
        sa.Column('project_id', sa.Integer, nullable=True),
        # Recommendation details
        sa.Column('recommendation_type', sa.String(50), nullable=False),  # similar, trending, personalized, new
        sa.Column('score', sa.Float, nullable=False),  # 0-1 relevance score
        sa.Column('reason', sa.Text, nullable=True),  # why this was recommended
        sa.Column('source_features', JSONB, nullable=True),  # features that led to this recommendation
        # Status
        sa.Column('status', sa.String(30), nullable=False, default='active'),  # active, dismissed, voted, expired
        sa.Column('dismissed_at', sa.DateTime, nullable=True),
        sa.Column('voted_at', sa.DateTime, nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        # Unique constraint - one recommendation per feature per user
        sa.UniqueConstraint('customer_id', 'feature_request_id', name='uq_customer_feature_recommendation'),
    )

    # Create indexes
    op.create_index('ix_feature_feedback_status', 'feature_feedback', ['status'])
    op.create_index('ix_feedback_requests_status', 'feedback_requests', ['status'])
    op.create_index('ix_user_badges_earned_at', 'user_badges', ['earned_at'])
    op.create_index('ix_user_points_history_created', 'user_points_history', ['created_at'])
    op.create_index('ix_feature_recommendations_score', 'feature_recommendations', ['score'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_feature_recommendations_score')
    op.drop_index('ix_user_points_history_created')
    op.drop_index('ix_user_badges_earned_at')
    op.drop_index('ix_feedback_requests_status')
    op.drop_index('ix_feature_feedback_status')

    # Drop tables
    op.drop_table('feature_recommendations')
    op.drop_table('dashboard_preferences')
    op.drop_table('user_points_history')
    op.drop_table('user_levels')
    op.drop_table('user_badges')
    op.drop_table('badge_definitions')
    op.drop_table('feedback_requests')
    op.drop_table('feature_feedback')
