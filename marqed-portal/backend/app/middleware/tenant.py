"""
Tenant middleware for multi-tenant isolation.

Extracts tenant from subdomain or header and sets context.
"""

import re
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..core.config import settings


# Paths that don't require tenant context
PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/auth/forgot-password",
}

# Pattern for extracting subdomain
SUBDOMAIN_PATTERN = re.compile(r"^([a-z0-9-]+)\.marqed\.ai$", re.IGNORECASE)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and validate tenant context.

    Tenant is determined from:
    1. X-Tenant-ID header (for API clients)
    2. Subdomain (for browser access)
    3. JWT token claims (for authenticated requests)
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request and set tenant context."""

        # Skip public paths
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Try to get tenant ID
        tenant_id = await self._extract_tenant_id(request)

        if tenant_id:
            # Store in request state for later use
            request.state.tenant_id = tenant_id
        else:
            # For protected paths, tenant is required
            if not request.url.path.startswith("/api/v1/public"):
                # Will be validated later by auth dependency
                request.state.tenant_id = None

        response = await call_next(request)
        return response

    async def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """
        Extract tenant ID from request.

        Priority:
        1. X-Tenant-ID header
        2. Subdomain
        3. None (will be extracted from JWT later)
        """
        # 1. Check header
        tenant_header = request.headers.get(settings.TENANT_HEADER_NAME)
        if tenant_header:
            return tenant_header

        # 2. Check subdomain
        host = request.headers.get("host", "")
        subdomain = self._extract_subdomain(host)
        if subdomain and subdomain != settings.DEFAULT_TENANT_SUBDOMAIN:
            # Subdomain is the tenant identifier
            # In production, this would lookup the tenant by subdomain
            return subdomain

        return None

    def _extract_subdomain(self, host: str) -> Optional[str]:
        """Extract subdomain from host header."""
        # Remove port if present
        host = host.split(":")[0]

        # Match pattern
        match = SUBDOMAIN_PATTERN.match(host)
        if match:
            return match.group(1).lower()

        # For localhost development, check for subdomain pattern
        if ".localhost" in host:
            parts = host.split(".")
            if len(parts) >= 2:
                return parts[0].lower()

        return None


def get_tenant_from_request(request: Request) -> Optional[str]:
    """
    Get tenant ID from request state.

    Usage in route handlers:
        @router.get("/items")
        async def get_items(request: Request):
            tenant_id = get_tenant_from_request(request)
            ...
    """
    return getattr(request.state, "tenant_id", None)


async def require_tenant(request: Request) -> str:
    """
    Dependency that requires tenant context.

    Raises HTTPException if no tenant found.

    Usage:
        @router.get("/items")
        async def get_items(tenant_id: str = Depends(require_tenant)):
            ...
    """
    tenant_id = get_tenant_from_request(request)

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required. Provide X-Tenant-ID header or use tenant subdomain.",
        )

    return tenant_id
