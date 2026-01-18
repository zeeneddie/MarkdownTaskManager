"""
Unit tests for SQLAlchemy models.
"""

import pytest
from datetime import datetime, timezone

from app.models.tenant import Tenant, TenantStatus, SubscriptionTier
from app.models.user import User, UserRole
from app.models.project import Project, ProjectStatus, ProjectType


class TestTenantModel:
    """Tests for Tenant model."""

    def test_tenant_creation(self):
        """Test basic tenant creation."""
        tenant = Tenant(
            name="Test Company",
            subdomain="test-company",
            status=TenantStatus.ACTIVE,
        )

        assert tenant.name == "Test Company"
        assert tenant.subdomain == "test-company"
        assert tenant.status == TenantStatus.ACTIVE
        assert tenant.is_active is True

    def test_tenant_status_enum(self):
        """Test TenantStatus enum values."""
        assert TenantStatus.ACTIVE.value == "active"
        assert TenantStatus.SUSPENDED.value == "suspended"
        assert TenantStatus.PENDING.value == "pending"

    def test_subscription_tier_enum(self):
        """Test SubscriptionTier enum values."""
        assert SubscriptionTier.FREE.value == "free"
        assert SubscriptionTier.STARTER.value == "starter"
        assert SubscriptionTier.PROFESSIONAL.value == "professional"
        assert SubscriptionTier.ENTERPRISE.value == "enterprise"

    def test_tenant_default_values(self):
        """Test tenant default values."""
        tenant = Tenant(name="Test", subdomain="test")

        assert tenant.is_active is True
        assert tenant.status == TenantStatus.PENDING


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self):
        """Test basic user creation."""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User",
        )

        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.full_name == "Test User"
        assert user.is_active is True

    def test_user_role_enum(self):
        """Test UserRole enum values."""
        assert UserRole.VIEWER.value == "viewer"
        assert UserRole.SUBMITTER.value == "submitter"
        assert UserRole.APPROVER.value == "approver"
        assert UserRole.MANAGER.value == "manager"
        assert UserRole.ADMIN.value == "admin"


class TestProjectModel:
    """Tests for Project model."""

    def test_project_creation(self):
        """Test basic project creation."""
        project = Project(
            tenant_id="test-tenant-id",
            name="Test Project",
            code="TEST",
            project_type=ProjectType.BROWNFIELD,
        )

        assert project.name == "Test Project"
        assert project.code == "TEST"
        assert project.project_type == ProjectType.BROWNFIELD

    def test_project_status_enum(self):
        """Test ProjectStatus enum values."""
        assert ProjectStatus.DRAFT.value == "draft"
        assert ProjectStatus.ACTIVE.value == "active"
        assert ProjectStatus.ON_HOLD.value == "on_hold"
        assert ProjectStatus.COMPLETED.value == "completed"
        assert ProjectStatus.ARCHIVED.value == "archived"

    def test_project_type_enum(self):
        """Test ProjectType enum values."""
        assert ProjectType.BROWNFIELD.value == "brownfield"
        assert ProjectType.GREENFIELD.value == "greenfield"
        assert ProjectType.HYBRID.value == "hybrid"

    def test_project_default_status(self):
        """Test project default status."""
        project = Project(
            tenant_id="test-tenant-id",
            name="Test",
            code="T",
        )

        assert project.status == ProjectStatus.DRAFT
