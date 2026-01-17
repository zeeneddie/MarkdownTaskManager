"""
Kanban Retry Tracking Models

Week 58: Models for tracking Build ↔ Test lane transitions
and agent actions for learning and escalation.
"""
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class RetryResult(str, Enum):
    """Result of a retry attempt"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    ESCALATED = "escalated"


class KanbanRetryLog(Base):
    """
    Tracks retry attempts for Build ↔ Test transitions.

    When an item moves between Build and Test lanes multiple times,
    each transition is logged. After MAX_RETRIES (3), the item is
    escalated to Human Needed lane with a summary of all attempts.
    """
    __tablename__ = "kanban_retry_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    item_id = Column(String(100), nullable=False, index=True)
    item_type = Column(String(20), nullable=False)  # story, task, bug
    from_lane = Column(String(20), nullable=False)
    to_lane = Column(String(20), nullable=False)
    attempt = Column(Integer, nullable=False, default=1)
    result = Column(String(20), nullable=False, default="pending")
    agent_used = Column(String(50), nullable=True)
    analysis = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "item_id": self.item_id,
            "item_type": self.item_type,
            "from_lane": self.from_lane,
            "to_lane": self.to_lane,
            "attempt": self.attempt,
            "result": self.result,
            "agent_used": self.agent_used,
            "analysis": self.analysis,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class KanbanAgentAction(Base):
    """
    Tracks all agent actions performed on Kanban items.

    Used for:
    - Learning which agents work best for which item types
    - Debugging failed transitions
    - Performance metrics
    """
    __tablename__ = "kanban_agent_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    item_id = Column(String(100), nullable=False, index=True)
    item_type = Column(String(20), nullable=False)
    lane = Column(String(20), nullable=False, index=True)
    agent_name = Column(String(50), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    success = Column(Boolean, nullable=False, default=False)
    details = Column(JSONB, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "item_id": self.item_id,
            "item_type": self.item_type,
            "lane": self.lane,
            "agent_name": self.agent_name,
            "action": self.action,
            "success": self.success,
            "details": self.details,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
