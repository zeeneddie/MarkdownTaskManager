"""
Tests for DualRunComparisonService - Week 134-135

Tests parallel execution of legacy and new systems with output comparison.

Agent: Tessa (Test Engineer)
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.dual_run_comparison_service import (
    DualRunComparisonService,
    SystemConfig,
    DualRunStatistics,
)
from app.models.testing import (
    ComparisonResult,
    DiffType,
    DualRunResult,
)


class TestDualRunComparisonService:
    """Test suite for DualRunComparisonService."""

    @pytest.fixture
    def legacy_config(self):
        """Create legacy system config."""
        return SystemConfig(
            base_url="http://legacy.example.com",
            headers={"Authorization": "Bearer legacy-token"},
        )

    @pytest.fixture
    def new_config(self):
        """Create new system config."""
        return SystemConfig(
            base_url="http://new.example.com",
            headers={"Authorization": "Bearer new-token"},
        )

    @pytest.fixture
    def service(self, legacy_config, new_config):
        """Create a fresh service instance."""
        return DualRunComparisonService(
            legacy_config=legacy_config,
            new_config=new_config,
            shadow_mode=True,
        )

    # =========================================================================
    # Session Configuration Tests
    # =========================================================================

    def test_service_initialization(self, service, legacy_config, new_config):
        """Test service initializes correctly."""
        assert service._legacy_config == legacy_config
        assert service._new_config == new_config
        assert service._shadow_mode is True

    def test_service_non_shadow_mode(self, legacy_config, new_config):
        """Test service can run in non-shadow mode."""
        service = DualRunComparisonService(
            legacy_config=legacy_config,
            new_config=new_config,
            shadow_mode=False,
        )
        assert service._shadow_mode is False

    # =========================================================================
    # Request Execution Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_execute_request_match(self, service):
        """Test executing a request when both systems return same output."""
        response = {"status": "ok", "data": {"id": 1, "name": "test"}}

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (response, 200, 100)

            result = await service.execute_request(
                endpoint_path="/api/users/1",
                method="GET",
            )

            assert result.result == ComparisonResult.MATCH
            assert result.match_percentage == 100.0
            assert result.diff_count == 0
            assert result.legacy_status == 200
            assert result.new_status == 200
            assert mock_call.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_request_mismatch(self, service):
        """Test executing a request when systems return different output."""
        legacy_response = {"version": "1.0", "count": 10}
        new_response = {"version": "2.0", "count": 10, "extra": "field"}

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [
                (legacy_response, 200, 100),
                (new_response, 200, 80),
            ]

            result = await service.execute_request(
                endpoint_path="/api/stats",
                method="GET",
            )

            assert result.result == ComparisonResult.MISMATCH
            assert result.diff_count > 0
            assert result.legacy_duration_ms == 100
            assert result.new_duration_ms == 80

    @pytest.mark.asyncio
    async def test_execute_request_with_data(self, service):
        """Test executing a POST request with data."""
        response = {"id": 123, "created": True}

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (response, 201, 150)

            result = await service.execute_request(
                endpoint_path="/api/users",
                method="POST",
                request_data={"name": "New User", "email": "user@example.com"},
            )

            assert result.result == ComparisonResult.MATCH
            mock_call.assert_called()

    @pytest.mark.asyncio
    async def test_execute_request_with_query_params(self, service):
        """Test executing a request with query parameters."""
        response = {"results": [1, 2, 3], "total": 3}

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (response, 200, 100)

            result = await service.execute_request(
                endpoint_path="/api/search",
                method="GET",
                query_params={"q": "test", "limit": "10"},
            )

            assert result.result == ComparisonResult.MATCH

    @pytest.mark.asyncio
    async def test_execute_request_with_ignored_fields(self, service):
        """Test request with ignored fields."""
        legacy_response = {"id": 1, "timestamp": "2025-01-01", "data": "same"}
        new_response = {"id": 2, "timestamp": "2025-12-31", "data": "same"}

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [
                (legacy_response, 200, 100),
                (new_response, 200, 90),
            ]

            result = await service.execute_request(
                endpoint_path="/api/data",
                method="GET",
                ignored_fields=["id", "timestamp"],
            )

            assert result.result == ComparisonResult.MATCH

    @pytest.mark.asyncio
    async def test_execute_request_with_tolerance(self, service):
        """Test request with numeric tolerance."""
        legacy_response = {"price": 100.00, "tax": 8.50}
        new_response = {"price": 100.02, "tax": 8.50}

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [
                (legacy_response, 200, 100),
                (new_response, 200, 90),
            ]

            result = await service.execute_request(
                endpoint_path="/api/order",
                method="GET",
                tolerance_rules={"price": 0.05},
            )

            assert result.result == ComparisonResult.MATCH

    @pytest.mark.asyncio
    async def test_execute_request_status_mismatch(self, service):
        """Test request when status codes differ."""
        legacy_response = {"status": "ok"}
        new_response = {"error": "not found"}

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [
                (legacy_response, 200, 100),
                (new_response, 404, 50),
            ]

            result = await service.execute_request(
                endpoint_path="/api/resource",
                method="GET",
            )

            assert result.result == ComparisonResult.MISMATCH
            assert result.legacy_status == 200
            assert result.new_status == 404

    @pytest.mark.asyncio
    async def test_execute_request_error(self, service):
        """Test request when an error occurs."""
        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("Connection failed")

            result = await service.execute_request(
                endpoint_path="/api/data",
                method="GET",
            )

            assert result.result == ComparisonResult.ERROR
            assert "Connection failed" in result.error

    # =========================================================================
    # Batch Execution Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_execute_batch(self, service):
        """Test executing a batch of requests."""
        response = {"status": "ok"}

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (response, 200, 100)

            requests = [
                {"endpoint_path": "/api/users/1", "method": "GET"},
                {"endpoint_path": "/api/users/2", "method": "GET"},
                {"endpoint_path": "/api/users/3", "method": "GET"},
            ]

            results = await service.execute_batch(requests)

            assert len(results) == 3
            assert all(r.result == ComparisonResult.MATCH for r in results)

    @pytest.mark.asyncio
    async def test_execute_batch_mixed_results(self, service):
        """Test batch with mixed results."""
        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            # First request matches
            mock_call.side_effect = [
                ({"data": 1}, 200, 100),
                ({"data": 1}, 200, 90),
                # Second request mismatches
                ({"data": 2}, 200, 100),
                ({"data": 3}, 200, 90),
            ]

            requests = [
                {"endpoint_path": "/api/data/1", "method": "GET"},
                {"endpoint_path": "/api/data/2", "method": "GET"},
            ]

            results = await service.execute_batch(requests)

            assert len(results) == 2
            assert results[0].result == ComparisonResult.MATCH
            assert results[1].result == ComparisonResult.MISMATCH

    @pytest.mark.asyncio
    async def test_execute_batch_with_options(self, service):
        """Test batch with global ignored fields."""
        response = {"id": 1, "timestamp": "2025-01-01", "value": 42}

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (response, 200, 100)

            requests = [
                {"endpoint_path": "/api/data", "method": "GET"},
            ]

            results = await service.execute_batch(
                requests,
                ignored_fields=["id", "timestamp"],
            )

            assert len(results) == 1
            assert results[0].result == ComparisonResult.MATCH

    # =========================================================================
    # Traffic Replay Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_replay_traffic(self, service):
        """Test replaying recorded traffic."""
        response = {"status": "ok"}

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (response, 200, 100)

            traffic_log = [
                {
                    "endpoint_path": "/api/users",
                    "method": "GET",
                    "timestamp": "2025-01-01T10:00:00Z",
                },
                {
                    "endpoint_path": "/api/orders",
                    "method": "POST",
                    "data": {"item_id": 1},
                    "timestamp": "2025-01-01T10:00:01Z",
                },
            ]

            results = await service.replay_traffic(traffic_log)

            assert len(results) == 2

    # =========================================================================
    # Statistics Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_statistics_empty(self, service):
        """Test statistics when no requests executed."""
        stats = service.get_statistics()

        assert isinstance(stats, DualRunStatistics)
        assert stats.total_requests == 0
        assert stats.matches == 0
        assert stats.mismatches == 0
        assert stats.errors == 0
        assert stats.match_rate == 0.0

    @pytest.mark.asyncio
    async def test_get_statistics_after_requests(self, service):
        """Test statistics after executing requests."""
        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            # First request matches
            mock_call.side_effect = [
                ({"data": 1}, 200, 100),
                ({"data": 1}, 200, 80),
                # Second request mismatches
                ({"data": 2}, 200, 100),
                ({"data": 3}, 200, 80),
            ]

            await service.execute_request("/api/data/1", "GET")
            await service.execute_request("/api/data/2", "GET")

            stats = service.get_statistics()

            assert stats.total_requests == 2
            assert stats.matches == 1
            assert stats.mismatches == 1
            assert stats.match_rate == 50.0

    @pytest.mark.asyncio
    async def test_statistics_performance_tracking(self, service):
        """Test performance tracking in statistics."""
        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [
                ({"data": 1}, 200, 100),  # legacy 100ms
                ({"data": 1}, 200, 50),   # new 50ms (faster)
                ({"data": 2}, 200, 200),  # legacy 200ms
                ({"data": 2}, 200, 100),  # new 100ms (faster)
            ]

            await service.execute_request("/api/data/1", "GET")
            await service.execute_request("/api/data/2", "GET")

            stats = service.get_statistics()

            assert stats.avg_legacy_duration_ms == 150.0  # (100+200)/2
            assert stats.avg_new_duration_ms == 75.0      # (50+100)/2
            assert stats.performance_ratio < 1.0         # New is faster

    # =========================================================================
    # Shadow Mode Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_shadow_mode_enabled(self, service):
        """Test shadow mode behavior."""
        assert service._shadow_mode is True

        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = ({"data": 1}, 200, 100)

            result = await service.execute_request("/api/data", "GET")

            # Both systems called
            assert mock_call.call_count == 2

    def test_shadow_mode_disabled(self, legacy_config, new_config):
        """Test non-shadow mode configuration."""
        service = DualRunComparisonService(
            legacy_config=legacy_config,
            new_config=new_config,
            shadow_mode=False,
        )
        assert service._shadow_mode is False

    # =========================================================================
    # Comparison Logic Tests
    # =========================================================================

    def test_compare_responses_identical(self, service):
        """Test comparison of identical responses."""
        response = {"a": 1, "b": {"c": 2}}

        diffs = service._compare_responses(response, response)
        assert len(diffs) == 0

    def test_compare_responses_different(self, service):
        """Test comparison of different responses."""
        legacy = {"a": 1, "b": 2}
        new = {"a": 1, "b": 3}

        diffs = service._compare_responses(legacy, new)
        assert len(diffs) == 1
        assert diffs[0].field_path == "b"

    def test_compare_responses_with_ignore(self, service):
        """Test comparison with ignored fields."""
        legacy = {"id": 1, "data": "same"}
        new = {"id": 2, "data": "same"}

        diffs = service._compare_responses(legacy, new, ignored_fields=["id"])
        assert len(diffs) == 0

    def test_compare_responses_with_tolerance(self, service):
        """Test comparison with tolerance."""
        legacy = {"price": 100.0}
        new = {"price": 100.02}

        diffs_no_tolerance = service._compare_responses(legacy, new)
        assert len(diffs_no_tolerance) == 1

        diffs_with_tolerance = service._compare_responses(
            legacy, new, tolerance_rules={"price": 0.05}
        )
        assert len(diffs_with_tolerance) == 0

    def test_compare_nested_objects(self, service):
        """Test comparison of nested objects."""
        legacy = {"user": {"name": "Alice", "profile": {"age": 30}}}
        new = {"user": {"name": "Alice", "profile": {"age": 31}}}

        diffs = service._compare_responses(legacy, new)
        assert len(diffs) == 1
        assert "profile.age" in diffs[0].field_path

    def test_compare_arrays(self, service):
        """Test comparison of arrays."""
        legacy = {"items": [1, 2, 3]}
        new = {"items": [1, 2, 4]}

        diffs = service._compare_responses(legacy, new)
        assert len(diffs) == 1

    def test_compare_array_length_change(self, service):
        """Test comparison when array length differs."""
        legacy = {"items": [1, 2, 3]}
        new = {"items": [1, 2]}

        diffs = service._compare_responses(legacy, new)
        assert len(diffs) == 1
        assert "length" in diffs[0].message.lower()

    # =========================================================================
    # System Config Tests
    # =========================================================================

    def test_system_config_creation(self):
        """Test SystemConfig creation."""
        config = SystemConfig(
            base_url="http://example.com",
            headers={"X-API-Key": "secret"},
            timeout=30,
        )

        assert config.base_url == "http://example.com"
        assert config.headers == {"X-API-Key": "secret"}
        assert config.timeout == 30

    def test_system_config_defaults(self):
        """Test SystemConfig defaults."""
        config = SystemConfig(base_url="http://example.com")

        assert config.headers is None
        assert config.timeout == 30  # default

    # =========================================================================
    # Error Handling Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_legacy_system_error(self, service):
        """Test handling when legacy system fails."""
        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [
                Exception("Legacy system unavailable"),
            ]

            result = await service.execute_request("/api/data", "GET")

            assert result.result == ComparisonResult.ERROR
            assert "Legacy" in result.error or "legacy" in result.error.lower()

    @pytest.mark.asyncio
    async def test_new_system_error(self, service):
        """Test handling when new system fails."""
        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [
                ({"data": 1}, 200, 100),  # Legacy succeeds
                Exception("New system unavailable"),  # New fails
            ]

            result = await service.execute_request("/api/data", "GET")

            assert result.result == ComparisonResult.ERROR

    # =========================================================================
    # Request ID Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_request_id_generation(self, service):
        """Test that each request gets a unique ID."""
        with patch.object(service, '_call_system', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = ({"data": 1}, 200, 100)

            result1 = await service.execute_request("/api/data", "GET")
            result2 = await service.execute_request("/api/data", "GET")

            assert result1.request_id != result2.request_id
