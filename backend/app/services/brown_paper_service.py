"""
Brown Paper Service

Week 57 Day 2: Reverse-engineer business logic from existing code and documentation.

Brown Paper is the counterpart to Green Paper:
- Green Paper: Top-down (Vision -> Requirements -> Epics)
- Brown Paper: Bottom-up (Code -> Analysis -> Epics)

Both produce the same unified output:
- Constitution (project charter)
- Specification (technical design)
- Epics/Features/Stories/Tasks (project backlog)

Architecture:
    1. Load Application from Application Registry
    2. Analyze code structure (modules, classes, functions)
    3. Analyze documentation (README, docs/, comments)
    4. Extract business domains from code patterns
    5. Generate Constitution from analysis
    6. Generate Epics from identified domains
"""

import logging
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal

# Week 143: Vector DB Integration
from app.services.chroma_service import ChromaService

# Week 145: MarQed Session Database Models
from app.models.marqed_session import (
    MarQedSession as MarQedSessionDB,
    MarQedAnswer as MarQedAnswerDB,
    MarQedSessionEvent as MarQedSessionEventDB,
    MarQedSessionStatus,
    MarQedWorkflowType,
    MarQedEventType,
)

from app.services.application_registry_service import (
    get_application_registry_service,
    Application,
    ApplicationComponent,
    ComponentType,
)

# Brown Paper Database Models - for persistence
from app.models.brown_paper import (
    BrownPaperSession as BrownPaperSessionDB,
    BrownPaperAnalysis as BrownPaperAnalysisDB,
    BrownPaperConstitution as BrownPaperConstitutionDB,
    BrownPaperEpic as BrownPaperEpicDB,
    BrownPaperSessionStatus as DBSessionStatus,
)
from app.models.application import Application as ApplicationDB
from app.services.brown_paper_estimation_service import (
    get_brown_paper_estimation_service,
    BrownPaperEstimationService,
)

# Phase 20: Brown Paper Enhanced - Integration Services
from app.services.dependency_graph_service import DependencyGraphService
from app.services.code_analysis_aggregator_service import CodeAnalysisAggregatorService
from app.services.layered_analysis_service import LayeredAnalysisService
from app.services.hierarchical_story_extraction_service import HierarchicalStoryExtractionService
from app.services.deep_extraction_service import DeepExtractionService

# Week 145-146: Stability Analysis Integration
from app.services.stability.brown_paper_integration import (
    get_brown_paper_stability_integration,
)

# Enhanced analysis models
from app.models.brown_paper_enhanced import (
    EnhancedAnalysisTier,
    EnhancedAnalysisPhase,
    EnhancedAnalysisRequest,
    EnhancedAnalysisOptions,
    EnhancedAnalysisResponse,
    EnhancedAnalysisSummary,
    Phase1Result,
    Phase2Result,
    Phase3Result,
    Phase4Result,
    Phase5Result,
    TIER_PHASES,
    TIER_CONFIDENCE_TARGETS,
    TIER_PROVIDERS,
)

# Fase 24.7: Async refactoring utilities
import warnings
from app.services.async_helpers import deprecated_sync_wrapper, log_deprecated_sync_call

# Week 158: Epic Searchers for journey-based and folder-based epic detection
from app.services.epic_searchers import (
    CombinedEpicSearcher,
    CombinedSearchConfig,
    DetectedEpic,
)

# Week 159: Business Logic Extraction - PVA Implementation
from app.services.business_domain_extractor_service import (
    BusinessDomainExtractorService,
    BusinessDomainCandidate,
    BusinessDomainExtractionResult,
    get_business_domain_extractor,
)
from app.services.business_driven_story_generator_service import (
    BusinessDrivenStoryGeneratorService,
    StoryGenerationResult,
    get_business_driven_story_generator,
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

class BrownPaperStatus(Enum):
    """Status of a Brown Paper session."""
    SCANNING = "scanning"           # Analyzing code structure
    ANALYZING = "analyzing"         # Extracting domains
    GENERATING = "generating"       # Creating constitution/epics
    REVIEW = "review"               # Awaiting human review
    APPROVED = "approved"           # Ready for implementation
    REJECTED = "rejected"           # Needs rework


@dataclass
class CodeModule:
    """Represents a code module/package discovered during analysis."""
    name: str
    path: str
    module_type: str  # service, repository, model, controller, util, etc.
    description: str
    classes: List[str]
    functions: List[str]
    dependencies: List[str]
    estimated_complexity: str  # low, medium, high
    business_domain: Optional[str] = None


@dataclass
class DocumentationInsight:
    """Insight extracted from documentation."""
    source: str  # README.md, docs/architecture.md, etc.
    section: str
    content: str
    insight_type: str  # purpose, feature, constraint, requirement, etc.
    confidence: float  # 0.0 - 1.0


@dataclass
class BusinessDomain:
    """A business domain identified from code analysis."""
    name: str
    description: str
    modules: List[str]  # Module paths
    entities: List[str]  # Entity/model names
    use_cases: List[str]  # Identified use cases
    complexity: str  # low, medium, high, very_high
    priority: int  # 1-5, higher = more important


@dataclass
class BrownPaperAnalysis:
    """Complete analysis result from Brown Paper workflow."""
    application_id: int
    application_name: str
    root_path: str

    # Code analysis
    modules: List[CodeModule]
    total_classes: int
    total_functions: int
    primary_patterns: List[str]  # MVC, DDD, microservices, etc.

    # Documentation analysis
    doc_insights: List[DocumentationInsight]
    readme_summary: Optional[str]

    # Domain extraction
    domains: List[BusinessDomain]

    # Generated outputs
    constitution: Optional[Dict[str, Any]] = None
    epics: List[Dict[str, Any]] = field(default_factory=list)

    # Stability Analysis (Week 145-146)
    stability_analysis: Optional[Dict[str, Any]] = None

    # Metadata
    analysis_time_ms: int = 0
    status: BrownPaperStatus = BrownPaperStatus.SCANNING


@dataclass
class BrownPaperSession:
    """A Brown Paper session tracking progress."""
    id: str
    application_id: int
    status: BrownPaperStatus
    analysis: Optional[BrownPaperAnalysis]
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    # Phase 20: Enhanced analysis fields
    project_path: Optional[str] = None
    project_name: Optional[str] = None
    enhanced_analysis: Optional[Dict[str, Any]] = None


# ============================================================================
# CODE ANALYSIS PATTERNS
# ============================================================================

# Patterns to identify code module types
MODULE_TYPE_PATTERNS = {
    "service": [r"service", r"svc", r"_service\.py$", r"Service\.", r"Service\.vb$"],
    "repository": [r"repository", r"repo", r"_repository\.py$", r"Repository\.", r"DB\.vb$"],
    "model": [r"model", r"entity", r"_model\.py$", r"Model\.", r"Entity\.vb$"],
    "controller": [r"controller", r"handler", r"_controller\.py$", r"Controller\.", r"routes", r"Page\.vb$"],
    "api": [r"api", r"endpoint", r"_api\.py$", r"Api\.", r"WebService\.vb$", r"asmx"],
    "util": [r"util", r"helper", r"_util\.py$", r"Util\.", r"Helper\.vb$"],
    "config": [r"config", r"settings", r"_config\.py$", r"AppSettings", r"Web\.config"],
    "test": [r"test", r"spec", r"_test\.py$", r"Test\.", r"Tests\.vb$"],
    "migration": [r"migration", r"alembic", r"_migration\.py$", r"Database\.vb$"],
    "form": [r"Form\.vb$", r"\.aspx", r"UserControl"],  # VB.NET forms
    "data_access": [r"DataAccess", r"DAL", r"Data\.vb$"],  # VB.NET data layer
}

# Patterns to identify architectural patterns
ARCHITECTURE_PATTERNS = {
    "ddd": ["domain", "aggregate", "value_object", "repository", "entity"],
    "mvc": ["model", "view", "controller"],
    "layered": ["presentation", "application", "domain", "infrastructure"],
    "microservices": ["service", "gateway", "discovery", "config"],
    "cqrs": ["command", "query", "handler", "event"],
    "hexagonal": ["port", "adapter", "application", "domain"],
}

# Documentation insight patterns
DOC_PATTERNS = {
    "purpose": [r"(?:this|the)\s+(?:project|application|system)\s+(?:is|provides|enables)", r"^#\s+\w+"],
    "feature": [r"features?:", r"capabilities:", r"supports?:", r"enables?:"],
    "constraint": [r"limitations?:", r"constraints?:", r"requirements?:"],
    "installation": [r"install(?:ation)?:", r"setup:", r"getting started:"],
    "architecture": [r"architecture:", r"design:", r"structure:"],
}


# ============================================================================
# BROWN PAPER SERVICE
# ============================================================================

class BrownPaperService:
    """
    Service for reverse-engineering business logic from code.

    Flow:
    1. Load Application from Application Registry
    2. Scan code structure (modules, classes, functions)
    3. Analyze documentation (README, docs/, docstrings)
    4. Extract business domains
    5. Generate Constitution (project charter)
    6. Generate Epics from domains
    """

    def __init__(self):
        self._sessions: Dict[str, BrownPaperSession] = {}
        self._registry = None

    def _get_registry(self):
        """Lazy load application registry."""
        if self._registry is None:
            self._registry = get_application_registry_service()
        return self._registry

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    async def start_session(self, application_id: int) -> BrownPaperSession:
        """Start a new Brown Paper analysis session.

        Gets application info from registry and sets project_path for enhanced analysis.
        Persists to database for durability.
        """
        session_id = str(uuid.uuid4())

        # Get application info from registry for project_path
        project_path = None
        project_name = None
        try:
            app_service = get_application_registry_service()
            application = app_service.get_application(application_id)
            if application:
                project_path = application.root_path
                project_name = application.name
                logger.info(f"Application found: {project_name} at {project_path}")
        except Exception as e:
            logger.warning(f"Could not get application {application_id} from registry: {e}")

        # Create in-memory session object
        session = BrownPaperSession(
            id=session_id,
            application_id=application_id,
            status=BrownPaperStatus.SCANNING,
            analysis=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            project_path=project_path,
            project_name=project_name,
        )

        # Persist to database
        try:
            async with AsyncSessionLocal() as db:
                db_session = BrownPaperSessionDB(
                    id=uuid.UUID(session_id),
                    application_id=application_id,
                    application_name=project_name or f"App-{application_id}",
                    root_path=project_path or "",
                    status=DBSessionStatus.SCANNING,
                    modules_count=0,
                    domains_count=0,
                )
                db.add(db_session)
                await db.commit()
                logger.info(f"Persisted Brown Paper session {session_id} to database")
        except Exception as e:
            logger.error(f"Failed to persist session to database: {e}")
            # Continue with in-memory session even if DB fails

        self._sessions[session_id] = session
        logger.info(f"Started Brown Paper session {session_id} for application {application_id}")

        return session

    @deprecated_sync_wrapper("get_session", "26.0")
    def get_session_sync(self, session_id: str) -> Optional[BrownPaperSession]:
        """Get a Brown Paper session by ID (sync, from cache only).

        DEPRECATED: Use get_session() (async) instead. This sync method will be
        removed in v26.0. Only accesses in-memory cache, does not load from DB.
        """
        return self._sessions.get(session_id)

    async def get_session(self, session_id: str) -> Optional[BrownPaperSession]:
        """Get a Brown Paper session by ID (async, with database fallback).

        Primary async method - loads from cache first, falls back to database.
        This is the recommended method for all new code.
        """
        # Check cache first
        if session_id in self._sessions:
            return self._sessions[session_id]

        # Load from database
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(BrownPaperSessionDB).where(
                        BrownPaperSessionDB.id == uuid.UUID(session_id)
                    )
                )
                db_session = result.scalar_one_or_none()

                if db_session:
                    # Also load analysis if exists
                    analysis_result = await db.execute(
                        select(BrownPaperAnalysisDB).where(
                            BrownPaperAnalysisDB.session_id == db_session.id
                        )
                    )
                    db_analysis = analysis_result.scalar_one_or_none()

                    # Convert to in-memory object
                    analysis = None
                    if db_analysis:
                        analysis = BrownPaperAnalysis(
                            application_id=db_session.application_id,
                            application_name=db_session.application_name,
                            root_path=db_session.root_path,
                            modules=[CodeModule(**m) if isinstance(m, dict) else m for m in (db_analysis.modules or [])],
                            total_classes=db_session.classes_count or 0,
                            total_functions=db_session.functions_count or 0,
                            primary_patterns=db_analysis.primary_patterns or [],
                            doc_insights=db_analysis.doc_insights or [],
                            readme_summary=db_analysis.readme_summary,
                            domains=[BusinessDomain(**d) if isinstance(d, dict) else d for d in (db_analysis.domains or [])],
                            analysis_time_ms=db_analysis.analysis_time_ms or 0,
                            status=db_session.status,
                        )

                    session = BrownPaperSession(
                        id=str(db_session.id),
                        application_id=db_session.application_id,
                        status=BrownPaperStatus(db_session.status) if db_session.status in [s.value for s in BrownPaperStatus] else BrownPaperStatus.SCANNING,
                        analysis=analysis,
                        created_at=db_session.created_at,
                        updated_at=db_session.updated_at,
                        project_path=db_session.root_path,
                        project_name=db_session.application_name,
                    )

                    # Add to cache
                    self._sessions[session_id] = session
                    return session

        except Exception as e:
            logger.error(f"Failed to load session {session_id} from database: {e}")

        return None

    @deprecated_sync_wrapper("list_sessions", "26.0")
    def list_sessions_sync(self, application_id: Optional[int] = None) -> List[BrownPaperSession]:
        """List all Brown Paper sessions (sync, from cache only).

        DEPRECATED: Use list_sessions() (async) instead. This sync method will be
        removed in v26.0. Only accesses in-memory cache, does not load from DB.
        """
        sessions = list(self._sessions.values())
        if application_id is not None:
            sessions = [s for s in sessions if s.application_id == application_id]
        return sorted(sessions, key=lambda s: s.created_at, reverse=True)

    async def list_sessions(self, application_id: Optional[int] = None) -> List[BrownPaperSession]:
        """List all Brown Paper sessions (async, from database).

        Primary async method - loads from database with cache integration.
        This is the recommended method for all new code.
        """
        try:
            async with AsyncSessionLocal() as db:
                query = select(BrownPaperSessionDB)
                if application_id is not None:
                    query = query.where(BrownPaperSessionDB.application_id == application_id)
                query = query.order_by(BrownPaperSessionDB.created_at.desc())

                result = await db.execute(query)
                db_sessions = result.scalars().all()

                sessions = []
                for db_session in db_sessions:
                    session_id = str(db_session.id)

                    # Check cache first
                    if session_id in self._sessions:
                        sessions.append(self._sessions[session_id])
                    else:
                        # Create minimal session object (without full analysis)
                        session = BrownPaperSession(
                            id=session_id,
                            application_id=db_session.application_id,
                            status=BrownPaperStatus(db_session.status) if db_session.status in [s.value for s in BrownPaperStatus] else BrownPaperStatus.SCANNING,
                            analysis=None,  # Load on demand
                            created_at=db_session.created_at,
                            updated_at=db_session.updated_at,
                            project_path=db_session.root_path,
                            project_name=db_session.application_name,
                            modules_count=db_session.modules_count or 0,
                            domains_count=db_session.domains_count or 0,
                        )
                        sessions.append(session)

                return sessions

        except Exception as e:
            logger.error(f"Failed to list sessions from database: {e}")
            # Fallback to cache (sync, no deprecation warning in this case)
            sessions = list(self._sessions.values())
            if application_id is not None:
                sessions = [s for s in sessions if s.application_id == application_id]
            return sorted(sessions, key=lambda s: s.created_at, reverse=True)

    async def _persist_analysis_to_db(
        self,
        session_id: str,
        session: BrownPaperSession,
        analysis: BrownPaperAnalysis
    ) -> None:
        """Persist analysis results to database."""
        try:
            async with AsyncSessionLocal() as db:
                # Update session summary
                await db.execute(
                    update(BrownPaperSessionDB)
                    .where(BrownPaperSessionDB.id == uuid.UUID(session_id))
                    .values(
                        status=session.status.value if hasattr(session.status, 'value') else session.status,
                        modules_count=len(analysis.modules),
                        domains_count=len(analysis.domains),
                        classes_count=analysis.total_classes,
                        functions_count=analysis.total_functions,
                        patterns_detected=analysis.primary_patterns,
                        updated_at=datetime.now(timezone.utc),
                        generation_metadata={
                            "analysis_time_ms": analysis.analysis_time_ms,
                        }
                    )
                )

                # Check if analysis record exists
                result = await db.execute(
                    select(BrownPaperAnalysisDB).where(
                        BrownPaperAnalysisDB.session_id == uuid.UUID(session_id)
                    )
                )
                existing_analysis = result.scalar_one_or_none()

                # Convert modules and domains to JSON-serializable format
                modules_json = [
                    {
                        "name": m.name,
                        "path": m.path,
                        "module_type": m.module_type,
                        "description": m.description,
                        "classes": m.classes,
                        "functions": m.functions,
                        "dependencies": m.dependencies,
                        "estimated_complexity": m.estimated_complexity,
                        "business_domain": m.business_domain,
                    } if hasattr(m, 'name') else m
                    for m in analysis.modules
                ]

                domains_json = [
                    {
                        "name": d.name,
                        "description": d.description,
                        "modules": d.modules,
                        "entities": d.entities,
                        "use_cases": d.use_cases,
                        "complexity": d.complexity,
                        "priority": d.priority,
                    } if hasattr(d, 'name') else d
                    for d in analysis.domains
                ]

                doc_insights_json = [
                    {
                        "source": di.source,
                        "section": di.section,
                        "content": di.content,
                        "insight_type": di.insight_type,
                        "confidence": di.confidence,
                    } if hasattr(di, 'source') else di
                    for di in analysis.doc_insights
                ]

                if existing_analysis:
                    # Update existing
                    await db.execute(
                        update(BrownPaperAnalysisDB)
                        .where(BrownPaperAnalysisDB.session_id == uuid.UUID(session_id))
                        .values(
                            modules=modules_json,
                            primary_patterns=analysis.primary_patterns,
                            doc_insights=doc_insights_json,
                            readme_summary=analysis.readme_summary,
                            domains=domains_json,
                            analysis_time_ms=analysis.analysis_time_ms,
                            updated_at=datetime.now(timezone.utc),
                        )
                    )
                else:
                    # Create new
                    db_analysis = BrownPaperAnalysisDB(
                        session_id=uuid.UUID(session_id),
                        modules=modules_json,
                        primary_patterns=analysis.primary_patterns,
                        doc_insights=doc_insights_json,
                        readme_summary=analysis.readme_summary,
                        domains=domains_json,
                        analysis_time_ms=analysis.analysis_time_ms,
                    )
                    db.add(db_analysis)

                await db.commit()
                logger.info(f"Persisted analysis for session {session_id} to database: "
                           f"{len(analysis.modules)} modules, {len(analysis.domains)} domains")

        except Exception as e:
            logger.error(f"Failed to persist analysis to database: {e}", exc_info=True)
            # Don't raise - continue with in-memory data

    async def _persist_constitution_to_db(
        self,
        session_id: str,
        constitution: Dict[str, Any],
        status: str = "review"
    ) -> bool:
        """
        Persist constitution to database.

        Returns:
            True on success, False on failure.
        """
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(BrownPaperConstitutionDB).where(
                        BrownPaperConstitutionDB.session_id == uuid.UUID(session_id)
                    )
                )
                db_constitution = result.scalar_one_or_none()

                # Extract full metadata from constitution
                const_metadata = constitution.get("metadata", {})
                generation_metadata = {
                    "generated_from": const_metadata.get("generated_from"),
                    "application_id": const_metadata.get("application_id"),
                    "domains_analyzed": const_metadata.get("domains_analyzed"),
                    "modules_analyzed": const_metadata.get("modules_analyzed"),
                    "generated_at": const_metadata.get("generated_at"),
                    "persisted_at": datetime.now(timezone.utc).isoformat(),
                }

                # Generate markdown version
                content_markdown = self._constitution_to_markdown(constitution)

                if db_constitution:
                    db_constitution.content_json = constitution
                    db_constitution.content_markdown = content_markdown
                    db_constitution.status = status
                    db_constitution.generation_metadata = generation_metadata
                    db_constitution.updated_at = datetime.now(timezone.utc)
                else:
                    db_constitution = BrownPaperConstitutionDB(
                        session_id=uuid.UUID(session_id),
                        content_json=constitution,
                        content_markdown=content_markdown,
                        status=status,
                        generation_metadata=generation_metadata,
                    )
                    db.add(db_constitution)

                await db.commit()
                logger.info(f"Persisted constitution for session {session_id} to database")
                return True

        except Exception as e:
            logger.error(f"Failed to persist constitution to database: {e}", exc_info=True)
            return False

    async def _persist_epics_to_db(
        self,
        session_id: str,
        epics: List[Dict[str, Any]]
    ) -> bool:
        """
        Persist epics to database.

        Returns:
            True on success, False on failure.
        """
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(BrownPaperConstitutionDB).where(
                        BrownPaperConstitutionDB.session_id == uuid.UUID(session_id)
                    )
                )
                db_constitution = result.scalar_one_or_none()

                if not db_constitution:
                    logger.warning(f"No constitution found for session {session_id}; skipping epic persistence")
                    return False

                await db.execute(
                    delete(BrownPaperEpicDB).where(
                        BrownPaperEpicDB.constitution_id == db_constitution.id
                    )
                )

                db_epics = []
                for epic in epics:
                    metadata = epic.get("metadata", {})
                    db_epics.append(
                        BrownPaperEpicDB(
                            constitution_id=db_constitution.id,
                            epic_number=epic.get("id", ""),
                            name=epic.get("name", "Untitled Epic"),
                            description=epic.get("description"),
                            priority=epic.get("priority", 1),
                            complexity=epic.get("complexity", "medium"),
                            # Use explicit domain field with fallback to name for backwards compat
                            source_domain=epic.get("domain", epic.get("name")),
                            source_modules=metadata.get("modules", []),
                            source_entities=metadata.get("entities", []),
                            features=epic.get("features", []),
                            status="draft",
                        )
                    )

                if db_epics:
                    db.add_all(db_epics)

                await db.commit()
                logger.info(f"Persisted {len(db_epics)} epics for session {session_id} to database")
                return True

        except Exception as e:
            logger.error(f"Failed to persist epics to database: {e}", exc_info=True)
            return False

    def _constitution_to_markdown(self, constitution: Dict[str, Any]) -> str:
        """
        Convert constitution JSON to markdown format.

        Args:
            constitution: Constitution dict with sections like mission_vision, core_principles, etc.

        Returns:
            Rendered markdown string.
        """
        lines = ["# Project Constitution", ""]

        # Mission & Vision
        mission_vision = constitution.get("mission_vision", {})
        if mission_vision:
            lines.append("## Mission & Vision")
            lines.append("")
            if mission_vision.get("mission"):
                lines.append(f"**Mission:** {mission_vision['mission']}")
                lines.append("")
            if mission_vision.get("vision"):
                lines.append(f"**Vision:** {mission_vision['vision']}")
                lines.append("")

        # Core Principles
        principles = constitution.get("core_principles", [])
        if principles:
            lines.append("## Core Principles")
            lines.append("")
            for principle in principles:
                if isinstance(principle, dict):
                    lines.append(f"### {principle.get('name', 'Principle')}")
                    lines.append(principle.get("description", ""))
                    lines.append("")
                else:
                    lines.append(f"- {principle}")
            lines.append("")

        # Key Requirements
        requirements = constitution.get("key_requirements", [])
        if requirements:
            lines.append("## Key Requirements")
            lines.append("")
            for req in requirements:
                if isinstance(req, dict):
                    lines.append(f"- **{req.get('category', 'Requirement')}:** {req.get('description', '')}")
                else:
                    lines.append(f"- {req}")
            lines.append("")

        # Constraints
        constraints = constitution.get("constraints", [])
        if constraints:
            lines.append("## Constraints & Limitations")
            lines.append("")
            for constraint in constraints:
                if isinstance(constraint, dict):
                    lines.append(f"- **{constraint.get('type', 'Constraint')}:** {constraint.get('description', '')}")
                else:
                    lines.append(f"- {constraint}")
            lines.append("")

        # Risks
        risks = constitution.get("risks", [])
        if risks:
            lines.append("## Risks & Mitigations")
            lines.append("")
            for risk in risks:
                if isinstance(risk, dict):
                    lines.append(f"### {risk.get('name', 'Risk')}")
                    lines.append(f"**Impact:** {risk.get('impact', 'Unknown')}")
                    lines.append(f"**Mitigation:** {risk.get('mitigation', 'None specified')}")
                    lines.append("")
                else:
                    lines.append(f"- {risk}")
            lines.append("")

        # Scope
        scope = constitution.get("scope", {})
        if scope:
            lines.append("## Scope Definition")
            lines.append("")
            if scope.get("in_scope"):
                lines.append("### In Scope")
                for item in scope["in_scope"]:
                    lines.append(f"- {item}")
                lines.append("")
            if scope.get("out_of_scope"):
                lines.append("### Out of Scope")
                for item in scope["out_of_scope"]:
                    lines.append(f"- {item}")
                lines.append("")

        # Success Criteria
        criteria = constitution.get("success_criteria", [])
        if criteria:
            lines.append("## Success Criteria")
            lines.append("")
            for criterion in criteria:
                if isinstance(criterion, dict):
                    lines.append(f"- **{criterion.get('metric', 'Criterion')}:** {criterion.get('target', '')}")
                else:
                    lines.append(f"- {criterion}")
            lines.append("")

        # Metadata
        metadata = constitution.get("metadata", {})
        if metadata:
            lines.append("---")
            lines.append("")
            lines.append("*Generated by Brown Paper Analysis*")
            if metadata.get("generated_at"):
                lines.append(f"*Date: {metadata['generated_at']}*")
            if metadata.get("domains_analyzed"):
                lines.append(f"*Domains analyzed: {metadata['domains_analyzed']}*")
            if metadata.get("modules_analyzed"):
                lines.append(f"*Modules analyzed: {metadata['modules_analyzed']}*")

        return "\n".join(lines)

    # ========================================================================
    # MAIN ANALYSIS FLOW
    # ========================================================================

    async def analyze_application(self, session_id: str) -> BrownPaperAnalysis:
        """
        Run complete Brown Paper analysis on an application.

        Steps:
        1. Load application from registry
        2. Analyze code structure
        3. Analyze documentation
        4. Extract domains
        5. Update session status
        """
        import time
        start_time = time.time()

        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        try:
            # Get application from registry
            registry = self._get_registry()
            app = registry.get_application(session.application_id)

            if not app:
                raise ValueError(f"Application not found: {session.application_id}")

            # Phase 1: Scan code structure
            session.status = BrownPaperStatus.SCANNING
            modules = await self._analyze_code_structure(app)

            # Phase 2: Analyze documentation
            doc_insights = await self._analyze_documentation(app.root_path)
            readme_summary = await self._extract_readme_summary(app.root_path)

            # Phase 3: Detect architectural patterns
            patterns = self._detect_architecture_patterns(modules)

            # Phase 4: Extract domains
            session.status = BrownPaperStatus.ANALYZING
            domains = await self._extract_business_domains(app, modules, doc_insights)

            # Phase 5: Stability Analysis (Week 145-146)
            stability_result = None
            try:
                stability_integration = get_brown_paper_stability_integration()
                stability_result = await stability_integration.analyze_for_brown_paper(
                    project_path=app.root_path,
                    project_name=app.name,
                    project_id=app.id,
                )
                logger.info(
                    f"Stability analysis complete: {stability_result.total_findings} findings, "
                    f"score: {stability_result.stability_score}"
                )
            except Exception as e:
                logger.warning(f"Stability analysis skipped: {e}")

            # Build analysis result
            analysis = BrownPaperAnalysis(
                application_id=app.id,
                application_name=app.name,
                root_path=app.root_path,
                modules=modules,
                total_classes=sum(len(m.classes) for m in modules),
                total_functions=sum(len(m.functions) for m in modules),
                primary_patterns=patterns,
                doc_insights=doc_insights,
                readme_summary=readme_summary,
                domains=domains,
                stability_analysis=stability_result.to_dict() if stability_result else None,
                analysis_time_ms=int((time.time() - start_time) * 1000),
                status=BrownPaperStatus.ANALYZING,
            )

            session.analysis = analysis
            session.updated_at = datetime.now(timezone.utc)

            # Persist analysis to database
            await self._persist_analysis_to_db(session_id, session, analysis)

            logger.info(f"Analysis complete for session {session_id}: "
                       f"{len(modules)} modules, {len(domains)} domains, "
                       f"{analysis.analysis_time_ms}ms")

            return analysis

        except Exception as e:
            session.status = BrownPaperStatus.REJECTED
            session.error_message = str(e)
            session.updated_at = datetime.now(timezone.utc)
            logger.error(f"Brown Paper analysis failed: {e}", exc_info=True)
            raise

    # ========================================================================
    # CODE ANALYSIS
    # ========================================================================

    async def _analyze_code_structure(self, app: Application) -> List[CodeModule]:
        """Analyze code structure from application components."""
        modules: List[CodeModule] = []

        for comp in app.components.values():
            comp_path = Path(comp.path)
            if not comp_path.exists():
                continue

            # Analyze each component
            comp_modules = await self._scan_component(comp, comp_path)
            modules.extend(comp_modules)

        return modules

    async def _scan_component(
        self,
        component: ApplicationComponent,
        comp_path: Path
    ) -> List[CodeModule]:
        """Scan a single component for modules."""
        modules: List[CodeModule] = []

        # Determine language-specific patterns
        stacks_lower = [s.lower() for s in component.stacks]

        if "python" in stacks_lower:
            modules.extend(await self._scan_python_component(component, comp_path))
        if "typescript" in stacks_lower or "javascript" in stacks_lower:
            modules.extend(await self._scan_typescript_component(component, comp_path))
        if any(s in stacks_lower for s in ["vb.net", "vb", "visualbasic", "vbnet"]):
            modules.extend(await self._scan_vbnet_component(component, comp_path))
        if any(s in stacks_lower for s in ["c#", "csharp", ".net", "dotnet"]):
            modules.extend(await self._scan_csharp_component(component, comp_path))
        if any(s in stacks_lower for s in ["asp.net", "aspx", "webforms"]):
            modules.extend(await self._scan_aspnet_component(component, comp_path))
        if any(s in stacks_lower for s in ["asp", "asp classic", "classic asp", "vbscript"]):
            modules.extend(await self._scan_asp_classic_component(component, comp_path))

        # If no specific stack matched, try to detect from files
        if not modules:
            modules.extend(await self._scan_auto_detect(component, comp_path))

        return modules

    async def _scan_python_component(
        self,
        component: ApplicationComponent,
        comp_path: Path
    ) -> List[CodeModule]:
        """Scan Python component for modules."""
        modules: List[CodeModule] = []

        # Find Python packages
        # Exclude patterns for virtual environments, dependencies, and build artifacts
        EXCLUDE_PATTERNS = [
            ".venv", "venv", ".env", "env",
            "node_modules",
            "__pycache__",
            ".git",
            "dist", "build",
            "site-packages",
            ".tox", ".pytest_cache", ".mypy_cache",
            "eggs", "*.egg-info",
        ]

        for py_file in comp_path.rglob("*.py"):
            # Skip excluded directories
            path_str = str(py_file)
            if any(excl in path_str for excl in EXCLUDE_PATTERNS):
                continue
            # Skip test files
            if "test" in py_file.name.lower():
                continue

            # Analyze file
            module = await self._analyze_python_file(py_file, comp_path)
            if module:
                modules.append(module)

        return modules

    async def _analyze_python_file(
        self,
        file_path: Path,
        root_path: Path
    ) -> Optional[CodeModule]:
        """Analyze a Python file for classes and functions."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Extract classes
            classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)

            # Extract functions (top-level only)
            functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)

            # Skip if no meaningful content
            if not classes and not functions:
                return None

            # Determine module type
            module_type = self._determine_module_type(file_path.name, content)

            # Extract imports for dependencies
            imports = re.findall(r'^(?:from|import)\s+([\w.]+)', content, re.MULTILINE)

            # Generate description from docstring
            docstring_match = re.search(r'^"""(.*?)"""', content, re.DOTALL)
            description = docstring_match.group(1).strip()[:200] if docstring_match else ""

            # Estimate complexity
            complexity = self._estimate_complexity(len(classes), len(functions), len(content))

            rel_path = str(file_path.relative_to(root_path))

            return CodeModule(
                name=file_path.stem,
                path=rel_path,
                module_type=module_type,
                description=description,
                classes=classes,
                functions=functions,
                dependencies=[i for i in imports if not i.startswith("__")],
                estimated_complexity=complexity,
            )

        except Exception as e:
            logger.warning(f"Could not analyze {file_path}: {e}")
            return None

    async def _scan_typescript_component(
        self,
        component: ApplicationComponent,
        comp_path: Path
    ) -> List[CodeModule]:
        """Scan TypeScript/JavaScript component for modules."""
        modules: List[CodeModule] = []

        for ts_file in comp_path.rglob("*.ts"):
            # Skip node_modules and test files
            if "node_modules" in str(ts_file) or ".spec." in ts_file.name or ".test." in ts_file.name:
                continue

            module = await self._analyze_typescript_file(ts_file, comp_path)
            if module:
                modules.append(module)

        return modules

    async def _analyze_typescript_file(
        self,
        file_path: Path,
        root_path: Path
    ) -> Optional[CodeModule]:
        """Analyze a TypeScript file for classes and functions."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Extract classes
            classes = re.findall(r'(?:export\s+)?class\s+(\w+)', content)

            # Extract functions
            functions = re.findall(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)', content)

            # Also look for arrow function exports
            arrow_funcs = re.findall(r'export\s+const\s+(\w+)\s*=', content)
            functions.extend(arrow_funcs)

            if not classes and not functions:
                return None

            module_type = self._determine_module_type(file_path.name, content)

            # Extract imports
            imports = re.findall(r"(?:from|import)\s+['\"]([^'\"]+)['\"]", content)

            complexity = self._estimate_complexity(len(classes), len(functions), len(content))

            rel_path = str(file_path.relative_to(root_path))

            return CodeModule(
                name=file_path.stem,
                path=rel_path,
                module_type=module_type,
                description="",
                classes=classes,
                functions=functions,
                dependencies=[i for i in imports if not i.startswith(".")],
                estimated_complexity=complexity,
            )

        except Exception as e:
            logger.warning(f"Could not analyze {file_path}: {e}")
            return None

    # ========================================================================
    # VB.NET ANALYSIS
    # ========================================================================

    async def _scan_vbnet_component(
        self,
        component: ApplicationComponent,
        comp_path: Path
    ) -> List[CodeModule]:
        """Scan VB.NET component for modules."""
        modules: List[CodeModule] = []

        for vb_file in comp_path.rglob("*.vb"):
            # Skip designer files and test files
            if ".Designer." in vb_file.name or "Test" in vb_file.name:
                continue
            # Skip My Project generated files
            if "My Project" in str(vb_file):
                continue
            # Skip Service References (auto-generated)
            if "Service References" in str(vb_file):
                continue

            module = await self._analyze_vbnet_file(vb_file, comp_path)
            if module:
                modules.append(module)

        return modules

    async def _analyze_vbnet_file(
        self,
        file_path: Path,
        root_path: Path
    ) -> Optional[CodeModule]:
        """Analyze a VB.NET file for classes and functions."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Extract classes (Public Class, Private Class, Friend Class, etc.)
            classes = re.findall(
                r'(?:Public|Private|Friend|Protected)?\s*(?:Partial\s+)?Class\s+(\w+)',
                content, re.IGNORECASE
            )

            # Extract modules (VB.NET Module = static class)
            vb_modules = re.findall(
                r'(?:Public|Private|Friend)?\s*Module\s+(\w+)',
                content, re.IGNORECASE
            )
            classes.extend(vb_modules)

            # Extract functions/subs
            functions = re.findall(
                r'(?:Public|Private|Protected|Friend)?\s*(?:Shared\s+)?(?:Function|Sub)\s+(\w+)',
                content, re.IGNORECASE
            )

            # Skip if no meaningful content
            if not classes and len(functions) < 2:
                return None

            module_type = self._determine_module_type(file_path.name, content)

            # Extract imports for dependencies
            imports = re.findall(r'^Imports\s+([\w.]+)', content, re.MULTILINE)

            # Generate description from comments
            comment_match = re.search(r"^'\s*(.+?)(?:\r?\n|$)", content, re.MULTILINE)
            description = comment_match.group(1).strip()[:200] if comment_match else ""

            complexity = self._estimate_complexity(len(classes), len(functions), len(content))

            rel_path = str(file_path.relative_to(root_path))

            return CodeModule(
                name=file_path.stem,
                path=rel_path,
                module_type=module_type,
                description=description,
                classes=classes,
                functions=functions[:50],  # Limit to 50 functions
                dependencies=[i for i in imports if not i.startswith("System.")],
                estimated_complexity=complexity,
            )

        except Exception as e:
            logger.warning(f"Could not analyze VB.NET file {file_path}: {e}")
            return None

    # ========================================================================
    # C# ANALYSIS
    # ========================================================================

    async def _scan_csharp_component(
        self,
        component: ApplicationComponent,
        comp_path: Path
    ) -> List[CodeModule]:
        """Scan C# component for modules."""
        modules: List[CodeModule] = []

        for cs_file in comp_path.rglob("*.cs"):
            # Skip designer and generated files
            if ".Designer." in cs_file.name or ".g.cs" in cs_file.name:
                continue
            if "AssemblyInfo.cs" in cs_file.name:
                continue

            module = await self._analyze_csharp_file(cs_file, comp_path)
            if module:
                modules.append(module)

        return modules

    async def _analyze_csharp_file(
        self,
        file_path: Path,
        root_path: Path
    ) -> Optional[CodeModule]:
        """Analyze a C# file for classes and methods."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Extract classes/interfaces/records
            classes = re.findall(
                r'(?:public|private|internal|protected)?\s*(?:partial\s+)?(?:class|interface|record|struct)\s+(\w+)',
                content
            )

            # Extract methods
            functions = re.findall(
                r'(?:public|private|protected|internal)\s+(?:static\s+)?(?:async\s+)?(?:virtual\s+)?[\w<>\[\],\s]+\s+(\w+)\s*\(',
                content
            )

            if not classes and len(functions) < 2:
                return None

            module_type = self._determine_module_type(file_path.name, content)

            # Extract using statements
            imports = re.findall(r'^using\s+([\w.]+);', content, re.MULTILINE)

            # Get XML doc summary
            summary_match = re.search(r'<summary>\s*(.+?)\s*</summary>', content, re.DOTALL)
            description = summary_match.group(1).strip()[:200] if summary_match else ""

            complexity = self._estimate_complexity(len(classes), len(functions), len(content))

            rel_path = str(file_path.relative_to(root_path))

            return CodeModule(
                name=file_path.stem,
                path=rel_path,
                module_type=module_type,
                description=description,
                classes=classes,
                functions=functions[:50],
                dependencies=[i for i in imports if not i.startswith("System.")],
                estimated_complexity=complexity,
            )

        except Exception as e:
            logger.warning(f"Could not analyze C# file {file_path}: {e}")
            return None

    # ========================================================================
    # ASP.NET / ASPX ANALYSIS
    # ========================================================================

    async def _scan_aspnet_component(
        self,
        component: ApplicationComponent,
        comp_path: Path
    ) -> List[CodeModule]:
        """Scan ASP.NET component (ASPX pages, code-behind)."""
        modules: List[CodeModule] = []

        # ASPX pages
        for aspx_file in comp_path.rglob("*.aspx"):
            module = await self._analyze_aspx_file(aspx_file, comp_path)
            if module:
                modules.append(module)

        # ASPX.VB code-behind files
        for aspx_vb in comp_path.rglob("*.aspx.vb"):
            module = await self._analyze_vbnet_file(aspx_vb, comp_path)
            if module:
                module.module_type = "page_controller"
                modules.append(module)

        # ASMX web services
        for asmx_file in comp_path.rglob("*.asmx"):
            module = await self._analyze_aspx_file(asmx_file, comp_path)
            if module:
                module.module_type = "webservice"
                modules.append(module)

        return modules

    async def _analyze_aspx_file(
        self,
        file_path: Path,
        root_path: Path
    ) -> Optional[CodeModule]:
        """Analyze an ASPX page."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Extract page directive info
            inherits_match = re.search(r'Inherits="([^"]+)"', content)
            codebehind_match = re.search(r'CodeBehind="([^"]+)"', content)

            # Extract server-side controls
            controls = re.findall(r'<asp:(\w+)', content)
            unique_controls = list(set(controls))

            # Extract user controls
            user_controls = re.findall(r'<%@\s+Register[^>]+TagName="(\w+)"', content, re.IGNORECASE)

            # Estimate functionality from content
            functions = []
            if inherits_match:
                functions.append(f"Inherits: {inherits_match.group(1)}")
            if codebehind_match:
                functions.append(f"CodeBehind: {codebehind_match.group(1)}")

            rel_path = str(file_path.relative_to(root_path))

            return CodeModule(
                name=file_path.stem,
                path=rel_path,
                module_type="form",
                description=f"ASP.NET page with {len(unique_controls)} controls",
                classes=user_controls,
                functions=functions,
                dependencies=unique_controls[:20],
                estimated_complexity=self._estimate_complexity(0, len(unique_controls), len(content)),
            )

        except Exception as e:
            logger.warning(f"Could not analyze ASPX file {file_path}: {e}")
            return None

    # ========================================================================
    # ASP CLASSIC ANALYSIS
    # ========================================================================

    async def _scan_asp_classic_component(
        self,
        component: ApplicationComponent,
        comp_path: Path
    ) -> List[CodeModule]:
        """Scan ASP Classic component (.asp files with VBScript)."""
        modules: List[CodeModule] = []

        for asp_file in comp_path.rglob("*.asp"):
            module = await self._analyze_asp_classic_file(asp_file, comp_path)
            if module:
                modules.append(module)

        return modules

    async def _analyze_asp_classic_file(
        self,
        file_path: Path,
        root_path: Path
    ) -> Optional[CodeModule]:
        """Analyze an ASP Classic file (VBScript)."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Extract VBScript functions and subs
            functions = re.findall(
                r'(?:Function|Sub)\s+(\w+)',
                content, re.IGNORECASE
            )

            # Extract Class definitions (ASP Classic also supports classes)
            classes = re.findall(
                r'Class\s+(\w+)',
                content, re.IGNORECASE
            )

            # Extract includes (<!-- #include -->)
            includes = re.findall(
                r'<!--\s*#include\s+(?:file|virtual)\s*=\s*"([^"]+)"',
                content, re.IGNORECASE
            )

            # Extract database connections
            has_db = bool(re.search(r'ADODB\.(?:Connection|Recordset)', content, re.IGNORECASE))

            if not functions and not classes:
                return None

            rel_path = str(file_path.relative_to(root_path))

            # Determine type based on content
            module_type = "data_access" if has_db else "form"
            if "login" in file_path.name.lower() or "auth" in file_path.name.lower():
                module_type = "controller"

            return CodeModule(
                name=file_path.stem,
                path=rel_path,
                module_type=module_type,
                description=f"ASP Classic page with {len(functions)} functions",
                classes=classes,
                functions=functions[:30],
                dependencies=includes,
                estimated_complexity=self._estimate_complexity(len(classes), len(functions), len(content)),
            )

        except Exception as e:
            logger.warning(f"Could not analyze ASP Classic file {file_path}: {e}")
            return None

    # ========================================================================
    # AUTO-DETECT LANGUAGE
    # ========================================================================

    async def _scan_auto_detect(
        self,
        component: ApplicationComponent,
        comp_path: Path
    ) -> List[CodeModule]:
        """Auto-detect language from files and scan accordingly."""
        modules: List[CodeModule] = []

        # Check for each file type and scan
        vb_files = list(comp_path.rglob("*.vb"))
        cs_files = list(comp_path.rglob("*.cs"))
        asp_files = list(comp_path.rglob("*.asp"))
        aspx_files = list(comp_path.rglob("*.aspx"))
        py_files = list(comp_path.rglob("*.py"))
        ts_files = list(comp_path.rglob("*.ts"))

        # Scan based on what exists
        if vb_files:
            logger.info(f"Auto-detected {len(vb_files)} VB.NET files in {comp_path}")
            modules.extend(await self._scan_vbnet_component(component, comp_path))

        if cs_files:
            logger.info(f"Auto-detected {len(cs_files)} C# files in {comp_path}")
            modules.extend(await self._scan_csharp_component(component, comp_path))

        if asp_files:
            logger.info(f"Auto-detected {len(asp_files)} ASP Classic files in {comp_path}")
            modules.extend(await self._scan_asp_classic_component(component, comp_path))

        if aspx_files:
            logger.info(f"Auto-detected {len(aspx_files)} ASPX files in {comp_path}")
            modules.extend(await self._scan_aspnet_component(component, comp_path))

        if py_files:
            logger.info(f"Auto-detected {len(py_files)} Python files in {comp_path}")
            modules.extend(await self._scan_python_component(component, comp_path))

        if ts_files:
            logger.info(f"Auto-detected {len(ts_files)} TypeScript files in {comp_path}")
            modules.extend(await self._scan_typescript_component(component, comp_path))

        return modules

    def _determine_module_type(self, filename: str, content: str) -> str:
        """Determine the type of module based on patterns."""
        lower_name = filename.lower()
        lower_content = content.lower()

        for module_type, patterns in MODULE_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, lower_name) or re.search(pattern, lower_content):
                    return module_type

        return "other"

    def _estimate_complexity(
        self,
        class_count: int,
        function_count: int,
        code_length: int
    ) -> str:
        """Estimate module complexity."""
        score = class_count * 3 + function_count + code_length // 1000

        if score < 5:
            return "low"
        elif score < 15:
            return "medium"
        elif score < 30:
            return "high"
        else:
            return "very_high"

    def _detect_architecture_patterns(self, modules: List[CodeModule]) -> List[str]:
        """Detect architectural patterns from module analysis."""
        detected = []
        module_types = [m.module_type for m in modules]
        module_paths = [m.path.lower() for m in modules]

        for pattern_name, indicators in ARCHITECTURE_PATTERNS.items():
            matches = sum(
                1 for indicator in indicators
                if any(indicator in mt for mt in module_types) or
                   any(indicator in mp for mp in module_paths)
            )
            # Need at least 2 indicators for a pattern
            if matches >= 2:
                detected.append(pattern_name)

        return detected if detected else ["unknown"]

    # ========================================================================
    # DOCUMENTATION ANALYSIS
    # ========================================================================

    async def _analyze_documentation(self, root_path: str) -> List[DocumentationInsight]:
        """Analyze documentation files for insights."""
        insights: List[DocumentationInsight] = []
        path = Path(root_path)

        # Find documentation files
        doc_files = []
        doc_files.extend(path.glob("*.md"))
        doc_files.extend(path.glob("docs/**/*.md"))
        doc_files.extend(path.glob("doc/**/*.md"))

        for doc_file in doc_files[:20]:  # Limit to 20 files
            file_insights = await self._extract_doc_insights(doc_file)
            insights.extend(file_insights)

        return insights

    async def _extract_doc_insights(self, doc_path: Path) -> List[DocumentationInsight]:
        """Extract insights from a documentation file."""
        insights: List[DocumentationInsight] = []

        try:
            content = doc_path.read_text(encoding='utf-8', errors='ignore')

            # Split into sections by headers
            sections = re.split(r'^#+\s+', content, flags=re.MULTILINE)

            for section in sections[:10]:  # Limit sections
                if not section.strip():
                    continue

                # Try to match against patterns
                for insight_type, patterns in DOC_PATTERNS.items():
                    for pattern in patterns:
                        if re.search(pattern, section, re.IGNORECASE):
                            insights.append(DocumentationInsight(
                                source=doc_path.name,
                                section=section[:50].strip(),
                                content=section[:500].strip(),
                                insight_type=insight_type,
                                confidence=0.7,
                            ))
                            break

        except Exception as e:
            logger.warning(f"Could not analyze doc {doc_path}: {e}")

        return insights

    async def _extract_readme_summary(self, root_path: str) -> Optional[str]:
        """Extract summary from README file."""
        path = Path(root_path)

        for readme_name in ["README.md", "README.rst", "README.txt", "readme.md"]:
            readme_path = path / readme_name
            if readme_path.exists():
                try:
                    content = readme_path.read_text(encoding='utf-8', errors='ignore')
                    # Get first meaningful paragraph
                    paragraphs = re.split(r'\n\n+', content)
                    for para in paragraphs:
                        # Skip headers and badges
                        if para.strip() and not para.startswith('#') and not para.startswith('['):
                            return para.strip()[:500]
                except Exception:
                    pass

        return None

    # ========================================================================
    # DOMAIN EXTRACTION
    # ========================================================================

    async def _extract_business_domains(
        self,
        app: Application,
        modules: List[CodeModule],
        doc_insights: List[DocumentationInsight]
    ) -> List[BusinessDomain]:
        """Extract business domains from code and documentation analysis."""
        domains: List[BusinessDomain] = []

        # Group modules by directory/package
        package_groups: Dict[str, List[CodeModule]] = {}
        for module in modules:
            # Get parent directory as package name
            parts = module.path.split('/')
            if len(parts) > 1:
                package = parts[-2]  # Parent directory
            else:
                package = "root"

            if package not in package_groups:
                package_groups[package] = []
            package_groups[package].append(module)

        # Create domain for each significant package
        domain_priority = 1
        for package_name, package_modules in package_groups.items():
            # Skip small packages and infrastructure
            if len(package_modules) < 2:
                continue
            if package_name in ["__pycache__", "tests", "test", "migrations", "alembic"]:
                continue

            # Extract entities (models, classes)
            entities = []
            for m in package_modules:
                entities.extend(m.classes)

            # Extract use cases from function names
            use_cases = []
            for m in package_modules:
                for func in m.functions:
                    # Convert function name to use case
                    if func.startswith("get_"):
                        use_cases.append(f"Retrieve {func[4:]}")
                    elif func.startswith("create_"):
                        use_cases.append(f"Create {func[7:]}")
                    elif func.startswith("update_"):
                        use_cases.append(f"Update {func[7:]}")
                    elif func.startswith("delete_"):
                        use_cases.append(f"Delete {func[7:]}")

            # Deduplicate
            use_cases = list(set(use_cases))[:10]

            # Determine complexity
            total_classes = sum(len(m.classes) for m in package_modules)
            complexity = "low" if total_classes < 3 else "medium" if total_classes < 8 else "high"

            # Generate description
            description = f"Handles {package_name} functionality"
            for insight in doc_insights:
                if package_name.lower() in insight.content.lower():
                    description = insight.content[:200]
                    break

            domain = BusinessDomain(
                name=package_name.replace("_", " ").title(),
                description=description,
                modules=[m.path for m in package_modules],
                entities=entities[:10],
                use_cases=use_cases,
                complexity=complexity,
                priority=domain_priority,
            )

            domains.append(domain)
            domain_priority += 1

        # Sort by number of modules (more modules = more important)
        domains.sort(key=lambda d: len(d.modules), reverse=True)

        # Re-assign priorities
        for i, domain in enumerate(domains):
            domain.priority = i + 1

        return domains[:15]  # Limit to 15 domains

    # ========================================================================
    # CONSTITUTION GENERATION
    # ========================================================================

    async def generate_constitution(
        self,
        session_id: str,
        human_input: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate Constitution from analysis.

        Constitution sections (matching Green Paper output):
        1. Mission & Vision
        2. Core Principles
        3. Key Requirements
        4. Constraints & Limitations
        5. Risks & Mitigations
        6. Scope Definition
        7. Success Criteria
        """
        session = await self.get_session(session_id)
        if not session or not session.analysis:
            raise ValueError(f"Session not found or no analysis: {session_id}")

        analysis = session.analysis
        session.status = BrownPaperStatus.GENERATING

        # Build constitution from analysis
        constitution = {
            "mission_vision": self._generate_mission_vision(analysis, human_input),
            "core_principles": self._generate_core_principles(analysis),
            "key_requirements": self._generate_key_requirements(analysis),
            "constraints": self._generate_constraints(analysis),
            "risks": self._generate_risks(analysis),
            "scope": self._generate_scope(analysis),
            "success_criteria": self._generate_success_criteria(analysis),
            "metadata": {
                "generated_from": "brown_paper",
                "application_id": analysis.application_id,
                "domains_analyzed": len(analysis.domains),
                "modules_analyzed": len(analysis.modules),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        }

        analysis.constitution = constitution
        session.status = BrownPaperStatus.REVIEW
        session.updated_at = datetime.now(timezone.utc)

        await self._persist_constitution_to_db(
            session_id=session_id,
            constitution=constitution,
            status=session.status.value,
        )

        return constitution

    def _generate_mission_vision(
        self,
        analysis: BrownPaperAnalysis,
        human_input: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Generate mission and vision from analysis."""
        # Start with README if available
        vision = analysis.readme_summary or f"The {analysis.application_name} application"

        # Use human input if provided
        if human_input and "mission" in human_input:
            return {
                "mission": human_input["mission"],
                "vision": human_input.get("vision", vision),
            }

        # Auto-generate from domains
        domain_names = [d.name for d in analysis.domains[:5]]
        mission = f"To provide comprehensive {', '.join(domain_names).lower()} capabilities."

        return {
            "mission": mission,
            "vision": vision,
        }

    def _generate_core_principles(self, analysis: BrownPaperAnalysis) -> List[Dict[str, str]]:
        """Generate core principles from detected patterns."""
        principles = []

        # Add principles based on detected architecture
        if "ddd" in analysis.primary_patterns:
            principles.append({
                "name": "Domain-Driven Design",
                "description": "Business logic is organized around domain concepts and bounded contexts.",
            })

        if "layered" in analysis.primary_patterns:
            principles.append({
                "name": "Layered Architecture",
                "description": "Clear separation between presentation, application, domain, and infrastructure layers.",
            })

        if "microservices" in analysis.primary_patterns:
            principles.append({
                "name": "Service Independence",
                "description": "Each service operates independently with its own data and deployment lifecycle.",
            })

        # Add default principles based on code analysis
        if analysis.total_classes > 20:
            principles.append({
                "name": "Modularity",
                "description": "Code is organized into well-defined modules with clear responsibilities.",
            })

        if len([m for m in analysis.modules if m.module_type == "test"]) > 5:
            principles.append({
                "name": "Test-Driven Development",
                "description": "Comprehensive test coverage ensures code quality and reliability.",
            })

        # Always add these
        principles.append({
            "name": "Maintainability",
            "description": "Code is structured to be easily understood, modified, and extended.",
        })

        return principles[:7]  # Max 7 principles

    def _generate_key_requirements(self, analysis: BrownPaperAnalysis) -> List[Dict[str, Any]]:
        """Generate key requirements from domains and use cases."""
        requirements = []

        for domain in analysis.domains[:5]:
            for use_case in domain.use_cases[:3]:
                requirements.append({
                    "id": f"REQ-{len(requirements)+1:03d}",
                    "domain": domain.name,
                    "description": use_case,
                    "priority": "high" if domain.priority <= 2 else "medium",
                    "derived_from": "code_analysis",
                })

        return requirements[:15]  # Max 15 requirements

    def _generate_constraints(self, analysis: BrownPaperAnalysis) -> List[Dict[str, str]]:
        """Generate constraints from technology stack."""
        constraints = []

        # Technology constraints
        for module in analysis.modules[:10]:
            for dep in module.dependencies[:3]:
                if dep.startswith("sqlalchemy") or dep.startswith("django"):
                    constraints.append({
                        "type": "technology",
                        "constraint": f"Database access via {dep.split('.')[0]}",
                    })
                    break

        # Pattern constraints
        for pattern in analysis.primary_patterns:
            constraints.append({
                "type": "architecture",
                "constraint": f"Must follow {pattern.upper()} architecture pattern",
            })

        return list({c["constraint"]: c for c in constraints}.values())[:10]

    def _generate_risks(self, analysis: BrownPaperAnalysis) -> List[Dict[str, str]]:
        """Generate risks from analysis."""
        risks = []

        # Complexity risks
        high_complexity = [m for m in analysis.modules if m.estimated_complexity in ["high", "very_high"]]
        if high_complexity:
            risks.append({
                "risk": f"High complexity in {len(high_complexity)} modules",
                "mitigation": "Refactor complex modules, add comprehensive tests",
                "severity": "medium",
            })

        # Domain coupling risks
        if len(analysis.domains) > 10:
            risks.append({
                "risk": "Many distinct domains may lead to coupling issues",
                "mitigation": "Define clear boundaries and interfaces between domains",
                "severity": "medium",
            })

        # Documentation risks
        if not analysis.readme_summary:
            risks.append({
                "risk": "Limited documentation may slow onboarding",
                "mitigation": "Create comprehensive README and architecture docs",
                "severity": "low",
            })

        return risks

    def _generate_scope(self, analysis: BrownPaperAnalysis) -> Dict[str, Any]:
        """Generate scope definition from domains."""
        in_scope = [
            f"{domain.name}: {domain.description[:100]}"
            for domain in analysis.domains[:8]
        ]

        out_of_scope = [
            "Infrastructure management",
            "Third-party service administration",
            "User authentication provider management",
        ]

        return {
            "in_scope": in_scope,
            "out_of_scope": out_of_scope,
            "boundaries": f"This system covers {len(analysis.domains)} business domains with {analysis.total_classes} classes.",
        }

    def _generate_success_criteria(self, analysis: BrownPaperAnalysis) -> List[Dict[str, str]]:
        """Generate success criteria."""
        criteria = []

        # Functional criteria from domains
        for domain in analysis.domains[:3]:
            criteria.append({
                "criterion": f"{domain.name} functionality is complete",
                "measurement": f"All {len(domain.use_cases)} identified use cases are implemented",
            })

        # Technical criteria
        criteria.append({
            "criterion": "Code quality maintained",
            "measurement": "Test coverage > 80%, no critical issues",
        })

        criteria.append({
            "criterion": "Documentation complete",
            "measurement": "All APIs documented, architecture docs up to date",
        })

        return criteria

    # ========================================================================
    # EPIC GENERATION
    # ========================================================================

    def enhance_domains_with_epic_searcher(
        self,
        session_id: str,
        project_path: Optional[str] = None
    ) -> List[BusinessDomain]:
        """
        Optionally enhance domain detection using CombinedEpicSearcher.

        Uses journey-based and folder-based detection to find meaningful
        business domains instead of relying solely on code pattern analysis.

        Args:
            session_id: The Brown Paper session ID
            project_path: Path to the project source code (optional)

        Returns:
            List of enhanced BusinessDomain objects
        """
        session = self._sessions.get(session_id)  # Direct cache access (sync method)
        if not session or not session.analysis:
            logger.warning(f"Cannot enhance domains: session {session_id} not found")
            return []

        # If no project_path provided, try to get from session
        if not project_path and session.analysis.project_path:
            project_path = session.analysis.project_path

        if not project_path:
            logger.info("No project_path available, skipping epic searcher enhancement")
            return session.analysis.domains

        try:
            # Configure the combined searcher
            config = CombinedSearchConfig(
                project_path=project_path,
                max_journey_depth=6,
                min_screens_per_journey=2,
                include_infrastructure=True,
                include_uncovered_folders=True,
            )

            # Run the combined search
            searcher = CombinedEpicSearcher(config)
            detected_epics: List[DetectedEpic] = searcher.search()

            if not detected_epics:
                logger.info("CombinedEpicSearcher found no epics, keeping existing domains")
                return session.analysis.domains

            # Convert detected epics to BusinessDomain objects
            enhanced_domains: List[BusinessDomain] = []

            for epic in detected_epics:
                domain = BusinessDomain(
                    name=epic.name,
                    description=epic.description,
                    modules=epic.source_folders,
                    entities=[],  # Will be enriched from existing analysis
                    use_cases=[],  # Will be enriched from existing analysis
                    priority="high" if epic.category == "business" else "medium",
                    complexity="medium",
                )

                # Add journey metadata if available
                if epic.metadata:
                    journey_count = epic.metadata.get("journey_count", 0)
                    actions = epic.metadata.get("actions", [])

                    # Convert actions to use cases
                    for action in actions[:10]:
                        domain.use_cases.append(action)

                    # Update description with journey info
                    if journey_count > 0:
                        domain.description = f"{epic.description} ({journey_count} user journeys)"

                enhanced_domains.append(domain)

            # Merge with existing domains to preserve entities and other metadata
            enhanced_domains = self._merge_domains(
                existing_domains=session.analysis.domains,
                new_domains=enhanced_domains
            )

            # Update session with enhanced domains
            session.analysis.domains = enhanced_domains
            session.updated_at = datetime.now(timezone.utc)

            logger.info(f"Enhanced domains with CombinedEpicSearcher: {len(enhanced_domains)} domains")
            return enhanced_domains

        except Exception as e:
            logger.warning(f"CombinedEpicSearcher enhancement failed: {e}")
            return session.analysis.domains

    def _merge_domains(
        self,
        existing_domains: List[BusinessDomain],
        new_domains: List[BusinessDomain]
    ) -> List[BusinessDomain]:
        """
        Merge existing domains with newly detected domains.

        Preserves entities and use_cases from existing domains when
        domains have matching names.
        """
        # Create lookup for existing domains
        existing_by_name: Dict[str, BusinessDomain] = {
            d.name.lower(): d for d in existing_domains
        }

        merged: List[BusinessDomain] = []

        for new_domain in new_domains:
            name_lower = new_domain.name.lower()

            # Check if there's a matching existing domain
            if name_lower in existing_by_name:
                existing = existing_by_name[name_lower]
                # Merge: keep new domain but enrich with existing data
                new_domain.entities = list(set(
                    new_domain.entities + existing.entities
                ))
                new_domain.use_cases = list(set(
                    new_domain.use_cases + existing.use_cases
                ))
                # Use more specific description if available
                if len(existing.description) > len(new_domain.description):
                    new_domain.description = existing.description

            merged.append(new_domain)

        # Add any existing domains that weren't in the new set
        existing_names_lower = {d.name.lower() for d in new_domains}
        for existing in existing_domains:
            if existing.name.lower() not in existing_names_lower:
                merged.append(existing)

        return merged

    async def generate_epics(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Generate Epics from domains.

        Each domain becomes an Epic with Features for each major use case group.
        """
        session = await self.get_session(session_id)
        if not session or not session.analysis:
            raise ValueError(f"Session not found or no analysis: {session_id}")

        analysis = session.analysis
        epics = []

        for domain in analysis.domains:
            epic = {
                "id": f"EPIC-{len(epics)+1:03d}",
                "name": domain.name,
                "domain": domain.name,  # Explicit domain field for clarity in persistence
                "description": domain.description,
                "priority": domain.priority,
                "complexity": domain.complexity,
                "source": "brown_paper_analysis",
                "features": [],
                "metadata": {
                    "modules": domain.modules,
                    "entities": domain.entities,
                    "domain_name": domain.name,  # Also in metadata for completeness
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                }
            }

            # Group use cases into features
            if domain.use_cases:
                # CRUD operations become one feature
                crud_cases = [uc for uc in domain.use_cases if any(
                    uc.startswith(prefix) for prefix in ["Create", "Retrieve", "Update", "Delete"]
                )]
                if crud_cases:
                    epic["features"].append({
                        "id": f"FEAT-{len(epics)+1:03d}-001",
                        "name": f"{domain.name} CRUD Operations",
                        "description": f"Basic create, read, update, delete operations for {domain.name}",
                        "use_cases": crud_cases,
                        "stories": [
                            {"title": uc, "points": 3} for uc in crud_cases
                        ],
                    })

                # Other use cases become separate features
                other_cases = [uc for uc in domain.use_cases if uc not in crud_cases]
                for i, use_case in enumerate(other_cases[:5]):
                    epic["features"].append({
                        "id": f"FEAT-{len(epics)+1:03d}-{i+2:03d}",
                        "name": use_case,
                        "description": f"Implementation of {use_case.lower()}",
                        "use_cases": [use_case],
                        "stories": [
                            {"title": use_case, "points": 5}
                        ],
                    })

            epics.append(epic)

        analysis.epics = epics
        session.updated_at = datetime.now(timezone.utc)

        if analysis.constitution:
            await self._persist_constitution_to_db(
                session_id=session_id,
                constitution=analysis.constitution,
                status=session.status.value if hasattr(session.status, "value") else session.status,
            )

        await self._persist_epics_to_db(session_id, epics)

        return epics

    # ========================================================================
    # APPROVAL WORKFLOW
    # ========================================================================

    async def approve_session(self, session_id: str, reviewer: str) -> bool:
        """Approve a Brown Paper session after review."""
        session = await self.get_session(session_id)
        if not session:
            return False

        if session.status != BrownPaperStatus.REVIEW:
            logger.warning(f"Cannot approve session {session_id} in status {session.status}")
            return False

        session.status = BrownPaperStatus.APPROVED
        session.updated_at = datetime.now(timezone.utc)

        # TODO: Persist to database and link to Green Paper models

        logger.info(f"Session {session_id} approved by {reviewer}")
        return True

    async def reject_session(
        self,
        session_id: str,
        reviewer: str,
        reason: str
    ) -> bool:
        """Reject a Brown Paper session."""
        session = await self.get_session(session_id)
        if not session:
            return False

        session.status = BrownPaperStatus.REJECTED
        session.error_message = f"Rejected by {reviewer}: {reason}"
        session.updated_at = datetime.now(timezone.utc)

        logger.info(f"Session {session_id} rejected by {reviewer}: {reason}")
        return True

    # =========================================================================
    # PHASE 20: BROWN PAPER ENHANCED - 6-PHASE DEEP ANALYSIS
    # =========================================================================

    async def run_enhanced_analysis(
        self,
        session_id: str,
        request: EnhancedAnalysisRequest,
        db: AsyncSession
    ) -> EnhancedAnalysisResponse:
        """
        Orchestrate 6-phase enhanced analysis using existing services.

        Phases:
        1. Code Understanding: DependencyGraph + CodeAnalysis + LayeredAnalysis
        2. Domain Extraction: Peter agent extracts business domains
        3. Hierarchical Extraction: HierarchicalStoryExtractionService
        4. Deep Extraction: DeepExtractionService + LLM Council
        5. Estimation: brown_paper_estimation_service (enhanced)
        6. Output: Consolidated documentation

        Args:
            session_id: MarQed session ID
            request: EnhancedAnalysisRequest with tier and options
            db: Database session

        Returns:
            EnhancedAnalysisResponse with all phase results
        """
        import time
        start_time = time.time()

        # Determine which phases to run based on tier
        phases_to_run = TIER_PHASES.get(request.tier, [1, 2, 3])
        target_confidence = TIER_CONFIDENCE_TARGETS.get(request.tier, 0.80)

        response = EnhancedAnalysisResponse(
            session_id=session_id,
            status="running",
            tier=request.tier,
            started_at=datetime.now(timezone.utc),
        )

        try:
            # Get session context - check both BrownPaper and MarQed sessions
            session = await self.get_session(session_id)
            project_path = None

            if session:
                # Regular BrownPaper session
                project_path = session.project_path
            else:
                # Try MarQed workflow session
                marqed_workflow = get_marqed_brown_paper_workflow()
                marqed_session = await marqed_workflow.get_session(session_id)
                if marqed_session:
                    project_path = marqed_session.project_path
                    # Store reference for later use in phase methods
                    session = marqed_session
                    logger.info(f"Using MarQed session {session_id} for enhanced analysis")

            if not project_path:
                response.status = "failed"
                response.errors.append(f"Session {session_id} not found in BrownPaper or MarQed workflow")
                return response

            # Phase 1: Code Understanding
            if 1 in phases_to_run:
                phase1 = await self._phase1_code_understanding(project_path, request.options, db)
                response.phase1_result = phase1
                response.phases_completed.append(1)
                if not phase1.success:
                    response.errors.extend(phase1.errors)

            # Phase 2: Domain Extraction
            # Week 159: Use enhanced business domain extraction if enabled
            use_business_logic_extraction = getattr(request.options, 'use_business_logic_extraction', True)

            if 2 in phases_to_run and response.phase1_result:
                if use_business_logic_extraction:
                    # New: Enhanced domain extraction with BusinessDomainExtractor
                    try:
                        domain_result = await self._enhanced_domain_extraction(
                            project_path, response.phase1_result, request.options
                        )
                        # Convert to Phase2Result format for compatibility
                        phase2 = Phase2Result()
                        phase2.domains = [
                            {
                                'name': d.name,
                                'module_count': len(d.modules),
                                'use_cases': d.use_cases,
                                'entities': [e.name for e in d.entities],
                                'confidence': d.confidence,
                                'source_files': d.source_files,
                            }
                            for d in domain_result.domains
                        ]
                        phase2.business_rules_count = sum(len(d.use_cases) for d in domain_result.domains)
                        phase2.success = True
                        phase2.duration_ms = domain_result.extraction_time_ms
                        # Store domain_result for Phase 3
                        response.business_domain_result = domain_result
                        logger.info(f"Enhanced domain extraction: {len(domain_result.domains)} domains found")
                    except Exception as e:
                        logger.warning(f"Enhanced domain extraction failed, falling back: {e}")
                        phase2 = await self._phase2_domain_extraction(
                            project_path, response.phase1_result, request.options, db
                        )
                else:
                    # Original domain extraction
                    phase2 = await self._phase2_domain_extraction(
                        project_path, response.phase1_result, request.options, db
                    )

                response.phase2_result = phase2
                response.phases_completed.append(2)
                if not phase2.success:
                    response.errors.extend(phase2.errors)

            # Phase 3: Hierarchical Extraction (or Business-Driven Story Generation)
            if 3 in phases_to_run and response.phase2_result:
                if use_business_logic_extraction and hasattr(response, 'business_domain_result'):
                    # New: Business-driven story generation
                    try:
                        story_result = await self._generate_business_driven_stories(
                            domain_result=response.business_domain_result,
                            phase1=response.phase1_result,
                        )
                        # Convert to Phase3Result format for compatibility
                        phase3 = Phase3Result()
                        phase3.epics = self._convert_story_result_to_epics(story_result)
                        phase3.total_stories = story_result.total_stories
                        phase3.total_story_points = story_result.total_story_points
                        phase3.success = True
                        phase3.duration_ms = story_result.generation_time_ms
                        logger.info(
                            f"Business-driven story generation: {len(phase3.epics)} epics, "
                            f"{story_result.total_stories} stories"
                        )
                    except Exception as e:
                        logger.warning(f"Business-driven story generation failed, falling back: {e}")
                        phase3 = await self._phase3_hierarchical_extraction(
                            project_path, response.phase2_result, request.options, db
                        )
                else:
                    # Original hierarchical extraction
                    phase3 = await self._phase3_hierarchical_extraction(
                        project_path, response.phase2_result, request.options, db
                    )

                response.phase3_result = phase3
                response.phases_completed.append(3)
                if not phase3.success:
                    response.errors.extend(phase3.errors)

            # Phase 4: Deep Extraction
            if 4 in phases_to_run and response.phase3_result:
                phase4 = await self._phase4_deep_extraction(
                    project_path, response.phase3_result, request.tier, db
                )
                response.phase4_result = phase4
                response.phases_completed.append(4)
                if not phase4.success:
                    response.errors.extend(phase4.errors)

            # Phase 5: Estimation
            if 5 in phases_to_run:
                phase5 = await self._phase5_estimation(
                    session_id, response, request.options
                )
                response.phase5_result = phase5
                response.phases_completed.append(5)
                if not phase5.success:
                    response.errors.extend(phase5.errors)

            # Phase 6: Output consolidation
            if 6 in phases_to_run:
                response = await self._phase6_output(session_id, response)
                response.phases_completed.append(6)

            # Calculate overall confidence
            response.confidence = self._calculate_confidence(response, target_confidence)
            response.status = "completed" if not response.errors else "partial"

        except Exception as e:
            logger.error(f"Enhanced analysis failed: {e}", exc_info=True)
            response.status = "failed"
            response.errors.append(str(e))

        response.completed_at = datetime.now(timezone.utc)
        response.total_duration_ms = int((time.time() - start_time) * 1000)

        # Store enhanced analysis in session for later retrieval
        if session:
            session.enhanced_analysis = {
                'phase1_result': vars(response.phase1_result) if response.phase1_result else None,
                'phase2_result': vars(response.phase2_result) if response.phase2_result else None,
                'phase3_result': vars(response.phase3_result) if response.phase3_result else None,
                'phase4_result': vars(response.phase4_result) if response.phase4_result else None,
                'phase5_result': vars(response.phase5_result) if response.phase5_result else None,
                'summary': vars(response.summary) if response.summary else None,
                'confidence': response.confidence,
                'phases_completed': response.phases_completed,
                'total_duration_ms': response.total_duration_ms,
            }
            session.updated_at = datetime.now(timezone.utc)
            logger.info(f"Enhanced analysis stored for session {session_id}")

            # Persist enhanced analysis to database
            # Use MarQed workflow for MarQed sessions
            if isinstance(session, MarQedBrownPaperSession):
                marqed_workflow = get_marqed_brown_paper_workflow()
                await marqed_workflow._persist_session_to_db(session)
            else:
                # For regular BrownPaper sessions, store in session object
                # (already stored in memory, will be persisted on next access)
                pass

        return response

    async def _phase1_code_understanding(
        self,
        project_path: str,
        options: EnhancedAnalysisOptions,
        db: AsyncSession
    ) -> Phase1Result:
        """
        Phase 1: Run DependencyGraph, CodeAnalysis, and LayeredAnalysis services.

        Uses existing services - NO NEW LOGIC, just integration.
        """
        import time
        start_time = time.time()
        result = Phase1Result()

        try:
            # 1. DependencyGraphService - uses analyze_directory (sync method)
            dep_service = DependencyGraphService()
            dep_result = dep_service.analyze_directory(project_path)
            result.dependency_graph = dep_result.to_dict() if hasattr(dep_result, 'to_dict') else dep_result

        except Exception as e:
            logger.warning(f"DependencyGraph analysis failed: {e}")
            result.errors.append(f"DependencyGraph: {e}")

        try:
            # 2. CodeAnalysisAggregatorService - correct method is analyze()
            code_service = CodeAnalysisAggregatorService(db)
            # analyze(project_id, repository_path, branch, include_codewiki, timeout_seconds)
            # Note: include_codewiki=False for adhoc analysis (project_id=0 causes FK violation)
            code_result = await code_service.analyze(
                project_id=0,  # Adhoc analysis - no DB project record
                repository_path=project_path,
                branch="main",
                include_codewiki=False,  # Disabled for adhoc (FK constraint on codewiki_analyses)
                timeout_seconds=300
            )
            result.code_analysis = code_result.to_dict() if hasattr(code_result, 'to_dict') else code_result

        except Exception as e:
            logger.warning(f"CodeAnalysis aggregation failed: {e}")
            result.errors.append(f"CodeAnalysis: {e}")

        try:
            # 3. LayeredAnalysisService - needs create_session first, then run_full_analysis
            # Signature: create_session(project_id: UUID, name: str, description: Optional[str])
            if not options.skip_vbscript:
                from uuid import uuid4
                layered_service = LayeredAnalysisService(db)
                # Create a session first with correct parameters
                session = await layered_service.create_session(
                    project_id=uuid4(),  # Generate adhoc project ID
                    name=f"BrownPaper-{project_path.split('/')[-1]}",
                    description=f"Enhanced analysis for {project_path}"
                )
                session_id = session.id if hasattr(session, 'id') else session.get('id')
                # Then run full analysis
                if session_id:
                    layered_result = await layered_service.run_full_analysis(session_id)
                    result.layered_analysis = layered_result if isinstance(layered_result, dict) else layered_result

        except Exception as e:
            logger.warning(f"LayeredAnalysis failed: {e}")
            result.errors.append(f"LayeredAnalysis: {e}")

        try:
            # 4. FoundationDetectionService - detect foundation/infrastructure modules
            # Uses dependency graph from step 1 to identify hub modules
            if result.dependency_graph:
                from app.services.foundation_detection_service import get_foundation_detection_service
                foundation_service = get_foundation_detection_service()
                foundation_result = foundation_service.detect_foundation(
                    dependency_graph=result.dependency_graph,
                    code_metrics=result.code_analysis,
                    project_path=project_path
                )
                result.foundation = foundation_result.to_dict()
                logger.info(
                    f"Foundation detection: {foundation_result.detection_stats.get('foundation_modules', 0)} "
                    f"foundation modules, {foundation_result.detection_stats.get('non_foundation_modules', 0)} business modules"
                )

        except Exception as e:
            logger.warning(f"Foundation detection failed: {e}")
            result.errors.append(f"FoundationDetection: {e}")

        # Week 131: Background Job Detection
        try:
            from app.services.background_job_detector_service import BackgroundJobDetectorService
            from pathlib import Path
            bg_service = BackgroundJobDetectorService()
            bg_result = bg_service.detect(project_path=Path(project_path))
            result.background_jobs = bg_result.to_dict()
            logger.info(
                f"Background job detection: {bg_result.total_jobs} jobs detected "
                f"({len(bg_result.by_job_type)} types)"
            )
        except Exception as e:
            logger.warning(f"Background job detection failed: {e}")
            result.errors.append(f"BackgroundJobDetection: {e}")

        # Week 131: Load Estimation
        try:
            from app.services.load_estimation_service import LoadEstimationService
            from pathlib import Path
            load_service = LoadEstimationService()
            load_result = load_service.analyze(project_path=Path(project_path))
            result.load_estimation = load_result.to_dict()
            logger.info(
                f"Load estimation: {load_result.estimated_concurrent_users} concurrent users, "
                f"bottleneck: {load_result.capacity_bottleneck}"
            )
        except Exception as e:
            logger.warning(f"Load estimation failed: {e}")
            result.errors.append(f"LoadEstimation: {e}")

        # Week 132-133: Dead Code Detection (Fase 22)
        try:
            from app.services.dead_code_detector_service import DeadCodeDetectorService
            from pathlib import Path
            dead_code_service = DeadCodeDetectorService()
            dead_code_result = dead_code_service.detect(project_path=Path(project_path))
            result.dead_code_analysis = dead_code_result.to_dict()
            logger.info(
                f"Dead code detection: {dead_code_result.dead_code_count} items found, "
                f"{dead_code_result.safe_removal_count} safe to remove"
            )
        except Exception as e:
            logger.warning(f"Dead code detection failed: {e}")
            result.errors.append(f"DeadCodeDetection: {e}")

        # Week 132-133: Runtime Analysis (Fase 22)
        try:
            from app.services.runtime_analysis_service import RuntimeAnalysisService
            from pathlib import Path
            runtime_service = RuntimeAnalysisService()
            runtime_result = runtime_service.analyze(project_path=Path(project_path))
            result.runtime_analysis = runtime_result.to_dict()
            logger.info(
                f"Runtime analysis: {runtime_result.called_functions}/{runtime_result.total_functions} "
                f"functions called ({runtime_result.coverage_percentage:.1f}% coverage)"
            )
        except Exception as e:
            logger.warning(f"Runtime analysis failed: {e}")
            result.errors.append(f"RuntimeAnalysis: {e}")

        # Week 132-133: Code Coverage Analysis (Fase 22)
        try:
            from app.services.code_coverage_analyzer_service import CodeCoverageAnalyzerService
            from pathlib import Path
            coverage_service = CodeCoverageAnalyzerService()
            coverage_result = coverage_service.analyze(project_path=Path(project_path))
            result.coverage_analysis = coverage_result.to_dict()
            logger.info(
                f"Coverage analysis: {coverage_result.line_coverage_percentage:.1f}% line, "
                f"{coverage_result.branch_coverage_percentage:.1f}% branch coverage"
            )
        except Exception as e:
            logger.warning(f"Coverage analysis failed: {e}")
            result.errors.append(f"CoverageAnalysis: {e}")

        # Week 136-137: Data Lineage Session (Fase 24)
        try:
            from app.services.data_lineage_service import DataLineageService
            from app.models.data_architecture import LineageNodeType
            lineage_service = DataLineageService(db)
            # Create session for lineage tracking
            session_id = await lineage_service.create_session(
                name=f"BrownPaper-{project_path.split('/')[-1]}",
                project_id=None,
                description=f"Data lineage for {project_path}"
            )
            # Build initial lineage from dependency graph
            if result.dependency_graph:
                nodes_created = 0
                dep_data = result.dependency_graph
                # Add module nodes from dependency graph
                for module_path in dep_data.get('modules', [])[:100]:  # Limit to 100
                    await lineage_service.add_node(
                        session_id=session_id,
                        node_type=LineageNodeType.CODE_FILE,
                        name=module_path.split('/')[-1] if '/' in module_path else module_path,
                        source_path=module_path
                    )
                    nodes_created += 1
                await lineage_service.save_session(session_id)
                logger.info(f"Data lineage: session {session_id[:8]}, {nodes_created} nodes from dependency graph")
            result.data_lineage_result = {
                "session_id": session_id,
                "status": "initialized",
                "nodes_created": nodes_created if result.dependency_graph else 0,
                "note": "Lineage populated in later phases"
            }
        except Exception as e:
            logger.warning(f"Data lineage initialization failed: {e}")
            result.errors.append(f"DataLineage: {e}")

        # Week 136-137: ERD Generation (Fase 24)
        # Note: ERD generation requires entities from Phase 2 domain extraction
        # In Phase 1, we just indicate it will be generated later
        result.erd_generation_result = {
            "status": "pending",
            "note": "ERD generated in Phase 2 after domain extraction"
        }

        # Week 144: SIG Top 10 Quality Metrics (Fase 21+)
        try:
            from app.scanners.dotnet.dotnet_scanner import DotNetVolumeScanner, DotNetDuplicationScanner
            from app.scanners.metrics.complexity_analyzer import ComplexityAnalyzer
            from app.scanners.metrics.interfacing_analyzer import InterfacingAnalyzer
            from app.scanners.metrics.coupling_analyzer import CouplingAnalyzer
            from app.scanners.metrics.balance_analyzer import BalanceAnalyzer
            from app.scanners.metrics.duplication_analyzer import DuplicationAnalyzer
            from app.scanners.metrics.comments_analyzer import CommentsAnalyzer

            sig_results = {
                "ratings": {},
                "overall_rating": 0,
                "volume": {},
                "findings_summary": {
                    "total": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                },
            }

            # Run SIG analyzers
            analyzers = {
                "volume": DotNetVolumeScanner(project_path),
                "complexity": ComplexityAnalyzer(project_path),
                "interfacing": InterfacingAnalyzer(project_path),
                "coupling": CouplingAnalyzer(project_path),
                "balance": BalanceAnalyzer(project_path),
                "duplication": DuplicationAnalyzer(project_path),
                "comments": CommentsAnalyzer(project_path),
            }

            ratings = []
            for name, analyzer in analyzers.items():
                try:
                    scan_result = await analyzer.scan()
                    if scan_result.success and scan_result.metrics:
                        metadata = scan_result.metrics.metadata or {}
                        rating = metadata.get("rating")
                        if rating:
                            sig_results["ratings"][name] = {
                                "rating": rating,
                                "stars": "★" * rating + "☆" * (5 - rating),
                            }
                            ratings.append(rating)
                        if name == "volume":
                            sig_results["volume"] = {
                                "files_scanned": scan_result.metrics.files_scanned,
                                "lines_of_code": scan_result.metrics.lines_of_code,
                                "code_lines": scan_result.metrics.code_lines,
                            }
                        if scan_result.findings:
                            sig_results["findings_summary"]["total"] += len(scan_result.findings)
                            for f in scan_result.findings:
                                sev = f.severity.value
                                if sev in sig_results["findings_summary"]:
                                    sig_results["findings_summary"][sev] += 1
                except Exception as sig_err:
                    logger.warning(f"SIG {name} analyzer failed: {sig_err}")

            if ratings:
                sig_results["overall_rating"] = round(sum(ratings) / len(ratings), 1)
                sig_results["overall_stars"] = "★" * int(sig_results["overall_rating"]) + "☆" * (5 - int(sig_results["overall_rating"]))

            result.sig_metrics = sig_results
            logger.info(
                f"SIG metrics: {len(ratings)} analyzers, overall rating: {sig_results.get('overall_rating', 0)}/5, "
                f"{sig_results['findings_summary']['total']} findings"
            )
        except Exception as e:
            logger.warning(f"SIG metrics failed: {e}")
            result.errors.append(f"SIGMetrics: {e}")

        result.duration_ms = int((time.time() - start_time) * 1000)
        result.success = len(result.errors) == 0 or result.dependency_graph is not None or result.code_analysis is not None

        return result

    async def _phase2_domain_extraction(
        self,
        project_path: str,
        phase1: Phase1Result,
        options: EnhancedAnalysisOptions,
        db: AsyncSession
    ) -> Phase2Result:
        """
        Phase 2: Extract business domains from Phase 1 analysis.

        Uses Phase 1 dependency graph to identify domain boundaries.
        EXCLUDES foundation modules detected in Phase 1.
        """
        import time
        start_time = time.time()
        result = Phase2Result()

        # Get foundation module names to exclude
        foundation_module_names: set = set()
        if phase1.foundation:
            for fm in phase1.foundation.get('foundation_modules', []):
                foundation_module_names.add(fm.get('name', ''))
            logger.info(f"Excluding {len(foundation_module_names)} foundation modules from domain extraction")

        try:
            # Extract domains from Phase 1 dependency graph
            domains = []
            if phase1.dependency_graph:
                dep_graph = phase1.dependency_graph
                # Get modules from graph - can be dict or list
                modules_data = dep_graph.get('modules', {}) if isinstance(dep_graph, dict) else {}

                # Normalize to list of module dicts
                # modules_data can be: dict (name -> info), list of dicts, or list of strings
                module_list: List[Dict] = []
                if isinstance(modules_data, dict):
                    # Dict: keys are module names, values are module info
                    for mod_name, mod_info in modules_data.items():
                        if isinstance(mod_info, dict):
                            module_list.append(mod_info)
                        else:
                            # Value is not a dict, create one with the key as name
                            module_list.append({'name': mod_name})
                elif isinstance(modules_data, list):
                    for item in modules_data:
                        if isinstance(item, dict):
                            module_list.append(item)
                        else:
                            module_list.append({'name': str(item)})

                # Group by directory/domain (excluding foundation modules)
                domain_groups: Dict[str, List[Dict]] = {}
                for module in module_list:
                    name = module.get('name', '') or module.get('path', '')
                    # Skip foundation modules
                    if name in foundation_module_names:
                        continue
                    # Extract domain from module path/name
                    parts = name.replace('\\', '/').split('/')
                    domain_name = parts[0] if len(parts) > 1 else 'Core'
                    if domain_name not in domain_groups:
                        domain_groups[domain_name] = []
                    domain_groups[domain_name].append(module)

                # Create domain entries
                for domain_name, domain_modules in domain_groups.items():
                    if len(domain_modules) >= 2:
                        domains.append({
                            'name': domain_name,
                            'module_count': len(domain_modules),
                            'use_cases': [m.get('name', m.get('path', 'unknown')) for m in domain_modules[:5]],
                        })

            result.domains = domains
            result.business_rules_count = sum(len(d.get('use_cases', [])) for d in domains)
            result.success = True

            # Map to CAFCR categories based on Phase 1 metrics
            if phase1.code_analysis:
                result.cafcr_mapping = self._map_to_cafcr(domains, phase1.code_analysis)

            # Determine module boundaries from dependency graph
            if phase1.dependency_graph:
                result.module_boundaries = self._extract_module_boundaries(phase1.dependency_graph)

        except Exception as e:
            logger.error(f"Domain extraction failed: {e}", exc_info=True)
            result.errors.append(str(e))
            result.success = False

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    # =========================================================================
    # WEEK 159: BUSINESS LOGIC EXTRACTION - PVA IMPLEMENTATION
    # =========================================================================

    async def _enhanced_domain_extraction(
        self,
        project_path: str,
        phase1: Phase1Result,
        options: EnhancedAnalysisOptions,
    ) -> BusinessDomainExtractionResult:
        """
        Enhanced domain extraction using BusinessDomainExtractor.

        Week 159 PVA: Improves upon basic Phase 2 extraction with:
        - Module clustering based on dependencies
        - Healthcare/FysioOne specific domain patterns
        - Entity extraction from classes, tables, forms
        - Source file references for traceability

        Args:
            project_path: Path to project being analyzed
            phase1: Phase 1 code analysis results

        Returns:
            BusinessDomainExtractionResult with detailed domains
        """
        logger.info(f"Starting enhanced domain extraction for {project_path}")

        # Create extractor with healthcare patterns (FysioOne)
        extractor = get_business_domain_extractor(
            use_healthcare_patterns=True
        )

        # Prepare modules from Phase 1
        modules = []
        if phase1.dependency_graph:
            dep_graph = phase1.dependency_graph
            modules_data = dep_graph.get('modules', {}) if isinstance(dep_graph, dict) else {}

            # Normalize to list of module dicts
            if isinstance(modules_data, dict):
                for mod_name, mod_info in modules_data.items():
                    if isinstance(mod_info, dict):
                        mod_info['name'] = mod_name
                        modules.append(mod_info)
                    else:
                        modules.append({'name': mod_name, 'path': mod_name})
            elif isinstance(modules_data, list):
                for item in modules_data:
                    if isinstance(item, dict):
                        modules.append(item)
                    else:
                        modules.append({'name': str(item), 'path': str(item)})

        # Prepare dependencies from Phase 1
        dependencies = []
        if phase1.dependency_graph:
            dep_graph = phase1.dependency_graph
            edges = dep_graph.get('edges', []) if isinstance(dep_graph, dict) else []
            for edge in edges:
                if isinstance(edge, dict):
                    dependencies.append(edge)
                elif isinstance(edge, (list, tuple)) and len(edge) >= 2:
                    dependencies.append({'source': edge[0], 'target': edge[1]})

        # Extract domains
        result = await extractor.extract_domains(
            modules=modules,
            dependencies=dependencies,
            scan_path=project_path,
        )

        logger.info(
            f"Enhanced extraction found {len(result.domains)} domains "
            f"from {len(modules)} modules in {result.extraction_time_ms}ms"
        )

        return result

    async def _generate_business_driven_stories(
        self,
        domain_result: BusinessDomainExtractionResult,
        phase1: Optional[Phase1Result] = None,
        specification_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> StoryGenerationResult:
        """
        Generate stories using BusinessDrivenStoryGenerator.

        Week 159 PVA: Creates meaningful epics/stories based on:
        - Business domains (not generic phases)
        - Source file references
        - Acceptance criteria from code analysis
        - Story points based on complexity

        Args:
            domain_result: Result from enhanced domain extraction
            phase1: Optional Phase 1 code analysis for enrichment
            specification_id: Optional spec ID for linking
            project_id: Optional project ID for linking

        Returns:
            StoryGenerationResult with epics, features, stories
        """
        logger.info(f"Generating business-driven stories for {len(domain_result.domains)} domains")

        # Create generator
        generator = get_business_driven_story_generator(velocity=20)

        # Generate stories
        code_analysis = None
        if phase1 and phase1.code_analysis:
            code_analysis = phase1.code_analysis

        result = await generator.generate_stories(
            domain_result=domain_result,
            code_analysis=code_analysis,
        )

        logger.info(
            f"Generated {result.total_stories} stories in {len(result.epics)} epics "
            f"({result.total_story_points} story points)"
        )

        return result

    def _convert_story_result_to_epics(
        self,
        story_result: StoryGenerationResult,
    ) -> List[Dict[str, Any]]:
        """
        Convert StoryGenerationResult to Brown Paper epic format.

        Maintains compatibility with existing epic persistence.
        """
        epics = []

        for epic in story_result.epics:
            epic_dict = {
                "id": epic.id,
                "name": epic.title,
                "domain": epic.domain_name,
                "description": epic.description,
                "priority": len(story_result.epics) - story_result.epics.index(epic),
                "complexity": epic.complexity,
                "source": "business_driven_story_generator",
                "features": [],
                "metadata": {
                    "modules": epic.source_modules,
                    "domain_name": epic.domain_name,
                    "estimated_story_points": epic.estimated_story_points,
                    "estimated_weeks": epic.estimated_weeks,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    **epic.metadata,
                }
            }

            for feature in epic.features:
                feature_dict = {
                    "id": feature.id,
                    "name": feature.title,
                    "description": feature.description,
                    "use_cases": [s.title for s in feature.stories],
                    "stories": [],
                }

                for story in feature.stories:
                    story_dict = {
                        "id": story.id,
                        "title": story.title,
                        "description": story.description,
                        "points": story.story_points,
                        "acceptance_criteria": [
                            {"id": ac.id, "description": ac.description}
                            for ac in story.acceptance_criteria
                        ],
                        "source_references": [
                            {
                                "file_path": sr.file_path,
                                "line_start": sr.line_start,
                                "element_type": sr.element_type,
                            }
                            for sr in story.source_references
                        ],
                        "story_type": story.story_type,
                        "complexity": story.complexity,
                    }
                    feature_dict["stories"].append(story_dict)

                epic_dict["features"].append(feature_dict)

            epics.append(epic_dict)

        return epics

    async def run_business_logic_extraction(
        self,
        session_id: str,
        phase1: Phase1Result,
        project_path: str,
    ) -> Tuple[List[Dict[str, Any]], BusinessDomainExtractionResult]:
        """
        Run complete business logic extraction workflow.

        Week 159 PVA: Main entry point for improved epic/story generation.

        Steps:
        1. Enhanced domain extraction (using BusinessDomainExtractor)
        2. Business-driven story generation
        3. Convert to Brown Paper format

        Args:
            session_id: Brown Paper session ID
            phase1: Phase 1 code analysis results
            project_path: Path to project

        Returns:
            Tuple of (epics list, domain extraction result)
        """
        logger.info(f"Running business logic extraction for session {session_id}")

        # Step 1: Enhanced domain extraction
        domain_result = await self._enhanced_domain_extraction(
            project_path=project_path,
            phase1=phase1,
            options=EnhancedAnalysisOptions(),
        )

        # Step 2: Generate business-driven stories
        story_result = await self._generate_business_driven_stories(
            domain_result=domain_result,
            phase1=phase1,
        )

        # Step 3: Convert to Brown Paper format
        epics = self._convert_story_result_to_epics(story_result)

        logger.info(
            f"Business logic extraction complete: {len(epics)} epics, "
            f"{story_result.total_stories} stories, "
            f"{story_result.total_story_points} story points"
        )

        return epics, domain_result

    async def _phase3_hierarchical_extraction(
        self,
        project_path: str,
        phase2: Phase2Result,
        options: EnhancedAnalysisOptions,
        db: AsyncSession
    ) -> Phase3Result:
        """
        Phase 3: Run HierarchicalStoryExtractionService.

        Uses existing service - NO NEW LOGIC.
        """
        import time
        start_time = time.time()
        result = Phase3Result()

        try:
            # Use HierarchicalStoryExtractionService
            # Note: Uses extract_hierarchical (not extract_stories)
            hier_service = HierarchicalStoryExtractionService(db)

            # Map tier from options (default to FREE if not specified)
            from app.services.hierarchical_story_extraction_service import ExtractionTier
            tier = ExtractionTier.FREE
            if hasattr(options, 'tier') and options.tier:
                tier_map = {
                    'free': ExtractionTier.FREE,
                    'basic': ExtractionTier.BASIC,
                    'standard': ExtractionTier.STANDARD,
                    'professional': ExtractionTier.PROFESSIONAL,
                    'premium': ExtractionTier.PREMIUM,
                }
                tier = tier_map.get(options.tier.lower(), ExtractionTier.FREE)

            # Week 129: Use project_id=0 for adhoc analysis (no project record)
            extraction = await hier_service.extract_hierarchical(
                project_id=0,  # Adhoc analysis without project record
                repository_path=project_path,
                tier=tier,
                include_cira_analysis=options.include_cira
            )

            result.extraction_result = extraction.to_dict() if hasattr(extraction, 'to_dict') else vars(extraction)

            # Extract CiRA causal relations if available
            if options.include_cira and hasattr(extraction, 'causal_relations'):
                result.causal_relations = extraction.causal_relations

        except Exception as e:
            logger.error(f"Hierarchical extraction failed: {e}", exc_info=True)
            result.errors.append(str(e))
            result.success = False

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    async def _phase4_deep_extraction(
        self,
        project_path: str,
        phase3: Phase3Result,
        tier: EnhancedAnalysisTier,
        db: AsyncSession
    ) -> Phase4Result:
        """
        Phase 4: Run DeepExtractionService with LLM Council.

        Uses existing service - NO NEW LOGIC.
        """
        import time
        start_time = time.time()
        result = Phase4Result()

        try:
            # Note: DeepExtractionService requires a valid project_id (FK constraint)
            # For adhoc analysis, we synthesize results from Phase 3 hierarchical extraction
            # instead of calling the full extraction service

            # Synthesize deep extraction from Phase 3 results
            result.deep_extraction_result = {
                'source': 'synthesized_from_phase3',
                'tier': tier.value if hasattr(tier, 'value') else str(tier),
                'extraction_method': 'hierarchical_to_deep',
                'note': 'Full DeepExtractionService requires DB project - using Phase 3 synthesis for adhoc analysis'
            }

            # Use Phase 3 epics/features/stories if available
            if phase3.hierarchical_structure:
                hier = phase3.hierarchical_structure
                result.deep_extraction_result['epics'] = hier.get('epics', [])
                result.deep_extraction_result['features'] = hier.get('features', [])
                result.deep_extraction_result['stories'] = hier.get('stories', [])
                result.deep_extraction_result['total_items'] = (
                    len(hier.get('epics', [])) +
                    len(hier.get('features', [])) +
                    len(hier.get('stories', []))
                )

            # No conflicts for synthesized extraction
            result.conflicts = []
            result.consensus_confidence = 0.75  # Default confidence for synthesis
            result.human_review_needed = 0
            result.success = True

        except Exception as e:
            logger.error(f"Deep extraction failed: {e}", exc_info=True)
            result.errors.append(str(e))
            result.success = False

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    async def _phase5_estimation(
        self,
        session_id: str,
        response: EnhancedAnalysisResponse,
        options: EnhancedAnalysisOptions
    ) -> Phase5Result:
        """
        Phase 5: Run brown_paper_estimation_service with complexity enhancement.

        Uses existing service - adds complexity metrics from Phase 1.
        """
        import time
        start_time = time.time()
        result = Phase5Result()

        try:
            # Get estimation service
            estimation_service = get_brown_paper_estimation_service()

            # Prepare estimation input with Phase 1 complexity data
            complexity_multiplier = 1.0
            if response.phase1_result and response.phase1_result.code_analysis:
                metrics = response.phase1_result.code_analysis
                # Adjust multiplier based on complexity profile
                high_complexity = metrics.get('complexity_profile', {}).get('high', 0)
                very_high = metrics.get('complexity_profile', {}).get('very_high', 0)
                if very_high > 10:
                    complexity_multiplier = 1.5
                elif high_complexity > 20:
                    complexity_multiplier = 1.3
                elif high_complexity > 10:
                    complexity_multiplier = 1.15

            result.complexity_multiplier = complexity_multiplier

            # Get project path from session to analyze
            session = self.sessions.get(session_id)
            project_path = session.project_path if session else None

            if project_path:
                from pathlib import Path
                # Run estimation using analyze_directory (sync method)
                estimation = estimation_service.analyze_directory(
                    directory=Path(project_path),
                    recursive=True
                )

                # Convert to dict and apply complexity multiplier
                estimation_dict = estimation.to_dict() if hasattr(estimation, 'to_dict') else estimation
                if isinstance(estimation_dict, dict) and 'total_afp' in estimation_dict:
                    # Apply complexity multiplier to AFP
                    estimation_dict['adjusted_afp'] = int(estimation_dict['total_afp'] * complexity_multiplier)

                result.estimation_result = estimation_dict
            else:
                result.estimation_result = {'error': 'No project path available for estimation'}

            # Add risk assessment based on circular dependencies
            if response.phase1_result and response.phase1_result.dependency_graph:
                dep_graph = response.phase1_result.dependency_graph
                circular_deps = dep_graph.get('circular_dependencies', [])
                result.risk_assessment = {
                    'circular_dependencies': len(circular_deps),
                    'risk_level': 'high' if len(circular_deps) > 5 else 'medium' if len(circular_deps) > 0 else 'low',
                    'circular_details': circular_deps[:5]  # Top 5
                }

        except Exception as e:
            logger.error(f"Estimation failed: {e}", exc_info=True)
            result.errors.append(str(e))
            result.success = False

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    async def _phase6_output(
        self,
        session_id: str,
        response: EnhancedAnalysisResponse
    ) -> EnhancedAnalysisResponse:
        """
        Phase 6: Consolidate all outputs and generate summary.
        """
        # Calculate summary statistics
        summary = EnhancedAnalysisSummary()

        if response.phase3_result and response.phase3_result.extraction_result:
            extraction = response.phase3_result.extraction_result
            summary.epics = len(extraction.get('epics', []))
            summary.features = len(extraction.get('features', []))
            summary.stories = len(extraction.get('stories', []))
            summary.tasks = len(extraction.get('tasks', []))

        if response.phase5_result and response.phase5_result.estimation_result:
            estimation = response.phase5_result.estimation_result
            summary.total_fp = estimation.get('total_fp', 0)
            summary.total_sp = estimation.get('total_sp', 0)
            summary.estimated_hours = estimation.get('estimated_hours', 0.0)

        summary.confidence = response.confidence
        response.summary = summary

        # Set output URLs
        response.dependency_graph_url = f"/api/brown-paper/marqed/{session_id}/dependency-graph"
        response.hierarchy_url = f"/api/brown-paper/marqed/{session_id}/hierarchy"
        response.metrics_url = f"/api/brown-paper/marqed/{session_id}/metrics"
        response.conflicts_url = f"/api/brown-paper/marqed/{session_id}/conflicts"

        return response

    def _calculate_confidence(
        self,
        response: EnhancedAnalysisResponse,
        target: float
    ) -> float:
        """Calculate overall confidence score based on phase completions."""
        completed = len(response.phases_completed)
        total_phases = 6

        # Base confidence from completion rate
        base = (completed / total_phases) * target

        # Adjust based on phase4 consensus confidence
        if response.phase4_result and response.phase4_result.consensus_confidence:
            consensus = response.phase4_result.consensus_confidence
            base = (base + consensus) / 2

        # Reduce confidence if there are errors
        error_penalty = min(len(response.errors) * 0.05, 0.20)

        return max(0.0, min(1.0, base - error_penalty))

    def _map_to_cafcr(
        self,
        domains: List[Any],
        code_analysis: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Map domains to CAFCR categories based on code analysis."""
        cafcr = {
            'Customer': [],      # User-facing
            'Application': [],   # Business logic
            'Functional': [],    # Core features
            'Conceptual': [],    # Domain model
            'Realization': []    # Infrastructure
        }

        for domain in domains:
            name = domain.get('name', '') if isinstance(domain, dict) else getattr(domain, 'name', '')
            domain_type = domain.get('type', '') if isinstance(domain, dict) else getattr(domain, 'type', '')

            if 'ui' in name.lower() or 'view' in name.lower() or 'presentation' in name.lower():
                cafcr['Customer'].append(name)
            elif 'service' in name.lower() or 'business' in name.lower():
                cafcr['Application'].append(name)
            elif 'model' in name.lower() or 'entity' in name.lower():
                cafcr['Conceptual'].append(name)
            elif 'repository' in name.lower() or 'database' in name.lower() or 'infra' in name.lower():
                cafcr['Realization'].append(name)
            else:
                cafcr['Functional'].append(name)

        return cafcr

    def _extract_module_boundaries(
        self,
        dependency_graph: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Extract module boundaries from dependency graph."""
        boundaries = {}

        nodes = dependency_graph.get('nodes', [])
        edges = dependency_graph.get('edges', [])

        # Group nodes by parent module
        for node in nodes:
            node_id = node.get('id', '')
            parts = node_id.split('.')
            if len(parts) > 1:
                module = parts[0]
                if module not in boundaries:
                    boundaries[module] = []
                boundaries[module].append(node_id)

        return boundaries


# ============================================================================
# MARQED BROWN-PAPER WORKFLOW (8 Strategic Questions)
# ============================================================================

@dataclass
class MarQedAnswer:
    """A single MarQed question answer."""
    question_number: int
    question_text: str
    answer: str
    answered_at: datetime


@dataclass
class MigrationAnalysisResult:
    """Result from Miguel's migration analysis (Stage 1)."""
    complexity: str  # LOW, MEDIUM, HIGH, VERY_HIGH
    complexity_justification: str
    risk_register: List[Dict[str, Any]]
    recommended_phases: List[Dict[str, Any]]
    technical_spikes: List[str]
    go_no_go_checkpoints: List[str]
    analyzed_at: datetime
    success: bool = True  # Added for consistency with other result types (BUG-001 fix)


@dataclass
class MarQedBrownPaperSession:
    """A MarQed Brown-Paper session tracking the 8-question workflow."""
    id: str
    project_name: str
    project_path: Optional[str]
    status: str  # questions, analyzing, generating, review, approved, rejected
    current_question: int  # 1-8
    answers: Dict[int, MarQedAnswer]
    migration_analysis: Optional[MigrationAnalysisResult]
    specification: Optional[Dict[str, Any]]
    tasks: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    enhanced_analysis: Optional[Dict[str, Any]] = None  # Week 129: 6-phase analysis results
    vector_context: Optional[Dict[str, Any]] = None  # Week 143: Vector DB pre-populated context

    @property
    def total_questions(self) -> int:
        """Return total number of questions (always 8)."""
        return 8


# The 8 MarQed Brown-Paper Questions
MARQED_QUESTIONS = {
    1: {
        "question": "Describe the current legacy system to be migrated",
        "description": "Technology stack, size (LOC, modules, pages, tables), age, known issues, deployment",
        "required": True,
        "min_length": 50,
    },
    2: {
        "question": "What is the target state after migration?",
        "description": "Target technology stack, architecture pattern, deployment platform",
        "required": True,
        "min_length": 50,
    },
    3: {
        "question": "What migration strategy will be used?",
        "description": "Strangler Fig, Big Bang, or Parallel Run. Phasing approach, rollback strategy",
        "required": True,
        "min_length": 50,
    },
    4: {
        "question": "How will data be migrated?",
        "description": "Schema changes, transformation requirements, validation approach, tooling",
        "required": True,
        "min_length": 30,
    },
    5: {
        "question": "What problems does this migration solve?",
        "description": "Current pain points, quantified impact, why migration is necessary NOW",
        "required": True,
        "min_length": 50,
    },
    6: {
        "question": "Who are the users and stakeholders affected?",
        "description": "Primary users, stakeholders, change impact, training needs",
        "required": True,
        "min_length": 30,
    },
    7: {
        "question": "What are the measurable success criteria?",
        "description": "Functional parity, non-functional requirements, validation approach",
        "required": True,
        "min_length": 50,
    },
    8: {
        "question": "What is the timeline and what are the constraints?",
        "description": "Total timeline, hard deadlines, team constraints, budget, dependencies",
        "required": True,
        "min_length": 30,
    },
}


class MarQedBrownPaperWorkflow:
    """
    MarQed Brown-Paper Workflow for migration projects.

    This is distinct from the code-analysis Brown Paper:
    - Code-analysis: Bottom-up (analyze existing code → extract domains → generate epics)
    - MarQed workflow: Top-down (8 questions → migration spec → task hierarchy)

    Workflow Stages:
    1. QUESTIONS: User answers 8 strategic questions
    2. ANALYZE: Miguel analyzes migration complexity and risks (Q1-Q4)
    3. GENERATE: Peter generates Migration Specification (all questions)
    4. TASKS: Felix generates Epic/Feature/Story hierarchy
    5. REVIEW: Quinn reviews quality, user approves/rejects

    Week 145: Database persistence via MarQedSession model.
    Sessions are persisted to PostgreSQL with full answer history and event audit trail.
    """

    def __init__(self):
        # In-memory cache for quick access (synced with database)
        self._sessions: Dict[str, MarQedBrownPaperSession] = {}
        # Vector DB service (lazy initialization)
        self._chroma_service: Optional[ChromaService] = None

    # ========================================================================
    # VECTOR DB INTEGRATION (Week 143)
    # ========================================================================

    def _get_chroma_service(self) -> Optional[ChromaService]:
        """Get or create ChromaDB service instance (lazy init)."""
        if self._chroma_service is None:
            try:
                self._chroma_service = ChromaService()
                logger.info("ChromaDB service initialized for MarQedBrownPaperWorkflow")
            except Exception as e:
                logger.warning(f"ChromaDB not available: {e}. Vector context will be skipped.")
                return None
        return self._chroma_service

    def _fetch_vector_context(
        self,
        project_name: str,
        project_path: Optional[str] = None,
        project_id: int = 1000  # Default project for Vector DB
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch relevant context from Vector DB for session pre-population.

        Returns architecture context, relevant docs, and code locations.
        """
        chroma = self._get_chroma_service()
        if not chroma:
            return None

        try:
            # Build query from project info
            query = f"{project_name} migration analysis architecture"
            if project_path:
                # Extract path components for better matching
                path_parts = project_path.replace("\\", "/").split("/")
                query += " " + " ".join(path_parts[-3:])  # Last 3 path components

            # Query project documents
            results = chroma.query_project_knowledge(
                query=query,
                project_id=project_id,
                top_k=10
            )

            # Format relevant docs
            relevant_docs = []
            architecture_context = []
            code_locations = []

            for doc, metadata, distance in zip(
                results.get("results", []),
                results.get("metadatas", []),
                results.get("distances", [])
            ):
                doc_type = metadata.get("document_type", "unknown")
                relevance = round(1 - distance, 4) if distance else 0

                doc_info = {
                    "content_snippet": doc[:500] if doc else "",
                    "source": metadata.get("relative_path", "unknown"),
                    "type": doc_type,
                    "relevance": relevance
                }
                relevant_docs.append(doc_info)

                # Collect architecture docs
                if doc_type == "architecture" and relevance > 0.5:
                    architecture_context.append(doc)

                # Extract code locations from content
                if doc and ("CRSLibrary" in doc or "WEB/" in doc or ".vb" in doc):
                    import re
                    paths = re.findall(r'[`"]?([A-Za-z_/\\]+\.(vb|aspx|ascx|asp))[`"]?', doc)
                    for path_match in paths[:3]:  # Limit to 3 per doc
                        code_locations.append({
                            "path": path_match[0],
                            "source": metadata.get("relative_path", "unknown")
                        })

            # Deduplicate code locations
            seen_paths = set()
            unique_locations = []
            for loc in code_locations:
                if loc["path"] not in seen_paths:
                    seen_paths.add(loc["path"])
                    unique_locations.append(loc)

            context = {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "project_id": project_id,
                "query": query,
                "relevant_docs": relevant_docs[:10],  # Top 10
                "architecture_summary": "\n\n".join(architecture_context[:2]) if architecture_context else None,
                "code_locations": unique_locations[:20],  # Top 20 unique
                "total_docs_found": len(relevant_docs)
            }

            logger.info(f"Fetched vector context for {project_name}: {len(relevant_docs)} docs, {len(unique_locations)} code locations")
            return context

        except Exception as e:
            logger.warning(f"Failed to fetch vector context: {e}")
            return None

    # ========================================================================
    # DATABASE PERSISTENCE (Week 145)
    # ========================================================================

    def _to_naive_utc(self, dt: Optional[datetime]) -> Optional[datetime]:
        """Convert timezone-aware datetime to timezone-naive UTC for database storage."""
        if dt is None:
            return None
        if dt.tzinfo is not None:
            # Convert to UTC then remove timezone info
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    async def _persist_session_to_db(
        self,
        session: MarQedBrownPaperSession,
        customer_id: Optional[int] = None
    ) -> None:
        """Persist session to database."""
        async with AsyncSessionLocal() as db:
            # Convert answers dict to JSON-serializable format
            answers_json = {}
            for q_num, answer in session.answers.items():
                answers_json[str(q_num)] = {
                    "question_number": answer.question_number,
                    "question_text": answer.question_text,
                    "answer": answer.answer,
                    "answered_at": answer.answered_at.isoformat(),
                }

            # Convert migration_analysis to dict if present
            migration_json = None
            if session.migration_analysis:
                migration_json = {
                    "complexity": session.migration_analysis.complexity,
                    "complexity_justification": session.migration_analysis.complexity_justification,
                    "risk_register": session.migration_analysis.risk_register,
                    "recommended_phases": session.migration_analysis.recommended_phases,
                    "technical_spikes": session.migration_analysis.technical_spikes,
                    "go_no_go_checkpoints": session.migration_analysis.go_no_go_checkpoints,
                    "analyzed_at": session.migration_analysis.analyzed_at.isoformat(),
                    "success": session.migration_analysis.success,
                }

            # Check if session exists
            result = await db.execute(
                select(MarQedSessionDB).where(MarQedSessionDB.id == session.id)
            )
            db_session = result.scalar_one_or_none()

            if db_session:
                # Update existing session
                db_session.status = session.status
                db_session.current_question = session.current_question
                db_session.answers = answers_json
                db_session.migration_analysis = migration_json
                db_session.specification = session.specification
                db_session.tasks = session.tasks
                db_session.enhanced_analysis = session.enhanced_analysis
                db_session.error_message = session.error_message
                db_session.updated_at = self._to_naive_utc(datetime.now(timezone.utc))
            else:
                # Create new session
                db_session = MarQedSessionDB(
                    id=session.id,
                    project_name=session.project_name,
                    project_path=session.project_path,
                    customer_id=customer_id,
                    status=session.status,
                    current_question=session.current_question,
                    workflow_type=MarQedWorkflowType.BROWN_PAPER,
                    answers=answers_json,
                    migration_analysis=migration_json,
                    specification=session.specification,
                    tasks=session.tasks,
                    enhanced_analysis=session.enhanced_analysis,
                    error_message=session.error_message,
                    created_at=self._to_naive_utc(session.created_at),
                    updated_at=self._to_naive_utc(session.updated_at),
                )
                db.add(db_session)

            await db.commit()
            logger.debug(f"Session {session.id} persisted to database")

    async def _load_session_from_db(self, session_id: str) -> Optional[MarQedBrownPaperSession]:
        """Load session from database."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(MarQedSessionDB).where(MarQedSessionDB.id == session_id)
            )
            db_session = result.scalar_one_or_none()

            if not db_session:
                return None

            # Convert JSONB answers back to MarQedAnswer dataclasses
            answers = {}
            if db_session.answers:
                for q_num_str, answer_data in db_session.answers.items():
                    q_num = int(q_num_str)
                    answers[q_num] = MarQedAnswer(
                        question_number=answer_data["question_number"],
                        question_text=answer_data["question_text"],
                        answer=answer_data["answer"],
                        answered_at=datetime.fromisoformat(answer_data["answered_at"]),
                    )

            # Convert migration_analysis JSON back to dataclass
            migration_analysis = None
            if db_session.migration_analysis:
                ma = db_session.migration_analysis
                migration_analysis = MigrationAnalysisResult(
                    complexity=ma["complexity"],
                    complexity_justification=ma["complexity_justification"],
                    risk_register=ma.get("risk_register", []),
                    recommended_phases=ma.get("recommended_phases", []),
                    technical_spikes=ma.get("technical_spikes", []),
                    go_no_go_checkpoints=ma.get("go_no_go_checkpoints", []),
                    analyzed_at=datetime.fromisoformat(ma["analyzed_at"]),
                    success=ma.get("success", True),
                )

            session = MarQedBrownPaperSession(
                id=db_session.id,
                project_name=db_session.project_name,
                project_path=db_session.project_path,
                status=db_session.status,
                current_question=db_session.current_question,
                answers=answers,
                migration_analysis=migration_analysis,
                specification=db_session.specification,
                tasks=db_session.tasks,
                created_at=db_session.created_at,
                updated_at=db_session.updated_at,
                error_message=db_session.error_message,
                enhanced_analysis=db_session.enhanced_analysis,
            )

            return session

    async def _log_event(
        self,
        session_id: str,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> None:
        """Log an event for audit trail."""
        async with AsyncSessionLocal() as db:
            event = MarQedSessionEventDB(
                session_id=session_id,
                event_type=event_type,
                event_data=event_data,
                created_by=created_by,
            )
            db.add(event)
            await db.commit()

    async def _save_answer_version(
        self,
        session_id: str,
        question_number: int,
        answer_text: str,
        version: int = 1
    ) -> None:
        """Save an answer version to database for audit trail."""
        async with AsyncSessionLocal() as db:
            # Get question text from MARQED_QUESTIONS
            q_info = MARQED_QUESTIONS.get(question_number, {})
            question_text = q_info.get("question", f"Question {question_number}")

            # Mark previous versions as not current
            if version > 1:
                await db.execute(
                    update(MarQedAnswerDB)
                    .where(MarQedAnswerDB.session_id == session_id)
                    .where(MarQedAnswerDB.question_number == question_number)
                    .values(is_current=False)
                )

            answer_record = MarQedAnswerDB(
                session_id=session_id,
                question_number=question_number,
                question_text=question_text,
                answer=answer_text,
                version=version,
                is_current=True,
            )
            db.add(answer_record)
            await db.commit()
            logger.debug(f"Saved answer v{version} for session {session_id} Q{question_number}")

    async def get_answer_history(
        self,
        session_id: str,
        question_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get answer history for a session, optionally filtered by question."""
        async with AsyncSessionLocal() as db:
            query = select(MarQedAnswerDB).where(MarQedAnswerDB.session_id == session_id)
            if question_number:
                query = query.where(MarQedAnswerDB.question_number == question_number)
            query = query.order_by(MarQedAnswerDB.question_number, MarQedAnswerDB.version.desc())

            result = await db.execute(query)
            answers = result.scalars().all()

            return [
                {
                    "id": a.id,
                    "session_id": a.session_id,
                    "question_number": a.question_number,
                    "question_text": a.question_text,
                    "answer": a.answer,
                    "version": a.version,
                    "is_current": a.is_current,
                    "answered_at": a.answered_at.isoformat() if a.answered_at else None,
                }
                for a in answers
            ]

    async def resume_session(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Optional[MarQedBrownPaperSession]:
        """
        Resume an existing MarQed session from database.

        Primary async method for session resumption.

        This method:
        1. Loads session from database
        2. Validates session is resumable
        3. Logs resume event
        4. Returns session ready for continuation
        """
        # Load from database
        session = await self._load_session_from_db(session_id)
        if not session:
            logger.warning(f"Cannot resume session {session_id}: not found")
            return None

        # Check if session is in a resumable state
        non_resumable = ["completed", "cancelled", "error"]
        if session.status in non_resumable:
            logger.warning(f"Cannot resume session {session_id}: status is {session.status}")
            return None

        # Add to cache
        self._sessions[session_id] = session

        # Log resume event
        await self._log_event(
            session_id,
            MarQedEventType.SESSION_RESUMED,
            {
                "resumed_at": datetime.now(timezone.utc).isoformat(),
                "resumed_by": user_id,
                "current_question": session.current_question,
                "status": session.status,
            },
            created_by=user_id
        )

        logger.info(f"Resumed MarQed session {session_id} at Q{session.current_question}")
        return session

    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a MarQed session."""
        session = await self.get_session(session_id)
        if not session:
            return None

        # Count answered questions
        answered_count = len(session.answers)

        return {
            "session_id": session.id,
            "project_name": session.project_name,
            "project_path": session.project_path,
            "status": session.status,
            "current_question": session.current_question,
            "answered_questions": answered_count,
            "total_questions": 8,
            "progress_percent": (answered_count / 8) * 100,
            "has_migration_analysis": session.migration_analysis is not None,
            "has_specification": session.specification is not None,
            "has_tasks": session.tasks is not None,
            "has_enhanced_analysis": session.enhanced_analysis is not None,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "error_message": session.error_message,
        }

    async def cancel_session(
        self,
        session_id: str,
        reason: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """Cancel a MarQed session.

        Primary async method for session cancellation.
        """
        session = await self.get_session(session_id)
        if not session:
            return False

        session.status = "cancelled"
        session.error_message = reason
        session.updated_at = datetime.now(timezone.utc)

        await self._persist_session_to_db(session)
        await self._log_event(
            session_id,
            MarQedEventType.SESSION_CANCELLED,
            {"reason": reason},
            created_by=user_id
        )

        logger.info(f"Cancelled MarQed session {session_id}: {reason}")
        return True

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    @deprecated_sync_wrapper("start_session", "26.0")
    def start_session_sync(
        self,
        project_name: str,
        project_path: Optional[str] = None,
        fetch_vector_context: bool = True,
        project_id: int = 1000  # Default project for Vector DB
    ) -> MarQedBrownPaperSession:
        """
        Start a new MarQed Brown-Paper session (sync, cache only).

        DEPRECATED: Use start_session() (async) instead. This sync method will be
        removed in v26.0. Does NOT persist to database.

        Args:
            project_name: Name of the project
            project_path: Optional path to project source code
            fetch_vector_context: Whether to pre-populate with Vector DB context (default: True)
            project_id: Project ID for Vector DB queries

        Returns:
            MarQedBrownPaperSession: New session with optional vector context (cache only)
        """
        session_id = str(uuid.uuid4())

        # Optionally fetch vector context for pre-population
        vector_context = None
        if fetch_vector_context:
            vector_context = self._fetch_vector_context(
                project_name=project_name,
                project_path=project_path,
                project_id=project_id
            )

        session = MarQedBrownPaperSession(
            id=session_id,
            project_name=project_name,
            project_path=project_path,
            status="questions",
            current_question=1,
            answers={},
            migration_analysis=None,
            specification=None,
            tasks=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            vector_context=vector_context,
        )

        self._sessions[session_id] = session

        context_info = f", {vector_context['total_docs_found']} docs from Vector DB" if vector_context else ""
        logger.info(f"Started MarQed Brown-Paper session {session_id} for {project_name}{context_info}")

        return session

    async def start_session(
        self,
        project_name: str,
        project_path: Optional[str] = None,
        customer_id: Optional[int] = None,
        fetch_vector_context: bool = True,
        project_id: int = 1000
    ) -> MarQedBrownPaperSession:
        """
        Start a new MarQed Brown-Paper session with database persistence.

        Primary async method - creates session and persists to database.
        This is the recommended method for all new code.

        Args:
            project_name: Name of the project
            project_path: Optional path to project source code
            customer_id: Optional customer ID for tier-based features
            fetch_vector_context: Whether to pre-populate with Vector DB context
            project_id: Project ID for Vector DB queries

        Returns:
            MarQedBrownPaperSession: New persisted session with optional vector context
        """
        session_id = str(uuid.uuid4())

        # Optionally fetch vector context for pre-population
        vector_context = None
        if fetch_vector_context:
            vector_context = self._fetch_vector_context(
                project_name=project_name,
                project_path=project_path,
                project_id=project_id
            )

        session = MarQedBrownPaperSession(
            id=session_id,
            project_name=project_name,
            project_path=project_path,
            status="questions",
            current_question=1,
            answers={},
            migration_analysis=None,
            specification=None,
            tasks=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            vector_context=vector_context,
        )

        self._sessions[session_id] = session

        context_info = f", {vector_context['total_docs_found']} docs from Vector DB" if vector_context else ""
        logger.info(f"Started MarQed Brown-Paper session {session_id} for {project_name}{context_info}")

        # Persist to database
        await self._persist_session_to_db(session, customer_id)

        # Log session start event with vector context info
        event_data = {
            "project_name": project_name,
            "project_path": project_path,
            "has_vector_context": session.vector_context is not None
        }
        if session.vector_context:
            event_data["vector_docs_count"] = session.vector_context.get("total_docs_found", 0)

        await self._log_event(
            session.id,
            MarQedEventType.SESSION_STARTED,
            event_data,
        )

        return session

    @deprecated_sync_wrapper("get_session", "26.0")
    def get_session_sync(self, session_id: str) -> Optional[MarQedBrownPaperSession]:
        """Get a MarQed session by ID (sync, cache only).

        DEPRECATED: Use get_session() (async) instead. This sync method will be
        removed in v26.0. Only accesses in-memory cache, does not load from DB.
        """
        return self._sessions.get(session_id)

    async def get_session(self, session_id: str) -> Optional[MarQedBrownPaperSession]:
        """Get a MarQed session by ID (async, with database fallback).

        Primary async method - loads from cache first, falls back to database.
        This is the recommended method for all new code.
        """
        # Check cache first
        if session_id in self._sessions:
            return self._sessions[session_id]

        # Load from database
        session = await self._load_session_from_db(session_id)
        if session:
            # Add to cache
            self._sessions[session_id] = session

        return session

    @deprecated_sync_wrapper("list_sessions", "26.0")
    def list_sessions_sync(self) -> List[MarQedBrownPaperSession]:
        """List all MarQed Brown-Paper sessions (sync, cache only).

        DEPRECATED: Use list_sessions() (async) instead. This sync method will be
        removed in v26.0. Only accesses in-memory cache, does not load from DB.
        """
        return sorted(
            self._sessions.values(),
            key=lambda s: s.created_at,
            reverse=True
        )

    async def list_sessions(self) -> List[MarQedBrownPaperSession]:
        """List all MarQed Brown-Paper sessions from database.

        Primary async method - loads from database with cache integration.
        This is the recommended method for all new code.
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(MarQedSessionDB)
                .where(MarQedSessionDB.workflow_type == MarQedWorkflowType.BROWN_PAPER)
                .order_by(MarQedSessionDB.created_at.desc())
            )
            db_sessions = result.scalars().all()

            sessions = []
            for db_session in db_sessions:
                session = await self._load_session_from_db(db_session.id)
                if session:
                    sessions.append(session)
                    # Update cache
                    self._sessions[session.id] = session

            return sessions

    @deprecated_sync_wrapper("get_current_question", "26.0")
    def get_current_question_sync(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the current question for a session (sync, cache only).

        DEPRECATED: Use get_current_question() (async) instead. This sync method
        will be removed in v26.0. Only accesses in-memory cache.
        """
        session = self._sessions.get(session_id)  # Direct cache access
        if not session or session.status != "questions":
            return None

        q_num = session.current_question
        if q_num > 8:
            return None

        q_info = MARQED_QUESTIONS[q_num]
        return {
            "question_number": q_num,
            "question": q_info["question"],
            "description": q_info["description"],
            "required": q_info["required"],
            "min_length": q_info["min_length"],
            "total_questions": 8,
            "progress_percent": ((q_num - 1) / 8) * 100,
        }

    @deprecated_sync_wrapper("get_current_question_with_context", "26.0")
    def get_current_question_with_context_sync(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current question with relevant Vector DB context (sync, cache only).

        DEPRECATED: Use get_current_question_with_context() (async) instead.
        This sync method will be removed in v26.0. Only accesses in-memory cache.
        """
        # Get question using internal sync logic (avoid double deprecation warning)
        session = self._sessions.get(session_id)
        if not session or session.status != "questions":
            return None

        q_num = session.current_question
        if q_num > 8:
            return None

        q_info = MARQED_QUESTIONS[q_num]
        question = {
            "question_number": q_num,
            "question": q_info["question"],
            "description": q_info["description"],
            "required": q_info["required"],
            "min_length": q_info["min_length"],
            "total_questions": 8,
            "progress_percent": ((q_num - 1) / 8) * 100,
        }

        # Add vector context if available
        if session.vector_context:
            question["vector_context"] = {
                "architecture_summary": session.vector_context.get("architecture_summary"),
                "relevant_docs": session.vector_context.get("relevant_docs", [])[:5],  # Top 5
                "code_locations": session.vector_context.get("code_locations", [])[:10],  # Top 10
                "context_available": True
            }
        else:
            question["vector_context"] = {"context_available": False}

        return question

    async def get_current_question(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the current question for a session (async, with database fallback).

        Primary async method - loads from cache first, falls back to database.
        This is the recommended method for all new code.
        """
        session = await self.get_session(session_id)
        if not session or session.status != "questions":
            return None

        q_num = session.current_question
        if q_num > 8:
            return None

        q_info = MARQED_QUESTIONS[q_num]
        return {
            "question_number": q_num,
            "question": q_info["question"],
            "description": q_info["description"],
            "required": q_info["required"],
            "min_length": q_info["min_length"],
            "total_questions": 8,
            "progress_percent": ((q_num - 1) / 8) * 100,
        }

    async def get_current_question_with_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current question with relevant Vector DB context (async).

        Primary async method - loads from database with cache integration.
        This is the recommended method for all new code.
        """
        question = await self.get_current_question(session_id)
        if not question:
            return None

        session = await self.get_session(session_id)
        if not session:
            return question

        # Add vector context if available
        if session.vector_context:
            question["vector_context"] = {
                "architecture_summary": session.vector_context.get("architecture_summary"),
                "relevant_docs": session.vector_context.get("relevant_docs", [])[:5],
                "code_locations": session.vector_context.get("code_locations", [])[:10],
                "context_available": True
            }
        else:
            question["vector_context"] = {"context_available": False}

        return question

    def get_session_vector_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the full Vector DB context for a session.

        Week 143: Returns all fetched context including docs, architecture, and code locations.
        Note: This is a sync method that uses direct cache access.
        """
        session = self._sessions.get(session_id)  # Direct cache access
        if not session:
            return None

        return session.vector_context

    @deprecated_sync_wrapper("submit_answer", "26.0")
    def submit_answer_sync(
        self,
        session_id: str,
        answer: str
    ) -> Dict[str, Any]:
        """Submit answer to current question (sync, cache only).

        DEPRECATED: Use submit_answer() (async) instead. This sync method will be
        removed in v26.0. Does NOT persist to database.
        """
        session = self._sessions.get(session_id)  # Direct cache access
        if not session:
            return {"error": "Session not found"}

        if session.status != "questions":
            return {"error": f"Session not in questions phase: {session.status}"}

        q_num = session.current_question
        if q_num > 8:
            return {"error": "All questions already answered"}

        q_info = MARQED_QUESTIONS[q_num]

        # Validate answer
        if q_info["required"] and len(answer.strip()) < q_info["min_length"]:
            return {
                "error": f"Answer too short. Minimum {q_info['min_length']} characters required.",
                "current_length": len(answer.strip()),
            }

        # Store answer
        session.answers[q_num] = MarQedAnswer(
            question_number=q_num,
            question_text=q_info["question"],
            answer=answer.strip(),
            answered_at=datetime.now(timezone.utc),
        )

        session.updated_at = datetime.now(timezone.utc)

        # Move to next question or complete
        if q_num < 8:
            session.current_question = q_num + 1
            # Get next question using direct cache access
            next_session = self._sessions.get(session_id)
            next_q = None
            if next_session and next_session.status == "questions":
                q_num_next = next_session.current_question
                if q_num_next <= 8:
                    q_info_next = MARQED_QUESTIONS[q_num_next]
                    next_q = {
                        "question_number": q_num_next,
                        "question": q_info_next["question"],
                        "description": q_info_next["description"],
                        "required": q_info_next["required"],
                        "min_length": q_info_next["min_length"],
                        "total_questions": 8,
                        "progress_percent": ((q_num_next - 1) / 8) * 100,
                    }
            return {
                "success": True,
                "answered_question": q_num,
                "next_question": next_q,
            }
        else:
            session.status = "analyzing"
            return {
                "success": True,
                "answered_question": q_num,
                "questions_complete": True,
                "next_step": "Run migration analysis (Miguel)",
            }

    async def submit_answer(
        self,
        session_id: str,
        answer: str
    ) -> Dict[str, Any]:
        """Submit answer to current question with database persistence.

        Primary async method - persists to database with full audit trail.
        This is the recommended method for all new code.
        """
        # First try to get from cache, then from database
        session = await self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        if session.status != "questions":
            return {"error": f"Session not in questions phase: {session.status}"}

        q_num = session.current_question
        if q_num > 8:
            return {"error": "All questions already answered"}

        q_info = MARQED_QUESTIONS[q_num]

        # Validate answer
        if q_info["required"] and len(answer.strip()) < q_info["min_length"]:
            return {
                "error": f"Answer too short. Minimum {q_info['min_length']} characters required.",
                "current_length": len(answer.strip()),
            }

        # Store answer
        session.answers[q_num] = MarQedAnswer(
            question_number=q_num,
            question_text=q_info["question"],
            answer=answer.strip(),
            answered_at=datetime.now(timezone.utc),
        )

        session.updated_at = datetime.now(timezone.utc)

        # Move to next question or complete
        if q_num < 8:
            session.current_question = q_num + 1
            result = {
                "success": True,
                "answered_question": q_num,
                "next_question": await self.get_current_question(session_id),
            }
        else:
            session.status = "analyzing"
            result = {
                "success": True,
                "answered_question": q_num,
                "questions_complete": True,
                "next_step": "Run migration analysis (Miguel)",
            }

        # Persist to database
        await self._persist_session_to_db(session)

        # Save answer version for audit trail
        # Get current version count for this question
        existing_answers = await self.get_answer_history(session_id, q_num)
        version = len(existing_answers) + 1
        await self._save_answer_version(session_id, q_num, answer.strip(), version)

        # Log event
        await self._log_event(
            session_id,
            MarQedEventType.ANSWER_SUBMITTED,
            {"question_number": q_num, "answer_length": len(answer.strip()), "version": version},
        )

        return result

    # ========================================================================
    # STAGE 1: MIGUEL'S MIGRATION ANALYSIS
    # ========================================================================

    async def run_migration_analysis(
        self,
        session_id: str,
        llm_provider: Optional[Any] = None
    ) -> MigrationAnalysisResult:
        """
        Run Miguel's migration analysis on Q1-Q4 answers.

        This analyzes:
        - Legacy system complexity
        - Migration risk register
        - Recommended phasing
        - Technical spikes needed
        - Go/No-Go checkpoints
        """
        # Use async session retrieval with database fallback
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if session.status not in ["analyzing", "questions"]:
            raise ValueError(f"Session not ready for analysis: {session.status}")

        # Ensure Q1-Q4 are answered
        for q in [1, 2, 3, 4]:
            if q not in session.answers:
                raise ValueError(f"Question {q} not answered yet")

        session.status = "analyzing"

        # Log analysis start
        await self._log_event(
            session_id,
            MarQedEventType.ANALYSIS_STARTED,
            {"phase": "migration_analysis"},
        )

        # Build analysis prompt for Miguel
        q1 = session.answers[1].answer
        q2 = session.answers[2].answer
        q3 = session.answers[3].answer
        q4 = session.answers[4].answer

        # For now, generate analysis without LLM (can be enhanced later)
        analysis = self._generate_migration_analysis(q1, q2, q3, q4)

        session.migration_analysis = analysis
        session.status = "generating"
        session.updated_at = datetime.now(timezone.utc)

        # Persist to database
        await self._persist_session_to_db(session)

        # Log analysis complete
        await self._log_event(
            session_id,
            MarQedEventType.ANALYSIS_COMPLETED,
            {"complexity": analysis.complexity, "risk_count": len(analysis.risk_register)},
        )

        logger.info(f"Migration analysis complete for session {session_id}: {analysis.complexity}")

        return analysis

    def _generate_migration_analysis(
        self,
        legacy_system: str,
        target_state: str,
        strategy: str,
        data_migration: str
    ) -> MigrationAnalysisResult:
        """Generate migration analysis from Q1-Q4 answers."""
        # Determine complexity based on keywords
        complexity_score = 0

        # Legacy complexity indicators
        if any(kw in legacy_system.lower() for kw in ["150,000", "200,000", "million", "large"]):
            complexity_score += 3
        if any(kw in legacy_system.lower() for kw in ["2,000", "1,000", "hundred"]):
            complexity_score += 2
        if any(kw in legacy_system.lower() for kw in ["2008", "2010", "2005", "legacy", "old"]):
            complexity_score += 2
        if any(kw in legacy_system.lower() for kw in ["no test", "no document", "technical debt"]):
            complexity_score += 2

        # Target complexity
        if any(kw in target_state.lower() for kw in ["microservices", "distributed", "kubernetes"]):
            complexity_score += 2
        if any(kw in target_state.lower() for kw in ["clean architecture", "cqrs", "ddd"]):
            complexity_score += 1

        # Strategy complexity
        if "strangler" in strategy.lower():
            complexity_score += 1  # Safer but complex
        if "big bang" in strategy.lower():
            complexity_score += 3  # Risky

        # Data migration complexity
        if any(kw in data_migration.lower() for kw in ["transform", "etl", "convert", "redesign"]):
            complexity_score += 2

        # Determine complexity level
        if complexity_score <= 3:
            complexity = "LOW"
            justification = "Straightforward migration with limited scope"
        elif complexity_score <= 6:
            complexity = "MEDIUM"
            justification = "Moderate complexity requiring careful planning"
        elif complexity_score <= 9:
            complexity = "HIGH"
            justification = "Complex migration with significant technology gap and data challenges"
        else:
            complexity = "VERY_HIGH"
            justification = "Very complex migration requiring extensive planning and risk mitigation"

        # Generate risk register
        risks = []

        if "no test" in legacy_system.lower() or "test" not in legacy_system.lower():
            risks.append({
                "risk": "Legacy system has limited or no test coverage",
                "likelihood": "HIGH",
                "impact": "HIGH",
                "mitigation": "Create comprehensive test suite for legacy before migration"
            })

        if "big bang" in strategy.lower():
            risks.append({
                "risk": "Big bang migration has high failure risk",
                "likelihood": "MEDIUM",
                "impact": "CRITICAL",
                "mitigation": "Extensive dry-runs, long maintenance window, instant rollback capability"
            })

        if "transform" in data_migration.lower() or "etl" in data_migration.lower():
            risks.append({
                "risk": "Data transformation may introduce errors",
                "likelihood": "MEDIUM",
                "impact": "HIGH",
                "mitigation": "Automated validation scripts, row-by-row verification, audit trails"
            })

        risks.append({
            "risk": "User adoption resistance due to UI changes",
            "likelihood": "MEDIUM",
            "impact": "MEDIUM",
            "mitigation": "Early user involvement, training program, phased rollout"
        })

        risks.append({
            "risk": "Hidden complexity in legacy code",
            "likelihood": "HIGH",
            "impact": "MEDIUM",
            "mitigation": "Code analysis tools, expert code review, buffer in timeline"
        })

        # Recommended phases
        phases = [
            {
                "phase": 1,
                "name": "Foundation",
                "description": "Project setup, architecture foundation, security/auth",
                "weeks": 8,
                "modules": ["Setup", "Architecture", "Identity", "MFA"]
            },
            {
                "phase": 2,
                "name": "Core Modules",
                "description": "Primary business functionality migration",
                "weeks": 20,
                "modules": ["User Management", "Core Business Logic"]
            },
            {
                "phase": 3,
                "name": "Extended Features",
                "description": "Secondary features and integrations",
                "weeks": 16,
                "modules": ["Reporting", "Integrations", "Workflows"]
            },
            {
                "phase": 4,
                "name": "Cutover",
                "description": "Data migration, validation, go-live",
                "weeks": 4,
                "modules": ["Data Migration", "Validation", "Training"]
            },
        ]

        # Technical spikes
        spikes = [
            "Database schema mapping validation (EF Core vs legacy)",
            "Authentication migration path (legacy users → new Identity)",
            "Performance benchmark: legacy vs new baseline",
            "Third-party integration compatibility testing",
        ]

        # Go/No-Go checkpoints
        checkpoints = [
            "Phase 1 Complete: Foundation working, auth functional, 100% test coverage",
            "Phase 2 Midpoint: Core module proof of concept validated",
            "Phase 3 Start: All critical modules migrated and tested",
            "Pre-Cutover: Full regression passed, performance targets met",
        ]

        return MigrationAnalysisResult(
            complexity=complexity,
            complexity_justification=justification,
            risk_register=risks,
            recommended_phases=phases,
            technical_spikes=spikes,
            go_no_go_checkpoints=checkpoints,
            analyzed_at=datetime.now(timezone.utc),
        )

    # ========================================================================
    # STAGE 2: PETER'S SPECIFICATION GENERATION
    # ========================================================================

    async def generate_specification(
        self,
        session_id: str,
        llm_provider: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Generate Migration Specification from all 8 answers + Miguel's analysis.

        This creates a comprehensive specification document.
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if session.status != "generating":
            raise ValueError(f"Session not ready for specification: {session.status}")

        if not session.migration_analysis:
            raise ValueError("Migration analysis not complete")

        # Build specification from answers
        specification = {
            "metadata": {
                "project_name": session.project_name,
                "project_path": session.project_path,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "workflow": "MARQED_BROWN_PAPER",
                "session_id": session_id,
            },
            "executive_summary": self._generate_executive_summary(session),
            "current_state": self._generate_current_state(session),
            "target_state": self._generate_target_state(session),
            "migration_approach": self._generate_migration_approach(session),
            "stakeholders": self._generate_stakeholders(session),
            "success_criteria": self._generate_success_criteria_spec(session),
            "timeline": self._generate_timeline(session),
            "risks": session.migration_analysis.risk_register,
            "technical_spikes": session.migration_analysis.technical_spikes,
            "go_no_go_checkpoints": session.migration_analysis.go_no_go_checkpoints,
        }

        session.specification = specification
        session.updated_at = datetime.now(timezone.utc)

        # Persist to database
        await self._persist_session_to_db(session)
        await self._log_event(
            session_id,
            MarQedEventType.SPECIFICATION_GENERATED,
            {"sections": list(specification.keys())},
        )

        logger.info(f"Specification generated for session {session_id}")

        # Return in expected format with success wrapper
        return {
            "success": True,
            "specification": {
                "project_name": session.project_name,
                "mission": specification["executive_summary"],
                "vision": specification["target_state"]["description"],
                "scope": {
                    "in_scope": [specification["current_state"]["description"]],
                    "out_of_scope": [],
                },
                "requirements": {
                    "functional": [specification["migration_approach"]["strategy_description"]],
                    "non_functional": specification.get("technical_spikes", []),
                },
                "constraints": specification.get("go_no_go_checkpoints", []),
                "success_criteria": specification["success_criteria"] if isinstance(specification["success_criteria"], list) else [specification["success_criteria"]],
            }
        }

    def _generate_executive_summary(self, session: MarQedBrownPaperSession) -> str:
        """Generate executive summary."""
        q5 = session.answers.get(5)
        q8 = session.answers.get(8)

        problem = q5.answer[:200] if q5 else "Migration required"
        timeline = q8.answer[:100] if q8 else "Timeline to be determined"

        return f"""Migration of {session.project_name} from legacy system to modern architecture.

Problem Statement: {problem}

Complexity Assessment: {session.migration_analysis.complexity}
{session.migration_analysis.complexity_justification}

Timeline: {timeline}
"""

    def _generate_current_state(self, session: MarQedBrownPaperSession) -> Dict[str, Any]:
        """Generate current state section."""
        q1 = session.answers.get(1)
        return {
            "description": q1.answer if q1 else "",
            "pain_points": session.answers.get(5).answer if session.answers.get(5) else "",
        }

    def _generate_target_state(self, session: MarQedBrownPaperSession) -> Dict[str, Any]:
        """Generate target state section."""
        q2 = session.answers.get(2)
        return {
            "description": q2.answer if q2 else "",
        }

    def _generate_migration_approach(self, session: MarQedBrownPaperSession) -> Dict[str, Any]:
        """Generate migration approach section."""
        q3 = session.answers.get(3)
        q4 = session.answers.get(4)

        # Detect strategy type
        strategy_text = q3.answer.lower() if q3 else ""
        if "strangler" in strategy_text:
            strategy_type = "strangler_fig"
        elif "big bang" in strategy_text:
            strategy_type = "big_bang"
        elif "parallel" in strategy_text:
            strategy_type = "parallel_run"
        else:
            strategy_type = "strangler_fig"  # Default

        return {
            "strategy_type": strategy_type,
            "strategy_description": q3.answer if q3 else "",
            "data_migration": q4.answer if q4 else "",
            "phases": session.migration_analysis.recommended_phases,
        }

    def _generate_stakeholders(self, session: MarQedBrownPaperSession) -> str:
        """Generate stakeholders section."""
        q6 = session.answers.get(6)
        return q6.answer if q6 else ""

    def _generate_success_criteria_spec(self, session: MarQedBrownPaperSession) -> str:
        """Generate success criteria section."""
        q7 = session.answers.get(7)
        return q7.answer if q7 else ""

    def _generate_timeline(self, session: MarQedBrownPaperSession) -> Dict[str, Any]:
        """Generate timeline section."""
        q8 = session.answers.get(8)
        phases = session.migration_analysis.recommended_phases

        total_weeks = sum(p["weeks"] for p in phases)

        return {
            "description": q8.answer if q8 else "",
            "total_weeks": total_weeks,
            "phases": phases,
            "checkpoints": session.migration_analysis.go_no_go_checkpoints,
        }

    # ========================================================================
    # STAGE 3: FELIX'S TASK GENERATION
    # ========================================================================

    async def generate_tasks(
        self,
        session_id: str,
        llm_provider: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Generate Epic/Feature/Story hierarchy from specification.

        Week 159: Now uses BusinessDomainExtractor and BusinessDrivenStoryGenerator
        for business-driven epic/feature/story generation based on actual code analysis.
        Falls back to phase-based generation if business extraction fails.

        Includes IFPUG Function Point estimation if project_path is available.
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if not session.specification:
            raise ValueError("Specification not generated yet")

        phases = session.migration_analysis.recommended_phases
        epics = []
        features = []
        stories = []

        # Calculate FP estimation if project path is available
        fp_analysis = None
        total_fp = 0
        fp_confidence = 0.0
        fp_breakdown = {}
        use_business_extraction = False

        if session.project_path:
            project_path = Path(session.project_path)

            # Try FP estimation first
            try:
                estimation_service = get_brown_paper_estimation_service()
                if project_path.exists():
                    fp_result = estimation_service.analyze_directory(project_path)
                    total_fp = fp_result.total_afp
                    fp_confidence = fp_result.confidence_score
                    fp_breakdown = fp_result.to_dict()
                    logger.info(f"FP analysis complete: {total_fp} FP, confidence: {fp_confidence:.1%}")
            except Exception as e:
                logger.warning(f"FP analysis failed for {session.project_path}: {e}")

            # Week 159: Try business-driven extraction
            if project_path.exists():
                try:
                    logger.info(f"Starting business domain extraction for {session.project_path}")

                    # Step 1: Quick scan to get modules and dependencies
                    modules, dependencies = await self._quick_code_scan(str(project_path))

                    if modules:
                        logger.info(f"Quick scan found {len(modules)} modules, {len(dependencies)} dependencies")

                        # Step 2: Extract business domains using BusinessDomainExtractorService
                        domain_extractor = get_business_domain_extractor(use_healthcare_patterns=True)
                        domain_result = await domain_extractor.extract_domains(
                            modules=modules,
                            dependencies=dependencies,
                            scan_path=str(project_path),
                        )

                        if domain_result and domain_result.domains:
                            logger.info(f"Extracted {len(domain_result.domains)} business domains")

                            # Step 3: Generate stories using BusinessDrivenStoryGeneratorService
                            story_generator = get_business_driven_story_generator()
                            story_result = await story_generator.generate_stories(domain_result)

                            if story_result and story_result.epics:
                                logger.info(f"Generated {len(story_result.epics)} business-driven epics")

                                # Convert to task format
                                epics, features, stories = self._convert_business_stories_to_tasks(
                                    story_result, total_fp
                                )
                                use_business_extraction = True
                                logger.info(
                                    f"Business extraction successful: {len(epics)} epics, "
                                    f"{len(features)} features, {len(stories)} stories"
                                )
                            else:
                                logger.warning("Story generation returned no epics, falling back to phase-based")
                        else:
                            logger.warning("Domain extraction returned no domains, falling back to phase-based")
                    else:
                        logger.warning("Quick scan found no modules, falling back to phase-based")

                except Exception as e:
                    logger.warning(f"Business extraction failed, falling back to phase-based: {e}")

        # Fallback: Phase-based generation (original logic)
        if not use_business_extraction:
            logger.info("Using phase-based task generation (fallback)")
            epics, features, stories = self._generate_phase_based_tasks(phases, total_fp)

        # Calculate totals
        total_sp = sum(s.get("estimated_sp", 0) for s in stories)
        total_epic_fp = sum(e.get("estimated_fp", 0) for e in epics)

        tasks = {
            "epics": epics,
            "features": features,
            "stories": stories,
            "summary": {
                "total_epics": len(epics),
                "total_features": len(features),
                "total_stories": len(stories),
                "total_story_points": total_sp,
                "estimated_fp": total_fp if total_fp > 0 else total_epic_fp,
                "fp_confidence": round(fp_confidence * 100, 1),
                "estimated_weeks": phases[-1]["weeks"] if phases else 0,
                "extraction_method": "business_driven" if use_business_extraction else "phase_based",
            },
            "fp_analysis": fp_breakdown if fp_breakdown else None,
        }

        session.tasks = tasks
        session.status = "review"
        session.updated_at = datetime.now(timezone.utc)

        # Persist to database
        await self._persist_session_to_db(session)
        await self._log_event(
            session_id,
            MarQedEventType.TASKS_GENERATED,
            {
                "total_epics": len(epics),
                "total_features": len(features),
                "total_stories": len(stories),
                "total_fp": total_fp,
                "extraction_method": "business_driven" if use_business_extraction else "phase_based",
            },
        )

        logger.info(
            f"Tasks generated for session {session_id}: {len(epics)} epics, "
            f"{len(stories)} stories, {total_fp} FP (method: {'business' if use_business_extraction else 'phase'})"
        )

        # Week 159: Sync to brown_paper_* tables for dashboard compatibility
        try:
            await self._sync_to_brown_paper_tables(session, tasks)
            logger.info(f"Synced {len(epics)} epics to brown_paper_epics table")
        except Exception as e:
            logger.warning(f"Failed to sync to brown_paper tables: {e}")

        return {"success": True, "tasks": tasks}

    def _convert_business_stories_to_tasks(
        self,
        story_result: "StoryGenerationResult",
        total_fp: int = 0
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Convert BusinessDrivenStoryGenerator output to MarQed task format.

        Week 159: Bridges business-driven generation with MarQed workflow.
        """
        epics = []
        features = []
        stories = []

        epic_num = 1
        feat_num = 1
        story_num = 1

        # Distribute FP across epics proportionally
        total_epic_stories = sum(
            sum(len(f.stories) for f in e.features)
            for e in story_result.epics
        ) or 1

        for gen_epic in story_result.epics:
            epic_id = f"EPIC-{epic_num:03d}"

            # Calculate FP for this epic based on story count
            epic_story_count = sum(len(f.stories) for f in gen_epic.features)
            epic_fp = round(total_fp * (epic_story_count / total_epic_stories)) if total_fp > 0 else 0

            epic = {
                "id": epic_id,
                "title": gen_epic.title,
                "description": gen_epic.description,
                "domain": gen_epic.domain_name,  # Fixed: domain_name not domain
                "estimated_fp": epic_fp,
                "estimated_weeks": gen_epic.estimated_weeks,
                "complexity": gen_epic.complexity,
                "source_modules": gen_epic.source_modules[:5],  # Fixed: source_modules not source_references
            }
            epics.append(epic)

            for gen_feature in gen_epic.features:
                feat_id = f"FEAT-{feat_num:03d}"

                # Distribute epic FP across features
                feature_count = len(gen_epic.features) or 1
                feature_fp = round(epic_fp / feature_count) if epic_fp > 0 else 0
                feature_sp = round(feature_fp * 0.19) if feature_fp > 0 else gen_feature.estimated_story_points

                feature = {
                    "id": feat_id,
                    "epic_id": epic_id,
                    "title": gen_feature.title,
                    "description": gen_feature.description,
                    "source_modules": gen_feature.source_modules[:5],  # Fixed: use source_modules
                    "estimated_fp": feature_fp,
                    "estimated_sp": feature_sp,
                    "complexity": gen_feature.complexity,
                }
                features.append(feature)

                # Distribute feature SP across stories
                story_count = len(gen_feature.stories) or 1
                base_story_sp = max(1, round(feature_sp / story_count))

                for gen_story in gen_feature.stories:
                    story_id = f"STORY-{story_num:03d}"

                    # Convert acceptance criteria to strings
                    ac_list = [
                        ac.criterion if hasattr(ac, 'criterion') else str(ac)
                        for ac in (gen_story.acceptance_criteria or [])
                    ] or [
                        f"{gen_story.title} is complete",
                        "Code reviewed and approved",
                        "Tests pass with >80% coverage",
                    ]

                    story = {
                        "id": story_id,
                        "feature_id": feat_id,
                        "epic_id": epic_id,
                        "title": gen_story.title,
                        "description": gen_story.description,
                        "story_type": gen_story.story_type,
                        "estimated_sp": gen_story.story_points or base_story_sp,
                        "acceptance_criteria": ac_list[:5],
                        "complexity": gen_story.complexity,
                        "source_files": [ref.file_path for ref in gen_story.source_references[:3]],
                    }
                    stories.append(story)
                    story_num += 1

                feat_num += 1
            epic_num += 1

        return epics, features, stories

    def _generate_phase_based_tasks(
        self,
        phases: List[Dict],
        total_fp: int = 0
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Original phase-based task generation (fallback).

        Generates epics from migration phases (Foundation, Core Modules, etc.)
        """
        epics = []
        features = []
        stories = []

        epic_num = 1
        feat_num = 1
        story_num = 1

        for phase in phases:
            epic_id = f"EPIC-{epic_num:03d}"

            # Calculate FP for this epic based on weeks
            phase_fp = 0
            if total_fp > 0:
                total_weeks = sum(p["weeks"] for p in phases)
                phase_fp = round(total_fp * (phase["weeks"] / total_weeks))

            epic = {
                "id": epic_id,
                "title": f"Phase {phase['phase']}: {phase['name']}",
                "description": phase["description"],
                "estimated_weeks": phase["weeks"],
                "estimated_fp": phase_fp,
                "modules": phase["modules"],
                "priority": phase["phase"],
            }
            epics.append(epic)

            module_count = len(phase["modules"])
            for module in phase["modules"]:
                feat_id = f"FEAT-{feat_num:03d}"

                feature_fp = round(phase_fp / module_count) if module_count > 0 and phase_fp > 0 else 0
                feature_sp = round(feature_fp * 0.19) if feature_fp > 0 else 21

                feature = {
                    "id": feat_id,
                    "epic_id": epic_id,
                    "title": f"{module} Implementation",
                    "description": f"Complete implementation of {module} functionality",
                    "estimated_fp": feature_fp,
                    "estimated_sp": feature_sp,
                }
                features.append(feature)

                default_stories = [
                    f"Setup {module} infrastructure",
                    f"Implement {module} core logic",
                    f"Create {module} API endpoints",
                    f"Write unit tests for {module}",
                    f"Write integration tests for {module}",
                    f"Document {module}",
                ]

                story_sp = round(feature_sp / len(default_stories)) if feature_sp > 0 else 3

                for story_title in default_stories:
                    story_id = f"STORY-{story_num:03d}"
                    story = {
                        "id": story_id,
                        "feature_id": feat_id,
                        "epic_id": epic_id,
                        "title": story_title,
                        "estimated_sp": max(1, story_sp),
                        "acceptance_criteria": [
                            f"{story_title} is complete",
                            "Code reviewed and approved",
                            "Tests pass with >80% coverage",
                        ],
                    }
                    stories.append(story)
                    story_num += 1

                feat_num += 1
            epic_num += 1

        return epics, features, stories

    async def _quick_code_scan(
        self,
        project_path: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Quick code scan to get modules and dependencies for business extraction.

        Week 159: Lightweight alternative to full Phase 1 analysis.
        Uses DependencyGraphService for fast module/dependency discovery.

        Returns:
            Tuple of (modules list, dependencies list)
        """
        from app.services.dependency_graph_service import DependencyGraphService

        modules = []
        dependencies = []

        try:
            # Use DependencyGraphService for quick scan
            dep_service = DependencyGraphService()
            result = dep_service.analyze_directory(project_path)

            if result:
                # Extract modules from DependencyGraphResult.modules (Dict[str, ModuleNode])
                for mod_name, mod_node in result.modules.items():
                    modules.append({
                        'name': mod_name,
                        'path': mod_node.file_path,
                        'type': mod_node.language.value if mod_node.language else 'unknown',
                        'lines_of_code': mod_node.lines_of_code,
                        'imports': list(mod_node.imports)[:10],  # Limit for performance
                    })

                # Extract dependencies from edges (List[DependencyEdge])
                for edge in result.edges:
                    dependencies.append({
                        'source': edge.source,
                        'target': edge.target,
                        'type': edge.import_type,  # Fixed: import_type not dependency_type
                    })

                logger.info(f"Quick scan: {len(modules)} modules, {len(dependencies)} dependencies")

        except Exception as e:
            logger.warning(f"Quick scan via DependencyGraphService failed: {e}")

            # Fallback: Simple file scan
            try:
                from pathlib import Path
                project = Path(project_path)

                # Find code files
                code_extensions = {'.py', '.cs', '.vb', '.aspx', '.ascx', '.js', '.ts', '.java'}
                for ext in code_extensions:
                    for file_path in project.rglob(f'*{ext}'):
                        if '.git' not in str(file_path) and 'node_modules' not in str(file_path):
                            rel_path = str(file_path.relative_to(project))
                            modules.append({
                                'name': file_path.stem,
                                'path': rel_path,
                                'type': 'file',
                                'extension': ext,
                            })

                logger.info(f"Fallback scan found {len(modules)} files")

            except Exception as e2:
                logger.error(f"Fallback file scan also failed: {e2}")

        return modules, dependencies

    async def _sync_to_brown_paper_tables(
        self,
        session: "MarQedBrownPaperSession",
        tasks: Dict[str, Any]
    ) -> None:
        """
        Sync MarQed session data to brown_paper_* tables for dashboard compatibility.

        Week 159: Bridges MarQed workflow with existing brown_paper dashboard.
        Creates/updates: applications, brown_paper_sessions, brown_paper_constitutions, brown_paper_epics

        Args:
            session: MarQed session with tasks
            tasks: Generated tasks dict with epics, features, stories
        """
        import uuid

        async with AsyncSessionLocal() as db:
            try:
                # Step 1: Find or create Application (using ApplicationDB database model)
                app_result = await db.execute(
                    select(ApplicationDB).where(ApplicationDB.name == session.project_name)
                )
                application = app_result.scalar_one_or_none()

                if not application:
                    application = ApplicationDB(
                        name=session.project_name,
                        root_path=session.project_path or "",
                        description=f"Auto-created from MarQed session {session.id}",
                        application_type="legacy",
                        is_active=True,
                        # Let model defaults handle created_at/updated_at
                    )
                    db.add(application)
                    await db.flush()
                    logger.info(f"Created application: {application.name} (id={application.id})")

                # Step 2: Create BrownPaperSession (using BrownPaperSessionDB alias)
                bp_session_id = uuid.uuid4()
                bp_session = BrownPaperSessionDB(
                    id=bp_session_id,
                    application_id=application.id,
                    application_name=session.project_name,
                    root_path=session.project_path or "",
                    status="completed",
                    modules_count=tasks["summary"].get("total_features", 0),
                    domains_count=tasks["summary"].get("total_epics", 0),
                    # Store FP/SP in generation_metadata since model doesn't have dedicated columns
                    generation_metadata={
                        "total_function_points": tasks["summary"].get("estimated_fp", 0),
                        "total_story_points": tasks["summary"].get("total_story_points", 0),
                        "extraction_method": tasks["summary"].get("extraction_method", "unknown"),
                    },
                )
                db.add(bp_session)
                await db.flush()
                logger.info(f"Created brown_paper_session: {bp_session_id}")

                # Step 3: Create BrownPaperConstitution (using BrownPaperConstitutionDB alias)
                constitution_id = uuid.uuid4()

                # Serialize answers to dict format (MarQedAnswer objects are not JSON serializable)
                answers_dict = {}
                if hasattr(session, 'answers') and session.answers:
                    for k, v in session.answers.items():
                        if hasattr(v, 'to_dict'):
                            answers_dict[k] = v.to_dict()
                        elif hasattr(v, '__dict__'):
                            answers_dict[k] = {key: str(val) for key, val in v.__dict__.items() if not key.startswith('_')}
                        else:
                            answers_dict[k] = str(v)

                constitution = BrownPaperConstitutionDB(
                    id=constitution_id,
                    session_id=bp_session_id,
                    status="approved",
                    content_json={
                        "marqed_session_id": session.id,
                        "extraction_method": tasks["summary"].get("extraction_method", "unknown"),
                        "answers": answers_dict,
                        "specification": session.specification.to_dict() if hasattr(session.specification, 'to_dict') else {},
                    },
                    generated_by="MarQedBrownPaperWorkflow",
                    # Let model defaults handle created_at
                )
                db.add(constitution)
                await db.flush()
                logger.info(f"Created brown_paper_constitution: {constitution_id}")

                # Step 4: Create BrownPaperEpics (limit to top 100 for performance)
                epics_to_save = tasks.get("epics", [])[:100]
                features_by_epic = {}
                for feature in tasks.get("features", []):
                    epic_id = feature.get("epic_id")
                    if epic_id not in features_by_epic:
                        features_by_epic[epic_id] = []
                    features_by_epic[epic_id].append(feature)

                for i, epic_data in enumerate(epics_to_save):
                    epic_id = epic_data.get("id", f"EPIC-{i+1:03d}")
                    epic_features = features_by_epic.get(epic_id, [])

                    # Build features JSON with stories
                    features_json = []
                    for feat in epic_features[:20]:  # Limit features per epic
                        feat_stories = [
                            s for s in tasks.get("stories", [])
                            if s.get("feature_id") == feat.get("id")
                        ][:10]  # Limit stories per feature

                        features_json.append({
                            "id": feat.get("id"),
                            "title": feat.get("title"),
                            "description": feat.get("description", ""),
                            "estimated_sp": feat.get("estimated_sp", 0),
                            "stories": [
                                {
                                    "id": s.get("id"),
                                    "title": s.get("title"),
                                    "story_type": s.get("story_type", ""),
                                    "estimated_sp": s.get("estimated_sp", 0),
                                    "acceptance_criteria": s.get("acceptance_criteria", []),
                                }
                                for s in feat_stories
                            ]
                        })

                    # Using BrownPaperEpicDB alias
                    bp_epic = BrownPaperEpicDB(
                        id=uuid.uuid4(),
                        constitution_id=constitution_id,
                        epic_number=epic_id,
                        name=epic_data.get("title", f"Epic {i+1}"),
                        description=epic_data.get("description", ""),
                        priority=i + 1,
                        complexity=epic_data.get("complexity", "medium"),
                        source_domain=epic_data.get("domain", ""),
                        source_modules=epic_data.get("source_modules", []),
                        features=features_json,
                        status="draft",
                        function_points=epic_data.get("estimated_fp", 0),
                        story_points=sum(f.get("estimated_sp", 0) for f in epic_features),
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(bp_epic)

                await db.commit()
                logger.info(
                    f"Synced to brown_paper tables: app={application.id}, "
                    f"session={bp_session_id}, epics={len(epics_to_save)}"
                )

            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to sync to brown_paper tables: {e}", exc_info=True)
                raise

    # ========================================================================
    # APPROVAL / EXPORT
    # ========================================================================

    @deprecated_sync_wrapper("approve_session", "26.0")
    def approve_session_sync(self, session_id: str) -> bool:
        """Approve the MarQed session (sync, cache only).

        DEPRECATED: Use approve_session() (async) instead. This sync method will be
        removed in v26.0. Does NOT persist to database.
        """
        session = self._sessions.get(session_id)  # Direct cache access
        if not session or session.status != "review":
            return False

        session.status = "approved"
        session.updated_at = datetime.now(timezone.utc)
        return True

    @deprecated_sync_wrapper("reject_session", "26.0")
    def reject_session_sync(self, session_id: str, reason: str) -> bool:
        """Reject the MarQed session (sync, cache only).

        DEPRECATED: Use reject_session() (async) instead. This sync method will be
        removed in v26.0. Does NOT persist to database.
        """
        session = self._sessions.get(session_id)  # Direct cache access
        if not session:
            return False

        session.status = "rejected"
        session.error_message = reason
        session.updated_at = datetime.now(timezone.utc)
        return True

    async def approve_session(
        self,
        session_id: str,
        reviewer: Optional[str] = None
    ) -> bool:
        """Approve the MarQed session with database persistence.

        Primary async method - persists to database with audit logging.
        This is the recommended method for all new code.
        """
        session = await self.get_session(session_id)
        if not session or session.status != "review":
            return False

        session.status = "approved"
        session.updated_at = datetime.now(timezone.utc)

        # Persist to database
        await self._persist_session_to_db(session)
        await self._log_event(
            session_id,
            MarQedEventType.SESSION_APPROVED,
            {"reviewer": reviewer},
            created_by=reviewer,
        )

        logger.info(f"Session {session_id} approved by {reviewer}")
        return True

    async def reject_session(
        self,
        session_id: str,
        reason: str,
        reviewer: Optional[str] = None
    ) -> bool:
        """Reject the MarQed session with database persistence.

        Primary async method - persists to database with audit logging.
        This is the recommended method for all new code.
        """
        session = await self.get_session(session_id)
        if not session:
            return False

        session.status = "rejected"
        session.error_message = reason
        session.updated_at = datetime.now(timezone.utc)

        # Persist to database
        await self._persist_session_to_db(session)
        await self._log_event(
            session_id,
            MarQedEventType.SESSION_REJECTED,
            {"reason": reason, "reviewer": reviewer},
            created_by=reviewer,
        )

        logger.info(f"Session {session_id} rejected: {reason}")
        return True

    def export_to_markdown(self, session_id: str) -> Optional[str]:
        """Export session results to Markdown.

        Note: This is a sync method that uses direct cache access.
        """
        session = self._sessions.get(session_id)  # Direct cache access
        if not session or not session.specification:
            return None

        spec = session.specification
        tasks = session.tasks or {}

        md = f"""# {session.project_name} - Migration Specification

**Generated**: {spec['metadata']['generated_at']}
**Workflow**: MarQed Brown-Paper
**Status**: {session.status}

---

## Executive Summary

{spec['executive_summary']}

---

## Current State (AS-IS)

{spec['current_state']['description']}

### Pain Points

{spec['current_state']['pain_points']}

---

## Target State (TO-BE)

{spec['target_state']['description']}

---

## Migration Approach

**Strategy**: {spec['migration_approach']['strategy_type'].replace('_', ' ').title()}

{spec['migration_approach']['strategy_description']}

### Data Migration

{spec['migration_approach']['data_migration']}

---

## Timeline

{spec['timeline']['description']}

**Total Duration**: {spec['timeline']['total_weeks']} weeks

### Phases

| Phase | Name | Weeks | Modules |
|-------|------|-------|---------|
"""

        for phase in spec['timeline']['phases']:
            modules = ', '.join(phase['modules'])
            md += f"| {phase['phase']} | {phase['name']} | {phase['weeks']} | {modules} |\n"

        md += f"""

---

## Stakeholders

{spec['stakeholders']}

---

## Success Criteria

{spec['success_criteria']}

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
"""

        for risk in spec['risks']:
            md += f"| {risk['risk']} | {risk['likelihood']} | {risk['impact']} | {risk['mitigation']} |\n"

        md += f"""

---

## Technical Spikes Required

"""
        for spike in spec['technical_spikes']:
            md += f"- {spike}\n"

        md += f"""

---

## Go/No-Go Checkpoints

"""
        for checkpoint in spec['go_no_go_checkpoints']:
            md += f"- [ ] {checkpoint}\n"

        if tasks:
            md += f"""

---

## Task Summary

- **Epics**: {tasks['summary']['total_epics']}
- **Features**: {tasks['summary']['total_features']}
- **Stories**: {tasks['summary']['total_stories']}
- **Total Story Points**: {tasks['summary']['total_story_points']}
- **Estimated Function Points**: {tasks['summary'].get('estimated_fp', 0)}
- **FP Confidence**: {tasks['summary'].get('fp_confidence', 0)}%

"""

            # Add FP breakdown if available
            if tasks.get('fp_analysis'):
                fp = tasks['fp_analysis']
                md += f"""### Function Point Breakdown

| Component Type | Count | FP |
|---------------|-------|-----|
"""
                for comp_type, data in fp.get('by_type', {}).items():
                    md += f"| {comp_type} | {data['count']} | {data['fp']} |\n"

                md += f"""
**Total UFP**: {fp.get('total_ufp', 0)}
**VAF**: {fp.get('vaf', 1.0)}
**Total AFP**: {fp.get('total_afp', 0)}
**Confidence Score**: {fp.get('confidence_score', 0)}%

"""

        return md


# ============================================================================
# SERVICE SINGLETONS
# ============================================================================

_brown_paper_service: Optional[BrownPaperService] = None
_marqed_workflow: Optional[MarQedBrownPaperWorkflow] = None


def get_brown_paper_service() -> BrownPaperService:
    """Get or create the Brown Paper (code-analysis) service singleton."""
    global _brown_paper_service
    if _brown_paper_service is None:
        _brown_paper_service = BrownPaperService()
    return _brown_paper_service


def get_marqed_brown_paper_workflow() -> MarQedBrownPaperWorkflow:
    """Get or create the MarQed Brown-Paper workflow singleton."""
    global _marqed_workflow
    if _marqed_workflow is None:
        _marqed_workflow = MarQedBrownPaperWorkflow()
    return _marqed_workflow


# Week 159: Business Logic Extraction singletons
_business_domain_extractor: Optional[BusinessDomainExtractorService] = None
_business_story_generator: Optional[BusinessDrivenStoryGeneratorService] = None


def get_business_domain_extractor(
    use_healthcare_patterns: bool = True
) -> BusinessDomainExtractorService:
    """Get or create the BusinessDomainExtractor service singleton."""
    global _business_domain_extractor
    if _business_domain_extractor is None:
        _business_domain_extractor = BusinessDomainExtractorService(
            use_healthcare_patterns=use_healthcare_patterns
        )
    return _business_domain_extractor


def get_business_driven_story_generator() -> BusinessDrivenStoryGeneratorService:
    """Get or create the BusinessDrivenStoryGenerator service singleton."""
    global _business_story_generator
    if _business_story_generator is None:
        _business_story_generator = BusinessDrivenStoryGeneratorService()
    return _business_story_generator
