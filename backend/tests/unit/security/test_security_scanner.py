"""
Tests for Fase 31 CWE Security Scanner System.

Tests cover:
- SARIF parsing
- Language detection
- Scanner adapters
- Orchestrator functionality
"""

import pytest
from pathlib import Path
from datetime import datetime

from app.services.security_scanner import (
    # Models
    ScannerType,
    Severity,
    CWE_TOP_25,
    Location,
    SecurityFinding,
    ScanResult,
    SecurityReport,
    # SARIF
    SarifLevel,
    SarifParser,
    # Adapters
    OpenGrepAdapter,
    BanditAdapter,
    GosecAdapter,
    TrivyAdapter,
    ClassicASPScanner,
    # Orchestrator
    SecurityScanOrchestrator,
    create_security_orchestrator,
    EXTENSION_TO_LANGUAGE,
)


# =============================================================================
# CWE TOP 25 TESTS
# =============================================================================


class TestCWETop25:
    """Tests for CWE Top 25 constants."""

    def test_cwe_top_25_count(self):
        """Should have 25 CWEs defined."""
        assert len(CWE_TOP_25) == 25

    def test_cwe_format(self):
        """CWE IDs should be properly formatted."""
        for cwe_id in CWE_TOP_25.keys():
            assert cwe_id.startswith("CWE-")
            # Should have numeric part after CWE-
            numeric_part = cwe_id.replace("CWE-", "")
            assert numeric_part.isdigit()

    def test_cwe_has_descriptions(self):
        """Each CWE should have a description."""
        for cwe_id, description in CWE_TOP_25.items():
            assert description
            assert len(description) > 5


# =============================================================================
# SEVERITY TESTS
# =============================================================================


class TestSeverity:
    """Tests for severity levels."""

    def test_severity_values(self):
        """Should have expected severity values."""
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"
        assert Severity.INFO.value == "info"

    def test_severity_count(self):
        """Should have 5 severity levels."""
        assert len(Severity) == 5


# =============================================================================
# SCANNER TYPE TESTS
# =============================================================================


class TestScannerType:
    """Tests for scanner types."""

    def test_external_scanner_types(self):
        """Should have external scanner types."""
        assert ScannerType.OPENGREP.value == "opengrep"
        assert ScannerType.BANDIT.value == "bandit"
        assert ScannerType.GOSEC.value == "gosec"
        assert ScannerType.TRIVY.value == "trivy"

    def test_custom_scanner_types(self):
        """Should have custom scanner types."""
        assert ScannerType.CUSTOM_ASP.value == "custom_asp"


# =============================================================================
# LOCATION TESTS
# =============================================================================


class TestLocation:
    """Tests for Location model."""

    def test_location_creation(self):
        """Should create location with required fields."""
        loc = Location(
            file_path="/test/file.py",
            start_line=10,
        )
        assert loc.file_path == "/test/file.py"
        assert loc.start_line == 10
        assert loc.end_line is None

    def test_location_with_all_fields(self):
        """Should create location with all optional fields."""
        loc = Location(
            file_path="/test/file.py",
            start_line=10,
            end_line=15,
            start_column=5,
            end_column=20,
            snippet="some code here",
            function_name="test_func",
            class_name="TestClass",
        )
        assert loc.end_line == 15
        assert loc.snippet == "some code here"
        assert loc.function_name == "test_func"


# =============================================================================
# SECURITY FINDING TESTS
# =============================================================================


class TestSecurityFinding:
    """Tests for SecurityFinding model."""

    def test_finding_creation(self):
        """Should create finding with required fields."""
        finding = SecurityFinding(
            id="test-001",
            rule_id="RULE-001",
            title="Test Finding",
            description="Test description",
            severity=Severity.HIGH,
            scanner=ScannerType.BANDIT,
            location=Location(file_path="/test.py", start_line=10),
        )
        assert finding.id == "test-001"
        assert finding.severity == Severity.HIGH
        assert finding.fingerprint  # Auto-generated

    def test_finding_cwe_top_25_check(self):
        """Should correctly identify CWE Top 25."""
        finding_top25 = SecurityFinding(
            id="test-001",
            rule_id="RULE-001",
            title="SQL Injection",
            description="SQL injection detected",
            severity=Severity.CRITICAL,
            scanner=ScannerType.BANDIT,
            location=Location(file_path="/test.py", start_line=10),
            cwe_ids=["CWE-89"],  # SQL Injection - Top 25
        )
        assert finding_top25.is_cwe_top_25 is True

        finding_not_top25 = SecurityFinding(
            id="test-002",
            rule_id="RULE-002",
            title="Other Issue",
            description="Some other issue",
            severity=Severity.LOW,
            scanner=ScannerType.BANDIT,
            location=Location(file_path="/test.py", start_line=20),
            cwe_ids=["CWE-999"],  # Not in Top 25
        )
        assert finding_not_top25.is_cwe_top_25 is False


# =============================================================================
# SCAN RESULT TESTS
# =============================================================================


class TestScanResult:
    """Tests for ScanResult model."""

    def test_scan_result_creation(self):
        """Should create scan result."""
        result = ScanResult(
            scanner=ScannerType.BANDIT,
            scanner_version="1.7.0",
            scan_duration_ms=1500,
            findings=[],
            files_scanned=10,
        )
        assert result.scanner == ScannerType.BANDIT
        assert result.finding_count == 0
        assert result.files_scanned == 10

    def test_scan_result_counts(self):
        """Should correctly count findings by severity."""
        findings = [
            SecurityFinding(
                id=f"test-{i}",
                rule_id="RULE",
                title="Test",
                description="Test",
                severity=sev,
                scanner=ScannerType.BANDIT,
                location=Location(file_path="/test.py", start_line=i),
            )
            for i, sev in enumerate([
                Severity.CRITICAL,
                Severity.CRITICAL,
                Severity.HIGH,
                Severity.MEDIUM,
            ])
        ]

        result = ScanResult(
            scanner=ScannerType.BANDIT,
            scanner_version="1.7.0",
            scan_duration_ms=1000,
            findings=findings,
            files_scanned=5,
        )

        assert result.critical_count == 2
        assert result.high_count == 1
        assert result.finding_count == 4


# =============================================================================
# LANGUAGE DETECTION TESTS
# =============================================================================


class TestLanguageDetection:
    """Tests for language detection."""

    def test_python_detection(self):
        """Should detect Python files."""
        assert EXTENSION_TO_LANGUAGE.get(".py") == "python"
        assert EXTENSION_TO_LANGUAGE.get(".pyw") == "python"

    def test_javascript_detection(self):
        """Should detect JavaScript files."""
        assert EXTENSION_TO_LANGUAGE.get(".js") == "javascript"
        assert EXTENSION_TO_LANGUAGE.get(".jsx") == "javascript"

    def test_go_detection(self):
        """Should detect Go files."""
        assert EXTENSION_TO_LANGUAGE.get(".go") == "go"

    def test_asp_detection(self):
        """Should detect Classic ASP files."""
        assert EXTENSION_TO_LANGUAGE.get(".asp") == "asp"
        assert EXTENSION_TO_LANGUAGE.get(".asa") == "asp"


# =============================================================================
# ADAPTER TESTS
# =============================================================================


class TestOpenGrepAdapter:
    """Tests for OpenGrep adapter."""

    def test_supported_languages(self):
        """Should support many languages."""
        adapter = OpenGrepAdapter()
        assert "python" in adapter.supported_languages
        assert "javascript" in adapter.supported_languages
        assert "go" in adapter.supported_languages
        assert "java" in adapter.supported_languages

    def test_supported_extensions(self):
        """Should support many extensions."""
        adapter = OpenGrepAdapter()
        assert ".py" in adapter.supported_extensions
        assert ".js" in adapter.supported_extensions
        assert ".go" in adapter.supported_extensions

    def test_scanner_type(self):
        """Should return correct scanner type."""
        adapter = OpenGrepAdapter()
        assert adapter.scanner_type == ScannerType.OPENGREP


class TestBanditAdapter:
    """Tests for Bandit adapter."""

    def test_supported_languages(self):
        """Should only support Python."""
        adapter = BanditAdapter()
        assert adapter.supported_languages == {"python"}

    def test_supported_extensions(self):
        """Should only support Python extensions."""
        adapter = BanditAdapter()
        assert adapter.supported_extensions == {".py", ".pyw"}

    def test_cwe_mapping(self):
        """Should have CWE mappings for Bandit tests."""
        assert "B608" in BanditAdapter.BANDIT_CWE_MAP
        assert "CWE-89" in BanditAdapter.BANDIT_CWE_MAP["B608"]


class TestGosecAdapter:
    """Tests for Gosec adapter."""

    def test_supported_languages(self):
        """Should only support Go."""
        adapter = GosecAdapter()
        assert adapter.supported_languages == {"go"}

    def test_cwe_mapping(self):
        """Should have CWE mappings for Gosec rules."""
        assert "G201" in GosecAdapter.GOSEC_CWE_MAP
        assert "CWE-89" in GosecAdapter.GOSEC_CWE_MAP["G201"]


class TestClassicASPScanner:
    """Tests for Classic ASP custom scanner."""

    def test_supported_languages(self):
        """Should support ASP and VBScript."""
        scanner = ClassicASPScanner()
        assert "asp" in scanner.supported_languages
        assert "vbscript" in scanner.supported_languages

    def test_has_rules(self):
        """Should have security rules defined."""
        scanner = ClassicASPScanner()
        assert len(scanner.rules) > 0

    def test_rules_have_cwe_ids(self):
        """All rules should have CWE IDs."""
        scanner = ClassicASPScanner()
        for rule in scanner.rules:
            assert "cwe_ids" in rule
            assert len(rule["cwe_ids"]) > 0

    def test_is_always_available(self):
        """Custom scanner should always be available."""
        scanner = ClassicASPScanner()
        assert scanner.is_available() is True


# =============================================================================
# ORCHESTRATOR TESTS
# =============================================================================


class TestSecurityScanOrchestrator:
    """Tests for security scan orchestrator."""

    def test_orchestrator_creation(self):
        """Should create orchestrator."""
        orchestrator = create_security_orchestrator()
        assert orchestrator is not None

    def test_detect_languages(self, tmp_path):
        """Should detect languages from file extensions."""
        # Create test files
        (tmp_path / "test.py").write_text("print('hello')")
        (tmp_path / "test.js").write_text("console.log('hello')")
        (tmp_path / "test.go").write_text("package main")

        orchestrator = create_security_orchestrator()
        languages = orchestrator.detect_languages(tmp_path)

        assert "python" in languages
        assert "javascript" in languages
        assert "go" in languages

    def test_get_available_scanners(self):
        """Should return list of available scanners."""
        orchestrator = create_security_orchestrator()
        available = orchestrator.get_available_scanners()

        # Custom ASP scanner should always be available
        assert ScannerType.CUSTOM_ASP in available


# =============================================================================
# SARIF PARSER TESTS
# =============================================================================


class TestSarifParser:
    """Tests for SARIF parser."""

    def test_parser_creation(self):
        """Should create parser with scanner type."""
        parser = SarifParser(ScannerType.BANDIT)
        assert parser.scanner_type == ScannerType.BANDIT

    def test_parse_minimal_sarif(self):
        """Should parse minimal SARIF structure."""
        parser = SarifParser(ScannerType.BANDIT)

        sarif_data = {
            "version": "2.1.0",
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "Bandit",
                            "version": "1.7.0",
                            "rules": [],
                        }
                    },
                    "results": [],
                }
            ],
        }

        sarif_log = parser.parse_json(sarif_data)

        assert sarif_log.version == "2.1.0"
        assert len(sarif_log.runs) == 1
        assert sarif_log.runs[0].tool_name == "Bandit"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
