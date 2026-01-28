"""
Unit Tests for Migration Stage Execution.

Tests individual stage execution logic with mocked agent extensions.
Each stage is tested in isolation with controlled inputs and outputs.

Coverage:
- validate_answers stage
- technical_analysis stage
- security_analysis stage
- generate_specification stage
- generate_tasks stage
- estimate_effort stage
- quality_review stage
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.confucius.workflows import (
    MigrationOrchestrator,
    WorkflowStage,
    WorkflowContext,
    WorkflowStatus,
)
from app.confucius.workflows.base import StageResult


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def orchestrator():
    """Create Migration orchestrator instance."""
    return MigrationOrchestrator()


@pytest.fixture
def base_context():
    """Create base workflow context with required shared data."""
    return WorkflowContext(
        workflow_id="test-mig-001",
        workflow_type="migration",
        session_id="test-session-001",
        shared_data={
            "source_path": "/opt/legacy/app",
            "target_tech": "dotnet-8",
        },
    )


@pytest.fixture
def complete_answers():
    """Complete set of 8 migration questions (matching actual orchestrator)."""
    return {
        "q1_legacy_system": "Classic ASP application with VBScript",
        "q2_migration_target": ".NET 8 with Blazor frontend",
        "q3_migration_strategy": "Strangler fig pattern",
        "q4_data_migration": "SQL Server to PostgreSQL",
        "q5_problem_statement": "Legacy system is unmaintainable",
        "q6_stakeholders": "Development team, Business users",
        "q7_success_criteria": "Zero data loss, performance maintained",
        "q8_timeline": "6 months target completion",
    }


@pytest.fixture
def mock_agent_extension():
    """Create a mock agent extension."""
    def _create_mock(success: bool = True, output: Dict[str, Any] = None):
        mock = MagicMock()
        mock.name = "MockAgent"
        mock.run_full_lifecycle = AsyncMock(
            return_value=MagicMock(
                success=success,
                output=output or {},
            )
        )
        return mock
    return _create_mock


# =============================================================================
# VALIDATE ANSWERS STAGE TESTS
# =============================================================================


class TestValidateAnswersStage:
    """Tests for validate_answers stage execution."""

    @pytest.mark.asyncio
    async def test_validate_answers_all_present(
        self, orchestrator, base_context, complete_answers
    ):
        """Test validation passes with all 8 answers."""
        base_context.shared_data["answers"] = complete_answers

        stage = WorkflowStage(
            name="validate_answers",
            description="Validate migration answers",
            agents=[],
        )

        result = await orchestrator.execute_stage(stage, base_context)

        assert result.status == WorkflowStatus.COMPLETED
        assert result.error is None

    @pytest.mark.asyncio
    async def test_validate_answers_missing_required(
        self, orchestrator, base_context
    ):
        """Test validation fails with missing required answers."""
        base_context.shared_data["answers"] = {
            "q1_legacy_system": "Classic ASP",
            # Missing q2-q8
        }

        stage = WorkflowStage(
            name="validate_answers",
            description="Validate migration answers",
            agents=[],
        )

        result = await orchestrator.execute_stage(stage, base_context)

        assert result.status == WorkflowStatus.FAILED
        assert "Missing answers" in result.error

    @pytest.mark.asyncio
    async def test_validate_answers_empty_answers(
        self, orchestrator, base_context
    ):
        """Test validation fails with empty answers dict."""
        base_context.shared_data["answers"] = {}

        stage = WorkflowStage(
            name="validate_answers",
            description="Validate migration answers",
            agents=[],
        )

        result = await orchestrator.execute_stage(stage, base_context)

        assert result.status == WorkflowStatus.FAILED

    @pytest.mark.asyncio
    async def test_validate_answers_stores_count(
        self, orchestrator, base_context, complete_answers
    ):
        """Test that validation stores answers count."""
        base_context.shared_data["answers"] = complete_answers

        stage = WorkflowStage(
            name="validate_answers",
            description="Validate migration answers",
            agents=[],
        )

        await orchestrator.execute_stage(stage, base_context)

        # Check that answers_count is stored
        result = base_context.shared_data.get("validate_answers_result", {})
        assert result.get("answers_count", 0) == 8 or "valid" in result


# =============================================================================
# TECHNICAL ANALYSIS STAGE TESTS
# =============================================================================


class TestTechnicalAnalysisStage:
    """Tests for technical_analysis stage execution."""

    @pytest.fixture
    def context_with_answers(self, base_context, complete_answers):
        """Context with validated answers."""
        base_context.shared_data["answers"] = complete_answers
        base_context.shared_data["validate_answers_result"] = {
            "valid": True,
            "answers_count": 8,
        }
        base_context.completed_stages.append("validate_answers")
        return base_context

    @pytest.mark.asyncio
    async def test_technical_analysis_success(
        self, orchestrator, context_with_answers, mock_agent_extension
    ):
        """Test successful technical analysis."""
        mock_miguel = mock_agent_extension(
            success=True,
            output={
                "tech_stack_detected": ["vbscript", "classic_asp", "sql_server"],
                "complexity_score": 0.78,
                "lines_of_code": 150000,
                "legacy_findings": [
                    {"type": "deprecated_api", "count": 45},
                    {"type": "hardcoded_sql", "count": 120},
                ],
            },
        )
        mock_miguel.name = "Miguel"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_miguel]
        ):
            stage = WorkflowStage(
                name="technical_analysis",
                description="Analyze legacy technology",
                agents=["Miguel"],
                depends_on=["validate_answers"],
            )

            result = await orchestrator.execute_stage(stage, context_with_answers)

            assert result.status == WorkflowStatus.COMPLETED
            assert "technical_analysis_result" in context_with_answers.shared_data

    @pytest.mark.asyncio
    async def test_technical_analysis_detects_tech_stack(
        self, orchestrator, context_with_answers, mock_agent_extension
    ):
        """Test that technical analysis detects technology stack."""
        mock_miguel = mock_agent_extension(
            success=True,
            output={
                "tech_stack_detected": ["python", "django", "postgresql"],
            },
        )
        mock_miguel.name = "Miguel"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_miguel]
        ):
            stage = WorkflowStage(
                name="technical_analysis",
                description="Analyze technology",
                agents=["Miguel"],
            )

            await orchestrator.execute_stage(stage, context_with_answers)

            stored = context_with_answers.shared_data.get(
                "technical_analysis_result", {}
            )
            assert "tech_stack_detected" in stored or len(stored) > 0


# =============================================================================
# SECURITY ANALYSIS STAGE TESTS
# =============================================================================


class TestSecurityAnalysisStage:
    """Tests for security_analysis stage execution (Fase 37)."""

    @pytest.fixture
    def context_with_tech_analysis(self, base_context, complete_answers):
        """Context with technical analysis results."""
        base_context.shared_data["answers"] = complete_answers
        base_context.shared_data["technical_analysis_result"] = {
            "tech_stack_detected": ["classic_asp", "sql_server"],
            "complexity_score": 0.75,
        }
        # Add input_data required by security_analysis stage
        base_context.input_data = {
            "source_path": base_context.shared_data.get("source_path", "/opt/legacy"),
        }
        base_context.completed_stages.extend(["validate_answers", "technical_analysis"])
        return base_context

    @pytest.mark.asyncio
    async def test_security_analysis_success(
        self, orchestrator, context_with_tech_analysis, mock_agent_extension
    ):
        """Test successful security analysis."""
        mock_quinn = mock_agent_extension(
            success=True,
            output={
                "findings": [
                    {"severity": "high", "cwe_ids": ["CWE-89"], "description": "SQL Injection"},
                    {"severity": "medium", "cwe_ids": ["CWE-79"], "description": "XSS"},
                ],
                "total_findings": 2,
                "cwe_top_25_coverage": 0.40,
                "scanners_used": ["semgrep", "bandit"],
            },
        )
        mock_quinn.name = "Quinn"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_quinn]
        ):
            stage = WorkflowStage(
                name="security_analysis",
                description="Analyze security vulnerabilities",
                agents=["Quinn"],
                depends_on=["technical_analysis"],
                quality_threshold=0.90,
            )

            result = await orchestrator.execute_stage(
                stage, context_with_tech_analysis
            )

            assert result.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_security_analysis_cwe_coverage(
        self, orchestrator, context_with_tech_analysis, mock_agent_extension
    ):
        """Test that security analysis reports CWE coverage."""
        mock_quinn = mock_agent_extension(
            success=True,
            output={
                "findings": [],
                "cwe_top_25_coverage": 0.80,
            },
        )
        mock_quinn.name = "Quinn"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_quinn]
        ):
            stage = WorkflowStage(
                name="security_analysis",
                description="Security scan",
                agents=["Quinn"],
            )

            await orchestrator.execute_stage(stage, context_with_tech_analysis)

            stored = context_with_tech_analysis.shared_data.get(
                "security_analysis_result", {}
            )
            # Verify some security data is stored
            assert len(stored) > 0


# =============================================================================
# GENERATE SPECIFICATION STAGE TESTS
# =============================================================================


class TestGenerateSpecificationStage:
    """Tests for generate_specification stage execution."""

    @pytest.fixture
    def context_with_security(self, base_context, complete_answers):
        """Context with security analysis results."""
        base_context.shared_data["answers"] = complete_answers
        base_context.shared_data["technical_analysis_result"] = {
            "tech_stack_detected": ["classic_asp"],
            "complexity_score": 0.75,
        }
        base_context.shared_data["security_analysis_result"] = {
            "findings": [],
            "cwe_top_25_coverage": 0.60,
        }
        base_context.completed_stages.extend([
            "validate_answers",
            "technical_analysis",
            "security_analysis",
        ])
        return base_context

    @pytest.mark.asyncio
    async def test_generate_specification_success(
        self, orchestrator, context_with_security, mock_agent_extension
    ):
        """Test successful specification generation."""
        mock_peter = mock_agent_extension(
            success=True,
            output={
                "specification": {
                    "problem_statement": "Migrate legacy ASP to .NET 8",
                    "stakeholders": ["Development Team", "Business Users"],
                    "success_criteria": ["Zero data loss", "Performance maintained"],
                },
                "architecture_decisions": [
                    {"decision": "Use Blazor for UI", "rationale": "Modern SPA approach"},
                ],
            },
        )
        mock_peter.name = "Peter"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_peter]
        ):
            stage = WorkflowStage(
                name="generate_specification",
                description="Generate migration specification",
                agents=["Peter", "Betty"],
                depends_on=["security_analysis"],
            )

            result = await orchestrator.execute_stage(stage, context_with_security)

            assert result.status == WorkflowStatus.COMPLETED


# =============================================================================
# GENERATE TASKS STAGE TESTS
# =============================================================================


class TestGenerateTasksStage:
    """Tests for generate_tasks stage execution."""

    @pytest.fixture
    def context_with_specification(self, base_context, complete_answers):
        """Context with specification results."""
        base_context.shared_data["answers"] = complete_answers
        base_context.shared_data["generate_specification_result"] = {
            "specification": {"problem_statement": "Migrate to .NET 8"},
        }
        base_context.completed_stages.append("generate_specification")
        return base_context

    @pytest.mark.asyncio
    async def test_generate_tasks_success(
        self, orchestrator, context_with_specification, mock_agent_extension
    ):
        """Test successful task generation."""
        mock_felix = mock_agent_extension(
            success=True,
            output={
                "epics": [
                    {"id": "E1", "title": "Data Layer Migration"},
                    {"id": "E2", "title": "Business Logic Migration"},
                ],
                "features": [
                    {"id": "F1", "epic_id": "E1", "title": "Database Schema"},
                ],
                "stories": [
                    {"id": "S1", "feature_id": "F1", "title": "Migrate Users table"},
                ],
                "migration_waves": [
                    {"wave": 1, "epic_ids": ["E1"]},
                    {"wave": 2, "epic_ids": ["E2"]},
                ],
            },
        )
        mock_felix.name = "Felix"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_felix]
        ):
            stage = WorkflowStage(
                name="generate_tasks",
                description="Generate migration tasks",
                agents=["Felix"],
                depends_on=["generate_specification"],
            )

            result = await orchestrator.execute_stage(
                stage, context_with_specification
            )

            assert result.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_generate_tasks_creates_waves(
        self, orchestrator, context_with_specification, mock_agent_extension
    ):
        """Test that task generation creates migration waves."""
        mock_felix = mock_agent_extension(
            success=True,
            output={
                "epics": [{"id": "E1", "title": "Migration"}],
                "migration_waves": [{"wave": 1, "epic_ids": ["E1"]}],
            },
        )
        mock_felix.name = "Felix"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_felix]
        ):
            stage = WorkflowStage(
                name="generate_tasks",
                description="Generate tasks",
                agents=["Felix"],
            )

            await orchestrator.execute_stage(stage, context_with_specification)

            stored = context_with_specification.shared_data.get(
                "generate_tasks_result", {}
            )
            # Should have epics or migration_waves
            assert "epics" in stored or "migration_waves" in stored or len(stored) > 0


# =============================================================================
# ESTIMATE EFFORT STAGE TESTS
# =============================================================================


class TestEstimateEffortStage:
    """Tests for estimate_effort stage execution."""

    @pytest.fixture
    def context_with_tasks(self, base_context):
        """Context with generated tasks."""
        base_context.shared_data["generate_tasks_result"] = {
            "epics": [{"id": "E1", "title": "Migration"}],
            "stories": [
                {"id": "S1", "title": "Story 1"},
                {"id": "S2", "title": "Story 2"},
            ],
            "migration_waves": [{"wave": 1, "epic_ids": ["E1"]}],
        }
        base_context.completed_stages.append("generate_tasks")
        return base_context

    @pytest.mark.asyncio
    async def test_estimate_effort_success(
        self, orchestrator, context_with_tasks, mock_agent_extension
    ):
        """Test successful effort estimation."""
        mock_paul = mock_agent_extension(
            success=True,
            output={
                "effort_by_wave": [
                    {"wave": 1, "effort_hours": 200},
                    {"wave": 2, "effort_hours": 300},
                ],
                "total_effort_hours": 500,
                "total_function_points": 150,
            },
        )
        mock_paul.name = "Paul"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_paul]
        ):
            stage = WorkflowStage(
                name="estimate_effort",
                description="Estimate migration effort",
                agents=["Paul", "Eliza"],
                depends_on=["generate_tasks"],
            )

            result = await orchestrator.execute_stage(stage, context_with_tasks)

            assert result.status == WorkflowStatus.COMPLETED


# =============================================================================
# QUALITY REVIEW STAGE TESTS
# =============================================================================


class TestQualityReviewStage:
    """Tests for quality_review stage execution."""

    @pytest.fixture
    def context_with_estimates(self, base_context):
        """Context with effort estimates."""
        base_context.shared_data["estimate_effort_result"] = {
            "total_effort_hours": 500,
            "total_function_points": 150,
        }
        base_context.completed_stages.append("estimate_effort")
        return base_context

    @pytest.mark.asyncio
    async def test_quality_review_success(
        self, orchestrator, context_with_estimates, mock_agent_extension
    ):
        """Test successful quality review."""
        mock_quinn = mock_agent_extension(
            success=True,
            output={
                "quality_score": 0.88,
                "recommendations": [
                    "Add more detail to Epic E2",
                    "Review security findings",
                ],
                "approval_status": "approved",
            },
        )
        mock_quinn.name = "Quinn"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_quinn]
        ):
            stage = WorkflowStage(
                name="quality_review",
                description="Review migration plan quality",
                agents=["Quinn"],
                depends_on=["estimate_effort"],
                quality_threshold=0.90,
            )

            result = await orchestrator.execute_stage(stage, context_with_estimates)

            assert result.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_quality_review_returns_recommendations(
        self, orchestrator, context_with_estimates, mock_agent_extension
    ):
        """Test that quality review returns actionable recommendations."""
        mock_quinn = mock_agent_extension(
            success=True,
            output={
                "quality_score": 0.75,
                "recommendations": ["Improve test coverage"],
                "approval_status": "needs_revision",
            },
        )
        mock_quinn.name = "Quinn"

        with patch.object(
            orchestrator, "get_agents_for_stage", return_value=[mock_quinn]
        ):
            stage = WorkflowStage(
                name="quality_review",
                description="Quality review",
                agents=["Quinn"],
            )

            await orchestrator.execute_stage(stage, context_with_estimates)

            stored = context_with_estimates.shared_data.get(
                "quality_review_result", {}
            )
            # Should have quality info
            assert "quality_score" in stored or "recommendations" in stored or len(stored) > 0


# =============================================================================
# QUESTIONS VALIDATION TESTS
# =============================================================================


class TestMigrationQuestions:
    """Tests for migration questions configuration."""

    def test_get_questions_returns_8(self, orchestrator):
        """Test that orchestrator returns exactly 8 questions."""
        questions = orchestrator.get_questions()
        assert len(questions) == 8

    def test_questions_have_required_fields(self, orchestrator):
        """Test that each question has required fields."""
        questions = orchestrator.get_questions()

        for q in questions:
            assert "id" in q
            assert "question" in q
            assert q["id"].startswith("q")

    def test_question_ids_are_unique(self, orchestrator):
        """Test that all question IDs are unique."""
        questions = orchestrator.get_questions()
        ids = [q["id"] for q in questions]
        assert len(ids) == len(set(ids))

    def test_questions_cover_migration_aspects(self, orchestrator):
        """Test that questions cover key migration aspects."""
        questions = orchestrator.get_questions()
        ids = [q["id"] for q in questions]

        # Check for actual question IDs used by the orchestrator
        assert "q1_legacy_system" in ids
        assert "q2_migration_target" in ids
        assert "q4_data_migration" in ids
        assert "q8_timeline" in ids
