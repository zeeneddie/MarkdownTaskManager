# backend/app/services/static_analysis/javascript_ast_extractor.py
"""
JavaScript/TypeScript AST-like Business Rule Extractor - High-precision extraction.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline (Phase 3)

Features:
- Structured parsing for JavaScript/TypeScript code (90% target confidence)
- Extracts business rules from:
  - if/else if/else statements
  - switch statements
  - Ternary operators
  - TypeScript guards and type checks
  - Array methods (filter, find, some, every)
  - Object property validations
  - Try/catch blocks
  - Class decorators (NestJS, Angular)

Detection Categories:
- VALIDATION: Input validation, Joi/Zod schemas, type guards
- AUTHORIZATION: Guards, middleware, decorators
- WORKFLOW: State transitions, Redux actions
- CALCULATION: Business calculations, aggregations
- ERROR_HANDLING: Exception handling, async error handling
- CONSTRAINT: Business constraints, type assertions
- DATA_ACCESS: API calls, database queries
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Set
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


class JavaScriptASTExtractor(BaseBusinessRuleExtractor):
    """
    Extracts business rules from JavaScript/TypeScript source code.

    Tier 1 extractor with 90% target confidence.
    Uses sophisticated pattern matching for JS/TS-specific constructs.
    """

    SUPPORTED_EXTENSIONS = ['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs']

    # JavaScript/TypeScript-specific rule type patterns
    JS_PATTERNS: Dict[RuleType, List[str]] = {
        RuleType.VALIDATION: [
            r'if\s*\(\s*!?\s*\w+\s*\)',
            r'if\s*\(\s*typeof\s+',
            r'if\s*\(\s*\w+\s*===?\s*null',
            r'if\s*\(\s*\w+\s*===?\s*undefined',
            r'\.validate\s*\(',
            r'\.isValid\s*\(',
            r'z\.object\s*\(',  # Zod
            r'Joi\.\w+\s*\(',   # Joi
            r'yup\.\w+\s*\(',   # Yup
            r'@IsNotEmpty',     # class-validator
            r'@IsString',
            r'@IsNumber',
            r'@IsEmail',
        ],
        RuleType.AUTHORIZATION: [
            r'@UseGuards\s*\(',
            r'@Roles\s*\(',
            r'@Auth\s*\(',
            r'\.canActivate\s*\(',
            r'isAuthenticated',
            r'hasPermission\s*\(',
            r'checkAccess\s*\(',
            r'@Authorized\s*\(',
            r'req\.user',
            r'context\.user',
        ],
        RuleType.WORKFLOW: [
            r'\.dispatch\s*\(\s*\{[^}]*type:',  # Redux
            r'setState\s*\(',
            r'\.status\s*=',
            r'\.state\s*=',
            r'case\s+[\'"`]\w+[\'"`]:',  # Redux action types
            r'@Action\s*\(',  # MobX
        ],
        RuleType.CALCULATION: [
            r'\.reduce\s*\(',
            r'\.sum\s*\(',
            r'Math\.\w+\s*\(',
            r'total\s*[+\-*/]=',
            r'calculate\w+\s*\(',
        ],
        RuleType.DATA_ACCESS: [
            r'\.filter\s*\(',
            r'\.find\s*\(',
            r'\.findOne\s*\(',
            r'\.findById\s*\(',
            r'\.query\s*\(',
            r'await\s+fetch\s*\(',
            r'axios\.\w+\s*\(',
            r'prisma\.\w+\.',
            r'mongoose\.\w+\.',
        ],
        RuleType.ERROR_HANDLING: [
            r'try\s*\{',
            r'catch\s*\(',
            r'\.catch\s*\(',
            r'throw\s+new\s+',
            r'Promise\.reject\s*\(',
            r'\.finally\s*\(',
        ],
        RuleType.CONSTRAINT: [
            r'assert\s*\(',
            r'invariant\s*\(',
            r'expect\s*\(',
            r'as\s+\w+',  # Type assertion
            r':\s*\w+\s*=',  # Type annotation
        ],
    }

    # Compiled patterns for structure parsing
    FUNCTION_PATTERN = re.compile(
        r'(?:async\s+)?(?:function\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*\w+)?\s*[{=>]',
        re.IGNORECASE
    )

    ARROW_FUNCTION_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(?[^)]*\)?\s*=>',
        re.IGNORECASE
    )

    CLASS_PATTERN = re.compile(
        r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)',
        re.IGNORECASE
    )

    METHOD_PATTERN = re.compile(
        r'^\s*(?:async\s+)?(?:static\s+)?(?:get\s+|set\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*\w+)?\s*\{',
        re.IGNORECASE | re.MULTILINE
    )

    IF_PATTERN = re.compile(
        r'if\s*\(\s*(.+?)\s*\)\s*\{?',
        re.IGNORECASE | re.DOTALL
    )

    SWITCH_PATTERN = re.compile(
        r'switch\s*\(\s*(.+?)\s*\)\s*\{',
        re.IGNORECASE
    )

    TERNARY_PATTERN = re.compile(
        r'(\w+(?:\.\w+)*)\s*\?\s*([^:]+?)\s*:\s*([^;\n]+)',
        re.IGNORECASE
    )

    DECORATOR_PATTERN = re.compile(
        r'@(\w+)\s*(?:\(\s*([^)]*)\s*\))?',
        re.IGNORECASE
    )

    ARRAY_METHOD_PATTERN = re.compile(
        r'\.(?:filter|find|some|every|map)\s*\(\s*(?:async\s+)?\(?(\w*)\)?\s*=>\s*([^)]+)\)',
        re.IGNORECASE
    )

    TYPE_GUARD_PATTERN = re.compile(
        r'if\s*\(\s*typeof\s+(\w+)\s*===?\s*[\'"`](\w+)[\'"`]',
        re.IGNORECASE
    )

    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return self.SUPPORTED_EXTENSIONS

    def get_language(self) -> Language:
        """Get the language this extractor handles."""
        # Return JAVASCRIPT for .js files, TYPESCRIPT for .ts files
        # Default to JAVASCRIPT
        return Language.JAVASCRIPT

    def _detect_language(self, file_path: str) -> Language:
        """Detect if file is JavaScript or TypeScript."""
        if file_path.endswith(('.ts', '.tsx')):
            return Language.TYPESCRIPT
        return Language.JAVASCRIPT

    def get_rule_patterns(self) -> Dict[RuleType, List[str]]:
        """Get JavaScript/TypeScript-specific rule patterns."""
        patterns = dict(self.COMMON_PATTERNS)
        for rule_type, js_patterns in self.JS_PATTERNS.items():
            if rule_type in patterns:
                patterns[rule_type].extend(js_patterns)
            else:
                patterns[rule_type] = js_patterns
        return patterns

    async def _extract_symbols(self, source: str, file_path: str) -> List[CodeSymbol]:
        """
        Extract code symbols from JavaScript/TypeScript source.

        Args:
            source: JS/TS source code
            file_path: Path to source file

        Returns:
            List of CodeSymbol objects
        """
        symbols = []
        language = self._detect_language(file_path)
        lines = source.split('\n')
        current_class = None

        for i, line in enumerate(lines, 1):
            # Detect classes
            class_match = self.CLASS_PATTERN.search(line)
            if class_match:
                current_class = class_match.group(1)
                symbols.append(CodeSymbol(
                    name=current_class,
                    symbol_type='class',
                    line_start=i,
                    line_end=i,
                    language=language,
                ))

            # Detect functions
            func_match = self.FUNCTION_PATTERN.search(line)
            if func_match and 'if' not in line and 'while' not in line:
                func_name = func_match.group(1)
                if func_name not in ('if', 'for', 'while', 'switch', 'catch'):
                    symbols.append(CodeSymbol(
                        name=func_name,
                        symbol_type='function',
                        line_start=i,
                        line_end=i,
                        parent=current_class or '',
                        language=language,
                    ))

            # Detect arrow functions
            arrow_match = self.ARROW_FUNCTION_PATTERN.search(line)
            if arrow_match:
                symbols.append(CodeSymbol(
                    name=arrow_match.group(1),
                    symbol_type='function',
                    line_start=i,
                    line_end=i,
                    language=language,
                ))

            # Detect methods in classes
            if current_class:
                method_match = self.METHOD_PATTERN.match(line)
                if method_match:
                    method_name = method_match.group(1)
                    if method_name not in ('if', 'for', 'while', 'switch', 'catch', 'constructor'):
                        symbols.append(CodeSymbol(
                            name=method_name,
                            symbol_type='method',
                            line_start=i,
                            line_end=i,
                            parent=current_class,
                            language=language,
                        ))

        return symbols

    async def _extract_rules_from_source(
        self,
        source: str,
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """
        Extract business rules from JavaScript/TypeScript source code.

        Args:
            source: JS/TS source code
            file_path: Path to source file
            symbols: Already extracted code symbols

        Returns:
            List of BusinessRule objects
        """
        rules = []
        source_lines = source.split('\n')
        language = self._detect_language(file_path)

        # Extract from different patterns
        rules.extend(self._extract_decorator_rules(source, source_lines, file_path, symbols, language))
        rules.extend(self._extract_if_rules(source, source_lines, file_path, symbols, language))
        rules.extend(self._extract_type_guard_rules(source, source_lines, file_path, symbols, language))
        rules.extend(self._extract_array_method_rules(source, source_lines, file_path, symbols, language))
        rules.extend(self._extract_ternary_rules(source, source_lines, file_path, symbols, language))
        rules.extend(self._extract_throw_rules(source, source_lines, file_path, symbols, language))
        rules.extend(self._extract_switch_rules(source, source_lines, file_path, symbols, language))

        return rules

    def _extract_decorator_rules(
        self,
        source: str,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol],
        language: Language
    ) -> List[BusinessRule]:
        """Extract business rules from decorators (NestJS, Angular, class-validator)."""
        rules = []

        for i, line in enumerate(source_lines, 1):
            for match in self.DECORATOR_PATTERN.finditer(line):
                decorator_name = match.group(1)
                decorator_args = match.group(2) or ''

                # Classify based on decorator name
                rule_type = None
                confidence = 0.90

                # Authorization decorators
                if decorator_name in ('UseGuards', 'Roles', 'Auth', 'Authorized',
                                       'RequireAuth', 'Protected'):
                    rule_type = RuleType.AUTHORIZATION
                    confidence = 0.93

                # Validation decorators (class-validator)
                elif decorator_name in ('IsNotEmpty', 'IsString', 'IsNumber', 'IsEmail',
                                        'IsInt', 'Min', 'Max', 'Length', 'IsOptional',
                                        'IsArray', 'IsBoolean', 'IsDate', 'ValidateNested'):
                    rule_type = RuleType.VALIDATION
                    confidence = 0.92

                if rule_type:
                    condition = f"@{decorator_name}({decorator_args})" if decorator_args else f"@{decorator_name}"
                    action = self._find_decorated_member(source_lines, i)

                    parent_class, parent_function = self._find_parent_symbol(i, symbols)

                    rules.append(BusinessRule(
                        id=self._generate_rule_id(),
                        rule_type=rule_type,
                        condition=condition,
                        action=action,
                        source_file=file_path,
                        source_lines=(i, i),
                        confidence=confidence,
                        natural_language=self._generate_decorator_description(decorator_name, decorator_args, action),
                        variables_involved=self._extract_variables(decorator_args),
                        language=language,
                        extraction_method=ExtractionMethod.AST,
                        extraction_tier=self.extraction_tier,
                        code_snippet=line.strip(),
                        parent_function=parent_function,
                        parent_class=parent_class,
                    ))

        return rules

    def _extract_if_rules(
        self,
        source: str,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol],
        language: Language
    ) -> List[BusinessRule]:
        """Extract business rules from if statements."""
        rules = []

        for match in self.IF_PATTERN.finditer(source):
            condition = match.group(1).strip()

            # Skip trivial conditions
            if len(condition) < 3:
                continue

            # Find line number
            start_pos = match.start()
            line_num = source[:start_pos].count('\n') + 1

            # Classify rule type
            rule_type = self._classify_js_condition(condition)
            if not rule_type:
                rule_type = RuleType.BRANCHING

            code_snippet = source_lines[line_num - 1] if line_num <= len(source_lines) else ''
            parent_class, parent_function = self._find_parent_symbol(line_num, symbols)

            # Extract action
            action = self._extract_if_action(source, match.end())

            confidence = self._calculate_js_confidence(rule_type, condition, action)

            rules.append(BusinessRule(
                id=self._generate_rule_id(),
                rule_type=rule_type,
                condition=condition,
                action=action,
                source_file=file_path,
                source_lines=(line_num, line_num + 2),
                confidence=confidence,
                natural_language=self._generate_natural_language(rule_type, condition, action),
                variables_involved=self._extract_variables(condition),
                related_entities=self._extract_entities(condition, self._extract_variables(condition)),
                language=language,
                extraction_method=ExtractionMethod.AST,
                extraction_tier=self.extraction_tier,
                code_snippet=code_snippet,
                parent_function=parent_function,
                parent_class=parent_class,
            ))

        return rules

    def _extract_type_guard_rules(
        self,
        source: str,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol],
        language: Language
    ) -> List[BusinessRule]:
        """Extract business rules from TypeScript type guards."""
        rules = []

        for match in self.TYPE_GUARD_PATTERN.finditer(source):
            variable = match.group(1)
            expected_type = match.group(2)

            start_pos = match.start()
            line_num = source[:start_pos].count('\n') + 1

            parent_class, parent_function = self._find_parent_symbol(line_num, symbols)

            condition = f"typeof {variable} === '{expected_type}'"
            action = f"Type guard for {variable}"

            rules.append(BusinessRule(
                id=self._generate_rule_id(),
                rule_type=RuleType.VALIDATION,
                condition=condition,
                action=action,
                source_file=file_path,
                source_lines=(line_num, line_num),
                confidence=0.88,
                natural_language=f"VALIDATE that {variable} is of type {expected_type}",
                variables_involved=[variable],
                language=language,
                extraction_method=ExtractionMethod.AST,
                extraction_tier=self.extraction_tier,
                code_snippet=source_lines[line_num - 1] if line_num <= len(source_lines) else '',
                parent_function=parent_function,
                parent_class=parent_class,
            ))

        return rules

    def _extract_array_method_rules(
        self,
        source: str,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol],
        language: Language
    ) -> List[BusinessRule]:
        """Extract business rules from array filter/find/some/every methods."""
        rules = []

        # Extended pattern to capture method name
        pattern = re.compile(
            r'\.(\w+)\s*\(\s*(?:async\s+)?\(?(\w*)\)?\s*=>\s*([^)]+)\)',
            re.IGNORECASE
        )

        for match in pattern.finditer(source):
            method = match.group(1)
            if method not in ('filter', 'find', 'some', 'every', 'map'):
                continue

            param = match.group(2) or 'item'
            condition = match.group(3).strip()

            start_pos = match.start()
            line_num = source[:start_pos].count('\n') + 1

            parent_class, parent_function = self._find_parent_symbol(line_num, symbols)

            # Determine rule type based on method
            if method in ('filter', 'find'):
                rule_type = RuleType.DATA_ACCESS
            elif method in ('some', 'every'):
                rule_type = RuleType.VALIDATION
            else:
                rule_type = RuleType.DERIVATION

            action = f"{method.capitalize()} where {condition}"

            rules.append(BusinessRule(
                id=self._generate_rule_id(),
                rule_type=rule_type,
                condition=f"{param} => {condition}",
                action=action,
                source_file=file_path,
                source_lines=(line_num, line_num),
                confidence=0.85,
                natural_language=f"{method.upper()} items where {condition}",
                variables_involved=self._extract_variables(condition),
                language=language,
                extraction_method=ExtractionMethod.AST,
                extraction_tier=self.extraction_tier,
                code_snippet=source_lines[line_num - 1] if line_num <= len(source_lines) else '',
                parent_function=parent_function,
                parent_class=parent_class,
            ))

        return rules

    def _extract_ternary_rules(
        self,
        source: str,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol],
        language: Language
    ) -> List[BusinessRule]:
        """Extract business rules from ternary operators."""
        rules = []

        for match in self.TERNARY_PATTERN.finditer(source):
            condition = match.group(1).strip()
            true_value = match.group(2).strip()
            false_value = match.group(3).strip()

            # Skip simple ternaries
            if len(condition) < 5:
                continue

            start_pos = match.start()
            line_num = source[:start_pos].count('\n') + 1

            parent_class, parent_function = self._find_parent_symbol(line_num, symbols)

            rule_type = self._classify_js_condition(condition)
            if not rule_type:
                rule_type = RuleType.DERIVATION

            rules.append(BusinessRule(
                id=self._generate_rule_id(),
                rule_type=rule_type,
                condition=condition,
                action=f"{true_value} else {false_value}",
                source_file=file_path,
                source_lines=(line_num, line_num),
                confidence=0.82,
                natural_language=f"IF {condition} THEN {true_value} ELSE {false_value}",
                variables_involved=self._extract_variables(condition),
                language=language,
                extraction_method=ExtractionMethod.AST,
                extraction_tier=self.extraction_tier,
                parent_function=parent_function,
                parent_class=parent_class,
            ))

        return rules

    def _extract_throw_rules(
        self,
        source: str,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol],
        language: Language
    ) -> List[BusinessRule]:
        """Extract business rules from throw statements."""
        rules = []

        throw_pattern = re.compile(
            r'throw\s+new\s+(\w+(?:Error)?)\s*\(\s*(?:[\'"`]([^\'"`]+)[\'"`])?\s*',
            re.IGNORECASE
        )

        for match in throw_pattern.finditer(source):
            error_type = match.group(1)
            message = match.group(2) or ''

            start_pos = match.start()
            line_num = source[:start_pos].count('\n') + 1

            parent_class, parent_function = self._find_parent_symbol(line_num, symbols)

            rule_type = RuleType.ERROR_HANDLING
            if 'Validation' in error_type or 'Argument' in error_type:
                rule_type = RuleType.VALIDATION
            elif 'Auth' in error_type or 'Forbidden' in error_type or 'Unauthorized' in error_type:
                rule_type = RuleType.AUTHORIZATION

            rules.append(BusinessRule(
                id=self._generate_rule_id(),
                rule_type=rule_type,
                condition=f"Throw {error_type}",
                action=message if message else f"Raise {error_type}",
                source_file=file_path,
                source_lines=(line_num, line_num),
                confidence=0.85,
                natural_language=f"THROW {error_type}: {message}" if message else f"THROW {error_type}",
                variables_involved=[],
                language=language,
                extraction_method=ExtractionMethod.AST,
                extraction_tier=self.extraction_tier,
                code_snippet=source_lines[line_num - 1] if line_num <= len(source_lines) else '',
                parent_function=parent_function,
                parent_class=parent_class,
            ))

        return rules

    def _extract_switch_rules(
        self,
        source: str,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol],
        language: Language
    ) -> List[BusinessRule]:
        """Extract business rules from switch statements."""
        rules = []

        for match in self.SWITCH_PATTERN.finditer(source):
            switch_var = match.group(1).strip()
            start_pos = match.start()
            line_num = source[:start_pos].count('\n') + 1

            # Find cases
            switch_end = self._find_matching_brace(source, match.end() - 1)
            switch_body = source[match.end():switch_end] if switch_end > match.end() else ''

            case_pattern = re.compile(r'case\s+([\'"`]?\w+[\'"`]?):', re.IGNORECASE)
            cases = case_pattern.findall(switch_body)
            case_summary = ', '.join(cases[:5])
            if len(cases) > 5:
                case_summary += f', ... ({len(cases)} total)'

            parent_class, parent_function = self._find_parent_symbol(line_num, symbols)

            # Determine rule type
            rule_type = RuleType.BRANCHING
            if '.type' in switch_var.lower() or 'action' in switch_var.lower():
                rule_type = RuleType.WORKFLOW  # Redux-style action handling
            elif '.status' in switch_var.lower() or '.state' in switch_var.lower():
                rule_type = RuleType.WORKFLOW

            rules.append(BusinessRule(
                id=self._generate_rule_id(),
                rule_type=rule_type,
                condition=f"switch({switch_var})",
                action=f"Handle cases: {case_summary}",
                source_file=file_path,
                source_lines=(line_num, line_num + len(cases)),
                confidence=0.86,
                natural_language=f"BRANCH on {switch_var} with {len(cases)} possible outcomes",
                variables_involved=self._extract_variables(switch_var),
                language=language,
                extraction_method=ExtractionMethod.AST,
                extraction_tier=self.extraction_tier,
                code_snippet=source_lines[line_num - 1] if line_num <= len(source_lines) else '',
                parent_function=parent_function,
                parent_class=parent_class,
            ))

        return rules

    def _classify_js_condition(self, condition: str) -> Optional[RuleType]:
        """Classify rule type based on JavaScript/TypeScript condition."""
        condition_lower = condition.lower()

        # Validation patterns
        if any(p in condition_lower for p in [
            '=== null', '=== undefined', '!== null', '!== undefined',
            'typeof', '.length', 'isvalid', 'validate', 'isnan'
        ]):
            return RuleType.VALIDATION

        # Authorization patterns
        if any(p in condition_lower for p in [
            'isauthorized', 'isauthenticated', 'haspermission',
            'user.role', 'req.user', 'context.user', 'session.user'
        ]):
            return RuleType.AUTHORIZATION

        # Workflow patterns
        if any(p in condition_lower for p in [
            '.status', '.state', 'action.type'
        ]):
            return RuleType.WORKFLOW

        return None

    def _calculate_js_confidence(
        self,
        rule_type: RuleType,
        condition: str,
        action: str
    ) -> float:
        """Calculate confidence score for JS/TS extracted rules."""
        base_confidence = 0.80

        type_boost = {
            RuleType.AUTHORIZATION: 0.10,
            RuleType.VALIDATION: 0.08,
            RuleType.WORKFLOW: 0.06,
            RuleType.ERROR_HANDLING: 0.05,
        }
        base_confidence += type_boost.get(rule_type, 0.0)

        # Boost for explicit patterns
        if 'typeof' in condition:
            base_confidence += 0.04
        if '===' in condition or '!==' in condition:
            base_confidence += 0.02

        return min(base_confidence, 0.92)

    def _find_decorated_member(self, source_lines: List[str], decorator_line: int) -> str:
        """Find the member decorated by a decorator."""
        for i in range(decorator_line, min(decorator_line + 5, len(source_lines))):
            line = source_lines[i].strip()
            if line.startswith('@') or not line:
                continue
            if any(kw in line for kw in ['class ', 'function ', 'async ', 'const ', 'get ', 'set ']):
                return line[:60] + ('...' if len(line) > 60 else '')
            if '(' in line or ':' in line:  # Method or property
                return line[:60] + ('...' if len(line) > 60 else '')
        return "decorated member"

    def _extract_if_action(self, source: str, start_pos: int) -> str:
        """Extract action from if body."""
        remaining = source[start_pos:start_pos + 200]
        if '{' in remaining:
            body_start = remaining.index('{') + 1
            lines = remaining[body_start:].split('\n')
            for line in lines[:3]:
                line = line.strip()
                if line and not line.startswith('//') and line != '}':
                    return line[:60] + ('...' if len(line) > 60 else '')
        return "execute logic"

    def _generate_decorator_description(self, decorator_name: str, decorator_args: str, target: str) -> str:
        """Generate natural language description for decorator-based rules."""
        if decorator_name == 'UseGuards':
            return f"REQUIRE {decorator_args or 'guard'} to access {target}"
        elif decorator_name == 'Roles':
            return f"REQUIRE role {decorator_args} to access {target}"
        elif decorator_name in ('IsNotEmpty', 'IsString', 'IsNumber', 'IsEmail'):
            return f"VALIDATE {target} with {decorator_name}"
        else:
            return f"APPLY @{decorator_name} to {target}"

    def _find_matching_brace(self, source: str, start_pos: int) -> int:
        """Find the position of the matching closing brace."""
        depth = 1
        pos = start_pos + 1

        while pos < len(source) and depth > 0:
            if source[pos] == '{':
                depth += 1
            elif source[pos] == '}':
                depth -= 1
            pos += 1

        return pos

    async def extract_from_file(
        self,
        file_path: str,
        source: Optional[str] = None,
    ):
        """Override to set language based on file extension."""
        result = await super().extract_from_file(file_path, source)
        result.extraction_method = ExtractionMethod.AST
        result.language = self._detect_language(file_path)
        return result


# Convenience functions
async def extract_javascript_rules(
    file_path: str,
    extraction_tier: ExtractionTier = ExtractionTier.STANDARD,
) -> List[BusinessRule]:
    """
    Extract business rules from a JavaScript file.

    Args:
        file_path: Path to JS file
        extraction_tier: Customer tier

    Returns:
        List of extracted BusinessRule objects
    """
    extractor = JavaScriptASTExtractor(extraction_tier=extraction_tier)
    result = await extractor.extract_from_file(file_path)
    return result.business_rules


async def extract_typescript_rules(
    file_path: str,
    extraction_tier: ExtractionTier = ExtractionTier.STANDARD,
) -> List[BusinessRule]:
    """
    Extract business rules from a TypeScript file.

    Args:
        file_path: Path to TS file
        extraction_tier: Customer tier

    Returns:
        List of extracted BusinessRule objects
    """
    extractor = JavaScriptASTExtractor(extraction_tier=extraction_tier)
    result = await extractor.extract_from_file(file_path)
    return result.business_rules
