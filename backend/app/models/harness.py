"""
Harness Framework Models

SQLAlchemy models for the Agent Harness Framework:
- ContextSnapshot: Immutable context versioning
- ConstraintAuditLog: Compliance audit trail
- AgentSystemContext: Persisted agent contexts
- ContextActionLink: Context-to-action linking
- HarnessConfig: Runtime configuration
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class ContextSnapshot(Base):
    """
    Immutable snapshot of agent context at a point in time.

    Used for:
    - Version tracking
    - Audit trail
    - Reproducibility
    - Debugging agent decisions
    """
    __tablename__ = "context_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_hash = Column(String(64), nullable=False, index=True)
    agent_id = Column(String(50), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())

    # Context layers (stored as JSON)
    system_context = Column(JSONB, nullable=True)
    task_context = Column(JSONB, nullable=True)
    memory_context = Column(JSONB, nullable=True)

    token_count = Column(Integer, nullable=False, default=0)
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey('context_snapshots.id', ondelete='SET NULL'), nullable=True)
    extra_metadata = Column(JSONB, nullable=True, default={})
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())

    # Self-referential relationship for version chain
    parent = relationship("ContextSnapshot", remote_side=[id], backref="children")

    # Links to actions
    action_links = relationship("ContextActionLink", back_populates="snapshot", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_context_snapshots_session_time', 'session_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<ContextSnapshot {self.id} agent={self.agent_id} hash={self.content_hash[:8]}>"


class ConstraintAuditLog(Base):
    """
    Audit log entry for constraint checks.

    Records all constraint evaluations for compliance and debugging.
    """
    __tablename__ = "constraint_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_id = Column(String(20), nullable=False, index=True)
    agent_id = Column(String(50), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)
    action_params = Column(JSONB, nullable=True)

    # Result
    result = Column(String(20), nullable=False)  # ALLOWED, DENIED, APPROVAL_REQUIRED
    severity = Column(String(20), nullable=False)  # BLOCK, WARN, AUDIT, APPROVE
    reason = Column(Text, nullable=True)
    matched_rules = Column(JSONB, nullable=True, default=[])

    # Context at time of check
    context = Column(JSONB, nullable=True)

    # Approval tracking
    requires_approval = Column(Boolean, nullable=False, default=False)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    session_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())

    __table_args__ = (
        Index('idx_audit_log_agent_time', 'agent_id', 'created_at'),
        Index('idx_audit_log_result', 'result', 'created_at'),
    )

    def __repr__(self):
        return f"<ConstraintAuditLog {self.audit_id} agent={self.agent_id} result={self.result}>"


class AgentSystemContext(Base):
    """
    Persisted system context for an agent.

    Contains the static role, rules, and ethics that define agent behavior.
    """
    __tablename__ = "agent_system_contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(50), nullable=False, unique=True)
    role = Column(String(100), nullable=False)
    capabilities = Column(JSONB, nullable=False, default=[])
    rules = Column(JSONB, nullable=False, default=[])
    ethics = Column(JSONB, nullable=False, default=[])
    llm_model = Column(String(100), nullable=True)
    extra_config = Column(JSONB, nullable=True, default={})
    token_count = Column(Integer, nullable=False, default=0)
    version = Column(Integer, nullable=False, default=1)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    __table_args__ = (
        Index('idx_agent_contexts_active', 'active', 'agent_id'),
    )

    def __repr__(self):
        return f"<AgentSystemContext {self.agent_id} role={self.role}>"


class ContextActionLink(Base):
    """
    Links a context snapshot to an agent action.

    Enables:
    - Audit: "What context did the agent have?"
    - Reproducibility: "Replay with same context"
    - Debugging: "Why did agent do X?"
    """
    __tablename__ = "context_action_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    context_snapshot_id = Column(UUID(as_uuid=True), ForeignKey('context_snapshots.id', ondelete='CASCADE'), nullable=False)
    action_id = Column(String(100), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())

    # Relationship
    snapshot = relationship("ContextSnapshot", back_populates="action_links")

    __table_args__ = (
        Index('idx_context_action_snapshot', 'context_snapshot_id'),
    )

    def __repr__(self):
        return f"<ContextActionLink snapshot={self.context_snapshot_id} action={self.action_id}>"


class HarnessConfig(Base):
    """
    Runtime configuration for harness modules.

    Stores YAML-like configurations in the database for:
    - Constraint rules
    - Context templates
    - Tool permissions
    - Versioning settings
    """
    __tablename__ = "harness_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_type = Column(String(50), nullable=False)  # constraints, context, tools, versioning
    config_name = Column(String(100), nullable=False)
    config_data = Column(JSONB, nullable=False, default={})
    description = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    __table_args__ = (
        Index('idx_harness_config_type_active', 'config_type', 'active'),
    )

    def __repr__(self):
        return f"<HarnessConfig {self.config_type}:{self.config_name}>"
