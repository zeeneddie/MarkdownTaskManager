"""
Hierarchical Story Extraction API - Week 84

API endpoints for hierarchical story extraction from code.
Supports bottom-up extraction at Function → Class → Module → System levels.

Endpoints:
- POST /extract/{project_id} - Start hierarchical extraction
- GET /sessions/{session_id} - Get extraction session
- GET /sessions/{session_id}/items - Get extracted items
- GET /sessions/{session_id}/hierarchy - Get item hierarchy
- GET /sessions/{session_id}/llm-context - Get LLM context string
- GET /project/{project_id}/sessions - List project sessions
- GET /templates - List available few-shot templates
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.hierarchical_extraction import (
    HierarchicalExtractionSession,
    ExtractedStoryItem,
    ExtractionLevelMetrics,
    ExtractionLevel,
    StoryItemType,
    StoryConfidenceLevel,
    ExtractionSessionStatus
)
from app.models.deep_extraction import ExtractionTier
from app.services.hierarchical_story_extraction_service import (
    HierarchicalStoryExtractionService,
    HierarchicalExtractionResult,
    FewShotTemplates,
    get_hierarchical_extraction_service,
)


router = APIRouter(prefix="/hierarchical-extraction", tags=["Hierarchical Extraction"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ExtractionRequest(BaseModel):
    """Request to start hierarchical extraction."""
    repository_path: str = Field(..., description="Path to repository")
    tier: str = Field(default="FREE", description="Extraction tier")
    levels: Optional[List[str]] = Field(
        default=None,
        description="Levels to extract: function, class, module, system"
    )
    max_files: int = Field(default=100, description="Maximum files to analyze")
    aggregation_id: Optional[str] = Field(
        default=None,
        description="Existing code analysis aggregation ID"
    )


class ExtractionResponse(BaseModel):
    """Response from extraction start."""
    session_id: str
    status: str
    message: str


class SessionResponse(BaseModel):
    """Extraction session details."""
    id: str
    project_id: int
    repository_path: str
    tier: str
    status: str
    primary_stack: Optional[str]
    totals: Dict[str, int]
    overall_confidence: float
    total_tokens: int
    total_cost_usd: float
    duration_ms: int
    created_at: str
    completed_at: Optional[str]
    errors: List[str]


class ExtractedItemResponse(BaseModel):
    """Extracted item details."""
    id: str
    item_type: str
    level: str
    title: str
    description: Optional[str]
    acceptance_criteria: List[str]
    source_file: Optional[str]
    confidence: float
    confidence_level: str
    complexity: str
    tags: List[str]
    story_points: Optional[int]
    function_points: Optional[float]
    children_count: int = 0


class HierarchyResponse(BaseModel):
    """Hierarchy view of extracted items."""
    epics: List[Dict[str, Any]]
    features: List[Dict[str, Any]]
    stories: List[Dict[str, Any]]
    tasks: List[Dict[str, Any]]
    orphans: List[Dict[str, Any]]  # Items without parents


class TemplateInfo(BaseModel):
    """Few-shot template info."""
    stack: str
    description: str
    example_count: int


# =============================================================================
# BACKGROUND TASK
# =============================================================================

async def run_extraction_task(
    session_id: UUID,
    project_id: int,
    repository_path: str,
    tier: ExtractionTier,
    levels: List[str],
    max_files: int,
    aggregation_id: Optional[UUID],
    db: AsyncSession,
):
    """Background task to run extraction."""
    try:
        # Update session to running
        await db.execute(
            update(HierarchicalExtractionSession)
            .where(HierarchicalExtractionSession.id == session_id)
            .values(
                status=ExtractionSessionStatus.RUNNING,
                started_at=datetime.utcnow()
            )
        )
        await db.commit()

        # Create service and run extraction
        service = get_hierarchical_extraction_service(db)

        # Convert level strings to enums
        level_enums = []
        for level in levels:
            try:
                level_enums.append(ExtractionLevel(level))
            except ValueError:
                pass

        result = await service.extract_hierarchical(
            project_id=project_id,
            repository_path=repository_path,
            tier=tier,
            levels=level_enums if level_enums else None,
            max_files=max_files,
            aggregation_id=aggregation_id,
        )

        # Store results
        await _store_extraction_results(db, session_id, result)

        # Update session to completed
        await db.execute(
            update(HierarchicalExtractionSession)
            .where(HierarchicalExtractionSession.id == session_id)
            .values(
                status=ExtractionSessionStatus.COMPLETED,
                completed_at=datetime.utcnow(),
                total_epics=result.total_epics,
                total_features=result.total_features,
                total_stories=result.total_stories,
                total_tasks=result.total_tasks,
                overall_confidence=result.overall_confidence,
                total_tokens=result.total_tokens,
                total_cost_usd=result.total_cost_usd,
                duration_ms=result.total_duration_ms,
                primary_stack=result.primary_stack,
                errors=result.errors,
            )
        )
        await db.commit()

    except Exception as e:
        # Update session to failed
        await db.execute(
            update(HierarchicalExtractionSession)
            .where(HierarchicalExtractionSession.id == session_id)
            .values(
                status=ExtractionSessionStatus.FAILED,
                completed_at=datetime.utcnow(),
                errors=[str(e)]
            )
        )
        await db.commit()


async def _store_extraction_results(
    db: AsyncSession,
    session_id: UUID,
    result: HierarchicalExtractionResult,
):
    """Store extracted items to database."""
    import uuid

    # Store level metrics
    for level_name, level_result in [
        (ExtractionLevel.FUNCTION, result.function_level),
        (ExtractionLevel.CLASS, result.class_level),
        (ExtractionLevel.MODULE, result.module_level),
        (ExtractionLevel.SYSTEM, result.system_level),
    ]:
        if level_result:
            metrics = ExtractionLevelMetrics(
                id=uuid.uuid4(),
                session_id=session_id,
                level=level_name,
                story_count=len(level_result.stories),
                feature_count=len(level_result.features),
                epic_count=len(level_result.epics),
                task_count=len(level_result.tasks),
                total_items=level_result.total_items,
                avg_confidence=level_result.avg_confidence,
                tokens_used=level_result.tokens_used,
                duration_ms=level_result.duration_ms,
                error_count=len(level_result.errors),
                errors=level_result.errors,
            )
            db.add(metrics)

            # Store items from this level
            for story in level_result.stories:
                item = ExtractedStoryItem(
                    id=uuid.UUID(story.id),
                    session_id=session_id,
                    item_type=StoryItemType(story.item_type.value),
                    extraction_level=level_name,
                    title=story.title,
                    description=story.description,
                    acceptance_criteria=story.acceptance_criteria,
                    source_file=story.source_file,
                    source_symbol=story.source_symbol,
                    confidence=story.confidence,
                    confidence_level=StoryConfidenceLevel(story.confidence_level.value),
                    complexity=story.complexity,
                    tags=story.tags,
                    story_points=story.story_points,
                    function_points=story.function_points,
                    extracted_by=story.extracted_by,
                )
                db.add(item)

            for feature in level_result.features:
                item = ExtractedStoryItem(
                    id=uuid.UUID(feature.id),
                    session_id=session_id,
                    item_type=StoryItemType.FEATURE,
                    extraction_level=level_name,
                    title=feature.title,
                    description=feature.description,
                    acceptance_criteria=feature.acceptance_criteria,
                    source_file=feature.source_file,
                    confidence=feature.confidence,
                    confidence_level=StoryConfidenceLevel(feature.confidence_level.value),
                    complexity=feature.complexity,
                    tags=feature.tags,
                    extracted_by=feature.extracted_by,
                )
                db.add(item)

            for epic in level_result.epics:
                item = ExtractedStoryItem(
                    id=uuid.UUID(epic.id),
                    session_id=session_id,
                    item_type=StoryItemType.EPIC,
                    extraction_level=level_name,
                    title=epic.title,
                    description=epic.description,
                    source_file=epic.source_file,
                    confidence=epic.confidence,
                    confidence_level=StoryConfidenceLevel(epic.confidence_level.value),
                    complexity=epic.complexity,
                    tags=epic.tags,
                    extracted_by=epic.extracted_by,
                )
                db.add(item)

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
    Start hierarchical story extraction for a project.

    Runs extraction in background and returns session ID immediately.
    Use GET /sessions/{session_id} to poll for status.
    """
    import uuid

    # Validate tier
    try:
        tier = ExtractionTier(request.tier.upper())
    except ValueError:
        tier = ExtractionTier.FREE

    # Parse levels
    levels = request.levels or ["function", "class", "module", "system"]

    # Parse aggregation ID
    aggregation_id = None
    if request.aggregation_id:
        try:
            aggregation_id = UUID(request.aggregation_id)
        except ValueError:
            pass

    # Create session
    session_id = uuid.uuid4()
    session = HierarchicalExtractionSession(
        id=session_id,
        project_id=project_id,
        repository_path=request.repository_path,
        tier=tier.value,
        status=ExtractionSessionStatus.PENDING,
        include_function_level="function" in levels,
        include_class_level="class" in levels,
        include_module_level="module" in levels,
        include_system_level="system" in levels,
        aggregation_id=aggregation_id,
    )
    db.add(session)
    await db.commit()

    # Start background task
    background_tasks.add_task(
        run_extraction_task,
        session_id=session_id,
        project_id=project_id,
        repository_path=request.repository_path,
        tier=tier,
        levels=levels,
        max_files=request.max_files,
        aggregation_id=aggregation_id,
        db=db,
    )

    return ExtractionResponse(
        session_id=str(session_id),
        status="pending",
        message="Extraction started. Poll GET /sessions/{session_id} for status.",
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
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
        select(HierarchicalExtractionSession)
        .where(HierarchicalExtractionSession.id == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(404, "Session not found")

    return SessionResponse(
        id=str(session.id),
        project_id=session.project_id,
        repository_path=session.repository_path,
        tier=session.tier,
        status=session.status.value,
        primary_stack=session.primary_stack,
        totals={
            "epics": session.total_epics,
            "features": session.total_features,
            "stories": session.total_stories,
            "tasks": session.total_tasks,
        },
        overall_confidence=session.overall_confidence,
        total_tokens=session.total_tokens,
        total_cost_usd=session.total_cost_usd,
        duration_ms=session.duration_ms,
        created_at=session.created_at.isoformat() if session.created_at else "",
        completed_at=session.completed_at.isoformat() if session.completed_at else None,
        errors=session.errors or [],
    )


@router.get("/sessions/{session_id}/items")
async def get_session_items(
    session_id: str,
    level: Optional[str] = Query(None, description="Filter by level"),
    item_type: Optional[str] = Query(None, description="Filter by type"),
    min_confidence: float = Query(0.0, description="Minimum confidence"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """Get extracted items from a session."""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(400, "Invalid session ID")

    query = select(ExtractedStoryItem).where(
        ExtractedStoryItem.session_id == session_uuid,
        ExtractedStoryItem.confidence >= min_confidence,
    )

    if level:
        try:
            level_enum = ExtractionLevel(level)
            query = query.where(ExtractedStoryItem.extraction_level == level_enum)
        except ValueError:
            pass

    if item_type:
        try:
            type_enum = StoryItemType(item_type)
            query = query.where(ExtractedStoryItem.item_type == type_enum)
        except ValueError:
            pass

    query = query.order_by(ExtractedStoryItem.confidence.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [item.to_dict() for item in items],
        "total": len(items),
        "offset": offset,
        "limit": limit,
    }


@router.get("/sessions/{session_id}/hierarchy")
async def get_session_hierarchy(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get hierarchical view of extracted items."""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(400, "Invalid session ID")

    result = await db.execute(
        select(ExtractedStoryItem)
        .where(ExtractedStoryItem.session_id == session_uuid)
        .order_by(ExtractedStoryItem.confidence.desc())
    )
    items = result.scalars().all()

    # Group by type
    epics = []
    features = []
    stories = []
    tasks = []
    orphans = []

    for item in items:
        item_dict = item.to_dict()

        # Count children
        child_count = len([i for i in items if i.parent_id == item.id])
        item_dict["children_count"] = child_count

        if item.item_type == StoryItemType.EPIC:
            epics.append(item_dict)
        elif item.item_type == StoryItemType.FEATURE:
            features.append(item_dict)
        elif item.item_type == StoryItemType.STORY:
            stories.append(item_dict)
        elif item.item_type == StoryItemType.TASK:
            tasks.append(item_dict)
        else:
            orphans.append(item_dict)

    return HierarchyResponse(
        epics=epics,
        features=features,
        stories=stories,
        tasks=tasks,
        orphans=orphans,
    )


@router.get("/sessions/{session_id}/llm-context")
async def get_llm_context(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get LLM-friendly context string for extracted items."""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(400, "Invalid session ID")

    # Get session
    result = await db.execute(
        select(HierarchicalExtractionSession)
        .where(HierarchicalExtractionSession.id == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(404, "Session not found")

    # Get items
    result = await db.execute(
        select(ExtractedStoryItem)
        .where(ExtractedStoryItem.session_id == session_uuid)
        .order_by(ExtractedStoryItem.confidence.desc())
    )
    items = result.scalars().all()

    # Build context string
    lines = [
        "## Hierarchical Story Extraction Results",
        "",
        f"**Repository**: {session.repository_path}",
        f"**Stack**: {session.primary_stack or 'Unknown'}",
        f"**Confidence**: {session.overall_confidence:.0%}",
        "",
        "### Summary",
        f"- **Epics**: {session.total_epics}",
        f"- **Features**: {session.total_features}",
        f"- **Stories**: {session.total_stories}",
        f"- **Tasks**: {session.total_tasks}",
        "",
    ]

    # Add top items by type
    epics = [i for i in items if i.item_type == StoryItemType.EPIC][:5]
    features = [i for i in items if i.item_type == StoryItemType.FEATURE][:10]
    stories = [i for i in items if i.item_type == StoryItemType.STORY][:15]

    if epics:
        lines.append("### Top Epics")
        for e in epics:
            lines.append(f"- **{e.title}** ({e.confidence:.0%} confidence)")
            if e.description:
                lines.append(f"  {e.description[:100]}...")
        lines.append("")

    if features:
        lines.append("### Top Features")
        for f in features:
            lines.append(f"- {f.title} ({f.confidence:.0%})")
        lines.append("")

    if stories:
        lines.append("### Top Stories")
        for s in stories:
            lines.append(f"- {s.title}")
        lines.append("")

    return {
        "context": "\n".join(lines),
        "token_estimate": len("\n".join(lines)) // 4,  # Rough token estimate
    }


@router.get("/project/{project_id}/sessions")
async def list_project_sessions(
    project_id: int,
    status: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """List extraction sessions for a project."""
    query = select(HierarchicalExtractionSession).where(
        HierarchicalExtractionSession.project_id == project_id
    )

    if status:
        try:
            status_enum = ExtractionSessionStatus(status)
            query = query.where(HierarchicalExtractionSession.status == status_enum)
        except ValueError:
            pass

    query = query.order_by(HierarchicalExtractionSession.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return {
        "sessions": [
            {
                "id": str(s.id),
                "tier": s.tier,
                "status": s.status.value,
                "primary_stack": s.primary_stack,
                "total_stories": s.total_stories,
                "overall_confidence": s.overall_confidence,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ],
        "total": len(sessions),
        "offset": offset,
        "limit": limit,
    }


@router.get("/templates")
async def list_templates():
    """List available few-shot templates."""
    templates = []

    for stack in FewShotTemplates.get_all_stacks():
        template = FewShotTemplates.get_template_for_stack(stack)
        # Count examples (rough estimate based on "### Example" occurrences)
        example_count = template.count("### Example")

        templates.append(TemplateInfo(
            stack=stack,
            description=f"Few-shot template for {stack.title()} projects",
            example_count=example_count,
        ))

    return {"templates": templates}


@router.get("/templates/{stack}")
async def get_template(stack: str):
    """Get specific few-shot template."""
    if stack.lower() not in FewShotTemplates.get_all_stacks():
        raise HTTPException(404, f"Template not found for stack: {stack}")

    template = FewShotTemplates.get_template_for_stack(stack)

    return {
        "stack": stack,
        "template": template,
        "example_count": template.count("### Example"),
    }


@router.get("/levels")
async def list_levels():
    """List available extraction levels."""
    return {
        "levels": [
            {
                "name": "function",
                "description": "Individual functions and methods",
                "output_types": ["story", "task"],
            },
            {
                "name": "class",
                "description": "Classes and their responsibilities",
                "output_types": ["feature", "story"],
            },
            {
                "name": "module",
                "description": "Modules and integration points",
                "output_types": ["epic", "feature"],
            },
            {
                "name": "system",
                "description": "System-wide features and cross-cutting concerns",
                "output_types": ["product_area", "cross_cutting", "epic"],
            },
        ]
    }


# =============================================================================
# WEEK 125: CIRA INTEGRATION ENDPOINTS
# =============================================================================

class CiRAExtractionRequest(BaseModel):
    """Request for extraction with CiRA causal analysis."""
    repository_path: str = Field(..., description="Path to repository")
    tier: str = Field(default="FREE", description="Extraction tier")
    levels: Optional[List[str]] = Field(
        default=None,
        description="Levels to extract: function, class, module, system"
    )
    max_files: int = Field(default=100, description="Maximum files to analyze")
    aggregation_id: Optional[str] = Field(
        default=None,
        description="Existing code analysis aggregation ID"
    )
    include_cira_analysis: bool = Field(
        default=True,
        description="Week 125: Enable CiRA causal dependency analysis"
    )
    generate_test_suggestions: bool = Field(
        default=True,
        description="Week 125: Generate test suggestions from causal analysis"
    )


class CausalDependencyResponse(BaseModel):
    """Response containing CiRA causal dependency analysis."""
    session_id: str
    cira_session_id: Optional[str]
    total_causal_sentences: int
    total_relations: int
    avg_confidence: float
    has_graph: bool
    node_count: int
    edge_count: int
    critical_path: List[str]
    root_nodes: List[str]
    leaf_nodes: List[str]
    suggested_sprint_order: List[str]
    cycles_detected: int
    relations_by_story: Dict[str, List[Dict[str, str]]]


class SprintOrderResponse(BaseModel):
    """Suggested sprint ordering based on causal analysis."""
    session_id: str
    suggested_order: List[Dict[str, Any]]
    total_stories: int
    root_nodes: List[str]
    critical_path: List[str]
    cycles_detected: int
    reasoning: str


class TraceabilityMatrixResponse(BaseModel):
    """Traceability matrix with causal links."""
    session_id: str
    cira_session_id: Optional[str]
    total_links: int
    causal_links: int
    dependency_links: int
    blocking_links: int
    coverage_percentage: float
    links: List[Dict[str, Any]]
    suggested_sprint_order: List[str]


@router.post("/extract-with-cira/{project_id}", response_model=ExtractionResponse)
async def start_extraction_with_cira(
    project_id: int,
    request: CiRAExtractionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Week 125: Start hierarchical extraction with CiRA causal analysis.

    Extends standard extraction with:
    - Automatic causal dependency detection using CiRA
    - Dependency graph building (DAG with cycle detection)
    - Suggested sprint ordering based on causal relationships
    - Test suggestions based on causal analysis
    """
    import uuid

    # Validate tier
    try:
        tier = ExtractionTier(request.tier.upper())
    except ValueError:
        tier = ExtractionTier.FREE

    # Parse levels
    levels = request.levels or ["function", "class", "module", "system"]

    # Parse aggregation ID
    aggregation_id = None
    if request.aggregation_id:
        try:
            aggregation_id = UUID(request.aggregation_id)
        except ValueError:
            pass

    # Create session
    session_id = uuid.uuid4()
    session = HierarchicalExtractionSession(
        id=session_id,
        project_id=project_id,
        repository_path=request.repository_path,
        tier=tier.value,
        status=ExtractionSessionStatus.PENDING,
        include_function_level="function" in levels,
        include_class_level="class" in levels,
        include_module_level="module" in levels,
        include_system_level="system" in levels,
        aggregation_id=aggregation_id,
    )
    db.add(session)
    await db.commit()

    # Start background task with CiRA analysis
    background_tasks.add_task(
        run_extraction_with_cira_task,
        session_id=session_id,
        project_id=project_id,
        repository_path=request.repository_path,
        tier=tier,
        levels=levels,
        max_files=request.max_files,
        aggregation_id=aggregation_id,
        include_cira_analysis=request.include_cira_analysis,
        generate_test_suggestions=request.generate_test_suggestions,
        db=db,
    )

    return ExtractionResponse(
        session_id=str(session_id),
        status="pending",
        message="Extraction with CiRA analysis started. Poll GET /sessions/{session_id} for status.",
    )


async def run_extraction_with_cira_task(
    session_id: UUID,
    project_id: int,
    repository_path: str,
    tier: ExtractionTier,
    levels: List[str],
    max_files: int,
    aggregation_id: Optional[UUID],
    include_cira_analysis: bool,
    generate_test_suggestions: bool,
    db: AsyncSession,
):
    """Week 125: Background task for extraction with CiRA analysis."""
    try:
        # Update session to running
        await db.execute(
            update(HierarchicalExtractionSession)
            .where(HierarchicalExtractionSession.id == session_id)
            .values(
                status=ExtractionSessionStatus.RUNNING,
                started_at=datetime.utcnow()
            )
        )
        await db.commit()

        # Create service and run extraction
        service = get_hierarchical_extraction_service(db)

        # Convert level strings to enums
        level_enums = []
        for level in levels:
            try:
                level_enums.append(ExtractionLevel(level))
            except ValueError:
                pass

        result = await service.extract_hierarchical(
            project_id=project_id,
            repository_path=repository_path,
            tier=tier,
            levels=level_enums if level_enums else None,
            max_files=max_files,
            aggregation_id=aggregation_id,
            include_cira_analysis=include_cira_analysis,
        )

        # Store results
        await _store_extraction_results(db, session_id, result)

        # Store CiRA causal dependencies if available
        cira_session_id = None
        if result.causal_dependencies:
            cira_session_id = result.causal_dependencies.session_id

        # Update session to completed
        await db.execute(
            update(HierarchicalExtractionSession)
            .where(HierarchicalExtractionSession.id == session_id)
            .values(
                status=ExtractionSessionStatus.COMPLETED,
                completed_at=datetime.utcnow(),
                total_epics=result.total_epics,
                total_features=result.total_features,
                total_stories=result.total_stories,
                total_tasks=result.total_tasks,
                overall_confidence=result.overall_confidence,
                total_tokens=result.total_tokens,
                total_cost_usd=result.total_cost_usd,
                duration_ms=result.total_duration_ms,
                primary_stack=result.primary_stack,
                errors=result.errors,
            )
        )
        await db.commit()

    except Exception as e:
        # Update session to failed
        await db.execute(
            update(HierarchicalExtractionSession)
            .where(HierarchicalExtractionSession.id == session_id)
            .values(
                status=ExtractionSessionStatus.FAILED,
                completed_at=datetime.utcnow(),
                errors=[str(e)]
            )
        )
        await db.commit()


@router.get("/sessions/{session_id}/causal-dependencies", response_model=CausalDependencyResponse)
async def get_causal_dependencies(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Week 125: Get CiRA causal dependency analysis for an extraction session.

    Returns:
    - Causal sentence count and relations
    - Dependency graph metrics (nodes, edges, cycles)
    - Critical path through dependencies
    - Root nodes (no dependencies) and leaf nodes (no dependents)
    - Suggested sprint ordering
    """
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(400, "Invalid session ID")

    # Get session
    result = await db.execute(
        select(HierarchicalExtractionSession)
        .where(HierarchicalExtractionSession.id == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(404, "Session not found")

    if session.status != ExtractionSessionStatus.COMPLETED:
        raise HTTPException(400, "Session not completed. Wait for extraction to finish.")

    # Re-run CiRA analysis on session items
    service = get_hierarchical_extraction_service(db)

    # Get all stories from session
    items_result = await db.execute(
        select(ExtractedStoryItem)
        .where(ExtractedStoryItem.session_id == session_uuid)
    )
    items = items_result.scalars().all()

    # Create mock result structure for CiRA analysis
    stories = [item.to_dict() for item in items]

    # Use CiRA service to analyze
    from app.services.cira_service import CiRAService
    cira_service = CiRAService(db)

    # Collect sentences from stories
    sentences = []
    for story in stories:
        if story.get("description"):
            sentences.append(story["description"])
        for ac in story.get("acceptance_criteria", []):
            sentences.append(ac)

    if not sentences:
        return CausalDependencyResponse(
            session_id=session_id,
            cira_session_id=None,
            total_causal_sentences=0,
            total_relations=0,
            avg_confidence=0.0,
            has_graph=False,
            node_count=0,
            edge_count=0,
            critical_path=[],
            root_nodes=[],
            leaf_nodes=[],
            suggested_sprint_order=[],
            cycles_detected=0,
            relations_by_story={},
        )

    # Create CiRA session and analyze
    cira_session = await cira_service.create_session(
        project_id=session.project_id,
        source_type="hierarchical_extraction",
        source_id=str(session_uuid),
    )

    analysis_result = await cira_service.analyze_sentences(
        session_id=cira_session["session_id"],
        sentences=sentences,
    )

    # Build dependency graph
    graph_result = await cira_service.build_dependency_graph(
        session_id=cira_session["session_id"],
    )

    # Map relations to stories
    relations_by_story: Dict[str, List[Dict[str, str]]] = {}
    for relation in analysis_result.get("relations", []):
        story_id = relation.get("source_story_id", "unknown")
        if story_id not in relations_by_story:
            relations_by_story[story_id] = []
        relations_by_story[story_id].append({
            "cause": relation.get("cause", ""),
            "effect": relation.get("effect", ""),
            "confidence": str(relation.get("confidence", 0)),
        })

    return CausalDependencyResponse(
        session_id=session_id,
        cira_session_id=cira_session["session_id"],
        total_causal_sentences=analysis_result.get("causal_sentence_count", 0),
        total_relations=len(analysis_result.get("relations", [])),
        avg_confidence=analysis_result.get("avg_confidence", 0.0),
        has_graph=graph_result.get("has_graph", False),
        node_count=graph_result.get("node_count", 0),
        edge_count=graph_result.get("edge_count", 0),
        critical_path=graph_result.get("critical_path", []),
        root_nodes=graph_result.get("root_nodes", []),
        leaf_nodes=graph_result.get("leaf_nodes", []),
        suggested_sprint_order=graph_result.get("topological_order", []),
        cycles_detected=graph_result.get("cycles_detected", 0),
        relations_by_story=relations_by_story,
    )


@router.get("/sessions/{session_id}/sprint-order", response_model=SprintOrderResponse)
async def get_sprint_order(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Week 125: Get suggested sprint ordering based on causal analysis.

    Returns stories in dependency order, with root nodes first
    and respecting causal chains.
    """
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(400, "Invalid session ID")

    # Get causal dependencies first
    causal_deps = await get_causal_dependencies(session_id, db)

    # Get all stories
    items_result = await db.execute(
        select(ExtractedStoryItem)
        .where(ExtractedStoryItem.session_id == session_uuid)
        .order_by(ExtractedStoryItem.confidence.desc())
    )
    items = items_result.scalars().all()

    # Build ordered list based on topological order
    ordered_stories = []
    order_map = {story_id: idx for idx, story_id in enumerate(causal_deps.suggested_sprint_order)}

    for item in items:
        item_dict = item.to_dict()
        item_dict["sprint_order_position"] = order_map.get(str(item.id), len(items))
        item_dict["is_root"] = str(item.id) in causal_deps.root_nodes
        item_dict["is_critical_path"] = str(item.id) in causal_deps.critical_path
        ordered_stories.append(item_dict)

    # Sort by sprint order position
    ordered_stories.sort(key=lambda x: x["sprint_order_position"])

    reasoning = _build_sprint_order_reasoning(causal_deps, len(items))

    return SprintOrderResponse(
        session_id=session_id,
        suggested_order=ordered_stories,
        total_stories=len(items),
        root_nodes=causal_deps.root_nodes,
        critical_path=causal_deps.critical_path,
        cycles_detected=causal_deps.cycles_detected,
        reasoning=reasoning,
    )


def _build_sprint_order_reasoning(causal_deps: CausalDependencyResponse, total_stories: int) -> str:
    """Build human-readable reasoning for sprint order."""
    parts = []

    if causal_deps.root_nodes:
        parts.append(
            f"Start with {len(causal_deps.root_nodes)} root node(s) that have no dependencies."
        )

    if causal_deps.critical_path:
        parts.append(
            f"Critical path contains {len(causal_deps.critical_path)} stories - prioritize these."
        )

    if causal_deps.cycles_detected > 0:
        parts.append(
            f"Warning: {causal_deps.cycles_detected} circular dependencies detected. "
            "Consider breaking these cycles by splitting stories."
        )

    if causal_deps.total_relations > 0:
        coverage = (causal_deps.total_relations / max(total_stories, 1)) * 100
        parts.append(
            f"Found {causal_deps.total_relations} causal relations "
            f"({coverage:.0f}% story coverage)."
        )
    else:
        parts.append(
            "No causal relations detected. Stories can be implemented in parallel."
        )

    return " ".join(parts) if parts else "No specific ordering constraints found."


@router.get("/sessions/{session_id}/traceability-matrix", response_model=TraceabilityMatrixResponse)
async def get_traceability_matrix(
    session_id: str,
    include_causal_links: bool = Query(True, description="Include CiRA causal links"),
    db: AsyncSession = Depends(get_db),
):
    """
    Week 125: Get traceability matrix with causal links.

    Combines code-to-story traceability with CiRA causal dependencies.
    """
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(400, "Invalid session ID")

    # Get session
    result = await db.execute(
        select(HierarchicalExtractionSession)
        .where(HierarchicalExtractionSession.id == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(404, "Session not found")

    # Get all items
    items_result = await db.execute(
        select(ExtractedStoryItem)
        .where(ExtractedStoryItem.session_id == session_uuid)
    )
    items = items_result.scalars().all()

    # Build basic traceability links
    links = []
    for item in items:
        if item.source_file:
            links.append({
                "id": str(item.id),
                "type": "code_to_story",
                "source": item.source_file,
                "target": item.title,
                "confidence": item.confidence,
            })

    causal_links = 0
    dependency_links = 0
    blocking_links = 0
    cira_session_id = None
    suggested_sprint_order = []

    if include_causal_links:
        # Get CiRA analysis
        try:
            causal_deps = await get_causal_dependencies(session_id, db)
            cira_session_id = causal_deps.cira_session_id
            suggested_sprint_order = causal_deps.suggested_sprint_order

            # Add causal links to matrix
            for story_id, relations in causal_deps.relations_by_story.items():
                for relation in relations:
                    link_type = "causal"
                    if "block" in relation.get("cause", "").lower():
                        link_type = "blocking"
                        blocking_links += 1
                    elif "depend" in relation.get("cause", "").lower():
                        link_type = "dependency"
                        dependency_links += 1
                    else:
                        causal_links += 1

                    links.append({
                        "id": f"{story_id}-{len(links)}",
                        "type": link_type,
                        "source": relation.get("cause", ""),
                        "target": relation.get("effect", ""),
                        "confidence": float(relation.get("confidence", 0)),
                        "story_id": story_id,
                    })
        except Exception:
            # CiRA analysis failed, continue with basic traceability
            pass

    total_links = len(links)
    coverage = (len(items) / max(total_links, 1)) * 100 if total_links > 0 else 0.0

    return TraceabilityMatrixResponse(
        session_id=session_id,
        cira_session_id=cira_session_id,
        total_links=total_links,
        causal_links=causal_links,
        dependency_links=dependency_links,
        blocking_links=blocking_links,
        coverage_percentage=min(100.0, coverage),
        links=links,
        suggested_sprint_order=suggested_sprint_order,
    )
