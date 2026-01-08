"""
Attribution API Endpoints
Week 21-22 Implementation
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.database import get_db
from app.services.attribution_service import AttributionService
from app.schemas.attribution import (
    TaskOutcomeInput,
    AttributionResponse,
    AttributionFeedbackResponse,
    AgentPerformanceMetricsResponse,
    AttributionQuery,
    AttributionListResponse,
    AttributionSummary,
    AgentSummary,
    OutcomeType,
    FeedbackType,
    BatchAnalyzeRequest,
    BatchDeliverFeedbackRequest
)

router = APIRouter(prefix="/api/attribution", tags=["attribution"])


def get_attribution_service(db: AsyncSession = Depends(get_db)) -> AttributionService:
    """Dependency injection for attribution service."""
    return AttributionService(db)


# =============================================================================
# Task Outcome Endpoints
# =============================================================================

@router.post("/outcomes", response_model=dict)
async def record_task_outcome(
    outcome: TaskOutcomeInput,
    service: AttributionService = Depends(get_attribution_service)
):
    """
    Record a task outcome for attribution analysis.

    This endpoint should be called when a task completes (success, failure, or partial).
    The outcome data will be stored and can later be analyzed for attribution.
    """
    try:
        task_outcome = await service.record_task_outcome(outcome)
        return {
            "status": "recorded",
            "outcome_id": str(task_outcome.id),
            "task_id": outcome.task_id,
            "message": "Task outcome recorded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outcomes/{outcome_id}/analyze", response_model=AttributionResponse)
async def analyze_task_outcome(
    outcome_id: UUID,
    service: AttributionService = Depends(get_attribution_service)
):
    """
    Trigger attribution analysis for a recorded task outcome.

    This will analyze the task steps, quality gate results, and validation history
    to determine what factors contributed to the outcome.
    """
    try:
        attribution = await service.analyze_task(outcome_id)
        return service._attribution_to_response(attribution)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Attribution Query Endpoints
# =============================================================================

@router.get("/", response_model=AttributionListResponse)
async def list_attributions(
    agent_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    outcome: Optional[OutcomeType] = None,
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: AttributionService = Depends(get_attribution_service)
):
    """
    List attributions with optional filtering.

    Supports filtering by agent, workflow, outcome type, confidence level,
    and date range. Results are paginated.
    """
    query = AttributionQuery(
        agent_id=agent_id,
        workflow_id=workflow_id,
        outcome=outcome,
        min_confidence=min_confidence,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )
    return await service.list_attributions(query)


@router.get("/summary", response_model=AttributionSummary)
async def get_attribution_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: AttributionService = Depends(get_attribution_service)
):
    """
    Get summary statistics for attributions.

    Returns overall counts and averages for the specified period.
    """
    return await service.get_summary(start_date, end_date)


@router.get("/health", response_model=dict)
async def health_check(
    service: AttributionService = Depends(get_attribution_service)
):
    """
    Check attribution service health.
    """
    try:
        summary = await service.get_summary()
        return {
            "status": "healthy",
            "total_attributions": summary.total_attributions,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/{attribution_id}", response_model=AttributionResponse)
async def get_attribution(
    attribution_id: UUID,
    service: AttributionService = Depends(get_attribution_service)
):
    """
    Get a specific attribution by ID.

    Returns full attribution details including key steps, causal factors,
    quality gate results, and validation history.
    """
    attribution = await service.get_attribution(attribution_id)
    if not attribution:
        raise HTTPException(status_code=404, detail="Attribution not found")
    return service._attribution_to_response(attribution)


# =============================================================================
# Feedback Endpoints
# =============================================================================

@router.post("/{attribution_id}/feedback", response_model=dict)
async def generate_feedback(
    attribution_id: UUID,
    service: AttributionService = Depends(get_attribution_service)
):
    """
    Generate feedback for an agent based on attribution analysis.

    Creates lessons learned and recommended adjustments based on the
    attribution results. The feedback is stored but not automatically delivered.
    """
    try:
        feedback = await service.generate_feedback(attribution_id)
        return {
            "status": "generated",
            "feedback_id": str(feedback.id),
            "agent_id": feedback.agent_id,
            "feedback_type": feedback.feedback_type,
            "message": "Feedback generated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback/{feedback_id}/deliver", response_model=dict)
async def deliver_feedback(
    feedback_id: UUID,
    service: AttributionService = Depends(get_attribution_service)
):
    """
    Deliver feedback to the agent's experience store.

    Sends the lessons learned and adjustments to the agent service
    so they can be integrated into the agent's decision-making.
    """
    try:
        success = await service.deliver_feedback(feedback_id)
        if success:
            return {
                "status": "delivered",
                "feedback_id": str(feedback_id),
                "message": "Feedback delivered to agent"
            }
        else:
            return {
                "status": "failed",
                "feedback_id": str(feedback_id),
                "message": "Failed to deliver feedback - agent service unavailable"
            }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/pending", response_model=List[dict])
async def get_pending_feedback(
    agent_id: Optional[str] = None,
    service: AttributionService = Depends(get_attribution_service)
):
    """
    Get list of undelivered feedback.

    Returns feedback that has been generated but not yet delivered
    to the agent's experience store.
    """
    pending = await service.list_pending_feedback(agent_id)
    return [
        {
            "feedback_id": str(f.id),
            "attribution_id": str(f.attribution_id),
            "agent_id": f.agent_id,
            "feedback_type": f.feedback_type,
            "created_at": f.created_at.isoformat()
        }
        for f in pending
    ]


# =============================================================================
# Agent Metrics Endpoints
# =============================================================================

@router.get("/agents/summary", response_model=List[AgentSummary])
async def get_all_agent_summaries(
    service: AttributionService = Depends(get_attribution_service)
):
    """
    Get summary metrics for all agents.

    Returns a list of all agents with their basic performance metrics
    and recent trend (improving/stable/declining).
    """
    return await service.get_agent_summaries()


@router.get("/agents/{agent_id}/metrics", response_model=AgentPerformanceMetricsResponse)
async def get_agent_metrics(
    agent_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: AttributionService = Depends(get_attribution_service)
):
    """
    Get detailed performance metrics for a specific agent.

    Returns comprehensive metrics including success rate, confidence scores,
    top success factors, failure patterns, and improvement trend.
    """
    return await service.get_agent_metrics(agent_id, start_date, end_date)


# =============================================================================
# Batch Operations
# =============================================================================

@router.post("/batch/analyze", response_model=dict)
async def batch_analyze(
    request: BatchAnalyzeRequest,
    service: AttributionService = Depends(get_attribution_service)
):
    """
    Analyze multiple task outcomes in batch.

    Useful for processing backlog of recorded outcomes.
    """
    results = {"analyzed": 0, "failed": 0, "errors": []}

    for outcome_id in request.outcome_ids:
        try:
            await service.analyze_task(outcome_id)
            results["analyzed"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "outcome_id": str(outcome_id),
                "error": str(e)
            })

    return results


@router.post("/batch/deliver-feedback", response_model=dict)
async def batch_deliver_feedback(
    request: BatchDeliverFeedbackRequest = BatchDeliverFeedbackRequest(),
    service: AttributionService = Depends(get_attribution_service)
):
    """
    Deliver multiple feedback items in batch.

    If no IDs provided, delivers all pending feedback (optionally filtered by agent).
    """
    feedback_ids = request.feedback_ids
    if not feedback_ids:
        pending = await service.list_pending_feedback(request.agent_id)
        feedback_ids = [f.id for f in pending]

    results = {"delivered": 0, "failed": 0}

    for feedback_id in feedback_ids:
        try:
            success = await service.deliver_feedback(feedback_id)
            if success:
                results["delivered"] += 1
            else:
                results["failed"] += 1
        except Exception:
            results["failed"] += 1

    return results
