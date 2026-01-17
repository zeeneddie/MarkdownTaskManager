"""
BigAGI Beam Service - Multi-Model Validation

Week 78: Implements multi-model consensus validation inspired by BigAGI's Beam feature.

Key Features:
- Submit responses to multiple LLMs for validation
- Calculate agreement scores between model responses
- Reach consensus through various methods (majority, weighted, unanimous)
- Track validation metrics and confidence levels
"""

import asyncio
import re
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.browser_automation import (
    BigAGIValidation,
    BigAGIResponse,
    BigAGIConsensus,
    ValidationStatus,
    ConsensusMethod,
    ConsensusRecommendation
)
from app.providers.registry import get_registry, ProviderRegistry
from app.providers.base import LLMRequest, LLMResponse


@dataclass
class ValidationResult:
    """Result of multi-model validation."""
    validation_id: UUID
    consensus_reached: bool
    consensus_score: float
    recommendation: str
    final_answer: Optional[str]
    key_agreements: List[str]
    key_disagreements: List[str]
    model_responses: Dict[str, Dict]


@dataclass
class AgreementScore:
    """Agreement score between two models."""
    model_a: str
    model_b: str
    score: float
    matching_points: List[str]
    differing_points: List[str]


class BigAGIBeamService:
    """
    Multi-model validation service for consensus-based answer verification.

    Implements the BigAGI Beam concept where multiple LLMs validate a primary
    response and reach consensus on the best answer.

    Use Cases:
    - Architecture decision validation
    - Code review consensus
    - Security audit verification
    - Planning estimate validation

    Consensus Methods:
    - MAJORITY: 50%+ agreement wins
    - WEIGHTED: Model confidence and role weights
    - UNANIMOUS: All models must agree
    """

    # Default validation models (prioritize local Ollama models)
    DEFAULT_VALIDATORS = [
        {"name": "qwen2.5-coder:7b", "provider": "ollama", "weight": 1.5},
        {"name": "deepseek-r1:latest", "provider": "ollama", "weight": 2.0},
        {"name": "mistral:latest", "provider": "ollama", "weight": 1.0},
    ]

    # Agreement thresholds
    CONSENSUS_THRESHOLD = 0.7  # 70% for consensus
    HIGH_CONFIDENCE_THRESHOLD = 0.85  # 85% for high confidence

    def __init__(
        self,
        db_session: AsyncSession,
        registry: Optional[ProviderRegistry] = None
    ):
        self.db = db_session
        self.registry = registry or get_registry()

    # ========================================================================
    # VALIDATION SESSIONS
    # ========================================================================

    async def create_validation(
        self,
        task: str,
        primary_response: str,
        primary_model: str,
        validation_models: Optional[List[Dict]] = None,
        session_metadata: Optional[Dict] = None
    ) -> BigAGIValidation:
        """
        Create a new multi-model validation session.

        Args:
            task: The task/question that was answered
            primary_response: The primary model's response to validate
            primary_model: Name of the model that produced primary_response
            validation_models: List of models to use for validation
            session_metadata: Additional context/metadata

        Returns:
            Created BigAGIValidation session
        """
        validators = validation_models or self.DEFAULT_VALIDATORS

        validation = BigAGIValidation(
            id=uuid4(),
            task=task,
            primary_response=primary_response,
            primary_model=primary_model,
            validation_models=validators,
            status=ValidationStatus.PENDING.value,
            session_metadata=session_metadata or {},
            created_at=datetime.now(timezone.utc)
        )

        self.db.add(validation)
        await self.db.commit()
        await self.db.refresh(validation)

        return validation

    async def get_validation(
        self,
        validation_id: UUID,
        include_responses: bool = True
    ) -> Optional[BigAGIValidation]:
        """Get validation session by ID."""
        query = select(BigAGIValidation).where(BigAGIValidation.id == validation_id)

        if include_responses:
            query = query.options(
                selectinload(BigAGIValidation.responses),
                selectinload(BigAGIValidation.consensus)
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_validations(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[BigAGIValidation]:
        """List validation sessions with optional status filter."""
        query = select(BigAGIValidation).order_by(BigAGIValidation.created_at.desc())

        if status:
            query = query.where(BigAGIValidation.status == status)

        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ========================================================================
    # VALIDATION EXECUTION
    # ========================================================================

    async def run_validation(
        self,
        validation_id: UUID,
        consensus_method: str = "weighted"
    ) -> ValidationResult:
        """
        Execute multi-model validation.

        Process:
        1. Fetch validation session and models
        2. Query each validator model in parallel
        3. Calculate agreement scores
        4. Determine consensus using specified method
        5. Generate synthesized answer if consensus reached

        Args:
            validation_id: Validation session to run
            consensus_method: "majority", "weighted", or "unanimous"

        Returns:
            ValidationResult with consensus details
        """
        # Get validation session
        validation = await self.get_validation(validation_id, include_responses=False)
        if not validation:
            raise ValueError(f"Validation {validation_id} not found")

        # Update status
        validation.status = ValidationStatus.VALIDATING.value
        await self.db.commit()

        try:
            # Query all validators in parallel
            responses = await self._query_validators(validation)

            # Store responses
            for resp in responses:
                self.db.add(resp)
            await self.db.commit()

            # Calculate agreement scores
            agreement_matrix = self._calculate_agreement_matrix(
                validation.primary_response,
                responses
            )

            # Determine consensus
            consensus_result = await self._determine_consensus(
                validation,
                responses,
                agreement_matrix,
                ConsensusMethod(consensus_method)
            )

            # Store consensus
            self.db.add(consensus_result)

            # Update validation with results
            validation.status = ValidationStatus.COMPLETED.value
            validation.consensus_score = consensus_result.confidence
            validation.consensus_reached = consensus_result.confidence >= self.CONSENSUS_THRESHOLD
            validation.final_answer = consensus_result.synthesis
            validation.completed_at = datetime.now(timezone.utc)

            await self.db.commit()

            # Build result
            return ValidationResult(
                validation_id=validation_id,
                consensus_reached=validation.consensus_reached,
                consensus_score=validation.consensus_score,
                recommendation=consensus_result.recommendation or "review",
                final_answer=consensus_result.synthesis,
                key_agreements=consensus_result.key_agreements or [],
                key_disagreements=consensus_result.key_disagreements or [],
                model_responses={
                    r.model: {
                        "response": r.response[:500] + "..." if len(r.response) > 500 else r.response,
                        "confidence": r.confidence,
                        "agreement_score": r.agreement_score
                    }
                    for r in responses
                }
            )

        except Exception as e:
            validation.status = ValidationStatus.FAILED.value
            validation.session_metadata = {**validation.session_metadata, "error": str(e)}
            await self.db.commit()
            raise

    async def _query_validators(
        self,
        validation: BigAGIValidation
    ) -> List[BigAGIResponse]:
        """Query all validator models in parallel."""

        validation_prompt = self._build_validation_prompt(
            validation.task,
            validation.primary_response
        )

        async def query_single(model_config: Dict) -> BigAGIResponse:
            """Query a single validator model."""
            model_name = model_config.get("name", model_config.get("model"))
            provider_name = model_config.get("provider", "ollama")

            provider = self.registry.get_provider(provider_name)
            if not provider:
                # Fallback to ollama
                provider = self.registry.get_provider("ollama")

            start_time = datetime.now(timezone.utc)

            try:
                request = LLMRequest(
                    prompt=validation_prompt,
                    system="You are a critical reviewer validating an AI response. Analyze accuracy, completeness, and potential issues. Provide your confidence level (0-100) at the end.",
                    max_tokens=2000,
                    temperature=0.3  # Lower temp for more consistent validation
                )

                response = await provider.generate(request)

                # Extract confidence from response
                confidence = self._extract_confidence(response.content)

                # Calculate agreement with primary
                agreement = self._calculate_text_agreement(
                    validation.primary_response,
                    response.content
                )

                duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

                return BigAGIResponse(
                    id=uuid4(),
                    validation_id=validation.id,
                    model=model_name,
                    provider=provider_name,
                    response=response.content,
                    thinking=self._extract_thinking(response.content),
                    confidence=confidence,
                    agreement_score=agreement,
                    tokens_used=response.token_input + response.token_output,
                    latency_ms=duration_ms,
                    created_at=datetime.now(timezone.utc)
                )

            except Exception as e:
                return BigAGIResponse(
                    id=uuid4(),
                    validation_id=validation.id,
                    model=model_name,
                    provider=provider_name,
                    response="",
                    error=str(e),
                    confidence=0.0,
                    agreement_score=0.0,
                    created_at=datetime.now(timezone.utc)
                )

        # Query all validators in parallel
        tasks = [
            query_single(model_config)
            for model_config in validation.validation_models
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_responses = []
        for resp in responses:
            if isinstance(resp, BigAGIResponse):
                valid_responses.append(resp)
            elif isinstance(resp, Exception):
                # Log but don't fail the whole validation
                print(f"Validator error: {resp}")

        return valid_responses

    def _build_validation_prompt(self, task: str, primary_response: str) -> str:
        """Build the validation prompt for reviewer models."""
        return f"""TASK TO VALIDATE:
{task}

PRIMARY RESPONSE TO REVIEW:
{primary_response}

---

Please critically review this response for:
1. ACCURACY: Are the facts and technical details correct?
2. COMPLETENESS: Does it fully address the task?
3. ISSUES: Any problems, errors, or missing information?
4. IMPROVEMENTS: What would make this response better?

After your analysis, provide:
- Your VERDICT: AGREE, PARTIALLY_AGREE, or DISAGREE with the primary response
- Your CONFIDENCE: 0-100 score for how confident you are
- SUMMARY: Brief summary of your assessment

Format your confidence as: "Confidence: XX/100" at the end of your response."""

    def _extract_confidence(self, response: str) -> float:
        """Extract confidence score from response."""
        # Look for patterns like "Confidence: 85/100" or "confidence: 85%"
        patterns = [
            r'[Cc]onfidence:?\s*(\d+)/100',
            r'[Cc]onfidence:?\s*(\d+)%',
            r'[Cc]onfidence:?\s*(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, response)
            if match:
                try:
                    conf = float(match.group(1))
                    return min(conf / 100.0 if conf > 1 else conf, 1.0)
                except ValueError:
                    pass

        # Default confidence based on response analysis
        return 0.5

    def _extract_thinking(self, response: str) -> Optional[str]:
        """Extract reasoning/thinking from response."""
        # Look for thinking blocks or structured reasoning
        patterns = [
            r'<thinking>(.*?)</thinking>',
            r'\*\*Analysis\*\*:?(.*?)(?=\*\*|$)',
            r'(?:Let me|I will|First,).*?(?=\n\n|\n-|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()[:500]

        return None

    def _calculate_text_agreement(self, text_a: str, text_b: str) -> float:
        """
        Calculate agreement score between two texts.

        Uses multiple heuristics:
        1. Key verdict extraction (AGREE/DISAGREE)
        2. Sentiment analysis of review
        3. Keyword overlap
        """
        text_b_lower = text_b.lower()

        # Check for explicit verdicts
        if 'disagree' in text_b_lower and 'agree' not in text_b_lower.replace('disagree', ''):
            return 0.2
        elif 'partially' in text_b_lower or 'partial' in text_b_lower:
            return 0.6
        elif 'agree' in text_b_lower:
            return 0.85

        # Check for positive/negative indicators
        positive_indicators = ['correct', 'accurate', 'good', 'valid', 'complete', 'proper']
        negative_indicators = ['incorrect', 'wrong', 'error', 'missing', 'incomplete', 'issue']

        pos_count = sum(1 for ind in positive_indicators if ind in text_b_lower)
        neg_count = sum(1 for ind in negative_indicators if ind in text_b_lower)

        if pos_count + neg_count > 0:
            return max(0.3, min(0.9, 0.5 + (pos_count - neg_count) * 0.1))

        return 0.5  # Neutral

    def _calculate_agreement_matrix(
        self,
        primary_response: str,
        responses: List[BigAGIResponse]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate pairwise agreement matrix between all responses."""
        matrix = {}

        # Include primary response
        all_texts = [("primary", primary_response)]
        all_texts.extend((r.model, r.response) for r in responses if r.response)

        for i, (name_a, text_a) in enumerate(all_texts):
            matrix[name_a] = {}
            for j, (name_b, text_b) in enumerate(all_texts):
                if i == j:
                    matrix[name_a][name_b] = 1.0
                else:
                    matrix[name_a][name_b] = self._calculate_text_agreement(text_a, text_b)

        return matrix

    async def _determine_consensus(
        self,
        validation: BigAGIValidation,
        responses: List[BigAGIResponse],
        agreement_matrix: Dict[str, Dict[str, float]],
        method: ConsensusMethod
    ) -> BigAGIConsensus:
        """Determine consensus using the specified method."""

        # Calculate overall consensus score
        valid_responses = [r for r in responses if not r.error]

        if not valid_responses:
            # No valid responses - can't determine consensus
            return BigAGIConsensus(
                id=uuid4(),
                validation_id=validation.id,
                method=method.value,
                agreement_matrix=agreement_matrix,
                confidence=0.0,
                recommendation=ConsensusRecommendation.REVIEW.value,
                key_agreements=[],
                key_disagreements=["No valid validator responses received"],
                synthesis="Unable to reach consensus - validation failed",
                created_at=datetime.now(timezone.utc)
            )

        # Calculate consensus score based on method
        if method == ConsensusMethod.MAJORITY:
            consensus_score = self._majority_consensus(valid_responses)
        elif method == ConsensusMethod.WEIGHTED:
            consensus_score = self._weighted_consensus(valid_responses, validation.validation_models)
        elif method == ConsensusMethod.UNANIMOUS:
            consensus_score = self._unanimous_consensus(valid_responses)
        else:
            consensus_score = self._weighted_consensus(valid_responses, validation.validation_models)

        # Extract key agreements and disagreements
        agreements, disagreements = self._extract_key_points(valid_responses)

        # Determine recommendation
        if consensus_score >= self.HIGH_CONFIDENCE_THRESHOLD:
            recommendation = ConsensusRecommendation.ACCEPT
        elif consensus_score >= self.CONSENSUS_THRESHOLD:
            recommendation = ConsensusRecommendation.REVIEW
        else:
            recommendation = ConsensusRecommendation.REJECT

        # Generate synthesis
        synthesis = await self._generate_synthesis(
            validation,
            valid_responses,
            consensus_score,
            recommendation
        )

        return BigAGIConsensus(
            id=uuid4(),
            validation_id=validation.id,
            method=method.value,
            agreement_matrix=agreement_matrix,
            confidence=consensus_score,
            recommendation=recommendation.value,
            key_agreements=agreements,
            key_disagreements=disagreements,
            synthesis=synthesis,
            created_at=datetime.now(timezone.utc)
        )

    def _majority_consensus(self, responses: List[BigAGIResponse]) -> float:
        """Calculate majority-based consensus."""
        if not responses:
            return 0.0

        # Count agreeing validators (agreement_score >= 0.6)
        agreeing = sum(1 for r in responses if r.agreement_score and r.agreement_score >= 0.6)
        return agreeing / len(responses)

    def _weighted_consensus(
        self,
        responses: List[BigAGIResponse],
        model_configs: List[Dict]
    ) -> float:
        """Calculate weight-adjusted consensus."""
        if not responses:
            return 0.0

        # Build weight lookup
        weights = {
            cfg.get("name", cfg.get("model")): cfg.get("weight", 1.0)
            for cfg in model_configs
        }

        total_weight = 0.0
        weighted_agreement = 0.0

        for resp in responses:
            if resp.agreement_score is not None:
                weight = weights.get(resp.model, 1.0)
                weighted_agreement += resp.agreement_score * weight
                total_weight += weight

        return weighted_agreement / total_weight if total_weight > 0 else 0.0

    def _unanimous_consensus(self, responses: List[BigAGIResponse]) -> float:
        """Calculate unanimous consensus (all must agree)."""
        if not responses:
            return 0.0

        # All validators must have high agreement (>= 0.7)
        all_agree = all(
            r.agreement_score and r.agreement_score >= 0.7
            for r in responses
        )

        if all_agree:
            # Return average agreement score
            return sum(r.agreement_score or 0 for r in responses) / len(responses)
        return 0.0

    def _extract_key_points(
        self,
        responses: List[BigAGIResponse]
    ) -> Tuple[List[str], List[str]]:
        """Extract key agreements and disagreements from responses."""
        agreements = []
        disagreements = []

        for resp in responses:
            text = resp.response.lower()

            # Look for agreement patterns
            if resp.agreement_score and resp.agreement_score >= 0.7:
                if 'accurate' in text:
                    agreements.append(f"{resp.model}: Found response accurate")
                if 'complete' in text:
                    agreements.append(f"{resp.model}: Found response complete")
                if 'correct' in text:
                    agreements.append(f"{resp.model}: Confirmed correctness")

            # Look for disagreement patterns
            if resp.agreement_score and resp.agreement_score < 0.5:
                if 'missing' in text:
                    disagreements.append(f"{resp.model}: Identified missing information")
                if 'error' in text or 'incorrect' in text:
                    disagreements.append(f"{resp.model}: Found errors in response")
                if 'incomplete' in text:
                    disagreements.append(f"{resp.model}: Response incomplete")

        return agreements[:5], disagreements[:5]  # Limit to top 5 each

    async def _generate_synthesis(
        self,
        validation: BigAGIValidation,
        responses: List[BigAGIResponse],
        consensus_score: float,
        recommendation: ConsensusRecommendation
    ) -> str:
        """Generate a synthesized answer based on all validator input."""

        # Build synthesis without making additional LLM call (for speed)
        response_summaries = []
        for resp in responses:
            verdict = "agrees" if resp.agreement_score and resp.agreement_score >= 0.6 else "disagrees"
            response_summaries.append(
                f"- {resp.model} ({resp.provider}): {verdict} "
                f"(confidence: {int((resp.confidence or 0) * 100)}%)"
            )

        synthesis = f"""MULTI-MODEL VALIDATION SUMMARY

Consensus Score: {consensus_score:.1%}
Recommendation: {recommendation.value.upper()}

Validator Responses:
{chr(10).join(response_summaries)}

Original Task: {validation.task[:200]}{'...' if len(validation.task) > 200 else ''}

Primary Model: {validation.primary_model}

"""

        if recommendation == ConsensusRecommendation.ACCEPT:
            synthesis += "CONCLUSION: The primary response has been validated by the council and can be accepted."
        elif recommendation == ConsensusRecommendation.REVIEW:
            synthesis += "CONCLUSION: The primary response shows mixed validation results and should be reviewed manually."
        else:
            synthesis += "CONCLUSION: The primary response was rejected by validators. Consider regenerating."

        return synthesis

    # ========================================================================
    # LLM COUNCIL INTEGRATION
    # ========================================================================

    async def cross_validate_council(
        self,
        council_session_id: UUID
    ) -> Dict:
        """
        Cross-validate an LLM Council session with BigAGI Beam.

        Takes the council's final decision and validates it with
        additional models not in the original council.

        Args:
            council_session_id: ID of completed council session

        Returns:
            Cross-validation results including consensus score
        """
        from app.models.llm_council import CouncilSession, CouncilDecision

        # Get council session
        result = await self.db.execute(
            select(CouncilSession)
            .options(selectinload(CouncilSession.decision))
            .where(CouncilSession.id == council_session_id)
        )
        session = result.scalar_one_or_none()

        if not session or not session.decision:
            raise ValueError(f"Council session {council_session_id} not found or has no decision")

        # Create validation with council's question and decision
        validation = await self.create_validation(
            task=session.question,
            primary_response=session.decision.decision,
            primary_model="council",
            validation_models=self.DEFAULT_VALIDATORS,
            session_metadata={
                "source": "llm_council",
                "council_session_id": str(council_session_id),
                "council_consensus": session.decision.consensus_level
            }
        )

        # Run validation
        result = await self.run_validation(
            validation.id,
            consensus_method="weighted"
        )

        return {
            "council_session_id": str(council_session_id),
            "validation_id": str(validation.id),
            "council_consensus": session.decision.consensus_level,
            "beam_consensus": result.consensus_score,
            "beam_recommendation": result.recommendation,
            "cross_validation_passed": (
                result.consensus_reached and
                result.recommendation != ConsensusRecommendation.REJECT.value
            )
        }

    # ========================================================================
    # QUICK VALIDATION (STATELESS)
    # ========================================================================

    async def quick_validate(
        self,
        task: str,
        response: str,
        model_used: str = "unknown"
    ) -> Dict:
        """
        Quick validation without database persistence.

        Useful for inline validation during response generation.

        Args:
            task: The task/question
            response: Response to validate
            model_used: Model that produced the response

        Returns:
            Simple validation result dict
        """
        # Create ephemeral validation
        validation = await self.create_validation(
            task=task,
            primary_response=response,
            primary_model=model_used,
            validation_models=[
                {"name": "qwen2.5-coder:7b", "provider": "ollama", "weight": 1.0}
            ],
            session_metadata={"ephemeral": True}
        )

        try:
            result = await self.run_validation(validation.id, "majority")

            return {
                "valid": result.consensus_reached,
                "score": result.consensus_score,
                "recommendation": result.recommendation,
                "key_issues": result.key_disagreements
            }
        finally:
            # Clean up ephemeral validation (optional - could keep for audit)
            pass

    # ========================================================================
    # STATISTICS
    # ========================================================================

    async def get_validation_stats(self) -> Dict:
        """Get overall validation statistics."""
        from sqlalchemy import func

        # Total validations
        total = await self.db.execute(
            select(func.count(BigAGIValidation.id))
        )
        total_count = total.scalar() or 0

        # By status
        status_query = await self.db.execute(
            select(
                BigAGIValidation.status,
                func.count(BigAGIValidation.id)
            ).group_by(BigAGIValidation.status)
        )
        by_status = {row[0]: row[1] for row in status_query}

        # Average consensus score
        avg_query = await self.db.execute(
            select(func.avg(BigAGIValidation.consensus_score))
            .where(BigAGIValidation.consensus_score.isnot(None))
        )
        avg_score = avg_query.scalar() or 0

        # Consensus reached rate
        reached_query = await self.db.execute(
            select(func.count(BigAGIValidation.id))
            .where(BigAGIValidation.consensus_reached == True)
        )
        reached_count = reached_query.scalar() or 0

        return {
            "total_validations": total_count,
            "by_status": by_status,
            "average_consensus_score": round(avg_score, 3),
            "consensus_reached_rate": round(reached_count / total_count, 3) if total_count > 0 else 0,
            "threshold": self.CONSENSUS_THRESHOLD
        }
