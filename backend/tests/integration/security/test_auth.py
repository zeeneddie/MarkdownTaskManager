import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration"""
    user_data = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "newpassword123",
        "full_name": "New User"
    }

    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user):
    """Test registering with duplicate email"""
    user_data = {
        "email": test_user.email,
        "username": "differentusername",
        "password": "password123"
    }

    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Test successful login"""
    login_data = {
        "username": test_user.username,
        "password": "testpassword123"
    }

    response = await client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    """Test login with wrong password"""
    login_data = {
        "username": test_user.username,
        "password": "wrongpassword"
    }

    response = await client.post("/api/auth/login", data=login_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent user"""
    login_data = {
        "username": "nonexistent",
        "password": "password123"
    }

    response = await client.post("/api/auth/login", data=login_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers):
    """Test getting current user info"""
    response = await client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient):
    """Test getting current user without authentication"""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_endpoint(client: AsyncClient, test_user):
    """Test the JSON token endpoint"""
    login_data = {
        "username": test_user.username,
        "password": "testpassword123"
    }

    response = await client.post("/api/auth/token", json=login_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
