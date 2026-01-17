"""
MultiFileProjectParser - Parse nested markdown structure into Python objects
"""

from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
import re
import yaml
import logging

logger = logging.getLogger(__name__)


class MultiFileProjectParser:
    """Parse project from nested markdown file structure"""

    def __init__(self, project_root: Path, project_name: str = "MarkdownTaskManager"):
        self.project_root = Path(project_root)
        self.project_name = project_name
        self.epics_dir = self.project_root / "Projecten" / project_name

    def parse_project(self) -> Dict:
        """
        Parse entire project structure.

        Returns:
            Dict with epics, features, stories, tasks
        """
        logger.info(f"Parsing project from {self.project_root}")

        project = {
            "epics": [],
            "features": [],
            "stories": [],
            "tasks": [],
            "parse_time": datetime.now(timezone.utc)
        }

        # Parse all epics
        if not self.epics_dir.exists():
            logger.warning(f"Epics directory not found: {self.epics_dir}")
            return project

        for epic_dir in self.epics_dir.iterdir():
            if epic_dir.is_dir() and epic_dir.name.startswith("EPIC-"):
                try:
                    epic_data = self.parse_epic(epic_dir)
                    if epic_data:
                        project["epics"].append(epic_data)

                        # Collect nested features, stories, tasks
                        for feature in epic_data.get("features", []):
                            project["features"].append(feature)
                            for story in feature.get("stories", []):
                                project["stories"].append(story)
                                for task in story.get("tasks", []):
                                    project["tasks"].append(task)
                except Exception as e:
                    logger.error(f"Error parsing epic {epic_dir.name}: {str(e)}")
                    continue

        logger.info(
            f"Parsed {len(project['epics'])} epics, "
            f"{len(project['features'])} features, "
            f"{len(project['stories'])} stories, "
            f"{len(project['tasks'])} tasks"
        )

        return project

    def parse_epic(self, epic_dir: Path) -> Optional[Dict]:
        """
        Parse single epic from its directory.

        Args:
            epic_dir: Path to epic directory (e.g., epics/EPIC-001)

        Returns:
            Dict with epic data including nested features
        """
        epic_file = epic_dir / "epic.md"

        if not epic_file.exists():
            logger.warning(f"Epic file not found: {epic_file}")
            return None

        logger.debug(f"Parsing epic: {epic_file}")

        # Read file content
        with open(epic_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract frontmatter
        metadata = self._extract_frontmatter(content)

        if not metadata:
            logger.warning(f"No frontmatter in {epic_file}")
            return None

        # Extract body content
        body = self._extract_body(content)

        # Parse body sections
        sections = self._parse_sections(body)

        epic_data = {
            **metadata,
            "description": sections.get("summary", ""),
            "business_value": sections.get("business_value", ""),
            "features": [],
            "file_path": str(epic_file)
        }

        # Parse nested features (directly under epic, no 'features' folder)
        for feature_dir in epic_dir.iterdir():
            if feature_dir.is_dir() and feature_dir.name.startswith("FEATURE-"):
                try:
                    feature_data = self.parse_feature(feature_dir, epic_data["id"])
                    if feature_data:
                        epic_data["features"].append(feature_data)
                except Exception as e:
                    logger.error(f"Error parsing feature {feature_dir.name}: {str(e)}")
                    continue

        return epic_data

    def parse_feature(self, feature_dir: Path, parent_epic_id: str) -> Optional[Dict]:
        """
        Parse single feature from its directory.

        Args:
            feature_dir: Path to feature directory
            parent_epic_id: ID of parent epic

        Returns:
            Dict with feature data including nested stories
        """
        feature_file = feature_dir / "feature.md"

        if not feature_file.exists():
            logger.warning(f"Feature file not found: {feature_file}")
            return None

        logger.debug(f"Parsing feature: {feature_file}")

        with open(feature_file, 'r', encoding='utf-8') as f:
            content = f.read()

        metadata = self._extract_frontmatter(content)

        if not metadata:
            return None

        body = self._extract_body(content)
        sections = self._parse_sections(body)

        feature_data = {
            **metadata,
            "parent_id": parent_epic_id,
            "description": sections.get("description", ""),
            "stories": [],
            "file_path": str(feature_file)
        }

        # Parse nested stories (directly under feature, no 'stories' folder)
        for story_dir in feature_dir.iterdir():
            if story_dir.is_dir() and story_dir.name.startswith("STORY-"):
                try:
                    story_data = self.parse_story(story_dir, feature_data["id"])
                    if story_data:
                        feature_data["stories"].append(story_data)
                except Exception as e:
                    logger.error(f"Error parsing story {story_dir.name}: {str(e)}")
                    continue

        return feature_data

    def parse_story(self, story_dir: Path, parent_feature_id: str) -> Optional[Dict]:
        """
        Parse single story from its directory.

        Args:
            story_dir: Path to story directory
            parent_feature_id: ID of parent feature

        Returns:
            Dict with story data including nested tasks
        """
        story_file = story_dir / "story.md"

        if not story_file.exists():
            logger.warning(f"Story file not found: {story_file}")
            return None

        logger.debug(f"Parsing story: {story_file}")

        with open(story_file, 'r', encoding='utf-8') as f:
            content = f.read()

        metadata = self._extract_frontmatter(content)

        if not metadata:
            return None

        body = self._extract_body(content)
        sections = self._parse_sections(body)

        # Extract user story parts
        user_story_text = sections.get("user_story", "")
        user_story_parts = self._parse_user_story(user_story_text)

        # Extract acceptance criteria
        acceptance_criteria = self._extract_checklist_items(
            sections.get("acceptance_criteria", "")
        )

        story_data = {
            **metadata,
            "parent_id": parent_feature_id,
            "description": user_story_text,
            "user_story_as": user_story_parts.get("as"),
            "user_story_want": user_story_parts.get("want"),
            "user_story_so_that": user_story_parts.get("so_that"),
            "acceptance_criteria": acceptance_criteria,
            "tasks": [],
            "file_path": str(story_file)
        }

        # Parse nested tasks (directly under story, no 'tasks' folder)
        for task_file in story_dir.glob("TASK-*.md"):
            try:
                task_data = self.parse_task(task_file, story_data["id"])
                if task_data:
                    story_data["tasks"].append(task_data)
            except Exception as e:
                logger.error(f"Error parsing task {task_file.name}: {str(e)}")
                continue

        return story_data

    def parse_task(self, task_file: Path, parent_story_id: str) -> Optional[Dict]:
        """
        Parse single task from its file.

        Args:
            task_file: Path to task file
            parent_story_id: ID of parent story

        Returns:
            Dict with task data
        """
        logger.debug(f"Parsing task: {task_file}")

        with open(task_file, 'r', encoding='utf-8') as f:
            content = f.read()

        metadata = self._extract_frontmatter(content)

        if not metadata:
            return None

        body = self._extract_body(content)
        sections = self._parse_sections(body)

        # Extract checklist
        checklist = self._extract_checklist_items(sections.get("checklist", ""))

        task_data = {
            **metadata,
            "parent_id": parent_story_id,
            "description": sections.get("description", ""),
            "checklist": checklist,
            "file_path": str(task_file)
        }

        return task_data

    def _extract_frontmatter(self, content: str) -> Optional[Dict]:
        """
        Extract YAML frontmatter from markdown.

        Args:
            content: Markdown content

        Returns:
            Dict with frontmatter data, or None if not found
        """
        # Match: ---\n...\n---
        pattern = r'^---\n(.*?)\n---'
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return None

        yaml_content = match.group(1)

        try:
            metadata = yaml.safe_load(yaml_content)
            return metadata
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {str(e)}")
            return None

    def _extract_body(self, content: str) -> str:
        """
        Extract markdown body (content after frontmatter).

        Args:
            content: Full markdown content

        Returns:
            Body content (without frontmatter)
        """
        # Remove frontmatter
        pattern = r'^---\n.*?\n---\n'
        body = re.sub(pattern, '', content, count=1, flags=re.DOTALL)

        return body.strip()

    def _parse_sections(self, body: str) -> Dict[str, str]:
        """
        Parse markdown body into sections based on ## headings.

        Args:
            body: Markdown body content

        Returns:
            Dict with section name -> content
        """
        sections = {}

        # Split by ## headings
        # Pattern: ## 📊 Summary\n\nContent here\n\n## 🎯 Next Section
        parts = re.split(r'\n## ', body)

        for part in parts:
            if not part.strip():
                continue

            # First line is section title, rest is content
            lines = part.split('\n', 1)
            if len(lines) == 2:
                title = lines[0].strip()
                content = lines[1].strip()

                # Normalize section name (remove emoji, lowercase, use underscore)
                # "📊 Summary" -> "summary"
                section_name = re.sub(r'[^\w\s]', '', title).strip().lower().replace(' ', '_')

                sections[section_name] = content

        return sections

    def _parse_user_story(self, user_story_text: str) -> Dict[str, str]:
        """
        Parse user story in "As a...I want...So that..." format.

        Args:
            user_story_text: User story section content

        Returns:
            Dict with 'as', 'want', 'so_that' keys
        """
        parts = {}

        # Extract "As a ..." part
        as_match = re.search(r'\*\*As a\*\*\s+(.+)', user_story_text, re.IGNORECASE)
        if as_match:
            parts['as'] = as_match.group(1).strip()

        # Extract "I want to ..." part
        want_match = re.search(r'\*\*I want to\*\*\s+(.+)', user_story_text, re.IGNORECASE)
        if want_match:
            parts['want'] = want_match.group(1).strip()

        # Extract "So that ..." part
        so_that_match = re.search(r'\*\*So that\*\*\s+(.+)', user_story_text, re.IGNORECASE)
        if so_that_match:
            parts['so_that'] = so_that_match.group(1).strip()

        return parts

    def _extract_checklist_items(self, text: str) -> List[Dict[str, any]]:
        """
        Extract checklist items from markdown.

        Args:
            text: Section content with checklist

        Returns:
            List of dicts with 'text' and 'checked' keys
        """
        items = []

        # Pattern: - [ ] Item text  or  - [x] Item text
        pattern = r'- \[([ x])\] (.+)'

        for match in re.finditer(pattern, text):
            checked = match.group(1).lower() == 'x'
            item_text = match.group(2).strip()

            items.append({
                "text": item_text,
                "checked": checked
            })

        return items


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    parser = MultiFileProjectParser(Path("/home/eddie/Projects/MarkdownTaskManager"))
    project = parser.parse_project()

    print(f"\n{'='*60}")
    print(f"Parsed Project Structure")
    print(f"{'='*60}")
    print(f"Epics: {len(project['epics'])}")
    print(f"Features: {len(project['features'])}")
    print(f"Stories: {len(project['stories'])}")
    print(f"Tasks: {len(project['tasks'])}")

    if project['epics']:
        epic = project['epics'][0]
        print(f"\n{'='*60}")
        print(f"Epic: {epic['id']} - {epic['title']}")
        print(f"{'='*60}")
        print(f"Status: {epic.get('status')}")
        print(f"Priority: {epic.get('priority')}")
        print(f"SP Total: {epic.get('sp_total')}")
        print(f"Features: {len(epic.get('features', []))}")

        if epic.get('features'):
            feature = epic['features'][0]
            print(f"\n  Feature: {feature['id']} - {feature['title']}")
            print(f"  Stories: {len(feature.get('stories', []))}")

            if feature.get('stories'):
                story = feature['stories'][0]
                print(f"\n    Story: {story['id']} - {story['title']}")
                print(f"    SP: {story.get('sp')}")
                print(f"    Tasks: {len(story.get('tasks', []))}")

                if story.get('tasks'):
                    task = story['tasks'][0]
                    print(f"\n      Task: {task['id']} - {task['title']}")
                    print(f"      Status: {task.get('status')}")
