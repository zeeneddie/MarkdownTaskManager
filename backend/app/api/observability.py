"""
Observability API Routes - Agent Monitoring & Performance

Week 54: REST API for observability system.
Provides endpoints for:
- Provider management
- Action logging
- Decision tracing
- Performance metrics
"""

from datetime import datetime, date, timedelta, timezone
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.observability_service import ObservabilityService


router = APIRouter(prefix="/observability", tags=["observability"])


# ==================== SCHEMAS ====================

class ProviderResponse(BaseModel):
    """LLM Provider response."""
    id: int
    name: str
    display_name: Optional[str]
    provider_type: str
    tier: str
    model: str
    cost_input_per_m: float
    cost_output_per_m: float
    is_local: bool
    is_active: bool


class ProviderStatusUpdate(BaseModel):
    """Request to update provider status."""
    is_active: bool


class LogActionRequest(BaseModel):
    """Request to log an agent action."""
    agent_id: str = Field(..., description="Agent identifier (e.g., 'felix', 'quinn')")
    action_type: str = Field(..., description="Type of action (e.g., 'generate', 'review')")
    provider: Optional[str] = Field(None, description="LLM provider used")
    model: Optional[str] = Field(None, description="Specific model used")
    task_id: Optional[UUID] = Field(None, description="Associated task ID")
    session_id: Optional[UUID] = Field(None, description="Session ID")
    input_summary: Optional[str] = Field(None, description="Truncated input")
    output_summary: Optional[str] = Field(None, description="Truncated output")
    decision_rationale: Optional[str] = Field(None, description="Why this action was taken")
    token_input: int = Field(0, description="Input tokens used")
    token_output: int = Field(0, description="Output tokens generated")
    duration_ms: int = Field(0, description="Duration in milliseconds")
    cost_cents: float = Field(0.0, description="Cost in cents")
    success: bool = Field(True, description="Whether action succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Confidence 0.0-1.0")
    extra_data: Optional[dict] = Field(None, description="Additional context")


class ActionResponse(BaseModel):
    """Agent action response."""
    id: int
    task_id: Optional[str]
    session_id: Optional[str]
    agent_id: str
    action_type: str
    provider: Optional[str]
    model: Optional[str]
    success: bool
    duration_ms: int
    cost_cents: float
    confidence_score: Optional[float]
    created_at: str


class LogDecisionRequest(BaseModel):
    """Request to log a decision point."""
    agent_id: str
    decision_point: str = Field(..., description="e.g., 'model_selection', 'quality_gate'")
    task_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    options: Optional[List[dict]] = Field(None, description="Options considered")
    selected_option: Optional[str] = None
    selection_rationale: Optional[str] = None
    outcome: Optional[str] = Field(None, description="success, failure, skipped")
    outcome_details: Optional[dict] = None


class DecisionResponse(BaseModel):
    """Decision trace response."""
    id: int
    task_id: Optional[str]
    sequence_number: int
    agent_id: str
    decision_point: str
    selected_option: Optional[str]
    outcome: Optional[str]
    created_at: str


class AgentStatsResponse(BaseModel):
    """Agent statistics response."""
    agent_id: str
    period_days: int
    total_actions: int
    successful_actions: int
    success_rate: float
    avg_duration_ms: int
    total_tokens: int
    total_cost_cents: float
    provider_breakdown: dict


class PlatformStatsResponse(BaseModel):
    """Platform-wide statistics."""
    period_days: int
    total_actions: int
    successful_actions: int
    success_rate: float
    active_agents: int
    total_cost_cents: float
    top_agents: List[dict]


class DailyPerformanceResponse(BaseModel):
    """Daily performance metrics."""
    id: int
    agent_id: str
    provider: Optional[str]
    date: str
    total_actions: int
    successful_actions: int
    failed_actions: int
    success_rate: float
    avg_duration_ms: int
    total_tokens_input: int
    total_tokens_output: int
    total_cost_cents: float
    avg_confidence: Optional[float]


# ==================== PROVIDER ENDPOINTS ====================

@router.get("/providers", response_model=List[ProviderResponse])
async def list_providers(
    active_only: bool = Query(False, description="Only return active providers"),
    tier: Optional[str] = Query(None, description="Filter by tier"),
    db: AsyncSession = Depends(get_db)
):
    """List all LLM providers."""
    service = ObservabilityService(db)

    if tier:
        providers = await service.get_providers_by_tier(tier)
    elif active_only:
        providers = await service.get_active_providers()
    else:
        providers = await service.get_all_providers()

    return [ProviderResponse(**p.to_dict()) for p in providers]


@router.get("/providers/{name}", response_model=ProviderResponse)
async def get_provider(
    name: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific provider by name."""
    service = ObservabilityService(db)
    provider = await service.get_provider_by_name(name)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{name}' not found")
    return ProviderResponse(**provider.to_dict())


@router.patch("/providers/{name}/status", response_model=ProviderResponse)
async def update_provider_status(
    name: str,
    update: ProviderStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Enable or disable a provider."""
    service = ObservabilityService(db)
    provider = await service.update_provider_status(name, update.is_active)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{name}' not found")
    return ProviderResponse(**provider.to_dict())


# ==================== ACTION LOGGING ENDPOINTS ====================

@router.post("/actions", response_model=ActionResponse)
async def log_action(
    request: LogActionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Log an agent action."""
    service = ObservabilityService(db)
    action = await service.log_action(**request.model_dump())

    return ActionResponse(
        id=action.id,
        task_id=str(action.task_id) if action.task_id else None,
        session_id=str(action.session_id) if action.session_id else None,
        agent_id=action.agent_id,
        action_type=action.action_type,
        provider=action.provider,
        model=action.model,
        success=action.success,
        duration_ms=action.duration_ms,
        cost_cents=float(action.cost_cents) if action.cost_cents else 0,
        confidence_score=float(action.confidence_score) if action.confidence_score else None,
        created_at=action.created_at.isoformat() if action.created_at else "",
    )


@router.get("/actions", response_model=List[ActionResponse])
async def list_actions(
    agent_id: Optional[str] = Query(None, description="Filter by agent"),
    limit: int = Query(50, ge=1, le=200),
    hours: Optional[int] = Query(None, description="Actions in last N hours"),
    db: AsyncSession = Depends(get_db)
):
    """List recent agent actions."""
    service = ObservabilityService(db)

    since = None
    if hours:
        since = datetime.utcnow() - timedelta(hours=hours)

    actions = await service.get_recent_actions(agent_id, limit, since)

    return [
        ActionResponse(
            id=a.id,
            task_id=str(a.task_id) if a.task_id else None,
            session_id=str(a.session_id) if a.session_id else None,
            agent_id=a.agent_id,
            action_type=a.action_type,
            provider=a.provider,
            model=a.model,
            success=a.success,
            duration_ms=a.duration_ms,
            cost_cents=float(a.cost_cents) if a.cost_cents else 0,
            confidence_score=float(a.confidence_score) if a.confidence_score else None,
            created_at=a.created_at.isoformat() if a.created_at else "",
        )
        for a in actions
    ]


@router.get("/actions/task/{task_id}", response_model=List[ActionResponse])
async def get_task_actions(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all actions for a specific task."""
    service = ObservabilityService(db)
    actions = await service.get_actions_by_task(task_id)

    return [
        ActionResponse(
            id=a.id,
            task_id=str(a.task_id) if a.task_id else None,
            session_id=str(a.session_id) if a.session_id else None,
            agent_id=a.agent_id,
            action_type=a.action_type,
            provider=a.provider,
            model=a.model,
            success=a.success,
            duration_ms=a.duration_ms,
            cost_cents=float(a.cost_cents) if a.cost_cents else 0,
            confidence_score=float(a.confidence_score) if a.confidence_score else None,
            created_at=a.created_at.isoformat() if a.created_at else "",
        )
        for a in actions
    ]


# ==================== DECISION TRACING ENDPOINTS ====================

@router.post("/decisions", response_model=DecisionResponse)
async def log_decision(
    request: LogDecisionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Log a decision point."""
    service = ObservabilityService(db)
    decision = await service.log_decision(**request.model_dump())

    return DecisionResponse(
        id=decision.id,
        task_id=str(decision.task_id) if decision.task_id else None,
        sequence_number=decision.sequence_number,
        agent_id=decision.agent_id,
        decision_point=decision.decision_point,
        selected_option=decision.selected_option,
        outcome=decision.outcome,
        created_at=decision.created_at.isoformat() if decision.created_at else "",
    )


@router.get("/decisions/task/{task_id}", response_model=List[DecisionResponse])
async def get_task_decisions(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get the decision trace for a task."""
    service = ObservabilityService(db)
    decisions = await service.get_decision_trace(task_id)

    return [
        DecisionResponse(
            id=d.id,
            task_id=str(d.task_id) if d.task_id else None,
            sequence_number=d.sequence_number,
            agent_id=d.agent_id,
            decision_point=d.decision_point,
            selected_option=d.selected_option,
            outcome=d.outcome,
            created_at=d.created_at.isoformat() if d.created_at else "",
        )
        for d in decisions
    ]


# ==================== PERFORMANCE & STATISTICS ENDPOINTS ====================

@router.get("/stats/agent/{agent_id}", response_model=AgentStatsResponse)
async def get_agent_stats(
    agent_id: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics for a specific agent."""
    service = ObservabilityService(db)
    stats = await service.get_agent_statistics(agent_id, days)
    return AgentStatsResponse(**stats)


@router.get("/stats/platform", response_model=PlatformStatsResponse)
async def get_platform_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """Get platform-wide statistics."""
    service = ObservabilityService(db)
    stats = await service.get_platform_statistics(days)
    return PlatformStatsResponse(**stats)


@router.get("/performance/daily", response_model=List[DailyPerformanceResponse])
async def get_daily_performance(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    agent_id: Optional[str] = Query(None, description="Filter by agent"),
    db: AsyncSession = Depends(get_db)
):
    """Get daily performance metrics."""
    service = ObservabilityService(db)
    records = await service.get_daily_performance(start_date, end_date, agent_id)

    return [
        DailyPerformanceResponse(
            id=r.id,
            agent_id=r.agent_id,
            provider=r.provider,
            date=r.date.isoformat() if r.date else "",
            total_actions=r.total_actions,
            successful_actions=r.successful_actions,
            failed_actions=r.failed_actions,
            success_rate=(
                r.successful_actions / r.total_actions * 100
                if r.total_actions > 0 else 0
            ),
            avg_duration_ms=r.avg_duration_ms,
            total_tokens_input=r.total_tokens_input,
            total_tokens_output=r.total_tokens_output,
            total_cost_cents=float(r.total_cost_cents) if r.total_cost_cents else 0,
            avg_confidence=float(r.avg_confidence) if r.avg_confidence else None,
        )
        for r in records
    ]


@router.post("/performance/aggregate")
async def trigger_aggregation(
    target_date: Optional[date] = Query(None, description="Date to aggregate (defaults to today)"),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger daily performance aggregation."""
    service = ObservabilityService(db)
    result = await service.aggregate_daily_performance(target_date)
    return {
        "message": "Aggregation complete",
        **result
    }


# ==================== HEALTH CHECK ====================

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check for observability system."""
    service = ObservabilityService(db)
    providers = await service.get_active_providers()

    return {
        "status": "healthy",
        "active_providers": len(providers),
        "providers": [p.name for p in providers],
    }
