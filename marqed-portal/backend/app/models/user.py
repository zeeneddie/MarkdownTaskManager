"""
User models for authentication and authorization.

Supports multi-tenant users with role-based access control.
"""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING, List
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from enum import Enum

from ..core.database import Base
from .base import TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from .tenant import Tenant


class UserRole(str, Enum):
    """
    User roles within a tenant.

    Hierarchy: VIEWER < SUBMITTER < APPROVER < MANAGER < ADMIN
    """

    VIEWER = "viewer"  # Read-only access
    SUBMITTER = "submitter"  # Can create items
    APPROVER = "approver"  # Can approve FP estimates
    MANAGER = "manager"  # Can view reports, KPIs
    ADMIN = "admin"  # Full tenant administration


class User(Base, TimestampMixin):
    """
    Global user account.

    A user can belong to multiple tenants with different roles.
    """

    __tablename__ = "users"

    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)

    # Security
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(
        SQLEnum(
            "0", "1", "2", "3", "4", "5",
            name="failed_login_attempts_enum"
        ),
        default="0",
        nullable=False,
    )

    # Metadata
    preferences = Column(JSON, default=dict, nullable=False)

    # Relationships
    tenant_memberships: List["TenantUser"] = relationship(
        "TenantUser",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or self.email

    def record_login(self) -> None:
        """Record successful login."""
        self.last_login_at = datetime.now(timezone.utc)
        self.failed_login_attempts = "0"

    def record_failed_login(self) -> None:
        """Record failed login attempt."""
        current = int(self.failed_login_attempts or "0")
        if current < 5:
            self.failed_login_attempts = str(current + 1)

    @property
    def is_locked(self) -> bool:
        """Check if account is locked due to failed attempts."""
        return self.failed_login_attempts == "5"


class TenantUser(Base, TimestampMixin):
    """
    Association between User and Tenant with role.

    A user can have different roles in different tenants.
    """

    __tablename__ = "tenant_users"

    # Composite primary key alternative: use separate id
    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Foreign keys
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Role
    role = Column(
        SQLEnum(UserRole),
        default=UserRole.VIEWER,
        nullable=False,
    )

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Permissions (granular, per-epic/feature)
    epic_permissions = Column(JSON, default=dict, nullable=False)
    feature_permissions = Column(JSON, default=dict, nullable=False)

    # Invitation
    invited_by_id = Column(String(36), nullable=True)
    invited_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant: "Tenant" = relationship("Tenant", back_populates="users")
    user: "User" = relationship("User", back_populates="tenant_memberships")

    # Constraints
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_tenant_user"),
    )

    def __repr__(self) -> str:
        return f"<TenantUser {self.user_id} in {self.tenant_id} as {self.role}>"

    def has_permission(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
    ) -> bool:
        """
        Check if user has permission for an action.

        Args:
            action: 'view', 'create', 'edit', 'delete', 'approve'
            resource_type: 'epic', 'feature', 'story', 'project'
            resource_id: Optional specific resource ID

        Returns:
            True if user has permission
        """
        # Admins have all permissions
        if self.role == UserRole.ADMIN:
            return True

        # Role-based defaults
        role_permissions = {
            UserRole.VIEWER: ["view"],
            UserRole.SUBMITTER: ["view", "create", "edit"],
            UserRole.APPROVER: ["view", "create", "edit", "approve"],
            UserRole.MANAGER: ["view", "create", "edit", "approve", "report"],
        }

        base_perms = role_permissions.get(self.role, [])
        if action not in base_perms:
            return False

        # Check granular permissions if resource_id specified
        if resource_id:
            if resource_type == "epic":
                perms = self.epic_permissions.get(resource_id, {})
                if perms.get("blocked"):
                    return False
            elif resource_type == "feature":
                perms = self.feature_permissions.get(resource_id, {})
                if perms.get("blocked"):
                    return False

        return True
