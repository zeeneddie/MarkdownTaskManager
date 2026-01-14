# Quality API v2
# Independent quality scanning, scheduling, and gate evaluation
#
# 3 Execution Modes:
# - Standalone: Direct scan on project_path
# - Integrated: Automatic during Brown Paper analysis
# - Scheduled: Periodic scans via scheduler
#
# Endpoints:
# - POST /api/v2/quality/scans/run - Run immediate quality scan
# - POST /api/v2/quality/schedules - Create scheduled scan
# - GET /api/v2/quality/schedules - List schedules
# - DELETE /api/v2/quality/schedules/{schedule_id} - Delete schedule
# - GET /api/v2/quality/gates/{project_id} - Evaluate quality gate
# - GET /api/v2/quality/scans/{scan_id} - Get scan result
#
# Architecture: docs/architecture/workflow-separation-plan.md
# Phase: Fase 21.5 (Week 145-146)

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ...database import get_db
from ...contracts import (
    QualityScanResult,
    QualitySchedule,
    QualityGateResult,
    QualityGateStatus,
    ScheduleType,
    QualityRuleViolation,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/quality", tags=["Quality v2"])


# === Request/Response Models ===

class RunScanRequest(BaseModel):
    """Request to run an immediate quality scan."""
    project_path: str = Field(..., description="Path to project to scan")
    project_id: Optional[str] = Field(default=None, description="Project identifier")
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Areas to focus on: security, performance, maintainability, reliability"
    )
    include_stability: bool = Field(default=True, description="Include stability analysis")


class ScanResultResponse(BaseModel):
    """Response from a quality scan."""
    scan_id: str
    project_id: str
    status: str
    overall_score: int
    security_score: int
    performance_score: int
    maintainability_score: int
    reliability_score: int
    blocker_count: int
    critical_count: int
    major_count: int
    minor_count: int
    total_violations: int
    files_scanned: int
    scan_duration_seconds: float
    is_passing: bool
    triggered_by: str
    created_at: datetime


class CreateScheduleRequest(BaseModel):
    """Request to create a quality scan schedule."""
    project_id: str = Field(..., description="Project to schedule scans for")
    schedule_type: str = Field(..., description="daily, weekly, or interval")
    hour: int = Field(default=2, ge=0, le=23, description="Hour of day for daily/weekly")
    day_of_week: str = Field(default="mon", description="Day for weekly schedules")
    interval_hours: int = Field(default=24, ge=1, description="Hours for interval schedules")
    focus_areas: Optional[List[str]] = Field(default=None, description="Areas to focus on")
    enabled: bool = Field(default=True, description="Whether schedule is active")


class ScheduleResponse(BaseModel):
    """Response for a schedule."""
    schedule_id: str
    project_id: str
    schedule_type: str
    enabled: bool
    hour: int
    day_of_week: str
    interval_hours: int
    focus_areas: List[str]
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    created_at: datetime


class QualityGateResponse(BaseModel):
    """Response from quality gate evaluation."""
    project_id: str
    gate_name: str
    status: str
    score: int
    threshold: int
    is_passed: bool
    checks: List[Dict[str, Any]]
    blocking_issues: List[str]
    evaluated_at: datetime


# === Quality Scan Service (Simplified) ===

class QualityScanService:
    """
    Service for running quality scans.

    In production, this would integrate with:
    - SonarQube/CodeClimate for code quality
    - Security scanners (SAST/DAST)
    - Stability analyzers
    """

    async def run_scan(
        self,
        project_path: str,
        project_id: str,
        focus_areas: Optional[List[str]] = None,
        triggered_by: str = "manual",
    ) -> QualityScanResult:
        """Run a quality scan on a project."""
        import time
        start_time = time.time()

        # Simulate scanning (in production, integrate real scanners)
        scan_id = str(uuid.uuid4())

        # Mock results (replace with actual scanning logic)
        result = QualityScanResult(
            scan_id=scan_id,
            project_id=project_id,
            project_path=project_path,
            overall_score=85,
            security_score=90,
            performance_score=80,
            maintainability_score=85,
            reliability_score=88,
            blocker_count=0,
            critical_count=1,
            major_count=5,
            minor_count=12,
            violations=[
                QualityRuleViolation(
                    rule_id="SEC-001",
                    rule_name="SQL Injection Risk",
                    severity="critical",
                    file_path=f"{project_path}/src/db.py",
                    line_number=42,
                    message="Potential SQL injection vulnerability",
                    suggestion="Use parameterized queries",
                    category="security",
                ),
            ],
            files_scanned=150,
            rules_evaluated=42,
            scan_duration_seconds=time.time() - start_time,
            scan_timestamp=datetime.now(timezone.utc),
            triggered_by=triggered_by,
        )

        return result

    def evaluate_gate(
        self,
        scan_result: QualityScanResult,
        threshold: int = 80,
    ) -> QualityGateResult:
        """Evaluate quality gate based on scan result."""
        checks = [
            {
                "name": "Overall Score",
                "status": "passed" if scan_result.overall_score >= threshold else "failed",
                "value": scan_result.overall_score,
                "threshold": threshold,
            },
            {
                "name": "No Blockers",
                "status": "passed" if scan_result.blocker_count == 0 else "failed",
                "value": scan_result.blocker_count,
                "threshold": 0,
            },
            {
                "name": "Critical Issues",
                "status": "passed" if scan_result.critical_count <= 3 else "failed",
                "value": scan_result.critical_count,
                "threshold": 3,
            },
        ]

        blocking_issues = []
        if scan_result.blocker_count > 0:
            blocking_issues.append(f"{scan_result.blocker_count} blocker issues found")
        if scan_result.critical_count > 3:
            blocking_issues.append(f"{scan_result.critical_count} critical issues (max 3)")

        status = QualityGateStatus.PASSED
        if blocking_issues:
            status = QualityGateStatus.FAILED
        elif scan_result.overall_score < threshold:
            status = QualityGateStatus.WARNING

        return QualityGateResult(
            project_id=scan_result.project_id,
            gate_name="default",
            status=status,
            score=scan_result.overall_score,
            threshold=threshold,
            checks=checks,
            blocking_issues=blocking_issues,
            scan_id=scan_result.scan_id,
        )


# === Endpoints ===

@router.post("/scans/run", response_model=ScanResultResponse)
async def run_quality_scan(
    request: RunScanRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Run an immediate quality scan on a project.

    This is Mode 1: Standalone execution.
    No Brown Paper or Migration context required.
    """
    logger.info(f"Running quality scan on: {request.project_path}")

    project_id = request.project_id or request.project_path.split("/")[-1]

    service = QualityScanService()
    result = await service.run_scan(
        project_path=request.project_path,
        project_id=project_id,
        focus_areas=request.focus_areas,
        triggered_by="api",
    )

    # Store result in database
    try:
        await db.execute(text("""
            INSERT INTO quality_scan_results (
                scan_id, project_id, project_path, status, overall_score,
                result_data, triggered_by, scan_duration_seconds, created_at
            ) VALUES (
                :scan_id, :project_id, :project_path, :status, :overall_score,
                :result_data, :triggered_by, :scan_duration_seconds, :created_at
            )
        """), {
            "scan_id": result.scan_id,
            "project_id": result.project_id,
            "project_path": result.project_path,
            "status": "completed",
            "overall_score": result.overall_score,
            "result_data": result.to_dict(),
            "triggered_by": result.triggered_by,
            "scan_duration_seconds": result.scan_duration_seconds,
            "created_at": result.scan_timestamp,
        })
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to store scan result: {e}")

    return ScanResultResponse(
        scan_id=result.scan_id,
        project_id=result.project_id,
        status="completed",
        overall_score=result.overall_score,
        security_score=result.security_score,
        performance_score=result.performance_score,
        maintainability_score=result.maintainability_score,
        reliability_score=result.reliability_score,
        blocker_count=result.blocker_count,
        critical_count=result.critical_count,
        major_count=result.major_count,
        minor_count=result.minor_count,
        total_violations=result.total_violations,
        files_scanned=result.files_scanned,
        scan_duration_seconds=result.scan_duration_seconds,
        is_passing=result.is_passing,
        triggered_by=result.triggered_by,
        created_at=result.scan_timestamp,
    )


@router.get("/scans/{scan_id}", response_model=Dict[str, Any])
async def get_scan_result(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a quality scan result by ID."""
    result = await db.execute(text("""
        SELECT result_data FROM quality_scan_results
        WHERE scan_id = :scan_id
    """), {"scan_id": scan_id})

    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Scan not found: {scan_id}")

    return row[0]


@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    request: CreateScheduleRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a scheduled quality scan.

    This enables Mode 3: Scheduled/Audit execution.
    """
    logger.info(f"Creating schedule for project: {request.project_id}")

    # Validate schedule type
    try:
        schedule_type = ScheduleType(request.schedule_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid schedule_type. Must be one of: daily, weekly, interval"
        )

    schedule_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Calculate next run time
    next_run = _calculate_next_run(
        schedule_type=schedule_type,
        hour=request.hour,
        day_of_week=request.day_of_week,
        interval_hours=request.interval_hours,
    )

    # Store schedule
    await db.execute(text("""
        INSERT INTO quality_schedules (
            schedule_id, project_id, schedule_type, schedule_config,
            focus_areas, enabled, next_run_at, created_at
        ) VALUES (
            :schedule_id, :project_id, :schedule_type, :schedule_config,
            :focus_areas, :enabled, :next_run_at, :created_at
        )
    """), {
        "schedule_id": schedule_id,
        "project_id": request.project_id,
        "schedule_type": request.schedule_type,
        "schedule_config": {
            "hour": request.hour,
            "day_of_week": request.day_of_week,
            "interval_hours": request.interval_hours,
        },
        "focus_areas": request.focus_areas or [],
        "enabled": request.enabled,
        "next_run_at": next_run,
        "created_at": now,
    })
    await db.commit()

    return ScheduleResponse(
        schedule_id=schedule_id,
        project_id=request.project_id,
        schedule_type=request.schedule_type,
        enabled=request.enabled,
        hour=request.hour,
        day_of_week=request.day_of_week,
        interval_hours=request.interval_hours,
        focus_areas=request.focus_areas or [],
        next_run_at=next_run,
        last_run_at=None,
        created_at=now,
    )


@router.get("/schedules", response_model=List[ScheduleResponse])
async def list_schedules(
    project_id: Optional[str] = None,
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List quality scan schedules."""
    query = "SELECT * FROM quality_schedules WHERE 1=1"
    params = {}

    if project_id:
        query += " AND project_id = :project_id"
        params["project_id"] = project_id

    if enabled_only:
        query += " AND enabled = true"

    query += " ORDER BY created_at DESC"

    result = await db.execute(text(query), params)
    rows = result.fetchall()

    schedules = []
    for row in rows:
        config = row.schedule_config or {}
        schedules.append(ScheduleResponse(
            schedule_id=row.schedule_id,
            project_id=row.project_id,
            schedule_type=row.schedule_type,
            enabled=row.enabled,
            hour=config.get("hour", 2),
            day_of_week=config.get("day_of_week", "mon"),
            interval_hours=config.get("interval_hours", 24),
            focus_areas=row.focus_areas or [],
            next_run_at=row.next_run_at,
            last_run_at=row.last_run_at,
            created_at=row.created_at,
        ))

    return schedules


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a quality scan schedule."""
    result = await db.execute(text("""
        DELETE FROM quality_schedules WHERE schedule_id = :schedule_id
    """), {"schedule_id": schedule_id})
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Schedule not found: {schedule_id}")

    return {"message": f"Schedule {schedule_id} deleted"}


@router.get("/gates/{project_id}", response_model=QualityGateResponse)
async def evaluate_quality_gate(
    project_id: str,
    threshold: int = 80,
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluate quality gate for a project.

    Uses the most recent scan result to determine pass/fail status.
    """
    # Get most recent scan for project
    result = await db.execute(text("""
        SELECT result_data FROM quality_scan_results
        WHERE project_id = :project_id
        ORDER BY created_at DESC
        LIMIT 1
    """), {"project_id": project_id})

    row = result.fetchone()
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"No scans found for project: {project_id}"
        )

    scan_data = row[0]
    scan_result = QualityScanResult.from_dict(scan_data)

    service = QualityScanService()
    gate_result = service.evaluate_gate(scan_result, threshold=threshold)

    return QualityGateResponse(
        project_id=gate_result.project_id,
        gate_name=gate_result.gate_name,
        status=gate_result.status.value,
        score=gate_result.score,
        threshold=gate_result.threshold,
        is_passed=gate_result.is_passed,
        checks=gate_result.checks,
        blocking_issues=gate_result.blocking_issues,
        evaluated_at=gate_result.evaluated_at,
    )


# === Helper Functions ===

def _calculate_next_run(
    schedule_type: ScheduleType,
    hour: int,
    day_of_week: str,
    interval_hours: int,
) -> datetime:
    """Calculate next run time for a schedule."""
    from datetime import timedelta

    now = datetime.now(timezone.utc)

    if schedule_type == ScheduleType.DAILY:
        next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        return next_run

    elif schedule_type == ScheduleType.WEEKLY:
        days = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
        target_day = days.get(day_of_week.lower(), 0)
        current_day = now.weekday()

        days_ahead = target_day - current_day
        if days_ahead <= 0:
            days_ahead += 7

        next_run = now + timedelta(days=days_ahead)
        next_run = next_run.replace(hour=hour, minute=0, second=0, microsecond=0)
        return next_run

    elif schedule_type == ScheduleType.INTERVAL:
        return now + timedelta(hours=interval_hours)

    return now + timedelta(days=1)
