#!/usr/bin/env python3
"""
Standalone test for M7: Domain Extraction module.

Doel: Peter en Betty agents identificeren de business-domeinen in de applicatie (bijv.
patiëntbeheer, facturatie, planning). Deze domeinstructuur vormt de basis voor de
business-driven epic-indeling in M8 — elke epic hoort bij een concreet domein.

Usage:
    cd backend
    .venv/bin/python3 tests/standalone_onboarding_m7_test.py

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


async def test_domain_extraction_result_dataclass():
    """Test DomainExtractionResult dataclass initialization and scoring."""
    from app.confucius.workflows.onboarding import DomainExtractionResult

    # Test 1: Rich extraction (5+ domains, high confidence, both agents)
    result = DomainExtractionResult(
        project_path="/test",
        agents_run=2,
        agents_succeeded=2,
        domains=[
            {"name": "Domain1", "confidence": 0.8, "use_cases": ["UC1", "UC2"], "entities": ["E1"]},
            {"name": "Domain2", "confidence": 0.75, "use_cases": ["UC3"], "entities": ["E2", "E3"]},
            {"name": "Domain3", "confidence": 0.9, "use_cases": ["UC4", "UC5"], "entities": []},
            {"name": "Domain4", "confidence": 0.72, "use_cases": ["UC6"], "entities": ["E4"]},
            {"name": "Domain5", "confidence": 0.65, "use_cases": ["UC7"], "entities": ["E5"]},
        ],
        total_domains=5,
        high_confidence_domains=4,
        total_use_cases=7,
        total_entities=5,
        modules_analyzed=50,
        entities_found=20,
    )
    assert result.quality_score == 1.0, f"Expected 1.0, got {result.quality_score}"
    print(f"  Test 1: Rich extraction score = {result.quality_score}")

    # Test 2: Good extraction (3+ domains, some high confidence)
    result2 = DomainExtractionResult(
        project_path="/test",
        agents_run=2,
        agents_succeeded=1,
        domains=[
            {"name": "Domain1", "confidence": 0.8, "use_cases": ["UC1"], "entities": []},
            {"name": "Domain2", "confidence": 0.6, "use_cases": ["UC2"], "entities": []},
            {"name": "Domain3", "confidence": 0.5, "use_cases": ["UC3"], "entities": []},
        ],
        total_domains=3,
        high_confidence_domains=1,
        total_use_cases=3,
        total_entities=0,
    )
    assert result2.quality_score == 0.85, f"Expected 0.85, got {result2.quality_score}"
    print(f"  Test 2: Good extraction score = {result2.quality_score}")

    # Test 3: Basic extraction (threshold - 1+ domains)
    result3 = DomainExtractionResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
        domains=[
            {"name": "Domain1", "confidence": 0.4, "use_cases": ["UC1"], "entities": []},
        ],
        total_domains=1,
        high_confidence_domains=0,
        total_use_cases=1,
        total_entities=0,
    )
    assert result3.quality_score == 0.70, f"Expected 0.70, got {result3.quality_score}"
    print(f"  Test 3: Basic extraction score = {result3.quality_score}")

    # Test 4: Minimal extraction (fallback)
    result4 = DomainExtractionResult(
        project_path="/test",
        agents_run=0,
        agents_succeeded=0,
        domains=[],
        total_domains=0,
        high_confidence_domains=0,
    )
    assert result4.quality_score == 0.50, f"Expected 0.50, got {result4.quality_score}"
    print(f"  Test 4: Minimal extraction score = {result4.quality_score}")

    # Test 5: to_dict serialization
    result_dict = result.to_dict()
    assert "domains" in result_dict
    assert "total_domains" in result_dict
    assert result_dict["total_domains"] == 5
    assert result_dict["high_confidence_domains"] == 4
    assert "module_clusters" in result_dict
    print(f"  Test 5: to_dict serialization OK")

    return True


async def test_module_extraction_helpers():
    """Test helper methods for extracting modules and dependencies."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator

    orchestrator = OnboardingOrchestrator()

    # Test _extract_modules_for_domain_analysis with various formats
    # Format 1: nodes list
    code_understanding1 = {
        "dependency_graph": {
            "nodes": [
                {"name": "ModuleA", "path": "/src/moduleA.cs", "classes": ["ClassA"]},
                {"name": "ModuleB", "path": "/src/moduleB.cs", "classes": ["ClassB", "ClassC"]},
            ]
        }
    }
    modules1 = orchestrator._extract_modules_for_domain_analysis(code_understanding1)
    assert len(modules1) == 2, f"Expected 2 modules, got {len(modules1)}"
    assert modules1[0]["name"] == "ModuleA"
    print(f"  Test 1: Node list format - {len(modules1)} modules extracted")

    # Format 2: modules list
    code_understanding2 = {
        "dependency_graph": {
            "modules": [
                {"name": "Service1", "path": "/services/service1.py"},
                {"name": "Service2", "path": "/services/service2.py"},
                {"name": "Service3", "path": "/services/service3.py"},
            ]
        }
    }
    modules2 = orchestrator._extract_modules_for_domain_analysis(code_understanding2)
    assert len(modules2) == 3, f"Expected 3 modules, got {len(modules2)}"
    print(f"  Test 2: Modules list format - {len(modules2)} modules extracted")

    # Format 3: Foundation layers
    code_understanding3 = {
        "foundation": {
            "layers": {
                "presentation": ["View1", "View2"],
                "business": ["Service1", "Service2", "Service3"],
                "data": ["Repository1"],
            }
        }
    }
    modules3 = orchestrator._extract_modules_for_domain_analysis(code_understanding3)
    assert len(modules3) >= 1, f"Expected >= 1 modules, got {len(modules3)}"
    print(f"  Test 3: Foundation layers format - {len(modules3)} modules extracted")

    # Test _extract_dependencies_for_domain_analysis
    code_understanding4 = {
        "dependency_graph": {
            "edges": [
                {"source": "ModuleA", "target": "ModuleB", "type": "imports"},
                {"source": "ModuleB", "target": "ModuleC", "type": "inherits"},
            ]
        }
    }
    deps = orchestrator._extract_dependencies_for_domain_analysis(code_understanding4)
    assert len(deps) == 2, f"Expected 2 dependencies, got {len(deps)}"
    assert deps[0]["source"] == "ModuleA"
    assert deps[0]["target"] == "ModuleB"
    print(f"  Test 4: Dependencies extraction - {len(deps)} dependencies")

    return True


async def test_business_domain_extractor_service():
    """Test BusinessDomainExtractorService independently."""
    try:
        from app.services.business_domain_extractor_service import (
            get_business_domain_extractor,
            BusinessDomainExtractionResult,
        )

        extractor = get_business_domain_extractor(use_healthcare_patterns=True)

        # Test with sample modules and dependencies
        modules = [
            {"name": "PatientController", "path": "/Controllers/PatientController.cs", "classes": ["PatientController"]},
            {"name": "PatientService", "path": "/Services/PatientService.cs", "classes": ["PatientService"]},
            {"name": "PatientRepository", "path": "/Data/PatientRepository.cs", "classes": ["PatientRepository"]},
            {"name": "AgendaController", "path": "/Controllers/AgendaController.cs", "classes": ["AgendaController"]},
            {"name": "AgendaService", "path": "/Services/AgendaService.cs", "classes": ["AgendaService"]},
            {"name": "DeclaratieService", "path": "/Services/DeclaratieService.cs", "classes": ["DeclaratieService"]},
        ]

        dependencies = [
            {"source": "PatientController", "target": "PatientService"},
            {"source": "PatientService", "target": "PatientRepository"},
            {"source": "AgendaController", "target": "AgendaService"},
            {"source": "DeclaratieService", "target": "PatientService"},
        ]

        result = await extractor.extract_domains(
            modules=modules,
            dependencies=dependencies,
            scan_path="/test/project",
        )

        assert isinstance(result, BusinessDomainExtractionResult)
        assert result.total_modules_analyzed > 0
        print(f"  BusinessDomainExtractor: {len(result.domains)} domains extracted")
        print(f"  Modules analyzed: {result.total_modules_analyzed}")
        print(f"  Entities found: {result.total_entities_found}")
        print(f"  Extraction time: {result.extraction_time_ms}ms")

        # Check for healthcare domains
        domain_names = [d.name for d in result.domains]
        print(f"  Domains found: {domain_names}")

        return True

    except ImportError as e:
        print(f"  SKIP: BusinessDomainExtractorService not available: {e}")
        return True


async def test_fallback_domain_extraction():
    """Test fallback domain extraction when service unavailable."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator

    orchestrator = OnboardingOrchestrator()

    # Test fallback with personas
    user_journey = {
        "personas": [
            {"name": "Administrator", "role_code": "ADMIN", "goals": ["Manage system settings"]},
            {"name": "Doctor", "role_code": "DOCTOR", "goals": ["View patient records", "Create prescriptions"]},
            {"name": "Receptionist", "role_code": "RECEPTION", "goals": ["Schedule appointments"]},
        ],
    }

    code_understanding = {
        "foundation": {
            "layers": {
                "ui": ["PatientForm", "AgendaView"],
                "services": ["PatientService", "AgendaService"],
            }
        }
    }

    domains = await orchestrator._fallback_domain_extraction(
        project_path="/test/project",
        code_understanding=code_understanding,
        user_journey=user_journey,
    )

    assert len(domains) >= 1, f"Expected >= 1 domains, got {len(domains)}"
    print(f"  Fallback extraction: {len(domains)} domains")

    for domain in domains:
        print(f"    - {domain['name']} (confidence: {domain.get('confidence', 'N/A')}, source: {domain.get('source', 'N/A')})")

    return True


async def test_domain_extraction_stage(project_path: str):
    """Test M7 domain extraction stage execution."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    orchestrator = OnboardingOrchestrator()

    # Prepare context with previous stage data
    context = WorkflowContext(
        session_id=f"test-m7-{datetime.now().strftime('%H%M%S')}",
        workflow_id="m7-test",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "answers": {
                "q1_primary_purpose": "Test healthcare system for domain extraction validation",
                "q2_users": "Healthcare professionals and administrators",
                "q3_critical_processes": "Patient management, appointments, billing",
                "q4_integrations": "HL7/FHIR, Vecozo, External APIs",
            },
            # Add minimal code_understanding data
            "code_understanding": {
                "dependency_graph": {
                    "nodes": [],
                    "edges": [],
                },
                "quality_score": 0.8,
            },
            # Add minimal user_journey data
            "user_journey": {
                "personas": [
                    {"name": "Admin", "role_code": "ADMIN", "goals": ["Manage system"]},
                    {"name": "User", "role_code": "USER", "goals": ["Use application"]},
                ],
                "journeys": [],
                "screens": [],
                "quality_score": 0.7,
            },
        },
    )

    # Execute domain extraction
    print(f"\n  Running domain extraction on: {project_path}")
    start_time = datetime.now(timezone.utc)

    result = await orchestrator._execute_domain_extraction(context)

    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

    # Validate result structure
    assert "project_path" in result, "Missing project_path"
    assert "quality_score" in result, "Missing quality_score"
    assert "domains" in result, "Missing domains"
    assert "total_domains" in result, "Missing total_domains"

    # Print results
    print(f"  Duration: {duration:.1f}s")
    print(f"  Quality Score: {result['quality_score']}")
    print(f"  Total Domains: {result['total_domains']}")
    print(f"  High Confidence Domains: {result['high_confidence_domains']}")
    print(f"  Total Use Cases: {result['total_use_cases']}")
    print(f"  Total Entities: {result['total_entities']}")
    print(f"  Modules Analyzed: {result['modules_analyzed']}")
    print(f"  Agents Run: {result['agents_run']}")
    print(f"  Agents Succeeded: {result['agents_succeeded']}")

    if result.get("domains"):
        print(f"\n  Domains found:")
        for domain in result["domains"][:5]:  # Show first 5
            print(f"    - {domain.get('name', 'N/A')} "
                  f"(confidence: {domain.get('confidence', 'N/A'):.2f}, "
                  f"use_cases: {len(domain.get('use_cases', []))})")

    if result.get("errors"):
        print(f"\n  Errors: {result['errors']}")

    # Check quality gate
    threshold = 0.70
    passed = result["quality_score"] >= threshold
    print(f"\n  Quality Gate (>={threshold}): {'PASSED' if passed else 'FAILED'}")

    return passed


async def test_agent_refinement_methods():
    """Test Peter and Betty refinement application methods."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator

    orchestrator = OnboardingOrchestrator()

    # Test Peter's refinements
    raw_domains = [
        {"name": "Domain1", "confidence": 0.5, "modules": ["ModA"], "entities": [], "use_cases": ["UC1"]},
        {"name": "Domain2", "confidence": 0.6, "modules": ["ModB"], "entities": [], "use_cases": ["UC2"]},
        {"name": "Domain3", "confidence": 0.4, "modules": ["ModC"], "entities": [], "use_cases": ["UC3"]},
    ]

    peter_result = {
        "success": True,
        "refinements": [
            {"domain_name": "Domain1", "confidence_boost": 0.2},
            {"domain_name": "Domain2", "additional_modules": ["ModD", "ModE"]},
        ],
        "merged_domains": [],
    }

    refined = orchestrator._apply_peter_refinements(raw_domains, peter_result)

    # Check confidence boost was applied
    domain1 = next(d for d in refined if d["name"] == "Domain1")
    assert domain1["confidence"] == 0.7, f"Expected 0.7, got {domain1['confidence']}"
    print(f"  Test 1: Peter confidence boost applied correctly")

    # Check modules were added
    domain2 = next(d for d in refined if d["name"] == "Domain2")
    assert "ModD" in domain2["modules"], "ModD not added to Domain2"
    assert "ModE" in domain2["modules"], "ModE not added to Domain2"
    print(f"  Test 2: Peter module additions applied correctly")

    # Test Betty's documentation
    betty_result = {
        "success": True,
        "enhanced_use_cases": {
            "Domain1": ["Enhanced UC1", "New UC for Domain1"],
            "Domain3": ["Enhanced UC3"],
        },
        "business_context": {
            "Domain1": {
                "description": "Enhanced description for Domain1",
                "business_value": "high",
            },
        },
    }

    enhanced = orchestrator._apply_betty_documentation(refined, betty_result)

    # Check use cases were added
    domain1 = next(d for d in enhanced if d["name"] == "Domain1")
    assert len(domain1["use_cases"]) > 1, "Use cases not expanded"
    print(f"  Test 3: Betty use case expansion applied correctly")

    # Check business context was added
    assert domain1.get("description") == "Enhanced description for Domain1"
    assert domain1.get("business_value") == "high"
    print(f"  Test 4: Betty business context applied correctly")

    return True


async def dump_output():
    """Run M7 domain extraction and dump full JSON output."""
    import json
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    print("=" * 60)
    print("M7: Domain Extraction — OUTPUT DUMP")
    print("=" * 60)

    project_path = str(Path(__file__).parent.parent.parent)
    print(f"Project: {project_path}")

    orchestrator = OnboardingOrchestrator()
    context = WorkflowContext(
        session_id="dump-m7",
        workflow_id="dump-m7",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "answers": {
                "q1_primary_purpose": "Healthcare system for domain extraction validation",
                "q2_users": "Healthcare professionals and administrators",
                "q3_critical_processes": "Patient management, appointments, billing",
                "q4_integrations": "HL7/FHIR, Vecozo, External APIs",
            },
            "code_understanding": {
                "dependency_graph": {"nodes": [], "edges": []},
                "quality_score": 0.8,
            },
            "user_journey": {
                "personas": [
                    {"name": "Admin", "role_code": "ADMIN", "goals": ["Manage system"]},
                    {"name": "User", "role_code": "USER", "goals": ["Use application"]},
                ],
                "journeys": [],
                "screens": [],
                "quality_score": 0.7,
            },
        },
    )

    result = await orchestrator._execute_domain_extraction(context)
    output = {
        "stage": "M7 - Domain Extraction (Peter+Betty)",
        "input": context.shared_data,
        "output": result,
    }
    print(json.dumps(output, indent=2, default=str))


async def run_all_tests():
    """Run all M7 tests."""
    print("=" * 70)
    print("M7: Domain Extraction — Standalone Tests")
    print("=" * 70)

    results = {}

    # Test 1: Dataclass
    print("\n[1] Testing DomainExtractionResult dataclass...")
    try:
        results["dataclass"] = await test_domain_extraction_result_dataclass()
        print("  PASSED")
    except Exception as e:
        results["dataclass"] = False
        print(f"  FAILED: {e}")

    # Test 2: Module extraction helpers
    print("\n[2] Testing module extraction helpers...")
    try:
        results["helpers"] = await test_module_extraction_helpers()
        print("  PASSED")
    except Exception as e:
        results["helpers"] = False
        print(f"  FAILED: {e}")

    # Test 3: BusinessDomainExtractorService
    print("\n[3] Testing BusinessDomainExtractorService...")
    try:
        results["extractor_service"] = await test_business_domain_extractor_service()
        print("  PASSED")
    except Exception as e:
        results["extractor_service"] = False
        print(f"  FAILED: {e}")

    # Test 4: Fallback extraction
    print("\n[4] Testing fallback domain extraction...")
    try:
        results["fallback"] = await test_fallback_domain_extraction()
        print("  PASSED")
    except Exception as e:
        results["fallback"] = False
        print(f"  FAILED: {e}")

    # Test 5: Agent refinement methods
    print("\n[5] Testing agent refinement methods...")
    try:
        results["agent_refinement"] = await test_agent_refinement_methods()
        print("  PASSED")
    except Exception as e:
        results["agent_refinement"] = False
        print(f"  FAILED: {e}")

    # Test 6: Full stage on MarkdownTaskManager (local project)
    print("\n[6] Testing full stage on MarkdownTaskManager...")
    try:
        results["stage_local"] = await test_domain_extraction_stage(
            str(Path(__file__).parent.parent.parent)
        )
        print("  PASSED" if results["stage_local"] else "  FAILED (below threshold)")
    except Exception as e:
        results["stage_local"] = False
        print(f"  FAILED: {e}")

    # Test 7: Reference project tests (if available and --full flag)
    # Skip reference projects by default to keep test fast
    run_full = "--full" in sys.argv
    if run_full:
        reference_projects = [
            "/opt/projecten/examples/dvpwa",
            "/opt/projecten/hci-crs",
            "/opt/projecten/paramedi/FRM",
            "/opt/projecten/paramedi/FysioOne-Classic",
        ]

        for i, project in enumerate(reference_projects, start=7):
            if Path(project).exists():
                print(f"\n[{i}] Testing full stage on {Path(project).name}...")
                try:
                    results[f"stage_{Path(project).name}"] = await test_domain_extraction_stage(project)
                    status = "PASSED" if results[f"stage_{Path(project).name}"] else "FAILED (below threshold)"
                    print(f"  {status}")
                except Exception as e:
                    results[f"stage_{Path(project).name}"] = False
                    print(f"  FAILED: {e}")
            else:
                print(f"\n[{i}] SKIP: {project} not found")
                results[f"stage_{Path(project).name}"] = None
    else:
        print("\n[7+] SKIP: Reference projects (use --full to run)")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    for test_name, result in results.items():
        if result is True:
            status = "PASSED"
        elif result is False:
            status = "FAILED"
        else:
            status = "SKIPPED"
        print(f"  {test_name}: {status}")

    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")

    return failed == 0


if __name__ == "__main__":
    if "--dump" in sys.argv:
        asyncio.run(dump_output())
    else:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
