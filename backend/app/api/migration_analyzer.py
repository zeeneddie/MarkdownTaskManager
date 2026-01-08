"""
MigrationAnalyzer API Routes

Week 65: MigrationAnalyzer Multi-Agent System
REST API endpoints for legacy code and database migration analysis.

Endpoints:
- POST /api/migration/analyze - Start new analysis
- GET /api/migration/analyses - List analyses
- GET /api/migration/analyses/{id} - Get analysis details
- POST /api/migration/analyses/{id}/run - Execute analysis
- GET /api/migration/analyses/{id}/modules - Get modules
- GET /api/migration/analyses/{id}/patterns - Get patterns
- GET /api/migration/analyses/{id}/recommendations - Get recommendations
- GET /api/migration/analyses/{id}/risks - Get risk assessments

Author: Claude Code (Week 65)
Date: 2025-12-12
"""

from uuid import UUID
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.migration_analyzer_service import (
    MigrationAnalyzerService,
    get_migration_analyzer_service
)

router = APIRouter(prefix="/api/migration", tags=["migration-analyzer"])


# ========== Pydantic Models ==========

class AnalysisCreateRequest(BaseModel):
    """Request to create a new migration analysis"""
    repo_path: str = Field(..., description="Path to the repository to analyze")
    target_stack: Optional[str] = Field(None, description="Target technology stack (e.g., 'dotnet8', 'python')")
    target_db: Optional[str] = Field("postgresql", description="Target database (default: postgresql)")
    project_id: Optional[int] = Field(None, description="Optional project ID to link analysis to")


class AnalysisResponse(BaseModel):
    """Analysis response model"""
    id: str
    repo_path: str
    repo_name: Optional[str]
    source_stack: Optional[str]
    secondary_stacks: Optional[List[str]]
    target_stack: Optional[str]
    target_db: Optional[str]
    total_files: Optional[int]
    total_loc: Optional[int]
    total_modules: Optional[int]
    estimated_fp: Optional[int]
    complexity_score: Optional[float]
    risk_score: Optional[float]
    db_type: Optional[str]
    db_migration_difficulty: Optional[str]
    db_estimated_days: Optional[float]
    status: str
    current_phase: Optional[str]
    progress_percent: int
    error_message: Optional[str]
    created_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class ModuleResponse(BaseModel):
    """Module response model"""
    id: str
    name: str
    module_type: Optional[str]
    stack_type: Optional[str]
    file_path: Optional[str]
    loc: Optional[int]
    estimated_fp: Optional[int]
    migration_difficulty: Optional[str]
    pattern_count: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class PatternResponse(BaseModel):
    """Pattern response model"""
    id: str
    pattern_name: str
    pattern_category: Optional[str]
    file_path: Optional[str]
    line_number: Optional[int]
    risk_level: Optional[str]
    is_security_issue: bool
    migration_note: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseModel):
    """Recommendation response model"""
    id: str
    category: str
    priority: Optional[str]
    title: str
    description: Optional[str]
    source_agent: Optional[str]
    estimated_effort: Optional[str]
    status: str

    model_config = ConfigDict(from_attributes=True)


class RiskResponse(BaseModel):
    """Risk assessment response model"""
    id: str
    risk_id: Optional[str]
    title: str
    category: Optional[str]
    probability: Optional[int]
    impact: Optional[int]
    risk_score: Optional[int]
    status: str
    mitigation_strategy: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class AnalysisSummaryResponse(BaseModel):
    """Summary response for analysis"""
    id: str
    repo_name: Optional[str]
    source_stack: Optional[str]
    status: str
    progress_percent: int
    total_modules: Optional[int]
    estimated_fp: Optional[int]
    complexity_score: Optional[float]
    created_at: Optional[str]


# ========== API Endpoints ==========

@router.post("/analyze", response_model=AnalysisResponse)
async def create_analysis(
    request: AnalysisCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> AnalysisResponse:
    """
    Create a new migration analysis

    Creates an analysis record and optionally starts execution in background.
    """
    service = get_migration_analyzer_service(db)

    try:
        analysis = await service.create_analysis(
            repo_path=request.repo_path,
            target_stack=request.target_stack,
            target_db=request.target_db,
            project_id=request.project_id
        )

        return AnalysisResponse(
            id=str(analysis.id),
            repo_path=analysis.repo_path,
            repo_name=analysis.repo_name,
            source_stack=analysis.source_stack,
            secondary_stacks=analysis.secondary_stacks,
            target_stack=analysis.target_stack,
            target_db=analysis.target_db,
            total_files=analysis.total_files,
            total_loc=analysis.total_loc,
            total_modules=analysis.total_modules,
            estimated_fp=analysis.estimated_fp,
            complexity_score=analysis.complexity_score,
            risk_score=analysis.risk_score,
            db_type=analysis.db_type,
            db_migration_difficulty=analysis.db_migration_difficulty,
            db_estimated_days=analysis.db_estimated_days,
            status=analysis.status,
            current_phase=analysis.current_phase,
            progress_percent=analysis.progress_percent or 0,
            error_message=analysis.error_message,
            created_at=analysis.created_at.isoformat() if analysis.created_at else None,
            started_at=analysis.started_at.isoformat() if analysis.started_at else None,
            completed_at=analysis.completed_at.isoformat() if analysis.completed_at else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyses", response_model=List[AnalysisSummaryResponse])
async def list_analyses(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
) -> List[AnalysisSummaryResponse]:
    """
    List migration analyses

    Optionally filter by status: pending, running, completed, failed
    """
    service = get_migration_analyzer_service(db)

    analyses = await service.list_analyses(
        status=status,
        limit=limit,
        offset=offset
    )

    return [
        AnalysisSummaryResponse(
            id=str(a.id),
            repo_name=a.repo_name,
            source_stack=a.source_stack,
            status=a.status,
            progress_percent=a.progress_percent or 0,
            total_modules=a.total_modules,
            estimated_fp=a.estimated_fp,
            complexity_score=a.complexity_score,
            created_at=a.created_at.isoformat() if a.created_at else None
        )
        for a in analyses
    ]


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> AnalysisResponse:
    """
    Get detailed analysis by ID
    """
    service = get_migration_analyzer_service(db)

    analysis = await service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    return AnalysisResponse(
        id=str(analysis.id),
        repo_path=analysis.repo_path,
        repo_name=analysis.repo_name,
        source_stack=analysis.source_stack,
        secondary_stacks=analysis.secondary_stacks,
        target_stack=analysis.target_stack,
        target_db=analysis.target_db,
        total_files=analysis.total_files,
        total_loc=analysis.total_loc,
        total_modules=analysis.total_modules,
        estimated_fp=analysis.estimated_fp,
        complexity_score=analysis.complexity_score,
        risk_score=analysis.risk_score,
        db_type=analysis.db_type,
        db_migration_difficulty=analysis.db_migration_difficulty,
        db_estimated_days=analysis.db_estimated_days,
        status=analysis.status,
        current_phase=analysis.current_phase,
        progress_percent=analysis.progress_percent or 0,
        error_message=analysis.error_message,
        created_at=analysis.created_at.isoformat() if analysis.created_at else None,
        started_at=analysis.started_at.isoformat() if analysis.started_at else None,
        completed_at=analysis.completed_at.isoformat() if analysis.completed_at else None
    )


@router.post("/analyses/{analysis_id}/run", response_model=AnalysisResponse)
async def run_analysis(
    analysis_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> AnalysisResponse:
    """
    Execute a migration analysis

    Starts the analysis workflow in the foreground.
    For background execution, use the /run-async endpoint.
    """
    service = get_migration_analyzer_service(db)

    try:
        analysis = await service.run_analysis(analysis_id)

        return AnalysisResponse(
            id=str(analysis.id),
            repo_path=analysis.repo_path,
            repo_name=analysis.repo_name,
            source_stack=analysis.source_stack,
            secondary_stacks=analysis.secondary_stacks,
            target_stack=analysis.target_stack,
            target_db=analysis.target_db,
            total_files=analysis.total_files,
            total_loc=analysis.total_loc,
            total_modules=analysis.total_modules,
            estimated_fp=analysis.estimated_fp,
            complexity_score=analysis.complexity_score,
            risk_score=analysis.risk_score,
            db_type=analysis.db_type,
            db_migration_difficulty=analysis.db_migration_difficulty,
            db_estimated_days=analysis.db_estimated_days,
            status=analysis.status,
            current_phase=analysis.current_phase,
            progress_percent=analysis.progress_percent or 0,
            error_message=analysis.error_message,
            created_at=analysis.created_at.isoformat() if analysis.created_at else None,
            started_at=analysis.started_at.isoformat() if analysis.started_at else None,
            completed_at=analysis.completed_at.isoformat() if analysis.completed_at else None
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyses/{analysis_id}/modules", response_model=List[ModuleResponse])
async def get_analysis_modules(
    analysis_id: UUID,
    module_type: Optional[str] = None,
    stack_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> List[ModuleResponse]:
    """
    Get modules for an analysis

    Optionally filter by module_type or stack_type
    """
    from sqlalchemy import select
    from app.models.migration_analysis import MigrationModule

    query = select(MigrationModule).where(MigrationModule.analysis_id == analysis_id)

    if module_type:
        query = query.where(MigrationModule.module_type == module_type)
    if stack_type:
        query = query.where(MigrationModule.stack_type == stack_type)

    result = await db.execute(query)
    modules = list(result.scalars().all())

    return [
        ModuleResponse(
            id=str(m.id),
            name=m.name,
            module_type=m.module_type,
            stack_type=m.stack_type,
            file_path=m.file_path,
            loc=m.loc,
            estimated_fp=m.estimated_fp,
            migration_difficulty=m.migration_difficulty,
            pattern_count=m.pattern_count
        )
        for m in modules
    ]


@router.get("/analyses/{analysis_id}/patterns", response_model=List[PatternResponse])
async def get_analysis_patterns(
    analysis_id: UUID,
    category: Optional[str] = None,
    risk_level: Optional[str] = None,
    security_only: bool = False,
    db: AsyncSession = Depends(get_db)
) -> List[PatternResponse]:
    """
    Get legacy patterns for an analysis

    Optionally filter by category, risk_level, or security issues only
    """
    from sqlalchemy import select
    from app.models.migration_analysis import LegacyPattern

    query = select(LegacyPattern).where(LegacyPattern.analysis_id == analysis_id)

    if category:
        query = query.where(LegacyPattern.pattern_category == category)
    if risk_level:
        query = query.where(LegacyPattern.risk_level == risk_level)
    if security_only:
        query = query.where(LegacyPattern.is_security_issue == True)

    result = await db.execute(query)
    patterns = list(result.scalars().all())

    return [
        PatternResponse(
            id=str(p.id),
            pattern_name=p.pattern_name,
            pattern_category=p.pattern_category,
            file_path=p.file_path,
            line_number=p.line_number,
            risk_level=p.risk_level,
            is_security_issue=p.is_security_issue or False,
            migration_note=p.migration_note
        )
        for p in patterns
    ]


@router.get("/analyses/{analysis_id}/recommendations", response_model=List[RecommendationResponse])
async def get_analysis_recommendations(
    analysis_id: UUID,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> List[RecommendationResponse]:
    """
    Get recommendations for an analysis

    Optionally filter by category or priority
    """
    from sqlalchemy import select
    from app.models.migration_analysis import MigrationRecommendation

    query = select(MigrationRecommendation).where(MigrationRecommendation.analysis_id == analysis_id)

    if category:
        query = query.where(MigrationRecommendation.category == category)
    if priority:
        query = query.where(MigrationRecommendation.priority == priority)

    result = await db.execute(query)
    recommendations = list(result.scalars().all())

    return [
        RecommendationResponse(
            id=str(r.id),
            category=r.category,
            priority=r.priority,
            title=r.title,
            description=r.description,
            source_agent=r.source_agent,
            estimated_effort=r.estimated_effort,
            status=r.status or "pending"
        )
        for r in recommendations
    ]


@router.get("/analyses/{analysis_id}/risks", response_model=List[RiskResponse])
async def get_analysis_risks(
    analysis_id: UUID,
    category: Optional[str] = None,
    min_score: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
) -> List[RiskResponse]:
    """
    Get risk assessments for an analysis

    Optionally filter by category or minimum risk score
    """
    from sqlalchemy import select
    from app.models.migration_analysis import RiskAssessment

    query = select(RiskAssessment).where(RiskAssessment.analysis_id == analysis_id)

    if category:
        query = query.where(RiskAssessment.category == category)
    if min_score:
        query = query.where(RiskAssessment.risk_score >= min_score)

    query = query.order_by(RiskAssessment.risk_score.desc())

    result = await db.execute(query)
    risks = list(result.scalars().all())

    return [
        RiskResponse(
            id=str(r.id),
            risk_id=r.risk_id,
            title=r.title,
            category=r.category,
            probability=r.probability,
            impact=r.impact,
            risk_score=r.risk_score,
            status=r.status or "identified",
            mitigation_strategy=r.mitigation_strategy
        )
        for r in risks
    ]


@router.get("/analyses/{analysis_id}/summary")
async def get_analysis_summary(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a comprehensive summary of an analysis

    Returns aggregated metrics and key findings
    """
    service = get_migration_analyzer_service(db)

    analysis = await service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    return {
        "analysis_id": str(analysis.id),
        "repo_name": analysis.repo_name,
        "status": analysis.status,
        "progress_percent": analysis.progress_percent or 0,
        "metrics": {
            "total_files": analysis.total_files,
            "total_loc": analysis.total_loc,
            "total_modules": analysis.total_modules,
            "estimated_fp": analysis.estimated_fp,
            "complexity_score": analysis.complexity_score,
            "risk_score": analysis.risk_score
        },
        "stacks": {
            "source": analysis.source_stack,
            "secondary": analysis.secondary_stacks,
            "target": analysis.target_stack
        },
        "database": {
            "type": analysis.db_type,
            "migration_difficulty": analysis.db_migration_difficulty,
            "estimated_days": analysis.db_estimated_days
        },
        "summaries": {
            "patterns": analysis.pattern_summary,
            "risks": analysis.risk_summary,
            "modules": analysis.module_inventory
        }
    }
