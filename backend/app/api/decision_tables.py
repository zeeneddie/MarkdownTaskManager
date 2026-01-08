"""
Decision Tables API - Fase 25: Business Logic Extraction

REST API endpoints for decision table extraction and management.

Author: Claude Code (Week 138 - Fase 25)
Date: 2026-01-01
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.decision_table import DecisionTableOutputFormat
from app.services.decision_table_extractor_service import DecisionTableExtractorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/decision-tables", tags=["Decision Tables"])


# Request/Response Models

class CreateSessionRequest(BaseModel):
    """Request to create a new extraction session"""
    project_id: Optional[str] = None
    name: str = "Decision Table Extraction"


class CreateSessionResponse(BaseModel):
    """Response with session ID"""
    session_id: str
    message: str = "Session created"


class ExtractRequest(BaseModel):
    """Request to extract decision tables from files"""
    files: Dict[str, str] = Field(..., description="Map of file paths to file contents")
    language: str = Field("vbnet", description="Programming language: vbnet, csharp, python, javascript")
    min_nesting: int = Field(2, ge=1, le=10, description="Minimum nesting level to consider")


class ExtractResponse(BaseModel):
    """Response with extraction results"""
    session_id: str
    total_files_scanned: int
    files_with_tables: int
    total_tables_extracted: int
    total_rules_extracted: int
    average_confidence: float
    warnings: List[str]
    errors: List[str]
    duration_seconds: float


class DecisionTableSummary(BaseModel):
    """Summary of a decision table"""
    id: str
    name: str
    description: str
    source_file: Optional[str]
    total_rules: int
    total_inputs: int
    total_outputs: int
    hit_policy: str
    confidence: float


class SessionDetails(BaseModel):
    """Full session details"""
    session_id: str
    project_id: Optional[str]
    tables: List[DecisionTableSummary]
    statistics: Dict[str, Any]
    started_at: str
    completed_at: Optional[str]
    duration_seconds: float


class ExportRequest(BaseModel):
    """Request to export tables"""
    format: str = Field("markdown", description="Export format: markdown, dmn_xml, dmn_json")
    table_ids: Optional[List[str]] = Field(None, description="Specific table IDs to export, or all if None")


# Service instance (will be replaced with proper DI)
_service: Optional[DecisionTableExtractorService] = None


def get_service(db: AsyncSession = Depends(get_db)) -> DecisionTableExtractorService:
    """Get or create service instance"""
    global _service
    if _service is None:
        _service = DecisionTableExtractorService(db=db)
    return _service


# Endpoints

@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    service: DecisionTableExtractorService = Depends(get_service)
):
    """Create a new decision table extraction session"""
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
    service: DecisionTableExtractorService = Depends(get_service)
):
    """Get session details"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    tables_summary = [
        DecisionTableSummary(
            id=t.id,
            name=t.name,
            description=t.description,
            source_file=t.source_file,
            total_rules=len(t.rules),
            total_inputs=len(t.inputs),
            total_outputs=len(t.outputs),
            hit_policy=t.hit_policy.value,
            confidence=t.confidence
        )
        for t in result.tables
    ]

    return SessionDetails(
        session_id=result.session_id,
        project_id=result.project_id,
        tables=tables_summary,
        statistics={
            "total_files_scanned": result.total_files_scanned,
            "files_with_tables": result.files_with_tables,
            "total_tables_extracted": result.total_tables_extracted,
            "total_rules_extracted": result.total_rules_extracted,
            "average_confidence": result.average_confidence
        },
        started_at=result.started_at.isoformat(),
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
        duration_seconds=result.duration_seconds
    )


@router.post("/sessions/{session_id}/extract", response_model=ExtractResponse)
async def extract_decision_tables(
    session_id: str,
    request: ExtractRequest,
    service: DecisionTableExtractorService = Depends(get_service)
):
    """Extract decision tables from provided source files"""
    try:
        result = await service.extract_from_files(
            session_id=session_id,
            files=request.files,
            language=request.language,
            min_nesting=request.min_nesting
        )

        return ExtractResponse(
            session_id=result.session_id,
            total_files_scanned=result.total_files_scanned,
            files_with_tables=result.files_with_tables,
            total_tables_extracted=result.total_tables_extracted,
            total_rules_extracted=result.total_rules_extracted,
            average_confidence=result.average_confidence,
            warnings=result.warnings,
            errors=result.errors,
            duration_seconds=result.duration_seconds
        )
    except Exception as e:
        logger.error(f"Error extracting decision tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/tables")
async def list_tables(
    session_id: str,
    service: DecisionTableExtractorService = Depends(get_service)
) -> List[DecisionTableSummary]:
    """List all decision tables in a session"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    return [
        DecisionTableSummary(
            id=t.id,
            name=t.name,
            description=t.description,
            source_file=t.source_file,
            total_rules=len(t.rules),
            total_inputs=len(t.inputs),
            total_outputs=len(t.outputs),
            hit_policy=t.hit_policy.value,
            confidence=t.confidence
        )
        for t in result.tables
    ]


@router.get("/sessions/{session_id}/tables/{table_id}")
async def get_table(
    session_id: str,
    table_id: str,
    service: DecisionTableExtractorService = Depends(get_service)
) -> Dict[str, Any]:
    """Get a specific decision table"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    table = next((t for t in result.tables if t.id == table_id), None)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    return table.to_dict()


@router.get("/sessions/{session_id}/export")
async def export_tables(
    session_id: str,
    format: str = Query("markdown", description="Export format: markdown, dmn_xml, dmn_json"),
    service: DecisionTableExtractorService = Depends(get_service)
) -> Dict[str, Any]:
    """Export decision tables in specified format"""
    try:
        # Map format string to enum
        format_map = {
            "markdown": DecisionTableOutputFormat.MARKDOWN,
            "dmn_xml": DecisionTableOutputFormat.DMN_XML,
            "dmn_json": DecisionTableOutputFormat.DMN_JSON,
        }
        output_format = format_map.get(format.lower())
        if not output_format:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format. Use: markdown, dmn_xml, dmn_json"
            )

        content = await service.export_tables(session_id, output_format)

        return {
            "session_id": session_id,
            "format": format,
            "content": content
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/tables/{table_id}/export")
async def export_single_table(
    session_id: str,
    table_id: str,
    format: str = Query("markdown", description="Export format"),
    service: DecisionTableExtractorService = Depends(get_service)
) -> Dict[str, Any]:
    """Export a single decision table"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    table = next((t for t in result.tables if t.id == table_id), None)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    try:
        if format == "markdown":
            content = await service.export_to_markdown(table)
        elif format == "dmn_xml":
            content = await service.export_to_dmn_xml(table)
        elif format == "dmn_json":
            import json
            content = json.dumps(await service.export_to_json(table), indent=2)
        else:
            raise HTTPException(status_code=400, detail="Invalid format")

        return {
            "table_id": table_id,
            "format": format,
            "content": content
        }
    except Exception as e:
        logger.error(f"Error exporting table: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "decision-tables"}
