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
    # Secret Scanner (K3 - Fase 24)
    SecretScanner,
    SecretPattern,
    SecretType,
    FalsePositiveFilter,
    EntropyAnalyzer,
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


# =============================================================================
# SECRET SCANNER TESTS (K3 - Fase 24)
# =============================================================================


class TestSecretScanner:
    """Tests for K3 Secret Detection Scanner."""

    def test_scanner_type(self):
        """Should return correct scanner type."""
        scanner = SecretScanner()
        assert scanner.scanner_type == ScannerType.SECRET_SCANNER

    def test_supported_languages(self):
        """Should support many languages."""
        scanner = SecretScanner()
        assert "python" in scanner.supported_languages
        assert "javascript" in scanner.supported_languages
        assert "yaml" in scanner.supported_languages
        assert "json" in scanner.supported_languages
        assert "terraform" in scanner.supported_languages

    def test_supported_extensions(self):
        """Should support many extensions."""
        scanner = SecretScanner()
        assert ".py" in scanner.supported_extensions
        assert ".js" in scanner.supported_extensions
        assert ".yaml" in scanner.supported_extensions
        assert ".env" in scanner.supported_extensions

    def test_is_always_available(self):
        """Custom scanner should always be available."""
        scanner = SecretScanner()
        assert scanner.is_available() is True

    def test_has_50_plus_patterns(self):
        """Should have 50+ secret detection patterns."""
        scanner = SecretScanner()
        assert len(scanner.patterns) >= 50

    def test_patterns_have_cwe_798(self):
        """All patterns should map to CWE-798 (hardcoded credentials)."""
        scanner = SecretScanner()
        for rule in scanner.rules:
            assert "CWE-798" in rule["cwe_ids"]


class TestSecretType:
    """Tests for SecretType enum."""

    def test_cloud_provider_types(self):
        """Should have cloud provider secret types."""
        assert SecretType.AWS_ACCESS_KEY.value == "aws_access_key"
        assert SecretType.AZURE_STORAGE_KEY.value == "azure_storage_key"
        assert SecretType.GCP_API_KEY.value == "gcp_api_key"

    def test_version_control_types(self):
        """Should have version control secret types."""
        assert SecretType.GITHUB_TOKEN.value == "github_token"
        assert SecretType.GITLAB_TOKEN.value == "gitlab_token"

    def test_database_types(self):
        """Should have database secret types."""
        assert SecretType.DATABASE_URL.value == "database_url"
        assert SecretType.MONGODB_URI.value == "mongodb_uri"

    def test_crypto_types(self):
        """Should have cryptographic key types."""
        assert SecretType.PRIVATE_KEY.value == "private_key"
        assert SecretType.RSA_PRIVATE_KEY.value == "rsa_private_key"
        assert SecretType.SSH_PRIVATE_KEY.value == "ssh_private_key"


class TestEntropyAnalyzer:
    """Tests for entropy-based secret detection."""

    def test_low_entropy_string(self):
        """Low entropy strings should not be flagged."""
        analyzer = EntropyAnalyzer(threshold=4.5)
        text = "aaaaaaaaaaaaaaaa"  # Very low entropy
        is_high, entropy = analyzer.is_high_entropy(text)
        assert is_high is False
        assert entropy < 1.0

    def test_high_entropy_string(self):
        """High entropy strings should be flagged."""
        analyzer = EntropyAnalyzer(threshold=4.0)
        text = "aB3$xY9#mK2@pL5^"  # High entropy (random-looking)
        is_high, entropy = analyzer.is_high_entropy(text)
        assert is_high is True
        assert entropy >= 4.0

    def test_api_key_like_string(self):
        """API key-like strings should have high entropy."""
        analyzer = EntropyAnalyzer(threshold=4.0)
        text = "sk_live_51H5q3rKmXpTqJHVkL9Zf"  # Stripe-like key
        is_high, entropy = analyzer.is_high_entropy(text)
        assert is_high is True

    def test_short_string_not_flagged(self):
        """Short strings should not be flagged."""
        analyzer = EntropyAnalyzer()
        text = "abc123"  # Too short
        is_high, _ = analyzer.is_high_entropy(text, min_length=16)
        assert is_high is False


class TestFalsePositiveFilter:
    """Tests for false positive filtering."""

    def test_filter_env_variable_reference(self):
        """Should filter environment variable references."""
        filter = FalsePositiveFilter()
        pattern = SecretPattern(
            secret_type=SecretType.API_KEY,
            pattern="",
            severity=Severity.MEDIUM,
            title="",
            description="",
        )

        is_fp, reason = filter.is_false_positive(
            matched_text="some_api_key",
            line="api_key = process.env.API_KEY",
            file_path="/app/config.js",
            pattern=pattern,
        )
        assert is_fp is True
        assert "Environment variable" in reason

    def test_filter_test_file(self):
        """Should filter test files."""
        filter = FalsePositiveFilter()
        pattern = SecretPattern(
            secret_type=SecretType.PASSWORD,
            pattern="",
            severity=Severity.HIGH,
            title="",
            description="",
        )

        is_fp, reason = filter.is_false_positive(
            matched_text="test_password",
            line="password = 'test_password'",
            file_path="/tests/test_auth.py",
            pattern=pattern,
        )
        assert is_fp is True
        assert "Test file" in reason

    def test_filter_example_value(self):
        """Should filter example/placeholder values."""
        filter = FalsePositiveFilter()
        pattern = SecretPattern(
            secret_type=SecretType.API_KEY,
            pattern="",
            severity=Severity.MEDIUM,
            title="",
            description="",
        )

        is_fp, reason = filter.is_false_positive(
            matched_text="your_api_key_here",
            line="api_key = 'your_api_key_here'",
            file_path="/app/config.example.py",
            pattern=pattern,
        )
        assert is_fp is True
        assert "Documentation" in reason

    def test_real_secret_not_filtered(self):
        """Real secrets should not be filtered."""
        filter = FalsePositiveFilter()
        pattern = SecretPattern(
            secret_type=SecretType.AWS_ACCESS_KEY,
            pattern="",
            severity=Severity.CRITICAL,
            title="",
            description="",
        )

        # Use realistic key format (not with EXAMPLE which triggers doc filter)
        is_fp, _ = filter.is_false_positive(
            matched_text="AKIAIOSFODNN7REALKEY1",
            line="aws_access_key = 'AKIAIOSFODNN7REALKEY1'",
            file_path="/app/deploy.py",
            pattern=pattern,
        )
        assert is_fp is False


class TestSecretScannerPatterns:
    """Tests for specific secret patterns."""

    def test_aws_access_key_pattern(self):
        """Should detect AWS access key IDs."""
        import re
        pattern = r"(?:^|[^A-Z0-9])((AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16})(?:[^A-Z0-9]|$)"

        # Valid AWS key
        match = re.search(pattern, "aws_key = 'AKIAIOSFODNN7EXAMPLE'")
        assert match is not None

        # Invalid (wrong prefix)
        match = re.search(pattern, "ABCD1234567890123456")
        assert match is None

    def test_github_token_pattern(self):
        """Should detect GitHub tokens."""
        import re
        pattern = r"gh[pousr]_[A-Za-z0-9_]{36,}"

        # Valid GitHub PAT
        match = re.search(pattern, "ghp_1234567890abcdefghijklmnopqrstuvwxyz12")
        assert match is not None

    def test_stripe_key_pattern(self):
        """Should detect Stripe API keys."""
        import re
        live_pattern = r"sk_live_[0-9a-zA-Z]{24,}"
        test_pattern = r"sk_test_[0-9a-zA-Z]{24,}"

        # Live key (fake pattern for testing - not a real key)
        match = re.search(live_pattern, "sk_live_" + "FAKE" * 6 + "1234")
        assert match is not None

        # Test key (fake pattern for testing - not a real key)
        match = re.search(test_pattern, "sk_test_" + "FAKE" * 6 + "5678")
        assert match is not None

    def test_private_key_pattern(self):
        """Should detect private keys."""
        import re
        pattern = r"-----BEGIN RSA PRIVATE KEY-----"

        match = re.search(pattern, "-----BEGIN RSA PRIVATE KEY-----\nMIIE...")
        assert match is not None


@pytest.mark.asyncio
class TestSecretScannerAsync:
    """Async tests for SecretScanner."""

    async def test_scan_file_with_secrets(self, tmp_path):
        """Should detect secrets in a file."""
        # Create file with hardcoded AWS key (using realistic format, not EXAMPLE)
        test_file = tmp_path / "config.py"
        test_file.write_text('''
AWS_ACCESS_KEY = "AKIAIOSFODNN7REALKEY1"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYREALKEYVAL"
''')

        scanner = SecretScanner()
        result = await scanner.scan(test_file)

        assert result.scanner == ScannerType.SECRET_SCANNER
        assert result.files_scanned == 1
        assert len(result.findings) >= 1

        # Check for AWS key finding
        aws_findings = [f for f in result.findings if "AWS" in f.title]
        assert len(aws_findings) >= 1

    async def test_scan_no_secrets(self, tmp_path):
        """Should not find secrets in clean file."""
        # Create clean file
        test_file = tmp_path / "clean.py"
        test_file.write_text('''
import os
API_KEY = os.environ.get("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
''')

        scanner = SecretScanner()
        result = await scanner.scan(test_file)

        # Should have no findings (env vars are filtered)
        assert len(result.findings) == 0

    async def test_scan_directory(self, tmp_path):
        """Should scan entire directory."""
        # Create multiple files
        (tmp_path / "config.py").write_text('API_KEY = "sk_live_51H5q3rKmXpTqJHVkL9Zf"')
        (tmp_path / "db.py").write_text('DATABASE_URL = os.environ["DB_URL"]')
        (tmp_path / "test_file.py").write_text('test_key = "AKIAIOSFODNN7EXAMPLE"')

        scanner = SecretScanner()
        result = await scanner.scan(tmp_path)

        # Should scan all files
        assert result.files_scanned >= 2

        # Should find secret in config.py but not in test file
        config_findings = [f for f in result.findings if "config.py" in f.location.file_path]
        assert len(config_findings) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
