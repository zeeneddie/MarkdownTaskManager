"""
Database Analyzer Service

Week 65 Day 7: Specialized analyzer for database schemas and stored procedures.
Detects SQL Server, Oracle, MySQL/MariaDB proprietary patterns and assesses
migration complexity to PostgreSQL.

Features:
- SQL Server T-SQL analysis (stored procedures, triggers, functions)
- Oracle PL/SQL analysis (packages, procedures, triggers)
- MySQL/MariaDB analysis (stored procedures, events)
- Data type mapping recommendations
- Stored procedure complexity scoring
- Migration difficulty assessment
- Ora2Pg compatibility analysis

Author: Claude Code (Week 65)
Date: 2025-12-12
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.migration_analysis import (
    MigrationAnalysis,
    MigrationModule,
    LegacyPattern,
    FPBreakdown
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class DatabaseTable:
    """Represents a database table"""
    name: str
    schema_name: str = "dbo"
    columns: List[Dict[str, Any]] = field(default_factory=list)
    primary_key: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, Any]] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    row_count_estimate: int = 0
    has_identity: bool = False
    has_computed_columns: bool = False


@dataclass
class StoredProcedure:
    """Represents a stored procedure or function"""
    name: str
    schema_name: str = "dbo"
    object_type: str = "procedure"  # procedure, function, trigger, package
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    loc: int = 0
    complexity_score: float = 0.0
    uses_cursors: bool = False
    uses_temp_tables: bool = False
    uses_dynamic_sql: bool = False
    proprietary_functions: List[str] = field(default_factory=list)
    migration_notes: List[str] = field(default_factory=list)


@dataclass
class DatabaseView:
    """Represents a database view"""
    name: str
    schema_name: str = "dbo"
    is_materialized: bool = False
    is_indexed: bool = False
    base_tables: List[str] = field(default_factory=list)
    complexity_score: float = 0.0


@dataclass
class DatabasePatternMatch:
    """A detected database-specific pattern"""
    pattern_name: str
    pattern_category: str  # tsql, plsql, mysql, datatype
    file_path: str
    line_number: int
    code_snippet: str
    risk_level: str
    migration_note: str
    postgresql_equivalent: str
    fp_multiplier: float = 1.0
    requires_rewrite: bool = False


@dataclass
class DataTypeMapping:
    """Maps source database type to PostgreSQL"""
    source_type: str
    source_db: str
    postgresql_type: str
    requires_conversion: bool = False
    data_loss_risk: bool = False
    notes: str = ""


@dataclass
class DatabaseAnalysisResult:
    """Complete database analysis result"""
    tables: List[DatabaseTable] = field(default_factory=list)
    stored_procedures: List[StoredProcedure] = field(default_factory=list)
    views: List[DatabaseView] = field(default_factory=list)
    legacy_patterns: List[DatabasePatternMatch] = field(default_factory=list)
    data_type_mappings: List[DataTypeMapping] = field(default_factory=list)
    source_database: str = "unknown"
    source_version: Optional[str] = None
    total_sql_files: int = 0
    total_loc: int = 0
    total_tables: int = 0
    total_procedures: int = 0
    total_views: int = 0
    migration_difficulty: str = "medium"
    estimated_conversion_hours: float = 0.0
    ora2pg_compatibility: float = 0.0


# ============================================================================
# PATTERN DEFINITIONS
# ============================================================================

# SQL Server T-SQL Patterns
TSQL_PATTERNS = {
    "identity_column": {
        "pattern": r"IDENTITY\s*\(\s*\d+\s*,\s*\d+\s*\)",
        "risk": "low",
        "note": "IDENTITY converts to SERIAL or GENERATED ALWAYS AS IDENTITY",
        "pg_equivalent": "SERIAL or GENERATED ALWAYS AS IDENTITY",
        "multiplier": 1.1,
    },
    "top_clause": {
        "pattern": r"\bTOP\s+\d+\b|\bTOP\s*\(\s*\d+\s*\)",
        "risk": "low",
        "note": "TOP n converts to LIMIT n",
        "pg_equivalent": "LIMIT n",
        "multiplier": 1.0,
    },
    "nolock_hint": {
        "pattern": r"\bWITH\s*\(\s*NOLOCK\s*\)|\(NOLOCK\)",
        "risk": "medium",
        "note": "NOLOCK hint has no direct equivalent, may need READ UNCOMMITTED",
        "pg_equivalent": "SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED",
        "multiplier": 1.3,
    },
    "getdate": {
        "pattern": r"\bGETDATE\s*\(\s*\)",
        "risk": "low",
        "note": "GETDATE() converts to NOW() or CURRENT_TIMESTAMP",
        "pg_equivalent": "NOW() or CURRENT_TIMESTAMP",
        "multiplier": 1.0,
    },
    "getutcdate": {
        "pattern": r"\bGETUTCDATE\s*\(\s*\)",
        "risk": "low",
        "note": "GETUTCDATE() converts to NOW() AT TIME ZONE 'UTC'",
        "pg_equivalent": "NOW() AT TIME ZONE 'UTC'",
        "multiplier": 1.0,
    },
    "isnull": {
        "pattern": r"\bISNULL\s*\(",
        "risk": "low",
        "note": "ISNULL converts to COALESCE",
        "pg_equivalent": "COALESCE()",
        "multiplier": 1.0,
    },
    "charindex": {
        "pattern": r"\bCHARINDEX\s*\(",
        "risk": "low",
        "note": "CHARINDEX converts to POSITION or STRPOS",
        "pg_equivalent": "POSITION() or STRPOS()",
        "multiplier": 1.1,
    },
    "len_function": {
        "pattern": r"\bLEN\s*\(",
        "risk": "low",
        "note": "LEN() converts to LENGTH() or CHAR_LENGTH()",
        "pg_equivalent": "LENGTH() or CHAR_LENGTH()",
        "multiplier": 1.0,
    },
    "dateadd": {
        "pattern": r"\bDATEADD\s*\(",
        "risk": "medium",
        "note": "DATEADD requires interval syntax conversion",
        "pg_equivalent": "timestamp + INTERVAL 'n unit'",
        "multiplier": 1.2,
    },
    "datediff": {
        "pattern": r"\bDATEDIFF\s*\(",
        "risk": "medium",
        "note": "DATEDIFF requires DATE_PART or extraction",
        "pg_equivalent": "DATE_PART() or timestamp arithmetic",
        "multiplier": 1.2,
    },
    "convert_function": {
        "pattern": r"\bCONVERT\s*\(\s*\w+\s*,",
        "risk": "medium",
        "note": "CONVERT requires CAST or TO_CHAR/TO_DATE",
        "pg_equivalent": "CAST() or TO_CHAR()/TO_DATE()",
        "multiplier": 1.3,
    },
    "square_brackets": {
        "pattern": r"\[[\w\s]+\]",
        "risk": "low",
        "note": "Square bracket identifiers convert to double quotes",
        "pg_equivalent": 'Double quotes "identifier"',
        "multiplier": 1.0,
    },
    "varchar_max": {
        "pattern": r"\bVARCHAR\s*\(\s*MAX\s*\)|\bNVARCHAR\s*\(\s*MAX\s*\)",
        "risk": "low",
        "note": "VARCHAR(MAX) converts to TEXT",
        "pg_equivalent": "TEXT",
        "multiplier": 1.0,
    },
    "uniqueidentifier": {
        "pattern": r"\bUNIQUEIDENTIFIER\b",
        "risk": "low",
        "note": "UNIQUEIDENTIFIER converts to UUID",
        "pg_equivalent": "UUID",
        "multiplier": 1.0,
    },
    "datetime2": {
        "pattern": r"\bDATETIME2\b",
        "risk": "low",
        "note": "DATETIME2 converts to TIMESTAMP",
        "pg_equivalent": "TIMESTAMP",
        "multiplier": 1.0,
    },
    "money_type": {
        "pattern": r"\bMONEY\b|\bSMALLMONEY\b",
        "risk": "medium",
        "note": "MONEY type converts to NUMERIC with precision consideration",
        "pg_equivalent": "NUMERIC(19,4) or DECIMAL",
        "multiplier": 1.2,
    },
    "rowversion": {
        "pattern": r"\bROWVERSION\b|\bTIMESTAMP\b(?!\s*WITH)",
        "risk": "high",
        "note": "ROWVERSION has no direct equivalent, needs trigger-based solution",
        "pg_equivalent": "Custom trigger with version column",
        "multiplier": 1.5,
        "rewrite": True,
    },
    "computed_column": {
        "pattern": r"\bAS\s+\([^)]+\)\s*(PERSISTED)?",
        "risk": "medium",
        "note": "Computed columns need GENERATED ALWAYS AS (expr) STORED",
        "pg_equivalent": "GENERATED ALWAYS AS (expression) STORED",
        "multiplier": 1.3,
    },
    "cross_apply": {
        "pattern": r"\bCROSS\s+APPLY\b|\bOUTER\s+APPLY\b",
        "risk": "medium",
        "note": "CROSS/OUTER APPLY converts to LATERAL JOIN",
        "pg_equivalent": "LATERAL JOIN",
        "multiplier": 1.3,
    },
    "merge_statement": {
        "pattern": r"\bMERGE\s+INTO\b",
        "risk": "medium",
        "note": "MERGE converts to INSERT ON CONFLICT or separate statements",
        "pg_equivalent": "INSERT ... ON CONFLICT DO UPDATE",
        "multiplier": 1.4,
    },
    "table_variable": {
        "pattern": r"DECLARE\s+@\w+\s+TABLE\s*\(",
        "risk": "high",
        "note": "Table variables need conversion to temporary tables",
        "pg_equivalent": "CREATE TEMP TABLE",
        "multiplier": 1.5,
        "rewrite": True,
    },
    "cursor_fast_forward": {
        "pattern": r"\bFAST_FORWARD\b|\bLOCAL\s+FAST_FORWARD\b",
        "risk": "high",
        "note": "Cursor options need adjustment, consider set-based approach",
        "pg_equivalent": "Standard cursor or refactor to set-based",
        "multiplier": 1.6,
        "rewrite": True,
    },
    "try_catch": {
        "pattern": r"\bBEGIN\s+TRY\b.*\bEND\s+TRY\b|\bBEGIN\s+CATCH\b",
        "risk": "medium",
        "note": "TRY/CATCH converts to BEGIN/EXCEPTION/END",
        "pg_equivalent": "BEGIN ... EXCEPTION WHEN ... END",
        "multiplier": 1.3,
    },
    "raiserror": {
        "pattern": r"\bRAISERROR\s*\(|THROW\s+\d+",
        "risk": "medium",
        "note": "RAISERROR/THROW converts to RAISE EXCEPTION",
        "pg_equivalent": "RAISE EXCEPTION",
        "multiplier": 1.2,
    },
    "exec_dynamic": {
        "pattern": r"\bEXEC\s*\(\s*@|\bEXECUTE\s*\(\s*@|sp_executesql",
        "risk": "high",
        "note": "Dynamic SQL needs EXECUTE format() or EXECUTE $$ $$",
        "pg_equivalent": "EXECUTE format() or EXECUTE $body$",
        "multiplier": 1.5,
        "rewrite": True,
    },
    "temp_table_hash": {
        "pattern": r"#\w+|##\w+",
        "risk": "medium",
        "note": "Temp tables #name convert to CREATE TEMP TABLE",
        "pg_equivalent": "CREATE TEMP TABLE name",
        "multiplier": 1.2,
    },
    "set_nocount": {
        "pattern": r"\bSET\s+NOCOUNT\s+(ON|OFF)\b",
        "risk": "low",
        "note": "SET NOCOUNT has no equivalent, can be removed",
        "pg_equivalent": "Remove (not needed)",
        "multiplier": 1.0,
    },
    "output_clause": {
        "pattern": r"\bOUTPUT\s+(INSERTED|DELETED)\.",
        "risk": "medium",
        "note": "OUTPUT clause converts to RETURNING",
        "pg_equivalent": "RETURNING clause",
        "multiplier": 1.2,
    },
}

# Oracle PL/SQL Patterns
PLSQL_PATTERNS = {
    "varchar2": {
        "pattern": r"\bVARCHAR2\s*\(",
        "risk": "low",
        "note": "VARCHAR2 converts to VARCHAR",
        "pg_equivalent": "VARCHAR",
        "multiplier": 1.0,
    },
    "number_type": {
        "pattern": r"\bNUMBER\s*\(|\bNUMBER\b(?!\s*\()",
        "risk": "low",
        "note": "NUMBER converts to NUMERIC or INTEGER",
        "pg_equivalent": "NUMERIC or INTEGER",
        "multiplier": 1.1,
    },
    "clob_blob": {
        "pattern": r"\bCLOB\b|\bBLOB\b|\bNCLOB\b",
        "risk": "low",
        "note": "CLOB/BLOB converts to TEXT/BYTEA",
        "pg_equivalent": "TEXT or BYTEA",
        "multiplier": 1.1,
    },
    "sysdate": {
        "pattern": r"\bSYSDATE\b",
        "risk": "low",
        "note": "SYSDATE converts to CURRENT_TIMESTAMP",
        "pg_equivalent": "CURRENT_TIMESTAMP",
        "multiplier": 1.0,
    },
    "systimestamp": {
        "pattern": r"\bSYSTIMESTAMP\b",
        "risk": "low",
        "note": "SYSTIMESTAMP converts to CURRENT_TIMESTAMP",
        "pg_equivalent": "CURRENT_TIMESTAMP",
        "multiplier": 1.0,
    },
    "nvl_function": {
        "pattern": r"\bNVL\s*\(",
        "risk": "low",
        "note": "NVL converts to COALESCE",
        "pg_equivalent": "COALESCE()",
        "multiplier": 1.0,
    },
    "nvl2_function": {
        "pattern": r"\bNVL2\s*\(",
        "risk": "medium",
        "note": "NVL2 converts to CASE expression or custom function",
        "pg_equivalent": "CASE WHEN expr IS NOT NULL THEN ... ELSE ... END",
        "multiplier": 1.2,
    },
    "decode_function": {
        "pattern": r"\bDECODE\s*\(",
        "risk": "medium",
        "note": "DECODE converts to CASE expression",
        "pg_equivalent": "CASE expression",
        "multiplier": 1.3,
    },
    "rownum": {
        "pattern": r"\bROWNUM\b",
        "risk": "medium",
        "note": "ROWNUM converts to ROW_NUMBER() or LIMIT",
        "pg_equivalent": "ROW_NUMBER() OVER() or LIMIT",
        "multiplier": 1.3,
    },
    "rowid": {
        "pattern": r"\bROWID\b",
        "risk": "high",
        "note": "ROWID has no direct equivalent, use ctid cautiously",
        "pg_equivalent": "ctid (internal) or surrogate key",
        "multiplier": 1.5,
        "rewrite": True,
    },
    "connect_by": {
        "pattern": r"\bCONNECT\s+BY\b|\bSTART\s+WITH\b",
        "risk": "high",
        "note": "Hierarchical queries need WITH RECURSIVE",
        "pg_equivalent": "WITH RECURSIVE CTE",
        "multiplier": 1.8,
        "rewrite": True,
    },
    "dual_table": {
        "pattern": r"\bFROM\s+DUAL\b",
        "risk": "low",
        "note": "FROM DUAL can be removed or use VALUES",
        "pg_equivalent": "Remove FROM clause or use VALUES ()",
        "multiplier": 1.0,
    },
    "sequence_nextval": {
        "pattern": r"\w+\.NEXTVAL|\w+\.CURRVAL",
        "risk": "low",
        "note": "sequence.NEXTVAL converts to nextval('sequence')",
        "pg_equivalent": "nextval('sequence_name')",
        "multiplier": 1.1,
    },
    "package_definition": {
        "pattern": r"\bCREATE\s+(OR\s+REPLACE\s+)?PACKAGE\b",
        "risk": "high",
        "note": "Packages need conversion to schemas + functions",
        "pg_equivalent": "Schema with separate functions",
        "multiplier": 2.0,
        "rewrite": True,
    },
    "package_body": {
        "pattern": r"\bCREATE\s+(OR\s+REPLACE\s+)?PACKAGE\s+BODY\b",
        "risk": "high",
        "note": "Package bodies need conversion to individual functions",
        "pg_equivalent": "Separate CREATE FUNCTION statements",
        "multiplier": 2.0,
        "rewrite": True,
    },
    "type_object": {
        "pattern": r"\bCREATE\s+(OR\s+REPLACE\s+)?TYPE\b.*\bAS\s+OBJECT\b",
        "risk": "high",
        "note": "Object types need conversion to composite types",
        "pg_equivalent": "CREATE TYPE ... AS ()",
        "multiplier": 1.8,
        "rewrite": True,
    },
    "bulk_collect": {
        "pattern": r"\bBULK\s+COLLECT\b|\bFORALL\b",
        "risk": "high",
        "note": "Bulk operations need array-based approach",
        "pg_equivalent": "Array operations or set-based SQL",
        "multiplier": 1.7,
        "rewrite": True,
    },
    "autonomous_transaction": {
        "pattern": r"PRAGMA\s+AUTONOMOUS_TRANSACTION",
        "risk": "critical",
        "note": "Autonomous transactions need dblink or separate connection",
        "pg_equivalent": "dblink or separate session",
        "multiplier": 2.5,
        "rewrite": True,
    },
    "dbms_output": {
        "pattern": r"\bDBMS_OUTPUT\.",
        "risk": "medium",
        "note": "DBMS_OUTPUT converts to RAISE NOTICE",
        "pg_equivalent": "RAISE NOTICE",
        "multiplier": 1.2,
    },
    "utl_file": {
        "pattern": r"\bUTL_FILE\.",
        "risk": "high",
        "note": "UTL_FILE needs COPY or pg_read_file/pg_write_file",
        "pg_equivalent": "COPY or extension functions",
        "multiplier": 1.8,
        "rewrite": True,
    },
    "dbms_sql": {
        "pattern": r"\bDBMS_SQL\.",
        "risk": "high",
        "note": "DBMS_SQL converts to EXECUTE with format()",
        "pg_equivalent": "EXECUTE format()",
        "multiplier": 1.7,
        "rewrite": True,
    },
    "ref_cursor": {
        "pattern": r"\bREF\s+CURSOR\b|\bSYS_REFCURSOR\b",
        "risk": "medium",
        "note": "REF CURSOR converts to REFCURSOR",
        "pg_equivalent": "REFCURSOR",
        "multiplier": 1.3,
    },
    "table_function": {
        "pattern": r"\bTABLE\s*\(\s*\w+\s*\(",
        "risk": "high",
        "note": "Table functions need RETURNS TABLE or SETOF",
        "pg_equivalent": "RETURNS TABLE or RETURNS SETOF",
        "multiplier": 1.6,
        "rewrite": True,
    },
    "pipelined": {
        "pattern": r"\bPIPELINED\b",
        "risk": "high",
        "note": "Pipelined functions need RETURN NEXT approach",
        "pg_equivalent": "RETURN NEXT or RETURN QUERY",
        "multiplier": 1.7,
        "rewrite": True,
    },
}

# MySQL/MariaDB Patterns
MYSQL_PATTERNS = {
    "auto_increment": {
        "pattern": r"\bAUTO_INCREMENT\b",
        "risk": "low",
        "note": "AUTO_INCREMENT converts to SERIAL or IDENTITY",
        "pg_equivalent": "SERIAL or GENERATED ALWAYS AS IDENTITY",
        "multiplier": 1.0,
    },
    "backtick_quotes": {
        "pattern": r"`[\w]+`",
        "risk": "low",
        "note": "Backtick identifiers convert to double quotes",
        "pg_equivalent": 'Double quotes "identifier"',
        "multiplier": 1.0,
    },
    "tinyint": {
        "pattern": r"\bTINYINT\b",
        "risk": "low",
        "note": "TINYINT converts to SMALLINT",
        "pg_equivalent": "SMALLINT",
        "multiplier": 1.0,
    },
    "mediumint": {
        "pattern": r"\bMEDIUMINT\b",
        "risk": "low",
        "note": "MEDIUMINT converts to INTEGER",
        "pg_equivalent": "INTEGER",
        "multiplier": 1.0,
    },
    "unsigned": {
        "pattern": r"\bUNSIGNED\b",
        "risk": "medium",
        "note": "UNSIGNED needs constraint or larger type",
        "pg_equivalent": "CHECK constraint or larger integer type",
        "multiplier": 1.2,
    },
    "enum_type": {
        "pattern": r"\bENUM\s*\(",
        "risk": "medium",
        "note": "ENUM needs CREATE TYPE ... AS ENUM",
        "pg_equivalent": "CREATE TYPE ... AS ENUM (...)",
        "multiplier": 1.3,
    },
    "set_type": {
        "pattern": r"\bSET\s*\(",
        "risk": "high",
        "note": "SET type needs array or separate table",
        "pg_equivalent": "Array type or junction table",
        "multiplier": 1.5,
        "rewrite": True,
    },
    "double_type": {
        "pattern": r"\bDOUBLE\b(?!\s+PRECISION)",
        "risk": "low",
        "note": "DOUBLE converts to DOUBLE PRECISION",
        "pg_equivalent": "DOUBLE PRECISION",
        "multiplier": 1.0,
    },
    "datetime_type": {
        "pattern": r"\bDATETIME\b(?!\d)",
        "risk": "low",
        "note": "DATETIME converts to TIMESTAMP",
        "pg_equivalent": "TIMESTAMP",
        "multiplier": 1.0,
    },
    "on_update_timestamp": {
        "pattern": r"\bON\s+UPDATE\s+CURRENT_TIMESTAMP\b",
        "risk": "medium",
        "note": "ON UPDATE needs trigger for auto-update",
        "pg_equivalent": "Trigger function for timestamp update",
        "multiplier": 1.4,
        "rewrite": True,
    },
    "ifnull": {
        "pattern": r"\bIFNULL\s*\(",
        "risk": "low",
        "note": "IFNULL converts to COALESCE",
        "pg_equivalent": "COALESCE()",
        "multiplier": 1.0,
    },
    "if_function": {
        "pattern": r"\bIF\s*\(\s*[^,]+,",
        "risk": "medium",
        "note": "IF() function converts to CASE expression",
        "pg_equivalent": "CASE WHEN ... THEN ... ELSE ... END",
        "multiplier": 1.2,
    },
    "limit_offset": {
        "pattern": r"\bLIMIT\s+\d+\s*,\s*\d+",
        "risk": "low",
        "note": "LIMIT x,y converts to LIMIT y OFFSET x",
        "pg_equivalent": "LIMIT y OFFSET x",
        "multiplier": 1.0,
    },
    "group_concat": {
        "pattern": r"\bGROUP_CONCAT\s*\(",
        "risk": "medium",
        "note": "GROUP_CONCAT converts to STRING_AGG",
        "pg_equivalent": "STRING_AGG()",
        "multiplier": 1.2,
    },
    "straight_join": {
        "pattern": r"\bSTRAIGHT_JOIN\b",
        "risk": "medium",
        "note": "STRAIGHT_JOIN has no equivalent, use query hints",
        "pg_equivalent": "Remove or use pg_hint_plan extension",
        "multiplier": 1.3,
    },
    "replace_into": {
        "pattern": r"\bREPLACE\s+INTO\b",
        "risk": "medium",
        "note": "REPLACE INTO converts to INSERT ON CONFLICT",
        "pg_equivalent": "INSERT ... ON CONFLICT DO UPDATE",
        "multiplier": 1.3,
    },
    "insert_ignore": {
        "pattern": r"\bINSERT\s+IGNORE\b",
        "risk": "medium",
        "note": "INSERT IGNORE converts to INSERT ON CONFLICT DO NOTHING",
        "pg_equivalent": "INSERT ... ON CONFLICT DO NOTHING",
        "multiplier": 1.2,
    },
    "mysql_engine": {
        "pattern": r"\bENGINE\s*=\s*\w+",
        "risk": "low",
        "note": "ENGINE clause should be removed",
        "pg_equivalent": "Remove (PostgreSQL uses single storage engine)",
        "multiplier": 1.0,
    },
    "mysql_delimiter": {
        "pattern": r"DELIMITER\s+[^\s]+",
        "risk": "low",
        "note": "DELIMITER not needed in PostgreSQL",
        "pg_equivalent": "Remove (use $$ for procedure bodies)",
        "multiplier": 1.0,
    },
}


# ============================================================================
# DATA TYPE MAPPINGS
# ============================================================================

SQL_SERVER_TYPE_MAP = {
    "BIT": ("BOOLEAN", False, ""),
    "TINYINT": ("SMALLINT", False, ""),
    "SMALLINT": ("SMALLINT", False, ""),
    "INT": ("INTEGER", False, ""),
    "BIGINT": ("BIGINT", False, ""),
    "DECIMAL": ("NUMERIC", False, ""),
    "NUMERIC": ("NUMERIC", False, ""),
    "MONEY": ("NUMERIC(19,4)", False, "Consider DECIMAL for better precision"),
    "SMALLMONEY": ("NUMERIC(10,4)", False, ""),
    "FLOAT": ("DOUBLE PRECISION", False, ""),
    "REAL": ("REAL", False, ""),
    "DATE": ("DATE", False, ""),
    "TIME": ("TIME", False, ""),
    "DATETIME": ("TIMESTAMP", False, ""),
    "DATETIME2": ("TIMESTAMP", False, ""),
    "SMALLDATETIME": ("TIMESTAMP", False, ""),
    "DATETIMEOFFSET": ("TIMESTAMP WITH TIME ZONE", False, ""),
    "CHAR": ("CHAR", False, ""),
    "VARCHAR": ("VARCHAR", False, ""),
    "NCHAR": ("CHAR", False, "PostgreSQL is UTF-8 native"),
    "NVARCHAR": ("VARCHAR", False, "PostgreSQL is UTF-8 native"),
    "TEXT": ("TEXT", False, ""),
    "NTEXT": ("TEXT", False, ""),
    "BINARY": ("BYTEA", False, ""),
    "VARBINARY": ("BYTEA", False, ""),
    "IMAGE": ("BYTEA", False, ""),
    "UNIQUEIDENTIFIER": ("UUID", False, ""),
    "XML": ("XML", False, ""),
    "GEOGRAPHY": ("GEOGRAPHY", False, "Requires PostGIS"),
    "GEOMETRY": ("GEOMETRY", False, "Requires PostGIS"),
    "HIERARCHYID": ("LTREE", True, "Requires ltree extension, significant rewrite"),
    "ROWVERSION": ("BYTEA", True, "Need trigger for auto-update"),
    "SQL_VARIANT": ("TEXT", True, "Lose type information"),
}

ORACLE_TYPE_MAP = {
    "VARCHAR2": ("VARCHAR", False, ""),
    "NVARCHAR2": ("VARCHAR", False, ""),
    "CHAR": ("CHAR", False, ""),
    "NCHAR": ("CHAR", False, ""),
    "NUMBER": ("NUMERIC", False, ""),
    "BINARY_FLOAT": ("REAL", False, ""),
    "BINARY_DOUBLE": ("DOUBLE PRECISION", False, ""),
    "DATE": ("TIMESTAMP", False, "Oracle DATE includes time"),
    "TIMESTAMP": ("TIMESTAMP", False, ""),
    "TIMESTAMP WITH TIME ZONE": ("TIMESTAMP WITH TIME ZONE", False, ""),
    "TIMESTAMP WITH LOCAL TIME ZONE": ("TIMESTAMP WITH TIME ZONE", False, ""),
    "INTERVAL YEAR TO MONTH": ("INTERVAL", False, ""),
    "INTERVAL DAY TO SECOND": ("INTERVAL", False, ""),
    "CLOB": ("TEXT", False, ""),
    "NCLOB": ("TEXT", False, ""),
    "BLOB": ("BYTEA", False, ""),
    "BFILE": ("TEXT", True, "Store file path, handle separately"),
    "RAW": ("BYTEA", False, ""),
    "LONG": ("TEXT", False, "Deprecated in Oracle"),
    "LONG RAW": ("BYTEA", False, "Deprecated in Oracle"),
    "ROWID": ("TEXT", True, "Use surrogate key instead"),
    "UROWID": ("TEXT", True, "Use surrogate key instead"),
    "XMLTYPE": ("XML", False, ""),
    "SDO_GEOMETRY": ("GEOMETRY", False, "Requires PostGIS"),
}

MYSQL_TYPE_MAP = {
    "TINYINT": ("SMALLINT", False, ""),
    "SMALLINT": ("SMALLINT", False, ""),
    "MEDIUMINT": ("INTEGER", False, ""),
    "INT": ("INTEGER", False, ""),
    "BIGINT": ("BIGINT", False, ""),
    "DECIMAL": ("NUMERIC", False, ""),
    "FLOAT": ("REAL", False, ""),
    "DOUBLE": ("DOUBLE PRECISION", False, ""),
    "BIT": ("BIT", False, ""),
    "DATE": ("DATE", False, ""),
    "DATETIME": ("TIMESTAMP", False, ""),
    "TIMESTAMP": ("TIMESTAMP", False, ""),
    "TIME": ("TIME", False, ""),
    "YEAR": ("SMALLINT", False, "Or use DATE"),
    "CHAR": ("CHAR", False, ""),
    "VARCHAR": ("VARCHAR", False, ""),
    "BINARY": ("BYTEA", False, ""),
    "VARBINARY": ("BYTEA", False, ""),
    "TINYBLOB": ("BYTEA", False, ""),
    "BLOB": ("BYTEA", False, ""),
    "MEDIUMBLOB": ("BYTEA", False, ""),
    "LONGBLOB": ("BYTEA", False, ""),
    "TINYTEXT": ("TEXT", False, ""),
    "TEXT": ("TEXT", False, ""),
    "MEDIUMTEXT": ("TEXT", False, ""),
    "LONGTEXT": ("TEXT", False, ""),
    "ENUM": ("Custom TYPE", True, "Create TYPE AS ENUM"),
    "SET": ("ARRAY", True, "Or use junction table"),
    "JSON": ("JSONB", False, "JSONB preferred for indexing"),
}


# ============================================================================
# DATABASE ANALYZER SERVICE
# ============================================================================

class DatabaseAnalyzerService:
    """
    Specialized analyzer for database schemas and SQL code.

    Analyzes:
    - SQL Server T-SQL
    - Oracle PL/SQL
    - MySQL/MariaDB
    - Stored procedures, triggers, functions
    - Data type compatibility
    - Migration complexity
    """

    SQL_EXTENSIONS = {".sql", ".pks", ".pkb", ".prc", ".fnc", ".trg", ".vw"}
    SKIP_DIRS = {".git", "node_modules", "vendor", "__pycache__"}

    def __init__(self, db: AsyncSession):
        """Initialize with database session"""
        self.db = db
        self.result = DatabaseAnalysisResult()

    async def analyze(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> DatabaseAnalysisResult:
        """
        Perform complete database analysis.

        Args:
            analysis: Parent MigrationAnalysis record
            repo_path: Path to repository

        Returns:
            DatabaseAnalysisResult with all findings
        """
        logger.info(f"Starting database analysis for {repo_path}")

        # Phase 1: Detect source database
        self._detect_database_type(repo_path)

        # Phase 2: Analyze SQL files for tables
        await self._analyze_tables(analysis, repo_path)

        # Phase 3: Analyze stored procedures
        await self._analyze_procedures(analysis, repo_path)

        # Phase 4: Analyze views
        await self._analyze_views(analysis, repo_path)

        # Phase 5: Detect all database patterns
        await self._detect_patterns(analysis, repo_path)

        # Phase 6: Generate data type mappings
        self._generate_type_mappings()

        # Phase 7: Calculate metrics
        self._calculate_metrics()

        logger.info(
            f"Database analysis complete: {self.result.source_database}, "
            f"{self.result.total_tables} tables, {self.result.total_procedures} procedures, "
            f"{len(self.result.legacy_patterns)} patterns"
        )

        return self.result

    def _detect_database_type(self, repo_path: Path) -> None:
        """Detect source database type from SQL files"""
        indicators = defaultdict(int)

        for sql_path in repo_path.rglob("*.sql"):
            if self._should_skip(sql_path):
                continue

            try:
                content = sql_path.read_text(encoding="utf-8", errors="ignore").upper()
            except Exception:
                continue

            # SQL Server indicators
            if "GETDATE()" in content or "ISNULL(" in content or "VARCHAR(MAX)" in content:
                indicators["sqlserver"] += 3
            if "[DBO]" in content or "NVARCHAR" in content:
                indicators["sqlserver"] += 2
            if "SET NOCOUNT" in content or "@" in content:
                indicators["sqlserver"] += 1

            # Oracle indicators
            if "VARCHAR2" in content or "NUMBER(" in content:
                indicators["oracle"] += 3
            if "SYSDATE" in content or "NVL(" in content:
                indicators["oracle"] += 2
            if "FROM DUAL" in content or "ROWNUM" in content:
                indicators["oracle"] += 2
            if "CREATE PACKAGE" in content:
                indicators["oracle"] += 5

            # MySQL indicators
            if "AUTO_INCREMENT" in content or "`" in content:
                indicators["mysql"] += 3
            if "ENGINE=" in content or "IFNULL(" in content:
                indicators["mysql"] += 2
            if "DELIMITER" in content:
                indicators["mysql"] += 2

        if indicators:
            self.result.source_database = max(indicators.items(), key=lambda x: x[1])[0]
        else:
            self.result.source_database = "unknown"

        logger.info(f"Detected database: {self.result.source_database}")

    async def _analyze_tables(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Analyze CREATE TABLE statements"""
        logger.info("Analyzing database tables...")

        create_table_pattern = r"CREATE\s+TABLE\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)\s*\("

        for sql_path in repo_path.rglob("*.sql"):
            if self._should_skip(sql_path):
                continue

            try:
                content = sql_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            self.result.total_sql_files += 1
            self.result.total_loc += len([l for l in content.splitlines() if l.strip()])

            for match in re.finditer(create_table_pattern, content, re.IGNORECASE):
                schema_name = match.group(1) or "dbo"
                table_name = match.group(2)

                table = DatabaseTable(
                    name=table_name,
                    schema_name=schema_name,
                )

                # Check for IDENTITY
                table.has_identity = bool(re.search(r"IDENTITY\s*\(", content[match.end():match.end()+500], re.IGNORECASE))

                # Check for computed columns
                table.has_computed_columns = bool(re.search(r"\bAS\s+\([^)]+\)", content[match.end():match.end()+1000], re.IGNORECASE))

                self.result.tables.append(table)

                # Create module record
                db_module = MigrationModule(
                    analysis_id=analysis.id,
                    name=f"{schema_name}.{table_name}",
                    module_type="database_table",
                    stack_type=self.result.source_database,
                    file_path=str(sql_path.relative_to(repo_path)),
                    migration_difficulty="easy" if not table.has_computed_columns else "medium",
                    migration_target="PostgreSQL table",
                )
                self.db.add(db_module)

        self.result.total_tables = len(self.result.tables)
        await self.db.commit()

    async def _analyze_procedures(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Analyze stored procedures and functions"""
        logger.info("Analyzing stored procedures...")

        proc_patterns = [
            (r"CREATE\s+(OR\s+REPLACE\s+)?PROC(?:EDURE)?\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)", "procedure"),
            (r"CREATE\s+(OR\s+REPLACE\s+)?FUNCTION\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)", "function"),
            (r"CREATE\s+(OR\s+REPLACE\s+)?TRIGGER\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)", "trigger"),
            (r"CREATE\s+(OR\s+REPLACE\s+)?PACKAGE\s+(?:BODY\s+)?(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)", "package"),
        ]

        for sql_path in repo_path.rglob("*.sql"):
            if self._should_skip(sql_path):
                continue

            try:
                content = sql_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for pattern, obj_type in proc_patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    schema_name = match.group(2) or "dbo"
                    proc_name = match.group(3)

                    # Find the procedure body
                    start_pos = match.end()
                    # Simple heuristic: find next CREATE or end of file
                    next_create = re.search(r"\bCREATE\s+(OR\s+REPLACE\s+)?(PROC|FUNCTION|TRIGGER|PACKAGE)", content[start_pos:], re.IGNORECASE)
                    end_pos = start_pos + next_create.start() if next_create else len(content)
                    proc_body = content[match.start():end_pos]

                    proc = StoredProcedure(
                        name=proc_name,
                        schema_name=schema_name,
                        object_type=obj_type,
                        loc=len([l for l in proc_body.splitlines() if l.strip()]),
                    )

                    # Analyze complexity indicators
                    proc.uses_cursors = bool(re.search(r"\bDECLARE\s+\w+\s+CURSOR\b|\bFOR\s+\w+\s+IN\b", proc_body, re.IGNORECASE))
                    proc.uses_temp_tables = bool(re.search(r"#\w+|CREATE\s+TEMP|CREATE\s+TEMPORARY", proc_body, re.IGNORECASE))
                    proc.uses_dynamic_sql = bool(re.search(r"EXEC\s*\(\s*@|EXECUTE\s+IMMEDIATE|sp_executesql", proc_body, re.IGNORECASE))

                    # Calculate complexity
                    complexity = proc.loc * 0.1
                    if proc.uses_cursors:
                        complexity += 5
                    if proc.uses_temp_tables:
                        complexity += 3
                    if proc.uses_dynamic_sql:
                        complexity += 8
                    proc.complexity_score = complexity

                    self.result.stored_procedures.append(proc)

                    # Determine migration difficulty
                    if proc.uses_dynamic_sql or obj_type == "package":
                        difficulty = "complex"
                    elif proc.uses_cursors or complexity > 20:
                        difficulty = "hard"
                    elif complexity > 10:
                        difficulty = "medium"
                    else:
                        difficulty = "easy"

                    # Create module record
                    db_module = MigrationModule(
                        analysis_id=analysis.id,
                        name=f"{schema_name}.{proc_name}",
                        module_type=f"database_{obj_type}",
                        stack_type=self.result.source_database,
                        file_path=str(sql_path.relative_to(repo_path)),
                        loc=proc.loc,
                        cyclomatic_complexity=proc.complexity_score,
                        migration_difficulty=difficulty,
                        migration_target=f"PostgreSQL {obj_type}",
                    )
                    self.db.add(db_module)

        self.result.total_procedures = len(self.result.stored_procedures)
        await self.db.commit()

    async def _analyze_views(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Analyze database views"""
        logger.info("Analyzing database views...")

        view_pattern = r"CREATE\s+(OR\s+REPLACE\s+)?(MATERIALIZED\s+)?VIEW\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)"

        for sql_path in repo_path.rglob("*.sql"):
            if self._should_skip(sql_path):
                continue

            try:
                content = sql_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for match in re.finditer(view_pattern, content, re.IGNORECASE):
                is_materialized = match.group(2) is not None
                schema_name = match.group(3) or "dbo"
                view_name = match.group(4)

                view = DatabaseView(
                    name=view_name,
                    schema_name=schema_name,
                    is_materialized=is_materialized,
                )

                self.result.views.append(view)

        self.result.total_views = len(self.result.views)

    async def _detect_patterns(
        self,
        analysis: MigrationAnalysis,
        repo_path: Path
    ) -> None:
        """Detect database-specific patterns"""
        logger.info("Detecting database patterns...")

        # Always scan ALL database patterns - migration projects often have mixed legacy code
        # The detected database is used for difficulty estimation, but we need to find all patterns
        all_patterns = {}
        all_patterns.update({f"tsql_{k}": {**v, "category": "tsql"} for k, v in TSQL_PATTERNS.items()})
        all_patterns.update({f"plsql_{k}": {**v, "category": "plsql"} for k, v in PLSQL_PATTERNS.items()})
        all_patterns.update({f"mysql_{k}": {**v, "category": "mysql"} for k, v in MYSQL_PATTERNS.items()})

        logger.info(f"Scanning for {len(all_patterns)} database patterns across all database types")

        for sql_path in repo_path.rglob("*.sql"):
            if self._should_skip(sql_path):
                continue

            try:
                content = sql_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for pattern_name, pattern_def in all_patterns.items():
                try:
                    matches = list(re.finditer(pattern_def["pattern"], content, re.IGNORECASE))
                except re.error:
                    continue

                for match in matches[:10]:  # Limit per pattern
                    line_num = content[:match.start()].count('\n') + 1

                    pattern_match = DatabasePatternMatch(
                        pattern_name=pattern_name,
                        pattern_category=pattern_def["category"],
                        file_path=str(sql_path.relative_to(repo_path)),
                        line_number=line_num,
                        code_snippet=match.group()[:100],
                        risk_level=pattern_def["risk"],
                        migration_note=pattern_def["note"],
                        postgresql_equivalent=pattern_def["pg_equivalent"],
                        fp_multiplier=pattern_def.get("multiplier", 1.0),
                        requires_rewrite=pattern_def.get("rewrite", False),
                    )
                    self.result.legacy_patterns.append(pattern_match)

                    # Store in database
                    db_pattern = LegacyPattern(
                        analysis_id=analysis.id,
                        pattern_name=pattern_name,
                        pattern_category=pattern_def["category"],
                        file_path=str(sql_path.relative_to(repo_path)),
                        line_number=line_num,
                        code_snippet=match.group()[:200],
                        risk_level=pattern_def["risk"],
                        fp_multiplier=pattern_def.get("multiplier", 1.0),
                        migration_note=pattern_def["note"],
                        migration_target=pattern_def["pg_equivalent"],
                    )
                    self.db.add(db_pattern)

        await self.db.commit()

    def _generate_type_mappings(self) -> None:
        """Generate data type mappings based on source database"""
        type_map = {}
        if self.result.source_database == "sqlserver":
            type_map = SQL_SERVER_TYPE_MAP
        elif self.result.source_database == "oracle":
            type_map = ORACLE_TYPE_MAP
        elif self.result.source_database == "mysql":
            type_map = MYSQL_TYPE_MAP

        for source_type, (pg_type, needs_conversion, notes) in type_map.items():
            mapping = DataTypeMapping(
                source_type=source_type,
                source_db=self.result.source_database,
                postgresql_type=pg_type,
                requires_conversion=needs_conversion,
                data_loss_risk=needs_conversion,
                notes=notes,
            )
            self.result.data_type_mappings.append(mapping)

    def _calculate_metrics(self) -> None:
        """Calculate overall metrics"""
        # Count patterns by risk
        critical_count = sum(1 for p in self.result.legacy_patterns if p.risk_level == "critical")
        high_count = sum(1 for p in self.result.legacy_patterns if p.risk_level == "high")
        rewrite_count = sum(1 for p in self.result.legacy_patterns if p.requires_rewrite)

        # Migration difficulty
        if critical_count > 10 or rewrite_count > 20:
            self.result.migration_difficulty = "complex"
        elif critical_count > 5 or high_count > 30 or rewrite_count > 10:
            self.result.migration_difficulty = "hard"
        elif high_count > 10 or rewrite_count > 5:
            self.result.migration_difficulty = "medium"
        else:
            self.result.migration_difficulty = "easy"

        # Estimated conversion hours (rough estimate)
        base_hours = self.result.total_tables * 0.5
        proc_hours = sum(p.complexity_score * 0.5 for p in self.result.stored_procedures)
        pattern_hours = sum(p.fp_multiplier for p in self.result.legacy_patterns)
        self.result.estimated_conversion_hours = base_hours + proc_hours + pattern_hours

        # Ora2Pg compatibility (percentage of patterns that are straightforward)
        if self.result.legacy_patterns:
            easy_patterns = sum(1 for p in self.result.legacy_patterns if p.risk_level in ["low", "medium"])
            self.result.ora2pg_compatibility = (easy_patterns / len(self.result.legacy_patterns)) * 100
        else:
            self.result.ora2pg_compatibility = 100.0

    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        return any(skip in file_path.parts for skip in self.SKIP_DIRS)


def get_database_analyzer_service(db: AsyncSession) -> DatabaseAnalyzerService:
    """Factory function to create DatabaseAnalyzerService instance"""
    return DatabaseAnalyzerService(db)
