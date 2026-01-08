# Utils package
# Week 101: Foundation Utilities
# Week 144: Added datetime utilities for timezone-naive database operations

from .result import (
    Result,
    ValidationError,
    combine_results,
    try_result,
)
from .guard import (
    Guard,
    GuardError,
    ensure_not_none,
    ensure_not_empty,
    ensure_positive,
    ensure_in_range,
)
from .test_builders import (
    Builder,
    UserBuilder,
    UserData,
    ProjectBuilder,
    ProjectData,
    TaskBuilder,
    TaskData,
    a_user,
    a_project,
    a_task,
    build_many,
    random_string,
    random_email,
    random_uuid,
)
from .datetime_utils import (
    utc_now,
    ensure_naive,
)

__all__ = [
    # Result Pattern
    "Result",
    "ValidationError",
    "combine_results",
    "try_result",
    # Guard Clauses
    "Guard",
    "GuardError",
    "ensure_not_none",
    "ensure_not_empty",
    "ensure_positive",
    "ensure_in_range",
    # Test Builders
    "Builder",
    "UserBuilder",
    "UserData",
    "ProjectBuilder",
    "ProjectData",
    "TaskBuilder",
    "TaskData",
    "a_user",
    "a_project",
    "a_task",
    "build_many",
    "random_string",
    "random_email",
    "random_uuid",
    # Datetime Utilities
    "utc_now",
    "ensure_naive",
]
