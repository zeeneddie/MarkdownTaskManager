"""
Quality Metrics Dashboard API

REST API endpoints for:
- Technical debt scanning and monitoring
- Quality gate checks
- Remediation plan management
- Debt trend analytics

Author: Claude Code (Week 18 Day 3)
Date: 2025-11-22
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from app.database import get_db
from app.services.technical_debt_service import (
    get_technical_debt_service, TechnicalDebtService
)
from app.models.technical_debt import (
    TechnicalDebtItem, TechnicalDebtSnapshot, RemediationPlan,
    DebtResolution, QualityGateResult,
    DebtType, DebtSeverity, DebtStatus
)


router = APIRouter(prefix="/api/quality", tags=["Quality Dashboard"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ScanRequest(BaseModel):
    """Request to scan codebase for technical debt"""
    scanners: Optional[List[str]] = Field(
        default=["ruff", "bandit", "coverage"],
        description="Scanners to run"
    )
    project_id: Optional[int] = None
    background: bool = Field(
        default=False,
        description="Run scan in background"
    )


class ScanResponse(BaseModel):
    """Scan result summary"""
    snapshot_id: int
    timestamp: str
    total_items: int
    total_principal: float
    debt_ratio: float
    critical_count: int
    high_count: int
    security_issues: int
    items_delta: int
    scan_duration: float


class DebtItemResponse(BaseModel):
    """Technical debt item"""
    id: int
    title: str
    description: Optional[str]
    debt_type: str
    severity: str
    status: str
    file_path: Optional[str]
    line_start: Optional[int]
    principal: float
    interest_rate: float
    roi: float
    detected_by: str
    detection_rule: Optional[str]
    first_detected: Optional[str]


class PrioritizedItemResponse(BaseModel):
    """Prioritized debt item for remediation"""
    id: int
    title: str
    debt_type: str
    severity: str
    file_path: Optional[str]
    principal: float
    priority_score: float
    roi: float
    urgency: float
    impact: float


class RemediationPlanRequest(BaseModel):
    """Request to create remediation plan"""
    name: str
    target_debt_ratio: Optional[float] = Field(
        default=None,
        description="Target TDR to achieve (%)"
    )
    max_effort_hours: Optional[float] = Field(
        default=None,
        description="Maximum hours to allocate"
    )
    focus_types: Optional[List[str]] = Field(
        default=None,
        description="Debt types to focus on"
    )
    project_id: Optional[int] = None


class RemediationPlanResponse(BaseModel):
    """Remediation plan details"""
    id: int
    name: str
    description: Optional[str]
    status: str
    target_debt_ratio: Optional[float]
    total_items: int
    total_effort_hours: float
    estimated_interest_saved: float
    items_completed: int
    progress: float
    roi: float
    assigned_agent: str
    created_at: str


class ResolveDebtRequest(BaseModel):
    """Request to resolve a debt item"""
    resolution_type: str = Field(
        description="Type: fix, refactor, remove, accept"
    )
    resolved_by_agent: Optional[str] = None
    resolved_by_human: Optional[str] = None
    actual_hours: Optional[float] = None
    commit_hash: Optional[str] = None
    pr_number: Optional[int] = None
    notes: Optional[str] = None


class QualityGateRequest(BaseModel):
    """Request for quality gate check"""
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    pr_number: Optional[int] = None
    project_id: Optional[int] = None


class QualityGateResponse(BaseModel):
    """Quality gate check result"""
    id: int
    timestamp: str
    passed: bool
    blocked: bool
    gate_results: Dict[str, Any]
    failure_reasons: List[str]
    blocking_issues: List[str]
    coverage_score: Optional[float]
    security_score: Optional[float]
    debt_ratio_score: Optional[float]


class DebtSummaryResponse(BaseModel):
    """Current debt summary"""
    total_items: int
    total_principal: float
    total_interest: float
    debt_ratio: float
    critical_count: int
    high_count: int
    security_issues: int
    items_delta: int
    ratio_delta: float
    resolved_last_30_days: int
    last_scan: Optional[str]
    status: str


class TrendDataPoint(BaseModel):
    """Single trend data point"""
    timestamp: str
    total_items: int
    total_principal: float
    debt_ratio: float
    critical_count: int
    security_issues: int


class SnapshotSummary(BaseModel):
    """Snapshot summary for listing"""
    id: int
    timestamp: Optional[str]
    total_items: int
    total_principal: float
    debt_ratio: float
    critical_count: int
    high_count: int
    security_issues: int
    items_delta: int


class SnapshotDetailResponse(BaseModel):
    """Detailed snapshot with items"""
    id: int
    timestamp: Optional[str]
    total_items: int
    total_principal: float
    debt_ratio: float
    critical_count: int
    high_count: int
    security_issues: int
    items_delta: int
    items: List[Dict[str, Any]]


class DebtItemDetailResponse(BaseModel):
    """Detailed debt item response"""
    id: int
    title: str
    description: Optional[str]
    debt_type: Optional[str]
    severity: Optional[str]
    status: Optional[str]
    file_path: Optional[str]
    line_start: Optional[int]
    principal: float
    interest_rate: float
    first_detected: Optional[str]


class ResolutionResponse(BaseModel):
    """Resolution response"""
    id: int
    item_id: int
    resolution_type: str
    resolved_at: Optional[str]
    actual_hours: Optional[float]
    commit_hash: Optional[str]


class PlanDetailResponse(BaseModel):
    """Detailed plan with items"""
    id: int
    name: str
    description: Optional[str]
    status: str
    target_debt_ratio: Optional[float]
    total_items: int
    total_effort_hours: float
    estimated_interest_saved: float
    items_completed: int
    assigned_agent: Optional[str]
    created_at: Optional[str]
    items: List[Dict[str, Any]]


class GateHistoryResponse(BaseModel):
    """Gate history item"""
    id: int
    timestamp: Optional[str]
    passed: bool
    blocked: bool
    commit_hash: Optional[str]
    branch: Optional[str]


class TypeStatsResponse(BaseModel):
    """Stats grouped by debt type"""
    stats: Dict[str, Any]


class FileStatsItem(BaseModel):
    """Single file stats"""
    file_path: str
    count: int
    total_principal: float
    security_issues: int


class QualityHealthResponse(BaseModel):
    """Overall quality health"""
    score: int
    status: str
    factors: Dict[str, Any]
    recommendations: List[str]


# ============================================================================
# Scanning Endpoints
# ============================================================================

@router.post("/scan", response_model=ScanResponse)
async def scan_codebase(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Scan the codebase for technical debt.

    Runs configured scanners (ruff, bandit, eslint, coverage)
    and creates a new debt snapshot.
    """
    service = get_technical_debt_service(db)

    if request.background:
        # Run in background
        background_tasks.add_task(
            _run_scan_background,
            db,
            request.scanners,
            request.project_id
        )
        return ScanResponse(
            snapshot_id=0,
            timestamp=datetime.utcnow().isoformat(),
            total_items=0,
            total_principal=0,
            debt_ratio=0,
            critical_count=0,
            high_count=0,
            security_issues=0,
            items_delta=0,
            scan_duration=0
        )

    snapshot = await service.scan_codebase(
        scanners=request.scanners,
        project_id=request.project_id
    )

    return ScanResponse(
        snapshot_id=snapshot.id,
        timestamp=snapshot.timestamp.isoformat() if snapshot.timestamp else "",
        total_items=snapshot.total_items,
        total_principal=snapshot.total_principal,
        debt_ratio=snapshot.debt_ratio,
        critical_count=snapshot.critical_count,
        high_count=snapshot.high_count,
        security_issues=snapshot.security_issues,
        items_delta=snapshot.items_delta,
        scan_duration=snapshot.scan_duration_seconds or 0
    )


async def _run_scan_background(
    db: AsyncSession,
    scanners: List[str],
    project_id: Optional[int]
):
    """Background scan task"""
    service = get_technical_debt_service(db)
    await service.scan_codebase(scanners=scanners, project_id=project_id)


@router.get("/snapshots", response_model=List[SnapshotSummary])
async def list_snapshots(
    project_id: Optional[int] = None,
    limit: int = Query(default=10, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List recent debt snapshots"""
    query = select(TechnicalDebtSnapshot).order_by(
        TechnicalDebtSnapshot.timestamp.desc()
    )

    if project_id:
        query = query.where(TechnicalDebtSnapshot.project_id == project_id)

    result = await db.execute(query.limit(limit))
    snapshots = result.scalars().all()

    return [
        SnapshotSummary(
            id=s.id,
            timestamp=s.timestamp.isoformat() if s.timestamp else None,
            total_items=s.total_items or 0,
            total_principal=s.total_principal or 0.0,
            debt_ratio=s.debt_ratio or 0.0,
            critical_count=s.critical_count or 0,
            high_count=s.high_count or 0,
            security_issues=s.security_issues or 0,
            items_delta=s.items_delta or 0
        )
        for s in snapshots
    ]


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotDetailResponse)
async def get_snapshot(
    snapshot_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific snapshot with its items"""
    result = await db.execute(
        select(TechnicalDebtSnapshot).where(TechnicalDebtSnapshot.id == snapshot_id)
    )
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    # Get items for this snapshot
    items_result = await db.execute(
        select(TechnicalDebtItem).where(TechnicalDebtItem.snapshot_id == snapshot_id)
    )
    items = items_result.scalars().all()

    return SnapshotDetailResponse(
        id=snapshot.id,
        timestamp=snapshot.timestamp.isoformat() if snapshot.timestamp else None,
        total_items=snapshot.total_items or 0,
        total_principal=snapshot.total_principal or 0.0,
        debt_ratio=snapshot.debt_ratio or 0.0,
        critical_count=snapshot.critical_count or 0,
        high_count=snapshot.high_count or 0,
        security_issues=snapshot.security_issues or 0,
        items_delta=snapshot.items_delta or 0,
        items=[item.to_dict() for item in items]
    )


# ============================================================================
# Debt Items Endpoints
# ============================================================================

@router.get("/items", response_model=List[DebtItemResponse])
async def list_debt_items(
    status: Optional[str] = None,
    debt_type: Optional[str] = None,
    severity: Optional[str] = None,
    project_id: Optional[int] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List technical debt items with filtering"""
    query = select(TechnicalDebtItem)

    if status:
        query = query.where(TechnicalDebtItem.status == DebtStatus(status))
    if debt_type:
        query = query.where(TechnicalDebtItem.debt_type == DebtType(debt_type))
    if severity:
        query = query.where(TechnicalDebtItem.severity == DebtSeverity(severity))
    if project_id:
        query = query.where(TechnicalDebtItem.project_id == project_id)

    query = query.order_by(TechnicalDebtItem.first_detected.desc())
    result = await db.execute(query.offset(offset).limit(limit))
    items = result.scalars().all()

    return [
        DebtItemResponse(
            id=item.id,
            title=item.title,
            description=item.description,
            debt_type=item.debt_type.value if item.debt_type else None,
            severity=item.severity.value if item.severity else None,
            status=item.status.value if item.status else None,
            file_path=item.file_path,
            line_start=item.line_start,
            principal=item.principal,
            interest_rate=item.interest_rate,
            roi=item.calculate_roi(),
            detected_by=item.detected_by.value if item.detected_by else None,
            detection_rule=item.detection_rule,
            first_detected=item.first_detected.isoformat() if item.first_detected else None
        )
        for item in items
    ]


@router.get("/items/{item_id}", response_model=DebtItemDetailResponse)
async def get_debt_item(
    item_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific debt item"""
    result = await db.execute(
        select(TechnicalDebtItem).where(TechnicalDebtItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Debt item not found")

    return DebtItemDetailResponse(
        id=item.id,
        title=item.title,
        description=item.description,
        debt_type=item.debt_type.value if item.debt_type else None,
        severity=item.severity.value if item.severity else None,
        status=item.status.value if item.status else None,
        file_path=item.file_path,
        line_start=item.line_start,
        principal=item.principal or 0.0,
        interest_rate=item.interest_rate or 0.0,
        first_detected=item.first_detected.isoformat() if item.first_detected else None
    )


@router.patch("/items/{item_id}/status", response_model=DebtItemDetailResponse)
async def update_item_status(
    item_id: int,
    status: str,
    db: AsyncSession = Depends(get_db)
):
    """Update debt item status"""
    result = await db.execute(
        select(TechnicalDebtItem).where(TechnicalDebtItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Debt item not found")

    item.status = DebtStatus(status)
    await db.commit()
    await db.refresh(item)

    return DebtItemDetailResponse(
        id=item.id,
        title=item.title,
        description=item.description,
        debt_type=item.debt_type.value if item.debt_type else None,
        severity=item.severity.value if item.severity else None,
        status=item.status.value if item.status else None,
        file_path=item.file_path,
        line_start=item.line_start,
        principal=item.principal or 0.0,
        interest_rate=item.interest_rate or 0.0,
        first_detected=item.first_detected.isoformat() if item.first_detected else None
    )


@router.post("/items/{item_id}/resolve", response_model=ResolutionResponse)
async def resolve_debt_item(
    item_id: int,
    request: ResolveDebtRequest,
    db: AsyncSession = Depends(get_db)
):
    """Mark a debt item as resolved"""
    service = get_technical_debt_service(db)

    try:
        resolution = await service.resolve_debt_item(
            item_id=item_id,
            resolution_type=request.resolution_type,
            resolved_by_agent=request.resolved_by_agent,
            resolved_by_human=request.resolved_by_human,
            actual_hours=request.actual_hours,
            commit_hash=request.commit_hash,
            pr_number=request.pr_number,
            notes=request.notes
        )
        return ResolutionResponse(
            id=resolution.id,
            item_id=resolution.item_id,
            resolution_type=resolution.resolution_type,
            resolved_at=resolution.resolved_at.isoformat() if resolution.resolved_at else None,
            actual_hours=resolution.actual_hours,
            commit_hash=resolution.commit_hash
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Prioritization Endpoints
# ============================================================================

@router.get("/prioritized", response_model=List[PrioritizedItemResponse])
async def get_prioritized_items(
    max_hours: Optional[float] = None,
    focus_types: Optional[str] = None,
    project_id: Optional[int] = None,
    limit: int = Query(default=20, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Get prioritized debt items for remediation.

    Items are scored based on:
    - ROI (interest saved per hour invested)
    - Urgency (severity-based)
    - Impact (type-based importance)
    """
    service = get_technical_debt_service(db)

    # Parse focus types
    types = None
    if focus_types:
        types = [DebtType(t.strip()) for t in focus_types.split(",")]

    prioritized = await service.prioritize_debt(
        project_id=project_id,
        max_hours=max_hours,
        focus_types=types,
        limit=limit
    )

    return [
        PrioritizedItemResponse(
            id=p.item.id,
            title=p.item.title,
            debt_type=p.item.debt_type.value if p.item.debt_type else None,
            severity=p.item.severity.value if p.item.severity else None,
            file_path=p.item.file_path,
            principal=p.item.principal,
            priority_score=round(p.priority_score, 3),
            roi=round(p.roi, 3),
            urgency=round(p.urgency, 3),
            impact=round(p.impact, 3)
        )
        for p in prioritized
    ]


# ============================================================================
# Remediation Plan Endpoints
# ============================================================================

@router.post("/plans", response_model=RemediationPlanResponse)
async def create_remediation_plan(
    request: RemediationPlanRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new remediation plan.

    Automatically prioritizes and selects debt items
    based on ROI and constraints.
    """
    service = get_technical_debt_service(db)

    # Parse focus types
    focus_types = None
    if request.focus_types:
        focus_types = [DebtType(t) for t in request.focus_types]

    try:
        plan = await service.create_remediation_plan(
            name=request.name,
            target_debt_ratio=request.target_debt_ratio,
            max_effort_hours=request.max_effort_hours,
            focus_types=focus_types,
            project_id=request.project_id
        )

        return RemediationPlanResponse(
            id=plan.id,
            name=plan.name,
            description=plan.description,
            status=plan.status,
            target_debt_ratio=plan.target_debt_ratio,
            total_items=plan.total_items,
            total_effort_hours=plan.total_effort_hours,
            estimated_interest_saved=plan.estimated_interest_saved,
            items_completed=plan.items_completed,
            progress=plan.calculate_progress(),
            roi=plan.calculate_roi(),
            assigned_agent=plan.assigned_agent,
            created_at=plan.created_at.isoformat() if plan.created_at else ""
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plans", response_model=List[RemediationPlanResponse])
async def list_remediation_plans(
    status: Optional[str] = None,
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """List remediation plans"""
    query = select(RemediationPlan).order_by(RemediationPlan.created_at.desc())

    if status:
        query = query.where(RemediationPlan.status == status)
    if project_id:
        query = query.where(RemediationPlan.project_id == project_id)

    result = await db.execute(query)
    plans = result.scalars().all()

    return [
        RemediationPlanResponse(
            id=plan.id,
            name=plan.name,
            description=plan.description,
            status=plan.status,
            target_debt_ratio=plan.target_debt_ratio,
            total_items=plan.total_items,
            total_effort_hours=plan.total_effort_hours,
            estimated_interest_saved=plan.estimated_interest_saved,
            items_completed=plan.items_completed,
            progress=plan.calculate_progress(),
            roi=plan.calculate_roi(),
            assigned_agent=plan.assigned_agent,
            created_at=plan.created_at.isoformat() if plan.created_at else ""
        )
        for plan in plans
    ]


@router.get("/plans/{plan_id}", response_model=PlanDetailResponse)
async def get_remediation_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific remediation plan with its items"""
    result = await db.execute(
        select(RemediationPlan).where(RemediationPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Get the items in this plan
    if plan.item_ids:
        items_result = await db.execute(
            select(TechnicalDebtItem).where(
                TechnicalDebtItem.id.in_(plan.item_ids)
            )
        )
        items = items_result.scalars().all()
    else:
        items = []

    return PlanDetailResponse(
        id=plan.id,
        name=plan.name,
        description=plan.description,
        status=plan.status,
        target_debt_ratio=plan.target_debt_ratio,
        total_items=plan.total_items or 0,
        total_effort_hours=plan.total_effort_hours or 0.0,
        estimated_interest_saved=plan.estimated_interest_saved or 0.0,
        items_completed=plan.items_completed or 0,
        assigned_agent=plan.assigned_agent,
        created_at=plan.created_at.isoformat() if plan.created_at else None,
        items=[item.to_dict() for item in items]
    )


@router.patch("/plans/{plan_id}/status", response_model=RemediationPlanResponse)
async def update_plan_status(
    plan_id: int,
    status: str,
    db: AsyncSession = Depends(get_db)
):
    """Update remediation plan status"""
    result = await db.execute(
        select(RemediationPlan).where(RemediationPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan.status = status
    if status == "active" and not plan.start_date:
        plan.start_date = datetime.utcnow()
    elif status == "completed":
        plan.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(plan)

    return RemediationPlanResponse(
        id=plan.id,
        name=plan.name,
        description=plan.description,
        status=plan.status,
        target_debt_ratio=plan.target_debt_ratio,
        total_items=plan.total_items or 0,
        total_effort_hours=plan.total_effort_hours or 0.0,
        estimated_interest_saved=plan.estimated_interest_saved or 0.0,
        items_completed=plan.items_completed or 0,
        progress=plan.calculate_progress(),
        roi=plan.calculate_roi(),
        assigned_agent=plan.assigned_agent,
        created_at=plan.created_at.isoformat() if plan.created_at else ""
    )


# ============================================================================
# Quality Gate Endpoints
# ============================================================================

@router.post("/gates/check", response_model=QualityGateResponse)
async def check_quality_gates(
    request: QualityGateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run quality gate checks.

    Checks:
    - Tests pass (100%)
    - Coverage >= 80%
    - No critical security issues
    - Debt ratio < 10%
    """
    service = get_technical_debt_service(db)

    result = await service.check_quality_gates(
        commit_hash=request.commit_hash,
        branch=request.branch,
        pr_number=request.pr_number,
        project_id=request.project_id
    )

    return QualityGateResponse(
        id=result.id,
        timestamp=result.timestamp.isoformat() if result.timestamp else "",
        passed=result.passed,
        blocked=result.blocked,
        gate_results=result.gate_results or {},
        failure_reasons=result.failure_reasons or [],
        blocking_issues=result.blocking_issues or [],
        coverage_score=result.coverage_score,
        security_score=result.security_score,
        debt_ratio_score=result.debt_ratio_score
    )


@router.get("/gates/history", response_model=List[GateHistoryResponse])
async def get_gate_history(
    project_id: Optional[int] = None,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get quality gate check history"""
    query = select(QualityGateResult).order_by(
        QualityGateResult.timestamp.desc()
    )

    if project_id:
        query = query.where(QualityGateResult.project_id == project_id)

    result = await db.execute(query.limit(limit))
    results = result.scalars().all()

    return [
        GateHistoryResponse(
            id=r.id,
            timestamp=r.timestamp.isoformat() if r.timestamp else None,
            passed=r.passed,
            blocked=r.blocked,
            commit_hash=r.commit_hash,
            branch=r.branch
        )
        for r in results
    ]


# ============================================================================
# Analytics Endpoints
# ============================================================================

@router.get("/summary", response_model=DebtSummaryResponse)
async def get_debt_summary(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get current debt summary"""
    service = get_technical_debt_service(db)
    summary = await service.get_debt_summary(project_id)

    return DebtSummaryResponse(**summary)


@router.get("/trends", response_model=List[TrendDataPoint])
async def get_debt_trends(
    days: int = Query(default=30, le=90),
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get debt metrics trend over time"""
    service = get_technical_debt_service(db)
    trend_data = await service.get_debt_trend(days=days, project_id=project_id)

    return [TrendDataPoint(**point) for point in trend_data]


@router.get("/stats/by-type", response_model=TypeStatsResponse)
async def get_stats_by_type(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get debt statistics grouped by type"""
    # Use cast to text for PostgreSQL enum compatibility
    from sqlalchemy import cast, String
    active_statuses = ["open", "acknowledged", "planned"]
    query = select(TechnicalDebtItem).where(
        cast(TechnicalDebtItem.status, String).in_(active_statuses)
    )

    if project_id:
        query = query.where(TechnicalDebtItem.project_id == project_id)

    result = await db.execute(query)
    items = result.scalars().all()

    # Group by type
    stats = {}
    for item in items:
        type_key = item.debt_type.value if item.debt_type else "unknown"
        if type_key not in stats:
            stats[type_key] = {
                "count": 0,
                "total_principal": 0,
                "total_interest": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }

        stats[type_key]["count"] += 1
        stats[type_key]["total_principal"] += item.principal
        stats[type_key]["total_interest"] += item.calculate_interest()

        if item.severity == DebtSeverity.CRITICAL:
            stats[type_key]["critical"] += 1
        elif item.severity == DebtSeverity.HIGH:
            stats[type_key]["high"] += 1
        elif item.severity == DebtSeverity.MEDIUM:
            stats[type_key]["medium"] += 1
        else:
            stats[type_key]["low"] += 1

    return TypeStatsResponse(stats=stats)


@router.get("/stats/by-file", response_model=List[FileStatsItem])
async def get_stats_by_file(
    project_id: Optional[int] = None,
    limit: int = Query(default=20, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get debt statistics grouped by file (top offenders)"""
    # Use cast to text for PostgreSQL enum compatibility
    from sqlalchemy import cast, String
    active_statuses = ["open", "acknowledged", "planned"]
    query = select(TechnicalDebtItem).where(
        cast(TechnicalDebtItem.status, String).in_(active_statuses)
    )

    if project_id:
        query = query.where(TechnicalDebtItem.project_id == project_id)

    result = await db.execute(query)
    items = result.scalars().all()

    # Group by file
    file_stats = {}
    for item in items:
        file_path = item.file_path or "unknown"
        if file_path not in file_stats:
            file_stats[file_path] = {
                "file_path": file_path,
                "count": 0,
                "total_principal": 0,
                "security_issues": 0
            }

        file_stats[file_path]["count"] += 1
        file_stats[file_path]["total_principal"] += item.principal

        if item.debt_type == DebtType.SECURITY:
            file_stats[file_path]["security_issues"] += 1

    # Sort by count and return top offenders
    sorted_files = sorted(
        file_stats.values(),
        key=lambda x: x["count"],
        reverse=True
    )

    return [
        FileStatsItem(
            file_path=f["file_path"],
            count=f["count"],
            total_principal=f["total_principal"],
            security_issues=f["security_issues"]
        )
        for f in sorted_files[:limit]
    ]


@router.get("/health", response_model=QualityHealthResponse)
async def get_quality_health(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall quality health score.

    Returns a health score (0-100) and status.
    """
    service = get_technical_debt_service(db)
    summary = await service.get_debt_summary(project_id)

    # Extract values with defaults (handles missing snapshot case)
    debt_ratio = summary.get("debt_ratio", 0)
    critical_count = summary.get("critical_count", 0)
    security_issues = summary.get("security_issues", 0)
    high_count = summary.get("high_count", 0)

    # Calculate health score
    score = 100

    # Deduct for high debt ratio
    if debt_ratio > 10:
        score -= min(30, (debt_ratio - 10) * 2)

    # Deduct for critical issues
    score -= critical_count * 10

    # Deduct for security issues
    score -= security_issues * 5

    # Deduct for high count issues
    score -= high_count * 2

    # Ensure score is within bounds
    score = max(0, min(100, score))

    # Determine status
    if score >= 80:
        status = "healthy"
    elif score >= 60:
        status = "warning"
    elif score >= 40:
        status = "degraded"
    else:
        status = "critical"

    return QualityHealthResponse(
        score=round(score),
        status=status,
        factors={
            "debt_ratio": debt_ratio,
            "critical_issues": critical_count,
            "security_issues": security_issues,
            "high_issues": high_count
        },
        recommendations=_get_recommendations(summary)
    )


def _get_recommendations(summary: dict) -> List[str]:
    """Generate recommendations based on summary"""
    recommendations = []

    critical_count = summary.get("critical_count", 0)
    security_issues = summary.get("security_issues", 0)
    debt_ratio = summary.get("debt_ratio", 0)
    items_delta = summary.get("items_delta", 0)

    if critical_count > 0:
        recommendations.append(
            f"Address {critical_count} critical issues immediately"
        )

    if security_issues > 0:
        recommendations.append(
            f"Review {security_issues} security vulnerabilities"
        )

    if debt_ratio > 15:
        recommendations.append(
            f"Debt ratio is {debt_ratio:.1f}% - create a remediation plan"
        )

    if items_delta > 10:
        recommendations.append(
            f"New debt increased by {items_delta} items - review recent changes"
        )

    if not recommendations:
        recommendations.append("Quality metrics are healthy - maintain current practices")

    return recommendations
