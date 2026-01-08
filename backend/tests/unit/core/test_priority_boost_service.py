# backend/tests/services/week118/test_priority_boost_service.py
"""
Tests for PriorityBoostService - Week 118 Client Portal 2.0 Phase 2
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.priority_boost_service import PriorityBoostService
from app.models.portal_enhancements import BoostAllowance, PriorityBoost, CustomerTier, BoostStatus


class TestPriorityBoostService:
    """Test suite for PriorityBoostService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mock db."""
        return PriorityBoostService(mock_db)

    # ============== Allowance Tests ==============

    @pytest.mark.asyncio
    async def test_get_or_create_allowance_creates_new(self, service, mock_db):
        """Test creating new allowance when none exists."""
        # Mock no existing allowance
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock refresh to set expected values
        async def mock_refresh(obj):
            obj.id = uuid4()
            obj.remaining_boosts = 1

        mock_db.refresh.side_effect = mock_refresh

        allowance = await service.get_or_create_allowance("customer_123")

        assert allowance is not None
        assert allowance.customer_id == "customer_123"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_allowance_returns_existing(self, service, mock_db):
        """Test returning existing allowance."""
        existing = BoostAllowance(
            id=uuid4(),
            customer_id="customer_123",
            period_start=date.today().replace(day=1),
            period_end=date.today().replace(day=28),
            total_boosts=3,
            used_boosts=1,
            remaining_boosts=2,
            tier=CustomerTier.PREMIUM.value,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute = AsyncMock(return_value=mock_result)

        allowance = await service.get_or_create_allowance("customer_123")

        assert allowance == existing
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_allowance_status(self, service, mock_db):
        """Test getting allowance status with active boosts."""
        allowance = BoostAllowance(
            id=uuid4(),
            customer_id="customer_123",
            period_start=date.today().replace(day=1),
            period_end=date.today().replace(day=28),
            total_boosts=3,
            used_boosts=1,
            remaining_boosts=2,
            tier=CustomerTier.PREMIUM.value,
        )

        # First call returns allowance (or creates one)
        # Second call returns active boosts
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = allowance

        active_boost = PriorityBoost(
            id=uuid4(),
            feature_request_id=42,
            feature_title="Test Feature",
            customer_id="customer_123",
            status=BoostStatus.ACTIVE.value,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30),
        )

        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.all.return_value = [active_boost]

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        status = await service.get_allowance_status("customer_123")

        assert status["customer_id"] == "customer_123"
        assert status["quota"]["total"] == 3
        assert status["quota"]["remaining"] == 2
        assert status["can_boost"] is True
        assert len(status["active_boosts"]) == 1

    # ============== Boost Usage Tests ==============

    @pytest.mark.asyncio
    async def test_use_boost_success(self, service, mock_db):
        """Test successfully using a boost."""
        allowance = BoostAllowance(
            id=uuid4(),
            customer_id="customer_123",
            period_start=date.today().replace(day=1),
            period_end=date.today().replace(day=28),
            total_boosts=3,
            used_boosts=0,
            remaining_boosts=3,
            tier=CustomerTier.PREMIUM.value,
        )

        # Mock allowance lookup
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = allowance

        # Mock no existing boost
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        async def mock_refresh(obj):
            if hasattr(obj, 'boosted_priority'):
                obj.id = uuid4()
                obj.expires_at = date.today() + timedelta(days=30)

        mock_db.refresh.side_effect = mock_refresh

        result = await service.use_boost(
            customer_id="customer_123",
            feature_request_id=42,
            feature_title="Test Feature",
            current_priority="P3",
        )

        assert result["success"] is True
        assert result["boosted_priority"] == "P2"
        assert result["remaining_boosts"] == 2

    @pytest.mark.asyncio
    async def test_use_boost_no_remaining(self, service, mock_db):
        """Test boost fails when no remaining boosts."""
        allowance = BoostAllowance(
            id=uuid4(),
            customer_id="customer_123",
            period_start=date.today().replace(day=1),
            period_end=date.today().replace(day=28),
            total_boosts=1,
            used_boosts=1,
            remaining_boosts=0,
            tier=CustomerTier.STANDARD.value,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = allowance
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.use_boost(
            customer_id="customer_123",
            feature_request_id=42,
        )

        assert result["success"] is False
        assert result["error"] == "no_boosts_remaining"

    @pytest.mark.asyncio
    async def test_use_boost_already_boosted(self, service, mock_db):
        """Test boost fails when feature already boosted."""
        allowance = BoostAllowance(
            id=uuid4(),
            customer_id="customer_123",
            period_start=date.today().replace(day=1),
            period_end=date.today().replace(day=28),
            total_boosts=3,
            used_boosts=1,
            remaining_boosts=2,
            tier=CustomerTier.PREMIUM.value,
        )

        existing_boost = PriorityBoost(
            id=uuid4(),
            feature_request_id=42,
            customer_id="customer_123",
            status=BoostStatus.ACTIVE.value,
        )

        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = allowance

        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = existing_boost

        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        result = await service.use_boost(
            customer_id="customer_123",
            feature_request_id=42,
        )

        assert result["success"] is False
        assert result["error"] == "already_boosted"

    # ============== Priority Calculation Tests ==============

    def test_calculate_boosted_priority(self, service):
        """Test priority calculation moves up one level."""
        assert service._calculate_boosted_priority("P4") == "P3"
        assert service._calculate_boosted_priority("P3") == "P2"
        assert service._calculate_boosted_priority("P2") == "P1"
        assert service._calculate_boosted_priority("P1") == "P0"
        assert service._calculate_boosted_priority("P0") == "P0"  # Can't go higher
        assert service._calculate_boosted_priority(None) == "P2"  # Default
        assert service._calculate_boosted_priority("invalid") == "P2"  # Default

    # ============== Tier Quota Tests ==============

    def test_tier_quotas(self):
        """Test tier quota values."""
        assert BoostAllowance.get_tier_quota(CustomerTier.STANDARD.value) == 1
        assert BoostAllowance.get_tier_quota(CustomerTier.PREMIUM.value) == 3
        assert BoostAllowance.get_tier_quota(CustomerTier.ENTERPRISE.value) == 10
        assert BoostAllowance.get_tier_quota("unknown") == 1  # Default

    # ============== Expiration Tests ==============

    @pytest.mark.asyncio
    async def test_expire_old_boosts(self, service, mock_db):
        """Test expiring old boosts."""
        expired_boost = PriorityBoost(
            id=uuid4(),
            feature_request_id=42,
            customer_id="customer_123",
            status=BoostStatus.ACTIVE.value,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [expired_boost]
        mock_db.execute = AsyncMock(return_value=mock_result)

        count = await service.expire_old_boosts()

        assert count == 1
        assert expired_boost.status == BoostStatus.EXPIRED.value
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_boost(self, service, mock_db):
        """Test completing a boost."""
        boost = PriorityBoost(
            id=uuid4(),
            feature_request_id=42,
            customer_id="customer_123",
            status=BoostStatus.ACTIVE.value,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = boost
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.complete_boost(boost.id)

        assert result["success"] is True
        assert boost.status == BoostStatus.COMPLETED.value
        assert boost.completed_at is not None
