"""
Estimation History API Endpoints

Provides REST API for estimation history and ML training data:
- View estimation history
- Record actual results
- Get ML training data
- Manage estimation projects

Author: Claude Code (Week 15 Day 5)
Date: 2025-11-21
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.estimation_history_service import EstimationHistoryService
from app.models.estimation_history import TechStack


router = APIRouter(prefix="/estimation/history", tags=["estimation-history"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ProjectCreateRequest(BaseModel):
    """Request to create an estimation project"""
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    external_id: Optional[str] = Field(None, description="External ID (Jira, GitHub, etc.)")
    tech_stack: Optional[str] = Field(None, description="Technology stack")
    team_size: Optional[int] = Field(None, ge=1, description="Team size")
    experience_level: Optional[float] = Field(None, ge=1.0, le=5.0, description="Average experience (1-5)")
    domain_complexity: Optional[float] = Field(None, ge=1.0, le=5.0, description="Domain complexity (1-5)")
    has_legacy_integration: bool = Field(False, description="Has legacy system integration")
    has_external_apis: bool = Field(False, description="Uses external APIs")
    is_greenfield: bool = Field(True, description="Is greenfield project")


class ProjectResponse(BaseModel):
    """Response with project details"""
    id: int
    name: str
    description: Optional[str]
    external_id: Optional[str]
    tech_stack: Optional[str]
    team_size: Optional[int]
    experience_level: Optional[float]
    domain_complexity: Optional[float]
    created_at: str


class RecordFPActualsRequest(BaseModel):
    """Request to record Function Point actuals"""
    actual_effort_hours: Optional[float] = Field(None, ge=0, description="Total hours spent")
    actual_person_days: Optional[float] = Field(None, ge=0, description="Person-days spent")
    actual_duration_days: Optional[int] = Field(None, ge=0, description="Calendar days elapsed")
    actual_team_size: Optional[int] = Field(None, ge=1, description="Team size used")
    actual_completion_date: Optional[datetime] = Field(None, description="Completion date")


class RecordSPActualsRequest(BaseModel):
    """Request to record Story Point actuals"""
    actual_effort_hours: Optional[float] = Field(None, ge=0, description="Total hours spent")
    actual_person_days: Optional[float] = Field(None, ge=0, description="Person-days spent")
    actual_duration_days: Optional[int] = Field(None, ge=0, description="Calendar days elapsed")
    actual_story_points: Optional[int] = Field(None, ge=1, le=21, description="Retrospective SP assessment")
    actual_completion_date: Optional[datetime] = Field(None, description="Completion date")


class EstimationStatistics(BaseModel):
    """Overall estimation statistics"""
    function_points: Dict[str, Any]
    story_points: Dict[str, Any]
    projects: int
    ml_ready: bool


# ============================================================================
# PROJECT ENDPOINTS
# ============================================================================

@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create or get an estimation project.

    Projects group related estimations for ML correlation and tracking.

    **Example:**
    ```json
    {
      "name": "E-Commerce Platform v2",
      "description": "Complete rewrite of e-commerce backend",
      "tech_stack": "fullstack",
      "team_size": 5,
      "experience_level": 3.5,
      "domain_complexity": 4.0,
      "is_greenfield": false
    }
    ```
    """
    try:
        service = EstimationHistoryService(db)

        # Validate tech_stack if provided (model uses String, not Enum)
        tech_stack_value = None
        if request.tech_stack:
            # Validate against known enum values
            valid_stacks = [ts.value for ts in TechStack]
            if request.tech_stack in valid_stacks:
                tech_stack_value = request.tech_stack

        project = await service.get_or_create_project(
            name=request.name,
            description=request.description,
            external_id=request.external_id,
            tech_stack=tech_stack_value,
            team_size=request.team_size,
            experience_level=request.experience_level,
            domain_complexity=request.domain_complexity,
            has_legacy_integration=request.has_legacy_integration,
            has_external_apis=request.has_external_apis,
            is_greenfield=request.is_greenfield
        )

        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            external_id=project.external_id,
            tech_stack=project.tech_stack,  # Already a string
            team_size=project.team_size,
            experience_level=project.experience_level,
            domain_complexity=project.domain_complexity,
            created_at=project.created_at.isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RECORD ACTUALS ENDPOINTS
# ============================================================================

@router.put("/function-points/{estimate_id}/actuals")
async def record_fp_actuals(
    estimate_id: int,
    request: RecordFPActualsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Record actual results for a Function Point estimate.

    This data is essential for ML model training. After completing work
    on an estimated project, record actual hours/days spent.

    **Example:**
    ```json
    {
      "actual_effort_hours": 64,
      "actual_person_days": 8,
      "actual_duration_days": 10,
      "actual_team_size": 2,
      "actual_completion_date": "2025-02-15T17:00:00"
    }
    ```
    """
    try:
        service = EstimationHistoryService(db)

        estimate = await service.record_fp_actuals(
            estimate_id=estimate_id,
            actual_effort_hours=request.actual_effort_hours,
            actual_person_days=request.actual_person_days,
            actual_duration_days=request.actual_duration_days,
            actual_team_size=request.actual_team_size,
            actual_completion_date=request.actual_completion_date
        )

        if not estimate:
            raise HTTPException(status_code=404, detail=f"Estimate {estimate_id} not found")

        return {
            "success": True,
            "estimate_id": estimate_id,
            "estimation_accuracy": estimate.estimation_accuracy,
            "message": "Actuals recorded successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/story-points/{estimate_id}/actuals")
async def record_sp_actuals(
    estimate_id: int,
    request: RecordSPActualsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Record actual results for a Story Point estimate.

    This data is essential for ML model training and velocity tracking.

    **Example:**
    ```json
    {
      "actual_effort_hours": 16,
      "actual_person_days": 2,
      "actual_duration_days": 3,
      "actual_story_points": 8,
      "actual_completion_date": "2025-02-15T17:00:00"
    }
    ```
    """
    try:
        service = EstimationHistoryService(db)

        estimate = await service.record_sp_actuals(
            estimate_id=estimate_id,
            actual_effort_hours=request.actual_effort_hours,
            actual_person_days=request.actual_person_days,
            actual_duration_days=request.actual_duration_days,
            actual_story_points=request.actual_story_points,
            actual_completion_date=request.actual_completion_date
        )

        if not estimate:
            raise HTTPException(status_code=404, detail=f"Estimate {estimate_id} not found")

        return {
            "success": True,
            "estimate_id": estimate_id,
            "velocity_factor": estimate.velocity_factor,
            "estimation_accuracy": estimate.estimation_accuracy,
            "message": "Actuals recorded successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HISTORY & STATISTICS ENDPOINTS
# ============================================================================

@router.get("/statistics", response_model=EstimationStatistics)
async def get_statistics(db: AsyncSession = Depends(get_db)):
    """
    Get overall estimation statistics.

    Returns counts and ML readiness status.
    """
    try:
        service = EstimationHistoryService(db)
        stats = await service.get_estimation_statistics()
        return EstimationStatistics(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_estimates(
    limit: int = Query(20, ge=1, le=100, description="Number of records"),
    estimation_type: Optional[str] = Query(None, description="function_points or story_points"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent estimation records.

    **Query Parameters:**
    - `limit`: Maximum records to return (default: 20)
    - `estimation_type`: Filter by type (function_points, story_points)
    """
    try:
        service = EstimationHistoryService(db)
        return await service.get_recent_estimates(
            limit=limit,
            estimation_type=estimation_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ML TRAINING DATA ENDPOINTS
# ============================================================================

@router.get("/training-data/function-points")
async def get_fp_training_data(
    min_samples: int = Query(10, ge=1, description="Minimum samples required"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get Function Point training data for ML model.

    Returns feature vectors with actual results for supervised learning.

    **Features included:**
    - Component counts (ILF, EIF, EI, EO, EQ)
    - Complexity distribution
    - Unadjusted/Adjusted FP
    - Project metadata (if available)

    **Target variables:**
    - actual_hours
    - actual_days
    """
    try:
        service = EstimationHistoryService(db)
        data = await service.get_fp_training_data(min_samples=min_samples)

        if not data:
            return {
                "status": "insufficient_data",
                "message": f"Need at least {min_samples} estimates with actuals",
                "current_count": 0,
                "data": []
            }

        return {
            "status": "ready",
            "sample_count": len(data),
            "features": list(data[0].keys()) if data else [],
            "data": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training-data/story-points")
async def get_sp_training_data(
    min_samples: int = Query(10, ge=1, description="Minimum samples required"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get Story Point training data for ML model.

    Returns feature vectors with actual results for supervised learning.

    **Features included:**
    - Complexity factors (technical, business, risk, uncertainty, dependencies)
    - Story points
    - PERT estimates

    **Target variables:**
    - actual_hours
    - actual_days
    - actual_sp (retrospective)
    - velocity_factor
    """
    try:
        service = EstimationHistoryService(db)
        data = await service.get_sp_training_data(min_samples=min_samples)

        if not data:
            return {
                "status": "insufficient_data",
                "message": f"Need at least {min_samples} estimates with actuals",
                "current_count": 0,
                "data": []
            }

        return {
            "status": "ready",
            "sample_count": len(data),
            "features": list(data[0].keys()) if data else [],
            "data": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TECH STACK OPTIONS
# ============================================================================

@router.get("/tech-stacks")
async def get_tech_stack_options():
    """Get available tech stack options for project creation"""
    return {
        "tech_stacks": [
            {"value": ts.value, "label": ts.name.replace("_", " ").title()}
            for ts in TechStack
        ]
    }
