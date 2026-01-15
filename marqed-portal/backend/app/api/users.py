"""
User management API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.security import get_current_user, get_current_tenant, TokenData
from ..models.user import User, TenantUser, UserRole

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class UserProfileUpdate(BaseModel):
    """Update user profile."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserInvite(BaseModel):
    """Invite user to tenant."""

    email: EmailStr
    role: UserRole = UserRole.VIEWER


class TenantUserResponse(BaseModel):
    """User within tenant context."""

    id: str
    user_id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: UserRole
    is_active: bool


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/profile")
async def get_profile(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's profile."""
    result = await db.execute(
        select(User).where(User.id == current_user.sub)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "avatar_url": user.avatar_url,
        "preferences": user.preferences,
    }


@router.patch("/profile")
async def update_profile(
    request: UserProfileUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile."""
    result = await db.execute(
        select(User).where(User.id == current_user.sub)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()

    return {"message": "Profile updated"}


@router.get("/tenant", response_model=List[TenantUserResponse])
async def list_tenant_users(
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List all users in current tenant."""
    result = await db.execute(
        select(TenantUser, User)
        .join(User)
        .where(TenantUser.tenant_id == tenant_id)
    )
    rows = result.all()

    return [
        TenantUserResponse(
            id=tu.id,
            user_id=tu.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=tu.role,
            is_active=tu.is_active,
        )
        for tu, user in rows
    ]


@router.post("/tenant/invite")
async def invite_user(
    request: UserInvite,
    current_user: TokenData = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Invite a user to the current tenant.

    If user exists, adds to tenant. Otherwise creates pending invitation.
    """
    # Verify current user is admin or manager
    if not any(r in ["admin", "manager"] for r in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or manager role required",
        )

    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    if user:
        # Check if already in tenant
        result = await db.execute(
            select(TenantUser)
            .where(
                TenantUser.tenant_id == tenant_id,
                TenantUser.user_id == user.id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already in tenant",
            )

        # Add to tenant
        tenant_user = TenantUser(
            tenant_id=tenant_id,
            user_id=user.id,
            role=request.role,
            invited_by_id=current_user.sub,
            is_active=True,
        )
        db.add(tenant_user)
        await db.commit()

        return {"message": "User added to tenant", "user_id": user.id}

    else:
        # TODO: Send invitation email
        return {
            "message": "Invitation sent",
            "email": request.email,
            "pending": True,
        }


@router.patch("/tenant/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: UserRole,
    current_user: TokenData = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's role in the tenant."""
    # Verify current user is admin
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    # Find tenant user
    result = await db.execute(
        select(TenantUser)
        .where(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == user_id,
        )
    )
    tenant_user = result.scalar_one_or_none()

    if not tenant_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in tenant",
        )

    # Prevent demoting last admin
    if tenant_user.role == UserRole.ADMIN and role != UserRole.ADMIN:
        result = await db.execute(
            select(TenantUser)
            .where(
                TenantUser.tenant_id == tenant_id,
                TenantUser.role == UserRole.ADMIN,
                TenantUser.is_active == True,
            )
        )
        admins = result.scalars().all()

        if len(admins) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove last admin",
            )

    tenant_user.role = role
    await db.commit()

    return {"message": "Role updated", "new_role": role.value}
