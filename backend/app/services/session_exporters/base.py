"""
Base Session Exporter - Abstract interface for export formats

Week 61: Enhanced Observability Integration
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


@dataclass
class ThinkingBlockExport:
    """Thinking block data for export."""
    block_type: str
    content: str
    token_count: int = 0
    sequence_number: int = 0
    signature: Optional[str] = None
    content_hash: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolExecutionExport:
    """Tool execution data for export."""
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Optional[str] = None
    duration_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    executed_at: Optional[datetime] = None


@dataclass
class MessageExport:
    """Message data for export."""
    role: str
    content: str
    message_id: Optional[str] = None
    parent_id: Optional[str] = None
    timestamp: Optional[datetime] = None


@dataclass
class SessionData:
    """
    Complete session data for export.

    Contains all information needed to export a CCTrace session.
    """
    session_id: str
    created_at: datetime
    provider: str = "unknown"
    model: str = "unknown"

    # Core data
    thinking_blocks: List[ThinkingBlockExport] = field(default_factory=list)
    tool_executions: List[ToolExecutionExport] = field(default_factory=list)
    messages: List[MessageExport] = field(default_factory=list)

    # Metrics
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    total_duration_ms: int = 0
    total_cost: float = 0.0

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "provider": self.provider,
            "model": self.model,
            "thinking_blocks": [
                {
                    "block_type": b.block_type,
                    "content": b.content,
                    "token_count": b.token_count,
                    "sequence_number": b.sequence_number,
                    "signature": b.signature,
                    "content_hash": b.content_hash,
                    "extra_data": b.extra_data,
                }
                for b in self.thinking_blocks
            ],
            "tool_executions": [
                {
                    "tool_name": t.tool_name,
                    "tool_input": t.tool_input,
                    "tool_output": t.tool_output,
                    "duration_ms": t.duration_ms,
                    "success": t.success,
                    "error_message": t.error_message,
                    "executed_at": t.executed_at.isoformat() if t.executed_at else None,
                }
                for t in self.tool_executions
            ],
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "message_id": m.message_id,
                    "parent_id": m.parent_id,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                }
                for m in self.messages
            ],
            "metrics": {
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "cache_creation_tokens": self.cache_creation_tokens,
                "cache_read_tokens": self.cache_read_tokens,
                "total_duration_ms": self.total_duration_ms,
                "total_cost": self.total_cost,
            },
            "metadata": self.metadata,
        }


class BaseSessionExporter(ABC):
    """
    Abstract base class for session exporters.

    Each exporter implements export() to produce format-specific output.
    """

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the format name (md, json, xml, jsonl)."""
        pass

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Return the MIME content type."""
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension."""
        pass

    @abstractmethod
    def export(
        self,
        session_data: SessionData,
        include_thinking: bool = True,
        include_tools: bool = True,
        include_messages: bool = True
    ) -> str:
        """
        Export session data to format-specific string.

        Args:
            session_data: Complete session data
            include_thinking: Include thinking blocks
            include_tools: Include tool executions
            include_messages: Include messages

        Returns:
            Formatted export string
        """
        pass

    def get_filename(self, session_id: str) -> str:
        """
        Generate filename for export.

        Args:
            session_id: Session identifier

        Returns:
            Filename with extension
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"session_{session_id}_{timestamp}.{self.file_extension}"
