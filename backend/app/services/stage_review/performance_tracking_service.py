"""
Performance Tracking Service for Stage Reviews.

Fase 23.6 Phase 24.4: Persistence and metrics aggregation for stage reviews.
Handles database storage of review sessions and performance analytics.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .types import (
    StageType,
    IssueSeverity,
    IssueCategory,
    ReviewDecision,
    ReviewResult,
    ConsolidatedIssue,
    ModelReviewResult,
)

logger = logging.getLogger(__name__)


@dataclass
class ModelPerformanceReport:
    """Performance report for a specific model."""
    model_name: str
    total_reviews: int = 0
    successful_reviews: int = 0
    timeout_rate: float = 0.0
    error_rate: float = 0.0
    avg_response_time_ms: float = 0.0
    p95_response_time_ms: int = 0
    avg_issues_found: float = 0.0
    consensus_alignment: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "total_reviews": self.total_reviews,
            "successful_reviews": self.successful_reviews,
            "timeout_rate": round(self.timeout_rate, 2),
            "error_rate": round(self.error_rate, 2),
            "avg_response_time_ms": round(self.avg_response_time_ms, 1),
            "p95_response_time_ms": self.p95_response_time_ms,
            "avg_issues_found": round(self.avg_issues_found, 2),
            "consensus_alignment": round(self.consensus_alignment, 2),
        }


@dataclass
class StagePerformanceReport:
    """Performance report for a specific stage."""
    stage_type: StageType
    total_reviews: int = 0
    approval_rate: float = 0.0
    avg_consensus: float = 0.0
    avg_duration_ms: float = 0.0
    avg_issues_per_review: float = 0.0
    second_round_rate: float = 0.0
    improvement_success_rate: float = 0.0
    top_issue_categories: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_type": self.stage_type.value,
            "total_reviews": self.total_reviews,
            "approval_rate": round(self.approval_rate, 2),
            "avg_consensus": round(self.avg_consensus, 2),
            "avg_duration_ms": round(self.avg_duration_ms, 1),
            "avg_issues_per_review": round(self.avg_issues_per_review, 2),
            "second_round_rate": round(self.second_round_rate, 2),
            "improvement_success_rate": round(self.improvement_success_rate, 2),
            "top_issue_categories": self.top_issue_categories,
        }


@dataclass
class OverallPerformanceReport:
    """Overall performance summary."""
    total_reviews: int = 0
    approval_rate: float = 0.0
    avg_consensus: float = 0.0
    avg_duration_ms: float = 0.0
    second_round_rate: float = 0.0
    most_common_issues: List[Dict[str, Any]] = field(default_factory=list)
    best_performing_model: Optional[str] = None
    worst_performing_stage: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_reviews": self.total_reviews,
            "approval_rate": round(self.approval_rate, 2),
            "avg_consensus": round(self.avg_consensus, 2),
            "avg_duration_ms": round(self.avg_duration_ms, 1),
            "second_round_rate": round(self.second_round_rate, 2),
            "most_common_issues": self.most_common_issues,
            "best_performing_model": self.best_performing_model,
            "worst_performing_stage": self.worst_performing_stage,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
        }


class PerformanceTrackingService:
    """
    Service for tracking and analyzing stage review performance.

    Features:
    - In-memory metrics collection
    - Database persistence (when db_session provided)
    - Model performance analytics
    - Stage performance analytics
    - Trend analysis
    """

    def __init__(self, db_session=None):
        """
        Initialize performance tracking service.

        Args:
            db_session: Optional SQLAlchemy session for persistence
        """
        self.db_session = db_session

        # In-memory metrics storage
        self._sessions: List[Dict[str, Any]] = []
        self._model_metrics: Dict[str, Dict[str, Any]] = {}
        self._stage_metrics: Dict[str, Dict[str, Any]] = {}

    async def record_review(self, result: ReviewResult) -> None:
        """
        Record a completed review session.

        Args:
            result: The review result to record
        """
        session_data = {
            "session_id": result.session_id,
            "stage_type": result.stage_type.value,
            "decision": result.decision.value,
            "approved": result.approved,
            "consensus_level": result.consensus_level,
            "rounds_completed": result.rounds_completed,
            "issues_count": len(result.issues),
            "critical_count": sum(
                1 for i in result.issues
                if i.severity == IssueSeverity.CRITICAL
            ),
            "major_count": sum(
                1 for i in result.issues
                if i.severity == IssueSeverity.MAJOR
            ),
            "duration_ms": result.metrics.get("duration_ms", 0),
            "improvement_applied": result.improved_artifact is not None,
            "created_at": result.created_at or datetime.utcnow(),
            "issues": [self._serialize_issue(i) for i in result.issues],
        }

        # Store in memory
        self._sessions.append(session_data)

        # Update aggregate metrics
        self._update_stage_metrics(session_data)

        # Persist to database if available
        if self.db_session:
            await self._persist_session(session_data)

        logger.info(
            f"Recorded review {result.session_id}: "
            f"{result.stage_type.value} - {result.decision.value}"
        )

    async def record_model_review(
        self,
        session_id: str,
        model_result: ModelReviewResult,
    ) -> None:
        """
        Record an individual model's review.

        Args:
            session_id: The parent session ID
            model_result: The model review result
        """
        model_name = model_result.model_name

        # Initialize model metrics if needed
        if model_name not in self._model_metrics:
            self._model_metrics[model_name] = {
                "total_reviews": 0,
                "successful": 0,
                "timeouts": 0,
                "errors": 0,
                "response_times": [],
                "issues_counts": [],
            }

        metrics = self._model_metrics[model_name]
        metrics["total_reviews"] += 1

        if model_result.status == "completed":
            metrics["successful"] += 1
            metrics["response_times"].append(model_result.response_time_ms)
            metrics["issues_counts"].append(len(model_result.issues))
        elif model_result.status == "timeout":
            metrics["timeouts"] += 1
        else:
            metrics["errors"] += 1

        # Persist if database available
        if self.db_session:
            await self._persist_model_review(session_id, model_result)

    def _update_stage_metrics(self, session_data: Dict[str, Any]) -> None:
        """Update stage-level aggregate metrics."""
        stage = session_data["stage_type"]

        if stage not in self._stage_metrics:
            self._stage_metrics[stage] = {
                "total_reviews": 0,
                "approved": 0,
                "consensus_levels": [],
                "durations": [],
                "issues_counts": [],
                "second_rounds": 0,
                "improvements": 0,
                "issue_categories": {},
            }

        metrics = self._stage_metrics[stage]
        metrics["total_reviews"] += 1

        if session_data["approved"]:
            metrics["approved"] += 1

        metrics["consensus_levels"].append(session_data["consensus_level"])
        metrics["durations"].append(session_data["duration_ms"])
        metrics["issues_counts"].append(session_data["issues_count"])

        if session_data["rounds_completed"] > 1:
            metrics["second_rounds"] += 1

        if session_data["improvement_applied"]:
            metrics["improvements"] += 1

        # Track issue categories
        for issue in session_data.get("issues", []):
            cat = issue.get("category", "unknown")
            metrics["issue_categories"][cat] = (
                metrics["issue_categories"].get(cat, 0) + 1
            )

    def get_model_performance(
        self,
        model_name: Optional[str] = None,
    ) -> List[ModelPerformanceReport]:
        """
        Get performance report for models.

        Args:
            model_name: Optional specific model name

        Returns:
            List of model performance reports
        """
        reports = []

        models = [model_name] if model_name else self._model_metrics.keys()

        for name in models:
            if name not in self._model_metrics:
                continue

            metrics = self._model_metrics[name]
            total = metrics["total_reviews"]

            if total == 0:
                continue

            response_times = metrics["response_times"]
            issues_counts = metrics["issues_counts"]

            report = ModelPerformanceReport(
                model_name=name,
                total_reviews=total,
                successful_reviews=metrics["successful"],
                timeout_rate=metrics["timeouts"] / total * 100 if total > 0 else 0,
                error_rate=metrics["errors"] / total * 100 if total > 0 else 0,
                avg_response_time_ms=(
                    sum(response_times) / len(response_times)
                    if response_times else 0
                ),
                p95_response_time_ms=(
                    sorted(response_times)[int(len(response_times) * 0.95)]
                    if response_times else 0
                ),
                avg_issues_found=(
                    sum(issues_counts) / len(issues_counts)
                    if issues_counts else 0
                ),
            )
            reports.append(report)

        return reports

    def get_stage_performance(
        self,
        stage_type: Optional[StageType] = None,
    ) -> List[StagePerformanceReport]:
        """
        Get performance report for stages.

        Args:
            stage_type: Optional specific stage type

        Returns:
            List of stage performance reports
        """
        reports = []

        stages = (
            [stage_type.value] if stage_type
            else self._stage_metrics.keys()
        )

        for stage in stages:
            if stage not in self._stage_metrics:
                continue

            metrics = self._stage_metrics[stage]
            total = metrics["total_reviews"]

            if total == 0:
                continue

            # Get top issue categories
            categories = metrics["issue_categories"]
            top_categories = sorted(
                categories.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]

            report = StagePerformanceReport(
                stage_type=StageType(stage),
                total_reviews=total,
                approval_rate=metrics["approved"] / total * 100,
                avg_consensus=(
                    sum(metrics["consensus_levels"]) /
                    len(metrics["consensus_levels"])
                    if metrics["consensus_levels"] else 0
                ),
                avg_duration_ms=(
                    sum(metrics["durations"]) / len(metrics["durations"])
                    if metrics["durations"] else 0
                ),
                avg_issues_per_review=(
                    sum(metrics["issues_counts"]) /
                    len(metrics["issues_counts"])
                    if metrics["issues_counts"] else 0
                ),
                second_round_rate=metrics["second_rounds"] / total * 100,
                improvement_success_rate=(
                    metrics["improvements"] / metrics["second_rounds"] * 100
                    if metrics["second_rounds"] > 0 else 0
                ),
                top_issue_categories=[cat for cat, _ in top_categories],
            )
            reports.append(report)

        return reports

    def get_overall_performance(
        self,
        days: int = 30,
    ) -> OverallPerformanceReport:
        """
        Get overall performance summary.

        Args:
            days: Number of days to include

        Returns:
            Overall performance report
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Filter sessions by date
        recent_sessions = [
            s for s in self._sessions
            if s.get("created_at", datetime.min) >= cutoff
        ]

        if not recent_sessions:
            return OverallPerformanceReport()

        total = len(recent_sessions)
        approved = sum(1 for s in recent_sessions if s["approved"])
        consensus_levels = [s["consensus_level"] for s in recent_sessions]
        durations = [s["duration_ms"] for s in recent_sessions]
        second_rounds = sum(
            1 for s in recent_sessions if s["rounds_completed"] > 1
        )

        # Count issue categories
        category_counts: Dict[str, int] = {}
        for session in recent_sessions:
            for issue in session.get("issues", []):
                cat = issue.get("category", "unknown")
                category_counts[cat] = category_counts.get(cat, 0) + 1

        most_common = sorted(
            [{"category": k, "count": v} for k, v in category_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:5]

        # Find best model and worst stage
        model_reports = self.get_model_performance()
        best_model = None
        if model_reports:
            best = max(
                model_reports,
                key=lambda r: r.successful_reviews / r.total_reviews
                if r.total_reviews > 0 else 0
            )
            best_model = best.model_name

        stage_reports = self.get_stage_performance()
        worst_stage = None
        if stage_reports:
            worst = min(
                stage_reports,
                key=lambda r: r.approval_rate
            )
            worst_stage = worst.stage_type.value

        return OverallPerformanceReport(
            total_reviews=total,
            approval_rate=approved / total * 100 if total > 0 else 0,
            avg_consensus=(
                sum(consensus_levels) / len(consensus_levels)
                if consensus_levels else 0
            ),
            avg_duration_ms=(
                sum(durations) / len(durations)
                if durations else 0
            ),
            second_round_rate=second_rounds / total * 100 if total > 0 else 0,
            most_common_issues=most_common,
            best_performing_model=best_model,
            worst_performing_stage=worst_stage,
            period_start=cutoff,
            period_end=datetime.utcnow(),
        )

    def _serialize_issue(self, issue: ConsolidatedIssue) -> Dict[str, Any]:
        """Serialize an issue for storage."""
        return {
            "severity": issue.severity.value,
            "category": issue.category.value,
            "title": issue.title,
            "description": issue.description,
            "consensus_score": issue.consensus_score,
            "line_start": issue.line_start,
        }

    async def _persist_session(self, session_data: Dict[str, Any]) -> None:
        """Persist session to database."""
        try:
            from app.models.stage_review import (
                StageReviewSession,
                StageTypeDB,
                ReviewDecisionDB,
            )

            db_session = StageReviewSession(
                session_id=session_data["session_id"],
                stage_type=StageTypeDB(session_data["stage_type"]),
                decision=ReviewDecisionDB(session_data["decision"]),
                approved=session_data["approved"],
                consensus_level=session_data["consensus_level"],
                rounds_completed=session_data["rounds_completed"],
                total_issues=session_data["issues_count"],
                critical_issues=session_data["critical_count"],
                major_issues=session_data["major_count"],
                minor_issues=session_data["issues_count"] - session_data["critical_count"] - session_data["major_count"],
                duration_ms=session_data["duration_ms"],
                improvement_applied=session_data["improvement_applied"],
            )

            self.db_session.add(db_session)
            await self.db_session.commit()

        except Exception as e:
            logger.error(f"Failed to persist session: {e}")

    async def _persist_model_review(
        self,
        session_id: str,
        model_result: ModelReviewResult,
    ) -> None:
        """Persist model review to database."""
        try:
            from app.models.stage_review import StageModelReview, StageReviewSession

            # Get session ID from database
            db_session = await self.db_session.execute(
                StageReviewSession.__table__.select().where(
                    StageReviewSession.session_id == session_id
                )
            )
            session_row = db_session.first()

            if not session_row:
                return

            model_review = StageModelReview(
                session_id=session_row.id,
                model_name=model_result.model_name,
                model_role=model_result.model_role.value,
                issues_found=len(model_result.issues),
                response_time_ms=model_result.response_time_ms,
                status=model_result.status,
                error_message=model_result.error_message,
            )

            self.db_session.add(model_review)
            await self.db_session.commit()

        except Exception as e:
            logger.error(f"Failed to persist model review: {e}")

    def clear_metrics(self) -> None:
        """Clear all in-memory metrics."""
        self._sessions.clear()
        self._model_metrics.clear()
        self._stage_metrics.clear()


# Factory function
def create_performance_tracking_service(db_session=None) -> PerformanceTrackingService:
    """Create a PerformanceTrackingService instance."""
    return PerformanceTrackingService(db_session=db_session)
