"""
Customer Model

Week 143 - Fase 28: Customer/Project/Application Hierarchy

Customers own Projects, which can be linked to multiple Applications.
This enables multi-tenant support and proper organizational structure.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Customer(Base):
    """
    Customer entity - top of the hierarchy.

    Hierarchy: Customer → Project → Application

    A customer represents an organization or individual that owns
    one or more projects in the platform.
    """
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Basic info
    name = Column(String(255), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # Contact info
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True, index=True)
    contact_phone = Column(String(50), nullable=True)

    # Billing/Tier info
    tier = Column(String(20), nullable=False, default='FREE')  # FREE, BASIC, STANDARD, PROFESSIONAL, PREMIUM
    billing_email = Column(String(255), nullable=True)

    # External references
    external_id = Column(String(100), nullable=True, index=True)  # CRM, ERP reference

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projects = relationship("Project", back_populates="customer", cascade="all, delete-orphan")
    bmad_sessions = relationship("BMADSession", back_populates="customer")

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', tier='{self.tier}')>"

    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "tier": self.tier,
            "billing_email": self.billing_email,
            "external_id": self.external_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "project_count": len(self.projects) if self.projects else 0,
        }


class ProjectApplication(Base):
    """
    Many-to-Many link table between Project and Application.

    A Project can have multiple Applications (e.g., frontend, backend, mobile).
    An Application can belong to multiple Projects (shared libraries, services).
    """
    __tablename__ = "project_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=False, index=True)
    application_id = Column(Integer, nullable=False, index=True)

    # Role of this application in the project
    role = Column(String(50), nullable=True)  # primary, dependency, shared, integration

    # Impact tracking for kanban items
    impact_level = Column(String(20), nullable=True)  # high, medium, low

    # Timestamps
    linked_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<ProjectApplication(project_id={self.project_id}, application_id={self.application_id}, role='{self.role}')>"
