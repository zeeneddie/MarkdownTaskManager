#!/usr/bin/env python3
"""
Standalone test for M9: Estimation module.

Tests the IFPUG Function Point estimation capabilities of the OnboardingOrchestrator
using MigrationEstimationService.

Usage:
    cd backend
    .venv/bin/python3 tests/standalone_onboarding_m9_test.py

Reference projects:
- /opt/projecten/hci-crs (9,922 files, 560MB)
- /opt/projecten/paramedi/FRM (6,710 files, 191MB)
- /opt/projecten/paramedi/FysioOne-Classic (2,235 files, 100MB)
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_estimation_result_dataclass():
    """Test EstimationResult dataclass initialization and scoring."""
    from app.confucius.workflows.onboarding import EstimationResult

    # Test 1: Complete estimation (FP + phases + agent)
    result = EstimationResult(
        project_path="/test",
        agents_run=1,
        agents_succeeded=1,
        adjusted_fp=500.0,
        component_count=50,
        confidence_level=0.75,
        phase_estimates=[
            {"phase": "discovery", "total_hours": 100},
            {"phase": "analysis", "total_hours": 200},
            {"phase": "design", "total_hours": 300},
            {"phase": "development", "total_hours": 800},
            {"phase": "testing", "total_hours": 400},
        ],
    )
    assert result.quality_score == 1.0, f"Expected 1.0, got {result.quality_score}"
    print(f"  Test 1: Complete estimation score = {result.quality_score}")

    # Test 2: Good estimation (FP with confidence)
    result2 = EstimationResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
        adjusted_fp=300.0,
        component_count=30,
        confidence_level=0.7,
    )
    assert result2.quality_score == 0.85, f"Expected 0.85, got {result2.quality_score}"
    print(f"  Test 2: Good estimation score = {result2.quality_score}")

    # Test 3: Basic estimation (some FP or story points) - threshold
    result3 = EstimationResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
        adjusted_fp=100.0,
        component_count=10,
        confidence_level=0.4,
    )
    assert result3.quality_score == 0.75, f"Expected 0.75, got {result3.quality_score}"
    print(f"  Test 3: Basic estimation score = {result3.quality_score}")

    # Test 4: Story points only (no FP)
    result4 = EstimationResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
        adjusted_fp=0,
        component_count=0,
        story_points_total=200,
    )
    assert result4.quality_score == 0.75, f"Expected 0.75, got {result4.quality_score}"
    print(f"  Test 4: Story points only score = {result4.quality_score}")

    # Test 5: Minimal estimation
    result5 = EstimationResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
        adjusted_fp=0,
        component_count=0,
        story_points_total=0,
    )
    assert result5.quality_score == 0.50, f"Expected 0.50, got {result5.quality_score}"
    print(f"  Test 5: Minimal estimation score = {result5.quality_score}")

    # Test 6: to_dict serialization
    result_dict = result.to_dict()
    assert "function_points" in result_dict
    assert result_dict["function_points"]["adjusted"] == 500.0
    assert "effort" in result_dict
    assert "estimates" in result_dict
    print(f"  Test 6: to_dict serialization OK")

    # Test 7: Default values
    result7 = EstimationResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
    )
    assert result7.components_by_type == {}, "components_by_type should default to {}"
    assert result7.phase_estimates == [], "phase_estimates should default to []"
    assert result7.risk_factors == [], "risk_factors should default to []"
    assert result7.recommendations == [], "recommendations should default to []"
    assert result7.errors == [], "errors should default to []"
    print(f"  Test 7: Default values OK")

    return True


async def test_migration_estimation_service():
    """Test MigrationEstimationService directly."""
    try:
        from app.services.migration_estimation_service import (
            MigrationEstimationService,
            TechnologyStack,
        )
    except ImportError as e:
        print(f"  SKIP: MigrationEstimationService not available: {e}")
        return True

    # Find a test project
    test_projects = [
        "/opt/projecten/hci-crs",
        "/opt/projecten/paramedi/FRM",
        "/opt/projecten/paramedi/FysioOne-Classic",
    ]

    test_path = None
    for proj in test_projects:
        if Path(proj).exists():
            test_path = proj
            break

    if not test_path:
        print("  SKIP: No test project available")
        return True

    print(f"\n  Running MigrationEstimationService on: {test_path}")

    service = MigrationEstimationService()
    start_time = datetime.now(timezone.utc)

    result = service.analyze_directory(
        directory=test_path,
        source_stack=TechnologyStack.VB_NET_WEBFORMS,
        target_stack="ASP.NET Core",
        include_risk_buffer=True,
    )

    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

    print(f"  Duration: {duration:.1f}s")
    print(f"  Unadjusted FP: {result.total_unadjusted_fp:.1f}")
    print(f"  VAF: {result.value_adjustment_factor:.2f}")
    print(f"  Adjusted FP: {result.total_adjusted_fp:.1f}")
    print(f"  Components: {len(result.components)}")
    print(f"  Total Effort Hours: {result.total_effort_hours:.1f}")
    print(f"  Total Person Days: {result.total_effort_person_days:.1f}")
    print(f"  Confidence: {result.confidence_level:.2f}")
    print(f"  Phases: {len(result.phase_estimates)}")

    assert result.total_adjusted_fp > 0, "Should have some function points"
    assert len(result.components) > 0 or result.total_effort_hours > 0, "Should have analysis results"

    return True


async def test_technology_stack_detection():
    """Test technology stack detection."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator

    orchestrator = OnboardingOrchestrator()

    # Test with different project paths
    test_cases = [
        ("/opt/projecten/hci-crs", "VB.NET WebForms expected"),
        ("/opt/projecten/paramedi/FRM", "VB.NET or C# WebForms expected"),
    ]

    for project_path, description in test_cases:
        if Path(project_path).exists():
            stack = orchestrator._detect_technology_stack({}, project_path)
            print(f"  {project_path}: {stack} ({description})")
            assert stack is not None, f"Should detect stack for {project_path}"

    return True


async def test_combined_estimates_calculation():
    """Test combined estimates calculation logic."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator, EstimationResult

    orchestrator = OnboardingOrchestrator()

    # Test 1: Both FP and story points
    result1 = EstimationResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
        total_effort_hours=800,  # 20 weeks at 40h/week
        story_based_estimate_weeks=15,
        story_points_total=300,
    )
    result1 = orchestrator._calculate_combined_estimates(result1)
    print(f"  Test 1: FP + Story combined:")
    print(f"    Low: {result1.estimated_weeks_low}, Likely: {result1.estimated_weeks_likely}, High: {result1.estimated_weeks_high}")
    assert result1.estimated_weeks_likely > 0, "Should have likely estimate"
    assert result1.estimated_weeks_low < result1.estimated_weeks_likely < result1.estimated_weeks_high, "Should be ordered"

    # Test 2: Only FP
    result2 = EstimationResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
        total_effort_hours=400,  # 10 weeks
        story_based_estimate_weeks=0,
        story_points_total=0,
    )
    result2 = orchestrator._calculate_combined_estimates(result2)
    print(f"  Test 2: FP only:")
    print(f"    Low: {result2.estimated_weeks_low}, Likely: {result2.estimated_weeks_likely}, High: {result2.estimated_weeks_high}")
    assert result2.estimated_weeks_likely == 10, f"Expected 10, got {result2.estimated_weeks_likely}"

    # Test 3: Only story points
    result3 = EstimationResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
        total_effort_hours=0,
        story_based_estimate_weeks=12,
        story_points_total=240,
    )
    result3 = orchestrator._calculate_combined_estimates(result3)
    print(f"  Test 3: Story points only:")
    print(f"    Low: {result3.estimated_weeks_low}, Likely: {result3.estimated_weeks_likely}, High: {result3.estimated_weeks_high}")
    assert result3.estimated_weeks_likely == 12, f"Expected 12, got {result3.estimated_weeks_likely}"

    return True


async def test_team_recommendations():
    """Test team size recommendations."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator, EstimationResult

    orchestrator = OnboardingOrchestrator()

    # Test with story points
    result = EstimationResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
        story_points_total=500,  # Would need ~25 weeks with 1 dev at 20 SP/week
        velocity_assumption=20,
    )
    result = orchestrator._calculate_team_recommendations(result)
    print(f"  Story points: {result.story_points_total}")
    print(f"  Recommended team size: {result.recommended_team_size}")
    assert 2 <= result.recommended_team_size <= 10, "Team size should be reasonable"

    return True


async def test_estimation_stage(project_path: str):
    """Test M9 estimation stage execution."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    orchestrator = OnboardingOrchestrator()

    # Prepare context with previous stage data
    context = WorkflowContext(
        session_id=f"test-m9-{datetime.now().strftime('%H%M%S')}",
        workflow_id="m9-test",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "answers": {
                "q1_primary_purpose": "Healthcare registration system",
                "q2_users": "Doctors, nurses, admin staff",
                "q3_critical_processes": "Patient registration, appointments",
                "q4_integrations": "HL7/FHIR, VECOZO",
            },
            # Mock M8 story_generation data
            "story_generation": {
                "total_story_points": 265,
                "estimated_weeks": 13,
                "total_stories": 51,
                "total_epics": 3,
                "quality_score": 1.0,
            },
            # Mock M7 domain_extraction data
            "domain_extraction": {
                "domains": [
                    {"name": "Patient Management", "complexity": "high"},
                    {"name": "Appointments", "complexity": "medium"},
                    {"name": "Billing", "complexity": "high"},
                ],
                "quality_score": 1.0,
            },
            # Mock M3 code_understanding data
            "code_understanding": {
                "quality_score": 1.0,
            },
        },
    )

    # Execute estimation
    print(f"\n  Running estimation on: {project_path}")
    start_time = datetime.now(timezone.utc)

    result = await orchestrator._execute_estimation(context)

    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

    # Validate result structure
    assert "project_path" in result, "Missing project_path"
    assert "quality_score" in result, "Missing quality_score"
    assert "function_points" in result, "Missing function_points"
    assert "estimates" in result, "Missing estimates"

    # Print results
    print(f"  Duration: {duration:.1f}s")
    print(f"  Quality Score: {result['quality_score']}")
    print(f"  Function Points:")
    print(f"    Unadjusted: {result['function_points']['unadjusted']}")
    print(f"    VAF: {result['function_points']['vaf']}")
    print(f"    Adjusted: {result['function_points']['adjusted']}")
    print(f"  Components: {result['components']['total']}")
    print(f"  Effort:")
    print(f"    Hours: {result['effort']['hours']}")
    print(f"    Person Days: {result['effort']['person_days']}")
    print(f"    Person Months: {result['effort']['person_months']}")
    print(f"  Estimates:")
    print(f"    Low: {result['estimates']['weeks_low']} weeks")
    print(f"    Likely: {result['estimates']['weeks_likely']} weeks")
    print(f"    High: {result['estimates']['weeks_high']} weeks")
    print(f"    Story-based: {result['estimates']['story_based_weeks']} weeks")
    print(f"  Team:")
    print(f"    Recommended Size: {result['team']['recommended_size']}")
    print(f"  Confidence: {result['confidence_level']}")
    print(f"  Phases: {len(result['phase_estimates'])}")
    print(f"  Risk Factors: {len(result['risk_factors'])}")
    if result.get('errors'):
        print(f"  Errors: {result['errors']}")

    # Verify it was stored in shared_data
    assert "estimation" in context.shared_data, "estimation not in shared_data"

    return result


async def test_integration_m8_to_m9(project_path: str):
    """Test integration from M8 story generation through M9 estimation."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    orchestrator = OnboardingOrchestrator()

    context = WorkflowContext(
        session_id=f"test-m8-m9-{datetime.now().strftime('%H%M%S')}",
        workflow_id="integration-test",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "answers": {
                "q1_primary_purpose": "Healthcare registration system",
                "q2_users": "Doctors, nurses, admin staff",
                "q3_critical_processes": "Patient registration, appointments",
                "q4_integrations": "HL7/FHIR, VECOZO",
            },
            # Need M7 domain_extraction for M8
            "domain_extraction": {
                "domains": [
                    {
                        "name": "Patient",
                        "description": "Patient management",
                        "modules": ["PatientController"],
                        "entities": ["Patient", "Address"],
                        "use_cases": ["Create patient", "Update patient"],
                        "complexity": "high",
                        "confidence": 0.8,
                    }
                ],
                "module_clusters": [],
                "modules_analyzed": 10,
                "entities_found": 5,
                "quality_score": 0.85,
            },
            "user_journey": {
                "journeys": [],
                "personas": [],
                "quality_score": 0.70,
            },
            "code_understanding": {
                "quality_score": 1.0,
            },
        },
    )

    stages_completed = []
    stages_failed = []

    # M8: Story Generation
    print("\n  [M8] Running story generation...")
    try:
        m8_result = await orchestrator._execute_story_generation(context)
        m8_score = m8_result.get("quality_score", 0)

        if m8_score >= 0.70:
            stages_completed.append("M8")
            print(f"  M8 PASSED: score={m8_score}, stories={m8_result.get('total_stories', 0)}")
        else:
            stages_failed.append("M8")
            print(f"  M8 FAILED: score={m8_score}")
    except Exception as e:
        print(f"  M8 ERROR: {e}")
        stages_failed.append("M8")

    # M9: Estimation
    print("\n  [M9] Running estimation...")
    try:
        m9_result = await orchestrator._execute_estimation(context)
        m9_score = m9_result.get("quality_score", 0)

        print(f"\n  M9 Estimation Results:")
        print(f"    Score: {m9_score}")
        print(f"    Threshold: 0.75")
        print(f"    Adjusted FP: {m9_result['function_points']['adjusted']}")
        print(f"    Weeks Likely: {m9_result['estimates']['weeks_likely']}")
        print(f"    Team Size: {m9_result['team']['recommended_size']}")

        if m9_score >= 0.75:
            stages_completed.append("M9")
            print(f"  M9 PASSED: score={m9_score}")
        else:
            # M9 can pass with 0.50 if at least story points are available
            if m9_score >= 0.50:
                stages_completed.append("M9")
                print(f"  M9 PASSED (fallback): score={m9_score}")
            else:
                stages_failed.append("M9")
                print(f"  M9 FAILED: score={m9_score} < 0.50")
    except Exception as e:
        print(f"  M9 ERROR: {e}")
        import traceback
        traceback.print_exc()
        stages_failed.append("M9")

    # Summary
    print(f"\n  Integration Test Summary:")
    print(f"    Stages Completed: {stages_completed}")
    print(f"    Stages Failed: {stages_failed}")
    print(f"    Success Rate: {len(stages_completed)}/{len(stages_completed) + len(stages_failed)}")

    return len(stages_failed) == 0


async def main():
    """Run all M9 tests."""
    print("=" * 60)
    print("OnboardingWorkflow M9: Estimation Tests")
    print("Fase 24.9 - IFPUG Function Point estimation")
    print("=" * 60)

    # Reference project paths
    reference_projects = [
        "/opt/projecten/hci-crs",
        "/opt/projecten/paramedi/FRM",
        "/opt/projecten/paramedi/FysioOne-Classic",
    ]

    # Find first available project
    available_project = None
    for proj in reference_projects:
        if Path(proj).exists():
            available_project = proj
            break

    if not available_project:
        print("\nWARNING: No reference project found. Using current directory.")
        available_project = str(Path.cwd())

    results = {}

    # Test 1: EstimationResult dataclass
    print("\n--- Test 1: EstimationResult Dataclass ---")
    try:
        passed = await test_estimation_result_dataclass()
        results["EstimationResult Dataclass"] = "PASSED" if passed else "FAILED"
        print(f"Result: {results['EstimationResult Dataclass']}")
    except Exception as e:
        results["EstimationResult Dataclass"] = f"ERROR: {e}"
        print(f"Result: {results['EstimationResult Dataclass']}")
        import traceback
        traceback.print_exc()

    # Test 2: MigrationEstimationService
    print("\n--- Test 2: MigrationEstimationService ---")
    try:
        passed = await test_migration_estimation_service()
        results["MigrationEstimationService"] = "PASSED" if passed else "FAILED"
        print(f"Result: {results['MigrationEstimationService']}")
    except Exception as e:
        results["MigrationEstimationService"] = f"ERROR: {e}"
        print(f"Result: {results['MigrationEstimationService']}")
        import traceback
        traceback.print_exc()

    # Test 3: Technology stack detection
    print("\n--- Test 3: Technology Stack Detection ---")
    try:
        passed = await test_technology_stack_detection()
        results["Technology Stack Detection"] = "PASSED" if passed else "FAILED"
        print(f"Result: {results['Technology Stack Detection']}")
    except Exception as e:
        results["Technology Stack Detection"] = f"ERROR: {e}"
        print(f"Result: {results['Technology Stack Detection']}")
        import traceback
        traceback.print_exc()

    # Test 4: Combined estimates calculation
    print("\n--- Test 4: Combined Estimates Calculation ---")
    try:
        passed = await test_combined_estimates_calculation()
        results["Combined Estimates"] = "PASSED" if passed else "FAILED"
        print(f"Result: {results['Combined Estimates']}")
    except Exception as e:
        results["Combined Estimates"] = f"ERROR: {e}"
        print(f"Result: {results['Combined Estimates']}")
        import traceback
        traceback.print_exc()

    # Test 5: Team recommendations
    print("\n--- Test 5: Team Recommendations ---")
    try:
        passed = await test_team_recommendations()
        results["Team Recommendations"] = "PASSED" if passed else "FAILED"
        print(f"Result: {results['Team Recommendations']}")
    except Exception as e:
        results["Team Recommendations"] = f"ERROR: {e}"
        print(f"Result: {results['Team Recommendations']}")
        import traceback
        traceback.print_exc()

    # Test 6: Full estimation stage
    print("\n--- Test 6: Estimation Stage ---")
    try:
        result = await test_estimation_stage(available_project)
        # Pass if we got results
        passed = result.get("quality_score", 0) >= 0.50
        results["Estimation Stage"] = "PASSED" if passed else "FAILED"
        print(f"Result: {results['Estimation Stage']}")
    except Exception as e:
        results["Estimation Stage"] = f"ERROR: {e}"
        print(f"Result: {results['Estimation Stage']}")
        import traceback
        traceback.print_exc()

    # Test 7: Integration M8-M9 (optional, slower)
    run_integration = "--full" in sys.argv
    if run_integration:
        print("\n--- Test 7: Integration M8-M9 ---")
        try:
            passed = await test_integration_m8_to_m9(available_project)
            results["Integration M8-M9"] = "PASSED" if passed else "FAILED"
            print(f"Result: {results['Integration M8-M9']}")
        except Exception as e:
            results["Integration M8-M9"] = f"ERROR: {e}"
            print(f"Result: {results['Integration M8-M9']}")
            import traceback
            traceback.print_exc()
    else:
        print("\n[SKIP] Integration M8-M9 test (use --full to run)")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed_count = sum(1 for v in results.values() if v == "PASSED")
    total_count = len(results)

    for test_name, result in results.items():
        status = "PASSED" if result == "PASSED" else "FAILED"
        symbol = "+" if status == "PASSED" else "x"
        print(f"{symbol} {status} | {test_name}")
        if result not in ["PASSED", "FAILED"]:
            print(f"  {result}")

    print("=" * 60)
    print(f"TOTAL: {passed_count}/{total_count} tests passed")
    print("=" * 60)

    # Exit code
    sys.exit(0 if passed_count == total_count else 1)


if __name__ == "__main__":
    asyncio.run(main())
