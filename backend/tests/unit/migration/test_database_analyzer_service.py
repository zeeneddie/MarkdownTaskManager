"""
Unit Tests for DatabaseAnalyzerService

Week 70: Comprehensive testing of database pattern detection and migration analysis.

Tests Cover:
- T-SQL pattern detection (SQL Server)
- PL/SQL pattern detection (Oracle)
- MySQL pattern detection
- Data type mapping recommendations
- Stored procedure complexity scoring
- Migration difficulty assessment
- Database type detection

Author: Claude Code (Week 70)
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
import tempfile
import os
import re

from app.services.database_analyzer_service import (
    DatabaseAnalyzerService,
    DatabaseAnalysisResult,
    DatabaseTable,
    StoredProcedure,
    DatabaseView,
    DatabasePatternMatch,
    DataTypeMapping,
    TSQL_PATTERNS,
    PLSQL_PATTERNS,
    MYSQL_PATTERNS,
    SQL_SERVER_TYPE_MAP,
    ORACLE_TYPE_MAP,
    MYSQL_TYPE_MAP
)


class TestDatabaseAnalyzerServiceInit:
    """Test DatabaseAnalyzerService initialization"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    def test_init_with_db_session(self, mock_db):
        """Test service initializes with database session"""
        service = DatabaseAnalyzerService(mock_db)
        assert service.db == mock_db

    def test_init_creates_empty_result(self, mock_db):
        """Test service initializes with empty result"""
        service = DatabaseAnalyzerService(mock_db)
        assert service.result is not None
        assert service.result.total_sql_files == 0
        assert service.result.source_database == "unknown"


class TestTSQLPatterns:
    """Test T-SQL pattern definitions"""

    def test_identity_column_pattern_exists(self):
        """Test IDENTITY column pattern is defined"""
        assert "identity_column" in TSQL_PATTERNS
        pattern = TSQL_PATTERNS["identity_column"]
        assert "pattern" in pattern
        assert "risk" in pattern
        assert pattern["risk"] == "low"

    def test_top_clause_pattern_exists(self):
        """Test TOP clause pattern is defined"""
        assert "top_clause" in TSQL_PATTERNS
        pattern = TSQL_PATTERNS["top_clause"]
        assert re.search(pattern["pattern"], "SELECT TOP 10 * FROM users", re.IGNORECASE)

    def test_nolock_hint_pattern_exists(self):
        """Test NOLOCK hint pattern is defined"""
        assert "nolock_hint" in TSQL_PATTERNS
        pattern = TSQL_PATTERNS["nolock_hint"]
        assert pattern["risk"] == "medium"

    def test_getdate_pattern_exists(self):
        """Test GETDATE pattern is defined"""
        assert "getdate" in TSQL_PATTERNS
        pattern = TSQL_PATTERNS["getdate"]
        assert re.search(pattern["pattern"], "SELECT GETDATE()", re.IGNORECASE)

    def test_isnull_pattern_exists(self):
        """Test ISNULL pattern is defined"""
        assert "isnull" in TSQL_PATTERNS
        pattern = TSQL_PATTERNS["isnull"]
        assert re.search(pattern["pattern"], "SELECT ISNULL(a, b)", re.IGNORECASE)

    def test_dateadd_pattern_exists(self):
        """Test DATEADD pattern is defined"""
        assert "dateadd" in TSQL_PATTERNS
        pattern = TSQL_PATTERNS["dateadd"]
        assert "pg_equivalent" in pattern

    def test_datediff_pattern_exists(self):
        """Test DATEDIFF pattern is defined"""
        assert "datediff" in TSQL_PATTERNS

    def test_cross_apply_pattern_exists(self):
        """Test CROSS APPLY pattern is defined"""
        assert "cross_apply" in TSQL_PATTERNS

    def test_temp_table_hash_pattern_exists(self):
        """Test temp table # pattern is defined"""
        assert "temp_table_hash" in TSQL_PATTERNS
        pattern = TSQL_PATTERNS["temp_table_hash"]
        assert re.search(pattern["pattern"], "#TempTable", re.IGNORECASE)

    def test_output_clause_pattern_exists(self):
        """Test OUTPUT clause pattern is defined"""
        assert "output_clause" in TSQL_PATTERNS

    def test_try_catch_pattern_exists(self):
        """Test TRY-CATCH pattern is defined"""
        assert "try_catch" in TSQL_PATTERNS

    def test_exec_dynamic_pattern_exists(self):
        """Test dynamic SQL EXEC pattern is defined"""
        assert "exec_dynamic" in TSQL_PATTERNS
        pattern = TSQL_PATTERNS["exec_dynamic"]
        assert pattern["risk"] == "high"

    def test_square_brackets_pattern_exists(self):
        """Test square brackets identifier pattern is defined"""
        assert "square_brackets" in TSQL_PATTERNS

    def test_all_patterns_have_required_fields(self):
        """Test all T-SQL patterns have required fields"""
        required_fields = ["pattern", "risk", "note", "pg_equivalent"]
        for name, pattern in TSQL_PATTERNS.items():
            for field in required_fields:
                assert field in pattern, f"Pattern {name} missing {field}"


class TestPLSQLPatterns:
    """Test PL/SQL pattern definitions"""

    def test_varchar2_pattern_exists(self):
        """Test VARCHAR2 pattern is defined"""
        assert "varchar2" in PLSQL_PATTERNS

    def test_number_type_pattern_exists(self):
        """Test NUMBER type pattern is defined"""
        assert "number_type" in PLSQL_PATTERNS

    def test_sysdate_pattern_exists(self):
        """Test SYSDATE pattern is defined"""
        assert "sysdate" in PLSQL_PATTERNS
        pattern = PLSQL_PATTERNS["sysdate"]
        assert re.search(pattern["pattern"], "SELECT SYSDATE", re.IGNORECASE)

    def test_nvl_function_pattern_exists(self):
        """Test NVL function pattern is defined"""
        assert "nvl_function" in PLSQL_PATTERNS
        pattern = PLSQL_PATTERNS["nvl_function"]
        assert "pg_equivalent" in pattern
        assert "COALESCE" in pattern["pg_equivalent"]

    def test_rownum_pattern_exists(self):
        """Test ROWNUM pattern is defined"""
        assert "rownum" in PLSQL_PATTERNS

    def test_dual_table_pattern_exists(self):
        """Test DUAL table pattern is defined"""
        assert "dual_table" in PLSQL_PATTERNS

    def test_connect_by_pattern_exists(self):
        """Test CONNECT BY pattern is defined"""
        assert "connect_by" in PLSQL_PATTERNS
        pattern = PLSQL_PATTERNS["connect_by"]
        assert pattern["risk"] == "high"

    def test_decode_function_pattern_exists(self):
        """Test DECODE function pattern is defined"""
        assert "decode_function" in PLSQL_PATTERNS
        pattern = PLSQL_PATTERNS["decode_function"]
        assert "CASE" in pattern["pg_equivalent"]

    def test_bulk_collect_pattern_exists(self):
        """Test BULK COLLECT pattern is defined"""
        assert "bulk_collect" in PLSQL_PATTERNS

    def test_package_definition_pattern_exists(self):
        """Test Oracle package pattern is defined"""
        assert "package_definition" in PLSQL_PATTERNS
        pattern = PLSQL_PATTERNS["package_definition"]
        assert pattern["risk"] == "high"

    def test_autonomous_transaction_pattern_exists(self):
        """Test AUTONOMOUS_TRANSACTION pattern is defined"""
        assert "autonomous_transaction" in PLSQL_PATTERNS

    def test_all_plsql_patterns_have_required_fields(self):
        """Test all PL/SQL patterns have required fields"""
        required_fields = ["pattern", "risk", "note", "pg_equivalent"]
        for name, pattern in PLSQL_PATTERNS.items():
            for field in required_fields:
                assert field in pattern, f"Pattern {name} missing {field}"


class TestMySQLPatterns:
    """Test MySQL pattern definitions"""

    def test_auto_increment_pattern_exists(self):
        """Test AUTO_INCREMENT pattern is defined"""
        assert "auto_increment" in MYSQL_PATTERNS
        pattern = MYSQL_PATTERNS["auto_increment"]
        assert re.search(pattern["pattern"], "AUTO_INCREMENT", re.IGNORECASE)

    def test_mysql_engine_pattern_exists(self):
        """Test ENGINE= pattern is defined"""
        assert "mysql_engine" in MYSQL_PATTERNS

    def test_backtick_quotes_pattern_exists(self):
        """Test backtick identifier pattern is defined"""
        assert "backtick_quotes" in MYSQL_PATTERNS

    def test_limit_offset_pattern_exists(self):
        """Test MySQL LIMIT offset pattern is defined"""
        assert "limit_offset" in MYSQL_PATTERNS

    def test_ifnull_pattern_exists(self):
        """Test IFNULL pattern is defined"""
        assert "ifnull" in MYSQL_PATTERNS
        pattern = MYSQL_PATTERNS["ifnull"]
        assert "COALESCE" in pattern["pg_equivalent"]

    def test_group_concat_pattern_exists(self):
        """Test GROUP_CONCAT pattern is defined"""
        assert "group_concat" in MYSQL_PATTERNS
        pattern = MYSQL_PATTERNS["group_concat"]
        assert "STRING_AGG" in pattern["pg_equivalent"]

    def test_enum_type_pattern_exists(self):
        """Test ENUM type pattern is defined"""
        assert "enum_type" in MYSQL_PATTERNS

    def test_insert_ignore_pattern_exists(self):
        """Test INSERT IGNORE pattern is defined"""
        assert "insert_ignore" in MYSQL_PATTERNS

    def test_replace_into_pattern_exists(self):
        """Test REPLACE INTO pattern is defined"""
        assert "replace_into" in MYSQL_PATTERNS

    def test_all_mysql_patterns_have_required_fields(self):
        """Test all MySQL patterns have required fields"""
        required_fields = ["pattern", "risk", "note", "pg_equivalent"]
        for name, pattern in MYSQL_PATTERNS.items():
            for field in required_fields:
                assert field in pattern, f"Pattern {name} missing {field}"


class TestDataTypeMappings:
    """Test data type mapping recommendations"""

    def test_sqlserver_nvarchar_mapping(self):
        """Test SQL Server NVARCHAR mapping - returns (target_type, is_breaking, notes)"""
        assert "NVARCHAR" in SQL_SERVER_TYPE_MAP
        assert SQL_SERVER_TYPE_MAP["NVARCHAR"][0] == "VARCHAR"

    def test_sqlserver_datetime2_mapping(self):
        """Test SQL Server DATETIME2 mapping - returns (target_type, is_breaking, notes)"""
        assert "DATETIME2" in SQL_SERVER_TYPE_MAP
        assert SQL_SERVER_TYPE_MAP["DATETIME2"][0] == "TIMESTAMP"

    def test_sqlserver_uniqueidentifier_mapping(self):
        """Test SQL Server UNIQUEIDENTIFIER mapping - returns (target_type, is_breaking, notes)"""
        assert "UNIQUEIDENTIFIER" in SQL_SERVER_TYPE_MAP
        assert SQL_SERVER_TYPE_MAP["UNIQUEIDENTIFIER"][0] == "UUID"

    def test_sqlserver_money_mapping(self):
        """Test SQL Server MONEY mapping - returns tuple"""
        assert "MONEY" in SQL_SERVER_TYPE_MAP
        mapping = SQL_SERVER_TYPE_MAP["MONEY"]
        assert isinstance(mapping, tuple)
        assert len(mapping) == 3

    def test_oracle_varchar2_mapping(self):
        """Test Oracle VARCHAR2 mapping - returns (target_type, is_breaking, notes)"""
        assert "VARCHAR2" in ORACLE_TYPE_MAP
        assert ORACLE_TYPE_MAP["VARCHAR2"][0] == "VARCHAR"

    def test_oracle_number_mapping(self):
        """Test Oracle NUMBER mapping - returns (target_type, is_breaking, notes)"""
        assert "NUMBER" in ORACLE_TYPE_MAP
        assert ORACLE_TYPE_MAP["NUMBER"][0] == "NUMERIC"

    def test_oracle_clob_mapping(self):
        """Test Oracle CLOB mapping - returns (target_type, is_breaking, notes)"""
        assert "CLOB" in ORACLE_TYPE_MAP
        assert ORACLE_TYPE_MAP["CLOB"][0] == "TEXT"

    def test_oracle_blob_mapping(self):
        """Test Oracle BLOB mapping - returns (target_type, is_breaking, notes)"""
        assert "BLOB" in ORACLE_TYPE_MAP
        assert ORACLE_TYPE_MAP["BLOB"][0] == "BYTEA"

    def test_mysql_mediumint_mapping(self):
        """Test MySQL MEDIUMINT mapping - returns (target_type, is_breaking, notes)"""
        assert "MEDIUMINT" in MYSQL_TYPE_MAP
        assert MYSQL_TYPE_MAP["MEDIUMINT"][0] == "INTEGER"

    def test_mysql_tinyint_mapping(self):
        """Test MySQL TINYINT mapping - returns (target_type, is_breaking, notes)"""
        assert "TINYINT" in MYSQL_TYPE_MAP
        assert MYSQL_TYPE_MAP["TINYINT"][0] == "SMALLINT"

    def test_mysql_datetime_mapping(self):
        """Test MySQL DATETIME mapping - returns (target_type, is_breaking, notes)"""
        assert "DATETIME" in MYSQL_TYPE_MAP
        assert MYSQL_TYPE_MAP["DATETIME"][0] == "TIMESTAMP"

    def test_mysql_enum_mapping(self):
        """Test MySQL ENUM mapping"""
        assert "ENUM" in MYSQL_TYPE_MAP


class TestDataClasses:
    """Test data class initialization and defaults"""

    def test_database_table_defaults(self):
        """Test DatabaseTable has correct defaults"""
        table = DatabaseTable(name="Users")
        assert table.name == "Users"
        assert table.schema_name == "dbo"
        assert table.columns == []
        assert table.primary_key == []
        assert table.foreign_keys == []
        assert table.has_identity is False
        assert table.has_computed_columns is False

    def test_stored_procedure_defaults(self):
        """Test StoredProcedure has correct defaults"""
        proc = StoredProcedure(name="GetUsers")
        assert proc.name == "GetUsers"
        assert proc.object_type == "procedure"
        assert proc.complexity_score == 0.0
        assert proc.uses_cursors is False
        assert proc.uses_temp_tables is False
        assert proc.uses_dynamic_sql is False
        assert proc.proprietary_functions == []

    def test_database_view_defaults(self):
        """Test DatabaseView has correct defaults"""
        view = DatabaseView(name="ActiveUsers")
        assert view.name == "ActiveUsers"
        assert view.schema_name == "dbo"
        assert view.is_materialized is False
        assert view.is_indexed is False
        assert view.base_tables == []

    def test_database_pattern_match_defaults(self):
        """Test DatabasePatternMatch has correct defaults"""
        pattern = DatabasePatternMatch(
            pattern_name="test",
            pattern_category="tsql",
            file_path="test.sql",
            line_number=1,
            code_snippet="",
            risk_level="low",
            migration_note="",
            postgresql_equivalent=""
        )
        assert pattern.fp_multiplier == 1.0
        assert pattern.requires_rewrite is False

    def test_database_analysis_result_defaults(self):
        """Test DatabaseAnalysisResult has correct defaults"""
        result = DatabaseAnalysisResult()
        assert result.source_database == "unknown"
        assert result.total_sql_files == 0
        assert result.total_loc == 0
        assert result.total_tables == 0
        assert result.total_procedures == 0
        assert result.total_views == 0
        assert result.migration_difficulty == "medium"
        assert result.tables == []
        assert result.stored_procedures == []

    def test_data_type_mapping_defaults(self):
        """Test DataTypeMapping has correct defaults"""
        mapping = DataTypeMapping(
            source_type="NVARCHAR",
            source_db="sqlserver",
            postgresql_type="VARCHAR"
        )
        assert mapping.requires_conversion is False
        assert mapping.data_loss_risk is False
        assert mapping.notes == ""


class TestPatternMatching:
    """Test pattern matching functionality"""

    def test_tsql_identity_pattern_matches(self):
        """Test IDENTITY pattern matches correctly"""
        pattern = TSQL_PATTERNS["identity_column"]["pattern"]
        assert re.search(pattern, "ID INT IDENTITY(1, 1)", re.IGNORECASE)
        assert re.search(pattern, "IDENTITY(1,1)", re.IGNORECASE)
        assert not re.search(pattern, "IDENTITY_COLUMN", re.IGNORECASE)

    def test_tsql_top_pattern_matches(self):
        """Test TOP pattern matches correctly"""
        pattern = TSQL_PATTERNS["top_clause"]["pattern"]
        assert re.search(pattern, "SELECT TOP 10 *", re.IGNORECASE)
        assert re.search(pattern, "TOP(100)", re.IGNORECASE)
        assert not re.search(pattern, "LAPTOP", re.IGNORECASE)

    def test_plsql_varchar2_pattern_matches(self):
        """Test VARCHAR2 pattern matches correctly"""
        pattern = PLSQL_PATTERNS["varchar2"]["pattern"]
        assert re.search(pattern, "VARCHAR2(100)", re.IGNORECASE)
        assert not re.search(pattern, "VARCHAR(100)", re.IGNORECASE)

    def test_plsql_sysdate_pattern_matches(self):
        """Test SYSDATE pattern matches correctly"""
        pattern = PLSQL_PATTERNS["sysdate"]["pattern"]
        assert re.search(pattern, "SELECT SYSDATE FROM DUAL", re.IGNORECASE)

    def test_mysql_auto_increment_pattern_matches(self):
        """Test AUTO_INCREMENT pattern matches correctly"""
        pattern = MYSQL_PATTERNS["auto_increment"]["pattern"]
        assert re.search(pattern, "AUTO_INCREMENT", re.IGNORECASE)


class TestServiceAnalyze:
    """Test the analyze method of DatabaseAnalyzerService"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def mock_analysis(self):
        analysis = MagicMock()
        analysis.id = "test-id"
        analysis.repo_path = "/tmp/test-repo"
        return analysis

    @pytest.mark.asyncio
    async def test_analyze_returns_result(self, mock_db, mock_analysis, tmp_path):
        """Test analyze method returns DatabaseAnalysisResult"""
        service = DatabaseAnalyzerService(mock_db)
        result = await service.analyze(mock_analysis, tmp_path)
        assert isinstance(result, DatabaseAnalysisResult)

    @pytest.mark.asyncio
    async def test_analyze_empty_directory(self, mock_db, mock_analysis, tmp_path):
        """Test analyze handles empty directory"""
        service = DatabaseAnalyzerService(mock_db)
        result = await service.analyze(mock_analysis, tmp_path)
        assert result.total_sql_files == 0
        assert result.source_database == "unknown"

    @pytest.mark.asyncio
    async def test_analyze_detects_sqlserver(self, mock_db, mock_analysis, tmp_path):
        """Test analyze detects SQL Server database"""
        # Create SQL Server file
        sql_file = tmp_path / "schema.sql"
        sql_file.write_text("""
            CREATE TABLE Users (
                ID INT IDENTITY(1,1) PRIMARY KEY,
                Name NVARCHAR(100),
                CreatedAt DATETIME2
            )
            SET NOCOUNT ON
        """)

        service = DatabaseAnalyzerService(mock_db)
        result = await service.analyze(mock_analysis, tmp_path)
        assert result.source_database == "sqlserver"

    @pytest.mark.asyncio
    async def test_analyze_detects_oracle(self, mock_db, mock_analysis, tmp_path):
        """Test analyze detects Oracle database"""
        sql_file = tmp_path / "schema.sql"
        sql_file.write_text("""
            CREATE TABLE Users (
                Name VARCHAR2(100),
                Age NUMBER(3)
            );
            SELECT SYSDATE FROM DUAL;
        """)

        service = DatabaseAnalyzerService(mock_db)
        result = await service.analyze(mock_analysis, tmp_path)
        assert result.source_database == "oracle"

    @pytest.mark.asyncio
    async def test_analyze_detects_mysql(self, mock_db, mock_analysis, tmp_path):
        """Test analyze detects MySQL database"""
        sql_file = tmp_path / "schema.sql"
        sql_file.write_text("""
            CREATE TABLE Users (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                Name VARCHAR(100)
            ) ENGINE=InnoDB;
        """)

        service = DatabaseAnalyzerService(mock_db)
        result = await service.analyze(mock_analysis, tmp_path)
        assert result.source_database == "mysql"

    @pytest.mark.asyncio
    async def test_analyze_counts_sql_files(self, mock_db, mock_analysis, tmp_path):
        """Test analyze correctly counts SQL files"""
        # Create multiple SQL files
        (tmp_path / "schema.sql").write_text("CREATE TABLE t1 (id INT)")
        (tmp_path / "procedures.sql").write_text("CREATE PROCEDURE p1 AS SELECT 1")
        (tmp_path / "views.sql").write_text("CREATE VIEW v1 AS SELECT 1")

        service = DatabaseAnalyzerService(mock_db)
        result = await service.analyze(mock_analysis, tmp_path)
        assert result.total_sql_files == 3

    @pytest.mark.asyncio
    async def test_analyze_skips_node_modules(self, mock_db, mock_analysis, tmp_path):
        """Test analyze skips node_modules directory"""
        nm_dir = tmp_path / "node_modules"
        nm_dir.mkdir()
        (nm_dir / "package.sql").write_text("SELECT 1")
        (tmp_path / "schema.sql").write_text("SELECT 2")

        service = DatabaseAnalyzerService(mock_db)
        result = await service.analyze(mock_analysis, tmp_path)
        # Should only count schema.sql, not the one in node_modules
        assert result.total_sql_files == 1


class TestServiceHelperMethods:
    """Test helper methods of DatabaseAnalyzerService"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        return DatabaseAnalyzerService(mock_db)

    def test_should_skip_git_directory(self, service):
        """Test _should_skip skips .git directory"""
        path = Path("/repo/.git/config")
        assert service._should_skip(path) is True

    def test_should_skip_node_modules(self, service):
        """Test _should_skip skips node_modules"""
        path = Path("/repo/node_modules/package/file.sql")
        assert service._should_skip(path) is True

    def test_should_skip_vendor(self, service):
        """Test _should_skip skips vendor directory"""
        path = Path("/repo/vendor/lib/file.sql")
        assert service._should_skip(path) is True

    def test_should_not_skip_src(self, service):
        """Test _should_skip does not skip src directory"""
        path = Path("/repo/src/database/schema.sql")
        assert service._should_skip(path) is False
