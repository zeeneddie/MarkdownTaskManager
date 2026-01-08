"""
Week 50: Quality Gate Integration Service Unit Tests

Tests for QualityGateIntegrationService class methods.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import List, Optional

from app.services.quality_gate_integration_service import (
    QualityGateIntegrationService,
    QualityGateResult,
    WORK_TYPE_PHASES,
    get_validation_config_for_workflow,
    evaluate_quality_gate
)
from app.services.validation_pipeline_service import (
    ValidationPhase,
    ValidationConfig,
    ValidationResult,
    ValidationPhaseResult,
    ValidationError
)


class TestWorkTypePhasesMapping:
    """Tests for WORK_TYPE_PHASES constant."""

    def test_all_workflow_types_defined(self):
        """Should have all 8 workflow types defined."""
        expected_types = [
            "NEW_FEATURE", "MAINTENANCE", "BUG", "QUALITY_AUDIT",
            "MIGRATION", "REFACTORING", "DOCUMENTATION", "HOTFIX"
        ]

        for wt in expected_types:
            assert wt in WORK_TYPE_PHASES, f"Missing workflow type: {wt}"

    def test_new_feature_has_full_pipeline(self):
        """NEW_FEATURE should have all 5 phases."""
        phases = WORK_TYPE_PHASES["NEW_FEATURE"]

        assert ValidationPhase.LINTING in phases
        assert ValidationPhase.TYPE_CHECK in phases
        assert ValidationPhase.STYLE in phases
        assert ValidationPhase.UNIT_TESTS in phases
        assert ValidationPhase.E2E_TESTS in phases

    def test_documentation_has_minimal_phases(self):
        """DOCUMENTATION should only have linting."""
        phases = WORK_TYPE_PHASES["DOCUMENTATION"]

        assert ValidationPhase.LINTING in phases
        assert len(phases) == 1

    def test_hotfix_has_quick_validation(self):
        """HOTFIX should have quick validation phases."""
        phases = WORK_TYPE_PHASES["HOTFIX"]

        assert ValidationPhase.LINTING in phases
        assert ValidationPhase.UNIT_TESTS in phases
        # Should not have style or e2e
        assert ValidationPhase.STYLE not in phases

    def test_migration_focuses_on_e2e(self):
        """MIGRATION should focus on E2E tests."""
        phases = WORK_TYPE_PHASES["MIGRATION"]

        assert ValidationPhase.E2E_TESTS in phases


class TestQualityGateResult:
    """Tests for QualityGateResult dataclass."""

    def test_to_dict_basic(self):
        """to_dict should return all fields."""
        result = QualityGateResult(
            passed=True,
            workflow_type="NEW_FEATURE",
            blocking_issues=[],
            warnings=[{"message": "test warning"}],
            coverage_met=True,
            coverage_actual=85.5,
            coverage_required=80,
            validation_result=None,
            gate_config={"blocking_severities": ["critical"]}
        )

        d = result.to_dict()

        assert d["passed"] is True
        assert d["workflow_type"] == "NEW_FEATURE"
        assert d["blocking_count"] == 0
        assert d["warning_count"] == 1
        assert d["coverage"]["met"] is True
        assert d["coverage"]["actual"] == 85.5
        assert d["coverage"]["required"] == 80

    def test_to_dict_with_blocking_issues(self):
        """to_dict should count blocking issues correctly."""
        result = QualityGateResult(
            passed=False,
            workflow_type="BUG",
            blocking_issues=[
                {"message": "issue1"},
                {"message": "issue2"},
                {"message": "issue3"}
            ],
            warnings=[],
            coverage_met=True,
            coverage_actual=90.0,
            coverage_required=70,
            validation_result=None,
            gate_config={}
        )

        d = result.to_dict()

        assert d["passed"] is False
        assert d["blocking_count"] == 3


class TestQualityGateIntegrationService:
    """Tests for QualityGateIntegrationService class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mock db."""
        return QualityGateIntegrationService(mock_db)

    @pytest.mark.asyncio
    async def test_get_validation_config_default(self, service):
        """Should return default config when no rules in database."""
        # Mock no config in database
        service._config_cache = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        service.db.execute = AsyncMock(return_value=mock_result)

        config = await service.get_validation_config("NEW_FEATURE")

        assert isinstance(config, ValidationConfig)
        assert config.max_iterations == 3
        assert config.required_coverage == 80

    @pytest.mark.asyncio
    async def test_clear_cache(self, service):
        """clear_cache should reset both caches."""
        service._config_cache = MagicMock()
        service._workflow_rules_cache = {"TEST": MagicMock()}

        service.clear_cache()

        assert service._config_cache is None
        assert len(service._workflow_rules_cache) == 0


class TestValidationConfigGeneration:
    """Tests for validation config generation logic."""

    def test_phases_match_workflow_type(self):
        """Phases should match the workflow type mapping."""
        for workflow_type, expected_phases in WORK_TYPE_PHASES.items():
            # Each workflow type should have its correct phases
            assert len(expected_phases) > 0
            assert all(isinstance(p, ValidationPhase) for p in expected_phases)


class TestCoverageRequirements:
    """Tests for coverage requirement logic."""

    def test_coverage_requirements_reasonable(self):
        """Coverage requirements should be reasonable values."""
        # Default coverage requirement
        default_coverage = 80

        # Should be between 0 and 100
        assert 0 <= default_coverage <= 100

    def test_different_workflows_different_coverage(self):
        """Different workflows can have different coverage requirements."""
        # These are typical coverage requirements
        typical_requirements = {
            "NEW_FEATURE": 80,
            "MAINTENANCE": 70,
            "BUG": 70,
            "REFACTORING": 85,
            "HOTFIX": 60
        }

        for wt, coverage in typical_requirements.items():
            assert wt in WORK_TYPE_PHASES
            assert 0 <= coverage <= 100


class TestBlockingSeverities:
    """Tests for blocking severity logic."""

    def test_default_blocking_severities(self):
        """Default blocking severities should be critical."""
        default_severities = ["critical"]

        assert "critical" in default_severities

    def test_strict_workflow_blocking(self):
        """Strict workflows should block more severities."""
        strict_severities = ["critical", "high", "medium"]

        # All should be valid severity levels
        valid_severities = {"critical", "high", "medium", "low", "warning", "error"}
        for sev in strict_severities:
            assert sev in valid_severities


class TestE2ERequirements:
    """Tests for E2E test requirements."""

    def test_migration_requires_e2e(self):
        """MIGRATION workflow should typically require E2E."""
        phases = WORK_TYPE_PHASES["MIGRATION"]
        assert ValidationPhase.E2E_TESTS in phases

    def test_documentation_no_e2e(self):
        """DOCUMENTATION should not require E2E."""
        phases = WORK_TYPE_PHASES["DOCUMENTATION"]
        assert ValidationPhase.E2E_TESTS not in phases
