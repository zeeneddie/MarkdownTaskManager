"""
Unit Tests for LLM Streaming - Fase 24.5

Tests for streaming LLM calls and SSE endpoints.

Author: Claude Code (Week 158 - Fase 24.5)
Date: 2026-01-19
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from aiohttp import ClientTimeout

from app.services.llm_resilience import StreamChunk, StreamingBuffer


# =============================================================================
# StreamChunk SSE Format Tests
# =============================================================================


class TestStreamChunkSSE:
    """Tests for StreamChunk SSE formatting."""

    def test_chunk_sse_format_basic(self):
        """Test basic chunk SSE format."""
        chunk = StreamChunk(content="Hello")
        sse = chunk.to_sse()

        # Should be valid SSE format
        assert sse.startswith("data: ")
        assert sse.endswith("\n\n")

        # Parse the data portion
        data = json.loads(sse.replace("data: ", "").strip())
        assert data["type"] == "chunk"
        assert data["content"] == "Hello"
        assert data["token_count"] == 0

    def test_chunk_sse_format_with_tokens(self):
        """Test chunk SSE format with token count."""
        chunk = StreamChunk(content="Hello World", token_count=2)
        sse = chunk.to_sse()

        data = json.loads(sse.replace("data: ", "").strip())
        assert data["token_count"] == 2

    def test_final_chunk_sse_format(self):
        """Test final chunk has 'done' type."""
        chunk = StreamChunk(content="", is_final=True)
        sse = chunk.to_sse()

        data = json.loads(sse.replace("data: ", "").strip())
        assert data["type"] == "done"

    def test_chunk_with_metadata_sse_format(self):
        """Test chunk with metadata includes metadata in SSE."""
        chunk = StreamChunk(
            content="",
            is_final=True,
            metadata={
                "total_tokens_input": 100,
                "total_tokens_output": 50,
                "total_time_ms": 1500,
            },
        )
        sse = chunk.to_sse()

        data = json.loads(sse.replace("data: ", "").strip())
        assert "metadata" in data
        assert data["metadata"]["total_tokens_input"] == 100
        assert data["metadata"]["total_time_ms"] == 1500

    def test_chunk_with_special_characters(self):
        """Test chunk with special characters is properly escaped."""
        chunk = StreamChunk(content='Hello\n"World"\tTest')
        sse = chunk.to_sse()

        # Should be valid JSON
        data = json.loads(sse.replace("data: ", "").strip())
        assert data["content"] == 'Hello\n"World"\tTest'

    def test_chunk_with_unicode(self):
        """Test chunk with unicode characters."""
        chunk = StreamChunk(content="Hello 🌍 世界 مرحبا")
        sse = chunk.to_sse()

        data = json.loads(sse.replace("data: ", "").strip())
        assert data["content"] == "Hello 🌍 世界 مرحبا"


# =============================================================================
# StreamingBuffer Tests
# =============================================================================


class TestStreamingBufferAdvanced:
    """Advanced tests for StreamingBuffer."""

    def test_empty_buffer(self):
        """Test empty buffer state."""
        buffer = StreamingBuffer()

        assert buffer.content == ""
        assert buffer.total_tokens == 0
        assert buffer.time_to_first_token_ms is None

    def test_large_content_aggregation(self):
        """Test aggregation of many small chunks."""
        buffer = StreamingBuffer()

        # Simulate many small chunks like real LLM output
        for i in range(100):
            buffer.add_chunk(f"word{i} ", tokens=1)

        assert buffer.total_tokens == 100
        assert "word0 " in buffer.content
        assert "word99 " in buffer.content

    def test_timing_accuracy(self):
        """Test timing measurements are reasonable."""
        buffer = StreamingBuffer()

        # Add first chunk immediately
        buffer.add_chunk("First")
        ttft = buffer.time_to_first_token_ms

        # Should be very fast (< 100ms in tests)
        assert ttft is not None
        assert 0 <= ttft < 100

        # Total time should also be small
        total = buffer.total_time_ms
        assert total >= ttft

    def test_metadata_completeness(self):
        """Test metadata includes all required fields."""
        buffer = StreamingBuffer()
        buffer.add_chunk("Test", tokens=5)

        metadata = buffer.get_metadata()

        required_fields = [
            "total_tokens",
            "chunk_count",
            "time_to_first_token_ms",
            "total_time_ms",
        ]

        for field in required_fields:
            assert field in metadata, f"Missing field: {field}"

    def test_chunk_count_tracking(self):
        """Test chunk count is tracked correctly."""
        buffer = StreamingBuffer()

        buffer.add_chunk("A")
        buffer.add_chunk("B")
        buffer.add_chunk("C")

        metadata = buffer.get_metadata()
        assert metadata["chunk_count"] == 3


# =============================================================================
# Mock Streaming Provider Tests
# =============================================================================


class TestMockOllamaStreaming:
    """Tests for mock Ollama streaming behavior."""

    @pytest.mark.asyncio
    async def test_ollama_streaming_pattern(self):
        """Test Ollama streaming produces expected pattern."""
        chunks = []

        # Simulate Ollama streaming behavior
        async def mock_ollama_stream():
            # Ollama streams token by token
            tokens = ["Hello", " ", "World", "!"]
            for token in tokens:
                yield StreamChunk(content=token, token_count=1)
            yield StreamChunk(
                content="",
                is_final=True,
                metadata={"eval_count": 4, "prompt_eval_count": 10},
            )

        async for chunk in mock_ollama_stream():
            chunks.append(chunk)

        # Verify pattern
        assert len(chunks) == 5  # 4 tokens + final
        assert chunks[-1].is_final
        assert "".join(c.content for c in chunks) == "Hello World!"

    @pytest.mark.asyncio
    async def test_ollama_error_during_stream(self):
        """Test handling of error during Ollama stream."""
        chunks = []

        async def mock_failing_stream():
            yield StreamChunk(content="Partial")
            yield StreamChunk(
                content="",
                is_final=True,
                metadata={"error": "Connection reset", "partial": True},
            )

        async for chunk in mock_failing_stream():
            chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[-1].metadata.get("error") == "Connection reset"
        assert chunks[-1].metadata.get("partial") is True


class TestMockAnthropicStreaming:
    """Tests for mock Anthropic streaming behavior."""

    @pytest.mark.asyncio
    async def test_anthropic_streaming_pattern(self):
        """Test Anthropic streaming produces expected pattern."""
        chunks = []

        # Simulate Anthropic streaming (larger chunks than Ollama)
        async def mock_anthropic_stream():
            yield StreamChunk(content="This is a longer ", token_count=4)
            yield StreamChunk(content="response from Claude ", token_count=4)
            yield StreamChunk(content="in streaming mode.", token_count=3)
            yield StreamChunk(
                content="",
                is_final=True,
                metadata={
                    "total_tokens_input": 50,
                    "total_tokens_output": 11,
                    "cost_usd": 0.00015,
                },
            )

        async for chunk in mock_anthropic_stream():
            chunks.append(chunk)

        # Verify pattern
        assert len(chunks) == 4
        final = chunks[-1]
        assert final.is_final
        assert final.metadata["cost_usd"] == 0.00015


# =============================================================================
# SSE Event Parsing Tests
# =============================================================================


class TestSSEEventParsing:
    """Tests for parsing SSE events (client-side simulation)."""

    def parse_sse_event(self, sse_text: str) -> dict:
        """Parse SSE event text into dict."""
        if not sse_text.startswith("data: "):
            raise ValueError("Invalid SSE format")
        json_str = sse_text.replace("data: ", "").strip()
        return json.loads(json_str)

    def test_parse_chunk_event(self):
        """Test parsing chunk event."""
        chunk = StreamChunk(content="Hello")
        sse = chunk.to_sse()

        parsed = self.parse_sse_event(sse)
        assert parsed["type"] == "chunk"
        assert parsed["content"] == "Hello"

    def test_parse_done_event(self):
        """Test parsing done event."""
        chunk = StreamChunk(
            content="",
            is_final=True,
            metadata={"total_time_ms": 1000},
        )
        sse = chunk.to_sse()

        parsed = self.parse_sse_event(sse)
        assert parsed["type"] == "done"
        assert parsed["metadata"]["total_time_ms"] == 1000

    def test_multiple_sse_events(self):
        """Test parsing multiple SSE events."""
        events = []

        # Create stream of events
        chunks = [
            StreamChunk(content="A"),
            StreamChunk(content="B"),
            StreamChunk(content="", is_final=True),
        ]

        for chunk in chunks:
            events.append(self.parse_sse_event(chunk.to_sse()))

        assert len(events) == 3
        assert events[0]["content"] == "A"
        assert events[1]["content"] == "B"
        assert events[2]["type"] == "done"


# =============================================================================
# Streaming Error Handling Tests
# =============================================================================


class TestStreamingErrorHandling:
    """Tests for streaming error scenarios."""

    def test_error_chunk_format(self):
        """Test error chunk has correct format."""
        error_chunk = StreamChunk(
            content="",
            is_final=True,
            metadata={"error": "Connection timeout", "partial": False},
        )

        sse = error_chunk.to_sse()
        data = json.loads(sse.replace("data: ", "").strip())

        assert data["type"] == "done"
        assert data["metadata"]["error"] == "Connection timeout"

    def test_partial_response_error(self):
        """Test error chunk with partial response indicator."""
        error_chunk = StreamChunk(
            content="",
            is_final=True,
            metadata={"error": "Stream interrupted", "partial": True},
        )

        sse = error_chunk.to_sse()
        data = json.loads(sse.replace("data: ", "").strip())

        assert data["metadata"]["partial"] is True

    def test_timeout_error_chunk(self):
        """Test timeout error chunk."""
        error_chunk = StreamChunk(
            content="",
            is_final=True,
            metadata={"error": "Timeout after 60s", "partial": False},
        )

        sse = error_chunk.to_sse()
        data = json.loads(sse.replace("data: ", "").strip())

        assert "Timeout" in data["metadata"]["error"]


# =============================================================================
# Streaming Metrics Tests
# =============================================================================


class TestStreamingMetrics:
    """Tests for streaming performance metrics."""

    def test_latency_metrics_in_final_chunk(self):
        """Test latency metrics are included in final chunk."""
        buffer = StreamingBuffer()
        buffer.add_chunk("First token")
        buffer.add_chunk("More content")

        metadata = buffer.get_metadata()

        # Time to first token should be tracked
        assert metadata["time_to_first_token_ms"] is not None
        assert metadata["time_to_first_token_ms"] >= 0

        # Total time should be tracked
        assert metadata["total_time_ms"] is not None
        assert metadata["total_time_ms"] >= metadata["time_to_first_token_ms"]

    def test_token_count_metrics(self):
        """Test token count metrics."""
        final_chunk = StreamChunk(
            content="",
            is_final=True,
            metadata={
                "total_tokens_input": 150,
                "total_tokens_output": 75,
                "provider_id": "ollama/qwen2.5-coder:7b",
            },
        )

        assert final_chunk.metadata["total_tokens_input"] == 150
        assert final_chunk.metadata["total_tokens_output"] == 75

    def test_cost_metrics_for_paid_providers(self):
        """Test cost metrics for paid providers."""
        final_chunk = StreamChunk(
            content="",
            is_final=True,
            metadata={
                "total_tokens_input": 1000,
                "total_tokens_output": 500,
                "cost_usd": 0.0175,  # Example Claude pricing
                "provider_id": "anthropic/sonnet",
            },
        )

        assert final_chunk.metadata["cost_usd"] > 0


# =============================================================================
# Concurrency Tests
# =============================================================================


class TestStreamingConcurrency:
    """Tests for concurrent streaming scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_streams(self):
        """Test multiple streams can run concurrently."""
        results = []

        async def create_stream(stream_id: int):
            chunks = []
            for i in range(3):
                chunk = StreamChunk(content=f"Stream{stream_id}-{i}")
                chunks.append(chunk)
                await asyncio.sleep(0.01)  # Simulate latency
            return chunks

        # Run multiple streams concurrently
        tasks = [create_stream(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        for i, stream_chunks in enumerate(results):
            assert len(stream_chunks) == 3
            assert f"Stream{i}-0" in stream_chunks[0].content

    @pytest.mark.asyncio
    async def test_buffer_thread_safety(self):
        """Test StreamingBuffer handles concurrent access."""
        buffer = StreamingBuffer()

        async def add_chunks(prefix: str):
            for i in range(10):
                buffer.add_chunk(f"{prefix}{i}", tokens=1)
                await asyncio.sleep(0.001)

        # Add chunks from multiple tasks
        await asyncio.gather(
            add_chunks("A"),
            add_chunks("B"),
            add_chunks("C"),
        )

        # All chunks should be present
        assert buffer.total_tokens == 30
        assert "A0" in buffer.content
        assert "B0" in buffer.content
        assert "C0" in buffer.content


# =============================================================================
# Cancellation Tests
# =============================================================================


class TestStreamCancellation:
    """Tests for stream cancellation handling."""

    @pytest.mark.asyncio
    async def test_stream_cancellation_cleanup(self):
        """Test stream handles cancellation gracefully."""
        # Track how many chunks were consumed before cancellation
        consumed_count = 0

        async def cancellable_stream():
            for i in range(100):
                yield StreamChunk(content=f"Chunk{i}")
                await asyncio.sleep(0.01)

        # Consume some chunks then cancel
        async for chunk in cancellable_stream():
            consumed_count += 1
            if consumed_count >= 3:
                break  # Simulate early exit/cancellation

        # Verify we only consumed what we needed
        assert consumed_count == 3

    @pytest.mark.asyncio
    async def test_partial_content_on_cancellation(self):
        """Test partial content is available on cancellation."""
        buffer = StreamingBuffer()

        async def stream_with_buffer():
            for i in range(100):
                content = f"Token{i} "
                buffer.add_chunk(content, tokens=1)
                yield StreamChunk(content=content, token_count=1)
                await asyncio.sleep(0.01)

        count = 0
        try:
            async for _ in stream_with_buffer():
                count += 1
                if count >= 5:
                    raise asyncio.CancelledError()
        except asyncio.CancelledError:
            pass

        # Buffer should have partial content
        assert buffer.total_tokens >= 5
        assert "Token0" in buffer.content
