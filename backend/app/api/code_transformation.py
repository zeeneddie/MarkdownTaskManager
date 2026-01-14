"""
Week 131 Transformation API Routes

Provides REST endpoints for:
- Code transformation (VB.NET → C#, VB.NET → Python, T-SQL → PL/pgSQL)
- Database migration execution
- Migration progress tracking

Author: Claude Code (Week 131)
Date: 2026-01-01
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
import logging

from app.services.code_transformation_service import (
    CodeTransformationService,
    TransformationRequest,
    TransformationDirection
)
from app.services.database_migration_executor_service import (
    DatabaseMigrationExecutorService,
    DatabaseConnection,
    DatabaseType,
    MigrationConfig,
    MigrationPhase,
    MigrationStatus
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/week131", tags=["Week 131 - Transformation"])

# Initialize services
code_transformation_service = CodeTransformationService()
db_migration_service = DatabaseMigrationExecutorService()


# ============================================
# Request/Response Models
# ============================================

class TransformationType(str, Enum):
    VBNET_TO_CSHARP = "vbnet_to_csharp"
    VBNET_TO_PYTHON = "vbnet_to_python"
    TSQL_TO_PLPGSQL = "tsql_to_plpgsql"


class TransformFileRequest(BaseModel):
    file_path: str = Field(..., description="Path to file to transform")
    transformation_type: TransformationType
    output_path: Optional[str] = Field(None, description="Output path (default: same as input with new extension)")
    dry_run: bool = Field(True, description="If true, show diff without writing")
    create_backup: bool = Field(True, description="Create backup before transformation")


class TransformDirectoryRequest(BaseModel):
    directory_path: str = Field(..., description="Path to directory")
    transformation_type: TransformationType
    output_directory: Optional[str] = Field(None, description="Output directory")
    file_patterns: List[str] = Field(default=["*.vb", "*.sql"], description="File patterns to match")
    recursive: bool = Field(True, description="Process subdirectories")
    dry_run: bool = Field(True, description="If true, show diff without writing")


class DatabaseConnectionRequest(BaseModel):
    db_type: str = Field(..., description="Database type: oracle, sqlserver, postgresql, mysql")
    host: str
    port: int
    database: str
    username: str
    password: str
    db_schema: Optional[str] = Field(None, description="Database schema (renamed from 'schema' to avoid Pydantic conflict)")


class StartMigrationRequest(BaseModel):
    source: DatabaseConnectionRequest
    target: DatabaseConnectionRequest
    brown_paper_session_id: Optional[str] = Field(None, description="Link to Brown Paper analysis session")
    dry_run: bool = Field(True, description="Simulate migration without making changes")
    batch_size: int = Field(10000, description="Rows per batch")
    parallel_tables: int = Field(4, description="Tables to migrate in parallel")
    create_backup: bool = Field(True, description="Backup target before migration")
    include_tables: List[str] = Field(default=[], description="Tables to include (empty = all)")
    exclude_tables: List[str] = Field(default=[], description="Tables to exclude")


class TransformationResponse(BaseModel):
    success: bool
    files_processed: int
    files_transformed: int
    total_lines_changed: int
    patterns_applied: int
    diff_preview: Optional[str] = None
    errors: List[str] = []
    warnings: List[str] = []


class MigrationResponse(BaseModel):
    success: bool
    session_id: str
    current_phase: str
    overall_progress: float
    tables_completed: int
    rows_migrated: int
    duration_seconds: float
    errors: List[str] = []


# ============================================
# Code Transformation Endpoints
# ============================================

@router.post("/transform/file", response_model=TransformationResponse)
async def transform_file(request: TransformFileRequest):
    """
    Transform a single code file.

    Supports:
    - VB.NET → C# conversion
    - VB.NET → Python conversion
    - T-SQL → PL/pgSQL conversion
    """
    try:
        # Map API transformation type to service direction
        direction_map = {
            TransformationType.VBNET_TO_CSHARP: TransformationDirection.VBNET_TO_CSHARP,
            TransformationType.VBNET_TO_PYTHON: TransformationDirection.VBNET_TO_PYTHON,
            TransformationType.TSQL_TO_PLPGSQL: TransformationDirection.TSQL_TO_PLPGSQL,
        }

        # Create service request
        service_request = TransformationRequest(
            source_path=request.file_path,
            direction=direction_map[request.transformation_type],
            target_path=request.output_path,
            dry_run=request.dry_run,
            generate_backup=request.create_backup
        )

        result = await code_transformation_service.transform_file(service_request)

        return TransformationResponse(
            success=result.success,
            files_processed=1,
            files_transformed=1 if result.success else 0,
            total_lines_changed=result.lines_changed,
            patterns_applied=sum(result.patterns_applied.values()),
            diff_preview=result.diff,
            errors=result.errors,
            warnings=result.warnings
        )
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transform/directory", response_model=TransformationResponse)
async def transform_directory(request: TransformDirectoryRequest):
    """
    Transform all matching files in a directory.

    Processes files matching the specified patterns and applies
    the selected transformation type to each.
    """
    try:
        # Map API transformation type to service direction
        direction_map = {
            TransformationType.VBNET_TO_CSHARP: TransformationDirection.VBNET_TO_CSHARP,
            TransformationType.VBNET_TO_PYTHON: TransformationDirection.VBNET_TO_PYTHON,
            TransformationType.TSQL_TO_PLPGSQL: TransformationDirection.TSQL_TO_PLPGSQL,
        }

        # Build glob pattern from file patterns
        glob_pattern = request.file_patterns[0] if request.file_patterns else "**/*"
        if request.recursive and not glob_pattern.startswith("**/"):
            glob_pattern = "**/" + glob_pattern

        results = await code_transformation_service.transform_directory(
            directory=request.directory_path,
            direction=direction_map[request.transformation_type],
            glob=glob_pattern,
            dry_run=request.dry_run
        )

        # Aggregate results
        total_lines = sum(r.lines_changed for r in results)
        total_patterns = sum(sum(r.patterns_applied.values()) for r in results)
        all_errors = [e for r in results for e in r.errors]
        all_warnings = [w for r in results for w in r.warnings]
        successful = sum(1 for r in results if r.success)

        return TransformationResponse(
            success=len(all_errors) == 0,
            files_processed=len(results),
            files_transformed=successful,
            total_lines_changed=total_lines,
            patterns_applied=total_patterns,
            errors=all_errors,
            warnings=all_warnings
        )
    except Exception as e:
        logger.error(f"Directory transformation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transform/rules")
async def get_transformation_rules():
    """Get available transformation rules by type."""
    try:
        rules = code_transformation_service.get_available_rules() if hasattr(code_transformation_service, 'get_available_rules') else {}
        return {
            "vbnet_to_csharp": rules.get("vbnet_to_csharp", []),
            "vbnet_to_python": rules.get("vbnet_to_python", []),
            "tsql_to_plpgsql": rules.get("tsql_to_plpgsql", [])
        }
    except Exception as e:
        logger.error(f"Failed to get rules: {e}")
        return {"vbnet_to_csharp": [], "vbnet_to_python": [], "tsql_to_plpgsql": []}


@router.post("/transform/rollback/{file_path:path}")
async def rollback_transformation(file_path: str):
    """Rollback a file to its backup version."""
    try:
        success = await code_transformation_service.rollback_file(file_path)
        return {"success": success, "file_path": file_path}
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Database Migration Endpoints
# ============================================

@router.post("/migration/start", response_model=MigrationResponse)
async def start_migration(request: StartMigrationRequest, background_tasks: BackgroundTasks):
    """
    Start a new database migration.

    The migration runs in the background and progress can be tracked
    via the /migration/{session_id} endpoint.
    """
    try:
        # Convert request to config
        source_conn = DatabaseConnection(
            db_type=DatabaseType(request.source.db_type),
            host=request.source.host,
            port=request.source.port,
            database=request.source.database,
            username=request.source.username,
            password=request.source.password,
            schema=request.source.db_schema
        )

        target_conn = DatabaseConnection(
            db_type=DatabaseType(request.target.db_type),
            host=request.target.host,
            port=request.target.port,
            database=request.target.database,
            username=request.target.username,
            password=request.target.password,
            schema=request.target.db_schema
        )

        config = MigrationConfig(
            source=source_conn,
            target=target_conn,
            dry_run=request.dry_run,
            batch_size=request.batch_size,
            parallel_tables=request.parallel_tables,
            create_backup=request.create_backup,
            include_tables=request.include_tables,
            exclude_tables=request.exclude_tables
        )

        # Start migration
        result = await db_migration_service.start_migration(config)

        return MigrationResponse(
            success=result.success,
            session_id=result.session_id,
            current_phase=result.progress.current_phase.value,
            overall_progress=result.progress.overall_progress,
            tables_completed=result.progress.tables_completed,
            rows_migrated=result.progress.rows_migrated,
            duration_seconds=result.progress.duration_seconds,
            errors=result.progress.errors[:10]
        )
    except Exception as e:
        logger.error(f"Migration start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/migration/{session_id}", response_model=MigrationResponse)
async def get_migration_status(session_id: str):
    """Get current status of a migration session."""
    progress = db_migration_service.get_progress(session_id)
    if not progress:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return MigrationResponse(
        success=len(progress.errors) == 0,
        session_id=session_id,
        current_phase=progress.current_phase.value,
        overall_progress=progress.overall_progress,
        tables_completed=progress.tables_completed,
        rows_migrated=progress.rows_migrated,
        duration_seconds=progress.duration_seconds,
        errors=progress.errors[:10]
    )


@router.get("/migration/{session_id}/phases")
async def get_migration_phases(session_id: str):
    """Get detailed phase status for a migration."""
    progress = db_migration_service.get_progress(session_id)
    if not progress:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return {
        "session_id": session_id,
        "phases": [
            {
                "phase": phase.value,
                "status": progress.phase_status.get(phase, MigrationStatus.PENDING).value,
                "is_current": phase == progress.current_phase
            }
            for phase in MigrationPhase
        ]
    }


@router.get("/migration/{session_id}/tables")
async def get_table_progress(session_id: str):
    """Get table-level progress for a migration."""
    progress = db_migration_service.get_progress(session_id)
    if not progress:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return {
        "session_id": session_id,
        "total_tables": progress.total_tables,
        "tables_completed": progress.tables_completed,
        "tables": [
            {
                "name": stats.table_name,
                "schema": stats.schema_name,
                "source_rows": stats.source_row_count,
                "migrated_rows": stats.rows_migrated,
                "progress": stats.success_rate,
                "status": stats.status.value,
                "duration_seconds": stats.duration_seconds
            }
            for stats in progress.table_stats.values()
        ]
    }


@router.post("/migration/{session_id}/rollback")
async def rollback_migration(session_id: str):
    """Rollback a migration to the backup state."""
    success = await db_migration_service.rollback_migration(session_id)
    if not success:
        raise HTTPException(status_code=400, detail="Rollback failed or no backup available")

    return {"success": True, "session_id": session_id, "message": "Migration rolled back successfully"}


# ============================================
# Service Status Endpoints
# ============================================

@router.get("/status")
async def get_week131_status():
    """Get status of Week 131 services."""
    return {
        "week": 131,
        "phase": "complete",
        "services": {
            "code_transformation": {
                "status": "active",
                "supported_transformations": [
                    "vbnet_to_csharp",
                    "vbnet_to_python",
                    "tsql_to_plpgsql"
                ]
            },
            "database_migration": db_migration_service.get_status()
        },
        "endpoints": {
            "transformation": [
                "/api/week131/transform/file",
                "/api/week131/transform/directory",
                "/api/week131/transform/rules",
                "/api/week131/transform/rollback/{file_path}"
            ],
            "migration": [
                "/api/week131/migration/start",
                "/api/week131/migration/{session_id}",
                "/api/week131/migration/{session_id}/phases",
                "/api/week131/migration/{session_id}/tables",
                "/api/week131/migration/{session_id}/rollback"
            ]
        }
    }
