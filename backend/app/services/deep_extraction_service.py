"""
Deep Extraction Service - Week 82 (Updated Week 99)

Main orchestrator for the 6-cycle hybrid extraction pipeline.
Coordinates static analysis, LLM calls, tier management, and result aggregation.

6 Cycles (Fase 15b - Week 99+):
0. Static Analysis - Deterministic code analysis (ProgramSlicer, BusinessRuleExtractor, etc.)
1. Independent Analysis - Each LLM analyzes code independently
2. Cross-Enrichment - LLMs review and enrich each other's outputs
3. Conflict Detection - Identify disagreements between LLMs + Static vs LLM conflicts
4. Human Decision - Surface conflicts for human resolution (72.5% threshold)
5. Final Synthesis - Create final consensus output

Key Changes Week 99:
- Added Cycle 0: Static Analysis integration
- ConflictDetector with 72.5% confidence threshold
- FREE tier removed - all tiers now include static analysis
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID
import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models.deep_extraction import (
    ExtractionSession,
    ExtractionRun,
    ExtractionLLMResult,
    ExtractionEnrichment,
    ExtractionConsensus,
    ExtractionConflict,
    ExtractionTier,
    ExtractionStatus,
    RunStatus,
    ConsensusStatus,
    ConflictStatus,
    ConflictType,
    ItemType,
    AnalysisType,
    TIER_CONFIG,
)
from app.models.project import Project
from app.services.tier_provider_selector import (
    TierProviderSelector,
    LLMCallResult,
    create_tier_selector,
    compare_tiers,
)
from app.services.extraction_llm_adapter import (
    ExtractionLLMAdapter,
    ExtractionPrompts,
    create_extraction_adapter,
)
from app.services.static_analysis.orchestrator import (
    StaticAnalysisOrchestrator,
    StaticAnalysisConfig,
    StaticAnalysisResult,
    create_orchestrator,
)
from app.services.conflict_detector_service import (
    ConflictDetectorService,
    ConflictType as StaticLLMConflictType,
    ConflictSeverity,
    ConflictDetectionResult,
)

# Week 111: Missing Patterns Integration (Check Alignment, Chunking)
try:
    from app.services.orchestration import (
        CheckAlignmentService,
        AlignmentLevel,
        ChunkingService,
        ChunkStrategy,
        ChunkingConfig,
    )
    WEEK_111_AVAILABLE = True
except ImportError:
    WEEK_111_AVAILABLE = False
    CheckAlignmentService = None
    ChunkingService = None
    ChunkStrategy = None
    ChunkingConfig = None

# Week 102-106: Extraction Services Integration
try:
    from app.services.extraction import (
        # FR-QW-1: Few-Shot Templates
        FewShotTemplateLoader,
        ExtractionDomain,
        # FR-QW-2: INVEST Validator
        INVESTValidator,
        UserStory,
        INVESTValidationResult,
        # FR-QW-3: Acceptance Criteria Enhancer
        AcceptanceCriteriaEnhancer,
        ACEnhancementResult,
        # NFR-QW-1: Quantitative NFR Detector
        QuantitativeNFRDetector,
        NFRDetectionResult,
        # NFR-QW-2: NFR Priority Scoring
        NFRPriorityScorer,
        NFRInput,
        NFRPriorityResult,
        BusinessDomain,
        # NFR-M-1: NFR Architecture Mapper
        NFRArchitectureMapper,
        NFRMapping,
        # FR-M-1: Traceability Matrix Generator
        TraceabilityMatrixGenerator,
        TraceabilityMatrix,
        ArtifactType,
    )
    EXTRACTION_SERVICES_AVAILABLE = True
except ImportError:
    EXTRACTION_SERVICES_AVAILABLE = False
    FewShotTemplateLoader = None
    ExtractionDomain = None
    INVESTValidator = None
    UserStory = None
    AcceptanceCriteriaEnhancer = None
    QuantitativeNFRDetector = None
    NFRPriorityScorer = None
    NFRArchitectureMapper = None
    TraceabilityMatrixGenerator = None


logger = logging.getLogger(__name__)


class DeepExtractionService:
    """
    Orchestrates the Deep Extraction Pipeline.

    This service manages:
    - Session lifecycle (create, run, complete)
    - Tier-aware LLM provider selection
    - Cost tracking and margin calculation
    - 5-cycle extraction flow
    - Re-run capability for tier upgrades

    Usage:
        service = DeepExtractionService(db_session)

        # Start new extraction
        session = await service.start_extraction(
            project_id=1,
            source_path="/opt/projects/myapp",
            tier=ExtractionTier.STANDARD
        )

        # Run cycles
        await service.run_cycle_1(session.id)  # Independent analysis
        await service.run_cycle_2(session.id)  # Cross-enrichment
        await service.run_cycle_3(session.id)  # Conflict detection
        # Cycle 4 is human review (via API)
        await service.run_cycle_5(session.id)  # Final synthesis

        # Or run all cycles
        await service.run_full_extraction(session.id)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._selectors: Dict[UUID, TierProviderSelector] = {}
        self._static_results: Dict[UUID, StaticAnalysisResult] = {}  # Week 99: Cache static analysis results
        self._conflict_detector = ConflictDetectorService()  # Week 99: Static vs LLM conflict detection

        # Week 102-106: Initialize extraction services
        self._init_extraction_services()

        # Week 111: Initialize Missing Patterns services
        self._init_week_111_services()

    def _init_extraction_services(self) -> None:
        """Initialize Week 102-106 extraction services."""
        if not EXTRACTION_SERVICES_AVAILABLE:
            logger.info("Extraction services not available - running without enhancements")
            self._few_shot_loader = None
            self._invest_validator = None
            self._ac_enhancer = None
            self._nfr_detector = None
            self._nfr_scorer = None
            self._nfr_mapper = None
            self._traceability_generator = None
            return

        try:
            # FR-QW-1: Few-Shot Templates per domain
            self._few_shot_loader = FewShotTemplateLoader()
            logger.debug("Initialized FewShotTemplateLoader")

            # FR-QW-2: INVEST Validator for user story quality
            self._invest_validator = INVESTValidator()
            logger.debug("Initialized INVESTValidator")

            # FR-QW-3: Acceptance Criteria Enhancer
            self._ac_enhancer = AcceptanceCriteriaEnhancer()
            logger.debug("Initialized AcceptanceCriteriaEnhancer")

            # NFR-QW-1: Quantitative NFR Detector
            self._nfr_detector = QuantitativeNFRDetector()
            logger.debug("Initialized QuantitativeNFRDetector")

            # NFR-QW-2: NFR Priority Scoring
            self._nfr_scorer = NFRPriorityScorer()
            logger.debug("Initialized NFRPriorityScorer")

            # NFR-M-1: NFR Architecture Mapper
            self._nfr_mapper = NFRArchitectureMapper()
            logger.debug("Initialized NFRArchitectureMapper")

            # FR-M-1: Traceability Matrix Generator
            self._traceability_generator = TraceabilityMatrixGenerator()
            logger.debug("Initialized TraceabilityMatrixGenerator")

            logger.info("All extraction services initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize extraction services: {e}")
            self._few_shot_loader = None
            self._invest_validator = None
            self._ac_enhancer = None
            self._nfr_detector = None
            self._nfr_scorer = None
            self._nfr_mapper = None
            self._traceability_generator = None

    def _init_week_111_services(self) -> None:
        """Initialize Week 111 Missing Patterns services."""
        if not WEEK_111_AVAILABLE:
            logger.info("Week 111 patterns not available - running without alignment/chunking")
            self._alignment_service = None
            self._chunking_service = None
            return

        try:
            # Check Alignment - verify extraction actions align with stated goals
            self._alignment_service = CheckAlignmentService()
            logger.debug("Initialized CheckAlignmentService")

            # Chunking - decompose large codebases for extraction
            self._chunking_service = ChunkingService()
            logger.debug("Initialized ChunkingService")

            logger.info("Week 111 Missing Patterns initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Week 111 patterns: {e}")
            self._alignment_service = None
            self._chunking_service = None

    def _create_alignment_session_for_extraction(
        self,
        session_id: UUID,
        source_path: str,
        tier: str
    ) -> Optional[UUID]:
        """
        Week 111: Create alignment session for tracking extraction goal alignment.

        Returns alignment session UUID for tracking throughout extraction cycles.
        """
        if not self._alignment_service:
            return None

        try:
            goal = f"Extract epics, features, and stories from codebase at {source_path}"
            sub_goals = [
                "Cycle 0: Perform static analysis",
                "Cycle 1: Independent LLM analysis",
                "Cycle 2: Cross-enrichment between LLMs",
                "Cycle 3: Detect and resolve conflicts",
                "Cycle 4: Human review of complex conflicts",
                "Cycle 5: Final synthesis and output",
            ]

            alignment_session = self._alignment_service.create_session(
                goal=goal,
                sub_goals=sub_goals
            )
            logger.debug(f"Created alignment session {alignment_session.id} for extraction {session_id}")
            return alignment_session.id
        except Exception as e:
            logger.warning(f"Failed to create alignment session: {e}")
            return None

    def _record_extraction_action(
        self,
        alignment_session_id: Optional[UUID],
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Week 111: Record an action in the alignment session."""
        if not self._alignment_service or not alignment_session_id:
            return

        try:
            self._alignment_service.record_action(
                session_id=alignment_session_id,
                action=action,
                context=context or {}
            )
        except Exception as e:
            logger.warning(f"Failed to record alignment action: {e}")

    def _chunk_large_codebase(
        self,
        file_contents: Dict[str, str],
        max_chunk_size: int = 50000
    ) -> List[Dict[str, str]]:
        """
        Week 111: Chunk large codebases for manageable LLM processing.

        Returns list of file content chunks, each within the max size limit.
        """
        if not self._chunking_service:
            # Without chunking, return as single batch
            total_size = sum(len(c) for c in file_contents.values())
            if total_size > max_chunk_size:
                logger.warning(f"Large codebase ({total_size} chars) without chunking available")
            return [file_contents]

        try:
            chunks = []
            current_chunk: Dict[str, str] = {}
            current_size = 0

            for filepath, content in file_contents.items():
                file_size = len(content)

                # If single file exceeds max, chunk it
                if file_size > max_chunk_size:
                    # Save current chunk first
                    if current_chunk:
                        chunks.append(current_chunk)
                        current_chunk = {}
                        current_size = 0

                    # Chunk the large file
                    file_chunks = self._chunking_service.chunk_text(
                        text=content,
                        strategy=ChunkStrategy.SEMANTIC,
                        config=ChunkingConfig(max_size=max_chunk_size, overlap=500)
                    )

                    # Add each chunk as separate entry
                    for i, chunk in enumerate(file_chunks.chunks):
                        chunk_path = f"{filepath}#chunk{i}"
                        chunks.append({chunk_path: chunk.content})
                else:
                    # Check if adding this file exceeds limit
                    if current_size + file_size > max_chunk_size:
                        chunks.append(current_chunk)
                        current_chunk = {}
                        current_size = 0

                    current_chunk[filepath] = content
                    current_size += file_size

            # Don't forget last chunk
            if current_chunk:
                chunks.append(current_chunk)

            logger.info(f"Chunked codebase into {len(chunks)} processing batches")
            return chunks

        except Exception as e:
            logger.warning(f"Failed to chunk codebase: {e}")
            return [file_contents]

    def _detect_extraction_domain(self, code_summary: str, file_list: List[str]) -> Optional[str]:
        """
        Week 102: Detect the extraction domain from code analysis.

        Returns domain name for few-shot template selection.
        """
        if not self._few_shot_loader or not ExtractionDomain:
            return None

        # Check file patterns and keywords for domain detection
        combined_text = code_summary.lower() + " ".join(file_list).lower()

        # Healthcare indicators
        if any(kw in combined_text for kw in [
            "patient", "medical", "health", "diagnosis", "hipaa",
            "hl7", "fhir", "clinical", "prescription", "ehr"
        ]):
            return ExtractionDomain.HEALTHCARE.value

        # Finance indicators
        if any(kw in combined_text for kw in [
            "transaction", "payment", "banking", "financial", "trading",
            "account", "invoice", "pci", "kyc", "aml", "ledger"
        ]):
            return ExtractionDomain.FINANCE.value

        # E-commerce indicators
        if any(kw in combined_text for kw in [
            "cart", "checkout", "product", "order", "shipping",
            "inventory", "catalog", "customer", "ecommerce", "shop"
        ]):
            return ExtractionDomain.ECOMMERCE.value

        return ExtractionDomain.GENERIC.value

    def _get_few_shot_examples(self, domain: str) -> str:
        """
        Week 102: Get few-shot examples for the detected domain.

        Returns formatted examples for LLM prompt injection.
        """
        if not self._few_shot_loader:
            return ""

        try:
            templates = self._few_shot_loader.get_templates_for_domain(domain)
            if not templates:
                return ""

            examples = []
            examples.append("\n## Domain-Specific Examples")
            examples.append(f"Based on detected domain: {domain.upper()}")
            examples.append("")

            for template in templates[:3]:  # Limit to 3 examples
                examples.append(f"### Example: {template.title}")
                examples.append(f"**Input:** {template.input_text[:200]}...")
                examples.append(f"**Expected Output:** {template.expected_output[:300]}...")
                examples.append("")

            return "\n".join(examples)
        except Exception as e:
            logger.warning(f"Failed to get few-shot examples: {e}")
            return ""

    def _validate_story_invest(self, story_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Week 102: Validate a user story against INVEST criteria.

        Returns validation result with scores and suggestions.
        """
        if not self._invest_validator or not UserStory:
            return None

        try:
            story = UserStory(
                title=story_data.get("title", ""),
                description=story_data.get("description", ""),
                acceptance_criteria=story_data.get("acceptance_criteria", []),
                story_points=story_data.get("story_points"),
            )
            result = self._invest_validator.validate(story)

            return {
                "overall_score": result.overall_score,
                "is_compliant": result.is_compliant,
                "criterion_scores": {c.name: s for c, s in result.criterion_scores.items()},
                "issues": [{"criterion": i.criterion.name, "message": i.message, "severity": i.severity.name}
                          for i in result.issues],
                "suggestions": result.suggestions,
            }
        except Exception as e:
            logger.warning(f"INVEST validation failed: {e}")
            return None

    def _enhance_acceptance_criteria(self, story_data: Dict[str, Any]) -> Optional[List[str]]:
        """
        Week 102: Enhance acceptance criteria for a story.

        Returns enhanced AC list with edge cases and negative scenarios.
        """
        if not self._ac_enhancer:
            return None

        try:
            existing_ac = story_data.get("acceptance_criteria", [])
            title = story_data.get("title", "")
            description = story_data.get("description", "")

            result = self._ac_enhancer.enhance(
                existing_criteria=existing_ac,
                story_title=title,
                story_description=description,
            )

            return result.enhanced_criteria
        except Exception as e:
            logger.warning(f"AC enhancement failed: {e}")
            return None

    def _score_nfrs(
        self,
        nfr_items: List[Dict[str, Any]],
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Week 102: Score and prioritize NFRs.

        Returns NFRs with priority scores and tiers.
        """
        if not self._nfr_scorer or not NFRInput or not BusinessDomain:
            return nfr_items

        try:
            # Map domain string to BusinessDomain enum
            business_domain = BusinessDomain.GENERAL
            if domain:
                domain_lower = domain.lower()
                if "health" in domain_lower:
                    business_domain = BusinessDomain.HEALTHCARE
                elif "finance" in domain_lower or "bank" in domain_lower:
                    business_domain = BusinessDomain.FINANCE
                elif "commerce" in domain_lower or "retail" in domain_lower:
                    business_domain = BusinessDomain.ECOMMERCE

            scored_nfrs = []
            for nfr in nfr_items:
                nfr_input = NFRInput(
                    category=nfr.get("category", "other"),
                    description=nfr.get("description", ""),
                    business_domain=business_domain,
                    risk_level=nfr.get("risk_level", "medium"),
                )
                result = self._nfr_scorer.score(nfr_input)

                scored_nfr = dict(nfr)
                scored_nfr["priority_score"] = result.score
                scored_nfr["priority_tier"] = result.tier.name
                scored_nfr["scoring_factors"] = [f.name for f in result.factors]
                scored_nfrs.append(scored_nfr)

            # Sort by priority score (highest first)
            scored_nfrs.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
            return scored_nfrs
        except Exception as e:
            logger.warning(f"NFR scoring failed: {e}")
            return nfr_items

    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================

    async def start_extraction(
        self,
        project_id: int,
        source_path: str,
        tier: ExtractionTier = ExtractionTier.BASIC,  # Week 99: Default changed from FREE to BASIC
        workflow_type: str = "GREEN_PAPER",
    ) -> ExtractionSession:
        """
        Start a new extraction session.

        Args:
            project_id: Project to extract from
            source_path: Path to codebase
            tier: Customer tier selection (BASIC, STANDARD, PROFESSIONAL, PREMIUM)
            workflow_type: GREEN_PAPER, BROWN_PAPER, etc.

        Returns:
            Created ExtractionSession

        Note:
            Week 99: FREE tier is deprecated. All tiers now include static analysis (Cycle 0).
            Minimum tier is now BASIC (€5 per 50K LOC).
        """
        tier_config = TIER_CONFIG[tier]

        # Week 99: Warn about deprecated FREE tier
        if tier_config.get("deprecated", False):
            deprecation_msg = tier_config.get("deprecation_message", "This tier is deprecated.")
            logger.warning(f"Deprecated tier used: {tier.value}. {deprecation_msg}")
            # Auto-upgrade to BASIC for new sessions
            logger.info(f"Auto-upgrading from {tier.value} to BASIC tier")
            tier = ExtractionTier.BASIC
            tier_config = TIER_CONFIG[tier]

        # Week 99: Check if tier includes static analysis
        includes_static = tier_config.get("static_analysis", False)

        # Create session
        session = ExtractionSession(
            project_id=project_id,
            source_path=source_path,
            workflow_type=workflow_type,
            tier=tier.value,
            tier_price_usd=tier_config.get("price_eur", tier_config.get("price_usd", 0)),  # Week 99: price_eur preferred
            tier_confidence_target=tier_config["confidence_target"],
            status=ExtractionStatus.STARTED.value,
            current_cycle=0,
        )

        self.db.add(session)
        await self.db.flush()

        # Create initial run
        run = ExtractionRun(
            project_id=project_id,
            session_id=session.id,
            run_number=1,
            tier=tier.value,
            tier_price_usd=tier_config["price_usd"],
            status=RunStatus.PENDING.value,
        )

        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(session)

        # Initialize tier selector
        self._selectors[session.id] = create_tier_selector(tier)

        logger.info(f"Started extraction session {session.id} with tier {tier.value}")

        return session

    async def get_session(self, session_id: UUID) -> Optional[ExtractionSession]:
        """Get extraction session by ID."""
        result = await self.db.execute(
            select(ExtractionSession)
            .options(
                selectinload(ExtractionSession.runs),
                selectinload(ExtractionSession.llm_results),
                selectinload(ExtractionSession.consensus_items),
                selectinload(ExtractionSession.conflicts),
            )
            .where(ExtractionSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_session_progress(self, session_id: UUID) -> Dict[str, Any]:
        """Get detailed progress for a session."""
        session = await self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        selector = self._get_selector(session_id, ExtractionTier(session.tier))

        # Week 99: Get static analysis metrics
        static_metrics = None
        if hasattr(session, 'static_analysis_id') and session.static_analysis_id:
            static_metrics = {
                "analysis_id": session.static_analysis_id,
                "domain_coverage": getattr(session, 'static_domain_coverage', None),
                "nfr_coverage": getattr(session, 'static_nfr_coverage', None),
                "compliance_score": getattr(session, 'static_compliance_score', None),
            }

        return {
            "session_id": str(session.id),
            "status": session.status,
            "current_cycle": session.current_cycle,
            "tier": session.tier,
            "cycles": {
                "cycle_0": {
                    "name": "Static Analysis",
                    "status": "completed" if getattr(session, 'cycle_0_completed_at', None) else "pending",
                    "completed_at": session.cycle_0_completed_at.isoformat() if getattr(session, 'cycle_0_completed_at', None) else None,
                    "metrics": static_metrics,
                },
                "cycle_1": {
                    "name": "Independent Analysis",
                    "status": "completed" if session.cycle_1_completed_at else "pending",
                    "completed_at": session.cycle_1_completed_at.isoformat() if session.cycle_1_completed_at else None,
                },
                "cycle_2": {
                    "name": "Cross-Enrichment",
                    "status": "completed" if session.cycle_2_completed_at else "pending",
                    "completed_at": session.cycle_2_completed_at.isoformat() if session.cycle_2_completed_at else None,
                },
                "cycle_3": {
                    "name": "Conflict Detection",
                    "status": "completed" if session.cycle_3_completed_at else "pending",
                    "completed_at": session.cycle_3_completed_at.isoformat() if session.cycle_3_completed_at else None,
                },
                "cycle_4": {
                    "name": "Human Decision",
                    "status": "completed" if session.cycle_4_completed_at else ("pending" if session.status == ExtractionStatus.AWAITING_REVIEW.value else "skipped"),
                    "completed_at": session.cycle_4_completed_at.isoformat() if session.cycle_4_completed_at else None,
                },
                "cycle_5": {
                    "name": "Final Synthesis",
                    "status": "completed" if session.cycle_5_completed_at else "pending",
                    "completed_at": session.cycle_5_completed_at.isoformat() if session.cycle_5_completed_at else None,
                },
            },
            "results": {
                "total_epics": session.total_epics,
                "total_features": session.total_features,
                "total_stories": session.total_stories,
                "total_tasks": session.total_tasks,
                "total_function_points": session.total_function_points,
            },
            "confidence": {
                "target": session.tier_confidence_target,
                "actual": session.avg_confidence,
                "items_auto_accepted": session.items_auto_accepted,
                "items_human_reviewed": session.items_human_reviewed,
                "threshold": 0.725,  # Week 99: 72.5% threshold
            },
            "cost": {
                "tier_price_usd": session.tier_price_usd,
                "actual_cost_usd": session.actual_cost_usd,
                "margin_usd": session.margin_usd,
                "total_tokens": session.total_tokens_used,
            },
            "provider_stats": selector.get_call_statistics() if selector else {},
        }

    async def list_sessions(
        self,
        project_id: Optional[int] = None,
        status: Optional[ExtractionStatus] = None,
        limit: int = 50,
    ) -> List[ExtractionSession]:
        """List extraction sessions with optional filters."""
        query = select(ExtractionSession).order_by(ExtractionSession.created_at.desc())

        if project_id:
            query = query.where(ExtractionSession.project_id == project_id)

        if status:
            query = query.where(ExtractionSession.status == status.value)

        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # TIER MANAGEMENT
    # =========================================================================

    def _get_selector(
        self,
        session_id: UUID,
        tier: Optional[ExtractionTier] = None
    ) -> TierProviderSelector:
        """Get or create tier selector for a session."""
        if session_id not in self._selectors:
            self._selectors[session_id] = create_tier_selector(tier or ExtractionTier.FREE)
        return self._selectors[session_id]

    async def upgrade_tier(
        self,
        session_id: UUID,
        new_tier: ExtractionTier,
    ) -> Dict[str, Any]:
        """
        Upgrade session to a higher tier.

        Creates a new run with delta tracking from previous.
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        old_tier = ExtractionTier(session.tier)
        if new_tier.value <= old_tier.value:
            raise ValueError(f"New tier {new_tier.value} must be higher than current {old_tier.value}")

        # Get upgrade info from selector
        selector = self._get_selector(session_id, old_tier)
        upgrade_info = selector.upgrade_tier(new_tier)

        # Get previous run
        previous_run = None
        if session.runs:
            previous_run = max(session.runs, key=lambda r: r.run_number)

        # Update session tier
        session.tier = new_tier.value
        new_config = TIER_CONFIG[new_tier]
        session.tier_price_usd = new_config["price_usd"]
        session.tier_confidence_target = new_config["confidence_target"]

        # Create new run
        new_run = ExtractionRun(
            project_id=session.project_id,
            session_id=session.id,
            run_number=(previous_run.run_number + 1) if previous_run else 1,
            tier=new_tier.value,
            tier_price_usd=new_config["price_usd"],
            status=RunStatus.PENDING.value,
            previous_run_id=previous_run.id if previous_run else None,
            credit_from_previous=upgrade_info["credit_usd"],
            amount_charged=upgrade_info["amount_to_charge_usd"],
        )

        self.db.add(new_run)
        await self.db.commit()

        logger.info(f"Upgraded session {session_id} from {old_tier.value} to {new_tier.value}")

        return {
            **upgrade_info,
            "session_id": str(session_id),
            "new_run_id": str(new_run.id),
            "run_number": new_run.run_number,
        }

    @staticmethod
    def get_tier_comparison() -> List[Dict[str, Any]]:
        """Get comparison of all tiers for UI display."""
        return compare_tiers()

    # =========================================================================
    # CYCLE 0: STATIC ANALYSIS (Week 99 - Fase 15b)
    # =========================================================================

    async def run_cycle_0(self, session_id: UUID) -> Dict[str, Any]:
        """
        Cycle 0: Static Analysis (Week 99)

        Runs deterministic code analysis before LLM enrichment:
        - ProgramSlicer: Dependency analysis
        - VariableClassifier: Domain/implementation/control
        - BusinessRuleExtractor: IF-THEN patterns
        - NFRDetector: Non-functional requirements
        - ComplianceChecker: Framework compliance

        This provides 80% deterministic baseline for all extraction tiers.
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Update status
        session.status = ExtractionStatus.RUNNING.value
        session.current_cycle = 0
        await self.db.commit()

        logger.info(f"Cycle 0: Running static analysis for session {session_id}")

        # Get source files
        files_dict, file_list = await self._get_source_files(session.source_path)

        if not files_dict:
            logger.warning(f"No source files found at {session.source_path}")
            session.cycle_0_completed_at = datetime.utcnow()
            await self.db.commit()
            return {
                "cycle": 0,
                "status": "completed",
                "message": "No source files found",
                "files_analyzed": 0,
            }

        # Configure static analysis
        config = StaticAnalysisConfig(
            enable_slicing=True,
            enable_variable_classification=True,
            enable_business_rules=True,
            enable_nfr_detection=True,
            enable_compliance=True,
            compliance_frameworks=self._get_compliance_frameworks(session),
        )

        # Run static analysis
        orchestrator = create_orchestrator(self.db)
        try:
            result = await orchestrator.run_analysis(
                project_id=session.project_id,
                files=files_dict,
                config=config,
            )
        except Exception as e:
            logger.error(f"Static analysis failed: {e}")
            session.cycle_0_completed_at = datetime.utcnow()
            await self.db.commit()
            return {
                "cycle": 0,
                "status": "error",
                "error": str(e),
            }

        # Cache results for later cycles
        self._static_results[session_id] = result

        # Update session with static analysis metrics
        session.total_files = result.total_files_analyzed
        session.static_analysis_id = result.id
        session.static_domain_coverage = result.domain_coverage
        session.static_nfr_coverage = result.nfr_coverage
        session.static_compliance_score = result.compliance_score
        session.cycle_0_completed_at = datetime.utcnow()

        await self.db.commit()

        logger.info(
            f"Cycle 0 completed for session {session_id}: "
            f"{result.total_files_analyzed} files, "
            f"{len(result.business_rules.rules) if result.business_rules else 0} business rules, "
            f"{len(result.nfr_report.detections) if result.nfr_report else 0} NFR detections"
        )

        return {
            "cycle": 0,
            "status": "completed",
            "static_analysis_id": result.id,
            "files_analyzed": result.total_files_analyzed,
            "lines_of_code": result.total_lines_of_code,
            "business_rules_found": len(result.business_rules.rules) if result.business_rules else 0,
            "nfr_detections": len(result.nfr_report.detections) if result.nfr_report else 0,
            "compliance_violations": len(result.compliance_report.violations) if result.compliance_report else 0,
            "domain_coverage": round(result.domain_coverage, 2),
            "nfr_coverage": round(result.nfr_coverage, 2),
            "compliance_score": round(result.compliance_score, 2),
            "high_confidence_findings": len(result.high_confidence_findings),
            "low_confidence_findings": len(result.low_confidence_findings),
        }

    async def _get_source_files(self, source_path: str) -> tuple[Dict[str, str], List[str]]:
        """
        Load source files from disk for static analysis.

        Returns:
            Tuple of (files_dict mapping path->content, list of file paths)
        """
        import os

        files_dict = {}
        file_list = []

        if not source_path or not os.path.exists(source_path):
            return files_dict, file_list

        # Supported extensions for analysis
        supported_extensions = {
            '.py', '.js', '.ts', '.tsx', '.cs', '.vb',
            '.java', '.go', '.rs', '.php', '.rb', '.sql'
        }

        # Directories to skip
        skip_dirs = {
            'node_modules', '.git', '__pycache__', '.venv', 'venv',
            'dist', 'build', '.next', 'coverage', '.tox', 'vendor'
        }

        for root, dirs, files in os.walk(source_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]

            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in supported_extensions:
                    file_path = os.path.join(root, f)
                    rel_path = os.path.relpath(file_path, source_path)

                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
                            content = fp.read()
                            files_dict[rel_path] = content
                            file_list.append(rel_path)
                    except Exception as e:
                        logger.warning(f"Could not read file {file_path}: {e}")

        return files_dict, file_list

    def _get_compliance_frameworks(self, session) -> List[str]:
        """Get configured compliance frameworks for the project."""
        # Check if project has configured frameworks
        if session.project and hasattr(session.project, 'compliance_frameworks'):
            return session.project.compliance_frameworks or []

        # Default to common frameworks based on industry
        return ["ISO27001", "GDPR"]  # Safe defaults

    def _get_static_context(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """Get static analysis context for LLM enrichment."""
        if session_id in self._static_results:
            return self._static_results[session_id].to_llm_context()
        return None

    def _format_static_context_for_llm(self, context: Dict[str, Any]) -> str:
        """Format static analysis context for LLM prompt injection."""
        parts = []

        summary = context.get("static_analysis_summary", {})
        parts.append("## Static Analysis Results (Cycle 0)")
        parts.append(f"- Files analyzed: {summary.get('files_analyzed', 0)}")
        parts.append(f"- Lines of code: {summary.get('lines_of_code', 0)}")
        parts.append(f"- Domain coverage: {summary.get('domain_coverage', 0):.0%}")
        parts.append(f"- NFR coverage: {summary.get('nfr_coverage', 0):.0%}")
        parts.append("")

        # Business rules
        rules = context.get("business_rules", [])
        if rules:
            parts.append("### Business Rules Detected")
            for rule in rules[:20]:  # Limit to top 20
                parts.append(f"- [{rule.get('type', 'rule')}] {rule.get('natural_language', 'Unknown rule')}")
                parts.append(f"  Confidence: {rule.get('confidence', 0):.0%} | Source: {rule.get('source_file', 'unknown')}")
            if len(rules) > 20:
                parts.append(f"  ... and {len(rules) - 20} more rules")
            parts.append("")

        # NFR detections
        nfrs = context.get("nfr_detections", [])
        if nfrs:
            parts.append("### Non-Functional Requirements Detected")
            for nfr in nfrs[:15]:  # Limit to top 15
                parts.append(f"- [{nfr.get('category', 'NFR')}] {nfr.get('description', '')}")
                parts.append(f"  Confidence: {nfr.get('confidence', 0):.0%}")
            if len(nfrs) > 15:
                parts.append(f"  ... and {len(nfrs) - 15} more detections")
            parts.append("")

        # Compliance violations
        violations = context.get("compliance_violations", [])
        if violations:
            parts.append("### Compliance Violations")
            for v in violations[:10]:  # Limit to top 10
                parts.append(f"- [{v.get('framework', 'Unknown')}] {v.get('title', '')}")
                parts.append(f"  Severity: {v.get('severity', 'unknown')} | File: {v.get('file_path', 'unknown')}")
            if len(violations) > 10:
                parts.append(f"  ... and {len(violations) - 10} more violations")
            parts.append("")

        # Domain variables
        domain_vars = context.get("domain_variables", [])
        if domain_vars:
            parts.append("### Domain Variables")
            parts.append(f"Found {len(domain_vars)} domain-specific variables: {', '.join(domain_vars[:20])}")
            if len(domain_vars) > 20:
                parts.append(f"... and {len(domain_vars) - 20} more")
            parts.append("")

        parts.append("---")
        parts.append("IMPORTANT: Validate and enrich the above static findings. If you disagree with a high-confidence finding, explain why.")
        parts.append("---")

        return "\n".join(parts)

    # =========================================================================
    # CYCLE EXECUTION (Week 83-84)
    # =========================================================================

    async def _get_code_summary(self, source_path: str) -> tuple[str, List[str]]:
        """
        Get code summary and file list from source path.

        In production, this would scan the actual filesystem.
        For now, returns placeholder data.
        """
        import os

        file_list = []
        code_summary = ""

        if source_path and os.path.exists(source_path):
            # Scan actual directory
            for root, dirs, files in os.walk(source_path):
                # Skip common non-code directories
                dirs[:] = [d for d in dirs if d not in [
                    'node_modules', '.git', '__pycache__', '.venv', 'venv',
                    'dist', 'build', '.next', 'coverage'
                ]]

                for f in files:
                    if f.endswith(('.py', '.js', '.ts', '.tsx', '.java', '.go', '.rs', '.cs', '.php', '.rb')):
                        rel_path = os.path.relpath(os.path.join(root, f), source_path)
                        file_list.append(rel_path)

            code_summary = f"""
Project at: {source_path}
Total code files: {len(file_list)}
File types: {', '.join(set(f.split('.')[-1] for f in file_list if '.' in f))}
"""
        else:
            # Placeholder for testing
            file_list = [
                "src/main.py",
                "src/models/user.py",
                "src/api/routes.py",
                "src/services/auth.py",
                "tests/test_auth.py",
            ]
            code_summary = f"""
Demo project analysis
Total files: {len(file_list)}
This is a placeholder for testing the extraction pipeline.
"""

        return code_summary, file_list

    async def run_cycle_1(self, session_id: UUID) -> Dict[str, Any]:
        """
        Cycle 1: Independent Analysis

        Each LLM analyzes the codebase independently, focusing on:
        - Architecture (system structure, patterns)
        - Business Logic (use cases, workflows)
        - Security (vulnerabilities, risks)
        - Code Structure (files, dependencies)
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        selector = self._get_selector(session_id, ExtractionTier(session.tier))
        adapter = create_extraction_adapter(selector)

        # Update status
        session.status = ExtractionStatus.RUNNING.value
        session.current_cycle = 1
        await self.db.commit()

        # Get code summary
        code_summary, file_list = await self._get_code_summary(session.source_path)

        # Update session with file info
        session.total_files = len(file_list)

        # Week 99: Get static analysis context if available
        static_context = self._get_static_context(session_id)
        if static_context:
            # Enhance code summary with static analysis findings
            static_summary = self._format_static_context_for_llm(static_context)
            code_summary = f"{code_summary}\n\n{static_summary}"
            logger.info(f"Cycle 1: Including static analysis context with {len(static_context.get('business_rules', []))} rules")

        # Week 102: Detect domain and add few-shot examples
        detected_domain = self._detect_extraction_domain(code_summary, file_list)
        if detected_domain:
            few_shot_examples = self._get_few_shot_examples(detected_domain)
            if few_shot_examples:
                code_summary = f"{code_summary}\n\n{few_shot_examples}"
                logger.info(f"Cycle 1: Added few-shot examples for domain '{detected_domain}'")

            # Store detected domain on session for later use
            if hasattr(session, 'detected_domain'):
                session.detected_domain = detected_domain

        # Get provider assignments for cycle 1
        assignments = selector.get_providers_for_cycle(1)

        logger.info(f"Cycle 1: Running {len(assignments)} parallel LLM analyses for session {session_id}")

        # Prepare parallel calls
        calls = []
        for provider_id, analysis_type in assignments:
            prompt_methods = {
                "architecture": ExtractionPrompts.get_architecture_prompt,
                "business_logic": ExtractionPrompts.get_business_logic_prompt,
                "security": ExtractionPrompts.get_security_prompt,
                "code_structure": ExtractionPrompts.get_code_structure_prompt,
            }
            prompt_method = prompt_methods.get(analysis_type, ExtractionPrompts.get_architecture_prompt)
            prompt = prompt_method(code_summary, file_list)
            calls.append((provider_id, prompt, analysis_type))

        # Execute parallel LLM calls
        try:
            parallel_results = await adapter.call_llms_parallel(
                calls,
                system=ExtractionPrompts.SYSTEM_BASE,
                timeout=300,  # 5 minutes per call
            )
        finally:
            await adapter.close()

        # Process results and store in database
        results = []
        total_epics = 0
        total_features = 0
        total_stories = 0
        total_tasks = 0

        for analysis_type, llm_result in parallel_results:
            # Parse JSON if successful
            parsed_data = None
            if llm_result.success:
                success, parsed = adapter.parse_json_response(llm_result.content)
                if success:
                    parsed_data = parsed

            # Extract items from parsed data
            extracted_epics = []
            extracted_features = []
            extracted_stories = []
            extracted_tasks = []

            if parsed_data:
                extracted_epics = parsed_data.get("epics", [])
                extracted_features = parsed_data.get("features", [])
                extracted_stories = []
                extracted_tasks = parsed_data.get("tasks", [])

                # Extract stories from features
                for feature in extracted_features:
                    if "stories" in feature:
                        extracted_stories.extend(feature.get("stories", []))

                # Week 102: Apply INVEST validation to each story
                for story in extracted_stories:
                    invest_result = self._validate_story_invest(story)
                    if invest_result:
                        story["invest_score"] = invest_result["overall_score"]
                        story["invest_compliant"] = invest_result["is_compliant"]
                        story["invest_issues"] = invest_result["issues"]
                        story["invest_suggestions"] = invest_result["suggestions"]

                        # Enhance acceptance criteria if score is low
                        if invest_result["overall_score"] < 0.7:
                            enhanced_ac = self._enhance_acceptance_criteria(story)
                            if enhanced_ac:
                                story["enhanced_acceptance_criteria"] = enhanced_ac

                total_epics += len(extracted_epics)
                total_features += len(extracted_features)
                total_stories += len(extracted_stories)
                total_tasks += len(extracted_tasks)

            # Create database record
            db_result = ExtractionLLMResult(
                session_id=session.id,
                cycle=1,
                llm_provider=llm_result.provider_id.split("/")[0],
                llm_model=llm_result.model,
                analysis_type=analysis_type,
                raw_output=llm_result.content if llm_result.success else llm_result.error,
                parsed_output=parsed_data,
                extracted_epics=extracted_epics,
                extracted_features=extracted_features,
                extracted_stories=extracted_stories,
                extracted_tasks=extracted_tasks,
                tokens_input=llm_result.tokens_input,
                tokens_output=llm_result.tokens_output,
                latency_ms=llm_result.latency_ms,
                cost_usd=llm_result.cost_usd,
            )
            self.db.add(db_result)

            results.append({
                "provider": llm_result.provider_id,
                "analysis_type": analysis_type,
                "success": llm_result.success,
                "epics_found": len(extracted_epics),
                "features_found": len(extracted_features),
                "stories_found": len(extracted_stories),
                "tasks_found": len(extracted_tasks),
                "latency_ms": llm_result.latency_ms,
                "tokens": llm_result.tokens_input + llm_result.tokens_output,
                "error": llm_result.error if not llm_result.success else None,
            })

        # Update session totals
        session.total_epics = total_epics
        session.total_features = total_features
        session.total_stories = total_stories
        session.total_tasks = total_tasks
        session.cycle_1_completed_at = datetime.utcnow()

        # Update cost tracking
        stats = selector.get_call_statistics()
        session.total_tokens_used = stats["total_tokens"]
        session.actual_cost_usd = stats["total_cost_usd"]

        await self.db.commit()

        logger.info(f"Cycle 1 completed for session {session_id}: {total_epics} epics, {total_features} features, {total_stories} stories, {total_tasks} tasks")

        return {
            "cycle": 1,
            "status": "completed",
            "llm_results": results,
            "providers_used": len(assignments),
            "totals": {
                "epics": total_epics,
                "features": total_features,
                "stories": total_stories,
                "tasks": total_tasks,
            },
            "cost_usd": stats["total_cost_usd"],
            "tokens_used": stats["total_tokens"],
        }

    async def run_cycle_2(self, session_id: UUID) -> Dict[str, Any]:
        """
        Cycle 2: Cross-Enrichment

        Each LLM reviews another's output and suggests:
        - Additions (missed items)
        - Modifications (improved descriptions)
        - Confidence adjustments
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.current_cycle = 2
        await self.db.commit()

        selector = self._get_selector(session_id, ExtractionTier(session.tier))
        adapter = create_extraction_adapter(selector)

        # Get Cycle 1 results
        cycle_1_results = [r for r in session.llm_results if r.cycle == 1 and r.parsed_output]

        if not cycle_1_results:
            logger.warning(f"No Cycle 1 results found for session {session_id}")
            session.cycle_2_completed_at = datetime.utcnow()
            await self.db.commit()
            return {
                "cycle": 2,
                "status": "completed",
                "enrichments_created": 0,
                "message": "No Cycle 1 results to enrich",
            }

        # Get available providers for enrichment
        providers = selector.get_provider_ids()
        enrichments_created = 0

        logger.info(f"Cycle 2: Cross-enrichment with {len(providers)} providers on {len(cycle_1_results)} results")

        try:
            # For each Cycle 1 result, have other LLMs review it
            for original_result in cycle_1_results:
                original_provider = f"{original_result.llm_provider}/{original_result.llm_model}"

                # Select a different provider for review (round-robin)
                reviewer_candidates = [p for p in providers if p != original_provider]
                if not reviewer_candidates:
                    reviewer_candidates = providers[:1]  # Fallback to first provider

                for reviewer_provider in reviewer_candidates[:2]:  # Max 2 reviewers per result
                    # Run enrichment
                    result, enrichment_data = await adapter.run_enrichment(
                        reviewer_provider_id=reviewer_provider,
                        original_analysis=original_result.parsed_output,
                        original_analysis_type=original_result.analysis_type or "general",
                    )

                    # Store enrichment
                    enrichment = ExtractionEnrichment(
                        session_id=session.id,
                        source_result_id=original_result.id,
                        reviewer_llm=reviewer_provider,
                        additions=enrichment_data.get("additions", []) if enrichment_data else [],
                        modifications=enrichment_data.get("modifications", []) if enrichment_data else [],
                        confidence_adjustments=enrichment_data.get("confidence_adjustments") if enrichment_data else None,
                    )
                    self.db.add(enrichment)
                    enrichments_created += 1

        finally:
            await adapter.close()

        session.cycle_2_completed_at = datetime.utcnow()

        # Update cost tracking
        stats = selector.get_call_statistics()
        session.total_tokens_used = stats["total_tokens"]
        session.actual_cost_usd = stats["total_cost_usd"]

        await self.db.commit()

        logger.info(f"Cycle 2 completed for session {session_id}: {enrichments_created} enrichments created")

        return {
            "cycle": 2,
            "status": "completed",
            "enrichments_created": enrichments_created,
            "cost_usd": stats["total_cost_usd"],
            "tokens_used": stats["total_tokens"],
        }

    async def run_cycle_3(self, session_id: UUID) -> Dict[str, Any]:
        """
        Cycle 3: Conflict Detection

        Analyze all LLM outputs to identify:
        - Consensus items (high agreement -> auto-accept)
        - Low confidence items (need human review)
        - Conflicts (disagreements to resolve)
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.current_cycle = 3
        await self.db.commit()

        selector = self._get_selector(session_id, ExtractionTier(session.tier))
        confidence_target = selector.get_confidence_target()

        # Collect all items from Cycle 1 results
        all_items = self._collect_items_from_results(session.llm_results)

        # Group items by similarity (title-based matching)
        grouped_items = self._group_similar_items(all_items)

        consensus_created = 0
        conflicts_created = 0
        auto_accepted = 0

        for group_key, items in grouped_items.items():
            item_type, title = group_key

            # Calculate consensus score
            llm_providers = list(set(item["provider"] for item in items))
            total_llms = len(selector.get_provider_ids())
            agreement_ratio = len(llm_providers) / max(total_llms, 1)

            # Combine data from all agreeing LLMs
            combined_data = self._merge_item_data(items)
            description = combined_data.get("description", "")

            # Check for conflicts within the group
            conflicts = self._detect_conflicts_in_group(items)

            if conflicts:
                # Create conflict records
                for conflict_type, conflict_data in conflicts:
                    conflict = ExtractionConflict(
                        session_id=session.id,
                        conflict_type=conflict_type,
                        item_type=item_type,
                        option_a=conflict_data.get("option_a"),
                        option_b=conflict_data.get("option_b"),
                        option_c=conflict_data.get("option_c"),
                        option_d=conflict_data.get("option_d"),
                        llm_recommendation=conflict_data.get("recommendation"),
                        recommendation_reasoning=conflict_data.get("reasoning"),
                        status=ConflictStatus.PENDING.value,
                    )
                    self.db.add(conflict)
                    conflicts_created += 1
            else:
                # Create consensus item
                confidence_score = self._calculate_confidence(
                    agreement_ratio=agreement_ratio,
                    item_count=len(items),
                    has_enrichments=any(item.get("enriched") for item in items),
                )

                # Determine status based on confidence
                if confidence_score >= confidence_target:
                    status = ConsensusStatus.AUTO_ACCEPTED.value
                    auto_accepted += 1
                else:
                    status = ConsensusStatus.HUMAN_REVIEW.value

                consensus = ExtractionConsensus(
                    session_id=session.id,
                    item_type=item_type,
                    item_title=title[:300],  # Truncate if needed
                    item_description=description[:2000] if description else None,
                    supporting_llms=llm_providers,
                    confidence_score=confidence_score,
                    confidence_breakdown={
                        "agreement_ratio": agreement_ratio,
                        "llm_count": len(llm_providers),
                        "total_llms": total_llms,
                        "enriched": any(item.get("enriched") for item in items),
                    },
                    status=status,
                    item_data=combined_data,
                )
                self.db.add(consensus)
                consensus_created += 1

        # Update session stats
        session.items_auto_accepted = auto_accepted
        session.avg_confidence = self._calculate_avg_confidence(grouped_items, selector)

        # Determine if human review is needed
        needs_review = conflicts_created > 0 or (consensus_created - auto_accepted) > 0
        if needs_review or selector.includes_human_review():
            session.status = ExtractionStatus.AWAITING_REVIEW.value
        else:
            # No conflicts and all items auto-accepted - can skip to Cycle 5
            session.status = ExtractionStatus.RUNNING.value

        session.cycle_3_completed_at = datetime.utcnow()
        await self.db.commit()

        logger.info(
            f"Cycle 3 completed for session {session_id}: "
            f"{consensus_created} consensus items ({auto_accepted} auto-accepted), "
            f"{conflicts_created} conflicts"
        )

        return {
            "cycle": 3,
            "status": "completed",
            "consensus_items": consensus_created,
            "auto_accepted": auto_accepted,
            "needs_human_review": consensus_created - auto_accepted,
            "conflicts_found": conflicts_created,
            "avg_confidence": session.avg_confidence,
            "awaiting_review": session.status == ExtractionStatus.AWAITING_REVIEW.value,
        }

    def _collect_items_from_results(
        self,
        llm_results: List[ExtractionLLMResult]
    ) -> List[Dict[str, Any]]:
        """Collect all extracted items from LLM results."""
        all_items = []

        for result in llm_results:
            if result.cycle != 1 or not result.parsed_output:
                continue

            provider = f"{result.llm_provider}/{result.llm_model}"

            # Collect epics
            for epic in result.extracted_epics or []:
                all_items.append({
                    "type": ItemType.EPIC.value,
                    "title": epic.get("title", "Untitled Epic"),
                    "data": epic,
                    "provider": provider,
                    "analysis_type": result.analysis_type,
                })

            # Collect features
            for feature in result.extracted_features or []:
                all_items.append({
                    "type": ItemType.FEATURE.value,
                    "title": feature.get("title", "Untitled Feature"),
                    "data": feature,
                    "provider": provider,
                    "analysis_type": result.analysis_type,
                })

            # Collect stories
            for story in result.extracted_stories or []:
                all_items.append({
                    "type": ItemType.STORY.value,
                    "title": story.get("title", "Untitled Story"),
                    "data": story,
                    "provider": provider,
                    "analysis_type": result.analysis_type,
                })

            # Collect tasks
            for task in result.extracted_tasks or []:
                all_items.append({
                    "type": ItemType.TASK.value,
                    "title": task.get("title", task.get("name", "Untitled Task")),
                    "data": task,
                    "provider": provider,
                    "analysis_type": result.analysis_type,
                })

        return all_items

    def _group_similar_items(
        self,
        items: List[Dict[str, Any]]
    ) -> Dict[tuple, List[Dict[str, Any]]]:
        """Group items by similarity using fuzzy title matching."""
        from difflib import SequenceMatcher

        groups: Dict[tuple, List[Dict[str, Any]]] = {}

        for item in items:
            item_type = item["type"]
            title = item["title"].lower().strip()

            # Find existing group with similar title
            matched_key = None
            best_ratio = 0.0

            for key in groups:
                if key[0] != item_type:
                    continue

                existing_title = key[1].lower()
                ratio = SequenceMatcher(None, title, existing_title).ratio()

                if ratio > 0.8 and ratio > best_ratio:  # 80% similarity threshold
                    matched_key = key
                    best_ratio = ratio

            if matched_key:
                groups[matched_key].append(item)
            else:
                # Create new group
                key = (item_type, item["title"])
                groups[key] = [item]

        return groups

    def _merge_item_data(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge data from multiple items into a single combined item."""
        if not items:
            return {}

        # Start with the first item's data
        merged = dict(items[0].get("data", {}))

        # Merge additional fields from other items
        for item in items[1:]:
            data = item.get("data", {})
            for key, value in data.items():
                if key not in merged:
                    merged[key] = value
                elif isinstance(merged[key], list) and isinstance(value, list):
                    # Merge lists (deduplicate)
                    existing = set(str(x) for x in merged[key])
                    for v in value:
                        if str(v) not in existing:
                            merged[key].append(v)

        return merged

    def _detect_conflicts_in_group(
        self,
        items: List[Dict[str, Any]]
    ) -> List[tuple]:
        """Detect conflicts within a group of similar items."""
        conflicts = []

        if len(items) < 2:
            return conflicts

        # Check for priority conflicts
        priorities = set()
        for item in items:
            priority = item.get("data", {}).get("priority")
            if priority:
                priorities.add(priority)

        if len(priorities) > 1:
            conflict_data = {
                "option_a": {"priority": list(priorities)[0], "provider": items[0]["provider"]},
                "option_b": {"priority": list(priorities)[1], "provider": items[1]["provider"]} if len(items) > 1 else None,
                "recommendation": list(priorities)[0],
                "reasoning": "First LLM's priority selected as default",
            }
            conflicts.append((ConflictType.PRIORITY.value, conflict_data))

        # Check for complexity/scope conflicts
        complexities = set()
        for item in items:
            complexity = item.get("data", {}).get("estimated_complexity") or item.get("data", {}).get("complexity")
            if complexity:
                complexities.add(complexity)

        if len(complexities) > 1:
            conflict_data = {
                "option_a": {"complexity": list(complexities)[0], "provider": items[0]["provider"]},
                "option_b": {"complexity": list(complexities)[1], "provider": items[1]["provider"]} if len(items) > 1 else None,
                "recommendation": "medium",
                "reasoning": "Default to medium complexity when LLMs disagree",
            }
            conflicts.append((ConflictType.SCOPE.value, conflict_data))

        return conflicts

    def _calculate_confidence(
        self,
        agreement_ratio: float,
        item_count: int,
        has_enrichments: bool,
    ) -> float:
        """Calculate confidence score for an item."""
        # Base confidence from agreement ratio (0-70%)
        base_confidence = agreement_ratio * 0.7

        # Bonus for multiple sources (0-15%)
        source_bonus = min(item_count * 0.05, 0.15)

        # Bonus for enrichment validation (0-15%)
        enrichment_bonus = 0.15 if has_enrichments else 0.0

        return min(base_confidence + source_bonus + enrichment_bonus, 1.0)

    def _calculate_avg_confidence(
        self,
        grouped_items: Dict[tuple, List[Dict[str, Any]]],
        selector: TierProviderSelector,
    ) -> float:
        """Calculate average confidence across all items."""
        if not grouped_items:
            return 0.0

        total_confidence = 0.0
        total_llms = len(selector.get_provider_ids())

        for items in grouped_items.values():
            llm_count = len(set(item["provider"] for item in items))
            agreement_ratio = llm_count / max(total_llms, 1)
            confidence = self._calculate_confidence(
                agreement_ratio=agreement_ratio,
                item_count=len(items),
                has_enrichments=any(item.get("enriched") for item in items),
            )
            total_confidence += confidence

        return total_confidence / len(grouped_items)

    async def complete_human_review(self, session_id: UUID) -> Dict[str, Any]:
        """
        Complete Cycle 4: Human Decision

        Called after all conflicts are resolved and consensus items reviewed.
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Check all conflicts are resolved
        pending_conflicts = [c for c in session.conflicts if c.status == ConflictStatus.PENDING.value]
        if pending_conflicts:
            return {
                "status": "incomplete",
                "pending_conflicts": len(pending_conflicts),
                "message": f"{len(pending_conflicts)} conflicts still pending",
            }

        session.current_cycle = 4
        session.cycle_4_completed_at = datetime.utcnow()
        session.status = ExtractionStatus.RUNNING.value

        # Count human reviewed items
        reviewed = [c for c in session.consensus_items if c.status in [ConsensusStatus.ACCEPTED.value, ConsensusStatus.REJECTED.value]]
        session.items_human_reviewed = len(reviewed)

        await self.db.commit()

        logger.info(f"Cycle 4 (human review) completed for session {session_id}")

        return {
            "cycle": 4,
            "status": "completed",
            "items_reviewed": len(reviewed),
            "conflicts_resolved": len(session.conflicts) - len(pending_conflicts),
        }

    async def run_cycle_5(self, session_id: UUID) -> Dict[str, Any]:
        """
        Cycle 5: Final Synthesis with LLM

        For PREMIUM tier, uses Claude Opus 4.5 for best reasoning.
        For other tiers, uses the best available LLM.

        Creates:
        - Validated Epic→Feature→Story→Task hierarchy
        - Confidence explanations per item
        - Function point estimates per Story/Task
        - Final synthesis summary
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.current_cycle = 5
        await self.db.commit()

        # Get selector and adapter
        tier = ExtractionTier(session.tier)
        selector = self._get_selector(session_id, tier)
        adapter = create_extraction_adapter(selector)

        # Collect accepted items
        accepted_items = self._get_accepted_items(session)

        # Prepare items for synthesis
        items_for_synthesis = []
        for item in accepted_items:
            items_for_synthesis.append({
                "type": item.item_type,
                "title": item.item_title,
                "description": item.item_description,
                "confidence_score": item.confidence_score,
                "supporting_llms": item.supporting_llms,
                "data": item.item_data,
            })

        # Project info for synthesis
        project_info = {
            "name": session.project.name if session.project else "Unknown",
            "source_path": session.source_path,
            "total_files": session.total_files,
        }

        # Get synthesis provider (Opus for PREMIUM, best available for others)
        synthesis_assignments = selector.get_providers_for_cycle(5)
        if synthesis_assignments:
            synthesis_provider = synthesis_assignments[0][0]
        else:
            synthesis_provider = "ollama/deepseek-r1"  # Fallback

        logger.info(f"Cycle 5: Running synthesis with {synthesis_provider} for session {session_id}")

        # Run LLM synthesis
        llm_synthesis = None
        synthesis_result = None

        try:
            synthesis_result, parsed_synthesis = await adapter.run_synthesis(
                provider_id=synthesis_provider,
                accepted_items=items_for_synthesis,
                tier=tier.value,
                project_info=project_info,
                timeout=300,  # 5 minutes for synthesis
            )

            if parsed_synthesis:
                llm_synthesis = parsed_synthesis
                logger.info(f"LLM synthesis successful with {synthesis_provider}")

                # Update consensus items with confidence explanations from synthesis
                await self._apply_synthesis_updates(session, llm_synthesis)

        except Exception as e:
            logger.warning(f"LLM synthesis failed: {e}, falling back to basic aggregation")
        finally:
            await adapter.close()

        # Count final items by type
        final_epics = [i for i in accepted_items if i.item_type == ItemType.EPIC.value]
        final_features = [i for i in accepted_items if i.item_type == ItemType.FEATURE.value]
        final_stories = [i for i in accepted_items if i.item_type == ItemType.STORY.value]
        final_tasks = [i for i in accepted_items if i.item_type == ItemType.TASK.value]

        # Update session totals
        session.total_epics = len(final_epics)
        session.total_features = len(final_features)
        session.total_stories = len(final_stories)
        session.total_tasks = len(final_tasks)

        # Calculate function points - use LLM synthesis if available
        if llm_synthesis and "summary" in llm_synthesis:
            session.total_function_points = llm_synthesis["summary"].get("total_function_points", 0)
        else:
            session.total_function_points = self._estimate_function_points(accepted_items)

        # Calculate final average confidence
        if llm_synthesis and "summary" in llm_synthesis:
            session.avg_confidence = llm_synthesis["summary"].get("avg_confidence", 0.0)
        elif accepted_items:
            session.avg_confidence = sum(i.confidence_score for i in accepted_items) / len(accepted_items)
        else:
            session.avg_confidence = 0.0

        # Count review statistics
        auto_accepted = [i for i in session.consensus_items if i.status == ConsensusStatus.AUTO_ACCEPTED.value]
        human_accepted = [i for i in session.consensus_items if i.status == ConsensusStatus.ACCEPTED.value]
        human_rejected = [i for i in session.consensus_items if i.status == ConsensusStatus.REJECTED.value]

        session.items_auto_accepted = len(auto_accepted)
        session.items_human_reviewed = len(human_accepted) + len(human_rejected)

        # Calculate costs
        stats = selector.get_call_statistics()
        session.actual_cost_usd = stats["total_cost_usd"]
        session.total_tokens_used = stats["total_tokens"]
        session.margin_usd = session.tier_price_usd - session.actual_cost_usd

        # Week 102-106: Generate traceability matrix
        traceability_data = await self._generate_traceability_matrix(
            session=session,
            epics=final_epics,
            features=final_features,
            stories=final_stories,
            tasks=final_tasks,
        )

        # Week 102: Apply NFR scoring if NFRs were detected
        nfr_summary = None
        if static_result := self._static_results.get(session_id):
            if hasattr(static_result, 'nfr_report') and static_result.nfr_report:
                nfr_items = [
                    {"category": d.category, "description": d.description, "risk_level": getattr(d, 'risk_level', 'medium')}
                    for d in static_result.nfr_report.detections
                ]
                scored_nfrs = self._score_nfrs(nfr_items, getattr(session, 'detected_domain', None))
                nfr_summary = {
                    "total_nfrs": len(scored_nfrs),
                    "critical_nfrs": len([n for n in scored_nfrs if n.get("priority_tier") == "CRITICAL"]),
                    "high_priority_nfrs": len([n for n in scored_nfrs if n.get("priority_tier") == "HIGH"]),
                    "scored_nfrs": scored_nfrs[:10],  # Top 10 by priority
                }

        # Generate final synthesis summary
        synthesis_summary = self._generate_synthesis_summary(
            session=session,
            final_epics=final_epics,
            final_features=final_features,
            final_stories=final_stories,
            final_tasks=final_tasks,
        )

        # Add traceability matrix and NFR summary
        if traceability_data:
            synthesis_summary["traceability"] = traceability_data
        if nfr_summary:
            synthesis_summary["nfr_summary"] = nfr_summary

        # Add LLM synthesis data if available
        if llm_synthesis:
            synthesis_summary["llm_synthesis"] = {
                "provider": synthesis_provider,
                "synthesis_metadata": llm_synthesis.get("synthesis_metadata", {}),
                "epics_with_hierarchy": llm_synthesis.get("epics", []),
            }

        # Mark session as completed
        session.cycle_5_completed_at = datetime.utcnow()
        session.completed_at = datetime.utcnow()
        session.status = ExtractionStatus.COMPLETED.value

        await self.db.commit()

        logger.info(
            f"Cycle 5 completed for session {session_id}: "
            f"{session.total_epics} epics, {session.total_features} features, "
            f"{session.total_stories} stories, {session.total_tasks} tasks, "
            f"{session.total_function_points} FP (synthesized by {synthesis_provider})"
        )

        return {
            "cycle": 5,
            "status": "completed",
            "session_status": "completed",
            "synthesis_provider": synthesis_provider,
            "synthesis_success": llm_synthesis is not None,
            "totals": {
                "epics": session.total_epics,
                "features": session.total_features,
                "stories": session.total_stories,
                "tasks": session.total_tasks,
                "function_points": session.total_function_points,
            },
            "confidence": {
                "average": session.avg_confidence,
                "items_auto_accepted": session.items_auto_accepted,
                "items_human_reviewed": session.items_human_reviewed,
            },
            "cost": {
                "tier_price_usd": session.tier_price_usd,
                "actual_cost_usd": session.actual_cost_usd,
                "margin_usd": session.margin_usd,
                "tokens_used": session.total_tokens_used,
            },
            "synthesis_summary": synthesis_summary,
        }

    async def _apply_synthesis_updates(
        self,
        session: ExtractionSession,
        synthesis: Dict[str, Any],
    ) -> None:
        """
        Apply LLM synthesis updates to consensus items.

        Updates:
        - Confidence explanations
        - Function point estimates
        - Hierarchical relationships
        """
        if not synthesis or "epics" not in synthesis:
            return

        # Build lookup by title for matching
        consensus_by_title = {}
        for item in session.consensus_items:
            key = (item.item_type, item.item_title.lower().strip())
            consensus_by_title[key] = item

        # Apply updates from synthesized epics
        for epic in synthesis.get("epics", []):
            epic_key = (ItemType.EPIC.value, epic.get("title", "").lower().strip())
            if epic_key in consensus_by_title:
                consensus_item = consensus_by_title[epic_key]
                item_data = consensus_item.item_data or {}

                # Add confidence explanation
                if "confidence_explanation" in epic:
                    item_data["confidence_explanation"] = epic["confidence_explanation"]

                # Add total FP for epic
                if "total_function_points" in epic:
                    item_data["total_function_points"] = epic["total_function_points"]

                # Add synthesized ID
                if "id" in epic:
                    item_data["synthesized_id"] = epic["id"]

                consensus_item.item_data = item_data

            # Process features within epic
            for feature in epic.get("features", []):
                feat_key = (ItemType.FEATURE.value, feature.get("title", "").lower().strip())
                if feat_key in consensus_by_title:
                    consensus_item = consensus_by_title[feat_key]
                    item_data = consensus_item.item_data or {}

                    if "confidence_explanation" in feature:
                        item_data["confidence_explanation"] = feature["confidence_explanation"]
                    if "id" in feature:
                        item_data["synthesized_id"] = feature["id"]
                    if "parent_epic_id" not in item_data:
                        item_data["parent_epic_id"] = epic.get("id")

                    consensus_item.item_data = item_data

                # Process stories within feature
                for story in feature.get("stories", []):
                    story_key = (ItemType.STORY.value, story.get("title", "").lower().strip())
                    if story_key in consensus_by_title:
                        consensus_item = consensus_by_title[story_key]
                        item_data = consensus_item.item_data or {}

                        if "function_points" in story:
                            item_data["function_points"] = story["function_points"]
                        if "fp_rationale" in story:
                            item_data["fp_rationale"] = story["fp_rationale"]
                        if "story_points" in story:
                            item_data["story_points"] = story["story_points"]
                        if "acceptance_criteria" in story:
                            item_data["acceptance_criteria"] = story["acceptance_criteria"]
                        if "id" in story:
                            item_data["synthesized_id"] = story["id"]
                        if "parent_feature_id" not in item_data:
                            item_data["parent_feature_id"] = feature.get("id")

                        consensus_item.item_data = item_data

                    # Process tasks within story
                    for task in story.get("tasks", []):
                        task_key = (ItemType.TASK.value, task.get("title", "").lower().strip())
                        if task_key in consensus_by_title:
                            consensus_item = consensus_by_title[task_key]
                            item_data = consensus_item.item_data or {}

                            if "function_points" in task:
                                item_data["function_points"] = task["function_points"]
                            if "estimated_hours" in task:
                                item_data["estimated_hours"] = task["estimated_hours"]
                            if "task_type" in task:
                                item_data["task_type"] = task["task_type"]
                            if "id" in task:
                                item_data["synthesized_id"] = task["id"]
                            if "parent_story_id" not in item_data:
                                item_data["parent_story_id"] = story.get("id")

                            consensus_item.item_data = item_data

        await self.db.commit()
        logger.info(f"Applied synthesis updates to {len(consensus_by_title)} consensus items")

    def _get_accepted_items(self, session: ExtractionSession) -> List[ExtractionConsensus]:
        """Get all accepted consensus items (auto + human accepted)."""
        accepted_statuses = [
            ConsensusStatus.AUTO_ACCEPTED.value,
            ConsensusStatus.ACCEPTED.value,
        ]
        return [
            item for item in session.consensus_items
            if item.status in accepted_statuses
        ]

    def _estimate_function_points(self, items: List[ExtractionConsensus]) -> int:
        """
        Estimate function points from extracted items.

        Uses IFPUG methodology when detailed data is available:
        - ILF (Internal Logical Files): 7-15 FP based on RETs × DETs
        - EIF (External Interface Files): 5-10 FP
        - EI (External Inputs): 3-6 FP based on FTRs × DETs
        - EO (External Outputs): 4-7 FP
        - EQ (External Queries): 3-6 FP

        Falls back to heuristic estimation when detailed data not available:
        - Epic: 100-200 FP (avg 150)
        - Feature: 20-50 FP (avg 35)
        - Story: 5-15 FP (avg 10)
        - Task: 2-5 FP (avg 3)
        """
        # Default heuristic estimates
        default_estimates = {
            ItemType.EPIC.value: 150,
            ItemType.FEATURE.value: 35,
            ItemType.STORY.value: 10,
            ItemType.TASK.value: 3,
        }

        # IFPUG component estimates (when we detect component type)
        ifpug_estimates = {
            "ilf": {"low": 7, "average": 10, "high": 15},
            "eif": {"low": 5, "average": 7, "high": 10},
            "ei": {"low": 3, "average": 4, "high": 6},
            "eo": {"low": 4, "average": 5, "high": 7},
            "eq": {"low": 3, "average": 4, "high": 6},
        }

        total_fp = 0
        for item in items:
            item_data = item.item_data or {}

            # Priority 1: Use LLM-synthesized FP estimate
            if "function_points" in item_data:
                total_fp += item_data["function_points"]
                continue

            # Priority 2: Use explicit estimated_fp
            if "estimated_fp" in item_data:
                total_fp += item_data["estimated_fp"]
                continue

            # Priority 3: Calculate using IFPUG if component type is known
            component_type = item_data.get("fp_component_type", "").lower()
            complexity = item_data.get("fp_complexity", "average").lower()

            if component_type in ifpug_estimates:
                fp_values = ifpug_estimates[component_type]
                total_fp += fp_values.get(complexity, fp_values["average"])
                continue

            # Priority 4: Infer from item characteristics
            title_lower = item.item_title.lower() if item.item_title else ""
            description_lower = (item.item_description or "").lower()

            # Detect data-related items (ILF/EIF)
            if any(kw in title_lower or kw in description_lower for kw in
                   ["database", "table", "entity", "model", "schema", "data store"]):
                # Assume average ILF
                total_fp += 10
                continue

            # Detect input forms (EI)
            if any(kw in title_lower or kw in description_lower for kw in
                   ["form", "input", "create", "add", "submit", "upload"]):
                total_fp += 4
                continue

            # Detect outputs/reports (EO)
            if any(kw in title_lower or kw in description_lower for kw in
                   ["report", "export", "generate", "output", "print", "pdf"]):
                total_fp += 5
                continue

            # Detect queries/searches (EQ)
            if any(kw in title_lower or kw in description_lower for kw in
                   ["search", "query", "find", "list", "view", "display"]):
                total_fp += 4
                continue

            # Priority 5: Fall back to default by item type
            total_fp += default_estimates.get(item.item_type, 5)

        return total_fp

    def _generate_synthesis_summary(
        self,
        session: ExtractionSession,
        final_epics: List[ExtractionConsensus],
        final_features: List[ExtractionConsensus],
        final_stories: List[ExtractionConsensus],
        final_tasks: List[ExtractionConsensus],
    ) -> Dict[str, Any]:
        """Generate a summary of the extraction synthesis."""
        # Get epic titles and their features
        epic_summary = []
        for epic in final_epics:
            epic_data = epic.item_data or {}
            epic_summary.append({
                "title": epic.item_title,
                "description": epic.item_description,
                "features": epic_data.get("features", []),
                "confidence": epic.confidence_score,
            })

        # Get high-confidence items
        high_confidence_items = [
            i for i in (final_epics + final_features + final_stories + final_tasks)
            if i.confidence_score >= 0.85
        ]

        # Get items that needed human review
        human_reviewed = [
            i for i in session.consensus_items
            if i.status in [ConsensusStatus.ACCEPTED.value, ConsensusStatus.REJECTED.value]
        ]

        # Conflict resolution summary
        conflicts_resolved = len([
            c for c in session.conflicts
            if c.status == ConflictStatus.RESOLVED.value
        ])

        return {
            "epics": [{"title": e.item_title, "confidence": e.confidence_score} for e in final_epics],
            "high_confidence_count": len(high_confidence_items),
            "human_reviewed_count": len(human_reviewed),
            "conflicts_resolved": conflicts_resolved,
            "tier": session.tier,
            "workflow_type": session.workflow_type,
            "source_path": session.source_path,
            "total_files": session.total_files,
        }

    async def _generate_traceability_matrix(
        self,
        session: ExtractionSession,
        epics: List[ExtractionConsensus],
        features: List[ExtractionConsensus],
        stories: List[ExtractionConsensus],
        tasks: List[ExtractionConsensus],
    ) -> Optional[Dict[str, Any]]:
        """
        Week 102-106: Generate traceability matrix from extracted items.

        Creates links between:
        - Epics → Features → Stories → Tasks
        - Stories → Acceptance Criteria
        - NFRs → Architecture Components
        """
        if not self._traceability_generator or not ArtifactType:
            return None

        try:
            # Build artifacts list
            artifacts = []

            # Add epics
            for epic in epics:
                artifacts.append({
                    "id": str(epic.id),
                    "type": ArtifactType.EPIC.value,
                    "title": epic.item_title,
                    "description": epic.item_description,
                })

            # Add features with links to epics
            for feature in features:
                feature_data = feature.item_data or {}
                artifacts.append({
                    "id": str(feature.id),
                    "type": ArtifactType.FEATURE.value,
                    "title": feature.item_title,
                    "description": feature.item_description,
                    "parent_id": feature_data.get("parent_epic_id"),
                })

            # Add stories with links to features
            for story in stories:
                story_data = story.item_data or {}
                artifacts.append({
                    "id": str(story.id),
                    "type": ArtifactType.USER_STORY.value,
                    "title": story.item_title,
                    "description": story.item_description,
                    "parent_id": story_data.get("parent_feature_id"),
                    "invest_score": story_data.get("invest_score"),
                })

            # Add tasks with links to stories
            for task in tasks:
                task_data = task.item_data or {}
                artifacts.append({
                    "id": str(task.id),
                    "type": ArtifactType.TASK.value,
                    "title": task.item_title,
                    "description": task.item_description,
                    "parent_id": task_data.get("parent_story_id"),
                })

            # Generate matrix
            matrix = self._traceability_generator.generate(artifacts)

            return {
                "total_artifacts": len(artifacts),
                "coverage_report": {
                    "epics_with_features": matrix.coverage.get("epic_to_feature", 0),
                    "features_with_stories": matrix.coverage.get("feature_to_story", 0),
                    "stories_with_tasks": matrix.coverage.get("story_to_task", 0),
                    "orphaned_items": matrix.coverage.get("orphaned", 0),
                },
                "links_count": len(matrix.links),
                "generated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.warning(f"Traceability matrix generation failed: {e}")
            return None

    async def run_full_extraction(self, session_id: UUID) -> Dict[str, Any]:
        """
        Run complete extraction pipeline (all 6 cycles - Week 99).

        Cycles:
        0. Static Analysis - Deterministic code analysis
        1. Independent Analysis - LLM analyses code
        2. Cross-Enrichment - LLMs review each other
        3. Conflict Detection - LLM conflicts + Static vs LLM conflicts
        4. Human Decision - Human review (for items below 72.5% confidence)
        5. Final Synthesis - Create final consensus output

        Note: Cycle 4 (human review) may pause the process if tier includes human review.
        """
        results = {}

        # Cycle 0: Static Analysis (Week 99)
        results["cycle_0"] = await self.run_cycle_0(session_id)

        # Cycle 1: Independent Analysis
        results["cycle_1"] = await self.run_cycle_1(session_id)

        # Cycle 2: Cross-Enrichment
        results["cycle_2"] = await self.run_cycle_2(session_id)

        # Cycle 3: Conflict Detection (includes Static vs LLM conflicts - Week 99)
        results["cycle_3"] = await self.run_cycle_3(session_id)

        # Week 99: Run Static vs LLM conflict detection
        static_llm_conflicts = await self._detect_static_llm_conflicts(session_id)
        if static_llm_conflicts:
            results["static_llm_conflicts"] = static_llm_conflicts

        # Check if waiting for human review
        session = await self.get_session(session_id)
        if session.status == ExtractionStatus.AWAITING_REVIEW.value:
            return {
                **results,
                "status": "awaiting_review",
                "message": "Extraction paused for human review. Call complete_human_review() when done.",
                "conflicts_requiring_review": static_llm_conflicts.get("conflicts_needing_review", 0) if static_llm_conflicts else 0,
            }

        # Cycle 4: Human Decision (skip if no human review)
        results["cycle_4"] = {"cycle": 4, "status": "skipped", "message": "No human review required for this tier"}

        # Cycle 5: Final Synthesis
        results["cycle_5"] = await self.run_cycle_5(session_id)

        return {
            **results,
            "status": "completed",
            "session_id": str(session_id),
        }

    async def _detect_static_llm_conflicts(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Week 99: Detect conflicts between static analysis and LLM results.

        Uses the 72.5% confidence threshold from ConflictDetectorService.
        """
        session = await self.get_session(session_id)
        if not session:
            return None

        # Get static analysis results
        static_result = self._static_results.get(session_id)
        if not static_result:
            logger.info(f"No static analysis results for session {session_id}")
            return None

        # Convert static results to format expected by ConflictDetector
        static_data = static_result.to_llm_context()

        # Collect LLM results from cycle 1
        llm_results = []
        for result in session.llm_results:
            if result.cycle == 1 and result.parsed_output:
                llm_results.append({
                    "provider": f"{result.llm_provider}/{result.llm_model}",
                    "analysis_type": result.analysis_type,
                    "epics": result.extracted_epics or [],
                    "features": result.extracted_features or [],
                    "stories": result.extracted_stories or [],
                    "tasks": result.extracted_tasks or [],
                })

        if not llm_results:
            logger.info(f"No LLM results for static conflict detection in session {session_id}")
            return None

        # Detect conflicts using ConflictDetector
        conflict_result = await self._conflict_detector.detect_conflicts(
            session_id=str(session_id),
            static_results=static_data,
            llm_results=llm_results,
        )

        # Update session status if conflicts need human review
        if conflict_result.conflicts_needing_review > 0:
            session.status = ExtractionStatus.AWAITING_REVIEW.value
            await self.db.commit()
            logger.info(
                f"Session {session_id} has {conflict_result.conflicts_needing_review} "
                f"static-LLM conflicts needing human review"
            )

        return {
            "total_conflicts": conflict_result.total_conflicts,
            "auto_resolved": conflict_result.auto_resolved,
            "conflicts_needing_review": conflict_result.conflicts_needing_review,
            "summary": conflict_result.summary,
        }

    # =========================================================================
    # CONFLICT RESOLUTION
    # =========================================================================

    async def resolve_conflict(
        self,
        conflict_id: UUID,
        choice: str,
        custom_resolution: Optional[Dict[str, Any]] = None,
        reasoning: Optional[str] = None,
        resolved_by: str = "human",
    ) -> ExtractionConflict:
        """Resolve a conflict with human decision."""
        result = await self.db.execute(
            select(ExtractionConflict).where(ExtractionConflict.id == conflict_id)
        )
        conflict = result.scalar_one_or_none()

        if not conflict:
            raise ValueError(f"Conflict {conflict_id} not found")

        conflict.human_choice = choice
        conflict.human_custom = custom_resolution
        conflict.human_reasoning = reasoning
        conflict.resolved_by = resolved_by
        conflict.resolved_at = datetime.utcnow()
        conflict.status = ConflictStatus.RESOLVED.value

        await self.db.commit()
        await self.db.refresh(conflict)

        return conflict

    async def decide_consensus(
        self,
        consensus_id: UUID,
        decision: str,  # "accept" or "reject"
        feedback: Optional[str] = None,
        decided_by: str = "human",
    ) -> ExtractionConsensus:
        """Make decision on a consensus item."""
        result = await self.db.execute(
            select(ExtractionConsensus).where(ExtractionConsensus.id == consensus_id)
        )
        consensus = result.scalar_one_or_none()

        if not consensus:
            raise ValueError(f"Consensus item {consensus_id} not found")

        consensus.human_decision = decision
        consensus.human_feedback = feedback
        consensus.decided_by = decided_by
        consensus.decided_at = datetime.utcnow()
        consensus.status = ConsensusStatus.ACCEPTED.value if decision == "accept" else ConsensusStatus.REJECTED.value

        await self.db.commit()
        await self.db.refresh(consensus)

        return consensus

    async def bulk_resolve_conflicts(
        self,
        session_id: UUID,
        resolutions: List[Dict[str, Any]],
        resolved_by: str = "human",
    ) -> Dict[str, Any]:
        """
        Bulk resolve multiple conflicts.

        Args:
            session_id: Session ID
            resolutions: List of {conflict_id, choice, reasoning}
            resolved_by: Who resolved the conflicts

        Returns:
            Summary of resolved conflicts
        """
        resolved = 0
        errors = []

        for resolution in resolutions:
            try:
                await self.resolve_conflict(
                    conflict_id=resolution["conflict_id"],
                    choice=resolution["choice"],
                    custom_resolution=resolution.get("custom_resolution"),
                    reasoning=resolution.get("reasoning"),
                    resolved_by=resolved_by,
                )
                resolved += 1
            except Exception as e:
                errors.append({
                    "conflict_id": str(resolution.get("conflict_id")),
                    "error": str(e),
                })

        return {
            "total_submitted": len(resolutions),
            "resolved": resolved,
            "errors": errors,
        }

    async def bulk_decide_consensus(
        self,
        session_id: UUID,
        decisions: List[Dict[str, Any]],
        decided_by: str = "human",
    ) -> Dict[str, Any]:
        """
        Bulk decide on multiple consensus items.

        Args:
            session_id: Session ID
            decisions: List of {consensus_id, decision, feedback}
            decided_by: Who made the decisions

        Returns:
            Summary of decisions made
        """
        accepted = 0
        rejected = 0
        errors = []

        for decision in decisions:
            try:
                result = await self.decide_consensus(
                    consensus_id=decision["consensus_id"],
                    decision=decision["decision"],
                    feedback=decision.get("feedback"),
                    decided_by=decided_by,
                )
                if result.status == ConsensusStatus.ACCEPTED.value:
                    accepted += 1
                else:
                    rejected += 1
            except Exception as e:
                errors.append({
                    "consensus_id": str(decision.get("consensus_id")),
                    "error": str(e),
                })

        return {
            "total_submitted": len(decisions),
            "accepted": accepted,
            "rejected": rejected,
            "errors": errors,
        }

    async def auto_resolve_llm_recommendations(
        self,
        session_id: UUID,
    ) -> Dict[str, Any]:
        """
        Auto-resolve conflicts using LLM recommendations.

        Useful for batch processing or lower-tier customers who don't
        want to manually review each conflict.
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        resolved = 0
        skipped = 0

        for conflict in session.conflicts:
            if conflict.status != ConflictStatus.PENDING.value:
                continue

            if conflict.llm_recommendation:
                conflict.human_choice = conflict.llm_recommendation
                conflict.human_reasoning = "Auto-resolved using LLM recommendation"
                conflict.resolved_by = "auto"
                conflict.resolved_at = datetime.utcnow()
                conflict.status = ConflictStatus.RESOLVED.value
                resolved += 1
            else:
                skipped += 1

        await self.db.commit()

        return {
            "resolved": resolved,
            "skipped": skipped,
            "message": f"Auto-resolved {resolved} conflicts using LLM recommendations",
        }

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics across all sessions."""
        # Total sessions by status
        result = await self.db.execute(select(ExtractionSession))
        sessions = list(result.scalars().all())

        by_status = {}
        by_tier = {}
        total_cost = 0.0
        total_revenue = 0.0

        for s in sessions:
            by_status[s.status] = by_status.get(s.status, 0) + 1
            by_tier[s.tier] = by_tier.get(s.tier, 0) + 1
            total_cost += s.actual_cost_usd or 0.0
            total_revenue += s.tier_price_usd or 0.0

        return {
            "total_sessions": len(sessions),
            "sessions_by_status": by_status,
            "sessions_by_tier": by_tier,
            "total_items_extracted": sum(
                (s.total_epics or 0) + (s.total_features or 0) +
                (s.total_stories or 0) + (s.total_tasks or 0)
                for s in sessions
            ),
            "total_cost_usd": total_cost,
            "total_revenue_usd": total_revenue,
            "margin_percentage": ((total_revenue - total_cost) / total_revenue * 100) if total_revenue > 0 else 0,
        }
