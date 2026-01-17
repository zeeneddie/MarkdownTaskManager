"""
Tests for Fase 39 PathSecurityDetector.

Tests cover all 10 path security detection rules:
- PS001-PS003: Uncontrolled Search Path (CWE-427)
- PS010-PS012: Unquoted Search Path (CWE-428)
- PS020-PS023: ReDoS (CWE-1333)
"""

import pytest
from pathlib import Path

from app.services.security_scanner.adapters.path_security_detector import (
    PathSecurityDetector,
    PathSecurityRule,
    PATH_SECURITY_RULES,
    create_path_security_detector,
)
from app.services.security_scanner.models.findings import (
    ScannerType,
    Severity,
)


# =============================================================================
# SCANNER BASICS
# =============================================================================


class TestPathSecurityDetectorBasics:
    """Tests for basic scanner properties."""

    def test_scanner_type(self):
        """Should return correct scanner type."""
        scanner = PathSecurityDetector()
        assert scanner.scanner_type == ScannerType.PATH_SECURITY

    def test_is_always_available(self):
        """Custom scanner should always be available."""
        scanner = PathSecurityDetector()
        assert scanner.is_available() is True

    def test_scanner_version(self):
        """Should return version string."""
        scanner = PathSecurityDetector()
        assert scanner.get_scanner_version() == "1.0.0"

    def test_has_10_rules(self):
        """Should have 10 path security detection rules."""
        assert len(PATH_SECURITY_RULES) == 10

    def test_supported_languages(self):
        """Should support expected languages."""
        scanner = PathSecurityDetector()
        languages = scanner.supported_languages
        assert "python" in languages
        assert "javascript" in languages
        assert "java" in languages
        assert "csharp" in languages
        assert "cpp" in languages
        assert "c" in languages
        assert "go" in languages
        assert "bash" in languages

    def test_supported_extensions(self):
        """Should support expected file extensions."""
        scanner = PathSecurityDetector()
        extensions = scanner.supported_extensions
        assert ".py" in extensions
        assert ".js" in extensions
        assert ".java" in extensions
        assert ".cs" in extensions
        assert ".cpp" in extensions
        assert ".c" in extensions
        assert ".go" in extensions
        assert ".sh" in extensions

    def test_factory_function(self):
        """Factory function should create scanner instance."""
        scanner = create_path_security_detector()
        assert isinstance(scanner, PathSecurityDetector)

    def test_rules_have_cwe_ids(self):
        """All rules should have CWE IDs."""
        for rule in PATH_SECURITY_RULES:
            assert len(rule.cwe_ids) > 0, f"Rule {rule.id} has no CWE IDs"

    def test_rules_have_fix_suggestions(self):
        """All rules should have fix suggestions."""
        for rule in PATH_SECURITY_RULES:
            assert rule.fix_suggestion, f"Rule {rule.id} has no fix suggestion"

    def test_covers_target_cwes(self):
        """Should cover the target CWEs for Fase 39."""
        cwe_coverage = set()
        for rule in PATH_SECURITY_RULES:
            cwe_coverage.update(rule.cwe_ids)

        assert "CWE-427" in cwe_coverage, "CWE-427 (Uncontrolled Search Path) not covered"
        assert "CWE-428" in cwe_coverage, "CWE-428 (Unquoted Search Path) not covered"
        assert "CWE-1333" in cwe_coverage, "CWE-1333 (ReDoS) not covered"


# =============================================================================
# PS001-PS003: UNCONTROLLED SEARCH PATH (CWE-427)
# =============================================================================


class TestUncontrolledSearchPath:
    """Tests for uncontrolled search path detection."""

    @pytest.mark.asyncio
    async def test_detect_relative_dlopen_c(self, tmp_path):
        """Should detect relative path in dlopen in C."""
        test_file = tmp_path / "loader.c"
        test_file.write_text('''
#include <dlfcn.h>

void load_plugin() {
    void *handle = dlopen("plugin.so", RTLD_LAZY);
}
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS001"), None)
        assert finding is not None
        assert "CWE-427" in finding.cwe_ids
        assert finding.severity == Severity.HIGH

    @pytest.mark.asyncio
    async def test_detect_loadlibrary_relative_cpp(self, tmp_path):
        """Should detect relative path in LoadLibrary in C++."""
        test_file = tmp_path / "loader.cpp"
        test_file.write_text('''
#include <windows.h>

void load_dll() {
    HMODULE lib = LoadLibrary("mydll.dll");
}
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS001"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_path_env_modification_python(self, tmp_path):
        """Should detect PATH environment modification in Python."""
        test_file = tmp_path / "env.py"
        test_file.write_text('''
import os

def add_to_path(new_path):
    os.environ['PATH'] = new_path + ':' + os.environ['PATH']
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS002"), None)
        assert finding is not None
        assert finding.severity == Severity.HIGH

    @pytest.mark.asyncio
    async def test_detect_path_env_modification_bash(self, tmp_path):
        """Should detect PATH modification in bash script."""
        test_file = tmp_path / "setup.sh"
        test_file.write_text('''
#!/bin/bash
export PATH=/custom/bin:$PATH
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS002"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_syspath_current_dir_python(self, tmp_path):
        """Should detect current directory added to sys.path in Python."""
        test_file = tmp_path / "import.py"
        test_file.write_text('''
import sys
import os

sys.path.insert(0, '.')
sys.path.append(os.getcwd())
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS003"), None)
        assert finding is not None
        assert finding.severity == Severity.MEDIUM


# =============================================================================
# PS010-PS012: UNQUOTED SEARCH PATH (CWE-428)
# =============================================================================


class TestUnquotedSearchPath:
    """Tests for unquoted search path detection."""

    @pytest.mark.asyncio
    async def test_detect_unquoted_program_files_cpp(self, tmp_path):
        """Should detect unquoted path with spaces in C++."""
        test_file = tmp_path / "exec.cpp"
        test_file.write_text('''
#include <windows.h>

void run_app() {
    CreateProcess(C:\\Program Files\\MyApp\\run.exe, NULL, ...);
}
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS010"), None)
        assert finding is not None
        assert "CWE-428" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_unquoted_service_path_powershell(self, tmp_path):
        """Should detect unquoted service path in registry in PowerShell."""
        # PowerShell is more suited for detecting this pattern
        test_file = tmp_path / "install.ps1"
        test_file.write_text('''
# Install service with unquoted ImagePath (vulnerable to hijacking)
Set-ItemProperty -Path "HKLM:\\SYSTEM\\Services\\MyService" `
    -Name ImagePath -Value C:\\Program Files\\App\\svc.exe
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS011"), None)
        assert finding is not None
        assert finding.severity == Severity.HIGH

    @pytest.mark.asyncio
    async def test_detect_unquoted_variable_bash(self, tmp_path):
        """Should detect unquoted variable in command execution in bash."""
        test_file = tmp_path / "run.sh"
        test_file.write_text('''
#!/bin/bash
PROGRAM=$1
exec $PROGRAM arg1 arg2
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS012"), None)
        assert finding is not None


# =============================================================================
# PS020-PS023: ReDoS (CWE-1333)
# =============================================================================


class TestReDoS:
    """Tests for ReDoS detection."""

    @pytest.mark.asyncio
    async def test_detect_nested_quantifiers_python(self, tmp_path):
        """Should detect nested quantifiers in Python regex."""
        test_file = tmp_path / "regex.py"
        test_file.write_text('''
import re

def validate_email(email):
    pattern = re.compile(r'(a+)+$')
    return pattern.match(email)
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS020"), None)
        assert finding is not None
        assert "CWE-1333" in finding.cwe_ids
        assert finding.severity == Severity.HIGH

    @pytest.mark.asyncio
    async def test_detect_nested_quantifiers_js(self, tmp_path):
        """Should detect nested quantifiers in JavaScript regex."""
        test_file = tmp_path / "regex.js"
        test_file.write_text('''
function validate(input) {
    const pattern = new RegExp("(a+)+$");
    const regex = /(a+)+$/;
    return pattern.test(input);
}
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS020"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_overlapping_alternations_java(self, tmp_path):
        """Should detect overlapping alternations in Java regex."""
        test_file = tmp_path / "Regex.java"
        test_file.write_text('''
import java.util.regex.Pattern;

public class Regex {
    public boolean validate(String input) {
        Pattern p = Pattern.compile("(a|a)+");
        return p.matcher(input).matches();
    }
}
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS021"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_greedy_quantifiers_python(self, tmp_path):
        """Should detect greedy quantifiers in Python regex."""
        test_file = tmp_path / "greedy.py"
        test_file.write_text('''
import re

def search(text):
    pattern = re.compile(r'.*foo.*bar.*')
    return pattern.search(text)
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS022"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_user_input_in_regex_python(self, tmp_path):
        """Should detect user input in regex in Python."""
        test_file = tmp_path / "search.py"
        test_file.write_text('''
import re

def search(request):
    pattern = re.compile(request.args['pattern'])
    return pattern.findall(content)
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS023"), None)
        assert finding is not None
        assert "CWE-185" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_user_input_in_regex_js(self, tmp_path):
        """Should detect user input in regex in JavaScript."""
        test_file = tmp_path / "search.js"
        test_file.write_text('''
function search(req, content) {
    const pattern = new RegExp(req.params.pattern);
    return content.match(pattern);
}
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS023"), None)
        assert finding is not None


# =============================================================================
# MULTI-LANGUAGE TESTS
# =============================================================================


class TestMultiLanguageSupport:
    """Tests for multi-language support."""

    @pytest.mark.asyncio
    async def test_scan_go_redos(self, tmp_path):
        """Should detect ReDoS in Go."""
        test_file = tmp_path / "regex.go"
        test_file.write_text('''
package main

import "regexp"

func validate(input string) bool {
    pattern := regexp.MustCompile(`(a+)+$`)
    return pattern.MatchString(input)
}
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS020"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_scan_ruby_redos(self, tmp_path):
        """Should detect user input in regex in Ruby."""
        test_file = tmp_path / "search.rb"
        test_file.write_text('''
def search
  pattern = Regexp.new(params[:pattern])
  content.scan(pattern)
end
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS023"), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_scan_php_redos(self, tmp_path):
        """Should detect user input in regex in PHP."""
        test_file = tmp_path / "search.php"
        test_file.write_text('''
<?php
function search() {
    preg_match($_GET['pattern'], $content, $matches);
    return $matches;
}
?>
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if f.rule_id == "PS023"), None)
        assert finding is not None


# =============================================================================
# EDGE CASES AND FALSE POSITIVES
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and false positive handling."""

    @pytest.mark.asyncio
    async def test_safe_absolute_path(self, tmp_path):
        """Should not flag absolute paths in library loading."""
        test_file = tmp_path / "safe.c"
        test_file.write_text('''
#include <dlfcn.h>

void load_plugin() {
    void *handle = dlopen("/usr/lib/plugin.so", RTLD_LAZY);
}
''')

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        # Should not flag absolute paths
        findings = [f for f in result.findings if f.rule_id == "PS001"]
        assert len(findings) == 0

    @pytest.mark.asyncio
    async def test_empty_file(self, tmp_path):
        """Should handle empty files gracefully."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")

        scanner = PathSecurityDetector()
        result = await scanner.scan(test_file)

        assert result.files_scanned == 1
        assert len(result.findings) == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_scan_directory(self, tmp_path):
        """Should scan all files in directory."""
        (tmp_path / "file1.py").write_text("os.environ['PATH'] = '/bad'")
        (tmp_path / "file2.js").write_text("new RegExp(req.params.p)")
        (tmp_path / "file3.txt").write_text("os.environ['PATH'] = '/bad'")  # Should be ignored

        scanner = PathSecurityDetector()
        result = await scanner.scan(tmp_path)

        assert result.files_scanned == 2  # Only .py and .js
        assert len(result.findings) == 2

    @pytest.mark.asyncio
    async def test_get_rules_summary(self):
        """Should return correct rules summary."""
        scanner = PathSecurityDetector()
        summary = scanner.get_rules_summary()

        assert summary["total_rules"] == 10
        assert len(summary["rules"]) == 10
        assert "CWE-427" in summary["cwe_coverage"]
        assert "CWE-428" in summary["cwe_coverage"]
        assert "CWE-1333" in summary["cwe_coverage"]
