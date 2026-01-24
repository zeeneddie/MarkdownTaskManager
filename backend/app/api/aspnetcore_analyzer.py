"""
ASP.NET Core Analyzer API Routes

Fase 24 GAP B5: ASP.NET Core Analyzer
REST API endpoints for ASP.NET Core codebase analysis.

Endpoints:
- POST /api/aspnetcore/analyze - Analyze ASP.NET Core project
- GET /api/aspnetcore/summary/{analysis_id} - Get analysis summary
- GET /api/aspnetcore/controllers - List controllers
- GET /api/aspnetcore/endpoints - List endpoints (controller + minimal API)
- GET /api/aspnetcore/blazor - Get Blazor components
- GET /api/aspnetcore/grpc - Get gRPC services
- GET /api/aspnetcore/infrastructure - Get DI, middleware, DbContexts
- GET /api/aspnetcore/patterns - Get detected patterns/anti-patterns

Author: Claude Code (Fase 24 GAP)
Date: 2026-01-24
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.aspnetcore_analyzer_service import (
    AspNetCoreAnalyzerService,
    AspNetCoreAnalysisResult,
)

router = APIRouter(prefix="/api/aspnetcore", tags=["aspnetcore-analyzer"])

# Service instance
_analyzer_service = AspNetCoreAnalyzerService()


# ========== Pydantic Models ==========

class AnalyzeRequest(BaseModel):
    """Request to analyze an ASP.NET Core project."""
    project_path: str = Field(..., description="Path to the project root")
    include_blazor: bool = Field(True, description="Include Blazor component analysis")
    include_grpc: bool = Field(True, description="Include gRPC service analysis")


class ControllerResponse(BaseModel):
    """Controller information."""
    name: str
    file_path: str
    route_prefix: Optional[str]
    controller_type: str
    action_count: int
    is_api_controller: bool
    uses_authorization: bool


class EndpointResponse(BaseModel):
    """Endpoint information."""
    route: str
    http_method: str
    source: str  # 'controller' or 'minimal_api'
    controller_name: Optional[str]
    action_name: Optional[str]
    return_type: Optional[str]


class BlazorComponentResponse(BaseModel):
    """Blazor component information."""
    name: str
    file_path: str
    component_type: str
    has_parameters: bool
    has_inject: bool
    has_cascade: bool


class GrpcServiceResponse(BaseModel):
    """gRPC service information."""
    service_name: str
    file_path: str
    proto_file: Optional[str]
    method_count: int


class InfrastructureResponse(BaseModel):
    """Infrastructure information."""
    di_registrations: List[Dict[str, Any]]
    middleware: List[Dict[str, Any]]
    db_contexts: List[Dict[str, Any]]


class PatternResponse(BaseModel):
    """Pattern/anti-pattern information."""
    pattern_name: str
    category: str
    file_path: str
    line_number: int
    description: str
    is_anti_pattern: bool
    recommendation: Optional[str]


class AnalysisSummaryResponse(BaseModel):
    """Analysis summary."""
    projects: int
    target_framework: Optional[str]
    total_controllers: int
    api_controllers: int
    mvc_controllers: int
    total_endpoints: int
    controller_endpoints: int
    minimal_api_endpoints: int
    blazor_components: int
    grpc_services: int
    db_contexts: int
    di_registrations: int
    middleware_count: int
    patterns_detected: int
    anti_patterns_detected: int
    scan_duration_ms: float


# ========== Endpoints ==========

@router.post("/analyze", response_model=AnalysisSummaryResponse)
async def analyze_aspnetcore_project(request: AnalyzeRequest) -> AnalysisSummaryResponse:
    """
    Analyze an ASP.NET Core project.

    Returns a summary of the analysis including controllers, endpoints,
    Blazor components, gRPC services, and detected patterns.
    """
    try:
        result = await _analyzer_service.analyze(
            project_path=request.project_path,
            include_blazor=request.include_blazor,
            include_grpc=request.include_grpc
        )

        # Store result for subsequent queries (in-memory for now)
        _analyzer_service._last_result = result

        # Build summary response
        return AnalysisSummaryResponse(
            projects=len(result.projects),
            target_framework=result.projects[0].target_framework if result.projects else None,
            total_controllers=len(result.controllers),
            api_controllers=sum(1 for c in result.controllers if c.is_api_controller),
            mvc_controllers=sum(1 for c in result.controllers if not c.is_api_controller),
            total_endpoints=len(result.controller_endpoints) + len(result.minimal_api_endpoints),
            controller_endpoints=len(result.controller_endpoints),
            minimal_api_endpoints=len(result.minimal_api_endpoints),
            blazor_components=len(result.blazor_components),
            grpc_services=len(result.grpc_services),
            db_contexts=len(result.db_contexts),
            di_registrations=len(result.di_registrations),
            middleware_count=len(result.middleware),
            patterns_detected=len([p for p in result.patterns if not p.is_anti_pattern]),
            anti_patterns_detected=len([p for p in result.patterns if p.is_anti_pattern]),
            scan_duration_ms=result.scan_duration_ms
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/controllers", response_model=List[ControllerResponse])
async def get_controllers() -> List[ControllerResponse]:
    """Get all detected ASP.NET Core controllers."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    return [
        ControllerResponse(
            name=c.name,
            file_path=c.file_path,
            route_prefix=c.route_prefix,
            controller_type=c.controller_type.value,
            action_count=len(c.actions),
            is_api_controller=c.is_api_controller,
            uses_authorization=c.uses_authorization
        )
        for c in result.controllers
    ]


@router.get("/endpoints", response_model=List[EndpointResponse])
async def get_endpoints(
    source: Optional[str] = Query(None, description="Filter by source: 'controller' or 'minimal_api'")
) -> List[EndpointResponse]:
    """Get all detected endpoints (controller actions + minimal API)."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    endpoints = []

    # Controller endpoints
    if source is None or source == 'controller':
        for endpoint in result.controller_endpoints:
            endpoints.append(EndpointResponse(
                route=endpoint.route,
                http_method=endpoint.http_method.value,
                source='controller',
                controller_name=endpoint.controller_name,
                action_name=endpoint.action_name,
                return_type=endpoint.return_type
            ))

    # Minimal API endpoints
    if source is None or source == 'minimal_api':
        for endpoint in result.minimal_api_endpoints:
            endpoints.append(EndpointResponse(
                route=endpoint.route,
                http_method=endpoint.http_method.value,
                source='minimal_api',
                controller_name=None,
                action_name=None,
                return_type=endpoint.return_type
            ))

    return endpoints


@router.get("/blazor", response_model=List[BlazorComponentResponse])
async def get_blazor_components() -> List[BlazorComponentResponse]:
    """Get all detected Blazor components."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    return [
        BlazorComponentResponse(
            name=c.name,
            file_path=c.file_path,
            component_type=c.component_type,
            has_parameters=len(c.parameters) > 0,
            has_inject=len(c.inject_services) > 0,
            has_cascade=len(c.cascade_parameters) > 0
        )
        for c in result.blazor_components
    ]


@router.get("/grpc", response_model=List[GrpcServiceResponse])
async def get_grpc_services() -> List[GrpcServiceResponse]:
    """Get all detected gRPC services."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    return [
        GrpcServiceResponse(
            service_name=s.service_name,
            file_path=s.file_path,
            proto_file=s.proto_file,
            method_count=len(s.methods)
        )
        for s in result.grpc_services
    ]


@router.get("/infrastructure", response_model=InfrastructureResponse)
async def get_infrastructure() -> InfrastructureResponse:
    """Get infrastructure details (DI, middleware, DbContexts)."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    return InfrastructureResponse(
        di_registrations=[
            {
                "service_type": r.service_type,
                "implementation_type": r.implementation_type,
                "lifetime": r.lifetime.value,
                "file_path": r.file_path
            }
            for r in result.di_registrations
        ],
        middleware=[
            {
                "name": m.name,
                "order": m.order,
                "file_path": m.file_path,
                "is_custom": m.is_custom
            }
            for m in result.middleware
        ],
        db_contexts=[
            {
                "name": db.name,
                "file_path": db.file_path,
                "entity_count": len(db.entities),
                "uses_migrations": db.uses_migrations
            }
            for db in result.db_contexts
        ]
    )


@router.get("/patterns", response_model=List[PatternResponse])
async def get_patterns(
    anti_patterns_only: bool = Query(False, description="Only return anti-patterns")
) -> List[PatternResponse]:
    """Get detected patterns and anti-patterns."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    patterns = result.patterns
    if anti_patterns_only:
        patterns = [p for p in patterns if p.is_anti_pattern]

    return [
        PatternResponse(
            pattern_name=p.pattern_name,
            category=p.category,
            file_path=p.file_path,
            line_number=p.line_number,
            description=p.description,
            is_anti_pattern=p.is_anti_pattern,
            recommendation=p.recommendation
        )
        for p in patterns
    ]


@router.get("/summary")
async def get_analysis_summary() -> Dict[str, Any]:
    """Get a detailed summary including recommendations."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    return _analyzer_service.get_summary(result)
