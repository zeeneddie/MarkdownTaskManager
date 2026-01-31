"""
CSV Session Exporter - Tabular data for spreadsheet analysis

Week 61+: Enhanced Observability Integration - CSV Export
"""

import csv
import io
from datetime import datetime, timezone
from app.services.session_exporters.base import BaseSessionExporter, SessionData


class CSVSessionExporter(BaseSessionExporter):
    """
    Export CCTrace session to CSV format.

    Produces multi-section CSV with:
    - Session metadata
    - Metrics summary
    - Thinking blocks (optional)
    - Tool executions (optional)
    - Messages (optional)
    """

    @property
    def format_name(self) -> str:
        return "csv"

    @property
    def content_type(self) -> str:
        return "text/csv"

    @property
    def file_extension(self) -> str:
        return "csv"

    def export(
        self,
        session_data: SessionData,
        include_thinking: bool = True,
        include_tools: bool = True,
        include_messages: bool = True,
    ) -> str:
        """Export session to CSV format with multiple sections."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Section 1: Metadata
        writer.writerow(["=== SESSION METADATA ==="])
        writer.writerow(["Field", "Value"])
        writer.writerow(["session_id", session_data.session_id])
        writer.writerow(["created_at", session_data.created_at.isoformat() if session_data.created_at else ""])
        writer.writerow(["provider", session_data.provider])
        writer.writerow(["model", session_data.model])
        writer.writerow(["export_timestamp", datetime.now(timezone.utc).isoformat()])
        writer.writerow([])

        # Section 2: Metrics
        writer.writerow(["=== METRICS ==="])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["total_input_tokens", session_data.total_input_tokens])
        writer.writerow(["total_output_tokens", session_data.total_output_tokens])
        writer.writerow(["cache_creation_tokens", session_data.cache_creation_tokens])
        writer.writerow(["cache_read_tokens", session_data.cache_read_tokens])
        writer.writerow(["total_duration_ms", session_data.total_duration_ms])
        writer.writerow(["total_cost", session_data.total_cost])
        writer.writerow([])

        # Section 3: Thinking Blocks
        if include_thinking and session_data.thinking_blocks:
            writer.writerow(["=== THINKING BLOCKS ==="])
            writer.writerow(["sequence", "type", "content", "tokens", "signature", "hash"])
            for block in session_data.thinking_blocks:
                writer.writerow([
                    block.sequence_number,
                    block.block_type,
                    block.content,
                    block.token_count,
                    block.signature or "",
                    block.content_hash or "",
                ])
            writer.writerow([])

        # Section 4: Tool Executions
        if include_tools and session_data.tool_executions:
            writer.writerow(["=== TOOL EXECUTIONS ==="])
            writer.writerow(["tool_name", "success", "duration_ms", "error", "executed_at", "input", "output"])
            for tool in session_data.tool_executions:
                writer.writerow([
                    tool.tool_name,
                    tool.success,
                    tool.duration_ms or "",
                    tool.error_message or "",
                    tool.executed_at.isoformat() if tool.executed_at else "",
                    str(tool.tool_input),
                    (tool.tool_output or "")[:500],
                ])
            writer.writerow([])

        # Section 5: Messages
        if include_messages and session_data.messages:
            writer.writerow(["=== MESSAGES ==="])
            writer.writerow(["message_id", "parent_id", "role", "content", "timestamp"])
            for msg in session_data.messages:
                writer.writerow([
                    msg.message_id or "",
                    msg.parent_id or "",
                    msg.role,
                    msg.content,
                    msg.timestamp.isoformat() if msg.timestamp else "",
                ])

        return output.getvalue()
