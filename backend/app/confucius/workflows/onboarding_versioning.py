"""
Onboarding Versioning - Manages versioned onboarding runs.

Elke onboarding-run krijgt een timestamped directory. De vorige run wordt
gearchiveerd zodat je kunt vergelijken wat er veranderd is na code-wijzigingen
of een opnieuw draaien van de pipeline.

Directory layout in het project:
    docs/
        onboarding-deliverables/          <- symlink naar latest versie
        onboarding-history/
            run-2026-02-10T21-11-00/      <- eerste run
                deliverables/             <- M10 output
                stepbystep/               <- per-stage markdown output
                manifest.json             <- metadata over deze run
            run-2026-02-11T14-30-00/      <- herrun na wijzigingen
                ...
    .marqed-stepbystep/                   <- symlink naar latest stepbystep/

manifest.json bevat:
    - run_id (timestamp)
    - trigger (initial / rerun / code_change)
    - started_at, completed_at, duration_seconds
    - stage_scores (per stage quality score)
    - project_path, project_name
    - previous_run_id (link naar vorige run)
"""

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _ts_now() -> str:
    """ISO timestamp for directory naming (filesystem-safe)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")


def _ts_display() -> str:
    """ISO timestamp for display in manifest."""
    return datetime.now(timezone.utc).isoformat()


class OnboardingRunManager:
    """
    Manages versioned onboarding runs for a project.

    Usage:
        mgr = OnboardingRunManager("/opt/projecten/hci-crs")
        run = mgr.start_run(trigger="initial")

        # ... pipeline draait, schrijft naar run.deliverables_dir en run.stepbystep_dir ...

        run.complete(stage_scores={"validate_input": 1.0, "intake_context": 0.85, ...})
        mgr.finalize(run)   # symlinks bijwerken
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.history_dir = self.project_path / "docs" / "onboarding-history"
        self.deliverables_link = self.project_path / "docs" / "onboarding-deliverables"
        self.stepbystep_link = self.project_path / ".marqed-stepbystep"

    def list_runs(self) -> List["OnboardingRun"]:
        """List all previous runs, sorted oldest first."""
        runs = []
        if not self.history_dir.exists():
            return runs
        for d in sorted(self.history_dir.iterdir()):
            if d.is_dir() and d.name.startswith("run-"):
                manifest_path = d / "manifest.json"
                manifest = {}
                if manifest_path.exists():
                    try:
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    except (json.JSONDecodeError, OSError):
                        pass
                runs.append(OnboardingRun(
                    run_dir=d,
                    run_id=d.name.replace("run-", ""),
                    manifest=manifest,
                ))
        return runs

    def get_latest_run(self) -> Optional["OnboardingRun"]:
        """Get the most recent completed run, or None."""
        runs = self.list_runs()
        completed = [r for r in runs if r.manifest.get("status") == "completed"]
        return completed[-1] if completed else None

    def start_run(
        self,
        trigger: str = "rerun",
        answers: Optional[Dict[str, str]] = None,
    ) -> "OnboardingRun":
        """
        Start a new onboarding run.

        Args:
            trigger: Why this run was started.
                     "initial" = first onboarding
                     "rerun"   = re-run na pipeline/config changes
                     "code_change" = re-run na code wijzigingen in het project
            answers: M1 intake answers (stored in manifest for reference)
        """
        self.history_dir.mkdir(parents=True, exist_ok=True)

        run_id = _ts_now()
        run_dir = self.history_dir / f"run-{run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)

        # Find previous run
        previous = self.get_latest_run()
        previous_run_id = previous.run_id if previous else None

        manifest = {
            "run_id": run_id,
            "trigger": trigger,
            "status": "running",
            "started_at": _ts_display(),
            "completed_at": None,
            "duration_seconds": None,
            "project_path": str(self.project_path),
            "project_name": self.project_path.name,
            "previous_run_id": previous_run_id,
            "answers": answers or {},
            "stage_scores": {},
        }

        run = OnboardingRun(run_dir=run_dir, run_id=run_id, manifest=manifest)
        run.deliverables_dir.mkdir(parents=True, exist_ok=True)
        run.stepbystep_dir.mkdir(parents=True, exist_ok=True)
        run.save_manifest()

        logger.info(
            f"Onboarding run {run_id} started for {self.project_path.name} "
            f"(trigger={trigger}, previous={previous_run_id})"
        )
        return run

    def finalize(self, run: "OnboardingRun"):
        """
        Finalize a completed run: update symlinks to point to latest.

        Replaces:
        - docs/onboarding-deliverables -> latest deliverables/
        - .marqed-stepbystep -> latest stepbystep/
        """
        # Archive existing non-symlink directories (from before versioning was introduced)
        self._migrate_legacy_dir(self.deliverables_link, run, "deliverables")
        self._migrate_legacy_dir(self.stepbystep_link, run, "stepbystep")

        # Update symlinks
        self._update_symlink(self.deliverables_link, run.deliverables_dir)
        self._update_symlink(self.stepbystep_link, run.stepbystep_dir)

        logger.info(f"Onboarding run {run.run_id} finalized — symlinks updated")

    def _migrate_legacy_dir(self, link_path: Path, run: "OnboardingRun", subdir: str):
        """
        If link_path is a real directory (not a symlink), migrate its contents
        to the first run in history, then remove the directory.
        """
        if link_path.exists() and not link_path.is_symlink():
            # This is a legacy directory from before versioning
            legacy_run_id = "legacy"
            legacy_dir = self.history_dir / f"run-{legacy_run_id}"
            target = legacy_dir / subdir
            if not target.exists():
                legacy_dir.mkdir(parents=True, exist_ok=True)
                # Move contents to legacy run
                shutil.copytree(link_path, target, dirs_exist_ok=True)
                # Write a minimal manifest
                manifest_path = legacy_dir / "manifest.json"
                if not manifest_path.exists():
                    manifest = {
                        "run_id": legacy_run_id,
                        "trigger": "migrated_from_legacy",
                        "status": "completed",
                        "started_at": "unknown",
                        "completed_at": "unknown",
                        "project_path": str(self.project_path),
                        "project_name": self.project_path.name,
                        "note": "Migrated from pre-versioning directory structure",
                    }
                    manifest_path.write_text(
                        json.dumps(manifest, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )
                logger.info(f"Migrated legacy {link_path} to {target}")
            # Remove old directory so we can create symlink
            shutil.rmtree(link_path)

    def _update_symlink(self, link_path: Path, target: Path):
        """Create or update a symlink."""
        if link_path.is_symlink():
            link_path.unlink()
        elif link_path.exists():
            # Should have been migrated already, but just in case
            shutil.rmtree(link_path)

        link_path.symlink_to(target)
        logger.info(f"Symlink: {link_path} -> {target}")


class OnboardingRun:
    """Represents a single onboarding run with its directories and manifest."""

    def __init__(self, run_dir: Path, run_id: str, manifest: Dict[str, Any]):
        self.run_dir = run_dir
        self.run_id = run_id
        self.manifest = manifest

    @property
    def deliverables_dir(self) -> Path:
        return self.run_dir / "deliverables"

    @property
    def stepbystep_dir(self) -> Path:
        return self.run_dir / "stepbystep"

    def complete(
        self,
        stage_scores: Optional[Dict[str, float]] = None,
        summary: Optional[str] = None,
    ):
        """Mark run as completed with final scores."""
        started = self.manifest.get("started_at", "")
        try:
            start_dt = datetime.fromisoformat(started)
            duration = (datetime.now(timezone.utc) - start_dt).total_seconds()
        except (ValueError, TypeError):
            duration = None

        self.manifest["status"] = "completed"
        self.manifest["completed_at"] = _ts_display()
        self.manifest["duration_seconds"] = duration
        self.manifest["stage_scores"] = stage_scores or {}
        if summary:
            self.manifest["summary"] = summary
        self.save_manifest()

    def fail(self, error: str, stage_scores: Optional[Dict[str, float]] = None):
        """Mark run as failed."""
        self.manifest["status"] = "failed"
        self.manifest["completed_at"] = _ts_display()
        self.manifest["error"] = error
        self.manifest["stage_scores"] = stage_scores or {}
        self.save_manifest()

    def update_stage_score(self, stage_name: str, score: float):
        """Update score for a single stage (called during pipeline execution)."""
        self.manifest.setdefault("stage_scores", {})[stage_name] = score
        self.save_manifest()

    def save_manifest(self):
        """Write manifest to disk."""
        manifest_path = self.run_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(self.manifest, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    def __repr__(self):
        return (
            f"OnboardingRun(id={self.run_id}, "
            f"status={self.manifest.get('status')}, "
            f"trigger={self.manifest.get('trigger')})"
        )


# =============================================================================
# DIFF UTILITIES (for comparing runs)
# =============================================================================

def compare_runs(
    run_a: OnboardingRun,
    run_b: OnboardingRun,
) -> Dict[str, Any]:
    """
    Compare two onboarding runs and return a diff summary.

    Returns dict with:
    - score_changes: {stage: {old, new, delta}}
    - files_added, files_removed, files_changed
    - trigger info
    """
    diff = {
        "run_a": run_a.run_id,
        "run_b": run_b.run_id,
        "trigger_a": run_a.manifest.get("trigger"),
        "trigger_b": run_b.manifest.get("trigger"),
    }

    # Compare stage scores
    scores_a = run_a.manifest.get("stage_scores", {})
    scores_b = run_b.manifest.get("stage_scores", {})
    all_stages = sorted(set(scores_a.keys()) | set(scores_b.keys()))

    score_changes = {}
    for stage in all_stages:
        old = scores_a.get(stage)
        new = scores_b.get(stage)
        if old != new:
            score_changes[stage] = {
                "old": old,
                "new": new,
                "delta": (new or 0) - (old or 0),
            }
    diff["score_changes"] = score_changes

    # Compare deliverable files
    files_a = set()
    files_b = set()

    if run_a.deliverables_dir.exists():
        files_a = {
            str(f.relative_to(run_a.deliverables_dir))
            for f in run_a.deliverables_dir.rglob("*")
            if f.is_file()
        }
    if run_b.deliverables_dir.exists():
        files_b = {
            str(f.relative_to(run_b.deliverables_dir))
            for f in run_b.deliverables_dir.rglob("*")
            if f.is_file()
        }

    diff["files_added"] = sorted(files_b - files_a)
    diff["files_removed"] = sorted(files_a - files_b)
    diff["files_common"] = sorted(files_a & files_b)

    return diff


def format_run_summary(run: OnboardingRun) -> str:
    """Format a single run as a readable summary string."""
    m = run.manifest
    lines = [
        f"Run: {run.run_id}",
        f"  Trigger:  {m.get('trigger', 'unknown')}",
        f"  Status:   {m.get('status', 'unknown')}",
        f"  Started:  {m.get('started_at', 'unknown')}",
        f"  Duration: {m.get('duration_seconds', 'unknown')}s",
    ]

    scores = m.get("stage_scores", {})
    if scores:
        lines.append("  Scores:")
        for stage, score in sorted(scores.items()):
            lines.append(f"    {stage:25s} {score:.2f}")

    prev = m.get("previous_run_id")
    if prev:
        lines.append(f"  Previous: {prev}")

    return "\n".join(lines)
