"""
Unit Tests for LLM Resilience Service - Fase 24.5

Tests for retry logic, circuit breaker, and streaming support.

Author: Claude Code (Week 158 - Fase 24.5)
Date: 2026-01-19
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from app.services.llm_resilience import (
    RetryPolicy,
    get_retry_policy,
    RETRY_POLICIES,
    CircuitState,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerRegistry,
    call_with_retry,
    StreamChunk,
    StreamingBuffer,
    stream_with_retry,
)


# =============================================================================
# RetryPolicy Tests
# =============================================================================


class TestRetryPolicy:
    """Tests for RetryPolicy configuration and behavior."""

    def test_default_policy_values(self):
        """Test default retry policy has expected values."""
        policy = RetryPolicy()
        assert policy.max_retries == 3
        assert policy.base_delay == 1.0
        assert policy.max_delay == 30.0
        assert policy.jitter_factor == 0.1
        assert 429 in policy.retryable_status_codes
        assert 503 in policy.retryable_status_codes
        assert asyncio.TimeoutError in policy.retryable_exceptions

    def test_custom_policy_values(self):
        """Test custom retry policy configuration."""
        policy = RetryPolicy(
            max_retries=5,
            base_delay=2.0,
            max_delay=60.0,
            jitter_factor=0.2,
        )
        assert policy.max_retries == 5
        assert policy.base_delay == 2.0
        assert policy.max_delay == 60.0
        assert policy.jitter_factor == 0.2

    def test_calculate_delay_exponential_backoff(self):
        """Test delay increases exponentially with attempts."""
        policy = RetryPolicy(base_delay=1.0, jitter_factor=0.0)

        # Without jitter, delays should be exact powers of 2
        delay_0 = policy.calculate_delay(0)
        delay_1 = policy.calculate_delay(1)
        delay_2 = policy.calculate_delay(2)
        delay_3 = policy.calculate_delay(3)

        assert delay_0 == 1.0  # 1 * 2^0
        assert delay_1 == 2.0  # 1 * 2^1
        assert delay_2 == 4.0  # 1 * 2^2
        assert delay_3 == 8.0  # 1 * 2^3

    def test_calculate_delay_respects_max_delay(self):
        """Test delay is capped at max_delay."""
        policy = RetryPolicy(base_delay=1.0, max_delay=5.0, jitter_factor=0.0)

        # Attempt 10 would be 1024s without cap
        delay = policy.calculate_delay(10)
        assert delay == 5.0  # Capped at max_delay

    def test_calculate_delay_includes_jitter(self):
        """Test delay includes random jitter."""
        policy = RetryPolicy(base_delay=1.0, jitter_factor=0.1)

        # Run multiple times - should see variation
        delays = [policy.calculate_delay(0) for _ in range(10)]
        unique_delays = set(delays)

        # With jitter, we should see some variation
        assert len(unique_delays) > 1

        # All delays should be within expected range (1.0 to 1.1)
        for delay in delays:
            assert 1.0 <= delay <= 1.1

    def test_is_retryable_status(self):
        """Test retryable status code detection."""
        policy = RetryPolicy()

        # Retryable codes
        assert policy.is_retryable_status(429) is True
        assert policy.is_retryable_status(503) is True
        assert policy.is_retryable_status(504) is True
        assert policy.is_retryable_status(500) is True

        # Non-retryable codes
        assert policy.is_retryable_status(200) is False
        assert policy.is_retryable_status(400) is False
        assert policy.is_retryable_status(401) is False
        assert policy.is_retryable_status(403) is False
        assert policy.is_retryable_status(404) is False

    def test_is_retryable_exception(self):
        """Test retryable exception detection."""
        policy = RetryPolicy()

        # Retryable exceptions
        assert policy.is_retryable_exception(asyncio.TimeoutError()) is True
        assert policy.is_retryable_exception(ConnectionError()) is True
        assert policy.is_retryable_exception(ConnectionResetError()) is True

        # Non-retryable exceptions
        assert policy.is_retryable_exception(ValueError()) is False
        assert policy.is_retryable_exception(KeyError()) is False


class TestRetryPolicies:
    """Tests for tier-based retry policies."""

    def test_all_tiers_have_policies(self):
        """Test all expected tiers have defined policies."""
        expected_tiers = ["FREE", "BASIC", "STANDARD", "PROFESSIONAL", "PREMIUM", "DEFAULT"]
        for tier in expected_tiers:
            assert tier in RETRY_POLICIES

    def test_get_retry_policy_valid_tier(self):
        """Test getting policy for valid tier."""
        policy = get_retry_policy("PREMIUM")
        assert policy.max_retries == 5
        assert policy.base_delay == 0.5

    def test_get_retry_policy_invalid_tier(self):
        """Test invalid tier returns DEFAULT policy."""
        policy = get_retry_policy("INVALID_TIER")
        assert policy == RETRY_POLICIES["DEFAULT"]

    def test_get_retry_policy_case_insensitive(self):
        """Test tier lookup is case insensitive."""
        policy1 = get_retry_policy("premium")
        policy2 = get_retry_policy("PREMIUM")
        policy3 = get_retry_policy("Premium")

        assert policy1 == policy2 == policy3

    def test_higher_tiers_have_more_retries(self):
        """Test that higher tiers have more generous retry settings."""
        free = RETRY_POLICIES["FREE"]
        premium = RETRY_POLICIES["PREMIUM"]

        assert premium.max_retries > free.max_retries
        assert premium.base_delay < free.base_delay  # Faster retry for premium


# =============================================================================
# CircuitBreaker Tests
# =============================================================================


class TestCircuitBreaker:
    """Tests for circuit breaker pattern."""

    @pytest.fixture
    def breaker(self):
        """Create a circuit breaker for testing."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=1.0,  # Short timeout for testing
        )
        return CircuitBreaker("test-provider", config)

    @pytest.mark.asyncio
    async def test_initial_state_is_closed(self, breaker):
        """Test circuit breaker starts in CLOSED state."""
        assert breaker.state == CircuitState.CLOSED
        assert await breaker.can_execute() is True

    @pytest.mark.asyncio
    async def test_opens_after_failure_threshold(self, breaker):
        """Test circuit opens after failure_threshold failures."""
        # Record failures up to threshold
        for _ in range(3):
            await breaker.record_failure("Test error")

        assert breaker.state == CircuitState.OPEN
        assert await breaker.can_execute() is False

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self, breaker):
        """Test success resets failure count in CLOSED state."""
        # Record some failures (but not enough to open)
        await breaker.record_failure("Error 1")
        await breaker.record_failure("Error 2")

        # Success should reset
        await breaker.record_success()

        # Now need full failure_threshold again to open
        await breaker.record_failure("Error 3")
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self, breaker):
        """Test circuit transitions to HALF_OPEN after timeout."""
        # Open the circuit
        for _ in range(3):
            await breaker.record_failure("Test error")

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(1.1)

        # Should be HALF_OPEN now
        assert breaker.state == CircuitState.HALF_OPEN
        assert await breaker.can_execute() is True

    @pytest.mark.asyncio
    async def test_closes_after_success_in_half_open(self, breaker):
        """Test circuit closes after success_threshold successes in HALF_OPEN."""
        # Open the circuit
        for _ in range(3):
            await breaker.record_failure("Test error")

        # Wait for timeout
        await asyncio.sleep(1.1)

        # Must call can_execute to transition internal state to HALF_OPEN
        assert await breaker.can_execute() is True

        # Now internal _state is HALF_OPEN, record successes
        await breaker.record_success()
        await breaker.record_success()

        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_reopens_on_failure_in_half_open(self, breaker):
        """Test circuit reopens on any failure in HALF_OPEN state."""
        # Open the circuit
        for _ in range(3):
            await breaker.record_failure("Test error")

        # Wait for timeout to reach HALF_OPEN
        await asyncio.sleep(1.1)

        # Manually set to half_open state by allowing execution
        assert await breaker.can_execute() is True

        # Any failure should reopen
        await breaker.record_failure("Test error in half-open")

        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_manual_reset(self, breaker):
        """Test manual reset returns to CLOSED state."""
        # Open the circuit
        for _ in range(3):
            await breaker.record_failure("Test error")

        assert breaker.state == CircuitState.OPEN

        # Manual reset
        await breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert await breaker.can_execute() is True

    def test_to_dict_serialization(self, breaker):
        """Test circuit breaker state serialization."""
        state_dict = breaker.to_dict()

        assert state_dict["provider_id"] == "test-provider"
        assert state_dict["state"] == "closed"
        assert state_dict["failure_count"] == 0
        assert "config" in state_dict


class TestCircuitBreakerRegistry:
    """Tests for circuit breaker registry."""

    @pytest.mark.asyncio
    async def test_get_breaker_creates_new(self):
        """Test registry creates new breaker for unknown provider."""
        registry = CircuitBreakerRegistry()
        breaker = await registry.get_breaker("new-provider")

        assert breaker is not None
        assert breaker.provider_id == "new-provider"

    @pytest.mark.asyncio
    async def test_get_breaker_returns_existing(self):
        """Test registry returns existing breaker for known provider."""
        registry = CircuitBreakerRegistry()

        breaker1 = await registry.get_breaker("provider-x")
        breaker2 = await registry.get_breaker("provider-x")

        assert breaker1 is breaker2

    @pytest.mark.asyncio
    async def test_reset_all(self):
        """Test reset_all resets all circuit breakers."""
        registry = CircuitBreakerRegistry()

        # Create and break some breakers
        breaker1 = await registry.get_breaker("provider-1")
        breaker2 = await registry.get_breaker("provider-2")

        for _ in range(5):
            await breaker1.record_failure("Error")
            await breaker2.record_failure("Error")

        # Reset all
        await registry.reset_all()

        assert breaker1.state == CircuitState.CLOSED
        assert breaker2.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_get_all_states(self):
        """Test getting all circuit breaker states."""
        registry = CircuitBreakerRegistry()

        await registry.get_breaker("provider-a")
        await registry.get_breaker("provider-b")

        states = registry.get_all_states()

        assert "provider-a" in states
        assert "provider-b" in states
        assert states["provider-a"]["state"] == "closed"


# =============================================================================
# call_with_retry Tests
# =============================================================================


class TestCallWithRetry:
    """Tests for call_with_retry function."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        """Test successful call on first attempt."""
        async def successful_call():
            return MagicMock(success=True, content="result")

        success, result, attempts, error = await call_with_retry(successful_call)

        assert success is True
        assert result.content == "result"
        assert attempts == 1
        assert error is None

    @pytest.mark.asyncio
    async def test_retries_on_transient_error(self):
        """Test retries on transient errors."""
        call_count = 0

        async def flaky_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise asyncio.TimeoutError("Timeout")
            return MagicMock(success=True, content="result")

        policy = RetryPolicy(max_retries=3, base_delay=0.01)
        success, result, attempts, error = await call_with_retry(
            flaky_call, policy=policy
        )

        assert success is True
        assert call_count == 3
        assert attempts == 3

    @pytest.mark.asyncio
    async def test_respects_max_retries(self):
        """Test stops after max_retries."""
        call_count = 0

        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise asyncio.TimeoutError("Timeout")

        policy = RetryPolicy(max_retries=2, base_delay=0.01)
        success, result, attempts, error = await call_with_retry(
            always_fails, policy=policy
        )

        assert success is False
        assert call_count == 3  # 1 initial + 2 retries
        assert attempts == 3
        assert "Timeout" in error

    @pytest.mark.asyncio
    async def test_no_retry_on_non_retryable_error(self):
        """Test non-retryable exceptions fail immediately."""
        call_count = 0

        async def non_retryable_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid input")

        success, result, attempts, error = await call_with_retry(non_retryable_error)

        assert success is False
        assert call_count == 1  # No retries
        assert attempts == 1
        assert "Invalid input" in error

    @pytest.mark.asyncio
    async def test_retries_on_retryable_status_in_result(self):
        """Test retries when result contains retryable status code."""
        call_count = 0

        async def returns_503():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return MagicMock(success=False, error="503 Service Unavailable")
            return MagicMock(success=True, content="result")

        policy = RetryPolicy(max_retries=3, base_delay=0.01)
        success, result, attempts, error = await call_with_retry(
            returns_503, policy=policy
        )

        assert success is True
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_circuit_breaker_prevents_call(self):
        """Test circuit breaker prevents calls when open."""
        async def should_not_be_called():
            raise AssertionError("Should not be called")

        # Create an open circuit breaker
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=1))
        await breaker.record_failure("Test error")

        success, result, attempts, error = await call_with_retry(
            should_not_be_called, circuit_breaker=breaker
        )

        assert success is False
        assert "Circuit breaker open" in error

    @pytest.mark.asyncio
    async def test_records_success_to_circuit_breaker(self):
        """Test successful call records to circuit breaker."""
        async def successful_call():
            return MagicMock(success=True)

        breaker = CircuitBreaker("test")
        breaker.record_success = AsyncMock()

        await call_with_retry(successful_call, circuit_breaker=breaker)

        breaker.record_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_records_failure_to_circuit_breaker(self):
        """Test failed call records to circuit breaker."""
        async def failing_call():
            raise ValueError("Error")

        breaker = CircuitBreaker("test")
        breaker.record_failure = AsyncMock()

        await call_with_retry(failing_call, circuit_breaker=breaker)

        breaker.record_failure.assert_called_once()


# =============================================================================
# StreamChunk Tests
# =============================================================================


class TestStreamChunk:
    """Tests for StreamChunk data class."""

    def test_basic_chunk(self):
        """Test basic chunk creation."""
        chunk = StreamChunk(content="Hello", token_count=1)
        assert chunk.content == "Hello"
        assert chunk.token_count == 1
        assert chunk.is_final is False

    def test_final_chunk(self):
        """Test final chunk with metadata."""
        chunk = StreamChunk(
            content="",
            is_final=True,
            metadata={"total_tokens": 100, "latency_ms": 500},
        )
        assert chunk.is_final is True
        assert chunk.metadata["total_tokens"] == 100

    def test_to_sse_format(self):
        """Test SSE formatting."""
        chunk = StreamChunk(content="Hello")
        sse = chunk.to_sse()

        assert sse.startswith("data: ")
        assert sse.endswith("\n\n")
        assert '"type": "chunk"' in sse
        assert '"content": "Hello"' in sse

    def test_to_sse_final_chunk(self):
        """Test SSE formatting for final chunk."""
        chunk = StreamChunk(content="", is_final=True)
        sse = chunk.to_sse()

        assert '"type": "done"' in sse


class TestStreamingBuffer:
    """Tests for StreamingBuffer class."""

    def test_add_chunks(self):
        """Test adding chunks to buffer."""
        buffer = StreamingBuffer()
        buffer.add_chunk("Hello ")
        buffer.add_chunk("World")

        assert buffer.content == "Hello World"

    def test_token_tracking(self):
        """Test token count tracking."""
        buffer = StreamingBuffer()
        buffer.add_chunk("Hello", tokens=1)
        buffer.add_chunk(" ", tokens=0)
        buffer.add_chunk("World", tokens=1)

        assert buffer.total_tokens == 2

    def test_time_to_first_token(self):
        """Test time to first token tracking."""
        buffer = StreamingBuffer()

        # Before any content
        assert buffer.time_to_first_token_ms is None

        # Add first content
        buffer.add_chunk("Hello")
        ttft = buffer.time_to_first_token_ms

        assert ttft is not None
        assert ttft >= 0

    def test_get_metadata(self):
        """Test metadata aggregation."""
        buffer = StreamingBuffer()
        buffer.add_chunk("Hello", tokens=1)
        buffer.add_chunk(" World", tokens=1)

        metadata = buffer.get_metadata()

        assert metadata["total_tokens"] == 2
        assert metadata["chunk_count"] == 2
        assert "time_to_first_token_ms" in metadata
        assert "total_time_ms" in metadata


# =============================================================================
# stream_with_retry Tests
# =============================================================================


class TestStreamWithRetry:
    """Tests for stream_with_retry function."""

    @pytest.mark.asyncio
    async def test_streams_chunks_successfully(self):
        """Test successful streaming of chunks."""
        async def generate_chunks():
            yield StreamChunk(content="Hello ", token_count=1)
            yield StreamChunk(content="World", token_count=1)
            yield StreamChunk(content="", is_final=True)

        chunks = []
        async for chunk in stream_with_retry(generate_chunks):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0].content == "Hello "
        assert chunks[1].content == "World"
        assert chunks[2].is_final is True

    @pytest.mark.asyncio
    async def test_retries_before_first_chunk(self):
        """Test retries when error occurs before any chunks."""
        call_count = 0

        async def flaky_stream():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise asyncio.TimeoutError("Timeout")
            yield StreamChunk(content="Success", is_final=True)

        policy = RetryPolicy(max_retries=2, base_delay=0.01)
        chunks = []
        async for chunk in stream_with_retry(flaky_stream, policy=policy):
            chunks.append(chunk)

        assert call_count == 2
        assert len(chunks) == 1
        assert chunks[0].content == "Success"

    @pytest.mark.asyncio
    async def test_no_retry_after_chunks_received(self):
        """Test no retry after chunks have been received."""
        call_count = 0

        async def partial_stream():
            nonlocal call_count
            call_count += 1
            yield StreamChunk(content="Partial")
            raise asyncio.TimeoutError("Timeout mid-stream")

        chunks = []
        async for chunk in stream_with_retry(partial_stream):
            chunks.append(chunk)

        assert call_count == 1  # No retry after receiving data
        assert len(chunks) == 2  # Partial + error chunk
        assert chunks[0].content == "Partial"
        assert chunks[1].is_final is True
        assert "error" in chunks[1].metadata

    @pytest.mark.asyncio
    async def test_error_chunk_on_complete_failure(self):
        """Test error chunk returned when all retries fail."""
        async def always_fails():
            raise asyncio.TimeoutError("Timeout")
            yield  # Never reached

        policy = RetryPolicy(max_retries=1, base_delay=0.01)
        chunks = []
        async for chunk in stream_with_retry(always_fails, policy=policy):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0].is_final is True
        assert "error" in chunks[0].metadata
        # Error can be either the raw error message or a "Failed after" message
        error_msg = chunks[0].metadata.get("error", "")
        assert "Timeout" in error_msg or "Failed after" in error_msg


# =============================================================================
# Integration Tests
# =============================================================================


class TestResilienceIntegration:
    """Integration tests for resilience components."""

    @pytest.mark.asyncio
    async def test_retry_with_circuit_breaker_flow(self):
        """Test complete flow with retry and circuit breaker."""
        call_count = 0
        breaker = CircuitBreaker(
            "integration-test",
            CircuitBreakerConfig(failure_threshold=5),
        )

        async def unreliable_call():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise asyncio.TimeoutError("Timeout")
            return MagicMock(success=True, content="Success")

        policy = RetryPolicy(max_retries=3, base_delay=0.01)
        success, result, attempts, error = await call_with_retry(
            unreliable_call,
            policy=policy,
            circuit_breaker=breaker,
        )

        assert success is True
        assert result.content == "Success"
        assert call_count == 3
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_opens_after_repeated_failures(self):
        """Test circuit opens after repeated failures across calls."""
        breaker = CircuitBreaker(
            "failure-test",
            CircuitBreakerConfig(failure_threshold=3),
        )

        async def always_fails():
            raise asyncio.TimeoutError("Timeout")

        policy = RetryPolicy(max_retries=0, base_delay=0.01)  # No retries

        # Make calls until circuit opens
        for _ in range(3):
            await call_with_retry(
                always_fails,
                policy=policy,
                circuit_breaker=breaker,
            )

        assert breaker.state == CircuitState.OPEN

        # Next call should fail fast
        call_made = False

        async def should_not_be_called():
            nonlocal call_made
            call_made = True
            return MagicMock(success=True)

        success, _, _, error = await call_with_retry(
            should_not_be_called,
            circuit_breaker=breaker,
        )

        assert success is False
        assert call_made is False
        assert "Circuit breaker open" in error
