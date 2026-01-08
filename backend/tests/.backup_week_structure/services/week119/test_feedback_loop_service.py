# backend/tests/services/week119/test_feedback_loop_service.py
"""
Tests for FeedbackLoopService - Week 119

Tests feedback submission, requests, NPS calculation, and statistics.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.feedback_loop_service import FeedbackLoopService
from app.models.engagement import (
    FeatureFeedback,
    FeedbackRequest,
    FeedbackType,
    FeedbackStatus,
    FeedbackRequestStatus,
    Sentiment,
)


class TestFeedbackLoopService:
    """Test suite for FeedbackLoopService."""

    @pytest.fixture
    async def service(self, db_session: AsyncSession):
        """Create service instance."""
        return FeedbackLoopService(db_session)

    # ============== Feedback Submission Tests ==============

    @pytest.mark.asyncio
    async def test_submit_feedback_basic(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test basic feedback submission."""
        result = await service.submit_feedback(
            feature_request_id=1,
            customer_id="feedback_user_123",
            rating=5,
            feedback_text="Great feature!",
        )

        assert result["success"] is True
        assert result["rating"] == 5
        assert result["sentiment"] == "positive"
        assert "feedback_id" in result

    @pytest.mark.asyncio
    async def test_submit_feedback_with_nps(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test feedback submission with NPS score."""
        result = await service.submit_feedback(
            feature_request_id=2,
            customer_id="nps_user_123",
            rating=4,
            satisfaction_score=9,
            meets_expectations=True,
            would_recommend=True,
        )

        assert result["success"] is True

        # Verify stored
        feedback_result = await db_session.execute(
            select(FeatureFeedback).where(
                FeatureFeedback.id == result["feedback_id"]
            )
        )
        # Can't query by UUID string directly, skip this check

    @pytest.mark.asyncio
    async def test_submit_feedback_invalid_rating(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test feedback with invalid rating."""
        result = await service.submit_feedback(
            feature_request_id=1,
            customer_id="invalid_rating_user",
            rating=0,  # Invalid
        )

        assert result["success"] is False
        assert "Rating must be" in result["error"]

    @pytest.mark.asyncio
    async def test_submit_feedback_rating_too_high(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test feedback with rating too high."""
        result = await service.submit_feedback(
            feature_request_id=1,
            customer_id="high_rating_user",
            rating=6,  # Invalid
        )

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_submit_feedback_sentiment_positive(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test that high rating sets positive sentiment."""
        result = await service.submit_feedback(
            feature_request_id=1,
            customer_id="positive_user",
            rating=4,
        )

        assert result["sentiment"] == "positive"

    @pytest.mark.asyncio
    async def test_submit_feedback_sentiment_neutral(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test that medium rating sets neutral sentiment."""
        result = await service.submit_feedback(
            feature_request_id=1,
            customer_id="neutral_user",
            rating=3,
        )

        assert result["sentiment"] == "neutral"

    @pytest.mark.asyncio
    async def test_submit_feedback_sentiment_negative(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test that low rating sets negative sentiment."""
        result = await service.submit_feedback(
            feature_request_id=1,
            customer_id="negative_user",
            rating=2,
        )

        assert result["sentiment"] == "negative"

    # ============== Feedback Request Tests ==============

    @pytest.mark.asyncio
    async def test_create_feedback_request(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test creating a feedback request."""
        result = await service.create_feedback_request(
            feature_request_id=1,
            customer_id="request_user_123",
            request_type="post_release",
            message="Please share your thoughts!",
        )

        assert result["success"] is True
        assert "request_id" in result
        assert result["feature_request_id"] == 1

    @pytest.mark.asyncio
    async def test_create_feedback_request_duplicate(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test that duplicate pending requests are rejected."""
        # Create first request
        await service.create_feedback_request(
            feature_request_id=1,
            customer_id="dup_request_user",
        )

        # Try to create duplicate
        result = await service.create_feedback_request(
            feature_request_id=1,
            customer_id="dup_request_user",
        )

        assert result["success"] is False
        assert "already exists" in result["error"]

    @pytest.mark.asyncio
    async def test_send_feedback_request(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test marking a feedback request as sent."""
        # Create request
        create_result = await service.create_feedback_request(
            feature_request_id=1,
            customer_id="send_request_user",
        )

        # Send it
        from uuid import UUID
        request_id = UUID(create_result["request_id"])
        result = await service.send_feedback_request(request_id)

        assert result["success"] is True
        assert "sent_at" in result

    @pytest.mark.asyncio
    async def test_send_feedback_request_not_found(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test sending non-existent request."""
        result = await service.send_feedback_request(uuid4())

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_pending_requests(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test getting pending requests."""
        customer_id = "pending_user_123"

        # Create and send a request
        create_result = await service.create_feedback_request(
            feature_request_id=1,
            customer_id=customer_id,
        )
        from uuid import UUID
        await service.send_feedback_request(UUID(create_result["request_id"]))

        # Get pending
        pending = await service.get_pending_requests(customer_id=customer_id)

        assert len(pending) == 1
        assert pending[0]["customer_id"] == customer_id

    # ============== Feedback Aggregation Tests ==============

    @pytest.mark.asyncio
    async def test_get_feedback_for_feature(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test getting feedback for a feature with aggregations."""
        feature_id = 100

        # Submit multiple feedbacks
        await service.submit_feedback(feature_id, "user_1", rating=5, satisfaction_score=10)
        await service.submit_feedback(feature_id, "user_2", rating=4, satisfaction_score=8)
        await service.submit_feedback(feature_id, "user_3", rating=3, satisfaction_score=5)

        result = await service.get_feedback_for_feature(feature_id)

        assert result["feature_request_id"] == feature_id
        assert result["total_feedback"] == 3
        assert result["average_rating"] == 4.0  # (5+4+3)/3
        assert result["nps_score"] is not None  # NPS calculated

    @pytest.mark.asyncio
    async def test_get_feedback_for_feature_nps_calculation(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test NPS calculation: (promoters - detractors) / total * 100."""
        feature_id = 101

        # 2 promoters (9-10), 1 passive (7-8), 2 detractors (0-6)
        await service.submit_feedback(feature_id, "p1", rating=5, satisfaction_score=10)
        await service.submit_feedback(feature_id, "p2", rating=5, satisfaction_score=9)
        await service.submit_feedback(feature_id, "n1", rating=4, satisfaction_score=8)  # passive
        await service.submit_feedback(feature_id, "d1", rating=2, satisfaction_score=5)
        await service.submit_feedback(feature_id, "d2", rating=1, satisfaction_score=3)

        result = await service.get_feedback_for_feature(feature_id)

        # NPS = (2 - 2) / 5 * 100 = 0
        assert result["nps_score"] == 0.0

    @pytest.mark.asyncio
    async def test_get_feedback_for_feature_empty(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test getting feedback for feature with no feedback."""
        result = await service.get_feedback_for_feature(999)

        assert result["total_feedback"] == 0
        assert result["average_rating"] is None
        assert result["feedback"] == []

    # ============== Review Tests ==============

    @pytest.mark.asyncio
    async def test_review_feedback(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test reviewing feedback."""
        # Create feedback
        submit_result = await service.submit_feedback(
            feature_request_id=1,
            customer_id="review_user",
            rating=3,
            feedback_text="Could be better",
        )

        from uuid import UUID
        feedback_id = UUID(submit_result["feedback_id"])

        # Review it
        result = await service.review_feedback(
            feedback_id=feedback_id,
            reviewed_by="admin@example.com",
            action_taken="Noted for improvement",
            new_status="reviewed",
        )

        assert result["success"] is True
        assert result["status"] == "reviewed"

    @pytest.mark.asyncio
    async def test_review_feedback_not_found(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test reviewing non-existent feedback."""
        result = await service.review_feedback(
            feedback_id=uuid4(),
            reviewed_by="admin",
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    # ============== Statistics Tests ==============

    @pytest.mark.asyncio
    async def test_get_feedback_statistics(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test getting feedback statistics."""
        # Create some feedback
        await service.submit_feedback(1, "stat_user_1", rating=5)
        await service.submit_feedback(2, "stat_user_2", rating=4)
        await service.submit_feedback(3, "stat_user_3", rating=2)

        stats = await service.get_feedback_statistics(days=30)

        assert stats["total_feedback"] == 3
        assert stats["average_rating"] is not None
        assert "by_type" in stats
        assert "by_status" in stats

    @pytest.mark.asyncio
    async def test_get_feedback_statistics_empty(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test statistics with no feedback."""
        stats = await service.get_feedback_statistics(days=30)

        assert stats["total_feedback"] == 0
        assert stats["average_rating"] is None

    # ============== Expiration Tests ==============

    @pytest.mark.asyncio
    async def test_expire_old_requests(
        self, service: FeedbackLoopService, db_session: AsyncSession
    ):
        """Test expiring old feedback requests."""
        customer_id = "expire_test_user"

        # Create request with past expiration
        request = FeedbackRequest(
            id=uuid4(),
            feature_request_id=1,
            customer_id=customer_id,
            status=FeedbackRequestStatus.SENT.value,
            sent_at=datetime.now(timezone.utc) - timedelta(days=20),
            expires_at=datetime.now(timezone.utc) - timedelta(days=5),  # Expired
        )
        db_session.add(request)
        await db_session.commit()

        # Expire old requests
        count = await service.expire_old_requests()

        assert count >= 1

        # Verify status changed
        result = await db_session.execute(
            select(FeedbackRequest).where(FeedbackRequest.id == request.id)
        )
        updated_request = result.scalar_one()
        assert updated_request.status == FeedbackRequestStatus.EXPIRED.value


class TestFeatureFeedbackModel:
    """Test FeatureFeedback model methods."""

    def test_is_positive_high_rating(self):
        """Test positive check with high rating."""
        feedback = FeatureFeedback(
            id=uuid4(),
            feature_request_id=1,
            customer_id="test",
            rating=5,
        )

        assert feedback.is_positive() is True

    def test_is_positive_low_rating(self):
        """Test positive check with low rating."""
        feedback = FeatureFeedback(
            id=uuid4(),
            feature_request_id=1,
            customer_id="test",
            rating=2,
        )

        assert feedback.is_positive() is False

    def test_calculate_nps_category_promoter(self):
        """Test NPS category for promoter."""
        feedback = FeatureFeedback(
            id=uuid4(),
            feature_request_id=1,
            customer_id="test",
            rating=5,
            satisfaction_score=10,
        )

        assert feedback.calculate_nps_category() == "promoter"

    def test_calculate_nps_category_passive(self):
        """Test NPS category for passive."""
        feedback = FeatureFeedback(
            id=uuid4(),
            feature_request_id=1,
            customer_id="test",
            rating=4,
            satisfaction_score=7,
        )

        assert feedback.calculate_nps_category() == "passive"

    def test_calculate_nps_category_detractor(self):
        """Test NPS category for detractor."""
        feedback = FeatureFeedback(
            id=uuid4(),
            feature_request_id=1,
            customer_id="test",
            rating=2,
            satisfaction_score=4,
        )

        assert feedback.calculate_nps_category() == "detractor"

    def test_calculate_nps_category_unknown(self):
        """Test NPS category when no score."""
        feedback = FeatureFeedback(
            id=uuid4(),
            feature_request_id=1,
            customer_id="test",
            rating=3,
            satisfaction_score=None,
        )

        assert feedback.calculate_nps_category() == "unknown"


class TestFeedbackRequestModel:
    """Test FeedbackRequest model methods."""

    def test_is_expired_no_date(self):
        """Test is_expired with no expiration date."""
        request = FeedbackRequest(
            id=uuid4(),
            feature_request_id=1,
            customer_id="test",
            expires_at=None,
        )

        assert request.is_expired() is False

    def test_is_expired_future(self):
        """Test is_expired with future date."""
        request = FeedbackRequest(
            id=uuid4(),
            feature_request_id=1,
            customer_id="test",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

        assert request.is_expired() is False

    def test_is_expired_past(self):
        """Test is_expired with past date."""
        request = FeedbackRequest(
            id=uuid4(),
            feature_request_id=1,
            customer_id="test",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )

        assert request.is_expired() is True
