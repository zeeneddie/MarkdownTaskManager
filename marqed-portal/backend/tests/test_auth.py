"""
Tests for authentication endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.tenant import Tenant
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_login_success(
    client: AsyncClient,
    test_user: User,
    test_tenant: Tenant,
    test_tenant_user,
):
    """Test successful login."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword",
            "tenant_subdomain": "test",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(
    client: AsyncClient,
    test_user: User,
):
    """Test login with invalid password."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with nonexistent user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "password",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_new_user(client: AsyncClient):
    """Test user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "newpassword123",
            "first_name": "New",
            "last_name": "User",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["first_name"] == "New"


@pytest.mark.asyncio
async def test_register_duplicate_email(
    client: AsyncClient,
    test_user: User,
):
    """Test registration with existing email."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",  # Already exists
            "password": "newpassword123",
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_current_user(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test getting current user info."""
    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    """Test accessing protected endpoint without auth."""
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 403  # No Authorization header
