"""
Tests for Fase 36 ControlFlowLogicDetector.

Tests cover all 12 control flow and logic error detection rules:
- CF001-CF004: Loop errors (off-by-one, infinite, empty, float counter)
- CF010-CF011: Condition errors (assignment, dangling else)
- CF020-CF022: Switch errors (missing break, default, enum)
- CF030-CF032: Exception errors (empty catch, missing finally, generic)
"""

import pytest
from pathlib import Path

from app.services.security_scanner.adapters.control_flow_logic_detector import (
    ControlFlowLogicDetector,
    ControlFlowRule,
    CONTROL_FLOW_RULES,
    create_control_flow_logic_detector,
)
from app.services.security_scanner.models.findings import (
    ScannerType,
    Severity,
)


# =============================================================================
# SCANNER BASICS
# =============================================================================


class TestControlFlowLogicDetectorBasics:
    """Tests for basic scanner properties."""

    def test_scanner_type(self):
        """Should return correct scanner type."""
        scanner = ControlFlowLogicDetector()
        assert scanner.scanner_type == ScannerType.CONTROL_FLOW_LOGIC

    def test_is_always_available(self):
        """Custom scanner should always be available."""
        scanner = ControlFlowLogicDetector()
        assert scanner.is_available() is True

    def test_scanner_version(self):
        """Should return version string."""
        scanner = ControlFlowLogicDetector()
        assert scanner.get_scanner_version() == "1.0.0"

    def test_has_12_rules(self):
        """Should have 12 control flow detection rules."""
        assert len(CONTROL_FLOW_RULES) == 12

    def test_supported_languages(self):
        """Should support multiple languages."""
        scanner = ControlFlowLogicDetector()
        languages = scanner.supported_languages
        assert "python" in languages
        assert "javascript" in languages
        assert "java" in languages
        assert "csharp" in languages
        assert "cpp" in languages

    def test_supported_extensions(self):
        """Should support expected file extensions."""
        scanner = ControlFlowLogicDetector()
        extensions = scanner.supported_extensions
        assert ".py" in extensions
        assert ".js" in extensions
        assert ".java" in extensions
        assert ".cs" in extensions

    def test_factory_function(self):
        """Factory function should create scanner instance."""
        scanner = create_control_flow_logic_detector()
        assert isinstance(scanner, ControlFlowLogicDetector)

    def test_rules_have_fix_suggestions(self):
        """All rules should have fix suggestions."""
        for rule in CONTROL_FLOW_RULES:
            assert rule.fix_suggestion, f"Rule {rule.id} has no fix suggestion"


# =============================================================================
# CF001-CF004: LOOP ERRORS
# =============================================================================


class TestLoopErrors:
    """Tests for loop error detection."""

    @pytest.mark.asyncio
    async def test_detect_off_by_one_javascript(self, tmp_path):
        """Should detect off-by-one error in JavaScript."""
        test_file = tmp_path / "loop.js"
        test_file.write_text('''
for (let i = 0; i <= arr.length; i++) {
    console.log(arr[i]);
}
''')

        scanner = ControlFlowLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        obo_finding = next((f for f in result.findings if f.rule_id == "CF001"), None)
        assert obo_finding is not None
        assert "CWE-193" in obo_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_off_by_one_java(self, tmp_path):
        """Should detect off-by-one error in Java."""
        test_file = tmp_path / "Loop.java"
        test_file.write_text('''
public class Loop {
    void process(int[] arr) {
        for (int i = 0; i <= arr.length; i++) {
            System.out.println(arr[i]);
        }
    }
}
''')

        scanner = ControlFlowLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        obo_finding = next((f for f in result.findings if f.rule_id == "CF001"), None)
        assert obo_finding is not None

    @pytest.mark.asyncio
    async def test_detect_empty_loop_body(self, tmp_path):
        """Should detect empty loop body (semicolon after for)."""
        test_file = tmp_path / "loop.js"
        test_file.write_text('''
for (let i = 0; i < 10; i++);
{
    console.log(i);  // This is NOT in the loop!
}
''')

        scanner = ControlFlowLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        empty_finding = next((f for f in result.findings if f.rule_id == "CF003"), None)
        assert empty_finding is not None

    @pytest.mark.asyncio
    async def test_detect_float_loop_counter(self, tmp_path):
        """Should detect float loop counter."""
        test_file = tmp_path / "Loop.java"
        test_file.write_text('''
public class Loop {
    void process() {
        for (float f = 0.0; f < 1.0; f += 0.1) {
            System.out.println(f);
        }
    }
}
''')

        scanner = ControlFlowLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        float_finding = next((f for f in result.findings if f.rule_id == "CF004"), None)
        assert float_finding is not None


# =============================================================================
# CF010-CF011: CONDITION ERRORS
# =============================================================================


class TestConditionErrors:
    """Tests for condition error detection."""

    @pytest.mark.asyncio
    async def test_detect_assignment_in_condition_javascript(self, tmp_path):
        """Should detect assignment instead of comparison."""
        test_file = tmp_path / "cond.js"
        test_file.write_text('''
if (x = 5) {
    console.log("This is probably a bug");
}
''')

        scanner = ControlFlowLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        assign_finding = next((f for f in result.findings if f.rule_id == "CF010"), None)
        assert assign_finding is not None
        assert "CWE-481" in assign_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_assignment_in_condition_php(self, tmp_path):
        """Should detect assignment in condition in PHP."""
        test_file = tmp_path / "cond.php"
        test_file.write_text('''<?php
if ($result = getValue()) {
    echo "Got result";
}
''')

        scanner = ControlFlowLogicDetector()
        result = await scanner.scan(test_file)

        # Check if finding exists (may be intentional pattern in PHP)
        assign_finding = next((f for f in result.findings if f.rule_id == "CF010"), None)
        assert assign_finding is not None


# =============================================================================
# CF020-CF022: SWITCH ERRORS
# =============================================================================


class TestSwitchErrors:
    """Tests for switch statement error detection."""

    @pytest.mark.asyncio
    async def test_detect_missing_break(self, tmp_path):
        """Should detect missing break in switch case."""
        test_file = tmp_path / "switch.js"
        test_file.write_text('''
switch (value) {
    case 1:
        doSomething();
    case 2:
        doSomethingElse();
        break;
}
''')

        scanner = ControlFlowLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        break_finding = next((f for f in result.findings if f.rule_id == "CF020"), None)
        assert break_finding is not None
        assert "CWE-484" in break_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_missing_default(self, tmp_path):
        """Should detect missing default case."""
        test_file = tmp_path / "switch.java"
        test_file.write_text('''
public class Switch {
    void process(int x) {
        switch (x) {
            case 1:
                System.out.println("One");
                break;
            case 2:
                System.out.println("Two");
                break;
        }
    }
}
''')

        scanner = ControlFlowLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        default_finding = next((f for f in result.findings if f.rule_id == "CF021"), None)
        assert default_finding is not None
        assert "CWE-478" in default_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_no_finding_with_default(self, tmp_path):
        """Should not flag switch with default case."""
        test_file = tmp_path / "switch.java"
        test_file.write_text('''
public class Switch {
    void process(int x) {
        switch (x) {
            case 1:
                System.out.println("One");
                break;
            default:
                System.out.println("Other");
                break;
        }
    }
}
''')

        scanner = ControlFlowLogicDetector()
        result = await scanner.scan(test_file)

        default_findings = [f for f in result.findings if f.rule_id == "CF021"]
        assert len(default_findings) == 0


# =============================================================================
# CF030-CF032: EXCEPTION ERRORS
# =============================================================================


class TestExceptionErrors:
    """Tests for exception handling error detection."""

    @pytest.mark.asyncio
    async def test_detect_empty_catch_python(self, tmp_path):
        """Should detect empty catch block in Python."""
        test_file = tmp_path / "exc.py"
        test_file.write_text('''
try:
    risky_operation()
except Exception as e:
    pass
''')

        scanner = ControlFlowLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        empty_finding = next((f for f in result.findings if f.rule_id == "CF030"), None)
        assert empty_finding is not None
        assert "CWE-1069" in empty_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_empty_catch_javascript(self, tmp_path):
        """Should detect empty catch block in JavaScript."""
        test_file = tmp_path / "exc.js"
        test_file.write_text('''
try {
    riskyOperation();
} catch (e) {
}
''')

        scanner = ControlFlowLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        empty_finding = next((f for f in result.findings if f.rule_id == "CF030"), None)
        assert empty_finding is not None

    @pytest.mark.asyncio
    async def test_detect_empty_catch_java(self, tmp_path):
        """Should detect empty catch block in Java."""
        test_file = tmp_path / "Exc.java"
        test_file.write_text('''
public class Exc {
    void process() {
        try {
            riskyOperation();
        } catch (Exception e) {
        }
    }
}
''')

        scanner = ControlFlowLogicDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        empty_finding = next((f for f in result.findings if f.rule_id == "CF030"), None)
        assert empty_finding is not None

    @pytest.mark.asyncio
    async def test_detect_generic_exception_catch(self, tmp_path):
        """Should detect catching generic Exception."""
        test_file = tmp_path / "exc.py"
        test_file.write_text('''
try:
    risky_operation()
except Exception as e:
    logger.error(e)
''')

        scanner = ControlFlowLogicDetector()
        result = await scanner.scan(test_file)

        generic_findings = [f for f in result.findings if f.rule_id == "CF032"]
        assert len(generic_findings) >= 1


# =============================================================================
# DIRECTORY SCANNING
# =============================================================================


class TestDirectoryScanning:
    """Tests for scanning directories."""

    @pytest.mark.asyncio
    async def test_scan_directory(self, tmp_path):
        """Should scan entire directory recursively."""
        # Create multiple files with different issues
        (tmp_path / "loop.js").write_text('for (let i = 0; i <= arr.length; i++) {}')
        (tmp_path / "switch.java").write_text('''
public class S {
    void f(int x) { switch(x) { case 1: break; } }
}
''')

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "exc.py").write_text('''
try:
    x()
except:
    pass
''')

        scanner = ControlFlowLogicDetector()
        result = await scanner.scan(tmp_path)

        assert result.files_scanned >= 3
        assert len(result.findings) >= 2

    @pytest.mark.asyncio
    async def test_scan_no_issues(self, tmp_path):
        """Should handle clean files."""
        test_file = tmp_path / "clean.js"
        test_file.write_text('''
for (let i = 0; i < arr.length; i++) {
    console.log(arr[i]);
}

switch (value) {
    case 1:
        doSomething();
        break;
    default:
        doDefault();
        break;
}

try {
    riskyOperation();
} catch (e) {
    console.error(e);
    throw e;
}
''')

        scanner = ControlFlowLogicDetector()
        result = await scanner.scan(test_file)

        assert result.files_scanned == 1
        # Should have minimal findings for this clean code
        critical_findings = [f for f in result.findings if f.severity == Severity.CRITICAL or f.severity == Severity.HIGH]
        assert len(critical_findings) == 0


# =============================================================================
# RULES SUMMARY
# =============================================================================


class TestRulesSummary:
    """Tests for rules summary functionality."""

    def test_get_rules_summary(self):
        """Should return structured rules summary."""
        scanner = ControlFlowLogicDetector()
        summary = scanner.get_rules_summary()

        assert summary["total_rules"] == 12
        assert len(summary["rules"]) == 12
        assert "supported_languages" in summary

        # Verify rule structure
        for rule in summary["rules"]:
            assert "id" in rule
            assert "title" in rule
            assert "severity" in rule
            assert "category" in rule

        # Verify categories
        categories = {rule["category"] for rule in summary["rules"]}
        assert "loop_error" in categories
        assert "exception_error" in categories
        assert "switch_error" in categories


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
