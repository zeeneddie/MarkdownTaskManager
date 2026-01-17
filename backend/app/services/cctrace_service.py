"""
CCTrace Service - Chain-of-Thought Capture and Analysis

Week 61: Enhanced Observability Integration

Captures thinking blocks, tool executions, and message hierarchies
from LLM providers (Claude, Codex, Ollama) for analysis and export.

Inspired by: https://github.com/jimmc414/cctrace
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Type
from sqlalchemy.orm import Session

from app.models.cctrace import (
    ThinkingBlock,
    ToolExecution,
    MessageRelationship,
    SessionExport,
)
from app.models.observability import AgentAction
from app.services.thinking_extractors import (
    BaseThinkingExtractor,
    ThinkingBlockData,
    ClaudeThinkingExtractor,
    CodexThinkingExtractor,
    OllamaThinkingExtractor,
)


class CCTraceService:
    """
    Service for capturing and analyzing LLM Chain-of-Thought.

    Features:
    - Multi-provider thinking block extraction
    - Tool execution logging with timing
    - Message hierarchy tracking (parent-child)
    - Session export in multiple formats
    - Token cache metrics
    """

    # Provider to extractor mapping
    EXTRACTORS: Dict[str, Type[BaseThinkingExtractor]] = {
        "claude": ClaudeThinkingExtractor,
        "codex": CodexThinkingExtractor,
        "ollama": OllamaThinkingExtractor,
    }

    def __init__(self, db: Session):
        """
        Initialize CCTrace service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self._extractors: Dict[str, BaseThinkingExtractor] = {}

    def get_extractor(self, provider: str) -> Optional[BaseThinkingExtractor]:
        """
        Get or create extractor for provider.

        Args:
            provider: Provider name (claude, codex, ollama)

        Returns:
            Extractor instance or None if not supported
        """
        provider = provider.lower()

        if provider not in self._extractors:
            extractor_class = self.EXTRACTORS.get(provider)
            if extractor_class:
                self._extractors[provider] = extractor_class()

        return self._extractors.get(provider)

    def capture_thinking_blocks(
        self,
        action_id: int,
        provider: str,
        response_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> List[ThinkingBlock]:
        """
        Extract and store thinking blocks from LLM response.

        Args:
            action_id: ID of the AgentAction record
            provider: LLM provider name
            response_data: Raw LLM response
            session_id: Optional session identifier

        Returns:
            List of created ThinkingBlock records
        """
        extractor = self.get_extractor(provider)
        if not extractor:
            return []

        if not extractor.can_extract(response_data):
            return []

        # Extract thinking blocks
        blocks_data = extractor.extract(response_data)

        # Store in database
        created_blocks = []
        for block_data in blocks_data:
            db_block = ThinkingBlock(
                action_id=action_id,
                session_id=session_id,
                block_type=block_data.block_type,
                content=block_data.content,
                token_count=block_data.token_count,
                sequence_number=block_data.sequence_number,
                signature=block_data.signature,
                content_hash=block_data.content_hash,
                extra_data=block_data.extra_data,
            )
            self.db.add(db_block)
            created_blocks.append(db_block)

        self.db.flush()  # Get IDs without committing
        return created_blocks

    def log_tool_execution(
        self,
        action_id: int,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Optional[str] = None,
        duration_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
        parent_tool_id: Optional[int] = None
    ) -> ToolExecution:
        """
        Log a tool execution event.

        Args:
            action_id: ID of the AgentAction record
            tool_name: Name of the tool executed
            tool_input: Tool input parameters
            tool_output: Tool output (may be truncated)
            duration_ms: Execution time in milliseconds
            success: Whether execution succeeded
            error_message: Error message if failed
            session_id: Optional session identifier
            parent_tool_id: Parent tool ID for nested executions

        Returns:
            Created ToolExecution record
        """
        # Truncate output if too large
        if tool_output and len(tool_output) > 10000:
            tool_output = tool_output[:10000] + "\n...[truncated]..."

        db_tool = ToolExecution(
            action_id=action_id,
            session_id=session_id,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            parent_tool_id=parent_tool_id,
        )
        self.db.add(db_tool)
        self.db.flush()
        return db_tool

    def build_message_tree(
        self,
        session_id: str,
        messages: List[Dict[str, Any]]
    ) -> List[MessageRelationship]:
        """
        Build message hierarchy from conversation.

        Creates parent-child relationships for:
        - User messages → Assistant responses
        - Multi-turn conversations
        - Tool calls and results

        Args:
            session_id: Session identifier
            messages: List of message dicts with role, content, id

        Returns:
            List of created MessageRelationship records
        """
        relationships = []
        parent_id = None
        depth = 0

        for i, msg in enumerate(messages):
            msg_id = msg.get("id") or str(uuid.uuid4())
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Calculate content preview
            preview = content[:200] if isinstance(content, str) else str(content)[:200]

            # Determine relationship type
            if role == "user":
                rel_type = "user_to_assistant"
                depth = 0
                parent_id = None  # Reset for new user turn
            elif role == "assistant":
                rel_type = "assistant_response"
                depth = 1
            elif role == "tool":
                rel_type = "tool_result"
                depth = 2
            else:
                rel_type = "continuation"

            db_rel = MessageRelationship(
                session_id=session_id,
                parent_message_id=uuid.UUID(parent_id) if parent_id else None,
                child_message_id=uuid.UUID(msg_id),
                relationship_type=rel_type,
                sequence_in_parent=i,
                depth_level=depth,
                metadata={
                    "role": role,
                    "content_preview": preview,
                    "index": i,
                }
            )
            self.db.add(db_rel)
            relationships.append(db_rel)

            # Update parent for next iteration
            if role in ("user", "assistant"):
                parent_id = msg_id

        self.db.flush()
        return relationships

    def update_action_cache_metrics(
        self,
        action_id: int,
        provider: str,
        response_data: Dict[str, Any]
    ) -> Optional[AgentAction]:
        """
        Update AgentAction with token cache metrics.

        Args:
            action_id: ID of the AgentAction record
            provider: LLM provider name
            response_data: Raw LLM response

        Returns:
            Updated AgentAction or None
        """
        action = self.db.query(AgentAction).filter(
            AgentAction.id == action_id
        ).first()

        if not action:
            return None

        extractor = self.get_extractor(provider)
        if not extractor:
            return action

        # Extract cache info based on provider
        if provider == "claude":
            cache_info = extractor.extract_token_cache_info(response_data)
            action.token_cache_creation = cache_info.get("cache_creation", 0)
            action.token_cache_read = cache_info.get("cache_read", 0)
        elif provider == "ollama":
            timing_info = extractor.extract_timing_info(response_data)
            # Ollama doesn't have cache, but we track token counts
            action.input_tokens = timing_info.get("prompt_tokens", 0)
            action.output_tokens = timing_info.get("completion_tokens", 0)
        elif provider == "codex":
            token_info = extractor.extract_token_info(response_data)
            action.input_tokens = token_info.get("input_tokens", 0)
            action.output_tokens = token_info.get("output_tokens", 0)

        self.db.flush()
        return action

    def get_session_thinking_blocks(
        self,
        session_id: str
    ) -> List[ThinkingBlock]:
        """
        Get all thinking blocks for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of ThinkingBlock records
        """
        return self.db.query(ThinkingBlock).filter(
            ThinkingBlock.session_id == session_id
        ).order_by(
            ThinkingBlock.sequence_number
        ).all()

    def get_session_tool_executions(
        self,
        session_id: str
    ) -> List[ToolExecution]:
        """
        Get all tool executions for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of ToolExecution records
        """
        return self.db.query(ToolExecution).filter(
            ToolExecution.session_id == session_id
        ).order_by(
            ToolExecution.executed_at
        ).all()

    def get_session_summary(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get summary statistics for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dict with thinking blocks, tool executions, token counts
        """
        thinking_blocks = self.get_session_thinking_blocks(session_id)
        tool_executions = self.get_session_tool_executions(session_id)

        # Calculate totals
        total_thinking_tokens = sum(b.token_count or 0 for b in thinking_blocks)
        total_tool_duration = sum(t.duration_ms or 0 for t in tool_executions)
        successful_tools = sum(1 for t in tool_executions if t.success)
        failed_tools = sum(1 for t in tool_executions if not t.success)

        # Group by type
        block_types = {}
        for block in thinking_blocks:
            block_types[block.block_type] = block_types.get(block.block_type, 0) + 1

        tool_names = {}
        for tool in tool_executions:
            tool_names[tool.tool_name] = tool_names.get(tool.tool_name, 0) + 1

        return {
            "session_id": session_id,
            "thinking_blocks": {
                "total": len(thinking_blocks),
                "total_tokens": total_thinking_tokens,
                "by_type": block_types,
            },
            "tool_executions": {
                "total": len(tool_executions),
                "successful": successful_tools,
                "failed": failed_tools,
                "total_duration_ms": total_tool_duration,
                "by_name": tool_names,
            },
        }

    def create_session_export(
        self,
        session_id: str,
        format: str = "json",
        include_thinking: bool = True,
        include_tools: bool = True,
        include_messages: bool = True
    ) -> SessionExport:
        """
        Create an export record for a session.

        Args:
            session_id: Session identifier
            format: Export format (json, md, xml, jsonl)
            include_thinking: Include thinking blocks
            include_tools: Include tool executions
            include_messages: Include message relationships

        Returns:
            Created SessionExport record (content populated by exporter)
        """
        db_export = SessionExport(
            session_id=session_id,
            format=format,
            include_thinking=include_thinking,
            include_tools=include_tools,
            include_messages=include_messages,
            export_status="pending",
        )
        self.db.add(db_export)
        self.db.flush()
        return db_export

    def complete_export(
        self,
        export_id: int,
        content: str,
        file_path: Optional[str] = None
    ) -> SessionExport:
        """
        Complete an export with generated content.

        Args:
            export_id: ID of the SessionExport record
            content: Generated export content
            file_path: Optional file path where saved

        Returns:
            Updated SessionExport record
        """
        db_export = self.db.query(SessionExport).filter(
            SessionExport.id == export_id
        ).first()

        if db_export:
            db_export.content = content
            db_export.file_path = file_path
            db_export.export_status = "completed"
            db_export.completed_at = datetime.now(timezone.utc)
            self.db.flush()

        return db_export


# Convenience function for getting CoT prompts
def get_cot_forcing_prompt(structured: bool = False) -> str:
    """
    Get Chain-of-Thought forcing prompt for Ollama.

    Args:
        structured: Use structured 5-step format

    Returns:
        Prompt string to inject into system message
    """
    return OllamaThinkingExtractor.get_cot_prompt(structured)
