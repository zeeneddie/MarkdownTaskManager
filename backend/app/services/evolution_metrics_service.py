"""
Evolution Metrics Service

Tracks agent performance over time, aggregates metrics,
and stores evolution milestones in ChromaDB.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID
import statistics

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ab_testing import (
    Experiment,
    ExperimentVariant,
    ExperimentResult
)


class EvolutionMetricsService:
    """
    Service for tracking agent evolution over time.

    Provides performance metrics, trend analysis,
    and evolution milestone tracking.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        chroma_client=None  # Optional ChromaDB client
    ):
        """Initialize service with database and optional ChromaDB."""
        self.db = db_session
        self.chroma = chroma_client

    # ========== AGENT PERFORMANCE METRICS ==========

    async def get_agent_performance(
        self,
        agent_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get performance metrics for an agent over time.

        Args:
            agent_id: Agent to analyze (e.g., "felix", "marcus")
            start_date: Start of analysis period (default: 30 days ago)
            end_date: End of analysis period (default: now)

        Returns:
            Dict with performance metrics:
            - total_experiments: Number of experiments
            - active_experiments: Currently running
            - completed_experiments: Finished experiments
            - average_success_rate: Across all experiments
            - total_tasks: Number of tasks tested
            - improvement_rate: % improvement from control
            - best_variant: Top performing variant
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        # Get all experiments for this agent in date range
        result = await self.db.execute(
            select(Experiment)
            .options(
                selectinload(Experiment.variants)
                .selectinload(ExperimentVariant.results)
            )
            .where(
                and_(
                    Experiment.agent_id == agent_id,
                    Experiment.created_at >= start_date,
                    Experiment.created_at <= end_date
                )
            )
        )
        experiments = list(result.scalars().all())

        if not experiments:
            return {
                "agent_id": agent_id,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "total_experiments": 0,
                "active_experiments": 0,
                "completed_experiments": 0,
                "average_success_rate": 0.0,
                "total_tasks": 0,
                "improvement_rate": 0.0,
                "best_variant": None
            }

        # Calculate metrics
        total_experiments = len(experiments)
        active_experiments = sum(1 for exp in experiments if exp.status == "ACTIVE")
        completed_experiments = sum(1 for exp in experiments if exp.status == "COMPLETED")

        # Calculate success rates
        all_results = []
        control_results = []
        variant_results = []

        for experiment in experiments:
            for variant in experiment.variants:
                for result in variant.results:
                    all_results.append(result)
                    if variant.is_control:
                        control_results.append(result)
                    else:
                        variant_results.append(result)

        total_tasks = len(all_results)
        average_success_rate = (
            sum(1 for r in all_results if r.success) / total_tasks
            if total_tasks > 0 else 0.0
        )

        # Calculate improvement rate (variant vs control)
        improvement_rate = 0.0
        if control_results and variant_results:
            control_success = sum(1 for r in control_results if r.success) / len(control_results)
            variant_success = sum(1 for r in variant_results if r.success) / len(variant_results)
            improvement_rate = ((variant_success - control_success) / control_success) * 100

        # Find best variant
        best_variant = None
        best_success_rate = 0.0

        for experiment in experiments:
            for variant in experiment.variants:
                if not variant.results:
                    continue
                success_rate = sum(1 for r in variant.results if r.success) / len(variant.results)
                if success_rate > best_success_rate:
                    best_success_rate = success_rate
                    best_variant = {
                        "variant_id": str(variant.id),
                        "variant_name": variant.variant_name,
                        "experiment_id": str(variant.experiment_id),
                        "success_rate": success_rate,
                        "sample_size": len(variant.results)
                    }

        return {
            "agent_id": agent_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_experiments": total_experiments,
            "active_experiments": active_experiments,
            "completed_experiments": completed_experiments,
            "average_success_rate": average_success_rate,
            "total_tasks": total_tasks,
            "improvement_rate": improvement_rate,
            "best_variant": best_variant
        }

    # ========== TREND ANALYSIS ==========

    async def analyze_trends(
        self,
        agent_id: str,
        metric: str = "success_rate",
        days: int = 30
    ) -> Dict:
        """
        Analyze trends for an agent over time.

        Args:
            agent_id: Agent to analyze
            metric: Metric to track (success_rate, execution_time_ms, code_quality_score)
            days: Number of days to analyze

        Returns:
            Dict with trend data:
            - daily_values: List of {date, value} pairs
            - trend_direction: "improving", "stable", "declining"
            - trend_percentage: % change over period
            - average_value: Mean across period
            - std_dev: Standard deviation
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Get all results for agent in period
        result = await self.db.execute(
            select(ExperimentResult)
            .join(ExperimentVariant)
            .join(Experiment)
            .where(
                and_(
                    Experiment.agent_id == agent_id,
                    ExperimentResult.created_at >= start_date
                )
            )
            .order_by(ExperimentResult.created_at)
        )
        results = list(result.scalars().all())

        if not results:
            return {
                "agent_id": agent_id,
                "metric": metric,
                "period_days": days,
                "daily_values": [],
                "trend_direction": "stable",
                "trend_percentage": 0.0,
                "average_value": 0.0,
                "std_dev": 0.0
            }

        # Group by day
        daily_data: Dict[str, List[float]] = {}

        for result_obj in results:
            date_key = result_obj.created_at.strftime("%Y-%m-%d")

            if date_key not in daily_data:
                daily_data[date_key] = []

            # Extract metric value
            if metric == "success_rate":
                value = 1.0 if result_obj.success else 0.0
            else:
                value = result_obj.metrics_json.get(metric, 0.0)

            daily_data[date_key].append(value)

        # Calculate daily averages
        daily_values = [
            {
                "date": date_key,
                "value": statistics.mean(values)
            }
            for date_key, values in sorted(daily_data.items())
        ]

        # Calculate overall statistics
        all_values = [dv["value"] for dv in daily_values]
        average_value = statistics.mean(all_values)
        std_dev = statistics.stdev(all_values) if len(all_values) > 1 else 0.0

        # Calculate trend
        if len(daily_values) < 2:
            trend_direction = "stable"
            trend_percentage = 0.0
        else:
            first_value = daily_values[0]["value"]
            last_value = daily_values[-1]["value"]

            if first_value == 0:
                trend_percentage = 0.0
            else:
                trend_percentage = ((last_value - first_value) / first_value) * 100

            if abs(trend_percentage) < 5:
                trend_direction = "stable"
            elif trend_percentage > 0:
                trend_direction = "improving"
            else:
                trend_direction = "declining"

        return {
            "agent_id": agent_id,
            "metric": metric,
            "period_days": days,
            "daily_values": daily_values,
            "trend_direction": trend_direction,
            "trend_percentage": trend_percentage,
            "average_value": average_value,
            "std_dev": std_dev
        }

    # ========== AGGREGATION ==========

    async def aggregate_metrics(
        self,
        agent_id: str,
        period: str = "daily"  # daily, weekly
    ) -> List[Dict]:
        """
        Aggregate metrics by period.

        Args:
            agent_id: Agent to aggregate
            period: Aggregation period (daily, weekly)

        Returns:
            List of aggregated metrics per period
        """
        if period == "daily":
            days = 30
            group_by_days = 1
        elif period == "weekly":
            days = 90
            group_by_days = 7
        else:
            raise ValueError(f"Invalid period: {period}")

        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Get all results for agent
        result = await self.db.execute(
            select(ExperimentResult)
            .join(ExperimentVariant)
            .join(Experiment)
            .where(
                and_(
                    Experiment.agent_id == agent_id,
                    ExperimentResult.created_at >= start_date
                )
            )
            .order_by(ExperimentResult.created_at)
        )
        results = list(result.scalars().all())

        # Group by period
        period_data: Dict[str, List[ExperimentResult]] = {}

        for result_obj in results:
            # Calculate period key
            if period == "daily":
                period_key = result_obj.created_at.strftime("%Y-%m-%d")
            else:  # weekly
                # Get ISO week number
                iso_cal = result_obj.created_at.isocalendar()
                period_key = f"{iso_cal[0]}-W{iso_cal[1]:02d}"

            if period_key not in period_data:
                period_data[period_key] = []

            period_data[period_key].append(result_obj)

        # Aggregate each period
        aggregated = []

        for period_key, period_results in sorted(period_data.items()):
            total_tasks = len(period_results)
            successes = sum(1 for r in period_results if r.success)
            success_rate = successes / total_tasks if total_tasks > 0 else 0.0

            # Average metrics
            execution_times = [
                r.metrics_json.get("execution_time_ms", 0)
                for r in period_results
                if "execution_time_ms" in r.metrics_json
            ]
            avg_execution_time = (
                statistics.mean(execution_times)
                if execution_times else 0.0
            )

            code_quality_scores = [
                r.metrics_json.get("code_quality_score", 0)
                for r in period_results
                if "code_quality_score" in r.metrics_json
            ]
            avg_code_quality = (
                statistics.mean(code_quality_scores)
                if code_quality_scores else 0.0
            )

            aggregated.append({
                "period": period_key,
                "total_tasks": total_tasks,
                "success_count": successes,
                "success_rate": success_rate,
                "avg_execution_time_ms": avg_execution_time,
                "avg_code_quality_score": avg_code_quality
            })

        return aggregated

    # ========== CROSS-AGENT COMPARISON ==========

    async def compare_agents(
        self,
        agent_ids: List[str],
        days: int = 30
    ) -> Dict:
        """
        Compare performance across multiple agents.

        Args:
            agent_ids: List of agents to compare
            days: Number of days to analyze

        Returns:
            Dict with comparison data per agent
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        comparison = {}

        for agent_id in agent_ids:
            perf = await self.get_agent_performance(
                agent_id=agent_id,
                start_date=start_date
            )
            comparison[agent_id] = perf

        # Add rankings
        sorted_by_success = sorted(
            comparison.items(),
            key=lambda x: x[1]["average_success_rate"],
            reverse=True
        )

        for rank, (agent_id, _) in enumerate(sorted_by_success, start=1):
            comparison[agent_id]["success_rate_rank"] = rank

        sorted_by_improvement = sorted(
            comparison.items(),
            key=lambda x: x[1]["improvement_rate"],
            reverse=True
        )

        for rank, (agent_id, _) in enumerate(sorted_by_improvement, start=1):
            comparison[agent_id]["improvement_rank"] = rank

        return comparison

    # ========== CHROMADB INTEGRATION ==========

    async def store_evolution_milestone(
        self,
        agent_id: str,
        milestone_type: str,
        description: str,
        metrics: Dict,
        experiment_id: Optional[UUID] = None
    ) -> bool:
        """
        Store evolution milestone in ChromaDB.

        Milestones represent significant agent improvements:
        - First successful experiment
        - 10% improvement threshold crossed
        - New best variant discovered
        - Consistent performance (7 days stable)

        Args:
            agent_id: Agent identifier
            milestone_type: Type of milestone (first_success, improvement_threshold, etc.)
            description: Human-readable description
            metrics: Associated metrics
            experiment_id: Optional related experiment

        Returns:
            True if stored successfully
        """
        if not self.chroma:
            # ChromaDB not configured, skip
            return False

        try:
            # Get or create collection
            collection = self.chroma.get_or_create_collection(
                name="agent_evolution_milestones"
            )

            # Create document
            document = f"""
            Agent: {agent_id}
            Milestone: {milestone_type}
            Description: {description}
            Date: {datetime.now(timezone.utc).isoformat()}

            Metrics:
            {self._format_metrics(metrics)}
            """

            # Store in ChromaDB
            collection.add(
                documents=[document],
                metadatas=[{
                    "agent_id": agent_id,
                    "milestone_type": milestone_type,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "experiment_id": str(experiment_id) if experiment_id else None,
                    **metrics
                }],
                ids=[f"{agent_id}_{milestone_type}_{datetime.now(timezone.utc).timestamp()}"]
            )

            return True

        except Exception as e:
            print(f"Failed to store milestone in ChromaDB: {e}")
            return False

    async def retrieve_evolution_milestones(
        self,
        agent_id: str,
        milestone_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Retrieve evolution milestones from ChromaDB.

        Args:
            agent_id: Agent to retrieve milestones for
            milestone_type: Optional filter by type
            limit: Maximum number of milestones to return

        Returns:
            List of milestone dictionaries
        """
        if not self.chroma:
            return []

        try:
            collection = self.chroma.get_or_create_collection(
                name="agent_evolution_milestones"
            )

            # Build filter
            where_filter = {"agent_id": agent_id}
            if milestone_type:
                where_filter["milestone_type"] = milestone_type

            # Query ChromaDB
            results = collection.query(
                query_texts=[f"Agent: {agent_id}"],
                n_results=limit,
                where=where_filter
            )

            # Format results
            milestones = []
            for i in range(len(results["ids"][0])):
                milestones.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                })

            return milestones

        except Exception as e:
            print(f"Failed to retrieve milestones from ChromaDB: {e}")
            return []

    # ========== HELPER METHODS ==========

    def _format_metrics(self, metrics: Dict) -> str:
        """Format metrics dict as readable string."""
        lines = []
        for key, value in metrics.items():
            if isinstance(value, float):
                lines.append(f"  - {key}: {value:.4f}")
            else:
                lines.append(f"  - {key}: {value}")
        return "\n".join(lines)

    async def detect_milestone(
        self,
        agent_id: str,
        experiment: Experiment
    ) -> Optional[Tuple[str, str]]:
        """
        Detect if experiment represents a milestone.

        Args:
            agent_id: Agent identifier
            experiment: Completed experiment to analyze

        Returns:
            Tuple of (milestone_type, description) if milestone detected,
            None otherwise
        """
        if experiment.status != "COMPLETED":
            return None

        if not experiment.winner_variant_id:
            return None

        # Get winner variant
        winner = next(
            (v for v in experiment.variants if v.id == experiment.winner_variant_id),
            None
        )

        if not winner:
            return None

        # Calculate improvement
        control = next((v for v in experiment.variants if v.is_control), None)
        if not control or not control.results or not winner.results:
            return None

        control_success_rate = sum(1 for r in control.results if r.success) / len(control.results)
        winner_success_rate = sum(1 for r in winner.results if r.success) / len(winner.results)

        improvement = ((winner_success_rate - control_success_rate) / control_success_rate) * 100

        # Milestone thresholds
        if improvement >= 20:
            return (
                "major_improvement",
                f"Achieved {improvement:.1f}% improvement with variant '{winner.variant_name}'"
            )
        elif improvement >= 10:
            return (
                "improvement_threshold",
                f"Crossed 10% improvement threshold with {improvement:.1f}% gain"
            )
        elif winner_success_rate >= 0.95:
            return (
                "high_success_rate",
                f"Achieved 95%+ success rate ({winner_success_rate:.1%})"
            )

        return None
