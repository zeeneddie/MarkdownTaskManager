"""
Specification Review Service - Option B+ Implementation

Two-agent adversarial review:
1. Felix generates specification
2. Quinn (QA) reviews and suggests improvements
3. Felix processes suggestions OR escalates to human if >3 critical issues

This avoids circular reasoning and is faster than full LLM Council.

Now with ProjectProfile support for dynamic agent configuration!
"""

import re
import asyncio
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.green_paper import Specification
from app.models.project_profile import (
    ProjectProfile,
    ProjectSize,
    FocusArea,
    StrictnessLevel,
    AgentConfig,
    get_preset_profile,
    KLAVERJAS_PROFILE
)

# Week 143: Vector DB Integration for context-aware reviews
import logging
logger = logging.getLogger(__name__)

try:
    from app.services.chroma_service import ChromaService
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaService not available - Vector DB context disabled")


class SuggestionType(str, Enum):
    ADD = "add"          # Add missing element
    REMOVE = "remove"    # Remove incorrect/unnecessary element
    CHANGE = "change"    # Modify existing element


class SuggestionPriority(str, Enum):
    CRITICAL = "critical"  # Must fix before approval
    HIGH = "high"          # Should fix
    MEDIUM = "medium"      # Nice to have
    LOW = "low"            # Minor improvement


class SuggestionStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass
class ReviewSuggestion:
    """Single review suggestion from Quinn."""
    id: str
    type: SuggestionType
    priority: SuggestionPriority
    section: str              # Which section of spec (e.g., "architecture", "data_model")
    description: str          # What to change
    reasoning: str            # Why this change is needed
    status: SuggestionStatus = SuggestionStatus.PENDING
    felix_response: Optional[str] = None  # Felix's decision reasoning


@dataclass
class ReviewResult:
    """Complete review result."""
    specification_id: UUID
    suggestions: List[ReviewSuggestion]
    overall_quality_score: float  # 0-10
    requires_human_review: bool
    escalation_reason: Optional[str]
    reviewed_at: datetime
    review_duration_seconds: float


@dataclass
class ProcessedResult:
    """Result after Felix processes suggestions."""
    specification_id: UUID
    accepted_count: int
    rejected_count: int
    updated_content: Optional[str]  # New spec content if changes made
    needs_human_decision: List[ReviewSuggestion]  # Suggestions Felix couldn't decide
    processed_at: datetime


class SpecReviewService:
    """
    Two-agent specification review service.

    Flow:
    1. Quinn reviews spec → generates suggestions
    2. Felix evaluates each suggestion → accept/reject
    3. If >3 critical issues OR Felix unsure → escalate to human

    Now with ProjectProfile support!
    Thresholds and strictness are dynamically configured based on project size and focus areas.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        ollama_base_url: str = "http://localhost:11434",
        project_profile: Optional[ProjectProfile] = None,
        project_id: int = 1000  # Week 143: Default to HCI-CRS project for Vector DB
    ):
        self.db = db_session
        self.ollama_url = ollama_base_url
        self.project_id = project_id

        # Project profile determines agent behavior
        self.profile = project_profile or get_preset_profile("club_app")

        # Agent configuration
        self.quinn_model = "deepseek-r1:latest"  # QA specialist
        self.felix_model = "qwen2.5-coder:7b"    # Feature architect

        # Get agent-specific configs from profile
        self.quinn_config = self.profile.get_agent_config("quinn")
        self.felix_config = self.profile.get_agent_config("felix")

        # Thresholds (now from profile!)
        self.critical_issue_threshold = self.quinn_config.critical_issue_threshold
        self.min_quality_score = self.quinn_config.min_quality_score

        # Week 143: Vector DB service (lazy initialization)
        self._chroma_service: Optional["ChromaService"] = None
        self._vector_context: Optional[Dict[str, Any]] = None

    def _get_chroma_service(self) -> Optional["ChromaService"]:
        """Get or create ChromaDB service instance (lazy init)."""
        if not CHROMA_AVAILABLE:
            return None
        if self._chroma_service is None:
            try:
                self._chroma_service = ChromaService()
                logger.info("ChromaDB service initialized for SpecReviewService")
            except Exception as e:
                logger.warning(f"ChromaDB not available: {e}. Vector context disabled.")
                return None
        return self._chroma_service

    def _fetch_review_context(
        self,
        spec_section: Optional[str] = None,
        topics: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch relevant context from Vector DB for spec review.

        Args:
            spec_section: Specific section being reviewed (e.g., "architecture", "data_model")
            topics: List of topics to search for (e.g., ["authentication", "database"])

        Returns:
            Dict with relevant docs, patterns, and code examples
        """
        chroma = self._get_chroma_service()
        if not chroma:
            return None

        try:
            context = {
                "architecture_docs": [],
                "code_patterns": [],
                "best_practices": [],
                "related_components": []
            }

            # Build search queries based on section and topics
            queries = []
            if spec_section:
                queries.append(f"{spec_section} implementation patterns")
                queries.append(f"{spec_section} best practices")
            if topics:
                for topic in topics[:3]:  # Limit to 3 topics
                    queries.append(f"{topic} architecture")

            # Default query if none specified
            if not queries:
                queries = ["system architecture overview", "design patterns"]

            # Fetch from Vector DB
            for query in queries[:5]:  # Max 5 queries
                results = chroma.query_project_knowledge(
                    project_id=self.project_id,
                    query=query,
                    n_results=3
                )

                if results and "documents" in results:
                    for doc in results.get("documents", [[]])[0]:
                        if doc and len(doc) > 50:
                            # Categorize by content
                            doc_lower = doc.lower()
                            if any(x in doc_lower for x in ["architecture", "system", "design"]):
                                if doc not in context["architecture_docs"]:
                                    context["architecture_docs"].append(doc[:500])
                            elif any(x in doc_lower for x in ["pattern", "practice", "standard"]):
                                if doc not in context["best_practices"]:
                                    context["best_practices"].append(doc[:500])
                            elif any(x in doc_lower for x in ["class", "function", "method", "component"]):
                                if doc not in context["code_patterns"]:
                                    context["code_patterns"].append(doc[:500])

            # Limit results
            context["architecture_docs"] = context["architecture_docs"][:3]
            context["best_practices"] = context["best_practices"][:3]
            context["code_patterns"] = context["code_patterns"][:3]

            # Only return if we found something
            total_items = sum(len(v) for v in context.values())
            if total_items > 0:
                logger.info(f"Fetched {total_items} context items for spec review")
                return context

            return None

        except Exception as e:
            logger.warning(f"Error fetching review context: {e}")
            return None

    def _format_vector_context(self, context: Optional[Dict[str, Any]]) -> str:
        """Format Vector DB context for inclusion in prompts."""
        if not context:
            return ""

        lines = ["\nRELEVANT PROJECT CONTEXT (from knowledge base):"]

        if context.get("architecture_docs"):
            lines.append("\n📐 Architecture References:")
            for i, doc in enumerate(context["architecture_docs"][:2], 1):
                lines.append(f"  {i}. {doc[:300]}...")

        if context.get("best_practices"):
            lines.append("\n✅ Best Practices:")
            for i, doc in enumerate(context["best_practices"][:2], 1):
                lines.append(f"  {i}. {doc[:300]}...")

        if context.get("code_patterns"):
            lines.append("\n🔧 Code Patterns:")
            for i, doc in enumerate(context["code_patterns"][:2], 1):
                lines.append(f"  {i}. {doc[:300]}...")

        lines.append("\n---")
        return "\n".join(lines)

    # ========================================================================
    # STAGE 1: QUINN REVIEWS SPECIFICATION
    # ========================================================================

    async def quinn_review(
        self,
        specification_id: UUID
    ) -> ReviewResult:
        """
        Quinn (QA agent) reviews the specification.

        Args:
            specification_id: UUID of the specification to review

        Returns:
            ReviewResult with suggestions and quality score
        """
        start_time = datetime.now(timezone.utc)

        # Get specification
        spec = await self._get_specification(specification_id)
        if not spec:
            raise ValueError(f"Specification {specification_id} not found")

        # Build review prompt
        prompt = self._build_quinn_review_prompt(spec)

        # Query Quinn
        try:
            response = await self._query_ollama(self.quinn_model, prompt)

            # Parse suggestions
            suggestions = self._parse_quinn_suggestions(response)
            quality_score = self._extract_quality_score(response)

            # Determine if escalation needed
            critical_count = sum(
                1 for s in suggestions
                if s.priority == SuggestionPriority.CRITICAL
            )

            requires_human = (
                critical_count > self.critical_issue_threshold or
                quality_score < self.min_quality_score
            )

            escalation_reason = None
            if requires_human:
                if critical_count > self.critical_issue_threshold:
                    escalation_reason = f"Too many critical issues ({critical_count})"
                else:
                    escalation_reason = f"Quality score too low ({quality_score:.1f}/10)"

            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            return ReviewResult(
                specification_id=specification_id,
                suggestions=suggestions,
                overall_quality_score=quality_score,
                requires_human_review=requires_human,
                escalation_reason=escalation_reason,
                reviewed_at=end_time,
                review_duration_seconds=duration
            )

        except Exception as e:
            raise Exception(f"Quinn review failed: {e}")

    def _build_quinn_review_prompt(
        self,
        spec: Specification,
        topics: Optional[List[str]] = None
    ) -> str:
        """Build Quinn's review prompt with project profile context and Vector DB knowledge."""

        # Build strictness guidance from profile
        strictness_guide = self._build_strictness_guidance()

        # Week 143: Fetch relevant context from Vector DB
        vector_context = self._fetch_review_context(
            spec_section="specification",
            topics=topics or ["architecture", "design patterns", "data model"]
        )
        context_section = self._format_vector_context(vector_context)

        return f"""You are Quinn, a QA specialist reviewing a High-Level Design specification.

SPECIFICATION TO REVIEW:
{spec.content_markdown}
{context_section}

{self.quinn_config.context_instructions}

YOUR TASK:
Review this specification for completeness, correctness, and quality.
Generate specific suggestions for improvement.
IMPORTANT: Adjust your evaluation based on the project size and focus areas above!

For each issue found, provide:
1. TYPE: add/remove/change
2. PRIORITY: critical/high/medium/low
3. SECTION: Which part of the spec (e.g., "architecture", "data_model", "api_design")
4. DESCRIPTION: What specifically needs to change
5. REASONING: Why this change is important

{strictness_guide}

SCORING GUIDANCE FOR {self.profile.size.value.upper()} PROJECTS:
- A score of {self.min_quality_score}/10 is the minimum acceptable
- For areas marked RELAXED/IGNORE, don't deduct points for missing enterprise features
- For areas marked STRICT/CRITICAL, be thorough and demanding
- Be proportionate: a {self.profile.size.value} project with {self.profile.expected_users} users
  doesn't need the same level of detail as an enterprise system

FORMAT YOUR RESPONSE AS:
QUALITY_SCORE: [0-10]

SUGGESTIONS:
---
TYPE: [add/remove/change]
PRIORITY: [critical/high/medium/low]
SECTION: [section name]
DESCRIPTION: [what to change]
REASONING: [why]
---
[repeat for each suggestion]

END_REVIEW
"""

    def _build_strictness_guidance(self) -> str:
        """Build review criteria based on focus area strictness."""
        lines = ["REVIEW CRITERIA (adjusted for project profile):"]

        # Map focus areas to review criteria
        criteria_map = {
            FocusArea.SECURITY: ("Security", "authentication, encryption, input validation"),
            FocusArea.PERFORMANCE: ("Performance", "response times, throughput, caching"),
            FocusArea.SCALABILITY: ("Scalability", "growth handling, load balancing"),
            FocusArea.USABILITY: ("Usability", "user experience, accessibility, simplicity"),
            FocusArea.RELIABILITY: ("Reliability", "uptime, error handling, recovery"),
            FocusArea.MAINTAINABILITY: ("Maintainability", "code quality, docs, testing"),
            FocusArea.COMPLIANCE: ("Compliance", "GDPR, data protection, auditing"),
        }

        strictness_labels = {
            StrictnessLevel.CRITICAL: "🔴 CRITICAL - Must be perfect, block on any issue",
            StrictnessLevel.STRICT: "🟠 STRICT - Thorough review required",
            StrictnessLevel.NORMAL: "🟡 NORMAL - Standard evaluation",
            StrictnessLevel.RELAXED: "🟢 RELAXED - Basic checks only, advisory",
            StrictnessLevel.IGNORE: "⚪ IGNORE - Skip this aspect entirely",
        }

        for area, (name, description) in criteria_map.items():
            strictness = self.quinn_config.get_strictness(area)
            label = strictness_labels.get(strictness, "NORMAL")
            lines.append(f"- {name} ({description})")
            lines.append(f"  → {label}")

        # Add general criteria not tied to focus areas
        lines.extend([
            "",
            "ALWAYS REVIEW (regardless of profile):",
            "- Architecture: Is the basic structure sound for project size?",
            "- Data Model: Are core entities defined?",
            "- API Design: Are main endpoints present?",
            "- Development Phases: Realistic for team size?",
        ])

        return "\n".join(lines)

    def _parse_quinn_suggestions(self, response: str) -> List[ReviewSuggestion]:
        """Parse Quinn's suggestions from response text."""
        suggestions = []

        # Split by suggestion blocks
        blocks = re.split(r'---+', response)

        for block in blocks:
            if not block.strip():
                continue

            # Extract fields
            type_match = re.search(r'TYPE:\s*(add|remove|change)', block, re.IGNORECASE)
            priority_match = re.search(r'PRIORITY:\s*(critical|high|medium|low)', block, re.IGNORECASE)
            section_match = re.search(r'SECTION:\s*(.+?)(?=\n|$)', block, re.IGNORECASE)
            desc_match = re.search(r'DESCRIPTION:\s*(.+?)(?=\nREASONING:|$)', block, re.IGNORECASE | re.DOTALL)
            reason_match = re.search(r'REASONING:\s*(.+?)(?=\n---|$)', block, re.IGNORECASE | re.DOTALL)

            if type_match and priority_match and section_match and desc_match:
                suggestions.append(ReviewSuggestion(
                    id=str(uuid4())[:8],
                    type=SuggestionType(type_match.group(1).lower()),
                    priority=SuggestionPriority(priority_match.group(1).lower()),
                    section=section_match.group(1).strip(),
                    description=desc_match.group(1).strip(),
                    reasoning=reason_match.group(1).strip() if reason_match else ""
                ))

        return suggestions

    def _extract_quality_score(self, response: str) -> float:
        """Extract quality score from response."""
        match = re.search(r'QUALITY_SCORE:\s*(\d+(?:\.\d+)?)', response, re.IGNORECASE)
        if match:
            score = float(match.group(1))
            return min(max(score, 0.0), 10.0)
        return 5.0  # Default middle score

    # ========================================================================
    # STAGE 2: FELIX PROCESSES SUGGESTIONS
    # ========================================================================

    async def felix_process_suggestions(
        self,
        specification_id: UUID,
        review_result: ReviewResult
    ) -> ProcessedResult:
        """
        Felix evaluates and processes Quinn's suggestions.

        Args:
            specification_id: UUID of the specification
            review_result: Quinn's review result

        Returns:
            ProcessedResult with acceptance/rejection decisions
        """
        if not review_result.suggestions:
            return ProcessedResult(
                specification_id=specification_id,
                accepted_count=0,
                rejected_count=0,
                updated_content=None,
                needs_human_decision=[],
                processed_at=datetime.now(timezone.utc)
            )

        # Get specification
        spec = await self._get_specification(specification_id)
        if not spec:
            raise ValueError(f"Specification {specification_id} not found")

        # Process each suggestion
        needs_human = []
        accepted = []
        rejected = []

        for suggestion in review_result.suggestions:
            decision, reasoning = await self._felix_evaluate_suggestion(
                spec, suggestion
            )

            suggestion.felix_response = reasoning

            if decision == "accept":
                suggestion.status = SuggestionStatus.ACCEPTED
                accepted.append(suggestion)
            elif decision == "reject":
                suggestion.status = SuggestionStatus.REJECTED
                rejected.append(suggestion)
            else:  # unsure
                needs_human.append(suggestion)

        # Generate updated content if any accepted
        updated_content = None
        if accepted:
            updated_content = await self._felix_apply_changes(spec, accepted)

        return ProcessedResult(
            specification_id=specification_id,
            accepted_count=len(accepted),
            rejected_count=len(rejected),
            updated_content=updated_content,
            needs_human_decision=needs_human,
            processed_at=datetime.now(timezone.utc)
        )

    async def _felix_evaluate_suggestion(
        self,
        spec: Specification,
        suggestion: ReviewSuggestion
    ) -> Tuple[str, str]:
        """
        Felix evaluates a single suggestion.

        Returns:
            Tuple of (decision: "accept"/"reject"/"unsure", reasoning: str)
        """
        prompt = f"""You are Felix, the Feature Architect who created this specification.
Quinn (QA) has suggested an improvement. Evaluate if it should be accepted.

ORIGINAL SPECIFICATION SECTION ({suggestion.section}):
{self._extract_section(spec.content_markdown, suggestion.section)}

QUINN'S SUGGESTION:
- Type: {suggestion.type.value}
- Priority: {suggestion.priority.value}
- Description: {suggestion.description}
- Reasoning: {suggestion.reasoning}

EVALUATE:
1. Is this suggestion valid and beneficial?
2. Does it align with the project's goals and constraints?
3. Would implementing it improve the specification?

Be objective - accept good suggestions even if they criticize your work.
Reject suggestions that are incorrect, unnecessary, or would harm the design.
Say "unsure" if you genuinely can't decide (this will escalate to human).

FORMAT:
DECISION: [accept/reject/unsure]
REASONING: [Your explanation]
"""

        try:
            response = await self._query_ollama(self.felix_model, prompt)

            # Parse decision
            decision_match = re.search(
                r'DECISION:\s*(accept|reject|unsure)',
                response,
                re.IGNORECASE
            )
            reasoning_match = re.search(
                r'REASONING:\s*(.+?)(?=$)',
                response,
                re.IGNORECASE | re.DOTALL
            )

            decision = decision_match.group(1).lower() if decision_match else "unsure"
            reasoning = reasoning_match.group(1).strip() if reasoning_match else response

            return decision, reasoning

        except Exception as e:
            return "unsure", f"Error evaluating: {e}"

    async def _felix_apply_changes(
        self,
        spec: Specification,
        accepted_suggestions: List[ReviewSuggestion]
    ) -> str:
        """
        Felix applies accepted suggestions to generate updated spec.

        Returns:
            Updated specification content
        """
        prompt = f"""You are Felix. Apply these accepted improvements to the specification.

ORIGINAL SPECIFICATION:
{spec.content_markdown}

ACCEPTED IMPROVEMENTS TO APPLY:
{self._format_suggestions_for_apply(accepted_suggestions)}

Generate the COMPLETE updated specification with all improvements applied.
Maintain the same structure and format as the original.
Only make the specified changes - don't add other modifications.

OUTPUT THE COMPLETE UPDATED SPECIFICATION:
"""

        try:
            response = await self._query_ollama(self.felix_model, prompt, timeout=180)
            return response.strip()
        except Exception as e:
            raise Exception(f"Failed to apply changes: {e}")

    def _format_suggestions_for_apply(self, suggestions: List[ReviewSuggestion]) -> str:
        """Format suggestions for the apply prompt."""
        lines = []
        for i, s in enumerate(suggestions, 1):
            lines.append(f"{i}. [{s.type.value.upper()}] in {s.section}:")
            lines.append(f"   {s.description}")
        return "\n".join(lines)

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a section from the spec content."""
        # Try to find markdown header
        pattern = rf'##\s*\d*\.?\s*{re.escape(section_name)}.*?(?=\n##|\Z)'
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(0)[:1000]  # Limit length
        return f"(Section '{section_name}' not found - review full spec)"

    # ========================================================================
    # COMBINED REVIEW FLOW
    # ========================================================================

    async def full_review_cycle(
        self,
        specification_id: UUID
    ) -> Dict:
        """
        Run complete review cycle: Quinn review → Felix process → Result

        Args:
            specification_id: UUID of the specification

        Returns:
            Dict with review results, processed results, and final status
        """
        # Stage 1: Quinn reviews
        print(f"Stage 1: Quinn reviewing specification {specification_id}...")
        review_result = await self.quinn_review(specification_id)

        print(f"  - Quality score: {review_result.overall_quality_score}/10")
        print(f"  - Suggestions: {len(review_result.suggestions)}")
        print(f"  - Requires human: {review_result.requires_human_review}")

        # Check for immediate escalation
        if review_result.requires_human_review:
            return {
                "status": "needs_human_review",
                "reason": review_result.escalation_reason,
                "review": review_result,
                "processed": None,
                "final_action": "human_must_review"
            }

        # Stage 2: Felix processes suggestions
        if review_result.suggestions:
            print(f"Stage 2: Felix processing {len(review_result.suggestions)} suggestions...")
            processed = await self.felix_process_suggestions(
                specification_id, review_result
            )

            print(f"  - Accepted: {processed.accepted_count}")
            print(f"  - Rejected: {processed.rejected_count}")
            print(f"  - Needs human: {len(processed.needs_human_decision)}")

            # Determine final action
            if processed.needs_human_decision:
                return {
                    "status": "partial_human_review",
                    "reason": f"{len(processed.needs_human_decision)} suggestions need human decision",
                    "review": review_result,
                    "processed": processed,
                    "final_action": "human_decides_remaining"
                }
            elif processed.accepted_count > 0:
                return {
                    "status": "auto_improved",
                    "reason": f"Applied {processed.accepted_count} improvements",
                    "review": review_result,
                    "processed": processed,
                    "final_action": "specification_updated"
                }
            else:
                return {
                    "status": "approved",
                    "reason": "All suggestions rejected - spec is good",
                    "review": review_result,
                    "processed": processed,
                    "final_action": "ready_for_next_stage"
                }
        else:
            return {
                "status": "approved",
                "reason": "No suggestions - spec is good",
                "review": review_result,
                "processed": None,
                "final_action": "ready_for_next_stage"
            }

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def _get_specification(
        self,
        specification_id: UUID
    ) -> Optional[Specification]:
        """Get specification from database."""
        result = await self.db.execute(
            select(Specification)
            .where(Specification.id == specification_id)
        )
        return result.scalar_one_or_none()

    async def _query_ollama(
        self,
        model: str,
        prompt: str,
        timeout: int = 300
    ) -> str:
        """Query Ollama model."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data.get("response", "")
        except aiohttp.ClientError as e:
            raise Exception(f"Ollama connection error: {e}")
        except asyncio.TimeoutError:
            raise Exception(f"Ollama timeout after {timeout}s for model {model}")
