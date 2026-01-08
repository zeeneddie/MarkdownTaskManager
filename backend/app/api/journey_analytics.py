# backend/app/api/journey_analytics.py
"""
Journey Analytics API - Week 121

Customer journey tracking and funnel analysis endpoints.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.journey_analytics_service import JourneyAnalyticsService

router = APIRouter(prefix="/api/portal/journey", tags=["Journey Analytics"])


# ============== REQUEST/RESPONSE SCHEMAS ==============

class TrackEventRequest(BaseModel):
    customer_id: str = Field(..., description="Customer identifier")
    event_type: str = Field(..., description="Type of event")
    event_data: Optional[dict] = Field(None, description="Additional event data")
    session_id: Optional[str] = Field(None, description="Browser/app session ID")
    project_id: Optional[int] = Field(None, description="Related project ID")
    feature_id: Optional[int] = Field(None, description="Related feature ID")
    feature_status: Optional[str] = Field(None, description="Feature status")
    page_path: Optional[str] = Field(None, description="Current page path")
    referrer: Optional[str] = Field(None, description="Referrer URL")
    device_type: Optional[str] = Field(None, description="Device type")
    browser: Optional[str] = Field(None, description="Browser name")


class JourneyEventResponse(BaseModel):
    id: str
    customer_id: str
    session_id: Optional[str]
    project_id: Optional[int]
    event_type: str
    event_category: str
    event_data: Optional[dict]
    page_path: Optional[str]
    feature_id: Optional[int]
    feature_status: Optional[str]
    device_type: Optional[str]
    browser: Optional[str]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class FunnelResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    steps: List[dict]
    goal_event: str
    window_days: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FunnelAnalysisResponse(BaseModel):
    funnel_id: str
    funnel_name: str
    period_start: str
    period_end: str
    step_counts: dict
    conversion_rates: dict
    drop_off_rates: dict
    overall_conversion: float
    bottleneck_step: Optional[str]
    avg_time_to_convert_hours: Optional[float]
    insights: List[dict]


class CustomerJourneyResponse(BaseModel):
    customer_id: str
    total_events: int
    events_by_category: dict
    first_event_at: Optional[str]
    last_event_at: Optional[str]
    features_interacted: int
    total_conversions: int
    journey_duration_days: int


class EventStatsResponse(BaseModel):
    period_start: str
    period_end: str
    total_events: int
    unique_customers: int
    events_by_type: dict
    events_by_category: dict
    events_by_device: dict
    avg_events_per_customer: float


# ============== ENDPOINTS ==============

@router.post("/events", response_model=JourneyEventResponse)
async def track_event(
    request: TrackEventRequest,
    db: AsyncSession = Depends(get_db),
):
    """Track a customer journey event."""
    service = JourneyAnalyticsService(db)

    event = await service.track_event(
        customer_id=request.customer_id,
        event_type=request.event_type,
        event_data=request.event_data,
        session_id=request.session_id,
        project_id=request.project_id,
        feature_id=request.feature_id,
        feature_status=request.feature_status,
        page_path=request.page_path,
        referrer=request.referrer,
        device_type=request.device_type,
        browser=request.browser,
    )

    return JourneyEventResponse(
        id=str(event.id),
        customer_id=event.customer_id,
        session_id=event.session_id,
        project_id=event.project_id,
        event_type=event.event_type,
        event_category=event.event_category,
        event_data=event.event_data,
        page_path=event.page_path,
        feature_id=event.feature_id,
        feature_status=event.feature_status,
        device_type=event.device_type,
        browser=event.browser,
        timestamp=event.timestamp,
    )


@router.get("/events", response_model=List[JourneyEventResponse])
async def list_customer_events(
    customer_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    event_types: Optional[str] = Query(None, description="Comma-separated event types"),
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """List events for a customer."""
    service = JourneyAnalyticsService(db)

    events = await service.get_customer_events(
        customer_id=customer_id,
        limit=limit,
        offset=offset,
        event_types=event_types.split(",") if event_types else None,
        categories=categories.split(",") if categories else None,
        start_date=start_date,
        end_date=end_date,
    )

    return [
        JourneyEventResponse(
            id=str(e.id),
            customer_id=e.customer_id,
            session_id=e.session_id,
            project_id=e.project_id,
            event_type=e.event_type,
            event_category=e.event_category,
            event_data=e.event_data,
            page_path=e.page_path,
            feature_id=e.feature_id,
            feature_status=e.feature_status,
            device_type=e.device_type,
            browser=e.browser,
            timestamp=e.timestamp,
        )
        for e in events
    ]


@router.get("/events/feature/{feature_id}", response_model=List[JourneyEventResponse])
async def get_feature_journey(
    feature_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get journey events for a specific feature."""
    service = JourneyAnalyticsService(db)
    events = await service.get_feature_journey(feature_id)

    return [
        JourneyEventResponse(
            id=str(e.id),
            customer_id=e.customer_id,
            session_id=e.session_id,
            project_id=e.project_id,
            event_type=e.event_type,
            event_category=e.event_category,
            event_data=e.event_data,
            page_path=e.page_path,
            feature_id=e.feature_id,
            feature_status=e.feature_status,
            device_type=e.device_type,
            browser=e.browser,
            timestamp=e.timestamp,
        )
        for e in events
    ]


@router.get("/events/session/{session_id}", response_model=List[JourneyEventResponse])
async def get_session_events(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get events for a specific browser/app session."""
    service = JourneyAnalyticsService(db)
    events = await service.get_session_events(session_id)

    return [
        JourneyEventResponse(
            id=str(e.id),
            customer_id=e.customer_id,
            session_id=e.session_id,
            project_id=e.project_id,
            event_type=e.event_type,
            event_category=e.event_category,
            event_data=e.event_data,
            page_path=e.page_path,
            feature_id=e.feature_id,
            feature_status=e.feature_status,
            device_type=e.device_type,
            browser=e.browser,
            timestamp=e.timestamp,
        )
        for e in events
    ]


# ============== FUNNEL ENDPOINTS ==============

@router.get("/funnels", response_model=List[FunnelResponse])
async def list_funnels(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """List all funnel definitions."""
    service = JourneyAnalyticsService(db)
    funnels = await service.list_funnels(active_only=active_only)

    return [
        FunnelResponse(
            id=str(f.id),
            name=f.name,
            description=f.description,
            steps=f.steps or [],
            goal_event=f.goal_event,
            window_days=f.window_days,
            is_active=f.is_active,
            created_at=f.created_at,
        )
        for f in funnels
    ]


@router.get("/funnels/{funnel_id}", response_model=FunnelResponse)
async def get_funnel(
    funnel_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a funnel by ID."""
    service = JourneyAnalyticsService(db)
    funnel = await service.get_funnel(funnel_id)

    if not funnel:
        raise HTTPException(status_code=404, detail="Funnel not found")

    return FunnelResponse(
        id=str(funnel.id),
        name=funnel.name,
        description=funnel.description,
        steps=funnel.steps or [],
        goal_event=funnel.goal_event,
        window_days=funnel.window_days,
        is_active=funnel.is_active,
        created_at=funnel.created_at,
    )


@router.get("/funnels/{funnel_id}/analyze", response_model=FunnelAnalysisResponse)
async def analyze_funnel(
    funnel_id: UUID,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """Analyze funnel performance for a given period."""
    service = JourneyAnalyticsService(db)

    try:
        analysis = await service.analyze_funnel(
            funnel_id=funnel_id,
            period_start=period_start,
            period_end=period_end,
        )
        return FunnelAnalysisResponse(**analysis)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/funnels/{funnel_id}/snapshot", response_model=FunnelAnalysisResponse)
async def create_funnel_snapshot(
    funnel_id: UUID,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """Create and store a funnel analysis snapshot."""
    service = JourneyAnalyticsService(db)

    try:
        snapshot = await service.create_funnel_snapshot(
            funnel_id=funnel_id,
            period_start=period_start,
            period_end=period_end,
        )
        return FunnelAnalysisResponse(
            funnel_id=str(snapshot.funnel_id),
            funnel_name="",  # Would need to join
            period_start=snapshot.period_start.isoformat(),
            period_end=snapshot.period_end.isoformat(),
            step_counts=snapshot.step_counts,
            conversion_rates=snapshot.conversion_rates,
            drop_off_rates=snapshot.drop_off_rates,
            overall_conversion=snapshot.overall_conversion,
            bottleneck_step=snapshot.bottleneck_step,
            avg_time_to_convert_hours=snapshot.avg_time_to_convert,
            insights=snapshot.insights or [],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== CUSTOMER JOURNEY ENDPOINTS ==============

@router.get("/customers/{customer_id}/summary", response_model=CustomerJourneyResponse)
async def get_customer_journey_summary(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get summary of a customer's journey."""
    service = JourneyAnalyticsService(db)
    summary = await service.get_customer_journey_summary(customer_id)
    return CustomerJourneyResponse(**summary)


# ============== STATS ENDPOINTS ==============

@router.get("/stats", response_model=EventStatsResponse)
async def get_event_stats(
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get aggregate event statistics."""
    service = JourneyAnalyticsService(db)
    stats = await service.get_event_stats(
        period_start=period_start,
        period_end=period_end,
    )
    return EventStatsResponse(**stats)


# ============== BATCH TRACKING ==============

class BatchEventRequest(BaseModel):
    events: List[TrackEventRequest] = Field(..., max_length=100)


class BatchEventResponse(BaseModel):
    tracked: int
    errors: int


@router.post("/events/batch", response_model=BatchEventResponse)
async def track_events_batch(
    request: BatchEventRequest,
    db: AsyncSession = Depends(get_db),
):
    """Track multiple events in a single request."""
    service = JourneyAnalyticsService(db)

    tracked = 0
    errors = 0

    for event in request.events:
        try:
            await service.track_event(
                customer_id=event.customer_id,
                event_type=event.event_type,
                event_data=event.event_data,
                session_id=event.session_id,
                project_id=event.project_id,
                feature_id=event.feature_id,
                feature_status=event.feature_status,
                page_path=event.page_path,
                referrer=event.referrer,
                device_type=event.device_type,
                browser=event.browser,
            )
            tracked += 1
        except Exception:
            errors += 1

    return BatchEventResponse(tracked=tracked, errors=errors)
