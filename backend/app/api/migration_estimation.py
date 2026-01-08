"""
Migration Estimation API - Eliza FP Integration Endpoints

Week 68 Day 2-3: REST API for IFPUG-based migration effort estimation
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

from app.services.migration_estimation_service import (
    MigrationEstimationService,
    TechnologyStack,
    ComplexityLevel,
    MigrationPhase
)


router = APIRouter(prefix="/api/migration-estimation", tags=["Migration Estimation"])

# Initialize service
estimation_service = MigrationEstimationService()


# ==================== Request/Response Models ====================

class EstimateRequest(BaseModel):
    """Request to estimate migration effort for a directory"""
    directory: str = Field(..., description="Path to source code directory")
    source_stack: str = Field(..., description="Source technology stack")
    target_stack: str = Field("python_fastapi", description="Target technology stack")
    team_size: int = Field(5, ge=1, le=50, description="Development team size")
    experience_level: str = Field("intermediate", description="Team experience: junior, intermediate, senior")


class QuickEstimateRequest(BaseModel):
    """Request for quick estimation without scanning"""
    source_stack: str = Field(..., description="Source technology stack")
    target_stack: str = Field("python_fastapi", description="Target technology stack")
    estimated_screens: int = Field(50, ge=1, description="Number of UI screens")
    estimated_tables: int = Field(30, ge=1, description="Number of database tables")
    estimated_integrations: int = Field(5, ge=0, description="External integrations")
    estimated_reports: int = Field(10, ge=0, description="Report count")
    team_size: int = Field(5, ge=1, le=50, description="Team size")


class PhaseBreakdownRequest(BaseModel):
    """Request for phase-by-phase breakdown"""
    total_function_points: float = Field(..., gt=0, description="Total FP count")
    source_stack: str = Field(..., description="Source technology stack")
    target_stack: str = Field("python_fastapi", description="Target stack")
    team_size: int = Field(5, ge=1, description="Team size")


# ==================== API Endpoints ====================

@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get estimation service status and supported stacks"""
    return estimation_service.get_status()


@router.post("/estimate")
async def estimate_migration(request: EstimateRequest) -> Dict[str, Any]:
    """
    Estimate migration effort based on source code analysis

    Uses IFPUG Function Point methodology (CPM 4.3.1) to calculate:
    - Total function points (unadjusted and adjusted)
    - Phase-by-phase effort breakdown
    - Risk assessment and recommendations

    Returns:
        Complete migration estimation with effort, cost, and timeline
    """
    # Validate source stack
    try:
        source = TechnologyStack(request.source_stack.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source stack. Valid stacks: {[s.value for s in TechnologyStack]}"
        )

    # Validate target stack
    try:
        target = TechnologyStack(request.target_stack.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target stack. Valid stacks: {[s.value for s in TechnologyStack]}"
        )

    # Map experience level
    experience_map = {
        "junior": 0.7,
        "intermediate": 1.0,
        "senior": 1.3
    }
    productivity = experience_map.get(request.experience_level.lower(), 1.0)

    result = estimation_service.estimate_directory(
        directory=request.directory,
        source_stack=source,
        target_stack=target,
        team_size=request.team_size,
        productivity_factor=productivity
    )

    return result.to_dict()


@router.post("/quick-estimate")
async def quick_estimate(request: QuickEstimateRequest) -> Dict[str, Any]:
    """
    Quick estimation based on high-level metrics (no code scanning)

    Uses industry averages for function point estimation when
    source code access is not available.

    Returns:
        Rough order of magnitude (ROM) estimate
    """
    # Validate stacks
    try:
        source = TechnologyStack(request.source_stack.lower())
        target = TechnologyStack(request.target_stack.lower())
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stack. Valid stacks: {[s.value for s in TechnologyStack]}"
        )

    result = estimation_service.quick_estimate(
        source_stack=source,
        target_stack=target,
        screen_count=request.estimated_screens,
        table_count=request.estimated_tables,
        integration_count=request.estimated_integrations,
        report_count=request.estimated_reports,
        team_size=request.team_size
    )

    return result.to_dict()


@router.post("/phase-breakdown")
async def get_phase_breakdown(request: PhaseBreakdownRequest) -> Dict[str, Any]:
    """
    Get detailed phase-by-phase effort breakdown

    Returns:
        10-phase migration effort distribution with hours and percentages
    """
    try:
        source = TechnologyStack(request.source_stack.lower())
        target = TechnologyStack(request.target_stack.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stack. Valid stacks: {[s.value for s in TechnologyStack]}"
        )

    phases = estimation_service.calculate_phase_breakdown(
        total_fp=request.total_function_points,
        source_stack=source,
        target_stack=target,
        team_size=request.team_size
    )

    total_hours = sum(p.hours for p in phases)

    return {
        "total_function_points": request.total_function_points,
        "total_hours": total_hours,
        "total_days": total_hours / 8,
        "total_weeks": total_hours / 40,
        "team_size": request.team_size,
        "phases": [
            {
                "phase": p.phase.value,
                "name": p.phase.name.replace("_", " ").title(),
                "hours": p.hours,
                "days": p.days,
                "percentage": p.percentage,
                "deliverables": p.deliverables,
                "risks": p.risks
            }
            for p in phases
        ]
    }


@router.get("/stacks")
async def list_stacks() -> Dict[str, Any]:
    """
    List all supported technology stacks with complexity multipliers

    Returns:
        Technology stacks with migration complexity indicators
    """
    from app.services.migration_estimation_service import STACK_COMPLEXITY_MULTIPLIERS

    stacks = []
    for stack in TechnologyStack:
        multiplier = STACK_COMPLEXITY_MULTIPLIERS.get(stack, 1.0)
        complexity = "Low" if multiplier < 1.5 else "Medium" if multiplier < 2.0 else "High"

        stacks.append({
            "id": stack.value,
            "name": stack.name.replace("_", " ").title(),
            "complexity_multiplier": multiplier,
            "complexity_rating": complexity,
            "description": _get_stack_description(stack)
        })

    return {
        "total_stacks": len(stacks),
        "stacks": stacks
    }


@router.get("/phases")
async def list_phases() -> Dict[str, Any]:
    """
    List all migration phases with effort distribution

    Returns:
        10-phase methodology with typical percentage allocation
    """
    from app.services.migration_estimation_service import HOURS_PER_FP_BY_PHASE

    total = sum(HOURS_PER_FP_BY_PHASE.values())

    phases = []
    for phase in MigrationPhase:
        hours_per_fp = HOURS_PER_FP_BY_PHASE.get(phase, 0)
        percentage = (hours_per_fp / total * 100) if total > 0 else 0

        phases.append({
            "id": phase.value,
            "name": phase.name.replace("_", " ").title(),
            "hours_per_fp": hours_per_fp,
            "percentage": round(percentage, 1),
            "description": _get_phase_description(phase)
        })

    return {
        "total_phases": len(phases),
        "total_hours_per_fp": total,
        "phases": phases
    }


@router.get("/ifpug-weights")
async def get_ifpug_weights() -> Dict[str, Any]:
    """
    Get IFPUG function point weights (CPM 4.3.1)

    Returns:
        Complexity weights for all function point component types
    """
    from app.services.migration_estimation_service import IFPUG_WEIGHTS, ComponentType

    weights = {}
    for comp_type in ComponentType:
        weights[comp_type.value] = {
            "name": comp_type.name.replace("_", " "),
            "description": _get_component_description(comp_type),
            "complexity_weights": IFPUG_WEIGHTS.get(comp_type, {})
        }

    return {
        "methodology": "IFPUG CPM 4.3.1",
        "component_types": weights,
        "complexity_levels": ["low", "average", "high"],
        "reference": "https://www.ifpug.org/standards/cpm/"
    }


@router.get("/vaf-factors")
async def get_vaf_factors() -> Dict[str, Any]:
    """
    Get Value Adjustment Factor (VAF) characteristics

    Returns:
        14 General System Characteristics (GSCs) for VAF calculation
    """
    gscs = [
        {"id": 1, "name": "Data Communications", "description": "Degree of data exchange with external systems"},
        {"id": 2, "name": "Distributed Data Processing", "description": "Distribution of data processing"},
        {"id": 3, "name": "Performance", "description": "Response time and throughput requirements"},
        {"id": 4, "name": "Heavily Used Configuration", "description": "Hardware constraints"},
        {"id": 5, "name": "Transaction Rate", "description": "Volume of transactions"},
        {"id": 6, "name": "Online Data Entry", "description": "Percentage of online data entry"},
        {"id": 7, "name": "End-User Efficiency", "description": "Design for end-user efficiency"},
        {"id": 8, "name": "Online Update", "description": "ILFs updated online"},
        {"id": 9, "name": "Complex Processing", "description": "Security, math, algorithms"},
        {"id": 10, "name": "Reusability", "description": "Designed for reuse"},
        {"id": 11, "name": "Installation Ease", "description": "Conversion and installation requirements"},
        {"id": 12, "name": "Operational Ease", "description": "Startup, backup, recovery procedures"},
        {"id": 13, "name": "Multiple Sites", "description": "Designed for multiple installations"},
        {"id": 14, "name": "Facilitate Change", "description": "Designed for change"}
    ]

    return {
        "methodology": "IFPUG VAF",
        "formula": "VAF = (TDI × 0.01) + 0.65",
        "range": {"min": 0.65, "max": 1.35},
        "influence_scale": {"min": 0, "max": 5},
        "characteristics": gscs
    }


@router.post("/compare-stacks")
async def compare_stack_migrations(
    source_stack: str = Query(..., description="Source technology stack"),
    target_stacks: List[str] = Query(..., description="Target stacks to compare"),
    function_points: float = Query(500, gt=0, description="Estimated function points"),
    team_size: int = Query(5, ge=1, description="Team size")
) -> Dict[str, Any]:
    """
    Compare migration effort to different target stacks

    Returns:
        Side-by-side comparison of migration estimates
    """
    try:
        source = TechnologyStack(source_stack.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source stack. Valid: {[s.value for s in TechnologyStack]}"
        )

    comparisons = []
    for target_str in target_stacks:
        try:
            target = TechnologyStack(target_str.lower())

            phases = estimation_service.calculate_phase_breakdown(
                total_fp=function_points,
                source_stack=source,
                target_stack=target,
                team_size=team_size
            )

            total_hours = sum(p.hours for p in phases)

            comparisons.append({
                "target_stack": target.value,
                "total_hours": total_hours,
                "total_days": total_hours / 8,
                "total_weeks": total_hours / 40,
                "estimated_cost_usd": total_hours * 75,  # $75/hr average
                "complexity_rating": _get_complexity_rating(source, target)
            })
        except ValueError:
            comparisons.append({
                "target_stack": target_str,
                "error": "Invalid stack"
            })

    # Sort by hours
    valid = [c for c in comparisons if "total_hours" in c]
    valid.sort(key=lambda x: x["total_hours"])

    return {
        "source_stack": source_stack,
        "function_points": function_points,
        "team_size": team_size,
        "comparisons": comparisons,
        "recommendation": valid[0]["target_stack"] if valid else None
    }


@router.get("/eliza-context/{estimation_id}")
async def get_eliza_context(
    estimation_id: str,
    directory: str = Query(..., description="Directory path for analysis")
) -> Dict[str, Any]:
    """
    Generate Eliza agent context for detailed estimation review

    Returns:
        Context for Eliza to perform detailed estimation review
    """
    # Run estimation
    result = estimation_service.estimate_directory(
        directory=directory,
        source_stack=TechnologyStack.CLASSIC_ASP,  # Will be auto-detected
        target_stack=TechnologyStack.PYTHON_FASTAPI,
        team_size=5
    )

    return {
        "estimation_id": estimation_id,
        "eliza_context": {
            "summary": f"Migration estimation: {result.unadjusted_fp:.0f} UFP, {result.adjusted_fp:.0f} AFP",
            "methodology": "IFPUG CPM 4.3.1",
            "key_metrics": {
                "unadjusted_fp": result.unadjusted_fp,
                "adjusted_fp": result.adjusted_fp,
                "vaf": result.vaf,
                "total_hours": result.total_hours,
                "total_days": result.total_days
            },
            "component_breakdown": {
                comp_type.value: sum(
                    c.function_points for c in result.components
                    if c.component_type == comp_type
                )
                for comp_type in set(c.component_type for c in result.components)
            },
            "phase_distribution": [
                {"phase": p.phase.value, "hours": p.hours, "percentage": p.percentage}
                for p in result.phases
            ],
            "risk_factors": result.risks,
            "questions_for_review": [
                "Are the component counts accurate?",
                "Is the complexity classification correct for each component?",
                "Are there hidden integrations not detected?",
                "What's the data migration complexity?",
                "Are there regulatory compliance requirements?"
            ],
            "assumptions": result.assumptions
        },
        "recommendations": result.recommendations
    }


# ==================== Helper Functions ====================

def _get_stack_description(stack: TechnologyStack) -> str:
    """Get description for technology stack"""
    descriptions = {
        TechnologyStack.CLASSIC_ASP: "Microsoft Classic ASP with VBScript",
        TechnologyStack.VBNET_WEBFORMS: "VB.NET WebForms with code-behind",
        TechnologyStack.CSHARP_WEBFORMS: "C# WebForms with code-behind",
        TechnologyStack.PHP_LEGACY: "PHP 5.x procedural code",
        TechnologyStack.JAVA_LEGACY: "Java 6/7 with Struts/JSP",
        TechnologyStack.COBOL: "COBOL mainframe applications",
        TechnologyStack.ORACLE_FORMS: "Oracle Forms 6i/10g applications",
        TechnologyStack.POWERBUILDER: "PowerBuilder client-server apps",
        TechnologyStack.PYTHON_FASTAPI: "Modern Python with FastAPI",
        TechnologyStack.PYTHON_DJANGO: "Python with Django framework",
        TechnologyStack.DOTNET_CORE: ".NET 6/7/8 with minimal API",
        TechnologyStack.NODEJS_EXPRESS: "Node.js with Express framework",
        TechnologyStack.JAVA_SPRING: "Java with Spring Boot",
        TechnologyStack.GO_GIN: "Go with Gin framework",
        TechnologyStack.RUST_ACTIX: "Rust with Actix-web framework"
    }
    return descriptions.get(stack, "Unknown technology stack")


def _get_phase_description(phase: MigrationPhase) -> str:
    """Get description for migration phase"""
    descriptions = {
        MigrationPhase.DISCOVERY: "Initial assessment and scope definition",
        MigrationPhase.ANALYSIS: "Detailed technical and functional analysis",
        MigrationPhase.PLANNING: "Migration strategy and timeline planning",
        MigrationPhase.DESIGN: "Target architecture and design specification",
        MigrationPhase.DEVELOPMENT: "Code conversion and new development",
        MigrationPhase.TESTING: "Unit, integration, and system testing",
        MigrationPhase.DATA_MIGRATION: "Data extraction, transformation, loading",
        MigrationPhase.DEPLOYMENT: "Infrastructure setup and deployment",
        MigrationPhase.PARALLEL_RUN: "Running both systems in parallel",
        MigrationPhase.CUTOVER: "Final switchover and decommissioning"
    }
    return descriptions.get(phase, "Unknown phase")


def _get_component_description(comp_type) -> str:
    """Get description for component type"""
    from app.services.migration_estimation_service import ComponentType
    descriptions = {
        ComponentType.EI: "External Input - data entering the system boundary",
        ComponentType.EO: "External Output - data leaving the system boundary",
        ComponentType.EQ: "External Inquiry - input/output combination for queries",
        ComponentType.ILF: "Internal Logical File - user-maintained data groups",
        ComponentType.EIF: "External Interface File - referenced data groups"
    }
    return descriptions.get(comp_type, "Unknown component type")


def _get_complexity_rating(source: TechnologyStack, target: TechnologyStack) -> str:
    """Get migration complexity rating"""
    from app.services.migration_estimation_service import STACK_COMPLEXITY_MULTIPLIERS

    source_mult = STACK_COMPLEXITY_MULTIPLIERS.get(source, 1.0)
    target_mult = STACK_COMPLEXITY_MULTIPLIERS.get(target, 1.0)

    # Higher source complexity + lower target = easier
    # Lower source complexity + higher target = harder
    ratio = source_mult / target_mult if target_mult > 0 else source_mult

    if ratio > 1.5:
        return "Low - Modern target simplifies migration"
    elif ratio > 1.0:
        return "Medium - Balanced migration effort"
    else:
        return "High - Complex target architecture"
