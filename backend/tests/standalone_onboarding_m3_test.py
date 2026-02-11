#!/usr/bin/env python3
"""
Standalone test for M3: Code Understanding (11 services).

Doel: Analyseert de codebase met 11 gespecialiseerde services (dependency analyse,
code analyse, layered analyse, framework detectie, background jobs, load estimatie,
dead code, runtime analyse, coverage, data lineage, SIG kwaliteit).
Bouwt een technisch profiel op als fundament voor M4-M7.

ECHT TESTEN: Roept de echte 11 services aan via OnboardingOrchestrator.

Usage:
    cd backend
    .venv/bin/python3 tests/standalone_onboarding_m3_test.py
    .venv/bin/python3 tests/standalone_onboarding_m3_test.py --dump
"""

import sys
import time
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
# PROGRESS TRACKING
# =============================================================================

_service_timers: dict = {}


def make_progress_callback(prefix: str = "  "):
    """Create a progress callback that logs service start/finish times."""
    def callback(event):
        service_num = event.current
        total = event.total
        msg = event.message or ""
        now = time.time()

        # Log finish of previous service
        if service_num > 1:
            prev_key = f"{prefix}:{service_num - 1}"
            if prev_key in _service_timers:
                elapsed = now - _service_timers[prev_key]
                print(f"{prefix}  [{service_num - 1}/{total}] done ({elapsed:.1f}s)")

        # Log start of current service
        _service_timers[f"{prefix}:{service_num}"] = now
        print(f"{prefix}  [{service_num}/{total}] {msg}")
        sys.stdout.flush()

    return callback


def log_final_service(prefix: str, total: int):
    """Log the finish time of the last service."""
    key = f"{prefix}:{total}"
    if key in _service_timers:
        elapsed = time.time() - _service_timers[key]
        print(f"{prefix}  [{total}/{total}] done ({elapsed:.1f}s)")
        sys.stdout.flush()


# =============================================================================
# TESTS
# =============================================================================

async def test_dataclass_scoring():
    """Test CodeUnderstandingResult quality score calculation."""
    from app.confucius.workflows.onboarding import CodeUnderstandingResult

    # All 11 succeed -> 1.0
    r1 = CodeUnderstandingResult(
        project_path="/test", services_run=11, services_succeeded=11, services_failed=0
    )
    assert r1.quality_score == 1.0, f"Expected 1.0, got {r1.quality_score}"

    # 8/11 -> 0.85
    r2 = CodeUnderstandingResult(
        project_path="/test", services_run=11, services_succeeded=8, services_failed=3
    )
    assert r2.quality_score == 0.85, f"Expected 0.85, got {r2.quality_score}"

    # 5/11 -> 0.75
    r3 = CodeUnderstandingResult(
        project_path="/test", services_run=11, services_succeeded=5, services_failed=6
    )
    assert r3.quality_score == 0.75, f"Expected 0.75, got {r3.quality_score}"

    # 3/11 -> 0.60
    r4 = CodeUnderstandingResult(
        project_path="/test", services_run=11, services_succeeded=3, services_failed=8
    )
    assert r4.quality_score == 0.60, f"Expected 0.60, got {r4.quality_score}"

    # 2/11 -> 0.50
    r5 = CodeUnderstandingResult(
        project_path="/test", services_run=11, services_succeeded=2, services_failed=9
    )
    assert r5.quality_score == 0.50, f"Expected 0.50, got {r5.quality_score}"

    # 0 run -> 0.0
    r6 = CodeUnderstandingResult(
        project_path="/test", services_run=0, services_succeeded=0, services_failed=0
    )
    assert r6.quality_score == 0.0, f"Expected 0.0, got {r6.quality_score}"

    print("  + PASSED | test_dataclass_scoring")


async def test_to_dict_serialization():
    """Test CodeUnderstandingResult serialization."""
    from app.confucius.workflows.onboarding import CodeUnderstandingResult

    result = CodeUnderstandingResult(
        project_path="/test",
        services_run=11,
        services_succeeded=8,
        services_failed=3,
        dependency_graph={"modules": ["a.py", "b.py"]},
        code_analysis={"status": "completed"},
    )

    d = result.to_dict()
    assert d["services_run"] == 11
    assert d["services_succeeded"] == 8
    assert d["quality_score"] == 0.85
    assert d["has_dependency_graph"] is True
    assert d["has_code_analysis"] is True
    print("  + PASSED | test_to_dict_serialization")


async def test_real_code_understanding_on_dvpwa():
    """Test REAL code understanding with 11 services on dvpwa."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    project_path = "/opt/projecten/examples/dvpwa"
    if not Path(project_path).exists():
        print("  o SKIPPED | test_real_code_understanding_on_dvpwa (dvpwa not found)")
        return

    orchestrator = OnboardingOrchestrator()
    cb = make_progress_callback("  ")
    context = WorkflowContext(
        session_id=f"test-m3-dvpwa-{datetime.now().strftime('%H%M%S')}",
        workflow_id="m3-test",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "answers": DVPWA_ANSWERS,
        },
        progress_callback=cb,
    )

    print(f"\n  Running 11 real services on: {project_path}")
    start_time = datetime.now(timezone.utc)

    result = await orchestrator._execute_code_understanding(context)

    log_final_service("  ", 11)
    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

    # Print detailed results
    print(f"  Duration: {duration:.1f}s")
    print(f"  Services Run: {result.get('services_run', 0)}")
    print(f"  Services Succeeded: {result.get('services_succeeded', 0)}")
    print(f"  Services Failed: {result.get('services_failed', 0)}")
    print(f"  Quality Score: {result.get('quality_score', 0)}")
    print(f"  Has Dependency Graph: {result.get('has_dependency_graph', False)}")
    print(f"  Has Code Analysis: {result.get('has_code_analysis', False)}")

    if result.get("errors"):
        print(f"  Errors ({len(result['errors'])}):")
        for err in result["errors"][:5]:
            print(f"    - {err}")

    # Validate
    assert result.get("services_run", 0) == 11, \
        f"Expected 11 services, got {result.get('services_run', 0)}"
    assert result.get("quality_score", 0) >= 0.50, \
        f"Score below M3 threshold (0.50): {result.get('quality_score', 0)}"

    # Verify stored in shared_data
    assert "code_understanding" in context.shared_data, "code_understanding not in shared_data"

    print(f"  + PASSED | test_real_code_understanding_on_dvpwa "
          f"({result.get('services_succeeded', 0)}/11 services, "
          f"score={result.get('quality_score', 0)})")


async def test_quality_threshold():
    """Test that M3 quality threshold (0.50) can be met."""
    from app.confucius.workflows.onboarding import CodeUnderstandingResult

    QUALITY_THRESHOLD = 0.50

    # Even with 2 services, should meet threshold
    result = CodeUnderstandingResult(
        project_path="/test", services_run=11, services_succeeded=2, services_failed=9
    )
    assert result.quality_score >= QUALITY_THRESHOLD, \
        f"Quality gate should pass: {result.quality_score} >= {QUALITY_THRESHOLD}"

    print("  + PASSED | test_quality_threshold")


async def test_reference_projects():
    """Test real code understanding on available reference projects."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    orchestrator = OnboardingOrchestrator()

    for project_path in REFERENCE_PROJECTS:
        if not Path(project_path).exists():
            print(f"  o SKIPPED | {Path(project_path).name} (not available)")
            continue

        prefix = f"  [{Path(project_path).name}]"
        cb = make_progress_callback(prefix)
        context = WorkflowContext(
            session_id=f"test-m3-ref-{Path(project_path).name}",
            workflow_id="m3-test",
            workflow_type="onboarding",
            shared_data={
                "project_path": project_path,
                "answers": DVPWA_ANSWERS,
            },
            progress_callback=cb,
        )

        print(f"\n  Running on {Path(project_path).name}...")
        start_time = datetime.now(timezone.utc)

        result = await orchestrator._execute_code_understanding(context)

        log_final_service(prefix, 11)
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        project_name = Path(project_path).name
        services = result.get("services_succeeded", 0)
        score = result.get("quality_score", 0)

        assert score >= 0.50, f"Score too low for {project_name}: {score}"

        print(f"  + PASSED | {project_name}: {services}/11 services, "
              f"score={score}, {duration:.1f}s")


# =============================================================================
# DUMP OUTPUT (--dump flag)
# =============================================================================

async def dump_output():
    """Run M3 code understanding and dump full JSON output."""
    import json
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    print("=" * 60)
    print("M3: Code Understanding (11 services) - OUTPUT DUMP")
    print("=" * 60)

    project_path = next(
        (p for p in REFERENCE_PROJECTS if Path(p).exists()),
        str(Path.cwd()),
    )
    print(f"Project: {project_path}")

    orchestrator = OnboardingOrchestrator()
    cb = make_progress_callback("")
    context = WorkflowContext(
        session_id="dump-m3",
        workflow_id="dump-m3",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "answers": DVPWA_ANSWERS,
        },
        progress_callback=cb,
    )

    result = await orchestrator._execute_code_understanding(context)
    log_final_service("", 11)
    output = {
        "stage": "M3 - Code Understanding (11 services)",
        "input": {"project_path": project_path},
        "output": result,
    }
    print(json.dumps(output, indent=2, default=str))


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run all M3 tests."""
    print("=" * 60)
    print("OnboardingWorkflow M3: Code Understanding Tests")
    print("REAL 11 services via OnboardingOrchestrator")
    print("=" * 60)

    results = {}

    tests = [
        ("Dataclass Scoring", test_dataclass_scoring),
        ("Serialization", test_to_dict_serialization),
        ("Quality Threshold", test_quality_threshold),
        ("Real Code Understanding on dvpwa", test_real_code_understanding_on_dvpwa),
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
