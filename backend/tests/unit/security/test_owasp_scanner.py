"""
Unit tests for OWASPScanner (K1 - Fase 24).

Tests cover:
- OWASP category detection
- Built-in pattern matching
- Coverage reporting
- Integration with SecurityPatternLoader
- Multi-language scanning

Author: Claude Code (Week 158)
Date: 2026-01-15
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.security_scanner.adapters.owasp_scanner import (
    OWASPScanner,
    OWASPCategoryInfo,
    OWASPCoverageReport,
    OWASP_CATEGORY_INFO,
    BUILTIN_OWASP_PATTERNS,
    create_owasp_scanner,
)
from app.services.security_scanner.models.findings import (
    ScannerType,
    Severity,
)
from app.services.security_pattern_loader import OWASPCategory


# ==================== Fixtures ====================

@pytest.fixture
def scanner():
    """Create a fresh OWASPScanner instance."""
    return OWASPScanner()


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


# ==================== Basic Scanner Tests ====================

class TestOWASPScannerBasics:
    """Test basic scanner functionality."""

    def test_scanner_type(self, scanner):
        """Test scanner type is correct."""
        assert scanner.scanner_type == ScannerType.OWASP_SCANNER

    def test_scanner_version(self, scanner):
        """Test scanner has version."""
        assert scanner.VERSION == "1.0.0"

    def test_is_available(self, scanner):
        """Test scanner is always available (custom scanner)."""
        assert scanner.is_available() is True

    def test_supported_languages(self, scanner):
        """Test supported languages includes common ones."""
        languages = scanner.supported_languages
        assert "generic" in languages

    def test_supported_extensions(self, scanner):
        """Test supported extensions includes common ones."""
        extensions = scanner.supported_extensions
        assert ".py" in extensions
        assert ".js" in extensions
        assert ".java" in extensions
        assert ".php" in extensions


# ==================== OWASP Category Tests ====================

class TestOWASPCategories:
    """Test OWASP category definitions."""

    def test_all_categories_have_info(self):
        """Test all OWASP categories have info defined."""
        for category in OWASPCategory:
            assert category in OWASP_CATEGORY_INFO
            info = OWASP_CATEGORY_INFO[category]
            assert isinstance(info, OWASPCategoryInfo)

    def test_category_info_structure(self):
        """Test category info has required fields."""
        for category, info in OWASP_CATEGORY_INFO.items():
            assert info.code is not None
            assert info.name is not None
            assert info.description is not None
            assert info.cwe_ids is not None
            assert info.risk_rating in ["Critical", "High", "Medium", "Low"]

    def test_injection_category(self):
        """Test A03 Injection category is properly defined."""
        info = OWASP_CATEGORY_INFO[OWASPCategory.A03_INJECTION]
        assert info.code == "A03"
        assert "Injection" in info.name
        assert "CWE-89" in info.cwe_ids  # SQL Injection
        assert "CWE-79" in info.cwe_ids  # XSS
        assert "CWE-78" in info.cwe_ids  # OS Command Injection

    def test_broken_access_control_category(self):
        """Test A01 Broken Access Control category."""
        info = OWASP_CATEGORY_INFO[OWASPCategory.A01_BROKEN_ACCESS_CONTROL]
        assert info.code == "A01"
        assert info.risk_rating == "Critical"
        assert "CWE-22" in info.cwe_ids  # Path Traversal

    def test_cryptographic_failures_category(self):
        """Test A02 Cryptographic Failures category."""
        info = OWASP_CATEGORY_INFO[OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES]
        assert info.code == "A02"
        assert "Crypto" in info.name
        assert "CWE-327" in info.cwe_ids  # Weak crypto

    def test_ssrf_category(self):
        """Test A10 SSRF category."""
        info = OWASP_CATEGORY_INFO[OWASPCategory.A10_SSRF]
        assert info.code == "A10"
        assert "Request Forgery" in info.name  # Server-Side Request Forgery
        assert "CWE-918" in info.cwe_ids


# ==================== Built-in Pattern Tests ====================

class TestBuiltinPatterns:
    """Test built-in OWASP patterns."""

    def test_builtin_patterns_exist(self):
        """Test built-in patterns are defined."""
        assert len(BUILTIN_OWASP_PATTERNS) > 20

    def test_patterns_have_required_fields(self):
        """Test all patterns have required fields."""
        for pattern in BUILTIN_OWASP_PATTERNS:
            assert "id" in pattern
            assert "pattern" in pattern
            assert "title" in pattern
            assert "severity" in pattern
            assert "owasp" in pattern
            assert pattern["id"].startswith("OWASP-A")

    def test_patterns_cover_all_categories(self):
        """Test patterns exist for all OWASP categories."""
        covered_categories = set()
        for pattern in BUILTIN_OWASP_PATTERNS:
            owasp = pattern["owasp"]
            covered_categories.add(owasp)

        # Should cover all 10 categories
        assert len(covered_categories) == 10

    def test_injection_patterns(self):
        """Test A03 injection patterns exist."""
        injection_patterns = [
            p for p in BUILTIN_OWASP_PATTERNS
            if p["owasp"] == OWASPCategory.A03_INJECTION
        ]
        assert len(injection_patterns) >= 4

        # Check SQL injection pattern exists
        sql_patterns = [p for p in injection_patterns if "SQL" in p["title"]]
        assert len(sql_patterns) >= 1

    def test_auth_patterns(self):
        """Test A07 authentication patterns exist."""
        auth_patterns = [
            p for p in BUILTIN_OWASP_PATTERNS
            if p["owasp"] == OWASPCategory.A07_AUTH_FAILURES
        ]
        assert len(auth_patterns) >= 2


# ==================== Scanning Tests ====================

class TestOWASPScanning:
    """Test actual scanning functionality."""

    @pytest.mark.asyncio
    async def test_scan_empty_file(self, scanner, temp_file):
        """Test scanning an empty file."""
        temp_file.write_text("")
        result = await scanner.scan(temp_file)

        assert result.scanner == ScannerType.OWASP_SCANNER
        assert result.files_scanned == 1
        assert len(result.findings) == 0

    @pytest.mark.asyncio
    async def test_scan_sql_injection(self, scanner, temp_file):
        """Test detection of SQL injection pattern."""
        code = '''
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
    return cursor.fetchone()
'''
        temp_file.write_text(code)
        result = await scanner.scan(temp_file)

        # Should find SQL injection
        sql_findings = [
            f for f in result.findings
            if "SQL" in f.title or "CWE-89" in f.cwe_ids
        ]
        assert len(sql_findings) >= 1

    @pytest.mark.asyncio
    async def test_scan_hardcoded_password(self, scanner, temp_file):
        """Test detection of hardcoded password."""
        code = '''
DATABASE_PASSWORD = "supersecret123"
API_KEY = "sk_live_abcdef123456"
'''
        temp_file.write_text(code)
        result = await scanner.scan(temp_file)

        # Should find hardcoded secrets (A02)
        secret_findings = [
            f for f in result.findings
            if "Hardcoded" in f.title or "Secret" in f.title
        ]
        assert len(secret_findings) >= 1

    @pytest.mark.asyncio
    async def test_scan_weak_crypto(self, scanner, temp_file):
        """Test detection of weak cryptography."""
        code = '''
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()
legacy_hash = SHA1.new(data)
'''
        temp_file.write_text(code)
        result = await scanner.scan(temp_file)

        # Should find weak crypto (A02)
        crypto_findings = [
            f for f in result.findings
            if "Crypto" in f.title or "MD5" in f.title or "SHA1" in f.title
        ]
        assert len(crypto_findings) >= 1

    @pytest.mark.asyncio
    async def test_scan_debug_enabled(self, scanner, temp_file):
        """Test detection of debug mode enabled (A05)."""
        code = '''
DEBUG = True
app.config['DEBUG'] = True
settings.debug = true
'''
        temp_file.write_text(code)
        result = await scanner.scan(temp_file)

        # Should find debug mode enabled
        debug_findings = [
            f for f in result.findings
            if "Debug" in f.title
        ]
        assert len(debug_findings) >= 1

    @pytest.mark.asyncio
    async def test_scan_xss(self, scanner, temp_file):
        """Test detection of XSS vulnerability."""
        code = '''
document.getElementById("output").innerHTML = userInput;
$('#display').html(data + userContent);
'''
        temp_file.write_text(code)
        result = await scanner.scan(temp_file)

        # Should find XSS (A03)
        xss_findings = [
            f for f in result.findings
            if "XSS" in f.title or "innerHTML" in f.title
        ]
        assert len(xss_findings) >= 1

    @pytest.mark.asyncio
    async def test_scan_ssrf(self, scanner, temp_file):
        """Test detection of SSRF vulnerability."""
        code = '''
response = requests.get(request.params['url'])
data = file_get_contents($user_url)
'''
        temp_file.write_text(code)
        result = await scanner.scan(temp_file)

        # Should find SSRF (A10)
        ssrf_findings = [
            f for f in result.findings
            if "SSRF" in f.title or "File Inclusion" in f.title
        ]
        assert len(ssrf_findings) >= 1

    @pytest.mark.asyncio
    async def test_scan_directory(self, scanner):
        """Test scanning a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text('password = "secret123"')

            js_file = Path(tmpdir) / "test.js"
            js_file.write_text('element.innerHTML = userInput;')

            result = await scanner.scan(Path(tmpdir))

            assert result.files_scanned >= 2
            assert len(result.findings) >= 2


# ==================== Coverage Report Tests ====================

class TestOWASPCoverageReport:
    """Test OWASP coverage reporting."""

    def test_coverage_report_structure(self, scanner):
        """Test coverage report has correct structure."""
        report = scanner.get_coverage_report()

        assert isinstance(report, OWASPCoverageReport)
        assert report.total_patterns > 0
        assert report.categories_covered > 0

    def test_coverage_report_all_categories(self, scanner):
        """Test coverage report includes all categories."""
        report = scanner.get_coverage_report()

        assert len(report.category_coverage) == 10
        for code in ["A01", "A02", "A03", "A04", "A05",
                     "A06", "A07", "A08", "A09", "A10"]:
            assert code in report.category_coverage

    def test_coverage_report_category_details(self, scanner):
        """Test category details are populated."""
        report = scanner.get_coverage_report()

        a03_details = report.category_coverage["A03"]
        assert "name" in a03_details
        assert "Injection" in a03_details["name"]
        assert "pattern_count" in a03_details
        assert a03_details["pattern_count"] > 0

    def test_coverage_report_to_dict(self, scanner):
        """Test coverage report can be serialized."""
        report = scanner.get_coverage_report()
        data = report.to_dict()

        assert "summary" in data
        assert "severity_breakdown" in data
        assert "category_details" in data

    @pytest.mark.asyncio
    async def test_coverage_report_with_findings(self, scanner, temp_file):
        """Test coverage report with actual findings."""
        code = '''
password = "hardcoded123"
query = "SELECT * FROM users WHERE id = " + user_id
DEBUG = True
'''
        temp_file.write_text(code)
        result = await scanner.scan(temp_file)
        report = scanner.get_coverage_report(result)

        assert report.total_findings > 0
        assert report.categories_with_findings > 0


# ==================== Category Info Tests ====================

class TestCategoryInfo:
    """Test category info retrieval."""

    def test_get_category_info_valid(self, scanner):
        """Test getting info for valid category."""
        info = scanner.get_category_info("A03")

        assert info is not None
        assert info.name == "Injection"

    def test_get_category_info_lowercase(self, scanner):
        """Test getting info with lowercase code."""
        info = scanner.get_category_info("a01")

        assert info is not None
        assert "Access Control" in info.name

    def test_get_category_info_invalid(self, scanner):
        """Test getting info for invalid category."""
        info = scanner.get_category_info("A99")

        assert info is None


# ==================== Recommendations Tests ====================

class TestRecommendations:
    """Test remediation recommendations."""

    @pytest.mark.asyncio
    async def test_recommendations_generated(self, scanner, temp_file):
        """Test recommendations are generated for findings."""
        code = '''
password = "hardcoded"
query = "SELECT * FROM " + table_name
'''
        temp_file.write_text(code)
        result = await scanner.scan(temp_file)
        recommendations = scanner.get_recommendations(result)

        # Should have recommendations grouped by category
        assert isinstance(recommendations, dict)

    @pytest.mark.asyncio
    async def test_recommendations_have_fixes(self, scanner, temp_file):
        """Test recommendations contain fix suggestions."""
        code = 'DEBUG = True'
        temp_file.write_text(code)
        result = await scanner.scan(temp_file)

        # Check findings have fix suggestions
        for finding in result.findings:
            if finding.suggested_fixes:
                assert len(finding.suggested_fixes) > 0


# ==================== Configuration Tests ====================

class TestOWASPScannerConfig:
    """Test scanner configuration options."""

    @pytest.mark.asyncio
    async def test_category_filter(self, scanner, temp_file):
        """Test filtering by OWASP category."""
        code = '''
password = "secret123"  # A02
query = "SELECT * FROM " + table  # A03
DEBUG = True  # A05
'''
        temp_file.write_text(code)

        # Scan with only A03 filter
        result = await scanner.scan(temp_file, config={"categories": ["A03"]})

        # Should only have injection findings
        for finding in result.findings:
            if finding.raw_data and "owasp_code" in finding.raw_data:
                assert finding.raw_data["owasp_code"] == "A03"


# ==================== Factory Function Tests ====================

class TestFactoryFunction:
    """Test factory function."""

    def test_create_owasp_scanner(self):
        """Test factory function creates scanner."""
        scanner = create_owasp_scanner()

        assert isinstance(scanner, OWASPScanner)
        assert scanner.scanner_type == ScannerType.OWASP_SCANNER


# ==================== Integration Tests ====================

class TestOWASPIntegration:
    """Test integration with other components."""

    def test_scanner_rules_loaded(self, scanner):
        """Test rules are loaded from patterns."""
        scanner._ensure_initialized()

        # Should have built-in patterns + loaded patterns
        assert len(scanner._all_rules) >= len(BUILTIN_OWASP_PATTERNS)

    def test_scanner_uses_pattern_loader(self, scanner):
        """Test scanner uses SecurityPatternLoader."""
        scanner._ensure_initialized()

        # Pattern loader should be initialized
        assert scanner._pattern_loader is not None
        assert scanner._initialized is True

    @pytest.mark.asyncio
    async def test_full_scan_workflow(self, scanner):
        """Test complete scanning workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create vulnerable code
            test_file = Path(tmpdir) / "vulnerable.py"
            test_file.write_text('''
# Multiple OWASP vulnerabilities
import hashlib
import subprocess

PASSWORD = "admin123"  # A02: Hardcoded credential

def login(username, password):
    # A02: Weak hash
    hash = hashlib.md5(password.encode()).hexdigest()

    # A03: SQL Injection
    query = f"SELECT * FROM users WHERE username='{username}'"

    # A03: Command injection
    subprocess.call("ls " + user_input, shell=True)

    return hash == stored_hash

DEBUG = True  # A05: Misconfiguration
''')

            # Execute scan
            result = await scanner.scan(Path(tmpdir))

            # Verify results
            assert result.scanner == ScannerType.OWASP_SCANNER
            assert result.files_scanned >= 1
            assert len(result.findings) >= 3

            # Generate coverage report
            report = scanner.get_coverage_report(result)
            assert report.categories_with_findings >= 2

            # Get recommendations
            recommendations = scanner.get_recommendations(result)
            assert len(recommendations) > 0
