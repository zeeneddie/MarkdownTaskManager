"""
Check Alignment Service - Week 111

Pattern: Check Alignment (from Gregor Riegler's Augmented Coding Pattern Language)

Purpose: Verify that agent actions align with stated goals before execution.
The pattern prevents drift, scope creep, and ensures all changes serve the original intent.

Key Concepts:
- Goal Statement: The high-level objective
- Proposed Action: What the agent intends to do
- Alignment Score: How well the action serves the goal (0.0-1.0)
- Drift Detection: Identifies when actions diverge from goals

Usage:
    service = CheckAlignmentService()

    # Check single action
    result = service.check_action_alignment(
        goal="Implement user authentication",
        proposed_action="Add rate limiting to API",
        context={"file": "auth_service.py"}
    )

    if result.is_aligned:
        # Proceed with action
    else:
        # Request clarification or adjust action

    # Track goal alignment over session
    session = service.create_session("Add dark mode support")
    service.record_action(session.id, "Created theme context provider")
    drift_report = service.analyze_drift(session.id)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class AlignmentLevel(Enum):
    """Alignment levels between action and goal."""
    PERFECT = "perfect"        # 0.9-1.0: Action directly serves goal
    STRONG = "strong"          # 0.7-0.9: Action clearly supports goal
    MODERATE = "moderate"      # 0.5-0.7: Action tangentially supports goal
    WEAK = "weak"              # 0.3-0.5: Action loosely connected to goal
    MISALIGNED = "misaligned"  # 0.0-0.3: Action doesn't serve goal


class DriftType(Enum):
    """Types of goal drift detected."""
    SCOPE_CREEP = "scope_creep"          # Adding features beyond goal
    PREMATURE_OPTIMIZATION = "premature_optimization"  # Optimizing before needed
    TANGENT = "tangent"                  # Working on unrelated item
    GOLD_PLATING = "gold_plating"        # Excessive polish beyond requirements
    OVER_ENGINEERING = "over_engineering"  # Unnecessary complexity


@dataclass
class AlignmentCheck:
    """Result of a single alignment check."""
    action: str
    goal: str
    alignment_score: float
    level: AlignmentLevel
    is_aligned: bool
    reasoning: str
    suggestions: List[str] = field(default_factory=list)
    drift_type: Optional[DriftType] = None
    context: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ActionRecord:
    """Record of an action taken in a session."""
    id: UUID
    action: str
    alignment_score: float
    level: AlignmentLevel
    context: Dict[str, Any]
    timestamp: datetime


@dataclass
class AlignmentSession:
    """Session for tracking goal alignment over time."""
    id: UUID
    goal: str
    sub_goals: List[str]
    actions: List[ActionRecord]
    created_at: datetime
    last_activity: datetime
    average_alignment: float = 0.0
    drift_detected: bool = False


@dataclass
class DriftReport:
    """Report on goal drift in a session."""
    session_id: UUID
    total_actions: int
    aligned_actions: int
    misaligned_actions: int
    average_alignment: float
    drift_types: List[DriftType]
    drift_severity: float  # 0.0-1.0
    recommendations: List[str]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CheckAlignmentService:
    """
    Week 111: Check Alignment Service

    Ensures agent actions align with stated goals before execution.
    Detects drift and provides recommendations to stay on track.
    """

    # Alignment threshold for "is_aligned" determination
    ALIGNMENT_THRESHOLD = 0.5

    # Keywords that indicate direct goal alignment
    ALIGNMENT_KEYWORDS = {
        "implement": ["create", "add", "build", "develop", "write"],
        "fix": ["repair", "resolve", "correct", "debug", "patch"],
        "refactor": ["restructure", "reorganize", "clean", "improve structure"],
        "test": ["verify", "validate", "check", "assert", "ensure"],
        "document": ["describe", "explain", "annotate", "comment"],
        "remove": ["delete", "clean up", "eliminate", "drop"],
    }

    # Keywords that suggest drift
    DRIFT_KEYWORDS = {
        DriftType.SCOPE_CREEP: ["also", "additionally", "while we're at it", "might as well"],
        DriftType.PREMATURE_OPTIMIZATION: ["optimize", "performance", "cache", "faster"],
        DriftType.GOLD_PLATING: ["polish", "beautify", "extra", "bonus"],
        DriftType.OVER_ENGINEERING: ["abstract", "generic", "future-proof", "extensible"],
    }

    def __init__(self):
        self._sessions: Dict[UUID, AlignmentSession] = {}

    def check_action_alignment(
        self,
        goal: str,
        proposed_action: str,
        context: Optional[Dict[str, Any]] = None,
        sub_goals: Optional[List[str]] = None,
    ) -> AlignmentCheck:
        """
        Check if a proposed action aligns with the stated goal.

        Args:
            goal: The high-level objective
            proposed_action: What the agent intends to do
            context: Optional context (file, function, etc.)
            sub_goals: Optional list of sub-goals

        Returns:
            AlignmentCheck with score, level, and recommendations
        """
        context = context or {}
        sub_goals = sub_goals or []

        # Calculate alignment score
        score = self._calculate_alignment_score(goal, proposed_action, sub_goals)
        level = self._score_to_level(score)
        is_aligned = score >= self.ALIGNMENT_THRESHOLD

        # Detect drift type if misaligned
        drift_type = None
        if not is_aligned:
            drift_type = self._detect_drift_type(proposed_action)

        # Generate reasoning
        reasoning = self._generate_reasoning(goal, proposed_action, score, level, drift_type)

        # Generate suggestions
        suggestions = self._generate_suggestions(goal, proposed_action, score, drift_type)

        return AlignmentCheck(
            action=proposed_action,
            goal=goal,
            alignment_score=score,
            level=level,
            is_aligned=is_aligned,
            reasoning=reasoning,
            suggestions=suggestions,
            drift_type=drift_type,
            context=context,
        )

    def create_session(
        self,
        goal: str,
        sub_goals: Optional[List[str]] = None
    ) -> AlignmentSession:
        """
        Create a new alignment tracking session.

        Args:
            goal: The high-level objective for this session
            sub_goals: Optional list of sub-goals

        Returns:
            AlignmentSession for tracking
        """
        session = AlignmentSession(
            id=uuid4(),
            goal=goal,
            sub_goals=sub_goals or [],
            actions=[],
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
        )
        self._sessions[session.id] = session
        logger.info(f"Created alignment session {session.id} for goal: {goal[:50]}...")
        return session

    def record_action(
        self,
        session_id: UUID,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AlignmentCheck:
        """
        Record an action and check its alignment with session goal.

        Args:
            session_id: Session to record action for
            action: The action taken
            context: Optional context

        Returns:
            AlignmentCheck for the action
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Check alignment
        check = self.check_action_alignment(
            goal=session.goal,
            proposed_action=action,
            context=context,
            sub_goals=session.sub_goals,
        )

        # Record the action
        record = ActionRecord(
            id=uuid4(),
            action=action,
            alignment_score=check.alignment_score,
            level=check.level,
            context=context or {},
            timestamp=datetime.now(timezone.utc),
        )
        session.actions.append(record)
        session.last_activity = datetime.now(timezone.utc)

        # Update average alignment
        total_score = sum(a.alignment_score for a in session.actions)
        session.average_alignment = total_score / len(session.actions)

        # Update drift flag
        if check.drift_type:
            session.drift_detected = True

        logger.debug(f"Recorded action in session {session_id}: score={check.alignment_score:.2f}")
        return check

    def analyze_drift(self, session_id: UUID) -> DriftReport:
        """
        Analyze a session for goal drift.

        Args:
            session_id: Session to analyze

        Returns:
            DriftReport with analysis and recommendations
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        aligned = [a for a in session.actions if a.alignment_score >= self.ALIGNMENT_THRESHOLD]
        misaligned = [a for a in session.actions if a.alignment_score < self.ALIGNMENT_THRESHOLD]

        # Detect drift types
        drift_types = []
        for action in misaligned:
            drift_type = self._detect_drift_type(action.action)
            if drift_type and drift_type not in drift_types:
                drift_types.append(drift_type)

        # Calculate drift severity
        drift_severity = len(misaligned) / len(session.actions) if session.actions else 0.0

        # Generate recommendations
        recommendations = self._generate_drift_recommendations(
            session.goal, misaligned, drift_types
        )

        return DriftReport(
            session_id=session_id,
            total_actions=len(session.actions),
            aligned_actions=len(aligned),
            misaligned_actions=len(misaligned),
            average_alignment=session.average_alignment,
            drift_types=drift_types,
            drift_severity=drift_severity,
            recommendations=recommendations,
        )

    def get_session(self, session_id: UUID) -> Optional[AlignmentSession]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def _calculate_alignment_score(
        self,
        goal: str,
        action: str,
        sub_goals: List[str]
    ) -> float:
        """Calculate alignment score between action and goal."""
        goal_lower = goal.lower()
        action_lower = action.lower()

        score = 0.0

        # Check for keyword overlap
        goal_words = set(goal_lower.split())
        action_words = set(action_lower.split())
        overlap = goal_words.intersection(action_words)
        if overlap:
            score += 0.3 * min(len(overlap) / 3, 1.0)

        # Check for action verb alignment
        for goal_verb, synonyms in self.ALIGNMENT_KEYWORDS.items():
            if goal_verb in goal_lower:
                if any(syn in action_lower for syn in [goal_verb] + synonyms):
                    score += 0.3
                    break

        # Check for sub-goal alignment
        for sub_goal in sub_goals:
            sub_goal_words = set(sub_goal.lower().split())
            if sub_goal_words.intersection(action_words):
                score += 0.2
                break

        # Check for drift indicators (negative)
        for drift_type, keywords in self.DRIFT_KEYWORDS.items():
            if any(kw in action_lower for kw in keywords):
                if not any(kw in goal_lower for kw in keywords):
                    score -= 0.2
                    break

        # Ensure score is in valid range
        return max(0.0, min(1.0, score + 0.3))  # Base score of 0.3

    def _score_to_level(self, score: float) -> AlignmentLevel:
        """Convert numeric score to alignment level."""
        if score >= 0.9:
            return AlignmentLevel.PERFECT
        elif score >= 0.7:
            return AlignmentLevel.STRONG
        elif score >= 0.5:
            return AlignmentLevel.MODERATE
        elif score >= 0.3:
            return AlignmentLevel.WEAK
        else:
            return AlignmentLevel.MISALIGNED

    def _detect_drift_type(self, action: str) -> Optional[DriftType]:
        """Detect type of drift from action description."""
        action_lower = action.lower()

        for drift_type, keywords in self.DRIFT_KEYWORDS.items():
            if any(kw in action_lower for kw in keywords):
                return drift_type

        return None

    def _generate_reasoning(
        self,
        goal: str,
        action: str,
        score: float,
        level: AlignmentLevel,
        drift_type: Optional[DriftType]
    ) -> str:
        """Generate human-readable reasoning for alignment check."""
        if level == AlignmentLevel.PERFECT:
            return f"Action directly implements the goal. Score: {score:.2f}"
        elif level == AlignmentLevel.STRONG:
            return f"Action clearly supports the goal. Score: {score:.2f}"
        elif level == AlignmentLevel.MODERATE:
            return f"Action is related to the goal but connection is indirect. Score: {score:.2f}"
        elif level == AlignmentLevel.WEAK:
            drift_msg = f" Detected drift: {drift_type.value}" if drift_type else ""
            return f"Action has weak connection to goal.{drift_msg} Score: {score:.2f}"
        else:
            drift_msg = f" Drift type: {drift_type.value}" if drift_type else ""
            return f"Action appears misaligned with goal.{drift_msg} Score: {score:.2f}"

    def _generate_suggestions(
        self,
        goal: str,
        action: str,
        score: float,
        drift_type: Optional[DriftType]
    ) -> List[str]:
        """Generate suggestions for improving alignment."""
        suggestions = []

        if score < 0.5:
            suggestions.append(f"Consider how '{action[:30]}...' directly serves '{goal[:30]}...'")

        if drift_type == DriftType.SCOPE_CREEP:
            suggestions.append("Complete the core goal before adding features")
            suggestions.append("Create a separate task for this enhancement")
        elif drift_type == DriftType.PREMATURE_OPTIMIZATION:
            suggestions.append("Focus on correctness first, optimize later")
            suggestions.append("Profile before optimizing to identify real bottlenecks")
        elif drift_type == DriftType.GOLD_PLATING:
            suggestions.append("Deliver minimum viable solution first")
            suggestions.append("Track polish items for post-delivery review")
        elif drift_type == DriftType.OVER_ENGINEERING:
            suggestions.append("Implement the simplest solution that works")
            suggestions.append("Avoid abstraction until you have 3+ concrete cases")

        return suggestions

    def _generate_drift_recommendations(
        self,
        goal: str,
        misaligned_actions: List[ActionRecord],
        drift_types: List[DriftType]
    ) -> List[str]:
        """Generate recommendations based on drift analysis."""
        recommendations = []

        if not misaligned_actions:
            recommendations.append("Session is well-aligned with goal. Keep up the focused work!")
            return recommendations

        recommendations.append(f"Refocus on original goal: '{goal[:50]}...'")

        if DriftType.SCOPE_CREEP in drift_types:
            recommendations.append("Create a backlog for scope additions discovered during work")

        if DriftType.PREMATURE_OPTIMIZATION in drift_types:
            recommendations.append("Defer optimization until core functionality is complete")

        if DriftType.OVER_ENGINEERING in drift_types:
            recommendations.append("Apply YAGNI principle - implement only what's needed now")

        if len(misaligned_actions) > 2:
            recommendations.append("Consider re-stating the goal to ensure clarity")

        return recommendations
