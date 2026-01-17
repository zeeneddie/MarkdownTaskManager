"""
JourneyComparisonService - E2E comparison between legacy and new systems

This service enables:
- Recording user journeys on legacy system
- Replaying journeys on new system
- Comparing step-by-step results
- Managing override rules (Eddie's approved exceptions)
- Visual and data diff generation

Key principle: 100% journey match unless explicitly overridden by Eddie.

Author: Claude Code (Week 136 - Fase 24)
Date: 2026-01-01
"""

import logging
import uuid
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict
from pathlib import Path
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.models.data_architecture import (
    JourneyStepType, JourneyMatchStatus,
    JourneyStep, JourneyRecording, JourneyStepComparison,
    JourneyOverrideRule, JourneyComparisonResult,
    JourneyRecordingModel, JourneyComparisonModel, JourneyOverrideRuleModel
)

logger = logging.getLogger(__name__)


class JourneyComparisonService:
    """
    Service for comparing user journeys between legacy and new systems.

    The rebuild strategy requires 100% functional equivalence.
    This service captures and compares:
    - UI interactions (clicks, inputs, navigation)
    - API responses (data integrity)
    - Visual appearance (screenshots)

    Any differences must be explicitly approved by Eddie via override rules.
    """

    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        screenshots_dir: str = "/tmp/journey_screenshots"
    ):
        self.db = db
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

        # In-memory caches
        self._recordings: Dict[str, JourneyRecording] = {}
        self._comparisons: Dict[str, JourneyComparisonResult] = {}
        self._override_rules: Dict[str, List[JourneyOverrideRule]] = {}  # journey_name -> rules

    # ============================================
    # Journey Recording
    # ============================================

    async def create_recording(
        self,
        name: str,
        system: str,  # "legacy" or "new"
        base_url: str,
        description: Optional[str] = None,
        recorded_by: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> str:
        """Create a new journey recording session."""
        recording_id = str(uuid.uuid4())

        recording = JourneyRecording(
            id=recording_id,
            name=name,
            description=description,
            system=system,
            base_url=base_url,
            steps=[],
            recorded_by=recorded_by
        )
        self._recordings[recording_id] = recording

        if self.db:
            db_recording = JourneyRecordingModel(
                id=recording_id,
                project_id=project_id,
                name=name,
                description=description,
                system=system,
                base_url=base_url,
                recorded_by=recorded_by
            )
            self.db.add(db_recording)
            await self.db.commit()

        logger.info(f"Created journey recording: {name} ({system}) - {recording_id}")
        return recording_id

    async def add_step(
        self,
        recording_id: str,
        step_type: JourneyStepType,
        selector: Optional[str] = None,
        action: Optional[str] = None,
        value: Optional[str] = None,
        expected_result: Optional[str] = None,
        screenshot_path: Optional[str] = None,
        api_request: Optional[Dict[str, Any]] = None,
        api_response: Optional[Dict[str, Any]] = None,
        duration_ms: int = 0
    ) -> int:
        """Add a step to a journey recording."""
        recording = self._recordings.get(recording_id)
        if not recording:
            raise ValueError(f"Recording {recording_id} not found")

        step_number = len(recording.steps) + 1
        step = JourneyStep(
            step_number=step_number,
            step_type=step_type,
            selector=selector,
            action=action,
            value=value,
            expected_result=expected_result,
            screenshot_path=screenshot_path,
            api_request=api_request,
            api_response=api_response,
            duration_ms=duration_ms
        )
        recording.steps.append(step)
        recording.total_duration_ms += duration_ms

        logger.debug(f"Added step {step_number} to recording {recording_id}: {step_type.value}")
        return step_number

    async def finalize_recording(self, recording_id: str) -> JourneyRecording:
        """Finalize and persist a recording."""
        recording = self._recordings.get(recording_id)
        if not recording:
            raise ValueError(f"Recording {recording_id} not found")

        if self.db:
            steps_data = [
                {
                    "step_number": s.step_number,
                    "step_type": s.step_type.value,
                    "selector": s.selector,
                    "action": s.action,
                    "value": s.value,
                    "expected_result": s.expected_result,
                    "screenshot_path": s.screenshot_path,
                    "api_request": s.api_request,
                    "api_response": s.api_response,
                    "duration_ms": s.duration_ms,
                    "timestamp": s.timestamp.isoformat()
                }
                for s in recording.steps
            ]

            await self.db.execute(
                update(JourneyRecordingModel)
                .where(JourneyRecordingModel.id == recording_id)
                .values(
                    step_count=len(recording.steps),
                    total_duration_ms=recording.total_duration_ms,
                    steps_data=steps_data
                )
            )
            await self.db.commit()

        logger.info(f"Finalized recording {recording_id}: {len(recording.steps)} steps")
        return recording

    async def get_recording(self, recording_id: str) -> Optional[JourneyRecording]:
        """Get a journey recording by ID."""
        if recording_id in self._recordings:
            return self._recordings[recording_id]

        if self.db:
            result = await self.db.execute(
                select(JourneyRecordingModel).where(JourneyRecordingModel.id == recording_id)
            )
            db_recording = result.scalar_one_or_none()
            if db_recording:
                recording = self._deserialize_recording(db_recording)
                self._recordings[recording_id] = recording
                return recording

        return None

    # ============================================
    # Journey Comparison
    # ============================================

    async def compare_journeys(
        self,
        legacy_recording_id: str,
        new_recording_id: str,
        project_id: Optional[str] = None,
        apply_overrides: bool = True
    ) -> JourneyComparisonResult:
        """
        Compare two journey recordings step by step.

        This is the core comparison logic:
        1. Compare each step between legacy and new
        2. Apply visual comparison for screenshots
        3. Apply data comparison for API responses
        4. Check for override rules
        5. Generate final match percentage
        """
        legacy = await self.get_recording(legacy_recording_id)
        new = await self.get_recording(new_recording_id)

        if not legacy:
            raise ValueError(f"Legacy recording {legacy_recording_id} not found")
        if not new:
            raise ValueError(f"New recording {new_recording_id} not found")

        comparison_id = str(uuid.uuid4())
        step_comparisons = []

        # Load override rules for this journey
        override_rules = []
        if apply_overrides:
            override_rules = await self.get_override_rules(legacy.name)

        # Compare step by step
        max_steps = max(len(legacy.steps), len(new.steps))

        for i in range(max_steps):
            legacy_step = legacy.steps[i] if i < len(legacy.steps) else None
            new_step = new.steps[i] if i < len(new.steps) else None

            comparison = await self._compare_step(
                step_number=i + 1,
                legacy_step=legacy_step,
                new_step=new_step,
                override_rules=override_rules
            )
            step_comparisons.append(comparison)

        # Calculate statistics
        matching = sum(1 for c in step_comparisons if c.status == JourneyMatchStatus.MATCH)
        mismatching = sum(1 for c in step_comparisons if c.status == JourneyMatchStatus.MISMATCH)
        overridden = sum(1 for c in step_comparisons if c.status == JourneyMatchStatus.OVERRIDE_APPROVED)

        # Calculate visual match percentage
        visual_diffs = [c.visual_diff_score for c in step_comparisons if c.visual_diff_score is not None]
        visual_match = (1 - sum(visual_diffs) / len(visual_diffs)) * 100 if visual_diffs else 100.0

        # Calculate data match percentage
        data_matches = sum(1 for c in step_comparisons if c.data_diff is None or len(c.data_diff) == 0)
        data_match = (data_matches / len(step_comparisons)) * 100 if step_comparisons else 100.0

        # Calculate overall match (mismatches count against, overrides don't)
        overall_match = ((matching + overridden) / max_steps * 100) if max_steps > 0 else 100.0

        # Determine status
        if mismatching == 0:
            status = "passed"
        elif overridden > 0 and mismatching == 0:
            status = "passed_with_overrides"
        else:
            status = "failed"

        result = JourneyComparisonResult(
            id=comparison_id,
            journey_name=legacy.name,
            legacy_recording_id=legacy_recording_id,
            new_recording_id=new_recording_id,
            step_comparisons=step_comparisons,
            total_steps=max_steps,
            matching_steps=matching,
            mismatching_steps=mismatching,
            overridden_steps=overridden,
            overall_match_percentage=round(overall_match, 2),
            visual_match_percentage=round(visual_match, 2),
            data_match_percentage=round(data_match, 2),
            status=status
        )

        self._comparisons[comparison_id] = result

        # Persist to database
        if self.db:
            db_comparison = JourneyComparisonModel(
                id=comparison_id,
                project_id=project_id,
                journey_name=legacy.name,
                legacy_recording_id=legacy_recording_id,
                new_recording_id=new_recording_id,
                total_steps=max_steps,
                matching_steps=matching,
                mismatching_steps=mismatching,
                overridden_steps=overridden,
                overall_match_percentage=overall_match,
                visual_match_percentage=visual_match,
                data_match_percentage=data_match,
                status=status,
                comparison_data=self._serialize_comparison(result)
            )
            self.db.add(db_comparison)
            await self.db.commit()

        logger.info(
            f"Compared journeys: {legacy.name} - "
            f"{matching}/{max_steps} matching, {mismatching} mismatches, {overridden} overrides"
        )
        return result

    async def _compare_step(
        self,
        step_number: int,
        legacy_step: Optional[JourneyStep],
        new_step: Optional[JourneyStep],
        override_rules: List[JourneyOverrideRule]
    ) -> JourneyStepComparison:
        """Compare a single step between legacy and new."""
        # Handle missing steps
        if not legacy_step and not new_step:
            raise ValueError("Both steps cannot be None")

        if not legacy_step or not new_step:
            # Step exists in one but not other - definite mismatch
            return JourneyStepComparison(
                step_number=step_number,
                legacy_step=legacy_step or JourneyStep(step_number=step_number, step_type=JourneyStepType.ASSERTION),
                new_step=new_step or JourneyStep(step_number=step_number, step_type=JourneyStepType.ASSERTION),
                status=JourneyMatchStatus.MISMATCH,
                data_diff={"error": "Step missing in one recording"}
            )

        # Check for override rule
        override = self._find_applicable_override(step_number, legacy_step, new_step, override_rules)
        if override:
            return JourneyStepComparison(
                step_number=step_number,
                legacy_step=legacy_step,
                new_step=new_step,
                status=JourneyMatchStatus.OVERRIDE_APPROVED,
                override_reason=override.reason,
                override_approved_by=override.approved_by,
                override_approved_at=override.approved_at
            )

        # Compare step type
        if legacy_step.step_type != new_step.step_type:
            return JourneyStepComparison(
                step_number=step_number,
                legacy_step=legacy_step,
                new_step=new_step,
                status=JourneyMatchStatus.MISMATCH,
                data_diff={"step_type": f"{legacy_step.step_type.value} -> {new_step.step_type.value}"}
            )

        # Compare data (API responses)
        data_diff = self._compare_data(legacy_step.api_response, new_step.api_response)

        # Compare visual (screenshots)
        visual_diff_score = 0.0
        visual_diff_path = None
        if legacy_step.screenshot_path and new_step.screenshot_path:
            visual_diff_score, visual_diff_path = await self._compare_screenshots(
                legacy_step.screenshot_path,
                new_step.screenshot_path
            )

        # Determine match status
        if data_diff or visual_diff_score > 0.05:  # 5% visual threshold
            status = JourneyMatchStatus.MISMATCH
        else:
            status = JourneyMatchStatus.MATCH

        return JourneyStepComparison(
            step_number=step_number,
            legacy_step=legacy_step,
            new_step=new_step,
            status=status,
            visual_diff_path=visual_diff_path,
            visual_diff_score=visual_diff_score,
            data_diff=data_diff
        )

    def _compare_data(
        self,
        legacy_data: Optional[Dict[str, Any]],
        new_data: Optional[Dict[str, Any]],
        ignored_fields: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Compare two data dictionaries and return differences.

        Ignored fields (dynamic data like timestamps, IDs) are skipped.
        """
        if legacy_data is None and new_data is None:
            return None
        if legacy_data is None or new_data is None:
            return {"error": "Data missing in one response"}

        ignored = set(ignored_fields or ["timestamp", "created_at", "updated_at", "id", "request_id"])
        differences = {}

        def compare_recursive(path: str, l_val: Any, n_val: Any):
            if path.split(".")[-1] in ignored:
                return

            if type(l_val) != type(n_val):
                differences[path] = {"legacy": str(l_val), "new": str(n_val), "issue": "type_mismatch"}
            elif isinstance(l_val, dict):
                all_keys = set(l_val.keys()) | set(n_val.keys())
                for key in all_keys:
                    compare_recursive(
                        f"{path}.{key}" if path else key,
                        l_val.get(key),
                        n_val.get(key)
                    )
            elif isinstance(l_val, list):
                if len(l_val) != len(n_val):
                    differences[path] = {"legacy_len": len(l_val), "new_len": len(n_val), "issue": "array_length"}
                else:
                    for i, (l_item, n_item) in enumerate(zip(l_val, n_val)):
                        compare_recursive(f"{path}[{i}]", l_item, n_item)
            elif l_val != n_val:
                differences[path] = {"legacy": l_val, "new": n_val}

        compare_recursive("", legacy_data, new_data)
        return differences if differences else None

    async def _compare_screenshots(
        self,
        legacy_path: str,
        new_path: str
    ) -> Tuple[float, Optional[str]]:
        """
        Compare two screenshots and return diff score and diff image path.

        Returns:
            (diff_score, diff_image_path)
            - diff_score: 0.0 = identical, 1.0 = completely different
        """
        try:
            # Try to use PIL for comparison
            from PIL import Image, ImageChops
            import numpy as np

            legacy_img = Image.open(legacy_path)
            new_img = Image.open(new_path)

            # Resize if different dimensions
            if legacy_img.size != new_img.size:
                new_img = new_img.resize(legacy_img.size)

            # Calculate difference
            diff = ImageChops.difference(legacy_img.convert("RGB"), new_img.convert("RGB"))
            diff_array = np.array(diff)

            # Calculate diff score (0-1)
            diff_score = np.sum(diff_array) / (255.0 * diff_array.size)

            # Save diff image if significant
            diff_path = None
            if diff_score > 0.01:  # 1% threshold to save diff
                diff_filename = f"diff_{uuid.uuid4().hex[:8]}.png"
                diff_path = str(self.screenshots_dir / diff_filename)

                # Create highlighted diff
                diff_highlighted = Image.blend(legacy_img.convert("RGB"), diff.convert("RGB"), 0.5)
                diff_highlighted.save(diff_path)

            return diff_score, diff_path

        except ImportError:
            # PIL not available, use hash comparison
            legacy_hash = self._file_hash(legacy_path)
            new_hash = self._file_hash(new_path)

            if legacy_hash == new_hash:
                return 0.0, None
            else:
                return 1.0, None

        except Exception as e:
            logger.warning(f"Screenshot comparison failed: {e}")
            return 0.0, None

    def _file_hash(self, path: str) -> str:
        """Calculate MD5 hash of file."""
        try:
            with open(path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    # ============================================
    # Override Rules (Eddie's Exceptions)
    # ============================================

    async def create_override_rule(
        self,
        journey_name: str,
        legacy_behavior: str,
        new_behavior: str,
        reason: str,
        approved_by: str,
        override_type: str = "intentional_change",
        step_number: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        Create an override rule for approved differences.

        Override types:
        - improved_ux: New system has better UX (approved)
        - intentional_change: Business-approved change
        - known_difference: Acceptable technical difference
        - temporary: Temporary exception, will be fixed later
        """
        rule_id = str(uuid.uuid4())

        rule = JourneyOverrideRule(
            id=rule_id,
            journey_name=journey_name,
            step_number=step_number,
            override_type=override_type,
            legacy_behavior=legacy_behavior,
            new_behavior=new_behavior,
            reason=reason,
            approved_by=approved_by,
            expires_at=expires_at
        )

        # Add to cache
        if journey_name not in self._override_rules:
            self._override_rules[journey_name] = []
        self._override_rules[journey_name].append(rule)

        # Persist to database
        if self.db:
            db_rule = JourneyOverrideRuleModel(
                id=rule_id,
                project_id=project_id,
                journey_name=journey_name,
                step_number=step_number,
                override_type=override_type,
                legacy_behavior=legacy_behavior,
                new_behavior=new_behavior,
                reason=reason,
                approved_by=approved_by,
                expires_at=expires_at
            )
            self.db.add(db_rule)
            await self.db.commit()

        logger.info(f"Created override rule for {journey_name}: {override_type} by {approved_by}")
        return rule_id

    async def get_override_rules(
        self,
        journey_name: str,
        include_expired: bool = False
    ) -> List[JourneyOverrideRule]:
        """Get override rules for a journey."""
        # Check cache first
        if journey_name in self._override_rules:
            rules = self._override_rules[journey_name]
        elif self.db:
            result = await self.db.execute(
                select(JourneyOverrideRuleModel)
                .where(JourneyOverrideRuleModel.journey_name == journey_name)
                .where(JourneyOverrideRuleModel.active == True)
            )
            db_rules = result.scalars().all()
            rules = [self._deserialize_override_rule(r) for r in db_rules]
            self._override_rules[journey_name] = rules
        else:
            rules = []

        # Filter expired unless requested
        now = datetime.now(timezone.utc)
        if not include_expired:
            rules = [r for r in rules if r.expires_at is None or r.expires_at > now]

        return rules

    async def deactivate_override_rule(self, rule_id: str) -> bool:
        """Deactivate an override rule."""
        # Remove from cache
        for journey_name, rules in self._override_rules.items():
            self._override_rules[journey_name] = [r for r in rules if r.id != rule_id]

        # Update database
        if self.db:
            await self.db.execute(
                update(JourneyOverrideRuleModel)
                .where(JourneyOverrideRuleModel.id == rule_id)
                .values(active=False, updated_at=datetime.now(timezone.utc))
            )
            await self.db.commit()
            return True

        return False

    def _find_applicable_override(
        self,
        step_number: int,
        legacy_step: JourneyStep,
        new_step: JourneyStep,
        rules: List[JourneyOverrideRule]
    ) -> Optional[JourneyOverrideRule]:
        """Find an applicable override rule for a step comparison."""
        now = datetime.now(timezone.utc)

        for rule in rules:
            # Check if rule is active and not expired
            if not rule.active:
                continue
            if rule.expires_at and rule.expires_at < now:
                continue

            # Check step number match (None = all steps)
            if rule.step_number is not None and rule.step_number != step_number:
                continue

            # Rule applies
            return rule

        return None

    # ============================================
    # Batch Comparison
    # ============================================

    async def compare_all_journeys(
        self,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Compare all journey pairs for a project.

        Finds matching legacy/new recording pairs and compares them.
        """
        if not self.db:
            return {"error": "Database required for batch comparison"}

        # Get all recordings for project
        result = await self.db.execute(
            select(JourneyRecordingModel)
            .where(JourneyRecordingModel.project_id == project_id)
        )
        recordings = result.scalars().all()

        # Group by name
        by_name: Dict[str, Dict[str, str]] = {}  # name -> {system: recording_id}
        for rec in recordings:
            if rec.name not in by_name:
                by_name[rec.name] = {}
            by_name[rec.name][rec.system] = rec.id

        # Compare pairs
        results = []
        for name, systems in by_name.items():
            if "legacy" in systems and "new" in systems:
                try:
                    comparison = await self.compare_journeys(
                        legacy_recording_id=systems["legacy"],
                        new_recording_id=systems["new"],
                        project_id=project_id
                    )
                    results.append({
                        "journey": name,
                        "status": comparison.status,
                        "match_percentage": comparison.overall_match_percentage,
                        "mismatches": comparison.mismatching_steps,
                        "overrides": comparison.overridden_steps
                    })
                except Exception as e:
                    results.append({
                        "journey": name,
                        "status": "error",
                        "error": str(e)
                    })
            else:
                results.append({
                    "journey": name,
                    "status": "incomplete",
                    "has_legacy": "legacy" in systems,
                    "has_new": "new" in systems
                })

        # Summary
        passed = sum(1 for r in results if r.get("status") in ("passed", "passed_with_overrides"))
        failed = sum(1 for r in results if r.get("status") == "failed")
        incomplete = sum(1 for r in results if r.get("status") == "incomplete")

        return {
            "project_id": project_id,
            "total_journeys": len(by_name),
            "passed": passed,
            "failed": failed,
            "incomplete": incomplete,
            "pass_rate": round(passed / len(by_name) * 100, 1) if by_name else 0.0,
            "results": results
        }

    # ============================================
    # Report Generation
    # ============================================

    async def generate_comparison_report(
        self,
        comparison_id: str
    ) -> Dict[str, Any]:
        """Generate a detailed comparison report."""
        comparison = self._comparisons.get(comparison_id)

        if not comparison and self.db:
            result = await self.db.execute(
                select(JourneyComparisonModel).where(JourneyComparisonModel.id == comparison_id)
            )
            db_comparison = result.scalar_one_or_none()
            if db_comparison and db_comparison.comparison_data:
                comparison = self._deserialize_comparison(db_comparison.comparison_data)

        if not comparison:
            return {"error": f"Comparison {comparison_id} not found"}

        # Build detailed report
        report = {
            "id": comparison.id,
            "journey": comparison.journey_name,
            "compared_at": comparison.compared_at.isoformat(),
            "status": comparison.status,
            "summary": {
                "total_steps": comparison.total_steps,
                "matching": comparison.matching_steps,
                "mismatching": comparison.mismatching_steps,
                "overridden": comparison.overridden_steps,
                "overall_match": f"{comparison.overall_match_percentage}%",
                "visual_match": f"{comparison.visual_match_percentage}%",
                "data_match": f"{comparison.data_match_percentage}%"
            },
            "steps": [],
            "mismatches": [],
            "overrides": []
        }

        for step in comparison.step_comparisons:
            step_report = {
                "step": step.step_number,
                "legacy_action": f"{step.legacy_step.step_type.value}: {step.legacy_step.action or step.legacy_step.selector or ''}",
                "new_action": f"{step.new_step.step_type.value}: {step.new_step.action or step.new_step.selector or ''}",
                "status": step.status.value
            }
            report["steps"].append(step_report)

            if step.status == JourneyMatchStatus.MISMATCH:
                report["mismatches"].append({
                    "step": step.step_number,
                    "data_diff": step.data_diff,
                    "visual_diff_score": step.visual_diff_score,
                    "visual_diff_path": step.visual_diff_path
                })

            if step.status == JourneyMatchStatus.OVERRIDE_APPROVED:
                report["overrides"].append({
                    "step": step.step_number,
                    "reason": step.override_reason,
                    "approved_by": step.override_approved_by,
                    "approved_at": step.override_approved_at.isoformat() if step.override_approved_at else None
                })

        return report

    # ============================================
    # Serialization Helpers
    # ============================================

    def _deserialize_recording(self, db_model: JourneyRecordingModel) -> JourneyRecording:
        """Deserialize database model to JourneyRecording."""
        steps = []
        if db_model.steps_data:
            for s in db_model.steps_data:
                steps.append(JourneyStep(
                    step_number=s["step_number"],
                    step_type=JourneyStepType(s["step_type"]),
                    selector=s.get("selector"),
                    action=s.get("action"),
                    value=s.get("value"),
                    expected_result=s.get("expected_result"),
                    screenshot_path=s.get("screenshot_path"),
                    api_request=s.get("api_request"),
                    api_response=s.get("api_response"),
                    duration_ms=s.get("duration_ms", 0),
                    timestamp=datetime.fromisoformat(s["timestamp"]) if s.get("timestamp") else datetime.now(timezone.utc)
                ))

        return JourneyRecording(
            id=db_model.id,
            name=db_model.name,
            description=db_model.description,
            system=db_model.system,
            base_url=db_model.base_url,
            steps=steps,
            total_duration_ms=db_model.total_duration_ms or 0,
            recorded_at=db_model.recorded_at or datetime.now(timezone.utc),
            recorded_by=db_model.recorded_by
        )

    def _deserialize_override_rule(self, db_model: JourneyOverrideRuleModel) -> JourneyOverrideRule:
        """Deserialize database model to JourneyOverrideRule."""
        return JourneyOverrideRule(
            id=db_model.id,
            journey_name=db_model.journey_name,
            step_number=db_model.step_number,
            override_type=db_model.override_type,
            legacy_behavior=db_model.legacy_behavior,
            new_behavior=db_model.new_behavior,
            reason=db_model.reason,
            approved_by=db_model.approved_by,
            approved_at=db_model.approved_at or datetime.now(timezone.utc),
            expires_at=db_model.expires_at,
            active=db_model.active
        )

    def _serialize_comparison(self, result: JourneyComparisonResult) -> Dict[str, Any]:
        """Serialize JourneyComparisonResult to JSON."""
        return {
            "id": result.id,
            "journey_name": result.journey_name,
            "legacy_recording_id": result.legacy_recording_id,
            "new_recording_id": result.new_recording_id,
            "total_steps": result.total_steps,
            "matching_steps": result.matching_steps,
            "mismatching_steps": result.mismatching_steps,
            "overridden_steps": result.overridden_steps,
            "overall_match_percentage": result.overall_match_percentage,
            "visual_match_percentage": result.visual_match_percentage,
            "data_match_percentage": result.data_match_percentage,
            "status": result.status,
            "compared_at": result.compared_at.isoformat(),
            "step_comparisons": [
                {
                    "step_number": s.step_number,
                    "status": s.status.value,
                    "visual_diff_score": s.visual_diff_score,
                    "visual_diff_path": s.visual_diff_path,
                    "data_diff": s.data_diff,
                    "override_reason": s.override_reason,
                    "override_approved_by": s.override_approved_by
                }
                for s in result.step_comparisons
            ]
        }

    def _deserialize_comparison(self, data: Dict[str, Any]) -> JourneyComparisonResult:
        """Deserialize JSON to JourneyComparisonResult."""
        # Simplified deserialization - steps need full reconstruction
        return JourneyComparisonResult(
            id=data["id"],
            journey_name=data["journey_name"],
            legacy_recording_id=data["legacy_recording_id"],
            new_recording_id=data["new_recording_id"],
            total_steps=data["total_steps"],
            matching_steps=data["matching_steps"],
            mismatching_steps=data["mismatching_steps"],
            overridden_steps=data["overridden_steps"],
            overall_match_percentage=data["overall_match_percentage"],
            visual_match_percentage=data["visual_match_percentage"],
            data_match_percentage=data["data_match_percentage"],
            status=data["status"],
            compared_at=datetime.fromisoformat(data["compared_at"])
        )
