"""
Base model mixins for common functionality.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, DateTime, String, ForeignKey, event
from sqlalchemy.orm import declared_attr
import uuid


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TenantMixin:
    """
    Mixin for multi-tenant models.

    Adds tenant_id column and ensures RLS compatibility.
    All models with this mixin are automatically filtered by tenant.
    """

    @declared_attr
    def tenant_id(cls) -> Column:
        return Column(
            String(36),
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())
