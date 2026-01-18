"""
Tests for Fase 41 InjectionDetector.

Tests cover injection vulnerability detection rules:
- XSS (CWE-79): Cross-site Scripting
- SQLi (CWE-89): SQL Injection
- CMDi (CWE-78/77): Command Injection
- Path Traversal (CWE-22)
- Deserialization (CWE-502)
- SSRF (CWE-918)
- Code Injection (CWE-94)
- XXE (CWE-611)
- SSTI (CWE-1336)
- LDAP Injection (CWE-90)
- NoSQL Injection (CWE-943)
- CSRF (CWE-352)
- File Upload (CWE-434)
"""

import pytest
from pathlib import Path

from app.services.security_scanner.adapters.injection_detector import (
    InjectionDetector,
    InjectionRule,
    ALL_INJECTION_RULES,
    XSS_RULES,
    SQL_INJECTION_RULES,
    COMMAND_INJECTION_RULES,
    PATH_TRAVERSAL_RULES,
    DESERIALIZATION_RULES,
    SSRF_RULES,
    CODE_INJECTION_RULES,
    XXE_RULES,
    SSTI_RULES,
    LDAP_INJECTION_RULES,
    NOSQL_INJECTION_RULES,
    CSRF_RULES,
    FILE_UPLOAD_RULES,
    create_injection_detector,
)
from app.services.security_scanner.models.findings import (
    ScannerType,
    Severity,
)


# =============================================================================
# SCANNER BASICS
# =============================================================================


class TestInjectionDetectorBasics:
    """Tests for basic scanner properties."""

    def test_scanner_type(self):
        """Should return correct scanner type."""
        scanner = InjectionDetector()
        assert scanner.scanner_type == ScannerType.INJECTION

    def test_is_always_available(self):
        """Custom scanner should always be available."""
        scanner = InjectionDetector()
        assert scanner.is_available() is True

    def test_scanner_version(self):
        """Should return version string."""
        scanner = InjectionDetector()
        assert scanner.get_scanner_version() == "1.0.0"

    def test_has_expected_rules(self):
        """Should have expected number of injection detection rules."""
        # Total rules across all categories
        assert len(ALL_INJECTION_RULES) >= 60  # Plenty of rules

    def test_supported_languages(self):
        """Should support expected languages."""
        scanner = InjectionDetector()
        languages = scanner.supported_languages
        assert "javascript" in languages
        assert "typescript" in languages
        assert "python" in languages
        assert "java" in languages
        assert "csharp" in languages
        assert "php" in languages
        assert "ruby" in languages
        assert "go" in languages

    def test_supported_extensions(self):
        """Should support expected file extensions."""
        scanner = InjectionDetector()
        extensions = scanner.supported_extensions
        assert ".js" in extensions
        assert ".ts" in extensions
        assert ".py" in extensions
        assert ".java" in extensions
        assert ".cs" in extensions
        assert ".php" in extensions
        assert ".rb" in extensions
        assert ".go" in extensions

    def test_factory_function(self):
        """Factory function should create scanner instance."""
        scanner = create_injection_detector()
        assert isinstance(scanner, InjectionDetector)

    def test_rules_have_cwe_ids(self):
        """All rules should have CWE IDs."""
        for rule in ALL_INJECTION_RULES:
            assert len(rule.cwe_ids) > 0, f"Rule {rule.id} has no CWE IDs"

    def test_rules_have_fix_suggestions(self):
        """All rules should have fix suggestions."""
        for rule in ALL_INJECTION_RULES:
            assert rule.fix_suggestion, f"Rule {rule.id} has no fix suggestion"

    def test_covers_target_cwes(self):
        """Should cover the target CWEs for Fase 41."""
        cwe_coverage = set()
        for rule in ALL_INJECTION_RULES:
            cwe_coverage.update(rule.cwe_ids)

        # Core injection CWEs
        assert "CWE-79" in cwe_coverage, "CWE-79 (XSS) not covered"
        assert "CWE-89" in cwe_coverage, "CWE-89 (SQL Injection) not covered"
        assert "CWE-78" in cwe_coverage, "CWE-78 (OS Command Injection) not covered"
        assert "CWE-22" in cwe_coverage, "CWE-22 (Path Traversal) not covered"
        assert "CWE-502" in cwe_coverage, "CWE-502 (Deserialization) not covered"
        assert "CWE-918" in cwe_coverage, "CWE-918 (SSRF) not covered"
        assert "CWE-94" in cwe_coverage, "CWE-94 (Code Injection) not covered"
        assert "CWE-611" in cwe_coverage, "CWE-611 (XXE) not covered"
        assert "CWE-90" in cwe_coverage, "CWE-90 (LDAP Injection) not covered"


# =============================================================================
# XSS (CWE-79)
# =============================================================================


class TestXSSDetection:
    """Tests for XSS detection rules."""

    @pytest.mark.asyncio
    async def test_detect_innerhtml_js(self, tmp_path):
        """Should detect innerHTML assignment with user input."""
        test_file = tmp_path / "xss.js"
        test_file.write_text('''
function render(userInput) {
    document.getElementById("output").innerHTML = userInput;
}
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "XSS" in f.rule_id), None)
        assert finding is not None
        assert "CWE-79" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_document_write_js(self, tmp_path):
        """Should detect document.write with user input."""
        test_file = tmp_path / "xss.js"
        test_file.write_text('''
function display(req) {
    document.write(req.query.message);
}
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "INJ-XSS-003"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_echo_php(self, tmp_path):
        """Should detect PHP echo with unescaped user input."""
        test_file = tmp_path / "xss.php"
        test_file.write_text('''<?php
echo $_GET['name'];
print $_POST['message'];
?>''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "XSS" in f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_render_template_string_python(self, tmp_path):
        """Should detect render_template_string with user input."""
        test_file = tmp_path / "xss.py"
        test_file.write_text('''
from flask import render_template_string, request

@app.route('/preview')
def preview():
    return render_template_string(request.args.get('template'))
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1


# =============================================================================
# SQL INJECTION (CWE-89)
# =============================================================================


class TestSQLInjectionDetection:
    """Tests for SQL injection detection rules."""

    @pytest.mark.asyncio
    async def test_detect_sql_concatenation_python(self, tmp_path):
        """Should detect SQL query with string concatenation."""
        test_file = tmp_path / "sqli.py"
        test_file.write_text('''
def get_user(user_id):
    db.execute("SELECT * FROM users WHERE id = " + user_id)
    conn.execute("DELETE FROM users WHERE name = " + request.args.get('name'))
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "SQL" in f.rule_id), None)
        assert finding is not None
        assert "CWE-89" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_sql_fstring_python(self, tmp_path):
        """Should detect SQL query with f-string interpolation."""
        test_file = tmp_path / "sqli.py"
        test_file.write_text('''
def search(query):
    cursor.execute(f"SELECT * FROM products WHERE name LIKE '%{query}%'")
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "INJ-SQL-002"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_sql_template_literal_js(self, tmp_path):
        """Should detect SQL query with template literal."""
        test_file = tmp_path / "sqli.js"
        test_file.write_text('''
async function getUser(req) {
    const result = await db.query(`SELECT * FROM users WHERE id = ${req.params.id}`);
    return result;
}
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "SQL" in f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_sql_statement_java(self, tmp_path):
        """Should detect SQL with Statement instead of PreparedStatement."""
        test_file = tmp_path / "SQLi.java"
        test_file.write_text('''
public class UserDAO {
    public User getUser(String id) {
        Statement stmt = conn.createStatement(); stmt.executeQuery("SELECT * FROM users WHERE id=" + id);
    }
}
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "SQL" in f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_sql_go_sprintf(self, tmp_path):
        """Should detect SQL with fmt.Sprintf in Go."""
        test_file = tmp_path / "sqli.go"
        test_file.write_text('''
func getUser(id string) {
    query := fmt.Sprintf("SELECT * FROM users WHERE id = '%s'", id)
    db.Query(fmt.Sprintf("SELECT * FROM users WHERE name = '%s'", name))
}
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1


# =============================================================================
# COMMAND INJECTION (CWE-78)
# =============================================================================


class TestCommandInjectionDetection:
    """Tests for command injection detection rules."""

    @pytest.mark.asyncio
    async def test_detect_os_system_python(self, tmp_path):
        """Should detect os.system with user input."""
        test_file = tmp_path / "cmdi.py"
        test_file.write_text('''
import os

def ping(host):
    os.system(f"ping -c 1 {host}")
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "CMD" in f.rule_id), None)
        assert finding is not None
        assert "CWE-78" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_shell_exec_php(self, tmp_path):
        """Should detect shell_exec with user input in PHP."""
        test_file = tmp_path / "cmdi.php"
        test_file.write_text('''<?php
$output = shell_exec("ls " . $_GET['dir']);
system("ping " . $_POST['host']);
exec("cat " . $_REQUEST['file']);
?>''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_detect_exec_js(self, tmp_path):
        """Should detect child_process.exec with user input."""
        test_file = tmp_path / "cmdi.js"
        test_file.write_text('''
const { exec } = require('child_process');

function runCommand(req) {
    exec(`ls ${req.query.dir}`, (err, stdout) => {
        console.log(stdout);
    });
}
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "CMD" in f.rule_id), None)
        assert finding is not None


# =============================================================================
# PATH TRAVERSAL (CWE-22)
# =============================================================================


class TestPathTraversalDetection:
    """Tests for path traversal detection rules."""

    @pytest.mark.asyncio
    async def test_detect_file_open_python(self, tmp_path):
        """Should detect file open with user-controlled path."""
        test_file = tmp_path / "path.py"
        test_file.write_text('''
def read_file(request):
    filename = request.args.get('file')
    with open(f"/uploads/{filename}") as f:
        return f.read()
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "PATH" in f.rule_id), None)
        assert finding is not None
        assert "CWE-22" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_fs_readfile_js(self, tmp_path):
        """Should detect fs.readFile with user input."""
        test_file = tmp_path / "path.js"
        test_file.write_text('''
const fs = require('fs');

app.get('/download', (req, res) => {
    fs.readFile(req.query.path, (err, data) => {
        res.send(data);
    });
});
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1


# =============================================================================
# DESERIALIZATION (CWE-502)
# =============================================================================


class TestDeserializationDetection:
    """Tests for deserialization vulnerability detection."""

    @pytest.mark.asyncio
    async def test_detect_pickle_python(self, tmp_path):
        """Should detect pickle.loads with untrusted data."""
        test_file = tmp_path / "deser.py"
        test_file.write_text('''
import pickle

def load_data(data):
    return pickle.loads(data)  # Dangerous with untrusted data
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "DESER" in f.rule_id), None)
        assert finding is not None
        assert "CWE-502" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_yaml_load_python(self, tmp_path):
        """Should detect yaml.load without SafeLoader."""
        test_file = tmp_path / "deser.py"
        test_file.write_text('''
import yaml

def parse_config(request):
    config = yaml.load(request.data)
    return config
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_detect_unserialize_php(self, tmp_path):
        """Should detect PHP unserialize with user input."""
        test_file = tmp_path / "deser.php"
        test_file.write_text('''<?php
$data = unserialize($_POST['data']);
?>''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1


# =============================================================================
# SSRF (CWE-918)
# =============================================================================


class TestSSRFDetection:
    """Tests for SSRF detection rules."""

    @pytest.mark.asyncio
    async def test_detect_requests_python(self, tmp_path):
        """Should detect requests.get with user-controlled URL."""
        test_file = tmp_path / "ssrf.py"
        test_file.write_text('''
import requests

def fetch(url):
    response = requests.get(url)
    return response.text
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "SSRF" in f.rule_id), None)
        assert finding is not None
        assert "CWE-918" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_fetch_js(self, tmp_path):
        """Should detect fetch with user-controlled URL."""
        test_file = tmp_path / "ssrf.js"
        test_file.write_text('''
async function proxy(req) {
    const response = await fetch(req.body.url);
    return response.json();
}
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1


# =============================================================================
# CODE INJECTION (CWE-94)
# =============================================================================


class TestCodeInjectionDetection:
    """Tests for code injection detection rules."""

    @pytest.mark.asyncio
    async def test_detect_eval_python(self, tmp_path):
        """Should detect eval with user input."""
        test_file = tmp_path / "code.py"
        test_file.write_text('''
def calculate(request):
    return eval(request.args.get('expr'))
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "CODE" in f.rule_id), None)
        assert finding is not None
        assert "CWE-94" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_eval_js(self, tmp_path):
        """Should detect JavaScript eval with user input."""
        test_file = tmp_path / "code.js"
        test_file.write_text('''
function calculate(req) {
    return eval(req.body.expression);
}
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_detect_new_function_js(self, tmp_path):
        """Should detect new Function with user input."""
        test_file = tmp_path / "code.js"
        test_file.write_text('''
function createHandler(req) {
    const handler = new Function(req.body.code);
    return handler();
}
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1


# =============================================================================
# XXE (CWE-611)
# =============================================================================


class TestXXEDetection:
    """Tests for XXE detection rules."""

    @pytest.mark.asyncio
    async def test_detect_xml_parse_python(self, tmp_path):
        """Should detect XML parsing without XXE protection."""
        test_file = tmp_path / "xxe.py"
        test_file.write_text('''
from xml.etree import ElementTree

def parse_xml(request):
    tree = ElementTree.parse(request.files['xml'])
    return tree.getroot()
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_detect_documentbuilder_java(self, tmp_path):
        """Should detect DocumentBuilder without XXE protection."""
        test_file = tmp_path / "XXE.java"
        test_file.write_text('''
import javax.xml.parsers.DocumentBuilderFactory;

public class XMLParser {
    public void parse(InputStream input) {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        DocumentBuilder builder = factory.newDocumentBuilder();
        Document doc = builder.parse(input);
    }
}
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1


# =============================================================================
# MULTI-LANGUAGE TESTS
# =============================================================================


class TestMultiLanguageSupport:
    """Tests for multi-language support."""

    @pytest.mark.asyncio
    async def test_scan_multiple_languages(self, tmp_path):
        """Should scan multiple language files correctly."""
        # Python SQLi
        (tmp_path / "app.py").write_text('cursor.execute("SELECT * FROM users WHERE id = " + user_id)')
        # JavaScript XSS
        (tmp_path / "app.js").write_text('document.innerHTML = userInput;')
        # PHP CMDi
        (tmp_path / "app.php").write_text('<?php shell_exec("ls " . $_GET["dir"]); ?>')
        # Ignored file
        (tmp_path / "readme.txt").write_text('SELECT * FROM users')

        scanner = InjectionDetector()
        result = await scanner.scan(tmp_path)

        assert result.files_scanned == 3  # Only code files
        assert len(result.findings) >= 2


# =============================================================================
# EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and false positive handling."""

    @pytest.mark.asyncio
    async def test_safe_parameterized_query(self, tmp_path):
        """Should not flag safe parameterized queries."""
        test_file = tmp_path / "safe.py"
        test_file.write_text('''
def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
''')

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        # Should not flag parameterized queries
        sql_findings = [f for f in result.findings if "SQL" in f.rule_id]
        assert len(sql_findings) == 0

    @pytest.mark.asyncio
    async def test_empty_file(self, tmp_path):
        """Should handle empty files gracefully."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")

        scanner = InjectionDetector()
        result = await scanner.scan(test_file)

        assert result.files_scanned == 1
        assert len(result.findings) == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_get_rules_summary(self):
        """Should return correct rules summary."""
        scanner = InjectionDetector()
        summary = scanner.get_rules_summary()

        assert summary["total_rules"] >= 60
        assert len(summary["rules"]) >= 60
        assert "CWE-79" in summary["cwe_coverage"]
        assert "CWE-89" in summary["cwe_coverage"]
        assert "CWE-78" in summary["cwe_coverage"]
