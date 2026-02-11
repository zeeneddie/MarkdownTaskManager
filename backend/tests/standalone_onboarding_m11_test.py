#!/usr/bin/env python3
"""
Standalone test for OnboardingWorkflow M11: Quality Review.

Doel: Finale kwaliteitscontrole over alle pipeline-resultaten. Controleert completeness,
consistentie tussen stages, en of de minimale kwaliteitsdrempels gehaald zijn (threshold 0.90).
Markeert de onboarding als geslaagd of signaleert welke onderdelen herwerk nodig hebben.

Usage:
    cd backend
    .venv/bin/python3 tests/standalone_onboarding_m11_test.py
"""

import sys
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_quality_review_result_dataclass():
    """Test QualityReviewResult dataclass and quality scoring."""
    print("\n[TEST 1] QualityReviewResult dataclass")

    from app.confucius.workflows.onboarding import QualityReviewResult

    # Test 1a: Empty result (minimal score)
    result = QualityReviewResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
    )

    score = result.quality_score
    print(f"  Empty result score: {score:.2f}")
    assert score >= 0.0, f"Score should be >= 0.0, got {score}"
    assert score <= 1.0, f"Score should be <= 1.0, got {score}"

    # Test 1b: Partial checks passed
    result = QualityReviewResult(
        project_path="/test",
        agents_run=1,
        agents_succeeded=1,
        consistency_score=0.85,
        security_compliant=True,
        security_score=0.90,
        estimation_reasonable=True,
        estimation_confidence=0.75,
        documentation_complete=False,
        documentation_score=0.70,
        data_integrity_score=0.85,
    )

    score = result.quality_score
    print(f"  Partial checks score: {score:.2f}")
    assert score >= 0.80, f"Partial checks should score >= 0.80, got {score}"

    # Test 1c: All checks passed
    result = QualityReviewResult(
        project_path="/test",
        agents_run=1,
        agents_succeeded=1,
        consistency_score=0.95,
        security_compliant=True,
        security_score=1.0,
        estimation_reasonable=True,
        estimation_confidence=0.85,
        documentation_complete=True,
        documentation_score=1.0,
        data_integrity_score=0.95,
        blockers=[],
    )

    score = result.quality_score
    print(f"  All checks passed score: {score:.2f}")
    assert score >= 0.95, f"All checks should score >= 0.95, got {score}"

    print("  PASSED: QualityReviewResult dataclass works correctly")
    return True


def test_quality_thresholds():
    """Test quality score thresholds for different scenarios."""
    print("\n[TEST 2] Quality score thresholds")

    from app.confucius.workflows.onboarding import QualityReviewResult

    # Minimal (score ~0.50) - few checks pass
    minimal = QualityReviewResult(
        project_path="/test",
        agents_run=1,
        agents_succeeded=0,
        consistency_score=0.3,
        security_score=0.4,
        estimation_confidence=0.3,
        documentation_score=0.3,
        data_integrity_score=0.4,
    )
    print(f"  Minimal score: {minimal.quality_score:.2f}")

    # Basic (score ~0.70) - 2-3 checks pass
    basic = QualityReviewResult(
        project_path="/test",
        agents_run=1,
        agents_succeeded=0,
        consistency_score=0.85,  # Pass
        security_score=0.85,  # Pass
        estimation_confidence=0.65,  # Pass
        documentation_score=0.5,  # Fail
        data_integrity_score=0.5,  # Fail
    )
    print(f"  Basic score: {basic.quality_score:.2f}")

    # Good (score ~0.90) - most checks pass
    good = QualityReviewResult(
        project_path="/test",
        agents_run=1,
        agents_succeeded=1,
        consistency_score=0.85,
        security_compliant=True,
        security_score=0.90,
        estimation_reasonable=True,
        estimation_confidence=0.70,
        documentation_complete=True,
        documentation_score=0.95,
        data_integrity_score=0.85,
    )
    print(f"  Good score: {good.quality_score:.2f}")

    # Excellent (score ~1.0) - all checks pass, agent approved
    excellent = QualityReviewResult(
        project_path="/test",
        agents_run=1,
        agents_succeeded=1,
        consistency_score=0.95,
        security_compliant=True,
        security_score=1.0,
        estimation_reasonable=True,
        estimation_confidence=0.90,
        documentation_complete=True,
        documentation_score=1.0,
        data_integrity_score=0.95,
        blockers=[],
    )
    print(f"  Excellent score: {excellent.quality_score:.2f}")

    # Verify ordering
    assert minimal.quality_score < basic.quality_score, "Basic should score higher than minimal"
    assert basic.quality_score < good.quality_score, "Good should score higher than basic"
    assert good.quality_score <= excellent.quality_score, "Excellent should score >= good"

    print("  PASSED: Quality thresholds are correctly ordered")
    return True


def test_quality_review_to_dict():
    """Test QualityReviewResult to_dict serialization."""
    print("\n[TEST 3] QualityReviewResult to_dict")

    from app.confucius.workflows.onboarding import QualityReviewResult

    result = QualityReviewResult(
        project_path="/test/project",
        agents_run=1,
        agents_succeeded=1,
        consistency_score=0.85,
        consistency_issues=[{"type": "test", "message": "Test issue"}],
        security_compliant=True,
        security_score=0.90,
        security_issues=["Minor warning"],
        estimation_reasonable=True,
        estimation_confidence=0.75,
        estimation_warnings=["Check assumptions"],
        documentation_complete=True,
        documentation_score=0.95,
        missing_sections=[],
        data_integrity_score=0.88,
        data_issues=[],
        overall_assessment="GOOD: Most checks passed",
        recommendations=["Review security"],
        blockers=[],
        duration_seconds=5.5,
    )

    d = result.to_dict()

    print(f"  Has project_path: {'project_path' in d}")
    print(f"  Has quality_score: {'quality_score' in d}")
    print(f"  Has checks section: {'checks' in d}")
    print(f"  Has assessment section: {'assessment' in d}")

    # Verify structure
    assert d["project_path"] == "/test/project"
    assert d["agents_run"] == 1
    assert d["quality_score"] >= 0.80
    assert "consistency" in d["checks"]
    assert "security" in d["checks"]
    assert "estimation" in d["checks"]
    assert "documentation" in d["checks"]
    assert "data_integrity" in d["checks"]
    assert d["assessment"]["overall"] == "GOOD: Most checks passed"

    print("  PASSED: QualityReviewResult serializes correctly")
    return True


def test_consistency_check():
    """Test consistency check logic."""
    print("\n[TEST 4] Consistency check")

    from app.confucius.workflows.onboarding import OnboardingOrchestrator

    orchestrator = OnboardingOrchestrator()

    # Good consistency
    result = orchestrator._check_consistency(
        validation={"quality_score": 1.0, "valid": True},
        domain_extraction={
            "domains": [
                {"name": "Patient", "description": "Patient domain"},
                {"name": "Scheduling", "description": "Scheduling domain"},
            ]
        },
        story_generation={
            "epics": [
                {"id": "E1", "domain_name": "Patient"},
                {"id": "E2", "domain_name": "Scheduling"},
            ],
            "total_story_points": 50,
            "stories": [{"title": "S1"}],
        },
        estimation={
            "function_points": {"adjusted": 1500},
        },
        user_journey={
            "journeys": [{"name": "J1"}],
            "personas": [{"name": "P1"}],
        },
    )

    print(f"  Consistency score: {result['score']:.2f}")
    print(f"  Issues: {len(result['issues'])}")

    assert result["score"] >= 0.6, f"Good data should have high consistency, got {result['score']}"

    print("  PASSED: Consistency check works correctly")
    return True


def test_security_compliance_check():
    """Test security compliance check logic."""
    print("\n[TEST 5] Security compliance check")

    from app.confucius.workflows.onboarding import OnboardingOrchestrator

    orchestrator = OnboardingOrchestrator()

    # Test 1: No critical findings - compliant
    result = orchestrator._check_security_compliance({
        "findings": {
            "total": 10,
            "critical": 0,
            "high": 3,
        }
    })
    print(f"  No critical - compliant: {result['compliant']}, score: {result['score']:.2f}")
    assert result["compliant"], "No critical findings should be compliant"
    assert result["score"] >= 0.85, f"Score should be high, got {result['score']}"

    # Test 2: Critical findings - not compliant
    result = orchestrator._check_security_compliance({
        "findings": {
            "total": 15,
            "critical": 3,
            "high": 5,
        }
    })
    print(f"  Critical - compliant: {result['compliant']}, score: {result['score']:.2f}")
    assert not result["compliant"], "Critical findings should not be compliant"
    assert len(result["issues"]) > 0, "Should have issues"

    # Test 3: Empty scan
    result = orchestrator._check_security_compliance({})
    print(f"  Empty scan - score: {result['score']:.2f}")
    assert result["score"] >= 0.5, "Empty scan should have partial score"

    print("  PASSED: Security compliance check works correctly")
    return True


def test_estimation_reasonableness_check():
    """Test estimation reasonableness check logic."""
    print("\n[TEST 6] Estimation reasonableness check")

    from app.confucius.workflows.onboarding import OnboardingOrchestrator

    orchestrator = OnboardingOrchestrator()

    # Test 1: Reasonable estimation
    result = orchestrator._check_estimation_reasonableness(
        estimation={
            "function_points": {"adjusted": 2000},
            "confidence_level": 0.75,
            "estimates": {
                "weeks_low": 30,
                "weeks_likely": 45,
                "weeks_high": 70,
            },
        },
        story_generation={"total_story_points": 150},
        code_understanding={"code_metrics": {"total_files": 500}},
    )
    print(f"  Reasonable: {result['reasonable']}, confidence: {result['confidence']:.2f}")
    assert result["reasonable"], "Should be reasonable"
    assert result["confidence"] >= 0.5, f"Confidence should be reasonable, got {result['confidence']}"

    # Test 2: Missing estimates
    result = orchestrator._check_estimation_reasonableness(
        estimation={},
        story_generation={"total_story_points": 0},
        code_understanding={},
    )
    print(f"  Missing - reasonable: {result['reasonable']}, warnings: {len(result['warnings'])}")
    assert not result["reasonable"], "Missing data should not be reasonable"

    print("  PASSED: Estimation reasonableness check works correctly")
    return True


def test_documentation_completeness_check():
    """Test documentation completeness check logic."""
    print("\n[TEST 7] Documentation completeness check")

    from app.confucius.workflows.onboarding import OnboardingOrchestrator

    orchestrator = OnboardingOrchestrator()

    # Test 1: Complete documentation
    result = orchestrator._check_documentation_completeness({
        "files": {"created": 10},
        "sections": {"generated": ["project-summary", "epics", "estimation", "user-journeys", "architecture"]},
    })
    print(f"  Complete: {result['complete']}, score: {result['score']:.2f}")
    assert result["complete"], "Should be complete"
    assert result["score"] >= 0.90, f"Score should be high, got {result['score']}"
    assert len(result["missing"]) == 0, "Should have no missing sections"

    # Test 2: Missing required sections
    result = orchestrator._check_documentation_completeness({
        "files": {"created": 2},
        "sections": {"generated": ["project-summary"]},
    })
    print(f"  Incomplete - complete: {result['complete']}, missing: {result['missing']}")
    assert not result["complete"], "Should not be complete"
    assert len(result["missing"]) > 0, "Should have missing sections"

    print("  PASSED: Documentation completeness check works correctly")
    return True


def test_data_integrity_check():
    """Test data integrity check logic."""
    print("\n[TEST 8] Data integrity check")

    from app.confucius.workflows.onboarding import OnboardingOrchestrator

    orchestrator = OnboardingOrchestrator()

    # Test with valid data
    result = orchestrator._check_data_integrity(
        domain_extraction={
            "domains": [
                {"name": "Patient", "description": "Patient management"},
                {"name": "Billing", "description": "Billing system"},
            ]
        },
        story_generation={
            "epics": [
                {"id": "E1", "title": "Epic 1", "domain_name": "Patient"},
                {"id": "E2", "title": "Epic 2", "domain_name": "Billing"},
            ],
            "stories": [
                {"id": "S1", "title": "Story 1"},
                {"id": "S2", "title": "Story 2"},
            ],
        },
        estimation={
            "phases": [
                {"name": "Discovery", "weeks": 2},
                {"name": "Analysis", "weeks": 4},
                {"name": "Development", "weeks": 10},
                {"name": "Testing", "weeks": 4},
            ],
        },
    )

    print(f"  Integrity score: {result['score']:.2f}")
    print(f"  Issues: {len(result['issues'])}")

    assert result["score"] >= 0.75, f"Valid data should have high integrity, got {result['score']}"

    print("  PASSED: Data integrity check works correctly")
    return True


def test_assessment_generation():
    """Test assessment and recommendation generation."""
    print("\n[TEST 9] Assessment generation")

    from app.confucius.workflows.onboarding import OnboardingOrchestrator, QualityReviewResult

    orchestrator = OnboardingOrchestrator()

    # Test excellent result
    result = QualityReviewResult(
        project_path="/test",
        agents_run=1,
        agents_succeeded=1,
        consistency_score=0.95,
        security_compliant=True,
        security_score=1.0,
        estimation_reasonable=True,
        estimation_confidence=0.85,
        documentation_complete=True,
        documentation_score=1.0,
        data_integrity_score=0.95,
    )

    assessment = orchestrator._generate_assessment(result)
    print(f"  Assessment: {assessment[:50]}...")
    assert "EXCELLENT" in assessment or "GOOD" in assessment, f"High scores should get positive assessment"

    # Test recommendations
    result.consistency_score = 0.6
    result.security_compliant = False
    result.documentation_complete = False
    result.missing_sections = ["epics", "estimation"]

    recommendations = orchestrator._generate_recommendations(result)
    print(f"  Recommendations count: {len(recommendations)}")
    assert len(recommendations) > 0, "Should have recommendations for issues"

    # Test blockers
    result.security_issues = ["5 critical security findings must be resolved"]
    result.consistency_score = 0.3
    result.documentation_score = 0.3
    result.data_integrity_score = 0.3

    blockers = orchestrator._identify_blockers(result)
    print(f"  Blockers count: {len(blockers)}")
    assert len(blockers) > 0, "Should have blockers for severe issues"

    print("  PASSED: Assessment generation works correctly")
    return True


async def test_quality_review_stage_execution():
    """Test full quality review stage execution."""
    print("\n[TEST 10] Quality review stage execution")

    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    orchestrator = OnboardingOrchestrator()

    dvpwa_path = "/opt/projecten/examples/dvpwa"
    project_path = dvpwa_path if Path(dvpwa_path).exists() else tempfile.mkdtemp()

    context = WorkflowContext(
        session_id="m11-test",
        workflow_id="m11-test",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "validation": {"quality_score": 1.0, "valid": True},
            "answers": {
                "q1_primary_purpose": "Damn Vulnerable Python Web Application voor security testing",
                "q2_users": "Security researchers, penetration testers",
                "q3_critical_processes": "SQL query handling, authenticatie, input validatie",
            },
            "intake_context": {"domains": []},
            "code_understanding": {
                "code_metrics": {"total_files": 100, "total_lines": 5000},
            },
            "deep_extraction": {"insights": []},
            "user_journey_extraction": {
                "journeys": [{"name": "Main Flow"}],
                "personas": [{"name": "User"}],
            },
            "security_scan": {
                "findings": {"total": 5, "critical": 0, "high": 2},
            },
            "domain_extraction": {
                "domains": [
                    {"name": "Security", "description": "Security domain"},
                ]
            },
            "story_generation": {
                "epics": [{"id": "E1", "title": "Epic 1", "domain_name": "Security"}],
                "stories": [{"id": "S1", "title": "Fix SQLi"}],
                "total_story_points": 50,
            },
            "estimation": {
                "function_points": {"adjusted": 1000},
                "confidence_level": 0.7,
                "estimates": {
                    "weeks_low": 15,
                    "weeks_likely": 25,
                    "weeks_high": 40,
                },
                "phases": [
                    {"name": "Analysis", "weeks": 5},
                    {"name": "Development", "weeks": 15},
                    {"name": "Testing", "weeks": 5},
                ],
            },
            "deliverables": {
                "files": {"created": 8},
                "sections": {"generated": ["project-summary", "epics", "estimation", "user-journeys"]},
            },
        },
    )

    # Get the quality_review stage
    stages = orchestrator.get_stages()
    quality_stage = None
    for stage in stages:
        if stage.name == "quality_review":
            quality_stage = stage
            break

    if not quality_stage:
        print("  SKIP: Quality review stage not found in orchestrator")
        return True

    print(f"  Stage: {quality_stage.name}")
    print(f"  Threshold: {quality_stage.quality_threshold}")
    print(f"  Depends on: {quality_stage.depends_on}")

    # Execute the stage
    try:
        result = await orchestrator.execute_stage(quality_stage, context)

        print(f"  Quality score: {result.quality_score:.2f}")
        print(f"  Passed gate: {result.passed_quality_gate}")

        # Check result
        review_result = context.shared_data.get("quality_review", {})
        if review_result:
            print(f"  Consistency: {review_result.get('checks', {}).get('consistency', {}).get('score', 'N/A')}")
            print(f"  Security: {review_result.get('checks', {}).get('security', {}).get('compliant', 'N/A')}")
            print(f"  Assessment: {review_result.get('assessment', {}).get('overall', 'N/A')[:40]}...")

        # With our test data, we expect a reasonable score
        assert result.quality_score >= 0.50, f"Should have reasonable score, got {result.quality_score}"

    except Exception as e:
        print(f"  Stage execution error: {e}")
        import traceback
        traceback.print_exc()
        raise

    print("  PASSED: Quality review stage executes correctly")
    return True


async def dump_output():
    """Run M11 quality review and dump full JSON output."""
    import json
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    print("=" * 60)
    print("M11: Quality Review — OUTPUT DUMP")
    print("=" * 60)

    orchestrator = OnboardingOrchestrator()

    dvpwa_path = "/opt/projecten/examples/dvpwa"
    project_path = dvpwa_path if Path(dvpwa_path).exists() else tempfile.mkdtemp()
    print(f"Project: {project_path}")

    context = WorkflowContext(
        session_id="dump-m11",
        workflow_id="dump-m11",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "validation": {"quality_score": 1.0, "valid": True},
            "answers": {
                "q1_primary_purpose": "Damn Vulnerable Python Web Application voor security testing",
                "q2_users": "Security researchers, penetration testers",
                "q3_critical_processes": "SQL query handling, authenticatie",
            },
            "intake_context": {"domains": []},
            "code_understanding": {"code_metrics": {"total_files": 100, "total_lines": 5000}},
            "deep_extraction": {"insights": []},
            "user_journey_extraction": {
                "journeys": [{"name": "Main Flow"}],
                "personas": [{"name": "User"}],
            },
            "security_scan": {"findings": {"total": 5, "critical": 0, "high": 2}},
            "domain_extraction": {
                "domains": [{"name": "Security", "description": "Security domain"}]
            },
            "story_generation": {
                "epics": [{"id": "E1", "title": "Fix SQLi", "domain_name": "Security"}],
                "stories": [{"id": "S1", "title": "Fix SQLi"}],
                "total_story_points": 50,
            },
            "estimation": {
                "function_points": {"adjusted": 1000},
                "confidence_level": 0.7,
                "estimates": {"weeks_low": 15, "weeks_likely": 25, "weeks_high": 40},
                "phases": [
                    {"name": "Analysis", "weeks": 5},
                    {"name": "Development", "weeks": 15},
                    {"name": "Testing", "weeks": 5},
                ],
            },
            "deliverables": {
                "files": {"created": 8},
                "sections": {"generated": ["project-summary", "epics", "estimation"]},
            },
        },
    )

    stages = orchestrator.get_stages()
    quality_stage = next((s for s in stages if s.name == "quality_review"), None)
    if quality_stage:
        result = await orchestrator.execute_stage(quality_stage, context)
        review = context.shared_data.get("quality_review", {})
        output = {
            "stage": "M11 - Quality Review",
            "input": {k: v for k, v in context.shared_data.items() if k != "quality_review"},
            "output": review,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print("ERROR: quality_review stage not found")


async def main():
    print("=" * 70)
    print("OnboardingWorkflow M11: Quality Review Tests")
    print("=" * 70)

    results = {}

    # Run synchronous tests
    sync_tests = [
        ("quality_review_result_dataclass", test_quality_review_result_dataclass),
        ("quality_thresholds", test_quality_thresholds),
        ("result_to_dict", test_quality_review_to_dict),
        ("consistency_check", test_consistency_check),
        ("security_compliance_check", test_security_compliance_check),
        ("estimation_reasonableness_check", test_estimation_reasonableness_check),
        ("documentation_completeness_check", test_documentation_completeness_check),
        ("data_integrity_check", test_data_integrity_check),
        ("assessment_generation", test_assessment_generation),
    ]

    for name, test_func in sync_tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n[TEST] {name}: FAILED - {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    # Run async test
    try:
        results["quality_review_stage_execution"] = await test_quality_review_stage_execution()
    except Exception as e:
        print(f"\n[TEST] quality_review_stage_execution: FAILED - {e}")
        import traceback
        traceback.print_exc()
        results["quality_review_stage_execution"] = False

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "PASSED" if result else "FAILED"
        print(f"  {name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    if "--dump" in sys.argv:
        asyncio.run(dump_output())
    else:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
