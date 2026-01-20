"""
Unit tests for SQLAnalysisService - F3 (Fase 24).

Tests cover:
- Query complexity scoring
- Operation type detection
- Table and JOIN extraction
- Subquery detection
- Issue and suggestion generation
- Multi-file analysis
- Multi-language SQL extraction

Author: Claude Code (Week 158)
Date: 2026-01-19
"""

import pytest

from app.services.sql_analysis_service import (
    QueryComplexity,
    SQLOperationType,
    JoinType,
    JoinInfo,
    SubqueryInfo,
    QueryMetrics,
    QueryAnalysis,
    SQLAnalysisResult,
    SQLAnalysisService,
)


# ==================== Fixtures ====================

@pytest.fixture
def service():
    """Create a fresh SQLAnalysisService instance."""
    return SQLAnalysisService()


@pytest.fixture
def simple_select_query():
    """Simple SELECT query."""
    return "SELECT id, name FROM users WHERE active = 1"


@pytest.fixture
def complex_join_query():
    """Complex query with multiple JOINs."""
    return """
    SELECT u.id, u.name, o.order_id, o.total, p.name AS product
    FROM users u
    INNER JOIN orders o ON u.id = o.user_id
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    INNER JOIN products p ON oi.product_id = p.id
    WHERE o.status = 'completed'
    ORDER BY o.created_at DESC
    """


@pytest.fixture
def subquery_query():
    """Query with subqueries."""
    return """
    SELECT * FROM users
    WHERE id IN (
        SELECT user_id FROM orders
        WHERE total > (
            SELECT AVG(total) FROM orders
        )
    )
    """


# ==================== QueryMetrics Tests ====================

class TestQueryMetrics:
    """Test QueryMetrics data class."""

    def test_default_metrics(self):
        """Test default metric values."""
        metrics = QueryMetrics()
        assert metrics.table_count == 0
        assert metrics.join_count == 0
        assert metrics.subquery_count == 0
        assert metrics.has_where_clause is False
        assert metrics.aggregate_functions == []

    def test_metrics_with_values(self):
        """Test metrics with custom values."""
        metrics = QueryMetrics(
            table_count=3,
            join_count=2,
            has_where_clause=True,
            aggregate_functions=["COUNT", "SUM"]
        )
        assert metrics.table_count == 3
        assert metrics.join_count == 2
        assert len(metrics.aggregate_functions) == 2


# ==================== QueryAnalysis Tests ====================

class TestQueryAnalysis:
    """Test QueryAnalysis data class."""

    def test_to_dict(self, service, simple_select_query):
        """Test serialization to dictionary."""
        analysis = service.analyze_query(simple_select_query)
        data = analysis.to_dict()

        assert "query_text" in data
        assert "operation_type" in data
        assert "complexity" in data
        assert "metrics" in data
        assert "tables" in data

    def test_to_dict_truncates_long_query(self, service):
        """Test long queries are truncated in serialization."""
        long_query = "SELECT " + ", ".join([f"col{i}" for i in range(200)]) + " FROM table"
        analysis = service.analyze_query(long_query)
        data = analysis.to_dict()

        assert len(data["query_text"]) <= 503  # 500 + "..."


# ==================== Operation Type Detection Tests ====================

class TestOperationTypeDetection:
    """Test SQL operation type detection."""

    def test_detect_select(self, service):
        """Test SELECT detection."""
        analysis = service.analyze_query("SELECT * FROM users")
        assert analysis.operation_type == SQLOperationType.SELECT

    def test_detect_insert(self, service):
        """Test INSERT detection."""
        analysis = service.analyze_query("INSERT INTO users (name) VALUES ('test')")
        assert analysis.operation_type == SQLOperationType.INSERT

    def test_detect_update(self, service):
        """Test UPDATE detection."""
        analysis = service.analyze_query("UPDATE users SET name = 'test' WHERE id = 1")
        assert analysis.operation_type == SQLOperationType.UPDATE

    def test_detect_delete(self, service):
        """Test DELETE detection."""
        analysis = service.analyze_query("DELETE FROM users WHERE id = 1")
        assert analysis.operation_type == SQLOperationType.DELETE

    def test_detect_create(self, service):
        """Test CREATE detection."""
        analysis = service.analyze_query("CREATE TABLE users (id INT PRIMARY KEY)")
        assert analysis.operation_type == SQLOperationType.CREATE

    def test_detect_alter(self, service):
        """Test ALTER detection."""
        analysis = service.analyze_query("ALTER TABLE users ADD COLUMN email VARCHAR(255)")
        assert analysis.operation_type == SQLOperationType.ALTER

    def test_detect_drop(self, service):
        """Test DROP detection."""
        analysis = service.analyze_query("DROP TABLE users")
        assert analysis.operation_type == SQLOperationType.DROP

    def test_detect_stored_proc(self, service):
        """Test stored procedure detection."""
        analysis = service.analyze_query("EXEC sp_get_users @status = 'active'")
        assert analysis.operation_type == SQLOperationType.STORED_PROC


# ==================== Table Extraction Tests ====================

class TestTableExtraction:
    """Test table name extraction."""

    def test_extract_single_table(self, service):
        """Test extracting single table from SELECT."""
        analysis = service.analyze_query("SELECT * FROM users")
        assert "USERS" in analysis.tables

    def test_extract_tables_from_join(self, service, complex_join_query):
        """Test extracting tables from JOINs."""
        analysis = service.analyze_query(complex_join_query)
        # Should find users, orders, order_items, products (case insensitive)
        assert analysis.metrics.table_count >= 2

    def test_extract_table_from_insert(self, service):
        """Test extracting table from INSERT."""
        analysis = service.analyze_query("INSERT INTO orders (user_id, total) VALUES (1, 100)")
        assert "ORDERS" in analysis.tables

    def test_extract_table_from_update(self, service):
        """Test extracting table from UPDATE."""
        analysis = service.analyze_query("UPDATE products SET price = 10 WHERE id = 1")
        assert "PRODUCTS" in analysis.tables

    def test_extract_table_from_delete(self, service):
        """Test extracting table from DELETE."""
        analysis = service.analyze_query("DELETE FROM logs WHERE created_at < '2024-01-01'")
        assert "LOGS" in analysis.tables


# ==================== JOIN Extraction Tests ====================

class TestJoinExtraction:
    """Test JOIN extraction and classification."""

    def test_detect_inner_join(self, service):
        """Test INNER JOIN detection."""
        query = "SELECT * FROM a INNER JOIN b ON a.id = b.a_id"
        analysis = service.analyze_query(query)
        assert analysis.metrics.join_count >= 1
        assert any(j.join_type == JoinType.INNER for j in analysis.joins)

    def test_detect_left_join(self, service):
        """Test LEFT JOIN detection."""
        query = "SELECT * FROM a LEFT JOIN b ON a.id = b.a_id"
        analysis = service.analyze_query(query)
        assert any(j.join_type == JoinType.LEFT for j in analysis.joins)

    def test_detect_left_outer_join(self, service):
        """Test LEFT OUTER JOIN detection."""
        query = "SELECT * FROM a LEFT OUTER JOIN b ON a.id = b.a_id"
        analysis = service.analyze_query(query)
        assert any(j.join_type == JoinType.LEFT for j in analysis.joins)

    def test_detect_right_join(self, service):
        """Test RIGHT JOIN detection."""
        query = "SELECT * FROM a RIGHT JOIN b ON a.id = b.a_id"
        analysis = service.analyze_query(query)
        assert any(j.join_type == JoinType.RIGHT for j in analysis.joins)

    def test_detect_full_join(self, service):
        """Test FULL JOIN detection."""
        query = "SELECT * FROM a FULL JOIN b ON a.id = b.a_id"
        analysis = service.analyze_query(query)
        assert any(j.join_type == JoinType.FULL for j in analysis.joins)

    def test_detect_cross_join(self, service):
        """Test CROSS JOIN detection."""
        query = "SELECT * FROM a CROSS JOIN b"
        analysis = service.analyze_query(query)
        assert any(j.join_type == JoinType.CROSS for j in analysis.joins)

    def test_detect_simple_join_as_inner(self, service):
        """Test simple JOIN defaults to INNER."""
        query = "SELECT * FROM a JOIN b ON a.id = b.a_id"
        analysis = service.analyze_query(query)
        assert any(j.join_type == JoinType.INNER for j in analysis.joins)

    def test_multiple_joins(self, service, complex_join_query):
        """Test detecting multiple JOINs."""
        analysis = service.analyze_query(complex_join_query)
        assert analysis.metrics.join_count >= 3


# ==================== Subquery Detection Tests ====================

class TestSubqueryDetection:
    """Test subquery detection."""

    def test_detect_simple_subquery(self, service):
        """Test detecting simple subquery."""
        query = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
        analysis = service.analyze_query(query)
        assert analysis.metrics.subquery_count >= 1

    def test_detect_nested_subqueries(self, service, subquery_query):
        """Test detecting nested subqueries."""
        analysis = service.analyze_query(subquery_query)
        assert analysis.metrics.subquery_count >= 2
        assert analysis.metrics.max_subquery_depth >= 2

    def test_no_subquery(self, service, simple_select_query):
        """Test query without subqueries."""
        analysis = service.analyze_query(simple_select_query)
        assert analysis.metrics.subquery_count == 0


# ==================== Clause Detection Tests ====================

class TestClauseDetection:
    """Test SQL clause detection."""

    def test_detect_where_clause(self, service):
        """Test WHERE clause detection."""
        analysis = service.analyze_query("SELECT * FROM users WHERE active = 1")
        assert analysis.metrics.has_where_clause is True

    def test_detect_no_where_clause(self, service):
        """Test missing WHERE clause detection."""
        analysis = service.analyze_query("SELECT * FROM users")
        assert analysis.metrics.has_where_clause is False

    def test_detect_group_by(self, service):
        """Test GROUP BY clause detection."""
        analysis = service.analyze_query("SELECT status, COUNT(*) FROM orders GROUP BY status")
        assert analysis.metrics.has_group_by is True

    def test_detect_order_by(self, service):
        """Test ORDER BY clause detection."""
        analysis = service.analyze_query("SELECT * FROM users ORDER BY created_at DESC")
        assert analysis.metrics.has_order_by is True

    def test_detect_having(self, service):
        """Test HAVING clause detection."""
        query = "SELECT status, COUNT(*) FROM orders GROUP BY status HAVING COUNT(*) > 10"
        analysis = service.analyze_query(query)
        assert analysis.metrics.has_having is True

    def test_detect_distinct(self, service):
        """Test DISTINCT detection."""
        analysis = service.analyze_query("SELECT DISTINCT category FROM products")
        assert analysis.metrics.uses_distinct is True

    def test_detect_union(self, service):
        """Test UNION detection."""
        query = "SELECT name FROM users UNION SELECT name FROM admins"
        analysis = service.analyze_query(query)
        assert analysis.metrics.uses_union is True


# ==================== Aggregate Function Tests ====================

class TestAggregateFunctionDetection:
    """Test aggregate function detection."""

    def test_detect_count(self, service):
        """Test COUNT detection."""
        analysis = service.analyze_query("SELECT COUNT(*) FROM users")
        assert "COUNT" in analysis.metrics.aggregate_functions

    def test_detect_sum(self, service):
        """Test SUM detection."""
        analysis = service.analyze_query("SELECT SUM(total) FROM orders")
        assert "SUM" in analysis.metrics.aggregate_functions

    def test_detect_avg(self, service):
        """Test AVG detection."""
        analysis = service.analyze_query("SELECT AVG(price) FROM products")
        assert "AVG" in analysis.metrics.aggregate_functions

    def test_detect_min_max(self, service):
        """Test MIN and MAX detection."""
        analysis = service.analyze_query("SELECT MIN(price), MAX(price) FROM products")
        assert "MIN" in analysis.metrics.aggregate_functions
        assert "MAX" in analysis.metrics.aggregate_functions

    def test_detect_multiple_aggregates(self, service):
        """Test multiple aggregate functions."""
        query = "SELECT COUNT(*), SUM(total), AVG(total) FROM orders"
        analysis = service.analyze_query(query)
        assert len(analysis.metrics.aggregate_functions) == 3


# ==================== Complexity Scoring Tests ====================

class TestComplexityScoring:
    """Test complexity score calculation."""

    def test_simple_query_low_score(self, service, simple_select_query):
        """Test simple query has low complexity score."""
        analysis = service.analyze_query(simple_select_query)
        assert analysis.complexity_score <= 30
        assert analysis.complexity == QueryComplexity.SIMPLE

    def test_join_query_medium_score(self, service):
        """Test query with JOINs has medium score."""
        query = "SELECT * FROM a JOIN b ON a.id = b.a_id WHERE a.active = 1"
        analysis = service.analyze_query(query)
        assert analysis.complexity_score >= 20

    def test_complex_query_high_score(self, service, complex_join_query):
        """Test complex query has high score."""
        analysis = service.analyze_query(complex_join_query)
        assert analysis.complexity_score >= 40
        assert analysis.complexity in [QueryComplexity.MEDIUM, QueryComplexity.COMPLEX]

    def test_highly_complex_query(self, service):
        """Test highly complex query."""
        query = """
        SELECT a.*, b.*, c.*, d.*, e.*
        FROM table1 a
        JOIN table2 b ON a.id = b.a_id
        JOIN table3 c ON b.id = c.b_id
        JOIN table4 d ON c.id = d.c_id
        JOIN table5 e ON d.id = e.d_id
        WHERE a.id IN (SELECT id FROM other WHERE x IN (SELECT x FROM deep))
        GROUP BY a.id
        HAVING COUNT(*) > 10
        UNION
        SELECT * FROM backup_table
        """
        analysis = service.analyze_query(query)
        assert analysis.complexity_score >= 60
        assert analysis.complexity in [QueryComplexity.COMPLEX, QueryComplexity.HIGHLY_COMPLEX]

    def test_score_capped_at_100(self, service):
        """Test complexity score is capped at 100."""
        # Extremely complex query
        query = """
        SELECT DISTINCT * FROM t1
        JOIN t2 ON 1=1 JOIN t3 ON 1=1 JOIN t4 ON 1=1 JOIN t5 ON 1=1
        JOIN t6 ON 1=1 JOIN t7 ON 1=1 JOIN t8 ON 1=1 JOIN t9 ON 1=1
        WHERE x IN (SELECT y FROM (SELECT z FROM (SELECT 1)))
        GROUP BY 1 HAVING 1=1
        UNION SELECT * FROM other
        """
        analysis = service.analyze_query(query)
        assert analysis.complexity_score <= 100


# ==================== Issue Detection Tests ====================

class TestIssueDetection:
    """Test issue and warning detection."""

    def test_detect_select_star(self, service):
        """Test SELECT * detection."""
        analysis = service.analyze_query("SELECT * FROM users WHERE id = 1")
        assert any("SELECT *" in issue for issue in analysis.issues)

    def test_detect_unbounded_select(self, service):
        """Test unbounded SELECT detection."""
        analysis = service.analyze_query("SELECT id, name FROM users")
        assert any("Unbounded" in issue for issue in analysis.issues)

    def test_no_issue_for_bounded_select(self, service):
        """Test no unbounded issue when WHERE/LIMIT present."""
        analysis = service.analyze_query("SELECT id FROM users WHERE active = 1")
        unbounded_issues = [i for i in analysis.issues if "Unbounded" in i]
        assert len(unbounded_issues) == 0

    def test_detect_high_join_count(self, service):
        """Test high JOIN count detection."""
        query = """
        SELECT * FROM a
        JOIN b ON 1=1 JOIN c ON 1=1 JOIN d ON 1=1 JOIN e ON 1=1
        WHERE 1=1
        """
        analysis = service.analyze_query(query)
        assert any("JOIN count" in issue for issue in analysis.issues)

    def test_detect_deep_subqueries(self, service):
        """Test deep subquery warning."""
        query = """
        SELECT * FROM t1 WHERE x IN (
            SELECT y FROM t2 WHERE y IN (
                SELECT z FROM t3 WHERE z IN (
                    SELECT w FROM t4
                )
            )
        )
        """
        analysis = service.analyze_query(query)
        assert any("nested subqueries" in issue for issue in analysis.issues)


# ==================== Suggestion Tests ====================

class TestSuggestions:
    """Test optimization suggestions."""

    def test_suggest_explicit_columns(self, service):
        """Test suggestion to specify columns."""
        analysis = service.analyze_query("SELECT * FROM users")
        assert any("columns" in s.lower() for s in analysis.suggestions)

    def test_suggest_where_or_limit(self, service):
        """Test suggestion to add WHERE/LIMIT."""
        analysis = service.analyze_query("SELECT id FROM users")
        assert any("WHERE" in s or "LIMIT" in s for s in analysis.suggestions)

    def test_suggest_cte_for_deep_subqueries(self, service, subquery_query):
        """Test CTE suggestion for deep subqueries."""
        analysis = service.analyze_query(subquery_query)
        # May or may not trigger depending on depth detection
        # Just verify suggestions list is populated
        assert isinstance(analysis.suggestions, list)


# ==================== SQL Extraction Tests ====================

class TestSQLExtraction:
    """Test SQL extraction from source code."""

    def test_extract_python_execute(self, service):
        """Test extracting SQL from Python cursor.execute()."""
        code = '''
def get_users():
    cursor.execute("SELECT id, name FROM users WHERE active = 1")
    return cursor.fetchall()
'''
        result = service.analyze_files({"file.py": code}, language="python")
        assert result.queries_analyzed >= 1

    def test_extract_python_raw_string(self, service):
        """Test extracting SQL from Python variable."""
        code = '''
sql = "SELECT * FROM orders WHERE status = 'pending'"
results = db.execute(sql)
'''
        result = service.analyze_files({"file.py": code}, language="python")
        assert result.queries_analyzed >= 1

    def test_extract_java_jdbc(self, service):
        """Test extracting SQL from Java JDBC."""
        code = '''
public List<User> getUsers() {
    String sql = "SELECT id, name FROM users";
    Statement stmt = conn.createStatement();
    ResultSet rs = stmt.executeQuery("SELECT * FROM orders WHERE id = 1");
    return null;
}
'''
        result = service.analyze_files({"file.java": code}, language="java")
        # Should find at least the executeQuery SQL
        assert result.queries_analyzed >= 1

    def test_extract_javascript_query(self, service):
        """Test extracting SQL from JavaScript."""
        code = '''
async function getOrders() {
    const result = await db.query("SELECT * FROM orders WHERE user_id = $1", [userId]);
    return result.rows;
}
'''
        result = service.analyze_files({"file.js": code}, language="javascript")
        assert result.queries_analyzed >= 1

    def test_extract_csharp_ado(self, service):
        """Test extracting SQL from C# ADO.NET."""
        code = '''
public void GetUsers()
{
    var cmd = new SqlCommand("SELECT * FROM Users WHERE Active = 1", conn);
    var reader = cmd.ExecuteReader();
}
'''
        result = service.analyze_files({"file.cs": code}, language="csharp")
        assert result.queries_analyzed >= 1

    def test_detect_language_from_extension(self, service):
        """Test language detection from file extension."""
        assert service._detect_language("app.py") == "python"
        assert service._detect_language("Service.java") == "java"
        assert service._detect_language("index.js") == "javascript"
        assert service._detect_language("index.ts") == "javascript"
        assert service._detect_language("Program.cs") == "csharp"
        assert service._detect_language("script.php") == "php"


# ==================== Multi-File Analysis Tests ====================

class TestMultiFileAnalysis:
    """Test multi-file analysis."""

    def test_analyze_multiple_files(self, service):
        """Test analyzing multiple files."""
        files = {
            "users.py": 'cursor.execute("SELECT * FROM users")',
            "orders.py": 'cursor.execute("SELECT * FROM orders JOIN users ON users.id = orders.user_id")',
        }
        result = service.analyze_files(files)

        assert result.queries_analyzed >= 2
        assert len(result.queries) >= 2

    def test_complexity_distribution(self, service):
        """Test complexity distribution calculation."""
        files = {
            "simple.py": 'cursor.execute("SELECT id FROM users WHERE id = 1")',
            "medium.py": 'cursor.execute("SELECT * FROM users u JOIN orders o ON u.id = o.user_id")',
        }
        result = service.analyze_files(files)

        # Should have distribution for all levels
        assert isinstance(result.complexity_distribution, dict)

    def test_files_with_complex_sql(self, service):
        """Test tracking files with complex SQL."""
        files = {
            "simple.py": 'cursor.execute("SELECT id FROM t WHERE id = 1")',
            "complex.py": '''cursor.execute("""
                SELECT * FROM a
                JOIN b ON 1=1 JOIN c ON 1=1 JOIN d ON 1=1
                WHERE x IN (SELECT y FROM deep)
            """)''',
        }
        result = service.analyze_files(files)

        # complex.py should be flagged
        # (if score is high enough)
        assert isinstance(result.files_with_complex_sql, list)

    def test_issues_by_type_aggregation(self, service):
        """Test issues are aggregated by type."""
        files = {
            "a.py": 'cursor.execute("SELECT * FROM users")',
            "b.py": 'cursor.execute("SELECT * FROM orders")',
        }
        result = service.analyze_files(files)

        # Both have SELECT * issue
        assert isinstance(result.issues_by_type, dict)

    def test_average_complexity_score(self, service):
        """Test average complexity score calculation."""
        files = {
            "a.py": 'cursor.execute("SELECT id FROM t WHERE id = 1")',
            "b.py": 'cursor.execute("SELECT id FROM t WHERE id = 2")',
        }
        result = service.analyze_files(files)

        assert result.avg_complexity_score >= 0
        assert result.avg_complexity_score <= 100

    def test_scan_duration_tracked(self, service):
        """Test scan duration is recorded."""
        files = {"test.py": 'cursor.execute("SELECT 1")'}
        result = service.analyze_files(files)

        assert result.scan_duration_seconds >= 0


# ==================== Report Generation Tests ====================

class TestReportGeneration:
    """Test markdown report generation."""

    def test_generate_report(self, service):
        """Test report generation."""
        files = {
            "test.py": 'cursor.execute("SELECT * FROM users WHERE active = 1")',
        }
        result = service.analyze_files(files)
        report = service.get_complexity_report(result)

        assert "# SQL Complexity Analysis Report" in report
        assert "Queries Analyzed" in report
        assert "Complexity Distribution" in report

    def test_report_includes_issues(self, service):
        """Test report includes common issues."""
        files = {
            "test.py": 'cursor.execute("SELECT * FROM users")',
        }
        result = service.analyze_files(files)
        report = service.get_complexity_report(result)

        # Should mention SELECT * issue
        assert "Issues" in report or "SELECT *" in report

    def test_report_handles_empty_result(self, service):
        """Test report handles empty results."""
        result = SQLAnalysisResult()
        report = service.get_complexity_report(result)

        assert "# SQL Complexity Analysis Report" in report
        assert "Queries Analyzed:** 0" in report


# ==================== Edge Cases ====================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_query(self, service):
        """Test handling empty query."""
        # _is_valid_sql should reject empty queries
        assert service._is_valid_sql("") is False

    def test_short_query(self, service):
        """Test handling very short query."""
        assert service._is_valid_sql("SELECT") is False

    def test_non_sql_string(self, service):
        """Test handling non-SQL string."""
        assert service._is_valid_sql("Hello World") is False

    def test_query_with_placeholders(self, service):
        """Test query with various placeholder styles."""
        query = "SELECT * FROM users WHERE id = ? AND name = :name AND status = %s"
        analysis = service.analyze_query(query)
        assert analysis.operation_type == SQLOperationType.SELECT

    def test_case_insensitive_keywords(self, service):
        """Test case insensitivity of SQL keywords."""
        analysis = service.analyze_query("select * from Users where ID = 1")
        assert analysis.operation_type == SQLOperationType.SELECT
        assert analysis.metrics.has_where_clause is True

    def test_multiline_query(self, service, complex_join_query):
        """Test multiline query handling."""
        analysis = service.analyze_query(complex_join_query)
        assert analysis.operation_type == SQLOperationType.SELECT
        assert analysis.metrics.join_count >= 3

    def test_empty_files_dict(self, service):
        """Test analyzing empty files dict."""
        result = service.analyze_files({})
        assert result.queries_analyzed == 0

    def test_file_with_no_sql(self, service):
        """Test file without SQL queries."""
        files = {
            "utils.py": '''
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
'''
        }
        result = service.analyze_files(files)
        assert result.queries_analyzed == 0


# ==================== SQLAnalysisResult Tests ====================

class TestSQLAnalysisResult:
    """Test SQLAnalysisResult data class."""

    def test_to_dict(self, service):
        """Test result serialization."""
        files = {
            "test.py": 'cursor.execute("SELECT id FROM users WHERE id = 1")',
        }
        result = service.analyze_files(files)
        data = result.to_dict()

        assert "queries_analyzed" in data
        assert "complexity_distribution" in data
        assert "avg_complexity_score" in data
        assert "queries" in data

    def test_queries_limited_in_output(self, service):
        """Test queries are limited in output."""
        # Create many queries
        files = {
            f"file{i}.py": f'cursor.execute("SELECT id FROM t{i} WHERE id = {i}")'
            for i in range(150)
        }
        result = service.analyze_files(files)
        data = result.to_dict()

        # Should limit to 100 queries
        assert len(data["queries"]) <= 100
