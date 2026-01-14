# Migration API v2
# Decoupled migration endpoints using AnalysisContract
#
# Key change: Uses analysis_id instead of brown_paper_session_id
#
# Endpoints:
# - POST /api/v2/migration/contracts/from-brown-paper - Create contract from Brown Paper
# - POST /api/v2/migration/start - Start migration with analysis_id
# - GET /api/v2/migration/contracts/{analysis_id} - Get contract details
# - GET /api/v2/migration/context/{analysis_id} - Get migration context
#
# Architecture: docs/architecture/workflow-separation-plan.md
# Phase: Fase 21.5 (Week 145-146)

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...database import get_db
from ...contracts import AnalysisContract, AnalysisSourceType
from ...domains.brown_paper import BrownPaperContractAdapter
from ...domains.migration import AnalysisContractConsumer
from ...domains.contracts.repository import ContractRepository
from ...models.brown_paper import BrownPaperSession, BrownPaperAnalysis, BrownPaperConstitution

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/migration", tags=["Migration v2"])


# === Request/Response Models ===

class CreateContractFromBrownPaperRequest(BaseModel):
    """Request to create an AnalysisContract from a Brown Paper session."""
    brown_paper_session_id: str = Field(..., description="Brown Paper session ID")
    include_stability: bool = Field(default=True, description="Include stability analysis")


class CreateContractResponse(BaseModel):
    """Response after creating a contract."""
    analysis_id: str
    source_type: str
    source_id: Optional[str]
    project_name: str
    project_path: str
    total_domains: int
    total_modules: int
    total_epics: int
    created_at: datetime
    is_valid_for_migration: bool
    validation_issues: List[str]


class StartMigrationRequest(BaseModel):
    """Request to start migration using an analysis contract."""
    analysis_id: str = Field(..., description="Analysis contract ID (NOT brown_paper_session_id)")
    target_stack: Optional[str] = Field(default=None, description="Target technology stack")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Migration options")


class StartMigrationResponse(BaseModel):
    """Response after starting migration."""
    migration_id: str
    analysis_id: str
    status: str
    risk_level: str
    estimated_weeks: float
    phases: List[Dict[str, Any]]
    message: str


class MigrationContextResponse(BaseModel):
    """Migration context derived from analysis contract."""
    analysis_id: str
    project_name: str
    project_path: str
    total_domains: int
    total_modules: int
    total_epics: int
    overall_risk_level: str
    stability_score: int
    risks: List[Dict[str, Any]]
    domain_priority: List[str]
    phases: List[Dict[str, Any]]


class ContractSummary(BaseModel):
    """Summary of an analysis contract."""
    analysis_id: str
    source_type: str
    project_name: str
    total_domains: int
    total_epics: int
    stability_score: int
    created_at: datetime


# === Endpoints ===

@router.post("/contracts/from-brown-paper", response_model=CreateContractResponse)
async def create_contract_from_brown_paper(
    request: CreateContractFromBrownPaperRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create an AnalysisContract from a Brown Paper session.

    This is the bridge between Brown Paper (analysis) and Migration (execution).
    The returned analysis_id should be used for all subsequent migration operations.
    """
    logger.info(f"Creating contract from Brown Paper session: {request.brown_paper_session_id}")

    try:
        # Load Brown Paper session with relations
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(BrownPaperSession)
            .options(
                selectinload(BrownPaperSession.analysis),
                selectinload(BrownPaperSession.constitution).selectinload(BrownPaperConstitution.epics)
            )
            .where(BrownPaperSession.id == request.brown_paper_session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Brown Paper session not found: {request.brown_paper_session_id}"
            )

        # Create contract using adapter
        adapter = BrownPaperContractAdapter()
        contract = adapter.to_contract(
            session=session,
            analysis=session.analysis,
            constitution=session.constitution,
            stability_result=None,  # TODO: Load stability result if available
        )

        # Save contract to database
        repo = ContractRepository(db)
        repo.save(contract)

        # Validate for migration
        is_valid, issues = contract.validate_for_migration()

        logger.info(f"Created contract {contract.analysis_id} from Brown Paper {request.brown_paper_session_id}")

        return CreateContractResponse(
            analysis_id=contract.analysis_id,
            source_type=contract.source_type.value,
            source_id=contract.source_id,
            project_name=contract.project.name,
            project_path=contract.project.path,
            total_domains=contract.total_domains,
            total_modules=contract.total_modules,
            total_epics=contract.total_epics,
            created_at=contract.created_at,
            is_valid_for_migration=is_valid,
            validation_issues=issues,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating contract: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start", response_model=StartMigrationResponse)
async def start_migration(
    request: StartMigrationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Start a migration using an analysis contract.

    IMPORTANT: Use analysis_id from /contracts/from-brown-paper, NOT brown_paper_session_id.
    """
    logger.info(f"Starting migration with analysis_id: {request.analysis_id}")

    try:
        # Load contract from database
        repo = ContractRepository(db)
        contract = repo.get_by_id(request.analysis_id)

        if not contract:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis contract not found: {request.analysis_id}"
            )

        # Validate contract
        is_valid, issues = contract.validate_for_migration()
        if not is_valid:
            # Filter out warnings
            errors = [i for i in issues if not i.startswith("Warning")]
            if errors:
                raise HTTPException(
                    status_code=400,
                    detail=f"Contract not valid for migration: {', '.join(errors)}"
                )

        # Create migration context
        consumer = AnalysisContractConsumer()
        context = consumer.consume(contract)

        # Generate migration ID
        import uuid
        migration_id = str(uuid.uuid4())

        # TODO: Store migration session in database
        # TODO: Trigger actual migration workflow

        logger.info(f"Started migration {migration_id} from contract {request.analysis_id}")

        return StartMigrationResponse(
            migration_id=migration_id,
            analysis_id=request.analysis_id,
            status="started",
            risk_level=context.overall_risk_level,
            estimated_weeks=context.estimated_weeks,
            phases=[p.to_dict() if hasattr(p, 'to_dict') else {
                "phase_number": p.phase_number,
                "name": p.name,
                "description": p.description,
                "estimated_hours": p.estimated_hours,
            } for p in context.phases],
            message=f"Migration started with {len(context.phases)} phases",
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting migration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/{analysis_id}", response_model=Dict[str, Any])
async def get_contract(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get an analysis contract by ID."""
    repo = ContractRepository(db)
    contract = repo.get_by_id(analysis_id)

    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract not found: {analysis_id}")

    return contract.to_dict()


@router.get("/context/{analysis_id}", response_model=MigrationContextResponse)
async def get_migration_context(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get migration context for an analysis contract.

    Returns risk assessment, domain priorities, and phase configuration.
    """
    repo = ContractRepository(db)
    contract = repo.get_by_id(analysis_id)

    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract not found: {analysis_id}")

    # Create migration context
    consumer = AnalysisContractConsumer()

    try:
        context = consumer.consume(contract)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return MigrationContextResponse(
        analysis_id=context.analysis_id,
        project_name=context.project_name,
        project_path=context.project_path,
        total_domains=context.total_domains,
        total_modules=context.total_modules,
        total_epics=context.total_epics,
        overall_risk_level=context.overall_risk_level,
        stability_score=context.stability_score,
        risks=[{
            "category": r.category,
            "severity": r.severity,
            "description": r.description,
            "mitigation": r.mitigation,
        } for r in context.risks],
        domain_priority=context.domain_priority,
        phases=[{
            "phase_number": p.phase_number,
            "name": p.name,
            "description": p.description,
            "estimated_hours": p.estimated_hours,
        } for p in context.phases],
    )


@router.get("/contracts", response_model=List[ContractSummary])
async def list_contracts(
    project_id: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List analysis contracts, optionally filtered by project."""
    repo = ContractRepository(db)

    if project_id:
        contracts = repo.list_by_project(project_id, limit=limit)
    else:
        # List recent contracts (would need a method for this)
        contracts = []

    return [
        ContractSummary(
            analysis_id=c.analysis_id,
            source_type=c.source_type.value,
            project_name=c.project.name,
            total_domains=c.total_domains,
            total_epics=c.total_epics,
            stability_score=c.stability.overall_score,
            created_at=c.created_at,
        )
        for c in contracts
    ]


# === Legacy Compatibility ===

@router.post("/start/legacy", deprecated=True)
async def start_migration_legacy(
    brown_paper_session_id: str,
    target_stack: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    DEPRECATED: Start migration using brown_paper_session_id.

    Use /contracts/from-brown-paper followed by /start instead.
    This endpoint auto-creates a contract for backwards compatibility.
    """
    logger.warning(f"Using deprecated legacy endpoint for session {brown_paper_session_id}")

    # Create contract first
    contract_response = await create_contract_from_brown_paper(
        CreateContractFromBrownPaperRequest(brown_paper_session_id=brown_paper_session_id),
        db=db,
    )

    # Then start migration
    return await start_migration(
        StartMigrationRequest(
            analysis_id=contract_response.analysis_id,
            target_stack=target_stack,
        ),
        db=db,
    )
