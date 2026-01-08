# backend/app/api/migration_execution.py
"""
Migration Execution API - Fase 26 (Week 140-141)

Endpoints for migration execution services:
- Strangler Fig Pattern (incremental migration)
- Library Migration Mapper (legacy lib mapping)
- Wave Planner (dependency-based waves)
- UI Layer Extraction (UI component mapping)

Agents:
- Miguel (Strangler Fig)
- Felix (Library Mapper)
- Paul (Wave Planner)
- Vicky (UI Extraction)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db

router = APIRouter(prefix="/api/migration-execution", tags=["Migration Execution"])


# =============================================================================
# Request/Response Models
# =============================================================================

# Strangler Fig Models
class CreateStranglerSessionRequest(BaseModel):
    """Request to create a strangler fig session."""
    name: str
    source_path: str
    target_stack: str = "dotnet8"
    description: Optional[str] = None


class CreateFeatureFlagRequest(BaseModel):
    """Request to create a feature flag."""
    name: str
    description: Optional[str] = None
    default_value: bool = False
    legacy_modules: List[str] = Field(default_factory=list)
    modern_modules: List[str] = Field(default_factory=list)


class TrafficRuleRequest(BaseModel):
    """Request to create a traffic rule."""
    feature_flag_id: str
    rule_type: str = "percentage"
    percentage: int = 10
    target: str = "modern"
    conditions: Optional[Dict[str, Any]] = None


class RolloutPlanRequest(BaseModel):
    """Request to create a rollout plan."""
    feature_flag_id: str
    stages: Optional[List[Dict[str, Any]]] = None
    duration_hours: int = 168  # 1 week default


class HealthCheckRequest(BaseModel):
    """Request to record a health check."""
    feature_flag_id: str
    endpoint: str
    status: str = "healthy"
    latency_ms: float = 0.0
    error_rate: float = 0.0


# Library Mapper Models
class ScanLibrariesRequest(BaseModel):
    """Request to scan codebase for libraries."""
    source_path: str
    target_stack: str = "dotnet8"
    include_patterns: List[str] = Field(default_factory=lambda: ["*.vb", "*.cs", "*.aspx"])
    exclude_patterns: List[str] = Field(default_factory=lambda: ["*test*", "*Test*"])


class GenerateMappingsRequest(BaseModel):
    """Request to generate library mappings."""
    libraries: List[Dict[str, Any]]
    target_stack: str = "dotnet8"


# Wave Planner Models
class AnalyzeDependenciesRequest(BaseModel):
    """Request to analyze module dependencies."""
    source_path: str
    modules: Optional[List[str]] = None


class CreateWavePlanRequest(BaseModel):
    """Request to create a wave plan."""
    source_path: str
    strategy: str = "risk_balanced"
    max_modules_per_wave: int = 5
    team_capacity: int = 3


class ScheduleWavesRequest(BaseModel):
    """Request to schedule waves."""
    wave_plan_id: str
    start_date: Optional[str] = None
    sprint_duration_days: int = 14


# UI Extraction Models
class ExtractUIRequest(BaseModel):
    """Request to extract UI components."""
    source_path: str
    target_framework: str = "react"
    include_patterns: List[str] = Field(default_factory=lambda: ["*.aspx", "*.ascx", "*.cshtml"])


class GenerateComponentMappingsRequest(BaseModel):
    """Request to generate component mappings."""
    components: List[Dict[str, Any]]
    target_framework: str = "react"


# =============================================================================
# Strangler Fig Endpoints
# =============================================================================

@router.post("/strangler/sessions")
async def create_strangler_session(
    request: CreateStranglerSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new strangler fig migration session.

    Agent: Miguel (Migration Architect)
    """
    from app.services.strangler_fig_service import StranglerFigService

    service = StranglerFigService(db)
    session = await service.create_session(
        name=request.name,
        source_path=request.source_path,
        target_stack=request.target_stack,
        description=request.description
    )

    return {
        "session_id": session.id,
        "name": session.name,
        "status": session.status.value if hasattr(session.status, 'value') else str(session.status),
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "message": "Strangler fig session created successfully"
    }


@router.get("/strangler/sessions/{session_id}")
async def get_strangler_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get strangler fig session details.
    """
    from app.services.strangler_fig_service import StranglerFigService

    service = StranglerFigService(db)
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session.id,
        "name": session.name,
        "status": session.status.value if hasattr(session.status, 'value') else str(session.status),
        "source_path": session.source_path,
        "target_stack": session.target_stack,
        "feature_flags": len(session.feature_flags),
        "traffic_rules": len(session.traffic_rules),
        "rollout_plans": len(session.rollout_plans),
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }


@router.post("/strangler/sessions/{session_id}/feature-flags")
async def create_feature_flag(
    session_id: str,
    request: CreateFeatureFlagRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a feature flag for the strangler fig migration.
    """
    from app.services.strangler_fig_service import StranglerFigService

    service = StranglerFigService(db)
    flag = await service.create_feature_flag(
        session_id=session_id,
        name=request.name,
        description=request.description,
        default_value=request.default_value,
        legacy_modules=request.legacy_modules,
        modern_modules=request.modern_modules
    )

    return {
        "flag_id": flag.id,
        "name": flag.name,
        "enabled": flag.enabled,
        "default_value": flag.default_value,
        "created_at": flag.created_at.isoformat() if flag.created_at else None,
        "message": "Feature flag created successfully"
    }


@router.get("/strangler/sessions/{session_id}/feature-flags")
async def list_feature_flags(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    List all feature flags for a session.
    """
    from app.services.strangler_fig_service import StranglerFigService

    service = StranglerFigService(db)
    flags = await service.list_feature_flags(session_id)

    return {
        "session_id": session_id,
        "count": len(flags),
        "feature_flags": [
            {
                "id": f.id,
                "name": f.name,
                "enabled": f.enabled,
                "default_value": f.default_value,
                "rollout_percentage": f.rollout_percentage,
            }
            for f in flags
        ]
    }


@router.post("/strangler/sessions/{session_id}/traffic-rules")
async def create_traffic_rule(
    session_id: str,
    request: TrafficRuleRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a traffic routing rule.
    """
    from app.services.strangler_fig_service import StranglerFigService

    service = StranglerFigService(db)
    rule = await service.create_traffic_rule(
        session_id=session_id,
        feature_flag_id=request.feature_flag_id,
        rule_type=request.rule_type,
        percentage=request.percentage,
        target=request.target,
        conditions=request.conditions
    )

    return {
        "rule_id": rule.id,
        "feature_flag_id": rule.feature_flag_id,
        "rule_type": rule.rule_type,
        "percentage": rule.percentage,
        "target": rule.target,
        "message": "Traffic rule created successfully"
    }


@router.post("/strangler/sessions/{session_id}/evaluate-routing")
async def evaluate_traffic_routing(
    session_id: str,
    request_context: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluate traffic routing for a request context.
    """
    from app.services.strangler_fig_service import StranglerFigService

    service = StranglerFigService(db)
    result = await service.evaluate_traffic_routing(session_id, request_context)

    return result


@router.post("/strangler/sessions/{session_id}/rollout-plans")
async def create_rollout_plan(
    session_id: str,
    request: RolloutPlanRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a gradual rollout plan for a feature flag.
    """
    from app.services.strangler_fig_service import StranglerFigService

    service = StranglerFigService(db)
    plan = await service.create_rollout_plan(
        session_id=session_id,
        feature_flag_id=request.feature_flag_id,
        stages=request.stages,
        duration_hours=request.duration_hours
    )

    return {
        "plan_id": plan.id,
        "feature_flag_id": plan.feature_flag_id,
        "stages": len(plan.stages),
        "current_stage": plan.current_stage,
        "status": plan.status,
        "message": "Rollout plan created successfully"
    }


@router.post("/strangler/sessions/{session_id}/rollout-plans/{plan_id}/advance")
async def advance_rollout(
    session_id: str,
    plan_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Advance a rollout plan to the next stage.
    """
    from app.services.strangler_fig_service import StranglerFigService

    service = StranglerFigService(db)
    plan = await service.advance_rollout(session_id, plan_id)

    return {
        "plan_id": plan.id,
        "current_stage": plan.current_stage,
        "status": plan.status,
        "message": "Rollout advanced to next stage"
    }


@router.post("/strangler/sessions/{session_id}/rollout-plans/{plan_id}/rollback")
async def rollback_plan(
    session_id: str,
    plan_id: str,
    reason: str = "Manual rollback",
    db: AsyncSession = Depends(get_db)
):
    """
    Rollback a rollout plan to previous stage or initial state.
    """
    from app.services.strangler_fig_service import StranglerFigService

    service = StranglerFigService(db)
    plan = await service.rollback_plan(session_id, plan_id, reason)

    return {
        "plan_id": plan.id,
        "current_stage": plan.current_stage,
        "status": plan.status,
        "message": f"Rollout rolled back: {reason}"
    }


@router.post("/strangler/sessions/{session_id}/health-checks")
async def record_health_check(
    session_id: str,
    request: HealthCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Record a health check for monitoring.
    """
    from app.services.strangler_fig_service import StranglerFigService

    service = StranglerFigService(db)
    check = await service.record_health_check(
        session_id=session_id,
        feature_flag_id=request.feature_flag_id,
        endpoint=request.endpoint,
        status=request.status,
        latency_ms=request.latency_ms,
        error_rate=request.error_rate
    )

    return {
        "check_id": check.id,
        "status": check.status,
        "recorded_at": check.timestamp.isoformat() if check.timestamp else None,
    }


@router.get("/strangler/sessions/{session_id}/report")
async def get_strangler_report(
    session_id: str,
    format: str = Query("json", enum=["json", "markdown", "mermaid"]),
    db: AsyncSession = Depends(get_db)
):
    """
    Get strangler fig migration report.
    """
    from app.services.strangler_fig_service import StranglerFigService

    service = StranglerFigService(db)

    if format == "markdown":
        report = await service.export_markdown(session_id)
        return {"format": "markdown", "content": report}
    elif format == "mermaid":
        diagram = await service.export_mermaid(session_id)
        return {"format": "mermaid", "content": diagram}
    else:
        report = await service.get_session_report(session_id)
        return report


# =============================================================================
# Library Migration Mapper Endpoints
# =============================================================================

@router.post("/library-mapper/scan")
async def scan_libraries(
    request: ScanLibrariesRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Scan codebase for external library usage.

    Agent: Felix (Feature Architect)
    """
    from app.services.library_migration_mapper_service import LibraryMigrationMapperService

    service = LibraryMigrationMapperService(db)
    libraries = await service.scan_codebase(
        source_path=request.source_path,
        include_patterns=request.include_patterns,
        exclude_patterns=request.exclude_patterns
    )

    return {
        "source_path": request.source_path,
        "libraries_found": len(libraries),
        "libraries": [
            {
                "name": lib.name,
                "version": lib.version,
                "usage_count": lib.usage_count,
                "file_locations": lib.file_locations[:5],  # Limit to first 5
                "patterns": lib.usage_patterns[:3],
            }
            for lib in libraries
        ]
    }


@router.post("/library-mapper/mappings")
async def generate_library_mappings(
    request: GenerateMappingsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate library mappings for target stack.
    """
    from app.services.library_migration_mapper_service import LibraryMigrationMapperService

    service = LibraryMigrationMapperService(db)
    mappings = await service.generate_mappings(
        libraries=request.libraries,
        target_stack=request.target_stack
    )

    # Categorize by risk
    high_risk = [m for m in mappings if m.risk_level == "high" or m.risk_level == "critical"]
    medium_risk = [m for m in mappings if m.risk_level == "medium"]
    low_risk = [m for m in mappings if m.risk_level == "low"]

    return {
        "target_stack": request.target_stack,
        "total_mappings": len(mappings),
        "risk_summary": {
            "high": len(high_risk),
            "medium": len(medium_risk),
            "low": len(low_risk),
        },
        "mappings": [
            {
                "legacy_library": m.legacy_library.name if hasattr(m, 'legacy_library') else m.get('legacy_library'),
                "modern_equivalent": m.modern_equivalent.name if hasattr(m, 'modern_equivalent') else m.get('modern_equivalent'),
                "effort": m.effort.value if hasattr(m.effort, 'value') else str(m.effort),
                "risk_level": m.risk_level,
                "notes": m.notes,
            }
            for m in mappings
        ]
    }


@router.get("/library-mapper/mapping/{library_name}")
async def get_library_mapping(
    library_name: str,
    target_stack: str = Query("dotnet8"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get mapping for a specific library.
    """
    from app.services.library_migration_mapper_service import LibraryMigrationMapperService

    service = LibraryMigrationMapperService(db)
    mapping = await service.get_library_mapping(library_name, target_stack)

    if not mapping:
        raise HTTPException(status_code=404, detail=f"No mapping found for {library_name}")

    return mapping


@router.post("/library-mapper/rules")
async def generate_migration_rules(
    request: GenerateMappingsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate migration rules for libraries.
    """
    from app.services.library_migration_mapper_service import LibraryMigrationMapperService

    service = LibraryMigrationMapperService(db)
    rules = await service.generate_migration_rules(
        mappings=request.libraries,
        target_stack=request.target_stack
    )

    return {
        "target_stack": request.target_stack,
        "rules_generated": len(rules),
        "rules": rules
    }


@router.get("/library-mapper/report")
async def get_library_mapper_report(
    source_path: str,
    target_stack: str = "dotnet8",
    format: str = Query("json", enum=["json", "markdown"]),
    db: AsyncSession = Depends(get_db)
):
    """
    Get library migration report.
    """
    from app.services.library_migration_mapper_service import LibraryMigrationMapperService

    service = LibraryMigrationMapperService(db)

    if format == "markdown":
        report = await service.export_markdown(source_path, target_stack)
        return {"format": "markdown", "content": report}
    else:
        report = await service.get_full_report(source_path, target_stack)
        return report


# =============================================================================
# Wave Planner Endpoints
# =============================================================================

@router.post("/wave-planner/analyze-dependencies")
async def analyze_dependencies(
    request: AnalyzeDependenciesRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze module dependencies.

    Agent: Paul (Project Lead)
    """
    from app.services.wave_planner_service import WavePlannerService

    service = WavePlannerService(db)
    graph = await service.analyze_dependencies(
        source_path=request.source_path,
        modules=request.modules
    )

    return {
        "source_path": request.source_path,
        "modules_analyzed": len(graph.nodes),
        "dependencies": len(graph.edges),
        "circular_dependencies": graph.circular_dependencies,
        "entry_points": graph.entry_points,
        "leaf_nodes": graph.leaf_nodes,
    }


@router.post("/wave-planner/create-plan")
async def create_wave_plan(
    request: CreateWavePlanRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a wave-based migration plan.
    """
    from app.services.wave_planner_service import WavePlannerService

    service = WavePlannerService(db)
    plan = await service.create_wave_plan(
        source_path=request.source_path,
        strategy=request.strategy,
        max_modules_per_wave=request.max_modules_per_wave,
        team_capacity=request.team_capacity
    )

    return {
        "plan_id": plan.id,
        "strategy": plan.strategy,
        "total_waves": len(plan.waves),
        "total_modules": sum(len(w.modules) for w in plan.waves),
        "estimated_duration_weeks": plan.estimated_duration_weeks,
        "waves_summary": [
            {
                "wave_number": w.wave_number,
                "modules": len(w.modules),
                "risk_level": w.risk_level,
                "estimated_effort_days": w.estimated_effort_days,
            }
            for w in plan.waves
        ]
    }


@router.get("/wave-planner/plans/{plan_id}")
async def get_wave_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get wave plan details.
    """
    from app.services.wave_planner_service import WavePlannerService

    service = WavePlannerService(db)
    plan = await service.get_wave_plan(plan_id)

    if not plan:
        raise HTTPException(status_code=404, detail="Wave plan not found")

    return {
        "plan_id": plan.id,
        "strategy": plan.strategy,
        "status": plan.status,
        "waves": [
            {
                "wave_number": w.wave_number,
                "modules": [m.name for m in w.modules],
                "dependencies": w.dependencies,
                "risk_level": w.risk_level,
                "estimated_effort_days": w.estimated_effort_days,
                "status": w.status,
            }
            for w in plan.waves
        ],
        "critical_path": plan.critical_path,
        "risks": plan.risks,
    }


@router.post("/wave-planner/plans/{plan_id}/schedule")
async def schedule_waves(
    plan_id: str,
    request: ScheduleWavesRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Schedule waves with dates and team assignments.
    """
    from app.services.wave_planner_service import WavePlannerService

    service = WavePlannerService(db)
    schedule = await service.schedule_waves(
        plan_id=plan_id,
        start_date=request.start_date,
        sprint_duration_days=request.sprint_duration_days
    )

    return {
        "plan_id": plan_id,
        "schedule": schedule
    }


@router.get("/wave-planner/plans/{plan_id}/gantt")
async def get_wave_gantt(
    plan_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get Mermaid Gantt chart for wave plan.
    """
    from app.services.wave_planner_service import WavePlannerService

    service = WavePlannerService(db)
    gantt = await service.export_mermaid_gantt(plan_id)

    return {
        "format": "mermaid",
        "type": "gantt",
        "content": gantt
    }


@router.get("/wave-planner/plans/{plan_id}/report")
async def get_wave_plan_report(
    plan_id: str,
    format: str = Query("json", enum=["json", "markdown"]),
    db: AsyncSession = Depends(get_db)
):
    """
    Get wave plan report.
    """
    from app.services.wave_planner_service import WavePlannerService

    service = WavePlannerService(db)

    if format == "markdown":
        report = await service.export_markdown(plan_id)
        return {"format": "markdown", "content": report}
    else:
        report = await service.get_full_report(plan_id)
        return report


# =============================================================================
# UI Layer Extraction Endpoints
# =============================================================================

@router.post("/ui-extraction/extract")
async def extract_ui_components(
    request: ExtractUIRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Extract UI components from legacy codebase.

    Agent: Vicky (Visual Designer)
    """
    from app.services.ui_layer_extraction_service import UILayerExtractionService

    service = UILayerExtractionService(db)
    result = await service.extract_ui_components(
        source_path=request.source_path,
        include_patterns=request.include_patterns
    )

    return {
        "source_path": request.source_path,
        "components_found": len(result.components),
        "pages_analyzed": len(result.pages),
        "design_tokens_extracted": len(result.design_tokens),
        "components": [
            {
                "name": c.name,
                "type": c.component_type,
                "source_file": c.source_file,
                "properties": len(c.properties),
            }
            for c in result.components[:20]  # Limit to first 20
        ]
    }


@router.post("/ui-extraction/design-tokens")
async def extract_design_tokens(
    request: ExtractUIRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Extract design tokens (colors, typography, spacing) from legacy UI.
    """
    from app.services.ui_layer_extraction_service import UILayerExtractionService

    service = UILayerExtractionService(db)
    tokens = await service.extract_design_tokens(
        source_path=request.source_path,
        include_patterns=request.include_patterns
    )

    return {
        "source_path": request.source_path,
        "tokens": {
            "colors": tokens.colors,
            "typography": tokens.typography,
            "spacing": tokens.spacing,
            "borders": tokens.borders,
            "shadows": tokens.shadows,
        },
        "css_variables": tokens.to_css_variables() if hasattr(tokens, 'to_css_variables') else None,
    }


@router.post("/ui-extraction/component-mappings")
async def generate_component_mappings(
    request: GenerateComponentMappingsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate component mappings for target framework.
    """
    from app.services.ui_layer_extraction_service import UILayerExtractionService

    service = UILayerExtractionService(db)
    mappings = await service.generate_component_mappings(
        components=request.components,
        target_framework=request.target_framework
    )

    return {
        "target_framework": request.target_framework,
        "total_mappings": len(mappings),
        "mappings": [
            {
                "legacy_component": m.legacy_component,
                "modern_component": m.modern_component,
                "library": m.library,
                "effort": m.effort,
                "notes": m.notes,
            }
            for m in mappings
        ]
    }


@router.get("/ui-extraction/report")
async def get_ui_extraction_report(
    source_path: str,
    target_framework: str = "react",
    format: str = Query("json", enum=["json", "markdown"]),
    db: AsyncSession = Depends(get_db)
):
    """
    Get UI extraction report.
    """
    from app.services.ui_layer_extraction_service import UILayerExtractionService

    service = UILayerExtractionService(db)

    if format == "markdown":
        report = await service.export_markdown(source_path, target_framework)
        return {"format": "markdown", "content": report}
    else:
        report = await service.get_full_report(source_path, target_framework)
        return report


@router.get("/ui-extraction/design-system")
async def get_design_system(
    source_path: str,
    target_framework: str = "react",
    db: AsyncSession = Depends(get_db)
):
    """
    Get generated design system configuration.
    """
    from app.services.ui_layer_extraction_service import UILayerExtractionService

    service = UILayerExtractionService(db)
    design_system = await service.generate_design_system(source_path, target_framework)

    return design_system


# =============================================================================
# Combined Report Endpoint
# =============================================================================

@router.get("/report/{session_id}")
async def get_combined_migration_report(
    session_id: str,
    format: str = Query("json", enum=["json", "markdown"]),
    db: AsyncSession = Depends(get_db)
):
    """
    Get combined Fase 26 migration execution report.

    Combines:
    - Strangler fig status
    - Library mappings
    - Wave plan
    - UI extraction
    """
    # This would aggregate reports from all services
    return {
        "session_id": session_id,
        "fase": 26,
        "status": "in_progress",
        "message": "Combined report aggregation - implement with actual session data",
        "components": {
            "strangler_fig": "pending",
            "library_mapper": "pending",
            "wave_planner": "pending",
            "ui_extraction": "pending",
        }
    }
