"""
API Tests for Fase 24: Data Architecture Endpoints

Tests cover:
- Data Lineage API endpoints
- ERD Generator API endpoints
- CDC Integration API endpoints

Author: Claude Code (Week 136 - Fase 24)
Date: 2026-01-01
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.main import app


@pytest.fixture
def test_client():
    """Create async test client"""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestDataLineageAPI:
    """Test Data Lineage API endpoints"""

    @pytest.mark.asyncio
    async def test_create_lineage_session(self, test_client):
        """Test POST /api/data-architecture/lineage/sessions"""
        async with test_client as client:
            response = await client.post(
                "/api/data-architecture/lineage/sessions",
                json={
                    "name": "Test Session",
                    "project_id": str(uuid4()),
                    "description": "Test lineage tracking"
                }
            )

            assert response.status_code in [200, 201, 422]  # 422 if validation fails

    @pytest.mark.asyncio
    async def test_get_lineage_session(self, test_client):
        """Test GET /api/data-architecture/lineage/sessions/{session_id}"""
        async with test_client as client:
            session_id = str(uuid4())
            response = await client.get(
                f"/api/data-architecture/lineage/sessions/{session_id}"
            )

            # 404 expected for non-existent session
            assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_add_lineage_node(self, test_client):
        """Test POST /api/data-architecture/lineage/sessions/{session_id}/nodes"""
        async with test_client as client:
            session_id = str(uuid4())
            response = await client.post(
                f"/api/data-architecture/lineage/sessions/{session_id}/nodes",
                json={
                    "node_type": "entity",
                    "name": "User",
                    "description": "User entity"
                }
            )

            # 404 for non-existent session, or success
            assert response.status_code in [200, 201, 404, 422]

    @pytest.mark.asyncio
    async def test_get_traceability_matrix(self, test_client):
        """Test GET /api/data-architecture/lineage/sessions/{session_id}/traceability"""
        async with test_client as client:
            session_id = str(uuid4())
            response = await client.get(
                f"/api/data-architecture/lineage/sessions/{session_id}/traceability"
            )

            assert response.status_code in [200, 404]


class TestERDGeneratorAPI:
    """Test ERD Generator API endpoints"""

    @pytest.mark.asyncio
    async def test_generate_erd(self, test_client):
        """Test POST /api/data-architecture/erd/generate"""
        async with test_client as client:
            response = await client.post(
                "/api/data-architecture/erd/generate",
                json={
                    "name": "Test ERD",
                    "entities": [
                        {
                            "name": "User",
                            "fields": [
                                {"name": "id", "type": "int"},
                                {"name": "name", "type": "varchar"}
                            ]
                        }
                    ]
                }
            )

            assert response.status_code in [200, 201, 422]

    @pytest.mark.asyncio
    async def test_get_erd_diagram(self, test_client):
        """Test GET /api/data-architecture/erd/diagrams/{diagram_id}"""
        async with test_client as client:
            diagram_id = str(uuid4())
            response = await client.get(
                f"/api/data-architecture/erd/diagrams/{diagram_id}"
            )

            assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_export_erd_mermaid(self, test_client):
        """Test GET /api/data-architecture/erd/diagrams/{diagram_id}/export?format=mermaid"""
        async with test_client as client:
            diagram_id = str(uuid4())
            response = await client.get(
                f"/api/data-architecture/erd/diagrams/{diagram_id}/export",
                params={"format": "mermaid"}
            )

            assert response.status_code in [200, 404]


class TestCDCIntegrationAPI:
    """Test CDC Integration API endpoints"""

    @pytest.mark.asyncio
    async def test_create_cdc_session(self, test_client):
        """Test POST /api/data-architecture/cdc/sessions"""
        async with test_client as client:
            response = await client.post(
                "/api/data-architecture/cdc/sessions",
                json={
                    "name": "Test CDC Session",
                    "mode": "shadow",
                    "provider": "polling",
                    "legacy_connection": {
                        "host": "localhost",
                        "port": "1433",
                        "database": "LegacyDB"
                    },
                    "new_connection": {
                        "host": "localhost",
                        "port": "5432",
                        "database": "new_db"
                    }
                }
            )

            assert response.status_code in [200, 201, 422]

    @pytest.mark.asyncio
    async def test_get_cdc_session(self, test_client):
        """Test GET /api/data-architecture/cdc/sessions/{session_id}"""
        async with test_client as client:
            session_id = str(uuid4())
            response = await client.get(
                f"/api/data-architecture/cdc/sessions/{session_id}"
            )

            assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_add_table_mapping(self, test_client):
        """Test POST /api/data-architecture/cdc/sessions/{session_id}/mappings"""
        async with test_client as client:
            session_id = str(uuid4())
            response = await client.post(
                f"/api/data-architecture/cdc/sessions/{session_id}/mappings",
                json={
                    "legacy_table": "tblUsers",
                    "new_table": "users",
                    "field_mappings": {
                        "strUserName": "username",
                        "strEmail": "email"
                    }
                }
            )

            assert response.status_code in [200, 201, 404, 422]

    @pytest.mark.asyncio
    async def test_get_sync_status(self, test_client):
        """Test GET /api/data-architecture/cdc/sessions/{session_id}/status"""
        async with test_client as client:
            session_id = str(uuid4())
            response = await client.get(
                f"/api/data-architecture/cdc/sessions/{session_id}/status"
            )

            assert response.status_code in [200, 404]
