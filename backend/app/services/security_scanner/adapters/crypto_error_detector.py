"""
Crypto Error Detector - Cryptographic Vulnerability Detection.

Fase 36: Detects cryptographic anti-patterns and vulnerabilities across multiple languages:
- CWE-321: Hardcoded Cryptographic Keys
- CWE-327: Use of Broken/Risky Cryptographic Algorithms
- CWE-328: Reversible One-Way Hash (MD5, SHA1)
- CWE-330: Use of Insufficiently Random Values
- CWE-208: Observable Timing Discrepancy (Timing Attacks)
- CWE-295: Improper Certificate Validation
- CWE-296: Improper Following of Chain of Trust for Certificate Validation
- CWE-326: Inadequate Encryption Strength
- CWE-798: Use of Hard-coded Credentials

Supports: Python, JavaScript/TypeScript, Java, C#, C/C++, Go, PHP, Ruby
"""

import re
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
# LANGUAGE DEFINITIONS
# =============================================================================

@dataclass
class LanguageDefinition:
    """Definition of a programming language for scanning."""
    name: str
    extensions: Set[str]


SUPPORTED_LANGUAGES: Dict[str, LanguageDefinition] = {
    "python": LanguageDefinition(
        name="Python",
        extensions={".py", ".pyw"},
    ),
    "javascript": LanguageDefinition(
        name="JavaScript/TypeScript",
        extensions={".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"},
    ),
    "java": LanguageDefinition(
        name="Java",
        extensions={".java", ".jsp"},
    ),
    "csharp": LanguageDefinition(
        name="C#",
        extensions={".cs", ".cshtml", ".razor"},
    ),
    "cpp": LanguageDefinition(
        name="C/C++",
        extensions={".c", ".cpp", ".h", ".hpp", ".cc", ".cxx"},
    ),
    "go": LanguageDefinition(
        name="Go",
        extensions={".go"},
    ),
    "php": LanguageDefinition(
        name="PHP",
        extensions={".php", ".phtml"},
    ),
    "ruby": LanguageDefinition(
        name="Ruby",
        extensions={".rb", ".erb"},
    ),
}


# =============================================================================
# CRYPTO RULES
# =============================================================================

@dataclass
class LanguagePattern:
    """Pattern for a specific language."""
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE


@dataclass
class CryptoRule:
    """A cryptographic security rule with language-specific patterns."""
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

    # Context keywords for reducing false positives
    context_keywords: List[str] = field(default_factory=list)
    require_context: bool = False
    context_window_lines: int = 10

    # False positive hints
    false_positive_patterns: List[str] = field(default_factory=list)


# =============================================================================
# RULE DEFINITIONS
# =============================================================================

CRYPTO_RULES: List[CryptoRule] = [
    # =========================================================================
    # CR001: Hardcoded Encryption Key (CWE-321)
    # =========================================================================
    CryptoRule(
        id="CR001",
        title="Hardcoded encryption key",
        description=(
            "A cryptographic key appears to be hardcoded in the source code. "
            "Hardcoded keys can be extracted by attackers through reverse engineering "
            "or source code access. Keys should be stored securely in environment "
            "variables, key vaults, or secure configuration."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-321"],
        category="cryptography",
        patterns={
            "python": LanguagePattern(
                r'(?:key|secret_key|encryption_key|aes_key|cipher_key)\s*=\s*["\'][A-Za-z0-9+/=]{16,}["\']',
            ),
            "javascript": LanguagePattern(
                r'(?:key|secretKey|encryptionKey|aesKey|cipherKey)\s*[=:]\s*["\'][A-Za-z0-9+/=]{16,}["\']',
            ),
            "java": LanguagePattern(
                r'(?:String|byte\[\])\s+(?:key|secretKey|encryptionKey|aesKey)\s*=\s*["\'][A-Za-z0-9+/=]{16,}["\']',
            ),
            "csharp": LanguagePattern(
                r'(?:string|byte\[\])\s+(?:key|secretKey|encryptionKey|aesKey)\s*=\s*["\'][A-Za-z0-9+/=]{16,}["\']',
            ),
            "cpp": LanguagePattern(
                r'(?:char\s*\*|std::string|const\s+char\s*\*)\s+(?:key|secret_key|encryption_key)\s*=\s*["\'][A-Za-z0-9+/=]{16,}["\']',
            ),
            "go": LanguagePattern(
                r'(?:key|secretKey|encryptionKey)\s*:?=\s*["\'][A-Za-z0-9+/=]{16,}["\']',
            ),
            "php": LanguagePattern(
                r'\$(?:key|secret_key|encryption_key|aes_key)\s*=\s*["\'][A-Za-z0-9+/=]{16,}["\']',
            ),
            "ruby": LanguagePattern(
                r'(?:key|secret_key|encryption_key)\s*=\s*["\'][A-Za-z0-9+/=]{16,}["\']',
            ),
        },
        fix_suggestion="Store encryption keys in environment variables or a secure key vault (AWS KMS, Azure Key Vault, HashiCorp Vault).",
        false_positive_patterns=[
            r'example', r'placeholder', r'test', r'dummy', r'xxx+', r'\$\{', r'%\w+%',
        ],
    ),

    # =========================================================================
    # CR002: Hardcoded Password (CWE-798)
    # =========================================================================
    CryptoRule(
        id="CR002",
        title="Hardcoded password in source code",
        description=(
            "A password appears to be hardcoded in the source code. "
            "Hardcoded passwords can be discovered through code review, reverse engineering, "
            "or version control history. Passwords should be retrieved from secure storage."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-798"],
        category="credentials",
        patterns={
            "python": LanguagePattern(
                r'(?:password|passwd|pwd|db_pass|db_password)\s*=\s*["\'][^"\']{8,}["\']',
            ),
            "javascript": LanguagePattern(
                r'(?:password|passwd|pwd|dbPass|dbPassword)\s*[=:]\s*["\'][^"\']{8,}["\']',
            ),
            "java": LanguagePattern(
                r'(?:String\s+)?(?:password|passwd|pwd)\s*=\s*["\'][^"\']{8,}["\']',
            ),
            "csharp": LanguagePattern(
                r'(?:string\s+)?(?:password|passwd|pwd)\s*=\s*["\'][^"\']{8,}["\']',
            ),
            "cpp": LanguagePattern(
                r'(?:char\s*\*|std::string)\s+(?:password|passwd|pwd)\s*=\s*["\'][^"\']{8,}["\']',
            ),
            "go": LanguagePattern(
                r'(?:password|passwd|pwd)\s*:?=\s*["\'][^"\']{8,}["\']',
            ),
            "php": LanguagePattern(
                r'\$(?:password|passwd|pwd|db_pass)\s*=\s*["\'][^"\']{8,}["\']',
            ),
            "ruby": LanguagePattern(
                r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{8,}["\']',
            ),
        },
        fix_suggestion="Store passwords in environment variables or a secrets manager. Never commit passwords to version control.",
        false_positive_patterns=[
            r'example', r'placeholder', r'your.?password', r'xxx+', r'\*{4,}', r'\$\{', r'%\w+%',
            r'process\.env', r'os\.environ', r'getenv',
        ],
    ),

    # =========================================================================
    # CR003: Hardcoded API Key (CWE-798)
    # =========================================================================
    CryptoRule(
        id="CR003",
        title="Hardcoded API key",
        description=(
            "An API key appears to be hardcoded in the source code. "
            "API keys grant access to external services and should be rotated regularly. "
            "Exposing them in code can lead to unauthorized service usage and data breaches."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-798"],
        category="credentials",
        patterns={
            "python": LanguagePattern(
                r'(?:api_key|apikey|api_secret|access_key)\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']',
            ),
            "javascript": LanguagePattern(
                r'(?:apiKey|apiSecret|accessKey|API_KEY)\s*[=:]\s*["\'][A-Za-z0-9_\-]{20,}["\']',
            ),
            "java": LanguagePattern(
                r'(?:String\s+)?(?:apiKey|apiSecret|accessKey)\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']',
            ),
            "csharp": LanguagePattern(
                r'(?:string\s+)?(?:apiKey|apiSecret|accessKey)\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']',
            ),
            "go": LanguagePattern(
                r'(?:apiKey|apiSecret|accessKey)\s*:?=\s*["\'][A-Za-z0-9_\-]{20,}["\']',
            ),
            "php": LanguagePattern(
                r'\$(?:api_key|apikey|api_secret|access_key)\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']',
            ),
            "ruby": LanguagePattern(
                r'(?:api_key|apikey|api_secret)\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']',
            ),
        },
        fix_suggestion="Store API keys in environment variables or a secrets manager. Use .env files for development (gitignored).",
        false_positive_patterns=[
            r'example', r'placeholder', r'your.?api', r'xxx+', r'\$\{', r'%\w+%',
            r'process\.env', r'os\.environ', r'getenv',
        ],
    ),

    # =========================================================================
    # CR004: MD5 Hash Usage (CWE-328)
    # =========================================================================
    CryptoRule(
        id="CR004",
        title="MD5 hash algorithm usage (cryptographically broken)",
        description=(
            "MD5 hash algorithm is used. MD5 is cryptographically broken and unsuitable "
            "for security purposes. Collision attacks have been demonstrated making it "
            "unsafe for digital signatures, certificate validation, and password hashing."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-328"],
        category="cryptography",
        patterns={
            "python": LanguagePattern(
                r'(?:hashlib\.md5|MD5\.new|Crypto\.Hash\.MD5)',
            ),
            "javascript": LanguagePattern(
                r'(?:crypto\.createHash\s*\(\s*["\']md5["\']|md5\s*\()',
            ),
            "java": LanguagePattern(
                r'MessageDigest\.getInstance\s*\(\s*["\']MD5["\']',
            ),
            "csharp": LanguagePattern(
                r'(?:MD5\.Create|MD5CryptoServiceProvider|System\.Security\.Cryptography\.MD5)',
            ),
            "cpp": LanguagePattern(
                r'(?:MD5_Init|MD5_Update|MD5_Final|EVP_md5)',
            ),
            "go": LanguagePattern(
                r'(?:md5\.New|md5\.Sum|crypto/md5)',
            ),
            "php": LanguagePattern(
                r'(?:md5\s*\(|hash\s*\(\s*["\']md5["\'])',
            ),
            "ruby": LanguagePattern(
                r'(?:Digest::MD5|OpenSSL::Digest::MD5)',
            ),
        },
        fix_suggestion="Use SHA-256 or SHA-3 for hashing. For password hashing, use bcrypt, Argon2, or scrypt.",
    ),

    # =========================================================================
    # CR005: SHA1 Hash Usage (CWE-328)
    # =========================================================================
    CryptoRule(
        id="CR005",
        title="SHA1 hash algorithm usage (deprecated for security)",
        description=(
            "SHA1 hash algorithm is used. SHA1 has known collision vulnerabilities and "
            "is deprecated for cryptographic use. While still seen in legacy systems, "
            "it should not be used for security-sensitive operations."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-328"],
        category="cryptography",
        patterns={
            "python": LanguagePattern(
                r'(?:hashlib\.sha1|SHA\.new|Crypto\.Hash\.SHA)',
            ),
            "javascript": LanguagePattern(
                r'crypto\.createHash\s*\(\s*["\']sha1["\']',
            ),
            "java": LanguagePattern(
                r'MessageDigest\.getInstance\s*\(\s*["\']SHA-?1["\']',
            ),
            "csharp": LanguagePattern(
                r'(?:SHA1\.Create|SHA1CryptoServiceProvider|SHA1Managed)',
            ),
            "cpp": LanguagePattern(
                r'(?:SHA1_Init|SHA1_Update|SHA1_Final|EVP_sha1)',
            ),
            "go": LanguagePattern(
                r'(?:sha1\.New|sha1\.Sum|crypto/sha1)',
            ),
            "php": LanguagePattern(
                r'(?:sha1\s*\(|hash\s*\(\s*["\']sha1["\'])',
            ),
            "ruby": LanguagePattern(
                r'(?:Digest::SHA1|OpenSSL::Digest::SHA1)',
            ),
        },
        fix_suggestion="Use SHA-256 or SHA-3 for hashing. For password hashing, use bcrypt, Argon2, or scrypt.",
    ),

    # =========================================================================
    # CR006: DES/3DES/RC4 Usage (CWE-327)
    # =========================================================================
    CryptoRule(
        id="CR006",
        title="Weak encryption algorithm (DES/3DES/RC4)",
        description=(
            "A weak or obsolete encryption algorithm (DES, 3DES, or RC4) is used. "
            "DES has a 56-bit key which is too small for modern security. "
            "3DES is slow and provides only 112-bit security. "
            "RC4 has known biases and should never be used."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-327"],
        category="cryptography",
        patterns={
            "python": LanguagePattern(
                r'(?:from\s+Crypto\.Cipher\s+import\s+(?:DES|DES3|ARC4)|DES\.new|DES3\.new|ARC4\.new)',
            ),
            "javascript": LanguagePattern(
                r'(?:createCipher(?:iv)?\s*\(\s*["\'](?:des|des3|rc4)|DES|TripleDES|RC4)',
            ),
            "java": LanguagePattern(
                r'Cipher\.getInstance\s*\(\s*["\'](?:DES|DESede|RC4|ARCFOUR)',
            ),
            "csharp": LanguagePattern(
                r'(?:DESCryptoServiceProvider|TripleDESCryptoServiceProvider|RC2CryptoServiceProvider)',
            ),
            "cpp": LanguagePattern(
                r'(?:DES_set_key|DES_ecb_encrypt|DES_cbc_encrypt|EVP_des|EVP_rc4)',
            ),
            "go": LanguagePattern(
                r'(?:des\.NewCipher|des\.NewTripleDESCipher|rc4\.NewCipher)',
            ),
            "php": LanguagePattern(
                r'(?:mcrypt_encrypt.*MCRYPT_(?:DES|3DES|RC4)|openssl_encrypt.*(?:des|rc4))',
            ),
        },
        fix_suggestion="Use AES-256-GCM for symmetric encryption. AES is the modern standard with strong security.",
    ),

    # =========================================================================
    # CR007: ECB Mode Usage (CWE-327)
    # =========================================================================
    CryptoRule(
        id="CR007",
        title="ECB encryption mode usage (insecure)",
        description=(
            "Electronic Codebook (ECB) mode is used for encryption. ECB mode encrypts "
            "identical plaintext blocks to identical ciphertext blocks, revealing patterns "
            "in the data. This is demonstrated by the famous 'ECB penguin' example."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-327"],
        category="cryptography",
        patterns={
            "python": LanguagePattern(
                r'(?:AES\.new\([^)]*,\s*AES\.MODE_ECB|mode\s*=\s*["\']?ECB)',
            ),
            "javascript": LanguagePattern(
                r'(?:createCipher(?:iv)?\s*\(\s*["\']aes-\d+-ecb|mode:\s*["\']?ECB)',
            ),
            "java": LanguagePattern(
                r'Cipher\.getInstance\s*\(\s*["\']AES/ECB',
            ),
            "csharp": LanguagePattern(
                r'(?:CipherMode\.ECB|\.Mode\s*=\s*CipherMode\.ECB)',
            ),
            "cpp": LanguagePattern(
                r'(?:EVP_aes_\d+_ecb|AES_ecb_encrypt)',
            ),
            "go": LanguagePattern(
                r'cipher\.NewECBEncrypter',
            ),
            "php": LanguagePattern(
                r'(?:MCRYPT_MODE_ECB|openssl_encrypt.*ecb)',
            ),
        },
        fix_suggestion="Use GCM mode (AES-GCM) for authenticated encryption, or CBC with proper IV handling.",
    ),

    # =========================================================================
    # CR008: Weak Random for Crypto (CWE-330)
    # =========================================================================
    CryptoRule(
        id="CR008",
        title="Non-cryptographic random number generator for security context",
        description=(
            "A non-cryptographic random number generator is used in a security-sensitive "
            "context. Standard RNGs like random(), Math.random(), or rand() are predictable "
            "and should never be used for tokens, keys, passwords, or other security values."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-330"],
        category="cryptography",
        context_keywords=[
            "token", "key", "secret", "password", "salt", "nonce", "iv", "session",
            "auth", "otp", "csrf", "jwt", "verification",
        ],
        require_context=True,
        context_window_lines=10,
        patterns={
            "python": LanguagePattern(
                r'(?:random\.(?:random|randint|choice|randrange|uniform|sample)\s*\()',
            ),
            "javascript": LanguagePattern(
                r'Math\.random\s*\(',
            ),
            "java": LanguagePattern(
                r'(?:new\s+Random\s*\(|Math\.random\s*\()',
            ),
            "csharp": LanguagePattern(
                r'new\s+Random\s*\(',
            ),
            "cpp": LanguagePattern(
                r'(?:rand\s*\(|srand\s*\()',
            ),
            "go": LanguagePattern(
                r'(?:rand\.(?:Int|Intn|Float|Seed)\s*\()',
            ),
            "php": LanguagePattern(
                r'(?:rand\s*\(|mt_rand\s*\()',
            ),
            "ruby": LanguagePattern(
                r'(?:rand\s*\(|Random\.(?:new|rand)\s*\()',
            ),
        },
        fix_suggestion="Use cryptographically secure random: secrets (Python), crypto.getRandomValues (JS), SecureRandom (Java/Ruby), RandomNumberGenerator (C#).",
    ),

    # =========================================================================
    # CR009: Timing-Vulnerable Comparison (CWE-208)
    # =========================================================================
    CryptoRule(
        id="CR009",
        title="Timing-vulnerable string comparison for secrets",
        description=(
            "A regular string comparison (== or ===) is used to compare secrets, tokens, "
            "or passwords. This is vulnerable to timing attacks where an attacker can "
            "determine the correct value byte-by-byte by measuring response times."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-208"],
        category="cryptography",
        context_keywords=[
            "token", "key", "secret", "password", "hash", "hmac", "signature", "digest",
        ],
        require_context=True,
        context_window_lines=5,
        patterns={
            "python": LanguagePattern(
                r'(?:token|secret|password|key|hash|hmac|signature)\s*(?:==|!=)\s*',
            ),
            "javascript": LanguagePattern(
                r'(?:token|secret|password|key|hash|hmac|signature)\s*(?:===|!==|==|!=)\s*',
            ),
            "java": LanguagePattern(
                r'(?:token|secret|password|key|hash|hmac|signature)\.equals\s*\(',
            ),
            "csharp": LanguagePattern(
                r'(?:token|secret|password|key|hash|hmac|signature)\s*(?:==|!=)\s*',
            ),
            "go": LanguagePattern(
                r'(?:token|secret|password|key|hash|hmac|signature)\s*(?:==|!=)\s*',
            ),
            "php": LanguagePattern(
                r'(?:\$token|\$secret|\$password|\$key|\$hash|\$hmac)\s*(?:===|!==|==|!=)\s*',
            ),
            "ruby": LanguagePattern(
                r'(?:token|secret|password|key|hash|hmac|signature)\s*(?:==|!=)\s*',
            ),
        },
        fix_suggestion="Use constant-time comparison: hmac.compare_digest (Python), crypto.timingSafeEqual (Node.js), MessageDigest.isEqual (Java), FixedTimeEquals (C#).",
    ),

    # =========================================================================
    # CR010: Certificate Validation Disabled (CWE-295)
    # =========================================================================
    CryptoRule(
        id="CR010",
        title="SSL/TLS certificate validation disabled",
        description=(
            "SSL/TLS certificate validation is explicitly disabled. This makes the "
            "application vulnerable to man-in-the-middle attacks as any certificate "
            "will be accepted, including self-signed or malicious ones."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-295"],
        category="cryptography",
        patterns={
            "python": LanguagePattern(
                r'(?:verify\s*=\s*False|ssl\._create_unverified_context|CERT_NONE)',
            ),
            "javascript": LanguagePattern(
                r'(?:rejectUnauthorized\s*:\s*false|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*["\']0["\'])',
            ),
            "java": LanguagePattern(
                r'(?:TrustAllCerts|X509TrustManager.*checkServerTrusted.*return;|setHostnameVerifier.*ALLOW_ALL)',
            ),
            "csharp": LanguagePattern(
                r'(?:ServerCertificateValidationCallback\s*=.*true|ServicePointManager\.ServerCertificateValidationCallback)',
            ),
            "go": LanguagePattern(
                r'InsecureSkipVerify\s*:\s*true',
            ),
            "php": LanguagePattern(
                r'(?:CURLOPT_SSL_VERIFYPEER\s*,\s*(?:false|0)|verify_peer.*false)',
            ),
            "ruby": LanguagePattern(
                r'(?:verify_mode\s*=\s*OpenSSL::SSL::VERIFY_NONE|ssl_verify_mode.*VERIFY_NONE)',
            ),
        },
        fix_suggestion="Always verify SSL certificates. Use proper certificate chain validation. For testing, use a local CA.",
    ),

    # =========================================================================
    # CR011: Hostname Verification Disabled (CWE-295)
    # =========================================================================
    CryptoRule(
        id="CR011",
        title="SSL/TLS hostname verification disabled",
        description=(
            "SSL/TLS hostname verification is disabled. Even with valid certificates, "
            "this allows man-in-the-middle attacks using any valid certificate from a "
            "trusted CA, not necessarily one issued for the target hostname."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-295"],
        category="cryptography",
        patterns={
            "python": LanguagePattern(
                r'(?:check_hostname\s*=\s*False)',
            ),
            "javascript": LanguagePattern(
                r'(?:checkServerIdentity\s*:\s*\(\)\s*=>|checkServerIdentity.*null)',
            ),
            "java": LanguagePattern(
                r'(?:setHostnameVerifier\s*\(\s*new\s*HostnameVerifier|HostnameVerifier.*return\s+true)',
            ),
            "csharp": LanguagePattern(
                r'(?:CheckCertificateRevocationList\s*=\s*false)',
            ),
            "go": LanguagePattern(
                r'InsecureSkipVerify\s*:\s*true',
            ),
            "php": LanguagePattern(
                r'(?:CURLOPT_SSL_VERIFYHOST\s*,\s*(?:false|0))',
            ),
        },
        fix_suggestion="Always verify hostnames in SSL/TLS connections. Use the default hostname verification.",
    ),

    # =========================================================================
    # CR012: Weak TLS Version (CWE-326)
    # =========================================================================
    CryptoRule(
        id="CR012",
        title="Weak TLS version (TLS 1.0/1.1 or SSLv3)",
        description=(
            "An outdated TLS version (TLS 1.0, TLS 1.1) or SSLv3 is used. These protocols "
            "have known vulnerabilities (POODLE, BEAST, etc.) and are deprecated. "
            "TLS 1.2 or TLS 1.3 should be the minimum version used."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-326"],
        category="cryptography",
        patterns={
            "python": LanguagePattern(
                r'(?:ssl\.PROTOCOL_SSLv3|ssl\.PROTOCOL_TLSv1(?:_1)?|TLSv1(?:_1)?)',
            ),
            "javascript": LanguagePattern(
                r'(?:secureProtocol\s*:\s*["\'](?:SSLv3|TLSv1|TLSv1_1)|minVersion\s*:\s*["\']TLS(?:v)?1(?:\.1)?["\'])',
            ),
            "java": LanguagePattern(
                r'(?:SSLContext\.getInstance\s*\(\s*["\'](?:SSL|SSLv3|TLS|TLSv1|TLSv1\.1)["\']|setEnabledProtocols.*SSLv3|TLSv1)',
            ),
            "csharp": LanguagePattern(
                r'(?:SecurityProtocolType\.(?:Ssl3|Tls|Tls11)|SslProtocols\.(?:Ssl3|Tls|Tls11))',
            ),
            "go": LanguagePattern(
                r'(?:MinVersion\s*:\s*tls\.Version(?:SSL30|TLS10|TLS11))',
            ),
            "php": LanguagePattern(
                r'(?:CURL_SSLVERSION_(?:SSLv3|TLSv1(?:_1)?)|stream_socket_enable_crypto.*STREAM_CRYPTO_METHOD_(?:SSLv3|TLSv1))',
            ),
        },
        fix_suggestion="Use TLS 1.2 or TLS 1.3 as the minimum version. Disable SSLv3, TLS 1.0, and TLS 1.1.",
    ),
]


# =============================================================================
# SCANNER IMPLEMENTATION
# =============================================================================

class CryptoErrorDetector(BaseScanner):
    """
    Detects cryptographic vulnerabilities and anti-patterns.

    Scans for weak algorithms, hardcoded keys, insecure random,
    certificate validation issues, and timing vulnerabilities.
    """

    SCANNER_VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        self._compiled_patterns: Dict[str, Dict[str, re.Pattern]] = {}
        self._compiled_fp_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance."""
        for rule in CRYPTO_RULES:
            self._compiled_patterns[rule.id] = {}
            for lang, lang_pattern in rule.patterns.items():
                try:
                    self._compiled_patterns[rule.id][lang] = re.compile(
                        lang_pattern.pattern,
                        lang_pattern.flags
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
        return ScannerType.CRYPTO_ERROR

    @property
    def supported_languages(self) -> Set[str]:
        return set(SUPPORTED_LANGUAGES.keys())

    @property
    def supported_extensions(self) -> Set[str]:
        extensions = set()
        for lang_def in SUPPORTED_LANGUAGES.values():
            extensions.update(lang_def.extensions)
        return extensions

    def is_available(self) -> bool:
        return True

    def get_scanner_version(self) -> Optional[str]:
        return self.SCANNER_VERSION

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect language from file extension."""
        ext = file_path.suffix.lower()
        for lang_name, lang_def in SUPPORTED_LANGUAGES.items():
            if ext in lang_def.extensions:
                return lang_name
        return None

    def _has_context_keyword(
        self,
        lines: List[str],
        match_line: int,
        keywords: List[str],
        window: int
    ) -> bool:
        """Check if any context keyword appears near the match."""
        if not keywords:
            return True

        start_line = max(0, match_line - window)
        end_line = min(len(lines), match_line + window)
        context_text = "\n".join(lines[start_line:end_line]).lower()

        return any(kw.lower() in context_text for kw in keywords)

    def _is_false_positive(
        self,
        rule_id: str,
        matched_text: str,
        context_lines: str
    ) -> bool:
        """Check if match is a false positive."""
        fp_patterns = self._compiled_fp_patterns.get(rule_id, [])
        full_text = matched_text + " " + context_lines

        for fp_pattern in fp_patterns:
            if fp_pattern.search(full_text):
                return True
        return False

    async def scan(
        self,
        target_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> ScanResult:
        """Execute cryptographic security scan."""
        started_at = datetime.now(timezone.utc)
        findings = []
        files_scanned = 0
        errors = []

        # Get files to scan
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

                for rule in CRYPTO_RULES:
                    # Get language-specific pattern
                    compiled_pattern = self._compiled_patterns.get(rule.id, {}).get(language)
                    if not compiled_pattern:
                        continue

                    for match in compiled_pattern.finditer(content):
                        # Calculate line number
                        line_start = content[:match.start()].count("\n") + 1
                        line_end = content[:match.end()].count("\n") + 1

                        # Check context keywords if required
                        if rule.require_context:
                            if not self._has_context_keyword(
                                lines, line_start,
                                rule.context_keywords, rule.context_window_lines
                            ):
                                continue

                        # Get snippet
                        snippet_start = max(0, line_start - 2)
                        snippet_end = min(len(lines), line_end + 3)
                        snippet = "\n".join(lines[snippet_start:snippet_end])

                        # Check for false positives
                        if self._is_false_positive(rule.id, match.group(), snippet):
                            continue

                        finding = SecurityFinding(
                            id=f"crypto-{rule.id}-{file_path}:{line_start}",
                            rule_id=rule.id,
                            title=rule.title,
                            description=rule.description,
                            severity=rule.severity,
                            scanner=self.scanner_type,
                            location=Location(
                                file_path=str(file_path),
                                start_line=line_start,
                                end_line=line_end,
                                snippet=snippet,
                            ),
                            cwe_ids=rule.cwe_ids,
                            category=rule.category,
                            tags={f"lang:{language}", "cryptography"},
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
        """Get summary of all rules."""
        return {
            "total_rules": len(CRYPTO_RULES),
            "rules": [
                {
                    "id": rule.id,
                    "title": rule.title,
                    "severity": rule.severity.value,
                    "cwe_ids": rule.cwe_ids,
                    "category": rule.category,
                    "languages": list(rule.patterns.keys()),
                }
                for rule in CRYPTO_RULES
            ],
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_crypto_error_detector() -> CryptoErrorDetector:
    """Factory function to create crypto error detector."""
    return CryptoErrorDetector()
