"""
Generic Multi-Language Security Scanner.

Detects language-agnostic security anti-patterns across all programming languages.
These patterns represent fundamental security issues that manifest similarly
regardless of the specific language syntax.

Based on CVD-2025-001 findings from HCI-CRS security audit.

Detected Anti-Patterns:
- CWE-337/330: Weak PRNG for security contexts
- CWE-602/841: Security check without enforcement
- CWE-521: Weak password generation
- CWE-200: Sensitive data in session/memory
- CWE-601: Incomplete URL validation (protocol-relative bypass)
- CWE-798: Hardcoded security values
"""

import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple
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
    comment_patterns: List[str] = field(default_factory=list)
    string_delimiters: List[str] = field(default_factory=lambda: ['"', "'"])


SUPPORTED_LANGUAGES: Dict[str, LanguageDefinition] = {
    "vbnet": LanguageDefinition(
        name="VB.NET",
        extensions={".vb", ".vbs", ".asp", ".aspx", ".ascx", ".asmx", ".ashx"},
        comment_patterns=[r"'.*$", r"REM\s+.*$"],
    ),
    "csharp": LanguageDefinition(
        name="C#",
        extensions={".cs", ".cshtml", ".razor"},
        comment_patterns=[r"//.*$", r"/\*.*?\*/"],
    ),
    "java": LanguageDefinition(
        name="Java",
        extensions={".java", ".jsp", ".jspx"},
        comment_patterns=[r"//.*$", r"/\*.*?\*/"],
    ),
    "python": LanguageDefinition(
        name="Python",
        extensions={".py", ".pyw", ".pyx"},
        comment_patterns=[r"#.*$", r'""".*?"""', r"'''.*?'''"],
    ),
    "javascript": LanguageDefinition(
        name="JavaScript",
        extensions={".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte"},
        comment_patterns=[r"//.*$", r"/\*.*?\*/"],
    ),
    "php": LanguageDefinition(
        name="PHP",
        extensions={".php", ".phtml", ".php3", ".php4", ".php5", ".phps"},
        comment_patterns=[r"//.*$", r"#.*$", r"/\*.*?\*/"],
    ),
    "go": LanguageDefinition(
        name="Go",
        extensions={".go"},
        comment_patterns=[r"//.*$", r"/\*.*?\*/"],
    ),
    "ruby": LanguageDefinition(
        name="Ruby",
        extensions={".rb", ".erb", ".rake", ".gemspec"},
        comment_patterns=[r"#.*$", r"=begin.*?=end"],
    ),
    "rust": LanguageDefinition(
        name="Rust",
        extensions={".rs"},
        comment_patterns=[r"//.*$", r"/\*.*?\*/"],
    ),
    "kotlin": LanguageDefinition(
        name="Kotlin",
        extensions={".kt", ".kts"},
        comment_patterns=[r"//.*$", r"/\*.*?\*/"],
    ),
    "scala": LanguageDefinition(
        name="Scala",
        extensions={".scala", ".sc"},
        comment_patterns=[r"//.*$", r"/\*.*?\*/"],
    ),
    "swift": LanguageDefinition(
        name="Swift",
        extensions={".swift"},
        comment_patterns=[r"//.*$", r"/\*.*?\*/"],
    ),
}


# =============================================================================
# GENERIC SECURITY RULES
# =============================================================================

@dataclass
class LanguagePattern:
    """Pattern for a specific language."""
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE


@dataclass
class GenericSecurityRule:
    """
    A generic security rule with language-specific patterns.

    Context-aware detection uses proximity to security keywords
    to reduce false positives.
    """
    id: str
    title: str
    description: str
    severity: Severity
    cwe_ids: List[str]
    category: str

    # Language-specific regex patterns
    patterns: Dict[str, LanguagePattern]

    # Context keywords - finding is more relevant if these appear nearby
    context_keywords: List[str] = field(default_factory=list)
    context_window_lines: int = 10  # Lines to search for context

    # If True, require at least one context keyword nearby
    require_context: bool = False

    # Fix suggestions per language
    fix_suggestions: Dict[str, str] = field(default_factory=dict)
    default_fix: str = ""

    # False positive hints
    false_positive_patterns: List[str] = field(default_factory=list)


# =============================================================================
# RULE DEFINITIONS
# =============================================================================

GENERIC_SECURITY_RULES: List[GenericSecurityRule] = [
    # =========================================================================
    # CWE-337/330: Weak PRNG for Security Contexts
    # =========================================================================
    GenericSecurityRule(
        id="GEN-CWE-337-001",
        title="Weak PRNG used for security-sensitive operation",
        description=(
            "Non-cryptographic random number generator detected in context that "
            "suggests security-sensitive use (tokens, passwords, keys, etc.). "
            "Standard RNGs like Random(), Math.random(), or rand() are predictable "
            "and should not be used for cryptographic purposes."
        ),
        severity=Severity.CRITICAL,
        cwe_ids=["CWE-337", "CWE-330"],
        category="cryptography",
        context_keywords=[
            "token", "password", "passwd", "pwd", "otp", "secret", "key",
            "pin", "code", "salt", "nonce", "iv", "session", "auth",
            "credential", "apikey", "api_key", "access_token", "refresh_token",
            "csrf", "xsrf", "2fa", "mfa", "totp", "hotp", "verification",
        ],
        context_window_lines=15,
        require_context=True,
        patterns={
            "vbnet": LanguagePattern(
                r"(?:Dim|Private|Public|Protected)\s+\w+\s+As\s+(?:New\s+)?Random(?:\s*\(\s*\))?"
            ),
            "csharp": LanguagePattern(
                r"(?:new\s+Random\s*\(|Random\s+\w+\s*=\s*new\s+Random)"
            ),
            "java": LanguagePattern(
                r"(?:new\s+Random\s*\(|Random\s+\w+\s*=\s*new\s+Random)"
            ),
            "python": LanguagePattern(
                r"(?:random\.(?:random|randint|choice|shuffle|sample|randrange|uniform)\s*\(|"
                r"from\s+random\s+import)"
            ),
            "javascript": LanguagePattern(
                r"Math\.random\s*\("
            ),
            "php": LanguagePattern(
                r"(?:rand|mt_rand|array_rand|shuffle)\s*\("
            ),
            "go": LanguagePattern(
                r'(?:rand\.(?:Int|Intn|Float|Seed|Perm)\s*\(|"math/rand")'
            ),
            "ruby": LanguagePattern(
                r"(?:rand\s*\(?|Random\.(?:new|rand)\s*\()"
            ),
            "rust": LanguagePattern(
                r"(?:rand::(?:thread_rng|random|Rng)|use\s+rand::)"
            ),
            "kotlin": LanguagePattern(
                r"(?:Random\s*\(\s*\)|kotlin\.random\.Random)"
            ),
        },
        fix_suggestions={
            "vbnet": "Use System.Security.Cryptography.RandomNumberGenerator.Create()",
            "csharp": "Use System.Security.Cryptography.RandomNumberGenerator.Create()",
            "java": "Use java.security.SecureRandom instead of java.util.Random",
            "python": "Use secrets.token_hex(), secrets.token_bytes(), or secrets.choice()",
            "javascript": "Use crypto.getRandomValues() or crypto.randomBytes() (Node.js)",
            "php": "Use random_bytes() or random_int() (PHP 7+)",
            "go": "Use crypto/rand instead of math/rand",
            "ruby": "Use SecureRandom.hex(), SecureRandom.random_bytes(), etc.",
            "rust": "Use rand::rngs::OsRng or getrandom crate",
            "kotlin": "Use java.security.SecureRandom",
        },
        default_fix="Replace with cryptographically secure random number generator (CSPRNG).",
    ),

    # =========================================================================
    # CWE-337-002: Direct use of time-based seeds
    # =========================================================================
    GenericSecurityRule(
        id="GEN-CWE-337-002",
        title="Time-based seed for random number generator",
        description=(
            "Random number generator seeded with predictable time value. "
            "Values like current time, ticks, or timestamps are observable "
            "and make the RNG output predictable."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-337", "CWE-330"],
        category="cryptography",
        context_keywords=[
            "token", "password", "secret", "key", "otp", "random", "seed",
        ],
        patterns={
            "vbnet": LanguagePattern(
                r"New\s+Random\s*\(\s*(?:Environment\.TickCount|DateTime\.Now\.Ticks|"
                r"Date\.Now|Now\s*\)|GetTickCount)"
            ),
            "csharp": LanguagePattern(
                r"new\s+Random\s*\(\s*(?:Environment\.TickCount|DateTime\.Now\.Ticks|"
                r"DateTime\.UtcNow\.Ticks|unchecked.*DateTime)"
            ),
            "java": LanguagePattern(
                r"new\s+Random\s*\(\s*(?:System\.currentTimeMillis|System\.nanoTime|"
                r"new\s+Date\s*\(\s*\)\.getTime)"
            ),
            "python": LanguagePattern(
                r"random\.seed\s*\(\s*(?:time\.time|datetime\.now|int\s*\(\s*time)"
            ),
            "javascript": LanguagePattern(
                r"(?:seed|srand)\s*\(\s*(?:Date\.now|new\s+Date|performance\.now)"
            ),
            "php": LanguagePattern(
                r"(?:srand|mt_srand)\s*\(\s*(?:time\s*\(|microtime|hrtime)"
            ),
            "go": LanguagePattern(
                r"rand\.Seed\s*\(\s*(?:time\.Now|UnixNano)"
            ),
        },
        fix_suggestions={
            "default": "Do not seed RNG with time. Use CSPRNG which self-seeds from OS entropy.",
        },
        default_fix="Remove manual seeding; use CSPRNG which obtains entropy from the OS.",
    ),

    # =========================================================================
    # CWE-602/841: Security Check Without Enforcement
    # =========================================================================
    GenericSecurityRule(
        id="GEN-CWE-602-001",
        title="Security validation without blocking action",
        description=(
            "A security-related condition is checked but no blocking action "
            "(return, throw, exit, redirect) follows. This allows code to "
            "continue executing even when security checks fail."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-602", "CWE-841"],
        category="authentication",
        context_keywords=[
            "password", "auth", "login", "permission", "access", "security",
            "credential", "token", "session", "role", "admin", "privilege",
            "authorize", "authenticate", "verify", "validate", "check",
        ],
        context_window_lines=5,
        require_context=True,
        patterns={
            # These patterns look for If/if with security keywords that don't have exit statements
            "vbnet": LanguagePattern(
                r"If\s+.*(?:Password|Auth|Login|Security|IsNull|IsEmpty).*Then\s*\r?\n"
                r"(?:(?!\s*(?:Exit\s+(?:Sub|Function)|Return|Response\.Redirect|Throw))[\s\S])*?"
                r"(?:End\s+If|Else)",
                flags=re.IGNORECASE | re.MULTILINE
            ),
            "csharp": LanguagePattern(
                r"if\s*\([^)]*(?:password|auth|user|login|security|null|empty)[^)]*\)\s*\{"
                r"(?:(?!\s*(?:return|throw|Response\.Redirect))[\s\S])*?\}",
                flags=re.IGNORECASE | re.MULTILINE
            ),
            "java": LanguagePattern(
                r"if\s*\([^)]*(?:password|auth|user|login|security|null)[^)]*\)\s*\{"
                r"(?:(?!\s*(?:return|throw\s+new))[\s\S])*?\}",
                flags=re.IGNORECASE | re.MULTILINE
            ),
            "python": LanguagePattern(
                r"if\s+.*(?:password|auth|user|login|security|none|not\s+).*:\s*\n"
                r"(?:(?!\s*(?:return|raise|redirect))[\s\S])*?(?=\n(?:else|elif|def|class|\S))",
                flags=re.IGNORECASE | re.MULTILINE
            ),
            "javascript": LanguagePattern(
                r"if\s*\([^)]*(?:password|auth|user|login|security|null|undefined)[^)]*\)\s*\{"
                r"(?:(?!\s*(?:return|throw|res\.redirect|next\s*\())[\s\S])*?\}",
                flags=re.IGNORECASE | re.MULTILINE
            ),
            "php": LanguagePattern(
                r"if\s*\([^)]*(?:password|\$_?auth|\$_?user|login|security|null|empty)[^)]*\)\s*\{"
                r"(?:(?!\s*(?:return|throw|exit|die|header.*Location))[\s\S])*?\}",
                flags=re.IGNORECASE | re.MULTILINE
            ),
            "go": LanguagePattern(
                r"if\s+.*(?:password|auth|user|login|err\s*!=\s*nil).*\s*\{"
                r"(?:(?!\s*(?:return|panic))[\s\S])*?\}",
                flags=re.IGNORECASE | re.MULTILINE
            ),
        },
        fix_suggestions={
            "vbnet": "Add 'Exit Sub', 'Exit Function', 'Return', or 'Response.Redirect' after security checks",
            "csharp": "Add 'return', 'throw', or redirect after security checks",
            "java": "Add 'return' or 'throw new Exception' after security checks",
            "python": "Add 'return', 'raise', or redirect after security checks",
            "javascript": "Add 'return', 'throw', or 'res.redirect()' after security checks",
            "php": "Add 'return', 'throw', 'exit', or 'header(Location:...)' after security checks",
            "go": "Add 'return' after error checks to prevent code continuation",
        },
        default_fix="Ensure all security checks are followed by blocking actions (return/throw/redirect).",
    ),

    # =========================================================================
    # CWE-521: Hardcoded Special Characters in Passwords
    # =========================================================================
    GenericSecurityRule(
        id="GEN-CWE-521-001",
        title="Hardcoded special character in password generation",
        description=(
            "Password generation uses a fixed special character (e.g., always '#'). "
            "This reduces password entropy and makes passwords more predictable. "
            "Special characters should be randomly selected from a diverse set."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-521", "CWE-330"],
        category="authentication",
        context_keywords=[
            "password", "passwd", "pwd", "generate", "random", "special",
        ],
        patterns={
            # Matches appending a single hardcoded special character
            "vbnet": LanguagePattern(
                r'\.Append\s*\(\s*["\'](#|!|\*|@|\$)["\']'
            ),
            "csharp": LanguagePattern(
                r'(?:\.Append|\.Add|\+=)\s*\(\s*["\'](#|!|\*|@|\$)["\']'
            ),
            "java": LanguagePattern(
                r'(?:\.append|\.add|\+=)\s*\(\s*["\'](#|!|\*|@|\$)["\']'
            ),
            "python": LanguagePattern(
                r'(?:\.append|\+=)\s*\(\s*["\'](#|!|\*|@|\$)["\']'
            ),
            "javascript": LanguagePattern(
                r'(?:\.push|\+=|concat)\s*\(\s*["\'](#|!|\*|@|\$)["\']'
            ),
            "php": LanguagePattern(
                r'(?:\.\s*=|\$\w+\s*\.=)\s*["\'](#|!|\*|@|\$)["\']'
            ),
            "go": LanguagePattern(
                r'(?:\+\s*=|\+=)\s*["\'](#|!|\*|@|\$)["\']'
            ),
            "ruby": LanguagePattern(
                r'(?:<<|push|\+=)\s*["\'](#|!|\*|@|\$)["\']'
            ),
        },
        fix_suggestions={
            "default": "Select special characters randomly from a set like: !@#$%^&*()_+-=[]{}|;:,.<>?",
        },
        default_fix="Use randomly selected special characters from a diverse character set.",
    ),

    # =========================================================================
    # CWE-521-002: Off-by-One in Character Range
    # =========================================================================
    GenericSecurityRule(
        id="GEN-CWE-521-002",
        title="Off-by-one error in character range calculation",
        description=(
            "Character range calculation may exclude expected characters. "
            "Formula like '25 * random + 65' generates A-Y but never Z. "
            "This reduces keyspace by ~21% per character position."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-521", "CWE-330"],
        category="cryptography",
        context_keywords=[
            "password", "token", "random", "char", "generate", "letter",
        ],
        patterns={
            # Matches formulas that produce off-by-one character ranges
            "vbnet": LanguagePattern(
                r"(?:25|51|61|35)\s*\*\s*(?:rnd|Random|Rnd).*\+\s*(?:65|97|48|33)"
            ),
            "csharp": LanguagePattern(
                r"(?:25|51|61|35)\s*\*\s*(?:rnd|random|Random).*\+\s*(?:65|97|48|33)"
            ),
            "java": LanguagePattern(
                r"(?:25|51|61|35)\s*\*\s*(?:rnd|random|Math\.random).*\+\s*(?:65|97|48|33)"
            ),
            "python": LanguagePattern(
                r"(?:25|51|61|35)\s*\*\s*(?:random\.random|randint).*\+\s*(?:65|97|48|33)"
            ),
            "javascript": LanguagePattern(
                r"(?:25|51|61|35)\s*\*\s*Math\.random.*\+\s*(?:65|97|48|33)"
            ),
            "php": LanguagePattern(
                r"(?:25|51|61|35)\s*\*\s*(?:rand|mt_rand).*\+\s*(?:65|97|48|33)"
            ),
        },
        fix_suggestions={
            "default": "Use 26 for A-Z, 52 for A-Za-z, 62 for A-Za-z0-9, 36 for A-Z0-9",
        },
        default_fix="Correct the multiplier: use 26 for A-Z, 52 for mixed case, etc.",
    ),

    # =========================================================================
    # CWE-200: Sensitive Data in Session/Storage
    # =========================================================================
    GenericSecurityRule(
        id="GEN-CWE-200-001",
        title="Sensitive data stored in session or client storage",
        description=(
            "Password, credentials, or other sensitive data is stored in session "
            "or client-side storage. This increases risk of exposure through "
            "session hijacking, XSS, or memory dumps."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-200", "CWE-522"],
        category="data_exposure",
        context_keywords=[],  # No context needed - the pattern itself is specific enough
        patterns={
            "vbnet": LanguagePattern(
                r'(?:Session|AppSession)\s*[\(\[]\s*["\'](?:Password|OldPassword|Wachtwoord|'
                r'Credential|Secret|ApiKey|AccessToken)["\']'
            ),
            "csharp": LanguagePattern(
                r'(?:Session|HttpContext\.Session|TempData)\s*\[\s*["\'](?:Password|'
                r'Credential|Secret|ApiKey|AccessToken)["\']'
            ),
            "java": LanguagePattern(
                r'(?:session|getSession\s*\(\s*\))\.(?:setAttribute|getAttribute)\s*\(\s*["\']'
                r'(?:password|credential|secret|apikey|token)["\']'
            ),
            "python": LanguagePattern(
                r'(?:session|request\.session)\s*\[\s*["\'](?:password|credential|secret|'
                r'api_key|access_token)["\']'
            ),
            "javascript": LanguagePattern(
                r'(?:localStorage|sessionStorage|cookies?)\.(?:setItem|getItem|\w+)\s*\(\s*'
                r'["\'](?:password|credential|secret|apiKey|accessToken|token)["\']'
            ),
            "php": LanguagePattern(
                r'\$_SESSION\s*\[\s*["\'](?:password|credential|secret|api_key|token)["\']'
            ),
            "go": LanguagePattern(
                r'session\.(?:Set|Get|Values)\s*\[\s*["\'](?:password|credential|secret|'
                r'apikey|token)["\']'
            ),
            "ruby": LanguagePattern(
                r'session\s*\[\s*:(?:password|credential|secret|api_key|token)\s*\]'
            ),
        },
        fix_suggestions={
            "default": "Never store passwords or secrets in session. Use secure, short-lived tokens instead.",
        },
        default_fix="Do not store sensitive data in session. Use hashed tokens or secure references.",
    ),

    # =========================================================================
    # CWE-601: Protocol-Relative URL Bypass
    # =========================================================================
    GenericSecurityRule(
        id="GEN-CWE-601-001",
        title="Incomplete redirect URL validation (protocol-relative bypass)",
        description=(
            "URL validation checks for '/' prefix but not '//' prefix. "
            "This allows protocol-relative URLs like '//evil.com' to bypass "
            "the check and redirect users to malicious sites."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-601"],
        category="redirect",
        context_keywords=[
            "redirect", "url", "return", "next", "callback", "continue",
        ],
        patterns={
            # Matches startsWith("/") without checking for "//"
            "vbnet": LanguagePattern(
                r'StartsWith\s*\(\s*["\']\/["\']'
            ),
            "csharp": LanguagePattern(
                r'\.StartsWith\s*\(\s*["\']\/["\']'
            ),
            "java": LanguagePattern(
                r'\.startsWith\s*\(\s*["\']\/["\']'
            ),
            "python": LanguagePattern(
                r'\.startswith\s*\(\s*["\']\/["\']'
            ),
            "javascript": LanguagePattern(
                r'\.startsWith\s*\(\s*["\']\/["\']'
            ),
            "php": LanguagePattern(
                r'(?:strpos|str_starts_with)\s*\([^,]+,\s*["\']\/["\']'
            ),
            "go": LanguagePattern(
                r'strings\.HasPrefix\s*\([^,]+,\s*["\']\/["\']'
            ),
            "ruby": LanguagePattern(
                r'\.start_with\?\s*\(\s*["\']\/["\']'
            ),
        },
        false_positive_patterns=[
            r'StartsWith.*\/\/.*StartsWith',  # Already checks for //
            r'&&.*!.*\/\/',  # Has negative check for //
        ],
        fix_suggestions={
            "default": "Also check that URL does not start with '//' to block protocol-relative URLs.",
        },
        default_fix="Add check: url.startsWith('/') && !url.startsWith('//')",
    ),

    # =========================================================================
    # CWE-798: Hardcoded Credentials
    # =========================================================================
    GenericSecurityRule(
        id="GEN-CWE-798-001",
        title="Hardcoded password or secret",
        description=(
            "Password, API key, or secret appears to be hardcoded in source code. "
            "Credentials should be stored in secure configuration, environment "
            "variables, or a secrets management system."
        ),
        severity=Severity.HIGH,
        cwe_ids=["CWE-798", "CWE-259"],
        category="credentials",
        context_keywords=[],  # Pattern is specific enough
        patterns={
            # Universal pattern - matches across most languages
            "vbnet": LanguagePattern(
                r'(?:password|passwd|pwd|secret|api_?key|apikey|auth_?token|'
                r'access_?token|private_?key)\s*=\s*["\'][^"\']{8,}["\']',
                flags=re.IGNORECASE
            ),
            "csharp": LanguagePattern(
                r'(?:password|passwd|pwd|secret|api_?key|apikey|auth_?token|'
                r'access_?token|private_?key)\s*=\s*["\'][^"\']{8,}["\']',
                flags=re.IGNORECASE
            ),
            "java": LanguagePattern(
                r'(?:password|passwd|pwd|secret|api_?key|apikey|auth_?token|'
                r'access_?token|private_?key)\s*=\s*["\'][^"\']{8,}["\']',
                flags=re.IGNORECASE
            ),
            "python": LanguagePattern(
                r'(?:password|passwd|pwd|secret|api_?key|apikey|auth_?token|'
                r'access_?token|private_?key)\s*=\s*["\'][^"\']{8,}["\']',
                flags=re.IGNORECASE
            ),
            "javascript": LanguagePattern(
                r'(?:password|passwd|pwd|secret|api_?key|apikey|auth_?token|'
                r'access_?token|private_?key)\s*[=:]\s*["\'][^"\']{8,}["\']',
                flags=re.IGNORECASE
            ),
            "php": LanguagePattern(
                r'(?:\$password|\$passwd|\$pwd|\$secret|\$api_?key|\$apikey|'
                r'\$auth_?token|\$access_?token)\s*=\s*["\'][^"\']{8,}["\']',
                flags=re.IGNORECASE
            ),
            "go": LanguagePattern(
                r'(?:password|passwd|pwd|secret|apiKey|apikey|authToken|'
                r'accessToken|privateKey)\s*(?:=|:=)\s*["\'][^"\']{8,}["\']',
                flags=re.IGNORECASE
            ),
            "ruby": LanguagePattern(
                r'(?:password|passwd|pwd|secret|api_?key|apikey|auth_?token|'
                r'access_?token|private_?key)\s*=\s*["\'][^"\']{8,}["\']',
                flags=re.IGNORECASE
            ),
        },
        false_positive_patterns=[
            r'example',
            r'placeholder',
            r'your[_-]?(?:password|key|secret)',
            r'xxx+',
            r'\*{4,}',
            r'<[^>]+>',  # Template variables
            r'\$\{',  # Variable interpolation
            r'%\w+%',  # Environment variable reference
        ],
        fix_suggestions={
            "default": "Store credentials in environment variables, secure config, or secrets manager.",
        },
        default_fix="Move credentials to secure storage (env vars, secrets manager, secure config).",
    ),

    # =========================================================================
    # CWE-841: Cancel Button Bypassing Workflow
    # =========================================================================
    GenericSecurityRule(
        id="GEN-CWE-841-001",
        title="Cancel/Back button may bypass mandatory security workflow",
        description=(
            "A cancel or back button redirects without checking if mandatory "
            "security steps (like setting up 2FA or security questions) have "
            "been completed. Users can skip required security configuration."
        ),
        severity=Severity.MEDIUM,
        cwe_ids=["CWE-841"],
        category="workflow",
        context_keywords=[
            "security", "question", "2fa", "mfa", "onboard", "setup",
            "mandatory", "required", "force",
        ],
        patterns={
            "vbnet": LanguagePattern(
                r'(?:btnTerug|btnCancel|btnAnnuleren|btnBack|btnSkip)_Click.*'
                r'Response\.Redirect',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "csharp": LanguagePattern(
                r'(?:CancelButton|BackButton|SkipButton).*(?:Click|Handler).*'
                r'(?:Redirect|Navigate)',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "java": LanguagePattern(
                r'(?:cancelButton|backButton|skipButton).*(?:onClick|Listener).*'
                r'(?:redirect|navigate|sendRedirect)',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "python": LanguagePattern(
                r'(?:cancel|back|skip).*(?:click|button|handler).*redirect',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "javascript": LanguagePattern(
                r'(?:cancel|back|skip)(?:Button|Btn)?.*(?:onclick|click|handler).*'
                r'(?:redirect|navigate|location\.href|push)',
                flags=re.IGNORECASE | re.DOTALL
            ),
            "php": LanguagePattern(
                r'(?:cancel|back|skip).*(?:click|submit|handler).*'
                r'(?:header.*Location|redirect)',
                flags=re.IGNORECASE | re.DOTALL
            ),
        },
        fix_suggestions={
            "default": "Verify all mandatory steps are complete before allowing navigation away.",
        },
        default_fix="Check if required security setup is complete before allowing cancel/back action.",
    ),
]


# =============================================================================
# SCANNER IMPLEMENTATION
# =============================================================================

class GenericSecurityScanner(BaseScanner):
    """
    Multi-language security scanner for generic anti-patterns.

    Detects language-agnostic security issues that appear across
    all programming languages with similar patterns.
    """

    SCANNER_VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        self._compiled_patterns: Dict[str, Dict[str, re.Pattern]] = {}
        self._compiled_fp_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance."""
        for rule in GENERIC_SECURITY_RULES:
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
        return ScannerType.GENERIC_SECURITY

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
        content: str,
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
        """Execute multi-language security scan."""
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

                for rule in GENERIC_SECURITY_RULES:
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
                                content, lines, line_start,
                                rule.context_keywords, rule.context_window_lines
                            ):
                                continue

                        # Get snippet
                        snippet_start = max(0, line_start - 2)
                        snippet_end = min(len(lines), line_end + 3)
                        snippet_lines = lines[snippet_start:snippet_end]
                        snippet = "\n".join(snippet_lines)

                        # Check for false positives
                        if self._is_false_positive(rule.id, match.group(), snippet):
                            continue

                        # Get language-specific fix suggestion
                        fix_text = rule.fix_suggestions.get(
                            language,
                            rule.fix_suggestions.get("default", rule.default_fix)
                        )

                        finding = SecurityFinding(
                            id=f"generic-{rule.id}-{file_path}:{line_start}",
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
                            tags={f"lang:{language}"},
                        )

                        if fix_text:
                            finding.suggested_fixes.append(
                                SuggestedFix(description=fix_text)
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
            "total_rules": len(GENERIC_SECURITY_RULES),
            "rules": [
                {
                    "id": rule.id,
                    "title": rule.title,
                    "severity": rule.severity.value,
                    "cwe_ids": rule.cwe_ids,
                    "category": rule.category,
                    "languages": list(rule.patterns.keys()),
                }
                for rule in GENERIC_SECURITY_RULES
            ],
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
            "total_extensions": len(self.supported_extensions),
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_generic_security_scanner() -> GenericSecurityScanner:
    """Factory function to create generic security scanner."""
    return GenericSecurityScanner()
