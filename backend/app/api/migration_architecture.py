"""
Migration Architecture API - Felix Integration Endpoints

Week 68 Day 3-4: REST API for target architecture recommendations
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.services.migration_architecture_service import (
    MigrationArchitectureService,
    ArchitecturePattern,
    TechnologyChoice,
    MigrationStrategy
)


router = APIRouter(prefix="/api/migration-architecture", tags=["Migration Architecture"])

# Initialize service
architecture_service = MigrationArchitectureService()


# ==================== Request/Response Models ====================

class AnalyzeRequest(BaseModel):
    """Request to analyze directory and generate architecture recommendations"""
    directory: str = Field(..., description="Path to source code directory")
    target_technology: str = Field("python_fastapi", description="Target technology stack")
    preferred_pattern: Optional[str] = Field(None, description="Preferred architecture pattern")


class CompareRequest(BaseModel):
    """Request to compare architecture options"""
    directory: str = Field(..., description="Path to source code directory")
    patterns: List[str] = Field(..., description="Patterns to compare")
    technologies: List[str] = Field(..., description="Technologies to compare")


class ADRRequest(BaseModel):
    """Request to generate Architecture Decision Records"""
    directory: str = Field(..., description="Path to source code directory")
    decisions_to_document: Optional[List[str]] = Field(
        None,
        description="Specific decisions to document (pattern, strategy, technology, database)"
    )


# ==================== API Endpoints ====================

@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get architecture service status and capabilities"""
    return architecture_service.get_status()


@router.post("/analyze")
async def analyze_architecture(request: AnalyzeRequest) -> Dict[str, Any]:
    """
    Analyze directory and generate target architecture recommendations

    Uses Felix agent methodology to:
    - Detect legacy component patterns
    - Recommend target architecture
    - Generate component mappings
    - Create API contracts
    - Plan data migration

    Returns:
        Complete architecture recommendation with ADRs
    """
    # Validate target technology
    try:
        target_tech = TechnologyChoice(request.target_technology.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid technology. Valid: {[t.value for t in TechnologyChoice]}"
        )

    # Validate preferred pattern if specified
    preferred = None
    if request.preferred_pattern:
        try:
            preferred = ArchitecturePattern(request.preferred_pattern.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid pattern. Valid: {[p.value for p in ArchitecturePattern]}"
            )

    result = architecture_service.analyze_directory(
        directory=request.directory,
        target_technology=target_tech,
        preferred_pattern=preferred
    )

    return result.to_dict()


@router.get("/patterns")
async def list_patterns() -> Dict[str, Any]:
    """
    List all available architecture patterns

    Returns:
        Architecture patterns with suitability descriptions
    """
    patterns = architecture_service.get_patterns()

    return {
        "total_patterns": len(patterns),
        "patterns": patterns
    }


@router.get("/patterns/{pattern_id}")
async def get_pattern_detail(pattern_id: str) -> Dict[str, Any]:
    """
    Get detailed information about an architecture pattern

    Returns:
        Pattern details with pros, cons, and use cases
    """
    try:
        pattern = ArchitecturePattern(pattern_id.lower())
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Pattern not found. Valid: {[p.value for p in ArchitecturePattern]}"
        )

    detail = {
        ArchitecturePattern.MONOLITH: {
            "pros": ["Simple deployment", "Easy debugging", "Low complexity"],
            "cons": ["Scaling limitations", "Single point of failure", "Technology lock-in"],
            "use_cases": ["MVPs", "Small teams", "Simple domains"]
        },
        ArchitecturePattern.MODULAR_MONOLITH: {
            "pros": ["Module boundaries", "Easier to refactor", "Single deployment"],
            "cons": ["Module coupling risk", "Still single deployment", "Database sharing"],
            "use_cases": ["Growing applications", "Teams preparing for microservices"]
        },
        ArchitecturePattern.MICROSERVICES: {
            "pros": ["Independent scaling", "Technology flexibility", "Team autonomy"],
            "cons": ["Distributed complexity", "Network latency", "Operational overhead"],
            "use_cases": ["Large teams", "High scale", "Complex domains"]
        },
        ArchitecturePattern.CLEAN_ARCHITECTURE: {
            "pros": ["Framework independence", "Testability", "Business focus"],
            "cons": ["Initial complexity", "More code", "Learning curve"],
            "use_cases": ["Long-lived applications", "Complex business logic"]
        },
        ArchitecturePattern.HEXAGONAL: {
            "pros": ["Port isolation", "Adapter flexibility", "Technology swapping"],
            "cons": ["Complexity", "Over-engineering risk", "Team alignment needed"],
            "use_cases": ["Integration-heavy systems", "Multiple interfaces"]
        },
        ArchitecturePattern.EVENT_DRIVEN: {
            "pros": ["Loose coupling", "Scalability", "Resilience"],
            "cons": ["Eventual consistency", "Debugging difficulty", "Event ordering"],
            "use_cases": ["Async workflows", "Real-time systems", "Microservices communication"]
        },
        ArchitecturePattern.SERVERLESS: {
            "pros": ["Auto-scaling", "Cost efficiency", "No server management"],
            "cons": ["Vendor lock-in", "Cold starts", "Execution limits"],
            "use_cases": ["Variable workloads", "Event triggers", "Batch processing"]
        },
        ArchitecturePattern.CQRS: {
            "pros": ["Optimized queries", "Scalability", "Event sourcing synergy"],
            "cons": ["Complexity", "Eventual consistency", "More code"],
            "use_cases": ["Complex queries", "High read/write ratio", "Audit requirements"]
        }
    }

    return {
        "pattern": pattern.value,
        "name": pattern.name.replace("_", " ").title(),
        **detail.get(pattern, {})
    }


@router.get("/strategies")
async def list_strategies() -> Dict[str, Any]:
    """
    List all available migration strategies

    Returns:
        Migration strategies with risk levels and descriptions
    """
    strategies = architecture_service.get_strategies()

    return {
        "total_strategies": len(strategies),
        "strategies": strategies
    }


@router.get("/strategies/{strategy_id}")
async def get_strategy_detail(strategy_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a migration strategy

    Returns:
        Strategy details with phases and prerequisites
    """
    try:
        strategy = MigrationStrategy(strategy_id.lower())
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Strategy not found. Valid: {[s.value for s in MigrationStrategy]}"
        )

    detail = {
        MigrationStrategy.STRANGLER_FIG: {
            "phases": [
                "Identify bounded contexts",
                "Build new functionality alongside legacy",
                "Redirect traffic gradually",
                "Decommission legacy components"
            ],
            "prerequisites": ["Clear module boundaries", "Routing capability"],
            "duration": "6-18 months",
            "team_size": "2-5 developers per component"
        },
        MigrationStrategy.BIG_BANG: {
            "phases": [
                "Complete development",
                "Extensive testing",
                "Data migration",
                "Single cutover"
            ],
            "prerequisites": ["Detailed specifications", "Complete test coverage"],
            "duration": "3-12 months",
            "team_size": "Full team dedicated"
        },
        MigrationStrategy.PARALLEL_RUN: {
            "phases": [
                "Deploy new system",
                "Run both systems",
                "Compare outputs",
                "Validate and cutover"
            ],
            "prerequisites": ["Data sync mechanism", "Comparison tooling"],
            "duration": "4-12 months",
            "team_size": "Team + operations support"
        },
        MigrationStrategy.INCREMENTAL: {
            "phases": [
                "Prioritize features",
                "Migrate one feature at a time",
                "Validate each migration",
                "Continue until complete"
            ],
            "prerequisites": ["Feature isolation possible", "Interface stability"],
            "duration": "6-24 months",
            "team_size": "1-3 developers per feature"
        },
        MigrationStrategy.PHASED: {
            "phases": [
                "Define phases by business area",
                "Migrate phase by phase",
                "Stabilize between phases",
                "Complete final phase"
            ],
            "prerequisites": ["Clear phase boundaries", "Business alignment"],
            "duration": "12-36 months",
            "team_size": "Variable per phase"
        },
        MigrationStrategy.BLUE_GREEN: {
            "phases": [
                "Set up parallel environment",
                "Deploy to green",
                "Test thoroughly",
                "Switch traffic",
                "Keep blue for rollback"
            ],
            "prerequisites": ["Infrastructure automation", "Load balancer"],
            "duration": "1-6 months deployment cycles",
            "team_size": "DevOps + development team"
        }
    }

    return {
        "strategy": strategy.value,
        "name": strategy.name.replace("_", " ").title(),
        **detail.get(strategy, {})
    }


@router.get("/technologies")
async def list_technologies() -> Dict[str, Any]:
    """
    List all supported target technologies

    Returns:
        Technology options with framework details
    """
    technologies = []

    for tech in TechnologyChoice:
        category = "backend"
        if tech.value in ["react", "vue", "angular", "nextjs", "blazor"]:
            category = "frontend"
        elif tech.value in ["postgresql", "mysql", "mongodb", "redis", "elasticsearch"]:
            category = "database"
        elif tech.value in ["docker", "kubernetes", "aws", "azure", "gcp"]:
            category = "infrastructure"

        technologies.append({
            "id": tech.value,
            "name": tech.name.replace("_", " ").title(),
            "category": category
        })

    # Group by category
    grouped = {}
    for t in technologies:
        cat = t["category"]
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append({"id": t["id"], "name": t["name"]})

    return {
        "total_technologies": len(technologies),
        "by_category": grouped
    }


@router.post("/compare")
async def compare_options(request: CompareRequest) -> Dict[str, Any]:
    """
    Compare multiple architecture options

    Returns:
        Side-by-side comparison of patterns and technologies
    """
    comparisons = []

    for pattern_str in request.patterns:
        for tech_str in request.technologies:
            try:
                pattern = ArchitecturePattern(pattern_str.lower())
                tech = TechnologyChoice(tech_str.lower())

                result = architecture_service.analyze_directory(
                    directory=request.directory,
                    target_technology=tech,
                    preferred_pattern=pattern
                )

                comparisons.append({
                    "pattern": pattern.value,
                    "technology": tech.value,
                    "confidence_score": result.confidence_score,
                    "total_effort_hours": result.total_effort_hours,
                    "component_count": len(result.target_components),
                    "api_count": len(result.api_contracts),
                    "risk_count": len(result.risks)
                })
            except ValueError:
                comparisons.append({
                    "pattern": pattern_str,
                    "technology": tech_str,
                    "error": "Invalid pattern or technology"
                })

    # Sort by effort (lower is better)
    valid = [c for c in comparisons if "total_effort_hours" in c]
    valid.sort(key=lambda x: x["total_effort_hours"])

    return {
        "directory": request.directory,
        "comparisons": comparisons,
        "recommended": valid[0] if valid else None
    }


@router.post("/adr")
async def generate_adrs(request: ADRRequest) -> Dict[str, Any]:
    """
    Generate Architecture Decision Records (ADRs)

    Returns:
        Formatted ADRs for documentation
    """
    result = architecture_service.analyze_directory(request.directory)

    # Filter ADRs if specific ones requested
    if request.decisions_to_document:
        adrs = [
            a for a in result.architecture_decisions
            if any(d.lower() in a.title.lower() for d in request.decisions_to_document)
        ]
    else:
        adrs = result.architecture_decisions

    return {
        "recommendation_id": result.recommendation_id,
        "adr_count": len(adrs),
        "adrs": [
            {
                "id": a.id,
                "title": a.title,
                "status": a.status,
                "context": a.context,
                "decision": a.decision,
                "rationale": a.rationale,
                "consequences": a.consequences,
                "alternatives": a.alternatives_considered,
                "markdown": _format_adr_markdown(a)
            }
            for a in adrs
        ]
    }


@router.get("/felix-context/{recommendation_id}")
async def get_felix_context(
    recommendation_id: str,
    directory: str = Query(..., description="Directory path for analysis")
) -> Dict[str, Any]:
    """
    Generate Felix agent context for architecture review

    Returns:
        Context for Felix to perform detailed architecture review
    """
    result = architecture_service.analyze_directory(directory)

    return {
        "recommendation_id": recommendation_id,
        "felix_context": {
            "summary": result.felix_context.summary,
            "key_decisions": result.felix_context.key_decisions,
            "risks": result.felix_context.risks,
            "questions_for_review": result.felix_context.questions_for_review,
            "recommended_patterns": result.felix_context.recommended_patterns,
            "technology_stack": result.felix_context.technology_stack
        },
        "source_analysis": result.source_analysis,
        "component_summary": {
            "legacy_count": len(result.legacy_components),
            "target_count": len(result.target_components),
            "api_count": len(result.api_contracts),
            "table_count": len(result.data_migration_plan)
        },
        "recommendations": result.recommendations
    }


@router.get("/component-mapping/{recommendation_id}")
async def get_component_mapping(
    recommendation_id: str,
    directory: str = Query(..., description="Directory path for analysis")
) -> Dict[str, Any]:
    """
    Get legacy to target component mapping

    Returns:
        Detailed mapping between legacy and target components
    """
    result = architecture_service.analyze_directory(directory)

    # Create mapping by layer
    mapping = {}
    for target in result.target_components:
        layer = target.layer.value
        if layer not in mapping:
            mapping[layer] = {
                "legacy_components": [],
                "target_component": None
            }

        mapping[layer]["target_component"] = {
            "name": target.name,
            "technology": target.technology.value,
            "responsibilities": target.responsibilities,
            "effort_hours": target.estimated_effort_hours
        }

    for legacy in result.legacy_components:
        layer = legacy.layer.value
        if layer in mapping:
            mapping[layer]["legacy_components"].append({
                "name": legacy.name,
                "file_count": len(legacy.file_paths),
                "complexity": legacy.complexity
            })

    return {
        "recommendation_id": recommendation_id,
        "layer_mapping": mapping,
        "total_legacy_components": len(result.legacy_components),
        "total_target_components": len(result.target_components)
    }


@router.get("/api-contracts/{recommendation_id}")
async def get_api_contracts(
    recommendation_id: str,
    directory: str = Query(..., description="Directory path for analysis")
) -> Dict[str, Any]:
    """
    Get generated API contracts

    Returns:
        OpenAPI-style API contract specifications
    """
    result = architecture_service.analyze_directory(directory)

    # Group by resource
    contracts_by_resource = {}
    for contract in result.api_contracts:
        # Extract resource name from endpoint
        parts = contract.endpoint.split("/")
        resource = parts[2] if len(parts) > 2 else "root"

        if resource not in contracts_by_resource:
            contracts_by_resource[resource] = []

        contracts_by_resource[resource].append({
            "endpoint": contract.endpoint,
            "method": contract.method,
            "description": contract.description,
            "request": contract.request_schema,
            "response": contract.response_schema,
            "legacy": contract.legacy_equivalent
        })

    return {
        "recommendation_id": recommendation_id,
        "total_endpoints": len(result.api_contracts),
        "resources": contracts_by_resource,
        "openapi_compatible": True
    }


@router.get("/data-migration/{recommendation_id}")
async def get_data_migration_plan(
    recommendation_id: str,
    directory: str = Query(..., description="Directory path for analysis")
) -> Dict[str, Any]:
    """
    Get data migration plan

    Returns:
        Table-by-table data migration strategy
    """
    result = architecture_service.analyze_directory(directory)

    return {
        "recommendation_id": recommendation_id,
        "total_tables": len(result.data_migration_plan),
        "migration_plan": [
            {
                "order": m.migration_order,
                "source_table": m.source_table,
                "target_table": m.target_table,
                "transformations": m.transformation_rules,
                "validations": m.validation_rules,
                "estimated_rows": m.estimated_row_count,
                "dependencies": m.dependencies
            }
            for m in sorted(result.data_migration_plan, key=lambda x: x.migration_order)
        ]
    }


# ==================== Helper Functions ====================

def _format_adr_markdown(adr) -> str:
    """Format ADR as markdown"""
    return f"""# {adr.id}: {adr.title}

## Status
{adr.status.upper()}

## Context
{adr.context}

## Decision
{adr.decision}

## Rationale
{adr.rationale}

## Consequences
{chr(10).join(f'- {c}' for c in adr.consequences)}

## Alternatives Considered
{chr(10).join(f'- {a}' for a in adr.alternatives_considered)}
"""
