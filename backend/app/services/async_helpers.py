"""
Async Helper Utilities for Brown Paper Service Refactoring

This module provides utilities for the async-first architecture migration,
including deprecation warnings for sync wrappers and async utilities.

Created as part of Fase 24.7: Async Database Persistence Refactoring
"""

import warnings
import functools
from typing import TypeVar, Callable, Any

T = TypeVar('T')


def deprecated_sync_wrapper(
    async_method_name: str,
    removal_version: str = "26.0"
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to mark sync wrapper methods as deprecated.

    The decorated method will emit a DeprecationWarning indicating that
    the async version should be used instead.

    Args:
        async_method_name: Name of the async method to use instead
        removal_version: Version when this sync method will be removed

    Usage:
        @deprecated_sync_wrapper("get_session", "26.0")
        def get_session_sync(self, session_id: str) -> Optional[Session]:
            return self._sessions.get(session_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            warnings.warn(
                f"{func.__name__}() is deprecated. "
                f"Use {async_method_name}() (async) instead. "
                f"This sync method will be removed in v{removal_version}.",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_deprecated_sync_call(
    method_name: str,
    async_method_name: str,
    logger: Any
) -> None:
    """
    Log a warning when a deprecated sync method is called.

    This is for methods where the decorator pattern doesn't fit well.

    Args:
        method_name: Name of the deprecated sync method
        async_method_name: Name of the async method to use instead
        logger: Logger instance to use for warning
    """
    logger.warning(
        f"DEPRECATED: {method_name}() called. "
        f"Use {async_method_name}() (async) instead. "
        "Sync methods will be removed in v26.0."
    )


class CacheOnlyAccessMixin:
    """
    Mixin providing cache-only access pattern for sync wrappers.

    Sync wrapper methods should only access in-memory cache, never
    directly access the database to avoid nested event loop issues.
    """

    @staticmethod
    def get_cache_or_none(
        cache: dict,
        key: str,
        logger: Any = None
    ) -> Any:
        """
        Get value from cache or return None.

        Unlike DB access, this never blocks or requires async context.
        Logs a debug message if the key is not in cache.

        Args:
            cache: Dictionary cache to lookup
            key: Key to lookup
            logger: Optional logger for debug messages

        Returns:
            Cached value or None if not found
        """
        value = cache.get(key)
        if value is None and logger:
            logger.debug(
                f"Cache miss for key '{key}'. "
                "Use async method for DB lookup."
            )
        return value
