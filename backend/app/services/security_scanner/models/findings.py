"""
Unified Security Finding Models.

Normalizes findings from various security scanners (SARIF, custom)
into a consistent internal representation.
"""

from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from app.utils.datetime_utils import utc_now
import hashlib


class Severity(str, Enum):
    """Unified severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingStatus(str, Enum):
    """Finding status."""
    OPEN = "open"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    FIXED = "fixed"
    ACCEPTED = "accepted"  # Risk accepted


class ScannerType(str, Enum):
    """Scanner type identifier."""
    OPENGREP = "opengrep"
    BANDIT = "bandit"
    GOSEC = "gosec"
    TRIVY = "trivy"
    BRAKEMAN = "brakeman"
    PMD = "pmd"
    CUSTOM_ASP = "custom_asp"
    CUSTOM_COBOL = "custom_cobol"
    CUSTOM_SQL = "custom_sql"
    SECRET_SCANNER = "secret_scanner"  # K3: Secret Detection (Fase 24)
    OWASP_SCANNER = "owasp_scanner"  # K1: OWASP Top 10 Integration (Fase 24)
    CVE_SCANNER = "cve_scanner"  # K2: CVE Database Integration (Fase 24)
    GENERIC_SECURITY = "generic_security"  # Generic multi-language security scanner (CVD-2025-001)
    CODE_QUALITY = "code_quality"  # Code quality scanner (common programming mistakes)
    CRYPTO_ERROR = "crypto_error"  # Fase 36: Cryptographic error detector
    CONTROL_FLOW_LOGIC = "control_flow_logic"  # Fase 36: Control flow and logic error detector
    BOOLEAN_LOGIC = "boolean_logic"  # Fase 36: Boolean logic error detector
    MEMORY_SAFETY = "memory_safety"  # Fase 38: Memory safety detector (CWE-787, 416, 125, 119)
    CONCURRENCY_ERROR = "concurrency_error"  # Fase 38: Concurrency/race condition detector (CWE-362)
    WEB_SECURITY = "web_security"  # Fase 39: Web security (CWE-1321, 1236, 1284)
    PATH_SECURITY = "path_security"  # Fase 39: Path security (CWE-427, 428, 1333)
    INJECTION = "injection"  # Fase 41: Injection vulnerabilities (XSS, SQLi, CMDi, etc.)
    AUTH_LOGIC = "auth_logic"  # Fase 41: Authorization logic (CWE-862, 863, 287, etc.)
    # Fase 42: Advanced False Negative Detection
    AST_TAINT = "ast_taint"  # Cross-function taint tracking (CWE-89, 79, 78, 22, etc.)
    DYNAMIC_FEATURE = "dynamic_feature"  # Dynamic language feature detection (CWE-94, 470)
    FRAMEWORK_SECURITY = "framework_security"  # Framework-specific security patterns
    OBFUSCATION = "obfuscation"  # Obfuscation/deobfuscation detection


# CWE Top 25 (2023) mapping for quick reference
CWE_TOP_25 = {
    "CWE-787": "Out-of-bounds Write",
    "CWE-79": "Cross-site Scripting (XSS)",
    "CWE-89": "SQL Injection",
    "CWE-416": "Use After Free",
    "CWE-78": "OS Command Injection",
    "CWE-20": "Improper Input Validation",
    "CWE-125": "Out-of-bounds Read",
    "CWE-22": "Path Traversal",
    "CWE-352": "Cross-Site Request Forgery (CSRF)",
    "CWE-434": "Unrestricted Upload",
    "CWE-862": "Missing Authorization",
    "CWE-476": "NULL Pointer Dereference",
    "CWE-287": "Improper Authentication",
    "CWE-190": "Integer Overflow",
    "CWE-502": "Deserialization of Untrusted Data",
    "CWE-77": "Command Injection",
    "CWE-119": "Buffer Overflow",
    "CWE-798": "Hardcoded Credentials",
    "CWE-918": "Server-Side Request Forgery (SSRF)",
    "CWE-306": "Missing Authentication",
    "CWE-362": "Race Condition",
    "CWE-269": "Improper Privilege Management",
    "CWE-94": "Code Injection",
    "CWE-863": "Incorrect Authorization",
    "CWE-276": "Incorrect Default Permissions",
}


@dataclass
class Location:
    """Normalized location in source code."""
    file_path: str
    start_line: int
    end_line: Optional[int] = None
    start_column: Optional[int] = None
    end_column: Optional[int] = None
    snippet: Optional[str] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None


@dataclass
class SuggestedFix:
    """Suggested fix for a finding."""
    description: str
    replacement_text: Optional[str] = None
    diff: Optional[str] = None


@dataclass
class SecurityFinding:
    """Unified security finding from any scanner."""
    id: str
    rule_id: str
    title: str
    description: str
    severity: Severity
    scanner: ScannerType
    location: Location

    # CWE mapping
    cwe_ids: List[str] = field(default_factory=list)

    # Additional context
    category: Optional[str] = None  # e.g., "injection", "authentication"
    confidence: Optional[float] = None  # 0.0 to 1.0
    status: FindingStatus = FindingStatus.OPEN

    # Fix information
    suggested_fixes: List[SuggestedFix] = field(default_factory=list)

    # Metadata
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    raw_data: Optional[Dict[str, Any]] = None  # Original scanner output
    tags: Set[str] = field(default_factory=set)

    # Deduplication
    fingerprint: Optional[str] = None

    def __post_init__(self):
        """Generate fingerprint if not provided."""
        if not self.fingerprint:
            self.fingerprint = self._generate_fingerprint()

    def _generate_fingerprint(self) -> str:
        """Generate unique fingerprint for deduplication."""
        content = f"{self.rule_id}:{self.location.file_path}:{self.location.start_line}"
        if self.location.snippet:
            content += f":{self.location.snippet[:100]}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @property
    def is_cwe_top_25(self) -> bool:
        """Check if finding is in CWE Top 25."""
        for cwe in self.cwe_ids:
            normalized = cwe.upper()
            if not normalized.startswith("CWE-"):
                normalized = f"CWE-{normalized}"
            if normalized in CWE_TOP_25:
                return True
        return False

    @property
    def cwe_names(self) -> List[str]:
        """Get human-readable CWE names."""
        names = []
        for cwe in self.cwe_ids:
            normalized = cwe.upper()
            if not normalized.startswith("CWE-"):
                normalized = f"CWE-{normalized}"
            if normalized in CWE_TOP_25:
                names.append(f"{normalized}: {CWE_TOP_25[normalized]}")
            else:
                names.append(normalized)
        return names


@dataclass
class ScanResult:
    """Result of a security scan."""
    scanner: ScannerType
    scanner_version: Optional[str]
    scan_duration_ms: int
    findings: List[SecurityFinding]
    files_scanned: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=utc_now)
    completed_at: Optional[datetime] = None

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)

    def get_findings_by_severity(self, severity: Severity) -> List[SecurityFinding]:
        return [f for f in self.findings if f.severity == severity]

    def get_findings_by_cwe(self, cwe_id: str) -> List[SecurityFinding]:
        normalized = cwe_id.upper()
        if not normalized.startswith("CWE-"):
            normalized = f"CWE-{normalized}"
        return [
            f for f in self.findings
            if any(c.upper() == normalized or f"CWE-{c.upper()}" == normalized for c in f.cwe_ids)
        ]


@dataclass
class SecurityReport:
    """Aggregated security report from multiple scanners."""
    project_path: str
    scan_results: List[ScanResult]
    started_at: datetime
    completed_at: datetime
    languages_detected: Set[str] = field(default_factory=set)
    scanners_used: Set[ScannerType] = field(default_factory=set)

    @property
    def total_findings(self) -> int:
        return sum(r.finding_count for r in self.scan_results)

    @property
    def total_critical(self) -> int:
        return sum(r.critical_count for r in self.scan_results)

    @property
    def total_high(self) -> int:
        return sum(r.high_count for r in self.scan_results)

    @property
    def all_findings(self) -> List[SecurityFinding]:
        """Get all findings, deduplicated."""
        seen_fingerprints = set()
        findings = []
        for result in self.scan_results:
            for finding in result.findings:
                if finding.fingerprint not in seen_fingerprints:
                    seen_fingerprints.add(finding.fingerprint)
                    findings.append(finding)
        return findings

    @property
    def cwe_coverage(self) -> Dict[str, int]:
        """Get CWE coverage statistics."""
        coverage = {}
        for finding in self.all_findings:
            for cwe in finding.cwe_ids:
                normalized = cwe.upper()
                if not normalized.startswith("CWE-"):
                    normalized = f"CWE-{normalized}"
                coverage[normalized] = coverage.get(normalized, 0) + 1
        return coverage

    @property
    def cwe_top_25_coverage(self) -> Dict[str, int]:
        """Get coverage for CWE Top 25 specifically."""
        all_coverage = self.cwe_coverage
        return {
            cwe: all_coverage.get(cwe, 0)
            for cwe in CWE_TOP_25.keys()
        }

    def get_severity_summary(self) -> Dict[str, int]:
        """Get finding count by severity."""
        summary = {s.value: 0 for s in Severity}
        for finding in self.all_findings:
            summary[finding.severity.value] += 1
        return summary

    def get_scanner_summary(self) -> Dict[str, int]:
        """Get finding count by scanner."""
        return {
            result.scanner.value: result.finding_count
            for result in self.scan_results
        }
