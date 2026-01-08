"""
CCTrace Models - Enhanced Observability for Multi-Provider LLM Systems

Week 61: CCTrace Integration
Based on patterns from github.com/jimmc414/cctrace and github.com/alexfazio/cc-trace

Models:
- ThinkingBlock: LLM reasoning capture (Claude native, Codex pseudo, Ollama CoT)
- ToolExecution: Complete tool I/O without truncation
- MessageRelationship: Parent-child conversation threading
- SessionExport: Export audit trail
- BudgetConfig: Cost management settings
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class ThinkingBlock(Base):
    """
    LLM reasoning/thinking block capture.

    Supports multiple providers:
    - Claude CLI: Native `thinking` blocks with cryptographic signature
    - Codex CLI: Pseudo-thinking extracted from `<thinking>` tags
    - Ollama: Chain-of-Thought (CoT) forcing with tag extraction

    Used for:
    - Self-Evolution learning (ChromaDB thinking_patterns collection)
    - Debugging and analysis
    - Pattern recognition for agent improvement
    """
    __tablename__ = "thinking_blocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(Integer, ForeignKey('agent_actions.id', ondelete='CASCADE'), nullable=True)
    session_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    message_id = Column(PGUUID(as_uuid=True), nullable=False)
    parent_message_id = Column(PGUUID(as_uuid=True), nullable=True)
    provider = Column(String(30), nullable=False)  # claude, codex, ollama
    block_type = Column(String(30), nullable=False)  # thinking, reasoning, cot, reflection
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=True)  # SHA-256 for verification
    signature = Column(String(256), nullable=True)  # Claude native cryptographic signature
    token_count = Column(Integer, default=0)
    sequence_number = Column(Integer, default=0)  # Order within message
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    __table_args__ = (
        Index('ix_thinking_blocks_session', 'session_id'),
        Index('ix_thinking_blocks_action', 'action_id'),
        Index('ix_thinking_blocks_provider', 'provider'),
        Index('ix_thinking_blocks_message', 'message_id'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action_id": self.action_id,
            "session_id": str(self.session_id) if self.session_id else None,
            "message_id": str(self.message_id) if self.message_id else None,
            "parent_message_id": str(self.parent_message_id) if self.parent_message_id else None,
            "provider": self.provider,
            "block_type": self.block_type,
            "content": self.content,
            "content_hash": self.content_hash,
            "signature": self.signature,
            "token_count": self.token_count,
            "sequence_number": self.sequence_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ToolExecution(Base):
    """
    Complete tool I/O logging without truncation.

    Unlike agent_actions which stores summaries, this stores:
    - Full input parameters (JSONB, no truncation)
    - Full output response (JSONB, no truncation)
    - Detailed timing and status information

    Used for:
    - Debugging tool failures
    - Analyzing tool usage patterns
    - Session export with complete context
    """
    __tablename__ = "tool_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(Integer, ForeignKey('agent_actions.id', ondelete='CASCADE'), nullable=True)
    session_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    message_id = Column(PGUUID(as_uuid=True), nullable=False)
    tool_name = Column(String(100), nullable=False)  # Read, Write, Bash, Grep, etc.
    tool_type = Column(String(50), nullable=True)  # read, write, bash, search, navigate
    input_full = Column(JSONB, nullable=False)  # Complete input (no truncation)
    output_full = Column(JSONB, nullable=True)  # Complete output (no truncation)
    description = Column(Text, nullable=True)  # Tool-provided description
    status = Column(String(30), default='pending')  # pending, success, error, timeout
    error_message = Column(Text, nullable=True)
    response_code = Column(Integer, nullable=True)
    byte_count_input = Column(Integer, default=0)
    byte_count_output = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    extra_data = Column(JSONB, default=dict)

    __table_args__ = (
        Index('ix_tool_executions_session', 'session_id'),
        Index('ix_tool_executions_action', 'action_id'),
        Index('ix_tool_executions_tool', 'tool_name'),
        Index('ix_tool_executions_message', 'message_id'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action_id": self.action_id,
            "session_id": str(self.session_id) if self.session_id else None,
            "message_id": str(self.message_id) if self.message_id else None,
            "tool_name": self.tool_name,
            "tool_type": self.tool_type,
            "input_full": self.input_full,
            "output_full": self.output_full,
            "description": self.description,
            "status": self.status,
            "error_message": self.error_message,
            "response_code": self.response_code,
            "byte_count_input": self.byte_count_input,
            "byte_count_output": self.byte_count_output,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "extra_data": self.extra_data or {},
        }


class MessageRelationship(Base):
    """
    Parent-child conversation threading.

    Tracks the hierarchical structure of conversations:
    - Message UUIDs with parent references
    - Role information (user, assistant, system)
    - Quick metadata for tree building

    Used for:
    - Session export with proper structure
    - Conversation context analysis
    - Message tree visualization
    """
    __tablename__ = "message_relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    message_id = Column(PGUUID(as_uuid=True), nullable=False, unique=True)
    parent_message_id = Column(PGUUID(as_uuid=True), nullable=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    model = Column(String(100), nullable=True)  # Model used for assistant messages
    provider = Column(String(30), nullable=True)  # Provider for assistant messages
    content_summary = Column(Text, nullable=True)  # First 500 chars for quick reference
    has_thinking_blocks = Column(Boolean, default=False)
    has_tool_calls = Column(Boolean, default=False)
    token_input = Column(Integer, default=0)
    token_output = Column(Integer, default=0)
    timestamp = Column(DateTime, default=lambda: datetime.utcnow())

    __table_args__ = (
        Index('ix_message_relationships_session', 'session_id'),
        Index('ix_message_relationships_parent', 'parent_message_id'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": str(self.session_id) if self.session_id else None,
            "message_id": str(self.message_id) if self.message_id else None,
            "parent_message_id": str(self.parent_message_id) if self.parent_message_id else None,
            "role": self.role,
            "model": self.model,
            "provider": self.provider,
            "content_summary": self.content_summary,
            "has_thinking_blocks": self.has_thinking_blocks,
            "has_tool_calls": self.has_tool_calls,
            "token_input": self.token_input,
            "token_output": self.token_output,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class SessionExport(Base):
    """
    Session export audit trail.

    Tracks all session exports with metadata:
    - Export format (markdown, json, xml, jsonl)
    - Included content (thinking blocks, tools)
    - Statistics (message count, tokens, cost)

    Used for:
    - Audit trail of exports
    - Re-download of previous exports
    - Usage analytics
    """
    __tablename__ = "session_exports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    project_id = Column(Integer, nullable=True)
    export_format = Column(String(20), nullable=False)  # markdown, json, xml, jsonl
    file_path = Column(Text, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    message_count = Column(Integer, default=0)
    thinking_block_count = Column(Integer, default=0)
    tool_execution_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost_cents = Column(Numeric(10, 4), default=0)
    include_thinking = Column(Boolean, default=True)
    include_tools = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    created_by = Column(String(100), nullable=True)

    __table_args__ = (
        Index('ix_session_exports_session', 'session_id'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": str(self.session_id) if self.session_id else None,
            "project_id": self.project_id,
            "export_format": self.export_format,
            "file_path": self.file_path,
            "file_size_bytes": self.file_size_bytes,
            "message_count": self.message_count,
            "thinking_block_count": self.thinking_block_count,
            "tool_execution_count": self.tool_execution_count,
            "total_tokens": self.total_tokens,
            "total_cost_cents": float(self.total_cost_cents) if self.total_cost_cents else 0,
            "include_thinking": self.include_thinking,
            "include_tools": self.include_tools,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }


class BudgetConfig(Base):
    """
    Budget management configuration.

    Defines budget limits with:
    - Threshold settings (warning at 80%, cutoff at 100%)
    - Fallback chain (Opus → Sonnet → Ollama)
    - Per-project or global scope

    Used for:
    - Cost control
    - Automatic model fallback
    - Usage alerts
    """
    __tablename__ = "budget_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    budget_type = Column(String(30), nullable=False)  # daily, monthly, project
    budget_cents = Column(Integer, nullable=False)
    warning_threshold = Column(Numeric(3, 2), default=0.80)  # 80%
    cutoff_threshold = Column(Numeric(3, 2), default=1.00)  # 100%
    fallback_enabled = Column(Boolean, default=True)
    fallback_chain = Column(JSONB, default=list)  # ["opus", "sonnet", "ollama"]
    is_active = Column(Boolean, default=True)
    project_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "budget_type": self.budget_type,
            "budget_cents": self.budget_cents,
            "budget_dollars": self.budget_cents / 100 if self.budget_cents else 0,
            "warning_threshold": float(self.warning_threshold) if self.warning_threshold else 0.80,
            "cutoff_threshold": float(self.cutoff_threshold) if self.cutoff_threshold else 1.00,
            "fallback_enabled": self.fallback_enabled,
            "fallback_chain": self.fallback_chain or ["opus", "sonnet", "ollama"],
            "is_active": self.is_active,
            "project_id": self.project_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
