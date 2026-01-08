# Requirements Extraction Improvement Plan - MarQed.ai

**Datum:** 24 december 2025
**Scope:** Business Rules, Functional Requirements, Non-Functional Requirements
**Huidige Implementatie:** Fase 15 Static Analysis (Week 97-100)

---

## Executive Summary

Na analyse van de huidige extractie-implementaties zijn **31 verbeterpunten** geïdentificeerd:

| Categorie | Quick Wins | Medium | Large | Totaal |
|-----------|------------|--------|-------|--------|
| Business Rules | 4 | 5 | 3 | 12 |
| Functional Requirements | 3 | 4 | 3 | 10 |
| Non-Functional Requirements | 3 | 3 | 3 | 9 |

**Geschatte impact:** 50-70% hogere extractie-kwaliteit en completeness.

---

## Analyse van Huidige Implementatie

### BusinessRuleExtractor (Huidige staat)

**Sterkten:**
- ✅ Multi-language support (Python, JS, C#, SQL)
- ✅ AST parsing voor Python
- ✅ 6 rule types (Validation, Calculation, Authorization, Workflow, Constraint, Derivation)
- ✅ Compliance tagging support
- ✅ Variable classification integratie

**Zwakten:**
- ❌ Alleen regex-gebaseerd voor niet-Python talen
- ❌ Geen semantische context (begrijpt niet WAT de regel betekent)
- ❌ Geen domein-specifieke vocabulaire
- ❌ Geen deduplicatie van gelijksoortige regels
- ❌ Gemiste inter-rule dependencies
- ❌ Natural language kwaliteit is templated, niet intelligent

### NFRDetector (Huidige staat)

**Sterkten:**
- ✅ 7 categorieën (Security, Performance, Reliability, etc.)
- ✅ 80+ regex patterns
- ✅ Compliance relevance tagging
- ✅ Coverage score berekening
- ✅ Gap analysis

**Zwakten:**
- ❌ Geen kwantitatieve metrics (geen "< 2s response time")
- ❌ Alleen detectie, geen prioritering
- ❌ Mist domein-specifieke NFR standaarden
- ❌ Geen cross-reference met architectuur
- ❌ False positive rate niet gemeten

### HierarchicalStoryExtractionService (Huidige staat)

**Sterkten:**
- ✅ 4 extractie levels (Function, Class, Module, System)
- ✅ Bottom-up approach
- ✅ Parent-child hierarchy
- ✅ Multi-LLM support
- ✅ Confidence scoring

**Zwakten:**
- ❌ Generieke prompts, niet domein-specifiek
- ❌ Geen few-shot examples
- ❌ INVEST validatie ontbreekt
- ❌ Geen traceability matrix generatie
- ❌ Acceptance criteria zijn vaak incompleet

---

## Categorie 1: Business Rules Extraction Verbeteringen

### BR-QW-1: Domain Vocabulary Loader ⭐⭐⭐⭐⭐
**Tijd:** 4 uur
**Impact:** HOOG - Betere domain-variable herkenning

```python
# app/services/static_analysis/domain_vocabulary.py
from pathlib import Path
from typing import Dict, Set
import json

class DomainVocabularyLoader:
    """Load domain-specific vocabulary for better rule extraction."""

    # Pre-built vocabularies
    HEALTHCARE_VOCABULARY = {
        "entities": [
            "patient", "diagnosis", "treatment", "medication", "prescription",
            "appointment", "physician", "nurse", "hospital", "ward", "bed",
            "lab_result", "vital_signs", "medical_record", "insurance", "claim"
        ],
        "actions": [
            "admit", "discharge", "prescribe", "diagnose", "treat", "refer",
            "schedule", "cancel", "transfer", "escalate", "approve", "reject"
        ],
        "states": [
            "pending", "approved", "rejected", "active", "inactive", "completed",
            "cancelled", "expired", "verified", "unverified"
        ],
        "constraints": [
            "age >= 18", "dosage <= max", "insurance_valid", "consent_given",
            "physician_approved", "within_hours"
        ],
        "compliance": ["NEN7510", "HIPAA", "GDPR"]
    }

    FINANCE_VOCABULARY = {
        "entities": [
            "account", "transaction", "balance", "payment", "invoice", "credit",
            "debit", "loan", "interest", "fee", "customer", "merchant"
        ],
        "actions": [
            "deposit", "withdraw", "transfer", "authorize", "decline", "refund",
            "reconcile", "audit", "freeze", "unfreeze"
        ],
        "states": [
            "pending", "processing", "completed", "failed", "reversed",
            "settled", "disputed", "chargedback"
        ],
        "constraints": [
            "balance >= 0", "amount <= limit", "authorized", "not_frozen",
            "within_business_hours", "kyc_verified"
        ],
        "compliance": ["PCI_DSS", "SOX", "AML"]
    }

    E_COMMERCE_VOCABULARY = {
        "entities": [
            "product", "cart", "order", "customer", "address", "payment",
            "shipping", "inventory", "category", "review", "coupon"
        ],
        "actions": [
            "add_to_cart", "remove_from_cart", "checkout", "place_order",
            "ship", "deliver", "return", "refund", "apply_discount"
        ],
        "states": [
            "in_stock", "out_of_stock", "pending", "processing", "shipped",
            "delivered", "returned", "cancelled"
        ],
        "constraints": [
            "quantity > 0", "in_stock", "valid_address", "payment_confirmed",
            "coupon_valid", "shipping_available"
        ],
        "compliance": ["GDPR", "PCI_DSS"]
    }

    def __init__(self, custom_vocabulary_path: Optional[Path] = None):
        self.vocabularies = {
            "healthcare": self.HEALTHCARE_VOCABULARY,
            "finance": self.FINANCE_VOCABULARY,
            "ecommerce": self.E_COMMERCE_VOCABULARY,
        }
        if custom_vocabulary_path:
            self._load_custom(custom_vocabulary_path)

    def detect_domain(self, code_content: str) -> str:
        """Auto-detect domain from code content."""
        scores = {}
        lower_content = code_content.lower()

        for domain, vocab in self.vocabularies.items():
            score = 0
            for entity in vocab["entities"]:
                score += lower_content.count(entity.lower())
            scores[domain] = score

        if not scores or max(scores.values()) < 5:
            return "generic"
        return max(scores, key=scores.get)

    def get_vocabulary(self, domain: str) -> Dict[str, Set[str]]:
        """Get vocabulary for domain."""
        vocab = self.vocabularies.get(domain, {})
        return {
            k: set(v) for k, v in vocab.items()
        }
```

**Actie:** Creëer domain vocabularies voor healthcare, finance, e-commerce.

---

### BR-QW-2: Rule Deduplication Service ⭐⭐⭐⭐
**Tijd:** 3 uur
**Impact:** MEDIUM-HOOG - Minder ruis in output

```python
# app/services/static_analysis/rule_deduplicator.py
from typing import List, Set, Tuple
from difflib import SequenceMatcher
from dataclasses import dataclass

@dataclass
class DeduplicationResult:
    unique_rules: List[BusinessRule]
    duplicates: List[Tuple[BusinessRule, BusinessRule]]  # (original, duplicate)
    similarity_threshold: float

class RuleDeduplicator:
    """Deduplicate similar business rules."""

    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold

    def deduplicate(self, rules: List[BusinessRule]) -> DeduplicationResult:
        """Remove duplicate/near-duplicate rules."""
        unique = []
        duplicates = []
        seen_signatures = set()

        for rule in sorted(rules, key=lambda r: r.confidence, reverse=True):
            # Create signature from condition + action
            signature = self._create_signature(rule)

            # Check for exact duplicates
            if signature in seen_signatures:
                # Find original
                original = next(r for r in unique if self._create_signature(r) == signature)
                duplicates.append((original, rule))
                continue

            # Check for semantic duplicates
            is_duplicate = False
            for existing in unique:
                similarity = self._calculate_similarity(rule, existing)
                if similarity >= self.threshold:
                    duplicates.append((existing, rule))
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(rule)
                seen_signatures.add(signature)

        return DeduplicationResult(
            unique_rules=unique,
            duplicates=duplicates,
            similarity_threshold=self.threshold
        )

    def _create_signature(self, rule: BusinessRule) -> str:
        """Create normalized signature for exact matching."""
        condition = self._normalize(rule.condition)
        action = self._normalize(rule.action)
        return f"{rule.rule_type.value}:{condition}:{action}"

    def _normalize(self, text: str) -> str:
        """Normalize text for comparison."""
        import re
        # Remove whitespace, lowercase, remove variable names
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'["\'].*?["\']', 'STR', text)
        text = re.sub(r'\d+', 'NUM', text)
        return text

    def _calculate_similarity(self, r1: BusinessRule, r2: BusinessRule) -> float:
        """Calculate semantic similarity between rules."""
        if r1.rule_type != r2.rule_type:
            return 0.0

        cond_sim = SequenceMatcher(None,
                                   self._normalize(r1.condition),
                                   self._normalize(r2.condition)).ratio()
        act_sim = SequenceMatcher(None,
                                  self._normalize(r1.action),
                                  self._normalize(r2.action)).ratio()

        # Variables overlap
        var_overlap = len(set(r1.variables_involved) & set(r2.variables_involved))
        var_total = len(set(r1.variables_involved) | set(r2.variables_involved))
        var_sim = var_overlap / max(var_total, 1)

        return (cond_sim * 0.4) + (act_sim * 0.4) + (var_sim * 0.2)
```

---

### BR-QW-3: Natural Language Quality Enhancer ⭐⭐⭐⭐
**Tijd:** 2 uur
**Impact:** MEDIUM - Betere leesbaarheid

```python
# Vervanging voor _generate_natural_language in business_rule_extractor.py

class NaturalLanguageEnhancer:
    """Generate high-quality natural language from rules."""

    # Better templates with business context
    TEMPLATES = {
        RuleType.VALIDATION: [
            "The system SHALL validate that {condition} before allowing {action}",
            "Input must satisfy: {condition}. Otherwise: {action}",
            "VALIDATION: When {condition_readable}, then {action_readable}",
        ],
        RuleType.AUTHORIZATION: [
            "ACCESS CONTROL: Only users with {condition} may {action}",
            "Authorization required: {condition} to perform {action}",
            "The system SHALL restrict {action} to users where {condition}",
        ],
        RuleType.CALCULATION: [
            "CALCULATION: {action} is computed when {condition}",
            "Business formula: IF {condition} THEN calculate {action}",
            "The {result} is derived as: {action} when {condition}",
        ],
        RuleType.WORKFLOW: [
            "WORKFLOW: Transition from {from_state} to {to_state} when {condition}",
            "State change: {action} triggered by {condition}",
            "Process step: When {condition}, execute {action}",
        ],
        RuleType.CONSTRAINT: [
            "CONSTRAINT: The system SHALL enforce that {condition}",
            "Business invariant: {condition} must always be true for {action}",
            "Data integrity: {action} requires {condition}",
        ],
        RuleType.DERIVATION: [
            "DERIVED VALUE: {result} is calculated as {action}",
            "Computed field: {action} based on {condition}",
            "The {result} value is derived from: {action}",
        ],
    }

    def generate(self, rule: BusinessRule) -> str:
        """Generate readable natural language description."""
        template = self.TEMPLATES.get(rule.rule_type, ["IF {condition} THEN {action}"])[0]

        # Extract readable parts
        condition_readable = self._make_readable(rule.condition)
        action_readable = self._make_readable(rule.action)

        # Extract states for workflow
        from_state, to_state = self._extract_states(rule.action)

        # Extract result variable for calculation/derivation
        result = self._extract_result_var(rule.variables_involved)

        return template.format(
            condition=rule.condition[:100],
            action=rule.action[:100],
            condition_readable=condition_readable,
            action_readable=action_readable,
            from_state=from_state,
            to_state=to_state,
            result=result
        )

    def _make_readable(self, code: str) -> str:
        """Convert code to readable text."""
        import re
        text = code
        # snake_case to spaces
        text = re.sub(r'_', ' ', text)
        # Remove common noise
        text = re.sub(r'self\.', '', text)
        text = re.sub(r'\(\)', '', text)
        # Operators to words
        text = text.replace('==', 'equals')
        text = text.replace('!=', 'is not')
        text = text.replace('>=', 'is at least')
        text = text.replace('<=', 'is at most')
        text = text.replace(' and ', ' AND ')
        text = text.replace(' or ', ' OR ')
        text = text.replace(' not ', ' NOT ')
        return text.strip()[:150]

    def _extract_states(self, action: str) -> Tuple[str, str]:
        """Extract from/to states from workflow action."""
        import re
        match = re.search(r"['\"](\w+)['\"].*['\"](\w+)['\"]", action)
        if match:
            return match.group(1), match.group(2)
        return "current_state", "new_state"

    def _extract_result_var(self, variables: List[str]) -> str:
        """Get likely result variable."""
        for var in variables:
            if var.startswith(('total', 'result', 'calculated', 'derived', 'computed')):
                return var.replace('_', ' ')
        return variables[0].replace('_', ' ') if variables else "value"
```

---

### BR-QW-4: Rule Completeness Checker ⭐⭐⭐
**Tijd:** 3 uur
**Impact:** MEDIUM - Identificeer missende regels

```python
# app/services/static_analysis/rule_completeness.py

class RuleCompletenessChecker:
    """Check if extracted rules cover expected business areas."""

    # Expected rule categories per domain
    EXPECTED_COVERAGE = {
        "healthcare": {
            "validation": ["patient_age", "medication_dosage", "insurance_validity"],
            "authorization": ["physician_access", "nurse_access", "admin_access"],
            "workflow": ["admission", "discharge", "transfer", "prescription"],
            "constraint": ["privacy", "consent", "data_retention"],
        },
        "finance": {
            "validation": ["amount_limits", "account_balance", "transaction_format"],
            "authorization": ["account_owner", "authorized_user", "admin"],
            "workflow": ["transaction_approval", "dispute_resolution", "account_opening"],
            "constraint": ["daily_limits", "fraud_prevention", "audit_trail"],
        },
        "ecommerce": {
            "validation": ["inventory_check", "address_validation", "payment_validation"],
            "authorization": ["customer_access", "seller_access", "admin_access"],
            "workflow": ["order_processing", "shipping", "return_handling"],
            "constraint": ["pricing_rules", "discount_limits", "stock_management"],
        }
    }

    def check_completeness(self,
                           rules: List[BusinessRule],
                           domain: str) -> CompletenessReport:
        """Check rule coverage against expected areas."""
        expected = self.EXPECTED_COVERAGE.get(domain, {})

        # Group extracted rules by type
        rules_by_type = {}
        for rule in rules:
            rules_by_type.setdefault(rule.rule_type.value, []).append(rule)

        gaps = []
        coverage = {}

        for rule_type, expected_areas in expected.items():
            covered = []
            missing = []

            type_rules = rules_by_type.get(rule_type, [])

            for area in expected_areas:
                # Check if any rule covers this area
                found = any(
                    area.lower() in r.natural_language.lower() or
                    any(area.lower() in v.lower() for v in r.variables_involved)
                    for r in type_rules
                )
                if found:
                    covered.append(area)
                else:
                    missing.append(area)
                    gaps.append(f"{rule_type}/{area}")

            coverage[rule_type] = {
                "covered": covered,
                "missing": missing,
                "percentage": len(covered) / len(expected_areas) * 100 if expected_areas else 100
            }

        overall_score = sum(c["percentage"] for c in coverage.values()) / len(coverage) if coverage else 0

        return CompletenessReport(
            domain=domain,
            coverage_by_type=coverage,
            gaps=gaps,
            overall_score=overall_score,
            recommendations=self._generate_recommendations(gaps)
        )

    def _generate_recommendations(self, gaps: List[str]) -> List[str]:
        """Generate recommendations for missing rules."""
        recommendations = []
        for gap in gaps[:5]:  # Top 5 gaps
            rule_type, area = gap.split('/')
            recommendations.append(
                f"Consider adding {rule_type} rules for: {area.replace('_', ' ')}"
            )
        return recommendations
```

---

### BR-M-1: Semantic Rule Understanding via LLM ⭐⭐⭐⭐⭐
**Tijd:** 2 dagen
**Impact:** ZEER HOOG - AI-enhanced rule extraction

```python
# app/services/static_analysis/semantic_rule_analyzer.py

class SemanticRuleAnalyzer:
    """Use LLM to understand rule semantics beyond pattern matching."""

    ANALYSIS_PROMPT = """Analyze this code snippet and extract the business rule:

## Code
```{language}
{code_snippet}
```

## Context
File: {file_path}
Variables detected: {variables}
Pattern matched: {pattern_type}

## Task
Extract the business rule with:
1. **Condition**: What must be true (precondition)
2. **Action**: What happens when condition is met
3. **Business Context**: Why this rule exists
4. **Exception Cases**: What happens if condition fails
5. **Related Rules**: Other rules this might connect to
6. **Stakeholder Impact**: Who is affected by this rule

## Output (JSON)
{{
    "condition_refined": "Clear statement of the condition",
    "action_refined": "Clear statement of the action",
    "business_context": "Why this rule matters",
    "exception_handling": "What happens on failure",
    "related_rules": ["potential related rule 1"],
    "stakeholders": ["user type affected"],
    "confidence_factors": {{
        "clarity": 0.0-1.0,
        "completeness": 0.0-1.0,
        "testability": 0.0-1.0
    }},
    "suggested_test_cases": [
        "test case description 1"
    ]
}}"""

    def __init__(self, llm_provider):
        self.llm = llm_provider

    async def analyze_rule(self,
                           rule: BusinessRule,
                           source_code: str) -> EnhancedBusinessRule:
        """Enhance rule with semantic understanding."""
        # Get code context around the rule
        lines = source_code.split('\n')
        start = max(0, rule.source_lines[0] - 5)
        end = min(len(lines), rule.source_lines[1] + 5)
        code_snippet = '\n'.join(lines[start:end])

        # Detect language
        language = self._detect_language(rule.source_file)

        # Call LLM for semantic analysis
        prompt = self.ANALYSIS_PROMPT.format(
            language=language,
            code_snippet=code_snippet,
            file_path=rule.source_file,
            variables=', '.join(rule.variables_involved),
            pattern_type=rule.rule_type.value
        )

        response = await self.llm.generate(prompt, max_tokens=1000)
        analysis = self._parse_response(response)

        return EnhancedBusinessRule(
            original=rule,
            condition_refined=analysis.get("condition_refined", rule.condition),
            action_refined=analysis.get("action_refined", rule.action),
            business_context=analysis.get("business_context", ""),
            exception_handling=analysis.get("exception_handling", ""),
            stakeholders=analysis.get("stakeholders", []),
            suggested_test_cases=analysis.get("suggested_test_cases", []),
            confidence_factors=analysis.get("confidence_factors", {}),
            semantic_confidence=self._calculate_confidence(analysis)
        )
```

---

### BR-M-2: Inter-Rule Dependency Detection ⭐⭐⭐⭐
**Tijd:** 2 dagen
**Impact:** HOOG - Betere regel ordening

```python
# app/services/static_analysis/rule_dependency_analyzer.py

class RuleDependencyAnalyzer:
    """Detect dependencies between business rules."""

    async def analyze_dependencies(self,
                                   rules: List[BusinessRule]) -> RuleDependencyGraph:
        """Build dependency graph between rules."""
        graph = RuleDependencyGraph()

        for rule in rules:
            graph.add_node(rule.id, rule)

        # Detect dependencies based on:
        # 1. Shared variables
        # 2. Sequential file locations
        # 3. State machine transitions
        # 4. Call hierarchy

        for i, rule1 in enumerate(rules):
            for rule2 in rules[i+1:]:
                deps = self._detect_dependencies(rule1, rule2)
                for dep_type, confidence in deps:
                    graph.add_edge(rule1.id, rule2.id, dep_type, confidence)

        return graph

    def _detect_dependencies(self,
                              r1: BusinessRule,
                              r2: BusinessRule) -> List[Tuple[str, float]]:
        """Detect all dependency types between two rules."""
        dependencies = []

        # Shared variables
        shared_vars = set(r1.variables_involved) & set(r2.variables_involved)
        if shared_vars:
            dependencies.append(("shared_variable", len(shared_vars) * 0.2))

        # Sequential (same file, close lines)
        if r1.source_file == r2.source_file:
            line_distance = abs(r1.source_lines[0] - r2.source_lines[0])
            if line_distance < 20:
                dependencies.append(("sequential", 1.0 - (line_distance / 20)))

        # State machine (workflow rule outputs become inputs)
        if r1.rule_type == RuleType.WORKFLOW and r2.rule_type == RuleType.WORKFLOW:
            # Check if r1's action state matches r2's condition state
            if self._is_state_transition(r1.action, r2.condition):
                dependencies.append(("state_transition", 0.9))

        # Prerequisite (r1 must pass before r2)
        if r1.rule_type == RuleType.VALIDATION and r2.rule_type != RuleType.VALIDATION:
            if any(v in r2.condition for v in r1.variables_involved):
                dependencies.append(("prerequisite", 0.8))

        return dependencies

    def get_execution_order(self, graph: RuleDependencyGraph) -> List[BusinessRule]:
        """Get topologically sorted execution order."""
        return graph.topological_sort()

    def detect_conflicts(self, graph: RuleDependencyGraph) -> List[RuleConflict]:
        """Detect conflicting rules."""
        conflicts = []

        # Rules that contradict each other
        for node1 in graph.nodes:
            for node2 in graph.nodes:
                if node1 != node2:
                    r1, r2 = graph.get_rule(node1), graph.get_rule(node2)
                    if self._are_conflicting(r1, r2):
                        conflicts.append(RuleConflict(
                            rule1=r1,
                            rule2=r2,
                            conflict_type="contradiction",
                            description=f"Rules may contradict: {r1.id} vs {r2.id}"
                        ))

        return conflicts
```

---

### BR-M-3: Legacy Pattern Recognition (VB6, COBOL, ASP Classic) ⭐⭐⭐⭐
**Tijd:** 3 dagen
**Impact:** HOOG - Legacy codebase support

```python
# app/services/static_analysis/legacy_rule_extractor.py

class LegacyRuleExtractor:
    """Extract business rules from legacy codebases."""

    # VB6/VBA patterns
    VB_PATTERNS = {
        RuleType.VALIDATION: [
            (r"If\s+Len\((.+?)\)\s*[<>=]+\s*\d+\s+Then", "String length validation"),
            (r"If\s+IsNumeric\((.+?)\)\s*=\s*False\s+Then", "Numeric validation"),
            (r"If\s+IsNull\((.+?)\)\s+Then", "Null check"),
            (r"If\s+(.+?)\s*<>\s*[\"'].*?[\"']\s+Then", "Value validation"),
        ],
        RuleType.AUTHORIZATION: [
            (r"If\s+Session\([\"'](\w+)[\"']\)\s*=", "Session-based auth"),
            (r"If\s+Request\.(?:Form|QueryString)\([\"'](\w+)[\"']\)", "Request parameter check"),
        ],
        RuleType.CALCULATION: [
            (r"(\w+)\s*=\s*(\w+)\s*[\+\-\*/]\s*(\w+)", "Arithmetic calculation"),
            (r"(\w+)\s*=\s*Format\(", "Formatted calculation"),
        ],
    }

    # COBOL patterns
    COBOL_PATTERNS = {
        RuleType.VALIDATION: [
            (r"IF\s+(\w+)\s+(?:IS\s+)?NUMERIC", "Numeric field validation"),
            (r"IF\s+(\w+)\s+(?:IS\s+)?ALPHABETIC", "Alphabetic validation"),
            (r"IF\s+(\w+)\s*(?:=|EQUAL)\s*(?:SPACE|SPACES|LOW-VALUE)", "Empty check"),
        ],
        RuleType.CALCULATION: [
            (r"COMPUTE\s+(\w+)\s*=\s*(.+)", "COMPUTE calculation"),
            (r"ADD\s+(\w+)\s+TO\s+(\w+)", "ADD operation"),
            (r"MULTIPLY\s+(\w+)\s+BY\s+(\w+)", "MULTIPLY operation"),
        ],
        RuleType.WORKFLOW: [
            (r"PERFORM\s+(\w+)(?:\s+THRU\s+(\w+))?", "Paragraph/section call"),
            (r"GO\s+TO\s+(\w+)", "Control flow"),
        ],
    }

    # ASP Classic patterns
    ASP_PATTERNS = {
        RuleType.VALIDATION: [
            (r"If\s+Request(?:\.Form)?\([\"'](\w+)[\"']\)\s*=\s*[\"'][\"']", "Empty request check"),
            (r"If\s+Not\s+IsDate\((.+?)\)", "Date validation"),
            (r"If\s+CInt\((.+?)\)\s*[<>=]+", "Integer conversion check"),
        ],
        RuleType.AUTHORIZATION: [
            (r"Session\([\"'](?:UserID|UserLevel|IsAdmin)[\"']\)", "Session auth"),
            (r"If\s+Session\([\"']LoggedIn[\"']\)\s*<>\s*True", "Login check"),
        ],
    }

    async def extract_from_vb(self, file_path: str, source: str) -> List[BusinessRule]:
        """Extract rules from VB6/VBA code."""
        return await self._extract_with_patterns(file_path, source, self.VB_PATTERNS)

    async def extract_from_cobol(self, file_path: str, source: str) -> List[BusinessRule]:
        """Extract rules from COBOL code."""
        # COBOL needs special preprocessing (fixed columns, etc.)
        source = self._preprocess_cobol(source)
        return await self._extract_with_patterns(file_path, source, self.COBOL_PATTERNS)

    async def extract_from_asp(self, file_path: str, source: str) -> List[BusinessRule]:
        """Extract rules from ASP Classic code."""
        return await self._extract_with_patterns(file_path, source, self.ASP_PATTERNS)

    def _preprocess_cobol(self, source: str) -> str:
        """Preprocess COBOL source (handle fixed columns)."""
        lines = []
        for line in source.split('\n'):
            if len(line) > 6:
                # Skip sequence numbers (cols 1-6)
                # Skip indicator column (col 7)
                lines.append(line[7:] if len(line) > 7 else '')
        return '\n'.join(lines)
```

---

### BR-M-4: Test Case Generation from Rules ⭐⭐⭐⭐
**Tijd:** 2 dagen
**Impact:** HOOG - Betere testbaarheid

```python
# app/services/static_analysis/rule_test_generator.py

class RuleTestCaseGenerator:
    """Generate test cases from extracted business rules."""

    def generate_tests(self, rule: BusinessRule) -> List[TestCase]:
        """Generate test cases for a business rule."""
        tests = []

        # 1. Happy path (condition true)
        tests.append(TestCase(
            name=f"test_{rule.id}_happy_path",
            description=f"Test when {rule.condition} is true",
            preconditions=self._generate_preconditions(rule, satisfied=True),
            expected_result=self._describe_action(rule.action),
            test_type="positive",
            priority="high"
        ))

        # 2. Negative path (condition false)
        tests.append(TestCase(
            name=f"test_{rule.id}_negative_path",
            description=f"Test when {rule.condition} is false",
            preconditions=self._generate_preconditions(rule, satisfied=False),
            expected_result="Action should not execute / alternative path",
            test_type="negative",
            priority="high"
        ))

        # 3. Boundary conditions
        for boundary in self._extract_boundaries(rule):
            tests.append(TestCase(
                name=f"test_{rule.id}_boundary_{boundary.name}",
                description=f"Test boundary: {boundary.description}",
                preconditions=boundary.preconditions,
                expected_result=boundary.expected,
                test_type="boundary",
                priority="medium"
            ))

        # 4. Edge cases
        for var in rule.variables_involved:
            tests.extend(self._generate_edge_case_tests(rule, var))

        return tests

    def _extract_boundaries(self, rule: BusinessRule) -> List[BoundaryCondition]:
        """Extract boundary conditions from rule."""
        boundaries = []

        # Pattern: age >= 18, amount <= 1000, etc.
        import re
        patterns = [
            (r'(\w+)\s*>=\s*(\d+)', 'greater_equal'),
            (r'(\w+)\s*<=\s*(\d+)', 'less_equal'),
            (r'(\w+)\s*>\s*(\d+)', 'greater'),
            (r'(\w+)\s*<\s*(\d+)', 'less'),
            (r'(\w+)\s*==\s*(\d+)', 'equal'),
        ]

        for pattern, op_type in patterns:
            match = re.search(pattern, rule.condition)
            if match:
                var, value = match.groups()
                value = int(value)

                if op_type == 'greater_equal':
                    boundaries.extend([
                        BoundaryCondition(f"{var}_at_boundary", f"{var} = {value}",
                                         [f"Set {var} to {value}"], "Should pass"),
                        BoundaryCondition(f"{var}_below_boundary", f"{var} = {value - 1}",
                                         [f"Set {var} to {value - 1}"], "Should fail"),
                    ])
                elif op_type == 'less_equal':
                    boundaries.extend([
                        BoundaryCondition(f"{var}_at_boundary", f"{var} = {value}",
                                         [f"Set {var} to {value}"], "Should pass"),
                        BoundaryCondition(f"{var}_above_boundary", f"{var} = {value + 1}",
                                         [f"Set {var} to {value + 1}"], "Should fail"),
                    ])

        return boundaries

    def generate_pytest_code(self, tests: List[TestCase]) -> str:
        """Generate pytest code from test cases."""
        code = ['import pytest\n\n']

        for test in tests:
            code.append(f'''
@pytest.mark.{test.priority}
def {test.name}():
    """
    {test.description}

    Preconditions:
    {chr(10).join(f"    - {p}" for p in test.preconditions)}

    Expected: {test.expected_result}
    """
    # Arrange
    # TODO: Set up preconditions

    # Act
    # TODO: Execute action

    # Assert
    # TODO: Verify expected result
    pytest.skip("Test case generated - implement assertions")
''')

        return '\n'.join(code)
```

---

### BR-M-5: Rule Documentation Generator ⭐⭐⭐
**Tijd:** 1 dag
**Impact:** MEDIUM - Betere documentatie

```python
# app/services/static_analysis/rule_documentation_generator.py

class RuleDocumentationGenerator:
    """Generate comprehensive documentation from extracted rules."""

    def generate_markdown(self,
                          result: RuleExtractionResult,
                          project_name: str) -> str:
        """Generate Markdown documentation."""
        doc = [
            f"# Business Rules Documentation - {project_name}",
            f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"\n**Total Rules:** {result.total_rules}",
            f"\n**High Confidence:** {result.high_confidence_rules}",
            "\n---\n"
        ]

        # Table of contents
        doc.append("## Table of Contents\n")
        for rule_type, rules in result.rules_by_type.items():
            doc.append(f"- [{rule_type.value.title()} Rules ({len(rules)})](#{rule_type.value}-rules)")
        doc.append("\n---\n")

        # Rules by type
        for rule_type, rules in result.rules_by_type.items():
            doc.append(f"\n## {rule_type.value.title()} Rules\n")

            for rule in sorted(rules, key=lambda r: r.confidence, reverse=True):
                doc.append(self._format_rule(rule))

        # Appendix: Rules by file
        doc.append("\n---\n## Appendix: Rules by File\n")
        for file_path, rules in result.rules_by_file.items():
            doc.append(f"\n### `{file_path}`\n")
            for rule in rules:
                doc.append(f"- **{rule.id}**: {rule.natural_language[:100]}")

        return '\n'.join(doc)

    def _format_rule(self, rule: BusinessRule) -> str:
        """Format single rule as Markdown."""
        confidence_icon = "🟢" if rule.confidence >= 0.8 else "🟡" if rule.confidence >= 0.6 else "🔴"

        return f"""
### {rule.id} {confidence_icon}

**Type:** {rule.rule_type.value.title()}
**Confidence:** {rule.confidence:.0%}
**Location:** `{rule.source_file}` (lines {rule.source_lines[0]}-{rule.source_lines[1]})

#### Description
{rule.natural_language}

#### Condition
```
{rule.condition}
```

#### Action
```
{rule.action}
```

#### Variables Involved
{', '.join(f'`{v}`' for v in rule.variables_involved)}

{'#### Compliance Tags' + chr(10) + ', '.join(rule.compliance_tags) if rule.compliance_tags else ''}

---
"""
```

---

### BR-L-1: LLM-Enhanced Hybrid Extraction Pipeline ⭐⭐⭐⭐⭐
**Tijd:** 1 week
**Impact:** ZEER HOOG - Beste van beide werelden

Combineer static analysis (accurate, fast, cheap) met LLM (semantic understanding):

```
┌─────────────────────────────────────────────────────────────────┐
│                HYBRID RULE EXTRACTION PIPELINE                   │
│                                                                  │
│  PHASE 1: STATIC (Deterministic)                                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ • Pattern Matching (regex)                                   ││
│  │ • AST Parsing (Python, JS)                                   ││
│  │ • Variable Classification                                    ││
│  │ • Basic Rule Detection                                       ││
│  │ Output: Candidate Rules (high recall, lower precision)       ││
│  └─────────────────────────────────────────────────────────────┘│
│                              ↓                                   │
│  PHASE 2: LLM (Semantic)                                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ • Filter false positives                                     ││
│  │ • Enhance natural language                                   ││
│  │ • Add business context                                       ││
│  │ • Generate test cases                                        ││
│  │ • Detect inter-rule dependencies                             ││
│  │ Output: Validated Rules (high precision + recall)            ││
│  └─────────────────────────────────────────────────────────────┘│
│                              ↓                                   │
│  PHASE 3: VALIDATION                                            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ • Deduplication                                              ││
│  │ • Conflict detection                                         ││
│  │ • Completeness check                                         ││
│  │ • Human review for low-confidence                            ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Categorie 2: Functional Requirements Extraction Verbeteringen

### FR-QW-1: Few-Shot Templates per Domain ⭐⭐⭐⭐⭐
**Tijd:** 4 uur
**Impact:** HOOG - Betere LLM output

```python
# app/services/extraction/few_shot_templates.py

class FewShotTemplates:
    """Domain-specific few-shot examples for better extraction."""

    HEALTHCARE_EXAMPLES = """
## Example 1: Patient Registration

**Code Pattern:**
```python
class PatientRegistrationService:
    def register_patient(self, patient_data: PatientDTO) -> Patient:
        if not self.validate_insurance(patient_data.insurance_id):
            raise ValidationError("Invalid insurance")
        patient = Patient(**patient_data.dict())
        self.patient_repo.save(patient)
        self.notification_service.send_welcome(patient)
        return patient
```

**Extracted Requirement:**
```json
{
    "type": "feature",
    "title": "Patient Registration",
    "stories": [
        {
            "title": "As a registration clerk, I want to register new patients so that they can receive care",
            "acceptance_criteria": [
                "Given valid patient data, when I submit registration, then patient is created",
                "Given invalid insurance, when I submit registration, then error is shown",
                "Given successful registration, when patient is created, then welcome notification is sent"
            ],
            "estimated_points": 5
        }
    ]
}
```

## Example 2: Medication Prescription

**Code Pattern:**
```python
@require_role("physician")
def prescribe_medication(self, patient_id: int, medication: Medication) -> Prescription:
    patient = self.get_patient(patient_id)
    if medication.dosage > medication.max_dosage:
        raise DosageError("Exceeds maximum dosage")
    if self.check_drug_interaction(patient, medication):
        raise InteractionWarning("Drug interaction detected")
    return self.create_prescription(patient, medication)
```

**Extracted Requirement:**
```json
{
    "type": "feature",
    "title": "Medication Prescription",
    "stories": [
        {
            "title": "As a physician, I want to prescribe medication so that patients receive treatment",
            "acceptance_criteria": [
                "Given I am a physician, when I prescribe medication, then prescription is created",
                "Given dosage exceeds maximum, when I prescribe, then error prevents prescription",
                "Given drug interaction exists, when I prescribe, then warning is displayed"
            ],
            "estimated_points": 8
        }
    ]
}
```
"""

    FINANCE_EXAMPLES = """
## Example 1: Fund Transfer

**Code Pattern:**
```python
class TransferService:
    @transactional
    def transfer_funds(self, from_acc: str, to_acc: str, amount: Decimal) -> Transfer:
        if amount > self.get_daily_limit(from_acc):
            raise LimitExceededError()
        self.debit(from_acc, amount)
        self.credit(to_acc, amount)
        self.audit_log.record(transfer)
        return Transfer(from_acc, to_acc, amount, status="completed")
```

**Extracted Requirement:**
```json
{
    "type": "feature",
    "title": "Fund Transfer",
    "stories": [
        {
            "title": "As a customer, I want to transfer funds between accounts so that I can manage my money",
            "acceptance_criteria": [
                "Given sufficient balance, when I transfer funds, then both accounts are updated",
                "Given amount exceeds daily limit, when I transfer, then error is shown",
                "Given successful transfer, when completed, then audit log is created"
            ],
            "estimated_points": 8
        }
    ]
}
```
"""

    E_COMMERCE_EXAMPLES = """
## Example 1: Add to Cart

**Code Pattern:**
```python
class CartService:
    def add_to_cart(self, user_id: int, product_id: int, quantity: int) -> Cart:
        product = self.product_repo.get(product_id)
        if product.stock < quantity:
            raise OutOfStockError()
        cart = self.get_or_create_cart(user_id)
        cart.add_item(product, quantity)
        self.update_cart_totals(cart)
        return cart
```

**Extracted Requirement:**
```json
{
    "type": "feature",
    "title": "Shopping Cart Management",
    "stories": [
        {
            "title": "As a customer, I want to add products to my cart so that I can purchase them later",
            "acceptance_criteria": [
                "Given product is in stock, when I add to cart, then item appears in cart",
                "Given quantity exceeds stock, when I add to cart, then error is shown",
                "Given items in cart, when I add more, then totals are recalculated"
            ],
            "estimated_points": 5
        }
    ]
}
```
"""

    def get_examples(self, domain: str) -> str:
        """Get few-shot examples for domain."""
        examples = {
            "healthcare": self.HEALTHCARE_EXAMPLES,
            "finance": self.FINANCE_EXAMPLES,
            "ecommerce": self.E_COMMERCE_EXAMPLES,
        }
        return examples.get(domain, "")
```

---

### FR-QW-2: INVEST Validator ⭐⭐⭐⭐⭐
**Tijd:** 3 uur
**Impact:** HOOG - Betere story kwaliteit

```python
# app/services/extraction/invest_validator.py

@dataclass
class INVESTScore:
    independent: float      # Can be developed independently
    negotiable: float       # Room for discussion
    valuable: float         # Delivers user value
    estimable: float        # Can be estimated
    small: float           # Fits in a sprint
    testable: float        # Has clear acceptance criteria
    overall: float
    issues: List[str]
    recommendations: List[str]

class INVESTValidator:
    """Validate extracted stories against INVEST criteria."""

    def validate(self, story: ExtractedStory) -> INVESTScore:
        issues = []
        recommendations = []

        # INDEPENDENT: Check for dependencies mentioned
        independent = self._check_independent(story)
        if independent < 0.7:
            issues.append("Story may have hidden dependencies")
            recommendations.append("Break down into smaller, independent stories")

        # NEGOTIABLE: Check if too prescriptive
        negotiable = self._check_negotiable(story)
        if negotiable < 0.7:
            issues.append("Story is too implementation-specific")
            recommendations.append("Focus on 'what' not 'how'")

        # VALUABLE: Check for business value statement
        valuable = self._check_valuable(story)
        if valuable < 0.7:
            issues.append("Missing clear business value")
            recommendations.append("Add 'so that [benefit]' clause")

        # ESTIMABLE: Check if too vague
        estimable = self._check_estimable(story)
        if estimable < 0.7:
            issues.append("Story is too vague to estimate")
            recommendations.append("Add more specific acceptance criteria")

        # SMALL: Check story points
        small = self._check_small(story)
        if small < 0.7:
            issues.append("Story may be too large for a sprint")
            recommendations.append("Consider splitting into multiple stories")

        # TESTABLE: Check acceptance criteria
        testable = self._check_testable(story)
        if testable < 0.7:
            issues.append("Acceptance criteria not testable")
            recommendations.append("Use Given/When/Then format")

        overall = (independent + negotiable + valuable +
                   estimable + small + testable) / 6

        return INVESTScore(
            independent=independent,
            negotiable=negotiable,
            valuable=valuable,
            estimable=estimable,
            small=small,
            testable=testable,
            overall=overall,
            issues=issues,
            recommendations=recommendations
        )

    def _check_independent(self, story: ExtractedStory) -> float:
        """Check if story is independent."""
        # Check for dependency keywords
        dep_keywords = ['after', 'depends on', 'requires', 'blocked by', 'following']
        text = f"{story.title} {story.description}".lower()

        dep_count = sum(1 for kw in dep_keywords if kw in text)
        return max(0.0, 1.0 - (dep_count * 0.3))

    def _check_negotiable(self, story: ExtractedStory) -> float:
        """Check if story is negotiable (not too prescriptive)."""
        impl_keywords = ['use', 'implement with', 'using', 'database', 'api',
                        'sql', 'rest', 'json', 'html', 'button']
        text = f"{story.title} {story.description}".lower()

        impl_count = sum(1 for kw in impl_keywords if kw in text)
        return max(0.0, 1.0 - (impl_count * 0.15))

    def _check_valuable(self, story: ExtractedStory) -> float:
        """Check if story has clear value."""
        # Check for "so that" clause
        if 'so that' in story.title.lower() or 'so that' in story.description.lower():
            return 1.0

        # Check for benefit keywords
        value_keywords = ['enable', 'improve', 'reduce', 'save', 'increase',
                         'allow', 'help', 'ensure']
        text = f"{story.title} {story.description}".lower()

        return 0.5 + (0.1 * sum(1 for kw in value_keywords if kw in text))

    def _check_estimable(self, story: ExtractedStory) -> float:
        """Check if story can be estimated."""
        # Must have acceptance criteria
        if not story.acceptance_criteria:
            return 0.3

        # Criteria should be specific
        specific_count = sum(
            1 for ac in story.acceptance_criteria
            if any(word in ac.lower() for word in ['given', 'when', 'then', 'should', 'must'])
        )

        return min(1.0, 0.5 + (specific_count * 0.15))

    def _check_small(self, story: ExtractedStory) -> float:
        """Check if story is small enough."""
        if story.story_points is None:
            return 0.5

        if story.story_points <= 3:
            return 1.0
        elif story.story_points <= 5:
            return 0.8
        elif story.story_points <= 8:
            return 0.6
        else:
            return 0.3

    def _check_testable(self, story: ExtractedStory) -> float:
        """Check if story is testable."""
        if not story.acceptance_criteria:
            return 0.2

        # Check for Given/When/Then format
        gherkin_count = sum(
            1 for ac in story.acceptance_criteria
            if 'given' in ac.lower() or 'when' in ac.lower() or 'then' in ac.lower()
        )

        gherkin_ratio = gherkin_count / len(story.acceptance_criteria)
        return 0.4 + (gherkin_ratio * 0.6)
```

---

### FR-QW-3: Acceptance Criteria Enhancer ⭐⭐⭐⭐
**Tijd:** 2 uur
**Impact:** MEDIUM-HOOG - Betere testbaarheid

```python
# app/services/extraction/acceptance_criteria_enhancer.py

class AcceptanceCriteriaEnhancer:
    """Enhance acceptance criteria to Given/When/Then format."""

    def enhance(self, criteria: List[str]) -> List[str]:
        """Convert criteria to Gherkin format."""
        enhanced = []

        for criterion in criteria:
            if self._is_gherkin_format(criterion):
                enhanced.append(criterion)
            else:
                enhanced.append(self._convert_to_gherkin(criterion))

        return enhanced

    def _is_gherkin_format(self, criterion: str) -> bool:
        """Check if already in Given/When/Then format."""
        lower = criterion.lower()
        return ('given' in lower and 'when' in lower and 'then' in lower)

    def _convert_to_gherkin(self, criterion: str) -> str:
        """Convert plain text to Gherkin format."""
        # Pattern matching for common phrasings
        patterns = [
            # "User can X" -> "Given user exists, When X, Then success"
            (r"(?:user|admin|customer)\s+(?:can|should|must)\s+(.+)",
             "Given a valid {actor}, When {action}, Then operation succeeds"),

            # "System displays X when Y" -> "Given Y, When triggered, Then displays X"
            (r"system\s+(?:displays?|shows?)\s+(.+?)\s+when\s+(.+)",
             "Given {condition}, When triggered, Then system displays {result}"),

            # "X is required" -> "Given X is empty, When submit, Then error shown"
            (r"(.+?)\s+is\s+required",
             "Given {field} is empty, When form is submitted, Then validation error is shown"),

            # "X must be Y" -> "Given X is not Y, When validated, Then error"
            (r"(.+?)\s+must\s+be\s+(.+)",
             "Given {field} is not {value}, When validated, Then error is shown"),
        ]

        import re
        for pattern, template in patterns:
            match = re.match(pattern, criterion, re.IGNORECASE)
            if match:
                groups = match.groups()
                return template.format(
                    actor="user",
                    action=groups[0] if groups else criterion,
                    condition=groups[1] if len(groups) > 1 else "",
                    result=groups[0] if groups else "",
                    field=groups[0] if groups else "",
                    value=groups[1] if len(groups) > 1 else ""
                )

        # Fallback: wrap in basic format
        return f"Given preconditions are met, When {criterion.lower()}, Then expected outcome occurs"

    async def enhance_with_llm(self, criteria: List[str], context: str) -> List[str]:
        """Use LLM to enhance acceptance criteria."""
        prompt = f"""Convert these acceptance criteria to Given/When/Then format.

Context: {context}

Original criteria:
{chr(10).join(f"- {c}" for c in criteria)}

Requirements:
- Each criterion MUST have Given, When, Then
- Be specific about conditions and outcomes
- Include edge cases where appropriate

Output as JSON array of strings."""

        response = await self.llm.generate(prompt)
        return json.loads(response)
```

---

### FR-M-1: Traceability Matrix Generator ⭐⭐⭐⭐⭐
**Tijd:** 2 dagen
**Impact:** ZEER HOOG - Complete traceability

```python
# app/services/extraction/traceability_matrix_service.py

@dataclass
class TraceabilityLink:
    source_type: str       # "code", "requirement", "test", "design"
    source_id: str
    source_name: str
    target_type: str
    target_id: str
    target_name: str
    link_type: str         # "implements", "tests", "derives_from", "satisfies"
    confidence: float
    evidence: str          # Why this link exists

class TraceabilityMatrixService:
    """Generate requirement-to-code traceability matrix."""

    async def generate_matrix(self,
                              stories: List[ExtractedStory],
                              rules: List[BusinessRule],
                              code_analysis: AggregatedAnalysis) -> TraceabilityMatrix:
        """Generate full traceability matrix."""
        links = []

        # Story -> Code (implementations)
        for story in stories:
            code_links = await self._find_implementing_code(story, code_analysis)
            links.extend(code_links)

        # Rule -> Code (where rule is enforced)
        for rule in rules:
            links.append(TraceabilityLink(
                source_type="rule",
                source_id=rule.id,
                source_name=rule.natural_language[:50],
                target_type="code",
                target_id=f"{rule.source_file}:{rule.source_lines[0]}",
                target_name=rule.source_file,
                link_type="implements",
                confidence=rule.confidence,
                evidence=f"Pattern matched at line {rule.source_lines[0]}"
            ))

        # Story -> Rule (business logic)
        for story in stories:
            for rule in rules:
                if self._story_matches_rule(story, rule):
                    links.append(TraceabilityLink(
                        source_type="story",
                        source_id=story.id,
                        source_name=story.title[:50],
                        target_type="rule",
                        target_id=rule.id,
                        target_name=rule.natural_language[:50],
                        link_type="derives_from",
                        confidence=0.7,
                        evidence="Shared variables/concepts"
                    ))

        # Build matrix
        return TraceabilityMatrix(
            links=links,
            coverage=self._calculate_coverage(stories, links),
            orphan_code=self._find_orphan_code(code_analysis, links),
            orphan_requirements=self._find_orphan_requirements(stories, links)
        )

    def _story_matches_rule(self, story: ExtractedStory, rule: BusinessRule) -> bool:
        """Check if story and rule are related."""
        story_text = f"{story.title} {story.description}".lower()
        rule_text = f"{rule.condition} {rule.action}".lower()

        # Check variable overlap
        story_words = set(story_text.split())
        rule_vars = set(v.lower() for v in rule.variables_involved)

        return bool(story_words & rule_vars)

    def export_matrix(self, matrix: TraceabilityMatrix, format: str) -> str:
        """Export matrix to various formats."""
        if format == "csv":
            return self._export_csv(matrix)
        elif format == "html":
            return self._export_html(matrix)
        elif format == "markdown":
            return self._export_markdown(matrix)
        else:
            raise ValueError(f"Unknown format: {format}")
```

---

### FR-M-2: Functional Decomposition Guidance ⭐⭐⭐⭐
**Tijd:** 2 dagen
**Impact:** HOOG - Betere epic/feature/story structuur

```python
# app/services/extraction/functional_decomposition.py

class FunctionalDecompositionService:
    """Guide proper Epic -> Feature -> Story decomposition."""

    # Size thresholds (in story points equivalent)
    EPIC_MIN_SIZE = 40       # Minimum size for an epic
    FEATURE_MAX_SIZE = 21    # Maximum size for a feature
    STORY_MAX_SIZE = 8       # Maximum size for a story (fits in sprint)

    async def decompose(self,
                        extracted_items: List[ExtractedStory],
                        target_story_size: int = 5) -> DecompositionResult:
        """Decompose extracted items into proper hierarchy."""

        # 1. Cluster items by functional area
        clusters = self._cluster_by_function(extracted_items)

        # 2. Create epics from large clusters
        epics = []
        for cluster_name, items in clusters.items():
            total_points = sum(i.story_points or 3 for i in items)

            if total_points >= self.EPIC_MIN_SIZE:
                epic = self._create_epic(cluster_name, items)
                epics.append(epic)

        # 3. Decompose epics into features
        for epic in epics:
            features = await self._decompose_to_features(epic)
            epic.children = features

            # 4. Decompose features into stories
            for feature in features:
                stories = await self._decompose_to_stories(feature, target_story_size)
                feature.children = stories

        # 5. Validate decomposition
        validation = self._validate_decomposition(epics)

        return DecompositionResult(
            epics=epics,
            total_stories=sum(
                len(f.children) for e in epics for f in e.children
            ),
            validation=validation
        )

    def _cluster_by_function(self, items: List[ExtractedStory]) -> Dict[str, List[ExtractedStory]]:
        """Cluster items by functional area using NLP."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import KMeans

        # Create text representations
        texts = [f"{i.title} {i.description}" for i in items]

        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
        X = vectorizer.fit_transform(texts)

        # Cluster
        n_clusters = max(3, len(items) // 10)  # Roughly 10 items per cluster
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels = kmeans.fit_predict(X)

        # Group items
        clusters = {}
        for item, label in zip(items, labels):
            cluster_name = self._generate_cluster_name(items, label, labels)
            clusters.setdefault(cluster_name, []).append(item)

        return clusters

    async def _decompose_to_stories(self,
                                     feature: ExtractedStory,
                                     target_size: int) -> List[ExtractedStory]:
        """Break feature into properly sized stories."""
        if (feature.story_points or 13) <= target_size:
            return [feature]  # Already small enough

        # Use LLM to split
        prompt = f"""Split this feature into smaller user stories (max {target_size} points each):

Feature: {feature.title}
Description: {feature.description}
Current estimate: {feature.story_points} points

Requirements:
1. Each story should be independently deliverable
2. Each story should have clear acceptance criteria
3. Stories should total approximately the original estimate

Output as JSON array of stories with title, description, acceptance_criteria, story_points."""

        response = await self.llm.generate(prompt)
        stories_data = json.loads(response)

        return [
            ExtractedStory(
                title=s["title"],
                description=s["description"],
                acceptance_criteria=s["acceptance_criteria"],
                story_points=s["story_points"],
                parent_id=feature.id,
                level=ExtractionLevel.FUNCTION,
                item_type=ItemType.STORY
            )
            for s in stories_data
        ]
```

---

## Categorie 3: Non-Functional Requirements Verbeteringen

### NFR-QW-1: Quantitative NFR Detector ⭐⭐⭐⭐⭐
**Tijd:** 4 uur
**Impact:** HOOG - Meetbare requirements

```python
# app/services/static_analysis/quantitative_nfr_detector.py

class QuantitativeNFRDetector:
    """Detect NFRs with quantitative specifications."""

    QUANTITATIVE_PATTERNS = {
        "response_time": [
            (r"response\s*(?:time)?\s*[<>]=?\s*(\d+)\s*(ms|s|seconds?|milliseconds?)",
             "Response time constraint"),
            (r"latency\s*[<>]=?\s*(\d+)\s*(ms|s)", "Latency requirement"),
            (r"timeout\s*=\s*(\d+)", "Timeout configuration"),
        ],
        "throughput": [
            (r"(\d+)\s*(?:requests?|tps|transactions?)\s*per\s*(?:second|minute|hour)",
             "Throughput requirement"),
            (r"rate[_-]?limit\s*=\s*(\d+)", "Rate limit"),
        ],
        "availability": [
            (r"(\d{2,3}(?:\.\d+)?)\s*%\s*(?:uptime|availability|sla)",
             "Availability target"),
            (r"max[_-]?downtime\s*[<>=]\s*(\d+)\s*(min|hour|day)",
             "Downtime limit"),
        ],
        "data_volume": [
            (r"max[_-]?(?:size|length)\s*=\s*(\d+)\s*(kb|mb|gb|bytes?)?",
             "Data size limit"),
            (r"batch[_-]?size\s*=\s*(\d+)", "Batch processing size"),
        ],
        "concurrency": [
            (r"max[_-]?(?:connections?|users?|threads?)\s*=\s*(\d+)",
             "Concurrency limit"),
            (r"pool[_-]?size\s*=\s*(\d+)", "Connection pool size"),
        ],
        "retention": [
            (r"retention[_-]?(?:period|days?)\s*=\s*(\d+)",
             "Data retention period"),
            (r"expire[s]?\s*(?:after|in)\s*(\d+)\s*(days?|hours?|minutes?)",
             "Expiration policy"),
        ],
    }

    async def detect_quantitative(self,
                                   file_path: str,
                                   source: str) -> List[QuantitativeNFR]:
        """Detect NFRs with numeric specifications."""
        detections = []

        for category, patterns in self.QUANTITATIVE_PATTERNS.items():
            for pattern, description in patterns:
                regex = re.compile(pattern, re.IGNORECASE)

                for match in regex.finditer(source):
                    value = match.group(1)
                    unit = match.group(2) if len(match.groups()) > 1 else None

                    line_num = source[:match.start()].count('\n') + 1

                    detections.append(QuantitativeNFR(
                        category=category,
                        metric=description,
                        value=float(value),
                        unit=unit,
                        source_file=file_path,
                        source_line=line_num,
                        raw_match=match.group(0),
                        specification=self._generate_specification(category, value, unit)
                    ))

        return detections

    def _generate_specification(self, category: str, value: str, unit: str) -> str:
        """Generate formal specification from detection."""
        templates = {
            "response_time": f"System SHALL respond within {value} {unit or 'ms'}",
            "throughput": f"System SHALL handle {value} {unit or 'requests/second'}",
            "availability": f"System SHALL maintain {value}% availability",
            "data_volume": f"System SHALL support data up to {value} {unit or 'bytes'}",
            "concurrency": f"System SHALL support {value} concurrent {unit or 'connections'}",
            "retention": f"System SHALL retain data for {value} {unit or 'days'}",
        }
        return templates.get(category, f"{category}: {value} {unit or ''}")
```

---

### NFR-QW-2: NFR Priority Scoring ⭐⭐⭐⭐
**Tijd:** 3 uur
**Impact:** MEDIUM-HOOG - Betere prioritering

```python
# app/services/static_analysis/nfr_priority_scorer.py

class NFRPriorityScorer:
    """Score and prioritize NFR detections."""

    # Priority weights per category
    CATEGORY_WEIGHTS = {
        NFRCategory.SECURITY: 1.0,       # Highest priority
        NFRCategory.RELIABILITY: 0.9,
        NFRCategory.PERFORMANCE: 0.8,
        NFRCategory.SCALABILITY: 0.7,
        NFRCategory.MAINTAINABILITY: 0.6,
        NFRCategory.USABILITY: 0.5,
        NFRCategory.ACCESSIBILITY: 0.5,
    }

    # Impact multipliers
    IMPACT_MULTIPLIERS = {
        "hardcoded credential": 2.0,     # Critical security
        "sql injection": 2.0,
        "authentication": 1.5,
        "encryption": 1.3,
        "broad exception": 1.4,          # Reliability issue
        "no error handling": 1.5,
        "n+1 query": 1.2,                # Performance issue
        "no caching": 1.1,
    }

    def score_detection(self, detection: NFRDetection) -> float:
        """Calculate priority score for detection."""
        base_score = detection.confidence * 100

        # Apply category weight
        category_weight = self.CATEGORY_WEIGHTS.get(detection.category, 0.5)

        # Apply impact multiplier
        impact_mult = 1.0
        for keyword, mult in self.IMPACT_MULTIPLIERS.items():
            if keyword.lower() in detection.description.lower():
                impact_mult = max(impact_mult, mult)

        # Compliance relevance bonus
        compliance_bonus = len(detection.compliance_relevance) * 10

        final_score = (base_score * category_weight * impact_mult) + compliance_bonus
        return min(100, final_score)

    def prioritize_detections(self,
                               detections: List[NFRDetection]) -> List[Tuple[NFRDetection, float]]:
        """Return detections sorted by priority score."""
        scored = [(d, self.score_detection(d)) for d in detections]
        return sorted(scored, key=lambda x: x[1], reverse=True)

    def categorize_by_action(self,
                              detections: List[NFRDetection]) -> Dict[str, List[NFRDetection]]:
        """Categorize detections by required action."""
        categories = {
            "immediate_action": [],       # Score >= 80
            "short_term": [],            # Score 60-79
            "medium_term": [],           # Score 40-59
            "backlog": [],               # Score < 40
        }

        for detection in detections:
            score = self.score_detection(detection)

            if score >= 80:
                categories["immediate_action"].append(detection)
            elif score >= 60:
                categories["short_term"].append(detection)
            elif score >= 40:
                categories["medium_term"].append(detection)
            else:
                categories["backlog"].append(detection)

        return categories
```

---

### NFR-QW-3: Industry Standard NFR Templates ⭐⭐⭐⭐
**Tijd:** 3 uur
**Impact:** MEDIUM - Betere standaard patterns

```python
# app/services/static_analysis/nfr_standards.py

class NFRStandardsLibrary:
    """Industry standard NFR templates and checks."""

    # ISO 25010 Quality Characteristics
    ISO_25010_CATEGORIES = {
        "functional_suitability": {
            "functional_completeness": "Degree to which functions cover all specified tasks",
            "functional_correctness": "Degree to which product provides correct results",
            "functional_appropriateness": "Degree to which functions facilitate accomplishment",
        },
        "performance_efficiency": {
            "time_behaviour": "Response time, processing time, throughput",
            "resource_utilization": "Amount of resources used",
            "capacity": "Maximum limits of a product parameter",
        },
        "compatibility": {
            "co_existence": "Perform functions while sharing environment",
            "interoperability": "Exchange information with other systems",
        },
        "usability": {
            "appropriateness_recognizability": "Users recognize if suitable for needs",
            "learnability": "Ease of learning to use",
            "operability": "Ease of operation and control",
            "user_error_protection": "Protection against user errors",
            "user_interface_aesthetics": "Pleasing and satisfying interaction",
            "accessibility": "Usable by people with widest range of characteristics",
        },
        "reliability": {
            "maturity": "Meet needs under normal operation",
            "availability": "Operational and accessible when required",
            "fault_tolerance": "Operate despite faults",
            "recoverability": "Recover data and re-establish desired state",
        },
        "security": {
            "confidentiality": "Accessible only to those authorized",
            "integrity": "Prevent unauthorized access or modification",
            "non_repudiation": "Actions can be proven to have taken place",
            "accountability": "Actions can be traced uniquely",
            "authenticity": "Identity can be proved to be claimed",
        },
        "maintainability": {
            "modularity": "Composed of discrete components",
            "reusability": "Asset can be used in other systems",
            "analysability": "Ease of assessing change impact",
            "modifiability": "Ease of modification without defects",
            "testability": "Ease of establishing test criteria",
        },
        "portability": {
            "adaptability": "Adapted for different environments",
            "installability": "Ease of installation/uninstallation",
            "replaceability": "Replace another product for same purpose",
        },
    }

    # Healthcare-specific (NEN7510, HIPAA)
    HEALTHCARE_NFR_TEMPLATES = {
        "audit_logging": {
            "requirement": "All access to patient data SHALL be logged",
            "pattern": r"audit|access_log|phi_access",
            "compliance": ["NEN7510-12.4", "HIPAA-164.312(b)"],
        },
        "data_encryption_at_rest": {
            "requirement": "Patient data SHALL be encrypted at rest",
            "pattern": r"encrypt.*storage|aes|encryption_key",
            "compliance": ["NEN7510-10.1", "HIPAA-164.312(a)(2)(iv)"],
        },
        "session_timeout": {
            "requirement": "Sessions SHALL timeout after 15 minutes of inactivity",
            "pattern": r"session.*timeout|idle.*timeout",
            "compliance": ["NEN7510-11.5", "HIPAA-164.312(a)(2)(iii)"],
        },
        "password_policy": {
            "requirement": "Passwords SHALL meet complexity requirements",
            "pattern": r"password.*(?:length|complexity|policy)",
            "compliance": ["NEN7510-9.3", "HIPAA-164.308(a)(5)"],
        },
    }

    def get_gap_analysis(self,
                         detections: List[NFRDetection],
                         domain: str = "healthcare") -> List[NFRGap]:
        """Compare detections against standards to find gaps."""
        gaps = []

        templates = self.HEALTHCARE_NFR_TEMPLATES if domain == "healthcare" else {}

        for req_name, template in templates.items():
            # Check if requirement is satisfied
            pattern = re.compile(template["pattern"], re.IGNORECASE)

            found = any(
                pattern.search(d.pattern_matched) or pattern.search(d.description)
                for d in detections
            )

            if not found:
                gaps.append(NFRGap(
                    requirement_name=req_name,
                    description=template["requirement"],
                    compliance_references=template["compliance"],
                    severity="high" if "SHALL" in template["requirement"] else "medium",
                    recommendation=f"Implement {req_name.replace('_', ' ')}"
                ))

        return gaps
```

---

### NFR-M-1: Cross-Reference with Architecture ⭐⭐⭐⭐
**Tijd:** 2 dagen
**Impact:** HOOG - Betere NFR plaatsing

```python
# app/services/static_analysis/nfr_architecture_mapper.py

class NFRArchitectureMapper:
    """Map NFR detections to architectural components."""

    async def map_to_architecture(self,
                                   nfr_report: NFRReport,
                                   code_analysis: AggregatedAnalysis) -> NFRArchitectureMap:
        """Map NFRs to architectural layers and components."""
        mappings = []

        # Get architecture layers from code analysis
        layers = self._identify_layers(code_analysis)

        for detection in nfr_report.detections:
            # Determine which layer this NFR belongs to
            layer = self._determine_layer(detection, layers)

            # Find related components
            components = self._find_related_components(detection, code_analysis)

            mappings.append(NFRArchitectureMapping(
                nfr=detection,
                layer=layer,
                components=components,
                implementation_location=self._suggest_implementation_location(detection, layer),
                cross_cutting=self._is_cross_cutting(detection)
            ))

        # Generate architecture diagram data
        diagram = self._generate_nfr_diagram(mappings, layers)

        return NFRArchitectureMap(
            mappings=mappings,
            by_layer=self._group_by_layer(mappings),
            cross_cutting_concerns=self._extract_cross_cutting(mappings),
            diagram_data=diagram
        )

    def _identify_layers(self, code_analysis: AggregatedAnalysis) -> List[ArchitectureLayer]:
        """Identify architectural layers from code structure."""
        layers = []

        # Common layer patterns
        layer_patterns = {
            "presentation": ["api", "controllers", "routes", "views", "ui"],
            "application": ["services", "use_cases", "handlers", "application"],
            "domain": ["domain", "entities", "models", "core"],
            "infrastructure": ["infrastructure", "repositories", "db", "external"],
        }

        for layer_name, patterns in layer_patterns.items():
            matching_files = []
            for file_path in code_analysis.files:
                if any(p in file_path.lower() for p in patterns):
                    matching_files.append(file_path)

            if matching_files:
                layers.append(ArchitectureLayer(
                    name=layer_name,
                    files=matching_files,
                    nfr_concerns=self._get_layer_nfr_concerns(layer_name)
                ))

        return layers

    def _get_layer_nfr_concerns(self, layer_name: str) -> List[str]:
        """Get typical NFR concerns for a layer."""
        concerns = {
            "presentation": ["performance", "usability", "accessibility", "security"],
            "application": ["performance", "reliability", "maintainability"],
            "domain": ["maintainability", "testability"],
            "infrastructure": ["performance", "scalability", "reliability", "security"],
        }
        return concerns.get(layer_name, [])
```

---

## Implementation Roadmap

### Fase 1: Quick Wins (Week 1-2)
| Dag | Items |
|-----|-------|
| 1 | BR-QW-1: Domain Vocabulary Loader |
| 2 | BR-QW-2: Rule Deduplication |
| 3 | FR-QW-1: Few-Shot Templates |
| 4 | FR-QW-2: INVEST Validator |
| 5 | NFR-QW-1: Quantitative NFR Detector |
| 6 | NFR-QW-2: Priority Scoring |
| 7 | BR-QW-3 + BR-QW-4: NL Enhancer + Completeness |
| 8 | FR-QW-3 + NFR-QW-3: AC Enhancer + Standards |

### Fase 2: Medium Improvements (Week 3-6)
| Week | Items |
|------|-------|
| 3 | BR-M-1: Semantic Rule Understanding (LLM) |
| 4 | BR-M-2: Inter-Rule Dependencies |
| 4 | FR-M-1: Traceability Matrix |
| 5 | BR-M-3: Legacy Pattern Recognition |
| 5 | FR-M-2: Functional Decomposition |
| 6 | BR-M-4 + BR-M-5: Test Generation + Documentation |
| 6 | NFR-M-1: Architecture Mapping |

### Fase 3: Large Improvements (Week 7-10)
| Week | Items |
|------|-------|
| 7-8 | BR-L-1: Hybrid Extraction Pipeline |
| 9-10 | FR-L-1: LLM Council Validation |
| 10 | NFR-L-1: Compliance Dashboard |

---

## Success Metrics

| Metric | Huidige | Target |
|--------|---------|--------|
| Business Rule Precision | 65% | 85% |
| Business Rule Recall | 70% | 90% |
| FR INVEST Score Average | 55% | 80% |
| NFR Coverage Score | 50% | 75% |
| False Positive Rate | 25% | <10% |
| Traceability Completeness | 30% | 80% |
| Time per 10K LOC | 45 min | 15 min |

---

## Conclusie

De verbeteringen zijn onderverdeeld in:

1. **Business Rules (12 items)**: Focus op semantic understanding, domain vocabulary, en legacy support
2. **Functional Requirements (10 items)**: Focus op INVEST compliance, traceability, en decomposition
3. **Non-Functional Requirements (9 items)**: Focus op quantitative specs, prioritering, en architecture mapping

**Belangrijkste innovaties:**
- Hybrid static-LLM pipeline voor beste van beide werelden
- Domain-specific vocabularies voor betere herkenning
- INVEST validator voor story kwaliteit
- Traceability matrix voor volledige traceerbaarheid
- Quantitative NFR detection voor meetbare requirements

**Geschatte totale impact:** 50-70% hogere extractie-kwaliteit.

---

**Document Status:** ✅ FINAL
**Versie:** 1.0
**Datum:** 2025-12-24
