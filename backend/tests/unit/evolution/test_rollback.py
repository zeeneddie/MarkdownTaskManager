"""
Integration Tests for Rollback API

Week 25-26: AgentEvolver Integration - Rollback Tests

Author: Claude Code (Week 26 Day 5)
Date: 2025-11-22
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.rollback_service import (
    RollbackService,
    Snapshot,
    RollbackEvent,
    RollbackResult,
    MonitorResult,
    ApprovalRequest,
    AuditLog,
    RollbackTrigger,
    RollbackStatus,
    ApprovalStatus
)


class TestRollbackService:
    """Tests for RollbackService"""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance"""
        return RollbackService()

    # -------------------------------------------------------------------------
    # SNAPSHOT TESTS
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_snapshot(self, service):
        """Test creating a snapshot"""
        snapshot = await service.create_snapshot(
            agent_id="felix",
            description="Test snapshot",
            is_baseline=False
        )

        assert isinstance(snapshot, Snapshot)
        assert snapshot.agent_id == "felix"
        assert snapshot.description == "Test snapshot"
        assert not snapshot.is_baseline
        assert snapshot.id in [s.id for s in service._snapshots.get("felix", [])]

    @pytest.mark.asyncio
    async def test_create_baseline_snapshot(self, service):
        """Test creating a baseline snapshot"""
        snapshot = await service.create_snapshot(
            agent_id="marcus",
            description="Baseline",
            is_baseline=True
        )

        assert snapshot.is_baseline
        assert service._baseline_snapshots.get("marcus") == snapshot.id

    @pytest.mark.asyncio
    async def test_get_snapshots(self, service):
        """Test getting snapshots for an agent"""
        # Create multiple snapshots
        for i in range(5):
            await service.create_snapshot(
                agent_id="quinn",
                description=f"Snapshot {i}"
            )

        snapshots = await service.get_snapshots("quinn", limit=3)

        assert len(snapshots) == 3
        assert all(s.agent_id == "quinn" for s in snapshots)

    @pytest.mark.asyncio
    async def test_get_baseline_snapshot(self, service):
        """Test getting baseline snapshot"""
        # No baseline yet
        baseline = await service.get_baseline_snapshot("betty")
        assert baseline is None

        # Create baseline
        snapshot = await service.create_snapshot(
            agent_id="betty",
            description="Baseline",
            is_baseline=True
        )

        baseline = await service.get_baseline_snapshot("betty")
        assert baseline is not None
        assert baseline.id == snapshot.id

    # -------------------------------------------------------------------------
    # ROLLBACK TESTS
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_rollback_to_snapshot_success(self, service):
        """Test successful rollback to snapshot"""
        # Create a snapshot
        snapshot = await service.create_snapshot(
            agent_id="eliza",
            description="Before changes"
        )

        result = await service.rollback_to_snapshot(
            agent_id="eliza",
            snapshot_id=snapshot.id,
            reason="Testing rollback"
        )

        assert isinstance(result, RollbackResult)
        assert result.success
        assert result.state_restored
        assert result.agent_id == "eliza"

    @pytest.mark.asyncio
    async def test_rollback_to_invalid_snapshot(self, service):
        """Test rollback to non-existent snapshot"""
        result = await service.rollback_to_snapshot(
            agent_id="tessa",
            snapshot_id="invalid-id",
            reason="Test"
        )

        assert not result.success
        assert "not found" in result.message

    @pytest.mark.asyncio
    async def test_rollback_cooldown(self, service):
        """Test rollback cooldown prevents rapid rollbacks"""
        # Create snapshot
        snapshot = await service.create_snapshot(
            agent_id="miguel",
            description="Test"
        )

        # First rollback
        result1 = await service.rollback_to_snapshot(
            "miguel", snapshot.id, "First rollback"
        )
        assert result1.success

        # Immediate second rollback should be blocked
        result2 = await service.rollback_to_snapshot(
            "miguel", snapshot.id, "Second rollback"
        )
        assert not result2.success
        assert "Cooldown" in result2.message

    @pytest.mark.asyncio
    async def test_manual_rollback(self, service):
        """Test manual rollback to latest snapshot"""
        # Create snapshot
        await service.create_snapshot(
            agent_id="diana",
            description="Latest"
        )

        result = await service.manual_rollback(
            agent_id="diana",
            reason="Manual test"
        )

        assert result.success

    @pytest.mark.asyncio
    async def test_manual_rollback_no_snapshots(self, service):
        """Test manual rollback when no snapshots exist"""
        result = await service.manual_rollback(
            agent_id="new_agent",
            reason="Test"
        )

        assert not result.success
        assert "No snapshots" in result.message

    # -------------------------------------------------------------------------
    # MONITORING TESTS
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_monitor_healthy_agent(self, service):
        """Test monitoring a healthy agent"""
        # Create baseline with good metrics
        await service.create_snapshot(
            agent_id="peter",
            description="Baseline",
            is_baseline=True
        )

        result = await service.monitor_and_rollback("peter")

        assert isinstance(result, MonitorResult)
        assert result.health_status in ["healthy", "warning", "critical"]
        assert result.agent_id == "peter"

    @pytest.mark.asyncio
    async def test_monitor_no_baseline(self, service):
        """Test monitoring without baseline"""
        result = await service.monitor_and_rollback("paul")

        assert not result.triggered_rollback
        # No baseline means no comparison

    # -------------------------------------------------------------------------
    # RATE LIMITING TESTS
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_rate_limit_check(self, service):
        """Test rate limit checking"""
        within_limit = await service.check_rate_limit("felix")
        assert within_limit

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, service):
        """Test rate limit when exceeded"""
        agent_id = "rate_test_agent"

        # Record many updates
        for _ in range(service.MAX_UPDATES_PER_HOUR + 5):
            await service.record_update(agent_id)

        within_limit = await service.check_rate_limit(agent_id)
        assert not within_limit

    # -------------------------------------------------------------------------
    # APPROVAL TESTS
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_request_human_approval(self, service):
        """Test requesting human approval"""
        request = await service.request_human_approval(
            agent_id="marcus",
            change_type="threshold_update",
            change_description="Updating validation thresholds",
            risk_level="medium"
        )

        assert isinstance(request, ApprovalRequest)
        assert request.agent_id == "marcus"
        assert request.status == ApprovalStatus.PENDING

    @pytest.mark.asyncio
    async def test_auto_approve_low_risk(self, service):
        """Test auto-approval for low risk changes"""
        request = await service.request_human_approval(
            agent_id="quinn",
            change_type="minor_update",
            change_description="Small change",
            risk_level="low"
        )

        assert request.status == ApprovalStatus.AUTO_APPROVED
        assert request.responder == "system"

    @pytest.mark.asyncio
    async def test_respond_to_approval(self, service):
        """Test responding to approval request"""
        request = await service.request_human_approval(
            agent_id="betty",
            change_type="major_update",
            change_description="Big change",
            risk_level="high"
        )

        updated = await service.respond_to_approval(
            request_id=request.id,
            approved=True,
            responder="admin",
            notes="Approved after review"
        )

        assert updated.status == ApprovalStatus.APPROVED
        assert updated.responder == "admin"

    @pytest.mark.asyncio
    async def test_respond_to_invalid_approval(self, service):
        """Test responding to non-existent approval"""
        with pytest.raises(ValueError):
            await service.respond_to_approval(
                request_id="invalid",
                approved=True,
                responder="admin"
            )

    @pytest.mark.asyncio
    async def test_get_pending_approvals(self, service):
        """Test getting pending approvals"""
        # Create multiple requests
        await service.request_human_approval(
            "agent1", "type1", "desc1", "medium"
        )
        await service.request_human_approval(
            "agent2", "type2", "desc2", "high"
        )
        await service.request_human_approval(
            "agent3", "type3", "desc3", "low"  # Auto-approved
        )

        pending = await service.get_pending_approvals()

        # Should only include medium and high risk (not auto-approved)
        assert len(pending) == 2

    # -------------------------------------------------------------------------
    # AUDIT LOG TESTS
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_audit_log_creation(self, service):
        """Test audit logs are created for actions"""
        # Create snapshot (should log)
        await service.create_snapshot("eliza", "Test")

        logs = await service.get_audit_logs("eliza")

        assert len(logs) >= 1
        assert logs[-1].action == "create_snapshot"
        assert logs[-1].result == "success"

    @pytest.mark.asyncio
    async def test_get_audit_logs_filtered(self, service):
        """Test getting filtered audit logs"""
        # Create actions for multiple agents
        await service.create_snapshot("tessa", "Test")
        await service.create_snapshot("miguel", "Test")

        tessa_logs = await service.get_audit_logs("tessa")
        miguel_logs = await service.get_audit_logs("miguel")

        assert all(l.agent_id == "tessa" for l in tessa_logs)
        assert all(l.agent_id == "miguel" for l in miguel_logs)

    # -------------------------------------------------------------------------
    # HISTORY TESTS
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_rollback_history(self, service):
        """Test getting rollback history"""
        # Create snapshot and rollback
        snapshot = await service.create_snapshot("diana", "Test")
        await service.rollback_to_snapshot("diana", snapshot.id, "Test")

        history = await service.get_rollback_history("diana")

        assert len(history) >= 1
        assert history[-1].agent_id == "diana"

    @pytest.mark.asyncio
    async def test_get_rollback_history_all_agents(self, service):
        """Test getting rollback history for all agents"""
        history = await service.get_rollback_history(limit=100)

        assert isinstance(history, list)


class TestRollbackIntegration:
    """Integration tests for rollback scenarios"""

    @pytest.fixture
    def service(self):
        return RollbackService()

    @pytest.mark.asyncio
    async def test_full_rollback_cycle(self, service):
        """Test complete rollback cycle: snapshot -> change -> rollback"""
        agent_id = "integration_test"

        # 1. Create baseline
        baseline = await service.create_snapshot(
            agent_id, "Baseline", is_baseline=True
        )

        # 2. Create another snapshot (simulating a change)
        await service.create_snapshot(agent_id, "After change")

        # 3. Monitor (should be healthy since no actual metric change)
        monitor_result = await service.monitor_and_rollback(agent_id)

        # 4. Manual rollback to baseline
        # Need to clear cooldown for test
        service._last_rollback.pop(agent_id, None)

        rollback_result = await service.rollback_to_snapshot(
            agent_id, baseline.id, "Reverting to baseline"
        )

        assert rollback_result.success

        # 5. Check audit logs
        logs = await service.get_audit_logs(agent_id)
        actions = [l.action for l in logs]

        assert "create_snapshot" in actions
        assert "rollback" in actions

    @pytest.mark.asyncio
    async def test_approval_workflow(self, service):
        """Test complete approval workflow"""
        agent_id = "approval_test"

        # 1. Request approval for high-risk change
        request = await service.request_human_approval(
            agent_id=agent_id,
            change_type="behavior_change",
            change_description="Major agent behavior modification",
            risk_level="critical"
        )

        assert request.status == ApprovalStatus.PENDING

        # 2. Check pending approvals
        pending = await service.get_pending_approvals()
        assert request.id in [p.id for p in pending]

        # 3. Respond to approval
        approved = await service.respond_to_approval(
            request.id,
            approved=True,
            responder="senior_engineer",
            notes="Reviewed and approved"
        )

        assert approved.status == ApprovalStatus.APPROVED

        # 4. Check no longer pending
        pending = await service.get_pending_approvals()
        assert request.id not in [p.id for p in pending]
