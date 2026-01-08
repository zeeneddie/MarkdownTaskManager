"""
Week 88: Portal Feature Request API Tests

Tests for customer portal feature request submission, classification,
and epic mapping functionality.
"""
import pytest
from httpx import AsyncClient
from datetime import datetime


@pytest.mark.asyncio
async def test_submit_feature_request(client: AsyncClient):
    """Test submitting a new feature request."""
    request_data = {
        "user_email": "customer@example.com",
        "title": "Add dark mode to the dashboard",
        "description": "Users have requested a dark mode option for better viewing at night",
        "priority": "medium",
        "category": "UI/UX",
        "user_name": "John Customer",
        "organization": "Example Corp",
    }

    response = await client.post("/api/portal/features/submit", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "request" in data
    assert data["request"]["title"] == "Add dark mode to the dashboard"
    assert data["request"]["status"] == "submitted"
    assert data["request"]["user_email"] == "customer@example.com"


@pytest.mark.asyncio
async def test_submit_feature_request_validation(client: AsyncClient):
    """Test feature request validation."""
    # Missing required fields
    response = await client.post("/api/portal/features/submit", json={
        "title": "Short"  # Missing user_email, title too short
    })

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_submit_feature_request_priority_validation(client: AsyncClient):
    """Test priority validation - accepts valid priorities."""
    request_data = {
        "user_email": "customer@example.com",
        "title": "Critical bug in payment processing",
        "priority": "critical",
    }

    response = await client.post("/api/portal/features/submit", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["request"]["priority"] == "critical"


@pytest.mark.asyncio
async def test_get_feature_request(client: AsyncClient):
    """Test retrieving a feature request by ID."""
    # First create a request
    create_response = await client.post("/api/portal/features/submit", json={
        "user_email": "test@example.com",
        "title": "Test feature request for retrieval",
    })
    assert create_response.status_code == 200
    request_id = create_response.json()["request"]["id"]

    # Then retrieve it
    response = await client.get(f"/api/portal/features/{request_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == request_id
    assert data["title"] == "Test feature request for retrieval"


@pytest.mark.asyncio
async def test_get_feature_request_not_found(client: AsyncClient):
    """Test retrieving non-existent feature request."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/portal/features/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_feature_requests(client: AsyncClient):
    """Test listing feature requests."""
    # Create a few requests
    for i in range(3):
        await client.post("/api/portal/features/submit", json={
            "user_email": "list-test@example.com",
            "title": f"List test request {i}",
        })

    # List all
    response = await client.get("/api/portal/features")

    assert response.status_code == 200
    data = response.json()
    assert "requests" in data
    assert "total" in data
    assert len(data["requests"]) >= 3


@pytest.mark.asyncio
async def test_list_feature_requests_with_filters(client: AsyncClient):
    """Test listing feature requests with filters."""
    # Create request with specific email
    await client.post("/api/portal/features/submit", json={
        "user_email": "filtered@example.com",
        "title": "Filtered test request",
        "organization": "FilterOrg",
    })

    # Filter by email
    response = await client.get("/api/portal/features", params={
        "user_email": "filtered@example.com"
    })

    assert response.status_code == 200
    data = response.json()
    assert all(r["user_email"] == "filtered@example.com" for r in data["requests"])


@pytest.mark.asyncio
async def test_update_feature_request(client: AsyncClient):
    """Test updating a feature request."""
    # Create request
    create_response = await client.post("/api/portal/features/submit", json={
        "user_email": "update-test@example.com",
        "title": "Original title",
        "priority": "low",
    })
    request_id = create_response.json()["request"]["id"]

    # Update it
    response = await client.patch(f"/api/portal/features/{request_id}", json={
        "title": "Updated title",
        "priority": "high",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["request"]["title"] == "Updated title"
    assert data["request"]["priority"] == "high"


@pytest.mark.asyncio
async def test_classify_feature_request(client: AsyncClient):
    """Test classifying a feature request with Peter agent."""
    # Create a bug-like request
    create_response = await client.post("/api/portal/features/submit", json={
        "user_email": "classify-test@example.com",
        "title": "Bug fix: Login crashes on invalid input",
        "description": "When users enter invalid characters, the login page crashes",
    })
    request_id = create_response.json()["request"]["id"]

    # Classify it
    response = await client.post(f"/api/portal/features/{request_id}/classify", json={
        "use_llm": True
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["request"]["work_type"] is not None
    assert data["request"]["classification_confidence"] is not None
    assert data["request"]["status"] == "classified"
    assert "classification" in data


@pytest.mark.asyncio
async def test_classify_feature_request_new_feature(client: AsyncClient):
    """Test classification identifies new feature work type."""
    create_response = await client.post("/api/portal/features/submit", json={
        "user_email": "new-feature@example.com",
        "title": "Add new export to PDF feature",
        "description": "We need to add the ability to export reports to PDF format",
    })
    request_id = create_response.json()["request"]["id"]

    response = await client.post(f"/api/portal/features/{request_id}/classify")

    assert response.status_code == 200
    data = response.json()
    # Should classify as NEW_FEATURE or ENHANCEMENT
    assert data["request"]["work_type"] in ["NEW_FEATURE", "ENHANCEMENT"]


@pytest.mark.asyncio
async def test_map_to_epic(client: AsyncClient, db_session):
    """Test mapping a feature request to an epic."""
    from app.models.project import Project

    # Create a project first
    project = Project(name="Test Project", description="Test")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create feature request
    create_response = await client.post("/api/portal/features/submit", json={
        "user_email": "map-test@example.com",
        "title": "Test feature for mapping",
    })
    request_id = create_response.json()["request"]["id"]

    # Map to project
    response = await client.post(
        f"/api/portal/features/{request_id}/map/{project.id}",
        params={"auto_suggest": True}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["request"]["mapped_project_id"] == project.id


@pytest.mark.asyncio
async def test_confirm_mapping(client: AsyncClient):
    """Test confirming epic mapping."""
    # Create feature request
    create_response = await client.post("/api/portal/features/submit", json={
        "user_email": "confirm-map@example.com",
        "title": "Test feature for confirm mapping",
    })
    request_id = create_response.json()["request"]["id"]

    # Confirm mapping
    response = await client.post(f"/api/portal/features/{request_id}/confirm-mapping", json={
        "epic_id": "EPIC-123",
        "feature_id": "FEAT-456",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["request"]["mapped_epic_id"] == "EPIC-123"
    assert data["request"]["mapped_feature_id"] == "FEAT-456"
    assert data["request"]["mapping_confidence"] == 1.0  # User confirmed


@pytest.mark.asyncio
async def test_assign_to_sprint(client: AsyncClient):
    """Test assigning a feature request to a sprint."""
    # Create feature request
    create_response = await client.post("/api/portal/features/submit", json={
        "user_email": "sprint-test@example.com",
        "title": "Test feature for sprint assignment",
    })
    request_id = create_response.json()["request"]["id"]

    # Assign to sprint
    response = await client.post(f"/api/portal/features/{request_id}/assign-sprint", json={
        "sprint_id": 42
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["request"]["sprint_id"] == 42
    assert data["request"]["status"] == "planned"


@pytest.mark.asyncio
async def test_create_kanban_item(client: AsyncClient):
    """Test creating a kanban item from a feature request."""
    # Create feature request
    create_response = await client.post("/api/portal/features/submit", json={
        "user_email": "kanban-test@example.com",
        "title": "Test feature for kanban",
    })
    request_id = create_response.json()["request"]["id"]

    # Create kanban item
    response = await client.post(f"/api/portal/features/{request_id}/create-kanban")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["kanban_item_id"] is not None
    assert data["request"]["status"] == "in_progress"


@pytest.mark.asyncio
async def test_process_feature_request_pipeline(client: AsyncClient):
    """Test full feature request processing pipeline."""
    # Create feature request
    create_response = await client.post("/api/portal/features/submit", json={
        "user_email": "pipeline-test@example.com",
        "title": "Add new reporting feature with charts",
        "description": "Users need a new reporting feature with visual charts",
    })
    request_id = create_response.json()["request"]["id"]

    # Process through pipeline
    response = await client.post(f"/api/portal/features/{request_id}/process")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "classification" in data
    assert "recommended_actions" in data
    assert "workflow_integrations" in data


@pytest.mark.asyncio
async def test_get_statistics(client: AsyncClient):
    """Test getting feature request statistics."""
    # Create some requests
    for i in range(5):
        await client.post("/api/portal/features/submit", json={
            "user_email": f"stats-test-{i}@example.com",
            "title": f"Stats test request {i}",
        })

    response = await client.get("/api/portal/features/stats/overview", params={
        "days": 30
    })

    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "by_status" in data
    assert "by_priority" in data
    assert "period_days" in data


@pytest.mark.asyncio
async def test_get_user_requests(client: AsyncClient):
    """Test getting all requests for a specific user."""
    user_email = "user-requests-test@example.com"

    # Create requests for this user
    for i in range(3):
        await client.post("/api/portal/features/submit", json={
            "user_email": user_email,
            "title": f"User request {i}",
        })

    response = await client.get(f"/api/portal/features/user/{user_email}")

    assert response.status_code == 200
    data = response.json()
    assert data["user_email"] == user_email
    assert len(data["requests"]) >= 3
