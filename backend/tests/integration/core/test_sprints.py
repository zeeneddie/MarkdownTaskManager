import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone


@pytest.mark.asyncio
async def test_create_sprint(client: AsyncClient):
    """Test creating a new sprint"""
    sprint_data = {
        "name": "Sprint 2",
        "start_date": datetime.now(timezone.utc).isoformat(),
        "end_date": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
        "goal": "Complete user authentication",
        "status": "PLANNED"
    }

    response = await client.post("/api/sprints/", json=sprint_data)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == sprint_data["name"]
    assert data["goal"] == sprint_data["goal"]
    assert data["status"] == sprint_data["status"]


@pytest.mark.asyncio
async def test_get_sprint(client: AsyncClient, test_sprint):
    """Test getting a specific sprint"""
    response = await client.get(f"/api/sprints/{test_sprint.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == test_sprint.id
    assert data["name"] == test_sprint.name


@pytest.mark.asyncio
async def test_list_sprints(client: AsyncClient, test_sprint):
    """Test listing all sprints"""
    response = await client.get("/api/sprints/")
    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0
    assert any(s["id"] == test_sprint.id for s in data)


@pytest.mark.asyncio
async def test_start_sprint(client: AsyncClient, test_sprint):
    """Test starting a sprint"""
    response = await client.post(f"/api/sprints/{test_sprint.id}/start")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_complete_sprint(client: AsyncClient, test_sprint):
    """Test completing a sprint"""
    # First start the sprint
    await client.post(f"/api/sprints/{test_sprint.id}/start")

    # Then complete it
    response = await client.post(f"/api/sprints/{test_sprint.id}/complete")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_assign_story_to_sprint(client: AsyncClient, test_story, test_sprint):
    """Test assigning a story to a sprint"""
    response = await client.post(
        f"/api/stories/{test_story.id}/assign-sprint?sprint_name={test_sprint.name}"
    )
    assert response.status_code == 200

    data = response.json()
    assert data["sprint_id"] == test_sprint.id


@pytest.mark.asyncio
async def test_get_sprint_velocity(client: AsyncClient, test_sprint):
    """Test getting sprint velocity metrics"""
    response = await client.get(f"/api/sprints/{test_sprint.id}/velocity")
    assert response.status_code == 200

    data = response.json()
    assert "velocity" in data
    assert "total_sp" in data
    assert "completed_sp" in data


@pytest.mark.asyncio
async def test_get_sprint_with_stories(client: AsyncClient, test_sprint, test_story, db_session):
    """Test getting sprint with all its stories"""
    # Assign story to sprint
    from app.crud import sprint as sprint_crud
    await sprint_crud.assign_story_to_sprint(db_session, test_story.id, test_sprint.name)

    response = await client.get(f"/api/sprints/{test_sprint.id}/with-stories")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == test_sprint.id
    assert "stories" in data
    assert len(data["stories"]) > 0
