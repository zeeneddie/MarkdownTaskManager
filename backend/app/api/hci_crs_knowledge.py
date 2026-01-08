"""
HCI-CRS Knowledge API - Query embedded project documentation

This API provides semantic search over the HCI-CRS project documentation
stored in ChromaDB. It supports:
- General knowledge queries
- Filtered queries by document type (epic, feature, user_story, task, architecture)
- Code location lookups
- Context retrieval for AI agents
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.services.chroma_service import ChromaService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/hci-crs", tags=["HCI-CRS Knowledge"])

# HCI-CRS project configuration
HCI_CRS_PROJECT_ID = 1000

# Document type mappings
VALID_DOCUMENT_TYPES = [
    "project_overview",
    "architecture",
    "epic",
    "feature",
    "user_story",
    "task",
    "documentation"
]


class KnowledgeQuery(BaseModel):
    """Request model for knowledge queries"""
    query: str = Field(..., description="Search query", min_length=3)
    document_types: Optional[List[str]] = Field(
        None,
        description="Filter by document types: project_overview, architecture, epic, feature, user_story, task, documentation"
    )
    top_k: int = Field(5, ge=1, le=20, description="Number of results to return")


class KnowledgeResult(BaseModel):
    """Response model for knowledge queries"""
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    query_time_ms: float


class CodeLocationQuery(BaseModel):
    """Request model for code location lookups"""
    component: str = Field(..., description="Component name (e.g., 'TellertjeJeugd', 'JeugdtrajectManager')")


class CodeLocation(BaseModel):
    """Response model for code locations"""
    component: str
    file_path: Optional[str]
    layer: Optional[str]
    domain: Optional[str]
    related_docs: List[Dict[str, Any]]


class AgentContextRequest(BaseModel):
    """Request model for agent context retrieval"""
    task_description: str = Field(..., description="Description of the task the agent is working on")
    current_epic: Optional[str] = Field(None, description="Current epic (e.g., 'EPIC-JW-jeugdtraject')")
    current_feature: Optional[str] = Field(None, description="Current feature (e.g., 'FEATURE-003-tellertje')")
    include_architecture: bool = Field(True, description="Include architecture context")
    include_code_locations: bool = Field(True, description="Include code location mappings")
    max_context_chunks: int = Field(10, ge=1, le=30, description="Maximum context chunks to return")


class AgentContext(BaseModel):
    """Response model for agent context"""
    task_description: str
    relevant_docs: List[Dict[str, Any]]
    architecture_context: Optional[str]
    code_locations: List[Dict[str, str]]
    recommendations: List[str]


# Initialize ChromaDB service (singleton pattern via dependency)
_chroma_service = None

def get_chroma_service() -> ChromaService:
    """Get or create ChromaDB service instance"""
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaService()
    return _chroma_service


@router.get("/health")
async def health_check():
    """Health check for HCI-CRS knowledge service"""
    try:
        chroma = get_chroma_service()
        # Quick collection count check
        count = chroma.project_documents.count()
        return {
            "status": "healthy",
            "project_id": HCI_CRS_PROJECT_ID,
            "documents_indexed": count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@router.post("/query", response_model=KnowledgeResult)
async def query_knowledge(request: KnowledgeQuery):
    """
    Query HCI-CRS project knowledge using semantic search

    Returns relevant documentation chunks based on the query.
    Can filter by document types for more targeted searches.
    """
    start_time = datetime.now()

    try:
        chroma = get_chroma_service()

        # Validate document types
        if request.document_types:
            invalid_types = [t for t in request.document_types if t not in VALID_DOCUMENT_TYPES]
            if invalid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid document types: {invalid_types}. Valid types: {VALID_DOCUMENT_TYPES}"
                )

        # Query ChromaDB
        results = chroma.query_project_knowledge(
            query=request.query,
            project_id=HCI_CRS_PROJECT_ID,
            document_types=request.document_types,
            top_k=request.top_k
        )

        # Format results
        formatted_results = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results.get("results", []),
            results.get("metadatas", []),
            results.get("distances", [])
        )):
            formatted_results.append({
                "rank": i + 1,
                "content": doc,
                "metadata": metadata,
                "relevance_score": round(1 - distance, 4),  # Convert distance to similarity
                "document_type": metadata.get("document_type", "unknown"),
                "source_file": metadata.get("relative_path", metadata.get("file_name", "unknown"))
            })

        query_time = (datetime.now() - start_time).total_seconds() * 1000

        return KnowledgeResult(
            query=request.query,
            results=formatted_results,
            total_results=len(formatted_results),
            query_time_ms=round(query_time, 2)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Knowledge query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/query/simple")
async def simple_query(
    q: str = Query(..., min_length=3, description="Search query"),
    type: Optional[str] = Query(None, description="Document type filter"),
    limit: int = Query(5, ge=1, le=20, description="Number of results")
):
    """
    Simple GET endpoint for quick queries

    Example: /api/hci-crs/query/simple?q=streefminuten&type=user_story&limit=3
    """
    request = KnowledgeQuery(
        query=q,
        document_types=[type] if type else None,
        top_k=limit
    )
    return await query_knowledge(request)


@router.post("/code-location", response_model=CodeLocation)
async def find_code_location(request: CodeLocationQuery):
    """
    Find code locations for a specific component

    Returns file paths, layer information, and related documentation.
    """
    try:
        chroma = get_chroma_service()

        # Search for component in architecture and documentation
        results = chroma.query_project_knowledge(
            query=f"code location file path {request.component}",
            project_id=HCI_CRS_PROJECT_ID,
            document_types=["architecture", "user_story", "task"],
            top_k=10
        )

        # Parse results to extract code locations
        file_path = None
        layer = None
        domain = None

        # Domain detection
        component_lower = request.component.lower()
        if "jw" in component_lower or "jeugd" in component_lower:
            domain = "Jeugd (JW_)"
        elif "wmo" in component_lower:
            domain = "WMO"

        # Layer detection
        if "manager" in component_lower:
            layer = "BLL (Business Logic Layer)"
        elif "db" in component_lower or "dal" in component_lower:
            layer = "DAL (Data Access Layer)"
        elif "ascx" in component_lower or "aspx" in component_lower:
            layer = "UI (User Interface)"
        elif "entity" in component_lower or "entities" in component_lower:
            layer = "Entity"

        # Format related docs
        related_docs = []
        for doc, metadata in zip(
            results.get("results", []),
            results.get("metadatas", [])
        ):
            if request.component.lower() in doc.lower():
                related_docs.append({
                    "content_snippet": doc[:200] + "..." if len(doc) > 200 else doc,
                    "source": metadata.get("relative_path", "unknown"),
                    "type": metadata.get("document_type", "unknown")
                })

                # Try to extract file path from content
                if "CRSLibrary" in doc or "WEB/" in doc:
                    import re
                    paths = re.findall(r'[`"]([A-Za-z_/\\]+\.(vb|aspx|ascx|asp)[`"]?)', doc)
                    if paths and not file_path:
                        file_path = paths[0][0]

        return CodeLocation(
            component=request.component,
            file_path=file_path,
            layer=layer,
            domain=domain,
            related_docs=related_docs[:5]  # Limit to top 5
        )

    except Exception as e:
        logger.error(f"Code location lookup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Lookup failed: {str(e)}")


@router.post("/agent-context", response_model=AgentContext)
async def get_agent_context(request: AgentContextRequest):
    """
    Get contextual information for AI agents working on HCI-CRS tasks

    This endpoint provides:
    - Relevant documentation based on task description
    - Architecture context
    - Code location mappings
    - Recommendations for the task
    """
    try:
        chroma = get_chroma_service()

        # Build comprehensive query
        query_parts = [request.task_description]
        if request.current_epic:
            query_parts.append(request.current_epic)
        if request.current_feature:
            query_parts.append(request.current_feature)

        full_query = " ".join(query_parts)

        # Get relevant docs
        results = chroma.query_project_knowledge(
            query=full_query,
            project_id=HCI_CRS_PROJECT_ID,
            top_k=request.max_context_chunks
        )

        # Format relevant docs
        relevant_docs = []
        for doc, metadata, distance in zip(
            results.get("results", []),
            results.get("metadatas", []),
            results.get("distances", [])
        ):
            relevant_docs.append({
                "content": doc,
                "source": metadata.get("relative_path", "unknown"),
                "type": metadata.get("document_type", "unknown"),
                "epic": metadata.get("epic"),
                "feature": metadata.get("feature"),
                "relevance": round(1 - distance, 4)
            })

        # Get architecture context if requested
        architecture_context = None
        if request.include_architecture:
            # Query architecture docs without document_type filter (ChromaDB limitation)
            arch_results = chroma.query_project_knowledge(
                query="architecture gescheiden codepaden JW WMO Entity Manager DAL",
                project_id=HCI_CRS_PROJECT_ID,
                top_k=5
            )
            # Filter for architecture docs manually
            arch_docs = [
                doc for doc, meta in zip(
                    arch_results.get("results", []),
                    arch_results.get("metadatas", [])
                )
                if meta.get("document_type") == "architecture"
            ]
            if arch_docs:
                architecture_context = "\n\n".join(arch_docs[:2])

        # Extract code locations
        code_locations = []
        if request.include_code_locations:
            # Known code location patterns from HCI-CRS
            code_location_patterns = {
                "JeugdtrajectManager": "CRSLibrary/Bll/JeugdtrajectManager.vb",
                "Traject_WMOManager": "CRSLibrary/Bll/Traject_WMOManager.vb",
                "TellertjeJeugd": "WEB/Dossier/UserControls/TellertjeJeugd.ascx.vb",
                "TellertjeWMO": "WEB/Dossier/UserControls/TellertjeWMO.ascx.vb",
                "JW_ContractPrijstabelProduct": "CRSLibrary/Entities/JW_ContractPrijstabelProduct.vb",
                "WMO_ContractPrijstabelProduct": "CRSLibrary/Entities/WMO_ContractPrijstabelProduct.vb",
            }

            # Check which patterns are relevant to the task
            task_lower = request.task_description.lower()
            for component, path in code_location_patterns.items():
                if component.lower() in task_lower or any(
                    keyword in task_lower
                    for keyword in component.lower().replace("_", " ").split()
                ):
                    code_locations.append({
                        "component": component,
                        "path": path
                    })

        # Generate recommendations based on context
        recommendations = []
        task_lower = request.task_description.lower()

        if "jeugd" in task_lower or "jw" in task_lower:
            recommendations.append("Dit is een Jeugd-domein taak. Gebruik JW_ prefixed tables en classes.")
        elif "wmo" in task_lower:
            recommendations.append("Dit is een WMO-domein taak. Gebruik WMO_ prefixed tables en classes.")

        if "tellertje" in task_lower or "streefminuten" in task_lower:
            recommendations.append("Check ARCHITECTURE.md voor de gescheiden codepaden: Jeugd en WMO hebben APARTE tellertje implementaties.")

        if "database" in task_lower or "migratie" in task_lower:
            recommendations.append("Zorg voor backward compatibility: default waarden voor nieuwe kolommen, NULL support voor bestaande records.")

        if "entity" in task_lower or "dal" in task_lower or "bll" in task_lower:
            recommendations.append("Volg het Entity → DAL → BLL → UI patroon consistent door de codebase.")

        return AgentContext(
            task_description=request.task_description,
            relevant_docs=relevant_docs,
            architecture_context=architecture_context,
            code_locations=code_locations,
            recommendations=recommendations if recommendations else [
                "Raadpleeg ARCHITECTURE.md voor domein-specifieke code patterns",
                "Check of wijzigingen zowel JW als WMO domein raken"
            ]
        )

    except Exception as e:
        logger.error(f"Agent context retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Context retrieval failed: {str(e)}")


@router.get("/stats")
async def get_stats():
    """
    Get statistics about the indexed HCI-CRS documentation
    """
    try:
        chroma = get_chroma_service()

        # Get document count by querying with a generic query
        # Note: ChromaDB doesn't have a direct count-by-metadata function
        total_count = chroma.project_documents.count()

        # Get sample to estimate type distribution
        sample_results = chroma.project_documents.get(
            where={"project_id": str(HCI_CRS_PROJECT_ID)},
            limit=500
        )

        # Count by document type
        type_counts = {}
        for metadata in sample_results.get("metadatas", []):
            doc_type = metadata.get("document_type", "unknown")
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

        return {
            "project_id": HCI_CRS_PROJECT_ID,
            "project_name": "HCI-CRS",
            "total_chunks": total_count,
            "indexed_chunks": len(sample_results.get("ids", [])),
            "document_types": type_counts,
            "valid_document_types": VALID_DOCUMENT_TYPES,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


# ============================================================================
# Week 143: Multi-Project Vector DB Support
# ============================================================================

# Known project registry - can be extended with database lookup
PROJECT_REGISTRY = {
    1000: {"name": "HCI-CRS", "description": "Healthcare CRS EPD System"},
    1001: {"name": "Klaverjas", "description": "Klaverjas Competition Manager"},
    1002: {"name": "TaskManager", "description": "Markdown Task Manager"},
}


@router.get("/projects")
async def list_indexed_projects():
    """
    List all projects with indexed documentation in Vector DB.

    Returns project IDs with document counts and metadata.
    """
    try:
        chroma = get_chroma_service()

        # Get all documents to find unique project IDs
        all_docs = chroma.project_documents.get(
            limit=1000,
            include=["metadatas"]
        )

        # Count documents per project
        project_counts: Dict[str, int] = {}
        project_types: Dict[str, set] = {}

        for metadata in all_docs.get("metadatas", []):
            project_id = metadata.get("project_id", "unknown")
            project_counts[project_id] = project_counts.get(project_id, 0) + 1
            if project_id not in project_types:
                project_types[project_id] = set()
            doc_type = metadata.get("document_type")
            if doc_type:
                project_types[project_id].add(doc_type)

        # Build response with registry info
        projects = []
        for pid, count in sorted(project_counts.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
            try:
                pid_int = int(pid)
            except ValueError:
                pid_int = None

            project_info = PROJECT_REGISTRY.get(pid_int, {})

            projects.append({
                "project_id": pid,
                "name": project_info.get("name", f"Project {pid}"),
                "description": project_info.get("description", "Unknown project"),
                "document_count": count,
                "document_types": list(project_types.get(pid, [])),
            })

        return {
            "status": "success",
            "total_projects": len(projects),
            "projects": projects,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Project listing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Project listing failed: {str(e)}")


@router.get("/projects/{project_id}/query")
async def query_project_knowledge(
    project_id: int,
    query: str = Query(..., min_length=3, description="Search query"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results")
):
    """
    Query knowledge for a specific project by ID.

    Allows querying any indexed project, not just HCI-CRS.
    """
    try:
        chroma = get_chroma_service()

        # Get project info
        project_info = PROJECT_REGISTRY.get(project_id, {
            "name": f"Project {project_id}",
            "description": "Unknown project"
        })

        # Query with project filter
        import time
        start = time.time()

        results = chroma.query_project_knowledge(
            query=query,
            project_id=project_id,
            top_k=top_k
        )

        query_time = (time.time() - start) * 1000

        # Format results
        formatted_results = []
        if results.get("documents"):
            docs = results["documents"][0] if results["documents"] else []
            metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
            distances = results.get("distances", [[]])[0] if results.get("distances") else []

            for i, doc in enumerate(docs):
                metadata = metadatas[i] if i < len(metadatas) else {}
                distance = distances[i] if i < len(distances) else 0

                formatted_results.append({
                    "content": doc[:500] + "..." if len(doc) > 500 else doc,
                    "document_type": metadata.get("document_type", "unknown"),
                    "source_file": metadata.get("source_file"),
                    "similarity": round(1 - distance, 3) if distance else None
                })

        return {
            "status": "success",
            "project_id": project_id,
            "project_name": project_info.get("name"),
            "query": query,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "query_time_ms": round(query_time, 2)
        }

    except Exception as e:
        logger.error(f"Project query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Project query failed: {str(e)}")


@router.get("/projects/{project_id}/stats")
async def get_project_stats(project_id: int):
    """
    Get statistics for a specific project.
    """
    try:
        chroma = get_chroma_service()

        # Get project info
        project_info = PROJECT_REGISTRY.get(project_id, {
            "name": f"Project {project_id}",
            "description": "Unknown project"
        })

        # Get project documents
        results = chroma.project_documents.get(
            where={"project_id": str(project_id)},
            limit=500
        )

        # Count by type
        type_counts: Dict[str, int] = {}
        for metadata in results.get("metadatas", []):
            doc_type = metadata.get("document_type", "unknown")
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

        return {
            "status": "success",
            "project_id": project_id,
            "project_name": project_info.get("name"),
            "description": project_info.get("description"),
            "total_documents": len(results.get("ids", [])),
            "document_types": type_counts,
            "is_registered": project_id in PROJECT_REGISTRY,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Project stats failed: {e}")
        raise HTTPException(status_code=500, detail=f"Project stats failed: {str(e)}")
