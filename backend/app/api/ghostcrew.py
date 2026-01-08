"""
GhostCrew API - Week 80-82

API endpoints for security scanning, pattern learning,
and compliance checking.
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.ghostcrew_service import GhostCrewService, get_ghostcrew_service
from app.services.shadow_graph_service import ShadowGraphService, get_shadow_graph_service
from app.services.security_rag_service import SecurityRAGService, get_security_rag_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ghostcrew", tags=["ghostcrew"])


# =========================================================================
# Request/Response Models
# =========================================================================

class AssistRequest(BaseModel):
    """Request for interactive security assistance."""
    query: str = Field(..., description="Security question or concern")
    context: Optional[str] = Field(None, description="Optional code context")
    project_id: Optional[int] = Field(None, description="Optional project association")
    include_knowledge: bool = Field(True, description="Include OWASP/CWE references")


class ScanRequest(BaseModel):
    """Request for autonomous security scan."""
    repo_path: str = Field(..., description="Path to repository to scan")
    project_id: Optional[int] = Field(None, description="Project association")
    scan_type: str = Field("full", description="Scan type: full, quick, targeted")
    workflow_type: Optional[str] = Field(None, description="Triggering workflow type")
    workflow_session_id: Optional[str] = Field(None, description="Workflow session ID")
    file_extensions: Optional[List[str]] = Field(None, description="File extensions to scan")


class CrewRequest(BaseModel):
    """Request for multi-agent security analysis."""
    project_id: int = Field(..., description="Project to analyze")
    target_path: Optional[str] = Field(None, description="Specific path to analyze")
    agents: Optional[List[str]] = Field(None, description="Agents to run")
    workflow_type: Optional[str] = Field(None, description="Triggering workflow type")
    workflow_session_id: Optional[str] = Field(None, description="Workflow session ID")


class FalsePositiveRequest(BaseModel):
    """Request to mark finding as false positive."""
    reason: str = Field(..., description="Reason for false positive classification")
    marked_by: str = Field(..., description="User/agent marking the FP")


class RemediationRequest(BaseModel):
    """Request for remediation guidance."""
    vulnerability_type: str = Field(..., description="Type of vulnerability")
    language: Optional[str] = Field(None, description="Programming language")
    framework: Optional[str] = Field(None, description="Framework")


# =========================================================================
# GHOSTCREW SCANNING ENDPOINTS
# =========================================================================

@router.post("/assist")
async def security_assist(
    request: AssistRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Interactive security assistance mode.

    Get security guidance and recommendations based on a query.
    Optionally provide code context for specific analysis.
    """
    try:
        service = get_ghostcrew_service(db)
        result = await service.assist(
            query=request.query,
            context=request.context,
            project_id=request.project_id,
            include_knowledge=request.include_knowledge
        )
        return result
    except Exception as e:
        logger.error(f"Assist failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan")
async def security_scan(
    request: ScanRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Autonomous security scanning mode.

    Scan a repository or directory for security vulnerabilities.
    Returns findings with severity, OWASP/CWE mapping, and recommendations.
    """
    try:
        service = get_ghostcrew_service(db)
        result = await service.scan_autonomous(
            repo_path=request.repo_path,
            project_id=request.project_id,
            scan_type=request.scan_type,
            workflow_type=request.workflow_type,
            workflow_session_id=request.workflow_session_id,
            file_extensions=request.file_extensions
        )
        return result
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crew/{project_id}")
async def run_security_crew(
    project_id: int,
    request: CrewRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Multi-agent security analysis mode.

    Run multiple security agents (SecurityAgent, AuditAgent, ComplianceAgent)
    in parallel for comprehensive security analysis.
    """
    try:
        service = get_ghostcrew_service(db)
        result = await service.run_crew(
            project_id=project_id,
            target_path=request.target_path,
            agents=request.agents,
            workflow_type=request.workflow_type,
            workflow_session_id=request.workflow_session_id
        )
        return result
    except Exception as e:
        logger.error(f"Crew run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# SCAN MANAGEMENT ENDPOINTS
# =========================================================================

@router.get("/scans/{scan_id}")
async def get_scan(
    scan_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get scan details by ID."""
    service = get_ghostcrew_service(db)
    scan = await service.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan.to_dict()


@router.get("/scans/{scan_id}/findings")
async def get_scan_findings(
    scan_id: UUID,
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Get findings for a scan."""
    service = get_ghostcrew_service(db)
    findings = await service.get_scan_findings(scan_id, severity, limit)
    return [f.to_dict() for f in findings]


@router.get("/projects/{project_id}/scans")
async def get_project_scans(
    project_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get scans for a project."""
    service = get_ghostcrew_service(db)
    scans = await service.get_project_scans(project_id, limit)
    return [s.to_dict() for s in scans]


@router.post("/findings/{finding_id}/false-positive")
async def mark_false_positive(
    finding_id: UUID,
    request: FalsePositiveRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a finding as false positive.

    This creates a learning record and updates pattern accuracy.
    Future scans will use this feedback to reduce similar false positives.
    """
    service = get_ghostcrew_service(db)
    result = await service.mark_finding_false_positive(
        finding_id=finding_id,
        reason=request.reason,
        marked_by=request.marked_by
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# =========================================================================
# SHADOW GRAPH (PATTERN LEARNING) ENDPOINTS
# =========================================================================

@router.get("/shadow-graph/patterns")
async def get_patterns(
    pattern_type: str = Query("vulnerability", description="Pattern type"),
    language: Optional[str] = Query(None, description="Filter by language"),
    min_accuracy: float = Query(0.5, ge=0, le=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Get learned security patterns."""
    service = get_shadow_graph_service(db)
    patterns = await service.get_patterns(
        language=language,
        pattern_type=pattern_type,
        min_accuracy=min_accuracy,
        limit=limit
    )
    return [p.to_dict() for p in patterns]


@router.get("/shadow-graph/stats")
async def get_learning_stats(
    project_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get pattern learning statistics."""
    service = get_shadow_graph_service(db)
    return await service.get_learning_stats(project_id, days)


@router.get("/shadow-graph/top-patterns")
async def get_top_patterns(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get most frequently detected patterns."""
    service = get_shadow_graph_service(db)
    return await service.get_top_patterns(limit)


@router.post("/shadow-graph/confirm/{finding_id}")
async def confirm_vulnerability(
    finding_id: UUID,
    confirmed_by: str = Query(..., description="Who confirmed"),
    db: AsyncSession = Depends(get_db)
):
    """Confirm a finding as a true positive."""
    service = get_shadow_graph_service(db)
    result = await service.confirm_vulnerability(finding_id, confirmed_by)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/shadow-graph/recommendations/{vulnerability}")
async def get_recommendations(
    vulnerability: str,
    language: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get recommendations for a vulnerability type."""
    service = get_shadow_graph_service(db)
    return await service.get_recommendations(vulnerability, language)


# =========================================================================
# SECURITY KNOWLEDGE (RAG) ENDPOINTS
# =========================================================================

@router.post("/knowledge/initialize")
async def initialize_knowledge_base(
    db: AsyncSession = Depends(get_db)
):
    """
    Initialize the security knowledge base.

    Loads OWASP Top 10 2021 and common CWE entries.
    Should be called once during setup.
    """
    service = get_security_rag_service(db)
    return await service.initialize_knowledge_base()


@router.get("/knowledge/owasp/{category}")
async def get_owasp_guidance(
    category: str,
    db: AsyncSession = Depends(get_db)
):
    """Get OWASP guidance for a category."""
    service = get_security_rag_service(db)
    result = await service.get_owasp_guidance(category)
    if not result:
        raise HTTPException(status_code=404, detail="OWASP category not found")
    return result


@router.get("/knowledge/cwe/{cwe_id}")
async def get_cwe_guidance(
    cwe_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get CWE guidance."""
    service = get_security_rag_service(db)
    result = await service.get_cwe_guidance(cwe_id)
    if not result:
        raise HTTPException(status_code=404, detail="CWE not found")
    return result


@router.post("/knowledge/remediation")
async def get_remediation(
    request: RemediationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get remediation guidance for a vulnerability."""
    service = get_security_rag_service(db)
    return await service.get_remediation(
        vulnerability_type=request.vulnerability_type,
        language=request.language,
        framework=request.framework
    )


@router.get("/knowledge/search")
async def search_knowledge(
    query: str = Query(..., min_length=2),
    knowledge_type: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Search security knowledge base."""
    service = get_security_rag_service(db)
    return await service.search_knowledge(query, knowledge_type, limit)


@router.get("/knowledge/checklist")
async def get_security_checklist(
    language: Optional[str] = Query(None),
    framework: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get a security checklist."""
    service = get_security_rag_service(db)
    return await service.get_security_checklist(language, framework)


# =========================================================================
# DASHBOARD ENDPOINTS
# =========================================================================

@router.get("/dashboard")
async def get_dashboard_data(
    project_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard overview data."""
    ghostcrew = get_ghostcrew_service(db)
    shadow = get_shadow_graph_service(db)

    # Get recent scans
    if project_id:
        scans = await ghostcrew.get_project_scans(project_id, limit=10)
    else:
        scans = []

    # Get learning stats
    stats = await shadow.get_learning_stats(project_id, days=30)

    # Get top patterns
    top_patterns = await shadow.get_top_patterns(limit=5)

    return {
        "recent_scans": [s.to_dict() for s in scans],
        "learning_stats": stats,
        "top_patterns": top_patterns,
        "total_scans": len(scans),
    }
