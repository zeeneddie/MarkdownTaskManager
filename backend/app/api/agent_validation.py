"""
Agent Validation API

Week 50 Day 4: API endpoints for agent validation loop

Endpoints:
- POST /api/agent/validate/quick - Quick validation check
- POST /api/agent/validate/loop - Run full validation loop (synchronous)
- GET /api/agent/validate/workflow-types - List supported workflow types

Author: Claude Code (Week 50 Day 4)
Date: 2025-11-24
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
import uuid

from app.database import get_db
from app.services.agent_validation_loop_service import (
    AgentValidationLoopService,
    LoopStatus
)
from app.services.validation_pipeline_service import Language

router = APIRouter(prefix="/api/agent/validate", tags=["Agent Validation"])


# ============================================================================
# SCHEMAS
# ============================================================================

class LanguageEnum(str, Enum):
    python = "python"
    typescript = "typescript"


class QuickValidateRequest(BaseModel):
    """Request for quick validation check"""
    workflow_type: str = Field(..., description="e.g., NEW_FEATURE, BUG, MAINTENANCE")
    code: str = Field(..., description="Code to validate")
    language: LanguageEnum = Field(default=LanguageEnum.python)


class QuickValidateResponse(BaseModel):
    """Response from quick validation"""
    passed: bool
    workflow_type: str
    blocking_count: int
    warning_count: int
    coverage_met: bool
    suggestions: List[Dict[str, Any]]


class ValidationLoopRequest(BaseModel):
    """Request to start validation loop"""
    workflow_type: str
    code: str
    language: LanguageEnum = Field(default=LanguageEnum.python)
    max_iterations: Optional[int] = Field(default=None, ge=1, le=10)
    file_path: Optional[str] = None




# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/quick", response_model=QuickValidateResponse)
async def quick_validate(
    request: QuickValidateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Quick validation check without iteration loop.

    Returns pass/fail status and fix suggestions.
    """
    # Validate workflow type
    valid_types = ["NEW_FEATURE", "MAINTENANCE", "BUG", "QUALITY_AUDIT",
                   "MIGRATION", "REFACTORING", "DOCUMENTATION", "HOTFIX"]

    workflow_type = request.workflow_type.upper()
    if workflow_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid workflow type. Valid: {valid_types}"
        )

    # Convert language enum
    language = Language.PYTHON if request.language == LanguageEnum.python else Language.TYPESCRIPT

    # Run validation
    service = AgentValidationLoopService(db)
    result = await service.get_validation_status(
        workflow_type=workflow_type,
        code=request.code,
        language=language
    )

    return QuickValidateResponse(**result)


class ValidationLoopSyncResponse(BaseModel):
    """Synchronous response from validation loop"""
    task_id: str
    status: str
    workflow_type: str
    total_iterations: int
    max_iterations: int
    passed: bool
    errors_fixed: int
    duration_seconds: float
    suggestions: List[Dict[str, Any]]


@router.post("/loop", response_model=ValidationLoopSyncResponse)
async def run_validation_loop(
    request: ValidationLoopRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run validation loop synchronously.

    The loop will iterate until validation passes or max iterations reached.
    Returns the complete result immediately.
    """
    workflow_type = request.workflow_type.upper()
    task_id = str(uuid.uuid4())[:8]

    # Convert language enum
    language = Language.PYTHON if request.language == LanguageEnum.python else Language.TYPESCRIPT

    # Run validation loop synchronously
    service = AgentValidationLoopService(db)
    result = await service.run_validation_loop(
        workflow_type=workflow_type,
        initial_code=request.code,
        language=language,
        fix_callback=None,
        file_path=request.file_path,
        max_iterations_override=request.max_iterations
    )

    # Get suggestions from final validation if available
    suggestions = []
    if result.final_validation:
        for phase_result in result.final_validation.phases:
            if not phase_result.passed and phase_result.errors:
                for error in phase_result.errors:
                    suggestions.append({
                        "phase": phase_result.phase.value,
                        "message": error.message,
                        "severity": error.severity,
                        "file": error.file,
                        "line": error.line
                    })

    return ValidationLoopSyncResponse(
        task_id=task_id,
        status=result.status.value,
        workflow_type=workflow_type,
        total_iterations=result.total_iterations,
        max_iterations=result.max_iterations,
        passed=result.status == LoopStatus.PASSED,
        errors_fixed=result.total_errors_fixed,
        duration_seconds=result.duration_seconds,
        suggestions=suggestions
    )


@router.get("/workflow-types")
async def list_workflow_types():
    """
    List all supported workflow types for validation.
    """
    return {
        "workflow_types": [
            {"type": "NEW_FEATURE", "description": "New feature development"},
            {"type": "MAINTENANCE", "description": "Code maintenance and updates"},
            {"type": "BUG", "description": "Bug fixes"},
            {"type": "QUALITY_AUDIT", "description": "Quality audit and review"},
            {"type": "MIGRATION", "description": "Code or data migration"},
            {"type": "REFACTORING", "description": "Code refactoring"},
            {"type": "DOCUMENTATION", "description": "Documentation updates"},
            {"type": "HOTFIX", "description": "Quick critical fixes"}
        ]
    }
