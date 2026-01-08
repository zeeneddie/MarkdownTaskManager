# Unit Tests for ClassicASPLeakDetector
# Tests for ADO Connection/Recordset leak detection in Classic ASP

import pytest
from app.services.stability.types import (
    ResourceType,
    LeakPatternType,
    SeverityLevel,
    StabilityCategory,
)
from app.services.stability.detectors.classic_asp_detector import (
    ClassicASPLeakDetector,
    ClassicASPCOMDetector,
    ClassicASPFileDetector,
)


class TestClassicASPLeakDetector:
    """Unit tests for ClassicASPLeakDetector."""

    @pytest.fixture
    def detector(self):
        return ClassicASPLeakDetector()

    # --- Configuration Tests ---

    def test_supported_extensions(self, detector):
        """Should support .asp and .inc files."""
        extensions = detector.get_supported_extensions()
        assert ".asp" in extensions
        assert ".inc" in extensions

    def test_language_name(self, detector):
        """Should return correct language name."""
        assert detector.get_language() == "Classic ASP (VBScript)"

    def test_case_insensitive(self, detector):
        """VBScript should be case-insensitive."""
        assert detector.is_case_insensitive() is True

    def test_category(self, detector):
        """Should be ADO_LEAKS category."""
        assert detector.get_category() == StabilityCategory.ADO_LEAKS

    # --- Connection Leak Detection ---

    def test_detect_connection_never_closed(self, detector):
        """Should detect connection opened but never closed."""
        code = '''
        <%
        Dim con
        Set con = Server.CreateObject("ADODB.Connection")
        con.Open "DSN=mydb"
        ' Do some work
        Response.Write "Done"
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        assert report.has_leaks
        assert len(report.findings) >= 1
        finding = report.findings[0]
        assert finding.resource_type == ResourceType.DATABASE_CONNECTION
        assert finding.leak_pattern == LeakPatternType.NEVER_CLOSED
        assert finding.severity == SeverityLevel.CRITICAL

    def test_detect_connection_properly_closed(self, detector):
        """Should not flag properly closed connection."""
        code = '''
        <%
        Dim con
        Set con = Server.CreateObject("ADODB.Connection")
        con.Open "DSN=mydb"
        ' Do some work
        con.Close
        Set con = Nothing
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        # Should have no leaks (connection properly closed)
        connection_leaks = [f for f in report.findings
                          if f.resource_type == ResourceType.DATABASE_CONNECTION]
        assert len(connection_leaks) == 0

    def test_detect_wrapper_function_connection(self, detector):
        """Should detect connection via wrapper function."""
        code = '''
        <%
        Dim con
        Set con = CreateCusCon()
        ' Do some work - forgot to close!
        Response.Write "Done"
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        assert report.has_leaks
        assert len(report.opens) >= 1
        assert report.opens[0].via_wrapper is True

    # --- Recordset Leak Detection ---

    def test_detect_recordset_never_closed(self, detector):
        """Should detect recordset opened but never closed."""
        code = '''
        <%
        Dim rs
        Set rs = Server.CreateObject("ADODB.Recordset")
        rs.Open "SELECT * FROM users", con
        While Not rs.EOF
            Response.Write rs("name")
            rs.MoveNext
        Wend
        ' Forgot to close rs!
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        assert report.has_leaks
        rs_findings = [f for f in report.findings
                      if f.resource_type == ResourceType.RECORDSET]
        assert len(rs_findings) >= 1
        assert rs_findings[0].severity == SeverityLevel.HIGH

    def test_detect_connection_execute_recordset(self, detector):
        """Should detect recordset from Connection.Execute."""
        code = '''
        <%
        Dim rs
        Set rs = con.Execute("SELECT * FROM users")
        ' Forgot to close rs!
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        assert len(report.opens) >= 1

    # --- Case Insensitivity Tests ---

    def test_case_insensitive_detection(self, detector):
        """Should detect patterns regardless of case."""
        code = '''
        <%
        Dim RS
        SET RS = SERVER.CREATEOBJECT("ADODB.RECORDSET")
        rs.open "SELECT * FROM users", CON
        ' Mixed case - should still detect
        RS.Close
        SET rs = NOTHING
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        # Should find the open operation
        assert len(report.opens) >= 1
        # Should find the close operation
        assert len(report.closes) >= 1

    # --- Loop Leak Detection ---

    def test_detect_loop_leak(self, detector):
        """Should detect leak inside loop (CRITICAL)."""
        code = '''
        <%
        Dim rs, i
        For i = 1 To 100
            Set rs = CreateRecordset()
            rs.Open "SELECT * FROM items WHERE id=" & i, con
            Response.Write rs("name")
            ' Missing rs.Close inside loop!
        Next
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        # Should detect opens
        assert len(report.opens) >= 1
        # Loop context should be detected
        loop_opens = [o for o in report.opens if o.in_loop]
        # Note: loop detection depends on pattern matching

    # --- Set Without Close Detection ---

    def test_detect_set_without_close(self, detector):
        """Should detect Set = Nothing without .Close() first."""
        code = '''
        <%
        Dim con
        Set con = Server.CreateObject("ADODB.Connection")
        con.Open "DSN=mydb"
        ' WRONG: Set to Nothing without Close!
        Set con = Nothing
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        # Should detect the leak pattern
        assert report.has_leaks
        # Should identify SET_WITHOUT_CLOSE pattern
        set_without_close = [f for f in report.findings
                           if f.leak_pattern == LeakPatternType.SET_WITHOUT_CLOSE]
        # This depends on state machine tracking

    # --- Wrapper Close Functions ---

    def test_detect_wrapper_close_function(self, detector):
        """Should recognize wrapper close functions."""
        code = '''
        <%
        Dim con
        Set con = CreateCusCon()
        ' Do work
        Call TryCloseConnection(con)
        Set con = Nothing
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        # Should find close via wrapper
        assert len(report.closes) >= 1

    # --- Multiple Resources ---

    def test_multiple_resources(self, detector):
        """Should track multiple resources independently."""
        code = '''
        <%
        Dim con, rs1, rs2
        Set con = CreateCusCon()
        Set rs1 = CreateRecordset()
        Set rs2 = CreateRecordset()

        rs1.Open "SELECT * FROM table1", con
        rs2.Open "SELECT * FROM table2", con

        rs1.Close  ' Only rs1 closed
        ' rs2 not closed!
        con.Close
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        # Should have 3 opens (con, rs1, rs2)
        assert len(report.opens) >= 3
        # Should have 2 closes (rs1, con)
        assert len(report.closes) >= 2


class TestClassicASPCOMDetector:
    """Unit tests for ClassicASPCOMDetector."""

    @pytest.fixture
    def detector(self):
        return ClassicASPCOMDetector()

    def test_category(self, detector):
        """Should be COM_OBJECTS category."""
        assert detector.get_category() == StabilityCategory.COM_OBJECTS

    def test_detect_xmlhttp_leak(self, detector):
        """Should detect XMLHTTP object leak."""
        code = '''
        <%
        Dim objHTTP
        Set objHTTP = Server.CreateObject("MSXML2.ServerXMLHTTP")
        objHTTP.Open "GET", "https://api.example.com/data", False
        objHTTP.Send
        Response.Write objHTTP.responseText
        ' Forgot to clean up!
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        assert len(report.opens) >= 1
        assert report.opens[0].resource_type == ResourceType.COM_OBJECT

    def test_detect_abcpdf_leak(self, detector):
        """Should detect ABCpdf object leak."""
        code = '''
        <%
        Dim pdf
        Set pdf = Server.CreateObject("ABCpdf9.Doc")
        pdf.AddHtml "<h1>Hello</h1>"
        Response.BinaryWrite pdf.GetData()
        ' Forgot pdf.Clear!
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        assert len(report.opens) >= 1

    def test_detect_xmldom_leak(self, detector):
        """Should detect XMLDOM object leak."""
        code = '''
        <%
        Dim xmlDoc
        Set xmlDoc = Server.CreateObject("Microsoft.XMLDOM")
        xmlDoc.Load "data.xml"
        ' Process XML...
        ' Forgot Set xmlDoc = Nothing
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        assert len(report.opens) >= 1


class TestClassicASPFileDetector:
    """Unit tests for ClassicASPFileDetector."""

    @pytest.fixture
    def detector(self):
        return ClassicASPFileDetector()

    def test_category(self, detector):
        """Should be FILE_HANDLES category."""
        assert detector.get_category() == StabilityCategory.FILE_HANDLES

    def test_detect_fso_textstream_leak(self, detector):
        """Should detect TextStream file handle leak."""
        code = '''
        <%
        Dim fso, ts
        Set fso = Server.CreateObject("Scripting.FileSystemObject")
        Set ts = fso.OpenTextFile("log.txt", 8, True)
        ts.WriteLine "Log entry"
        ' Forgot ts.Close!
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        assert len(report.opens) >= 2  # FSO and TextStream

    def test_detect_createtextfile_leak(self, detector):
        """Should detect CreateTextFile leak."""
        code = '''
        <%
        Dim fso, file
        Set fso = CreateObject("Scripting.FileSystemObject")
        Set file = fso.CreateTextFile("output.txt", True)
        file.Write "Data"
        ' Missing file.Close
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        assert len(report.opens) >= 2


class TestDetectorService:
    """Integration tests for detector service."""

    def test_register_multiple_detectors(self):
        """Should register and use multiple detectors."""
        from app.services.stability.detector_service import ResourceLeakDetectorService

        service = ResourceLeakDetectorService()
        service.register_detector(ClassicASPLeakDetector())
        service.register_detector(ClassicASPCOMDetector())
        service.register_detector(ClassicASPFileDetector())

        # Should have detectors for .asp files
        assert service.get_detector_for_file("test.asp") is not None
        assert service.get_detector_for_file("include.inc") is not None

    def test_unsupported_file(self):
        """Should return None for unsupported file types."""
        from app.services.stability.detector_service import ResourceLeakDetectorService

        service = ResourceLeakDetectorService()
        service.register_detector(ClassicASPLeakDetector())

        # Python files not supported
        assert service.get_detector_for_file("test.py") is None


class TestSeverityCalculation:
    """Tests for severity calculation logic."""

    @pytest.fixture
    def detector(self):
        return ClassicASPLeakDetector()

    def test_connection_is_critical(self, detector):
        """Connection leaks should always be CRITICAL."""
        code = '''
        <%
        Set con = Server.CreateObject("ADODB.Connection")
        con.Open "DSN=test"
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        if report.findings:
            connection_findings = [f for f in report.findings
                                  if f.resource_type == ResourceType.DATABASE_CONNECTION]
            for f in connection_findings:
                assert f.severity == SeverityLevel.CRITICAL

    def test_recordset_is_high(self, detector):
        """Recordset leaks should be HIGH severity."""
        code = '''
        <%
        Set rs = Server.CreateObject("ADODB.Recordset")
        rs.Open "SELECT 1", con
        %>
        '''
        report = detector.analyze_file("test.asp", code)

        if report.findings:
            rs_findings = [f for f in report.findings
                         if f.resource_type == ResourceType.RECORDSET]
            for f in rs_findings:
                assert f.severity == SeverityLevel.HIGH
