#!/usr/bin/env python3
"""
Step-by-step onboarding test for HCI-CRS with per-stage markdown output.

Runs each stage individually, saves results to markdown, and reports timing.
No timeouts are enforced - stages run to completion.

Usage:
    cd backend
    .venv/bin/python3 tests/standalone_onboarding_stepbystep_test.py

    # Run specific stages only:
    .venv/bin/python3 tests/standalone_onboarding_stepbystep_test.py --stages m1,m2,m3

    # Resume from a specific stage (loads checkpoint):
    .venv/bin/python3 tests/standalone_onboarding_stepbystep_test.py --from m8

    # Include plane_export:
    .venv/bin/python3 tests/standalone_onboarding_stepbystep_test.py --plane-export
"""

import json
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

logger = logging.getLogger("stepbystep")

# =============================================================================
# Configuration
# =============================================================================

# Use dvpwa as primary test project, fall back to hci-crs
_DVPWA_PATH = "/opt/projecten/examples/dvpwa"
_HCI_CRS_PATH = "/opt/projecten/hci-crs"
PROJECT_PATH = _DVPWA_PATH if Path(_DVPWA_PATH).exists() else _HCI_CRS_PATH
OUTPUT_DIR = Path(PROJECT_PATH) / ".marqed-stepbystep"

# Answers depend on which project we're using
if PROJECT_PATH == _DVPWA_PATH:
    ANSWERS = {
        "q1_primary_purpose": (
            "Damn Vulnerable Python Web Application - een demonstratie webapplicatie "
            "voor security testing met opzettelijke SQL-injection kwetsbaarheden, "
            "gebouwd op het aiohttp framework met PostgreSQL database"
        ),
        "q2_users": (
            "Security researchers, penetration testers, developers "
            "die web security kwetsbaarheden leren herkennen en beveiligen"
        ),
        "q3_critical_processes": (
            "SQL query verwerking met opzettelijke injection points, "
            "user authenticatie zonder input validatie, database operaties "
            "met raw SQL queries die kwetsbaar zijn voor aanvallen"
        ),
        "q4_integrations": (
            "PostgreSQL database, aiohttp web framework, "
            "Jinja2 template engine, Docker container orchestratie"
        ),
        "q5_pain_points": (
            "Opzettelijke security kwetsbaarheden, geen input sanitization, "
            "raw SQL queries, verouderde dependencies, geen unit tests"
        ),
    }
else:
    ANSWERS = {
        "q1_primary_purpose": (
            "HCI-CRS is een legacy healthcare registratiesysteem voor het beheren van "
            "clientgegevens, zorgtrajecten en declaraties in de geestelijke gezondheidszorg (GGZ). "
            "Het systeem ondersteunt het volledige zorgproces van intake tot declaratie."
        ),
        "q2_users": (
            "GGZ behandelaren (psychiaters, psychologen, verpleegkundigen), administratief "
            "personeel, financiele afdeling, management voor rapportages, en indirect de "
            "zorgverzekeraars via declaraties."
        ),
        "q3_critical_processes": (
            "Client registratie en dossiervorming, behandelplan opstellen en bewaken, "
            "afspraakplanning en agenda, urenregistratie van behandelaren, DBC/ZZP declaraties "
            "naar zorgverzekeraars, rapportages voor management en externe instanties."
        ),
        "q4_integrations": (
            "Vecozo voor declaratie-uitwisseling met zorgverzekeraars, mogelijk EPD/ECD "
            "koppelingen, email notificaties, legacy database systemen."
        ),
        "q5_pain_points": (
            "Verouderde ASP.NET WebForms technologie, monolithische architectuur, beperkte "
            "testbaarheid, tightly coupled componenten, onduidelijke scheiding van concerns, "
            "technische schuld door jaren van ad-hoc aanpassingen."
        ),
    }

# Stage name -> human-readable name + description of what's LLM-heavy
STAGE_INFO = {
    "validate_input":   ("M1: Input Validation",     "CPU-only",        "< 1s"),
    "intake_context":   ("M2: Intake Context",        "Vector DB query", "< 10s"),
    "code_understanding": ("M3: Code Understanding",  "11 services, no LLM", "1-10 min (large codebase)"),
    "deep_extraction":  ("M4: Deep Extraction",       "LLM: Felix+Quinn+Marcus (parallel)", "2-5 min"),
    "user_journey":     ("M5: User Journey",          "LLM: Vicky+Peter (sequential)", "2-5 min"),
    "security_scan":    ("M6: Security Scan",         "Scanners + LLM: Quinn review", "5-30 min (large codebase)"),
    "domain_extraction": ("M7: Domain Extraction",    "LLM: Peter+Betty (parallel)", "2-5 min"),
    "story_generation": ("M8: Story Generation",      "LLM: Peter enrichment", "2-5 min"),
    "estimation":       ("M9: Estimation",            "LLM: Eliza refinement", "1-3 min"),
    "deliverables":     ("M10: Deliverables",         "LLM: Diana enhancement", "1-3 min"),
    "plane_export":     ("Plane Export",              "CPU-only (assembly)", "< 5s"),
    "quality_review":   ("M11: Quality Review",       "LLM: Quinn assessment", "1-3 min"),
}


# =============================================================================
# Markdown writers
# =============================================================================

def write_stage_result_md(
    stage_name: str,
    stage_result,
    duration_seconds: float,
    context_data: dict,
    output_dir: Path,
):
    """Write a markdown file with stage results."""
    info = STAGE_INFO.get(stage_name, (stage_name, "Unknown", "Unknown"))
    human_name, compute_type, expected_time = info

    lines = [
        f"# {human_name}",
        "",
        f"**Stage:** `{stage_name}`",
        f"**Compute:** {compute_type}",
        f"**Expected time:** {expected_time}",
        f"**Actual time:** {duration_seconds:.1f}s ({duration_seconds/60:.1f} min)",
        f"**Quality score:** {stage_result.quality_score:.2f}",
        f"**Passed quality gate:** {'Yes' if stage_result.passed_quality_gate else 'No'}",
        f"**Status:** {stage_result.status.value}",
        "",
    ]

    # Add stage-specific data from shared_data
    stage_data = context_data.get(stage_name, {})
    if isinstance(stage_data, dict):
        lines.extend(_format_stage_data(stage_name, stage_data))

    # Add agent results if present
    agent_results = stage_result.agent_results or {}
    if agent_results:
        lines.extend(["", "## Agent Results", ""])
        for key, value in agent_results.items():
            if key == "quality_score":
                continue  # Already shown above
            if isinstance(value, dict):
                lines.append(f"### {key}")
                lines.append("```json")
                try:
                    lines.append(json.dumps(value, indent=2, default=str)[:3000])
                except (TypeError, ValueError):
                    lines.append(str(value)[:3000])
                lines.append("```")
            elif isinstance(value, list):
                lines.append(f"### {key} ({len(value)} items)")
                for item in value[:10]:
                    lines.append(f"- {str(item)[:200]}")
            else:
                lines.append(f"- **{key}:** {str(value)[:500]}")

    # Errors
    errors = agent_results.get("errors", [])
    if errors:
        lines.extend(["", "## Errors", ""])
        for err in errors:
            lines.append(f"- {err}")

    output_file = output_dir / f"{stage_name}.md"
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info(f"Wrote {output_file}")


def _format_stage_data(stage_name: str, data: dict) -> list:
    """Format stage-specific shared_data into markdown lines."""
    lines = ["## Results", ""]

    if stage_name == "code_understanding":
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total files | {data.get('total_files', 'N/A')} |")
        lines.append(f"| Total lines | {data.get('total_lines', 'N/A')} |")
        lines.append(f"| Languages | {', '.join(data.get('languages', []))} |")
        lines.append(f"| Services run | {data.get('services_run', 'N/A')} |")
        lines.append(f"| Services succeeded | {data.get('services_succeeded', 'N/A')} |")

    elif stage_name == "user_journey":
        journeys = data.get("journeys", [])
        personas = data.get("personas", [])
        lines.append(f"**Journeys found:** {len(journeys)}")
        for j in journeys[:10]:
            name = j.get("name", j.get("journey_name", "Unknown"))
            steps = j.get("steps", j.get("step_count", 0))
            if isinstance(steps, list):
                steps = len(steps)
            lines.append(f"- {name} ({steps} steps)")
        lines.append(f"\n**Personas found:** {len(personas)}")
        for p in personas[:10]:
            name = p.get("name", p.get("persona_name", "Unknown"))
            role = p.get("role", p.get("description", ""))[:80]
            lines.append(f"- **{name}**: {role}")

    elif stage_name == "security_scan":
        findings = data.get("findings", {})
        lines.append(f"| Severity | Count |")
        lines.append(f"|----------|-------|")
        lines.append(f"| Critical | {findings.get('critical', 0)} |")
        lines.append(f"| High | {findings.get('high', 0)} |")
        lines.append(f"| Medium | {findings.get('medium', 0)} |")
        lines.append(f"| Low | {findings.get('low', 0)} |")
        lines.append(f"| **Total** | **{findings.get('total', 0)}** |")
        lines.append(f"\nScanners: {', '.join(data.get('scanners_used', []))}")
        lines.append(f"Languages: {', '.join(data.get('languages_detected', []))}")

    elif stage_name == "domain_extraction":
        domains = data.get("domains", data.get("bounded_contexts", []))
        lines.append(f"**Domains found:** {len(domains)}")
        for d in domains[:10]:
            name = d.get("name", "Unknown")
            confidence = d.get("confidence", 0)
            entities = d.get("entities", d.get("entity_count", 0))
            if isinstance(entities, list):
                entities = len(entities)
            lines.append(f"- **{name}** (confidence: {confidence:.2f}, entities: {entities})")

    elif stage_name == "story_generation":
        epics = data.get("epics", [])
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Epics | {data.get('total_epics', len(epics))} |")
        lines.append(f"| Features | {data.get('total_features', 0)} |")
        lines.append(f"| Stories | {data.get('total_stories', 0)} |")
        lines.append(f"| Story Points | {data.get('total_story_points', 0)} |")
        lines.append(f"| Estimated Weeks | {data.get('estimated_weeks', 0)} |")
        if epics:
            lines.extend(["", "### Epics"])
            for e in epics[:10]:
                title = e.get("title", "Unknown")
                sp = e.get("story_points", e.get("estimated_story_points", 0))
                fc = e.get("feature_count", 0)
                lines.append(f"- **{e.get('id', '?')}**: {title} ({sp} SP, {fc} features)")

    elif stage_name == "estimation":
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Adjusted FP | {data.get('adjusted_fp', 0):.1f} |")
        lines.append(f"| Weeks (low) | {data.get('estimated_weeks_low', 0)} |")
        lines.append(f"| Weeks (likely) | {data.get('estimated_weeks_likely', 0)} |")
        lines.append(f"| Weeks (high) | {data.get('estimated_weeks_high', 0)} |")
        lines.append(f"| Effort (person-days) | {data.get('total_effort_person_days', 0):.1f} |")
        lines.append(f"| Team size | {data.get('recommended_team_size', 0)} |")
        lines.append(f"| Confidence | {data.get('confidence_level', 0):.0%} |")

    elif stage_name == "plane_export":
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| JSON path | `{data.get('json_path', 'N/A')}` |")
        lines.append(f"| Markdown path | `{data.get('markdown_path', 'N/A')}` |")
        lines.append(f"| Epics | {data.get('total_epics', 0)} |")
        lines.append(f"| Stories | {data.get('total_stories', 0)} |")
        lines.append(f"| Relations | {data.get('total_relations', 0)} |")

    else:
        # Generic: dump first-level keys
        for key, value in list(data.items())[:20]:
            if isinstance(value, (str, int, float, bool)):
                lines.append(f"- **{key}:** {value}")
            elif isinstance(value, list):
                lines.append(f"- **{key}:** {len(value)} items")
            elif isinstance(value, dict):
                lines.append(f"- **{key}:** {len(value)} keys")

    return lines


def write_summary_md(
    stage_timings: list,
    context_data: dict,
    output_dir: Path,
):
    """Write overall summary markdown."""
    total_time = sum(t["duration"] for t in stage_timings)

    lines = [
        "# HCI-CRS Onboarding - Step-by-Step Results",
        "",
        f"**Project:** {PROJECT_PATH}",
        f"**Run date:** {datetime.now(timezone.utc).isoformat()}",
        f"**Total duration:** {total_time:.1f}s ({total_time/60:.1f} min)",
        "",
        "## Stage Results",
        "",
        "| # | Stage | Score | Passed | Duration | Compute |",
        "|---|-------|-------|--------|----------|---------|",
    ]

    for i, t in enumerate(stage_timings, 1):
        info = STAGE_INFO.get(t["stage"], (t["stage"], "", ""))
        human_name, compute_type, _ = info
        passed = "Yes" if t["passed"] else "**No**"
        lines.append(
            f"| {i} | [{human_name}]({t['stage']}.md) | {t['score']:.2f} | "
            f"{passed} | {t['duration']:.1f}s | {compute_type} |"
        )

    # LLM-heavy stages timing
    llm_stages = [t for t in stage_timings if "LLM" in STAGE_INFO.get(t["stage"], ("", "", ""))[1]]
    if llm_stages:
        llm_total = sum(t["duration"] for t in llm_stages)
        lines.extend([
            "",
            "## LLM-Heavy Stages",
            "",
            f"**Total LLM time:** {llm_total:.1f}s ({llm_total/60:.1f} min)",
            f"**Percentage of total:** {llm_total/total_time*100:.0f}%" if total_time > 0 else "",
            "",
        ])
        for t in llm_stages:
            info = STAGE_INFO.get(t["stage"], (t["stage"], "", ""))
            lines.append(f"- **{info[0]}**: {t['duration']:.1f}s ({info[1]})")

    # Failed stages
    failed = [t for t in stage_timings if not t["passed"]]
    if failed:
        lines.extend(["", "## Failed Stages", ""])
        for t in failed:
            info = STAGE_INFO.get(t["stage"], (t["stage"], "", ""))
            lines.append(f"- **{info[0]}**: score {t['score']:.2f}, error: {t.get('error', 'N/A')}")

    output_file = output_dir / "SUMMARY.md"
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info(f"Wrote {output_file}")


# =============================================================================
# Main runner
# =============================================================================

async def run_stepbystep(
    include_plane_export: bool = False,
    stages_filter: list = None,
    start_from: str = None,
):
    """Run onboarding step-by-step, saving each result to markdown."""
    from app.confucius.workflows.onboarding import OnboardingOrchestrator
    from app.confucius.workflows.base import WorkflowContext

    # Check project exists
    if not Path(PROJECT_PATH).exists():
        logger.error(f"Project not found: {PROJECT_PATH}")
        return False

    # Versioned run management
    from app.confucius.workflows.onboarding_versioning import OnboardingRunManager

    run_mgr = OnboardingRunManager(PROJECT_PATH)
    trigger = "rerun" if run_mgr.get_latest_run() else "initial"
    onboarding_run = run_mgr.start_run(trigger=trigger, answers=ANSWERS)

    # Use versioned stepbystep dir; OUTPUT_DIR stays as symlink target
    versioned_output = onboarding_run.stepbystep_dir
    versioned_output.mkdir(parents=True, exist_ok=True)

    orchestrator = OnboardingOrchestrator()
    session_id = f"stepbystep-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Check for existing checkpoint to resume from
    checkpoint_file = versioned_output / "checkpoint.json"
    shared_data = {
        "project_path": PROJECT_PATH,
        "answers": ANSWERS,
        "onboarding_trigger": trigger,
        "onboarding_run_id": onboarding_run.run_id,
        "onboarding_run_dir": str(onboarding_run.run_dir),
    }
    completed_stages = []

    if start_from and checkpoint_file.exists():
        try:
            with open(checkpoint_file, "r") as f:
                checkpoint = json.load(f)
            shared_data = checkpoint.get("shared_data", shared_data)
            completed_stages = checkpoint.get("completed_stages", [])
            logger.info(f"Loaded checkpoint: {len(completed_stages)} stages completed")
        except Exception as e:
            logger.warning(f"Could not load checkpoint: {e}")

    context = WorkflowContext(
        session_id=session_id,
        workflow_id="stepbystep",
        workflow_type="onboarding",
        shared_data=shared_data,
        completed_stages=completed_stages,
        router=orchestrator._router,
    )

    stages = orchestrator.get_stages()
    stage_timings = []

    # Determine which stages to run
    stage_names = [s.name for s in stages]
    if not include_plane_export:
        stage_names = [s for s in stage_names if s != "plane_export"]

    if stages_filter:
        # Map m1,m2,... to stage names
        name_map = {f"m{i+1}": name for i, name in enumerate(
            [s for s in stage_names if s != "plane_export"]
        )}
        name_map["plane_export"] = "plane_export"
        stage_names = [name_map.get(f, f) for f in stages_filter]

    if start_from:
        name_map = {f"m{i+1}": name for i, name in enumerate(
            [s for s in [st.name for st in stages] if s != "plane_export"]
        )}
        name_map["plane_export"] = "plane_export"
        start_name = name_map.get(start_from, start_from)
        try:
            start_idx = [s.name for s in stages].index(start_name)
            stage_names = [s.name for s in stages[start_idx:]]
            if not include_plane_export:
                stage_names = [s for s in stage_names if s != "plane_export"]
        except ValueError:
            logger.error(f"Unknown stage: {start_from}")
            return False

    print(f"\n{'='*70}")
    print(f"HCI-CRS Step-by-Step Onboarding")
    print(f"{'='*70}")
    print(f"Project: {PROJECT_PATH}")
    print(f"Output:  {OUTPUT_DIR}")
    print(f"Stages:  {stage_names}")
    print(f"{'='*70}\n")

    total_start = datetime.now(timezone.utc)

    for stage in stages:
        if stage.name not in stage_names:
            continue

        # Skip already completed stages (from checkpoint)
        if stage.name in context.completed_stages:
            logger.info(f"Skipping completed stage: {stage.name}")
            continue

        info = STAGE_INFO.get(stage.name, (stage.name, "Unknown", "Unknown"))
        human_name, compute_type, expected_time = info

        print(f"\n{'─'*70}")
        print(f"  {human_name}")
        print(f"  Compute: {compute_type}")
        print(f"  Expected: {expected_time}")
        print(f"  Threshold: {stage.quality_threshold}")
        print(f"{'─'*70}")

        stage_start = datetime.now(timezone.utc)

        try:
            stage_result = await orchestrator.execute_stage(stage, context)

            duration = (datetime.now(timezone.utc) - stage_start).total_seconds()
            score = stage_result.quality_score
            passed = stage_result.passed_quality_gate

            timing = {
                "stage": stage.name,
                "score": score,
                "passed": passed,
                "duration": duration,
                "threshold": stage.quality_threshold,
            }
            stage_timings.append(timing)

            # Write stage result markdown to versioned dir
            write_stage_result_md(
                stage.name, stage_result, duration,
                context.shared_data, versioned_output,
            )

            # Update run manifest with stage score
            onboarding_run.update_stage_score(stage.name, score)

            status = "PASSED" if passed else "FAILED"
            print(f"\n  Result: {status}")
            print(f"  Score:  {score:.2f} / {stage.quality_threshold}")
            print(f"  Time:   {duration:.1f}s ({duration/60:.1f} min)")

            # Save checkpoint after each stage (to versioned dir)
            checkpoint_data = {
                "session_id": session_id,
                "run_id": onboarding_run.run_id,
                "completed_stages": context.completed_stages.copy(),
                "shared_data": context.shared_data,
                "stage_timings": stage_timings,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            try:
                with open(checkpoint_file, "w") as f:
                    json.dump(checkpoint_data, f, indent=2, default=str)
            except Exception as e:
                logger.warning(f"Could not save checkpoint: {e}")

            if not passed and stage.required:
                print(f"\n  Required stage failed - stopping.")
                break

        except Exception as e:
            duration = (datetime.now(timezone.utc) - stage_start).total_seconds()
            stage_timings.append({
                "stage": stage.name,
                "score": 0,
                "passed": False,
                "duration": duration,
                "error": str(e),
            })
            print(f"\n  ERROR: {e}")
            import traceback
            traceback.print_exc()

            if stage.required:
                print(f"\n  Required stage failed - stopping.")
                break

    # Write summary to versioned dir
    total_duration = (datetime.now(timezone.utc) - total_start).total_seconds()
    write_summary_md(stage_timings, context.shared_data, versioned_output)

    # Finalize versioned run
    all_passed = all(t["passed"] for t in stage_timings)
    stage_scores = {t["stage"]: t["score"] for t in stage_timings}

    if all_passed:
        onboarding_run.complete(stage_scores=stage_scores)
    else:
        failed_names = [t["stage"] for t in stage_timings if not t["passed"]]
        onboarding_run.fail(
            error=f"Failed stages: {', '.join(failed_names)}",
            stage_scores=stage_scores,
        )

    # Update symlinks (stepbystep + deliverables if M10 ran)
    run_mgr.finalize(onboarding_run)

    # Show run history
    all_runs = run_mgr.list_runs()

    # Final summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Run ID:  {onboarding_run.run_id}")
    print(f"Trigger: {trigger}")
    print(f"Total:   {total_duration:.1f}s ({total_duration/60:.1f} min)")
    print(f"Stages:  {len(stage_timings)}/{len(stage_names)}")

    for t in stage_timings:
        info = STAGE_INFO.get(t["stage"], (t["stage"], "", ""))
        status = "OK" if t["passed"] else "FAIL"
        print(f"  [{status}] {info[0]}: {t['duration']:.1f}s (score: {t['score']:.2f})")

    passed_count = sum(1 for t in stage_timings if t["passed"])
    print(f"\nPassed: {passed_count}/{len(stage_timings)}")
    print(f"Output: {versioned_output}")
    print(f"History: {len(all_runs)} run(s) in {run_mgr.history_dir}")

    if len(all_runs) > 1:
        print(f"\nPrevious runs:")
        for r in all_runs[:-1]:
            print(f"  - {r.run_id} ({r.manifest.get('trigger', '?')}, {r.manifest.get('status', '?')})")

    return all_passed


async def main():
    include_plane = "--plane-export" in sys.argv
    stages_filter = None
    start_from = None

    for arg in sys.argv[1:]:
        if arg.startswith("--stages="):
            stages_filter = arg.split("=")[1].split(",")
        elif arg.startswith("--from="):
            start_from = arg.split("=")[1]

    success = await run_stepbystep(
        include_plane_export=include_plane,
        stages_filter=stages_filter,
        start_from=start_from,
    )
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
