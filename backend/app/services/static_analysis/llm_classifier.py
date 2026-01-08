# backend/app/services/static_analysis/llm_classifier.py
"""
LLM Rule Classifier - Classifies ambiguous regex-extracted business rules.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline (Phase 2.5)

Features:
- Validates regex-extracted rules using LLM judgment
- Classifies rule type when regex detection is uncertain
- Calculates confidence boost from LLM validation
- Tier-aware provider selection

Use Cases:
1. Ambiguous Regex Match - Regex finds `If condition Then` but is it a business rule?
2. Type Classification - Is this validation, authorization, or workflow?
3. False Positive Detection - Filter out code patterns that aren't business rules
"""

import logging
import json
import re
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .extraction_models import (
    BusinessRule,
    RuleType,
    ExtractionTier,
    ExtractionMethod,
)

logger = logging.getLogger(__name__)


class ClassificationResult(Enum):
    """Result of LLM classification."""
    CONFIRMED_RULE = "confirmed_rule"       # Definitely a business rule
    REJECTED = "rejected"                    # Not a business rule (false positive)
    UNCERTAIN = "uncertain"                  # LLM couldn't determine
    ERROR = "error"                          # Classification failed


@dataclass
class ClassificationResponse:
    """Response from LLM classification."""
    result: ClassificationResult
    is_business_rule: bool
    suggested_type: Optional[RuleType] = None
    confidence_boost: float = 0.0           # How much to boost confidence (0.0-0.15)
    natural_language: Optional[str] = None  # Improved NL description
    reasoning: Optional[str] = None         # LLM's reasoning
    provider_used: Optional[str] = None
    tokens_used: int = 0
    cost_cents: float = 0.0


# Tier to provider mapping for classification
TIER_CLASSIFICATION_PROVIDERS: Dict[ExtractionTier, List[str]] = {
    ExtractionTier.FREE: [],                              # No LLM
    ExtractionTier.BASIC: ["ollama"],                     # Local only
    ExtractionTier.STANDARD: ["ollama", "groq"],          # + Groq
    ExtractionTier.PROFESSIONAL: ["ollama", "groq", "gemini"],  # + Gemini
    ExtractionTier.PREMIUM: ["ollama", "groq", "gemini", "anthropic"],  # + Claude
}


# Classification prompt template
CLASSIFICATION_PROMPT = """You are an expert at analyzing legacy code to identify business rules.

Given the following code snippet, determine if it represents a BUSINESS RULE.

A BUSINESS RULE is:
- A constraint, validation, or policy enforced by the code
- Authorization/access control logic
- Workflow state transitions
- Scheduling/date-time constraints
- Data validation requirements
- Calculation formulas with business meaning

NOT a business rule:
- Pure technical/infrastructure code (logging, caching, connection handling)
- UI formatting or display logic
- Simple variable assignments without business meaning
- Error handling for technical errors (network, file I/O)
- Loop constructs for iteration only

CODE CONTEXT:
Language: {language}
File: {source_file}
Lines: {line_start}-{line_end}
{parent_context}

CODE SNIPPET:
```
{code_snippet}
```

CURRENT CLASSIFICATION:
Type: {rule_type}
Condition: {condition}
Action: {action}
Current Confidence: {confidence}%

Respond in JSON format:
{{
    "is_business_rule": true/false,
    "rule_type": "validation|authorization|scheduling|workflow|branching|threshold|data_access|state_management|error_handling|navigation|calculation|constraint|derivation",
    "confidence_boost": 0.0-0.15,
    "natural_language": "Clear business description in English",
    "reasoning": "Brief explanation of your decision"
}}

Only respond with the JSON, no other text."""


class LLMRuleClassifier:
    """
    Classifies ambiguous regex-extracted rules using LLM.

    Provides:
    - Validation of regex-extracted rules
    - Type classification for uncertain rules
    - Confidence boost calculation
    - Tier-aware provider selection
    """

    def __init__(
        self,
        extraction_tier: ExtractionTier = ExtractionTier.BASIC,
    ):
        """
        Initialize the classifier.

        Args:
            extraction_tier: Customer tier determining available LLM providers
        """
        self.extraction_tier = extraction_tier
        self._registry = None  # Lazy load

    def _get_registry(self):
        """Lazy load provider registry."""
        if self._registry is None:
            try:
                from app.providers.registry import get_registry
                self._registry = get_registry()
            except ImportError:
                logger.warning("Provider registry not available")
                self._registry = None
        return self._registry

    def get_available_providers(self) -> List[str]:
        """Get list of available providers for current tier."""
        return TIER_CLASSIFICATION_PROVIDERS.get(self.extraction_tier, [])

    async def classify_rule(
        self,
        rule: BusinessRule,
        prefer_local: bool = True,
    ) -> ClassificationResponse:
        """
        Classify a potentially ambiguous business rule.

        Args:
            rule: BusinessRule to classify
            prefer_local: Prefer local Ollama for privacy

        Returns:
            ClassificationResponse with validation result
        """
        # Check if we have LLM access
        providers = self.get_available_providers()
        if not providers:
            logger.debug(f"No LLM providers available for tier {self.extraction_tier.value}")
            return ClassificationResponse(
                result=ClassificationResult.UNCERTAIN,
                is_business_rule=True,  # Assume true when no LLM
                confidence_boost=0.0,
            )

        # Get registry
        registry = self._get_registry()
        if not registry:
            return ClassificationResponse(
                result=ClassificationResult.ERROR,
                is_business_rule=True,
                reasoning="Provider registry not available",
            )

        # Select provider
        provider_name = "ollama" if prefer_local and "ollama" in providers else providers[-1]
        provider = registry.get_provider(provider_name)

        if not provider:
            return ClassificationResponse(
                result=ClassificationResult.ERROR,
                is_business_rule=True,
                reasoning=f"Provider {provider_name} not available",
            )

        # Build prompt
        prompt = self._build_classification_prompt(rule)

        try:
            # Import request type
            from app.providers.base import LLMRequest

            request = LLMRequest(
                prompt=prompt,
                max_tokens=500,
                temperature=0.1,  # Low temperature for consistent classification
            )

            response = await provider.generate(request)

            if not response.success:
                return ClassificationResponse(
                    result=ClassificationResult.ERROR,
                    is_business_rule=True,
                    reasoning=response.error,
                    provider_used=provider_name,
                )

            # Parse response
            return self._parse_classification_response(
                response.content,
                provider_name,
                response.token_input + response.token_output,
                response.cost_cents,
            )

        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return ClassificationResponse(
                result=ClassificationResult.ERROR,
                is_business_rule=True,
                reasoning=str(e),
                provider_used=provider_name,
            )

    def _build_classification_prompt(self, rule: BusinessRule) -> str:
        """Build the classification prompt for a rule."""
        parent_context = ""
        if rule.parent_function:
            parent_context += f"Parent Function: {rule.parent_function}\n"
        if rule.parent_class:
            parent_context += f"Parent Class: {rule.parent_class}\n"
        if rule.region:
            parent_context += f"VB.NET Region: {rule.region}\n"

        return CLASSIFICATION_PROMPT.format(
            language=rule.language.value if rule.language else "unknown",
            source_file=rule.source_file,
            line_start=rule.source_lines[0],
            line_end=rule.source_lines[1],
            parent_context=parent_context,
            code_snippet=rule.code_snippet or rule.condition,
            rule_type=rule.rule_type.value,
            condition=rule.condition,
            action=rule.action,
            confidence=int(rule.confidence * 100),
        )

    def _parse_classification_response(
        self,
        content: str,
        provider_name: str,
        tokens_used: int,
        cost_cents: float,
    ) -> ClassificationResponse:
        """Parse the LLM response into a ClassificationResponse."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if not json_match:
                return ClassificationResponse(
                    result=ClassificationResult.ERROR,
                    is_business_rule=True,
                    reasoning="Could not parse JSON from response",
                    provider_used=provider_name,
                    tokens_used=tokens_used,
                    cost_cents=cost_cents,
                )

            data = json.loads(json_match.group())

            is_rule = data.get("is_business_rule", True)

            # Parse rule type
            suggested_type = None
            if "rule_type" in data:
                try:
                    suggested_type = RuleType(data["rule_type"])
                except ValueError:
                    pass

            # Determine result
            if is_rule:
                result = ClassificationResult.CONFIRMED_RULE
            else:
                result = ClassificationResult.REJECTED

            return ClassificationResponse(
                result=result,
                is_business_rule=is_rule,
                suggested_type=suggested_type,
                confidence_boost=min(float(data.get("confidence_boost", 0.0)), 0.15),
                natural_language=data.get("natural_language"),
                reasoning=data.get("reasoning"),
                provider_used=provider_name,
                tokens_used=tokens_used,
                cost_cents=cost_cents,
            )

        except json.JSONDecodeError as e:
            return ClassificationResponse(
                result=ClassificationResult.ERROR,
                is_business_rule=True,
                reasoning=f"JSON parse error: {e}",
                provider_used=provider_name,
                tokens_used=tokens_used,
                cost_cents=cost_cents,
            )

    async def classify_batch(
        self,
        rules: List[BusinessRule],
        confidence_threshold: float = 0.7,
        max_rules: int = 50,
    ) -> List[Tuple[BusinessRule, ClassificationResponse]]:
        """
        Classify a batch of rules, focusing on low-confidence ones.

        Args:
            rules: List of BusinessRules to classify
            confidence_threshold: Only classify rules below this confidence
            max_rules: Maximum rules to classify (cost control)

        Returns:
            List of (rule, classification) tuples
        """
        results = []

        # Filter to low-confidence rules
        candidates = [r for r in rules if r.confidence < confidence_threshold]
        candidates = candidates[:max_rules]

        logger.info(
            f"Classifying {len(candidates)} low-confidence rules "
            f"(threshold: {confidence_threshold}, tier: {self.extraction_tier.value})"
        )

        for rule in candidates:
            classification = await self.classify_rule(rule)
            results.append((rule, classification))

            # Apply classification results to rule
            if classification.result == ClassificationResult.CONFIRMED_RULE:
                rule.validated_by_llm = True
                rule.confidence = min(rule.confidence + classification.confidence_boost, 0.95)
                if classification.suggested_type:
                    rule.rule_type = classification.suggested_type
                if classification.natural_language:
                    rule.natural_language = classification.natural_language
                rule.llm_validation_result = "confirmed"
            elif classification.result == ClassificationResult.REJECTED:
                rule.validated_by_llm = True
                rule.confidence = 0.0  # Mark for removal
                rule.llm_validation_result = "rejected"

        confirmed = sum(1 for _, c in results if c.result == ClassificationResult.CONFIRMED_RULE)
        rejected = sum(1 for _, c in results if c.result == ClassificationResult.REJECTED)
        logger.info(f"Classification complete: {confirmed} confirmed, {rejected} rejected")

        return results

    def filter_rejected_rules(
        self,
        rules: List[BusinessRule],
        classifications: List[Tuple[BusinessRule, ClassificationResponse]],
    ) -> List[BusinessRule]:
        """
        Filter out rejected rules from the list.

        Args:
            rules: Original list of rules
            classifications: Classification results

        Returns:
            Filtered list with rejected rules removed
        """
        rejected_ids = {
            rule.id
            for rule, cls in classifications
            if cls.result == ClassificationResult.REJECTED
        }

        return [r for r in rules if r.id not in rejected_ids]


# Convenience function for one-off classification
async def classify_business_rule(
    rule: BusinessRule,
    tier: ExtractionTier = ExtractionTier.BASIC,
) -> ClassificationResponse:
    """
    Convenience function to classify a single business rule.

    Args:
        rule: BusinessRule to classify
        tier: Extraction tier determining LLM access

    Returns:
        ClassificationResponse
    """
    classifier = LLMRuleClassifier(extraction_tier=tier)
    return await classifier.classify_rule(rule)
