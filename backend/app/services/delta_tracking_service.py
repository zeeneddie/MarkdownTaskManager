"""
Delta Tracking Service - Week 85

Tracks changes across multiple extraction runs over time.
Provides historical analysis, trend detection, and change management.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class ChangeCategory(str, Enum):
    """Category of change."""
    STRUCTURAL = "structural"  # Code structure changed
    REFINEMENT = "refinement"  # Story refined/improved
    DISCOVERY = "discovery"  # New story discovered
    REMOVAL = "removal"  # Story removed
    CONFIDENCE = "confidence"  # Confidence changed
    ESTIMATION = "estimation"  # Estimation changed
    PRIORITY = "priority"  # Priority changed


class TrendDirection(str, Enum):
    """Direction of trend."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"


@dataclass
class ChangeEvent:
    """A single change event in the history."""
    event_id: str
    timestamp: datetime
    session_id: str
    tier: str
    category: ChangeCategory
    entity_type: str  # story, epic, feature, task
    entity_id: str
    entity_title: Optional[str]
    change_description: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    impact_score: float = 0.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeltaSnapshot:
    """Snapshot of extraction state at a point in time."""
    snapshot_id: str
    project_id: int
    session_id: str
    tier: str
    timestamp: datetime
    total_stories: int
    total_epics: int
    total_features: int
    total_tasks: int
    overall_confidence: float
    invest_score: float
    story_ids: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrendAnalysis:
    """Analysis of trends over time."""
    metric_name: str
    direction: TrendDirection
    current_value: float
    previous_value: float
    change_percentage: float
    data_points: List[Tuple[datetime, float]]
    forecast_next: Optional[float] = None
    recommendation: Optional[str] = None


@dataclass
class DeltaHistory:
    """Complete delta history for a project."""
    project_id: int
    snapshots: List[DeltaSnapshot]
    events: List[ChangeEvent]
    trends: List[TrendAnalysis]
    summary: Dict[str, Any]


@dataclass
class ChangeImpactAssessment:
    """Assessment of change impact."""
    total_changes: int
    high_impact_changes: int
    medium_impact_changes: int
    low_impact_changes: int
    affected_areas: List[str]
    risk_assessment: str
    recommendations: List[str]


class DeltaTrackingService:
    """
    Service for tracking extraction changes over time.

    Features:
    - Historical snapshot storage
    - Change event tracking
    - Trend analysis
    - Impact assessment
    - Change reporting
    """

    def __init__(self, db=None):
        self.db = db
        self._snapshots: Dict[int, List[DeltaSnapshot]] = defaultdict(list)
        self._events: Dict[int, List[ChangeEvent]] = defaultdict(list)

    async def record_snapshot(
        self,
        project_id: int,
        extraction_result: Dict[str, Any],
    ) -> DeltaSnapshot:
        """
        Record a snapshot of the current extraction state.

        Args:
            project_id: Project ID
            extraction_result: Extraction result to snapshot

        Returns:
            DeltaSnapshot
        """
        stories = self._extract_stories(extraction_result)
        story_ids = [s.get("id", "") for s in stories]

        snapshot = DeltaSnapshot(
            snapshot_id=str(uuid4()),
            project_id=project_id,
            session_id=extraction_result.get("extraction_id", ""),
            tier=extraction_result.get("tier", "FREE"),
            timestamp=datetime.utcnow(),
            total_stories=len(stories),
            total_epics=extraction_result.get("total_epics", 0),
            total_features=extraction_result.get("total_features", 0),
            total_tasks=extraction_result.get("total_tasks", 0),
            overall_confidence=extraction_result.get("overall_confidence", 0.0),
            invest_score=extraction_result.get("invest_score", 0.0),
            story_ids=story_ids,
            metadata={
                "primary_stack": extraction_result.get("primary_stack"),
                "repository_path": extraction_result.get("repository_path"),
            },
        )

        self._snapshots[project_id].append(snapshot)

        # Detect changes from previous snapshot
        await self._detect_changes(project_id, snapshot, extraction_result)

        return snapshot

    async def get_history(
        self,
        project_id: int,
        since: Optional[datetime] = None,
        limit: int = 50,
    ) -> DeltaHistory:
        """
        Get delta history for a project.

        Args:
            project_id: Project ID
            since: Optional start date
            limit: Maximum number of snapshots

        Returns:
            DeltaHistory
        """
        snapshots = self._snapshots.get(project_id, [])
        events = self._events.get(project_id, [])

        if since:
            snapshots = [s for s in snapshots if s.timestamp >= since]
            events = [e for e in events if e.timestamp >= since]

        # Sort by timestamp descending
        snapshots = sorted(snapshots, key=lambda x: x.timestamp, reverse=True)[:limit]
        events = sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit * 5]

        # Analyze trends
        trends = await self._analyze_trends(snapshots)

        # Generate summary
        summary = self._generate_summary(snapshots, events)

        return DeltaHistory(
            project_id=project_id,
            snapshots=snapshots,
            events=events,
            trends=trends,
            summary=summary,
        )

    async def compare_snapshots(
        self,
        snapshot_id_1: str,
        snapshot_id_2: str,
    ) -> Dict[str, Any]:
        """
        Compare two specific snapshots.

        Args:
            snapshot_id_1: First snapshot ID
            snapshot_id_2: Second snapshot ID

        Returns:
            Comparison result
        """
        snap1 = None
        snap2 = None

        for snapshots in self._snapshots.values():
            for s in snapshots:
                if s.snapshot_id == snapshot_id_1:
                    snap1 = s
                if s.snapshot_id == snapshot_id_2:
                    snap2 = s

        if not snap1 or not snap2:
            return {"error": "Snapshot not found"}

        # Ensure chronological order
        if snap1.timestamp > snap2.timestamp:
            snap1, snap2 = snap2, snap1

        # Calculate differences
        story_diff = snap2.total_stories - snap1.total_stories
        confidence_diff = snap2.overall_confidence - snap1.overall_confidence
        invest_diff = snap2.invest_score - snap1.invest_score

        # Story set analysis
        added_stories = set(snap2.story_ids) - set(snap1.story_ids)
        removed_stories = set(snap1.story_ids) - set(snap2.story_ids)
        unchanged_stories = set(snap1.story_ids) & set(snap2.story_ids)

        # Time between snapshots
        time_diff = snap2.timestamp - snap1.timestamp

        return {
            "snapshot_1": {
                "id": snap1.snapshot_id,
                "timestamp": snap1.timestamp.isoformat(),
                "tier": snap1.tier,
                "total_stories": snap1.total_stories,
                "confidence": snap1.overall_confidence,
            },
            "snapshot_2": {
                "id": snap2.snapshot_id,
                "timestamp": snap2.timestamp.isoformat(),
                "tier": snap2.tier,
                "total_stories": snap2.total_stories,
                "confidence": snap2.overall_confidence,
            },
            "differences": {
                "time_between": str(time_diff),
                "stories_added": len(added_stories),
                "stories_removed": len(removed_stories),
                "stories_unchanged": len(unchanged_stories),
                "story_count_change": story_diff,
                "confidence_change": confidence_diff,
                "invest_score_change": invest_diff,
                "tier_changed": snap1.tier != snap2.tier,
            },
            "added_story_ids": list(added_stories),
            "removed_story_ids": list(removed_stories),
            "interpretation": self._interpret_comparison(
                story_diff, confidence_diff, invest_diff
            ),
        }

    async def get_change_timeline(
        self,
        project_id: int,
        entity_id: Optional[str] = None,
        category: Optional[ChangeCategory] = None,
        since: Optional[datetime] = None,
    ) -> List[ChangeEvent]:
        """
        Get timeline of changes for project or entity.

        Args:
            project_id: Project ID
            entity_id: Optional specific entity
            category: Optional category filter
            since: Optional start date

        Returns:
            List of change events
        """
        events = self._events.get(project_id, [])

        if entity_id:
            events = [e for e in events if e.entity_id == entity_id]

        if category:
            events = [e for e in events if e.category == category]

        if since:
            events = [e for e in events if e.timestamp >= since]

        return sorted(events, key=lambda x: x.timestamp, reverse=True)

    async def assess_change_impact(
        self,
        project_id: int,
        session_id: str,
        previous_result: Dict[str, Any],
        current_result: Dict[str, Any],
    ) -> ChangeImpactAssessment:
        """
        Assess the impact of changes between two extraction runs.

        Args:
            project_id: Project ID
            session_id: Current session ID
            previous_result: Previous extraction result
            current_result: Current extraction result

        Returns:
            ChangeImpactAssessment
        """
        # Record the current state
        await self.record_snapshot(project_id, current_result)

        # Get events from this session
        session_events = [
            e for e in self._events.get(project_id, [])
            if e.session_id == session_id
        ]

        # Categorize by impact
        high_impact = [e for e in session_events if e.impact_score >= 0.7]
        medium_impact = [e for e in session_events if 0.3 <= e.impact_score < 0.7]
        low_impact = [e for e in session_events if e.impact_score < 0.3]

        # Determine affected areas
        affected_areas = list(set(
            e.metadata.get("area", "unknown") for e in session_events
        ))

        # Risk assessment
        risk = self._assess_risk(high_impact, medium_impact, session_events)

        # Generate recommendations
        recommendations = self._generate_impact_recommendations(
            session_events, previous_result, current_result
        )

        return ChangeImpactAssessment(
            total_changes=len(session_events),
            high_impact_changes=len(high_impact),
            medium_impact_changes=len(medium_impact),
            low_impact_changes=len(low_impact),
            affected_areas=affected_areas,
            risk_assessment=risk,
            recommendations=recommendations,
        )

    async def get_story_evolution(
        self,
        project_id: int,
        story_id: str,
    ) -> Dict[str, Any]:
        """
        Get the evolution history of a specific story.

        Args:
            project_id: Project ID
            story_id: Story ID

        Returns:
            Evolution history
        """
        events = [
            e for e in self._events.get(project_id, [])
            if e.entity_id == story_id
        ]

        # Find in which snapshots this story appeared
        appearances = []
        for snapshot in self._snapshots.get(project_id, []):
            if story_id in snapshot.story_ids:
                appearances.append({
                    "snapshot_id": snapshot.snapshot_id,
                    "timestamp": snapshot.timestamp.isoformat(),
                    "tier": snapshot.tier,
                    "session_id": snapshot.session_id,
                })

        return {
            "story_id": story_id,
            "first_seen": appearances[0] if appearances else None,
            "last_seen": appearances[-1] if appearances else None,
            "appearance_count": len(appearances),
            "change_events": [
                {
                    "event_id": e.event_id,
                    "timestamp": e.timestamp.isoformat(),
                    "category": e.category.value,
                    "description": e.change_description,
                    "old_value": e.old_value,
                    "new_value": e.new_value,
                }
                for e in sorted(events, key=lambda x: x.timestamp)
            ],
            "evolution_summary": self._summarize_evolution(events),
        }

    async def generate_change_report(
        self,
        project_id: int,
        since: Optional[datetime] = None,
        format: str = "summary",
    ) -> Dict[str, Any]:
        """
        Generate a change report for the project.

        Args:
            project_id: Project ID
            since: Report start date
            format: Report format (summary, detailed, timeline)

        Returns:
            Change report
        """
        history = await self.get_history(project_id, since=since)

        if format == "summary":
            return self._generate_summary_report(history)
        elif format == "detailed":
            return self._generate_detailed_report(history)
        elif format == "timeline":
            return self._generate_timeline_report(history)
        else:
            return self._generate_summary_report(history)

    # ==================== Private Methods ====================

    def _extract_stories(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract stories from extraction result."""
        stories = []
        if "stories" in result:
            stories.extend(result["stories"])
        for level in ["function_level", "class_level", "module_level", "system_level"]:
            level_data = result.get(level, {})
            if isinstance(level_data, dict) and "stories" in level_data:
                stories.extend(level_data["stories"])
        return stories

    async def _detect_changes(
        self,
        project_id: int,
        current_snapshot: DeltaSnapshot,
        extraction_result: Dict[str, Any],
    ):
        """Detect changes from previous snapshot."""
        snapshots = self._snapshots.get(project_id, [])

        if len(snapshots) < 2:
            # First snapshot, record as discovery
            for story_id in current_snapshot.story_ids:
                event = ChangeEvent(
                    event_id=str(uuid4()),
                    timestamp=current_snapshot.timestamp,
                    session_id=current_snapshot.session_id,
                    tier=current_snapshot.tier,
                    category=ChangeCategory.DISCOVERY,
                    entity_type="story",
                    entity_id=story_id,
                    entity_title=None,
                    change_description="Initial discovery",
                    impact_score=0.5,
                )
                self._events[project_id].append(event)
            return

        # Get previous snapshot
        previous = snapshots[-2]

        # Detect story changes
        current_ids = set(current_snapshot.story_ids)
        previous_ids = set(previous.story_ids)

        # New stories
        for story_id in current_ids - previous_ids:
            event = ChangeEvent(
                event_id=str(uuid4()),
                timestamp=current_snapshot.timestamp,
                session_id=current_snapshot.session_id,
                tier=current_snapshot.tier,
                category=ChangeCategory.DISCOVERY,
                entity_type="story",
                entity_id=story_id,
                entity_title=None,
                change_description="New story discovered in this run",
                impact_score=0.6,
                metadata={"area": "story_discovery"},
            )
            self._events[project_id].append(event)

        # Removed stories
        for story_id in previous_ids - current_ids:
            event = ChangeEvent(
                event_id=str(uuid4()),
                timestamp=current_snapshot.timestamp,
                session_id=current_snapshot.session_id,
                tier=current_snapshot.tier,
                category=ChangeCategory.REMOVAL,
                entity_type="story",
                entity_id=story_id,
                entity_title=None,
                change_description="Story no longer detected",
                impact_score=0.7,
                metadata={"area": "story_removal"},
            )
            self._events[project_id].append(event)

        # Confidence change
        if abs(current_snapshot.overall_confidence - previous.overall_confidence) > 0.05:
            event = ChangeEvent(
                event_id=str(uuid4()),
                timestamp=current_snapshot.timestamp,
                session_id=current_snapshot.session_id,
                tier=current_snapshot.tier,
                category=ChangeCategory.CONFIDENCE,
                entity_type="project",
                entity_id=str(project_id),
                entity_title=None,
                change_description="Overall confidence changed significantly",
                old_value=previous.overall_confidence,
                new_value=current_snapshot.overall_confidence,
                impact_score=0.5,
                metadata={"area": "confidence"},
            )
            self._events[project_id].append(event)

    async def _analyze_trends(
        self,
        snapshots: List[DeltaSnapshot],
    ) -> List[TrendAnalysis]:
        """Analyze trends from snapshots."""
        if len(snapshots) < 2:
            return []

        trends = []

        # Confidence trend
        confidence_data = [
            (s.timestamp, s.overall_confidence)
            for s in sorted(snapshots, key=lambda x: x.timestamp)
        ]
        trends.append(self._analyze_metric_trend(
            "overall_confidence", confidence_data
        ))

        # Story count trend
        story_data = [
            (s.timestamp, float(s.total_stories))
            for s in sorted(snapshots, key=lambda x: x.timestamp)
        ]
        trends.append(self._analyze_metric_trend(
            "story_count", story_data
        ))

        # INVEST score trend
        invest_data = [
            (s.timestamp, s.invest_score)
            for s in sorted(snapshots, key=lambda x: x.timestamp)
        ]
        trends.append(self._analyze_metric_trend(
            "invest_score", invest_data
        ))

        return trends

    def _analyze_metric_trend(
        self,
        metric_name: str,
        data_points: List[Tuple[datetime, float]],
    ) -> TrendAnalysis:
        """Analyze trend for a specific metric."""
        if len(data_points) < 2:
            return TrendAnalysis(
                metric_name=metric_name,
                direction=TrendDirection.STABLE,
                current_value=data_points[-1][1] if data_points else 0.0,
                previous_value=data_points[0][1] if data_points else 0.0,
                change_percentage=0.0,
                data_points=data_points,
            )

        current = data_points[-1][1]
        previous = data_points[-2][1]

        if previous > 0:
            change_pct = ((current - previous) / previous) * 100
        else:
            change_pct = 0.0 if current == 0 else 100.0

        # Determine direction
        if len(data_points) >= 3:
            # Check for volatility
            changes = [
                data_points[i][1] - data_points[i-1][1]
                for i in range(1, len(data_points))
            ]
            signs_differ = any(
                (changes[i] > 0) != (changes[i-1] > 0)
                for i in range(1, len(changes))
            )
            if signs_differ:
                direction = TrendDirection.VOLATILE
            elif current > previous:
                direction = TrendDirection.IMPROVING
            elif current < previous:
                direction = TrendDirection.DECLINING
            else:
                direction = TrendDirection.STABLE
        else:
            if current > previous:
                direction = TrendDirection.IMPROVING
            elif current < previous:
                direction = TrendDirection.DECLINING
            else:
                direction = TrendDirection.STABLE

        # Simple forecast (linear)
        if len(data_points) >= 2:
            avg_change = (current - data_points[0][1]) / (len(data_points) - 1)
            forecast = current + avg_change
        else:
            forecast = current

        # Generate recommendation
        recommendation = self._get_trend_recommendation(
            metric_name, direction, change_pct
        )

        return TrendAnalysis(
            metric_name=metric_name,
            direction=direction,
            current_value=current,
            previous_value=previous,
            change_percentage=change_pct,
            data_points=data_points,
            forecast_next=forecast,
            recommendation=recommendation,
        )

    def _get_trend_recommendation(
        self,
        metric: str,
        direction: TrendDirection,
        change_pct: float,
    ) -> str:
        """Get recommendation based on trend."""
        if metric == "overall_confidence":
            if direction == TrendDirection.DECLINING:
                return "Consider upgrading tier or reviewing extraction parameters"
            elif direction == TrendDirection.IMPROVING:
                return "Confidence improving. Continue current approach."
        elif metric == "story_count":
            if direction == TrendDirection.VOLATILE:
                return "Story count unstable. Review extraction consistency."
        elif metric == "invest_score":
            if direction == TrendDirection.DECLINING:
                return "Story quality declining. Enable INVEST validation."

        return ""

    def _generate_summary(
        self,
        snapshots: List[DeltaSnapshot],
        events: List[ChangeEvent],
    ) -> Dict[str, Any]:
        """Generate summary from history."""
        if not snapshots:
            return {"total_snapshots": 0, "total_events": 0}

        return {
            "total_snapshots": len(snapshots),
            "total_events": len(events),
            "date_range": {
                "earliest": min(s.timestamp for s in snapshots).isoformat(),
                "latest": max(s.timestamp for s in snapshots).isoformat(),
            },
            "tier_distribution": self._count_by(snapshots, lambda s: s.tier),
            "event_categories": self._count_by(events, lambda e: e.category.value),
            "avg_confidence": sum(s.overall_confidence for s in snapshots) / len(snapshots),
            "avg_stories": sum(s.total_stories for s in snapshots) / len(snapshots),
        }

    def _count_by(self, items: List, key_fn) -> Dict[str, int]:
        """Count items by key function."""
        counts: Dict[str, int] = {}
        for item in items:
            key = key_fn(item)
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _interpret_comparison(
        self,
        story_diff: int,
        confidence_diff: float,
        invest_diff: float,
    ) -> str:
        """Interpret comparison results."""
        parts = []

        if story_diff > 0:
            parts.append(f"Discovered {story_diff} new stories")
        elif story_diff < 0:
            parts.append(f"Lost {abs(story_diff)} stories")

        if confidence_diff > 0.1:
            parts.append("Significant confidence improvement")
        elif confidence_diff < -0.1:
            parts.append("Confidence declined")

        if invest_diff > 0.1:
            parts.append("Quality improved")
        elif invest_diff < -0.1:
            parts.append("Quality declined")

        if not parts:
            return "No significant changes detected"

        return ". ".join(parts) + "."

    def _assess_risk(
        self,
        high_impact: List[ChangeEvent],
        medium_impact: List[ChangeEvent],
        all_events: List[ChangeEvent],
    ) -> str:
        """Assess overall risk level."""
        if len(high_impact) > 3:
            return "high"
        if len(high_impact) > 0 or len(medium_impact) > 5:
            return "medium"
        return "low"

    def _generate_impact_recommendations(
        self,
        events: List[ChangeEvent],
        previous: Dict[str, Any],
        current: Dict[str, Any],
    ) -> List[str]:
        """Generate impact recommendations."""
        recommendations = []

        # Count by category
        category_counts = self._count_by(events, lambda e: e.category)

        if category_counts.get(ChangeCategory.REMOVAL.value, 0) > 3:
            recommendations.append(
                "Multiple stories removed. Verify these are intentional."
            )

        if category_counts.get(ChangeCategory.DISCOVERY.value, 0) > 10:
            recommendations.append(
                "Many new stories discovered. Review for accuracy."
            )

        confidence_change = (
            current.get("overall_confidence", 0) -
            previous.get("overall_confidence", 0)
        )
        if confidence_change < -0.1:
            recommendations.append(
                "Confidence dropped significantly. Consider using higher tier."
            )

        return recommendations

    def _summarize_evolution(self, events: List[ChangeEvent]) -> str:
        """Summarize story evolution."""
        if not events:
            return "No changes recorded for this story."

        categories = [e.category.value for e in events]
        unique_categories = list(set(categories))

        if len(events) == 1:
            return f"Story has undergone 1 change: {events[0].category.value}"

        return f"Story has undergone {len(events)} changes across categories: {', '.join(unique_categories)}"

    def _generate_summary_report(self, history: DeltaHistory) -> Dict[str, Any]:
        """Generate summary report."""
        return {
            "report_type": "summary",
            "project_id": history.project_id,
            "generated_at": datetime.utcnow().isoformat(),
            "snapshot_count": len(history.snapshots),
            "event_count": len(history.events),
            "trends": [
                {
                    "metric": t.metric_name,
                    "direction": t.direction.value,
                    "change": f"{t.change_percentage:+.1f}%",
                }
                for t in history.trends
            ],
            "summary": history.summary,
        }

    def _generate_detailed_report(self, history: DeltaHistory) -> Dict[str, Any]:
        """Generate detailed report."""
        return {
            "report_type": "detailed",
            "project_id": history.project_id,
            "generated_at": datetime.utcnow().isoformat(),
            "snapshots": [
                {
                    "id": s.snapshot_id,
                    "timestamp": s.timestamp.isoformat(),
                    "tier": s.tier,
                    "stories": s.total_stories,
                    "confidence": s.overall_confidence,
                }
                for s in history.snapshots
            ],
            "events": [
                {
                    "id": e.event_id,
                    "timestamp": e.timestamp.isoformat(),
                    "category": e.category.value,
                    "entity": e.entity_id,
                    "description": e.change_description,
                }
                for e in history.events
            ],
            "trends": [
                {
                    "metric": t.metric_name,
                    "direction": t.direction.value,
                    "current": t.current_value,
                    "previous": t.previous_value,
                    "change_pct": t.change_percentage,
                    "forecast": t.forecast_next,
                    "recommendation": t.recommendation,
                }
                for t in history.trends
            ],
        }

    def _generate_timeline_report(self, history: DeltaHistory) -> Dict[str, Any]:
        """Generate timeline report."""
        # Merge snapshots and events into timeline
        timeline = []

        for s in history.snapshots:
            timeline.append({
                "type": "snapshot",
                "timestamp": s.timestamp.isoformat(),
                "id": s.snapshot_id,
                "description": f"Extraction snapshot: {s.total_stories} stories, {s.overall_confidence:.0%} confidence",
                "tier": s.tier,
            })

        for e in history.events:
            timeline.append({
                "type": "event",
                "timestamp": e.timestamp.isoformat(),
                "id": e.event_id,
                "description": e.change_description,
                "category": e.category.value,
                "impact": e.impact_score,
            })

        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])

        return {
            "report_type": "timeline",
            "project_id": history.project_id,
            "generated_at": datetime.utcnow().isoformat(),
            "timeline": timeline,
        }


def get_delta_tracking_service(db=None) -> DeltaTrackingService:
    """Factory function for DeltaTrackingService."""
    return DeltaTrackingService(db)
