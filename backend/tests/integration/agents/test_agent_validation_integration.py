"""
Week 50 Day 5: Agent Validation Loop Integration Tests

Tests for the complete agent validation pipeline:
- Quality gate blocking behavior
- Workflow-specific validation phases
- Iteration logic and fix suggestions
- API endpoint integration

Author: Claude Code (Week 50 Day 5)
Date: 2025-11-24
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.database import get_db
from app.services.agent_validation_loop_service import (
    AgentValidationLoopService,
    LoopStatus,
    ValidationLoopResult,
    FixSuggestion,
    FixSuggestionGenerator
)
from app.services.quality_gate_integration_service import (
    QualityGateIntegrationService,
    QualityGateResult,
    WORK_TYPE_PHASES
)
from app.services.validation_pipeline_service import (
    ValidationPipelineService,
    ValidationResult,
    ValidationPhaseResult,
    ValidationPhase,
    ValidationError,
    ValidationConfig,
    Language
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
async def client(mock_db):
    """Create async test client with mocked database."""
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing."""
    return '''
def hello_world():
    """Say hello."""
    print("Hello, World!")
    return True
'''


@pytest.fixture
def sample_code_with_errors():
    """Sample code with intentional errors."""
    return '''
def broken_function()
    x = undefined_variable
    return x
'''


# ============================================================================
# API ENDPOINT INTEGRATION TESTS
# ============================================================================

class TestAgentValidationAPI:
    """Integration tests for agent validation API endpoints."""

    @pytest.mark.asyncio
    async def test_quick_validate_endpoint_success(self, client, mock_db):
        """POST /api/agent/validate/quick should return validation result."""
        with patch('app.api.agent_validation.AgentValidationLoopService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.get_validation_status = AsyncMock(return_value={
                "passed": True,
                "workflow_type": "BUG",
                "blocking_count": 0,
                "warning_count": 0,
                "coverage_met": True,
                "suggestions": []
            })

            response = await client.post(
                "/api/agent/validate/quick",
                json={
                    "workflow_type": "BUG",
                    "code": "def fix(): return True",
                    "language": "python"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "passed" in data
            assert "workflow_type" in data
            assert data["workflow_type"] == "BUG"
            assert "blocking_count" in data
            assert "suggestions" in data

    @pytest.mark.asyncio
    async def test_quick_validate_invalid_workflow_type(self, client):
        """Should reject invalid workflow types."""
        response = await client.post(
            "/api/agent/validate/quick",
            json={
                "workflow_type": "INVALID_TYPE",
                "code": "def x(): pass",
                "language": "python"
            }
        )

        assert response.status_code == 400
        assert "Invalid workflow type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_loop_endpoint_returns_result(self, client, mock_db):
        """POST /api/agent/validate/loop should return complete result."""
        with patch('app.api.agent_validation.AgentValidationLoopService') as MockService:
            mock_instance = MockService.return_value
            mock_result = ValidationLoopResult(
                status=LoopStatus.PASSED,
                workflow_type="HOTFIX",
                total_iterations=1,
                max_iterations=1,
                final_code="def quick_fix(): return True",
                final_validation=ValidationResult(
                    success=True, phases=[], total_duration=0.05,
                    total_errors=0, total_warnings=0, coverage_percent=None,
                    iterations=1, final_code="def quick_fix(): return True"
                ),
                final_gate_result=None,
                attempts=[],
                total_errors_fixed=0,
                duration_seconds=0.5
            )
            mock_instance.run_validation_loop = AsyncMock(return_value=mock_result)

            response = await client.post(
                "/api/agent/validate/loop",
                json={
                    "workflow_type": "HOTFIX",
                    "code": "def quick_fix(): return True",
                    "language": "python",
                    "max_iterations": 1
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
            assert "status" in data
            assert "total_iterations" in data
            assert "max_iterations" in data
            assert data["max_iterations"] == 1
            assert "passed" in data
            assert "duration_seconds" in data

    @pytest.mark.asyncio
    async def test_loop_respects_max_iterations(self, client, mock_db):
        """Validation loop should respect max_iterations parameter."""
        with patch('app.api.agent_validation.AgentValidationLoopService') as MockService:
            mock_instance = MockService.return_value
            mock_result = ValidationLoopResult(
                status=LoopStatus.MAX_ITERATIONS,
                workflow_type="NEW_FEATURE",
                total_iterations=2,
                max_iterations=2,
                final_code="def feature(): pass",
                final_validation=None,
                final_gate_result=None,
                attempts=[],
                total_errors_fixed=0,
                duration_seconds=1.0
            )
            mock_instance.run_validation_loop = AsyncMock(return_value=mock_result)

            response = await client.post(
                "/api/agent/validate/loop",
                json={
                    "workflow_type": "NEW_FEATURE",
                    "code": "def feature(): pass",
                    "language": "python",
                    "max_iterations": 2
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_iterations"] <= 2
            assert data["max_iterations"] == 2

    @pytest.mark.asyncio
    async def test_workflow_types_endpoint(self, client):
        """GET /api/agent/validate/workflow-types should list all types."""
        response = await client.get("/api/agent/validate/workflow-types")

        assert response.status_code == 200
        data = response.json()
        assert "workflow_types" in data

        types = [wt["type"] for wt in data["workflow_types"]]
        assert "NEW_FEATURE" in types
        assert "BUG" in types
        assert "HOTFIX" in types
        assert "MAINTENANCE" in types

    @pytest.mark.asyncio
    async def test_typescript_language_support(self, client, mock_db):
        """Should support TypeScript language."""
        with patch('app.api.agent_validation.AgentValidationLoopService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.get_validation_status = AsyncMock(return_value={
                "passed": True,
                "workflow_type": "NEW_FEATURE",
                "blocking_count": 0,
                "warning_count": 0,
                "coverage_met": True,
                "suggestions": []
            })

            response = await client.post(
                "/api/agent/validate/quick",
                json={
                    "workflow_type": "NEW_FEATURE",
                    "code": "function hello(): string { return 'hello'; }",
                    "language": "typescript"
                }
            )

            assert response.status_code == 200


# ============================================================================
# QUALITY GATE BLOCKING TESTS
# ============================================================================

class TestQualityGateBlocking:
    """Tests for quality gate blocking behavior."""

    @pytest.mark.asyncio
    async def test_critical_errors_block_validation(self, mock_db):
        """Critical errors should block validation."""
        service = AgentValidationLoopService(mock_db)

        # Mock validation with critical error
        with patch.object(service, '_run_validation') as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=False,
                phases=[
                    ValidationPhaseResult(
                        phase=ValidationPhase.LINTING,
                        passed=False,
                        duration=0.1,
                        errors=[
                            ValidationError(
                                phase=ValidationPhase.LINTING,
                                file="test.py",
                                line=1,
                                column=None,
                                message="Syntax error: invalid syntax",
                                code=None,
                                severity="critical",
                                auto_fixable=False
                            )
                        ],
                        warnings=[],
                        fix_suggestions=[],
                        raw_output=""
                    )
                ],
                total_duration=0.1,
                total_errors=1,
                total_warnings=0,
                coverage_percent=None,
                iterations=1,
                final_code=None
            )

            with patch.object(service.gate_service, 'get_validation_config') as mock_config:
                mock_config.return_value = ValidationConfig(
                    phases=[ValidationPhase.LINTING],
                    max_iterations=3,
                    required_coverage=0
                )

                with patch.object(service.gate_service, 'evaluate_gate') as mock_gate:
                    mock_gate.return_value = QualityGateResult(
                        passed=False,
                        workflow_type="BUG",
                        blocking_issues=[{"message": "Critical error"}],
                        warnings=[],
                        coverage_met=True,
                        coverage_actual=0,
                        coverage_required=0,
                        validation_result=None,
                        gate_config={}
                    )

                    result = await service.run_validation_loop(
                        workflow_type="BUG",
                        initial_code="broken code",
                        language=Language.PYTHON,
                        max_iterations_override=1
                    )

                    assert result.status == LoopStatus.MAX_ITERATIONS
                    assert not result.final_gate_result.passed

    @pytest.mark.asyncio
    async def test_warnings_dont_block_validation(self, mock_db):
        """Warnings should not block validation if no blocking issues."""
        service = AgentValidationLoopService(mock_db)

        with patch.object(service, '_run_validation') as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=True,
                phases=[
                    ValidationPhaseResult(
                        phase=ValidationPhase.LINTING,
                        passed=True,
                        duration=0.05,
                        errors=[],
                        warnings=[],
                        fix_suggestions=[],
                        raw_output=""
                    )
                ],
                total_duration=0.05,
                total_errors=0,
                total_warnings=0,
                coverage_percent=None,
                iterations=1,
                final_code=None
            )

            with patch.object(service.gate_service, 'get_validation_config') as mock_config:
                mock_config.return_value = ValidationConfig(
                    phases=[ValidationPhase.LINTING],
                    max_iterations=3,
                    required_coverage=0
                )

                with patch.object(service.gate_service, 'evaluate_gate') as mock_gate:
                    mock_gate.return_value = QualityGateResult(
                        passed=True,
                        workflow_type="MAINTENANCE",
                        blocking_issues=[],
                        warnings=[{"message": "Style warning"}],
                        coverage_met=True,
                        coverage_actual=0,
                        coverage_required=0,
                        validation_result=None,
                        gate_config={}
                    )

                    result = await service.run_validation_loop(
                        workflow_type="MAINTENANCE",
                        initial_code="good code",
                        language=Language.PYTHON
                    )

                    assert result.status == LoopStatus.PASSED


# ============================================================================
# WORKFLOW-SPECIFIC TESTS
# ============================================================================

class TestWorkflowSpecificValidation:
    """Tests for workflow-specific validation behavior."""

    def test_new_feature_has_all_phases(self):
        """NEW_FEATURE should have all validation phases."""
        phases = WORK_TYPE_PHASES["NEW_FEATURE"]

        assert ValidationPhase.LINTING in phases
        assert ValidationPhase.TYPE_CHECK in phases
        assert ValidationPhase.STYLE in phases
        assert ValidationPhase.UNIT_TESTS in phases
        assert ValidationPhase.E2E_TESTS in phases

    def test_hotfix_has_minimal_phases(self):
        """HOTFIX should have quick validation phases."""
        phases = WORK_TYPE_PHASES["HOTFIX"]

        assert ValidationPhase.LINTING in phases
        assert ValidationPhase.UNIT_TESTS in phases
        # Should not require full style checks for hotfixes
        assert len(phases) < len(WORK_TYPE_PHASES["NEW_FEATURE"])

    def test_documentation_only_linting(self):
        """DOCUMENTATION should only require linting."""
        phases = WORK_TYPE_PHASES["DOCUMENTATION"]

        assert ValidationPhase.LINTING in phases
        assert len(phases) == 1

    def test_migration_requires_e2e(self):
        """MIGRATION should require E2E tests."""
        phases = WORK_TYPE_PHASES["MIGRATION"]

        assert ValidationPhase.E2E_TESTS in phases


# ============================================================================
# FIX SUGGESTION TESTS
# ============================================================================

class TestFixSuggestionGenerator:
    """Tests for fix suggestion generation."""

    def test_generates_suggestions_for_linting_errors(self):
        """Should generate suggestions for linting errors."""
        generator = FixSuggestionGenerator()

        errors = [
            ValidationError(
                phase=ValidationPhase.LINTING,
                file="test.py",
                line=10,
                column=None,
                message="undefined variable 'foo'",
                code=None,
                severity="error",
                auto_fixable=False
            )
        ]

        suggestions = generator.generate_suggestions(errors, ValidationPhase.LINTING)

        assert len(suggestions) == 1
        assert suggestions[0].phase == "linting"
        assert "undefined" in suggestions[0].error_message.lower()
        assert suggestions[0].suggestion is not None

    def test_generates_suggestions_for_type_errors(self):
        """Should generate suggestions for type check errors."""
        generator = FixSuggestionGenerator()

        errors = [
            ValidationError(
                phase=ValidationPhase.TYPE_CHECK,
                file="test.py",
                line=5,
                column=None,
                message="Type 'str' is not assignable to type 'int'",
                code=None,
                severity="error",
                auto_fixable=False
            )
        ]

        suggestions = generator.generate_suggestions(errors, ValidationPhase.TYPE_CHECK)

        assert len(suggestions) == 1
        assert suggestions[0].phase == "type_check"

    def test_handles_empty_errors(self):
        """Should handle empty error list."""
        generator = FixSuggestionGenerator()

        suggestions = generator.generate_suggestions([], ValidationPhase.LINTING)

        assert len(suggestions) == 0


# ============================================================================
# VALIDATION LOOP RESULT TESTS
# ============================================================================

class TestValidationLoopResult:
    """Tests for ValidationLoopResult dataclass."""

    def test_to_dict_returns_all_fields(self):
        """to_dict should return all necessary fields."""
        result = ValidationLoopResult(
            status=LoopStatus.PASSED,
            workflow_type="NEW_FEATURE",
            total_iterations=2,
            max_iterations=3,
            final_code="def x(): pass",
            final_validation=None,
            final_gate_result=None,
            attempts=[],
            total_errors_fixed=5,
            duration_seconds=1.5
        )

        d = result.to_dict()

        assert d["status"] == "passed"
        assert d["workflow_type"] == "NEW_FEATURE"
        assert d["total_iterations"] == 2
        assert d["max_iterations"] == 3
        assert d["passed"] is True
        assert d["total_errors_fixed"] == 5
        assert d["duration_seconds"] == 1.5

    def test_to_dict_handles_failed_status(self):
        """to_dict should correctly represent failed status."""
        result = ValidationLoopResult(
            status=LoopStatus.MAX_ITERATIONS,
            workflow_type="BUG",
            total_iterations=3,
            max_iterations=3,
            final_code=None,
            final_validation=None,
            final_gate_result=None,
            attempts=[],
            total_errors_fixed=0,
            duration_seconds=5.0
        )

        d = result.to_dict()

        assert d["status"] == "max_iterations"
        assert d["passed"] is False


# ============================================================================
# ITERATION BEHAVIOR TESTS
# ============================================================================

class TestIterationBehavior:
    """Tests for validation loop iteration behavior."""

    @pytest.mark.asyncio
    async def test_stops_on_first_success(self, mock_db):
        """Loop should stop when validation passes."""
        service = AgentValidationLoopService(mock_db)

        call_count = 0

        async def mock_run_validation(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return ValidationResult(
                success=True,
                phases=[],
                total_duration=0.05,
                total_errors=0,
                total_warnings=0,
                coverage_percent=None,
                iterations=1,
                final_code=None
            )

        with patch.object(service, '_run_validation', side_effect=mock_run_validation):
            with patch.object(service.gate_service, 'get_validation_config') as mock_config:
                mock_config.return_value = ValidationConfig(
                    phases=[],
                    max_iterations=5,
                    required_coverage=0
                )

                with patch.object(service.gate_service, 'evaluate_gate') as mock_gate:
                    mock_gate.return_value = QualityGateResult(
                        passed=True,
                        workflow_type="BUG",
                        blocking_issues=[],
                        warnings=[],
                        coverage_met=True,
                        coverage_actual=0,
                        coverage_required=0,
                        validation_result=None,
                        gate_config={}
                    )

                    result = await service.run_validation_loop(
                        workflow_type="BUG",
                        initial_code="code",
                        language=Language.PYTHON
                    )

                    assert result.status == LoopStatus.PASSED
                    assert result.total_iterations == 1
                    assert call_count == 1

    @pytest.mark.asyncio
    async def test_tracks_errors_fixed(self, mock_db):
        """Loop should track errors fixed across iterations."""
        service = AgentValidationLoopService(mock_db)

        iteration = 0

        async def mock_run_validation(*args, **kwargs):
            nonlocal iteration
            iteration += 1
            # First call: 3 errors, second call: 1 error
            error_count = 3 if iteration == 1 else 1
            return ValidationResult(
                success=False,
                phases=[
                    ValidationPhaseResult(
                        phase=ValidationPhase.LINTING,
                        passed=False,
                        duration=0.05,
                        errors=[
                            ValidationError(
                                phase=ValidationPhase.LINTING,
                                file="test.py",
                                line=i + 1,
                                column=None,
                                message=f"Error {i}",
                                code=None,
                                severity="error",
                                auto_fixable=False
                            )
                            for i in range(error_count)
                        ],
                        warnings=[],
                        fix_suggestions=[],
                        raw_output=""
                    )
                ],
                total_duration=0.05,
                total_errors=error_count,
                total_warnings=0,
                coverage_percent=None,
                iterations=1,
                final_code=None
            )

        with patch.object(service, '_run_validation', side_effect=mock_run_validation):
            with patch.object(service.gate_service, 'get_validation_config') as mock_config:
                mock_config.return_value = ValidationConfig(
                    phases=[ValidationPhase.LINTING],
                    max_iterations=2,
                    required_coverage=0
                )

                gate_call_count = 0

                def make_gate_result(*args, **kwargs):
                    nonlocal gate_call_count
                    gate_call_count += 1
                    # First call: 3 blocking issues, second call: 1 blocking issue
                    issue_count = 3 if gate_call_count == 1 else 1
                    return QualityGateResult(
                        passed=False,
                        workflow_type="BUG",
                        blocking_issues=[{"message": f"Error {i}"} for i in range(issue_count)],
                        warnings=[],
                        coverage_met=True,
                        coverage_actual=0,
                        coverage_required=0,
                        validation_result=None,
                        gate_config={}
                    )

                with patch.object(service.gate_service, 'evaluate_gate', side_effect=make_gate_result):
                    result = await service.run_validation_loop(
                        workflow_type="BUG",
                        initial_code="code",
                        language=Language.PYTHON
                    )

                    assert result.total_iterations == 2
                    # 3 errors -> 1 error = 2 fixed
                    assert result.total_errors_fixed == 2


# ============================================================================
# COVERAGE REQUIREMENT TESTS
# ============================================================================

class TestCoverageRequirements:
    """Tests for coverage requirement enforcement."""

    @pytest.mark.asyncio
    async def test_fails_when_coverage_not_met(self, mock_db):
        """Validation should fail if coverage requirement not met."""
        service = AgentValidationLoopService(mock_db)

        with patch.object(service, '_run_validation') as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=True,
                phases=[],
                total_duration=0.05,
                total_errors=0,
                total_warnings=0,
                coverage_percent=60,
                iterations=1,
                final_code=None
            )

            with patch.object(service.gate_service, 'get_validation_config') as mock_config:
                mock_config.return_value = ValidationConfig(
                    phases=[],
                    max_iterations=1,
                    required_coverage=80
                )

                with patch.object(service.gate_service, 'evaluate_gate') as mock_gate:
                    mock_gate.return_value = QualityGateResult(
                        passed=False,
                        workflow_type="NEW_FEATURE",
                        blocking_issues=[],
                        warnings=[],
                        coverage_met=False,
                        coverage_actual=60,
                        coverage_required=80,
                        validation_result=None,
                        gate_config={}
                    )

                    result = await service.run_validation_loop(
                        workflow_type="NEW_FEATURE",
                        initial_code="code",
                        language=Language.PYTHON
                    )

                    assert result.status == LoopStatus.MAX_ITERATIONS
                    assert not result.final_gate_result.coverage_met

    @pytest.mark.asyncio
    async def test_passes_when_coverage_met(self, mock_db):
        """Validation should pass if coverage requirement met."""
        service = AgentValidationLoopService(mock_db)

        with patch.object(service, '_run_validation') as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=True,
                phases=[],
                total_duration=0.05,
                total_errors=0,
                total_warnings=0,
                coverage_percent=85,
                iterations=1,
                final_code=None
            )

            with patch.object(service.gate_service, 'get_validation_config') as mock_config:
                mock_config.return_value = ValidationConfig(
                    phases=[],
                    max_iterations=1,
                    required_coverage=80
                )

                with patch.object(service.gate_service, 'evaluate_gate') as mock_gate:
                    mock_gate.return_value = QualityGateResult(
                        passed=True,
                        workflow_type="NEW_FEATURE",
                        blocking_issues=[],
                        warnings=[],
                        coverage_met=True,
                        coverage_actual=85,
                        coverage_required=80,
                        validation_result=None,
                        gate_config={}
                    )

                    result = await service.run_validation_loop(
                        workflow_type="NEW_FEATURE",
                        initial_code="code",
                        language=Language.PYTHON
                    )

                    assert result.status == LoopStatus.PASSED
                    assert result.final_gate_result.coverage_met
