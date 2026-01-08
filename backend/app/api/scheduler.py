"""
Scheduler API Endpoints

Manage periodic maintenance scans:
- Schedule daily/weekly/interval scans
- View scheduled jobs
- View execution history
- Remove scheduled jobs
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.scheduler_service import get_scheduler

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ScheduleDailyRequest(BaseModel):
    """Request to schedule daily scan"""
    hour: int = Field(2, ge=0, le=23, description="Hour to run (0-23)")
    minute: int = Field(0, ge=0, le=59, description="Minute to run (0-59)")
    scope: str = Field("full_codebase", description="Scope: full_codebase, module, specific_files")
    focusAreas: Optional[List[str]] = Field(None, description="Areas to focus on")
    urgency: str = Field("medium", description="Urgency: low, medium, high, critical")


class ScheduleWeeklyRequest(BaseModel):
    """Request to schedule weekly scan"""
    dayOfWeek: str = Field("mon", description="Day: mon, tue, wed, thu, fri, sat, sun")
    hour: int = Field(2, ge=0, le=23, description="Hour to run (0-23)")
    minute: int = Field(0, ge=0, le=59, description="Minute to run (0-59)")
    scope: str = Field("full_codebase", description="Scope: full_codebase, module, specific_files")
    focusAreas: Optional[List[str]] = Field(None, description="Areas to focus on")
    urgency: str = Field("medium", description="Urgency: low, medium, high, critical")


class ScheduleIntervalRequest(BaseModel):
    """Request to schedule interval scan with flexible interval types"""
    intervalType: str = Field("hours", description="Interval type: hours, weeks, months")
    intervalValue: int = Field(24, ge=1, description="Interval value")
    scope: str = Field("full_codebase", description="Scope: full_codebase, module, specific_files")
    focusAreas: Optional[List[str]] = Field(None, description="Areas to focus on")
    urgency: str = Field("medium", description="Urgency: low, medium, high, critical")

    def get_hours(self) -> int:
        """Convert interval to hours for scheduler"""
        if self.intervalType == "hours":
            return self.intervalValue
        elif self.intervalType == "weeks":
            return self.intervalValue * 168  # 7 days * 24 hours
        elif self.intervalType == "months":
            return self.intervalValue * 720  # ~30 days * 24 hours
        return self.intervalValue


class ScheduleResponse(BaseModel):
    """Response after scheduling"""
    success: bool
    jobId: str
    message: str


class JobInfo(BaseModel):
    """Job information"""
    id: str
    name: str
    nextRunTime: Optional[str]
    trigger: str


class ExecutionRecord(BaseModel):
    """Execution history record"""
    jobId: Optional[str]
    startTime: str
    endTime: str
    durationSeconds: float
    scope: str
    focusAreas: Optional[List[str]]
    urgency: str
    status: str
    findingsCount: Optional[int] = None
    tasksCount: Optional[int] = None
    error: Optional[str] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/daily", response_model=ScheduleResponse)
async def schedule_daily_scan(request: ScheduleDailyRequest):
    """
    Schedule a daily maintenance scan

    **Example:**
    ```json
    {
      "hour": 2,
      "minute": 0,
      "scope": "full_codebase",
      "focusAreas": ["dependencies", "security"],
      "urgency": "medium"
    }
    ```

    **Returns:**
    - Job ID for the scheduled scan
    """
    try:
        scheduler = get_scheduler()

        job_id = scheduler.schedule_daily_scan(
            hour=request.hour,
            minute=request.minute,
            scope=request.scope,
            focus_areas=request.focusAreas,
            urgency=request.urgency
        )

        return ScheduleResponse(
            success=True,
            jobId=job_id,
            message=f"Daily scan scheduled at {request.hour:02d}:{request.minute:02d} UTC"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weekly", response_model=ScheduleResponse)
async def schedule_weekly_scan(request: ScheduleWeeklyRequest):
    """
    Schedule a weekly maintenance scan

    **Example:**
    ```json
    {
      "dayOfWeek": "mon",
      "hour": 2,
      "minute": 0,
      "scope": "full_codebase",
      "focusAreas": ["dependencies", "security", "code_quality"],
      "urgency": "medium"
    }
    ```

    **Returns:**
    - Job ID for the scheduled scan
    """
    try:
        scheduler = get_scheduler()

        job_id = scheduler.schedule_weekly_scan(
            day_of_week=request.dayOfWeek,
            hour=request.hour,
            minute=request.minute,
            scope=request.scope,
            focus_areas=request.focusAreas,
            urgency=request.urgency
        )

        return ScheduleResponse(
            success=True,
            jobId=job_id,
            message=f"Weekly scan scheduled on {request.dayOfWeek} at {request.hour:02d}:{request.minute:02d} UTC"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interval", response_model=ScheduleResponse)
async def schedule_interval_scan(request: ScheduleIntervalRequest):
    """
    Schedule maintenance scan at flexible interval (hours, weeks, or months)

    **Example:**
    ```json
    {
      "intervalType": "hours",
      "intervalValue": 24,
      "scope": "full_codebase",
      "focusAreas": ["dependencies", "security"],
      "urgency": "medium"
    }
    ```

    **Interval Types:**
    - `hours`: 1-999 hours
    - `weeks`: 1-52 weeks (converted to hours internally)
    - `months`: 1-12 months (converted to hours internally, ~30 days)

    **Returns:**
    - Job ID for the scheduled scan
    """
    try:
        scheduler = get_scheduler()

        # Convert to hours for scheduler
        hours = request.get_hours()

        job_id = scheduler.schedule_interval_scan(
            hours=hours,
            scope=request.scope,
            focus_areas=request.focusAreas,
            urgency=request.urgency
        )

        # Create human-readable message
        interval_desc = f"{request.intervalValue} {request.intervalType}"

        return ScheduleResponse(
            success=True,
            jobId=job_id,
            message=f"Interval scan scheduled every {interval_desc}"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}", response_model=ScheduleResponse)
async def remove_scheduled_job(job_id: str):
    """
    Remove a scheduled job

    **Example:**
    ```
    DELETE /api/scheduler/jobs/daily_scan_full_codebase
    ```

    **Returns:**
    - Success/failure message
    """
    try:
        scheduler = get_scheduler()

        success = scheduler.remove_job(job_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

        return ScheduleResponse(
            success=True,
            jobId=job_id,
            message=f"Job {job_id} removed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[JobInfo])
async def get_scheduled_jobs():
    """
    Get all scheduled jobs

    **Returns:**
    - List of scheduled maintenance scans with next run times
    """
    try:
        scheduler = get_scheduler()
        jobs = scheduler.get_jobs()

        return [
            JobInfo(
                id=job['id'],
                name=job['name'],
                nextRunTime=job['next_run_time'],
                trigger=job['trigger']
            )
            for job in jobs
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[ExecutionRecord])
async def get_execution_history(
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    status: Optional[str] = Query(None, description="Filter by status: completed, failed, timeout")
):
    """
    Get execution history for scheduled scans

    **Query Parameters:**
    - `limit`: Maximum number of records (default: 50, max: 500)
    - `status`: Filter by status ('completed', 'failed', 'timeout')

    **Returns:**
    - List of execution records with results and timing
    """
    try:
        scheduler = get_scheduler()
        history = scheduler.get_execution_history(limit=limit, status=status)

        return [
            ExecutionRecord(
                jobId=record.get('job_id'),
                startTime=record['start_time'],
                endTime=record['end_time'],
                durationSeconds=record['duration_seconds'],
                scope=record['scope'],
                focusAreas=record.get('focus_areas'),
                urgency=record['urgency'],
                status=record['status'],
                findingsCount=record.get('findings_count'),
                tasksCount=record.get('tasks_count'),
                error=record.get('error')
            )
            for record in history
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_scheduler_status():
    """
    Get scheduler status

    **Returns:**
    - Scheduler running status
    - Number of scheduled jobs
    - Number of execution records
    """
    try:
        scheduler = get_scheduler()

        jobs = scheduler.get_jobs()
        history = scheduler.get_execution_history(limit=1000)

        return {
            "running": scheduler.scheduler.running,
            "scheduledJobs": len(jobs),
            "executionRecords": len(history),
            "completedScans": len([h for h in history if h.get('status') == 'completed']),
            "failedScans": len([h for h in history if h.get('status') == 'failed']),
            "timeoutScans": len([h for h in history if h.get('status') == 'timeout'])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EXPORT ENDPOINTS (Week 15)
# ============================================================================

class ExportFormat(BaseModel):
    """Export format options"""
    format: str = Field("json", pattern="^(json|csv)$", description="Export format: json or csv")
    include_details: bool = Field(True, description="Include detailed findings")


@router.get("/export/history")
async def export_history(
    format: str = Query("json", pattern="^(json|csv)$", description="Export format"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(500, ge=1, le=5000, description="Max records")
):
    """
    Export execution history to JSON or CSV

    **Query Parameters:**
    - `format`: 'json' or 'csv' (default: json)
    - `status`: Filter by status (optional)
    - `limit`: Max records to export (default: 500)

    **Returns:**
    - JSON array or CSV file content
    """
    from fastapi.responses import Response
    import csv
    import io

    try:
        scheduler = get_scheduler()
        history = scheduler.get_execution_history(limit=limit, status=status)

        if format == "csv":
            # Generate CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow([
                "Start Time", "End Time", "Duration (s)", "Scope",
                "Focus Areas", "Urgency", "Status", "Findings", "Tasks", "Error"
            ])

            # Data rows
            for record in history:
                writer.writerow([
                    record.get('start_time', ''),
                    record.get('end_time', ''),
                    record.get('duration_seconds', ''),
                    record.get('scope', ''),
                    ','.join(record.get('focus_areas', []) or []),
                    record.get('urgency', ''),
                    record.get('status', ''),
                    record.get('findings_count', ''),
                    record.get('tasks_count', ''),
                    record.get('error', '')
                ])

            csv_content = output.getvalue()
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": "attachment; filename=maintenance_history.csv"
                }
            )

        else:
            # Return JSON
            return {
                "export_date": datetime.now().isoformat(),
                "total_records": len(history),
                "filter_status": status,
                "records": history
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/details")
async def get_job_details(job_id: str):
    """
    Get detailed information about a specific job

    **Returns:**
    - Job configuration
    - Recent execution history
    - Statistics
    """
    try:
        scheduler = get_scheduler()

        # Find the job
        jobs = scheduler.get_jobs()
        job = next((j for j in jobs if j['id'] == job_id), None)

        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

        # Get execution history for this job
        history = scheduler.get_execution_history(limit=100)
        job_history = [h for h in history if h.get('job_id') == job_id]

        # Calculate statistics
        total_runs = len(job_history)
        successful_runs = len([h for h in job_history if h.get('status') == 'completed'])
        failed_runs = len([h for h in job_history if h.get('status') == 'failed'])
        avg_duration = sum(h.get('duration_seconds', 0) for h in job_history) / total_runs if total_runs > 0 else 0

        return {
            "job": job,
            "statistics": {
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0,
                "average_duration_seconds": round(avg_duration, 2)
            },
            "recent_history": job_history[:10]  # Last 10 runs
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/pause")
async def pause_job(job_id: str):
    """
    Pause a scheduled job

    The job will remain in the schedule but won't execute until resumed.
    """
    try:
        scheduler = get_scheduler()

        # APScheduler supports pausing jobs
        job = scheduler.scheduler.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

        scheduler.scheduler.pause_job(job_id)

        return {
            "success": True,
            "jobId": job_id,
            "message": f"Job {job_id} paused successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    """
    Resume a paused job
    """
    try:
        scheduler = get_scheduler()

        job = scheduler.scheduler.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

        scheduler.scheduler.resume_job(job_id)

        return {
            "success": True,
            "jobId": job_id,
            "message": f"Job {job_id} resumed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-now")
async def run_maintenance_now(
    scope: str = Query("full_codebase", description="Scope to scan"),
    focus_areas: str = Query("dependencies,security", description="Comma-separated focus areas"),
    urgency: str = Query("medium", description="Urgency level")
):
    """
    Run a maintenance scan immediately (not scheduled)

    **Query Parameters:**
    - `scope`: Scope to scan (default: full_codebase)
    - `focus_areas`: Comma-separated focus areas
    - `urgency`: Urgency level

    **Returns:**
    - Execution ID for tracking
    """
    try:
        scheduler = get_scheduler()

        # Parse focus areas
        areas = [a.strip() for a in focus_areas.split(',')]

        # Run the scan immediately
        result = scheduler.run_immediate_scan(
            scope=scope,
            focus_areas=areas,
            urgency=urgency
        )

        return {
            "success": True,
            "execution_id": result.get('execution_id'),
            "message": "Maintenance scan started",
            "scope": scope,
            "focus_areas": areas
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# QUALITY SCAN SCHEDULING (Week 56 - Project Config Integration)
# ============================================================================

class ScheduleQualityScanRequest(BaseModel):
    """Request to schedule periodic quality scans for a project"""
    project_id: int = Field(..., description="Project ID to scan")
    interval_hours: int = Field(24, ge=1, le=720, description="Scan interval in hours (1-720)")
    enabled: bool = Field(True, description="Whether scanning is enabled")
    scan_types: List[str] = Field(
        default=["technical_debt", "code_quality", "security"],
        description="Types of scans to perform"
    )


class QualityScanScheduleResponse(BaseModel):
    """Response with quality scan schedule info"""
    project_id: int
    job_id: str
    interval_hours: int
    enabled: bool
    scan_types: List[str]
    next_run_time: Optional[str]
    created_at: str


@router.post("/quality-scan", response_model=QualityScanScheduleResponse)
async def schedule_quality_scan(request: ScheduleQualityScanRequest):
    """
    Schedule periodic quality scans for a project.

    **Example:**
    ```json
    {
      "project_id": 1,
      "interval_hours": 24,
      "enabled": true,
      "scan_types": ["technical_debt", "code_quality", "security"]
    }
    ```

    **Returns:**
    - Job ID and schedule info
    """
    try:
        scheduler = get_scheduler()

        job_id = f"quality_scan_project_{request.project_id}"

        # Remove existing job if any
        try:
            scheduler.remove_job(job_id)
        except:
            pass

        if request.enabled:
            from apscheduler.triggers.interval import IntervalTrigger

            # Schedule the quality scan job
            scheduler.scheduler.add_job(
                func=_run_quality_scan,
                trigger=IntervalTrigger(hours=request.interval_hours),
                id=job_id,
                name=f"Quality Scan - Project {request.project_id}",
                kwargs={
                    "project_id": request.project_id,
                    "scan_types": request.scan_types
                },
                replace_existing=True
            )

        # Get next run time
        job = scheduler.scheduler.get_job(job_id)
        next_run = job.next_run_time.isoformat() if job and job.next_run_time else None

        return QualityScanScheduleResponse(
            project_id=request.project_id,
            job_id=job_id,
            interval_hours=request.interval_hours,
            enabled=request.enabled,
            scan_types=request.scan_types,
            next_run_time=next_run,
            created_at=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality-scan/{project_id}", response_model=QualityScanScheduleResponse)
async def get_quality_scan_schedule(project_id: int):
    """
    Get quality scan schedule for a project.
    """
    try:
        scheduler = get_scheduler()
        job_id = f"quality_scan_project_{project_id}"

        job = scheduler.scheduler.get_job(job_id)

        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"No quality scan schedule found for project {project_id}"
            )

        # Extract interval from trigger
        interval_hours = 24  # Default
        if hasattr(job.trigger, 'interval'):
            interval_hours = int(job.trigger.interval.total_seconds() / 3600)

        return QualityScanScheduleResponse(
            project_id=project_id,
            job_id=job_id,
            interval_hours=interval_hours,
            enabled=True,
            scan_types=job.kwargs.get('scan_types', []),
            next_run_time=job.next_run_time.isoformat() if job.next_run_time else None,
            created_at=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/quality-scan/{project_id}")
async def remove_quality_scan_schedule(project_id: int):
    """
    Remove quality scan schedule for a project.
    """
    try:
        scheduler = get_scheduler()
        job_id = f"quality_scan_project_{project_id}"

        success = scheduler.remove_job(job_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"No quality scan schedule found for project {project_id}"
            )

        return {
            "success": True,
            "message": f"Quality scan schedule removed for project {project_id}",
            "job_id": job_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _run_quality_scan(project_id: int, scan_types: List[str]):
    """
    Internal function to run a quality scan.
    Called by the scheduler.

    Results are stored in:
    - technical_debt_items table
    - technical_debt_snapshots table

    View results at:
    - /quality-dashboard.html
    - GET /api/quality/summary
    - GET /api/quality/items
    - GET /api/quality/snapshots
    """
    import logging
    from app.database import async_get_db
    from app.services.technical_debt_service import get_technical_debt_service

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Running scheduled quality scan for project {project_id}")

        # Get database session
        async for db in async_get_db():
            try:
                service = get_technical_debt_service(db)

                # Map scan types to scanners
                scanners = []
                if "technical_debt" in scan_types:
                    scanners.extend(["ruff", "radon"])  # Code quality
                if "code_quality" in scan_types:
                    scanners.extend(["ruff", "eslint"])
                if "security" in scan_types:
                    scanners.extend(["bandit", "semgrep"])

                # Remove duplicates
                scanners = list(set(scanners))

                # Run the scan
                snapshot = await service.scan_codebase(
                    scanners=scanners if scanners else None,
                    project_id=project_id
                )

                logger.info(
                    f"Quality scan completed for project {project_id}: "
                    f"{snapshot.total_items} items found, "
                    f"debt ratio: {snapshot.debt_ratio:.1f}%"
                )

                # Store execution record
                scheduler = get_scheduler()
                scheduler._record_execution(
                    job_id=f"quality_scan_project_{project_id}",
                    scope="project",
                    focus_areas=scan_types,
                    urgency="scheduled",
                    status="completed",
                    findings_count=snapshot.total_items,
                    tasks_count=0
                )

            except Exception as e:
                logger.error(f"Scan execution failed: {e}")
                raise
            finally:
                await db.close()

    except Exception as e:
        logger.error(f"Quality scan failed for project {project_id}: {e}")
        # Record failure
        try:
            scheduler = get_scheduler()
            scheduler._record_execution(
                job_id=f"quality_scan_project_{project_id}",
                scope="project",
                focus_areas=scan_types,
                urgency="scheduled",
                status="failed",
                error=str(e)
            )
        except:
            pass
        raise
