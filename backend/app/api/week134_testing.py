"""
Week 134-135: Testing Excellence API

API endpoints for characterization tests, visual regression, and dual-run comparison.
Part of Fase 23 - Testing Excellence for migration validation.

Agent: Tessa (Test Engineer) + Vicky (Visual Designer)
"""
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.characterization_test_service import CharacterizationTestService
from app.services.visual_regression_service import VisualRegressionService
from app.services.dual_run_comparison_service import DualRunComparisonService, SystemConfig
from app.models.week134_testing import (
    TestStatus,
    ComparisonResult,
    ScreenshotTool,
    OutputFormat,
    TestInput,
)

router = APIRouter(prefix="/api/testing-excellence", tags=["testing-excellence"])


# ============================================================================
# Request/Response Models
# ============================================================================

class RecordBaselineRequest(BaseModel):
    """Request for recording a Golden Master baseline."""
    test_name: str = Field(..., description="Human-readable test name")
    legacy_endpoint: str = Field(..., description="URL of legacy system endpoint")
    input_data: Dict[str, Any] = Field(..., description="Input data to send")
    input_scenario: Optional[str] = Field(None, description="Scenario name")
    method: str = Field("POST", description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers")


class CompareWithBaselineRequest(BaseModel):
    """Request for comparing against a baseline."""
    test_name: str = Field(..., description="Human-readable test name")
    new_endpoint: str = Field(..., description="URL of new system endpoint")
    input_data: Dict[str, Any] = Field(..., description="Input data to send")
    input_scenario: Optional[str] = Field(None, description="Scenario name")
    method: str = Field("POST", description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers")
    ignored_fields: Optional[List[str]] = Field(None, description="Fields to ignore")
    tolerance_rules: Optional[Dict[str, Any]] = Field(None, description="Numeric tolerances")
    baseline_data: Optional[Dict[str, Any]] = Field(None, description="Override baseline")


class FullTestRequest(BaseModel):
    """Request for full characterization test (both systems)."""
    test_name: str = Field(..., description="Human-readable test name")
    legacy_endpoint: str = Field(..., description="URL of legacy system")
    new_endpoint: str = Field(..., description="URL of new system")
    input_data: Dict[str, Any] = Field(..., description="Input data to send")
    input_scenario: Optional[str] = Field(None, description="Scenario name")
    method: str = Field("POST", description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers")
    ignored_fields: Optional[List[str]] = Field(None, description="Fields to ignore")
    tolerance_rules: Optional[Dict[str, Any]] = Field(None, description="Numeric tolerances")


class BatchTestRequest(BaseModel):
    """Request for batch characterization tests."""
    test_name: str = Field(..., description="Base test name")
    legacy_endpoint: str = Field(..., description="URL of legacy system")
    new_endpoint: str = Field(..., description="URL of new system")
    test_inputs: List[Dict[str, Any]] = Field(..., description="List of test inputs")
    method: str = Field("POST", description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers")
    ignored_fields: Optional[List[str]] = Field(None, description="Fields to ignore")
    tolerance_rules: Optional[Dict[str, Any]] = Field(None, description="Numeric tolerances")


class VisualBaselineRequest(BaseModel):
    """Request for capturing visual baseline."""
    test_name: str = Field(..., description="Human-readable test name")
    legacy_url: str = Field(..., description="URL to capture")
    viewport_width: int = Field(1920, description="Viewport width")
    viewport_height: int = Field(1080, description="Viewport height")
    full_page: bool = Field(False, description="Capture full page")
    wait_for_selector: Optional[str] = Field(None, description="Wait for element")
    hide_selectors: Optional[List[str]] = Field(None, description="Elements to hide")


class VisualCompareRequest(BaseModel):
    """Request for visual comparison."""
    test_name: str = Field(..., description="Human-readable test name")
    new_url: str = Field(..., description="URL to capture and compare")
    viewport_width: int = Field(1920, description="Viewport width")
    viewport_height: int = Field(1080, description="Viewport height")
    full_page: bool = Field(False, description="Capture full page")
    wait_for_selector: Optional[str] = Field(None, description="Wait for element")
    hide_selectors: Optional[List[str]] = Field(None, description="Elements to hide")
    diff_threshold: float = Field(0.1, ge=0.0, le=1.0, description="Max allowed diff")
    baseline_path: Optional[str] = Field(None, description="Override baseline path")


class DualRunSessionRequest(BaseModel):
    """Request for creating a dual-run comparison session."""
    session_name: str = Field(..., description="Session name")
    legacy_base_url: str = Field(..., description="Legacy system base URL")
    new_base_url: str = Field(..., description="New system base URL")
    legacy_headers: Optional[Dict[str, str]] = Field(None, description="Legacy headers")
    new_headers: Optional[Dict[str, str]] = Field(None, description="New headers")
    shadow_mode: bool = Field(True, description="Enable shadow mode")


class DualRunExecuteRequest(BaseModel):
    """Request for executing a dual-run request."""
    endpoint_path: str = Field(..., description="Endpoint path (e.g., /api/users)")
    method: str = Field("GET", description="HTTP method")
    request_data: Optional[Dict[str, Any]] = Field(None, description="Request body")
    query_params: Optional[Dict[str, str]] = Field(None, description="Query parameters")
    ignored_fields: Optional[List[str]] = Field(None, description="Fields to ignore")
    tolerance_rules: Optional[Dict[str, Any]] = Field(None, description="Numeric tolerances")


# ============================================================================
# Service Instances
# ============================================================================

characterization_service = CharacterizationTestService()
visual_service = VisualRegressionService()
dual_run_sessions: Dict[str, DualRunComparisonService] = {}


# ============================================================================
# Characterization Test Endpoints (Golden Master)
# ============================================================================

@router.post("/characterization/record-baseline")
async def record_characterization_baseline(request: RecordBaselineRequest) -> Dict[str, Any]:
    """
    Record legacy system output as Golden Master baseline.

    This captures the current behavior of the legacy system for later comparison.
    Use this to establish what the "correct" output looks like before migration.
    """
    test_id = str(uuid4())

    result = await characterization_service.record_baseline(
        test_id=test_id,
        test_name=request.test_name,
        legacy_endpoint=request.legacy_endpoint,
        input_data=request.input_data,
        input_scenario=request.input_scenario,
        method=request.method,
        headers=request.headers,
    )

    return {
        "test_id": test_id,
        "test_name": result.test_name,
        "result": result.result.value,
        "match_percentage": result.match_percentage,
        "legacy_duration_ms": result.legacy_duration_ms,
        "legacy_output": result.legacy_output,
        "error": result.error,
    }


@router.post("/characterization/compare/{test_id}")
async def compare_with_characterization_baseline(
    test_id: str,
    request: CompareWithBaselineRequest,
) -> Dict[str, Any]:
    """
    Compare new system output against recorded baseline.

    Returns detailed field-level differences with confidence scoring.
    """
    result = await characterization_service.compare_with_baseline(
        test_id=test_id,
        test_name=request.test_name,
        new_endpoint=request.new_endpoint,
        input_data=request.input_data,
        input_scenario=request.input_scenario,
        method=request.method,
        headers=request.headers,
        ignored_fields=request.ignored_fields,
        tolerance_rules=request.tolerance_rules,
        baseline_data=request.baseline_data,
    )

    differences = [
        {
            "field_path": d.field_path,
            "diff_type": d.diff_type.value,
            "expected_value": d.expected_value,
            "actual_value": d.actual_value,
            "message": d.message,
        }
        for d in (result.differences or [])
    ]

    return {
        "test_id": result.test_id,
        "test_name": result.test_name,
        "result": result.result.value,
        "match_percentage": result.match_percentage,
        "diff_count": result.diff_count,
        "differences": differences,
        "new_duration_ms": result.new_duration_ms,
        "error": result.error,
    }


@router.post("/characterization/run-test")
async def run_full_characterization_test(request: FullTestRequest) -> Dict[str, Any]:
    """
    Run full characterization test: call both systems and compare.

    This is the primary endpoint for migration validation. It calls both
    legacy and new systems, compares outputs, and returns detailed differences.
    """
    test_id = str(uuid4())

    result = await characterization_service.run_full_test(
        test_id=test_id,
        test_name=request.test_name,
        legacy_endpoint=request.legacy_endpoint,
        new_endpoint=request.new_endpoint,
        input_data=request.input_data,
        input_scenario=request.input_scenario,
        method=request.method,
        headers=request.headers,
        ignored_fields=request.ignored_fields,
        tolerance_rules=request.tolerance_rules,
    )

    differences = [
        {
            "field_path": d.field_path,
            "diff_type": d.diff_type.value,
            "expected_value": d.expected_value,
            "actual_value": d.actual_value,
            "message": d.message,
        }
        for d in (result.differences or [])
    ]

    return {
        "test_id": test_id,
        "test_name": result.test_name,
        "result": result.result.value,
        "match_percentage": result.match_percentage,
        "diff_count": result.diff_count,
        "differences": differences,
        "legacy_duration_ms": result.legacy_duration_ms,
        "new_duration_ms": result.new_duration_ms,
        "performance_comparison": {
            "legacy_ms": result.legacy_duration_ms,
            "new_ms": result.new_duration_ms,
            "diff_ms": (result.new_duration_ms or 0) - (result.legacy_duration_ms or 0),
            "new_faster": (result.new_duration_ms or 0) < (result.legacy_duration_ms or 0),
        },
        "error": result.error,
    }


@router.post("/characterization/batch")
async def run_batch_characterization_tests(request: BatchTestRequest) -> Dict[str, Any]:
    """
    Run batch of characterization tests with multiple inputs.

    Useful for testing edge cases, boundary conditions, and various scenarios.
    """
    base_test_id = str(uuid4())

    # Convert dict inputs to TestInput objects
    test_inputs = [
        TestInput(
            name=inp.get("name", f"Scenario {i+1}"),
            data=inp.get("data", inp),
            description=inp.get("description", ""),
        )
        for i, inp in enumerate(request.test_inputs)
    ]

    results = await characterization_service.run_batch_tests(
        test_id=base_test_id,
        test_name=request.test_name,
        legacy_endpoint=request.legacy_endpoint,
        new_endpoint=request.new_endpoint,
        test_inputs=test_inputs,
        method=request.method,
        headers=request.headers,
        ignored_fields=request.ignored_fields,
        tolerance_rules=request.tolerance_rules,
    )

    # Summarize results
    total = len(results)
    matches = sum(1 for r in results if r.result == ComparisonResult.MATCH)
    mismatches = sum(1 for r in results if r.result == ComparisonResult.MISMATCH)
    errors = sum(1 for r in results if r.result == ComparisonResult.ERROR)

    return {
        "batch_id": base_test_id,
        "test_name": request.test_name,
        "summary": {
            "total": total,
            "matches": matches,
            "mismatches": mismatches,
            "errors": errors,
            "pass_rate": (matches / total * 100) if total > 0 else 0,
        },
        "results": [
            {
                "test_id": r.test_id,
                "scenario": r.input_scenario,
                "result": r.result.value,
                "match_percentage": r.match_percentage,
                "diff_count": r.diff_count,
                "error": r.error,
            }
            for r in results
        ],
    }


@router.get("/characterization/baseline/{test_id}")
async def get_characterization_baseline(test_id: str) -> Dict[str, Any]:
    """Get stored baseline for a test."""
    baseline = characterization_service.get_baseline(test_id)

    if baseline is None:
        raise HTTPException(status_code=404, detail=f"Baseline not found for test {test_id}")

    return {
        "test_id": test_id,
        "baseline": baseline,
    }


@router.delete("/characterization/baseline/{test_id}")
async def delete_characterization_baseline(test_id: str) -> Dict[str, Any]:
    """Delete stored baseline for a test."""
    success = characterization_service.clear_baseline(test_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Baseline not found for test {test_id}")

    return {
        "test_id": test_id,
        "deleted": True,
    }


# ============================================================================
# Visual Regression Test Endpoints
# ============================================================================

@router.post("/visual/capture-baseline")
async def capture_visual_baseline(request: VisualBaselineRequest) -> Dict[str, Any]:
    """
    Capture visual baseline screenshot from legacy system.

    Uses Playwright to render the page and capture a screenshot.
    """
    test_id = str(uuid4())

    result = await visual_service.capture_baseline(
        test_id=test_id,
        test_name=request.test_name,
        url=request.legacy_url,
        viewport_width=request.viewport_width,
        viewport_height=request.viewport_height,
        full_page=request.full_page,
        wait_for_selector=request.wait_for_selector,
        hide_selectors=request.hide_selectors,
    )

    return {
        "test_id": test_id,
        "test_name": result.test_name,
        "result": result.result.value,
        "baseline_path": result.baseline_path,
        "baseline_dimensions": result.baseline_dimensions,
        "capture_duration_ms": result.legacy_duration_ms,
        "error": result.error,
    }


@router.post("/visual/compare/{test_id}")
async def compare_visual_with_baseline(
    test_id: str,
    request: VisualCompareRequest,
) -> Dict[str, Any]:
    """
    Compare new system screenshot against visual baseline.

    Returns diff percentage and highlighted difference regions.
    """
    result = await visual_service.compare_with_baseline(
        test_id=test_id,
        test_name=request.test_name,
        url=request.new_url,
        viewport_width=request.viewport_width,
        viewport_height=request.viewport_height,
        full_page=request.full_page,
        wait_for_selector=request.wait_for_selector,
        hide_selectors=request.hide_selectors,
        diff_threshold=request.diff_threshold,
        baseline_path=request.baseline_path,
    )

    diff_regions = [
        {
            "x": r.x,
            "y": r.y,
            "width": r.width,
            "height": r.height,
            "diff_percentage": r.diff_percentage,
        }
        for r in (result.diff_regions or [])
    ]

    return {
        "test_id": result.test_id,
        "test_name": result.test_name,
        "result": result.result.value,
        "match_percentage": result.match_percentage,
        "diff_percentage": result.diff_percentage,
        "diff_region_count": len(diff_regions),
        "diff_regions": diff_regions,
        "diff_image_path": result.diff_image_path,
        "new_screenshot_path": result.new_screenshot_path,
        "threshold": request.diff_threshold,
        "passed": result.result == ComparisonResult.MATCH,
        "error": result.error,
    }


@router.post("/visual/batch-compare")
async def batch_visual_compare(
    legacy_urls: List[str],
    new_urls: List[str],
    test_name: str = Query(..., description="Base test name"),
    viewport_width: int = Query(1920, description="Viewport width"),
    viewport_height: int = Query(1080, description="Viewport height"),
    diff_threshold: float = Query(0.1, ge=0.0, le=1.0, description="Max diff threshold"),
) -> Dict[str, Any]:
    """
    Run batch visual comparison for multiple URL pairs.

    Useful for comparing multiple pages during migration.
    """
    if len(legacy_urls) != len(new_urls):
        raise HTTPException(
            status_code=400,
            detail="legacy_urls and new_urls must have the same length"
        )

    batch_id = str(uuid4())

    results = await visual_service.run_batch_comparison(
        test_id=batch_id,
        test_name=test_name,
        legacy_urls=legacy_urls,
        new_urls=new_urls,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        diff_threshold=diff_threshold,
    )

    total = len(results)
    passes = sum(1 for r in results if r.result == ComparisonResult.MATCH)

    return {
        "batch_id": batch_id,
        "test_name": test_name,
        "summary": {
            "total": total,
            "passes": passes,
            "failures": total - passes,
            "pass_rate": (passes / total * 100) if total > 0 else 0,
        },
        "results": [
            {
                "test_id": r.test_id,
                "result": r.result.value,
                "match_percentage": r.match_percentage,
                "diff_percentage": r.diff_percentage,
                "diff_image_path": r.diff_image_path,
                "error": r.error,
            }
            for r in results
        ],
    }


@router.put("/visual/update-baseline/{test_id}")
async def update_visual_baseline(
    test_id: str,
    new_screenshot_path: str = Query(..., description="Path to new screenshot"),
) -> Dict[str, Any]:
    """
    Update baseline with new screenshot (approve changes).

    Use this when intentional visual changes have been made.
    """
    success = await visual_service.update_baseline(test_id, new_screenshot_path)

    if not success:
        raise HTTPException(status_code=404, detail=f"Baseline not found for test {test_id}")

    return {
        "test_id": test_id,
        "updated": True,
        "new_baseline_path": new_screenshot_path,
    }


# ============================================================================
# Dual-Run Comparison Endpoints
# ============================================================================

@router.post("/dual-run/session")
async def create_dual_run_session(request: DualRunSessionRequest) -> Dict[str, Any]:
    """
    Create a dual-run comparison session.

    This session will execute requests against both legacy and new systems
    and compare the results. Shadow mode ensures new system responses are
    not returned to callers.
    """
    session_id = str(uuid4())

    legacy_config = SystemConfig(
        base_url=request.legacy_base_url,
        headers=request.legacy_headers,
    )

    new_config = SystemConfig(
        base_url=request.new_base_url,
        headers=request.new_headers,
    )

    service = DualRunComparisonService(
        legacy_config=legacy_config,
        new_config=new_config,
        shadow_mode=request.shadow_mode,
    )

    dual_run_sessions[session_id] = service

    return {
        "session_id": session_id,
        "session_name": request.session_name,
        "legacy_base_url": request.legacy_base_url,
        "new_base_url": request.new_base_url,
        "shadow_mode": request.shadow_mode,
        "created": True,
    }


@router.post("/dual-run/{session_id}/execute")
async def execute_dual_run_request(
    session_id: str,
    request: DualRunExecuteRequest,
) -> Dict[str, Any]:
    """
    Execute a request against both systems and compare results.

    Returns comparison results including field-level differences.
    """
    if session_id not in dual_run_sessions:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    service = dual_run_sessions[session_id]

    result = await service.execute_request(
        endpoint_path=request.endpoint_path,
        method=request.method,
        request_data=request.request_data,
        query_params=request.query_params,
        ignored_fields=request.ignored_fields,
        tolerance_rules=request.tolerance_rules,
    )

    differences = [
        {
            "field_path": d.field_path,
            "diff_type": d.diff_type.value,
            "expected_value": d.expected_value,
            "actual_value": d.actual_value,
            "message": d.message,
        }
        for d in (result.differences or [])
    ]

    return {
        "request_id": result.request_id,
        "endpoint": request.endpoint_path,
        "method": request.method,
        "result": result.result.value,
        "match_percentage": result.match_percentage,
        "diff_count": result.diff_count,
        "differences": differences,
        "legacy_status": result.legacy_status,
        "new_status": result.new_status,
        "legacy_duration_ms": result.legacy_duration_ms,
        "new_duration_ms": result.new_duration_ms,
        "error": result.error,
    }


@router.post("/dual-run/{session_id}/batch")
async def execute_dual_run_batch(
    session_id: str,
    requests: List[DualRunExecuteRequest],
) -> Dict[str, Any]:
    """
    Execute batch of requests against both systems.

    Useful for replaying traffic logs or running test suites.
    """
    if session_id not in dual_run_sessions:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    service = dual_run_sessions[session_id]

    # Convert to internal format
    request_dicts = [
        {
            "endpoint_path": r.endpoint_path,
            "method": r.method,
            "data": r.request_data,
            "query_params": r.query_params,
        }
        for r in requests
    ]

    results = await service.execute_batch(
        requests=request_dicts,
        ignored_fields=requests[0].ignored_fields if requests else None,
        tolerance_rules=requests[0].tolerance_rules if requests else None,
    )

    total = len(results)
    matches = sum(1 for r in results if r.result == ComparisonResult.MATCH)
    mismatches = sum(1 for r in results if r.result == ComparisonResult.MISMATCH)
    errors = sum(1 for r in results if r.result == ComparisonResult.ERROR)

    return {
        "session_id": session_id,
        "summary": {
            "total": total,
            "matches": matches,
            "mismatches": mismatches,
            "errors": errors,
            "match_rate": (matches / total * 100) if total > 0 else 0,
        },
        "results": [
            {
                "request_id": r.request_id,
                "result": r.result.value,
                "match_percentage": r.match_percentage,
                "diff_count": r.diff_count,
                "legacy_duration_ms": r.legacy_duration_ms,
                "new_duration_ms": r.new_duration_ms,
                "error": r.error,
            }
            for r in results
        ],
    }


@router.get("/dual-run/{session_id}/statistics")
async def get_dual_run_statistics(session_id: str) -> Dict[str, Any]:
    """
    Get statistics for a dual-run session.

    Returns match rates, performance comparisons, and error summaries.
    """
    if session_id not in dual_run_sessions:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    service = dual_run_sessions[session_id]
    stats = service.get_statistics()

    return {
        "session_id": session_id,
        "total_requests": stats.total_requests,
        "matches": stats.matches,
        "mismatches": stats.mismatches,
        "errors": stats.errors,
        "match_rate": stats.match_rate,
        "avg_legacy_ms": stats.avg_legacy_duration_ms,
        "avg_new_ms": stats.avg_new_duration_ms,
        "performance_ratio": stats.performance_ratio,
    }


@router.delete("/dual-run/{session_id}")
async def close_dual_run_session(session_id: str) -> Dict[str, Any]:
    """Close and clean up a dual-run session."""
    if session_id not in dual_run_sessions:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    del dual_run_sessions[session_id]

    return {
        "session_id": session_id,
        "closed": True,
    }


# ============================================================================
# Summary and Reporting Endpoints
# ============================================================================

@router.get("/summary")
async def get_testing_excellence_summary() -> Dict[str, Any]:
    """
    Get overall testing excellence summary.

    Returns status of all active tests and sessions.
    """
    active_sessions = len(dual_run_sessions)

    return {
        "testing_excellence_version": "1.0.0",
        "week": "134-135",
        "fase": "23",
        "agents": ["Tessa (Test Engineer)", "Vicky (Visual Designer)"],
        "active_dual_run_sessions": active_sessions,
        "available_endpoints": {
            "characterization": [
                "POST /api/testing-excellence/characterization/record-baseline",
                "POST /api/testing-excellence/characterization/compare/{test_id}",
                "POST /api/testing-excellence/characterization/run-test",
                "POST /api/testing-excellence/characterization/batch",
                "GET /api/testing-excellence/characterization/baseline/{test_id}",
                "DELETE /api/testing-excellence/characterization/baseline/{test_id}",
            ],
            "visual_regression": [
                "POST /api/testing-excellence/visual/capture-baseline",
                "POST /api/testing-excellence/visual/compare/{test_id}",
                "POST /api/testing-excellence/visual/batch-compare",
                "PUT /api/testing-excellence/visual/update-baseline/{test_id}",
            ],
            "dual_run": [
                "POST /api/testing-excellence/dual-run/session",
                "POST /api/testing-excellence/dual-run/{session_id}/execute",
                "POST /api/testing-excellence/dual-run/{session_id}/batch",
                "GET /api/testing-excellence/dual-run/{session_id}/statistics",
                "DELETE /api/testing-excellence/dual-run/{session_id}",
            ],
        },
        "documentation": {
            "golden_master": "Record legacy I/O as baseline, compare new system output",
            "visual_regression": "Screenshot comparison with diff highlighting",
            "dual_run": "Parallel execution with shadow mode for safe validation",
        },
    }
