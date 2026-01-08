"""
Natural Language Quality Enhancer - Week 101

Improves the natural language quality of extracted business rules.
Provides type-specific templates and enhancement strategies.

Usage:
    enhancer = NLQualityEnhancer()

    # Enhance a single rule
    enhanced = enhancer.enhance(rule)

    # Enhance with specific template
    enhanced = enhancer.enhance(rule, template="validation")

    # Batch enhance rules
    enhanced_rules = enhancer.enhance_batch(rules)
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod


class RuleType(Enum):
    """Types of business rules."""
    VALIDATION = "validation"
    AUTHORIZATION = "authorization"
    CALCULATION = "calculation"
    WORKFLOW = "workflow"
    CONSTRAINT = "constraint"
    DERIVATION = "derivation"
    INFERENCE = "inference"


@dataclass
class EnhancedRule:
    """Enhanced version of a business rule."""
    original_text: str
    enhanced_text: str
    rule_type: RuleType
    clarity_score: float  # 0-1
    improvements: List[str]
    metadata: Dict = field(default_factory=dict)


@dataclass
class RuleTemplate:
    """Template for formatting a rule type."""
    rule_type: RuleType
    pattern: str
    example: str
    placeholders: List[str]


class RuleEnhancementStrategy(ABC):
    """Abstract base for rule enhancement strategies."""

    @abstractmethod
    def can_enhance(self, text: str) -> bool:
        """Check if this strategy can enhance the given text."""
        pass

    @abstractmethod
    def enhance(self, text: str) -> Tuple[str, List[str]]:
        """
        Enhance the text.

        Returns:
            Tuple of (enhanced_text, list_of_improvements)
        """
        pass


class NLQualityEnhancer:
    """
    Service for improving natural language quality of business rules.

    Applies rule-type-specific templates and enhancement strategies
    to produce clearer, more consistent rule descriptions.
    """

    def __init__(self):
        self._templates = self._load_templates()
        self._strategies = self._load_strategies()

    # =========================================================================
    # Templates by Rule Type
    # =========================================================================

    def _load_templates(self) -> Dict[RuleType, List[RuleTemplate]]:
        """Load rule templates for each type."""
        return {
            RuleType.VALIDATION: [
                RuleTemplate(
                    rule_type=RuleType.VALIDATION,
                    pattern="The {entity} {field} must {constraint}.",
                    example="The user email must be a valid email format.",
                    placeholders=["entity", "field", "constraint"],
                ),
                RuleTemplate(
                    rule_type=RuleType.VALIDATION,
                    pattern="When {condition}, the {entity} must {requirement}.",
                    example="When creating a new account, the user must provide a valid phone number.",
                    placeholders=["condition", "entity", "requirement"],
                ),
                RuleTemplate(
                    rule_type=RuleType.VALIDATION,
                    pattern="{field} is required when {condition}.",
                    example="Shipping address is required when delivery method is selected.",
                    placeholders=["field", "condition"],
                ),
            ],
            RuleType.AUTHORIZATION: [
                RuleTemplate(
                    rule_type=RuleType.AUTHORIZATION,
                    pattern="Only {role} can {action} {resource}.",
                    example="Only administrators can delete user accounts.",
                    placeholders=["role", "action", "resource"],
                ),
                RuleTemplate(
                    rule_type=RuleType.AUTHORIZATION,
                    pattern="{role} is authorized to {action} when {condition}.",
                    example="Managers are authorized to approve expenses when amount is below $10,000.",
                    placeholders=["role", "action", "condition"],
                ),
                RuleTemplate(
                    rule_type=RuleType.AUTHORIZATION,
                    pattern="Access to {resource} requires {permission}.",
                    example="Access to financial reports requires finance department membership.",
                    placeholders=["resource", "permission"],
                ),
            ],
            RuleType.CALCULATION: [
                RuleTemplate(
                    rule_type=RuleType.CALCULATION,
                    pattern="{result} is calculated as {formula}.",
                    example="Total price is calculated as unit price multiplied by quantity.",
                    placeholders=["result", "formula"],
                ),
                RuleTemplate(
                    rule_type=RuleType.CALCULATION,
                    pattern="When {condition}, {result} equals {calculation}.",
                    example="When order exceeds $100, discount equals 10% of subtotal.",
                    placeholders=["condition", "result", "calculation"],
                ),
                RuleTemplate(
                    rule_type=RuleType.CALCULATION,
                    pattern="{field} must be {comparison} {value}.",
                    example="Account balance must be greater than or equal to zero.",
                    placeholders=["field", "comparison", "value"],
                ),
            ],
            RuleType.WORKFLOW: [
                RuleTemplate(
                    rule_type=RuleType.WORKFLOW,
                    pattern="After {trigger}, the system must {action}.",
                    example="After payment confirmation, the system must send receipt email.",
                    placeholders=["trigger", "action"],
                ),
                RuleTemplate(
                    rule_type=RuleType.WORKFLOW,
                    pattern="{entity} transitions from {state1} to {state2} when {condition}.",
                    example="Order transitions from pending to approved when manager approves.",
                    placeholders=["entity", "state1", "state2", "condition"],
                ),
                RuleTemplate(
                    rule_type=RuleType.WORKFLOW,
                    pattern="Before {action}, the {entity} must {prerequisite}.",
                    example="Before shipping, the order must have confirmed payment.",
                    placeholders=["action", "entity", "prerequisite"],
                ),
            ],
            RuleType.CONSTRAINT: [
                RuleTemplate(
                    rule_type=RuleType.CONSTRAINT,
                    pattern="{entity} cannot {forbidden_action}.",
                    example="Users cannot have duplicate email addresses.",
                    placeholders=["entity", "forbidden_action"],
                ),
                RuleTemplate(
                    rule_type=RuleType.CONSTRAINT,
                    pattern="{field} must be between {min} and {max}.",
                    example="Age must be between 18 and 120.",
                    placeholders=["field", "min", "max"],
                ),
                RuleTemplate(
                    rule_type=RuleType.CONSTRAINT,
                    pattern="{field} must not exceed {limit} {unit}.",
                    example="File size must not exceed 10 megabytes.",
                    placeholders=["field", "limit", "unit"],
                ),
            ],
            RuleType.DERIVATION: [
                RuleTemplate(
                    rule_type=RuleType.DERIVATION,
                    pattern="{derived_field} is derived from {source_fields}.",
                    example="Full name is derived from first name and last name.",
                    placeholders=["derived_field", "source_fields"],
                ),
                RuleTemplate(
                    rule_type=RuleType.DERIVATION,
                    pattern="If {condition}, then {conclusion}.",
                    example="If customer has 10+ orders, then customer status is 'loyal'.",
                    placeholders=["condition", "conclusion"],
                ),
            ],
            RuleType.INFERENCE: [
                RuleTemplate(
                    rule_type=RuleType.INFERENCE,
                    pattern="When {observation}, infer that {conclusion}.",
                    example="When cart is abandoned for 24 hours, infer that customer lost interest.",
                    placeholders=["observation", "conclusion"],
                ),
                RuleTemplate(
                    rule_type=RuleType.INFERENCE,
                    pattern="{entity} is considered {classification} when {criteria}.",
                    example="Customer is considered high-risk when payment fails 3+ times.",
                    placeholders=["entity", "classification", "criteria"],
                ),
            ],
        }

    # =========================================================================
    # Enhancement Strategies
    # =========================================================================

    def _load_strategies(self) -> List[RuleEnhancementStrategy]:
        """Load all enhancement strategies."""
        return [
            CapitalizationStrategy(),
            PassiveToActiveStrategy(),
            AmbiguityResolver(),
            TechnicalTermSimplifier(),
            QuantifierNormalizer(),
            ModalVerbNormalizer(),
            NegationClarifier(),
            PunctuationNormalizer(),
        ]

    # =========================================================================
    # Main Enhancement API
    # =========================================================================

    def enhance(
        self,
        text: str,
        rule_type: Optional[RuleType] = None,
    ) -> EnhancedRule:
        """
        Enhance a single rule's natural language quality.

        Args:
            text: Original rule text
            rule_type: Optional rule type hint

        Returns:
            EnhancedRule with improvements
        """
        # Detect rule type if not provided
        if rule_type is None:
            rule_type = self._detect_rule_type(text)

        # Apply enhancement strategies
        enhanced_text = text
        all_improvements: List[str] = []

        for strategy in self._strategies:
            if strategy.can_enhance(enhanced_text):
                new_text, improvements = strategy.enhance(enhanced_text)
                if new_text != enhanced_text:
                    enhanced_text = new_text
                    all_improvements.extend(improvements)

        # Calculate clarity score
        clarity_score = self._calculate_clarity_score(enhanced_text)

        return EnhancedRule(
            original_text=text,
            enhanced_text=enhanced_text,
            rule_type=rule_type,
            clarity_score=clarity_score,
            improvements=all_improvements,
        )

    def enhance_batch(
        self,
        rules: List[Tuple[str, Optional[RuleType]]],
    ) -> List[EnhancedRule]:
        """
        Enhance multiple rules.

        Args:
            rules: List of (text, rule_type) tuples

        Returns:
            List of EnhancedRule objects
        """
        return [
            self.enhance(text, rule_type)
            for text, rule_type in rules
        ]

    def get_template_suggestion(
        self,
        text: str,
        rule_type: Optional[RuleType] = None,
    ) -> Optional[RuleTemplate]:
        """
        Suggest a template that best fits the rule.

        Args:
            text: Rule text to analyze
            rule_type: Optional rule type hint

        Returns:
            Best matching RuleTemplate or None
        """
        if rule_type is None:
            rule_type = self._detect_rule_type(text)

        templates = self._templates.get(rule_type, [])
        if not templates:
            return None

        # Simple heuristic: return first template that has some keyword overlap
        text_lower = text.lower()

        for template in templates:
            # Extract keywords from pattern
            keywords = re.findall(r'\b[a-z]+\b', template.pattern.lower())
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches >= 2:
                return template

        return templates[0] if templates else None

    # =========================================================================
    # Rule Type Detection
    # =========================================================================

    def _detect_rule_type(self, text: str) -> RuleType:
        """Detect the type of business rule from its text."""
        text_lower = text.lower()

        # Validation indicators
        if any(kw in text_lower for kw in [
            "must be valid", "required", "format", "pattern",
            "cannot be empty", "must contain", "must match",
        ]):
            return RuleType.VALIDATION

        # Authorization indicators
        if any(kw in text_lower for kw in [
            "only", "authorized", "permission", "access",
            "role", "can only", "allowed to",
        ]):
            return RuleType.AUTHORIZATION

        # Calculation indicators
        if any(kw in text_lower for kw in [
            "calculated", "computed", "equals", "sum of",
            "multiply", "percentage", "total",
        ]):
            return RuleType.CALCULATION

        # Workflow indicators
        if any(kw in text_lower for kw in [
            "after", "before", "when", "then", "triggers",
            "transitions", "state", "step", "process",
        ]):
            return RuleType.WORKFLOW

        # Constraint indicators
        if any(kw in text_lower for kw in [
            "cannot", "must not", "maximum", "minimum",
            "between", "limit", "exceed", "unique",
        ]):
            return RuleType.CONSTRAINT

        # Derivation indicators
        if any(kw in text_lower for kw in [
            "derived", "based on", "determined by",
            "depends on", "if then",
        ]):
            return RuleType.DERIVATION

        # Default to inference
        return RuleType.INFERENCE

    # =========================================================================
    # Clarity Scoring
    # =========================================================================

    def _calculate_clarity_score(self, text: str) -> float:
        """Calculate clarity score for rule text (0-1)."""
        score = 1.0
        penalties = []

        # Check for passive voice (reduce score)
        if self._has_passive_voice(text):
            score -= 0.1
            penalties.append("passive_voice")

        # Check for ambiguous words
        ambiguous_count = self._count_ambiguous_words(text)
        score -= ambiguous_count * 0.05
        if ambiguous_count > 0:
            penalties.append(f"ambiguous_words:{ambiguous_count}")

        # Check sentence length (penalize very long sentences)
        word_count = len(text.split())
        if word_count > 30:
            score -= 0.15
            penalties.append("too_long")
        elif word_count > 20:
            score -= 0.05
            penalties.append("somewhat_long")

        # Check for proper structure
        if not text[0].isupper():
            score -= 0.05
            penalties.append("no_capital")

        if not text.rstrip().endswith(('.', '!', '?')):
            score -= 0.05
            penalties.append("no_punctuation")

        # Check for specific business terms (bonus)
        if self._has_specific_terms(text):
            score += 0.05

        return max(0.0, min(1.0, score))

    def _has_passive_voice(self, text: str) -> bool:
        """Check if text uses passive voice."""
        passive_patterns = [
            r"\bis\s+\w+ed\b",
            r"\bare\s+\w+ed\b",
            r"\bwas\s+\w+ed\b",
            r"\bwere\s+\w+ed\b",
            r"\bbeen\s+\w+ed\b",
            r"\bbe\s+\w+ed\b",
        ]
        text_lower = text.lower()
        return any(re.search(p, text_lower) for p in passive_patterns)

    def _count_ambiguous_words(self, text: str) -> int:
        """Count ambiguous words in text."""
        ambiguous = [
            "some", "many", "few", "several", "various",
            "appropriate", "reasonable", "adequate", "sufficient",
            "etc", "and so on", "things", "stuff",
        ]
        text_lower = text.lower()
        return sum(1 for word in ambiguous if word in text_lower)

    def _has_specific_terms(self, text: str) -> bool:
        """Check if text contains specific domain terms."""
        specific_patterns = [
            r"\d+",  # Numbers
            r"\$[\d,]+",  # Currency
            r"\b[A-Z]{2,}\b",  # Acronyms
            r"\b\w+_\w+\b",  # Technical identifiers
        ]
        return any(re.search(p, text) for p in specific_patterns)


# =========================================================================
# Enhancement Strategies
# =========================================================================


class CapitalizationStrategy(RuleEnhancementStrategy):
    """Ensures proper capitalization."""

    def can_enhance(self, text: str) -> bool:
        return text and not text[0].isupper()

    def enhance(self, text: str) -> Tuple[str, List[str]]:
        enhanced = text[0].upper() + text[1:] if text else text
        return enhanced, ["Capitalized first letter"]


class PassiveToActiveStrategy(RuleEnhancementStrategy):
    """Converts passive voice to active voice."""

    PASSIVE_PATTERNS = [
        (r"(\w+)\s+is\s+required\s+to\s+be\s+(\w+)", r"\1 must be \2"),
        (r"(\w+)\s+should\s+be\s+(\w+ed)\s+by\s+(\w+)", r"\3 must \2 \1"),
        (r"it\s+is\s+required\s+that\s+(\w+)", r"\1 is required"),
    ]

    def can_enhance(self, text: str) -> bool:
        text_lower = text.lower()
        return any("is required" in text_lower, "should be" in text_lower)

    def enhance(self, text: str) -> Tuple[str, List[str]]:
        enhanced = text
        improvements = []

        for pattern, replacement in self.PASSIVE_PATTERNS:
            new_text = re.sub(pattern, replacement, enhanced, flags=re.IGNORECASE)
            if new_text != enhanced:
                enhanced = new_text
                improvements.append("Converted passive to active voice")

        return enhanced, improvements


class AmbiguityResolver(RuleEnhancementStrategy):
    """Replaces ambiguous terms with specific alternatives."""

    REPLACEMENTS = {
        "appropriate": "valid",
        "reasonable": "acceptable",
        "etc.": "",
        "and so on": "",
        "various": "all applicable",
        "some": "one or more",
    }

    def can_enhance(self, text: str) -> bool:
        text_lower = text.lower()
        return any(term in text_lower for term in self.REPLACEMENTS)

    def enhance(self, text: str) -> Tuple[str, List[str]]:
        enhanced = text
        improvements = []

        for old, new in self.REPLACEMENTS.items():
            if old.lower() in enhanced.lower():
                pattern = re.compile(re.escape(old), re.IGNORECASE)
                enhanced = pattern.sub(new, enhanced)
                improvements.append(f"Replaced '{old}' with '{new}'")

        # Clean up extra whitespace
        enhanced = " ".join(enhanced.split())

        return enhanced, improvements


class TechnicalTermSimplifier(RuleEnhancementStrategy):
    """Simplifies overly technical terms."""

    SIMPLIFICATIONS = {
        "instantiate": "create",
        "invoke": "call",
        "utilize": "use",
        "implement": "create",
        "terminate": "end",
        "initialize": "set up",
        "persist": "save",
        "retrieve": "get",
    }

    def can_enhance(self, text: str) -> bool:
        text_lower = text.lower()
        return any(term in text_lower for term in self.SIMPLIFICATIONS)

    def enhance(self, text: str) -> Tuple[str, List[str]]:
        enhanced = text
        improvements = []

        for old, new in self.SIMPLIFICATIONS.items():
            if old.lower() in enhanced.lower():
                pattern = re.compile(r'\b' + re.escape(old) + r'\b', re.IGNORECASE)
                enhanced = pattern.sub(new, enhanced)
                improvements.append(f"Simplified '{old}' to '{new}'")

        return enhanced, improvements


class QuantifierNormalizer(RuleEnhancementStrategy):
    """Normalizes quantity expressions."""

    NORMALIZATIONS = [
        (r"at\s+least\s+(\d+)", r"\1 or more"),
        (r"at\s+most\s+(\d+)", r"up to \1"),
        (r"no\s+more\s+than\s+(\d+)", r"up to \1"),
        (r"no\s+less\s+than\s+(\d+)", r"\1 or more"),
    ]

    def can_enhance(self, text: str) -> bool:
        text_lower = text.lower()
        return any(
            re.search(pattern, text_lower)
            for pattern, _ in self.NORMALIZATIONS
        )

    def enhance(self, text: str) -> Tuple[str, List[str]]:
        enhanced = text
        improvements = []

        for pattern, replacement in self.NORMALIZATIONS:
            new_text = re.sub(pattern, replacement, enhanced, flags=re.IGNORECASE)
            if new_text != enhanced:
                enhanced = new_text
                improvements.append("Normalized quantity expression")

        return enhanced, improvements


class ModalVerbNormalizer(RuleEnhancementStrategy):
    """Normalizes modal verbs to 'must'."""

    REPLACEMENTS = [
        (r"\bshould\b", "must"),
        (r"\bshall\b", "must"),
        (r"\bneeds?\s+to\b", "must"),
        (r"\brequired\s+to\b", "must"),
        (r"\bhas\s+to\b", "must"),
        (r"\bhave\s+to\b", "must"),
    ]

    def can_enhance(self, text: str) -> bool:
        text_lower = text.lower()
        return any(
            re.search(pattern, text_lower)
            for pattern, _ in self.REPLACEMENTS
        )

    def enhance(self, text: str) -> Tuple[str, List[str]]:
        enhanced = text
        improvements = []

        for pattern, replacement in self.REPLACEMENTS:
            new_text = re.sub(pattern, replacement, enhanced, flags=re.IGNORECASE)
            if new_text != enhanced:
                enhanced = new_text
                improvements.append("Normalized modal verb to 'must'")

        return enhanced, improvements


class NegationClarifier(RuleEnhancementStrategy):
    """Clarifies double negatives and unclear negations."""

    CLARIFICATIONS = [
        (r"not\s+un(\w+)", r"\1"),  # "not unlike" -> "like"
        (r"cannot\s+not\s+", "must "),
        (r"don't\s+not\s+", "do "),
    ]

    def can_enhance(self, text: str) -> bool:
        text_lower = text.lower()
        return any(
            re.search(pattern, text_lower)
            for pattern, _ in self.CLARIFICATIONS
        )

    def enhance(self, text: str) -> Tuple[str, List[str]]:
        enhanced = text
        improvements = []

        for pattern, replacement in self.CLARIFICATIONS:
            new_text = re.sub(pattern, replacement, enhanced, flags=re.IGNORECASE)
            if new_text != enhanced:
                enhanced = new_text
                improvements.append("Clarified double negative")

        return enhanced, improvements


class PunctuationNormalizer(RuleEnhancementStrategy):
    """Ensures proper punctuation."""

    def can_enhance(self, text: str) -> bool:
        stripped = text.rstrip()
        return stripped and stripped[-1] not in '.!?'

    def enhance(self, text: str) -> Tuple[str, List[str]]:
        stripped = text.rstrip()
        if stripped and stripped[-1] not in '.!?':
            return stripped + ".", ["Added ending punctuation"]
        return text, []


# Convenience functions
def enhance_rule(text: str, rule_type: Optional[RuleType] = None) -> EnhancedRule:
    """Quick function to enhance a single rule."""
    return NLQualityEnhancer().enhance(text, rule_type)


def detect_rule_type(text: str) -> RuleType:
    """Quick function to detect rule type."""
    return NLQualityEnhancer()._detect_rule_type(text)
