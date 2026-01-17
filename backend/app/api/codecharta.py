"""
CodeCharta API Endpoints

Week 145 - Fase 28: CodeCharta Integration

Provides endpoints to export code analysis data to CodeCharta format
for 3D visualization of software metrics.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.services.codecharta_exporter_service import get_codecharta_exporter, CodeChartaProject

router = APIRouter(prefix="/api/codecharta", tags=["CodeCharta"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ExportRequest(BaseModel):
    """Request to export analysis data to CodeCharta format."""
    project_name: str = Field(..., description="Name of the project")
    root_path: str = Field(..., description="Root path of the codebase")
    analysis_data: Dict[str, Any] = Field(..., description="Analysis data with files and dependencies")
    include_edges: bool = Field(True, description="Include dependency edges")

    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "my-project",
                "root_path": "/opt/projecten/my-project",
                "analysis_data": {
                    "files": [
                        {"path": "/opt/projecten/my-project/src/main.py", "loc": 150, "complexity": 12},
                        {"path": "/opt/projecten/my-project/src/utils.py", "loc": 80, "complexity": 5}
                    ],
                    "dependencies": [
                        {"from": "src/main.py", "to": "src/utils.py", "calls": 5}
                    ]
                },
                "include_edges": True
            }
        }


class ExportFromSourceRequest(BaseModel):
    """Request to export from a specific analysis source."""
    project_name: str = Field(..., description="Name of the project")
    root_path: str = Field(..., description="Root path of the codebase")
    source: str = Field(..., description="Source type: aggregator, dependency_graph, static_analysis")
    source_data: Dict[str, Any] = Field(..., description="Source-specific analysis data")


class ExportResponse(BaseModel):
    """Response containing CodeCharta JSON export."""
    project_name: str
    format: str = "codecharta"
    api_version: str
    node_count: int
    edge_count: int
    metrics: List[str]
    json_data: Dict[str, Any]
    exported_at: str


class MetricsInfoResponse(BaseModel):
    """Information about supported metrics."""
    metrics: Dict[str, Dict[str, Any]]
    total_metrics: int


class VisualizationUrlResponse(BaseModel):
    """Response with visualization URL."""
    visualization_url: str
    project_name: str
    instructions: str


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/export", response_model=ExportResponse)
async def export_to_codecharta(request: ExportRequest):
    """
    Export analysis data to CodeCharta JSON format.

    The exported JSON can be:
    1. Downloaded and opened in CodeCharta desktop app
    2. Uploaded to CodeCharta web visualization
    3. Used with local CodeCharta server

    Returns the complete CodeCharta JSON structure.
    """
    try:
        exporter = get_codecharta_exporter()

        project = exporter.create_project(
            project_name=request.project_name,
            root_path=request.root_path,
            analysis_data=request.analysis_data,
            include_edges=request.include_edges,
        )

        json_data = project.to_dict()

        # Count nodes recursively
        def count_nodes(node: Dict) -> int:
            count = 1
            for child in node.get("children", []):
                count += count_nodes(child)
            return count

        total_nodes = sum(count_nodes(n) for n in json_data.get("nodes", []))

        return ExportResponse(
            project_name=request.project_name,
            api_version=project.apiVersion,
            node_count=total_nodes,
            edge_count=len(json_data.get("edges", [])),
            metrics=list(json_data.get("attributeDescriptors", {}).keys()),
            json_data=json_data,
            exported_at=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/export/from-source", response_model=ExportResponse)
async def export_from_source(request: ExportFromSourceRequest):
    """
    Export from a specific analysis source format.

    Supported sources:
    - aggregator: CodeAnalysisAggregatorService output
    - dependency_graph: DependencyGraphService output
    - static_analysis: Static analysis tool output
    """
    try:
        exporter = get_codecharta_exporter()

        if request.source == "aggregator":
            project = exporter.from_code_analysis_aggregator(
                project_name=request.project_name,
                root_path=request.root_path,
                aggregator_result=request.source_data,
            )
        elif request.source == "dependency_graph":
            project = exporter.from_dependency_graph(
                project_name=request.project_name,
                root_path=request.root_path,
                graph_data=request.source_data,
            )
        elif request.source == "static_analysis":
            project = exporter.from_static_analysis(
                project_name=request.project_name,
                root_path=request.root_path,
                static_analysis_result=request.source_data,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown source type: {request.source}. Supported: aggregator, dependency_graph, static_analysis"
            )

        json_data = project.to_dict()

        def count_nodes(node: Dict) -> int:
            count = 1
            for child in node.get("children", []):
                count += count_nodes(child)
            return count

        total_nodes = sum(count_nodes(n) for n in json_data.get("nodes", []))

        return ExportResponse(
            project_name=request.project_name,
            api_version=project.apiVersion,
            node_count=total_nodes,
            edge_count=len(json_data.get("edges", [])),
            metrics=list(json_data.get("attributeDescriptors", {}).keys()),
            json_data=json_data,
            exported_at=datetime.now(timezone.utc).isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/metrics", response_model=MetricsInfoResponse)
async def get_supported_metrics():
    """
    Get information about supported CodeCharta metrics.

    Returns all metrics that can be exported and their descriptions.
    """
    exporter = get_codecharta_exporter()

    return MetricsInfoResponse(
        metrics=exporter.attribute_descriptors,
        total_metrics=len(exporter.attribute_descriptors),
    )


@router.get("/visualization-url")
async def get_visualization_url(
    project_name: str = Query(..., description="Name of the project"),
):
    """
    Get CodeCharta visualization URL and instructions.

    Returns URL to the CodeCharta web visualization tool
    and instructions for using it with exported data.
    """
    # CodeCharta web visualization URL
    web_url = "https://maibornwolff.github.io/codecharta/visualization/app/"

    return VisualizationUrlResponse(
        visualization_url=web_url,
        project_name=project_name,
        instructions="""
1. Export your project using POST /api/codecharta/export
2. Download the json_data as a .cc.json file
3. Open the visualization URL in your browser
4. Click "Open Files" and select your .cc.json file
5. Explore your codebase as a 3D city!

For local visualization:
- See /api/codecharta/local-setup for Docker-based setup
- Or install CodeCharta standalone from GitHub releases

Metrics explanation:
- Building HEIGHT = primary metric (e.g., LOC)
- Building COLOR = secondary metric (e.g., complexity)
- Building AREA = tertiary metric (e.g., functions)
        """.strip(),
    )


@router.get("/local-setup")
async def get_local_setup_instructions():
    """
    Get instructions for setting up CodeCharta locally.

    Returns Docker commands and configuration for running
    CodeCharta visualization server locally.
    """
    return {
        "title": "Local CodeCharta Setup",
        "description": "Run CodeCharta visualization locally using Docker",
        "github_repo": "https://github.com/MaibornWolff/codecharta",
        "docker_setup": {
            "option_1_docker_compose": """
# docker-compose.yml
version: '3.8'
services:
  codecharta:
    image: maibornwolff/codecharta-visualization:latest
    ports:
      - "9000:80"
    volumes:
      - ./exports:/data
""",
            "option_2_docker_run": "docker run -p 9000:80 -v $(pwd)/exports:/data maibornwolff/codecharta-visualization:latest",
        },
        "standalone_setup": {
            "releases_url": "https://github.com/MaibornWolff/codecharta/releases",
            "platforms": ["Windows (.exe)", "macOS (.dmg)", "Linux (.AppImage)"],
            "steps": [
                "1. Download the latest release for your platform",
                "2. Install/run the application",
                "3. Use File > Open to load your .cc.json export",
            ],
        },
        "analysis_tools": {
            "description": "CodeCharta also provides analysis tools to generate metrics",
            "tools": [
                {"name": "ccsh", "description": "CodeCharta Shell - unified analysis interface"},
                {"name": "sonar-importer", "description": "Import from SonarQube"},
                {"name": "git-log-parser", "description": "Extract git metrics"},
                {"name": "source-code-parser", "description": "Analyze source code directly"},
            ],
            "install": "npm install -g codecharta-analysis",
        },
        "integration_with_marqed": {
            "description": "MarQed AI Platform can export to CodeCharta automatically",
            "endpoints": [
                "/api/codecharta/export - General export",
                "/api/codecharta/export/from-source - From specific analysis",
                "/api/codecharta/metrics - Available metrics",
            ],
            "workflow": [
                "1. Run code analysis via /api/code-analysis/*",
                "2. Export to CodeCharta via /api/codecharta/export/from-source",
                "3. Open in local CodeCharta visualization",
            ],
        },
    }
