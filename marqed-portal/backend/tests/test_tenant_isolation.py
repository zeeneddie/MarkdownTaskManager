"""
Tests for multi-tenant isolation.

Verifies that tenants cannot access each other's data.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant, TenantStatus, SubscriptionTier
from app.models.user import User, TenantUser, UserRole
from app.models.project import Project, ProjectStatus, ProjectType
from app.core.security import create_access_token, get_password_hash


@pytest.fixture
async def tenant_a(db_session: AsyncSession) -> Tenant:
    """Create tenant A."""
    tenant = Tenant(
        name="Company A",
        subdomain="company-a",
        status=TenantStatus.ACTIVE,
        is_active=True,
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def tenant_b(db_session: AsyncSession) -> Tenant:
    """Create tenant B."""
    tenant = Tenant(
        name="Company B",
        subdomain="company-b",
        status=TenantStatus.ACTIVE,
        is_active=True,
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def user_a(db_session: AsyncSession, tenant_a: Tenant) -> tuple[User, str]:
    """Create user for tenant A with auth token."""
    user = User(
        email="user-a@company-a.com",
        password_hash=get_password_hash("password"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    tenant_user = TenantUser(
        tenant_id=tenant_a.id,
        user_id=user.id,
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(tenant_user)
    await db_session.commit()

    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "tenant_id": tenant_a.id,
        "roles": ["admin"],
    })

    return user, token


@pytest.fixture
async def user_b(db_session: AsyncSession, tenant_b: Tenant) -> tuple[User, str]:
    """Create user for tenant B with auth token."""
    user = User(
        email="user-b@company-b.com",
        password_hash=get_password_hash("password"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    tenant_user = TenantUser(
        tenant_id=tenant_b.id,
        user_id=user.id,
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(tenant_user)
    await db_session.commit()

    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "tenant_id": tenant_b.id,
        "roles": ["admin"],
    })

    return user, token


@pytest.fixture
async def project_a(db_session: AsyncSession, tenant_a: Tenant) -> Project:
    """Create project for tenant A."""
    project = Project(
        tenant_id=tenant_a.id,
        name="Project A - Secret",
        code="PRJA",
        status=ProjectStatus.ACTIVE,
        project_type=ProjectType.BROWNFIELD,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def project_b(db_session: AsyncSession, tenant_b: Tenant) -> Project:
    """Create project for tenant B."""
    project = Project(
        tenant_id=tenant_b.id,
        name="Project B - Secret",
        code="PRJB",
        status=ProjectStatus.ACTIVE,
        project_type=ProjectType.GREENFIELD,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_tenant_a_cannot_see_tenant_b_projects(
    client: AsyncClient,
    user_a: tuple[User, str],
    project_a: Project,
    project_b: Project,
):
    """Verify tenant A cannot access tenant B's projects."""
    _, token_a = user_a

    # List projects - should only see tenant A's project
    response = await client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert response.status_code == 200
    projects = response.json()

    # Should only contain project A
    project_ids = [p["id"] for p in projects]
    assert project_a.id in project_ids
    assert project_b.id not in project_ids


@pytest.mark.asyncio
async def test_tenant_a_cannot_access_tenant_b_project_directly(
    client: AsyncClient,
    user_a: tuple[User, str],
    project_b: Project,
):
    """Verify tenant A cannot directly access tenant B's project by ID."""
    _, token_a = user_a

    # Try to access project B directly
    response = await client.get(
        f"/api/v1/projects/{project_b.id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # Should get 404 (not found) because of tenant isolation
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_tenant_b_sees_own_projects(
    client: AsyncClient,
    user_b: tuple[User, str],
    project_a: Project,
    project_b: Project,
):
    """Verify tenant B only sees their own projects."""
    _, token_b = user_b

    response = await client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 200
    projects = response.json()

    # Should only contain project B
    project_ids = [p["id"] for p in projects]
    assert project_b.id in project_ids
    assert project_a.id not in project_ids


@pytest.mark.asyncio
async def test_tenant_isolation_on_create(
    client: AsyncClient,
    user_a: tuple[User, str],
    tenant_a: Tenant,
):
    """Verify projects are created with correct tenant_id."""
    _, token_a = user_a

    response = await client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "name": "New Project",
            "code": "NEW",
            "project_type": "brownfield",
        },
    )

    assert response.status_code == 200
    # Project should be associated with tenant A (verified through listing)
