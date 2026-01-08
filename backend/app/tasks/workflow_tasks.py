"""
Celery Tasks for Async Workflow Execution

These tasks handle long-running workflow executions in the background.
"""
import asyncio
from datetime import datetime
from typing import Dict, Any
import logging

from celery import Task
from app.celery_app import celery_app
from app.schemas.workflow import WorkflowRequest, ProjectDefinitionRequest
from app.services.agent_service import get_agent_service
from app.services.project_service import get_project_service

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task class with callback support"""

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(f"Task {task_id} completed successfully")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        logger.error(f"Task {task_id} failed: {exc}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logger.warning(f"Task {task_id} retrying: {exc}")


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.tasks.workflow_tasks.execute_workflow_async",
    max_retries=3,
    default_retry_delay=60,  # 1 minute
)
def execute_workflow_async(
    self,
    description: str,
    context: Dict[str, Any] = None,
    priority: str = "medium",
    timeout: int = 1800
) -> Dict[str, Any]:
    """
    Execute a workflow asynchronously

    Args:
        self: Celery task instance
        description: Work description
        context: Additional context
        priority: Priority level
        timeout: Soft timeout in seconds (default 30 min)

    Returns:
        Dict with workflow result

    Raises:
        Exception: If workflow execution fails
    """
    logger.info(f"Starting async workflow execution: {self.request.id}")
    logger.info(f"Description: {description}")

    # Update task state to STARTED
    self.update_state(
        state="STARTED",
        meta={
            "description": description,
            "started_at": datetime.now().isoformat(),
        }
    )

    try:
        # Create request
        request = WorkflowRequest(
            description=description,
            context=context or {},
            priority=priority
        )

        # Get agent service
        agent_service = get_agent_service()

        # Execute workflow (async function, need to run in event loop)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                agent_service.execute_workflow(request, timeout=timeout)
            )
        finally:
            loop.close()

        # Convert result to dict
        result_dict = {
            "work_type": result.work_type,
            "status": result.status,
            "agents_executed": [
                {
                    "agent_name": agent.agent_name,
                    "agent_role": agent.agent_role,
                    "output": agent.output,
                    "execution_time": agent.execution_time,
                    "status": agent.status,
                }
                for agent in result.agents_executed
            ],
            "total_execution_time": result.total_execution_time,
            "result": result.result,
            "error": result.error,
            "timestamp": result.timestamp.isoformat(),
            "task_id": self.request.id,
        }

        logger.info(f"Workflow {self.request.id} completed: {result.status}")
        return result_dict

    except Exception as exc:
        logger.error(f"Workflow {self.request.id} failed: {exc}", exc_info=True)

        # Retry on failure
        try:
            raise self.retry(exc=exc, countdown=60)
        except self.MaxRetriesExceededError:
            # Return error result after max retries
            return {
                "work_type": "UNKNOWN",
                "status": "failed",
                "agents_executed": [],
                "total_execution_time": 0.0,
                "result": {},
                "error": str(exc),
                "timestamp": datetime.now().isoformat(),
                "task_id": self.request.id,
            }


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.tasks.workflow_tasks.execute_project_definition_async",
    max_retries=3,
    default_retry_delay=60,
)
def execute_project_definition_async(
    self,
    project_name: str,
    description: str,
    business_goals: list[str] = None,
    target_audience: str = None,
    constraints: list[str] = None,
    folder_path: str = None,
    timeout: int = 1800
) -> Dict[str, Any]:
    """
    Execute PROJECT_DEFINITION workflow asynchronously

    Args:
        self: Celery task instance
        project_name: Name of the project
        description: Project description
        business_goals: Business goals (optional)
        target_audience: Target audience (optional)
        constraints: Project constraints (optional)
        folder_path: Custom folder path (optional)
        timeout: Soft timeout in seconds (default 30 min)

    Returns:
        Dict with project definition result

    Raises:
        Exception: If project definition fails
    """
    logger.info(f"Starting async project definition: {self.request.id}")
    logger.info(f"Project: {project_name}")

    # Update task state
    self.update_state(
        state="STARTED",
        meta={
            "project_name": project_name,
            "started_at": datetime.now().isoformat(),
        }
    )

    try:
        # Create request
        request = ProjectDefinitionRequest(
            project_name=project_name,
            description=description,
            business_goals=business_goals,
            target_audience=target_audience,
            constraints=constraints,
            folder_path=folder_path
        )

        # Get project service
        project_service = get_project_service()

        # Execute project definition (async function)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                project_service.create_project(request, timeout=timeout)
            )
        finally:
            loop.close()

        # Convert result to dict
        result_dict = {
            "project_name": result.project_name,
            "business_case": result.business_case,
            "architecture": result.architecture,
            "epics": result.epics,
            "project_plan": result.project_plan,
            "documentation": result.documentation,
            "folder_structure": result.folder_structure,
            "workflow_execution": {
                "work_type": result.workflow_execution.work_type,
                "status": result.workflow_execution.status,
                "total_execution_time": result.workflow_execution.total_execution_time,
                "error": result.workflow_execution.error,
            },
            "task_id": self.request.id,
        }

        logger.info(f"Project definition {self.request.id} completed: {result.project_name}")
        return result_dict

    except Exception as exc:
        logger.error(f"Project definition {self.request.id} failed: {exc}", exc_info=True)

        # Retry on failure
        try:
            raise self.retry(exc=exc, countdown=60)
        except self.MaxRetriesExceededError:
            return {
                "project_name": project_name,
                "business_case": {},
                "architecture": {},
                "epics": [],
                "project_plan": {},
                "documentation": {},
                "folder_structure": {"created": False, "error": str(exc)},
                "workflow_execution": {
                    "work_type": "PROJECT_DEFINITION",
                    "status": "failed",
                    "total_execution_time": 0.0,
                    "error": str(exc),
                },
                "task_id": self.request.id,
            }


@celery_app.task(name="app.tasks.workflow_tasks.get_task_status")
def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get status of a Celery task

    Args:
        task_id: Celery task ID

    Returns:
        Dict with task status info
    """
    from celery.result import AsyncResult

    result = AsyncResult(task_id, app=celery_app)

    return {
        "task_id": task_id,
        "state": result.state,
        "info": result.info,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
        "failed": result.failed() if result.ready() else None,
    }


@celery_app.task(name="app.tasks.workflow_tasks.cancel_task")
def cancel_task(task_id: str) -> Dict[str, Any]:
    """
    Cancel a running Celery task

    Args:
        task_id: Celery task ID

    Returns:
        Dict with cancellation status
    """
    from celery.result import AsyncResult

    result = AsyncResult(task_id, app=celery_app)
    result.revoke(terminate=True)

    return {
        "task_id": task_id,
        "cancelled": True,
        "message": "Task cancellation requested",
    }
