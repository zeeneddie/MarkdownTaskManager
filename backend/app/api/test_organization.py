"""
Test Organization API

Week 57: API endpoints for managing test organization in projects.

Provides:
- Initialize test structure for projects
- Register test results
- Generate test reports
- Get developer feedback on test failures
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

from app.services.test_organization_service import (
    get_test_organization_service,
    TestType,
    TestStatus,
    TEST_FOLDER_STRUCTURE,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test-organization", tags=["test-organization"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class InitializeTestStructureRequest(BaseModel):
    """Request to initialize test structure."""
    project_path: str = Field(..., description="Path to project root")
    project_name: str = Field(..., description="Project name")


class InitializeTestStructureResponse(BaseModel):
    """Response from initializing test structure."""
    project: str
    tests_path: str
    created: List[str]
    structure: Dict[str, Any]


class RegisterTestResultRequest(BaseModel):
    """Request to register a test result."""
    project_name: str = Field(..., description="Project name")
    test_type: TestType = Field(..., description="Type of test")
    test_name: str = Field(..., description="Name of the test")
    status: TestStatus = Field(..., description="Test status")
    duration_ms: int = Field(0, description="Test duration in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    screenshots: Optional[List[str]] = Field(None, description="Screenshot paths for e2e tests")


class TestResultResponse(BaseModel):
    """Response with test result."""
    test_type: str
    test_name: str
    status: str
    duration_ms: int
    timestamp: str
    error_message: Optional[str]
    screenshots: List[str]


class TestCountsResponse(BaseModel):
    """Response with test counts by type."""
    unit: int
    module: int
    integration: int
    e2e: int


class GenerateReportRequest(BaseModel):
    """Request to generate test report."""
    project_path: str = Field(..., description="Path to project root")
    project_name: str = Field(..., description="Project name")


class TestReportResponse(BaseModel):
    """Response with test report."""
    project: str
    generated_at: str
    summary: Dict[str, Any]
    test_counts: Dict[str, int]
    failures: List[Dict[str, Any]]


class DeveloperFeedbackResponse(BaseModel):
    """Response with developer feedback."""
    status: str
    message: str
    action_required: bool
    failures: List[Dict[str, Any]]
    feedback: Optional[str] = None
    recommendation: Optional[str] = None


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/initialize", response_model=InitializeTestStructureResponse)
async def initialize_test_structure(request: InitializeTestStructureRequest):
    """
    Initialize the standard test folder structure for a project.

    Creates:
    - tests/unit/
    - tests/module/
    - tests/integration/
    - tests/e2e/screenshots/
    - tests/fixtures/
    - tests/reports/latest/
    - tests/reports/history/
    - tests/README.md

    **Example Request:**
    ```json
    {
      "project_path": "/opt/projecten/hci-crs",
      "project_name": "HCI-CRS"
    }
    ```
    """
    try:
        service = get_test_organization_service()
        result = service.initialize_test_structure(
            project_path=Path(request.project_path),
            project_name=request.project_name,
        )
        return InitializeTestStructureResponse(**result)

    except Exception as e:
        logger.error(f"Failed to initialize test structure: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize test structure: {str(e)}",
        )


@router.get("/structure")
async def get_test_structure():
    """
    Get the standard test folder structure definition.

    Returns the expected folder structure and naming conventions.
    """
    return {
        "structure": TEST_FOLDER_STRUCTURE,
        "test_types": [t.value for t in TestType],
        "test_statuses": [s.value for s in TestStatus],
    }


@router.post("/results", response_model=TestResultResponse)
async def register_test_result(request: RegisterTestResultRequest):
    """
    Register a test execution result.

    Called by Tessa (Test Agent) after running tests.

    **Example Request:**
    ```json
    {
      "project_name": "HCI-CRS",
      "test_type": "e2e",
      "test_name": "TC001_client_aanmaken",
      "status": "passed",
      "duration_ms": 5230,
      "screenshots": ["screenshots/tc001_step1.png"]
    }
    ```
    """
    try:
        service = get_test_organization_service()
        result = service.register_test_result(
            project_name=request.project_name,
            test_type=request.test_type,
            test_name=request.test_name,
            status=request.status,
            duration_ms=request.duration_ms,
            error_message=request.error_message,
            screenshots=request.screenshots,
        )
        return TestResultResponse(**result)

    except Exception as e:
        logger.error(f"Failed to register test result: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register test result: {str(e)}",
        )


@router.get("/results/{project_name}", response_model=List[TestResultResponse])
async def get_test_results(
    project_name: str,
    test_type: Optional[TestType] = None,
):
    """
    Get test results for a project.

    Optionally filter by test type (unit, module, integration, e2e).
    """
    try:
        service = get_test_organization_service()
        results = service.get_test_results(
            project_name=project_name,
            test_type=test_type,
        )
        return [TestResultResponse(**r) for r in results]

    except Exception as e:
        logger.error(f"Failed to get test results: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get test results: {str(e)}",
        )


@router.get("/counts/{project_path:path}", response_model=TestCountsResponse)
async def get_test_counts(project_path: str):
    """
    Count tests by type in a project.

    Scans the test folders and counts test files.
    """
    try:
        service = get_test_organization_service()
        counts = service.get_test_counts(Path(project_path))
        return TestCountsResponse(**counts)

    except Exception as e:
        logger.error(f"Failed to get test counts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get test counts: {str(e)}",
        )


@router.post("/report", response_model=TestReportResponse)
async def generate_test_report(request: GenerateReportRequest):
    """
    Generate a test report for a project.

    Creates a report in tests/reports/latest/ and archives to history/.

    **Example Request:**
    ```json
    {
      "project_path": "/opt/projecten/hci-crs",
      "project_name": "HCI-CRS"
    }
    ```
    """
    try:
        service = get_test_organization_service()
        report = service.generate_test_report(
            project_path=Path(request.project_path),
            project_name=request.project_name,
        )
        return TestReportResponse(
            project=report["project"],
            generated_at=report["generated_at"],
            summary=report["summary"],
            test_counts=report["test_counts"],
            failures=report["failures"],
        )

    except Exception as e:
        logger.error(f"Failed to generate test report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate test report: {str(e)}",
        )


@router.get("/feedback/{project_name}", response_model=DeveloperFeedbackResponse)
async def get_developer_feedback(project_name: str):
    """
    Get developer feedback based on test results.

    Used by Tessa to communicate issues back to the developer.

    Returns:
    - status: "success" or "failure"
    - message: Summary message
    - action_required: Whether developer action is needed
    - failures: List of failed tests
    - feedback: Detailed feedback text
    - recommendation: Suggested next steps
    """
    try:
        service = get_test_organization_service()
        feedback = service.get_developer_feedback(project_name)
        return DeveloperFeedbackResponse(**feedback)

    except Exception as e:
        logger.error(f"Failed to get developer feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get developer feedback: {str(e)}",
        )


@router.post("/run-tests/{project_name}")
async def trigger_test_run(
    project_name: str,
    test_type: Optional[TestType] = None,
):
    """
    Trigger Tessa to run tests for a project.

    This endpoint queues a test run request for the Test Agent.

    **Note:** This is an async operation - tests are executed by Tessa
    and results are registered via the /results endpoint.
    """
    # TODO: Integrate with agent workflow system
    return {
        "status": "queued",
        "project": project_name,
        "test_type": test_type.value if test_type else "all",
        "message": f"Test run queued for {project_name}. Tessa will execute and report results.",
    }
