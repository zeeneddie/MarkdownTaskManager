"""
Security API Endpoints - CyberStrike Integration

Week 63: Automated security scanning and quality gate integration

Endpoints:
- POST /security/scan - Full security scan
- POST /security/quick-scan - Quick pattern-based scan
- GET /security/owasp/{project_id} - OWASP Top 10 report
- POST /security/pr-scan - Pull request focused scan
- GET /security/gate/{project_id} - Security gate status
- POST /security/pre-deployment - Pre-deployment validation
- GET /security/quinn-context/{project_id} - Quinn agent context
- GET /security/vulnerabilities - List vulnerabilities
- GET /security/dashboard/stats - Dashboard statistics
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.cyberstrike_service import (
    CyberStrikeService,
    VulnerabilitySeverity,
    OWASPCategory,
    ScannerType
)
from app.services.security_workflow_service import (
    SecurityWorkflowService,
    SecurityWorkflowConfig,
    SecurityGateDecision,
    WorkflowType
)

router = APIRouter(prefix="/api/security", tags=["Security"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ScanRequest(BaseModel):
    """Request to initiate a security scan."""
    project_path: str = Field(..., description="Path to project to scan")
    scan_type: str = Field("full", description="Scan type: full, quick, owasp")
    include_external: bool = Field(True, description="Include Bandit/Safety scanners")
    workflow_type: Optional[str] = Field(None, description="Workflow context")


class PRScanRequest(BaseModel):
    """Request to scan pull request changes."""
    base_path: str = Field(..., description="Base project path")
    changed_files: List[str] = Field(..., description="List of changed file paths")


class PreDeploymentRequest(BaseModel):
    """Request for pre-deployment security check."""
    project_path: str = Field(..., description="Path to project")
    deployment_target: str = Field("staging", description="Target: staging, production")


class SecurityGateRequest(BaseModel):
    """Request to evaluate security gate."""
    project_path: str = Field(..., description="Path to project")
    workflow_type: str = Field("new_feature", description="Workflow type")
    item_id: Optional[str] = Field(None, description="Item identifier")


class VulnerabilityResponse(BaseModel):
    """Single vulnerability in response."""
    id: str
    title: str
    description: str
    severity: str
    owasp_category: str
    file_path: Optional[str]
    line_number: Optional[int]
    code_snippet: Optional[str]
    scanner: str
    cwe_id: Optional[str]
    remediation: Optional[str]


class ScanResponse(BaseModel):
    """Response from a security scan."""
    scan_id: str
    status: str
    project_path: str
    scan_type: str
    vulnerabilities_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    quality_gate_passed: bool
    deployment_blocked: bool
    started_at: str
    completed_at: Optional[str]
    scanners_used: List[str]


class SecurityGateResponse(BaseModel):
    """Response from security gate evaluation."""
    decision: str
    can_deploy: bool
    requires_review: bool
    blocking_issues_count: int
    warnings_count: int
    quinn_assessment: Optional[str]
    recommendations: List[str]


# ============================================================================
# SCAN STORAGE (In-memory for MVP, would use DB in production)
# ============================================================================

_scan_results: dict = {}
_scan_counter: int = 0


# ============================================================================
# ENDPOINTS - SCANNING
# ============================================================================

@router.post("/scan", response_model=ScanResponse)
async def run_security_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Run a full security scan on a project.

    Features:
    - OWASP Top 10 vulnerability detection
    - Pattern-based code analysis
    - Optional Bandit/Safety integration
    - Quality gate evaluation

    Returns scan results with vulnerability counts and recommendations.
    """
    global _scan_counter

    service = CyberStrikeService(project_path=request.project_path)

    try:
        result = await service.full_scan(
            path=request.project_path,
            scan_type=request.scan_type,
            include_external=request.include_external
        )

        # Store result
        _scan_counter += 1
        _scan_results[result.scan_id] = result

        summary = result.summary

        return ScanResponse(
            scan_id=result.scan_id,
            status=result.status,
            project_path=result.project_path,
            scan_type=result.scan_type,
            vulnerabilities_count=len(result.vulnerabilities),
            critical_count=summary.get("critical_count", 0),
            high_count=summary.get("high_count", 0),
            medium_count=summary.get("by_severity", {}).get("medium", 0),
            low_count=summary.get("by_severity", {}).get("low", 0),
            quality_gate_passed=summary.get("quality_gate_passed", True),
            deployment_blocked=summary.get("deployment_blocked", False),
            started_at=result.started_at.isoformat(),
            completed_at=result.completed_at.isoformat() if result.completed_at else None,
            scanners_used=[s.value for s in result.scanners_used]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.post("/quick-scan")
async def run_quick_scan(
    request: ScanRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run a quick security scan (pattern-based only).

    Faster than full scan, suitable for:
    - Pre-commit hooks
    - IDE integration
    - Quick validation during development
    """
    service = CyberStrikeService(project_path=request.project_path)

    try:
        result = await service.quick_scan(path=request.project_path)

        _scan_results[result.scan_id] = result

        return {
            "scan_id": result.scan_id,
            "status": result.status,
            "vulnerabilities_count": len(result.vulnerabilities),
            "critical_count": result.summary.get("critical_count", 0),
            "high_count": result.summary.get("high_count", 0),
            "quality_gate_passed": result.summary.get("quality_gate_passed", True),
            "duration_ms": (
                (result.completed_at - result.started_at).total_seconds() * 1000
                if result.completed_at else None
            )
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick scan failed: {str(e)}")


@router.post("/pr-scan")
async def scan_pull_request(
    request: PRScanRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Scan only changed files in a pull request.

    Optimized for:
    - CI/CD pipeline integration
    - Fast PR review feedback
    - Focused vulnerability detection
    """
    service = SecurityWorkflowService(db=db)

    try:
        result = await service.scan_pull_request(
            base_path=request.base_path,
            changed_files=request.changed_files
        )

        return {
            "decision": result.decision.value,
            "can_deploy": result.can_deploy,
            "files_scanned": len(request.changed_files),
            "vulnerabilities_found": len(result.scan_result.vulnerabilities) if result.scan_result else 0,
            "blocking_issues": result.blocking_issues[:5],  # Top 5
            "warnings": result.warnings[:10],  # Top 10
            "quinn_assessment": result.quinn_assessment,
            "recommendations": result.recommendations
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PR scan failed: {str(e)}")


# ============================================================================
# ENDPOINTS - OWASP ANALYSIS
# ============================================================================

@router.get("/owasp/{project_id}")
async def get_owasp_report(
    project_id: int,
    project_path: str = Query(..., description="Path to project"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get OWASP Top 10 focused security report.

    Returns vulnerabilities grouped by OWASP 2021 categories:
    - A01: Broken Access Control
    - A02: Cryptographic Failures
    - A03: Injection
    - A04: Insecure Design
    - A05: Security Misconfiguration
    - A06: Vulnerable Components
    - A07: Authentication Failures
    - A08: Data Integrity Failures
    - A09: Logging Failures
    - A10: SSRF
    """
    service = CyberStrikeService(project_path=project_path)

    try:
        owasp_results = await service.owasp_scan(path=project_path)

        # Format response
        report = {
            "project_id": project_id,
            "timestamp": datetime.utcnow().isoformat(),
            "categories": {}
        }

        total_vulns = 0
        for category in OWASPCategory:
            vulns = owasp_results.get(category.value, [])
            report["categories"][category.value] = {
                "count": len(vulns),
                "vulnerabilities": [
                    {
                        "id": v.id,
                        "title": v.title,
                        "severity": v.severity.value,
                        "file": v.file_path,
                        "line": v.line_number,
                        "remediation": v.remediation
                    }
                    for v in vulns[:10]  # Top 10 per category
                ]
            }
            total_vulns += len(vulns)

        report["total_vulnerabilities"] = total_vulns
        report["compliance_score"] = max(0, 100 - (total_vulns * 5))  # Simple scoring

        return report

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OWASP scan failed: {str(e)}")


# ============================================================================
# ENDPOINTS - SECURITY GATE
# ============================================================================

@router.post("/gate/evaluate", response_model=SecurityGateResponse)
async def evaluate_security_gate(
    request: SecurityGateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluate security gate for deployment decision.

    Decision outcomes:
    - PASS: All clear, proceed to deployment
    - WARN: Issues found but non-blocking
    - BLOCK: Critical issues, cannot proceed
    - ERROR: Scan failed, manual review required
    """
    service = SecurityWorkflowService(db=db)

    try:
        workflow_type = WorkflowType(request.workflow_type.lower())
        result = await service.evaluate_security_gate(
            project_path=request.project_path,
            workflow_type=workflow_type,
            item_id=request.item_id
        )

        return SecurityGateResponse(
            decision=result.decision.value,
            can_deploy=result.can_deploy,
            requires_review=result.requires_review,
            blocking_issues_count=len(result.blocking_issues),
            warnings_count=len(result.warnings),
            quinn_assessment=result.quinn_assessment,
            recommendations=result.recommendations
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid workflow type: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gate evaluation failed: {str(e)}")


@router.get("/gate/{project_id}")
async def get_security_gate_status(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current security gate status for a project.

    Returns the latest scan result and gate decision.
    """
    # Find latest scan for project
    latest_scan = None
    for scan_id, scan in _scan_results.items():
        if str(project_id) in scan.project_path:
            if not latest_scan or scan.completed_at > latest_scan.completed_at:
                latest_scan = scan

    if not latest_scan:
        return {
            "project_id": project_id,
            "status": "no_scans",
            "message": "No security scans found for this project"
        }

    return {
        "project_id": project_id,
        "latest_scan_id": latest_scan.scan_id,
        "scan_status": latest_scan.status,
        "last_scanned": latest_scan.completed_at.isoformat() if latest_scan.completed_at else None,
        "vulnerabilities_count": len(latest_scan.vulnerabilities),
        "critical_count": latest_scan.summary.get("critical_count", 0),
        "high_count": latest_scan.summary.get("high_count", 0),
        "quality_gate_passed": latest_scan.summary.get("quality_gate_passed", True),
        "deployment_blocked": latest_scan.summary.get("deployment_blocked", False)
    }


@router.post("/pre-deployment")
async def run_pre_deployment_check(
    request: PreDeploymentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run pre-deployment security validation.

    More comprehensive scan for production deployments.
    Stricter thresholds for production target.
    """
    service = SecurityWorkflowService(db=db)

    try:
        result = await service.pre_deployment_check(
            project_path=request.project_path,
            deployment_target=request.deployment_target
        )

        return {
            "deployment_target": request.deployment_target,
            "decision": result.decision.value,
            "can_deploy": result.can_deploy,
            "requires_approval": result.requires_review,
            "blocking_issues": result.blocking_issues[:10],
            "warnings": result.warnings[:10],
            "quinn_assessment": result.quinn_assessment,
            "recommendations": result.recommendations,
            "timestamp": result.timestamp.isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pre-deployment check failed: {str(e)}")


# ============================================================================
# ENDPOINTS - QUINN INTEGRATION
# ============================================================================

@router.get("/quinn-context/{project_id}")
async def get_quinn_security_context(
    project_id: int,
    project_path: str = Query(..., description="Path to project"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get security context for Quinn Quality Inspector agent.

    Returns formatted security summary for Quinn's quality assessments.
    """
    service = CyberStrikeService(project_path=project_path)

    try:
        context = await service.get_quinn_security_context(path=project_path)

        return {
            "project_id": project_id,
            **context
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Quinn context: {str(e)}")


# ============================================================================
# ENDPOINTS - VULNERABILITY MANAGEMENT
# ============================================================================

@router.get("/vulnerabilities")
async def list_vulnerabilities(
    scan_id: Optional[str] = Query(None, description="Filter by scan ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    owasp_category: Optional[str] = Query(None, description="Filter by OWASP category"),
    limit: int = Query(50, description="Max results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    List vulnerabilities from scans with filtering options.
    """
    vulnerabilities = []

    # Collect from scan results
    for sid, scan in _scan_results.items():
        if scan_id and sid != scan_id:
            continue

        for vuln in scan.vulnerabilities:
            # Apply filters
            if severity and vuln.severity.value != severity.lower():
                continue
            if owasp_category and owasp_category not in vuln.owasp_category.value:
                continue

            vulnerabilities.append({
                "scan_id": sid,
                "id": vuln.id,
                "title": vuln.title,
                "description": vuln.description,
                "severity": vuln.severity.value,
                "owasp_category": vuln.owasp_category.value,
                "file_path": vuln.file_path,
                "line_number": vuln.line_number,
                "code_snippet": vuln.code_snippet,
                "scanner": vuln.scanner.value,
                "cwe_id": vuln.cwe_id,
                "remediation": vuln.remediation
            })

    # Apply pagination
    total = len(vulnerabilities)
    vulnerabilities = vulnerabilities[offset:offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "vulnerabilities": vulnerabilities
    }


@router.get("/vulnerability/{vuln_id}")
async def get_vulnerability_details(
    vuln_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific vulnerability.
    """
    # Search in scan results
    for scan in _scan_results.values():
        for vuln in scan.vulnerabilities:
            if vuln.id == vuln_id:
                return {
                    "id": vuln.id,
                    "title": vuln.title,
                    "description": vuln.description,
                    "severity": vuln.severity.value,
                    "owasp_category": vuln.owasp_category.value,
                    "file_path": vuln.file_path,
                    "line_number": vuln.line_number,
                    "column": vuln.column,
                    "code_snippet": vuln.code_snippet,
                    "scanner": vuln.scanner.value,
                    "cwe_id": vuln.cwe_id,
                    "cvss_score": vuln.cvss_score,
                    "remediation": vuln.remediation,
                    "references": vuln.references,
                    "metadata": vuln.metadata
                }

    raise HTTPException(status_code=404, detail="Vulnerability not found")


# ============================================================================
# ENDPOINTS - DASHBOARD
# ============================================================================

@router.get("/dashboard/stats")
async def get_dashboard_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get security dashboard statistics.

    Aggregates data from all scans for dashboard visualization.
    """
    stats = {
        "total_scans": len(_scan_results),
        "total_vulnerabilities": 0,
        "by_severity": {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        },
        "by_owasp_category": {},
        "by_scanner": {},
        "scans_passed": 0,
        "scans_blocked": 0,
        "recent_scans": [],
        "top_vulnerabilities": [],
        "owasp_compliance": {}
    }

    # Initialize OWASP categories
    for cat in OWASPCategory:
        stats["by_owasp_category"][cat.value] = 0
        stats["owasp_compliance"][cat.value] = True  # Assume compliant

    # Aggregate statistics
    all_vulns = []
    for scan in _scan_results.values():
        # Count vulnerabilities
        stats["total_vulnerabilities"] += len(scan.vulnerabilities)

        # Count by severity
        for vuln in scan.vulnerabilities:
            sev = vuln.severity.value
            if sev in stats["by_severity"]:
                stats["by_severity"][sev] += 1

            # Count by OWASP
            cat = vuln.owasp_category.value
            stats["by_owasp_category"][cat] = stats["by_owasp_category"].get(cat, 0) + 1
            stats["owasp_compliance"][cat] = False  # Has issues

            # Count by scanner
            scanner = vuln.scanner.value
            stats["by_scanner"][scanner] = stats["by_scanner"].get(scanner, 0) + 1

            all_vulns.append(vuln)

        # Count pass/block
        if scan.summary.get("quality_gate_passed", True):
            stats["scans_passed"] += 1
        else:
            stats["scans_blocked"] += 1

        # Recent scans
        stats["recent_scans"].append({
            "scan_id": scan.scan_id,
            "project": scan.project_path.split("/")[-1],
            "status": scan.status,
            "vulnerabilities": len(scan.vulnerabilities),
            "timestamp": scan.completed_at.isoformat() if scan.completed_at else None
        })

    # Sort recent scans
    stats["recent_scans"] = sorted(
        stats["recent_scans"],
        key=lambda x: x["timestamp"] or "",
        reverse=True
    )[:10]

    # Top vulnerabilities (critical/high)
    critical_vulns = [v for v in all_vulns if v.severity in [VulnerabilitySeverity.CRITICAL, VulnerabilitySeverity.HIGH]]
    stats["top_vulnerabilities"] = [
        {
            "id": v.id,
            "title": v.title,
            "severity": v.severity.value,
            "category": v.owasp_category.value,
            "file": v.file_path
        }
        for v in critical_vulns[:10]
    ]

    # Calculate compliance score
    compliant_categories = sum(1 for v in stats["owasp_compliance"].values() if v)
    stats["owasp_compliance_score"] = (compliant_categories / len(OWASPCategory)) * 100

    return stats


@router.get("/dashboard/trends")
async def get_security_trends(
    days: int = Query(30, description="Number of days for trend"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get security vulnerability trends over time.
    """
    # Group scans by date
    daily_stats = {}

    for scan in _scan_results.values():
        if not scan.completed_at:
            continue

        date_key = scan.completed_at.date().isoformat()

        if date_key not in daily_stats:
            daily_stats[date_key] = {
                "date": date_key,
                "scans": 0,
                "vulnerabilities": 0,
                "critical": 0,
                "high": 0
            }

        daily_stats[date_key]["scans"] += 1
        daily_stats[date_key]["vulnerabilities"] += len(scan.vulnerabilities)
        daily_stats[date_key]["critical"] += scan.summary.get("critical_count", 0)
        daily_stats[date_key]["high"] += scan.summary.get("high_count", 0)

    # Sort by date
    trends = sorted(daily_stats.values(), key=lambda x: x["date"])

    return {
        "period_days": days,
        "data_points": len(trends),
        "trends": trends
    }


# ============================================================================
# PATTERN MANAGEMENT
# ============================================================================

@router.get("/patterns")
async def get_pattern_statistics():
    """
    Get statistics about loaded security patterns.

    Returns:
        Pattern count by language, severity, and OWASP category.
    """
    service = CyberStrikeService()
    stats = service.get_pattern_statistics()

    return {
        "status": "ok",
        **stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/patterns/languages")
async def get_supported_languages():
    """
    Get list of supported languages for scanning.
    """
    service = CyberStrikeService()

    return {
        "languages": service.get_supported_languages(),
        "extensions": list(service.get_supported_extensions()),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/patterns/reload")
async def reload_patterns():
    """
    Reload security patterns from configuration files.

    Use this after modifying pattern YAML files.
    """
    service = CyberStrikeService()
    stats = service.reload_patterns()

    return {
        "status": "reloaded",
        **stats,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def security_health():
    """Health check for security service."""
    # Check available scanners
    test_service = CyberStrikeService()

    return {
        "status": "healthy",
        "service": "cyberstrike_security",
        "available_scanners": [s.value for s in test_service._available_scanners],
        "supported_languages": test_service.get_supported_languages(),
        "pattern_count": test_service.get_pattern_statistics().get("total_patterns", 0),
        "total_scans_performed": len(_scan_results),
        "owasp_coverage": [cat.value for cat in OWASPCategory],
        "timestamp": datetime.utcnow().isoformat()
    }
