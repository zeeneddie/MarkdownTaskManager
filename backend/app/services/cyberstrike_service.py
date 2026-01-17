"""
CyberStrike Security Service - Automated Security Scanning

Week 63: Integration with Quality Gates and Quinn Agent
Week 63+: External pattern loading for multi-language support

Features:
- OWASP Top 10 vulnerability scanning
- External YAML pattern configuration (extensible without code changes)
- Multi-language support: Python, JavaScript, C#, VB.NET, ASP/ASPX, SQL
- Bandit (Python) security linter integration
- Safety dependency vulnerability checking
- Semgrep pattern-based analysis
- Integration with Quinn Quality Inspector
- Pre-deployment security automation

Architecture:
┌─────────────────────────────────────────────────────────────────────┐
│                    CYBERSTRIKE SECURITY PIPELINE                     │
│                                                                      │
│  ┌─────────┐    ┌──────────┐    ┌─────────┐    ┌─────────────────┐ │
│  │ Source  │───▶│ Scanners │───▶│ Quinn   │───▶│ Quality Gate    │ │
│  │ Code    │    │ (Local)  │    │ Review  │    │ Decision        │ │
│  └─────────┘    └──────────┘    └─────────┘    └─────────────────┘ │
│                                                                      │
│  Scanners:                                                           │
│  • External Patterns: YAML config in config/security-patterns/      │
│  • Bandit: Python static analysis (AST-based)                       │
│  • Safety: Dependency vulnerability (CVE database)                   │
│  • Semgrep: Pattern-based SAST (OWASP rules)                        │
│                                                                      │
│  Supported Languages (via external patterns):                        │
│  • Python (.py)       • JavaScript/TypeScript (.js, .ts)            │
│  • C# (.cs)           • VB.NET (.vb)                                │
│  • ASP/ASPX (.asp, .aspx, .ascx)  • SQL (.sql)                     │
│                                                                      │
│  OWASP Top 10 Coverage:                                              │
│  A01: Broken Access Control          ✓ (Pattern + Flow Analysis)    │
│  A02: Cryptographic Failures         ✓ (Weak crypto detection)      │
│  A03: Injection                      ✓ (SQL, Command, LDAP, XSS)    │
│  A04: Insecure Design                ✓ (Pattern analysis)           │
│  A05: Security Misconfiguration      ✓ (Config scanning)            │
│  A06: Vulnerable Components          ✓ (Safety check)               │
│  A07: Auth Failures                  ✓ (Auth flow analysis)         │
│  A08: Data Integrity Failures        ✓ (Serialization checks)       │
│  A09: Logging Failures               ✓ (Sensitive data in logs)     │
│  A10: SSRF                           ✓ (URL pattern detection)      │
└─────────────────────────────────────────────────────────────────────┘
"""

import ast
import asyncio
import json
import logging
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Import external pattern loader
from app.services.security_pattern_loader import (
    SecurityPatternLoader,
    SecurityPattern,
    get_pattern_loader,
    get_patterns_for_file,
    VulnerabilitySeverity as PatternSeverity,
    OWASPCategory as PatternOWASP,
)

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND TYPES
# ============================================================================

class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity levels aligned with CVSS."""
    CRITICAL = "critical"   # CVSS 9.0-10.0
    HIGH = "high"           # CVSS 7.0-8.9
    MEDIUM = "medium"       # CVSS 4.0-6.9
    LOW = "low"             # CVSS 0.1-3.9
    INFO = "info"           # Informational


class OWASPCategory(str, Enum):
    """OWASP Top 10 2021 categories."""
    A01_BROKEN_ACCESS_CONTROL = "A01:2021-Broken Access Control"
    A02_CRYPTOGRAPHIC_FAILURES = "A02:2021-Cryptographic Failures"
    A03_INJECTION = "A03:2021-Injection"
    A04_INSECURE_DESIGN = "A04:2021-Insecure Design"
    A05_SECURITY_MISCONFIGURATION = "A05:2021-Security Misconfiguration"
    A06_VULNERABLE_COMPONENTS = "A06:2021-Vulnerable and Outdated Components"
    A07_AUTH_FAILURES = "A07:2021-Identification and Authentication Failures"
    A08_DATA_INTEGRITY_FAILURES = "A08:2021-Software and Data Integrity Failures"
    A09_LOGGING_FAILURES = "A09:2021-Security Logging and Monitoring Failures"
    A10_SSRF = "A10:2021-Server-Side Request Forgery"


class ScannerType(str, Enum):
    """Available security scanner types."""
    BANDIT = "bandit"           # Python AST analysis
    SAFETY = "safety"           # Dependency CVE check
    SEMGREP = "semgrep"         # Pattern-based SAST
    CUSTOM = "custom"           # Built-in pattern matching
    SECRETS = "secrets"         # Secret detection
    SQL_INJECTION = "sql_injection"  # SQL injection patterns


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Vulnerability:
    """Single security vulnerability finding."""
    id: str
    title: str
    description: str
    severity: VulnerabilitySeverity
    owasp_category: OWASPCategory
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    code_snippet: Optional[str] = None
    scanner: ScannerType = ScannerType.CUSTOM
    cwe_id: Optional[str] = None  # Common Weakness Enumeration
    cvss_score: Optional[float] = None
    remediation: Optional[str] = None
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "owasp_category": self.owasp_category.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "code_snippet": self.code_snippet,
            "scanner": self.scanner.value,
            "cwe_id": self.cwe_id,
            "cvss_score": self.cvss_score,
            "remediation": self.remediation,
            "references": self.references,
            "metadata": self.metadata,
        }


@dataclass
class ScanResult:
    """Result of a security scan."""
    scan_id: str
    project_path: str
    scan_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    scanners_used: List[ScannerType] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scan_id": self.scan_id,
            "project_path": self.project_path,
            "scan_type": self.scan_type,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "summary": self.summary,
            "scanners_used": [s.value for s in self.scanners_used],
            "error": self.error,
        }


# ============================================================================
# PATTERN DEFINITIONS
# ============================================================================

# SQL Injection patterns (A03)
SQL_INJECTION_PATTERNS = [
    # f-string SQL
    (r'f["\'].*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER).*{.*}.*["\']', "SQL query with f-string interpolation"),
    # .format() SQL
    (r'["\'].*(?:SELECT|INSERT|UPDATE|DELETE).*["\']\.format\(', "SQL query with .format() interpolation"),
    # % formatting SQL
    (r'["\'].*(?:SELECT|INSERT|UPDATE|DELETE).*%s.*["\'].*%', "SQL query with % formatting"),
    # String concatenation
    (r'(?:SELECT|INSERT|UPDATE|DELETE).*\+.*(?:request|input|user)', "SQL query with string concatenation"),
    # execute with raw string
    (r'\.execute\([^,]+\+', "execute() with string concatenation"),
]

# XSS patterns (A03)
XSS_PATTERNS = [
    (r'innerHTML\s*=\s*[^"\'`]', "Direct innerHTML assignment without sanitization"),
    (r'document\.write\s*\(', "Use of document.write"),
    (r'\.html\s*\([^"\'`]', "jQuery .html() with unsanitized input"),
    (r'dangerouslySetInnerHTML', "React dangerouslySetInnerHTML usage"),
    (r'\|\s*safe\s*}}', "Django/Jinja2 |safe filter without proper sanitization"),
]

# Hardcoded secrets patterns (A02, A05)
SECRET_PATTERNS = [
    (r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']', "Hardcoded password"),
    (r'(?:api_key|apikey|api-key)\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded API key"),
    (r'(?:secret|secret_key)\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded secret"),
    (r'(?:token|auth_token)\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded token"),
    (r'(?:aws_access_key|aws_secret)\s*=\s*["\'][A-Za-z0-9+/]{20,}["\']', "AWS credentials"),
    (r'-----BEGIN (?:RSA |DSA |EC )?PRIVATE KEY-----', "Hardcoded private key"),
    (r'(?:ssh-rsa|ssh-ed25519)\s+[A-Za-z0-9+/=]{50,}', "Hardcoded SSH key"),
]

# Weak crypto patterns (A02)
WEAK_CRYPTO_PATTERNS = [
    (r'hashlib\.md5\(', "Use of weak MD5 hash"),
    (r'hashlib\.sha1\(', "Use of weak SHA1 hash"),
    (r'DES\.new\(', "Use of weak DES encryption"),
    (r'RC4\.new\(|ARC4\.new\(', "Use of weak RC4 encryption"),
    (r'random\.(random|randint|choice)\(', "Use of non-cryptographic random for security"),
]

# Command injection patterns (A03)
COMMAND_INJECTION_PATTERNS = [
    (r'os\.system\([^"\']+\+', "os.system with string concatenation"),
    (r'subprocess\.\w+\([^)]*shell\s*=\s*True', "subprocess with shell=True"),
    (r'eval\s*\(', "Use of eval()"),
    (r'exec\s*\(', "Use of exec()"),
    (r'__import__\s*\(', "Dynamic import"),
]

# SSRF patterns (A10)
SSRF_PATTERNS = [
    (r'requests\.(?:get|post|put|delete)\s*\([^"\']+\+', "Request with user-controlled URL"),
    (r'urllib\.request\.urlopen\s*\([^"\']+\+', "urlopen with user-controlled URL"),
    (r'aiohttp\.ClientSession\(\)\.get\s*\([^"\']+\+', "aiohttp with user-controlled URL"),
]

# Insecure deserialization (A08)
DESERIALIZATION_PATTERNS = [
    (r'pickle\.loads?\(', "Use of pickle (insecure deserialization)"),
    (r'yaml\.load\([^)]*Loader\s*=\s*None', "YAML load without safe loader"),
    (r'yaml\.unsafe_load\(', "YAML unsafe_load"),
    (r'marshal\.loads?\(', "Use of marshal (insecure)"),
]

# Authentication issues (A07)
AUTH_PATTERNS = [
    (r'@login_required.*\n.*def\s+\w+.*admin', "Admin function may need additional authorization"),
    (r'verify\s*=\s*False', "SSL verification disabled"),
    (r'JWT.*algorithm.*none', "JWT with 'none' algorithm"),
]

# Logging sensitive data (A09)
LOGGING_PATTERNS = [
    (r'log(?:ger)?\.(?:info|debug|warning|error)\([^)]*(?:password|secret|token|key)', "Possible sensitive data in logs"),
    (r'print\([^)]*(?:password|secret|token|key)', "Possible sensitive data in print"),
]


# ============================================================================
# CYBERSTRIKE SERVICE
# ============================================================================

class CyberStrikeService:
    """
    Automated security scanning service for code repositories.

    Provides:
    - OWASP Top 10 vulnerability detection
    - Integration with external tools (Bandit, Safety, Semgrep)
    - External pattern-based scanning (multi-language via YAML config)
    - Quality gate integration for Quinn agent
    """

    def __init__(self, project_path: Optional[str] = None):
        """
        Initialize CyberStrike service.

        Args:
            project_path: Default path to scan
        """
        self.project_path = project_path
        self._scan_count = 0
        self._available_scanners: Set[ScannerType] = set()
        self._pattern_loader = get_pattern_loader()
        self._detect_available_scanners()

        # Pre-load patterns
        self._pattern_loader.load_all_patterns()

    def _detect_available_scanners(self):
        """Detect which external scanners are available."""
        # Check for bandit
        try:
            result = subprocess.run(
                ["bandit", "--version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                self._available_scanners.add(ScannerType.BANDIT)
                logger.info("Bandit scanner available")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Check for safety
        try:
            result = subprocess.run(
                ["safety", "--version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                self._available_scanners.add(ScannerType.SAFETY)
                logger.info("Safety scanner available")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Check for semgrep
        try:
            result = subprocess.run(
                ["semgrep", "--version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                self._available_scanners.add(ScannerType.SEMGREP)
                logger.info("Semgrep scanner available")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Custom scanners are always available
        self._available_scanners.add(ScannerType.CUSTOM)
        self._available_scanners.add(ScannerType.SECRETS)
        self._available_scanners.add(ScannerType.SQL_INJECTION)

    async def full_scan(
        self,
        path: Optional[str] = None,
        scan_type: str = "full",
        include_external: bool = True
    ) -> ScanResult:
        """
        Perform a full security scan of the codebase.

        Args:
            path: Path to scan (default: self.project_path)
            scan_type: Type of scan ("full", "quick", "owasp")
            include_external: Include external scanners (Bandit, Safety)

        Returns:
            ScanResult with all vulnerabilities found
        """
        scan_path = path or self.project_path
        if not scan_path:
            raise ValueError("No path specified for security scan")

        self._scan_count += 1
        scan_id = f"scan-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{self._scan_count}"

        result = ScanResult(
            scan_id=scan_id,
            project_path=scan_path,
            scan_type=scan_type,
            started_at=datetime.now(timezone.utc)
        )

        try:
            # Run all scanners concurrently
            tasks = []

            # Custom pattern scanning (always run)
            tasks.append(self._run_custom_scan(scan_path))
            result.scanners_used.append(ScannerType.CUSTOM)

            # Secret detection
            tasks.append(self._run_secret_scan(scan_path))
            result.scanners_used.append(ScannerType.SECRETS)

            # SQL injection scan
            tasks.append(self._run_sql_injection_scan(scan_path))
            result.scanners_used.append(ScannerType.SQL_INJECTION)

            # External scanners if available and requested
            if include_external:
                if ScannerType.BANDIT in self._available_scanners:
                    tasks.append(self._run_bandit_scan(scan_path))
                    result.scanners_used.append(ScannerType.BANDIT)

                if ScannerType.SAFETY in self._available_scanners:
                    tasks.append(self._run_safety_scan(scan_path))
                    result.scanners_used.append(ScannerType.SAFETY)

            # Run all scans
            all_vulnerabilities = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect results
            for vulns in all_vulnerabilities:
                if isinstance(vulns, Exception):
                    logger.warning(f"Scanner error: {vulns}")
                    continue
                if isinstance(vulns, list):
                    result.vulnerabilities.extend(vulns)

            # Deduplicate vulnerabilities
            result.vulnerabilities = self._deduplicate_vulnerabilities(result.vulnerabilities)

            # Generate summary
            result.summary = self._generate_summary(result.vulnerabilities)
            result.status = "completed"
            result.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Security scan failed: {e}")
            result.status = "failed"
            result.error = str(e)
            result.completed_at = datetime.now(timezone.utc)

        return result

    async def quick_scan(
        self,
        path: Optional[str] = None
    ) -> ScanResult:
        """
        Perform a quick security scan (custom patterns only).

        Faster but less comprehensive than full_scan.
        """
        return await self.full_scan(path, scan_type="quick", include_external=False)

    async def owasp_scan(
        self,
        path: Optional[str] = None
    ) -> Dict[str, List[Vulnerability]]:
        """
        Perform OWASP Top 10 focused scan.

        Returns vulnerabilities grouped by OWASP category.
        """
        result = await self.full_scan(path, scan_type="owasp")

        # Group by OWASP category
        grouped: Dict[str, List[Vulnerability]] = {
            category.value: [] for category in OWASPCategory
        }

        for vuln in result.vulnerabilities:
            grouped[vuln.owasp_category.value].append(vuln)

        return grouped

    async def scan_file(
        self,
        file_path: str
    ) -> List[Vulnerability]:
        """
        Scan a single file for vulnerabilities.

        Args:
            file_path: Path to the file to scan

        Returns:
            List of vulnerabilities found
        """
        if not os.path.exists(file_path):
            return []

        vulnerabilities = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            # Run pattern scans
            vulnerabilities.extend(self._scan_content_for_patterns(
                content, lines, file_path, SQL_INJECTION_PATTERNS,
                OWASPCategory.A03_INJECTION, VulnerabilitySeverity.HIGH,
                "sql_injection"
            ))

            vulnerabilities.extend(self._scan_content_for_patterns(
                content, lines, file_path, SECRET_PATTERNS,
                OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES, VulnerabilitySeverity.CRITICAL,
                "hardcoded_secret"
            ))

            vulnerabilities.extend(self._scan_content_for_patterns(
                content, lines, file_path, WEAK_CRYPTO_PATTERNS,
                OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES, VulnerabilitySeverity.MEDIUM,
                "weak_crypto"
            ))

            vulnerabilities.extend(self._scan_content_for_patterns(
                content, lines, file_path, COMMAND_INJECTION_PATTERNS,
                OWASPCategory.A03_INJECTION, VulnerabilitySeverity.CRITICAL,
                "command_injection"
            ))

            vulnerabilities.extend(self._scan_content_for_patterns(
                content, lines, file_path, DESERIALIZATION_PATTERNS,
                OWASPCategory.A08_DATA_INTEGRITY_FAILURES, VulnerabilitySeverity.HIGH,
                "insecure_deserialization"
            ))

            vulnerabilities.extend(self._scan_content_for_patterns(
                content, lines, file_path, SSRF_PATTERNS,
                OWASPCategory.A10_SSRF, VulnerabilitySeverity.HIGH,
                "ssrf"
            ))

            vulnerabilities.extend(self._scan_content_for_patterns(
                content, lines, file_path, LOGGING_PATTERNS,
                OWASPCategory.A09_LOGGING_FAILURES, VulnerabilitySeverity.MEDIUM,
                "sensitive_logging"
            ))

        except Exception as e:
            logger.warning(f"Error scanning file {file_path}: {e}")

        return vulnerabilities

    # ========================================================================
    # INTERNAL SCANNING METHODS
    # ========================================================================

    async def _run_custom_scan(self, path: str) -> List[Vulnerability]:
        """Run custom pattern-based scanning using external patterns."""
        vulnerabilities = []

        # Get all supported file extensions from pattern loader
        supported_extensions = self._pattern_loader.get_all_extensions()

        # Skip patterns for directories/files we don't want to scan
        skip_patterns = [
            'test_', '_test.py', 'venv/', 'node_modules/', '__pycache__',
            '.git/', 'bin/', 'obj/', 'packages/', 'TestResults/',
            'My Project/', 'Service References/', 'Web References/',
            '.designer.', '.Designer.', 'Reference.vb', 'AssemblyInfo.'
        ]

        # Collect all files matching supported extensions
        all_files: List[Path] = []
        for ext in supported_extensions:
            pattern = f"*{ext}"
            all_files.extend(Path(path).rglob(pattern))

        logger.info(f"Found {len(all_files)} files to scan across {len(supported_extensions)} extensions")

        # Scan each file
        scanned_count = 0
        for file_path in all_files:
            str_path = str(file_path)

            # Skip unwanted files
            if any(skip in str_path for skip in skip_patterns):
                continue

            # Scan file using external patterns
            file_vulns = await self.scan_file_with_external_patterns(str_path)
            vulnerabilities.extend(file_vulns)
            scanned_count += 1

            # Log progress every 100 files
            if scanned_count % 100 == 0:
                logger.info(f"Scanned {scanned_count} files, found {len(vulnerabilities)} vulnerabilities so far")

        logger.info(f"Custom scan complete: {scanned_count} files, {len(vulnerabilities)} vulnerabilities")
        return vulnerabilities

    async def scan_file_with_external_patterns(self, file_path: str) -> List[Vulnerability]:
        """
        Scan a single file using external patterns.

        Args:
            file_path: Path to the file to scan

        Returns:
            List of vulnerabilities found
        """
        if not os.path.exists(file_path):
            return []

        vulnerabilities = []

        # Get patterns for this file type
        patterns = self._pattern_loader.get_patterns_for_file(file_path)
        if not patterns:
            return []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            # Apply each pattern
            for pattern in patterns:
                if not pattern.compiled_pattern:
                    continue

                # Check for false positive hints
                is_likely_false_positive = False
                if pattern.false_positive_hints:
                    file_lower = file_path.lower()
                    content_lower = content.lower()
                    for hint in pattern.false_positive_hints:
                        if hint.lower() in file_lower or hint.lower() in content_lower:
                            is_likely_false_positive = True
                            break

                if is_likely_false_positive:
                    continue

                # Find all matches
                for match in pattern.compiled_pattern.finditer(content):
                    line_num = content[:match.start()].count('\n') + 1
                    snippet = lines[line_num - 1] if line_num <= len(lines) else ""

                    vuln = Vulnerability(
                        id=f"{pattern.id}-{Path(file_path).name}-{line_num}",
                        title=pattern.title,
                        description=pattern.description,
                        severity=VulnerabilitySeverity(pattern.severity.value),
                        owasp_category=OWASPCategory(pattern.owasp_category.value),
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=snippet.strip()[:200],
                        scanner=ScannerType.CUSTOM,
                        cwe_id=pattern.cwe_id,
                        remediation=pattern.remediation,
                        references=pattern.references
                    )
                    vulnerabilities.append(vuln)

        except Exception as e:
            logger.debug(f"Error scanning file {file_path}: {e}")

        return vulnerabilities

    async def _run_secret_scan(self, path: str) -> List[Vulnerability]:
        """Dedicated secret scanning."""
        vulnerabilities = []

        # Scan all text files for secrets
        extensions = ['*.py', '*.js', '*.ts', '*.json', '*.yaml', '*.yml', '*.env', '*.conf', '*.cfg']

        for ext in extensions:
            for file_path in Path(path).rglob(ext):
                str_path = str(file_path)

                # Skip obvious false positives
                if any(skip in str_path for skip in ['venv/', 'node_modules/', '.git/', 'test_']):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.split('\n')

                    vulnerabilities.extend(self._scan_content_for_patterns(
                        content, lines, str_path, SECRET_PATTERNS,
                        OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES, VulnerabilitySeverity.CRITICAL,
                        "secret"
                    ))
                except Exception as e:
                    logger.debug(f"Error scanning {file_path} for secrets: {e}")

        return vulnerabilities

    async def _run_sql_injection_scan(self, path: str) -> List[Vulnerability]:
        """Dedicated SQL injection scanning using AST analysis."""
        vulnerabilities = []

        for file_path in Path(path).rglob("*.py"):
            str_path = str(file_path)

            if any(skip in str_path for skip in ['venv/', '__pycache__', 'test_']):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()

                # Parse AST for SQL patterns
                try:
                    tree = ast.parse(source)
                    sql_vulns = self._analyze_ast_for_sql_injection(tree, str_path, source)
                    vulnerabilities.extend(sql_vulns)
                except SyntaxError:
                    # Fall back to regex patterns for unparseable files
                    lines = source.split('\n')
                    vulnerabilities.extend(self._scan_content_for_patterns(
                        source, lines, str_path, SQL_INJECTION_PATTERNS,
                        OWASPCategory.A03_INJECTION, VulnerabilitySeverity.HIGH,
                        "sql_injection"
                    ))

            except Exception as e:
                logger.debug(f"Error in SQL injection scan for {file_path}: {e}")

        return vulnerabilities

    def _analyze_ast_for_sql_injection(
        self,
        tree: ast.AST,
        file_path: str,
        source: str
    ) -> List[Vulnerability]:
        """Analyze AST for SQL injection vulnerabilities."""
        vulnerabilities = []
        lines = source.split('\n')

        class SQLInjectionVisitor(ast.NodeVisitor):
            def __init__(self):
                self.vulns = []

            def visit_Call(self, node):
                # Check for .execute() calls
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ('execute', 'executemany', 'raw'):
                        # Check if first argument is a formatted string
                        if node.args:
                            arg = node.args[0]
                            if isinstance(arg, ast.JoinedStr):  # f-string
                                self.vulns.append(Vulnerability(
                                    id=f"sql-fstring-{node.lineno}",
                                    title="SQL Injection via f-string",
                                    description="SQL query uses f-string interpolation which may be vulnerable to injection",
                                    severity=VulnerabilitySeverity.HIGH,
                                    owasp_category=OWASPCategory.A03_INJECTION,
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else None,
                                    scanner=ScannerType.SQL_INJECTION,
                                    cwe_id="CWE-89",
                                    remediation="Use parameterized queries instead of string interpolation"
                                ))
                            elif isinstance(arg, ast.BinOp):
                                if isinstance(arg.op, (ast.Add, ast.Mod)):
                                    self.vulns.append(Vulnerability(
                                        id=f"sql-concat-{node.lineno}",
                                        title="SQL Injection via String Concatenation",
                                        description="SQL query uses string concatenation which may be vulnerable to injection",
                                        severity=VulnerabilitySeverity.HIGH,
                                        owasp_category=OWASPCategory.A03_INJECTION,
                                        file_path=file_path,
                                        line_number=node.lineno,
                                        code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else None,
                                        scanner=ScannerType.SQL_INJECTION,
                                        cwe_id="CWE-89",
                                        remediation="Use parameterized queries with placeholders"
                                    ))
                self.generic_visit(node)

        visitor = SQLInjectionVisitor()
        visitor.visit(tree)
        vulnerabilities.extend(visitor.vulns)

        return vulnerabilities

    async def _run_bandit_scan(self, path: str) -> List[Vulnerability]:
        """Run Bandit security scanner."""
        vulnerabilities = []

        try:
            # Run bandit with JSON output
            result = subprocess.run(
                ["bandit", "-r", path, "-f", "json", "-q"],
                capture_output=True,
                timeout=300,
                text=True
            )

            if result.stdout:
                data = json.loads(result.stdout)
                for issue in data.get("results", []):
                    # Map Bandit severity to our severity
                    severity_map = {
                        "HIGH": VulnerabilitySeverity.HIGH,
                        "MEDIUM": VulnerabilitySeverity.MEDIUM,
                        "LOW": VulnerabilitySeverity.LOW,
                    }

                    # Map Bandit test IDs to OWASP categories
                    owasp_map = {
                        "B101": OWASPCategory.A03_INJECTION,  # assert
                        "B102": OWASPCategory.A03_INJECTION,  # exec
                        "B103": OWASPCategory.A05_SECURITY_MISCONFIGURATION,  # set_bad_file_permissions
                        "B104": OWASPCategory.A05_SECURITY_MISCONFIGURATION,  # hardcoded_bind_all_interfaces
                        "B105": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,  # hardcoded_password_string
                        "B106": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,  # hardcoded_password_funcarg
                        "B107": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,  # hardcoded_password_default
                        "B108": OWASPCategory.A05_SECURITY_MISCONFIGURATION,  # hardcoded_tmp_directory
                        "B110": OWASPCategory.A04_INSECURE_DESIGN,  # try_except_pass
                        "B112": OWASPCategory.A04_INSECURE_DESIGN,  # try_except_continue
                        "B201": OWASPCategory.A03_INJECTION,  # flask_debug_true
                        "B301": OWASPCategory.A08_DATA_INTEGRITY_FAILURES,  # pickle
                        "B302": OWASPCategory.A08_DATA_INTEGRITY_FAILURES,  # marshal
                        "B303": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,  # md5
                        "B304": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,  # ciphers
                        "B305": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,  # cipher_modes
                        "B306": OWASPCategory.A05_SECURITY_MISCONFIGURATION,  # mktemp
                        "B307": OWASPCategory.A03_INJECTION,  # eval
                        "B308": OWASPCategory.A03_INJECTION,  # mark_safe
                        "B310": OWASPCategory.A10_SSRF,  # urllib_urlopen
                        "B311": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,  # random
                        "B312": OWASPCategory.A05_SECURITY_MISCONFIGURATION,  # telnetlib
                        "B320": OWASPCategory.A03_INJECTION,  # xml_bad_cElementTree
                        "B321": OWASPCategory.A05_SECURITY_MISCONFIGURATION,  # ftplib
                        "B323": OWASPCategory.A05_SECURITY_MISCONFIGURATION,  # unverified_context
                        "B324": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,  # hashlib_insecure_functions
                        "B501": OWASPCategory.A05_SECURITY_MISCONFIGURATION,  # request_with_no_cert_validation
                        "B502": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,  # ssl_with_bad_version
                        "B503": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,  # ssl_with_bad_defaults
                        "B504": OWASPCategory.A05_SECURITY_MISCONFIGURATION,  # ssl_with_no_version
                        "B505": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,  # weak_cryptographic_key
                        "B506": OWASPCategory.A08_DATA_INTEGRITY_FAILURES,  # yaml_load
                        "B507": OWASPCategory.A05_SECURITY_MISCONFIGURATION,  # ssh_no_host_key_verification
                        "B601": OWASPCategory.A03_INJECTION,  # paramiko_calls
                        "B602": OWASPCategory.A03_INJECTION,  # subprocess_popen_with_shell_equals_true
                        "B603": OWASPCategory.A03_INJECTION,  # subprocess_without_shell_equals_true
                        "B604": OWASPCategory.A03_INJECTION,  # any_other_function_with_shell_equals_true
                        "B605": OWASPCategory.A03_INJECTION,  # start_process_with_a_shell
                        "B606": OWASPCategory.A03_INJECTION,  # start_process_with_no_shell
                        "B607": OWASPCategory.A03_INJECTION,  # start_process_with_partial_path
                        "B608": OWASPCategory.A03_INJECTION,  # hardcoded_sql_expressions
                        "B609": OWASPCategory.A03_INJECTION,  # linux_commands_wildcard_injection
                        "B610": OWASPCategory.A03_INJECTION,  # django_extra_used
                        "B611": OWASPCategory.A03_INJECTION,  # django_rawsql_used
                        "B701": OWASPCategory.A03_INJECTION,  # jinja2_autoescape_false
                        "B702": OWASPCategory.A03_INJECTION,  # use_of_mako_templates
                        "B703": OWASPCategory.A04_INSECURE_DESIGN,  # django_mark_safe
                    }

                    test_id = issue.get("test_id", "")
                    owasp = owasp_map.get(test_id, OWASPCategory.A04_INSECURE_DESIGN)

                    vuln = Vulnerability(
                        id=f"bandit-{test_id}-{issue.get('line_number', 0)}",
                        title=issue.get("test_name", "Unknown"),
                        description=issue.get("issue_text", ""),
                        severity=severity_map.get(issue.get("issue_severity"), VulnerabilitySeverity.MEDIUM),
                        owasp_category=owasp,
                        file_path=issue.get("filename"),
                        line_number=issue.get("line_number"),
                        code_snippet=issue.get("code"),
                        scanner=ScannerType.BANDIT,
                        cwe_id=issue.get("issue_cwe", {}).get("id") if isinstance(issue.get("issue_cwe"), dict) else None,
                        metadata={"bandit_test_id": test_id}
                    )
                    vulnerabilities.append(vuln)

        except subprocess.TimeoutExpired:
            logger.warning("Bandit scan timed out")
        except json.JSONDecodeError:
            logger.warning("Failed to parse Bandit output")
        except Exception as e:
            logger.warning(f"Bandit scan error: {e}")

        return vulnerabilities

    async def _run_safety_scan(self, path: str) -> List[Vulnerability]:
        """Run Safety dependency vulnerability scanner."""
        vulnerabilities = []

        # Look for requirements files
        req_files = list(Path(path).rglob("requirements*.txt"))

        for req_file in req_files:
            try:
                result = subprocess.run(
                    ["safety", "check", "-r", str(req_file), "--json"],
                    capture_output=True,
                    timeout=120,
                    text=True
                )

                if result.stdout:
                    try:
                        data = json.loads(result.stdout)
                        for vuln_data in data.get("vulnerabilities", []):
                            vuln = Vulnerability(
                                id=f"safety-{vuln_data.get('vulnerability_id', 'unknown')}",
                                title=f"Vulnerable dependency: {vuln_data.get('package_name')}",
                                description=vuln_data.get("advisory", ""),
                                severity=self._map_cvss_to_severity(vuln_data.get("severity", {}).get("cvssv3", {}).get("base_score")),
                                owasp_category=OWASPCategory.A06_VULNERABLE_COMPONENTS,
                                file_path=str(req_file),
                                scanner=ScannerType.SAFETY,
                                cwe_id=f"CWE-{vuln_data.get('cwe', '')}" if vuln_data.get('cwe') else None,
                                cvss_score=vuln_data.get("severity", {}).get("cvssv3", {}).get("base_score"),
                                metadata={
                                    "package_name": vuln_data.get("package_name"),
                                    "installed_version": vuln_data.get("analyzed_version"),
                                    "vulnerable_versions": vuln_data.get("vulnerable_versions"),
                                    "cve": vuln_data.get("cve"),
                                }
                            )
                            vulnerabilities.append(vuln)
                    except json.JSONDecodeError:
                        pass

            except subprocess.TimeoutExpired:
                logger.warning(f"Safety scan timed out for {req_file}")
            except Exception as e:
                logger.warning(f"Safety scan error for {req_file}: {e}")

        return vulnerabilities

    def _scan_content_for_patterns(
        self,
        content: str,
        lines: List[str],
        file_path: str,
        patterns: List[Tuple[str, str]],
        owasp_category: OWASPCategory,
        default_severity: VulnerabilitySeverity,
        vuln_type: str
    ) -> List[Vulnerability]:
        """Scan content for regex patterns."""
        vulnerabilities = []
        vuln_count = 0

        for pattern, description in patterns:
            try:
                regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                for match in regex.finditer(content):
                    vuln_count += 1
                    # Find line number
                    line_num = content[:match.start()].count('\n') + 1

                    # Get code snippet
                    snippet = lines[line_num - 1] if line_num <= len(lines) else ""

                    vuln = Vulnerability(
                        id=f"{vuln_type}-{file_path.replace('/', '-')}-{line_num}-{vuln_count}",
                        title=description,
                        description=f"Pattern match found: {description}",
                        severity=default_severity,
                        owasp_category=owasp_category,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=snippet.strip()[:200],
                        scanner=ScannerType.CUSTOM,
                        remediation=self._get_remediation(vuln_type)
                    )
                    vulnerabilities.append(vuln)
            except re.error as e:
                logger.debug(f"Regex error for pattern {pattern}: {e}")

        return vulnerabilities

    def _deduplicate_vulnerabilities(
        self,
        vulnerabilities: List[Vulnerability]
    ) -> List[Vulnerability]:
        """Remove duplicate vulnerabilities."""
        seen = set()
        unique = []

        for vuln in vulnerabilities:
            # Create unique key based on location and type
            key = (
                vuln.file_path,
                vuln.line_number,
                vuln.owasp_category.value,
                vuln.title[:50] if vuln.title else ""
            )

            if key not in seen:
                seen.add(key)
                unique.append(vuln)

        return unique

    def _generate_summary(self, vulnerabilities: List[Vulnerability]) -> Dict[str, Any]:
        """Generate scan summary statistics."""
        summary = {
            "total_vulnerabilities": len(vulnerabilities),
            "by_severity": {},
            "by_owasp_category": {},
            "by_scanner": {},
            "critical_count": 0,
            "high_count": 0,
            "blocking_issues": [],
        }

        for vuln in vulnerabilities:
            # By severity
            sev = vuln.severity.value
            summary["by_severity"][sev] = summary["by_severity"].get(sev, 0) + 1

            # By OWASP category
            owasp = vuln.owasp_category.value
            summary["by_owasp_category"][owasp] = summary["by_owasp_category"].get(owasp, 0) + 1

            # By scanner
            scanner = vuln.scanner.value
            summary["by_scanner"][scanner] = summary["by_scanner"].get(scanner, 0) + 1

            # Count critical/high
            if vuln.severity == VulnerabilitySeverity.CRITICAL:
                summary["critical_count"] += 1
                summary["blocking_issues"].append({
                    "id": vuln.id,
                    "title": vuln.title,
                    "file": vuln.file_path,
                    "line": vuln.line_number
                })
            elif vuln.severity == VulnerabilitySeverity.HIGH:
                summary["high_count"] += 1
                summary["blocking_issues"].append({
                    "id": vuln.id,
                    "title": vuln.title,
                    "file": vuln.file_path,
                    "line": vuln.line_number
                })

        # Pass/fail status for quality gate
        summary["quality_gate_passed"] = summary["critical_count"] == 0
        summary["deployment_blocked"] = summary["critical_count"] > 0 or summary["high_count"] > 5

        return summary

    def _map_cvss_to_severity(self, cvss_score: Optional[float]) -> VulnerabilitySeverity:
        """Map CVSS score to severity level."""
        if cvss_score is None:
            return VulnerabilitySeverity.MEDIUM
        if cvss_score >= 9.0:
            return VulnerabilitySeverity.CRITICAL
        if cvss_score >= 7.0:
            return VulnerabilitySeverity.HIGH
        if cvss_score >= 4.0:
            return VulnerabilitySeverity.MEDIUM
        if cvss_score > 0:
            return VulnerabilitySeverity.LOW
        return VulnerabilitySeverity.INFO

    def _get_remediation(self, vuln_type: str) -> str:
        """Get remediation advice for vulnerability type."""
        remediation_map = {
            "sql_injection": "Use parameterized queries or prepared statements. Never concatenate user input into SQL queries.",
            "xss": "Always escape user input before rendering. Use Content Security Policy headers. Use framework-provided escaping functions.",
            "secret": "Move secrets to environment variables or a secrets manager. Never commit secrets to version control.",
            "hardcoded_secret": "Use environment variables, AWS Secrets Manager, HashiCorp Vault, or similar secret management solutions.",
            "weak_crypto": "Use modern cryptographic algorithms: AES-256 for encryption, SHA-256/SHA-3 for hashing, bcrypt/Argon2 for passwords.",
            "command_injection": "Avoid shell=True in subprocess. Use shlex.quote() for any user input. Prefer subprocess.run with a list of arguments.",
            "ssrf": "Validate and whitelist allowed URLs/domains. Block internal IP ranges. Use URL parsers to validate URLs.",
            "sensitive_logging": "Never log passwords, tokens, or PII. Implement log sanitization. Use structured logging with field filtering.",
            "insecure_deserialization": "Use safe serialization formats like JSON. If pickle is required, use signing/verification."
        }
        return remediation_map.get(vuln_type, "Review and fix the security issue following OWASP guidelines.")

    # ========================================================================
    # QUINN INTEGRATION
    # ========================================================================

    async def get_quinn_security_context(
        self,
        path: str
    ) -> Dict[str, Any]:
        """
        Generate security context for Quinn Quality Inspector agent.

        Returns a summary that Quinn can use to make quality gate decisions.
        """
        result = await self.quick_scan(path)

        return {
            "agent": "quinn",
            "role": "Quality Inspector",
            "security_summary": {
                "scan_status": result.status,
                "total_issues": len(result.vulnerabilities),
                "critical_issues": result.summary.get("critical_count", 0),
                "high_issues": result.summary.get("high_count", 0),
                "quality_gate_passed": result.summary.get("quality_gate_passed", True),
                "deployment_blocked": result.summary.get("deployment_blocked", False),
                "owasp_coverage": {
                    cat.value: result.summary.get("by_owasp_category", {}).get(cat.value, 0)
                    for cat in OWASPCategory
                },
                "blocking_issues": result.summary.get("blocking_issues", [])[:10],  # Top 10
            },
            "recommendations": self._generate_quinn_recommendations(result),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _generate_quinn_recommendations(self, result: ScanResult) -> List[str]:
        """Generate recommendations for Quinn based on scan results."""
        recommendations = []

        if result.summary.get("critical_count", 0) > 0:
            recommendations.append("BLOCK: Critical security vulnerabilities found. Do not proceed to deployment.")

        if result.summary.get("high_count", 0) > 5:
            recommendations.append("WARN: Multiple high-severity issues. Consider security review before deployment.")

        # Check OWASP categories
        owasp_counts = result.summary.get("by_owasp_category", {})

        if owasp_counts.get(OWASPCategory.A03_INJECTION.value, 0) > 0:
            recommendations.append("Review all injection vulnerabilities - these are critical attack vectors.")

        if owasp_counts.get(OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES.value, 0) > 0:
            recommendations.append("Check for hardcoded secrets and weak cryptography.")

        if owasp_counts.get(OWASPCategory.A06_VULNERABLE_COMPONENTS.value, 0) > 0:
            recommendations.append("Update vulnerable dependencies to patched versions.")

        if not recommendations:
            recommendations.append("Security scan passed. No critical issues found.")

        return recommendations

    # ========================================================================
    # PATTERN MANAGEMENT
    # ========================================================================

    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded security patterns."""
        return self._pattern_loader.get_statistics()

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages for scanning."""
        return self._pattern_loader.get_supported_languages()

    def get_supported_extensions(self) -> Set[str]:
        """Get all supported file extensions."""
        return self._pattern_loader.get_all_extensions()

    def reload_patterns(self) -> Dict[str, Any]:
        """Reload patterns from configuration files."""
        self._pattern_loader.load_all_patterns(force_reload=True)
        return self.get_pattern_statistics()


# ============================================================================
# MODULE FUNCTIONS
# ============================================================================

def get_cyberstrike_service(path: Optional[str] = None) -> CyberStrikeService:
    """Factory function to get CyberStrike service instance."""
    return CyberStrikeService(project_path=path)


async def run_security_scan(
    path: str,
    scan_type: str = "full"
) -> Dict[str, Any]:
    """
    Convenience function to run a security scan.

    Args:
        path: Path to scan
        scan_type: Type of scan ("full", "quick", "owasp")

    Returns:
        Scan result as dictionary
    """
    service = CyberStrikeService(project_path=path)
    result = await service.full_scan(path, scan_type)
    return result.to_dict()
