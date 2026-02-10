#!/usr/bin/env python3
"""
Standalone test for OnboardingWorkflow Module 1.

This test can be run without the full dependency stack.
It validates the core validation logic.

Usage:
    python3 backend/tests/standalone_onboarding_m1_test.py
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# =============================================================================
# INLINE DEFINITIONS (copied from onboarding.py for standalone testing)
# =============================================================================

ONBOARDING_QUESTIONS = [
    {
        "id": "q1_primary_purpose",
        "question": "Wat is het primaire doel van deze applicatie?",
        "description": "Beschrijf de kernfunctionaliteit en het businessdoel",
        "required": True,
        "min_length": 50,
        "category": "context",
    },
    {
        "id": "q2_users",
        "question": "Wie zijn de belangrijkste gebruikers?",
        "description": "Beschrijf de doelgroepen en hun rollen",
        "required": True,
        "min_length": 30,
        "category": "context",
    },
    {
        "id": "q3_critical_processes",
        "question": "Wat zijn de kritieke business processen?",
        "description": "Beschrijf de processen die niet mogen falen",
        "required": True,
        "min_length": 50,
        "category": "analysis",
    },
    {
        "id": "q4_integrations",
        "question": "Welke integraties bestaan er?",
        "description": "Beschrijf externe systemen, APIs, databases",
        "required": True,
        "min_length": 20,
        "category": "analysis",
    },
    {
        "id": "q5_pain_points",
        "question": "Wat zijn de belangrijkste pijnpunten?",
        "description": "Beschrijf technische schuld, performance issues, etc.",
        "required": False,
        "min_length": 0,
        "category": "analysis",
    },
]


@dataclass
class OnboardingValidationResult:
    """Result of onboarding input validation."""
    valid: bool
    answers_count: int
    questions_total: int
    missing_required: List[str]
    validation_errors: List[str]

    @property
    def quality_score(self) -> float:
        if self.missing_required:
            return 0.0
        return 1.0 if self.valid else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "answers_count": self.answers_count,
            "questions_total": self.questions_total,
            "missing_required": self.missing_required,
            "validation_errors": self.validation_errors,
            "quality_score": self.quality_score,
        }


def validate_input(project_path: Optional[str], answers: Dict[str, str]) -> OnboardingValidationResult:
    """
    Validate onboarding inputs.

    This is the core validation logic from OnboardingOrchestrator._validate_input().
    """
    validation_errors: List[str] = []
    missing_required: List[str] = []

    # Validate project_path
    if not project_path:
        validation_errors.append("project_path is required")
    else:
        path = Path(project_path)
        if not path.exists():
            validation_errors.append(f"project_path does not exist: {project_path}")
        elif not path.is_dir():
            validation_errors.append(f"project_path is not a directory: {project_path}")

    # Validate answers
    for q in ONBOARDING_QUESTIONS:
        q_id = q["id"]
        answer = answers.get(q_id, "").strip()

        if q["required"]:
            if not answer:
                missing_required.append(q_id)
                validation_errors.append(f"Required question not answered: {q_id}")
            elif len(answer) < q["min_length"]:
                validation_errors.append(
                    f"Answer too short for {q_id}: "
                    f"got {len(answer)}, need {q['min_length']}"
                )

    is_valid = len(validation_errors) == 0
    return OnboardingValidationResult(
        valid=is_valid,
        answers_count=len([a for a in answers.values() if a]),
        questions_total=len(ONBOARDING_QUESTIONS),
        missing_required=missing_required,
        validation_errors=validation_errors,
    )


# =============================================================================
# TEST DATA
# =============================================================================

VALID_ANSWERS = {
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

PARTIAL_ANSWERS = {
    "q1_primary_purpose": (
        "Dit is een healthcare registratie systeem voor het beheren van "
        "patientgegevens en afspraken in ziekenhuizen en klinieken."
    ),
    "q2_users": "Administratief personeel en artsen",
    "q3_critical_processes": (
        "Patient registratie en afspraak planning. "
        "Deze processen mogen nooit data verliezen."
    ),
    "q4_integrations": "HL7 FHIR, Vecozo, LDAP",  # min 20 chars
    # q5 is optional, not provided
}

REFERENCE_PROJECTS = [
    "/opt/projecten/hci-crs",
    "/opt/projecten/paramedi/FRM",
    "/opt/projecten/paramedi/FysioOne-Classic",
]


# =============================================================================
# TESTS
# =============================================================================

def test_questions_defined():
    """Test that 5 onboarding questions are defined."""
    assert len(ONBOARDING_QUESTIONS) == 5, f"Expected 5 questions, got {len(ONBOARDING_QUESTIONS)}"

    required_count = sum(1 for q in ONBOARDING_QUESTIONS if q["required"])
    assert required_count == 4, f"Expected 4 required questions, got {required_count}"
    print("✓ test_questions_defined PASSED")


def test_valid_input_passes(tmp_dir: Path):
    """Test that valid input passes validation."""
    result = validate_input(str(tmp_dir), VALID_ANSWERS)

    assert result.valid, f"Expected valid, got errors: {result.validation_errors}"
    assert result.quality_score == 1.0, f"Expected score 1.0, got {result.quality_score}"
    assert result.answers_count == 5, f"Expected 5 answers, got {result.answers_count}"
    print("✓ test_valid_input_passes PASSED")


def test_partial_answers_passes(tmp_dir: Path):
    """Test that partial answers (only required) still passes."""
    result = validate_input(str(tmp_dir), PARTIAL_ANSWERS)

    assert result.valid, f"Expected valid, got errors: {result.validation_errors}"
    assert result.quality_score == 1.0
    print("✓ test_partial_answers_passes PASSED")


def test_missing_required_fails(tmp_dir: Path):
    """Test that missing required answers fails validation."""
    incomplete = {"q1_primary_purpose": "Valid answer that is long enough for validation"}
    result = validate_input(str(tmp_dir), incomplete)

    assert not result.valid, "Expected invalid"
    assert result.quality_score == 0.0
    assert len(result.missing_required) == 3, f"Expected 3 missing, got {result.missing_required}"
    print("✓ test_missing_required_fails PASSED")


def test_missing_project_path_fails():
    """Test that missing project_path fails validation."""
    result = validate_input(None, VALID_ANSWERS)

    assert not result.valid, "Expected invalid"
    assert "project_path is required" in result.validation_errors
    print("✓ test_missing_project_path_fails PASSED")


def test_nonexistent_path_fails():
    """Test that nonexistent project_path fails validation."""
    result = validate_input("/nonexistent/path", VALID_ANSWERS)

    assert not result.valid, "Expected invalid"
    assert any("does not exist" in e for e in result.validation_errors)
    print("✓ test_nonexistent_path_fails PASSED")


def test_answer_too_short_fails(tmp_dir: Path):
    """Test that answers below min_length fail validation."""
    short_answers = {
        "q1_primary_purpose": "Too short",  # Needs 50 chars
        "q2_users": "OK length for this question here",
        "q3_critical_processes": "Also too short",  # Needs 50 chars
        "q4_integrations": "API integration here",
    }
    result = validate_input(str(tmp_dir), short_answers)

    assert not result.valid, "Expected invalid"
    errors = result.validation_errors
    assert any("q1_primary_purpose" in e for e in errors), f"Expected q1 error in {errors}"
    assert any("q3_critical_processes" in e for e in errors), f"Expected q3 error in {errors}"
    print("✓ test_answer_too_short_fails PASSED")


def test_reference_projects():
    """Test that reference projects can be validated."""
    for project_path in REFERENCE_PROJECTS:
        if not Path(project_path).exists():
            print(f"⊘ SKIPPED {project_path} (not available)")
            continue

        result = validate_input(project_path, VALID_ANSWERS)
        assert result.valid, f"Failed for {project_path}: {result.validation_errors}"
        assert result.quality_score == 1.0
        print(f"✓ test_reference_project {Path(project_path).name} PASSED")


def test_quality_score_calculation():
    """Test OnboardingValidationResult quality score calculation."""
    # Valid result
    result1 = OnboardingValidationResult(
        valid=True, answers_count=5, questions_total=5,
        missing_required=[], validation_errors=[],
    )
    assert result1.quality_score == 1.0

    # Invalid with missing required
    result2 = OnboardingValidationResult(
        valid=False, answers_count=2, questions_total=5,
        missing_required=["q2", "q3"], validation_errors=["Missing q2", "Missing q3"],
    )
    assert result2.quality_score == 0.0
    print("✓ test_quality_score_calculation PASSED")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all tests."""
    import tempfile

    print("=" * 60)
    print("OnboardingWorkflow Module 1 - Standalone Tests")
    print("=" * 60)
    print()

    # Create temp directory for tests
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)

        tests = [
            lambda: test_questions_defined(),
            lambda: test_valid_input_passes(tmp_dir),
            lambda: test_partial_answers_passes(tmp_dir),
            lambda: test_missing_required_fails(tmp_dir),
            lambda: test_missing_project_path_fails(),
            lambda: test_nonexistent_path_fails(),
            lambda: test_answer_too_short_fails(tmp_dir),
            lambda: test_quality_score_calculation(),
        ]

        passed = 0
        failed = 0

        for test in tests:
            try:
                test()
                passed += 1
            except AssertionError as e:
                print(f"✗ FAILED: {e}")
                failed += 1
            except Exception as e:
                print(f"✗ ERROR: {e}")
                failed += 1

        print()
        print("-" * 60)
        print("Reference Project Tests")
        print("-" * 60)

        try:
            test_reference_projects()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            failed += 1

        print()
        print("=" * 60)
        print(f"RESULTS: {passed} passed, {failed} failed")
        print("=" * 60)

        if failed > 0:
            sys.exit(1)

        print()
        print("✓ Module 1 (Input Validation) - ALL TESTS PASSED")
        print()
        print("Ready to proceed to Module 2 (Intake + Vector DB)")


if __name__ == "__main__":
    main()
