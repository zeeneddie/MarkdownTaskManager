"""
MultiFileProjectGenerator - Generate nested markdown structure from database records
"""

from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import yaml
import logging

logger = logging.getLogger(__name__)


class MultiFileProjectGenerator:
    """Generate markdown files from database records in nested structure"""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.epics_dir = self.project_root / "Projecten" / "MarkdownTaskManager"
        self.archive_dir = self.project_root / "archive" / "epics"

    def generate_project(self, project_data: Dict):
        """
        Generate all markdown files from project data.

        Args:
            project_data: Dict with epics, features, stories, tasks
        """
        logger.info(f"Generating project files in {self.project_root}")

        # Ensure directories exist
        self.epics_dir.mkdir(exist_ok=True, parents=True)
        self.archive_dir.mkdir(exist_ok=True, parents=True)

        epics = project_data.get("epics", [])

        for epic in epics:
            try:
                self.generate_epic(epic)
            except Exception as e:
                logger.error(f"Error generating epic {epic.get('id')}: {str(e)}")
                continue

        logger.info(f"Generated {len(epics)} epics")

    def generate_epic(self, epic: Dict):
        """
        Generate epic directory and file.

        Args:
            epic: Dict with epic data including nested features
        """
        epic_id = epic.get("id")
        if not epic_id:
            logger.error("Epic missing id")
            return

        logger.debug(f"Generating epic: {epic_id}")

        # Create epic directory
        epic_dir = self.epics_dir / epic_id
        epic_dir.mkdir(exist_ok=True, parents=True)

        # Generate epic.md file
        epic_file = epic_dir / "epic.md"
        epic_content = self._generate_epic_content(epic)

        with open(epic_file, 'w', encoding='utf-8') as f:
            f.write(epic_content)

        logger.debug(f"Generated {epic_file}")

        # Generate nested features (directly under epic, no 'features' folder)
        features = epic.get("features", [])
        if features:
            for feature in features:
                try:
                    self.generate_feature(feature, epic_dir)
                except Exception as e:
                    logger.error(f"Error generating feature {feature.get('id')}: {str(e)}")
                    continue

    def generate_feature(self, feature: Dict, epic_dir: Path):
        """
        Generate feature directory and file.

        Args:
            feature: Dict with feature data including nested stories
            epic_dir: Parent epic directory
        """
        feature_id = feature.get("id")
        if not feature_id:
            logger.error("Feature missing id")
            return

        logger.debug(f"Generating feature: {feature_id}")

        # Create feature directory (directly under epic, no 'features' folder)
        feature_dir = epic_dir / feature_id
        feature_dir.mkdir(exist_ok=True, parents=True)

        # Generate feature.md file
        feature_file = feature_dir / "feature.md"
        feature_content = self._generate_feature_content(feature)

        with open(feature_file, 'w', encoding='utf-8') as f:
            f.write(feature_content)

        logger.debug(f"Generated {feature_file}")

        # Generate nested stories (directly under feature, no 'stories' folder)
        stories = feature.get("stories", [])
        if stories:
            for story in stories:
                try:
                    self.generate_story(story, feature_dir)
                except Exception as e:
                    logger.error(f"Error generating story {story.get('id')}: {str(e)}")
                    continue

    def generate_story(self, story: Dict, feature_dir: Path):
        """
        Generate story directory and file.

        Args:
            story: Dict with story data including nested tasks
            feature_dir: Parent feature directory
        """
        story_id = story.get("id")
        if not story_id:
            logger.error("Story missing id")
            return

        logger.debug(f"Generating story: {story_id}")

        # Create story directory (directly under feature, no 'stories' folder)
        story_dir = feature_dir / story_id
        story_dir.mkdir(exist_ok=True, parents=True)

        # Generate story.md file
        story_file = story_dir / "story.md"
        story_content = self._generate_story_content(story)

        with open(story_file, 'w', encoding='utf-8') as f:
            f.write(story_content)

        logger.debug(f"Generated {story_file}")

        # Generate nested tasks (directly under story, no 'tasks' folder)
        tasks = story.get("tasks", [])
        if tasks:
            for task in tasks:
                try:
                    self.generate_task(task, story_dir)
                except Exception as e:
                    logger.error(f"Error generating task {task.get('id')}: {str(e)}")
                    continue

    def generate_task(self, task: Dict, story_dir: Path):
        """
        Generate task file.

        Args:
            task: Dict with task data
            story_dir: Parent story directory
        """
        task_id = task.get("id")
        if not task_id:
            logger.error("Task missing id")
            return

        logger.debug(f"Generating task: {task_id}")

        # Generate TASK-XXX.md file (directly under story, no 'tasks' folder)
        task_file = story_dir / f"{task_id}.md"
        task_content = self._generate_task_content(task)

        with open(task_file, 'w', encoding='utf-8') as f:
            f.write(task_content)

        logger.debug(f"Generated {task_file}")

    def _generate_epic_content(self, epic: Dict) -> str:
        """Generate epic markdown content"""

        # Generate frontmatter
        frontmatter = self._generate_frontmatter(epic, [
            'id', 'type', 'title', 'status', 'priority', 'phase',
            'owner', 'created_at', 'updated_at', 'started_at',
            'target_date', 'sp_total', 'sp_completed', 'progress',
            'epic_type', 'tags', 'dependencies'
        ])

        # Generate body
        body = f"# {epic['id']}: {epic['title']}\n\n"

        # Summary section
        body += "## 📊 Summary\n\n"
        body += f"{epic.get('description', '')}\n\n"

        # Business Value section
        if epic.get('business_value'):
            body += "## 🎯 Business Value\n\n"
            body += f"{epic['business_value']}\n\n"

        # Features section
        body += "## 📋 Features\n\n"
        features = epic.get('features', [])
        if features:
            for feature in features:
                status_emoji = self._get_status_emoji(feature.get('status'))
                body += f"- [{feature['id']}](features/{feature['id']}/feature.md) - "
                body += f"{feature['title']} ({feature.get('sp_total', 0)} FP, {status_emoji} {feature.get('status', 'PLANNED')})\n"
        else:
            body += "*(No features yet)*\n"

        body += "\n"

        # Metrics section
        body += "## 📈 Metrics\n\n"
        body += f"- **Story Points:** {epic.get('sp_total', 0)} FP\n"
        body += f"- **T-shirt Size:** {self._calculate_tshirt_size(epic.get('sp_total', 0))}\n"
        body += f"- **Estimated Sprints:** {epic.get('estimated_sprints', 'TBD')}\n"
        body += f"- **Confidence:** ±15%\n\n"

        # Footer
        body += "---\n\n"
        body += f"**Last Sync:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        return f"---\n{frontmatter}---\n\n{body}"

    def _generate_feature_content(self, feature: Dict) -> str:
        """Generate feature markdown content"""

        frontmatter = self._generate_frontmatter(feature, [
            'id', 'type', 'parent_id', 'title', 'status', 'priority',
            'owner', 'created_at', 'updated_at', 'sp_total', 'sp_completed',
            'tags'
        ])

        body = f"# {feature['id']}: {feature['title']}\n\n"

        # Parent link
        body += f"**Parent:** [EPIC-{feature.get('parent_id', '').split('-')[1] if feature.get('parent_id') else ''}](../../epic.md)\n\n"

        # Description section
        body += "## 📋 Description\n\n"
        body += f"{feature.get('description', '')}\n\n"

        # Stories section
        body += "## 📊 Stories\n\n"
        stories = feature.get('stories', [])
        if stories:
            for story in stories:
                status_emoji = self._get_status_emoji(story.get('status'))
                body += f"- [{story['id']}](stories/{story['id']}/story.md) - "
                body += f"{story['title']} ({story.get('sp', 0)} SP, {status_emoji} {story.get('status', 'PLANNED')})\n"
        else:
            body += "*(No stories yet)*\n"

        body += "\n"

        # Metrics section
        body += "## 📈 Metrics\n\n"
        body += f"- **Function Points:** {feature.get('sp_total', 0)} FP\n"
        body += f"- **Story Points:** {sum(s.get('sp', 0) for s in stories)} SP total\n"

        # Footer
        body += "\n---\n\n"
        body += f"**Last Sync:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        return f"---\n{frontmatter}---\n\n{body}"

    def _generate_story_content(self, story: Dict) -> str:
        """Generate story markdown content"""

        frontmatter = self._generate_frontmatter(story, [
            'id', 'type', 'parent_id', 'title', 'status', 'priority',
            'sprint', 'assigned_to', 'sp', 'estimated_hours', 'actual_hours',
            'created_at', 'started_at', 'completed_at', 'tags'
        ])

        body = f"# {story['id']}: {story['title']}\n\n"

        # Parent link
        body += f"**Parent:** [FEATURE-{story.get('parent_id', '').split('-')[1] if story.get('parent_id') else ''}](../../feature.md)\n\n"

        # User Story section
        body += "## 📋 User Story\n\n"
        user_story_as = story.get('user_story_as', story.get('description', ''))
        user_story_want = story.get('user_story_want', '')
        user_story_so_that = story.get('user_story_so_that', '')

        if user_story_as or user_story_want or user_story_so_that:
            body += f"**As a** {user_story_as}\n"
            body += f"**I want to** {user_story_want}\n"
            body += f"**So that** {user_story_so_that}\n\n"
        else:
            body += f"{story.get('description', '')}\n\n"

        # Acceptance Criteria section
        body += "## ✅ Acceptance Criteria\n\n"
        acceptance_criteria = story.get('acceptance_criteria', [])
        if acceptance_criteria:
            for criterion in acceptance_criteria:
                checked = 'x' if criterion.get('checked') else ' '
                body += f"- [{checked}] {criterion.get('text', '')}\n"
        else:
            body += "*(No acceptance criteria defined)*\n"

        body += "\n"

        # Tasks section
        body += "## 🔧 Tasks\n\n"
        tasks = story.get('tasks', [])
        if tasks:
            for task in tasks:
                status_emoji = self._get_status_emoji(task.get('status'))
                est_hours = task.get('estimated_hours', 0)
                body += f"- [{task['id']}](tasks/{task['id']}.md) - "
                body += f"{task['title']} ({status_emoji} {est_hours}h)\n"
        else:
            body += "*(No tasks yet)*\n"

        body += "\n"

        # Metrics section
        body += "## 📊 Metrics\n\n"
        body += f"- **Estimated:** {story.get('sp', 0)} SP ({story.get('estimated_hours', 0)} hours)\n"
        if story.get('actual_hours'):
            body += f"- **Actual:** {story.get('actual_hours')} hours\n"
            variance = ((story.get('actual_hours', 0) - story.get('estimated_hours', 0)) / story.get('estimated_hours', 1)) * 100
            body += f"- **Variance:** {variance:+.0f}%\n"
        body += f"- **Confidence:** ±10%\n\n"

        # Footer
        body += "---\n\n"
        body += f"**Last Sync:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        return f"---\n{frontmatter}---\n\n{body}"

    def _generate_task_content(self, task: Dict) -> str:
        """Generate task markdown content"""

        frontmatter = self._generate_frontmatter(task, [
            'id', 'type', 'parent_id', 'title', 'status', 'priority',
            'assigned_to', 'estimated_hours', 'actual_hours',
            'created_at', 'completed_at', 'tags'
        ])

        body = f"# {task['id']}: {task['title']}\n\n"

        # Parent link
        body += f"**Parent:** [STORY-{task.get('parent_id', '').split('-')[1] if task.get('parent_id') else ''}](../story.md)\n\n"

        # Description section
        body += "## 📋 Description\n\n"
        body += f"{task.get('description', '')}\n\n"

        # Checklist section
        body += "## ✅ Checklist\n\n"
        checklist = task.get('checklist', [])
        if checklist:
            for item in checklist:
                checked = 'x' if item.get('checked') else ' '
                body += f"- [{checked}] {item.get('text', '')}\n"
        else:
            body += "*(No checklist)*\n"

        body += "\n"

        # Footer
        body += "---\n\n"
        if task.get('completed_at'):
            body += f"**Completed:** {task['completed_at']}\n"
        else:
            body += f"**Created:** {task.get('created_at', datetime.now().strftime('%Y-%m-%d'))}\n"

        return f"---\n{frontmatter}---\n\n{body}"

    def _generate_frontmatter(self, data: Dict, fields: List[str]) -> str:
        """
        Generate YAML frontmatter from data dict.

        Args:
            data: Data dictionary
            fields: List of field names to include

        Returns:
            YAML string
        """
        frontmatter_data = {}

        for field in fields:
            if field in data and data[field] is not None:
                value = data[field]

                # Convert datetime to string
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d')

                frontmatter_data[field] = value

        return yaml.dump(frontmatter_data, default_flow_style=False, allow_unicode=True)

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status"""
        status_map = {
            'PLANNED': '📋',
            'IN_PROGRESS': '🚀',
            'TESTING': '🧪',
            'COMPLETED': '✅',
            'BLOCKED': '🚫',
            'TODO': '📝',
            'DONE': '✅'
        }
        return status_map.get(status, '📝')

    def _calculate_tshirt_size(self, fp: int) -> str:
        """Calculate T-shirt size from Function Points"""
        if fp < 5:
            return "XS"
        elif fp < 13:
            return "S"
        elif fp < 21:
            return "M"
        elif fp < 34:
            return "L"
        elif fp < 55:
            return "XL"
        else:
            return "XXL"


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # Test data
    test_project = {
        "epics": [
            {
                "id": "EPIC-002",
                "type": "epic",
                "title": "User Authentication System",
                "status": "PLANNED",
                "priority": "HIGH",
                "phase": "INITIATIE",
                "owner": "eddie",
                "created_at": datetime(2025, 11, 12),
                "updated_at": datetime(2025, 11, 12),
                "target_date": datetime(2025, 12, 30),
                "sp_total": 21,
                "sp_completed": 0,
                "progress": 0,
                "epic_type": "FUNCTIONAL",
                "tags": ["auth", "security", "backend"],
                "dependencies": [],
                "description": "Implement secure user authentication with JWT tokens and refresh mechanism.",
                "business_value": "Enable user accounts and personalized experiences. Required for premium features.",
                "features": [
                    {
                        "id": "FEATURE-003",
                        "type": "feature",
                        "parent_id": "EPIC-002",
                        "title": "JWT Authentication",
                        "status": "PLANNED",
                        "priority": "HIGH",
                        "owner": "eddie",
                        "created_at": datetime(2025, 11, 12),
                        "updated_at": datetime(2025, 11, 12),
                        "sp_total": 13,
                        "sp_completed": 0,
                        "tags": ["jwt", "auth"],
                        "description": "Implement JWT-based authentication with access and refresh tokens.",
                        "stories": [
                            {
                                "id": "STORY-003",
                                "type": "story",
                                "parent_id": "FEATURE-003",
                                "title": "Implement login endpoint",
                                "status": "PLANNED",
                                "priority": "HIGH",
                                "sprint": "Sprint 16",
                                "assigned_to": "eddie",
                                "sp": 5,
                                "estimated_hours": 8,
                                "created_at": datetime(2025, 11, 12),
                                "tags": ["backend", "api"],
                                "user_story_as": "user",
                                "user_story_want": "login with email and password",
                                "user_story_so_that": "I can access my account",
                                "acceptance_criteria": [
                                    {"text": "API endpoint POST /api/auth/login exists", "checked": False},
                                    {"text": "Returns JWT access token on success", "checked": False},
                                    {"text": "Returns refresh token in httpOnly cookie", "checked": False},
                                    {"text": "Returns 401 on invalid credentials", "checked": False}
                                ],
                                "tasks": [
                                    {
                                        "id": "TASK-003",
                                        "type": "task",
                                        "parent_id": "STORY-003",
                                        "title": "Create login endpoint",
                                        "status": "TODO",
                                        "priority": "HIGH",
                                        "assigned_to": "eddie",
                                        "estimated_hours": 4,
                                        "created_at": datetime(2025, 11, 12),
                                        "tags": ["backend"],
                                        "description": "Create POST /api/auth/login endpoint in FastAPI.",
                                        "checklist": [
                                            {"text": "Define LoginRequest schema", "checked": False},
                                            {"text": "Implement login route", "checked": False},
                                            {"text": "Add password hashing verification", "checked": False},
                                            {"text": "Generate JWT tokens", "checked": False}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }

    generator = MultiFileProjectGenerator(Path("/home/eddie/Projects/MarkdownTaskManager"))
    generator.generate_project(test_project)

    print("\n" + "="*60)
    print("Generated Files:")
    print("="*60)

    import subprocess
    result = subprocess.run(
        ["find", "epics/EPIC-002", "-type", "f"],
        cwd="/home/eddie/Projects/MarkdownTaskManager",
        capture_output=True,
        text=True
    )
    print(result.stdout)
