"""
LLM Resilience Service - Fase 24.5

Provides retry logic, circuit breaker, and streaming support for LLM calls.

Features:
- Exponential backoff with jitter for transient failures
- Circuit breaker pattern to prevent cascading failures
- Configurable retry policies per tier/provider
- Streaming support with async generators

Author: Claude Code (Week 158 - Fase 24.5)
Date: 2026-01-19
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Coroutine,
    Dict,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
)

import aiohttp

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# Retry Policy
# =============================================================================


@dataclass
class RetryPolicy:
    """Configuration for retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts (0 = no retries)
        base_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay cap in seconds
        jitter_factor: Random jitter as fraction of delay (0.1 = 10%)
        retryable_status_codes: HTTP status codes that should trigger retry
        retryable_exceptions: Exception types that should trigger retry
    """
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    jitter_factor: float = 0.1
    retryable_status_codes: Set[int] = field(default_factory=lambda: {
        408,  # Request Timeout
        429,  # Too Many Requests (Rate Limited)
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504,  # Gateway Timeout
    })
    retryable_exceptions: Tuple[Type[Exception], ...] = field(default_factory=lambda: (
        asyncio.TimeoutError,
        aiohttp.ClientError,
        aiohttp.ServerDisconnectedError,
        ConnectionError,
        ConnectionResetError,
        ConnectionRefusedError,
    ))

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number with exponential backoff and jitter.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds with jitter applied
        """
        # Exponential backoff: base_delay * 2^attempt
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)

        # Add jitter to prevent thundering herd
        jitter = delay * self.jitter_factor * random.random()

        return delay + jitter

    def is_retryable_status(self, status_code: int) -> bool:
        """Check if HTTP status code should trigger retry."""
        return status_code in self.retryable_status_codes

    def is_retryable_exception(self, exc: Exception) -> bool:
        """Check if exception type should trigger retry."""
        return isinstance(exc, self.retryable_exceptions)


# Pre-configured policies for different tiers
RETRY_POLICIES: Dict[str, RetryPolicy] = {
    "FREE": RetryPolicy(
        max_retries=2,
        base_delay=2.0,
        max_delay=20.0,
    ),
    "BASIC": RetryPolicy(
        max_retries=3,
        base_delay=1.5,
        max_delay=25.0,
    ),
    "STANDARD": RetryPolicy(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
    ),
    "PROFESSIONAL": RetryPolicy(
        max_retries=4,
        base_delay=1.0,
        max_delay=30.0,
    ),
    "PREMIUM": RetryPolicy(
        max_retries=5,
        base_delay=0.5,
        max_delay=30.0,
    ),
    "DEFAULT": RetryPolicy(),  # Default policy
}


def get_retry_policy(tier: str = "DEFAULT") -> RetryPolicy:
    """Get retry policy for given tier.

    Args:
        tier: Tier name (FREE, BASIC, STANDARD, PROFESSIONAL, PREMIUM)

    Returns:
        RetryPolicy for the tier, or DEFAULT if not found
    """
    return RETRY_POLICIES.get(tier.upper(), RETRY_POLICIES["DEFAULT"])


# =============================================================================
# Circuit Breaker
# =============================================================================


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation, requests pass through
    OPEN = "open"          # Failing fast, requests rejected immediately
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration.

    Attributes:
        failure_threshold: Number of failures before opening circuit
        success_threshold: Number of successes in HALF_OPEN to close circuit
        timeout_seconds: Time to wait in OPEN state before testing
        half_open_max_calls: Maximum concurrent calls in HALF_OPEN state
    """
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 30.0
    half_open_max_calls: int = 1


class CircuitBreaker:
    """Circuit breaker implementation for LLM providers.

    Prevents cascading failures by failing fast when a provider is unhealthy.

    State transitions:
        CLOSED → OPEN: After failure_threshold consecutive failures
        OPEN → HALF_OPEN: After timeout_seconds
        HALF_OPEN → CLOSED: After success_threshold successes
        HALF_OPEN → OPEN: On any failure
    """

    def __init__(
        self,
        provider_id: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        self.provider_id = provider_id
        self.config = config or CircuitBreakerConfig()

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for timeout transitions."""
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                return CircuitState.HALF_OPEN
        return self._state

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return True
        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.config.timeout_seconds

    async def can_execute(self) -> bool:
        """Check if a request can be executed.

        Returns:
            True if request should proceed, False if circuit is open
        """
        async with self._lock:
            state = self.state

            if state == CircuitState.CLOSED:
                return True

            if state == CircuitState.OPEN:
                logger.warning(
                    f"Circuit breaker OPEN for {self.provider_id}, "
                    f"failing fast (wait {self.config.timeout_seconds}s)"
                )
                return False

            # HALF_OPEN: Allow limited test requests
            # Update internal state to HALF_OPEN if we transitioned via timeout
            if self._state == CircuitState.OPEN:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                logger.info(f"Circuit breaker transitioned to HALF_OPEN for {self.provider_id}")

            if self._half_open_calls < self.config.half_open_max_calls:
                self._half_open_calls += 1
                logger.info(
                    f"Circuit breaker HALF_OPEN for {self.provider_id}, "
                    f"allowing test request ({self._half_open_calls}/{self.config.half_open_max_calls})"
                )
                return True

            return False

    async def record_success(self) -> None:
        """Record a successful request."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            else:
                # Reset failure count on success in CLOSED state
                self._failure_count = 0

    async def record_failure(self, error: Optional[str] = None) -> None:
        """Record a failed request."""
        async with self._lock:
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN immediately opens circuit
                self._transition_to_open()
                logger.warning(
                    f"Circuit breaker reopened for {self.provider_id}: {error}"
                )
            else:
                self._failure_count += 1
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to_open()
                    logger.warning(
                        f"Circuit breaker opened for {self.provider_id} "
                        f"after {self._failure_count} failures: {error}"
                    )

    def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        self._state = CircuitState.OPEN
        self._success_count = 0
        self._half_open_calls = 0

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        logger.info(f"Circuit breaker closed for {self.provider_id}")

    async def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        async with self._lock:
            self._transition_to_closed()
            self._last_failure_time = None
            logger.info(f"Circuit breaker manually reset for {self.provider_id}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize circuit breaker state."""
        return {
            "provider_id": self.provider_id,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds,
            },
        }


class CircuitBreakerRegistry:
    """Registry for managing circuit breakers across providers."""

    def __init__(self, default_config: Optional[CircuitBreakerConfig] = None):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._default_config = default_config or CircuitBreakerConfig()
        self._lock = asyncio.Lock()

    async def get_breaker(self, provider_id: str) -> CircuitBreaker:
        """Get or create circuit breaker for provider."""
        async with self._lock:
            if provider_id not in self._breakers:
                self._breakers[provider_id] = CircuitBreaker(
                    provider_id, self._default_config
                )
            return self._breakers[provider_id]

    async def reset_all(self) -> None:
        """Reset all circuit breakers."""
        async with self._lock:
            for breaker in self._breakers.values():
                await breaker.reset()

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers."""
        return {
            provider_id: breaker.to_dict()
            for provider_id, breaker in self._breakers.items()
        }


# Global circuit breaker registry
circuit_breaker_registry = CircuitBreakerRegistry()


# =============================================================================
# Retry Execution
# =============================================================================


@dataclass
class RetryResult:
    """Result of a retried operation.

    Attributes:
        success: Whether the operation ultimately succeeded
        result: The result if successful, None otherwise
        attempts: Total number of attempts made
        total_time_ms: Total time spent including retries
        last_error: Last error message if failed
        retry_history: List of (attempt, delay, error) tuples
    """
    success: bool
    result: Optional[Any] = None
    attempts: int = 1
    total_time_ms: int = 0
    last_error: Optional[str] = None
    retry_history: list = field(default_factory=list)


async def call_with_retry(
    call_func: Callable[[], Coroutine[Any, Any, T]],
    policy: Optional[RetryPolicy] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
    operation_name: str = "LLM call",
) -> Tuple[bool, Optional[T], int, Optional[str]]:
    """Execute an async function with retry logic.

    Args:
        call_func: Async function to call (no arguments, use closure/partial)
        policy: Retry policy to use (default: DEFAULT policy)
        circuit_breaker: Optional circuit breaker for the provider
        operation_name: Name for logging purposes

    Returns:
        Tuple of (success, result, attempts, last_error)

    Example:
        success, result, attempts, error = await call_with_retry(
            lambda: some_async_function(arg1, arg2),
            policy=get_retry_policy("STANDARD"),
        )
    """
    policy = policy or RETRY_POLICIES["DEFAULT"]
    start_time = time.time()
    last_error: Optional[str] = None
    retry_history: list = []

    for attempt in range(policy.max_retries + 1):
        # Check circuit breaker
        if circuit_breaker and not await circuit_breaker.can_execute():
            return (
                False,
                None,
                attempt,
                f"Circuit breaker open for {operation_name}",
            )

        try:
            result = await call_func()

            # Check if result indicates failure (for LLMCallResult-like objects)
            if hasattr(result, "success") and not result.success:
                error_msg = getattr(result, "error", "Unknown error")

                # Check if error contains retryable status code
                is_retryable = False
                for code in policy.retryable_status_codes:
                    if str(code) in str(error_msg):
                        is_retryable = True
                        break

                if is_retryable and attempt < policy.max_retries:
                    delay = policy.calculate_delay(attempt)
                    last_error = error_msg
                    retry_history.append((attempt + 1, delay, error_msg))

                    logger.warning(
                        f"{operation_name}: Attempt {attempt + 1}/{policy.max_retries + 1} "
                        f"failed with retryable error: {error_msg}. "
                        f"Retrying in {delay:.2f}s"
                    )

                    await asyncio.sleep(delay)
                    continue
                else:
                    # Non-retryable error or max retries reached
                    if circuit_breaker:
                        await circuit_breaker.record_failure(error_msg)
                    return (False, result, attempt + 1, error_msg)

            # Success!
            if circuit_breaker:
                await circuit_breaker.record_success()

            if attempt > 0:
                total_time = int((time.time() - start_time) * 1000)
                logger.info(
                    f"{operation_name}: Succeeded on attempt {attempt + 1} "
                    f"after {total_time}ms total"
                )

            return (True, result, attempt + 1, None)

        except policy.retryable_exceptions as e:
            last_error = str(e)

            if attempt < policy.max_retries:
                delay = policy.calculate_delay(attempt)
                retry_history.append((attempt + 1, delay, last_error))

                logger.warning(
                    f"{operation_name}: Attempt {attempt + 1}/{policy.max_retries + 1} "
                    f"failed with {type(e).__name__}: {last_error}. "
                    f"Retrying in {delay:.2f}s"
                )

                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"{operation_name}: All {policy.max_retries + 1} attempts failed. "
                    f"Last error: {last_error}"
                )
                if circuit_breaker:
                    await circuit_breaker.record_failure(last_error)

        except Exception as e:
            # Non-retryable exception
            last_error = str(e)
            logger.error(
                f"{operation_name}: Non-retryable error on attempt {attempt + 1}: "
                f"{type(e).__name__}: {last_error}"
            )
            if circuit_breaker:
                await circuit_breaker.record_failure(last_error)
            return (False, None, attempt + 1, last_error)

    # All retries exhausted
    return (False, None, policy.max_retries + 1, last_error)


# =============================================================================
# Streaming Support
# =============================================================================


@dataclass
class StreamChunk:
    """A chunk of streaming response.

    Attributes:
        content: The text content of this chunk
        token_count: Number of tokens in this chunk (estimated)
        is_final: Whether this is the final chunk
        metadata: Additional metadata (latency, total tokens, etc.)
    """
    content: str
    token_count: int = 0
    is_final: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_sse(self) -> str:
        """Format chunk as Server-Sent Event."""
        import json
        data = {
            "type": "chunk" if not self.is_final else "done",
            "content": self.content,
            "token_count": self.token_count,
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return f"data: {json.dumps(data)}\n\n"


class StreamingBuffer:
    """Buffer for aggregating streaming chunks.

    Tracks total content, token count, and timing for streaming responses.
    """

    def __init__(self):
        self._chunks: list[str] = []
        self._total_tokens = 0
        self._start_time = time.time()
        self._first_token_time: Optional[float] = None

    def add_chunk(self, content: str, tokens: int = 0) -> None:
        """Add a chunk to the buffer."""
        if not self._first_token_time and content:
            self._first_token_time = time.time()
        self._chunks.append(content)
        self._total_tokens += tokens

    @property
    def content(self) -> str:
        """Get full aggregated content."""
        return "".join(self._chunks)

    @property
    def total_tokens(self) -> int:
        """Get total token count."""
        return self._total_tokens

    @property
    def time_to_first_token_ms(self) -> Optional[int]:
        """Get time to first token in milliseconds."""
        if self._first_token_time:
            return int((self._first_token_time - self._start_time) * 1000)
        return None

    @property
    def total_time_ms(self) -> int:
        """Get total elapsed time in milliseconds."""
        return int((time.time() - self._start_time) * 1000)

    def get_metadata(self) -> Dict[str, Any]:
        """Get aggregated metadata."""
        return {
            "total_tokens": self._total_tokens,
            "chunk_count": len(self._chunks),
            "time_to_first_token_ms": self.time_to_first_token_ms,
            "total_time_ms": self.total_time_ms,
        }


async def stream_with_retry(
    stream_func: Callable[[], AsyncGenerator[StreamChunk, None]],
    policy: Optional[RetryPolicy] = None,
    operation_name: str = "LLM stream",
) -> AsyncGenerator[StreamChunk, None]:
    """Execute a streaming function with retry logic.

    Only retries if the stream fails before yielding any chunks.
    Once chunks start flowing, failures are propagated.

    Args:
        stream_func: Async generator factory function
        policy: Retry policy to use
        operation_name: Name for logging

    Yields:
        StreamChunk objects from the underlying stream
    """
    policy = policy or RETRY_POLICIES["DEFAULT"]
    last_error: Optional[str] = None

    for attempt in range(policy.max_retries + 1):
        chunks_received = False

        try:
            async for chunk in stream_func():
                chunks_received = True
                yield chunk

                if chunk.is_final:
                    return

        except policy.retryable_exceptions as e:
            last_error = str(e)

            if not chunks_received and attempt < policy.max_retries:
                delay = policy.calculate_delay(attempt)
                logger.warning(
                    f"{operation_name}: Stream failed before receiving data. "
                    f"Attempt {attempt + 1}/{policy.max_retries + 1}. "
                    f"Retrying in {delay:.2f}s"
                )
                await asyncio.sleep(delay)
            else:
                # Already received chunks or max retries reached
                logger.error(f"{operation_name}: Stream failed: {last_error}")
                yield StreamChunk(
                    content="",
                    is_final=True,
                    metadata={"error": last_error, "partial": chunks_received},
                )
                return

        except Exception as e:
            # Non-retryable exception
            logger.error(f"{operation_name}: Non-retryable stream error: {e}")
            yield StreamChunk(
                content="",
                is_final=True,
                metadata={"error": str(e), "partial": chunks_received},
            )
            return

    # All retries exhausted without receiving any data
    yield StreamChunk(
        content="",
        is_final=True,
        metadata={"error": f"Failed after {policy.max_retries + 1} attempts: {last_error}"},
    )
