"""
Tenant model for multi-tenant architecture.

Each tenant represents a customer organization with isolated data.
"""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Integer,
    Enum as SQLEnum,
    JSON,
    Text,
)
from sqlalchemy.orm import relationship
from enum import Enum

from ..core.database import Base
from .base import TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from .user import TenantUser
    from .project import Project


class SubscriptionTier(str, Enum):
    """Subscription tier levels."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant account status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    CANCELLED = "cancelled"


class Tenant(Base, TimestampMixin):
    """
    Tenant model representing a customer organization.

    Each tenant has:
    - Unique subdomain (e.g., hci.marqed.ai)
    - Subscription tier with FP allocation
    - Isolated data through RLS policies
    """

    __tablename__ = "tenants"

    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Identification
    name = Column(String(255), nullable=False)
    subdomain = Column(String(63), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)

    # Status
    status = Column(
        SQLEnum(TenantStatus),
        default=TenantStatus.PENDING,
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)

    # Subscription
    subscription_tier = Column(
        SQLEnum(SubscriptionTier),
        default=SubscriptionTier.FREE,
        nullable=False,
    )
    monthly_fp_allocation = Column(Integer, default=0, nullable=False)
    fp_overage_allowed = Column(Boolean, default=False, nullable=False)

    # Contact
    primary_email = Column(String(255), nullable=True)
    billing_email = Column(String(255), nullable=True)

    # Metadata
    logo_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict, nullable=False)

    # Timestamps
    activated_at = Column(DateTime(timezone=True), nullable=True)
    suspended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    users: list["TenantUser"] = relationship(
        "TenantUser",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    projects: list["Project"] = relationship(
        "Project",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    settings: Optional["TenantSettings"] = relationship(
        "TenantSettings",
        back_populates="tenant",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Tenant {self.subdomain} ({self.name})>"

    def activate(self) -> None:
        """Activate the tenant."""
        self.status = TenantStatus.ACTIVE
        self.is_active = True
        self.activated_at = datetime.now(timezone.utc)

    def suspend(self, reason: Optional[str] = None) -> None:
        """Suspend the tenant."""
        self.status = TenantStatus.SUSPENDED
        self.is_active = False
        self.suspended_at = datetime.now(timezone.utc)
        if reason:
            self.metadata["suspension_reason"] = reason


class TenantSettings(Base, TimestampMixin):
    """
    Tenant-specific settings and configuration.
    """

    __tablename__ = "tenant_settings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Branding
    primary_color = Column(String(7), default="#3B82F6", nullable=False)
    secondary_color = Column(String(7), default="#10B981", nullable=False)
    custom_css = Column(Text, nullable=True)

    # Features
    features_enabled = Column(JSON, default=dict, nullable=False)

    # Notifications
    email_notifications = Column(Boolean, default=True, nullable=False)
    slack_webhook_url = Column(String(500), nullable=True)

    # Integration
    main_backend_project_ids = Column(JSON, default=list, nullable=False)

    # SLA
    sla_response_hours = Column(Integer, default=24, nullable=False)
    sla_resolution_hours = Column(Integer, default=72, nullable=False)

    # Relationships
    tenant: "Tenant" = relationship("Tenant", back_populates="settings")

    def __repr__(self) -> str:
        return f"<TenantSettings for {self.tenant_id}>"
