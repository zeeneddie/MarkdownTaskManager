"""
JSON Session Exporter - Structured data for analysis

Week 61: Enhanced Observability Integration
"""

import json
from datetime import datetime, timezone
from typing import Any
from app.services.session_exporters.base import BaseSessionExporter, SessionData


class JSONSessionExporter(BaseSessionExporter):
    """
    Export CCTrace session to JSON format.

    Produces structured JSON with:
    - Full session metadata
    - Thinking blocks with all fields
    - Tool executions with timing
    - Message hierarchy
    - Complete metrics
    """

    @property
    def format_name(self) -> str:
        return "json"

    @property
    def content_type(self) -> str:
        return "application/json"

    @property
    def file_extension(self) -> str:
        return "json"

    def export(
        self,
        session_data: SessionData,
        include_thinking: bool = True,
        include_tools: bool = True,
        include_messages: bool = True
    ) -> str:
        """Export session to JSON format."""
        data = self._build_export_data(
            session_data,
            include_thinking,
            include_tools,
            include_messages
        )

        return json.dumps(data, indent=2, default=self._json_serializer)

    def _build_export_data(
        self,
        session_data: SessionData,
        include_thinking: bool,
        include_tools: bool,
        include_messages: bool
    ) -> dict:
        """Build export data structure."""
        data = {
            "cctrace_version": "1.0",
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "session": {
                "id": session_data.session_id,
                "created_at": session_data.created_at.isoformat() if session_data.created_at else None,
                "provider": session_data.provider,
                "model": session_data.model,
            },
            "metrics": {
                "tokens": {
                    "input": session_data.total_input_tokens,
                    "output": session_data.total_output_tokens,
                    "total": session_data.total_input_tokens + session_data.total_output_tokens,
                },
                "cache": {
                    "creation": session_data.cache_creation_tokens,
                    "read": session_data.cache_read_tokens,
                    "savings_percent": self._calculate_cache_savings(session_data),
                },
                "timing": {
                    "total_duration_ms": session_data.total_duration_ms,
                },
                "cost": {
                    "total_usd": session_data.total_cost,
                },
            },
            "metadata": session_data.metadata,
        }

        if include_thinking:
            data["thinking_blocks"] = [
                {
                    "type": block.block_type,
                    "content": block.content,
                    "tokens": block.token_count,
                    "sequence": block.sequence_number,
                    "signature": block.signature,
                    "hash": block.content_hash,
                    "extra": block.extra_data,
                }
                for block in session_data.thinking_blocks
            ]

        if include_tools:
            data["tool_executions"] = [
                {
                    "name": tool.tool_name,
                    "input": tool.tool_input,
                    "output": tool.tool_output,
                    "duration_ms": tool.duration_ms,
                    "success": tool.success,
                    "error": tool.error_message,
                    "executed_at": tool.executed_at.isoformat() if tool.executed_at else None,
                }
                for tool in session_data.tool_executions
            ]

        if include_messages:
            data["messages"] = [
                {
                    "id": msg.message_id,
                    "parent_id": msg.parent_id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                }
                for msg in session_data.messages
            ]

        return data

    def _calculate_cache_savings(self, session_data: SessionData) -> float:
        """Calculate cache savings percentage."""
        total_input = session_data.total_input_tokens
        cache_read = session_data.cache_read_tokens

        if total_input == 0:
            return 0.0

        # Cache read tokens are tokens that didn't need to be processed
        return round((cache_read / (total_input + cache_read)) * 100, 2)

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for datetime and other types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
