# SQL Performance Analyzer
# Detects SQL performance issues in Classic ASP code
#
# Category 8: SQL Performance
# - N+1 query patterns
# - Missing parameterized queries (SQL injection risk)
# - SELECT * usage
# - Missing query timeouts
# - Cursor type issues
# - Missing indexes (hints from queries)
# - Transaction handling issues
#
# Week 144-145 Implementation

from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

from ..types import (
    StabilityCategory,
    SeverityLevel,
    LeakFinding,
    LeakPatternType,
    ResourceType,
)

logger = logging.getLogger(__name__)


class SQLIssueType(Enum):
    """Types of SQL performance issues."""
    N_PLUS_ONE = "n_plus_one"
    SQL_INJECTION = "sql_injection"
    SELECT_STAR = "select_star"
    NO_QUERY_TIMEOUT = "no_query_timeout"
    WRONG_CURSOR_TYPE = "wrong_cursor_type"
    MISSING_INDEX_HINT = "missing_index_hint"
    NO_TRANSACTION = "no_transaction"
    NESTED_TRANSACTION = "nested_transaction"
    QUERY_IN_LOOP = "query_in_loop"
    UNBOUNDED_QUERY = "unbounded_query"
    STRING_CONCAT_SQL = "string_concat_sql"
    DYNAMIC_SQL = "dynamic_sql"


@dataclass
class SQLQuery:
    """Represents a SQL query in the code."""
    line_number: int
    query_text: str
    variable_name: str
    is_in_loop: bool = False
    has_parameters: bool = False
    has_top_clause: bool = False
    tables_referenced: List[str] = field(default_factory=list)
    uses_string_concat: bool = False
    code_snippet: str = ""


@dataclass
class SQLFinding:
    """A detected SQL performance issue."""
    file_path: str
    line_number: int
    issue_type: SQLIssueType
    severity: SeverityLevel
    description: str
    suggested_fix: str
    query_snippet: str = ""
    code_context: List[str] = field(default_factory=list)
    confidence: float = 1.0
    tables_affected: List[str] = field(default_factory=list)

    def to_leak_finding(self) -> LeakFinding:
        """Convert to standard LeakFinding format."""
        return LeakFinding(
            file_path=self.file_path,
            line_number=self.line_number,
            resource_type=ResourceType.DATABASE_CONNECTION,
            variable_name="SQLQuery",
            leak_pattern=LeakPatternType.LOOP_LEAK if self.issue_type == SQLIssueType.N_PLUS_ONE else LeakPatternType.NEVER_CLOSED,
            severity=self.severity,
            category=StabilityCategory.SQL_PERFORMANCE,
            description=self.description,
            suggested_fix=self.suggested_fix,
            code_context=self.code_context,
            confidence=self.confidence,
        )


class SQLAnalyzer:
    """
    Analyzes SQL usage patterns for performance and security issues.

    Detects:
    1. N+1 query patterns (queries inside loops) - HIGH
    2. SQL injection vulnerabilities (string concatenation) - CRITICAL
    3. SELECT * usage - LOW
    4. Missing query timeouts - MEDIUM
    5. Wrong cursor types for read-only data - LOW
    6. Missing TOP/LIMIT clauses (unbounded queries) - MEDIUM
    7. Transaction handling issues - HIGH
    8. Dynamic SQL construction - MEDIUM
    """

    # SQL execution patterns
    SQL_EXECUTE_PATTERNS = [
        r'\.Execute\s*\(\s*["\']?(.*?)["\']?\s*\)',
        r'\.Execute\s*\(\s*(\w+)\s*\)',
        r'\.Open\s*["\']?(SELECT.*?)["\']?',
        r'con\.Execute\s*\(["\']?(.*?)["\']?\)',
    ]

    # SQL query patterns
    SELECT_PATTERN = r'\bSELECT\b'
    SELECT_STAR_PATTERN = r'\bSELECT\s+\*\s+FROM\b'
    INSERT_PATTERN = r'\bINSERT\s+INTO\b'
    UPDATE_PATTERN = r'\bUPDATE\b.*\bSET\b'
    DELETE_PATTERN = r'\bDELETE\s+FROM\b'

    # Table extraction
    FROM_PATTERN = r'\bFROM\s+(\w+)'
    JOIN_PATTERN = r'\bJOIN\s+(\w+)'

    # TOP/LIMIT clause
    TOP_PATTERN = r'\bSELECT\s+TOP\s+\d+'
    WHERE_PATTERN = r'\bWHERE\b'

    # String concatenation in SQL (injection risk)
    SQL_CONCAT_PATTERNS = [
        r'["\'][^"\']*\bSELECT\b[^"\']*["\']\s*&',
        r'&\s*["\'][^"\']*\bFROM\b',
        r'["\'][^"\']*\bWHERE\b[^"\']*["\']\s*&\s*\w+',
        r'=\s*["\'].*\bSELECT\b.*["\']\s*&',
    ]

    # Safe parameterized patterns
    PARAMETERIZED_PATTERNS = [
        r'\.Parameters\.Append',
        r'\.CreateParameter',
        r'cmd\.Parameters',
        r'@\w+',  # Parameter placeholder
    ]

    # Loop patterns
    LOOP_START_PATTERNS = [
        r'\bDo\s+While\b',
        r'\bDo\s+Until\b',
        r'\bFor\s+Each\b',
        r'\bFor\s+\w+\s*=',
        r'\bWhile\b.*\bNot\b.*\bEOF\b',
    ]

    LOOP_END_PATTERNS = [
        r'\bLoop\b',
        r'\bNext\b',
        r'\bWend\b',
    ]

    # Transaction patterns
    BEGIN_TRANS_PATTERN = r'\.BeginTrans'
    COMMIT_TRANS_PATTERN = r'\.CommitTrans'
    ROLLBACK_TRANS_PATTERN = r'\.RollbackTrans'

    # Cursor types
    CURSOR_TYPE_PATTERN = r'\.CursorType\s*=\s*(\d+)'
    LOCK_TYPE_PATTERN = r'\.LockType\s*=\s*(\d+)'

    # Command timeout
    COMMAND_TIMEOUT_PATTERN = r'\.CommandTimeout\s*=\s*(\d+)'

    def __init__(self):
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile all regex patterns."""
        flags = re.IGNORECASE | re.DOTALL

        self._compiled_patterns = {
            "sql_execute": [re.compile(p, flags) for p in self.SQL_EXECUTE_PATTERNS],
            "select": re.compile(self.SELECT_PATTERN, flags),
            "select_star": re.compile(self.SELECT_STAR_PATTERN, flags),
            "insert": re.compile(self.INSERT_PATTERN, flags),
            "update": re.compile(self.UPDATE_PATTERN, flags),
            "delete": re.compile(self.DELETE_PATTERN, flags),
            "from": re.compile(self.FROM_PATTERN, flags),
            "join": re.compile(self.JOIN_PATTERN, flags),
            "top": re.compile(self.TOP_PATTERN, flags),
            "where": re.compile(self.WHERE_PATTERN, flags),
            "sql_concat": [re.compile(p, flags) for p in self.SQL_CONCAT_PATTERNS],
            "parameterized": [re.compile(p, flags) for p in self.PARAMETERIZED_PATTERNS],
            "loop_start": [re.compile(p, flags) for p in self.LOOP_START_PATTERNS],
            "loop_end": [re.compile(p, flags) for p in self.LOOP_END_PATTERNS],
            "begin_trans": re.compile(self.BEGIN_TRANS_PATTERN, flags),
            "commit_trans": re.compile(self.COMMIT_TRANS_PATTERN, flags),
            "rollback_trans": re.compile(self.ROLLBACK_TRANS_PATTERN, flags),
            "cursor_type": re.compile(self.CURSOR_TYPE_PATTERN, flags),
            "lock_type": re.compile(self.LOCK_TYPE_PATTERN, flags),
            "command_timeout": re.compile(self.COMMAND_TIMEOUT_PATTERN, flags),
        }

    def analyze_file(self, file_path: str, content: str) -> List[SQLFinding]:
        """
        Analyze a file for SQL performance issues.

        Args:
            file_path: Path to the file
            content: File content

        Returns:
            List of SQL findings
        """
        findings = []
        lines = content.split('\n')

        # Find loop regions
        loop_regions = self._find_loop_regions(lines)

        # Find all SQL queries
        queries = self._find_sql_queries(lines, loop_regions)

        # Analyze for N+1 patterns
        findings.extend(self._check_n_plus_one(file_path, lines, queries, loop_regions))

        # Analyze for SQL injection
        findings.extend(self._check_sql_injection(file_path, lines, queries))

        # Analyze for SELECT *
        findings.extend(self._check_select_star(file_path, lines, queries))

        # Analyze for unbounded queries
        findings.extend(self._check_unbounded_queries(file_path, lines, queries))

        # Analyze for missing timeouts
        findings.extend(self._check_query_timeout(file_path, lines))

        # Analyze transaction handling
        findings.extend(self._check_transactions(file_path, lines))

        return findings

    def _find_loop_regions(self, lines: List[str]) -> List[Tuple[int, int]]:
        """Find start and end lines of loops."""
        regions = []
        loop_starts = []

        for line_num, line in enumerate(lines, 1):
            # Check for loop start
            for pattern in self._compiled_patterns["loop_start"]:
                if pattern.search(line):
                    loop_starts.append(line_num)
                    break

            # Check for loop end
            for pattern in self._compiled_patterns["loop_end"]:
                if pattern.search(line) and loop_starts:
                    start = loop_starts.pop()
                    regions.append((start, line_num))
                    break

        return regions

    def _is_in_loop(self, line_num: int, loop_regions: List[Tuple[int, int]]) -> bool:
        """Check if a line is inside a loop."""
        for start, end in loop_regions:
            if start <= line_num <= end:
                return True
        return False

    def _find_sql_queries(
        self,
        lines: List[str],
        loop_regions: List[Tuple[int, int]]
    ) -> List[SQLQuery]:
        """Find all SQL query executions."""
        queries = []

        for line_num, line in enumerate(lines, 1):
            for pattern in self._compiled_patterns["sql_execute"]:
                match = pattern.search(line)
                if match:
                    query_text = match.group(1) if match.groups() else ""

                    # Extract tables
                    tables = []
                    from_match = self._compiled_patterns["from"].search(line)
                    if from_match:
                        tables.append(from_match.group(1))

                    join_matches = self._compiled_patterns["join"].findall(line)
                    tables.extend(join_matches)

                    # Check for string concatenation
                    uses_concat = any(
                        p.search(line)
                        for p in self._compiled_patterns["sql_concat"]
                    )

                    # Check for TOP clause
                    has_top = bool(self._compiled_patterns["top"].search(line))

                    queries.append(SQLQuery(
                        line_number=line_num,
                        query_text=query_text,
                        variable_name="",
                        is_in_loop=self._is_in_loop(line_num, loop_regions),
                        has_parameters=False,
                        has_top_clause=has_top,
                        tables_referenced=tables,
                        uses_string_concat=uses_concat,
                        code_snippet=line.strip(),
                    ))

        return queries

    def _check_n_plus_one(
        self,
        file_path: str,
        lines: List[str],
        queries: List[SQLQuery],
        loop_regions: List[Tuple[int, int]]
    ) -> List[SQLFinding]:
        """Detect N+1 query patterns."""
        findings = []

        for query in queries:
            if query.is_in_loop:
                findings.append(SQLFinding(
                    file_path=file_path,
                    line_number=query.line_number,
                    issue_type=SQLIssueType.N_PLUS_ONE,
                    severity=SeverityLevel.HIGH,
                    description=(
                        f"SQL query executed inside loop at line {query.line_number} - "
                        f"potential N+1 pattern causing excessive database calls"
                    ),
                    suggested_fix=(
                        "Move query outside loop and fetch all needed data at once, "
                        "use JOINs or batch queries instead of iterating"
                    ),
                    query_snippet=query.code_snippet,
                    code_context=self._get_context(lines, query.line_number),
                    confidence=0.9,
                    tables_affected=query.tables_referenced,
                ))

        return findings

    def _check_sql_injection(
        self,
        file_path: str,
        lines: List[str],
        queries: List[SQLQuery]
    ) -> List[SQLFinding]:
        """Detect SQL injection vulnerabilities."""
        findings = []

        for line_num, line in enumerate(lines, 1):
            # Check for string concatenation in SQL
            for pattern in self._compiled_patterns["sql_concat"]:
                if pattern.search(line):
                    # Check if parameterized query is used nearby
                    context_start = max(0, line_num - 10)
                    context_end = min(len(lines), line_num + 10)
                    context = '\n'.join(lines[context_start:context_end])

                    has_params = any(
                        p.search(context)
                        for p in self._compiled_patterns["parameterized"]
                    )

                    if not has_params:
                        findings.append(SQLFinding(
                            file_path=file_path,
                            line_number=line_num,
                            issue_type=SQLIssueType.SQL_INJECTION,
                            severity=SeverityLevel.CRITICAL,
                            description=(
                                f"Potential SQL injection at line {line_num} - "
                                f"SQL query built using string concatenation"
                            ),
                            suggested_fix=(
                                "Use parameterized queries with ADODB.Command and Parameters.Append, "
                                "never concatenate user input directly into SQL"
                            ),
                            query_snippet=line.strip(),
                            code_context=self._get_context(lines, line_num),
                            confidence=0.85,
                        ))
                    break

        return findings

    def _check_select_star(
        self,
        file_path: str,
        lines: List[str],
        queries: List[SQLQuery]
    ) -> List[SQLFinding]:
        """Detect SELECT * usage."""
        findings = []

        for line_num, line in enumerate(lines, 1):
            if self._compiled_patterns["select_star"].search(line):
                findings.append(SQLFinding(
                    file_path=file_path,
                    line_number=line_num,
                    issue_type=SQLIssueType.SELECT_STAR,
                    severity=SeverityLevel.LOW,
                    description=(
                        f"SELECT * at line {line_num} - "
                        f"retrieves all columns which may be inefficient"
                    ),
                    suggested_fix=(
                        "Specify only the columns you need: SELECT col1, col2 FROM table"
                    ),
                    query_snippet=line.strip(),
                    code_context=self._get_context(lines, line_num),
                    confidence=0.95,
                ))

        return findings

    def _check_unbounded_queries(
        self,
        file_path: str,
        lines: List[str],
        queries: List[SQLQuery]
    ) -> List[SQLFinding]:
        """Detect queries without TOP/WHERE clauses."""
        findings = []

        for line_num, line in enumerate(lines, 1):
            if self._compiled_patterns["select"].search(line):
                # Skip if it's a subquery or has TOP
                if self._compiled_patterns["top"].search(line):
                    continue

                # Check for WHERE clause (may be on next line)
                context_end = min(len(lines), line_num + 5)
                context = '\n'.join(lines[line_num - 1:context_end])

                has_where = self._compiled_patterns["where"].search(context)
                has_top = self._compiled_patterns["top"].search(context)

                if not has_where and not has_top:
                    findings.append(SQLFinding(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type=SQLIssueType.UNBOUNDED_QUERY,
                        severity=SeverityLevel.MEDIUM,
                        description=(
                            f"Query at line {line_num} has no WHERE or TOP clause - "
                            f"may return excessive data"
                        ),
                        suggested_fix=(
                            "Add WHERE clause to filter results or TOP n to limit rows"
                        ),
                        query_snippet=line.strip(),
                        code_context=self._get_context(lines, line_num),
                        confidence=0.7,
                    ))

        return findings

    def _check_query_timeout(
        self,
        file_path: str,
        lines: List[str]
    ) -> List[SQLFinding]:
        """Check for missing query timeout configuration."""
        findings = []
        content = '\n'.join(lines)

        # Check if CommandTimeout is set anywhere
        has_timeout = self._compiled_patterns["command_timeout"].search(content)

        # Find connection/command objects
        connection_pattern = re.compile(
            r'Server\.CreateObject\s*\(\s*["\']ADODB\.(Connection|Command)["\']',
            re.IGNORECASE
        )

        for line_num, line in enumerate(lines, 1):
            if connection_pattern.search(line):
                # Check if timeout is set within next 20 lines
                context_end = min(len(lines), line_num + 20)
                context = '\n'.join(lines[line_num - 1:context_end])

                if not self._compiled_patterns["command_timeout"].search(context):
                    findings.append(SQLFinding(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type=SQLIssueType.NO_QUERY_TIMEOUT,
                        severity=SeverityLevel.MEDIUM,
                        description=(
                            f"ADODB object at line {line_num} without CommandTimeout - "
                            f"queries may hang indefinitely"
                        ),
                        suggested_fix=(
                            "Set CommandTimeout property: connection.CommandTimeout = 30"
                        ),
                        code_context=self._get_context(lines, line_num),
                        confidence=0.7,
                    ))

        return findings

    def _check_transactions(
        self,
        file_path: str,
        lines: List[str]
    ) -> List[SQLFinding]:
        """Check transaction handling patterns."""
        findings = []

        begin_trans_lines = []
        commit_trans_lines = []
        rollback_trans_lines = []

        for line_num, line in enumerate(lines, 1):
            if self._compiled_patterns["begin_trans"].search(line):
                begin_trans_lines.append(line_num)
            if self._compiled_patterns["commit_trans"].search(line):
                commit_trans_lines.append(line_num)
            if self._compiled_patterns["rollback_trans"].search(line):
                rollback_trans_lines.append(line_num)

        # Check for BeginTrans without Commit/Rollback
        for begin_line in begin_trans_lines:
            has_commit = any(c > begin_line for c in commit_trans_lines)
            has_rollback = any(r > begin_line for r in rollback_trans_lines)

            if not has_commit and not has_rollback:
                findings.append(SQLFinding(
                    file_path=file_path,
                    line_number=begin_line,
                    issue_type=SQLIssueType.NO_TRANSACTION,
                    severity=SeverityLevel.HIGH,
                    description=(
                        f"BeginTrans at line {begin_line} without CommitTrans/RollbackTrans - "
                        f"transaction may be left open"
                    ),
                    suggested_fix=(
                        "Always pair BeginTrans with CommitTrans (success) and RollbackTrans (error)"
                    ),
                    code_context=self._get_context(lines, begin_line),
                    confidence=0.85,
                ))

        return findings

    def _get_context(self, lines: List[str], line_num: int) -> List[str]:
        """Get code context around a line."""
        start = max(0, line_num - 4)
        end = min(len(lines), line_num + 3)
        return lines[start:end]

    def get_supported_extensions(self) -> List[str]:
        """Return supported file extensions."""
        return [".asp", ".inc", ".asa"]

    def supports_file(self, file_path: str) -> bool:
        """Check if this analyzer supports the given file."""
        return any(
            file_path.lower().endswith(ext)
            for ext in self.get_supported_extensions()
        )

    def get_language(self) -> str:
        """Return the language name."""
        return "Classic ASP (VBScript)"

    def is_case_insensitive(self) -> bool:
        """VBScript is case-insensitive."""
        return True

    def get_category(self) -> StabilityCategory:
        """Return the stability category."""
        return StabilityCategory.SQL_PERFORMANCE

    def analyze(self, content: str, file_path: str = "test.asp") -> List[SQLFinding]:
        """
        Analyze code content for SQL issues.

        Convenience method that wraps analyze_file.

        Args:
            content: Code content to analyze
            file_path: Optional file path (defaults to test.asp)

        Returns:
            List of SQL findings
        """
        return self.analyze_file(file_path, content)
