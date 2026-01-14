"""
Tests for DualRunComparisonService - Week 134-135

Tests parallel execution of legacy and new systems with output comparison.

Agent: Tessa (Test Engineer)
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from app.services.dual_run_comparison_service import (
    DualRunComparisonService,
    SystemConfig,
    DualRunStatistics,
)
from app.models.testing import (
    ComparisonResult,
    DiffType,
    DualRunResult,
    FieldDifference,
)


class TestDualRunComparisonService:
    """Test suite for DualRunComparisonService."""

    @pytest.fixture
    def legacy_config(self):
        """Create legacy system config."""
        return SystemConfig(
            url="http://legacy.example.com",
            name="legacy-system",
            headers={"Authorization": "Bearer legacy-token"},
        )

    @pytest.fixture
    def new_config(self):
        """Create new system config."""
        return SystemConfig(
            url="http://new.example.com",
            name="new-system",
            headers={"Authorization": "Bearer new-token"},
        )

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        return DualRunComparisonService()

    @pytest.fixture
    async def session(self, service, legacy_config, new_config):
        """Create a comparison session."""
        session_id = await service.create_comparison_session(
            comparison_id="test-session",
            legacy_config=legacy_config,
            new_config=new_config,
            shadow_mode=True,
        )
        return session_id

    # =========================================================================
    # Session Configuration Tests
    # =========================================================================

    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service._timeout is not None
        assert service._sessions == {}
        assert service._statistics == {}

    @pytest.mark.asyncio
    async def test_create_session(self, service, legacy_config, new_config):
        """Test creating a comparison session."""
        session_id = await service.create_comparison_session(
            comparison_id="my-session",
            legacy_config=legacy_config,
            new_config=new_config,
            shadow_mode=True,
        )

        assert session_id == "my-session"
        assert "my-session" in service._sessions
        assert "my-session" in service._statistics

    @pytest.mark.asyncio
    async def test_session_configuration(self, service, legacy_config, new_config):
        """Test session stores configuration correctly."""
        await service.create_comparison_session(
            comparison_id="config-test",
            legacy_config=legacy_config,
            new_config=new_config,
            shadow_mode=False,
            ignored_fields=["timestamp"],
            field_mappings={"old_name": "new_name"},
        )

        session = service._sessions["config-test"]
        assert session["legacy"] == legacy_config
        assert session["new"] == new_config
        assert session["shadow_mode"] is False
        assert session["ignored_fields"] == ["timestamp"]
        assert session["field_mappings"] == {"old_name": "new_name"}

    # =========================================================================
    # Request Execution Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_execute_request_match(self, service, session):
        """Test executing a request when both systems return same output."""
        response = {"status_code": 200, "body": {"status": "ok", "data": {"id": 1}}, "duration_ms": 100}

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = response

            result = await service.execute_request(
                comparison_id=session,
                method="GET",
                path="/api/users/1",
            )

            assert result.result == ComparisonResult.MATCH
            assert result.diff_count == 0
            assert result.legacy_status_code == 200
            assert result.new_status_code == 200
            assert mock_call.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_request_mismatch(self, service, session):
        """Test executing a request when systems return different output."""
        legacy_response = {"status_code": 200, "body": {"version": "1.0", "count": 10}, "duration_ms": 100}
        new_response = {"status_code": 200, "body": {"version": "2.0", "count": 10, "extra": "field"}, "duration_ms": 80}

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [legacy_response, new_response]

            result = await service.execute_request(
                comparison_id=session,
                method="GET",
                path="/api/stats",
            )

            assert result.result == ComparisonResult.MISMATCH
            assert result.diff_count > 0
            assert result.legacy_response_time_ms == 100
            assert result.new_response_time_ms == 80

    @pytest.mark.asyncio
    async def test_execute_request_with_data(self, service, session):
        """Test executing a POST request with data."""
        response = {"status_code": 201, "body": {"id": 123, "created": True}, "duration_ms": 150}

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = response

            result = await service.execute_request(
                comparison_id=session,
                method="POST",
                path="/api/users",
                body={"name": "New User", "email": "user@example.com"},
            )

            assert result.result == ComparisonResult.MATCH
            mock_call.assert_called()

    @pytest.mark.asyncio
    async def test_execute_request_status_mismatch(self, service, session):
        """Test request when status codes differ."""
        legacy_response = {"status_code": 200, "body": {"status": "ok"}, "duration_ms": 100}
        new_response = {"status_code": 404, "body": {"error": "not found"}, "duration_ms": 50}

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [legacy_response, new_response]

            result = await service.execute_request(
                comparison_id=session,
                method="GET",
                path="/api/resource",
            )

            assert result.result == ComparisonResult.MISMATCH
            assert result.legacy_status_code == 200
            assert result.new_status_code == 404

    @pytest.mark.asyncio
    async def test_execute_request_error(self, service, session):
        """Test request when an error occurs."""
        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("Connection failed")

            result = await service.execute_request(
                comparison_id=session,
                method="GET",
                path="/api/data",
            )

            assert result.result == ComparisonResult.ERROR

    @pytest.mark.asyncio
    async def test_execute_request_session_not_found(self, service):
        """Test request with invalid session ID."""
        result = await service.execute_request(
            comparison_id="nonexistent",
            method="GET",
            path="/api/data",
        )

        assert result.result == ComparisonResult.ERROR
        assert "not found" in result.new_error.lower()

    # =========================================================================
    # Batch Execution Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_execute_batch(self, service, session):
        """Test executing a batch of requests."""
        response = {"status_code": 200, "body": {"status": "ok"}, "duration_ms": 100}

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = response

            requests = [
                {"path": "/api/users/1", "method": "GET"},
                {"path": "/api/users/2", "method": "GET"},
                {"path": "/api/users/3", "method": "GET"},
            ]

            results = await service.execute_batch(session, requests)

            assert len(results) == 3
            assert all(r.result == ComparisonResult.MATCH for r in results)

    @pytest.mark.asyncio
    async def test_execute_batch_mixed_results(self, service, session):
        """Test batch with mixed results."""
        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [
                {"status_code": 200, "body": {"data": 1}, "duration_ms": 100},
                {"status_code": 200, "body": {"data": 1}, "duration_ms": 90},
                {"status_code": 200, "body": {"data": 2}, "duration_ms": 100},
                {"status_code": 200, "body": {"data": 3}, "duration_ms": 90},
            ]

            requests = [
                {"path": "/api/data/1", "method": "GET"},
                {"path": "/api/data/2", "method": "GET"},
            ]

            results = await service.execute_batch(session, requests)

            assert len(results) == 2
            assert results[0].result == ComparisonResult.MATCH
            assert results[1].result == ComparisonResult.MISMATCH

    # =========================================================================
    # Traffic Replay Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_replay_traffic(self, service, session):
        """Test replaying recorded traffic."""
        response = {"status_code": 200, "body": {"status": "ok"}, "duration_ms": 100}

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = response

            traffic_log = [
                {
                    "path": "/api/users",
                    "method": "GET",
                    "timestamp": "2025-01-01T10:00:00+00:00",
                },
                {
                    "path": "/api/orders",
                    "method": "POST",
                    "body": {"item_id": 1},
                    "timestamp": "2025-01-01T10:00:01+00:00",
                },
            ]

            results = await service.replay_traffic(session, traffic_log)

            assert len(results) == 2

    # =========================================================================
    # Statistics Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_statistics_empty(self, service, session):
        """Test statistics when no requests executed."""
        stats = service.get_statistics(session)

        assert isinstance(stats, DualRunStatistics)
        assert stats.total_requests == 0
        assert stats.matched_requests == 0
        assert stats.mismatched_requests == 0
        assert stats.error_requests == 0
        assert stats.match_rate == 0.0

    @pytest.mark.asyncio
    async def test_get_statistics_after_requests(self, service, session):
        """Test statistics after executing requests."""
        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [
                {"status_code": 200, "body": {"data": 1}, "duration_ms": 100},
                {"status_code": 200, "body": {"data": 1}, "duration_ms": 80},
                {"status_code": 200, "body": {"data": 2}, "duration_ms": 100},
                {"status_code": 200, "body": {"data": 3}, "duration_ms": 80},
            ]

            await service.execute_request(session, "GET", "/api/data/1")
            await service.execute_request(session, "GET", "/api/data/2")

            stats = service.get_statistics(session)

            assert stats.total_requests == 2
            assert stats.matched_requests == 1
            assert stats.mismatched_requests == 1
            assert stats.match_rate == 50.0

    @pytest.mark.asyncio
    async def test_statistics_performance_tracking(self, service, session):
        """Test performance tracking in statistics."""
        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [
                {"status_code": 200, "body": {"data": 1}, "duration_ms": 100},
                {"status_code": 200, "body": {"data": 1}, "duration_ms": 50},
                {"status_code": 200, "body": {"data": 2}, "duration_ms": 200},
                {"status_code": 200, "body": {"data": 2}, "duration_ms": 100},
            ]

            await service.execute_request(session, "GET", "/api/data/1")
            await service.execute_request(session, "GET", "/api/data/2")

            stats = service.get_statistics(session)

            assert stats.avg_legacy_time_ms == 150.0
            assert stats.avg_new_time_ms == 75.0
            assert stats.performance_improvement > 0

    @pytest.mark.asyncio
    async def test_statistics_nonexistent_session(self, service):
        """Test getting statistics for nonexistent session."""
        stats = service.get_statistics("nonexistent")
        assert stats is None

    # =========================================================================
    # Session Management Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_stop_session(self, service, session):
        """Test stopping a session."""
        assert service.is_session_active(session) is True

        success = service.stop_session(session)

        assert success is True
        assert service.is_session_active(session) is False

    def test_stop_nonexistent_session(self, service):
        """Test stopping nonexistent session."""
        success = service.stop_session("nonexistent")
        assert success is False

    # =========================================================================
    # Comparison Logic Tests
    # =========================================================================

    def test_compare_responses_identical(self, service):
        """Test comparison of identical responses."""
        response = {"a": 1, "b": {"c": 2}}

        diffs = service._compare_responses(response, response, [], {})
        assert len(diffs) == 0

    def test_compare_responses_different(self, service):
        """Test comparison of different responses."""
        legacy = {"a": 1, "b": 2}
        new = {"a": 1, "b": 3}

        diffs = service._compare_responses(legacy, new, [], {})
        assert len(diffs) == 1
        assert diffs[0].field_path == "b"

    def test_compare_responses_with_ignore(self, service):
        """Test comparison with ignored fields."""
        legacy = {"id": 1, "data": "same"}
        new = {"id": 2, "data": "same"}

        diffs = service._compare_responses(legacy, new, ["id"], {})
        assert len(diffs) == 0

    def test_compare_nested_objects(self, service):
        """Test comparison of nested objects."""
        legacy = {"user": {"name": "Alice", "profile": {"age": 30}}}
        new = {"user": {"name": "Alice", "profile": {"age": 31}}}

        diffs = service._compare_responses(legacy, new, [], {})
        assert len(diffs) == 1
        assert "profile.age" in diffs[0].field_path or "age" in diffs[0].field_path

    def test_compare_arrays(self, service):
        """Test comparison of arrays."""
        legacy = {"items": [1, 2, 3]}
        new = {"items": [1, 2, 4]}

        diffs = service._compare_responses(legacy, new, [], {})
        assert len(diffs) == 1

    def test_compare_array_length_change(self, service):
        """Test comparison when array length differs."""
        legacy = {"items": [1, 2, 3]}
        new = {"items": [1, 2]}

        diffs = service._compare_responses(legacy, new, [], {})
        assert len(diffs) == 1
        assert diffs[0].message is not None and "length" in diffs[0].message.lower()

    def test_compare_type_change(self, service):
        """Test comparison when types differ."""
        legacy = {"value": "string"}
        new = {"value": 123}

        diffs = service._compare_responses(legacy, new, [], {})
        assert len(diffs) == 1
        assert diffs[0].diff_type == DiffType.TYPE_CHANGE

    def test_compare_with_field_mapping(self, service):
        """Test comparison with field mappings."""
        legacy = {"old_field": "value"}
        new = {"new_field": "value"}

        diffs = service._compare_responses(legacy, new, [], {"old_field": "new_field"})
        assert len(diffs) == 0

    # =========================================================================
    # System Config Tests
    # =========================================================================

    def test_system_config_creation(self):
        """Test SystemConfig creation."""
        config = SystemConfig(
            url="http://example.com",
            name="test-system",
            headers={"X-API-Key": "secret"},
            timeout_ms=60000,
        )

        assert config.url == "http://example.com"
        assert config.name == "test-system"
        assert config.headers == {"X-API-Key": "secret"}
        assert config.timeout_ms == 60000

    def test_system_config_defaults(self):
        """Test SystemConfig defaults."""
        config = SystemConfig(url="http://example.com", name="test")

        assert config.type == "http"
        assert config.headers == {}
        assert config.timeout_ms == 30000
        assert config.retry_count == 0

    # =========================================================================
    # Error Handling Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_legacy_system_error(self, service, session):
        """Test handling when legacy system fails."""
        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("Legacy system unavailable")

            result = await service.execute_request(session, "GET", "/api/data")

            assert result.result == ComparisonResult.ERROR

    @pytest.mark.asyncio
    async def test_new_system_error(self, service, session):
        """Test handling when new system fails."""
        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [
                {"status_code": 200, "body": {"data": 1}, "duration_ms": 100},
                Exception("New system unavailable"),
            ]

            result = await service.execute_request(session, "GET", "/api/data")

            assert result.result == ComparisonResult.ERROR

    # =========================================================================
    # Correlation ID Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_correlation_id_generation(self, service, session):
        """Test that each request gets a correlation ID."""
        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"status_code": 200, "body": {"data": 1}, "duration_ms": 100}

            result1 = await service.execute_request(session, "GET", "/api/data")
            result2 = await service.execute_request(session, "GET", "/api/data")

            assert result1.correlation_id is not None
            assert result2.correlation_id is not None
            assert result1.correlation_id != result2.correlation_id

    @pytest.mark.asyncio
    async def test_custom_correlation_id(self, service, session):
        """Test providing custom correlation ID."""
        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"status_code": 200, "body": {"data": 1}, "duration_ms": 100}

            result = await service.execute_request(
                session, "GET", "/api/data",
                correlation_id="my-custom-id",
            )

            assert result.correlation_id == "my-custom-id"
