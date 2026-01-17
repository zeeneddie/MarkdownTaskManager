"""
Tests for Fase 39 WebSecurityDetector.

Tests cover all 12 web security detection rules:
- WS001-WS004: Prototype Pollution (CWE-1321)
- WS010-WS013: CSV Injection (CWE-1236)
- WS020-WS023: Invalid Quantity (CWE-1284)
"""

import pytest
from pathlib import Path

from app.services.security_scanner.adapters.web_security_detector import (
    WebSecurityDetector,
    WebSecurityRule,
    WEB_SECURITY_RULES,
    create_web_security_detector,
)
from app.services.security_scanner.models.findings import (
    ScannerType,
    Severity,
)


# =============================================================================
# SCANNER BASICS
# =============================================================================


class TestWebSecurityDetectorBasics:
    """Tests for basic scanner properties."""

    def test_scanner_type(self):
        """Should return correct scanner type."""
        scanner = WebSecurityDetector()
        assert scanner.scanner_type == ScannerType.WEB_SECURITY

    def test_is_always_available(self):
        """Custom scanner should always be available."""
        scanner = WebSecurityDetector()
        assert scanner.is_available() is True

    def test_scanner_version(self):
        """Should return version string."""
        scanner = WebSecurityDetector()
        assert scanner.get_scanner_version() == "1.0.0"

    def test_has_12_rules(self):
        """Should have 12 web security detection rules."""
        assert len(WEB_SECURITY_RULES) == 12

    def test_supported_languages(self):
        """Should support expected languages."""
        scanner = WebSecurityDetector()
        languages = scanner.supported_languages
        assert "javascript" in languages
        assert "typescript" in languages
        assert "python" in languages
        assert "java" in languages
        assert "csharp" in languages
        assert "php" in languages
        assert "ruby" in languages

    def test_supported_extensions(self):
        """Should support expected file extensions."""
        scanner = WebSecurityDetector()
        extensions = scanner.supported_extensions
        assert ".js" in extensions
        assert ".ts" in extensions
        assert ".py" in extensions
        assert ".java" in extensions
        assert ".cs" in extensions
        assert ".php" in extensions
        assert ".rb" in extensions

    def test_factory_function(self):
        """Factory function should create scanner instance."""
        scanner = create_web_security_detector()
        assert isinstance(scanner, WebSecurityDetector)

    def test_rules_have_cwe_ids(self):
        """All rules should have CWE IDs."""
        for rule in WEB_SECURITY_RULES:
            assert len(rule.cwe_ids) > 0, f"Rule {rule.id} has no CWE IDs"

    def test_rules_have_fix_suggestions(self):
        """All rules should have fix suggestions."""
        for rule in WEB_SECURITY_RULES:
            assert rule.fix_suggestion, f"Rule {rule.id} has no fix suggestion"

    def test_covers_target_cwes(self):
        """Should cover the target CWEs for Fase 39."""
        cwe_coverage = set()
        for rule in WEB_SECURITY_RULES:
            cwe_coverage.update(rule.cwe_ids)

        assert "CWE-1321" in cwe_coverage, "CWE-1321 (Prototype Pollution) not covered"
        assert "CWE-1236" in cwe_coverage, "CWE-1236 (CSV Injection) not covered"
        assert "CWE-1284" in cwe_coverage, "CWE-1284 (Invalid Quantity) not covered"


# =============================================================================
# WS001-WS004: PROTOTYPE POLLUTION (CWE-1321)
# =============================================================================


class TestPrototypePollution:
    """Tests for prototype pollution detection."""

    @pytest.mark.asyncio
    async def test_detect_proto_assignment_js(self, tmp_path):
        """Should detect direct __proto__ assignment in JavaScript."""
        test_file = tmp_path / "proto.js"
        test_file.write_text('''
function vulnerable(userInput) {
    const obj = {};
    obj.__proto__ = userInput;
    return obj;
}
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        proto_finding = next((f for f in result.findings if f.rule_id == "WS001"), None)
        assert proto_finding is not None
        assert "CWE-1321" in proto_finding.cwe_ids
        assert proto_finding.severity == Severity.CRITICAL

    @pytest.mark.asyncio
    async def test_detect_proto_bracket_access_ts(self, tmp_path):
        """Should detect __proto__ bracket notation in TypeScript."""
        test_file = tmp_path / "proto.ts"
        test_file.write_text('''
function merge(target: any, source: any) {
    target.__proto__["polluted"] = true;
}
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "WS001"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_constructor_prototype_js(self, tmp_path):
        """Should detect constructor.prototype manipulation in JavaScript."""
        test_file = tmp_path / "constructor.js"
        test_file.write_text('''
function pollute(key, value) {
    const obj = {};
    obj.constructor.prototype[key] = value;
}
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "WS002"), None)
        assert finding is not None
        assert finding.severity == Severity.HIGH

    @pytest.mark.asyncio
    async def test_detect_object_assign_user_input_js(self, tmp_path):
        """Should detect Object.assign with user input in JavaScript."""
        test_file = tmp_path / "assign.js"
        test_file.write_text('''
app.post('/api/update', (req, res) => {
    const config = {};
    Object.assign(config, req.body);
    res.json(config);
});
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "WS003"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_bracket_access_user_input_ts(self, tmp_path):
        """Should detect dynamic property access with user input in TypeScript."""
        test_file = tmp_path / "bracket.ts"
        test_file.write_text('''
function setProperty(obj: any, value: any) {
    const key = req.body.field;
    obj[key] = value;
}
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "WS004"), None)
        assert finding is not None


# =============================================================================
# WS010-WS013: CSV INJECTION (CWE-1236)
# =============================================================================


class TestCSVInjection:
    """Tests for CSV injection detection."""

    @pytest.mark.asyncio
    async def test_detect_csv_write_user_data_python(self, tmp_path):
        """Should detect CSV output with user data in Python."""
        test_file = tmp_path / "export.py"
        test_file.write_text('''
import csv

def export_to_csv(request):
    with open('export.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow([request.data['name'], request.data['email']])
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "WS010"), None)
        assert finding is not None
        assert "CWE-1236" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_csv_write_java(self, tmp_path):
        """Should detect CSV output with user data in Java."""
        test_file = tmp_path / "Export.java"
        test_file.write_text('''
import com.opencsv.CSVWriter;

public class Export {
    public void exportData(HttpServletRequest request) {
        CSVWriter writer = new CSVWriter(new FileWriter("export.csv"));
        writer.writeNext(new String[]{request.getParameter("name")});
    }
}
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "WS010"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_csv_fputcsv_php(self, tmp_path):
        """Should detect fputcsv with $_POST in PHP."""
        test_file = tmp_path / "export.php"
        test_file.write_text('''
<?php
$file = fopen('export.csv', 'w');
fputcsv($file, [$_POST['name'], $_POST['email']]);
fclose($file);
?>
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "WS010"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_excel_export_python(self, tmp_path):
        """Should detect Excel export with user data in Python."""
        test_file = tmp_path / "excel_export.py"
        test_file.write_text('''
import openpyxl
from openpyxl import Workbook

def export_users(users, request):
    wb = Workbook()
    ws = wb.active
    for user in users:
        ws.append([user.name, user.email])
    wb.save('users.xlsx')
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)

        # Should detect openpyxl usage
        assert result.files_scanned == 1


# =============================================================================
# WS020-WS023: INVALID QUANTITY (CWE-1284)
# =============================================================================


class TestInvalidQuantity:
    """Tests for invalid quantity detection."""

    @pytest.mark.asyncio
    async def test_detect_array_index_user_input_python(self, tmp_path):
        """Should detect unchecked array index from user input in Python."""
        test_file = tmp_path / "array.py"
        test_file.write_text('''
def get_item(request):
    items = ["a", "b", "c"]
    index = int(request.args['index'])
    return items[int(request.args['idx'])]
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "WS020"), None)
        assert finding is not None
        assert "CWE-1284" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_array_index_user_input_js(self, tmp_path):
        """Should detect unchecked array index from user input in JavaScript."""
        test_file = tmp_path / "array.js"
        test_file.write_text('''
function getItem(req, res) {
    const items = ["a", "b", "c"];
    const idx = parseInt(req.params.index);
    return items[req.query.idx];
}
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "WS020"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_loop_count_user_input_python(self, tmp_path):
        """Should detect loop count from user input in Python."""
        test_file = tmp_path / "loop.py"
        test_file.write_text('''
def process(request):
    count = int(request.args['count'])
    for i in range(int(request.args['iterations'])):
        process_item(i)
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "WS021"), None)
        assert finding is not None
        assert "CWE-606" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_memory_alloc_user_input_js(self, tmp_path):
        """Should detect memory allocation from user input in JavaScript."""
        test_file = tmp_path / "alloc.js"
        test_file.write_text('''
function createBuffer(req) {
    const size = parseInt(req.params.size);
    const buffer = Buffer.alloc(parseInt(req.query.size));
    return buffer;
}
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "WS022"), None)
        assert finding is not None
        assert "CWE-789" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_quantity_not_validated_python(self, tmp_path):
        """Should detect quantity from user input without validation in Python."""
        test_file = tmp_path / "quantity.py"
        test_file.write_text('''
def checkout(request):
    quantity = int(request.form['quantity'])
    amount = int(request.args['amount'])
    limit = int(request.json['limit'])
    process_order(quantity, amount)
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "WS023"), None)
        assert finding is not None


# =============================================================================
# MULTI-LANGUAGE TESTS
# =============================================================================


class TestMultiLanguageSupport:
    """Tests for multi-language support."""

    @pytest.mark.asyncio
    async def test_scan_csharp_csv_export(self, tmp_path):
        """Should detect CSV issues in C#."""
        test_file = tmp_path / "Export.cs"
        test_file.write_text('''
using CsvHelper;

public class Export
{
    public void ExportData(Request request)
    {
        using var writer = new CsvWriter(new StreamWriter("export.csv"));
        writer.WriteRecord(new { Name = Request.Form["name"] });
    }
}
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)
        assert result.files_scanned == 1

    @pytest.mark.asyncio
    async def test_scan_ruby_csv_export(self, tmp_path):
        """Should detect CSV issues in Ruby."""
        test_file = tmp_path / "export.rb"
        test_file.write_text('''
require 'csv'

def export_users(params)
  CSV.open("export.csv", "w") do |csv|
    csv << [params[:name], params[:email]]
  end
end
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)
        assert result.files_scanned == 1


# =============================================================================
# EDGE CASES AND FALSE POSITIVES
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and false positive handling."""

    @pytest.mark.asyncio
    async def test_safe_object_assign(self, tmp_path):
        """Should not flag Object.assign with literal objects."""
        test_file = tmp_path / "safe.js"
        test_file.write_text('''
const defaults = { theme: "dark" };
const config = Object.assign({}, defaults, { color: "blue" });
''')

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)

        # Should not flag Object.assign with literal objects
        findings = [f for f in result.findings if f.rule_id == "WS003"]
        assert len(findings) == 0

    @pytest.mark.asyncio
    async def test_empty_file(self, tmp_path):
        """Should handle empty files gracefully."""
        test_file = tmp_path / "empty.js"
        test_file.write_text("")

        scanner = WebSecurityDetector()
        result = await scanner.scan(test_file)

        assert result.files_scanned == 1
        assert len(result.findings) == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_scan_directory(self, tmp_path):
        """Should scan all files in directory."""
        (tmp_path / "file1.js").write_text('obj.__proto__ = evil;')
        (tmp_path / "file2.ts").write_text('obj.__proto__ = evil;')
        (tmp_path / "file3.txt").write_text('obj.__proto__ = evil;')  # Should be ignored

        scanner = WebSecurityDetector()
        result = await scanner.scan(tmp_path)

        assert result.files_scanned == 2  # Only .js and .ts
        assert len(result.findings) == 2

    @pytest.mark.asyncio
    async def test_get_rules_summary(self):
        """Should return correct rules summary."""
        scanner = WebSecurityDetector()
        summary = scanner.get_rules_summary()

        assert summary["total_rules"] == 12
        assert len(summary["rules"]) == 12
        assert "CWE-1321" in summary["cwe_coverage"]
        assert "CWE-1236" in summary["cwe_coverage"]
        assert "CWE-1284" in summary["cwe_coverage"]
