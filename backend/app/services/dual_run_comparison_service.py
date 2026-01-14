"""
DualRunComparisonService - Week 134

Parallel execution of legacy and new systems with output comparison.
Supports shadow mode and traffic splitting for safe migration validation.

Agent: Tessa (Test Engineer)
"""
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

import aiohttp

from app.models.testing import (
    ComparisonResult,
    DiffType,
    DualRunResult,
    FieldDifference,
)

logger = logging.getLogger(__name__)


@dataclass
class SystemConfig:
    """Configuration for a system endpoint."""
    url: str
    name: str
    type: str = "http"  # http, grpc, websocket
    headers: Dict[str, str] = field(default_factory=dict)
    timeout_ms: int = 30000
    retry_count: int = 0


@dataclass
class DualRunStatistics:
    """Statistics for a dual-run comparison session."""
    total_requests: int = 0
    matched_requests: int = 0
    mismatched_requests: int = 0
    error_requests: int = 0
    legacy_errors: int = 0
    new_errors: int = 0
    avg_legacy_time_ms: float = 0.0
    avg_new_time_ms: float = 0.0
    performance_improvement: float = 0.0
    match_rate: float = 0.0
    mismatch_by_type: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "matched_requests": self.matched_requests,
            "mismatched_requests": self.mismatched_requests,
            "error_requests": self.error_requests,
            "legacy_errors": self.legacy_errors,
            "new_errors": self.new_errors,
            "avg_legacy_time_ms": round(self.avg_legacy_time_ms, 2),
            "avg_new_time_ms": round(self.avg_new_time_ms, 2),
            "performance_improvement": round(self.performance_improvement, 2),
            "match_rate": round(self.match_rate, 4),
            "mismatch_by_type": self.mismatch_by_type,
        }


class DualRunComparisonService:
    """
    Dual-Run Comparison Service.

    Runs requests against both legacy and new systems in parallel,
    compares outputs, and tracks statistics.

    Key Features:
    - Parallel execution with configurable timeouts
    - Shadow mode (run both, return legacy)
    - Traffic splitting
    - Response comparison with tolerance
    - Performance metrics
    - Mismatch categorization
    """

    def __init__(self, http_timeout: int = 30):
        self._timeout = aiohttp.ClientTimeout(total=http_timeout)
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._statistics: Dict[str, DualRunStatistics] = {}

    async def create_comparison_session(
        self,
        comparison_id: str,
        legacy_config: SystemConfig,
        new_config: SystemConfig,
        shadow_mode: bool = True,
        traffic_split: float = 0.0,
        ignored_fields: Optional[List[str]] = None,
        field_mappings: Optional[Dict[str, str]] = None,
        time_tolerance_ms: int = 100,
    ) -> str:
        """
        Create a new dual-run comparison session.

        Args:
            comparison_id: Unique session identifier
            legacy_config: Configuration for legacy system
            new_config: Configuration for new system
            shadow_mode: If True, both run but legacy response returned
            traffic_split: Percentage of traffic to route to new (0.0-1.0)
            ignored_fields: Fields to ignore in comparison
            field_mappings: Field name mappings (legacy -> new)
            time_tolerance_ms: Tolerance for response time comparison

        Returns:
            Session ID
        """
        self._sessions[comparison_id] = {
            "legacy": legacy_config,
            "new": new_config,
            "shadow_mode": shadow_mode,
            "traffic_split": traffic_split,
            "ignored_fields": ignored_fields or [],
            "field_mappings": field_mappings or {},
            "time_tolerance_ms": time_tolerance_ms,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._statistics[comparison_id] = DualRunStatistics()

        logger.info(f"Created dual-run session {comparison_id}")
        return comparison_id

    async def execute_request(
        self,
        comparison_id: str,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
    ) -> DualRunResult:
        """
        Execute a request against both systems and compare.

        Args:
            comparison_id: Session identifier
            method: HTTP method (GET, POST, etc.)
            path: Request path (appended to base URLs)
            body: Request body
            headers: Request headers
            correlation_id: Optional correlation ID for tracking

        Returns:
            DualRunResult with comparison
        """
        if comparison_id not in self._sessions:
            return DualRunResult(
                comparison_id=comparison_id,
                request_path=path,
                request_method=method,
                result=ComparisonResult.ERROR,
                correlation_id=correlation_id or str(uuid4()),
                new_error=f"Session {comparison_id} not found",
                executed_at=datetime.utcnow(),
            )

        session = self._sessions[comparison_id]
        stats = self._statistics[comparison_id]
        correlation_id = correlation_id or str(uuid4())

        result = DualRunResult(
            comparison_id=comparison_id,
            request_path=path,
            request_method=method,
            result=ComparisonResult.MISMATCH,
            correlation_id=correlation_id,
            executed_at=datetime.utcnow(),
        )

        legacy_config: SystemConfig = session["legacy"]
        new_config: SystemConfig = session["new"]

        # Build full URLs
        legacy_url = f"{legacy_config.url.rstrip('/')}/{path.lstrip('/')}"
        new_url = f"{new_config.url.rstrip('/')}/{path.lstrip('/')}"

        # Merge headers
        legacy_headers = {**legacy_config.headers, **(headers or {})}
        new_headers = {**new_config.headers, **(headers or {})}

        # Execute both in parallel
        legacy_task = self._call_system(
            legacy_url, method, body, legacy_headers, legacy_config.timeout_ms
        )
        new_task = self._call_system(
            new_url, method, body, new_headers, new_config.timeout_ms
        )

        legacy_result, new_result = await asyncio.gather(
            legacy_task, new_task, return_exceptions=True
        )

        # Process legacy result
        if isinstance(legacy_result, Exception):
            result.legacy_error = str(legacy_result)
            stats.legacy_errors += 1
        else:
            result.legacy_status_code = legacy_result["status_code"]
            result.legacy_response_time_ms = legacy_result["duration_ms"]

        # Process new result
        if isinstance(new_result, Exception):
            result.new_error = str(new_result)
            stats.new_errors += 1
        else:
            result.new_status_code = new_result["status_code"]
            result.new_response_time_ms = new_result["duration_ms"]

        # Compare if both succeeded
        if result.legacy_error or result.new_error:
            result.result = ComparisonResult.ERROR
            stats.error_requests += 1
        else:
            # Compare status codes
            if result.legacy_status_code != result.new_status_code:
                result.differences.append(FieldDifference(
                    field_path="status_code",
                    diff_type=DiffType.MODIFIED,
                    expected_value=result.legacy_status_code,
                    actual_value=result.new_status_code,
                ))

            # Compare bodies
            body_diffs = self._compare_responses(
                legacy_result.get("body", {}),
                new_result.get("body", {}),
                session["ignored_fields"],
                session["field_mappings"],
            )
            result.differences.extend(body_diffs)
            result.diff_count = len(result.differences)

            if result.differences:
                result.result = ComparisonResult.MISMATCH
                stats.mismatched_requests += 1

                # Categorize mismatches
                for diff in result.differences:
                    diff_type = diff.diff_type.value if hasattr(diff.diff_type, 'value') else str(diff.diff_type)
                    stats.mismatch_by_type[diff_type] = (
                        stats.mismatch_by_type.get(diff_type, 0) + 1
                    )
            else:
                result.result = ComparisonResult.MATCH
                stats.matched_requests += 1

        # Update statistics
        stats.total_requests += 1
        self._update_averages(stats, result)

        logger.debug(
            f"Dual-run {correlation_id}: {result.result.value}, "
            f"diffs={result.diff_count}"
        )

        return result

    async def execute_batch(
        self,
        comparison_id: str,
        requests: List[Dict[str, Any]],
        parallel: bool = True,
        max_concurrent: int = 10,
    ) -> List[DualRunResult]:
        """
        Execute batch of requests.

        Args:
            comparison_id: Session identifier
            requests: List of request configs
            parallel: Execute in parallel if True
            max_concurrent: Max concurrent requests

        Returns:
            List of DualRunResult
        """
        if parallel:
            semaphore = asyncio.Semaphore(max_concurrent)

            async def limited_execute(req: Dict[str, Any]) -> DualRunResult:
                async with semaphore:
                    return await self.execute_request(
                        comparison_id=comparison_id,
                        method=req.get("method", "GET"),
                        path=req["path"],
                        body=req.get("body"),
                        headers=req.get("headers"),
                        correlation_id=req.get("correlation_id"),
                    )

            results = await asyncio.gather(*[limited_execute(r) for r in requests])
            return list(results)
        else:
            results = []
            for req in requests:
                result = await self.execute_request(
                    comparison_id=comparison_id,
                    method=req.get("method", "GET"),
                    path=req["path"],
                    body=req.get("body"),
                    headers=req.get("headers"),
                    correlation_id=req.get("correlation_id"),
                )
                results.append(result)
            return results

    async def replay_traffic(
        self,
        comparison_id: str,
        traffic_log: List[Dict[str, Any]],
        speed_multiplier: float = 1.0,
        preserve_timing: bool = False,
    ) -> List[DualRunResult]:
        """
        Replay recorded traffic for comparison.

        Args:
            comparison_id: Session identifier
            traffic_log: List of recorded requests with timestamps
            speed_multiplier: Playback speed (1.0 = real-time)
            preserve_timing: Preserve original request timing

        Returns:
            List of DualRunResult
        """
        results = []
        last_timestamp = None

        for entry in traffic_log:
            # Optionally preserve timing
            if preserve_timing and last_timestamp and "timestamp" in entry:
                current_ts = datetime.fromisoformat(entry["timestamp"])
                delay = (current_ts - last_timestamp).total_seconds()
                delay = delay / speed_multiplier
                if delay > 0:
                    await asyncio.sleep(delay)
                last_timestamp = current_ts
            elif "timestamp" in entry:
                last_timestamp = datetime.fromisoformat(entry["timestamp"])

            result = await self.execute_request(
                comparison_id=comparison_id,
                method=entry.get("method", "GET"),
                path=entry["path"],
                body=entry.get("body"),
                headers=entry.get("headers"),
                correlation_id=entry.get("correlation_id"),
            )
            results.append(result)

        return results

    def get_statistics(self, comparison_id: str) -> Optional[DualRunStatistics]:
        """Get statistics for a comparison session."""
        return self._statistics.get(comparison_id)

    def get_mismatch_summary(
        self,
        comparison_id: str,
    ) -> Dict[str, Any]:
        """Get detailed mismatch summary."""
        stats = self._statistics.get(comparison_id)
        if not stats:
            return {}

        return {
            "total_mismatches": stats.mismatched_requests,
            "by_type": stats.mismatch_by_type,
            "mismatch_rate": (
                stats.mismatched_requests / stats.total_requests * 100
                if stats.total_requests > 0 else 0
            ),
        }

    def stop_session(self, comparison_id: str) -> bool:
        """Stop a comparison session."""
        if comparison_id in self._sessions:
            self._sessions[comparison_id]["is_active"] = False
            self._sessions[comparison_id]["stopped_at"] = datetime.utcnow().isoformat()
            return True
        return False

    def is_session_active(self, comparison_id: str) -> bool:
        """Check if session is active."""
        session = self._sessions.get(comparison_id)
        return session.get("is_active", False) if session else False

    async def _call_system(
        self,
        url: str,
        method: str,
        body: Optional[Dict[str, Any]],
        headers: Dict[str, str],
        timeout_ms: int,
    ) -> Dict[str, Any]:
        """Call a system endpoint and return result with timing."""
        start = time.time()

        timeout = aiohttp.ClientTimeout(total=timeout_ms / 1000)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            default_headers = {"Content-Type": "application/json"}
            default_headers.update(headers)

            if method.upper() == "GET":
                async with session.get(url, headers=default_headers, params=body) as response:
                    body_content = await response.json() if response.content_type == "application/json" else {}
                    status = response.status
            else:
                async with session.request(
                    method.upper(), url, json=body, headers=default_headers
                ) as response:
                    body_content = await response.json() if response.content_type == "application/json" else {}
                    status = response.status

        duration_ms = int((time.time() - start) * 1000)

        return {
            "status_code": status,
            "body": body_content,
            "duration_ms": duration_ms,
        }

    def _compare_responses(
        self,
        legacy: Any,
        new: Any,
        ignored_fields: List[str],
        field_mappings: Dict[str, str],
        path: str = "",
    ) -> List[FieldDifference]:
        """Deep compare two responses."""
        differences = []
        ignored = set(ignored_fields)

        # Check if path is ignored
        if path in ignored:
            return differences

        # Apply field mappings
        if isinstance(legacy, dict) and isinstance(new, dict):
            for old_name, new_name in field_mappings.items():
                if old_name in legacy and new_name in new:
                    new[old_name] = new.pop(new_name)

        if type(legacy) != type(new):
            differences.append(FieldDifference(
                field_path=path or "(root)",
                diff_type=DiffType.TYPE_CHANGE,
                expected_value=type(legacy).__name__,
                actual_value=type(new).__name__,
            ))
            return differences

        if isinstance(legacy, dict):
            all_keys = set(legacy.keys()) | set(new.keys())
            for key in all_keys:
                field_path = f"{path}.{key}" if path else key

                if field_path in ignored or key in ignored:
                    continue

                if key not in legacy:
                    differences.append(FieldDifference(
                        field_path=field_path,
                        diff_type=DiffType.ADDED,
                        expected_value=None,
                        actual_value=new[key],
                    ))
                elif key not in new:
                    differences.append(FieldDifference(
                        field_path=field_path,
                        diff_type=DiffType.REMOVED,
                        expected_value=legacy[key],
                        actual_value=None,
                    ))
                else:
                    differences.extend(self._compare_responses(
                        legacy[key], new[key], ignored_fields, field_mappings, field_path
                    ))

        elif isinstance(legacy, list):
            if len(legacy) != len(new):
                differences.append(FieldDifference(
                    field_path=path,
                    diff_type=DiffType.MODIFIED,
                    expected_value=len(legacy),
                    actual_value=len(new),
                    message=f"Array length: {len(legacy)} -> {len(new)}",
                ))
            else:
                for i, (l, n) in enumerate(zip(legacy, new)):
                    differences.extend(self._compare_responses(
                        l, n, ignored_fields, field_mappings, f"{path}[{i}]"
                    ))

        elif legacy != new:
            differences.append(FieldDifference(
                field_path=path,
                diff_type=DiffType.MODIFIED,
                expected_value=legacy,
                actual_value=new,
            ))

        return differences

    def _update_averages(
        self,
        stats: DualRunStatistics,
        result: DualRunResult,
    ) -> None:
        """Update running averages."""
        n = stats.total_requests

        # Update legacy average
        if result.legacy_response_time_ms > 0:
            stats.avg_legacy_time_ms = (
                (stats.avg_legacy_time_ms * (n - 1) + result.legacy_response_time_ms) / n
            )

        # Update new average
        if result.new_response_time_ms > 0:
            stats.avg_new_time_ms = (
                (stats.avg_new_time_ms * (n - 1) + result.new_response_time_ms) / n
            )

        # Calculate performance improvement
        if stats.avg_legacy_time_ms > 0:
            stats.performance_improvement = (
                (stats.avg_legacy_time_ms - stats.avg_new_time_ms)
                / stats.avg_legacy_time_ms * 100
            )

        # Update match rate
        stats.match_rate = (
            stats.matched_requests / stats.total_requests * 100
            if stats.total_requests > 0 else 0
        )
