"""
Fase 24: Data Architecture API Routes

Provides REST endpoints for:
- DataLineageService: Track data flow from specs to code
- ERDGeneratorService: Generate target architecture ERD
- JourneyComparisonService: E2E journey comparison

Author: Claude Code (Week 136 - Fase 24)
Date: 2026-01-01
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db

from app.services.data_lineage_service import DataLineageService
from app.services.erd_generator_service import ERDGeneratorService
from app.services.journey_comparison_service import JourneyComparisonService
from app.services.cdc_integration_service import (
    get_cdc_service,
    CDCMode, CDCProvider, ChangeOperation, ChangeEvent,
    TableMapping
)
from app.models.data_architecture import (
    LineageNodeType, LineageEdgeType, TransformationType,
    ERDOutputFormat, JourneyStepType
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/data-architecture", tags=["Fase 24 - Data Architecture"])


# ============================================
# Request/Response Models
# ============================================

class CreateLineageSessionRequest(BaseModel):
    name: str = Field(..., description="Session name")
    project_id: Optional[str] = None
    brown_paper_session_id: Optional[str] = None
    description: Optional[str] = None


class AddNodeRequest(BaseModel):
    node_type: str = Field(..., description="Type of node (domain, entity, epic, story, etc.)")
    name: str
    description: Optional[str] = None
    source_path: Optional[str] = None
    source_line: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class AddEdgeRequest(BaseModel):
    source_node_id: str
    target_node_id: str
    edge_type: str
    transformation: Optional[str] = None
    transformation_rule: Optional[str] = None
    confidence: float = 1.0


class AddFieldMappingRequest(BaseModel):
    legacy_table: str
    legacy_field: str
    legacy_type: str
    new_table: str
    new_field: str
    new_type: str
    transformation: str
    transformation_rule: Optional[str] = None
    nullable_legacy: bool = True
    nullable_new: bool = True
    default_value: Optional[str] = None
    validation_rule: Optional[str] = None
    notes: Optional[str] = None


class ImportBrownPaperRequest(BaseModel):
    brown_paper_data: Dict[str, Any] = Field(..., description="Brown Paper Enhanced output")


class GenerateERDRequest(BaseModel):
    entities: List[Dict[str, Any]] = Field(..., description="List of extracted entities")
    name: str = "Target Architecture"
    project_id: Optional[str] = None
    brown_paper_session_id: Optional[str] = None
    apply_normalization: bool = True
    detect_relationships: bool = True
    infer_bounded_contexts: bool = True


class CreateRecordingRequest(BaseModel):
    name: str
    system: str = Field(..., description="'legacy' or 'new'")
    base_url: str
    description: Optional[str] = None
    recorded_by: Optional[str] = None
    project_id: Optional[str] = None


class AddStepRequest(BaseModel):
    step_type: str
    selector: Optional[str] = None
    action: Optional[str] = None
    value: Optional[str] = None
    expected_result: Optional[str] = None
    screenshot_path: Optional[str] = None
    api_request: Optional[Dict[str, Any]] = None
    api_response: Optional[Dict[str, Any]] = None
    duration_ms: int = 0


class CompareJourneysRequest(BaseModel):
    legacy_recording_id: str
    new_recording_id: str
    project_id: Optional[str] = None
    apply_overrides: bool = True


class CreateOverrideRuleRequest(BaseModel):
    journey_name: str
    legacy_behavior: str
    new_behavior: str
    reason: str
    approved_by: str
    override_type: str = "intentional_change"
    step_number: Optional[int] = None
    expires_at: Optional[datetime] = None
    project_id: Optional[str] = None


# ============================================
# Data Lineage Endpoints
# ============================================

@router.post("/lineage/sessions")
async def create_lineage_session(
    request: CreateLineageSessionRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new data lineage tracking session."""
    service = DataLineageService(db)
    session_id = await service.create_session(
        name=request.name,
        project_id=request.project_id,
        brown_paper_session_id=request.brown_paper_session_id,
        description=request.description
    )
    return {"session_id": session_id, "name": request.name}


@router.get("/lineage/sessions/{session_id}")
async def get_lineage_session(
    session_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get lineage session details."""
    service = DataLineageService(db)
    graph = await service.get_session(session_id)
    if not graph:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return {
        "session_id": session_id,
        "project_id": graph.project_id,
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "field_mapping_count": len(graph.field_mappings)
    }


@router.post("/lineage/sessions/{session_id}/nodes")
async def add_lineage_node(
    session_id: str,
    request: AddNodeRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Add a node to the lineage graph."""
    service = DataLineageService(db)
    try:
        node_type = LineageNodeType(request.node_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid node type: {request.node_type}")

    node_id = await service.add_node(
        session_id=session_id,
        node_type=node_type,
        name=request.name,
        description=request.description,
        source_path=request.source_path,
        source_line=request.source_line,
        metadata=request.metadata
    )
    return {"node_id": node_id}


@router.post("/lineage/sessions/{session_id}/edges")
async def add_lineage_edge(
    session_id: str,
    request: AddEdgeRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Add an edge connecting two nodes."""
    service = DataLineageService(db)
    try:
        edge_type = LineageEdgeType(request.edge_type)
        transformation = TransformationType(request.transformation) if request.transformation else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    edge_id = await service.add_edge(
        session_id=session_id,
        source_node_id=request.source_node_id,
        target_node_id=request.target_node_id,
        edge_type=edge_type,
        transformation=transformation,
        transformation_rule=request.transformation_rule,
        confidence=request.confidence
    )
    return {"edge_id": edge_id}


@router.post("/lineage/sessions/{session_id}/field-mappings")
async def add_field_mapping(
    session_id: str,
    request: AddFieldMappingRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Add a field mapping between legacy and new schema."""
    service = DataLineageService(db)
    try:
        transformation = TransformationType(request.transformation)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid transformation: {request.transformation}")

    mapping_id = await service.add_field_mapping(
        session_id=session_id,
        legacy_table=request.legacy_table,
        legacy_field=request.legacy_field,
        legacy_type=request.legacy_type,
        new_table=request.new_table,
        new_field=request.new_field,
        new_type=request.new_type,
        transformation=transformation,
        transformation_rule=request.transformation_rule,
        nullable_legacy=request.nullable_legacy,
        nullable_new=request.nullable_new,
        default_value=request.default_value,
        validation_rule=request.validation_rule,
        notes=request.notes
    )
    return {"mapping_id": mapping_id}


@router.get("/lineage/sessions/{session_id}/field-mappings")
async def get_field_mappings(
    session_id: str,
    table_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Get field mappings for a session."""
    service = DataLineageService(db)
    mappings = await service.get_field_mappings(session_id, table_filter)
    return {
        "session_id": session_id,
        "count": len(mappings),
        "mappings": [
            {
                "legacy": f"{m.legacy_table}.{m.legacy_field}",
                "new": f"{m.new_table}.{m.new_field}",
                "transformation": m.transformation.value,
                "rule": m.transformation_rule
            }
            for m in mappings
        ]
    }


@router.post("/lineage/sessions/{session_id}/import-brown-paper")
async def import_brown_paper(
    session_id: str,
    request: ImportBrownPaperRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Import lineage from Brown Paper Enhanced output."""
    service = DataLineageService(db)
    counts = await service.import_from_brown_paper(session_id, request.brown_paper_data)
    return {"session_id": session_id, "imported": counts}


@router.get("/lineage/sessions/{session_id}/impact/{node_id}")
async def analyze_impact(
    session_id: str,
    node_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Analyze impact of changing a node."""
    service = DataLineageService(db)
    result = await service.analyze_impact(session_id, node_id)
    return {
        "changed_node": result.changed_node_name,
        "risk_level": result.risk_level,
        "affected_nodes": len(result.affected_nodes),
        "test_cases_affected": result.test_cases_affected,
        "code_files_affected": result.code_files_affected,
        "stories_affected": result.stories_affected,
        "recommendations": result.recommendations
    }


@router.get("/lineage/sessions/{session_id}/traceability")
async def get_traceability_matrix(
    session_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Generate traceability matrix."""
    service = DataLineageService(db)
    matrix = await service.generate_traceability_matrix(session_id)
    return matrix


@router.get("/lineage/sessions/{session_id}/statistics")
async def get_lineage_statistics(
    session_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get lineage session statistics."""
    service = DataLineageService(db)
    stats = await service.get_statistics(session_id)
    return stats


# ============================================
# ERD Generator Endpoints
# ============================================

@router.post("/erd/generate")
async def generate_erd(
    request: GenerateERDRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Generate ERD from extracted entities."""
    service = ERDGeneratorService(db)
    diagram = await service.generate_from_entities(
        entities=request.entities,
        name=request.name,
        project_id=request.project_id,
        brown_paper_session_id=request.brown_paper_session_id,
        apply_normalization=request.apply_normalization,
        detect_relationships=request.detect_relationships,
        infer_bounded_contexts=request.infer_bounded_contexts
    )

    return {
        "name": diagram.name,
        "table_count": len(diagram.tables),
        "relationship_count": len(diagram.relationships),
        "bounded_contexts": list(diagram.bounded_contexts.keys()),
        "mermaid": diagram.to_mermaid()
    }


@router.get("/erd/{diagram_id}/export")
async def export_erd(
    diagram_id: str,
    format: str = "mermaid",
    db: AsyncSession = Depends(get_async_db)
):
    """Export ERD in specified format."""
    service = ERDGeneratorService(db)
    try:
        output_format = ERDOutputFormat(format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid format: {format}")

    output = await service.export_diagram(diagram_id, output_format)
    return {"format": format, "output": output}


@router.get("/erd/{diagram_id}/statistics")
async def get_erd_statistics(
    diagram_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get ERD statistics."""
    service = ERDGeneratorService(db)
    stats = await service.get_statistics(diagram_id)
    if not stats:
        raise HTTPException(status_code=404, detail=f"Diagram {diagram_id} not found")
    return stats


# ============================================
# Journey Comparison Endpoints
# ============================================

@router.post("/journey/recordings")
async def create_recording(
    request: CreateRecordingRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new journey recording session."""
    if request.system not in ("legacy", "new"):
        raise HTTPException(status_code=400, detail="System must be 'legacy' or 'new'")

    service = JourneyComparisonService(db)
    recording_id = await service.create_recording(
        name=request.name,
        system=request.system,
        base_url=request.base_url,
        description=request.description,
        recorded_by=request.recorded_by,
        project_id=request.project_id
    )
    return {"recording_id": recording_id, "name": request.name, "system": request.system}


@router.post("/journey/recordings/{recording_id}/steps")
async def add_journey_step(
    recording_id: str,
    request: AddStepRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Add a step to a journey recording."""
    service = JourneyComparisonService(db)
    try:
        step_type = JourneyStepType(request.step_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid step type: {request.step_type}")

    step_number = await service.add_step(
        recording_id=recording_id,
        step_type=step_type,
        selector=request.selector,
        action=request.action,
        value=request.value,
        expected_result=request.expected_result,
        screenshot_path=request.screenshot_path,
        api_request=request.api_request,
        api_response=request.api_response,
        duration_ms=request.duration_ms
    )
    return {"step_number": step_number}


@router.post("/journey/recordings/{recording_id}/finalize")
async def finalize_recording(
    recording_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Finalize and persist a recording."""
    service = JourneyComparisonService(db)
    recording = await service.finalize_recording(recording_id)
    return {
        "recording_id": recording.id,
        "name": recording.name,
        "system": recording.system,
        "step_count": len(recording.steps),
        "total_duration_ms": recording.total_duration_ms
    }


@router.get("/journey/recordings/{recording_id}")
async def get_recording(
    recording_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get a journey recording."""
    service = JourneyComparisonService(db)
    recording = await service.get_recording(recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail=f"Recording {recording_id} not found")

    return {
        "id": recording.id,
        "name": recording.name,
        "system": recording.system,
        "base_url": recording.base_url,
        "step_count": len(recording.steps),
        "total_duration_ms": recording.total_duration_ms,
        "steps": [
            {
                "step_number": s.step_number,
                "step_type": s.step_type.value,
                "action": s.action,
                "selector": s.selector
            }
            for s in recording.steps
        ]
    }


@router.post("/journey/compare")
async def compare_journeys(
    request: CompareJourneysRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Compare two journey recordings."""
    service = JourneyComparisonService(db)
    result = await service.compare_journeys(
        legacy_recording_id=request.legacy_recording_id,
        new_recording_id=request.new_recording_id,
        project_id=request.project_id,
        apply_overrides=request.apply_overrides
    )

    return {
        "comparison_id": result.id,
        "journey": result.journey_name,
        "status": result.status,
        "total_steps": result.total_steps,
        "matching": result.matching_steps,
        "mismatching": result.mismatching_steps,
        "overridden": result.overridden_steps,
        "overall_match": f"{result.overall_match_percentage}%",
        "visual_match": f"{result.visual_match_percentage}%",
        "data_match": f"{result.data_match_percentage}%"
    }


@router.get("/journey/comparisons/{comparison_id}/report")
async def get_comparison_report(
    comparison_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get detailed comparison report."""
    service = JourneyComparisonService(db)
    report = await service.generate_comparison_report(comparison_id)
    return report


@router.post("/journey/compare-all/{project_id}")
async def compare_all_journeys(
    project_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Compare all journey pairs for a project."""
    service = JourneyComparisonService(db)
    result = await service.compare_all_journeys(project_id)
    return result


@router.post("/journey/overrides")
async def create_override_rule(
    request: CreateOverrideRuleRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Create an override rule for approved differences."""
    service = JourneyComparisonService(db)
    rule_id = await service.create_override_rule(
        journey_name=request.journey_name,
        legacy_behavior=request.legacy_behavior,
        new_behavior=request.new_behavior,
        reason=request.reason,
        approved_by=request.approved_by,
        override_type=request.override_type,
        step_number=request.step_number,
        expires_at=request.expires_at,
        project_id=request.project_id
    )
    return {"rule_id": rule_id, "journey": request.journey_name, "approved_by": request.approved_by}


@router.get("/journey/overrides/{journey_name}")
async def get_override_rules(
    journey_name: str,
    include_expired: bool = False,
    db: AsyncSession = Depends(get_async_db)
):
    """Get override rules for a journey."""
    service = JourneyComparisonService(db)
    rules = await service.get_override_rules(journey_name, include_expired)
    return {
        "journey": journey_name,
        "count": len(rules),
        "rules": [
            {
                "id": r.id,
                "step_number": r.step_number,
                "override_type": r.override_type,
                "legacy_behavior": r.legacy_behavior,
                "new_behavior": r.new_behavior,
                "reason": r.reason,
                "approved_by": r.approved_by,
                "expires_at": r.expires_at.isoformat() if r.expires_at else None
            }
            for r in rules
        ]
    }


@router.delete("/journey/overrides/{rule_id}")
async def deactivate_override_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Deactivate an override rule."""
    service = JourneyComparisonService(db)
    success = await service.deactivate_override_rule(rule_id)
    return {"success": success, "rule_id": rule_id}


# ============================================
# CDC Integration Request/Response Models
# ============================================

class CreateCDCSessionRequest(BaseModel):
    name: str = Field(..., description="Session name")
    mode: str = Field(..., description="CDC mode: shadow, mirror, cutover, rollback")
    provider: str = Field("polling", description="CDC provider: debezium, aws_dms, polling, trigger")
    legacy_connection: Dict[str, str] = Field(..., description="Legacy DB connection details")
    new_connection: Dict[str, str] = Field(..., description="New DB connection details")


class AddTableMappingRequest(BaseModel):
    legacy_table: str
    new_table: str
    field_mappings: Optional[Dict[str, str]] = None
    transform_functions: Optional[Dict[str, str]] = None


class SwitchCDCModeRequest(BaseModel):
    new_mode: str = Field(..., description="Target mode: shadow, mirror, cutover, rollback")
    approved_by: str = Field("system", description="Who approved this transition (eddie for cutover/rollback)")


class ProcessEventRequest(BaseModel):
    table: str
    operation: str = Field(..., description="insert, update, delete, or snapshot")
    legacy_data: Dict[str, Any]
    primary_key: Optional[Dict[str, Any]] = None


class ResolveConflictRequest(BaseModel):
    conflict_index: int
    strategy: str = Field(..., description="legacy_wins, new_wins, merge, or manual")
    resolved_by: str = "system"
    resolved_data: Optional[Dict[str, Any]] = None


# ============================================
# CDC Integration Endpoints
# ============================================

@router.post("/cdc/sessions")
async def create_cdc_session(request: CreateCDCSessionRequest):
    """Create a new CDC synchronization session."""
    try:
        mode = CDCMode(request.mode)
        provider = CDCProvider(request.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    service = get_cdc_service()
    session = await service.create_session(
        name=request.name,
        mode=mode,
        provider=provider,
        legacy_connection=request.legacy_connection,
        new_connection=request.new_connection
    )

    return {
        "session_id": session.id,
        "name": session.name,
        "mode": session.mode.value,
        "provider": session.provider.value,
        "status": session.status
    }


@router.get("/cdc/sessions")
async def list_cdc_sessions(status: Optional[str] = None):
    """List all CDC sessions."""
    service = get_cdc_service()
    sessions = await service.list_sessions(status)
    return {
        "count": len(sessions),
        "sessions": [
            {
                "id": s.id,
                "name": s.name,
                "mode": s.mode.value,
                "provider": s.provider.value,
                "status": s.status,
                "events_processed": s.events_processed,
                "conflicts_detected": s.conflicts_detected
            }
            for s in sessions
        ]
    }


@router.get("/cdc/sessions/{session_id}")
async def get_cdc_session(session_id: str):
    """Get CDC session details."""
    service = get_cdc_service()
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return {
        "id": session.id,
        "name": session.name,
        "mode": session.mode.value,
        "provider": session.provider.value,
        "status": session.status,
        "created_at": session.created_at.isoformat(),
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "table_mappings": len(session.table_mappings),
        "events_processed": session.events_processed,
        "events_failed": session.events_failed,
        "conflicts_detected": session.conflicts_detected,
        "conflicts_resolved": session.conflicts_resolved
    }


@router.post("/cdc/sessions/{session_id}/table-mappings")
async def add_table_mapping(session_id: str, request: AddTableMappingRequest):
    """Add a table mapping to a CDC session."""
    service = get_cdc_service()
    mapping = await service.add_table_mapping(
        session_id=session_id,
        legacy_table=request.legacy_table,
        new_table=request.new_table,
        field_mappings=request.field_mappings,
        transform_functions=request.transform_functions
    )
    return {
        "legacy_table": mapping.legacy_table,
        "new_table": mapping.new_table,
        "field_mappings": mapping.field_mappings
    }


@router.post("/cdc/sessions/{session_id}/auto-detect-mappings")
async def auto_detect_mappings(session_id: str, legacy_tables: List[str]):
    """Auto-detect table mappings based on naming conventions."""
    service = get_cdc_service()
    mappings = await service.auto_detect_mappings(session_id, legacy_tables)
    return {
        "count": len(mappings),
        "mappings": [
            {"legacy": m.legacy_table, "new": m.new_table}
            for m in mappings
        ]
    }


@router.post("/cdc/sessions/{session_id}/start")
async def start_cdc_session(session_id: str):
    """Start CDC synchronization."""
    service = get_cdc_service()
    session = await service.start_session(session_id)
    return {
        "session_id": session.id,
        "status": session.status,
        "started_at": session.started_at.isoformat() if session.started_at else None
    }


@router.post("/cdc/sessions/{session_id}/stop")
async def stop_cdc_session(session_id: str):
    """Stop CDC synchronization."""
    service = get_cdc_service()
    session = await service.stop_session(session_id)
    return {
        "session_id": session.id,
        "status": session.status,
        "stopped_at": session.stopped_at.isoformat() if session.stopped_at else None
    }


@router.post("/cdc/sessions/{session_id}/pause")
async def pause_cdc_session(session_id: str):
    """Pause CDC synchronization (maintains position)."""
    service = get_cdc_service()
    session = await service.pause_session(session_id)
    return {"session_id": session.id, "status": session.status}


@router.post("/cdc/sessions/{session_id}/resume")
async def resume_cdc_session(session_id: str):
    """Resume paused CDC synchronization."""
    service = get_cdc_service()
    session = await service.resume_session(session_id)
    return {"session_id": session.id, "status": session.status}


@router.post("/cdc/sessions/{session_id}/switch-mode")
async def switch_cdc_mode(session_id: str, request: SwitchCDCModeRequest):
    """
    Switch CDC mode. Critical transitions (cutover, rollback) require approval.

    Mode transitions:
    - SHADOW -> MIRROR: Enable writes to new system
    - MIRROR -> CUTOVER: New system becomes primary
    - CUTOVER -> ROLLBACK: Revert to legacy (emergency)
    """
    try:
        new_mode = CDCMode(request.new_mode)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {request.new_mode}")

    service = get_cdc_service()
    try:
        session = await service.switch_mode(
            session_id=session_id,
            new_mode=new_mode,
            approved_by=request.approved_by
        )
        return {
            "session_id": session.id,
            "mode": session.mode.value,
            "approved_by": request.approved_by
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cdc/sessions/{session_id}/events")
async def process_cdc_event(session_id: str, request: ProcessEventRequest):
    """Process a change event (for testing/manual injection)."""
    try:
        operation = ChangeOperation(request.operation)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid operation: {request.operation}")

    from datetime import datetime
    from uuid import uuid4

    event = ChangeEvent(
        id=str(uuid4()),
        table=request.table,
        operation=operation,
        timestamp=datetime.utcnow(),
        legacy_data=request.legacy_data,
        primary_key=request.primary_key or {}
    )

    service = get_cdc_service()
    result = await service.process_event(session_id, event)
    return {
        "event_id": result.id,
        "table": result.table,
        "operation": result.operation.value,
        "sync_status": result.sync_status.value,
        "error_message": result.error_message
    }


@router.get("/cdc/sessions/{session_id}/conflicts")
async def get_cdc_conflicts(session_id: str, unresolved_only: bool = False):
    """Get conflicts for a CDC session."""
    service = get_cdc_service()
    conflicts = await service.get_conflicts(session_id, unresolved_only)
    return {
        "session_id": session_id,
        "count": len(conflicts),
        "conflicts": [
            {
                "index": i,
                "table": c.table,
                "conflict_type": c.conflict_type,
                "resolution_strategy": c.resolution_strategy,
                "resolved": c.resolved_at is not None,
                "resolved_by": c.resolved_by
            }
            for i, c in enumerate(conflicts)
        ]
    }


@router.post("/cdc/sessions/{session_id}/conflicts/resolve")
async def resolve_cdc_conflict(session_id: str, request: ResolveConflictRequest):
    """Resolve a CDC conflict."""
    service = get_cdc_service()
    try:
        conflict = await service.resolve_conflict(
            session_id=session_id,
            conflict_index=request.conflict_index,
            strategy=request.strategy,
            resolved_by=request.resolved_by,
            resolved_data=request.resolved_data
        )
        return {
            "table": conflict.table,
            "strategy": conflict.resolution_strategy,
            "resolved_by": conflict.resolved_by,
            "resolved_at": conflict.resolved_at.isoformat() if conflict.resolved_at else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cdc/sessions/{session_id}/metrics")
async def get_cdc_metrics(session_id: str):
    """Get current CDC metrics."""
    service = get_cdc_service()
    try:
        metrics = await service.get_metrics(session_id)
        return {
            "session_id": metrics.session_id,
            "timestamp": metrics.timestamp.isoformat(),
            "events_per_second": metrics.events_per_second,
            "latency_ms": metrics.latency_ms,
            "queue_depth": metrics.queue_depth,
            "tables_synced": metrics.tables_synced,
            "errors_last_hour": metrics.errors_last_hour
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/cdc/sessions/{session_id}/summary")
async def get_cdc_summary(session_id: str):
    """Get summary of CDC session."""
    service = get_cdc_service()
    try:
        summary = await service.get_session_summary(session_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================
# Status Endpoint
# ============================================

@router.get("/status")
async def get_fase24_status():
    """Get status of Fase 24 services."""
    return {
        "fase": 24,
        "name": "Data Architecture",
        "status": "active",
        "services": {
            "data_lineage": {
                "status": "active",
                "description": "Track data flow from specs to code"
            },
            "erd_generator": {
                "status": "active",
                "description": "Generate target architecture ERD",
                "output_formats": ["mermaid", "plantuml", "dbml", "json", "dot"]
            },
            "journey_comparison": {
                "status": "active",
                "description": "E2E journey comparison between legacy and new"
            },
            "cdc_integration": {
                "status": "active",
                "description": "Change Data Capture for dual-system sync",
                "modes": ["shadow", "mirror", "cutover", "rollback"],
                "providers": ["debezium", "aws_dms", "polling", "trigger"]
            }
        },
        "endpoints": {
            "lineage": [
                "/api/data-architecture/lineage/sessions",
                "/api/data-architecture/lineage/sessions/{session_id}/nodes",
                "/api/data-architecture/lineage/sessions/{session_id}/edges",
                "/api/data-architecture/lineage/sessions/{session_id}/field-mappings",
                "/api/data-architecture/lineage/sessions/{session_id}/import-brown-paper",
                "/api/data-architecture/lineage/sessions/{session_id}/impact/{node_id}",
                "/api/data-architecture/lineage/sessions/{session_id}/traceability"
            ],
            "erd": [
                "/api/data-architecture/erd/generate",
                "/api/data-architecture/erd/{diagram_id}/export",
                "/api/data-architecture/erd/{diagram_id}/statistics"
            ],
            "journey": [
                "/api/data-architecture/journey/recordings",
                "/api/data-architecture/journey/recordings/{recording_id}/steps",
                "/api/data-architecture/journey/recordings/{recording_id}/finalize",
                "/api/data-architecture/journey/compare",
                "/api/data-architecture/journey/compare-all/{project_id}",
                "/api/data-architecture/journey/overrides"
            ],
            "cdc": [
                "/api/data-architecture/cdc/sessions",
                "/api/data-architecture/cdc/sessions/{session_id}/table-mappings",
                "/api/data-architecture/cdc/sessions/{session_id}/start",
                "/api/data-architecture/cdc/sessions/{session_id}/stop",
                "/api/data-architecture/cdc/sessions/{session_id}/switch-mode",
                "/api/data-architecture/cdc/sessions/{session_id}/events",
                "/api/data-architecture/cdc/sessions/{session_id}/conflicts",
                "/api/data-architecture/cdc/sessions/{session_id}/metrics"
            ]
        }
    }
