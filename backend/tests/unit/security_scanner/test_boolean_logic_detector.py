"""
Tests for Fase 36 BooleanLogicDetector.

Tests cover all 12 boolean logic and comparison error detection rules:
- BL001-BL002: Operator confusion (bitwise vs boolean)
- BL010-BL011: Precedence issues
- BL020-BL023: Comparison issues (==, float, chained, String.equals)
- BL030-BL031: Short-circuit issues
- BL040-BL041: Tautology/contradiction
"""

import pytest
from pathlib import Path

from app.services.security_scanner.adapters.boolean_logic_detector import (
    BooleanLogicDetector,
    BooleanLogicRule,
    BOOLEAN_LOGIC_RULES,
    create_boolean_logic_detector,
)
from app.services.security_scanner.models.findings import (
    ScannerType,
    Severity,
)


# =============================================================================
# SCANNER BASICS
# =============================================================================


class TestBooleanLogicDetectorBasics:
    """Tests for basic scanner properties."""

    def test_scanner_type(self):
        """Should return correct scanner type."""
        scanner = BooleanLogicDetector()
        assert scanner.scanner_type == ScannerType.BOOLEAN_LOGIC

    def test_is_always_available(self):
        """Custom scanner should always be available."""
        scanner = BooleanLogicDetector()
        assert scanner.is_available() is True

    def test_scanner_version(self):
        """Should return version string."""
        scanner = BooleanLogicDetector()
        assert scanner.get_scanner_version() == "1.1.0"

    def test_has_20_rules(self):
        """Should have 20 boolean logic detection rules."""
        assert len(BOOLEAN_LOGIC_RULES) == 20

    def test_supported_languages(self):
        """Should support multiple languages."""
        scanner = BooleanLogicDetector()
        languages = scanner.supported_languages
        assert "python" in languages
        assert "javascript" in languages
        assert "java" in languages
        assert "csharp" in languages
        assert "cpp" in languages

    def test_supported_extensions(self):
        """Should support expected file extensions."""
        scanner = BooleanLogicDetector()
        extensions = scanner.supported_extensions
        assert ".py" in extensions
        assert ".js" in extensions
        assert ".java" in extensions
        assert ".cs" in extensions

    def test_factory_function(self):
        """Factory function should create scanner instance."""
        scanner = create_boolean_logic_detector()
        assert isinstance(scanner, BooleanLogicDetector)

    def test_rules_have_fix_suggestions(self):
        """All rules should have fix suggestions."""
        for rule in BOOLEAN_LOGIC_RULES:
            assert rule.fix_suggestion, f"Rule {rule.id} has no fix suggestion"


# =============================================================================
# BL001-BL002: BITWISE VS BOOLEAN
# =============================================================================


class TestBitwiseVsBoolean:
    """Tests for bitwise vs boolean operator confusion."""

    @pytest.mark.asyncio
    async def test_detect_bitwise_and_in_condition_cpp(self, tmp_path):
        """Should detect bitwise AND in boolean context."""
        test_file = tmp_path / "cond.cpp"
        test_file.write_text('''
#include <iostream>
int main() {
    if (a & b) {
        std::cout << "Probably meant &&";
    }
}
''')

        scanner = BooleanLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        bitwise_finding = next((f for f in result.findings if f.rule_id == "BL001"), None)
        assert bitwise_finding is not None
        assert "CWE-480" in bitwise_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_bitwise_or_in_condition_php(self, tmp_path):
        """Should detect bitwise OR in boolean context."""
        test_file = tmp_path / "cond.php"
        test_file.write_text('''<?php
if ($a | $b) {
    echo "Probably meant ||";
}
''')

        scanner = BooleanLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        bitwise_finding = next((f for f in result.findings if f.rule_id == "BL002"), None)
        assert bitwise_finding is not None


# =============================================================================
# BL010-BL011: PRECEDENCE ISSUES
# =============================================================================


class TestPrecedenceIssues:
    """Tests for operator precedence issue detection."""

    @pytest.mark.asyncio
    async def test_detect_precedence_issue_javascript(self, tmp_path):
        """Should detect precedence issue with bitwise and comparison."""
        test_file = tmp_path / "prec.js"
        test_file.write_text('''
if (a & b == c) {
    // a & (b == c) not (a & b) == c
    console.log("Precedence bug");
}
''')

        scanner = BooleanLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        prec_finding = next((f for f in result.findings if f.rule_id == "BL010"), None)
        assert prec_finding is not None
        assert "CWE-783" in prec_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_and_or_precedence_ambiguity(self, tmp_path):
        """Should detect AND/OR precedence ambiguity."""
        test_file = tmp_path / "prec.js"
        test_file.write_text('''
if (a || b && c) {
    // a || (b && c) - might not be intended
    console.log("Precedence ambiguity");
}
''')

        scanner = BooleanLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        prec_finding = next((f for f in result.findings if f.rule_id == "BL011"), None)
        assert prec_finding is not None


# =============================================================================
# BL020-BL023: COMPARISON ISSUES
# =============================================================================


class TestComparisonIssues:
    """Tests for comparison issue detection."""

    @pytest.mark.asyncio
    async def test_detect_loose_equality_javascript(self, tmp_path):
        """Should detect == instead of === in JavaScript."""
        test_file = tmp_path / "compare.js"
        test_file.write_text('''
if (value == otherValue) {
    console.log("Should use ===");
}

return (x == y);
''')

        scanner = BooleanLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        eq_finding = next((f for f in result.findings if f.rule_id == "BL020"), None)
        assert eq_finding is not None
        assert "CWE-843" in eq_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_float_equality_python(self, tmp_path):
        """Should detect float equality comparison."""
        test_file = tmp_path / "float.py"
        test_file.write_text('''
if float(a) == float(b):
    print("Dangerous float comparison")

if 0.1 + 0.2 == 0.3:
    print("This is False!")
''')

        scanner = BooleanLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        float_finding = next((f for f in result.findings if f.rule_id == "BL021"), None)
        assert float_finding is not None
        assert "CWE-1077" in float_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_chained_comparison_javascript(self, tmp_path):
        """Should detect chained comparison in non-Python language."""
        test_file = tmp_path / "chain.js"
        test_file.write_text('''
if (a < b < c) {
    // This does NOT work like Python!
    console.log("Bug");
}
''')

        scanner = BooleanLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        chain_finding = next((f for f in result.findings if f.rule_id == "BL022"), None)
        assert chain_finding is not None
        assert "CWE-480" in chain_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_string_equality_java(self, tmp_path):
        """Should detect String == instead of .equals() in Java."""
        test_file = tmp_path / "Str.java"
        test_file.write_text('''
public class Str {
    void compare(String a) {
        if (a == "test") {
            System.out.println("Should use .equals()");
        }
    }
}
''')

        scanner = BooleanLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        str_finding = next((f for f in result.findings if f.rule_id == "BL023"), None)
        assert str_finding is not None


# =============================================================================
# BL030-BL031: SHORT-CIRCUIT ISSUES
# =============================================================================


class TestShortCircuitIssues:
    """Tests for short-circuit evaluation issues."""

    @pytest.mark.asyncio
    async def test_detect_null_check_after_dereference_java(self, tmp_path):
        """Should detect null check after dereference."""
        test_file = tmp_path / "Null.java"
        test_file.write_text('''
public class Null {
    void process(String s) {
        int len = s.length();
        if (s != null) {
            System.out.println(len);
        }
    }
}
''')

        scanner = BooleanLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        null_finding = next((f for f in result.findings if f.rule_id == "BL030"), None)
        assert null_finding is not None
        assert "CWE-476" in null_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_side_effect_in_short_circuit(self, tmp_path):
        """Should detect side effect in short-circuit."""
        test_file = tmp_path / "side.js"
        test_file.write_text('''
if (condition && i++) {
    console.log("i may not be incremented");
}

if (flag || doSomething()) {
    console.log("doSomething may not be called");
}
''')

        scanner = BooleanLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        side_finding = next((f for f in result.findings if f.rule_id == "BL031"), None)
        assert side_finding is not None
        assert "CWE-768" in side_finding.cwe_ids


# =============================================================================
# BL040-BL041: TAUTOLOGY/CONTRADICTION
# =============================================================================


class TestTautologyContradiction:
    """Tests for tautology and contradiction detection."""

    @pytest.mark.asyncio
    async def test_detect_tautology_javascript(self, tmp_path):
        """Should detect always-true condition."""
        test_file = tmp_path / "taut.js"
        test_file.write_text('''
if (true) {
    console.log("Always executes");
}

if (1 == 1) {
    console.log("Always true");
}
''')

        scanner = BooleanLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        taut_finding = next((f for f in result.findings if f.rule_id == "BL040"), None)
        assert taut_finding is not None
        assert "CWE-571" in taut_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_contradiction_python(self, tmp_path):
        """Should detect always-false condition."""
        test_file = tmp_path / "contra.py"
        test_file.write_text('''
if False:
    print("Never executes - dead code")

if 1 == 2:
    print("Also dead code")
''')

        scanner = BooleanLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        contra_finding = next((f for f in result.findings if f.rule_id == "BL041"), None)
        assert contra_finding is not None
        assert "CWE-570" in contra_finding.cwe_ids


# =============================================================================
# DIRECTORY SCANNING
# =============================================================================


class TestDirectoryScanning:
    """Tests for scanning directories."""

    @pytest.mark.asyncio
    async def test_scan_directory(self, tmp_path):
        """Should scan entire directory recursively."""
        # Create multiple files with different issues
        (tmp_path / "bool.js").write_text('if (a & b) { console.log("bitwise"); }')
        (tmp_path / "compare.java").write_text('''
public class C {
    void f(String s) { if (s == "x") {} }
}
''')

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "float.py").write_text('if 0.1 == 0.2: pass')

        scanner = BooleanLogicDetector()
        result = await scanner.scan(tmp_path)

        assert result.files_scanned >= 3
        assert len(result.findings) >= 2

    @pytest.mark.asyncio
    async def test_scan_no_issues(self, tmp_path):
        """Should handle clean files."""
        test_file = tmp_path / "clean.js"
        test_file.write_text('''
// Good: Using && for boolean
if (a && b) {
    console.log("Correct");
}

// Good: Using strict equality
if (value === otherValue) {
    console.log("Correct");
}

// Good: Explicit comparison
if (a < b && b < c) {
    console.log("Correct");
}
''')

        scanner = BooleanLogicDetector()
        result = await scanner.scan(test_file)

        assert result.files_scanned == 1
        # Minimal findings expected for clean code
        high_findings = [f for f in result.findings if f.severity == Severity.HIGH or f.severity == Severity.CRITICAL]
        assert len(high_findings) == 0


# =============================================================================
# RULES SUMMARY
# =============================================================================


class TestRulesSummary:
    """Tests for rules summary functionality."""

    def test_get_rules_summary(self):
        """Should return structured rules summary."""
        scanner = BooleanLogicDetector()
        summary = scanner.get_rules_summary()

        assert summary["total_rules"] == 20
        assert len(summary["rules"]) == 20
        assert "supported_languages" in summary

        # Verify rule structure
        for rule in summary["rules"]:
            assert "id" in rule
            assert "title" in rule
            assert "severity" in rule
            assert "category" in rule

        # Verify categories
        categories = {rule["category"] for rule in summary["rules"]}
        assert "operator_error" in categories
        assert "comparison_error" in categories
        assert "logic_error" in categories


# =============================================================================
# FALSE POSITIVE FILTERING
# =============================================================================


class TestFalsePositiveFiltering:
    """Tests for false positive filtering."""

    @pytest.mark.asyncio
    async def test_filter_intentional_bitwise_operations(self, tmp_path):
        """Should not flag intentional bitwise operations."""
        test_file = tmp_path / "bits.cpp"
        test_file.write_text('''
#include <iostream>
int main() {
    // Intentional bitwise for masking
    int flags = MASK & 0xFF;
    int masked = value & FLAG_ENABLED;
}
''')

        scanner = BooleanLogicDetector()
        result = await scanner.scan(test_file)

        # Bitwise with constants/masks should be filtered
        bitwise_findings = [f for f in result.findings if f.rule_id in ["BL001", "BL002"]]
        assert len(bitwise_findings) == 0

    @pytest.mark.asyncio
    async def test_filter_null_equality_check_javascript(self, tmp_path):
        """Should not flag == with null (valid pattern)."""
        test_file = tmp_path / "null.js"
        test_file.write_text('''
if (value == null) {
    // This is a valid pattern to check null/undefined
    console.log("null or undefined");
}
''')

        scanner = BooleanLogicDetector()
        result = await scanner.scan(test_file)

        # null == check is a valid pattern
        eq_findings = [f for f in result.findings if f.rule_id == "BL020"]
        assert len(eq_findings) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
