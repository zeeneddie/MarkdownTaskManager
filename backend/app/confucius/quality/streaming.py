"""
SSE Streaming for Quality Gate Progress.

Provides Server-Sent Events streaming for real-time progress
updates during PIV (Plan-Implement-Validate) iteration cycles.
"""

from typing import Dict, Any, AsyncIterator, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class StreamEventType(str, Enum):
    """Types of SSE stream events."""
    # Lifecycle events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # Iteration events
    ITERATION_STARTED = "iteration_started"
    ITERATION_EXECUTING = "iteration_executing"
    ITERATION_EVALUATED = "iteration_evaluated"
    ITERATION_SUCCEEDED = "iteration_succeeded"
    ITERATION_FAILED = "iteration_failed"
    ITERATION_COMPLETED = "iteration_completed"

    # Quality events
    QUALITY_CHECK_STARTED = "quality_check_started"
    QUALITY_RULE_EVALUATED = "quality_rule_evaluated"
    QUALITY_CHECK_COMPLETED = "quality_check_completed"

    # Escalation events
    ESCALATION_TRIGGERED = "escalation_triggered"
    ESCALATION_RESOLVED = "escalation_resolved"

    # Progress events
    PROGRESS_UPDATE = "progress_update"
    PARTIAL_RESULT = "partial_result"

    # Heartbeat
    HEARTBEAT = "heartbeat"


@dataclass
class StreamEvent:
    """A single SSE event."""
    event_type: StreamEventType
    entry_id: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    sequence: int = 0

    def to_sse(self) -> str:
        """Format as SSE message."""
        event_data = {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "sequence": self.sequence,
            **self.data,
        }

        lines = [
            f"event: {self.event_type.value}",
            f"data: {json.dumps(event_data)}",
            "",
        ]
        return "\n".join(lines) + "\n"


class QualityProgressStream:
    """
    SSE stream manager for quality gate progress.

    Manages event queues and provides async iteration for SSE responses.

    Example:
    ```python
    stream = QualityProgressStream()

    # In API route
    async def stream_progress(entry_id: str):
        async for event in stream.subscribe(entry_id):
            yield event.to_sse()

    # In iteration controller
    await stream.emit(StreamEventType.ITERATION_STARTED, entry_id, {...})
    ```
    """

    def __init__(
        self,
        heartbeat_interval: float = 30.0,
        max_queue_size: int = 100,
    ):
        """
        Initialize stream manager.

        Args:
            heartbeat_interval: Seconds between heartbeats
            max_queue_size: Max events to queue per subscriber
        """
        self._heartbeat_interval = heartbeat_interval
        self._max_queue_size = max_queue_size
        self._subscribers: Dict[str, asyncio.Queue] = {}
        self._sequence_counters: Dict[str, int] = {}
        self._active = True

    async def emit(
        self,
        event_type: StreamEventType,
        entry_id: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Emit event to all subscribers of an entry.

        Args:
            event_type: Type of event
            entry_id: Entry ID to emit to
            data: Event data
        """
        # Increment sequence
        self._sequence_counters[entry_id] = (
            self._sequence_counters.get(entry_id, 0) + 1
        )

        event = StreamEvent(
            event_type=event_type,
            entry_id=entry_id,
            data=data,
            sequence=self._sequence_counters[entry_id],
        )

        # Emit to entry-specific subscribers
        if entry_id in self._subscribers:
            try:
                self._subscribers[entry_id].put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"Queue full for {entry_id}, dropping event")

        # Also emit to global subscribers (entry_id="*")
        if "*" in self._subscribers:
            try:
                self._subscribers["*"].put_nowait(event)
            except asyncio.QueueFull:
                pass

        logger.debug(f"Emitted {event_type.value} for {entry_id}")

    async def subscribe(
        self,
        entry_id: str,
        include_heartbeat: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """
        Subscribe to events for an entry.

        Args:
            entry_id: Entry ID to subscribe to (or "*" for all)
            include_heartbeat: Whether to include heartbeat events

        Yields:
            StreamEvent objects
        """
        queue = asyncio.Queue(maxsize=self._max_queue_size)
        self._subscribers[entry_id] = queue

        try:
            while self._active:
                try:
                    # Wait for event with heartbeat timeout
                    event = await asyncio.wait_for(
                        queue.get(),
                        timeout=self._heartbeat_interval,
                    )
                    yield event

                    # Check for terminal events
                    if event.event_type in [
                        StreamEventType.TASK_COMPLETED,
                        StreamEventType.TASK_FAILED,
                    ]:
                        break

                except asyncio.TimeoutError:
                    if include_heartbeat:
                        yield StreamEvent(
                            event_type=StreamEventType.HEARTBEAT,
                            entry_id=entry_id,
                            data={"status": "alive"},
                        )

        finally:
            # Cleanup subscription
            if entry_id in self._subscribers:
                del self._subscribers[entry_id]

    def unsubscribe(self, entry_id: str) -> bool:
        """
        Unsubscribe from entry events.

        Args:
            entry_id: Entry to unsubscribe from

        Returns:
            True if was subscribed, False otherwise
        """
        if entry_id in self._subscribers:
            del self._subscribers[entry_id]
            return True
        return False

    def get_subscriber_count(self) -> int:
        """Get number of active subscribers."""
        return len(self._subscribers)

    def shutdown(self) -> None:
        """Shutdown the stream manager."""
        self._active = False
        self._subscribers.clear()

    def create_progress_callback(
        self,
        entry_id: str,
    ) -> Callable[[str, Dict[str, Any]], Awaitable[None]]:
        """
        Create a progress callback for iteration controller.

        Args:
            entry_id: Entry ID for events

        Returns:
            Callback function compatible with IterationController
        """
        async def callback(event: str, data: Dict[str, Any]) -> None:
            # Map iteration events to stream events
            event_mapping = {
                "iteration_started": StreamEventType.ITERATION_STARTED,
                "iteration_executing": StreamEventType.ITERATION_EXECUTING,
                "iteration_evaluated": StreamEventType.ITERATION_EVALUATED,
                "iteration_completed": StreamEventType.ITERATION_COMPLETED,
            }

            event_type = event_mapping.get(event, StreamEventType.PROGRESS_UPDATE)
            await self.emit(event_type, entry_id, data)

        return callback


class QualityProgressContext:
    """
    Context manager for quality progress streaming.

    Automatically emits start/complete/fail events and provides
    convenient methods for progress updates.

    Example:
    ```python
    stream = QualityProgressStream()

    async with QualityProgressContext(stream, "task-123", "Felix") as ctx:
        await ctx.update_progress(0.25, "Analyzing architecture")
        result = await do_work()
        await ctx.emit_partial({"patterns": result.patterns})
    ```
    """

    def __init__(
        self,
        stream: QualityProgressStream,
        entry_id: str,
        agent_name: str,
        task_description: Optional[str] = None,
    ):
        """
        Initialize progress context.

        Args:
            stream: Stream manager
            entry_id: Entry ID
            agent_name: Agent name
            task_description: Optional task description
        """
        self._stream = stream
        self._entry_id = entry_id
        self._agent_name = agent_name
        self._task_description = task_description
        self._started_at: Optional[datetime] = None
        self._failed = False

    async def __aenter__(self) -> "QualityProgressContext":
        """Enter context - emit start event."""
        self._started_at = datetime.utcnow()
        await self._stream.emit(
            StreamEventType.TASK_STARTED,
            self._entry_id,
            {
                "agent_name": self._agent_name,
                "task": self._task_description,
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context - emit complete/fail event."""
        duration_ms = None
        if self._started_at:
            duration_ms = (datetime.utcnow() - self._started_at).total_seconds() * 1000

        if exc_type is not None:
            self._failed = True
            await self._stream.emit(
                StreamEventType.TASK_FAILED,
                self._entry_id,
                {
                    "agent_name": self._agent_name,
                    "error": str(exc_val),
                    "duration_ms": duration_ms,
                },
            )
        elif not self._failed:
            await self._stream.emit(
                StreamEventType.TASK_COMPLETED,
                self._entry_id,
                {
                    "agent_name": self._agent_name,
                    "duration_ms": duration_ms,
                },
            )

    async def update_progress(
        self,
        progress: float,
        message: Optional[str] = None,
    ) -> None:
        """
        Update progress percentage.

        Args:
            progress: Progress 0.0 - 1.0
            message: Optional status message
        """
        await self._stream.emit(
            StreamEventType.PROGRESS_UPDATE,
            self._entry_id,
            {
                "progress": round(progress, 3),
                "message": message,
                "agent_name": self._agent_name,
            },
        )

    async def emit_partial(
        self,
        data: Dict[str, Any],
    ) -> None:
        """
        Emit partial result.

        Args:
            data: Partial result data
        """
        await self._stream.emit(
            StreamEventType.PARTIAL_RESULT,
            self._entry_id,
            {
                "agent_name": self._agent_name,
                "partial": data,
            },
        )

    async def emit_iteration(
        self,
        iteration: int,
        status: str,
        score: Optional[float] = None,
    ) -> None:
        """
        Emit iteration status.

        Args:
            iteration: Iteration number
            status: Status string
            score: Optional quality score
        """
        data = {
            "iteration": iteration,
            "status": status,
            "agent_name": self._agent_name,
        }
        if score is not None:
            data["score"] = round(score, 3)

        event_type = StreamEventType.ITERATION_EVALUATED
        if status == "succeeded":
            event_type = StreamEventType.ITERATION_SUCCEEDED
        elif status == "failed":
            event_type = StreamEventType.ITERATION_FAILED

        await self._stream.emit(event_type, self._entry_id, data)

    def mark_failed(self) -> None:
        """Mark task as failed (for early exit)."""
        self._failed = True


# Global stream instance for shared use
_global_stream: Optional[QualityProgressStream] = None


def get_global_stream() -> QualityProgressStream:
    """
    Get or create global stream instance.

    Returns:
        Global QualityProgressStream instance
    """
    global _global_stream
    if _global_stream is None:
        _global_stream = QualityProgressStream()
    return _global_stream


def reset_global_stream() -> None:
    """Reset global stream (for testing)."""
    global _global_stream
    if _global_stream:
        _global_stream.shutdown()
    _global_stream = None
