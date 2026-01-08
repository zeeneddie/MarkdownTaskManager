# backend/app/services/static_analysis/business_rule_extractor.py
"""
Business Rule Extractor - Extracts IF-THEN business rules from code.

Detects patterns including:
- IF-THEN conditionals
- Validation logic
- Authorization checks
- Business calculations
- State machine transitions

Part of Fase 15: Hybrid Static-LLM Extraction Pipeline
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING
from enum import Enum
import ast
import re
import logging

if TYPE_CHECKING:
    from .variable_classifier import VariableClassifier

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Types of business rules."""
    VALIDATION = "validation"       # Input validation rules
    CALCULATION = "calculation"     # Business calculations
    AUTHORIZATION = "authorization" # Access control rules
    WORKFLOW = "workflow"           # State transitions
    CONSTRAINT = "constraint"       # Business constraints
    DERIVATION = "derivation"       # Derived values


@dataclass
class BusinessRule:
    """A detected business rule."""
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
    """Result of extracting all rules."""
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
        r'if\s+.*(?:min|max|range|between)',
        r'if\s+.*(?:empty|blank|null|none)',
        r'raise\s+(?:ValidationError|ValueError)',
    ]

    AUTHORIZATION_PATTERNS = [
        r'if\s+(?:\w+\.)?(?:is_admin|is_authenticated|has_permission|can_)',
        r'if\s+(?:\w+\.)?role\s*[=!]=',
        r'if\s+(?:\w+\.)?user\.(?:is_|has_|can_)',
        r'@(?:login_required|permission_required|roles_required|authenticated)',
        r'require[_a-z]*(?:auth|permission|role)',
        r'(?:check|verify)_(?:permission|role|access)',
        r'if\s+.*(?:authorized|authenticated|logged_in)',
    ]

    CALCULATION_PATTERNS = [
        r'(\w+)\s*=\s*(\w+)\s*[+\-*/]\s*(\w+)',
        r'total\s*[+]=',
        r'sum\s*\(',
        r'calculate[_a-z]*\(',
        r'compute[_a-z]*\(',
        r'(?:price|cost|amount|total|tax|discount)\s*=',
        r'(?:avg|average|mean|median)\s*\(',
        r'round\s*\(',
    ]

    WORKFLOW_PATTERNS = [
        r'status\s*=\s*["\'](\w+)["\']',
        r'state\s*=\s*["\'](\w+)["\']',
        r'transition[_a-z]*\(',
        r'if\s+status\s*==\s*["\'](\w+)["\']',
        r'\.change_state\(',
        r'(?:approve|reject|submit|cancel|complete)\s*\(',
        r'set_status\s*\(',
        r'workflow[_a-z]*\.',
    ]

    CONSTRAINT_PATTERNS = [
        r'if\s+.*\s*[<>=!]+\s*.*:',
        r'assert\s+',
        r'must_be|should_be|required',
        r'constraint[_a-z]*',
        r'enforce[_a-z]*',
    ]

    DERIVATION_PATTERNS = [
        r'@property',
        r'@cached_property',
        r'def\s+get_\w+',
        r'\.computed',
        r'derived_from',
    ]

    def __init__(self, variable_classifier: Optional['VariableClassifier'] = None):
        """
        Initialize extractor with optional variable classifier.

        Args:
            variable_classifier: Optional classifier for filtering domain variables
        """
        self.variable_classifier = variable_classifier
        self._rule_counter = 0
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for performance."""
        self.validation_regex = [re.compile(p, re.IGNORECASE) for p in self.VALIDATION_PATTERNS]
        self.authorization_regex = [re.compile(p, re.IGNORECASE) for p in self.AUTHORIZATION_PATTERNS]
        self.calculation_regex = [re.compile(p, re.IGNORECASE) for p in self.CALCULATION_PATTERNS]
        self.workflow_regex = [re.compile(p, re.IGNORECASE) for p in self.WORKFLOW_PATTERNS]
        self.constraint_regex = [re.compile(p, re.IGNORECASE) for p in self.CONSTRAINT_PATTERNS]
        self.derivation_regex = [re.compile(p, re.IGNORECASE) for p in self.DERIVATION_PATTERNS]

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
        except SyntaxError as e:
            logger.warning(f"Syntax error parsing {file_path}: {e}")
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
                # Check for derivation patterns (property getters)
                if node.name.startswith('get_') or node.name.startswith('calculate_'):
                    rule = self._analyze_derivation(node, file_path, source)
                    if rule:
                        rules.append(rule)
            elif isinstance(node, ast.Assert):
                rule = self._analyze_assert(node, file_path, source)
                if rule:
                    rules.append(rule)

        return rules

    async def _extract_from_javascript(self, file_path: str, source: str) -> List[BusinessRule]:
        """Extract rules from JavaScript/TypeScript source using regex."""
        rules = []
        lines = source.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Check for IF statements
            if_match = re.search(r'if\s*\((.+?)\)\s*\{?', line)
            if if_match:
                condition = if_match.group(1)
                rule_type = self._classify_rule_type(condition)
                if rule_type:
                    rule = self._create_rule_from_pattern(
                        rule_type=rule_type,
                        condition=condition,
                        action=self._get_next_statement(lines, line_num),
                        file_path=file_path,
                        line_num=line_num,
                        source=line
                    )
                    if rule:
                        rules.append(rule)

            # Check for validation functions
            validate_match = re.search(r'function\s+(\w*validate\w*)\s*\(', line, re.IGNORECASE)
            if validate_match:
                func_name = validate_match.group(1)
                self._rule_counter += 1
                rules.append(BusinessRule(
                    id=f"BR-{self._rule_counter:04d}",
                    rule_type=RuleType.VALIDATION,
                    condition=f"When calling {func_name}",
                    action="Validate input according to function logic",
                    source_file=file_path,
                    source_lines=(line_num, line_num),
                    variables_involved=[func_name],
                    confidence=0.7,
                    natural_language=f"Validation function {func_name} enforces input rules"
                ))

        return rules

    async def _extract_from_dotnet(self, file_path: str, source: str) -> List[BusinessRule]:
        """Extract rules from C#/VB.NET source using regex."""
        rules = []
        lines = source.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Check for IF statements
            if_match = re.search(r'if\s*\((.+?)\)', line)
            if if_match:
                condition = if_match.group(1)
                rule_type = self._classify_rule_type(condition)
                if rule_type:
                    rule = self._create_rule_from_pattern(
                        rule_type=rule_type,
                        condition=condition,
                        action=self._get_next_statement(lines, line_num),
                        file_path=file_path,
                        line_num=line_num,
                        source=line
                    )
                    if rule:
                        rules.append(rule)

            # Check for data annotations
            annotation_match = re.search(r'\[(\w+(?:Attribute)?)\s*(?:\(([^)]*)\))?\]', line)
            if annotation_match:
                attr_name = annotation_match.group(1)
                if attr_name in ('Required', 'Range', 'StringLength', 'RegularExpression', 'Authorize'):
                    self._rule_counter += 1
                    rules.append(BusinessRule(
                        id=f"BR-{self._rule_counter:04d}",
                        rule_type=RuleType.VALIDATION if attr_name != 'Authorize' else RuleType.AUTHORIZATION,
                        condition=f"[{attr_name}] attribute applied",
                        action=f"Enforce {attr_name} constraint",
                        source_file=file_path,
                        source_lines=(line_num, line_num),
                        variables_involved=[],
                        confidence=0.9,
                        natural_language=f"{attr_name} validation applied to following member"
                    ))

        return rules

    async def _extract_from_sql(self, file_path: str, source: str) -> List[BusinessRule]:
        """Extract rules from SQL source."""
        rules = []
        lines = source.split('\n')

        for line_num, line in enumerate(lines, 1):
            upper_line = line.upper()

            # Check for WHERE clauses with business logic
            where_match = re.search(r'WHERE\s+(.+?)(?:;|$|ORDER|GROUP|HAVING)', upper_line)
            if where_match:
                condition = where_match.group(1).strip()
                if condition and len(condition) > 5:  # Non-trivial condition
                    self._rule_counter += 1
                    rules.append(BusinessRule(
                        id=f"BR-{self._rule_counter:04d}",
                        rule_type=RuleType.CONSTRAINT,
                        condition=condition,
                        action="Filter data based on condition",
                        source_file=file_path,
                        source_lines=(line_num, line_num),
                        variables_involved=self._extract_sql_columns(condition),
                        confidence=0.7,
                        natural_language=f"Data filtered where {condition}"
                    ))

            # Check for CHECK constraints
            check_match = re.search(r'CHECK\s*\((.+?)\)', upper_line)
            if check_match:
                constraint = check_match.group(1)
                self._rule_counter += 1
                rules.append(BusinessRule(
                    id=f"BR-{self._rule_counter:04d}",
                    rule_type=RuleType.CONSTRAINT,
                    condition=constraint,
                    action="Enforce data integrity constraint",
                    source_file=file_path,
                    source_lines=(line_num, line_num),
                    variables_involved=self._extract_sql_columns(constraint),
                    confidence=0.95,
                    natural_language=f"Database constraint: {constraint}"
                ))

            # Check for triggers
            trigger_match = re.search(r'CREATE\s+TRIGGER\s+(\w+)', upper_line)
            if trigger_match:
                trigger_name = trigger_match.group(1)
                self._rule_counter += 1
                rules.append(BusinessRule(
                    id=f"BR-{self._rule_counter:04d}",
                    rule_type=RuleType.WORKFLOW,
                    condition=f"Trigger {trigger_name} fires",
                    action="Execute trigger logic",
                    source_file=file_path,
                    source_lines=(line_num, line_num),
                    variables_involved=[trigger_name],
                    confidence=0.85,
                    natural_language=f"Trigger {trigger_name} enforces business logic on data changes"
                ))

        return rules

    def _analyze_if_statement(self,
                               node: ast.If,
                               file_path: str,
                               source: str) -> Optional[BusinessRule]:
        """Analyze an IF statement for business rule patterns."""

        # Get the condition as string
        try:
            condition_source = ast.unparse(node.test)
        except Exception:
            return None

        # Determine rule type
        rule_type = self._classify_rule_type(condition_source)
        if not rule_type:
            return None

        # Get the action (THEN part)
        action_lines = []
        for stmt in node.body[:3]:  # First 3 statements
            try:
                action_lines.append(ast.unparse(stmt))
            except Exception:
                pass
        action = "; ".join(action_lines)

        # Extract variables
        variables = self._extract_variables_from_ast(node)

        # Filter to domain variables if classifier available
        if self.variable_classifier:
            classification = self.variable_classifier.classify_all(variables)
            domain_vars = classification.domain_variables
            confidence = 0.7 + (len(domain_vars) / max(len(variables), 1) * 0.2)
        else:
            domain_vars = variables
            confidence = 0.6

        # Skip if no domain variables (likely not a business rule)
        if not domain_vars and self.variable_classifier:
            return None

        self._rule_counter += 1

        return BusinessRule(
            id=f"BR-{self._rule_counter:04d}",
            rule_type=rule_type,
            condition=condition_source,
            action=action,
            source_file=file_path,
            source_lines=(node.lineno, node.end_lineno or node.lineno),
            variables_involved=domain_vars or variables,
            confidence=confidence,
            natural_language=self._generate_natural_language(rule_type, condition_source, action)
        )

    def _analyze_decorator(self,
                           decorator: ast.expr,
                           func: ast.FunctionDef,
                           file_path: str) -> Optional[BusinessRule]:
        """Analyze decorator for authorization rules."""
        try:
            decorator_name = ast.unparse(decorator)
        except Exception:
            return None

        for pattern in self.authorization_regex:
            if pattern.search(decorator_name):
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

    def _analyze_derivation(self,
                             node: ast.FunctionDef,
                             file_path: str,
                             source: str) -> Optional[BusinessRule]:
        """Analyze function for derivation rules."""
        # Check if it looks like a calculated/derived value
        if not (node.name.startswith('get_') or node.name.startswith('calculate_') or
                node.name.startswith('compute_')):
            return None

        # Get return statement
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Return) and stmt.value:
                try:
                    return_expr = ast.unparse(stmt.value)
                    self._rule_counter += 1
                    return BusinessRule(
                        id=f"BR-{self._rule_counter:04d}",
                        rule_type=RuleType.DERIVATION,
                        condition=f"When {node.name} is called",
                        action=f"Return {return_expr[:100]}",
                        source_file=file_path,
                        source_lines=(node.lineno, node.end_lineno or node.lineno),
                        variables_involved=[node.name],
                        confidence=0.7,
                        natural_language=f"{node.name} derives value from: {return_expr[:50]}"
                    )
                except Exception:
                    pass
        return None

    def _analyze_assert(self,
                        node: ast.Assert,
                        file_path: str,
                        source: str) -> Optional[BusinessRule]:
        """Analyze assert statement for constraint rules."""
        try:
            test_expr = ast.unparse(node.test)
            msg = ast.unparse(node.msg) if node.msg else "Assertion violated"
        except Exception:
            return None

        self._rule_counter += 1
        return BusinessRule(
            id=f"BR-{self._rule_counter:04d}",
            rule_type=RuleType.CONSTRAINT,
            condition=test_expr,
            action=f"Assert: {msg}",
            source_file=file_path,
            source_lines=(node.lineno, node.lineno),
            variables_involved=self._extract_variables_from_ast(node),
            confidence=0.85,
            natural_language=f"Constraint: {test_expr} must be true"
        )

    def _classify_rule_type(self, condition: str) -> Optional[RuleType]:
        """Classify the type of business rule based on condition patterns."""

        for pattern in self.authorization_regex:
            if pattern.search(condition):
                return RuleType.AUTHORIZATION

        for pattern in self.validation_regex:
            if pattern.search(condition):
                return RuleType.VALIDATION

        for pattern in self.workflow_regex:
            if pattern.search(condition):
                return RuleType.WORKFLOW

        for pattern in self.calculation_regex:
            if pattern.search(condition):
                return RuleType.CALCULATION

        for pattern in self.derivation_regex:
            if pattern.search(condition):
                return RuleType.DERIVATION

        for pattern in self.constraint_regex:
            if pattern.search(condition):
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

    def _extract_sql_columns(self, sql: str) -> List[str]:
        """Extract column names from SQL expression."""
        # Simple pattern matching for identifiers
        pattern = r'\b([a-z_][a-z0-9_]*)\b'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        # Filter out SQL keywords
        keywords = {'and', 'or', 'not', 'in', 'is', 'null', 'like', 'between', 'exists',
                    'select', 'from', 'where', 'join', 'on', 'true', 'false'}
        return [m for m in matches if m.lower() not in keywords]

    def _get_next_statement(self, lines: List[str], current_line: int) -> str:
        """Get the next non-empty statement after current line."""
        for i in range(current_line, min(current_line + 3, len(lines))):
            line = lines[i].strip()
            if line and not line.startswith('//') and not line.startswith('#'):
                return line[:100]
        return ""

    def _create_rule_from_pattern(self,
                                   rule_type: RuleType,
                                   condition: str,
                                   action: str,
                                   file_path: str,
                                   line_num: int,
                                   source: str) -> Optional[BusinessRule]:
        """Create a business rule from a pattern match."""
        self._rule_counter += 1

        # Extract variables from condition
        variables = re.findall(r'\b([a-z_][a-z0-9_]*)\b', condition, re.IGNORECASE)
        keywords = {'if', 'else', 'then', 'and', 'or', 'not', 'true', 'false', 'null', 'undefined'}
        variables = [v for v in variables if v.lower() not in keywords]

        if self.variable_classifier and variables:
            classification = self.variable_classifier.classify_all(variables)
            domain_vars = classification.domain_variables
            if not domain_vars:
                return None  # Skip non-domain rules
            variables = domain_vars

        return BusinessRule(
            id=f"BR-{self._rule_counter:04d}",
            rule_type=rule_type,
            condition=condition[:200],
            action=action[:200],
            source_file=file_path,
            source_lines=(line_num, line_num),
            variables_involved=variables[:10],  # Limit variables
            confidence=0.6,
            natural_language=self._generate_natural_language(rule_type, condition, action)
        )

    def _generate_natural_language(self,
                                   rule_type: RuleType,
                                   condition: str,
                                   action: str) -> str:
        """Generate human-readable description of the rule."""
        templates = {
            RuleType.VALIDATION: "WHEN {condition}, THEN validate that {action}",
            RuleType.AUTHORIZATION: "WHEN {condition}, THEN authorize access to {action}",
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

    async def extract_all(self,
                          files: Dict[str, str]) -> RuleExtractionResult:
        """Extract rules from all files."""
        all_rules = []

        for file_path, source in files.items():
            try:
                rules = await self.extract_from_file(file_path, source)
                all_rules.extend(rules)
            except Exception as e:
                logger.warning(f"Error extracting rules from {file_path}: {e}")
                continue

        # Organize results
        by_type: Dict[RuleType, List[BusinessRule]] = {}
        by_file: Dict[str, List[BusinessRule]] = {}

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
