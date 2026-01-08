# backend/app/api/static_analysis.py
"""
Static Analysis API - Fase 15: Hybrid Static-LLM Extraction Pipeline

Endpoints for:
- Running static analysis (Cycle 0)
- Retrieving business rules, NFRs, and compliance violations
- Managing conflicts between static and LLM analysis
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models.static_analysis import (
    StaticAnalysisResult,
    BusinessRule,
    NFRDetection,
    ComplianceViolation,
    VariableClassification,
    ProgramSlice,
    StaticAnalysisConflict,
)
from app.services.static_analysis import (
    StaticAnalysisOrchestrator,
    StaticAnalysisConfig,
    ComplianceFramework,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/static-analysis", tags=["Static Analysis"])


# Request/Response Models
class StaticAnalysisRequest(BaseModel):
    """Request to run static analysis."""
    project_id: int
    files: Dict[str, str] = Field(default_factory=dict, description="Map of file paths to source code")
    enable_slicing: bool = True
    enable_variable_classification: bool = True
    enable_business_rules: bool = True
    enable_nfr_detection: bool = True
    enable_compliance: bool = True
    compliance_frameworks: List[str] = Field(
        default_factory=list,
        description="List of compliance frameworks to check (NEN7510, ISO27001, HIPAA, SOC2, GDPR, PCI_DSS)"
    )
    custom_domain_terms: List[str] = Field(
        default_factory=list,
        description="Project-specific domain terms to add to classifier"
    )
    languages: List[str] = Field(
        default=["python"],
        description="Programming languages in the codebase"
    )


class StaticAnalysisResponse(BaseModel):
    """Response from static analysis."""
    id: str
    project_id: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    total_files_analyzed: int
    total_lines_of_code: int
    domain_coverage: float
    nfr_coverage: float
    compliance_score: float
    business_rules_count: int
    nfr_detections_count: int
    compliance_violations_count: int
    high_confidence_count: int
    low_confidence_count: int
    errors: List[Dict]


class BusinessRuleResponse(BaseModel):
    """Business rule response."""
    id: str
    rule_type: str
    condition: str
    action: str
    source_file: str
    source_lines: List[int]
    variables_involved: List[str]
    confidence: float
    natural_language: str
    compliance_tags: List[str]
    llm_validated: bool


class NFRDetectionResponse(BaseModel):
    """NFR detection response."""
    id: str
    category: str
    pattern_matched: str
    source_file: str
    source_line: int
    code_snippet: Optional[str]
    confidence: float
    description: str
    recommendation: Optional[str]
    compliance_relevance: List[str]


class ComplianceViolationResponse(BaseModel):
    """Compliance violation response."""
    id: int
    requirement_id: str
    framework: str
    title: str
    category: str
    violation_type: str
    severity: str
    file_path: Optional[str]
    line_number: Optional[int]
    remediation: str
    resolved: bool


class ConflictResolutionRequest(BaseModel):
    """Request to resolve a static-LLM conflict."""
    resolution: str = Field(description="accepted_static, accepted_llm, or human_review")
    resolved_by: str
    resolution_notes: Optional[str] = None


# Endpoints

@router.post("/analyze", response_model=StaticAnalysisResponse)
async def run_static_analysis(
    request: StaticAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Run static analysis (Cycle 0) on project files.

    This is the foundation of the Hybrid Static-LLM Extraction Pipeline.
    Provides deterministic analysis before LLM enrichment (Cycles 1-5).
    """
    try:
        # Configure analysis
        config = StaticAnalysisConfig(
            enable_slicing=request.enable_slicing,
            enable_variable_classification=request.enable_variable_classification,
            enable_business_rules=request.enable_business_rules,
            enable_nfr_detection=request.enable_nfr_detection,
            enable_compliance=request.enable_compliance,
            compliance_frameworks=request.compliance_frameworks,
            custom_domain_terms=request.custom_domain_terms,
            languages=request.languages,
        )

        # Run orchestrator
        orchestrator = StaticAnalysisOrchestrator(db)
        result = await orchestrator.run_analysis(
            project_id=request.project_id,
            files=request.files,
            config=config
        )

        # Persist results to database
        db_result = StaticAnalysisResult(
            id=result.id,
            project_id=result.project_id,
            started_at=result.started_at,
            completed_at=result.completed_at,
            status="completed",
            total_files_analyzed=result.total_files_analyzed,
            total_lines_of_code=result.total_lines_of_code,
            domain_coverage=result.domain_coverage,
            nfr_coverage=result.nfr_coverage,
            compliance_score=result.compliance_score,
            config=request.dict(),
            summary=result.to_summary(),
            errors=result.errors,
        )
        db.add(db_result)

        # Persist business rules
        if result.business_rules:
            for rule in result.business_rules.rules:
                db_rule = BusinessRule(
                    id=rule.id,
                    analysis_id=result.id,
                    rule_type=rule.rule_type.value,
                    condition=rule.condition,
                    action=rule.action,
                    source_file=rule.source_file,
                    source_line_start=rule.source_lines[0],
                    source_line_end=rule.source_lines[1],
                    variables_involved=rule.variables_involved,
                    confidence=rule.confidence,
                    natural_language=rule.natural_language,
                    compliance_tags=rule.compliance_tags,
                )
                db.add(db_rule)

        # Persist NFR detections
        if result.nfr_report:
            for detection in result.nfr_report.detections:
                db_nfr = NFRDetection(
                    id=detection.id,
                    analysis_id=result.id,
                    category=detection.category.value,
                    pattern_matched=detection.pattern_matched,
                    source_file=detection.source_file,
                    source_line=detection.source_line,
                    code_snippet=detection.code_snippet,
                    confidence=detection.confidence,
                    description=detection.description,
                    recommendation=detection.recommendation,
                    compliance_relevance=detection.compliance_relevance,
                )
                db.add(db_nfr)

        # Persist compliance violations
        if result.compliance_report:
            for violation in result.compliance_report.violations:
                db_violation = ComplianceViolation(
                    analysis_id=result.id,
                    requirement_id=violation.requirement.id,
                    framework=violation.requirement.framework.value,
                    title=violation.requirement.title,
                    category=violation.requirement.category,
                    violation_type=violation.violation_type,
                    severity=violation.requirement.severity,
                    file_path=violation.file_path,
                    line_number=violation.line_number,
                    code_snippet=violation.code_snippet,
                    remediation=violation.remediation,
                )
                db.add(db_violation)

        # Persist variable classifications
        if result.variable_classification:
            for var in result.variable_classification.variables:
                db_var = VariableClassification(
                    analysis_id=result.id,
                    name=var.name,
                    variable_type=var.variable_type.value,
                    confidence=var.confidence,
                    context=var.context,
                    reasoning=var.reasoning,
                )
                db.add(db_var)

        # Persist program slices
        for slice_result in result.slices:
            db_slice = ProgramSlice(
                analysis_id=result.id,
                file_path=slice_result.criterion.file_path,
                line_number=slice_result.criterion.line_number,
                variable_name=slice_result.criterion.variable_name,
                direction=slice_result.criterion.direction.value,
                statements=slice_result.statements,
                variables=list(slice_result.variables),
                functions_involved=list(slice_result.functions_involved),
                files_involved=list(slice_result.files_involved),
                slice_size=slice_result.slice_size,
                complexity_score=slice_result.complexity_score,
            )
            db.add(db_slice)

        db.commit()

        return StaticAnalysisResponse(
            id=result.id,
            project_id=result.project_id,
            status="completed",
            started_at=result.started_at,
            completed_at=result.completed_at,
            total_files_analyzed=result.total_files_analyzed,
            total_lines_of_code=result.total_lines_of_code,
            domain_coverage=result.domain_coverage,
            nfr_coverage=result.nfr_coverage,
            compliance_score=result.compliance_score,
            business_rules_count=len(result.business_rules.rules) if result.business_rules else 0,
            nfr_detections_count=len(result.nfr_report.detections) if result.nfr_report else 0,
            compliance_violations_count=len(result.compliance_report.violations) if result.compliance_report else 0,
            high_confidence_count=len(result.high_confidence_findings),
            low_confidence_count=len(result.low_confidence_findings),
            errors=result.errors,
        )

    except Exception as e:
        logger.error(f"Static analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{analysis_id}", response_model=StaticAnalysisResponse)
async def get_analysis_result(analysis_id: str, db: Session = Depends(get_db)):
    """Get static analysis result by ID."""
    result = db.query(StaticAnalysisResult).filter(
        StaticAnalysisResult.id == analysis_id
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    rules_count = db.query(BusinessRule).filter(BusinessRule.analysis_id == analysis_id).count()
    nfr_count = db.query(NFRDetection).filter(NFRDetection.analysis_id == analysis_id).count()
    violations_count = db.query(ComplianceViolation).filter(ComplianceViolation.analysis_id == analysis_id).count()

    return StaticAnalysisResponse(
        id=result.id,
        project_id=result.project_id,
        status=result.status,
        started_at=result.started_at,
        completed_at=result.completed_at,
        total_files_analyzed=result.total_files_analyzed,
        total_lines_of_code=result.total_lines_of_code,
        domain_coverage=result.domain_coverage,
        nfr_coverage=result.nfr_coverage,
        compliance_score=result.compliance_score,
        business_rules_count=rules_count,
        nfr_detections_count=nfr_count,
        compliance_violations_count=violations_count,
        high_confidence_count=result.summary.get("high_confidence_count", 0) if result.summary else 0,
        low_confidence_count=result.summary.get("low_confidence_count", 0) if result.summary else 0,
        errors=result.errors or [],
    )


@router.get("/results/{analysis_id}/business-rules", response_model=List[BusinessRuleResponse])
async def get_business_rules(
    analysis_id: str,
    rule_type: Optional[str] = None,
    min_confidence: float = 0.0,
    db: Session = Depends(get_db)
):
    """Get business rules from analysis."""
    query = db.query(BusinessRule).filter(BusinessRule.analysis_id == analysis_id)

    if rule_type:
        query = query.filter(BusinessRule.rule_type == rule_type)

    if min_confidence > 0:
        query = query.filter(BusinessRule.confidence >= min_confidence)

    rules = query.all()

    return [
        BusinessRuleResponse(
            id=r.id,
            rule_type=r.rule_type,
            condition=r.condition,
            action=r.action,
            source_file=r.source_file,
            source_lines=[r.source_line_start, r.source_line_end],
            variables_involved=r.variables_involved or [],
            confidence=r.confidence,
            natural_language=r.natural_language,
            compliance_tags=r.compliance_tags or [],
            llm_validated=r.llm_validated,
        )
        for r in rules
    ]


@router.get("/results/{analysis_id}/nfr-detections", response_model=List[NFRDetectionResponse])
async def get_nfr_detections(
    analysis_id: str,
    category: Optional[str] = None,
    min_confidence: float = 0.0,
    db: Session = Depends(get_db)
):
    """Get NFR detections from analysis."""
    query = db.query(NFRDetection).filter(NFRDetection.analysis_id == analysis_id)

    if category:
        query = query.filter(NFRDetection.category == category)

    if min_confidence > 0:
        query = query.filter(NFRDetection.confidence >= min_confidence)

    detections = query.all()

    return [
        NFRDetectionResponse(
            id=d.id,
            category=d.category,
            pattern_matched=d.pattern_matched,
            source_file=d.source_file,
            source_line=d.source_line,
            code_snippet=d.code_snippet,
            confidence=d.confidence,
            description=d.description,
            recommendation=d.recommendation,
            compliance_relevance=d.compliance_relevance or [],
        )
        for d in detections
    ]


@router.get("/results/{analysis_id}/compliance-violations", response_model=List[ComplianceViolationResponse])
async def get_compliance_violations(
    analysis_id: str,
    framework: Optional[str] = None,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get compliance violations from analysis."""
    query = db.query(ComplianceViolation).filter(ComplianceViolation.analysis_id == analysis_id)

    if framework:
        query = query.filter(ComplianceViolation.framework == framework)

    if severity:
        query = query.filter(ComplianceViolation.severity == severity)

    if resolved is not None:
        query = query.filter(ComplianceViolation.resolved == resolved)

    violations = query.all()

    return [
        ComplianceViolationResponse(
            id=v.id,
            requirement_id=v.requirement_id,
            framework=v.framework,
            title=v.title,
            category=v.category,
            violation_type=v.violation_type,
            severity=v.severity,
            file_path=v.file_path,
            line_number=v.line_number,
            remediation=v.remediation,
            resolved=v.resolved,
        )
        for v in violations
    ]


@router.patch("/compliance-violations/{violation_id}/resolve")
async def resolve_compliance_violation(
    violation_id: int,
    resolved_by: str,
    db: Session = Depends(get_db)
):
    """Mark a compliance violation as resolved."""
    violation = db.query(ComplianceViolation).filter(
        ComplianceViolation.id == violation_id
    ).first()

    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")

    violation.resolved = True
    violation.resolved_at = datetime.utcnow()
    violation.resolved_by = resolved_by

    db.commit()

    return {"status": "resolved", "violation_id": violation_id}


@router.get("/results/{analysis_id}/conflicts")
async def get_conflicts(
    analysis_id: str,
    conflict_type: Optional[str] = None,
    unresolved_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get static-LLM conflicts for an analysis."""
    query = db.query(StaticAnalysisConflict).filter(StaticAnalysisConflict.analysis_id == analysis_id)

    if conflict_type:
        query = query.filter(StaticAnalysisConflict.conflict_type == conflict_type)

    if unresolved_only:
        query = query.filter(StaticAnalysisConflict.resolution.is_(None))

    conflicts = query.all()

    return [c.to_dict() for c in conflicts]


@router.post("/results/{analysis_id}/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    analysis_id: str,
    conflict_id: int,
    request: ConflictResolutionRequest,
    db: Session = Depends(get_db)
):
    """Resolve a static-LLM conflict."""
    conflict = db.query(StaticAnalysisConflict).filter(
        StaticAnalysisConflict.id == conflict_id,
        StaticAnalysisConflict.analysis_id == analysis_id
    ).first()

    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    conflict.resolution = request.resolution
    conflict.resolved_by = request.resolved_by
    conflict.resolved_at = datetime.utcnow()
    conflict.resolution_notes = request.resolution_notes

    db.commit()

    return {"status": "resolved", "conflict_id": conflict_id, "resolution": request.resolution}


@router.get("/results/{analysis_id}/llm-context")
async def get_llm_context(analysis_id: str, db: Session = Depends(get_db)):
    """
    Get static analysis results in LLM-consumable format.

    This endpoint provides the context needed for Cycles 1-5 LLM enrichment.
    """
    result = db.query(StaticAnalysisResult).filter(
        StaticAnalysisResult.id == analysis_id
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Build context
    business_rules = db.query(BusinessRule).filter(BusinessRule.analysis_id == analysis_id).all()
    nfr_detections = db.query(NFRDetection).filter(NFRDetection.analysis_id == analysis_id).all()
    violations = db.query(ComplianceViolation).filter(ComplianceViolation.analysis_id == analysis_id).all()
    variables = db.query(VariableClassification).filter(
        VariableClassification.analysis_id == analysis_id,
        VariableClassification.variable_type == "domain"
    ).all()

    return {
        "static_analysis_summary": {
            "id": result.id,
            "files_analyzed": result.total_files_analyzed,
            "lines_of_code": result.total_lines_of_code,
            "domain_coverage": result.domain_coverage,
            "nfr_coverage": result.nfr_coverage,
            "compliance_score": result.compliance_score,
        },
        "business_rules": [
            {
                "id": r.id,
                "type": r.rule_type,
                "condition": r.condition,
                "action": r.action,
                "natural_language": r.natural_language,
                "confidence": r.confidence,
                "source_file": r.source_file,
            }
            for r in business_rules
        ],
        "nfr_detections": [
            {
                "id": d.id,
                "category": d.category,
                "description": d.description,
                "confidence": d.confidence,
                "source_file": d.source_file,
                "compliance_relevance": d.compliance_relevance or [],
            }
            for d in nfr_detections
        ],
        "compliance_violations": [
            {
                "requirement_id": v.requirement_id,
                "framework": v.framework,
                "title": v.title,
                "violation_type": v.violation_type,
                "severity": v.severity,
                "remediation": v.remediation,
            }
            for v in violations
        ],
        "domain_variables": [v.name for v in variables],
    }


@router.get("/frameworks")
async def list_compliance_frameworks():
    """List available compliance frameworks."""
    return [
        {
            "id": "NEN7510",
            "name": "NEN7510 (Dutch Healthcare)",
            "description": "Dutch standard for information security in healthcare",
            "region": "Netherlands",
        },
        {
            "id": "ISO27001",
            "name": "ISO 27001",
            "description": "International standard for information security management",
            "region": "International",
        },
        {
            "id": "HIPAA",
            "name": "HIPAA (US Healthcare)",
            "description": "Health Insurance Portability and Accountability Act",
            "region": "United States",
        },
        {
            "id": "SOC2",
            "name": "SOC 2",
            "description": "Service Organization Control 2 - Trust Services Criteria",
            "region": "International",
        },
        {
            "id": "GDPR",
            "name": "GDPR (EU Privacy)",
            "description": "General Data Protection Regulation",
            "region": "European Union",
        },
        {
            "id": "PCI_DSS",
            "name": "PCI-DSS (Payment Card)",
            "description": "Payment Card Industry Data Security Standard",
            "region": "International",
        },
    ]


@router.get("/project/{project_id}/history")
async def get_analysis_history(
    project_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get static analysis history for a project."""
    results = db.query(StaticAnalysisResult).filter(
        StaticAnalysisResult.project_id == project_id
    ).order_by(
        StaticAnalysisResult.started_at.desc()
    ).limit(limit).all()

    return [r.to_dict() for r in results]


@router.get("/stats/global")
async def get_global_stats(db: Session = Depends(get_db)):
    """Get global statistics for static analysis."""
    total_analyses = db.query(StaticAnalysisResult).count()
    total_rules = db.query(BusinessRule).count()
    total_nfrs = db.query(NFRDetection).count()
    total_violations = db.query(ComplianceViolation).count()
    unresolved_violations = db.query(ComplianceViolation).filter(
        ComplianceViolation.resolved == False
    ).count()

    return {
        "total_analyses": total_analyses,
        "total_business_rules": total_rules,
        "total_nfr_detections": total_nfrs,
        "total_compliance_violations": total_violations,
        "unresolved_violations": unresolved_violations,
    }


# =============================================================================
# Fase 25: Business Logic Extraction Endpoints
# =============================================================================

@router.get("/results/{analysis_id}/decision-tables")
async def get_decision_tables(
    analysis_id: str,
    format: str = "json",
    db: Session = Depends(get_db)
):
    """
    Generate decision tables from BRANCHING rules.

    Fase 25: Extracts decision tables from conditional business rules
    and exports in DMN (Decision Model and Notation) XML format.

    Args:
        analysis_id: Static analysis ID
        format: Output format - "json" (default), "dmn", or "markdown"

    Returns:
        Decision tables in requested format
    """
    from app.services.static_analysis.rule_correlation_service import RuleCorrelationService
    from app.services.static_analysis.extraction_models import (
        ExtractedBusinessRule as ServiceBusinessRule,
        RuleType
    )

    # Get business rules from database
    db_rules = db.query(BusinessRule).filter(
        BusinessRule.analysis_id == analysis_id,
        BusinessRule.rule_type == "BRANCHING"
    ).all()

    if not db_rules:
        return {
            "analysis_id": analysis_id,
            "decision_tables": [],
            "count": 0,
            "message": "No BRANCHING rules found for decision table generation"
        }

    # Convert to service model
    rules = []
    for r in db_rules:
        rule = ServiceBusinessRule(
            id=r.id,
            rule_type=RuleType.BRANCHING,
            condition=r.condition,
            action=r.action,
            source_file=r.source_file,
            source_lines=(r.source_line_start, r.source_line_end),
            variables_involved=r.variables_involved or [],
            confidence=r.confidence,
            natural_language=r.natural_language,
            compliance_tags=r.compliance_tags or []
        )
        rules.append(rule)

    # Generate decision tables
    service = RuleCorrelationService()
    tables = service.generate_decision_tables(rules)

    if format == "dmn":
        # Return DMN XML format
        dmn_outputs = []
        for table in tables:
            dmn_outputs.append({
                "id": table["id"],
                "name": table["name"],
                "dmn_xml": table.get("dmn_xml", ""),
            })
        return {
            "analysis_id": analysis_id,
            "format": "dmn",
            "decision_tables": dmn_outputs,
            "count": len(tables)
        }
    elif format == "markdown":
        # Return markdown format
        md_outputs = []
        for table in tables:
            md_outputs.append({
                "id": table["id"],
                "name": table["name"],
                "markdown": table.get("markdown", ""),
            })
        return {
            "analysis_id": analysis_id,
            "format": "markdown",
            "decision_tables": md_outputs,
            "count": len(tables)
        }
    else:
        # Return JSON format (default)
        return {
            "analysis_id": analysis_id,
            "format": "json",
            "decision_tables": tables,
            "count": len(tables)
        }


@router.get("/results/{analysis_id}/authorization-matrix")
async def get_authorization_matrix(
    analysis_id: str,
    format: str = "json",
    db: Session = Depends(get_db)
):
    """
    Generate RBAC authorization matrix from AUTHORIZATION rules.

    Fase 25: Extracts role-based access control patterns from
    authorization business rules.

    Args:
        analysis_id: Static analysis ID
        format: Output format - "json" (default) or "markdown"

    Returns:
        Authorization matrix with roles, permissions, and resources
    """
    from app.services.static_analysis.rule_correlation_service import RuleCorrelationService
    from app.services.static_analysis.extraction_models import (
        ExtractedBusinessRule as ServiceBusinessRule,
        RuleType
    )

    # Get authorization rules from database
    db_rules = db.query(BusinessRule).filter(
        BusinessRule.analysis_id == analysis_id,
        BusinessRule.rule_type == "AUTHORIZATION"
    ).all()

    if not db_rules:
        return {
            "analysis_id": analysis_id,
            "matrix": {},
            "roles": [],
            "permissions": [],
            "resources": [],
            "message": "No AUTHORIZATION rules found for matrix generation"
        }

    # Convert to service model
    rules = []
    for r in db_rules:
        rule = ServiceBusinessRule(
            id=r.id,
            rule_type=RuleType.AUTHORIZATION,
            condition=r.condition,
            action=r.action,
            source_file=r.source_file,
            source_lines=(r.source_line_start, r.source_line_end),
            variables_involved=r.variables_involved or [],
            confidence=r.confidence,
            natural_language=r.natural_language,
            compliance_tags=r.compliance_tags or []
        )
        rules.append(rule)

    # Generate authorization matrix
    service = RuleCorrelationService()
    matrix = service.generate_authorization_matrix(rules)

    if format == "markdown":
        return {
            "analysis_id": analysis_id,
            "format": "markdown",
            "markdown": matrix.get("markdown", ""),
            "roles_count": len(matrix.get("roles", [])),
            "permissions_count": len(matrix.get("permissions", [])),
            "resources_count": len(matrix.get("resources", []))
        }
    else:
        return {
            "analysis_id": analysis_id,
            "format": "json",
            **matrix
        }


@router.get("/results/{analysis_id}/state-machines")
async def get_state_machines(
    analysis_id: str,
    format: str = "json",
    db: Session = Depends(get_db)
):
    """
    Get detected state machine patterns from analysis.

    Fase 25: Returns state machines in XState or Mermaid format.

    Args:
        analysis_id: Static analysis ID
        format: Output format - "json", "xstate", or "mermaid"

    Returns:
        State machines in requested format
    """
    from app.services.static_analysis.rule_correlation_service import RuleCorrelationService
    from app.services.static_analysis.extraction_models import (
        ExtractedBusinessRule as ServiceBusinessRule,
        RuleType
    )

    # Get all rules to detect state machine patterns
    db_rules = db.query(BusinessRule).filter(
        BusinessRule.analysis_id == analysis_id
    ).all()

    if not db_rules:
        return {
            "analysis_id": analysis_id,
            "state_machines": [],
            "count": 0,
            "message": "No business rules found for state machine detection"
        }

    # Convert to service model
    rules = []
    for r in db_rules:
        try:
            rule_type = RuleType[r.rule_type]
        except KeyError:
            rule_type = RuleType.OTHER

        rule = ServiceBusinessRule(
            id=r.id,
            rule_type=rule_type,
            condition=r.condition,
            action=r.action,
            source_file=r.source_file,
            source_lines=(r.source_line_start, r.source_line_end),
            variables_involved=r.variables_involved or [],
            confidence=r.confidence,
            natural_language=r.natural_language,
            compliance_tags=r.compliance_tags or []
        )
        rules.append(rule)

    # Detect state machine workflows
    service = RuleCorrelationService()
    workflows = service._detect_state_machine_workflows(rules)

    state_machines = []
    for workflow in workflows:
        sm_data = {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "states": workflow.states,
            "trigger_rules": [r.id for r in workflow.trigger_rules],
            "confidence": workflow.confidence
        }

        if format == "xstate":
            # Generate XState format
            from app.services.orchestration.statemachine_tool_service import StateMachine, Transition

            # Build StateMachine from workflow
            transitions = []
            for rule in workflow.trigger_rules:
                # Parse state transitions from rule conditions/actions
                if "→" in rule.condition or "->" in rule.condition:
                    parts = rule.condition.replace("→", "->").split("->")
                    if len(parts) == 2:
                        transitions.append(Transition(
                            from_state=parts[0].strip(),
                            to_state=parts[1].strip(),
                            trigger=rule.action or "trigger"
                        ))

            if transitions:
                sm = StateMachine(
                    name=workflow.name,
                    states=workflow.states,
                    initial_state=workflow.states[0] if workflow.states else "initial",
                    transitions=transitions,
                    context={}
                )
                sm_data["xstate"] = sm.to_xstate()

        elif format == "mermaid":
            # Generate Mermaid diagram
            mermaid_lines = ["stateDiagram-v2"]
            for i, state in enumerate(workflow.states):
                if i < len(workflow.states) - 1:
                    mermaid_lines.append(f"    {state} --> {workflow.states[i+1]}")
            sm_data["mermaid"] = "\n".join(mermaid_lines)

        state_machines.append(sm_data)

    return {
        "analysis_id": analysis_id,
        "format": format,
        "state_machines": state_machines,
        "count": len(state_machines)
    }


@router.get("/results/{analysis_id}/business-logic-summary")
async def get_business_logic_summary(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive business logic extraction summary.

    Fase 25: Combines decision tables, authorization matrix,
    and state machines into a unified summary.

    Returns:
        Comprehensive business logic summary with counts and references
    """
    # Count rules by type
    branching_count = db.query(BusinessRule).filter(
        BusinessRule.analysis_id == analysis_id,
        BusinessRule.rule_type == "BRANCHING"
    ).count()

    auth_count = db.query(BusinessRule).filter(
        BusinessRule.analysis_id == analysis_id,
        BusinessRule.rule_type == "AUTHORIZATION"
    ).count()

    validation_count = db.query(BusinessRule).filter(
        BusinessRule.analysis_id == analysis_id,
        BusinessRule.rule_type == "VALIDATION"
    ).count()

    calculation_count = db.query(BusinessRule).filter(
        BusinessRule.analysis_id == analysis_id,
        BusinessRule.rule_type == "CALCULATION"
    ).count()

    total_count = db.query(BusinessRule).filter(
        BusinessRule.analysis_id == analysis_id
    ).count()

    # Get high-confidence rules
    high_confidence = db.query(BusinessRule).filter(
        BusinessRule.analysis_id == analysis_id,
        BusinessRule.confidence >= 0.8
    ).count()

    return {
        "analysis_id": analysis_id,
        "summary": {
            "total_rules": total_count,
            "high_confidence_rules": high_confidence,
            "by_type": {
                "branching": branching_count,
                "authorization": auth_count,
                "validation": validation_count,
                "calculation": calculation_count
            }
        },
        "fase_25_capabilities": {
            "decision_tables": {
                "available": branching_count > 0,
                "source_rules": branching_count,
                "endpoint": f"/api/static-analysis/results/{analysis_id}/decision-tables"
            },
            "authorization_matrix": {
                "available": auth_count > 0,
                "source_rules": auth_count,
                "endpoint": f"/api/static-analysis/results/{analysis_id}/authorization-matrix"
            },
            "state_machines": {
                "available": total_count > 0,
                "endpoint": f"/api/static-analysis/results/{analysis_id}/state-machines"
            }
        },
        "export_formats": {
            "decision_tables": ["json", "dmn", "markdown"],
            "authorization_matrix": ["json", "markdown"],
            "state_machines": ["json", "xstate", "mermaid"]
        }
    }
