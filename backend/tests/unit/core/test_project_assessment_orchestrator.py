"""
Tests for ProjectAssessmentOrchestrator (Week 69)

Tests cover:
- Orchestrator initialization (with/without LLM)
- Assessment start and run workflows
- Individual phase execution
- Score calculation
- Error handling
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from uuid import uuid4

from app.services.project_assessment_orchestrator import (
    ProjectAssessmentOrchestrator,
    PhaseResult,
    run_project_assessment,
)
from app.models.project_assessment import ProjectAssessment, AssessmentPhase


class TestProjectAssessmentOrchestratorInit:
    """Test orchestrator initialization"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    def test_init_without_llm(self, mock_db):
        """Test initialization without LLM"""
        orchestrator = ProjectAssessmentOrchestrator(mock_db, use_llm=False)

        assert orchestrator.db == mock_db
        assert orchestrator.use_llm == False
        # Note: stack_service is created per-assessment, not at init
        assert orchestrator.asis_service is not None
        assert orchestrator.llm_provider is None

    def test_init_with_llm_unavailable(self, mock_db):
        """Test initialization with LLM requested but unavailable"""
        # LLM is only used if available and requested
        orchestrator = ProjectAssessmentOrchestrator(mock_db, use_llm=True)

        # May or may not have LLM depending on environment
        # The key is it shouldn't crash
        assert orchestrator.db == mock_db

    def test_init_creates_services(self, mock_db):
        """Test that required services are created"""
        orchestrator = ProjectAssessmentOrchestrator(mock_db)

        # Note: stack_service is created per-assessment with repo_path, not at init
        assert orchestrator.asis_service is not None


class TestAssessmentStart:
    """Test assessment start workflow"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()

        async def mock_refresh(obj):
            obj.id = uuid4()
        db.refresh = mock_refresh

        return db

    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some source files
            src = Path(tmpdir) / "src"
            src.mkdir()
            (src / "main.py").write_text("print('hello')")
            (src / "service.py").write_text("class Service: pass")
            yield tmpdir

    @pytest.mark.asyncio
    async def test_start_assessment_creates_record(self, mock_db, temp_project):
        """Test that start_assessment creates database record"""
        orchestrator = ProjectAssessmentOrchestrator(mock_db)

        assessment = await orchestrator.start_assessment(
            project_name="TestProject",
            directory_path=temp_project
        )

        assert assessment.project_name == "TestProject"
        assert assessment.directory_path == temp_project
        assert assessment.status == "running"
        assert assessment.current_phase == "registration"
        assert assessment.progress_percent == 0
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_assessment_with_app_id(self, mock_db, temp_project):
        """Test start_assessment with application_id"""
        orchestrator = ProjectAssessmentOrchestrator(mock_db)

        assessment = await orchestrator.start_assessment(
            project_name="TestProject",
            directory_path=temp_project,
            application_id=123
        )

        assert assessment.application_id == 123

    @pytest.mark.asyncio
    async def test_start_assessment_invalid_path_raises(self, mock_db):
        """Test that invalid path raises ValueError"""
        orchestrator = ProjectAssessmentOrchestrator(mock_db)

        with pytest.raises(ValueError) as exc_info:
            await orchestrator.start_assessment(
                project_name="TestProject",
                directory_path="/nonexistent/path/xyz123"
            )

        assert "does not exist" in str(exc_info.value)


class TestPhaseResults:
    """Test PhaseResult dataclass"""

    def test_phase_result_success(self):
        """Test successful phase result"""
        result = PhaseResult(
            success=True,
            phase_name="registration",
            data={"files": 10},
            duration_seconds=5,
            items_processed=10,
            items_found=3
        )

        assert result.success == True
        assert result.phase_name == "registration"
        assert result.data == {"files": 10}
        assert result.error is None

    def test_phase_result_failure(self):
        """Test failed phase result"""
        result = PhaseResult(
            success=False,
            phase_name="security",
            data={},
            error="Security scan failed"
        )

        assert result.success == False
        assert result.error == "Security scan failed"


class TestRegistrationPhase:
    """Test registration phase execution"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with mocked db"""
        db = AsyncMock()
        return ProjectAssessmentOrchestrator(db)

    @pytest.fixture
    def temp_python_project(self):
        """Create temporary Python project"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Python project structure
            (Path(tmpdir) / "main.py").write_text("print('hello')")
            (Path(tmpdir) / "requirements.txt").write_text("fastapi\npydantic")

            services = Path(tmpdir) / "services"
            services.mkdir()
            (services / "user_service.py").write_text("class UserService: pass")

            tests = Path(tmpdir) / "tests"
            tests.mkdir()
            (tests / "test_user.py").write_text("def test_user(): pass")

            yield tmpdir

    @pytest.mark.asyncio
    async def test_registration_phase_detects_stack(self, orchestrator, temp_python_project):
        """Test that registration phase detects tech stack"""
        assessment = ProjectAssessment(
            project_name="TestPython",
            directory_path=temp_python_project
        )

        result = await orchestrator._run_registration_phase(assessment)

        assert result.success == True
        assert result.phase_name == "registration"
        assert "detected_stacks" in result.data
        assert result.items_processed >= 1

    @pytest.mark.asyncio
    async def test_registration_phase_counts_files(self, orchestrator, temp_python_project):
        """Test that registration counts files correctly"""
        assessment = ProjectAssessment(
            project_name="TestPython",
            directory_path=temp_python_project
        )

        result = await orchestrator._run_registration_phase(assessment)

        assert result.success == True
        assert "file_count" in result.data
        assert result.data["file_count"] >= 3  # main.py, requirements.txt, user_service.py, test_user.py


class TestASISPhase:
    """Test AS-IS architecture phase"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator"""
        db = AsyncMock()
        return ProjectAssessmentOrchestrator(db)

    @pytest.fixture
    def temp_layered_project(self):
        """Create temporary layered project"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # DDD-like structure
            dirs = ["domain", "application", "infrastructure", "presentation"]
            for d in dirs:
                path = Path(tmpdir) / d
                path.mkdir()
                (path / f"{d}_service.py").write_text("class Service: pass")
            yield tmpdir

    @pytest.mark.asyncio
    async def test_asis_phase_analyzes_architecture(self, orchestrator, temp_layered_project):
        """Test AS-IS phase analyzes architecture"""
        assessment = ProjectAssessment(
            project_name="LayeredProject",
            directory_path=temp_layered_project
        )

        result = await orchestrator._run_asis_phase(assessment)

        assert result.success == True
        assert result.phase_name == "as_is"
        assert "detected_pattern" in result.data
        assert "layers" in result.data

    @pytest.mark.asyncio
    async def test_asis_phase_updates_assessment(self, orchestrator, temp_layered_project):
        """Test AS-IS phase updates assessment object"""
        assessment = ProjectAssessment(
            project_name="LayeredProject",
            directory_path=temp_layered_project
        )

        await orchestrator._run_asis_phase(assessment)

        assert assessment.as_is_architecture is not None
        assert assessment.architecture_pattern is not None
        assert assessment.architecture_score is not None


class TestCodeAnalysisPhase:
    """Test code analysis phase"""

    @pytest.fixture
    def orchestrator(self):
        db = AsyncMock()
        return ProjectAssessmentOrchestrator(db)

    @pytest.fixture
    def temp_project_with_tests(self):
        """Create project with test files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Source files
            src = Path(tmpdir) / "src"
            src.mkdir()
            (src / "main.py").write_text("class Main: pass")
            (src / "service.py").write_text("class Service: pass")

            # Test files
            tests = Path(tmpdir) / "tests"
            tests.mkdir()
            (tests / "test_main.py").write_text("def test_main(): pass")
            (tests / "test_service.py").write_text("def test_service(): pass")

            yield tmpdir

    @pytest.mark.asyncio
    async def test_code_analysis_detects_tests(self, orchestrator, temp_project_with_tests):
        """Test code analysis detects test files"""
        assessment = ProjectAssessment(
            project_name="TestProject",
            directory_path=temp_project_with_tests,
            file_count=4
        )

        result = await orchestrator._run_code_analysis_phase(assessment)

        assert result.success == True
        assert result.items_found >= 2  # At least 2 test files


class TestSecurityPhase:
    """Test security analysis phase"""

    @pytest.fixture
    def orchestrator(self):
        db = AsyncMock()
        return ProjectAssessmentOrchestrator(db)

    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "main.py").write_text("import os\nos.system('ls')")
            yield tmpdir

    @pytest.mark.asyncio
    async def test_security_phase_runs(self, orchestrator, temp_project):
        """Test security phase executes successfully"""
        assessment = ProjectAssessment(
            project_name="TestProject",
            directory_path=temp_project,
            primary_stack="python",
            file_count=1
        )

        result = await orchestrator._run_security_phase(assessment)

        assert result.success == True
        assert result.phase_name == "security"
        # Should have a grade even with fallback
        assert "grade" in result.data


class TestQualityPhase:
    """Test quality analysis phase"""

    @pytest.fixture
    def orchestrator(self):
        db = AsyncMock()
        return ProjectAssessmentOrchestrator(db)

    @pytest.mark.asyncio
    async def test_quality_phase_calculates_score(self, orchestrator):
        """Test quality phase calculates quality score"""
        assessment = ProjectAssessment(
            project_name="TestProject",
            directory_path="/tmp",
            file_count=100,
            line_count=5000,
            architecture_score=75,
            architecture_issues=[
                {"severity": "medium", "title": "Test issue", "description": "Desc"}
            ]
        )

        result = await orchestrator._run_quality_phase(assessment)

        assert result.success == True
        assert "score" in result.data
        assert "grade" in result.data
        assert result.data["grade"] in ["A", "B", "C", "D", "F"]

    @pytest.mark.asyncio
    async def test_quality_phase_estimates_tech_debt(self, orchestrator):
        """Test tech debt estimation based on issues"""
        assessment = ProjectAssessment(
            project_name="TestProject",
            directory_path="/tmp",
            file_count=100,
            line_count=5000,
            architecture_score=50,
            architecture_issues=[
                {"severity": "critical", "title": "Issue 1", "description": "Critical"},
                {"severity": "high", "title": "Issue 2", "description": "High"},
                {"severity": "medium", "title": "Issue 3", "description": "Medium"},
            ]
        )

        result = await orchestrator._run_quality_phase(assessment)

        # Critical = 40h, High = 16h, Medium = 8h = 64h total
        assert result.data["tech_debt_hours"] == 64


class TestReportPhase:
    """Test report generation phase"""

    @pytest.fixture
    def orchestrator(self):
        db = AsyncMock()
        return ProjectAssessmentOrchestrator(db)

    @pytest.mark.asyncio
    async def test_report_phase_generates_summary(self, orchestrator):
        """Test report phase generates markdown summary"""
        assessment = ProjectAssessment(
            project_name="TestProject",
            directory_path="/tmp",
            primary_stack="python",
            file_count=100,
            line_count=5000,
            architecture_pattern="layered",
            architecture_score=70,
            architecture_layers=[],
            security_grade="B",
            security_finding_count=5,
            security_critical_count=0,
            security_high_count=1,
            security_medium_count=2,
            security_low_count=2,
            quality_grade="B",
            quality_score=75,
            tech_debt_hours=20,
            maintainability_index=80
        )

        result = await orchestrator._run_report_phase(assessment)

        assert result.success == True
        assert "summary" in result.data
        assert "Project Health Report" in result.data["summary"]
        assert "TestProject" in result.data["summary"]

    @pytest.mark.asyncio
    async def test_report_phase_identifies_blockers(self, orchestrator):
        """Test report phase identifies migration blockers"""
        assessment = ProjectAssessment(
            project_name="BlockedProject",
            directory_path="/tmp",
            primary_stack="python",
            file_count=100,
            line_count=5000,
            architecture_pattern="monolith",
            architecture_score=20,  # Very low - should be a blocker
            architecture_layers=[],
            security_grade="F",
            security_finding_count=20,
            security_critical_count=10,  # Many criticals - should be a blocker
            security_high_count=5,
            security_medium_count=3,
            security_low_count=2,
            quality_grade="D",
            quality_score=40,
            tech_debt_hours=200,
            maintainability_index=30
        )

        result = await orchestrator._run_report_phase(assessment)

        assert "blockers" in result.data
        assert len(result.data["blockers"]) >= 2  # Security + architecture blockers


class TestScoreCalculation:
    """Test overall score calculation"""

    @pytest.fixture
    def orchestrator(self):
        db = AsyncMock()
        return ProjectAssessmentOrchestrator(db)

    @pytest.mark.asyncio
    async def test_calculate_overall_scores(self, orchestrator):
        """Test weighted score calculation"""
        assessment = ProjectAssessment(
            project_name="TestProject",
            directory_path="/tmp",
            architecture_score=80,  # 30% weight
            security_risk_score=20,  # 35% weight (inverse: 80)
            quality_score=70  # 35% weight
        )

        await orchestrator._calculate_overall_scores(assessment)

        # Expected: (80 * 0.30) + (80 * 0.35) + (70 * 0.35) = 24 + 28 + 24.5 = 76.5
        assert assessment.overall_health_score == 76
        assert assessment.overall_grade == "B"

    @pytest.mark.asyncio
    async def test_grade_assignment(self, orchestrator):
        """Test grade assignment based on score"""
        test_cases = [
            (95, "A"),
            (85, "B"),
            (65, "C"),
            (45, "D"),
            (30, "F"),
        ]

        for score, expected_grade in test_cases:
            assessment = ProjectAssessment(
                project_name="TestProject",
                directory_path="/tmp",
                architecture_score=score,
                security_risk_score=100 - score,
                quality_score=score
            )

            await orchestrator._calculate_overall_scores(assessment)

            assert assessment.overall_grade == expected_grade, f"Score {score} should give grade {expected_grade}"


class TestAgentMapping:
    """Test agent mapping for phases"""

    @pytest.fixture
    def orchestrator(self):
        db = AsyncMock()
        return ProjectAssessmentOrchestrator(db)

    def test_agent_mapping(self, orchestrator):
        """Test correct agent is assigned to each phase"""
        expected_agents = {
            "registration": "system",
            "as_is": "miguel",
            "code": "coderag",
            "security": "quinn",
            "quality": "quinn",
            "report": "diana"
        }

        for phase, expected_agent in expected_agents.items():
            agent = orchestrator._get_agent_for_phase(phase)
            assert agent == expected_agent, f"Phase {phase} should use agent {expected_agent}"

    def test_unknown_phase_returns_unknown(self, orchestrator):
        """Test unknown phase returns 'unknown'"""
        agent = orchestrator._get_agent_for_phase("nonexistent")
        assert agent == "unknown"


class TestAssessmentStatus:
    """Test assessment status retrieval"""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_get_assessment_status_found(self, mock_db):
        """Test getting status of existing assessment"""
        assessment_id = uuid4()
        assessment = ProjectAssessment(
            id=assessment_id,
            project_name="TestProject",
            directory_path="/tmp",
            status="running",
            current_phase="security",
            progress_percent=66,
            started_at=datetime.now(timezone.utc)
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = assessment
        mock_db.execute = AsyncMock(return_value=mock_result)

        orchestrator = ProjectAssessmentOrchestrator(mock_db)
        status = await orchestrator.get_assessment_status(assessment_id)

        assert status["project_name"] == "TestProject"
        assert status["status"] == "running"
        assert status["current_phase"] == "security"
        assert status["progress_percent"] == 66

    @pytest.mark.asyncio
    async def test_get_assessment_status_not_found(self, mock_db):
        """Test getting status of nonexistent assessment"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        orchestrator = ProjectAssessmentOrchestrator(mock_db)
        status = await orchestrator.get_assessment_status(uuid4())

        assert "error" in status


class TestFullWorkflow:
    """Test complete assessment workflow"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database with full behavior"""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()

        assessment_id = uuid4()

        async def mock_refresh(obj):
            obj.id = assessment_id
        db.refresh = mock_refresh

        return db

    @pytest.fixture
    def temp_complete_project(self):
        """Create a complete project structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create DDD structure
            for layer in ["domain", "application", "infrastructure", "presentation"]:
                path = Path(tmpdir) / layer
                path.mkdir()
                (path / "__init__.py").write_text("")
                (path / f"{layer}_service.py").write_text(f"class {layer.title()}Service: pass")

            # Tests
            tests = Path(tmpdir) / "tests"
            tests.mkdir()
            (tests / "test_domain.py").write_text("def test_domain(): pass")

            # Config files
            (Path(tmpdir) / "requirements.txt").write_text("fastapi\npydantic")
            (Path(tmpdir) / "pyproject.toml").write_text("[tool.pytest]\n")

            yield tmpdir

    @pytest.mark.asyncio
    async def test_start_and_run_assessment(self, mock_db, temp_complete_project):
        """Test starting and running a complete assessment"""
        # Setup mock for run_assessment
        assessment = ProjectAssessment(
            project_name="CompleteProject",
            directory_path=temp_complete_project,
            status="running",
            current_phase="registration",
            progress_percent=0,
            started_at=datetime.now(timezone.utc)
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = assessment
        mock_db.execute = AsyncMock(return_value=mock_result)

        orchestrator = ProjectAssessmentOrchestrator(mock_db)

        # Start assessment
        started = await orchestrator.start_assessment(
            project_name="CompleteProject",
            directory_path=temp_complete_project
        )

        assert started.status == "running"

        # Run assessment (uses mock db that returns the same assessment)
        completed = await orchestrator.run_assessment(started.id)

        # Should complete successfully
        assert completed.status == "completed"
        assert completed.progress_percent == 100


class TestConvenienceFunction:
    """Test convenience function"""

    @pytest.mark.asyncio
    async def test_run_project_assessment_function(self):
        """Test the run_project_assessment convenience function"""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "main.py").write_text("print('hello')")

            # Create mock db
            mock_db = AsyncMock()
            mock_db.add = MagicMock()
            mock_db.commit = AsyncMock()

            assessment_id = uuid4()
            assessment = ProjectAssessment(
                id=assessment_id,
                project_name="TestProject",
                directory_path=tmpdir,
                status="running",
                current_phase="registration",
                progress_percent=0,
                started_at=datetime.now(timezone.utc)
            )

            async def mock_refresh(obj):
                obj.id = assessment_id
            mock_db.refresh = mock_refresh

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = assessment
            mock_db.execute = AsyncMock(return_value=mock_result)

            # Run convenience function
            result = await run_project_assessment(
                db=mock_db,
                project_name="TestProject",
                directory_path=tmpdir,
                use_llm=False
            )

            assert result.status == "completed"
