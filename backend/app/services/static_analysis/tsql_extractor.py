# backend/app/services/static_analysis/tsql_extractor.py
"""
T-SQL Business Rule Extractor - Extracts business rules from T-SQL stored procedures.

Part of Week 111-114: Hybrid Business Rule Extraction Pipeline - Phase 2

Supports:
- T-SQL stored procedures (.sql, .prc)
- SQL Server scripts

Detection patterns:
- IF-ELSE blocks with business logic
- CASE WHEN statements
- Constraint checks (CHECK, WHERE conditions)
- Transaction boundaries (BEGIN TRAN, COMMIT, ROLLBACK)
- Error handling (TRY-CATCH, RAISERROR, THROW)
- Authorization (EXECUTE AS, HAS_PERMS_BY_NAME)
- Trigger logic (INSERT, UPDATE, DELETE triggers)
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


class TSQLBusinessRuleExtractor(BaseBusinessRuleExtractor):
    """
    Extracts business rules from T-SQL stored procedures and scripts.

    Uses regex-enhanced extraction (Tier 2) with optional LLM validation.
    Designed for SQL Server stored procedures with business logic.
    """

    SUPPORTED_EXTENSIONS = ['.sql', '.prc']

    # T-SQL specific patterns for rule detection
    TSQL_PATTERNS: Dict[RuleType, List[str]] = {
        RuleType.VALIDATION: [
            r'IF\s+(.+?)\s+BEGIN',                              # IF block start
            r'IF\s+(.+?)\s*\n',                                 # Single line IF
            r'IF\s+NOT\s+EXISTS\s*\(',                          # Existence check
            r'IF\s+EXISTS\s*\(',                                # Existence check
            r'IF\s+@@ROWCOUNT',                                 # Row count check
            r'IF\s+@@ERROR',                                    # Error check
            r'IF\s+@\w+\s*(IS\s+NULL|=\s*NULL)',                # Null check
            r'IF\s+@\w+\s*(IS\s+NOT\s+NULL|<>\s*NULL)',         # Not null check
            r'IF\s+LEN\s*\(@\w+\)',                             # Length check
            r'IF\s+ISNULL\s*\(',                                # ISNULL check
            r'WHERE\s+.+?(?:AND|OR)',                           # Complex WHERE
        ],
        RuleType.AUTHORIZATION: [
            r'EXECUTE\s+AS\s+',                                 # Execute as context
            r'HAS_PERMS_BY_NAME\s*\(',                          # Permission check
            r'IS_MEMBER\s*\(',                                  # Role membership
            r'IS_SRVROLEMEMBER\s*\(',                           # Server role check
            r'SUSER_SNAME\s*\(',                                # Security user
            r'USER_NAME\s*\(',                                  # User name check
            r'GRANT\s+',                                        # Grant permission
            r'DENY\s+',                                         # Deny permission
            r'REVOKE\s+',                                       # Revoke permission
            r'@intCan\w+',                                      # HCI-CRS permission var
            r'@CanView|@CanEdit|@CanDelete|@CanAdd',            # Permission flags
        ],
        RuleType.SCHEDULING: [
            r'GETDATE\s*\(\)',                                  # Current date/time
            r'DATEADD\s*\(',                                    # Date arithmetic
            r'DATEDIFF\s*\(',                                   # Date difference
            r'@StartDate|@EndDate',                             # Date parameters
            r'@StartTime|@EndTime',                             # Time parameters
            r'@datStart|@datEnd|@datumVan|@datumTot',           # Dutch date vars
            r'CONVERT\s*\(\s*date',                             # Date conversion
            r'CONVERT\s*\(\s*datetime',                         # Datetime conversion
        ],
        RuleType.WORKFLOW: [
            r'@Status\s*(=|<>)',                                # Status check
            r'SET\s+@Status\s*=',                               # Status assignment
            r"Status\s*=\s*'(\w+)'",                            # Status literal
            r'@State\s*(=|<>)',                                 # State check
            r'UPDATE\s+.+?\s+SET\s+.+?Status',                  # Status update
        ],
        RuleType.BRANCHING: [
            r'CASE\s+WHEN',                                     # CASE WHEN start
            r'WHEN\s+.+?\s+THEN',                               # WHEN clause
            r'ELSE\s+',                                         # ELSE clause
            r'END\s*(?:AS|$)',                                  # CASE END
            r'IF\s+.+?\s+ELSE\s+IF',                            # Chained IF-ELSE
        ],
        RuleType.THRESHOLD: [
            r'@\w+\s*(>=|<=|>|<|=)\s*(\d+)',                    # Numeric comparison
            r'COUNT\s*\(.+?\)\s*(>=|<=|>|<|=)\s*(\d+)',         # Count threshold
            r'SUM\s*\(.+?\)\s*(>=|<=|>|<|=)',                   # Sum threshold
            r'MAX\s*\(.+?\)\s*(>=|<=|>|<|=)',                   # Max threshold
            r'MIN\s*\(.+?\)\s*(>=|<=|>|<|=)',                   # Min threshold
            r'AVG\s*\(.+?\)\s*(>=|<=|>|<|=)',                   # Average threshold
            r'TOP\s+(\d+)',                                     # TOP clause
        ],
        RuleType.DATA_ACCESS: [
            r'INSERT\s+INTO\s+(\w+)',                           # Insert statement
            r'UPDATE\s+(\w+)\s+SET',                            # Update statement
            r'DELETE\s+FROM\s+(\w+)',                           # Delete statement
            r'SELECT\s+.+?\s+FROM\s+(\w+)',                     # Select statement
            r'EXEC\s+(\w+)',                                    # Execute procedure
            r'EXECUTE\s+(\w+)',                                 # Execute procedure
            r'sp_executesql',                                   # Dynamic SQL
            r'MERGE\s+INTO\s+(\w+)',                            # Merge statement
            r'TRUNCATE\s+TABLE\s+(\w+)',                        # Truncate
        ],
        RuleType.STATE_MANAGEMENT: [
            r'SET\s+@\w+\s*=',                                  # Variable assignment
            r'DECLARE\s+@\w+',                                  # Variable declaration
            r'SELECT\s+@\w+\s*=',                               # Variable from select
            r'CURSOR\s+',                                       # Cursor usage
            r'FETCH\s+',                                        # Cursor fetch
            r'@@IDENTITY',                                      # Last identity
            r'SCOPE_IDENTITY\s*\(\)',                           # Scope identity
            r'@@TRANCOUNT',                                     # Transaction count
        ],
        RuleType.ERROR_HANDLING: [
            r'BEGIN\s+TRY',                                     # Try block
            r'END\s+TRY',                                       # End try
            r'BEGIN\s+CATCH',                                   # Catch block
            r'END\s+CATCH',                                     # End catch
            r'RAISERROR\s*\(',                                  # Raise error
            r'THROW\s+',                                        # Throw error
            r'@@ERROR',                                         # Error number
            r'ERROR_MESSAGE\s*\(\)',                            # Error message
            r'ERROR_NUMBER\s*\(\)',                             # Error number func
            r'ERROR_SEVERITY\s*\(\)',                           # Error severity
            r'XACT_ABORT',                                      # Transaction abort
        ],
        RuleType.CONSTRAINT: [
            r'CHECK\s*\(',                                      # Check constraint
            r'CONSTRAINT\s+\w+',                                # Named constraint
            r'PRIMARY\s+KEY',                                   # Primary key
            r'FOREIGN\s+KEY',                                   # Foreign key
            r'UNIQUE\s+',                                       # Unique constraint
            r'NOT\s+NULL',                                      # Not null constraint
            r'DEFAULT\s+',                                      # Default constraint
            r'REFERENCES\s+',                                   # Reference constraint
        ],
        RuleType.CALCULATION: [
            r'SET\s+@\w+\s*=\s*@\w+\s*[+\-*/]',                  # Arithmetic
            r'SELECT\s+.+?[+\-*/].+?\s+AS',                     # Calculated column
            r'SUM\s*\(',                                        # Sum aggregate
            r'AVG\s*\(',                                        # Average
            r'ROUND\s*\(',                                      # Rounding
            r'CEILING\s*\(',                                    # Ceiling
            r'FLOOR\s*\(',                                      # Floor
            r'ABS\s*\(',                                        # Absolute value
        ],
        RuleType.NAVIGATION: [
            r'RETURN\s+',                                       # Return statement
            r'GOTO\s+\w+',                                      # Goto label
            r'BREAK',                                           # Break loop
            r'CONTINUE',                                        # Continue loop
        ],
    }

    # Symbol detection patterns
    PROCEDURE_PATTERN = re.compile(
        r'CREATE\s+(OR\s+ALTER\s+)?PROC(?:EDURE)?\s+(\[?\w+\]?\.)?(\[?\w+\]?)',
        re.IGNORECASE | re.MULTILINE
    )

    FUNCTION_PATTERN = re.compile(
        r'CREATE\s+(OR\s+ALTER\s+)?FUNCTION\s+(\[?\w+\]?\.)?(\[?\w+\]?)',
        re.IGNORECASE | re.MULTILINE
    )

    TRIGGER_PATTERN = re.compile(
        r'CREATE\s+(OR\s+ALTER\s+)?TRIGGER\s+(\[?\w+\]?\.)?(\[?\w+\]?)',
        re.IGNORECASE | re.MULTILINE
    )

    VIEW_PATTERN = re.compile(
        r'CREATE\s+(OR\s+ALTER\s+)?VIEW\s+(\[?\w+\]?\.)?(\[?\w+\]?)',
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
        self._compile_tsql_patterns()

    def _compile_tsql_patterns(self):
        """Compile T-SQL specific patterns."""
        self._tsql_compiled: Dict[RuleType, List[re.Pattern]] = {}
        for rule_type, patterns in self.TSQL_PATTERNS.items():
            self._tsql_compiled[rule_type] = [
                re.compile(p, re.IGNORECASE)
                for p in patterns
            ]

    def get_supported_extensions(self) -> List[str]:
        return self.SUPPORTED_EXTENSIONS

    def get_language(self) -> Language:
        return Language.TSQL

    def get_rule_patterns(self) -> Dict[RuleType, List[str]]:
        """Return T-SQL specific patterns."""
        return self.TSQL_PATTERNS

    async def _extract_symbols(self, source: str, file_path: str) -> List[CodeSymbol]:
        """Extract code symbols from T-SQL source."""
        symbols = []
        lines = source.split('\n')

        # Remove block comments for cleaner parsing
        clean_source = self.COMMENT_BLOCK_PATTERN.sub('', source)

        for i, line in enumerate(lines, 1):
            # Stored Procedure
            proc_match = self.PROCEDURE_PATTERN.search(line)
            if proc_match:
                name = proc_match.group(3).replace('[', '').replace(']', '')
                symbols.append(CodeSymbol(
                    name=name,
                    symbol_type="procedure",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'GO'),
                    docstring=self._extract_header_comment(lines, i),
                    parent="",
                    language=Language.TSQL,
                ))

            # Function
            func_match = self.FUNCTION_PATTERN.search(line)
            if func_match:
                name = func_match.group(3).replace('[', '').replace(']', '')
                symbols.append(CodeSymbol(
                    name=name,
                    symbol_type="function",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'GO'),
                    docstring=self._extract_header_comment(lines, i),
                    parent="",
                    language=Language.TSQL,
                ))

            # Trigger
            trigger_match = self.TRIGGER_PATTERN.search(line)
            if trigger_match:
                name = trigger_match.group(3).replace('[', '').replace(']', '')
                symbols.append(CodeSymbol(
                    name=name,
                    symbol_type="trigger",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'GO'),
                    docstring=self._extract_header_comment(lines, i),
                    parent="",
                    language=Language.TSQL,
                ))

            # View
            view_match = self.VIEW_PATTERN.search(line)
            if view_match:
                name = view_match.group(3).replace('[', '').replace(']', '')
                symbols.append(CodeSymbol(
                    name=name,
                    symbol_type="view",
                    line_start=i,
                    line_end=self._find_end_line(lines, i, 'GO'),
                    docstring=self._extract_header_comment(lines, i),
                    parent="",
                    language=Language.TSQL,
                ))

        return symbols

    def _find_end_line(self, lines: List[str], start: int, terminator: str = 'GO') -> int:
        """Find the end line for a T-SQL block (GO statement or EOF)."""
        for i in range(start, len(lines)):
            if lines[i].strip().upper() == terminator:
                return i + 1
        return len(lines)

    def _extract_header_comment(self, lines: List[str], start_line: int) -> str:
        """Extract any header comment before a stored procedure."""
        comments = []
        for i in range(start_line - 2, max(0, start_line - 15), -1):
            line = lines[i].strip()
            if line.startswith('--'):
                comments.insert(0, line[2:].strip())
            elif line.startswith('/*') or line.endswith('*/') or line.startswith('*'):
                # Part of block comment
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
        """Extract business rules from T-SQL source."""
        rules = []
        lines = source.split('\n')
        in_comment_block = False

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Track block comments
            if '/*' in stripped:
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
            for rule_type, patterns in self._tsql_compiled.items():
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

        # Find parent symbol (stored procedure)
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
            language=Language.TSQL,
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
            if_match = re.search(r'IF\s+(.+?)(?:\s+BEGIN|\s*$)', line, re.IGNORECASE)
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
                r'(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM|FROM|MERGE\s+INTO)\s+(\[?\w+\]?(?:\.\[?\w+\]?)?)',
                line, re.IGNORECASE
            )
            if table_match:
                return f"Table: {table_match.group(1)}"

        return match.group(0).strip()

    def _extract_action(
        self,
        line: str,
        lines: List[str],
        line_num: int,
        rule_type: RuleType
    ) -> str:
        """Extract the action part of a rule."""

        # For IF statements, look for the action after BEGIN or on same line
        if 'IF ' in line.upper():
            if 'BEGIN' in line.upper():
                # Action is on next line(s)
                if line_num < len(lines):
                    next_line = lines[line_num].strip()
                    if next_line and not next_line.startswith('--'):
                        return next_line
            else:
                # Single-line IF: extract after condition
                parts = line.split(' ')
                # Find the action after the condition
                for j, part in enumerate(parts):
                    if part.upper() in ('SELECT', 'SET', 'EXEC', 'RETURN', 'RAISERROR', 'THROW'):
                        return ' '.join(parts[j:])

        # For CASE WHEN, extract THEN part
        if 'THEN ' in line.upper():
            then_match = re.search(r'THEN\s+(.+?)(?:\s*$|WHEN|ELSE|END)', line, re.IGNORECASE)
            if then_match:
                return then_match.group(1).strip()

        # For DML, the statement itself is the action
        if rule_type == RuleType.DATA_ACCESS:
            return line.strip()

        # Check next line
        if line_num < len(lines):
            next_line = lines[line_num].strip()
            if next_line and not next_line.startswith('--'):
                return next_line

        return "execute"

    def _extract_variables(self, text: str) -> List[str]:
        """Extract variables from T-SQL code."""
        # T-SQL variable pattern (@varname)
        pattern = r'@([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(pattern, text)

        # Also extract column/table references
        col_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        col_matches = re.findall(col_pattern, text)

        # T-SQL keywords to exclude
        keywords = {
            'if', 'else', 'begin', 'end', 'select', 'from', 'where',
            'and', 'or', 'not', 'in', 'is', 'null', 'like', 'between',
            'insert', 'into', 'update', 'set', 'delete', 'values',
            'join', 'left', 'right', 'inner', 'outer', 'on', 'as',
            'create', 'alter', 'drop', 'table', 'view', 'procedure',
            'function', 'trigger', 'index', 'constraint', 'primary',
            'foreign', 'key', 'references', 'unique', 'check', 'default',
            'exec', 'execute', 'declare', 'return', 'returns',
            'try', 'catch', 'throw', 'raiserror', 'error', 'goto',
            'while', 'for', 'case', 'when', 'then', 'else', 'go',
            'int', 'varchar', 'nvarchar', 'char', 'nchar', 'text',
            'datetime', 'date', 'time', 'bit', 'decimal', 'float',
            'money', 'smallint', 'bigint', 'tinyint', 'real',
            'identity', 'getdate', 'scope_identity', 'rowcount',
        }

        all_vars = ['@' + m for m in matches]
        all_vars.extend([m for m in col_matches if m.lower() not in keywords])

        return list(set(all_vars))

    def _extract_entities(self, text: str, variables: List[str]) -> List[str]:
        """Extract table/entity names from T-SQL code."""
        entities = set()

        # Table name patterns
        table_patterns = [
            r'\b(?:FROM|JOIN|INTO|UPDATE|MERGE\s+INTO)\s+(\[?[a-zA-Z_]\w*\]?(?:\.\[?[a-zA-Z_]\w*\]?)?)',
            r'\bta([A-Z][a-z]+\w*)',                    # HCI-CRS table prefix
            r'\btbl([A-Z][a-z]+)',                      # Common table prefix
            r'\b([A-Z][a-z]+)(?:ID|Id)\b',              # Entity ID columns
        ]

        for pattern in table_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else (match[1] if len(match) > 1 else '')
                if match:
                    clean = match.replace('[', '').replace(']', '')
                    if clean and len(clean) > 2:
                        entities.add(clean)

        return list(entities)
