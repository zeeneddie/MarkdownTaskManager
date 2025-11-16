"""
Celery Application Configuration

This module configures Celery for async task execution with Redis as broker.
"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "markdown_task_manager",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.workflow_tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
    },

    # Task execution settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,  # Fetch one task at a time
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks

    # Retry settings
    task_acks_late=True,  # Acknowledge tasks after completion
    task_reject_on_worker_lost=True,  # Reject tasks if worker crashes

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Task routes (optional - for multiple queues)
celery_app.conf.task_routes = {
    "app.tasks.workflow_tasks.execute_workflow_async": {"queue": "workflows"},
    "app.tasks.workflow_tasks.execute_project_definition_async": {"queue": "projects"},
}

# Beat schedule (optional - for periodic tasks)
celery_app.conf.beat_schedule = {
    # Example: Clean up old results every day
    # "cleanup-old-results": {
    #     "task": "app.tasks.workflow_tasks.cleanup_old_results",
    #     "schedule": crontab(hour=3, minute=0),  # Run at 3:00 AM daily
    # },
}
