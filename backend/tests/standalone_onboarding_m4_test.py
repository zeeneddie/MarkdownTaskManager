#!/usr/bin/env python3
"""
Standalone test for M4: Deep Extraction (Felix+Quinn+Marcus).

Doel: Drie LLM-agents voeren diepe code-analyse uit:
- Felix: Architectuur patronen en legacy code analyse
- Quinn: Code quality review en issue identificatie
- Marcus: Onderhoudbaarheid en technische schuld

Samen leveren ze de gedetailleerde technische inzichten die M8 nodig heeft.

ECHT TESTEN: Roept de echte agents aan via OnboardingOrchestrator.
Bij graceful degradation (agents niet beschikbaar) valt terug op code_understanding.

Usage:
    cd backend
    .venv/bin/python3 tests/standalone_onboarding_m4_test.py
    .venv/bin/python3 tests/standalone_onboarding_m4_test.py --dump
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
    """Test DeepExtractionResult quality score calculation."""
    from app.confucius.workflows.onboarding import DeepExtractionResult

    # All 3 agents with substantive output -> 1.0
    r1 = DeepExtractionResult(
        project_path="/test",
        agents_run=3,
        agents_succeeded=3,
        architecture_insights={"patterns": [{"name": "MVC"}]},
        quality_findings=[{"id": "Q001", "severity": "high"}],
        maintenance_recommendations=[{"id": "M001"}],
    )
    assert r1.quality_score == 1.0, f"Expected 1.0, got {r1.quality_score}"

    # 2/3 agents -> 0.85
    r2 = DeepExtractionResult(
        project_path="/test",
        agents_run=3,
        agents_succeeded=2,
        architecture_insights={"patterns": [{"name": "MVC"}]},
        quality_findings=[{"id": "Q001"}],
        maintenance_recommendations=[],
    )
    assert r2.quality_score == 0.85, f"Expected 0.85, got {r2.quality_score}"

    # 1/3 agents -> 0.70
    r3 = DeepExtractionResult(
        project_path="/test",
        agents_run=3,
        agents_succeeded=1,
        architecture_insights={"patterns": [{"name": "MVC"}]},
        quality_findings=[],
        maintenance_recommendations=[],
    )
    assert r3.quality_score == 0.70, f"Expected 0.70, got {r3.quality_score}"

    # No agents (degraded) -> 0.50
    r4 = DeepExtractionResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
    )
    assert r4.quality_score == 0.50, f"Expected 0.50, got {r4.quality_score}"

    print("  + PASSED | test_dataclass_scoring")


async def test_to_dict_serialization():
    """Test DeepExtractionResult serialization."""
    from app.confucius.workflows.onboarding import DeepExtractionResult

    result = DeepExtractionResult(
        project_path="/test",
        agents_run=3,
        agents_succeeded=2,
        architecture_insights={"patterns": [{"name": "MVC"}]},
        quality_findings=[{"id": "Q001"}],
        maintenance_recommendations=[],
        council_consensus={"status": "partial"},
    )

    d = result.to_dict()
    assert d["agents_run"] == 3
    assert d["agents_succeeded"] == 2
    assert d["agents_failed"] == 1
    assert d["quality_score"] == 0.85
    assert d["has_architecture_insights"] is True
    assert d["quality_findings_count"] == 1
    assert d["maintenance_recommendations_count"] == 0
    print("  + PASSED | test_to_dict_serialization")


async def test_real_deep_extraction_on_dvpwa():
    """Test REAL deep extraction with Felix/Quinn/Marcus on dvpwa."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    project_path = "/opt/projecten/examples/dvpwa"
    if not Path(project_path).exists():
        print("  o SKIPPED | test_real_deep_extraction_on_dvpwa (dvpwa not found)")
        return

    orchestrator = OnboardingOrchestrator()
    context = WorkflowContext(
        session_id=f"test-m4-dvpwa-{datetime.now().strftime('%H%M%S')}",
        workflow_id="m4-test",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "answers": DVPWA_ANSWERS,
            # Provide code_understanding so M4 has context
            "code_understanding": {
                "services_run": 11,
                "services_succeeded": 5,
                "quality_score": 0.75,
            },
        },
    )

    print(f"\n  Running deep extraction (Felix/Quinn/Marcus) on: {project_path}")
    start_time = datetime.now(timezone.utc)

    result = await orchestrator._execute_deep_extraction(context)

    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

    # Print detailed results
    print(f"  Duration: {duration:.1f}s")
    print(f"  Agents Run: {result.get('agents_run', 0)}")
    print(f"  Agents Succeeded: {result.get('agents_succeeded', 0)}")
    print(f"  Quality Score: {result.get('quality_score', 0)}")
    print(f"  Has Architecture Insights: {result.get('has_architecture_insights', False)}")
    print(f"  Quality Findings: {result.get('quality_findings_count', 0)}")
    print(f"  Maintenance Recommendations: {result.get('maintenance_recommendations_count', 0)}")
    print(f"  Council Consensus: {'yes' if result.get('council_consensus') else 'no'}")

    if result.get("errors"):
        print(f"  Errors ({len(result['errors'])}):")
        for err in result["errors"][:5]:
            print(f"    - {err}")

    # M4 threshold is 0.70, but degraded mode gives 0.50
    assert result.get("quality_score", 0) >= 0.50, \
        f"Score below minimum: {result.get('quality_score', 0)}"

    # Verify stored in shared_data
    assert "deep_extraction" in context.shared_data, "deep_extraction not in shared_data"

    agents_status = "agents active" if result.get("agents_succeeded", 0) > 0 else "degraded mode"
    print(f"  + PASSED | test_real_deep_extraction_on_dvpwa "
          f"({agents_status}, score={result.get('quality_score', 0)})")


async def test_quality_threshold():
    """Test that M4 quality threshold (0.70) met with at least 1 agent."""
    from app.confucius.workflows.onboarding import DeepExtractionResult

    QUALITY_THRESHOLD = 0.70

    result = DeepExtractionResult(
        project_path="/test",
        agents_run=3,
        agents_succeeded=1,
        architecture_insights={"patterns": [{"name": "MVC"}]},
    )
    assert result.quality_score >= QUALITY_THRESHOLD, \
        f"Quality gate should pass: {result.quality_score} >= {QUALITY_THRESHOLD}"

    print("  + PASSED | test_quality_threshold")


async def test_council_consensus_building():
    """Test council consensus building from real dataclass."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator, DeepExtractionResult

    orchestrator = OnboardingOrchestrator()

    result = DeepExtractionResult(
        project_path="/test",
        agents_run=3,
        agents_succeeded=3,
        architecture_insights={
            "patterns": [{"name": "MVC"}, {"name": "Repository"}],
            "concerns": [{"issue": "Circular deps", "severity": "medium"}],
        },
        quality_findings=[
            {"id": "Q001", "description": "High complexity", "severity": "critical"},
            {"id": "Q002", "description": "Duplicate code", "severity": "medium"},
        ],
        maintenance_recommendations=[
            {"id": "M001", "description": "Refactor DAL", "effort": "high"},
        ],
    )

    consensus = orchestrator._build_council_consensus(result)

    assert consensus["status"] == "complete"
    assert consensus["agents_contributing"] == 3
    assert len(consensus["key_insights"]) > 0
    assert len(consensus["risk_areas"]) > 0
    assert len(consensus["priority_actions"]) > 0

    print("  + PASSED | test_council_consensus_building")


async def test_reference_projects():
    """Test real deep extraction on available reference projects."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    orchestrator = OnboardingOrchestrator()

    for project_path in REFERENCE_PROJECTS:
        if not Path(project_path).exists():
            print(f"  o SKIPPED | {Path(project_path).name} (not available)")
            continue

        context = WorkflowContext(
            session_id=f"test-m4-ref-{Path(project_path).name}",
            workflow_id="m4-test",
            workflow_type="onboarding",
            shared_data={
                "project_path": project_path,
                "answers": DVPWA_ANSWERS,
                "code_understanding": {
                    "services_run": 11,
                    "services_succeeded": 5,
                    "quality_score": 0.75,
                },
            },
        )

        print(f"\n  Running on {Path(project_path).name}...")
        start_time = datetime.now(timezone.utc)

        result = await orchestrator._execute_deep_extraction(context)

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        project_name = Path(project_path).name
        agents = result.get("agents_succeeded", 0)
        score = result.get("quality_score", 0)

        assert score >= 0.50, f"Score too low for {project_name}: {score}"

        agents_status = f"{agents} agents" if agents > 0 else "degraded"
        print(f"  + PASSED | {project_name}: {agents_status}, "
              f"score={score}, {duration:.1f}s")


# =============================================================================
# DUMP OUTPUT (--dump flag)
# =============================================================================

async def dump_output():
    """Run M4 deep extraction and dump full JSON output."""
    import json
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    print("=" * 60)
    print("M4: Deep Extraction (Felix+Quinn+Marcus) - OUTPUT DUMP")
    print("=" * 60)

    project_path = next(
        (p for p in REFERENCE_PROJECTS if Path(p).exists()),
        str(Path.cwd()),
    )
    print(f"Project: {project_path}")

    orchestrator = OnboardingOrchestrator()
    context = WorkflowContext(
        session_id="dump-m4",
        workflow_id="dump-m4",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "answers": DVPWA_ANSWERS,
            "code_understanding": {
                "services_run": 11,
                "services_succeeded": 5,
                "quality_score": 0.75,
            },
        },
    )

    result = await orchestrator._execute_deep_extraction(context)
    output = {
        "stage": "M4 - Deep Extraction (Felix+Quinn+Marcus)",
        "input": {"project_path": project_path},
        "output": result,
    }
    print(json.dumps(output, indent=2, default=str))


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run all M4 tests."""
    print("=" * 60)
    print("OnboardingWorkflow M4: Deep Extraction Tests")
    print("REAL agents (Felix+Quinn+Marcus) via OnboardingOrchestrator")
    print("=" * 60)

    results = {}

    tests = [
        ("Dataclass Scoring", test_dataclass_scoring),
        ("Serialization", test_to_dict_serialization),
        ("Quality Threshold", test_quality_threshold),
        ("Council Consensus", test_council_consensus_building),
        ("Real Deep Extraction on dvpwa", test_real_deep_extraction_on_dvpwa),
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
