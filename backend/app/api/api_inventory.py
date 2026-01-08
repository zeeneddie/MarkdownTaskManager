"""
API Inventory Routes - Fase 26: Migration Execution (Week 140-141)

FastAPI routes for API endpoint extraction and external API detection.

Author: Claude Code (Week 140 - Fase 26)
Date: 2026-01-01
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.services.api_inventory_service import APIInventoryService
from app.models.api_inventory import (
    APIInventoryResult,
    Endpoint,
    ExternalAPI,
    HTTPMethod,
)

router = APIRouter(prefix="/api/api-inventory", tags=["API Inventory"])

# Service instance (in production, use dependency injection)
_service: Optional[APIInventoryService] = None


def get_service() -> APIInventoryService:
    """Get or create service instance."""
    global _service
    if _service is None:
        _service = APIInventoryService()
    return _service


# Request/Response Models

class CreateSessionRequest(BaseModel):
    """Request to create a new API inventory session."""
    project_id: str = Field(..., description="Project identifier")
    name: str = Field(default="", description="Session name")


class SessionResponse(BaseModel):
    """Response with session ID."""
    session_id: str
    project_id: str
    name: str
    created_at: datetime
    status: str


class ScanRequest(BaseModel):
    """Request to scan codebase for APIs."""
    project_path: str = Field(..., description="Path to project root")
    file_extensions: Optional[List[str]] = Field(
        default=None,
        description="File extensions to scan (e.g., ['.py', '.js'])"
    )
    exclude_patterns: Optional[List[str]] = Field(
        default=None,
        description="Patterns to exclude (e.g., ['**/node_modules/**'])"
    )
    framework: Optional[str] = Field(
        default=None,
        description="Force specific framework detection"
    )


class FileScanRequest(BaseModel):
    """Request to scan specific files."""
    files: Dict[str, str] = Field(..., description="Map of filename to content")
    framework: Optional[str] = Field(default=None, description="Framework hint")
    language: Optional[str] = Field(default="python", description="Language for external API detection")


class OpenAPIInfoRequest(BaseModel):
    """Request with OpenAPI spec metadata."""
    title: str = Field(default="API Documentation", description="API title")
    version: str = Field(default="1.0.0", description="API version")
    description: Optional[str] = Field(default=None, description="API description")


# Endpoints

@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest) -> SessionResponse:
    """
    Create a new API inventory session.

    A session tracks the state of an API extraction process,
    allowing for incremental scanning and result retrieval.
    """
    service = get_service()
    session_id = await service.create_session(
        project_id=request.project_id,
        name=request.name
    )

    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=500, detail="Failed to create session")

    return SessionResponse(
        session_id=session.session_id,
        project_id=session.project_id,
        name=request.name,
        created_at=session.scan_date,
        status="created"
    )


@router.post("/sessions/{session_id}/scan")
async def scan_codebase(
    session_id: str,
    request: ScanRequest,
) -> Dict[str, Any]:
    """
    Scan a codebase for internal endpoints and external API calls.

    This performs a comprehensive scan of the specified project path,
    detecting frameworks, extracting route definitions, and identifying
    external API integrations.
    """
    service = get_service()

    # Verify session exists
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    result = await service.scan_codebase(
        session_id=session_id,
        project_path=request.project_path,
        file_extensions=request.file_extensions,
        exclude_patterns=request.exclude_patterns,
    )

    return result.to_dict()


@router.post("/sessions/{session_id}/scan-files")
async def scan_files(
    session_id: str,
    request: FileScanRequest,
) -> Dict[str, Any]:
    """
    Scan specific file contents for APIs.

    Useful for scanning files without filesystem access,
    such as files from a Git repository or uploaded content.
    """
    service = get_service()

    # Verify session exists
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    # Extract internal endpoints
    endpoints = await service.extract_internal_endpoints(
        files=request.files,
        framework=request.framework,
    )

    # Extract external APIs
    external_apis = await service.extract_external_apis(
        files=request.files,
        language=request.language or "python",
    )

    # Update session with results
    session.internal_endpoints = endpoints
    session.external_apis = external_apis
    session.total_internal = len(endpoints)
    session.total_external = len(external_apis)
    session.files_scanned = len(request.files)

    return session.to_dict()


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> Dict[str, Any]:
    """
    Get session results.

    Returns the complete API inventory including all extracted
    endpoints and external API integrations.
    """
    service = get_service()

    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return result.to_dict()


@router.get("/sessions/{session_id}/endpoints")
async def get_endpoints(
    session_id: str,
    method: Optional[str] = Query(None, description="Filter by HTTP method (GET, POST, etc.)"),
    path_contains: Optional[str] = Query(None, description="Filter by path substring"),
    auth_required: Optional[bool] = Query(None, description="Filter by auth requirement"),
    deprecated: Optional[bool] = Query(None, description="Filter deprecated endpoints"),
) -> List[Dict[str, Any]]:
    """
    List internal endpoints with optional filtering.

    Supports filtering by HTTP method, path pattern,
    authentication requirements, and deprecation status.
    """
    service = get_service()

    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    endpoints = result.internal_endpoints

    # Apply filters
    if method:
        try:
            http_method = HTTPMethod(method.upper())
            endpoints = [e for e in endpoints if http_method in e.methods]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid HTTP method: {method}")

    if path_contains:
        endpoints = [e for e in endpoints if path_contains in e.path]

    if auth_required is not None:
        from app.models.api_inventory import AuthType
        if auth_required:
            endpoints = [e for e in endpoints if e.authentication != AuthType.NONE]
        else:
            endpoints = [e for e in endpoints if e.authentication == AuthType.NONE]

    if deprecated is not None:
        endpoints = [e for e in endpoints if e.deprecated == deprecated]

    return [e.to_dict() for e in endpoints]


@router.get("/sessions/{session_id}/external")
async def get_external_apis(
    session_id: str,
    category: Optional[str] = Query(None, description="Filter by category (payment, email, etc.)"),
    domain_contains: Optional[str] = Query(None, description="Filter by domain substring"),
) -> List[Dict[str, Any]]:
    """
    List detected external API integrations.

    Returns all external APIs called from the codebase,
    including their endpoints, authentication methods, and categories.
    """
    service = get_service()

    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    apis = result.external_apis

    # Apply filters
    if category:
        apis = [a for a in apis if a.category == category.lower()]

    if domain_contains:
        apis = [a for a in apis if domain_contains.lower() in a.detected_domain.lower()]

    return [a.to_dict() for a in apis]


@router.get("/sessions/{session_id}/openapi")
async def get_openapi_spec(
    session_id: str,
    title: str = Query("API Documentation", description="OpenAPI title"),
    version: str = Query("1.0.0", description="API version"),
    description: Optional[str] = Query(None, description="API description"),
) -> Dict[str, Any]:
    """
    Generate OpenAPI 3.0 specification from extracted endpoints.

    Creates a valid OpenAPI spec that can be used with Swagger UI
    or other API documentation tools.
    """
    service = get_service()

    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    info = {
        "title": title,
        "version": version,
    }
    if description:
        info["description"] = description

    spec = await service.generate_openapi_spec(
        endpoints=result.internal_endpoints,
        info=info,
    )

    return spec


@router.get("/sessions/{session_id}/report")
async def get_report(
    session_id: str,
    format: str = Query("markdown", description="Output format: markdown, csv"),
) -> Dict[str, str]:
    """
    Get API inventory report in various formats.

    Supported formats:
    - markdown: Human-readable documentation
    - csv: Spreadsheet-compatible data
    """
    service = get_service()

    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    if format.lower() == "markdown":
        content = service.to_markdown_report(result)
        content_type = "text/markdown"
    elif format.lower() == "csv":
        content = service.to_csv(result)
        content_type = "text/csv"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Use 'markdown' or 'csv'."
        )

    return {
        "format": format,
        "content_type": content_type,
        "content": content,
    }


@router.get("/sessions/{session_id}/summary")
async def get_summary(session_id: str) -> Dict[str, Any]:
    """
    Get a summary of the API inventory.

    Returns high-level statistics about the scanned codebase,
    including endpoint counts, framework detection, and external APIs.
    """
    service = get_service()

    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    # Count endpoints by method
    method_counts: Dict[str, int] = {}
    for endpoint in result.internal_endpoints:
        for method in endpoint.methods:
            method_counts[method.value] = method_counts.get(method.value, 0) + 1

    # Count external APIs by category
    category_counts: Dict[str, int] = {}
    for api in result.external_apis:
        category_counts[api.category] = category_counts.get(api.category, 0) + 1

    # Count endpoints requiring auth
    auth_required = len([e for e in result.internal_endpoints if e.authentication.value != "none"])

    return {
        "session_id": session_id,
        "project_id": result.project_id,
        "scan_date": result.scan_date.isoformat(),
        "files_scanned": result.files_scanned,
        "scan_duration_seconds": result.scan_duration_seconds,
        "internal_endpoints": {
            "total": result.total_internal,
            "by_method": method_counts,
            "auth_required": auth_required,
            "deprecated": len([e for e in result.internal_endpoints if e.deprecated]),
        },
        "external_apis": {
            "total": result.total_external,
            "by_category": category_counts,
        },
        "frameworks_detected": [f.to_dict() for f in result.frameworks_detected],
        "languages_scanned": result.languages_scanned,
        "errors": len(result.errors),
        "warnings": len(result.warnings),
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> Dict[str, str]:
    """
    Delete an API inventory session.

    Removes all data associated with the session.
    """
    service = get_service()

    result = await service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    # Remove from in-memory storage
    if session_id in service.sessions:
        del service.sessions[session_id]

    return {"status": "deleted", "session_id": session_id}


@router.get("/frameworks")
async def list_supported_frameworks() -> Dict[str, Any]:
    """
    List all supported frameworks for API extraction.

    Returns the frameworks that can be auto-detected and their
    associated route patterns.
    """
    from app.models.api_inventory import APIFramework

    return {
        "frameworks": [
            {
                "id": f.value,
                "name": f.name,
                "description": _get_framework_description(f),
            }
            for f in APIFramework
            if f != APIFramework.UNKNOWN
        ]
    }


def _get_framework_description(framework) -> str:
    """Get description for a framework."""
    from app.models.api_inventory import APIFramework
    descriptions = {
        APIFramework.FASTAPI: "Python async web framework with automatic OpenAPI",
        APIFramework.FLASK: "Python micro web framework",
        APIFramework.DJANGO: "Python full-stack web framework",
        APIFramework.EXPRESS: "Node.js minimal web framework",
        APIFramework.NESTJS: "Node.js progressive TypeScript framework",
        APIFramework.ASPNET: "Microsoft .NET web framework",
        APIFramework.ASPNET_CORE: "Microsoft .NET Core cross-platform framework",
        APIFramework.SPRING: "Java enterprise framework",
        APIFramework.LARAVEL: "PHP full-stack framework",
        APIFramework.RAILS: "Ruby on Rails web framework",
        APIFramework.GIN: "Go HTTP web framework",
        APIFramework.ACTIX: "Rust actor-based web framework",
    }
    return descriptions.get(framework, "Unknown framework")


@router.get("/categories")
async def list_api_categories() -> Dict[str, List[str]]:
    """
    List known external API categories.

    Returns categories used for classifying detected external APIs.
    """
    from app.models.api_inventory import KNOWN_API_CATEGORIES

    # Group domains by category
    categories: Dict[str, List[str]] = {}
    for domain, category in KNOWN_API_CATEGORIES.items():
        if category not in categories:
            categories[category] = []
        categories[category].append(domain)

    return {"categories": categories}
