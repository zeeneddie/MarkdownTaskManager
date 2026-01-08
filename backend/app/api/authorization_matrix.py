"""
Authorization Matrix API - Fase 25: Business Logic Extraction

REST API endpoints for authorization matrix extraction from legacy code.

Author: Claude Code (Week 139 - Fase 25)
Date: 2026-01-01
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.authorization_matrix import AuthorizationMatrixOutputFormat
from app.services.authorization_matrix_service import AuthorizationMatrixService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/authorization-matrix", tags=["Authorization Matrix"])


# Request/Response Models

class CreateSessionRequest(BaseModel):
    """Request to create a new extraction session"""
    project_id: Optional[str] = None
    name: str = "Authorization Matrix Extraction"


class CreateSessionResponse(BaseModel):
    """Response with session ID"""
    session_id: str
    message: str = "Session created"


class ExtractRequest(BaseModel):
    """Request to extract authorization matrix from files"""
    files: Dict[str, str] = Field(..., description="Map of file paths to file contents")
    language: str = Field("vbnet", description="Programming language: vbnet, csharp, python, javascript")


class ExtractResponse(BaseModel):
    """Response with extraction results"""
    session_id: str
    total_files_scanned: int
    files_with_auth: int
    total_roles: int
    total_permissions: int
    total_resources: int
    total_mappings: int
    total_conflicts: int
    average_confidence: float
    warnings: List[str]
    errors: List[str]
    duration_seconds: float


class RoleSummary(BaseModel):
    """Summary of an extracted role"""
    id: str
    name: str
    display_name: str
    level: str
    parent_role: Optional[str]
    confidence: float


class PermissionSummary(BaseModel):
    """Summary of an extracted permission"""
    id: str
    name: str
    display_name: str
    permission_type: str
    confidence: float


class ResourceSummary(BaseModel):
    """Summary of an extracted resource"""
    id: str
    name: str
    display_name: str
    resource_type: str
    path: Optional[str]
    confidence: float


class ConflictSummary(BaseModel):
    """Summary of an authorization conflict"""
    id: str
    conflict_type: str
    severity: str
    description: str
    recommendation: str


class MatrixSummary(BaseModel):
    """Summary of the authorization matrix"""
    id: str
    name: str
    total_roles: int
    total_permissions: int
    total_resources: int
    total_mappings: int
    total_conflicts: int
    coverage_percentage: float
    confidence: float


class SessionDetails(BaseModel):
    """Full session details"""
    session_id: str
    project_id: Optional[str]
    matrix: Optional[MatrixSummary]
    statistics: Dict[str, Any]
    started_at: str
    completed_at: Optional[str]
    duration_seconds: float


class AccessCheckRequest(BaseModel):
    """Request to check if a role has access"""
    role_name: str
    permission_name: str
    resource_name: Optional[str] = None


class AccessCheckResponse(BaseModel):
    """Response for access check"""
    role_name: str
    permission_name: str
    resource_name: Optional[str]
    has_access: bool


# Service instance
_service: Optional[AuthorizationMatrixService] = None


def get_service(db: AsyncSession = Depends(get_db)) -> AuthorizationMatrixService:
    """Get or create service instance"""
    global _service
    if _service is None:
        _service = AuthorizationMatrixService(db=db)
    return _service


# Endpoints

@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    service: AuthorizationMatrixService = Depends(get_service)
):
    """Create a new authorization matrix extraction session"""
    try:
        session_id = await service.create_session(
            project_id=request.project_id,
            name=request.name
        )
        return CreateSessionResponse(
            session_id=session_id,
            message="Session created successfully"
        )
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=SessionDetails)
async def get_session(
    session_id: str,
    service: AuthorizationMatrixService = Depends(get_service)
):
    """Get session details"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    matrix_summary = None
    if result.matrix:
        stats = result.matrix.statistics
        matrix_summary = MatrixSummary(
            id=result.matrix.id,
            name=result.matrix.name,
            total_roles=stats.total_roles if stats else len(result.matrix.roles),
            total_permissions=stats.total_permissions if stats else len(result.matrix.permissions),
            total_resources=stats.total_resources if stats else len(result.matrix.resources),
            total_mappings=stats.total_mappings if stats else len(result.matrix.mappings),
            total_conflicts=stats.total_conflicts if stats else len(result.matrix.conflicts),
            coverage_percentage=stats.coverage_percentage if stats else 0.0,
            confidence=result.matrix.confidence
        )

    return SessionDetails(
        session_id=result.session_id,
        project_id=result.project_id,
        matrix=matrix_summary,
        statistics={
            "total_files_scanned": result.total_files_scanned,
            "files_with_auth": result.files_with_auth,
            "average_confidence": result.average_confidence
        },
        started_at=result.started_at.isoformat(),
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
        duration_seconds=result.duration_seconds
    )


@router.post("/sessions/{session_id}/extract", response_model=ExtractResponse)
async def extract_authorization_matrix(
    session_id: str,
    request: ExtractRequest,
    service: AuthorizationMatrixService = Depends(get_service)
):
    """Extract authorization matrix from provided source files"""
    try:
        result = await service.extract_from_files(
            session_id=session_id,
            files=request.files,
            language=request.language
        )

        matrix = result.matrix
        stats = matrix.statistics if matrix else None

        return ExtractResponse(
            session_id=result.session_id,
            total_files_scanned=result.total_files_scanned,
            files_with_auth=result.files_with_auth,
            total_roles=stats.total_roles if stats else 0,
            total_permissions=stats.total_permissions if stats else 0,
            total_resources=stats.total_resources if stats else 0,
            total_mappings=stats.total_mappings if stats else 0,
            total_conflicts=stats.total_conflicts if stats else 0,
            average_confidence=result.average_confidence,
            warnings=result.warnings,
            errors=result.errors,
            duration_seconds=result.duration_seconds
        )
    except Exception as e:
        logger.error(f"Error extracting authorization matrix: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/roles")
async def list_roles(
    session_id: str,
    service: AuthorizationMatrixService = Depends(get_service)
) -> List[RoleSummary]:
    """List all roles in a session"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    if not result.matrix:
        return []

    return [
        RoleSummary(
            id=r.id,
            name=r.name,
            display_name=r.display_name,
            level=r.level.value,
            parent_role=r.parent_role,
            confidence=r.confidence
        )
        for r in result.matrix.roles
    ]


@router.get("/sessions/{session_id}/permissions")
async def list_permissions(
    session_id: str,
    service: AuthorizationMatrixService = Depends(get_service)
) -> List[PermissionSummary]:
    """List all permissions in a session"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    if not result.matrix:
        return []

    return [
        PermissionSummary(
            id=p.id,
            name=p.name,
            display_name=p.display_name,
            permission_type=p.permission_type.value,
            confidence=p.confidence
        )
        for p in result.matrix.permissions
    ]


@router.get("/sessions/{session_id}/resources")
async def list_resources(
    session_id: str,
    service: AuthorizationMatrixService = Depends(get_service)
) -> List[ResourceSummary]:
    """List all resources in a session"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    if not result.matrix:
        return []

    return [
        ResourceSummary(
            id=r.id,
            name=r.name,
            display_name=r.display_name,
            resource_type=r.resource_type.value,
            path=r.path,
            confidence=r.confidence
        )
        for r in result.matrix.resources
    ]


@router.get("/sessions/{session_id}/conflicts")
async def list_conflicts(
    session_id: str,
    severity: Optional[str] = Query(None, description="Filter by severity: low, medium, high, critical"),
    service: AuthorizationMatrixService = Depends(get_service)
) -> List[ConflictSummary]:
    """List all conflicts in a session"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    if not result.matrix:
        return []

    conflicts = result.matrix.conflicts
    if severity:
        conflicts = [c for c in conflicts if c.severity == severity]

    return [
        ConflictSummary(
            id=c.id,
            conflict_type=c.conflict_type.value,
            severity=c.severity,
            description=c.description,
            recommendation=c.recommendation
        )
        for c in conflicts
    ]


@router.get("/sessions/{session_id}/matrix")
async def get_matrix(
    session_id: str,
    service: AuthorizationMatrixService = Depends(get_service)
) -> Dict[str, Any]:
    """Get the complete authorization matrix"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    if not result.matrix:
        raise HTTPException(status_code=404, detail="Matrix not found")

    return result.matrix.to_dict()


@router.post("/sessions/{session_id}/check-access", response_model=AccessCheckResponse)
async def check_access(
    session_id: str,
    request: AccessCheckRequest,
    service: AuthorizationMatrixService = Depends(get_service)
):
    """Check if a role has access to a permission/resource"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    if not result.matrix:
        raise HTTPException(status_code=404, detail="Matrix not found")

    has_access = result.matrix.check_access(
        role_name=request.role_name,
        permission_name=request.permission_name,
        resource_name=request.resource_name
    )

    return AccessCheckResponse(
        role_name=request.role_name,
        permission_name=request.permission_name,
        resource_name=request.resource_name,
        has_access=has_access
    )


@router.get("/sessions/{session_id}/role/{role_name}/permissions")
async def get_role_permissions(
    session_id: str,
    role_name: str,
    service: AuthorizationMatrixService = Depends(get_service)
) -> Dict[str, Any]:
    """Get all permissions for a specific role"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    if not result.matrix:
        raise HTTPException(status_code=404, detail="Matrix not found")

    permission_ids = result.matrix.get_role_permissions(role_name)

    # Get full permission details
    permissions = [
        {
            "id": p.id,
            "name": p.name,
            "display_name": p.display_name,
            "permission_type": p.permission_type.value
        }
        for p in result.matrix.permissions
        if p.id in permission_ids
    ]

    return {
        "role_name": role_name,
        "permissions": permissions,
        "count": len(permissions)
    }


@router.get("/sessions/{session_id}/resource/{resource_name}/roles")
async def get_resource_roles(
    session_id: str,
    resource_name: str,
    service: AuthorizationMatrixService = Depends(get_service)
) -> Dict[str, Any]:
    """Get all roles that can access a specific resource"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    if not result.matrix:
        raise HTTPException(status_code=404, detail="Matrix not found")

    role_names = result.matrix.get_resource_roles(resource_name)

    # Get full role details
    roles = [
        {
            "id": r.id,
            "name": r.name,
            "display_name": r.display_name,
            "level": r.level.value
        }
        for r in result.matrix.roles
        if r.name in role_names
    ]

    return {
        "resource_name": resource_name,
        "roles": roles,
        "count": len(roles)
    }


@router.get("/sessions/{session_id}/export")
async def export_session(
    session_id: str,
    format: str = Query("markdown", description="Export format: markdown, csv, json, html"),
    service: AuthorizationMatrixService = Depends(get_service)
) -> Dict[str, Any]:
    """Export authorization matrix in specified format"""
    try:
        format_map = {
            "markdown": AuthorizationMatrixOutputFormat.MARKDOWN,
            "csv": AuthorizationMatrixOutputFormat.CSV,
            "json": AuthorizationMatrixOutputFormat.JSON,
            "html": AuthorizationMatrixOutputFormat.HTML,
        }

        output_format = format_map.get(format.lower())
        if not output_format:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format. Use: markdown, csv, json, html"
            )

        content = await service.export_session(session_id, output_format)

        return {
            "session_id": session_id,
            "format": format,
            "content": content
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/statistics")
async def get_statistics(
    session_id: str,
    service: AuthorizationMatrixService = Depends(get_service)
) -> Dict[str, Any]:
    """Get detailed statistics for the authorization matrix"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    if not result.matrix or not result.matrix.statistics:
        return {
            "session_id": session_id,
            "statistics": None,
            "message": "No statistics available"
        }

    stats = result.matrix.statistics
    return {
        "session_id": session_id,
        "statistics": {
            "total_roles": stats.total_roles,
            "total_permissions": stats.total_permissions,
            "total_resources": stats.total_resources,
            "total_mappings": stats.total_mappings,
            "total_conflicts": stats.total_conflicts,
            "coverage_percentage": stats.coverage_percentage,
            "role_hierarchy_depth": stats.role_hierarchy_depth,
            "average_permissions_per_role": stats.average_permissions_per_role,
            "critical_conflicts": stats.critical_conflicts,
            "high_conflicts": stats.high_conflicts
        }
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "authorization-matrix"}
