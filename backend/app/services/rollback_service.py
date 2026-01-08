"""
Rollback Service

Week 25-26: AgentEvolver Integration - Rollback Mechanisms & Safety
Based on: github.com/zeeneddie/AgentEvolver

Implements safety mechanisms:
1. Automatic rollback triggers
2. State snapshots before learning
3. Rollback to previous states
4. Monitoring and auto-recovery
5. Audit logging

Author: Claude Code (Week 26 Day 3-4)
Date: 2025-11-22
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import logging
import json
import copy

from app.services.experience_store_service import (
    AgentRole,
    WorkType
)
from app.services.agent_evolution_service import (
    EvolutionConfig
)

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND TYPES
# ============================================================================

class RollbackTrigger(str, Enum):
    """Triggers for automatic rollback"""
    SUCCESS_RATE_DROP = "success_rate_drop"
    QUALITY_SCORE_DROP = "quality_score_drop"
    ESTIMATION_ERROR = "estimation_error"
    VALIDATION_FAILURES = "validation_failures"
    MANUAL = "manual"


class RollbackStatus(str, Enum):
    """Status of a rollback operation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ApprovalStatus(str, Enum):
    """Status of human approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Snapshot:
    """A snapshot of agent state"""
    id: str
    agent_id: str
    created_at: datetime
    description: str

    # State data
    evolution_config: Dict[str, Any]
    pattern_weights: Dict[str, float]
    threshold_config: Dict[str, Any]
    learning_metrics: Dict[str, Any]

    # Metadata
    trigger: str = "manual"
    is_baseline: bool = False
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "evolution_config": self.evolution_config,
            "pattern_weights": self.pattern_weights,
            "threshold_config": self.threshold_config,
            "learning_metrics": self.learning_metrics,
            "trigger": self.trigger,
            "is_baseline": self.is_baseline,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


@dataclass
class RollbackEvent:
    """A rollback event record"""
    id: str
    agent_id: str
    trigger: RollbackTrigger
    status: RollbackStatus
    snapshot_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None

    # Metrics before rollback
    metrics_before: Dict[str, Any] = field(default_factory=dict)
    # Metrics after rollback
    metrics_after: Dict[str, Any] = field(default_factory=dict)

    # Details
    reason: str = ""
    initiated_by: str = "system"  # 'system' or 'user'
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "trigger": self.trigger.value,
            "status": self.status.value,
            "snapshot_id": self.snapshot_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metrics_before": self.metrics_before,
            "metrics_after": self.metrics_after,
            "reason": self.reason,
            "initiated_by": self.initiated_by,
            "notes": self.notes
        }


@dataclass
class RollbackResult:
    """Result of a rollback operation"""
    event_id: str
    agent_id: str
    success: bool
    duration_ms: int
    state_restored: bool
    metrics_improved: bool
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "agent_id": self.agent_id,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "state_restored": self.state_restored,
            "metrics_improved": self.metrics_improved,
            "message": self.message
        }


@dataclass
class MonitorResult:
    """Result of monitoring check"""
    agent_id: str
    timestamp: datetime
    health_status: str  # 'healthy', 'warning', 'critical'
    triggered_rollback: bool
    trigger_reason: Optional[str] = None
    current_metrics: Dict[str, Any] = field(default_factory=dict)
    threshold_violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "health_status": self.health_status,
            "triggered_rollback": self.triggered_rollback,
            "trigger_reason": self.trigger_reason,
            "current_metrics": self.current_metrics,
            "threshold_violations": self.threshold_violations
        }


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    id: str
    agent_id: str
    change_type: str
    change_description: str
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    status: ApprovalStatus
    requested_at: datetime
    responded_at: Optional[datetime] = None
    responder: Optional[str] = None
    response_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "change_type": self.change_type,
            "change_description": self.change_description,
            "risk_level": self.risk_level,
            "status": self.status.value,
            "requested_at": self.requested_at.isoformat(),
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "responder": self.responder,
            "response_notes": self.response_notes
        }


@dataclass
class AuditLog:
    """Audit log entry"""
    id: str
    timestamp: datetime
    agent_id: str
    action: str
    details: Dict[str, Any]
    result: str
    initiated_by: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "action": self.action,
            "details": self.details,
            "result": self.result,
            "initiated_by": self.initiated_by
        }


# ============================================================================
# ROLLBACK SERVICE
# ============================================================================

class RollbackService:
    """
    Service for rollback mechanisms and safety guardrails.

    Implements:
    - Automatic rollback triggers
    - State snapshots
    - Safe rollback operations
    - Continuous monitoring
    - Human approval workflow
    - Audit logging
    """

    # Rollback trigger thresholds
    ROLLBACK_TRIGGERS = {
        'success_rate_drop': 0.10,      # >10% drop triggers rollback
        'quality_score_drop': 0.15,     # >15% drop triggers rollback
        'estimation_error_increase': 0.20,  # >20% increase triggers rollback
        'validation_failure_rate': 0.30  # >30% validation failures
    }

    # Rate limiting
    MAX_UPDATES_PER_HOUR = 10
    COOLDOWN_AFTER_ROLLBACK = 3600  # 1 hour in seconds

    def __init__(self):
        # In-memory storage (in production, use database)
        self._snapshots: Dict[str, List[Snapshot]] = {}
        self._rollback_events: List[RollbackEvent] = []
        self._approval_requests: Dict[str, ApprovalRequest] = {}
        self._audit_logs: List[AuditLog] = []

        # Agent state tracking
        self._agent_states: Dict[str, Dict[str, Any]] = {}
        self._baseline_snapshots: Dict[str, str] = {}  # agent_id -> snapshot_id

        # Rate limiting
        self._update_counts: Dict[str, List[datetime]] = {}
        self._last_rollback: Dict[str, datetime] = {}

    # -------------------------------------------------------------------------
    # SNAPSHOT MANAGEMENT
    # -------------------------------------------------------------------------

    async def create_snapshot(
        self,
        agent_id: str,
        description: str = "Automatic snapshot",
        is_baseline: bool = False
    ) -> Snapshot:
        """
        Create a snapshot of current agent state before learning.
        """
        snapshot_id = str(uuid.uuid4())

        # Get current state (mock data for now)
        current_state = self._get_agent_state(agent_id)

        snapshot = Snapshot(
            id=snapshot_id,
            agent_id=agent_id,
            created_at=datetime.now(),
            description=description,
            evolution_config=current_state.get("evolution_config", {}),
            pattern_weights=current_state.get("pattern_weights", {}),
            threshold_config=current_state.get("threshold_config", {}),
            learning_metrics=current_state.get("learning_metrics", {}),
            is_baseline=is_baseline,
            expires_at=datetime.now() + timedelta(days=30) if not is_baseline else None
        )

        # Store snapshot
        if agent_id not in self._snapshots:
            self._snapshots[agent_id] = []
        self._snapshots[agent_id].append(snapshot)

        # Update baseline if needed
        if is_baseline:
            self._baseline_snapshots[agent_id] = snapshot_id

        # Audit log
        self._log_action(agent_id, "create_snapshot", {
            "snapshot_id": snapshot_id,
            "is_baseline": is_baseline
        }, "success")

        logger.info(f"Created snapshot {snapshot_id} for agent {agent_id}")

        return snapshot

    async def get_snapshots(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[Snapshot]:
        """Get recent snapshots for an agent"""
        snapshots = self._snapshots.get(agent_id, [])
        return snapshots[-limit:]

    async def get_baseline_snapshot(self, agent_id: str) -> Optional[Snapshot]:
        """Get the baseline snapshot for an agent"""
        baseline_id = self._baseline_snapshots.get(agent_id)
        if not baseline_id:
            return None

        snapshots = self._snapshots.get(agent_id, [])
        return next((s for s in snapshots if s.id == baseline_id), None)

    # -------------------------------------------------------------------------
    # ROLLBACK OPERATIONS
    # -------------------------------------------------------------------------

    async def rollback_to_snapshot(
        self,
        agent_id: str,
        snapshot_id: str,
        reason: str = "Manual rollback"
    ) -> RollbackResult:
        """
        Rollback agent to a previous snapshot state.
        """
        import time
        start_time = time.time()

        # Find snapshot
        snapshots = self._snapshots.get(agent_id, [])
        snapshot = next((s for s in snapshots if s.id == snapshot_id), None)

        if not snapshot:
            return RollbackResult(
                event_id="",
                agent_id=agent_id,
                success=False,
                duration_ms=0,
                state_restored=False,
                metrics_improved=False,
                message=f"Snapshot {snapshot_id} not found"
            )

        # Check cooldown
        if agent_id in self._last_rollback:
            time_since = (datetime.now() - self._last_rollback[agent_id]).seconds
            if time_since < self.COOLDOWN_AFTER_ROLLBACK:
                return RollbackResult(
                    event_id="",
                    agent_id=agent_id,
                    success=False,
                    duration_ms=0,
                    state_restored=False,
                    metrics_improved=False,
                    message=f"Cooldown active. Please wait {self.COOLDOWN_AFTER_ROLLBACK - time_since}s"
                )

        # Create rollback event
        event = RollbackEvent(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            trigger=RollbackTrigger.MANUAL,
            status=RollbackStatus.IN_PROGRESS,
            snapshot_id=snapshot_id,
            started_at=datetime.now(),
            metrics_before=self._get_agent_state(agent_id).get("learning_metrics", {}),
            reason=reason
        )

        self._rollback_events.append(event)

        try:
            # Restore state from snapshot
            self._agent_states[agent_id] = {
                "evolution_config": copy.deepcopy(snapshot.evolution_config),
                "pattern_weights": copy.deepcopy(snapshot.pattern_weights),
                "threshold_config": copy.deepcopy(snapshot.threshold_config),
                "learning_metrics": copy.deepcopy(snapshot.learning_metrics)
            }

            # Update event
            event.status = RollbackStatus.COMPLETED
            event.completed_at = datetime.now()
            event.metrics_after = snapshot.learning_metrics

            # Update cooldown
            self._last_rollback[agent_id] = datetime.now()

            # Audit log
            self._log_action(agent_id, "rollback", {
                "snapshot_id": snapshot_id,
                "reason": reason
            }, "success")

            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(f"Rolled back agent {agent_id} to snapshot {snapshot_id}")

            return RollbackResult(
                event_id=event.id,
                agent_id=agent_id,
                success=True,
                duration_ms=duration_ms,
                state_restored=True,
                metrics_improved=True,
                message="Successfully rolled back to snapshot"
            )

        except Exception as e:
            event.status = RollbackStatus.FAILED
            event.notes.append(f"Error: {str(e)}")

            self._log_action(agent_id, "rollback", {
                "snapshot_id": snapshot_id,
                "error": str(e)
            }, "failed")

            return RollbackResult(
                event_id=event.id,
                agent_id=agent_id,
                success=False,
                duration_ms=int((time.time() - start_time) * 1000),
                state_restored=False,
                metrics_improved=False,
                message=f"Rollback failed: {str(e)}"
            )

    async def manual_rollback(
        self,
        agent_id: str,
        reason: str
    ) -> RollbackResult:
        """
        Manually trigger rollback to the most recent snapshot.
        """
        snapshots = self._snapshots.get(agent_id, [])

        if not snapshots:
            return RollbackResult(
                event_id="",
                agent_id=agent_id,
                success=False,
                duration_ms=0,
                state_restored=False,
                metrics_improved=False,
                message="No snapshots available for rollback"
            )

        # Get most recent snapshot
        latest_snapshot = snapshots[-1]

        return await self.rollback_to_snapshot(agent_id, latest_snapshot.id, reason)

    # -------------------------------------------------------------------------
    # MONITORING AND AUTO-ROLLBACK
    # -------------------------------------------------------------------------

    async def monitor_and_rollback(self, agent_id: str) -> MonitorResult:
        """
        Monitor agent performance and trigger rollback if needed.
        """
        current_state = self._get_agent_state(agent_id)
        current_metrics = current_state.get("learning_metrics", {})

        # Get baseline for comparison
        baseline = await self.get_baseline_snapshot(agent_id)
        baseline_metrics = baseline.learning_metrics if baseline else {}

        threshold_violations = []
        health_status = "healthy"

        # Check success rate
        current_success = current_metrics.get("success_rate", 0.7)
        baseline_success = baseline_metrics.get("success_rate", 0.7)
        success_drop = baseline_success - current_success

        if success_drop > self.ROLLBACK_TRIGGERS['success_rate_drop']:
            threshold_violations.append(f"Success rate dropped by {success_drop:.1%}")
            health_status = "critical"

        # Check quality score
        current_quality = current_metrics.get("quality_score", 70)
        baseline_quality = baseline_metrics.get("quality_score", 70)
        quality_drop = (baseline_quality - current_quality) / max(baseline_quality, 1)

        if quality_drop > self.ROLLBACK_TRIGGERS['quality_score_drop']:
            threshold_violations.append(f"Quality score dropped by {quality_drop:.1%}")
            health_status = "critical" if health_status == "critical" else "warning"

        # Trigger rollback if critical
        triggered_rollback = False
        trigger_reason = None

        if health_status == "critical" and baseline:
            logger.warning(f"Agent {agent_id} health critical, triggering rollback")
            trigger_reason = "; ".join(threshold_violations)

            result = await self.rollback_to_snapshot(
                agent_id,
                baseline.id,
                f"Automatic rollback: {trigger_reason}"
            )

            triggered_rollback = result.success

        return MonitorResult(
            agent_id=agent_id,
            timestamp=datetime.now(),
            health_status=health_status,
            triggered_rollback=triggered_rollback,
            trigger_reason=trigger_reason,
            current_metrics=current_metrics,
            threshold_violations=threshold_violations
        )

    # -------------------------------------------------------------------------
    # SAFETY GUARDRAILS
    # -------------------------------------------------------------------------

    async def check_rate_limit(self, agent_id: str) -> bool:
        """
        Check if agent has exceeded rate limit for updates.
        """
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        # Clean old entries
        if agent_id in self._update_counts:
            self._update_counts[agent_id] = [
                t for t in self._update_counts[agent_id]
                if t > hour_ago
            ]
        else:
            self._update_counts[agent_id] = []

        return len(self._update_counts[agent_id]) < self.MAX_UPDATES_PER_HOUR

    async def record_update(self, agent_id: str) -> None:
        """Record an update for rate limiting"""
        if agent_id not in self._update_counts:
            self._update_counts[agent_id] = []
        self._update_counts[agent_id].append(datetime.now())

    async def request_human_approval(
        self,
        agent_id: str,
        change_type: str,
        change_description: str,
        risk_level: str = "medium"
    ) -> ApprovalRequest:
        """
        Request human approval for a major change.
        """
        request = ApprovalRequest(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            change_type=change_type,
            change_description=change_description,
            risk_level=risk_level,
            status=ApprovalStatus.PENDING,
            requested_at=datetime.now()
        )

        self._approval_requests[request.id] = request

        # Auto-approve low risk changes
        if risk_level == "low":
            request.status = ApprovalStatus.AUTO_APPROVED
            request.responded_at = datetime.now()
            request.responder = "system"
            request.response_notes = "Auto-approved due to low risk"

        logger.info(f"Approval request {request.id} created for {agent_id}")

        return request

    async def respond_to_approval(
        self,
        request_id: str,
        approved: bool,
        responder: str,
        notes: str = ""
    ) -> ApprovalRequest:
        """Respond to an approval request"""
        request = self._approval_requests.get(request_id)
        if not request:
            raise ValueError(f"Approval request {request_id} not found")

        request.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        request.responded_at = datetime.now()
        request.responder = responder
        request.response_notes = notes

        self._log_action(request.agent_id, "approval_response", {
            "request_id": request_id,
            "approved": approved,
            "responder": responder
        }, "success")

        return request

    async def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approval requests"""
        return [
            r for r in self._approval_requests.values()
            if r.status == ApprovalStatus.PENDING
        ]

    # -------------------------------------------------------------------------
    # ROLLBACK HISTORY
    # -------------------------------------------------------------------------

    async def get_rollback_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 50
    ) -> List[RollbackEvent]:
        """Get rollback history"""
        events = self._rollback_events

        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]

        return events[-limit:]

    # -------------------------------------------------------------------------
    # AUDIT LOGGING
    # -------------------------------------------------------------------------

    def _log_action(
        self,
        agent_id: str,
        action: str,
        details: Dict[str, Any],
        result: str
    ) -> None:
        """Log an action to the audit log"""
        log = AuditLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            agent_id=agent_id,
            action=action,
            details=details,
            result=result,
            initiated_by="system"
        )
        self._audit_logs.append(log)

    async def get_audit_logs(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs"""
        logs = self._audit_logs

        if agent_id:
            logs = [l for l in logs if l.agent_id == agent_id]

        return logs[-limit:]

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def _get_agent_state(self, agent_id: str) -> Dict[str, Any]:
        """Get current agent state"""
        if agent_id not in self._agent_states:
            # Initialize with default state
            self._agent_states[agent_id] = {
                "evolution_config": {
                    "learning_rate": 0.1,
                    "experience_weight": 0.7,
                    "exploration_rate": 0.2
                },
                "pattern_weights": {},
                "threshold_config": {
                    "min_confidence": 0.6,
                    "min_quality_score": 70
                },
                "learning_metrics": {
                    "success_rate": 0.7,
                    "quality_score": 75,
                    "total_sessions": 0
                }
            }
        return self._agent_states[agent_id]


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_rollback_service: Optional[RollbackService] = None


async def get_rollback_service() -> RollbackService:
    """Get or create rollback service instance"""
    global _rollback_service
    if _rollback_service is None:
        _rollback_service = RollbackService()
    return _rollback_service
