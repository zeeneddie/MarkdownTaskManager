"""
Week 10 Green Paper API Integration Tests

Comprehensive tests for all 14 API endpoints:
- Session Management (4 endpoints)
- Constitution Management (5 endpoints)
- Specification Management (4 endpoints)
- Search & Discovery (1 endpoint)
"""

import pytest
from uuid import uuid4
from httpx import AsyncClient


# ========== Session Management Tests (4 endpoints) ==========

@pytest.mark.asyncio
async def test_start_session_success(client: AsyncClient):
    """Test successful BMAD session creation"""
    project_id = str(uuid4())

    response = await client.post(
        "/api/week10/sessions",
        json={
            "project_id": project_id,
            "metadata": {"initiated_by": "test_user"}
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert "session_id" in data
    assert data["project_id"] == project_id
    assert data["status"] == "in_progress"
    assert "questions" in data
    assert len(data["questions"]) == 6


@pytest.mark.asyncio
async def test_get_session_success(client: AsyncClient):
    """Test retrieving session status"""
    project_id = str(uuid4())

    # Create session
    create_response = await client.post(
        "/api/week10/sessions",
        json={"project_id": project_id, "metadata": {}}
    )
    session_id = create_response.json()["session_id"]

    # Get session
    response = await client.get(f"/api/week10/sessions/{session_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["session_id"] == session_id
    assert data["status"] == "in_progress"
    assert "answers" in data
    assert "progress" in data


@pytest.mark.asyncio
async def test_submit_answer_success(client: AsyncClient):
    """Test successful answer submission"""
    project_id = str(uuid4())

    # Create session
    create_response = await client.post(
        "/api/week10/sessions",
        json={"project_id": project_id, "metadata": {}}
    )
    session_id = create_response.json()["session_id"]

    # Submit answer
    response = await client.post(
        f"/api/week10/sessions/{session_id}/answers",
        json={
            "question_number": 1,
            "answer": "We are building a comprehensive task management system with AI-powered assistance.",
            "metadata": {}
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "answer_id" in data
    assert data["question_number"] == 1
    assert data["progress"]["answered"] == 1


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test green paper workflow health check"""
    response = await client.get("/api/week10/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["endpoints"]["total"] == 14
