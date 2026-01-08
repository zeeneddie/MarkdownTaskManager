"""
Migration Security API - Quinn Integration Endpoints

Week 68 Day 1-2: REST API for legacy security analysis during migration
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

from app.services.migration_security_service import (
    MigrationSecurityService,
    LegacyStack,
    SecuritySeverity,
    OWASPCategory
)


router = APIRouter(prefix="/api/migration-security", tags=["Migration Security"])

# Initialize service
security_service = MigrationSecurityService()


# ==================== Request/Response Models ====================

class AnalyzeRequest(BaseModel):
    """Request to analyze directory for security issues"""
    directory: str = Field(..., description="Path to source code directory")
    stacks: Optional[List[str]] = Field(None, description="Specific stacks to check (auto-detect if None)")
    severity_threshold: str = Field("low", description="Minimum severity: critical, high, medium, low, info")


class QuinnReviewRequest(BaseModel):
    """Request to generate Quinn review context"""
    directory: str = Field(..., description="Path to source code directory")
    focus_categories: Optional[List[str]] = Field(None, description="OWASP categories to focus on")


class PatternLookupRequest(BaseModel):
    """Request to lookup patterns"""
    stack: Optional[str] = Field(None, description="Filter by legacy stack")
    owasp_category: Optional[str] = Field(None, description="Filter by OWASP category")


# ==================== API Endpoints ====================

@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get security service status and pattern statistics"""
    return security_service.get_status()


@router.post("/analyze")
async def analyze_directory(request: AnalyzeRequest) -> Dict[str, Any]:
    """
    Analyze directory for legacy security vulnerabilities

    Returns:
        Complete security analysis with findings, risk score, and Quinn context
    """
    # Parse stacks
    stacks = None
    if request.stacks:
        try:
            stacks = [LegacyStack(s.lower()) for s in request.stacks]
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stack: {e}. Valid stacks: {[s.value for s in LegacyStack]}"
            )

    # Parse severity threshold
    try:
        severity = SecuritySeverity(request.severity_threshold.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid severity. Valid values: {[s.value for s in SecuritySeverity]}"
        )

    result = security_service.analyze_directory(
        directory=request.directory,
        stacks=stacks,
        severity_threshold=severity
    )

    return result.to_dict()


@router.post("/quinn-context")
async def generate_quinn_context(request: QuinnReviewRequest) -> Dict[str, Any]:
    """
    Generate Quinn agent context for security review

    Returns:
        Focused context for Quinn to perform detailed security review
    """
    # First run analysis
    result = security_service.analyze_directory(request.directory)

    # Filter by focus categories if specified
    if request.focus_categories:
        findings = [
            f for f in result.findings
            if any(cat in f.owasp_category.value for cat in request.focus_categories)
        ]
    else:
        findings = result.findings

    return {
        "analysis_id": result.analysis_id,
        "quinn_context": {
            "summary": result.quinn_context.summary,
            "focus_areas": result.quinn_context.focus_areas,
            "priority_files": result.quinn_context.priority_files[:15],
            "owasp_checklist": result.quinn_context.owasp_checklist,
            "questions_for_review": result.quinn_context.questions_for_review,
            "recommended_tools": result.quinn_context.recommended_tools,
            "filtered_findings_count": len(findings)
        },
        "severity_summary": {
            "critical": sum(1 for f in findings if f.severity == SecuritySeverity.CRITICAL),
            "high": sum(1 for f in findings if f.severity == SecuritySeverity.HIGH),
            "medium": sum(1 for f in findings if f.severity == SecuritySeverity.MEDIUM),
            "low": sum(1 for f in findings if f.severity == SecuritySeverity.LOW)
        },
        "recommendations": result.recommendations
    }


@router.get("/patterns")
async def list_patterns(
    stack: Optional[str] = Query(None, description="Filter by legacy stack"),
    owasp_category: Optional[str] = Query(None, description="Filter by OWASP category")
) -> Dict[str, Any]:
    """
    List available security patterns

    Returns:
        Patterns organized by category or stack
    """
    if stack:
        try:
            legacy_stack = LegacyStack(stack.lower())
            patterns = security_service.get_patterns_by_stack(legacy_stack)
            return {
                "stack": stack,
                "pattern_count": len(patterns),
                "patterns": patterns
            }
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stack. Valid stacks: {[s.value for s in LegacyStack]}"
            )

    if owasp_category:
        all_patterns = security_service.get_patterns_by_owasp()
        matching = {
            k: v for k, v in all_patterns.items()
            if owasp_category.upper() in k
        }
        return {
            "filter": owasp_category,
            "categories": matching
        }

    # Return all organized by OWASP
    return {
        "total_patterns": len(security_service.patterns),
        "by_owasp_category": security_service.get_patterns_by_owasp()
    }


@router.get("/patterns/{pattern_id}")
async def get_pattern_detail(pattern_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific pattern

    Returns:
        Full pattern definition with examples and remediation
    """
    for pattern in security_service.patterns:
        if pattern.id == pattern_id:
            return {
                "id": pattern.id,
                "name": pattern.name,
                "owasp_category": pattern.owasp_category.value,
                "severity": pattern.severity.value,
                "stacks": [s.value for s in pattern.stacks],
                "pattern": pattern.pattern,
                "description": pattern.description,
                "legacy_example": pattern.legacy_example,
                "modern_remediation": pattern.modern_remediation,
                "remediation_effort": pattern.remediation_effort.value,
                "cwe_id": pattern.cwe_id,
                "references": pattern.references
            }

    raise HTTPException(status_code=404, detail=f"Pattern {pattern_id} not found")


@router.get("/owasp-categories")
async def list_owasp_categories() -> Dict[str, Any]:
    """
    List all OWASP Top 10 2021 categories with pattern counts

    Returns:
        OWASP categories with coverage statistics
    """
    patterns_by_owasp = security_service.get_patterns_by_owasp()

    categories = []
    for cat in OWASPCategory:
        patterns = patterns_by_owasp.get(cat.value, [])
        categories.append({
            "id": cat.name,
            "name": cat.value,
            "pattern_count": len(patterns),
            "severity_distribution": {
                "critical": sum(1 for p in patterns if p["severity"] == "critical"),
                "high": sum(1 for p in patterns if p["severity"] == "high"),
                "medium": sum(1 for p in patterns if p["severity"] == "medium"),
                "low": sum(1 for p in patterns if p["severity"] == "low")
            }
        })

    return {
        "total_categories": len(categories),
        "categories": categories
    }


@router.get("/stacks")
async def list_stacks() -> Dict[str, Any]:
    """
    List all supported legacy stacks with pattern counts

    Returns:
        Legacy stacks with coverage statistics
    """
    stacks = []
    for stack in LegacyStack:
        patterns = security_service.get_patterns_by_stack(stack)
        stacks.append({
            "id": stack.value,
            "name": stack.name.replace("_", " ").title(),
            "pattern_count": len(patterns),
            "file_extensions": [
                ext for ext in
                security_service._collect_files.__code__.co_consts
                if isinstance(ext, str) and ext.startswith(".")
            ] if hasattr(security_service, '_collect_files') else []
        })

    return {
        "total_stacks": len(stacks),
        "stacks": stacks
    }


@router.get("/risk-assessment/{analysis_id}")
async def get_risk_assessment(
    analysis_id: str,
    directory: str = Query(..., description="Directory path for re-analysis")
) -> Dict[str, Any]:
    """
    Get detailed risk assessment for migration planning

    Returns:
        Risk scores, blockers, and remediation estimates
    """
    result = security_service.analyze_directory(directory)

    return {
        "analysis_id": analysis_id,
        "risk_score": {
            "total": result.risk_score.total_score,
            "grade": _score_to_grade(result.risk_score.total_score),
            "critical_issues": result.risk_score.critical_count,
            "high_issues": result.risk_score.high_count,
            "medium_issues": result.risk_score.medium_count,
            "low_issues": result.risk_score.low_count
        },
        "migration_readiness": {
            "can_migrate": result.risk_score.critical_count == 0,
            "blockers": result.risk_score.migration_blockers,
            "estimated_remediation_hours": result.risk_score.estimated_remediation_hours
        },
        "owasp_coverage": result.risk_score.owasp_coverage,
        "top_risks": result.risk_score.top_risks,
        "recommendations": result.recommendations
    }


@router.post("/compare")
async def compare_analyses(
    directories: List[str] = Query(..., description="Directories to compare")
) -> Dict[str, Any]:
    """
    Compare security analysis across multiple directories/branches

    Returns:
        Comparison of findings and risk scores
    """
    if len(directories) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 directories required for comparison"
        )

    results = []
    for directory in directories:
        result = security_service.analyze_directory(directory)
        results.append({
            "directory": directory,
            "total_findings": len(result.findings),
            "risk_score": result.risk_score.total_score,
            "critical": result.risk_score.critical_count,
            "high": result.risk_score.high_count,
            "stacks": [s.value for s in result.stacks_detected]
        })

    # Calculate improvements/regressions
    if len(results) >= 2:
        baseline = results[0]
        comparison = results[-1]

        delta = {
            "findings_delta": comparison["total_findings"] - baseline["total_findings"],
            "risk_delta": comparison["risk_score"] - baseline["risk_score"],
            "critical_delta": comparison["critical"] - baseline["critical"],
            "improved": comparison["risk_score"] < baseline["risk_score"]
        }
    else:
        delta = None

    return {
        "analyses": results,
        "delta": delta
    }


def _score_to_grade(score: float) -> str:
    """Convert numeric score to letter grade"""
    if score < 10:
        return "A"
    elif score < 25:
        return "B"
    elif score < 50:
        return "C"
    elif score < 75:
        return "D"
    else:
        return "F"
