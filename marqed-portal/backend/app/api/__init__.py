"""API routes for MarQed.ai Client Portal."""

from fastapi import APIRouter
from .auth import router as auth_router
from .tenants import router as tenants_router
from .users import router as users_router
from .projects import router as projects_router
from .health import router as health_router

# Main API router
api_router = APIRouter(prefix="/api/v1")

# Include all routers
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants_router, prefix="/tenants", tags=["tenants"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])

__all__ = ["api_router"]
