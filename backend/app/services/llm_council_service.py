"""
LLM Council Service for Multi-Model Decision Making

Week 52: Implements 3-stage consensus process
- Stage 1: Response (query all models in parallel)
- Stage 2: Peer Review (models review each other blind/anonymous)
- Stage 3: Synthesis (chairman creates final decision)
"""

import re
import asyncio
from uuid import UUID, uuid4
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.llm_council import (
    CouncilSession,
    CouncilResponse,
    CouncilReview,
    CouncilDecision
)
from app.config import settings


class LLMCouncilService:
    """
    Multi-LLM consensus decision making service.

    Uses 6 local Ollama models to reach consensus on critical decisions:
    - Architecture & design decisions
    - Epic/Feature/Story generation validation
    - Quality gate override assessments
    - Project planning & resource allocation

    3-Stage Process:
    1. Response: Query all models in parallel (asyncio.gather)
    2. Peer Review: Models review each other (blind/anonymous)
    3. Synthesis: Chairman creates final decision with consensus level
    """

    def __init__(
        self,
        db_session: AsyncSession,
        ollama_base_url: str = None
    ):
        self.db = db_session
        # Use settings.OLLAMA_BASE_URL if no base_url provided
        self.ollama_url = ollama_base_url or settings.OLLAMA_BASE_URL

        # Council model configuration
        self.models = {
            "deepseek-r1:latest": {"weight": 2.0, "role": "chairman"},
            "qwen2.5-coder:7b": {"weight": 1.5, "role": "technical"},
            "codellama:latest": {"weight": 1.5, "role": "implementation"},
            "mistral:latest": {"weight": 1.0, "role": "documentation"},
            "qwen2.5:7b": {"weight": 1.0, "role": "planning"},
            "llama3.2:latest": {"weight": 1.0, "role": "quality"}
        }

        # Council thresholds
        self.min_consensus_threshold = 70.0  # % agreement required
        self.high_consensus_threshold = 80.0  # % for "strong consensus"

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    async def create_session(
        self,
        question: str,
        context: dict,
        decision_type: str,
        agent_id: str
    ) -> CouncilSession:
        """
        Create new council session.

        Args:
            question: The question/decision to be made
            context: Additional context (codebase info, previous attempts, etc.)
            decision_type: architecture, planning, quality, or generation
            agent_id: Which agent is requesting the council decision

        Returns:
            Created CouncilSession with status='pending'
        """
        session = CouncilSession(
            id=uuid4(),
            question=question,
            context=context,
            decision_type=decision_type,
            agent_id=agent_id,
            status="pending",
            created_at=datetime.utcnow()
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def get_session(
        self,
        session_id: UUID,
        include_relationships: bool = True
    ) -> Optional[CouncilSession]:
        """
        Retrieve council session by ID.

        Args:
            session_id: UUID of the session
            include_relationships: Whether to eager-load responses, reviews, decision

        Returns:
            CouncilSession or None if not found
        """
        query = select(CouncilSession).where(CouncilSession.id == session_id)

        if include_relationships:
            query = query.options(
                selectinload(CouncilSession.responses)
                    .selectinload(CouncilResponse.reviews_received),
                selectinload(CouncilSession.reviews),
                selectinload(CouncilSession.decision)
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        decision_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CouncilSession]:
        """
        List council sessions with optional filters.

        Args:
            agent_id: Filter by agent
            status: Filter by status (pending, reviewing, complete)
            decision_type: Filter by decision type
            limit: Max results
            offset: Pagination offset

        Returns:
            List of CouncilSession objects
        """
        query = select(CouncilSession)

        if agent_id:
            query = query.where(CouncilSession.agent_id == agent_id)
        if status:
            query = query.where(CouncilSession.status == status)
        if decision_type:
            query = query.where(CouncilSession.decision_type == decision_type)

        query = query.order_by(CouncilSession.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ========================================================================
    # STAGE 1: RESPONSE - Query All Models in Parallel
    # ========================================================================

    async def query_all_models(
        self,
        session_id: UUID
    ) -> List[CouncilResponse]:
        """
        Stage 1: Query all models in parallel.

        Uses asyncio.gather for concurrent Ollama API calls.
        Each model receives same question + context.

        Args:
            session_id: UUID of the council session

        Returns:
            List of successful CouncilResponse objects

        Raises:
            ValueError: If session not found or not in correct status
        """
        # Get session
        session = await self.get_session(session_id, include_relationships=False)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if session.status != "pending":
            raise ValueError(
                f"Session must be 'pending' for querying. Current status: {session.status}"
            )

        # Build prompt
        prompt = self._build_prompt(
            session.question,
            session.context,
            session.decision_type
        )

        # Query all models concurrently
        tasks = [
            self._query_single_model(model_name, prompt, session_id)
            for model_name in self.models.keys()
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failures, log errors
        successful_responses = []
        failed_models = []

        for i, response in enumerate(responses):
            if isinstance(response, CouncilResponse):
                successful_responses.append(response)
            else:
                model_name = list(self.models.keys())[i]
                failed_models.append(model_name)
                print(f"❌ Failed to query {model_name}: {response}")

        # Update session status
        if successful_responses:
            session.status = "reviewing"
            await self.db.commit()
            print(
                f"✓ Stage 1 complete: {len(successful_responses)}/{len(self.models)} models responded"
            )
        else:
            print("❌ Stage 1 failed: No models responded successfully")

        return successful_responses

    async def _query_single_model(
        self,
        model_name: str,
        prompt: str,
        session_id: UUID
    ) -> CouncilResponse:
        """
        Query single Ollama model.

        Args:
            model_name: Name of Ollama model to query
            prompt: Full prompt text
            session_id: UUID of session (for saving response)

        Returns:
            CouncilResponse object

        Raises:
            Exception: If Ollama API call fails
        """
        try:
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=aiohttp.ClientTimeout(total=900)  # 15 min timeout for complex queries
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

                    # Parse response
                    response_text = data.get("response", "")
                    confidence = self._extract_confidence(response_text)
                    reasoning = self._extract_reasoning(response_text)

                    # Save to database
                    council_response = CouncilResponse(
                        id=uuid4(),
                        session_id=session_id,
                        model_name=model_name,
                        response_text=response_text,
                        confidence=confidence,
                        reasoning=reasoning,
                        created_at=datetime.utcnow()
                    )

                    self.db.add(council_response)
                    await self.db.commit()
                    await self.db.refresh(council_response)

                    return council_response

        except asyncio.TimeoutError:
            raise Exception(f"Timeout querying {model_name}")
        except aiohttp.ClientError as e:
            raise Exception(f"HTTP error querying {model_name}: {e}")
        except Exception as e:
            raise Exception(f"Error querying {model_name}: {e}")

    # ========================================================================
    # PROMPT ENGINEERING
    # ========================================================================

    def _build_prompt(
        self,
        question: str,
        context: dict,
        decision_type: str
    ) -> str:
        """
        Build prompt based on decision type.

        Args:
            question: The question/decision to be made
            context: Additional context dictionary
            decision_type: architecture, planning, quality, or generation

        Returns:
            Complete prompt string with instructions
        """
        base_prompt = f"""You are participating in a technical council to make a critical decision.

QUESTION:
{question}

CONTEXT:
{self._format_context(context)}

INSTRUCTIONS:
1. Analyze the question carefully
2. Consider the provided context
3. Provide your recommendation
4. Explain your reasoning
5. Rate your confidence (0-100%)

FORMAT YOUR RESPONSE AS:
RECOMMENDATION: [Your specific recommendation]
REASONING: [Why you recommend this]
CONFIDENCE: [0-100]%
"""

        # Add decision-type specific guidance
        if decision_type == "architecture":
            base_prompt += """
ARCHITECTURE CONSIDERATIONS:
- Scalability: How will this handle growth?
- Maintainability: How easy to modify/extend?
- Performance: Latency/throughput impacts?
- Security: Potential vulnerabilities?
- Cost: Infrastructure/operational costs?
- Technology fit: Does it align with existing stack?
"""
        elif decision_type == "quality":
            base_prompt += """
QUALITY CONSIDERATIONS:
- Test coverage: Is testing sufficient?
- Code quality: Are standards met?
- Security: Any vulnerabilities?
- Performance: Any bottlenecks?
- Maintainability: Is code readable/documented?
- Technical debt: Does this add or remove debt?
"""
        elif decision_type == "planning":
            base_prompt += """
PLANNING CONSIDERATIONS:
- Resource allocation: Do we have capacity?
- Risk assessment: What could go wrong?
- Dependencies: What's required first?
- Timeline: Is estimate realistic?
- Priorities: Does this align with goals?
- ROI: Is this worth the investment?
"""
        elif decision_type == "generation":
            base_prompt += """
GENERATION QUALITY CONSIDERATIONS:
- Requirements completeness: Are all aspects covered?
- Clarity: Are requirements unambiguous?
- Testability: Can we verify completion?
- Scope: Is it appropriately sized?
- Dependencies: Are related items identified?
- Acceptance criteria: Are they clear/measurable?
"""

        return base_prompt

    def _format_context(self, context: dict) -> str:
        """
        Format context dictionary into readable text.

        Args:
            context: Context dictionary

        Returns:
            Formatted string
        """
        if not context:
            return "(No additional context provided)"

        lines = []
        for key, value in context.items():
            # Convert key from snake_case to Title Case
            formatted_key = key.replace("_", " ").title()
            lines.append(f"- {formatted_key}: {value}")

        return "\n".join(lines)

    def _extract_confidence(self, response_text: str) -> float:
        """
        Extract confidence value from response text.

        Looks for "CONFIDENCE: XX%" pattern.

        Args:
            response_text: Model's response text

        Returns:
            Confidence as float (0.0-1.0), defaults to 0.5 if not found
        """
        # Match "CONFIDENCE: 85%" or "CONFIDENCE: 85"
        match = re.search(r'CONFIDENCE:\s*(\d+)%?', response_text, re.IGNORECASE)

        if match:
            confidence_int = int(match.group(1))
            return min(max(confidence_int / 100.0, 0.0), 1.0)  # Clamp to 0-1

        # Default to 50% if not found
        return 0.5

    def _extract_reasoning(self, response_text: str) -> Optional[str]:
        """
        Extract reasoning section from response text.

        Looks for "REASONING: ..." pattern.

        Args:
            response_text: Model's response text

        Returns:
            Reasoning text or None
        """
        # Match text after "REASONING:" until next section or end
        match = re.search(
            r'REASONING:\s*(.+?)(?=\n(?:CONFIDENCE|RECOMMENDATION)|$)',
            response_text,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            return match.group(1).strip()

        return None

    # ========================================================================
    # STAGE 2: PEER REVIEW - Models Review Each Other (Blind)
    # ========================================================================

    async def peer_review(
        self,
        session_id: UUID
    ) -> List[CouncilReview]:
        """
        Stage 2: Models review each other's responses (blind/anonymous).

        Each model reviews all OTHER models' responses.
        Reviews are anonymous (model names hidden during review).

        Args:
            session_id: UUID of the council session

        Returns:
            List of successful CouncilReview objects

        Raises:
            ValueError: If session not found or not enough responses
        """
        # Get session with responses
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        responses = session.responses

        if len(responses) < 2:
            raise ValueError("Need at least 2 responses for peer review")

        # Each model reviews all others
        review_tasks = []
        for reviewer_model in self.models.keys():
            # Find this model's response
            reviewer_response = next(
                (r for r in responses if r.model_name == reviewer_model),
                None
            )

            if not reviewer_response:
                continue  # This model didn't respond in Stage 1

            # Review all other responses
            for response_to_review in responses:
                if response_to_review.model_name == reviewer_model:
                    continue  # Don't review own response

                review_tasks.append(
                    self._review_single_response(
                        reviewer_model,
                        response_to_review,
                        session
                    )
                )

        # Execute all reviews concurrently
        reviews = await asyncio.gather(*review_tasks, return_exceptions=True)

        # Filter successful reviews
        successful_reviews = [
            r for r in reviews
            if isinstance(r, CouncilReview)
        ]

        print(
            f"✓ Stage 2 complete: {len(successful_reviews)} reviews from {len(responses)} models"
        )

        return successful_reviews

    async def _review_single_response(
        self,
        reviewer_model: str,
        response_to_review: CouncilResponse,
        session: CouncilSession
    ) -> CouncilReview:
        """
        Single model reviews another's response.

        Args:
            reviewer_model: Name of model doing the review
            response_to_review: Response being reviewed
            session: Council session context

        Returns:
            CouncilReview object

        Raises:
            Exception: If review fails
        """
        # Build review prompt (anonymized - no model names shown)
        prompt = f"""You are peer-reviewing a technical recommendation from another expert.

ORIGINAL QUESTION:
{session.question}

RECOMMENDATION TO REVIEW:
{response_to_review.response_text}

Rate this recommendation on:
1. ACCURACY (0-10): Is it technically correct?
2. COMPLETENESS (0-10): Does it address all aspects?
3. CLARITY (0-10): Is it easy to understand?
4. FEASIBILITY (0-10): Can it be realistically implemented?

Provide brief comments explaining your scores.

FORMAT:
ACCURACY: [0-10]
COMPLETENESS: [0-10]
CLARITY: [0-10]
FEASIBILITY: [0-10]
COMMENTS: [Your explanation]
"""

        try:
            # Query reviewer model
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": reviewer_model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=aiohttp.ClientTimeout(total=600)  # 10 min for peer reviews
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    review_text = data.get("response", "")

                    # Parse scores
                    scores = self._parse_review_scores(review_text)

                    # Save review
                    review = CouncilReview(
                        id=uuid4(),
                        session_id=session.id,
                        reviewer_model=reviewer_model,
                        reviewed_response_id=response_to_review.id,
                        accuracy_score=scores["accuracy"],
                        completeness_score=scores["completeness"],
                        clarity_score=scores["clarity"],
                        feasibility_score=scores["feasibility"],
                        comments=scores.get("comments"),
                        created_at=datetime.utcnow()
                    )

                    self.db.add(review)
                    await self.db.commit()
                    await self.db.refresh(review)

                    return review

        except Exception as e:
            raise Exception(f"Error in peer review by {reviewer_model}: {e}")

    def _parse_review_scores(self, review_text: str) -> Dict:
        """
        Parse review scores from review text.

        Args:
            review_text: Model's review text

        Returns:
            Dict with scores and comments
        """
        scores = {
            "accuracy": 5.0,
            "completeness": 5.0,
            "clarity": 5.0,
            "feasibility": 5.0,
            "comments": None
        }

        # Parse each score
        for key in ["accuracy", "completeness", "clarity", "feasibility"]:
            pattern = rf'{key}:\s*(\d+(?:\.\d+)?)'
            match = re.search(pattern, review_text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                scores[key] = min(max(value, 0.0), 10.0)  # Clamp 0-10

        # Parse comments
        comments_match = re.search(
            r'COMMENTS:\s*(.+?)(?=\n[A-Z]+:|$)',
            review_text,
            re.IGNORECASE | re.DOTALL
        )
        if comments_match:
            scores["comments"] = comments_match.group(1).strip()

        return scores

    # ========================================================================
    # STAGE 3: SYNTHESIS - Chairman Creates Final Decision
    # ========================================================================

    async def synthesize(
        self,
        session_id: UUID,
        chairman_model: str = "deepseek-r1:latest"
    ) -> CouncilDecision:
        """
        Stage 3: Chairman synthesizes final decision.

        Considers:
        - All model responses
        - Peer review scores
        - Model weights
        - Consensus level

        Args:
            session_id: UUID of the council session
            chairman_model: Model to use for synthesis (default: deepseek-r1)

        Returns:
            CouncilDecision object

        Raises:
            ValueError: If session not found or missing data
        """
        # Get session with responses and reviews
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if not session.responses:
            raise ValueError("No responses to synthesize")

        # Calculate aggregate scores per response
        response_scores = self._calculate_aggregate_scores(
            session.responses,
            session.reviews
        )

        # Calculate consensus level
        consensus_level = self._calculate_consensus(
            session.responses,
            response_scores
        )

        # Identify dissenting opinions
        dissenting_opinions = self._detect_outliers(
            session.responses,
            response_scores
        )

        # Build synthesis prompt for chairman
        prompt = f"""You are the chairman synthesizing the council's decision.

ORIGINAL QUESTION:
{session.question}

COUNCIL RESPONSES ({len(session.responses)}):
{self._format_responses_for_synthesis(session.responses, response_scores)}

PEER REVIEW SUMMARY:
{self._format_review_summary(session.reviews)}

CONSENSUS LEVEL: {consensus_level:.1f}%

TASK:
Synthesize the best elements from all responses into a final recommendation.
Balance majority opinions with valuable dissenting views.
Explain your reasoning and rate your confidence.

FORMAT:
FINAL DECISION: [Synthesized recommendation]
REASONING: [Why this synthesis is best]
CONFIDENCE: [0-100]%
KEY CONSIDERATIONS: [Important points to remember]
"""

        try:
            # Query chairman model
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": chairman_model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=aiohttp.ClientTimeout(total=600)  # 10 min for chairman synthesis
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    decision_text = data.get("response", "")

                    # Parse decision
                    final_decision = self._extract_decision(decision_text)
                    confidence = self._extract_confidence(decision_text)
                    reasoning = self._extract_reasoning(decision_text)

                    # Save decision
                    decision = CouncilDecision(
                        id=uuid4(),
                        session_id=session.id,
                        chairman_model=chairman_model,
                        final_decision=final_decision or decision_text,
                        confidence=confidence,
                        consensus_level=consensus_level,
                        dissenting_opinions=dissenting_opinions if dissenting_opinions else None,
                        synthesis_reasoning=reasoning,
                        created_at=datetime.utcnow()
                    )

                    self.db.add(decision)

                    # Update session status
                    session.status = "complete"
                    session.completed_at = datetime.utcnow()

                    await self.db.commit()
                    await self.db.refresh(decision)

                    print(
                        f"✓ Stage 3 complete: Decision with {consensus_level:.1f}% consensus"
                    )

                    return decision

        except Exception as e:
            raise Exception(f"Error in synthesis by {chairman_model}: {e}")

    def _calculate_aggregate_scores(
        self,
        responses: List[CouncilResponse],
        reviews: List[CouncilReview]
    ) -> Dict[str, float]:
        """
        Calculate aggregate review scores per response.

        Args:
            responses: List of council responses
            reviews: List of council reviews

        Returns:
            Dict mapping response_id to average review score
        """
        scores = {}

        for response in responses:
            # Get all reviews for this response
            response_reviews = [
                r for r in reviews
                if r.reviewed_response_id == response.id
            ]

            if response_reviews:
                # Average of all 4 scores from all reviews
                avg_score = sum(
                    (r.accuracy_score + r.completeness_score +
                     r.clarity_score + r.feasibility_score) / 4
                    for r in response_reviews
                ) / len(response_reviews)

                scores[str(response.id)] = avg_score
            else:
                scores[str(response.id)] = 5.0  # Default middle score

        return scores

    def _calculate_consensus(
        self,
        responses: List[CouncilResponse],
        response_scores: Dict[str, float]
    ) -> float:
        """
        Calculate consensus level (0-100%).

        Uses:
        - Confidence values from responses
        - Review scores
        - Standard deviation of confidences

        Args:
            responses: List of council responses
            response_scores: Aggregate review scores

        Returns:
            Consensus level as percentage (0-100)
        """
        if not responses:
            return 0.0

        # Calculate variance in confidence values
        confidences = [r.confidence for r in responses]
        avg_confidence = sum(confidences) / len(confidences)
        variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)
        std_dev = variance ** 0.5

        # Calculate variance in review scores
        scores = list(response_scores.values())
        avg_score = sum(scores) / len(scores) if scores else 5.0
        score_variance = sum((s - avg_score) ** 2 for s in scores) / len(scores) if scores else 1.0
        score_std_dev = score_variance ** 0.5

        # Lower std_dev = higher consensus
        # Normalize: std_dev of 0 = 100%, std_dev of 0.5 = 0%
        confidence_consensus = max(0, 100 * (1 - std_dev / 0.5))
        score_consensus = max(0, 100 * (1 - score_std_dev / 5.0))

        # Weighted average
        consensus = (confidence_consensus * 0.6 + score_consensus * 0.4)

        return min(max(consensus, 0.0), 100.0)

    def _detect_outliers(
        self,
        responses: List[CouncilResponse],
        response_scores: Dict[str, float]
    ) -> List[str]:
        """
        Detect outlier responses that differ significantly from consensus.

        Args:
            responses: List of council responses
            response_scores: Aggregate review scores

        Returns:
            List of dissenting opinion texts
        """
        if len(responses) < 3:
            return []  # Need at least 3 for outlier detection

        outliers = []

        # Calculate mean and std dev of review scores
        scores = list(response_scores.values())
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5

        # Responses with scores >2 std devs from mean
        for response in responses:
            score = response_scores.get(str(response.id), 5.0)

            if abs(score - avg_score) > 2 * std_dev:
                # Extract just the recommendation part
                rec_match = re.search(
                    r'RECOMMENDATION:\s*(.+?)(?=\nREASONING:|$)',
                    response.response_text,
                    re.IGNORECASE | re.DOTALL
                )
                if rec_match:
                    outliers.append(rec_match.group(1).strip())

        return outliers

    def _format_responses_for_synthesis(
        self,
        responses: List[CouncilResponse],
        response_scores: Dict[str, float]
    ) -> str:
        """Format responses for synthesis prompt."""
        lines = []

        for i, response in enumerate(responses, 1):
            score = response_scores.get(str(response.id), 5.0)
            weight = self.models.get(response.model_name, {}).get("weight", 1.0)

            lines.append(f"\n--- Response {i} ---")
            lines.append(f"Weight: {weight}")
            lines.append(f"Confidence: {response.confidence:.0%}")
            lines.append(f"Peer Review Score: {score:.1f}/10")
            lines.append(f"Content: {response.response_text[:500]}...")

        return "\n".join(lines)

    def _format_review_summary(self, reviews: List[CouncilReview]) -> str:
        """Format review summary for synthesis prompt."""
        if not reviews:
            return "(No reviews available)"

        total_reviews = len(reviews)
        avg_accuracy = sum(r.accuracy_score for r in reviews) / total_reviews
        avg_completeness = sum(r.completeness_score for r in reviews) / total_reviews
        avg_clarity = sum(r.clarity_score for r in reviews) / total_reviews
        avg_feasibility = sum(r.feasibility_score for r in reviews) / total_reviews

        return f"""
Total Reviews: {total_reviews}
Average Accuracy: {avg_accuracy:.1f}/10
Average Completeness: {avg_completeness:.1f}/10
Average Clarity: {avg_clarity:.1f}/10
Average Feasibility: {avg_feasibility:.1f}/10
Overall Average: {(avg_accuracy + avg_completeness + avg_clarity + avg_feasibility) / 4:.1f}/10
"""

    def _extract_decision(self, decision_text: str) -> Optional[str]:
        """Extract final decision from synthesis text."""
        match = re.search(
            r'FINAL DECISION:\s*(.+?)(?=\n(?:REASONING|CONFIDENCE|KEY CONSIDERATIONS)|$)',
            decision_text,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            return match.group(1).strip()

        return None

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def check_ollama_health(self) -> Dict[str, bool]:
        """
        Check which Ollama models are available.

        Returns:
            Dict mapping model names to availability (True/False)
        """
        health = {}

        async with aiohttp.ClientSession() as session:
            for model_name in self.models.keys():
                try:
                    async with session.post(
                        f"{self.ollama_url}/api/generate",
                        json={
                            "model": model_name,
                            "prompt": "test",
                            "stream": False
                        },
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        health[model_name] = response.status == 200
                except Exception:
                    health[model_name] = False

        return health
