# backend/app/models/engagement.py
"""
Engagement System Models - Week 119-120

Client Portal 2.0 Phase 3: Engagement
- Feedback Loop (FeatureFeedback, FeedbackRequest)
- Gamification (BadgeDefinition, UserBadge, UserLevel, UserPointsHistory)
- Personalized Dashboard (DashboardPreferences, FeatureRecommendation)
"""

from datetime import datetime, date, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, DateTime, Date, Float,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


# ============== ENUMS ==============

class FeedbackType(str, Enum):
    GENERAL = "general"
    BUG = "bug"
    ENHANCEMENT = "enhancement"
    PRAISE = "praise"
    COMPLAINT = "complaint"


class FeedbackStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    ACTIONED = "actioned"
    ARCHIVED = "archived"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class FeedbackRequestStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    RESPONDED = "responded"
    EXPIRED = "expired"


class BadgeCategory(str, Enum):
    ENGAGEMENT = "engagement"
    FEEDBACK = "feedback"
    CONTRIBUTION = "contribution"
    MILESTONE = "milestone"
    SPECIAL = "special"


class BadgeTier(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


class CriteriaType(str, Enum):
    COUNT = "count"
    THRESHOLD = "threshold"
    ACTION = "action"
    STREAK = "streak"
    CUSTOM = "custom"


class ActionType(str, Enum):
    FEATURE_REQUEST = "feature_request"
    FEEDBACK = "feedback"
    VOTE = "vote"
    COMMENT = "comment"
    BADGE = "badge"
    BONUS = "bonus"
    LEVEL_UP = "level_up"


class RecommendationType(str, Enum):
    SIMILAR = "similar"
    TRENDING = "trending"
    PERSONALIZED = "personalized"
    NEW = "new"
    POPULAR = "popular"


class RecommendationStatus(str, Enum):
    ACTIVE = "active"
    DISMISSED = "dismissed"
    VOTED = "voted"
    EXPIRED = "expired"


# ============== LEVEL DEFINITIONS ==============

LEVEL_DEFINITIONS = {
    1: {"name": "Newcomer", "points_required": 0, "color": "#9CA3AF"},
    2: {"name": "Contributor", "points_required": 100, "color": "#10B981"},
    3: {"name": "Active Member", "points_required": 250, "color": "#3B82F6"},
    4: {"name": "Valued Member", "points_required": 500, "color": "#8B5CF6"},
    5: {"name": "Champion", "points_required": 1000, "color": "#F59E0B"},
    6: {"name": "Expert", "points_required": 2000, "color": "#EF4444"},
    7: {"name": "Ambassador", "points_required": 5000, "color": "#EC4899"},
    8: {"name": "Legend", "points_required": 10000, "color": "#6366F1"},
}


# ============== FEEDBACK LOOP MODELS ==============

class FeatureFeedback(Base):
    """Post-release feedback from customers."""
    __tablename__ = "feature_feedback"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    feature_request_id = Column(Integer, nullable=False, index=True)
    project_id = Column(Integer, nullable=True, index=True)
    customer_id = Column(String(100), nullable=False, index=True)

    # Feedback content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    satisfaction_score = Column(Integer, nullable=True)  # 1-10 NPS-style
    meets_expectations = Column(Boolean, nullable=True)
    would_recommend = Column(Boolean, nullable=True)
    feedback_text = Column(Text, nullable=True)
    improvement_suggestions = Column(Text, nullable=True)

    # Categorization
    feedback_type = Column(String(50), nullable=False, default=FeedbackType.GENERAL.value)
    sentiment = Column(String(20), nullable=True)
    tags = Column(JSONB, nullable=True, default=[])

    # Status
    status = Column(String(30), nullable=False, default=FeedbackStatus.PENDING.value)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    action_taken = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc))

    def is_positive(self) -> bool:
        """Check if feedback is positive."""
        return self.rating >= 4 or self.sentiment == Sentiment.POSITIVE.value

    def calculate_nps_category(self) -> str:
        """Calculate NPS category from satisfaction score."""
        if self.satisfaction_score is None:
            return "unknown"
        if self.satisfaction_score >= 9:
            return "promoter"
        elif self.satisfaction_score >= 7:
            return "passive"
        else:
            return "detractor"


class FeedbackRequest(Base):
    """Proactive feedback solicitation."""
    __tablename__ = "feedback_requests"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    feature_request_id = Column(Integer, nullable=False, index=True)
    project_id = Column(Integer, nullable=True, index=True)
    customer_id = Column(String(100), nullable=False, index=True)

    # Request details
    request_type = Column(String(50), nullable=False, default="post_release")
    trigger_event = Column(String(100), nullable=True)
    message = Column(Text, nullable=True)

    # Status
    status = Column(String(30), nullable=False, default=FeedbackRequestStatus.PENDING.value)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Link to response
    feedback_id = Column(PGUUID(as_uuid=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def is_expired(self) -> bool:
        """Check if request has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


# ============== GAMIFICATION MODELS ==============

class BadgeDefinition(Base):
    """Available badges that can be earned."""
    __tablename__ = "badge_definitions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)
    color = Column(String(20), nullable=True)

    # Category
    category = Column(String(50), nullable=False, default=BadgeCategory.ENGAGEMENT.value)
    tier = Column(String(20), nullable=False, default=BadgeTier.BRONZE.value)

    # Earning criteria
    criteria_type = Column(String(50), nullable=False)
    criteria_target = Column(String(100), nullable=True)
    criteria_value = Column(Integer, nullable=True)
    criteria_config = Column(JSONB, nullable=True)

    # Points
    points_awarded = Column(Integer, nullable=False, default=10)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_secret = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def check_criteria(self, user_stats: Dict[str, Any]) -> bool:
        """Check if user meets badge criteria."""
        if self.criteria_type == CriteriaType.COUNT.value:
            current = user_stats.get(self.criteria_target, 0)
            return current >= (self.criteria_value or 0)
        elif self.criteria_type == CriteriaType.THRESHOLD.value:
            current = user_stats.get(self.criteria_target, 0)
            return current >= (self.criteria_value or 0)
        elif self.criteria_type == CriteriaType.STREAK.value:
            current_streak = user_stats.get("current_streak_days", 0)
            return current_streak >= (self.criteria_value or 0)
        return False


class UserBadge(Base):
    """Badges earned by users."""
    __tablename__ = "user_badges"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(String(100), nullable=False, index=True)
    badge_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Earning details
    earned_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    earned_for = Column(Text, nullable=True)
    progress_snapshot = Column(JSONB, nullable=True)

    # Display
    is_displayed = Column(Boolean, nullable=False, default=True)
    display_order = Column(Integer, nullable=True)

    # Notification
    notified = Column(Boolean, nullable=False, default=False)
    notified_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint('customer_id', 'badge_id', name='uq_user_badge'),
    )


class UserLevel(Base):
    """User gamification levels and stats."""
    __tablename__ = "user_levels"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(String(100), nullable=False, unique=True, index=True)

    # Level info
    current_level = Column(Integer, nullable=False, default=1)
    level_name = Column(String(50), nullable=False, default="Newcomer")
    total_points = Column(Integer, nullable=False, default=0)
    points_to_next_level = Column(Integer, nullable=False, default=100)

    # Activity counts
    features_requested = Column(Integer, nullable=False, default=0)
    feedback_given = Column(Integer, nullable=False, default=0)
    votes_cast = Column(Integer, nullable=False, default=0)
    comments_made = Column(Integer, nullable=False, default=0)
    features_delivered = Column(Integer, nullable=False, default=0)

    # Streaks
    current_streak_days = Column(Integer, nullable=False, default=0)
    longest_streak_days = Column(Integer, nullable=False, default=0)
    last_activity_date = Column(Date, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc))

    def add_points(self, points: int) -> bool:
        """Add points and check for level up."""
        self.total_points += points
        return self._check_level_up()

    def _check_level_up(self) -> bool:
        """Check and apply level up if applicable."""
        leveled_up = False
        for level, info in sorted(LEVEL_DEFINITIONS.items(), reverse=True):
            if self.total_points >= info["points_required"] and level > self.current_level:
                self.current_level = level
                self.level_name = info["name"]
                leveled_up = True
                break

        # Calculate points to next level
        next_level = self.current_level + 1
        if next_level in LEVEL_DEFINITIONS:
            self.points_to_next_level = LEVEL_DEFINITIONS[next_level]["points_required"] - self.total_points
        else:
            self.points_to_next_level = 0  # Max level

        return leveled_up

    def update_streak(self) -> None:
        """Update activity streak."""
        today = date.today()
        if self.last_activity_date is None:
            self.current_streak_days = 1
        elif self.last_activity_date == today:
            pass  # Already active today
        elif (today - self.last_activity_date).days == 1:
            self.current_streak_days += 1
        else:
            self.current_streak_days = 1  # Streak broken

        self.last_activity_date = today
        if self.current_streak_days > self.longest_streak_days:
            self.longest_streak_days = self.current_streak_days

    def get_stats(self) -> Dict[str, Any]:
        """Get user stats for badge checking."""
        return {
            "features_requested": self.features_requested,
            "feedback_given": self.feedback_given,
            "votes_cast": self.votes_cast,
            "comments_made": self.comments_made,
            "features_delivered": self.features_delivered,
            "current_streak_days": self.current_streak_days,
            "longest_streak_days": self.longest_streak_days,
            "total_points": self.total_points,
            "current_level": self.current_level,
        }


class UserPointsHistory(Base):
    """Point transaction history."""
    __tablename__ = "user_points_history"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(String(100), nullable=False, index=True)

    # Transaction
    points = Column(Integer, nullable=False)
    reason = Column(String(200), nullable=False)
    action_type = Column(String(50), nullable=False)
    reference_id = Column(String(100), nullable=True)
    reference_type = Column(String(50), nullable=True)

    # Balance
    balance_after = Column(Integer, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


# ============== PERSONALIZED DASHBOARD MODELS ==============

class DashboardPreferences(Base):
    """User dashboard preferences."""
    __tablename__ = "dashboard_preferences"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(String(100), nullable=False, unique=True, index=True)

    # Layout preferences
    layout = Column(String(20), nullable=False, default="default")
    widgets_order = Column(JSONB, nullable=True)
    hidden_widgets = Column(JSONB, nullable=True)

    # Content preferences
    show_recommendations = Column(Boolean, nullable=False, default=True)
    show_trending = Column(Boolean, nullable=False, default=True)
    show_activity_feed = Column(Boolean, nullable=False, default=True)
    show_badges = Column(Boolean, nullable=False, default=True)
    show_stats = Column(Boolean, nullable=False, default=True)

    # Notification preferences
    email_digest = Column(String(20), nullable=False, default="weekly")
    notify_feature_updates = Column(Boolean, nullable=False, default=True)
    notify_new_badges = Column(Boolean, nullable=False, default=True)
    notify_level_up = Column(Boolean, nullable=False, default=True)

    def __init__(self, **kwargs):
        # Apply Python defaults for non-persisted instantiation
        kwargs.setdefault('layout', 'default')
        kwargs.setdefault('show_recommendations', True)
        kwargs.setdefault('show_trending', True)
        kwargs.setdefault('show_activity_feed', True)
        kwargs.setdefault('show_badges', True)
        kwargs.setdefault('show_stats', True)
        kwargs.setdefault('email_digest', 'weekly')
        kwargs.setdefault('notify_feature_updates', True)
        kwargs.setdefault('notify_new_badges', True)
        kwargs.setdefault('notify_level_up', True)
        super().__init__(**kwargs)

    # Interest areas
    interest_tags = Column(JSONB, nullable=True)
    watched_features = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc))


class FeatureRecommendation(Base):
    """Personalized feature recommendations."""
    __tablename__ = "feature_recommendations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(String(100), nullable=False, index=True)
    feature_request_id = Column(Integer, nullable=False, index=True)
    project_id = Column(Integer, nullable=True)

    # Recommendation details
    recommendation_type = Column(String(50), nullable=False)
    score = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)
    source_features = Column(JSONB, nullable=True)

    # Status
    status = Column(String(30), nullable=False, default=RecommendationStatus.ACTIVE.value)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)
    voted_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint('customer_id', 'feature_request_id', name='uq_customer_feature_recommendation'),
    )

    def is_expired(self) -> bool:
        """Check if recommendation has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


# ============== POINT VALUES ==============

POINT_VALUES = {
    ActionType.FEATURE_REQUEST.value: 10,
    ActionType.FEEDBACK.value: 15,
    ActionType.VOTE.value: 2,
    ActionType.COMMENT.value: 5,
    ActionType.BADGE.value: 0,  # Points from badge itself
    ActionType.BONUS.value: 0,  # Variable
    ActionType.LEVEL_UP.value: 25,
}


# ============== DEFAULT BADGES ==============

DEFAULT_BADGES = [
    # Engagement badges
    {"name": "first_request", "display_name": "First Request", "description": "Submitted your first feature request", "category": "engagement", "tier": "bronze", "criteria_type": "count", "criteria_target": "features_requested", "criteria_value": 1, "points_awarded": 25, "icon": "star"},
    {"name": "active_requester", "display_name": "Active Requester", "description": "Submitted 10 feature requests", "category": "engagement", "tier": "silver", "criteria_type": "count", "criteria_target": "features_requested", "criteria_value": 10, "points_awarded": 50, "icon": "stars"},
    {"name": "power_requester", "display_name": "Power Requester", "description": "Submitted 50 feature requests", "category": "engagement", "tier": "gold", "criteria_type": "count", "criteria_target": "features_requested", "criteria_value": 50, "points_awarded": 100, "icon": "crown"},

    # Feedback badges
    {"name": "first_feedback", "display_name": "Voice Heard", "description": "Gave your first feedback", "category": "feedback", "tier": "bronze", "criteria_type": "count", "criteria_target": "feedback_given", "criteria_value": 1, "points_awarded": 20, "icon": "message"},
    {"name": "feedback_champion", "display_name": "Feedback Champion", "description": "Gave feedback on 10 features", "category": "feedback", "tier": "silver", "criteria_type": "count", "criteria_target": "feedback_given", "criteria_value": 10, "points_awarded": 75, "icon": "megaphone"},

    # Voting badges
    {"name": "first_vote", "display_name": "Democracy!", "description": "Cast your first vote", "category": "contribution", "tier": "bronze", "criteria_type": "count", "criteria_target": "votes_cast", "criteria_value": 1, "points_awarded": 10, "icon": "check"},
    {"name": "active_voter", "display_name": "Active Voter", "description": "Cast 25 votes", "category": "contribution", "tier": "silver", "criteria_type": "count", "criteria_target": "votes_cast", "criteria_value": 25, "points_awarded": 40, "icon": "ballot"},

    # Streak badges
    {"name": "week_streak", "display_name": "Week Warrior", "description": "7 day activity streak", "category": "milestone", "tier": "bronze", "criteria_type": "streak", "criteria_target": "current_streak_days", "criteria_value": 7, "points_awarded": 30, "icon": "fire"},
    {"name": "month_streak", "display_name": "Monthly Master", "description": "30 day activity streak", "category": "milestone", "tier": "gold", "criteria_type": "streak", "criteria_target": "current_streak_days", "criteria_value": 30, "points_awarded": 150, "icon": "flame"},

    # Special badges
    {"name": "early_adopter", "display_name": "Early Adopter", "description": "One of the first 100 users", "category": "special", "tier": "platinum", "criteria_type": "custom", "criteria_value": 100, "points_awarded": 200, "icon": "rocket", "is_secret": True},
]
