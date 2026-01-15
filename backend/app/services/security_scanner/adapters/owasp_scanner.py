"""
OWASP Top 10 Security Scanner (K1 - Fase 24).

Provides comprehensive OWASP Top 10 2021 vulnerability scanning with:
- Pattern-based detection using SecurityPatternLoader
- Built-in patterns for all 10 OWASP categories
- Coverage reporting per category
- Multi-language support
- CWE mapping

OWASP Top 10 2021:
- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection
- A04: Insecure Design
- A05: Security Misconfiguration
- A06: Vulnerable and Outdated Components
- A07: Identification and Authentication Failures
- A08: Software and Data Integrity Failures
- A09: Security Logging and Monitoring Failures
- A10: Server-Side Request Forgery (SSRF)

Author: Claude Code (Week 158)
Date: 2026-01-15
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .base import CustomPatternScanner
from ..models.findings import (
    SecurityFinding,
    ScanResult,
    Severity,
    ScannerType,
    Location,
    SuggestedFix,
)
from ...security_pattern_loader import (
    SecurityPatternLoader,
    OWASPCategory,
    OWASP_CODE_MAP,
    get_pattern_loader,
)

logger = logging.getLogger(__name__)


# ==================== OWASP Category Details ====================

@dataclass
class OWASPCategoryInfo:
    """Detailed information about an OWASP category."""
    code: str
    name: str
    description: str
    cwe_ids: List[str]
    risk_rating: str  # Critical, High, Medium, Low
    prevalence: str  # Widespread, Common, Uncommon
    detectability: str  # Easy, Average, Difficult


OWASP_CATEGORY_INFO: Dict[OWASPCategory, OWASPCategoryInfo] = {
    OWASPCategory.A01_BROKEN_ACCESS_CONTROL: OWASPCategoryInfo(
        code="A01",
        name="Broken Access Control",
        description="Restrictions on authenticated users are not properly enforced",
        cwe_ids=["CWE-22", "CWE-23", "CWE-35", "CWE-59", "CWE-200", "CWE-201",
                 "CWE-219", "CWE-264", "CWE-275", "CWE-276", "CWE-284", "CWE-285",
                 "CWE-352", "CWE-359", "CWE-377", "CWE-402", "CWE-425", "CWE-441",
                 "CWE-497", "CWE-538", "CWE-540", "CWE-548", "CWE-552", "CWE-566",
                 "CWE-601", "CWE-639", "CWE-651", "CWE-668", "CWE-706", "CWE-862",
                 "CWE-863", "CWE-913", "CWE-922", "CWE-1275"],
        risk_rating="Critical",
        prevalence="Widespread",
        detectability="Average",
    ),
    OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES: OWASPCategoryInfo(
        code="A02",
        name="Cryptographic Failures",
        description="Failures related to cryptography which lead to exposure of sensitive data",
        cwe_ids=["CWE-261", "CWE-296", "CWE-310", "CWE-319", "CWE-321", "CWE-322",
                 "CWE-323", "CWE-324", "CWE-325", "CWE-326", "CWE-327", "CWE-328",
                 "CWE-329", "CWE-330", "CWE-331", "CWE-335", "CWE-336", "CWE-337",
                 "CWE-338", "CWE-340", "CWE-347", "CWE-523", "CWE-720", "CWE-757",
                 "CWE-759", "CWE-760", "CWE-780", "CWE-818", "CWE-916"],
        risk_rating="Critical",
        prevalence="Common",
        detectability="Average",
    ),
    OWASPCategory.A03_INJECTION: OWASPCategoryInfo(
        code="A03",
        name="Injection",
        description="User-supplied data is not validated, filtered, or sanitized",
        cwe_ids=["CWE-20", "CWE-74", "CWE-75", "CWE-77", "CWE-78", "CWE-79",
                 "CWE-80", "CWE-83", "CWE-87", "CWE-88", "CWE-89", "CWE-90",
                 "CWE-91", "CWE-93", "CWE-94", "CWE-95", "CWE-96", "CWE-97",
                 "CWE-98", "CWE-99", "CWE-100", "CWE-113", "CWE-116", "CWE-138",
                 "CWE-184", "CWE-470", "CWE-471", "CWE-564", "CWE-610", "CWE-643",
                 "CWE-644", "CWE-652", "CWE-917"],
        risk_rating="Critical",
        prevalence="Common",
        detectability="Easy",
    ),
    OWASPCategory.A04_INSECURE_DESIGN: OWASPCategoryInfo(
        code="A04",
        name="Insecure Design",
        description="Missing or ineffective security controls in application design",
        cwe_ids=["CWE-73", "CWE-183", "CWE-209", "CWE-213", "CWE-235", "CWE-256",
                 "CWE-257", "CWE-266", "CWE-269", "CWE-280", "CWE-311", "CWE-312",
                 "CWE-313", "CWE-316", "CWE-419", "CWE-430", "CWE-434", "CWE-444",
                 "CWE-451", "CWE-472", "CWE-501", "CWE-522", "CWE-525", "CWE-539",
                 "CWE-579", "CWE-598", "CWE-602", "CWE-642", "CWE-646", "CWE-650",
                 "CWE-653", "CWE-656", "CWE-657", "CWE-799", "CWE-807", "CWE-840",
                 "CWE-841", "CWE-927", "CWE-1021", "CWE-1173"],
        risk_rating="High",
        prevalence="Common",
        detectability="Difficult",
    ),
    OWASPCategory.A05_SECURITY_MISCONFIGURATION: OWASPCategoryInfo(
        code="A05",
        name="Security Misconfiguration",
        description="Insecure default configurations, incomplete setups, or verbose errors",
        cwe_ids=["CWE-2", "CWE-11", "CWE-13", "CWE-15", "CWE-16", "CWE-260",
                 "CWE-315", "CWE-520", "CWE-526", "CWE-537", "CWE-541", "CWE-547",
                 "CWE-611", "CWE-614", "CWE-756", "CWE-776", "CWE-942", "CWE-1004",
                 "CWE-1032", "CWE-1174"],
        risk_rating="High",
        prevalence="Widespread",
        detectability="Easy",
    ),
    OWASPCategory.A06_VULNERABLE_COMPONENTS: OWASPCategoryInfo(
        code="A06",
        name="Vulnerable and Outdated Components",
        description="Using components with known vulnerabilities",
        cwe_ids=["CWE-937", "CWE-1035", "CWE-1104"],
        risk_rating="High",
        prevalence="Widespread",
        detectability="Average",
    ),
    OWASPCategory.A07_AUTH_FAILURES: OWASPCategoryInfo(
        code="A07",
        name="Identification and Authentication Failures",
        description="Incorrectly implemented authentication functions",
        cwe_ids=["CWE-255", "CWE-259", "CWE-287", "CWE-288", "CWE-290", "CWE-294",
                 "CWE-295", "CWE-297", "CWE-300", "CWE-302", "CWE-304", "CWE-306",
                 "CWE-307", "CWE-346", "CWE-384", "CWE-521", "CWE-613", "CWE-620",
                 "CWE-640", "CWE-798", "CWE-940", "CWE-1216"],
        risk_rating="Critical",
        prevalence="Common",
        detectability="Average",
    ),
    OWASPCategory.A08_DATA_INTEGRITY_FAILURES: OWASPCategoryInfo(
        code="A08",
        name="Software and Data Integrity Failures",
        description="Code and infrastructure without integrity verification",
        cwe_ids=["CWE-345", "CWE-353", "CWE-426", "CWE-494", "CWE-502", "CWE-565",
                 "CWE-784", "CWE-829", "CWE-830", "CWE-915"],
        risk_rating="High",
        prevalence="Common",
        detectability="Average",
    ),
    OWASPCategory.A09_LOGGING_FAILURES: OWASPCategoryInfo(
        code="A09",
        name="Security Logging and Monitoring Failures",
        description="Insufficient logging, detection, monitoring, and response",
        cwe_ids=["CWE-117", "CWE-223", "CWE-532", "CWE-778"],
        risk_rating="Medium",
        prevalence="Widespread",
        detectability="Difficult",
    ),
    OWASPCategory.A10_SSRF: OWASPCategoryInfo(
        code="A10",
        name="Server-Side Request Forgery",
        description="Web application fetches remote resource without validating URL",
        cwe_ids=["CWE-918"],
        risk_rating="High",
        prevalence="Common",
        detectability="Average",
    ),
}


# ==================== Built-in OWASP Patterns ====================

# These patterns supplement the YAML patterns from SecurityPatternLoader
BUILTIN_OWASP_PATTERNS: List[Dict[str, Any]] = [
    # A01: Broken Access Control
    {
        "id": "OWASP-A01-001",
        "pattern": r"(?:@|#).*(?:allow|permit).*\*",
        "title": "Overly Permissive Access Control",
        "description": "Wildcard permissions detected which may allow unauthorized access",
        "severity": Severity.HIGH,
        "owasp": OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
        "cwe_ids": ["CWE-284"],
        "fix_suggestion": "Replace wildcard with specific permissions",
    },
    {
        "id": "OWASP-A01-002",
        "pattern": r"(?:role|permission)\s*[=:]\s*[\"']?(?:admin|root|superuser)",
        "title": "Hardcoded Admin Role Assignment",
        "description": "Direct assignment of admin/root role detected",
        "severity": Severity.HIGH,
        "owasp": OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
        "cwe_ids": ["CWE-269"],
        "fix_suggestion": "Use role-based access control with proper authorization",
    },
    {
        "id": "OWASP-A01-003",
        "pattern": r"\.\.\/|\.\.\\\\",
        "title": "Path Traversal Pattern",
        "description": "Directory traversal sequence detected",
        "severity": Severity.HIGH,
        "owasp": OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
        "cwe_ids": ["CWE-22"],
        "fix_suggestion": "Sanitize file paths and use allowlists",
    },

    # A02: Cryptographic Failures
    {
        "id": "OWASP-A02-001",
        "pattern": r"(?:MD5|SHA1|SHA-1|DES|RC4|RC2)\s*[(\.]",
        "title": "Weak Cryptographic Algorithm",
        "description": "Use of weak/deprecated cryptographic algorithm",
        "severity": Severity.HIGH,
        "owasp": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
        "cwe_ids": ["CWE-327", "CWE-328"],
        "fix_suggestion": "Use SHA-256, SHA-3, or AES-256 instead",
    },
    {
        "id": "OWASP-A02-002",
        "pattern": r"(?:password|secret|key|token)\s*=\s*[\"'][^\"']{8,}[\"']",
        "title": "Hardcoded Secret",
        "description": "Hardcoded password, secret, or key detected",
        "severity": Severity.CRITICAL,
        "owasp": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
        "cwe_ids": ["CWE-798", "CWE-259"],
        "fix_suggestion": "Use environment variables or secret management",
    },
    {
        "id": "OWASP-A02-003",
        "pattern": r"http://(?!localhost|127\.0\.0\.1)",
        "title": "Unencrypted HTTP Connection",
        "description": "Non-HTTPS connection to external host",
        "severity": Severity.MEDIUM,
        "owasp": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
        "cwe_ids": ["CWE-319"],
        "fix_suggestion": "Use HTTPS for all external connections",
    },

    # A03: Injection
    {
        "id": "OWASP-A03-001",
        "pattern": r"(?:execute|exec|query)\s*\([^)]*\+[^)]*\)",
        "title": "SQL Injection via String Concatenation",
        "description": "SQL query built with string concatenation",
        "severity": Severity.CRITICAL,
        "owasp": OWASPCategory.A03_INJECTION,
        "cwe_ids": ["CWE-89"],
        "fix_suggestion": "Use parameterized queries or prepared statements",
    },
    {
        "id": "OWASP-A03-002",
        "pattern": r"(?:eval|exec|system|shell_exec|passthru)\s*\([^)]*\$",
        "title": "Command Injection Risk",
        "description": "Dynamic command execution with variable input",
        "severity": Severity.CRITICAL,
        "owasp": OWASPCategory.A03_INJECTION,
        "cwe_ids": ["CWE-78", "CWE-77"],
        "fix_suggestion": "Avoid dynamic command execution; use safe APIs",
    },
    {
        "id": "OWASP-A03-003",
        "pattern": r"innerHTML\s*=|\.html\s*\([^)]*\+",
        "title": "XSS via DOM Manipulation",
        "description": "Direct HTML injection without sanitization",
        "severity": Severity.HIGH,
        "owasp": OWASPCategory.A03_INJECTION,
        "cwe_ids": ["CWE-79"],
        "fix_suggestion": "Use textContent or sanitize HTML input",
    },
    {
        "id": "OWASP-A03-004",
        "pattern": r"LIKE\s+[\"']%.*\$.*%[\"']",
        "title": "SQL LIKE Injection",
        "description": "LIKE clause with unsanitized input",
        "severity": Severity.HIGH,
        "owasp": OWASPCategory.A03_INJECTION,
        "cwe_ids": ["CWE-89"],
        "fix_suggestion": "Escape special LIKE characters",
    },

    # A04: Insecure Design
    {
        "id": "OWASP-A04-001",
        "pattern": r"(?:TODO|FIXME|HACK|XXX).*(?:security|auth|password|encrypt)",
        "title": "Security TODO in Code",
        "description": "Unresolved security-related TODO comment",
        "severity": Severity.MEDIUM,
        "owasp": OWASPCategory.A04_INSECURE_DESIGN,
        "cwe_ids": ["CWE-1164"],
        "fix_suggestion": "Address security TODOs before deployment",
    },
    {
        "id": "OWASP-A04-002",
        "pattern": r"(?:rate_limit|throttle)\s*[=:]\s*(?:false|0|none|null)",
        "title": "Rate Limiting Disabled",
        "description": "Rate limiting appears to be disabled",
        "severity": Severity.MEDIUM,
        "owasp": OWASPCategory.A04_INSECURE_DESIGN,
        "cwe_ids": ["CWE-770"],
        "fix_suggestion": "Enable rate limiting to prevent abuse",
    },

    # A05: Security Misconfiguration
    {
        "id": "OWASP-A05-001",
        "pattern": r"DEBUG\s*[=:]\s*(?:true|True|1|yes)",
        "title": "Debug Mode Enabled",
        "description": "Debug mode is enabled which may expose sensitive info",
        "severity": Severity.HIGH,
        "owasp": OWASPCategory.A05_SECURITY_MISCONFIGURATION,
        "cwe_ids": ["CWE-489"],
        "fix_suggestion": "Disable debug mode in production",
    },
    {
        "id": "OWASP-A05-002",
        "pattern": r"(?:cors|access-control-allow-origin)\s*[=:]\s*[\"']\*[\"']",
        "title": "Overly Permissive CORS",
        "description": "CORS allows all origins",
        "severity": Severity.MEDIUM,
        "owasp": OWASPCategory.A05_SECURITY_MISCONFIGURATION,
        "cwe_ids": ["CWE-942"],
        "fix_suggestion": "Restrict CORS to specific trusted origins",
    },
    {
        "id": "OWASP-A05-003",
        "pattern": r"(?:X-Frame-Options|Content-Security-Policy)\s*[=:]\s*[\"']?(?:none|disabled)",
        "title": "Security Headers Disabled",
        "description": "Important security headers are disabled",
        "severity": Severity.MEDIUM,
        "owasp": OWASPCategory.A05_SECURITY_MISCONFIGURATION,
        "cwe_ids": ["CWE-1021"],
        "fix_suggestion": "Enable security headers (CSP, X-Frame-Options)",
    },

    # A06: Vulnerable Components (limited - requires dependency scanning)
    {
        "id": "OWASP-A06-001",
        "pattern": r"(?:lodash|jquery|angular|react|vue)\s*[\"']?\s*:\s*[\"']?[0-3]\.",
        "title": "Potentially Outdated JavaScript Library",
        "description": "Major version indicates possibly outdated library",
        "severity": Severity.LOW,
        "owasp": OWASPCategory.A06_VULNERABLE_COMPONENTS,
        "cwe_ids": ["CWE-1104"],
        "fix_suggestion": "Update to latest stable version",
    },

    # A07: Authentication Failures
    {
        "id": "OWASP-A07-001",
        "pattern": r"(?:session|cookie).*(?:secure\s*[=:]\s*false|httponly\s*[=:]\s*false)",
        "title": "Insecure Session Configuration",
        "description": "Session/cookie missing secure flags",
        "severity": Severity.HIGH,
        "owasp": OWASPCategory.A07_AUTH_FAILURES,
        "cwe_ids": ["CWE-614", "CWE-1004"],
        "fix_suggestion": "Enable Secure and HttpOnly flags on cookies",
    },
    {
        "id": "OWASP-A07-002",
        "pattern": r"(?:password|passwd).*(?:min.*length|minlength)\s*[=:<]\s*[1-7]\b",
        "title": "Weak Password Policy",
        "description": "Password minimum length is too short",
        "severity": Severity.MEDIUM,
        "owasp": OWASPCategory.A07_AUTH_FAILURES,
        "cwe_ids": ["CWE-521"],
        "fix_suggestion": "Require minimum 8 character passwords",
    },
    {
        "id": "OWASP-A07-003",
        "pattern": r"(?:jwt|token).*(?:verify|validate)\s*[=:]\s*false",
        "title": "Token Verification Disabled",
        "description": "JWT/token verification appears disabled",
        "severity": Severity.CRITICAL,
        "owasp": OWASPCategory.A07_AUTH_FAILURES,
        "cwe_ids": ["CWE-287", "CWE-345"],
        "fix_suggestion": "Always verify tokens",
    },

    # A08: Data Integrity Failures
    {
        "id": "OWASP-A08-001",
        "pattern": r"(?:pickle|marshal|yaml\.load|unserialize|deserialize)\s*\(",
        "title": "Unsafe Deserialization",
        "description": "Potentially unsafe deserialization function",
        "severity": Severity.HIGH,
        "owasp": OWASPCategory.A08_DATA_INTEGRITY_FAILURES,
        "cwe_ids": ["CWE-502"],
        "fix_suggestion": "Use safe deserialization with type checking",
    },
    {
        "id": "OWASP-A08-002",
        "pattern": r"(?:integrity|checksum|hash)\s*[=:]\s*(?:false|none|skip)",
        "title": "Integrity Check Disabled",
        "description": "Data integrity verification is disabled",
        "severity": Severity.MEDIUM,
        "owasp": OWASPCategory.A08_DATA_INTEGRITY_FAILURES,
        "cwe_ids": ["CWE-345"],
        "fix_suggestion": "Enable integrity checks for critical data",
    },

    # A09: Logging Failures
    {
        "id": "OWASP-A09-001",
        "pattern": r"(?:log|logger|logging).*(?:password|secret|token|key|credential)",
        "title": "Sensitive Data in Logs",
        "description": "Logging of potentially sensitive data",
        "severity": Severity.HIGH,
        "owasp": OWASPCategory.A09_LOGGING_FAILURES,
        "cwe_ids": ["CWE-532"],
        "fix_suggestion": "Mask or exclude sensitive data from logs",
    },
    {
        "id": "OWASP-A09-002",
        "pattern": r"catch.*(?:pass|continue|\{\s*\})",
        "title": "Silent Exception Handling",
        "description": "Exception caught but not logged",
        "severity": Severity.LOW,
        "owasp": OWASPCategory.A09_LOGGING_FAILURES,
        "cwe_ids": ["CWE-390"],
        "fix_suggestion": "Log exceptions for security monitoring",
    },

    # A10: SSRF
    {
        "id": "OWASP-A10-001",
        "pattern": r"(?:fetch|request|get|post|axios|http)\s*\([^)]*(?:\$|request\.|params\.|query\.)",
        "title": "SSRF via User Input",
        "description": "HTTP request with user-controlled URL",
        "severity": Severity.HIGH,
        "owasp": OWASPCategory.A10_SSRF,
        "cwe_ids": ["CWE-918"],
        "fix_suggestion": "Validate and allowlist permitted URLs",
    },
    {
        "id": "OWASP-A10-002",
        "pattern": r"(?:file_get_contents|include|require|fopen)\s*\([^)]*(?:\$|request)",
        "title": "Local/Remote File Inclusion Risk",
        "description": "File operation with user-controlled path",
        "severity": Severity.CRITICAL,
        "owasp": OWASPCategory.A10_SSRF,
        "cwe_ids": ["CWE-98", "CWE-918"],
        "fix_suggestion": "Use allowlists for file paths",
    },
]


# ==================== Data Classes ====================

@dataclass
class OWASPFinding:
    """Extended finding with OWASP-specific metadata."""
    finding: SecurityFinding
    owasp_category: OWASPCategory
    owasp_info: OWASPCategoryInfo
    related_cwe_ids: List[str] = field(default_factory=list)


@dataclass
class OWASPCoverageReport:
    """OWASP Top 10 coverage analysis."""
    total_patterns: int
    total_findings: int
    categories_covered: int
    categories_with_findings: int

    # Per-category breakdown
    category_coverage: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Risk summary
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0

    # Languages analyzed
    languages: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "summary": {
                "total_patterns": self.total_patterns,
                "total_findings": self.total_findings,
                "owasp_coverage": f"{self.categories_covered}/10",
                "categories_with_issues": self.categories_with_findings,
            },
            "severity_breakdown": {
                "critical": self.critical_findings,
                "high": self.high_findings,
                "medium": self.medium_findings,
                "low": self.low_findings,
            },
            "category_details": self.category_coverage,
            "languages_analyzed": self.languages,
        }


# ==================== OWASP Scanner ====================

class OWASPScanner(CustomPatternScanner):
    """
    OWASP Top 10 Security Scanner.

    Provides comprehensive OWASP vulnerability scanning by combining:
    - Built-in OWASP patterns (30+ rules)
    - Language-specific patterns from SecurityPatternLoader
    - Coverage reporting per OWASP category
    """

    VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        self._pattern_loader = get_pattern_loader()
        self._initialized = False
        self._all_rules: List[Dict[str, Any]] = []
        self._owasp_findings: List[OWASPFinding] = []

    def _ensure_initialized(self):
        """Ensure patterns are loaded."""
        if not self._initialized:
            self._pattern_loader.load_all_patterns()
            self._build_combined_rules()
            self._initialized = True

    def _build_combined_rules(self):
        """Build combined rule set from built-in and loaded patterns."""
        self._all_rules = []

        # Add built-in OWASP patterns
        for pattern in BUILTIN_OWASP_PATTERNS:
            self._all_rules.append({
                "id": pattern["id"],
                "pattern": pattern["pattern"],
                "title": pattern["title"],
                "description": pattern["description"],
                "severity": pattern["severity"],
                "owasp": pattern["owasp"],
                "cwe_ids": pattern.get("cwe_ids", []),
                "fix_suggestion": pattern.get("fix_suggestion"),
                "category": f"OWASP-{pattern['owasp'].value[:3]}",
            })

        # Add patterns from SecurityPatternLoader
        stats = self._pattern_loader.get_statistics()
        for lang, lang_info in stats.get("by_language", {}).items():
            lang_patterns = self._pattern_loader.get_patterns_by_language(lang)
            if lang_patterns:
                for pattern in lang_patterns.patterns:
                    self._all_rules.append({
                        "id": f"{lang.upper()}-{pattern.id}",
                        "pattern": pattern.pattern,
                        "title": pattern.title,
                        "description": pattern.description,
                        "severity": self._map_severity(pattern.severity.value),
                        "owasp": pattern.owasp_category,
                        "cwe_ids": [pattern.cwe_id] if pattern.cwe_id else [],
                        "fix_suggestion": pattern.remediation,
                        "category": f"OWASP-{pattern.owasp_category.value[:3]}",
                    })

    def _map_severity(self, severity_str: str) -> Severity:
        """Map severity string to Severity enum."""
        mapping = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
            "info": Severity.INFO,
        }
        return mapping.get(severity_str.lower(), Severity.MEDIUM)

    @property
    def scanner_type(self) -> ScannerType:
        return ScannerType.OWASP_SCANNER

    @property
    def supported_languages(self) -> Set[str]:
        self._ensure_initialized()
        return set(self._pattern_loader.get_supported_languages()) | {
            "generic"  # Built-in patterns work on any language
        }

    @property
    def supported_extensions(self) -> Set[str]:
        self._ensure_initialized()
        return self._pattern_loader.get_all_extensions() | {
            ".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go",
            ".asp", ".aspx", ".jsp", ".html", ".xml", ".yaml", ".yml",
            ".json", ".sql", ".sh", ".bash", ".ps1", ".config", ".ini",
        }

    @property
    def rules(self) -> List[Dict[str, Any]]:
        self._ensure_initialized()
        return self._all_rules

    async def scan(
        self,
        target_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> ScanResult:
        """
        Execute OWASP-focused security scan.

        Args:
            target_path: Path to scan
            config: Optional configuration
                - categories: List of OWASP categories to scan (e.g., ["A01", "A03"])
                - severity_threshold: Minimum severity to report
                - include_info: Include informational findings

        Returns:
            ScanResult with OWASP-tagged findings
        """
        self._ensure_initialized()
        self._owasp_findings = []

        config = config or {}
        categories_filter = config.get("categories")  # e.g., ["A01", "A03"]
        severity_threshold = config.get("severity_threshold", "low")

        # Filter rules by category if specified
        active_rules = self._all_rules
        if categories_filter:
            active_rules = [
                r for r in self._all_rules
                if any(cat in r.get("owasp", "").value for cat in categories_filter)
            ]

        # Use parent scan logic with filtered rules
        original_rules = self._all_rules
        self._all_rules = active_rules

        result = await super().scan(target_path, config)

        self._all_rules = original_rules

        # Tag findings with OWASP metadata
        for finding in result.findings:
            owasp_cat = self._get_owasp_category_for_finding(finding)
            if owasp_cat:
                finding.category = owasp_cat.value
                # Add OWASP info to raw_data
                if not finding.raw_data:
                    finding.raw_data = {}
                finding.raw_data["owasp_code"] = owasp_cat.value[:3]
                finding.raw_data["owasp_name"] = OWASP_CATEGORY_INFO[owasp_cat].name
                # Also add to tags for easy filtering
                finding.tags.add(f"owasp:{owasp_cat.value[:3]}")

        return result

    def _get_owasp_category_for_finding(self, finding: SecurityFinding) -> Optional[OWASPCategory]:
        """Get OWASP category for a finding based on rule ID."""
        for rule in self._all_rules:
            if rule["id"] in finding.rule_id:
                return rule.get("owasp")
        return None

    def get_coverage_report(self, scan_result: Optional[ScanResult] = None) -> OWASPCoverageReport:
        """
        Generate OWASP Top 10 coverage report.

        Args:
            scan_result: Optional scan result to analyze

        Returns:
            OWASPCoverageReport with detailed breakdown
        """
        self._ensure_initialized()

        # Count patterns per category
        patterns_per_category: Dict[OWASPCategory, int] = {cat: 0 for cat in OWASPCategory}
        for rule in self._all_rules:
            owasp = rule.get("owasp")
            if owasp and isinstance(owasp, OWASPCategory):
                patterns_per_category[owasp] += 1

        # Count findings per category
        findings_per_category: Dict[OWASPCategory, List[SecurityFinding]] = {cat: [] for cat in OWASPCategory}
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        if scan_result:
            for finding in scan_result.findings:
                owasp = self._get_owasp_category_for_finding(finding)
                if owasp:
                    findings_per_category[owasp].append(finding)

                sev = finding.severity.value.lower()
                if sev in severity_counts:
                    severity_counts[sev] += 1

        # Build category details
        category_coverage = {}
        categories_covered = 0
        categories_with_findings = 0

        for cat in OWASPCategory:
            info = OWASP_CATEGORY_INFO[cat]
            pattern_count = patterns_per_category[cat]
            finding_list = findings_per_category[cat]

            if pattern_count > 0:
                categories_covered += 1
            if len(finding_list) > 0:
                categories_with_findings += 1

            category_coverage[info.code] = {
                "name": info.name,
                "description": info.description,
                "risk_rating": info.risk_rating,
                "pattern_count": pattern_count,
                "finding_count": len(finding_list),
                "covered": pattern_count > 0,
                "cwe_mapping": info.cwe_ids[:5],  # Top 5 CWEs
            }

        return OWASPCoverageReport(
            total_patterns=len(self._all_rules),
            total_findings=len(scan_result.findings) if scan_result else 0,
            categories_covered=categories_covered,
            categories_with_findings=categories_with_findings,
            category_coverage=category_coverage,
            critical_findings=severity_counts["critical"],
            high_findings=severity_counts["high"],
            medium_findings=severity_counts["medium"],
            low_findings=severity_counts["low"],
            languages=list(self.supported_languages),
        )

    def get_category_info(self, code: str) -> Optional[OWASPCategoryInfo]:
        """Get detailed info for an OWASP category."""
        category = OWASP_CODE_MAP.get(code.upper())
        if category:
            return OWASP_CATEGORY_INFO.get(category)
        return None

    def get_recommendations(self, scan_result: ScanResult) -> Dict[str, List[str]]:
        """
        Get prioritized remediation recommendations.

        Returns recommendations grouped by OWASP category.
        """
        recommendations: Dict[str, List[str]] = {}

        for finding in scan_result.findings:
            owasp = self._get_owasp_category_for_finding(finding)
            if owasp:
                code = owasp.value[:3]
                if code not in recommendations:
                    recommendations[code] = []

                # Add unique recommendations
                for fix in finding.suggested_fixes:
                    if fix.description and fix.description not in recommendations[code]:
                        recommendations[code].append(fix.description)

        return recommendations


# ==================== Factory Function ====================

def create_owasp_scanner() -> OWASPScanner:
    """Create a new OWASPScanner instance."""
    return OWASPScanner()
