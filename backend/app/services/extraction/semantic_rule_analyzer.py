"""
Semantic Rule Analyzer - Week 105
BR-M-1: Semantic Rule Understanding via LLM

Enhances business rule extraction by using LLM to:
- Understand semantic meaning of code patterns
- Categorize rules by business domain
- Identify implicit rules from code structure
- Generate human-readable rule descriptions
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import re
import json


class RuleCategory(Enum):
    """Business rule categories."""
    VALIDATION = "validation"           # Input/data validation
    AUTHORIZATION = "authorization"     # Access control rules
    CALCULATION = "calculation"         # Business calculations
    WORKFLOW = "workflow"               # State transitions
    CONSTRAINT = "constraint"           # Business constraints
    TRANSFORMATION = "transformation"   # Data transformations
    NOTIFICATION = "notification"       # Alert/notification triggers
    INTEGRATION = "integration"         # External system rules
    COMPLIANCE = "compliance"           # Regulatory requirements


class RuleConfidence(Enum):
    """Confidence levels for rule extraction."""
    HIGH = "high"       # Explicit rule (e.g., validation decorator)
    MEDIUM = "medium"   # Inferred from patterns
    LOW = "low"         # Implicit, needs verification


@dataclass
class ExtractedRule:
    """A business rule extracted from code."""
    id: str
    name: str
    description: str
    category: RuleCategory
    confidence: RuleConfidence
    source_file: str
    source_line: int
    code_snippet: str
    conditions: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    domain_terms: List[str] = field(default_factory=list)
    compliance_tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.utcnow())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "confidence": self.confidence.value,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "code_snippet": self.code_snippet,
            "conditions": self.conditions,
            "actions": self.actions,
            "entities": self.entities,
            "domain_terms": self.domain_terms,
            "compliance_tags": self.compliance_tags,
            "dependencies": self.dependencies,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class RulePattern:
    """Pattern for detecting business rules in code."""
    name: str
    pattern: str
    category: RuleCategory
    confidence: RuleConfidence
    description_template: str


class SemanticRuleAnalyzer:
    """
    Analyzes code to extract and enhance business rules.

    Uses pattern matching and LLM enhancement to identify:
    - Explicit validation rules
    - Authorization checks
    - Business calculations
    - Workflow state machines
    - Constraint enforcement
    """

    # Common patterns for rule detection
    RULE_PATTERNS: List[RulePattern] = [
        # Validation patterns
        RulePattern(
            name="validation_decorator",
            pattern=r"@validate[_a-z]*\s*\(",
            category=RuleCategory.VALIDATION,
            confidence=RuleConfidence.HIGH,
            description_template="Validation rule for {entity}"
        ),
        RulePattern(
            name="if_validation",
            pattern=r"if\s+(?:not\s+)?[\w.]+\s*(?:is|==|!=|<|>|<=|>=)",
            category=RuleCategory.VALIDATION,
            confidence=RuleConfidence.MEDIUM,
            description_template="Conditional check on {entity}"
        ),
        RulePattern(
            name="raise_validation",
            pattern=r"raise\s+(?:ValueError|ValidationError|InvalidError)",
            category=RuleCategory.VALIDATION,
            confidence=RuleConfidence.HIGH,
            description_template="Validation error for {condition}"
        ),

        # Authorization patterns
        RulePattern(
            name="permission_check",
            pattern=r"(?:has_permission|check_permission|is_authorized|can_access)",
            category=RuleCategory.AUTHORIZATION,
            confidence=RuleConfidence.HIGH,
            description_template="Authorization check for {action}"
        ),
        RulePattern(
            name="role_check",
            pattern=r"(?:user\.role|current_user\.role|has_role)\s*(?:==|in|!=)",
            category=RuleCategory.AUTHORIZATION,
            confidence=RuleConfidence.HIGH,
            description_template="Role-based access control for {role}"
        ),
        RulePattern(
            name="auth_decorator",
            pattern=r"@(?:requires?_auth|login_required|authenticated)",
            category=RuleCategory.AUTHORIZATION,
            confidence=RuleConfidence.HIGH,
            description_template="Authentication required for {endpoint}"
        ),

        # Calculation patterns
        RulePattern(
            name="calculate_method",
            pattern=r"def\s+(?:calculate|compute|total|sum|average)[_a-z]*\s*\(",
            category=RuleCategory.CALCULATION,
            confidence=RuleConfidence.HIGH,
            description_template="Business calculation: {name}"
        ),
        RulePattern(
            name="formula",
            pattern=r"(?:price|total|amount|rate|tax|discount)\s*=\s*[^=]",
            category=RuleCategory.CALCULATION,
            confidence=RuleConfidence.MEDIUM,
            description_template="Calculation of {variable}"
        ),

        # Workflow patterns
        RulePattern(
            name="state_transition",
            pattern=r"(?:status|state)\s*=\s*['\"]?\w+['\"]?",
            category=RuleCategory.WORKFLOW,
            confidence=RuleConfidence.MEDIUM,
            description_template="State transition to {state}"
        ),
        RulePattern(
            name="workflow_decorator",
            pattern=r"@(?:transition|workflow|state_machine)",
            category=RuleCategory.WORKFLOW,
            confidence=RuleConfidence.HIGH,
            description_template="Workflow transition: {transition}"
        ),

        # Constraint patterns
        RulePattern(
            name="constraint_check",
            pattern=r"assert\s+[\w.]+\s*(?:>|<|==|!=|>=|<=)",
            category=RuleCategory.CONSTRAINT,
            confidence=RuleConfidence.HIGH,
            description_template="Constraint: {assertion}"
        ),
        RulePattern(
            name="limit_check",
            pattern=r"(?:max|min|limit|threshold|quota)\s*(?:=|<|>|<=|>=)",
            category=RuleCategory.CONSTRAINT,
            confidence=RuleConfidence.MEDIUM,
            description_template="Limit constraint on {variable}"
        ),

        # Compliance patterns
        RulePattern(
            name="gdpr_pattern",
            pattern=r"(?:consent|anonymize|pseudonymize|data_request|right_to)",
            category=RuleCategory.COMPLIANCE,
            confidence=RuleConfidence.HIGH,
            description_template="GDPR compliance: {requirement}"
        ),
        RulePattern(
            name="audit_logging",
            pattern=r"(?:audit_log|log_access|track_change|record_event)",
            category=RuleCategory.COMPLIANCE,
            confidence=RuleConfidence.HIGH,
            description_template="Audit logging for {event}"
        ),
    ]

    def __init__(
        self,
        domain_vocabulary: Optional[Dict[str, Any]] = None,
        compliance_standards: Optional[List[str]] = None
    ):
        self.domain_vocabulary = domain_vocabulary or {}
        self.compliance_standards = compliance_standards or []
        self._rule_counter = 0

    def analyze_code(
        self,
        code: str,
        file_path: str,
        context: Optional[str] = None
    ) -> List[ExtractedRule]:
        """
        Analyze code to extract business rules.

        Args:
            code: Source code to analyze
            file_path: Path to the source file
            context: Optional context about the code's purpose

        Returns:
            List of extracted business rules
        """
        rules = []
        lines = code.split('\n')

        for pattern in self.RULE_PATTERNS:
            matches = list(re.finditer(pattern.pattern, code, re.IGNORECASE))
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                snippet = self._get_code_snippet(lines, line_num)

                rule = self._create_rule(
                    pattern=pattern,
                    match=match,
                    snippet=snippet,
                    file_path=file_path,
                    line_num=line_num
                )

                # Enhance with domain vocabulary
                rule = self._enhance_with_domain(rule)

                # Tag with compliance standards
                rule = self._tag_compliance(rule)

                rules.append(rule)

        return self._deduplicate_rules(rules)

    def _create_rule(
        self,
        pattern: RulePattern,
        match: re.Match,
        snippet: str,
        file_path: str,
        line_num: int
    ) -> ExtractedRule:
        """Create a rule from a pattern match."""
        self._rule_counter += 1

        # Extract entities from the code snippet
        entities = self._extract_entities(snippet)

        # Extract conditions
        conditions = self._extract_conditions(snippet)

        # Generate description
        description = self._generate_description(
            pattern.description_template,
            snippet,
            entities
        )

        return ExtractedRule(
            id=f"BR-{self._rule_counter:04d}",
            name=f"{pattern.name}_{self._rule_counter}",
            description=description,
            category=pattern.category,
            confidence=pattern.confidence,
            source_file=file_path,
            source_line=line_num,
            code_snippet=snippet,
            conditions=conditions,
            entities=entities
        )

    def _get_code_snippet(
        self,
        lines: List[str],
        line_num: int,
        context_lines: int = 3
    ) -> str:
        """Get code snippet around the matched line."""
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        return '\n'.join(lines[start:end])

    def _extract_entities(self, code: str) -> List[str]:
        """Extract entity names from code."""
        entities = []

        # Class references
        class_refs = re.findall(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)*)\b', code)
        entities.extend(class_refs)

        # Variable names that look like entities
        var_refs = re.findall(r'\b(user|customer|order|product|account|transaction)\b', code, re.IGNORECASE)
        entities.extend([v.lower() for v in var_refs])

        return list(set(entities))

    def _extract_conditions(self, code: str) -> List[str]:
        """Extract conditions from code."""
        conditions = []

        # If conditions
        if_matches = re.findall(r'if\s+(.+?):', code)
        conditions.extend(if_matches)

        # Assert conditions
        assert_matches = re.findall(r'assert\s+(.+?)(?:,|$)', code)
        conditions.extend(assert_matches)

        return conditions

    def _generate_description(
        self,
        template: str,
        snippet: str,
        entities: List[str]
    ) -> str:
        """Generate human-readable description."""
        description = template

        # Replace placeholders
        if "{entity}" in description and entities:
            description = description.replace("{entity}", entities[0])
        if "{name}" in description:
            # Extract function/method name
            name_match = re.search(r'def\s+(\w+)', snippet)
            if name_match:
                description = description.replace("{name}", name_match.group(1))

        # Clean up unreplaced placeholders
        description = re.sub(r'\{[^}]+\}', 'unknown', description)

        return description

    def _enhance_with_domain(self, rule: ExtractedRule) -> ExtractedRule:
        """Enhance rule with domain-specific terminology."""
        if not self.domain_vocabulary:
            return rule

        terms = self.domain_vocabulary.get("terms", {})
        found_terms = []

        for term, info in terms.items():
            patterns = info.get("code_patterns", [])
            for pattern in patterns:
                if re.search(pattern, rule.code_snippet, re.IGNORECASE):
                    found_terms.append(term)
                    # Add PII flag if applicable
                    if info.get("pii"):
                        if "PII" not in rule.compliance_tags:
                            rule.compliance_tags.append("PII")

        rule.domain_terms = list(set(found_terms))
        return rule

    def _tag_compliance(self, rule: ExtractedRule) -> ExtractedRule:
        """Tag rule with applicable compliance standards."""
        snippet_lower = rule.code_snippet.lower()

        # GDPR indicators
        gdpr_indicators = ["consent", "gdpr", "privacy", "data_request", "anonymize", "pseudonymize"]
        if any(ind in snippet_lower for ind in gdpr_indicators):
            if "GDPR" not in rule.compliance_tags:
                rule.compliance_tags.append("GDPR")

        # PCI-DSS indicators
        pci_indicators = ["encrypt", "mask_pan", "tokenize", "card_number", "cvv"]
        if any(ind in snippet_lower for ind in pci_indicators):
            if "PCI-DSS" not in rule.compliance_tags:
                rule.compliance_tags.append("PCI-DSS")

        # SOX indicators
        sox_indicators = ["audit", "approval_workflow", "dual_control", "segregation"]
        if any(ind in snippet_lower for ind in sox_indicators):
            if "SOX" not in rule.compliance_tags:
                rule.compliance_tags.append("SOX")

        # NEN7510 indicators
        nen_indicators = ["phi_access", "rbac", "2fa", "mfa", "session_timeout"]
        if any(ind in snippet_lower for ind in nen_indicators):
            if "NEN7510" not in rule.compliance_tags:
                rule.compliance_tags.append("NEN7510")

        return rule

    def _deduplicate_rules(self, rules: List[ExtractedRule]) -> List[ExtractedRule]:
        """Remove duplicate rules based on code snippet similarity."""
        seen = {}
        unique = []

        for rule in rules:
            # Create a fingerprint
            fingerprint = (
                rule.source_file,
                rule.source_line,
                rule.category.value
            )

            if fingerprint not in seen:
                seen[fingerprint] = True
                unique.append(rule)

        return unique

    def categorize_rules(
        self,
        rules: List[ExtractedRule]
    ) -> Dict[str, List[ExtractedRule]]:
        """Categorize rules by category."""
        categorized = {}
        for rule in rules:
            category = rule.category.value
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(rule)
        return categorized

    def get_compliance_summary(
        self,
        rules: List[ExtractedRule]
    ) -> Dict[str, List[str]]:
        """Get summary of compliance-tagged rules."""
        summary = {}
        for rule in rules:
            for tag in rule.compliance_tags:
                if tag not in summary:
                    summary[tag] = []
                summary[tag].append(rule.id)
        return summary

    def export_rules(
        self,
        rules: List[ExtractedRule],
        format: str = "json"
    ) -> str:
        """Export rules to specified format."""
        if format == "json":
            return json.dumps(
                [r.to_dict() for r in rules],
                indent=2,
                default=str
            )
        elif format == "markdown":
            return self._to_markdown(rules)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _to_markdown(self, rules: List[ExtractedRule]) -> str:
        """Export rules as Markdown."""
        lines = ["# Extracted Business Rules\n"]

        categorized = self.categorize_rules(rules)

        for category, cat_rules in categorized.items():
            lines.append(f"\n## {category.title()}\n")

            for rule in cat_rules:
                lines.append(f"### {rule.id}: {rule.name}")
                lines.append(f"**Description**: {rule.description}")
                lines.append(f"**Confidence**: {rule.confidence.value}")
                lines.append(f"**Source**: `{rule.source_file}:{rule.source_line}`")

                if rule.conditions:
                    lines.append(f"**Conditions**: {', '.join(rule.conditions)}")
                if rule.entities:
                    lines.append(f"**Entities**: {', '.join(rule.entities)}")
                if rule.compliance_tags:
                    lines.append(f"**Compliance**: {', '.join(rule.compliance_tags)}")

                lines.append(f"\n```python\n{rule.code_snippet}\n```\n")

        return '\n'.join(lines)


# LLM Enhancement interface (to be implemented with actual LLM)
class LLMRuleEnhancer:
    """
    Enhances extracted rules using LLM analysis.

    This is a placeholder for LLM integration. In production,
    this would use the provider registry to call the configured LLM.
    """

    def __init__(self, provider_name: str = "ollama"):
        self.provider_name = provider_name

    async def enhance_rule(
        self,
        rule: ExtractedRule,
        context: Optional[str] = None
    ) -> ExtractedRule:
        """
        Use LLM to enhance rule description and categorization.

        In production, this would:
        1. Send the code snippet to LLM
        2. Ask for business rule interpretation
        3. Get improved description and categorization
        4. Identify related rules and dependencies
        """
        # Placeholder - returns rule unchanged
        # TODO: Integrate with provider registry
        return rule

    async def identify_implicit_rules(
        self,
        code: str,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to identify implicit business rules.

        Implicit rules are not expressed as explicit conditions
        but are embedded in the code structure.
        """
        # Placeholder - returns empty list
        # TODO: Integrate with provider registry
        return []

    async def generate_rule_documentation(
        self,
        rules: List[ExtractedRule]
    ) -> str:
        """
        Generate comprehensive documentation for rules.
        """
        # Placeholder - uses basic markdown export
        analyzer = SemanticRuleAnalyzer()
        return analyzer.export_rules(rules, format="markdown")
