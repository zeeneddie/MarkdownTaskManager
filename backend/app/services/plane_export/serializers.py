"""
Plane Export Serializers - JSON and ADR-002 Markdown output formats.

Two output formats:
1. JSON: plane-export.json for API-based import by the Plane importer
2. ADR-002 Markdown: Directory structure for Git PR review

Both consume a PlaneExportPackage and produce output files.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from .models import (
    ExportEpic,
    ExportFeature,
    ExportStory,
    PlaneExportPackage,
)

logger = logging.getLogger(__name__)


class JsonExportSerializer:
    """Serialize PlaneExportPackage to JSON for API-based Plane import."""

    def serialize(self, package: PlaneExportPackage) -> str:
        """Serialize to JSON string."""
        return package.model_dump_json(indent=2)

    def write(self, package: PlaneExportPackage, output_path: str) -> str:
        """Write JSON export to file. Returns the file path."""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        content = self.serialize(package)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Wrote Plane JSON export to {output_path}")
        return output_path


class Adr002MarkdownSerializer:
    """
    Serialize PlaneExportPackage to ADR-002 markdown directory structure.

    Output structure:
    project/
      project.md
      epics/
        EPIC-001-patient-management/
          epic.md
          features/
            FEATURE-001-crud-operations/
              feature.md
              stories/
                STORY-001-create-patient/
                  story.md
    """

    def write(self, package: PlaneExportPackage, output_dir: str) -> str:
        """Write ADR-002 markdown export. Returns the output directory path."""
        root = Path(output_dir)
        root.mkdir(parents=True, exist_ok=True)

        # Write project.md
        self._write_project_md(package, root)

        # Write epics
        epics_dir = root / "epics"
        epics_dir.mkdir(exist_ok=True)

        for epic in package.epics:
            epic_slug = self._slugify(f"{epic.id}-{epic.domain_name}")
            epic_dir = epics_dir / epic_slug
            epic_dir.mkdir(exist_ok=True)

            self._write_epic_md(epic, package, epic_dir)

            # Write features
            features_dir = epic_dir / "features"
            features_dir.mkdir(exist_ok=True)

            for feature in epic.features:
                feature_slug = self._slugify(f"{feature.id}-{feature.title[:40]}")
                feature_dir = features_dir / feature_slug
                feature_dir.mkdir(exist_ok=True)

                self._write_feature_md(feature, epic, feature_dir)

                # Write stories
                stories_dir = feature_dir / "stories"
                stories_dir.mkdir(exist_ok=True)

                for story in feature.stories:
                    story_slug = self._slugify(f"{story.id}-{story.title[:40]}")
                    story_dir = stories_dir / story_slug
                    story_dir.mkdir(exist_ok=True)

                    self._write_story_md(story, feature, epic, story_dir)

        logger.info(f"Wrote ADR-002 markdown export to {output_dir}")
        return output_dir

    def _write_project_md(self, package: PlaneExportPackage, root: Path) -> None:
        """Write project summary markdown."""
        summary = package.project_summary
        lines = [
            f"# {summary.project_name or 'Project'} - Migration Plan",
            "",
            f"**Exported:** {package.exported_at.isoformat()}",
            f"**Source:** {package.source}",
            f"**Session:** {package.session_id or 'N/A'}",
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Epics | {summary.total_epics} |",
            f"| Features | {summary.total_features} |",
            f"| Stories | {summary.total_stories} |",
            f"| Story Points | {summary.total_story_points} |",
        ]

        if summary.estimated_weeks_likely:
            lines.extend([
                "",
                "## Estimation",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Weeks (low) | {summary.estimated_weeks_low} |",
                f"| Weeks (likely) | {summary.estimated_weeks_likely} |",
                f"| Weeks (high) | {summary.estimated_weeks_high} |",
                f"| Adjusted FP | {summary.adjusted_fp:.1f} |",
                f"| Effort (person-days) | {summary.total_effort_person_days:.1f} |",
                f"| Recommended Team Size | {summary.recommended_team_size} |",
                f"| Estimation Confidence | {summary.estimation_confidence:.0%} |",
            ])

        if summary.risk_factors:
            lines.extend(["", "## Risk Factors", ""])
            for risk in summary.risk_factors:
                desc = risk.get("description", risk.get("factor", str(risk)))
                lines.append(f"- {desc}")

        if summary.recommendations:
            lines.extend(["", "## Recommendations", ""])
            for rec in summary.recommendations:
                lines.append(f"- {rec}")

        lines.extend([
            "",
            "## Epics",
            "",
        ])
        for epic in package.epics:
            lines.append(
                f"- [{epic.id}](epics/{self._slugify(f'{epic.id}-{epic.domain_name}')}/epic.md) "
                f"- {epic.title} ({epic.estimated_story_points} SP, {epic.priority.value})"
            )

        self._write_file(root / "project.md", "\n".join(lines))

    def _write_epic_md(self, epic: ExportEpic, package: PlaneExportPackage, epic_dir: Path) -> None:
        """Write epic markdown."""
        lines = [
            f"# {epic.id}: {epic.title}",
            "",
            f"**Domain:** {epic.domain_name}",
            f"**Priority:** {epic.priority.value}",
            f"**Status:** {epic.status.value}",
            f"**Complexity:** {epic.complexity}",
            f"**Story Points:** {epic.estimated_story_points}",
            f"**Estimated Weeks:** {epic.estimated_weeks}",
            "",
            "## Description",
            "",
            epic.description,
            "",
        ]

        if epic.source_modules:
            lines.extend(["## Source Modules", ""])
            for mod in epic.source_modules[:20]:
                lines.append(f"- `{mod}`")
            lines.append("")

        lines.extend(["## Features", ""])
        for feature in epic.features:
            feature_slug = self._slugify(f"{feature.id}-{feature.title[:40]}")
            lines.append(
                f"- [{feature.id}](features/{feature_slug}/feature.md) "
                f"- {feature.title} ({feature.estimated_story_points} SP)"
            )

        self._write_file(epic_dir / "epic.md", "\n".join(lines))

    def _write_feature_md(self, feature: ExportFeature, epic: ExportEpic, feature_dir: Path) -> None:
        """Write feature markdown."""
        lines = [
            f"# {feature.id}: {feature.title}",
            "",
            f"**Epic:** {epic.id} - {epic.title}",
            f"**Priority:** {feature.priority.value}",
            f"**Status:** {feature.status.value}",
            f"**Complexity:** {feature.complexity}",
            f"**Story Points:** {feature.estimated_story_points}",
            "",
            "## Description",
            "",
            feature.description,
            "",
        ]

        if feature.source_modules:
            lines.extend(["## Source Modules", ""])
            for mod in feature.source_modules[:20]:
                lines.append(f"- `{mod}`")
            lines.append("")

        lines.extend(["## Stories", ""])
        for story in feature.stories:
            story_slug = self._slugify(f"{story.id}-{story.title[:40]}")
            lines.append(
                f"- [{story.id}](stories/{story_slug}/story.md) "
                f"- {story.title} ({story.story_points} SP, {story.priority.value})"
            )

        self._write_file(feature_dir / "feature.md", "\n".join(lines))

    def _write_story_md(
        self,
        story: ExportStory,
        feature: ExportFeature,
        epic: ExportEpic,
        story_dir: Path,
    ) -> None:
        """Write story markdown with full data preserved."""
        lines = [
            f"# {story.id}: {story.title}",
            "",
            f"**Feature:** {feature.id} - {feature.title}",
            f"**Epic:** {epic.id} - {epic.title}",
            f"**Priority:** {story.priority.value}",
            f"**Status:** {story.status.value}",
            f"**Story Points:** {story.story_points}",
            f"**Complexity:** {story.complexity}",
            f"**Type:** {story.story_type}",
            "",
            "## Description",
            "",
            story.description,
            "",
        ]

        # Acceptance criteria (preserved from M8!)
        if story.acceptance_criteria:
            lines.extend(["## Acceptance Criteria", ""])
            for ac in story.acceptance_criteria:
                lines.append(f"- [ ] **{ac.id}**: {ac.description} _{ac.test_type}_")
                if ac.source_hint:
                    lines.append(f"  - Source: `{ac.source_hint}`")
            lines.append("")

        # Source references (preserved from M8!)
        if story.source_references:
            lines.extend(["## Source References", ""])
            for ref in story.source_references:
                location = f"`{ref.file_path}`"
                if ref.line_start:
                    location += f" (L{ref.line_start}"
                    if ref.line_end:
                        location += f"-{ref.line_end}"
                    location += ")"
                lines.append(f"- {location} [{ref.element_type}]")
                if ref.code_snippet:
                    lines.extend([f"  ```", f"  {ref.code_snippet}", f"  ```"])
            lines.append("")

        # Legacy context (preserved from M8!)
        if story.legacy_functionality or story.target_implementation:
            lines.extend(["## Migration Context", ""])
            if story.legacy_functionality:
                lines.append(f"**Legacy:** {story.legacy_functionality}")
            if story.target_implementation:
                lines.append(f"**Target:** {story.target_implementation}")
            lines.append("")

        if story.business_value:
            lines.extend([
                "## Business Value",
                "",
                story.business_value,
                "",
            ])

        # Dependencies
        if story.blocked_by:
            lines.extend(["## Dependencies", ""])
            for dep_id in story.blocked_by:
                lines.append(f"- Blocked by: `{dep_id}`")
            lines.append("")

        self._write_file(story_dir / "story.md", "\n".join(lines))

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to filesystem-safe slug."""
        import re
        slug = text.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        return slug.strip("-")[:60]

    @staticmethod
    def _write_file(path: Path, content: str) -> None:
        """Write content to file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content + "\n")
