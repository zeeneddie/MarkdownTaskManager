"""
J2: Performance Baseline Tool

Tool voor het vastleggen van performance baselines voor legacy systemen
als referentie voor migratie validatie.

Metrics:
- Response times (p50, p95, p99)
- Throughput (requests/second)
- Resource usage (CPU, memory, I/O)
- Database query times
- External service latencies
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4
import statistics
import json


class MetricType(str, Enum):
    """Types of performance metrics."""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    IO_READ = "io_read"
    IO_WRITE = "io_write"
    DB_QUERY_TIME = "db_query_time"
    EXTERNAL_LATENCY = "external_latency"


class BaselineStatus(str, Enum):
    """Status of a baseline capture."""
    CAPTURING = "capturing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


@dataclass
class MetricSample:
    """A single metric measurement."""
    timestamp: datetime
    value: float
    unit: str
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "unit": self.unit,
            "tags": self.tags
        }


@dataclass
class PercentileStats:
    """Statistical percentiles for a metric."""
    p50: float  # Median
    p75: float
    p90: float
    p95: float
    p99: float
    min: float
    max: float
    mean: float
    std_dev: float
    sample_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "p50": round(self.p50, 3),
            "p75": round(self.p75, 3),
            "p90": round(self.p90, 3),
            "p95": round(self.p95, 3),
            "p99": round(self.p99, 3),
            "min": round(self.min, 3),
            "max": round(self.max, 3),
            "mean": round(self.mean, 3),
            "std_dev": round(self.std_dev, 3),
            "sample_count": self.sample_count
        }


@dataclass
class ResponseTimeBaseline:
    """Response time baseline for an endpoint."""
    endpoint: str
    method: str
    percentiles: PercentileStats
    samples_period: str  # e.g., "24h", "7d"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "percentiles": self.percentiles.to_dict(),
            "samples_period": self.samples_period
        }


@dataclass
class ThroughputBaseline:
    """Throughput baseline."""
    requests_per_second: PercentileStats
    peak_rps: float
    sustained_rps: float  # Average over longer period
    time_to_peak: float  # Seconds to reach peak under load

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requests_per_second": self.requests_per_second.to_dict(),
            "peak_rps": round(self.peak_rps, 2),
            "sustained_rps": round(self.sustained_rps, 2),
            "time_to_peak": round(self.time_to_peak, 2)
        }


@dataclass
class ResourceUsageBaseline:
    """Resource usage baseline."""
    cpu_percent: PercentileStats
    memory_percent: PercentileStats
    memory_mb: PercentileStats
    io_read_mbps: PercentileStats
    io_write_mbps: PercentileStats

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_percent": self.cpu_percent.to_dict(),
            "memory_percent": self.memory_percent.to_dict(),
            "memory_mb": self.memory_mb.to_dict(),
            "io_read_mbps": self.io_read_mbps.to_dict(),
            "io_write_mbps": self.io_write_mbps.to_dict()
        }


@dataclass
class DatabaseQueryBaseline:
    """Database query performance baseline."""
    query_name: str
    query_pattern: str  # Normalized query pattern
    execution_time: PercentileStats
    rows_examined: PercentileStats
    rows_returned: PercentileStats

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_name": self.query_name,
            "query_pattern": self.query_pattern,
            "execution_time": self.execution_time.to_dict(),
            "rows_examined": self.rows_examined.to_dict(),
            "rows_returned": self.rows_returned.to_dict()
        }


@dataclass
class ExternalServiceBaseline:
    """External service latency baseline."""
    service_name: str
    endpoint: str
    latency: PercentileStats
    error_rate: float  # Percentage
    timeout_rate: float  # Percentage

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "endpoint": self.endpoint,
            "latency": self.latency.to_dict(),
            "error_rate": round(self.error_rate, 2),
            "timeout_rate": round(self.timeout_rate, 2)
        }


@dataclass
class PerformanceBaseline:
    """Complete performance baseline for a system."""
    id: UUID
    system_name: str
    version: str
    environment: str  # e.g., "production", "staging"
    capture_start: datetime
    capture_end: Optional[datetime]
    status: BaselineStatus

    # Baseline components
    response_times: List[ResponseTimeBaseline] = field(default_factory=list)
    throughput: Optional[ThroughputBaseline] = None
    resource_usage: Optional[ResourceUsageBaseline] = None
    database_queries: List[DatabaseQueryBaseline] = field(default_factory=list)
    external_services: List[ExternalServiceBaseline] = field(default_factory=list)

    # Metadata
    tags: Dict[str, str] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "system_name": self.system_name,
            "version": self.version,
            "environment": self.environment,
            "capture_start": self.capture_start.isoformat(),
            "capture_end": self.capture_end.isoformat() if self.capture_end else None,
            "status": self.status.value,
            "response_times": [rt.to_dict() for rt in self.response_times],
            "throughput": self.throughput.to_dict() if self.throughput else None,
            "resource_usage": self.resource_usage.to_dict() if self.resource_usage else None,
            "database_queries": [dq.to_dict() for dq in self.database_queries],
            "external_services": [es.to_dict() for es in self.external_services],
            "tags": self.tags,
            "notes": self.notes
        }


@dataclass
class BaselineComparison:
    """Comparison between two baselines."""
    baseline_id: UUID
    comparison_id: UUID
    compared_at: datetime

    response_time_diff: Dict[str, float]  # endpoint -> % change
    throughput_diff: float  # % change
    resource_diff: Dict[str, float]  # metric -> % change
    db_query_diff: Dict[str, float]  # query -> % change
    external_diff: Dict[str, float]  # service -> % change

    regressions: List[str]  # List of degraded metrics
    improvements: List[str]  # List of improved metrics
    overall_status: str  # "improved", "degraded", "stable"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_id": str(self.baseline_id),
            "comparison_id": str(self.comparison_id),
            "compared_at": self.compared_at.isoformat(),
            "response_time_diff": self.response_time_diff,
            "throughput_diff": round(self.throughput_diff, 2),
            "resource_diff": self.resource_diff,
            "db_query_diff": self.db_query_diff,
            "external_diff": self.external_diff,
            "regressions": self.regressions,
            "improvements": self.improvements,
            "overall_status": self.overall_status
        }


class PerformanceBaselineService:
    """
    Service voor het vastleggen en vergelijken van performance baselines.

    Gebruik:
    1. Start baseline capture voor legacy systeem
    2. Verzamel metrics over tijd (response times, throughput, etc.)
    3. Finaliseer baseline
    4. Na migratie: vergelijk nieuwe metrics met baseline
    """

    def __init__(self):
        self._baselines: Dict[UUID, PerformanceBaseline] = {}
        self._samples: Dict[UUID, Dict[MetricType, List[MetricSample]]] = {}
        # Threshold for regression detection (percentage)
        self._regression_threshold = 10.0  # 10% degradation = regression
        self._improvement_threshold = -10.0  # 10% improvement

    # =========================================================================
    # Baseline Management
    # =========================================================================

    def create_baseline(
        self,
        system_name: str,
        version: str,
        environment: str = "production",
        tags: Optional[Dict[str, str]] = None,
        notes: str = ""
    ) -> PerformanceBaseline:
        """Create a new baseline capture session."""
        baseline = PerformanceBaseline(
            id=uuid4(),
            system_name=system_name,
            version=version,
            environment=environment,
            capture_start=datetime.now(),
            capture_end=None,
            status=BaselineStatus.CAPTURING,
            tags=tags or {},
            notes=notes
        )
        self._baselines[baseline.id] = baseline
        self._samples[baseline.id] = {mt: [] for mt in MetricType}
        return baseline

    def get_baseline(self, baseline_id: Union[UUID, str]) -> Optional[PerformanceBaseline]:
        """Get a baseline by ID."""
        if isinstance(baseline_id, str):
            baseline_id = UUID(baseline_id)
        return self._baselines.get(baseline_id)

    def list_baselines(
        self,
        system_name: Optional[str] = None,
        environment: Optional[str] = None,
        status: Optional[BaselineStatus] = None
    ) -> List[PerformanceBaseline]:
        """List baselines with optional filters."""
        results = list(self._baselines.values())

        if system_name:
            results = [b for b in results if b.system_name == system_name]
        if environment:
            results = [b for b in results if b.environment == environment]
        if status:
            results = [b for b in results if b.status == status]

        return sorted(results, key=lambda b: b.capture_start, reverse=True)

    def finalize_baseline(self, baseline_id: Union[UUID, str]) -> PerformanceBaseline:
        """Finalize baseline capture and calculate statistics."""
        baseline = self.get_baseline(baseline_id)
        if not baseline:
            raise ValueError(f"Baseline not found: {baseline_id}")

        if baseline.status != BaselineStatus.CAPTURING:
            raise ValueError(f"Baseline is not in capturing state: {baseline.status}")

        samples = self._samples.get(baseline.id, {})

        # Calculate response time baselines
        rt_samples = samples.get(MetricType.RESPONSE_TIME, [])
        baseline.response_times = self._calculate_response_time_baselines(rt_samples)

        # Calculate throughput baseline
        tp_samples = samples.get(MetricType.THROUGHPUT, [])
        if tp_samples:
            baseline.throughput = self._calculate_throughput_baseline(tp_samples)

        # Calculate resource usage baseline
        baseline.resource_usage = self._calculate_resource_baseline(samples)

        # Calculate database query baselines
        db_samples = samples.get(MetricType.DB_QUERY_TIME, [])
        baseline.database_queries = self._calculate_db_baselines(db_samples)

        # Calculate external service baselines
        ext_samples = samples.get(MetricType.EXTERNAL_LATENCY, [])
        baseline.external_services = self._calculate_external_baselines(ext_samples)

        baseline.capture_end = datetime.now()
        baseline.status = BaselineStatus.COMPLETED

        return baseline

    # =========================================================================
    # Metric Collection
    # =========================================================================

    def record_response_time(
        self,
        baseline_id: Union[UUID, str],
        endpoint: str,
        method: str,
        duration_ms: float
    ) -> None:
        """Record a response time measurement."""
        self._add_sample(
            baseline_id,
            MetricType.RESPONSE_TIME,
            duration_ms,
            "ms",
            {"endpoint": endpoint, "method": method}
        )

    def record_throughput(
        self,
        baseline_id: Union[UUID, str],
        requests_per_second: float
    ) -> None:
        """Record throughput measurement."""
        self._add_sample(
            baseline_id,
            MetricType.THROUGHPUT,
            requests_per_second,
            "rps"
        )

    def record_cpu_usage(
        self,
        baseline_id: Union[UUID, str],
        cpu_percent: float
    ) -> None:
        """Record CPU usage."""
        self._add_sample(
            baseline_id,
            MetricType.CPU_USAGE,
            cpu_percent,
            "percent"
        )

    def record_memory_usage(
        self,
        baseline_id: Union[UUID, str],
        memory_percent: float,
        memory_mb: Optional[float] = None
    ) -> None:
        """Record memory usage."""
        tags = {}
        if memory_mb is not None:
            tags["memory_mb"] = str(memory_mb)
        self._add_sample(
            baseline_id,
            MetricType.MEMORY_USAGE,
            memory_percent,
            "percent",
            tags
        )

    def record_io(
        self,
        baseline_id: Union[UUID, str],
        read_mbps: float,
        write_mbps: float
    ) -> None:
        """Record I/O throughput."""
        self._add_sample(baseline_id, MetricType.IO_READ, read_mbps, "mbps")
        self._add_sample(baseline_id, MetricType.IO_WRITE, write_mbps, "mbps")

    def record_db_query(
        self,
        baseline_id: Union[UUID, str],
        query_name: str,
        query_pattern: str,
        execution_time_ms: float,
        rows_examined: int = 0,
        rows_returned: int = 0
    ) -> None:
        """Record database query performance."""
        self._add_sample(
            baseline_id,
            MetricType.DB_QUERY_TIME,
            execution_time_ms,
            "ms",
            {
                "query_name": query_name,
                "query_pattern": query_pattern,
                "rows_examined": str(rows_examined),
                "rows_returned": str(rows_returned)
            }
        )

    def record_external_latency(
        self,
        baseline_id: Union[UUID, str],
        service_name: str,
        endpoint: str,
        latency_ms: float,
        is_error: bool = False,
        is_timeout: bool = False
    ) -> None:
        """Record external service latency."""
        self._add_sample(
            baseline_id,
            MetricType.EXTERNAL_LATENCY,
            latency_ms,
            "ms",
            {
                "service_name": service_name,
                "endpoint": endpoint,
                "is_error": str(is_error),
                "is_timeout": str(is_timeout)
            }
        )

    def _add_sample(
        self,
        baseline_id: Union[UUID, str],
        metric_type: MetricType,
        value: float,
        unit: str,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Add a metric sample to a baseline."""
        if isinstance(baseline_id, str):
            baseline_id = UUID(baseline_id)

        if baseline_id not in self._samples:
            raise ValueError(f"Baseline not found: {baseline_id}")

        sample = MetricSample(
            timestamp=datetime.now(),
            value=value,
            unit=unit,
            tags=tags or {}
        )
        self._samples[baseline_id][metric_type].append(sample)

    # =========================================================================
    # Statistics Calculation
    # =========================================================================

    def _calculate_percentiles(self, values: List[float]) -> PercentileStats:
        """Calculate percentile statistics from values."""
        if not values:
            return PercentileStats(
                p50=0, p75=0, p90=0, p95=0, p99=0,
                min=0, max=0, mean=0, std_dev=0, sample_count=0
            )

        sorted_values = sorted(values)
        n = len(sorted_values)

        def percentile(p: float) -> float:
            idx = (n - 1) * p / 100
            lower = int(idx)
            upper = min(lower + 1, n - 1)
            weight = idx - lower
            return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight

        return PercentileStats(
            p50=percentile(50),
            p75=percentile(75),
            p90=percentile(90),
            p95=percentile(95),
            p99=percentile(99),
            min=min(values),
            max=max(values),
            mean=statistics.mean(values),
            std_dev=statistics.stdev(values) if len(values) > 1 else 0,
            sample_count=len(values)
        )

    def _calculate_response_time_baselines(
        self,
        samples: List[MetricSample]
    ) -> List[ResponseTimeBaseline]:
        """Calculate response time baselines per endpoint."""
        # Group by endpoint + method
        grouped: Dict[str, List[float]] = {}
        for sample in samples:
            key = f"{sample.tags.get('method', 'GET')}:{sample.tags.get('endpoint', '/')}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(sample.value)

        baselines = []
        for key, values in grouped.items():
            method, endpoint = key.split(":", 1)
            baselines.append(ResponseTimeBaseline(
                endpoint=endpoint,
                method=method,
                percentiles=self._calculate_percentiles(values),
                samples_period=self._calculate_period(samples)
            ))

        return baselines

    def _calculate_throughput_baseline(
        self,
        samples: List[MetricSample]
    ) -> ThroughputBaseline:
        """Calculate throughput baseline."""
        values = [s.value for s in samples]
        percentiles = self._calculate_percentiles(values)

        # Calculate sustained (average over longer window)
        sustained = percentiles.mean

        # Find time to peak (simplified - time from first sample to max)
        if samples:
            sorted_samples = sorted(samples, key=lambda s: s.timestamp)
            max_sample = max(samples, key=lambda s: s.value)
            time_to_peak = (max_sample.timestamp - sorted_samples[0].timestamp).total_seconds()
        else:
            time_to_peak = 0

        return ThroughputBaseline(
            requests_per_second=percentiles,
            peak_rps=percentiles.max,
            sustained_rps=sustained,
            time_to_peak=time_to_peak
        )

    def _calculate_resource_baseline(
        self,
        samples: Dict[MetricType, List[MetricSample]]
    ) -> Optional[ResourceUsageBaseline]:
        """Calculate resource usage baseline."""
        cpu_samples = samples.get(MetricType.CPU_USAGE, [])
        mem_samples = samples.get(MetricType.MEMORY_USAGE, [])
        io_read_samples = samples.get(MetricType.IO_READ, [])
        io_write_samples = samples.get(MetricType.IO_WRITE, [])

        if not any([cpu_samples, mem_samples, io_read_samples, io_write_samples]):
            return None

        # Extract memory MB from tags
        mem_mb_values = []
        for s in mem_samples:
            if "memory_mb" in s.tags:
                try:
                    mem_mb_values.append(float(s.tags["memory_mb"]))
                except ValueError:
                    pass

        return ResourceUsageBaseline(
            cpu_percent=self._calculate_percentiles([s.value for s in cpu_samples]),
            memory_percent=self._calculate_percentiles([s.value for s in mem_samples]),
            memory_mb=self._calculate_percentiles(mem_mb_values) if mem_mb_values else self._calculate_percentiles([]),
            io_read_mbps=self._calculate_percentiles([s.value for s in io_read_samples]),
            io_write_mbps=self._calculate_percentiles([s.value for s in io_write_samples])
        )

    def _calculate_db_baselines(
        self,
        samples: List[MetricSample]
    ) -> List[DatabaseQueryBaseline]:
        """Calculate database query baselines."""
        # Group by query name
        grouped: Dict[str, Dict[str, List]] = {}
        for sample in samples:
            query_name = sample.tags.get("query_name", "unknown")
            if query_name not in grouped:
                grouped[query_name] = {
                    "pattern": sample.tags.get("query_pattern", ""),
                    "times": [],
                    "examined": [],
                    "returned": []
                }
            grouped[query_name]["times"].append(sample.value)
            try:
                grouped[query_name]["examined"].append(int(sample.tags.get("rows_examined", 0)))
                grouped[query_name]["returned"].append(int(sample.tags.get("rows_returned", 0)))
            except ValueError:
                pass

        baselines = []
        for query_name, data in grouped.items():
            baselines.append(DatabaseQueryBaseline(
                query_name=query_name,
                query_pattern=data["pattern"],
                execution_time=self._calculate_percentiles(data["times"]),
                rows_examined=self._calculate_percentiles([float(x) for x in data["examined"]]),
                rows_returned=self._calculate_percentiles([float(x) for x in data["returned"]])
            ))

        return baselines

    def _calculate_external_baselines(
        self,
        samples: List[MetricSample]
    ) -> List[ExternalServiceBaseline]:
        """Calculate external service baselines."""
        # Group by service name
        grouped: Dict[str, Dict[str, Any]] = {}
        for sample in samples:
            service = sample.tags.get("service_name", "unknown")
            if service not in grouped:
                grouped[service] = {
                    "endpoint": sample.tags.get("endpoint", ""),
                    "latencies": [],
                    "errors": 0,
                    "timeouts": 0,
                    "total": 0
                }
            grouped[service]["latencies"].append(sample.value)
            grouped[service]["total"] += 1
            if sample.tags.get("is_error") == "True":
                grouped[service]["errors"] += 1
            if sample.tags.get("is_timeout") == "True":
                grouped[service]["timeouts"] += 1

        baselines = []
        for service, data in grouped.items():
            total = data["total"]
            baselines.append(ExternalServiceBaseline(
                service_name=service,
                endpoint=data["endpoint"],
                latency=self._calculate_percentiles(data["latencies"]),
                error_rate=(data["errors"] / total * 100) if total > 0 else 0,
                timeout_rate=(data["timeouts"] / total * 100) if total > 0 else 0
            ))

        return baselines

    def _calculate_period(self, samples: List[MetricSample]) -> str:
        """Calculate the time period covered by samples."""
        if not samples:
            return "0h"

        timestamps = [s.timestamp for s in samples]
        duration = max(timestamps) - min(timestamps)

        hours = duration.total_seconds() / 3600
        if hours < 24:
            return f"{int(hours)}h"
        else:
            return f"{int(hours / 24)}d"

    # =========================================================================
    # Baseline Comparison
    # =========================================================================

    def compare_baselines(
        self,
        baseline_id: Union[UUID, str],
        comparison_id: Union[UUID, str]
    ) -> BaselineComparison:
        """Compare two baselines and identify regressions/improvements."""
        baseline = self.get_baseline(baseline_id)
        comparison = self.get_baseline(comparison_id)

        if not baseline or not comparison:
            raise ValueError("One or both baselines not found")

        if baseline.status != BaselineStatus.COMPLETED or comparison.status != BaselineStatus.COMPLETED:
            raise ValueError("Both baselines must be completed")

        response_time_diff = {}
        throughput_diff = 0.0
        resource_diff = {}
        db_query_diff = {}
        external_diff = {}
        regressions = []
        improvements = []

        # Compare response times
        baseline_rt = {f"{rt.method}:{rt.endpoint}": rt for rt in baseline.response_times}
        for rt in comparison.response_times:
            key = f"{rt.method}:{rt.endpoint}"
            if key in baseline_rt:
                diff = self._calc_percent_change(
                    baseline_rt[key].percentiles.p95,
                    rt.percentiles.p95
                )
                response_time_diff[key] = diff
                if diff > self._regression_threshold:
                    regressions.append(f"Response time {key}: +{diff:.1f}%")
                elif diff < self._improvement_threshold:
                    improvements.append(f"Response time {key}: {diff:.1f}%")

        # Compare throughput
        if baseline.throughput and comparison.throughput:
            throughput_diff = self._calc_percent_change(
                baseline.throughput.sustained_rps,
                comparison.throughput.sustained_rps
            )
            # For throughput, higher is better, so invert the logic
            if throughput_diff < self._improvement_threshold:
                regressions.append(f"Throughput: {throughput_diff:.1f}%")
            elif throughput_diff > self._regression_threshold:
                improvements.append(f"Throughput: +{throughput_diff:.1f}%")

        # Compare resource usage
        if baseline.resource_usage and comparison.resource_usage:
            cpu_diff = self._calc_percent_change(
                baseline.resource_usage.cpu_percent.p95,
                comparison.resource_usage.cpu_percent.p95
            )
            mem_diff = self._calc_percent_change(
                baseline.resource_usage.memory_percent.p95,
                comparison.resource_usage.memory_percent.p95
            )
            resource_diff["cpu"] = cpu_diff
            resource_diff["memory"] = mem_diff

            if cpu_diff > self._regression_threshold:
                regressions.append(f"CPU usage: +{cpu_diff:.1f}%")
            if mem_diff > self._regression_threshold:
                regressions.append(f"Memory usage: +{mem_diff:.1f}%")

        # Compare database queries
        baseline_db = {dq.query_name: dq for dq in baseline.database_queries}
        for dq in comparison.database_queries:
            if dq.query_name in baseline_db:
                diff = self._calc_percent_change(
                    baseline_db[dq.query_name].execution_time.p95,
                    dq.execution_time.p95
                )
                db_query_diff[dq.query_name] = diff
                if diff > self._regression_threshold:
                    regressions.append(f"DB query {dq.query_name}: +{diff:.1f}%")

        # Compare external services
        baseline_ext = {es.service_name: es for es in baseline.external_services}
        for es in comparison.external_services:
            if es.service_name in baseline_ext:
                diff = self._calc_percent_change(
                    baseline_ext[es.service_name].latency.p95,
                    es.latency.p95
                )
                external_diff[es.service_name] = diff
                if diff > self._regression_threshold:
                    regressions.append(f"External {es.service_name}: +{diff:.1f}%")

        # Determine overall status
        if len(regressions) > len(improvements):
            overall_status = "degraded"
        elif len(improvements) > len(regressions):
            overall_status = "improved"
        else:
            overall_status = "stable"

        return BaselineComparison(
            baseline_id=baseline.id,
            comparison_id=comparison.id,
            compared_at=datetime.now(),
            response_time_diff=response_time_diff,
            throughput_diff=throughput_diff,
            resource_diff=resource_diff,
            db_query_diff=db_query_diff,
            external_diff=external_diff,
            regressions=regressions,
            improvements=improvements,
            overall_status=overall_status
        )

    def _calc_percent_change(self, baseline: float, current: float) -> float:
        """Calculate percentage change from baseline to current."""
        if baseline == 0:
            return 0 if current == 0 else 100
        return ((current - baseline) / baseline) * 100

    # =========================================================================
    # Export
    # =========================================================================

    def export_baseline(
        self,
        baseline_id: Union[UUID, str],
        format: str = "json"
    ) -> str:
        """Export baseline to JSON or markdown format."""
        baseline = self.get_baseline(baseline_id)
        if not baseline:
            raise ValueError(f"Baseline not found: {baseline_id}")

        if format == "json":
            return json.dumps(baseline.to_dict(), indent=2)
        elif format == "markdown":
            return self._export_markdown(baseline)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_markdown(self, baseline: PerformanceBaseline) -> str:
        """Export baseline as markdown report."""
        lines = [
            f"# Performance Baseline: {baseline.system_name}",
            f"",
            f"**Version**: {baseline.version}",
            f"**Environment**: {baseline.environment}",
            f"**Captured**: {baseline.capture_start.strftime('%Y-%m-%d %H:%M')} - {baseline.capture_end.strftime('%Y-%m-%d %H:%M') if baseline.capture_end else 'In Progress'}",
            f"**Status**: {baseline.status.value}",
            f"",
            "## Response Times",
            "",
            "| Endpoint | Method | p50 | p95 | p99 | Samples |",
            "|----------|--------|-----|-----|-----|---------|"
        ]

        for rt in baseline.response_times:
            lines.append(
                f"| {rt.endpoint} | {rt.method} | "
                f"{rt.percentiles.p50:.1f}ms | {rt.percentiles.p95:.1f}ms | "
                f"{rt.percentiles.p99:.1f}ms | {rt.percentiles.sample_count} |"
            )

        if baseline.throughput:
            lines.extend([
                "",
                "## Throughput",
                "",
                f"- **Peak RPS**: {baseline.throughput.peak_rps:.1f}",
                f"- **Sustained RPS**: {baseline.throughput.sustained_rps:.1f}",
                f"- **p95 RPS**: {baseline.throughput.requests_per_second.p95:.1f}",
            ])

        if baseline.resource_usage:
            lines.extend([
                "",
                "## Resource Usage",
                "",
                f"- **CPU (p95)**: {baseline.resource_usage.cpu_percent.p95:.1f}%",
                f"- **Memory (p95)**: {baseline.resource_usage.memory_percent.p95:.1f}%",
            ])

        if baseline.database_queries:
            lines.extend([
                "",
                "## Database Queries",
                "",
                "| Query | p50 | p95 | p99 |",
                "|-------|-----|-----|-----|"
            ])
            for dq in baseline.database_queries:
                lines.append(
                    f"| {dq.query_name} | {dq.execution_time.p50:.1f}ms | "
                    f"{dq.execution_time.p95:.1f}ms | {dq.execution_time.p99:.1f}ms |"
                )

        if baseline.external_services:
            lines.extend([
                "",
                "## External Services",
                "",
                "| Service | p95 Latency | Error Rate | Timeout Rate |",
                "|---------|-------------|------------|--------------|"
            ])
            for es in baseline.external_services:
                lines.append(
                    f"| {es.service_name} | {es.latency.p95:.1f}ms | "
                    f"{es.error_rate:.1f}% | {es.timeout_rate:.1f}% |"
                )

        return "\n".join(lines)
