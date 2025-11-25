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
        ollama_base_url: str = "http://localhost:11434"
    ):
        self.db = db_session
        self.ollama_url = ollama_base_url

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
                    timeout=aiohttp.ClientTimeout(total=120)  # 2 min timeout
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
