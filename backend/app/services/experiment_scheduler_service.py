"""
Experiment Scheduler Service

Week 53 Day 3: Automatic Experiment Scheduler
Automatically detect performance gaps, generate experiment hypotheses,
schedule A/B tests, and manage experiment lifecycle.

Author: Claude Code (Week 53 Day 3)
Date: 2025-11-25
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from uuid import UUID, uuid4
import statistics

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.models.ab_testing import Experiment, ExperimentVariant, ExperimentStatus
from app.services.evolution_dashboard_service import (
    EvolutionDashboardService,
    TimeRange,
    TrendDirection,
    PerformanceLevel
)
from app.services.ab_testing_service import ABTestingService


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class ImprovementOpportunityType(str, Enum):
    """Types of improvement opportunities."""
    PERFORMANCE_GAP = "performance_gap"  # Agent underperforming vs peers
    DECLINING_TREND = "declining_trend"  # Agent performance declining
    LOW_WIN_RATE = "low_win_rate"  # Agent losing experiments
    INCONSISTENT = "inconsistent"  # High variance in success rate
    NEW_AGENT = "new_agent"  # Agent needs baseline experiments


class ExperimentPriority(str, Enum):
    """Experiment scheduling priority."""
    CRITICAL = "critical"  # High impact, schedule immediately
    HIGH = "high"  # Schedule within 24 hours
    MEDIUM = "medium"  # Schedule within week
    LOW = "low"  # Schedule when capacity available


class StoppingCondition(str, Enum):
    """Early stopping conditions for experiments."""
    STATISTICAL_SIGNIFICANCE = "statistical_significance"  # Significant difference found
    NO_IMPROVEMENT = "no_improvement"  # No improvement detected
    DEGRADATION = "degradation"  # Performance worse than control
    MAX_DURATION = "max_duration"  # Time limit reached
    MAX_TRIALS = "max_trials"  # Trial limit reached


@dataclass
class ImprovementOpportunity:
    """Represents a detected improvement opportunity."""
    agent_id: str
    opportunity_type: ImprovementOpportunityType
    priority: ExperimentPriority
    current_performance: float  # Current success rate
    expected_improvement: float  # Expected improvement %
    confidence: float  # Confidence in opportunity (0-1)
    description: str
    recommended_variants: List[str]
    metadata: Dict[str, Any]


@dataclass
class ExperimentHypothesis:
    """Generated experiment hypothesis."""
    agent_id: str
    feature_name: str
    hypothesis: str
    control_description: str
    treatment_description: str
    success_criteria: str
    estimated_impact: float  # Expected improvement %
    confidence: float  # Confidence in hypothesis (0-1)
    metadata: Dict[str, Any]


@dataclass
class ScheduledExperiment:
    """Scheduled experiment details."""
    experiment_id: UUID
    agent_id: str
    scheduled_at: datetime
    start_at: datetime
    priority: ExperimentPriority
    hypothesis: ExperimentHypothesis
    status: str


@dataclass
class StoppingDecision:
    """Decision about stopping an experiment."""
    should_stop: bool
    condition: Optional[StoppingCondition]
    reason: str
    winner_variant_id: Optional[UUID]
    confidence: float


# ============================================================================
# EXPERIMENT SCHEDULER SERVICE
# ============================================================================

class ExperimentSchedulerService:
    """
    Automatic experiment scheduling and management service.

    Features:
    - Detect improvement opportunities from performance metrics
    - Generate experiment hypotheses using LLM
    - Schedule experiments automatically based on priority
    - Execute scheduled experiments
    - Check early stopping conditions
    - Auto-create baseline experiments for new agents
    """

    def __init__(self, db: AsyncSession):
        """Initialize scheduler service."""
        self.db = db
        self.dashboard_service = EvolutionDashboardService(db)
        self.ab_testing_service = ABTestingService(db)
        self.scheduler: Optional[AsyncIOScheduler] = None

        # Configuration
        self.config = {
            "performance_threshold": 75.0,  # Target success rate
            "decline_threshold": -5.0,  # % decline to trigger experiment
            "win_rate_threshold": 50.0,  # Target win rate
            "variance_threshold": 15.0,  # Max acceptable variance
            "min_trials_for_significance": 30,  # Min trials for statistical test
            "significance_level": 0.05,  # p-value threshold
            "min_improvement": 5.0,  # Min % improvement to declare winner
            "max_experiment_duration_days": 14,  # Max experiment duration
            "max_concurrent_experiments": 5,  # Max experiments per agent
        }

    # ========================================================================
    # OPPORTUNITY DETECTION
    # ========================================================================

    async def detect_improvement_opportunity(
        self,
        agent_id: str,
        time_range: TimeRange = TimeRange.THIRTY_DAYS
    ) -> Optional[ImprovementOpportunity]:
        """
        Detect improvement opportunities for a specific agent.

        Analyzes:
        - Success rate vs peers (performance gap)
        - Trend direction (declining performance)
        - Win rate in experiments (low wins)
        - Performance variance (inconsistency)

        Args:
            agent_id: Agent to analyze
            time_range: Time range for analysis

        Returns:
            ImprovementOpportunity if found, None otherwise
        """
        # Get agent performance metrics
        metrics = await self.dashboard_service.get_agent_performance_trends(
            agent_id, time_range
        )

        # Get all agents for comparison
        all_agents = await self.dashboard_service.get_all_agents_performance(time_range)
        avg_success_rate = statistics.mean([a.success_rate for a in all_agents])

        # Check for performance gap
        if metrics.success_rate < self.config["performance_threshold"]:
            gap = self.config["performance_threshold"] - metrics.success_rate
            return ImprovementOpportunity(
                agent_id=agent_id,
                opportunity_type=ImprovementOpportunityType.PERFORMANCE_GAP,
                priority=self._calculate_priority(gap, metrics.success_rate),
                current_performance=metrics.success_rate,
                expected_improvement=gap * 0.5,  # Conservative estimate
                confidence=0.8,
                description=f"{agent_id} success rate ({metrics.success_rate:.1f}%) below target ({self.config['performance_threshold']}%)",
                recommended_variants=["enhanced_validation", "improved_error_handling"],
                metadata={
                    "gap": gap,
                    "target": self.config["performance_threshold"],
                    "peer_average": avg_success_rate
                }
            )

        # Check for declining trend
        if metrics.trend_direction == TrendDirection.DECLINING:
            return ImprovementOpportunity(
                agent_id=agent_id,
                opportunity_type=ImprovementOpportunityType.DECLINING_TREND,
                priority=ExperimentPriority.HIGH,
                current_performance=metrics.success_rate,
                expected_improvement=abs(metrics.improvement_rate),
                confidence=0.75,
                description=f"{agent_id} performance declining at {metrics.improvement_rate:.1f}% rate",
                recommended_variants=["revert_recent_changes", "alternative_approach"],
                metadata={
                    "improvement_rate": metrics.improvement_rate,
                    "trend": metrics.trend_direction.value
                }
            )

        # Check for low win rate
        if metrics.win_rate < self.config["win_rate_threshold"]:
            return ImprovementOpportunity(
                agent_id=agent_id,
                opportunity_type=ImprovementOpportunityType.LOW_WIN_RATE,
                priority=ExperimentPriority.MEDIUM,
                current_performance=metrics.win_rate,
                expected_improvement=20.0,  # Target 20% improvement
                confidence=0.7,
                description=f"{agent_id} win rate ({metrics.win_rate:.1f}%) below target ({self.config['win_rate_threshold']}%)",
                recommended_variants=["strategy_optimization", "parameter_tuning"],
                metadata={
                    "win_rate": metrics.win_rate,
                    "experiments_participated": metrics.experiments_participated,
                    "experiments_won": metrics.experiments_won
                }
            )

        return None

    async def detect_all_opportunities(
        self,
        time_range: TimeRange = TimeRange.THIRTY_DAYS
    ) -> List[ImprovementOpportunity]:
        """
        Detect improvement opportunities for all agents.

        Returns:
            List of improvement opportunities, sorted by priority
        """
        opportunities = []

        # Get all agents
        all_agents = await self.dashboard_service.get_all_agents_performance(time_range)

        # Check each agent
        for agent_metrics in all_agents:
            opportunity = await self.detect_improvement_opportunity(
                agent_metrics.agent_id, time_range
            )
            if opportunity:
                opportunities.append(opportunity)

        # Sort by priority (critical > high > medium > low)
        priority_order = {
            ExperimentPriority.CRITICAL: 0,
            ExperimentPriority.HIGH: 1,
            ExperimentPriority.MEDIUM: 2,
            ExperimentPriority.LOW: 3
        }
        opportunities.sort(key=lambda o: priority_order[o.priority])

        return opportunities

    def _calculate_priority(self, gap: float, current_rate: float) -> ExperimentPriority:
        """Calculate experiment priority based on performance gap."""
        if current_rate < 50.0 or gap > 30.0:
            return ExperimentPriority.CRITICAL
        elif gap > 20.0:
            return ExperimentPriority.HIGH
        elif gap > 10.0:
            return ExperimentPriority.MEDIUM
        else:
            return ExperimentPriority.LOW

    # ========================================================================
    # HYPOTHESIS GENERATION
    # ========================================================================

    async def generate_experiment_hypothesis(
        self,
        opportunity: ImprovementOpportunity
    ) -> ExperimentHypothesis:
        """
        Generate experiment hypothesis from improvement opportunity.

        Uses LLM to generate:
        - Feature name
        - Hypothesis statement
        - Control and treatment descriptions
        - Success criteria

        Args:
            opportunity: Detected improvement opportunity

        Returns:
            Generated experiment hypothesis
        """
        # For now, generate rule-based hypothesis
        # TODO: Integrate with LLM for more sophisticated generation

        if opportunity.opportunity_type == ImprovementOpportunityType.PERFORMANCE_GAP:
            return ExperimentHypothesis(
                agent_id=opportunity.agent_id,
                feature_name="enhanced_validation",
                hypothesis=f"Adding enhanced input validation will improve {opportunity.agent_id} success rate from {opportunity.current_performance:.1f}% to {opportunity.current_performance + opportunity.expected_improvement:.1f}%",
                control_description="Current validation approach",
                treatment_description="Enhanced validation with edge case handling and error recovery",
                success_criteria=f"Success rate improvement > {self.config['min_improvement']}% with p < {self.config['significance_level']}",
                estimated_impact=opportunity.expected_improvement,
                confidence=opportunity.confidence,
                metadata={
                    "opportunity_type": opportunity.opportunity_type.value,
                    "current_performance": opportunity.current_performance,
                    "recommended_variants": opportunity.recommended_variants
                }
            )

        elif opportunity.opportunity_type == ImprovementOpportunityType.DECLINING_TREND:
            return ExperimentHypothesis(
                agent_id=opportunity.agent_id,
                feature_name="trend_reversal",
                hypothesis=f"Reverting recent changes or trying alternative approach will reverse declining trend for {opportunity.agent_id}",
                control_description="Current approach (declining performance)",
                treatment_description="Alternative approach or revert to previous stable version",
                success_criteria=f"Trend direction changes to stable or improving",
                estimated_impact=opportunity.expected_improvement,
                confidence=opportunity.confidence,
                metadata={
                    "opportunity_type": opportunity.opportunity_type.value,
                    "improvement_rate": opportunity.metadata.get("improvement_rate", 0)
                }
            )

        elif opportunity.opportunity_type == ImprovementOpportunityType.LOW_WIN_RATE:
            return ExperimentHypothesis(
                agent_id=opportunity.agent_id,
                feature_name="strategy_optimization",
                hypothesis=f"Optimizing decision strategy will improve {opportunity.agent_id} win rate from {opportunity.current_performance:.1f}% to {opportunity.current_performance + opportunity.expected_improvement:.1f}%",
                control_description="Current decision strategy",
                treatment_description="Optimized strategy with parameter tuning and heuristics",
                success_criteria=f"Win rate improvement > {self.config['min_improvement']}%",
                estimated_impact=opportunity.expected_improvement,
                confidence=opportunity.confidence,
                metadata={
                    "opportunity_type": opportunity.opportunity_type.value,
                    "win_rate": opportunity.current_performance
                }
            )

        else:
            # Default hypothesis
            return ExperimentHypothesis(
                agent_id=opportunity.agent_id,
                feature_name="general_improvement",
                hypothesis=f"General improvements will enhance {opportunity.agent_id} performance",
                control_description="Current implementation",
                treatment_description="Improved implementation",
                success_criteria="Performance improvement detected",
                estimated_impact=opportunity.expected_improvement,
                confidence=opportunity.confidence,
                metadata={
                    "opportunity_type": opportunity.opportunity_type.value
                }
            )

    # ========================================================================
    # EXPERIMENT SCHEDULING
    # ========================================================================

    async def schedule_performance_experiment(
        self,
        hypothesis: ExperimentHypothesis,
        priority: ExperimentPriority = ExperimentPriority.MEDIUM
    ) -> ScheduledExperiment:
        """
        Schedule a performance improvement experiment.

        Args:
            hypothesis: Generated experiment hypothesis
            priority: Scheduling priority

        Returns:
            Scheduled experiment details
        """
        # Calculate start time based on priority
        now = datetime.utcnow()
        if priority == ExperimentPriority.CRITICAL:
            start_at = now + timedelta(minutes=5)  # Start immediately
        elif priority == ExperimentPriority.HIGH:
            start_at = now + timedelta(hours=1)
        elif priority == ExperimentPriority.MEDIUM:
            start_at = now + timedelta(hours=24)
        else:
            start_at = now + timedelta(days=7)

        # Create experiment using AB Testing service
        experiment = await self.ab_testing_service.create_experiment(
            agent_id=hypothesis.agent_id,
            feature_name=hypothesis.feature_name,
            description=hypothesis.hypothesis,
            variants=[
                {
                    "variant_name": "control",
                    "description": hypothesis.control_description,
                    "traffic_percentage": 50.0,
                    "config_json": {"is_control": True},
                    "is_control": True
                },
                {
                    "variant_name": "treatment",
                    "description": hypothesis.treatment_description,
                    "traffic_percentage": 50.0,
                    "config_json": {"enhanced": True},
                    "is_control": False
                }
            ]
        )

        scheduled = ScheduledExperiment(
            experiment_id=experiment.id,
            agent_id=hypothesis.agent_id,
            scheduled_at=now,
            start_at=start_at,
            priority=priority,
            hypothesis=hypothesis,
            status="SCHEDULED"
        )

        return scheduled

    async def auto_create_baseline_experiments(
        self,
        agent_id: str
    ) -> List[ScheduledExperiment]:
        """
        Auto-create baseline experiments for a new agent.

        Creates experiments to establish performance baselines:
        - Default vs optimized parameters
        - Different prompting strategies
        - Various context window sizes

        Args:
            agent_id: New agent to create baselines for

        Returns:
            List of scheduled baseline experiments
        """
        scheduled_experiments = []

        # Baseline experiment 1: Parameter optimization
        hypothesis1 = ExperimentHypothesis(
            agent_id=agent_id,
            feature_name="parameter_baseline",
            hypothesis=f"Establish optimal parameter configuration for {agent_id}",
            control_description="Default parameters",
            treatment_description="Optimized parameters (temperature, top_p, etc.)",
            success_criteria="Performance difference > 5%",
            estimated_impact=10.0,
            confidence=0.6,
            metadata={"baseline_type": "parameters"}
        )

        exp1 = await self.schedule_performance_experiment(
            hypothesis1, ExperimentPriority.MEDIUM
        )
        scheduled_experiments.append(exp1)

        # Baseline experiment 2: Prompting strategy
        hypothesis2 = ExperimentHypothesis(
            agent_id=agent_id,
            feature_name="prompting_baseline",
            hypothesis=f"Determine best prompting strategy for {agent_id}",
            control_description="Standard prompting",
            treatment_description="Chain-of-thought prompting",
            success_criteria="Quality improvement detected",
            estimated_impact=8.0,
            confidence=0.65,
            metadata={"baseline_type": "prompting"}
        )

        exp2 = await self.schedule_performance_experiment(
            hypothesis2, ExperimentPriority.MEDIUM
        )
        scheduled_experiments.append(exp2)

        return scheduled_experiments

    # ========================================================================
    # EXPERIMENT EXECUTION
    # ========================================================================

    async def execute_scheduled_experiments(self) -> List[UUID]:
        """
        Execute scheduled experiments that are due to start.

        Checks all scheduled experiments and starts those whose
        start_at time has passed.

        Returns:
            List of started experiment IDs
        """
        now = datetime.utcnow()
        started_experiments = []

        # Query scheduled experiments
        # For now, query all pending experiments
        query = select(Experiment).where(
            Experiment.status == ExperimentStatus.PENDING
        )
        result = await self.db.execute(query)
        pending = result.scalars().all()

        for experiment in pending:
            # Check if it's time to start
            # (In real implementation, we'd store scheduled_at in a separate table)
            # For now, start all pending experiments
            await self.ab_testing_service.start_experiment(str(experiment.id))
            started_experiments.append(experiment.id)

        return started_experiments

    # ========================================================================
    # STOPPING CONDITIONS
    # ========================================================================

    async def check_experiment_stopping_conditions(
        self,
        experiment_id: str
    ) -> StoppingDecision:
        """
        Check if experiment should be stopped early.

        Checks for:
        - Statistical significance reached
        - No improvement detected
        - Performance degradation
        - Max duration reached
        - Max trials reached

        Args:
            experiment_id: Experiment to check

        Returns:
            Decision about stopping experiment
        """
        # Get experiment results
        results = await self.ab_testing_service.get_experiment_results(experiment_id)

        if not results:
            return StoppingDecision(
                should_stop=False,
                condition=None,
                reason="Insufficient data",
                winner_variant_id=None,
                confidence=0.0
            )

        experiment = results["experiment"]
        control = results["control"]
        treatment = results["treatment"]

        # Check max duration
        if experiment.started_at:
            duration_days = (datetime.utcnow() - experiment.started_at).days
            if duration_days >= self.config["max_experiment_duration_days"]:
                return StoppingDecision(
                    should_stop=True,
                    condition=StoppingCondition.MAX_DURATION,
                    reason=f"Max duration ({self.config['max_experiment_duration_days']} days) reached",
                    winner_variant_id=self._determine_winner(control, treatment),
                    confidence=0.8
                )

        # Check for statistical significance
        if (control["total_trials"] >= self.config["min_trials_for_significance"] and
            treatment["total_trials"] >= self.config["min_trials_for_significance"]):

            # Calculate improvement
            improvement = ((treatment["success_rate"] - control["success_rate"]) /
                          control["success_rate"] * 100 if control["success_rate"] > 0 else 0)

            # Check if significant improvement
            if abs(improvement) >= self.config["min_improvement"]:
                winner_id = treatment["variant_id"] if improvement > 0 else control["variant_id"]
                return StoppingDecision(
                    should_stop=True,
                    condition=StoppingCondition.STATISTICAL_SIGNIFICANCE,
                    reason=f"Significant difference detected: {improvement:.1f}% improvement",
                    winner_variant_id=UUID(winner_id),
                    confidence=0.9
                )

        # Check for degradation
        if treatment["success_rate"] < control["success_rate"] * 0.9:  # >10% worse
            return StoppingDecision(
                should_stop=True,
                condition=StoppingCondition.DEGRADATION,
                reason=f"Treatment performance degraded by {abs((treatment['success_rate'] - control['success_rate']))}%",
                winner_variant_id=UUID(control["variant_id"]),
                confidence=0.85
            )

        # Continue experiment
        return StoppingDecision(
            should_stop=False,
            condition=None,
            reason="Continue collecting data",
            winner_variant_id=None,
            confidence=0.0
        )

    def _determine_winner(
        self,
        control: Dict[str, Any],
        treatment: Dict[str, Any]
    ) -> UUID:
        """Determine winner variant based on success rate."""
        if treatment["success_rate"] > control["success_rate"]:
            return UUID(treatment["variant_id"])
        else:
            return UUID(control["variant_id"])

    # ========================================================================
    # BACKGROUND SCHEDULING
    # ========================================================================

    def start_scheduler(self):
        """Start background scheduler for automatic experiment management."""
        if self.scheduler is not None:
            return  # Already running

        self.scheduler = AsyncIOScheduler()

        # Check for improvement opportunities every 6 hours
        self.scheduler.add_job(
            self._check_opportunities_job,
            CronTrigger(hour="*/6"),
            id="check_opportunities",
            name="Check for improvement opportunities"
        )

        # Execute scheduled experiments every hour
        self.scheduler.add_job(
            self._execute_experiments_job,
            CronTrigger(minute="0"),
            id="execute_experiments",
            name="Execute scheduled experiments"
        )

        # Check stopping conditions every 2 hours
        self.scheduler.add_job(
            self._check_stopping_conditions_job,
            CronTrigger(hour="*/2"),
            id="check_stopping",
            name="Check experiment stopping conditions"
        )

        self.scheduler.start()

    def stop_scheduler(self):
        """Stop background scheduler."""
        if self.scheduler:
            self.scheduler.shutdown()
            self.scheduler = None

    async def _check_opportunities_job(self):
        """Background job to check for improvement opportunities."""
        opportunities = await self.detect_all_opportunities()

        # Auto-schedule high and critical priority experiments
        for opp in opportunities:
            if opp.priority in [ExperimentPriority.CRITICAL, ExperimentPriority.HIGH]:
                hypothesis = await self.generate_experiment_hypothesis(opp)
                await self.schedule_performance_experiment(hypothesis, opp.priority)

    async def _execute_experiments_job(self):
        """Background job to execute scheduled experiments."""
        await self.execute_scheduled_experiments()

    async def _check_stopping_conditions_job(self):
        """Background job to check stopping conditions."""
        # Get all active experiments
        query = select(Experiment).where(
            Experiment.status == ExperimentStatus.ACTIVE
        )
        result = await self.db.execute(query)
        active = result.scalars().all()

        # Check each experiment
        for experiment in active:
            decision = await self.check_experiment_stopping_conditions(str(experiment.id))

            if decision.should_stop and decision.winner_variant_id:
                # Complete experiment with winner
                await self.ab_testing_service.complete_experiment(
                    str(experiment.id),
                    str(decision.winner_variant_id)
                )
