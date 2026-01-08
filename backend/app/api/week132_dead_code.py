"""
Week 132-133: Dead Code & Runtime Analysis API

API endpoints for dead code detection, runtime analysis, and code coverage.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.dead_code_detector_service import DeadCodeDetectorService
from app.services.runtime_analysis_service import RuntimeAnalysisService, APMConfig
from app.services.code_coverage_analyzer_service import (
    CodeCoverageAnalyzerService,
    CoverageThresholds,
)
from app.models.week132_dead_code import (
    AnalysisType,
    APMProvider,
    CoverageSource,
    RemovalRisk,
)

router = APIRouter(prefix="/api/dead-code", tags=["dead-code-analysis"])


# ============================================================================
# Request/Response Models
# ============================================================================

class DeadCodeAnalysisRequest(BaseModel):
    """Request for dead code analysis."""
    project_path: str = Field(..., description="Path to the project")
    include_languages: Optional[List[str]] = Field(
        None, description="Languages to analyze (None = auto-detect)"
    )
    exclude_patterns: Optional[List[str]] = Field(
        None, description="Glob patterns to exclude"
    )
    include_tests: bool = Field(False, description="Include test files in analysis")
    confidence_threshold: float = Field(
        0.5, ge=0.0, le=1.0, description="Minimum confidence to report"
    )


class RuntimeAnalysisRequest(BaseModel):
    """Request for runtime analysis."""
    project_path: str = Field(..., description="Path to the project")
    apm_provider: Optional[str] = Field(None, description="APM provider name")
    api_key: Optional[str] = Field(None, description="APM API key")
    api_url: Optional[str] = Field(None, description="APM API URL")
    analysis_days: int = Field(30, ge=1, le=365, description="Days to analyze")
    include_traces: bool = Field(True, description="Include execution traces")


class CoverageAnalysisRequest(BaseModel):
    """Request for coverage analysis."""
    project_path: str = Field(..., description="Path to the project")
    coverage_source: Optional[str] = Field(None, description="Coverage tool source")
    include_file_details: bool = Field(True, description="Include per-file details")
    line_threshold: float = Field(80.0, ge=0, le=100, description="Line coverage threshold")
    branch_threshold: float = Field(70.0, ge=0, le=100, description="Branch coverage threshold")
    function_threshold: float = Field(80.0, ge=0, le=100, description="Function coverage threshold")


class CombinedAnalysisRequest(BaseModel):
    """Request for combined dead code analysis."""
    project_path: str = Field(..., description="Path to the project")
    include_static: bool = Field(True, description="Include static analysis")
    include_runtime: bool = Field(True, description="Include runtime analysis")
    include_coverage: bool = Field(True, description="Include coverage analysis")
    confidence_threshold: float = Field(0.5, description="Minimum confidence")


# ============================================================================
# Service Instances
# ============================================================================

dead_code_service = DeadCodeDetectorService()
runtime_service = RuntimeAnalysisService()
coverage_service = CodeCoverageAnalyzerService()


# ============================================================================
# Dead Code Detection Endpoints
# ============================================================================

@router.post("/detect")
async def detect_dead_code(request: DeadCodeAnalysisRequest) -> Dict[str, Any]:
    """
    Detect dead code in a project using static analysis.

    Returns unused functions, classes, imports, variables, etc.
    """
    project_path = Path(request.project_path)

    result = dead_code_service.detect(
        project_path=project_path,
        include_languages=request.include_languages,
        exclude_patterns=request.exclude_patterns,
        include_tests=request.include_tests,
        confidence_threshold=request.confidence_threshold,
    )

    return result.to_dict()


@router.get("/detect/{project_id}")
async def get_dead_code_analysis(project_id: str) -> Dict[str, Any]:
    """Get stored dead code analysis results."""
    # TODO: Implement database retrieval
    return {
        "project_id": project_id,
        "message": "Database retrieval not yet implemented",
        "hint": "Use POST /api/dead-code/detect to run analysis"
    }


@router.post("/detect/cleanup-script")
async def generate_cleanup_script(
    request: DeadCodeAnalysisRequest,
    safe_only: bool = Query(True, description="Only include safe removals")
) -> Dict[str, Any]:
    """
    Generate a cleanup script for removing dead code.

    Returns shell script content that can be reviewed and executed.
    """
    project_path = Path(request.project_path)

    result = dead_code_service.detect(
        project_path=project_path,
        include_languages=request.include_languages,
        exclude_patterns=request.exclude_patterns,
        include_tests=request.include_tests,
        confidence_threshold=request.confidence_threshold,
    )

    script = dead_code_service.get_cleanup_script(result, safe_only=safe_only)

    return {
        "success": result.success,
        "items_count": len(result.items),
        "safe_removal_count": result.safe_removal_count,
        "script": script,
    }


# ============================================================================
# Runtime Analysis Endpoints
# ============================================================================

@router.post("/runtime/analyze")
async def analyze_runtime(request: RuntimeAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze runtime data for dead code detection.

    Uses APM data or local coverage/logs to identify unused code.
    """
    project_path = Path(request.project_path)

    # Build APM config if provider specified
    apm_config = None
    if request.apm_provider:
        try:
            provider = APMProvider(request.apm_provider.lower())
        except ValueError:
            provider = APMProvider.CUSTOM

        apm_config = APMConfig(
            provider=provider,
            api_key=request.api_key,
            api_url=request.api_url,
        )

    result = runtime_service.analyze(
        project_path=project_path,
        config=apm_config,
        analysis_days=request.analysis_days,
        include_traces=request.include_traces,
    )

    return result.to_dict()


@router.get("/runtime/{project_id}")
async def get_runtime_analysis(project_id: str) -> Dict[str, Any]:
    """Get stored runtime analysis results."""
    return {
        "project_id": project_id,
        "message": "Database retrieval not yet implemented",
    }


@router.post("/runtime/endpoint-coverage")
async def analyze_endpoint_coverage(
    project_path: str,
    endpoints: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Compare defined endpoints against actual usage.

    Requires list of defined endpoints: [{path, method, handler}]
    """
    path = Path(project_path)

    result = runtime_service.analyze_endpoint_coverage(
        project_path=path,
        defined_endpoints=endpoints,
    )

    return result


# ============================================================================
# Coverage Analysis Endpoints
# ============================================================================

@router.post("/coverage/analyze")
async def analyze_coverage(request: CoverageAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze code coverage from test reports.

    Supports Jest, pytest-cov, Coverlet, JaCoCo, LCOV formats.
    """
    project_path = Path(request.project_path)

    # Parse coverage source
    coverage_source = None
    if request.coverage_source:
        try:
            coverage_source = CoverageSource(request.coverage_source.lower())
        except ValueError:
            pass

    # Set thresholds
    thresholds = CoverageThresholds(
        line_coverage=request.line_threshold,
        branch_coverage=request.branch_threshold,
        function_coverage=request.function_threshold,
    )

    service = CodeCoverageAnalyzerService(thresholds=thresholds)

    result = service.analyze(
        project_path=project_path,
        coverage_source=coverage_source,
        include_file_details=request.include_file_details,
    )

    # Add threshold check
    response = result.to_dict()
    response["threshold_check"] = service.check_thresholds(result)

    return response


@router.get("/coverage/{project_id}")
async def get_coverage_analysis(project_id: str) -> Dict[str, Any]:
    """Get stored coverage analysis results."""
    return {
        "project_id": project_id,
        "message": "Database retrieval not yet implemented",
    }


@router.post("/coverage/check-thresholds")
async def check_coverage_thresholds(request: CoverageAnalysisRequest) -> Dict[str, Any]:
    """
    Check if coverage meets specified thresholds.

    Returns pass/fail status suitable for CI/CD gates.
    """
    project_path = Path(request.project_path)

    coverage_source = None
    if request.coverage_source:
        try:
            coverage_source = CoverageSource(request.coverage_source.lower())
        except ValueError:
            pass

    thresholds = CoverageThresholds(
        line_coverage=request.line_threshold,
        branch_coverage=request.branch_threshold,
        function_coverage=request.function_threshold,
    )

    service = CodeCoverageAnalyzerService(thresholds=thresholds)

    result = service.analyze(
        project_path=project_path,
        coverage_source=coverage_source,
        include_file_details=False,  # Skip details for threshold check
    )

    check_result = service.check_thresholds(result)

    return {
        "project_path": str(project_path),
        **check_result,
        "coverage": {
            "line": result.line_coverage_percentage,
            "branch": result.branch_coverage_percentage,
            "function": result.function_coverage_percentage,
        },
    }


# ============================================================================
# Combined Analysis Endpoints
# ============================================================================

@router.post("/analyze/combined")
async def analyze_combined(request: CombinedAnalysisRequest) -> Dict[str, Any]:
    """
    Run combined dead code analysis (static + runtime + coverage).

    Provides comprehensive dead code report with cross-validation.
    """
    project_path = Path(request.project_path)
    results: Dict[str, Any] = {
        "project_path": str(project_path),
        "analysis_id": str(uuid4()),
    }

    errors: List[str] = []

    # Static analysis
    if request.include_static:
        static_result = dead_code_service.detect(
            project_path=project_path,
            confidence_threshold=request.confidence_threshold,
        )
        results["static_analysis"] = static_result.to_dict()
        if not static_result.success:
            errors.extend(static_result.errors)

    # Runtime analysis
    if request.include_runtime:
        runtime_result = runtime_service.analyze(project_path=project_path)
        results["runtime_analysis"] = runtime_result.to_dict()
        if not runtime_result.success:
            errors.extend(runtime_result.errors)

    # Coverage analysis
    if request.include_coverage:
        coverage_result = coverage_service.analyze(project_path=project_path)
        results["coverage_analysis"] = coverage_result.to_dict()
        if not coverage_result.success:
            errors.extend(coverage_result.errors)

    # Cross-validate findings
    if request.include_static and request.include_runtime:
        results["cross_validation"] = _cross_validate_findings(
            results.get("static_analysis", {}),
            results.get("runtime_analysis", {}),
        )

    # Summary
    results["summary"] = _generate_combined_summary(results)
    results["errors"] = errors
    results["success"] = len(errors) == 0

    return results


@router.get("/summary/{project_id}")
async def get_analysis_summary(project_id: str) -> Dict[str, Any]:
    """Get combined analysis summary for a project."""
    return {
        "project_id": project_id,
        "message": "Database retrieval not yet implemented",
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _cross_validate_findings(
    static: Dict[str, Any],
    runtime: Dict[str, Any],
) -> Dict[str, Any]:
    """Cross-validate static and runtime findings."""
    static_items = {item["name"]: item for item in static.get("items", [])}
    runtime_cold = {path.get("function", ""): path for path in runtime.get("cold_paths", [])}

    # Find items detected by both
    confirmed_dead = []
    for name, item in static_items.items():
        if name in runtime_cold:
            item["confirmed_by_runtime"] = True
            item["confidence"] = min(1.0, item.get("confidence", 0.7) + 0.2)
            confirmed_dead.append(item)

    return {
        "confirmed_dead_code_count": len(confirmed_dead),
        "static_only_count": len(static_items) - len(confirmed_dead),
        "runtime_only_count": len(runtime_cold) - len(confirmed_dead),
        "confirmed_items": confirmed_dead[:10],  # Top 10
    }


def _generate_combined_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary from combined analysis."""
    summary = {
        "total_dead_code_items": 0,
        "safe_removal_count": 0,
        "estimated_cleanup_hours": 0.0,
        "coverage_percentage": 0.0,
        "recommendations": [],
    }

    if "static_analysis" in results:
        static = results["static_analysis"]
        summary["total_dead_code_items"] = static.get("dead_code_count", 0)
        summary["safe_removal_count"] = static.get("safe_removal_count", 0)
        summary["estimated_cleanup_hours"] = static.get("estimated_cleanup_hours", 0.0)
        summary["recommendations"].extend(static.get("recommendations", []))

    if "coverage_analysis" in results:
        coverage = results["coverage_analysis"]
        summary["coverage_percentage"] = coverage.get("line_coverage_percentage", 0.0)

    if "cross_validation" in results:
        cv = results["cross_validation"]
        confirmed = cv.get("confirmed_dead_code_count", 0)
        if confirmed > 0:
            summary["recommendations"].append(
                f"{confirmed} dead code items confirmed by both static and runtime analysis"
            )

    return summary
