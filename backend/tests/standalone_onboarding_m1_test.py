#!/usr/bin/env python3
"""
Standalone test for M1: Input Validation.

Doel: Valideert dat de intake-vragen (project pad, doel, gebruikers, kritieke processen)
correct zijn ingevuld voordat de pipeline start. Threshold 1.0 — alle verplichte velden
moeten aanwezig zijn, anders stopt de workflow direct.

Usage:
    cd backend
    .venv/bin/python3 tests/standalone_onboarding_m1_test.py
    .venv/bin/python3 tests/standalone_onboarding_m1_test.py --dump
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# =============================================================================
# REFERENCE PROJECTS & TEST DATA
# =============================================================================

REFERENCE_PROJECTS = [
    "/opt/projecten/examples/dvpwa",
    "/opt/projecten/hci-crs",
    "/opt/projecten/paramedi/FRM",
    "/opt/projecten/paramedi/FysioOne-Classic",
]

DVPWA_ANSWERS = {
    "q1_primary_purpose": (
        "Damn Vulnerable Python Web Application - een demonstratie webapplicatie "
        "voor security testing met opzettelijke SQL-injection kwetsbaarheden, "
        "gebouwd op het aiohttp framework met PostgreSQL database"
    ),
    "q2_users": (
        "Security researchers, penetration testers, developers "
        "die web security kwetsbaarheden leren herkennen"
    ),
    "q3_critical_processes": (
        "SQL query verwerking met opzettelijke injection points, "
        "user authenticatie zonder input validatie, database operaties "
        "met raw SQL queries die kwetsbaar zijn voor aanvallen"
    ),
    "q4_integrations": (
        "PostgreSQL database, aiohttp web framework, "
        "Jinja2 template engine, Docker"
    ),
    "q5_pain_points": (
        "Opzettelijke security kwetsbaarheden, geen input sanitization, "
        "raw SQL queries, verouderde dependencies"
    ),
}

PARTIAL_ANSWERS = {
    "q1_primary_purpose": DVPWA_ANSWERS["q1_primary_purpose"],
    "q2_users": DVPWA_ANSWERS["q2_users"],
    "q3_critical_processes": DVPWA_ANSWERS["q3_critical_processes"],
    "q4_integrations": DVPWA_ANSWERS["q4_integrations"],
    # q5 is optional, not provided
}


# =============================================================================
# TESTS
# =============================================================================

async def test_questions_defined():
    """Test that 5 onboarding questions are defined."""
    from app.confucius.workflows.onboarding import ONBOARDING_QUESTIONS

    assert len(ONBOARDING_QUESTIONS) == 5, f"Expected 5 questions, got {len(ONBOARDING_QUESTIONS)}"

    required_count = sum(1 for q in ONBOARDING_QUESTIONS if q["required"])
    assert required_count == 4, f"Expected 4 required questions, got {required_count}"
    print("  + PASSED | test_questions_defined")


async def test_dataclass_scoring():
    """Test OnboardingValidationResult quality score calculation."""
    from app.confucius.workflows.onboarding import OnboardingValidationResult

    # Valid result -> 1.0
    result1 = OnboardingValidationResult(
        valid=True, answers_count=5, questions_total=5,
        missing_required=[], validation_errors=[],
    )
    assert result1.quality_score == 1.0, f"Expected 1.0, got {result1.quality_score}"

    # Invalid with missing required -> 0.0
    result2 = OnboardingValidationResult(
        valid=False, answers_count=2, questions_total=5,
        missing_required=["q2", "q3"], validation_errors=["Missing q2", "Missing q3"],
    )
    assert result2.quality_score == 0.0, f"Expected 0.0, got {result2.quality_score}"
    print("  + PASSED | test_dataclass_scoring")


async def test_valid_input_on_dvpwa():
    """Test that valid dvpwa input passes validation via real orchestrator."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    project_path = "/opt/projecten/examples/dvpwa"
    if not Path(project_path).exists():
        print("  o SKIPPED | test_valid_input_on_dvpwa (dvpwa not found)")
        return

    orchestrator = OnboardingOrchestrator()
    context = WorkflowContext(
        session_id=f"test-m1-valid-{datetime.now().strftime('%H%M%S')}",
        workflow_id="m1-test",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "answers": DVPWA_ANSWERS,
        },
    )

    result = await orchestrator._validate_input(context)

    assert result["valid"], f"Expected valid, got errors: {result.get('validation_errors', [])}"
    assert result["quality_score"] == 1.0, f"Expected 1.0, got {result['quality_score']}"
    assert result["answers_count"] == 5, f"Expected 5 answers, got {result['answers_count']}"

    print(f"  + PASSED | test_valid_input_on_dvpwa (score={result['quality_score']})")


async def test_partial_answers_passes():
    """Test that partial answers (only required) still passes."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    project_path = "/opt/projecten/examples/dvpwa"
    if not Path(project_path).exists():
        print("  o SKIPPED | test_partial_answers_passes (dvpwa not found)")
        return

    orchestrator = OnboardingOrchestrator()
    context = WorkflowContext(
        session_id=f"test-m1-partial-{datetime.now().strftime('%H%M%S')}",
        workflow_id="m1-test",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "answers": PARTIAL_ANSWERS,
        },
    )

    result = await orchestrator._validate_input(context)

    assert result["valid"], f"Expected valid, got errors: {result.get('validation_errors', [])}"
    assert result["quality_score"] == 1.0
    print("  + PASSED | test_partial_answers_passes")


async def test_missing_required_fails():
    """Test that missing required answers fails validation."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    orchestrator = OnboardingOrchestrator()
    context = WorkflowContext(
        session_id="test-m1-missing",
        workflow_id="m1-test",
        workflow_type="onboarding",
        shared_data={
            "project_path": "/tmp",
            "answers": {"q1_primary_purpose": "Valid answer that is long enough for validation to pass"},
        },
    )

    result = await orchestrator._validate_input(context)

    assert not result["valid"], "Expected invalid"
    assert result["quality_score"] == 0.0
    assert len(result["missing_required"]) == 3, f"Expected 3 missing, got {result['missing_required']}"
    print("  + PASSED | test_missing_required_fails")


async def test_missing_project_path_fails():
    """Test that missing project_path fails validation."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    orchestrator = OnboardingOrchestrator()
    context = WorkflowContext(
        session_id="test-m1-nopath",
        workflow_id="m1-test",
        workflow_type="onboarding",
        shared_data={
            "answers": DVPWA_ANSWERS,
        },
    )

    result = await orchestrator._validate_input(context)

    assert not result["valid"], "Expected invalid"
    assert "project_path is required" in result["validation_errors"]
    print("  + PASSED | test_missing_project_path_fails")


async def test_nonexistent_path_fails():
    """Test that nonexistent project_path fails validation."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    orchestrator = OnboardingOrchestrator()
    context = WorkflowContext(
        session_id="test-m1-badpath",
        workflow_id="m1-test",
        workflow_type="onboarding",
        shared_data={
            "project_path": "/nonexistent/path",
            "answers": DVPWA_ANSWERS,
        },
    )

    result = await orchestrator._validate_input(context)

    assert not result["valid"], "Expected invalid"
    assert any("does not exist" in e for e in result["validation_errors"])
    print("  + PASSED | test_nonexistent_path_fails")


async def test_answer_too_short_fails():
    """Test that answers below min_length fail validation."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    orchestrator = OnboardingOrchestrator()
    context = WorkflowContext(
        session_id="test-m1-short",
        workflow_id="m1-test",
        workflow_type="onboarding",
        shared_data={
            "project_path": "/tmp",
            "answers": {
                "q1_primary_purpose": "Too short",  # Needs 50 chars
                "q2_users": "OK length for this question here",
                "q3_critical_processes": "Also too short",  # Needs 50 chars
                "q4_integrations": "API integration here",
            },
        },
    )

    result = await orchestrator._validate_input(context)

    assert not result["valid"], "Expected invalid"
    errors = result["validation_errors"]
    assert any("q1_primary_purpose" in e for e in errors), f"Expected q1 error in {errors}"
    assert any("q3_critical_processes" in e for e in errors), f"Expected q3 error in {errors}"
    print("  + PASSED | test_answer_too_short_fails")


async def test_reference_projects():
    """Test input validation on all available reference projects."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    orchestrator = OnboardingOrchestrator()

    for project_path in REFERENCE_PROJECTS:
        if not Path(project_path).exists():
            print(f"  o SKIPPED | {Path(project_path).name} (not available)")
            continue

        context = WorkflowContext(
            session_id=f"test-m1-ref-{Path(project_path).name}",
            workflow_id="m1-test",
            workflow_type="onboarding",
            shared_data={
                "project_path": project_path,
                "answers": DVPWA_ANSWERS,
            },
        )

        result = await orchestrator._validate_input(context)
        assert result["valid"], f"Failed for {project_path}: {result.get('validation_errors', [])}"
        assert result["quality_score"] == 1.0
        print(f"  + PASSED | reference project {Path(project_path).name} (score={result['quality_score']})")


# =============================================================================
# DUMP OUTPUT (--dump flag)
# =============================================================================

async def dump_output():
    """Run M1 validation on dvpwa and dump full JSON output."""
    import json
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    print("=" * 60)
    print("M1: Input Validation - OUTPUT DUMP")
    print("=" * 60)

    project_path = next(
        (p for p in REFERENCE_PROJECTS if Path(p).exists()),
        str(Path.cwd()),
    )
    print(f"Project: {project_path}")

    orchestrator = OnboardingOrchestrator()
    context = WorkflowContext(
        session_id="dump-m1",
        workflow_id="dump-m1",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "answers": DVPWA_ANSWERS,
        },
    )

    result = await orchestrator._validate_input(context)
    output = {
        "stage": "M1 - Input Validation",
        "input": context.shared_data,
        "output": result,
    }
    print(json.dumps(output, indent=2, default=str))


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run all M1 tests."""
    print("=" * 60)
    print("OnboardingWorkflow M1: Input Validation Tests")
    print("Real imports from app.confucius.workflows.onboarding")
    print("=" * 60)

    results = {}

    tests = [
        ("Questions Defined", test_questions_defined),
        ("Dataclass Scoring", test_dataclass_scoring),
        ("Valid Input on dvpwa", test_valid_input_on_dvpwa),
        ("Partial Answers Passes", test_partial_answers_passes),
        ("Missing Required Fails", test_missing_required_fails),
        ("Missing Project Path Fails", test_missing_project_path_fails),
        ("Nonexistent Path Fails", test_nonexistent_path_fails),
        ("Answer Too Short Fails", test_answer_too_short_fails),
        ("Reference Projects", test_reference_projects),
    ]

    for name, test_fn in tests:
        print(f"\n--- {name} ---")
        try:
            await test_fn()
            results[name] = "PASSED"
        except Exception as e:
            results[name] = f"ERROR: {e}"
            print(f"  x FAILED | {name}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed_count = sum(1 for v in results.values() if v == "PASSED")
    total_count = len(results)

    for test_name, result in results.items():
        status = "PASSED" if result == "PASSED" else "FAILED"
        symbol = "+" if status == "PASSED" else "x"
        print(f"  {symbol} {status} | {test_name}")
        if result not in ["PASSED", "FAILED"]:
            print(f"    {result}")

    print("=" * 60)
    print(f"TOTAL: {passed_count}/{total_count} tests passed")
    print("=" * 60)

    sys.exit(0 if passed_count == total_count else 1)


if __name__ == "__main__":
    if "--dump" in sys.argv:
        asyncio.run(dump_output())
    else:
        asyncio.run(main())
