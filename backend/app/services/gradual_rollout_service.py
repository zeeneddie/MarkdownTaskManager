"""
Gradual Rollout Service

Week 53 Day 4: Gradual Rollout System
Manages gradual rollout of experiment winners with automatic rollback on performance degradation.

4-Stage Rollout: 5% → 25% → 50% → 100%

Author: Claude Code (Week 53 Day 4)
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
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.orm import selectinload

from app.models.gradual_rollout import Rollout, RolloutStage, RolloutMetric
from app.models.ab_testing import Experiment, ExperimentVariant
from app.services.evolution_dashboard_service import EvolutionDashboardService, TimeRange


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class RolloutStatus(str, Enum):
    """Rollout status."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ROLLED_BACK = "ROLLED_BACK"


class StageStatus(str, Enum):
    """Stage status."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class RollbackTrigger(str, Enum):
    """Reasons for rollback."""
    PERFORMANCE_DROP = "performance_drop"  # Success rate dropped
    ERROR_SPIKE = "error_spike"  # Error rate too high
    MANUAL = "manual"  # Human-initiated
    TIMEOUT = "timeout"  # Stage took too long
    THRESHOLD_BREACH = "threshold_breach"  # Metric threshold breached


@dataclass
class RolloutConfig:
    """Configuration for gradual rollout."""
    stages: List[float] = None  # Traffic percentages per stage
    stage_duration_minutes: int = 60  # Min duration per stage
    max_performance_drop: float = 10.0  # Max allowed drop (%)
    max_error_rate: float = 5.0  # Max allowed error rate (%)
    min_requests_per_stage: int = 100  # Min requests before advancing
    health_check_interval_seconds: int = 60  # Health check frequency
    auto_advance: bool = True  # Auto-advance to next stage
    auto_rollback: bool = True  # Auto-rollback on failure

    def __post_init__(self):
        if self.stages is None:
            self.stages = [5.0, 25.0, 50.0, 100.0]  # Default 4-stage rollout


@dataclass
class HealthCheckResult:
    """Result of rollout health check."""
    stage_id: UUID
    is_healthy: bool
    success_rate: float
    baseline_success_rate: float
    performance_drop: float
    error_rate: float
    total_requests: int
    recommendations: List[str]
    should_rollback: bool
    rollback_reason: Optional[str]


@dataclass
class RolloutStatusReport:
    """Complete rollout status."""
    rollout_id: UUID
    status: RolloutStatus
    current_stage: int
    current_percentage: float
    total_stages: int
    stages_completed: int
    elapsed_time: Optional[timedelta]
    estimated_time_remaining: Optional[timedelta]
    overall_health: str
    can_advance: bool
    should_rollback: bool


# ============================================================================
# GRADUAL ROLLOUT SERVICE
# ============================================================================

class GradualRolloutService:
    """
    Gradual rollout service for safe deployment of experiment winners.

    Features:
    - 4-stage gradual rollout (5% → 25% → 50% → 100%)
    - Continuous health monitoring
    - Automatic rollback on performance degradation
    - Configurable thresholds and stages
    - Metrics collection and analysis
    """

    def __init__(self, db: AsyncSession, config: Optional[RolloutConfig] = None):
        """Initialize rollout service."""
        self.db = db
        self.config = config or RolloutConfig()
        self.dashboard_service = EvolutionDashboardService(db)

    # ========================================================================
    # ROLLOUT INITIATION
    # ========================================================================

    async def start_rollout(
        self,
        experiment_id: UUID,
        variant_id: UUID,
        agent_id: str,
        feature_name: str,
        config: Optional[RolloutConfig] = None
    ) -> Rollout:
        """
        Start gradual rollout of experiment winner.

        Args:
            experiment_id: Experiment that was won
            variant_id: Winning variant to roll out
            agent_id: Agent receiving the rollout
            feature_name: Feature being rolled out
            config: Optional custom rollout configuration

        Returns:
            Created rollout object
        """
        rollout_config = config or self.config

        # Create rollout
        rollout = Rollout(
            id=uuid4(),
            experiment_id=experiment_id,
            variant_id=variant_id,
            agent_id=agent_id,
            feature_name=feature_name,
            current_stage=0,
            current_percentage=0.0,
            status=RolloutStatus.PENDING.value,
            metadata={
                "config": {
                    "stages": rollout_config.stages,
                    "stage_duration_minutes": rollout_config.stage_duration_minutes,
                    "max_performance_drop": rollout_config.max_performance_drop,
                    "max_error_rate": rollout_config.max_error_rate,
                    "auto_advance": rollout_config.auto_advance,
                    "auto_rollback": rollout_config.auto_rollback
                }
            }
        )

        self.db.add(rollout)
        await self.db.flush()

        # Create stages
        for i, percentage in enumerate(rollout_config.stages):
            stage = RolloutStage(
                id=uuid4(),
                rollout_id=rollout.id,
                stage_number=i,
                traffic_percentage=percentage,
                status=StageStatus.PENDING.value,
                metadata={}
            )
            self.db.add(stage)

        await self.db.commit()
        await self.db.refresh(rollout)

        # Start first stage
        await self._start_stage(rollout, 0)

        return rollout

    async def _start_stage(self, rollout: Rollout, stage_number: int) -> RolloutStage:
        """Start a specific rollout stage."""
        # Get stage
        query = select(RolloutStage).where(
            and_(
                RolloutStage.rollout_id == rollout.id,
                RolloutStage.stage_number == stage_number
            )
        )
        result = await self.db.execute(query)
        stage = result.scalar_one()

        # Get baseline performance
        metrics = await self.dashboard_service.get_agent_performance_trends(
            rollout.agent_id,
            TimeRange.SEVEN_DAYS
        )
        baseline_success_rate = metrics.success_rate

        # Update stage
        stage.status = StageStatus.ACTIVE.value
        stage.started_at = datetime.now(timezone.utc)
        stage.baseline_success_rate = baseline_success_rate

        # Update rollout
        rollout.current_stage = stage_number
        rollout.current_percentage = stage.traffic_percentage
        rollout.status = RolloutStatus.ACTIVE.value
        if stage_number == 0:
            rollout.started_at = datetime.now(timezone.utc)

        await self.db.commit()

        return stage

    # ========================================================================
    # STAGE ADVANCEMENT
    # ========================================================================

    async def advance_to_next_stage(
        self,
        rollout_id: UUID
    ) -> Optional[RolloutStage]:
        """
        Advance rollout to next stage if current stage is healthy.

        Args:
            rollout_id: Rollout to advance

        Returns:
            Next stage if advanced, None if completed or failed
        """
        # Get rollout with stages
        query = select(Rollout).where(
            Rollout.id == rollout_id
        ).options(selectinload(Rollout.stages))
        result = await self.db.execute(query)
        rollout = result.scalar_one_or_none()

        if not rollout:
            return None

        if rollout.status != RolloutStatus.ACTIVE.value:
            return None

        # Get current stage
        current_stage_num = rollout.current_stage
        query = select(RolloutStage).where(
            and_(
                RolloutStage.rollout_id == rollout_id,
                RolloutStage.stage_number == current_stage_num
            )
        )
        result = await self.db.execute(query)
        current_stage = result.scalar_one()

        # Check if current stage is complete
        if current_stage.status != StageStatus.COMPLETED.value:
            # Check if stage can be completed
            health = await self.check_rollout_health(rollout_id)

            if health.should_rollback:
                await self.trigger_rollback(rollout_id, health.rollback_reason)
                return None

            if not health.is_healthy:
                return None

            # Complete current stage
            current_stage.status = StageStatus.COMPLETED.value
            current_stage.completed_at = datetime.now(timezone.utc)
            current_stage.duration_seconds = int(
                (current_stage.completed_at - current_stage.started_at).total_seconds()
            )
            current_stage.health_check_passed = True
            await self.db.commit()

        # Check if this was the last stage
        total_stages = len(rollout.stages)
        if current_stage_num >= total_stages - 1:
            # Rollout complete
            rollout.status = RolloutStatus.COMPLETED.value
            rollout.completed_at = datetime.now(timezone.utc)
            rollout.current_percentage = 100.0
            await self.db.commit()
            return None

        # Start next stage
        next_stage = await self._start_stage(rollout, current_stage_num + 1)
        return next_stage

    # ========================================================================
    # HEALTH MONITORING
    # ========================================================================

    async def check_rollout_health(
        self,
        rollout_id: UUID
    ) -> HealthCheckResult:
        """
        Check health of current rollout stage.

        Monitors:
        - Success rate vs baseline
        - Error rate
        - Performance degradation
        - Request volume

        Args:
            rollout_id: Rollout to check

        Returns:
            Health check result with recommendations
        """
        # Get rollout and current stage
        query = select(Rollout).where(Rollout.id == rollout_id)
        result = await self.db.execute(query)
        rollout = result.scalar_one_or_none()

        if not rollout:
            raise ValueError(f"Rollout {rollout_id} not found")

        query = select(RolloutStage).where(
            and_(
                RolloutStage.rollout_id == rollout_id,
                RolloutStage.stage_number == rollout.current_stage
            )
        )
        result = await self.db.execute(query)
        stage = result.scalar_one()

        # Get current metrics
        metrics = await self.dashboard_service.get_agent_performance_trends(
            rollout.agent_id,
            TimeRange.SEVEN_DAYS
        )
        current_success_rate = metrics.success_rate
        baseline_success_rate = stage.baseline_success_rate or metrics.success_rate

        # Calculate performance drop
        performance_drop = baseline_success_rate - current_success_rate

        # Calculate error rate
        total_requests = stage.total_requests
        failed_requests = stage.failed_requests
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0

        # Update stage metrics
        stage.success_rate = current_success_rate
        stage.performance_drop = performance_drop
        stage.total_requests = total_requests
        stage.failed_requests = failed_requests
        stage.successful_requests = total_requests - failed_requests

        # Check thresholds
        config = RolloutConfig(**rollout.metadata.get("config", {}))
        recommendations = []
        should_rollback = False
        rollback_reason = None

        # Check performance drop
        if performance_drop > config.max_performance_drop:
            recommendations.append(
                f"Performance dropped by {performance_drop:.1f}% (threshold: {config.max_performance_drop}%)"
            )
            should_rollback = True
            rollback_reason = f"Performance drop: {performance_drop:.1f}%"

        # Check error rate
        if error_rate > config.max_error_rate:
            recommendations.append(
                f"Error rate {error_rate:.1f}% exceeds threshold ({config.max_error_rate}%)"
            )
            should_rollback = True
            rollback_reason = f"Error rate too high: {error_rate:.1f}%"

        # Check minimum requests
        if total_requests < config.min_requests_per_stage:
            recommendations.append(
                f"Only {total_requests} requests (need {config.min_requests_per_stage})"
            )

        # Check stage duration
        if stage.started_at:
            duration_minutes = (datetime.now(timezone.utc) - stage.started_at).total_seconds() / 60
            if duration_minutes < config.stage_duration_minutes:
                recommendations.append(
                    f"Stage running for {duration_minutes:.0f} min (need {config.stage_duration_minutes} min)"
                )

        is_healthy = not should_rollback and total_requests >= config.min_requests_per_stage

        await self.db.commit()

        return HealthCheckResult(
            stage_id=stage.id,
            is_healthy=is_healthy,
            success_rate=current_success_rate,
            baseline_success_rate=baseline_success_rate,
            performance_drop=performance_drop,
            error_rate=error_rate,
            total_requests=total_requests,
            recommendations=recommendations,
            should_rollback=should_rollback,
            rollback_reason=rollback_reason
        )

    # ========================================================================
    # ROLLBACK
    # ========================================================================

    async def trigger_rollback(
        self,
        rollout_id: UUID,
        reason: str,
        trigger: RollbackTrigger = RollbackTrigger.MANUAL
    ) -> Rollout:
        """
        Trigger rollback of current rollout.

        Reverts to previous stable version (0% traffic to new variant).

        Args:
            rollout_id: Rollout to roll back
            reason: Reason for rollback
            trigger: What triggered the rollback

        Returns:
            Updated rollout object
        """
        # Get rollout
        query = select(Rollout).where(Rollout.id == rollout_id)
        result = await self.db.execute(query)
        rollout = result.scalar_one_or_none()

        if not rollout:
            raise ValueError(f"Rollout {rollout_id} not found")

        # Update rollout status
        rollout.status = RolloutStatus.ROLLED_BACK.value
        rollout.rolled_back_at = datetime.now(timezone.utc)
        rollout.rollback_reason = f"[{trigger.value}] {reason}"
        rollout.current_percentage = 0.0

        # Mark current stage as rolled back
        if rollout.current_stage is not None:
            query = select(RolloutStage).where(
                and_(
                    RolloutStage.rollout_id == rollout_id,
                    RolloutStage.stage_number == rollout.current_stage
                )
            )
            result = await self.db.execute(query)
            current_stage = result.scalar_one_or_none()

            if current_stage:
                current_stage.status = StageStatus.ROLLED_BACK.value
                current_stage.rollback_triggered = True
                current_stage.rollback_reason = reason
                current_stage.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(rollout)

        return rollout

    # ========================================================================
    # STATUS & REPORTING
    # ========================================================================

    async def get_rollout_status(
        self,
        rollout_id: UUID
    ) -> RolloutStatusReport:
        """
        Get comprehensive rollout status.

        Args:
            rollout_id: Rollout to check

        Returns:
            Complete status report
        """
        # Get rollout with stages
        query = select(Rollout).where(
            Rollout.id == rollout_id
        ).options(selectinload(Rollout.stages))
        result = await self.db.execute(query)
        rollout = result.scalar_one_or_none()

        if not rollout:
            raise ValueError(f"Rollout {rollout_id} not found")

        # Count completed stages
        stages_completed = sum(
            1 for s in rollout.stages
            if s.status == StageStatus.COMPLETED.value
        )
        total_stages = len(rollout.stages)

        # Calculate elapsed time
        elapsed_time = None
        if rollout.started_at:
            if rollout.completed_at:
                elapsed_time = rollout.completed_at - rollout.started_at
            elif rollout.rolled_back_at:
                elapsed_time = rollout.rolled_back_at - rollout.started_at
            else:
                elapsed_time = datetime.now(timezone.utc) - rollout.started_at

        # Estimate time remaining
        estimated_remaining = None
        if (rollout.status == RolloutStatus.ACTIVE.value and
            elapsed_time and stages_completed > 0):
            avg_stage_time = elapsed_time / stages_completed
            remaining_stages = total_stages - stages_completed
            estimated_remaining = avg_stage_time * remaining_stages

        # Overall health
        if rollout.status == RolloutStatus.COMPLETED.value:
            overall_health = "COMPLETED"
        elif rollout.status == RolloutStatus.ROLLED_BACK.value:
            overall_health = "ROLLED_BACK"
        elif rollout.status == RolloutStatus.ACTIVE.value:
            health = await self.check_rollout_health(rollout_id)
            overall_health = "HEALTHY" if health.is_healthy else "DEGRADED"
        else:
            overall_health = "PENDING"

        # Can advance?
        can_advance = False
        should_rollback = False
        if rollout.status == RolloutStatus.ACTIVE.value:
            health = await self.check_rollout_health(rollout_id)
            can_advance = health.is_healthy
            should_rollback = health.should_rollback

        return RolloutStatusReport(
            rollout_id=rollout.id,
            status=RolloutStatus(rollout.status),
            current_stage=rollout.current_stage,
            current_percentage=rollout.current_percentage,
            total_stages=total_stages,
            stages_completed=stages_completed,
            elapsed_time=elapsed_time,
            estimated_time_remaining=estimated_remaining,
            overall_health=overall_health,
            can_advance=can_advance,
            should_rollback=should_rollback
        )

    async def list_active_rollouts(
        self,
        agent_id: Optional[str] = None
    ) -> List[Rollout]:
        """
        List all active rollouts.

        Args:
            agent_id: Optional filter by agent

        Returns:
            List of active rollouts
        """
        query = select(Rollout).where(
            Rollout.status == RolloutStatus.ACTIVE.value
        )

        if agent_id:
            query = query.where(Rollout.agent_id == agent_id)

        query = query.options(selectinload(Rollout.stages))
        query = query.order_by(Rollout.started_at.desc())

        result = await self.db.execute(query)
        return result.scalars().all()

    # ========================================================================
    # METRICS COLLECTION
    # ========================================================================

    async def record_metric(
        self,
        stage_id: UUID,
        metric_name: str,
        metric_value: float,
        threshold_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RolloutMetric:
        """
        Record a metric for a rollout stage.

        Args:
            stage_id: Stage to record metric for
            metric_name: Name of metric
            metric_value: Value of metric
            threshold_value: Optional threshold for breach detection
            metadata: Optional additional data

        Returns:
            Created metric record
        """
        threshold_breached = False
        if threshold_value is not None:
            threshold_breached = metric_value > threshold_value

        metric = RolloutMetric(
            id=uuid4(),
            stage_id=stage_id,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold_value=threshold_value,
            threshold_breached=threshold_breached,
            metadata=metadata or {}
        )

        self.db.add(metric)
        await self.db.commit()
        await self.db.refresh(metric)

        return metric

    async def get_stage_metrics(
        self,
        stage_id: UUID,
        metric_name: Optional[str] = None
    ) -> List[RolloutMetric]:
        """
        Get metrics for a rollout stage.

        Args:
            stage_id: Stage to get metrics for
            metric_name: Optional filter by metric name

        Returns:
            List of metrics
        """
        query = select(RolloutMetric).where(
            RolloutMetric.stage_id == stage_id
        )

        if metric_name:
            query = query.where(RolloutMetric.metric_name == metric_name)

        query = query.order_by(RolloutMetric.timestamp.asc())

        result = await self.db.execute(query)
        return result.scalars().all()
