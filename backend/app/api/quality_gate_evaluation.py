"""
Quality Gate Evaluation API

Week 50: API endpoints for evaluating quality gates

Endpoints:
- GET /api/quality/gate/{workflow_type}/config - Get validation config
- POST /api/quality/gate/{workflow_type}/evaluate - Evaluate gate pass/fail
- GET /api/quality/gate/status - Get all workflow gate statuses

Author: Claude Code (Week 50 Day 1)
Date: 2025-11-24
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.services.quality_gate_integration_service import (
    QualityGateIntegrationService,
    QualityGateResult,
    WORK_TYPE_PHASES
)
from app.services.validation_pipeline_service import ValidationPhase


router = APIRouter(prefix="/api/quality/gate", tags=["Quality Gate Evaluation"])


# ============================================================================
# SCHEMAS
# ============================================================================

class ValidationConfigResponse(BaseModel):
    """Validation config for a workflow"""
    workflow_type: str
    phases: List[str]
    max_iterations: int
    stop_on_first_failure: bool
    required_coverage: Optional[int]
    regression_test_required: bool
    blocking_severities: List[str]
    e2e_required: bool


class ValidationErrorInput(BaseModel):
    """Input for a validation error"""
    phase: str
    message: str
    severity: str = "error"
    file: Optional[str] = None
    line: Optional[int] = None


class EvaluateGateRequest(BaseModel):
    """Request to evaluate a quality gate"""
    errors: List[ValidationErrorInput] = []
    coverage_percent: Optional[float] = None
    phases_passed: List[str] = []


class GateEvaluationResponse(BaseModel):
    """Response from gate evaluation"""
    passed: bool
    workflow_type: str
    blocking_issues: List[Dict[str, Any]]
    blocking_count: int
    warnings: List[Dict[str, Any]]
    warning_count: int
    coverage_met: bool
    coverage_actual: Optional[float]
    coverage_required: int


class WorkflowGateStatus(BaseModel):
    """Status of a single workflow's gate"""
    workflow_type: str
    configured: bool
    blocking_severities: List[str]
    required_coverage: int
    e2e_required: bool
    regression_required: bool
    phases: List[str]


class AllGatesStatusResponse(BaseModel):
    """Status of all workflow gates"""
    active_config: bool
    config_name: Optional[str]
    workflows: List[WorkflowGateStatus]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/{workflow_type}/config", response_model=ValidationConfigResponse)
async def get_workflow_validation_config(
    workflow_type: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the validation configuration for a specific workflow type.

    Returns phases, iterations, coverage requirements, etc.
    """
    workflow_type = workflow_type.upper()

    if workflow_type not in WORK_TYPE_PHASES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown workflow type: {workflow_type}. Valid types: {list(WORK_TYPE_PHASES.keys())}"
        )

    service = QualityGateIntegrationService(db)
    config = await service.get_validation_config(workflow_type)
    rules = await service.get_workflow_rules(workflow_type)

    return ValidationConfigResponse(
        workflow_type=workflow_type,
        phases=[p.value for p in config.phases],
        max_iterations=config.max_iterations,
        stop_on_first_failure=config.stop_on_first_failure,
        required_coverage=config.required_coverage,
        regression_test_required=config.regression_test_required,
        blocking_severities=rules.blocking_severities if rules else ["critical"],
        e2e_required=rules.e2e_required if rules else False
    )


@router.post("/{workflow_type}/evaluate", response_model=GateEvaluationResponse)
async def evaluate_quality_gate(
    workflow_type: str,
    request: EvaluateGateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluate if a validation result passes the quality gate.

    Provide:
    - errors: List of validation errors with severity
    - coverage_percent: Test coverage percentage (optional)
    - phases_passed: List of phase names that passed

    Returns pass/fail status with blocking issues.
    """
    workflow_type = workflow_type.upper()

    if workflow_type not in WORK_TYPE_PHASES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown workflow type: {workflow_type}"
        )

    service = QualityGateIntegrationService(db)
    rules = await service.get_workflow_rules(workflow_type)

    # Build blocking issues and warnings from input
    blocking_severities = set(rules.blocking_severities if rules else ["critical"])
    blocking_issues = []
    warnings = []

    for error in request.errors:
        error_dict = {
            "phase": error.phase,
            "message": error.message,
            "severity": error.severity,
            "file": error.file,
            "line": error.line
        }
        if error.severity in blocking_severities:
            blocking_issues.append(error_dict)
        else:
            warnings.append(error_dict)

    # Check coverage
    required_coverage = rules.required_coverage if rules else 80
    coverage_met = True

    if request.coverage_percent is not None and required_coverage > 0:
        if request.coverage_percent < required_coverage:
            coverage_met = False
            blocking_issues.append({
                "phase": "coverage",
                "message": f"Coverage {request.coverage_percent:.1f}% below required {required_coverage}%",
                "severity": "critical",
                "file": None,
                "line": None
            })

    # Check E2E requirement
    e2e_required = rules.e2e_required if rules else False
    if e2e_required and "e2e_tests" not in request.phases_passed:
        blocking_issues.append({
            "phase": "e2e",
            "message": "E2E tests required but did not pass",
            "severity": "critical",
            "file": None,
            "line": None
        })

    passed = len(blocking_issues) == 0

    return GateEvaluationResponse(
        passed=passed,
        workflow_type=workflow_type,
        blocking_issues=blocking_issues,
        blocking_count=len(blocking_issues),
        warnings=warnings,
        warning_count=len(warnings),
        coverage_met=coverage_met,
        coverage_actual=request.coverage_percent,
        coverage_required=required_coverage
    )


@router.get("/status", response_model=AllGatesStatusResponse)
async def get_all_gates_status(db: AsyncSession = Depends(get_db)):
    """
    Get status of all workflow quality gates.

    Shows which workflows have configured gates and their settings.
    """
    service = QualityGateIntegrationService(db)
    config = await service.get_active_config()

    workflows = []
    for workflow_type, phases in WORK_TYPE_PHASES.items():
        rules = await service.get_workflow_rules(workflow_type)

        workflows.append(WorkflowGateStatus(
            workflow_type=workflow_type,
            configured=rules is not None,
            blocking_severities=rules.blocking_severities if rules else ["critical"],
            required_coverage=rules.required_coverage if rules else 80,
            e2e_required=rules.e2e_required if rules else False,
            regression_required=rules.regression_required if rules else False,
            phases=[p.value for p in phases]
        ))

    return AllGatesStatusResponse(
        active_config=config is not None,
        config_name=config.name if config else None,
        workflows=workflows
    )


@router.get("/workflow-types")
async def get_workflow_types():
    """
    Get list of all supported workflow types with their default phases.
    """
    return {
        "workflow_types": [
            {
                "type": wt,
                "phases": [p.value for p in phases],
                "description": _get_workflow_description(wt)
            }
            for wt, phases in WORK_TYPE_PHASES.items()
        ]
    }


def _get_workflow_description(workflow_type: str) -> str:
    """Get description for a workflow type"""
    descriptions = {
        "NEW_FEATURE": "New feature development - full validation",
        "MAINTENANCE": "Code maintenance and tech debt",
        "BUG": "Bug fixes - requires regression tests",
        "QUALITY_AUDIT": "Quality audits and code review",
        "MIGRATION": "System migrations - E2E critical",
        "REFACTORING": "Code refactoring - full lint + tests",
        "DOCUMENTATION": "Documentation changes - lint only",
        "HOTFIX": "Emergency fixes - minimal validation"
    }
    return descriptions.get(workflow_type, "Unknown workflow type")
