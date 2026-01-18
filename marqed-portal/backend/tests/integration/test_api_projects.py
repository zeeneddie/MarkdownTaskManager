"""
Integration tests for Projects API endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.user import User
from app.models.project import Project, ProjectStatus, ProjectType


@pytest.mark.integration
@pytest.mark.asyncio
class TestProjectsAPI:
    """Integration tests for /api/v1/projects endpoints."""

    async def test_list_projects_unauthorized(self, client: AsyncClient):
        """Test listing projects without authentication."""
        response = await client.get("/api/v1/projects")
        assert response.status_code == 401

    async def test_list_projects_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_tenant_user,
    ):
        """Test listing projects when none exist."""
        response = await client.get(
            "/api/v1/projects",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_create_project(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_tenant_user,
    ):
        """Test creating a new project."""
        project_data = {
            "name": "New Test Project",
            "code": "NTP",
            "description": "A test project for integration tests",
            "project_type": "brownfield",
        }

        response = await client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json=project_data,
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["code"] == project_data["code"]

    async def test_get_project_by_id(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_tenant: Tenant,
        test_tenant_user,
    ):
        """Test getting a specific project."""
        # Create a project first
        project = Project(
            tenant_id=test_tenant.id,
            name="Get By ID Test",
            code="GBIT",
            project_type=ProjectType.BROWNFIELD,
            status=ProjectStatus.ACTIVE,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        # Get the project
        response = await client.get(
            f"/api/v1/projects/{project.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Get By ID Test"

    async def test_get_nonexistent_project(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_tenant_user,
    ):
        """Test getting a project that doesn't exist."""
        response = await client.get(
            "/api/v1/projects/nonexistent-id-12345",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_update_project(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_tenant: Tenant,
        test_tenant_user,
    ):
        """Test updating a project."""
        # Create a project
        project = Project(
            tenant_id=test_tenant.id,
            name="Update Test",
            code="UPT",
            project_type=ProjectType.GREENFIELD,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        # Update the project
        response = await client.patch(
            f"/api/v1/projects/{project.id}",
            headers=auth_headers,
            json={"name": "Updated Name", "description": "Updated description"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    async def test_delete_project(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_tenant: Tenant,
        test_tenant_user,
    ):
        """Test deleting a project."""
        # Create a project
        project = Project(
            tenant_id=test_tenant.id,
            name="Delete Test",
            code="DEL",
            project_type=ProjectType.HYBRID,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        # Delete the project
        response = await client.delete(
            f"/api/v1/projects/{project.id}",
            headers=auth_headers,
        )

        assert response.status_code in [200, 204]

        # Verify it's gone
        get_response = await client.get(
            f"/api/v1/projects/{project.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
class TestProjectsFiltering:
    """Integration tests for project filtering and pagination."""

    async def test_filter_by_status(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_tenant_user,
    ):
        """Test filtering projects by status."""
        response = await client.get(
            "/api/v1/projects?status=active",
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_tenant_user,
    ):
        """Test projects pagination."""
        response = await client.get(
            "/api/v1/projects?page=1&page_size=5",
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_sorting(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_tenant_user,
    ):
        """Test projects sorting."""
        response = await client.get(
            "/api/v1/projects?sort=-created_at",
            headers=auth_headers,
        )

        assert response.status_code == 200
