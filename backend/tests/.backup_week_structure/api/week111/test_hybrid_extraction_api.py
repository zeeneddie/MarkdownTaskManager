"""
Week 111-114 Phase 5: Hybrid Business Rule Extraction API Tests.

Tests for the hybrid extraction API endpoints that expose
the TierOrchestrator's 5-stage LLM extraction pipeline.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.main import app


client = TestClient(app)


class TestHybridExtractionAPI:
    """Test suite for hybrid extraction API endpoints."""

    def test_get_supported_languages(self):
        """Test GET /api/hybrid-extraction/languages returns all 12 languages."""
        response = client.get("/api/hybrid-extraction/languages")

        assert response.status_code == 200
        data = response.json()

        assert "languages" in data
        assert len(data["languages"]) >= 12

        # Check key languages are present
        language_names = [lang["language"] for lang in data["languages"]]
        assert "VB.NET" in language_names
        assert "Python" in language_names
        assert "JavaScript" in language_names
        assert "T-SQL" in language_names

    def test_get_extraction_tiers(self):
        """Test GET /api/hybrid-extraction/tiers returns all 5 tiers."""
        response = client.get("/api/hybrid-extraction/tiers")

        assert response.status_code == 200
        data = response.json()

        assert "tiers" in data
        assert len(data["tiers"]) == 5

        tier_names = [tier["tier"] for tier in data["tiers"]]
        assert "FREE" in tier_names
        assert "BASIC" in tier_names
        assert "STANDARD" in tier_names
        assert "PROFESSIONAL" in tier_names
        assert "PREMIUM" in tier_names

    def test_get_rule_types(self):
        """Test GET /api/hybrid-extraction/rule-types returns all rule types."""
        response = client.get("/api/hybrid-extraction/rule-types")

        assert response.status_code == 200
        data = response.json()

        assert "rule_types" in data
        assert len(data["rule_types"]) >= 10

        # Check key rule types
        type_names = [rt["type"] for rt in data["rule_types"]]
        assert "VALIDATION" in type_names
        assert "AUTHORIZATION" in type_names
        assert "CALCULATION" in type_names
        assert "WORKFLOW" in type_names

    def test_list_sessions_empty(self):
        """Test GET /api/hybrid-extraction/sessions returns empty list initially."""
        response = client.get("/api/hybrid-extraction/sessions")

        assert response.status_code == 200
        data = response.json()

        # Should return list (may be empty or have existing sessions)
        assert isinstance(data, list)

    def test_get_nonexistent_session(self):
        """Test GET /api/hybrid-extraction/sessions/{id} returns 404 for unknown session."""
        fake_id = str(uuid4())
        response = client.get(f"/api/hybrid-extraction/sessions/{fake_id}")

        assert response.status_code == 404

    def test_get_session_rules_invalid_session(self):
        """Test GET /api/hybrid-extraction/sessions/{id}/rules returns 404 for unknown session."""
        fake_id = str(uuid4())
        response = client.get(f"/api/hybrid-extraction/sessions/{fake_id}/rules")

        assert response.status_code == 404

    def test_get_session_workflows_invalid_session(self):
        """Test GET /api/hybrid-extraction/sessions/{id}/workflows returns 404."""
        fake_id = str(uuid4())
        response = client.get(f"/api/hybrid-extraction/sessions/{fake_id}/workflows")

        assert response.status_code == 404

    def test_get_session_entities_invalid_session(self):
        """Test GET /api/hybrid-extraction/sessions/{id}/entities returns 404."""
        fake_id = str(uuid4())
        response = client.get(f"/api/hybrid-extraction/sessions/{fake_id}/entities")

        assert response.status_code == 404

    @patch('app.api.hybrid_extraction.get_db')
    def test_start_extraction_requires_valid_project(self, mock_get_db):
        """Test POST /api/hybrid-extraction/extract/{project_id} validates project exists."""
        # Mock database session
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = iter([mock_db])

        response = client.post(
            "/api/hybrid-extraction/extract/99999",
            json={
                "source_path": "/path/to/code",
                "extraction_tier": "STANDARD"
            }
        )

        # Should return 404 for non-existent project
        assert response.status_code in [404, 422]


class TestHybridExtractionTierConfidence:
    """Test tier-specific confidence targets."""

    def test_tier_confidence_targets(self):
        """Verify each tier has correct confidence target."""
        response = client.get("/api/hybrid-extraction/tiers")
        data = response.json()

        tier_confidence = {tier["tier"]: tier["confidence_target"] for tier in data["tiers"]}

        assert tier_confidence["FREE"] == 0.60
        assert tier_confidence["BASIC"] == 0.70
        assert tier_confidence["STANDARD"] == 0.80
        assert tier_confidence["PROFESSIONAL"] == 0.90
        assert tier_confidence["PREMIUM"] == 0.95

    def test_tier_llm_counts(self):
        """Verify each tier has correct LLM count."""
        response = client.get("/api/hybrid-extraction/tiers")
        data = response.json()

        tier_llms = {tier["tier"]: tier["llm_count"] for tier in data["tiers"]}

        assert tier_llms["FREE"] == 3
        assert tier_llms["BASIC"] == 5
        assert tier_llms["STANDARD"] == 7
        assert tier_llms["PROFESSIONAL"] == 9
        assert tier_llms["PREMIUM"] == 10


class TestHybridExtractionAgentContext:
    """Test agent context generation for workflows."""

    def test_get_agent_context_invalid_session(self):
        """Test GET /api/hybrid-extraction/sessions/{id}/agent-context/{agent} returns 404."""
        fake_id = str(uuid4())
        response = client.get(f"/api/hybrid-extraction/sessions/{fake_id}/agent-context/miguel")

        assert response.status_code == 404

    def test_invalid_agent_name(self):
        """Test invalid agent names are handled gracefully."""
        fake_id = str(uuid4())
        response = client.get(f"/api/hybrid-extraction/sessions/{fake_id}/agent-context/invalid_agent")

        # Should return 404 (session not found first) or 400 (invalid agent)
        assert response.status_code in [400, 404]


class TestHybridExtractionRuleTypes:
    """Test rule type categorization."""

    def test_rule_type_descriptions(self):
        """Verify each rule type has a description."""
        response = client.get("/api/hybrid-extraction/rule-types")
        data = response.json()

        for rule_type in data["rule_types"]:
            assert "type" in rule_type
            assert "description" in rule_type
            assert len(rule_type["description"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
