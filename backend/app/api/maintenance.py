"""
Maintenance API Endpoints

Provides automated code maintenance workflows including:
- Dependency updates
- Security patches
- Code quality improvements
- Technical debt reduction
- Test coverage improvements

All maintenance requires an active project (project-first enforcement).
Results are stored in ChromaDB for historical pattern analysis.
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import subprocess
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


# ==================== REQUEST/RESPONSE MODELS ====================

class MaintenanceRequest(BaseModel):
    """Request to run code maintenance workflow"""
    project_id: int = Field(..., description="ID of the project to maintain")

    scope: str = Field(
        default="full_codebase",
        pattern="^(full_codebase|module|specific_files)$",
        description="Scope of maintenance analysis"
    )

    target_files: Optional[List[str]] = Field(
        None,
        description="Specific files to analyze (for 'specific_files' scope)"
    )

    module_path: Optional[str] = Field(
        None,
        description="Module path to analyze (for 'module' scope)"
    )

    focus_areas: Optional[List[str]] = Field(
        default_factory=lambda: ['dependencies', 'code_quality', 'security'],
        description="Areas to focus on: dependencies, code_quality, security, performance, tests, documentation"
    )

    urgency: str = Field(
        default="medium",
        pattern="^(low|medium|high|critical)$",
        description="Urgency level"
    )

    auto_fix: Optional[Dict[str, bool]] = Field(
        default_factory=lambda: {'dependencies': False, 'formatting': True, 'linting': True},
        description="Auto-fix configuration"
    )

    use_historical_patterns: bool = Field(
        default=True,
        description="Use historical maintenance patterns from RAG"
    )

    store_results: bool = Field(
        default=True,
        description="Store results in ChromaDB"
    )


class MaintenanceResponse(BaseModel):
    """Maintenance workflow execution response"""
    workflow_id: str
    project_id: int
    project_name: str
    status: str
    execution_time_ms: int

    # Summary metrics
    technical_debt_reduced: float
    vulnerabilities_fixed: int
    dependencies_updated: int
    code_smells_fixed: int

    # Detailed results (optional, can be large)
    analysis_summary: Optional[Dict[str, Any]] = None
    rag_insights: Optional[Dict[str, Any]] = None

    # ChromaDB reference
    chroma_document_id: Optional[str] = None

    # Timestamps
    started_at: datetime
    completed_at: datetime


class MaintenanceJobResponse(BaseModel):
    """Response for background job submission"""
    job_id: str
    status: str
    message: str
    check_status_url: str


class MaintenanceStatusResponse(BaseModel):
    """Status of a maintenance job"""
    job_id: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    progress: Optional[int] = None  # 0-100%
    current_stage: Optional[str] = None
    result: Optional[MaintenanceResponse] = None
    error: Optional[str] = None


# ==================== API ENDPOINTS ====================

@router.post("/run", response_model=MaintenanceResponse, status_code=status.HTTP_200_OK)
async def run_maintenance_workflow(request: MaintenanceRequest) -> MaintenanceResponse:
    """
    Run code maintenance workflow (synchronous)

    This executes the complete 6-stage maintenance workflow:
    1. ANALYSIS - Scan codebase for issues
    2. PRIORITIZATION - Rank findings by severity/impact
    3. PLANNING - Create maintenance plan
    4. EXECUTION - Apply automated fixes
    5. TESTING - Run test suite
    6. DEPLOYMENT - Create PR/commit

    **Prerequisites**:
    - Project must exist and be active
    - Project must have completed MarQed session
    - For brownfield: Quality scan required

    **Example Request**:
    ```json
    {
      "project_id": 123,
      "scope": "full_codebase",
      "focus_areas": ["dependencies", "security"],
      "urgency": "high",
      "auto_fix": {
        "dependencies": true,
        "formatting": true,
        "linting": true
      },
      "use_historical_patterns": true
    }
    ```

    **Example Response**:
    ```json
    {
      "workflow_id": "MAINT-123-1700000000",
      "project_id": 123,
      "project_name": "Patient Portal",
      "status": "completed",
      "execution_time_ms": 45000,
      "technical_debt_reduced": 2.5,
      "vulnerabilities_fixed": 3,
      "dependencies_updated": 12,
      "code_smells_fixed": 8,
      "chroma_document_id": "maintenance-123-1700000000"
    }
    ```
    """
    try:
        logger.info(f"Starting maintenance workflow for project {request.project_id}")

        # Build TypeScript execution command
        ts_request = {
            "project_id": request.project_id,
            "scope": request.scope,
            "targetFiles": request.target_files,
            "modulePath": request.module_path,
            "focusAreas": request.focus_areas,
            "urgency": request.urgency,
            "autoFix": request.auto_fix,
            "use_historical_patterns": request.use_historical_patterns,
            "store_results": request.store_results
        }

        # Execute TypeScript maintenance workflow
        result = await execute_ts_maintenance_workflow(ts_request)

        logger.info(f"Maintenance workflow completed for project {request.project_id}")

        return result

    except ValueError as e:
        # Validation errors (project not found, not active, etc.)
        logger.warning(f"Maintenance validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except subprocess.CalledProcessError as e:
        # TypeScript execution error
        logger.error(f"Maintenance workflow execution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {e.stderr}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in maintenance workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Maintenance workflow failed: {str(e)}"
        )


@router.post("/run-async", response_model=MaintenanceJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_maintenance_workflow_async(
    request: MaintenanceRequest,
    background_tasks: BackgroundTasks
) -> MaintenanceJobResponse:
    """
    Run code maintenance workflow (asynchronous)

    Submits maintenance workflow as background job for long-running operations.
    Use this when maintenance may take >30 seconds.

    Returns job ID to check status with GET /maintenance/jobs/{job_id}

    **Example Response**:
    ```json
    {
      "job_id": "MAINT-JOB-123-1700000000",
      "status": "pending",
      "message": "Maintenance workflow submitted",
      "check_status_url": "/api/maintenance/jobs/MAINT-JOB-123-1700000000"
    }
    ```
    """
    try:
        job_id = f"MAINT-JOB-{request.project_id}-{int(datetime.now().timestamp())}"

        logger.info(f"Submitting async maintenance workflow: {job_id}")

        # Add to background tasks
        # background_tasks.add_task(execute_maintenance_background, job_id, request)

        # TODO: Store job in database or cache for status tracking

        return MaintenanceJobResponse(
            job_id=job_id,
            status="pending",
            message="Maintenance workflow submitted successfully",
            check_status_url=f"/api/maintenance/jobs/{job_id}"
        )

    except Exception as e:
        logger.error(f"Failed to submit async maintenance workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit workflow: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=MaintenanceStatusResponse)
async def get_maintenance_job_status(job_id: str) -> MaintenanceStatusResponse:
    """
    Get status of a maintenance job

    Returns current status and progress of an async maintenance workflow.

    **Statuses**:
    - pending: Job queued, not started
    - running: Job in progress
    - completed: Job finished successfully
    - failed: Job encountered an error

    **Example Response**:
    ```json
    {
      "job_id": "MAINT-JOB-123-1700000000",
      "status": "running",
      "progress": 65,
      "current_stage": "Stage 4: Execution"
    }
    ```
    """
    try:
        logger.info(f"Getting status for maintenance job {job_id}")

        # TODO: Query job status from database/cache

        # Placeholder response
        return MaintenanceStatusResponse(
            job_id=job_id,
            status="running",
            progress=65,
            current_stage="Stage 4: Execution",
            result=None,
            error=None
        )

    except Exception as e:
        logger.error(f"Failed to get job status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )


@router.get("/history/{project_id}", response_model=List[Dict[str, Any]])
async def get_maintenance_history(
    project_id: int,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get maintenance history for a project

    Returns past maintenance executions from ChromaDB.

    **Query Parameters**:
    - limit: Maximum number of records to return (default: 10)

    **Example Response**:
    ```json
    [
      {
        "workflow_id": "MAINT-123-1700000000",
        "executed_at": "2025-11-18T10:00:00Z",
        "technical_debt_reduced": 2.5,
        "vulnerabilities_fixed": 3,
        "status": "completed"
      }
    ]
    ```
    """
    try:
        logger.info(f"Getting maintenance history for project {project_id}")

        # TODO: Query ChromaDB code_analysis collection for maintenance history

        # Placeholder response
        history = []

        return history

    except Exception as e:
        logger.error(f"Failed to get maintenance history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve history: {str(e)}"
        )


# ==================== HELPER FUNCTIONS ====================

async def execute_ts_maintenance_workflow(request: Dict[str, Any]) -> MaintenanceResponse:
    """
    Execute TypeScript maintenance workflow via subprocess

    Calls the maintenanceWorkflowIntegration.ts module
    """
    # TODO: Implement actual subprocess call to TypeScript
    # For now, return mock response

    workflow_id = f"MAINT-{request['project_id']}-{int(datetime.now().timestamp())}"

    return MaintenanceResponse(
        workflow_id=workflow_id,
        project_id=request['project_id'],
        project_name="Example Project",
        status="completed",
        execution_time_ms=45000,
        technical_debt_reduced=2.5,
        vulnerabilities_fixed=3,
        dependencies_updated=12,
        code_smells_fixed=8,
        analysis_summary={
            "total_findings": 45,
            "critical": 3,
            "high": 8,
            "medium": 20,
            "low": 14
        },
        rag_insights={
            "similar_patterns": 5,
            "average_fix_time_hours": 2.5
        },
        chroma_document_id=f"maintenance-{request['project_id']}-{int(datetime.now().timestamp())}",
        started_at=datetime.now(),
        completed_at=datetime.now()
    )


# ==================== MARCUS AGENT INTEGRATION ====================

class MarcusScanRequest(BaseModel):
    """Request for Marcus-powered maintenance scan"""
    scope: str = Field(
        default="full_codebase",
        pattern="^(full_codebase|module|specific_files)$",
        description="Scope of maintenance analysis"
    )
    focus_areas: List[str] = Field(
        default_factory=lambda: ["dependencies", "security", "code_quality"],
        description="Areas to focus on"
    )
    urgency: str = Field(
        default="medium",
        pattern="^(low|medium|high|critical)$",
        description="Urgency level"
    )
    target_path: Optional[str] = Field(
        None,
        description="Specific path to analyze"
    )


class MarcusStatusResponse(BaseModel):
    """Marcus agent status response"""
    agent: str
    role: str
    llm: str
    available: bool
    specialties: List[str]
    timestamp: datetime


class MarcusScanResponse(BaseModel):
    """Response from Marcus scan"""
    scan_id: str
    status: str
    scope: str
    focus_areas: List[str]
    urgency: str
    total_findings: int
    findings: List[Dict[str, Any]]
    priority_actions: List[str]
    summary: Dict[str, Any]
    duration_seconds: float
    start_time: datetime
    end_time: Optional[datetime] = None


@router.get("/marcus/status", response_model=MarcusStatusResponse)
async def get_marcus_status():
    """
    Get Marcus agent status

    Checks if Marcus (Maintenance Specialist Agent) is available.
    Marcus requires Ollama with qwen2.5-coder:7b model.

    **Returns:**
    - Agent name, role, LLM model
    - Availability status
    - Agent specialties
    """
    try:
        from app.services.marcus_integration import check_marcus_status

        status = await check_marcus_status()

        return MarcusStatusResponse(
            agent=status["agent"],
            role=status["role"],
            llm=status["llm"],
            available=status["available"],
            specialties=status["specialties"],
            timestamp=datetime.fromisoformat(status["timestamp"])
        )

    except ImportError:
        logger.warning("Marcus integration not available")
        return MarcusStatusResponse(
            agent="Marcus",
            role="Maintenance Specialist",
            llm="qwen2.5-coder:7b",
            available=False,
            specialties=["refactoring", "dependency_updates", "code_health"],
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Failed to get Marcus status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check Marcus status: {str(e)}"
        )


@router.post("/marcus/scan", response_model=MarcusScanResponse)
async def run_marcus_scan(request: MarcusScanRequest):
    """
    Run Marcus-powered maintenance scan

    Executes a maintenance scan using the Marcus AI agent.
    Marcus analyzes code for:
    - Dependencies: Outdated packages, security vulnerabilities
    - Security: OWASP issues, hardcoded secrets
    - Code Quality: Code smells, anti-patterns, complexity
    - Tech Debt: Legacy patterns, missing tests

    **Requires:** Ollama running with qwen2.5-coder:7b model

    **Example Request:**
    ```json
    {
      "scope": "full_codebase",
      "focus_areas": ["dependencies", "security"],
      "urgency": "high"
    }
    ```

    **Example Response:**
    ```json
    {
      "scan_id": "marcus_scan_20251121_120000",
      "status": "completed",
      "total_findings": 15,
      "priority_actions": [
        "Update fastapi to 0.109.0 (security fix)",
        "Remove hardcoded API key in config.py"
      ]
    }
    ```
    """
    try:
        from app.services.marcus_integration import (
            get_marcus_agent,
            MaintenanceScope,
            FocusArea,
            Urgency
        )

        marcus = get_marcus_agent()

        # Convert to enums
        scope_enum = MaintenanceScope(request.scope)
        focus_enums = [FocusArea(f) for f in request.focus_areas]
        urgency_enum = Urgency(request.urgency)

        # Run scan
        result = await marcus.run_maintenance_scan(
            scope=scope_enum,
            focus_areas=focus_enums,
            urgency=urgency_enum,
            target_path=request.target_path
        )

        # Broadcast to WebSocket clients
        try:
            from app.api.websocket import broadcast_scan_completed
            await broadcast_scan_completed(
                scan_id=result.get("scan_id", ""),
                findings_count=result.get("total_findings", 0),
                tasks_created=0,
                duration_seconds=result.get("duration_seconds", 0)
            )
        except ImportError:
            pass

        return MarcusScanResponse(
            scan_id=result.get("scan_id", ""),
            status=result.get("status", "unknown"),
            scope=result.get("scope", request.scope),
            focus_areas=result.get("focus_areas", request.focus_areas),
            urgency=result.get("urgency", request.urgency),
            total_findings=result.get("total_findings", 0),
            findings=result.get("findings", []),
            priority_actions=result.get("priority_actions", []),
            summary=result.get("summary", {}),
            duration_seconds=result.get("duration_seconds", 0),
            start_time=datetime.fromisoformat(result.get("start_time", datetime.now().isoformat())),
            end_time=datetime.fromisoformat(result["end_time"]) if result.get("end_time") else None
        )

    except ImportError as e:
        logger.error(f"Marcus integration not available: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Marcus agent integration not available"
        )

    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Marcus scan failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Marcus scan failed: {str(e)}"
        )
