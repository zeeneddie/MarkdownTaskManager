"""
API Routes for CWE Top 25 Security Scanning.

Fase 31: Language-Agnostic Security Scanner Orchestrator.

Uses open-source tools:
- OpenGrep (30+ languages) - LGPL 2.1
- Bandit (Python) - Apache 2.0
- Gosec (Go) - Apache 2.0
- Trivy (Dependencies) - Apache 2.0
- Custom ASP Scanner (Classic ASP/VBScript)

All tools are fully open source and extensible.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
import logging

from app.services.security_scanner import (
    SecurityScanOrchestrator,
    create_security_orchestrator,
    ScannerType,
    Severity,
    CWE_TOP_25,
    SecurityReport,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/security/cwe", tags=["security-cwe"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class CWEScanRequest(BaseModel):
    """Request for CWE security scan."""
    project_path: str = Field(..., description="Path to project or file to scan")
    scanners: Optional[List[str]] = Field(None, description="Specific scanners to run (all if not specified)")
    languages: Optional[List[str]] = Field(None, description="Override language detection")
    severity_threshold: Optional[str] = Field(None, description="Minimum severity: critical, high, medium, low")
    exclude_patterns: Optional[List[str]] = Field(None, description="Glob patterns to exclude")
    include_patterns: Optional[List[str]] = Field(None, description="Glob patterns to include")


class LocationResponse(BaseModel):
    """Location in source code."""
    file: str
    start_line: int
    end_line: Optional[int]
    snippet: Optional[str]


class FindingResponse(BaseModel):
    """Security finding response."""
    id: str
    rule_id: str
    title: str
    description: str
    severity: str
    scanner: str
    location: LocationResponse
    cwe_ids: List[str]
    is_cwe_top_25: bool
    category: Optional[str]


class ScanSummaryResponse(BaseModel):
    """Scan summary statistics."""
    total_findings: int
    critical: int
    high: int
    medium: int
    low: int
    info: int
    by_scanner: Dict[str, int]


class CWECoverageResponse(BaseModel):
    """CWE coverage statistics."""
    top_25: Dict[str, int]
    all_detected: Dict[str, int]


class CWEScanResponse(BaseModel):
    """Complete CWE scan response."""
    project_path: str
    started_at: str
    completed_at: str
    duration_ms: int
    languages_detected: List[str]
    scanners_used: List[str]
    summary: ScanSummaryResponse
    cwe_coverage: CWECoverageResponse
    findings: List[FindingResponse]


class ScannerInfoResponse(BaseModel):
    """Scanner information."""
    type: str
    name: str
    languages: List[str]
    available: bool
    version: Optional[str]


# =============================================================================
# SERVICE INSTANCE
# =============================================================================


_orchestrator: Optional[SecurityScanOrchestrator] = None


def get_orchestrator() -> SecurityScanOrchestrator:
    """Get or create security scan orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = create_security_orchestrator()
    return _orchestrator


# =============================================================================
# SCAN ENDPOINTS
# =============================================================================


@router.post("/scan", response_model=CWEScanResponse)
async def run_cwe_security_scan(request: CWEScanRequest):
    """
    Run CWE-focused security scan on project.

    Uses multiple open-source scanners:
    - OpenGrep for 30+ languages (LGPL 2.1)
    - Bandit for Python (Apache 2.0)
    - Gosec for Go (Apache 2.0)
    - Trivy for dependencies (Apache 2.0)
    - Custom scanner for Classic ASP

    Automatically detects languages and selects appropriate scanners.
    Returns unified findings mapped to CWE IDs.
    """
    orchestrator = get_orchestrator()

    project_path = Path(request.project_path)
    if not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {request.project_path}")

    # Build config
    config = {}

    if request.scanners:
        try:
            scanners = [ScannerType(s) for s in request.scanners]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid scanner type: {e}")
    else:
        scanners = None

    languages = set(request.languages) if request.languages else None

    if request.exclude_patterns:
        config["exclude"] = request.exclude_patterns
    if request.include_patterns:
        config["include"] = request.include_patterns

    try:
        report_dict = await orchestrator.scan_with_report(project_path, config=config)

        # Filter by severity if requested
        if request.severity_threshold:
            threshold = Severity(request.severity_threshold.lower())
            severity_order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]
            threshold_idx = severity_order.index(threshold)
            allowed_severities = {s.value for s in severity_order[:threshold_idx + 1]}

            report_dict["findings"] = [
                f for f in report_dict["findings"]
                if f["severity"] in allowed_severities
            ]
            report_dict["summary"]["total_findings"] = len(report_dict["findings"])

        return CWEScanResponse(
            project_path=report_dict["project_path"],
            started_at=report_dict["started_at"],
            completed_at=report_dict["completed_at"],
            duration_ms=report_dict["duration_ms"],
            languages_detected=report_dict["languages_detected"],
            scanners_used=report_dict["scanners_used"],
            summary=ScanSummaryResponse(
                total_findings=report_dict["summary"]["total_findings"],
                critical=report_dict["summary"]["by_severity"].get("critical", 0),
                high=report_dict["summary"]["by_severity"].get("high", 0),
                medium=report_dict["summary"]["by_severity"].get("medium", 0),
                low=report_dict["summary"]["by_severity"].get("low", 0),
                info=report_dict["summary"]["by_severity"].get("info", 0),
                by_scanner=report_dict["summary"]["by_scanner"],
            ),
            cwe_coverage=CWECoverageResponse(
                top_25=report_dict["cwe_coverage"]["top_25"],
                all_detected=report_dict["cwe_coverage"]["all"],
            ),
            findings=[
                FindingResponse(
                    id=f["id"],
                    rule_id=f["rule_id"],
                    title=f["title"],
                    description=f["description"],
                    severity=f["severity"],
                    scanner=f["scanner"],
                    location=LocationResponse(
                        file=f["location"]["file"],
                        start_line=f["location"]["start_line"],
                        end_line=f["location"]["end_line"],
                        snippet=f["location"]["snippet"],
                    ),
                    cwe_ids=f["cwe_ids"],
                    is_cwe_top_25=f["is_cwe_top_25"],
                    category=f["category"],
                )
                for f in report_dict["findings"]
            ],
        )

    except Exception as e:
        logger.error(f"CWE security scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.post("/scan/category/{category}")
async def run_category_scan(category: str, request: CWEScanRequest):
    """
    Run security scan for specific vulnerability category.

    Categories:
    - injection: SQL, OS command, code injection (CWE-89, CWE-78, CWE-94)
    - xss: Cross-site scripting (CWE-79)
    - authentication: Auth bypass, missing auth (CWE-287, CWE-306, CWE-798)
    - authorization: Access control issues (CWE-862, CWE-863)
    - cryptography: Weak crypto (CWE-327, CWE-311)
    - path_traversal: Directory traversal (CWE-22)
    - file_upload: Unrestricted upload (CWE-434)
    - deserialization: Unsafe deserialization (CWE-502)
    - ssrf: Server-side request forgery (CWE-918)
    - csrf: Cross-site request forgery (CWE-352)
    """
    category_cwes = {
        "injection": ["CWE-89", "CWE-78", "CWE-94", "CWE-77"],
        "xss": ["CWE-79"],
        "authentication": ["CWE-287", "CWE-306", "CWE-798"],
        "authorization": ["CWE-862", "CWE-863", "CWE-269"],
        "cryptography": ["CWE-327", "CWE-311", "CWE-326"],
        "path_traversal": ["CWE-22"],
        "file_upload": ["CWE-434"],
        "deserialization": ["CWE-502"],
        "ssrf": ["CWE-918"],
        "csrf": ["CWE-352"],
    }

    if category.lower() not in category_cwes:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown category: {category}. Available: {list(category_cwes.keys())}"
        )

    full_response = await run_cwe_security_scan(request)

    target_cwes = set(category_cwes[category.lower()])
    filtered_findings = [
        f for f in full_response.findings
        if any(cwe in target_cwes for cwe in f.cwe_ids) or f.category == category.lower()
    ]

    full_response.findings = filtered_findings
    full_response.summary.total_findings = len(filtered_findings)

    return full_response


# =============================================================================
# SCANNER MANAGEMENT
# =============================================================================


@router.get("/scanners")
async def list_scanners():
    """
    List all available CWE security scanners.

    All scanners are open source and extensible.
    """
    orchestrator = get_orchestrator()

    scanner_info = {
        ScannerType.OPENGREP: {
            "name": "OpenGrep",
            "description": "Multi-language SAST scanner (Semgrep fork)",
            "languages": ["python", "javascript", "typescript", "go", "java", "ruby", "php", "rust", "c", "cpp", "csharp", "kotlin", "scala", "swift"],
            "license": "LGPL 2.1",
            "github": "https://github.com/zeeneddie/opengrep",
        },
        ScannerType.BANDIT: {
            "name": "Bandit",
            "description": "Python security scanner",
            "languages": ["python"],
            "license": "Apache 2.0",
            "github": "https://github.com/zeeneddie/bandit",
        },
        ScannerType.GOSEC: {
            "name": "Gosec",
            "description": "Go security scanner",
            "languages": ["go"],
            "license": "Apache 2.0",
            "github": "https://github.com/zeeneddie/gosec",
        },
        ScannerType.TRIVY: {
            "name": "Trivy",
            "description": "Vulnerability and dependency scanner",
            "languages": ["dependencies", "containers", "iac"],
            "license": "Apache 2.0",
            "github": "https://github.com/zeeneddie/trivy",
        },
        ScannerType.CUSTOM_ASP: {
            "name": "Classic ASP Scanner",
            "description": "Custom regex-based scanner for legacy ASP/VBScript",
            "languages": ["asp", "vbscript"],
            "license": "Internal",
            "github": None,
        },
    }

    available = orchestrator.get_available_scanners()

    return {
        "scanners": [
            {
                "type": st.value,
                "name": scanner_info[st]["name"],
                "description": scanner_info[st]["description"],
                "languages": scanner_info[st]["languages"],
                "license": scanner_info[st]["license"],
                "github": scanner_info[st]["github"],
                "available": st in available,
            }
            for st in ScannerType
            if st in scanner_info
        ]
    }


@router.get("/scanners/{scanner_type}/rules")
async def get_scanner_rules(scanner_type: str):
    """Get available rules for a specific scanner."""
    try:
        st = ScannerType(scanner_type)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown scanner: {scanner_type}")

    orchestrator = get_orchestrator()

    if st not in orchestrator._scanners:
        raise HTTPException(status_code=404, detail=f"Scanner not available: {scanner_type}")

    scanner = orchestrator._scanners[st]

    rules = {}
    if hasattr(scanner, "get_available_rules"):
        rules = scanner.get_available_rules()
    elif hasattr(scanner, "get_available_tests"):
        rules = scanner.get_available_tests()
    elif hasattr(scanner, "rules"):
        rules = {r["id"]: r["title"] for r in scanner.rules}

    return {"scanner": scanner_type, "rules": rules}


# =============================================================================
# CWE COVERAGE
# =============================================================================


@router.get("/cwe/top-25")
async def get_cwe_top_25():
    """Get CWE Top 25 (2023) information."""
    return {
        "year": 2023,
        "source": "MITRE CWE",
        "cwes": [
            {"id": cwe_id, "name": name}
            for cwe_id, name in CWE_TOP_25.items()
        ]
    }


@router.get("/cwe/coverage")
async def get_cwe_coverage():
    """Get CWE coverage statistics for available scanners."""
    orchestrator = get_orchestrator()

    coverage = {}

    for scanner_type, scanner in orchestrator._scanners.items():
        scanner_cwes = set()

        if hasattr(scanner, "BANDIT_CWE_MAP"):
            for cwes in scanner.BANDIT_CWE_MAP.values():
                scanner_cwes.update(cwes)
        elif hasattr(scanner, "GOSEC_CWE_MAP"):
            for cwes in scanner.GOSEC_CWE_MAP.values():
                scanner_cwes.update(cwes)
        elif hasattr(scanner, "rules"):
            for rule in scanner.rules:
                scanner_cwes.update(rule.get("cwe_ids", []))

        coverage[scanner_type.value] = list(scanner_cwes)

    all_covered = set()
    for cwes in coverage.values():
        all_covered.update(cwes)

    top_25_covered = all_covered.intersection(CWE_TOP_25.keys())

    return {
        "total_cwe_top_25": len(CWE_TOP_25),
        "covered_cwe_top_25": len(top_25_covered),
        "coverage_percentage": round(len(top_25_covered) / len(CWE_TOP_25) * 100, 1),
        "covered_cwes": list(top_25_covered),
        "missing_cwes": list(set(CWE_TOP_25.keys()) - top_25_covered),
        "by_scanner": coverage,
    }


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================


@router.get("/health")
async def health_check():
    """Health check for CWE security scanning service."""
    orchestrator = get_orchestrator()
    available = orchestrator.get_available_scanners()

    return {
        "status": "healthy" if available else "degraded",
        "service": "cwe-security-scanner",
        "fase": "31",
        "version": "1.0.0",
        "scanners_available": len(available),
        "scanners": [s.value for s in available],
        "open_source": True,
    }


@router.get("/languages")
async def list_supported_languages():
    """List all supported programming languages."""
    from app.services.security_scanner import EXTENSION_TO_LANGUAGE, LANGUAGE_SCANNERS

    languages = {}
    for ext, lang in EXTENSION_TO_LANGUAGE.items():
        if lang not in languages:
            languages[lang] = {"extensions": [], "scanners": []}
        languages[lang]["extensions"].append(ext)

    for lang, scanners in LANGUAGE_SCANNERS.items():
        if lang in languages:
            languages[lang]["scanners"] = [s.__name__ for s in scanners]

    return {"languages": languages}


@router.get("/severities")
async def list_severities():
    """List severity levels."""
    return {
        "severities": [
            {"value": "critical", "description": "Must fix immediately - security breach possible"},
            {"value": "high", "description": "Should fix soon - significant security risk"},
            {"value": "medium", "description": "Should fix - moderate security concern"},
            {"value": "low", "description": "Consider fixing - minor security issue"},
            {"value": "info", "description": "Informational - best practice suggestion"},
        ]
    }
