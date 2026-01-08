"""
Application Registry Models

Week 57: Database models for persistent application registration.

Stores:
- Applications (registered projects)
- Components (detected project parts)
- Stack Agents (assigned AI agents per stack)
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from app.models.green_paper import Base


class Application(Base):
    """
    Registered application/project in the platform.

    An application can be:
    - single-project: One standalone project
    - mono-repo: Multiple related projects
    - multi-repo: Distributed across repositories
    """
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    root_path = Column(String(1024), nullable=False)
    description = Column(Text, nullable=True)
    application_type = Column(String(50), default="single-project")  # single-project, mono-repo, multi-repo

    # Detected stacks (stored as JSON array)
    primary_stacks = Column(JSON, default=list)

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    last_scan_at = Column(DateTime, nullable=True)

    # Configuration
    doc_path = Column(String(1024), nullable=True)
    test_path = Column(String(1024), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    components = relationship("Component", back_populates="application", cascade="all, delete-orphan")
    stack_agents = relationship("StackAgent", back_populates="application", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary for API response."""
        components_by_type = {}
        for comp in self.components:
            comp_type = comp.component_type.lower()
            components_by_type[comp_type] = components_by_type.get(comp_type, 0) + 1

        agents_by_role = {}
        for agent in self.stack_agents:
            role = agent.role
            agents_by_role[role] = agents_by_role.get(role, 0) + 1

        return {
            "id": self.id,
            "name": self.name,
            "root_path": self.root_path,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "application_type": self.application_type,
            "primary_stacks": self.primary_stacks or [],
            "total_components": len(self.components),
            "components_by_type": components_by_type,
            "total_agents": len(self.stack_agents),
            "agents_by_role": agents_by_role,
        }


class Component(Base):
    """
    A component within an application.

    Components can be:
    - PROJECT: Main project/module
    - SERVICE: Backend service
    - LIBRARY: Shared library
    - FRONTEND: UI component
    - DATABASE: Database schema/migrations
    """
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)

    name = Column(String(255), nullable=False)
    path = Column(String(1024), nullable=False)
    component_type = Column(String(50), nullable=False)  # PROJECT, SERVICE, LIBRARY, FRONTEND, DATABASE

    # Detected stacks for this component
    stacks = Column(JSON, default=list)

    # File statistics
    file_count = Column(Integer, default=0)
    line_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    last_scan_at = Column(DateTime, nullable=True)

    # Relationships
    application = relationship("Application", back_populates="components")

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "name": self.name,
            "path": self.path,
            "component_type": self.component_type,
            "stacks": self.stacks or [],
            "file_count": self.file_count,
            "line_count": self.line_count,
        }


class StackAgent(Base):
    """
    An AI agent assigned to work on a specific stack within an application.

    Each stack (python, javascript, etc.) can have multiple specialized agents:
    - BackendDev: Implements backend features
    - CodeReviewer: Reviews code quality
    - SecurityAuditor: Checks for vulnerabilities
    - Tester: Writes and runs tests
    """
    __tablename__ = "stack_agents"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)

    stack = Column(String(50), nullable=False)  # python, javascript, go, rust, etc.
    role = Column(String(50), nullable=False)   # BackendDev, CodeReviewer, SecurityAuditor, Tester

    # Agent configuration
    model_preference = Column(String(100), nullable=True)  # qwen2.5-coder:7b, claude/sonnet, etc.
    prompt_additions = Column(Text, nullable=True)
    capabilities = Column(JSON, default=list)

    # Performance tracking
    tasks_completed = Column(Integer, default=0)
    success_rate = Column(Integer, default=0)  # Percentage 0-100

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    last_active_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    application = relationship("Application", back_populates="stack_agents")

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "stack": self.stack,
            "role": self.role,
            "model_preference": self.model_preference,
            "capabilities": self.capabilities or [],
            "tasks_completed": self.tasks_completed,
            "success_rate": self.success_rate,
            "is_active": self.is_active,
        }
