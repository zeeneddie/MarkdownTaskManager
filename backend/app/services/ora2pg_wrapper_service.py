"""
Ora2Pg Wrapper Service

Week 67 Day 8: Wrapper service for ora2pg tool integration.
Provides Oracle to PostgreSQL migration analysis and schema conversion assessment.

Features:
- Ora2pg CLI integration (if installed)
- Fallback analysis using pattern-based detection
- Migration cost estimation (A-E scale)
- PL/SQL to PL/pgSQL complexity assessment
- Schema extraction and analysis
- Object type statistics

Author: Claude Code (Week 67)
Date: 2025-12-15
"""

import os
import re
import json
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class Ora2PgCostLevel(str, Enum):
    """Ora2pg migration cost levels (A-E scale)"""
    A = "A"  # Trivial - automatic conversion
    B = "B"  # Simple - minor manual adjustments
    C = "C"  # Medium - moderate rewrite needed
    D = "D"  # Difficult - significant restructuring
    E = "E"  # Extreme - complete redesign required


@dataclass
class Ora2PgObjectStats:
    """Statistics for a specific Oracle object type"""
    object_type: str
    count: int = 0
    invalid_count: int = 0
    cost_level: Ora2PgCostLevel = Ora2PgCostLevel.B
    estimated_hours: float = 0.0
    notes: List[str] = field(default_factory=list)


@dataclass
class Ora2PgSchemaInfo:
    """Oracle schema information"""
    schema_name: str
    tables: List[str] = field(default_factory=list)
    views: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    sequences: List[str] = field(default_factory=list)
    packages: List[str] = field(default_factory=list)
    procedures: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    types: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    total_loc: int = 0


@dataclass
class Ora2PgPatternIssue:
    """Oracle-specific pattern that needs conversion"""
    pattern_name: str
    category: str  # datatype, plsql, syntax, function
    occurrences: int = 0
    files: List[str] = field(default_factory=list)
    cost_level: Ora2PgCostLevel = Ora2PgCostLevel.B
    conversion_strategy: str = ""
    pg_equivalent: str = ""


@dataclass
class Ora2PgAnalysisResult:
    """Complete ora2pg analysis result"""
    tool_available: bool = False
    tool_version: Optional[str] = None

    # Schema summary
    schemas_analyzed: List[str] = field(default_factory=list)
    total_objects: int = 0
    total_loc: int = 0

    # Object statistics by type
    object_stats: Dict[str, Ora2PgObjectStats] = field(default_factory=dict)

    # Pattern issues
    pattern_issues: List[Ora2PgPatternIssue] = field(default_factory=list)

    # Cost summary
    overall_cost_level: Ora2PgCostLevel = Ora2PgCostLevel.B
    total_estimated_hours: float = 0.0
    estimated_cost_breakdown: Dict[str, float] = field(default_factory=dict)

    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)

    # Raw output (if ora2pg was run)
    raw_report: Optional[str] = None


# Oracle to PostgreSQL conversion patterns
ORACLE_CONVERSION_PATTERNS = {
    # PL/SQL constructs
    "package_body": {
        "pattern": r"\bCREATE\s+(OR\s+REPLACE\s+)?PACKAGE\s+BODY\b",
        "cost": Ora2PgCostLevel.D,
        "pg_equivalent": "Multiple functions in schema",
        "strategy": "Split package into individual functions, manage state via schema variables or tables",
        "category": "plsql"
    },
    "package_spec": {
        "pattern": r"\bCREATE\s+(OR\s+REPLACE\s+)?PACKAGE\b(?!\s+BODY)",
        "cost": Ora2PgCostLevel.C,
        "pg_equivalent": "Schema with function signatures",
        "strategy": "Create schema, define functions without body",
        "category": "plsql"
    },
    "autonomous_transaction": {
        "pattern": r"PRAGMA\s+AUTONOMOUS_TRANSACTION",
        "cost": Ora2PgCostLevel.D,
        "pg_equivalent": "dblink or separate connection",
        "strategy": "Use dblink to self or restructure to avoid autonomous transactions",
        "category": "plsql"
    },
    "bulk_collect": {
        "pattern": r"\bBULK\s+COLLECT\b|\bFORALL\b",
        "cost": Ora2PgCostLevel.C,
        "pg_equivalent": "Array operations or COPY",
        "strategy": "Use ARRAY_AGG, UNNEST, or COPY for bulk operations",
        "category": "plsql"
    },
    "connect_by": {
        "pattern": r"\bCONNECT\s+BY\b|\bSTART\s+WITH\b",
        "cost": Ora2PgCostLevel.C,
        "pg_equivalent": "WITH RECURSIVE",
        "strategy": "Convert hierarchical queries to recursive CTEs",
        "category": "syntax"
    },
    "decode_function": {
        "pattern": r"\bDECODE\s*\(",
        "cost": Ora2PgCostLevel.B,
        "pg_equivalent": "CASE WHEN",
        "strategy": "Replace DECODE with CASE WHEN expressions",
        "category": "function"
    },
    "nvl_function": {
        "pattern": r"\bNVL\s*\(",
        "cost": Ora2PgCostLevel.A,
        "pg_equivalent": "COALESCE",
        "strategy": "Direct replacement with COALESCE",
        "category": "function"
    },
    "nvl2_function": {
        "pattern": r"\bNVL2\s*\(",
        "cost": Ora2PgCostLevel.B,
        "pg_equivalent": "CASE WHEN x IS NOT NULL",
        "strategy": "Replace with CASE WHEN expression",
        "category": "function"
    },
    "sysdate": {
        "pattern": r"\bSYSDATE\b",
        "cost": Ora2PgCostLevel.A,
        "pg_equivalent": "CURRENT_TIMESTAMP or NOW()",
        "strategy": "Direct replacement",
        "category": "function"
    },
    "systimestamp": {
        "pattern": r"\bSYSTIMESTAMP\b",
        "cost": Ora2PgCostLevel.A,
        "pg_equivalent": "CURRENT_TIMESTAMP",
        "strategy": "Direct replacement",
        "category": "function"
    },
    "rownum": {
        "pattern": r"\bROWNUM\b",
        "cost": Ora2PgCostLevel.B,
        "pg_equivalent": "ROW_NUMBER() OVER() or LIMIT",
        "strategy": "Use window function or LIMIT/OFFSET",
        "category": "syntax"
    },
    "rowid": {
        "pattern": r"\bROWID\b",
        "cost": Ora2PgCostLevel.C,
        "pg_equivalent": "ctid (with caveats)",
        "strategy": "Use ctid cautiously or add surrogate key",
        "category": "syntax"
    },
    "dual_table": {
        "pattern": r"\bFROM\s+DUAL\b",
        "cost": Ora2PgCostLevel.A,
        "pg_equivalent": "Omit FROM clause or use VALUES",
        "strategy": "Remove FROM DUAL, PostgreSQL allows SELECT without FROM",
        "category": "syntax"
    },
    "sequence_nextval": {
        "pattern": r"\w+\.NEXTVAL|\w+\.CURRVAL",
        "cost": Ora2PgCostLevel.B,
        "pg_equivalent": "nextval('seq_name'), currval('seq_name')",
        "strategy": "Use function syntax for sequences",
        "category": "syntax"
    },
    "varchar2": {
        "pattern": r"\bVARCHAR2\s*\(",
        "cost": Ora2PgCostLevel.A,
        "pg_equivalent": "VARCHAR",
        "strategy": "Direct replacement, note BYTE vs CHAR semantics",
        "category": "datatype"
    },
    "number_type": {
        "pattern": r"\bNUMBER\s*\(|\bNUMBER\b(?!\s*\()",
        "cost": Ora2PgCostLevel.B,
        "pg_equivalent": "NUMERIC or specific integer types",
        "strategy": "Map to appropriate NUMERIC, INTEGER, BIGINT based on precision",
        "category": "datatype"
    },
    "clob_blob": {
        "pattern": r"\bCLOB\b|\bBLOB\b|\bNCLOB\b",
        "cost": Ora2PgCostLevel.B,
        "pg_equivalent": "TEXT or BYTEA",
        "strategy": "CLOB->TEXT, BLOB->BYTEA, check size limits",
        "category": "datatype"
    },
    "ref_cursor": {
        "pattern": r"\bREF\s+CURSOR\b|\bSYS_REFCURSOR\b",
        "cost": Ora2PgCostLevel.C,
        "pg_equivalent": "REFCURSOR",
        "strategy": "Use PostgreSQL REFCURSOR, adjust fetch logic",
        "category": "plsql"
    },
    "dbms_output": {
        "pattern": r"\bDBMS_OUTPUT\.",
        "cost": Ora2PgCostLevel.B,
        "pg_equivalent": "RAISE NOTICE",
        "strategy": "Replace with RAISE NOTICE for debugging output",
        "category": "plsql"
    },
    "dbms_sql": {
        "pattern": r"\bDBMS_SQL\.",
        "cost": Ora2PgCostLevel.D,
        "pg_equivalent": "EXECUTE or plpgsql dynamic SQL",
        "strategy": "Rewrite using EXECUTE with format() for safety",
        "category": "plsql"
    },
    "utl_file": {
        "pattern": r"\bUTL_FILE\.",
        "cost": Ora2PgCostLevel.D,
        "pg_equivalent": "pg_read_file, COPY, external scripts",
        "strategy": "Use server-side functions or move file I/O to application layer",
        "category": "plsql"
    },
    "pipelined": {
        "pattern": r"\bPIPELINED\b",
        "cost": Ora2PgCostLevel.C,
        "pg_equivalent": "RETURNS SETOF or TABLE function",
        "strategy": "Use RETURNS SETOF with RETURN NEXT",
        "category": "plsql"
    },
    "table_function": {
        "pattern": r"\bTABLE\s*\(\s*\w+\s*\(",
        "cost": Ora2PgCostLevel.C,
        "pg_equivalent": "UNNEST or TABLE function",
        "strategy": "Use UNNEST for arrays, TABLE function for sets",
        "category": "plsql"
    },
    "type_object": {
        "pattern": r"\bCREATE\s+(OR\s+REPLACE\s+)?TYPE\b.*\bAS\s+OBJECT\b",
        "cost": Ora2PgCostLevel.D,
        "pg_equivalent": "Composite type or table",
        "strategy": "Create composite type, but methods need separate functions",
        "category": "plsql"
    }
}

# Cost level to hours multiplier
COST_HOURS_MULTIPLIER = {
    Ora2PgCostLevel.A: 0.5,
    Ora2PgCostLevel.B: 2.0,
    Ora2PgCostLevel.C: 8.0,
    Ora2PgCostLevel.D: 24.0,
    Ora2PgCostLevel.E: 80.0,
}


class Ora2PgWrapperService:
    """
    Wrapper service for ora2pg Oracle to PostgreSQL migration tool.

    Provides both direct ora2pg integration (if installed) and
    fallback pattern-based analysis for environments without ora2pg.
    """

    def __init__(self):
        self.ora2pg_path = self._find_ora2pg()
        self.tool_available = self.ora2pg_path is not None
        self.tool_version = self._get_version() if self.tool_available else None

    def _find_ora2pg(self) -> Optional[str]:
        """Find ora2pg executable in system PATH"""
        ora2pg_path = shutil.which("ora2pg")
        if ora2pg_path:
            logger.info(f"Found ora2pg at: {ora2pg_path}")
            return ora2pg_path

        # Check common installation paths
        common_paths = [
            "/usr/local/bin/ora2pg",
            "/usr/bin/ora2pg",
            "/opt/ora2pg/ora2pg",
        ]
        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                logger.info(f"Found ora2pg at: {path}")
                return path

        logger.warning("ora2pg not found, will use pattern-based analysis")
        return None

    def _get_version(self) -> Optional[str]:
        """Get ora2pg version"""
        if not self.ora2pg_path:
            return None

        try:
            result = subprocess.run(
                [self.ora2pg_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Parse version from output like "Ora2Pg v24.1"
            match = re.search(r"v?(\d+\.\d+(?:\.\d+)?)", result.stdout)
            if match:
                return match.group(1)
        except Exception as e:
            logger.error(f"Failed to get ora2pg version: {e}")

        return None

    async def analyze_directory(
        self,
        directory: Path,
        file_extensions: List[str] = None
    ) -> Ora2PgAnalysisResult:
        """
        Analyze Oracle SQL/PL-SQL files in directory.
        Uses ora2pg if available, otherwise falls back to pattern analysis.
        """
        if file_extensions is None:
            file_extensions = [".sql", ".pls", ".plb", ".pks", ".pkb", ".prc", ".fnc", ".trg", ".vw"]

        result = Ora2PgAnalysisResult(
            tool_available=self.tool_available,
            tool_version=self.tool_version
        )

        # Collect all SQL files
        sql_files = []
        for ext in file_extensions:
            sql_files.extend(directory.rglob(f"*{ext}"))

        if not sql_files:
            logger.warning(f"No SQL files found in {directory}")
            result.recommendations.append("No Oracle SQL files found to analyze")
            return result

        # Analyze patterns
        await self._analyze_patterns(sql_files, result)

        # Calculate costs
        self._calculate_costs(result)

        # Generate recommendations
        self._generate_recommendations(result)

        return result

    async def analyze_files(
        self,
        files: List[Path]
    ) -> Ora2PgAnalysisResult:
        """Analyze specific Oracle SQL files"""
        result = Ora2PgAnalysisResult(
            tool_available=self.tool_available,
            tool_version=self.tool_version
        )

        if not files:
            return result

        await self._analyze_patterns(files, result)
        self._calculate_costs(result)
        self._generate_recommendations(result)

        return result

    async def _analyze_patterns(
        self,
        files: List[Path],
        result: Ora2PgAnalysisResult
    ) -> None:
        """Analyze files for Oracle-specific patterns"""

        pattern_counts: Dict[str, Ora2PgPatternIssue] = {}
        object_counts: Dict[str, int] = defaultdict(int)
        total_loc = 0

        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                total_loc += len(lines)

                # Detect object types
                self._detect_objects(content, object_counts, file_path)

                # Check for conversion patterns
                for pattern_name, pattern_info in ORACLE_CONVERSION_PATTERNS.items():
                    matches = re.findall(pattern_info["pattern"], content, re.IGNORECASE)
                    if matches:
                        if pattern_name not in pattern_counts:
                            pattern_counts[pattern_name] = Ora2PgPatternIssue(
                                pattern_name=pattern_name,
                                category=pattern_info["category"],
                                cost_level=pattern_info["cost"],
                                conversion_strategy=pattern_info["strategy"],
                                pg_equivalent=pattern_info["pg_equivalent"]
                            )
                        pattern_counts[pattern_name].occurrences += len(matches)
                        if str(file_path) not in pattern_counts[pattern_name].files:
                            pattern_counts[pattern_name].files.append(str(file_path))

            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")

        result.total_loc = total_loc
        result.pattern_issues = list(pattern_counts.values())

        # Create object stats
        for obj_type, count in object_counts.items():
            result.object_stats[obj_type] = Ora2PgObjectStats(
                object_type=obj_type,
                count=count
            )

        result.total_objects = sum(object_counts.values())

    def _detect_objects(
        self,
        content: str,
        object_counts: Dict[str, int],
        file_path: Path
    ) -> None:
        """Detect Oracle database objects in content"""

        object_patterns = {
            "TABLE": r"\bCREATE\s+TABLE\b",
            "VIEW": r"\bCREATE\s+(OR\s+REPLACE\s+)?(MATERIALIZED\s+)?VIEW\b",
            "INDEX": r"\bCREATE\s+(UNIQUE\s+)?INDEX\b",
            "SEQUENCE": r"\bCREATE\s+SEQUENCE\b",
            "PACKAGE": r"\bCREATE\s+(OR\s+REPLACE\s+)?PACKAGE\b(?!\s+BODY)",
            "PACKAGE_BODY": r"\bCREATE\s+(OR\s+REPLACE\s+)?PACKAGE\s+BODY\b",
            "PROCEDURE": r"\bCREATE\s+(OR\s+REPLACE\s+)?PROCEDURE\b",
            "FUNCTION": r"\bCREATE\s+(OR\s+REPLACE\s+)?FUNCTION\b",
            "TRIGGER": r"\bCREATE\s+(OR\s+REPLACE\s+)?TRIGGER\b",
            "TYPE": r"\bCREATE\s+(OR\s+REPLACE\s+)?TYPE\b",
            "SYNONYM": r"\bCREATE\s+(OR\s+REPLACE\s+)?(PUBLIC\s+)?SYNONYM\b",
        }

        for obj_type, pattern in object_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            object_counts[obj_type] += len(matches)

    def _calculate_costs(self, result: Ora2PgAnalysisResult) -> None:
        """Calculate migration cost estimates"""

        total_hours = 0.0
        cost_breakdown = defaultdict(float)
        max_cost_level = Ora2PgCostLevel.A

        # Calculate hours from pattern issues
        for issue in result.pattern_issues:
            hours = issue.occurrences * COST_HOURS_MULTIPLIER[issue.cost_level]
            total_hours += hours
            cost_breakdown[issue.category] += hours

            if issue.cost_level.value > max_cost_level.value:
                max_cost_level = issue.cost_level

        # Add base hours for object types
        object_base_hours = {
            "TABLE": 1.0,
            "VIEW": 2.0,
            "INDEX": 0.5,
            "SEQUENCE": 0.25,
            "PACKAGE": 8.0,
            "PACKAGE_BODY": 16.0,
            "PROCEDURE": 4.0,
            "FUNCTION": 3.0,
            "TRIGGER": 4.0,
            "TYPE": 6.0,
            "SYNONYM": 0.25,
        }

        for obj_type, stats in result.object_stats.items():
            base_hours = object_base_hours.get(obj_type, 2.0)
            hours = stats.count * base_hours
            total_hours += hours
            cost_breakdown["objects"] += hours
            stats.estimated_hours = hours

            # Assign cost levels based on object type
            if obj_type in ["PACKAGE", "PACKAGE_BODY", "TYPE"]:
                stats.cost_level = Ora2PgCostLevel.D
            elif obj_type in ["PROCEDURE", "FUNCTION", "TRIGGER"]:
                stats.cost_level = Ora2PgCostLevel.C
            else:
                stats.cost_level = Ora2PgCostLevel.B

        result.total_estimated_hours = total_hours
        result.estimated_cost_breakdown = dict(cost_breakdown)
        result.overall_cost_level = max_cost_level

        # Calculate ora2pg compatibility score (0-100)
        if result.total_objects > 0:
            simple_objects = sum(
                stats.count for obj_type, stats in result.object_stats.items()
                if obj_type in ["TABLE", "VIEW", "INDEX", "SEQUENCE", "SYNONYM"]
            )
            complex_objects = result.total_objects - simple_objects
            result.ora2pg_compatibility = (
                (simple_objects * 0.9 + complex_objects * 0.5) / result.total_objects * 100
            )

    def _generate_recommendations(self, result: Ora2PgAnalysisResult) -> None:
        """Generate migration recommendations"""

        # Check for blockers
        for issue in result.pattern_issues:
            if issue.cost_level == Ora2PgCostLevel.E:
                result.blockers.append(
                    f"Critical: {issue.pattern_name} found {issue.occurrences} times - "
                    f"requires complete redesign"
                )

        # High-priority recommendations
        package_count = result.object_stats.get("PACKAGE", Ora2PgObjectStats("PACKAGE")).count
        package_body_count = result.object_stats.get("PACKAGE_BODY", Ora2PgObjectStats("PACKAGE_BODY")).count

        if package_count > 0 or package_body_count > 0:
            result.recommendations.append(
                f"Found {package_count + package_body_count} Oracle packages. "
                "Consider restructuring into PostgreSQL schemas with individual functions."
            )

        # Check for autonomous transactions
        for issue in result.pattern_issues:
            if issue.pattern_name == "autonomous_transaction" and issue.occurrences > 0:
                result.recommendations.append(
                    f"Found {issue.occurrences} AUTONOMOUS_TRANSACTION usages. "
                    "Consider using dblink to self or restructuring transaction logic."
                )

        # Check for CONNECT BY
        for issue in result.pattern_issues:
            if issue.pattern_name == "connect_by" and issue.occurrences > 0:
                result.recommendations.append(
                    f"Found {issue.occurrences} hierarchical queries (CONNECT BY). "
                    "Convert to PostgreSQL WITH RECURSIVE CTEs."
                )

        # General recommendations based on complexity
        if result.overall_cost_level in [Ora2PgCostLevel.D, Ora2PgCostLevel.E]:
            result.recommendations.append(
                "High complexity migration detected. Consider phased approach: "
                "1) Schema objects, 2) Simple PL/SQL, 3) Complex packages, 4) Data migration"
            )

        if result.total_estimated_hours > 100:
            result.recommendations.append(
                f"Estimated {result.total_estimated_hours:.0f} hours of conversion work. "
                "Consider using ora2pg for automated conversion of simple objects."
            )

        # Tool recommendation
        if not result.tool_available:
            result.recommendations.append(
                "Install ora2pg for more accurate analysis and automated schema conversion: "
                "https://ora2pg.darold.net/"
            )

    def get_status(self) -> Dict[str, Any]:
        """Get wrapper status"""
        return {
            "tool_name": "ora2pg",
            "tool_available": self.tool_available,
            "tool_version": self.tool_version,
            "tool_path": self.ora2pg_path,
            "supported_source": "Oracle",
            "supported_target": "PostgreSQL",
            "fallback_available": True,
            "pattern_count": len(ORACLE_CONVERSION_PATTERNS)
        }

    def to_dict(self, result: Ora2PgAnalysisResult) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "tool_available": result.tool_available,
            "tool_version": result.tool_version,
            "schemas_analyzed": result.schemas_analyzed,
            "total_objects": result.total_objects,
            "total_loc": result.total_loc,
            "object_stats": {
                k: {
                    "object_type": v.object_type,
                    "count": v.count,
                    "cost_level": v.cost_level.value,
                    "estimated_hours": v.estimated_hours,
                    "notes": v.notes
                }
                for k, v in result.object_stats.items()
            },
            "pattern_issues": [
                {
                    "pattern_name": p.pattern_name,
                    "category": p.category,
                    "occurrences": p.occurrences,
                    "files_count": len(p.files),
                    "cost_level": p.cost_level.value,
                    "conversion_strategy": p.conversion_strategy,
                    "pg_equivalent": p.pg_equivalent
                }
                for p in result.pattern_issues
            ],
            "overall_cost_level": result.overall_cost_level.value,
            "total_estimated_hours": result.total_estimated_hours,
            "estimated_cost_breakdown": result.estimated_cost_breakdown,
            "ora2pg_compatibility": result.ora2pg_compatibility,
            "recommendations": result.recommendations,
            "blockers": result.blockers
        }
