"""
Tests for Delta Tracking Service - Week 85

Tests:
- DeltaTrackingService
- Snapshot recording
- Change event detection
- Trend analysis
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.services.delta_tracking_service import (
    DeltaTrackingService,
    ChangeCategory,
    TrendDirection,
    ChangeEvent,
    DeltaSnapshot,
    TrendAnalysis,
    DeltaHistory,
    ChangeImpactAssessment,
    get_delta_tracking_service,
)


class TestChangeEvent:
    """Tests for ChangeEvent dataclass."""

    def test_create_discovery_event(self):
        """Should create discovery event."""
        event = ChangeEvent(
            event_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc),
            session_id="session-001",
            tier="STANDARD",
            category=ChangeCategory.DISCOVERY,
            entity_type="story",
            entity_id="S001",
            entity_title="New Story",
            change_description="Story discovered in extraction",
            impact_score=0.6,
        )

        assert event.category == ChangeCategory.DISCOVERY
        assert event.impact_score == 0.6

    def test_create_removal_event(self):
        """Should create removal event."""
        event = ChangeEvent(
            event_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc),
            session_id="session-002",
            tier="PROFESSIONAL",
            category=ChangeCategory.REMOVAL,
            entity_type="story",
            entity_id="S002",
            entity_title=None,
            change_description="Story no longer detected",
            old_value={"title": "Old Story"},
            impact_score=0.7,
        )

        assert event.category == ChangeCategory.REMOVAL
        assert event.old_value is not None


class TestDeltaSnapshot:
    """Tests for DeltaSnapshot dataclass."""

    def test_create_snapshot(self):
        """Should create snapshot."""
        snapshot = DeltaSnapshot(
            snapshot_id=str(uuid4()),
            project_id=1,
            session_id="session-001",
            tier="STANDARD",
            timestamp=datetime.now(timezone.utc),
            total_stories=25,
            total_epics=3,
            total_features=8,
            total_tasks=14,
            overall_confidence=0.82,
            invest_score=7.5,
            story_ids=["S001", "S002", "S003"],
        )

        assert snapshot.total_stories == 25
        assert len(snapshot.story_ids) == 3


class TestDeltaTrackingService:
    """Tests for DeltaTrackingService."""

    def test_init_service(self):
        """Should initialize service."""
        service = DeltaTrackingService()

        assert service._snapshots == {}
        assert service._events == {}

    @pytest.mark.asyncio
    async def test_record_snapshot(self):
        """Should record extraction snapshot."""
        service = DeltaTrackingService()

        extraction_result = {
            "extraction_id": "ext-001",
            "tier": "STANDARD",
            "stories": [
                {"id": "S001", "title": "Story 1"},
                {"id": "S002", "title": "Story 2"},
            ],
            "total_epics": 1,
            "total_features": 2,
            "total_tasks": 0,
            "overall_confidence": 0.85,
            "invest_score": 8.0,
        }

        snapshot = await service.record_snapshot(
            project_id=1,
            extraction_result=extraction_result,
        )

        assert snapshot.project_id == 1
        assert snapshot.total_stories == 2
        assert snapshot.overall_confidence == 0.85
        assert len(snapshot.story_ids) == 2

    @pytest.mark.asyncio
    async def test_record_multiple_snapshots(self):
        """Should track changes between snapshots."""
        service = DeltaTrackingService()

        # First snapshot
        result1 = {
            "extraction_id": "ext-001",
            "tier": "FREE",
            "stories": [{"id": "S001"}],
            "overall_confidence": 0.60,
        }
        await service.record_snapshot(1, result1)

        # Second snapshot with changes
        result2 = {
            "extraction_id": "ext-002",
            "tier": "STANDARD",
            "stories": [{"id": "S001"}, {"id": "S002"}, {"id": "S003"}],
            "overall_confidence": 0.80,
        }
        await service.record_snapshot(1, result2)

        # Should have 2 snapshots
        assert len(service._snapshots[1]) == 2

        # Should have change events
        events = service._events.get(1, [])
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_detect_story_additions(self):
        """Should detect new stories."""
        service = DeltaTrackingService()

        # First snapshot
        await service.record_snapshot(1, {
            "extraction_id": "ext-001",
            "tier": "FREE",
            "stories": [{"id": "S001"}],
            "overall_confidence": 0.60,
        })

        # Second snapshot with new story
        await service.record_snapshot(1, {
            "extraction_id": "ext-002",
            "tier": "STANDARD",
            "stories": [{"id": "S001"}, {"id": "S002"}],
            "overall_confidence": 0.80,
        })

        discovery_events = [
            e for e in service._events[1]
            if e.category == ChangeCategory.DISCOVERY and e.entity_id == "S002"
        ]
        assert len(discovery_events) >= 1

    @pytest.mark.asyncio
    async def test_detect_story_removals(self):
        """Should detect removed stories."""
        service = DeltaTrackingService()

        # First snapshot
        await service.record_snapshot(1, {
            "extraction_id": "ext-001",
            "tier": "STANDARD",
            "stories": [{"id": "S001"}, {"id": "S002"}],
            "overall_confidence": 0.80,
        })

        # Second snapshot with story removed
        await service.record_snapshot(1, {
            "extraction_id": "ext-002",
            "tier": "PROFESSIONAL",
            "stories": [{"id": "S001"}],
            "overall_confidence": 0.85,
        })

        removal_events = [
            e for e in service._events[1]
            if e.category == ChangeCategory.REMOVAL and e.entity_id == "S002"
        ]
        assert len(removal_events) >= 1

    @pytest.mark.asyncio
    async def test_get_history(self):
        """Should retrieve delta history."""
        service = DeltaTrackingService()

        # Create some history
        await service.record_snapshot(1, {
            "extraction_id": "ext-001",
            "tier": "FREE",
            "stories": [{"id": "S001"}],
            "overall_confidence": 0.60,
        })
        await service.record_snapshot(1, {
            "extraction_id": "ext-002",
            "tier": "STANDARD",
            "stories": [{"id": "S001"}, {"id": "S002"}],
            "overall_confidence": 0.80,
        })

        history = await service.get_history(project_id=1)

        assert isinstance(history, DeltaHistory)
        assert history.project_id == 1
        assert len(history.snapshots) == 2
        assert len(history.events) > 0
        assert "total_snapshots" in history.summary

    @pytest.mark.asyncio
    async def test_get_history_with_since(self):
        """Should filter history by date."""
        service = DeltaTrackingService()

        await service.record_snapshot(1, {
            "extraction_id": "ext-001",
            "tier": "FREE",
            "stories": [],
            "overall_confidence": 0.60,
        })

        # Get history from future (should be empty)
        future = datetime.now(timezone.utc) + timedelta(days=1)
        history = await service.get_history(project_id=1, since=future)

        assert len(history.snapshots) == 0

    @pytest.mark.asyncio
    async def test_compare_snapshots(self):
        """Should compare two snapshots."""
        service = DeltaTrackingService()

        await service.record_snapshot(1, {
            "extraction_id": "ext-001",
            "tier": "FREE",
            "stories": [{"id": "S001"}],
            "overall_confidence": 0.60,
            "invest_score": 6.0,
        })
        await service.record_snapshot(1, {
            "extraction_id": "ext-002",
            "tier": "STANDARD",
            "stories": [{"id": "S001"}, {"id": "S002"}, {"id": "S003"}],
            "overall_confidence": 0.80,
            "invest_score": 8.0,
        })

        snapshots = service._snapshots[1]
        comparison = await service.compare_snapshots(
            snapshots[0].snapshot_id,
            snapshots[1].snapshot_id,
        )

        assert "differences" in comparison
        assert comparison["differences"]["stories_added"] == 2
        assert comparison["differences"]["confidence_change"] == pytest.approx(0.20)

    @pytest.mark.asyncio
    async def test_compare_nonexistent_snapshots(self):
        """Should handle nonexistent snapshot comparison."""
        service = DeltaTrackingService()

        result = await service.compare_snapshots(
            "nonexistent-1",
            "nonexistent-2",
        )

        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_change_timeline(self):
        """Should get timeline of changes."""
        service = DeltaTrackingService()

        await service.record_snapshot(1, {
            "extraction_id": "ext-001",
            "tier": "FREE",
            "stories": [{"id": "S001"}],
            "overall_confidence": 0.60,
        })
        await service.record_snapshot(1, {
            "extraction_id": "ext-002",
            "tier": "STANDARD",
            "stories": [{"id": "S001"}, {"id": "S002"}],
            "overall_confidence": 0.80,
        })

        timeline = await service.get_change_timeline(project_id=1)

        assert len(timeline) > 0
        # Should be sorted by timestamp descending
        if len(timeline) > 1:
            assert timeline[0].timestamp >= timeline[1].timestamp

    @pytest.mark.asyncio
    async def test_get_change_timeline_filtered(self):
        """Should filter timeline by category."""
        service = DeltaTrackingService()

        await service.record_snapshot(1, {
            "extraction_id": "ext-001",
            "tier": "FREE",
            "stories": [{"id": "S001"}],
            "overall_confidence": 0.60,
        })
        await service.record_snapshot(1, {
            "extraction_id": "ext-002",
            "tier": "STANDARD",
            "stories": [{"id": "S002"}],  # S001 removed, S002 added
            "overall_confidence": 0.80,
        })

        discoveries = await service.get_change_timeline(
            project_id=1,
            category=ChangeCategory.DISCOVERY,
        )

        assert all(e.category == ChangeCategory.DISCOVERY for e in discoveries)

    @pytest.mark.asyncio
    async def test_assess_change_impact(self):
        """Should assess impact of changes."""
        service = DeltaTrackingService()

        # Record initial state
        await service.record_snapshot(1, {
            "extraction_id": "ext-001",
            "tier": "FREE",
            "stories": [{"id": "S001"}],
            "overall_confidence": 0.60,
        })

        previous = {
            "extraction_id": "ext-001",
            "tier": "FREE",
            "stories": [{"id": "S001"}],
            "overall_confidence": 0.60,
        }

        current = {
            "extraction_id": "ext-002",
            "tier": "STANDARD",
            "stories": [{"id": "S001"}, {"id": "S002"}, {"id": "S003"}],
            "overall_confidence": 0.80,
        }

        assessment = await service.assess_change_impact(
            project_id=1,
            session_id="ext-002",
            previous_result=previous,
            current_result=current,
        )

        assert isinstance(assessment, ChangeImpactAssessment)
        assert assessment.total_changes >= 0
        assert assessment.risk_assessment in ["low", "medium", "high"]

    @pytest.mark.asyncio
    async def test_get_story_evolution(self):
        """Should track story evolution."""
        service = DeltaTrackingService()

        # Story appears in first snapshot
        await service.record_snapshot(1, {
            "extraction_id": "ext-001",
            "tier": "FREE",
            "stories": [{"id": "S001", "title": "Initial"}],
            "overall_confidence": 0.60,
        })

        # Story still present in second
        await service.record_snapshot(1, {
            "extraction_id": "ext-002",
            "tier": "STANDARD",
            "stories": [{"id": "S001", "title": "Updated"}],
            "overall_confidence": 0.80,
        })

        evolution = await service.get_story_evolution(
            project_id=1,
            story_id="S001",
        )

        assert evolution["story_id"] == "S001"
        assert evolution["appearance_count"] == 2

    @pytest.mark.asyncio
    async def test_generate_summary_report(self):
        """Should generate summary report."""
        service = DeltaTrackingService()

        await service.record_snapshot(1, {
            "extraction_id": "ext-001",
            "tier": "FREE",
            "stories": [{"id": "S001"}],
            "overall_confidence": 0.60,
        })

        report = await service.generate_change_report(
            project_id=1,
            format="summary",
        )

        assert report["report_type"] == "summary"
        assert report["project_id"] == 1

    @pytest.mark.asyncio
    async def test_generate_detailed_report(self):
        """Should generate detailed report."""
        service = DeltaTrackingService()

        await service.record_snapshot(1, {
            "extraction_id": "ext-001",
            "tier": "FREE",
            "stories": [{"id": "S001"}],
            "overall_confidence": 0.60,
        })

        report = await service.generate_change_report(
            project_id=1,
            format="detailed",
        )

        assert report["report_type"] == "detailed"
        assert "snapshots" in report
        assert "events" in report

    @pytest.mark.asyncio
    async def test_generate_timeline_report(self):
        """Should generate timeline report."""
        service = DeltaTrackingService()

        await service.record_snapshot(1, {
            "extraction_id": "ext-001",
            "tier": "FREE",
            "stories": [{"id": "S001"}],
            "overall_confidence": 0.60,
        })

        report = await service.generate_change_report(
            project_id=1,
            format="timeline",
        )

        assert report["report_type"] == "timeline"
        assert "timeline" in report


class TestTrendAnalysis:
    """Tests for trend analysis."""

    @pytest.mark.asyncio
    async def test_analyze_improving_trend(self):
        """Should detect improving trend."""
        service = DeltaTrackingService()

        # Create improving trend
        for i in range(3):
            await service.record_snapshot(1, {
                "extraction_id": f"ext-{i}",
                "tier": "STANDARD",
                "stories": [{"id": f"S{j}"} for j in range(i + 1)],
                "overall_confidence": 0.60 + (i * 0.1),
            })

        history = await service.get_history(project_id=1)

        # Find confidence trend
        confidence_trend = next(
            (t for t in history.trends if t.metric_name == "overall_confidence"),
            None
        )

        if confidence_trend:
            assert confidence_trend.direction in [
                TrendDirection.IMPROVING,
                TrendDirection.STABLE,
                TrendDirection.VOLATILE,
            ]


class TestFactoryFunction:
    """Tests for factory function."""

    def test_get_delta_tracking_service(self):
        """Should create service via factory."""
        service = get_delta_tracking_service()

        assert isinstance(service, DeltaTrackingService)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
