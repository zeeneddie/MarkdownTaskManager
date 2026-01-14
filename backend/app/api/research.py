"""
Week 131 Research API - Background Jobs, Load Estimation, Documentation Rules

API endpoints for the three research services:
- BackgroundJobDetectorService
- LoadEstimationService
- DocumentationRuleExtractorService

Agent: Miguel (Migration Architect), Peter (Product Owner)
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_async_db as get_async_session
from app.services.background_job_detector_service import BackgroundJobDetectorService
from app.services.load_estimation_service import LoadEstimationService
from app.services.static_analysis.documentation_rule_extractor import DocumentationRuleExtractorService
from app.models.research import (
    BackgroundJobModel,
    LoadEstimationModel,
    DocumentationRuleModel,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research", tags=["Week 131 Research"])


# ============================================================================
# Request/Response Models
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Base request for analysis endpoints."""
    project_path: str = Field(..., description="Path to the project to analyze")
    project_id: Optional[int] = Field(None, description="Optional project ID for database storage")


class BackgroundJobAnalyzeRequest(AnalyzeRequest):
    """Request for background job detection."""
    include_extensions: Optional[List[str]] = Field(
        None,
        description="File extensions to scan (default: .vb, .cs, .sql, etc.)"
    )
    exclude_patterns: Optional[List[str]] = Field(
        None,
        description="Glob patterns to exclude"
    )


class LoadEstimationAnalyzeRequest(AnalyzeRequest):
    """Request for load estimation analysis."""
    include_sql_analysis: bool = Field(
        True,
        description="Whether to include SQL query complexity analysis"
    )


class DocumentationExtractRequest(AnalyzeRequest):
    """Request for documentation rule extraction."""
    include_extensions: Optional[List[str]] = Field(
        None,
        description="Documentation file extensions (default: .md, .txt, .rst)"
    )
    code_rules: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Optional code-extracted rules for correlation"
    )


class BackgroundJobResponse(BaseModel):
    """Response model for a background job."""
    job_id: str
    name: str
    job_type: str
    source_file: str
    confidence: float
    trigger_type: Optional[str] = None
    schedule: Optional[str] = None
    entry_point: Optional[str] = None
    detection_method: Optional[str] = None
    has_error_handling: bool = False
    has_logging: bool = False
    database_dependencies: List[str] = []
    service_dependencies: List[str] = []
    description: Optional[str] = None


class BackgroundJobDetectionResponse(BaseModel):
    """Response for background job detection."""
    success: bool
    jobs: List[BackgroundJobResponse] = []
    total_jobs: int = 0
    by_job_type: Dict[str, int] = {}
    by_trigger_type: Dict[str, int] = {}
    files_scanned: int = 0
    duration_ms: int = 0
    errors: List[str] = []


class ConnectionPoolResponse(BaseModel):
    """Response model for connection pool config."""
    name: str
    min_pool_size: int
    max_pool_size: int
    connection_timeout: int
    provider: Optional[str] = None


class LoadEstimationResponse(BaseModel):
    """Response for load estimation analysis."""
    success: bool
    connection_pools: List[ConnectionPoolResponse] = []
    total_sql_connections: int = 0
    using_block_count: int = 0
    open_close_ratio: float = 0.0
    session_mode: Optional[str] = None
    session_timeout_minutes: int = 20
    query_complexity_score: int = 0
    estimated_concurrent_users: int = 0
    capacity_rating: str = ""
    capacity_bottleneck: Optional[str] = None
    bottleneck_details: Optional[str] = None
    recommendations: List[str] = []
    files_analyzed: int = 0
    duration_ms: int = 0
    errors: List[str] = []


class DocumentationRuleResponse(BaseModel):
    """Response model for a documentation rule."""
    rule_id: str
    rule_type: str
    condition: Optional[str] = None
    action: Optional[str] = None
    natural_language: Optional[str] = None
    source_file: str
    source_section: Optional[str] = None
    source_line: Optional[int] = None
    extraction_pattern: Optional[str] = None
    confidence: float
    related_code_rules: List[str] = []
    conflicts: List[str] = []


class DocumentationExtractionResponse(BaseModel):
    """Response for documentation rule extraction."""
    success: bool
    rules: List[DocumentationRuleResponse] = []
    total_rules: int = 0
    by_type: Dict[str, int] = {}
    by_confidence: Dict[str, int] = {}
    files_scanned: int = 0
    duration_ms: int = 0
    errors: List[str] = []


class ConflictResponse(BaseModel):
    """Response model for a rule conflict."""
    rule1_id: str
    rule2_id: str
    conflict_type: str
    description: str
    rule1_source: str
    rule2_source: str


# ============================================================================
# Background Job Detection Endpoints
# ============================================================================

@router.post("/background-jobs/analyze", response_model=BackgroundJobDetectionResponse)
async def analyze_background_jobs(
    request: BackgroundJobAnalyzeRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Analyze a project to detect background jobs, scheduled tasks, and batch processes.

    Detection patterns:
    - Naming conventions (Nachtjob, Batch, Scheduler)
    - Directory patterns (/Beheer/, /Jobs/, etc.)
    - Code patterns (Timer_Elapsed, BackgroundWorker, etc.)
    - SQL Agent jobs
    - Quartz.NET / Hangfire configurations
    """
    project_path = Path(request.project_path)

    if not project_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Project path does not exist: {project_path}"
        )

    try:
        service = BackgroundJobDetectorService()
        result = service.detect(
            project_path=project_path,
            include_extensions=request.include_extensions,
            exclude_patterns=request.exclude_patterns,
        )

        # Store in database if project_id provided
        if request.project_id and result.success:
            for job in result.jobs:
                db_job = BackgroundJobModel(
                    project_id=request.project_id,
                    job_id=job.job_id,
                    name=job.name,
                    job_type=job.job_type.value if hasattr(job.job_type, 'value') else str(job.job_type),
                    schedule=job.schedule,
                    source_file=job.source_file,
                    source_line_start=job.source_line_start,
                    source_line_end=job.source_line_end,
                    entry_point=job.entry_point,
                    trigger_type=job.trigger_type.value if hasattr(job.trigger_type, 'value') else str(job.trigger_type),
                    detection_method=job.detection_method.value if hasattr(job.detection_method, 'value') else str(job.detection_method),
                    confidence=job.confidence,
                    database_dependencies=job.database_dependencies,
                    file_dependencies=job.file_dependencies,
                    service_dependencies=job.service_dependencies,
                    has_error_handling=job.has_error_handling,
                    error_handling_pattern=job.error_handling_pattern,
                    has_logging=job.has_logging,
                    estimated_duration=job.estimated_duration,
                    resource_intensity=job.resource_intensity.value if hasattr(job.resource_intensity, 'value') else str(job.resource_intensity),
                    description=job.description,
                )
                session.add(db_job)
            await session.commit()

        # Build response
        job_responses = [
            BackgroundJobResponse(
                job_id=j.job_id,
                name=j.name,
                job_type=j.job_type.value if hasattr(j.job_type, 'value') else str(j.job_type),
                source_file=j.source_file,
                confidence=j.confidence,
                trigger_type=j.trigger_type.value if hasattr(j.trigger_type, 'value') else str(j.trigger_type),
                schedule=j.schedule,
                entry_point=j.entry_point,
                detection_method=j.detection_method.value if hasattr(j.detection_method, 'value') else str(j.detection_method),
                has_error_handling=j.has_error_handling,
                has_logging=j.has_logging,
                database_dependencies=j.database_dependencies,
                service_dependencies=j.service_dependencies,
                description=j.description,
            )
            for j in result.jobs
        ]

        return BackgroundJobDetectionResponse(
            success=result.success,
            jobs=job_responses,
            total_jobs=result.total_jobs,
            by_job_type=result.by_job_type,
            by_trigger_type=result.by_trigger_type,
            files_scanned=result.files_scanned,
            duration_ms=result.duration_ms,
            errors=result.errors,
        )

    except Exception as e:
        logger.exception(f"Error analyzing background jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/background-jobs/{project_id}", response_model=List[BackgroundJobResponse])
async def get_background_jobs(
    project_id: int,
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    trigger_type: Optional[str] = Query(None, description="Filter by trigger type"),
    min_confidence: float = Query(0.0, description="Minimum confidence threshold"),
    session: AsyncSession = Depends(get_async_session),
):
    """Get stored background jobs for a project."""
    try:
        query = select(BackgroundJobModel).where(
            BackgroundJobModel.project_id == project_id,
            BackgroundJobModel.confidence >= min_confidence,
        )

        if job_type:
            query = query.where(BackgroundJobModel.job_type == job_type)
        if trigger_type:
            query = query.where(BackgroundJobModel.trigger_type == trigger_type)

        result = await session.execute(query)
        jobs = result.scalars().all()

        return [
            BackgroundJobResponse(
                job_id=j.job_id,
                name=j.name,
                job_type=j.job_type,
                source_file=j.source_file,
                confidence=j.confidence,
                trigger_type=j.trigger_type,
                schedule=j.schedule,
                entry_point=j.entry_point,
                detection_method=j.detection_method,
                has_error_handling=j.has_error_handling,
                has_logging=j.has_logging,
                database_dependencies=j.database_dependencies or [],
                service_dependencies=j.service_dependencies or [],
                description=j.description,
            )
            for j in jobs
        ]

    except Exception as e:
        logger.exception(f"Error getting background jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Load Estimation Endpoints
# ============================================================================

@router.post("/load-estimation/analyze", response_model=LoadEstimationResponse)
async def analyze_load_estimation(
    request: LoadEstimationAnalyzeRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Analyze a project to estimate concurrent user capacity.

    Analyzes:
    - Connection pool configurations (web.config, appsettings.json)
    - Session state configuration
    - Database connection patterns (Using blocks, Open/Close ratio)
    - SQL query complexity
    """
    project_path = Path(request.project_path)

    if not project_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Project path does not exist: {project_path}"
        )

    try:
        service = LoadEstimationService()
        result = service.analyze(
            project_path=project_path,
            include_sql_analysis=request.include_sql_analysis,
        )

        # Store in database if project_id provided
        if request.project_id and result.success:
            db_estimation = LoadEstimationModel(
                project_id=request.project_id,
                connection_pools=[p.to_dict() for p in result.connection_pools],
                total_sql_connections=result.total_sql_connections,
                using_block_count=result.using_block_count,
                open_close_ratio=result.open_close_ratio,
                session_config=result.session_config.to_dict() if result.session_config else None,
                session_access_count=result.session_access_count,
                session_variable_count=result.session_variable_count,
                query_metrics=result.query_metrics.to_dict() if result.query_metrics else None,
                estimated_concurrent_users=result.estimated_concurrent_users,
                capacity_bottleneck=result.capacity_bottleneck.value if hasattr(result.capacity_bottleneck, 'value') else str(result.capacity_bottleneck),
                bottleneck_details=result.bottleneck_details,
                recommendations=result.recommendations,
                analysis_path=result.analysis_path,
                files_analyzed=result.files_analyzed,
                duration_ms=result.duration_ms,
                success=result.success,
                errors=result.errors,
            )
            session.add(db_estimation)
            await session.commit()

        # Build response
        pool_responses = [
            ConnectionPoolResponse(
                name=p.name,
                min_pool_size=p.min_pool_size,
                max_pool_size=p.max_pool_size,
                connection_timeout=p.connection_timeout,
                provider=p.provider,
            )
            for p in result.connection_pools
        ]

        return LoadEstimationResponse(
            success=result.success,
            connection_pools=pool_responses,
            total_sql_connections=result.total_sql_connections,
            using_block_count=result.using_block_count,
            open_close_ratio=result.open_close_ratio,
            session_mode=result.session_config.mode.value if result.session_config else None,
            session_timeout_minutes=result.session_config.timeout_minutes if result.session_config else 20,
            query_complexity_score=result.query_metrics.complexity_score if result.query_metrics else 0,
            estimated_concurrent_users=result.estimated_concurrent_users,
            capacity_rating=service._get_capacity_rating(result.estimated_concurrent_users),
            capacity_bottleneck=result.capacity_bottleneck.value if hasattr(result.capacity_bottleneck, 'value') else None,
            bottleneck_details=result.bottleneck_details,
            recommendations=result.recommendations,
            files_analyzed=result.files_analyzed,
            duration_ms=result.duration_ms,
            errors=result.errors,
        )

    except Exception as e:
        logger.exception(f"Error analyzing load estimation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/load-estimation/{project_id}", response_model=LoadEstimationResponse)
async def get_load_estimation(
    project_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Get the latest load estimation for a project."""
    try:
        query = select(LoadEstimationModel).where(
            LoadEstimationModel.project_id == project_id
        ).order_by(LoadEstimationModel.created_at.desc()).limit(1)

        result = await session.execute(query)
        estimation = result.scalar_one_or_none()

        if not estimation:
            raise HTTPException(
                status_code=404,
                detail=f"No load estimation found for project {project_id}"
            )

        pools = estimation.connection_pools or []
        pool_responses = [
            ConnectionPoolResponse(
                name=p.get('name', 'Unknown'),
                min_pool_size=p.get('min_pool_size', 0),
                max_pool_size=p.get('max_pool_size', 100),
                connection_timeout=p.get('connection_timeout', 15),
                provider=p.get('provider'),
            )
            for p in pools
        ]

        session_config = estimation.session_config or {}
        query_metrics = estimation.query_metrics or {}

        return LoadEstimationResponse(
            success=estimation.success,
            connection_pools=pool_responses,
            total_sql_connections=estimation.total_sql_connections,
            using_block_count=estimation.using_block_count,
            open_close_ratio=estimation.open_close_ratio,
            session_mode=session_config.get('mode'),
            session_timeout_minutes=session_config.get('timeout_minutes', 20),
            query_complexity_score=query_metrics.get('complexity_score', 0),
            estimated_concurrent_users=estimation.estimated_concurrent_users,
            capacity_rating=LoadEstimationService()._get_capacity_rating(estimation.estimated_concurrent_users),
            capacity_bottleneck=estimation.capacity_bottleneck,
            bottleneck_details=estimation.bottleneck_details,
            recommendations=estimation.recommendations or [],
            files_analyzed=estimation.files_analyzed,
            duration_ms=estimation.duration_ms,
            errors=estimation.errors or [],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting load estimation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Documentation Rule Extraction Endpoints
# ============================================================================

@router.post("/documentation-rules/extract", response_model=DocumentationExtractionResponse)
async def extract_documentation_rules(
    request: DocumentationExtractRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Extract business rules from documentation files.

    Extraction patterns:
    - Rule prefixes (Rule:, Business Rule:, BR-xxx)
    - RFC 2119 keywords (MUST, SHALL, SHOULD, MAY)
    - Conditional statements (IF-THEN, WHEN-THEN)
    - Numbered lists with rule content
    - Markdown tables with Condition/Action columns
    """
    project_path = Path(request.project_path)

    if not project_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Project path does not exist: {project_path}"
        )

    try:
        service = DocumentationRuleExtractorService()
        result = service.extract_from_directory(
            path=project_path,
            code_rules=request.code_rules,
            include_extensions=request.include_extensions,
        )

        # Store in database if project_id provided
        if request.project_id and result.success:
            for rule in result.rules:
                db_rule = DocumentationRuleModel(
                    project_id=request.project_id,
                    rule_id=rule.rule_id,
                    rule_type=rule.rule_type.value if hasattr(rule.rule_type, 'value') else str(rule.rule_type),
                    condition=rule.condition,
                    action=rule.action,
                    natural_language=rule.natural_language,
                    source_file=rule.source_file,
                    source_section=rule.source_section,
                    source_line=rule.source_line,
                    extraction_pattern=rule.extraction_pattern,
                    confidence=rule.confidence,
                    related_code_rules=rule.related_code_rules,
                    conflicts=rule.conflicts,
                )
                session.add(db_rule)
            await session.commit()

        # Build response
        rule_responses = [
            DocumentationRuleResponse(
                rule_id=r.rule_id,
                rule_type=r.rule_type.value if hasattr(r.rule_type, 'value') else str(r.rule_type),
                condition=r.condition,
                action=r.action,
                natural_language=r.natural_language,
                source_file=r.source_file,
                source_section=r.source_section,
                source_line=r.source_line,
                extraction_pattern=r.extraction_pattern,
                confidence=r.confidence,
                related_code_rules=r.related_code_rules,
                conflicts=r.conflicts,
            )
            for r in result.rules
        ]

        return DocumentationExtractionResponse(
            success=result.success,
            rules=rule_responses,
            total_rules=result.total_rules,
            by_type=result.by_type,
            by_confidence=result.by_confidence,
            files_scanned=result.files_scanned,
            duration_ms=result.duration_ms,
            errors=result.errors,
        )

    except Exception as e:
        logger.exception(f"Error extracting documentation rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documentation-rules/{project_id}", response_model=List[DocumentationRuleResponse])
async def get_documentation_rules(
    project_id: int,
    rule_type: Optional[str] = Query(None, description="Filter by rule type"),
    min_confidence: float = Query(0.0, description="Minimum confidence threshold"),
    validated_only: bool = Query(False, description="Only return validated rules"),
    session: AsyncSession = Depends(get_async_session),
):
    """Get stored documentation rules for a project."""
    try:
        query = select(DocumentationRuleModel).where(
            DocumentationRuleModel.project_id == project_id,
            DocumentationRuleModel.confidence >= min_confidence,
        )

        if rule_type:
            query = query.where(DocumentationRuleModel.rule_type == rule_type)
        if validated_only:
            query = query.where(DocumentationRuleModel.is_validated == True)

        result = await session.execute(query)
        rules = result.scalars().all()

        return [
            DocumentationRuleResponse(
                rule_id=r.rule_id,
                rule_type=r.rule_type,
                condition=r.condition,
                action=r.action,
                natural_language=r.natural_language,
                source_file=r.source_file,
                source_section=r.source_section,
                source_line=r.source_line,
                extraction_pattern=r.extraction_pattern,
                confidence=r.confidence,
                related_code_rules=r.related_code_rules or [],
                conflicts=r.conflicts or [],
            )
            for r in rules
        ]

    except Exception as e:
        logger.exception(f"Error getting documentation rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documentation-rules/{project_id}/conflicts", response_model=List[ConflictResponse])
async def get_documentation_rule_conflicts(
    project_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Detect conflicts between documentation rules for a project.

    Returns pairs of rules that have similar conditions but different actions.
    """
    try:
        # Get all rules for the project
        query = select(DocumentationRuleModel).where(
            DocumentationRuleModel.project_id == project_id
        )
        result = await session.execute(query)
        db_rules = result.scalars().all()

        # Convert to domain objects for conflict detection
        from app.models.research import DocumentationRule, RuleType

        rules = [
            DocumentationRule(
                rule_id=r.rule_id,
                rule_type=RuleType(r.rule_type) if r.rule_type in [rt.value for rt in RuleType] else RuleType.GENERAL,
                condition=r.condition,
                action=r.action,
                natural_language=r.natural_language,
                source_file=r.source_file,
                source_section=r.source_section,
                source_line=r.source_line,
                extraction_pattern=r.extraction_pattern,
                confidence=r.confidence,
                related_code_rules=r.related_code_rules or [],
                conflicts=r.conflicts or [],
            )
            for r in db_rules
        ]

        # Detect conflicts
        service = DocumentationRuleExtractorService()
        conflicts = service.detect_conflicts(rules)

        return [
            ConflictResponse(**c)
            for c in conflicts
        ]

    except Exception as e:
        logger.exception(f"Error detecting conflicts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Summary Endpoint
# ============================================================================

@router.get("/summary/{project_id}")
async def get_research_summary(
    project_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get a summary of all Week 131 research results for a project.

    Combines:
    - Background job detection results
    - Load estimation results
    - Documentation rule extraction results
    """
    try:
        # Get background jobs count
        jobs_query = select(BackgroundJobModel).where(
            BackgroundJobModel.project_id == project_id
        )
        jobs_result = await session.execute(jobs_query)
        jobs = jobs_result.scalars().all()

        # Get latest load estimation
        load_query = select(LoadEstimationModel).where(
            LoadEstimationModel.project_id == project_id
        ).order_by(LoadEstimationModel.created_at.desc()).limit(1)
        load_result = await session.execute(load_query)
        load_estimation = load_result.scalar_one_or_none()

        # Get documentation rules count
        rules_query = select(DocumentationRuleModel).where(
            DocumentationRuleModel.project_id == project_id
        )
        rules_result = await session.execute(rules_query)
        rules = rules_result.scalars().all()

        return {
            "project_id": project_id,
            "background_jobs": {
                "total": len(jobs),
                "by_type": _count_by_field(jobs, 'job_type'),
                "by_trigger": _count_by_field(jobs, 'trigger_type'),
                "high_confidence": len([j for j in jobs if j.confidence >= 0.8]),
            },
            "load_estimation": {
                "available": load_estimation is not None,
                "estimated_users": load_estimation.estimated_concurrent_users if load_estimation else None,
                "bottleneck": load_estimation.capacity_bottleneck if load_estimation else None,
                "recommendations_count": len(load_estimation.recommendations or []) if load_estimation else 0,
            },
            "documentation_rules": {
                "total": len(rules),
                "by_type": _count_by_field(rules, 'rule_type'),
                "high_confidence": len([r for r in rules if r.confidence >= 0.8]),
                "with_conflicts": len([r for r in rules if r.conflicts]),
            },
        }

    except Exception as e:
        logger.exception(f"Error getting research summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _count_by_field(items, field_name: str) -> Dict[str, int]:
    """Count items by a field value."""
    counts = {}
    for item in items:
        value = getattr(item, field_name, None)
        if value:
            counts[value] = counts.get(value, 0) + 1
    return counts
