"""
Week 71: MCP Proxy Models

SQLAlchemy models for MCP server management, tool registry,
execution tracking, and token savings optimization.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class MCPServer(Base):
    """MCP Server configuration."""

    __tablename__ = "mcp_servers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    server_type = Column(String(50), nullable=False)  # stdio, http, docker
    command = Column(String(500))  # Command to start server
    args = Column(JSONB, default=list)  # Command arguments
    env_vars = Column(JSONB, default=dict)  # Environment variables
    docker_image = Column(String(200))  # Docker image if containerized
    docker_config = Column(JSONB, default=dict)  # Docker configuration
    security_level = Column(String(20), default="standard")  # standard, isolated, quarantine
    is_active = Column(Boolean, default=True)
    health_status = Column(String(20), default="unknown")  # healthy, unhealthy, unknown
    last_health_check = Column(DateTime)
    priority = Column(Integer, default=100)  # Lower = higher priority
    config = Column(JSONB, default=dict)  # Additional configuration
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    tools = relationship("MCPToolRegistry", back_populates="server", cascade="all, delete-orphan")
    executions = relationship("MCPToolExecution", back_populates="server", cascade="all, delete-orphan")
    savings = relationship("MCPTokenSavings", back_populates="server", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "server_type": self.server_type,
            "command": self.command,
            "args": self.args or [],
            "env_vars": self.env_vars or {},
            "docker_image": self.docker_image,
            "docker_config": self.docker_config or {},
            "security_level": self.security_level,
            "is_active": self.is_active,
            "health_status": self.health_status,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "priority": self.priority,
            "config": self.config or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tool_count": len(self.tools) if self.tools else 0
        }


class MCPToolRegistry(Base):
    """MCP Tool registry - available tools per server."""

    __tablename__ = "mcp_tool_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    server_id = Column(UUID(as_uuid=True), ForeignKey("mcp_servers.id", ondelete="CASCADE"), nullable=False)
    tool_name = Column(String(100), nullable=False)
    description = Column(Text)
    input_schema = Column(JSONB)  # JSON Schema for input
    category = Column(String(50))  # file, code, search, browser, etc.
    tags = Column(JSONB, default=list)  # Semantic tags for search
    embedding = Column(JSONB)  # Vector embedding for semantic search
    success_rate = Column(Float, default=1.0)  # Historical success rate
    avg_latency_ms = Column(Integer)  # Average execution time
    total_executions = Column(Integer, default=0)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    server = relationship("MCPServer", back_populates="tools")
    executions = relationship("MCPToolExecution", back_populates="tool", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('server_id', 'tool_name', name='uq_server_tool'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "server_id": str(self.server_id),
            "server_name": self.server.name if self.server else None,
            "tool_name": self.tool_name,
            "description": self.description,
            "input_schema": self.input_schema,
            "category": self.category,
            "tags": self.tags or [],
            "success_rate": self.success_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "total_executions": self.total_executions,
            "is_enabled": self.is_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class MCPToolExecution(Base):
    """MCP Tool execution history."""

    __tablename__ = "mcp_tool_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("mcp_tool_registry.id", ondelete="CASCADE"), nullable=False)
    server_id = Column(UUID(as_uuid=True), ForeignKey("mcp_servers.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(String(50))  # Which agent triggered this
    task_id = Column(UUID(as_uuid=True))  # Associated task
    input_params = Column(JSONB)  # Input parameters
    output_result = Column(JSONB)  # Output result
    input_tokens = Column(Integer)  # Token count for input
    output_tokens = Column(Integer)  # Token count for output
    tokens_saved = Column(Integer)  # Tokens saved via optimization
    latency_ms = Column(Integer)  # Execution time
    status = Column(String(20))  # success, failed, timeout
    error_message = Column(Text)
    was_cached = Column(Boolean, default=False)
    cache_key = Column(String(64))  # Hash for caching
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    tool = relationship("MCPToolRegistry", back_populates="executions")
    server = relationship("MCPServer", back_populates="executions")

    def to_dict(self):
        return {
            "id": str(self.id),
            "tool_id": str(self.tool_id),
            "tool_name": self.tool.tool_name if self.tool else None,
            "server_id": str(self.server_id),
            "server_name": self.server.name if self.server else None,
            "agent_id": self.agent_id,
            "task_id": str(self.task_id) if self.task_id else None,
            "input_params": self.input_params,
            "output_result": self.output_result,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "tokens_saved": self.tokens_saved,
            "latency_ms": self.latency_ms,
            "status": self.status,
            "error_message": self.error_message,
            "was_cached": self.was_cached,
            "cache_key": self.cache_key,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class MCPTokenSavings(Base):
    """Aggregated token savings per day/server/agent."""

    __tablename__ = "mcp_token_savings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    server_id = Column(UUID(as_uuid=True), ForeignKey("mcp_servers.id", ondelete="CASCADE"))
    agent_id = Column(String(50))
    total_executions = Column(Integer, default=0)
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_tokens_saved = Column(Integer, default=0)
    cache_hits = Column(Integer, default=0)
    cache_misses = Column(Integer, default=0)
    avg_latency_ms = Column(Integer)
    success_rate = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    server = relationship("MCPServer", back_populates="savings")

    __table_args__ = (
        UniqueConstraint('date', 'server_id', 'agent_id', name='uq_daily_savings'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "server_id": str(self.server_id) if self.server_id else None,
            "server_name": self.server.name if self.server else None,
            "agent_id": self.agent_id,
            "total_executions": self.total_executions,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens_saved": self.total_tokens_saved,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "avg_latency_ms": self.avg_latency_ms,
            "success_rate": self.success_rate,
            "savings_percentage": round(
                (self.total_tokens_saved / (self.total_input_tokens + self.total_output_tokens + self.total_tokens_saved)) * 100, 2
            ) if (self.total_input_tokens or self.total_output_tokens or self.total_tokens_saved) else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
