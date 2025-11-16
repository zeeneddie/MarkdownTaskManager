"""
Workflow API endpoints for AI agent integration
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from typing import List, Dict, Any, Optional
import logging

from app.schemas.workflow import (
    WorkflowRequest,
    WorkflowResult,
    WorkTypeInfo,
    AgentInfo,
    WorkflowStatistics,
    SpecKitWorkflowRequest,
    SpecKitWorkflowResult,
    GeneratedFile
)
from app.services.agent_service import get_agent_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/analyze", response_model=WorkflowResult, status_code=status.HTTP_200_OK)
async def analyze_work(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks
) -> WorkflowResult:
    """
    Execute a workflow to analyze and plan work

    This endpoint:
    1. Classifies the work type based on the description
    2. Routes to the appropriate agent team
    3. Executes the workflow (sequential or parallel)
    4. Returns structured results (Epic → Features → Stories → Tasks)

    **Work Types:**
    - NEW_FEATURE: New feature development
    - MAINTENANCE: Code maintenance and refactoring
    - BUG: Bug fixing
    - QUALITY_AUDIT: Quality and security audit
    - ENHANCEMENT: Feature improvements
    - MIGRATION: Technology migration
    - QUALITY_IMPROVEMENT: Technical debt reduction
    - TESTING: Test coverage improvement

    **Example Request:**
    ```json
    {
      "description": "Add OAuth2 authentication with Google and GitHub",
      "context": {
        "files": ["src/auth/"],
        "dependencies": ["passport", "oauth2"]
      },
      "priority": "high"
    }
    ```

    **Example Response:**
    ```json
    {
      "work_type": "NEW_FEATURE",
      "status": "success",
      "agents_executed": [
        {
          "agent_name": "Felix",
          "agent_role": "Feature Architect",
          "output": {"epic": "OAuth2 Authentication"},
          "execution_time": 2.5,
          "status": "success"
        }
      ],
      "result": {
        "epic": "OAuth2 Authentication System",
        "features": ["Google OAuth", "GitHub OAuth"],
        "stories": ["User login with Google", "User login with GitHub"]
      }
    }
    ```
    """
    try:
        logger.info(f"Workflow request received: {request.description[:100]}")

        agent_service = get_agent_service()
        result = await agent_service.execute_workflow(request)

        logger.info(f"Workflow completed: {result.work_type}, status: {result.status}")

        return result

    except Exception as e:
        logger.error(f"Workflow execution error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.get("/work-types", response_model=List[WorkTypeInfo])
async def get_work_types() -> List[WorkTypeInfo]:
    """
    Get all available work types and their configurations

    Returns information about each work type including:
    - Name and description
    - Agent team composition
    - Execution process (sequential/parallel)
    - Workflow pipeline name

    **Example Response:**
    ```json
    [
      {
        "name": "NEW_FEATURE",
        "description": "New feature development from concept to implementation plan",
        "agents": ["Felix", "Eliza", "Tessa", "Quinn", "Diana"],
        "process": "sequential",
        "workflow": "spec_kit_pipeline"
      },
      {
        "name": "BUG",
        "description": "Bug investigation, fixing, and verification",
        "agents": ["Betty", "Tessa", "Diana"],
        "process": "sequential",
        "workflow": "bug_fix_pipeline"
      }
    ]
    ```
    """
    try:
        agent_service = get_agent_service()
        work_types = await agent_service.get_work_types()
        return work_types

    except Exception as e:
        logger.error(f"Error fetching work types: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch work types: {str(e)}"
        )


@router.get("/agents", response_model=List[AgentInfo])
async def get_agents() -> List[AgentInfo]:
    """
    Get all available agents and their status

    Returns information about each agent including:
    - Name and role
    - Description
    - Available tools
    - Current status (ready/not_configured/error)

    **Example Response:**
    ```json
    [
      {
        "name": "Felix",
        "role": "Feature Architect",
        "description": "Spec Kit specialist who transforms ideas into structured epics",
        "tools": ["spec_kit_constitution", "epic_creator", "feasibility_checker"],
        "status": "ready"
      },
      {
        "name": "Betty",
        "role": "Bug Hunter",
        "description": "Root cause analyst and bug fixing specialist",
        "tools": ["bug_analyzer", "stack_trace_parser", "test_case_generator"],
        "status": "ready"
      }
    ]
    ```
    """
    try:
        agent_service = get_agent_service()
        agents = await agent_service.get_agents()
        return agents

    except Exception as e:
        logger.error(f"Error fetching agents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch agents: {str(e)}"
        )


@router.get("/statistics", response_model=WorkflowStatistics)
async def get_statistics() -> WorkflowStatistics:
    """
    Get workflow execution statistics

    Returns metrics about workflow execution including:
    - Total workflows executed
    - Breakdown by work type
    - Average execution time
    - Success rate

    **Example Response:**
    ```json
    {
      "total_workflows_executed": 42,
      "workflows_by_type": {
        "NEW_FEATURE": 15,
        "BUG": 10,
        "MAINTENANCE": 8,
        "ENHANCEMENT": 9
      },
      "average_execution_time": 12.5,
      "success_rate": 0.95
    }
    ```
    """
    try:
        agent_service = get_agent_service()
        stats = await agent_service.get_statistics()

        return WorkflowStatistics(
            total_workflows_executed=stats.get("total_workflows_executed", 0),
            workflows_by_type=stats.get("workflows_by_type", {}),
            average_execution_time=stats.get("average_execution_time", 0.0),
            success_rate=stats.get("success_rate", 0.0)
        )

    except Exception as e:
        logger.error(f"Error fetching statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch statistics: {str(e)}"
        )


# ========================================
# ASYNC WORKFLOW EXECUTION (Celery)
# ========================================

@router.post("/analyze/async", status_code=status.HTTP_202_ACCEPTED)
async def analyze_work_async(request: WorkflowRequest) -> Dict[str, Any]:
    """
    Execute a workflow asynchronously using Celery

    This endpoint starts a workflow execution in the background and immediately
    returns a task ID. Use GET /workflows/tasks/{task_id} to check status.

    **Use this for:**
    - Long-running workflows (>30 seconds)
    - Large repositories
    - Multiple agent executions

    **Returns:**
    ```json
    {
      "task_id": "abc-123-def-456",
      "status": "PENDING",
      "message": "Workflow execution started",
      "check_status_url": "/api/workflows/tasks/abc-123-def-456"
    }
    ```
    """
    try:
        from app.tasks.workflow_tasks import execute_workflow_async

        # Start async task
        task = execute_workflow_async.delay(
            description=request.description,
            context=request.context or {},
            priority=request.priority,
            timeout=1800  # 30 minutes
        )

        return {
            "task_id": task.id,
            "status": "PENDING",
            "message": "Workflow execution started in background",
            "check_status_url": f"/api/workflows/tasks/{task.id}"
        }

    except Exception as e:
        logger.error(f"Error starting async workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start async workflow: {str(e)}"
        )


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get status of an async workflow task

    **Task States:**
    - PENDING: Task is waiting to be executed
    - STARTED: Task execution has begun
    - SUCCESS: Task completed successfully
    - FAILURE: Task failed
    - RETRY: Task is being retried

    **Example Response (in progress):**
    ```json
    {
      "task_id": "abc-123",
      "state": "STARTED",
      "info": {
        "description": "Add OAuth2 authentication",
        "started_at": "2025-11-13T10:30:00"
      },
      "ready": false,
      "successful": null,
      "failed": null
    }
    ```

    **Example Response (completed):**
    ```json
    {
      "task_id": "abc-123",
      "state": "SUCCESS",
      "info": {
        "work_type": "NEW_FEATURE",
        "status": "success",
        "total_execution_time": 45.2,
        "result": { ... }
      },
      "ready": true,
      "successful": true,
      "failed": false
    }
    ```
    """
    try:
        from celery.result import AsyncResult
        from app.celery_app import celery_app

        result = AsyncResult(task_id, app=celery_app)

        return {
            "task_id": task_id,
            "state": result.state,
            "info": result.info,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "failed": result.failed() if result.ready() else None,
        }

    except Exception as e:
        logger.error(f"Error fetching task status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch task status: {str(e)}"
        )


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str) -> Dict[str, Any]:
    """
    Cancel a running async workflow task

    **Returns:**
    ```json
    {
      "task_id": "abc-123",
      "cancelled": true,
      "message": "Task cancellation requested"
    }
    ```
    """
    try:
        from celery.result import AsyncResult
        from app.celery_app import celery_app

        result = AsyncResult(task_id, app=celery_app)
        result.revoke(terminate=True)

        return {
            "task_id": task_id,
            "cancelled": True,
            "message": "Task cancellation requested"
        }

    except Exception as e:
        logger.error(f"Error cancelling task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}"
        )


# ========================================
# SPEC-KIT WORKFLOW ENDPOINTS
# ========================================

@router.post("/spec-kit", response_model=SpecKitWorkflowResult, status_code=status.HTTP_200_OK)
async def execute_spec_kit_workflow(
    request: SpecKitWorkflowRequest
) -> SpecKitWorkflowResult:
    """
    Execute complete Spec-Kit workflow (Constitution → Specification → Tasks)

    This endpoint orchestrates the complete 3-stage Spec-Kit pipeline:
    1. **Constitution** (Peter - Product Owner): Define principles, requirements, constraints, risks, scope
    2. **Specification** (Felix - Feature Architect): Design architecture, components, interfaces, data model, quality
    3. **Tasks** (Felix - Feature Architect): Generate epics, features, stories, tasks with dependencies

    **Output Files:**
    - constitution.md - Project constitution document
    - specification.md - Technical specification
    - tasks.md - Work breakdown with Planning Poker guide
    - README.md - Project overview
    - metadata.json - Structured project metadata

    **Use Cases:**
    - New project definition
    - Major feature planning
    - RFP/proposal responses
    - Migration planning

    **Example Request:**
    ```json
    {
      "business_case": "Build e-commerce platform for SMBs",
      "stakeholders": ["CEO", "CTO", "Sales Team"],
      "constraints": ["Budget: €50k", "Timeline: 6 months", "Team: 5 devs"],
      "success_criteria": ["10k concurrent users", "99.9% uptime", "< 2s load"],
      "technical_context": {
        "existing_systems": ["Legacy Inventory"],
        "technologies": ["FastAPI", "Vue.js", "PostgreSQL"],
        "team_size": 5,
        "timeline": "6 months"
      },
      "project_path": "projects/ecommerce",
      "project_name": "E-commerce Platform"
    }
    ```

    **Returns:** Complete workflow result with all generated files
    """
    try:
        logger.info(f"Spec-Kit workflow request: {request.business_case[:100]}")

        agent_service = get_agent_service()
        result = await agent_service.execute_spec_kit_workflow(request)

        logger.info(f"Spec-Kit workflow completed: {len(result.files)} files generated")

        return result

    except Exception as e:
        logger.error(f"Spec-Kit workflow error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Spec-Kit workflow failed: {str(e)}"
        )


@router.post("/spec-kit/constitution", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def execute_constitution(
    request: SpecKitWorkflowRequest
) -> Dict[str, Any]:
    """
    Execute only the Constitution stage of Spec-Kit workflow

    **Agent:** Peter (Product Owner)

    **Generates:**
    - Guiding principles (5-8 core principles)
    - Functional requirements
    - Non-functional requirements
    - Constraints (budget, timeline, technical)
    - Risk assessment
    - Scope definition (in-scope / out-of-scope)

    **Output:** Constitution document with all project foundations

    **Use When:**
    - Need to validate project vision before technical design
    - Stakeholder alignment required
    - Business case review needed
    """
    try:
        logger.info(f"Constitution request: {request.business_case[:100]}")

        agent_service = get_agent_service()
        result = await agent_service.execute_constitution(request)

        logger.info("Constitution generation completed")

        return result

    except Exception as e:
        logger.error(f"Constitution generation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Constitution generation failed: {str(e)}"
        )


@router.post("/spec-kit/specification", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def execute_specification(
    request: SpecKitWorkflowRequest,
    constitution: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute only the Specification stage of Spec-Kit workflow

    **Agent:** Felix (Feature Architect)

    **Generates:**
    - Architecture pattern selection (Monolith, Microservices, Serverless, etc.)
    - Component breakdown with responsibilities
    - Interface definitions (REST API, GraphQL, WebSocket, etc.)
    - Data model (entities, relationships, validations)
    - Quality requirements (performance, security, scalability)

    **Input:** Business case + optional constitution result

    **Output:** Technical specification document

    **Use When:**
    - Constitution already exists
    - Need architecture design only
    - Technical review required
    """
    try:
        logger.info(f"Specification request: {request.business_case[:100]}")

        agent_service = get_agent_service()
        result = await agent_service.execute_specification(request, constitution)

        logger.info("Specification generation completed")

        return result

    except Exception as e:
        logger.error(f"Specification generation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Specification generation failed: {str(e)}"
        )


@router.post("/spec-kit/tasks", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def execute_tasks(
    request: SpecKitWorkflowRequest,
    specification: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute only the Tasks stage of Spec-Kit workflow

    **Agent:** Felix (Feature Architect)

    **Generates:**
    - Epics (from specification components)
    - Features (epic breakdown)
    - Stories (4-phase approach: Foundation → Core → Integration → Polish)
    - Tasks (with skill requirements and technical notes)
    - Suggested dependencies

    **Important:** All estimates are **TBD** - Team must use Planning Poker!

    **Output:** Work breakdown structure with Planning Poker guide

    **Use When:**
    - Constitution and specification already exist
    - Need task breakdown only
    - Sprint planning preparation
    """
    try:
        logger.info(f"Tasks generation request: {request.business_case[:100]}")

        agent_service = get_agent_service()
        result = await agent_service.execute_tasks(request, specification)

        logger.info("Tasks generation completed")

        return result

    except Exception as e:
        logger.error(f"Tasks generation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tasks generation failed: {str(e)}"
        )
