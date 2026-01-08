# backend/app/api/hybrid_extraction.py
"""
Hybrid Business Rule Extraction API - Week 111-114 Phase 5

API endpoints for the 12-language hybrid extraction pipeline:
- VB.NET, Classic ASP, T-SQL, PL/SQL (Regex Tier 2)
- Python, C#, JavaScript/TypeScript, Java (AST Tier 1)
- ASPX, VB6, PHP (Regex Tier 2)
- LLM-assisted classification and validation (Tier 3)

Endpoints:
- POST /extract/{project_id} - Start hybrid extraction
- GET /sessions/{session_id} - Get extraction session
- GET /sessions/{session_id}/rules - Get extracted rules
- GET /sessions/{session_id}/workflows - Get detected workflows
- GET /sessions/{session_id}/entities - Get detected entities
- GET /sessions/{session_id}/agent-context/{agent_name} - Get agent-specific context
- GET /project/{project_id}/sessions - List project sessions
- GET /languages - List supported languages
- GET /tiers - List extraction tiers
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.database import get_db
from app.models.hybrid_extraction import (
    HybridExtractionSession,
    HybridExtractedRule,
    HybridWorkflowCorrelation,
    HybridEntityMapping,
    ExtractionStatus,
    ExtractionTier,
    RuleType,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hybrid-extraction", tags=["Hybrid Extraction"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ExtractionRequest(BaseModel):
    """Request to start hybrid extraction."""
    source_path: str = Field(..., description="Path to source code (file or directory)")
    tier: str = Field(default="STANDARD", description="Extraction tier: FREE, BASIC, STANDARD, PROFESSIONAL, PREMIUM")
    workflow_type: Optional[str] = Field(default=None, description="Workflow context: BROWN_PAPER, MIGRATION, BACKLOG_GENERATION")
    enable_llm: bool = Field(default=True, description="Enable LLM features (if tier allows)")
    recursive: bool = Field(default=True, description="Scan subdirectories")
    languages: Optional[List[str]] = Field(default=None, description="Filter by languages (optional)")


class ExtractionResponse(BaseModel):
    """Response from extraction start."""
    session_id: str
    status: str
    message: str


class SessionSummary(BaseModel):
    """Extraction session summary."""
    id: str
    project_id: int
    source_path: str
    tier: str
    status: str
    workflow_type: Optional[str]
    total_rules: int
    high_confidence_rules: int
    average_confidence: float
    detected_languages: List[str]
    total_cost_cents: float
    total_ms: int
    created_at: str
    completed_at: Optional[str]


class RuleResponse(BaseModel):
    """Business rule response."""
    id: str
    rule_type: str
    extraction_method: str
    language: str
    condition: str
    action: str
    description: Optional[str]
    natural_language: Optional[str]
    source_file: str
    source_lines: Optional[List[int]]
    confidence: float
    llm_validated: bool
    compliance_tags: List[str]


class WorkflowResponse(BaseModel):
    """Workflow correlation response."""
    id: str
    workflow_name: str
    workflow_type: str
    primary_entity: Optional[str]
    operations: List[str]
    total_rules: int
    confidence: float


class EntityResponse(BaseModel):
    """Entity mapping response."""
    id: str
    entity_name: str
    entity_type: str
    rule_count: int
    crud_coverage: Optional[str]
    has_create: bool
    has_read: bool
    has_update: bool
    has_delete: bool


# =============================================================================
# BACKGROUND TASK
# =============================================================================

async def run_extraction_task(
    session_id: UUID,
    project_id: int,
    source_path: str,
    tier: str,
    workflow_type: Optional[str],
    enable_llm: bool,
    recursive: bool,
    languages: Optional[List[str]],
    db: AsyncSession,
):
    """Background task to run hybrid extraction."""
    from app.services.static_analysis.tier_orchestrator import TierOrchestrator
    from app.services.static_analysis.extraction_models import ExtractionTier as ETier, Language
    from app.services.static_analysis.rule_correlation_service import RuleCorrelationService
    from pathlib import Path

    try:
        # Update session to running
        await db.execute(
            update(HybridExtractionSession)
            .where(HybridExtractionSession.id == session_id)
            .values(status='running', started_at=datetime.utcnow())
        )
        await db.commit()

        # Map tier string to enum
        tier_map = {
            "FREE": ETier.FREE,
            "BASIC": ETier.BASIC,
            "STANDARD": ETier.STANDARD,
            "PROFESSIONAL": ETier.PROFESSIONAL,
            "PREMIUM": ETier.PREMIUM,
        }
        extraction_tier = tier_map.get(tier.upper(), ETier.STANDARD)

        # Map language strings to enums if specified
        language_enums = None
        if languages:
            lang_map = {
                "python": Language.PYTHON,
                "csharp": Language.CSHARP,
                "javascript": Language.JAVASCRIPT,
                "typescript": Language.TYPESCRIPT,
                "java": Language.JAVA,
                "vbnet": Language.VB_NET,
                "vb.net": Language.VB_NET,
                "asp": Language.CLASSIC_ASP,
                "classic_asp": Language.CLASSIC_ASP,
                "tsql": Language.T_SQL,
                "t-sql": Language.T_SQL,
                "plsql": Language.PL_SQL,
                "pl/sql": Language.PL_SQL,
                "aspx": Language.ASPX,
                "vb6": Language.VB6,
                "php": Language.PHP,
            }
            language_enums = [lang_map[l.lower()] for l in languages if l.lower() in lang_map]

        # Create orchestrator and run extraction
        orchestrator = TierOrchestrator(
            extraction_tier=extraction_tier,
            project_id=project_id,
        )

        path = Path(source_path)
        if path.is_file():
            result = await orchestrator.extract_from_file(str(path), enable_llm)
        else:
            result = await orchestrator.extract_from_directory(
                str(path),
                recursive=recursive,
                languages=language_enums,
                enable_llm=enable_llm,
            )

        # Run correlation to detect workflows and entities
        correlation_service = RuleCorrelationService(project_id=project_id)
        correlation_result = correlation_service.correlate(result.rules)

        # Count files and lines (estimate)
        total_files = len(set(r.source_file for r in result.rules)) if result.rules else 0

        # Detect technologies from rules
        detected_languages = list(set(
            Path(r.source_file).suffix[1:].upper() if r.source_file else "UNKNOWN"
            for r in result.rules
        ))

        # Store rules
        for rule in result.rules:
            db_rule = HybridExtractedRule(
                id=rule.id,
                session_id=session_id,
                rule_type=rule.rule_type.value if hasattr(rule.rule_type, 'value') else str(rule.rule_type),
                extraction_method=rule.extraction_method.value if hasattr(rule.extraction_method, 'value') else 'REGEX',
                language=rule.language.value if hasattr(rule.language, 'value') else 'UNKNOWN',
                condition=rule.condition,
                action=rule.action,
                description=rule.description,
                natural_language=getattr(rule, 'natural_language', None),
                code_snippet=getattr(rule, 'code_snippet', None),
                source_file=rule.source_file,
                source_line_start=rule.line_start if hasattr(rule, 'line_start') else None,
                source_line_end=rule.line_end if hasattr(rule, 'line_end') else None,
                variables_involved=getattr(rule, 'variables', []),
                entities_referenced=getattr(rule, 'entities', []),
                confidence=rule.confidence,
                llm_validated=getattr(rule, 'llm_validated', False),
                llm_confidence=getattr(rule, 'llm_confidence', None),
                validation_provider=getattr(rule, 'validation_provider', None),
                compliance_tags=getattr(rule, 'compliance_tags', []),
            )
            db.add(db_rule)

        # Store workflows
        for workflow in correlation_result.workflows:
            db_workflow = HybridWorkflowCorrelation(
                id=uuid.uuid4(),
                session_id=session_id,
                workflow_name=workflow.name,
                workflow_type=workflow.workflow_type.value if hasattr(workflow.workflow_type, 'value') else str(workflow.workflow_type),
                primary_entity=workflow.primary_entity,
                operations=[op.value if hasattr(op, 'value') else str(op) for op in workflow.operations],
                total_rules=workflow.total_rules,
                source_files=workflow.source_files[:10],
                auth_pattern=workflow.auth_pattern,
                confidence=workflow.confidence,
            )
            db.add(db_workflow)

        # Store entities
        for entity in correlation_result.entities:
            db_entity = HybridEntityMapping(
                id=uuid.uuid4(),
                session_id=session_id,
                entity_name=entity.name,
                entity_type=entity.entity_type if hasattr(entity, 'entity_type') else 'TABLE',
                rule_count=entity.rule_count,
                has_create=entity.has_create,
                has_read=entity.has_read,
                has_update=entity.has_update,
                has_delete=entity.has_delete,
                crud_coverage=entity.crud_coverage,
                files_referenced=entity.files_referenced[:10],
            )
            db.add(db_entity)

        # Update session with results
        await db.execute(
            update(HybridExtractionSession)
            .where(HybridExtractionSession.id == session_id)
            .values(
                status='completed',
                completed_at=datetime.utcnow(),
                total_files=total_files,
                total_rules=result.metrics.total_rules,
                high_confidence_rules=result.metrics.high_confidence_rules,
                average_confidence=result.metrics.average_confidence,
                static_rules_extracted=result.metrics.static_rules_extracted,
                llm_rules_extracted=result.metrics.llm_rules_extracted,
                rules_classified=result.metrics.rules_classified,
                rules_confirmed=result.metrics.rules_confirmed,
                rules_rejected=result.metrics.rules_rejected,
                multi_llm_validated=result.metrics.multi_llm_validated,
                consensus_reached=result.metrics.consensus_reached,
                premium_synthesis_performed=result.metrics.premium_synthesis_performed,
                total_tokens=result.metrics.total_tokens,
                total_cost_cents=result.metrics.total_cost_cents,
                static_extraction_ms=result.metrics.static_extraction_ms,
                llm_classification_ms=result.metrics.llm_classification_ms,
                llm_extraction_ms=result.metrics.llm_extraction_ms,
                multi_llm_validation_ms=result.metrics.multi_llm_validation_ms,
                premium_synthesis_ms=result.metrics.premium_synthesis_ms,
                total_ms=result.metrics.total_ms,
                detected_languages=detected_languages,
                synthesis_result=result.synthesis_result,
                errors=result.errors,
                warnings=result.warnings,
            )
        )
        await db.commit()

        logger.info(
            f"Extraction complete for session {session_id}: "
            f"{result.metrics.total_rules} rules, "
            f"{len(correlation_result.workflows)} workflows, "
            f"{len(correlation_result.entities)} entities"
        )

    except Exception as e:
        logger.error(f"Extraction failed for session {session_id}: {e}", exc_info=True)
        await db.execute(
            update(HybridExtractionSession)
            .where(HybridExtractionSession.id == session_id)
            .values(
                status='failed',
                completed_at=datetime.utcnow(),
                errors=[str(e)],
            )
        )
        await db.commit()


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/extract/{project_id}", response_model=ExtractionResponse)
async def start_extraction(
    project_id: int,
    request: ExtractionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Start hybrid business rule extraction for a project.

    Runs extraction in background and returns session ID immediately.
    Use GET /sessions/{session_id} to poll for status.

    Pipeline:
    1. Static Extraction (AST/Regex) - Always runs
    2. LLM Classification (BASIC+) - Validates ambiguous rules
    3. LLM Extraction (STANDARD+) - Extracts from comments/messages
    4. Multi-LLM Validation (PROFESSIONAL+) - Cross-validation
    5. Premium Synthesis (PREMIUM) - Final Claude Opus review
    """
    # Validate tier
    valid_tiers = ["FREE", "BASIC", "STANDARD", "PROFESSIONAL", "PREMIUM"]
    tier = request.tier.upper()
    if tier not in valid_tiers:
        tier = "STANDARD"

    # Create session
    session_id = uuid.uuid4()
    session = HybridExtractionSession(
        id=session_id,
        project_id=project_id,
        source_path=request.source_path,
        extraction_tier=tier,
        status='pending',
        workflow_type=request.workflow_type,
    )
    db.add(session)
    await db.commit()

    # Start background task
    background_tasks.add_task(
        run_extraction_task,
        session_id=session_id,
        project_id=project_id,
        source_path=request.source_path,
        tier=tier,
        workflow_type=request.workflow_type,
        enable_llm=request.enable_llm,
        recursive=request.recursive,
        languages=request.languages,
        db=db,
    )

    return ExtractionResponse(
        session_id=str(session_id),
        status="pending",
        message=f"Hybrid extraction started with tier {tier}. Poll GET /sessions/{session_id} for status.",
    )


@router.get("/sessions/{session_id}", response_model=SessionSummary)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get extraction session details."""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(400, "Invalid session ID")

    result = await db.execute(
        select(HybridExtractionSession).where(HybridExtractionSession.id == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(404, "Session not found")

    return SessionSummary(
        id=str(session.id),
        project_id=session.project_id,
        source_path=session.source_path,
        tier=session.extraction_tier,
        status=session.status,
        workflow_type=session.workflow_type,
        total_rules=session.total_rules or 0,
        high_confidence_rules=session.high_confidence_rules or 0,
        average_confidence=session.average_confidence or 0.0,
        detected_languages=session.detected_languages or [],
        total_cost_cents=session.total_cost_cents or 0.0,
        total_ms=session.total_ms or 0,
        created_at=session.created_at.isoformat() if session.created_at else "",
        completed_at=session.completed_at.isoformat() if session.completed_at else None,
    )


@router.get("/sessions/{session_id}/full")
async def get_session_full(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get full session details including all metrics."""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(400, "Invalid session ID")

    result = await db.execute(
        select(HybridExtractionSession).where(HybridExtractionSession.id == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(404, "Session not found")

    return session.to_dict()


@router.get("/sessions/{session_id}/rules")
async def get_session_rules(
    session_id: str,
    rule_type: Optional[str] = Query(None, description="Filter by rule type"),
    language: Optional[str] = Query(None, description="Filter by language"),
    min_confidence: float = Query(0.0, description="Minimum confidence"),
    llm_validated_only: bool = Query(False, description="Only LLM-validated rules"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """Get extracted business rules from a session."""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(400, "Invalid session ID")

    query = select(HybridExtractedRule).where(
        HybridExtractedRule.session_id == session_uuid,
        HybridExtractedRule.confidence >= min_confidence,
    )

    if rule_type:
        query = query.where(HybridExtractedRule.rule_type == rule_type.upper())

    if language:
        query = query.where(HybridExtractedRule.language == language.upper())

    if llm_validated_only:
        query = query.where(HybridExtractedRule.llm_validated == True)

    query = query.order_by(HybridExtractedRule.confidence.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    rules = result.scalars().all()

    # Get total count
    count_query = select(func.count()).select_from(HybridExtractedRule).where(
        HybridExtractedRule.session_id == session_uuid
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return {
        "rules": [r.to_dict() for r in rules],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get("/sessions/{session_id}/workflows")
async def get_session_workflows(
    session_id: str,
    workflow_type: Optional[str] = Query(None, description="Filter by workflow type"),
    db: AsyncSession = Depends(get_db),
):
    """Get detected workflows from a session."""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(400, "Invalid session ID")

    query = select(HybridWorkflowCorrelation).where(
        HybridWorkflowCorrelation.session_id == session_uuid
    )

    if workflow_type:
        query = query.where(HybridWorkflowCorrelation.workflow_type == workflow_type.upper())

    query = query.order_by(HybridWorkflowCorrelation.confidence.desc())

    result = await db.execute(query)
    workflows = result.scalars().all()

    return {
        "workflows": [w.to_dict() for w in workflows],
        "total": len(workflows),
    }


@router.get("/sessions/{session_id}/entities")
async def get_session_entities(
    session_id: str,
    min_rule_count: int = Query(0, description="Minimum rule count"),
    db: AsyncSession = Depends(get_db),
):
    """Get detected entities from a session."""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(400, "Invalid session ID")

    query = select(HybridEntityMapping).where(
        HybridEntityMapping.session_id == session_uuid,
        HybridEntityMapping.rule_count >= min_rule_count,
    )

    query = query.order_by(HybridEntityMapping.rule_count.desc())

    result = await db.execute(query)
    entities = result.scalars().all()

    return {
        "entities": [e.to_dict() for e in entities],
        "total": len(entities),
    }


@router.get("/sessions/{session_id}/agent-context/{agent_name}")
async def get_agent_context(
    session_id: str,
    agent_name: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get agent-specific context from extraction results.

    Agents:
    - miguel: Migration Architect - tech stack insights
    - peter: Product Owner - user story material
    - felix: Feature Architect - technical architecture
    - quinn: Quality Inspector - quality insights
    """
    from app.services.orchestration.business_rule_workflow_integration import (
        RuleExtractionContext,
    )

    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(400, "Invalid session ID")

    # Get session
    session_result = await db.execute(
        select(HybridExtractionSession).where(HybridExtractionSession.id == session_uuid)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    # Get rules, workflows, entities
    rules_result = await db.execute(
        select(HybridExtractedRule).where(HybridExtractedRule.session_id == session_uuid)
    )
    rules = rules_result.scalars().all()

    workflows_result = await db.execute(
        select(HybridWorkflowCorrelation).where(HybridWorkflowCorrelation.session_id == session_uuid)
    )
    workflows = workflows_result.scalars().all()

    entities_result = await db.execute(
        select(HybridEntityMapping).where(HybridEntityMapping.session_id == session_uuid)
    )
    entities = entities_result.scalars().all()

    # Build extraction context
    validation_rules = [r.to_dict() for r in rules if r.rule_type == 'VALIDATION']
    authorization_rules = [r.to_dict() for r in rules if r.rule_type == 'AUTHORIZATION']
    data_access_rules = [r.to_dict() for r in rules if r.rule_type == 'DATA_ACCESS']
    business_logic_rules = [r.to_dict() for r in rules if r.rule_type not in ['VALIDATION', 'AUTHORIZATION', 'DATA_ACCESS']]

    context = RuleExtractionContext(
        total_rules=session.total_rules or 0,
        high_confidence_rules=session.high_confidence_rules or 0,
        average_confidence=session.average_confidence or 0.0,
        entities=[e.to_dict() for e in entities],
        workflows=[w.to_dict() for w in workflows],
        validation_rules=validation_rules,
        authorization_rules=authorization_rules,
        business_logic_rules=business_logic_rules,
        data_access_rules=data_access_rules,
        detected_languages=session.detected_languages or [],
        detected_frameworks=session.detected_frameworks or [],
        database_patterns=session.database_patterns or [],
        extraction_tier=session.extraction_tier,
        extraction_time_ms=session.total_ms or 0,
        extraction_cost_cents=session.total_cost_cents or 0.0,
        synthesis_result=session.synthesis_result,
        errors=session.errors or [],
        warnings=session.warnings or [],
    )

    return context.to_agent_context(agent_name)


@router.get("/project/{project_id}/sessions")
async def list_project_sessions(
    project_id: int,
    status: Optional[str] = Query(None, description="Filter by status"),
    workflow_type: Optional[str] = Query(None, description="Filter by workflow type"),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """List extraction sessions for a project."""
    query = select(HybridExtractionSession).where(
        HybridExtractionSession.project_id == project_id
    )

    if status:
        query = query.where(HybridExtractionSession.status == status)

    if workflow_type:
        query = query.where(HybridExtractionSession.workflow_type == workflow_type)

    query = query.order_by(HybridExtractionSession.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return {
        "sessions": [
            {
                "id": str(s.id),
                "source_path": s.source_path,
                "tier": s.extraction_tier,
                "status": s.status,
                "workflow_type": s.workflow_type,
                "total_rules": s.total_rules,
                "average_confidence": s.average_confidence,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ],
        "total": len(sessions),
        "offset": offset,
        "limit": limit,
    }


@router.get("/languages")
async def list_supported_languages():
    """List all supported programming languages for extraction."""
    return {
        "languages": [
            {"id": "python", "name": "Python", "tier": "AST", "extensions": [".py"]},
            {"id": "csharp", "name": "C#", "tier": "AST", "extensions": [".cs", ".aspx.cs", ".ascx.cs"]},
            {"id": "javascript", "name": "JavaScript", "tier": "AST", "extensions": [".js", ".jsx", ".mjs", ".cjs"]},
            {"id": "typescript", "name": "TypeScript", "tier": "AST", "extensions": [".ts", ".tsx"]},
            {"id": "java", "name": "Java", "tier": "AST", "extensions": [".java"]},
            {"id": "vbnet", "name": "VB.NET", "tier": "Regex", "extensions": [".vb", ".aspx.vb"]},
            {"id": "classic_asp", "name": "Classic ASP", "tier": "Regex", "extensions": [".asp", ".asa"]},
            {"id": "tsql", "name": "T-SQL (SQL Server)", "tier": "Regex", "extensions": [".sql", ".prc"]},
            {"id": "plsql", "name": "PL/SQL (Oracle)", "tier": "Regex", "extensions": [".pkg", ".pkb", ".pks", ".fnc", ".trg"]},
            {"id": "aspx", "name": "ASP.NET WebForms", "tier": "Regex", "extensions": [".aspx", ".ascx", ".master"]},
            {"id": "vb6", "name": "VB6 (Legacy)", "tier": "Regex", "extensions": [".frm", ".bas", ".cls", ".ctl", ".vbp"]},
            {"id": "php", "name": "PHP", "tier": "Regex", "extensions": [".php", ".phtml", ".inc"]},
        ],
        "total": 12,
    }


@router.get("/tiers")
async def list_extraction_tiers():
    """List available extraction tiers and their features."""
    return {
        "tiers": [
            {
                "id": "FREE",
                "name": "Free",
                "price_per_50k_loc": 0,
                "features": ["Static extraction only (AST/Regex)", "No LLM features"],
                "confidence": "60%",
                "deprecated": True,
            },
            {
                "id": "BASIC",
                "name": "Basic",
                "price_per_50k_loc": 5,
                "features": ["Static extraction", "LLM classification (Ollama)"],
                "confidence": "70%",
            },
            {
                "id": "STANDARD",
                "name": "Standard",
                "price_per_50k_loc": 25,
                "features": ["Static extraction", "LLM classification", "Comment extraction (Ollama, Groq, Gemini)"],
                "confidence": "80%",
                "recommended": True,
            },
            {
                "id": "PROFESSIONAL",
                "name": "Professional",
                "price_per_50k_loc": 75,
                "features": ["All STANDARD features", "Multi-LLM validation (+OpenAI)", "Optional human review"],
                "confidence": "90%",
            },
            {
                "id": "PREMIUM",
                "name": "Premium",
                "price_per_50k_loc": 150,
                "features": ["All PROFESSIONAL features", "Claude Opus synthesis", "Included human review"],
                "confidence": "95%",
            },
        ],
    }


@router.get("/rule-types")
async def list_rule_types():
    """List all business rule types."""
    return {
        "rule_types": [
            {"id": "VALIDATION", "description": "Input validation and data integrity checks"},
            {"id": "AUTHORIZATION", "description": "Permission and access control rules"},
            {"id": "SCHEDULING", "description": "Date/time and scheduling logic"},
            {"id": "WORKFLOW", "description": "Process and state transitions"},
            {"id": "BRANCHING", "description": "Decision logic and conditional paths"},
            {"id": "THRESHOLD", "description": "Limit and boundary checks"},
            {"id": "DATA_ACCESS", "description": "Database and data retrieval patterns"},
            {"id": "STATE_MANAGEMENT", "description": "State tracking and updates"},
            {"id": "ERROR_HANDLING", "description": "Exception and error processing"},
            {"id": "NAVIGATION", "description": "UI navigation and routing"},
            {"id": "CALCULATION", "description": "Business calculations and formulas"},
            {"id": "CONSTRAINT", "description": "Business constraints and invariants"},
            {"id": "DERIVATION", "description": "Derived values and computed properties"},
        ],
        "total": 13,
    }
