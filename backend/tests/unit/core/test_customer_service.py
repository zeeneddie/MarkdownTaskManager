"""
Unit tests for CustomerService

Week 143 - Fase 28: Data Architecture Enhancement
Tests for Customer CRUD operations, tier management, and relationship handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.services.customer_service import (
    CustomerService,
    CustomerTier,
    TIER_LIMITS,
    CustomerStats,
)
from app.models.customer import Customer, ProjectApplication
from app.models.project import Project


class TestCustomerTier:
    """Test CustomerTier enum and tier limits."""

    def test_all_tiers_exist(self):
        """Test that all expected tiers exist."""
        expected_tiers = ["FREE", "BASIC", "STANDARD", "PROFESSIONAL", "PREMIUM"]
        for tier in expected_tiers:
            assert CustomerTier(tier) is not None

    def test_tier_limits_defined(self):
        """Test that all tiers have limits defined."""
        for tier in CustomerTier:
            assert tier in TIER_LIMITS
            limits = TIER_LIMITS[tier]
            assert "max_projects" in limits
            assert "max_applications" in limits
            assert "extraction_tier" in limits

    def test_premium_has_unlimited_projects(self):
        """Test that premium tier has no project limit."""
        limits = TIER_LIMITS[CustomerTier.PREMIUM]
        assert limits["max_projects"] is None
        assert limits["max_applications"] is None

    def test_free_tier_is_most_limited(self):
        """Test that free tier has the lowest limits."""
        free_limits = TIER_LIMITS[CustomerTier.FREE]
        basic_limits = TIER_LIMITS[CustomerTier.BASIC]
        assert free_limits["max_projects"] < basic_limits["max_projects"]


class TestCustomerService:
    """Tests for CustomerService class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        db.delete = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create CustomerService with mock database."""
        return CustomerService(mock_db)

    @pytest.fixture
    def sample_customer(self):
        """Create a sample customer for testing."""
        customer = MagicMock(spec=Customer)
        customer.id = 1
        customer.name = "Test Customer"
        customer.display_name = "Test Display Name"
        customer.description = "Test Description"
        customer.tier = "BASIC"
        customer.is_active = True
        customer.projects = []
        customer.created_at = datetime.now(timezone.utc)
        customer.updated_at = datetime.now(timezone.utc)
        return customer

    @pytest.mark.asyncio
    async def test_list_customers_returns_list(self, service, mock_db, sample_customer):
        """Test that list_customers returns a list of customers."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_customer]
        mock_db.execute.return_value = mock_result

        # Execute
        customers = await service.list_customers()

        # Assert
        assert isinstance(customers, list)
        assert len(customers) == 1
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_customers_with_tier_filter(self, service, mock_db, sample_customer):
        """Test filtering customers by tier."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_customer]
        mock_db.execute.return_value = mock_result

        customers = await service.list_customers(tier="BASIC")

        assert len(customers) == 1
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_customer_found(self, service, mock_db, sample_customer):
        """Test getting a customer that exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_customer
        mock_db.execute.return_value = mock_result

        customer = await service.get_customer(1)

        assert customer is not None
        assert customer.id == 1

    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, service, mock_db):
        """Test getting a customer that doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        customer = await service.get_customer(999)

        assert customer is None

    @pytest.mark.asyncio
    async def test_create_customer_success(self, service, mock_db):
        """Test creating a customer successfully."""
        mock_db.refresh = AsyncMock()

        customer = await service.create_customer(
            name="New Customer",
            tier="BASIC"
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_customer_invalid_tier(self, service, mock_db):
        """Test that invalid tier raises error."""
        with pytest.raises(ValueError) as exc_info:
            await service.create_customer(
                name="New Customer",
                tier="INVALID_TIER"
            )

        assert "Invalid tier" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_customer_success(self, service, mock_db, sample_customer):
        """Test updating a customer."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_customer
        mock_db.execute.return_value = mock_result

        updated = await service.update_customer(
            customer_id=1,
            display_name="Updated Name"
        )

        assert updated is not None
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_update_customer_not_found(self, service, mock_db):
        """Test updating a customer that doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        updated = await service.update_customer(customer_id=999, display_name="Test")

        assert updated is None

    @pytest.mark.asyncio
    async def test_delete_customer_success(self, service, mock_db, sample_customer):
        """Test deleting a customer."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_customer
        mock_db.execute.return_value = mock_result

        result = await service.delete_customer(1)

        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_delete_customer_not_found(self, service, mock_db):
        """Test deleting a customer that doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.delete_customer(999)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_stats(self, service, mock_db):
        """Test getting customer statistics."""
        # Mock total count
        total_result = MagicMock()
        total_result.scalar.return_value = 10

        # Mock active count
        active_result = MagicMock()
        active_result.scalar.return_value = 8

        # Mock by_tier
        tier_result = MagicMock()
        tier_result.all.return_value = [("FREE", 3), ("BASIC", 5), ("PREMIUM", 2)]

        mock_db.execute.side_effect = [total_result, active_result, tier_result]

        stats = await service.get_stats()

        assert isinstance(stats, CustomerStats)
        assert stats.total_customers == 10
        assert stats.active_customers == 8
        assert stats.inactive_customers == 2


class TestCustomerTierValidation:
    """Tests for tier validation in CustomerService."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        return CustomerService(mock_db)

    def test_validate_tier_valid(self, service):
        """Test that valid tiers pass validation."""
        for tier in ["FREE", "BASIC", "STANDARD", "PROFESSIONAL", "PREMIUM"]:
            service._validate_tier(tier)  # Should not raise

    def test_validate_tier_invalid(self, service):
        """Test that invalid tiers raise ValueError."""
        with pytest.raises(ValueError):
            service._validate_tier("INVALID")

    @pytest.mark.asyncio
    async def test_upgrade_tier(self, service, mock_db):
        """Test upgrading a customer's tier."""
        customer = MagicMock(spec=Customer)
        customer.id = 1
        customer.tier = "FREE"
        customer.projects = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = customer
        mock_db.execute.return_value = mock_result

        result = await service.upgrade_tier(1, "PROFESSIONAL")

        assert result is not None
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_get_tier_limits(self, service, mock_db):
        """Test getting tier limits for a customer."""
        customer = MagicMock(spec=Customer)
        customer.id = 1
        customer.tier = "BASIC"
        customer.projects = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = customer
        mock_db.execute.return_value = mock_result

        limits = await service.get_tier_limits(1)

        assert limits is not None
        assert "max_projects" in limits
        assert limits["max_projects"] == 3


class TestCustomerProjectRelationship:
    """Tests for customer-project relationships."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        return CustomerService(mock_db)

    @pytest.mark.asyncio
    async def test_get_customer_projects(self, service, mock_db):
        """Test getting projects for a customer."""
        project = MagicMock(spec=Project)
        project.id = 1
        project.name = "Test Project"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [project]
        mock_db.execute.return_value = mock_result

        projects = await service.get_customer_projects(1)

        assert isinstance(projects, list)
        assert len(projects) == 1

    @pytest.mark.asyncio
    async def test_assign_project_success(self, service, mock_db):
        """Test assigning a project to a customer."""
        customer = MagicMock(spec=Customer)
        customer.id = 1
        customer.tier = "PREMIUM"  # Unlimited projects
        customer.projects = []

        project = MagicMock(spec=Project)
        project.id = 1
        project.customer_id = None

        # First call returns customer, second returns project
        mock_customer_result = MagicMock()
        mock_customer_result.scalar_one_or_none.return_value = customer

        mock_project_result = MagicMock()
        mock_project_result.scalar_one_or_none.return_value = project

        mock_projects_result = MagicMock()
        mock_projects_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [
            mock_customer_result,  # get_customer
            mock_project_result,   # get project
            mock_projects_result,  # get_customer_projects for limit check
        ]

        result = await service.assign_project(1, 1)

        assert result is True
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_unassign_project_success(self, service, mock_db):
        """Test unassigning a project from a customer."""
        project = MagicMock(spec=Project)
        project.id = 1
        project.customer_id = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = project
        mock_db.execute.return_value = mock_result

        result = await service.unassign_project(1, 1)

        assert result is True
        assert project.customer_id is None
        mock_db.commit.assert_called()


class TestProjectApplicationLink:
    """Tests for project-application link management."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        db.delete = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        return CustomerService(mock_db)

    @pytest.mark.asyncio
    async def test_list_project_applications(self, service, mock_db):
        """Test listing project-application links."""
        link = MagicMock(spec=ProjectApplication)
        link.id = 1
        link.project_id = 1
        link.application_id = 1
        link.role = "primary"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [link]
        mock_db.execute.return_value = mock_result

        links = await service.list_project_applications()

        assert isinstance(links, list)
        assert len(links) == 1

    @pytest.mark.asyncio
    async def test_link_project_application_success(self, service, mock_db):
        """Test creating a project-application link."""
        # Mock check for existing link (returns None = no existing link)
        mock_existing = MagicMock()
        mock_existing.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_existing

        link = await service.link_project_application(
            project_id=1,
            application_id=1,
            role="primary"
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_link_project_application_already_exists(self, service, mock_db):
        """Test that duplicate links return None."""
        existing_link = MagicMock(spec=ProjectApplication)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_link
        mock_db.execute.return_value = mock_result

        link = await service.link_project_application(
            project_id=1,
            application_id=1
        )

        assert link is None

    @pytest.mark.asyncio
    async def test_unlink_project_application_success(self, service, mock_db):
        """Test removing a project-application link."""
        link = MagicMock(spec=ProjectApplication)
        link.id = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = link
        mock_db.execute.return_value = mock_result

        result = await service.unlink_project_application(1)

        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called()
