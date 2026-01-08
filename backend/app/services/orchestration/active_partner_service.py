"""
Active Partner Service - Week 111

Pattern: Active Partner (from Gregor Riegler's Augmented Coding Pattern Language)

Purpose: Maintain effective human-AI collaboration where both parties
actively contribute to problem-solving. The human isn't just a reviewer
but an active partner in the decision-making process.

Key Concepts:
- Handoff Points: Explicit moments to involve the human
- Decision Types: Categorize decisions by who should make them
- Collaboration Mode: Track the current mode of interaction
- Feedback Loop: Continuous improvement through human feedback

Usage:
    service = ActivePartnerService()

    # Start a collaboration session
    session = service.start_session(
        task="Implement user authentication",
        user_id="developer-123"
    )

    # Register a decision point
    decision = service.request_decision(
        session_id=session.id,
        question="Should we use JWT or session-based auth?",
        options=["JWT", "Session", "OAuth2"],
        context={"requirements": "stateless API"}
    )

    # Record human decision
    service.record_decision(decision.id, selected_option="JWT", reasoning="API needs to scale")

    # Generate collaboration report
    report = service.generate_report(session.id)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """Types of decisions based on who should make them."""
    HUMAN_REQUIRED = "human_required"      # Human must decide
    AI_SUGGESTED = "ai_suggested"          # AI suggests, human confirms
    AI_AUTONOMOUS = "ai_autonomous"        # AI decides, human can override
    COLLABORATIVE = "collaborative"         # Both contribute to decision


class CollaborationMode(Enum):
    """Current mode of human-AI interaction."""
    ACTIVE = "active"          # Human actively involved
    OBSERVING = "observing"    # Human watching, AI leading
    REVIEWING = "reviewing"    # Human reviewing AI work
    PAUSED = "paused"          # Waiting for human input
    AUTONOMOUS = "autonomous"  # AI working independently


class HandoffReason(Enum):
    """Reasons for handing off to human."""
    DECISION_REQUIRED = "decision_required"        # Need human judgment
    UNCERTAINTY = "uncertainty"                    # AI unsure about approach
    RISK = "risk"                                  # High-risk change
    POLICY = "policy"                              # Business/policy decision
    QUALITY_GATE = "quality_gate"                  # Checkpoint reached
    CLARIFICATION = "clarification"                # Need more information
    APPROVAL = "approval"                          # Need explicit approval
    LEARNING = "learning"                          # AI wants to learn from human


@dataclass
class DecisionOption:
    """An option in a decision point."""
    label: str
    description: str
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    ai_confidence: float = 0.5  # AI's confidence this is the right choice


@dataclass
class DecisionPoint:
    """A point where human input is needed."""
    id: UUID
    session_id: UUID
    question: str
    decision_type: DecisionType
    handoff_reason: HandoffReason
    options: List[DecisionOption]
    context: Dict[str, Any]
    ai_recommendation: Optional[str] = None
    ai_reasoning: Optional[str] = None
    selected_option: Optional[str] = None
    human_reasoning: Optional[str] = None
    status: str = "pending"  # pending, decided, skipped
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    decided_at: Optional[datetime] = None


@dataclass
class CollaborationEvent:
    """Event in the collaboration timeline."""
    id: UUID
    session_id: UUID
    event_type: str  # decision, handoff, feedback, mode_change
    description: str
    actor: str  # human, ai
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.utcnow())


@dataclass
class CollaborationSession:
    """Session tracking human-AI collaboration."""
    id: UUID
    task: str
    user_id: str
    mode: CollaborationMode
    decision_points: List[DecisionPoint]
    events: List[CollaborationEvent]
    feedback: List[Dict[str, Any]]
    created_at: datetime
    last_activity: datetime
    total_decisions: int = 0
    human_decisions: int = 0
    ai_decisions: int = 0
    overrides: int = 0  # Times human overrode AI suggestion


@dataclass
class CollaborationReport:
    """Report on collaboration effectiveness."""
    session_id: UUID
    task: str
    duration_minutes: float
    total_decisions: int
    human_decisions: int
    ai_decisions: int
    ai_recommendation_acceptance_rate: float
    override_rate: float
    pending_decisions: int
    collaboration_score: float  # 0.0-1.0
    recommendations: List[str]
    generated_at: datetime = field(default_factory=lambda: datetime.utcnow())


class ActivePartnerService:
    """
    Week 111: Active Partner Service

    Maintains effective human-AI collaboration where both parties
    actively contribute to problem-solving.
    """

    # Decision types that require human input
    HUMAN_REQUIRED_REASONS = {
        HandoffReason.DECISION_REQUIRED,
        HandoffReason.POLICY,
        HandoffReason.APPROVAL,
        HandoffReason.RISK,
    }

    def __init__(self):
        self._sessions: Dict[UUID, CollaborationSession] = {}
        self._decision_points: Dict[UUID, DecisionPoint] = {}
        self._callbacks: Dict[str, List[Callable]] = {
            "decision_required": [],
            "mode_change": [],
            "session_complete": [],
        }

    def start_session(
        self,
        task: str,
        user_id: str,
        initial_mode: CollaborationMode = CollaborationMode.ACTIVE,
    ) -> CollaborationSession:
        """
        Start a new collaboration session.

        Args:
            task: The task being worked on
            user_id: ID of the human partner
            initial_mode: Starting collaboration mode

        Returns:
            CollaborationSession for tracking
        """
        session = CollaborationSession(
            id=uuid4(),
            task=task,
            user_id=user_id,
            mode=initial_mode,
            decision_points=[],
            events=[],
            feedback=[],
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
        )
        self._sessions[session.id] = session

        # Record session start event
        self._record_event(
            session.id,
            "session_start",
            f"Started collaboration on: {task[:50]}...",
            "ai",
            {"initial_mode": initial_mode.value}
        )

        logger.info(f"Started collaboration session {session.id} for user {user_id}")
        return session

    def request_decision(
        self,
        session_id: UUID,
        question: str,
        options: List[str | DecisionOption],
        handoff_reason: HandoffReason = HandoffReason.DECISION_REQUIRED,
        context: Optional[Dict[str, Any]] = None,
        ai_recommendation: Optional[str] = None,
        ai_reasoning: Optional[str] = None,
    ) -> DecisionPoint:
        """
        Request a decision from the human partner.

        Args:
            session_id: Session to request decision in
            question: The question to answer
            options: List of options (strings or DecisionOption objects)
            handoff_reason: Why human input is needed
            context: Additional context for the decision
            ai_recommendation: AI's recommended option
            ai_reasoning: AI's reasoning for recommendation

        Returns:
            DecisionPoint for tracking the decision
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Convert string options to DecisionOption objects
        option_objects = []
        for opt in options:
            if isinstance(opt, str):
                option_objects.append(DecisionOption(label=opt, description=opt))
            else:
                option_objects.append(opt)

        # Determine decision type
        decision_type = self._determine_decision_type(handoff_reason, ai_recommendation)

        decision = DecisionPoint(
            id=uuid4(),
            session_id=session_id,
            question=question,
            decision_type=decision_type,
            handoff_reason=handoff_reason,
            options=option_objects,
            context=context or {},
            ai_recommendation=ai_recommendation,
            ai_reasoning=ai_reasoning,
        )

        self._decision_points[decision.id] = decision
        session.decision_points.append(decision)
        session.total_decisions += 1
        session.last_activity = datetime.utcnow()

        # Change mode to paused if human decision required
        if handoff_reason in self.HUMAN_REQUIRED_REASONS:
            self._change_mode(session, CollaborationMode.PAUSED)

        # Record event
        self._record_event(
            session_id,
            "decision_requested",
            f"Decision requested: {question[:50]}...",
            "ai",
            {"decision_id": str(decision.id), "reason": handoff_reason.value}
        )

        # Trigger callbacks
        self._trigger_callback("decision_required", decision)

        logger.debug(f"Decision requested in session {session_id}: {question[:30]}...")
        return decision

    def record_decision(
        self,
        decision_id: UUID,
        selected_option: str,
        reasoning: Optional[str] = None,
    ) -> DecisionPoint:
        """
        Record a human decision.

        Args:
            decision_id: The decision point to update
            selected_option: The option selected by human
            reasoning: Human's reasoning for the decision

        Returns:
            Updated DecisionPoint
        """
        decision = self._decision_points.get(decision_id)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")

        decision.selected_option = selected_option
        decision.human_reasoning = reasoning
        decision.status = "decided"
        decision.decided_at = datetime.utcnow()

        # Update session stats
        session = self._sessions.get(decision.session_id)
        if session:
            session.human_decisions += 1
            session.last_activity = datetime.utcnow()

            # Check if human overrode AI recommendation
            if decision.ai_recommendation and selected_option != decision.ai_recommendation:
                session.overrides += 1

            # Resume from paused state
            if session.mode == CollaborationMode.PAUSED:
                self._change_mode(session, CollaborationMode.ACTIVE)

        # Record event
        self._record_event(
            decision.session_id,
            "decision_made",
            f"Decision made: {selected_option}",
            "human",
            {
                "decision_id": str(decision_id),
                "selected": selected_option,
                "was_override": decision.ai_recommendation != selected_option if decision.ai_recommendation else False
            }
        )

        logger.debug(f"Decision {decision_id} recorded: {selected_option}")
        return decision

    def record_ai_decision(
        self,
        session_id: UUID,
        decision_description: str,
        reasoning: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record an AI autonomous decision (for transparency).

        Args:
            session_id: Session the decision was made in
            decision_description: What was decided
            reasoning: Why the AI made this decision
            context: Additional context
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.ai_decisions += 1
        session.last_activity = datetime.utcnow()

        self._record_event(
            session_id,
            "ai_decision",
            decision_description,
            "ai",
            {"reasoning": reasoning, **(context or {})}
        )

    def provide_feedback(
        self,
        session_id: UUID,
        feedback_type: str,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record human feedback on AI work.

        Args:
            session_id: Session to provide feedback for
            feedback_type: Type of feedback (positive, negative, suggestion, correction)
            content: The feedback content
            context: Additional context
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        feedback = {
            "type": feedback_type,
            "content": content,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        session.feedback.append(feedback)
        session.last_activity = datetime.utcnow()

        self._record_event(
            session_id,
            "feedback",
            f"Feedback provided: {feedback_type}",
            "human",
            feedback
        )

    def change_mode(
        self,
        session_id: UUID,
        new_mode: CollaborationMode,
        reason: Optional[str] = None,
    ) -> None:
        """
        Change the collaboration mode.

        Args:
            session_id: Session to change mode for
            new_mode: The new mode
            reason: Reason for the change
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        self._change_mode(session, new_mode, reason)

    def generate_report(self, session_id: UUID) -> CollaborationReport:
        """
        Generate a collaboration effectiveness report.

        Args:
            session_id: Session to report on

        Returns:
            CollaborationReport with analysis
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Calculate metrics
        duration = (datetime.utcnow() - session.created_at).total_seconds() / 60

        # AI recommendation acceptance rate
        decisions_with_rec = [d for d in session.decision_points
                             if d.ai_recommendation and d.status == "decided"]
        if decisions_with_rec:
            accepted = sum(1 for d in decisions_with_rec
                         if d.selected_option == d.ai_recommendation)
            acceptance_rate = accepted / len(decisions_with_rec)
        else:
            acceptance_rate = 1.0

        # Override rate
        override_rate = session.overrides / session.human_decisions if session.human_decisions > 0 else 0.0

        # Pending decisions
        pending = len([d for d in session.decision_points if d.status == "pending"])

        # Collaboration score (higher is better)
        # Based on: balanced decisions, low override rate, feedback provided
        balance_score = min(session.human_decisions, session.ai_decisions) / max(
            session.human_decisions + session.ai_decisions, 1) * 2  # Max 1.0
        feedback_score = min(len(session.feedback) / 5, 1.0)  # Max 1.0 at 5 feedbacks
        collaboration_score = (
            balance_score * 0.4 +
            (1 - override_rate) * 0.3 +
            feedback_score * 0.3
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            session, acceptance_rate, override_rate, pending
        )

        return CollaborationReport(
            session_id=session_id,
            task=session.task,
            duration_minutes=duration,
            total_decisions=session.total_decisions,
            human_decisions=session.human_decisions,
            ai_decisions=session.ai_decisions,
            ai_recommendation_acceptance_rate=acceptance_rate,
            override_rate=override_rate,
            pending_decisions=pending,
            collaboration_score=collaboration_score,
            recommendations=recommendations,
        )

    def get_session(self, session_id: UUID) -> Optional[CollaborationSession]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def get_pending_decisions(self, session_id: UUID) -> List[DecisionPoint]:
        """Get all pending decisions for a session."""
        session = self._sessions.get(session_id)
        if not session:
            return []
        return [d for d in session.decision_points if d.status == "pending"]

    def register_callback(
        self,
        event_type: str,
        callback: Callable,
    ) -> None:
        """Register a callback for collaboration events."""
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)

    def _determine_decision_type(
        self,
        reason: HandoffReason,
        has_recommendation: bool
    ) -> DecisionType:
        """Determine decision type based on reason and AI input."""
        if reason in self.HUMAN_REQUIRED_REASONS:
            return DecisionType.HUMAN_REQUIRED
        elif has_recommendation:
            return DecisionType.AI_SUGGESTED
        else:
            return DecisionType.COLLABORATIVE

    def _change_mode(
        self,
        session: CollaborationSession,
        new_mode: CollaborationMode,
        reason: Optional[str] = None,
    ) -> None:
        """Internal method to change mode and record event."""
        old_mode = session.mode
        session.mode = new_mode
        session.last_activity = datetime.utcnow()

        self._record_event(
            session.id,
            "mode_change",
            f"Mode changed: {old_mode.value} -> {new_mode.value}",
            "ai",
            {"old_mode": old_mode.value, "new_mode": new_mode.value, "reason": reason}
        )

        self._trigger_callback("mode_change", session, old_mode, new_mode)

    def _record_event(
        self,
        session_id: UUID,
        event_type: str,
        description: str,
        actor: str,
        data: Dict[str, Any],
    ) -> None:
        """Record an event in the session timeline."""
        session = self._sessions.get(session_id)
        if session:
            event = CollaborationEvent(
                id=uuid4(),
                session_id=session_id,
                event_type=event_type,
                description=description,
                actor=actor,
                data=data,
            )
            session.events.append(event)

    def _trigger_callback(self, event_type: str, *args) -> None:
        """Trigger callbacks for an event type."""
        for callback in self._callbacks.get(event_type, []):
            try:
                callback(*args)
            except Exception as e:
                logger.warning(f"Callback failed for {event_type}: {e}")

    def _generate_recommendations(
        self,
        session: CollaborationSession,
        acceptance_rate: float,
        override_rate: float,
        pending_decisions: int,
    ) -> List[str]:
        """Generate recommendations for improving collaboration."""
        recommendations = []

        if pending_decisions > 0:
            recommendations.append(f"Address {pending_decisions} pending decision(s)")

        if override_rate > 0.5:
            recommendations.append(
                "High override rate suggests AI recommendations need calibration"
            )

        if acceptance_rate < 0.3:
            recommendations.append(
                "Low acceptance rate - AI should request more context before recommending"
            )

        if session.human_decisions > session.ai_decisions * 3:
            recommendations.append(
                "Consider enabling more AI autonomous decisions for routine tasks"
            )

        if session.ai_decisions > session.human_decisions * 5:
            recommendations.append(
                "Increase human touchpoints to maintain active partnership"
            )

        if len(session.feedback) == 0:
            recommendations.append(
                "Provide feedback to help AI improve recommendations"
            )

        if not recommendations:
            recommendations.append("Collaboration is well-balanced. Keep up the good work!")

        return recommendations
