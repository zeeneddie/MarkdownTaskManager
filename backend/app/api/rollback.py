"""
Rollback API

Week 25-26: AgentEvolver Integration - Rollback API Endpoints
Based on: github.com/zeeneddie/AgentEvolver

API endpoints for:
- Snapshot management
- Rollback operations
- Monitoring
- Approval workflow
- Audit logs

Author: Claude Code (Week 26 Day 4)
Date: 2025-11-22
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.rollback_service import (
    RollbackService,
    get_rollback_service,
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

router = APIRouter(prefix="/api/rollback", tags=["Rollback"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateSnapshotRequest(BaseModel):
    """Request to create a snapshot"""
    description: str = Field("Manual snapshot", description="Snapshot description")
    is_baseline: bool = Field(False, description="Whether this is a baseline snapshot")


class RollbackRequest(BaseModel):
    """Request to rollback to a snapshot"""
    reason: str = Field(..., description="Reason for rollback")


class ApprovalResponseRequest(BaseModel):
    """Request to respond to an approval"""
    approved: bool = Field(..., description="Whether to approve")
    responder: str = Field(..., description="Who is responding")
    notes: str = Field("", description="Response notes")


class SnapshotResponse(BaseModel):
    """Response for snapshot"""
    id: str
    agent_id: str
    created_at: str
    description: str
    is_baseline: bool
    expires_at: Optional[str]


class RollbackEventResponse(BaseModel):
    """Response for rollback event"""
    id: str
    agent_id: str
    trigger: str
    status: str
    snapshot_id: str
    started_at: str
    completed_at: Optional[str]
    reason: str
    initiated_by: str


class RollbackResultResponse(BaseModel):
    """Response for rollback result"""
    event_id: str
    agent_id: str
    success: bool
    duration_ms: int
    state_restored: bool
    metrics_improved: bool
    message: str


class MonitorResultResponse(BaseModel):
    """Response for monitor result"""
    agent_id: str
    timestamp: str
    health_status: str
    triggered_rollback: bool
    trigger_reason: Optional[str]
    threshold_violations: List[str]


class ApprovalRequestResponse(BaseModel):
    """Response for approval request"""
    id: str
    agent_id: str
    change_type: str
    change_description: str
    risk_level: str
    status: str
    requested_at: str
    responded_at: Optional[str]
    responder: Optional[str]


class AuditLogResponse(BaseModel):
    """Response for audit log"""
    id: str
    timestamp: str
    agent_id: str
    action: str
    result: str
    initiated_by: str


# ============================================================================
# SNAPSHOT ENDPOINTS
# ============================================================================

@router.post("/snapshots/{agent_id}", response_model=SnapshotResponse)
async def create_snapshot(
    agent_id: str,
    request: CreateSnapshotRequest = None
):
    """
    Create a snapshot of agent state.
    """
    try:
        service = await get_rollback_service()

        description = request.description if request else "Manual snapshot"
        is_baseline = request.is_baseline if request else False

        snapshot = await service.create_snapshot(
            agent_id=agent_id,
            description=description,
            is_baseline=is_baseline
        )

        return SnapshotResponse(
            id=snapshot.id,
            agent_id=snapshot.agent_id,
            created_at=snapshot.created_at.isoformat(),
            description=snapshot.description,
            is_baseline=snapshot.is_baseline,
            expires_at=snapshot.expires_at.isoformat() if snapshot.expires_at else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/snapshots/{agent_id}", response_model=List[SnapshotResponse])
async def get_snapshots(
    agent_id: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum snapshots to return")
):
    """
    Get snapshots for an agent.
    """
    try:
        service = await get_rollback_service()
        snapshots = await service.get_snapshots(agent_id, limit)

        return [
            SnapshotResponse(
                id=s.id,
                agent_id=s.agent_id,
                created_at=s.created_at.isoformat(),
                description=s.description,
                is_baseline=s.is_baseline,
                expires_at=s.expires_at.isoformat() if s.expires_at else None
            )
            for s in snapshots
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/snapshots/{agent_id}/baseline", response_model=Optional[SnapshotResponse])
async def get_baseline_snapshot(agent_id: str):
    """
    Get the baseline snapshot for an agent.
    """
    try:
        service = await get_rollback_service()
        snapshot = await service.get_baseline_snapshot(agent_id)

        if not snapshot:
            return None

        return SnapshotResponse(
            id=snapshot.id,
            agent_id=snapshot.agent_id,
            created_at=snapshot.created_at.isoformat(),
            description=snapshot.description,
            is_baseline=snapshot.is_baseline,
            expires_at=snapshot.expires_at.isoformat() if snapshot.expires_at else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ROLLBACK ENDPOINTS
# ============================================================================

@router.post("/execute/{agent_id}/{snapshot_id}", response_model=RollbackResultResponse)
async def rollback_to_snapshot(
    agent_id: str,
    snapshot_id: str,
    request: RollbackRequest
):
    """
    Rollback an agent to a specific snapshot.
    """
    try:
        service = await get_rollback_service()

        result = await service.rollback_to_snapshot(
            agent_id=agent_id,
            snapshot_id=snapshot_id,
            reason=request.reason
        )

        return RollbackResultResponse(**result.to_dict())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{agent_id}/latest", response_model=RollbackResultResponse)
async def rollback_to_latest(
    agent_id: str,
    request: RollbackRequest
):
    """
    Rollback an agent to the most recent snapshot.
    """
    try:
        service = await get_rollback_service()
        result = await service.manual_rollback(agent_id, request.reason)

        return RollbackResultResponse(**result.to_dict())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[RollbackEventResponse])
async def get_rollback_history(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum events to return")
):
    """
    Get rollback history.
    """
    try:
        service = await get_rollback_service()
        events = await service.get_rollback_history(agent_id, limit)

        return [
            RollbackEventResponse(
                id=e.id,
                agent_id=e.agent_id,
                trigger=e.trigger.value,
                status=e.status.value,
                snapshot_id=e.snapshot_id,
                started_at=e.started_at.isoformat(),
                completed_at=e.completed_at.isoformat() if e.completed_at else None,
                reason=e.reason,
                initiated_by=e.initiated_by
            )
            for e in events
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MONITORING ENDPOINTS
# ============================================================================

@router.post("/monitor/{agent_id}", response_model=MonitorResultResponse)
async def monitor_agent(agent_id: str):
    """
    Monitor agent performance and trigger rollback if needed.
    """
    try:
        service = await get_rollback_service()
        result = await service.monitor_and_rollback(agent_id)

        return MonitorResultResponse(
            agent_id=result.agent_id,
            timestamp=result.timestamp.isoformat(),
            health_status=result.health_status,
            triggered_rollback=result.triggered_rollback,
            trigger_reason=result.trigger_reason,
            threshold_violations=result.threshold_violations
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/all")
async def monitor_all_agents():
    """
    Monitor all agents and return health status.
    """
    try:
        service = await get_rollback_service()

        agent_ids = [
            "felix", "marcus", "quinn", "betty", "eliza",
            "tessa", "miguel", "diana", "peter", "paul"
        ]

        results = []
        for agent_id in agent_ids:
            result = await service.monitor_and_rollback(agent_id)
            results.append(result.to_dict())

        return {
            "timestamp": datetime.now().isoformat(),
            "agents_monitored": len(results),
            "rollbacks_triggered": sum(1 for r in results if r["triggered_rollback"]),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# APPROVAL ENDPOINTS
# ============================================================================

@router.get("/approvals/pending", response_model=List[ApprovalRequestResponse])
async def get_pending_approvals():
    """
    Get all pending approval requests.
    """
    try:
        service = await get_rollback_service()
        approvals = await service.get_pending_approvals()

        return [
            ApprovalRequestResponse(
                id=a.id,
                agent_id=a.agent_id,
                change_type=a.change_type,
                change_description=a.change_description,
                risk_level=a.risk_level,
                status=a.status.value,
                requested_at=a.requested_at.isoformat(),
                responded_at=a.responded_at.isoformat() if a.responded_at else None,
                responder=a.responder
            )
            for a in approvals
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approvals/{request_id}/respond", response_model=ApprovalRequestResponse)
async def respond_to_approval(
    request_id: str,
    request: ApprovalResponseRequest
):
    """
    Respond to an approval request.
    """
    try:
        service = await get_rollback_service()

        approval = await service.respond_to_approval(
            request_id=request_id,
            approved=request.approved,
            responder=request.responder,
            notes=request.notes
        )

        return ApprovalRequestResponse(
            id=approval.id,
            agent_id=approval.agent_id,
            change_type=approval.change_type,
            change_description=approval.change_description,
            risk_level=approval.risk_level,
            status=approval.status.value,
            requested_at=approval.requested_at.isoformat(),
            responded_at=approval.responded_at.isoformat() if approval.responded_at else None,
            responder=approval.responder
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    limit: int = Query(100, ge=1, le=500, description="Maximum logs to return")
):
    """
    Get audit logs.
    """
    try:
        service = await get_rollback_service()
        logs = await service.get_audit_logs(agent_id, limit)

        return [
            AuditLogResponse(
                id=l.id,
                timestamp=l.timestamp.isoformat(),
                agent_id=l.agent_id,
                action=l.action,
                result=l.result,
                initiated_by=l.initiated_by
            )
            for l in logs
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RATE LIMITING ENDPOINTS
# ============================================================================

@router.get("/rate-limit/{agent_id}")
async def check_rate_limit(agent_id: str):
    """
    Check if an agent has exceeded rate limits.
    """
    try:
        service = await get_rollback_service()
        within_limit = await service.check_rate_limit(agent_id)

        return {
            "agent_id": agent_id,
            "within_limit": within_limit,
            "max_updates_per_hour": service.MAX_UPDATES_PER_HOUR
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
