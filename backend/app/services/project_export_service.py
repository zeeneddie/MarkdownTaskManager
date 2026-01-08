"""
Project Export Service - Week 86

Exports Deep Extraction synthesis results to markdown project structure.

Generates:
- EPIC-{NNN}/epic.md
- EPIC-{NNN}/FEAT-{NNN}/feature.md
- EPIC-{NNN}/FEAT-{NNN}/STORY-{NNN}.md
- project-summary.md
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.deep_extraction import (
    ExtractionSession,
    ExtractionConsensus,
    ExtractionTier,
    ItemType,
    ConsensusStatus,
)


logger = logging.getLogger(__name__)


class ProjectExportService:
    """
    Export Deep Extraction results to markdown project structure.

    Output structure:
    ```
    {output_dir}/
    ├── project-summary.md           # Overview with all epics, FP totals
    ├── EPIC-001/
    │   ├── epic.md                  # Epic details + confidence explanation
    │   ├── FEAT-001/
    │   │   ├── feature.md           # Feature details
    │   │   ├── STORY-001.md         # User story with AC, FP
    │   │   └── STORY-002.md
    │   └── FEAT-002/
    │       └── ...
    └── EPIC-002/
        └── ...
    ```
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_session(
        self,
        session_id: UUID,
        output_dir: Path,
        include_tasks: bool = True,
    ) -> Dict[str, Any]:
        """
        Export a completed extraction session to markdown files.

        Args:
            session_id: The extraction session to export
            output_dir: Directory to write markdown files
            include_tasks: Whether to include tasks in story files

        Returns:
            Export summary with file counts and paths
        """
        # Get session with consensus items
        result = await self.db.execute(
            select(ExtractionSession)
            .options(selectinload(ExtractionSession.consensus_items))
            .where(ExtractionSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Get accepted items grouped by type
        accepted_items = [
            item for item in session.consensus_items
            if item.status in [ConsensusStatus.AUTO_ACCEPTED.value, ConsensusStatus.ACCEPTED.value]
        ]

        # Build hierarchy from synthesis data
        hierarchy = self._build_hierarchy_from_synthesis(session, accepted_items)

        # Generate files
        files_created = []

        # Generate project summary
        summary_path = output_path / "project-summary.md"
        summary_content = self._generate_project_summary(session, hierarchy)
        summary_path.write_text(summary_content, encoding='utf-8')
        files_created.append(str(summary_path))

        # Generate epic files
        for epic in hierarchy.get("epics", []):
            epic_files = self._generate_epic_files(
                epic=epic,
                output_path=output_path,
                include_tasks=include_tasks,
            )
            files_created.extend(epic_files)

        logger.info(f"Exported {len(files_created)} files to {output_path}")

        return {
            "session_id": str(session_id),
            "output_dir": str(output_path),
            "files_created": len(files_created),
            "file_paths": files_created,
            "epics": len(hierarchy.get("epics", [])),
            "total_function_points": hierarchy.get("total_fp", 0),
        }

    def _build_hierarchy_from_synthesis(
        self,
        session: ExtractionSession,
        accepted_items: List[ExtractionConsensus],
    ) -> Dict[str, Any]:
        """Build epic→feature→story→task hierarchy from synthesis data."""
        # Group items by type
        epics = [i for i in accepted_items if i.item_type == ItemType.EPIC.value]
        features = [i for i in accepted_items if i.item_type == ItemType.FEATURE.value]
        stories = [i for i in accepted_items if i.item_type == ItemType.STORY.value]
        tasks = [i for i in accepted_items if i.item_type == ItemType.TASK.value]

        # Build hierarchy using synthesized IDs if available
        hierarchy_epics = []
        total_fp = 0

        for i, epic in enumerate(epics, 1):
            epic_data = epic.item_data or {}
            epic_id = epic_data.get("synthesized_id", f"EPIC-{i:03d}")

            epic_entry = {
                "id": epic_id,
                "title": epic.item_title,
                "description": epic.item_description,
                "confidence_score": epic.confidence_score,
                "confidence_explanation": epic_data.get("confidence_explanation", ""),
                "total_function_points": epic_data.get("total_function_points", 0),
                "supporting_llms": epic.supporting_llms,
                "features": [],
            }

            # Find features for this epic
            epic_features = [
                f for f in features
                if (f.item_data or {}).get("parent_epic_id") == epic_id
            ]

            # If no parent linkage, assign features by order
            if not epic_features and i == 1:
                epic_features = features  # Assign all to first epic as fallback

            for j, feature in enumerate(epic_features, 1):
                feat_data = feature.item_data or {}
                feat_id = feat_data.get("synthesized_id", f"FEAT-{i:02d}{j:02d}")

                feat_entry = {
                    "id": feat_id,
                    "title": feature.item_title,
                    "description": feature.item_description,
                    "confidence_score": feature.confidence_score,
                    "confidence_explanation": feat_data.get("confidence_explanation", ""),
                    "stories": [],
                }

                # Find stories for this feature
                feat_stories = [
                    s for s in stories
                    if (s.item_data or {}).get("parent_feature_id") == feat_id
                ]

                for k, story in enumerate(feat_stories, 1):
                    story_data = story.item_data or {}
                    story_id = story_data.get("synthesized_id", f"STORY-{i:02d}{j:02d}{k:02d}")
                    story_fp = story_data.get("function_points", 10)
                    total_fp += story_fp

                    story_entry = {
                        "id": story_id,
                        "title": story.item_title,
                        "description": story.item_description,
                        "function_points": story_fp,
                        "fp_rationale": story_data.get("fp_rationale", ""),
                        "story_points": story_data.get("story_points", 5),
                        "acceptance_criteria": story_data.get("acceptance_criteria", []),
                        "tasks": [],
                    }

                    # Find tasks for this story
                    story_tasks = [
                        t for t in tasks
                        if (t.item_data or {}).get("parent_story_id") == story_id
                    ]

                    for m, task in enumerate(story_tasks, 1):
                        task_data = task.item_data or {}
                        task_id = task_data.get("synthesized_id", f"TASK-{story_id}-{m:02d}")
                        task_fp = task_data.get("function_points", 3)
                        total_fp += task_fp

                        task_entry = {
                            "id": task_id,
                            "title": task.item_title,
                            "task_type": task_data.get("task_type", "backend"),
                            "function_points": task_fp,
                            "estimated_hours": task_data.get("estimated_hours", 4),
                        }
                        story_entry["tasks"].append(task_entry)

                    feat_entry["stories"].append(story_entry)

                epic_entry["features"].append(feat_entry)

            hierarchy_epics.append(epic_entry)

        return {
            "epics": hierarchy_epics,
            "total_fp": total_fp,
            "session_tier": session.tier,
            "avg_confidence": session.avg_confidence,
        }

    def _generate_project_summary(
        self,
        session: ExtractionSession,
        hierarchy: Dict[str, Any],
    ) -> str:
        """Generate project-summary.md content."""
        epics = hierarchy.get("epics", [])
        total_fp = hierarchy.get("total_fp", 0)

        content = f"""# Project Summary

**Generated**: {datetime.utcnow().isoformat()}
**Extraction Tier**: {session.tier}
**Source Path**: {session.source_path}
**Total Files Analyzed**: {session.total_files}

## Overview

| Metric | Value |
|--------|-------|
| Total Epics | {len(epics)} |
| Total Features | {sum(len(e.get('features', [])) for e in epics)} |
| Total Stories | {sum(len(f.get('stories', [])) for e in epics for f in e.get('features', []))} |
| Total Function Points | {total_fp} |
| Average Confidence | {session.avg_confidence:.1%} |

## Epics

"""
        for epic in epics:
            features = epic.get("features", [])
            epic_fp = epic.get("total_function_points", 0)
            content += f"""### {epic['id']}: {epic['title']}

- **Confidence**: {epic['confidence_score']:.1%}
- **Function Points**: {epic_fp}
- **Features**: {len(features)}

{epic.get('confidence_explanation', '')}

"""

        content += """---

## Confidence Explanations

The confidence scores indicate how many LLMs agreed on each item during extraction:
- **>90%**: Strong consensus across most LLMs
- **80-90%**: Good consensus with minor variations
- **70-80%**: Moderate consensus, some LLMs disagreed
- **<70%**: Low consensus, human review recommended

## Function Point Methodology

Function points are estimated using IFPUG CPM 4.3.1 methodology:
- **ILF** (Internal Logical Files): 7-15 FP
- **EIF** (External Interface Files): 5-10 FP
- **EI** (External Inputs): 3-6 FP
- **EO** (External Outputs): 4-7 FP
- **EQ** (External Queries): 3-6 FP

---
*Generated by MarQed Deep Extraction Pipeline*
"""
        return content

    def _generate_epic_files(
        self,
        epic: Dict[str, Any],
        output_path: Path,
        include_tasks: bool = True,
    ) -> List[str]:
        """Generate epic directory and all nested files."""
        files_created = []
        epic_id = epic["id"]

        # Create epic directory
        epic_dir = output_path / epic_id
        epic_dir.mkdir(exist_ok=True)

        # Generate epic.md
        epic_file = epic_dir / "epic.md"
        epic_content = self._generate_epic_content(epic)
        epic_file.write_text(epic_content, encoding='utf-8')
        files_created.append(str(epic_file))

        # Generate feature directories and files
        for feature in epic.get("features", []):
            feat_files = self._generate_feature_files(
                feature=feature,
                epic_dir=epic_dir,
                include_tasks=include_tasks,
            )
            files_created.extend(feat_files)

        return files_created

    def _generate_epic_content(self, epic: Dict[str, Any]) -> str:
        """Generate epic.md content."""
        features = epic.get("features", [])

        content = f"""# {epic['id']}: {epic['title']}

## Description

{epic.get('description', 'No description provided.')}

## Confidence

- **Score**: {epic['confidence_score']:.1%}
- **Supporting LLMs**: {', '.join(epic.get('supporting_llms', []))}

### Explanation

{epic.get('confidence_explanation', 'No confidence explanation available.')}

## Metrics

| Metric | Value |
|--------|-------|
| Total Function Points | {epic.get('total_function_points', 0)} |
| Features | {len(features)} |
| Stories | {sum(len(f.get('stories', [])) for f in features)} |

## Features

"""
        for feature in features:
            story_count = len(feature.get("stories", []))
            content += f"- [{feature['id']}]({feature['id']}/feature.md): {feature['title']} ({story_count} stories)\n"

        content += """
---
*Generated by MarQed Deep Extraction Pipeline*
"""
        return content

    def _generate_feature_files(
        self,
        feature: Dict[str, Any],
        epic_dir: Path,
        include_tasks: bool = True,
    ) -> List[str]:
        """Generate feature directory and story files."""
        files_created = []
        feat_id = feature["id"]

        # Create feature directory
        feat_dir = epic_dir / feat_id
        feat_dir.mkdir(exist_ok=True)

        # Generate feature.md
        feat_file = feat_dir / "feature.md"
        feat_content = self._generate_feature_content(feature)
        feat_file.write_text(feat_content, encoding='utf-8')
        files_created.append(str(feat_file))

        # Generate story files
        for story in feature.get("stories", []):
            story_file = feat_dir / f"{story['id']}.md"
            story_content = self._generate_story_content(story, include_tasks)
            story_file.write_text(story_content, encoding='utf-8')
            files_created.append(str(story_file))

        return files_created

    def _generate_feature_content(self, feature: Dict[str, Any]) -> str:
        """Generate feature.md content."""
        stories = feature.get("stories", [])
        total_fp = sum(s.get("function_points", 0) for s in stories)
        total_sp = sum(s.get("story_points", 0) for s in stories)

        content = f"""# {feature['id']}: {feature['title']}

## Description

{feature.get('description', 'No description provided.')}

## Confidence

- **Score**: {feature['confidence_score']:.1%}

### Explanation

{feature.get('confidence_explanation', 'No confidence explanation available.')}

## Metrics

| Metric | Value |
|--------|-------|
| Stories | {len(stories)} |
| Total Function Points | {total_fp} |
| Total Story Points | {total_sp} |

## Stories

| ID | Title | FP | SP |
|----|-------|----|----|
"""
        for story in stories:
            content += f"| [{story['id']}]({story['id']}.md) | {story['title'][:50]} | {story.get('function_points', 0)} | {story.get('story_points', 0)} |\n"

        content += """
---
*Generated by MarQed Deep Extraction Pipeline*
"""
        return content

    def _generate_story_content(
        self,
        story: Dict[str, Any],
        include_tasks: bool = True,
    ) -> str:
        """Generate story markdown content."""
        content = f"""# {story['id']}: {story['title']}

## User Story

{story.get('description', story['title'])}

## Estimates

| Metric | Value | Rationale |
|--------|-------|-----------|
| Function Points | {story.get('function_points', 0)} | {story.get('fp_rationale', 'Estimated based on complexity')} |
| Story Points | {story.get('story_points', 0)} | Relative effort estimate |

## Acceptance Criteria

"""
        criteria = story.get("acceptance_criteria", [])
        if criteria:
            for i, ac in enumerate(criteria, 1):
                content += f"{i}. {ac}\n"
        else:
            content += "- [ ] Acceptance criteria to be defined\n"

        if include_tasks and story.get("tasks"):
            content += """
## Technical Tasks

| ID | Task | Type | FP | Hours |
|----|------|------|----|----|
"""
            for task in story.get("tasks", []):
                content += f"| {task['id']} | {task['title'][:40]} | {task.get('task_type', 'backend')} | {task.get('function_points', 0)} | {task.get('estimated_hours', 0)} |\n"

        content += """
---
*Generated by MarQed Deep Extraction Pipeline*
"""
        return content


async def create_project_export_service(db: AsyncSession) -> ProjectExportService:
    """Factory function to create ProjectExportService."""
    return ProjectExportService(db)
