"""
Customer API Tests

Week 143 - Fase 28: Data Architecture Enhancement

Tests for Customer CRUD operations and hierarchy management.
"""

import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from datetime import datetime

from app.main import app
from app.database import get_db
from app.models.customer import Customer, ProjectApplication
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import TestSessionLocal


async def override_get_db():
    """Override database dependency for tests."""
    async with TestSessionLocal() as session:
        yield session


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


def unique_name(prefix: str = "Test") -> str:
    """Generate unique name for test isolation."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.fixture
async def async_client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestCustomerCRUD:
    """Test Customer CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_customer(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test creating a new customer."""
        name = unique_name("Customer")
        response = await async_client.post(
            "/api/customers",
            json={
                "name": name,
                "display_name": "Test Display Name",
                "description": "A test customer",
                "contact_name": "John Doe",
                "contact_email": "john@test.com",
                "tier": "STANDARD"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == name
        assert data["display_name"] == "Test Display Name"
        assert data["tier"] == "STANDARD"
        assert data["is_active"] == True
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_customer_duplicate_name(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that duplicate customer names are rejected."""
        name = unique_name("UniqueCustomer")

        # Create first customer
        await async_client.post(
            "/api/customers",
            json={"name": name, "tier": "FREE"}
        )

        # Try to create duplicate
        response = await async_client.post(
            "/api/customers",
            json={"name": name, "tier": "FREE"}
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_customer_invalid_tier(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that invalid tier is rejected."""
        response = await async_client.post(
            "/api/customers",
            json={"name": unique_name("InvalidTier"), "tier": "INVALID"}
        )

        assert response.status_code == 400
        assert "Invalid tier" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_customers(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test listing customers."""
        # Create test customers
        for i in range(3):
            await async_client.post(
                "/api/customers",
                json={"name": unique_name(f"ListTest{i}"), "tier": "FREE"}
            )

        response = await async_client.get("/api/customers")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    @pytest.mark.asyncio
    async def test_list_customers_with_tier_filter(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test filtering customers by tier."""
        # Create customers with different tiers
        await async_client.post(
            "/api/customers",
            json={"name": unique_name("PremiumCust"), "tier": "PREMIUM"}
        )
        await async_client.post(
            "/api/customers",
            json={"name": unique_name("BasicCust"), "tier": "BASIC"}
        )

        response = await async_client.get("/api/customers?tier=PREMIUM")

        assert response.status_code == 200
        data = response.json()
        assert all(c["tier"] == "PREMIUM" for c in data)

    @pytest.mark.asyncio
    async def test_list_customers_with_search(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test searching customers."""
        search_term = f"SearchABC{uuid.uuid4().hex[:4]}"
        await async_client.post(
            "/api/customers",
            json={"name": f"Searchable Customer {search_term}", "tier": "FREE"}
        )

        response = await async_client.get(f"/api/customers?search={search_term}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(search_term in c["name"] for c in data)

    @pytest.mark.asyncio
    async def test_get_customer(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test getting a single customer."""
        name = unique_name("GetTest")

        # Create customer
        create_response = await async_client.post(
            "/api/customers",
            json={"name": name, "tier": "STANDARD"}
        )
        customer_id = create_response.json()["id"]

        # Get customer
        response = await async_client.get(f"/api/customers/{customer_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == customer_id
        assert data["name"] == name

    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test getting non-existent customer."""
        response = await async_client.get("/api/customers/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_customer(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test updating a customer."""
        name = unique_name("UpdateTest")

        # Create customer
        create_response = await async_client.post(
            "/api/customers",
            json={"name": name, "tier": "FREE"}
        )
        customer_id = create_response.json()["id"]

        # Update customer
        response = await async_client.put(
            f"/api/customers/{customer_id}",
            json={
                "display_name": "Updated Display Name",
                "tier": "PROFESSIONAL",
                "contact_email": "updated@test.com"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Display Name"
        assert data["tier"] == "PROFESSIONAL"
        assert data["contact_email"] == "updated@test.com"

    @pytest.mark.asyncio
    async def test_delete_customer(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test deleting a customer."""
        name = unique_name("DeleteTest")

        # Create customer
        create_response = await async_client.post(
            "/api/customers",
            json={"name": name, "tier": "FREE"}
        )
        customer_id = create_response.json()["id"]

        # Delete customer
        response = await async_client.delete(f"/api/customers/{customer_id}")

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify deleted
        get_response = await async_client.get(f"/api/customers/{customer_id}")
        assert get_response.status_code == 404


class TestCustomerStats:
    """Test Customer statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_customer_stats(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test getting customer statistics."""
        # Create some test customers first
        await async_client.post(
            "/api/customers",
            json={"name": unique_name("StatTest"), "tier": "STANDARD"}
        )

        response = await async_client.get("/api/customers/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_customers" in data
        assert "active_customers" in data
        assert "inactive_customers" in data
        assert "by_tier" in data


class TestCustomerProjects:
    """Test Customer-Project relationship endpoints."""

    @pytest.mark.asyncio
    async def test_get_customer_projects_empty(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test getting projects for customer with no projects."""
        # Create customer
        create_response = await async_client.post(
            "/api/customers",
            json={"name": unique_name("NoProjects"), "tier": "FREE"}
        )
        customer_id = create_response.json()["id"]

        # Get projects
        response = await async_client.get(f"/api/customers/{customer_id}/projects")

        assert response.status_code == 200
        assert response.json() == []


class TestProjectApplicationLinks:
    """Test Project-Application link endpoints."""

    @pytest.mark.asyncio
    async def test_list_project_applications_empty(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test listing project-application links when empty."""
        response = await async_client.get("/api/customers/project-applications")

        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestCustomerTiers:
    """Test tier validation and business rules."""

    @pytest.mark.asyncio
    async def test_valid_tiers(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that all valid tiers are accepted."""
        valid_tiers = ["FREE", "BASIC", "STANDARD", "PROFESSIONAL", "PREMIUM"]

        for tier in valid_tiers:
            response = await async_client.post(
                "/api/customers",
                json={"name": unique_name(f"TierTest{tier}"), "tier": tier}
            )
            assert response.status_code == 201, f"Failed for tier: {tier}"
            assert response.json()["tier"] == tier

    @pytest.mark.asyncio
    async def test_default_tier_is_free(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that default tier is FREE when not specified."""
        response = await async_client.post(
            "/api/customers",
            json={"name": unique_name("DefaultTier")}
        )

        assert response.status_code == 201
        assert response.json()["tier"] == "FREE"
