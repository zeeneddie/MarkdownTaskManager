# backend/app/services/static_analysis/plsql_extractor.py
"""
PL/SQL Business Rule Extractor - Extracts business rules from Oracle PL/SQL code.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline - Phase 2

Supports:
- Oracle stored procedures and functions
- PL/SQL packages (.pkg, .pkb, .pks)
- Oracle triggers

Detection patterns:
- IF-THEN-ELSE/ELSIF blocks
- CASE WHEN statements
- EXCEPTION handling (WHEN OTHERS, specific exceptions)
- Cursor logic
- DBMS_OUTPUT debug statements
- Constraint checks
"""

from typing import List, Dict, Optional, Tuple
import re
import logging

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


class PLSQLBusinessRuleExtractor(BaseBusinessRuleExtractor):
    """
    Extracts business rules from Oracle PL/SQL code.

    Uses regex-enhanced extraction (Tier 2) with optional LLM validation.
    Designed for Oracle stored procedures, functions, packages, and triggers.
    """

    SUPPORTED_EXTENSIONS = ['.pkg', '.pkb', '.pks', '.fnc', '.trg']

    # PL/SQL specific patterns for rule detection
    PLSQL_PATTERNS: Dict[RuleType, List[str]] = {
        RuleType.VALIDATION: [
            r'IF\s+(.+?)\s+THEN',                               # IF-THEN
            r'ELSIF\s+(.+?)\s+THEN',                            # ELSIF-THEN
            r'IF\s+NOT\s+',                                     # Negated condition
            r'IF\s+\w+\s+IS\s+NULL',                            # Null check
            r'IF\s+\w+\s+IS\s+NOT\s+NULL',                      # Not null check
            r'IF\s+NVL\s*\(',                                   # NVL check
            r'IF\s+LENGTH\s*\(',                                # Length check
            r'IF\s+REGEXP_LIKE\s*\(',                           # Regex validation
            r'WHERE\s+.+?(?:AND|OR)',                           # Complex WHERE
        ],
        RuleType.AUTHORIZATION: [
            r'SYS_CONTEXT\s*\(',                                # Context security
            r'USERENV\s*\(',                                    # User environment
            r'USER\b',                                          # Current user
            r'DBMS_SESSION\.',                                  # Session management
            r'GRANT\s+',                                        # Grant permission
            r'REVOKE\s+',                                       # Revoke permission
            r'p_can\w+',                                        # Permission parameter
            r'v_can\w+',                                        # Permission variable
            r'l_can\w+',                                        # Local permission var
        ],
        RuleType.SCHEDULING: [
            r'SYSDATE',                                         # Current date/time
            r'SYSTIMESTAMP',                                    # Current timestamp
            r'ADD_MONTHS\s*\(',                                 # Date arithmetic
            r'MONTHS_BETWEEN\s*\(',                             # Date difference
            r'TRUNC\s*\(.+?,\s*[\'\"]',                         # Date truncation
            r'TO_DATE\s*\(',                                    # Date conversion
            r'TO_TIMESTAMP\s*\(',                               # Timestamp conversion
            r'p_start_date|p_end_date',                         # Date parameters
            r'v_start_date|v_end_date',                         # Date variables
            r'INTERVAL\s+',                                     # Interval literal
        ],
        RuleType.WORKFLOW: [
            r'v_status\s*:?=',                                  # Status assignment
            r'p_status\s*',                                     # Status parameter
            r"status\s*=\s*'(\w+)'",                            # Status literal
            r'l_state\s*:?=',                                   # State assignment
            r'UPDATE\s+.+?\s+SET\s+.+?status',                  # Status update
        ],
        RuleType.BRANCHING: [
            r'CASE\s+WHEN',                                     # CASE WHEN start
            r'CASE\s+\w+',                                      # Simple CASE
            r'WHEN\s+.+?\s+THEN',                               # WHEN clause
            r'ELSE\s+',                                         # ELSE clause
            r'END\s+CASE',                                      # CASE END
            r'ELSIF\s+',                                        # ELSIF branch
        ],
        RuleType.THRESHOLD: [
            r'\w+\s*(>=|<=|>|<|=)\s*(\d+)',                     # Numeric comparison
            r'COUNT\s*\(.+?\)\s*(>=|<=|>|<|=)\s*(\d+)',         # Count threshold
            r'SUM\s*\(.+?\)\s*(>=|<=|>|<|=)',                   # Sum threshold
            r'MAX\s*\(.+?\)\s*(>=|<=|>|<|=)',                   # Max threshold
            r'MIN\s*\(.+?\)\s*(>=|<=|>|<|=)',                   # Min threshold
            r'AVG\s*\(.+?\)\s*(>=|<=|>|<|=)',                   # Average threshold
            r'ROWNUM\s*(<=|<)\s*(\d+)',                         # Rownum limit
            r'FETCH\s+FIRST\s+(\d+)',                           # Fetch first
        ],
        RuleType.DATA_ACCESS: [
            r'INSERT\s+INTO\s+(\w+)',                           # Insert statement
            r'UPDATE\s+(\w+)\s+SET',                            # Update statement
            r'DELETE\s+FROM\s+(\w+)',                           # Delete statement
            r'SELECT\s+.+?\s+INTO\s+',                          # Select into
            r'SELECT\s+.+?\s+FROM\s+(\w+)',                     # Select statement
            r'EXECUTE\s+IMMEDIATE',                             # Dynamic SQL
            r'MERGE\s+INTO\s+(\w+)',                            # Merge statement
            r'FORALL\s+',                                       # Bulk DML
            r'BULK\s+COLLECT',                                  # Bulk collect
        ],
        RuleType.STATE_MANAGEMENT: [
            r'\w+\s*:=',                                        # Variable assignment
            r'DECLARE\s+',                                      # Declare section
            r'CURSOR\s+\w+\s+IS',                               # Cursor declaration
            r'OPEN\s+\w+',                                      # Open cursor
            r'FETCH\s+\w+\s+INTO',                              # Fetch cursor
            r'CLOSE\s+\w+',                                     # Close cursor
            r'FOR\s+\w+\s+IN\s+',                               # FOR loop
            r'DBMS_SESSION\.',                                  # Session state
            r'SQL%ROWCOUNT',                                    # Row count
            r'SQL%FOUND',                                       # Found flag
            r'SQL%NOTFOUND',                                    # Not found flag
        ],
        RuleType.ERROR_HANDLING: [
            r'EXCEPTION',                                       # Exception section
            r'WHEN\s+\w+\s+THEN',                               # Named exception
            r'WHEN\s+OTHERS\s+THEN',                            # Catch all
            r'RAISE\s+',                                        # Raise exception
            r'RAISE_APPLICATION_ERROR\s*\(',                    # Custom error
            r'SQLCODE',                                         # Error code
            r'SQLERRM',                                         # Error message
            r'NO_DATA_FOUND',                                   # No data exception
            r'TOO_MANY_ROWS',                                   # Too many rows
            r'DUP_VAL_ON_INDEX',                                # Duplicate key
            r'PRAGMA\s+EXCEPTION_INIT',                         # Exception init
        ],
        RuleType.CONSTRAINT: [
            r'CHECK\s*\(',                                      # Check constraint
            r'CONSTRAINT\s+\w+',                                # Named constraint
            r'PRIMARY\s+KEY',                                   # Primary key
            r'FOREIGN\s+KEY',                                   # Foreign key
            r'UNIQUE\s+',                                       # Unique constraint
            r'NOT\s+NULL',                                      # Not null constraint
            r'DEFAULT\s+',                                      # Default value
            r'REFERENCES\s+',                                   # Reference constraint
        ],
        RuleType.CALCULATION: [
            r':=\s*.+?[+\-*/]',                                 # Arithmetic assignment
            r'SUM\s*\(',                                        # Sum aggregate
            r'AVG\s*\(',                                        # Average
            r'ROUND\s*\(',                                      # Rounding
            r'CEIL\s*\(',                                       # Ceiling
            r'FLOOR\s*\(',                                      # Floor
            r'ABS\s*\(',                                        # Absolute value
            r'MOD\s*\(',                                        # Modulo
            r'POWER\s*\(',                                      # Power
            r'SQRT\s*\(',                                       # Square root
        ],
        RuleType.NAVIGATION: [
            r'RETURN\s+',                                       # Return statement
            r'RETURN;',                                         # Void return
            r'EXIT\s+WHEN',                                     # Exit loop condition
            r'EXIT;',                                           # Exit loop
            r'CONTINUE\s+WHEN',                                 # Continue condition
            r'CONTINUE;',                                       # Continue
            r'GOTO\s+\w+',                                      # Goto label
        ],
    }

    # Symbol detection patterns
    PACKAGE_PATTERN = re.compile(
        r'CREATE\s+(?:OR\s+REPLACE\s+)?PACKAGE\s+(BODY\s+)?(\w+(?:\.\w+)?)',
        re.IGNORECASE | re.MULTILINE
    )

    PROCEDURE_PATTERN = re.compile(
        r'(?:CREATE\s+(?:OR\s+REPLACE\s+)?)?PROCEDURE\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    FUNCTION_PATTERN = re.compile(
        r'(?:CREATE\s+(?:OR\s+REPLACE\s+)?)?FUNCTION\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    TRIGGER_PATTERN = re.compile(
        r'CREATE\s+(?:OR\s+REPLACE\s+)?TRIGGER\s+(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    TYPE_PATTERN = re.compile(
        r'CREATE\s+(?:OR\s+REPLACE\s+)?TYPE\s+(BODY\s+)?(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    COMMENT_BLOCK_PATTERN = re.compile(
        r'/\*[\s\S]*?\*/',
        re.MULTILINE
    )

    COMMENT_LINE_PATTERN = re.compile(
        r'--.*$',
        re.MULTILINE
    )

    def __init__(
        self,
        extraction_tier: ExtractionTier = ExtractionTier.FREE,
        project_id: Optional[int] = None,
    ):
        super().__init__(extraction_tier, project_id)
        self._compile_plsql_patterns()

    def _compile_plsql_patterns(self):
        """Compile PL/SQL specific patterns."""
        self._plsql_compiled: Dict[RuleType, List[re.Pattern]] = {}
        for rule_type, patterns in self.PLSQL_PATTERNS.items():
            self._plsql_compiled[rule_type] = [
                re.compile(p, re.IGNORECASE)
                for p in patterns
            ]

    def get_supported_extensions(self) -> List[str]:
        return self.SUPPORTED_EXTENSIONS

    def get_language(self) -> Language:
        return Language.PLSQL

    def get_rule_patterns(self) -> Dict[RuleType, List[str]]:
        """Return PL/SQL specific patterns."""
        return self.PLSQL_PATTERNS

    async def _extract_symbols(self, source: str, file_path: str) -> List[CodeSymbol]:
        """Extract code symbols from PL/SQL source."""
        symbols = []
        lines = source.split('\n')
        current_package = ""

        for i, line in enumerate(lines, 1):
            # Package
            pkg_match = self.PACKAGE_PATTERN.search(line)
            if pkg_match:
                is_body = bool(pkg_match.group(1))
                name = pkg_match.group(2)
                current_package = name
                symbols.append(CodeSymbol(
                    name=name,
                    symbol_type="package_body" if is_body else "package_spec",
                    line_start=i,
                    line_end=self._find_end_line(lines, i),
                    docstring=self._extract_header_comment(lines, i),
                    parent="",
                    language=Language.PLSQL,
                ))

            # Procedure (inside or outside package)
            proc_match = self.PROCEDURE_PATTERN.search(line)
            if proc_match and 'END ' not in line.upper():
                name = proc_match.group(1)
                symbols.append(CodeSymbol(
                    name=name,
                    symbol_type="procedure",
                    line_start=i,
                    line_end=self._find_proc_end_line(lines, i, name),
                    docstring=self._extract_header_comment(lines, i),
                    parent=current_package,
                    language=Language.PLSQL,
                ))

            # Function
            func_match = self.FUNCTION_PATTERN.search(line)
            if func_match and 'END ' not in line.upper():
                name = func_match.group(1)
                symbols.append(CodeSymbol(
                    name=name,
                    symbol_type="function",
                    line_start=i,
                    line_end=self._find_proc_end_line(lines, i, name),
                    docstring=self._extract_header_comment(lines, i),
                    parent=current_package,
                    language=Language.PLSQL,
                ))

            # Trigger
            trigger_match = self.TRIGGER_PATTERN.search(line)
            if trigger_match:
                name = trigger_match.group(1)
                symbols.append(CodeSymbol(
                    name=name,
                    symbol_type="trigger",
                    line_start=i,
                    line_end=self._find_end_line(lines, i),
                    docstring=self._extract_header_comment(lines, i),
                    parent="",
                    language=Language.PLSQL,
                ))

            # Type
            type_match = self.TYPE_PATTERN.search(line)
            if type_match:
                is_body = bool(type_match.group(1))
                name = type_match.group(2)
                symbols.append(CodeSymbol(
                    name=name,
                    symbol_type="type_body" if is_body else "type_spec",
                    line_start=i,
                    line_end=self._find_end_line(lines, i),
                    docstring=self._extract_header_comment(lines, i),
                    parent="",
                    language=Language.PLSQL,
                ))

        return symbols

    def _find_end_line(self, lines: List[str], start: int) -> int:
        """Find the END line for a PL/SQL block."""
        depth = 1
        end_pattern = re.compile(r'^\s*END\s*;?\s*$', re.IGNORECASE)
        begin_pattern = re.compile(r'\bBEGIN\b', re.IGNORECASE)

        for i in range(start, len(lines)):
            line = lines[i]

            # Track nested BEGIN blocks
            if begin_pattern.search(line) and i > start - 1:
                depth += 1

            if end_pattern.match(line.strip()) or line.strip().upper().startswith('END '):
                depth -= 1
                if depth == 0:
                    return i + 1

        return len(lines)

    def _find_proc_end_line(self, lines: List[str], start: int, name: str) -> int:
        """Find the END line for a specific procedure/function."""
        # Look for END <name>; or just END;
        end_pattern = re.compile(
            rf'^\s*END\s+{re.escape(name)}\s*;?|^\s*END\s*;?\s*$',
            re.IGNORECASE
        )

        depth = 0
        begin_seen = False

        for i in range(start, len(lines)):
            line = lines[i]

            if re.search(r'\bBEGIN\b', line, re.IGNORECASE):
                begin_seen = True
                depth += 1

            if begin_seen and re.search(r'\bEND\b', line, re.IGNORECASE):
                depth -= 1
                if depth == 0 or end_pattern.match(line.strip()):
                    return i + 1

        return len(lines)

    def _extract_header_comment(self, lines: List[str], start_line: int) -> str:
        """Extract any header comment before a procedure/function."""
        comments = []
        for i in range(start_line - 2, max(0, start_line - 20), -1):
            line = lines[i].strip()
            if line.startswith('--'):
                comments.insert(0, line[2:].strip())
            elif line.startswith('/*') or line.endswith('*/') or line.startswith('*'):
                comments.insert(0, line.replace('/*', '').replace('*/', '').replace('*', '').strip())
            elif line and not line.startswith('--') and not line.startswith('/*'):
                break
        return ' '.join(comments)

    async def _extract_rules_from_source(
        self,
        source: str,
        file_path: str,
        symbols: List[CodeSymbol]
    ) -> List[BusinessRule]:
        """Extract business rules from PL/SQL source."""
        rules = []
        lines = source.split('\n')
        in_comment_block = False

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Track block comments
            if '/*' in stripped and '*/' not in stripped:
                in_comment_block = True
            if '*/' in stripped:
                in_comment_block = False
                continue
            if in_comment_block:
                continue

            # Skip line comments
            if stripped.startswith('--'):
                continue

            # Try each rule type pattern
            for rule_type, patterns in self._plsql_compiled.items():
                for pattern in patterns:
                    match = pattern.search(line)
                    if match:
                        rule = self._create_rule_from_match(
                            match=match,
                            rule_type=rule_type,
                            line=line,
                            line_num=i,
                            lines=lines,
                            file_path=file_path,
                            symbols=symbols,
                        )
                        if rule:
                            rules.append(rule)
                        break  # Only one rule per line

        return rules

    def _create_rule_from_match(
        self,
        match: re.Match,
        rule_type: RuleType,
        line: str,
        line_num: int,
        lines: List[str],
        file_path: str,
        symbols: List[CodeSymbol],
    ) -> Optional[BusinessRule]:
        """Create a BusinessRule from a regex match."""

        # Extract condition
        condition = self._extract_condition(line, match, rule_type)

        # Extract action
        action = self._extract_action(line, lines, line_num, rule_type)

        # Extract variables
        variables = self._extract_variables(line)

        # Extract entities (table names)
        entities = self._extract_entities(line, variables)

        # Find parent symbol
        parent_class, parent_function = self._find_parent_symbol(line_num, symbols)

        # Calculate confidence
        confidence = self._calculate_confidence(
            rule_type=rule_type,
            condition=condition,
            variables=variables,
            has_clear_action=bool(action),
        )

        # Generate natural language
        natural_language = self._generate_natural_language(rule_type, condition, action)

        return BusinessRule(
            id=self._generate_rule_id(),
            rule_type=rule_type,
            condition=condition[:200],
            action=action[:200],
            source_file=file_path,
            source_lines=(line_num, line_num),
            confidence=confidence,
            natural_language=natural_language,
            variables_involved=variables[:10],
            related_entities=entities[:5],
            language=Language.PLSQL,
            extraction_method=ExtractionMethod.REGEX,
            extraction_tier=self.extraction_tier,
            code_snippet=line.strip()[:150],
            parent_function=parent_function,
            parent_class=parent_class,
        )

    def _extract_condition(self, line: str, match: re.Match, rule_type: RuleType) -> str:
        """Extract the condition from the matched line."""
        if rule_type == RuleType.VALIDATION:
            # Extract full IF condition
            if_match = re.search(r'(?:ELS)?IF\s+(.+?)\s+THEN', line, re.IGNORECASE)
            if if_match:
                return if_match.group(1).strip()

        if rule_type == RuleType.BRANCHING:
            # Extract CASE WHEN condition
            when_match = re.search(r'WHEN\s+(.+?)\s+THEN', line, re.IGNORECASE)
            if when_match:
                return when_match.group(1).strip()

        if rule_type == RuleType.DATA_ACCESS:
            # Extract table name from DML
            table_match = re.search(
                r'(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM|FROM|MERGE\s+INTO)\s+(\w+(?:\.\w+)?)',
                line, re.IGNORECASE
            )
            if table_match:
                return f"Table: {table_match.group(1)}"

        if rule_type == RuleType.ERROR_HANDLING:
            # Extract exception name
            when_match = re.search(r'WHEN\s+(\w+)\s+THEN', line, re.IGNORECASE)
            if when_match:
                return f"Exception: {when_match.group(1)}"

        return match.group(0).strip()

    def _extract_action(
        self,
        line: str,
        lines: List[str],
        line_num: int,
        rule_type: RuleType
    ) -> str:
        """Extract the action part of a rule."""

        # For IF statements in PL/SQL, action is after THEN (may be on same or next line)
        if 'THEN' in line.upper():
            then_idx = line.upper().find('THEN')
            after_then = line[then_idx + 4:].strip()
            if after_then:
                return after_then
            # Check next line
            if line_num < len(lines):
                next_line = lines[line_num].strip()
                if next_line and not next_line.startswith('--') and not next_line.upper().startswith('END'):
                    return next_line

        # For DML, the statement itself is the action
        if rule_type == RuleType.DATA_ACCESS:
            return line.strip()

        # For error handling, look at the next non-empty line
        if rule_type == RuleType.ERROR_HANDLING:
            for j in range(line_num, min(line_num + 3, len(lines))):
                next_line = lines[j].strip()
                if next_line and not next_line.startswith('--') and 'WHEN' not in next_line.upper():
                    return next_line

        # Check next line
        if line_num < len(lines):
            next_line = lines[line_num].strip()
            if next_line and not next_line.startswith('--'):
                return next_line

        return "execute"

    def _extract_variables(self, text: str) -> List[str]:
        """Extract variables from PL/SQL code."""
        variables = []

        # PL/SQL variable patterns (v_, p_, l_ prefixes common)
        var_patterns = [
            r'\b(v_\w+)',                                       # Local variables
            r'\b(p_\w+)',                                       # Parameters
            r'\b(l_\w+)',                                       # Local variables alt
            r'\b(g_\w+)',                                       # Global variables
            r'\b(c_\w+)',                                       # Constants
            r'\b([a-z_]\w*)\s*:=',                              # Assignment targets
        ]

        for pattern in var_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            variables.extend(matches)

        # PL/SQL keywords to exclude
        keywords = {
            'if', 'then', 'else', 'elsif', 'end', 'select', 'from', 'where',
            'and', 'or', 'not', 'in', 'is', 'null', 'like', 'between',
            'insert', 'into', 'update', 'set', 'delete', 'values',
            'join', 'left', 'right', 'inner', 'outer', 'on', 'as',
            'create', 'replace', 'alter', 'drop', 'table', 'view',
            'procedure', 'function', 'package', 'body', 'trigger',
            'begin', 'declare', 'exception', 'when', 'others', 'raise',
            'return', 'returns', 'cursor', 'for', 'loop', 'while',
            'exit', 'continue', 'goto', 'case', 'open', 'close', 'fetch',
            'number', 'varchar2', 'varchar', 'char', 'nchar', 'clob', 'blob',
            'date', 'timestamp', 'boolean', 'integer', 'pls_integer',
            'binary_integer', 'natural', 'positive', 'real', 'float',
            'sysdate', 'systimestamp', 'user', 'rowcount', 'found', 'notfound',
        }

        return [v for v in variables if v.lower() not in keywords]

    def _extract_entities(self, text: str, variables: List[str]) -> List[str]:
        """Extract table/entity names from PL/SQL code."""
        entities = set()

        # Table name patterns
        table_patterns = [
            r'\b(?:FROM|JOIN|INTO|UPDATE|MERGE\s+INTO)\s+(\w+(?:\.\w+)?)',
            r'\bta_?([A-Z][a-z]+\w*)',                          # HCI-style prefix
            r'\btbl_?([A-Z][a-z]+)',                            # Common table prefix
            r'\b([A-Z][a-z]+)(?:_ID|ID)\b',                     # Entity ID columns
            r'%TYPE\b.*?(\w+)\.',                               # Type reference
            r'%ROWTYPE\b.*?(\w+)',                              # Rowtype reference
        ]

        for pattern in table_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else (match[1] if len(match) > 1 else '')
                if match and len(match) > 2:
                    entities.add(match)

        return list(entities)
