"""
Authentication API endpoints.

Handles login, registration, token refresh, and password management.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    TokenResponse,
    get_current_user,
    TokenData,
)
from ..models.user import User, TenantUser, UserRole
from ..models.tenant import Tenant

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class LoginRequest(BaseModel):
    """Login request body."""

    email: EmailStr
    password: str
    tenant_subdomain: Optional[str] = None


class RegisterRequest(BaseModel):
    """Registration request body."""

    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tenant_subdomain: Optional[str] = None  # For joining existing tenant
    invite_code: Optional[str] = None


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class UserResponse(BaseModel):
    """User response model."""

    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    tenants: list[dict]

    class Config:
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    """Password change request."""

    current_password: str
    new_password: str


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return JWT tokens.

    If tenant_subdomain is provided, validates user has access to that tenant.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Check if account is locked
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is locked due to too many failed attempts",
        )

    # Verify password
    if not verify_password(request.password, user.password_hash):
        user.record_failed_login()
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Check user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Get tenant membership
    tenant_id = None
    roles = []

    if request.tenant_subdomain:
        # Validate user has access to specified tenant
        result = await db.execute(
            select(TenantUser)
            .join(Tenant)
            .where(
                TenantUser.user_id == user.id,
                Tenant.subdomain == request.tenant_subdomain,
                TenantUser.is_active == True,
            )
        )
        tenant_user = result.scalar_one_or_none()

        if not tenant_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No access to tenant: {request.tenant_subdomain}",
            )

        tenant_id = tenant_user.tenant_id
        roles = [tenant_user.role.value]
    else:
        # Get first active tenant membership
        result = await db.execute(
            select(TenantUser)
            .where(
                TenantUser.user_id == user.id,
                TenantUser.is_active == True,
            )
            .limit(1)
        )
        tenant_user = result.scalar_one_or_none()

        if tenant_user:
            tenant_id = tenant_user.tenant_id
            roles = [tenant_user.role.value]

    # Record successful login
    user.record_login()
    await db.commit()

    # Create tokens
    token_data = {
        "sub": user.id,
        "email": user.email,
        "tenant_id": tenant_id or "",
        "roles": roles,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60,  # 30 minutes
    )


@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.

    Optionally joins an existing tenant if subdomain/invite provided.
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=request.email,
        password_hash=get_password_hash(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        is_active=True,
    )

    db.add(user)
    await db.flush()

    # Handle tenant membership
    tenants = []
    if request.tenant_subdomain:
        result = await db.execute(
            select(Tenant).where(Tenant.subdomain == request.tenant_subdomain)
        )
        tenant = result.scalar_one_or_none()

        if tenant:
            # TODO: Validate invite code
            tenant_user = TenantUser(
                tenant_id=tenant.id,
                user_id=user.id,
                role=UserRole.VIEWER,  # Default role
                is_active=True,
                accepted_at=datetime.now(timezone.utc),
            )
            db.add(tenant_user)
            tenants.append({
                "id": tenant.id,
                "name": tenant.name,
                "subdomain": tenant.subdomain,
                "role": UserRole.VIEWER.value,
            })

    await db.commit()

    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        tenants=tenants,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    """
    try:
        token_data = decode_token(request.refresh_token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Verify user still exists and is active
    result = await db.execute(
        select(User).where(User.id == token_data.sub)
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new tokens
    new_token_data = {
        "sub": user.id,
        "email": user.email,
        "tenant_id": token_data.tenant_id,
        "roles": token_data.roles,
    }

    return TokenResponse(
        access_token=create_access_token(new_token_data),
        refresh_token=create_refresh_token(new_token_data),
        expires_in=30 * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current authenticated user info.
    """
    result = await db.execute(
        select(User).where(User.id == current_user.sub)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get tenant memberships
    result = await db.execute(
        select(TenantUser, Tenant)
        .join(Tenant)
        .where(TenantUser.user_id == user.id)
    )
    memberships = result.all()

    tenants = [
        {
            "id": tenant.id,
            "name": tenant.name,
            "subdomain": tenant.subdomain,
            "role": tu.role.value,
        }
        for tu, tenant in memberships
    ]

    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        tenants=tenants,
    )


@router.post("/password/change")
async def change_password(
    request: PasswordChangeRequest,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change current user's password.
    """
    result = await db.execute(
        select(User).where(User.id == current_user.sub)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Verify current password
    if not verify_password(request.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    user.password_hash = get_password_hash(request.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Password changed successfully"}
