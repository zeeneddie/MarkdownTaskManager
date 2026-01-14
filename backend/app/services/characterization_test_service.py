"""
CharacterizationTestService - Week 134

Golden Master pattern implementation for recording legacy system behavior
and comparing against new system output.

Agent: Tessa (Test Engineer)
"""
import hashlib
import json
import logging
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import aiohttp

from app.models.testing import (
    CharacterizationTestResult,
    ComparisonResult,
    DiffType,
    FieldDifference,
    OutputFormat,
    TestInput,
    TestStatus,
)

logger = logging.getLogger(__name__)


class CharacterizationTestService:
    """
    Golden Master / Characterization Test Service.

    Records legacy system behavior as "golden master" baseline,
    then compares new system output against this baseline.

    Key Features:
    - Record legacy I/O as baseline
    - Compare new system output
    - Field-level diff detection
    - Configurable tolerance rules
    - Ignored fields support
    """

    def __init__(self, http_timeout: int = 30):
        self._timeout = aiohttp.ClientTimeout(total=http_timeout)
        self._baselines: Dict[str, Dict[str, Any]] = {}

    async def record_baseline(
        self,
        test_id: str,
        test_name: str,
        legacy_endpoint: str,
        input_data: Dict[str, Any],
        input_scenario: Optional[str] = None,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
    ) -> CharacterizationTestResult:
        """
        Record legacy system output as baseline (Golden Master).

        Args:
            test_id: Unique test identifier
            test_name: Human-readable test name
            legacy_endpoint: URL of legacy system endpoint
            input_data: Input data to send
            input_scenario: Name of the input scenario
            method: HTTP method (GET, POST, etc.)
            headers: Optional HTTP headers

        Returns:
            CharacterizationTestResult with baseline data
        """
        start_time = time.time()

        result = CharacterizationTestResult(
            test_id=test_id,
            test_name=test_name,
            result=ComparisonResult.NEW_BASELINE,
            input_scenario=input_scenario,
            executed_at=datetime.utcnow(),
        )

        try:
            # Call legacy system
            legacy_output, legacy_duration = await self._call_endpoint(
                legacy_endpoint, method, input_data, headers
            )

            result.legacy_output = legacy_output
            result.legacy_duration_ms = legacy_duration

            # Store as baseline
            baseline_hash = self._compute_hash(legacy_output)
            self._baselines[test_id] = {
                "data": legacy_output,
                "hash": baseline_hash,
                "recorded_at": datetime.utcnow().isoformat(),
                "input_scenario": input_scenario,
            }

            result.match_percentage = 100.0

            logger.info(
                f"Baseline recorded for test {test_id}: hash={baseline_hash[:16]}..."
            )

        except Exception as e:
            result.result = ComparisonResult.ERROR
            result.error = str(e)
            logger.error(f"Failed to record baseline for {test_id}: {e}")

        return result

    async def compare_with_baseline(
        self,
        test_id: str,
        test_name: str,
        new_endpoint: str,
        input_data: Dict[str, Any],
        input_scenario: Optional[str] = None,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        ignored_fields: Optional[List[str]] = None,
        tolerance_rules: Optional[Dict[str, Any]] = None,
        baseline_data: Optional[Dict[str, Any]] = None,
    ) -> CharacterizationTestResult:
        """
        Compare new system output against recorded baseline.

        Args:
            test_id: Unique test identifier
            test_name: Human-readable test name
            new_endpoint: URL of new system endpoint
            input_data: Input data to send
            input_scenario: Name of the input scenario
            method: HTTP method
            headers: Optional HTTP headers
            ignored_fields: List of field paths to ignore (e.g., ["timestamp", "id"])
            tolerance_rules: Tolerance for numeric comparisons
            baseline_data: Override stored baseline with provided data

        Returns:
            CharacterizationTestResult with comparison details
        """
        start_time = time.time()

        result = CharacterizationTestResult(
            test_id=test_id,
            test_name=test_name,
            result=ComparisonResult.MISMATCH,
            input_scenario=input_scenario,
            executed_at=datetime.utcnow(),
        )

        # Get baseline
        if baseline_data:
            baseline = baseline_data
        elif test_id in self._baselines:
            baseline = self._baselines[test_id]["data"]
        else:
            result.result = ComparisonResult.ERROR
            result.error = f"No baseline found for test {test_id}"
            return result

        result.legacy_output = baseline

        try:
            # Call new system
            new_output, new_duration = await self._call_endpoint(
                new_endpoint, method, input_data, headers
            )

            result.new_output = new_output
            result.new_duration_ms = new_duration

            # Compare outputs
            differences = self._compare_outputs(
                baseline, new_output, ignored_fields, tolerance_rules
            )

            result.differences = differences
            result.diff_count = len(differences)

            if differences:
                result.result = ComparisonResult.MISMATCH
                total_fields = self._count_fields(baseline)
                result.match_percentage = (
                    (total_fields - len(differences)) / total_fields * 100
                    if total_fields > 0 else 0.0
                )
            else:
                result.result = ComparisonResult.MATCH
                result.match_percentage = 100.0

            logger.info(
                f"Comparison for {test_id}: {result.result.value}, "
                f"match={result.match_percentage:.1f}%, diffs={result.diff_count}"
            )

        except Exception as e:
            result.result = ComparisonResult.ERROR
            result.error = str(e)
            logger.error(f"Comparison failed for {test_id}: {e}")

        return result

    async def run_full_test(
        self,
        test_id: str,
        test_name: str,
        legacy_endpoint: str,
        new_endpoint: str,
        input_data: Dict[str, Any],
        input_scenario: Optional[str] = None,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        ignored_fields: Optional[List[str]] = None,
        tolerance_rules: Optional[Dict[str, Any]] = None,
    ) -> CharacterizationTestResult:
        """
        Run full characterization test: call both systems and compare.

        This calls both legacy and new systems in parallel, compares outputs,
        and returns detailed difference information.

        Args:
            test_id: Unique test identifier
            test_name: Human-readable test name
            legacy_endpoint: URL of legacy system
            new_endpoint: URL of new system
            input_data: Input data to send
            input_scenario: Name of the input scenario
            method: HTTP method
            headers: Optional HTTP headers
            ignored_fields: Fields to ignore
            tolerance_rules: Numeric tolerances

        Returns:
            CharacterizationTestResult with full comparison
        """
        result = CharacterizationTestResult(
            test_id=test_id,
            test_name=test_name,
            result=ComparisonResult.MISMATCH,
            input_scenario=input_scenario,
            executed_at=datetime.utcnow(),
        )

        try:
            # Call both systems
            legacy_output, legacy_duration = await self._call_endpoint(
                legacy_endpoint, method, input_data, headers
            )
            new_output, new_duration = await self._call_endpoint(
                new_endpoint, method, input_data, headers
            )

            result.legacy_output = legacy_output
            result.legacy_duration_ms = legacy_duration
            result.new_output = new_output
            result.new_duration_ms = new_duration

            # Compare
            differences = self._compare_outputs(
                legacy_output, new_output, ignored_fields, tolerance_rules
            )

            result.differences = differences
            result.diff_count = len(differences)

            if differences:
                result.result = ComparisonResult.MISMATCH
                total_fields = self._count_fields(legacy_output)
                result.match_percentage = (
                    (total_fields - len(differences)) / total_fields * 100
                    if total_fields > 0 else 0.0
                )
            else:
                result.result = ComparisonResult.MATCH
                result.match_percentage = 100.0

        except Exception as e:
            result.result = ComparisonResult.ERROR
            result.error = str(e)
            logger.error(f"Full test failed for {test_id}: {e}")

        return result

    async def run_batch_tests(
        self,
        test_id: str,
        test_name: str,
        legacy_endpoint: str,
        new_endpoint: str,
        test_inputs: List[TestInput],
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        ignored_fields: Optional[List[str]] = None,
        tolerance_rules: Optional[Dict[str, Any]] = None,
    ) -> List[CharacterizationTestResult]:
        """
        Run batch of characterization tests with multiple inputs.

        Args:
            test_id: Base test identifier
            test_name: Base test name
            legacy_endpoint: Legacy system URL
            new_endpoint: New system URL
            test_inputs: List of test input scenarios
            method: HTTP method
            headers: Optional headers
            ignored_fields: Fields to ignore
            tolerance_rules: Numeric tolerances

        Returns:
            List of CharacterizationTestResult for each input
        """
        results = []

        for i, test_input in enumerate(test_inputs):
            scenario_id = f"{test_id}_scenario_{i}"
            scenario_name = f"{test_name} - {test_input.name}"

            result = await self.run_full_test(
                test_id=scenario_id,
                test_name=scenario_name,
                legacy_endpoint=legacy_endpoint,
                new_endpoint=new_endpoint,
                input_data=test_input.data,
                input_scenario=test_input.name,
                method=method,
                headers=headers,
                ignored_fields=ignored_fields,
                tolerance_rules=tolerance_rules,
            )
            results.append(result)

        return results

    def generate_test_inputs_from_examples(
        self,
        examples: List[Dict[str, Any]],
    ) -> List[TestInput]:
        """
        Generate test inputs from example data.

        Useful for generating characterization tests from recorded
        production data or log files.

        Args:
            examples: List of example input data

        Returns:
            List of TestInput objects
        """
        test_inputs = []

        for i, example in enumerate(examples):
            test_inputs.append(
                TestInput(
                    name=f"Example {i + 1}",
                    data=example,
                    description=f"Auto-generated from example data",
                )
            )

        return test_inputs

    async def _call_endpoint(
        self,
        url: str,
        method: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> tuple[Dict[str, Any], int]:
        """Call an HTTP endpoint and return response with timing."""
        start = time.time()

        default_headers = {"Content-Type": "application/json"}
        if headers:
            default_headers.update(headers)

        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            if method.upper() == "GET":
                async with session.get(url, headers=default_headers, params=data) as response:
                    result = await response.json()
            else:
                async with session.request(
                    method.upper(), url, json=data, headers=default_headers
                ) as response:
                    result = await response.json()

        duration_ms = int((time.time() - start) * 1000)
        return result, duration_ms

    def _compare_outputs(
        self,
        expected: Any,
        actual: Any,
        ignored_fields: Optional[List[str]] = None,
        tolerance_rules: Optional[Dict[str, Any]] = None,
        path: str = "",
    ) -> List[FieldDifference]:
        """
        Deep compare two outputs and return list of differences.

        Supports:
        - Nested object comparison
        - Array comparison (with order sensitivity)
        - Numeric tolerance
        - Field path ignoring
        """
        differences = []
        ignored = set(ignored_fields or [])
        tolerances = tolerance_rules or {}

        if path in ignored:
            return differences

        if type(expected) != type(actual):
            differences.append(FieldDifference(
                field_path=path or "(root)",
                diff_type=DiffType.TYPE_CHANGE,
                expected_value=type(expected).__name__,
                actual_value=type(actual).__name__,
                message=f"Type mismatch: expected {type(expected).__name__}, got {type(actual).__name__}",
            ))
            return differences

        if isinstance(expected, dict):
            all_keys = set(expected.keys()) | set(actual.keys())
            for key in all_keys:
                field_path = f"{path}.{key}" if path else key

                if field_path in ignored or key in ignored:
                    continue

                if key not in expected:
                    differences.append(FieldDifference(
                        field_path=field_path,
                        diff_type=DiffType.ADDED,
                        expected_value=None,
                        actual_value=actual[key],
                        message=f"Field added in new output",
                    ))
                elif key not in actual:
                    differences.append(FieldDifference(
                        field_path=field_path,
                        diff_type=DiffType.REMOVED,
                        expected_value=expected[key],
                        actual_value=None,
                        message=f"Field removed in new output",
                    ))
                else:
                    differences.extend(self._compare_outputs(
                        expected[key], actual[key], ignored_fields, tolerance_rules, field_path
                    ))

        elif isinstance(expected, list):
            if len(expected) != len(actual):
                differences.append(FieldDifference(
                    field_path=path,
                    diff_type=DiffType.MODIFIED,
                    expected_value=len(expected),
                    actual_value=len(actual),
                    message=f"Array length changed: {len(expected)} -> {len(actual)}",
                ))
            else:
                for i, (exp_item, act_item) in enumerate(zip(expected, actual)):
                    item_path = f"{path}[{i}]"
                    differences.extend(self._compare_outputs(
                        exp_item, act_item, ignored_fields, tolerance_rules, item_path
                    ))

        elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            # Check numeric tolerance
            tolerance = tolerances.get(path, tolerances.get("_default", 0))
            if abs(expected - actual) > tolerance:
                differences.append(FieldDifference(
                    field_path=path,
                    diff_type=DiffType.MODIFIED,
                    expected_value=expected,
                    actual_value=actual,
                    message=f"Numeric value changed (tolerance: {tolerance})",
                ))
        elif expected != actual:
            differences.append(FieldDifference(
                field_path=path,
                diff_type=DiffType.MODIFIED,
                expected_value=expected,
                actual_value=actual,
            ))

        return differences

    def _count_fields(self, obj: Any, count: int = 0) -> int:
        """Count total number of fields in an object."""
        if isinstance(obj, dict):
            count += len(obj)
            for value in obj.values():
                count = self._count_fields(value, count)
        elif isinstance(obj, list):
            for item in obj:
                count = self._count_fields(item, count)
        return count

    def _compute_hash(self, data: Any) -> str:
        """Compute SHA256 hash of JSON data."""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def get_baseline(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get stored baseline for a test."""
        return self._baselines.get(test_id)

    def set_baseline(self, test_id: str, baseline_data: Dict[str, Any]) -> str:
        """Manually set baseline for a test."""
        baseline_hash = self._compute_hash(baseline_data)
        self._baselines[test_id] = {
            "data": baseline_data,
            "hash": baseline_hash,
            "recorded_at": datetime.utcnow().isoformat(),
        }
        return baseline_hash

    def clear_baseline(self, test_id: str) -> bool:
        """Clear stored baseline for a test."""
        if test_id in self._baselines:
            del self._baselines[test_id]
            return True
        return False
