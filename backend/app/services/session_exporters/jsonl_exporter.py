"""
JSONL Session Exporter - Line-delimited JSON for streaming/ML

Week 61: Enhanced Observability Integration

JSONL format is ideal for:
- Streaming processing
- ML training data
- Log aggregation systems
- Append-only storage
"""

import json
from datetime import datetime, timezone
from typing import Any, List
from app.services.session_exporters.base import BaseSessionExporter, SessionData


class JSONLSessionExporter(BaseSessionExporter):
    """
    Export CCTrace session to JSONL (JSON Lines) format.

    Produces one JSON object per line:
    1. Session metadata record
    2. Metrics record
    3. One record per thinking block
    4. One record per tool execution
    5. One record per message
    """

    @property
    def format_name(self) -> str:
        return "jsonl"

    @property
    def content_type(self) -> str:
        return "application/x-ndjson"

    @property
    def file_extension(self) -> str:
        return "jsonl"

    def export(
        self,
        session_data: SessionData,
        include_thinking: bool = True,
        include_tools: bool = True,
        include_messages: bool = True
    ) -> str:
        """Export session to JSONL format."""
        lines: List[str] = []

        # Session metadata record
        lines.append(self._serialize({
            "record_type": "session",
            "session_id": session_data.session_id,
            "created_at": session_data.created_at.isoformat() if session_data.created_at else None,
            "provider": session_data.provider,
            "model": session_data.model,
            "metadata": session_data.metadata,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
        }))

        # Metrics record
        lines.append(self._serialize({
            "record_type": "metrics",
            "session_id": session_data.session_id,
            "input_tokens": session_data.total_input_tokens,
            "output_tokens": session_data.total_output_tokens,
            "cache_creation_tokens": session_data.cache_creation_tokens,
            "cache_read_tokens": session_data.cache_read_tokens,
            "duration_ms": session_data.total_duration_ms,
            "cost_usd": session_data.total_cost,
        }))

        # Thinking blocks
        if include_thinking:
            for i, block in enumerate(session_data.thinking_blocks):
                lines.append(self._serialize({
                    "record_type": "thinking_block",
                    "session_id": session_data.session_id,
                    "sequence": i,
                    "block_type": block.block_type,
                    "content": block.content,
                    "token_count": block.token_count,
                    "signature": block.signature,
                    "content_hash": block.content_hash,
                    "extra_data": block.extra_data,
                }))

        # Tool executions
        if include_tools:
            for i, tool in enumerate(session_data.tool_executions):
                lines.append(self._serialize({
                    "record_type": "tool_execution",
                    "session_id": session_data.session_id,
                    "sequence": i,
                    "tool_name": tool.tool_name,
                    "tool_input": tool.tool_input,
                    "tool_output": tool.tool_output[:5000] if tool.tool_output else None,
                    "duration_ms": tool.duration_ms,
                    "success": tool.success,
                    "error": tool.error_message,
                    "executed_at": tool.executed_at.isoformat() if tool.executed_at else None,
                }))

        # Messages
        if include_messages:
            for i, msg in enumerate(session_data.messages):
                lines.append(self._serialize({
                    "record_type": "message",
                    "session_id": session_data.session_id,
                    "sequence": i,
                    "message_id": msg.message_id,
                    "parent_id": msg.parent_id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                }))

        return "\n".join(lines)

    def _serialize(self, obj: dict) -> str:
        """Serialize object to single JSON line."""
        return json.dumps(obj, default=self._json_serializer, ensure_ascii=False)

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for datetime and other types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class JSONLStreamExporter:
    """
    Streaming JSONL exporter for real-time capture.

    Use this when you want to export records as they happen
    rather than all at once.
    """

    def __init__(self, session_id: str):
        """
        Initialize streaming exporter.

        Args:
            session_id: Session identifier
        """
        self.session_id = session_id
        self._sequence = 0

    def emit_session_start(
        self,
        provider: str,
        model: str,
        metadata: dict = None
    ) -> str:
        """Emit session start record."""
        return self._serialize({
            "record_type": "session_start",
            "session_id": self.session_id,
            "provider": provider,
            "model": model,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def emit_thinking_block(
        self,
        block_type: str,
        content: str,
        token_count: int = 0,
        signature: str = None,
        content_hash: str = None,
        extra_data: dict = None
    ) -> str:
        """Emit thinking block record."""
        record = self._serialize({
            "record_type": "thinking_block",
            "session_id": self.session_id,
            "sequence": self._sequence,
            "block_type": block_type,
            "content": content,
            "token_count": token_count,
            "signature": signature,
            "content_hash": content_hash,
            "extra_data": extra_data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self._sequence += 1
        return record

    def emit_tool_execution(
        self,
        tool_name: str,
        tool_input: dict,
        tool_output: str = None,
        duration_ms: int = None,
        success: bool = True,
        error: str = None
    ) -> str:
        """Emit tool execution record."""
        record = self._serialize({
            "record_type": "tool_execution",
            "session_id": self.session_id,
            "sequence": self._sequence,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output[:5000] if tool_output else None,
            "duration_ms": duration_ms,
            "success": success,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self._sequence += 1
        return record

    def emit_message(
        self,
        role: str,
        content: str,
        message_id: str = None,
        parent_id: str = None
    ) -> str:
        """Emit message record."""
        record = self._serialize({
            "record_type": "message",
            "session_id": self.session_id,
            "sequence": self._sequence,
            "message_id": message_id,
            "parent_id": parent_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self._sequence += 1
        return record

    def emit_session_end(
        self,
        total_tokens: int = 0,
        total_cost: float = 0.0,
        duration_ms: int = 0
    ) -> str:
        """Emit session end record."""
        return self._serialize({
            "record_type": "session_end",
            "session_id": self.session_id,
            "total_sequence": self._sequence,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def _serialize(self, obj: dict) -> str:
        """Serialize object to single JSON line."""
        return json.dumps(obj, default=self._json_serializer, ensure_ascii=False)

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for datetime."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
