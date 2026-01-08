# Fase 15: Hybrid Static-LLM Extraction Pipeline

**Version**: 1.0
**Status**: Planned
**Timeline**: Week 97-102 (25 days)
**Owner**: MarQed.ai Development Team

---

## Executive Summary

Dit document beschrijft de implementatie van een hybride static analysis + LLM extraction pipeline voor business requirement extractie. De pipeline voegt een nieuw **Cycle 0 (Static Analysis)** toe als fundament voor de bestaande 5-cycle LLM pipeline, waardoor we deterministisch 80% van code-elementen kunnen identificeren voordat LLM enrichment plaatsvindt.

### Key Benefits

| Benefit | Impact |
|---------|--------|
| **Deterministische baseline** | 80% code coverage zonder LLM kosten |
| **Verbeterde nauwkeurigheid** | LLM valideert/verrijkt ipv volledig genereert |
| **Conflict detectie** | 72.5% confidence threshold voor human review |
| **NFR detectie** | Security, Performance, Reliability, Maintainability |
| **Compliance frameworks** | Pluggable per project (NEN7510, ISO27001, HIPAA, SOC2) |

---

## 1. Architecture Overview

### 1.1 Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HYBRID STATIC-LLM EXTRACTION PIPELINE                     │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  CYCLE 0: STATIC ANALYSIS (NEW - Foundation for ALL tiers)          │   │
│  │  ┌─────────────┬─────────────┬─────────────┬─────────────┬────────┐ │   │
│  │  │ Program     │ Variable    │ Business    │ NFR         │Compli- │ │   │
│  │  │ Slicer      │ Classifier  │ Rule Extractor│ Detector  │ance    │ │   │
│  │  └─────────────┴─────────────┴─────────────┴─────────────┴────────┘ │   │
│  │                              │                                       │   │
│  │                              ▼                                       │   │
│  │                 StaticAnalysisResult (~80% coverage)                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  CYCLE 1-5: LLM ENRICHMENT (Existing - Enhanced)                    │   │
│  │  ┌─────────┬─────────┬─────────┬─────────┬─────────┐                │   │
│  │  │ Cycle 1 │ Cycle 2 │ Cycle 3 │ Cycle 4 │ Cycle 5 │                │   │
│  │  │ Initial │ Cross   │ Gap     │ INVEST  │ Final   │                │   │
│  │  │ Enrich  │ Valid   │ Fill    │ Valid   │ Synth   │                │   │
│  │  └─────────┴─────────┴─────────┴─────────┴─────────┘                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  CONFLICT DETECTION                                                  │   │
│  │  IF LLM.confidence < 72.5% AND LLM overrules static → Human Review   │   │
│  │  + Explicit disagreement between LLMs                                │   │
│  │  + Classification change (Epic→Feature, Feature→Story)              │   │
│  │  + Item removal (static found, LLM removes)                          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│                                  ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  OUTPUT: Full Details (always stored for migrations, bugs, features) │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Updated Tier Structure

| Tier | Static Analysis | LLM Providers | Human Review | Price (50K LOC) |
|------|-----------------|---------------|--------------|-----------------|
| ~~FREE~~ | ~~N/A~~ | ~~3 Ollama~~ | ~~No~~ | ~~$0~~ |
| **BASIC** | Full Cycle 0 | 3 (Ollama only) | No | €5 |
| **STANDARD** | Full Cycle 0 | 5 (+Groq, Qwen) | Optional | €25 |
| **PROFESSIONAL** | Full Cycle 0 | 7 (+Gemini, GPT) | Included | €75 |
| **PREMIUM** | Full Cycle 0 | 10 (+Opus, Moonshot) | Included | €150 |

**Note**: FREE tier removed - Static analysis provides foundation for all paid tiers.

---

## 2. Component Specifications

### 2.1 ProgramSlicer

Backward/forward slicing voor dependency analysis gebaseerd op IEEE 852482 (Huang et al. 1996).

```python
# backend/app/services/program_slicer.py

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
import ast
import re

class SliceDirection(Enum):
    BACKWARD = "backward"  # Data dependencies leading TO variable
    FORWARD = "forward"    # Data dependencies FROM variable
    BOTH = "both"

class LanguageSupport(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    CSHARP = "csharp"
    VBNET = "vbnet"
    ASP_CLASSIC = "asp_classic"
    SQL = "sql"

@dataclass
class SliceCriterion:
    """IEEE 852482: Slice criterion = (statement, variable)"""
    file_path: str
    line_number: int
    variable_name: str
    direction: SliceDirection = SliceDirection.BACKWARD

@dataclass
class ProgramSlice:
    """Result of slicing operation"""
    criterion: SliceCriterion
    statements: List[int]  # Line numbers in slice
    variables: Set[str]    # Variables in slice
    functions_involved: Set[str]
    files_involved: Set[str]
    slice_size: int
    complexity_score: float  # 0.0 - 1.0

@dataclass
class DependencyGraph:
    """Control and data flow graph"""
    nodes: Dict[str, 'DependencyNode']
    edges: List['DependencyEdge']
    entry_points: List[str]
    exit_points: List[str]

@dataclass
class DependencyNode:
    id: str
    file_path: str
    line_start: int
    line_end: int
    node_type: str  # function, class, module, statement
    name: str
    variables_defined: Set[str] = field(default_factory=set)
    variables_used: Set[str] = field(default_factory=set)

@dataclass
class DependencyEdge:
    source_id: str
    target_id: str
    edge_type: str  # data_flow, control_flow, call

class ProgramSlicer:
    """
    Multi-language program slicer for dependency analysis.

    Implements:
    - Backward slicing: Find all code affecting a variable
    - Forward slicing: Find all code affected by a variable
    - Inter-procedural analysis: Cross-function dependencies
    """

    LANGUAGE_PARSERS = {
        LanguageSupport.PYTHON: "_parse_python",
        LanguageSupport.JAVASCRIPT: "_parse_javascript",
        LanguageSupport.CSHARP: "_parse_csharp",
        LanguageSupport.SQL: "_parse_sql",
    }

    def __init__(self, language: LanguageSupport):
        self.language = language
        self.dependency_graph: Optional[DependencyGraph] = None

    async def build_dependency_graph(self, source_files: List[str]) -> DependencyGraph:
        """Build control and data flow graph from source files."""
        parser_method = self.LANGUAGE_PARSERS.get(self.language)
        if not parser_method:
            raise ValueError(f"Unsupported language: {self.language}")

        nodes = {}
        edges = []

        for file_path in source_files:
            file_nodes, file_edges = await getattr(self, parser_method)(file_path)
            nodes.update(file_nodes)
            edges.extend(file_edges)

        self.dependency_graph = DependencyGraph(
            nodes=nodes,
            edges=edges,
            entry_points=self._find_entry_points(nodes),
            exit_points=self._find_exit_points(nodes)
        )
        return self.dependency_graph

    async def compute_slice(self, criterion: SliceCriterion) -> ProgramSlice:
        """Compute program slice for given criterion."""
        if not self.dependency_graph:
            raise ValueError("Dependency graph not built. Call build_dependency_graph first.")

        if criterion.direction == SliceDirection.BACKWARD:
            return await self._backward_slice(criterion)
        elif criterion.direction == SliceDirection.FORWARD:
            return await self._forward_slice(criterion)
        else:
            backward = await self._backward_slice(criterion)
            forward = await self._forward_slice(criterion)
            return self._merge_slices(backward, forward)

    async def _backward_slice(self, criterion: SliceCriterion) -> ProgramSlice:
        """Find all statements that affect the criterion variable."""
        affected_statements = set()
        affected_variables = {criterion.variable_name}
        functions_involved = set()
        files_involved = {criterion.file_path}

        worklist = [(criterion.file_path, criterion.line_number, criterion.variable_name)]
        visited = set()

        while worklist:
            file_path, line, var = worklist.pop()
            if (file_path, line, var) in visited:
                continue
            visited.add((file_path, line, var))

            # Find node containing this line
            node = self._find_node_at_line(file_path, line)
            if not node:
                continue

            affected_statements.add(line)
            functions_involved.add(node.name)

            # Find definitions of var that reach this point
            for edge in self.dependency_graph.edges:
                if edge.target_id == node.id and edge.edge_type == "data_flow":
                    source_node = self.dependency_graph.nodes.get(edge.source_id)
                    if source_node and var in source_node.variables_defined:
                        # Add source to worklist with its used variables
                        for used_var in source_node.variables_used:
                            worklist.append((source_node.file_path, source_node.line_start, used_var))
                        files_involved.add(source_node.file_path)
                        affected_variables.update(source_node.variables_used)

        return ProgramSlice(
            criterion=criterion,
            statements=sorted(affected_statements),
            variables=affected_variables,
            functions_involved=functions_involved,
            files_involved=files_involved,
            slice_size=len(affected_statements),
            complexity_score=self._calculate_complexity(affected_statements, functions_involved)
        )

    async def _forward_slice(self, criterion: SliceCriterion) -> ProgramSlice:
        """Find all statements affected by the criterion variable."""
        # Similar implementation, following forward edges
        # ... implementation details ...
        pass

    def _find_node_at_line(self, file_path: str, line: int) -> Optional[DependencyNode]:
        """Find the node containing the given line."""
        for node in self.dependency_graph.nodes.values():
            if node.file_path == file_path and node.line_start <= line <= node.line_end:
                return node
        return None

    def _calculate_complexity(self, statements: Set[int], functions: Set[str]) -> float:
        """Calculate slice complexity score (0.0 - 1.0)."""
        # Higher complexity = more statements, more functions
        stmt_factor = min(len(statements) / 100, 1.0)
        func_factor = min(len(functions) / 10, 1.0)
        return (stmt_factor + func_factor) / 2

    async def _parse_python(self, file_path: str) -> tuple:
        """Parse Python source file into dependency graph nodes/edges."""
        with open(file_path, 'r') as f:
            source = f.read()

        tree = ast.parse(source)
        nodes = {}
        edges = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                node_id = f"{file_path}:{node.name}"
                dep_node = DependencyNode(
                    id=node_id,
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    node_type="function",
                    name=node.name,
                    variables_defined=self._extract_assignments(node),
                    variables_used=self._extract_references(node)
                )
                nodes[node_id] = dep_node

        return nodes, edges

    def _extract_assignments(self, node: ast.AST) -> Set[str]:
        """Extract all variable assignments in an AST node."""
        assignments = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        assignments.add(target.id)
            elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                assignments.add(child.target.id)
        return assignments

    def _extract_references(self, node: ast.AST) -> Set[str]:
        """Extract all variable references in an AST node."""
        references = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                references.add(child.id)
        return references

    def _find_entry_points(self, nodes: Dict[str, DependencyNode]) -> List[str]:
        """Find entry point nodes (e.g., main functions, API endpoints)."""
        entry_patterns = ['main', '__main__', 'app', 'handler', 'endpoint']
        return [nid for nid, node in nodes.items()
                if any(p in node.name.lower() for p in entry_patterns)]

    def _find_exit_points(self, nodes: Dict[str, DependencyNode]) -> List[str]:
        """Find exit point nodes (e.g., return statements, outputs)."""
        return [nid for nid, node in nodes.items()
                if 'return' in node.name.lower() or 'output' in node.name.lower()]
```

### 2.2 VariableClassifier

Classificeert variabelen als DOMAIN, IMPLEMENTATION, of CONTROL.

```python
# backend/app/services/variable_classifier.py

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Set, Optional
import re

class VariableType(Enum):
    DOMAIN = "domain"           # Business concepts (customer, order, invoice)
    IMPLEMENTATION = "implementation"  # Technical (cache, buffer, connection)
    CONTROL = "control"         # Flow control (i, j, index, flag, temp)

@dataclass
class ClassifiedVariable:
    name: str
    variable_type: VariableType
    confidence: float  # 0.0 - 1.0
    context: str       # Where variable was found
    reasoning: str     # Why this classification

@dataclass
class VariableClassificationResult:
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
        r'(?i)(employee|staff|manager|department|organization)',
        r'(?i)(transaction|balance|amount|price|cost|total|discount)',
        r'(?i)(date|time|period|deadline|schedule)',
        r'(?i)(status|state|phase|stage|level)',
        r'(?i)(address|email|phone|contact)',
        r'(?i)(name|title|description|comment|note)',
        # Domain verbs as nouns
        r'(?i)(approval|validation|verification|authorization)',
        r'(?i)(request|response|notification|alert)',
    ]

    IMPLEMENTATION_PATTERNS = [
        # Technical concepts
        r'(?i)(cache|buffer|pool|queue|stack)',
        r'(?i)(connection|session|socket|stream)',
        r'(?i)(config|setting|option|param)',
        r'(?i)(logger|log|trace|debug)',
        r'(?i)(handler|listener|callback|hook)',
        r'(?i)(factory|builder|provider|service)',
        r'(?i)(mapper|converter|transformer|adapter)',
        r'(?i)(repository|store|dao|dal)',
        # Database/ORM
        r'(?i)(cursor|result_set|row|column)',
        r'(?i)(query|sql|command|statement)',
    ]

    CONTROL_PATTERNS = [
        # Loop/iteration
        r'^[ijk]$',
        r'(?i)^(index|idx|pos|offset|count|counter)$',
        r'(?i)^(iter|iterator|enum|enumerator)$',
        # Temporary
        r'(?i)^(temp|tmp|t|_)$',
        r'(?i)^(result|ret|rv|res)$',
        r'(?i)^(val|value|v)$',
        # Flags
        r'(?i)^(flag|is_|has_|should_|can_|will_)',
        r'(?i)^(found|done|finished|completed|success|error)$',
        # Collections
        r'(?i)^(list|array|dict|map|set|items|elements)$',
    ]

    def __init__(self, custom_domain_terms: Optional[List[str]] = None):
        self.custom_domain_terms = custom_domain_terms or []
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for performance."""
        self.domain_regex = [re.compile(p) for p in self.DOMAIN_PATTERNS]
        self.impl_regex = [re.compile(p) for p in self.IMPLEMENTATION_PATTERNS]
        self.control_regex = [re.compile(p) for p in self.CONTROL_PATTERNS]

        # Add custom domain terms
        if self.custom_domain_terms:
            pattern = r'(?i)(' + '|'.join(self.custom_domain_terms) + ')'
            self.domain_regex.append(re.compile(pattern))

    def classify_variable(self,
                          name: str,
                          context: Optional[str] = None) -> ClassifiedVariable:
        """Classify a single variable."""

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

        # CamelCase with business-like words suggests domain
        if any(word in name.lower() for word in ['get', 'set', 'create', 'update', 'delete']):
            return ClassifiedVariable(
                name=name,
                variable_type=VariableType.IMPLEMENTATION,
                confidence=0.6,
                context=context or "",
                reasoning="CRUD operation suggests implementation"
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
        """Classify all variables in a codebase."""
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
```

### 2.3 BusinessRuleExtractor

Extraheert IF-THEN business rules uit alle code (niet alleen stored procedures).

```python
# backend/app/services/business_rule_extractor.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import ast
import re

class RuleType(Enum):
    VALIDATION = "validation"       # Input validation rules
    CALCULATION = "calculation"     # Business calculations
    AUTHORIZATION = "authorization" # Access control rules
    WORKFLOW = "workflow"           # State transitions
    CONSTRAINT = "constraint"       # Business constraints
    DERIVATION = "derivation"       # Derived values

@dataclass
class BusinessRule:
    id: str
    rule_type: RuleType
    condition: str          # IF part
    action: str            # THEN part
    source_file: str
    source_lines: Tuple[int, int]
    variables_involved: List[str]
    confidence: float
    natural_language: str   # Human-readable description
    compliance_tags: List[str] = field(default_factory=list)  # NEN7510, ISO27001, etc.

@dataclass
class RuleExtractionResult:
    rules: List[BusinessRule]
    rules_by_type: Dict[RuleType, List[BusinessRule]]
    rules_by_file: Dict[str, List[BusinessRule]]
    total_rules: int
    high_confidence_rules: int  # confidence >= 0.8

class BusinessRuleExtractor:
    """
    Extracts business rules from source code.

    Detects patterns:
    - IF-THEN conditionals
    - Validation logic
    - Authorization checks
    - Business calculations
    - State machine transitions
    """

    # Pattern templates for rule detection
    VALIDATION_PATTERNS = [
        r'if\s+(?:not\s+)?(?:\w+\.)?is_valid',
        r'if\s+len\((\w+)\)\s*[<>=]+\s*\d+',
        r'if\s+(\w+)\s+is\s+None',
        r'if\s+not\s+(\w+)',
        r'validate[_a-z]*\(',
        r'check[_a-z]*\(',
    ]

    AUTHORIZATION_PATTERNS = [
        r'if\s+(?:\w+\.)?(?:is_admin|is_authenticated|has_permission|can_)',
        r'if\s+(?:\w+\.)?role\s*[=!]=',
        r'if\s+(?:\w+\.)?user\.(?:is_|has_|can_)',
        r'@(?:login_required|permission_required|roles_required)',
        r'require[_a-z]*(?:auth|permission|role)',
    ]

    CALCULATION_PATTERNS = [
        r'(\w+)\s*=\s*(\w+)\s*[+\-*/]\s*(\w+)',
        r'total\s*[+]=',
        r'sum\s*\(',
        r'calculate[_a-z]*\(',
        r'compute[_a-z]*\(',
    ]

    WORKFLOW_PATTERNS = [
        r'status\s*=\s*["\'](\w+)["\']',
        r'state\s*=\s*["\'](\w+)["\']',
        r'transition[_a-z]*\(',
        r'if\s+status\s*==\s*["\'](\w+)["\']',
        r'\.change_state\(',
    ]

    def __init__(self, variable_classifier: Optional['VariableClassifier'] = None):
        self.variable_classifier = variable_classifier
        self._rule_counter = 0

    async def extract_from_file(self, file_path: str, source: str) -> List[BusinessRule]:
        """Extract business rules from a single source file."""
        rules = []

        # Detect file type and parse accordingly
        if file_path.endswith('.py'):
            rules.extend(await self._extract_from_python(file_path, source))
        elif file_path.endswith(('.js', '.ts')):
            rules.extend(await self._extract_from_javascript(file_path, source))
        elif file_path.endswith(('.cs', '.vb')):
            rules.extend(await self._extract_from_dotnet(file_path, source))
        elif file_path.endswith('.sql'):
            rules.extend(await self._extract_from_sql(file_path, source))

        return rules

    async def _extract_from_python(self, file_path: str, source: str) -> List[BusinessRule]:
        """Extract rules from Python source."""
        rules = []

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return rules

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                rule = self._analyze_if_statement(node, file_path, source)
                if rule:
                    rules.append(rule)
            elif isinstance(node, ast.FunctionDef):
                # Check for validation/authorization decorators
                for decorator in node.decorator_list:
                    rule = self._analyze_decorator(decorator, node, file_path)
                    if rule:
                        rules.append(rule)

        return rules

    def _analyze_if_statement(self,
                               node: ast.If,
                               file_path: str,
                               source: str) -> Optional[BusinessRule]:
        """Analyze an IF statement for business rule patterns."""

        # Get the condition as string
        try:
            condition_source = ast.unparse(node.test)
        except:
            return None

        # Determine rule type
        rule_type = self._classify_rule_type(condition_source)
        if not rule_type:
            return None

        # Get the action (THEN part)
        action_lines = []
        for stmt in node.body:
            try:
                action_lines.append(ast.unparse(stmt))
            except:
                pass
        action = "; ".join(action_lines[:3])  # First 3 statements

        # Extract variables
        variables = self._extract_variables_from_ast(node)

        # Filter to domain variables if classifier available
        if self.variable_classifier:
            classification = self.variable_classifier.classify_all(variables)
            domain_vars = classification.domain_variables
            confidence = 0.7 + (len(domain_vars) / len(variables) * 0.2) if variables else 0.7
        else:
            domain_vars = variables
            confidence = 0.6

        # Skip if no domain variables
        if not domain_vars:
            return None

        self._rule_counter += 1

        return BusinessRule(
            id=f"BR-{self._rule_counter:04d}",
            rule_type=rule_type,
            condition=condition_source,
            action=action,
            source_file=file_path,
            source_lines=(node.lineno, node.end_lineno or node.lineno),
            variables_involved=domain_vars,
            confidence=confidence,
            natural_language=self._generate_natural_language(rule_type, condition_source, action)
        )

    def _classify_rule_type(self, condition: str) -> Optional[RuleType]:
        """Classify the type of business rule based on condition patterns."""

        for pattern in self.AUTHORIZATION_PATTERNS:
            if re.search(pattern, condition, re.IGNORECASE):
                return RuleType.AUTHORIZATION

        for pattern in self.VALIDATION_PATTERNS:
            if re.search(pattern, condition, re.IGNORECASE):
                return RuleType.VALIDATION

        for pattern in self.WORKFLOW_PATTERNS:
            if re.search(pattern, condition, re.IGNORECASE):
                return RuleType.WORKFLOW

        for pattern in self.CALCULATION_PATTERNS:
            if re.search(pattern, condition, re.IGNORECASE):
                return RuleType.CALCULATION

        # Check for constraint patterns
        if re.search(r'if.*[<>=!]+.*:', condition):
            return RuleType.CONSTRAINT

        return None

    def _extract_variables_from_ast(self, node: ast.AST) -> List[str]:
        """Extract all variable names from an AST node."""
        variables = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                variables.add(child.id)
            elif isinstance(child, ast.Attribute):
                variables.add(child.attr)
        return list(variables)

    def _generate_natural_language(self,
                                   rule_type: RuleType,
                                   condition: str,
                                   action: str) -> str:
        """Generate human-readable description of the rule."""
        templates = {
            RuleType.VALIDATION: "WHEN {condition}, THEN validate that {action}",
            RuleType.AUTHORIZATION: "WHEN {condition}, THEN authorize {action}",
            RuleType.CALCULATION: "WHEN {condition}, THEN calculate {action}",
            RuleType.WORKFLOW: "WHEN {condition}, THEN transition to {action}",
            RuleType.CONSTRAINT: "WHEN {condition}, THEN enforce {action}",
            RuleType.DERIVATION: "WHEN {condition}, THEN derive {action}",
        }

        template = templates.get(rule_type, "IF {condition} THEN {action}")
        return template.format(
            condition=condition[:100],
            action=action[:100]
        )

    def _analyze_decorator(self,
                           decorator: ast.expr,
                           func: ast.FunctionDef,
                           file_path: str) -> Optional[BusinessRule]:
        """Analyze decorator for authorization rules."""
        try:
            decorator_name = ast.unparse(decorator)
        except:
            return None

        for pattern in self.AUTHORIZATION_PATTERNS:
            if re.search(pattern, decorator_name, re.IGNORECASE):
                self._rule_counter += 1
                return BusinessRule(
                    id=f"BR-{self._rule_counter:04d}",
                    rule_type=RuleType.AUTHORIZATION,
                    condition=decorator_name,
                    action=f"Allow access to {func.name}",
                    source_file=file_path,
                    source_lines=(func.lineno, func.lineno),
                    variables_involved=[func.name],
                    confidence=0.9,
                    natural_language=f"Require {decorator_name} to access {func.name}"
                )
        return None

    async def extract_all(self,
                          files: Dict[str, str]) -> RuleExtractionResult:
        """Extract rules from all files."""
        all_rules = []

        for file_path, source in files.items():
            rules = await self.extract_from_file(file_path, source)
            all_rules.extend(rules)

        # Organize results
        by_type = {}
        by_file = {}

        for rule in all_rules:
            by_type.setdefault(rule.rule_type, []).append(rule)
            by_file.setdefault(rule.source_file, []).append(rule)

        high_conf = sum(1 for r in all_rules if r.confidence >= 0.8)

        return RuleExtractionResult(
            rules=all_rules,
            rules_by_type=by_type,
            rules_by_file=by_file,
            total_rules=len(all_rules),
            high_confidence_rules=high_conf
        )
```

### 2.4 NFRDetector

Detecteert Non-Functional Requirements in code.

```python
# backend/app/services/nfr_detector.py

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum
import re

class NFRCategory(Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"
    SCALABILITY = "scalability"
    USABILITY = "usability"
    ACCESSIBILITY = "accessibility"

@dataclass
class NFRDetection:
    id: str
    category: NFRCategory
    pattern_matched: str
    source_file: str
    source_line: int
    code_snippet: str
    confidence: float
    description: str
    recommendation: Optional[str] = None
    compliance_relevance: List[str] = field(default_factory=list)

@dataclass
class NFRReport:
    detections: List[NFRDetection]
    by_category: Dict[NFRCategory, List[NFRDetection]]
    coverage_score: float  # 0.0 - 1.0, how well NFRs are addressed
    gaps: List[str]        # Categories with no detections

class NFRDetector:
    """
    Detects Non-Functional Requirements patterns in code.

    Categories:
    - Security: Authentication, authorization, encryption, input validation
    - Performance: Caching, pagination, async operations, indexing
    - Reliability: Error handling, retries, circuit breakers, health checks
    - Maintainability: Logging, documentation, modularity, testing
    """

    NFR_PATTERNS = {
        NFRCategory.SECURITY: {
            "patterns": [
                (r'(?:password|secret|api_key|token)\s*=', "Hardcoded credential detected", 0.95),
                (r'@(?:login_required|authenticated)', "Authentication check", 0.9),
                (r'\.(?:encrypt|decrypt|hash)\(', "Encryption/hashing used", 0.85),
                (r'(?:sanitize|escape|validate)_?(?:input|html|sql)', "Input sanitization", 0.9),
                (r'Content-Security-Policy|X-Frame-Options', "Security headers", 0.85),
                (r'(?:CSRF|csrf)_(?:token|protect)', "CSRF protection", 0.9),
                (r'rate_limit|throttle', "Rate limiting", 0.85),
                (r'ssl_context|verify_ssl|https_only', "SSL/TLS configuration", 0.85),
            ],
            "compliance": ["NEN7510", "ISO27001", "SOC2"],
        },
        NFRCategory.PERFORMANCE: {
            "patterns": [
                (r'@cache|\.cache\(|lru_cache|memoize', "Caching implementation", 0.9),
                (r'pagination|page_size|limit\s*=\s*\d+|offset\s*=', "Pagination", 0.85),
                (r'async\s+def|await\s+|asyncio\.|aiohttp', "Async operations", 0.8),
                (r'(?:db_)?index|create_index|add_index', "Database indexing", 0.85),
                (r'bulk_(?:create|update|insert)|batch_', "Bulk operations", 0.85),
                (r'connection_pool|pool_size', "Connection pooling", 0.85),
                (r'lazy_load|defer|prefetch', "Lazy loading/prefetching", 0.8),
                (r'(?:response_)?timeout\s*=', "Timeout configuration", 0.8),
            ],
            "compliance": [],
        },
        NFRCategory.RELIABILITY: {
            "patterns": [
                (r'try\s*:|except\s+\w+', "Exception handling", 0.7),
                (r'@retry|retry_on_|max_retries', "Retry mechanism", 0.9),
                (r'circuit_breaker|CircuitBreaker', "Circuit breaker pattern", 0.95),
                (r'health_check|healthz|ready', "Health check endpoint", 0.9),
                (r'@transactional|with\s+transaction', "Transaction management", 0.85),
                (r'backup|recover|rollback', "Backup/recovery", 0.8),
                (r'failover|fallback|redundan', "Failover/redundancy", 0.85),
                (r'dead_letter|dlq|error_queue', "Dead letter queue", 0.9),
            ],
            "compliance": [],
        },
        NFRCategory.MAINTAINABILITY: {
            "patterns": [
                (r'logger\.|logging\.|log\.(debug|info|warning|error)', "Logging implementation", 0.85),
                (r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', "Docstring present", 0.7),
                (r'#\s*TODO|#\s*FIXME|#\s*XXX', "Technical debt marker", 0.8),
                (r'def\s+test_|class\s+Test|@pytest|unittest', "Unit tests", 0.9),
                (r'@dataclass|@attr\.s|NamedTuple', "Structured data classes", 0.75),
                (r'from\s+abc\s+import|ABC,?\s*abstractmethod', "Abstract interfaces", 0.8),
                (r'config\.|settings\.|\.env|environ', "Configuration externalized", 0.8),
                (r'type:\s*\w+|\):\s*\w+|->\\s*\w+', "Type annotations", 0.75),
            ],
            "compliance": [],
        },
        NFRCategory.SCALABILITY: {
            "patterns": [
                (r'(?:redis|memcached|celery)\.|queue\.|message_broker', "Message queue/cache", 0.9),
                (r'shard|partition|replica', "Data partitioning", 0.9),
                (r'load_balanc|round_robin|least_conn', "Load balancing", 0.9),
                (r'stateless|session_store|external_session', "Stateless design", 0.85),
                (r'horizontal_scal|auto_scal|scale_out', "Horizontal scaling", 0.9),
            ],
            "compliance": [],
        },
    }

    def __init__(self):
        self._detection_counter = 0
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for performance."""
        self.compiled_patterns = {}
        for category, config in self.NFR_PATTERNS.items():
            self.compiled_patterns[category] = [
                (re.compile(pattern, re.IGNORECASE | re.MULTILINE), desc, conf)
                for pattern, desc, conf in config["patterns"]
            ]

    async def detect_in_file(self,
                              file_path: str,
                              source: str) -> List[NFRDetection]:
        """Detect NFR patterns in a single file."""
        detections = []
        lines = source.split('\n')

        for category, patterns in self.compiled_patterns.items():
            compliance = self.NFR_PATTERNS[category].get("compliance", [])

            for pattern, description, confidence in patterns:
                for match in pattern.finditer(source):
                    # Find line number
                    line_num = source[:match.start()].count('\n') + 1

                    # Get code snippet (context around match)
                    start_line = max(0, line_num - 2)
                    end_line = min(len(lines), line_num + 2)
                    snippet = '\n'.join(lines[start_line:end_line])

                    self._detection_counter += 1

                    detections.append(NFRDetection(
                        id=f"NFR-{self._detection_counter:04d}",
                        category=category,
                        pattern_matched=match.group(0),
                        source_file=file_path,
                        source_line=line_num,
                        code_snippet=snippet,
                        confidence=confidence,
                        description=description,
                        compliance_relevance=compliance
                    ))

        return detections

    async def detect_all(self,
                         files: Dict[str, str]) -> NFRReport:
        """Detect NFR patterns across all files."""
        all_detections = []

        for file_path, source in files.items():
            detections = await self.detect_in_file(file_path, source)
            all_detections.extend(detections)

        # Organize by category
        by_category = {}
        for detection in all_detections:
            by_category.setdefault(detection.category, []).append(detection)

        # Find gaps (categories with no detections)
        all_categories = set(NFRCategory)
        detected_categories = set(by_category.keys())
        gaps = [cat.value for cat in (all_categories - detected_categories)]

        # Calculate coverage score
        coverage = len(detected_categories) / len(all_categories)

        return NFRReport(
            detections=all_detections,
            by_category=by_category,
            coverage_score=coverage,
            gaps=gaps
        )

    def get_recommendations(self, report: NFRReport) -> List[str]:
        """Generate recommendations based on NFR gaps."""
        recommendations = []

        gap_recommendations = {
            "security": "Consider adding authentication, input validation, and encryption",
            "performance": "Consider adding caching, pagination, and async operations",
            "reliability": "Consider adding error handling, retries, and health checks",
            "maintainability": "Consider adding logging, documentation, and unit tests",
            "scalability": "Consider adding message queues and stateless design",
        }

        for gap in report.gaps:
            if gap in gap_recommendations:
                recommendations.append(gap_recommendations[gap])

        return recommendations
```

### 2.5 ComplianceChecker

Pluggable compliance framework per project.

```python
# backend/app/services/compliance_checker.py

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from enum import Enum
from abc import ABC, abstractmethod
import json

class ComplianceFramework(Enum):
    NEN7510 = "NEN7510"      # Dutch healthcare
    ISO27001 = "ISO27001"    # Information security
    HIPAA = "HIPAA"          # US healthcare
    SOC2 = "SOC2"            # Service organization
    GDPR = "GDPR"            # EU privacy
    PCI_DSS = "PCI_DSS"      # Payment card

@dataclass
class ComplianceRequirement:
    id: str                    # e.g., "NEN7510-7.1.1"
    framework: ComplianceFramework
    title: str
    description: str
    category: str              # e.g., "Access Control", "Encryption"
    required_patterns: List[str]  # Patterns that should be present
    forbidden_patterns: List[str] # Patterns that should NOT be present
    severity: str              # critical, high, medium, low

@dataclass
class ComplianceViolation:
    requirement: ComplianceRequirement
    violation_type: str        # "missing" or "forbidden"
    file_path: str
    line_number: Optional[int]
    code_snippet: Optional[str]
    remediation: str

@dataclass
class ComplianceReport:
    frameworks_checked: List[ComplianceFramework]
    violations: List[ComplianceViolation]
    passed_requirements: List[str]
    compliance_score: float    # 0.0 - 1.0
    by_framework: Dict[str, Dict]
    by_severity: Dict[str, List[ComplianceViolation]]

class ComplianceRuleSet(ABC):
    """Abstract base class for compliance rule sets."""

    @abstractmethod
    def get_requirements(self) -> List[ComplianceRequirement]:
        pass

    @abstractmethod
    def get_framework(self) -> ComplianceFramework:
        pass

class NEN7510RuleSet(ComplianceRuleSet):
    """NEN7510 (Dutch healthcare) compliance rules."""

    def get_framework(self) -> ComplianceFramework:
        return ComplianceFramework.NEN7510

    def get_requirements(self) -> List[ComplianceRequirement]:
        return [
            ComplianceRequirement(
                id="NEN7510-9.4.1",
                framework=ComplianceFramework.NEN7510,
                title="Information access restriction",
                description="Access to information must be restricted based on access control policy",
                category="Access Control",
                required_patterns=[
                    r'@login_required|@authenticated|is_authenticated',
                    r'has_permission|check_permission|require_permission',
                ],
                forbidden_patterns=[],
                severity="critical"
            ),
            ComplianceRequirement(
                id="NEN7510-10.1.1",
                framework=ComplianceFramework.NEN7510,
                title="Cryptographic controls",
                description="Encryption must be used for sensitive health data",
                category="Encryption",
                required_patterns=[
                    r'\.encrypt\(|\.decrypt\(|AES|RSA|fernet',
                    r'hash_password|bcrypt|argon2|pbkdf2',
                ],
                forbidden_patterns=[
                    r'password\s*=\s*["\'][^"\']+["\']',  # Hardcoded passwords
                    r'md5\(',  # Weak hashing
                ],
                severity="high"
            ),
            ComplianceRequirement(
                id="NEN7510-12.4.1",
                framework=ComplianceFramework.NEN7510,
                title="Event logging",
                description="All access to patient data must be logged",
                category="Audit",
                required_patterns=[
                    r'logger\.|logging\.|audit_log|access_log',
                ],
                forbidden_patterns=[],
                severity="high"
            ),
        ]

class ISO27001RuleSet(ComplianceRuleSet):
    """ISO 27001 compliance rules."""

    def get_framework(self) -> ComplianceFramework:
        return ComplianceFramework.ISO27001

    def get_requirements(self) -> List[ComplianceRequirement]:
        return [
            ComplianceRequirement(
                id="ISO27001-A.9.4.1",
                framework=ComplianceFramework.ISO27001,
                title="Information access restriction",
                description="Access to information and application system functions shall be restricted",
                category="Access Control",
                required_patterns=[
                    r'@login_required|@authenticated',
                    r'role_required|permission_required',
                ],
                forbidden_patterns=[],
                severity="high"
            ),
            ComplianceRequirement(
                id="ISO27001-A.10.1.1",
                framework=ComplianceFramework.ISO27001,
                title="Cryptographic controls policy",
                description="A policy on the use of cryptographic controls shall be developed",
                category="Encryption",
                required_patterns=[
                    r'ssl|tls|https|encrypt',
                ],
                forbidden_patterns=[
                    r'verify\s*=\s*False',  # SSL verification disabled
                ],
                severity="high"
            ),
        ]

class HIPAARuleSet(ComplianceRuleSet):
    """HIPAA (US healthcare) compliance rules - stub implementation."""

    def get_framework(self) -> ComplianceFramework:
        return ComplianceFramework.HIPAA

    def get_requirements(self) -> List[ComplianceRequirement]:
        # Stub - to be expanded
        return [
            ComplianceRequirement(
                id="HIPAA-164.312(a)(1)",
                framework=ComplianceFramework.HIPAA,
                title="Access Control",
                description="Implement technical policies for electronic systems maintaining PHI",
                category="Access Control",
                required_patterns=[r'@authenticated|require_auth'],
                forbidden_patterns=[],
                severity="critical"
            ),
        ]

class SOC2RuleSet(ComplianceRuleSet):
    """SOC 2 compliance rules - stub implementation."""

    def get_framework(self) -> ComplianceFramework:
        return ComplianceFramework.SOC2

    def get_requirements(self) -> List[ComplianceRequirement]:
        # Stub - to be expanded
        return [
            ComplianceRequirement(
                id="SOC2-CC6.1",
                framework=ComplianceFramework.SOC2,
                title="Logical Access Security",
                description="Logical access security software controls",
                category="Access Control",
                required_patterns=[r'auth|login|permission'],
                forbidden_patterns=[],
                severity="high"
            ),
        ]

class ComplianceChecker:
    """
    Pluggable compliance checker supporting multiple frameworks.

    Usage:
        checker = ComplianceChecker()
        checker.add_framework(ComplianceFramework.NEN7510)
        checker.add_framework(ComplianceFramework.ISO27001)
        report = await checker.check_compliance(files)
    """

    FRAMEWORK_RULESETS = {
        ComplianceFramework.NEN7510: NEN7510RuleSet,
        ComplianceFramework.ISO27001: ISO27001RuleSet,
        ComplianceFramework.HIPAA: HIPAARuleSet,
        ComplianceFramework.SOC2: SOC2RuleSet,
    }

    def __init__(self):
        self.active_frameworks: List[ComplianceFramework] = []
        self.rulesets: List[ComplianceRuleSet] = []

    def add_framework(self, framework: ComplianceFramework):
        """Add a compliance framework to check."""
        if framework not in self.active_frameworks:
            self.active_frameworks.append(framework)
            ruleset_class = self.FRAMEWORK_RULESETS.get(framework)
            if ruleset_class:
                self.rulesets.append(ruleset_class())

    def remove_framework(self, framework: ComplianceFramework):
        """Remove a compliance framework."""
        if framework in self.active_frameworks:
            self.active_frameworks.remove(framework)
            self.rulesets = [rs for rs in self.rulesets if rs.get_framework() != framework]

    def set_frameworks_from_project(self, project_settings: Dict):
        """Configure frameworks from project settings."""
        self.active_frameworks.clear()
        self.rulesets.clear()

        framework_names = project_settings.get("compliance_frameworks", [])
        for name in framework_names:
            try:
                framework = ComplianceFramework(name)
                self.add_framework(framework)
            except ValueError:
                pass  # Unknown framework, skip

    async def check_compliance(self,
                                files: Dict[str, str],
                                nfr_detections: Optional[List] = None) -> ComplianceReport:
        """Check compliance across all active frameworks."""
        all_violations = []
        passed = []

        # Combine all sources for searching
        combined_source = "\n\n".join(f"# {path}\n{content}" for path, content in files.items())

        for ruleset in self.rulesets:
            for requirement in ruleset.get_requirements():
                violations = self._check_requirement(requirement, files, combined_source)

                if violations:
                    all_violations.extend(violations)
                else:
                    passed.append(requirement.id)

        # Organize by framework and severity
        by_framework = {}
        by_severity = {"critical": [], "high": [], "medium": [], "low": []}

        for violation in all_violations:
            fw = violation.requirement.framework.value
            by_framework.setdefault(fw, {"violations": [], "passed": []})["violations"].append(violation)
            by_severity.setdefault(violation.requirement.severity, []).append(violation)

        for req_id in passed:
            # Find framework for passed requirement
            for ruleset in self.rulesets:
                for req in ruleset.get_requirements():
                    if req.id == req_id:
                        fw = req.framework.value
                        by_framework.setdefault(fw, {"violations": [], "passed": []})["passed"].append(req_id)

        # Calculate compliance score
        total_requirements = sum(len(rs.get_requirements()) for rs in self.rulesets)
        if total_requirements > 0:
            score = len(passed) / total_requirements
        else:
            score = 1.0

        return ComplianceReport(
            frameworks_checked=self.active_frameworks,
            violations=all_violations,
            passed_requirements=passed,
            compliance_score=score,
            by_framework=by_framework,
            by_severity=by_severity
        )

    def _check_requirement(self,
                           requirement: ComplianceRequirement,
                           files: Dict[str, str],
                           combined_source: str) -> List[ComplianceViolation]:
        """Check a single compliance requirement."""
        import re
        violations = []

        # Check required patterns
        for pattern in requirement.required_patterns:
            if not re.search(pattern, combined_source, re.IGNORECASE):
                violations.append(ComplianceViolation(
                    requirement=requirement,
                    violation_type="missing",
                    file_path="(project-wide)",
                    line_number=None,
                    code_snippet=None,
                    remediation=f"Required pattern not found: {pattern}"
                ))

        # Check forbidden patterns
        for pattern in requirement.forbidden_patterns:
            for file_path, source in files.items():
                for match in re.finditer(pattern, source, re.IGNORECASE):
                    line_num = source[:match.start()].count('\n') + 1
                    lines = source.split('\n')
                    snippet = lines[line_num - 1] if line_num <= len(lines) else ""

                    violations.append(ComplianceViolation(
                        requirement=requirement,
                        violation_type="forbidden",
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=snippet,
                        remediation=f"Forbidden pattern detected: {pattern}"
                    ))

        return violations
```

### 2.6 StaticAnalysisOrchestrator (Cycle 0)

Orchestreert alle static analysis componenten.

```python
# backend/app/services/static_analysis_orchestrator.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio

from app.services.program_slicer import ProgramSlicer, ProgramSlice, LanguageSupport
from app.services.variable_classifier import VariableClassifier, VariableClassificationResult
from app.services.business_rule_extractor import BusinessRuleExtractor, RuleExtractionResult
from app.services.nfr_detector import NFRDetector, NFRReport
from app.services.compliance_checker import ComplianceChecker, ComplianceReport, ComplianceFramework

@dataclass
class StaticAnalysisConfig:
    """Configuration for static analysis."""
    enable_slicing: bool = True
    enable_variable_classification: bool = True
    enable_business_rules: bool = True
    enable_nfr_detection: bool = True
    enable_compliance: bool = True
    compliance_frameworks: List[str] = field(default_factory=list)
    custom_domain_terms: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=lambda: ["python"])

@dataclass
class StaticAnalysisResult:
    """Complete result of Cycle 0 static analysis."""
    id: str
    project_id: int
    started_at: datetime
    completed_at: datetime

    # Component results
    slices: List[ProgramSlice] = field(default_factory=list)
    variable_classification: Optional[VariableClassificationResult] = None
    business_rules: Optional[RuleExtractionResult] = None
    nfr_report: Optional[NFRReport] = None
    compliance_report: Optional[ComplianceReport] = None

    # Summary metrics
    total_files_analyzed: int = 0
    total_lines_of_code: int = 0
    domain_coverage: float = 0.0
    nfr_coverage: float = 0.0
    compliance_score: float = 0.0

    # For LLM enrichment
    high_confidence_findings: List[Dict] = field(default_factory=list)
    low_confidence_findings: List[Dict] = field(default_factory=list)

    def to_llm_context(self) -> Dict[str, Any]:
        """Convert to context for LLM enrichment."""
        return {
            "static_analysis_summary": {
                "files_analyzed": self.total_files_analyzed,
                "lines_of_code": self.total_lines_of_code,
                "domain_coverage": self.domain_coverage,
                "nfr_coverage": self.nfr_coverage,
                "compliance_score": self.compliance_score,
            },
            "business_rules": [
                {
                    "id": r.id,
                    "type": r.rule_type.value,
                    "condition": r.condition,
                    "action": r.action,
                    "natural_language": r.natural_language,
                    "confidence": r.confidence,
                }
                for r in (self.business_rules.rules if self.business_rules else [])
            ],
            "nfr_detections": [
                {
                    "category": d.category.value,
                    "description": d.description,
                    "confidence": d.confidence,
                }
                for d in (self.nfr_report.detections if self.nfr_report else [])
            ],
            "compliance_violations": [
                {
                    "requirement_id": v.requirement.id,
                    "framework": v.requirement.framework.value,
                    "violation_type": v.violation_type,
                    "remediation": v.remediation,
                }
                for v in (self.compliance_report.violations if self.compliance_report else [])
            ],
            "domain_variables": (
                self.variable_classification.domain_variables
                if self.variable_classification else []
            ),
        }

class StaticAnalysisOrchestrator:
    """
    Orchestrates Cycle 0: Static Analysis for all extraction tiers.

    This is the foundation layer that provides deterministic analysis
    before LLM enrichment (Cycles 1-5).
    """

    def __init__(self, db_session):
        self.db = db_session

    async def run_analysis(self,
                           project_id: int,
                           files: Dict[str, str],
                           config: StaticAnalysisConfig) -> StaticAnalysisResult:
        """Run complete static analysis pipeline."""
        from uuid import uuid4

        started_at = datetime.utcnow()
        result_id = str(uuid4())

        # Initialize components
        variable_classifier = VariableClassifier(
            custom_domain_terms=config.custom_domain_terms
        )
        business_rule_extractor = BusinessRuleExtractor(variable_classifier)
        nfr_detector = NFRDetector()
        compliance_checker = ComplianceChecker()

        # Configure compliance frameworks
        for framework_name in config.compliance_frameworks:
            try:
                framework = ComplianceFramework(framework_name)
                compliance_checker.add_framework(framework)
            except ValueError:
                pass

        # Run all analyses in parallel
        tasks = []

        # Variable classification
        if config.enable_variable_classification:
            all_variables = self._extract_all_variables(files)
            variable_result = variable_classifier.classify_all(all_variables)
        else:
            variable_result = None

        # Business rule extraction
        if config.enable_business_rules:
            business_rules = await business_rule_extractor.extract_all(files)
        else:
            business_rules = None

        # NFR detection
        if config.enable_nfr_detection:
            nfr_report = await nfr_detector.detect_all(files)
        else:
            nfr_report = None

        # Compliance check
        if config.enable_compliance and compliance_checker.active_frameworks:
            compliance_report = await compliance_checker.check_compliance(
                files,
                nfr_report.detections if nfr_report else None
            )
        else:
            compliance_report = None

        # Program slicing (if enabled)
        slices = []
        if config.enable_slicing:
            for lang_str in config.languages:
                try:
                    lang = LanguageSupport(lang_str)
                    slicer = ProgramSlicer(lang)
                    lang_files = [f for f in files.keys() if self._matches_language(f, lang)]
                    if lang_files:
                        await slicer.build_dependency_graph(lang_files)
                        # Slice key entry points
                        # ... slicing logic ...
                except ValueError:
                    pass

        completed_at = datetime.utcnow()

        # Calculate metrics
        total_loc = sum(source.count('\n') + 1 for source in files.values())
        domain_coverage = variable_result.domain_coverage if variable_result else 0.0
        nfr_coverage = nfr_report.coverage_score if nfr_report else 0.0
        compliance_score = compliance_report.compliance_score if compliance_report else 1.0

        # Separate high/low confidence findings
        high_conf = []
        low_conf = []

        if business_rules:
            for rule in business_rules.rules:
                finding = {
                    "type": "business_rule",
                    "id": rule.id,
                    "description": rule.natural_language,
                    "confidence": rule.confidence,
                    "source": f"{rule.source_file}:{rule.source_lines[0]}"
                }
                if rule.confidence >= 0.8:
                    high_conf.append(finding)
                else:
                    low_conf.append(finding)

        if nfr_report:
            for detection in nfr_report.detections:
                finding = {
                    "type": "nfr",
                    "id": detection.id,
                    "category": detection.category.value,
                    "description": detection.description,
                    "confidence": detection.confidence,
                    "source": f"{detection.source_file}:{detection.source_line}"
                }
                if detection.confidence >= 0.8:
                    high_conf.append(finding)
                else:
                    low_conf.append(finding)

        return StaticAnalysisResult(
            id=result_id,
            project_id=project_id,
            started_at=started_at,
            completed_at=completed_at,
            slices=slices,
            variable_classification=variable_result,
            business_rules=business_rules,
            nfr_report=nfr_report,
            compliance_report=compliance_report,
            total_files_analyzed=len(files),
            total_lines_of_code=total_loc,
            domain_coverage=domain_coverage,
            nfr_coverage=nfr_coverage,
            compliance_score=compliance_score,
            high_confidence_findings=high_conf,
            low_confidence_findings=low_conf,
        )

    def _extract_all_variables(self, files: Dict[str, str]) -> List[str]:
        """Extract all variable names from files."""
        import re
        variables = set()

        # Python pattern
        python_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*='

        for source in files.values():
            matches = re.findall(python_pattern, source)
            variables.update(matches)

        return list(variables)

    def _matches_language(self, file_path: str, language: LanguageSupport) -> bool:
        """Check if file matches language."""
        extensions = {
            LanguageSupport.PYTHON: ['.py'],
            LanguageSupport.JAVASCRIPT: ['.js', '.ts', '.jsx', '.tsx'],
            LanguageSupport.CSHARP: ['.cs'],
            LanguageSupport.SQL: ['.sql'],
        }
        return any(file_path.endswith(ext) for ext in extensions.get(language, []))
```

---

## 3. Conflict Detection System

### 3.1 Conflict Definition

Een conflict treedt op wanneer:

1. **LLM overrules static met lage confidence**
   - Static analysis vindt iets
   - LLM verwijdert of wijzigt het
   - LLM confidence < 72.5%

2. **Expliciete disagreement tussen LLMs**
   - LLM A zegt "ja"
   - LLM B zegt "nee"
   - Geen consensus bereikt

3. **Classification change**
   - Static/LLM1: "Dit is een Epic"
   - LLM2: "Dit is een Feature"
   - Significant verschil in scope

4. **Item removal**
   - Static analysis vindt business rule/NFR
   - LLM markeert als irrelevant
   - Potentieel gemiste requirement

### 3.2 Conflict Detection Implementation

```python
# backend/app/services/conflict_detector.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

class ConflictType(Enum):
    LLM_OVERRULE_LOW_CONFIDENCE = "llm_overrule_low_confidence"
    LLM_DISAGREEMENT = "llm_disagreement"
    CLASSIFICATION_CHANGE = "classification_change"
    ITEM_REMOVAL = "item_removal"

class ConflictSeverity(Enum):
    CRITICAL = "critical"   # Always requires human review
    HIGH = "high"           # Requires review for STANDARD+
    MEDIUM = "medium"       # Optional review
    LOW = "low"             # Informational

@dataclass
class ConflictItem:
    id: str
    conflict_type: ConflictType
    severity: ConflictSeverity

    # What was detected
    static_finding: Optional[Dict]
    llm_finding: Optional[Dict]

    # Confidence scores
    static_confidence: float
    llm_confidence: float

    # Context
    source_file: str
    source_lines: tuple
    description: str

    # Resolution
    requires_human_review: bool
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None

@dataclass
class ConflictReport:
    conflicts: List[ConflictItem]
    total_conflicts: int
    by_type: Dict[ConflictType, int]
    by_severity: Dict[ConflictSeverity, int]
    requires_human_review: int
    auto_resolvable: int

class ConflictDetector:
    """
    Detects conflicts between static analysis and LLM enrichment.

    Key threshold: 72.5% confidence
    - If LLM overrules static with confidence < 72.5%, flag for human review
    """

    CONFIDENCE_THRESHOLD = 0.725  # 72.5%

    def __init__(self, tier: str):
        self.tier = tier
        self._conflict_counter = 0

    def detect_conflicts(self,
                         static_result: 'StaticAnalysisResult',
                         llm_results: List[Dict]) -> ConflictReport:
        """Detect all conflicts between static and LLM results."""
        conflicts = []

        # Check for LLM overrules with low confidence
        conflicts.extend(self._check_overrules(static_result, llm_results))

        # Check for LLM disagreements
        conflicts.extend(self._check_llm_disagreements(llm_results))

        # Check for classification changes
        conflicts.extend(self._check_classification_changes(static_result, llm_results))

        # Check for item removals
        conflicts.extend(self._check_removals(static_result, llm_results))

        # Organize results
        by_type = {}
        by_severity = {}
        requires_review = 0
        auto_resolve = 0

        for conflict in conflicts:
            by_type[conflict.conflict_type] = by_type.get(conflict.conflict_type, 0) + 1
            by_severity[conflict.severity] = by_severity.get(conflict.severity, 0) + 1

            if conflict.requires_human_review:
                requires_review += 1
            else:
                auto_resolve += 1

        return ConflictReport(
            conflicts=conflicts,
            total_conflicts=len(conflicts),
            by_type=by_type,
            by_severity=by_severity,
            requires_human_review=requires_review,
            auto_resolvable=auto_resolve
        )

    def _check_overrules(self,
                         static_result: 'StaticAnalysisResult',
                         llm_results: List[Dict]) -> List[ConflictItem]:
        """Check for LLM overrules with low confidence."""
        conflicts = []

        # Build index of static findings
        static_findings = {}

        if static_result.business_rules:
            for rule in static_result.business_rules.rules:
                key = f"rule:{rule.source_file}:{rule.source_lines[0]}"
                static_findings[key] = {
                    "type": "business_rule",
                    "data": rule,
                    "confidence": rule.confidence
                }

        if static_result.nfr_report:
            for detection in static_result.nfr_report.detections:
                key = f"nfr:{detection.source_file}:{detection.source_line}"
                static_findings[key] = {
                    "type": "nfr",
                    "data": detection,
                    "confidence": detection.confidence
                }

        # Check LLM modifications
        for llm_result in llm_results:
            model_name = llm_result.get("model", "unknown")

            for modification in llm_result.get("modifications", []):
                key = modification.get("static_finding_key")
                llm_confidence = modification.get("confidence", 0.5)
                action = modification.get("action")  # "remove", "modify", "confirm"

                if key in static_findings and action in ["remove", "modify"]:
                    static = static_findings[key]

                    if llm_confidence < self.CONFIDENCE_THRESHOLD:
                        self._conflict_counter += 1

                        # Determine severity
                        if static["confidence"] >= 0.8:
                            severity = ConflictSeverity.CRITICAL
                        elif static["confidence"] >= 0.6:
                            severity = ConflictSeverity.HIGH
                        else:
                            severity = ConflictSeverity.MEDIUM

                        conflicts.append(ConflictItem(
                            id=f"CONFLICT-{self._conflict_counter:04d}",
                            conflict_type=ConflictType.LLM_OVERRULE_LOW_CONFIDENCE,
                            severity=severity,
                            static_finding=static,
                            llm_finding=modification,
                            static_confidence=static["confidence"],
                            llm_confidence=llm_confidence,
                            source_file=static["data"].source_file if hasattr(static["data"], "source_file") else "",
                            source_lines=(0, 0),
                            description=f"{model_name} {action}s static finding with {llm_confidence*100:.1f}% confidence (< 72.5% threshold)",
                            requires_human_review=self._requires_review(severity)
                        ))

        return conflicts

    def _check_llm_disagreements(self, llm_results: List[Dict]) -> List[ConflictItem]:
        """Check for explicit disagreements between LLMs."""
        conflicts = []

        if len(llm_results) < 2:
            return conflicts

        # Build agreement matrix
        findings_by_llm = {}
        for llm_result in llm_results:
            model = llm_result.get("model", "unknown")
            findings_by_llm[model] = set(
                f.get("id") for f in llm_result.get("findings", [])
            )

        # Find disagreements
        all_findings = set()
        for findings in findings_by_llm.values():
            all_findings.update(findings)

        for finding_id in all_findings:
            present_in = [m for m, f in findings_by_llm.items() if finding_id in f]
            absent_in = [m for m, f in findings_by_llm.items() if finding_id not in f]

            # If more than 50% disagree, flag it
            if len(absent_in) >= len(present_in):
                self._conflict_counter += 1

                conflicts.append(ConflictItem(
                    id=f"CONFLICT-{self._conflict_counter:04d}",
                    conflict_type=ConflictType.LLM_DISAGREEMENT,
                    severity=ConflictSeverity.HIGH,
                    static_finding=None,
                    llm_finding={"finding_id": finding_id, "present_in": present_in, "absent_in": absent_in},
                    static_confidence=0.0,
                    llm_confidence=len(present_in) / (len(present_in) + len(absent_in)),
                    source_file="",
                    source_lines=(0, 0),
                    description=f"LLM disagreement: {present_in} include, {absent_in} exclude finding {finding_id}",
                    requires_human_review=True
                ))

        return conflicts

    def _check_classification_changes(self,
                                       static_result: 'StaticAnalysisResult',
                                       llm_results: List[Dict]) -> List[ConflictItem]:
        """Check for significant classification changes."""
        conflicts = []

        # Implementation: Compare static classifications with LLM classifications
        # Flag when Epic becomes Feature, Feature becomes Story, etc.

        return conflicts

    def _check_removals(self,
                        static_result: 'StaticAnalysisResult',
                        llm_results: List[Dict]) -> List[ConflictItem]:
        """Check for items removed by LLM that static analysis found."""
        conflicts = []

        # Get all static findings
        static_ids = set()
        if static_result.business_rules:
            static_ids.update(r.id for r in static_result.business_rules.rules)
        if static_result.nfr_report:
            static_ids.update(d.id for d in static_result.nfr_report.detections)

        # Check which are missing from LLM output
        for llm_result in llm_results:
            llm_ids = set(f.get("static_ref") for f in llm_result.get("findings", []) if f.get("static_ref"))

            removed = static_ids - llm_ids
            for removed_id in removed:
                if llm_result.get("explicitly_removed", {}).get(removed_id):
                    self._conflict_counter += 1

                    conflicts.append(ConflictItem(
                        id=f"CONFLICT-{self._conflict_counter:04d}",
                        conflict_type=ConflictType.ITEM_REMOVAL,
                        severity=ConflictSeverity.MEDIUM,
                        static_finding={"id": removed_id},
                        llm_finding={"removed_by": llm_result.get("model"), "reason": llm_result.get("explicitly_removed", {}).get(removed_id)},
                        static_confidence=0.8,
                        llm_confidence=llm_result.get("removal_confidence", {}).get(removed_id, 0.5),
                        source_file="",
                        source_lines=(0, 0),
                        description=f"Static finding {removed_id} removed by {llm_result.get('model')}",
                        requires_human_review=self._requires_review(ConflictSeverity.MEDIUM)
                    ))

        return conflicts

    def _requires_review(self, severity: ConflictSeverity) -> bool:
        """Determine if conflict requires human review based on tier and severity."""
        tier_review_rules = {
            "BASIC": [ConflictSeverity.CRITICAL],  # Only critical
            "STANDARD": [ConflictSeverity.CRITICAL, ConflictSeverity.HIGH],  # Optional but recommended
            "PROFESSIONAL": [ConflictSeverity.CRITICAL, ConflictSeverity.HIGH, ConflictSeverity.MEDIUM],
            "PREMIUM": [ConflictSeverity.CRITICAL, ConflictSeverity.HIGH, ConflictSeverity.MEDIUM, ConflictSeverity.LOW],
        }

        required_severities = tier_review_rules.get(self.tier, [ConflictSeverity.CRITICAL])
        return severity in required_severities
```

---

## 4. Database Schema

### 4.1 New Tables

```sql
-- Migration: 045_add_static_analysis_tables.py

-- Static analysis results
CREATE TABLE static_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id INTEGER NOT NULL REFERENCES projects(id),

    -- Timing
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,

    -- Configuration
    config JSONB NOT NULL,

    -- Metrics
    total_files_analyzed INTEGER DEFAULT 0,
    total_lines_of_code INTEGER DEFAULT 0,
    domain_coverage FLOAT DEFAULT 0.0,
    nfr_coverage FLOAT DEFAULT 0.0,
    compliance_score FLOAT DEFAULT 0.0,

    -- Full results (stored for migrations, bugs, features)
    variable_classification JSONB,
    business_rules JSONB,
    nfr_report JSONB,
    compliance_report JSONB,
    slices JSONB,

    -- Findings summary
    high_confidence_findings JSONB DEFAULT '[]',
    low_confidence_findings JSONB DEFAULT '[]',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_static_analysis_project ON static_analysis_results(project_id);
CREATE INDEX idx_static_analysis_created ON static_analysis_results(created_at DESC);

-- Business rules
CREATE TABLE business_rules (
    id VARCHAR(20) PRIMARY KEY,
    static_analysis_id UUID REFERENCES static_analysis_results(id),

    rule_type VARCHAR(50) NOT NULL,
    condition TEXT NOT NULL,
    action TEXT NOT NULL,
    natural_language TEXT NOT NULL,

    source_file VARCHAR(500),
    source_line_start INTEGER,
    source_line_end INTEGER,

    variables JSONB DEFAULT '[]',
    confidence FLOAT DEFAULT 0.5,
    compliance_tags JSONB DEFAULT '[]',

    -- LLM validation
    llm_validated BOOLEAN DEFAULT FALSE,
    llm_confidence FLOAT,
    llm_modifications JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_business_rules_analysis ON business_rules(static_analysis_id);
CREATE INDEX idx_business_rules_type ON business_rules(rule_type);

-- NFR detections
CREATE TABLE nfr_detections (
    id VARCHAR(20) PRIMARY KEY,
    static_analysis_id UUID REFERENCES static_analysis_results(id),

    category VARCHAR(50) NOT NULL,
    pattern_matched TEXT NOT NULL,
    description TEXT NOT NULL,

    source_file VARCHAR(500),
    source_line INTEGER,
    code_snippet TEXT,

    confidence FLOAT DEFAULT 0.5,
    compliance_relevance JSONB DEFAULT '[]',
    recommendation TEXT,

    -- LLM validation
    llm_validated BOOLEAN DEFAULT FALSE,
    llm_confidence FLOAT,
    llm_modifications JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_nfr_detections_analysis ON nfr_detections(static_analysis_id);
CREATE INDEX idx_nfr_detections_category ON nfr_detections(category);

-- Compliance violations
CREATE TABLE compliance_violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    static_analysis_id UUID REFERENCES static_analysis_results(id),

    requirement_id VARCHAR(50) NOT NULL,
    framework VARCHAR(50) NOT NULL,
    title VARCHAR(200),
    category VARCHAR(100),
    severity VARCHAR(20),

    violation_type VARCHAR(20) NOT NULL,
    file_path VARCHAR(500),
    line_number INTEGER,
    code_snippet TEXT,
    remediation TEXT,

    -- Resolution tracking
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMP,
    resolution_notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_compliance_violations_analysis ON compliance_violations(static_analysis_id);
CREATE INDEX idx_compliance_violations_framework ON compliance_violations(framework);

-- Extraction conflicts
CREATE TABLE extraction_conflicts (
    id VARCHAR(30) PRIMARY KEY,
    extraction_id UUID NOT NULL,  -- Links to deep_extractions
    static_analysis_id UUID REFERENCES static_analysis_results(id),

    conflict_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,

    static_finding JSONB,
    llm_finding JSONB,
    static_confidence FLOAT,
    llm_confidence FLOAT,

    source_file VARCHAR(500),
    source_line_start INTEGER,
    source_line_end INTEGER,
    description TEXT NOT NULL,

    requires_human_review BOOLEAN DEFAULT TRUE,
    resolved BOOLEAN DEFAULT FALSE,
    resolution TEXT,
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_extraction_conflicts_extraction ON extraction_conflicts(extraction_id);
CREATE INDEX idx_extraction_conflicts_unresolved ON extraction_conflicts(resolved) WHERE resolved = FALSE;

-- Project compliance settings
CREATE TABLE project_compliance_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id INTEGER NOT NULL REFERENCES projects(id),

    frameworks JSONB DEFAULT '[]',  -- ["NEN7510", "ISO27001"]
    custom_rules JSONB DEFAULT '[]',

    -- Review settings
    auto_flag_critical BOOLEAN DEFAULT TRUE,
    require_review_for_high BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(project_id)
);
```

---

## 5. API Endpoints

### 5.1 Static Analysis API

```python
# backend/app/api/static_analysis.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/static-analysis", tags=["static-analysis"])

class StaticAnalysisRequest(BaseModel):
    project_id: int
    enable_slicing: bool = True
    enable_variable_classification: bool = True
    enable_business_rules: bool = True
    enable_nfr_detection: bool = True
    enable_compliance: bool = True
    languages: List[str] = ["python"]

class StaticAnalysisResponse(BaseModel):
    id: str
    status: str
    message: str

@router.post("/analyze", response_model=StaticAnalysisResponse)
async def start_static_analysis(
    request: StaticAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Start a new static analysis for a project."""
    from app.services.static_analysis_orchestrator import (
        StaticAnalysisOrchestrator,
        StaticAnalysisConfig
    )

    orchestrator = StaticAnalysisOrchestrator(db)

    # Get project files
    files = await get_project_files(request.project_id, db)

    config = StaticAnalysisConfig(
        enable_slicing=request.enable_slicing,
        enable_variable_classification=request.enable_variable_classification,
        enable_business_rules=request.enable_business_rules,
        enable_nfr_detection=request.enable_nfr_detection,
        enable_compliance=request.enable_compliance,
        languages=request.languages
    )

    # Run in background
    background_tasks.add_task(
        orchestrator.run_analysis,
        request.project_id,
        files,
        config
    )

    return StaticAnalysisResponse(
        id="pending",
        status="started",
        message="Static analysis started in background"
    )

@router.get("/results/{project_id}")
async def get_static_analysis_results(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get static analysis results for a project."""
    # Implementation
    pass

@router.get("/business-rules/{project_id}")
async def get_business_rules(
    project_id: int,
    rule_type: Optional[str] = None,
    min_confidence: float = 0.0,
    db: AsyncSession = Depends(get_db)
):
    """Get extracted business rules."""
    # Implementation
    pass

@router.get("/nfr/{project_id}")
async def get_nfr_detections(
    project_id: int,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get NFR detections."""
    # Implementation
    pass

@router.get("/compliance/{project_id}")
async def get_compliance_report(
    project_id: int,
    framework: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get compliance report."""
    # Implementation
    pass

@router.get("/conflicts/{extraction_id}")
async def get_extraction_conflicts(
    extraction_id: str,
    unresolved_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get conflicts for an extraction."""
    # Implementation
    pass

@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: str,
    resolution: str,
    resolved_by: str,
    db: AsyncSession = Depends(get_db)
):
    """Resolve a conflict."""
    # Implementation
    pass
```

### 5.2 Compliance Settings API

```python
# backend/app/api/compliance_settings.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/api/compliance-settings", tags=["compliance"])

class ComplianceSettingsRequest(BaseModel):
    project_id: int
    frameworks: List[str]  # ["NEN7510", "ISO27001"]
    custom_rules: List[dict] = []
    auto_flag_critical: bool = True
    require_review_for_high: bool = True

@router.get("/{project_id}")
async def get_compliance_settings(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get compliance settings for a project."""
    # Implementation
    pass

@router.put("/{project_id}")
async def update_compliance_settings(
    project_id: int,
    settings: ComplianceSettingsRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update compliance settings for a project."""
    # Implementation
    pass

@router.get("/frameworks")
async def list_available_frameworks():
    """List all available compliance frameworks."""
    return {
        "frameworks": [
            {"id": "NEN7510", "name": "NEN 7510", "description": "Dutch healthcare information security"},
            {"id": "ISO27001", "name": "ISO 27001", "description": "Information security management"},
            {"id": "HIPAA", "name": "HIPAA", "description": "US healthcare privacy"},
            {"id": "SOC2", "name": "SOC 2", "description": "Service organization controls"},
            {"id": "GDPR", "name": "GDPR", "description": "EU General Data Protection Regulation"},
            {"id": "PCI_DSS", "name": "PCI DSS", "description": "Payment Card Industry Data Security Standard"},
        ]
    }
```

---

## 6. Implementation Timeline

### Week 97-98: Static Analysis Foundation (10 dagen)

| Dag | Deliverable | Owner |
|-----|-------------|-------|
| 1 | `ProgramSlicer` class + Python parser | Dev |
| 2 | `VariableClassifier` class + patterns | Dev |
| 3 | `BusinessRuleExtractor` class + IF-THEN patterns | Dev |
| 4 | `NFRDetector` class + all 5 categories | Dev |
| 5 | `ComplianceChecker` base class + NEN7510 rules | Dev |
| 6 | `ComplianceChecker` ISO27001 + HIPAA stubs | Dev |
| 7 | `StaticAnalysisOrchestrator` integration | Dev |
| 8 | Database migration + models | Dev |
| 9 | API endpoints static analysis | Dev |
| 10 | Unit tests + integration tests | QA |

### Week 99-100: Pipeline Integration (5 dagen)

| Dag | Deliverable | Owner |
|-----|-------------|-------|
| 1 | `ConflictDetector` class + 72.5% threshold | Dev |
| 2 | Integrate Cycle 0 into `DeepExtractionService` | Dev |
| 3 | Update tier configuration (remove FREE) | Dev |
| 4 | Conflict resolution UI (dashboard) | Frontend |
| 5 | End-to-end testing full pipeline | QA |

### Week 101: Compliance Library (5 dagen)

| Dag | Deliverable | Owner |
|-----|-------------|-------|
| 1 | SOC2 ruleset volledig | Dev |
| 2 | GDPR ruleset | Dev |
| 3 | PCI-DSS ruleset (stubs) | Dev |
| 4 | Project compliance settings UI | Frontend |
| 5 | Compliance dashboard updates | Frontend |

### Week 102: Hierarchy Completion (5 dagen)

| Dag | Deliverable | Owner |
|-----|-------------|-------|
| 1 | Mid-Level Requirements layer | Dev |
| 2 | Business Goals extraction | Dev |
| 3 | CAFCR mapping integration | Dev |
| 4 | 5-level hierarchy visualization | Frontend |
| 5 | Final testing + documentation | QA |

---

## 7. Testing Strategy

### 7.1 Unit Tests

```python
# backend/tests/services/test_static_analysis/test_program_slicer.py

import pytest
from app.services.program_slicer import ProgramSlicer, SliceCriterion, LanguageSupport

class TestProgramSlicer:
    @pytest.fixture
    def python_slicer(self):
        return ProgramSlicer(LanguageSupport.PYTHON)

    @pytest.mark.asyncio
    async def test_backward_slice_simple(self, python_slicer):
        """Test backward slicing on simple Python code."""
        source = """
def calculate_total(price, quantity):
    subtotal = price * quantity
    tax = subtotal * 0.21
    total = subtotal + tax
    return total
"""
        # ... test implementation

    @pytest.mark.asyncio
    async def test_variable_classification_domain(self, python_slicer):
        """Test domain variable classification."""
        # ...
```

### 7.2 Integration Tests

```python
# backend/tests/integration/test_hybrid_pipeline.py

import pytest
from app.services.static_analysis_orchestrator import StaticAnalysisOrchestrator
from app.services.deep_extraction_service import DeepExtractionService
from app.services.conflict_detector import ConflictDetector

class TestHybridPipeline:
    @pytest.mark.asyncio
    async def test_full_pipeline_basic_tier(self, db_session):
        """Test full pipeline for BASIC tier."""
        # 1. Run static analysis (Cycle 0)
        # 2. Run LLM enrichment (Cycle 1-5)
        # 3. Detect conflicts
        # 4. Verify output
        pass

    @pytest.mark.asyncio
    async def test_conflict_detection_threshold(self, db_session):
        """Test 72.5% confidence threshold."""
        # ...
```

---

## 8. Migration Path

### 8.1 Existing Projects

Voor bestaande projecten met extractions:

1. **Geen automatische re-run** - Bestaande extractions blijven intact
2. **Optional re-run** - Klanten kunnen kiezen om opnieuw te extraheren met Cycle 0
3. **New extractions only** - Cycle 0 alleen voor nieuwe extraction runs

### 8.2 Tier Migration

| Oud | Nieuw | Actie |
|-----|-------|-------|
| FREE | - | Niet meer beschikbaar |
| BASIC (5 LLMs) | BASIC (Static + 3 Ollama) | Prijs gelijk, minder LLMs maar + Static |
| STANDARD | STANDARD (Static + 5 LLMs) | Geen wijziging |
| PROFESSIONAL | PROFESSIONAL (Static + 7 LLMs) | Geen wijziging |
| PREMIUM | PREMIUM (Static + 10 LLMs) | Geen wijziging |

---

## 9. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Static coverage** | ≥80% business rules | Static vs LLM discovery rate |
| **Conflict rate** | ≤15% | Conflicts / total findings |
| **Human review reduction** | ≥30% | Compared to pure LLM approach |
| **NFR detection** | 4/4 categories | Per project coverage |
| **Compliance automation** | ≥70% checks | Automated vs manual checks |
| **Extraction time** | ≤+10% | With Cycle 0 vs without |

---

## 10. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Static analysis too slow | High | Async processing, caching, incremental analysis |
| False positives | Medium | LLM validation, adjustable thresholds |
| Language support gaps | Medium | Extensible parser architecture, priority languages first |
| Compliance framework incomplete | Low | Stub implementations, iterative enhancement |
| Conflict overload | Medium | Smart severity classification, batch review UI |

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [ROADMAP.md](../../ROADMAP.md) | Project roadmap - Week 97-102 |
| [ARCHITECTURE.md](../../ARCHITECTURE.md) | System architecture |
| [deep-extraction-pipeline.md](deep-extraction-pipeline.md) | Current 5-cycle pipeline |
| [code-driven-backlog-generation.md](code-driven-backlog-generation.md) | Backlog extraction |

---

**Created**: Week 96
**Last Updated**: Week 96
**Author**: MarQed.ai Development Team
