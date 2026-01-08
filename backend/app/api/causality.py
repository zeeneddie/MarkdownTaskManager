# backend/app/api/causality.py
"""
CiRA Causality Detection API - Week 123-125

Endpoints for causality detection in requirements.

Based on:
- Paper: arXiv:2101.10766 - REFSQ 2021
- Repository: github.com/fischJan/CiRA
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.cira_service import CiRAService
from app.models.causality import (
    CausalSessionStatus,
    CausalSourceType,
    CausalRelationType,
    TestCaseType,
    TestCaseStatus,
    TestPriority,
)

router = APIRouter(prefix="/api/causality", tags=["Causality Detection"])


# ============== REQUEST SCHEMAS ==============

class CreateSessionRequest(BaseModel):
    project_id: Optional[int] = Field(None, description="Associated project ID")
    extraction_id: Optional[str] = Field(None, description="Linked extraction session ID")
    name: Optional[str] = Field(None, description="Session name")
    description: Optional[str] = Field(None, description="Session description")
    source_type: str = Field(
        CausalSourceType.REQUIREMENTS.value,
        description="Type of source: requirements, stories, acceptance_criteria"
    )
    confidence_threshold: float = Field(
        0.6,
        ge=0.0, le=1.0,
        description="Minimum confidence for relation extraction"
    )
    settings: Optional[dict] = Field(None, description="Additional settings")


class AnalyzeRequest(BaseModel):
    sentences: List[str] = Field(..., min_length=1, description="Sentences to analyze")
    source_ids: Optional[List[str]] = Field(None, description="Optional source IDs for each sentence")
    source_type: Optional[str] = Field(None, description="Type of source")


class ValidateRelationRequest(BaseModel):
    approved: bool = Field(..., description="Whether the relation is approved")
    notes: Optional[str] = Field(None, description="Validation notes")


class ExecuteTestRequest(BaseModel):
    result: str = Field(..., description="Test execution result: passed, failed, skipped, error")
    notes: Optional[str] = Field(None, description="Execution notes")


# ============== RESPONSE SCHEMAS ==============

class SessionResponse(BaseModel):
    id: str
    project_id: Optional[int]
    extraction_id: Optional[str]
    name: Optional[str]
    description: Optional[str]
    status: str
    source_type: str
    input_count: int
    causal_count: int
    non_causal_count: int
    relation_count: int
    avg_confidence: Optional[float]
    confidence_threshold: float
    causal_percentage: float
    processing_time_ms: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ClassificationResponse(BaseModel):
    id: str
    session_id: str
    source_id: Optional[str]
    source_type: Optional[str]
    sentence: str
    is_causal: bool
    confidence: float
    probability_causal: float
    probability_non_causal: float
    markers: Optional[List[str]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RelationResponse(BaseModel):
    id: str
    session_id: str
    classification_id: Optional[str]
    relation_type: str
    confidence: float
    cause_source_id: Optional[str]
    cause_text: str
    cause_entity: Optional[str]
    effect_source_id: Optional[str]
    effect_text: str
    effect_entity: Optional[str]
    causal_marker: Optional[str]
    extraction_method: str
    human_validated: bool
    human_approved: Optional[bool]
    validation_notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GraphNodeResponse(BaseModel):
    id: str
    label: str
    source_id: Optional[str]
    type: str


class GraphEdgeResponse(BaseModel):
    id: str
    source: str
    target: str
    relation_type: str
    confidence: float
    label: str


class DependencyGraphResponse(BaseModel):
    id: str
    session_id: str
    project_id: Optional[int]
    name: Optional[str]
    graph_type: str
    nodes: List[GraphNodeResponse]
    edges: List[GraphEdgeResponse]
    node_count: int
    edge_count: int
    root_nodes: Optional[List[str]]
    leaf_nodes: Optional[List[str]]
    cycles: Optional[List[List[str]]]
    topological_order: Optional[List[str]]
    suggested_sprint_order: Optional[List[List[str]]]
    has_cycles: bool
    critical_path_length: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestCaseResponse(BaseModel):
    id: str
    relation_id: str
    session_id: str
    project_id: Optional[int]
    test_type: str
    test_name: str
    description: Optional[str]
    preconditions: Optional[List[str]]
    trigger: str
    expected_result: str
    test_steps: Optional[List[dict]]
    priority: str
    tags: Optional[List[str]]
    status: str
    execution_result: Optional[str]
    execution_notes: Optional[str]
    created_at: datetime
    executed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class AnalysisResultResponse(BaseModel):
    session_id: str
    status: str
    input_count: int
    causal_count: int
    non_causal_count: int
    relation_count: int
    avg_confidence: float
    causal_percentage: float
    classifications: List[dict]
    relations: List[dict]


class SessionStatisticsResponse(BaseModel):
    session_id: str
    status: str
    input_count: int
    causal_count: int
    non_causal_count: int
    relation_count: int
    causal_percentage: float
    avg_confidence: Optional[float]
    relation_type_distribution: dict
    confidence_distribution: dict
    validation_status: dict
    processing_time_ms: Optional[int]
    created_at: Optional[str]
    completed_at: Optional[str]


# ============== SESSION ENDPOINTS ==============

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new causality analysis session.

    Sessions group causality analyses and their results.
    """
    service = CiRAService(db)

    extraction_id = None
    if request.extraction_id:
        try:
            extraction_id = UUID(request.extraction_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid extraction_id format")

    session = await service.create_session(
        project_id=request.project_id,
        extraction_id=extraction_id,
        name=request.name,
        description=request.description,
        source_type=request.source_type,
        confidence_threshold=request.confidence_threshold,
        settings=request.settings,
    )

    return SessionResponse(
        id=str(session.id),
        project_id=session.project_id,
        extraction_id=str(session.extraction_id) if session.extraction_id else None,
        name=session.name,
        description=session.description,
        status=session.status,
        source_type=session.source_type,
        input_count=session.input_count,
        causal_count=session.causal_count,
        non_causal_count=session.non_causal_count,
        relation_count=session.relation_count,
        avg_confidence=session.avg_confidence,
        confidence_threshold=session.confidence_threshold,
        causal_percentage=session.get_causal_percentage(),
        processing_time_ms=session.processing_time_ms,
        created_at=session.created_at,
        completed_at=session.completed_at,
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a causality session by ID."""
    service = CiRAService(db)

    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    session = await service.get_session(session_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        id=str(session.id),
        project_id=session.project_id,
        extraction_id=str(session.extraction_id) if session.extraction_id else None,
        name=session.name,
        description=session.description,
        status=session.status,
        source_type=session.source_type,
        input_count=session.input_count,
        causal_count=session.causal_count,
        non_causal_count=session.non_causal_count,
        relation_count=session.relation_count,
        avg_confidence=session.avg_confidence,
        confidence_threshold=session.confidence_threshold,
        causal_percentage=session.get_causal_percentage(),
        processing_time_ms=session.processing_time_ms,
        created_at=session.created_at,
        completed_at=session.completed_at,
    )


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum sessions to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """List causality sessions with optional filters."""
    service = CiRAService(db)

    sessions = await service.list_sessions(
        project_id=project_id,
        status=status,
        limit=limit,
        offset=offset,
    )

    return [
        SessionResponse(
            id=str(s.id),
            project_id=s.project_id,
            extraction_id=str(s.extraction_id) if s.extraction_id else None,
            name=s.name,
            description=s.description,
            status=s.status,
            source_type=s.source_type,
            input_count=s.input_count,
            causal_count=s.causal_count,
            non_causal_count=s.non_causal_count,
            relation_count=s.relation_count,
            avg_confidence=s.avg_confidence,
            confidence_threshold=s.confidence_threshold,
            causal_percentage=s.get_causal_percentage(),
            processing_time_ms=s.processing_time_ms,
            created_at=s.created_at,
            completed_at=s.completed_at,
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}/statistics", response_model=SessionStatisticsResponse)
async def get_session_statistics(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive statistics for a session."""
    service = CiRAService(db)

    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    try:
        stats = await service.get_session_statistics(session_uuid)
        return SessionStatisticsResponse(**stats)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== ANALYSIS ENDPOINTS ==============

@router.post("/sessions/{session_id}/analyze", response_model=AnalysisResultResponse)
async def analyze_sentences(
    session_id: str,
    request: AnalyzeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze sentences for causality.

    Classifies sentences as causal/non-causal and extracts
    cause-effect relations from causal sentences.
    """
    service = CiRAService(db)

    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    try:
        result = await service.analyze_sentences(
            session_id=session_uuid,
            sentences=request.sentences,
            source_ids=request.source_ids,
            source_type=request.source_type,
        )
        return AnalysisResultResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ============== RELATION ENDPOINTS ==============

@router.get("/sessions/{session_id}/relations", response_model=List[RelationResponse])
async def get_relations(
    session_id: str,
    relation_type: Optional[str] = Query(None, description="Filter by relation type"),
    validated: Optional[bool] = Query(None, description="Filter by validation status"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence"),
    db: AsyncSession = Depends(get_db)
):
    """Get causal relations for a session."""
    service = CiRAService(db)

    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    relations = await service.get_relations(
        session_id=session_uuid,
        relation_type=relation_type,
        validated=validated,
        min_confidence=min_confidence,
    )

    return [
        RelationResponse(
            id=str(r.id),
            session_id=str(r.session_id),
            classification_id=str(r.classification_id) if r.classification_id else None,
            relation_type=r.relation_type,
            confidence=r.confidence,
            cause_source_id=r.cause_source_id,
            cause_text=r.cause_text,
            cause_entity=r.cause_entity,
            effect_source_id=r.effect_source_id,
            effect_text=r.effect_text,
            effect_entity=r.effect_entity,
            causal_marker=r.causal_marker,
            extraction_method=r.extraction_method,
            human_validated=r.human_validated,
            human_approved=r.human_approved,
            validation_notes=r.validation_notes,
            created_at=r.created_at,
        )
        for r in relations
    ]


@router.post("/relations/{relation_id}/validate", response_model=RelationResponse)
async def validate_relation(
    relation_id: str,
    request: ValidateRelationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Validate a causal relation (human review)."""
    service = CiRAService(db)

    try:
        relation_uuid = UUID(relation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid relation_id format")

    try:
        relation = await service.validate_relation(
            relation_id=relation_uuid,
            approved=request.approved,
            notes=request.notes,
        )

        return RelationResponse(
            id=str(relation.id),
            session_id=str(relation.session_id),
            classification_id=str(relation.classification_id) if relation.classification_id else None,
            relation_type=relation.relation_type,
            confidence=relation.confidence,
            cause_source_id=relation.cause_source_id,
            cause_text=relation.cause_text,
            cause_entity=relation.cause_entity,
            effect_source_id=relation.effect_source_id,
            effect_text=relation.effect_text,
            effect_entity=relation.effect_entity,
            causal_marker=relation.causal_marker,
            extraction_method=relation.extraction_method,
            human_validated=relation.human_validated,
            human_approved=relation.human_approved,
            validation_notes=relation.validation_notes,
            created_at=relation.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== GRAPH ENDPOINTS ==============

@router.post("/sessions/{session_id}/graph", response_model=DependencyGraphResponse)
async def build_dependency_graph(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Build dependency graph from session relations.

    Analyzes causal relations to build a dependency graph
    with cycle detection, topological ordering, and
    sprint planning suggestions.
    """
    service = CiRAService(db)

    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    try:
        graph = await service.build_dependency_graph(session_uuid)

        return DependencyGraphResponse(
            id=str(graph.id),
            session_id=str(graph.session_id),
            project_id=graph.project_id,
            name=graph.name,
            graph_type=graph.graph_type,
            nodes=[GraphNodeResponse(**n) for n in graph.nodes],
            edges=[GraphEdgeResponse(**e) for e in graph.edges],
            node_count=graph.node_count,
            edge_count=graph.edge_count,
            root_nodes=graph.root_nodes,
            leaf_nodes=graph.leaf_nodes,
            cycles=graph.cycles,
            topological_order=graph.topological_order,
            suggested_sprint_order=graph.suggested_sprint_order,
            has_cycles=graph.has_cycles(),
            critical_path_length=graph.get_critical_path_length(),
            created_at=graph.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}/graph", response_model=DependencyGraphResponse)
async def get_dependency_graph(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the dependency graph for a session."""
    service = CiRAService(db)

    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    graph = await service.get_dependency_graph(session_uuid)
    if not graph:
        raise HTTPException(status_code=404, detail="No graph found for session")

    return DependencyGraphResponse(
        id=str(graph.id),
        session_id=str(graph.session_id),
        project_id=graph.project_id,
        name=graph.name,
        graph_type=graph.graph_type,
        nodes=[GraphNodeResponse(**n) for n in graph.nodes],
        edges=[GraphEdgeResponse(**e) for e in graph.edges],
        node_count=graph.node_count,
        edge_count=graph.edge_count,
        root_nodes=graph.root_nodes,
        leaf_nodes=graph.leaf_nodes,
        cycles=graph.cycles,
        topological_order=graph.topological_order,
        suggested_sprint_order=graph.suggested_sprint_order,
        has_cycles=graph.has_cycles(),
        critical_path_length=graph.get_critical_path_length(),
        created_at=graph.created_at,
    )


# ============== TEST CASE ENDPOINTS ==============

@router.post("/sessions/{session_id}/tests", response_model=List[TestCaseResponse])
async def generate_test_cases(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate test cases from causal relations.

    Creates positive, negative, and boundary tests
    for each cause-effect relation.
    """
    service = CiRAService(db)

    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    try:
        test_cases = await service.generate_test_cases(session_uuid)

        return [
            TestCaseResponse(
                id=str(tc.id),
                relation_id=str(tc.relation_id),
                session_id=str(tc.session_id),
                project_id=tc.project_id,
                test_type=tc.test_type,
                test_name=tc.test_name,
                description=tc.description,
                preconditions=tc.preconditions,
                trigger=tc.trigger,
                expected_result=tc.expected_result,
                test_steps=tc.test_steps,
                priority=tc.priority,
                tags=tc.tags,
                status=tc.status,
                execution_result=tc.execution_result,
                execution_notes=tc.execution_notes,
                created_at=tc.created_at,
                executed_at=tc.executed_at,
            )
            for tc in test_cases
        ]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sessions/{session_id}/tests", response_model=List[TestCaseResponse])
async def get_test_cases(
    session_id: str,
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    db: AsyncSession = Depends(get_db)
):
    """Get test cases for a session."""
    service = CiRAService(db)

    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    test_cases = await service.get_test_cases(
        session_id=session_uuid,
        test_type=test_type,
        status=status,
        priority=priority,
    )

    return [
        TestCaseResponse(
            id=str(tc.id),
            relation_id=str(tc.relation_id),
            session_id=str(tc.session_id),
            project_id=tc.project_id,
            test_type=tc.test_type,
            test_name=tc.test_name,
            description=tc.description,
            preconditions=tc.preconditions,
            trigger=tc.trigger,
            expected_result=tc.expected_result,
            test_steps=tc.test_steps,
            priority=tc.priority,
            tags=tc.tags,
            status=tc.status,
            execution_result=tc.execution_result,
            execution_notes=tc.execution_notes,
            created_at=tc.created_at,
            executed_at=tc.executed_at,
        )
        for tc in test_cases
    ]


# ============== METADATA ENDPOINTS ==============

@router.get("/relation-types")
async def get_relation_types():
    """Get available causal relation types."""
    return {
        "relation_types": [
            {
                "value": CausalRelationType.CAUSES.value,
                "label": "Causes",
                "description": "Story A causes Story B to happen"
            },
            {
                "value": CausalRelationType.ENABLES.value,
                "label": "Enables",
                "description": "Story A makes Story B possible"
            },
            {
                "value": CausalRelationType.BLOCKS.value,
                "label": "Blocks",
                "description": "Story A prevents Story B from happening"
            },
            {
                "value": CausalRelationType.DEPENDS_ON.value,
                "label": "Depends On",
                "description": "Story A requires Story B as a prerequisite"
            },
        ]
    }


@router.get("/source-types")
async def get_source_types():
    """Get available source types for causality analysis."""
    return {
        "source_types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in CausalSourceType
        ]
    }


@router.get("/test-types")
async def get_test_types():
    """Get available test case types."""
    return {
        "test_types": [
            {
                "value": TestCaseType.POSITIVE.value,
                "label": "Positive",
                "description": "Verify cause leads to effect"
            },
            {
                "value": TestCaseType.NEGATIVE.value,
                "label": "Negative",
                "description": "Verify without cause, no effect"
            },
            {
                "value": TestCaseType.BOUNDARY.value,
                "label": "Boundary",
                "description": "Edge case testing"
            },
        ]
    }


@router.get("/causal-markers")
async def get_causal_markers():
    """Get the list of causal markers used for detection."""
    from app.models.causality import CAUSAL_MARKERS
    return {
        "markers": CAUSAL_MARKERS,
        "total": len(CAUSAL_MARKERS),
    }


# ============== WEEK 124: MODEL MANAGEMENT ENDPOINTS ==============

class FineTuneRequest(BaseModel):
    """Request for fine-tuning the BERT model."""
    project_id: int = Field(..., description="Project ID for training data")
    use_validated_only: bool = Field(True, description="Only use human-validated relations")
    epochs: int = Field(3, ge=1, le=10, description="Number of training epochs")
    learning_rate: float = Field(2e-5, ge=1e-6, le=1e-3, description="Learning rate")
    save_path: Optional[str] = Field(None, description="Path to save model (optional)")


class CalibrateRequest(BaseModel):
    """Request for confidence calibration."""
    project_id: int = Field(..., description="Project ID for calibration data")


class FineTuneResponse(BaseModel):
    """Response from fine-tuning."""
    epochs: int
    final_train_accuracy: float
    final_val_accuracy: float
    best_val_accuracy: float
    f1_score: float
    saved_to: Optional[str]


class CalibrateResponse(BaseModel):
    """Response from calibration."""
    optimal_temperature: float
    calibration_samples: int
    project_id: int


class ModelStatusResponse(BaseModel):
    """Response for model status."""
    is_loaded: bool
    model_name: str
    model_path: Optional[str]
    device: str
    temperature: float
    max_length: int
    batch_size: int
    metadata: Optional[dict]
    config: dict

    model_config = ConfigDict(protected_namespaces=())


@router.get("/model/status", response_model=ModelStatusResponse)
async def get_model_status(db: AsyncSession = Depends(get_db)):
    """
    Get the current status of the BERT causality model.

    Week 124: Returns model configuration, loading status, and metadata.
    """
    service = CiRAService(db)
    status = await service.get_model_status()
    return ModelStatusResponse(**status)


@router.post("/model/load")
async def load_model(db: AsyncSession = Depends(get_db)):
    """
    Explicitly load the BERT model.

    Week 124: Loads the model into memory if not already loaded.
    Useful for pre-warming before analysis.
    """
    service = CiRAService(db)
    await service.ensure_model_loaded()
    status = await service.get_model_status()

    return {
        "success": status["is_loaded"],
        "message": "Model loaded successfully" if status["is_loaded"] else "Model loading failed, using rule-based fallback",
        "status": status
    }


@router.post("/model/fine-tune", response_model=FineTuneResponse)
async def fine_tune_model(
    request: FineTuneRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Fine-tune the BERT model on project-specific data.

    Week 124: Uses human-validated causal relations as training data.
    The fine-tuned model is saved and can be loaded for future analyses.

    Requires:
    - At least 10 validated relations for training
    - BERT model loaded (will load if not)
    """
    service = CiRAService(db)

    try:
        results = await service.fine_tune_model(
            project_id=request.project_id,
            use_validated_only=request.use_validated_only,
            epochs=request.epochs,
            learning_rate=request.learning_rate,
            save_path=request.save_path
        )

        return FineTuneResponse(
            epochs=results["epochs"],
            final_train_accuracy=results["final_train_accuracy"],
            final_val_accuracy=results["final_val_accuracy"],
            best_val_accuracy=results["best_val_accuracy"],
            f1_score=results["f1_score"],
            saved_to=results.get("saved_to")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fine-tuning failed: {str(e)}")


@router.post("/model/calibrate", response_model=CalibrateResponse)
async def calibrate_confidence(
    request: CalibrateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Calibrate confidence scores using temperature scaling.

    Week 124: Finds optimal temperature to make probability estimates
    better calibrated. Uses existing classifications as calibration data.

    Requires:
    - At least 50 classified sentences for calibration
    """
    service = CiRAService(db)

    try:
        results = await service.calibrate_confidence(project_id=request.project_id)
        return CalibrateResponse(**results)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calibration failed: {str(e)}")
