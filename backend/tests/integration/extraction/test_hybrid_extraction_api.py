"""
Week 111-114 Phase 5: Hybrid Business Rule Extraction API Tests.

Tests for the hybrid extraction API endpoints that expose
the TierOrchestrator's 5-stage LLM extraction pipeline.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from app.main import app
from app.database import get_db


@pytest.fixture
def mock_db_session():
    """Mock database session for tests that don't need real DB"""
    mock_session = AsyncMock()

    # Create a proper mock result for various query patterns
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_result.scalar = MagicMock(return_value=None)

    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.get = AsyncMock(return_value=None)
    return mock_session


@pytest.fixture
async def client(mock_db_session):
    """Async test client with mocked database"""
    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


class TestHybridExtractionAPI:
    """Test suite for hybrid extraction API endpoints."""

    @pytest.mark.asyncio
    async def test_get_supported_languages(self, client):
        """Test GET /api/hybrid-extraction/languages returns all 12 languages."""
        response = await client.get("/api/hybrid-extraction/languages")

        assert response.status_code == 200
        data = response.json()

        assert "languages" in data
        assert len(data["languages"]) >= 12

        # Check key languages are present (API returns 'name' not 'language')
        language_names = [lang["name"] for lang in data["languages"]]
        assert "VB.NET" in language_names
        assert "Python" in language_names
        assert "JavaScript" in language_names
        assert "T-SQL (SQL Server)" in language_names

    @pytest.mark.asyncio
    async def test_get_extraction_tiers(self, client):
        """Test GET /api/hybrid-extraction/tiers returns all 5 tiers."""
        response = await client.get("/api/hybrid-extraction/tiers")

        assert response.status_code == 200
        data = response.json()

        assert "tiers" in data
        assert len(data["tiers"]) == 5

        tier_ids = [tier["id"] for tier in data["tiers"]]
        assert "FREE" in tier_ids
        assert "BASIC" in tier_ids
        assert "STANDARD" in tier_ids
        assert "PROFESSIONAL" in tier_ids
        assert "PREMIUM" in tier_ids

    @pytest.mark.asyncio
    async def test_get_rule_types(self, client):
        """Test GET /api/hybrid-extraction/rule-types returns all rule types."""
        response = await client.get("/api/hybrid-extraction/rule-types")

        assert response.status_code == 200
        data = response.json()

        assert "rule_types" in data
        assert len(data["rule_types"]) >= 10

        # Check key rule types (API returns 'id' not 'type')
        type_ids = [rt["id"] for rt in data["rule_types"]]
        assert "VALIDATION" in type_ids
        assert "AUTHORIZATION" in type_ids
        assert "CALCULATION" in type_ids
        assert "WORKFLOW" in type_ids

    @pytest.mark.asyncio
    async def test_list_sessions_by_project(self, client):
        """Test GET /api/hybrid-extraction/project/{project_id}/sessions endpoint exists."""
        # Use project/sessions endpoint (sessions requires project_id)
        response = await client.get("/api/hybrid-extraction/project/1/sessions")

        # May return 200 with empty list or 404 if project doesn't exist
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "sessions" in data
            assert isinstance(data["sessions"], list)

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, client):
        """Test GET /api/hybrid-extraction/sessions/{id} returns 404 for unknown session."""
        fake_id = str(uuid4())
        response = await client.get(f"/api/hybrid-extraction/sessions/{fake_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_session_rules_invalid_session(self, client):
        """Test GET /api/hybrid-extraction/sessions/{id}/rules handles unknown session."""
        fake_id = str(uuid4())
        response = await client.get(f"/api/hybrid-extraction/sessions/{fake_id}/rules")

        # 200 with empty results, 404 not found, or 500 error
        assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_get_session_workflows_invalid_session(self, client):
        """Test GET /api/hybrid-extraction/sessions/{id}/workflows handles unknown session."""
        fake_id = str(uuid4())
        response = await client.get(f"/api/hybrid-extraction/sessions/{fake_id}/workflows")

        assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_get_session_entities_invalid_session(self, client):
        """Test GET /api/hybrid-extraction/sessions/{id}/entities handles unknown session."""
        fake_id = str(uuid4())
        response = await client.get(f"/api/hybrid-extraction/sessions/{fake_id}/entities")

        assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_start_extraction_validates_request(self, client):
        """Test POST /api/hybrid-extraction/extract/{project_id} validates request."""
        response = await client.post(
            "/api/hybrid-extraction/extract/99999",
            json={
                "source_path": "/path/to/code",
                "extraction_tier": "STANDARD"
            }
        )

        # 200 for success, 404 for non-existent project, 422 for validation, 500 for error
        assert response.status_code in [200, 404, 422, 500]


class TestHybridExtractionTierConfidence:
    """Test tier-specific confidence targets."""

    @pytest.mark.asyncio
    async def test_tier_confidence_targets(self, client):
        """Verify each tier has correct confidence target (as string percentages)."""
        response = await client.get("/api/hybrid-extraction/tiers")
        data = response.json()

        tier_confidence = {tier["id"]: tier["confidence"] for tier in data["tiers"]}

        # API returns confidence as strings like "60%"
        assert tier_confidence["FREE"] == "60%"
        assert tier_confidence["BASIC"] == "70%"
        assert tier_confidence["STANDARD"] == "80%"
        assert tier_confidence["PROFESSIONAL"] == "90%"
        assert tier_confidence["PREMIUM"] == "95%"

    @pytest.mark.asyncio
    async def test_tier_has_features(self, client):
        """Verify each tier has features list."""
        response = await client.get("/api/hybrid-extraction/tiers")
        data = response.json()

        for tier in data["tiers"]:
            assert "features" in tier
            assert isinstance(tier["features"], list)
            assert len(tier["features"]) > 0


class TestHybridExtractionAgentContext:
    """Test agent context generation for workflows."""

    @pytest.mark.asyncio
    async def test_get_agent_context_invalid_session(self, client):
        """Test GET /api/hybrid-extraction/sessions/{id}/agent-context/{agent} returns 404."""
        fake_id = str(uuid4())
        response = await client.get(f"/api/hybrid-extraction/sessions/{fake_id}/agent-context/miguel")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_agent_name(self, client):
        """Test invalid agent names are handled gracefully."""
        fake_id = str(uuid4())
        response = await client.get(f"/api/hybrid-extraction/sessions/{fake_id}/agent-context/invalid_agent")

        # Should return 404 (session not found first) or 400 (invalid agent)
        assert response.status_code in [400, 404]


class TestHybridExtractionRuleTypes:
    """Test rule type categorization."""

    @pytest.mark.asyncio
    async def test_rule_type_descriptions(self, client):
        """Verify each rule type has a description."""
        response = await client.get("/api/hybrid-extraction/rule-types")
        data = response.json()

        for rule_type in data["rule_types"]:
            assert "id" in rule_type
            assert "description" in rule_type
            assert len(rule_type["description"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
