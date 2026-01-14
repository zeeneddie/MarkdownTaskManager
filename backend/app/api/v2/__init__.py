# API v2 Module
# New decoupled API endpoints for Workflow Separation (Fase 21.5)
#
# Key differences from v1:
# - Migration uses analysis_id instead of brown_paper_session_id
# - Quality can run independently (standalone, integrated, scheduled)
# - All domains communicate via contracts
#
# Architecture: docs/architecture/workflow-separation-plan.md

from .migration import router as migration_router
from .quality import router as quality_router

__all__ = [
    "migration_router",
    "quality_router",
]
