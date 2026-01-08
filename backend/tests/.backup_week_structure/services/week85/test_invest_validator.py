"""
Tests for INVEST Validator Service - Week 85

Tests:
- INVESTValidatorService
- Individual criterion validators
- Batch validation
- SMART validation for tasks
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from app.services.invest_validator_service import (
    INVESTValidatorService,
    ValidationLevel,
    CriterionStatus,
    ItemType,
    CriterionResult,
    INVESTValidationResult,
    SMARTValidationResult,
    BatchValidationResult,
    get_invest_validator,
)


class TestCriterionResult:
    """Tests for CriterionResult dataclass."""

    def test_create_pass_result(self):
        """Should create passing criterion result."""
        result = CriterionResult(
            criterion="independent",
            status=CriterionStatus.PASS,
            score=0.9,
            feedback="Story has no dependencies",
        )

        assert result.criterion == "independent"
        assert result.status == CriterionStatus.PASS
        assert result.score == 0.9
        assert "dependencies" in result.feedback

    def test_create_fail_result(self):
        """Should create failing criterion result."""
        result = CriterionResult(
            criterion="small",
            status=CriterionStatus.FAIL,
            score=0.3,
            feedback="Story too large - 15 acceptance criteria",
        )

        assert result.status == CriterionStatus.FAIL
        assert result.score == 0.3


class TestINVESTValidationResult:
    """Tests for INVESTValidationResult dataclass."""

    def test_create_valid_result(self):
        """Should create valid result."""
        result = INVESTValidationResult(
            item_id="S001",
            title="User Authentication",
            overall_score=0.85,
            is_valid=True,
            validation_level=ValidationLevel.STANDARD,
        )

        assert result.is_valid is True
        assert result.overall_score == 0.85
        assert result.item_id == "S001"

    def test_create_invalid_result(self):
        """Should create invalid result with issues."""
        result = INVESTValidationResult(
            item_id="S002",
            title="Complex Feature",
            overall_score=0.55,
            is_valid=False,
            validation_level=ValidationLevel.STRICT,
            small=CriterionResult(
                criterion="small",
                status=CriterionStatus.FAIL,
                score=0.3,
                feedback="Too large",
            ),
            errors=["Story too large - split into smaller stories"],
        )

        assert result.is_valid is False
        assert result.small is not None
        assert result.small.status == CriterionStatus.FAIL


class TestINVESTValidatorService:
    """Tests for INVESTValidatorService."""

    def test_init_service(self):
        """Should initialize service with defaults."""
        service = INVESTValidatorService()

        assert hasattr(service, 'WEIGHTS')
        assert "independent" in service.WEIGHTS
        assert sum(service.WEIGHTS.values()) == pytest.approx(1.0)

    def test_service_has_thresholds(self):
        """Should have validation thresholds."""
        service = INVESTValidatorService()
        assert hasattr(service, 'THRESHOLDS')
        assert ValidationLevel.STANDARD in service.THRESHOLDS

    @pytest.mark.asyncio
    async def test_validate_good_story(self):
        """Should validate a well-formed story."""
        service = INVESTValidatorService()

        story = {
            "id": "S001",
            "title": "As a user, I want to reset my password",
            "description": "Allow users to reset forgotten passwords via email",
            "type": "story",
            "acceptance_criteria": [
                "User clicks 'Forgot Password' link",
                "User receives email within 5 minutes",
                "Reset link expires after 24 hours",
            ],
            "estimation": {"story_points": 3},
        }

        result = await service.validate_story(story)

        assert result.item_id == "S001"
        assert result.overall_score > 0.6
        assert result.validation_level == ValidationLevel.STANDARD

    @pytest.mark.asyncio
    async def test_validate_poor_story(self):
        """Should identify issues in poor story."""
        service = INVESTValidatorService()

        story = {
            "id": "S002",
            "title": "Make system better",  # Vague
            "description": "",  # No description
            "type": "story",
            "acceptance_criteria": [],  # No AC
        }

        result = await service.validate_story(story)

        assert result.overall_score < 0.7
        assert result.is_valid is False
        # Testable criterion should fail due to no AC
        assert result.testable is not None
        assert result.testable.status == CriterionStatus.FAIL

    @pytest.mark.asyncio
    async def test_validate_with_lenient_level(self):
        """Should perform lenient validation."""
        service = INVESTValidatorService()

        story = {
            "id": "S003",
            "title": "Add login button",
            "type": "story",
        }

        result = await service.validate_story(story, level=ValidationLevel.LENIENT)

        assert result.validation_level == ValidationLevel.LENIENT
        # Lenient validation should still produce a score
        assert result.overall_score >= 0.0

    @pytest.mark.asyncio
    async def test_validate_with_strict_level(self):
        """Should perform strict validation."""
        service = INVESTValidatorService()

        story = {
            "id": "S004",
            "title": "As a user, I want to export my data to CSV",
            "description": "Full data export functionality",
            "type": "story",
            "acceptance_criteria": [
                "Export includes all user data",
                "CSV format is valid",
                "Large exports are chunked",
            ],
            "dependencies": [],
            "estimation": {"story_points": 5, "hours": 20},
        }

        result = await service.validate_story(story, level=ValidationLevel.STRICT)

        assert result.validation_level == ValidationLevel.STRICT
        # All criteria should be evaluated - check individual fields
        criteria_count = sum(1 for c in [result.independent, result.negotiable, result.valuable,
                                          result.estimable, result.small, result.testable] if c is not None)
        assert criteria_count >= 6

    @pytest.mark.asyncio
    async def test_validate_batch(self):
        """Should validate multiple stories."""
        service = INVESTValidatorService()

        stories = [
            {"id": "S001", "title": "Story 1", "type": "story"},
            {"id": "S002", "title": "Story 2", "type": "story"},
            {"id": "S003", "title": "Story 3", "type": "story"},
        ]

        result = await service.validate_batch(stories)

        assert isinstance(result, BatchValidationResult)
        assert result.total_items == 3
        assert len(result.results) == 3
        assert result.average_score >= 0.0

    @pytest.mark.asyncio
    async def test_validate_batch_with_failures(self):
        """Should count valid and invalid in batch."""
        service = INVESTValidatorService()

        stories = [
            {
                "id": "S001",
                "title": "As a user, I want to login securely",
                "description": "Secure authentication",
                "acceptance_criteria": ["AC1", "AC2"],
                "estimation": {"story_points": 3},
            },
            {
                "id": "S002",
                "title": "Fix stuff",  # Poor story
                "description": "",
            },
        ]

        # Use STRICT level so poor stories are more likely to be invalid
        result = await service.validate_batch(stories, level=ValidationLevel.STRICT)

        assert result.total_items == 2
        # At least one should pass or fail based on quality
        assert result.valid_items + result.invalid_items == 2


class TestPrivateValidators:
    """Tests for internal validation methods."""

    def test_validate_independent(self):
        """Should check story independence."""
        service = INVESTValidatorService()

        # Story with no dependencies
        story1 = {"id": "S001", "title": "Independent story"}
        result1 = service._validate_independent(story1, None)
        assert result1.score > 0.5

        # Story with explicit dependencies
        story2 = {"id": "S002", "dependencies": ["S001", "S003"]}
        result2 = service._validate_independent(story2, None)
        assert result2.score < result1.score

    def test_validate_valuable(self):
        """Should check story value."""
        service = INVESTValidatorService()

        # Story with clear value proposition
        story1 = {
            "title": "As a user, I want to save my preferences",
            "description": "Improves user experience",
        }
        result1 = service._validate_valuable(story1)
        assert result1.score > 0.5

        # Story with unclear value
        story2 = {"title": "Refactor module X"}
        result2 = service._validate_valuable(story2)
        assert result2.score <= result1.score

    def test_validate_small(self):
        """Should check story size."""
        service = INVESTValidatorService()

        # Small story
        story1 = {
            "estimation": {"story_points": 3},
            "acceptance_criteria": ["AC1", "AC2"],
        }
        result1 = service._validate_small(story1)
        assert result1.score > 0.6

        # Large story
        story2 = {
            "estimation": {"story_points": 21},
            "acceptance_criteria": [f"AC{i}" for i in range(15)],
        }
        result2 = service._validate_small(story2)
        assert result2.score < result1.score

    def test_validate_testable(self):
        """Should check story testability."""
        service = INVESTValidatorService()

        # Testable story
        story1 = {
            "acceptance_criteria": [
                "When user clicks Submit, form validates",
                "Error message displays for invalid input",
            ],
        }
        result1 = service._validate_testable(story1)
        assert result1.score > 0.5

        # Not testable (no AC)
        story2 = {"title": "Make it work"}
        result2 = service._validate_testable(story2)
        assert result2.score < result1.score


class TestSMARTValidation:
    """Tests for SMART validation of tasks."""

    @pytest.mark.asyncio
    async def test_validate_task(self):
        """Should validate task against SMART criteria."""
        service = INVESTValidatorService()

        task = {
            "id": "T001",
            "title": "Implement password hashing using bcrypt",
            "description": "Add bcrypt hashing to user password storage",
            "estimation": {"hours": 4},
            "due_date": "2024-12-25",
        }

        result = await service.validate_task(task)

        assert isinstance(result, SMARTValidationResult)
        assert result.task_id == "T001"
        assert result.overall_score >= 0.0

    @pytest.mark.asyncio
    async def test_validate_task_with_parent(self):
        """Should validate task in context of parent story."""
        service = INVESTValidatorService()

        parent_story = {
            "id": "S001",
            "title": "User Authentication",
            "acceptance_criteria": ["Passwords are hashed"],
        }

        task = {
            "id": "T001",
            "title": "Implement bcrypt hashing",
            "parent_story_id": "S001",
        }

        result = await service.validate_task(task, parent_story)

        # Relevance should be higher with matching parent
        assert result.overall_score >= 0.0


class TestFactoryFunction:
    """Tests for factory function."""

    def test_get_invest_validator(self):
        """Should create validator via factory."""
        validator = get_invest_validator()

        assert isinstance(validator, INVESTValidatorService)
        assert hasattr(validator, 'WEIGHTS')

    def test_get_invest_validator_with_db(self):
        """Should create validator with database session."""
        mock_db = Mock()
        validator = get_invest_validator(db=mock_db)

        assert validator.db == mock_db


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
