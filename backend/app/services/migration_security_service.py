"""
Migration Security Service - Quinn Integration for Legacy OWASP Patterns

Week 68 Day 1-2: Integration of Quinn (Quality Inspector) with MigrationAnalyzer
for comprehensive security assessment of legacy codebases.

Provides:
- OWASP Top 10 legacy patterns for ASP, VB.NET, PHP, Java
- Security risk scoring for migration planning
- Quinn context generation for detailed review
- Remediation recommendations aligned with target stack
"""

import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Set, Tuple
from enum import Enum
from datetime import datetime
from collections import defaultdict


class OWASPCategory(Enum):
    """OWASP Top 10 2021 Categories"""
    A01_BROKEN_ACCESS_CONTROL = "A01:2021 - Broken Access Control"
    A02_CRYPTOGRAPHIC_FAILURES = "A02:2021 - Cryptographic Failures"
    A03_INJECTION = "A03:2021 - Injection"
    A04_INSECURE_DESIGN = "A04:2021 - Insecure Design"
    A05_SECURITY_MISCONFIGURATION = "A05:2021 - Security Misconfiguration"
    A06_VULNERABLE_COMPONENTS = "A06:2021 - Vulnerable and Outdated Components"
    A07_AUTH_FAILURES = "A07:2021 - Identification and Authentication Failures"
    A08_DATA_INTEGRITY = "A08:2021 - Software and Data Integrity Failures"
    A09_LOGGING_FAILURES = "A09:2021 - Security Logging and Monitoring Failures"
    A10_SSRF = "A10:2021 - Server-Side Request Forgery"


class LegacyStack(Enum):
    """Legacy technology stacks"""
    CLASSIC_ASP = "classic_asp"
    VB_NET_WEBFORMS = "vb_net_webforms"
    CSHARP_WEBFORMS = "csharp_webforms"
    PHP_LEGACY = "php_legacy"  # PHP 4.x - 5.x patterns
    JAVA_LEGACY = "java_legacy"  # Java 1.4 - 6 patterns
    COLDFUSION = "coldfusion"
    PERL_CGI = "perl_cgi"


class SecuritySeverity(Enum):
    """Security finding severity"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RemediationEffort(Enum):
    """Effort required to remediate"""
    TRIVIAL = "trivial"      # < 1 hour
    EASY = "easy"            # 1-4 hours
    MODERATE = "moderate"    # 4-16 hours
    COMPLEX = "complex"      # 16-40 hours
    MAJOR = "major"          # > 40 hours


@dataclass
class LegacySecurityPattern:
    """Definition of a legacy security pattern"""
    id: str
    name: str
    owasp_category: OWASPCategory
    severity: SecuritySeverity
    stacks: List[LegacyStack]
    pattern: str  # Regex pattern
    description: str
    legacy_example: str
    modern_remediation: str
    remediation_effort: RemediationEffort
    cwe_id: Optional[int] = None
    references: List[str] = field(default_factory=list)


@dataclass
class SecurityFinding:
    """Single security finding in code"""
    pattern_id: str
    pattern_name: str
    owasp_category: OWASPCategory
    severity: SecuritySeverity
    file_path: str
    line_number: int
    code_snippet: str
    description: str
    remediation: str
    remediation_effort: RemediationEffort
    cwe_id: Optional[int] = None
    confidence: float = 0.9  # 0.0 - 1.0


@dataclass
class SecurityRiskScore:
    """Overall security risk scoring"""
    total_score: float  # 0-100, higher = more risk
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    owasp_coverage: Dict[str, int]  # Category -> count
    top_risks: List[str]
    migration_blockers: List[str]
    estimated_remediation_hours: float


@dataclass
class QuinnContext:
    """Context prepared for Quinn agent review"""
    summary: str
    focus_areas: List[str]
    priority_files: List[str]
    owasp_checklist: Dict[str, bool]
    questions_for_review: List[str]
    recommended_tools: List[str]


@dataclass
class MigrationSecurityResult:
    """Complete security analysis result for migration"""
    analysis_id: str
    project_path: str
    stacks_detected: List[LegacyStack]
    findings: List[SecurityFinding]
    risk_score: SecurityRiskScore
    quinn_context: QuinnContext
    recommendations: List[str]
    files_scanned: int = 0
    analysis_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "project_path": self.project_path,
            "stacks_detected": [s.value for s in self.stacks_detected],
            "findings_count": len(self.findings),
            "findings": [
                {
                    "pattern_id": f.pattern_id,
                    "pattern_name": f.pattern_name,
                    "owasp_category": f.owasp_category.value,
                    "severity": f.severity.value,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "code_snippet": f.code_snippet[:200],
                    "description": f.description,
                    "remediation": f.remediation,
                    "remediation_effort": f.remediation_effort.value,
                    "cwe_id": f.cwe_id,
                    "confidence": f.confidence
                }
                for f in self.findings
            ],
            "risk_score": {
                "total_score": round(self.risk_score.total_score, 1),
                "critical_count": self.risk_score.critical_count,
                "high_count": self.risk_score.high_count,
                "medium_count": self.risk_score.medium_count,
                "low_count": self.risk_score.low_count,
                "owasp_coverage": self.risk_score.owasp_coverage,
                "top_risks": self.risk_score.top_risks,
                "migration_blockers": self.risk_score.migration_blockers,
                "estimated_remediation_hours": round(self.risk_score.estimated_remediation_hours, 1)
            },
            "quinn_context": {
                "summary": self.quinn_context.summary,
                "focus_areas": self.quinn_context.focus_areas,
                "priority_files": self.quinn_context.priority_files[:10],
                "owasp_checklist": self.quinn_context.owasp_checklist,
                "questions_for_review": self.quinn_context.questions_for_review,
                "recommended_tools": self.quinn_context.recommended_tools
            },
            "recommendations": self.recommendations,
            "analysis_timestamp": self.analysis_timestamp
        }


# Legacy Security Patterns Database
LEGACY_SECURITY_PATTERNS: List[LegacySecurityPattern] = [
    # ==================== A01: Broken Access Control ====================
    LegacySecurityPattern(
        id="A01-ASP-001",
        name="Classic ASP Session Without Validation",
        owasp_category=OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
        severity=SecuritySeverity.HIGH,
        stacks=[LegacyStack.CLASSIC_ASP],
        pattern=r"Session\s*\(\s*[\"'](?:user|admin|role|auth)[\"']\s*\)",
        description="Session variable access without proper validation, common in Classic ASP",
        legacy_example='If Session("IsAdmin") = True Then',
        modern_remediation="Implement proper authentication middleware with claims-based authorization",
        remediation_effort=RemediationEffort.MODERATE,
        cwe_id=284,
        references=["https://cwe.mitre.org/data/definitions/284.html"]
    ),
    LegacySecurityPattern(
        id="A01-PHP-001",
        name="PHP Direct File Access Without Auth",
        owasp_category=OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
        severity=SecuritySeverity.HIGH,
        stacks=[LegacyStack.PHP_LEGACY],
        pattern=r"\$_GET\s*\[\s*[\"'](?:file|path|doc|download)[\"']\s*\]",
        description="Direct file path from user input, enabling path traversal",
        legacy_example="$file = $_GET['file']; include($file);",
        modern_remediation="Use whitelist validation, secure file routing, and proper access controls",
        remediation_effort=RemediationEffort.MODERATE,
        cwe_id=22,
        references=["https://cwe.mitre.org/data/definitions/22.html"]
    ),
    LegacySecurityPattern(
        id="A01-VB-001",
        name="VB.NET ViewState Without MAC",
        owasp_category=OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
        severity=SecuritySeverity.MEDIUM,
        stacks=[LegacyStack.VB_NET_WEBFORMS, LegacyStack.CSHARP_WEBFORMS],
        pattern=r"EnableViewStateMac\s*=\s*[\"']?false[\"']?",
        description="ViewState MAC disabled, allowing tampering",
        legacy_example='<%@ Page EnableViewStateMac="false" %>',
        modern_remediation="Enable ViewStateMac or migrate to modern state management (JWT, server-side sessions)",
        remediation_effort=RemediationEffort.EASY,
        cwe_id=352
    ),

    # ==================== A02: Cryptographic Failures ====================
    LegacySecurityPattern(
        id="A02-ASP-001",
        name="MD5 Password Hashing",
        owasp_category=OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
        severity=SecuritySeverity.CRITICAL,
        stacks=[LegacyStack.CLASSIC_ASP, LegacyStack.PHP_LEGACY, LegacyStack.VB_NET_WEBFORMS],
        pattern=r"(?:md5|MD5)\s*\(",
        description="MD5 is cryptographically broken for password hashing",
        legacy_example="password = md5(Request.Form('password'))",
        modern_remediation="Use bcrypt, Argon2, or PBKDF2 with salt",
        remediation_effort=RemediationEffort.MODERATE,
        cwe_id=328,
        references=["https://cwe.mitre.org/data/definitions/328.html"]
    ),
    LegacySecurityPattern(
        id="A02-PHP-002",
        name="SHA1 Without Salt",
        owasp_category=OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
        severity=SecuritySeverity.HIGH,
        stacks=[LegacyStack.PHP_LEGACY],
        pattern=r"sha1\s*\(\s*\$",
        description="SHA1 without salt is vulnerable to rainbow table attacks",
        legacy_example="$hash = sha1($password);",
        modern_remediation="Use password_hash() with PASSWORD_BCRYPT or PASSWORD_ARGON2ID",
        remediation_effort=RemediationEffort.EASY,
        cwe_id=916
    ),
    LegacySecurityPattern(
        id="A02-VB-002",
        name="DES Encryption",
        owasp_category=OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
        severity=SecuritySeverity.CRITICAL,
        stacks=[LegacyStack.VB_NET_WEBFORMS, LegacyStack.CSHARP_WEBFORMS, LegacyStack.JAVA_LEGACY],
        pattern=r"(?:DES|TripleDES|DESCryptoServiceProvider)",
        description="DES/3DES is deprecated due to small key size",
        legacy_example="Dim des As New DESCryptoServiceProvider()",
        modern_remediation="Use AES-256-GCM or AES-256-CBC with HMAC",
        remediation_effort=RemediationEffort.MODERATE,
        cwe_id=327
    ),
    LegacySecurityPattern(
        id="A02-JAVA-001",
        name="ECB Mode Encryption",
        owasp_category=OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
        severity=SecuritySeverity.HIGH,
        stacks=[LegacyStack.JAVA_LEGACY],
        pattern=r"Cipher\.getInstance\s*\(\s*[\"'](?:AES|DES)[\"']\s*\)",
        description="ECB mode (default when not specified) doesn't hide data patterns",
        legacy_example='Cipher cipher = Cipher.getInstance("AES");',
        modern_remediation='Use Cipher.getInstance("AES/GCM/NoPadding") with random IV',
        remediation_effort=RemediationEffort.MODERATE,
        cwe_id=327
    ),

    # ==================== A03: Injection ====================
    LegacySecurityPattern(
        id="A03-ASP-001",
        name="Classic ASP SQL Injection",
        owasp_category=OWASPCategory.A03_INJECTION,
        severity=SecuritySeverity.CRITICAL,
        stacks=[LegacyStack.CLASSIC_ASP],
        pattern=r"(?:Execute|Open)\s*\(?.*Request\.",
        description="Direct concatenation of user input in SQL queries",
        legacy_example='rs.Open "SELECT * FROM users WHERE id=" & Request("id")',
        modern_remediation="Use parameterized queries with ADO.NET or ORM",
        remediation_effort=RemediationEffort.MODERATE,
        cwe_id=89,
        references=["https://cwe.mitre.org/data/definitions/89.html"]
    ),
    LegacySecurityPattern(
        id="A03-ASP-002",
        name="Classic ASP String Concatenation SQL",
        owasp_category=OWASPCategory.A03_INJECTION,
        severity=SecuritySeverity.CRITICAL,
        stacks=[LegacyStack.CLASSIC_ASP],
        pattern=r"[\"']SELECT\s+.*[\"']\s*&\s*(?:Request|Session)",
        description="SQL query built with string concatenation",
        legacy_example="sql = \"SELECT * FROM users WHERE name='\" & Request(\"name\") & \"'\"",
        modern_remediation="Use parameterized queries or stored procedures",
        remediation_effort=RemediationEffort.MODERATE,
        cwe_id=89
    ),
    LegacySecurityPattern(
        id="A03-PHP-001",
        name="PHP mysql_* Functions",
        owasp_category=OWASPCategory.A03_INJECTION,
        severity=SecuritySeverity.CRITICAL,
        stacks=[LegacyStack.PHP_LEGACY],
        pattern=r"mysql_(?:query|real_escape_string|connect)",
        description="Deprecated mysql_* functions are vulnerable and removed in PHP 7+",
        legacy_example='mysql_query("SELECT * FROM users WHERE id=" . $_GET["id"]);',
        modern_remediation="Use PDO with prepared statements",
        remediation_effort=RemediationEffort.MODERATE,
        cwe_id=89
    ),
    LegacySecurityPattern(
        id="A03-PHP-002",
        name="PHP eval() with User Input",
        owasp_category=OWASPCategory.A03_INJECTION,
        severity=SecuritySeverity.CRITICAL,
        stacks=[LegacyStack.PHP_LEGACY],
        pattern=r"eval\s*\(\s*\$_(?:GET|POST|REQUEST|COOKIE)",
        description="Code injection via eval() with user-controlled input",
        legacy_example="eval($_GET['code']);",
        modern_remediation="Remove eval() entirely; use proper design patterns",
        remediation_effort=RemediationEffort.COMPLEX,
        cwe_id=94
    ),
    LegacySecurityPattern(
        id="A03-VB-001",
        name="VB.NET SqlCommand Concatenation",
        owasp_category=OWASPCategory.A03_INJECTION,
        severity=SecuritySeverity.CRITICAL,
        stacks=[LegacyStack.VB_NET_WEBFORMS, LegacyStack.CSHARP_WEBFORMS],
        pattern=r"SqlCommand\s*\([^)]*\+\s*(?:Request|TextBox|DropDownList)",
        description="SQL command with string concatenation from user input",
        legacy_example='cmd = New SqlCommand("SELECT * FROM users WHERE id=" + txtId.Text)',
        modern_remediation="Use SqlParameter for all user inputs",
        remediation_effort=RemediationEffort.EASY,
        cwe_id=89
    ),
    LegacySecurityPattern(
        id="A03-JAVA-001",
        name="Java Statement Concatenation",
        owasp_category=OWASPCategory.A03_INJECTION,
        severity=SecuritySeverity.CRITICAL,
        stacks=[LegacyStack.JAVA_LEGACY],
        pattern=r"(?:Statement|createStatement).*execute(?:Query|Update)\s*\([^)]*\+",
        description="JDBC Statement with string concatenation",
        legacy_example='stmt.executeQuery("SELECT * FROM users WHERE id=" + userId);',
        modern_remediation="Use PreparedStatement with parameter binding",
        remediation_effort=RemediationEffort.EASY,
        cwe_id=89
    ),
    LegacySecurityPattern(
        id="A03-ASP-003",
        name="Command Injection via Shell",
        owasp_category=OWASPCategory.A03_INJECTION,
        severity=SecuritySeverity.CRITICAL,
        stacks=[LegacyStack.CLASSIC_ASP, LegacyStack.PHP_LEGACY],
        pattern=r"(?:Shell|WScript\.Shell|system|exec|passthru|shell_exec)\s*\([^)]*(?:Request|\$_)",
        description="OS command execution with user input",
        legacy_example='Set shell = Server.CreateObject("WScript.Shell")\nshell.Run Request("cmd")',
        modern_remediation="Avoid shell commands; use APIs. If needed, use strict whitelist validation",
        remediation_effort=RemediationEffort.COMPLEX,
        cwe_id=78
    ),

    # ==================== A04: Insecure Design ====================
    LegacySecurityPattern(
        id="A04-ASP-001",
        name="Client-Side Validation Only",
        owasp_category=OWASPCategory.A04_INSECURE_DESIGN,
        severity=SecuritySeverity.MEDIUM,
        stacks=[LegacyStack.CLASSIC_ASP, LegacyStack.VB_NET_WEBFORMS],
        pattern=r"(?:ClientTarget|EnableClientScript)\s*=\s*[\"']?true[\"']?",
        description="Relying on client-side validation without server-side checks",
        legacy_example='<asp:RequiredFieldValidator EnableClientScript="true">',
        modern_remediation="Always implement server-side validation alongside client-side",
        remediation_effort=RemediationEffort.MODERATE,
        cwe_id=602
    ),
    LegacySecurityPattern(
        id="A04-PHP-001",
        name="register_globals Pattern",
        owasp_category=OWASPCategory.A04_INSECURE_DESIGN,
        severity=SecuritySeverity.HIGH,
        stacks=[LegacyStack.PHP_LEGACY],
        pattern=r"(?:extract\s*\(\s*\$_(?:GET|POST|REQUEST)|import_request_variables)",
        description="Pattern mimicking register_globals behavior",
        legacy_example="extract($_POST);",
        modern_remediation="Explicitly access superglobals; never auto-import",
        remediation_effort=RemediationEffort.MODERATE,
        cwe_id=621
    ),

    # ==================== A05: Security Misconfiguration ====================
    LegacySecurityPattern(
        id="A05-ASP-001",
        name="Debug Mode Enabled",
        owasp_category=OWASPCategory.A05_SECURITY_MISCONFIGURATION,
        severity=SecuritySeverity.MEDIUM,
        stacks=[LegacyStack.VB_NET_WEBFORMS, LegacyStack.CSHARP_WEBFORMS],
        pattern=r"<compilation\s+debug\s*=\s*[\"']true[\"']",
        description="Debug mode enabled in production",
        legacy_example='<compilation debug="true">',
        modern_remediation="Disable debug in production; use transform for environment-specific config",
        remediation_effort=RemediationEffort.TRIVIAL,
        cwe_id=489
    ),
    LegacySecurityPattern(
        id="A05-ASP-002",
        name="Custom Errors Disabled",
        owasp_category=OWASPCategory.A05_SECURITY_MISCONFIGURATION,
        severity=SecuritySeverity.MEDIUM,
        stacks=[LegacyStack.VB_NET_WEBFORMS, LegacyStack.CSHARP_WEBFORMS, LegacyStack.CLASSIC_ASP],
        pattern=r"<customErrors\s+mode\s*=\s*[\"']Off[\"']",
        description="Detailed error messages exposed to users",
        legacy_example='<customErrors mode="Off">',
        modern_remediation='Set mode="RemoteOnly" or "On" with custom error pages',
        remediation_effort=RemediationEffort.TRIVIAL,
        cwe_id=209
    ),
    LegacySecurityPattern(
        id="A05-PHP-001",
        name="display_errors Enabled",
        owasp_category=OWASPCategory.A05_SECURITY_MISCONFIGURATION,
        severity=SecuritySeverity.MEDIUM,
        stacks=[LegacyStack.PHP_LEGACY],
        pattern=r"(?:ini_set\s*\(\s*[\"']display_errors[\"']\s*,\s*[\"']?(?:1|on|true)|error_reporting\s*\(\s*E_ALL\s*\))",
        description="Error display enabled showing sensitive information",
        legacy_example="ini_set('display_errors', 1);",
        modern_remediation="Log errors to file; never display in production",
        remediation_effort=RemediationEffort.TRIVIAL,
        cwe_id=209
    ),

    # ==================== A06: Vulnerable Components ====================
    LegacySecurityPattern(
        id="A06-PHP-001",
        name="Outdated PHP Version Indicators",
        owasp_category=OWASPCategory.A06_VULNERABLE_COMPONENTS,
        severity=SecuritySeverity.HIGH,
        stacks=[LegacyStack.PHP_LEGACY],
        pattern=r"(?:mysql_|ereg\(|eregi\(|split\(|spliti\()",
        description="Functions removed in PHP 7+, indicating outdated codebase",
        legacy_example="if (ereg('^[a-z]+$', $input))",
        modern_remediation="Update to PHP 8.x; replace deprecated functions",
        remediation_effort=RemediationEffort.COMPLEX,
        cwe_id=1104
    ),
    LegacySecurityPattern(
        id="A06-JAVA-001",
        name="Legacy Servlet Pattern",
        owasp_category=OWASPCategory.A06_VULNERABLE_COMPONENTS,
        severity=SecuritySeverity.MEDIUM,
        stacks=[LegacyStack.JAVA_LEGACY],
        pattern=r"extends\s+HttpServlet.*doGet|doPost.*getParameter\s*\(",
        description="Old servlet pattern without framework protections",
        legacy_example="public void doGet(HttpServletRequest req, HttpServletResponse res)",
        modern_remediation="Migrate to Spring Boot with built-in security",
        remediation_effort=RemediationEffort.MAJOR,
        cwe_id=1104
    ),

    # ==================== A07: Authentication Failures ====================
    LegacySecurityPattern(
        id="A07-ASP-001",
        name="Hardcoded Credentials",
        owasp_category=OWASPCategory.A07_AUTH_FAILURES,
        severity=SecuritySeverity.CRITICAL,
        stacks=[LegacyStack.CLASSIC_ASP, LegacyStack.VB_NET_WEBFORMS, LegacyStack.PHP_LEGACY],
        pattern=r"(?:password|pwd|passwd|secret|apikey|api_key)\s*=\s*[\"'][^\"']+[\"']",
        description="Hardcoded credentials in source code",
        legacy_example='Const PASSWORD = "admin123"',
        modern_remediation="Use environment variables or secure vault (HashiCorp, Azure Key Vault)",
        remediation_effort=RemediationEffort.MODERATE,
        cwe_id=798
    ),
    LegacySecurityPattern(
        id="A07-ASP-002",
        name="Forms Authentication Timeout",
        owasp_category=OWASPCategory.A07_AUTH_FAILURES,
        severity=SecuritySeverity.MEDIUM,
        stacks=[LegacyStack.VB_NET_WEBFORMS, LegacyStack.CSHARP_WEBFORMS],
        pattern=r"<forms\s+.*timeout\s*=\s*[\"'](?:[0-9]{4,}|0)[\"']",
        description="Extremely long or disabled session timeout",
        legacy_example='<forms timeout="525600">',
        modern_remediation="Set reasonable timeout (20-60 min); implement sliding expiration",
        remediation_effort=RemediationEffort.TRIVIAL,
        cwe_id=613
    ),
    LegacySecurityPattern(
        id="A07-PHP-001",
        name="Session Fixation Vulnerable",
        owasp_category=OWASPCategory.A07_AUTH_FAILURES,
        severity=SecuritySeverity.HIGH,
        stacks=[LegacyStack.PHP_LEGACY],
        pattern=r"session_start\s*\(\s*\)(?:(?!session_regenerate_id).)*\$_SESSION\s*\[\s*[\"'](?:user|logged|auth)",
        description="Session start without regeneration after login",
        legacy_example="session_start(); $_SESSION['logged_in'] = true;",
        modern_remediation="Call session_regenerate_id(true) after successful login",
        remediation_effort=RemediationEffort.EASY,
        cwe_id=384
    ),

    # ==================== A08: Data Integrity Failures ====================
    LegacySecurityPattern(
        id="A08-PHP-001",
        name="Unserialize with User Data",
        owasp_category=OWASPCategory.A08_DATA_INTEGRITY,
        severity=SecuritySeverity.CRITICAL,
        stacks=[LegacyStack.PHP_LEGACY],
        pattern=r"unserialize\s*\(\s*\$_(?:GET|POST|REQUEST|COOKIE)",
        description="Unsafe deserialization of user-controlled data",
        legacy_example="$data = unserialize($_COOKIE['data']);",
        modern_remediation="Use JSON for data exchange; avoid unserialize with user data",
        remediation_effort=RemediationEffort.MODERATE,
        cwe_id=502
    ),
    LegacySecurityPattern(
        id="A08-JAVA-001",
        name="Java Object Deserialization",
        owasp_category=OWASPCategory.A08_DATA_INTEGRITY,
        severity=SecuritySeverity.CRITICAL,
        stacks=[LegacyStack.JAVA_LEGACY],
        pattern=r"ObjectInputStream.*readObject\s*\(",
        description="Java deserialization vulnerability",
        legacy_example="Object obj = new ObjectInputStream(inputStream).readObject();",
        modern_remediation="Use JSON/XML serialization; implement whitelist filter for ObjectInputStream",
        remediation_effort=RemediationEffort.COMPLEX,
        cwe_id=502
    ),

    # ==================== A09: Logging Failures ====================
    LegacySecurityPattern(
        id="A09-ASP-001",
        name="Password in Error Message",
        owasp_category=OWASPCategory.A09_LOGGING_FAILURES,
        severity=SecuritySeverity.HIGH,
        stacks=[LegacyStack.CLASSIC_ASP, LegacyStack.VB_NET_WEBFORMS, LegacyStack.PHP_LEGACY],
        pattern=r"(?:Response\.Write|echo|print|Console\.Write|log).*(?:password|pwd|secret)",
        description="Sensitive data potentially logged or displayed",
        legacy_example='Response.Write "Login failed for " & username & " with password " & password',
        modern_remediation="Never log sensitive data; use structured logging with data masking",
        remediation_effort=RemediationEffort.EASY,
        cwe_id=532
    ),

    # ==================== A10: SSRF ====================
    LegacySecurityPattern(
        id="A10-PHP-001",
        name="PHP file_get_contents with User URL",
        owasp_category=OWASPCategory.A10_SSRF,
        severity=SecuritySeverity.HIGH,
        stacks=[LegacyStack.PHP_LEGACY],
        pattern=r"file_get_contents\s*\(\s*\$_(?:GET|POST|REQUEST)",
        description="Server-Side Request Forgery via file_get_contents",
        legacy_example="$content = file_get_contents($_GET['url']);",
        modern_remediation="Validate URLs against whitelist; use cURL with restrictions",
        remediation_effort=RemediationEffort.MODERATE,
        cwe_id=918
    ),
    LegacySecurityPattern(
        id="A10-JAVA-001",
        name="Java URL Connection SSRF",
        owasp_category=OWASPCategory.A10_SSRF,
        severity=SecuritySeverity.HIGH,
        stacks=[LegacyStack.JAVA_LEGACY],
        pattern=r"new\s+URL\s*\([^)]*(?:getParameter|request\.get)",
        description="URL created from user input enabling SSRF",
        legacy_example='URL url = new URL(request.getParameter("url"));',
        modern_remediation="Validate against URL whitelist; block internal IPs",
        remediation_effort=RemediationEffort.MODERATE,
        cwe_id=918
    ),

    # ==================== XSS Patterns ====================
    LegacySecurityPattern(
        id="XSS-ASP-001",
        name="Classic ASP Response.Write XSS",
        owasp_category=OWASPCategory.A03_INJECTION,
        severity=SecuritySeverity.HIGH,
        stacks=[LegacyStack.CLASSIC_ASP],
        pattern=r"Response\.Write\s*(?:\(?\s*Request|.*&\s*Request)",
        description="Direct output of user input without encoding",
        legacy_example='Response.Write "Hello, " & Request("name")',
        modern_remediation="Use Server.HTMLEncode() or migrate to MVC with automatic encoding",
        remediation_effort=RemediationEffort.MODERATE,
        cwe_id=79
    ),
    LegacySecurityPattern(
        id="XSS-PHP-001",
        name="PHP Echo Without Encoding",
        owasp_category=OWASPCategory.A03_INJECTION,
        severity=SecuritySeverity.HIGH,
        stacks=[LegacyStack.PHP_LEGACY],
        pattern=r"(?:echo|print)\s+\$_(?:GET|POST|REQUEST|COOKIE)\s*\[",
        description="Direct echo of user input without htmlspecialchars",
        legacy_example='echo $_GET["search"];',
        modern_remediation="Use htmlspecialchars($var, ENT_QUOTES, 'UTF-8')",
        remediation_effort=RemediationEffort.EASY,
        cwe_id=79
    ),
    LegacySecurityPattern(
        id="XSS-VB-001",
        name="VB.NET Literal Without Encoding",
        owasp_category=OWASPCategory.A03_INJECTION,
        severity=SecuritySeverity.HIGH,
        stacks=[LegacyStack.VB_NET_WEBFORMS, LegacyStack.CSHARP_WEBFORMS],
        pattern=r"\.Text\s*=\s*Request(?:\.QueryString|\.Form|\[)",
        description="Setting control text directly from request",
        legacy_example='lblMessage.Text = Request.QueryString("msg")',
        modern_remediation="Use Server.HtmlEncode() or migrate to Razor with auto-encoding",
        remediation_effort=RemediationEffort.EASY,
        cwe_id=79
    ),
]

# Remediation effort hours mapping
EFFORT_HOURS: Dict[RemediationEffort, float] = {
    RemediationEffort.TRIVIAL: 0.5,
    RemediationEffort.EASY: 2.0,
    RemediationEffort.MODERATE: 8.0,
    RemediationEffort.COMPLEX: 24.0,
    RemediationEffort.MAJOR: 60.0,
}

# Severity score weights
SEVERITY_SCORES: Dict[SecuritySeverity, float] = {
    SecuritySeverity.CRITICAL: 10.0,
    SecuritySeverity.HIGH: 7.0,
    SecuritySeverity.MEDIUM: 4.0,
    SecuritySeverity.LOW: 1.0,
    SecuritySeverity.INFO: 0.5,
}

# File extensions by stack
STACK_EXTENSIONS: Dict[LegacyStack, List[str]] = {
    LegacyStack.CLASSIC_ASP: [".asp", ".asa", ".inc"],
    LegacyStack.VB_NET_WEBFORMS: [".aspx", ".aspx.vb", ".ascx", ".ascx.vb", ".vb"],
    LegacyStack.CSHARP_WEBFORMS: [".aspx", ".aspx.cs", ".ascx", ".ascx.cs", ".cs"],
    LegacyStack.PHP_LEGACY: [".php", ".php3", ".php4", ".php5", ".phtml", ".inc"],
    LegacyStack.JAVA_LEGACY: [".java", ".jsp", ".jspx"],
    LegacyStack.COLDFUSION: [".cfm", ".cfc"],
    LegacyStack.PERL_CGI: [".pl", ".cgi", ".pm"],
}


class MigrationSecurityService:
    """Service for security analysis of legacy codebases during migration"""

    def __init__(self):
        self.patterns = LEGACY_SECURITY_PATTERNS

    def analyze_directory(
        self,
        directory: str,
        stacks: Optional[List[LegacyStack]] = None,
        severity_threshold: SecuritySeverity = SecuritySeverity.LOW
    ) -> MigrationSecurityResult:
        """
        Analyze directory for legacy security patterns

        Args:
            directory: Path to source code directory
            stacks: Specific stacks to check (auto-detect if None)
            severity_threshold: Minimum severity to report

        Returns:
            MigrationSecurityResult with findings and recommendations
        """
        import uuid
        analysis_id = str(uuid.uuid4())[:8]

        path = Path(directory)
        if not path.exists():
            return self._empty_result(analysis_id, directory, "Directory does not exist")

        # Auto-detect stacks if not specified
        if stacks is None:
            stacks = self._detect_stacks(path)

        if not stacks:
            return self._empty_result(analysis_id, directory, "No legacy stacks detected")

        # Collect relevant files
        files = self._collect_files(path, stacks)

        if not files:
            return self._empty_result(analysis_id, directory, "No source files found")

        # Run pattern analysis
        findings = self._analyze_files(files, stacks, severity_threshold)

        # Calculate risk score
        risk_score = self._calculate_risk_score(findings)

        # Generate Quinn context
        quinn_context = self._generate_quinn_context(findings, stacks)

        # Generate recommendations
        recommendations = self._generate_recommendations(findings, stacks, risk_score)

        return MigrationSecurityResult(
            analysis_id=analysis_id,
            project_path=str(directory),
            stacks_detected=stacks,
            findings=findings,
            risk_score=risk_score,
            quinn_context=quinn_context,
            recommendations=recommendations
        )

    def _detect_stacks(self, path: Path) -> List[LegacyStack]:
        """Auto-detect legacy stacks from file extensions"""
        detected = set()

        for stack, extensions in STACK_EXTENSIONS.items():
            for ext in extensions:
                if list(path.rglob(f"*{ext}")):
                    detected.add(stack)
                    break

        return list(detected)

    def _collect_files(
        self,
        path: Path,
        stacks: List[LegacyStack]
    ) -> Dict[str, str]:
        """Collect relevant source files"""
        files = {}
        extensions = set()

        for stack in stacks:
            extensions.update(STACK_EXTENSIONS.get(stack, []))

        for ext in extensions:
            for file_path in path.rglob(f"*{ext}"):
                # Skip common non-source directories
                if any(skip in str(file_path) for skip in [
                    "node_modules", ".git", "vendor", "packages", "bin", "obj"
                ]):
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    files[str(file_path.relative_to(path))] = content
                except Exception:
                    continue

        return files

    def _analyze_files(
        self,
        files: Dict[str, str],
        stacks: List[LegacyStack],
        severity_threshold: SecuritySeverity
    ) -> List[SecurityFinding]:
        """Analyze files for security patterns"""
        findings = []
        severity_order = [
            SecuritySeverity.CRITICAL,
            SecuritySeverity.HIGH,
            SecuritySeverity.MEDIUM,
            SecuritySeverity.LOW,
            SecuritySeverity.INFO
        ]
        threshold_idx = severity_order.index(severity_threshold)

        for file_path, content in files.items():
            lines = content.splitlines()

            for pattern_def in self.patterns:
                # Check if pattern applies to detected stacks
                if not any(s in stacks for s in pattern_def.stacks):
                    continue

                # Check severity threshold
                if severity_order.index(pattern_def.severity) > threshold_idx:
                    continue

                try:
                    regex = re.compile(pattern_def.pattern, re.IGNORECASE | re.MULTILINE)

                    for i, line in enumerate(lines, 1):
                        if regex.search(line):
                            findings.append(SecurityFinding(
                                pattern_id=pattern_def.id,
                                pattern_name=pattern_def.name,
                                owasp_category=pattern_def.owasp_category,
                                severity=pattern_def.severity,
                                file_path=file_path,
                                line_number=i,
                                code_snippet=line.strip(),
                                description=pattern_def.description,
                                remediation=pattern_def.modern_remediation,
                                remediation_effort=pattern_def.remediation_effort,
                                cwe_id=pattern_def.cwe_id
                            ))
                except re.error:
                    continue

        return findings

    def _calculate_risk_score(self, findings: List[SecurityFinding]) -> SecurityRiskScore:
        """Calculate overall security risk score"""
        critical_count = sum(1 for f in findings if f.severity == SecuritySeverity.CRITICAL)
        high_count = sum(1 for f in findings if f.severity == SecuritySeverity.HIGH)
        medium_count = sum(1 for f in findings if f.severity == SecuritySeverity.MEDIUM)
        low_count = sum(1 for f in findings if f.severity == SecuritySeverity.LOW)

        # OWASP coverage
        owasp_coverage: Dict[str, int] = defaultdict(int)
        for f in findings:
            owasp_coverage[f.owasp_category.value] += 1

        # Calculate total score (0-100)
        total_weighted = sum(
            SEVERITY_SCORES[f.severity] for f in findings
        )
        max_score = 100.0
        total_score = min(total_weighted, max_score)

        # Top risks
        pattern_counts: Dict[str, int] = defaultdict(int)
        for f in findings:
            pattern_counts[f.pattern_name] += 1

        top_risks = sorted(
            pattern_counts.keys(),
            key=lambda x: pattern_counts[x],
            reverse=True
        )[:5]

        # Migration blockers (critical + high issues)
        blocker_patterns = set()
        for f in findings:
            if f.severity in [SecuritySeverity.CRITICAL, SecuritySeverity.HIGH]:
                blocker_patterns.add(f.pattern_name)

        # Remediation hours
        total_hours = sum(
            EFFORT_HOURS[f.remediation_effort] for f in findings
        )

        return SecurityRiskScore(
            total_score=total_score,
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            owasp_coverage=dict(owasp_coverage),
            top_risks=top_risks,
            migration_blockers=list(blocker_patterns)[:10],
            estimated_remediation_hours=total_hours
        )

    def _generate_quinn_context(
        self,
        findings: List[SecurityFinding],
        stacks: List[LegacyStack]
    ) -> QuinnContext:
        """Generate context for Quinn agent review"""
        # Summary
        critical_high = sum(
            1 for f in findings
            if f.severity in [SecuritySeverity.CRITICAL, SecuritySeverity.HIGH]
        )
        summary = f"Legacy security analysis found {len(findings)} issues ({critical_high} critical/high). " \
                  f"Stacks: {', '.join(s.value for s in stacks)}"

        # Focus areas
        focus_areas = []
        owasp_counts: Dict[OWASPCategory, int] = defaultdict(int)
        for f in findings:
            owasp_counts[f.owasp_category] += 1

        for category in sorted(owasp_counts, key=lambda x: owasp_counts[x], reverse=True)[:3]:
            focus_areas.append(f"{category.value} ({owasp_counts[category]} issues)")

        # Priority files
        file_severity: Dict[str, float] = defaultdict(float)
        for f in findings:
            file_severity[f.file_path] += SEVERITY_SCORES[f.severity]

        priority_files = sorted(
            file_severity.keys(),
            key=lambda x: file_severity[x],
            reverse=True
        )

        # OWASP checklist
        owasp_checklist = {}
        for cat in OWASPCategory:
            owasp_checklist[cat.value] = cat in owasp_counts

        # Questions for review
        questions = [
            "Are there additional authentication mechanisms not detected by pattern matching?",
            "Does the application use a WAF or other security middleware?",
            "Are there business logic vulnerabilities beyond code patterns?",
            "What is the data sensitivity level requiring encryption review?",
            "Are there third-party integrations requiring security assessment?"
        ]

        # Recommended tools
        recommended_tools = ["OWASP ZAP", "SonarQube", "Burp Suite"]
        if LegacyStack.PHP_LEGACY in stacks:
            recommended_tools.append("PHPStan Security Rules")
        if any(s in stacks for s in [LegacyStack.VB_NET_WEBFORMS, LegacyStack.CSHARP_WEBFORMS]):
            recommended_tools.append("Roslyn Security Analyzers")
        if LegacyStack.JAVA_LEGACY in stacks:
            recommended_tools.append("SpotBugs with Find-Sec-Bugs")

        return QuinnContext(
            summary=summary,
            focus_areas=focus_areas,
            priority_files=priority_files,
            owasp_checklist=owasp_checklist,
            questions_for_review=questions,
            recommended_tools=recommended_tools
        )

    def _generate_recommendations(
        self,
        findings: List[SecurityFinding],
        stacks: List[LegacyStack],
        risk_score: SecurityRiskScore
    ) -> List[str]:
        """Generate migration security recommendations"""
        recommendations = []

        # Critical issues
        if risk_score.critical_count > 0:
            recommendations.append(
                f"BLOCKER: {risk_score.critical_count} critical security issues must be "
                f"resolved before migration (estimated: {risk_score.estimated_remediation_hours:.0f}h)"
            )

        # Stack-specific
        if LegacyStack.CLASSIC_ASP in stacks:
            recommendations.append(
                "Classic ASP detected: Plan full rewrite to modern framework (ASP.NET Core, Node.js, or Python)"
            )

        if LegacyStack.PHP_LEGACY in stacks:
            has_mysql = any("mysql_" in f.code_snippet for f in findings)
            if has_mysql:
                recommendations.append(
                    "PHP mysql_* functions detected: Upgrade to PHP 8.x with PDO is mandatory"
                )

        if any(s in stacks for s in [LegacyStack.VB_NET_WEBFORMS, LegacyStack.CSHARP_WEBFORMS]):
            recommendations.append(
                "WebForms detected: Consider incremental migration to ASP.NET Core MVC/Blazor"
            )

        # OWASP coverage
        covered = sum(1 for v in risk_score.owasp_coverage.values() if v > 0)
        if covered >= 5:
            recommendations.append(
                f"High OWASP coverage ({covered}/10 categories): Comprehensive security review required"
            )

        # Injection patterns
        injection_count = sum(
            1 for f in findings
            if f.owasp_category == OWASPCategory.A03_INJECTION
        )
        if injection_count > 10:
            recommendations.append(
                f"High injection vulnerability count ({injection_count}): Implement WAF during migration"
            )

        # Authentication
        auth_issues = sum(
            1 for f in findings
            if f.owasp_category == OWASPCategory.A07_AUTH_FAILURES
        )
        if auth_issues > 0:
            recommendations.append(
                "Authentication issues detected: Implement modern identity (OAuth 2.0/OIDC) in target"
            )

        # Crypto
        crypto_issues = sum(
            1 for f in findings
            if f.owasp_category == OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES
        )
        if crypto_issues > 0:
            recommendations.append(
                "Cryptographic issues detected: Audit all encryption and implement modern algorithms"
            )

        # General
        recommendations.append(
            "Run DAST (Dynamic Application Security Testing) on deployed legacy application"
        )
        recommendations.append(
            "Implement security testing in CI/CD pipeline for target application"
        )

        return recommendations

    def _empty_result(
        self,
        analysis_id: str,
        directory: str,
        message: str
    ) -> MigrationSecurityResult:
        """Create empty result with message"""
        return MigrationSecurityResult(
            analysis_id=analysis_id,
            project_path=directory,
            stacks_detected=[],
            findings=[],
            risk_score=SecurityRiskScore(
                total_score=0,
                critical_count=0,
                high_count=0,
                medium_count=0,
                low_count=0,
                owasp_coverage={},
                top_risks=[],
                migration_blockers=[],
                estimated_remediation_hours=0
            ),
            quinn_context=QuinnContext(
                summary=message,
                focus_areas=[],
                priority_files=[],
                owasp_checklist={},
                questions_for_review=[],
                recommended_tools=[]
            ),
            recommendations=[message]
        )

    def get_patterns_by_owasp(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all patterns organized by OWASP category"""
        result: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for pattern in self.patterns:
            result[pattern.owasp_category.value].append({
                "id": pattern.id,
                "name": pattern.name,
                "severity": pattern.severity.value,
                "stacks": [s.value for s in pattern.stacks],
                "description": pattern.description,
                "remediation_effort": pattern.remediation_effort.value
            })

        return dict(result)

    def get_patterns_by_stack(self, stack: LegacyStack) -> List[Dict[str, Any]]:
        """Get all patterns for a specific stack"""
        return [
            {
                "id": p.id,
                "name": p.name,
                "owasp_category": p.owasp_category.value,
                "severity": p.severity.value,
                "description": p.description,
                "legacy_example": p.legacy_example,
                "modern_remediation": p.modern_remediation,
                "remediation_effort": p.remediation_effort.value
            }
            for p in self.patterns
            if stack in p.stacks
        ]

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "total_patterns": len(self.patterns),
            "owasp_coverage": len(set(p.owasp_category for p in self.patterns)),
            "stacks_covered": len(set(s for p in self.patterns for s in p.stacks)),
            "severity_distribution": {
                "critical": sum(1 for p in self.patterns if p.severity == SecuritySeverity.CRITICAL),
                "high": sum(1 for p in self.patterns if p.severity == SecuritySeverity.HIGH),
                "medium": sum(1 for p in self.patterns if p.severity == SecuritySeverity.MEDIUM),
                "low": sum(1 for p in self.patterns if p.severity == SecuritySeverity.LOW)
            }
        }


# Singleton instance
_migration_security_service: Optional[MigrationSecurityService] = None


def get_migration_security_service() -> MigrationSecurityService:
    """
    Factory function to get the MigrationSecurityService singleton.

    Week 113 Fix: This factory was missing, causing ImportError fallback
    in ProjectAssessmentOrchestrator which resulted in 0 security findings.

    Returns:
        MigrationSecurityService: Singleton instance with 60+ OWASP patterns
    """
    global _migration_security_service
    if _migration_security_service is None:
        _migration_security_service = MigrationSecurityService()
    return _migration_security_service
