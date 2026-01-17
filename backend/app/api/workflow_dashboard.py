"""
Workflow Dashboard API (Week 69)

Provides API endpoints for the Workflow Monitoring Dashboard.
Exposes assessment progress, migration plans, and agent activity.

Author: Claude Code (Week 69)
Date: 2025-12-15
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models.project_assessment import ProjectAssessment, MigrationPlan, AssessmentPhase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflows", tags=["workflows"])


# ============ Response Models ============

class WorkflowStatistics(BaseModel):
    """Overall workflow statistics"""
    active_assessments: int
    completed_today: int
    plans_in_review: int
    approved_plans: int
    avg_assessment_minutes: Optional[int] = None
    success_rate: Optional[int] = None
    total_assessments: int
    total_plans: int


class AssessmentSummary(BaseModel):
    """Summary of an assessment for the dashboard"""
    id: str
    project_name: str
    status: str
    current_phase: str
    progress_percent: int
    primary_stack: Optional[str] = None
    overall_grade: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class PlanSummary(BaseModel):
    """Summary of a migration plan for the dashboard"""
    id: str
    project_name: str
    target_technology: str
    adjusted_fp: Optional[int] = None
    timeline_weeks: Optional[int] = None
    status: str
    reviewed_by: Optional[str] = None


class AgentActivity(BaseModel):
    """Agent activity summary"""
    agent_name: str
    task_count: int
    last_active: Optional[datetime] = None


class PhaseDetail(BaseModel):
    """Phase execution detail"""
    phase_number: int
    phase_name: str
    agent_name: str
    status: str
    duration_seconds: Optional[int] = None
    items_processed: Optional[int] = None


class PlanApprovalRequest(BaseModel):
    """Request to approve a migration plan"""
    reviewer: str
    notes: Optional[str] = None


class PlanRejectionRequest(BaseModel):
    """Request to reject a migration plan"""
    reviewer: str
    notes: str


# ============ API Endpoints ============

@router.get("/statistics", response_model=WorkflowStatistics)
async def get_workflow_statistics(db: AsyncSession = Depends(get_db)):
    """
    Get overall workflow statistics for the dashboard.

    Returns counts of active assessments, completed today, plans in review, etc.
    """
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    try:
        # Count active assessments
        active_result = await db.execute(
            select(func.count(ProjectAssessment.id))
            .where(ProjectAssessment.status == "running")
        )
        active_assessments = active_result.scalar() or 0

        # Count completed today
        completed_result = await db.execute(
            select(func.count(ProjectAssessment.id))
            .where(and_(
                ProjectAssessment.status == "completed",
                ProjectAssessment.completed_at >= today_start
            ))
        )
        completed_today = completed_result.scalar() or 0

        # Count plans in review
        review_result = await db.execute(
            select(func.count(MigrationPlan.id))
            .where(MigrationPlan.status == "in_review")
        )
        plans_in_review = review_result.scalar() or 0

        # Count approved plans
        approved_result = await db.execute(
            select(func.count(MigrationPlan.id))
            .where(MigrationPlan.status == "approved")
        )
        approved_plans = approved_result.scalar() or 0

        # Total counts
        total_assessments_result = await db.execute(
            select(func.count(ProjectAssessment.id))
        )
        total_assessments = total_assessments_result.scalar() or 0

        total_plans_result = await db.execute(
            select(func.count(MigrationPlan.id))
        )
        total_plans = total_plans_result.scalar() or 0

        # Calculate average assessment time (completed in last 7 days)
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        avg_result = await db.execute(
            select(
                func.avg(
                    func.extract('epoch', ProjectAssessment.completed_at) -
                    func.extract('epoch', ProjectAssessment.started_at)
                )
            ).where(and_(
                ProjectAssessment.status == "completed",
                ProjectAssessment.completed_at >= week_ago,
                ProjectAssessment.started_at.isnot(None),
                ProjectAssessment.completed_at.isnot(None)
            ))
        )
        avg_seconds = avg_result.scalar()
        avg_assessment_minutes = int(avg_seconds / 60) if avg_seconds else None

        # Calculate success rate
        total_finished = await db.execute(
            select(func.count(ProjectAssessment.id))
            .where(ProjectAssessment.status.in_(["completed", "failed"]))
        )
        total_finished_count = total_finished.scalar() or 0

        success_count = await db.execute(
            select(func.count(ProjectAssessment.id))
            .where(ProjectAssessment.status == "completed")
        )
        success_count_val = success_count.scalar() or 0

        success_rate = int((success_count_val / total_finished_count) * 100) if total_finished_count > 0 else None

        return WorkflowStatistics(
            active_assessments=active_assessments,
            completed_today=completed_today,
            plans_in_review=plans_in_review,
            approved_plans=approved_plans,
            avg_assessment_minutes=avg_assessment_minutes,
            success_rate=success_rate,
            total_assessments=total_assessments,
            total_plans=total_plans
        )

    except Exception as e:
        logger.error(f"Failed to get workflow statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessments", response_model=List[AssessmentSummary])
async def get_assessments(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of project assessments.

    Optionally filter by status (running, completed, failed).
    """
    try:
        query = select(ProjectAssessment).order_by(ProjectAssessment.started_at.desc())

        if status:
            query = query.where(ProjectAssessment.status == status)

        query = query.limit(limit)

        result = await db.execute(query)
        assessments = result.scalars().all()

        return [
            AssessmentSummary(
                id=str(a.id),
                project_name=a.project_name,
                status=a.status,
                current_phase=a.current_phase or "unknown",
                progress_percent=a.progress_percent or 0,
                primary_stack=a.primary_stack,
                overall_grade=a.overall_grade,
                started_at=a.started_at,
                completed_at=a.completed_at
            )
            for a in assessments
        ]

    except Exception as e:
        logger.error(f"Failed to get assessments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessments/{assessment_id}", response_model=Dict[str, Any])
async def get_assessment_detail(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed assessment information including phase results.
    """
    try:
        # Get assessment
        result = await db.execute(
            select(ProjectAssessment).where(ProjectAssessment.id == assessment_id)
        )
        assessment = result.scalar_one_or_none()

        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        # Get phases
        phases_result = await db.execute(
            select(AssessmentPhase)
            .where(AssessmentPhase.assessment_id == assessment_id)
            .order_by(AssessmentPhase.phase_number)
        )
        phases = phases_result.scalars().all()

        return {
            "id": str(assessment.id),
            "project_name": assessment.project_name,
            "directory_path": assessment.directory_path,
            "status": assessment.status,
            "current_phase": assessment.current_phase,
            "progress_percent": assessment.progress_percent,
            "primary_stack": assessment.primary_stack,
            "detected_stacks": assessment.detected_stacks,
            "file_count": assessment.file_count,
            "line_count": assessment.line_count,
            "architecture_pattern": assessment.architecture_pattern,
            "architecture_score": assessment.architecture_score,
            "security_grade": assessment.security_grade,
            "quality_grade": assessment.quality_grade,
            "overall_grade": assessment.overall_grade,
            "overall_health_score": assessment.overall_health_score,
            "health_summary": assessment.health_summary,
            "recommendations": assessment.recommendations,
            "blockers": assessment.blockers,
            "started_at": assessment.started_at.isoformat() if assessment.started_at else None,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
            "phases": [
                {
                    "phase_number": p.phase_number,
                    "phase_name": p.phase_name,
                    "agent_name": p.agent_name,
                    "status": p.status,
                    "duration_seconds": p.duration_seconds,
                    "items_processed": p.items_processed,
                    "items_found": p.items_found,
                    "result_summary": p.result_summary
                }
                for p in phases
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assessment detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans", response_model=List[PlanSummary])
async def get_migration_plans(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of migration plans.

    Optionally filter by status (draft, in_review, approved, rejected).
    """
    try:
        query = select(MigrationPlan, ProjectAssessment.project_name).join(
            ProjectAssessment,
            MigrationPlan.assessment_id == ProjectAssessment.id
        ).order_by(MigrationPlan.started_at.desc())

        if status:
            query = query.where(MigrationPlan.status == status)

        query = query.limit(limit)

        result = await db.execute(query)
        plans = result.all()

        return [
            PlanSummary(
                id=str(p[0].id),
                project_name=p[1],
                target_technology=p[0].target_technology,
                adjusted_fp=p[0].adjusted_fp,
                timeline_weeks=p[0].timeline_weeks,
                status=p[0].status,
                reviewed_by=p[0].reviewed_by
            )
            for p in plans
        ]

    except Exception as e:
        logger.error(f"Failed to get migration plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans/{plan_id}", response_model=Dict[str, Any])
async def get_plan_detail(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed migration plan information.
    """
    try:
        result = await db.execute(
            select(MigrationPlan).where(MigrationPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()

        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        # Get assessment for project name
        assessment_result = await db.execute(
            select(ProjectAssessment).where(ProjectAssessment.id == plan.assessment_id)
        )
        assessment = assessment_result.scalar_one_or_none()

        return {
            "id": str(plan.id),
            "assessment_id": str(plan.assessment_id),
            "project_name": assessment.project_name if assessment else "Unknown",
            "target_technology": plan.target_technology,
            "target_database": plan.target_database,
            "target_frontend": plan.target_frontend,
            "status": plan.status,
            "unadjusted_fp": plan.unadjusted_fp,
            "adjusted_fp": plan.adjusted_fp,
            "total_hours": plan.total_hours,
            "total_weeks": plan.total_weeks,
            "timeline_weeks": plan.timeline_weeks,
            "team_size_recommended": plan.team_size_recommended,
            "team_composition": plan.team_composition,
            "migration_strategy": plan.migration_strategy,
            "migration_phases": plan.migration_phases,
            "milestones": plan.milestones,
            "architecture_pattern": plan.architecture_pattern,
            "architecture_layers": plan.architecture_layers,
            "component_mapping": plan.component_mapping,
            "risks": plan.risks,
            "success_criteria": plan.success_criteria,
            "report_content": plan.report_content,
            "reviewed_by": plan.reviewed_by,
            "reviewed_at": plan.reviewed_at.isoformat() if plan.reviewed_at else None,
            "review_notes": plan.review_notes,
            "started_at": plan.started_at.isoformat() if plan.started_at else None,
            "completed_at": plan.completed_at.isoformat() if plan.completed_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get plan detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans/{plan_id}/approve")
async def approve_plan(
    plan_id: UUID,
    request: PlanApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve a migration plan after human review.
    """
    try:
        result = await db.execute(
            select(MigrationPlan).where(MigrationPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()

        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        if plan.status != "in_review":
            raise HTTPException(
                status_code=400,
                detail=f"Plan must be in_review to approve. Current status: {plan.status}"
            )

        plan.status = "approved"
        plan.reviewed_by = request.reviewer
        plan.reviewed_at = datetime.now(timezone.utc)
        plan.review_notes = request.notes

        await db.commit()

        return {
            "success": True,
            "plan_id": str(plan_id),
            "status": "approved",
            "reviewed_by": request.reviewer
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans/{plan_id}/reject")
async def reject_plan(
    plan_id: UUID,
    request: PlanRejectionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reject a migration plan.
    """
    try:
        result = await db.execute(
            select(MigrationPlan).where(MigrationPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()

        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        if plan.status not in ["in_review", "draft"]:
            raise HTTPException(
                status_code=400,
                detail=f"Plan cannot be rejected. Current status: {plan.status}"
            )

        plan.status = "rejected"
        plan.reviewed_by = request.reviewer
        plan.reviewed_at = datetime.now(timezone.utc)
        plan.review_notes = request.notes

        await db.commit()

        return {
            "success": True,
            "plan_id": str(plan_id),
            "status": "rejected",
            "reviewed_by": request.reviewer,
            "notes": request.notes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents", response_model=List[AgentActivity])
async def get_agent_activity(db: AsyncSession = Depends(get_db)):
    """
    Get activity summary for all agents.
    """
    try:
        # Count phases by agent
        result = await db.execute(
            select(
                AssessmentPhase.agent_name,
                func.count(AssessmentPhase.id).label("task_count"),
                func.max(AssessmentPhase.completed_at).label("last_active")
            )
            .group_by(AssessmentPhase.agent_name)
            .order_by(func.count(AssessmentPhase.id).desc())
        )

        agent_data = result.all()

        # Define all agents with default counts
        all_agents = {
            "felix": "Architect",
            "quinn": "Quality",
            "betty": "Bug Hunter",
            "eliza": "Estimation",
            "diana": "Documentation",
            "marcus": "Maintenance",
            "tessa": "Testing",
            "miguel": "Migration",
            "peter": "Product",
            "paul": "Planning",
            "system": "System",
            "coderag": "CodeRAG"
        }

        # Merge actual data with defaults
        activity_map = {
            row[0]: {"task_count": row[1], "last_active": row[2]}
            for row in agent_data
        }

        return [
            AgentActivity(
                agent_name=name,
                task_count=activity_map.get(name, {}).get("task_count", 0),
                last_active=activity_map.get(name, {}).get("last_active")
            )
            for name in all_agents.keys()
        ]

    except Exception as e:
        logger.error(f"Failed to get agent activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/phases/{assessment_id}", response_model=List[PhaseDetail])
async def get_assessment_phases(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get phase execution details for an assessment.
    """
    try:
        result = await db.execute(
            select(AssessmentPhase)
            .where(AssessmentPhase.assessment_id == assessment_id)
            .order_by(AssessmentPhase.phase_number)
        )
        phases = result.scalars().all()

        return [
            PhaseDetail(
                phase_number=p.phase_number,
                phase_name=p.phase_name,
                agent_name=p.agent_name,
                status=p.status,
                duration_seconds=p.duration_seconds,
                items_processed=p.items_processed
            )
            for p in phases
        ]

    except Exception as e:
        logger.error(f"Failed to get phases: {e}")
        raise HTTPException(status_code=500, detail=str(e))
