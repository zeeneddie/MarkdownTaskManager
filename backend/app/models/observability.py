"""
Observability Models - Agent Monitoring & Performance Tracking

Week 54: Provider Registry & Observability Foundation
"""

from datetime import datetime, date, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class LLMProvider(Base):
    """
    LLM Provider configuration and status.

    Stores configuration for all available LLM providers:
    - Ollama (local, free)
    - Codex (OpenAI CLI, deep analysis)
    - Claude (Anthropic CLI, balanced)
    """
    __tablename__ = "llm_providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100))
    provider_type = Column(String(30), nullable=False)  # ollama, codex, claude
    tier = Column(String(20), nullable=False)  # free, fast, balanced, deep
    model = Column(String(100), nullable=False)
    cost_input_per_m = Column(Numeric(10, 4), default=0)  # $ per million tokens
    cost_output_per_m = Column(Numeric(10, 4), default=0)
    is_local = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    config = Column(JSONB, default=dict)  # Provider-specific settings
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_llm_providers_type_tier', 'provider_type', 'tier'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "provider_type": self.provider_type,
            "tier": self.tier,
            "model": self.model,
            "cost_input_per_m": float(self.cost_input_per_m) if self.cost_input_per_m else 0,
            "cost_output_per_m": float(self.cost_output_per_m) if self.cost_output_per_m else 0,
            "is_local": self.is_local,
            "is_active": self.is_active,
            "config": self.config or {},
        }


class AgentAction(Base):
    """
    Log every agent action for monitoring and debugging.

    Captures:
    - What action was taken (generate, review, estimate, etc.)
    - Which provider/model was used
    - Input/output summaries
    - Performance metrics (duration, tokens, cost)
    - Success/failure status
    """
    __tablename__ = "agent_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(PGUUID(as_uuid=True), index=True)
    session_id = Column(PGUUID(as_uuid=True), index=True)
    message_id = Column(PGUUID(as_uuid=True), nullable=True)  # Week 61: CCTrace message tracking
    parent_message_id = Column(PGUUID(as_uuid=True), nullable=True)  # Week 61: Message hierarchy
    agent_id = Column(String(50), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)  # generate, review, estimate, etc.
    provider = Column(String(30))  # ollama, codex, claude
    model = Column(String(100))  # Specific model used
    input_summary = Column(Text)  # Truncated input for logging
    output_summary = Column(Text)  # Truncated output for logging
    decision_rationale = Column(Text)  # Why this action was taken
    token_input = Column(Integer, default=0)
    token_output = Column(Integer, default=0)
    token_cache_creation = Column(Integer, default=0)  # Week 61: Cache tokens created
    token_cache_read = Column(Integer, default=0)  # Week 61: Cache tokens read (savings)
    duration_ms = Column(Integer, default=0)
    cost_cents = Column(Numeric(10, 4), default=0)
    success = Column(Boolean, default=True)
    error = Column(Text)  # Error message if failed
    confidence_score = Column(Numeric(3, 2))  # 0.00 - 1.00
    extra_data = Column(JSONB, default=dict)  # Additional context
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index('ix_agent_actions_created_at_agent', 'created_at', 'agent_id'),
        Index('ix_agent_actions_provider', 'provider'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": str(self.task_id) if self.task_id else None,
            "session_id": str(self.session_id) if self.session_id else None,
            "message_id": str(self.message_id) if self.message_id else None,
            "parent_message_id": str(self.parent_message_id) if self.parent_message_id else None,
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "provider": self.provider,
            "model": self.model,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "decision_rationale": self.decision_rationale,
            "token_input": self.token_input,
            "token_output": self.token_output,
            "token_cache_creation": self.token_cache_creation or 0,
            "token_cache_read": self.token_cache_read or 0,
            "duration_ms": self.duration_ms,
            "cost_cents": float(self.cost_cents) if self.cost_cents else 0,
            "success": self.success,
            "error": self.error,
            "confidence_score": float(self.confidence_score) if self.confidence_score else None,
            "extra_data": self.extra_data or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DecisionTrace(Base):
    """
    Track decision points for debugging and analysis.

    Records every decision point in agent workflows:
    - Which options were considered
    - What was selected and why
    - The outcome of that decision
    """
    __tablename__ = "decision_traces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(PGUUID(as_uuid=True), index=True)
    session_id = Column(PGUUID(as_uuid=True), index=True)
    sequence_number = Column(Integer, nullable=False)  # Order within task
    agent_id = Column(String(50), nullable=False)
    decision_point = Column(String(100), nullable=False)  # e.g., "model_selection", "quality_gate"
    options = Column(JSONB)  # Available options considered
    selected_option = Column(String(100))  # What was chosen
    selection_rationale = Column(Text)  # Why this option
    outcome = Column(String(50))  # success, failure, skipped
    outcome_details = Column(JSONB)  # Additional outcome info
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_decision_traces_task_seq', 'task_id', 'sequence_number'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": str(self.task_id) if self.task_id else None,
            "session_id": str(self.session_id) if self.session_id else None,
            "sequence_number": self.sequence_number,
            "agent_id": self.agent_id,
            "decision_point": self.decision_point,
            "options": self.options,
            "selected_option": self.selected_option,
            "selection_rationale": self.selection_rationale,
            "outcome": self.outcome,
            "outcome_details": self.outcome_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AgentPerformanceDaily(Base):
    """
    Daily aggregated performance metrics per agent.

    Pre-computed daily summaries for:
    - Action counts (total, success, failed)
    - Token usage
    - Cost tracking
    - Average performance metrics
    """
    __tablename__ = "agent_performance_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), nullable=False)
    provider = Column(String(30))  # Optional: breakdown by provider
    date = Column(Date, nullable=False, index=True)
    total_actions = Column(Integer, default=0)
    successful_actions = Column(Integer, default=0)
    failed_actions = Column(Integer, default=0)
    avg_duration_ms = Column(Integer, default=0)
    total_tokens_input = Column(Integer, default=0)
    total_tokens_output = Column(Integer, default=0)
    total_cost_cents = Column(Numeric(10, 2), default=0)
    avg_confidence = Column(Numeric(3, 2))  # Average confidence score
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Note: date column already has index=True, no need for explicit Index

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "provider": self.provider,
            "date": self.date.isoformat() if self.date else None,
            "total_actions": self.total_actions,
            "successful_actions": self.successful_actions,
            "failed_actions": self.failed_actions,
            "success_rate": (
                self.successful_actions / self.total_actions * 100
                if self.total_actions > 0 else 0
            ),
            "avg_duration_ms": self.avg_duration_ms,
            "total_tokens_input": self.total_tokens_input,
            "total_tokens_output": self.total_tokens_output,
            "total_cost_cents": float(self.total_cost_cents) if self.total_cost_cents else 0,
            "avg_confidence": float(self.avg_confidence) if self.avg_confidence else None,
        }
