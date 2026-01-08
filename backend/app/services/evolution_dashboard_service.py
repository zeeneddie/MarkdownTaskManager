"""
Evolution Dashboard Service

Week 53: Continuous Evolution - Evolution Dashboard
Provides real-time agent performance metrics, trends, and insights.

Aggregates data from:
- A/B Testing Framework (Week 51)
- Experience Store (Week 17)
- Attribution System (Week 21-22)
- Self-Questioning (Week 23-24)

Author: Claude Code (Week 53 Day 1)
Date: 2025-11-25
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from statistics import mean, stdev

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ab_testing import Experiment, ExperimentVariant, ExperimentResult
from app.services.experience_store_service import ExperienceStoreService, AgentRole, WorkType, Outcome

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND TYPES
# ============================================================================

class TrendDirection(str, Enum):
    """Performance trend direction"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    INSUFFICIENT_DATA = "insufficient_data"


class PerformanceLevel(str, Enum):
    """Overall performance classification"""
    EXCELLENT = "excellent"  # >90%
    GOOD = "good"            # 75-90%
    AVERAGE = "average"      # 60-75%
    POOR = "poor"            # 45-60%
    CRITICAL = "critical"    # <45%


class TimeRange(str, Enum):
    """Time range for analysis"""
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"
    NINETY_DAYS = "90d"
    ALL_TIME = "all"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for a single agent"""
    agent_id: str
    agent_role: str

    # Success metrics
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    success_rate: float  # 0-100

    # Trend analysis
    trend_direction: TrendDirection
    improvement_rate: float  # % change week-over-week
    learning_velocity: float  # Rate of improvement

    # Experiment participation
    experiments_participated: int
    experiments_won: int
    win_rate: float  # 0-100

    # Quality metrics
    avg_code_quality: Optional[float]  # 0-100
    avg_estimation_accuracy: Optional[float]  # 0-100

    # Performance level
    performance_level: PerformanceLevel

    # Time series data (last 30 days)
    daily_success_rates: List[Tuple[str, float]]  # [(date, rate), ...]

    # Last updated
    last_activity: Optional[datetime]
    data_points: int  # Number of data points used


@dataclass
class ExperimentSummary:
    """Summary of an experiment"""
    experiment_id: str
    agent_id: str
    feature_name: str
    status: str

    # Timestamps
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_days: Optional[float]

    # Variants
    variant_count: int
    control_variant: str
    treatment_variants: List[str]

    # Results
    winner_variant: Optional[str]
    improvement_percentage: Optional[float]
    confidence_level: Optional[float]

    # Statistical metrics
    total_trials: int
    control_success_rate: Optional[float]
    treatment_success_rate: Optional[float]


@dataclass
class LearningMilestone:
    """A significant learning achievement"""
    milestone_id: str
    agent_id: str
    milestone_type: str  # "success_rate_high", "pattern_discovered", "skill_mastered"
    description: str
    achieved_at: datetime
    metric_value: Optional[float]
    context: Dict[str, Any]


@dataclass
class DashboardOverview:
    """High-level dashboard metrics"""
    # Global metrics
    total_experiments: int
    active_experiments: int
    completed_experiments: int

    # Agent metrics
    total_agents: int
    improving_agents: int
    stable_agents: int
    declining_agents: int

    # Performance metrics
    avg_success_rate: float  # Across all agents
    avg_improvement_rate: float  # Week-over-week
    top_performer: Optional[str]  # Agent ID

    # Learning metrics
    total_experiences_logged: int
    successful_patterns: int
    failure_analyses: int
    recent_milestones: int  # Last 7 days

    # Time range
    time_range: TimeRange
    generated_at: datetime


# ============================================================================
# EVOLUTION DASHBOARD SERVICE
# ============================================================================

class EvolutionDashboardService:
    """
    Service for evolution dashboard metrics and insights.

    Provides:
    - Agent performance trends
    - Experiment summaries
    - Learning velocity tracking
    - Milestone detection
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize service with database session."""
        self.db = db_session
        self.experience_store = ExperienceStoreService()


    # ========== OVERVIEW METRICS ==========

    async def get_dashboard_overview(
        self,
        time_range: TimeRange = TimeRange.THIRTY_DAYS
    ) -> DashboardOverview:
        """
        Get high-level dashboard metrics.

        Args:
            time_range: Time range for analysis

        Returns:
            DashboardOverview with global metrics
        """
        # Calculate date cutoff
        cutoff_date = self._get_cutoff_date(time_range)

        # Get experiment metrics
        total_experiments = await self._count_experiments()
        active_experiments = await self._count_experiments(status="ACTIVE")
        completed_experiments = await self._count_experiments(status="COMPLETED")

        # Get agent performance metrics
        agent_metrics = await self._get_all_agent_metrics(time_range)

        improving_count = sum(1 for m in agent_metrics if m.trend_direction == TrendDirection.IMPROVING)
        stable_count = sum(1 for m in agent_metrics if m.trend_direction == TrendDirection.STABLE)
        declining_count = sum(1 for m in agent_metrics if m.trend_direction == TrendDirection.DECLINING)

        # Calculate averages
        avg_success = mean([m.success_rate for m in agent_metrics]) if agent_metrics else 0.0
        avg_improvement = mean([m.improvement_rate for m in agent_metrics]) if agent_metrics else 0.0

        # Find top performer
        top_performer = None
        if agent_metrics:
            top = max(agent_metrics, key=lambda m: m.success_rate)
            top_performer = top.agent_id

        # Get experience store metrics
        try:
            total_experiences = await self.experience_store.count_experiences()
            successful_patterns = await self.experience_store.count_successful_patterns()
            failure_analyses = await self.experience_store.count_failure_analyses()
        except Exception as e:
            logger.warning(f"Could not fetch experience store metrics: {e}")
            total_experiences = 0
            successful_patterns = 0
            failure_analyses = 0

        # Get recent milestones
        recent_milestones = await self._count_recent_milestones(days=7)

        return DashboardOverview(
            total_experiments=total_experiments,
            active_experiments=active_experiments,
            completed_experiments=completed_experiments,
            total_agents=len(agent_metrics),
            improving_agents=improving_count,
            stable_agents=stable_count,
            declining_agents=declining_count,
            avg_success_rate=avg_success,
            avg_improvement_rate=avg_improvement,
            top_performer=top_performer,
            total_experiences_logged=total_experiences,
            successful_patterns=successful_patterns,
            failure_analyses=failure_analyses,
            recent_milestones=recent_milestones,
            time_range=time_range,
            generated_at=datetime.now(timezone.utc)
        )


    async def get_agent_performance_trends(
        self,
        agent_id: str,
        time_range: TimeRange = TimeRange.THIRTY_DAYS
    ) -> AgentPerformanceMetrics:
        """
        Get performance trends for a specific agent.

        Args:
            agent_id: Agent identifier
            time_range: Time range for analysis

        Returns:
            AgentPerformanceMetrics with detailed metrics
        """
        cutoff_date = self._get_cutoff_date(time_range)

        # Get agent role
        agent_role = self._get_agent_role(agent_id)

        # Get task outcomes from experience store
        experiences = await self.experience_store.get_agent_experiences(
            agent_id=agent_id,
            since_date=cutoff_date
        )

        # Calculate success metrics
        total_tasks = len(experiences)
        successful_tasks = sum(1 for exp in experiences if exp.outcome == Outcome.SUCCESS)
        failed_tasks = sum(1 for exp in experiences if exp.outcome == Outcome.FAILURE)
        success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0.0

        # Calculate trend
        trend_direction, improvement_rate = await self._calculate_trend(agent_id, cutoff_date)
        learning_velocity = await self._calculate_learning_velocity(agent_id, cutoff_date)

        # Get experiment participation
        experiments_participated = await self._count_agent_experiments(agent_id)
        experiments_won = await self._count_agent_wins(agent_id)
        win_rate = (experiments_won / experiments_participated * 100) if experiments_participated > 0 else 0.0

        # Get quality metrics from experience store
        avg_code_quality = await self._get_avg_quality_metric(agent_id, "code_quality", cutoff_date)
        avg_estimation_accuracy = await self._get_avg_quality_metric(agent_id, "estimation_accuracy", cutoff_date)

        # Determine performance level
        performance_level = self._classify_performance(success_rate)

        # Get daily success rates for sparkline
        daily_rates = await self._get_daily_success_rates(agent_id, days=30)

        # Last activity
        last_activity = experiences[0].timestamp if experiences else None

        return AgentPerformanceMetrics(
            agent_id=agent_id,
            agent_role=agent_role,
            total_tasks=total_tasks,
            successful_tasks=successful_tasks,
            failed_tasks=failed_tasks,
            success_rate=success_rate,
            trend_direction=trend_direction,
            improvement_rate=improvement_rate,
            learning_velocity=learning_velocity,
            experiments_participated=experiments_participated,
            experiments_won=experiments_won,
            win_rate=win_rate,
            avg_code_quality=avg_code_quality,
            avg_estimation_accuracy=avg_estimation_accuracy,
            performance_level=performance_level,
            daily_success_rates=daily_rates,
            last_activity=last_activity,
            data_points=total_tasks
        )


    async def get_all_agents_performance(
        self,
        time_range: TimeRange = TimeRange.THIRTY_DAYS
    ) -> List[AgentPerformanceMetrics]:
        """
        Get performance metrics for all agents.

        Args:
            time_range: Time range for analysis

        Returns:
            List of AgentPerformanceMetrics, sorted by success_rate
        """
        return await self._get_all_agent_metrics(time_range)


    # ========== EXPERIMENT SUMMARIES ==========

    async def get_experiment_summary(
        self,
        experiment_id: str
    ) -> Optional[ExperimentSummary]:
        """
        Get summary for a specific experiment.

        Args:
            experiment_id: Experiment UUID

        Returns:
            ExperimentSummary or None if not found
        """
        # Fetch experiment with variants
        stmt = select(Experiment).where(
            Experiment.id == experiment_id
        ).options(selectinload(Experiment.variants))

        result = await self.db.execute(stmt)
        experiment = result.scalar_one_or_none()

        if not experiment:
            return None

        # Calculate duration
        duration_days = None
        if experiment.started_at and experiment.completed_at:
            delta = experiment.completed_at - experiment.started_at
            duration_days = delta.total_seconds() / 86400

        # Parse variants
        control_variant = None
        treatment_variants = []
        for variant in experiment.variants:
            if variant.is_control:
                control_variant = variant.variant_name
            else:
                treatment_variants.append(variant.variant_name)

        # Get winner info
        winner_variant = None
        improvement_pct = None
        if experiment.winner_variant_id:
            winner = next((v for v in experiment.variants if v.id == experiment.winner_variant_id), None)
            if winner:
                winner_variant = winner.variant_name
                # Calculate improvement if we have results
                improvement_pct = await self._calculate_experiment_improvement(experiment.id)

        # Count total trials
        total_trials = await self._count_experiment_trials(experiment.id)

        # Get success rates
        control_success_rate = await self._get_variant_success_rate(experiment.id, control_variant) if control_variant else None
        treatment_success_rate = await self._get_variant_success_rate(experiment.id, winner_variant) if winner_variant else None

        return ExperimentSummary(
            experiment_id=str(experiment.id),
            agent_id=experiment.agent_id,
            feature_name=experiment.feature_name,
            status=experiment.status,
            created_at=experiment.created_at,
            started_at=experiment.started_at,
            completed_at=experiment.completed_at,
            duration_days=duration_days,
            variant_count=len(experiment.variants),
            control_variant=control_variant or "unknown",
            treatment_variants=treatment_variants,
            winner_variant=winner_variant,
            improvement_percentage=improvement_pct,
            confidence_level=None,  # TODO: Calculate from statistical analysis
            total_trials=total_trials,
            control_success_rate=control_success_rate,
            treatment_success_rate=treatment_success_rate
        )


    async def get_active_experiments(self) -> List[ExperimentSummary]:
        """
        Get all active experiments.

        Returns:
            List of ExperimentSummary for active experiments
        """
        stmt = select(Experiment).where(
            Experiment.status == "ACTIVE"
        ).options(selectinload(Experiment.variants))

        result = await self.db.execute(stmt)
        experiments = result.scalars().all()

        summaries = []
        for exp in experiments:
            summary = await self.get_experiment_summary(str(exp.id))
            if summary:
                summaries.append(summary)

        return summaries


    # ========== INTERNAL HELPERS ==========

    def _get_cutoff_date(self, time_range: TimeRange) -> datetime:
        """Calculate cutoff date for time range."""
        now = datetime.now(timezone.utc)

        if time_range == TimeRange.SEVEN_DAYS:
            return now - timedelta(days=7)
        elif time_range == TimeRange.THIRTY_DAYS:
            return now - timedelta(days=30)
        elif time_range == TimeRange.NINETY_DAYS:
            return now - timedelta(days=90)
        else:  # ALL_TIME
            return datetime(2020, 1, 1)  # Arbitrary old date


    def _get_agent_role(self, agent_id: str) -> str:
        """Get human-readable agent role."""
        role_map = {
            "felix": "Feature Architect",
            "marcus": "Maintenance Specialist",
            "quinn": "Quality Inspector",
            "betty": "Bug Hunter",
            "eliza": "Estimation Engine",
            "tessa": "Test Engineer",
            "miguel": "Migration Architect",
            "diana": "Documentation Writer",
            "peter": "Product Owner",
            "paul": "Project Lead"
        }
        return role_map.get(agent_id.lower(), agent_id)


    def _classify_performance(self, success_rate: float) -> PerformanceLevel:
        """Classify performance level based on success rate."""
        if success_rate >= 90:
            return PerformanceLevel.EXCELLENT
        elif success_rate >= 75:
            return PerformanceLevel.GOOD
        elif success_rate >= 60:
            return PerformanceLevel.AVERAGE
        elif success_rate >= 45:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL


    async def _get_all_agent_metrics(
        self,
        time_range: TimeRange
    ) -> List[AgentPerformanceMetrics]:
        """Get metrics for all 10 agents."""
        agent_ids = ["felix", "marcus", "quinn", "betty", "eliza",
                     "tessa", "miguel", "diana", "peter", "paul"]

        metrics = []
        for agent_id in agent_ids:
            try:
                metric = await self.get_agent_performance_trends(agent_id, time_range)
                metrics.append(metric)
            except Exception as e:
                logger.error(f"Error getting metrics for {agent_id}: {e}")

        # Sort by success rate descending
        metrics.sort(key=lambda m: m.success_rate, reverse=True)
        return metrics


    async def _count_experiments(self, status: Optional[str] = None) -> int:
        """Count experiments, optionally filtered by status."""
        if status:
            stmt = select(func.count()).select_from(Experiment).where(Experiment.status == status)
        else:
            stmt = select(func.count()).select_from(Experiment)

        result = await self.db.execute(stmt)
        return result.scalar() or 0


    async def _count_agent_experiments(self, agent_id: str) -> int:
        """Count experiments for an agent."""
        stmt = select(func.count()).select_from(Experiment).where(
            Experiment.agent_id == agent_id
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0


    async def _count_agent_wins(self, agent_id: str) -> int:
        """Count how many experiments this agent won."""
        # An agent "wins" if their treatment variant was selected as winner
        stmt = select(func.count()).select_from(Experiment).where(
            and_(
                Experiment.agent_id == agent_id,
                Experiment.winner_variant_id.isnot(None),
                Experiment.status == "COMPLETED"
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0


    async def _calculate_trend(
        self,
        agent_id: str,
        cutoff_date: datetime
    ) -> Tuple[TrendDirection, float]:
        """
        Calculate trend direction and improvement rate.

        Returns:
            (TrendDirection, improvement_rate_percentage)
        """
        # Get experiences split by time
        now = datetime.now(timezone.utc)
        mid_point = cutoff_date + (now - cutoff_date) / 2

        # Recent period (second half)
        recent_experiences = await self.experience_store.get_agent_experiences(
            agent_id=agent_id,
            since_date=mid_point
        )

        # Earlier period (first half)
        earlier_experiences = await self.experience_store.get_agent_experiences(
            agent_id=agent_id,
            since_date=cutoff_date,
            until_date=mid_point
        )

        # Not enough data
        if len(recent_experiences) < 5 or len(earlier_experiences) < 5:
            return TrendDirection.INSUFFICIENT_DATA, 0.0

        # Calculate success rates
        recent_success = sum(1 for e in recent_experiences if e.outcome == Outcome.SUCCESS) / len(recent_experiences)
        earlier_success = sum(1 for e in earlier_experiences if e.outcome == Outcome.SUCCESS) / len(earlier_experiences)

        # Calculate improvement
        if earlier_success == 0:
            improvement_rate = 0.0
        else:
            improvement_rate = ((recent_success - earlier_success) / earlier_success) * 100

        # Determine trend
        if improvement_rate > 5:
            direction = TrendDirection.IMPROVING
        elif improvement_rate < -5:
            direction = TrendDirection.DECLINING
        else:
            direction = TrendDirection.STABLE

        return direction, improvement_rate


    async def _calculate_learning_velocity(
        self,
        agent_id: str,
        cutoff_date: datetime
    ) -> float:
        """
        Calculate learning velocity (rate of improvement).

        Returns velocity as percentage points per week.
        """
        # Get experiences
        experiences = await self.experience_store.get_agent_experiences(
            agent_id=agent_id,
            since_date=cutoff_date
        )

        if len(experiences) < 10:
            return 0.0

        # Sort by timestamp
        experiences.sort(key=lambda e: e.timestamp)

        # Split into buckets (weekly)
        now = datetime.now(timezone.utc)
        weeks_back = (now - cutoff_date).days // 7
        if weeks_back < 2:
            return 0.0

        # Calculate success rate per week
        weekly_rates = []
        for week in range(weeks_back):
            week_start = cutoff_date + timedelta(weeks=week)
            week_end = week_start + timedelta(weeks=1)

            week_experiences = [
                e for e in experiences
                if week_start <= e.timestamp < week_end
            ]

            if len(week_experiences) > 0:
                success_count = sum(1 for e in week_experiences if e.outcome == Outcome.SUCCESS)
                rate = (success_count / len(week_experiences)) * 100
                weekly_rates.append(rate)

        # Calculate average improvement per week
        if len(weekly_rates) < 2:
            return 0.0

        # Simple linear regression slope
        improvements = [weekly_rates[i+1] - weekly_rates[i] for i in range(len(weekly_rates) - 1)]
        avg_improvement = mean(improvements) if improvements else 0.0

        return avg_improvement


    async def _get_daily_success_rates(
        self,
        agent_id: str,
        days: int = 30
    ) -> List[Tuple[str, float]]:
        """Get daily success rates for sparkline visualization."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        experiences = await self.experience_store.get_agent_experiences(
            agent_id=agent_id,
            since_date=cutoff
        )

        # Group by day
        daily_data = {}
        for exp in experiences:
            date_key = exp.timestamp.strftime("%Y-%m-%d")
            if date_key not in daily_data:
                daily_data[date_key] = {"total": 0, "success": 0}

            daily_data[date_key]["total"] += 1
            if exp.outcome == Outcome.SUCCESS:
                daily_data[date_key]["success"] += 1

        # Calculate rates
        result = []
        for date_key in sorted(daily_data.keys()):
            data = daily_data[date_key]
            rate = (data["success"] / data["total"] * 100) if data["total"] > 0 else 0.0
            result.append((date_key, rate))

        return result


    async def _get_avg_quality_metric(
        self,
        agent_id: str,
        metric_name: str,
        cutoff_date: datetime
    ) -> Optional[float]:
        """Get average quality metric from experience store."""
        try:
            # This would query quality_metrics collection in ChromaDB
            # For now, return None (implement when quality metrics are available)
            return None
        except Exception as e:
            logger.warning(f"Could not fetch quality metric {metric_name}: {e}")
            return None


    async def _count_recent_milestones(self, days: int = 7) -> int:
        """Count milestones achieved in the last N days."""
        # TODO: Implement milestone tracking
        # For now return 0
        return 0


    async def _count_experiment_trials(self, experiment_id: str) -> int:
        """Count total trials for an experiment."""
        stmt = select(func.count()).select_from(ExperimentResult).where(
            ExperimentResult.experiment_id == experiment_id
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0


    async def _get_variant_success_rate(
        self,
        experiment_id: str,
        variant_name: str
    ) -> Optional[float]:
        """Get success rate for a specific variant."""
        # Get variant ID
        stmt = select(ExperimentVariant).where(
            and_(
                ExperimentVariant.experiment_id == experiment_id,
                ExperimentVariant.variant_name == variant_name
            )
        )
        result = await self.db.execute(stmt)
        variant = result.scalar_one_or_none()

        if not variant:
            return None

        # Get results
        stmt = select(ExperimentResult).where(
            ExperimentResult.variant_id == variant.id
        )
        result = await self.db.execute(stmt)
        results = result.scalars().all()

        if not results:
            return None

        success_count = sum(1 for r in results if r.outcome == "SUCCESS")
        return (success_count / len(results)) * 100


    async def _calculate_experiment_improvement(
        self,
        experiment_id: str
    ) -> Optional[float]:
        """Calculate improvement percentage for experiment winner vs control."""
        # Get experiment
        stmt = select(Experiment).where(Experiment.id == experiment_id).options(
            selectinload(Experiment.variants)
        )
        result = await self.db.execute(stmt)
        experiment = result.scalar_one_or_none()

        if not experiment or not experiment.winner_variant_id:
            return None

        # Find control and winner
        control = next((v for v in experiment.variants if v.is_control), None)
        winner = next((v for v in experiment.variants if v.id == experiment.winner_variant_id), None)

        if not control or not winner:
            return None

        # Get success rates
        control_rate = await self._get_variant_success_rate(experiment_id, control.variant_name)
        winner_rate = await self._get_variant_success_rate(experiment_id, winner.variant_name)

        if control_rate is None or winner_rate is None or control_rate == 0:
            return None

        improvement = ((winner_rate - control_rate) / control_rate) * 100
        return improvement
