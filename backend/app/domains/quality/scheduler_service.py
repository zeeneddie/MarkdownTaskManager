# Quality Scheduler Service
# Independent scheduling for quality scans
#
# Features:
# - Daily/Weekly/Interval scheduling
# - APScheduler integration
# - Database persistence for schedules
# - Execution history tracking
#
# Architecture: docs/architecture/workflow-separation-plan.md
# Phase: Fase 21.5 Phase 4 (Week 145-146)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Callable
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ...contracts import ScheduleType, QualityScanResult

logger = logging.getLogger(__name__)


class QualitySchedulerService:
    """
    Independent scheduler for quality scans.

    Supports 3 schedule types:
    - DAILY: Run at specific hour each day
    - WEEKLY: Run on specific day/hour each week
    - INTERVAL: Run every N hours

    Usage:
        scheduler = QualitySchedulerService()
        scheduler.start()

        # Schedule daily scan at 2 AM
        schedule_id = await scheduler.schedule_daily_scan(
            project_id="my-project",
            project_path="/path/to/project",
            hour=2
        )

        # Schedule weekly scan on Monday at 3 AM
        schedule_id = await scheduler.schedule_weekly_scan(
            project_id="my-project",
            project_path="/path/to/project",
            day_of_week="mon",
            hour=3
        )
    """

    def __init__(self, db_session_factory: Optional[Callable] = None):
        """
        Initialize the quality scheduler.

        Args:
            db_session_factory: Optional factory to create database sessions
        """
        jobstores = {
            'default': MemoryJobStore()
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            timezone='UTC'
        )

        self.db_session_factory = db_session_factory
        self._scan_callback: Optional[Callable] = None
        self._schedules: Dict[str, Dict[str, Any]] = {}

    def set_scan_callback(self, callback: Callable):
        """Set the callback function to execute scans."""
        self._scan_callback = callback

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Quality Scheduler started")

    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Quality Scheduler stopped")

    async def schedule_daily_scan(
        self,
        project_id: str,
        project_path: str,
        hour: int = 2,
        focus_areas: Optional[List[str]] = None,
        db: Optional[AsyncSession] = None,
    ) -> str:
        """
        Schedule a daily quality scan.

        Args:
            project_id: Project identifier
            project_path: Path to project for scanning
            hour: Hour of day (0-23) to run scan
            focus_areas: Optional areas to focus on
            db: Optional database session for persistence

        Returns:
            schedule_id: Unique identifier for the schedule
        """
        schedule_id = str(uuid.uuid4())

        trigger = CronTrigger(hour=hour, minute=0, timezone='UTC')

        self.scheduler.add_job(
            self._execute_scheduled_scan,
            trigger=trigger,
            id=schedule_id,
            kwargs={
                'schedule_id': schedule_id,
                'project_id': project_id,
                'project_path': project_path,
                'focus_areas': focus_areas,
            },
            replace_existing=True,
        )

        # Store schedule info
        self._schedules[schedule_id] = {
            'project_id': project_id,
            'project_path': project_path,
            'schedule_type': ScheduleType.DAILY,
            'hour': hour,
            'focus_areas': focus_areas or [],
            'enabled': True,
            'created_at': datetime.now(timezone.utc),
        }

        # Persist to database if session provided
        if db:
            await self._persist_schedule(db, schedule_id)

        logger.info(f"Scheduled daily scan for {project_id} at {hour}:00 UTC (schedule_id: {schedule_id})")

        return schedule_id

    async def schedule_weekly_scan(
        self,
        project_id: str,
        project_path: str,
        day_of_week: str = "mon",
        hour: int = 2,
        focus_areas: Optional[List[str]] = None,
        db: Optional[AsyncSession] = None,
    ) -> str:
        """
        Schedule a weekly quality scan.

        Args:
            project_id: Project identifier
            project_path: Path to project for scanning
            day_of_week: Day of week (mon, tue, wed, thu, fri, sat, sun)
            hour: Hour of day (0-23) to run scan
            focus_areas: Optional areas to focus on
            db: Optional database session for persistence

        Returns:
            schedule_id: Unique identifier for the schedule
        """
        schedule_id = str(uuid.uuid4())

        trigger = CronTrigger(
            day_of_week=day_of_week,
            hour=hour,
            minute=0,
            timezone='UTC'
        )

        self.scheduler.add_job(
            self._execute_scheduled_scan,
            trigger=trigger,
            id=schedule_id,
            kwargs={
                'schedule_id': schedule_id,
                'project_id': project_id,
                'project_path': project_path,
                'focus_areas': focus_areas,
            },
            replace_existing=True,
        )

        self._schedules[schedule_id] = {
            'project_id': project_id,
            'project_path': project_path,
            'schedule_type': ScheduleType.WEEKLY,
            'day_of_week': day_of_week,
            'hour': hour,
            'focus_areas': focus_areas or [],
            'enabled': True,
            'created_at': datetime.now(timezone.utc),
        }

        if db:
            await self._persist_schedule(db, schedule_id)

        logger.info(f"Scheduled weekly scan for {project_id} on {day_of_week} at {hour}:00 UTC")

        return schedule_id

    async def schedule_interval_scan(
        self,
        project_id: str,
        project_path: str,
        hours: int = 24,
        focus_areas: Optional[List[str]] = None,
        db: Optional[AsyncSession] = None,
    ) -> str:
        """
        Schedule an interval-based quality scan.

        Args:
            project_id: Project identifier
            project_path: Path to project for scanning
            hours: Interval in hours between scans
            focus_areas: Optional areas to focus on
            db: Optional database session for persistence

        Returns:
            schedule_id: Unique identifier for the schedule
        """
        schedule_id = str(uuid.uuid4())

        trigger = IntervalTrigger(hours=hours, timezone='UTC')

        self.scheduler.add_job(
            self._execute_scheduled_scan,
            trigger=trigger,
            id=schedule_id,
            kwargs={
                'schedule_id': schedule_id,
                'project_id': project_id,
                'project_path': project_path,
                'focus_areas': focus_areas,
            },
            replace_existing=True,
        )

        self._schedules[schedule_id] = {
            'project_id': project_id,
            'project_path': project_path,
            'schedule_type': ScheduleType.INTERVAL,
            'interval_hours': hours,
            'focus_areas': focus_areas or [],
            'enabled': True,
            'created_at': datetime.now(timezone.utc),
        }

        if db:
            await self._persist_schedule(db, schedule_id)

        logger.info(f"Scheduled interval scan for {project_id} every {hours} hours")

        return schedule_id

    def remove_schedule(self, schedule_id: str) -> bool:
        """
        Remove a scheduled scan.

        Args:
            schedule_id: The schedule to remove

        Returns:
            True if removed, False if not found
        """
        try:
            self.scheduler.remove_job(schedule_id)
            if schedule_id in self._schedules:
                del self._schedules[schedule_id]
            logger.info(f"Removed schedule: {schedule_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to remove schedule {schedule_id}: {e}")
            return False

    def pause_schedule(self, schedule_id: str) -> bool:
        """Pause a scheduled scan."""
        try:
            self.scheduler.pause_job(schedule_id)
            if schedule_id in self._schedules:
                self._schedules[schedule_id]['enabled'] = False
            logger.info(f"Paused schedule: {schedule_id}")
            return True
        except Exception:
            return False

    def resume_schedule(self, schedule_id: str) -> bool:
        """Resume a paused schedule."""
        try:
            self.scheduler.resume_job(schedule_id)
            if schedule_id in self._schedules:
                self._schedules[schedule_id]['enabled'] = True
            logger.info(f"Resumed schedule: {schedule_id}")
            return True
        except Exception:
            return False

    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get schedule details."""
        return self._schedules.get(schedule_id)

    def list_schedules(
        self,
        project_id: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        List all schedules.

        Args:
            project_id: Optional filter by project
            enabled_only: Only return enabled schedules

        Returns:
            List of schedule details
        """
        schedules = []
        for schedule_id, info in self._schedules.items():
            if project_id and info['project_id'] != project_id:
                continue
            if enabled_only and not info.get('enabled', True):
                continue

            job = self.scheduler.get_job(schedule_id)
            schedules.append({
                'schedule_id': schedule_id,
                **info,
                'next_run_at': job.next_run_time if job else None,
            })

        return schedules

    async def _execute_scheduled_scan(
        self,
        schedule_id: str,
        project_id: str,
        project_path: str,
        focus_areas: Optional[List[str]] = None,
    ):
        """Execute a scheduled quality scan."""
        logger.info(f"Executing scheduled scan for {project_id} (schedule: {schedule_id})")

        try:
            if self._scan_callback:
                await self._scan_callback(
                    project_id=project_id,
                    project_path=project_path,
                    focus_areas=focus_areas,
                    triggered_by=f"schedule:{schedule_id}",
                )
                logger.info(f"Completed scheduled scan for {project_id}")
            else:
                logger.warning("No scan callback configured - scan skipped")

            # Update last run time
            if schedule_id in self._schedules:
                self._schedules[schedule_id]['last_run_at'] = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Scheduled scan failed for {project_id}: {e}")

    async def _persist_schedule(self, db: AsyncSession, schedule_id: str):
        """Persist schedule to database."""
        info = self._schedules.get(schedule_id)
        if not info:
            return

        try:
            await db.execute(text("""
                INSERT INTO quality_schedules (
                    schedule_id, project_id, schedule_type, schedule_config,
                    focus_areas, enabled, next_run_at, created_at
                ) VALUES (
                    :schedule_id, :project_id, :schedule_type, :schedule_config,
                    :focus_areas, :enabled, :next_run_at, :created_at
                )
                ON CONFLICT (schedule_id) DO UPDATE SET
                    enabled = :enabled,
                    schedule_config = :schedule_config
            """), {
                'schedule_id': schedule_id,
                'project_id': info['project_id'],
                'schedule_type': info['schedule_type'].value,
                'schedule_config': {
                    'hour': info.get('hour', 2),
                    'day_of_week': info.get('day_of_week', 'mon'),
                    'interval_hours': info.get('interval_hours', 24),
                },
                'focus_areas': info.get('focus_areas', []),
                'enabled': info.get('enabled', True),
                'next_run_at': None,  # Will be updated by scheduler
                'created_at': info.get('created_at', datetime.now(timezone.utc)),
            })
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to persist schedule: {e}")


# Singleton instance
_scheduler_instance: Optional[QualitySchedulerService] = None


def get_quality_scheduler() -> QualitySchedulerService:
    """Get the singleton scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = QualitySchedulerService()
    return _scheduler_instance
