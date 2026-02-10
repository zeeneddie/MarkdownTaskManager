"""
Tests for OnboardingOrchestrator Module 1: Input Validation.

Test Protocol:
- Each module is tested on all 3 reference projects before proceeding
- Tests must pass on: hci-crs, FRM, FysioOne-Classic
- Criteria: No errors, valid output, acceptable performance

Reference projects:
- /opt/projecten/hci-crs (9,922 files, 560MB)
- /opt/projecten/paramedi/FRM (6,710 files, 191MB)
- /opt/projecten/paramedi/FysioOne-Classic (2,235 files, 100MB)
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from app.confucius.workflows.onboarding import (
    OnboardingOrchestrator,
    ONBOARDING_QUESTIONS,
    OnboardingValidationResult,
    get_onboarding_orchestrator,
)
from app.confucius.workflows.base import (
    WorkflowContext,
    WorkflowStatus,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def orchestrator():
    """Create OnboardingOrchestrator instance."""
    return get_onboarding_orchestrator()


@pytest.fixture
def valid_answers():
    """Valid answers for all 5 onboarding questions."""
    return {
        "q1_primary_purpose": (
            "Dit is een healthcare registratie systeem voor het beheren van "
            "patientgegevens en afspraken in ziekenhuizen en klinieken."
        ),
        "q2_users": (
            "Administratief personeel, artsen, verpleegkundigen en patienten "
            "via het patient portaal."
        ),
        "q3_critical_processes": (
            "Patient registratie, afspraak planning, facturatie en declaratie "
            "naar verzekeraars. Deze processen mogen nooit data verliezen."
        ),
        "q4_integrations": (
            "HL7 FHIR voor patient data, Vecozo voor declaraties, "
            "email gateway voor notificaties."
        ),
        "q5_pain_points": (
            "Legacy ASP.NET codebase met veel technische schuld, "
            "trage database queries, geen unit tests."
        ),
    }


@pytest.fixture
def partial_answers():
    """Only required questions answered, optional q5 missing."""
    return {
        "q1_primary_purpose": (
            "Dit is een healthcare registratie systeem voor het beheren van "
            "patientgegevens en afspraken in ziekenhuizen en klinieken."
        ),
        "q2_users": "Administratief personeel en artsen",
        "q3_critical_processes": (
            "Patient registratie en afspraak planning. "
            "Deze processen mogen nooit data verliezen."
        ),
        "q4_integrations": "HL7 FHIR en Vecozo",
        # q5_pain_points is optional, not provided
    }


# =============================================================================
# MODULE 1: INPUT VALIDATION TESTS
# =============================================================================

class TestOnboardingOrchestratorM1:
    """Tests for Module 1: Input Validation."""

    def test_workflow_type(self, orchestrator):
        """Test that workflow type is correct."""
        assert orchestrator.workflow_type == "onboarding"

    def test_get_stages_m1_only(self, orchestrator):
        """Test that only M1 stage is defined."""
        stages = orchestrator.get_stages()
        assert len(stages) == 1
        assert stages[0].name == "validate_input"
        assert stages[0].quality_threshold == 1.0
        assert stages[0].max_iterations == 1

    def test_questions_defined(self):
        """Test that 5 onboarding questions are defined."""
        assert len(ONBOARDING_QUESTIONS) == 5

        # Check required fields
        for q in ONBOARDING_QUESTIONS:
            assert "id" in q
            assert "question" in q
            assert "required" in q
            assert "min_length" in q

        # Check that first 4 are required, 5th is optional
        required_count = sum(1 for q in ONBOARDING_QUESTIONS if q["required"])
        assert required_count == 4

    @pytest.mark.asyncio
    async def test_valid_input_passes(self, orchestrator, valid_answers, tmp_path):
        """Test that valid input passes validation with score 1.0."""
        # Create a temp directory to simulate project
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        context = WorkflowContext(
            workflow_id="test-001",
            session_id="session-001",
            shared_data={
                "project_path": str(project_dir),
                "answers": valid_answers,
            },
        )

        stage = orchestrator.get_stages()[0]
        result = await orchestrator.execute_stage(stage, context)

        assert result.status == WorkflowStatus.COMPLETED
        assert result.quality_score == 1.0
        assert result.passed_quality_gate is True
        assert result.agent_results["valid"] is True
        assert result.agent_results["answers_count"] == 5

    @pytest.mark.asyncio
    async def test_partial_answers_passes(self, orchestrator, partial_answers, tmp_path):
        """Test that partial answers (only required) still passes."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        context = WorkflowContext(
            workflow_id="test-002",
            session_id="session-002",
            shared_data={
                "project_path": str(project_dir),
                "answers": partial_answers,
            },
        )

        stage = orchestrator.get_stages()[0]
        result = await orchestrator.execute_stage(stage, context)

        assert result.status == WorkflowStatus.COMPLETED
        assert result.quality_score == 1.0
        assert result.passed_quality_gate is True

    @pytest.mark.asyncio
    async def test_missing_required_fails(self, orchestrator, tmp_path):
        """Test that missing required answers fails validation."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        incomplete_answers = {
            "q1_primary_purpose": "Valid answer that is long enough for validation",
            # Missing q2, q3, q4
        }

        context = WorkflowContext(
            workflow_id="test-003",
            session_id="session-003",
            shared_data={
                "project_path": str(project_dir),
                "answers": incomplete_answers,
            },
        )

        stage = orchestrator.get_stages()[0]
        result = await orchestrator.execute_stage(stage, context)

        assert result.status == WorkflowStatus.FAILED
        assert result.quality_score == 0.0
        assert result.passed_quality_gate is False
        assert len(result.agent_results["missing_required"]) == 3

    @pytest.mark.asyncio
    async def test_missing_project_path_fails(self, orchestrator, valid_answers):
        """Test that missing project_path fails validation."""
        context = WorkflowContext(
            workflow_id="test-004",
            session_id="session-004",
            shared_data={
                # No project_path
                "answers": valid_answers,
            },
        )

        stage = orchestrator.get_stages()[0]
        result = await orchestrator.execute_stage(stage, context)

        assert result.status == WorkflowStatus.FAILED
        assert result.quality_score == 0.0
        assert "project_path is required" in result.agent_results["validation_errors"]

    @pytest.mark.asyncio
    async def test_nonexistent_path_fails(self, orchestrator, valid_answers):
        """Test that nonexistent project_path fails validation."""
        context = WorkflowContext(
            workflow_id="test-005",
            session_id="session-005",
            shared_data={
                "project_path": "/nonexistent/path/that/does/not/exist",
                "answers": valid_answers,
            },
        )

        stage = orchestrator.get_stages()[0]
        result = await orchestrator.execute_stage(stage, context)

        assert result.status == WorkflowStatus.FAILED
        assert result.quality_score == 0.0
        assert any("does not exist" in e for e in result.agent_results["validation_errors"])

    @pytest.mark.asyncio
    async def test_answer_too_short_fails(self, orchestrator, tmp_path):
        """Test that answers below min_length fail validation."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        short_answers = {
            "q1_primary_purpose": "Too short",  # Needs 50 chars
            "q2_users": "OK length for this question",
            "q3_critical_processes": "Also too short",  # Needs 50 chars
            "q4_integrations": "API integration",
        }

        context = WorkflowContext(
            workflow_id="test-006",
            session_id="session-006",
            shared_data={
                "project_path": str(project_dir),
                "answers": short_answers,
            },
        )

        stage = orchestrator.get_stages()[0]
        result = await orchestrator.execute_stage(stage, context)

        assert result.status == WorkflowStatus.FAILED
        assert result.quality_score == 0.0
        # Should have errors for q1 and q3 being too short
        errors = result.agent_results["validation_errors"]
        assert any("q1_primary_purpose" in e for e in errors)
        assert any("q3_critical_processes" in e for e in errors)


# =============================================================================
# REFERENCE PROJECT TESTS
# =============================================================================

class TestOnboardingReferenceProjects:
    """
    Tests against the 3 reference projects.

    These tests validate that the workflow can accept real project paths.
    They only test input validation (M1), not actual code analysis.
    """

    REFERENCE_PROJECTS = [
        "/opt/projecten/hci-crs",
        "/opt/projecten/paramedi/FRM",
        "/opt/projecten/paramedi/FysioOne-Classic",
    ]

    @pytest.fixture
    def sample_answers_hci_crs(self):
        """Sample answers for hci-crs project."""
        return {
            "q1_primary_purpose": (
                "HCI-CRS is een healthcare registratie systeem voor het beheren van "
                "patientgegevens, afspraken en declaraties in ziekenhuizen."
            ),
            "q2_users": (
                "Administratief personeel, artsen, verpleegkundigen"
            ),
            "q3_critical_processes": (
                "Patient registratie, afspraakplanning, facturatie, "
                "declaratie naar verzekeraars via Vecozo."
            ),
            "q4_integrations": "HL7 FHIR, Vecozo, LDAP",
            "q5_pain_points": "Legacy .NET Framework, stored procedures",
        }

    @pytest.fixture
    def sample_answers_frm(self):
        """Sample answers for FRM project."""
        return {
            "q1_primary_purpose": (
                "FRM is een fysio-registratie en management systeem voor "
                "fysiotherapie praktijken en paramedische zorg."
            ),
            "q2_users": "Fysiotherapeuten, praktijkhouders, patienten",
            "q3_critical_processes": (
                "Behandelregistratie, declaratie via Vecozo, "
                "agendabeheer en patientdossiers."
            ),
            "q4_integrations": "Vecozo declaraties, email",
            "q5_pain_points": "Oude WinForms UI, monolithische structuur",
        }

    @pytest.fixture
    def sample_answers_fysioone(self):
        """Sample answers for FysioOne-Classic project."""
        return {
            "q1_primary_purpose": (
                "FysioOne-Classic is de oorspronkelijke versie van het "
                "fysiotherapie praktijkbeheer systeem."
            ),
            "q2_users": "Fysiotherapeuten en administratie",
            "q3_critical_processes": (
                "Patientbeheer, behandelregistratie, "
                "en basis declaratieverwerking."
            ),
            "q4_integrations": "Database, lokale bestanden",
            "q5_pain_points": "Verouderde technologie stack",
        }

    @pytest.mark.asyncio
    @pytest.mark.parametrize("project_path", REFERENCE_PROJECTS)
    async def test_reference_project_path_validation(
        self,
        orchestrator,
        project_path,
        sample_answers_hci_crs,
    ):
        """Test that reference project paths are accepted as valid."""
        project = Path(project_path)
        if not project.exists():
            pytest.skip(f"Reference project not available: {project_path}")

        context = WorkflowContext(
            workflow_id=f"ref-{project.name}",
            session_id=f"session-{project.name}",
            shared_data={
                "project_path": str(project),
                "answers": sample_answers_hci_crs,
            },
        )

        stage = orchestrator.get_stages()[0]
        result = await orchestrator.execute_stage(stage, context)

        assert result.status == WorkflowStatus.COMPLETED, (
            f"Validation failed for {project_path}: "
            f"{result.agent_results.get('validation_errors', [])}"
        )
        assert result.quality_score == 1.0
        assert result.passed_quality_gate is True

    @pytest.mark.asyncio
    async def test_hci_crs_full_validation(
        self,
        orchestrator,
        sample_answers_hci_crs,
    ):
        """Full validation test for hci-crs with project-specific answers."""
        project_path = "/opt/projecten/hci-crs"
        if not Path(project_path).exists():
            pytest.skip("hci-crs project not available")

        context = WorkflowContext(
            workflow_id="hci-crs-full",
            session_id="session-hci-crs",
            shared_data={
                "project_path": project_path,
                "answers": sample_answers_hci_crs,
            },
        )

        stage = orchestrator.get_stages()[0]
        result = await orchestrator.execute_stage(stage, context)

        assert result.status == WorkflowStatus.COMPLETED
        assert result.agent_results["valid"] is True
        assert result.agent_results["answers_count"] == 5

    @pytest.mark.asyncio
    async def test_frm_full_validation(
        self,
        orchestrator,
        sample_answers_frm,
    ):
        """Full validation test for FRM with project-specific answers."""
        project_path = "/opt/projecten/paramedi/FRM"
        if not Path(project_path).exists():
            pytest.skip("FRM project not available")

        context = WorkflowContext(
            workflow_id="frm-full",
            session_id="session-frm",
            shared_data={
                "project_path": project_path,
                "answers": sample_answers_frm,
            },
        )

        stage = orchestrator.get_stages()[0]
        result = await orchestrator.execute_stage(stage, context)

        assert result.status == WorkflowStatus.COMPLETED
        assert result.agent_results["valid"] is True

    @pytest.mark.asyncio
    async def test_fysioone_full_validation(
        self,
        orchestrator,
        sample_answers_fysioone,
    ):
        """Full validation test for FysioOne-Classic with project-specific answers."""
        project_path = "/opt/projecten/paramedi/FysioOne-Classic"
        if not Path(project_path).exists():
            pytest.skip("FysioOne-Classic project not available")

        context = WorkflowContext(
            workflow_id="fysioone-full",
            session_id="session-fysioone",
            shared_data={
                "project_path": project_path,
                "answers": sample_answers_fysioone,
            },
        )

        stage = orchestrator.get_stages()[0]
        result = await orchestrator.execute_stage(stage, context)

        assert result.status == WorkflowStatus.COMPLETED
        assert result.agent_results["valid"] is True


# =============================================================================
# VALIDATION RESULT TESTS
# =============================================================================

class TestOnboardingValidationResult:
    """Tests for OnboardingValidationResult dataclass."""

    def test_quality_score_valid(self):
        """Test quality score is 1.0 when valid."""
        result = OnboardingValidationResult(
            valid=True,
            answers_count=5,
            questions_total=5,
            missing_required=[],
            validation_errors=[],
        )
        assert result.quality_score == 1.0

    def test_quality_score_invalid(self):
        """Test quality score is 0.0 when missing required."""
        result = OnboardingValidationResult(
            valid=False,
            answers_count=2,
            questions_total=5,
            missing_required=["q2_users", "q3_critical_processes"],
            validation_errors=["Missing q2", "Missing q3"],
        )
        assert result.quality_score == 0.0

    def test_to_dict(self):
        """Test to_dict serialization."""
        result = OnboardingValidationResult(
            valid=True,
            answers_count=4,
            questions_total=5,
            missing_required=[],
            validation_errors=[],
        )
        d = result.to_dict()
        assert d["valid"] is True
        assert d["answers_count"] == 4
        assert d["quality_score"] == 1.0
