"""
Test Data Builder Pattern - Week 101

Fluent builders for creating test data with sensible defaults.
Makes tests more readable and maintainable.

Usage:
    # Create a user with defaults
    user = UserBuilder().build()

    # Customize specific fields
    admin = UserBuilder().with_email("admin@example.com").as_admin().build()

    # Create multiple with variations
    users = [
        UserBuilder().with_name(f"User {i}").build()
        for i in range(10)
    ]
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Generic, List, Optional, TypeVar
from abc import ABC, abstractmethod
import random
import string


T = TypeVar("T")


class Builder(ABC, Generic[T]):
    """
    Abstract base class for test data builders.

    Provides a fluent interface for building test objects
    with sensible defaults.
    """

    @abstractmethod
    def build(self) -> T:
        """Build and return the object."""
        pass

    @abstractmethod
    def reset(self) -> "Builder[T]":
        """Reset builder to default state."""
        pass


# =============================================================================
# User Builder
# =============================================================================


@dataclass
class UserData:
    """User test data structure."""
    id: int
    email: str
    name: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    metadata: Dict[str, Any] = field(default_factory=dict)


class UserBuilder(Builder[UserData]):
    """
    Builder for creating User test data.

    Usage:
        user = UserBuilder().build()  # Default user
        admin = UserBuilder().with_email("admin@test.com").as_admin().build()
    """

    _counter: int = 0

    def __init__(self):
        self.reset()

    def reset(self) -> "UserBuilder":
        UserBuilder._counter += 1
        self._id = UserBuilder._counter
        self._email = f"user{self._id}@example.com"
        self._name = f"Test User {self._id}"
        self._is_active = True
        self._is_admin = False
        self._created_at = datetime.utcnow()
        self._metadata: Dict[str, Any] = {}
        return self

    def with_id(self, id: int) -> "UserBuilder":
        self._id = id
        return self

    def with_email(self, email: str) -> "UserBuilder":
        self._email = email
        return self

    def with_name(self, name: str) -> "UserBuilder":
        self._name = name
        return self

    def as_active(self) -> "UserBuilder":
        self._is_active = True
        return self

    def as_inactive(self) -> "UserBuilder":
        self._is_active = False
        return self

    def as_admin(self) -> "UserBuilder":
        self._is_admin = True
        return self

    def with_created_at(self, created_at: datetime) -> "UserBuilder":
        self._created_at = created_at
        return self

    def created_days_ago(self, days: int) -> "UserBuilder":
        self._created_at = datetime.utcnow() - timedelta(days=days)
        return self

    def with_metadata(self, key: str, value: Any) -> "UserBuilder":
        self._metadata[key] = value
        return self

    def build(self) -> UserData:
        return UserData(
            id=self._id,
            email=self._email,
            name=self._name,
            is_active=self._is_active,
            is_admin=self._is_admin,
            created_at=self._created_at,
            metadata=self._metadata,
        )


# =============================================================================
# Project Builder
# =============================================================================


@dataclass
class ProjectData:
    """Project test data structure."""
    id: int
    name: str
    description: str
    owner_id: int
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    tech_stack: List[str] = field(default_factory=list)


class ProjectBuilder(Builder[ProjectData]):
    """
    Builder for creating Project test data.

    Usage:
        project = ProjectBuilder().build()
        python_project = ProjectBuilder().with_tech_stack(["Python", "FastAPI"]).build()
    """

    _counter: int = 0

    def __init__(self):
        self.reset()

    def reset(self) -> "ProjectBuilder":
        ProjectBuilder._counter += 1
        self._id = ProjectBuilder._counter
        self._name = f"Test Project {self._id}"
        self._description = f"Description for project {self._id}"
        self._owner_id = 1
        self._status = "active"
        self._created_at = datetime.utcnow()
        self._tech_stack: List[str] = []
        return self

    def with_id(self, id: int) -> "ProjectBuilder":
        self._id = id
        return self

    def with_name(self, name: str) -> "ProjectBuilder":
        self._name = name
        return self

    def with_description(self, description: str) -> "ProjectBuilder":
        self._description = description
        return self

    def with_owner(self, owner_id: int) -> "ProjectBuilder":
        self._owner_id = owner_id
        return self

    def with_status(self, status: str) -> "ProjectBuilder":
        self._status = status
        return self

    def as_active(self) -> "ProjectBuilder":
        return self.with_status("active")

    def as_archived(self) -> "ProjectBuilder":
        return self.with_status("archived")

    def as_draft(self) -> "ProjectBuilder":
        return self.with_status("draft")

    def with_tech_stack(self, stack: List[str]) -> "ProjectBuilder":
        self._tech_stack = stack
        return self

    def add_technology(self, tech: str) -> "ProjectBuilder":
        self._tech_stack.append(tech)
        return self

    def python_project(self) -> "ProjectBuilder":
        return self.with_tech_stack(["Python", "FastAPI", "PostgreSQL"])

    def typescript_project(self) -> "ProjectBuilder":
        return self.with_tech_stack(["TypeScript", "React", "Node.js"])

    def build(self) -> ProjectData:
        return ProjectData(
            id=self._id,
            name=self._name,
            description=self._description,
            owner_id=self._owner_id,
            status=self._status,
            created_at=self._created_at,
            tech_stack=self._tech_stack,
        )


# =============================================================================
# Task Builder
# =============================================================================


@dataclass
class TaskData:
    """Task test data structure."""
    id: int
    title: str
    description: str
    status: str = "todo"
    priority: str = "medium"
    assignee_id: Optional[int] = None
    project_id: Optional[int] = None
    story_points: Optional[int] = None
    due_date: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)


class TaskBuilder(Builder[TaskData]):
    """
    Builder for creating Task test data.

    Usage:
        task = TaskBuilder().build()
        urgent = TaskBuilder().with_title("Fix bug").as_high_priority().build()
    """

    _counter: int = 0

    def __init__(self):
        self.reset()

    def reset(self) -> "TaskBuilder":
        TaskBuilder._counter += 1
        self._id = TaskBuilder._counter
        self._title = f"Task {self._id}"
        self._description = f"Description for task {self._id}"
        self._status = "todo"
        self._priority = "medium"
        self._assignee_id: Optional[int] = None
        self._project_id: Optional[int] = None
        self._story_points: Optional[int] = None
        self._due_date: Optional[datetime] = None
        self._tags: List[str] = []
        return self

    def with_id(self, id: int) -> "TaskBuilder":
        self._id = id
        return self

    def with_title(self, title: str) -> "TaskBuilder":
        self._title = title
        return self

    def with_description(self, description: str) -> "TaskBuilder":
        self._description = description
        return self

    # Status helpers
    def as_todo(self) -> "TaskBuilder":
        self._status = "todo"
        return self

    def as_in_progress(self) -> "TaskBuilder":
        self._status = "in_progress"
        return self

    def as_done(self) -> "TaskBuilder":
        self._status = "done"
        return self

    def as_blocked(self) -> "TaskBuilder":
        self._status = "blocked"
        return self

    # Priority helpers
    def as_low_priority(self) -> "TaskBuilder":
        self._priority = "low"
        return self

    def as_medium_priority(self) -> "TaskBuilder":
        self._priority = "medium"
        return self

    def as_high_priority(self) -> "TaskBuilder":
        self._priority = "high"
        return self

    def as_critical(self) -> "TaskBuilder":
        self._priority = "critical"
        return self

    def assigned_to(self, user_id: int) -> "TaskBuilder":
        self._assignee_id = user_id
        return self

    def in_project(self, project_id: int) -> "TaskBuilder":
        self._project_id = project_id
        return self

    def with_story_points(self, points: int) -> "TaskBuilder":
        self._story_points = points
        return self

    def due_in_days(self, days: int) -> "TaskBuilder":
        self._due_date = datetime.utcnow() + timedelta(days=days)
        return self

    def overdue(self) -> "TaskBuilder":
        self._due_date = datetime.utcnow() - timedelta(days=1)
        return self

    def with_tags(self, tags: List[str]) -> "TaskBuilder":
        self._tags = tags
        return self

    def add_tag(self, tag: str) -> "TaskBuilder":
        self._tags.append(tag)
        return self

    def as_bug(self) -> "TaskBuilder":
        return self.add_tag("bug")

    def as_feature(self) -> "TaskBuilder":
        return self.add_tag("feature")

    def build(self) -> TaskData:
        return TaskData(
            id=self._id,
            title=self._title,
            description=self._description,
            status=self._status,
            priority=self._priority,
            assignee_id=self._assignee_id,
            project_id=self._project_id,
            story_points=self._story_points,
            due_date=self._due_date,
            tags=self._tags,
        )


# =============================================================================
# Utility Functions
# =============================================================================


def random_string(length: int = 10) -> str:
    """Generate a random string of specified length."""
    return "".join(random.choices(string.ascii_lowercase, k=length))


def random_email() -> str:
    """Generate a random email address."""
    return f"{random_string(8)}@example.com"


def random_uuid() -> str:
    """Generate a random UUID string."""
    return str(uuid.uuid4())


def build_many(builder: Builder[T], count: int) -> List[T]:
    """
    Build multiple instances using a builder.

    Each call resets and builds a new instance.

    Usage:
        users = build_many(UserBuilder(), 10)
    """
    return [builder.reset().build() for _ in range(count)]


# =============================================================================
# Factory Functions (Convenience)
# =============================================================================


def a_user() -> UserBuilder:
    """Create a UserBuilder with defaults."""
    return UserBuilder()


def a_project() -> ProjectBuilder:
    """Create a ProjectBuilder with defaults."""
    return ProjectBuilder()


def a_task() -> TaskBuilder:
    """Create a TaskBuilder with defaults."""
    return TaskBuilder()


# Example usage in tests:
#
# def test_user_creation():
#     user = a_user().with_email("test@test.com").as_admin().build()
#     assert user.email == "test@test.com"
#     assert user.is_admin
#
# def test_multiple_tasks():
#     tasks = build_many(a_task().as_high_priority(), 5)
#     assert len(tasks) == 5
#     assert all(t.priority == "high" for t in tasks)
