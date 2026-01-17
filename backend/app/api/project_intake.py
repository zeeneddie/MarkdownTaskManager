"""
Project Intake Wizard API - Week 145

Endpoints for managing project intakes:
- Brown Paper: Discovery bestaand systeem → onderhoud of migratie
- Green Paper: Nieuw project vanaf scratch
- Migratie: Transformatie (vereist Brown Paper als voorwaarde)

Flow:
- Brown Paper → Decision → (optioneel) Migration
- Green Paper → Project Generation
- Migration (requires Brown Paper) → Project Generation
"""

from datetime import datetime, timezone, date
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.project_intake import (
    ProjectIntake,
    ProjectIntakeSource,
    ProjectIntakeIntegration,
    ProjectIntakeScope,
    ProjectIntakeFeature,
    ProjectIntakeEvent,
    TrajectType,
    MigrationType,
    IntegrationAction,
    IntakeStatus,
    AnalysisTier,
    ExpectedOutcome,
    MigrationStrategy,
    BrownPaperDecision,
    IntakeEventType,
    PREDEFINED_FEATURES,
)
from app.models.bmad_session import BMADSession


router = APIRouter(prefix="/api/intake", tags=["Project Intake Wizard"])


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

class ProjectIntakeCreate(BaseModel):
    """Schema for creating a new project intake."""
    name: str = Field(..., min_length=1, max_length=255)
    traject_type: str = Field(..., description="brown_paper, green_paper, or migration")
    organization: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    description: Optional[str] = None

    @field_validator('traject_type')
    @classmethod
    def validate_traject_type(cls, v):
        if v not in TrajectType.all():
            raise ValueError(f"traject_type must be one of {TrajectType.all()}")
        return v


class ProjectIntakeUpdate(BaseModel):
    """Schema for updating a project intake."""
    name: Optional[str] = None
    organization: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    description: Optional[str] = None
    migration_type: Optional[str] = None
    target_stack: Optional[Dict[str, Any]] = None
    target_architecture: Optional[str] = None
    start_date: Optional[date] = None
    target_go_live: Optional[date] = None
    hard_deadline: Optional[bool] = None
    migration_strategy: Optional[str] = None
    parallel_run_weeks: Optional[int] = None


class BrownPaperScopeCreate(BaseModel):
    """Schema for configuring Brown Paper analysis scope."""
    analyze_functionality: bool = True
    analyze_quality: bool = True
    analyze_security: bool = True
    analyze_tech_debt: bool = True
    analyze_performance: bool = False
    analyze_database: bool = False
    analyze_integrations: bool = False
    analyze_documentation: bool = False
    tier: str = "standard"
    expected_outcome: Optional[str] = None
    system_path: Optional[str] = None
    repository_url: Optional[str] = None
    branch: str = "main"
    has_local_files: bool = True
    has_database_access: bool = False

    @field_validator('tier')
    @classmethod
    def validate_tier(cls, v):
        if v not in AnalysisTier.all():
            raise ValueError(f"tier must be one of {AnalysisTier.all()}")
        return v

    @field_validator('expected_outcome')
    @classmethod
    def validate_expected_outcome(cls, v):
        if v and v not in ExpectedOutcome.all():
            raise ValueError(f"expected_outcome must be one of {ExpectedOutcome.all()}")
        return v


class BrownPaperDecisionRequest(BaseModel):
    """Schema for recording Brown Paper decision."""
    decision: str = Field(..., description="report_only, maintenance, or migration")
    decision_notes: Optional[str] = None
    decision_by: Optional[str] = None

    @field_validator('decision')
    @classmethod
    def validate_decision(cls, v):
        if v not in BrownPaperDecision.all():
            raise ValueError(f"decision must be one of {BrownPaperDecision.all()}")
        return v


class MigrationSourceAdd(BaseModel):
    """Schema for adding a source to a migration."""
    brown_paper_session_id: str
    display_order: int = 0


class IntegrationConfigUpdate(BaseModel):
    """Schema for configuring an integration."""
    action: str = Field(..., description="include, library, or exclude")
    library_name: Optional[str] = None
    library_type: Optional[str] = None
    decision_notes: Optional[str] = None

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        if v not in IntegrationAction.all():
            raise ValueError(f"action must be one of {IntegrationAction.all()}")
        return v


class MigrationTargetConfig(BaseModel):
    """Schema for configuring migration target."""
    target_stack: Dict[str, Any] = Field(..., description="e.g., {backend: '.NET 8', frontend: 'Vue.js', database: 'SQL Server'}")
    target_architecture: str = Field(..., description="e.g., 'Clean Architecture', 'DDD'")


class MigrationStrategyConfig(BaseModel):
    """Schema for configuring migration strategy."""
    migration_strategy: str = Field(..., description="big_bang, module_by_module, or strangler_fig")
    parallel_run_weeks: Optional[int] = None
    start_date: Optional[date] = None
    target_go_live: Optional[date] = None
    hard_deadline: bool = False

    @field_validator('migration_strategy')
    @classmethod
    def validate_strategy(cls, v):
        if v not in MigrationStrategy.all():
            raise ValueError(f"migration_strategy must be one of {MigrationStrategy.all()}")
        return v


class GreenPaperFeaturesUpdate(BaseModel):
    """Schema for updating Green Paper features."""
    features: List[str] = Field(..., description="List of feature names to enable")


class ProjectIntakeResponse(BaseModel):
    """Response schema for project intake."""
    id: str
    name: str
    organization: Optional[str]
    contact_person: Optional[str]
    contact_email: Optional[str]
    description: Optional[str]
    traject_type: str
    migration_type: Optional[str]
    target_stack: Optional[Dict[str, Any]]
    target_architecture: Optional[str]
    start_date: Optional[str]
    target_go_live: Optional[str]
    hard_deadline: bool
    migration_strategy: Optional[str]
    parallel_run_weeks: Optional[int]
    brown_paper_decision: Optional[str]
    decision_date: Optional[str]
    decision_by: Optional[str]
    decision_notes: Optional[str]
    follow_up_migration_id: Optional[str]
    status: str
    generated_project_id: Optional[int]
    generated_kanban_items: Optional[int]
    generated_requirements: Optional[int]
    analysis_results: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str
    completed_at: Optional[str]
    created_by: Optional[str]
    # Computed
    is_brown_paper: bool
    is_green_paper: bool
    is_migration: bool
    can_start_analysis: bool
    can_make_decision: bool
    can_start_migration: bool
    source_count: int
    integration_count: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

async def get_intake_or_404(db: AsyncSession, intake_id: UUID) -> ProjectIntake:
    """Get intake by ID or raise 404."""
    result = await db.execute(
        select(ProjectIntake)
        .options(
            selectinload(ProjectIntake.sources),
            selectinload(ProjectIntake.integrations),
            selectinload(ProjectIntake.scope),
            selectinload(ProjectIntake.features),
        )
        .where(ProjectIntake.id == intake_id)
    )
    intake = result.scalar_one_or_none()
    if not intake:
        raise HTTPException(status_code=404, detail=f"Project intake {intake_id} not found")
    return intake


async def add_intake_event(
    db: AsyncSession,
    intake_id: UUID,
    event_type: str,
    event_data: Optional[Dict] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    created_by: Optional[str] = None
):
    """Add an event to the intake audit trail."""
    event = ProjectIntakeEvent(
        intake_id=intake_id,
        event_type=event_type,
        event_data=event_data,
        old_value=old_value,
        new_value=new_value,
        created_by=created_by,
    )
    db.add(event)


# ============================================================
# ENDPOINTS: Intake Management
# ============================================================

@router.get("/traject-types")
async def get_traject_types():
    """Get available traject types."""
    return {
        "traject_types": [
            {"code": "brown_paper", "name": "Brown Paper", "description": "Discovery bestaand systeem"},
            {"code": "green_paper", "name": "Green Paper", "description": "Nieuw project vanaf scratch"},
            {"code": "migration", "name": "Migratie", "description": "Transformatie (vereist Brown Paper)"},
        ]
    }


@router.get("/migration-types")
async def get_migration_types():
    """Get available migration types."""
    return {
        "migration_types": [
            {"code": "modernize", "name": "Moderniseren", "description": "Enkele applicatie moderniseren"},
            {"code": "consolidate", "name": "Samenvoegen", "description": "Meerdere applicaties samenvoegen"},
            {"code": "hybrid", "name": "Hybride", "description": "Functionaliteit lenen tussen applicaties"},
        ]
    }


@router.get("/analysis-tiers")
async def get_analysis_tiers():
    """Get available analysis tiers."""
    return {
        "tiers": [
            {"code": "free", "name": "Quick Scan", "duration": "5-15 minuten", "description": "Basis statistieken, top 10 issues"},
            {"code": "standard", "name": "Standard", "duration": "30-60 minuten", "description": "Volledige inventarisatie, alle issues"},
            {"code": "premium", "name": "Deep Dive", "duration": "2-4 uur", "description": "Alles + data flow, dependency graphs, AI recommendations"},
        ]
    }


@router.get("/predefined-features")
async def get_predefined_features():
    """Get predefined features for Green Paper."""
    return {
        "features": PREDEFINED_FEATURES,
        "categories": ["core", "domain", "integration"]
    }


@router.get("/projects")
async def list_intakes(
    traject_type: Optional[str] = None,
    status: Optional[str] = None,
    organization: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all project intakes with optional filters."""
    query = select(ProjectIntake).options(
        selectinload(ProjectIntake.sources),
        selectinload(ProjectIntake.integrations),
    )

    # Apply filters
    conditions = []
    if traject_type:
        conditions.append(ProjectIntake.traject_type == traject_type)
    if status:
        conditions.append(ProjectIntake.status == status)
    if organization:
        conditions.append(ProjectIntake.organization.ilike(f"%{organization}%"))

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(ProjectIntake.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    intakes = result.scalars().all()

    return {
        "intakes": [intake.to_summary_dict() for intake in intakes],
        "total": len(intakes),
        "offset": offset,
        "limit": limit,
    }


@router.post("/projects")
async def create_intake(
    request: ProjectIntakeCreate,
    created_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Create a new project intake."""
    intake = ProjectIntake(
        name=request.name,
        traject_type=request.traject_type,
        organization=request.organization,
        contact_person=request.contact_person,
        contact_email=request.contact_email,
        description=request.description,
        status=IntakeStatus.DRAFT,
        created_by=created_by,
    )
    db.add(intake)
    await db.flush()  # Flush to get the intake.id

    # Add creation event
    await add_intake_event(
        db, intake.id, IntakeEventType.CREATED,
        event_data={"traject_type": request.traject_type},
        created_by=created_by
    )

    # If Green Paper, initialize predefined features
    if request.traject_type == TrajectType.GREEN_PAPER:
        for feat in PREDEFINED_FEATURES:
            feature = ProjectIntakeFeature(
                intake_id=intake.id,
                feature_name=feat["name"],
                feature_category=feat["category"],
                enabled=False,
                display_order=feat["order"],
            )
            db.add(feature)

    await db.commit()
    # Reload with relationships to avoid lazy loading in async context
    intake = await get_intake_or_404(db, intake.id)

    return intake.to_dict()


@router.get("/projects/{intake_id}")
async def get_intake(
    intake_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get project intake details."""
    intake = await get_intake_or_404(db, intake_id)
    response = intake.to_dict()

    # Add related data
    if intake.scope:
        response["scope"] = intake.scope.to_dict()
    if intake.sources:
        response["sources"] = [s.to_dict() for s in intake.sources]
    if intake.integrations:
        response["integrations"] = [i.to_dict() for i in intake.integrations]
    if intake.features:
        response["features"] = [f.to_dict() for f in intake.features]

    return response


@router.put("/projects/{intake_id}")
async def update_intake(
    intake_id: UUID,
    request: ProjectIntakeUpdate,
    updated_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Update project intake."""
    intake = await get_intake_or_404(db, intake_id)

    # Update fields if provided
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(intake, field):
            setattr(intake, field, value)

    intake.updated_at = datetime.now(timezone.utc)
    intake.last_modified_by = updated_by

    await db.commit()
    # Reload with relationships to avoid lazy loading in async context
    intake = await get_intake_or_404(db, intake_id)

    return intake.to_dict()


@router.delete("/projects/{intake_id}")
async def delete_intake(
    intake_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete project intake (only drafts)."""
    intake = await get_intake_or_404(db, intake_id)

    if intake.status != IntakeStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Only draft intakes can be deleted"
        )

    await db.delete(intake)
    await db.commit()

    return {"message": f"Project intake {intake_id} deleted"}


# ============================================================
# ENDPOINTS: Brown Paper Specific
# ============================================================

@router.put("/projects/{intake_id}/brown-paper/scope")
async def configure_brown_paper_scope(
    intake_id: UUID,
    request: BrownPaperScopeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Configure Brown Paper analysis scope."""
    intake = await get_intake_or_404(db, intake_id)

    if intake.traject_type != TrajectType.BROWN_PAPER:
        raise HTTPException(
            status_code=400,
            detail="Scope configuration is only for Brown Paper intakes"
        )

    # Create or update scope
    if intake.scope:
        scope = intake.scope
        for field, value in request.model_dump().items():
            setattr(scope, field, value)
        scope.updated_at = datetime.now(timezone.utc)
    else:
        scope = ProjectIntakeScope(
            intake_id=intake_id,
            **request.model_dump()
        )
        db.add(scope)

    await add_intake_event(
        db, intake_id, IntakeEventType.SCOPE_CONFIGURED,
        event_data=request.model_dump()
    )

    await db.commit()
    await db.refresh(scope)

    return scope.to_dict()


@router.post("/projects/{intake_id}/brown-paper/start")
async def start_brown_paper_analysis(
    intake_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start Brown Paper analysis (async)."""
    intake = await get_intake_or_404(db, intake_id)

    if not intake.can_start_analysis:
        raise HTTPException(
            status_code=400,
            detail="Cannot start analysis. Check traject_type is brown_paper, status is draft/active, and scope is configured."
        )

    # Update status
    old_status = intake.status
    intake.status = IntakeStatus.ANALYZING
    intake.updated_at = datetime.now(timezone.utc)

    await add_intake_event(
        db, intake_id, IntakeEventType.ANALYSIS_STARTED,
        old_value=old_status,
        new_value=IntakeStatus.ANALYZING
    )

    await db.commit()

    # TODO: Trigger actual Brown Paper analysis in background
    # background_tasks.add_task(run_brown_paper_analysis, intake_id, intake.scope)

    return {
        "message": "Brown Paper analysis started",
        "intake_id": str(intake_id),
        "status": intake.status,
    }


@router.post("/projects/{intake_id}/brown-paper/decision")
async def record_brown_paper_decision(
    intake_id: UUID,
    request: BrownPaperDecisionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Record Brown Paper decision after analysis."""
    intake = await get_intake_or_404(db, intake_id)

    if not intake.can_make_decision:
        raise HTTPException(
            status_code=400,
            detail="Cannot make decision. Intake must be Brown Paper and status must be awaiting_decision."
        )

    # Record decision
    intake.brown_paper_decision = request.decision
    intake.decision_date = datetime.now(timezone.utc)
    intake.decision_by = request.decision_by
    intake.decision_notes = request.decision_notes
    intake.status = IntakeStatus.COMPLETED
    intake.completed_at = datetime.now(timezone.utc)

    await add_intake_event(
        db, intake_id, IntakeEventType.DECISION_MADE,
        event_data={"decision": request.decision, "notes": request.decision_notes},
        new_value=request.decision
    )

    # If decision is migration, create follow-up migration intake
    follow_up_id = None
    if request.decision == BrownPaperDecision.MIGRATION:
        migration_intake = ProjectIntake(
            name=f"{intake.name} - Migratie",
            traject_type=TrajectType.MIGRATION,
            organization=intake.organization,
            contact_person=intake.contact_person,
            contact_email=intake.contact_email,
            description=f"Migratie traject voortkomend uit Brown Paper: {intake.name}",
            status=IntakeStatus.DRAFT,
            created_by=request.decision_by,
        )
        db.add(migration_intake)
        await db.flush()

        # Link source
        source = ProjectIntakeSource(
            intake_id=migration_intake.id,
            system_name=intake.name,
            system_path=intake.scope.system_path if intake.scope else None,
            repository_url=intake.scope.repository_url if intake.scope else None,
            analysis_summary=intake.analysis_results,
        )
        db.add(source)

        intake.follow_up_migration_id = migration_intake.id
        follow_up_id = str(migration_intake.id)

    await db.commit()

    return {
        "message": f"Decision recorded: {request.decision}",
        "intake_id": str(intake_id),
        "decision": request.decision,
        "follow_up_migration_id": follow_up_id,
    }


# ============================================================
# ENDPOINTS: Green Paper Specific
# ============================================================

@router.put("/projects/{intake_id}/green-paper/stack")
async def configure_green_paper_stack(
    intake_id: UUID,
    request: MigrationTargetConfig,
    db: AsyncSession = Depends(get_db),
):
    """Configure target stack for Green Paper."""
    intake = await get_intake_or_404(db, intake_id)

    if intake.traject_type != TrajectType.GREEN_PAPER:
        raise HTTPException(
            status_code=400,
            detail="Stack configuration via this endpoint is only for Green Paper intakes"
        )

    intake.target_stack = request.target_stack
    intake.target_architecture = request.target_architecture
    intake.updated_at = datetime.now(timezone.utc)

    await add_intake_event(
        db, intake_id, IntakeEventType.TARGET_CONFIGURED,
        event_data={"stack": request.target_stack, "architecture": request.target_architecture}
    )

    await db.commit()

    return {"message": "Stack configured", "target_stack": intake.target_stack}


@router.put("/projects/{intake_id}/green-paper/features")
async def update_green_paper_features(
    intake_id: UUID,
    request: GreenPaperFeaturesUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update enabled features for Green Paper."""
    intake = await get_intake_or_404(db, intake_id)

    if intake.traject_type != TrajectType.GREEN_PAPER:
        raise HTTPException(
            status_code=400,
            detail="Feature selection is only for Green Paper intakes"
        )

    # Update features
    for feature in intake.features:
        feature.enabled = feature.feature_name in request.features

    await add_intake_event(
        db, intake_id, IntakeEventType.TARGET_CONFIGURED,
        event_data={"enabled_features": request.features}
    )

    await db.commit()

    enabled = [f.to_dict() for f in intake.features if f.enabled]
    return {
        "message": f"Enabled {len(enabled)} features",
        "enabled_features": enabled,
    }


@router.post("/projects/{intake_id}/green-paper/generate")
async def generate_green_paper_project(
    intake_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Generate project structure and backlog for Green Paper."""
    intake = await get_intake_or_404(db, intake_id)

    if intake.traject_type != TrajectType.GREEN_PAPER:
        raise HTTPException(status_code=400, detail="Only for Green Paper intakes")

    if not intake.target_stack:
        raise HTTPException(status_code=400, detail="Target stack must be configured first")

    # Update status
    intake.status = IntakeStatus.ACTIVE
    intake.updated_at = datetime.now(timezone.utc)

    # TODO: Trigger project generation in background
    # background_tasks.add_task(generate_project_from_green_paper, intake_id)

    await db.commit()

    return {
        "message": "Project generation started",
        "intake_id": str(intake_id),
    }


# ============================================================
# ENDPOINTS: Migration Specific
# ============================================================

@router.get("/projects/{intake_id}/migration/available-sources")
async def get_available_migration_sources(
    intake_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get available Brown Paper sessions that can be used as migration sources."""
    intake = await get_intake_or_404(db, intake_id)

    if intake.traject_type != TrajectType.MIGRATION:
        raise HTTPException(status_code=400, detail="Only for Migration intakes")

    # Get completed Brown Paper sessions
    result = await db.execute(
        select(BMADSession)
        .where(BMADSession.workflow_type == "brown_paper")
        .where(BMADSession.status.in_(["approved", "completed", "review"]))
        .order_by(BMADSession.created_at.desc())
    )
    sessions = result.scalars().all()

    # Get already added source IDs
    existing_ids = {s.brown_paper_session_id for s in intake.sources}

    return {
        "available_sources": [
            {
                "id": s.id,
                "project_name": s.project_name,
                "project_path": s.project_path,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "already_added": s.id in existing_ids,
            }
            for s in sessions
        ]
    }


@router.put("/projects/{intake_id}/migration/type")
async def set_migration_type(
    intake_id: UUID,
    migration_type: str = Query(..., description="modernize, consolidate, or hybrid"),
    db: AsyncSession = Depends(get_db),
):
    """Set migration type."""
    intake = await get_intake_or_404(db, intake_id)

    if intake.traject_type != TrajectType.MIGRATION:
        raise HTTPException(status_code=400, detail="Only for Migration intakes")

    if migration_type not in MigrationType.all():
        raise HTTPException(status_code=400, detail=f"migration_type must be one of {MigrationType.all()}")

    old_value = intake.migration_type
    intake.migration_type = migration_type
    intake.updated_at = datetime.now(timezone.utc)

    await add_intake_event(
        db, intake_id, IntakeEventType.STATUS_CHANGED,
        old_value=old_value,
        new_value=migration_type,
        event_data={"field": "migration_type"}
    )

    await db.commit()

    return {"message": f"Migration type set to {migration_type}"}


@router.post("/projects/{intake_id}/migration/sources")
async def add_migration_source(
    intake_id: UUID,
    request: MigrationSourceAdd,
    db: AsyncSession = Depends(get_db),
):
    """Add a Brown Paper session as source for migration."""
    intake = await get_intake_or_404(db, intake_id)

    if intake.traject_type != TrajectType.MIGRATION:
        raise HTTPException(status_code=400, detail="Only for Migration intakes")

    # Check if Brown Paper session exists
    result = await db.execute(
        select(BMADSession).where(BMADSession.id == request.brown_paper_session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Brown Paper session not found")

    # Check if already added
    existing = [s for s in intake.sources if s.brown_paper_session_id == request.brown_paper_session_id]
    if existing:
        raise HTTPException(status_code=400, detail="Source already added")

    # Create source
    source = ProjectIntakeSource(
        intake_id=intake_id,
        brown_paper_session_id=request.brown_paper_session_id,
        system_name=session.project_name,
        system_path=session.project_path,
        analysis_summary=session.enhanced_analysis or session.migration_analysis,
        display_order=request.display_order,
    )
    db.add(source)

    await add_intake_event(
        db, intake_id, IntakeEventType.SOURCES_ADDED,
        event_data={"source": session.project_name, "session_id": request.brown_paper_session_id}
    )

    await db.commit()
    await db.refresh(source)

    return source.to_dict()


@router.delete("/projects/{intake_id}/migration/sources/{source_id}")
async def remove_migration_source(
    intake_id: UUID,
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove a source from migration."""
    intake = await get_intake_or_404(db, intake_id)

    source = next((s for s in intake.sources if s.id == source_id), None)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    await db.delete(source)
    await db.commit()

    return {"message": "Source removed"}


@router.put("/projects/{intake_id}/migration/target")
async def configure_migration_target(
    intake_id: UUID,
    request: MigrationTargetConfig,
    db: AsyncSession = Depends(get_db),
):
    """Configure target stack and architecture for migration."""
    intake = await get_intake_or_404(db, intake_id)

    if intake.traject_type != TrajectType.MIGRATION:
        raise HTTPException(status_code=400, detail="Only for Migration intakes")

    intake.target_stack = request.target_stack
    intake.target_architecture = request.target_architecture
    intake.updated_at = datetime.now(timezone.utc)

    await add_intake_event(
        db, intake_id, IntakeEventType.TARGET_CONFIGURED,
        event_data={"stack": request.target_stack, "architecture": request.target_architecture}
    )

    await db.commit()

    return {"message": "Target configured", "target_stack": intake.target_stack}


@router.put("/projects/{intake_id}/migration/strategy")
async def configure_migration_strategy(
    intake_id: UUID,
    request: MigrationStrategyConfig,
    db: AsyncSession = Depends(get_db),
):
    """Configure migration strategy and timeline."""
    intake = await get_intake_or_404(db, intake_id)

    if intake.traject_type != TrajectType.MIGRATION:
        raise HTTPException(status_code=400, detail="Only for Migration intakes")

    intake.migration_strategy = request.migration_strategy
    intake.parallel_run_weeks = request.parallel_run_weeks
    intake.start_date = request.start_date
    intake.target_go_live = request.target_go_live
    intake.hard_deadline = request.hard_deadline
    intake.updated_at = datetime.now(timezone.utc)

    await add_intake_event(
        db, intake_id, IntakeEventType.TARGET_CONFIGURED,
        event_data=request.model_dump()
    )

    await db.commit()

    return {"message": "Strategy configured"}


@router.get("/projects/{intake_id}/migration/integrations")
async def get_migration_integrations(
    intake_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all integrations discovered from sources."""
    intake = await get_intake_or_404(db, intake_id)

    if intake.traject_type != TrajectType.MIGRATION:
        raise HTTPException(status_code=400, detail="Only for Migration intakes")

    return {
        "integrations": [i.to_dict() for i in intake.integrations],
        "total": len(intake.integrations),
    }


@router.put("/projects/{intake_id}/migration/integrations/{integration_id}")
async def configure_integration(
    intake_id: UUID,
    integration_id: UUID,
    request: IntegrationConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Configure how an integration should be handled."""
    intake = await get_intake_or_404(db, intake_id)

    integration = next((i for i in intake.integrations if i.id == integration_id), None)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    integration.action = request.action
    integration.library_name = request.library_name
    integration.library_type = request.library_type
    integration.decision_notes = request.decision_notes
    integration.updated_at = datetime.now(timezone.utc)

    await add_intake_event(
        db, intake_id, IntakeEventType.INTEGRATIONS_CONFIGURED,
        event_data={"integration": integration.integration_name, "action": request.action}
    )

    await db.commit()

    return integration.to_dict()


@router.post("/projects/{intake_id}/migration/start")
async def start_migration_project(
    intake_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start migration project (creates project, imports requirements, generates backlog)."""
    intake = await get_intake_or_404(db, intake_id)

    if not intake.can_start_migration:
        raise HTTPException(
            status_code=400,
            detail="Cannot start migration. Check traject_type is migration, status is active, and sources are added."
        )

    if not intake.target_stack:
        raise HTTPException(status_code=400, detail="Target stack must be configured first")

    if not intake.migration_strategy:
        raise HTTPException(status_code=400, detail="Migration strategy must be configured first")

    # Update status
    intake.status = IntakeStatus.ACTIVE
    intake.updated_at = datetime.now(timezone.utc)

    await add_intake_event(
        db, intake_id, IntakeEventType.MIGRATION_STARTED,
        event_data={
            "sources": [s.system_name for s in intake.sources],
            "target_stack": intake.target_stack,
            "strategy": intake.migration_strategy,
        }
    )

    # TODO: Trigger migration project creation in background
    # background_tasks.add_task(create_migration_project, intake_id)

    await db.commit()

    return {
        "message": "Migration project started",
        "intake_id": str(intake_id),
        "sources": [s.system_name for s in intake.sources],
    }


# ============================================================
# ENDPOINTS: Events & History
# ============================================================

@router.get("/projects/{intake_id}/events")
async def get_intake_events(
    intake_id: UUID,
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get event history for an intake."""
    intake = await get_intake_or_404(db, intake_id)

    result = await db.execute(
        select(ProjectIntakeEvent)
        .where(ProjectIntakeEvent.intake_id == intake_id)
        .order_by(ProjectIntakeEvent.created_at.desc())
        .limit(limit)
    )
    events = result.scalars().all()

    return {
        "events": [e.to_dict() for e in events],
        "total": len(events),
    }
