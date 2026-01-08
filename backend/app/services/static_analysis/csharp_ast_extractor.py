# backend/app/services/static_analysis/csharp_ast_extractor.py
"""
C# AST-like Business Rule Extractor - High-precision extraction using structured parsing.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline (Phase 3)

Features:
- Structured parsing for C# code (95% target confidence)
- Extracts business rules from:
  - if/else if/else statements
  - switch statements
  - LINQ Where/Select clauses
  - Data annotations and attributes
  - Property getters/setters with validation
  - Try/catch blocks
  - Guard clauses

Detection Categories:
- VALIDATION: Input validation, FluentValidation, DataAnnotations
- AUTHORIZATION: [Authorize], policy checks, role checks
- WORKFLOW: State pattern, status changes
- CALCULATION: Business calculations, aggregations
- ERROR_HANDLING: Exception handling, Result pattern
- CONSTRAINT: Business constraints, invariants
- DATA_ACCESS: Entity Framework, repository patterns
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Set, Pattern
from pathlib import Path
from dataclasses import dataclass

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


@dataclass
class CSharpBlock:
    """Represents a parsed C# code block."""
    block_type: str  # if, switch, try, method, class, etc.
    condition: str
    body: str
    start_line: int
    end_line: int
    parent: Optional[str] = None


class CSharpASTExtractor(BaseBusinessRuleExtractor):
    """
    Extracts business rules from C# source code using structured parsing.

    Tier 1 extractor with 95% target confidence.
    Uses sophisticated regex-based parsing that simulates AST-like analysis.
    """

    SUPPORTED_EXTENSIONS = ['.cs', '.aspx.cs', '.ascx.cs']

    # C#-specific rule type patterns
    CSHARP_PATTERNS: Dict[RuleType, List[str]] = {
        RuleType.VALIDATION: [
            r'\[Required\]',
            r'\[StringLength\s*\(',
            r'\[Range\s*\(',
            r'\[RegularExpression\s*\(',
            r'\[MaxLength\s*\(',
            r'\[MinLength\s*\(',
            r'\.Validate\s*\(',
            r'\.IsValid\s*\(',
            r'FluentValidation',
            r'if\s*\(\s*string\.IsNullOrEmpty',
            r'if\s*\(\s*string\.IsNullOrWhiteSpace',
            r'ArgumentNullException\.ThrowIfNull',
        ],
        RuleType.AUTHORIZATION: [
            r'\[Authorize\s*\(',
            r'\[Authorize\]',
            r'\[AllowAnonymous\]',
            r'\.HasPermission\s*\(',
            r'\.IsInRole\s*\(',
            r'User\.IsInRole',
            r'ClaimsPrincipal',
            r'\.CanEdit\s*\(',
            r'\.CanView\s*\(',
            r'\.CanDelete\s*\(',
            r'Policy\s*=\s*"',
        ],
        RuleType.WORKFLOW: [
            r'\.Status\s*=',
            r'\.State\s*=',
            r'TransitionTo\s*\(',
            r'SetStatus\s*\(',
            r'ChangeState\s*\(',
            r'case\s+\w+Status\.',
            r'switch\s*\(\s*\w+\.Status',
            r'switch\s*\(\s*\w+\.State',
        ],
        RuleType.CALCULATION: [
            r'\.Sum\s*\(',
            r'\.Average\s*\(',
            r'\.Count\s*\(',
            r'Calculate\w+\s*\(',
            r'Compute\w+\s*\(',
            r'\.TotalAmount',
            r'\.GrandTotal',
            r'decimal\s+\w*[Tt]otal',
        ],
        RuleType.DATA_ACCESS: [
            r'\.Where\s*\(',
            r'\.FirstOrDefault\s*\(',
            r'\.SingleOrDefault\s*\(',
            r'\.Find\s*\(',
            r'\.Include\s*\(',
            r'DbContext',
            r'Repository<',
            r'IQueryable<',
            r'\.SaveChanges\s*\(',
            r'\.ExecuteAsync\s*\(',
        ],
        RuleType.ERROR_HANDLING: [
            r'try\s*\{',
            r'catch\s*\(',
            r'finally\s*\{',
            r'throw\s+new\s+',
            r'\.ThrowIfNull\s*\(',
            r'Result<',
            r'\.OnFailure\s*\(',
            r'\.OnSuccess\s*\(',
        ],
        RuleType.CONSTRAINT: [
            r'\.Requires\s*\(',
            r'\.Ensures\s*\(',
            r'Contract\.Requires',
            r'Contract\.Ensures',
            r'Guard\.\w+\s*\(',
            r'Precondition',
            r'Postcondition',
        ],
    }

    # Compiled patterns for structure parsing
    CLASS_PATTERN = re.compile(
        r'^\s*(public|private|protected|internal)?\s*(partial\s+)?'
        r'(abstract\s+|sealed\s+|static\s+)?'
        r'(class|interface|struct|record)\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    METHOD_PATTERN = re.compile(
        r'^\s*(public|private|protected|internal)?\s*'
        r'(override\s+|virtual\s+|abstract\s+|static\s+|async\s+)?'
        r'([\w<>\[\],\s]+?)\s+(\w+)\s*\(',
        re.IGNORECASE | re.MULTILINE
    )

    PROPERTY_PATTERN = re.compile(
        r'^\s*(public|private|protected|internal)?\s*'
        r'(override\s+|virtual\s+|abstract\s+|static\s+)?'
        r'([\w<>\[\]?]+)\s+(\w+)\s*\{',
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

    CASE_PATTERN = re.compile(
        r'case\s+(.+?):\s*',
        re.IGNORECASE
    )

    ATTRIBUTE_PATTERN = re.compile(
        r'\[(\w+)(?:\s*\(([^)]*)\))?\]',
        re.IGNORECASE
    )

    LINQ_WHERE_PATTERN = re.compile(
        r'\.Where\s*\(\s*(\w+)\s*=>\s*(.+?)\s*\)',
        re.IGNORECASE
    )

    THROW_PATTERN = re.compile(
        r'throw\s+new\s+(\w+(?:Exception)?)\s*\(\s*(?:"([^"]+)")?\s*',
        re.IGNORECASE
    )

    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return self.SUPPORTED_EXTENSIONS

    def get_language(self) -> Language:
        """Get the language this extractor handles."""
        return Language.CSHARP

    def get_rule_patterns(self) -> Dict[RuleType, List[str]]:
        """Get C#-specific rule patterns."""
        patterns = dict(self.COMMON_PATTERNS)
        for rule_type, csharp_patterns in self.CSHARP_PATTERNS.items():
            if rule_type in patterns:
                patterns[rule_type].extend(csharp_patterns)
            else:
                patterns[rule_type] = csharp_patterns
        return patterns

    async def _extract_symbols(self, source: str, file_path: str) -> List[CodeSymbol]:
        """
        Extract code symbols from C# source.

        Args:
            source: C# source code
            file_path: Path to source file

        Returns:
            List of CodeSymbol objects
        """
        symbols = []
        lines = source.split('\n')
        current_class = None
        brace_depth = 0
        class_start_line = 0

        for i, line in enumerate(lines, 1):
            # Track brace depth
            brace_depth += line.count('{') - line.count('}')

            # Detect class/interface/struct/record
            class_match = self.CLASS_PATTERN.match(line)
            if class_match:
                current_class = class_match.group(5)
                class_start_line = i
                symbol_type = class_match.group(4).lower()

                symbols.append(CodeSymbol(
                    name=current_class,
                    symbol_type=symbol_type,
                    line_start=i,
                    line_end=i,  # Will be updated when class ends
                    language=Language.CSHARP,
                ))

            # Detect methods
            method_match = self.METHOD_PATTERN.match(line)
            if method_match and ('{' in line or '(' in line):
                method_name = method_match.group(4) if method_match.lastindex >= 4 else None

                # Skip if it looks like a constructor or control statement
                if method_name and method_name not in ('if', 'for', 'while', 'switch', 'catch', 'using'):
                    symbols.append(CodeSymbol(
                        name=method_name,
                        symbol_type='method',
                        line_start=i,
                        line_end=i,
                        parent=current_class or '',
                        language=Language.CSHARP,
                    ))

            # Detect properties
            prop_match = self.PROPERTY_PATTERN.match(line)
            if prop_match:
                prop_name = prop_match.group(4)
                if prop_name not in ('get', 'set', 'init'):
                    symbols.append(CodeSymbol(
                        name=prop_name,
                        symbol_type='property',
                        line_start=i,
                        line_end=i,
                        parent=current_class or '',
                        language=Language.CSHARP,
                    ))

        return symbols

    async def _extract_rules_from_source(
        self,
        source: str,
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """
        Extract business rules from C# source code.

        Args:
            source: C# source code
            file_path: Path to source file
            symbols: Already extracted code symbols

        Returns:
            List of BusinessRule objects
        """
        rules = []
        source_lines = source.split('\n')

        # Extract from different patterns
        rules.extend(self._extract_attribute_rules(source, source_lines, file_path, symbols))
        rules.extend(self._extract_if_rules(source, source_lines, file_path, symbols))
        rules.extend(self._extract_switch_rules(source, source_lines, file_path, symbols))
        rules.extend(self._extract_linq_rules(source, source_lines, file_path, symbols))
        rules.extend(self._extract_throw_rules(source, source_lines, file_path, symbols))
        rules.extend(self._extract_guard_rules(source, source_lines, file_path, symbols))

        return rules

    def _extract_attribute_rules(
        self,
        source: str,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from C# attributes (DataAnnotations, Authorize, etc.)."""
        rules = []

        for i, line in enumerate(source_lines, 1):
            for match in self.ATTRIBUTE_PATTERN.finditer(line):
                attr_name = match.group(1)
                attr_args = match.group(2) or ''

                # Classify based on attribute name
                rule_type = None
                confidence = 0.92

                # Authorization attributes
                if attr_name in ('Authorize', 'AllowAnonymous', 'Roles', 'Policy'):
                    rule_type = RuleType.AUTHORIZATION
                    confidence = 0.95
                # Validation attributes
                elif attr_name in ('Required', 'StringLength', 'Range', 'MaxLength',
                                   'MinLength', 'RegularExpression', 'EmailAddress',
                                   'Phone', 'CreditCard', 'Compare', 'DataType'):
                    rule_type = RuleType.VALIDATION
                    confidence = 0.94

                if rule_type:
                    condition = f"[{attr_name}({attr_args})]" if attr_args else f"[{attr_name}]"

                    # Find what this attribute decorates (next line typically)
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
                        natural_language=self._generate_attribute_description(attr_name, attr_args, action),
                        variables_involved=self._extract_variables(attr_args),
                        language=Language.CSHARP,
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
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from if statements."""
        rules = []

        for match in self.IF_PATTERN.finditer(source):
            condition = match.group(1).strip()

            # Skip trivial conditions
            if len(condition) < 5:
                continue

            # Find line number
            start_pos = match.start()
            line_num = source[:start_pos].count('\n') + 1

            # Classify rule type
            rule_type = self._classify_csharp_condition(condition)
            if not rule_type:
                rule_type = RuleType.BRANCHING

            # Get context
            code_snippet = source_lines[line_num - 1] if line_num <= len(source_lines) else ''
            parent_class, parent_function = self._find_parent_symbol(line_num, symbols)

            # Extract action from body (simplified)
            action = self._extract_if_action(source, match.end())

            # Calculate confidence
            confidence = self._calculate_csharp_confidence(rule_type, condition, action)

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
                language=Language.CSHARP,
                extraction_method=ExtractionMethod.AST,
                extraction_tier=self.extraction_tier,
                code_snippet=code_snippet,
                parent_function=parent_function,
                parent_class=parent_class,
            ))

        return rules

    def _extract_switch_rules(
        self,
        source: str,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from switch statements."""
        rules = []

        for match in self.SWITCH_PATTERN.finditer(source):
            switch_var = match.group(1).strip()
            start_pos = match.start()
            line_num = source[:start_pos].count('\n') + 1

            # Find all cases in this switch
            switch_end = self._find_matching_brace(source, match.end() - 1)
            switch_body = source[match.end():switch_end] if switch_end > match.end() else ''

            # Determine rule type based on what's being switched
            rule_type = RuleType.BRANCHING
            if '.status' in switch_var.lower() or '.state' in switch_var.lower():
                rule_type = RuleType.WORKFLOW
            elif 'type' in switch_var.lower():
                rule_type = RuleType.BRANCHING

            # Extract cases
            cases = self.CASE_PATTERN.findall(switch_body)
            case_summary = ', '.join(cases[:5])  # First 5 cases
            if len(cases) > 5:
                case_summary += f', ... ({len(cases)} total)'

            parent_class, parent_function = self._find_parent_symbol(line_num, symbols)

            rules.append(BusinessRule(
                id=self._generate_rule_id(),
                rule_type=rule_type,
                condition=f"switch({switch_var})",
                action=f"Handle cases: {case_summary}",
                source_file=file_path,
                source_lines=(line_num, line_num + len(cases)),
                confidence=0.88,
                natural_language=f"BRANCH on {switch_var} with {len(cases)} possible outcomes",
                variables_involved=self._extract_variables(switch_var),
                language=Language.CSHARP,
                extraction_method=ExtractionMethod.AST,
                extraction_tier=self.extraction_tier,
                code_snippet=source_lines[line_num - 1] if line_num <= len(source_lines) else '',
                parent_function=parent_function,
                parent_class=parent_class,
            ))

        return rules

    def _extract_linq_rules(
        self,
        source: str,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from LINQ Where clauses."""
        rules = []

        for match in self.LINQ_WHERE_PATTERN.finditer(source):
            param = match.group(1)
            condition = match.group(2).strip()

            start_pos = match.start()
            line_num = source[:start_pos].count('\n') + 1

            parent_class, parent_function = self._find_parent_symbol(line_num, symbols)

            # Classify based on condition
            rule_type = self._classify_csharp_condition(condition)
            if not rule_type:
                rule_type = RuleType.DATA_ACCESS

            rules.append(BusinessRule(
                id=self._generate_rule_id(),
                rule_type=rule_type,
                condition=f"{param} => {condition}",
                action=f"Filter data where {condition}",
                source_file=file_path,
                source_lines=(line_num, line_num),
                confidence=0.86,
                natural_language=f"FILTER data WHERE {condition}",
                variables_involved=self._extract_variables(condition),
                language=Language.CSHARP,
                extraction_method=ExtractionMethod.AST,
                extraction_tier=self.extraction_tier,
                code_snippet=source_lines[line_num - 1] if line_num <= len(source_lines) else '',
                parent_function=parent_function,
                parent_class=parent_class,
            ))

        return rules

    def _extract_throw_rules(
        self,
        source: str,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from throw statements."""
        rules = []

        for match in self.THROW_PATTERN.finditer(source):
            exception_type = match.group(1)
            message = match.group(2) or ''

            start_pos = match.start()
            line_num = source[:start_pos].count('\n') + 1

            parent_class, parent_function = self._find_parent_symbol(line_num, symbols)

            # Classify based on exception type
            rule_type = RuleType.ERROR_HANDLING
            if 'Argument' in exception_type:
                rule_type = RuleType.VALIDATION
            elif 'Unauthorized' in exception_type or 'Access' in exception_type:
                rule_type = RuleType.AUTHORIZATION

            condition = f"Throw {exception_type}"
            action = message if message else f"Raise {exception_type}"

            rules.append(BusinessRule(
                id=self._generate_rule_id(),
                rule_type=rule_type,
                condition=condition,
                action=action,
                source_file=file_path,
                source_lines=(line_num, line_num),
                confidence=0.85,
                natural_language=f"THROW {exception_type}: {message}" if message else f"THROW {exception_type}",
                variables_involved=[],
                language=Language.CSHARP,
                extraction_method=ExtractionMethod.AST,
                extraction_tier=self.extraction_tier,
                code_snippet=source_lines[line_num - 1] if line_num <= len(source_lines) else '',
                parent_function=parent_function,
                parent_class=parent_class,
            ))

        return rules

    def _extract_guard_rules(
        self,
        source: str,
        source_lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from guard clauses and early returns."""
        rules = []

        # Pattern for guard clauses: if (condition) { return/throw }
        guard_pattern = re.compile(
            r'if\s*\(\s*(.+?)\s*\)\s*\{\s*(return|throw)[^}]+\}',
            re.IGNORECASE | re.DOTALL
        )

        for match in guard_pattern.finditer(source):
            condition = match.group(1).strip()
            action_type = match.group(2)

            start_pos = match.start()
            line_num = source[:start_pos].count('\n') + 1

            parent_class, parent_function = self._find_parent_symbol(line_num, symbols)

            rule_type = RuleType.VALIDATION if action_type.lower() == 'throw' else RuleType.CONSTRAINT

            rules.append(BusinessRule(
                id=self._generate_rule_id(),
                rule_type=rule_type,
                condition=condition,
                action=f"Guard: {action_type}",
                source_file=file_path,
                source_lines=(line_num, line_num + 1),
                confidence=0.90,  # Guard clauses are explicit business logic
                natural_language=f"GUARD: If {condition} then {action_type}",
                variables_involved=self._extract_variables(condition),
                language=Language.CSHARP,
                extraction_method=ExtractionMethod.AST,
                extraction_tier=self.extraction_tier,
                parent_function=parent_function,
                parent_class=parent_class,
            ))

        return rules

    def _classify_csharp_condition(self, condition: str) -> Optional[RuleType]:
        """Classify rule type based on C# condition."""
        condition_lower = condition.lower()

        # Validation patterns
        if any(p in condition_lower for p in [
            'string.isnullorempty', 'string.isnullorwhitespace',
            '== null', 'is null', '!= null', 'is not null',
            '.length', '.count', 'isvalid'
        ]):
            return RuleType.VALIDATION

        # Authorization patterns
        if any(p in condition_lower for p in [
            'isauthorized', 'haspermission', 'isinrole',
            'isauthenticated', 'canview', 'canedit', 'candelete'
        ]):
            return RuleType.AUTHORIZATION

        # Workflow patterns
        if any(p in condition_lower for p in [
            '.status', '.state', 'status ==', 'state =='
        ]):
            return RuleType.WORKFLOW

        # Threshold patterns
        if any(p in condition_lower for p in [
            '>=', '<=', '> ', '< ', '.count', '.length'
        ]):
            return RuleType.THRESHOLD

        return None

    def _calculate_csharp_confidence(
        self,
        rule_type: RuleType,
        condition: str,
        action: str
    ) -> float:
        """Calculate confidence score for C# extracted rules."""
        base_confidence = 0.82

        # Boost for explicit patterns
        type_boost = {
            RuleType.AUTHORIZATION: 0.10,
            RuleType.VALIDATION: 0.08,
            RuleType.WORKFLOW: 0.08,
            RuleType.ERROR_HANDLING: 0.05,
        }
        base_confidence += type_boost.get(rule_type, 0.0)

        # Boost for framework-specific patterns
        if any(p in condition.lower() for p in ['string.isnull', 'argumentexception']):
            base_confidence += 0.05

        return min(base_confidence, 0.95)

    def _find_decorated_member(self, source_lines: List[str], attr_line: int) -> str:
        """Find the member decorated by an attribute."""
        for i in range(attr_line, min(attr_line + 5, len(source_lines))):
            line = source_lines[i].strip()
            # Skip more attributes and empty lines
            if line.startswith('[') or not line:
                continue
            # Found a declaration
            if 'public' in line or 'private' in line or 'protected' in line:
                return line[:80] + ('...' if len(line) > 80 else '')
        return "decorated member"

    def _extract_if_action(self, source: str, start_pos: int) -> str:
        """Extract action from if body."""
        # Simple extraction of first statement after if
        remaining = source[start_pos:start_pos + 200]
        if '{' in remaining:
            body_start = remaining.index('{') + 1
            lines = remaining[body_start:].split('\n')
            for line in lines[:3]:
                line = line.strip()
                if line and not line.startswith('//') and line != '}':
                    return line[:60] + ('...' if len(line) > 60 else '')
        return "execute logic"

    def _generate_attribute_description(self, attr_name: str, attr_args: str, target: str) -> str:
        """Generate natural language description for attribute-based rules."""
        if attr_name == 'Required':
            return f"REQUIRE that {target} is not null or empty"
        elif attr_name == 'StringLength':
            return f"CONSTRAIN length of {target} to {attr_args}"
        elif attr_name == 'Range':
            return f"CONSTRAIN {target} value to range {attr_args}"
        elif attr_name == 'Authorize':
            policy = f"policy {attr_args}" if attr_args else "authentication"
            return f"REQUIRE {policy} to access {target}"
        elif attr_name == 'AllowAnonymous':
            return f"ALLOW anonymous access to {target}"
        else:
            return f"APPLY {attr_name}({attr_args}) to {target}"

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
        """Override to set AST extraction method."""
        result = await super().extract_from_file(file_path, source)
        result.extraction_method = ExtractionMethod.AST
        return result


# Convenience function
async def extract_csharp_rules(
    file_path: str,
    extraction_tier: ExtractionTier = ExtractionTier.STANDARD,
) -> List[BusinessRule]:
    """
    Extract business rules from a C# file.

    Args:
        file_path: Path to C# file
        extraction_tier: Customer tier

    Returns:
        List of extracted BusinessRule objects
    """
    extractor = CSharpASTExtractor(extraction_tier=extraction_tier)
    result = await extractor.extract_from_file(file_path)
    return result.business_rules
