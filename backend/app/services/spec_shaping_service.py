"""
SpecShapingService - Implements the spec iteration loop from Agent OS

Week 59: Agent OS Integration
Pattern: Shape → Verify → Loop until quality gates pass

The service iterates on specifications until they meet quality standards:
1. Take initial description
2. Shape into structured spec (using Felix)
3. Verify against quality checks
4. If checks fail, reshape with feedback
5. Loop until approved or max iterations reached
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class SessionStatus(str, Enum):
    """Status of a spec shaping session."""
    DRAFT = "draft"
    SHAPING = "shaping"
    VERIFYING = "verifying"
    APPROVED = "approved"
    REJECTED = "rejected"
    MAX_ITERATIONS = "max_iterations"


class CheckCategory(str, Enum):
    """Categories of spec quality checks."""
    STRUCTURE = "structure"
    CONTENT = "content"
    FEASIBILITY = "feasibility"
    CLARITY = "clarity"
    COMPLETENESS = "completeness"


@dataclass
class VerificationResult:
    """Result of a single quality check."""
    check_name: str
    category: CheckCategory
    passed: bool
    score: float
    message: str
    suggestions: Optional[str] = None


@dataclass
class ShapingResult:
    """Result of a shaping iteration."""
    iteration_number: int
    input_spec: str
    output_spec: str
    verifications: List[VerificationResult]
    all_passed: bool
    agent_used: str
    tokens_used: int
    duration_ms: int


# Quality checks for specifications
SPEC_QUALITY_CHECKS = [
    {
        "name": "has_problem_statement",
        "category": CheckCategory.COMPLETENESS,
        "description": "Spec clearly states the problem being solved",
        "required_keywords": ["problem", "issue", "challenge", "need"],
    },
    {
        "name": "has_success_criteria",
        "category": CheckCategory.COMPLETENESS,
        "description": "Spec defines measurable success criteria",
        "required_keywords": ["success", "criteria", "measure", "kpi", "metric"],
    },
    {
        "name": "has_scope_boundaries",
        "category": CheckCategory.STRUCTURE,
        "description": "Spec defines what is in and out of scope",
        "required_keywords": ["scope", "in scope", "out of scope", "boundary"],
    },
    {
        "name": "has_user_context",
        "category": CheckCategory.CONTENT,
        "description": "Spec identifies target users or stakeholders",
        "required_keywords": ["user", "stakeholder", "audience", "persona"],
    },
    {
        "name": "has_technical_constraints",
        "category": CheckCategory.FEASIBILITY,
        "description": "Spec mentions technical constraints or requirements",
        "required_keywords": ["constraint", "requirement", "limitation", "dependency"],
    },
    {
        "name": "is_actionable",
        "category": CheckCategory.CLARITY,
        "description": "Spec contains actionable items or next steps",
        "required_keywords": ["implement", "create", "build", "develop", "action"],
    },
    {
        "name": "sufficient_length",
        "category": CheckCategory.COMPLETENESS,
        "description": "Spec has sufficient detail (min 200 words)",
        "min_words": 200,
    },
]


class SpecShapingService:
    """
    Service for iteratively shaping specifications until they pass quality gates.

    Implements the Agent OS "spec-shaper" pattern:
    - Shape: Transform raw description into structured spec
    - Verify: Check against quality gates
    - Loop: Iterate with feedback until approved
    """

    def __init__(self, db: AsyncSession, ollama_service=None):
        """
        Initialize the spec shaping service.

        Args:
            db: Database session for persistence
            ollama_service: Optional Ollama service for LLM calls
        """
        self.db = db
        self.ollama = ollama_service
        self.max_iterations = 5

    async def start_session(
        self,
        description: str,
        workflow_type: str,
        project_id: Optional[int] = None,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Start a new spec shaping session.

        Args:
            description: Initial description to shape into a spec
            workflow_type: Type of workflow (NEW_FEATURE, BUG, etc.)
            project_id: Optional project ID to link to
            max_iterations: Maximum iterations before giving up

        Returns:
            Dict with session ID and initial status
        """
        from app.models.spec_shaping import SpecShapingSession

        session = SpecShapingSession(
            project_id=project_id,
            workflow_type=workflow_type.upper(),
            initial_description=description,
            current_spec=description,
            status=SessionStatus.DRAFT,
            max_iterations=max_iterations,
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Started spec shaping session {session.id} for {workflow_type}")

        return {
            "session_id": session.id,
            "status": session.status,
            "workflow_type": session.workflow_type,
            "message": "Session created. Call /iterate to start shaping.",
        }

    async def iterate(self, session_id: int) -> Dict[str, Any]:
        """
        Perform one shape-verify iteration.

        Args:
            session_id: ID of the session to iterate

        Returns:
            Dict with iteration results and updated status
        """
        from app.models.spec_shaping import SpecShapingSession, SpecIteration, SpecVerification

        # Get session
        result = await self.db.execute(
            select(SpecShapingSession)
            .where(SpecShapingSession.id == session_id)
            .options(selectinload(SpecShapingSession.iterations))
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        if session.status in [SessionStatus.APPROVED, SessionStatus.MAX_ITERATIONS]:
            return {
                "session_id": session_id,
                "status": session.status,
                "message": f"Session already completed with status: {session.status}",
            }

        if session.iteration_count >= session.max_iterations:
            session.status = SessionStatus.MAX_ITERATIONS
            await self.db.commit()
            return {
                "session_id": session_id,
                "status": session.status,
                "message": "Maximum iterations reached",
            }

        # Increment iteration count
        session.iteration_count += 1
        iteration_num = session.iteration_count

        # Phase 1: Shape the spec
        session.status = SessionStatus.SHAPING
        await self.db.commit()

        start_time = datetime.now()
        shaped_spec = await self._shape_spec(
            session.current_spec,
            session.workflow_type,
            iteration_num
        )
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Create iteration record
        iteration = SpecIteration(
            session_id=session_id,
            iteration_number=iteration_num,
            input_spec=session.current_spec,
            output_spec=shaped_spec,
            agent_used="Felix",
            llm_model="qwen2.5-coder:7b",
            tokens_used=len(shaped_spec.split()),  # Rough estimate
            duration_ms=duration_ms,
        )
        self.db.add(iteration)
        await self.db.commit()
        await self.db.refresh(iteration)

        # Phase 2: Verify the spec
        session.status = SessionStatus.VERIFYING
        await self.db.commit()

        verifications = self._verify_spec(shaped_spec)

        # Store verification results
        for v in verifications:
            verification = SpecVerification(
                iteration_id=iteration.id,
                check_name=v.check_name,
                check_category=v.category.value,
                passed=v.passed,
                score=v.score,
                message=v.message,
                suggestions=v.suggestions,
            )
            self.db.add(verification)

        # Check if all passed
        all_passed = all(v.passed for v in verifications)
        passed_count = sum(1 for v in verifications if v.passed)

        if all_passed:
            session.status = SessionStatus.APPROVED
            session.completed_at = datetime.now()
        else:
            session.status = SessionStatus.DRAFT  # Ready for next iteration

        session.current_spec = shaped_spec
        await self.db.commit()

        logger.info(
            f"Session {session_id} iteration {iteration_num}: "
            f"{passed_count}/{len(verifications)} checks passed"
        )

        return {
            "session_id": session_id,
            "iteration_number": iteration_num,
            "status": session.status,
            "checks_passed": passed_count,
            "checks_total": len(verifications),
            "all_passed": all_passed,
            "verifications": [
                {
                    "check": v.check_name,
                    "category": v.category.value,
                    "passed": v.passed,
                    "score": v.score,
                    "message": v.message,
                    "suggestions": v.suggestions,
                }
                for v in verifications
            ],
            "current_spec_preview": shaped_spec[:500] + "..." if len(shaped_spec) > 500 else shaped_spec,
        }

    async def _shape_spec(
        self,
        current_spec: str,
        workflow_type: str,
        iteration: int
    ) -> str:
        """
        Shape the spec using LLM.

        For now, uses a template-based approach. When Ollama is available,
        this will call Felix agent for intelligent shaping.
        """
        # If Ollama is available, use it
        if self.ollama:
            try:
                prompt = self._build_shaping_prompt(current_spec, workflow_type, iteration)
                response = await self.ollama.generate(
                    model="qwen2.5-coder:7b",
                    prompt=prompt,
                )
                return response.get("response", current_spec)
            except Exception as e:
                logger.warning(f"Ollama shaping failed: {e}, using template")

        # Fallback: Template-based shaping
        return self._template_shape(current_spec, workflow_type, iteration)

    def _build_shaping_prompt(self, spec: str, workflow_type: str, iteration: int) -> str:
        """Build the prompt for LLM-based shaping."""
        return f"""You are Felix, a specification architect. Shape this specification for a {workflow_type} workflow.

Iteration {iteration}: Improve the specification to pass all quality checks.

Current specification:
{spec}

Required sections:
1. Problem Statement - What problem does this solve?
2. Success Criteria - How do we measure success?
3. Scope - What is in/out of scope?
4. Users/Stakeholders - Who is affected?
5. Technical Constraints - What limitations exist?
6. Action Items - What needs to be done?

Output the improved specification in markdown format. Be specific and actionable."""

    def _template_shape(self, spec: str, workflow_type: str, iteration: int) -> str:
        """Template-based shaping when LLM is unavailable."""
        # Check what's missing
        has_problem = any(kw in spec.lower() for kw in ["problem", "issue", "challenge"])
        has_success = any(kw in spec.lower() for kw in ["success", "criteria", "measure"])
        has_scope = any(kw in spec.lower() for kw in ["scope", "boundary"])
        has_users = any(kw in spec.lower() for kw in ["user", "stakeholder"])
        has_constraints = any(kw in spec.lower() for kw in ["constraint", "requirement"])
        has_actions = any(kw in spec.lower() for kw in ["implement", "create", "build"])

        # Build improved spec
        sections = [f"# {workflow_type} Specification\n"]
        sections.append(f"## Original Description\n{spec}\n")

        if not has_problem:
            sections.append("## Problem Statement\n*[TODO: Describe the problem being solved]*\n")
        if not has_success:
            sections.append("## Success Criteria\n*[TODO: Define measurable success criteria]*\n")
        if not has_scope:
            sections.append("## Scope\n### In Scope\n- *[TODO]*\n\n### Out of Scope\n- *[TODO]*\n")
        if not has_users:
            sections.append("## Users & Stakeholders\n*[TODO: Identify target users]*\n")
        if not has_constraints:
            sections.append("## Technical Constraints\n*[TODO: List constraints and requirements]*\n")
        if not has_actions:
            sections.append("## Action Items\n- [ ] *[TODO: Define actionable next steps]*\n")

        return "\n".join(sections)

    def _verify_spec(self, spec: str) -> List[VerificationResult]:
        """
        Verify a spec against all quality checks.

        Args:
            spec: The specification to verify

        Returns:
            List of verification results
        """
        results = []
        spec_lower = spec.lower()
        word_count = len(spec.split())

        for check in SPEC_QUALITY_CHECKS:
            name = check["name"]
            category = check["category"]

            # Check by keywords
            if "required_keywords" in check:
                keywords = check["required_keywords"]
                found = any(kw in spec_lower for kw in keywords)
                score = 1.0 if found else 0.0
                passed = found
                message = f"Found required keywords" if found else f"Missing keywords: {keywords}"
                suggestions = f"Add a section addressing: {', '.join(keywords)}" if not found else None

            # Check by minimum words
            elif "min_words" in check:
                min_words = check["min_words"]
                passed = word_count >= min_words
                score = min(1.0, word_count / min_words)
                message = f"Word count: {word_count}/{min_words}"
                suggestions = f"Add more detail (need {min_words - word_count} more words)" if not passed else None

            else:
                passed = True
                score = 1.0
                message = "Check passed"
                suggestions = None

            results.append(VerificationResult(
                check_name=name,
                category=category,
                passed=passed,
                score=score,
                message=message,
                suggestions=suggestions,
            ))

        return results

    async def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get session details including all iterations."""
        from app.models.spec_shaping import SpecShapingSession

        result = await self.db.execute(
            select(SpecShapingSession)
            .where(SpecShapingSession.id == session_id)
            .options(
                selectinload(SpecShapingSession.iterations)
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        return {
            "id": session.id,
            "project_id": session.project_id,
            "workflow_type": session.workflow_type,
            "status": session.status,
            "iteration_count": session.iteration_count,
            "max_iterations": session.max_iterations,
            "initial_description": session.initial_description,
            "current_spec": session.current_spec,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "iterations": [
                {
                    "number": it.iteration_number,
                    "agent": it.agent_used,
                    "tokens": it.tokens_used,
                    "duration_ms": it.duration_ms,
                }
                for it in session.iterations
            ],
        }

    async def list_sessions(
        self,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """List spec shaping sessions."""
        from app.models.spec_shaping import SpecShapingSession

        query = select(SpecShapingSession).order_by(SpecShapingSession.created_at.desc()).limit(limit)

        if status:
            query = query.where(SpecShapingSession.status == status)

        result = await self.db.execute(query)
        sessions = result.scalars().all()

        return [
            {
                "id": s.id,
                "workflow_type": s.workflow_type,
                "status": s.status,
                "iteration_count": s.iteration_count,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ]
