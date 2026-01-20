"""
SQL Analysis Service - F3 (Fase 24)

Analyzes SQL query complexity across multiple languages and frameworks.

Features:
- Query complexity scoring (simple, medium, complex, highly complex)
- JOIN count and depth analysis
- Subquery detection and counting
- Table count extraction
- Missing index hints
- Query optimization suggestions
- Multi-language support (Python, Java, JavaScript, C#, PHP, etc.)

Version: 1.0.0
Week: 129 (Fase 24)
"""

import re
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class QueryComplexity(str, Enum):
    """Query complexity levels."""
    SIMPLE = "simple"           # Single table, basic operations
    MEDIUM = "medium"           # 2-3 tables, some JOINs
    COMPLEX = "complex"         # Multiple JOINs, subqueries
    HIGHLY_COMPLEX = "highly_complex"  # Deep nesting, many tables


class SQLOperationType(str, Enum):
    """Types of SQL operations."""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CREATE = "create"
    ALTER = "alter"
    DROP = "drop"
    STORED_PROC = "stored_proc"
    UNKNOWN = "unknown"


class JoinType(str, Enum):
    """Types of SQL joins."""
    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"
    FULL = "full"
    CROSS = "cross"
    SELF = "self"


@dataclass
class JoinInfo:
    """Information about a JOIN in a query."""
    join_type: JoinType
    table: str
    alias: Optional[str] = None
    condition: Optional[str] = None


@dataclass
class SubqueryInfo:
    """Information about a subquery."""
    location: str  # WHERE, FROM, SELECT, etc.
    depth: int = 1
    tables_involved: List[str] = field(default_factory=list)


@dataclass
class QueryMetrics:
    """
    Metrics about a SQL query's complexity.

    Attributes:
        table_count: Number of tables involved
        join_count: Number of JOINs
        subquery_count: Number of subqueries
        max_subquery_depth: Maximum nesting level
        has_where_clause: Whether query has WHERE
        has_group_by: Whether query has GROUP BY
        has_order_by: Whether query has ORDER BY
        has_having: Whether query has HAVING
        aggregate_functions: List of aggregate functions used
        uses_distinct: Whether query uses DISTINCT
        uses_union: Whether query uses UNION
        estimated_rows: Estimated row impact (if detectable)
    """
    table_count: int = 0
    join_count: int = 0
    subquery_count: int = 0
    max_subquery_depth: int = 0
    has_where_clause: bool = False
    has_group_by: bool = False
    has_order_by: bool = False
    has_having: bool = False
    aggregate_functions: List[str] = field(default_factory=list)
    uses_distinct: bool = False
    uses_union: bool = False
    estimated_rows: Optional[int] = None


@dataclass
class QueryAnalysis:
    """
    Complete analysis of a SQL query.

    Attributes:
        query_text: The SQL query text
        operation_type: Type of operation (SELECT, INSERT, etc.)
        complexity: Complexity level
        complexity_score: Numeric score (0-100)
        metrics: Detailed metrics
        tables: List of tables involved
        joins: List of JOIN information
        subqueries: List of subquery information
        issues: Detected issues/warnings
        suggestions: Optimization suggestions
        source_file: Source file if known
        source_line: Source line if known
    """
    query_text: str
    operation_type: SQLOperationType
    complexity: QueryComplexity
    complexity_score: int
    metrics: QueryMetrics
    tables: List[str] = field(default_factory=list)
    joins: List[JoinInfo] = field(default_factory=list)
    subqueries: List[SubqueryInfo] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    source_file: Optional[str] = None
    source_line: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_text": self.query_text[:500] + "..." if len(self.query_text) > 500 else self.query_text,
            "operation_type": self.operation_type.value,
            "complexity": self.complexity.value,
            "complexity_score": self.complexity_score,
            "metrics": {
                "table_count": self.metrics.table_count,
                "join_count": self.metrics.join_count,
                "subquery_count": self.metrics.subquery_count,
                "max_subquery_depth": self.metrics.max_subquery_depth,
                "has_where_clause": self.metrics.has_where_clause,
                "has_group_by": self.metrics.has_group_by,
                "has_order_by": self.metrics.has_order_by,
                "has_having": self.metrics.has_having,
                "aggregate_functions": self.metrics.aggregate_functions,
                "uses_distinct": self.metrics.uses_distinct,
                "uses_union": self.metrics.uses_union,
            },
            "tables": self.tables,
            "joins": [{"type": j.join_type.value, "table": j.table} for j in self.joins],
            "issues": self.issues,
            "suggestions": self.suggestions,
            "source_file": self.source_file,
            "source_line": self.source_line,
        }


@dataclass
class SQLAnalysisResult:
    """
    Result of analyzing SQL in a codebase.

    Attributes:
        queries_analyzed: Total queries found
        complexity_distribution: Count per complexity level
        avg_complexity_score: Average complexity score
        issues_by_type: Issues grouped by type
        files_with_complex_sql: Files containing complex queries
        queries: List of query analyses
    """
    queries_analyzed: int = 0
    complexity_distribution: Dict[str, int] = field(default_factory=dict)
    avg_complexity_score: float = 0.0
    issues_by_type: Dict[str, int] = field(default_factory=dict)
    files_with_complex_sql: List[str] = field(default_factory=list)
    queries: List[QueryAnalysis] = field(default_factory=list)
    scan_duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "queries_analyzed": self.queries_analyzed,
            "complexity_distribution": self.complexity_distribution,
            "avg_complexity_score": self.avg_complexity_score,
            "issues_by_type": self.issues_by_type,
            "files_with_complex_sql": self.files_with_complex_sql,
            "scan_duration_seconds": self.scan_duration_seconds,
            "queries": [q.to_dict() for q in self.queries[:100]],  # Limit output
        }


class SQLAnalysisService:
    """
    Service for analyzing SQL query complexity.

    Usage:
        service = SQLAnalysisService()

        # Analyze a single query
        analysis = service.analyze_query("SELECT * FROM users JOIN orders ON ...")

        # Analyze SQL in files
        result = service.analyze_files({"file.py": "...", "file.java": "..."})
    """

    # SQL extraction patterns per language
    SQL_EXTRACTION_PATTERNS: Dict[str, List[str]] = {
        "python": [
            # f-strings and formatted strings
            r'(?:cursor|conn|connection|db|session)\.execute\s*\(\s*[f]?["\']+(.*?)["\']',
            r'(?:cursor|conn|connection|db|session)\.executemany\s*\(\s*[f]?["\']+(.*?)["\']',
            # SQLAlchemy raw queries
            r'text\s*\(\s*["\']+(.*?)["\']',
            # Raw SQL strings
            r'(?:sql|query|statement)\s*=\s*[f]?["\']{1,3}(.*?)["\']{1,3}',
        ],
        "java": [
            # JDBC
            r'(?:statement|preparedStatement|ps|stmt)\.executeQuery\s*\(\s*["\']+(.*?)["\']',
            r'(?:statement|preparedStatement|ps|stmt)\.executeUpdate\s*\(\s*["\']+(.*?)["\']',
            # JPA/Hibernate
            r'createNativeQuery\s*\(\s*["\']+(.*?)["\']',
            r'createQuery\s*\(\s*["\']+(.*?)["\']',
            # MyBatis-style
            r'@Select\s*\(\s*["\']+(.*?)["\']',
            r'@Update\s*\(\s*["\']+(.*?)["\']',
            r'@Insert\s*\(\s*["\']+(.*?)["\']',
            r'@Delete\s*\(\s*["\']+(.*?)["\']',
        ],
        "javascript": [
            # Generic database calls
            r'\.query\s*\(\s*[`"\']+(.*?)[`"\']',
            r'\.execute\s*\(\s*[`"\']+(.*?)[`"\']',
            # Raw SQL
            r'(?:sql|query)\s*=\s*[`"\']+([^`"\']*(?:SELECT|INSERT|UPDATE|DELETE)[^`"\']*)[`"\']+',
            # Sequelize raw
            r'sequelize\.query\s*\(\s*[`"\']+(.*?)[`"\']',
        ],
        "csharp": [
            # ADO.NET
            r'(?:SqlCommand|SqlDataAdapter)\s*\([^,]*,?\s*["\']+(.*?)["\']',
            r'\.CommandText\s*=\s*["\']+(.*?)["\']',
            # Entity Framework raw
            r'\.FromSqlRaw\s*\(\s*["\']+(.*?)["\']',
            r'\.ExecuteSqlRaw\s*\(\s*["\']+(.*?)["\']',
            # Dapper
            r'\.Query(?:<[^>]+>)?\s*\(\s*["\']+(.*?)["\']',
            r'\.Execute\s*\(\s*["\']+(.*?)["\']',
        ],
        "php": [
            # PDO
            r'->query\s*\(\s*["\']+(.*?)["\']',
            r'->prepare\s*\(\s*["\']+(.*?)["\']',
            r'->exec\s*\(\s*["\']+(.*?)["\']',
            # MySQLi
            r'mysqli_query\s*\([^,]+,\s*["\']+(.*?)["\']',
        ],
    }

    # SQL keywords for pattern detection
    JOIN_PATTERNS = [
        (r'\bINNER\s+JOIN\s+(\w+)', JoinType.INNER),
        (r'\bLEFT\s+(?:OUTER\s+)?JOIN\s+(\w+)', JoinType.LEFT),
        (r'\bRIGHT\s+(?:OUTER\s+)?JOIN\s+(\w+)', JoinType.RIGHT),
        (r'\bFULL\s+(?:OUTER\s+)?JOIN\s+(\w+)', JoinType.FULL),
        (r'\bCROSS\s+JOIN\s+(\w+)', JoinType.CROSS),
        (r'\bJOIN\s+(\w+)', JoinType.INNER),  # Default to INNER
    ]

    AGGREGATE_FUNCTIONS = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP_CONCAT']

    def __init__(self):
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()
        logger.info("SQLAnalysisService initialized")

    def _compile_patterns(self) -> None:
        """Compile all regex patterns."""
        flags = re.IGNORECASE | re.DOTALL

        # Compile extraction patterns
        for lang, patterns in self.SQL_EXTRACTION_PATTERNS.items():
            self._compiled_patterns[lang] = [
                re.compile(p, flags) for p in patterns
            ]

        # Compile join patterns
        self._compiled_patterns["joins"] = [
            (re.compile(p, flags), jt) for p, jt in self.JOIN_PATTERNS
        ]

    def _detect_language(self, filepath: str) -> str:
        """Detect language from file extension."""
        ext_map = {
            ".py": "python",
            ".java": "java",
            ".js": "javascript",
            ".ts": "javascript",
            ".cs": "csharp",
            ".php": "php",
            ".rb": "python",  # Similar patterns
            ".go": "python",  # Similar patterns
        }
        ext = filepath.rsplit(".", 1)[-1].lower() if "." in filepath else ""
        return ext_map.get(f".{ext}", "python")

    def _extract_sql_queries(
        self,
        content: str,
        language: str
    ) -> List[Tuple[str, int]]:
        """
        Extract SQL queries from source code.

        Returns list of (query_text, line_number) tuples.
        """
        queries = []
        patterns = self._compiled_patterns.get(language, [])

        for pattern in patterns:
            for match in pattern.finditer(content):
                query_text = match.group(1) if match.groups() else match.group(0)
                # Clean up the query
                query_text = self._clean_query(query_text)
                if self._is_valid_sql(query_text):
                    line_num = content[:match.start()].count("\n") + 1
                    queries.append((query_text, line_num))

        return queries

    def _clean_query(self, query: str) -> str:
        """Clean up extracted query text."""
        # Remove common string formatting placeholders
        query = re.sub(r'\{\w*\}', '?', query)  # f-string placeholders
        query = re.sub(r'%s', '?', query)  # Python format
        query = re.sub(r'\$\d+', '?', query)  # PostgreSQL params
        query = re.sub(r':\w+', '?', query)  # Named params
        query = re.sub(r'\s+', ' ', query)  # Normalize whitespace
        return query.strip()

    def _is_valid_sql(self, query: str) -> bool:
        """Check if string looks like a valid SQL query."""
        if not query or len(query) < 10:
            return False

        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'EXEC']
        query_upper = query.upper()
        return any(kw in query_upper for kw in sql_keywords)

    def analyze_query(
        self,
        query: str,
        source_file: Optional[str] = None,
        source_line: Optional[int] = None
    ) -> QueryAnalysis:
        """
        Analyze a single SQL query for complexity.

        Args:
            query: The SQL query text
            source_file: Optional source file path
            source_line: Optional source line number

        Returns:
            QueryAnalysis with complexity metrics
        """
        query_upper = query.upper()
        metrics = QueryMetrics()
        tables: List[str] = []
        joins: List[JoinInfo] = []
        subqueries: List[SubqueryInfo] = []
        issues: List[str] = []
        suggestions: List[str] = []

        # Detect operation type
        operation_type = self._detect_operation_type(query_upper)

        # Extract tables
        tables = self._extract_tables(query_upper)
        metrics.table_count = len(tables)

        # Extract JOINs
        joins = self._extract_joins(query_upper)
        metrics.join_count = len(joins)

        # Detect subqueries
        subqueries = self._detect_subqueries(query_upper)
        metrics.subquery_count = len(subqueries)
        metrics.max_subquery_depth = max([s.depth for s in subqueries], default=0)

        # Check for clauses
        metrics.has_where_clause = 'WHERE' in query_upper
        metrics.has_group_by = 'GROUP BY' in query_upper
        metrics.has_order_by = 'ORDER BY' in query_upper
        metrics.has_having = 'HAVING' in query_upper
        metrics.uses_distinct = 'DISTINCT' in query_upper
        metrics.uses_union = 'UNION' in query_upper

        # Extract aggregate functions
        for func in self.AGGREGATE_FUNCTIONS:
            if f'{func}(' in query_upper:
                metrics.aggregate_functions.append(func)

        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(metrics)
        complexity = self._score_to_level(complexity_score)

        # Generate issues and suggestions
        issues, suggestions = self._generate_recommendations(
            query, metrics, operation_type
        )

        return QueryAnalysis(
            query_text=query,
            operation_type=operation_type,
            complexity=complexity,
            complexity_score=complexity_score,
            metrics=metrics,
            tables=tables,
            joins=joins,
            subqueries=subqueries,
            issues=issues,
            suggestions=suggestions,
            source_file=source_file,
            source_line=source_line,
        )

    def _detect_operation_type(self, query: str) -> SQLOperationType:
        """Detect the type of SQL operation."""
        if query.strip().startswith('SELECT'):
            return SQLOperationType.SELECT
        if query.strip().startswith('INSERT'):
            return SQLOperationType.INSERT
        if query.strip().startswith('UPDATE'):
            return SQLOperationType.UPDATE
        if query.strip().startswith('DELETE'):
            return SQLOperationType.DELETE
        if query.strip().startswith('CREATE'):
            return SQLOperationType.CREATE
        if query.strip().startswith('ALTER'):
            return SQLOperationType.ALTER
        if query.strip().startswith('DROP'):
            return SQLOperationType.DROP
        if 'EXEC' in query or 'CALL' in query:
            return SQLOperationType.STORED_PROC
        return SQLOperationType.UNKNOWN

    def _extract_tables(self, query: str) -> List[str]:
        """Extract table names from query."""
        tables = set()

        # FROM clause
        from_match = re.search(r'\bFROM\s+(\w+)', query)
        if from_match:
            tables.add(from_match.group(1))

        # JOIN clauses
        for match in re.finditer(r'\bJOIN\s+(\w+)', query):
            tables.add(match.group(1))

        # INSERT INTO
        insert_match = re.search(r'\bINSERT\s+INTO\s+(\w+)', query)
        if insert_match:
            tables.add(insert_match.group(1))

        # UPDATE
        update_match = re.search(r'\bUPDATE\s+(\w+)', query)
        if update_match:
            tables.add(update_match.group(1))

        # DELETE FROM
        delete_match = re.search(r'\bDELETE\s+FROM\s+(\w+)', query)
        if delete_match:
            tables.add(delete_match.group(1))

        return list(tables)

    def _extract_joins(self, query: str) -> List[JoinInfo]:
        """Extract JOIN information from query."""
        joins = []

        for pattern, join_type in self._compiled_patterns["joins"]:
            for match in pattern.finditer(query):
                table = match.group(1)
                joins.append(JoinInfo(
                    join_type=join_type,
                    table=table,
                ))

        return joins

    def _detect_subqueries(self, query: str) -> List[SubqueryInfo]:
        """Detect and analyze subqueries."""
        subqueries = []

        # Count SELECT keywords (excluding first one)
        select_count = query.count('SELECT') - 1
        if select_count > 0:
            # Simple depth detection based on parentheses
            depth = 1
            for i, char in enumerate(query):
                if char == '(':
                    # Check if followed by SELECT
                    remainder = query[i+1:i+50].strip()
                    if remainder.startswith('SELECT'):
                        subqueries.append(SubqueryInfo(
                            location="nested",
                            depth=depth,
                        ))
                        depth += 1
                elif char == ')':
                    depth = max(1, depth - 1)

        return subqueries

    def _calculate_complexity_score(self, metrics: QueryMetrics) -> int:
        """
        Calculate complexity score (0-100).

        Scoring factors:
        - Tables: +10 per table (max 40)
        - JOINs: +15 per JOIN (max 45)
        - Subqueries: +20 per subquery (max 40)
        - Subquery depth: +10 per level beyond 1 (max 30)
        - GROUP BY: +5
        - HAVING: +10
        - DISTINCT: +5
        - UNION: +15
        - No WHERE (for SELECT): +10 (performance concern)
        """
        score = 0

        # Tables (0-40)
        score += min(metrics.table_count * 10, 40)

        # JOINs (0-45)
        score += min(metrics.join_count * 15, 45)

        # Subqueries (0-40)
        score += min(metrics.subquery_count * 20, 40)

        # Subquery depth (0-30)
        if metrics.max_subquery_depth > 1:
            score += min((metrics.max_subquery_depth - 1) * 10, 30)

        # Clauses
        if metrics.has_group_by:
            score += 5
        if metrics.has_having:
            score += 10
        if metrics.uses_distinct:
            score += 5
        if metrics.uses_union:
            score += 15

        # Performance concerns
        if not metrics.has_where_clause and metrics.table_count > 0:
            score += 10  # Unbounded query

        return min(score, 100)

    def _score_to_level(self, score: int) -> QueryComplexity:
        """Convert numeric score to complexity level."""
        if score <= 20:
            return QueryComplexity.SIMPLE
        if score <= 45:
            return QueryComplexity.MEDIUM
        if score <= 70:
            return QueryComplexity.COMPLEX
        return QueryComplexity.HIGHLY_COMPLEX

    def _generate_recommendations(
        self,
        query: str,
        metrics: QueryMetrics,
        operation_type: SQLOperationType
    ) -> Tuple[List[str], List[str]]:
        """Generate issues and optimization suggestions."""
        issues = []
        suggestions = []
        query_upper = query.upper()

        # Check for SELECT *
        if 'SELECT *' in query_upper or 'SELECT  *' in query_upper:
            issues.append("Uses SELECT * - may fetch unnecessary columns")
            suggestions.append("Specify exact columns needed instead of SELECT *")

        # Check for unbounded SELECT
        if (operation_type == SQLOperationType.SELECT and
            not metrics.has_where_clause and
            'LIMIT' not in query_upper and
            'TOP' not in query_upper):
            issues.append("Unbounded SELECT without WHERE/LIMIT clause")
            suggestions.append("Add WHERE clause or LIMIT to prevent full table scan")

        # Check for complex JOINs
        if metrics.join_count > 3:
            issues.append(f"High JOIN count ({metrics.join_count}) - may impact performance")
            suggestions.append("Consider denormalization or breaking into multiple queries")

        # Check for deep subqueries
        if metrics.max_subquery_depth > 2:
            issues.append(f"Deeply nested subqueries (depth {metrics.max_subquery_depth})")
            suggestions.append("Consider using CTEs (WITH clause) or temporary tables")

        # Check for missing index hints
        if metrics.table_count > 2 and not metrics.has_where_clause:
            suggestions.append("Consider adding indexes on JOIN columns")

        # Check for HAVING without GROUP BY
        if metrics.has_having and not metrics.has_group_by:
            issues.append("HAVING clause without GROUP BY is unusual")

        # Check for DISTINCT with ORDER BY
        if metrics.uses_distinct and metrics.has_order_by:
            suggestions.append("DISTINCT with ORDER BY can be slow - ensure proper indexes")

        # Check for multiple UNIONs
        if query_upper.count('UNION') > 2:
            issues.append("Multiple UNIONs detected - consider alternative approaches")
            suggestions.append("Consider using UNION ALL if duplicates are acceptable")

        return issues, suggestions

    def analyze_files(
        self,
        files: Dict[str, str],
        language: Optional[str] = None
    ) -> SQLAnalysisResult:
        """
        Analyze SQL queries in multiple files.

        Args:
            files: Dict of filepath -> content
            language: Optional language override

        Returns:
            SQLAnalysisResult with all analyses
        """
        import time
        start_time = time.time()

        result = SQLAnalysisResult()
        queries_by_file: Dict[str, List[QueryAnalysis]] = {}
        all_scores = []

        for filepath, content in files.items():
            file_lang = language or self._detect_language(filepath)
            queries = self._extract_sql_queries(content, file_lang)

            file_queries = []
            for query_text, line_num in queries:
                analysis = self.analyze_query(query_text, filepath, line_num)
                file_queries.append(analysis)
                all_scores.append(analysis.complexity_score)

                # Track issues
                for issue in analysis.issues:
                    result.issues_by_type[issue] = result.issues_by_type.get(issue, 0) + 1

            if file_queries:
                queries_by_file[filepath] = file_queries
                result.queries.extend(file_queries)

                # Check for complex SQL
                if any(q.complexity in [QueryComplexity.COMPLEX, QueryComplexity.HIGHLY_COMPLEX]
                       for q in file_queries):
                    result.files_with_complex_sql.append(filepath)

        # Calculate summary stats
        result.queries_analyzed = len(result.queries)
        result.scan_duration_seconds = time.time() - start_time

        if all_scores:
            result.avg_complexity_score = sum(all_scores) / len(all_scores)

        # Complexity distribution
        for level in QueryComplexity:
            count = len([q for q in result.queries if q.complexity == level])
            result.complexity_distribution[level.value] = count

        logger.info(
            f"Analyzed {result.queries_analyzed} SQL queries in {len(files)} files "
            f"({result.scan_duration_seconds:.2f}s)"
        )

        return result

    def get_complexity_report(self, result: SQLAnalysisResult) -> str:
        """Generate a markdown report of SQL complexity analysis."""
        lines = [
            "# SQL Complexity Analysis Report",
            "",
            f"**Queries Analyzed:** {result.queries_analyzed}",
            f"**Average Complexity Score:** {result.avg_complexity_score:.1f}/100",
            f"**Scan Duration:** {result.scan_duration_seconds:.2f}s",
            "",
            "## Complexity Distribution",
            "",
            "| Level | Count | Percentage |",
            "|-------|-------|------------|",
        ]

        total = result.queries_analyzed or 1
        for level in QueryComplexity:
            count = result.complexity_distribution.get(level.value, 0)
            pct = (count / total) * 100
            lines.append(f"| {level.value.title()} | {count} | {pct:.1f}% |")

        if result.issues_by_type:
            lines.extend([
                "",
                "## Common Issues",
                "",
            ])
            for issue, count in sorted(result.issues_by_type.items(), key=lambda x: -x[1]):
                lines.append(f"- **{issue}**: {count} occurrences")

        if result.files_with_complex_sql:
            lines.extend([
                "",
                "## Files with Complex SQL",
                "",
            ])
            for filepath in result.files_with_complex_sql[:20]:
                lines.append(f"- {filepath}")

        # Top complex queries
        complex_queries = [q for q in result.queries
                         if q.complexity in [QueryComplexity.COMPLEX, QueryComplexity.HIGHLY_COMPLEX]]
        if complex_queries:
            lines.extend([
                "",
                "## Most Complex Queries",
                "",
            ])
            for query in sorted(complex_queries, key=lambda x: -x.complexity_score)[:10]:
                lines.append(f"### Score: {query.complexity_score} ({query.complexity.value})")
                lines.append(f"**File:** {query.source_file}:{query.source_line}")
                lines.append("```sql")
                lines.append(query.query_text[:300] + ("..." if len(query.query_text) > 300 else ""))
                lines.append("```")
                if query.issues:
                    lines.append("**Issues:**")
                    for issue in query.issues:
                        lines.append(f"- {issue}")
                lines.append("")

        return "\n".join(lines)
