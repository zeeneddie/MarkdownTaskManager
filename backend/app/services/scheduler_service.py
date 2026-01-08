"""
Scheduler Service for Periodic Maintenance

Manages automatic maintenance scans using APScheduler:
- Daily full codebase scans
- Weekly comprehensive maintenance
- Custom scheduled scans
- Schedule persistence and management
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import logging
import asyncio

from app.services.agent_service import AgentService
from app.schemas.workflow import WorkflowRequest, WorkType

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Manages periodic maintenance execution

    Features:
    - Automatic daily/weekly scans
    - Custom cron schedules
    - Job persistence
    - Execution history tracking
    """

    def __init__(self):
        """Initialize scheduler with memory job store"""
        jobstores = {
            'default': MemoryJobStore()
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            timezone='UTC'
        )

        self.agent_service = AgentService()
        self.execution_history: List[Dict[str, Any]] = []

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Scheduler started")

    def shutdown(self):
        """Shutdown the scheduler gracefully"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Scheduler stopped")

    async def execute_maintenance_scan(
        self,
        scope: str = 'full_codebase',
        focus_areas: Optional[List[str]] = None,
        urgency: str = 'medium',
        job_id: Optional[str] = None
    ):
        """
        Execute a maintenance scan

        Args:
            scope: 'full_codebase', 'module', or 'specific_files'
            focus_areas: List of areas to focus on
            urgency: 'low', 'medium', 'high', or 'critical'
            job_id: Optional job identifier
        """
        logger.info(f"🔧 Starting scheduled maintenance scan (job_id: {job_id})")

        start_time = datetime.utcnow()

        try:
            # Create maintenance request
            request = WorkflowRequest(
                description=f"Scheduled maintenance scan ({scope})",
                context={
                    "scope": scope,
                    "focusAreas": focus_areas or ['dependencies', 'security', 'code_quality'],
                    "urgency": urgency,
                    "thresholds": {
                        "maxComplexity": 15,
                        "minTestCoverage": 80,
                        "maxTechnicalDebtRatio": 10
                    }
                }
            )

            # Execute workflow (async with timeout)
            result = await asyncio.wait_for(
                self.agent_service.execute_workflow(request),
                timeout=1800  # 30 minutes max
            )

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Track execution history
            execution_record = {
                "job_id": job_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "scope": scope,
                "focus_areas": focus_areas,
                "urgency": urgency,
                "status": "completed",
                "findings_count": len(result.get('findings', [])) if isinstance(result, dict) else 0,
                "tasks_count": len(result.get('prioritizedTasks', [])) if isinstance(result, dict) else 0
            }

            self.execution_history.append(execution_record)

            logger.info(f"✅ Scheduled maintenance completed in {duration:.1f}s")
            logger.info(f"   Findings: {execution_record['findings_count']}")
            logger.info(f"   Tasks: {execution_record['tasks_count']}")

        except asyncio.TimeoutError:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            execution_record = {
                "job_id": job_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "scope": scope,
                "focus_areas": focus_areas,
                "urgency": urgency,
                "status": "timeout",
                "error": "Execution timeout (30 minutes)"
            }

            self.execution_history.append(execution_record)
            logger.error(f"⏱️ Scheduled maintenance timed out after {duration:.1f}s")

        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            execution_record = {
                "job_id": job_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "scope": scope,
                "focus_areas": focus_areas,
                "urgency": urgency,
                "status": "failed",
                "error": str(e)
            }

            self.execution_history.append(execution_record)
            logger.error(f"❌ Scheduled maintenance failed: {e}")

    def schedule_daily_scan(
        self,
        hour: int = 2,
        minute: int = 0,
        scope: str = 'full_codebase',
        focus_areas: Optional[List[str]] = None,
        urgency: str = 'medium'
    ) -> str:
        """
        Schedule daily maintenance scan

        Args:
            hour: Hour to run (0-23, default 2 AM)
            minute: Minute to run (0-59, default 0)
            scope: Scope of scan
            focus_areas: Areas to focus on
            urgency: Urgency level

        Returns:
            Job ID
        """
        job_id = f"daily_scan_{scope}"

        job = self.scheduler.add_job(
            self.execute_maintenance_scan,
            trigger=CronTrigger(hour=hour, minute=minute),
            args=[scope, focus_areas, urgency, job_id],
            id=job_id,
            replace_existing=True,
            name=f"Daily {scope} scan"
        )

        logger.info(f"📅 Scheduled daily scan: {job_id} at {hour:02d}:{minute:02d} UTC")

        return job_id

    def schedule_weekly_scan(
        self,
        day_of_week: str = 'mon',
        hour: int = 2,
        minute: int = 0,
        scope: str = 'full_codebase',
        focus_areas: Optional[List[str]] = None,
        urgency: str = 'medium'
    ) -> str:
        """
        Schedule weekly maintenance scan

        Args:
            day_of_week: 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'
            hour: Hour to run (0-23, default 2 AM)
            minute: Minute to run (0-59, default 0)
            scope: Scope of scan
            focus_areas: Areas to focus on
            urgency: Urgency level

        Returns:
            Job ID
        """
        job_id = f"weekly_scan_{scope}"

        job = self.scheduler.add_job(
            self.execute_maintenance_scan,
            trigger=CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
            args=[scope, focus_areas, urgency, job_id],
            id=job_id,
            replace_existing=True,
            name=f"Weekly {scope} scan"
        )

        logger.info(f"📅 Scheduled weekly scan: {job_id} on {day_of_week} at {hour:02d}:{minute:02d} UTC")

        return job_id

    def schedule_interval_scan(
        self,
        hours: int = 24,
        scope: str = 'full_codebase',
        focus_areas: Optional[List[str]] = None,
        urgency: str = 'medium'
    ) -> str:
        """
        Schedule maintenance scan at fixed interval

        Args:
            hours: Interval in hours
            scope: Scope of scan
            focus_areas: Areas to focus on
            urgency: Urgency level

        Returns:
            Job ID
        """
        job_id = f"interval_scan_{scope}_{hours}h"

        job = self.scheduler.add_job(
            self.execute_maintenance_scan,
            trigger=IntervalTrigger(hours=hours),
            args=[scope, focus_areas, urgency, job_id],
            id=job_id,
            replace_existing=True,
            name=f"Every {hours}h {scope} scan"
        )

        logger.info(f"📅 Scheduled interval scan: {job_id} every {hours} hours")

        return job_id

    def remove_job(self, job_id: str) -> bool:
        """
        Remove a scheduled job

        Args:
            job_id: Job identifier

        Returns:
            True if removed, False if not found
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"🗑️ Removed scheduled job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to remove job {job_id}: {e}")
            return False

    def get_jobs(self) -> List[Dict[str, Any]]:
        """
        Get all scheduled jobs

        Returns:
            List of job details
        """
        jobs = []

        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })

        return jobs

    def get_execution_history(
        self,
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get execution history

        Args:
            limit: Max number of records to return
            status: Filter by status ('completed', 'failed', 'timeout')

        Returns:
            List of execution records
        """
        history = self.execution_history

        if status:
            history = [h for h in history if h.get('status') == status]

        # Return most recent first
        return sorted(history, key=lambda x: x['start_time'], reverse=True)[:limit]


# Global scheduler instance
scheduler_service = SchedulerService()


def get_scheduler() -> SchedulerService:
    """Get the global scheduler instance"""
    return scheduler_service
