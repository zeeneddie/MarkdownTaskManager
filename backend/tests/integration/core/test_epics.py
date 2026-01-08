import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_epics_empty(client: AsyncClient):
    """Test listing epics when none exist"""
    response = await client.get("/api/epics/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_epic(client: AsyncClient):
    """Test creating a new epic"""
    epic_data = {
        "title": "New Epic",
        "status": "PLANNED",
        "priority": "HIGH",
        "owner": "John Doe",
        "description": "Epic description"
    }

    response = await client.post("/api/epics/", json=epic_data)
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == epic_data["title"]
    assert data["status"] == epic_data["status"]
    assert data["priority"] == epic_data["priority"]
    assert data["id"].startswith("EPIC-")
    assert data["type"] == "epic"


@pytest.mark.asyncio
async def test_get_epic(client: AsyncClient, test_epic):
    """Test getting a specific epic"""
    response = await client.get(f"/api/epics/{test_epic.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == test_epic.id
    assert data["title"] == test_epic.title


@pytest.mark.asyncio
async def test_get_epic_not_found(client: AsyncClient):
    """Test getting a non-existent epic"""
    response = await client.get("/api/epics/EPIC-999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_epic(client: AsyncClient, test_epic):
    """Test updating an epic"""
    update_data = {
        "title": "Updated Epic Title",
        "status": "IN_PROGRESS"
    }

    response = await client.put(f"/api/epics/{test_epic.id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["status"] == update_data["status"]


@pytest.mark.asyncio
async def test_delete_epic(client: AsyncClient, test_epic):
    """Test deleting an epic"""
    response = await client.delete(f"/api/epics/{test_epic.id}")
    assert response.status_code == 204

    # Verify it's deleted
    response = await client.get(f"/api/epics/{test_epic.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_epic_hierarchy(client: AsyncClient, test_epic, test_feature, test_story):
    """Test getting epic with its hierarchy"""
    response = await client.get(f"/api/epics/{test_epic.id}/hierarchy")
    assert response.status_code == 200

    data = response.json()
    assert data["item"]["id"] == test_epic.id
    assert len(data["children"]) > 0
