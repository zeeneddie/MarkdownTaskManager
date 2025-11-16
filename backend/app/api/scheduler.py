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
    """Request to schedule interval scan"""
    hours: int = Field(24, ge=1, le=168, description="Interval in hours (1-168)")
    scope: str = Field("full_codebase", description="Scope: full_codebase, module, specific_files")
    focusAreas: Optional[List[str]] = Field(None, description="Areas to focus on")
    urgency: str = Field("medium", description="Urgency: low, medium, high, critical")


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
    Schedule maintenance scan at fixed interval

    **Example:**
    ```json
    {
      "hours": 24,
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

        job_id = scheduler.schedule_interval_scan(
            hours=request.hours,
            scope=request.scope,
            focus_areas=request.focusAreas,
            urgency=request.urgency
        )

        return ScheduleResponse(
            success=True,
            jobId=job_id,
            message=f"Interval scan scheduled every {request.hours} hours"
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
