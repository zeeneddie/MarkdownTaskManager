# Infrastructure Module
# Shared infrastructure components for all domains
#
# Contains:
# - Stability analysis (extracted for reuse)
# - Metrics collection
# - Cross-cutting concerns
#
# Architecture: docs/architecture/workflow-separation-plan.md
# Phase: Fase 21.5 (Week 145-146)

# Re-export stability services for shared access
# The actual implementation remains in services/stability/ for now
# This provides a clean import path for domains

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..services.stability.detector_service import ResourceLeakDetectorService
    from ..services.stability.types import (
        StabilityReport,
        LeakFinding,
        StabilityCategory,
        SeverityLevel,
    )

__all__ = [
    "get_stability_service",
    "StabilityReport",
    "LeakFinding",
    "StabilityCategory",
    "SeverityLevel",
]


def get_stability_service():
    """
    Factory function to get the stability detector service.
    Lazy import to avoid circular dependencies.
    """
    from ..services.stability.detector_service import ResourceLeakDetectorService
    return ResourceLeakDetectorService()
