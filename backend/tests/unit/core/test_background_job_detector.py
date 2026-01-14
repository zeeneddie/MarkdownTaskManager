"""
Unit tests for BackgroundJobDetectorService - Week 131

Tests for detection of background jobs, scheduled tasks, and batch processes.
"""
import pytest
import tempfile
from pathlib import Path

from app.services.background_job_detector_service import (
    BackgroundJobDetectorService,
    NAMING_PATTERNS,
    DIRECTORY_PATTERNS,
    CODE_PATTERNS,
)
from app.models.research import (
    JobType,
    TriggerType,
    DetectionMethod,
)


@pytest.fixture
def service():
    return BackgroundJobDetectorService()


@pytest.fixture
def temp_project():
    """Create a temporary project directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestBackgroundJobDetectorServiceBasic:
    """Basic service functionality tests."""

    def test_service_init(self, service):
        """Test service initialization."""
        assert service is not None
        assert service._job_counter == 0

    def test_detect_nonexistent_path(self, service):
        """Test detection on non-existent path."""
        result = service.detect(Path("/nonexistent/path"))
        assert result.success is False
        assert len(result.errors) > 0
        assert "does not exist" in result.errors[0]

    def test_detect_empty_directory(self, service, temp_project):
        """Test detection on empty directory."""
        result = service.detect(temp_project)
        assert result.success is True
        assert result.total_jobs == 0
        assert result.files_scanned == 0


class TestNamingPatternDetection:
    """Tests for naming convention detection."""

    def test_detect_nachtjob_naming(self, service, temp_project):
        """Test detection of Nachtjob naming pattern."""
        (temp_project / "ROMNachtjob.vb").write_text("Public Class ROMNachtjob\nEnd Class")
        result = service.detect(temp_project)
        assert result.total_jobs >= 1
        job = next((j for j in result.jobs if "nachtjob" in j.name.lower()), None)
        assert job is not None
        assert job.job_type == JobType.NIGHTLY
        assert job.confidence >= 0.8

    def test_detect_batch_naming(self, service, temp_project):
        """Test detection of Batch naming pattern."""
        (temp_project / "ProcessBatch.cs").write_text("public class ProcessBatch { }")
        result = service.detect(temp_project)
        assert result.total_jobs >= 1
        job = next((j for j in result.jobs if "batch" in j.name.lower()), None)
        assert job is not None
        assert job.detection_method == DetectionMethod.NAMING

    def test_detect_scheduler_naming(self, service, temp_project):
        """Test detection of Scheduler naming pattern."""
        (temp_project / "TaskScheduler.vb").write_text("Public Class TaskScheduler\nEnd Class")
        result = service.detect(temp_project)
        assert result.total_jobs >= 1

    def test_multiple_naming_patterns(self, service, temp_project):
        """Test detection of multiple naming patterns."""
        (temp_project / "NightlyBatch.cs").write_text("class NightlyBatch { }")
        (temp_project / "CronJob.cs").write_text("class CronJob { }")
        (temp_project / "TimerWorker.cs").write_text("class TimerWorker { }")
        result = service.detect(temp_project)
        assert result.total_jobs >= 3


class TestDirectoryPatternDetection:
    """Tests for directory pattern detection."""

    def test_detect_jobs_directory(self, service, temp_project):
        """Test detection of /Jobs/ directory pattern."""
        jobs_dir = temp_project / "Jobs"
        jobs_dir.mkdir()
        (jobs_dir / "ProcessData.cs").write_text("class ProcessData { }")
        result = service.detect(temp_project)
        assert result.total_jobs >= 1
        job = next((j for j in result.jobs if "ProcessData" in j.name), None)
        assert job is not None

    def test_detect_beheer_directory(self, service, temp_project):
        """Test detection of /Beheer/ directory pattern."""
        beheer_dir = temp_project / "Beheer"
        beheer_dir.mkdir()
        (beheer_dir / "AdminTask.vb").write_text("Public Class AdminTask\nEnd Class")
        result = service.detect(temp_project)
        assert result.total_jobs >= 1


class TestCodePatternDetection:
    """Tests for code pattern detection."""

    def test_detect_timer_elapsed(self, service, temp_project):
        """Test detection of Timer_Elapsed pattern."""
        code = """
        Private Sub Timer_Elapsed(sender As Object, e As ElapsedEventArgs)
            ProcessData()
        End Sub
        """
        (temp_project / "Service.vb").write_text(code)
        result = service.detect(temp_project)
        assert result.total_jobs >= 1
        job = next((j for j in result.jobs if j.trigger_type == TriggerType.TIMER), None)
        assert job is not None

    def test_detect_background_worker(self, service, temp_project):
        """Test detection of BackgroundWorker pattern."""
        code = """
        private BackgroundWorker worker;
        worker = new BackgroundWorker();
        """
        (temp_project / "Worker.cs").write_text(code)
        result = service.detect(temp_project)
        assert result.total_jobs >= 1

    def test_detect_hosted_service(self, service, temp_project):
        """Test detection of IHostedService pattern."""
        code = """
        public class MyService : IHostedService
        {
            public Task StartAsync(CancellationToken ct) => Task.CompletedTask;
        }
        """
        (temp_project / "MyService.cs").write_text(code)
        result = service.detect(temp_project)
        assert result.total_jobs >= 1
        job = next((j for j in result.jobs if j.trigger_type == TriggerType.STARTUP), None)
        assert job is not None


class TestSQLAgentJobDetection:
    """Tests for SQL Server Agent job detection."""

    def test_detect_sp_add_job(self, service, temp_project):
        """Test detection of sp_add_job SQL pattern."""
        sql = """
        EXEC sp_add_job @job_name = N'NightlyDataSync',
            @enabled = 1,
            @description = N'Sync data nightly'
        """
        (temp_project / "jobs.sql").write_text(sql)
        result = service.detect(temp_project)
        assert result.total_jobs >= 1
        job = next((j for j in result.jobs if "NightlyDataSync" in j.name), None)
        assert job is not None
        assert job.trigger_type == TriggerType.SQL_AGENT
        assert job.confidence >= 0.9


class TestConfigPatternDetection:
    """Tests for configuration file detection."""

    def test_detect_quartz_config(self, service, temp_project):
        """Test detection of Quartz.NET configuration."""
        config = """
        <configuration>
            <quartz>
                <job name="MyJob">
                    <cron-expression>0 0 1 * * ?</cron-expression>
                </job>
            </quartz>
        </configuration>
        """
        (temp_project / "quartz.config").write_text(config)
        result = service.detect(temp_project)
        assert result.total_jobs >= 1

    def test_detect_hangfire_pattern(self, service, temp_project):
        """Test detection of Hangfire pattern."""
        code = """
        RecurringJob.AddOrUpdate("my-job", () => ProcessData(), "0 1 * * *");
        """
        (temp_project / "Jobs.cs").write_text(code)
        result = service.detect(temp_project)
        assert result.total_jobs >= 1
        job = next((j for j in result.jobs if j.trigger_type == TriggerType.HANGFIRE), None)
        assert job is not None


class TestErrorHandlingAnalysis:
    """Tests for error handling detection."""

    def test_detect_try_catch(self, service, temp_project):
        """Test detection of try-catch error handling."""
        code = """
        public class BatchJob {
            public void Run() {
                try {
                    ProcessData();
                } catch (Exception ex) {
                    LogError(ex);
                }
            }
        }
        """
        (temp_project / "BatchJob.cs").write_text(code)
        result = service.detect(temp_project)
        assert result.total_jobs >= 1
        job = result.jobs[0]
        assert job.has_error_handling is True


class TestDatabaseDependencyExtraction:
    """Tests for database dependency extraction."""

    def test_extract_table_dependencies(self, service, temp_project):
        """Test extraction of SQL table dependencies."""
        code = """
        SELECT * FROM Orders o
        JOIN Customers c ON o.CustomerID = c.ID
        INSERT INTO OrderLog (Message) VALUES (@msg)
        """
        (temp_project / "DataBatch.sql").write_text(code)
        result = service.detect(temp_project)
        # Should extract Orders, Customers, OrderLog as dependencies


class TestBatchTableDetection:
    """Tests for batch-related table detection."""

    def test_detect_batch_tables(self, service):
        """Test identification of batch-related tables."""
        table_names = [
            "Orders", "OrderLog", "BatchJobs", "TaskQueue",
            "ProcessHistory", "ScheduleConfig", "Users"
        ]
        batch_tables = service.detect_batch_tables(table_names)
        assert "OrderLog" in batch_tables
        assert "BatchJobs" in batch_tables
        assert "TaskQueue" in batch_tables
        assert "ScheduleConfig" in batch_tables
        assert "Users" not in batch_tables
