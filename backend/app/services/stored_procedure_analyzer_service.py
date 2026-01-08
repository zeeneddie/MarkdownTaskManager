"""
StoredProcedureAnalyzerService - Complete Database Stored Procedure Analyzer

Week 77: Database business logic analysis for complete picture.
Analyzes stored procedures, functions, triggers, views for:
- Business logic extraction
- Data transformations
- Validation rules
- Dependencies between SPs
- Table usage patterns
- Complexity metrics
- Migration difficulty assessment
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Supported database types."""
    SQL_SERVER = "sql_server"
    ORACLE = "oracle"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    UNKNOWN = "unknown"


class ComplexityLevel(Enum):
    """Complexity classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class StoredProcedure:
    """Extracted stored procedure definition."""
    name: str
    schema: str
    database_type: DatabaseType
    parameters: List[Dict[str, str]]  # [{name, type, direction}]
    return_type: Optional[str]
    line_count: int
    complexity: int  # Cyclomatic complexity
    complexity_level: ComplexityLevel
    body: str  # Full SP body
    file_path: Optional[str] = None  # If from SQL file

    # Dependencies
    tables_used: List[str] = field(default_factory=list)
    sps_called: List[str] = field(default_factory=list)
    functions_called: List[str] = field(default_factory=list)

    # Business logic indicators
    has_transaction: bool = False
    has_cursor: bool = False
    has_dynamic_sql: bool = False
    has_temp_tables: bool = False
    has_error_handling: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "schema": self.schema,
            "database_type": self.database_type.value,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "line_count": self.line_count,
            "complexity": self.complexity,
            "complexity_level": self.complexity_level.value,
            "tables_used": self.tables_used,
            "sps_called": self.sps_called,
            "functions_called": self.functions_called,
            "has_transaction": self.has_transaction,
            "has_cursor": self.has_cursor,
            "has_dynamic_sql": self.has_dynamic_sql,
            "has_temp_tables": self.has_temp_tables,
            "has_error_handling": self.has_error_handling,
            "file_path": self.file_path,
        }


@dataclass
class DatabaseFunction:
    """Extracted database function definition."""
    name: str
    schema: str
    database_type: DatabaseType
    parameters: List[Dict[str, str]]
    return_type: str
    function_type: str  # scalar, table, inline
    line_count: int
    complexity: int
    is_deterministic: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "schema": self.schema,
            "database_type": self.database_type.value,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "function_type": self.function_type,
            "line_count": self.line_count,
            "complexity": self.complexity,
            "is_deterministic": self.is_deterministic,
        }


@dataclass
class Trigger:
    """Extracted trigger definition."""
    name: str
    schema: str
    table_name: str
    trigger_event: str  # INSERT, UPDATE, DELETE
    trigger_timing: str  # BEFORE, AFTER, INSTEAD OF
    line_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "schema": self.schema,
            "table_name": self.table_name,
            "trigger_event": self.trigger_event,
            "trigger_timing": self.trigger_timing,
            "line_count": self.line_count,
        }


@dataclass
class View:
    """Extracted view definition."""
    name: str
    schema: str
    is_materialized: bool
    dependencies: List[str]  # Tables/views used
    line_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "schema": self.schema,
            "is_materialized": self.is_materialized,
            "dependencies": self.dependencies,
            "line_count": self.line_count,
        }


@dataclass
class BusinessRule:
    """Extracted business rule from SP."""
    sp_name: str
    rule_type: str  # validation, calculation, workflow, constraint
    description: str
    confidence: float  # 0-1 confidence in extraction
    code_snippet: str
    line_number: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sp_name": self.sp_name,
            "rule_type": self.rule_type,
            "description": self.description,
            "confidence": self.confidence,
            "code_snippet": self.code_snippet[:300],
            "line_number": self.line_number,
        }


@dataclass
class DataTransformation:
    """Extracted data transformation."""
    sp_name: str
    input_columns: List[str]
    output_columns: List[str]
    transformation_type: str  # aggregate, pivot, join, calculate
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sp_name": self.sp_name,
            "input_columns": self.input_columns,
            "output_columns": self.output_columns,
            "transformation_type": self.transformation_type,
            "description": self.description,
        }


@dataclass
class ValidationLogic:
    """Extracted validation logic."""
    sp_name: str
    field_name: str
    validation_type: str  # null_check, range, format, lookup, custom
    condition: str
    error_handling: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sp_name": self.sp_name,
            "field_name": self.field_name,
            "validation_type": self.validation_type,
            "condition": self.condition,
            "error_handling": self.error_handling,
        }


@dataclass
class VendorSpecificFeature:
    """Vendor-specific SQL feature that may need migration attention."""
    feature_name: str
    sp_name: str
    line_number: int
    database_type: DatabaseType
    migration_impact: str  # low, medium, high
    alternative: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature": self.feature_name,
            "sp_name": self.sp_name,
            "line": self.line_number,
            "database_type": self.database_type.value,
            "migration_impact": self.migration_impact,
            "alternative": self.alternative,
        }


@dataclass
class PerformanceConcern:
    """Performance issue identified in SP."""
    sp_name: str
    concern_type: str
    description: str
    recommendation: str
    severity: str  # low, medium, high

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sp_name": self.sp_name,
            "concern_type": self.concern_type,
            "description": self.description,
            "recommendation": self.recommendation,
            "severity": self.severity,
        }


@dataclass
class StoredProcedureAnalysisResult:
    """Complete analysis result for stored procedures."""
    # Database info
    database_type: DatabaseType = DatabaseType.UNKNOWN
    database_name: str = ""
    schema_name: str = ""

    # Inventory
    stored_procedures: List[StoredProcedure] = field(default_factory=list)
    functions: List[DatabaseFunction] = field(default_factory=list)
    triggers: List[Trigger] = field(default_factory=list)
    views: List[View] = field(default_factory=list)
    total_lines: int = 0

    # Dependencies
    sp_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    table_usage: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)
    cross_database_calls: List[Dict[str, str]] = field(default_factory=list)

    # Business logic
    business_rules: List[BusinessRule] = field(default_factory=list)
    data_transformations: List[DataTransformation] = field(default_factory=list)
    validation_logic: List[ValidationLogic] = field(default_factory=list)

    # Complexity
    complexity_distribution: Dict[str, int] = field(default_factory=dict)
    most_complex_sps: List[Dict[str, Any]] = field(default_factory=list)
    most_called_sps: List[Dict[str, Any]] = field(default_factory=list)

    # Migration indicators
    vendor_specific_features: List[VendorSpecificFeature] = field(default_factory=list)
    deprecated_syntax: List[Dict[str, str]] = field(default_factory=list)
    performance_concerns: List[PerformanceConcern] = field(default_factory=list)

    # Scores
    overall_complexity_score: int = 0
    migration_difficulty_score: int = 0
    business_logic_coverage: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "database_info": {
                "type": self.database_type.value,
                "name": self.database_name,
                "schema": self.schema_name,
            },
            "inventory": {
                "stored_procedures": len(self.stored_procedures),
                "functions": len(self.functions),
                "triggers": len(self.triggers),
                "views": len(self.views),
                "total_lines": self.total_lines,
            },
            "stored_procedures": [sp.to_dict() for sp in self.stored_procedures],
            "functions": [f.to_dict() for f in self.functions],
            "triggers": [t.to_dict() for t in self.triggers],
            "views": [v.to_dict() for v in self.views],
            "dependencies": {
                "sp_dependencies": self.sp_dependencies,
                "table_usage": self.table_usage,
                "cross_database_calls": self.cross_database_calls,
            },
            "business_logic": {
                "business_rules": [r.to_dict() for r in self.business_rules],
                "data_transformations": [t.to_dict() for t in self.data_transformations],
                "validation_logic": [v.to_dict() for v in self.validation_logic],
            },
            "complexity": {
                "distribution": self.complexity_distribution,
                "most_complex": self.most_complex_sps,
                "most_called": self.most_called_sps,
            },
            "migration_indicators": {
                "vendor_specific": [f.to_dict() for f in self.vendor_specific_features],
                "deprecated": self.deprecated_syntax,
                "performance_concerns": [p.to_dict() for p in self.performance_concerns],
            },
            "scores": {
                "complexity": self.overall_complexity_score,
                "migration_difficulty": self.migration_difficulty_score,
                "business_logic_coverage": self.business_logic_coverage,
            },
        }


class StoredProcedureAnalyzerService:
    """
    Complete database stored procedure analyzer.
    Extracts business logic, dependencies, and migration indicators.
    """

    # SQL Server patterns
    SQLSERVER_SP_PATTERN = re.compile(
        r'CREATE\s+(OR\s+ALTER\s+)?PROC(?:EDURE)?\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?',
        re.IGNORECASE | re.MULTILINE
    )
    SQLSERVER_FUNC_PATTERN = re.compile(
        r'CREATE\s+(OR\s+ALTER\s+)?FUNCTION\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?',
        re.IGNORECASE | re.MULTILINE
    )

    # Oracle patterns
    ORACLE_SP_PATTERN = re.compile(
        r'CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+"?(\w+)"?\."?(\w+)"?',
        re.IGNORECASE | re.MULTILINE
    )
    ORACLE_FUNC_PATTERN = re.compile(
        r'CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+"?(\w+)"?\."?(\w+)"?',
        re.IGNORECASE | re.MULTILINE
    )

    # PostgreSQL patterns
    PG_SP_PATTERN = re.compile(
        r'CREATE\s+(?:OR\s+REPLACE\s+)?(?:PROCEDURE|FUNCTION)\s+(?:(\w+)\.)?(\w+)',
        re.IGNORECASE | re.MULTILINE
    )

    # Generic patterns
    TRIGGER_PATTERN = re.compile(
        r'CREATE\s+(?:OR\s+REPLACE\s+)?TRIGGER\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?\s+'
        r'(?:BEFORE|AFTER|INSTEAD\s+OF)\s+(INSERT|UPDATE|DELETE)',
        re.IGNORECASE | re.MULTILINE
    )
    VIEW_PATTERN = re.compile(
        r'CREATE\s+(?:OR\s+REPLACE\s+)?(?:MATERIALIZED\s+)?VIEW\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?',
        re.IGNORECASE | re.MULTILINE
    )

    # Business logic patterns
    VALIDATION_PATTERNS = [
        (r'IF\s+@?\w+\s+IS\s+NULL', 'null_check'),
        (r'IF\s+@?\w+\s+(?:NOT\s+)?BETWEEN', 'range'),
        (r'IF\s+@?\w+\s+(?:NOT\s+)?LIKE', 'format'),
        (r'IF\s+(?:NOT\s+)?EXISTS\s*\(', 'lookup'),
        (r'IF\s+LEN\s*\(\s*@?\w+\s*\)', 'length'),
        (r'RAISERROR|THROW|SIGNAL', 'error_handling'),
    ]

    # Vendor-specific features (SQL Server)
    SQLSERVER_SPECIFIC = [
        ('@@IDENTITY', 'Identity variable', 'high', 'Use SCOPE_IDENTITY() or OUTPUT clause'),
        ('SET NOCOUNT', 'Row count suppression', 'low', 'Not needed in most modern frameworks'),
        ('sp_executesql', 'Dynamic SQL', 'medium', 'Convert to parameterized queries'),
        (r'EXEC\s*\(', 'String-based dynamic SQL', 'high', 'Convert to parameterized queries'),
        (r'WITH\s*\(NOLOCK\)', 'Dirty reads hint', 'medium', 'Review isolation requirements'),
        ('@@ROWCOUNT', 'Row count variable', 'low', 'Use ROW_COUNT()'),
        (r'CONVERT\s*\(', 'Data conversion', 'low', 'Use CAST or database-specific functions'),
        (r'TOP\s+\d+', 'Row limiting', 'low', 'Use LIMIT or FETCH FIRST'),
        (r'GETDATE\s*\(\)', 'Date function', 'low', 'Use NOW() or CURRENT_TIMESTAMP'),
        (r'ISNULL\s*\(', 'Null handling', 'low', 'Use COALESCE for portability'),
    ]

    # Performance anti-patterns
    PERFORMANCE_ANTIPATTERNS = [
        (r'SELECT\s+\*', 'Select all columns', 'Specify only needed columns'),
        (r'CURSOR\s+', 'Cursor usage', 'Consider set-based operations'),
        (r'WHILE\s+', 'Loop in SQL', 'Consider set-based operations'),
        (r'IN\s*\(\s*SELECT', 'Subquery in IN clause', 'Consider EXISTS or JOIN'),
        (r'NOT\s+IN\s*\(\s*SELECT', 'NOT IN with subquery', 'Use NOT EXISTS instead'),
        (r'LIKE\s+[\'"]%', 'Leading wildcard LIKE', 'Consider full-text search'),
        (r'OR\s+\w+\s*=', 'Multiple OR conditions', 'Consider UNION or IN clause'),
    ]

    def __init__(self):
        self.result = StoredProcedureAnalysisResult()

    async def analyze(
        self,
        source_path: str,
        database_type: Optional[DatabaseType] = None
    ) -> StoredProcedureAnalysisResult:
        """
        Analyze stored procedures from SQL files or database connection.

        Args:
            source_path: Path to SQL files directory or connection string
            database_type: Optional database type hint

        Returns:
            StoredProcedureAnalysisResult with complete analysis
        """
        self.result = StoredProcedureAnalysisResult()

        path = Path(source_path)
        if path.is_dir():
            # Analyze SQL files
            await self._analyze_sql_files(path, database_type)
        else:
            # Single file
            await self._analyze_sql_file(source_path, database_type)

        # Post-processing
        self._build_dependency_graph()
        self._extract_business_rules()
        self._analyze_complexity_distribution()
        self._identify_vendor_specific()
        self._identify_performance_issues()
        self._calculate_scores()

        return self.result

    async def _analyze_sql_files(
        self,
        source_path: Path,
        database_type: Optional[DatabaseType]
    ) -> None:
        """Analyze all SQL files in directory."""
        sql_patterns = ['**/*.sql', '**/*.prc', '**/*.fnc', '**/*.trg', '**/*.vw']

        for pattern in sql_patterns:
            for file_path in source_path.glob(pattern):
                await self._analyze_sql_file(str(file_path), database_type)

    async def _analyze_sql_file(
        self,
        file_path: str,
        database_type: Optional[DatabaseType]
    ) -> None:
        """Analyze a single SQL file."""
        try:
            # Try multiple encodings
            content = None
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if not content:
                logger.warning(f"Could not decode file: {file_path}")
                return

            # Detect database type if not provided
            if database_type is None:
                database_type = self._detect_database_type(content)

            self.result.database_type = database_type

            # Extract objects based on database type
            self._extract_stored_procedures(content, file_path, database_type)
            self._extract_functions(content, file_path, database_type)
            self._extract_triggers(content, file_path)
            self._extract_views(content, file_path)

            # Count lines
            self.result.total_lines += len(content.split('\n'))

        except Exception as e:
            logger.error(f"Error analyzing SQL file {file_path}: {e}")

    def _detect_database_type(self, content: str) -> DatabaseType:
        """Detect database type from SQL content."""
        content_lower = content.lower()

        # SQL Server indicators
        if any(ind in content_lower for ind in ['[dbo]', 'nvarchar', 'set nocount', '@@identity', 'sp_']):
            return DatabaseType.SQL_SERVER

        # Oracle indicators
        if any(ind in content_lower for ind in ['begin\n', 'dbms_', 'nvl(', 'sysdate', 'rownum']):
            return DatabaseType.ORACLE

        # PostgreSQL indicators
        if any(ind in content_lower for ind in ['$$', 'plpgsql', 'serial', 'returning']):
            return DatabaseType.POSTGRESQL

        # MySQL indicators
        if any(ind in content_lower for ind in ['delimiter', 'auto_increment', 'limit ', 'ifnull(']):
            return DatabaseType.MYSQL

        return DatabaseType.UNKNOWN

    def _extract_stored_procedures(
        self,
        content: str,
        file_path: str,
        database_type: DatabaseType
    ) -> None:
        """Extract stored procedure definitions."""
        # Select pattern based on database type
        if database_type == DatabaseType.SQL_SERVER:
            pattern = self.SQLSERVER_SP_PATTERN
        elif database_type == DatabaseType.ORACLE:
            pattern = self.ORACLE_SP_PATTERN
        else:
            pattern = self.PG_SP_PATTERN

        for match in pattern.finditer(content):
            try:
                # Extract SP name and schema
                groups = match.groups()
                if database_type == DatabaseType.SQL_SERVER:
                    schema = groups[1] or 'dbo'
                    name = groups[2]
                else:
                    schema = groups[0] or 'public'
                    name = groups[1]

                # Find SP body
                start_pos = match.start()
                body, end_pos = self._extract_sp_body(content, start_pos, database_type)

                # Extract parameters
                params = self._extract_parameters(content[match.end():match.end() + 500])

                # Calculate complexity
                complexity = self._calculate_complexity(body)
                complexity_level = self._get_complexity_level(complexity)

                # Analyze body
                tables = self._extract_table_references(body)
                called_sps = self._extract_sp_calls(body)
                called_funcs = self._extract_function_calls(body)

                sp = StoredProcedure(
                    name=name,
                    schema=schema,
                    database_type=database_type,
                    parameters=params,
                    return_type=None,
                    line_count=body.count('\n') + 1,
                    complexity=complexity,
                    complexity_level=complexity_level,
                    body=body,
                    file_path=file_path,
                    tables_used=tables,
                    sps_called=called_sps,
                    functions_called=called_funcs,
                    has_transaction='BEGIN TRAN' in body.upper() or 'START TRANSACTION' in body.upper(),
                    has_cursor='CURSOR' in body.upper(),
                    has_dynamic_sql='EXEC(' in body.upper() or 'EXECUTE IMMEDIATE' in body.upper(),
                    has_temp_tables='#' in body or 'TEMP' in body.upper(),
                    has_error_handling='TRY' in body.upper() or 'EXCEPTION' in body.upper() or 'HANDLER' in body.upper(),
                )

                self.result.stored_procedures.append(sp)

            except Exception as e:
                logger.error(f"Error extracting SP from {file_path}: {e}")

    def _extract_sp_body(
        self,
        content: str,
        start_pos: int,
        database_type: DatabaseType
    ) -> Tuple[str, int]:
        """Extract the body of a stored procedure."""
        # Find the end marker based on database type
        if database_type == DatabaseType.SQL_SERVER:
            # Look for GO or next CREATE
            go_match = re.search(r'\nGO\b', content[start_pos:], re.IGNORECASE)
            create_match = re.search(r'\nCREATE\s+(?:PROC|FUNCTION|TRIGGER|VIEW)', content[start_pos + 10:], re.IGNORECASE)

            if go_match and (not create_match or go_match.start() < create_match.start()):
                end_pos = start_pos + go_match.end()
            elif create_match:
                end_pos = start_pos + 10 + create_match.start()
            else:
                end_pos = len(content)

        elif database_type == DatabaseType.ORACLE:
            # Look for END <name>; or /
            end_match = re.search(r'END\s+\w+\s*;\s*/?\s*$', content[start_pos:], re.IGNORECASE | re.MULTILINE)
            if end_match:
                end_pos = start_pos + end_match.end()
            else:
                end_pos = len(content)

        else:
            # PostgreSQL - look for $$ end marker or END
            dollar_match = re.search(r'\$\$\s*;', content[start_pos + 10:])
            if dollar_match:
                end_pos = start_pos + 10 + dollar_match.end()
            else:
                end_pos = len(content)

        return content[start_pos:end_pos], end_pos

    def _extract_parameters(self, param_section: str) -> List[Dict[str, str]]:
        """Extract parameters from parameter section."""
        params = []

        # Match parameter declarations
        # SQL Server style: @param_name data_type
        # Oracle/PG style: param_name IN/OUT data_type
        param_pattern = re.compile(
            r'[@]?(\w+)\s+(IN|OUT|INOUT|IN\s+OUT)?\s*(\w+(?:\([^)]+\))?)',
            re.IGNORECASE
        )

        # Get the parameter section (between parentheses)
        paren_match = re.search(r'\((.*?)\)', param_section, re.DOTALL)
        if paren_match:
            param_str = paren_match.group(1)

            for match in param_pattern.finditer(param_str):
                params.append({
                    "name": match.group(1),
                    "direction": (match.group(2) or 'IN').strip(),
                    "type": match.group(3),
                })

        return params

    def _extract_functions(
        self,
        content: str,
        file_path: str,
        database_type: DatabaseType
    ) -> None:
        """Extract function definitions."""
        if database_type == DatabaseType.SQL_SERVER:
            pattern = self.SQLSERVER_FUNC_PATTERN
        elif database_type == DatabaseType.ORACLE:
            pattern = self.ORACLE_FUNC_PATTERN
        else:
            # For PG, functions and procedures use similar syntax
            return

        for match in pattern.finditer(content):
            try:
                groups = match.groups()
                schema = groups[1] if len(groups) > 1 else 'dbo'
                name = groups[-1]

                # Determine function type
                func_section = content[match.end():match.end() + 200].upper()
                if 'RETURNS TABLE' in func_section:
                    func_type = 'table'
                elif 'RETURNS @' in func_section:
                    func_type = 'inline'
                else:
                    func_type = 'scalar'

                # Extract return type
                return_match = re.search(r'RETURNS\s+(\w+)', func_section, re.IGNORECASE)
                return_type = return_match.group(1) if return_match else 'unknown'

                body, _ = self._extract_sp_body(content, match.start(), database_type)

                func = DatabaseFunction(
                    name=name,
                    schema=schema or 'dbo',
                    database_type=database_type,
                    parameters=self._extract_parameters(content[match.end():match.end() + 500]),
                    return_type=return_type,
                    function_type=func_type,
                    line_count=body.count('\n') + 1,
                    complexity=self._calculate_complexity(body),
                    is_deterministic='DETERMINISTIC' in body.upper() or 'WITH SCHEMABINDING' in body.upper(),
                )

                self.result.functions.append(func)

            except Exception as e:
                logger.error(f"Error extracting function from {file_path}: {e}")

    def _extract_triggers(self, content: str, file_path: str) -> None:
        """Extract trigger definitions."""
        for match in self.TRIGGER_PATTERN.finditer(content):
            try:
                schema = match.group(1) or 'dbo'
                name = match.group(2)
                event = match.group(3).upper()

                # Find timing and table
                trigger_section = content[match.start():match.start() + 300]
                timing_match = re.search(r'(BEFORE|AFTER|INSTEAD\s+OF)', trigger_section, re.IGNORECASE)
                table_match = re.search(r'ON\s+(?:\[?\w+\]?\.)?\[?(\w+)\]?', trigger_section, re.IGNORECASE)

                body, _ = self._extract_sp_body(content, match.start(), self.result.database_type)

                trigger = Trigger(
                    name=name,
                    schema=schema,
                    table_name=table_match.group(1) if table_match else 'unknown',
                    trigger_event=event,
                    trigger_timing=(timing_match.group(1) if timing_match else 'AFTER').upper(),
                    line_count=body.count('\n') + 1,
                )

                self.result.triggers.append(trigger)

            except Exception as e:
                logger.error(f"Error extracting trigger from {file_path}: {e}")

    def _extract_views(self, content: str, file_path: str) -> None:
        """Extract view definitions."""
        for match in self.VIEW_PATTERN.finditer(content):
            try:
                schema = match.group(1) or 'dbo'
                name = match.group(2)
                is_materialized = 'MATERIALIZED' in content[match.start():match.start() + 50].upper()

                # Get view definition to find dependencies
                view_section = content[match.start():]
                as_match = re.search(r'\bAS\b', view_section, re.IGNORECASE)
                if as_match:
                    view_body = view_section[as_match.end():as_match.end() + 2000]
                    dependencies = self._extract_table_references(view_body)
                else:
                    dependencies = []

                view = View(
                    name=name,
                    schema=schema,
                    is_materialized=is_materialized,
                    dependencies=dependencies,
                    line_count=min(view_section.split('\nGO')[0].count('\n') + 1, 100),
                )

                self.result.views.append(view)

            except Exception as e:
                logger.error(f"Error extracting view from {file_path}: {e}")

    def _extract_table_references(self, body: str) -> List[str]:
        """Extract table references from SQL body."""
        tables = set()

        # FROM and JOIN patterns
        table_pattern = re.compile(
            r'(?:FROM|JOIN|INTO|UPDATE|DELETE\s+FROM)\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?',
            re.IGNORECASE
        )

        for match in table_pattern.finditer(body):
            table_name = match.group(2)
            # Filter out common aliases and keywords
            if table_name.upper() not in ['SELECT', 'WHERE', 'AND', 'OR', 'AS', 'ON', 'SET']:
                tables.add(table_name)

        return list(tables)

    def _extract_sp_calls(self, body: str) -> List[str]:
        """Extract stored procedure calls."""
        sps = set()

        # EXEC sp_name or EXECUTE sp_name
        exec_pattern = re.compile(
            r'(?:EXEC(?:UTE)?|CALL)\s+(?:\[?(\w+)\]?\.)?\[?(\w+)\]?(?:\s|\(|$)',
            re.IGNORECASE
        )

        for match in exec_pattern.finditer(body):
            sp_name = match.group(2)
            if sp_name and sp_name.upper() not in ['SP_EXECUTESQL']:
                sps.add(sp_name)

        return list(sps)

    def _extract_function_calls(self, body: str) -> List[str]:
        """Extract function calls (excluding built-ins)."""
        funcs = set()

        # function_name(
        func_pattern = re.compile(r'\b(\w+)\s*\(', re.IGNORECASE)

        # Built-in functions to exclude
        builtins = {
            'select', 'insert', 'update', 'delete', 'from', 'where', 'join',
            'count', 'sum', 'avg', 'max', 'min', 'cast', 'convert', 'coalesce',
            'isnull', 'nullif', 'case', 'when', 'then', 'else', 'end', 'if',
            'len', 'substring', 'left', 'right', 'trim', 'ltrim', 'rtrim',
            'upper', 'lower', 'replace', 'charindex', 'patindex', 'stuff',
            'getdate', 'dateadd', 'datediff', 'year', 'month', 'day',
            'round', 'ceiling', 'floor', 'abs', 'power', 'sqrt',
            'exists', 'not', 'in', 'between', 'like', 'is', 'null',
        }

        for match in func_pattern.finditer(body):
            func_name = match.group(1).lower()
            if func_name not in builtins:
                funcs.add(match.group(1))

        return list(funcs)

    def _calculate_complexity(self, body: str) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1

        # Decision points
        decision_patterns = [
            r'\bIF\b', r'\bELSE\s+IF\b', r'\bELSEIF\b',
            r'\bCASE\b', r'\bWHEN\b',
            r'\bWHILE\b', r'\bLOOP\b', r'\bFOR\b',
            r'\bAND\b', r'\bOR\b',
            r'\bCATCH\b', r'\bEXCEPTION\b',
        ]

        for pattern in decision_patterns:
            complexity += len(re.findall(pattern, body, re.IGNORECASE))

        return min(complexity, 100)

    def _get_complexity_level(self, complexity: int) -> ComplexityLevel:
        """Classify complexity level."""
        if complexity <= 5:
            return ComplexityLevel.LOW
        elif complexity <= 10:
            return ComplexityLevel.MEDIUM
        elif complexity <= 20:
            return ComplexityLevel.HIGH
        else:
            return ComplexityLevel.CRITICAL

    def _build_dependency_graph(self) -> None:
        """Build SP dependency graph."""
        for sp in self.result.stored_procedures:
            sp_key = f"{sp.schema}.{sp.name}"
            self.result.sp_dependencies[sp_key] = {
                "calls": sp.sps_called,
                "tables": sp.tables_used,
                "functions": sp.functions_called,
            }

            # Build table usage
            for table in sp.tables_used:
                if table not in self.result.table_usage:
                    self.result.table_usage[table] = {"read": [], "write": []}

                # Determine if read or write
                if any(kw in sp.body.upper() for kw in ['INSERT', 'UPDATE', 'DELETE']):
                    if table.upper() in sp.body.upper():
                        self.result.table_usage[table]["write"].append(sp_key)
                if 'SELECT' in sp.body.upper():
                    self.result.table_usage[table]["read"].append(sp_key)

    def _extract_business_rules(self) -> None:
        """Extract business rules from SPs."""
        for sp in self.result.stored_procedures:
            lines = sp.body.split('\n')

            for i, line in enumerate(lines, 1):
                for pattern, rule_type in self.VALIDATION_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Extract the condition
                        description = self._describe_validation(line, rule_type)

                        self.result.business_rules.append(BusinessRule(
                            sp_name=sp.name,
                            rule_type=rule_type,
                            description=description,
                            confidence=0.7,
                            code_snippet=line.strip(),
                            line_number=i,
                        ))

                        # Extract validation logic
                        if rule_type != 'error_handling':
                            field = self._extract_field_name(line)
                            self.result.validation_logic.append(ValidationLogic(
                                sp_name=sp.name,
                                field_name=field,
                                validation_type=rule_type,
                                condition=line.strip(),
                                error_handling=self._find_error_handling(lines, i),
                            ))

    def _describe_validation(self, line: str, rule_type: str) -> str:
        """Generate description for validation rule."""
        descriptions = {
            'null_check': 'Validates that field is not null',
            'range': 'Validates value is within acceptable range',
            'format': 'Validates value matches expected pattern',
            'lookup': 'Validates value exists in reference table',
            'length': 'Validates string length',
            'error_handling': 'Handles error condition',
        }
        return descriptions.get(rule_type, 'Business validation rule')

    def _extract_field_name(self, line: str) -> str:
        """Extract field/parameter name from validation."""
        match = re.search(r'[@]?(\w+)', line)
        return match.group(1) if match else 'unknown'

    def _find_error_handling(self, lines: List[str], start_line: int) -> str:
        """Find error handling for a validation."""
        for i in range(start_line, min(start_line + 5, len(lines))):
            if any(kw in lines[i].upper() for kw in ['RAISERROR', 'THROW', 'RETURN', 'SIGNAL']):
                return lines[i].strip()
        return 'No explicit error handling'

    def _analyze_complexity_distribution(self) -> None:
        """Analyze complexity distribution."""
        distribution = {level.value: 0 for level in ComplexityLevel}

        for sp in self.result.stored_procedures:
            distribution[sp.complexity_level.value] += 1

        self.result.complexity_distribution = distribution

        # Most complex SPs
        sorted_sps = sorted(self.result.stored_procedures, key=lambda x: x.complexity, reverse=True)
        self.result.most_complex_sps = [
            {"name": sp.name, "complexity": sp.complexity, "lines": sp.line_count}
            for sp in sorted_sps[:10]
        ]

        # Most called SPs
        call_counts = {}
        for sp in self.result.stored_procedures:
            for called in sp.sps_called:
                call_counts[called] = call_counts.get(called, 0) + 1

        sorted_calls = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)
        self.result.most_called_sps = [
            {"name": name, "call_count": count}
            for name, count in sorted_calls[:10]
        ]

    def _identify_vendor_specific(self) -> None:
        """Identify vendor-specific features."""
        if self.result.database_type != DatabaseType.SQL_SERVER:
            return

        for sp in self.result.stored_procedures:
            lines = sp.body.split('\n')

            for i, line in enumerate(lines, 1):
                for pattern, feature_name, impact, alternative in self.SQLSERVER_SPECIFIC:
                    if re.search(pattern, line, re.IGNORECASE):
                        self.result.vendor_specific_features.append(VendorSpecificFeature(
                            feature_name=feature_name,
                            sp_name=sp.name,
                            line_number=i,
                            database_type=self.result.database_type,
                            migration_impact=impact,
                            alternative=alternative,
                        ))

    def _identify_performance_issues(self) -> None:
        """Identify performance concerns."""
        for sp in self.result.stored_procedures:
            for pattern, concern, recommendation in self.PERFORMANCE_ANTIPATTERNS:
                if re.search(pattern, sp.body, re.IGNORECASE):
                    severity = 'high' if 'CURSOR' in concern or 'Loop' in concern else 'medium'
                    self.result.performance_concerns.append(PerformanceConcern(
                        sp_name=sp.name,
                        concern_type=concern,
                        description=f"Found {concern} in stored procedure",
                        recommendation=recommendation,
                        severity=severity,
                    ))

    def _calculate_scores(self) -> None:
        """Calculate overall scores."""
        # Complexity score (0-100, lower is better)
        if self.result.stored_procedures:
            avg_complexity = sum(sp.complexity for sp in self.result.stored_procedures) / len(self.result.stored_procedures)
            self.result.overall_complexity_score = min(100, int(avg_complexity * 5))
        else:
            self.result.overall_complexity_score = 0

        # Migration difficulty score (0-100, higher is harder)
        migration_score = 0
        migration_score += len(self.result.vendor_specific_features) * 2
        migration_score += sum(1 for sp in self.result.stored_procedures if sp.has_dynamic_sql) * 5
        migration_score += sum(1 for sp in self.result.stored_procedures if sp.has_cursor) * 3
        migration_score += self.result.complexity_distribution.get('critical', 0) * 10
        migration_score += self.result.complexity_distribution.get('high', 0) * 5
        self.result.migration_difficulty_score = min(100, migration_score)

        # Business logic coverage (0-100)
        # Estimate how much business logic is in SPs vs. application
        if self.result.stored_procedures:
            total_lines = sum(sp.line_count for sp in self.result.stored_procedures)
            logic_indicators = len(self.result.business_rules) + len(self.result.validation_logic)
            # Higher score means more logic in database
            self.result.business_logic_coverage = min(100, (logic_indicators * 10) + (total_lines // 100))
        else:
            self.result.business_logic_coverage = 0
