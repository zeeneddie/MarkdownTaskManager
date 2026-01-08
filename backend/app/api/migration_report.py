"""
Migration Report API - Diana Integration Endpoints

Week 68 Day 4-5: REST API for markdown report generation
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.services.migration_report_service import (
    MigrationReportService,
    ReportType,
    ReportFormat
)


router = APIRouter(prefix="/api/migration-report", tags=["Migration Report"])

# Initialize service
report_service = MigrationReportService()


# ==================== Request/Response Models ====================

class GenerateReportRequest(BaseModel):
    """Request to generate a migration report"""
    report_type: str = Field(..., description="Type of report to generate")
    project_name: str = Field(..., description="Name of the project")
    directory: str = Field(..., description="Directory being analyzed")
    security_data: Optional[Dict[str, Any]] = Field(None, description="Quinn security analysis data")
    estimation_data: Optional[Dict[str, Any]] = Field(None, description="Eliza estimation data")
    architecture_data: Optional[Dict[str, Any]] = Field(None, description="Felix architecture data")
    output_format: str = Field("markdown", description="Output format: markdown, html, json")


class CombinedAnalysisRequest(BaseModel):
    """Request to run all analyses and generate report"""
    project_name: str = Field(..., description="Name of the project")
    directory: str = Field(..., description="Directory to analyze")
    report_type: str = Field("full_migration_plan", description="Type of report")
    target_technology: str = Field("python_fastapi", description="Target technology stack")


# ==================== API Endpoints ====================

@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get report service status and capabilities"""
    return report_service.get_status()


@router.get("/types")
async def list_report_types() -> Dict[str, Any]:
    """
    List all available report types

    Returns:
        Report types with sections and target audience
    """
    types = report_service.get_report_types()

    return {
        "total_types": len(types),
        "report_types": types
    }


@router.get("/types/{type_id}")
async def get_report_type_detail(type_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a report type

    Returns:
        Report type details with sections and purpose
    """
    try:
        report_type = ReportType(type_id.lower())
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Report type not found. Valid: {[t.value for t in ReportType]}"
        )

    # Get template info
    types = report_service.get_report_types()
    for t in types:
        if t["id"] == type_id:
            return {
                "report_type": t,
                "description": _get_report_description(report_type),
                "use_cases": _get_report_use_cases(report_type)
            }

    raise HTTPException(status_code=404, detail="Report type details not found")


@router.get("/sections")
async def list_sections() -> Dict[str, Any]:
    """
    List all available report sections

    Returns:
        Section types with descriptions
    """
    sections = report_service.get_sections()

    return {
        "total_sections": len(sections),
        "sections": [
            {
                **s,
                "description": _get_section_description(s["id"])
            }
            for s in sections
        ]
    }


@router.post("/generate")
async def generate_report(request: GenerateReportRequest) -> Dict[str, Any]:
    """
    Generate a migration report

    Combines data from Quinn (security), Eliza (estimation), and Felix (architecture)
    into a comprehensive migration report.

    Returns:
        Report metadata and content summary
    """
    # Validate report type
    try:
        report_type = ReportType(request.report_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report type. Valid: {[t.value for t in ReportType]}"
        )

    # Validate output format
    try:
        output_format = ReportFormat(request.output_format.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Valid: {[f.value for f in ReportFormat]}"
        )

    report = report_service.generate_report(
        report_type=report_type,
        project_name=request.project_name,
        directory=request.directory,
        security_data=request.security_data,
        estimation_data=request.estimation_data,
        architecture_data=request.architecture_data,
        output_format=output_format
    )

    return report.to_dict()


@router.post("/generate/markdown", response_class=PlainTextResponse)
async def generate_markdown_report(request: GenerateReportRequest) -> str:
    """
    Generate a migration report in markdown format

    Returns:
        Complete markdown document
    """
    try:
        report_type = ReportType(request.report_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report type. Valid: {[t.value for t in ReportType]}"
        )

    report = report_service.generate_report(
        report_type=report_type,
        project_name=request.project_name,
        directory=request.directory,
        security_data=request.security_data,
        estimation_data=request.estimation_data,
        architecture_data=request.architecture_data,
        output_format=ReportFormat.MARKDOWN
    )

    return report.to_markdown()


@router.post("/generate/combined")
async def generate_combined_report(request: CombinedAnalysisRequest) -> Dict[str, Any]:
    """
    Run all analyses and generate combined report

    Orchestrates Quinn, Eliza, and Felix to perform complete analysis,
    then generates a comprehensive report.

    Returns:
        Complete report with all analysis data
    """
    # Import services
    from app.services.migration_security_service import MigrationSecurityService, SecuritySeverity
    from app.services.migration_estimation_service import MigrationEstimationService, TechnologyStack
    from app.services.migration_architecture_service import MigrationArchitectureService, TechnologyChoice

    try:
        report_type = ReportType(request.report_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report type. Valid: {[t.value for t in ReportType]}"
        )

    # Run Quinn security analysis
    security_service = MigrationSecurityService()
    security_result = security_service.analyze_directory(
        directory=request.directory,
        severity_threshold=SecuritySeverity.LOW
    )
    security_data = security_result.to_dict()

    # Run Eliza estimation
    estimation_service = MigrationEstimationService()
    try:
        target_stack = TechnologyStack(request.target_technology.lower())
    except ValueError:
        target_stack = TechnologyStack.PYTHON_FASTAPI

    estimation_result = estimation_service.estimate_directory(
        directory=request.directory,
        source_stack=TechnologyStack.CLASSIC_ASP,  # Auto-detect in real implementation
        target_stack=target_stack,
        team_size=5
    )
    estimation_data = estimation_result.to_dict()

    # Run Felix architecture analysis
    architecture_service = MigrationArchitectureService()
    try:
        target_tech = TechnologyChoice(request.target_technology.lower())
    except ValueError:
        target_tech = TechnologyChoice.PYTHON_FASTAPI

    architecture_result = architecture_service.analyze_directory(
        directory=request.directory,
        target_technology=target_tech
    )
    architecture_data = architecture_result.to_dict()

    # Generate combined report
    report = report_service.generate_report(
        report_type=report_type,
        project_name=request.project_name,
        directory=request.directory,
        security_data=security_data,
        estimation_data=estimation_data,
        architecture_data=architecture_data,
        output_format=ReportFormat.MARKDOWN
    )

    return {
        "report": report.to_dict(),
        "markdown_preview": report.to_markdown()[:5000] + "..." if len(report.to_markdown()) > 5000 else report.to_markdown(),
        "analysis_summary": {
            "security_findings": security_data.get("total_findings", 0),
            "function_points": estimation_data.get("adjusted_fp", 0),
            "total_hours": estimation_data.get("total_hours", 0),
            "architecture_pattern": architecture_data.get("architecture", {}).get("pattern", "N/A")
        }
    }


@router.get("/diana-context/{report_id}")
async def get_diana_context(
    report_id: str,
    project_name: str = Query(..., description="Project name"),
    directory: str = Query(..., description="Directory analyzed"),
    report_type: str = Query("full_migration_plan", description="Report type")
) -> Dict[str, Any]:
    """
    Generate Diana agent context for report review

    Returns:
        Context for Diana to review and improve the report
    """
    try:
        rtype = ReportType(report_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report type. Valid: {[t.value for t in ReportType]}"
        )

    # Generate a sample report to get Diana context
    report = report_service.generate_report(
        report_type=rtype,
        project_name=project_name,
        directory=directory
    )

    return {
        "report_id": report_id,
        "diana_context": {
            "summary": report.diana_context.summary,
            "key_findings": report.diana_context.key_findings,
            "document_structure": report.diana_context.document_structure,
            "style_guidelines": report.diana_context.style_guidelines,
            "target_audience": report.diana_context.target_audience,
            "questions_for_review": report.diana_context.questions_for_review
        },
        "improvement_suggestions": [
            "Add executive summary highlights",
            "Include visual diagrams for architecture",
            "Enhance risk mitigation details",
            "Add timeline visualization",
            "Include cost breakdown chart"
        ]
    }


@router.get("/templates")
async def list_templates() -> Dict[str, Any]:
    """
    List report templates and their configurations

    Returns:
        Template configurations for each report type
    """
    from app.services.migration_report_service import REPORT_TEMPLATES

    templates = []
    for report_type, config in REPORT_TEMPLATES.items():
        templates.append({
            "report_type": report_type.value,
            "sections": [s.value for s in config["sections"]],
            "max_pages": config["max_pages"],
            "audience": config["audience"]
        })

    return {
        "total_templates": len(templates),
        "templates": templates
    }


@router.post("/preview")
async def preview_report(
    report_type: str = Query(..., description="Report type"),
    project_name: str = Query("Sample Project", description="Project name")
) -> Dict[str, Any]:
    """
    Generate a preview report with sample data

    Returns:
        Preview report for template evaluation
    """
    try:
        rtype = ReportType(report_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report type. Valid: {[t.value for t in ReportType]}"
        )

    # Sample data for preview
    sample_security = {
        "total_findings": 15,
        "risk_score": {
            "total": 45,
            "grade": "C",
            "critical_issues": 2,
            "high_issues": 5,
            "medium_issues": 8,
            "low_issues": 0,
            "owasp_coverage": {"A01:2021 - Broken Access Control": 3},
            "top_risks": ["SQL Injection in user input", "Missing authentication"],
            "migration_blockers": ["Critical SQL injection vulnerability"]
        },
        "stacks_detected": ["classic_asp", "vbnet_webforms"]
    }

    sample_estimation = {
        "unadjusted_fp": 450,
        "adjusted_fp": 520,
        "vaf": 1.15,
        "total_hours": 2600,
        "total_days": 325,
        "team_size": 5,
        "duration_weeks": 26,
        "components": [
            {"type": "EI", "count": 45, "function_points": 180},
            {"type": "EO", "count": 30, "function_points": 150},
            {"type": "ILF", "count": 25, "function_points": 175}
        ],
        "phases": [
            {"phase": "discovery", "hours": 260, "days": 32.5, "percentage": 10},
            {"phase": "development", "hours": 1040, "days": 130, "percentage": 40}
        ]
    }

    sample_architecture = {
        "architecture": {
            "pattern": "clean_architecture",
            "migration_strategy": "strangler_fig",
            "design_principles": ["solid", "separation_of_concerns"]
        },
        "target_components": [
            {"name": "api_gateway", "layer": "api_gateway", "technology": "python_fastapi", "effort_hours": 40}
        ],
        "architecture_decisions": [
            {"id": "ADR-001", "title": "Architecture Pattern", "decision": "Clean Architecture", "status": "proposed"}
        ],
        "risks": ["Data integrity during migration", "Performance regression"],
        "recommendations": ["Start with low-risk modules", "Implement feature flags"]
    }

    report = report_service.generate_report(
        report_type=rtype,
        project_name=project_name,
        directory="/sample/directory",
        security_data=sample_security,
        estimation_data=sample_estimation,
        architecture_data=sample_architecture
    )

    return {
        "preview": True,
        "report": report.to_dict(),
        "markdown_length": len(report.to_markdown()),
        "markdown_preview": report.to_markdown()[:3000]
    }


# ==================== Helper Functions ====================

def _get_report_description(report_type: ReportType) -> str:
    """Get description for report type"""
    descriptions = {
        ReportType.EXECUTIVE_SUMMARY: "High-level overview for executives and stakeholders, focusing on business impact and key decisions.",
        ReportType.TECHNICAL_ASSESSMENT: "Detailed technical analysis for architects and senior developers, covering system analysis and design.",
        ReportType.SECURITY_AUDIT: "Security-focused report for security teams and compliance officers, highlighting vulnerabilities and remediation.",
        ReportType.ESTIMATION_REPORT: "Effort and cost estimation for project managers and budget owners, with detailed breakdown by phase.",
        ReportType.ARCHITECTURE_RECOMMENDATION: "Architecture design document for development teams, including ADRs and component specifications.",
        ReportType.FULL_MIGRATION_PLAN: "Comprehensive migration plan combining all analyses for full project planning and execution.",
        ReportType.PROGRESS_REPORT: "Status update for ongoing migrations, tracking progress against plan."
    }
    return descriptions.get(report_type, "Migration analysis report")


def _get_report_use_cases(report_type: ReportType) -> List[str]:
    """Get use cases for report type"""
    use_cases = {
        ReportType.EXECUTIVE_SUMMARY: [
            "Board presentations",
            "Budget approval requests",
            "Stakeholder communication",
            "Project kick-off meetings"
        ],
        ReportType.TECHNICAL_ASSESSMENT: [
            "Technical planning sessions",
            "Architecture review meetings",
            "Team onboarding",
            "Technical decision making"
        ],
        ReportType.SECURITY_AUDIT: [
            "Security compliance reviews",
            "Risk assessment meetings",
            "Audit preparation",
            "Security remediation planning"
        ],
        ReportType.ESTIMATION_REPORT: [
            "Budget planning",
            "Resource allocation",
            "Timeline negotiation",
            "Vendor evaluation"
        ],
        ReportType.ARCHITECTURE_RECOMMENDATION: [
            "Design reviews",
            "Technical specifications",
            "Development guidelines",
            "Architecture documentation"
        ],
        ReportType.FULL_MIGRATION_PLAN: [
            "Complete project planning",
            "Contract documentation",
            "Comprehensive stakeholder communication",
            "Project baseline establishment"
        ]
    }
    return use_cases.get(report_type, ["General migration documentation"])


def _get_section_description(section_id: str) -> str:
    """Get description for report section"""
    descriptions = {
        "executive_summary": "High-level overview with key metrics and recommendations",
        "system_overview": "Current system analysis including components and dependencies",
        "technology_analysis": "Technology stack assessment and debt analysis",
        "security_findings": "Security vulnerabilities and OWASP Top 10 coverage",
        "effort_estimation": "Function point analysis and effort breakdown",
        "architecture_design": "Target architecture with ADRs and component mapping",
        "migration_roadmap": "Phase-by-phase migration timeline and milestones",
        "risk_assessment": "Risk matrix with impact, likelihood, and mitigations",
        "recommendations": "Actionable recommendations and success criteria",
        "appendices": "Glossary, references, and supplementary information"
    }
    return descriptions.get(section_id, "Report section content")
