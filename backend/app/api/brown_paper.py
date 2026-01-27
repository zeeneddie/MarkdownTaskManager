"""
Brown Paper API

Week 57 Day 2: REST API endpoints for Brown Paper workflows.
Phase 20 (Week 128-129): Enhanced 6-phase deep analysis integration.

THREE WORKFLOW TYPES:
1. Code-Analysis (bottom-up) - Analyze existing codebase to extract structure
2. MarQed Brown-Paper (top-down) - 8-question guided workflow for migration projects
3. Enhanced Analysis (Phase 20) - 6-phase deep analysis with service integration

CODE-ANALYSIS ENDPOINTS (prefix: /api/brown-paper/sessions):
- POST /sessions         - Start analysis session
- GET  /sessions         - List sessions
- GET  /sessions/{id}    - Get session details
- POST /sessions/{id}/analyze  - Run basic analysis
- POST /sessions/{id}/enhanced-analyze  - Run 6-phase deep analysis
- GET  /sessions/{id}/dependency-graph  - Get D3.js graph visualization
- GET  /sessions/{id}/hierarchy  - Get Epic/Feature/Story/Task tree
- GET  /sessions/{id}/metrics  - Get code quality metrics
- POST /sessions/{id}/constitution  - Generate constitution
- POST /sessions/{id}/epics  - Generate epics
- POST /sessions/{id}/approve  - Approve session
- POST /sessions/{id}/reject   - Reject session

MARQED BROWN-PAPER ENDPOINTS (prefix: /api/brown-paper/marqed):
- POST /marqed/start                   - Start 8-question workflow
- GET  /marqed/{id}/question           - Get current question
- POST /marqed/{id}/answer             - Submit answer
- GET  /marqed/{id}/status             - Get full session status
- POST /marqed/{id}/analyze            - Run migration analysis (Miguel)
- POST /marqed/{id}/specification      - Generate specification (Peter)
- POST /marqed/{id}/tasks              - Generate tasks (Felix)
- GET  /marqed/{id}/export             - Export to markdown
- GET  /marqed/questions               - List all 8 questions

ENHANCED ANALYSIS ENDPOINTS (Phase 20 - prefix: /api/brown-paper/marqed):
- POST /marqed/{id}/enhanced-analyze   - Run 6-phase deep analysis
- GET  /marqed/{id}/dependency-graph   - Get D3.js graph visualization data
- GET  /marqed/{id}/hierarchy          - Get Epic/Feature/Story/Task tree
- GET  /marqed/{id}/conflicts          - Get LLM Council conflicts
- GET  /marqed/{id}/metrics            - Get code quality metrics

Enhanced Analysis Phases:
1. Code Understanding: DependencyGraph + CodeAnalysis + LayeredAnalysis
2. Domain Extraction: Peter agent extracts business domains + CAFCR mapping
3. Hierarchical Extraction: HierarchicalStoryExtractionService + CiRA
4. Deep Extraction: DeepExtractionService + LLM Council + INVEST
5. Estimation: brown_paper_estimation_service (complexity-enhanced)
6. Output: Consolidated documentation
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.services.brown_paper_service import (
    get_brown_paper_service,
    get_marqed_brown_paper_workflow,
    BrownPaperStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/brown-paper", tags=["brown-paper"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class StartSessionRequest(BaseModel):
    """Request to start a Brown Paper session."""
    application_id: int = Field(..., description="Application ID from Application Registry")


class StartSessionResponse(BaseModel):
    """Response from starting a session."""
    session_id: str
    application_id: int
    status: str
    created_at: str


class SessionSummaryResponse(BaseModel):
    """Summary of a Brown Paper session."""
    id: str
    application_id: int
    status: str
    created_at: str
    updated_at: str
    error_message: Optional[str] = None
    modules_count: int = 0
    domains_count: int = 0


class CodeModuleResponse(BaseModel):
    """Response for a code module."""
    name: str
    path: str
    module_type: str
    description: str
    classes: List[str]
    functions: List[str]
    dependencies: List[str]
    estimated_complexity: str
    business_domain: Optional[str] = None


class DocumentationInsightResponse(BaseModel):
    """Response for a documentation insight."""
    source: str
    section: str
    content: str
    insight_type: str
    confidence: float


class BusinessDomainResponse(BaseModel):
    """Response for a business domain."""
    name: str
    description: str
    modules: List[str]
    entities: List[str]
    use_cases: List[str]
    complexity: str
    priority: int


class AnalysisResponse(BaseModel):
    """Response with full analysis details."""
    application_id: int
    application_name: str
    root_path: str
    modules: List[CodeModuleResponse]
    total_classes: int
    total_functions: int
    primary_patterns: List[str]
    doc_insights: List[DocumentationInsightResponse]
    readme_summary: Optional[str]
    domains: List[BusinessDomainResponse]
    analysis_time_ms: int
    status: str


class SessionDetailResponse(BaseModel):
    """Detailed session response including analysis if available."""
    id: str
    application_id: int
    status: str
    created_at: str
    updated_at: str
    error_message: Optional[str] = None
    analysis: Optional[AnalysisResponse] = None
    constitution: Optional[Dict[str, Any]] = None
    epics: List[Dict[str, Any]] = []


class GenerateConstitutionRequest(BaseModel):
    """Request to generate constitution with optional human input."""
    mission: Optional[str] = Field(None, description="Human-provided mission statement")
    vision: Optional[str] = Field(None, description="Human-provided vision statement")


class ConstitutionResponse(BaseModel):
    """Response with generated constitution."""
    mission_vision: Dict[str, str]
    core_principles: List[Dict[str, str]]
    key_requirements: List[Dict[str, Any]]
    constraints: List[Dict[str, str]]
    risks: List[Dict[str, str]]
    scope: Dict[str, Any]
    success_criteria: List[Dict[str, str]]
    metadata: Dict[str, Any]


class EpicResponse(BaseModel):
    """Response for a generated epic."""
    id: str
    name: str
    description: str
    priority: int
    complexity: str
    source: str
    features: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class ApproveRejectRequest(BaseModel):
    """Request to approve or reject a session."""
    reviewer: str = Field(..., description="Name or ID of the reviewer")
    reason: Optional[str] = Field(None, description="Reason for rejection (required for reject)")


class EnhancedAnalysisRequestModel(BaseModel):
    """Request for enhanced 6-phase analysis."""
    tier: str = Field(
        default="STANDARD",
        description="Analysis tier: FREE, BASIC, STANDARD, PROFESSIONAL, PREMIUM"
    )
    include_phases: List[int] = Field(
        default=[1, 2, 3, 4, 5, 6],
        description="Phases to include (1-6)"
    )
    skip_vbscript: bool = Field(default=False, description="Skip VBScript analysis")
    include_cira: bool = Field(default=True, description="Include CiRA causality detection")
    generate_tests: bool = Field(default=True, description="Generate test cases")
    include_swot: bool = Field(default=True, description="Include SWOT analysis")


class EnhancedAnalysisResponseModel(BaseModel):
    """Response from enhanced analysis."""
    session_id: str
    status: str
    tier: str
    phases_completed: List[int] = []
    confidence: float = 0.0
    summary: Optional[Dict[str, Any]] = None
    phase1_result: Optional[Dict[str, Any]] = None
    phase2_result: Optional[Dict[str, Any]] = None
    phase3_result: Optional[Dict[str, Any]] = None
    phase4_result: Optional[Dict[str, Any]] = None
    phase5_result: Optional[Dict[str, Any]] = None
    dependency_graph_url: Optional[str] = None
    hierarchy_url: Optional[str] = None
    metrics_url: Optional[str] = None
    conflicts_url: Optional[str] = None
    total_duration_ms: int = 0
    errors: List[str] = []


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/sessions", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest):
    """
    Start a new Brown Paper analysis session for an application.

    This creates a session but doesn't run the analysis yet.
    Call /sessions/{id}/analyze to run the actual analysis.

    **Example Request:**
    ```json
    {
      "application_id": 1
    }
    ```
    """
    try:
        service = get_brown_paper_service()
        session = await service.start_session(request.application_id)

        return StartSessionResponse(
            session_id=session.id,
            application_id=session.application_id,
            status=session.status.value,
            created_at=session.created_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to start session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start session: {str(e)}",
        )


@router.get("/sessions", response_model=List[SessionSummaryResponse])
async def list_sessions(application_id: Optional[int] = None):
    """
    List all Brown Paper sessions.

    Optionally filter by application_id.
    Sessions are loaded from database for persistence across server restarts.
    """
    try:
        service = get_brown_paper_service()
        # Use async method to load from database
        sessions = await service.list_sessions(application_id)

        return [
            SessionSummaryResponse(
                id=s.id,
                application_id=s.application_id,
                status=s.status.value if hasattr(s.status, 'value') else s.status,
                created_at=s.created_at.isoformat() if s.created_at else None,
                updated_at=s.updated_at.isoformat() if s.updated_at else None,
                error_message=s.error_message if hasattr(s, 'error_message') else None,
                modules_count=getattr(s, 'modules_count', 0) or (len(s.analysis.modules) if s.analysis else 0),
                domains_count=getattr(s, 'domains_count', 0) or (len(s.analysis.domains) if s.analysis else 0),
            )
            for s in sessions
        ]

    except Exception as e:
        logger.error(f"Failed to list sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}",
        )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str):
    """
    Get detailed information about a Brown Paper session.

    Includes analysis results if analysis has been run.
    Loads from database for persistence across server restarts.
    """
    try:
        service = get_brown_paper_service()
        # Use async method to load from database
        session = await service.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}",
            )

        # Build analysis response if available
        analysis_response = None
        if session.analysis:
            a = session.analysis
            analysis_response = AnalysisResponse(
                application_id=a.application_id,
                application_name=a.application_name,
                root_path=a.root_path,
                modules=[
                    CodeModuleResponse(
                        name=m.name,
                        path=m.path,
                        module_type=m.module_type,
                        description=m.description,
                        classes=m.classes,
                        functions=m.functions,
                        dependencies=m.dependencies,
                        estimated_complexity=m.estimated_complexity,
                        business_domain=m.business_domain,
                    )
                    for m in a.modules
                ],
                total_classes=a.total_classes,
                total_functions=a.total_functions,
                primary_patterns=a.primary_patterns,
                doc_insights=[
                    DocumentationInsightResponse(
                        source=d.source,
                        section=d.section,
                        content=d.content,
                        insight_type=d.insight_type,
                        confidence=d.confidence,
                    )
                    for d in a.doc_insights
                ],
                readme_summary=a.readme_summary,
                domains=[
                    BusinessDomainResponse(
                        name=d.name,
                        description=d.description,
                        modules=d.modules,
                        entities=d.entities,
                        use_cases=d.use_cases,
                        complexity=d.complexity,
                        priority=d.priority,
                    )
                    for d in a.domains
                ],
                analysis_time_ms=a.analysis_time_ms,
                status=a.status.value,
            )

        return SessionDetailResponse(
            id=session.id,
            application_id=session.application_id,
            status=session.status.value,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            error_message=session.error_message,
            analysis=analysis_response,
            constitution=session.analysis.constitution if session.analysis else None,
            epics=session.analysis.epics if session.analysis else [],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}",
        )


@router.post("/sessions/{session_id}/analyze", response_model=AnalysisResponse)
async def analyze_application(session_id: str):
    """
    Run Brown Paper analysis on the application.

    This scans the codebase, analyzes documentation, and extracts
    business domains. Can take several seconds for large codebases.

    **Process:**
    1. Scan code structure (modules, classes, functions)
    2. Analyze documentation (README, docs/, docstrings)
    3. Detect architecture patterns (DDD, MVC, etc.)
    4. Extract business domains from code patterns
    """
    try:
        service = get_brown_paper_service()
        analysis = await service.analyze_application(session_id)

        return AnalysisResponse(
            application_id=analysis.application_id,
            application_name=analysis.application_name,
            root_path=analysis.root_path,
            modules=[
                CodeModuleResponse(
                    name=m.name,
                    path=m.path,
                    module_type=m.module_type,
                    description=m.description,
                    classes=m.classes,
                    functions=m.functions,
                    dependencies=m.dependencies,
                    estimated_complexity=m.estimated_complexity,
                    business_domain=m.business_domain,
                )
                for m in analysis.modules
            ],
            total_classes=analysis.total_classes,
            total_functions=analysis.total_functions,
            primary_patterns=analysis.primary_patterns,
            doc_insights=[
                DocumentationInsightResponse(
                    source=d.source,
                    section=d.section,
                    content=d.content,
                    insight_type=d.insight_type,
                    confidence=d.confidence,
                )
                for d in analysis.doc_insights
            ],
            readme_summary=analysis.readme_summary,
            domains=[
                BusinessDomainResponse(
                    name=d.name,
                    description=d.description,
                    modules=d.modules,
                    entities=d.entities,
                    use_cases=d.use_cases,
                    complexity=d.complexity,
                    priority=d.priority,
                )
                for d in analysis.domains
            ],
            analysis_time_ms=analysis.analysis_time_ms,
            status=analysis.status.value,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.post("/sessions/{session_id}/constitution", response_model=ConstitutionResponse)
async def generate_constitution(session_id: str, request: Optional[GenerateConstitutionRequest] = None):
    """
    Generate a Constitution from the analysis.

    The constitution follows the same structure as Green Paper constitutions
    for unified output. You can optionally provide human input to refine
    the auto-generated mission and vision.

    **Constitution Sections:**
    1. Mission & Vision
    2. Core Principles (from detected patterns)
    3. Key Requirements (from use cases)
    4. Constraints (from technology stack)
    5. Risks (from complexity analysis)
    6. Scope (from domains)
    7. Success Criteria
    """
    try:
        service = get_brown_paper_service()

        human_input = None
        if request:
            human_input = {}
            if request.mission:
                human_input["mission"] = request.mission
            if request.vision:
                human_input["vision"] = request.vision

        constitution = await service.generate_constitution(session_id, human_input)

        return ConstitutionResponse(**constitution)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Constitution generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Constitution generation failed: {str(e)}",
        )


@router.post("/sessions/{session_id}/epics", response_model=List[EpicResponse])
async def generate_epics(session_id: str):
    """
    Generate Epics from the analyzed domains.

    Each business domain becomes an Epic, with Features derived
    from the identified use cases.

    **Epic Structure:**
    - Epic = Business Domain
    - Features = Use Case Groups (CRUD ops, specific functions)
    - Stories = Individual Use Cases
    """
    try:
        service = get_brown_paper_service()
        epics = await service.generate_epics(session_id)

        return [
            EpicResponse(
                id=e["id"],
                name=e["name"],
                description=e["description"],
                priority=e["priority"],
                complexity=e["complexity"],
                source=e["source"],
                features=e["features"],
                metadata=e["metadata"],
            )
            for e in epics
        ]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Epic generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Epic generation failed: {str(e)}",
        )


@router.post("/sessions/{session_id}/approve")
async def approve_session(session_id: str, request: ApproveRejectRequest):
    """
    Approve a Brown Paper session after review.

    Once approved, the generated Constitution and Epics can be
    linked to the actual project hierarchy.
    """
    try:
        service = get_brown_paper_service()
        success = await service.approve_session(session_id, request.reviewer)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session cannot be approved in current state",
            )

        return {"status": "approved", "session_id": session_id, "reviewer": request.reviewer}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approval failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Approval failed: {str(e)}",
        )


@router.post("/sessions/{session_id}/reject")
async def reject_session(session_id: str, request: ApproveRejectRequest):
    """
    Reject a Brown Paper session.

    Requires a reason for rejection. The session can be re-analyzed
    or a new session can be started.
    """
    if not request.reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reason is required for rejection",
        )

    try:
        service = get_brown_paper_service()
        success = await service.reject_session(session_id, request.reviewer, request.reason)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}",
            )

        return {
            "status": "rejected",
            "session_id": session_id,
            "reviewer": request.reviewer,
            "reason": request.reason,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rejection failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rejection failed: {str(e)}",
        )


# ============================================================================
# ENHANCED ANALYSIS ENDPOINTS (Sessions)
# ============================================================================

@router.post("/sessions/{session_id}/enhanced-analyze", response_model=EnhancedAnalysisResponseModel)
async def sessions_enhanced_analysis(
    session_id: str,
    request: EnhancedAnalysisRequestModel
):
    """
    Start 6-phase enhanced analysis for a Brown Paper session.

    This endpoint integrates multiple services for deep code analysis:
    - Phase 1: DependencyGraph + CodeAnalysis + LayeredAnalysis
    - Phase 2: Domain Extraction (Peter agent)
    - Phase 3: HierarchicalStoryExtractionService
    - Phase 4: DeepExtractionService + LLM Council
    - Phase 5: brown_paper_estimation_service (enhanced)
    - Phase 6: Output consolidation

    The phases run depend on the tier:
    - FREE: Phase 1 only
    - BASIC: Phases 1-2
    - STANDARD: Phases 1-3
    - PROFESSIONAL: Phases 1-5
    - PREMIUM: All 6 phases with Human Review

    **Example Request:**
    ```json
    {
      "tier": "STANDARD",
      "include_phases": [1, 2, 3, 4, 5, 6],
      "skip_vbscript": false,
      "include_cira": true,
      "generate_tests": true,
      "include_swot": true
    }
    ```
    """
    from app.database import AsyncSessionLocal
    from app.models.brown_paper_enhanced import (
        EnhancedAnalysisTier,
        EnhancedAnalysisRequest,
        EnhancedAnalysisOptions,
    )

    try:
        service = get_brown_paper_service()

        # Verify session exists
        session = await service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}",
            )

        # Convert tier string to enum
        try:
            tier_enum = EnhancedAnalysisTier(request.tier.upper())
        except ValueError:
            tier_enum = EnhancedAnalysisTier.STANDARD

        # Build request
        enhanced_request = EnhancedAnalysisRequest(
            tier=tier_enum,
            include_phases=request.include_phases,
            options=EnhancedAnalysisOptions(
                skip_vbscript=request.skip_vbscript,
                include_cira=request.include_cira,
                generate_tests=request.generate_tests,
                include_swot=request.include_swot,
            )
        )

        async with AsyncSessionLocal() as db:
            result = await service.run_enhanced_analysis(
                session_id=session_id,
                request=enhanced_request,
                db=db
            )

        # Convert dataclasses to dict for response
        return EnhancedAnalysisResponseModel(
            session_id=result.session_id,
            status=result.status,
            tier=result.tier.value,
            phases_completed=result.phases_completed,
            confidence=result.confidence,
            summary=vars(result.summary) if result.summary else None,
            phase1_result=vars(result.phase1_result) if result.phase1_result else None,
            phase2_result=vars(result.phase2_result) if result.phase2_result else None,
            phase3_result=vars(result.phase3_result) if result.phase3_result else None,
            phase4_result=vars(result.phase4_result) if result.phase4_result else None,
            phase5_result=vars(result.phase5_result) if result.phase5_result else None,
            dependency_graph_url=result.dependency_graph_url,
            hierarchy_url=result.hierarchy_url,
            metrics_url=result.metrics_url,
            conflicts_url=result.conflicts_url,
            total_duration_ms=result.total_duration_ms,
            errors=result.errors,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhanced analysis failed: {str(e)}",
        )


@router.get("/sessions/{session_id}/dependency-graph")
async def sessions_dependency_graph(session_id: str):
    """
    Get dependency graph visualization data for a session.

    Returns graph nodes and edges in D3.js-compatible format.
    """
    try:
        service = get_brown_paper_service()
        session = await service.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}",
            )

        # Check if enhanced analysis has been run
        enhanced = getattr(session, 'enhanced_analysis', None)
        if not enhanced:
            return {
                "session_id": session_id,
                "has_graph": False,
                "message": "Run enhanced-analyze first to generate dependency graph",
            }

        phase1 = enhanced.get('phase1_result', {}) if isinstance(enhanced, dict) else {}
        dep_graph = phase1.get('dependency_graph', {})

        return {
            "session_id": session_id,
            "has_graph": bool(dep_graph),
            "graph": dep_graph,
            "nodes": dep_graph.get('nodes', []),
            "edges": dep_graph.get('edges', []),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dependency graph: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dependency graph: {str(e)}",
        )


@router.get("/sessions/{session_id}/hierarchy")
async def sessions_hierarchy(session_id: str):
    """
    Get Epic/Feature/Story/Task hierarchy for a session.

    Returns the hierarchical breakdown generated by enhanced analysis.
    """
    try:
        service = get_brown_paper_service()
        session = await service.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}",
            )

        # Check if enhanced analysis has been run
        enhanced = getattr(session, 'enhanced_analysis', None)
        if not enhanced:
            return {
                "session_id": session_id,
                "has_hierarchy": False,
                "message": "Run enhanced-analyze first to generate hierarchy",
            }

        phase3 = enhanced.get('phase3_result', {}) if isinstance(enhanced, dict) else {}
        phase4 = enhanced.get('phase4_result', {}) if isinstance(enhanced, dict) else {}

        return {
            "session_id": session_id,
            "has_hierarchy": bool(phase3 or phase4),
            "epics": phase3.get('epics', []) or phase4.get('epics', []),
            "features": phase3.get('features', []) or phase4.get('features', []),
            "stories": phase3.get('stories', []) or phase4.get('stories', []),
            "tasks": phase4.get('tasks', []),
            "summary": {
                "total_epics": len(phase3.get('epics', []) or phase4.get('epics', [])),
                "total_features": len(phase3.get('features', []) or phase4.get('features', [])),
                "total_stories": len(phase3.get('stories', []) or phase4.get('stories', [])),
                "total_tasks": len(phase4.get('tasks', [])),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get hierarchy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get hierarchy: {str(e)}",
        )


@router.get("/sessions/{session_id}/metrics")
async def sessions_metrics(session_id: str):
    """
    Get code quality metrics for a session.

    Returns metrics from code analysis and estimation phases.
    """
    try:
        service = get_brown_paper_service()
        session = await service.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}",
            )

        # Check if enhanced analysis has been run
        enhanced = getattr(session, 'enhanced_analysis', None)
        if not enhanced:
            return {
                "session_id": session_id,
                "has_metrics": False,
                "message": "Run enhanced-analyze first to generate metrics",
            }

        phase1 = enhanced.get('phase1_result', {}) if isinstance(enhanced, dict) else {}
        phase5 = enhanced.get('phase5_result', {}) if isinstance(enhanced, dict) else {}

        return {
            "session_id": session_id,
            "has_metrics": bool(phase1 or phase5),
            "code_analysis": phase1.get('code_analysis', {}),
            "layered_analysis": phase1.get('layered_analysis', {}),
            "estimation": {
                "total_fp": phase5.get('total_fp', 0),
                "total_sp": phase5.get('total_sp', 0),
                "estimated_hours": phase5.get('estimated_hours', 0),
                "complexity_multiplier": phase5.get('complexity_multiplier', 1.0),
            },
            "confidence": enhanced.get('confidence', 0),
            "phases_completed": enhanced.get('phases_completed', []),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}",
        )


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get("/patterns")
async def list_architecture_patterns():
    """
    List all architecture patterns that can be detected.

    Use this for documentation and UI reference.
    """
    patterns = {
        "ddd": {
            "name": "Domain-Driven Design",
            "description": "Code organized around domain concepts and bounded contexts",
            "indicators": ["domain", "aggregate", "value_object", "repository", "entity"],
        },
        "mvc": {
            "name": "Model-View-Controller",
            "description": "Separation of data, presentation, and business logic",
            "indicators": ["model", "view", "controller"],
        },
        "layered": {
            "name": "Layered Architecture",
            "description": "Horizontal layers with clear responsibilities",
            "indicators": ["presentation", "application", "domain", "infrastructure"],
        },
        "microservices": {
            "name": "Microservices",
            "description": "Distributed services with independent deployment",
            "indicators": ["service", "gateway", "discovery", "config"],
        },
        "cqrs": {
            "name": "Command Query Responsibility Segregation",
            "description": "Separate read and write models",
            "indicators": ["command", "query", "handler", "event"],
        },
        "hexagonal": {
            "name": "Hexagonal (Ports & Adapters)",
            "description": "Core domain isolated from external concerns",
            "indicators": ["port", "adapter", "application", "domain"],
        },
    }

    return {"patterns": patterns}


@router.get("/module-types")
async def list_module_types():
    """
    List all module types that can be detected.

    Use this for documentation and UI reference.
    """
    types = {
        "service": "Business logic and service layer components",
        "repository": "Data access and persistence components",
        "model": "Domain entities and data models",
        "controller": "HTTP handlers and request routing",
        "api": "API endpoint definitions",
        "util": "Utility functions and helpers",
        "config": "Configuration and settings",
        "test": "Test files and test utilities",
        "migration": "Database migrations",
    }

    return {"module_types": types}


# ============================================================================
# MARQED BROWN-PAPER WORKFLOW ENDPOINTS (8-Question Migration Planning)
# ============================================================================
#
# These endpoints implement the MarQed Brown-Paper workflow for migration projects.
# Unlike the code-analysis endpoints above (bottom-up), these are top-down planning
# endpoints that guide the user through 8 strategic questions.
#
# Flow:
# 1. POST /marqed/start              - Start interactive session
# 2. GET  /marqed/{id}/question      - Get current question
# 3. POST /marqed/{id}/answer        - Submit answer, advance to next
# 4. POST /marqed/{id}/analyze       - Run migration analysis (Miguel agent)
# 5. POST /marqed/{id}/specification - Generate specification (Peter agent)
# 6. POST /marqed/{id}/tasks         - Generate task hierarchy (Felix agent)
# 7. GET  /marqed/{id}/export        - Export to markdown
# ============================================================================


class MarQedStartRequest(BaseModel):
    """Request to start a MarQed Brown-Paper session."""
    project_name: str = Field(..., description="Name of the migration project")
    project_path: Optional[str] = Field(
        None,
        description="Path to the project source code (optional)",
        alias="source_path"
    )

    model_config = {"populate_by_name": True}  # Allow both project_path and source_path


class MarQedStartResponse(BaseModel):
    """Response from starting a MarQed session."""
    session_id: str
    project_name: str
    total_questions: int
    current_question: int
    status: str


class MarQedQuestionResponse(BaseModel):
    """Response with current question details."""
    question_number: int
    total_questions: int
    question: str
    description: str
    agent: str
    required: bool
    min_length: int
    is_complete: bool


class MarQedAnswerRequest(BaseModel):
    """Request to submit an answer."""
    answer: str = Field(..., min_length=30, description="Answer to the current question (min 30 chars)")


class MarQedAnswerResponse(BaseModel):
    """Response after submitting an answer."""
    accepted: bool
    question_answered: int
    next_question: Optional[int]
    is_complete: bool
    message: str


class MarQedStatusResponse(BaseModel):
    """Full session status."""
    session_id: str
    project_name: str
    status: str
    current_question: int
    total_questions: int
    answers: Dict[str, str]
    migration_analysis: Optional[Dict[str, Any]] = None
    specification: Optional[Dict[str, Any]] = None
    tasks: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str


class MarQedAnalysisResponse(BaseModel):
    """Response from migration analysis."""
    success: bool = True
    complexity: str
    complexity_justification: str
    risk_register: List[Dict[str, Any]]
    recommended_phases: List[Dict[str, Any]]
    technical_spikes: List[str]
    go_no_go_checkpoints: List[str]


class MarQedSpecificationResponse(BaseModel):
    """Response from specification generation."""
    project_name: str
    mission: str
    vision: str
    scope: Dict[str, Any]
    requirements: Dict[str, Any]  # {"functional": [...], "non_functional": [...]}
    constraints: List[str]  # List of constraint strings
    success_criteria: List[str]  # List of success criteria strings


class MarQedTasksResponse(BaseModel):
    """Response from task generation."""
    epics: List[Dict[str, Any]]
    total_epics: int
    total_features: int
    total_stories: int
    total_story_points: int
    estimated_fp: float
    fp_confidence: float = 0.0
    fp_analysis: Optional[Dict[str, Any]] = None


@router.post("/marqed/start", response_model=MarQedStartResponse)
async def marqed_start_session(request: MarQedStartRequest):
    """
    Start a new MarQed Brown-Paper session for migration planning.

    This begins the interactive 8-question workflow that guides the user
    through defining a brownfield/migration project.

    **The 8 Strategic Questions:**
    1. Legacy System Analysis - What exists today?
    2. Migration Target - What is the end state?
    3. Migration Strategy - How will we get there?
    4. Data Migration - How do we handle data?
    5. Problem Statement - Why are we doing this?
    6. Stakeholders - Who is affected?
    7. Success Criteria - How do we measure success?
    8. Timeline & Constraints - What are the limitations?

    **Example Request:**
    ```json
    {
      "project_name": "Legacy System Migration",
      "project_path": "/opt/projects/legacy-system"
    }
    ```
    """
    try:
        workflow = get_marqed_brown_paper_workflow()
        # Use async version for database persistence (required for restart functionality)
        session = await workflow.start_session(
            project_name=request.project_name,
            project_path=request.project_path,
            customer_id=getattr(request, 'customer_id', None)
        )

        return MarQedStartResponse(
            session_id=session.id,
            project_name=session.project_name,
            total_questions=session.total_questions,
            current_question=session.current_question,
            status=session.status,
        )

    except Exception as e:
        logger.error(f"Failed to start MarQed session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start MarQed session: {str(e)}",
        )


@router.get("/marqed/{session_id}/question", response_model=MarQedQuestionResponse)
async def marqed_get_question(session_id: str):
    """
    Get the current question for the MarQed session.

    Returns the question text, which agent will process the answer,
    a description, and validation requirements.
    """
    # Agent mapping for each question
    AGENT_MAPPING = {
        1: "Miguel",  # Legacy System Analysis
        2: "Miguel",  # Migration Target
        3: "Miguel",  # Migration Strategy
        4: "Miguel",  # Data Migration
        5: "Peter",   # Problem Statement
        6: "Peter",   # Stakeholders
        7: "Peter",   # Success Criteria
        8: "Felix",   # Timeline & Constraints
    }

    try:
        workflow = get_marqed_brown_paper_workflow()
        question = await workflow.get_current_question(session_id)

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found or all questions answered: {session_id}",
            )

        q_num = question["question_number"]
        total_q = question.get("total_questions", 8)
        return MarQedQuestionResponse(
            question_number=q_num,
            total_questions=total_q,
            question=question["question"],
            description=question.get("description", ""),
            agent=AGENT_MAPPING.get(q_num, "Felix"),
            required=question.get("required", True),
            min_length=question.get("min_length", 30),
            is_complete=q_num > total_q,  # All questions answered
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get MarQed question: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get question: {str(e)}",
        )


@router.get("/marqed/{session_id}/question-with-context")
async def marqed_get_question_with_context(session_id: str):
    """
    Get the current question with Vector DB context for answer assistance.

    Week 143: Enhanced question retrieval that includes:
    - Question details (same as /question endpoint)
    - Relevant architecture documentation from Vector DB
    - Related code locations
    - Top 5 most relevant documents

    Use this endpoint when you want AI agents to have context for formulating answers.
    """
    # Agent mapping for each question
    AGENT_MAPPING = {
        1: "Miguel",  # Legacy System Analysis
        2: "Miguel",  # Migration Target
        3: "Miguel",  # Migration Strategy
        4: "Miguel",  # Data Migration
        5: "Peter",   # Problem Statement
        6: "Peter",   # Stakeholders
        7: "Peter",   # Success Criteria
        8: "Felix",   # Timeline & Constraints
    }

    try:
        workflow = get_marqed_brown_paper_workflow()
        question = await workflow.get_current_question_with_context(session_id)

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found or all questions answered: {session_id}",
            )

        q_num = question["question_number"]
        total_q = question.get("total_questions", 8)

        return {
            "question_number": q_num,
            "total_questions": total_q,
            "question": question["question"],
            "description": question.get("description", ""),
            "agent": AGENT_MAPPING.get(q_num, "Felix"),
            "required": question.get("required", True),
            "min_length": question.get("min_length", 30),
            "is_complete": q_num > total_q,
            "vector_context": question.get("vector_context", {"context_available": False}),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get MarQed question with context: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get question with context: {str(e)}",
        )


@router.get("/marqed/{session_id}/vector-context")
async def marqed_get_vector_context(session_id: str):
    """
    Get the full Vector DB context for a MarQed session.

    Week 143: Returns all fetched context including:
    - Architecture summary
    - All relevant documents with relevance scores
    - Code locations extracted from documentation

    This is the complete context fetched at session start.
    """
    try:
        workflow = get_marqed_brown_paper_workflow()
        context = workflow.get_session_vector_context(session_id)

        if context is None:
            # Check if session exists (use async for database fallback)
            session = await workflow.get_session(session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session not found: {session_id}",
                )
            # Session exists but no context
            return {
                "session_id": session_id,
                "context_available": False,
                "message": "No Vector DB context was fetched for this session"
            }

        return {
            "session_id": session_id,
            "context_available": True,
            **context
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get MarQed vector context: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vector context: {str(e)}",
        )


@router.post("/marqed/{session_id}/answer", response_model=MarQedAnswerResponse)
async def marqed_submit_answer(session_id: str, request: MarQedAnswerRequest):
    """
    Submit an answer to the current question.

    The answer is validated and stored. If accepted, the session
    advances to the next question. After all 8 questions are answered,
    you can proceed to migration analysis.

    **Minimum answer length:** 30 characters
    """
    try:
        workflow = get_marqed_brown_paper_workflow()
        # Use async version for database persistence (required for restart functionality)
        result = await workflow.submit_answer(session_id, request.answer)

        # Handle error responses from service
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        # Map service response to API response
        accepted = result.get("success", False)
        question_answered = result.get("answered_question", 0)
        is_complete = result.get("questions_complete", False)

        # Get next question number if available
        next_q = result.get("next_question")
        next_q_num = next_q.get("question_number") if next_q else None

        # Build appropriate message
        if is_complete:
            message = "All 8 questions answered. Ready for migration analysis."
        else:
            message = f"Answer accepted for question {question_answered}. Next: question {next_q_num}."

        return MarQedAnswerResponse(
            accepted=accepted,
            question_answered=question_answered,
            next_question=next_q_num,
            is_complete=is_complete,
            message=message,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to submit MarQed answer: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit answer: {str(e)}",
        )


@router.get("/marqed/{session_id}/status", response_model=MarQedStatusResponse)
async def marqed_get_status(session_id: str):
    """
    Get full status of a MarQed Brown-Paper session.

    Includes all answers, analysis results, specifications, and tasks
    if they have been generated.
    """
    try:
        workflow = get_marqed_brown_paper_workflow()
        # Use async version for database fallback when not in cache
        session = await workflow.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}",
            )

        # Convert answers from Dict[int, MarQedAnswer] to Dict[str, str]
        answers_dict = {
            f"Q{k}": v.answer for k, v in session.answers.items()
        }

        # Convert migration_analysis to dict if present
        migration_analysis_dict = None
        if session.migration_analysis:
            ma = session.migration_analysis
            migration_analysis_dict = {
                "complexity": ma.complexity,
                "complexity_justification": ma.complexity_justification,
                "risk_register": ma.risk_register,
                "recommended_phases": ma.recommended_phases,
                "technical_spikes": ma.technical_spikes,
                "go_no_go_checkpoints": ma.go_no_go_checkpoints,
            }

        return MarQedStatusResponse(
            session_id=session.id,
            project_name=session.project_name,
            status=session.status,
            current_question=session.current_question,
            total_questions=session.total_questions,
            answers=answers_dict,
            migration_analysis=migration_analysis_dict,
            specification=session.specification,
            tasks=session.tasks,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get MarQed status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}",
        )


@router.post("/marqed/{session_id}/analyze", response_model=MarQedAnalysisResponse)
async def marqed_run_analysis(session_id: str):
    """
    Run migration analysis using the Miguel agent.

    This analyzes all 8 answers and generates:
    - Complexity assessment (LOW, MEDIUM, HIGH, VERY_HIGH)
    - Risk register with mitigations
    - Recommended migration phases
    - Technical spikes needed
    - Go/No-Go checkpoints

    **Requires:** All 8 questions must be answered first.
    """
    try:
        workflow = get_marqed_brown_paper_workflow()
        result = await workflow.run_migration_analysis(session_id)

        # BUG-001 FIX: MigrationAnalysisResult now has success field
        return MarQedAnalysisResponse(
            success=result.success,
            complexity=result.complexity,
            complexity_justification=result.complexity_justification,
            risk_register=result.risk_register,
            recommended_phases=result.recommended_phases,
            technical_spikes=result.technical_spikes,
            go_no_go_checkpoints=result.go_no_go_checkpoints,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"MarQed analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.post("/marqed/{session_id}/specification", response_model=MarQedSpecificationResponse)
async def marqed_generate_specification(session_id: str):
    """
    Generate project specification using the Peter (PO) agent.

    This transforms the answers and migration analysis into a
    structured specification document with:
    - Mission & Vision statements
    - Scope definition (in/out of scope)
    - Requirements (functional & non-functional)
    - Constraints
    - Success criteria

    **Requires:** Migration analysis must be completed first.
    """
    try:
        workflow = get_marqed_brown_paper_workflow()
        result = await workflow.generate_specification(session_id)

        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Specification generation failed"),
            )

        spec = result["specification"]
        return MarQedSpecificationResponse(
            project_name=spec["project_name"],
            mission=spec["mission"],
            vision=spec["vision"],
            scope=spec["scope"],
            requirements=spec["requirements"],
            constraints=spec["constraints"],
            success_criteria=spec["success_criteria"],
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"MarQed specification failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Specification generation failed: {str(e)}",
        )


@router.post("/marqed/{session_id}/tasks", response_model=MarQedTasksResponse)
async def marqed_generate_tasks(session_id: str):
    """
    Generate task hierarchy using the Felix (Architect) agent.

    This creates a complete project structure:
    - Epics (major migration phases)
    - Features (functional groupings)
    - Stories (individual work items)
    - Function Point estimates

    **Requires:** Specification must be completed first.
    """
    try:
        workflow = get_marqed_brown_paper_workflow()
        result = await workflow.generate_tasks(session_id)

        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Task generation failed"),
            )

        tasks = result["tasks"]
        return MarQedTasksResponse(
            epics=tasks["epics"],
            total_epics=tasks["summary"]["total_epics"],
            total_features=tasks["summary"]["total_features"],
            total_stories=tasks["summary"]["total_stories"],
            total_story_points=tasks["summary"]["total_story_points"],
            estimated_fp=tasks["summary"]["estimated_fp"],
            fp_confidence=tasks["summary"].get("fp_confidence", 0.0),
            fp_analysis=tasks.get("fp_analysis"),
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"MarQed task generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task generation failed: {str(e)}",
        )


@router.get("/marqed/{session_id}/export")
async def marqed_export_markdown(session_id: str):
    """
    Export the complete MarQed Brown-Paper session to markdown.

    This generates a PROJECT_CONSTITUTION.md file that can be saved
    to the project's documentation folder.

    **Includes:**
    - All 8 question answers
    - Migration analysis results
    - Specification document
    - Task hierarchy
    - Timeline and risk information
    """
    try:
        workflow = get_marqed_brown_paper_workflow()
        markdown = workflow.export_to_markdown(session_id)

        if not markdown:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}",
            )

        return {
            "session_id": session_id,
            "filename": "PROJECT_CONSTITUTION.md",
            "content": markdown,
            "content_length": len(markdown),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MarQed export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}",
        )


@router.get("/marqed/questions")
async def marqed_list_questions():
    """
    List all 8 MarQed Brown-Paper questions.

    Use this for documentation, UI reference, or previewing
    the workflow before starting a session.
    """
    from app.services.brown_paper_service import MARQED_QUESTIONS

    # Agent mapping for each question
    AGENT_MAPPING = {
        1: "Miguel",  # Legacy System Analysis
        2: "Miguel",  # Migration Target
        3: "Miguel",  # Migration Strategy
        4: "Miguel",  # Data Migration
        5: "Peter",   # Problem Statement
        6: "Peter",   # Stakeholders
        7: "Peter",   # Success Criteria
        8: "Felix",   # Timeline & Constraints
    }

    questions = []
    for num, q in sorted(MARQED_QUESTIONS.items()):
        questions.append({
            "number": num,
            "question": q["question"],
            "description": q.get("description", ""),
            "agent": AGENT_MAPPING.get(num, "Felix"),
            "required": q.get("required", True),
            "min_length": q.get("min_length", 30),
        })

    return {
        "total_questions": len(questions),
        "workflow_type": "BROWN_PAPER",
        "description": "MarQed Brown-Paper workflow for brownfield/migration projects",
        "questions": questions,
    }


# ============================================================================
# PHASE 20: BROWN PAPER ENHANCED - 6-PHASE DEEP ANALYSIS ENDPOINTS (MARQED)
# ============================================================================

@router.post("/marqed/{session_id}/enhanced-analyze", response_model=EnhancedAnalysisResponseModel)
async def start_enhanced_analysis(
    session_id: str,
    request: EnhancedAnalysisRequestModel
):
    """
    Start 6-phase enhanced analysis for a MarQed session.

    This endpoint integrates 5 existing services:
    - Phase 1: DependencyGraph + CodeAnalysis + LayeredAnalysis
    - Phase 2: Domain Extraction (Peter agent)
    - Phase 3: HierarchicalStoryExtractionService
    - Phase 4: DeepExtractionService + LLM Council
    - Phase 5: brown_paper_estimation_service (enhanced)
    - Phase 6: Output consolidation

    The phases run depend on the tier:
    - FREE: Phase 1 only
    - BASIC: Phases 1-2
    - STANDARD: Phases 1-3
    - PROFESSIONAL: Phases 1-5
    - PREMIUM: All 6 phases with Human Review
    """
    from app.database import AsyncSessionLocal
    from app.models.brown_paper_enhanced import (
        EnhancedAnalysisTier,
        EnhancedAnalysisRequest,
        EnhancedAnalysisOptions,
    )

    try:
        service = get_brown_paper_service()

        # Convert tier string to enum
        try:
            tier_enum = EnhancedAnalysisTier(request.tier.upper())
        except ValueError:
            tier_enum = EnhancedAnalysisTier.STANDARD

        # Build request
        enhanced_request = EnhancedAnalysisRequest(
            tier=tier_enum,
            include_phases=request.include_phases,
            options=EnhancedAnalysisOptions(
                skip_vbscript=request.skip_vbscript,
                include_cira=request.include_cira,
                generate_tests=request.generate_tests,
                include_swot=request.include_swot,
            )
        )

        async with AsyncSessionLocal() as db:
            result = await service.run_enhanced_analysis(
                session_id=session_id,
                request=enhanced_request,
                db=db
            )

        # Convert dataclasses to dict for response
        return EnhancedAnalysisResponseModel(
            session_id=result.session_id,
            status=result.status,
            tier=result.tier.value,
            phases_completed=result.phases_completed,
            confidence=result.confidence,
            summary=vars(result.summary) if result.summary else None,
            phase1_result=vars(result.phase1_result) if result.phase1_result else None,
            phase2_result=vars(result.phase2_result) if result.phase2_result else None,
            phase3_result=vars(result.phase3_result) if result.phase3_result else None,
            phase4_result=vars(result.phase4_result) if result.phase4_result else None,
            phase5_result=vars(result.phase5_result) if result.phase5_result else None,
            dependency_graph_url=result.dependency_graph_url,
            hierarchy_url=result.hierarchy_url,
            metrics_url=result.metrics_url,
            conflicts_url=result.conflicts_url,
            total_duration_ms=result.total_duration_ms,
            errors=result.errors,
        )

    except Exception as e:
        logger.error(f"Enhanced analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhanced analysis failed: {str(e)}",
        )


@router.get("/marqed/{session_id}/dependency-graph")
async def get_dependency_graph(session_id: str):
    """
    Get dependency graph visualization data for a session.

    Returns graph nodes and edges in D3.js-compatible format.
    """
    try:
        service = get_brown_paper_service()
        session = await service.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )

        # Check if enhanced analysis has been run
        if not hasattr(session, 'enhanced_analysis') or not session.enhanced_analysis:
            # Try to get from stored analysis
            if hasattr(session, 'analysis') and session.analysis:
                return {
                    "session_id": session_id,
                    "has_graph": False,
                    "message": "Run enhanced-analyze first to generate dependency graph",
                    "fallback": {
                        "modules": len(getattr(session.analysis, 'modules', []))
                    }
                }

        # Return cached graph data if available
        enhanced = getattr(session, 'enhanced_analysis', {})
        phase1 = enhanced.get('phase1_result', {}) if isinstance(enhanced, dict) else {}
        dep_graph = phase1.get('dependency_graph', {})

        return {
            "session_id": session_id,
            "has_graph": bool(dep_graph),
            "graph": dep_graph,
            "nodes": dep_graph.get('nodes', []),
            "edges": dep_graph.get('edges', []),
            "metrics": dep_graph.get('metrics', {}),
            "circular_dependencies": dep_graph.get('circular_dependencies', []),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get dependency graph failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dependency graph: {str(e)}",
        )


@router.get("/marqed/{session_id}/foundation")
async def get_foundation(session_id: str):
    """
    Get foundation/infrastructure modules for a session.

    Returns detected foundation modules grouped by category:
    - security: Authentication, authorization, permissions
    - database: Data access layer, repositories
    - ui_components: Shared UI, layouts, templates
    - shared_services: Utilities, helpers, procedures
    - infrastructure: Config, logging, caching
    - admin: Administration modules

    This data is used by MIGRATION_ENHANCED to determine migration order.
    """
    try:
        # Try regular BrownPaper session first
        service = get_brown_paper_service()
        # Use async version for database fallback
        session = await service.get_session(session_id)

        # If not found, try MarQed workflow session
        if not session:
            workflow = get_marqed_brown_paper_workflow()
            session = await workflow.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found in BrownPaper or MarQed workflow",
            )

        # Check for enhanced analysis results
        enhanced = getattr(session, 'enhanced_analysis', None)
        if not enhanced:
            enhanced = {}
        phase1 = enhanced.get('phase1_result', {}) if isinstance(enhanced, dict) else {}
        foundation = phase1.get('foundation', {})

        if not foundation:
            return {
                "session_id": session_id,
                "has_foundation": False,
                "message": "Foundation detection not yet run. Execute enhanced-analyze first.",
            }

        return {
            "session_id": session_id,
            "has_foundation": True,
            "foundation_epic": foundation.get('foundation_epic', {}),
            "foundation_modules": foundation.get('foundation_modules', []),
            "non_foundation_modules": foundation.get('non_foundation_modules', []),
            "detection_stats": foundation.get('detection_stats', {}),
            "summary": {
                "total_foundation": len(foundation.get('foundation_modules', [])),
                "total_business": len(foundation.get('non_foundation_modules', [])),
                "categories": foundation.get('detection_stats', {}).get('categories', {}),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get foundation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get foundation: {str(e)}",
        )


@router.get("/marqed/{session_id}/hierarchy")
async def get_hierarchy(session_id: str):
    """
    Get Epic/Feature/Story/Task hierarchy for a session.

    Returns hierarchical structure extracted from code analysis.
    """
    try:
        service = get_brown_paper_service()
        session = await service.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )

        # Check for enhanced analysis results
        enhanced = getattr(session, 'enhanced_analysis', {})
        phase3 = enhanced.get('phase3_result', {}) if isinstance(enhanced, dict) else {}
        extraction = phase3.get('extraction_result', {})

        return {
            "session_id": session_id,
            "has_hierarchy": bool(extraction),
            "epics": extraction.get('epics', []),
            "features": extraction.get('features', []),
            "stories": extraction.get('stories', []),
            "tasks": extraction.get('tasks', []),
            "causal_relations": phase3.get('causal_relations', []),
            "summary": {
                "total_epics": len(extraction.get('epics', [])),
                "total_features": len(extraction.get('features', [])),
                "total_stories": len(extraction.get('stories', [])),
                "total_tasks": len(extraction.get('tasks', [])),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get hierarchy failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get hierarchy: {str(e)}",
        )


@router.get("/marqed/{session_id}/conflicts")
async def get_conflicts(session_id: str):
    """
    Get detected conflicts from deep extraction.

    Returns conflicts detected by LLM Council during Phase 4.
    """
    try:
        service = get_brown_paper_service()
        session = await service.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )

        # Check for enhanced analysis results
        enhanced = getattr(session, 'enhanced_analysis', {})
        phase4 = enhanced.get('phase4_result', {}) if isinstance(enhanced, dict) else {}

        conflicts = phase4.get('conflicts', [])
        human_review_needed = phase4.get('human_review_needed', 0)
        consensus_confidence = phase4.get('consensus_confidence', 0.0)

        return {
            "session_id": session_id,
            "has_conflicts": bool(conflicts),
            "total_conflicts": len(conflicts),
            "human_review_needed": human_review_needed,
            "consensus_confidence": consensus_confidence,
            "conflicts": conflicts,
            "conflicts_by_severity": {
                "high": [c for c in conflicts if c.get('severity') == 'high'],
                "medium": [c for c in conflicts if c.get('severity') == 'medium'],
                "low": [c for c in conflicts if c.get('severity') == 'low'],
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conflicts failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conflicts: {str(e)}",
        )


@router.get("/marqed/{session_id}/metrics")
async def get_metrics(session_id: str):
    """
    Get code quality metrics for a session.

    Returns complexity, coupling, cohesion, and documentation metrics.
    """
    try:
        service = get_brown_paper_service()
        session = await service.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )

        # Check for enhanced analysis results
        enhanced = getattr(session, 'enhanced_analysis', {})
        phase1 = enhanced.get('phase1_result', {}) if isinstance(enhanced, dict) else {}

        code_analysis = phase1.get('code_analysis', {})
        layered_analysis = phase1.get('layered_analysis', {})

        # Phase 5 estimation metrics
        phase5 = enhanced.get('phase5_result', {}) if isinstance(enhanced, dict) else {}
        estimation = phase5.get('estimation_result', {})
        risk = phase5.get('risk_assessment', {})

        # Week 144: SIG metrics from Phase 1
        sig_metrics = phase1.get('sig_metrics', {})

        return {
            "session_id": session_id,
            "has_metrics": bool(code_analysis),

            # Week 144: SIG Top 10 Quality Ratings
            "sig_top10": {
                "overall_rating": sig_metrics.get('overall_rating', 0),
                "overall_stars": sig_metrics.get('overall_stars', '☆☆☆☆☆'),
                "ratings": sig_metrics.get('ratings', {}),
                "volume": sig_metrics.get('volume', {}),
                "findings_summary": sig_metrics.get('findings_summary', {}),
            },

            # Complexity metrics
            "complexity": {
                "profile": code_analysis.get('complexity_profile', {}),
                "average": code_analysis.get('average_complexity', 0),
            },

            # Coupling metrics
            "coupling": code_analysis.get('coupling_analysis', {}),

            # Documentation coverage
            "documentation": {
                "coverage": code_analysis.get('documentation_coverage', 0),
            },

            # Layered analysis (VBScript, stored procs, ASP)
            "legacy_patterns": {
                "vbscript_files": layered_analysis.get('vbscript_files', 0),
                "stored_procedures": layered_analysis.get('stored_procedures', 0),
                "asp_patterns": layered_analysis.get('asp_patterns', []),
                "swot": layered_analysis.get('swot', {}),
            },

            # Risk assessment
            "risk_assessment": risk,

            # Estimation summary
            "estimation": {
                "total_fp": estimation.get('total_fp', 0),
                "total_sp": estimation.get('total_sp', 0),
                "estimated_hours": estimation.get('estimated_hours', 0),
                "complexity_multiplier": phase5.get('complexity_multiplier', 1.0),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get metrics failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}",
        )
