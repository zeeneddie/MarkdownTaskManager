"""
Continuous Learning Service

Week 25-26: AgentEvolver Integration - Continuous Learning Infrastructure
Based on: github.com/zeeneddie/AgentEvolver

Implements continuous learning for agents:
1. Automatic threshold optimization
2. Learning rate adjustment based on performance
3. Pattern weight updates
4. Automatic retraining triggers
5. Learning session management

Author: Claude Code (Week 25 Day 1-2)
Date: 2025-11-22
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import logging
import asyncio
import json

from app.services.experience_store_service import (
    ExperienceStoreService,
    get_experience_store,
    Experience,
    SuccessfulPattern,
    AgentRole,
    WorkType,
    Outcome,
    Complexity
)
from app.services.agent_evolution_service import (
    AgentEvolutionService,
    EvolutionConfig,
    PerformanceMetrics,
    get_evolution_service
)

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND TYPES
# ============================================================================

class LearningStatus(str, Enum):
    """Status of a learning session"""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class OptimizationType(str, Enum):
    """Types of optimization that can be performed"""
    THRESHOLD = "threshold"
    LEARNING_RATE = "learning_rate"
    PATTERN_WEIGHT = "pattern_weight"
    EXPLORATION_RATE = "exploration_rate"


class RetrainingReason(str, Enum):
    """Reasons for triggering retraining"""
    PERFORMANCE_DROP = "performance_drop"
    QUALITY_DECLINE = "quality_decline"
    NEW_PATTERNS = "new_patterns"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ThresholdUpdate:
    """Result of threshold optimization"""
    agent_id: str
    optimization_type: OptimizationType
    previous_values: Dict[str, float]
    new_values: Dict[str, float]
    improvement_expected: float
    confidence: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "optimization_type": self.optimization_type.value,
            "previous_values": self.previous_values,
            "new_values": self.new_values,
            "improvement_expected": self.improvement_expected,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class WeightUpdate:
    """Result of pattern weight update"""
    agent_id: str
    pattern_id: str
    pattern_name: str
    previous_weight: float
    new_weight: float
    success_rate: float
    usage_count: int
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "pattern_id": self.pattern_id,
            "pattern_name": self.pattern_name,
            "previous_weight": self.previous_weight,
            "new_weight": self.new_weight,
            "success_rate": self.success_rate,
            "usage_count": self.usage_count,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class LearningSession:
    """A learning session for an agent"""
    id: str
    agent_id: str
    agent_role: AgentRole
    status: LearningStatus
    started_at: datetime
    ended_at: Optional[datetime] = None

    # Session configuration
    optimization_types: List[OptimizationType] = field(default_factory=list)
    max_iterations: int = 10

    # Progress tracking
    current_iteration: int = 0
    threshold_updates: List[ThresholdUpdate] = field(default_factory=list)
    weight_updates: List[WeightUpdate] = field(default_factory=list)

    # Metrics before and after
    initial_metrics: Optional[PerformanceMetrics] = None
    final_metrics: Optional[PerformanceMetrics] = None

    # Results
    total_improvements: float = 0.0
    learnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "agent_role": self.agent_role.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "optimization_types": [ot.value for ot in self.optimization_types],
            "max_iterations": self.max_iterations,
            "current_iteration": self.current_iteration,
            "threshold_updates": [tu.to_dict() for tu in self.threshold_updates],
            "weight_updates": [wu.to_dict() for wu in self.weight_updates],
            "total_improvements": self.total_improvements,
            "learnings": self.learnings,
            "recommendations": self.recommendations
        }


@dataclass
class SessionResult:
    """Result of completing a learning session"""
    session_id: str
    agent_id: str
    success: bool
    total_duration: float  # seconds
    improvements_made: int
    average_improvement: float
    new_success_rate: float
    learnings: List[str]
    recommendations: List[str]
    next_session_scheduled: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "success": self.success,
            "total_duration": self.total_duration,
            "improvements_made": self.improvements_made,
            "average_improvement": self.average_improvement,
            "new_success_rate": self.new_success_rate,
            "learnings": self.learnings,
            "recommendations": self.recommendations,
            "next_session_scheduled": self.next_session_scheduled.isoformat() if self.next_session_scheduled else None
        }


@dataclass
class RetrainingCheck:
    """Result of checking if retraining is needed"""
    agent_id: str
    retraining_needed: bool
    reasons: List[RetrainingReason]
    urgency: str  # 'low', 'medium', 'high', 'critical'
    metrics_summary: Dict[str, Any]
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "retraining_needed": self.retraining_needed,
            "reasons": [r.value for r in self.reasons],
            "urgency": self.urgency,
            "metrics_summary": self.metrics_summary,
            "recommendation": self.recommendation
        }


@dataclass
class LearningMetrics:
    """Comprehensive learning metrics for an agent"""
    agent_id: str
    agent_role: AgentRole

    # Overall learning progress
    total_sessions: int = 0
    successful_sessions: int = 0
    total_improvements: float = 0.0
    average_improvement_per_session: float = 0.0

    # Threshold optimization metrics
    thresholds_optimized: int = 0
    threshold_improvements: List[float] = field(default_factory=list)

    # Pattern learning metrics
    patterns_learned: int = 0
    pattern_reuse_rate: float = 0.0

    # Time-based metrics
    learning_streak: int = 0  # consecutive successful sessions
    time_since_last_session: Optional[timedelta] = None
    next_scheduled_session: Optional[datetime] = None

    # Trend analysis
    improvement_trend: str = "stable"  # 'improving', 'stable', 'declining'
    performance_trajectory: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_role": self.agent_role.value,
            "total_sessions": self.total_sessions,
            "successful_sessions": self.successful_sessions,
            "total_improvements": self.total_improvements,
            "average_improvement_per_session": self.average_improvement_per_session,
            "thresholds_optimized": self.thresholds_optimized,
            "threshold_improvements": self.threshold_improvements,
            "patterns_learned": self.patterns_learned,
            "pattern_reuse_rate": self.pattern_reuse_rate,
            "learning_streak": self.learning_streak,
            "time_since_last_session": str(self.time_since_last_session) if self.time_since_last_session else None,
            "next_scheduled_session": self.next_scheduled_session.isoformat() if self.next_scheduled_session else None,
            "improvement_trend": self.improvement_trend,
            "performance_trajectory": self.performance_trajectory
        }


# ============================================================================
# CONTINUOUS LEARNING SERVICE
# ============================================================================

class ContinuousLearningService:
    """
    Service for continuous agent learning and improvement.

    Implements automatic optimization of:
    - Validation thresholds
    - Learning rates
    - Pattern weights
    - Exploration rates
    """

    # Default optimization parameters
    DEFAULT_LEARNING_RATE = 0.1
    MIN_LEARNING_RATE = 0.01
    MAX_LEARNING_RATE = 0.5

    DEFAULT_EXPLORATION_RATE = 0.2
    MIN_EXPLORATION_RATE = 0.05
    MAX_EXPLORATION_RATE = 0.4

    # Retraining triggers
    RETRAINING_TRIGGERS = {
        'success_rate_drop': 0.10,      # >10% drop triggers retraining
        'quality_score_drop': 0.15,     # >15% drop triggers retraining
        'estimation_error_increase': 0.20  # >20% increase triggers retraining
    }

    def __init__(self):
        self._experience_store: Optional[ExperienceStoreService] = None
        self._evolution_service: Optional[AgentEvolutionService] = None

        # In-memory storage for sessions (in production, use database)
        self._sessions: Dict[str, LearningSession] = {}
        self._agent_configs: Dict[str, EvolutionConfig] = {}
        self._learning_metrics: Dict[str, LearningMetrics] = {}

        # Optimization history
        self._optimization_history: List[Dict[str, Any]] = []

    async def _get_experience_store(self) -> ExperienceStoreService:
        """Get or create experience store instance"""
        if self._experience_store is None:
            self._experience_store = await get_experience_store()
        return self._experience_store

    async def _get_evolution_service(self) -> AgentEvolutionService:
        """Get or create evolution service instance"""
        if self._evolution_service is None:
            self._evolution_service = await get_evolution_service()
        return self._evolution_service

    # -------------------------------------------------------------------------
    # THRESHOLD OPTIMIZATION
    # -------------------------------------------------------------------------

    async def optimize_validation_thresholds(
        self,
        agent_id: str,
        work_type: Optional[WorkType] = None
    ) -> ThresholdUpdate:
        """
        Optimize validation thresholds based on accumulated experience.

        Analyzes past validation successes/failures to find optimal thresholds.
        """
        experience_store = await self._get_experience_store()

        # Get recent experiences
        experiences = await experience_store.get_experiences(
            agent_id=agent_id,
            work_type=work_type,
            limit=100
        )

        if not experiences:
            logger.warning(f"No experiences found for agent {agent_id}")
            return ThresholdUpdate(
                agent_id=agent_id,
                optimization_type=OptimizationType.THRESHOLD,
                previous_values={},
                new_values={},
                improvement_expected=0.0,
                confidence=0.0,
                reasoning="No experiences available for optimization"
            )

        # Analyze success rates at different quality thresholds
        current_threshold = self._get_agent_config(agent_id).min_experience_confidence

        # Calculate optimal threshold based on experience distribution
        quality_scores = [exp.quality_score for exp in experiences]
        successful = [exp for exp in experiences if exp.outcome == Outcome.SUCCESS]

        success_rate = len(successful) / len(experiences)
        avg_success_quality = sum(exp.quality_score for exp in successful) / len(successful) if successful else 0
        avg_quality = sum(quality_scores) / len(quality_scores)

        # Determine new threshold
        # If success rate is high, we can be more selective
        # If success rate is low, we need to be more inclusive
        if success_rate > 0.8:
            # High success rate - increase threshold slightly
            new_threshold = min(current_threshold + 0.05, 0.9)
            reasoning = f"High success rate ({success_rate:.1%}), increasing selectivity"
        elif success_rate < 0.5:
            # Low success rate - decrease threshold
            new_threshold = max(current_threshold - 0.1, 0.3)
            reasoning = f"Low success rate ({success_rate:.1%}), decreasing selectivity"
        else:
            # Moderate success rate - fine-tune based on quality distribution
            quality_variance = sum((q - avg_quality) ** 2 for q in quality_scores) / len(quality_scores)
            if quality_variance > 100:
                new_threshold = avg_success_quality / 100  # Use success quality as guide
            else:
                new_threshold = current_threshold
            reasoning = f"Moderate success rate ({success_rate:.1%}), optimizing for quality distribution"

        # Calculate expected improvement
        improvement_expected = (new_threshold - current_threshold) * 0.1  # Rough estimate

        # Update config
        config = self._get_agent_config(agent_id)
        config.min_experience_confidence = new_threshold

        update = ThresholdUpdate(
            agent_id=agent_id,
            optimization_type=OptimizationType.THRESHOLD,
            previous_values={"min_experience_confidence": current_threshold},
            new_values={"min_experience_confidence": new_threshold},
            improvement_expected=improvement_expected,
            confidence=min(0.9, success_rate + 0.1),
            reasoning=reasoning
        )

        # Log optimization
        self._optimization_history.append(update.to_dict())
        logger.info(f"Optimized thresholds for {agent_id}: {update.reasoning}")

        return update

    # -------------------------------------------------------------------------
    # LEARNING RATE ADJUSTMENT
    # -------------------------------------------------------------------------

    async def adjust_learning_rate(
        self,
        agent_id: str,
        performance: PerformanceMetrics
    ) -> float:
        """
        Adjust learning rate based on performance.

        - If performance is improving: decrease learning rate (fine-tuning)
        - If performance is declining: increase learning rate (more aggressive)
        - If performance is stable: maintain or slightly decrease
        """
        config = self._get_agent_config(agent_id)
        current_rate = config.learning_rate

        # Get historical performance for trend analysis
        metrics = self._learning_metrics.get(agent_id)

        if metrics and metrics.performance_trajectory:
            # Calculate trend
            recent = metrics.performance_trajectory[-5:]  # Last 5 measurements
            if len(recent) >= 2:
                trend = recent[-1] - recent[0]

                if trend > 0.05:  # Improving
                    # Decrease learning rate for fine-tuning
                    new_rate = max(self.MIN_LEARNING_RATE, current_rate * 0.9)
                    logger.info(f"Agent {agent_id} improving, decreasing learning rate to {new_rate:.3f}")
                elif trend < -0.05:  # Declining
                    # Increase learning rate for faster adaptation
                    new_rate = min(self.MAX_LEARNING_RATE, current_rate * 1.2)
                    logger.info(f"Agent {agent_id} declining, increasing learning rate to {new_rate:.3f}")
                else:  # Stable
                    new_rate = max(self.MIN_LEARNING_RATE, current_rate * 0.95)
            else:
                new_rate = current_rate
        else:
            # No history - use success rate to determine
            if performance.success_rate > 0.8:
                new_rate = max(self.MIN_LEARNING_RATE, current_rate * 0.8)
            elif performance.success_rate < 0.5:
                new_rate = min(self.MAX_LEARNING_RATE, current_rate * 1.3)
            else:
                new_rate = current_rate

        # Update config
        config.learning_rate = new_rate

        return new_rate

    # -------------------------------------------------------------------------
    # PATTERN WEIGHT UPDATES
    # -------------------------------------------------------------------------

    async def update_pattern_weights(self, agent_id: str) -> List[WeightUpdate]:
        """
        Update pattern weights based on success rates.

        Patterns that lead to success get higher weights,
        patterns that lead to failure get lower weights.
        """
        experience_store = await self._get_experience_store()

        # Get successful patterns for this agent
        patterns = await experience_store.get_successful_patterns(
            work_types=None,  # All work types
            min_success_count=1
        )

        updates = []

        for pattern in patterns:
            # Calculate success rate
            total_uses = pattern.success_count + pattern.failure_count
            if total_uses == 0:
                continue

            success_rate = pattern.success_count / total_uses

            # Current weight (stored in metadata or default)
            current_weight = 0.5  # Default weight

            # Calculate new weight based on success rate and usage
            # Higher success rate = higher weight
            # More usage = more confident in the weight
            confidence = min(1.0, total_uses / 20)  # Max confidence at 20+ uses
            new_weight = (success_rate * confidence) + (0.5 * (1 - confidence))

            # Determine reasoning
            if success_rate > 0.8:
                reasoning = f"High success rate ({success_rate:.1%}) with {total_uses} uses"
            elif success_rate < 0.4:
                reasoning = f"Low success rate ({success_rate:.1%}), consider deprecating"
            else:
                reasoning = f"Moderate success rate ({success_rate:.1%}), maintaining"

            update = WeightUpdate(
                agent_id=agent_id,
                pattern_id=pattern.id,
                pattern_name=pattern.name,
                previous_weight=current_weight,
                new_weight=new_weight,
                success_rate=success_rate,
                usage_count=total_uses,
                reasoning=reasoning
            )
            updates.append(update)

            logger.info(f"Updated pattern weight for '{pattern.name}': {current_weight:.2f} -> {new_weight:.2f}")

        return updates

    # -------------------------------------------------------------------------
    # RETRAINING TRIGGERS
    # -------------------------------------------------------------------------

    async def check_retraining_needed(self, agent_id: str) -> RetrainingCheck:
        """
        Check if agent needs retraining based on performance metrics.
        """
        evolution_service = await self._get_evolution_service()

        # Get current and historical performance
        current_metrics = await evolution_service.get_performance_metrics(
            agent_id=agent_id,
            period_days=7
        )

        historical_metrics = await evolution_service.get_performance_metrics(
            agent_id=agent_id,
            period_days=30
        )

        reasons = []
        urgency = "low"

        # Check success rate
        if historical_metrics and current_metrics:
            success_drop = historical_metrics.success_rate - current_metrics.success_rate
            if success_drop > self.RETRAINING_TRIGGERS['success_rate_drop']:
                reasons.append(RetrainingReason.PERFORMANCE_DROP)
                urgency = "high" if success_drop > 0.2 else "medium"

            # Check quality score
            quality_drop = historical_metrics.average_quality_score - current_metrics.average_quality_score
            if quality_drop > self.RETRAINING_TRIGGERS['quality_score_drop'] * 100:
                reasons.append(RetrainingReason.QUALITY_DECLINE)
                urgency = max(urgency, "medium", key=lambda x: ["low", "medium", "high", "critical"].index(x))

        # Check if there are new patterns to learn
        experience_store = await self._get_experience_store()
        recent_patterns = await experience_store.get_successful_patterns(
            work_types=None,
            min_success_count=3
        )

        learning_metrics = self._learning_metrics.get(agent_id)
        if learning_metrics and len(recent_patterns) > learning_metrics.patterns_learned + 5:
            reasons.append(RetrainingReason.NEW_PATTERNS)

        # Build recommendation
        if reasons:
            if RetrainingReason.PERFORMANCE_DROP in reasons:
                recommendation = "Immediate retraining recommended due to performance degradation"
            elif RetrainingReason.QUALITY_DECLINE in reasons:
                recommendation = "Retraining recommended to address quality issues"
            else:
                recommendation = "Scheduled retraining recommended to learn new patterns"
        else:
            recommendation = "No retraining needed at this time"

        return RetrainingCheck(
            agent_id=agent_id,
            retraining_needed=len(reasons) > 0,
            reasons=reasons,
            urgency=urgency,
            metrics_summary={
                "current_success_rate": current_metrics.success_rate if current_metrics else 0.0,
                "current_quality_score": current_metrics.average_quality_score if current_metrics else 0.0,
                "patterns_available": len(recent_patterns)
            },
            recommendation=recommendation
        )

    # -------------------------------------------------------------------------
    # LEARNING SESSION MANAGEMENT
    # -------------------------------------------------------------------------

    async def start_learning_session(
        self,
        agent_id: str,
        optimization_types: Optional[List[OptimizationType]] = None,
        max_iterations: int = 10
    ) -> LearningSession:
        """
        Start a new learning session for an agent.
        """
        evolution_service = await self._get_evolution_service()

        # Get agent role
        agent_role = self._get_agent_role(agent_id)

        # Default to all optimization types
        if optimization_types is None:
            optimization_types = list(OptimizationType)

        # Create session
        session = LearningSession(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            agent_role=agent_role,
            status=LearningStatus.ACTIVE,
            started_at=datetime.now(),
            optimization_types=optimization_types,
            max_iterations=max_iterations
        )

        # Get initial metrics
        session.initial_metrics = await evolution_service.get_performance_metrics(
            agent_id=agent_id,
            period_days=7
        )

        # Store session
        self._sessions[session.id] = session

        logger.info(f"Started learning session {session.id} for agent {agent_id}")

        # Start learning iterations
        await self._run_learning_iterations(session)

        return session

    async def _run_learning_iterations(self, session: LearningSession) -> None:
        """Run learning iterations for a session"""
        for i in range(session.max_iterations):
            if session.status != LearningStatus.ACTIVE:
                break

            session.current_iteration = i + 1

            # Run optimizations
            if OptimizationType.THRESHOLD in session.optimization_types:
                update = await self.optimize_validation_thresholds(session.agent_id)
                session.threshold_updates.append(update)

            if OptimizationType.PATTERN_WEIGHT in session.optimization_types:
                updates = await self.update_pattern_weights(session.agent_id)
                session.weight_updates.extend(updates)

            if OptimizationType.LEARNING_RATE in session.optimization_types:
                evolution_service = await self._get_evolution_service()
                metrics = await evolution_service.get_performance_metrics(
                    agent_id=session.agent_id,
                    period_days=7
                )
                if metrics:
                    await self.adjust_learning_rate(session.agent_id, metrics)

            # Small delay between iterations
            await asyncio.sleep(0.1)

        # Mark session as completed
        session.status = LearningStatus.COMPLETED

    async def complete_learning_session(
        self,
        session_id: str,
        outcomes: Dict[str, Any]
    ) -> SessionResult:
        """
        Complete a learning session and record outcomes.
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        evolution_service = await self._get_evolution_service()

        # Get final metrics
        session.final_metrics = await evolution_service.get_performance_metrics(
            agent_id=session.agent_id,
            period_days=7
        )

        session.ended_at = datetime.now()
        session.status = LearningStatus.COMPLETED

        # Calculate improvements
        improvements_made = len(session.threshold_updates) + len(session.weight_updates)

        # Calculate average improvement
        all_improvements = []
        for tu in session.threshold_updates:
            all_improvements.append(tu.improvement_expected)

        average_improvement = sum(all_improvements) / len(all_improvements) if all_improvements else 0.0

        # Generate learnings and recommendations
        learnings = []
        recommendations = []

        if session.initial_metrics and session.final_metrics:
            success_change = session.final_metrics.success_rate - session.initial_metrics.success_rate
            if success_change > 0:
                learnings.append(f"Success rate improved by {success_change:.1%}")
            elif success_change < 0:
                learnings.append(f"Success rate decreased by {abs(success_change):.1%}")
                recommendations.append("Consider reverting recent changes")

        for wu in session.weight_updates:
            if wu.success_rate > 0.8:
                learnings.append(f"Pattern '{wu.pattern_name}' is highly effective")
            elif wu.success_rate < 0.4:
                recommendations.append(f"Consider deprecating pattern '{wu.pattern_name}'")

        session.learnings = learnings
        session.recommendations = recommendations

        # Update learning metrics
        self._update_learning_metrics(session)

        # Schedule next session if needed
        next_session = datetime.now() + timedelta(days=7)  # Weekly by default

        result = SessionResult(
            session_id=session.id,
            agent_id=session.agent_id,
            success=improvements_made > 0,
            total_duration=(session.ended_at - session.started_at).total_seconds(),
            improvements_made=improvements_made,
            average_improvement=average_improvement,
            new_success_rate=session.final_metrics.success_rate if session.final_metrics else 0.0,
            learnings=learnings,
            recommendations=recommendations,
            next_session_scheduled=next_session
        )

        logger.info(f"Completed learning session {session_id} with {improvements_made} improvements")

        return result

    # -------------------------------------------------------------------------
    # METRICS AND STATUS
    # -------------------------------------------------------------------------

    async def get_learning_metrics(self, agent_id: str) -> LearningMetrics:
        """Get learning metrics for an agent"""
        if agent_id not in self._learning_metrics:
            agent_role = self._get_agent_role(agent_id)
            self._learning_metrics[agent_id] = LearningMetrics(
                agent_id=agent_id,
                agent_role=agent_role
            )
        return self._learning_metrics[agent_id]

    async def get_all_learning_metrics(self) -> List[LearningMetrics]:
        """Get learning metrics for all agents"""
        return list(self._learning_metrics.values())

    async def get_session(self, session_id: str) -> Optional[LearningSession]:
        """Get a learning session by ID"""
        return self._sessions.get(session_id)

    async def get_agent_sessions(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[LearningSession]:
        """Get recent sessions for an agent"""
        sessions = [s for s in self._sessions.values() if s.agent_id == agent_id]
        sessions.sort(key=lambda s: s.started_at, reverse=True)
        return sessions[:limit]

    async def auto_tune_all_agents(self) -> Dict[str, Any]:
        """
        Auto-tune all agents with a single call.
        """
        results = {}
        agent_ids = [
            "felix", "marcus", "quinn", "betty", "eliza",
            "tessa", "miguel", "diana", "peter", "paul"
        ]

        for agent_id in agent_ids:
            try:
                # Check if retraining needed
                check = await self.check_retraining_needed(agent_id)

                if check.retraining_needed:
                    # Start learning session
                    session = await self.start_learning_session(agent_id)
                    outcome = await self.complete_learning_session(
                        session.id,
                        {"auto_tune": True}
                    )
                    results[agent_id] = {
                        "status": "tuned",
                        "session_id": session.id,
                        "improvements": outcome.improvements_made
                    }
                else:
                    results[agent_id] = {
                        "status": "no_tuning_needed",
                        "reason": check.recommendation
                    }
            except Exception as e:
                logger.error(f"Error auto-tuning agent {agent_id}: {e}")
                results[agent_id] = {
                    "status": "error",
                    "error": str(e)
                }

        return results

    # -------------------------------------------------------------------------
    # HELPER METHODS
    # -------------------------------------------------------------------------

    def _get_agent_config(self, agent_id: str) -> EvolutionConfig:
        """Get or create evolution config for an agent"""
        if agent_id not in self._agent_configs:
            self._agent_configs[agent_id] = EvolutionConfig()
        return self._agent_configs[agent_id]

    def _get_agent_role(self, agent_id: str) -> AgentRole:
        """Map agent ID to role"""
        role_map = {
            "felix": AgentRole.FEATURE_ARCHITECT,
            "marcus": AgentRole.MAINTENANCE_SPECIALIST,
            "quinn": AgentRole.QUALITY_INSPECTOR,
            "betty": AgentRole.BUG_HUNTER,
            "eliza": AgentRole.ESTIMATION_ENGINE,
            "tessa": AgentRole.TEST_ENGINEER,
            "miguel": AgentRole.MIGRATION_ARCHITECT,
            "diana": AgentRole.DOCUMENTATION_WRITER,
            "peter": AgentRole.PRODUCT_OWNER,
            "paul": AgentRole.PROJECT_LEAD
        }
        return role_map.get(agent_id.lower(), AgentRole.FEATURE_ARCHITECT)

    def _update_learning_metrics(self, session: LearningSession) -> None:
        """Update learning metrics after a session"""
        if session.agent_id not in self._learning_metrics:
            self._learning_metrics[session.agent_id] = LearningMetrics(
                agent_id=session.agent_id,
                agent_role=session.agent_role
            )

        metrics = self._learning_metrics[session.agent_id]
        metrics.total_sessions += 1

        if session.status == LearningStatus.COMPLETED:
            metrics.successful_sessions += 1
            metrics.learning_streak += 1
        else:
            metrics.learning_streak = 0

        metrics.thresholds_optimized += len(session.threshold_updates)
        metrics.patterns_learned += len(session.weight_updates)

        # Update trajectory
        if session.final_metrics:
            metrics.performance_trajectory.append(session.final_metrics.success_rate)

            # Determine trend
            if len(metrics.performance_trajectory) >= 3:
                recent = metrics.performance_trajectory[-3:]
                if all(recent[i] < recent[i+1] for i in range(len(recent)-1)):
                    metrics.improvement_trend = "improving"
                elif all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
                    metrics.improvement_trend = "declining"
                else:
                    metrics.improvement_trend = "stable"


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_continuous_learning_service: Optional[ContinuousLearningService] = None


async def get_continuous_learning_service() -> ContinuousLearningService:
    """Get or create continuous learning service instance"""
    global _continuous_learning_service
    if _continuous_learning_service is None:
        _continuous_learning_service = ContinuousLearningService()
    return _continuous_learning_service
