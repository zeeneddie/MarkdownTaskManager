"""
State Machine Extraction API - Fase 25: Business Logic Extraction

REST API endpoints for state machine extraction from legacy code.

Author: Claude Code (Week 138 - Fase 25)
Date: 2026-01-01
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.state_machine_extractor_service import (
    StateMachineExtractorService,
    StateMachineOutputFormat,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/state-machines", tags=["State Machine Extraction"])


# Request/Response Models

class CreateSessionRequest(BaseModel):
    """Request to create a new extraction session"""
    project_id: Optional[str] = None
    name: str = "State Machine Extraction"


class CreateSessionResponse(BaseModel):
    """Response with session ID"""
    session_id: str
    message: str = "Session created"


class ExtractRequest(BaseModel):
    """Request to extract state machines from files"""
    files: Dict[str, str] = Field(..., description="Map of file paths to file contents")
    language: str = Field("vbnet", description="Programming language: vbnet, csharp, python, javascript")


class ExtractResponse(BaseModel):
    """Response with extraction results"""
    session_id: str
    total_files_scanned: int
    files_with_machines: int
    total_machines_extracted: int
    average_confidence: float
    warnings: List[str]
    errors: List[str]
    duration_seconds: float


class StateMachineSummary(BaseModel):
    """Summary of an extracted state machine"""
    id: str
    name: str
    description: str
    pattern_type: str
    source_file: Optional[str]
    total_states: int
    total_transitions: int
    initial_state: Optional[str]
    confidence: float


class SessionDetails(BaseModel):
    """Full session details"""
    session_id: str
    project_id: Optional[str]
    machines: List[StateMachineSummary]
    statistics: Dict[str, Any]
    started_at: str
    completed_at: Optional[str]
    duration_seconds: float


# Service instance
_service: Optional[StateMachineExtractorService] = None


def get_service(db: AsyncSession = Depends(get_db)) -> StateMachineExtractorService:
    """Get or create service instance"""
    global _service
    if _service is None:
        _service = StateMachineExtractorService(db=db)
    return _service


# Endpoints

@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    service: StateMachineExtractorService = Depends(get_service)
):
    """Create a new state machine extraction session"""
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
    service: StateMachineExtractorService = Depends(get_service)
):
    """Get session details"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    machines_summary = [
        StateMachineSummary(
            id=m.id,
            name=m.name,
            description=m.description,
            pattern_type=m.pattern_type.value,
            source_file=m.source_file,
            total_states=len(m.states),
            total_transitions=len(m.transitions),
            initial_state=m.initial_state,
            confidence=m.confidence
        )
        for m in result.machines
    ]

    return SessionDetails(
        session_id=result.session_id,
        project_id=result.project_id,
        machines=machines_summary,
        statistics={
            "total_files_scanned": result.total_files_scanned,
            "files_with_machines": result.files_with_machines,
            "total_machines_extracted": result.total_machines_extracted,
            "average_confidence": result.average_confidence
        },
        started_at=result.started_at.isoformat(),
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
        duration_seconds=result.duration_seconds
    )


@router.post("/sessions/{session_id}/extract", response_model=ExtractResponse)
async def extract_state_machines(
    session_id: str,
    request: ExtractRequest,
    service: StateMachineExtractorService = Depends(get_service)
):
    """Extract state machines from provided source files"""
    try:
        result = await service.extract_from_files(
            session_id=session_id,
            files=request.files,
            language=request.language
        )

        return ExtractResponse(
            session_id=result.session_id,
            total_files_scanned=result.total_files_scanned,
            files_with_machines=result.files_with_machines,
            total_machines_extracted=result.total_machines_extracted,
            average_confidence=result.average_confidence,
            warnings=result.warnings,
            errors=result.errors,
            duration_seconds=result.duration_seconds
        )
    except Exception as e:
        logger.error(f"Error extracting state machines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/machines")
async def list_machines(
    session_id: str,
    service: StateMachineExtractorService = Depends(get_service)
) -> List[StateMachineSummary]:
    """List all state machines in a session"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    return [
        StateMachineSummary(
            id=m.id,
            name=m.name,
            description=m.description,
            pattern_type=m.pattern_type.value,
            source_file=m.source_file,
            total_states=len(m.states),
            total_transitions=len(m.transitions),
            initial_state=m.initial_state,
            confidence=m.confidence
        )
        for m in result.machines
    ]


@router.get("/sessions/{session_id}/machines/{machine_id}")
async def get_machine(
    session_id: str,
    machine_id: str,
    service: StateMachineExtractorService = Depends(get_service)
) -> Dict[str, Any]:
    """Get a specific state machine"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    machine = next((m for m in result.machines if m.id == machine_id), None)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    return machine.to_dict()


@router.get("/sessions/{session_id}/machines/{machine_id}/diagram")
async def get_machine_diagram(
    session_id: str,
    machine_id: str,
    format: str = Query("mermaid", description="Diagram format: mermaid, plantuml, xstate"),
    service: StateMachineExtractorService = Depends(get_service)
) -> Dict[str, Any]:
    """Get state machine diagram in specified format"""
    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    machine = next((m for m in result.machines if m.id == machine_id), None)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    try:
        format_map = {
            "mermaid": StateMachineOutputFormat.MERMAID,
            "plantuml": StateMachineOutputFormat.PLANTUML,
            "xstate": StateMachineOutputFormat.XSTATE,
            "json": StateMachineOutputFormat.JSON,
            "markdown": StateMachineOutputFormat.MARKDOWN,
        }

        output_format = format_map.get(format.lower())
        if not output_format:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format. Use: mermaid, plantuml, xstate, json, markdown"
            )

        content = await service.export_to_format(machine, output_format)

        return {
            "machine_id": machine_id,
            "format": format,
            "content": content
        }
    except Exception as e:
        logger.error(f"Error generating diagram: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/export")
async def export_session(
    session_id: str,
    format: str = Query("mermaid", description="Export format"),
    service: StateMachineExtractorService = Depends(get_service)
) -> Dict[str, Any]:
    """Export all state machines from a session"""
    try:
        format_map = {
            "mermaid": StateMachineOutputFormat.MERMAID,
            "plantuml": StateMachineOutputFormat.PLANTUML,
            "xstate": StateMachineOutputFormat.XSTATE,
            "json": StateMachineOutputFormat.JSON,
            "markdown": StateMachineOutputFormat.MARKDOWN,
        }

        output_format = format_map.get(format.lower())
        if not output_format:
            raise HTTPException(status_code=400, detail="Invalid format")

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


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "state-machine-extraction"}
