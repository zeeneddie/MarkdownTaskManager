"""
Unit tests for PerformanceBaselineService - J2 (Fase 24).

Tests cover:
- Baseline capture and storage
- Percentile calculations (p50, p75, p90, p95, p99)
- Baseline comparison and regression detection
- Resource usage metrics
- Database query baselines
- External service latencies

Author: Claude Code (Week 158)
Date: 2026-01-19
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.services.performance_baseline_service import (
    MetricType,
    BaselineStatus,
    PercentileStats,
    ResponseTimeBaseline,
    ThroughputBaseline,
    ResourceUsageBaseline,
    DatabaseQueryBaseline,
    ExternalServiceBaseline,
    MetricSample,
    PerformanceBaseline,
    BaselineComparison,
    PerformanceBaselineService,
)


# ==================== Fixtures ====================

@pytest.fixture
def service():
    """Create a fresh PerformanceBaselineService instance."""
    return PerformanceBaselineService()


@pytest.fixture
def sample_response_times():
    """Sample response time data."""
    return [10, 15, 20, 25, 30, 35, 40, 50, 100, 200]  # ms


@pytest.fixture
def percentile_stats():
    """Sample percentile statistics."""
    return PercentileStats(
        p50=25.0,
        p75=40.0,
        p90=100.0,
        p95=150.0,
        p99=200.0,
        mean=52.5,
        min=10.0,
        max=200.0,
        std_dev=58.0
    )


@pytest.fixture
def response_time_baseline(percentile_stats):
    """Sample response time baseline."""
    return ResponseTimeBaseline(
        endpoint="/api/users",
        method="GET",
        percentiles=percentile_stats,
        sample_count=100
    )


# ==================== PercentileStats Tests ====================

class TestPercentileStats:
    """Test PercentileStats data class."""

    def test_create_percentile_stats(self, percentile_stats):
        """Test creating percentile stats."""
        assert percentile_stats.p50 == 25.0
        assert percentile_stats.p99 == 200.0

    def test_to_dict(self, percentile_stats):
        """Test serialization."""
        data = percentile_stats.to_dict()

        assert data["p50"] == 25.0
        assert data["p95"] == 150.0
        assert "mean" in data
        assert "std_dev" in data


# ==================== Baseline Data Classes Tests ====================

class TestResponseTimeBaseline:
    """Test ResponseTimeBaseline data class."""

    def test_create_baseline(self, response_time_baseline):
        """Test creating response time baseline."""
        assert response_time_baseline.endpoint == "/api/users"
        assert response_time_baseline.method == "GET"

    def test_to_dict(self, response_time_baseline):
        """Test serialization."""
        data = response_time_baseline.to_dict()

        assert data["endpoint"] == "/api/users"
        assert "percentiles" in data


class TestThroughputBaseline:
    """Test ThroughputBaseline data class."""

    def test_create_throughput_baseline(self):
        """Test creating throughput baseline."""
        baseline = ThroughputBaseline(
            requests_per_second=100.0,
            peak_rps=150.0,
            sustained_rps=90.0,
            time_to_peak=5.0
        )
        assert baseline.requests_per_second == 100.0
        assert baseline.peak_rps == 150.0

    def test_to_dict(self):
        """Test serialization."""
        baseline = ThroughputBaseline(
            requests_per_second=100.0,
            peak_rps=150.0,
            sustained_rps=90.0,
            time_to_peak=5.0
        )
        data = baseline.to_dict()

        assert data["requests_per_second"] == 100.0
        assert "peak_rps" in data


class TestResourceUsageBaseline:
    """Test ResourceUsageBaseline data class."""

    def test_create_resource_baseline(self):
        """Test creating resource usage baseline."""
        baseline = ResourceUsageBaseline(
            cpu_percent=45.0,
            memory_mb=512.0,
            memory_percent=25.0,
            io_read_mbps=10.0,
            io_write_mbps=5.0
        )
        assert baseline.cpu_percent == 45.0
        assert baseline.memory_mb == 512.0

    def test_to_dict(self):
        """Test serialization."""
        baseline = ResourceUsageBaseline(
            cpu_percent=45.0,
            memory_mb=512.0,
            memory_percent=25.0,
            io_read_mbps=10.0,
            io_write_mbps=5.0
        )
        data = baseline.to_dict()

        assert data["cpu_percent"] == 45.0


class TestDatabaseQueryBaseline:
    """Test DatabaseQueryBaseline data class."""

    def test_create_db_baseline(self):
        """Test creating database query baseline."""
        baseline = DatabaseQueryBaseline(
            query_name="get_users",
            query_pattern="SELECT * FROM users WHERE active = ?",
            execution_time=PercentileStats(
                p50=5.0, p75=8.0, p90=15.0, p95=25.0, p99=50.0,
                mean=10.0, min=2.0, max=50.0, std_dev=8.0
            ),
            rows_returned=100,
            rows_examined=150
        )
        assert baseline.query_name == "get_users"
        assert baseline.rows_returned == 100


class TestExternalServiceBaseline:
    """Test ExternalServiceBaseline data class."""

    def test_create_external_baseline(self):
        """Test creating external service baseline."""
        baseline = ExternalServiceBaseline(
            service_name="payment-gateway",
            latency=PercentileStats(
                p50=100.0, p75=150.0, p90=200.0, p95=250.0, p99=500.0,
                mean=120.0, min=50.0, max=500.0, std_dev=80.0
            ),
            error_rate=0.01,
            timeout_rate=0.001
        )
        assert baseline.service_name == "payment-gateway"
        assert baseline.error_rate == 0.01


# ==================== PerformanceBaseline Tests ====================

class TestPerformanceBaseline:
    """Test PerformanceBaseline container class."""

    def test_create_baseline(self, response_time_baseline):
        """Test creating performance baseline."""
        baseline = PerformanceBaseline(
            id=uuid4(),
            system_name="test-system",
            environment="production",
            version="1.0.0",
            response_times=[response_time_baseline],
            throughput=ThroughputBaseline(100.0, 150.0, 90.0, 5.0),
            resource_usage=ResourceUsageBaseline(45.0, 512.0, 25.0, 10.0, 5.0),
            database_queries=[],
            external_services=[],
            capture_start=datetime.now(timezone.utc),
            capture_end=datetime.now(timezone.utc)
        )

        assert baseline.system_name == "test-system"
        assert len(baseline.response_times) == 1

    def test_to_dict(self, response_time_baseline):
        """Test serialization."""
        baseline = PerformanceBaseline(
            id=uuid4(),
            system_name="test-system",
            environment="production",
            version="1.0.0",
            response_times=[response_time_baseline],
            throughput=ThroughputBaseline(100.0, 150.0, 90.0, 5.0),
            resource_usage=ResourceUsageBaseline(45.0, 512.0, 25.0, 10.0, 5.0),
            database_queries=[],
            external_services=[],
            capture_start=datetime.now(timezone.utc),
            capture_end=datetime.now(timezone.utc)
        )

        data = baseline.to_dict()

        assert data["system_name"] == "test-system"
        assert "response_times" in data
        assert "throughput" in data


# ==================== BaselineComparison Tests ====================

class TestBaselineComparison:
    """Test BaselineComparison data class."""

    def test_create_comparison_pass(self):
        """Test creating passing comparison."""
        comparison = BaselineComparison(
            baseline_id=uuid4(),
            comparison_id=uuid4(),
            overall_status=BaselineStatus.PASS,
            response_time_diff={},
            throughput_diff={},
            resource_diff={},
            db_query_diff={},
            external_diff={},
            regressions=[],
            improvements=[]
        )

        assert comparison.overall_status == BaselineStatus.PASS
        assert len(comparison.regressions) == 0

    def test_create_comparison_with_regressions(self):
        """Test creating comparison with regressions."""
        comparison = BaselineComparison(
            baseline_id=uuid4(),
            comparison_id=uuid4(),
            overall_status=BaselineStatus.REGRESSION,
            response_time_diff={"p95": 50.0},  # 50% slower
            throughput_diff={},
            resource_diff={},
            db_query_diff={},
            external_diff={},
            regressions=["Response time p95 increased by 50%"],
            improvements=[]
        )

        assert comparison.overall_status == BaselineStatus.REGRESSION
        assert len(comparison.regressions) == 1


# ==================== PerformanceBaselineService Tests ====================

class TestPerformanceBaselineService:
    """Test PerformanceBaselineService."""

    def test_initialization(self, service):
        """Test service initialization."""
        assert service is not None
        assert service._baselines == {}

    def test_calculate_percentiles(self, service, sample_response_times):
        """Test percentile calculation."""
        stats = service.calculate_percentiles(sample_response_times)

        assert stats.p50 <= stats.p75 <= stats.p90 <= stats.p95 <= stats.p99
        assert stats.min == 10
        assert stats.max == 200

    def test_calculate_percentiles_single_value(self, service):
        """Test percentiles with single value."""
        stats = service.calculate_percentiles([100])

        assert stats.p50 == 100
        assert stats.p99 == 100
        assert stats.mean == 100

    def test_calculate_percentiles_empty(self, service):
        """Test percentiles with empty list."""
        stats = service.calculate_percentiles([])

        assert stats.p50 == 0
        assert stats.mean == 0

    def test_capture_baseline(self, service):
        """Test baseline capture."""
        samples = [
            MetricSample(MetricType.RESPONSE_TIME, 100.0, {"endpoint": "/api/users"}),
            MetricSample(MetricType.RESPONSE_TIME, 150.0, {"endpoint": "/api/users"}),
            MetricSample(MetricType.THROUGHPUT, 500.0, {}),
            MetricSample(MetricType.CPU_USAGE, 45.0, {}),
            MetricSample(MetricType.MEMORY_USAGE, 512.0, {}),
        ]

        baseline = service.capture_baseline(
            system_name="test-system",
            environment="test",
            version="1.0.0",
            samples=samples
        )

        assert baseline is not None
        assert baseline.system_name == "test-system"

    def test_store_baseline(self, service, response_time_baseline):
        """Test baseline storage."""
        baseline = PerformanceBaseline(
            id=uuid4(),
            system_name="test",
            environment="prod",
            version="1.0",
            response_times=[response_time_baseline],
            throughput=ThroughputBaseline(100.0, 150.0, 90.0, 5.0),
            resource_usage=ResourceUsageBaseline(45.0, 512.0, 25.0, 10.0, 5.0),
            database_queries=[],
            external_services=[],
            capture_start=datetime.now(timezone.utc),
            capture_end=datetime.now(timezone.utc)
        )

        service.store_baseline(baseline)

        assert baseline.id in service._baselines

    def test_get_baseline(self, service, response_time_baseline):
        """Test baseline retrieval."""
        baseline = PerformanceBaseline(
            id=uuid4(),
            system_name="test",
            environment="prod",
            version="1.0",
            response_times=[response_time_baseline],
            throughput=ThroughputBaseline(100.0, 150.0, 90.0, 5.0),
            resource_usage=ResourceUsageBaseline(45.0, 512.0, 25.0, 10.0, 5.0),
            database_queries=[],
            external_services=[],
            capture_start=datetime.now(timezone.utc),
            capture_end=datetime.now(timezone.utc)
        )

        service.store_baseline(baseline)
        retrieved = service.get_baseline(baseline.id)

        assert retrieved is not None
        assert retrieved.id == baseline.id

    def test_get_baseline_not_found(self, service):
        """Test getting nonexistent baseline."""
        result = service.get_baseline(uuid4())
        assert result is None

    def test_compare_baselines(self, service):
        """Test baseline comparison."""
        baseline1 = PerformanceBaseline(
            id=uuid4(),
            system_name="test",
            environment="prod",
            version="1.0",
            response_times=[ResponseTimeBaseline(
                "/api/users", "GET",
                PercentileStats(50, 75, 100, 125, 150, 80, 20, 150, 30),
                100
            )],
            throughput=ThroughputBaseline(100.0, 150.0, 90.0, 5.0),
            resource_usage=ResourceUsageBaseline(45.0, 512.0, 25.0, 10.0, 5.0),
            database_queries=[],
            external_services=[],
            capture_start=datetime.now(timezone.utc),
            capture_end=datetime.now(timezone.utc)
        )

        baseline2 = PerformanceBaseline(
            id=uuid4(),
            system_name="test",
            environment="prod",
            version="2.0",
            response_times=[ResponseTimeBaseline(
                "/api/users", "GET",
                PercentileStats(55, 80, 110, 140, 170, 90, 25, 170, 35),  # Slightly worse
                100
            )],
            throughput=ThroughputBaseline(95.0, 140.0, 85.0, 5.5),
            resource_usage=ResourceUsageBaseline(50.0, 550.0, 27.0, 11.0, 6.0),
            database_queries=[],
            external_services=[],
            capture_start=datetime.now(timezone.utc),
            capture_end=datetime.now(timezone.utc)
        )

        service.store_baseline(baseline1)
        service.store_baseline(baseline2)

        comparison = service.compare_baselines(baseline1.id, baseline2.id)

        assert comparison is not None
        assert comparison.baseline_id == baseline1.id

    def test_detect_regression_threshold(self, service):
        """Test regression detection threshold."""
        # Test with 10% threshold
        is_regression = service._is_regression(100, 115, threshold=0.10)
        assert is_regression is True

        is_regression = service._is_regression(100, 105, threshold=0.10)
        assert is_regression is False

    def test_detect_improvement(self, service):
        """Test improvement detection."""
        is_improvement = service._is_improvement(100, 85, threshold=0.10)
        assert is_improvement is True

        is_improvement = service._is_improvement(100, 98, threshold=0.10)
        assert is_improvement is False

    def test_list_baselines(self, service, response_time_baseline):
        """Test listing baselines."""
        for i in range(3):
            baseline = PerformanceBaseline(
                id=uuid4(),
                system_name=f"system-{i}",
                environment="prod",
                version="1.0",
                response_times=[response_time_baseline],
                throughput=ThroughputBaseline(100.0, 150.0, 90.0, 5.0),
                resource_usage=ResourceUsageBaseline(45.0, 512.0, 25.0, 10.0, 5.0),
                database_queries=[],
                external_services=[],
                capture_start=datetime.now(timezone.utc),
                capture_end=datetime.now(timezone.utc)
            )
            service.store_baseline(baseline)

        baselines = service.list_baselines()

        assert len(baselines) == 3

    def test_list_baselines_filter_by_system(self, service, response_time_baseline):
        """Test listing baselines filtered by system."""
        for i, name in enumerate(["api", "api", "web"]):
            baseline = PerformanceBaseline(
                id=uuid4(),
                system_name=name,
                environment="prod",
                version="1.0",
                response_times=[response_time_baseline],
                throughput=ThroughputBaseline(100.0, 150.0, 90.0, 5.0),
                resource_usage=ResourceUsageBaseline(45.0, 512.0, 25.0, 10.0, 5.0),
                database_queries=[],
                external_services=[],
                capture_start=datetime.now(timezone.utc),
                capture_end=datetime.now(timezone.utc)
            )
            service.store_baseline(baseline)

        api_baselines = service.list_baselines(system_name="api")

        assert len(api_baselines) == 2

    def test_delete_baseline(self, service, response_time_baseline):
        """Test baseline deletion."""
        baseline = PerformanceBaseline(
            id=uuid4(),
            system_name="test",
            environment="prod",
            version="1.0",
            response_times=[response_time_baseline],
            throughput=ThroughputBaseline(100.0, 150.0, 90.0, 5.0),
            resource_usage=ResourceUsageBaseline(45.0, 512.0, 25.0, 10.0, 5.0),
            database_queries=[],
            external_services=[],
            capture_start=datetime.now(timezone.utc),
            capture_end=datetime.now(timezone.utc)
        )

        service.store_baseline(baseline)
        assert service.get_baseline(baseline.id) is not None

        result = service.delete_baseline(baseline.id)

        assert result is True
        assert service.get_baseline(baseline.id) is None

    def test_delete_baseline_not_found(self, service):
        """Test deleting nonexistent baseline."""
        result = service.delete_baseline(uuid4())
        assert result is False


# ==================== Enums Tests ====================

class TestEnums:
    """Test enum values."""

    def test_metric_type_values(self):
        """Test MetricType enum values."""
        assert MetricType.RESPONSE_TIME.value == "response_time"
        assert MetricType.THROUGHPUT.value == "throughput"
        assert MetricType.CPU_USAGE.value == "cpu_usage"

    def test_baseline_status_values(self):
        """Test BaselineStatus enum values."""
        assert BaselineStatus.PASS.value == "pass"
        assert BaselineStatus.REGRESSION.value == "regression"
        assert BaselineStatus.IMPROVEMENT.value == "improvement"
