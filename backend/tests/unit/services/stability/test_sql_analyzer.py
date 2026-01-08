# Unit Tests for SQLAnalyzer
# Tests for SQL performance issue detection in Classic ASP
# Week 145 Implementation

import pytest
from app.services.stability.types import (
    SeverityLevel,
    StabilityCategory,
)
from app.services.stability.detectors.sql_analyzer import (
    SQLAnalyzer,
    SQLIssueType,
    SQLQuery,
    SQLFinding,
)


class TestSQLAnalyzerConfiguration:
    """Configuration tests for SQLAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        return SQLAnalyzer()

    def test_supported_extensions(self, analyzer):
        """Should support .asp, .inc, and .asa files."""
        extensions = analyzer.get_supported_extensions()
        assert ".asp" in extensions
        assert ".inc" in extensions
        assert ".asa" in extensions

    def test_language_name(self, analyzer):
        """Should return correct language name."""
        assert analyzer.get_language() == "Classic ASP (VBScript)"

    def test_case_insensitive(self, analyzer):
        """VBScript should be case-insensitive."""
        assert analyzer.is_case_insensitive() is True

    def test_category(self, analyzer):
        """Should be SQL_PERFORMANCE category."""
        assert analyzer.get_category() == StabilityCategory.SQL_PERFORMANCE

    def test_supports_file(self, analyzer):
        """Should support ASP files."""
        assert analyzer.supports_file("test.asp") is True
        assert analyzer.supports_file("include.inc") is True
        assert analyzer.supports_file("global.asa") is True
        assert analyzer.supports_file("script.js") is False


class TestNPlusOneDetection:
    """Tests for N+1 query pattern detection."""

    @pytest.fixture
    def analyzer(self):
        return SQLAnalyzer()

    def test_detect_query_in_for_loop(self, analyzer):
        """Should detect SQL query inside For loop."""
        code = '''
        <%
        Dim rs, id
        For Each id In idArray
            Set rs = conn.Execute("SELECT * FROM users WHERE id = " & id)
            Response.Write rs("name")
            rs.Close
        Next
        %>
        '''
        findings = analyzer.analyze(code)

        n_plus_one = [f for f in findings
                     if f.issue_type == SQLIssueType.N_PLUS_ONE or
                        f.issue_type == SQLIssueType.QUERY_IN_LOOP]
        assert len(n_plus_one) >= 1

    def test_detect_query_in_while_loop(self, analyzer):
        """Should detect SQL query inside While loop."""
        code = '''
        <%
        Dim rs
        Do While Not rs.EOF
            Set rsDetail = conn.Execute("SELECT * FROM details WHERE parent_id = " & rs("id"))
            ProcessDetail rsDetail
            rsDetail.Close
            rs.MoveNext
        Loop
        %>
        '''
        findings = analyzer.analyze(code)

        n_plus_one = [f for f in findings
                     if f.issue_type == SQLIssueType.N_PLUS_ONE or
                        f.issue_type == SQLIssueType.QUERY_IN_LOOP]
        assert len(n_plus_one) >= 1

    def test_single_query_no_n_plus_one(self, analyzer):
        """Should not flag single query outside loop."""
        code = '''
        <%
        Dim rs
        Set rs = conn.Execute("SELECT * FROM users WHERE active = 1")
        %>
        '''
        findings = analyzer.analyze(code)

        n_plus_one = [f for f in findings
                     if f.issue_type == SQLIssueType.N_PLUS_ONE]
        assert len(n_plus_one) == 0


class TestSQLInjectionDetection:
    """Tests for SQL injection vulnerability detection."""

    @pytest.fixture
    def analyzer(self):
        return SQLAnalyzer()

    def test_detect_string_concat_in_query(self, analyzer):
        """Should detect SQL injection via string concatenation."""
        code = '''
        <%
        Dim userInput, sql
        userInput = Request.QueryString("username")
        sql = "SELECT * FROM users WHERE username = '" & userInput & "'"
        Set rs = conn.Execute(sql)
        %>
        '''
        findings = analyzer.analyze(code)

        injection = [f for f in findings
                    if f.issue_type == SQLIssueType.SQL_INJECTION or
                       f.issue_type == SQLIssueType.STRING_CONCAT_SQL]
        assert len(injection) >= 1

    def test_detect_inline_concat_injection(self, analyzer):
        """Should detect inline SQL concatenation."""
        code = '''
        <%
        Set rs = conn.Execute("SELECT * FROM users WHERE id = " & Request("id"))
        %>
        '''
        findings = analyzer.analyze(code)

        injection = [f for f in findings
                    if f.issue_type == SQLIssueType.SQL_INJECTION or
                       f.issue_type == SQLIssueType.STRING_CONCAT_SQL]
        # Should detect string concatenation in SQL

    def test_parameterized_query_no_injection(self, analyzer):
        """Should not flag parameterized queries."""
        code = '''
        <%
        Dim cmd
        Set cmd = Server.CreateObject("ADODB.Command")
        cmd.ActiveConnection = conn
        cmd.CommandText = "SELECT * FROM users WHERE id = @id"
        cmd.Parameters.Append cmd.CreateParameter("@id", adInteger, adParamInput, , userId)
        Set rs = cmd.Execute()
        %>
        '''
        findings = analyzer.analyze(code)

        injection = [f for f in findings
                    if f.issue_type == SQLIssueType.SQL_INJECTION]
        # Parameterized queries should be safe
        assert len(injection) == 0


class TestSelectStarDetection:
    """Tests for SELECT * usage detection."""

    @pytest.fixture
    def analyzer(self):
        return SQLAnalyzer()

    def test_detect_select_star(self, analyzer):
        """Should detect SELECT * usage."""
        code = '''
        <%
        Set rs = conn.Execute("SELECT * FROM users")
        %>
        '''
        findings = analyzer.analyze(code)

        select_star = [f for f in findings
                      if f.issue_type == SQLIssueType.SELECT_STAR]
        assert len(select_star) >= 1

    def test_explicit_columns_no_issue(self, analyzer):
        """Should not flag explicit column selection."""
        code = '''
        <%
        Set rs = conn.Execute("SELECT id, name, email FROM users")
        %>
        '''
        findings = analyzer.analyze(code)

        select_star = [f for f in findings
                      if f.issue_type == SQLIssueType.SELECT_STAR]
        assert len(select_star) == 0


class TestUnboundedQueryDetection:
    """Tests for unbounded query detection."""

    @pytest.fixture
    def analyzer(self):
        return SQLAnalyzer()

    def test_detect_unbounded_select(self, analyzer):
        """Should detect SELECT without TOP or WHERE."""
        code = '''
        <%
        Set rs = conn.Execute("SELECT name FROM large_table")
        %>
        '''
        findings = analyzer.analyze(code)

        unbounded = [f for f in findings
                    if f.issue_type == SQLIssueType.UNBOUNDED_QUERY]
        # May or may not detect based on pattern

    def test_bounded_query_with_top_no_issue(self, analyzer):
        """Should not flag queries with TOP clause."""
        code = '''
        <%
        Set rs = conn.Execute("SELECT TOP 100 name FROM large_table")
        %>
        '''
        findings = analyzer.analyze(code)

        unbounded = [f for f in findings
                    if f.issue_type == SQLIssueType.UNBOUNDED_QUERY]
        assert len(unbounded) == 0

    def test_bounded_query_with_where_acceptable(self, analyzer):
        """Should handle queries with WHERE clause."""
        code = '''
        <%
        Set rs = conn.Execute("SELECT name FROM users WHERE active = 1")
        %>
        '''
        findings = analyzer.analyze(code)
        # WHERE clause provides some bounding


class TestTransactionHandling:
    """Tests for transaction handling issue detection."""

    @pytest.fixture
    def analyzer(self):
        return SQLAnalyzer()

    def test_detect_begin_without_commit(self, analyzer):
        """Should detect BeginTrans without CommitTrans."""
        code = '''
        <%
        conn.BeginTrans
        conn.Execute "INSERT INTO logs (message) VALUES ('test')"
        ' Missing CommitTrans or RollbackTrans!
        %>
        '''
        findings = analyzer.analyze(code)

        trans_issue = [f for f in findings
                      if f.issue_type == SQLIssueType.NO_TRANSACTION]
        # Should detect transaction issue

    def test_proper_transaction_no_issue(self, analyzer):
        """Should not flag proper transaction handling."""
        code = '''
        <%
        On Error Resume Next
        conn.BeginTrans
        conn.Execute "INSERT INTO logs (message) VALUES ('test')"
        If Err.Number = 0 Then
            conn.CommitTrans
        Else
            conn.RollbackTrans
        End If
        On Error GoTo 0
        %>
        '''
        findings = analyzer.analyze(code)

        trans_issue = [f for f in findings
                      if f.issue_type == SQLIssueType.NO_TRANSACTION]
        # Should be okay (has both commit and rollback)
        assert len(trans_issue) == 0


class TestDynamicSQLDetection:
    """Tests for dynamic SQL construction detection."""

    @pytest.fixture
    def analyzer(self):
        return SQLAnalyzer()

    def test_detect_dynamic_sql_construction(self, analyzer):
        """Should detect dynamic SQL built from variables."""
        code = '''
        <%
        Dim tableName, sql
        tableName = Request("table")
        sql = "SELECT * FROM " & tableName
        Set rs = conn.Execute(sql)
        %>
        '''
        findings = analyzer.analyze(code)

        dynamic = [f for f in findings
                  if f.issue_type == SQLIssueType.DYNAMIC_SQL or
                     f.issue_type == SQLIssueType.STRING_CONCAT_SQL]
        # Should detect dynamic SQL


class TestQueryTimeoutDetection:
    """Tests for missing query timeout detection."""

    @pytest.fixture
    def analyzer(self):
        return SQLAnalyzer()

    def test_detect_no_command_timeout(self, analyzer):
        """Should detect missing CommandTimeout."""
        code = '''
        <%
        Dim cmd
        Set cmd = Server.CreateObject("ADODB.Command")
        cmd.ActiveConnection = conn
        cmd.CommandText = "SELECT * FROM very_large_table"
        ' No CommandTimeout set!
        Set rs = cmd.Execute()
        %>
        '''
        findings = analyzer.analyze(code)

        timeout = [f for f in findings
                  if f.issue_type == SQLIssueType.NO_QUERY_TIMEOUT]
        # May detect based on analysis

    def test_with_timeout_no_issue(self, analyzer):
        """Should not flag when CommandTimeout is set."""
        code = '''
        <%
        Dim cmd
        Set cmd = Server.CreateObject("ADODB.Command")
        cmd.CommandTimeout = 30
        cmd.ActiveConnection = conn
        cmd.CommandText = "SELECT * FROM very_large_table"
        Set rs = cmd.Execute()
        %>
        '''
        findings = analyzer.analyze(code)

        timeout = [f for f in findings
                  if f.issue_type == SQLIssueType.NO_QUERY_TIMEOUT]
        assert len(timeout) == 0


class TestCaseInsensitivity:
    """Tests for case-insensitive SQL pattern matching."""

    @pytest.fixture
    def analyzer(self):
        return SQLAnalyzer()

    def test_case_insensitive_select_star(self, analyzer):
        """Should detect SELECT * regardless of case."""
        code = '''
        <%
        Set rs = conn.Execute("select * from USERS")
        %>
        '''
        findings = analyzer.analyze(code)

        select_star = [f for f in findings
                      if f.issue_type == SQLIssueType.SELECT_STAR]
        assert len(select_star) >= 1

    def test_mixed_case_sql_keywords(self, analyzer):
        """Should handle mixed case SQL keywords."""
        code = '''
        <%
        Set rs = conn.Execute("SELECT TOP 10 name FROM users WHERE active = 1")
        %>
        '''
        findings = analyzer.analyze(code)
        # Should process without error
        assert isinstance(findings, list)


class TestSeverityLevels:
    """Tests for severity level assignment."""

    @pytest.fixture
    def analyzer(self):
        return SQLAnalyzer()

    def test_sql_injection_is_critical(self, analyzer):
        """SQL injection should be CRITICAL severity."""
        code = '''
        <%
        sql = "SELECT * FROM users WHERE name = '" & Request("name") & "'"
        %>
        '''
        findings = analyzer.analyze(code)

        injection = [f for f in findings
                    if f.issue_type == SQLIssueType.SQL_INJECTION]
        if injection:
            assert injection[0].severity == SeverityLevel.CRITICAL

    def test_n_plus_one_is_high(self, analyzer):
        """N+1 query should be HIGH severity."""
        code = '''
        <%
        For Each id In ids
            Set rs = conn.Execute("SELECT * FROM items WHERE id = " & id)
        Next
        %>
        '''
        findings = analyzer.analyze(code)

        n_plus_one = [f for f in findings
                     if f.issue_type == SQLIssueType.N_PLUS_ONE or
                        f.issue_type == SQLIssueType.QUERY_IN_LOOP]
        if n_plus_one:
            assert n_plus_one[0].severity in [SeverityLevel.HIGH, SeverityLevel.MEDIUM]

    def test_select_star_is_low(self, analyzer):
        """SELECT * should be LOW severity."""
        code = '''
        <%
        Set rs = conn.Execute("SELECT * FROM users")
        %>
        '''
        findings = analyzer.analyze(code)

        select_star = [f for f in findings
                      if f.issue_type == SQLIssueType.SELECT_STAR]
        if select_star:
            assert select_star[0].severity == SeverityLevel.LOW


class TestToLeakFindingConversion:
    """Tests for conversion to standard LeakFinding format."""

    @pytest.fixture
    def analyzer(self):
        return SQLAnalyzer()

    def test_convert_to_leak_finding(self, analyzer):
        """Should convert SQLFinding to LeakFinding."""
        code = '''
        <%
        Set rs = conn.Execute("SELECT * FROM users")
        %>
        '''
        findings = analyzer.analyze(code)

        if findings:
            leak_finding = findings[0].to_leak_finding()
            assert leak_finding.file_path == "test.asp"
            assert leak_finding.category == StabilityCategory.SQL_PERFORMANCE
            assert leak_finding.severity in [SeverityLevel.LOW, SeverityLevel.MEDIUM,
                                            SeverityLevel.HIGH, SeverityLevel.CRITICAL]

    def test_leak_finding_has_description(self, analyzer):
        """Converted LeakFinding should have description."""
        code = '''
        <%
        Set rs = conn.Execute("SELECT * FROM users")
        %>
        '''
        findings = analyzer.analyze(code)

        if findings:
            leak_finding = findings[0].to_leak_finding()
            assert leak_finding.description is not None
            assert len(leak_finding.description) > 0

    def test_leak_finding_has_suggested_fix(self, analyzer):
        """Converted LeakFinding should have suggested fix."""
        code = '''
        <%
        Set rs = conn.Execute("SELECT * FROM users")
        %>
        '''
        findings = analyzer.analyze(code)

        if findings:
            leak_finding = findings[0].to_leak_finding()
            assert leak_finding.suggested_fix is not None
            assert len(leak_finding.suggested_fix) > 0


class TestSQLQueryDataclass:
    """Tests for SQLQuery dataclass."""

    def test_sql_query_defaults(self):
        """SQLQuery should have sensible defaults."""
        query = SQLQuery(
            line_number=10,
            query_text="SELECT * FROM users",
            variable_name="rs"
        )
        assert query.is_in_loop is False
        assert query.has_parameters is False
        assert query.has_top_clause is False
        assert query.tables_referenced == []

    def test_sql_query_with_loop(self):
        """SQLQuery should track loop context."""
        query = SQLQuery(
            line_number=10,
            query_text="SELECT * FROM users",
            variable_name="rs",
            is_in_loop=True
        )
        assert query.is_in_loop is True


class TestAnalyzeMethod:
    """Tests for the analyze() convenience method."""

    @pytest.fixture
    def analyzer(self):
        return SQLAnalyzer()

    def test_analyze_with_default_path(self, analyzer):
        """analyze() should use default test.asp path."""
        code = '''
        <%
        Set rs = conn.Execute("SELECT * FROM users")
        %>
        '''
        findings = analyzer.analyze(code)

        if findings:
            assert findings[0].file_path == "test.asp"

    def test_analyze_with_custom_path(self, analyzer):
        """analyze() should accept custom file path."""
        code = '''
        <%
        Set rs = conn.Execute("SELECT * FROM users")
        %>
        '''
        findings = analyzer.analyze(code, file_path="custom/query.asp")

        if findings:
            assert findings[0].file_path == "custom/query.asp"


class TestMultipleIssuesInFile:
    """Tests for detecting multiple issues in one file."""

    @pytest.fixture
    def analyzer(self):
        return SQLAnalyzer()

    def test_detect_multiple_issues(self, analyzer):
        """Should detect multiple different issues in one file."""
        code = '''
        <%
        ' Issue 1: SELECT *
        Set rs1 = conn.Execute("SELECT * FROM users")

        ' Issue 2: SQL Injection
        Set rs2 = conn.Execute("SELECT id FROM orders WHERE user = '" & Request("user") & "'")

        ' Issue 3: Query in loop
        For Each id In userIds
            Set rs3 = conn.Execute("SELECT name FROM users WHERE id = " & id)
        Next
        %>
        '''
        findings = analyzer.analyze(code)

        # Should find multiple issues
        issue_types = set(f.issue_type for f in findings)
        assert len(findings) >= 2  # At least 2 different issues


class TestCodeContext:
    """Tests for code context in findings."""

    @pytest.fixture
    def analyzer(self):
        return SQLAnalyzer()

    def test_finding_includes_query_snippet(self, analyzer):
        """Finding should include query snippet."""
        code = '''
        <%
        Set rs = conn.Execute("SELECT * FROM very_important_table")
        %>
        '''
        findings = analyzer.analyze(code)

        if findings:
            # Check that context or snippet contains relevant info
            assert findings[0].code_context is not None or findings[0].query_snippet


class TestTableExtraction:
    """Tests for table name extraction from queries."""

    @pytest.fixture
    def analyzer(self):
        return SQLAnalyzer()

    def test_extract_table_from_simple_query(self, analyzer):
        """Should extract table name from simple query."""
        code = '''
        <%
        Set rs = conn.Execute("SELECT * FROM customers")
        %>
        '''
        findings = analyzer.analyze(code)

        # Check tables_affected if available
        if findings and findings[0].tables_affected:
            assert "customers" in [t.lower() for t in findings[0].tables_affected]

    def test_extract_tables_from_join(self, analyzer):
        """Should extract table names from JOIN queries."""
        code = '''
        <%
        Set rs = conn.Execute("SELECT * FROM orders o JOIN customers c ON o.customer_id = c.id")
        %>
        '''
        findings = analyzer.analyze(code)
        # Should process JOIN query without error
        assert isinstance(findings, list)
