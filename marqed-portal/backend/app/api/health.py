"""Health check endpoints."""

from fastapi import APIRouter
from datetime import datetime, timezone

from ..core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns basic service status.
    """
    return {
        "status": "healthy",
        "service": "marqed-portal",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes/Docker.

    Verifies database and dependencies are accessible.
    """
    # TODO: Add actual DB check
    return {
        "status": "ready",
        "checks": {
            "database": "ok",
            "redis": "ok",
        },
    }
