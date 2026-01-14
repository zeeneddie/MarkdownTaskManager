"""
Tests for CharacterizationTestService - Week 134-135

Tests Golden Master pattern implementation for recording legacy system behavior
and comparing against new system output.

Agent: Tessa (Test Engineer)
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.characterization_test_service import CharacterizationTestService
from app.models.testing import (
    ComparisonResult,
    DiffType,
    FieldDifference,
    CharacterizationTestResult,
    TestInput,
)


class TestCharacterizationTestService:
    """Test suite for CharacterizationTestService."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        return CharacterizationTestService(http_timeout=5)

    # =========================================================================
    # Baseline Recording Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_record_baseline_success(self, service):
        """Test recording a baseline successfully."""
        mock_response = {"status": "ok", "data": {"id": 1, "name": "test"}}

        with patch.object(service, '_call_endpoint', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (mock_response, 100)

            result = await service.record_baseline(
                test_id="test-001",
                test_name="Test Baseline Recording",
                legacy_endpoint="http://legacy.example.com/api/data",
                input_data={"query": "test"},
            )

            assert result.result == ComparisonResult.NEW_BASELINE
            assert result.legacy_output == mock_response
            assert result.legacy_duration_ms == 100
            assert result.match_percentage == 100.0
            assert result.error is None

    @pytest.mark.asyncio
    async def test_record_baseline_with_scenario(self, service):
        """Test recording baseline with input scenario name."""
        mock_response = {"result": "success"}

        with patch.object(service, '_call_endpoint', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (mock_response, 50)

            result = await service.record_baseline(
                test_id="test-002",
                test_name="Scenario Test",
                legacy_endpoint="http://legacy.example.com/api",
                input_data={"id": 123},
                input_scenario="Happy Path",
            )

            assert result.input_scenario == "Happy Path"
            assert result.result == ComparisonResult.NEW_BASELINE

    @pytest.mark.asyncio
    async def test_record_baseline_error(self, service):
        """Test baseline recording handles errors."""
        with patch.object(service, '_call_endpoint', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("Connection failed")

            result = await service.record_baseline(
                test_id="test-003",
                test_name="Error Test",
                legacy_endpoint="http://legacy.example.com/api",
                input_data={},
            )

            assert result.result == ComparisonResult.ERROR
            assert "Connection failed" in result.error

    # =========================================================================
    # Baseline Comparison Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_compare_with_baseline_match(self, service):
        """Test comparison when outputs match exactly."""
        baseline = {"status": "ok", "count": 10}

        # First record baseline
        service.set_baseline("test-match", baseline)

        with patch.object(service, '_call_endpoint', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (baseline, 80)

            result = await service.compare_with_baseline(
                test_id="test-match",
                test_name="Match Test",
                new_endpoint="http://new.example.com/api",
                input_data={"query": "test"},
            )

            assert result.result == ComparisonResult.MATCH
            assert result.match_percentage == 100.0
            assert result.diff_count == 0
            assert len(result.differences) == 0

    @pytest.mark.asyncio
    async def test_compare_with_baseline_mismatch(self, service):
        """Test comparison when outputs differ."""
        baseline = {"status": "ok", "count": 10, "items": ["a", "b"]}
        new_output = {"status": "ok", "count": 15, "items": ["a", "b", "c"]}

        service.set_baseline("test-mismatch", baseline)

        with patch.object(service, '_call_endpoint', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (new_output, 90)

            result = await service.compare_with_baseline(
                test_id="test-mismatch",
                test_name="Mismatch Test",
                new_endpoint="http://new.example.com/api",
                input_data={},
            )

            assert result.result == ComparisonResult.MISMATCH
            assert result.diff_count > 0
            assert result.match_percentage < 100.0

    @pytest.mark.asyncio
    async def test_compare_with_ignored_fields(self, service):
        """Test comparison with ignored fields."""
        baseline = {"id": 1, "timestamp": "2025-01-01", "data": "same"}
        new_output = {"id": 2, "timestamp": "2025-12-31", "data": "same"}

        service.set_baseline("test-ignore", baseline)

        with patch.object(service, '_call_endpoint', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (new_output, 75)

            result = await service.compare_with_baseline(
                test_id="test-ignore",
                test_name="Ignore Fields Test",
                new_endpoint="http://new.example.com/api",
                input_data={},
                ignored_fields=["id", "timestamp"],
            )

            assert result.result == ComparisonResult.MATCH
            assert result.match_percentage == 100.0

    @pytest.mark.asyncio
    async def test_compare_with_tolerance_rules(self, service):
        """Test comparison with numeric tolerance."""
        baseline = {"price": 100.00, "quantity": 10}
        new_output = {"price": 100.05, "quantity": 10}

        service.set_baseline("test-tolerance", baseline)

        with patch.object(service, '_call_endpoint', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (new_output, 60)

            result = await service.compare_with_baseline(
                test_id="test-tolerance",
                test_name="Tolerance Test",
                new_endpoint="http://new.example.com/api",
                input_data={},
                tolerance_rules={"price": 0.1},
            )

            assert result.result == ComparisonResult.MATCH

    @pytest.mark.asyncio
    async def test_compare_missing_baseline(self, service):
        """Test comparison without baseline returns error."""
        result = await service.compare_with_baseline(
            test_id="nonexistent",
            test_name="Missing Baseline Test",
            new_endpoint="http://new.example.com/api",
            input_data={},
        )

        assert result.result == ComparisonResult.ERROR
        assert "No baseline found" in result.error

    # =========================================================================
    # Full Test (Both Systems) Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_run_full_test_match(self, service):
        """Test full test when both systems return same output."""
        output = {"status": "ok", "value": 42}

        with patch.object(service, '_call_endpoint', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (output, 100)

            result = await service.run_full_test(
                test_id="full-match",
                test_name="Full Match Test",
                legacy_endpoint="http://legacy.example.com/api",
                new_endpoint="http://new.example.com/api",
                input_data={"query": "test"},
            )

            assert result.result == ComparisonResult.MATCH
            assert result.match_percentage == 100.0
            assert mock_call.call_count == 2

    @pytest.mark.asyncio
    async def test_run_full_test_mismatch(self, service):
        """Test full test when systems return different output."""
        legacy_output = {"version": "1.0", "data": [1, 2, 3]}
        new_output = {"version": "2.0", "data": [1, 2, 3, 4]}

        with patch.object(service, '_call_endpoint', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [
                (legacy_output, 100),
                (new_output, 80),
            ]

            result = await service.run_full_test(
                test_id="full-mismatch",
                test_name="Full Mismatch Test",
                legacy_endpoint="http://legacy.example.com/api",
                new_endpoint="http://new.example.com/api",
                input_data={},
            )

            assert result.result == ComparisonResult.MISMATCH
            assert result.legacy_output == legacy_output
            assert result.new_output == new_output
            assert result.legacy_duration_ms == 100
            assert result.new_duration_ms == 80

    # =========================================================================
    # Batch Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_run_batch_tests(self, service):
        """Test running batch of tests."""
        output = {"result": "ok"}

        with patch.object(service, '_call_endpoint', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (output, 50)

            test_inputs = [
                TestInput(name="Scenario 1", data={"id": 1}),
                TestInput(name="Scenario 2", data={"id": 2}),
                TestInput(name="Scenario 3", data={"id": 3}),
            ]

            results = await service.run_batch_tests(
                test_id="batch-001",
                test_name="Batch Test",
                legacy_endpoint="http://legacy.example.com/api",
                new_endpoint="http://new.example.com/api",
                test_inputs=test_inputs,
            )

            assert len(results) == 3
            assert all(r.result == ComparisonResult.MATCH for r in results)
            assert mock_call.call_count == 6  # 2 calls per test

    # =========================================================================
    # Comparison Logic Tests
    # =========================================================================

    def test_compare_outputs_same_values(self, service):
        """Test deep comparison with identical values."""
        expected = {"a": 1, "b": {"c": 2}}
        actual = {"a": 1, "b": {"c": 2}}

        diffs = service._compare_outputs(expected, actual)
        assert len(diffs) == 0

    def test_compare_outputs_value_change(self, service):
        """Test detection of value changes."""
        expected = {"name": "old", "count": 5}
        actual = {"name": "new", "count": 5}

        diffs = service._compare_outputs(expected, actual)
        assert len(diffs) == 1
        assert diffs[0].field_path == "name"
        assert diffs[0].diff_type == DiffType.MODIFIED

    def test_compare_outputs_nested_change(self, service):
        """Test detection of nested value changes."""
        expected = {"user": {"name": "Alice", "age": 30}}
        actual = {"user": {"name": "Alice", "age": 31}}

        diffs = service._compare_outputs(expected, actual)
        assert len(diffs) == 1
        assert diffs[0].field_path == "user.age"

    def test_compare_outputs_added_field(self, service):
        """Test detection of added fields."""
        expected = {"a": 1}
        actual = {"a": 1, "b": 2}

        diffs = service._compare_outputs(expected, actual)
        assert len(diffs) == 1
        assert diffs[0].diff_type == DiffType.ADDED

    def test_compare_outputs_removed_field(self, service):
        """Test detection of removed fields."""
        expected = {"a": 1, "b": 2}
        actual = {"a": 1}

        diffs = service._compare_outputs(expected, actual)
        assert len(diffs) == 1
        assert diffs[0].diff_type == DiffType.REMOVED

    def test_compare_outputs_type_change(self, service):
        """Test detection of type changes."""
        expected = {"value": "string"}
        actual = {"value": 123}

        diffs = service._compare_outputs(expected, actual)
        assert len(diffs) == 1
        assert diffs[0].diff_type == DiffType.TYPE_CHANGE

    def test_compare_outputs_array_length_change(self, service):
        """Test detection of array length changes."""
        expected = {"items": [1, 2, 3]}
        actual = {"items": [1, 2]}

        diffs = service._compare_outputs(expected, actual)
        assert len(diffs) == 1
        assert "Array length" in diffs[0].message

    def test_compare_outputs_with_ignore(self, service):
        """Test comparison with ignored fields."""
        expected = {"id": 1, "timestamp": "old", "data": "same"}
        actual = {"id": 2, "timestamp": "new", "data": "same"}

        diffs = service._compare_outputs(
            expected, actual, ignored_fields=["id", "timestamp"]
        )
        assert len(diffs) == 0

    def test_compare_outputs_with_tolerance(self, service):
        """Test numeric comparison with tolerance."""
        expected = {"price": 100.0}
        actual = {"price": 100.05}

        # Without tolerance
        diffs_no_tolerance = service._compare_outputs(expected, actual)
        assert len(diffs_no_tolerance) == 1

        # With tolerance
        diffs_with_tolerance = service._compare_outputs(
            expected, actual, tolerance_rules={"price": 0.1}
        )
        assert len(diffs_with_tolerance) == 0

    # =========================================================================
    # Baseline Management Tests
    # =========================================================================

    def test_set_and_get_baseline(self, service):
        """Test setting and getting a baseline."""
        data = {"test": "data", "value": 123}

        baseline_hash = service.set_baseline("test-baseline", data)
        assert baseline_hash is not None
        assert len(baseline_hash) == 64  # SHA256 hex length

        baseline = service.get_baseline("test-baseline")
        assert baseline is not None
        assert baseline["data"] == data
        assert baseline["hash"] == baseline_hash

    def test_get_nonexistent_baseline(self, service):
        """Test getting a baseline that doesn't exist."""
        baseline = service.get_baseline("nonexistent")
        assert baseline is None

    def test_clear_baseline(self, service):
        """Test clearing a baseline."""
        service.set_baseline("to-delete", {"data": "test"})
        assert service.get_baseline("to-delete") is not None

        success = service.clear_baseline("to-delete")
        assert success is True
        assert service.get_baseline("to-delete") is None

    def test_clear_nonexistent_baseline(self, service):
        """Test clearing a baseline that doesn't exist."""
        success = service.clear_baseline("nonexistent")
        assert success is False

    # =========================================================================
    # Helper Method Tests
    # =========================================================================

    def test_count_fields(self, service):
        """Test field counting in nested objects."""
        obj = {
            "a": 1,
            "b": {
                "c": 2,
                "d": 3,
            },
            "e": [1, 2, 3],
        }

        count = service._count_fields(obj)
        assert count == 4  # a, b.c, b.d, e (list counted as 1 field)

    def test_compute_hash(self, service):
        """Test hash computation."""
        data1 = {"a": 1, "b": 2}
        data2 = {"a": 1, "b": 2}
        data3 = {"a": 1, "b": 3}

        hash1 = service._compute_hash(data1)
        hash2 = service._compute_hash(data2)
        hash3 = service._compute_hash(data3)

        assert hash1 == hash2  # Same data = same hash
        assert hash1 != hash3  # Different data = different hash
        assert len(hash1) == 64  # SHA256 hex length

    # =========================================================================
    # Test Input Generation
    # =========================================================================

    def test_generate_test_inputs_from_examples(self, service):
        """Test generating test inputs from example data."""
        examples = [
            {"user_id": 1, "action": "login"},
            {"user_id": 2, "action": "logout"},
            {"user_id": 3, "action": "refresh"},
        ]

        test_inputs = service.generate_test_inputs_from_examples(examples)

        assert len(test_inputs) == 3
        assert all(isinstance(t, TestInput) for t in test_inputs)
        assert test_inputs[0].name == "Example 1"
        assert test_inputs[0].data == examples[0]
