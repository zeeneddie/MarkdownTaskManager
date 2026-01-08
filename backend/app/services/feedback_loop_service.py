# backend/app/services/feedback_loop_service.py
"""
Feedback Loop Service - Week 119-120

Manages post-release feedback collection and analysis.
- Collect customer feedback on delivered features
- Send feedback requests proactively
- Analyze sentiment and satisfaction
- Track NPS scores
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.models.engagement import (
    FeatureFeedback,
    FeedbackRequest,
    FeedbackType,
    FeedbackStatus,
    FeedbackRequestStatus,
    Sentiment,
)


class FeedbackLoopService:
    """Service for managing feature feedback."""

    # Points awarded for feedback
    FEEDBACK_POINTS = 15

    def __init__(self, db: AsyncSession):
        self.db = db

    async def submit_feedback(
        self,
        feature_request_id: int,
        customer_id: str,
        rating: int,
        feedback_text: Optional[str] = None,
        satisfaction_score: Optional[int] = None,
        meets_expectations: Optional[bool] = None,
        would_recommend: Optional[bool] = None,
        improvement_suggestions: Optional[str] = None,
        feedback_type: str = "general",
        tags: Optional[List[str]] = None,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Submit feedback for a delivered feature."""
        # Validate rating
        if not 1 <= rating <= 5:
            return {"success": False, "error": "Rating must be between 1 and 5"}

        # Determine sentiment from rating
        if rating >= 4:
            sentiment = Sentiment.POSITIVE.value
        elif rating >= 3:
            sentiment = Sentiment.NEUTRAL.value
        else:
            sentiment = Sentiment.NEGATIVE.value

        # Create feedback record
        feedback = FeatureFeedback(
            id=uuid4(),
            feature_request_id=feature_request_id,
            project_id=project_id,
            customer_id=customer_id,
            rating=rating,
            satisfaction_score=satisfaction_score,
            meets_expectations=meets_expectations,
            would_recommend=would_recommend,
            feedback_text=feedback_text,
            improvement_suggestions=improvement_suggestions,
            feedback_type=feedback_type,
            sentiment=sentiment,
            tags=tags or [],
            status=FeedbackStatus.PENDING.value,
        )

        self.db.add(feedback)

        # Check if this responds to a feedback request
        await self._link_to_request(feedback)

        await self.db.commit()
        await self.db.refresh(feedback)

        return {
            "success": True,
            "feedback_id": str(feedback.id),
            "feature_request_id": feature_request_id,
            "rating": rating,
            "sentiment": sentiment,
            "points_earned": self.FEEDBACK_POINTS,
            "message": "Thank you for your feedback!",
        }

    async def _link_to_request(self, feedback: FeatureFeedback) -> None:
        """Link feedback to any pending request."""
        result = await self.db.execute(
            select(FeedbackRequest).where(
                and_(
                    FeedbackRequest.feature_request_id == feedback.feature_request_id,
                    FeedbackRequest.customer_id == feedback.customer_id,
                    FeedbackRequest.status == FeedbackRequestStatus.SENT.value,
                )
            )
        )
        request = result.scalar_one_or_none()

        if request:
            request.status = FeedbackRequestStatus.RESPONDED.value
            request.responded_at = datetime.utcnow()
            request.feedback_id = feedback.id

    async def create_feedback_request(
        self,
        feature_request_id: int,
        customer_id: str,
        request_type: str = "post_release",
        trigger_event: Optional[str] = None,
        message: Optional[str] = None,
        expires_in_days: int = 14,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a proactive feedback request."""
        # Check for existing pending request
        result = await self.db.execute(
            select(FeedbackRequest).where(
                and_(
                    FeedbackRequest.feature_request_id == feature_request_id,
                    FeedbackRequest.customer_id == customer_id,
                    FeedbackRequest.status.in_([
                        FeedbackRequestStatus.PENDING.value,
                        FeedbackRequestStatus.SENT.value,
                    ]),
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            return {
                "success": False,
                "error": "Feedback request already exists",
                "request_id": str(existing.id),
            }

        # Create request
        request = FeedbackRequest(
            id=uuid4(),
            feature_request_id=feature_request_id,
            project_id=project_id,
            customer_id=customer_id,
            request_type=request_type,
            trigger_event=trigger_event,
            message=message or f"We'd love to hear your thoughts on the recently delivered feature!",
            status=FeedbackRequestStatus.PENDING.value,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
        )

        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)

        return {
            "success": True,
            "request_id": str(request.id),
            "feature_request_id": feature_request_id,
            "customer_id": customer_id,
            "expires_at": request.expires_at.isoformat(),
        }

    async def send_feedback_request(self, request_id: UUID) -> Dict[str, Any]:
        """Mark feedback request as sent."""
        result = await self.db.execute(
            select(FeedbackRequest).where(FeedbackRequest.id == request_id)
        )
        request = result.scalar_one_or_none()

        if not request:
            return {"success": False, "error": "Request not found"}

        if request.status != FeedbackRequestStatus.PENDING.value:
            return {"success": False, "error": f"Request is not pending (status: {request.status})"}

        request.status = FeedbackRequestStatus.SENT.value
        request.sent_at = datetime.utcnow()

        await self.db.commit()

        return {
            "success": True,
            "request_id": str(request.id),
            "sent_at": request.sent_at.isoformat(),
        }

    async def get_pending_requests(
        self,
        customer_id: Optional[str] = None,
        project_id: Optional[int] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get pending feedback requests."""
        query = select(FeedbackRequest).where(
            FeedbackRequest.status == FeedbackRequestStatus.SENT.value
        ).order_by(FeedbackRequest.created_at.desc()).limit(limit)

        if customer_id:
            query = query.where(FeedbackRequest.customer_id == customer_id)
        if project_id:
            query = query.where(FeedbackRequest.project_id == project_id)

        result = await self.db.execute(query)
        requests = result.scalars().all()

        return [
            {
                "request_id": str(r.id),
                "feature_request_id": r.feature_request_id,
                "customer_id": r.customer_id,
                "message": r.message,
                "sent_at": r.sent_at.isoformat() if r.sent_at else None,
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                "is_expired": r.is_expired(),
            }
            for r in requests
        ]

    async def get_feedback_for_feature(
        self,
        feature_request_id: int,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get all feedback for a feature with aggregations."""
        result = await self.db.execute(
            select(FeatureFeedback).where(
                FeatureFeedback.feature_request_id == feature_request_id
            ).order_by(FeatureFeedback.created_at.desc()).limit(limit)
        )
        feedback_list = result.scalars().all()

        if not feedback_list:
            return {
                "feature_request_id": feature_request_id,
                "total_feedback": 0,
                "average_rating": None,
                "nps_score": None,
                "feedback": [],
            }

        # Calculate aggregations
        total = len(feedback_list)
        avg_rating = sum(f.rating for f in feedback_list) / total

        # Calculate NPS
        nps_scores = [f.satisfaction_score for f in feedback_list if f.satisfaction_score]
        nps_score = None
        if nps_scores:
            promoters = sum(1 for s in nps_scores if s >= 9)
            detractors = sum(1 for s in nps_scores if s <= 6)
            nps_score = ((promoters - detractors) / len(nps_scores)) * 100

        # Sentiment breakdown
        sentiment_counts = {
            "positive": sum(1 for f in feedback_list if f.sentiment == Sentiment.POSITIVE.value),
            "neutral": sum(1 for f in feedback_list if f.sentiment == Sentiment.NEUTRAL.value),
            "negative": sum(1 for f in feedback_list if f.sentiment == Sentiment.NEGATIVE.value),
        }

        return {
            "feature_request_id": feature_request_id,
            "total_feedback": total,
            "average_rating": round(avg_rating, 2),
            "nps_score": round(nps_score, 1) if nps_score is not None else None,
            "sentiment_breakdown": sentiment_counts,
            "meets_expectations_rate": self._calculate_rate(feedback_list, "meets_expectations"),
            "would_recommend_rate": self._calculate_rate(feedback_list, "would_recommend"),
            "feedback": [
                {
                    "id": str(f.id),
                    "customer_id": f.customer_id,
                    "rating": f.rating,
                    "sentiment": f.sentiment,
                    "feedback_text": f.feedback_text,
                    "created_at": f.created_at.isoformat(),
                }
                for f in feedback_list[:10]  # Only return first 10
            ],
        }

    def _calculate_rate(self, feedback_list: List[FeatureFeedback], field: str) -> Optional[float]:
        """Calculate percentage rate for a boolean field."""
        values = [getattr(f, field) for f in feedback_list if getattr(f, field) is not None]
        if not values:
            return None
        return round((sum(1 for v in values if v) / len(values)) * 100, 1)

    async def review_feedback(
        self,
        feedback_id: UUID,
        reviewed_by: str,
        action_taken: Optional[str] = None,
        new_status: str = "reviewed",
    ) -> Dict[str, Any]:
        """Review a feedback submission."""
        result = await self.db.execute(
            select(FeatureFeedback).where(FeatureFeedback.id == feedback_id)
        )
        feedback = result.scalar_one_or_none()

        if not feedback:
            return {"success": False, "error": "Feedback not found"}

        feedback.status = new_status
        feedback.reviewed_by = reviewed_by
        feedback.reviewed_at = datetime.utcnow()
        if action_taken:
            feedback.action_taken = action_taken

        await self.db.commit()

        return {
            "success": True,
            "feedback_id": str(feedback.id),
            "status": new_status,
            "reviewed_by": reviewed_by,
        }

    async def get_feedback_statistics(
        self,
        project_id: Optional[int] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get feedback statistics."""
        since = datetime.utcnow() - timedelta(days=days)

        query = select(FeatureFeedback).where(
            FeatureFeedback.created_at >= since
        )
        if project_id:
            query = query.where(FeatureFeedback.project_id == project_id)

        result = await self.db.execute(query)
        feedback_list = result.scalars().all()

        if not feedback_list:
            return {
                "period_days": days,
                "total_feedback": 0,
                "average_rating": None,
                "nps_score": None,
            }

        total = len(feedback_list)
        avg_rating = sum(f.rating for f in feedback_list) / total

        # Calculate NPS
        nps_scores = [f.satisfaction_score for f in feedback_list if f.satisfaction_score]
        nps_score = None
        if nps_scores:
            promoters = sum(1 for s in nps_scores if s >= 9)
            detractors = sum(1 for s in nps_scores if s <= 6)
            nps_score = ((promoters - detractors) / len(nps_scores)) * 100

        # By type
        by_type = {}
        for f in feedback_list:
            by_type[f.feedback_type] = by_type.get(f.feedback_type, 0) + 1

        # By status
        by_status = {}
        for f in feedback_list:
            by_status[f.status] = by_status.get(f.status, 0) + 1

        return {
            "period_days": days,
            "total_feedback": total,
            "average_rating": round(avg_rating, 2),
            "nps_score": round(nps_score, 1) if nps_score is not None else None,
            "by_type": by_type,
            "by_status": by_status,
            "pending_review": by_status.get(FeedbackStatus.PENDING.value, 0),
        }

    async def expire_old_requests(self) -> int:
        """Expire feedback requests past their expiration date."""
        result = await self.db.execute(
            select(FeedbackRequest).where(
                and_(
                    FeedbackRequest.status == FeedbackRequestStatus.SENT.value,
                    FeedbackRequest.expires_at < datetime.utcnow(),
                )
            )
        )
        requests = result.scalars().all()

        for request in requests:
            request.status = FeedbackRequestStatus.EXPIRED.value

        await self.db.commit()
        return len(requests)
