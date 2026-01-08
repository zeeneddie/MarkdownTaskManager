# backend/app/models/chatbot_journey.py
"""
Chatbot and Journey Analytics Models - Week 121

Client Portal 2.0 Phase 4: Advanced Features
- Conversational Interface (ChatSession, ChatMessage)
- Customer Journey Analytics (JourneyEvent, JourneyFunnel, JourneyFunnelSnapshot)
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, DateTime, Float,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


# ============== ENUMS ==============

class ChatSessionStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatContentType(str, Enum):
    TEXT = "text"
    ACTION = "action"
    CARD = "card"
    SUGGESTION = "suggestion"


class ChatIntent(str, Enum):
    STATUS_QUERY = "status_query"
    ETA_QUERY = "eta_query"
    NEW_REQUEST = "new_request"
    FEATURE_SEARCH = "feature_search"
    HELP = "help"
    FEEDBACK = "feedback"
    VOTING = "voting"
    GENERAL = "general"
    ESCALATION = "escalation"


class ChatAgent(str, Enum):
    PETER = "peter"  # Product Owner - Classification, understanding
    DIANA = "diana"  # Documentation - Message generation
    FELIX = "felix"  # Architect - Technical questions
    ELIZA = "eliza"  # Estimation - ETA questions
    PAUL = "paul"    # Project Lead - Sprint questions
    TESSA = "tessa"  # Test Engineer - Test result questions


class ChatActionType(str, Enum):
    START_REQUEST = "start_request"
    SHOW_STATUS = "show_status"
    SHOW_ETA = "show_eta"
    REDIRECT = "redirect"
    VOTE = "vote"
    FEEDBACK = "feedback"
    ESCALATE = "escalate"


class EventCategory(str, Enum):
    NAVIGATION = "navigation"
    INTERACTION = "interaction"
    CONVERSION = "conversion"
    MILESTONE = "milestone"
    ERROR = "error"


class DeviceType(str, Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    UNKNOWN = "unknown"


# ============== INTENT PATTERNS ==============

INTENT_PATTERNS = {
    ChatIntent.STATUS_QUERY.value: [
        "status", "waar staat", "hoe gaat het met", "stand van zaken",
        "voortgang", "progress", "update", "wat is de status"
    ],
    ChatIntent.ETA_QUERY.value: [
        "wanneer", "when", "hoe lang", "how long", "eta", "klaar",
        "deadline", "tijdlijn", "timeline", "expected"
    ],
    ChatIntent.NEW_REQUEST.value: [
        "nieuw", "new", "aanvragen", "request", "toevoegen", "add",
        "ik wil", "ik zou graag", "i want", "i would like"
    ],
    ChatIntent.FEATURE_SEARCH.value: [
        "zoek", "search", "vind", "find", "waar is", "where is"
    ],
    ChatIntent.HELP.value: [
        "help", "hulp", "hoe", "how", "wat kan", "what can"
    ],
    ChatIntent.FEEDBACK.value: [
        "feedback", "review", "beoordeling", "rating", "klacht", "complaint"
    ],
    ChatIntent.VOTING.value: [
        "stem", "vote", "upvote", "support", "ondersteunen"
    ]
}


# ============== CHAT MODELS ==============

class ChatSession(Base):
    """Chat session with the portal chatbot."""
    __tablename__ = "chat_sessions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(String(100), nullable=False, index=True)
    project_id = Column(Integer, nullable=True, index=True)

    # Session info
    title = Column(String(200), nullable=True)
    status = Column(String(30), nullable=False, default=ChatSessionStatus.ACTIVE.value)

    # Agent assignment
    primary_agent = Column(String(50), nullable=False, default=ChatAgent.PETER.value)
    agents_involved = Column(JSONB, nullable=True, default=[])

    # Context
    context = Column(JSONB, nullable=True)
    feature_ids_mentioned = Column(JSONB, nullable=True, default=[])

    # Stats
    message_count = Column(Integer, nullable=False, default=0)
    resolved = Column(Boolean, nullable=False, default=False)
    satisfaction_rating = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
    last_message_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def add_message(self) -> None:
        """Increment message count and update last message time."""
        self.message_count += 1
        self.last_message_at = datetime.utcnow()

    def add_agent(self, agent: str) -> None:
        """Add agent to the list of involved agents."""
        if self.agents_involved is None:
            self.agents_involved = []
        if agent not in self.agents_involved:
            self.agents_involved = self.agents_involved + [agent]

    def add_feature_mention(self, feature_id: int) -> None:
        """Add feature ID to mentioned features."""
        if self.feature_ids_mentioned is None:
            self.feature_ids_mentioned = []
        if feature_id not in self.feature_ids_mentioned:
            self.feature_ids_mentioned = self.feature_ids_mentioned + [feature_id]

    def close(self, rating: Optional[int] = None) -> None:
        """Close the session."""
        self.status = ChatSessionStatus.CLOSED.value
        self.closed_at = datetime.utcnow()
        if rating:
            self.satisfaction_rating = rating

    def is_active(self) -> bool:
        """Check if session is active."""
        return self.status == ChatSessionStatus.ACTIVE.value


class ChatMessage(Base):
    """Individual message in a chat session."""
    __tablename__ = "chat_messages"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(100), nullable=False, index=True)

    # Message content
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(30), nullable=False, default=ChatContentType.TEXT.value)

    # Agent info (for assistant messages)
    agent = Column(String(50), nullable=True)
    agent_reasoning = Column(Text, nullable=True)

    # Intent detection
    detected_intent = Column(String(50), nullable=True)
    intent_confidence = Column(Float, nullable=True)
    entities = Column(JSONB, nullable=True)

    # Actions
    action_type = Column(String(50), nullable=True)
    action_data = Column(JSONB, nullable=True)
    action_executed = Column(Boolean, nullable=False, default=False)

    # Feedback
    helpful = Column(Boolean, nullable=True)
    feedback_text = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def is_from_user(self) -> bool:
        """Check if message is from user."""
        return self.role == ChatRole.USER.value

    def is_from_assistant(self) -> bool:
        """Check if message is from assistant."""
        return self.role == ChatRole.ASSISTANT.value

    def has_action(self) -> bool:
        """Check if message has an action."""
        return self.action_type is not None

    def mark_helpful(self, helpful: bool, feedback: Optional[str] = None) -> None:
        """Mark message as helpful or not."""
        self.helpful = helpful
        if feedback:
            self.feedback_text = feedback


# ============== JOURNEY ANALYTICS MODELS ==============

class JourneyEvent(Base):
    """Individual event in customer journey."""
    __tablename__ = "journey_events"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(String(100), nullable=False, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    project_id = Column(Integer, nullable=True, index=True)

    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    event_category = Column(String(30), nullable=False, default=EventCategory.INTERACTION.value)
    event_data = Column(JSONB, nullable=True)

    # Page/context
    page_path = Column(String(500), nullable=True)
    referrer = Column(String(500), nullable=True)

    # Feature context
    feature_id = Column(Integer, nullable=True, index=True)
    feature_status = Column(String(30), nullable=True)

    # User agent / device
    device_type = Column(String(20), nullable=True)
    browser = Column(String(50), nullable=True)

    # Timestamps
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())

    def is_conversion_event(self) -> bool:
        """Check if this is a conversion event."""
        return self.event_category == EventCategory.CONVERSION.value

    def is_milestone(self) -> bool:
        """Check if this is a milestone event."""
        return self.event_category == EventCategory.MILESTONE.value


class JourneyFunnel(Base):
    """Funnel definition for journey analysis."""
    __tablename__ = "journey_funnels"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Funnel definition
    steps = Column(JSONB, nullable=False)
    goal_event = Column(String(50), nullable=False)

    # Analysis window
    window_days = Column(Integer, nullable=False, default=30)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, nullable=True, onupdate=lambda: datetime.utcnow())

    # Relationships
    snapshots = relationship("JourneyFunnelSnapshot", back_populates="funnel", cascade="all, delete-orphan")

    def get_step_count(self) -> int:
        """Get number of steps in funnel."""
        return len(self.steps) if self.steps else 0

    def get_step_names(self) -> List[str]:
        """Get ordered list of step names."""
        if not self.steps:
            return []
        return [step.get("name", f"step_{i}") for i, step in enumerate(self.steps)]


class JourneyFunnelSnapshot(Base):
    """Periodic snapshot of funnel analysis results."""
    __tablename__ = "journey_funnel_snapshots"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    funnel_id = Column(PGUUID(as_uuid=True), ForeignKey("journey_funnels.id", ondelete="CASCADE"), nullable=False, index=True)

    # Analysis period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Results
    step_counts = Column(JSONB, nullable=False)
    conversion_rates = Column(JSONB, nullable=False)
    drop_off_rates = Column(JSONB, nullable=False)
    overall_conversion = Column(Float, nullable=False)
    avg_time_to_convert = Column(Float, nullable=True)

    # Insights
    bottleneck_step = Column(String(100), nullable=True)
    insights = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())

    # Relationships
    funnel = relationship("JourneyFunnel", back_populates="snapshots")

    def get_biggest_drop(self) -> Optional[str]:
        """Get step with biggest drop-off."""
        if not self.drop_off_rates:
            return None
        max_drop = 0
        max_step = None
        for step, rate in self.drop_off_rates.items():
            if rate > max_drop:
                max_drop = rate
                max_step = step
        return max_step


# ============== EVENT TYPE CONSTANTS ==============

EVENT_TYPES = {
    # Navigation events
    "portal_visit": {"category": "navigation", "description": "User visited portal"},
    "page_view": {"category": "navigation", "description": "User viewed a page"},
    "dashboard_view": {"category": "navigation", "description": "User viewed dashboard"},

    # Feature interaction events
    "feature_view": {"category": "interaction", "description": "User viewed feature details"},
    "feature_create_start": {"category": "interaction", "description": "User started creating feature"},
    "feature_create_submit": {"category": "conversion", "description": "User submitted feature request"},
    "feature_vote": {"category": "interaction", "description": "User voted on feature"},
    "feature_comment": {"category": "interaction", "description": "User commented on feature"},

    # Feature lifecycle events
    "feature_submitted": {"category": "milestone", "description": "Feature was submitted"},
    "feature_analyzed": {"category": "milestone", "description": "Feature was analyzed"},
    "feature_sprint_assigned": {"category": "milestone", "description": "Feature assigned to sprint"},
    "feature_in_development": {"category": "milestone", "description": "Feature in development"},
    "feature_testing": {"category": "milestone", "description": "Feature being tested"},
    "feature_released": {"category": "milestone", "description": "Feature was released"},

    # Feedback events
    "feedback_requested": {"category": "interaction", "description": "Feedback was requested"},
    "feedback_opened": {"category": "interaction", "description": "Feedback form was opened"},
    "feedback_submitted": {"category": "conversion", "description": "Feedback was submitted"},

    # Chatbot events
    "chatbot_opened": {"category": "interaction", "description": "Chatbot was opened"},
    "chatbot_message_sent": {"category": "interaction", "description": "User sent chat message"},
    "chatbot_action_taken": {"category": "interaction", "description": "Chatbot action was executed"},
    "chatbot_closed": {"category": "interaction", "description": "Chatbot was closed"},

    # Session events
    "session_start": {"category": "navigation", "description": "New session started"},
    "session_end": {"category": "navigation", "description": "Session ended"},

    # Gamification events
    "badge_earned": {"category": "milestone", "description": "User earned a badge"},
    "level_up": {"category": "milestone", "description": "User leveled up"},

    # Error events
    "error": {"category": "error", "description": "An error occurred"},
    "validation_error": {"category": "error", "description": "Form validation failed"},
}


# ============== AGENT RESPONSE TEMPLATES ==============

AGENT_TEMPLATES = {
    ChatAgent.PETER.value: {
        "greeting": "Hoi! Ik ben Peter, je productmanager. Hoe kan ik je helpen?",
        "status_found": "Ik heb je feature '{title}' gevonden! {status_message}",
        "status_not_found": "Hmm, ik kon geen feature vinden die daarop lijkt. Kun je wat specifieker zijn?",
        "new_request_start": "Geweldig dat je een nieuw idee hebt! Laten we dat vastleggen.",
        "handoff_diana": "Diana neemt het nu over om je vraag te beantwoorden.",
    },
    ChatAgent.DIANA.value: {
        "greeting": "Hallo! Ik ben Diana, ik help je met informatie en documentatie.",
        "status_update": "{feature_title} is nu in de '{status}' fase. {additional_info}",
        "eta_response": "Op basis van onze huidige planning verwacht ik dat '{title}' rond {eta} klaar is.",
        "clarification": "Kun je me wat meer vertellen over wat je precies zoekt?",
    },
    ChatAgent.ELIZA.value: {
        "eta_calculation": "Ik heb de inschatting gemaakt. {details}",
        "confidence": "Mijn vertrouwen in deze inschatting is {confidence}%.",
    },
    ChatAgent.FELIX.value: {
        "technical_answer": "Vanuit technisch perspectief: {answer}",
        "impact_analysis": "Deze feature zou impact hebben op: {components}",
    },
}
