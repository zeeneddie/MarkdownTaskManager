"""
Security utilities: JWT tokens, password hashing, authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from .config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer scheme
security = HTTPBearer()


class TokenData(BaseModel):
    """JWT token payload data."""

    sub: str  # User ID
    tenant_id: str  # Tenant ID
    email: Optional[str] = None
    roles: list[str] = []
    exp: Optional[datetime] = None


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data (should include 'sub' and 'tenant_id')
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt


def create_refresh_token(
    data: dict[str, Any],
) -> str:
    """Create a JWT refresh token with longer expiration."""
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode.update({"exp": expire, "type": "refresh"})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token.

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        user_id: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")

        if user_id is None or tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing required claims",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(
            sub=user_id,
            tenant_id=tenant_id,
            email=payload.get("email"),
            roles=payload.get("roles", []),
            exp=datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc),
        )

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """
    Dependency to get current authenticated user from JWT token.

    Usage:
        @router.get("/me")
        async def get_me(user: TokenData = Depends(get_current_user)):
            return {"user_id": user.sub, "tenant_id": user.tenant_id}
    """
    return decode_token(credentials.credentials)


async def get_current_tenant(
    user: TokenData = Depends(get_current_user),
) -> str:
    """
    Dependency to get current tenant ID from authenticated user.

    Usage:
        @router.get("/projects")
        async def get_projects(tenant_id: str = Depends(get_current_tenant)):
            ...
    """
    return user.tenant_id


def require_roles(*required_roles: str):
    """
    Dependency factory to require specific roles.

    Usage:
        @router.delete("/users/{id}")
        async def delete_user(
            user: TokenData = Depends(require_roles("admin"))
        ):
            ...
    """
    async def role_checker(
        user: TokenData = Depends(get_current_user),
    ) -> TokenData:
        if not any(role in user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {required_roles}",
            )
        return user

    return role_checker
