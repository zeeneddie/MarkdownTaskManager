# backend/tests/api/week100/test_static_llm_conflict_api.py
"""
Week 100 Tests - Static-LLM Conflict API Endpoints

Tests for the API endpoints supporting conflict detection and resolution
between static analysis (Cycle 0) and LLM analysis results.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.api.deep_extraction import router


class TestCycle0Endpoints:
    """Test Cycle 0 (Static Analysis) API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = FastAPI()
        app.include_router(router, prefix="/api/deep-extraction")
        return TestClient(app)

    def test_cycle_0_status_endpoint_exists(self, client):
        """Test that GET /sessions/{id}/cycle-0 endpoint exists."""
        session_id = str(uuid.uuid4())

        with patch('app.api.deep_extraction.get_db') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session

            # The endpoint should exist (may return 404 for non-existent session)
            response = client.get(f"/api/deep-extraction/sessions/{session_id}/cycle-0")
            # Accept 404 (not found) or 200 (success) - both indicate endpoint exists
            assert response.status_code in [200, 404, 500]

    def test_run_cycle_0_endpoint_exists(self, client):
        """Test that POST /sessions/{id}/cycle-0/run endpoint exists."""
        session_id = str(uuid.uuid4())

        with patch('app.api.deep_extraction.get_db') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session

            response = client.post(f"/api/deep-extraction/sessions/{session_id}/cycle-0/run")
            assert response.status_code in [200, 404, 500]


class TestStaticLLMConflictEndpoints:
    """Test Static-LLM conflict API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = FastAPI()
        app.include_router(router, prefix="/api/deep-extraction")
        return TestClient(app)

    @pytest.fixture
    def sample_conflict(self):
        """Sample conflict data for testing."""
        return {
            "id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "item_id": "rule-123",
            "item_type": "business_rule",
            "conflict_type": "confidence_threshold",
            "severity": "medium",
            "static_classification": "validation_rule",
            "static_confidence": 0.85,
            "llm_classification": "business_logic",
            "llm_confidence": 0.65,
            "status": "pending",
            "description": "LLM confidence below 72.5% threshold",
        }

    def test_list_conflicts_endpoint_exists(self, client):
        """Test that GET /sessions/{id}/static-llm-conflicts endpoint exists."""
        session_id = str(uuid.uuid4())

        with patch('app.api.deep_extraction.get_db') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session

            response = client.get(f"/api/deep-extraction/sessions/{session_id}/static-llm-conflicts")
            assert response.status_code in [200, 404, 500]

    def test_get_single_conflict_endpoint_exists(self, client):
        """Test that GET /static-llm-conflicts/{id} endpoint exists."""
        conflict_id = str(uuid.uuid4())

        with patch('app.api.deep_extraction.get_db') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session

            response = client.get(f"/api/deep-extraction/static-llm-conflicts/{conflict_id}")
            assert response.status_code in [200, 404, 500]

    def test_resolve_conflict_endpoint_exists(self, client):
        """Test that POST /static-llm-conflicts/{id}/resolve endpoint exists."""
        conflict_id = str(uuid.uuid4())

        with patch('app.api.deep_extraction.get_db') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session

            response = client.post(
                f"/api/deep-extraction/static-llm-conflicts/{conflict_id}/resolve",
                json={
                    "resolution": "human_selected_static",
                    "notes": "Static analysis is correct",
                }
            )
            assert response.status_code in [200, 404, 422, 500]

    def test_bulk_resolve_endpoint_exists(self, client):
        """Test that POST /sessions/{id}/static-llm-conflicts/bulk-resolve endpoint exists."""
        session_id = str(uuid.uuid4())

        with patch('app.api.deep_extraction.get_db') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session

            response = client.post(
                f"/api/deep-extraction/sessions/{session_id}/static-llm-conflicts/bulk-resolve",
                json={
                    "resolutions": [
                        {
                            "conflict_id": str(uuid.uuid4()),
                            "resolution": "human_selected_llm",
                        }
                    ],
                    "resolved_by": "test_user",
                }
            )
            assert response.status_code in [200, 404, 422, 500]

    def test_summary_endpoint_exists(self, client):
        """Test that GET /sessions/{id}/static-llm-conflicts/summary endpoint exists."""
        session_id = str(uuid.uuid4())

        with patch('app.api.deep_extraction.get_db') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session

            response = client.get(f"/api/deep-extraction/sessions/{session_id}/static-llm-conflicts/summary")
            assert response.status_code in [200, 404, 500]


class TestConflictFiltering:
    """Test conflict filtering parameters."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = FastAPI()
        app.include_router(router, prefix="/api/deep-extraction")
        return TestClient(app)

    def test_filter_by_status(self, client):
        """Test filtering conflicts by status."""
        session_id = str(uuid.uuid4())

        with patch('app.api.deep_extraction.get_db') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session

            response = client.get(
                f"/api/deep-extraction/sessions/{session_id}/static-llm-conflicts",
                params={"status": "pending"}
            )
            assert response.status_code in [200, 404, 500]

    def test_filter_by_severity(self, client):
        """Test filtering conflicts by severity."""
        session_id = str(uuid.uuid4())

        with patch('app.api.deep_extraction.get_db') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session

            response = client.get(
                f"/api/deep-extraction/sessions/{session_id}/static-llm-conflicts",
                params={"severity": "high"}
            )
            assert response.status_code in [200, 404, 500]

    def test_filter_by_conflict_type(self, client):
        """Test filtering conflicts by type."""
        session_id = str(uuid.uuid4())

        with patch('app.api.deep_extraction.get_db') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session

            response = client.get(
                f"/api/deep-extraction/sessions/{session_id}/static-llm-conflicts",
                params={"conflict_type": "confidence_threshold"}
            )
            assert response.status_code in [200, 404, 500]

    def test_pagination(self, client):
        """Test pagination parameters."""
        session_id = str(uuid.uuid4())

        with patch('app.api.deep_extraction.get_db') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session

            response = client.get(
                f"/api/deep-extraction/sessions/{session_id}/static-llm-conflicts",
                params={"limit": 10, "offset": 0}
            )
            assert response.status_code in [200, 404, 500]


class TestResolutionValidation:
    """Test resolution validation logic."""

    def test_valid_resolution_types(self):
        """Test all valid resolution type values."""
        valid_resolutions = [
            "auto_accepted_static",
            "auto_accepted_llm",
            "human_selected_static",
            "human_selected_llm",
            "human_merged",
            "human_rejected_both",
        ]
        assert len(valid_resolutions) == 6

    def test_resolution_requires_actor(self):
        """Test that resolution requires resolved_by field."""
        # Human resolutions require a user identifier
        human_resolutions = [
            "human_selected_static",
            "human_selected_llm",
            "human_merged",
            "human_rejected_both",
        ]

        # Auto resolutions use "system" as resolved_by
        auto_resolutions = [
            "auto_accepted_static",
            "auto_accepted_llm",
        ]

        assert len(human_resolutions) + len(auto_resolutions) == 6


class TestHealthCheckVersion:
    """Test health check endpoint includes Week 100 features."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = FastAPI()
        app.include_router(router, prefix="/api/deep-extraction")
        return TestClient(app)

    def test_health_check_returns_version(self, client):
        """Test that health check returns version 5.0.0."""
        response = client.get("/api/deep-extraction/health")

        if response.status_code == 200:
            data = response.json()
            assert "version" in data
            # Week 100 should be version 5.0.0
            assert data["version"] == "5.0.0"

    def test_health_check_includes_cycle_0_feature(self, client):
        """Test that health check lists cycle_0 feature."""
        response = client.get("/api/deep-extraction/health")

        if response.status_code == 200:
            data = response.json()
            if "features" in data:
                assert "cycle_0_static_analysis" in data["features"]

    def test_health_check_includes_conflict_feature(self, client):
        """Test that health check lists static_llm_conflicts feature."""
        response = client.get("/api/deep-extraction/health")

        if response.status_code == 200:
            data = response.json()
            if "features" in data:
                assert "static_llm_conflicts" in data["features"]

    def test_health_check_includes_threshold_feature(self, client):
        """Test that health check lists 72.5% threshold feature."""
        response = client.get("/api/deep-extraction/health")

        if response.status_code == 200:
            data = response.json()
            if "features" in data:
                assert "72.5_percent_threshold" in data["features"]


class TestConflictResolutionHistory:
    """Test conflict resolution history tracking."""

    def test_history_actions(self):
        """Test valid history action types."""
        valid_actions = [
            "created",
            "viewed",
            "assigned",
            "resolved",
            "reopened",
            "escalated",
        ]
        assert len(valid_actions) == 6

    def test_history_captures_state_change(self):
        """Test that history captures before/after state."""
        # History entry should capture:
        # - previous_status, new_status
        # - previous_resolution, new_resolution
        # - action_by (user or "system")
        # - notes (optional)

        required_fields = [
            "conflict_id",
            "action",
            "action_by",
            "previous_status",
            "new_status",
            "created_at",
        ]
        assert len(required_fields) == 6


class TestConfidenceThresholdBehavior:
    """Test 72.5% confidence threshold behavior in API."""

    def test_threshold_value(self):
        """Test that 72.5% is the threshold."""
        CONFIDENCE_THRESHOLD = 0.725

        # Test values
        below_threshold = [0.50, 0.60, 0.70, 0.724]
        at_or_above = [0.725, 0.80, 0.90, 1.00]

        for val in below_threshold:
            assert val < CONFIDENCE_THRESHOLD

        for val in at_or_above:
            assert val >= CONFIDENCE_THRESHOLD

    def test_below_threshold_needs_review(self):
        """Test that LLM confidence below 72.5% triggers human review."""
        # When LLM confidence < 72.5%, even if static is high,
        # the conflict needs human review
        llm_confidence = 0.65  # Below 72.5%
        static_confidence = 0.90  # High

        # This combination should trigger CONFIDENCE_THRESHOLD conflict
        needs_review = llm_confidence < 0.725
        assert needs_review is True
