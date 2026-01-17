"""
Tests for Fase 36 CryptoErrorDetector.

Tests cover all 12 cryptographic vulnerability detection rules:
- CR001-CR003: Hardcoded keys/passwords/API keys
- CR004-CR007: Weak algorithms (MD5, SHA1, DES, ECB)
- CR008: Weak random for security
- CR009: Timing-vulnerable comparison
- CR010-CR012: Certificate and TLS issues
"""

import pytest
from pathlib import Path

from app.services.security_scanner.adapters.crypto_error_detector import (
    CryptoErrorDetector,
    CryptoRule,
    CRYPTO_RULES,
    create_crypto_error_detector,
)
from app.services.security_scanner.models.findings import (
    ScannerType,
    Severity,
)


# =============================================================================
# SCANNER BASICS
# =============================================================================


class TestCryptoErrorDetectorBasics:
    """Tests for basic scanner properties."""

    def test_scanner_type(self):
        """Should return correct scanner type."""
        scanner = CryptoErrorDetector()
        assert scanner.scanner_type == ScannerType.CRYPTO_ERROR

    def test_is_always_available(self):
        """Custom scanner should always be available."""
        scanner = CryptoErrorDetector()
        assert scanner.is_available() is True

    def test_scanner_version(self):
        """Should return version string."""
        scanner = CryptoErrorDetector()
        assert scanner.get_scanner_version() == "1.0.0"

    def test_has_12_rules(self):
        """Should have 12 cryptographic detection rules."""
        assert len(CRYPTO_RULES) == 12

    def test_supported_languages(self):
        """Should support multiple languages."""
        scanner = CryptoErrorDetector()
        languages = scanner.supported_languages
        assert "python" in languages
        assert "javascript" in languages
        assert "java" in languages
        assert "csharp" in languages
        assert "cpp" in languages
        assert "go" in languages

    def test_supported_extensions(self):
        """Should support expected file extensions."""
        scanner = CryptoErrorDetector()
        extensions = scanner.supported_extensions
        assert ".py" in extensions
        assert ".js" in extensions
        assert ".java" in extensions
        assert ".cs" in extensions
        assert ".go" in extensions

    def test_factory_function(self):
        """Factory function should create scanner instance."""
        scanner = create_crypto_error_detector()
        assert isinstance(scanner, CryptoErrorDetector)

    def test_rules_have_cwe_ids(self):
        """All rules should have CWE IDs."""
        for rule in CRYPTO_RULES:
            assert len(rule.cwe_ids) > 0, f"Rule {rule.id} has no CWE IDs"

    def test_rules_have_fix_suggestions(self):
        """All rules should have fix suggestions."""
        for rule in CRYPTO_RULES:
            assert rule.fix_suggestion, f"Rule {rule.id} has no fix suggestion"


# =============================================================================
# CR001-CR003: HARDCODED CREDENTIALS
# =============================================================================


class TestHardcodedCredentials:
    """Tests for hardcoded credentials detection."""

    @pytest.mark.asyncio
    async def test_detect_hardcoded_encryption_key_python(self, tmp_path):
        """Should detect hardcoded encryption key in Python."""
        test_file = tmp_path / "crypto.py"
        test_file.write_text('''
encryption_key = "ThisIsAVeryLongSecretKey12345"
cipher = AES.new(encryption_key, AES.MODE_GCM)
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        key_finding = next((f for f in result.findings if f.rule_id == "CR001"), None)
        assert key_finding is not None
        assert "CWE-321" in key_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_hardcoded_password_javascript(self, tmp_path):
        """Should detect hardcoded password in JavaScript."""
        test_file = tmp_path / "auth.js"
        test_file.write_text('''
const password = "SuperSecretPassword123";
const db = connectDb(user, password);
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        pwd_finding = next((f for f in result.findings if f.rule_id == "CR002"), None)
        assert pwd_finding is not None
        assert "CWE-798" in pwd_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_hardcoded_api_key_java(self, tmp_path):
        """Should detect hardcoded API key in Java."""
        test_file = tmp_path / "Config.java"
        test_file.write_text('''
public class Config {
    String apiKey = "api_key_FAKE_TEST_1234567890abcdef";
}
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        api_finding = next((f for f in result.findings if f.rule_id == "CR003"), None)
        assert api_finding is not None

    @pytest.mark.asyncio
    async def test_filter_placeholder_password(self, tmp_path):
        """Should not flag placeholder passwords."""
        test_file = tmp_path / "example.py"
        test_file.write_text('''
password = "your_password_here"
password = "example_password"
password = "xxxxxxxxxxxxxxx"
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        # Should be filtered as false positives
        pwd_findings = [f for f in result.findings if f.rule_id == "CR002"]
        assert len(pwd_findings) == 0


# =============================================================================
# CR004-CR007: WEAK ALGORITHMS
# =============================================================================


class TestWeakAlgorithms:
    """Tests for weak cryptographic algorithm detection."""

    @pytest.mark.asyncio
    async def test_detect_md5_python(self, tmp_path):
        """Should detect MD5 usage in Python."""
        test_file = tmp_path / "hash.py"
        test_file.write_text('''
import hashlib
digest = hashlib.md5(data.encode()).hexdigest()
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        md5_finding = next((f for f in result.findings if f.rule_id == "CR004"), None)
        assert md5_finding is not None
        assert "CWE-328" in md5_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_md5_javascript(self, tmp_path):
        """Should detect MD5 usage in JavaScript."""
        test_file = tmp_path / "hash.js"
        test_file.write_text('''
const hash = crypto.createHash('md5').update(data).digest('hex');
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        md5_finding = next((f for f in result.findings if f.rule_id == "CR004"), None)
        assert md5_finding is not None

    @pytest.mark.asyncio
    async def test_detect_sha1_java(self, tmp_path):
        """Should detect SHA1 usage in Java."""
        test_file = tmp_path / "Hash.java"
        test_file.write_text('''
MessageDigest md = MessageDigest.getInstance("SHA-1");
byte[] digest = md.digest(data);
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        sha1_finding = next((f for f in result.findings if f.rule_id == "CR005"), None)
        assert sha1_finding is not None
        assert "CWE-328" in sha1_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_des_csharp(self, tmp_path):
        """Should detect DES usage in C#."""
        test_file = tmp_path / "Crypto.cs"
        test_file.write_text('''
var des = new DESCryptoServiceProvider();
var encryptor = des.CreateEncryptor();
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        des_finding = next((f for f in result.findings if f.rule_id == "CR006"), None)
        assert des_finding is not None
        assert "CWE-327" in des_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_ecb_mode_python(self, tmp_path):
        """Should detect ECB mode usage in Python."""
        test_file = tmp_path / "encrypt.py"
        test_file.write_text('''
from Crypto.Cipher import AES
cipher = AES.new(key, AES.MODE_ECB)
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        ecb_finding = next((f for f in result.findings if f.rule_id == "CR007"), None)
        assert ecb_finding is not None


# =============================================================================
# CR008: WEAK RANDOM
# =============================================================================


class TestWeakRandom:
    """Tests for weak random number generator detection."""

    @pytest.mark.asyncio
    async def test_detect_weak_random_python_with_context(self, tmp_path):
        """Should detect weak random in security context."""
        test_file = tmp_path / "token.py"
        test_file.write_text('''
import random

def generate_token():
    # Generate session token
    token = ''.join(random.choice(chars) for _ in range(32))
    return token
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        rand_finding = next((f for f in result.findings if f.rule_id == "CR008"), None)
        assert rand_finding is not None
        assert "CWE-330" in rand_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_math_random_javascript_with_context(self, tmp_path):
        """Should detect Math.random() in security context."""
        test_file = tmp_path / "auth.js"
        test_file.write_text('''
function generateSecretKey() {
    let key = '';
    for (let i = 0; i < 32; i++) {
        key += Math.random().toString(36).charAt(2);
    }
    return key;
}
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        rand_finding = next((f for f in result.findings if f.rule_id == "CR008"), None)
        assert rand_finding is not None


# =============================================================================
# CR009: TIMING ATTACK
# =============================================================================


class TestTimingAttack:
    """Tests for timing-vulnerable comparison detection."""

    @pytest.mark.asyncio
    async def test_detect_timing_vulnerable_comparison_python(self, tmp_path):
        """Should detect timing-vulnerable comparison in Python."""
        test_file = tmp_path / "auth.py"
        test_file.write_text('''
def verify_token(stored_token, received_token):
    if stored_token == received_token:
        return True
    return False
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        # This should be detected because 'token' is in context
        assert len(result.findings) >= 1
        timing_finding = next((f for f in result.findings if f.rule_id == "CR009"), None)
        assert timing_finding is not None
        assert "CWE-208" in timing_finding.cwe_ids


# =============================================================================
# CR010-CR012: CERTIFICATE/TLS ISSUES
# =============================================================================


class TestCertificateIssues:
    """Tests for certificate and TLS issue detection."""

    @pytest.mark.asyncio
    async def test_detect_disabled_cert_validation_python(self, tmp_path):
        """Should detect disabled certificate validation in Python."""
        test_file = tmp_path / "http.py"
        test_file.write_text('''
import requests
response = requests.get(url, verify=False)
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        cert_finding = next((f for f in result.findings if f.rule_id == "CR010"), None)
        assert cert_finding is not None
        assert "CWE-295" in cert_finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_disabled_cert_validation_javascript(self, tmp_path):
        """Should detect disabled certificate validation in JavaScript."""
        test_file = tmp_path / "http.js"
        test_file.write_text('''
const https = require('https');
const options = {
    hostname: 'example.com',
    rejectUnauthorized: false
};
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        cert_finding = next((f for f in result.findings if f.rule_id == "CR010"), None)
        assert cert_finding is not None

    @pytest.mark.asyncio
    async def test_detect_insecure_skip_verify_go(self, tmp_path):
        """Should detect InsecureSkipVerify in Go."""
        test_file = tmp_path / "http.go"
        test_file.write_text('''
package main

import "crypto/tls"

func main() {
    config := &tls.Config{InsecureSkipVerify: true}
}
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_detect_weak_tls_version_java(self, tmp_path):
        """Should detect weak TLS version in Java."""
        test_file = tmp_path / "Ssl.java"
        test_file.write_text('''
SSLContext ctx = SSLContext.getInstance("TLSv1");
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        tls_finding = next((f for f in result.findings if f.rule_id == "CR012"), None)
        assert tls_finding is not None
        assert "CWE-326" in tls_finding.cwe_ids


# =============================================================================
# DIRECTORY SCANNING
# =============================================================================


class TestDirectoryScanning:
    """Tests for scanning directories."""

    @pytest.mark.asyncio
    async def test_scan_directory(self, tmp_path):
        """Should scan entire directory recursively."""
        # Create multiple files with different vulnerabilities
        (tmp_path / "crypto.py").write_text('import hashlib; hashlib.md5(data)')
        (tmp_path / "auth.js").write_text('const password = "hardcoded12345678";')

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "config.java").write_text('MessageDigest.getInstance("MD5");')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(tmp_path)

        assert result.files_scanned >= 3
        assert len(result.findings) >= 2

    @pytest.mark.asyncio
    async def test_scan_no_vulnerabilities(self, tmp_path):
        """Should handle clean files."""
        test_file = tmp_path / "secure.py"
        test_file.write_text('''
import secrets
import hashlib

token = secrets.token_hex(32)
digest = hashlib.sha256(data.encode()).hexdigest()
''')

        scanner = CryptoErrorDetector()
        result = await scanner.scan(test_file)

        assert result.files_scanned == 1
        # Should have no findings for this secure code
        assert len([f for f in result.findings if f.rule_id in ["CR004", "CR005", "CR008"]]) == 0


# =============================================================================
# RULES SUMMARY
# =============================================================================


class TestRulesSummary:
    """Tests for rules summary functionality."""

    def test_get_rules_summary(self):
        """Should return structured rules summary."""
        scanner = CryptoErrorDetector()
        summary = scanner.get_rules_summary()

        assert summary["total_rules"] == 12
        assert len(summary["rules"]) == 12
        assert "supported_languages" in summary
        assert len(summary["supported_languages"]) >= 6

        # Verify rule structure
        for rule in summary["rules"]:
            assert "id" in rule
            assert "title" in rule
            assert "severity" in rule
            assert "cwe_ids" in rule
            assert "category" in rule


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
