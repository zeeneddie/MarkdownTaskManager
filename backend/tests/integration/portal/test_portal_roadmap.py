"""
Week 90: Portal Roadmap API Tests

Tests for:
- Analysis Queue (submit items for analysis, manage status)
- Release Management (CRUD, timeline, ordering)
- Roadmap Items (analyzed items only, dependencies)
- Public Roadmaps (shareable URLs, customization)
"""

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4
from httpx import AsyncClient


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_item_id():
    """Sample backlog item ID."""
    return f"EPIC-{uuid4().hex[:8]}"


@pytest.fixture
def sample_release_data():
    """Sample release creation data."""
    return {
        "name": "v1.0 - Initial Release",
        "version": "1.0.0",
        "description": "First public release with core features",
        "color": "#4CAF50",
        "target_date": (date.today() + timedelta(days=30)).isoformat(),
        "start_date": date.today().isoformat(),
        "status": "planned",
        "display_order": 0
    }


@pytest.fixture
def sample_public_roadmap_data():
    """Sample public roadmap creation data."""
    return {
        "slug": f"test-roadmap-{uuid4().hex[:8]}",
        "title": "Product Roadmap 2025",
        "description": "Public roadmap for stakeholders",
        "show_completed": True,
        "show_cancelled": False,
        "show_dates": True,
        "show_progress": True,
        "show_votes": True,
        "theme": "light",
        "header_color": "#1976D2"
    }


# =============================================================================
# Analysis Queue Tests
# =============================================================================

class TestAnalysisQueue:
    """Tests for the analysis queue workflow."""

    @pytest.mark.asyncio
    async def test_submit_item_for_analysis(self, client: AsyncClient, sample_item_id):
        """Test submitting a backlog item for analysis."""
        # Note: This would require a real item in the database
        # For now, we test the endpoint structure
        response = await client.post(
            "/api/portal/roadmap/analysis-queue",
            json={
                "item_id": sample_item_id,
                "priority": 5,
                "requested_by": "user@example.com"
            }
        )
        # Will return 404 if item doesn't exist, which is expected
        assert response.status_code in [200, 201, 404]

    @pytest.mark.asyncio
    async def test_list_analysis_queue(self, client: AsyncClient):
        """Test listing analysis queue entries."""
        response = await client.get("/api/portal/roadmap/analysis-queue")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_pending_analysis(self, client: AsyncClient):
        """Test getting pending items for agents."""
        response = await client.get("/api/portal/roadmap/analysis-queue/pending")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_completed_analysis(self, client: AsyncClient):
        """Test getting completed analysis entries."""
        response = await client.get("/api/portal/roadmap/analysis-queue/completed")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_analysis_queue_stats(self, client: AsyncClient):
        """Test getting analysis queue statistics."""
        response = await client.get("/api/portal/roadmap/analysis-queue/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_status" in data
        assert "ready_for_roadmap" in data

    @pytest.mark.asyncio
    async def test_get_available_backlog_items(self, client: AsyncClient):
        """Test getting available backlog items for analysis."""
        response = await client.get("/api/portal/roadmap/backlog/available")
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert "total_available" in data
        assert "in_queue_count" in data


# =============================================================================
# Release Management Tests
# =============================================================================

class TestReleases:
    """Tests for release management."""

    @pytest.mark.asyncio
    async def test_create_release(self, client: AsyncClient, sample_release_data):
        """Test creating a new release."""
        response = await client.post(
            "/api/portal/roadmap/releases",
            json=sample_release_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_release_data["name"]
        assert data["version"] == sample_release_data["version"]
        assert data["status"] == "planned"
        assert "id" in data
        return data["id"]

    @pytest.mark.asyncio
    async def test_list_releases(self, client: AsyncClient):
        """Test listing all releases."""
        response = await client.get("/api/portal/roadmap/releases")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_releases_with_filter(self, client: AsyncClient):
        """Test listing releases with status filter."""
        response = await client.get(
            "/api/portal/roadmap/releases",
            params={"status": "planned"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_release_not_found(self, client: AsyncClient):
        """Test getting a non-existent release."""
        response = await client.get(
            f"/api/portal/roadmap/releases/{uuid4()}"
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_release(self, client: AsyncClient, sample_release_data):
        """Test updating a release."""
        # First create a release
        create_response = await client.post(
            "/api/portal/roadmap/releases",
            json=sample_release_data
        )
        assert create_response.status_code == 200
        release_id = create_response.json()["id"]

        # Then update it
        update_response = await client.patch(
            f"/api/portal/roadmap/releases/{release_id}",
            json={
                "name": "v1.0 - Updated Release",
                "status": "in_progress"
            }
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "v1.0 - Updated Release"
        assert data["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_delete_release(self, client: AsyncClient, sample_release_data):
        """Test deleting a release."""
        # First create a release
        create_response = await client.post(
            "/api/portal/roadmap/releases",
            json=sample_release_data
        )
        assert create_response.status_code == 200
        release_id = create_response.json()["id"]

        # Then delete it
        delete_response = await client.delete(
            f"/api/portal/roadmap/releases/{release_id}"
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_reorder_releases(self, client: AsyncClient, sample_release_data):
        """Test reordering releases."""
        # Create two releases
        release1 = await client.post(
            "/api/portal/roadmap/releases",
            json={**sample_release_data, "name": "Release 1"}
        )
        release2 = await client.post(
            "/api/portal/roadmap/releases",
            json={**sample_release_data, "name": "Release 2"}
        )

        release1_id = release1.json()["id"]
        release2_id = release2.json()["id"]

        # Reorder
        response = await client.post(
            "/api/portal/roadmap/releases/reorder",
            json=[release2_id, release1_id]
        )
        assert response.status_code == 200
        assert response.json()["count"] == 2

    @pytest.mark.asyncio
    async def test_release_timeline(self, client: AsyncClient, sample_release_data):
        """Test getting release timeline."""
        # First create a release
        create_response = await client.post(
            "/api/portal/roadmap/releases",
            json=sample_release_data
        )
        release_id = create_response.json()["id"]

        # Get timeline
        response = await client.get(
            f"/api/portal/roadmap/releases/{release_id}/timeline"
        )
        assert response.status_code == 200
        data = response.json()
        assert "release" in data
        assert "total_estimated_days" in data
        assert "items" in data


# =============================================================================
# Roadmap Items Tests
# =============================================================================

class TestRoadmapItems:
    """Tests for roadmap items."""

    @pytest.mark.asyncio
    async def test_add_item_without_analysis_fails(self, client: AsyncClient, sample_item_id):
        """Test that adding an unanalyzed item fails."""
        response = await client.post(
            "/api/portal/roadmap/items",
            json={"item_id": sample_item_id}
        )
        # Should fail because item hasn't been analyzed
        assert response.status_code in [400, 404]
        if response.status_code == 400:
            assert "analyzed" in response.json()["detail"].lower() or "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_add_item_requires_id(self, client: AsyncClient):
        """Test that adding an item requires either item_id or feature_request_id."""
        response = await client.post(
            "/api/portal/roadmap/items",
            json={}
        )
        assert response.status_code == 400
        assert "item_id or feature_request_id" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_roadmap_items(self, client: AsyncClient):
        """Test listing roadmap items."""
        response = await client.get("/api/portal/roadmap/items")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_roadmap_items_by_status(self, client: AsyncClient):
        """Test listing roadmap items filtered by status."""
        response = await client.get(
            "/api/portal/roadmap/items",
            params={"status": "backlog"}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_item_not_found(self, client: AsyncClient):
        """Test getting a non-existent roadmap item."""
        response = await client.get(
            f"/api/portal/roadmap/items/{uuid4()}"
        )
        assert response.status_code == 404


# =============================================================================
# Public Roadmap Tests
# =============================================================================

class TestPublicRoadmaps:
    """Tests for public roadmap configurations."""

    @pytest.mark.asyncio
    async def test_create_public_roadmap(self, client: AsyncClient, sample_public_roadmap_data):
        """Test creating a public roadmap."""
        response = await client.post(
            "/api/portal/roadmap/public",
            json=sample_public_roadmap_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == sample_public_roadmap_data["slug"]
        assert data["title"] == sample_public_roadmap_data["title"]
        assert "public_url" in data

    @pytest.mark.asyncio
    async def test_create_duplicate_slug_fails(self, client: AsyncClient, sample_public_roadmap_data):
        """Test that creating a roadmap with duplicate slug fails."""
        # Create first
        await client.post(
            "/api/portal/roadmap/public",
            json=sample_public_roadmap_data
        )

        # Try to create duplicate
        response = await client.post(
            "/api/portal/roadmap/public",
            json=sample_public_roadmap_data
        )
        assert response.status_code == 400
        assert "slug" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_list_public_roadmaps(self, client: AsyncClient):
        """Test listing public roadmaps."""
        response = await client.get("/api/portal/roadmap/public")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_public_roadmap_by_slug(self, client: AsyncClient, sample_public_roadmap_data):
        """Test getting a public roadmap by slug."""
        # Create first
        await client.post(
            "/api/portal/roadmap/public",
            json=sample_public_roadmap_data
        )

        # Get by slug
        response = await client.get(
            f"/api/portal/roadmap/public/by-slug/{sample_public_roadmap_data['slug']}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert "releases" in data

    @pytest.mark.asyncio
    async def test_get_public_roadmap_not_found(self, client: AsyncClient):
        """Test getting a non-existent public roadmap."""
        response = await client.get(
            "/api/portal/roadmap/public/by-slug/non-existent-slug"
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_public_roadmap(self, client: AsyncClient, sample_public_roadmap_data):
        """Test updating a public roadmap."""
        # Create first
        create_response = await client.post(
            "/api/portal/roadmap/public",
            json=sample_public_roadmap_data
        )
        roadmap_id = create_response.json()["id"]

        # Update
        update_response = await client.patch(
            f"/api/portal/roadmap/public/{roadmap_id}",
            json={
                "title": "Updated Roadmap Title",
                "theme": "dark"
            }
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["title"] == "Updated Roadmap Title"
        assert data["theme"] == "dark"

    @pytest.mark.asyncio
    async def test_delete_public_roadmap(self, client: AsyncClient, sample_public_roadmap_data):
        """Test deleting a public roadmap."""
        # Create first
        create_response = await client.post(
            "/api/portal/roadmap/public",
            json=sample_public_roadmap_data
        )
        roadmap_id = create_response.json()["id"]

        # Delete
        delete_response = await client.delete(
            f"/api/portal/roadmap/public/{roadmap_id}"
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_public_roadmap_stats(self, client: AsyncClient, sample_public_roadmap_data):
        """Test getting public roadmap statistics."""
        # Create first
        create_response = await client.post(
            "/api/portal/roadmap/public",
            json=sample_public_roadmap_data
        )
        roadmap_id = create_response.json()["id"]

        # Get stats
        response = await client.get(
            f"/api/portal/roadmap/public/{roadmap_id}/stats"
        )
        assert response.status_code == 200
        data = response.json()
        assert "view_count" in data
        assert "slug" in data


# =============================================================================
# Overview and Kanban Tests
# =============================================================================

class TestOverviewAndKanban:
    """Tests for overview and kanban views."""

    @pytest.mark.asyncio
    async def test_roadmap_overview(self, client: AsyncClient):
        """Test getting roadmap overview."""
        response = await client.get("/api/portal/roadmap/overview")
        assert response.status_code == 200
        data = response.json()
        assert "releases" in data
        assert "items" in data
        assert "upcoming_releases" in data

    @pytest.mark.asyncio
    async def test_roadmap_kanban(self, client: AsyncClient):
        """Test getting roadmap in kanban format."""
        response = await client.get("/api/portal/roadmap/kanban")
        assert response.status_code == 200
        data = response.json()
        assert "lanes" in data
        assert "lane_order" in data
        assert "total_items" in data


# =============================================================================
# Workflow Integration Tests
# =============================================================================

class TestWorkflowIntegration:
    """Tests for the complete analysis-to-roadmap workflow."""

    @pytest.mark.asyncio
    async def test_complete_workflow_structure(self, client: AsyncClient):
        """Test that all workflow endpoints exist and return correct structure."""
        # 1. Check available backlog items
        available_response = await client.get("/api/portal/roadmap/backlog/available")
        assert available_response.status_code == 200

        # 2. Check analysis queue
        queue_response = await client.get("/api/portal/roadmap/analysis-queue")
        assert queue_response.status_code == 200

        # 3. Check pending analysis
        pending_response = await client.get("/api/portal/roadmap/analysis-queue/pending")
        assert pending_response.status_code == 200

        # 4. Check completed analysis
        completed_response = await client.get("/api/portal/roadmap/analysis-queue/completed")
        assert completed_response.status_code == 200

        # 5. Check roadmap items
        items_response = await client.get("/api/portal/roadmap/items")
        assert items_response.status_code == 200

        # 6. Check releases
        releases_response = await client.get("/api/portal/roadmap/releases")
        assert releases_response.status_code == 200
