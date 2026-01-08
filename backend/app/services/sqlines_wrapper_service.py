"""
SQLines Wrapper Service - Multi-Database Conversion Assessment

Week 67 Day 9: Wrapper for SQLines migration tool
SQLines supports heterogeneous database migrations between:
- Oracle, SQL Server, MySQL, PostgreSQL, DB2, Sybase, Informix, Teradata

Provides:
- Tool detection and version info
- Multi-database pattern analysis
- Conversion path assessment
- Effort estimation per source/target combination
"""

import os
import re
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from datetime import datetime


class DatabasePlatform(Enum):
    """Supported database platforms"""
    ORACLE = "oracle"
    SQL_SERVER = "sqlserver"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    DB2 = "db2"
    SYBASE = "sybase"
    INFORMIX = "informix"
    TERADATA = "teradata"
    MARIADB = "mariadb"
    UNKNOWN = "unknown"


class ConversionComplexity(Enum):
    """Conversion complexity levels"""
    TRIVIAL = "trivial"      # Direct syntax mapping
    SIMPLE = "simple"        # Minor adjustments needed
    MODERATE = "moderate"    # Significant changes required
    COMPLEX = "complex"      # Major rewrites needed
    UNSUPPORTED = "unsupported"  # No direct conversion path


@dataclass
class ConversionRule:
    """Single conversion rule definition"""
    source_pattern: str
    target_pattern: str
    complexity: ConversionComplexity
    description: str
    example_source: str = ""
    example_target: str = ""


@dataclass
class PatternDetection:
    """Detected pattern in source code"""
    pattern_name: str
    source_platform: DatabasePlatform
    occurrences: int
    complexity: ConversionComplexity
    line_numbers: List[int] = field(default_factory=list)
    sample_code: str = ""
    conversion_notes: str = ""


@dataclass
class ConversionPathAssessment:
    """Assessment for a specific source→target conversion"""
    source_platform: DatabasePlatform
    target_platform: DatabasePlatform
    total_patterns: int
    trivial_count: int
    simple_count: int
    moderate_count: int
    complex_count: int
    unsupported_count: int
    estimated_hours: float
    confidence: float  # 0.0 - 1.0
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class SQLinesAnalysisResult:
    """Complete SQLines analysis result"""
    tool_available: bool
    tool_version: Optional[str]
    source_platform: DatabasePlatform
    detected_platforms: List[DatabasePlatform]
    files_analyzed: int
    total_lines: int
    patterns_detected: List[PatternDetection]
    conversion_paths: List[ConversionPathAssessment]
    recommendations: List[str]
    analysis_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_available": self.tool_available,
            "tool_version": self.tool_version,
            "source_platform": self.source_platform.value,
            "detected_platforms": [p.value for p in self.detected_platforms],
            "files_analyzed": self.files_analyzed,
            "total_lines": self.total_lines,
            "patterns_detected": [
                {
                    "pattern_name": p.pattern_name,
                    "source_platform": p.source_platform.value,
                    "occurrences": p.occurrences,
                    "complexity": p.complexity.value,
                    "line_numbers": p.line_numbers[:10],  # Limit for response size
                    "sample_code": p.sample_code[:200] if p.sample_code else "",
                    "conversion_notes": p.conversion_notes
                }
                for p in self.patterns_detected
            ],
            "conversion_paths": [
                {
                    "source": cp.source_platform.value,
                    "target": cp.target_platform.value,
                    "total_patterns": cp.total_patterns,
                    "complexity_breakdown": {
                        "trivial": cp.trivial_count,
                        "simple": cp.simple_count,
                        "moderate": cp.moderate_count,
                        "complex": cp.complex_count,
                        "unsupported": cp.unsupported_count
                    },
                    "estimated_hours": cp.estimated_hours,
                    "confidence": cp.confidence,
                    "blockers": cp.blockers,
                    "warnings": cp.warnings
                }
                for cp in self.conversion_paths
            ],
            "recommendations": self.recommendations,
            "analysis_timestamp": self.analysis_timestamp
        }


# Platform-specific SQL patterns for detection
PLATFORM_DETECTION_PATTERNS: Dict[DatabasePlatform, Dict[str, str]] = {
    DatabasePlatform.ORACLE: {
        "nvl_function": r"\bNVL\s*\(",
        "decode_function": r"\bDECODE\s*\(",
        "connect_by": r"\bCONNECT\s+BY\b",
        "rownum": r"\bROWNUM\b",
        "sysdate": r"\bSYSDATE\b",
        "dual_table": r"\bFROM\s+DUAL\b",
        "sequence_nextval": r"\b\w+\.NEXTVAL\b",
        "sequence_currval": r"\b\w+\.CURRVAL\b",
        "package_body": r"\bCREATE\s+(OR\s+REPLACE\s+)?PACKAGE\s+BODY\b",
        "package_spec": r"\bCREATE\s+(OR\s+REPLACE\s+)?PACKAGE\b",
        "type_body": r"\bCREATE\s+(OR\s+REPLACE\s+)?TYPE\s+BODY\b",
        "varchar2": r"\bVARCHAR2\s*\(",
        "number_type": r"\bNUMBER\s*\(",
        "pls_integer": r"\bPLS_INTEGER\b",
        "bulk_collect": r"\bBULK\s+COLLECT\b",
        "forall_statement": r"\bFORALL\b",
        "returning_into": r"\bRETURNING\s+.*\s+INTO\b",
        "merge_statement": r"\bMERGE\s+INTO\b",
        "dbms_output": r"\bDBMS_OUTPUT\b",
        "utl_file": r"\bUTL_FILE\b",
    },
    DatabasePlatform.SQL_SERVER: {
        "top_clause": r"\bSELECT\s+TOP\s+\d+\b",
        "identity_column": r"\bIDENTITY\s*\(\s*\d+\s*,\s*\d+\s*\)",
        "getdate_function": r"\bGETDATE\s*\(\s*\)",
        "isnull_function": r"\bISNULL\s*\(",
        "charindex_function": r"\bCHARINDEX\s*\(",
        "convert_function": r"\bCONVERT\s*\(\s*\w+\s*,",
        "nvarchar_type": r"\bNVARCHAR\s*\(",
        "datetime2_type": r"\bDATETIME2\b",
        "datetimeoffset": r"\bDATETIMEOFFSET\b",
        "rowversion_type": r"\bROWVERSION\b",
        "cross_apply": r"\bCROSS\s+APPLY\b",
        "outer_apply": r"\bOUTER\s+APPLY\b",
        "with_nolock": r"\bWITH\s*\(\s*NOLOCK\s*\)",
        "set_nocount": r"\bSET\s+NOCOUNT\s+ON\b",
        "raiserror": r"\bRAISERROR\s*\(",
        "throw_statement": r"\bTHROW\b",
        "try_catch": r"\bBEGIN\s+TRY\b",
        "table_variable": r"\bDECLARE\s+@\w+\s+TABLE\b",
        "cursor_fast_forward": r"\bFAST_FORWARD\b",
        "xml_datatype": r"\bXML\b",
    },
    DatabasePlatform.MYSQL: {
        "auto_increment": r"\bAUTO_INCREMENT\b",
        "limit_clause": r"\bLIMIT\s+\d+",
        "ifnull_function": r"\bIFNULL\s*\(",
        "now_function": r"\bNOW\s*\(\s*\)",
        "concat_ws": r"\bCONCAT_WS\s*\(",
        "group_concat": r"\bGROUP_CONCAT\s*\(",
        "on_duplicate_key": r"\bON\s+DUPLICATE\s+KEY\s+UPDATE\b",
        "engine_innodb": r"\bENGINE\s*=\s*InnoDB\b",
        "engine_myisam": r"\bENGINE\s*=\s*MyISAM\b",
        "tinyint_type": r"\bTINYINT\b",
        "mediumint_type": r"\bMEDIUMINT\b",
        "unsigned_type": r"\bUNSIGNED\b",
        "zerofill_type": r"\bZEROFILL\b",
        "enum_type": r"\bENUM\s*\(",
        "set_type": r"\bSET\s*\(",
        "delimiter_statement": r"\bDELIMITER\b",
        "handler_statement": r"\bDECLARE\s+.*\s+HANDLER\b",
        "straight_join": r"\bSTRAIGHT_JOIN\b",
        "sql_calc_found_rows": r"\bSQL_CALC_FOUND_ROWS\b",
        "found_rows": r"\bFOUND_ROWS\s*\(\s*\)",
    },
    DatabasePlatform.POSTGRESQL: {
        "serial_type": r"\bSERIAL\b",
        "bigserial_type": r"\bBIGSERIAL\b",
        "returning_clause": r"\bRETURNING\s+\*",
        "array_type": r"\b\w+\[\]",
        "json_type": r"\bJSON\b",
        "jsonb_type": r"\bJSONB\b",
        "hstore_type": r"\bHSTORE\b",
        "uuid_type": r"\bUUID\b",
        "citext_type": r"\bCITEXT\b",
        "inet_type": r"\bINET\b",
        "macaddr_type": r"\bMACADDR\b",
        "tsvector_type": r"\bTSVECTOR\b",
        "coalesce_function": r"\bCOALESCE\s*\(",
        "generate_series": r"\bGENERATE_SERIES\s*\(",
        "string_agg": r"\bSTRING_AGG\s*\(",
        "array_agg": r"\bARRAY_AGG\s*\(",
        "window_function": r"\bOVER\s*\(\s*PARTITION\s+BY\b",
        "cte_recursive": r"\bWITH\s+RECURSIVE\b",
        "create_extension": r"\bCREATE\s+EXTENSION\b",
        "dollar_quoting": r"\$\w*\$",
    },
    DatabasePlatform.DB2: {
        "values_clause": r"\bVALUES\s+\d+\b",
        "fetch_first": r"\bFETCH\s+FIRST\s+\d+\s+ROWS\s+ONLY\b",
        "with_ur": r"\bWITH\s+UR\b",
        "with_cs": r"\bWITH\s+CS\b",
        "with_rs": r"\bWITH\s+RS\b",
        "db2_timestamp": r"\bCURRENT\s+TIMESTAMP\b",
        "db2_date": r"\bCURRENT\s+DATE\b",
        "db2_time": r"\bCURRENT\s+TIME\b",
        "db2_user": r"\bCURRENT\s+USER\b",
        "db2_schema": r"\bCURRENT\s+SCHEMA\b",
        "graphic_type": r"\bGRAPHIC\b",
        "vargraphic_type": r"\bVARGRAPHIC\b",
        "decfloat_type": r"\bDECFLOAT\b",
        "organize_by": r"\bORGANIZE\s+BY\b",
        "partition_by": r"\bPARTITION\s+BY\s+RANGE\b",
    },
    DatabasePlatform.SYBASE: {
        "sybase_identity": r"\bIDENTITY\b",
        "sybase_getdate": r"\bGETDATE\s*\(\s*\)",
        "sybase_convert": r"\bCONVERT\s*\(",
        "sybase_money": r"\bMONEY\b",
        "sybase_smallmoney": r"\bSMALLMONEY\b",
        "sybase_image": r"\bIMAGE\b",
        "sybase_text": r"\bTEXT\b",
        "compute_clause": r"\bCOMPUTE\b",
        "sybase_cursor": r"\bDECLARE\s+\w+\s+CURSOR\b",
    },
}

# Conversion complexity by pattern and target
CONVERSION_COMPLEXITY: Dict[str, Dict[DatabasePlatform, ConversionComplexity]] = {
    # Oracle patterns
    "nvl_function": {
        DatabasePlatform.POSTGRESQL: ConversionComplexity.TRIVIAL,  # COALESCE
        DatabasePlatform.SQL_SERVER: ConversionComplexity.TRIVIAL,  # ISNULL
        DatabasePlatform.MYSQL: ConversionComplexity.TRIVIAL,  # IFNULL
    },
    "decode_function": {
        DatabasePlatform.POSTGRESQL: ConversionComplexity.SIMPLE,  # CASE WHEN
        DatabasePlatform.SQL_SERVER: ConversionComplexity.SIMPLE,  # CASE WHEN
        DatabasePlatform.MYSQL: ConversionComplexity.SIMPLE,  # CASE WHEN
    },
    "connect_by": {
        DatabasePlatform.POSTGRESQL: ConversionComplexity.COMPLEX,  # WITH RECURSIVE
        DatabasePlatform.SQL_SERVER: ConversionComplexity.COMPLEX,  # WITH RECURSIVE CTE
        DatabasePlatform.MYSQL: ConversionComplexity.COMPLEX,  # WITH RECURSIVE (8.0+)
    },
    "rownum": {
        DatabasePlatform.POSTGRESQL: ConversionComplexity.MODERATE,  # ROW_NUMBER() or LIMIT
        DatabasePlatform.SQL_SERVER: ConversionComplexity.MODERATE,  # ROW_NUMBER() or TOP
        DatabasePlatform.MYSQL: ConversionComplexity.SIMPLE,  # LIMIT
    },
    "package_body": {
        DatabasePlatform.POSTGRESQL: ConversionComplexity.COMPLEX,  # Schema + functions
        DatabasePlatform.SQL_SERVER: ConversionComplexity.COMPLEX,  # Schema + procedures
        DatabasePlatform.MYSQL: ConversionComplexity.UNSUPPORTED,  # No direct equivalent
    },
    "bulk_collect": {
        DatabasePlatform.POSTGRESQL: ConversionComplexity.MODERATE,  # ARRAY aggregation
        DatabasePlatform.SQL_SERVER: ConversionComplexity.COMPLEX,  # Table variables
        DatabasePlatform.MYSQL: ConversionComplexity.UNSUPPORTED,  # No equivalent
    },
    # SQL Server patterns
    "top_clause": {
        DatabasePlatform.POSTGRESQL: ConversionComplexity.TRIVIAL,  # LIMIT
        DatabasePlatform.ORACLE: ConversionComplexity.SIMPLE,  # ROWNUM or FETCH FIRST
        DatabasePlatform.MYSQL: ConversionComplexity.TRIVIAL,  # LIMIT
    },
    "cross_apply": {
        DatabasePlatform.POSTGRESQL: ConversionComplexity.MODERATE,  # LATERAL JOIN
        DatabasePlatform.ORACLE: ConversionComplexity.MODERATE,  # LATERAL or TABLE()
        DatabasePlatform.MYSQL: ConversionComplexity.COMPLEX,  # Subqueries
    },
    "table_variable": {
        DatabasePlatform.POSTGRESQL: ConversionComplexity.SIMPLE,  # Temp tables
        DatabasePlatform.ORACLE: ConversionComplexity.MODERATE,  # Collections
        DatabasePlatform.MYSQL: ConversionComplexity.SIMPLE,  # Temp tables
    },
    # MySQL patterns
    "auto_increment": {
        DatabasePlatform.POSTGRESQL: ConversionComplexity.TRIVIAL,  # SERIAL
        DatabasePlatform.ORACLE: ConversionComplexity.SIMPLE,  # SEQUENCE + TRIGGER
        DatabasePlatform.SQL_SERVER: ConversionComplexity.TRIVIAL,  # IDENTITY
    },
    "on_duplicate_key": {
        DatabasePlatform.POSTGRESQL: ConversionComplexity.SIMPLE,  # ON CONFLICT
        DatabasePlatform.ORACLE: ConversionComplexity.MODERATE,  # MERGE
        DatabasePlatform.SQL_SERVER: ConversionComplexity.MODERATE,  # MERGE
    },
    "group_concat": {
        DatabasePlatform.POSTGRESQL: ConversionComplexity.TRIVIAL,  # STRING_AGG
        DatabasePlatform.ORACLE: ConversionComplexity.SIMPLE,  # LISTAGG
        DatabasePlatform.SQL_SERVER: ConversionComplexity.MODERATE,  # STRING_AGG (2017+)
    },
}

# Hours multiplier by complexity
COMPLEXITY_HOURS: Dict[ConversionComplexity, float] = {
    ConversionComplexity.TRIVIAL: 0.1,
    ConversionComplexity.SIMPLE: 0.5,
    ConversionComplexity.MODERATE: 2.0,
    ConversionComplexity.COMPLEX: 8.0,
    ConversionComplexity.UNSUPPORTED: 24.0,  # Manual rewrite needed
}


class SQLinesWrapperService:
    """Service for SQLines multi-database migration assessment"""

    def __init__(self):
        self.sqlines_path = self._find_sqlines()
        self.version = self._get_version() if self.sqlines_path else None

    def _find_sqlines(self) -> Optional[str]:
        """Find sqlines executable"""
        # Check common locations
        locations = [
            shutil.which("sqlines"),
            "/usr/local/bin/sqlines",
            "/opt/sqlines/sqlines",
            os.path.expanduser("~/sqlines/sqlines"),
        ]

        for loc in locations:
            if loc and os.path.isfile(loc) and os.access(loc, os.X_OK):
                return loc

        return None

    def _get_version(self) -> Optional[str]:
        """Get sqlines version"""
        if not self.sqlines_path:
            return None

        try:
            result = subprocess.run(
                [self.sqlines_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Parse version from output
            version_match = re.search(r"(\d+\.\d+\.?\d*)", result.stdout + result.stderr)
            return version_match.group(1) if version_match else "unknown"
        except Exception:
            return None

    def analyze_directory(
        self,
        directory: str,
        source_platform: Optional[DatabasePlatform] = None,
        target_platforms: Optional[List[DatabasePlatform]] = None,
        file_extensions: Optional[List[str]] = None
    ) -> SQLinesAnalysisResult:
        """
        Analyze directory for multi-database conversion assessment

        Args:
            directory: Path to source code directory
            source_platform: Known source platform (auto-detected if None)
            target_platforms: Target platforms to assess (all if None)
            file_extensions: File extensions to scan (default: .sql, .prc, .pkg, etc.)

        Returns:
            SQLinesAnalysisResult with conversion assessments
        """
        if file_extensions is None:
            file_extensions = [
                ".sql", ".prc", ".pkg", ".pkb", ".pks", ".fnc", ".trg",
                ".vw", ".viw", ".ddl", ".dml", ".plsql", ".tsql"
            ]

        # Collect all files
        files_content: Dict[str, str] = {}
        total_lines = 0

        path = Path(directory)
        if not path.exists():
            return SQLinesAnalysisResult(
                tool_available=self.sqlines_path is not None,
                tool_version=self.version,
                source_platform=source_platform or DatabasePlatform.UNKNOWN,
                detected_platforms=[],
                files_analyzed=0,
                total_lines=0,
                patterns_detected=[],
                conversion_paths=[],
                recommendations=["Directory does not exist"]
            )

        for ext in file_extensions:
            for file_path in path.rglob(f"*{ext}"):
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    files_content[str(file_path)] = content
                    total_lines += len(content.splitlines())
                except Exception:
                    continue

        if not files_content:
            return SQLinesAnalysisResult(
                tool_available=self.sqlines_path is not None,
                tool_version=self.version,
                source_platform=source_platform or DatabasePlatform.UNKNOWN,
                detected_platforms=[],
                files_analyzed=0,
                total_lines=0,
                patterns_detected=[],
                conversion_paths=[],
                recommendations=["No SQL files found in directory"]
            )

        # Detect patterns
        patterns_detected = self._detect_patterns(files_content)

        # Auto-detect source platform if not specified
        if source_platform is None:
            source_platform = self._detect_source_platform(patterns_detected)

        # Get unique detected platforms
        detected_platforms = list(set(p.source_platform for p in patterns_detected))

        # Define target platforms if not specified
        if target_platforms is None:
            target_platforms = [
                DatabasePlatform.POSTGRESQL,
                DatabasePlatform.SQL_SERVER,
                DatabasePlatform.MYSQL,
            ]
            # Don't include source in targets
            target_platforms = [t for t in target_platforms if t != source_platform]

        # Assess conversion paths
        conversion_paths = self._assess_conversion_paths(
            source_platform, target_platforms, patterns_detected
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            source_platform, conversion_paths, patterns_detected
        )

        return SQLinesAnalysisResult(
            tool_available=self.sqlines_path is not None,
            tool_version=self.version,
            source_platform=source_platform,
            detected_platforms=detected_platforms,
            files_analyzed=len(files_content),
            total_lines=total_lines,
            patterns_detected=patterns_detected,
            conversion_paths=conversion_paths,
            recommendations=recommendations
        )

    def _detect_patterns(
        self, files_content: Dict[str, str]
    ) -> List[PatternDetection]:
        """Detect platform-specific patterns in files"""
        patterns_found: Dict[Tuple[str, DatabasePlatform], PatternDetection] = {}

        for file_path, content in files_content.items():
            lines = content.splitlines()

            for platform, patterns in PLATFORM_DETECTION_PATTERNS.items():
                for pattern_name, regex in patterns.items():
                    try:
                        for i, line in enumerate(lines, 1):
                            if re.search(regex, line, re.IGNORECASE):
                                key = (pattern_name, platform)

                                if key not in patterns_found:
                                    # Determine complexity (use PostgreSQL as default target)
                                    complexity = CONVERSION_COMPLEXITY.get(
                                        pattern_name, {}
                                    ).get(DatabasePlatform.POSTGRESQL, ConversionComplexity.MODERATE)

                                    patterns_found[key] = PatternDetection(
                                        pattern_name=pattern_name,
                                        source_platform=platform,
                                        occurrences=0,
                                        complexity=complexity,
                                        line_numbers=[],
                                        sample_code="",
                                        conversion_notes=self._get_conversion_note(
                                            pattern_name, platform
                                        )
                                    )

                                patterns_found[key].occurrences += 1
                                patterns_found[key].line_numbers.append(i)

                                if not patterns_found[key].sample_code:
                                    patterns_found[key].sample_code = line.strip()
                    except re.error:
                        continue

        return list(patterns_found.values())

    def _detect_source_platform(
        self, patterns: List[PatternDetection]
    ) -> DatabasePlatform:
        """Auto-detect source platform based on pattern frequency"""
        platform_scores: Dict[DatabasePlatform, int] = {}

        for pattern in patterns:
            platform = pattern.source_platform
            platform_scores[platform] = platform_scores.get(platform, 0) + pattern.occurrences

        if not platform_scores:
            return DatabasePlatform.UNKNOWN

        return max(platform_scores.items(), key=lambda x: x[1])[0]

    def _assess_conversion_paths(
        self,
        source_platform: DatabasePlatform,
        target_platforms: List[DatabasePlatform],
        patterns: List[PatternDetection]
    ) -> List[ConversionPathAssessment]:
        """Assess conversion complexity for each target platform"""
        assessments = []

        # Filter patterns for source platform
        source_patterns = [p for p in patterns if p.source_platform == source_platform]

        for target in target_platforms:
            trivial_count = 0
            simple_count = 0
            moderate_count = 0
            complex_count = 0
            unsupported_count = 0
            total_hours = 0.0
            blockers = []
            warnings = []

            for pattern in source_patterns:
                # Get complexity for this target
                complexity = CONVERSION_COMPLEXITY.get(
                    pattern.pattern_name, {}
                ).get(target, ConversionComplexity.MODERATE)

                # Count by complexity
                if complexity == ConversionComplexity.TRIVIAL:
                    trivial_count += pattern.occurrences
                elif complexity == ConversionComplexity.SIMPLE:
                    simple_count += pattern.occurrences
                elif complexity == ConversionComplexity.MODERATE:
                    moderate_count += pattern.occurrences
                elif complexity == ConversionComplexity.COMPLEX:
                    complex_count += pattern.occurrences
                else:  # UNSUPPORTED
                    unsupported_count += pattern.occurrences
                    blockers.append(
                        f"{pattern.pattern_name}: No direct conversion to {target.value}"
                    )

                # Calculate hours
                total_hours += COMPLEXITY_HOURS[complexity] * pattern.occurrences

                # Add warnings for complex patterns
                if complexity in [ConversionComplexity.COMPLEX, ConversionComplexity.MODERATE]:
                    if pattern.occurrences > 10:
                        warnings.append(
                            f"{pattern.pattern_name}: {pattern.occurrences} occurrences "
                            f"({complexity.value} conversion)"
                        )

            total_patterns = sum([
                trivial_count, simple_count, moderate_count,
                complex_count, unsupported_count
            ])

            # Calculate confidence based on complexity distribution
            if total_patterns > 0:
                weighted_score = (
                    trivial_count * 1.0 +
                    simple_count * 0.9 +
                    moderate_count * 0.7 +
                    complex_count * 0.4 +
                    unsupported_count * 0.0
                ) / total_patterns
                confidence = min(weighted_score, 1.0)
            else:
                confidence = 1.0  # No patterns = trivial conversion

            assessments.append(ConversionPathAssessment(
                source_platform=source_platform,
                target_platform=target,
                total_patterns=total_patterns,
                trivial_count=trivial_count,
                simple_count=simple_count,
                moderate_count=moderate_count,
                complex_count=complex_count,
                unsupported_count=unsupported_count,
                estimated_hours=round(total_hours, 1),
                confidence=round(confidence, 2),
                blockers=blockers[:5],  # Limit to top 5
                warnings=warnings[:5]
            ))

        return assessments

    def _get_conversion_note(
        self, pattern_name: str, source_platform: DatabasePlatform
    ) -> str:
        """Get conversion notes for a pattern"""
        notes = {
            "nvl_function": "Use COALESCE (standard) or platform-specific null handling",
            "decode_function": "Convert to CASE WHEN expression",
            "connect_by": "Rewrite as WITH RECURSIVE CTE",
            "rownum": "Use ROW_NUMBER() window function or LIMIT/OFFSET",
            "package_body": "Split into schema with individual functions/procedures",
            "bulk_collect": "Use array aggregation or cursor-based approach",
            "top_clause": "Convert to LIMIT or FETCH FIRST",
            "cross_apply": "Convert to LATERAL JOIN",
            "auto_increment": "Use SERIAL/IDENTITY or sequence",
            "on_duplicate_key": "Use ON CONFLICT (PostgreSQL) or MERGE",
            "group_concat": "Use STRING_AGG or LISTAGG",
        }
        return notes.get(pattern_name, "Manual review recommended")

    def _generate_recommendations(
        self,
        source_platform: DatabasePlatform,
        conversion_paths: List[ConversionPathAssessment],
        patterns: List[PatternDetection]
    ) -> List[str]:
        """Generate migration recommendations"""
        recommendations = []

        # Find best target
        if conversion_paths:
            best_path = max(conversion_paths, key=lambda x: x.confidence)
            recommendations.append(
                f"Recommended target: {best_path.target_platform.value} "
                f"(confidence: {best_path.confidence:.0%}, "
                f"estimated: {best_path.estimated_hours:.0f}h)"
            )

        # Check for blockers
        total_blockers = sum(len(cp.blockers) for cp in conversion_paths)
        if total_blockers > 0:
            recommendations.append(
                f"Warning: {total_blockers} blocking patterns detected - manual rewrite needed"
            )

        # Check for complex patterns
        complex_patterns = [p for p in patterns if p.complexity == ConversionComplexity.COMPLEX]
        if complex_patterns:
            complex_names = [p.pattern_name for p in complex_patterns[:3]]
            recommendations.append(
                f"Complex patterns requiring attention: {', '.join(complex_names)}"
            )

        # SQLines tool recommendation
        if not self.sqlines_path:
            recommendations.append(
                "Install SQLines for automated conversion: https://www.sqlines.com/"
            )
        else:
            recommendations.append(
                f"SQLines {self.version} available for automated conversion assistance"
            )

        # Platform-specific recommendations
        if source_platform == DatabasePlatform.ORACLE:
            recommendations.append(
                "Consider ora2pg for comprehensive Oracle migration analysis"
            )
        elif source_platform == DatabasePlatform.SQL_SERVER:
            recommendations.append(
                "Consider SSMA (SQL Server Migration Assistant) for detailed analysis"
            )

        # Test strategy
        recommendations.append(
            "Create comprehensive test suite before migration to validate conversions"
        )

        return recommendations

    def get_supported_conversions(self) -> Dict[str, List[str]]:
        """Get list of supported conversion paths"""
        return {
            "oracle": ["postgresql", "mysql", "sqlserver", "db2", "mariadb"],
            "sqlserver": ["postgresql", "mysql", "oracle", "db2"],
            "mysql": ["postgresql", "oracle", "sqlserver"],
            "db2": ["postgresql", "oracle", "sqlserver"],
            "sybase": ["postgresql", "sqlserver"],
            "informix": ["postgresql", "mysql"],
        }

    def get_status(self) -> Dict[str, Any]:
        """Get wrapper status"""
        return {
            "tool_available": self.sqlines_path is not None,
            "tool_path": self.sqlines_path,
            "tool_version": self.version,
            "supported_platforms": [p.value for p in DatabasePlatform if p != DatabasePlatform.UNKNOWN],
            "supported_conversions": self.get_supported_conversions()
        }
