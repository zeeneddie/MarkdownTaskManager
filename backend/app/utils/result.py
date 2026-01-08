"""
Result Pattern - Week 101

Type-safe error handling pattern that eliminates exception-based flow control.
Based on Rust's Result type and functional programming patterns.

Usage:
    def get_user(user_id: int) -> Result[User]:
        if not user_id:
            return Result.fail("Invalid user ID")

        user = db.find(user_id)
        if not user:
            return Result.fail("User not found", "USER_NOT_FOUND")

        return Result.ok(user)

    # Using the result
    result = get_user(123)
    if result.is_success:
        user = result.value
        print(f"Found user: {user.name}")
    else:
        print(f"Error: {result.error}")

    # Chaining with map
    result = get_user(123).map(lambda u: u.name)

    # Unwrap with default
    name = get_user(123).unwrap_or("Unknown")
"""

from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Generic,
    List,
    Optional,
    TypeVar,
    Union,
)

T = TypeVar("T")
U = TypeVar("U")


@dataclass
class ValidationError:
    """Represents a single validation error."""

    field: str
    message: str
    code: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        result = {"field": self.field, "message": self.message}
        if self.code:
            result["code"] = self.code
        return result


@dataclass
class Result(Generic[T]):
    """
    Result type for explicit success/failure handling.

    Provides a type-safe alternative to exceptions for expected failure cases.
    Forces explicit handling of both success and failure paths.

    Attributes:
        success: Whether the operation succeeded
        value: The success value (if success=True)
        error: The error message (if success=False)
        error_code: Optional error code for categorization
        validation_errors: List of field-level validation errors
    """

    success: bool
    value: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    validation_errors: List[ValidationError] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        """Check if result is successful."""
        return self.success

    @property
    def is_failure(self) -> bool:
        """Check if result is a failure."""
        return not self.success

    @classmethod
    def ok(cls, value: T) -> "Result[T]":
        """
        Create a successful result.

        Args:
            value: The success value

        Returns:
            Result with success=True and the given value
        """
        return cls(success=True, value=value)

    @classmethod
    def fail(
        cls,
        error: str,
        error_code: Optional[str] = None,
        validation_errors: Optional[List[ValidationError]] = None,
    ) -> "Result[T]":
        """
        Create a failed result.

        Args:
            error: Error message describing the failure
            error_code: Optional error code for categorization
            validation_errors: Optional list of field-level validation errors

        Returns:
            Result with success=False and error information
        """
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            validation_errors=validation_errors or [],
        )

    @classmethod
    def validation_failure(
        cls,
        errors: List[ValidationError],
        message: str = "Validation failed",
    ) -> "Result[T]":
        """
        Create a failed result from validation errors.

        Args:
            errors: List of validation errors
            message: Overall error message

        Returns:
            Result with validation errors
        """
        return cls(
            success=False,
            error=message,
            error_code="VALIDATION_ERROR",
            validation_errors=errors,
        )

    def map(self, func: Callable[[T], U]) -> "Result[U]":
        """
        Transform the success value.

        If this Result is successful, applies func to the value.
        If this Result is a failure, returns a new failure Result.

        Args:
            func: Function to transform the value

        Returns:
            New Result with transformed value or original error
        """
        if self.is_success and self.value is not None:
            try:
                return Result.ok(func(self.value))
            except Exception as e:
                return Result.fail(str(e))
        return Result.fail(
            self.error or "Unknown error",
            self.error_code,
            self.validation_errors,
        )

    def flat_map(self, func: Callable[[T], "Result[U]"]) -> "Result[U]":
        """
        Chain operations that return Results.

        If this Result is successful, applies func (which returns a Result).
        If this Result is a failure, returns a new failure Result.

        Args:
            func: Function that takes a value and returns a Result

        Returns:
            Result from func or original error
        """
        if self.is_success and self.value is not None:
            return func(self.value)
        return Result.fail(
            self.error or "Unknown error",
            self.error_code,
            self.validation_errors,
        )

    def unwrap(self) -> T:
        """
        Get the success value or raise an exception.

        Use this only when you're certain the Result is successful.

        Returns:
            The success value

        Raises:
            ValueError: If the Result is a failure
        """
        if self.is_failure:
            raise ValueError(f"Cannot unwrap failed Result: {self.error}")
        return self.value  # type: ignore

    def unwrap_or(self, default: T) -> T:
        """
        Get the success value or a default.

        Args:
            default: Value to return if this is a failure

        Returns:
            The success value or the default
        """
        if self.is_success and self.value is not None:
            return self.value
        return default

    def unwrap_or_else(self, func: Callable[[], T]) -> T:
        """
        Get the success value or compute a default.

        Args:
            func: Function to compute default value

        Returns:
            The success value or computed default
        """
        if self.is_success and self.value is not None:
            return self.value
        return func()

    def on_success(self, func: Callable[[T], Any]) -> "Result[T]":
        """
        Execute a function if successful.

        Args:
            func: Function to execute with the value

        Returns:
            This Result (for chaining)
        """
        if self.is_success and self.value is not None:
            func(self.value)
        return self

    def on_failure(self, func: Callable[[str], Any]) -> "Result[T]":
        """
        Execute a function if failed.

        Args:
            func: Function to execute with the error message

        Returns:
            This Result (for chaining)
        """
        if self.is_failure and self.error:
            func(self.error)
        return self

    def to_dict(self) -> dict:
        """
        Convert to dictionary representation.

        Useful for API responses.

        Returns:
            Dictionary with success, value/error, and validation_errors
        """
        result = {"success": self.success}

        if self.is_success:
            result["value"] = self.value
        else:
            result["error"] = self.error
            if self.error_code:
                result["error_code"] = self.error_code
            if self.validation_errors:
                result["validation_errors"] = [
                    e.to_dict() for e in self.validation_errors
                ]

        return result

    def __bool__(self) -> bool:
        """Allow using Result in boolean context."""
        return self.is_success


def combine_results(*results: Result[Any]) -> Result[List[Any]]:
    """
    Combine multiple Results into a single Result.

    If all Results are successful, returns a Result with list of values.
    If any Result is a failure, returns the first failure.

    Args:
        *results: Variable number of Results to combine

    Returns:
        Combined Result with list of values or first error
    """
    values = []
    for result in results:
        if result.is_failure:
            return Result.fail(
                result.error or "Unknown error",
                result.error_code,
                result.validation_errors,
            )
        values.append(result.value)

    return Result.ok(values)


def try_result(func: Callable[[], T]) -> Result[T]:
    """
    Execute a function and wrap the result.

    Converts exceptions to failed Results.

    Args:
        func: Function to execute

    Returns:
        Result with value or error
    """
    try:
        return Result.ok(func())
    except Exception as e:
        return Result.fail(str(e), type(e).__name__)
