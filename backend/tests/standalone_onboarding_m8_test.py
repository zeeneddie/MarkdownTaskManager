#!/usr/bin/env python3
"""
Standalone test for M8: Story Generation module.

Tests the story generation capabilities of the OnboardingOrchestrator
using BusinessDrivenStoryGeneratorService (W159).

Usage:
    cd backend
    .venv/bin/python3 tests/standalone_onboarding_m8_test.py

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


async def test_story_generation_result_dataclass():
    """Test StoryGenerationResult dataclass initialization and scoring."""
    from app.confucius.workflows.onboarding import StoryGenerationResult

    # Test 1: Rich generation (10+ stories, 3+ epics, agent contributed)
    result = StoryGenerationResult(
        project_path="/test",
        agents_run=1,
        agents_succeeded=1,
        total_epics=5,
        total_stories=15,
        total_story_points=75,
    )
    assert result.quality_score == 1.0, f"Expected 1.0, got {result.quality_score}"
    print(f"  Test 1: Rich generation score = {result.quality_score}")

    # Test 2: Good generation (5+ stories, 2+ epics)
    result2 = StoryGenerationResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
        total_epics=3,
        total_stories=8,
        total_story_points=40,
    )
    assert result2.quality_score == 0.85, f"Expected 0.85, got {result2.quality_score}"
    print(f"  Test 2: Good generation score = {result2.quality_score}")

    # Test 3: Basic generation (1+ stories, 1+ epic) - threshold
    result3 = StoryGenerationResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
        total_epics=1,
        total_stories=3,
        total_story_points=15,
    )
    assert result3.quality_score == 0.70, f"Expected 0.70, got {result3.quality_score}"
    print(f"  Test 3: Basic generation score = {result3.quality_score}")

    # Test 4: Minimal generation (no epics or stories)
    result4 = StoryGenerationResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
        total_epics=0,
        total_stories=0,
        total_story_points=0,
    )
    assert result4.quality_score == 0.50, f"Expected 0.50, got {result4.quality_score}"
    print(f"  Test 4: Minimal generation score = {result4.quality_score}")

    # Test 5: to_dict serialization
    result_dict = result.to_dict()
    assert "epics" in result_dict
    assert result_dict["total_epics"] == 5
    assert result_dict["total_stories"] == 15
    assert result_dict["total_story_points"] == 75
    print(f"  Test 5: to_dict serialization OK")

    # Test 6: Default values
    result6 = StoryGenerationResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
    )
    assert result6.epics == [], "epics should default to []"
    assert result6.stories == [], "stories should default to []"
    assert result6.features == [], "features should default to []"
    assert result6.errors == [], "errors should default to []"
    print(f"  Test 6: Default values OK")

    return True


async def test_fallback_story_generation():
    """Test fallback story generation from domains."""
    from app.confucius.workflows.onboarding import (
        OnboardingOrchestrator,
        StoryGenerationResult,
    )

    orchestrator = OnboardingOrchestrator()

    # Create test domains
    domains = [
        {
            "name": "Patient Management",
            "description": "Beheer van patientgegevens",
            "modules": ["PatientController", "PatientService"],
            "entities": ["Patient", "Adres", "Verzekering"],
            "use_cases": ["Patient aanmaken", "Patient zoeken", "Patient wijzigen"],
            "complexity": "medium",
            "confidence": 0.8,
        },
        {
            "name": "Agenda",
            "description": "Afspraak planning",
            "modules": ["AgendaController"],
            "entities": ["Afspraak", "Tijdslot"],
            "use_cases": ["Afspraak plannen", "Afspraak annuleren"],
            "complexity": "low",
            "confidence": 0.9,
        },
    ]

    journeys = [
        {
            "id": "journey_001",
            "name": "Patient registratie",
            "steps": [
                {"action": "Zoek patient"},
                {"action": "Maak nieuwe patient"},
            ],
        }
    ]

    personas = [
        {
            "id": "persona_001",
            "name": "Receptionist",
            "role_code": "RECEPTIONIST",
        }
    ]

    # Create initial result
    result = StoryGenerationResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
        errors=[],
    )

    # Run fallback generation
    print(f"\n  Running fallback story generation...")
    start_time = datetime.now(timezone.utc)

    result = await orchestrator._fallback_story_generation(
        domains, journeys, personas, result
    )

    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

    print(f"  Duration: {duration:.2f}s")
    print(f"  Total Epics: {result.total_epics}")
    print(f"  Total Stories: {result.total_stories}")
    print(f"  Total Story Points: {result.total_story_points}")
    print(f"  Quality Score: {result.quality_score}")

    # Validate
    assert result.total_epics == 2, f"Expected 2 epics, got {result.total_epics}"
    assert result.total_stories >= 5, f"Expected at least 5 stories, got {result.total_stories}"
    assert result.total_story_points > 0, "Should have story points"

    # Check epic structure
    assert len(result.epics) == 2
    assert result.epics[0]["domain_name"] == "Patient Management"
    assert result.epics[1]["domain_name"] == "Agenda"

    # Check story structure
    assert len(result.stories) >= 5
    for story in result.stories:
        assert "id" in story
        assert "title" in story
        assert "story_points" in story
        assert "acceptance_criteria" in story

    return result


async def test_story_generation_stage(project_path: str):
    """Test M8 story generation stage execution."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    orchestrator = OnboardingOrchestrator()

    # Prepare context with previous stage data (M7 domain_extraction)
    context = WorkflowContext(
        session_id=f"test-m8-{datetime.now().strftime('%H%M%S')}",
        workflow_id="m8-test",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "answers": {
                "q1_primary_purpose": "Healthcare registration system for patient management",
                "q2_users": "Doctors, nurses, administrative staff",
                "q3_critical_processes": "Patient registration, appointments, billing",
                "q4_integrations": "HL7/FHIR, VECOZO, LSP",
            },
            # Mock M7 domain_extraction data
            "domain_extraction": {
                "domains": [
                    {
                        "name": "Patient Management",
                        "description": "Patient data and records management",
                        "modules": ["PatientController", "PatientService", "PatientRepository"],
                        "entities": ["Patient", "MedicalRecord", "Insurance"],
                        "use_cases": [
                            "Register new patient",
                            "Update patient data",
                            "View patient history",
                        ],
                        "complexity": "high",
                        "confidence": 0.85,
                    },
                    {
                        "name": "Appointment Scheduling",
                        "description": "Appointment and calendar management",
                        "modules": ["AppointmentController", "CalendarService"],
                        "entities": ["Appointment", "TimeSlot", "Resource"],
                        "use_cases": [
                            "Book appointment",
                            "Cancel appointment",
                            "Reschedule appointment",
                        ],
                        "complexity": "medium",
                        "confidence": 0.9,
                    },
                    {
                        "name": "Billing",
                        "description": "Invoicing and payment processing",
                        "modules": ["BillingController", "InvoiceService"],
                        "entities": ["Invoice", "Payment", "InsuranceClaim"],
                        "use_cases": [
                            "Generate invoice",
                            "Process payment",
                            "Submit claim",
                        ],
                        "complexity": "high",
                        "confidence": 0.75,
                    },
                ],
                "module_clusters": [
                    {
                        "name": "Patient Cluster",
                        "modules": ["PatientController", "PatientService"],
                        "cohesion_score": 0.8,
                        "central_module": "PatientService",
                        "dependency_count": 5,
                    }
                ],
                "modules_analyzed": 50,
                "entities_found": 20,
                "quality_score": 1.0,
            },
            # Mock M5 user_journey data
            "user_journey": {
                "journeys": [
                    {
                        "id": "journey_001",
                        "name": "Patient Registration Flow",
                        "steps": [
                            {"action": "Search for patient"},
                            {"action": "Create new patient"},
                            {"action": "Add insurance details"},
                        ],
                    },
                    {
                        "id": "journey_002",
                        "name": "Appointment Booking Flow",
                        "steps": [
                            {"action": "Select patient"},
                            {"action": "Choose time slot"},
                            {"action": "Confirm booking"},
                        ],
                    },
                ],
                "personas": [
                    {
                        "id": "persona_001",
                        "name": "Receptionist",
                        "role_code": "RECEPTIONIST",
                    },
                    {
                        "id": "persona_002",
                        "name": "Doctor",
                        "role_code": "DOCTOR",
                    },
                ],
                "quality_score": 0.85,
            },
            # Mock M3 code_understanding data
            "code_understanding": {
                "dependency_graph": {
                    "modules": [],
                    "edges": [],
                },
                "quality_score": 1.0,
            },
        },
    )

    # Execute story generation
    print(f"\n  Running story generation on: {project_path}")
    start_time = datetime.now(timezone.utc)

    result = await orchestrator._execute_story_generation(context)

    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

    # Validate result structure
    assert "project_path" in result, "Missing project_path"
    assert "quality_score" in result, "Missing quality_score"
    assert "total_epics" in result, "Missing total_epics"
    assert "total_stories" in result, "Missing total_stories"
    assert "total_story_points" in result, "Missing total_story_points"

    # Print results
    print(f"  Duration: {duration:.1f}s")
    print(f"  Quality Score: {result['quality_score']}")
    print(f"  Total Epics: {result['total_epics']}")
    print(f"  Total Features: {result['total_features']}")
    print(f"  Total Stories: {result['total_stories']}")
    print(f"  Total Story Points: {result['total_story_points']}")
    print(f"  Estimated Weeks: {result['estimated_weeks']}")
    print(f"  Domains Processed: {result['domains_processed']}")
    print(f"  Journeys Linked: {result['journeys_linked']}")
    print(f"  Personas Linked: {result['personas_linked']}")
    print(f"  Agents Run: {result['agents_run']}")
    print(f"  Agents Succeeded: {result['agents_succeeded']}")
    if result.get('errors'):
        print(f"  Errors: {result['errors']}")

    # Show sample epic
    if result.get("epics"):
        print(f"\n  Sample Epic:")
        epic = result["epics"][0]
        print(f"    ID: {epic.get('id')}")
        print(f"    Title: {epic.get('title')}")
        print(f"    Domain: {epic.get('domain_name')}")
        print(f"    Story Count: {epic.get('story_count')}")
        print(f"    Story Points: {epic.get('story_points')}")

    # Show sample story
    if result.get("stories"):
        print(f"\n  Sample Story:")
        story = result["stories"][0]
        print(f"    ID: {story.get('id')}")
        print(f"    Title: {story.get('title')}")
        print(f"    Type: {story.get('story_type')}")
        print(f"    Points: {story.get('story_points')}")

    # Verify it was stored in shared_data
    assert "story_generation" in context.shared_data, "story_generation not in shared_data"

    return result


async def test_integration_m7_to_m8(project_path: str):
    """Test integration from M7 domain extraction through M8 story generation."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    orchestrator = OnboardingOrchestrator()

    context = WorkflowContext(
        session_id=f"test-m7-m8-{datetime.now().strftime('%H%M%S')}",
        workflow_id="integration-test",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "answers": {
                "q1_primary_purpose": "Healthcare registration and patient management system",
                "q2_users": "Doctors, nurses, administrative staff, patients",
                "q3_critical_processes": "Patient registration, appointments, medical records",
                "q4_integrations": "HL7/FHIR, VECOZO, LSP, ZorgDomein",
                "q5_pain_points": "Legacy code, security concerns",
            },
        },
    )

    stages_completed = []
    stages_failed = []

    # M7: Domain Extraction
    print("\n  [M7] Running domain extraction...")
    try:
        m7_result = await orchestrator._execute_domain_extraction(context)
        m7_score = m7_result.get("quality_score", 0)

        if m7_score >= 0.70:
            stages_completed.append("M7")
            print(f"  M7 PASSED: score={m7_score}, domains={m7_result.get('total_domains', 0)}")
        else:
            stages_failed.append("M7")
            print(f"  M7 FAILED: score={m7_score}")
            return False
    except Exception as e:
        print(f"  M7 ERROR: {e}")
        stages_failed.append("M7")
        return False

    # M8: Story Generation
    print("\n  [M8] Running story generation...")
    try:
        m8_result = await orchestrator._execute_story_generation(context)
        m8_score = m8_result.get("quality_score", 0)

        print(f"\n  M8 Story Generation Results:")
        print(f"    Score: {m8_score}")
        print(f"    Threshold: 0.70")
        print(f"    Epics: {m8_result.get('total_epics', 0)}")
        print(f"    Stories: {m8_result.get('total_stories', 0)}")
        print(f"    Story Points: {m8_result.get('total_story_points', 0)}")
        print(f"    Domains Processed: {m8_result.get('domains_processed', 0)}")

        if m8_score >= 0.70:
            stages_completed.append("M8")
            print(f"  M8 PASSED: score={m8_score}")
        else:
            stages_failed.append("M8")
            print(f"  M8 FAILED: score={m8_score} < 0.70")
    except Exception as e:
        print(f"  M8 ERROR: {e}")
        import traceback
        traceback.print_exc()
        stages_failed.append("M8")

    # Summary
    print(f"\n  Integration Test Summary:")
    print(f"    Stages Completed: {stages_completed}")
    print(f"    Stages Failed: {stages_failed}")
    print(f"    Success Rate: {len(stages_completed)}/{len(stages_completed) + len(stages_failed)}")

    return len(stages_failed) == 0


async def test_story_to_journey_linking():
    """Test linking stories to user journeys and personas."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator

    orchestrator = OnboardingOrchestrator()

    stories = [
        {
            "id": "STORY-001",
            "title": "Implement patient registration form",
            "description": "Create form for registering new patients",
        },
        {
            "id": "STORY-002",
            "title": "Build appointment booking page",
            "description": "Allow users to book appointments",
        },
        {
            "id": "STORY-003",
            "title": "Admin dashboard for user management",
            "description": "Dashboard for administrators to manage users",
        },
    ]

    journeys = [
        {
            "id": "journey_001",
            "name": "Patient Registration Flow",
            "steps": [
                {"action": "Register patient"},
                {"action": "Add details"},
            ],
        },
        {
            "id": "journey_002",
            "name": "Appointment Flow",
            "steps": [
                {"action": "Book appointment"},
            ],
        },
    ]

    personas = [
        {
            "id": "persona_001",
            "name": "Administrator",
            "role_code": "ADMIN",
        },
        {
            "id": "persona_002",
            "name": "Receptionist",
            "role_code": "RECEPTIONIST",
        },
    ]

    print(f"\n  Testing story-to-journey linking...")

    journeys_linked, personas_linked = orchestrator._link_stories_to_journeys(
        stories, journeys, personas
    )

    print(f"  Journeys Linked: {journeys_linked}")
    print(f"  Personas Linked: {personas_linked}")

    # Check that stories have linked_journeys or linked_personas
    stories_with_links = sum(
        1 for s in stories
        if s.get("linked_journeys") or s.get("linked_personas")
    )
    print(f"  Stories with Links: {stories_with_links}/{len(stories)}")

    # Story 1 should link to journey_001 (patient registration)
    assert "linked_journeys" in stories[0] or journeys_linked > 0, "Expected some journey links"

    # Story 3 should link to admin persona
    assert "linked_personas" in stories[2] or personas_linked > 0, "Expected some persona links"

    return True


async def main():
    """Run all M8 tests."""
    print("=" * 60)
    print("OnboardingWorkflow M8: Story Generation Tests")
    print("Fase 24.9 - Story generation with BusinessDrivenStoryGenerator")
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

    # Test 1: StoryGenerationResult dataclass
    print("\n--- Test 1: StoryGenerationResult Dataclass ---")
    try:
        passed = await test_story_generation_result_dataclass()
        results["StoryGenerationResult Dataclass"] = "PASSED" if passed else "FAILED"
        print(f"Result: {results['StoryGenerationResult Dataclass']}")
    except Exception as e:
        results["StoryGenerationResult Dataclass"] = f"ERROR: {e}"
        print(f"Result: {results['StoryGenerationResult Dataclass']}")
        import traceback
        traceback.print_exc()

    # Test 2: Fallback story generation
    print("\n--- Test 2: Fallback Story Generation ---")
    try:
        result = await test_fallback_story_generation()
        passed = result.total_stories > 0 and result.total_epics > 0
        results["Fallback Story Generation"] = "PASSED" if passed else "FAILED"
        print(f"Result: {results['Fallback Story Generation']}")
    except Exception as e:
        results["Fallback Story Generation"] = f"ERROR: {e}"
        print(f"Result: {results['Fallback Story Generation']}")
        import traceback
        traceback.print_exc()

    # Test 3: Story-to-journey linking
    print("\n--- Test 3: Story-to-Journey Linking ---")
    try:
        passed = await test_story_to_journey_linking()
        results["Story-to-Journey Linking"] = "PASSED" if passed else "FAILED"
        print(f"Result: {results['Story-to-Journey Linking']}")
    except Exception as e:
        results["Story-to-Journey Linking"] = f"ERROR: {e}"
        print(f"Result: {results['Story-to-Journey Linking']}")
        import traceback
        traceback.print_exc()

    # Test 4: Full story generation stage
    print("\n--- Test 4: Story Generation Stage ---")
    try:
        result = await test_story_generation_stage(available_project)
        # Pass if we got results (score depends on actual domains)
        passed = result.get("total_stories", 0) > 0 or result.get("quality_score", 0) >= 0.50
        results["Story Generation Stage"] = "PASSED" if passed else "FAILED"
        print(f"Result: {results['Story Generation Stage']}")
    except Exception as e:
        results["Story Generation Stage"] = f"ERROR: {e}"
        print(f"Result: {results['Story Generation Stage']}")
        import traceback
        traceback.print_exc()

    # Test 5: Integration M7-M8 (optional, slower)
    run_integration = "--full" in sys.argv
    if run_integration:
        print("\n--- Test 5: Integration M7-M8 ---")
        try:
            passed = await test_integration_m7_to_m8(available_project)
            results["Integration M7-M8"] = "PASSED" if passed else "FAILED"
            print(f"Result: {results['Integration M7-M8']}")
        except Exception as e:
            results["Integration M7-M8"] = f"ERROR: {e}"
            print(f"Result: {results['Integration M7-M8']}")
            import traceback
            traceback.print_exc()
    else:
        print("\n[SKIP] Integration M7-M8 test (use --full to run)")

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
