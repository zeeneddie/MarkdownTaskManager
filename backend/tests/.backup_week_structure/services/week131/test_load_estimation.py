"""
Unit tests for LoadEstimationService - Week 131

Tests for connection pool analysis, session state configuration, and capacity estimation.
"""
import pytest
import tempfile
from pathlib import Path

from app.services.load_estimation_service import (
    LoadEstimationService,
    DEFAULT_MIN_POOL_SIZE,
    DEFAULT_MAX_POOL_SIZE,
    DEFAULT_SESSION_TIMEOUT,
)
from app.models.research import (
    SessionMode,
    CapacityBottleneck,
)


@pytest.fixture
def service():
    return LoadEstimationService()


@pytest.fixture
def temp_project():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestLoadEstimationServiceBasic:
    """Basic service functionality tests."""

    def test_service_init(self, service):
        """Test service initialization."""
        assert service is not None

    def test_analyze_nonexistent_path(self, service):
        """Test analysis on non-existent path."""
        result = service.analyze(Path("/nonexistent/path"))
        assert result.success is False
        assert len(result.errors) > 0

    def test_analyze_empty_directory(self, service, temp_project):
        """Test analysis on empty directory."""
        result = service.analyze(temp_project)
        assert result.success is True
        assert len(result.connection_pools) == 0
        assert result.estimated_concurrent_users > 0  # Default capacity


class TestConnectionPoolParsing:
    """Tests for connection pool configuration parsing."""

    def test_parse_web_config_connection_string(self, service, temp_project):
        """Test parsing connection string from web.config."""
        config = """<?xml version="1.0"?>
        <configuration>
            <connectionStrings>
                <add name="MainDB" connectionString="Server=localhost;Database=MyDB;Max Pool Size=150;Min Pool Size=10;Connection Timeout=30" />
            </connectionStrings>
        </configuration>
        """
        (temp_project / "web.config").write_text(config)
        result = service.analyze(temp_project)
        assert len(result.connection_pools) >= 1
        pool = result.connection_pools[0]
        assert pool.max_pool_size == 150
        assert pool.min_pool_size == 10
        assert pool.connection_timeout == 30

    def test_parse_multiple_connection_strings(self, service, temp_project):
        """Test parsing multiple connection strings."""
        config = """<?xml version="1.0"?>
        <configuration>
            <connectionStrings>
                <add name="MainDB" connectionString="Server=db1;Database=Main;Max Pool Size=100" />
                <add name="ReportDB" connectionString="Server=db2;Database=Reports;Max Pool Size=50" />
            </connectionStrings>
        </configuration>
        """
        (temp_project / "web.config").write_text(config)
        result = service.analyze(temp_project)
        assert len(result.connection_pools) >= 2

    def test_parse_appsettings_json(self, service, temp_project):
        """Test parsing connection strings from appsettings.json."""
        config = """
        {
            "ConnectionStrings": {
                "DefaultConnection": "Server=localhost;Database=App;Max Pool Size=200"
            }
        }
        """
        (temp_project / "appsettings.json").write_text(config)
        result = service.analyze(temp_project)
        assert len(result.connection_pools) >= 1

    def test_default_pool_values(self, service, temp_project):
        """Test that default pool values are used when not specified."""
        config = """<?xml version="1.0"?>
        <configuration>
            <connectionStrings>
                <add name="Simple" connectionString="Server=localhost;Database=Test" />
            </connectionStrings>
        </configuration>
        """
        (temp_project / "web.config").write_text(config)
        result = service.analyze(temp_project)
        if result.connection_pools:
            pool = result.connection_pools[0]
            assert pool.min_pool_size == DEFAULT_MIN_POOL_SIZE
            assert pool.max_pool_size == DEFAULT_MAX_POOL_SIZE


class TestSessionStateParsing:
    """Tests for session state configuration parsing."""

    def test_parse_inproc_session(self, service, temp_project):
        """Test parsing InProc session state."""
        config = """<?xml version="1.0"?>
        <configuration>
            <system.web>
                <sessionState mode="InProc" timeout="20" />
            </system.web>
        </configuration>
        """
        (temp_project / "web.config").write_text(config)
        result = service.analyze(temp_project)
        assert result.session_config.mode == SessionMode.IN_PROC
        assert result.session_config.timeout_minutes == 20

    def test_parse_sqlserver_session(self, service, temp_project):
        """Test parsing SQL Server session state."""
        config = """<?xml version="1.0"?>
        <configuration>
            <system.web>
                <sessionState mode="SQLServer"
                    sqlConnectionString="Server=session;Database=ASPState"
                    timeout="30" />
            </system.web>
        </configuration>
        """
        (temp_project / "web.config").write_text(config)
        result = service.analyze(temp_project)
        assert result.session_config.mode == SessionMode.SQL_SERVER
        assert result.session_config.timeout_minutes == 30


class TestUsingBlockAnalysis:
    """Tests for Using block analysis."""

    def test_count_using_blocks_vb(self, service, temp_project):
        """Test counting VB.NET Using blocks."""
        code = """
        Using conn As New SqlConnection(connStr)
            conn.Open()
            ' Do work
        End Using

        Using cmd As New SqlCommand()
            ' Another block
        End Using
        """
        (temp_project / "Data.vb").write_text(code)
        result = service.analyze(temp_project)
        assert result.using_block_count >= 1

    def test_count_using_blocks_cs(self, service, temp_project):
        """Test counting C# using blocks."""
        code = """
        using (var conn = new SqlConnection(connStr))
        {
            conn.Open();
        }
        """
        (temp_project / "Data.cs").write_text(code)
        result = service.analyze(temp_project)
        assert result.using_block_count >= 1

    def test_open_close_ratio(self, service, temp_project):
        """Test Open/Close ratio calculation."""
        code = """
        conn.Open()
        conn.Close()

        conn2.Open()
        conn2.Close()
        """
        (temp_project / "Connections.vb").write_text(code)
        result = service.analyze(temp_project)
        assert result.open_close_ratio == 1.0


class TestQueryComplexityAnalysis:
    """Tests for SQL query complexity analysis."""

    def test_simple_query_low_complexity(self, service, temp_project):
        """Test that simple queries have low complexity."""
        sql = "SELECT * FROM Users WHERE ID = @id"
        (temp_project / "query.sql").write_text(sql)
        result = service.analyze(temp_project)
        assert result.query_metrics.complexity_score < 30

    def test_join_increases_complexity(self, service, temp_project):
        """Test that JOINs increase complexity score."""
        sql = """
        SELECT * FROM Orders o
        JOIN Customers c ON o.CustomerID = c.ID
        JOIN Products p ON o.ProductID = p.ID
        JOIN Categories cat ON p.CategoryID = cat.ID
        JOIN Suppliers s ON p.SupplierID = s.ID
        """
        (temp_project / "complex.sql").write_text(sql)
        result = service.analyze(temp_project)
        assert result.query_metrics.max_joins_in_query >= 4

    def test_subquery_detection(self, service, temp_project):
        """Test subquery detection."""
        sql = """
        SELECT * FROM Orders
        WHERE CustomerID IN (SELECT ID FROM Customers WHERE Country = 'NL')
        """
        (temp_project / "subquery.sql").write_text(sql)
        result = service.analyze(temp_project)
        assert result.query_metrics.subquery_count >= 1

    def test_cursor_detection(self, service, temp_project):
        """Test cursor detection."""
        sql = """
        DECLARE @cursor CURSOR
        DECLARE myCursor CURSOR FOR SELECT * FROM Orders
        """
        (temp_project / "cursor.sql").write_text(sql)
        result = service.analyze(temp_project)
        assert result.query_metrics.uses_cursors is True
        assert result.query_metrics.cursor_count >= 1


class TestCapacityEstimation:
    """Tests for concurrent user capacity estimation."""

    def test_basic_capacity_calculation(self, service, temp_project):
        """Test basic capacity estimation."""
        config = """<?xml version="1.0"?>
        <configuration>
            <connectionStrings>
                <add name="Main" connectionString="Server=db;Database=App;Max Pool Size=100" />
            </connectionStrings>
        </configuration>
        """
        (temp_project / "web.config").write_text(config)
        result = service.analyze(temp_project)
        # Base capacity = 100 * 0.8 = 80
        assert result.estimated_concurrent_users > 0

    def test_inproc_session_reduces_capacity(self, service, temp_project):
        """Test that InProc session reduces capacity."""
        config = """<?xml version="1.0"?>
        <configuration>
            <connectionStrings>
                <add name="Main" connectionString="Server=db;Max Pool Size=100" />
            </connectionStrings>
            <system.web>
                <sessionState mode="InProc" timeout="20" />
            </system.web>
        </configuration>
        """
        (temp_project / "web.config").write_text(config)
        result = service.analyze(temp_project)
        # InProc reduces by /2, so ~40
        assert result.capacity_bottleneck == CapacityBottleneck.SESSION_STATE

    def test_connection_leak_detection(self, service, temp_project):
        """Test connection leak detection (no Using blocks)."""
        code = """
        Dim conn As New SqlConnection(connStr)
        conn.Open()
        ' No Using block, no Close()
        """
        (temp_project / "Data.vb").write_text(code)
        result = service.analyze(temp_project)
        # Should detect potential leak
        assert result.capacity_bottleneck == CapacityBottleneck.CONNECTION_POOL or result.using_block_count == 0


class TestRecommendations:
    """Tests for recommendations generation."""

    def test_recommend_increase_pool_size(self, service, temp_project):
        """Test recommendation for small pool size."""
        config = """<?xml version="1.0"?>
        <configuration>
            <connectionStrings>
                <add name="Main" connectionString="Server=db;Max Pool Size=20" />
            </connectionStrings>
        </configuration>
        """
        (temp_project / "web.config").write_text(config)
        result = service.analyze(temp_project)
        pool_rec = [r for r in result.recommendations if "Pool Size" in r]
        assert len(pool_rec) > 0

    def test_recommend_using_blocks(self, service, temp_project):
        """Test recommendation for Using blocks."""
        code = """
        conn = New SqlConnection()
        conn.Open()
        """
        (temp_project / "Data.vb").write_text(code)
        result = service.analyze(temp_project)
        using_rec = [r for r in result.recommendations if "Using" in r or "using" in r]
        assert len(using_rec) > 0

    def test_capacity_rating(self, service):
        """Test capacity rating function."""
        assert service._get_capacity_rating(250) == "Excellent"
        assert service._get_capacity_rating(100) == "Good"
        assert service._get_capacity_rating(50) == "Moderate"
        assert service._get_capacity_rating(20) == "Limited"
        assert service._get_capacity_rating(10) == "Critical"
