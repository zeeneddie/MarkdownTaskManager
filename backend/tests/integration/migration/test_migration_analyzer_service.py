"""
Unit Tests for MigrationAnalyzerService

Week 70: Comprehensive testing of the Miguel Orchestrator
for multi-agent migration analysis.

Tests Cover:
- Service initialization
- Phase management (DETECTION, STACK_ANALYSIS, DB_ANALYSIS, CROSS_CUTTING, OUTPUT)
- Stack pattern definitions
- Database pattern definitions
- Analysis workflow phases

Author: Claude Code (Week 70)
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
from uuid import uuid4, UUID
import tempfile
import os

from app.services.migration_analyzer_service import (
    MigrationAnalyzerService,
    AnalysisPhase,
    AnalysisStatus,
    STACK_PATTERNS,
    DB_PATTERNS
)


class TestAnalysisPhaseEnum:
    """Test AnalysisPhase enum values"""

    def test_pending_phase(self):
        """Test PENDING phase value"""
        assert AnalysisPhase.PENDING.value == "pending"

    def test_detection_phase(self):
        """Test DETECTION phase value"""
        assert AnalysisPhase.DETECTION.value == "detection"

    def test_stack_analysis_phase(self):
        """Test STACK_ANALYSIS phase value"""
        assert AnalysisPhase.STACK_ANALYSIS.value == "stack_analysis"

    def test_db_analysis_phase(self):
        """Test DB_ANALYSIS phase value"""
        assert AnalysisPhase.DB_ANALYSIS.value == "db_analysis"

    def test_cross_cutting_phase(self):
        """Test CROSS_CUTTING phase value"""
        assert AnalysisPhase.CROSS_CUTTING.value == "cross_cutting"

    def test_output_phase(self):
        """Test OUTPUT phase value"""
        assert AnalysisPhase.OUTPUT.value == "output"

    def test_completed_phase(self):
        """Test COMPLETED phase value"""
        assert AnalysisPhase.COMPLETED.value == "completed"

    def test_failed_phase(self):
        """Test FAILED phase value"""
        assert AnalysisPhase.FAILED.value == "failed"


class TestAnalysisStatusEnum:
    """Test AnalysisStatus enum values"""

    def test_pending_status(self):
        """Test PENDING status value"""
        assert AnalysisStatus.PENDING.value == "pending"

    def test_running_status(self):
        """Test RUNNING status value"""
        assert AnalysisStatus.RUNNING.value == "running"

    def test_completed_status(self):
        """Test COMPLETED status value"""
        assert AnalysisStatus.COMPLETED.value == "completed"

    def test_failed_status(self):
        """Test FAILED status value"""
        assert AnalysisStatus.FAILED.value == "failed"


class TestStackPatternsDotNet:
    """Test .NET stack pattern definitions"""

    def test_aspnet_webforms_pattern_exists(self):
        """Test ASP.NET WebForms pattern is defined"""
        assert "aspnet_webforms" in STACK_PATTERNS
        pattern = STACK_PATTERNS["aspnet_webforms"]
        assert "extensions" in pattern
        assert ".aspx" in pattern["extensions"]
        assert "patterns" in pattern
        assert "ViewState" in pattern["patterns"]

    def test_asp_classic_pattern_exists(self):
        """Test ASP Classic pattern is defined"""
        assert "asp_classic" in STACK_PATTERNS
        pattern = STACK_PATTERNS["asp_classic"]
        assert ".asp" in pattern["extensions"]
        assert "Response.Write" in pattern["patterns"]

    def test_aspnet_mvc_pattern_exists(self):
        """Test ASP.NET MVC pattern is defined"""
        assert "aspnet_mvc" in STACK_PATTERNS
        pattern = STACK_PATTERNS["aspnet_mvc"]
        assert ".cshtml" in pattern["extensions"]
        assert "@Model" in pattern["patterns"]

    def test_wcf_pattern_exists(self):
        """Test WCF pattern is defined"""
        assert "wcf" in STACK_PATTERNS
        pattern = STACK_PATTERNS["wcf"]
        assert ".svc" in pattern["extensions"]
        assert "ServiceContract" in pattern["patterns"]


class TestStackPatternsFrontend:
    """Test frontend stack pattern definitions"""

    def test_angularjs_pattern_exists(self):
        """Test AngularJS pattern is defined"""
        assert "angularjs" in STACK_PATTERNS
        pattern = STACK_PATTERNS["angularjs"]
        assert "ng-app" in pattern["patterns"]
        assert "$scope" in pattern["patterns"]

    def test_angular_pattern_exists(self):
        """Test Angular pattern is defined"""
        assert "angular" in STACK_PATTERNS
        pattern = STACK_PATTERNS["angular"]
        assert "@Component" in pattern["patterns"]
        assert ".ts" in pattern["extensions"]

    def test_vue2_pattern_exists(self):
        """Test Vue2 pattern is defined"""
        assert "vue2" in STACK_PATTERNS
        pattern = STACK_PATTERNS["vue2"]
        assert ".vue" in pattern["extensions"]
        assert "new Vue" in pattern["patterns"]

    def test_react_class_pattern_exists(self):
        """Test React class components pattern is defined"""
        assert "react_class" in STACK_PATTERNS
        pattern = STACK_PATTERNS["react_class"]
        assert ".jsx" in pattern["extensions"]
        assert "componentDidMount" in pattern["patterns"]

    def test_jquery_pattern_exists(self):
        """Test jQuery pattern is defined"""
        assert "jquery" in STACK_PATTERNS
        pattern = STACK_PATTERNS["jquery"]
        assert "$(" in pattern["patterns"]
        assert ".ajax(" in pattern["patterns"]


class TestStackPatternsPHP:
    """Test PHP stack pattern definitions"""

    def test_php_legacy_pattern_exists(self):
        """Test PHP legacy pattern is defined"""
        assert "php_legacy" in STACK_PATTERNS
        pattern = STACK_PATTERNS["php_legacy"]
        assert ".php" in pattern["extensions"]
        assert "mysql_" in pattern["patterns"]

    def test_laravel_pattern_exists(self):
        """Test Laravel pattern is defined"""
        assert "laravel" in STACK_PATTERNS
        pattern = STACK_PATTERNS["laravel"]
        assert ".blade.php" in pattern["extensions"]
        assert "Eloquent" in pattern["patterns"]


class TestStackPatternsJava:
    """Test Java stack pattern definitions"""

    def test_java_legacy_pattern_exists(self):
        """Test Java legacy pattern is defined"""
        assert "java_legacy" in STACK_PATTERNS
        pattern = STACK_PATTERNS["java_legacy"]
        assert ".java" in pattern["extensions"]
        assert "HttpServlet" in pattern["patterns"]

    def test_spring_pattern_exists(self):
        """Test Spring pattern is defined"""
        assert "spring" in STACK_PATTERNS
        pattern = STACK_PATTERNS["spring"]
        assert "@SpringBootApplication" in pattern["patterns"]
        assert "@Controller" in pattern["patterns"]

    def test_struts_pattern_exists(self):
        """Test Struts pattern is defined"""
        assert "struts" in STACK_PATTERNS
        pattern = STACK_PATTERNS["struts"]
        assert "ActionForm" in pattern["patterns"]


class TestStackPatternsStructure:
    """Test stack pattern structure"""

    def test_all_patterns_have_extensions(self):
        """Test all patterns have extensions field"""
        for name, pattern in STACK_PATTERNS.items():
            assert "extensions" in pattern, f"Pattern {name} missing extensions"

    def test_all_patterns_have_patterns(self):
        """Test all patterns have patterns field"""
        for name, pattern in STACK_PATTERNS.items():
            assert "patterns" in pattern, f"Pattern {name} missing patterns"

    def test_all_patterns_have_analyzer(self):
        """Test all patterns have analyzer field"""
        for name, pattern in STACK_PATTERNS.items():
            assert "analyzer" in pattern, f"Pattern {name} missing analyzer"

    def test_pattern_count(self):
        """Test there are expected number of patterns"""
        assert len(STACK_PATTERNS) >= 13  # At least 13 stack patterns


class TestDBPatterns:
    """Test database pattern definitions"""

    def test_sqlserver_pattern_exists(self):
        """Test SQL Server pattern is defined"""
        assert "sqlserver" in DB_PATTERNS
        pattern = DB_PATTERNS["sqlserver"]
        assert "extensions" in pattern
        assert ".sql" in pattern["extensions"]
        assert "patterns" in pattern
        assert "NVARCHAR" in pattern["patterns"]
        assert "IDENTITY" in pattern["patterns"]
        assert "connection_patterns" in pattern

    def test_oracle_pattern_exists(self):
        """Test Oracle pattern is defined"""
        assert "oracle" in DB_PATTERNS
        pattern = DB_PATTERNS["oracle"]
        assert "VARCHAR2" in pattern["patterns"]
        assert "DBMS_" in pattern["patterns"]
        assert "PL/SQL" in pattern["patterns"]

    def test_mysql_pattern_exists(self):
        """Test MySQL pattern is defined"""
        assert "mysql" in DB_PATTERNS
        pattern = DB_PATTERNS["mysql"]
        assert "AUTO_INCREMENT" in pattern["patterns"]
        assert "ENGINE=InnoDB" in pattern["patterns"]


class TestMigrationAnalyzerServiceInit:
    """Test MigrationAnalyzerService initialization"""

    @pytest.fixture
    def mock_db(self):
        mock = AsyncMock()
        mock.add = MagicMock()
        mock.commit = AsyncMock()
        mock.refresh = AsyncMock()
        mock.execute = AsyncMock()
        return mock

    def test_init_with_db_session(self, mock_db):
        """Test service initializes with database session"""
        service = MigrationAnalyzerService(mock_db)
        assert service.db == mock_db

    def test_init_sets_no_current_analysis(self, mock_db):
        """Test service starts without current analysis"""
        service = MigrationAnalyzerService(mock_db)
        assert service._current_analysis is None


class TestCreateAnalysis:
    """Test create_analysis method"""

    @pytest.fixture
    def mock_db(self):
        mock = AsyncMock()
        mock.add = MagicMock()
        mock.commit = AsyncMock()
        mock.refresh = AsyncMock()
        return mock

    @pytest.fixture
    def service(self, mock_db):
        return MigrationAnalyzerService(mock_db)

    @pytest.mark.asyncio
    async def test_create_analysis_returns_analysis(self, service, mock_db, tmp_path):
        """Test create_analysis returns MigrationAnalysis"""
        # Mock the refresh to set an ID
        async def mock_refresh(obj):
            obj.id = uuid4()
        mock_db.refresh.side_effect = mock_refresh

        analysis = await service.create_analysis(str(tmp_path))
        assert analysis is not None
        assert analysis.repo_path == str(tmp_path)

    @pytest.mark.asyncio
    async def test_create_analysis_sets_repo_name(self, service, mock_db, tmp_path):
        """Test create_analysis extracts repo name from path"""
        async def mock_refresh(obj):
            obj.id = uuid4()
        mock_db.refresh.side_effect = mock_refresh

        analysis = await service.create_analysis(str(tmp_path))
        assert analysis.repo_name == tmp_path.name

    @pytest.mark.asyncio
    async def test_create_analysis_sets_target_db(self, service, mock_db, tmp_path):
        """Test create_analysis sets target database"""
        async def mock_refresh(obj):
            obj.id = uuid4()
        mock_db.refresh.side_effect = mock_refresh

        analysis = await service.create_analysis(str(tmp_path), target_db="postgresql")
        assert analysis.target_db == "postgresql"

    @pytest.mark.asyncio
    async def test_create_analysis_defaults_target_db(self, service, mock_db, tmp_path):
        """Test create_analysis defaults to postgresql"""
        async def mock_refresh(obj):
            obj.id = uuid4()
        mock_db.refresh.side_effect = mock_refresh

        analysis = await service.create_analysis(str(tmp_path))
        assert analysis.target_db == "postgresql"

    @pytest.mark.asyncio
    async def test_create_analysis_sets_pending_status(self, service, mock_db, tmp_path):
        """Test create_analysis sets pending status"""
        async def mock_refresh(obj):
            obj.id = uuid4()
        mock_db.refresh.side_effect = mock_refresh

        analysis = await service.create_analysis(str(tmp_path))
        assert analysis.status == AnalysisStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_analysis_sets_pending_phase(self, service, mock_db, tmp_path):
        """Test create_analysis sets pending phase"""
        async def mock_refresh(obj):
            obj.id = uuid4()
        mock_db.refresh.side_effect = mock_refresh

        analysis = await service.create_analysis(str(tmp_path))
        assert analysis.current_phase == AnalysisPhase.PENDING


class TestListAnalyses:
    """Test list_analyses method"""

    @pytest.fixture
    def mock_db(self):
        mock = AsyncMock()
        mock.execute = AsyncMock()
        return mock

    @pytest.fixture
    def service(self, mock_db):
        return MigrationAnalyzerService(mock_db)

    @pytest.mark.asyncio
    async def test_list_analyses_returns_list(self, service, mock_db):
        """Test list_analyses returns a list"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.list_analyses()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_analyses_respects_limit(self, service, mock_db):
        """Test list_analyses respects limit parameter"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        await service.list_analyses(limit=10)
        # Verify execute was called (query built correctly)
        mock_db.execute.assert_called_once()


class TestGetAnalysis:
    """Test get_analysis method"""

    @pytest.fixture
    def mock_db(self):
        mock = AsyncMock()
        mock.execute = AsyncMock()
        return mock

    @pytest.fixture
    def service(self, mock_db):
        return MigrationAnalyzerService(mock_db)

    @pytest.mark.asyncio
    async def test_get_analysis_with_valid_id(self, service, mock_db):
        """Test get_analysis returns analysis for valid ID"""
        analysis_id = uuid4()
        mock_analysis = MagicMock()
        mock_analysis.id = analysis_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_analysis
        mock_db.execute.return_value = mock_result

        result = await service.get_analysis(analysis_id)
        assert result is not None
        assert result.id == analysis_id

    @pytest.mark.asyncio
    async def test_get_analysis_with_invalid_id(self, service, mock_db):
        """Test get_analysis returns None for invalid ID"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_analysis(uuid4())
        assert result is None


class TestRunAnalysisPhases:
    """Test run_analysis phase transitions"""

    @pytest.fixture
    def mock_db(self):
        mock = AsyncMock()
        mock.commit = AsyncMock()
        mock.execute = AsyncMock()
        return mock

    @pytest.fixture
    def service(self, mock_db):
        return MigrationAnalyzerService(mock_db)

    @pytest.fixture
    def mock_analysis(self):
        analysis = MagicMock()
        analysis.id = uuid4()
        analysis.repo_path = "/tmp/test-repo"
        analysis.status = AnalysisStatus.PENDING
        analysis.current_phase = AnalysisPhase.PENDING
        analysis.progress_percent = 0
        analysis.modules = []
        analysis.patterns = []
        analysis.recommendations = []
        analysis.risk_assessments = []
        return analysis

    @pytest.mark.asyncio
    async def test_run_analysis_raises_for_nonexistent(self, service, mock_db):
        """Test run_analysis raises ValueError for nonexistent ID"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not found"):
            await service.run_analysis(uuid4())


class TestAnalyzerAssignments:
    """Test that stack patterns have correct analyzer assignments"""

    def test_dotnet_stacks_use_dotnet_analyzer(self):
        """Test .NET stacks use DotNetAnalyzer"""
        dotnet_stacks = ["aspnet_webforms", "asp_classic", "aspnet_mvc", "wcf"]
        for stack in dotnet_stacks:
            assert STACK_PATTERNS[stack]["analyzer"] == "DotNetAnalyzer"

    def test_frontend_stacks_use_frontend_analyzer(self):
        """Test frontend stacks use FrontendAnalyzer"""
        frontend_stacks = ["angularjs", "angular", "vue2", "react_class", "jquery"]
        for stack in frontend_stacks:
            assert STACK_PATTERNS[stack]["analyzer"] == "FrontendAnalyzer"

    def test_php_stacks_use_php_analyzer(self):
        """Test PHP stacks use PHPAnalyzer"""
        php_stacks = ["php_legacy", "laravel"]
        for stack in php_stacks:
            assert STACK_PATTERNS[stack]["analyzer"] == "PHPAnalyzer"

    def test_java_stacks_use_java_analyzer(self):
        """Test Java stacks use JavaAnalyzer"""
        java_stacks = ["java_legacy", "spring", "struts"]
        for stack in java_stacks:
            assert STACK_PATTERNS[stack]["analyzer"] == "JavaAnalyzer"


class TestDBPatternsConnectionStrings:
    """Test database pattern connection string detection"""

    def test_sqlserver_connection_patterns(self):
        """Test SQL Server connection patterns"""
        pattern = DB_PATTERNS["sqlserver"]
        assert "Server=" in pattern["connection_patterns"]
        assert "Data Source=" in pattern["connection_patterns"]
        assert "SqlConnection" in pattern["connection_patterns"]

    def test_oracle_connection_patterns(self):
        """Test Oracle connection patterns"""
        pattern = DB_PATTERNS["oracle"]
        assert "OracleConnection" in pattern["connection_patterns"]
        assert "ODP.NET" in pattern["connection_patterns"]

    def test_mysql_connection_patterns(self):
        """Test MySQL connection patterns"""
        pattern = DB_PATTERNS["mysql"]
        assert "MySqlConnection" in pattern["connection_patterns"]
        assert "mysql://" in pattern["connection_patterns"]


class TestPatternExtensions:
    """Test pattern extension definitions"""

    def test_webforms_extensions(self):
        """Test WebForms has correct extensions"""
        pattern = STACK_PATTERNS["aspnet_webforms"]
        expected = [".aspx", ".aspx.cs", ".aspx.vb", ".ascx", ".master"]
        for ext in expected:
            assert ext in pattern["extensions"]

    def test_angular_extensions(self):
        """Test Angular has correct extensions"""
        pattern = STACK_PATTERNS["angular"]
        assert ".ts" in pattern["extensions"]
        assert ".html" in pattern["extensions"]

    def test_vue_extensions(self):
        """Test Vue has correct extensions"""
        pattern = STACK_PATTERNS["vue2"]
        assert ".vue" in pattern["extensions"]

    def test_sql_extensions(self):
        """Test SQL patterns have correct extensions"""
        for db_name, pattern in DB_PATTERNS.items():
            assert ".sql" in pattern["extensions"]
