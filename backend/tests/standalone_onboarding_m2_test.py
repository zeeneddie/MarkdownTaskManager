#!/usr/bin/env python3
"""
Standalone test for M2: Intake + Context Fetching.

Doel: Haalt bestaande projectkennis op uit docs (architectuurdocs, eerdere analyses)
om latere stages te verrijken. Graceful degradation: als er geen docs zijn,
gaat de pipeline door met score 0.70 — de context is optioneel, niet blokkerend.

Usage:
    cd backend
    .venv/bin/python3 tests/standalone_onboarding_m2_test.py
    .venv/bin/python3 tests/standalone_onboarding_m2_test.py --dump
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


# =============================================================================
# TESTS
# =============================================================================

async def test_dataclass_scoring():
    """Test IntakeContextResult quality score calculation."""
    from app.confucius.workflows.onboarding import IntakeContextResult

    # No context -> 0.70
    r1 = IntakeContextResult(
        context_available=False, project_name="test", project_path="/test",
        relevant_docs=[], architecture_summary=None, code_locations=[],
        total_docs_found=0, fetched_at="2026-01-01T00:00:00Z",
    )
    assert r1.quality_score == 0.70, f"Expected 0.70, got {r1.quality_score}"

    # Rich context -> 1.0
    r2 = IntakeContextResult(
        context_available=True, project_name="test", project_path="/test",
        relevant_docs=[{"x": i} for i in range(5)],
        architecture_summary="Some architecture", code_locations=[],
        total_docs_found=5, fetched_at="2026-01-01T00:00:00Z",
    )
    assert r2.quality_score == 1.0, f"Expected 1.0, got {r2.quality_score}"

    # Partial (docs but no architecture) -> 0.85
    r3 = IntakeContextResult(
        context_available=True, project_name="test", project_path="/test",
        relevant_docs=[{"x": 1}], architecture_summary=None, code_locations=[],
        total_docs_found=1, fetched_at="2026-01-01T00:00:00Z",
    )
    assert r3.quality_score == 0.85, f"Expected 0.85, got {r3.quality_score}"

    print("  + PASSED | test_dataclass_scoring")


async def test_to_dict_serialization():
    """Test IntakeContextResult serialization."""
    from app.confucius.workflows.onboarding import IntakeContextResult

    result = IntakeContextResult(
        context_available=True, project_name="test", project_path="/test",
        relevant_docs=[{"content": "test"}],
        architecture_summary="Test arch", code_locations=[{"path": "a.py", "source": "x"}],
        total_docs_found=1, fetched_at="2026-01-01T00:00:00Z",
    )
    d = result.to_dict()
    assert d["context_available"] is True
    assert d["relevant_docs_count"] == 1
    assert d["has_architecture_summary"] is True
    assert "quality_score" in d
    print("  + PASSED | test_to_dict_serialization")


async def test_intake_context_on_dvpwa():
    """Test real intake context fetching on dvpwa project."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    project_path = "/opt/projecten/examples/dvpwa"
    if not Path(project_path).exists():
        print("  o SKIPPED | test_intake_context_on_dvpwa (dvpwa not found)")
        return

    orchestrator = OnboardingOrchestrator()
    context = WorkflowContext(
        session_id=f"test-m2-dvpwa-{datetime.now().strftime('%H%M%S')}",
        workflow_id="m2-test",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "answers": DVPWA_ANSWERS,
        },
    )

    print(f"\n  Running intake context on: {project_path}")
    result = await orchestrator._fetch_intake_context(context)

    # Print results
    print(f"  Context Available: {result.get('context_available')}")
    print(f"  Total Docs Found: {result.get('total_docs_found', 0)}")
    print(f"  Has Architecture: {result.get('has_architecture_summary', False)}")
    print(f"  Code Locations: {result.get('code_locations_count', 0)}")
    print(f"  Quality Score: {result.get('quality_score')}")
    print(f"  Error: {result.get('error')}")

    # Validate structure
    assert "quality_score" in result, "Missing quality_score"
    assert result["quality_score"] >= 0.70, f"Score below threshold: {result['quality_score']}"

    # Verify stored in shared_data
    assert "intake_context" in context.shared_data, "intake_context not in shared_data"

    print(f"  + PASSED | test_intake_context_on_dvpwa (score={result['quality_score']})")


async def test_graceful_degradation():
    """Test graceful degradation when no docs available."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext
    import tempfile

    orchestrator = OnboardingOrchestrator()

    with tempfile.TemporaryDirectory() as tmp:
        context = WorkflowContext(
            session_id="test-m2-degrade",
            workflow_id="m2-test",
            workflow_type="onboarding",
            shared_data={
                "project_path": tmp,
                "answers": DVPWA_ANSWERS,
            },
        )

        result = await orchestrator._fetch_intake_context(context)

        assert result["quality_score"] >= 0.70, \
            f"Degradation should still meet threshold: {result['quality_score']}"
        print(f"  + PASSED | test_graceful_degradation (score={result['quality_score']})")


async def test_reference_projects():
    """Test intake context on all available reference projects."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    orchestrator = OnboardingOrchestrator()

    for project_path in REFERENCE_PROJECTS:
        if not Path(project_path).exists():
            print(f"  o SKIPPED | {Path(project_path).name} (not available)")
            continue

        context = WorkflowContext(
            session_id=f"test-m2-ref-{Path(project_path).name}",
            workflow_id="m2-test",
            workflow_type="onboarding",
            shared_data={
                "project_path": project_path,
                "answers": DVPWA_ANSWERS,
            },
        )

        result = await orchestrator._fetch_intake_context(context)

        project_name = Path(project_path).name
        score = result.get("quality_score", 0)
        docs = result.get("total_docs_found", 0)
        assert score >= 0.70, f"Score too low for {project_name}: {score}"

        print(f"  + PASSED | {project_name}: {docs} docs, score={score}")


# =============================================================================
# DUMP OUTPUT (--dump flag)
# =============================================================================

async def dump_output():
    """Run M2 intake context and dump full JSON output."""
    import json
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    print("=" * 60)
    print("M2: Intake Context - OUTPUT DUMP")
    print("=" * 60)

    project_path = next(
        (p for p in REFERENCE_PROJECTS if Path(p).exists()),
        str(Path.cwd()),
    )
    print(f"Project: {project_path}")

    orchestrator = OnboardingOrchestrator()
    context = WorkflowContext(
        session_id="dump-m2",
        workflow_id="dump-m2",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "answers": DVPWA_ANSWERS,
        },
    )

    result = await orchestrator._fetch_intake_context(context)
    output = {
        "stage": "M2 - Intake Context",
        "input": {"project_path": project_path, "answers": DVPWA_ANSWERS},
        "output": result,
    }
    print(json.dumps(output, indent=2, default=str, ensure_ascii=False))


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run all M2 tests."""
    print("=" * 60)
    print("OnboardingWorkflow M2: Intake Context Tests")
    print("Real imports from app.confucius.workflows.onboarding")
    print("=" * 60)

    results = {}

    tests = [
        ("Dataclass Scoring", test_dataclass_scoring),
        ("Serialization", test_to_dict_serialization),
        ("Intake Context on dvpwa", test_intake_context_on_dvpwa),
        ("Graceful Degradation", test_graceful_degradation),
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
