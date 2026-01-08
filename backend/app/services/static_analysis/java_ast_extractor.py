# backend/app/services/static_analysis/java_ast_extractor.py
"""
Java AST-Based Business Rule Extractor.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline - Phase 3

Features:
- Spring/Jakarta annotations (@Valid, @NotNull, @PreAuthorize, @Secured)
- If-statement condition extraction
- Switch statement pattern detection
- Try-catch exception handling
- Stream API operations (filter, map, collect)
- Optional handling patterns
- Guard clause detection
- Bean Validation annotations

Confidence Range: 80-95% (AST-based)
"""

import re
import logging
from typing import List, Optional, Tuple
from pathlib import Path

from .base_business_rule_extractor import BaseBusinessRuleExtractor
from .extraction_models import (
    BusinessRule,
    CodeSymbol,
    NFRIndicator,
    ExtractionResult,
    RuleType,
    Language,
    ExtractionMethod,
    ExtractionTier,
)

logger = logging.getLogger(__name__)


class JavaASTExtractor(BaseBusinessRuleExtractor):
    """
    Java business rule extractor using regex-based AST-like analysis.

    Targets Spring/Jakarta EE patterns common in enterprise Java applications:
    - Bean Validation annotations
    - Spring Security annotations
    - Conditional logic in services
    - Stream API filtering
    """

    # Spring/Jakarta annotations indicating business rules
    ANNOTATION_PATTERNS = {
        # Bean Validation
        'validation': [
            (re.compile(r'@NotNull\s*(?:\([^)]*\))?\s*(?:private|public|protected)?\s*\w+\s+(\w+)'), 'VALIDATION', 0.92),
            (re.compile(r'@NotEmpty\s*(?:\([^)]*\))?\s*(?:private|public|protected)?\s*\w+\s+(\w+)'), 'VALIDATION', 0.92),
            (re.compile(r'@NotBlank\s*(?:\([^)]*\))?\s*(?:private|public|protected)?\s*\w+\s+(\w+)'), 'VALIDATION', 0.92),
            (re.compile(r'@Size\s*\(([^)]+)\)\s*(?:private|public|protected)?\s*\w+\s+(\w+)'), 'VALIDATION', 0.90),
            (re.compile(r'@Min\s*\(([^)]+)\)\s*(?:private|public|protected)?\s*\w+\s+(\w+)'), 'THRESHOLD', 0.90),
            (re.compile(r'@Max\s*\(([^)]+)\)\s*(?:private|public|protected)?\s*\w+\s+(\w+)'), 'THRESHOLD', 0.90),
            (re.compile(r'@Pattern\s*\(([^)]+)\)\s*(?:private|public|protected)?\s*\w+\s+(\w+)'), 'VALIDATION', 0.88),
            (re.compile(r'@Email\s*(?:\([^)]*\))?\s*(?:private|public|protected)?\s*\w+\s+(\w+)'), 'VALIDATION', 0.90),
            (re.compile(r'@Valid\s+(?:private|public|protected)?\s*(\w+)\s+(\w+)'), 'VALIDATION', 0.88),
            (re.compile(r'@Validated\s+(?:private|public|protected)?\s*(\w+)\s+(\w+)'), 'VALIDATION', 0.88),
        ],
        # Spring Security
        'authorization': [
            # Match double-quoted strings that may contain single quotes inside
            (re.compile(r'@PreAuthorize\s*\(\s*"([^"]+)"\s*\)'), 'AUTHORIZATION', 0.95),
            (re.compile(r'@PostAuthorize\s*\(\s*"([^"]+)"\s*\)'), 'AUTHORIZATION', 0.95),
            (re.compile(r'@Secured\s*\(\s*\{?\s*"([^"]+)"\s*\}?\s*\)'), 'AUTHORIZATION', 0.93),
            (re.compile(r'@RolesAllowed\s*\(\s*\{?\s*"([^"]+)"\s*\}?\s*\)'), 'AUTHORIZATION', 0.93),
            (re.compile(r'@PermitAll'), 'AUTHORIZATION', 0.85),
            (re.compile(r'@DenyAll'), 'AUTHORIZATION', 0.85),
        ],
        # Transactional
        'workflow': [
            (re.compile(r'@Transactional\s*(?:\([^)]*\))?'), 'WORKFLOW', 0.85),
            (re.compile(r'@Async'), 'WORKFLOW', 0.80),
            (re.compile(r'@Scheduled\s*\(([^)]+)\)'), 'SCHEDULING', 0.90),
            (re.compile(r'@EventListener'), 'WORKFLOW', 0.82),
        ],
    }

    # If-statement patterns
    IF_PATTERNS = [
        # Standard if with condition
        (re.compile(
            r'if\s*\(\s*([^{]+?)\s*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
            re.DOTALL
        ), 0.85),
        # If with throw
        (re.compile(
            r'if\s*\(\s*([^)]+)\s*\)\s*\{?\s*throw\s+new\s+(\w+Exception)',
            re.MULTILINE
        ), 0.90),
        # Ternary operator
        (re.compile(
            r'(\w+)\s*=\s*([^?]+)\s*\?\s*([^:]+)\s*:\s*([^;]+);',
            re.MULTILINE
        ), 0.80),
    ]

    # Switch statement pattern - match identifier, method call, or chained expression
    SWITCH_PATTERN = re.compile(
        r'switch\s*\(\s*(\w+(?:\.\w+(?:\(\))?)*)\s*\)\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
        re.DOTALL
    )
    CASE_PATTERN = re.compile(r'case\s+(\w+|"[^"]+"|\'[^\']+\')\s*:([^:}]+?)(?=case\s|default\s*:|$)', re.DOTALL)

    # Try-catch pattern
    TRY_CATCH_PATTERN = re.compile(
        r'try\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}\s*catch\s*\(\s*(\w+)\s+\w+\s*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
        re.DOTALL
    )

    # Stream API patterns
    STREAM_PATTERNS = [
        (re.compile(r'\.filter\s*\(\s*(\w+)\s*->\s*([^)]+)\)'), 'CONSTRAINT', 0.85),
        (re.compile(r'\.filter\s*\(\s*([^)]+)\s*\)'), 'CONSTRAINT', 0.82),
        (re.compile(r'\.findFirst\s*\(\s*\)'), 'DATA_ACCESS', 0.80),
        (re.compile(r'\.findAny\s*\(\s*\)'), 'DATA_ACCESS', 0.80),
        (re.compile(r'\.anyMatch\s*\(\s*([^)]+)\s*\)'), 'VALIDATION', 0.82),
        (re.compile(r'\.allMatch\s*\(\s*([^)]+)\s*\)'), 'VALIDATION', 0.82),
        (re.compile(r'\.noneMatch\s*\(\s*([^)]+)\s*\)'), 'VALIDATION', 0.82),
    ]

    # Optional handling patterns
    OPTIONAL_PATTERNS = [
        (re.compile(r'\.orElseThrow\s*\(\s*\(\s*\)\s*->\s*new\s+(\w+Exception)\s*\([^)]*\)\s*\)'), 'ERROR_HANDLING', 0.88),
        (re.compile(r'\.orElseThrow\s*\(\s*(\w+Exception)::new\s*\)'), 'ERROR_HANDLING', 0.88),
        (re.compile(r'\.orElse\s*\(\s*([^)]+)\s*\)'), 'DERIVATION', 0.80),
        (re.compile(r'\.ifPresent\s*\(\s*([^)]+)\s*\)'), 'WORKFLOW', 0.78),
    ]

    # Guard clause patterns (early return)
    GUARD_PATTERNS = [
        (re.compile(r'if\s*\(\s*(\w+)\s*==\s*null\s*\)\s*\{?\s*throw\s+new\s+(\w+)'), 'VALIDATION', 0.92),
        (re.compile(r'if\s*\(\s*!(\w+)\s*\)\s*\{?\s*throw\s+new\s+(\w+)'), 'VALIDATION', 0.90),
        (re.compile(r'Objects\.requireNonNull\s*\(\s*(\w+)'), 'VALIDATION', 0.95),
        (re.compile(r'Assert\.notNull\s*\(\s*(\w+)'), 'VALIDATION', 0.93),
        (re.compile(r'Assert\.hasText\s*\(\s*(\w+)'), 'VALIDATION', 0.93),
        (re.compile(r'Assert\.isTrue\s*\(\s*([^,]+)'), 'VALIDATION', 0.93),
    ]

    # Class/method patterns for symbol extraction
    CLASS_PATTERN = re.compile(
        r'(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w\s,]+))?\s*\{',
        re.MULTILINE
    )
    METHOD_PATTERN = re.compile(
        r'(?:@\w+(?:\([^)]*\))?\s*)*(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w\s,]+)?\s*\{',
        re.MULTILINE
    )
    INTERFACE_PATTERN = re.compile(
        r'(?:public|private|protected)?\s*interface\s+(\w+)(?:\s+extends\s+([\w\s,]+))?\s*\{',
        re.MULTILINE
    )

    def get_supported_extensions(self) -> List[str]:
        """Return supported file extensions."""
        return ['.java']

    def get_language(self) -> Language:
        """Return the language this extractor handles."""
        return Language.JAVA

    async def _extract_symbols(self, source: str, file_path: str) -> List[CodeSymbol]:
        """
        Extract code symbols (classes, methods, interfaces) from Java source.

        Args:
            source: Java source code
            file_path: Path to the source file

        Returns:
            List of CodeSymbol objects
        """
        symbols = []
        lines = source.split('\n')

        # Extract classes
        for match in self.CLASS_PATTERN.finditer(source):
            class_name = match.group(1)
            line_num = source[:match.start()].count('\n') + 1

            # Find class end (matching braces)
            end_line = self._find_block_end(source, match.end() - 1)

            symbols.append(CodeSymbol(
                name=class_name,
                symbol_type='class',
                line_start=line_num,
                line_end=end_line,
                docstring=self._extract_javadoc(source, match.start()),
                parent='',
                language=Language.JAVA,
            ))

        # Extract interfaces
        for match in self.INTERFACE_PATTERN.finditer(source):
            interface_name = match.group(1)
            line_num = source[:match.start()].count('\n') + 1
            end_line = self._find_block_end(source, match.end() - 1)

            symbols.append(CodeSymbol(
                name=interface_name,
                symbol_type='interface',
                line_start=line_num,
                line_end=end_line,
                docstring=self._extract_javadoc(source, match.start()),
                parent='',
                language=Language.JAVA,
            ))

        # Extract methods
        for match in self.METHOD_PATTERN.finditer(source):
            return_type = match.group(1)
            method_name = match.group(2)
            params = match.group(3)
            line_num = source[:match.start()].count('\n') + 1
            end_line = self._find_block_end(source, match.end() - 1)

            # Find parent class
            parent_class = self._find_parent_class(source, match.start())

            symbols.append(CodeSymbol(
                name=method_name,
                symbol_type='method',
                line_start=line_num,
                line_end=end_line,
                docstring=self._extract_javadoc(source, match.start()),
                parent=parent_class,
                language=Language.JAVA,
            ))

        return symbols

    async def _extract_rules_from_source(
        self,
        source: str,
        file_path: str,
        symbols: List[CodeSymbol],
    ) -> List[BusinessRule]:
        """
        Extract business rules from Java source code.

        Args:
            source: Java source code
            file_path: Path to the source file
            symbols: Previously extracted symbols

        Returns:
            List of BusinessRule objects
        """
        rules = []
        lines = source.split('\n')

        # Extract rules from annotations
        rules.extend(self._extract_annotation_rules(source, file_path, lines))

        # Extract rules from if-statements
        rules.extend(self._extract_if_rules(source, file_path, lines))

        # Extract rules from switch statements
        rules.extend(self._extract_switch_rules(source, file_path, lines))

        # Extract rules from try-catch blocks
        rules.extend(self._extract_try_catch_rules(source, file_path, lines))

        # Extract rules from Stream API
        rules.extend(self._extract_stream_rules(source, file_path, lines))

        # Extract rules from Optional handling
        rules.extend(self._extract_optional_rules(source, file_path, lines))

        # Extract rules from guard clauses
        rules.extend(self._extract_guard_rules(source, file_path, lines))

        return rules

    def _extract_annotation_rules(
        self, source: str, file_path: str, lines: List[str]
    ) -> List[BusinessRule]:
        """Extract rules from Java annotations."""
        rules = []

        for category, patterns in self.ANNOTATION_PATTERNS.items():
            for pattern, rule_type_str, confidence in patterns:
                for match in pattern.finditer(source):
                    line_num = source[:match.start()].count('\n') + 1

                    # Get the full annotation and target
                    annotation_text = match.group(0)
                    params = match.group(1) if (match.lastindex or 0) >= 1 else ""

                    rule_type = RuleType(rule_type_str.lower())

                    # Generate natural language
                    nl = self._annotation_to_natural_language(
                        annotation_text, rule_type, params
                    )

                    rule = BusinessRule(
                        id=f"BR-{len(rules) + 1:03d}",
                        rule_type=rule_type,
                        condition=annotation_text.split('(')[0].strip(),
                        action=params if params else annotation_text,
                        source_file=file_path,
                        source_lines=(line_num, line_num + annotation_text.count('\n')),
                        confidence=confidence,
                        natural_language=nl,
                        language=Language.JAVA,
                        extraction_method=ExtractionMethod.AST,
                        extraction_tier=self.extraction_tier,
                        code_snippet=annotation_text,
                        parent_function=self._find_parent_method(source, match.start()),
                        parent_class=self._find_parent_class(source, match.start()),
                    )
                    rules.append(rule)

        return rules

    def _extract_if_rules(
        self, source: str, file_path: str, lines: List[str]
    ) -> List[BusinessRule]:
        """Extract rules from if-statements."""
        rules = []

        for pattern, confidence in self.IF_PATTERNS:
            for match in pattern.finditer(source):
                line_num = source[:match.start()].count('\n') + 1
                condition = match.group(1).strip()

                if len(match.groups()) >= 2:
                    action = match.group(2).strip()[:100]
                else:
                    action = "Execute conditional block"

                # Classify rule type
                rule_type = self._classify_rule_type(condition + " " + action)
                if not rule_type:
                    rule_type = RuleType.BRANCHING  # Default for if statements

                # Skip trivial conditions
                if len(condition) < 5 or condition in ['true', 'false']:
                    continue

                rule = BusinessRule(
                    id=f"BR-{len(rules) + 1:03d}",
                    rule_type=rule_type,
                    condition=condition,
                    action=action,
                    source_file=file_path,
                    source_lines=(line_num, line_num + match.group(0).count('\n')),
                    confidence=confidence,
                    natural_language=self._generate_natural_language(rule_type, condition, action),
                    language=Language.JAVA,
                    extraction_method=ExtractionMethod.AST,
                    extraction_tier=self.extraction_tier,
                    code_snippet=match.group(0)[:200],
                    parent_function=self._find_parent_method(source, match.start()),
                    parent_class=self._find_parent_class(source, match.start()),
                    variables_involved=self._extract_variables(condition),
                )
                rules.append(rule)

        return rules

    def _extract_switch_rules(
        self, source: str, file_path: str, lines: List[str]
    ) -> List[BusinessRule]:
        """Extract rules from switch statements."""
        rules = []

        for match in self.SWITCH_PATTERN.finditer(source):
            switch_var = match.group(1)
            switch_body = match.group(2)
            line_num = source[:match.start()].count('\n') + 1

            # Extract each case
            for case_match in self.CASE_PATTERN.finditer(switch_body):
                case_value = case_match.group(1)
                case_body = case_match.group(2).strip()

                rule = BusinessRule(
                    id=f"BR-{len(rules) + 1:03d}",
                    rule_type=RuleType.BRANCHING,
                    condition=f"{switch_var} == {case_value}",
                    action=case_body[:100] if case_body else f"Handle case {case_value}",
                    source_file=file_path,
                    source_lines=(line_num, line_num + case_match.group(0).count('\n')),
                    confidence=0.85,
                    natural_language=f"When {switch_var} equals {case_value}, execute case logic",
                    language=Language.JAVA,
                    extraction_method=ExtractionMethod.AST,
                    extraction_tier=self.extraction_tier,
                    code_snippet=f"case {case_value}: {case_body[:50]}",
                    parent_function=self._find_parent_method(source, match.start()),
                    parent_class=self._find_parent_class(source, match.start()),
                )
                rules.append(rule)

        return rules

    def _extract_try_catch_rules(
        self, source: str, file_path: str, lines: List[str]
    ) -> List[BusinessRule]:
        """Extract rules from try-catch blocks."""
        rules = []

        for match in self.TRY_CATCH_PATTERN.finditer(source):
            try_body = match.group(1).strip()
            exception_type = match.group(2)
            catch_body = match.group(3).strip()
            line_num = source[:match.start()].count('\n') + 1

            rule = BusinessRule(
                id=f"BR-{len(rules) + 1:03d}",
                rule_type=RuleType.ERROR_HANDLING,
                condition=f"When {exception_type} occurs",
                action=catch_body[:100] if catch_body else f"Handle {exception_type}",
                source_file=file_path,
                source_lines=(line_num, line_num + match.group(0).count('\n')),
                confidence=0.85,
                natural_language=f"Handle {exception_type} exception in protected code block",
                language=Language.JAVA,
                extraction_method=ExtractionMethod.AST,
                extraction_tier=self.extraction_tier,
                code_snippet=f"try {{ ... }} catch ({exception_type}) {{ {catch_body[:50]} }}",
                parent_function=self._find_parent_method(source, match.start()),
                parent_class=self._find_parent_class(source, match.start()),
            )
            rules.append(rule)

        return rules

    def _extract_stream_rules(
        self, source: str, file_path: str, lines: List[str]
    ) -> List[BusinessRule]:
        """Extract rules from Stream API operations."""
        rules = []

        for pattern, rule_type_str, confidence in self.STREAM_PATTERNS:
            for match in pattern.finditer(source):
                line_num = source[:match.start()].count('\n') + 1
                full_match = match.group(0)

                # Get filter condition if available
                if (match.lastindex or 0) >= 1:
                    condition = match.group(1)
                    if (match.lastindex or 0) >= 2:
                        condition = f"{match.group(1)} -> {match.group(2)}"
                else:
                    condition = full_match

                rule_type = RuleType(rule_type_str.lower())

                rule = BusinessRule(
                    id=f"BR-{len(rules) + 1:03d}",
                    rule_type=rule_type,
                    condition=condition,
                    action=f"Stream {full_match.split('(')[0].strip('.')}",
                    source_file=file_path,
                    source_lines=(line_num, line_num),
                    confidence=confidence,
                    natural_language=self._stream_to_natural_language(full_match, condition),
                    language=Language.JAVA,
                    extraction_method=ExtractionMethod.AST,
                    extraction_tier=self.extraction_tier,
                    code_snippet=full_match,
                    parent_function=self._find_parent_method(source, match.start()),
                    parent_class=self._find_parent_class(source, match.start()),
                )
                rules.append(rule)

        return rules

    def _extract_optional_rules(
        self, source: str, file_path: str, lines: List[str]
    ) -> List[BusinessRule]:
        """Extract rules from Optional handling patterns."""
        rules = []

        for pattern, rule_type_str, confidence in self.OPTIONAL_PATTERNS:
            for match in pattern.finditer(source):
                line_num = source[:match.start()].count('\n') + 1
                full_match = match.group(0)

                rule_type = RuleType(rule_type_str.lower())

                if (match.lastindex or 0) >= 1:
                    action = match.group(1)
                else:
                    action = full_match

                rule = BusinessRule(
                    id=f"BR-{len(rules) + 1:03d}",
                    rule_type=rule_type,
                    condition="Optional value handling",
                    action=action,
                    source_file=file_path,
                    source_lines=(line_num, line_num),
                    confidence=confidence,
                    natural_language=self._optional_to_natural_language(full_match, action),
                    language=Language.JAVA,
                    extraction_method=ExtractionMethod.AST,
                    extraction_tier=self.extraction_tier,
                    code_snippet=full_match,
                    parent_function=self._find_parent_method(source, match.start()),
                    parent_class=self._find_parent_class(source, match.start()),
                )
                rules.append(rule)

        return rules

    def _extract_guard_rules(
        self, source: str, file_path: str, lines: List[str]
    ) -> List[BusinessRule]:
        """Extract rules from guard clauses."""
        rules = []

        for pattern, rule_type_str, confidence in self.GUARD_PATTERNS:
            for match in pattern.finditer(source):
                line_num = source[:match.start()].count('\n') + 1
                full_match = match.group(0)

                variable = match.group(1) if (match.lastindex or 0) >= 1 else "value"
                exception = match.group(2) if (match.lastindex or 0) >= 2 else "Exception"

                rule_type = RuleType(rule_type_str.lower())

                rule = BusinessRule(
                    id=f"BR-{len(rules) + 1:03d}",
                    rule_type=rule_type,
                    condition=f"{variable} must not be null/empty",
                    action=f"Throw {exception}",
                    source_file=file_path,
                    source_lines=(line_num, line_num),
                    confidence=confidence,
                    natural_language=f"Guard: {variable} is required, throws {exception} if invalid",
                    language=Language.JAVA,
                    extraction_method=ExtractionMethod.AST,
                    extraction_tier=self.extraction_tier,
                    code_snippet=full_match,
                    parent_function=self._find_parent_method(source, match.start()),
                    parent_class=self._find_parent_class(source, match.start()),
                    variables_involved=[variable],
                )
                rules.append(rule)

        return rules

    def _find_block_end(self, source: str, start_pos: int) -> int:
        """Find the end line of a code block starting at start_pos."""
        brace_count = 1
        pos = start_pos + 1

        while pos < len(source) and brace_count > 0:
            if source[pos] == '{':
                brace_count += 1
            elif source[pos] == '}':
                brace_count -= 1
            pos += 1

        return source[:pos].count('\n') + 1

    def _extract_javadoc(self, source: str, pos: int) -> str:
        """Extract Javadoc comment before a declaration."""
        # Look backwards for /** ... */
        search_start = max(0, pos - 500)
        before = source[search_start:pos]

        javadoc_pattern = re.compile(r'/\*\*\s*(.*?)\s*\*/', re.DOTALL)
        matches = list(javadoc_pattern.finditer(before))

        if matches:
            last_match = matches[-1]
            # Check if it's close to the declaration (within 50 chars)
            if pos - search_start - last_match.end() < 50:
                return last_match.group(1).strip()

        return ""

    def _find_parent_class(self, source: str, pos: int) -> str:
        """Find the parent class for a given position."""
        before = source[:pos]

        # Find all class declarations before this position
        for match in reversed(list(self.CLASS_PATTERN.finditer(before))):
            return match.group(1)

        return ""

    def _find_parent_method(self, source: str, pos: int) -> str:
        """Find the parent method for a given position."""
        before = source[:pos]

        # Find all method declarations before this position
        for match in reversed(list(self.METHOD_PATTERN.finditer(before))):
            # Check if we're inside this method's block
            method_end = self._find_block_end(source, match.end() - 1)
            method_end_pos = len(source.split('\n')[:method_end])

            if pos < sum(len(line) + 1 for line in source.split('\n')[:method_end]):
                return match.group(2)

        return ""

    def _annotation_to_natural_language(
        self, annotation: str, rule_type: RuleType, params: str
    ) -> str:
        """Convert annotation to natural language description."""
        if '@NotNull' in annotation:
            return f"Field must not be null"
        elif '@NotEmpty' in annotation:
            return f"Field must not be empty"
        elif '@NotBlank' in annotation:
            return f"Field must not be blank"
        elif '@Size' in annotation:
            return f"Field size must satisfy: {params}"
        elif '@Min' in annotation:
            return f"Value must be at least {params}"
        elif '@Max' in annotation:
            return f"Value must be at most {params}"
        elif '@Pattern' in annotation:
            return f"Value must match pattern: {params}"
        elif '@Email' in annotation:
            return f"Field must be a valid email address"
        elif '@PreAuthorize' in annotation:
            return f"Access requires: {params}"
        elif '@Secured' in annotation:
            return f"Access restricted to role: {params}"
        elif '@Transactional' in annotation:
            return "Operation runs in a database transaction"
        elif '@Scheduled' in annotation:
            return f"Task scheduled: {params}"
        else:
            return f"Annotation constraint: {annotation}"

    def _stream_to_natural_language(self, operation: str, condition: str) -> str:
        """Convert Stream operation to natural language."""
        if '.filter' in operation:
            return f"Filter elements where {condition}"
        elif '.findFirst' in operation:
            return "Get first matching element"
        elif '.findAny' in operation:
            return "Get any matching element"
        elif '.anyMatch' in operation:
            return f"Check if any element matches: {condition}"
        elif '.allMatch' in operation:
            return f"Check if all elements match: {condition}"
        elif '.noneMatch' in operation:
            return f"Check if no elements match: {condition}"
        else:
            return f"Stream operation: {operation}"

    def _optional_to_natural_language(self, operation: str, action: str) -> str:
        """Convert Optional handling to natural language."""
        if '.orElseThrow' in operation:
            return f"Value is required, throw {action} if absent"
        elif '.orElse' in operation:
            return f"Use default value {action} if absent"
        elif '.ifPresent' in operation:
            return f"If value present, execute: {action}"
        else:
            return f"Optional handling: {operation}"
