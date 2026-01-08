"""
Backlog Service

Reads project backlog (epics/features/stories/tasks) from registered applications.
Provides data for the hub to display project progress.
"""

import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TaskInfo:
    """Task information."""
    id: str
    title: str
    status: str
    priority: str
    story_points: int
    function_points: int
    category: str
    path: str


@dataclass
class StoryInfo:
    """Story information."""
    id: str
    title: str
    status: str
    priority: str
    story_points: int
    function_points: int
    tasks: List[TaskInfo] = field(default_factory=list)
    path: str = ""


@dataclass
class FeatureInfo:
    """Feature information."""
    id: str
    title: str
    status: str
    stories: List[StoryInfo] = field(default_factory=list)
    path: str = ""


@dataclass
class EpicInfo:
    """Epic information."""
    id: str
    title: str
    status: str
    priority: str
    story_points: int
    function_points: int
    features: List[FeatureInfo] = field(default_factory=list)
    path: str = ""


@dataclass
class ProjectBacklog:
    """Complete project backlog."""
    name: str
    status: str
    total_story_points: int
    total_function_points: int
    completed_story_points: int
    progress_percent: float
    epics: List[EpicInfo] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)


class BacklogService:
    """
    Service for reading project backlog from markdown files.

    Expected structure:
        doc/project/
        ├── project.md
        └── epics/
            ├── EPIC-001-*/
            │   ├── epic.md
            │   └── features/
            │       └── FEATURE-001-*/
            │           ├── feature.md
            │           └── stories/
            │               └── STORY-001-*/
            │                   ├── story.md
            │                   └── tasks/
            │                       └── TASK-001.md
    """

    def get_backlog(self, app_root_path: str) -> Optional[ProjectBacklog]:
        """
        Read the complete backlog for an application.

        Args:
            app_root_path: Root path of the application (e.g., /opt/projecten/hci-crs)

        Returns:
            ProjectBacklog with all epics, features, stories, tasks
        """
        project_path = Path(app_root_path) / "doc" / "project"

        if not project_path.exists():
            logger.warning(f"No project folder found at {project_path}")
            return None

        # Read project.md
        project_md = project_path / "project.md"
        if not project_md.exists():
            logger.warning(f"No project.md found at {project_md}")
            return None

        project_data = self._parse_markdown_frontmatter(project_md)

        # Read all epics
        epics = []
        epics_path = project_path / "epics"

        if epics_path.exists():
            for epic_dir in sorted(epics_path.iterdir()):
                if epic_dir.is_dir() and epic_dir.name.startswith("EPIC-"):
                    epic = self._read_epic(epic_dir)
                    if epic:
                        epics.append(epic)

        # Calculate totals
        total_sp = sum(e.story_points for e in epics)
        total_fp = sum(e.function_points for e in epics)
        completed_sp = self._calculate_completed_sp(epics)
        progress = (completed_sp / total_sp * 100) if total_sp > 0 else 0

        return ProjectBacklog(
            name=project_data.get("name", Path(app_root_path).name),
            status=project_data.get("status", "ACTIVE"),
            total_story_points=total_sp,
            total_function_points=total_fp,
            completed_story_points=completed_sp,
            progress_percent=round(progress, 1),
            epics=epics,
            statistics={
                "total_epics": len(epics),
                "total_features": sum(len(e.features) for e in epics),
                "total_stories": sum(len(f.stories) for e in epics for f in e.features),
                "total_tasks": sum(
                    len(s.tasks)
                    for e in epics
                    for f in e.features
                    for s in f.stories
                ),
                "epics_by_status": self._count_by_status([e.status for e in epics]),
            }
        )

    def _read_epic(self, epic_dir: Path) -> Optional[EpicInfo]:
        """Read an epic and its features."""
        epic_md = epic_dir / "epic.md"
        if not epic_md.exists():
            return None

        data = self._parse_markdown_frontmatter(epic_md)

        # Read features
        features = []
        features_path = epic_dir / "features"

        if features_path.exists():
            for feature_dir in sorted(features_path.iterdir()):
                if feature_dir.is_dir() and feature_dir.name.startswith("FEATURE-"):
                    feature = self._read_feature(feature_dir)
                    if feature:
                        features.append(feature)

        return EpicInfo(
            id=epic_dir.name,
            title=data.get("title", epic_dir.name),
            status=data.get("status", "PLANNED"),
            priority=data.get("priority", "MEDIUM"),
            story_points=self._extract_int(data.get("story_points", 0)),
            function_points=self._extract_int(data.get("function_points", 0)),
            features=features,
            path=str(epic_dir),
        )

    def _read_feature(self, feature_dir: Path) -> Optional[FeatureInfo]:
        """Read a feature and its stories."""
        feature_md = feature_dir / "feature.md"
        if not feature_md.exists():
            return None

        data = self._parse_markdown_frontmatter(feature_md)

        # Read stories
        stories = []
        stories_path = feature_dir / "stories"

        if stories_path.exists():
            for story_dir in sorted(stories_path.iterdir()):
                if story_dir.is_dir() and story_dir.name.startswith("STORY-"):
                    story = self._read_story(story_dir)
                    if story:
                        stories.append(story)

        return FeatureInfo(
            id=feature_dir.name,
            title=data.get("title", feature_dir.name),
            status=data.get("status", "PLANNED"),
            stories=stories,
            path=str(feature_dir),
        )

    def _read_story(self, story_dir: Path) -> Optional[StoryInfo]:
        """Read a story and its tasks."""
        story_md = story_dir / "story.md"
        if not story_md.exists():
            return None

        data = self._parse_markdown_frontmatter(story_md)

        # Read tasks
        tasks = []
        tasks_path = story_dir / "tasks"

        if tasks_path.exists():
            for task_file in sorted(tasks_path.glob("TASK-*.md")):
                task = self._read_task(task_file)
                if task:
                    tasks.append(task)

        return StoryInfo(
            id=story_dir.name,
            title=data.get("title", story_dir.name),
            status=data.get("status", "PLANNED"),
            priority=data.get("priority", "MEDIUM"),
            story_points=self._extract_int(data.get("story_points", 0)),
            function_points=self._extract_int(data.get("function_points", 0)),
            tasks=tasks,
            path=str(story_dir),
        )

    def _read_task(self, task_file: Path) -> Optional[TaskInfo]:
        """Read a task file."""
        data = self._parse_markdown_frontmatter(task_file)

        # Extract ID from filename (TASK-001.md -> TASK-001)
        task_id = task_file.stem

        return TaskInfo(
            id=task_id,
            title=data.get("title", task_id),
            status=data.get("status", "PLANNED"),
            priority=data.get("priority", "MEDIUM"),
            story_points=self._extract_int(data.get("story_points", 0)),
            function_points=self._extract_int(data.get("function_points", 0)),
            category=data.get("category", ""),
            path=str(task_file),
        )

    def _parse_markdown_frontmatter(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse markdown file and extract frontmatter-style metadata.

        Supports both YAML frontmatter and inline **Key**: Value format.
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return {}

        data = {}

        # Try to extract title from first heading
        title_match = re.search(r'^#\s+(?:TASK-\d+\s*\|?\s*)?(.+)$', content, re.MULTILINE)
        if title_match:
            data['title'] = title_match.group(1).strip()

        # Extract **Key**: Value patterns
        patterns = {
            'status': r'\*\*Status\*\*:\s*(\w+)',
            'priority': r'\*\*Priority\*\*:\s*(\w+)',
            'category': r'\*\*Category\*\*:\s*(\w+)',
            'type': r'\*\*Type\*\*:\s*(\w+)',
            'name': r'^#\s*Project:\s*(.+)$',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if match:
                data[key] = match.group(1).strip()

        # Extract story points and function points
        # Pattern 1: **Story Points**: X or **Total**: X under ## Story Points section
        sp_match = re.search(r'(?:\*\*)?(?:Story Points|Total Story Points)(?:\*\*)?:\s*(\d+)', content, re.IGNORECASE)
        if sp_match:
            data['story_points'] = int(sp_match.group(1))

        fp_match = re.search(r'(?:\*\*)?(?:Function Points|Total Function Points)(?:\*\*)?:\s*(\d+)', content, re.IGNORECASE)
        if fp_match:
            data['function_points'] = int(fp_match.group(1))

        # Pattern 2: ## Story Points section with **Total**: X
        sp_section_match = re.search(r'^##\s*Story Points\s*\n+\*\*Total\*\*:\s*(\d+)', content, re.MULTILINE)
        if sp_section_match and 'story_points' not in data:
            data['story_points'] = int(sp_section_match.group(1))

        fp_section_match = re.search(r'^##\s*Function Points\s*\n+\*\*Total\*\*:\s*(\d+)', content, re.MULTILINE)
        if fp_section_match and 'function_points' not in data:
            data['function_points'] = int(fp_section_match.group(1))

        # Pattern 3: ## Story Points: X format
        sp_section = re.search(r'^##\s*Story Points:\s*(\d+)', content, re.MULTILINE)
        if sp_section and 'story_points' not in data:
            data['story_points'] = int(sp_section.group(1))

        fp_section = re.search(r'^##\s*Function Points:\s*(\d+)', content, re.MULTILINE)
        if fp_section and 'function_points' not in data:
            data['function_points'] = int(fp_section.group(1))

        return data

    def _extract_int(self, value: Any) -> int:
        """Safely extract integer from various formats."""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return 0
        return 0

    def _calculate_completed_sp(self, epics: List[EpicInfo]) -> int:
        """Calculate completed story points."""
        completed = 0
        for epic in epics:
            if epic.status.upper() == "COMPLETED":
                completed += epic.story_points
            else:
                # Check individual stories
                for feature in epic.features:
                    for story in feature.stories:
                        if story.status.upper() == "COMPLETED":
                            completed += story.story_points
        return completed

    def _count_by_status(self, statuses: List[str]) -> Dict[str, int]:
        """Count items by status."""
        counts = {}
        for status in statuses:
            status_upper = status.upper()
            counts[status_upper] = counts.get(status_upper, 0) + 1
        return counts


# Singleton
_service: Optional[BacklogService] = None


def get_backlog_service() -> BacklogService:
    """Get the global backlog service instance."""
    global _service
    if _service is None:
        _service = BacklogService()
    return _service
