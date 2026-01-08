"""
Migration Enhanced API - Fase 21 (Week 130)

10 endpoints for 7-phase migration execution workflow.

Endpoints:
- POST /api/migration/start - Start migration from Brown Paper session
- GET  /api/migration/{session_id} - Get migration status
- POST /api/migration/{session_id}/phase/{n}/start - Start phase N
- GET  /api/migration/{session_id}/phase/{n}/status - Get phase N status
- GET  /api/migration/{session_id}/report - Full migration report
- GET  /api/migration/{session_id}/report/testing - Test report
- GET  /api/migration/{session_id}/report/validation - Validation report
- POST /api/migration/{session_id}/phase/7/staging - Deploy to staging
- POST /api/migration/{session_id}/phase/7/production - Deploy to production
- POST /api/migration/{session_id}/phase/7/rollback - Rollback deployment
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, Optional
from pydantic import BaseModel

from app.database import get_db
from app.services.migration_enhanced_service import MigrationEnhancedService
from app.models.migration_enhanced import (
    MigrationEnhancedRequest,
    TargetTechnology,
    TargetDatabase,
    MigrationStrategy,
    DeploymentStrategy,
    TestStrategy,
)

router = APIRouter(prefix="/api/migration", tags=["Migration Enhanced"])


# =============================================================================
# Request/Response Models
# =============================================================================

class StartMigrationRequest(BaseModel):
    """Request to start a migration."""
    brown_paper_session_id: str
    target_technology: str = "dotnet8"
    target_database: str = "postgresql"
    migration_strategy: str = "strangler_fig"
    deployment_strategy: str = "blue_green"
    team_size: int = 3
    parallel_execution: bool = True
    test_strategy: str = "auto"
    test_coverage_target: float = 0.80
    performance_tolerance: float = 1.10


class PhaseStartRequest(BaseModel):
    """Request to start a specific phase."""
    force: bool = False  # Force start even if prerequisites not met
    config: Optional[Dict[str, Any]] = None


class DeploymentRequest(BaseModel):
    """Request for deployment operations."""
    target: str = "staging"  # staging or production


# =============================================================================
# Session Management Endpoints
# =============================================================================

@router.post("/start")
async def start_migration(
    request: StartMigrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new migration execution from Brown Paper Enhanced session.

    Requires a completed Brown Paper analysis as input.
    Returns session_id for tracking the migration.
    """
    service = MigrationEnhancedService(db)

    # Convert to dataclass
    migration_request = MigrationEnhancedRequest(
        brown_paper_session_id=request.brown_paper_session_id,
        target_technology=TargetTechnology(request.target_technology),
        target_database=TargetDatabase(request.target_database),
        migration_strategy=MigrationStrategy(request.migration_strategy),
        deployment_strategy=DeploymentStrategy(request.deployment_strategy),
        team_size=request.team_size,
        parallel_execution=request.parallel_execution,
        test_strategy=TestStrategy(request.test_strategy),
        test_coverage_target=request.test_coverage_target,
        performance_tolerance=request.performance_tolerance,
    )

    response = await service.start_migration(migration_request)

    return {
        "session_id": response.session_id,
        "status": response.status.value,
        "message": f"Migration started. Use session_id to track progress.",
        "next_step": "POST /api/migration/{session_id}/phase/1/start"
    }


@router.get("/{session_id}")
async def get_migration_status(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current migration status.

    Returns progress, phases completed, and current phase.
    """
    service = MigrationEnhancedService(db)
    response = await service.get_status(session_id)

    if not response:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": response.session_id,
        "status": response.status.value,
        "current_phase": response.current_phase.value if response.current_phase else None,
        "phases_completed": response.phases_completed,
        "progress_percent": response.progress_percent,
        "metrics": {
            "components_migrated": response.components_migrated,
            "tables_migrated": response.tables_migrated,
            "tests_passing": response.tests_passing,
            "test_coverage": response.test_coverage,
        },
        "workspace_url": response.workspace_url,
        "total_duration_ms": response.total_duration_ms,
    }


# =============================================================================
# Phase Control Endpoints
# =============================================================================

@router.post("/{session_id}/phase/{phase_number}/start")
async def start_phase(
    session_id: str,
    phase_number: int,
    request: PhaseStartRequest = PhaseStartRequest(),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a specific phase of the migration.

    Phases:
    1. Preparation - Setup environment and load Brown Paper data
    2. Code Transformation - Convert legacy code to target stack
    3. Data Migration - Migrate database schema and data
    4. Testing - Execute/generate tests and measure coverage
    5. Validation (Gate) - Functional equivalence, data integrity, security
    6. Acceptance - Business rules, stakeholder sign-off, GO/NO-GO
    7. Deployment - Deploy to staging/production with rollback

    Phases 2, 3, 4 can run in parallel after Phase 1 completes.
    Phase 5 requires Phases 2, 3, 4 to complete (gate check).
    """
    if phase_number < 1 or phase_number > 7:
        raise HTTPException(status_code=400, detail="Phase must be between 1 and 7")

    service = MigrationEnhancedService(db)

    phase_methods = {
        1: service.run_preparation_phase,
        2: service.run_code_transformation_phase,
        3: service.run_data_migration_phase,
        4: service.run_testing_phase,
        5: service.run_validation_phase,
        6: service.run_acceptance_phase,
        7: lambda sid: service.run_deployment_phase(sid, "staging"),
    }

    result = await phase_methods[phase_number](session_id)

    return {
        "session_id": session_id,
        "phase": phase_number,
        "success": result.success,
        "duration_ms": result.duration_ms,
        "errors": result.errors,
        "result": result.__dict__,
    }


@router.get("/{session_id}/phase/{phase_number}/status")
async def get_phase_status(
    session_id: str,
    phase_number: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get status of a specific phase.
    """
    if phase_number < 1 or phase_number > 7:
        raise HTTPException(status_code=400, detail="Phase must be between 1 and 7")

    service = MigrationEnhancedService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    phase_names = [
        "Preparation",
        "Code Transformation",
        "Data Migration",
        "Testing",
        "Validation",
        "Acceptance",
        "Deployment",
    ]

    status = getattr(session, f"phase_{phase_number}_status")
    result = getattr(session, f"phase_{phase_number}_result")

    return {
        "session_id": session_id,
        "phase": phase_number,
        "name": phase_names[phase_number - 1],
        "status": status.value,
        "result": result.__dict__ if result else None,
    }


# =============================================================================
# Reporting Endpoints
# =============================================================================

@router.get("/{session_id}/report")
async def get_full_report(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete migration report.

    Includes all phases, timing, configuration, and errors.
    """
    service = MigrationEnhancedService(db)
    report = await service.get_full_report(session_id)

    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])

    return report


@router.get("/{session_id}/report/testing")
async def get_testing_report(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get Phase 4 testing report.

    Includes test strategy decision, coverage, and breakdown.
    """
    service = MigrationEnhancedService(db)
    report = await service.get_testing_report(session_id)

    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])

    return report


@router.get("/{session_id}/report/validation")
async def get_validation_report(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get Phase 5 validation report.

    Includes functional equivalence, data integrity, performance, security.
    """
    service = MigrationEnhancedService(db)
    report = await service.get_validation_report(session_id)

    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])

    return report


# =============================================================================
# Deployment Endpoints
# =============================================================================

@router.post("/{session_id}/phase/7/staging")
async def deploy_to_staging(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Deploy to staging environment.

    Runs smoke tests and prepares rollback.
    """
    service = MigrationEnhancedService(db)
    result = await service.run_deployment_phase(session_id, "staging")

    if not result.success:
        raise HTTPException(status_code=400, detail=result.errors)

    return {
        "session_id": session_id,
        "target": "staging",
        "success": result.success,
        "staging_deployed": result.staging_deployed,
        "smoke_tests_passed": result.staging_smoke_tests_passed,
        "rollback_ready": result.rollback_ready,
        "next_step": "POST /api/migration/{session_id}/phase/7/production"
    }


@router.post("/{session_id}/phase/7/production")
async def deploy_to_production(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Deploy to production environment.

    Requires successful staging deployment.
    """
    service = MigrationEnhancedService(db)
    result = await service.run_deployment_phase(session_id, "production")

    if not result.success:
        raise HTTPException(status_code=400, detail=result.errors)

    return {
        "session_id": session_id,
        "target": "production",
        "success": result.success,
        "production_deployed": result.production_deployed,
        "smoke_tests_passed": result.production_smoke_tests_passed,
        "error_rate": result.error_rate,
        "rollback_available": "POST /api/migration/{session_id}/phase/7/rollback"
    }


@router.post("/{session_id}/phase/7/rollback")
async def rollback_deployment(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Rollback to legacy system.

    Only available after deployment with rollback_ready=True.
    """
    service = MigrationEnhancedService(db)
    result = await service.rollback(session_id)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.errors)

    return {
        "session_id": session_id,
        "rollback_executed": True,
        "legacy_standby": result.legacy_standby,
        "message": "Rolled back to legacy system. New system deactivated."
    }
