"""
Tenant management API endpoints.

For tenant administration and configuration.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.security import get_current_user, require_roles, TokenData
from ..models.tenant import Tenant, TenantSettings, SubscriptionTier, TenantStatus
from ..models.user import TenantUser, UserRole

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class TenantCreate(BaseModel):
    """Request to create a new tenant."""

    name: str
    subdomain: str
    display_name: Optional[str] = None
    primary_email: Optional[EmailStr] = None
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    monthly_fp_allocation: int = 0


class TenantUpdate(BaseModel):
    """Request to update a tenant."""

    name: Optional[str] = None
    display_name: Optional[str] = None
    primary_email: Optional[EmailStr] = None
    billing_email: Optional[EmailStr] = None
    subscription_tier: Optional[SubscriptionTier] = None
    monthly_fp_allocation: Optional[int] = None
    fp_overage_allowed: Optional[bool] = None


class TenantResponse(BaseModel):
    """Tenant response model."""

    id: str
    name: str
    subdomain: str
    display_name: Optional[str]
    status: TenantStatus
    subscription_tier: SubscriptionTier
    monthly_fp_allocation: int
    fp_overage_allowed: bool
    is_active: bool

    class Config:
        from_attributes = True


class TenantDetailResponse(TenantResponse):
    """Detailed tenant response with settings."""

    primary_email: Optional[str]
    billing_email: Optional[str]
    user_count: int = 0
    project_count: int = 0
    settings: Optional[dict] = None


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("", response_model=List[TenantResponse])
async def list_tenants(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List tenants accessible to current user.

    Regular users see only their tenants.
    Superusers see all tenants.
    """
    # Get user's tenant memberships
    result = await db.execute(
        select(Tenant)
        .join(TenantUser)
        .where(
            TenantUser.user_id == current_user.sub,
            TenantUser.is_active == True,
        )
    )
    tenants = result.scalars().all()

    return [TenantResponse.model_validate(t) for t in tenants]


@router.get("/{tenant_id}", response_model=TenantDetailResponse)
async def get_tenant(
    tenant_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get tenant details.

    User must be a member of the tenant.
    """
    # Verify user has access to tenant
    result = await db.execute(
        select(TenantUser)
        .where(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == current_user.sub,
            TenantUser.is_active == True,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant",
        )

    # Get tenant with counts
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # Get counts
    user_count = len(tenant.users) if tenant.users else 0
    project_count = len(tenant.projects) if tenant.projects else 0

    # Get settings
    settings_dict = None
    if tenant.settings:
        settings_dict = {
            "primary_color": tenant.settings.primary_color,
            "secondary_color": tenant.settings.secondary_color,
            "features_enabled": tenant.settings.features_enabled,
        }

    return TenantDetailResponse(
        id=tenant.id,
        name=tenant.name,
        subdomain=tenant.subdomain,
        display_name=tenant.display_name,
        status=tenant.status,
        subscription_tier=tenant.subscription_tier,
        monthly_fp_allocation=tenant.monthly_fp_allocation,
        fp_overage_allowed=tenant.fp_overage_allowed,
        is_active=tenant.is_active,
        primary_email=tenant.primary_email,
        billing_email=tenant.billing_email,
        user_count=user_count,
        project_count=project_count,
        settings=settings_dict,
    )


@router.post("", response_model=TenantResponse)
async def create_tenant(
    request: TenantCreate,
    current_user: TokenData = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new tenant.

    Only admins can create tenants.
    """
    # Check subdomain is unique
    result = await db.execute(
        select(Tenant).where(Tenant.subdomain == request.subdomain)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subdomain already taken",
        )

    # Create tenant
    tenant = Tenant(
        name=request.name,
        subdomain=request.subdomain.lower(),
        display_name=request.display_name,
        primary_email=request.primary_email,
        subscription_tier=request.subscription_tier,
        monthly_fp_allocation=request.monthly_fp_allocation,
        status=TenantStatus.ACTIVE,
        is_active=True,
    )

    db.add(tenant)

    # Create default settings
    settings = TenantSettings(tenant_id=tenant.id)
    db.add(settings)

    # Add current user as admin
    tenant_user = TenantUser(
        tenant_id=tenant.id,
        user_id=current_user.sub,
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(tenant_user)

    await db.commit()
    await db.refresh(tenant)

    return TenantResponse.model_validate(tenant)


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    request: TenantUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update tenant settings.

    Only tenant admins can update.
    """
    # Verify user is admin of tenant
    result = await db.execute(
        select(TenantUser)
        .where(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == current_user.sub,
            TenantUser.role == UserRole.ADMIN,
            TenantUser.is_active == True,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Get tenant
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    await db.commit()
    await db.refresh(tenant)

    return TenantResponse.model_validate(tenant)


@router.get("/{tenant_id}/users")
async def list_tenant_users(
    tenant_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List users in a tenant.
    """
    # Verify user has access
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    result = await db.execute(
        select(TenantUser)
        .where(TenantUser.tenant_id == tenant_id)
    )
    users = result.scalars().all()

    return [
        {
            "id": u.id,
            "user_id": u.user_id,
            "role": u.role.value,
            "is_active": u.is_active,
        }
        for u in users
    ]
