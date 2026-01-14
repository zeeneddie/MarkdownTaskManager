"""
Task Hierarchy Validation Service

Enforces business rules and constraints on the task hierarchy:
- Count limits per hierarchy level
- Status transition validation
- Consistency rules
- Data integrity checks
"""
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.task_hierarchy import Epic, Feature, Story, Task
from app.models.green_paper import Specification


class ValidationError(Exception):
    """Raised when validation rules are violated."""
    pass


class HierarchyValidationService:
    """
    Validates task hierarchy operations and enforces business rules.
    """

    # Count limits for each hierarchy level
    MAX_EPICS_PER_SPECIFICATION = 10
    MAX_FEATURES_PER_EPIC = 15
    MAX_STORIES_PER_FEATURE = 10
    MAX_TASKS_PER_STORY = 8

    # Valid status transitions
    VALID_EPIC_TRANSITIONS = {
        "draft": ["planned", "cancelled"],
        "planned": ["in_progress", "on_hold", "cancelled"],
        "in_progress": ["completed", "on_hold", "cancelled"],
        "completed": [],  # Final state
        "on_hold": ["planned", "in_progress", "cancelled"],
        "cancelled": []  # Final state
    }

    VALID_FEATURE_TRANSITIONS = {
        "draft": ["planned", "cancelled"],
        "planned": ["in_progress", "on_hold", "cancelled"],
        "in_progress": ["review", "on_hold", "cancelled"],
        "review": ["completed", "in_progress", "cancelled"],
        "completed": [],
        "on_hold": ["planned", "in_progress", "cancelled"],
        "cancelled": []
    }

    VALID_STORY_TRANSITIONS = {
        "backlog": ["ready", "cancelled"],
        "ready": ["in_progress", "backlog", "cancelled"],
        "in_progress": ["review", "blocked", "cancelled"],
        "review": ["done", "in_progress", "cancelled"],
        "done": [],
        "blocked": ["in_progress", "cancelled"],
        "cancelled": []
    }

    VALID_TASK_TRANSITIONS = {
        "todo": ["in_progress", "cancelled"],
        "in_progress": ["review", "blocked", "cancelled"],
        "review": ["done", "in_progress", "cancelled"],
        "done": [],
        "blocked": ["todo", "in_progress", "cancelled"],
        "cancelled": []
    }

    # Valid Fibonacci story points
    VALID_STORY_POINTS = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

    # Valid priority levels
    VALID_PRIORITIES = ["critical", "high", "medium", "low"]

    # Valid complexity levels
    VALID_COMPLEXITIES = ["simple", "moderate", "complex"]

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_epic_creation(
        self,
        specification_id: str,
        num_epics_to_create: int = 1
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that creating epics won't exceed limits.

        Args:
            specification_id: The specification ID
            num_epics_to_create: Number of epics to create

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check specification exists and is approved
        result = await self.db.execute(
            select(Specification).where(Specification.id == specification_id)
        )
        spec = result.scalar_one_or_none()

        if not spec:
            return False, f"Specification {specification_id} not found"

        if spec.status != "approved":
            return False, f"Specification must be approved (current status: {spec.status})"

        # Check current epic count
        result = await self.db.execute(
            select(func.count(Epic.id)).where(Epic.specification_id == specification_id)
        )
        current_count = result.scalar()

        if current_count + num_epics_to_create > self.MAX_EPICS_PER_SPECIFICATION:
            return False, (
                f"Cannot create {num_epics_to_create} epics. "
                f"Current: {current_count}, Max: {self.MAX_EPICS_PER_SPECIFICATION}"
            )

        return True, None

    async def validate_feature_creation(
        self,
        epic_id: str,
        num_features_to_create: int = 1
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that creating features won't exceed limits.

        Args:
            epic_id: The epic ID
            num_features_to_create: Number of features to create

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check epic exists
        result = await self.db.execute(
            select(Epic).where(Epic.id == epic_id)
        )
        epic = result.scalar_one_or_none()

        if not epic:
            return False, f"Epic {epic_id} not found"

        # Check epic status allows feature creation
        if epic.status in ["completed", "cancelled"]:
            return False, f"Cannot create features for {epic.status} epic"

        # Check current feature count
        result = await self.db.execute(
            select(func.count(Feature.id)).where(Feature.epic_id == epic_id)
        )
        current_count = result.scalar()

        if current_count + num_features_to_create > self.MAX_FEATURES_PER_EPIC:
            return False, (
                f"Cannot create {num_features_to_create} features. "
                f"Current: {current_count}, Max: {self.MAX_FEATURES_PER_EPIC}"
            )

        return True, None

    async def validate_story_creation(
        self,
        feature_id: str,
        num_stories_to_create: int = 1
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that creating stories won't exceed limits.

        Args:
            feature_id: The feature ID
            num_stories_to_create: Number of stories to create

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check feature exists
        result = await self.db.execute(
            select(Feature).where(Feature.id == feature_id)
        )
        feature = result.scalar_one_or_none()

        if not feature:
            return False, f"Feature {feature_id} not found"

        # Check feature status allows story creation
        if feature.status in ["completed", "cancelled"]:
            return False, f"Cannot create stories for {feature.status} feature"

        # Check current story count
        result = await self.db.execute(
            select(func.count(Story.id)).where(Story.feature_id == feature_id)
        )
        current_count = result.scalar()

        if current_count + num_stories_to_create > self.MAX_STORIES_PER_FEATURE:
            return False, (
                f"Cannot create {num_stories_to_create} stories. "
                f"Current: {current_count}, Max: {self.MAX_STORIES_PER_FEATURE}"
            )

        return True, None

    async def validate_task_creation(
        self,
        story_id: str,
        num_tasks_to_create: int = 1
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that creating tasks won't exceed limits.

        Args:
            story_id: The story ID
            num_tasks_to_create: Number of tasks to create

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check story exists
        result = await self.db.execute(
            select(Story).where(Story.id == story_id)
        )
        story = result.scalar_one_or_none()

        if not story:
            return False, f"Story {story_id} not found"

        # Check story status allows task creation
        if story.status in ["done", "cancelled"]:
            return False, f"Cannot create tasks for {story.status} story"

        # Check current task count
        result = await self.db.execute(
            select(func.count(Task.id)).where(Task.story_id == story_id)
        )
        current_count = result.scalar()

        if current_count + num_tasks_to_create > self.MAX_TASKS_PER_STORY:
            return False, (
                f"Cannot create {num_tasks_to_create} tasks. "
                f"Current: {current_count}, Max: {self.MAX_TASKS_PER_STORY}"
            )

        return True, None

    def validate_status_transition(
        self,
        entity_type: str,
        current_status: str,
        new_status: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a status transition is allowed.

        Args:
            entity_type: Type of entity (epic, feature, story, task)
            current_status: Current status
            new_status: Desired new status

        Returns:
            Tuple of (is_valid, error_message)
        """
        transitions = {
            "epic": self.VALID_EPIC_TRANSITIONS,
            "feature": self.VALID_FEATURE_TRANSITIONS,
            "story": self.VALID_STORY_TRANSITIONS,
            "task": self.VALID_TASK_TRANSITIONS
        }

        if entity_type not in transitions:
            return False, f"Unknown entity type: {entity_type}"

        valid_transitions = transitions[entity_type]

        if current_status not in valid_transitions:
            return False, f"Invalid current status: {current_status}"

        if new_status not in valid_transitions.get(current_status, []):
            return False, (
                f"Cannot transition from '{current_status}' to '{new_status}' "
                f"for {entity_type}. Valid transitions: {valid_transitions[current_status]}"
            )

        return True, None

    def validate_story_points(self, story_points: int) -> Tuple[bool, Optional[str]]:
        """
        Validate story points follow Fibonacci sequence.

        Args:
            story_points: Story point value

        Returns:
            Tuple of (is_valid, error_message)
        """
        if story_points not in self.VALID_STORY_POINTS:
            return False, (
                f"Story points must be Fibonacci numbers: {self.VALID_STORY_POINTS}. "
                f"Got: {story_points}"
            )

        return True, None

    def validate_priority(self, priority: str) -> Tuple[bool, Optional[str]]:
        """
        Validate priority level.

        Args:
            priority: Priority value

        Returns:
            Tuple of (is_valid, error_message)
        """
        if priority not in self.VALID_PRIORITIES:
            return False, (
                f"Priority must be one of: {self.VALID_PRIORITIES}. "
                f"Got: {priority}"
            )

        return True, None

    def validate_complexity(self, complexity: str) -> Tuple[bool, Optional[str]]:
        """
        Validate complexity level.

        Args:
            complexity: Complexity value

        Returns:
            Tuple of (is_valid, error_message)
        """
        if complexity not in self.VALID_COMPLEXITIES:
            return False, (
                f"Complexity must be one of: {self.VALID_COMPLEXITIES}. "
                f"Got: {complexity}"
            )

        return True, None

    async def validate_epic_data(self, epic_data: Dict) -> List[str]:
        """
        Validate epic data structure and values.

        Args:
            epic_data: Dictionary containing epic data

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Required fields
        required = ["title", "description"]
        for field in required:
            if not epic_data.get(field):
                errors.append(f"Missing required field: {field}")

        # Title length
        if len(epic_data.get("title", "")) > 200:
            errors.append("Title must be 200 characters or less")

        # Priority validation
        if "priority" in epic_data:
            is_valid, error = self.validate_priority(epic_data["priority"])
            if not is_valid:
                errors.append(error)

        # Story points validation
        if "estimated_story_points" in epic_data:
            if epic_data["estimated_story_points"] < 0:
                errors.append("Estimated story points must be non-negative")

        # Weeks validation
        if "estimated_weeks" in epic_data:
            if epic_data["estimated_weeks"] < 0:
                errors.append("Estimated weeks must be non-negative")

        return errors

    async def validate_feature_data(self, feature_data: Dict) -> List[str]:
        """
        Validate feature data structure and values.

        Args:
            feature_data: Dictionary containing feature data

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Required fields
        required = ["title", "description"]
        for field in required:
            if not feature_data.get(field):
                errors.append(f"Missing required field: {field}")

        # Title length
        if len(feature_data.get("title", "")) > 200:
            errors.append("Title must be 200 characters or less")

        # Priority validation
        if "priority" in feature_data:
            is_valid, error = self.validate_priority(feature_data["priority"])
            if not is_valid:
                errors.append(error)

        # Complexity validation
        if "complexity" in feature_data:
            is_valid, error = self.validate_complexity(feature_data["complexity"])
            if not is_valid:
                errors.append(error)

        # Story points validation
        if "estimated_story_points" in feature_data:
            if feature_data["estimated_story_points"] < 0:
                errors.append("Estimated story points must be non-negative")

        return errors

    async def validate_story_data(self, story_data: Dict) -> List[str]:
        """
        Validate story data structure and values.

        Args:
            story_data: Dictionary containing story data

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Required fields
        required = ["title", "description"]
        for field in required:
            if not story_data.get(field):
                errors.append(f"Missing required field: {field}")

        # Title length
        if len(story_data.get("title", "")) > 500:
            errors.append("Title must be 500 characters or less")

        # Priority validation
        if "priority" in story_data:
            is_valid, error = self.validate_priority(story_data["priority"])
            if not is_valid:
                errors.append(error)

        # Story points validation (Fibonacci)
        if "story_points" in story_data:
            is_valid, error = self.validate_story_points(story_data["story_points"])
            if not is_valid:
                errors.append(error)

        # User story format validation (optional but recommended)
        if "title" in story_data:
            title = story_data["title"]
            if not any(phrase in title.lower() for phrase in ["as a", "i want", "so that"]):
                # This is a warning, not an error
                pass

        return errors

    async def validate_task_data(self, task_data: Dict) -> List[str]:
        """
        Validate task data structure and values.

        Args:
            task_data: Dictionary containing task data

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Required fields
        required = ["title", "description"]
        for field in required:
            if not task_data.get(field):
                errors.append(f"Missing required field: {field}")

        # Title length
        if len(task_data.get("title", "")) > 200:
            errors.append("Title must be 200 characters or less")

        # Priority validation
        if "priority" in task_data:
            is_valid, error = self.validate_priority(task_data["priority"])
            if not is_valid:
                errors.append(error)

        # Task type validation
        valid_task_types = ["backend", "frontend", "database", "testing", "devops", "documentation"]
        if "task_type" in task_data and task_data["task_type"] not in valid_task_types:
            errors.append(f"Task type must be one of: {valid_task_types}")

        # Estimated hours validation
        if "estimated_hours" in task_data:
            if task_data["estimated_hours"] < 0:
                errors.append("Estimated hours must be non-negative")
            if task_data["estimated_hours"] > 80:
                errors.append("Estimated hours should not exceed 80 (2 weeks)")

        return errors

    async def get_hierarchy_summary(self, specification_id: str) -> Dict:
        """
        Get a summary of the task hierarchy for a specification.

        Args:
            specification_id: The specification ID

        Returns:
            Dictionary with counts and statistics
        """
        # Count epics
        result = await self.db.execute(
            select(func.count(Epic.id)).where(Epic.specification_id == specification_id)
        )
        epic_count = result.scalar()

        # Count features
        result = await self.db.execute(
            select(func.count(Feature.id))
            .join(Epic)
            .where(Epic.specification_id == specification_id)
        )
        feature_count = result.scalar()

        # Count stories
        result = await self.db.execute(
            select(func.count(Story.id))
            .join(Feature)
            .join(Epic)
            .where(Epic.specification_id == specification_id)
        )
        story_count = result.scalar()

        # Count tasks
        result = await self.db.execute(
            select(func.count(Task.id))
            .join(Story)
            .join(Feature)
            .join(Epic)
            .where(Epic.specification_id == specification_id)
        )
        task_count = result.scalar()

        # Calculate total story points
        result = await self.db.execute(
            select(func.sum(Story.story_points))
            .join(Feature)
            .join(Epic)
            .where(Epic.specification_id == specification_id)
        )
        total_story_points = result.scalar() or 0

        return {
            "specification_id": str(specification_id),
            "counts": {
                "epics": epic_count,
                "features": feature_count,
                "stories": story_count,
                "tasks": task_count
            },
            "limits": {
                "max_epics": self.MAX_EPICS_PER_SPECIFICATION,
                "max_features_per_epic": self.MAX_FEATURES_PER_EPIC,
                "max_stories_per_feature": self.MAX_STORIES_PER_FEATURE,
                "max_tasks_per_story": self.MAX_TASKS_PER_STORY
            },
            "remaining_capacity": {
                "epics": self.MAX_EPICS_PER_SPECIFICATION - epic_count
            },
            "statistics": {
                "total_story_points": int(total_story_points),
                "avg_features_per_epic": round(feature_count / epic_count, 2) if epic_count > 0 else 0,
                "avg_stories_per_feature": round(story_count / feature_count, 2) if feature_count > 0 else 0,
                "avg_tasks_per_story": round(task_count / story_count, 2) if story_count > 0 else 0
            }
        }


def get_validation_service(db: AsyncSession) -> HierarchyValidationService:
    """
    Factory function to get validation service instance.

    Args:
        db: Database session

    Returns:
        HierarchyValidationService instance
    """
    return HierarchyValidationService(db)
