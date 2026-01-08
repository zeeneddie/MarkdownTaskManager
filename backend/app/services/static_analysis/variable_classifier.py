# backend/app/services/static_analysis/variable_classifier.py
"""
Variable Classifier - Classifies variables as DOMAIN, IMPLEMENTATION, or CONTROL.

Used to identify business-relevant code sections and filter noise
from requirement extraction.

Part of Fase 15: Hybrid Static-LLM Extraction Pipeline
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Set, Optional
import re
import logging

logger = logging.getLogger(__name__)


class VariableType(Enum):
    """Classification types for variables."""
    DOMAIN = "domain"           # Business concepts (customer, order, invoice)
    IMPLEMENTATION = "implementation"  # Technical (cache, buffer, connection)
    CONTROL = "control"         # Flow control (i, j, index, flag, temp)


@dataclass
class ClassifiedVariable:
    """A variable with its classification."""
    name: str
    variable_type: VariableType
    confidence: float  # 0.0 - 1.0
    context: str       # Where variable was found
    reasoning: str     # Why this classification


@dataclass
class VariableClassificationResult:
    """Result of classifying all variables."""
    variables: List[ClassifiedVariable]
    domain_variables: List[str]
    implementation_variables: List[str]
    control_variables: List[str]
    domain_coverage: float  # % of code related to domain


class VariableClassifier:
    """
    Classifies variables into DOMAIN, IMPLEMENTATION, or CONTROL types.

    Used to:
    - Identify business-relevant code sections
    - Filter noise from requirement extraction
    - Weight variables for business rule detection
    """

    # Patterns for each variable type
    DOMAIN_PATTERNS = [
        # Business entities
        r'(?i)(customer|client|user|account|order|invoice|payment|product|item)',
        r'(?i)(employee|staff|manager|department|organization|company)',
        r'(?i)(transaction|balance|amount|price|cost|total|discount|tax|fee)',
        r'(?i)(date|time|period|deadline|schedule|calendar|appointment)',
        r'(?i)(status|state|phase|stage|level|priority|category)',
        r'(?i)(address|email|phone|contact|location|country|city)',
        r'(?i)(name|title|description|comment|note|message|text)',
        r'(?i)(patient|doctor|hospital|medical|health|diagnosis|treatment)',
        r'(?i)(policy|contract|agreement|terms|conditions)',
        r'(?i)(score|rating|rank|grade|assessment|evaluation)',
        # Domain verbs as nouns
        r'(?i)(approval|validation|verification|authorization|authentication)',
        r'(?i)(request|response|notification|alert|warning|error)',
        r'(?i)(subscription|membership|license|permission|role)',
        r'(?i)(delivery|shipment|inventory|stock|warehouse)',
        r'(?i)(report|summary|analysis|dashboard|metric)',
    ]

    IMPLEMENTATION_PATTERNS = [
        # Technical concepts
        r'(?i)(cache|buffer|pool|queue|stack|heap)',
        r'(?i)(connection|session|socket|stream|channel)',
        r'(?i)(config|setting|option|param|argument|env)',
        r'(?i)(logger|log|trace|debug|monitor|telemetry)',
        r'(?i)(handler|listener|callback|hook|observer|subscriber)',
        r'(?i)(factory|builder|provider|service|manager|controller)',
        r'(?i)(mapper|converter|transformer|adapter|wrapper|decorator)',
        r'(?i)(repository|store|dao|dal|gateway|client)',
        r'(?i)(thread|process|worker|executor|scheduler|task)',
        r'(?i)(mutex|lock|semaphore|barrier|condition)',
        # Database/ORM
        r'(?i)(cursor|result_set|row|column|field|schema)',
        r'(?i)(query|sql|command|statement|transaction)',
        r'(?i)(db|database|table|collection|document)',
        # HTTP/API
        r'(?i)(request|response|header|body|cookie|token)',
        r'(?i)(endpoint|route|path|url|uri|method)',
        # Framework
        r'(?i)(context|scope|container|injector|resolver)',
        r'(?i)(middleware|interceptor|filter|pipe|guard)',
    ]

    CONTROL_PATTERNS = [
        # Loop/iteration
        r'^[ijk]$',
        r'(?i)^(index|idx|pos|offset|count|counter|num)$',
        r'(?i)^(iter|iterator|enum|enumerator)$',
        r'(?i)^(len|length|size|capacity)$',
        # Temporary
        r'(?i)^(temp|tmp|t|_|__)$',
        r'(?i)^(result|ret|rv|res|output|out)$',
        r'(?i)^(val|value|v|data|obj|item|elem)$',
        # Flags
        r'(?i)^(flag|is_|has_|should_|can_|will_|must_|need_)',
        r'(?i)^(found|done|finished|completed|success|ok|valid)$',
        r'(?i)^(enabled|disabled|active|visible|hidden|selected)$',
        # Collections (generic)
        r'(?i)^(list|array|dict|map|set|items|elements|entries|keys|values)$',
        # Loop variables
        r'(?i)^(row|col|x|y|z|n|m|p|q)$',
        r'^_+$',  # Underscores
    ]

    def __init__(self, custom_domain_terms: Optional[List[str]] = None):
        """
        Initialize classifier with optional custom domain terms.

        Args:
            custom_domain_terms: Project-specific domain terms to add
        """
        self.custom_domain_terms = custom_domain_terms or []
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for performance."""
        self.domain_regex = [re.compile(p) for p in self.DOMAIN_PATTERNS]
        self.impl_regex = [re.compile(p) for p in self.IMPLEMENTATION_PATTERNS]
        self.control_regex = [re.compile(p) for p in self.CONTROL_PATTERNS]

        # Add custom domain terms
        if self.custom_domain_terms:
            pattern = r'(?i)(' + '|'.join(re.escape(t) for t in self.custom_domain_terms) + ')'
            self.domain_regex.append(re.compile(pattern))

    def add_domain_terms(self, terms: List[str]):
        """Add additional domain terms dynamically."""
        self.custom_domain_terms.extend(terms)
        self._compile_patterns()

    def classify_variable(self,
                          name: str,
                          context: Optional[str] = None) -> ClassifiedVariable:
        """
        Classify a single variable.

        Args:
            name: Variable name to classify
            context: Optional context (e.g., surrounding code)

        Returns:
            ClassifiedVariable with type and confidence
        """

        # Check control patterns first (most specific)
        for pattern in self.control_regex:
            if pattern.match(name):
                return ClassifiedVariable(
                    name=name,
                    variable_type=VariableType.CONTROL,
                    confidence=0.9,
                    context=context or "",
                    reasoning=f"Matches control pattern: {pattern.pattern}"
                )

        # Check domain patterns
        domain_matches = sum(1 for p in self.domain_regex if p.search(name))
        impl_matches = sum(1 for p in self.impl_regex if p.search(name))

        if domain_matches > impl_matches:
            confidence = min(0.6 + (domain_matches * 0.1), 0.95)
            return ClassifiedVariable(
                name=name,
                variable_type=VariableType.DOMAIN,
                confidence=confidence,
                context=context or "",
                reasoning=f"Matches {domain_matches} domain patterns"
            )
        elif impl_matches > 0:
            confidence = min(0.6 + (impl_matches * 0.1), 0.95)
            return ClassifiedVariable(
                name=name,
                variable_type=VariableType.IMPLEMENTATION,
                confidence=confidence,
                context=context or "",
                reasoning=f"Matches {impl_matches} implementation patterns"
            )

        # Default: use heuristics
        return self._heuristic_classify(name, context)

    def _heuristic_classify(self, name: str, context: Optional[str]) -> ClassifiedVariable:
        """Use heuristics when no pattern matches."""
        # Short names are usually control
        if len(name) <= 2:
            return ClassifiedVariable(
                name=name,
                variable_type=VariableType.CONTROL,
                confidence=0.7,
                context=context or "",
                reasoning="Short name suggests control variable"
            )

        # Names with underscores starting with _ are usually private/internal
        if name.startswith('_'):
            return ClassifiedVariable(
                name=name,
                variable_type=VariableType.IMPLEMENTATION,
                confidence=0.65,
                context=context or "",
                reasoning="Leading underscore suggests implementation detail"
            )

        # CamelCase with CRUD-like words suggests implementation
        crud_words = ['get', 'set', 'create', 'update', 'delete', 'find', 'fetch', 'load', 'save', 'remove']
        if any(word in name.lower() for word in crud_words):
            return ClassifiedVariable(
                name=name,
                variable_type=VariableType.IMPLEMENTATION,
                confidence=0.6,
                context=context or "",
                reasoning="CRUD operation suggests implementation"
            )

        # ALL_CAPS suggests constant (could be domain or impl)
        if name.isupper() and len(name) > 2:
            return ClassifiedVariable(
                name=name,
                variable_type=VariableType.DOMAIN,
                confidence=0.5,
                context=context or "",
                reasoning="Constant naming - may be domain or configuration"
            )

        # Default to domain with low confidence
        return ClassifiedVariable(
            name=name,
            variable_type=VariableType.DOMAIN,
            confidence=0.5,
            context=context or "",
            reasoning="Default classification - needs LLM validation"
        )

    def classify_all(self,
                     variables: List[str],
                     contexts: Optional[Dict[str, str]] = None) -> VariableClassificationResult:
        """
        Classify all variables in a codebase.

        Args:
            variables: List of variable names to classify
            contexts: Optional dict mapping variable names to their contexts

        Returns:
            VariableClassificationResult with all classifications
        """
        contexts = contexts or {}
        classified = [
            self.classify_variable(var, contexts.get(var))
            for var in variables
        ]

        domain = [v.name for v in classified if v.variable_type == VariableType.DOMAIN]
        impl = [v.name for v in classified if v.variable_type == VariableType.IMPLEMENTATION]
        control = [v.name for v in classified if v.variable_type == VariableType.CONTROL]

        total = len(classified)
        domain_coverage = len(domain) / total if total > 0 else 0.0

        return VariableClassificationResult(
            variables=classified,
            domain_variables=domain,
            implementation_variables=impl,
            control_variables=control,
            domain_coverage=domain_coverage
        )

    def get_domain_weight(self, variable: str) -> float:
        """
        Get the domain relevance weight for a variable.

        Used for weighting business rule detection.

        Returns:
            Float 0.0-1.0 where 1.0 = highly domain relevant
        """
        classification = self.classify_variable(variable)

        if classification.variable_type == VariableType.DOMAIN:
            return classification.confidence
        elif classification.variable_type == VariableType.IMPLEMENTATION:
            return classification.confidence * 0.3  # Implementation may still be relevant
        else:
            return 0.0  # Control variables are not domain relevant

    def filter_domain_variables(self, variables: List[str], min_confidence: float = 0.6) -> List[str]:
        """
        Filter to only domain variables above confidence threshold.

        Args:
            variables: List of variable names
            min_confidence: Minimum confidence threshold

        Returns:
            List of domain variable names meeting threshold
        """
        result = self.classify_all(variables)
        return [
            v.name for v in result.variables
            if v.variable_type == VariableType.DOMAIN and v.confidence >= min_confidence
        ]

    def suggest_domain_terms(self, variables: List[str]) -> List[str]:
        """
        Suggest potential domain terms from unclassified variables.

        Returns variables that might be domain-specific but weren't recognized.
        """
        suggestions = []
        for var in variables:
            classification = self.classify_variable(var)
            # Low confidence domain or implementation might be project-specific domain terms
            if classification.confidence < 0.6 and len(var) > 4:
                suggestions.append(var)
        return suggestions
