#!/usr/bin/env python3
"""
Full flow test for OnboardingWorkflow M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8 → M9 → M10 → M11.

Tests the complete onboarding pipeline using the actual OnboardingOrchestrator.

Usage:
    cd backend
    .venv/bin/python3 tests/standalone_onboarding_full_flow_test.py
    .venv/bin/python3 tests/standalone_onboarding_full_flow_test.py --hci-crs
"""

import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone
import tempfile

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging to show scanner progress
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Clean output, just the message
    handlers=[logging.StreamHandler(sys.stdout)]
)
# Reduce noise from other loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)


def create_progress_callback():
    """Create a progress callback that prints to console."""
    last_stage = [None]  # Use list to allow modification in closure
    last_item_type = [None]

    def progress_callback(event):
        """Print progress updates to console."""
        stage_changed = last_stage[0] != event.stage
        item_type_changed = last_item_type[0] != event.item_type
        last_stage[0] = event.stage
        last_item_type[0] = event.item_type

        # Print stage header if changed
        if stage_changed:
            print(f"\n      [M{event.stage_index + 1}] {event.stage}: ", end="", flush=True)

        # Print progress indicator
        bar_width = 20
        filled = int(bar_width * event.percentage / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        # Include message (e.g., scanner name or file name) if available
        if event.item_type == "files":
            # File-level progress: show file name from message
            file_info = event.message if event.message else ""
            detail = f"({event.current}/{event.total} files) {file_info}"
            # Print on new line for file progress
            print(f"\r        [{bar}] {event.percentage:.0f}% {detail[:60]}", end="", flush=True)
        else:
            # Scanner or other progress
            detail = f"({event.current}/{event.total} {event.item_type})"
            if event.message:
                if event.message.startswith("Running "):
                    scanner = event.message.replace("Running ", "").rstrip("...")
                    detail = f"({event.current}/{event.total}) {scanner}"
                elif "scanners" not in event.message.lower() and event.message != "complete":
                    detail = f"({event.current}/{event.total}) {event.message}"
            print(f"\r      [M{event.stage_index + 1}] {event.stage}: [{bar}] {event.percentage:.0f}% {detail}", end="", flush=True)

        # Newline when complete
        if event.percentage >= 100:
            print("", flush=True)

    return progress_callback


async def run_full_flow(project_path: str, answers: dict, show_progress: bool = True) -> tuple:
    """Run complete M1-M11 flow using actual orchestrator.

    Returns:
        tuple: (results dict, shared_data dict with all extracted data)
    """
    import json
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    orchestrator = OnboardingOrchestrator()
    session_id = f"full-flow-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    context = WorkflowContext(
        session_id=session_id,
        workflow_id="full-flow-test",
        workflow_type="onboarding",
        shared_data={
            "project_path": project_path,
            "answers": answers,
        },
    )

    # Set up progress callback
    if show_progress:
        context.set_progress_callback(create_progress_callback())

    results = {}
    stages = orchestrator.get_stages()

    print(f"\n  Running {len(stages)} stages on: {project_path}", flush=True)
    print(f"  Stages: {[s.name for s in stages]}", flush=True)

    total_start = datetime.now(timezone.utc)

    for stage in stages:
        stage_start = datetime.now(timezone.utc)
        print(f"\n  [{stage.name}] Starting (threshold: {stage.quality_threshold})...", flush=True)

        try:
            stage_result = await orchestrator.execute_stage(stage, context)

            duration = (datetime.now(timezone.utc) - stage_start).total_seconds()
            score = stage_result.quality_score
            passed = stage_result.passed_quality_gate

            results[stage.name] = {
                "score": score,
                "passed": passed,
                "duration": duration,
                "threshold": stage.quality_threshold,
            }

            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"  [{stage.name}] {status} (score: {score:.2f}, threshold: {stage.quality_threshold}, {duration:.1f}s)", flush=True)

            if not passed:
                print(f"  [{stage.name}] Quality gate failed - stopping flow", flush=True)
                break

        except Exception as e:
            duration = (datetime.now(timezone.utc) - stage_start).total_seconds()
            results[stage.name] = {
                "score": 0,
                "passed": False,
                "duration": duration,
                "threshold": stage.quality_threshold,
                "error": str(e),
            }
            print(f"  [{stage.name}] ✗ ERROR: {e}", flush=True)
            break

    total_duration = (datetime.now(timezone.utc) - total_start).total_seconds()

    # Summary
    print(f"\n  Total duration: {total_duration:.1f}s", flush=True)
    print(f"  Stages completed: {len(results)}/{len(stages)}", flush=True)

    # Save results to JSON file for persistence
    output_file = Path(project_path) / f".marqed-onboarding-{session_id}.json"
    try:
        output_data = {
            "session_id": session_id,
            "project_path": project_path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stages_completed": len(results),
            "total_stages": len(stages),
            "total_duration_seconds": total_duration,
            "stage_results": results,
            "shared_data": context.shared_data,
        }
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"\n  Results saved to: {output_file}", flush=True)
    except Exception as e:
        print(f"\n  Warning: Could not save results: {e}", flush=True)

    return results, context.shared_data


async def test_with_temp_project():
    """Test full flow with a temporary project."""
    print("\n" + "=" * 70, flush=True)
    print("TEST 1: Temporary project (minimal files)", flush=True)
    print("=" * 70, flush=True)

    with tempfile.TemporaryDirectory() as tmp:
        # Create mock healthcare project structure
        tmp_path = Path(tmp)

        # Create directories
        (tmp_path / "Controllers").mkdir()
        (tmp_path / "Services").mkdir()
        (tmp_path / "Models").mkdir()
        (tmp_path / "Views").mkdir()
        (tmp_path / "Security").mkdir()

        # Create sample files
        (tmp_path / "Controllers" / "PatientController.cs").write_text("""
using System;
public class PatientController {
    public void GetPatient(int id) { }
    public void CreatePatient(Patient p) { }
}
""")
        (tmp_path / "Controllers" / "AgendaController.cs").write_text("""
public class AgendaController {
    public void GetAfspraken() { }
}
""")
        (tmp_path / "Controllers" / "AdminController.cs").write_text("""
public class AdminController {
    [Authorize(Roles = "Admin")]
    public void ManageUsers() { }
}
""")
        (tmp_path / "Services" / "PatientService.cs").write_text("""
public class PatientService {
    public Patient FindByBSN(string bsn) { return null; }
}
""")
        (tmp_path / "Services" / "DeclaratieService.cs").write_text("""
public class DeclaratieService {
    public void CreateDeclaratie() { }
    public void SendToVecozo() { }
}
""")
        (tmp_path / "Models" / "Patient.cs").write_text("""
public class Patient {
    public int Id { get; set; }
    public string BSN { get; set; }
    public string Naam { get; set; }
}
""")

        # Create more views/screens for M5 user journey extraction
        (tmp_path / "Views" / "PatientList.aspx").write_text("<%@ Page %><html>Patient List</html>")
        (tmp_path / "Views" / "PatientForm.aspx").write_text("<%@ Page %><html>Patient Form</html>")
        (tmp_path / "Views" / "PatientDetail.aspx").write_text("<%@ Page %><html>Patient Detail</html>")
        (tmp_path / "Views" / "AgendaView.aspx").write_text("<%@ Page %><html>Agenda</html>")
        (tmp_path / "Views" / "AgendaForm.aspx").write_text("<%@ Page %><html>Agenda Form</html>")
        (tmp_path / "Views" / "Dashboard.aspx").write_text("<%@ Page %><html>Dashboard</html>")
        (tmp_path / "Views" / "UserList.aspx").write_text("<%@ Page %><html>User List</html>")
        (tmp_path / "Views" / "RoleManager.aspx").write_text("<%@ Page %><html>Role Manager</html>")
        (tmp_path / "Views" / "DeclaratieOverzicht.aspx").write_text("<%@ Page %><html>Declaratie Overzicht</html>")
        (tmp_path / "Views" / "RapportageView.aspx").write_text("<%@ Page %><html>Rapportage</html>")

        # Security/Auth files for role extraction
        (tmp_path / "Security" / "RoleProvider.cs").write_text("""
public class RoleProvider {
    public static string[] Roles = new[] { "Admin", "User", "Manager", "Doctor", "Receptionist" };
}
""")
        (tmp_path / "Security" / "AuthorizationService.cs").write_text("""
public class AuthorizationService {
    public bool HasRole(string user, string role) { return true; }
    public string[] GetRolesForUser(string user) { return new[] { "User" }; }
}
""")
        (tmp_path / "Security" / "PermissionCheck.cs").write_text("""
public class PermissionCheck {
    public bool CanViewPatient(string role) { return role == "Admin" || role == "Doctor"; }
    public bool CanEditPatient(string role) { return role == "Admin"; }
}
""")

        # Add a clean auth service (no hardcoded credentials)
        (tmp_path / "Services" / "AuthService.cs").write_text("""
public class AuthService {
    private IPasswordValidator _validator;

    public AuthService(IPasswordValidator validator) {
        _validator = validator;
    }

    public bool Login(string user, string pass) {
        return _validator.Validate(user, pass);
    }
}
""")

        answers = {
            "q1_primary_purpose": "Dit is een healthcare registratie systeem voor het beheren van patientgegevens, afspraken en declaraties in ziekenhuizen.",
            "q2_users": "Administratief personeel, artsen, verpleegkundigen en patienten via het portaal.",
            "q3_critical_processes": "Patient registratie, afspraak planning, facturatie en declaratie naar verzekeraars via Vecozo.",
            "q4_integrations": "HL7 FHIR voor patient data, Vecozo voor declaraties, email gateway.",
            "q5_pain_points": "Legacy codebase met technische schuld.",
        }

        results, shared_data = await run_full_flow(tmp, answers)

        # Check all stages passed
        all_passed = all(r.get("passed", False) for r in results.values())
        stages_run = len(results)

        print(f"\n  Result: {'ALL PASSED' if all_passed and stages_run == 11 else 'INCOMPLETE'}", flush=True)

        return all_passed and stages_run == 11


async def test_with_markdowntaskmanager():
    """Test full flow with MarkdownTaskManager (real project)."""
    print("\n" + "=" * 70, flush=True)
    print("TEST 2: MarkdownTaskManager (real project, limited scan)", flush=True)
    print("=" * 70, flush=True)

    project_path = str(Path(__file__).parent.parent.parent)

    answers = {
        "q1_primary_purpose": "MarQed AI Platform - een multi-stack AI agent platform voor automated software development, legacy modernization en project management.",
        "q2_users": "Software developers, architects, project managers die legacy code willen moderniseren.",
        "q3_critical_processes": "Code analysis, security scanning, domain extraction, story generation voor migration planning.",
        "q4_integrations": "ChromaDB vector store, PostgreSQL database, Ollama LLM inference, multiple scanners.",
        "q5_pain_points": "Complex legacy codebases met onbekende dependencies.",
    }

    results, shared_data = await run_full_flow(project_path, answers)

    # Check all stages passed
    all_passed = all(r.get("passed", False) for r in results.values())
    stages_run = len(results)

    print(f"\n  Result: {'ALL PASSED' if all_passed and stages_run == 11 else 'INCOMPLETE'}", flush=True)

    return all_passed and stages_run == 11


async def test_with_hci_crs():
    """Test full flow with HCI-CRS (real healthcare legacy project)."""
    print("\n" + "=" * 70, flush=True)
    print("TEST: HCI-CRS Healthcare Legacy System Analysis", flush=True)
    print("=" * 70, flush=True)

    project_path = "/opt/projecten/hci-crs"

    # Check if project exists
    if not Path(project_path).exists():
        print(f"  ERROR: Project path not found: {project_path}", flush=True)
        return {}, {}, False, 0

    answers = {
        "q1_primary_purpose": "HCI-CRS is een legacy healthcare registratiesysteem voor het beheren van clientgegevens, zorgtrajecten en declaraties in de geestelijke gezondheidszorg (GGZ). Het systeem ondersteunt het volledige zorgproces van intake tot declaratie.",
        "q2_users": "GGZ behandelaren (psychiaters, psychologen, verpleegkundigen), administratief personeel, financiele afdeling, management voor rapportages, en indirect de zorgverzekeraars via declaraties.",
        "q3_critical_processes": "Client registratie en dossiervorming, behandelplan opstellen en bewaken, afspraakplanning en agenda, urenregistratie van behandelaren, DBC/ZZP declaraties naar zorgverzekeraars, rapportages voor management en externe instanties.",
        "q4_integrations": "Vecozo voor declaratie-uitwisseling met zorgverzekeraars, mogelijk EPD/ECD koppelingen, email notificaties, legacy database systemen.",
        "q5_pain_points": "Verouderde ASP.NET WebForms technologie, monolithische architectuur, beperkte testbaarheid, tightly coupled componenten, onduidelijke scheiding van concerns, technische schuld door jaren van ad-hoc aanpassingen.",
    }

    results, shared_data = await run_full_flow(project_path, answers)

    # Check all stages passed
    all_passed = all(r.get("passed", False) for r in results.values())
    stages_run = len(results)

    print(f"\n  Result: {'ALL PASSED' if all_passed and stages_run == 11 else 'INCOMPLETE'}", flush=True)

    # Return detailed results for analysis
    return results, shared_data, all_passed, stages_run


def print_extracted_data(shared_data: dict):
    """Print key extracted data for analysis."""
    import json

    # User Journey
    user_journey = shared_data.get("user_journey", {})
    if user_journey:
        print("\n" + "=" * 70, flush=True)
        print("USER JOURNEY EXTRACTION", flush=True)
        print("=" * 70, flush=True)

        journeys = user_journey.get("journeys", [])
        print(f"\n  Journeys found: {len(journeys)}", flush=True)
        for j in journeys[:5]:
            name = j.get("name", j.get("journey_name", "Unknown"))
            steps = j.get("steps", j.get("step_count", 0))
            if isinstance(steps, list):
                steps = len(steps)
            print(f"    - {name} ({steps} steps)", flush=True)

        personas = user_journey.get("personas", [])
        print(f"\n  Personas found: {len(personas)}", flush=True)
        for p in personas[:5]:
            name = p.get("name", p.get("persona_name", "Unknown"))
            role = p.get("role", p.get("description", ""))[:50]
            print(f"    - {name}: {role}", flush=True)

        flows = user_journey.get("user_flows", user_journey.get("flows", []))
        print(f"\n  User flows found: {len(flows)}", flush=True)
        for f in flows[:5]:
            name = f.get("name", f.get("flow_name", "Unknown"))
            screens = f.get("screens", f.get("screen_count", 0))
            if isinstance(screens, list):
                screens = len(screens)
            print(f"    - {name} ({screens} screens)", flush=True)

    # Security Scan
    security_scan = shared_data.get("security_scan", {})
    if security_scan:
        print("\n" + "=" * 70, flush=True)
        print("SECURITY SCAN RESULTS", flush=True)
        print("=" * 70, flush=True)

        findings = security_scan.get("findings", {})
        print(f"\n  Scanners used: {security_scan.get('scanners_used', [])}", flush=True)
        print(f"  Languages detected: {security_scan.get('languages_detected', [])}", flush=True)
        print(f"\n  Findings:", flush=True)
        print(f"    - Critical: {findings.get('critical', 0)}", flush=True)
        print(f"    - High: {findings.get('high', 0)}", flush=True)
        print(f"    - Medium: {findings.get('medium', 0)}", flush=True)
        print(f"    - Low: {findings.get('low', 0)}", flush=True)
        print(f"    - Total: {findings.get('total', 0)}", flush=True)

        top_critical = security_scan.get("top_critical", [])
        if top_critical:
            print(f"\n  Top Critical Issues:", flush=True)
            for issue in top_critical[:5]:
                rule = issue.get("rule_id", "Unknown")
                loc = issue.get("location", {}).get("file", "Unknown")
                print(f"    - {rule}: {loc}", flush=True)

    # Story Generation (if available)
    story_gen = shared_data.get("story_generation", {})
    if story_gen:
        print("\n" + "=" * 70, flush=True)
        print("STORY GENERATION", flush=True)
        print("=" * 70, flush=True)

        epics = story_gen.get("epics", [])
        print(f"\n  Epics: {len(epics)}", flush=True)
        for e in epics[:5]:
            name = e.get("name", e.get("epic_name", "Unknown"))
            stories = e.get("stories", e.get("story_count", 0))
            if isinstance(stories, list):
                stories = len(stories)
            print(f"    - {name} ({stories} stories)", flush=True)

        total_stories = story_gen.get("total_stories", 0)
        total_sp = story_gen.get("total_story_points", 0)
        print(f"\n  Total stories: {total_stories}", flush=True)
        print(f"  Total story points: {total_sp}", flush=True)

    # Domain Extraction
    domain_ext = shared_data.get("domain_extraction", {})
    if domain_ext:
        print("\n" + "=" * 70, flush=True)
        print("DOMAIN EXTRACTION", flush=True)
        print("=" * 70, flush=True)

        domains = domain_ext.get("domains", domain_ext.get("bounded_contexts", []))
        print(f"\n  Domains/Bounded Contexts: {len(domains)}", flush=True)
        for d in domains[:5]:
            name = d.get("name", "Unknown")
            entities = d.get("entities", d.get("entity_count", 0))
            if isinstance(entities, list):
                entities = len(entities)
            print(f"    - {name} ({entities} entities)", flush=True)


async def main():
    print("=" * 70, flush=True)
    print("OnboardingWorkflow Full Flow Test: M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8 → M9 → M10 → M11", flush=True)
    print("=" * 70, flush=True)

    results = {}

    # Check for HCI-CRS specific test
    run_hci_crs = "--hci-crs" in sys.argv

    if run_hci_crs:
        # Only run HCI-CRS test
        try:
            hci_results, shared_data, all_passed, stages_run = await test_with_hci_crs()
            results["hci_crs"] = all_passed and stages_run == 11

            # Print detailed analysis
            print("\n" + "=" * 70, flush=True)
            print("HCI-CRS DETAILED ANALYSIS", flush=True)
            print("=" * 70, flush=True)

            for stage_name, stage_data in hci_results.items():
                score = stage_data.get("score", 0)
                passed = stage_data.get("passed", False)
                duration = stage_data.get("duration", 0)
                threshold = stage_data.get("threshold", 0)
                error = stage_data.get("error")

                status = "✓" if passed else "✗"
                print(f"\n  {status} {stage_name}:", flush=True)
                print(f"      Score: {score:.2f} / Threshold: {threshold}", flush=True)
                print(f"      Duration: {duration:.1f}s", flush=True)
                if error:
                    print(f"      Error: {error}", flush=True)

            # Print extracted data (user journeys, security, etc.)
            print_extracted_data(shared_data)

        except Exception as e:
            import traceback
            print(f"\n  ERROR: {e}", flush=True)
            traceback.print_exc()
            results["hci_crs"] = False
    else:
        # Test 1: Temp project
        try:
            results["temp_project"] = await test_with_temp_project()
        except Exception as e:
            print(f"\n  ERROR: {e}", flush=True)
            results["temp_project"] = False

        # Test 2: Real project (optional, slower)
        run_real = "--full" in sys.argv
        if run_real:
            try:
                results["markdowntaskmanager"] = await test_with_markdowntaskmanager()
            except Exception as e:
                print(f"\n  ERROR: {e}", flush=True)
                results["markdowntaskmanager"] = False
        else:
            print("\n[SKIP] MarkdownTaskManager test (use --full to run)", flush=True)

    # Summary
    print("\n" + "=" * 70, flush=True)
    print("SUMMARY", flush=True)
    print("=" * 70, flush=True)

    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {test_name}: {status}", flush=True)

    all_passed = all(results.values())
    print(f"\nOverall: {'SUCCESS' if all_passed else 'FAILURE'}", flush=True)

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
