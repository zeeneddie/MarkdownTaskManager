# backend/app/api/portal_boost.py
"""
Portal Boost & Enhancement API - Week 118

Client Portal 2.0 Phase 2: Transparency & Control
- Priority Boost endpoints
- Impact Preview endpoints (Felix)
- Duplicate Detection endpoints
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.priority_boost_service import PriorityBoostService
from app.services.impact_preview_service import ImpactPreviewService
from app.services.duplicate_detector_service import DuplicateDetectorService


router = APIRouter(prefix="/api/portal", tags=["Portal Enhancements"])


# ============== Schemas ==============

class BoostRequest(BaseModel):
    """Request to use a priority boost."""
    feature_request_id: int
    feature_title: Optional[str] = None
    current_priority: Optional[str] = None
    reason: Optional[str] = None


class BoostResponse(BaseModel):
    """Response from boost operation."""
    success: bool
    boost_id: Optional[str] = None
    feature_request_id: Optional[int] = None
    original_priority: Optional[str] = None
    boosted_priority: Optional[str] = None
    expires_at: Optional[str] = None
    remaining_boosts: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None


class ImpactRequest(BaseModel):
    """Request for impact analysis."""
    title: str
    description: str
    project_id: Optional[int] = None
    context: Optional[str] = None
    force_refresh: bool = False


class DuplicateCheckRequest(BaseModel):
    """Request to check for duplicates."""
    title: str
    description: str
    project_id: Optional[int] = None
    auto_record: bool = True


class DuplicateResolveRequest(BaseModel):
    """Request to resolve a duplicate."""
    resolution: str = Field(..., pattern="^(confirmed|rejected|merged)$")
    resolved_by: str
    merge_target_id: Optional[int] = None


class MergeRequest(BaseModel):
    """Request to merge features."""
    source_feature_id: int
    target_feature_id: int
    resolved_by: str


# ============== Priority Boost Endpoints ==============

@router.get("/boosts/allowance")
async def get_boost_allowance(
    customer_id: str = Query(..., description="Customer identifier"),
    db: AsyncSession = Depends(get_db),
):
    """Get current boost allowance status for customer."""
    service = PriorityBoostService(db)
    return await service.get_allowance_status(customer_id)


@router.post("/boosts", response_model=BoostResponse)
async def use_boost(
    request: BoostRequest,
    customer_id: str = Query(..., description="Customer identifier"),
    db: AsyncSession = Depends(get_db),
):
    """Use a priority boost on a feature request."""
    service = PriorityBoostService(db)
    result = await service.use_boost(
        customer_id=customer_id,
        feature_request_id=request.feature_request_id,
        feature_title=request.feature_title,
        current_priority=request.current_priority,
        reason=request.reason,
    )
    return result


@router.get("/boosts/history")
async def get_boost_history(
    customer_id: str = Query(..., description="Customer identifier"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get boost history for customer."""
    service = PriorityBoostService(db)
    return await service.get_boost_history(customer_id, limit)


@router.get("/boosts/active")
async def get_active_boosts(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get all currently active boosted features."""
    service = PriorityBoostService(db)
    boosts = await service.get_boosted_features(project_id)
    return {"active_boosts": boosts, "count": len(boosts)}


@router.post("/boosts/{boost_id}/complete")
async def complete_boost(
    boost_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Mark a boost as completed (feature delivered)."""
    service = PriorityBoostService(db)
    return await service.complete_boost(boost_id)


@router.post("/boosts/expire-old")
async def expire_old_boosts(
    db: AsyncSession = Depends(get_db),
):
    """Expire boosts that have passed their expiration date."""
    service = PriorityBoostService(db)
    count = await service.expire_old_boosts()
    return {"expired_count": count, "message": f"Expired {count} boosts"}


# ============== Impact Preview Endpoints (Felix) ==============

@router.post("/features/{feature_id}/impact")
async def analyze_feature_impact(
    feature_id: int,
    request: ImpactRequest,
    db: AsyncSession = Depends(get_db),
):
    """Analyze feature request impact using Felix agent."""
    service = ImpactPreviewService(db)
    return await service.analyze_feature(
        feature_request_id=feature_id,
        title=request.title,
        description=request.description,
        project_id=request.project_id,
        context=request.context,
        force_refresh=request.force_refresh,
    )


@router.get("/features/{feature_id}/impact")
async def get_feature_impact(
    feature_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get cached impact preview for a feature."""
    service = ImpactPreviewService(db)
    # Try to get cached
    result = await service.analyze_feature(
        feature_request_id=feature_id,
        title="",  # Will use cache if available
        description="",
        force_refresh=False,
    )
    return result


@router.delete("/features/{feature_id}/impact/cache")
async def invalidate_impact_cache(
    feature_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Invalidate cached impact preview."""
    service = ImpactPreviewService(db)
    success = await service.invalidate_cache(feature_id)
    return {"success": success, "feature_id": feature_id}


@router.get("/impact/summary")
async def get_impact_summary(
    project_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get summary of recent impact analyses."""
    service = ImpactPreviewService(db)
    return await service.get_impact_summary(project_id, limit)


# ============== Duplicate Detection Endpoints ==============

@router.post("/features/{feature_id}/check-duplicates")
async def check_for_duplicates(
    feature_id: int,
    request: DuplicateCheckRequest,
    db: AsyncSession = Depends(get_db),
):
    """Check if a feature request has duplicates."""
    service = DuplicateDetectorService(db)
    return await service.check_for_duplicates(
        feature_id=feature_id,
        title=request.title,
        description=request.description,
        project_id=request.project_id,
        auto_record=request.auto_record,
    )


@router.post("/features/{feature_id}/index")
async def index_feature(
    feature_id: int,
    title: str = Query(...),
    description: str = Query(...),
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Index a feature for similarity search."""
    service = DuplicateDetectorService(db)
    success = await service.index_feature(
        feature_id=feature_id,
        title=title,
        description=description,
        project_id=project_id,
    )
    return {"success": success, "feature_id": feature_id}


@router.get("/features/similar")
async def find_similar_features(
    feature_id: int = Query(...),
    title: str = Query(...),
    description: str = Query(...),
    project_id: Optional[int] = None,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Find similar features to a given feature."""
    service = DuplicateDetectorService(db)
    similar = await service.find_similar(
        feature_id=feature_id,
        title=title,
        description=description,
        project_id=project_id,
        limit=limit,
    )
    return {"feature_id": feature_id, "similar": similar, "count": len(similar)}


@router.get("/duplicates/pending")
async def get_pending_duplicates(
    project_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get pending duplicate detections for review."""
    service = DuplicateDetectorService(db)
    duplicates = await service.get_pending_duplicates(project_id, limit)
    return {"duplicates": duplicates, "count": len(duplicates)}


@router.post("/duplicates/{duplicate_id}/resolve")
async def resolve_duplicate(
    duplicate_id: UUID,
    request: DuplicateResolveRequest,
    db: AsyncSession = Depends(get_db),
):
    """Resolve a duplicate detection (confirm, reject, or merge)."""
    service = DuplicateDetectorService(db)
    return await service.resolve_duplicate(
        duplicate_id=duplicate_id,
        resolution=request.resolution,
        resolved_by=request.resolved_by,
        merge_target_id=request.merge_target_id,
    )


@router.post("/features/merge")
async def merge_features(
    request: MergeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Merge duplicate features."""
    service = DuplicateDetectorService(db)
    return await service.merge_features(
        source_feature_id=request.source_feature_id,
        target_feature_id=request.target_feature_id,
        resolved_by=request.resolved_by,
    )


@router.get("/duplicates/statistics")
async def get_duplicate_statistics(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get duplicate detection statistics."""
    service = DuplicateDetectorService(db)
    return await service.get_statistics(project_id)
