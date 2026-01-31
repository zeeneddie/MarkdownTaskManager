"""
Obfuscation Detector - Code Obfuscation and Anti-Analysis Pattern Detection.

Fase 42: Detects obfuscated code patterns that may indicate malicious intent:

OBF-CONCAT: String concatenation building dangerous function names
OBF-ENCODE: Base64/hex encoding used to hide dangerous calls
OBF-UNICODE: Unicode escape sequences forming dangerous identifiers
OBF-CHARCODE: Character code arithmetic building strings
OBF-ENTROPY: High Shannon entropy in identifiers (minified/obfuscated code)

Multi-language support: JavaScript, TypeScript, Python, Java
"""

import re
import math
import base64
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timezone

from ..models.findings import (
    SecurityFinding, ScanResult, Severity, ScannerType, Location, SuggestedFix,
)
from .base import BaseScanner

logger = logging.getLogger(__name__)


# =============================================================================
# DANGEROUS FUNCTIONS SET
# =============================================================================

DANGEROUS_FUNCTIONS: Set[str] = {
    "eval", "exec", "system", "popen", "spawn",
    "innerHTML", "outerHTML", "Function", "setTimeout", "setInterval",
    "execSync", "child_process", "subprocess", "os.system",
    "Runtime.exec",
}


# =============================================================================
# LANGUAGE DEFINITIONS
# =============================================================================

@dataclass
class LanguageDefinition:
    """Definition of a programming language for scanning."""
    name: str
    extensions: Set[str]


SUPPORTED_LANGUAGES: Dict[str, LanguageDefinition] = {
    "javascript": LanguageDefinition(
        name="JavaScript",
        extensions={".js", ".jsx", ".mjs", ".cjs"},
    ),
    "typescript": LanguageDefinition(
        name="TypeScript",
        extensions={".ts", ".tsx"},
    ),
    "python": LanguageDefinition(
        name="Python",
        extensions={".py", ".pyw"},
    ),
    "java": LanguageDefinition(
        name="Java",
        extensions={".java", ".jsp"},
    ),
}


# =============================================================================
# OBFUSCATION RULES DATA STRUCTURE
# =============================================================================

@dataclass
class LanguagePattern:
    """Pattern for a specific language."""
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE


@dataclass
class ObfuscationRule:
    """An obfuscation detection rule with language-specific patterns."""
    id: str
    title: str
    description: str
    severity: Severity
    cwe_ids: List[str]
    category: str

    # Language-specific regex patterns
    patterns: Dict[str, LanguagePattern]

    # Fix suggestions
    fix_suggestion: str

    # Confidence level for this rule category (0.0 to 1.0)
    confidence: float = 0.5

    # False positive hints
    false_positive_patterns: List[str] = field(default_factory=list)


# =============================================================================
# OBF-CONCAT: STRING CONCATENATION OBFUSCATION RULES
# =============================================================================

CONCAT_RULES: List[ObfuscationRule] = [
    # OBF-CONCAT-001: JS string concat building dangerous function names
    ObfuscationRule(
        id="OBF-CONCAT-001",
        title="String concatenation building dangerous function name (JavaScript)",
        description=(
            "String concatenation is used to construct the name of a dangerous function "
            "such as eval or exec at runtime. This is a common obfuscation technique "
            "used by malware to evade static analysis tools that search for direct "
            "function references. The resulting string is typically passed to bracket "
            "notation (window['ev'+'al']) or used with Function constructor."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-94", "CWE-506"],
        category="obfuscation_concat",
        patterns={
            "javascript": LanguagePattern(
                r"""(?:"""
                r"""["']ev["']\s*\+\s*["']al["']"""        # "ev"+"al"
                r"""|["']ex["']\s*\+\s*["']ec["']"""        # "ex"+"ec"
                r"""|["']set["']\s*\+\s*["']Timeout["']"""  # "set"+"Timeout"
                r"""|["']set["']\s*\+\s*["']Interval["']""" # "set"+"Interval"
                r"""|["']Fun["']\s*\+\s*["']ction["']"""    # "Fun"+"ction"
                r"""|["']inner["']\s*\+\s*["']HTML["']"""   # "inner"+"HTML"
                r""")""",
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r"""(?:"""
                r"""["']ev["']\s*\+\s*["']al["']"""
                r"""|["']ex["']\s*\+\s*["']ec["']"""
                r"""|["']set["']\s*\+\s*["']Timeout["']"""
                r"""|["']set["']\s*\+\s*["']Interval["']"""
                r"""|["']Fun["']\s*\+\s*["']ction["']"""
                r"""|["']inner["']\s*\+\s*["']HTML["']"""
                r""")""",
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Remove string concatenation obfuscation and call functions directly. "
            "If the code legitimately needs dynamic dispatch, use a safe allowlist pattern."
        ),
        confidence=0.5,
        false_positive_patterns=[
            r'(?:test|spec|describe|it)\s*\(',
            r'^\s*(?://|/\*|\*)',
            r'(?:eslint|jshint|prettier)',
        ],
    ),

    # OBF-CONCAT-002: Python string concat building dangerous function names
    ObfuscationRule(
        id="OBF-CONCAT-002",
        title="String concatenation building dangerous function name (Python)",
        description=(
            "String concatenation is used to construct the name of a dangerous function "
            "in Python, such as eval or exec. This pattern is commonly seen in obfuscated "
            "Python payloads where getattr(builtins, 'ev'+'al') or similar constructs "
            "are used to dynamically resolve and invoke dangerous built-in functions."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-94", "CWE-506"],
        category="obfuscation_concat",
        patterns={
            "python": LanguagePattern(
                r"""(?:"""
                r"""["']ev["']\s*\+\s*["']al["']"""
                r"""|["']ex["']\s*\+\s*["']ec["']"""
                r"""|["']sy["']\s*\+\s*["']stem["']"""
                r"""|["']po["']\s*\+\s*["']pen["']"""
                r"""|["']subp["']\s*\+\s*["']rocess["']"""
                r"""|getattr\s*\([^,]+,\s*["'][a-z]{1,4}["']\s*\+"""
                r""")""",
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Remove string concatenation obfuscation and reference functions directly. "
            "Avoid using getattr with concatenated strings to resolve built-in functions."
        ),
        confidence=0.5,
        false_positive_patterns=[
            r'(?:test_|def\s+test|pytest|unittest)',
            r'^\s*#',
            r'\.join\s*\(\s*\[',
        ],
    ),

    # OBF-CONCAT-003: Array/list join building function names
    ObfuscationRule(
        id="OBF-CONCAT-003",
        title="Array join building dangerous function name",
        description=(
            "An array of single characters is joined to construct a dangerous function "
            "name. For example, ['e','v','a','l'].join('') produces 'eval'. This technique "
            "splits the function name across array elements to defeat simple string-matching "
            "detection tools."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-94", "CWE-506"],
        category="obfuscation_concat",
        patterns={
            "javascript": LanguagePattern(
                r"""\[\s*["'][a-zA-Z]["']\s*(?:,\s*["'][a-zA-Z]["']\s*){3,}\]\.join\s*\(\s*["']['"]?\s*\)""",
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r"""\[\s*["'][a-zA-Z]["']\s*(?:,\s*["'][a-zA-Z]["']\s*){3,}\]\.join\s*\(\s*["']['"]?\s*\)""",
                flags=re.MULTILINE,
            ),
            "python": LanguagePattern(
                r"""["']["']\.join\s*\(\s*\[\s*["'][a-zA-Z]["']\s*(?:,\s*["'][a-zA-Z]["']\s*){3,}\]\s*\)""",
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Replace array-join obfuscation with a direct string literal. "
            "If this is test code verifying obfuscation detection, mark it accordingly."
        ),
        confidence=0.5,
        false_positive_patterns=[
            r'(?:test|spec|describe|it)\s*\(',
            r'^\s*(?://|#|/\*|\*)',
        ],
    ),
]


# =============================================================================
# OBF-ENCODE: BASE64 AND HEX ENCODING OBFUSCATION RULES
# =============================================================================

ENCODE_RULES: List[ObfuscationRule] = [
    # OBF-ENCODE-001: Base64 decode to dangerous strings (JavaScript)
    ObfuscationRule(
        id="OBF-ENCODE-001",
        title="Base64 decode potentially hiding dangerous function call (JavaScript)",
        description=(
            "The atob() function is used to decode a base64 string that may contain "
            "a dangerous function name or code payload. Malware commonly base64-encodes "
            "eval, exec, or entire script payloads to bypass static analysis. The decoded "
            "result is often passed to eval() or the Function constructor."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-94", "CWE-506"],
        category="obfuscation_encode",
        patterns={
            "javascript": LanguagePattern(
                r"""atob\s*\(\s*["'][A-Za-z0-9+/=]{4,}["']\s*\)""",
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r"""atob\s*\(\s*["'][A-Za-z0-9+/=]{4,}["']\s*\)""",
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Avoid decoding base64 strings to obtain function names or code. "
            "Use direct function references. If base64 is needed for data, "
            "ensure the decoded content is not executed."
        ),
        confidence=0.6,
        false_positive_patterns=[
            r'(?:test|spec|describe|it)\s*\(',
            r'^\s*(?://|/\*|\*)',
            r'(?:data:image|data:application)',
            r'(?:\.png|\.jpg|\.gif|\.svg|\.woff|\.ttf)',
        ],
    ),

    # OBF-ENCODE-002: Base64 decode (Python)
    ObfuscationRule(
        id="OBF-ENCODE-002",
        title="Base64 decode potentially hiding dangerous function call (Python)",
        description=(
            "base64.b64decode() is used to decode a string that may contain a dangerous "
            "function name or executable code. This is a common pattern in obfuscated "
            "Python malware where payloads are base64-encoded to avoid detection, then "
            "decoded and passed to exec() or eval() at runtime."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-94", "CWE-506"],
        category="obfuscation_encode",
        patterns={
            "python": LanguagePattern(
                r"""base64\.(?:b64decode|b32decode|b16decode|decodebytes)\s*\(\s*(?:b?["'][A-Za-z0-9+/=]{4,}["'])""",
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Avoid using base64 decoding to obtain function names or executable code. "
            "If base64 is used for legitimate data encoding, ensure the result is "
            "never passed to eval(), exec(), or similar functions."
        ),
        confidence=0.6,
        false_positive_patterns=[
            r'(?:test_|def\s+test|pytest|unittest)',
            r'^\s*#',
            r'(?:\.png|\.jpg|\.gif|\.pdf|\.zip)',
            r'(?:content_type|mime_type|media_type)',
        ],
    ),

    # OBF-ENCODE-003: Hex decode patterns
    ObfuscationRule(
        id="OBF-ENCODE-003",
        title="Hex escape sequence or hex decode hiding dangerous content",
        description=(
            "Hexadecimal escape sequences (\\x65\\x76\\x61\\x6c) or hex decode "
            "operations (Buffer.from(..., 'hex'), bytes.fromhex()) are used to construct "
            "strings that may contain dangerous function names. This encoding technique "
            "makes the actual string content invisible to casual code review."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-94", "CWE-506"],
        category="obfuscation_encode",
        patterns={
            "javascript": LanguagePattern(
                r"""(?:"""
                r"""(?:\\x[0-9a-fA-F]{2}){4,}"""
                r"""|Buffer\.from\s*\(\s*["'][0-9a-fA-F]{8,}["']\s*,\s*["']hex["']\s*\)"""
                r""")""",
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r"""(?:"""
                r"""(?:\\x[0-9a-fA-F]{2}){4,}"""
                r"""|Buffer\.from\s*\(\s*["'][0-9a-fA-F]{8,}["']\s*,\s*["']hex["']\s*\)"""
                r""")""",
                flags=re.MULTILINE,
            ),
            "python": LanguagePattern(
                r"""(?:"""
                r"""(?:\\x[0-9a-fA-F]{2}){4,}"""
                r"""|bytes\.fromhex\s*\(\s*["'][0-9a-fA-F]{8,}["']\s*\)"""
                r"""|codecs\.decode\s*\(\s*["'][0-9a-fA-F]{8,}["']\s*,\s*["']hex["']\s*\)"""
                r""")""",
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r"""(?:"""
                r"""(?:\\x[0-9a-fA-F]{2}){4,}"""
                r"""|DatatypeConverter\.parseHexBinary\s*\(\s*["'][0-9a-fA-F]{8,}["']\s*\)"""
                r""")""",
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Replace hex-encoded strings with readable string literals. "
            "If hex encoding is needed for binary data, ensure the decoded "
            "content is never used to construct executable code."
        ),
        confidence=0.6,
        false_positive_patterns=[
            r'(?:test|spec|describe|it)\s*\(',
            r'^\s*(?://|#|/\*|\*)',
            r'(?:color|colour|rgb|hex|0x)',
            r'(?:hash|digest|hmac|checksum|signature|uuid)',
            r'(?:encoding|charset|utf)',
        ],
    ),
]


# =============================================================================
# OBF-UNICODE: UNICODE ESCAPE SEQUENCE OBFUSCATION RULES
# =============================================================================

UNICODE_RULES: List[ObfuscationRule] = [
    # OBF-UNICODE-001: Unicode escape sequences forming dangerous words
    ObfuscationRule(
        id="OBF-UNICODE-001",
        title="Unicode escape sequences forming dangerous identifier",
        description=(
            "Multiple Unicode escape sequences (\\u0065\\u0076\\u0061\\u006c) are "
            "used in succession to spell out a dangerous function name like 'eval'. "
            "JavaScript allows Unicode escapes in identifiers, so \\u0065\\u0076\\u0061\\u006c "
            "is syntactically equivalent to eval. This technique is used to hide "
            "malicious function calls from static analysis."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-94", "CWE-506"],
        category="obfuscation_unicode",
        patterns={
            "javascript": LanguagePattern(
                r"""(?:\\u[0-9a-fA-F]{4}){4,}""",
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r"""(?:\\u[0-9a-fA-F]{4}){4,}""",
                flags=re.MULTILINE,
            ),
            "python": LanguagePattern(
                r"""(?:\\u[0-9a-fA-F]{4}){4,}""",
                flags=re.MULTILINE,
            ),
            "java": LanguagePattern(
                r"""(?:\\u[0-9a-fA-F]{4}){4,}""",
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Replace Unicode escape sequences with readable identifiers. "
            "If internationalization requires Unicode, use string literals "
            "rather than escape sequences in identifier positions."
        ),
        confidence=0.5,
        false_positive_patterns=[
            r'(?:test|spec|describe|it)\s*\(',
            r'^\s*(?://|#|/\*|\*)',
            r'(?:i18n|l10n|locale|intl|translation)',
            r'(?:emoji|icon|symbol|glyph)',
            r'(?:encoding|charset|utf|unicode)',
        ],
    ),

    # OBF-UNICODE-002: String.fromCharCode with multiple arguments
    ObfuscationRule(
        id="OBF-UNICODE-002",
        title="String.fromCharCode with multiple character codes",
        description=(
            "String.fromCharCode() is called with multiple numeric arguments to construct "
            "a string character-by-character. For example, String.fromCharCode(101,118,97,108) "
            "produces 'eval'. This is a widely-used obfuscation technique in JavaScript "
            "malware to hide the actual string being constructed."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-94", "CWE-506"],
        category="obfuscation_unicode",
        patterns={
            "javascript": LanguagePattern(
                r"""String\.fromCharCode\s*\(\s*\d{2,3}\s*(?:,\s*\d{2,3}\s*){3,}\)""",
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r"""String\.fromCharCode\s*\(\s*\d{2,3}\s*(?:,\s*\d{2,3}\s*){3,}\)""",
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Replace String.fromCharCode() with a direct string literal. "
            "Character code construction of strings is rarely needed in "
            "legitimate application code."
        ),
        confidence=0.5,
        false_positive_patterns=[
            r'(?:test|spec|describe|it)\s*\(',
            r'^\s*(?://|/\*|\*)',
            r'(?:keyCode|charCode|keypress|keyboard)',
        ],
    ),
]


# =============================================================================
# OBF-CHARCODE: CHARACTER CODE ARITHMETIC OBFUSCATION RULES
# =============================================================================

CHARCODE_RULES: List[ObfuscationRule] = [
    # OBF-CHARCODE-001: fromCharCode with many arguments (JavaScript)
    ObfuscationRule(
        id="OBF-CHARCODE-001",
        title="fromCharCode building long string from numeric codes (JavaScript)",
        description=(
            "String.fromCharCode is called with a large number of numeric arguments "
            "(six or more) to construct a substantial string from character codes. "
            "When many character codes are used together, it typically indicates "
            "obfuscated code rather than legitimate character manipulation. Malware "
            "uses this to hide entire code blocks or URLs."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-94", "CWE-506"],
        category="obfuscation_charcode",
        patterns={
            "javascript": LanguagePattern(
                r"""String\.fromCharCode\s*\(\s*\d{2,3}\s*(?:,\s*\d{2,3}\s*){5,}\)""",
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r"""String\.fromCharCode\s*\(\s*\d{2,3}\s*(?:,\s*\d{2,3}\s*){5,}\)""",
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Replace character code arrays with direct string literals. "
            "If dynamic character generation is needed, document the purpose clearly."
        ),
        confidence=0.5,
        false_positive_patterns=[
            r'(?:test|spec|describe|it)\s*\(',
            r'^\s*(?://|/\*|\*)',
            r'(?:keyCode|charCode|keypress|keyboard)',
            r'(?:crypto|random|generate)',
        ],
    ),

    # OBF-CHARCODE-002: chr() concatenation in Python
    ObfuscationRule(
        id="OBF-CHARCODE-002",
        title="chr() concatenation building string from character codes (Python)",
        description=(
            "Multiple chr() calls are concatenated to construct a string character-by-character "
            "in Python. For example, chr(101)+chr(118)+chr(97)+chr(108) produces 'eval'. "
            "This is a common obfuscation technique in Python malware to hide function "
            "names and code strings from static analysis."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-94", "CWE-506"],
        category="obfuscation_charcode",
        patterns={
            "python": LanguagePattern(
                r"""chr\s*\(\s*\d{2,3}\s*\)\s*\+\s*chr\s*\(\s*\d{2,3}\s*\)(?:\s*\+\s*chr\s*\(\s*\d{2,3}\s*\)){1,}""",
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Replace chr() concatenation chains with direct string literals. "
            "Character-by-character string construction is a strong indicator "
            "of obfuscated or malicious code."
        ),
        confidence=0.5,
        false_positive_patterns=[
            r'(?:test_|def\s+test|pytest|unittest)',
            r'^\s*#',
            r'(?:ascii|ordinal|character\s+table)',
        ],
    ),
]


# =============================================================================
# OBF-ENTROPY: HIGH ENTROPY IDENTIFIER DETECTION RULES
# =============================================================================

ENTROPY_RULES: List[ObfuscationRule] = [
    # OBF-ENTROPY-001: High entropy variable/function names (JavaScript)
    ObfuscationRule(
        id="OBF-ENTROPY-001",
        title="High entropy identifier suggesting obfuscated code (JavaScript)",
        description=(
            "A variable or function name with unusually high Shannon entropy (above 3.5 bits "
            "per character) has been detected. Legitimate code uses meaningful, readable "
            "identifiers with lower entropy, while obfuscation tools and malware packers "
            "generate random-looking names like _0x4a3f, _$Zq8x, or a1b2c3d4. High entropy "
            "names across multiple identifiers strongly suggest automated obfuscation."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-506"],
        category="obfuscation_entropy",
        patterns={
            "javascript": LanguagePattern(
                r"""(?:var|let|const|function)\s+(?:_0x[0-9a-fA-F]{4,}|_\$[A-Za-z0-9]{4,}|[a-zA-Z]{1,2}[0-9a-fA-F]{4,})""",
                flags=re.MULTILINE,
            ),
            "typescript": LanguagePattern(
                r"""(?:var|let|const|function)\s+(?:_0x[0-9a-fA-F]{4,}|_\$[A-Za-z0-9]{4,}|[a-zA-Z]{1,2}[0-9a-fA-F]{4,})""",
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Use meaningful, descriptive identifier names. If this is minified "
            "production code, consider scanning the source map or original source instead. "
            "If the code is intentionally obfuscated, review it for malicious intent."
        ),
        confidence=0.4,
        false_positive_patterns=[
            r'(?:\.min\.js|\.bundle\.js|\.prod\.js)',
            r'(?:test|spec|describe|it)\s*\(',
            r'(?:sourceMappingURL|sourceMap)',
            r'(?:webpack|rollup|esbuild|terser|uglify)',
        ],
    ),

    # OBF-ENTROPY-002: High entropy variable/function names (Python)
    ObfuscationRule(
        id="OBF-ENTROPY-002",
        title="High entropy identifier suggesting obfuscated code (Python)",
        description=(
            "A variable or function name with unusually high Shannon entropy has been "
            "detected in Python code. Python conventions favor readable snake_case names. "
            "Random-looking identifiers such as _x4f3a, O0O0O0, lIlIlI, or sequences "
            "of mixed alphanumeric characters are characteristic of obfuscation tools "
            "like pyarmor or manual obfuscation attempts."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-506"],
        category="obfuscation_entropy",
        patterns={
            "python": LanguagePattern(
                r"""(?:^|\s)(?:def|class)\s+(?:_x[0-9a-fA-F]{4,}|[OoIl0]{5,}|[a-zA-Z][a-zA-Z0-9]{1,2}[0-9a-fA-F]{4,})""",
                flags=re.MULTILINE,
            ),
        },
        fix_suggestion=(
            "Use meaningful, PEP 8 compliant identifier names. If this is "
            "generated code, consider reviewing the generator configuration. "
            "Obfuscated Python code should be reviewed for malicious intent."
        ),
        confidence=0.4,
        false_positive_patterns=[
            r'(?:test_|def\s+test|pytest|unittest)',
            r'^\s*#',
            r'(?:pyarmor|cython|nuitka)',
            r'(?:generated|auto.generated|autogen)',
        ],
    ),
]


# =============================================================================
# ALL RULES COMBINED
# =============================================================================

ALL_OBFUSCATION_RULES: List[ObfuscationRule] = (
    CONCAT_RULES +
    ENCODE_RULES +
    UNICODE_RULES +
    CHARCODE_RULES +
    ENTROPY_RULES
)


# =============================================================================
# CONFIDENCE LEVELS PER CATEGORY
# =============================================================================

CATEGORY_CONFIDENCE: Dict[str, float] = {
    "obfuscation_concat": 0.5,
    "obfuscation_encode": 0.6,
    "obfuscation_unicode": 0.5,
    "obfuscation_charcode": 0.5,
    "obfuscation_entropy": 0.4,
}


# =============================================================================
# SCANNER IMPLEMENTATION
# =============================================================================

class ObfuscationDetector(BaseScanner):
    """
    Detects code obfuscation patterns that may indicate malicious intent.

    Covers obfuscation techniques commonly used by malware:
    - OBF-CONCAT: String concatenation building dangerous function names
    - OBF-ENCODE: Base64/hex encoding hiding dangerous calls
    - OBF-UNICODE: Unicode escape sequences forming dangerous identifiers
    - OBF-CHARCODE: Character code arithmetic building strings
    - OBF-ENTROPY: High Shannon entropy in identifiers (obfuscated/packed code)

    Includes semantic verification:
    - Shannon entropy calculation for identifier analysis
    - Base64/hex decode verification against known dangerous functions
    - False positive filtering for test files, comments, and legitimate usage

    Multi-language: JavaScript, TypeScript, Python, Java
    """

    SCANNER_VERSION = "1.0.0"

    def __init__(self):
        """Initialize the obfuscation detector and pre-compile all patterns."""
        super().__init__()
        self._compiled_patterns: Dict[str, Dict[str, re.Pattern]] = {}
        self._compiled_fp_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance.

        Iterates through every rule and compiles both the detection patterns
        and the false positive patterns. Invalid patterns are logged and skipped
        rather than causing the scanner to fail entirely.
        """
        for rule in ALL_OBFUSCATION_RULES:
            self._compiled_patterns[rule.id] = {}
            for lang, lang_pattern in rule.patterns.items():
                try:
                    self._compiled_patterns[rule.id][lang] = re.compile(
                        lang_pattern.pattern,
                        lang_pattern.flags,
                    )
                except re.error as e:
                    logger.warning(f"Invalid regex for {rule.id}/{lang}: {e}")

            # Compile false positive patterns
            self._compiled_fp_patterns[rule.id] = []
            for fp_pattern in rule.false_positive_patterns:
                try:
                    self._compiled_fp_patterns[rule.id].append(
                        re.compile(fp_pattern, re.IGNORECASE)
                    )
                except re.error:
                    pass

    @property
    def scanner_type(self) -> ScannerType:
        """Return the scanner type identifier."""
        return ScannerType.OBFUSCATION

    @property
    def supported_languages(self) -> Set[str]:
        """Return set of supported language identifiers."""
        return set(SUPPORTED_LANGUAGES.keys())

    @property
    def supported_extensions(self) -> Set[str]:
        """Return set of supported file extensions."""
        extensions = set()
        for lang_def in SUPPORTED_LANGUAGES.values():
            extensions.update(lang_def.extensions)
        return extensions

    def is_available(self) -> bool:
        """Obfuscation detector is always available (no external dependencies)."""
        return True

    def get_scanner_version(self) -> Optional[str]:
        """Return the scanner version string."""
        return self.SCANNER_VERSION

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension.

        Args:
            file_path: Path to the source file.

        Returns:
            Language identifier string or None if the extension is not supported.
        """
        ext = file_path.suffix.lower()
        for lang_name, lang_def in SUPPORTED_LANGUAGES.items():
            if ext in lang_def.extensions:
                return lang_name
        return None

    @staticmethod
    def _calculate_shannon_entropy(text: str) -> float:
        """Calculate Shannon entropy of a string.

        Shannon entropy measures the average information content per character.
        Higher entropy indicates more randomness. Typical values:
        - English text: ~3.5-4.5 bits
        - Readable code identifiers: ~2.5-3.5 bits
        - Obfuscated identifiers: ~3.5-5.0 bits
        - Random strings: ~4.5-5.5 bits

        Args:
            text: The input string to measure.

        Returns:
            Shannon entropy value in bits per character. Returns 0.0 for
            empty strings.
        """
        if not text:
            return 0.0

        length = len(text)
        frequency: Dict[str, int] = {}
        for char in text:
            frequency[char] = frequency.get(char, 0) + 1

        entropy = 0.0
        for count in frequency.values():
            probability = count / length
            if probability > 0:
                entropy -= probability * math.log2(probability)

        return entropy

    @staticmethod
    def _check_dangerous_decode(encoded_value: str, encoding: str = "base64") -> bool:
        """Attempt to decode an encoded string and check for dangerous function names.

        Tries to decode the given value using the specified encoding and checks
        whether the result contains any known dangerous function names from the
        DANGEROUS_FUNCTIONS set. This provides semantic verification beyond
        simple pattern matching.

        Args:
            encoded_value: The encoded string to decode and check.
            encoding: The encoding type, either 'base64' or 'hex'.

        Returns:
            True if the decoded string contains a dangerous function name,
            False otherwise or if decoding fails.
        """
        try:
            if encoding == "base64":
                # Strip quotes and whitespace
                cleaned = encoded_value.strip().strip("'\"").strip()
                # Add padding if necessary
                padding = 4 - (len(cleaned) % 4)
                if padding != 4:
                    cleaned += "=" * padding
                decoded = base64.b64decode(cleaned).decode("utf-8", errors="replace")
            elif encoding == "hex":
                cleaned = encoded_value.strip().strip("'\"").strip()
                decoded = bytes.fromhex(cleaned).decode("utf-8", errors="replace")
            else:
                return False

            decoded_lower = decoded.lower()
            for func in DANGEROUS_FUNCTIONS:
                if func.lower() in decoded_lower:
                    return True

            return False
        except Exception:
            return False

    def _is_false_positive(
        self,
        rule_id: str,
        matched_text: str,
        context_lines: str,
    ) -> bool:
        """Check if a match is a false positive.

        Tests the matched text and surrounding context against the rule's
        false positive patterns. If any false positive pattern matches,
        the finding is considered a false positive.

        Args:
            rule_id: The rule identifier to look up false positive patterns.
            matched_text: The actual text that matched the detection pattern.
            context_lines: Surrounding source code lines for context analysis.

        Returns:
            True if the match is likely a false positive, False otherwise.
        """
        fp_patterns = self._compiled_fp_patterns.get(rule_id, [])
        full_text = matched_text + " " + context_lines

        for fp_pattern in fp_patterns:
            if fp_pattern.search(full_text):
                return True
        return False

    def _determine_severity(
        self,
        rule: ObfuscationRule,
        matched_text: str,
    ) -> Severity:
        """Determine the effective severity based on rule and match analysis.

        For encode rules, if the decoded content is confirmed to contain
        dangerous function names, the severity is elevated to HIGH. Otherwise,
        the rule's default severity is used.

        Args:
            rule: The obfuscation rule that matched.
            matched_text: The matched source text.

        Returns:
            Effective Severity for this finding.
        """
        if rule.category == "obfuscation_encode":
            # Try to extract and decode the encoded value
            b64_match = re.search(r"""["']([A-Za-z0-9+/=]{4,})["']""", matched_text)
            if b64_match:
                if self._check_dangerous_decode(b64_match.group(1), "base64"):
                    return Severity.HIGH

            hex_match = re.search(r"""["']([0-9a-fA-F]{8,})["']""", matched_text)
            if hex_match:
                if self._check_dangerous_decode(hex_match.group(1), "hex"):
                    return Severity.HIGH

        return rule.severity

    def _determine_confidence(
        self,
        rule: ObfuscationRule,
        matched_text: str,
    ) -> float:
        """Determine the confidence level for a finding.

        Uses the category-level confidence as a baseline, then adjusts upward
        if semantic verification (such as successful dangerous decode) confirms
        the suspicion.

        Args:
            rule: The obfuscation rule that matched.
            matched_text: The matched source text.

        Returns:
            Confidence value between 0.0 and 1.0.
        """
        base_confidence = CATEGORY_CONFIDENCE.get(rule.category, rule.confidence)

        # Boost confidence for encode rules where decode confirms danger
        if rule.category == "obfuscation_encode":
            b64_match = re.search(r"""["']([A-Za-z0-9+/=]{4,})["']""", matched_text)
            if b64_match and self._check_dangerous_decode(b64_match.group(1), "base64"):
                return min(base_confidence + 0.2, 0.9)

            hex_match = re.search(r"""["']([0-9a-fA-F]{8,})["']""", matched_text)
            if hex_match and self._check_dangerous_decode(hex_match.group(1), "hex"):
                return min(base_confidence + 0.2, 0.9)

        # For entropy rules, compute actual entropy on the identifier
        if rule.category == "obfuscation_entropy":
            ident_match = re.search(r"""(?:var|let|const|function|def|class)\s+(\S+)""", matched_text)
            if ident_match:
                entropy = self._calculate_shannon_entropy(ident_match.group(1))
                if entropy > 4.0:
                    return min(base_confidence + 0.15, 0.7)
                elif entropy > 3.5:
                    return base_confidence
                else:
                    # Below threshold, reduce confidence
                    return max(base_confidence - 0.1, 0.2)

        return base_confidence

    async def scan(
        self,
        target_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> ScanResult:
        """Execute obfuscation detection scan on the target path.

        Scans all supported files under the target path for obfuscation patterns.
        For each file, the scanner detects the language from the file extension,
        then applies all rules that have patterns for that language. Matches are
        checked against false positive patterns and enriched with confidence
        scores and severity adjustments.

        Args:
            target_path: Path to a file or directory to scan.
            config: Optional scanner-specific configuration. Supported keys:
                - min_confidence (float): Minimum confidence to report (default 0.0)
                - exclude_categories (list): Categories to skip

        Returns:
            ScanResult containing all obfuscation findings.
        """
        started_at = datetime.now(timezone.utc)
        findings: List[SecurityFinding] = []
        files_scanned = 0
        errors: List[str] = []

        # Parse config
        min_confidence = 0.0
        exclude_categories: Set[str] = set()
        if config:
            min_confidence = config.get("min_confidence", 0.0)
            exclude_categories = set(config.get("exclude_categories", []))

        # Collect files to scan
        if target_path.is_file():
            files = [target_path]
        else:
            files = []
            for ext in self.supported_extensions:
                files.extend(target_path.rglob(f"*{ext}"))

        for file_path in files:
            files_scanned += 1
            language = self._detect_language(file_path)

            if not language:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                lines = content.split("\n")

                for rule in ALL_OBFUSCATION_RULES:
                    # Skip excluded categories
                    if rule.category in exclude_categories:
                        continue

                    # Get language-specific compiled pattern
                    compiled_pattern = self._compiled_patterns.get(
                        rule.id, {}
                    ).get(language)
                    if not compiled_pattern:
                        continue

                    for match in compiled_pattern.finditer(content):
                        # Calculate line numbers
                        line_start = content[:match.start()].count("\n") + 1
                        line_end = content[:match.end()].count("\n") + 1

                        # Extract snippet with surrounding context
                        snippet_start = max(0, line_start - 2)
                        snippet_end = min(len(lines), line_end + 3)
                        snippet = "\n".join(lines[snippet_start:snippet_end])

                        # Check for false positives
                        if self._is_false_positive(rule.id, match.group(), snippet):
                            continue

                        # Determine effective severity and confidence
                        effective_severity = self._determine_severity(
                            rule, match.group()
                        )
                        confidence = self._determine_confidence(
                            rule, match.group()
                        )

                        # Skip findings below minimum confidence
                        if confidence < min_confidence:
                            continue

                        finding = SecurityFinding(
                            id=f"obfuscation-{rule.id}-{file_path}:{line_start}",
                            rule_id=rule.id,
                            title=rule.title,
                            description=rule.description,
                            severity=effective_severity,
                            scanner=self.scanner_type,
                            location=Location(
                                file_path=str(file_path),
                                start_line=line_start,
                                end_line=line_end,
                                snippet=snippet,
                            ),
                            cwe_ids=rule.cwe_ids,
                            category=rule.category,
                            confidence=confidence,
                            tags={
                                f"lang:{language}",
                                "obfuscation",
                                rule.category,
                            },
                        )

                        finding.suggested_fixes.append(
                            SuggestedFix(description=rule.fix_suggestion)
                        )

                        findings.append(finding)

            except Exception as e:
                errors.append(f"Error scanning {file_path}: {e}")
                logger.error(f"Error scanning {file_path}: {e}")

        completed_at = datetime.now(timezone.utc)
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        return ScanResult(
            scanner=self.scanner_type,
            scanner_version=self.SCANNER_VERSION,
            scan_duration_ms=duration_ms,
            findings=findings,
            files_scanned=files_scanned,
            errors=errors,
            started_at=started_at,
            completed_at=completed_at,
        )

    def get_rules_summary(self) -> Dict[str, Any]:
        """Get a summary of all obfuscation detection rules.

        Returns:
            Dictionary containing rule counts, category breakdowns,
            per-rule details, supported languages, and CWE coverage.
        """
        categories: Dict[str, int] = {}
        for rule in ALL_OBFUSCATION_RULES:
            if rule.category not in categories:
                categories[rule.category] = 0
            categories[rule.category] += 1

        cwe_coverage: Set[str] = set()
        for rule in ALL_OBFUSCATION_RULES:
            cwe_coverage.update(rule.cwe_ids)

        return {
            "total_rules": len(ALL_OBFUSCATION_RULES),
            "rules_by_category": categories,
            "rules": [
                {
                    "id": rule.id,
                    "title": rule.title,
                    "severity": rule.severity.value,
                    "cwe_ids": rule.cwe_ids,
                    "category": rule.category,
                    "confidence": rule.confidence,
                    "languages": list(rule.patterns.keys()),
                }
                for rule in ALL_OBFUSCATION_RULES
            ],
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
            "cwe_coverage": sorted(cwe_coverage),
            "category_descriptions": {
                "obfuscation_concat": "String concatenation building dangerous function names",
                "obfuscation_encode": "Base64/hex encoding hiding dangerous calls",
                "obfuscation_unicode": "Unicode escape sequences forming dangerous identifiers",
                "obfuscation_charcode": "Character code arithmetic building strings",
                "obfuscation_entropy": "High Shannon entropy in identifiers (obfuscated code)",
            },
            "confidence_levels": CATEGORY_CONFIDENCE,
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_obfuscation_detector() -> ObfuscationDetector:
    """Factory function to create an obfuscation detector instance.

    Returns:
        A fully initialized ObfuscationDetector with all patterns pre-compiled.
    """
    return create_obfuscation_detector.__wrapped__()


# Store direct constructor reference to avoid recursion
create_obfuscation_detector.__wrapped__ = ObfuscationDetector  # type: ignore[attr-defined]
