# backend/app/api/portal_engagement.py
"""
Portal Engagement API - Week 119-120

Client Portal 2.0 Phase 3: Engagement
- Feedback Loop endpoints
- Gamification endpoints (badges, points, levels)
- Personalized Dashboard endpoints
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.feedback_loop_service import FeedbackLoopService
from app.services.gamification_service import GamificationService
from app.services.personalized_dashboard_service import PersonalizedDashboardService


router = APIRouter(prefix="/api/portal", tags=["Portal Engagement"])


# ============== Schemas ==============

class FeedbackSubmitRequest(BaseModel):
    """Submit feedback for a feature."""
    rating: int = Field(..., ge=1, le=5, description="1-5 star rating")
    feedback_text: Optional[str] = None
    satisfaction_score: Optional[int] = Field(None, ge=1, le=10)
    meets_expectations: Optional[bool] = None
    would_recommend: Optional[bool] = None
    improvement_suggestions: Optional[str] = None
    feedback_type: str = "general"
    tags: Optional[List[str]] = None
    project_id: Optional[int] = None


class FeedbackRequestCreate(BaseModel):
    """Create a feedback request."""
    request_type: str = "post_release"
    trigger_event: Optional[str] = None
    message: Optional[str] = None
    expires_in_days: int = 14
    project_id: Optional[int] = None


class ReviewFeedbackRequest(BaseModel):
    """Review feedback."""
    action_taken: Optional[str] = None
    new_status: str = "reviewed"


class AwardPointsRequest(BaseModel):
    """Award points to user."""
    action_type: str
    points: Optional[int] = None
    reason: Optional[str] = None
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None


class UpdatePreferencesRequest(BaseModel):
    """Update dashboard preferences."""
    layout: Optional[str] = None
    widgets_order: Optional[List[str]] = None
    hidden_widgets: Optional[List[str]] = None
    show_recommendations: Optional[bool] = None
    show_trending: Optional[bool] = None
    show_activity_feed: Optional[bool] = None
    show_badges: Optional[bool] = None
    show_stats: Optional[bool] = None
    email_digest: Optional[str] = None
    notify_feature_updates: Optional[bool] = None
    notify_new_badges: Optional[bool] = None
    notify_level_up: Optional[bool] = None
    interest_tags: Optional[List[str]] = None


# ============== Feedback Endpoints ==============

@router.post("/features/{feature_id}/feedback")
async def submit_feedback(
    feature_id: int,
    request: FeedbackSubmitRequest,
    customer_id: str = Query(..., description="Customer identifier"),
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback for a delivered feature."""
    service = FeedbackLoopService(db)
    result = await service.submit_feedback(
        feature_request_id=feature_id,
        customer_id=customer_id,
        **request.model_dump(),
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    # Also award gamification points
    gam_service = GamificationService(db)
    points_result = await gam_service.award_points(
        customer_id=customer_id,
        action_type="feedback",
        reference_id=str(feature_id),
        reference_type="feature",
    )
    result["gamification"] = points_result

    return result


@router.get("/features/{feature_id}/feedback")
async def get_feature_feedback(
    feature_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get all feedback for a feature with aggregations."""
    service = FeedbackLoopService(db)
    return await service.get_feedback_for_feature(feature_id, limit)


@router.post("/features/{feature_id}/feedback-request")
async def create_feedback_request(
    feature_id: int,
    request: FeedbackRequestCreate,
    customer_id: str = Query(..., description="Customer identifier"),
    db: AsyncSession = Depends(get_db),
):
    """Create a proactive feedback request."""
    service = FeedbackLoopService(db)
    return await service.create_feedback_request(
        feature_request_id=feature_id,
        customer_id=customer_id,
        **request.model_dump(),
    )


@router.post("/feedback-requests/{request_id}/send")
async def send_feedback_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Mark feedback request as sent."""
    service = FeedbackLoopService(db)
    return await service.send_feedback_request(request_id)


@router.get("/feedback/pending")
async def get_pending_feedback_requests(
    customer_id: Optional[str] = None,
    project_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get pending feedback requests."""
    service = FeedbackLoopService(db)
    return await service.get_pending_requests(customer_id, project_id, limit)


@router.post("/feedback/{feedback_id}/review")
async def review_feedback(
    feedback_id: UUID,
    request: ReviewFeedbackRequest,
    reviewed_by: str = Query(..., description="Reviewer identifier"),
    db: AsyncSession = Depends(get_db),
):
    """Review a feedback submission."""
    service = FeedbackLoopService(db)
    return await service.review_feedback(
        feedback_id=feedback_id,
        reviewed_by=reviewed_by,
        action_taken=request.action_taken,
        new_status=request.new_status,
    )


@router.get("/feedback/statistics")
async def get_feedback_statistics(
    project_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get feedback statistics."""
    service = FeedbackLoopService(db)
    return await service.get_feedback_statistics(project_id, days)


@router.post("/feedback/expire-old")
async def expire_old_feedback_requests(
    db: AsyncSession = Depends(get_db),
):
    """Expire old feedback requests."""
    service = FeedbackLoopService(db)
    count = await service.expire_old_requests()
    return {"expired_count": count, "message": f"Expired {count} feedback requests"}


# ============== Gamification Endpoints ==============

@router.get("/users/{customer_id}/profile")
async def get_user_profile(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get complete gamification profile for a user."""
    service = GamificationService(db)
    return await service.get_user_profile(customer_id)


@router.get("/users/{customer_id}/level")
async def get_user_level(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get user level information."""
    service = GamificationService(db)
    profile = await service.get_user_profile(customer_id)
    return profile["level"]


@router.post("/users/{customer_id}/points")
async def award_points(
    customer_id: str,
    request: AwardPointsRequest,
    db: AsyncSession = Depends(get_db),
):
    """Award points to a user."""
    service = GamificationService(db)
    return await service.award_points(
        customer_id=customer_id,
        **request.model_dump(),
    )


@router.get("/users/{customer_id}/points/history")
async def get_points_history(
    customer_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get points transaction history."""
    service = GamificationService(db)
    return await service.get_points_history(customer_id, limit)


@router.get("/badges")
async def get_all_badges(
    include_secret: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Get all available badges."""
    service = GamificationService(db)
    badges = await service.get_all_badges(include_secret)
    return {"badges": badges, "count": len(badges)}


@router.post("/badges/initialize")
async def initialize_default_badges(
    db: AsyncSession = Depends(get_db),
):
    """Initialize default badge definitions."""
    service = GamificationService(db)
    count = await service.initialize_default_badges()
    return {"initialized": count, "message": f"Initialized {count} badges"}


@router.get("/users/{customer_id}/badges")
async def get_user_badges(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all badges earned by a user."""
    service = GamificationService(db)
    badges = await service.get_user_badges(customer_id)
    return {"badges": badges, "count": len(badges)}


@router.post("/users/{customer_id}/badges/check")
async def check_and_award_badges(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Check and award any newly earned badges."""
    service = GamificationService(db)
    new_badges = await service.check_and_award_badges(customer_id)
    return {"new_badges": new_badges, "count": len(new_badges)}


@router.post("/users/{customer_id}/badges/{badge_name}")
async def award_badge_manually(
    customer_id: str,
    badge_name: str,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Manually award a badge to a user."""
    service = GamificationService(db)
    return await service.award_badge_manually(customer_id, badge_name, reason)


@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    timeframe: str = Query("all_time"),
    db: AsyncSession = Depends(get_db),
):
    """Get points leaderboard."""
    service = GamificationService(db)
    leaderboard = await service.get_leaderboard(limit, timeframe)
    return {"leaderboard": leaderboard, "count": len(leaderboard)}


@router.get("/gamification/statistics")
async def get_gamification_statistics(
    db: AsyncSession = Depends(get_db),
):
    """Get overall gamification statistics."""
    service = GamificationService(db)
    return await service.get_gamification_statistics()


# ============== Dashboard Endpoints ==============

@router.get("/users/{customer_id}/dashboard")
async def get_dashboard(
    customer_id: str,
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get personalized dashboard data."""
    service = PersonalizedDashboardService(db)
    return await service.get_dashboard_data(customer_id, project_id)


@router.get("/users/{customer_id}/preferences")
async def get_preferences(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get user dashboard preferences."""
    service = PersonalizedDashboardService(db)
    return await service.get_preferences(customer_id)


@router.put("/users/{customer_id}/preferences")
async def update_preferences(
    customer_id: str,
    request: UpdatePreferencesRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update user dashboard preferences."""
    service = PersonalizedDashboardService(db)
    return await service.update_preferences(
        customer_id=customer_id,
        **request.model_dump(exclude_none=True),
    )


@router.post("/users/{customer_id}/watch/{feature_id}")
async def watch_feature(
    customer_id: str,
    feature_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Add a feature to watch list."""
    service = PersonalizedDashboardService(db)
    return await service.watch_feature(customer_id, feature_id)


@router.delete("/users/{customer_id}/watch/{feature_id}")
async def unwatch_feature(
    customer_id: str,
    feature_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Remove a feature from watch list."""
    service = PersonalizedDashboardService(db)
    return await service.unwatch_feature(customer_id, feature_id)


@router.get("/users/{customer_id}/recommendations")
async def get_recommendations(
    customer_id: str,
    project_id: Optional[int] = None,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get personalized feature recommendations."""
    service = PersonalizedDashboardService(db)
    recs = await service.get_recommendations(customer_id, project_id, limit)
    return {"recommendations": recs, "count": len(recs)}


@router.post("/users/{customer_id}/recommendations/generate")
async def generate_recommendations(
    customer_id: str,
    project_id: Optional[int] = None,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Generate new personalized recommendations."""
    service = PersonalizedDashboardService(db)
    recs = await service.generate_recommendations(customer_id, project_id, limit)
    return {"recommendations": recs, "count": len(recs)}


@router.post("/recommendations/{recommendation_id}/dismiss")
async def dismiss_recommendation(
    recommendation_id: UUID,
    customer_id: str = Query(..., description="Customer identifier"),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss a recommendation."""
    service = PersonalizedDashboardService(db)
    return await service.dismiss_recommendation(customer_id, recommendation_id)


@router.get("/recommendations/statistics")
async def get_recommendation_statistics(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get recommendation statistics."""
    service = PersonalizedDashboardService(db)
    return await service.get_recommendation_statistics(project_id)
