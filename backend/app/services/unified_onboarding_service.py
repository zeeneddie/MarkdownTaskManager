"""
Unified Onboarding Service

Orchestrator for the 4th Brown Paper workflow. Calls the 3 existing workflows
in sequence and adds a Reconciliation step (step 8).

Steps:
1. CODE SCAN         - BrownPaperService.analyze_application()
2. 8 VRAGEN          - Validate MarQed session has 8 answers
3. MIGUEL'S ANALYSE  - MarQedBrownPaperWorkflow.run_migration_analysis()
4. PETER'S SPEC      - MarQedBrownPaperWorkflow.generate_specification()
5. FELIX BOTTOM-UP   - BusinessDomainExtractor + StoryGenerator
6. FELIX TOP-DOWN    - MarQedBrownPaperWorkflow.generate_tasks()
7. ENHANCED 6-FASE   - BrownPaperService.run_enhanced_analysis()
8. RECONCILIATION    - ReconciliationService.reconcile()
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.unified_onboarding import UnifiedOnboardingSession
from app.models.brown_paper import (
    BrownPaperSession as BrownPaperSessionDB,
    BrownPaperConstitution as BrownPaperConstitutionDB,
)
from app.models.marqed_session import MarQedSession as MarQedSessionDB
from app.services.brown_paper_service import BrownPaperService, MarQedBrownPaperWorkflow
from app.services.business_domain_extractor_service import (
    BusinessDomainExtractorService,
    get_business_domain_extractor,
)
from app.services.business_driven_story_generator_service import (
    BusinessDrivenStoryGeneratorService,
    get_business_driven_story_generator,
)
from app.services.reconciliation_service import ReconciliationService
from app.models.brown_paper_enhanced import (
    EnhancedAnalysisRequest,
    EnhancedAnalysisTier,
)

logger = logging.getLogger(__name__)

# Step metadata for status endpoint
STEP_NAMES = {
    1: "Code Scan",
    2: "8 Vragen Validatie",
    3: "Miguel's Analyse",
    4: "Peter's Specificatie",
    5: "Felix Bottom-Up",
    6: "Felix Top-Down",
    7: "Enhanced 6-Fase",
    8: "Reconciliation",
}


class UnifiedOnboardingService:
    """
    Orchestrator for the Unified Onboarding Workflow.
    Calls existing services in order and stores results per step.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._brown_paper_service = BrownPaperService()
        self._marqed_workflow = MarQedBrownPaperWorkflow()

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    async def start(
        self,
        marqed_session_id: str,
        project_path: Optional[str] = None,
    ) -> UnifiedOnboardingSession:
        """Start unified workflow from an existing MarQed session."""
        # Validate MarQed session exists
        marqed_session = await self._marqed_workflow.get_session(marqed_session_id)
        if not marqed_session:
            raise ValueError(f"MarQed session not found: {marqed_session_id}")

        session = UnifiedOnboardingSession(
            id=uuid.uuid4(),
            marqed_session_id=marqed_session_id,
            project_name=marqed_session.project_name,
            project_path=project_path or marqed_session.project_path,
            status="initialized",
            current_step=0,
            tier="ENTERPRISE",
            step_timings={},
        )
        self.db.add(session)
        await self.db.flush()

        logger.info(f"Started unified onboarding session {session.id} for project '{session.project_name}'")
        return session

    async def get_session(self, unified_id: uuid.UUID) -> Optional[UnifiedOnboardingSession]:
        """Get a unified session by ID."""
        result = await self.db.execute(
            select(UnifiedOnboardingSession).where(UnifiedOnboardingSession.id == unified_id)
        )
        return result.scalar_one_or_none()

    async def get_status(self, unified_id: uuid.UUID) -> Dict[str, Any]:
        """Get detailed progress per step."""
        session = await self.get_session(unified_id)
        if not session:
            raise ValueError(f"Unified session not found: {unified_id}")

        timings = session.step_timings or {}
        steps = []
        for step_num in range(1, 9):
            step_key = f"step_{step_num}_ms"
            if step_num < session.current_step:
                step_status = "completed"
            elif step_num == session.current_step and session.status.endswith("_running"):
                step_status = "running"
            elif step_num == session.current_step and session.status.endswith("_done"):
                step_status = "completed"
            else:
                step_status = "pending"

            steps.append({
                "step": step_num,
                "name": STEP_NAMES.get(step_num, f"Step {step_num}"),
                "status": step_status,
                "duration_ms": timings.get(step_key),
            })

        return {
            "unified_session_id": str(session.id),
            "project_name": session.project_name,
            "status": session.status,
            "current_step": session.current_step,
            "total_steps": 8,
            "steps": steps,
            "total_duration_ms": session.total_duration_ms,
            "error_message": session.error_message,
        }

    # ========================================================================
    # STEP EXECUTION
    # ========================================================================

    async def execute_step(self, unified_id: uuid.UUID, step: int) -> Dict:
        """Execute a single step (1-8). Steps are independently callable."""
        if step < 1 or step > 8:
            raise ValueError(f"Invalid step: {step}. Must be 1-8.")

        session = await self.get_session(unified_id)
        if not session:
            raise ValueError(f"Unified session not found: {unified_id}")

        step_methods = {
            1: self._step_1_code_scan,
            2: self._step_2_validate_questions,
            3: self._step_3_migration_analysis,
            4: self._step_4_specification,
            5: self._step_5_epics_bottom_up,
            6: self._step_6_epics_top_down,
            7: self._step_7_enhanced_analysis,
            8: self._step_8_reconciliation,
        }

        method = step_methods[step]
        start_time = time.time()

        await self._update_status(session, f"step_{step}_running", step)

        try:
            result = await method(session)
            duration_ms = int((time.time() - start_time) * 1000)

            await self._save_step_result(session, step, result)
            await self._save_step_timing(session, step, duration_ms)
            await self._update_status(session, f"step_{step}_done", step)

            return {
                "step": step,
                "name": STEP_NAMES.get(step, f"Step {step}"),
                "status": "completed",
                "duration_ms": duration_ms,
                "result_summary": self._summarize_result(step, result),
            }

        except Exception as e:
            logger.error(f"Step {step} failed for session {unified_id}: {e}", exc_info=True)
            session.error_message = f"Step {step} failed: {str(e)}"
            session.status = "failed"
            await self.db.flush()
            raise

    async def execute_all(
        self,
        unified_id: uuid.UUID,
        tier: str = "ENTERPRISE",
    ) -> Dict:
        """Execute all 8 steps sequentially."""
        session = await self.get_session(unified_id)
        if not session:
            raise ValueError(f"Unified session not found: {unified_id}")

        session.tier = tier
        total_start = time.time()
        steps_completed = 0

        try:
            for step in range(1, 9):
                await self.execute_step(unified_id, step)
                steps_completed = step
                # Refresh session after each step (step may have modified it)
                session = await self.get_session(unified_id)

            total_duration_ms = int((time.time() - total_start) * 1000)
            session.total_duration_ms = total_duration_ms
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            await self.db.flush()

            # Get reconciliation summary
            recon_summary = {}
            if session.step_8_result:
                recon_summary = {
                    k: session.step_8_result.get(k)
                    for k in [
                        "blind_spots", "phantom_features", "confidence_heatmap",
                        "fp_deltas", "domain_disputes", "unified_epics_count",
                        "unified_features_count", "unified_stories_count",
                    ]
                    if k in (session.step_8_result or {})
                }

            return {
                "unified_session_id": str(unified_id),
                "status": "completed",
                "steps_completed": steps_completed,
                "total_duration_ms": total_duration_ms,
                "reconciliation_summary": recon_summary,
            }

        except Exception as e:
            total_duration_ms = int((time.time() - total_start) * 1000)
            session.total_duration_ms = total_duration_ms
            await self.db.flush()
            raise

    # ========================================================================
    # INDIVIDUAL STEPS
    # ========================================================================

    async def _step_1_code_scan(self, session: UnifiedOnboardingSession) -> Dict:
        """Step 1: Run code analysis via BrownPaperService."""
        project_path = session.project_path
        if not project_path:
            return {
                "status": "skipped",
                "reason": "No project_path provided",
                "modules": [],
                "domains": [],
                "patterns": [],
            }

        # Start a BrownPaper session for code analysis
        bp_session = await self._brown_paper_service.start_session(
            application_id=1000  # Default application ID for unified onboarding
        )
        session.brown_paper_session_id = bp_session.id

        # Run analysis
        analysis = await self._brown_paper_service.analyze_application(str(bp_session.id))

        result = {
            "status": "completed",
            "brown_paper_session_id": str(bp_session.id),
            "modules_count": len(analysis.modules or []),
            "domains_count": len(analysis.domains or []),
            "patterns": analysis.primary_patterns or [],
            "modules": analysis.modules or [],
            "domains": analysis.domains or [],
        }
        return result

    async def _step_2_validate_questions(self, session: UnifiedOnboardingSession) -> Dict:
        """Step 2: Validate that MarQed session has 8 answered questions."""
        marqed_session = await self._marqed_workflow.get_session(session.marqed_session_id)
        if not marqed_session:
            raise ValueError(f"MarQed session not found: {session.marqed_session_id}")

        answered = len(marqed_session.answers)
        answers_valid = answered >= 8

        answer_summaries = {}
        for q_num, answer in marqed_session.answers.items():
            answer_summaries[str(q_num)] = {
                "answered": True,
                "answer_length": len(answer.answer) if hasattr(answer, 'answer') else 0,
            }

        return {
            "status": "completed" if answers_valid else "incomplete",
            "total_questions": 8,
            "questions_answered": answered,
            "all_valid": answers_valid,
            "answer_summaries": answer_summaries,
            "session_status": marqed_session.status,
        }

    async def _step_3_migration_analysis(self, session: UnifiedOnboardingSession) -> Dict:
        """Step 3: Run Miguel's migration analysis, enriched with code scan results."""
        marqed_session = await self._marqed_workflow.get_session(session.marqed_session_id)
        if not marqed_session:
            raise ValueError(f"MarQed session not found: {session.marqed_session_id}")

        # Ensure session is in correct state for analysis
        if marqed_session.status not in ["analyzing", "questions"]:
            # Try to advance the status
            marqed_session.status = "analyzing"

        analysis = await self._marqed_workflow.run_migration_analysis(session.marqed_session_id)

        # Enrich with code scan data if available
        enrichment = {}
        if session.step_1_result and session.step_1_result.get("status") == "completed":
            enrichment = {
                "code_scan_modules_count": session.step_1_result.get("modules_count", 0),
                "code_scan_domains_count": session.step_1_result.get("domains_count", 0),
                "code_scan_patterns": session.step_1_result.get("patterns", []),
            }

        result = {
            "status": "completed",
            "complexity": analysis.complexity if hasattr(analysis, 'complexity') else None,
            "risk_register": analysis.risk_register if hasattr(analysis, 'risk_register') else [],
            "recommended_phases": analysis.recommended_phases if hasattr(analysis, 'recommended_phases') else [],
            "go_no_go_checkpoints": analysis.go_no_go_checkpoints if hasattr(analysis, 'go_no_go_checkpoints') else [],
            "technical_spikes": analysis.technical_spikes if hasattr(analysis, 'technical_spikes') else [],
            "enrichment": enrichment,
        }
        return result

    async def _step_4_specification(self, session: UnifiedOnboardingSession) -> Dict:
        """Step 4: Generate Peter's specification."""
        marqed_session = await self._marqed_workflow.get_session(session.marqed_session_id)
        if not marqed_session:
            raise ValueError(f"MarQed session not found: {session.marqed_session_id}")

        # Ensure session is in correct state
        if marqed_session.status not in ["generating"]:
            marqed_session.status = "generating"

        specification = await self._marqed_workflow.generate_specification(session.marqed_session_id)

        return {
            "status": "completed",
            "specification": specification,
        }

    async def _step_5_epics_bottom_up(self, session: UnifiedOnboardingSession) -> Dict:
        """Step 5: Generate epics bottom-up using BusinessDomainExtractor + StoryGenerator."""
        # Get code scan modules from step 1
        step_1 = session.step_1_result or {}
        modules = step_1.get("modules", [])
        domains = step_1.get("domains", [])

        if not modules:
            return {
                "status": "skipped",
                "reason": "No modules available from step 1 code scan",
                "epics": [],
                "features": [],
                "stories": [],
            }

        # Extract domains from code
        extractor = get_business_domain_extractor()
        domain_result = await extractor.extract_domains(
            modules=modules,
            dependencies=[],  # Dependencies from code scan if available
            scan_path=session.project_path,
        )

        # Generate stories from domains
        generator = get_business_driven_story_generator()
        story_result = await generator.generate_stories(
            domain_result=domain_result,
            code_analysis=step_1,
        )

        # Convert to epic dicts
        epics = []
        for epic in story_result.epics:
            epic_dict = epic if isinstance(epic, dict) else {
                "name": getattr(epic, "name", str(epic)),
                "description": getattr(epic, "description", ""),
                "features": getattr(epic, "features", []),
                "source_domain": getattr(epic, "source_domain", getattr(epic, "domain_name", "")),
                "source_modules": getattr(epic, "source_modules", getattr(epic, "modules", [])),
                "function_points": getattr(epic, "function_points", getattr(epic, "estimated_fp", 0)),
                "story_points": getattr(epic, "story_points", getattr(epic, "estimated_sp", 0)),
                "complexity": getattr(epic, "complexity", "medium"),
                "priority": getattr(epic, "priority", 3),
            }
            epics.append(epic_dict)

        return {
            "status": "completed",
            "extraction_method": "business_domain_extraction",
            "domains_found": len(domain_result.domains),
            "epics": epics,
            "total_epics": len(epics),
            "total_features": story_result.total_features if hasattr(story_result, 'total_features') else 0,
            "total_stories": story_result.total_stories if hasattr(story_result, 'total_stories') else 0,
            "total_story_points": story_result.total_story_points if hasattr(story_result, 'total_story_points') else 0,
        }

    async def _step_6_epics_top_down(self, session: UnifiedOnboardingSession) -> Dict:
        """Step 6: Generate epics top-down via MarQed workflow."""
        marqed_session = await self._marqed_workflow.get_session(session.marqed_session_id)
        if not marqed_session:
            raise ValueError(f"MarQed session not found: {session.marqed_session_id}")

        tasks_result = await self._marqed_workflow.generate_tasks(session.marqed_session_id)

        # Extract epics from tasks result
        epics = tasks_result.get("epics", [])

        return {
            "status": "completed",
            "extraction_method": "marqed_top_down",
            "epics": epics,
            "total_epics": len(epics),
            "total_features": tasks_result.get("total_features", 0),
            "total_stories": tasks_result.get("total_stories", 0),
            "total_story_points": tasks_result.get("total_story_points", 0),
            "summary": tasks_result.get("summary", {}),
        }

    async def _step_7_enhanced_analysis(self, session: UnifiedOnboardingSession) -> Dict:
        """Step 7: Run enhanced 6-phase analysis."""
        tier_map = {
            "ENTERPRISE": EnhancedAnalysisTier.PREMIUM,
            "PREMIUM": EnhancedAnalysisTier.PREMIUM,
            "PROFESSIONAL": EnhancedAnalysisTier.PROFESSIONAL,
            "STANDARD": EnhancedAnalysisTier.STANDARD,
            "BASIC": EnhancedAnalysisTier.BASIC,
            "FREE": EnhancedAnalysisTier.FREE,
        }
        tier = tier_map.get(session.tier or "ENTERPRISE", EnhancedAnalysisTier.PREMIUM)

        request = EnhancedAnalysisRequest(tier=tier)

        try:
            enhanced_result = await self._brown_paper_service.run_enhanced_analysis(
                session_id=session.marqed_session_id,
                request=request,
                db=self.db,
            )

            # Extract epics from enhanced result
            epics = []
            if hasattr(enhanced_result, 'epics'):
                epics = enhanced_result.epics if isinstance(enhanced_result.epics, list) else []
            elif isinstance(enhanced_result, dict):
                epics = enhanced_result.get("epics", [])

            result_dict = enhanced_result.to_dict() if hasattr(enhanced_result, 'to_dict') else (
                enhanced_result if isinstance(enhanced_result, dict) else {"raw": str(enhanced_result)}
            )
            result_dict["epics"] = epics
            result_dict["status"] = "completed"

            return result_dict

        except Exception as e:
            logger.warning(f"Enhanced analysis failed (non-fatal): {e}")
            return {
                "status": "partial",
                "error": str(e),
                "epics": [],
            }

    async def _step_8_reconciliation(self, session: UnifiedOnboardingSession) -> Dict:
        """Step 8: Reconcile the 3 epic sets and save unified result."""
        # Extract epics from steps 5, 6, 7
        epics_bottom_up = (session.step_5_result or {}).get("epics", [])
        epics_top_down = (session.step_6_result or {}).get("epics", [])
        epics_enhanced = (session.step_7_result or {}).get("epics", [])

        # Extract FP data
        fp_bottom_up = {}
        for e in epics_bottom_up:
            name = e.get("name", "")
            fp = e.get("function_points", e.get("estimated_fp"))
            if name and fp:
                fp_bottom_up[name] = fp

        fp_top_down = {}
        for e in epics_top_down:
            name = e.get("name", e.get("title", ""))
            fp = e.get("function_points", e.get("estimated_fp"))
            if name and fp:
                fp_top_down[name] = fp

        # Extract domain data
        domains_code = (session.step_1_result or {}).get("domains", [])
        # Business domains come from answers / specification
        domains_business = []
        spec = (session.step_4_result or {}).get("specification", {})
        if isinstance(spec, dict) and spec.get("scope", {}).get("domains"):
            domains_business = spec["scope"]["domains"]

        # Run reconciliation
        recon_service = ReconciliationService(self.db)
        recon_result = await recon_service.reconcile(
            epics_bottom_up=epics_bottom_up,
            epics_top_down=epics_top_down,
            epics_enhanced=epics_enhanced,
            fp_bottom_up=fp_bottom_up,
            fp_top_down=fp_top_down,
            domains_code=domains_code,
            domains_business=domains_business,
        )

        # Create a constitution for the unified epics
        constitution = BrownPaperConstitutionDB(
            id=uuid.uuid4(),
            session_id=session.brown_paper_session_id or uuid.uuid4(),
            status="approved",
            content_json={
                "source": "UnifiedOnboardingWorkflow",
                "unified_session_id": str(session.id),
                "marqed_session_id": session.marqed_session_id,
            },
            generated_by="UnifiedOnboardingWorkflow",
        )
        self.db.add(constitution)
        await self.db.flush()

        # Save unified epics to brown_paper_epics
        saved_epics = await recon_service.save_unified_epics_to_db(
            unified_epics=recon_result.unified_epics,
            constitution_id=constitution.id,
            unified_session_id=session.id,
        )

        # Update session with constitution reference
        session.unified_constitution_id = constitution.id

        # Build result dict
        result = recon_result.to_dict()
        result["status"] = "completed"
        result["constitution_id"] = str(constitution.id)
        result["epics_saved"] = len(saved_epics)

        return result

    # ========================================================================
    # HELPERS
    # ========================================================================

    async def _save_step_result(self, session: UnifiedOnboardingSession, step: int, result: Dict):
        """Save step result to the appropriate step_N_result column."""
        col_name = f"step_{step}_result"
        setattr(session, col_name, result)
        await self.db.flush()

    async def _save_step_timing(self, session: UnifiedOnboardingSession, step: int, duration_ms: int):
        """Save step timing."""
        timings = dict(session.step_timings or {})
        timings[f"step_{step}_ms"] = duration_ms
        session.step_timings = timings
        await self.db.flush()

    async def _update_status(self, session: UnifiedOnboardingSession, status: str, step: int = None):
        """Update status and current_step."""
        session.status = status
        if step is not None:
            session.current_step = step
        session.updated_at = datetime.utcnow()
        await self.db.flush()

    def _summarize_result(self, step: int, result: Dict) -> Dict:
        """Create a brief summary of a step result for the API response."""
        summary = {"status": result.get("status", "unknown")}

        if step == 1:
            summary["modules_count"] = result.get("modules_count", 0)
            summary["domains_count"] = result.get("domains_count", 0)
        elif step == 2:
            summary["questions_answered"] = result.get("questions_answered", 0)
            summary["all_valid"] = result.get("all_valid", False)
        elif step == 3:
            summary["complexity"] = result.get("complexity")
            summary["risks_count"] = len(result.get("risk_register", []))
        elif step == 4:
            summary["has_specification"] = "specification" in result
        elif step == 5:
            summary["total_epics"] = result.get("total_epics", 0)
            summary["total_stories"] = result.get("total_stories", 0)
        elif step == 6:
            summary["total_epics"] = result.get("total_epics", 0)
            summary["total_stories"] = result.get("total_stories", 0)
        elif step == 7:
            summary["total_epics"] = len(result.get("epics", []))
        elif step == 8:
            summary["unified_epics_count"] = result.get("unified_epics_count", 0)
            summary["blind_spots_count"] = len(result.get("blind_spots", []))
            summary["phantom_features_count"] = len(result.get("phantom_features", []))
            summary["epics_saved"] = result.get("epics_saved", 0)

        return summary
