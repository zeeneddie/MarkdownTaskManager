"""
Project Workflows API

Week 69: Gestandaardiseerde Project Workflows
API endpoints for:
- Workflow 1: Project Analysis (standalone health check)
- Workflow 2: Migration Planning (requires Workflow 1)
- Workflow 3: Full Assessment (combined workflow)

Author: Claude Code (Week 69)
Date: 2025-12-15
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.project_assessment import ProjectAssessment, MigrationPlan, AssessmentPhase
from app.services.project_assessment_orchestrator import (
    ProjectAssessmentOrchestrator,
    run_project_assessment,
    VerboseConfig
)
from app.services.migration_planning_orchestrator import (
    MigrationPlanningOrchestrator,
    run_migration_planning,
    TARGET_TECHNOLOGIES,
    MIGRATION_STRATEGIES
)

router = APIRouter(prefix="/api/project-workflows", tags=["Project Workflows"])


# ============ Request/Response Models ============

class StartAssessmentRequest(BaseModel):
    """Request to start Workflow 1: Project Analysis"""
    project_name: str = Field(..., description="Name of the project")
    directory_path: str = Field(..., description="Path to project source code")
    application_id: Optional[int] = Field(None, description="Optional ApplicationRegistry ID")
    verbose: bool = Field(False, description="Enable verbose logging for step-by-step tracking")


class StartPlanningRequest(BaseModel):
    """Request to start Workflow 2: Migration Planning"""
    assessment_id: str = Field(..., description="UUID of completed assessment")
    target_technology: str = Field(..., description="Target technology stack")
    target_database: Optional[str] = Field(None, description="Target database (optional)")
    target_frontend: Optional[str] = Field(None, description="Target frontend (optional)")


class FullWorkflowRequest(BaseModel):
    """Request to start Workflow 3: Full Assessment"""
    project_name: str = Field(..., description="Name of the project")
    directory_path: str = Field(..., description="Path to project source code")
    target_technology: str = Field(..., description="Target technology stack")
    target_database: Optional[str] = Field(None, description="Target database")
    target_frontend: Optional[str] = Field(None, description="Target frontend")
    application_id: Optional[int] = Field(None, description="Optional ApplicationRegistry ID")


class ReviewPlanRequest(BaseModel):
    """Request to approve/reject a migration plan"""
    reviewer: str = Field(..., description="Name of the reviewer")
    notes: Optional[str] = Field(None, description="Review notes")


class AssessmentSummary(BaseModel):
    """Summary of a project assessment"""
    id: str
    project_name: str
    primary_stack: Optional[str]
    overall_health_score: Optional[int]
    overall_grade: Optional[str]
    security_grade: Optional[str]
    quality_grade: Optional[str]
    status: str
    assessment_date: Optional[datetime]


class PlanSummary(BaseModel):
    """Summary of a migration plan"""
    id: str
    assessment_id: str
    target_technology: str
    adjusted_fp: Optional[int]
    total_weeks: Optional[int]
    migration_strategy: Optional[str]
    status: str
    created_at: Optional[datetime]


# ============ Workflow 1: Project Analysis ============

@router.post("/analysis/start", response_model=dict)
async def start_project_analysis(
    request: StartAssessmentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Start Workflow 1: Project Analysis

    Creates a new project assessment and starts the analysis process
    in the background.

    Set verbose=true to enable step-by-step logging (logs are written to server log).

    Phases executed:
    1. Registration (ApplicationRegistry scan)
    2. AS-IS Architecture (Miguel)
    3. Code Analysis (CodeRAG)
    4. Security Analysis (Quinn)
    5. Quality Analysis (Quinn)
    6. Requirements Extraction (Peter)
    7. Health Report (Diana)
    """
    orchestrator = ProjectAssessmentOrchestrator(db)

    try:
        assessment = await orchestrator.start_assessment(
            project_name=request.project_name,
            directory_path=request.directory_path,
            application_id=request.application_id
        )

        # Run assessment in background (with verbose if requested)
        background_tasks.add_task(
            _run_assessment_background,
            str(assessment.id),
            request.project_name,
            request.directory_path,
            request.application_id,
            request.verbose
        )

        return {
            "success": True,
            "assessment_id": str(assessment.id),
            "status": "running",
            "verbose": request.verbose,
            "message": "Project analysis started. Use /analysis/{id}/status to check progress."
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def _run_assessment_background(
    assessment_id: str,
    project_name: str,
    directory_path: str,
    application_id: Optional[int],
    verbose: bool = False
):
    """Background task to run assessment"""
    from app.database import async_session_maker

    async with async_session_maker() as db:
        verbose_config = VerboseConfig(enabled=verbose) if verbose else None
        orchestrator = ProjectAssessmentOrchestrator(db, verbose=verbose_config)
        try:
            await orchestrator.run_assessment(UUID(assessment_id))
        except Exception as e:
            print(f"Assessment failed: {e}")


@router.post("/analysis/run-sync", response_model=dict)
async def run_project_analysis_sync(
    request: StartAssessmentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run Workflow 1 synchronously (blocks until complete)

    For smaller projects or when immediate results are needed.

    Set verbose=true to get step-by-step execution logs in the response.
    """
    try:
        # Create orchestrator with verbose mode if requested
        verbose_config = VerboseConfig(enabled=request.verbose) if request.verbose else None
        orchestrator = ProjectAssessmentOrchestrator(db, verbose=verbose_config)

        # Start and run assessment
        assessment = await orchestrator.start_assessment(
            project_name=request.project_name,
            directory_path=request.directory_path,
            application_id=request.application_id
        )
        assessment = await orchestrator.run_assessment(assessment.id)

        result = {
            "success": True,
            "assessment_id": str(assessment.id),
            "status": assessment.status,
            "overall_grade": assessment.overall_grade,
            "overall_health_score": assessment.overall_health_score,
            "architecture_score": assessment.architecture_score,
            "security_grade": assessment.security_grade,
            "quality_grade": assessment.quality_grade,
            "recommendations_count": len(assessment.recommendations or []),
            "blockers_count": len(assessment.blockers or [])
        }

        # Include verbose logs if requested
        if request.verbose:
            result["verbose_logs"] = orchestrator.get_verbose_logs()

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{assessment_id}/status", response_model=dict)
async def get_assessment_status(
    assessment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get current status of a project assessment"""
    orchestrator = ProjectAssessmentOrchestrator(db)
    status = await orchestrator.get_assessment_status(UUID(assessment_id))

    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])

    return status


@router.get("/analysis/{assessment_id}", response_model=dict)
async def get_assessment_details(
    assessment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get full details of a completed assessment"""
    result = await db.execute(
        select(ProjectAssessment).where(ProjectAssessment.id == UUID(assessment_id))
    )
    assessment = result.scalar_one_or_none()

    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    return assessment.to_dict()


@router.get("/analysis", response_model=List[AssessmentSummary])
async def list_assessments(
    status: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """List all project assessments"""
    query = select(ProjectAssessment).order_by(desc(ProjectAssessment.created_at)).limit(limit)

    if status:
        query = query.where(ProjectAssessment.status == status)

    result = await db.execute(query)
    assessments = result.scalars().all()

    return [
        AssessmentSummary(
            id=str(a.id),
            project_name=a.project_name,
            primary_stack=a.primary_stack,
            overall_health_score=a.overall_health_score,
            overall_grade=a.overall_grade,
            security_grade=a.security_grade,
            quality_grade=a.quality_grade,
            status=a.status,
            assessment_date=a.assessment_date
        )
        for a in assessments
    ]


@router.get("/analysis/{assessment_id}/report", response_model=dict)
async def get_assessment_report(
    assessment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the health report for an assessment"""
    result = await db.execute(
        select(ProjectAssessment).where(ProjectAssessment.id == UUID(assessment_id))
    )
    assessment = result.scalar_one_or_none()

    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if assessment.status != "completed":
        raise HTTPException(status_code=400, detail="Assessment not yet completed")

    return {
        "assessment_id": str(assessment.id),
        "project_name": assessment.project_name,
        "report": assessment.health_summary,
        "recommendations": assessment.recommendations,
        "blockers": assessment.blockers
    }


# ============ Workflow 2: Migration Planning ============

@router.post("/planning/start", response_model=dict)
async def start_migration_planning(
    request: StartPlanningRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Start Workflow 2: Migration Planning

    Requires a completed assessment from Workflow 1.

    Phases executed:
    7. FP Estimation (Eliza)
    8. Target Architecture (Felix)
    9. Migration Strategy (Felix)
    10. Migration Report (Diana)
    """
    orchestrator = MigrationPlanningOrchestrator(db)

    try:
        plan = await orchestrator.start_planning(
            assessment_id=UUID(request.assessment_id),
            target_technology=request.target_technology,
            target_database=request.target_database,
            target_frontend=request.target_frontend
        )

        # Run planning in background
        background_tasks.add_task(
            _run_planning_background,
            str(plan.id)
        )

        return {
            "success": True,
            "plan_id": str(plan.id),
            "status": "draft",
            "message": "Migration planning started. Use /planning/{id}/status to check progress."
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def _run_planning_background(plan_id: str):
    """Background task to run planning"""
    from app.database import async_session_maker

    async with async_session_maker() as db:
        orchestrator = MigrationPlanningOrchestrator(db)
        try:
            await orchestrator.run_planning(UUID(plan_id))
        except Exception as e:
            print(f"Planning failed: {e}")


@router.post("/planning/run-sync", response_model=dict)
async def run_migration_planning_sync(
    request: StartPlanningRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run Workflow 2 synchronously (blocks until complete)
    """
    try:
        plan = await run_migration_planning(
            db=db,
            assessment_id=UUID(request.assessment_id),
            target_technology=request.target_technology,
            target_database=request.target_database,
            target_frontend=request.target_frontend
        )

        return {
            "success": True,
            "plan_id": str(plan.id),
            "status": plan.status,
            "adjusted_fp": plan.adjusted_fp,
            "total_weeks": plan.total_weeks,
            "migration_strategy": plan.migration_strategy,
            "team_size_recommended": plan.team_size_recommended
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/planning/{plan_id}/status", response_model=dict)
async def get_plan_status(
    plan_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get current status of a migration plan"""
    result = await db.execute(
        select(MigrationPlan).where(MigrationPlan.id == UUID(plan_id))
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return {
        "id": str(plan.id),
        "status": plan.status,
        "current_phase": plan.current_phase,
        "progress_percent": plan.progress_percent,
        "error_message": plan.error_message,
        "started_at": plan.started_at.isoformat() if plan.started_at else None,
        "completed_at": plan.completed_at.isoformat() if plan.completed_at else None
    }


@router.get("/planning/{plan_id}", response_model=dict)
async def get_plan_details(
    plan_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get full details of a migration plan"""
    result = await db.execute(
        select(MigrationPlan).where(MigrationPlan.id == UUID(plan_id))
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return plan.to_dict()


@router.get("/planning", response_model=List[PlanSummary])
async def list_plans(
    status: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """List all migration plans"""
    query = select(MigrationPlan).order_by(desc(MigrationPlan.created_at)).limit(limit)

    if status:
        query = query.where(MigrationPlan.status == status)

    result = await db.execute(query)
    plans = result.scalars().all()

    return [
        PlanSummary(
            id=str(p.id),
            assessment_id=str(p.assessment_id),
            target_technology=p.target_technology,
            adjusted_fp=p.adjusted_fp,
            total_weeks=p.total_weeks,
            migration_strategy=p.migration_strategy,
            status=p.status,
            created_at=p.created_at
        )
        for p in plans
    ]


@router.get("/planning/{plan_id}/report", response_model=dict)
async def get_plan_report(
    plan_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the migration report for a plan"""
    result = await db.execute(
        select(MigrationPlan).where(MigrationPlan.id == UUID(plan_id))
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return {
        "plan_id": str(plan.id),
        "report_type": plan.report_type,
        "report": plan.report_content,
        "metadata": plan.report_metadata
    }


@router.post("/planning/{plan_id}/approve", response_model=dict)
async def approve_plan(
    plan_id: str,
    request: ReviewPlanRequest,
    db: AsyncSession = Depends(get_db)
):
    """Approve a migration plan after human review"""
    orchestrator = MigrationPlanningOrchestrator(db)

    try:
        plan = await orchestrator.approve_plan(
            plan_id=UUID(plan_id),
            reviewer=request.reviewer,
            notes=request.notes
        )

        return {
            "success": True,
            "plan_id": str(plan.id),
            "status": plan.status,
            "reviewed_by": plan.reviewed_by,
            "reviewed_at": plan.reviewed_at.isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/planning/{plan_id}/reject", response_model=dict)
async def reject_plan(
    plan_id: str,
    request: ReviewPlanRequest,
    db: AsyncSession = Depends(get_db)
):
    """Reject a migration plan"""
    if not request.notes:
        raise HTTPException(status_code=400, detail="Notes required when rejecting a plan")

    orchestrator = MigrationPlanningOrchestrator(db)

    try:
        plan = await orchestrator.reject_plan(
            plan_id=UUID(plan_id),
            reviewer=request.reviewer,
            notes=request.notes
        )

        return {
            "success": True,
            "plan_id": str(plan.id),
            "status": plan.status,
            "reviewed_by": plan.reviewed_by,
            "review_notes": plan.review_notes
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ Workflow 3: Full Assessment ============

@router.post("/full/start", response_model=dict)
async def start_full_workflow(
    request: FullWorkflowRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Start Workflow 3: Full Assessment (Workflow 1 + 2 combined)

    Runs complete project analysis followed by migration planning.

    All phases executed:
    1-6: Project Analysis
    7-10: Migration Planning
    """
    # Start assessment first
    assessment_orchestrator = ProjectAssessmentOrchestrator(db)

    try:
        assessment = await assessment_orchestrator.start_assessment(
            project_name=request.project_name,
            directory_path=request.directory_path,
            application_id=request.application_id
        )

        # Run full workflow in background
        background_tasks.add_task(
            _run_full_workflow_background,
            str(assessment.id),
            request.target_technology,
            request.target_database,
            request.target_frontend
        )

        return {
            "success": True,
            "assessment_id": str(assessment.id),
            "status": "running",
            "message": "Full workflow started. Assessment runs first, then migration planning."
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def _run_full_workflow_background(
    assessment_id: str,
    target_technology: str,
    target_database: Optional[str],
    target_frontend: Optional[str]
):
    """Background task to run full workflow"""
    from app.database import async_session_maker

    async with async_session_maker() as db:
        # Run assessment
        assessment_orchestrator = ProjectAssessmentOrchestrator(db)
        try:
            assessment = await assessment_orchestrator.run_assessment(UUID(assessment_id))

            # If assessment completed successfully, start planning
            if assessment.status == "completed" and not assessment.blockers:
                planning_orchestrator = MigrationPlanningOrchestrator(db)
                plan = await planning_orchestrator.start_planning(
                    assessment_id=UUID(assessment_id),
                    target_technology=target_technology,
                    target_database=target_database,
                    target_frontend=target_frontend
                )
                await planning_orchestrator.run_planning(plan.id)

        except Exception as e:
            print(f"Full workflow failed: {e}")


@router.post("/full/run-sync", response_model=dict)
async def run_full_workflow_sync(
    request: FullWorkflowRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run Workflow 3 synchronously (blocks until complete)

    Warning: This may take several minutes for large projects.
    """
    try:
        # Run assessment
        assessment = await run_project_assessment(
            db=db,
            project_name=request.project_name,
            directory_path=request.directory_path,
            application_id=request.application_id
        )

        # Check for blockers
        if assessment.blockers:
            return {
                "success": False,
                "assessment_id": str(assessment.id),
                "assessment_status": assessment.status,
                "blockers": assessment.blockers,
                "message": "Assessment has blockers. Resolve them before migration planning."
            }

        # Run planning
        plan = await run_migration_planning(
            db=db,
            assessment_id=assessment.id,
            target_technology=request.target_technology,
            target_database=request.target_database,
            target_frontend=request.target_frontend
        )

        return {
            "success": True,
            "assessment_id": str(assessment.id),
            "plan_id": str(plan.id),
            "assessment_grade": assessment.overall_grade,
            "assessment_score": assessment.overall_health_score,
            "adjusted_fp": plan.adjusted_fp,
            "total_weeks": plan.total_weeks,
            "migration_strategy": plan.migration_strategy,
            "plan_status": plan.status
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Reference Data ============

@router.get("/reference/technologies", response_model=dict)
async def list_target_technologies():
    """List available target technologies for migration"""
    return {
        "technologies": [
            {
                "key": key,
                "name": config["name"],
                "default_database": config["default_database"],
                "default_frontend": config["default_frontend"],
                "supported_patterns": config["patterns"]
            }
            for key, config in TARGET_TECHNOLOGIES.items()
        ]
    }


@router.get("/reference/strategies", response_model=dict)
async def list_migration_strategies():
    """List available migration strategies"""
    return {
        "strategies": [
            {
                "key": key,
                "name": config["name"],
                "description": config["description"],
                "risk_level": config["risk_level"],
                "best_for": config["best_for"],
                "timeline_multiplier": config["timeline_multiplier"]
            }
            for key, config in MIGRATION_STRATEGIES.items()
        ]
    }


# ============ Phase Tracking ============

@router.get("/phases/{assessment_id}", response_model=List[dict])
async def get_assessment_phases(
    assessment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all phases for an assessment"""
    result = await db.execute(
        select(AssessmentPhase)
        .where(AssessmentPhase.assessment_id == UUID(assessment_id))
        .order_by(AssessmentPhase.phase_number)
    )
    phases = result.scalars().all()

    return [p.to_dict() for p in phases]


@router.get("/phases/plan/{plan_id}", response_model=List[dict])
async def get_plan_phases(
    plan_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all phases for a migration plan"""
    result = await db.execute(
        select(AssessmentPhase)
        .where(AssessmentPhase.migration_plan_id == UUID(plan_id))
        .order_by(AssessmentPhase.phase_number)
    )
    phases = result.scalars().all()

    return [p.to_dict() for p in phases]
