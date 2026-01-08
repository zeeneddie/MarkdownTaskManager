# backend/app/services/static_analysis/python_ast_extractor.py
"""
Python AST Business Rule Extractor - High-precision extraction using AST.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline (Phase 3)

Features:
- Full AST parsing for Python code (95% target confidence)
- Extracts business rules from:
  - if/elif/else statements
  - assert statements
  - try/except blocks
  - Decorator-based validations
  - Property getters/setters with validation
  - Comprehensions with conditions

Detection Categories:
- VALIDATION: Input validation, type checks, range checks
- AUTHORIZATION: Permission checks, role checks, access control
- WORKFLOW: State transitions, status changes
- CALCULATION: Business calculations, formulas
- ERROR_HANDLING: Exception handling, error propagation
- CONSTRAINT: Business constraints, invariants
- DERIVATION: Derived values, computed properties
"""

import ast
import logging
from typing import List, Dict, Optional, Tuple, Set, Any
from pathlib import Path

from .base_business_rule_extractor import BaseBusinessRuleExtractor
from .extraction_models import (
    BusinessRule,
    CodeSymbol,
    RuleType,
    Language,
    ExtractionTier,
    ExtractionMethod,
)

logger = logging.getLogger(__name__)


class PythonASTExtractor(BaseBusinessRuleExtractor):
    """
    Extracts business rules from Python source code using AST parsing.

    Tier 1 extractor with 95% target confidence.
    Uses Python's built-in ast module for accurate parsing.
    """

    SUPPORTED_EXTENSIONS = ['.py']

    # Python-specific rule type patterns (for fallback regex matching)
    PYTHON_PATTERNS: Dict[RuleType, List[str]] = {
        RuleType.VALIDATION: [
            r'if\s+not\s+\w+',
            r'if\s+\w+\s+is\s+None',
            r'if\s+len\s*\(',
            r'isinstance\s*\(',
            r'assert\s+',
            r'raise\s+ValueError',
            r'raise\s+TypeError',
        ],
        RuleType.AUTHORIZATION: [
            r'@requires_permission',
            r'@login_required',
            r'@admin_required',
            r'has_permission\s*\(',
            r'is_authenticated',
            r'check_access\s*\(',
            r'can_\w+\s*\(',
        ],
        RuleType.WORKFLOW: [
            r'\.status\s*=',
            r'\.state\s*=',
            r'transition_to\s*\(',
            r'set_status\s*\(',
            r'change_state\s*\(',
        ],
        RuleType.CALCULATION: [
            r'total\s*=',
            r'sum\s*\(',
            r'calculate_\w+',
            r'compute_\w+',
            r'price\s*[+\-*/=]',
        ],
        RuleType.ERROR_HANDLING: [
            r'try\s*:',
            r'except\s+\w+',
            r'raise\s+',
            r'finally\s*:',
        ],
        RuleType.DATA_ACCESS: [
            r'\.query\s*\(',
            r'\.filter\s*\(',
            r'\.get\s*\(',
            r'cursor\.execute',
            r'session\.query',
        ],
    }

    # Validation function name patterns
    VALIDATION_FUNCTIONS = {
        'validate', 'is_valid', 'check', 'verify', 'ensure',
        'assert', 'require', 'must_be', 'should_be',
    }

    # Authorization function name patterns
    AUTH_FUNCTIONS = {
        'can', 'has_permission', 'is_allowed', 'check_access',
        'authorize', 'is_authenticated', 'is_admin', 'has_role',
    }

    # Workflow function name patterns
    WORKFLOW_FUNCTIONS = {
        'transition', 'set_status', 'change_state', 'update_status',
        'approve', 'reject', 'submit', 'complete', 'cancel',
    }

    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return self.SUPPORTED_EXTENSIONS

    def get_language(self) -> Language:
        """Get the language this extractor handles."""
        return Language.PYTHON

    def get_rule_patterns(self) -> Dict[RuleType, List[str]]:
        """Get Python-specific rule patterns."""
        patterns = dict(self.COMMON_PATTERNS)
        for rule_type, python_patterns in self.PYTHON_PATTERNS.items():
            if rule_type in patterns:
                patterns[rule_type].extend(python_patterns)
            else:
                patterns[rule_type] = python_patterns
        return patterns

    async def _extract_symbols(self, source: str, file_path: str) -> List[CodeSymbol]:
        """
        Extract code symbols using AST parsing.

        Args:
            source: Python source code
            file_path: Path to source file

        Returns:
            List of CodeSymbol objects
        """
        symbols = []

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            logger.warning(f"Syntax error parsing {file_path}: {e}")
            return symbols

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                symbols.append(CodeSymbol(
                    name=node.name,
                    symbol_type='class',
                    line_start=node.lineno,
                    line_end=self._get_end_lineno(node),
                    docstring=ast.get_docstring(node) or '',
                    language=Language.PYTHON,
                ))

            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Determine parent class if any
                parent = ''
                for parent_node in ast.walk(tree):
                    if isinstance(parent_node, ast.ClassDef):
                        for child in ast.iter_child_nodes(parent_node):
                            if child is node:
                                parent = parent_node.name
                                break

                symbol_type = 'method' if parent else 'function'

                symbols.append(CodeSymbol(
                    name=node.name,
                    symbol_type=symbol_type,
                    line_start=node.lineno,
                    line_end=self._get_end_lineno(node),
                    docstring=ast.get_docstring(node) or '',
                    parent=parent,
                    language=Language.PYTHON,
                ))

        return symbols

    async def _extract_rules_from_source(
        self,
        source: str,
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """
        Extract business rules using AST parsing.

        Args:
            source: Python source code
            file_path: Path to source file
            symbols: Already extracted code symbols

        Returns:
            List of BusinessRule objects
        """
        rules = []

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            logger.warning(f"Syntax error parsing {file_path}: {e}")
            return rules

        # Split source into lines for code snippet extraction
        source_lines = source.split('\n')

        # Extract rules from different AST node types
        rules.extend(self._extract_if_rules(tree, source_lines, file_path, symbols))
        rules.extend(self._extract_assert_rules(tree, source_lines, file_path, symbols))
        rules.extend(self._extract_try_except_rules(tree, source_lines, file_path, symbols))
        rules.extend(self._extract_decorator_rules(tree, source_lines, file_path, symbols))
        rules.extend(self._extract_comprehension_rules(tree, source_lines, file_path, symbols))

        return rules

    def _extract_if_rules(
        self,
        tree: ast.AST,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from if statements."""
        rules = []

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                condition = self._unparse_condition(node.test)
                action = self._summarize_body(node.body)

                # Classify rule type based on condition
                rule_type = self._classify_condition(node.test, condition)
                if not rule_type:
                    rule_type = self._classify_rule_type(condition)
                if not rule_type:
                    rule_type = RuleType.BRANCHING  # Default for if statements

                # Extract variables
                variables = self._extract_variables_from_ast(node.test)

                # Get code snippet
                start_line = node.lineno
                end_line = self._get_end_lineno(node)
                code_snippet = '\n'.join(source_lines[start_line - 1:min(end_line, start_line + 5)])

                # Find parent context
                parent_class, parent_function = self._find_parent_symbol(start_line, symbols)

                # Calculate confidence (AST-based = high confidence)
                confidence = self._calculate_ast_confidence(
                    rule_type, variables, condition, action
                )

                rules.append(BusinessRule(
                    id=self._generate_rule_id(),
                    rule_type=rule_type,
                    condition=condition,
                    action=action,
                    source_file=file_path,
                    source_lines=(start_line, end_line),
                    confidence=confidence,
                    natural_language=self._generate_natural_language(rule_type, condition, action),
                    variables_involved=variables,
                    related_entities=self._extract_entities(condition, variables),
                    language=Language.PYTHON,
                    extraction_method=ExtractionMethod.AST,
                    extraction_tier=self.extraction_tier,
                    code_snippet=code_snippet,
                    parent_function=parent_function,
                    parent_class=parent_class,
                ))

        return rules

    def _extract_assert_rules(
        self,
        tree: ast.AST,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from assert statements."""
        rules = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                condition = self._unparse_condition(node.test)

                # Assert messages often describe the business rule
                message = ''
                if node.msg:
                    if isinstance(node.msg, ast.Constant):
                        message = str(node.msg.value)
                    else:
                        message = self._unparse_condition(node.msg)

                action = message if message else f"Assert: {condition}"
                variables = self._extract_variables_from_ast(node.test)

                start_line = node.lineno
                end_line = self._get_end_lineno(node)
                code_snippet = source_lines[start_line - 1] if start_line <= len(source_lines) else ''

                parent_class, parent_function = self._find_parent_symbol(start_line, symbols)

                # Asserts are typically constraints/validation
                rule_type = RuleType.CONSTRAINT

                confidence = self._calculate_ast_confidence(
                    rule_type, variables, condition, action, is_assert=True
                )

                rules.append(BusinessRule(
                    id=self._generate_rule_id(),
                    rule_type=rule_type,
                    condition=condition,
                    action=action,
                    source_file=file_path,
                    source_lines=(start_line, end_line),
                    confidence=confidence,
                    natural_language=f"CONSTRAINT: {message}" if message else f"ASSERT {condition}",
                    variables_involved=variables,
                    related_entities=self._extract_entities(condition, variables),
                    language=Language.PYTHON,
                    extraction_method=ExtractionMethod.AST,
                    extraction_tier=self.extraction_tier,
                    code_snippet=code_snippet,
                    parent_function=parent_function,
                    parent_class=parent_class,
                ))

        return rules

    def _extract_try_except_rules(
        self,
        tree: ast.AST,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from try-except blocks."""
        rules = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    # Get exception type
                    if handler.type:
                        if isinstance(handler.type, ast.Name):
                            exception_type = handler.type.id
                        elif isinstance(handler.type, ast.Tuple):
                            exception_type = ', '.join(
                                self._unparse_condition(e) for e in handler.type.elts
                            )
                        else:
                            exception_type = self._unparse_condition(handler.type)
                    else:
                        exception_type = 'Exception'

                    condition = f"Catch {exception_type}"
                    action = self._summarize_body(handler.body)
                    variables = [handler.name] if handler.name else []

                    start_line = handler.lineno
                    end_line = self._get_end_lineno(handler)
                    code_snippet = '\n'.join(source_lines[start_line - 1:min(end_line, start_line + 3)])

                    parent_class, parent_function = self._find_parent_symbol(start_line, symbols)

                    confidence = self._calculate_ast_confidence(
                        RuleType.ERROR_HANDLING, variables, condition, action
                    )

                    rules.append(BusinessRule(
                        id=self._generate_rule_id(),
                        rule_type=RuleType.ERROR_HANDLING,
                        condition=condition,
                        action=action,
                        source_file=file_path,
                        source_lines=(start_line, end_line),
                        confidence=confidence,
                        natural_language=f"WHEN {exception_type} occurs, THEN {action}",
                        variables_involved=variables,
                        language=Language.PYTHON,
                        extraction_method=ExtractionMethod.AST,
                        extraction_tier=self.extraction_tier,
                        code_snippet=code_snippet,
                        parent_function=parent_function,
                        parent_class=parent_class,
                    ))

        return rules

    def _extract_decorator_rules(
        self,
        tree: ast.AST,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from decorators (auth, validation, etc.)."""
        rules = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    decorator_name = self._get_decorator_name(decorator)

                    # Check for authorization decorators
                    if any(auth in decorator_name.lower() for auth in
                           ['permission', 'login', 'auth', 'admin', 'role', 'require']):

                        args = self._get_decorator_args(decorator)
                        condition = f"@{decorator_name}({', '.join(args)})" if args else f"@{decorator_name}"
                        action = f"Allow access to {node.name}"

                        start_line = node.lineno
                        end_line = self._get_end_lineno(node)

                        parent_class, parent_function = self._find_parent_symbol(start_line, symbols)

                        rules.append(BusinessRule(
                            id=self._generate_rule_id(),
                            rule_type=RuleType.AUTHORIZATION,
                            condition=condition,
                            action=action,
                            source_file=file_path,
                            source_lines=(start_line, start_line),
                            confidence=0.90,  # High confidence for explicit decorators
                            natural_language=f"REQUIRE {decorator_name} to access {node.name}",
                            variables_involved=args,
                            language=Language.PYTHON,
                            extraction_method=ExtractionMethod.AST,
                            extraction_tier=self.extraction_tier,
                            parent_function=node.name,
                            parent_class=parent_class,
                        ))

                    # Check for validation decorators
                    elif any(val in decorator_name.lower() for val in
                             ['valid', 'check', 'schema', 'verify']):

                        args = self._get_decorator_args(decorator)
                        condition = f"@{decorator_name}({', '.join(args)})" if args else f"@{decorator_name}"
                        action = f"Validate input for {node.name}"

                        start_line = node.lineno

                        parent_class, parent_function = self._find_parent_symbol(start_line, symbols)

                        rules.append(BusinessRule(
                            id=self._generate_rule_id(),
                            rule_type=RuleType.VALIDATION,
                            condition=condition,
                            action=action,
                            source_file=file_path,
                            source_lines=(start_line, start_line),
                            confidence=0.88,
                            natural_language=f"VALIDATE input using {decorator_name} for {node.name}",
                            variables_involved=args,
                            language=Language.PYTHON,
                            extraction_method=ExtractionMethod.AST,
                            extraction_tier=self.extraction_tier,
                            parent_function=node.name,
                            parent_class=parent_class,
                        ))

        return rules

    def _extract_comprehension_rules(
        self,
        tree: ast.AST,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from list/dict/set comprehensions with conditions."""
        rules = []

        for node in ast.walk(tree):
            # List, Set, Dict comprehensions and Generator expressions
            if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                for generator in node.generators:
                    for if_clause in generator.ifs:
                        condition = self._unparse_condition(if_clause)

                        # Determine what's being filtered
                        if isinstance(generator.iter, ast.Name):
                            source_name = generator.iter.id
                        else:
                            source_name = self._unparse_condition(generator.iter)

                        action = f"Filter {source_name} where {condition}"
                        variables = self._extract_variables_from_ast(if_clause)

                        start_line = node.lineno
                        end_line = self._get_end_lineno(node)
                        code_snippet = source_lines[start_line - 1] if start_line <= len(source_lines) else ''

                        parent_class, parent_function = self._find_parent_symbol(start_line, symbols)

                        # Determine rule type from filter condition
                        rule_type = self._classify_condition(if_clause, condition)
                        if not rule_type:
                            rule_type = RuleType.DERIVATION

                        rules.append(BusinessRule(
                            id=self._generate_rule_id(),
                            rule_type=rule_type,
                            condition=condition,
                            action=action,
                            source_file=file_path,
                            source_lines=(start_line, end_line),
                            confidence=0.82,  # Good confidence for explicit filter conditions
                            natural_language=f"FILTER {source_name} WHERE {condition}",
                            variables_involved=variables,
                            language=Language.PYTHON,
                            extraction_method=ExtractionMethod.AST,
                            extraction_tier=self.extraction_tier,
                            code_snippet=code_snippet,
                            parent_function=parent_function,
                            parent_class=parent_class,
                        ))

        return rules

    def _unparse_condition(self, node: ast.AST) -> str:
        """Convert AST node back to source code string."""
        try:
            return ast.unparse(node)
        except (AttributeError, TypeError):
            # Fallback for older Python versions
            return self._manual_unparse(node)

    def _manual_unparse(self, node: ast.AST) -> str:
        """Manual unparsing for older Python versions."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Compare):
            left = self._manual_unparse(node.left)
            ops = [self._op_to_str(op) for op in node.ops]
            comparators = [self._manual_unparse(c) for c in node.comparators]
            result = left
            for op, comp in zip(ops, comparators):
                result += f" {op} {comp}"
            return result
        elif isinstance(node, ast.BoolOp):
            op = ' and ' if isinstance(node.op, ast.And) else ' or '
            return op.join(self._manual_unparse(v) for v in node.values)
        elif isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.Not):
                return f"not {self._manual_unparse(node.operand)}"
            return f"{self._op_to_str(node.op)}{self._manual_unparse(node.operand)}"
        elif isinstance(node, ast.Call):
            func = self._manual_unparse(node.func)
            args = [self._manual_unparse(a) for a in node.args]
            return f"{func}({', '.join(args)})"
        elif isinstance(node, ast.Attribute):
            return f"{self._manual_unparse(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._manual_unparse(node.value)}[{self._manual_unparse(node.slice)}]"
        else:
            return str(type(node).__name__)

    def _op_to_str(self, op: ast.AST) -> str:
        """Convert AST operator to string."""
        op_map = {
            ast.Eq: '==', ast.NotEq: '!=', ast.Lt: '<', ast.LtE: '<=',
            ast.Gt: '>', ast.GtE: '>=', ast.Is: 'is', ast.IsNot: 'is not',
            ast.In: 'in', ast.NotIn: 'not in', ast.Add: '+', ast.Sub: '-',
            ast.Mult: '*', ast.Div: '/', ast.Mod: '%', ast.Pow: '**',
            ast.And: 'and', ast.Or: 'or', ast.Not: 'not',
        }
        return op_map.get(type(op), str(type(op).__name__))

    def _summarize_body(self, body: List[ast.AST]) -> str:
        """Create a summary of a code body."""
        if not body:
            return "empty body"

        summaries = []
        for node in body[:3]:  # Only summarize first 3 statements
            if isinstance(node, ast.Return):
                if node.value:
                    summaries.append(f"return {self._unparse_condition(node.value)}")
                else:
                    summaries.append("return")
            elif isinstance(node, ast.Raise):
                if node.exc:
                    summaries.append(f"raise {self._unparse_condition(node.exc)}")
                else:
                    summaries.append("raise")
            elif isinstance(node, ast.Assign):
                targets = ', '.join(self._unparse_condition(t) for t in node.targets)
                summaries.append(f"{targets} = ...")
            elif isinstance(node, ast.Expr):
                if isinstance(node.value, ast.Call):
                    summaries.append(f"call {self._unparse_condition(node.value.func)}()")
            elif isinstance(node, ast.If):
                summaries.append("conditional logic")
            elif isinstance(node, ast.Pass):
                summaries.append("pass")

        return '; '.join(summaries) if summaries else "complex logic"

    def _classify_condition(self, node: ast.AST, condition_text: str) -> Optional[RuleType]:
        """Classify rule type based on AST condition node."""
        # Check for authorization patterns
        if isinstance(node, ast.Call):
            func_name = self._get_call_name(node).lower()
            if any(auth in func_name for auth in self.AUTH_FUNCTIONS):
                return RuleType.AUTHORIZATION
            if any(val in func_name for val in self.VALIDATION_FUNCTIONS):
                return RuleType.VALIDATION
            if any(wf in func_name for wf in self.WORKFLOW_FUNCTIONS):
                return RuleType.WORKFLOW

        # Check for common patterns in condition text
        condition_lower = condition_text.lower()

        if 'is none' in condition_lower or 'is not none' in condition_lower:
            return RuleType.VALIDATION
        if 'isinstance(' in condition_lower:
            return RuleType.VALIDATION
        if '.status' in condition_lower or '.state' in condition_lower:
            return RuleType.WORKFLOW
        if any(word in condition_lower for word in ['permission', 'authorized', 'allowed', 'access']):
            return RuleType.AUTHORIZATION
        if any(word in condition_lower for word in ['len(', 'count', 'size']):
            return RuleType.THRESHOLD

        return None

    def _get_call_name(self, node: ast.Call) -> str:
        """Get the function name from a Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    def _extract_variables_from_ast(self, node: ast.AST) -> List[str]:
        """Extract variable names from an AST node."""
        variables = []
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                variables.append(child.id)
            elif isinstance(child, ast.Attribute):
                variables.append(child.attr)
        return list(set(variables))

    def _get_end_lineno(self, node: ast.AST) -> int:
        """Get the end line number of an AST node."""
        if hasattr(node, 'end_lineno') and node.end_lineno:
            return node.end_lineno
        # Fallback: estimate based on child nodes
        max_line = getattr(node, 'lineno', 1)
        for child in ast.walk(node):
            child_line = getattr(child, 'lineno', 0)
            if child_line > max_line:
                max_line = child_line
        return max_line

    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Get the name of a decorator."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return ""

    def _get_decorator_args(self, decorator: ast.AST) -> List[str]:
        """Get arguments from a decorator call."""
        if isinstance(decorator, ast.Call):
            args = []
            for arg in decorator.args:
                if isinstance(arg, ast.Constant):
                    args.append(str(arg.value))
                elif isinstance(arg, ast.Name):
                    args.append(arg.id)
            return args
        return []

    def _calculate_ast_confidence(
        self,
        rule_type: RuleType,
        variables: List[str],
        condition: str,
        action: str,
        is_assert: bool = False,
    ) -> float:
        """
        Calculate confidence score for AST-extracted rules.

        AST extraction is Tier 1 with high base confidence (0.85).
        """
        # AST gives us higher base confidence
        base_confidence = 0.85

        # Boost for explicit rule types
        type_boost = {
            RuleType.AUTHORIZATION: 0.08,
            RuleType.VALIDATION: 0.06,
            RuleType.CONSTRAINT: 0.06,
            RuleType.WORKFLOW: 0.05,
            RuleType.ERROR_HANDLING: 0.04,
        }
        base_confidence += type_boost.get(rule_type, 0.0)

        # Boost for clear variable names
        domain_indicators = ['id', 'name', 'status', 'date', 'amount', 'user', 'role', 'permission']
        domain_vars = [v for v in variables if any(ind in v.lower() for ind in domain_indicators)]
        base_confidence += min(len(domain_vars) * 0.02, 0.06)

        # Boost for asserts (explicit business constraints)
        if is_assert:
            base_confidence += 0.05

        # Slight boost for longer, more complex conditions (more context)
        if len(condition) > 30:
            base_confidence += 0.02

        return min(base_confidence, 0.95)

    async def extract_from_file(
        self,
        file_path: str,
        source: Optional[str] = None,
    ):
        """
        Override to set AST extraction method.
        """
        result = await super().extract_from_file(file_path, source)
        result.extraction_method = ExtractionMethod.AST
        return result


# Convenience function
async def extract_python_rules(
    file_path: str,
    extraction_tier: ExtractionTier = ExtractionTier.STANDARD,
) -> List[BusinessRule]:
    """
    Extract business rules from a Python file.

    Args:
        file_path: Path to Python file
        extraction_tier: Customer tier

    Returns:
        List of extracted BusinessRule objects
    """
    extractor = PythonASTExtractor(extraction_tier=extraction_tier)
    result = await extractor.extract_from_file(file_path)
    return result.business_rules
