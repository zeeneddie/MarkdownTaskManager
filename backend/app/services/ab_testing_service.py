"""
A/B Testing Service

Core business logic for managing experiments, traffic allocation,
and statistical analysis.
"""

import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4
import math

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ab_testing import (
    Experiment,
    ExperimentVariant,
    ExperimentResult
)


class ABTestingService:
    """
    Service for managing A/B testing experiments.

    Provides experiment lifecycle management, traffic allocation,
    result tracking, and statistical analysis.
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize service with database session."""
        self.db = db_session

    # ========== EXPERIMENT LIFECYCLE ==========

    async def create_experiment(
        self,
        agent_id: str,
        feature_name: str,
        description: Optional[str],
        variants: List[Dict]
    ) -> Experiment:
        """
        Create new A/B test experiment.

        Args:
            agent_id: Which agent is being tested
            feature_name: Feature being experimented with
            description: Optional description
            variants: List of variant configs [
                {
                    "variant_name": str,
                    "traffic_percentage": float,
                    "config_json": dict,
                    "is_control": bool
                }
            ]

        Returns:
            Created Experiment

        Raises:
            ValueError: If traffic percentages don't sum to 100
        """
        # Validate traffic allocation
        total_traffic = sum(v["traffic_percentage"] for v in variants)
        if abs(total_traffic - 100.0) > 0.01:
            raise ValueError(
                f"Traffic percentages must sum to 100, got {total_traffic}"
            )

        # Ensure exactly one control variant
        control_count = sum(1 for v in variants if v.get("is_control", False))
        if control_count != 1:
            raise ValueError(
                f"Exactly one control variant required, got {control_count}"
            )

        # Create experiment
        experiment = Experiment(
            id=uuid4(),
            agent_id=agent_id,
            feature_name=feature_name,
            description=description,
            status="DRAFT",
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(experiment)
        await self.db.flush()  # Get experiment.id

        # Create variants
        for variant_data in variants:
            variant = ExperimentVariant(
                id=uuid4(),
                experiment_id=experiment.id,
                variant_name=variant_data["variant_name"],
                description=variant_data.get("description"),
                traffic_percentage=variant_data["traffic_percentage"],
                config_json=variant_data["config_json"],
                is_control=variant_data.get("is_control", False),
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(variant)

        await self.db.commit()
        await self.db.refresh(experiment)

        # Load relationships
        result = await self.db.execute(
            select(Experiment)
            .options(selectinload(Experiment.variants))
            .where(Experiment.id == experiment.id)
        )
        return result.scalar_one()

    async def start_experiment(self, experiment_id: UUID) -> Experiment:
        """
        Start an experiment (DRAFT → ACTIVE).

        Args:
            experiment_id: Experiment to start

        Returns:
            Updated experiment

        Raises:
            ValueError: If experiment not in DRAFT status
        """
        result = await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        if experiment.status != "DRAFT":
            raise ValueError(
                f"Can only start DRAFT experiments, got {experiment.status}"
            )

        experiment.status = "ACTIVE"
        experiment.started_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(experiment)

        return experiment

    async def pause_experiment(self, experiment_id: UUID) -> Experiment:
        """
        Pause an active experiment (ACTIVE → PAUSED).

        Args:
            experiment_id: Experiment to pause

        Returns:
            Updated experiment
        """
        result = await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        if experiment.status != "ACTIVE":
            raise ValueError(
                f"Can only pause ACTIVE experiments, got {experiment.status}"
            )

        experiment.status = "PAUSED"

        await self.db.commit()
        await self.db.refresh(experiment)

        return experiment

    async def complete_experiment(
        self,
        experiment_id: UUID,
        winner_variant_id: UUID
    ) -> Experiment:
        """
        Complete an experiment and declare winner (ACTIVE/PAUSED → COMPLETED).

        Args:
            experiment_id: Experiment to complete
            winner_variant_id: Winning variant

        Returns:
            Updated experiment

        Raises:
            ValueError: If winner not in this experiment
        """
        result = await self.db.execute(
            select(Experiment)
            .options(selectinload(Experiment.variants))
            .where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        if experiment.status not in ("ACTIVE", "PAUSED"):
            raise ValueError(
                f"Can only complete ACTIVE/PAUSED experiments, got {experiment.status}"
            )

        # Verify winner variant belongs to this experiment
        variant_ids = [v.id for v in experiment.variants]
        if winner_variant_id not in variant_ids:
            raise ValueError(
                f"Winner variant {winner_variant_id} not in experiment {experiment_id}"
            )

        experiment.status = "COMPLETED"
        experiment.completed_at = datetime.now(timezone.utc)
        experiment.winner_variant_id = winner_variant_id

        await self.db.commit()
        await self.db.refresh(experiment)

        return experiment

    # ========== TRAFFIC ALLOCATION ==========

    async def allocate_traffic(
        self,
        experiment_id: UUID,
        task_id: str
    ) -> ExperimentVariant:
        """
        Allocate task to a variant using deterministic sticky assignment.

        Uses hash(task_id + experiment_id) for consistent assignment.
        Same task always gets same variant.

        Args:
            experiment_id: Active experiment
            task_id: Task to assign

        Returns:
            Assigned variant

        Raises:
            ValueError: If experiment not ACTIVE
        """
        # Get experiment with variants
        result = await self.db.execute(
            select(Experiment)
            .options(selectinload(Experiment.variants))
            .where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        if experiment.status != "ACTIVE":
            raise ValueError(
                f"Can only allocate traffic for ACTIVE experiments, got {experiment.status}"
            )

        if not experiment.variants:
            raise ValueError(f"Experiment {experiment_id} has no variants")

        # Deterministic hash for sticky assignment
        hash_input = f"{task_id}-{experiment_id}"
        hash_value = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)
        random_value = hash_value % 100  # 0-99

        # Weighted random selection
        cumulative = 0.0
        for variant in sorted(experiment.variants, key=lambda v: v.variant_name):
            cumulative += variant.traffic_percentage
            if random_value < cumulative:
                return variant

        # Fallback to first variant (shouldn't happen if traffic sums to 100)
        return experiment.variants[0]

    # ========== RESULT TRACKING ==========

    async def log_result(
        self,
        variant_id: UUID,
        task_id: str,
        success: bool,
        metrics: Dict,
        work_type: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> ExperimentResult:
        """
        Log result from a variant execution.

        Args:
            variant_id: Which variant was used
            task_id: Task identifier
            success: Whether task succeeded
            metrics: Metrics dict (success_rate, execution_time_ms, etc.)
            work_type: Optional work type classification
            error_message: Optional error message if failed

        Returns:
            Created result
        """
        result = ExperimentResult(
            id=uuid4(),
            variant_id=variant_id,
            task_id=task_id,
            work_type=work_type,
            success=success,
            metrics_json=metrics,
            error_message=error_message,
            created_at=datetime.now(timezone.utc)
        )

        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)

        return result

    # ========== STATISTICAL ANALYSIS ==========

    async def analyze_experiment(
        self,
        experiment_id: UUID
    ) -> Dict:
        """
        Perform statistical analysis on experiment results.

        Calculates:
        - Sample size per variant
        - Success rate per variant
        - Confidence intervals (95%)
        - P-value (t-test between control and variants)
        - Recommended winner (if significant)
        - Consensus level (confidence in winner)

        Args:
            experiment_id: Experiment to analyze

        Returns:
            Analysis dict with statistics
        """
        # Get experiment with variants and results
        result = await self.db.execute(
            select(Experiment)
            .options(
                selectinload(Experiment.variants)
                .selectinload(ExperimentVariant.results)
            )
            .where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Calculate statistics per variant
        variant_stats = {}
        control_variant = None

        for variant in experiment.variants:
            results = variant.results
            n = len(results)

            if n == 0:
                variant_stats[str(variant.id)] = {
                    "variant_name": variant.variant_name,
                    "sample_size": 0,
                    "success_rate": 0.0,
                    "confidence_interval": {"lower": 0.0, "upper": 0.0}
                }
                continue

            # Success rate
            successes = sum(1 for r in results if r.success)
            success_rate = successes / n

            # Confidence interval (95%, using normal approximation)
            ci_lower, ci_upper = self._calculate_confidence_interval(
                success_rate, n, confidence_level=0.95
            )

            variant_stats[str(variant.id)] = {
                "variant_name": variant.variant_name,
                "sample_size": n,
                "success_rate": success_rate,
                "confidence_interval": {
                    "lower": ci_lower,
                    "upper": ci_upper
                }
            }

            if variant.is_control:
                control_variant = {
                    "id": str(variant.id),
                    "success_rate": success_rate,
                    "n": n
                }

        # Determine winner and calculate p-value
        recommended_winner = None
        p_value = None
        consensus_level = 0.0

        if control_variant and len(variant_stats) > 1:
            # Compare each variant to control
            best_variant_id = None
            best_improvement = 0.0
            min_p_value = 1.0

            for variant_id, stats in variant_stats.items():
                if stats["variant_name"] == control_variant["id"]:
                    continue  # Skip control

                if stats["sample_size"] < 30:
                    continue  # Need minimum samples

                # Calculate p-value (two-proportion z-test)
                p = self._calculate_p_value(
                    control_success_rate=control_variant["success_rate"],
                    control_n=control_variant["n"],
                    variant_success_rate=stats["success_rate"],
                    variant_n=stats["sample_size"]
                )

                improvement = stats["success_rate"] - control_variant["success_rate"]

                if p < 0.05 and improvement > best_improvement:
                    best_variant_id = variant_id
                    best_improvement = improvement
                    min_p_value = p

            if best_variant_id:
                recommended_winner = best_variant_id
                p_value = min_p_value
                consensus_level = 1.0 - min_p_value  # Higher confidence = lower p-value

        # Check if minimum samples reached
        min_samples_reached = all(
            stats["sample_size"] >= 30
            for stats in variant_stats.values()
        )

        return {
            "experiment_id": str(experiment_id),
            "variant_statistics": variant_stats,
            "p_value": p_value,
            "recommended_winner": recommended_winner,
            "consensus_level": consensus_level,
            "min_samples_reached": min_samples_reached
        }

    def _calculate_confidence_interval(
        self,
        success_rate: float,
        n: int,
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval for success rate.

        Uses normal approximation to binomial distribution.

        Args:
            success_rate: Observed success rate (0-1)
            n: Sample size
            confidence_level: Confidence level (default 0.95 for 95%)

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if n == 0:
            return (0.0, 0.0)

        # Z-score for confidence level (1.96 for 95%)
        z = 1.96 if confidence_level == 0.95 else 2.576  # 99%

        # Standard error
        se = math.sqrt((success_rate * (1 - success_rate)) / n)

        # Margin of error
        margin = z * se

        # Bounds
        lower = max(0.0, success_rate - margin)
        upper = min(1.0, success_rate + margin)

        return (lower, upper)

    def _calculate_p_value(
        self,
        control_success_rate: float,
        control_n: int,
        variant_success_rate: float,
        variant_n: int
    ) -> float:
        """
        Calculate p-value using two-proportion z-test.

        Tests null hypothesis: variant_rate == control_rate

        Args:
            control_success_rate: Control success rate
            control_n: Control sample size
            variant_success_rate: Variant success rate
            variant_n: Variant sample size

        Returns:
            P-value (0-1)
        """
        if control_n == 0 or variant_n == 0:
            return 1.0  # Can't compute

        # Pooled proportion
        pooled_p = (
            (control_success_rate * control_n + variant_success_rate * variant_n)
            / (control_n + variant_n)
        )

        # Standard error
        se = math.sqrt(
            pooled_p * (1 - pooled_p) * (1/control_n + 1/variant_n)
        )

        if se == 0:
            return 1.0

        # Z-score
        z = (variant_success_rate - control_success_rate) / se

        # P-value (two-tailed test, using normal approximation)
        # This is a simplified calculation; for production use scipy.stats
        p_value = 2 * (1 - self._normal_cdf(abs(z)))

        return p_value

    def _normal_cdf(self, z: float) -> float:
        """
        Cumulative distribution function for standard normal distribution.

        Approximation using error function.

        Args:
            z: Z-score

        Returns:
            Probability (0-1)
        """
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))

    # ========== QUERY METHODS ==========

    async def get_experiment(self, experiment_id: UUID) -> Optional[Experiment]:
        """Get experiment by ID with variants loaded."""
        result = await self.db.execute(
            select(Experiment)
            .options(selectinload(Experiment.variants))
            .where(Experiment.id == experiment_id)
        )
        return result.scalar_one_or_none()

    async def list_experiments(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Experiment]:
        """
        List experiments with optional filters.

        Args:
            agent_id: Filter by agent
            status: Filter by status

        Returns:
            List of experiments
        """
        query = select(Experiment).options(selectinload(Experiment.variants))

        filters = []
        if agent_id:
            filters.append(Experiment.agent_id == agent_id)
        if status:
            filters.append(Experiment.status == status)

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(Experiment.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())
