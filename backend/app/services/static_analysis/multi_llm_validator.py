# backend/app/services/static_analysis/multi_llm_validator.py
"""
Multi-LLM Validator - Cross-validates business rules with multiple LLM providers.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline (Phase 2.5)

Features:
- Multi-provider consensus for high-confidence validation
- Voting mechanism for rule classification
- Tier-aware provider selection
- Aggregated confidence scoring

Use Cases:
1. Cross-Validation - 3 LLMs must agree for confidence boost (+10-15%)
2. Type Consensus - Multiple LLMs vote on rule classification
3. Premium Synthesis - Claude Opus final review for PREMIUM tier
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from collections import Counter

from .extraction_models import (
    BusinessRule,
    RuleType,
    ExtractionTier,
)
from .llm_classifier import (
    LLMRuleClassifier,
    ClassificationResponse,
    ClassificationResult,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationVote:
    """A vote from a single LLM provider."""
    provider: str
    is_business_rule: bool
    suggested_type: Optional[RuleType] = None
    confidence_boost: float = 0.0
    natural_language: Optional[str] = None


@dataclass
class ConsensusResult:
    """Result of multi-LLM consensus validation."""
    is_business_rule: bool
    consensus_reached: bool           # Did LLMs agree?
    agreement_ratio: float            # 0.0-1.0 how much they agreed
    final_type: Optional[RuleType] = None
    final_confidence_boost: float = 0.0
    final_natural_language: Optional[str] = None
    votes: List[ValidationVote] = field(default_factory=list)
    providers_used: List[str] = field(default_factory=list)
    total_tokens: int = 0
    total_cost_cents: float = 0.0


# Minimum agreement ratio for consensus
CONSENSUS_THRESHOLD = 0.67  # 2/3 must agree


# Tier to providers mapping for validation
TIER_VALIDATION_PROVIDERS: Dict[ExtractionTier, List[str]] = {
    ExtractionTier.FREE: [],
    ExtractionTier.BASIC: ["ollama"],
    ExtractionTier.STANDARD: ["ollama", "groq", "gemini"],
    ExtractionTier.PROFESSIONAL: ["ollama", "groq", "gemini", "openai"],
    ExtractionTier.PREMIUM: ["ollama", "groq", "gemini", "openai", "anthropic"],
}


class MultiLLMValidator:
    """
    Validates business rules using multiple LLM providers.

    Provides:
    - Multi-provider cross-validation
    - Consensus-based classification
    - Confidence boost aggregation
    - Tier-aware provider selection
    """

    def __init__(
        self,
        extraction_tier: ExtractionTier = ExtractionTier.PROFESSIONAL,
        min_providers: int = 2,
        max_providers: int = 5,
    ):
        """
        Initialize the validator.

        Args:
            extraction_tier: Customer tier determining available providers
            min_providers: Minimum providers needed for validation
            max_providers: Maximum providers to use
        """
        self.extraction_tier = extraction_tier
        self.min_providers = min_providers
        self.max_providers = max_providers
        self._registry = None

    def _get_registry(self):
        """Lazy load provider registry."""
        if self._registry is None:
            try:
                from app.providers.registry import get_registry
                self._registry = get_registry()
            except ImportError:
                logger.warning("Provider registry not available")
        return self._registry

    def get_available_providers(self) -> List[str]:
        """Get available providers for current tier."""
        providers = TIER_VALIDATION_PROVIDERS.get(self.extraction_tier, [])
        return providers[:self.max_providers]

    async def validate_rule(
        self,
        rule: BusinessRule,
    ) -> ConsensusResult:
        """
        Validate a business rule using multiple LLM providers.

        Args:
            rule: BusinessRule to validate

        Returns:
            ConsensusResult with voting results
        """
        providers = self.get_available_providers()

        if len(providers) < self.min_providers:
            logger.debug(
                f"Not enough providers ({len(providers)}) for multi-LLM validation"
            )
            return ConsensusResult(
                is_business_rule=True,  # Assume true if can't validate
                consensus_reached=False,
                agreement_ratio=0.0,
            )

        # Create classifiers for each provider and run in parallel
        tasks = []
        for provider_name in providers:
            classifier = LLMRuleClassifier(extraction_tier=self.extraction_tier)
            task = self._classify_with_provider(classifier, rule, provider_name)
            tasks.append(task)

        # Run all classifications in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect votes
        votes: List[ValidationVote] = []
        total_tokens = 0
        total_cost = 0.0

        for provider_name, result in zip(providers, results):
            if isinstance(result, Exception):
                logger.warning(f"Provider {provider_name} failed: {result}")
                continue

            if result.result == ClassificationResult.ERROR:
                continue

            votes.append(ValidationVote(
                provider=provider_name,
                is_business_rule=result.is_business_rule,
                suggested_type=result.suggested_type,
                confidence_boost=result.confidence_boost,
                natural_language=result.natural_language,
            ))
            total_tokens += result.tokens_used
            total_cost += result.cost_cents

        if not votes:
            return ConsensusResult(
                is_business_rule=True,
                consensus_reached=False,
                agreement_ratio=0.0,
                providers_used=providers,
            )

        # Calculate consensus
        return self._calculate_consensus(
            votes,
            providers,
            total_tokens,
            total_cost,
        )

    async def _classify_with_provider(
        self,
        classifier: LLMRuleClassifier,
        rule: BusinessRule,
        provider_name: str,
    ) -> ClassificationResponse:
        """Run classification with a specific provider."""
        # Force the classifier to use this specific provider
        prefer_local = provider_name == "ollama"
        return await classifier.classify_rule(rule, prefer_local=prefer_local)

    def _calculate_consensus(
        self,
        votes: List[ValidationVote],
        providers: List[str],
        total_tokens: int,
        total_cost: float,
    ) -> ConsensusResult:
        """Calculate consensus from votes."""
        n_votes = len(votes)
        if n_votes == 0:
            return ConsensusResult(
                is_business_rule=True,
                consensus_reached=False,
                agreement_ratio=0.0,
            )

        # Vote on is_business_rule
        rule_votes = [v.is_business_rule for v in votes]
        true_votes = sum(1 for v in rule_votes if v)
        agreement_ratio = max(true_votes, n_votes - true_votes) / n_votes

        # Majority wins
        is_business_rule = true_votes > n_votes / 2

        # Vote on rule type
        type_votes = [v.suggested_type for v in votes if v.suggested_type]
        final_type = None
        if type_votes:
            type_counter = Counter(type_votes)
            final_type = type_counter.most_common(1)[0][0]

        # Average confidence boost
        boosts = [v.confidence_boost for v in votes if v.confidence_boost > 0]
        final_boost = sum(boosts) / len(boosts) if boosts else 0.0

        # Apply consensus bonus if agreement is high
        if agreement_ratio >= CONSENSUS_THRESHOLD:
            final_boost = min(final_boost + 0.05, 0.15)  # Bonus for consensus

        # Pick best natural language description
        nl_descriptions = [v.natural_language for v in votes if v.natural_language]
        final_nl = max(nl_descriptions, key=len) if nl_descriptions else None

        consensus_reached = agreement_ratio >= CONSENSUS_THRESHOLD

        return ConsensusResult(
            is_business_rule=is_business_rule,
            consensus_reached=consensus_reached,
            agreement_ratio=agreement_ratio,
            final_type=final_type,
            final_confidence_boost=final_boost,
            final_natural_language=final_nl,
            votes=votes,
            providers_used=[v.provider for v in votes],
            total_tokens=total_tokens,
            total_cost_cents=total_cost,
        )

    async def validate_batch(
        self,
        rules: List[BusinessRule],
        confidence_threshold: float = 0.75,
        max_rules: int = 20,
    ) -> List[Tuple[BusinessRule, ConsensusResult]]:
        """
        Validate a batch of rules with multi-LLM consensus.

        Args:
            rules: List of BusinessRules to validate
            confidence_threshold: Only validate rules below this confidence
            max_rules: Maximum rules to validate (cost control)

        Returns:
            List of (rule, consensus) tuples
        """
        # Filter to candidates
        candidates = [r for r in rules if r.confidence < confidence_threshold]
        candidates = candidates[:max_rules]

        logger.info(
            f"Multi-LLM validating {len(candidates)} rules "
            f"with {len(self.get_available_providers())} providers"
        )

        results = []
        for rule in candidates:
            consensus = await self.validate_rule(rule)
            results.append((rule, consensus))

            # Apply consensus results
            if consensus.consensus_reached:
                if not consensus.is_business_rule:
                    rule.confidence = 0.0
                    rule.validated_by_llm = True
                    rule.llm_validation_result = "rejected_consensus"
                else:
                    rule.confidence = min(
                        rule.confidence + consensus.final_confidence_boost,
                        0.95
                    )
                    rule.validated_by_llm = True
                    rule.llm_validation_result = "confirmed_consensus"
                    if consensus.final_type:
                        rule.rule_type = consensus.final_type
                    if consensus.final_natural_language:
                        rule.natural_language = consensus.final_natural_language

        confirmed = sum(
            1 for _, c in results
            if c.consensus_reached and c.is_business_rule
        )
        rejected = sum(
            1 for _, c in results
            if c.consensus_reached and not c.is_business_rule
        )
        no_consensus = sum(
            1 for _, c in results if not c.consensus_reached
        )

        logger.info(
            f"Multi-LLM validation: {confirmed} confirmed, "
            f"{rejected} rejected, {no_consensus} no consensus"
        )

        return results


class PremiumSynthesizer:
    """
    Premium-tier final synthesis using Claude Opus.

    For PREMIUM tier customers, provides a final review and synthesis
    of all business rules by the most capable LLM.
    """

    SYNTHESIS_PROMPT = """You are a senior business analyst reviewing extracted business rules.

Review the following business rules extracted from legacy code and:
1. Verify they are genuine business rules (not technical code)
2. Improve their natural language descriptions
3. Suggest any rules that should be merged or split
4. Identify any missing rules based on context

PROJECT: {project_name}
LANGUAGE: {language}
TOTAL RULES: {rule_count}

RULES TO REVIEW:
{rules_summary}

Provide your synthesis in JSON:
{{
    "reviewed_rules": [
        {{
            "id": "BR-001",
            "is_valid": true,
            "improved_description": "Clear business rule description",
            "confidence_adjustment": 0.05,
            "notes": "Any observations"
        }}
    ],
    "merge_suggestions": [
        {{
            "rule_ids": ["BR-010", "BR-011"],
            "reason": "These rules represent the same authorization check"
        }}
    ],
    "missing_rules": [
        {{
            "suggested_rule": "Description of potentially missing rule",
            "location_hint": "Where in the code to look"
        }}
    ],
    "overall_quality": "Assessment of the extraction quality"
}}

Only respond with JSON."""

    def __init__(self):
        self._registry = None

    def _get_registry(self):
        if self._registry is None:
            try:
                from app.providers.registry import get_registry
                self._registry = get_registry()
            except ImportError:
                pass
        return self._registry

    async def synthesize(
        self,
        rules: List[BusinessRule],
        project_name: str = "Unknown",
    ) -> Dict[str, Any]:
        """
        Perform premium synthesis of business rules.

        Args:
            rules: All extracted business rules
            project_name: Project name for context

        Returns:
            Synthesis result dict
        """
        registry = self._get_registry()
        if not registry:
            return {"error": "Provider registry not available"}

        # Use Claude Opus for synthesis
        provider = registry.get_provider("anthropic")
        if not provider:
            return {"error": "Anthropic provider not available"}

        # Build rules summary (limit to 50 for token efficiency)
        sample_rules = rules[:50]
        rules_summary = "\n\n".join([
            f"ID: {r.id}\n"
            f"Type: {r.rule_type.value}\n"
            f"Condition: {r.condition}\n"
            f"Action: {r.action}\n"
            f"NL: {r.natural_language}\n"
            f"Confidence: {r.confidence:.0%}\n"
            f"Source: {r.source_file}:{r.source_lines[0]}"
            for r in sample_rules
        ])

        language = rules[0].language.value if rules and rules[0].language else "unknown"

        prompt = self.SYNTHESIS_PROMPT.format(
            project_name=project_name,
            language=language,
            rule_count=len(rules),
            rules_summary=rules_summary,
        )

        try:
            from app.providers.base import LLMRequest

            request = LLMRequest(
                prompt=prompt,
                max_tokens=4000,
                temperature=0.3,
            )

            response = await provider.generate(request)

            if not response.success:
                return {"error": response.error}

            # Parse JSON response
            import json
            import re

            json_match = re.search(r'\{[\s\S]*\}', response.content)
            if json_match:
                result = json.loads(json_match.group())
                result["tokens_used"] = response.token_input + response.token_output
                result["cost_cents"] = response.cost_cents
                return result

            return {"error": "Could not parse synthesis response"}

        except Exception as e:
            logger.error(f"Premium synthesis failed: {e}")
            return {"error": str(e)}


# Convenience functions
async def multi_llm_validate(
    rule: BusinessRule,
    tier: ExtractionTier = ExtractionTier.PROFESSIONAL,
) -> ConsensusResult:
    """
    Validate a single rule with multiple LLMs.

    Args:
        rule: BusinessRule to validate
        tier: Customer extraction tier

    Returns:
        ConsensusResult
    """
    validator = MultiLLMValidator(extraction_tier=tier)
    return await validator.validate_rule(rule)


async def premium_synthesize(
    rules: List[BusinessRule],
    project_name: str = "Unknown",
) -> Dict[str, Any]:
    """
    Perform premium synthesis on business rules.

    Args:
        rules: All extracted rules
        project_name: Project name

    Returns:
        Synthesis result
    """
    synthesizer = PremiumSynthesizer()
    return await synthesizer.synthesize(rules, project_name)
