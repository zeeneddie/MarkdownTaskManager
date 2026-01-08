# backend/app/api/requirements.py
"""
Requirements Management API - Week 117

Endpoints for rmtoo requirements management:
- CRUD operations for requirements
- Import from extraction sessions
- Sync with rmtoo files
- Export documentation (HTML, PDF, graphs)
- Traceability links
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.rmtoo_adapter_service import RmtooAdapterService
from app.services.requirements_sync_service import RequirementsSyncService
from app.models.rmtoo import (
    RequirementCategory,
    RequirementStatus,
    SyncDirection,
    ExportType,
    LinkType,
)


router = APIRouter(prefix="/api/requirements", tags=["Requirements Management"])


# ============== Schemas ==============

class RequirementCreate(BaseModel):
    """Schema for creating a requirement manually."""
    name: Optional[str] = None  # Auto-generated if not provided
    description: str
    rationale: Optional[str] = None
    category: str = "BR"
    owner: Optional[str] = "development"
    priority: Optional[str] = None
    effort_estimation: Optional[int] = None
    topic: Optional[str] = None
    solved_by: Optional[List[str]] = []
    depends_on: Optional[List[str]] = []


class RequirementUpdate(BaseModel):
    """Schema for updating a requirement."""
    description: Optional[str] = None
    rationale: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    effort_estimation: Optional[int] = None
    topic: Optional[str] = None
    solved_by: Optional[List[str]] = None
    depends_on: Optional[List[str]] = None


class RequirementResponse(BaseModel):
    """Schema for requirement response."""
    id: UUID
    project_id: int
    name: str
    req_type: str
    description: str
    rationale: Optional[str]
    invented_on: Optional[str]
    invented_by: Optional[str]
    owner: Optional[str]
    status: str
    priority: Optional[str]
    effort_estimation: Optional[int]
    topic: Optional[str]
    category: str
    source_type: Optional[str]
    source_file: Optional[str]
    confidence: Optional[float]
    validated: bool
    validated_by: Optional[str]
    solved_by: List[str]
    depends_on: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImportFromExtractionRequest(BaseModel):
    """Schema for importing from extraction session."""
    extraction_session_id: UUID
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class SyncRequest(BaseModel):
    """Schema for sync operations."""
    output_path: str
    git_auto_commit: bool = False


class ExportRequest(BaseModel):
    """Schema for export operations."""
    export_type: str  # html, markdown, graph, pdf
    output_path: str
    include_topics: Optional[List[str]] = None
    include_categories: Optional[List[str]] = None


class TraceabilityLinkCreate(BaseModel):
    """Schema for creating traceability link."""
    entity_type: str  # epic, feature, story, task, business_rule
    entity_id: str
    entity_name: Optional[str] = None
    link_type: str = "implements"
    confidence: Optional[float] = None


class StatisticsResponse(BaseModel):
    """Schema for project statistics."""
    total_requirements: int
    by_category: dict
    by_status: dict
    validated_count: int
    validation_percentage: float
    average_confidence: float
    traceability_links: int


class SyncSessionResponse(BaseModel):
    """Schema for sync session response."""
    id: UUID
    project_id: int
    direction: str
    status: str
    requirements_created: int
    requirements_updated: int
    topics_synced: int
    conflicts_detected: int
    output_path: Optional[str]
    git_commit_hash: Optional[str]
    errors: List[str]
    warnings: List[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]

    model_config = ConfigDict(from_attributes=True)


# ============== Endpoints ==============

@router.get("/categories")
async def get_categories():
    """Get available requirement categories."""
    return {
        "categories": [
            {"code": "BR", "name": "Business Rule", "prefix": "REQ-BR"},
            {"code": "FR", "name": "Functional Requirement", "prefix": "REQ-FR"},
            {"code": "NFR", "name": "Non-Functional Requirement", "prefix": "REQ-NFR"},
            {"code": "TR", "name": "Technical Requirement", "prefix": "REQ-TR"},
            {"code": "CMP", "name": "Compliance Requirement", "prefix": "REQ-CMP"},
        ]
    }


@router.get("/statuses")
async def get_statuses():
    """Get available requirement statuses."""
    return {
        "statuses": [
            {"code": "not done", "name": "Not Done"},
            {"code": "done", "name": "Done"},
            {"code": "approved", "name": "Approved"},
            {"code": "rejected", "name": "Rejected"},
        ]
    }


@router.get("/export-types")
async def get_export_types():
    """Get available export types."""
    return {
        "export_types": [
            {"code": "html", "name": "HTML Documentation"},
            {"code": "markdown", "name": "Markdown Documentation"},
            {"code": "graph", "name": "Dependency Graph (DOT/SVG)"},
            {"code": "pdf", "name": "PDF (requires LaTeX)"},
        ]
    }


@router.get("/projects")
async def list_projects(
    db: AsyncSession = Depends(get_db),
):
    """List all projects with their IDs for requirements management."""
    from app.models.project import Project
    from sqlalchemy import select

    result = await db.execute(select(Project).order_by(Project.name))
    projects = result.scalars().all()

    return {
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "description": getattr(p, 'description', None),
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in projects
        ]
    }


@router.post("/projects/{project_id}/initialize-topics")
async def initialize_topics(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Initialize default topic structure for a project."""
    adapter = RmtooAdapterService(db)
    topics = await adapter.initialize_topics(project_id)
    return {
        "message": f"Initialized {len(topics)} topics",
        "topics": [{"name": t.name, "title": t.title} for t in topics]
    }


@router.post("/projects/{project_id}/import-from-extraction", response_model=dict)
async def import_from_extraction(
    project_id: int,
    request: ImportFromExtractionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Import requirements from a hybrid extraction session."""
    adapter = RmtooAdapterService(db)
    stats = await adapter.import_from_extraction_session(
        extraction_session_id=request.extraction_session_id,
        min_confidence=request.min_confidence,
    )
    return stats


@router.get("/projects/{project_id}", response_model=List[RequirementResponse])
async def get_requirements(
    project_id: int,
    category: Optional[str] = None,
    status: Optional[str] = None,
    validated_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Get all requirements for a project with optional filters."""
    adapter = RmtooAdapterService(db)

    cat = RequirementCategory(category) if category else None
    stat = RequirementStatus(status) if status else None

    requirements = await adapter.get_requirements_by_project(
        project_id=project_id,
        category=cat,
        status=stat,
        validated_only=validated_only,
    )

    return [
        RequirementResponse(
            id=r.id,
            project_id=r.project_id,
            name=r.name,
            req_type=r.req_type,
            description=r.description,
            rationale=r.rationale,
            invented_on=r.invented_on.isoformat() if r.invented_on else None,
            invented_by=r.invented_by,
            owner=r.owner,
            status=r.status,
            priority=r.priority,
            effort_estimation=r.effort_estimation,
            topic=r.topic,
            category=r.category,
            source_type=r.source_type,
            source_file=r.source_file,
            confidence=r.confidence,
            validated=r.validated,
            validated_by=r.validated_by,
            solved_by=r.solved_by or [],
            depends_on=r.depends_on or [],
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in requirements
    ]


@router.get("/projects/{project_id}/statistics", response_model=StatisticsResponse)
async def get_statistics(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get requirement statistics for a project."""
    adapter = RmtooAdapterService(db)
    stats = await adapter.get_project_statistics(project_id)
    return StatisticsResponse(**stats)


@router.get("/projects/{project_id}/requirements/{name}")
async def get_requirement_by_name(
    project_id: int,
    name: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific requirement by name."""
    adapter = RmtooAdapterService(db)
    req = await adapter.get_requirement_by_name(project_id, name)
    if not req:
        raise HTTPException(status_code=404, detail=f"Requirement {name} not found")

    return {
        "id": str(req.id),
        "name": req.name,
        "description": req.description,
        "category": req.category,
        "status": req.status,
        "rmtoo_content": req.rmtoo_content,
    }


@router.post("/requirements/{requirement_id}/validate")
async def validate_requirement(
    requirement_id: UUID,
    validated_by: str = Query(..., description="Name of validator"),
    db: AsyncSession = Depends(get_db),
):
    """Mark a requirement as validated."""
    adapter = RmtooAdapterService(db)
    try:
        req = await adapter.validate_requirement(requirement_id, validated_by)
        return {"message": f"Requirement {req.name} validated", "status": req.status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/requirements/{requirement_id}/dependencies")
async def add_dependency(
    requirement_id: UUID,
    solved_by_name: str = Query(..., description="Name of solving requirement"),
    db: AsyncSession = Depends(get_db),
):
    """Add a 'Solved by' dependency to a requirement."""
    adapter = RmtooAdapterService(db)
    try:
        req = await adapter.add_dependency(requirement_id, solved_by_name)
        return {"message": f"Dependency added", "solved_by": req.solved_by}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/requirements/{requirement_id}/traceability")
async def create_traceability_link(
    requirement_id: UUID,
    request: TraceabilityLinkCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a traceability link between requirement and MarQed entity."""
    adapter = RmtooAdapterService(db)
    try:
        link_type = LinkType(request.link_type)
        link = await adapter.create_traceability_link(
            requirement_id=requirement_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            entity_name=request.entity_name,
            link_type=link_type,
            confidence=request.confidence,
        )
        return {
            "id": str(link.id),
            "requirement_name": link.requirement_name,
            "entity_type": link.entity_type,
            "entity_id": link.entity_id,
            "link_type": link.link_type,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== Sync Endpoints ==============

@router.post("/projects/{project_id}/sync/db-to-files", response_model=SyncSessionResponse)
async def sync_db_to_files(
    project_id: int,
    request: SyncRequest,
    db: AsyncSession = Depends(get_db),
):
    """Export requirements from database to rmtoo files."""
    sync_service = RequirementsSyncService(db)
    session = await sync_service.sync_db_to_files(
        project_id=project_id,
        output_path=request.output_path,
        git_auto_commit=request.git_auto_commit,
    )
    return session


@router.post("/projects/{project_id}/sync/files-to-db", response_model=SyncSessionResponse)
async def sync_files_to_db(
    project_id: int,
    request: SyncRequest,
    db: AsyncSession = Depends(get_db),
):
    """Import requirements from rmtoo files to database."""
    sync_service = RequirementsSyncService(db)
    session = await sync_service.sync_files_to_db(
        project_id=project_id,
        input_path=request.output_path,
    )
    return session


@router.get("/projects/{project_id}/sync/history", response_model=List[SyncSessionResponse])
async def get_sync_history(
    project_id: int,
    limit: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get sync session history for a project."""
    sync_service = RequirementsSyncService(db)
    sessions = await sync_service.get_sync_history(project_id, limit)
    return sessions


# ============== Export Endpoints ==============

@router.post("/projects/{project_id}/export")
async def export_documentation(
    project_id: int,
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate documentation from requirements."""
    sync_service = RequirementsSyncService(db)
    try:
        export_type = ExportType(request.export_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid export type: {request.export_type}")

    export = await sync_service.export_documentation(
        project_id=project_id,
        export_type=export_type,
        output_path=request.output_path,
        include_topics=request.include_topics,
        include_categories=request.include_categories,
    )

    return {
        "id": str(export.id),
        "export_type": export.export_type,
        "status": export.status,
        "output_path": export.output_path,
        "requirements_included": export.requirements_included,
        "file_size_bytes": export.file_size_bytes,
        "duration_ms": export.duration_ms,
    }


@router.get("/projects/{project_id}/export/history")
async def get_export_history(
    project_id: int,
    limit: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get export history for a project."""
    sync_service = RequirementsSyncService(db)
    exports = await sync_service.get_export_history(project_id, limit)
    return [
        {
            "id": str(e.id),
            "export_type": e.export_type,
            "status": e.status,
            "output_path": e.output_path,
            "requirements_included": e.requirements_included,
            "created_at": e.created_at.isoformat(),
        }
        for e in exports
    ]


# ============== Traceability Matrix ==============

@router.get("/projects/{project_id}/traceability-matrix")
async def get_traceability_matrix(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get traceability matrix for a project."""
    from sqlalchemy import select
    from app.models.rmtoo import RmtooRequirement, RmtooTraceabilityLink

    # Get all requirements with their links
    result = await db.execute(
        select(RmtooRequirement).where(
            RmtooRequirement.project_id == project_id
        ).order_by(RmtooRequirement.name)
    )
    requirements = result.scalars().all()

    result = await db.execute(
        select(RmtooTraceabilityLink).where(
            RmtooTraceabilityLink.project_id == project_id
        )
    )
    links = result.scalars().all()

    # Build matrix
    matrix = []
    for req in requirements:
        req_links = [l for l in links if l.requirement_id == req.id]
        matrix.append({
            "requirement": {
                "id": str(req.id),
                "name": req.name,
                "category": req.category,
                "description": req.description[:100] + "..." if len(req.description) > 100 else req.description,
            },
            "links": [
                {
                    "entity_type": l.entity_type,
                    "entity_id": l.entity_id,
                    "entity_name": l.entity_name,
                    "link_type": l.link_type,
                    "confidence": l.confidence,
                    "validated": l.validated,
                }
                for l in req_links
            ],
            "coverage": len(req_links) > 0,
        })

    return {
        "project_id": project_id,
        "total_requirements": len(requirements),
        "linked_requirements": len([m for m in matrix if m["coverage"]]),
        "coverage_percentage": len([m for m in matrix if m["coverage"]]) / len(requirements) * 100 if requirements else 0,
        "matrix": matrix,
    }
