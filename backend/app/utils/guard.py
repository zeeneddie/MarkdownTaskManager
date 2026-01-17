"""
Guard Clauses Library - Week 101

Defensive programming utilities for input validation.
Replaces nested if/else with early returns and clear error messages.

Usage:
    def create_user(name: str, email: str, age: int) -> Result[User]:
        Guard.against_empty(name, "name")
        Guard.against_empty(email, "email")
        Guard.against_out_of_range(age, 0, 150, "age")
        Guard.against_invalid_email(email, "email")

        # Main logic here - inputs are validated
        return Result.ok(User(name=name, email=email, age=age))
"""

import re
from datetime import datetime, timezone
from typing import Any, Collection, Optional, TypeVar, Union
from uuid import UUID

T = TypeVar("T")


class GuardError(ValueError):
    """Exception raised when a guard clause fails."""

    def __init__(self, message: str, parameter_name: str):
        self.parameter_name = parameter_name
        super().__init__(f"{parameter_name}: {message}")


class Guard:
    """
    Guard clause utilities for input validation.

    All methods raise GuardError if validation fails.
    Use these at the beginning of functions to validate inputs.
    """

    # =========================================================================
    # Null/Empty Checks
    # =========================================================================

    @staticmethod
    def against_null(value: Optional[T], parameter_name: str) -> T:
        """
        Guard against null/None values.

        Args:
            value: Value to check
            parameter_name: Name for error message

        Returns:
            The value if not None

        Raises:
            GuardError: If value is None
        """
        if value is None:
            raise GuardError("cannot be null", parameter_name)
        return value

    @staticmethod
    def against_empty(value: Optional[str], parameter_name: str) -> str:
        """
        Guard against empty or whitespace-only strings.

        Args:
            value: String to check
            parameter_name: Name for error message

        Returns:
            The value if not empty

        Raises:
            GuardError: If value is None, empty, or whitespace-only
        """
        if value is None or not value.strip():
            raise GuardError("cannot be empty or whitespace", parameter_name)
        return value

    @staticmethod
    def against_empty_collection(
        value: Optional[Collection[T]],
        parameter_name: str,
    ) -> Collection[T]:
        """
        Guard against empty collections (list, set, dict, etc.).

        Args:
            value: Collection to check
            parameter_name: Name for error message

        Returns:
            The collection if not empty

        Raises:
            GuardError: If collection is None or empty
        """
        if value is None or len(value) == 0:
            raise GuardError("cannot be empty", parameter_name)
        return value

    # =========================================================================
    # Numeric Checks
    # =========================================================================

    @staticmethod
    def against_negative(
        value: Union[int, float],
        parameter_name: str,
    ) -> Union[int, float]:
        """
        Guard against negative numbers.

        Args:
            value: Number to check
            parameter_name: Name for error message

        Returns:
            The value if not negative

        Raises:
            GuardError: If value is negative
        """
        if value < 0:
            raise GuardError(f"cannot be negative (got {value})", parameter_name)
        return value

    @staticmethod
    def against_zero(
        value: Union[int, float],
        parameter_name: str,
    ) -> Union[int, float]:
        """
        Guard against zero values.

        Args:
            value: Number to check
            parameter_name: Name for error message

        Returns:
            The value if not zero

        Raises:
            GuardError: If value is zero
        """
        if value == 0:
            raise GuardError("cannot be zero", parameter_name)
        return value

    @staticmethod
    def against_negative_or_zero(
        value: Union[int, float],
        parameter_name: str,
    ) -> Union[int, float]:
        """
        Guard against non-positive numbers.

        Args:
            value: Number to check
            parameter_name: Name for error message

        Returns:
            The value if positive

        Raises:
            GuardError: If value is zero or negative
        """
        if value <= 0:
            raise GuardError(
                f"must be positive (got {value})",
                parameter_name,
            )
        return value

    @staticmethod
    def against_out_of_range(
        value: Union[int, float],
        min_value: Union[int, float],
        max_value: Union[int, float],
        parameter_name: str,
    ) -> Union[int, float]:
        """
        Guard against values outside a range.

        Args:
            value: Number to check
            min_value: Minimum allowed value (inclusive)
            max_value: Maximum allowed value (inclusive)
            parameter_name: Name for error message

        Returns:
            The value if within range

        Raises:
            GuardError: If value is outside the range
        """
        if value < min_value or value > max_value:
            raise GuardError(
                f"must be between {min_value} and {max_value} (got {value})",
                parameter_name,
            )
        return value

    # =========================================================================
    # String Checks
    # =========================================================================

    @staticmethod
    def against_too_short(
        value: str,
        min_length: int,
        parameter_name: str,
    ) -> str:
        """
        Guard against strings that are too short.

        Args:
            value: String to check
            min_length: Minimum required length
            parameter_name: Name for error message

        Returns:
            The value if long enough

        Raises:
            GuardError: If string is too short
        """
        if len(value) < min_length:
            raise GuardError(
                f"must be at least {min_length} characters (got {len(value)})",
                parameter_name,
            )
        return value

    @staticmethod
    def against_too_long(
        value: str,
        max_length: int,
        parameter_name: str,
    ) -> str:
        """
        Guard against strings that are too long.

        Args:
            value: String to check
            max_length: Maximum allowed length
            parameter_name: Name for error message

        Returns:
            The value if short enough

        Raises:
            GuardError: If string is too long
        """
        if len(value) > max_length:
            raise GuardError(
                f"cannot exceed {max_length} characters (got {len(value)})",
                parameter_name,
            )
        return value

    @staticmethod
    def against_invalid_format(
        value: str,
        pattern: str,
        parameter_name: str,
        format_description: str = "expected format",
    ) -> str:
        """
        Guard against strings that don't match a regex pattern.

        Args:
            value: String to check
            pattern: Regex pattern to match
            parameter_name: Name for error message
            format_description: Human-readable format description

        Returns:
            The value if it matches

        Raises:
            GuardError: If string doesn't match pattern
        """
        if not re.match(pattern, value):
            raise GuardError(
                f"does not match {format_description}",
                parameter_name,
            )
        return value

    @staticmethod
    def against_invalid_email(value: str, parameter_name: str) -> str:
        """
        Guard against invalid email addresses.

        Args:
            value: Email to validate
            parameter_name: Name for error message

        Returns:
            The value if valid email

        Raises:
            GuardError: If not a valid email format
        """
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, value):
            raise GuardError("is not a valid email address", parameter_name)
        return value

    @staticmethod
    def against_invalid_url(value: str, parameter_name: str) -> str:
        """
        Guard against invalid URLs.

        Args:
            value: URL to validate
            parameter_name: Name for error message

        Returns:
            The value if valid URL

        Raises:
            GuardError: If not a valid URL format
        """
        url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        if not re.match(url_pattern, value):
            raise GuardError("is not a valid URL", parameter_name)
        return value

    # =========================================================================
    # Type Checks
    # =========================================================================

    @staticmethod
    def against_invalid_type(
        value: Any,
        expected_type: type,
        parameter_name: str,
    ) -> Any:
        """
        Guard against incorrect types.

        Args:
            value: Value to check
            expected_type: Expected type
            parameter_name: Name for error message

        Returns:
            The value if correct type

        Raises:
            GuardError: If value is not the expected type
        """
        if not isinstance(value, expected_type):
            raise GuardError(
                f"must be {expected_type.__name__} (got {type(value).__name__})",
                parameter_name,
            )
        return value

    @staticmethod
    def against_invalid_uuid(value: str, parameter_name: str) -> str:
        """
        Guard against invalid UUID strings.

        Args:
            value: UUID string to validate
            parameter_name: Name for error message

        Returns:
            The value if valid UUID

        Raises:
            GuardError: If not a valid UUID format
        """
        try:
            UUID(value)
            return value
        except (ValueError, AttributeError):
            raise GuardError("is not a valid UUID", parameter_name)

    # =========================================================================
    # Date/Time Checks
    # =========================================================================

    @staticmethod
    def against_past_date(
        value: datetime,
        parameter_name: str,
        reference: Optional[datetime] = None,
    ) -> datetime:
        """
        Guard against dates in the past.

        Args:
            value: Date to check
            parameter_name: Name for error message
            reference: Reference date (default: now)

        Returns:
            The value if not in the past

        Raises:
            GuardError: If date is in the past
        """
        ref = reference or datetime.now(timezone.utc)
        if value < ref:
            raise GuardError("cannot be in the past", parameter_name)
        return value

    @staticmethod
    def against_future_date(
        value: datetime,
        parameter_name: str,
        reference: Optional[datetime] = None,
    ) -> datetime:
        """
        Guard against dates in the future.

        Args:
            value: Date to check
            parameter_name: Name for error message
            reference: Reference date (default: now)

        Returns:
            The value if not in the future

        Raises:
            GuardError: If date is in the future
        """
        ref = reference or datetime.now(timezone.utc)
        if value > ref:
            raise GuardError("cannot be in the future", parameter_name)
        return value

    # =========================================================================
    # Collection Checks
    # =========================================================================

    @staticmethod
    def against_not_in_set(
        value: T,
        allowed_values: Collection[T],
        parameter_name: str,
    ) -> T:
        """
        Guard against values not in an allowed set.

        Args:
            value: Value to check
            allowed_values: Set of allowed values
            parameter_name: Name for error message

        Returns:
            The value if in the allowed set

        Raises:
            GuardError: If value is not in allowed values
        """
        if value not in allowed_values:
            raise GuardError(
                f"must be one of: {', '.join(str(v) for v in allowed_values)}",
                parameter_name,
            )
        return value

    @staticmethod
    def against_duplicates(
        collection: Collection[T],
        parameter_name: str,
    ) -> Collection[T]:
        """
        Guard against collections with duplicate values.

        Args:
            collection: Collection to check
            parameter_name: Name for error message

        Returns:
            The collection if no duplicates

        Raises:
            GuardError: If collection has duplicates
        """
        seen = set()
        duplicates = []
        for item in collection:
            if item in seen:
                duplicates.append(item)
            seen.add(item)

        if duplicates:
            raise GuardError(
                f"contains duplicates: {duplicates}",
                parameter_name,
            )
        return collection


# Convenience functions for common guard patterns
def ensure_not_none(value: Optional[T], name: str) -> T:
    """Alias for Guard.against_null."""
    return Guard.against_null(value, name)


def ensure_not_empty(value: Optional[str], name: str) -> str:
    """Alias for Guard.against_empty."""
    return Guard.against_empty(value, name)


def ensure_positive(value: Union[int, float], name: str) -> Union[int, float]:
    """Alias for Guard.against_negative_or_zero."""
    return Guard.against_negative_or_zero(value, name)


def ensure_in_range(
    value: Union[int, float],
    min_val: Union[int, float],
    max_val: Union[int, float],
    name: str,
) -> Union[int, float]:
    """Alias for Guard.against_out_of_range."""
    return Guard.against_out_of_range(value, min_val, max_val, name)
