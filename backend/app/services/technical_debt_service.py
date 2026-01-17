"""
Technical Debt Service

Service for managing technical debt:
- Scan codebase with multiple tools (ruff, eslint, bandit, coverage)
- Calculate debt metrics (TDR, interest, ROI)
- Prioritize remediation based on impact
- Track resolution progress

Author: Claude Code (Week 18 Day 2)
Date: 2025-11-22
"""

import subprocess
import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.models.technical_debt import (
    TechnicalDebtItem, TechnicalDebtSnapshot, RemediationPlan,
    DebtResolution, QualityGateResult,
    DebtType, DebtSeverity, DebtStatus, DetectionSource
)
from app.scanners import get_scanner_registry, ScanFinding, Severity, FindingType


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ScanResult:
    """Result from a single scanner"""
    source: DetectionSource
    items: List[Dict[str, Any]]
    duration_seconds: float
    success: bool
    error: Optional[str] = None
    version: Optional[str] = None


@dataclass
class DebtMetrics:
    """Calculated debt metrics"""
    total_items: int = 0
    total_principal: float = 0.0
    total_interest: float = 0.0
    debt_ratio: float = 0.0

    # By type
    items_by_type: Dict[str, int] = field(default_factory=dict)
    principal_by_type: Dict[str, float] = field(default_factory=dict)

    # By severity
    items_by_severity: Dict[str, int] = field(default_factory=dict)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # Quality metrics
    code_coverage: Optional[float] = None
    security_issues: int = 0
    outdated_deps: int = 0


@dataclass
class PrioritizedItem:
    """Debt item with priority score"""
    item: TechnicalDebtItem
    priority_score: float
    roi: float
    urgency: float
    impact: float


# ============================================================================
# Scanner Configurations
# ============================================================================

DEBT_TYPE_MAPPING = {
    # Ruff codes
    "E": DebtType.CODE_SMELL,      # pycodestyle errors
    "W": DebtType.CODE_SMELL,      # pycodestyle warnings
    "F": DebtType.CODE_SMELL,      # pyflakes
    "C": DebtType.CODE_SMELL,      # complexity
    "I": DebtType.CODE_SMELL,      # import order
    "N": DebtType.CODE_SMELL,      # naming
    "D": DebtType.DOCUMENTATION,   # docstring
    "S": DebtType.SECURITY,        # bandit security
    "B": DebtType.CODE_SMELL,      # bugbear
    "A": DebtType.CODE_SMELL,      # builtins
    "COM": DebtType.CODE_SMELL,    # commas
    "DTZ": DebtType.CODE_SMELL,    # datetime
    "ERA": DebtType.CODE_SMELL,    # eradicate (commented code)
    "PL": DebtType.CODE_SMELL,     # pylint
    "SIM": DebtType.CODE_SMELL,    # simplify
    "ARG": DebtType.CODE_SMELL,    # unused arguments
    "PTH": DebtType.CODE_SMELL,    # use pathlib
    "RUF": DebtType.CODE_SMELL,    # ruff-specific

    # ESLint codes
    "no-unused-vars": DebtType.CODE_SMELL,
    "no-console": DebtType.CODE_SMELL,
    "prefer-const": DebtType.CODE_SMELL,
    "security": DebtType.SECURITY,
    "complexity": DebtType.CODE_SMELL,

    # Bandit codes
    "B101": DebtType.CODE_SMELL,   # assert
    "B102": DebtType.SECURITY,     # exec
    "B103": DebtType.SECURITY,     # chmod
    "B104": DebtType.SECURITY,     # bind all interfaces
    "B105": DebtType.SECURITY,     # hardcoded password
    "B106": DebtType.SECURITY,     # hardcoded password in func arg
    "B107": DebtType.SECURITY,     # hardcoded password default
    "B108": DebtType.SECURITY,     # hardcoded tmp path
    "B110": DebtType.SECURITY,     # try except pass
    "B201": DebtType.SECURITY,     # flask debug
    "B301": DebtType.SECURITY,     # pickle
    "B303": DebtType.SECURITY,     # md5
    "B304": DebtType.SECURITY,     # des
    "B305": DebtType.SECURITY,     # cipher
    "B306": DebtType.SECURITY,     # mktemp
    "B307": DebtType.SECURITY,     # eval
    "B308": DebtType.SECURITY,     # mark_safe
    "B309": DebtType.SECURITY,     # httpsconnection
    "B310": DebtType.SECURITY,     # urllib_urlopen
    "B311": DebtType.SECURITY,     # random
    "B312": DebtType.SECURITY,     # telnet
    "B313": DebtType.SECURITY,     # xml
    "B314": DebtType.SECURITY,     # xml
    "B315": DebtType.SECURITY,     # xml
    "B316": DebtType.SECURITY,     # xml
    "B317": DebtType.SECURITY,     # xml
    "B318": DebtType.SECURITY,     # xml
    "B319": DebtType.SECURITY,     # xml
    "B320": DebtType.SECURITY,     # xml
    "B321": DebtType.SECURITY,     # ftp
    "B323": DebtType.SECURITY,     # ssl unverified
    "B324": DebtType.SECURITY,     # insecure hash
    "B401": DebtType.SECURITY,     # import telnetlib
    "B402": DebtType.SECURITY,     # import ftplib
    "B403": DebtType.SECURITY,     # import pickle
    "B404": DebtType.SECURITY,     # import subprocess
    "B405": DebtType.SECURITY,     # import xml
    "B406": DebtType.SECURITY,     # import xml
    "B407": DebtType.SECURITY,     # import xml
    "B408": DebtType.SECURITY,     # import xml
    "B409": DebtType.SECURITY,     # import xml
    "B410": DebtType.SECURITY,     # import lxml
    "B411": DebtType.SECURITY,     # import xmlrpc
    "B412": DebtType.SECURITY,     # import httpoxy
    "B413": DebtType.SECURITY,     # import pycrypto
    "B501": DebtType.SECURITY,     # request without timeout
    "B502": DebtType.SECURITY,     # ssl with bad version
    "B503": DebtType.SECURITY,     # ssl with bad default
    "B504": DebtType.SECURITY,     # ssl without version
    "B505": DebtType.SECURITY,     # weak cryptographic key
    "B506": DebtType.SECURITY,     # yaml load
    "B507": DebtType.SECURITY,     # ssh no host key verification
    "B508": DebtType.SECURITY,     # snmp weak crypto
    "B509": DebtType.SECURITY,     # snmp insecure version
    "B601": DebtType.SECURITY,     # paramiko calls
    "B602": DebtType.SECURITY,     # subprocess popen shell=True
    "B603": DebtType.SECURITY,     # subprocess without shell
    "B604": DebtType.SECURITY,     # shell cmd
    "B605": DebtType.SECURITY,     # start process with shell
    "B606": DebtType.SECURITY,     # start process with no shell
    "B607": DebtType.SECURITY,     # start process with partial path
    "B608": DebtType.SECURITY,     # hardcoded sql
    "B609": DebtType.SECURITY,     # wildcard injection
    "B610": DebtType.SECURITY,     # django extra
    "B611": DebtType.SECURITY,     # django raw html
    "B701": DebtType.SECURITY,     # jinja2 autoescape
    "B702": DebtType.SECURITY,     # mako templates
    "B703": DebtType.SECURITY,     # django mark safe
}

SEVERITY_MAPPING = {
    # High severity codes
    "B602": DebtSeverity.CRITICAL,  # shell=True
    "B608": DebtSeverity.CRITICAL,  # SQL injection
    "B307": DebtSeverity.CRITICAL,  # eval
    "B102": DebtSeverity.CRITICAL,  # exec
    "B105": DebtSeverity.HIGH,      # hardcoded password
    "B106": DebtSeverity.HIGH,
    "B107": DebtSeverity.HIGH,
    "S": DebtSeverity.HIGH,          # Security category
    "F": DebtSeverity.MEDIUM,        # Pyflakes (actual errors)
    "E": DebtSeverity.LOW,           # Style errors
    "W": DebtSeverity.LOW,           # Warnings
    "C": DebtSeverity.LOW,           # Complexity
}

# Principal estimates (hours to fix)
PRINCIPAL_ESTIMATES = {
    DebtType.CODE_SMELL: 0.5,
    DebtType.SECURITY: 2.0,
    DebtType.PERFORMANCE: 1.5,
    DebtType.DEPENDENCY: 1.0,
    DebtType.TEST_GAP: 1.0,
    DebtType.DOCUMENTATION: 0.5,
    DebtType.ARCHITECTURE: 4.0,
    DebtType.DUPLICATION: 1.0,
    DebtType.COMPATIBILITY: 1.5,
    DebtType.ACCESSIBILITY: 1.0,
}

# Interest rates (cost per sprint if not fixed)
INTEREST_RATES = {
    DebtSeverity.CRITICAL: 0.5,   # 50% of principal per sprint
    DebtSeverity.HIGH: 0.2,       # 20%
    DebtSeverity.MEDIUM: 0.1,     # 10%
    DebtSeverity.LOW: 0.05,       # 5%
}


# ============================================================================
# Technical Debt Service
# ============================================================================

class TechnicalDebtService:
    """
    Service for scanning, tracking, and managing technical debt.

    Integrates with:
    - ruff (Python linting)
    - eslint (TypeScript/JavaScript linting)
    - bandit (Python security)
    - coverage (test coverage)
    - npm audit (dependency vulnerabilities)
    """

    def __init__(self, db: AsyncSession, project_path: str = "."):
        self.db = db
        self.project_path = Path(project_path).resolve()
        self._scanner_versions: Dict[str, str] = {}

    # ========================================================================
    # Scanning
    # ========================================================================

    async def scan_codebase(
        self,
        scanners: Optional[List[str]] = None,
        project_id: Optional[int] = None,
        project_path: Optional[str] = None,
        tech_stack: Optional[List[str]] = None
    ) -> TechnicalDebtSnapshot:
        """
        Run all scanners and create a new snapshot.

        Args:
            scanners: List of scanners to run (default: auto-detect based on stack)
            project_id: Optional project ID
            project_path: Path to project to scan (default: current project)
            tech_stack: Tech stack for scanner selection (auto-detected if not provided)

        Returns:
            TechnicalDebtSnapshot with all detected items
        """
        start_time = datetime.now(timezone.utc)

        # Use specified path or default
        scan_path = Path(project_path) if project_path else self.project_path

        # Use scanner registry for stack-aware scanning
        if tech_stack or project_path:
            return await self._scan_with_registry(
                scan_path=scan_path,
                tech_stack=tech_stack,
                scanner_names=scanners,
                project_id=project_id,
                start_time=start_time
            )

        # Legacy scanning (fallback for local project)
        if scanners is None:
            scanners = ["ruff", "bandit", "coverage"]

        # Run scanners
        all_items: List[Dict[str, Any]] = []
        scan_results: Dict[str, ScanResult] = {}

        for scanner in scanners:
            if scanner == "ruff":
                result = await self._run_ruff()
            elif scanner == "bandit":
                result = await self._run_bandit()
            elif scanner == "eslint":
                result = await self._run_eslint()
            elif scanner == "coverage":
                result = await self._run_coverage()
            else:
                continue

            scan_results[scanner] = result
            if result.success:
                all_items.extend(result.items)
                if result.version:
                    self._scanner_versions[scanner] = result.version

        # Calculate duration
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Create snapshot
        snapshot = await self._create_snapshot(
            items=all_items,
            scan_results=scan_results,
            duration=duration,
            project_id=project_id
        )

        return snapshot

    async def _scan_with_registry(
        self,
        scan_path: Path,
        tech_stack: Optional[List[str]],
        scanner_names: Optional[List[str]],
        project_id: Optional[int],
        start_time: datetime
    ) -> TechnicalDebtSnapshot:
        """
        Run scans using the scanner registry for stack-aware scanning.
        """
        registry = get_scanner_registry()

        # Auto-detect stack if not provided
        if not tech_stack:
            tech_stack = self._detect_tech_stack(scan_path)

        # Run scans via registry
        registry_results = await registry.run_scan(
            project_path=str(scan_path),
            stacks=tech_stack,
            scanner_names=scanner_names
        )

        # Convert registry results to debt items
        all_items: List[Dict[str, Any]] = []
        scan_results: Dict[str, ScanResult] = {}

        for scanner_name, result in registry_results.items():
            items = []
            if result.success and result.findings:
                for finding in result.findings:
                    item = self._convert_finding_to_debt_item(finding)
                    items.append(item)
                    all_items.append(item)

            # Create ScanResult in legacy format
            source = self._get_detection_source(scanner_name)
            scan_results[scanner_name] = ScanResult(
                source=source,
                items=items,
                duration_seconds=(result.completed_at - result.started_at).total_seconds()
                    if result.completed_at and result.started_at else 0,
                success=result.success,
                error=result.error_message,
                version=result.scanner_version
            )

            if result.scanner_version:
                self._scanner_versions[scanner_name] = result.scanner_version

        # Calculate duration
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Create snapshot
        snapshot = await self._create_snapshot(
            items=all_items,
            scan_results=scan_results,
            duration=duration,
            project_id=project_id
        )

        return snapshot

    def _detect_tech_stack(self, path: Path) -> List[str]:
        """Auto-detect tech stack from project files"""
        stacks = []

        # Python
        if list(path.glob("*.py")) or list(path.glob("**/*.py")):
            stacks.append("python")

        # .NET
        if list(path.glob("*.csproj")) or list(path.glob("**/*.csproj")):
            stacks.append("dotnet")
            stacks.append("csharp")
        if list(path.glob("*.vbproj")) or list(path.glob("**/*.vbproj")):
            stacks.append("vbnet")
        if list(path.glob("**/*.aspx")) or list(path.glob("**/*.asp")):
            stacks.append("aspnet")

        # JavaScript/TypeScript
        if (path / "package.json").exists():
            stacks.append("node")
        if list(path.glob("**/*.ts")) or list(path.glob("**/*.tsx")):
            stacks.append("typescript")
        if list(path.glob("**/*.js")) or list(path.glob("**/*.jsx")):
            stacks.append("javascript")

        return list(set(stacks)) if stacks else ["generic"]

    def _get_detection_source(self, scanner_name: str) -> DetectionSource:
        """Map scanner name to DetectionSource enum"""
        mapping = {
            "ruff": DetectionSource.SCANNER_RUFF,
            "bandit": DetectionSource.SCANNER_BANDIT,
            "eslint": DetectionSource.SCANNER_ESLINT,
            "radon": DetectionSource.SCANNER_RUFF,  # Complexity
            "dotnet-volume": DetectionSource.MANUAL,
            "dotnet-duplication": DetectionSource.MANUAL,
        }
        return mapping.get(scanner_name, DetectionSource.MANUAL)

    def _convert_finding_to_debt_item(self, finding: ScanFinding) -> Dict[str, Any]:
        """Convert a ScanFinding to the debt item format"""
        # Map severity
        severity_map = {
            Severity.CRITICAL: DebtSeverity.CRITICAL,
            Severity.HIGH: DebtSeverity.HIGH,
            Severity.MEDIUM: DebtSeverity.MEDIUM,
            Severity.LOW: DebtSeverity.LOW,
            Severity.INFO: DebtSeverity.LOW,
        }
        severity = severity_map.get(finding.severity, DebtSeverity.MEDIUM)

        # Map finding type to debt type
        type_map = {
            FindingType.CODE_SMELL: DebtType.CODE_SMELL,
            FindingType.SECURITY: DebtType.SECURITY,
            FindingType.PERFORMANCE: DebtType.PERFORMANCE,
            FindingType.COMPLEXITY: DebtType.CODE_SMELL,
            FindingType.DUPLICATION: DebtType.DUPLICATION,
            FindingType.DEPENDENCY: DebtType.DEPENDENCY,
            FindingType.TEST_GAP: DebtType.TEST_GAP,
            FindingType.DOCUMENTATION: DebtType.DOCUMENTATION,
        }
        debt_type = type_map.get(finding.finding_type, DebtType.CODE_SMELL)

        # Get detection source
        detection_source = self._get_detection_source(finding.scanner)

        return {
            "title": f"{finding.rule_id}: {finding.message[:100] if finding.message else 'Issue found'}",
            "description": finding.message,
            "debt_type": debt_type.value,  # Use .value for asyncpg compatibility
            "severity": severity.value,    # Use .value for asyncpg compatibility
            "file_path": finding.file_path,
            "line_start": finding.line_number,
            "line_end": finding.end_line,
            "detected_by": detection_source.value if hasattr(detection_source, 'value') else detection_source,
            "detection_rule": finding.rule_id,
            "detection_message": finding.message,
            "principal": PRINCIPAL_ESTIMATES.get(debt_type, 0.5),
            "interest_rate": INTEREST_RATES.get(severity, 0.1),
        }

    async def _run_ruff(self) -> ScanResult:
        """Run ruff linter on Python files"""
        start_time = datetime.now(timezone.utc)
        items = []

        try:
            # Get version
            version_result = subprocess.run(
                ["ruff", "--version"],
                capture_output=True,
                text=True,
                cwd=str(self.project_path)
            )
            version = version_result.stdout.strip() if version_result.returncode == 0 else None

            # Run ruff
            result = subprocess.run(
                ["ruff", "check", ".", "--output-format", "json", "--ignore", "E501"],
                capture_output=True,
                text=True,
                cwd=str(self.project_path)
            )

            if result.stdout:
                findings = json.loads(result.stdout)
                for finding in findings:
                    items.append(self._parse_ruff_finding(finding))

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            return ScanResult(
                source=DetectionSource.SCANNER_RUFF,
                items=items,
                duration_seconds=duration,
                success=True,
                version=version
            )

        except FileNotFoundError:
            return ScanResult(
                source=DetectionSource.SCANNER_RUFF,
                items=[],
                duration_seconds=0,
                success=False,
                error="ruff not installed"
            )
        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            return ScanResult(
                source=DetectionSource.SCANNER_RUFF,
                items=[],
                duration_seconds=duration,
                success=False,
                error=str(e)
            )

    def _parse_ruff_finding(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a ruff finding into debt item format"""
        code = finding.get("code", "")
        code_prefix = re.match(r"^([A-Z]+)", code)
        prefix = code_prefix.group(1) if code_prefix else "E"

        debt_type = DEBT_TYPE_MAPPING.get(prefix, DebtType.CODE_SMELL)
        severity = self._determine_severity(code, debt_type)

        return {
            "title": f"{code}: {finding.get('message', 'Unknown issue')}",
            "description": finding.get("message"),
            "debt_type": debt_type,
            "severity": severity,
            "file_path": finding.get("filename"),
            "line_start": finding.get("location", {}).get("row"),
            "line_end": finding.get("end_location", {}).get("row"),
            "detected_by": DetectionSource.SCANNER_RUFF,
            "detection_rule": code,
            "detection_message": finding.get("message"),
            "principal": PRINCIPAL_ESTIMATES.get(debt_type, 0.5),
            "interest_rate": INTEREST_RATES.get(severity, 0.1),
        }

    async def _run_bandit(self) -> ScanResult:
        """Run bandit security scanner on Python files"""
        start_time = datetime.now(timezone.utc)
        items = []

        try:
            # Get version
            version_result = subprocess.run(
                ["bandit", "--version"],
                capture_output=True,
                text=True
            )
            version = version_result.stdout.split('\n')[0] if version_result.returncode == 0 else None

            # Run bandit
            result = subprocess.run(
                ["bandit", "-r", ".", "-f", "json", "-q", "--exclude", ".venv,node_modules"],
                capture_output=True,
                text=True,
                cwd=str(self.project_path)
            )

            if result.stdout:
                data = json.loads(result.stdout)
                for finding in data.get("results", []):
                    items.append(self._parse_bandit_finding(finding))

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            return ScanResult(
                source=DetectionSource.SCANNER_BANDIT,
                items=items,
                duration_seconds=duration,
                success=True,
                version=version
            )

        except FileNotFoundError:
            return ScanResult(
                source=DetectionSource.SCANNER_BANDIT,
                items=[],
                duration_seconds=0,
                success=False,
                error="bandit not installed"
            )
        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            return ScanResult(
                source=DetectionSource.SCANNER_BANDIT,
                items=[],
                duration_seconds=duration,
                success=False,
                error=str(e)
            )

    def _parse_bandit_finding(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a bandit finding into debt item format"""
        test_id = finding.get("test_id", "")

        # Map severity
        bandit_severity = finding.get("issue_severity", "MEDIUM")
        if bandit_severity == "HIGH":
            severity = DebtSeverity.CRITICAL
        elif bandit_severity == "MEDIUM":
            severity = DebtSeverity.HIGH
        else:
            severity = DebtSeverity.MEDIUM

        return {
            "title": f"{test_id}: {finding.get('issue_text', 'Security issue')}",
            "description": finding.get("issue_text"),
            "debt_type": DebtType.SECURITY,
            "severity": severity,
            "file_path": finding.get("filename"),
            "line_start": finding.get("line_number"),
            "line_end": finding.get("line_number"),
            "detected_by": DetectionSource.SCANNER_BANDIT,
            "detection_rule": test_id,
            "detection_message": finding.get("issue_text"),
            "principal": PRINCIPAL_ESTIMATES.get(DebtType.SECURITY, 2.0),
            "interest_rate": INTEREST_RATES.get(severity, 0.2),
            "metadata": {
                "confidence": finding.get("issue_confidence"),
                "cwe": finding.get("issue_cwe", {}).get("id"),
                "more_info": finding.get("more_info")
            }
        }

    async def _run_eslint(self) -> ScanResult:
        """Run ESLint on TypeScript/JavaScript files"""
        start_time = datetime.now(timezone.utc)
        items = []

        # Check if there's a TypeScript/JS project
        ts_path = self.project_path / "agents"
        if not ts_path.exists():
            return ScanResult(
                source=DetectionSource.SCANNER_ESLINT,
                items=[],
                duration_seconds=0,
                success=True,
                error="No TypeScript project found"
            )

        try:
            result = subprocess.run(
                ["npx", "eslint", ".", "--format", "json", "--ext", ".ts,.tsx,.js,.jsx"],
                capture_output=True,
                text=True,
                cwd=str(ts_path)
            )

            if result.stdout:
                data = json.loads(result.stdout)
                for file_result in data:
                    for message in file_result.get("messages", []):
                        items.append(self._parse_eslint_finding(
                            file_result.get("filePath"),
                            message
                        ))

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            return ScanResult(
                source=DetectionSource.SCANNER_ESLINT,
                items=items,
                duration_seconds=duration,
                success=True
            )

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            return ScanResult(
                source=DetectionSource.SCANNER_ESLINT,
                items=[],
                duration_seconds=duration,
                success=False,
                error=str(e)
            )

    def _parse_eslint_finding(self, file_path: str, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Parse an ESLint finding into debt item format"""
        rule_id = finding.get("ruleId", "")
        eslint_severity = finding.get("severity", 1)

        if eslint_severity == 2:
            severity = DebtSeverity.HIGH
        else:
            severity = DebtSeverity.MEDIUM

        # Check for security rules
        debt_type = DebtType.CODE_SMELL
        if "security" in rule_id.lower():
            debt_type = DebtType.SECURITY
            severity = DebtSeverity.HIGH

        return {
            "title": f"{rule_id}: {finding.get('message', 'ESLint issue')}",
            "description": finding.get("message"),
            "debt_type": debt_type,
            "severity": severity,
            "file_path": file_path,
            "line_start": finding.get("line"),
            "line_end": finding.get("endLine") or finding.get("line"),
            "detected_by": DetectionSource.SCANNER_ESLINT,
            "detection_rule": rule_id,
            "detection_message": finding.get("message"),
            "principal": PRINCIPAL_ESTIMATES.get(debt_type, 0.5),
            "interest_rate": INTEREST_RATES.get(severity, 0.1),
        }

    async def _run_coverage(self) -> ScanResult:
        """Get test coverage metrics"""
        start_time = datetime.now(timezone.utc)
        items = []

        try:
            # Try to read existing coverage report
            coverage_file = self.project_path / ".coverage"
            coverage_json = self.project_path / "coverage.json"

            if coverage_json.exists():
                with open(coverage_json) as f:
                    data = json.load(f)

                # Find files with low coverage
                for file_path, file_data in data.get("files", {}).items():
                    coverage_pct = file_data.get("summary", {}).get("percent_covered", 100)

                    if coverage_pct < 80:  # Below threshold
                        severity = DebtSeverity.LOW
                        if coverage_pct < 50:
                            severity = DebtSeverity.MEDIUM
                        if coverage_pct < 20:
                            severity = DebtSeverity.HIGH

                        items.append({
                            "title": f"Low test coverage: {coverage_pct:.1f}%",
                            "description": f"File {file_path} has only {coverage_pct:.1f}% test coverage",
                            "debt_type": DebtType.TEST_GAP,
                            "severity": severity,
                            "file_path": file_path,
                            "detected_by": DetectionSource.SCANNER_COVERAGE,
                            "detection_rule": "coverage_threshold",
                            "principal": PRINCIPAL_ESTIMATES.get(DebtType.TEST_GAP, 1.0),
                            "interest_rate": INTEREST_RATES.get(severity, 0.1),
                            "metadata": {
                                "coverage_percent": coverage_pct,
                                "missing_lines": file_data.get("missing_lines", [])
                            }
                        })

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            return ScanResult(
                source=DetectionSource.SCANNER_COVERAGE,
                items=items,
                duration_seconds=duration,
                success=True
            )

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            return ScanResult(
                source=DetectionSource.SCANNER_COVERAGE,
                items=[],
                duration_seconds=duration,
                success=False,
                error=str(e)
            )

    def _determine_severity(self, code: str, debt_type: DebtType) -> DebtSeverity:
        """Determine severity based on code and type"""
        # Check specific code mappings
        if code in SEVERITY_MAPPING:
            return SEVERITY_MAPPING[code]

        # Check code prefix
        prefix = re.match(r"^([A-Z]+)", code)
        if prefix and prefix.group(1) in SEVERITY_MAPPING:
            return SEVERITY_MAPPING[prefix.group(1)]

        # Default based on type
        if debt_type == DebtType.SECURITY:
            return DebtSeverity.HIGH
        elif debt_type == DebtType.PERFORMANCE:
            return DebtSeverity.MEDIUM
        else:
            return DebtSeverity.LOW

    # ========================================================================
    # Snapshot Creation
    # ========================================================================

    async def _create_snapshot(
        self,
        items: List[Dict[str, Any]],
        scan_results: Dict[str, ScanResult],
        duration: float,
        project_id: Optional[int] = None
    ) -> TechnicalDebtSnapshot:
        """Create a snapshot from scan results"""

        # Calculate metrics
        metrics = self._calculate_metrics(items)

        # Get previous snapshot for delta calculation
        previous = await self._get_latest_snapshot(project_id)

        # Calculate deltas
        items_delta = metrics.total_items - (previous.total_items if previous else 0)
        principal_delta = metrics.total_principal - (previous.total_principal if previous else 0)
        ratio_delta = metrics.debt_ratio - (previous.debt_ratio if previous else 0)

        # Create snapshot
        snapshot = TechnicalDebtSnapshot(
            scan_duration_seconds=duration,
            total_items=metrics.total_items,
            total_principal=metrics.total_principal,
            total_interest=metrics.total_interest,
            debt_ratio=metrics.debt_ratio,
            items_by_type=metrics.items_by_type,
            principal_by_type=metrics.principal_by_type,
            items_by_severity=metrics.items_by_severity,
            critical_count=metrics.critical_count,
            high_count=metrics.high_count,
            medium_count=metrics.medium_count,
            low_count=metrics.low_count,
            code_coverage=metrics.code_coverage,
            security_issues=metrics.security_issues,
            items_delta=items_delta,
            principal_delta=principal_delta,
            ratio_delta=ratio_delta,
            project_id=project_id,
            trigger="scan",
            scanner_versions=self._scanner_versions
        )

        self.db.add(snapshot)
        await self.db.flush()

        # Create debt items
        for item_data in items:
            # Helper function to get enum value as string (for asyncpg compatibility)
            def get_enum_value(value, enum_class, default_value: str) -> str:
                """Convert any enum representation to its string value"""
                if isinstance(value, enum_class):
                    return value.value
                if isinstance(value, str):
                    # Already a string - normalize to lowercase
                    val_lower = value.lower()
                    # Check if it's a valid value
                    for member in enum_class:
                        if member.value == val_lower:
                            return member.value
                        if member.name.lower() == val_lower or member.name == value:
                            return member.value
                    # If it looks like a valid value, use it
                    if val_lower in [m.value for m in enum_class]:
                        return val_lower
                return default_value

            debt_type_val = get_enum_value(item_data["debt_type"], DebtType, "code_smell")
            severity_val = get_enum_value(item_data["severity"], DebtSeverity, "medium")
            detected_by_val = get_enum_value(item_data.get("detected_by", "manual"), DetectionSource, "manual")

            debt_item = TechnicalDebtItem(
                title=item_data["title"],
                description=item_data.get("description"),
                debt_type=debt_type_val,
                severity=severity_val,
                file_path=item_data.get("file_path"),
                line_start=item_data.get("line_start"),
                line_end=item_data.get("line_end"),
                detected_by=detected_by_val,
                detection_rule=item_data.get("detection_rule"),
                detection_message=item_data.get("detection_message"),
                principal=item_data.get("principal", 0.5),
                interest_rate=item_data.get("interest_rate", 0.1),
                project_id=project_id,
                snapshot_id=snapshot.id,
                metadata=item_data.get("metadata", {})
            )
            self.db.add(debt_item)

        await self.db.commit()
        await self.db.refresh(snapshot)

        return snapshot

    def _calculate_metrics(self, items: List[Dict[str, Any]]) -> DebtMetrics:
        """Calculate aggregate metrics from items"""
        metrics = DebtMetrics()

        for item in items:
            metrics.total_items += 1

            principal = item.get("principal", 0.5)
            metrics.total_principal += principal

            interest_rate = item.get("interest_rate", 0.1)
            metrics.total_interest += principal * interest_rate

            # By type
            debt_type = item["debt_type"]
            type_key = debt_type.value if isinstance(debt_type, DebtType) else str(debt_type)
            metrics.items_by_type[type_key] = metrics.items_by_type.get(type_key, 0) + 1
            metrics.principal_by_type[type_key] = metrics.principal_by_type.get(type_key, 0) + principal

            # By severity
            severity = item["severity"]
            sev_key = severity.value if isinstance(severity, DebtSeverity) else str(severity)
            metrics.items_by_severity[sev_key] = metrics.items_by_severity.get(sev_key, 0) + 1

            if severity == DebtSeverity.CRITICAL or sev_key == "critical":
                metrics.critical_count += 1
            elif severity == DebtSeverity.HIGH or sev_key == "high":
                metrics.high_count += 1
            elif severity == DebtSeverity.MEDIUM or sev_key == "medium":
                metrics.medium_count += 1
            else:
                metrics.low_count += 1

            # Security issues
            if debt_type == DebtType.SECURITY or type_key == "security":
                metrics.security_issues += 1

        # Calculate TDR (assuming 160 productive hours per sprint)
        productive_hours = 160.0
        metrics.debt_ratio = (metrics.total_principal / productive_hours) * 100

        return metrics

    async def _get_latest_snapshot(
        self,
        project_id: Optional[int] = None
    ) -> Optional[TechnicalDebtSnapshot]:
        """Get the most recent snapshot"""
        query = select(TechnicalDebtSnapshot).order_by(
            TechnicalDebtSnapshot.timestamp.desc()
        )

        if project_id:
            query = query.where(TechnicalDebtSnapshot.project_id == project_id)

        result = await self.db.execute(query.limit(1))
        return result.scalar_one_or_none()

    # ========================================================================
    # Prioritization
    # ========================================================================

    async def prioritize_debt(
        self,
        project_id: Optional[int] = None,
        max_hours: Optional[float] = None,
        focus_types: Optional[List[DebtType]] = None,
        limit: int = 20
    ) -> List[PrioritizedItem]:
        """
        Prioritize debt items for remediation.

        Uses a scoring formula:
        priority = (ROI * 0.4) + (urgency * 0.3) + (impact * 0.3)

        Where:
        - ROI = interest saved per hour invested
        - Urgency = based on severity
        - Impact = based on debt type importance
        """
        # Get open debt items
        query = select(TechnicalDebtItem).where(
            TechnicalDebtItem.status.in_([DebtStatus.OPEN, DebtStatus.ACKNOWLEDGED])
        )

        if project_id:
            query = query.where(TechnicalDebtItem.project_id == project_id)

        if focus_types:
            query = query.where(TechnicalDebtItem.debt_type.in_(focus_types))

        result = await self.db.execute(query)
        items = result.scalars().all()

        # Calculate priority scores
        prioritized = []
        for item in items:
            roi = item.calculate_roi()
            urgency = self._calculate_urgency(item)
            impact = self._calculate_impact(item)

            priority_score = (roi * 0.4) + (urgency * 0.3) + (impact * 0.3)

            prioritized.append(PrioritizedItem(
                item=item,
                priority_score=priority_score,
                roi=roi,
                urgency=urgency,
                impact=impact
            ))

        # Sort by priority
        prioritized.sort(key=lambda x: x.priority_score, reverse=True)

        # Apply budget constraint
        if max_hours:
            result = []
            total_hours = 0
            for p in prioritized:
                if total_hours + p.item.principal <= max_hours:
                    result.append(p)
                    total_hours += p.item.principal
            return result[:limit]

        return prioritized[:limit]

    def _calculate_urgency(self, item: TechnicalDebtItem) -> float:
        """Calculate urgency score (0-1) based on severity"""
        urgency_map = {
            DebtSeverity.CRITICAL: 1.0,
            DebtSeverity.HIGH: 0.75,
            DebtSeverity.MEDIUM: 0.5,
            DebtSeverity.LOW: 0.25
        }
        return urgency_map.get(item.severity, 0.5)

    def _calculate_impact(self, item: TechnicalDebtItem) -> float:
        """Calculate impact score (0-1) based on debt type"""
        impact_map = {
            DebtType.SECURITY: 1.0,
            DebtType.ARCHITECTURE: 0.9,
            DebtType.PERFORMANCE: 0.8,
            DebtType.TEST_GAP: 0.7,
            DebtType.DEPENDENCY: 0.6,
            DebtType.CODE_SMELL: 0.5,
            DebtType.DUPLICATION: 0.4,
            DebtType.DOCUMENTATION: 0.3,
            DebtType.COMPATIBILITY: 0.5,
            DebtType.ACCESSIBILITY: 0.5
        }
        return impact_map.get(item.debt_type, 0.5)

    # ========================================================================
    # Remediation Plans
    # ========================================================================

    async def create_remediation_plan(
        self,
        name: str,
        target_debt_ratio: Optional[float] = None,
        max_effort_hours: Optional[float] = None,
        focus_types: Optional[List[DebtType]] = None,
        project_id: Optional[int] = None
    ) -> RemediationPlan:
        """
        Create a remediation plan based on prioritized debt items.

        Args:
            name: Plan name
            target_debt_ratio: Target TDR to achieve
            max_effort_hours: Maximum hours to allocate
            focus_types: Types of debt to focus on
            project_id: Project ID
        """
        # Get prioritized items
        prioritized = await self.prioritize_debt(
            project_id=project_id,
            max_hours=max_effort_hours,
            focus_types=focus_types,
            limit=50
        )

        if not prioritized:
            raise ValueError("No debt items found for remediation")

        # Calculate plan metrics
        item_ids = [p.item.id for p in prioritized]
        total_effort = sum(p.item.principal for p in prioritized)
        total_interest = sum(p.item.calculate_interest() for p in prioritized)

        # Get latest snapshot for ratio calculation
        snapshot = await self._get_latest_snapshot(project_id)
        current_ratio = snapshot.debt_ratio if snapshot else 0

        # Estimate ratio reduction
        if snapshot and snapshot.total_principal > 0:
            ratio_reduction = (total_effort / snapshot.total_principal) * current_ratio
        else:
            ratio_reduction = 0

        # Create plan
        plan = RemediationPlan(
            name=name,
            description=f"Auto-generated plan targeting {len(prioritized)} debt items",
            status="draft",
            target_debt_ratio=target_debt_ratio,
            max_effort_hours=max_effort_hours,
            priority_types=[t.value for t in focus_types] if focus_types else [],
            item_ids=item_ids,
            total_items=len(item_ids),
            total_effort_hours=total_effort,
            estimated_interest_saved=total_interest,
            estimated_ratio_reduction=ratio_reduction,
            assigned_agent="marcus",
            project_id=project_id,
            snapshot_id=snapshot.id if snapshot else None
        )

        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)

        # Update item statuses
        for item_id in item_ids:
            await self.db.execute(
                select(TechnicalDebtItem)
                .where(TechnicalDebtItem.id == item_id)
            )

        result = await self.db.execute(
            select(TechnicalDebtItem)
            .where(TechnicalDebtItem.id.in_(item_ids))
        )
        items = result.scalars().all()
        for item in items:
            item.status = DebtStatus.PLANNED

        await self.db.commit()

        return plan

    async def get_remediation_plan(self, plan_id: int) -> Optional[RemediationPlan]:
        """Get a remediation plan by ID"""
        result = await self.db.execute(
            select(RemediationPlan).where(RemediationPlan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def update_plan_progress(
        self,
        plan_id: int,
        resolved_item_id: int,
        actual_hours: float
    ) -> RemediationPlan:
        """Update plan progress when an item is resolved"""
        plan = await self.get_remediation_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        # Get the resolved item
        result = await self.db.execute(
            select(TechnicalDebtItem).where(TechnicalDebtItem.id == resolved_item_id)
        )
        item = result.scalar_one_or_none()

        if item:
            plan.items_completed += 1
            plan.effort_spent_hours += actual_hours
            plan.actual_interest_saved += item.calculate_interest()

        # Check if plan is complete
        if plan.items_completed >= plan.total_items:
            plan.status = "completed"
            plan.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(plan)

        return plan

    # ========================================================================
    # Resolution Tracking
    # ========================================================================

    async def resolve_debt_item(
        self,
        item_id: int,
        resolution_type: str,
        resolved_by_agent: Optional[str] = None,
        resolved_by_human: Optional[str] = None,
        actual_hours: Optional[float] = None,
        commit_hash: Optional[str] = None,
        pr_number: Optional[int] = None,
        notes: Optional[str] = None
    ) -> DebtResolution:
        """Record resolution of a debt item"""
        # Get the item
        result = await self.db.execute(
            select(TechnicalDebtItem).where(TechnicalDebtItem.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            raise ValueError(f"Debt item {item_id} not found")

        # Create resolution record
        resolution = DebtResolution(
            debt_item_id=item_id,
            resolution_type=resolution_type,
            resolution_notes=notes,
            resolved_by_agent=resolved_by_agent,
            resolved_by_human=resolved_by_human,
            estimated_hours=item.principal,
            actual_hours=actual_hours or item.principal,
            commit_hash=commit_hash,
            pr_number=pr_number,
            interest_eliminated=item.calculate_interest()
        )

        self.db.add(resolution)

        # Update item status
        item.status = DebtStatus.RESOLVED
        item.resolved_at = datetime.now(timezone.utc)
        item.resolved_by = resolved_by_agent or resolved_by_human
        item.resolution_notes = notes
        item.resolution_commit = commit_hash

        await self.db.commit()
        await self.db.refresh(resolution)

        return resolution

    # ========================================================================
    # Quality Gates
    # ========================================================================

    async def check_quality_gates(
        self,
        commit_hash: Optional[str] = None,
        branch: Optional[str] = None,
        pr_number: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> QualityGateResult:
        """
        Run quality gate checks and determine pass/fail.

        Gates:
        - Tests must pass (100%)
        - Coverage must be >= 80%
        - No critical security issues
        - Debt ratio must be < 10%
        """
        start_time = datetime.now(timezone.utc)

        # Run a quick scan
        snapshot = await self.scan_codebase(
            scanners=["ruff", "bandit"],
            project_id=project_id
        )

        # Define gate thresholds
        gates = {
            "tests": {"threshold": 100, "score": 100},  # Placeholder
            "coverage": {"threshold": 80, "score": snapshot.code_coverage or 0},
            "security": {"threshold": 0, "score": snapshot.security_issues},
            "debt_ratio": {"threshold": 10, "score": snapshot.debt_ratio}
        }

        # Evaluate each gate
        gate_results = {}
        failure_reasons = []
        blocking_issues = []
        passed = True

        for gate_name, gate_config in gates.items():
            threshold = gate_config["threshold"]
            score = gate_config["score"]

            if gate_name == "security":
                # Security: lower is better
                gate_passed = score <= threshold
            elif gate_name == "debt_ratio":
                # Debt ratio: lower is better
                gate_passed = score <= threshold
            else:
                # Coverage/tests: higher is better
                gate_passed = score >= threshold

            gate_results[gate_name] = {
                "passed": gate_passed,
                "score": score,
                "threshold": threshold
            }

            if not gate_passed:
                passed = False
                failure_reasons.append(f"{gate_name}: {score} {'>' if gate_name in ['security', 'debt_ratio'] else '<'} {threshold}")

                if gate_name == "security" and score > 0:
                    blocking_issues.append(f"{score} security issues found")

        # Create result
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        result = QualityGateResult(
            trigger="check",
            commit_hash=commit_hash,
            branch=branch,
            pr_number=pr_number,
            passed=passed,
            blocked=not passed and len(blocking_issues) > 0,
            gate_results=gate_results,
            coverage_score=snapshot.code_coverage,
            security_score=float(snapshot.security_issues),
            debt_ratio_score=snapshot.debt_ratio,
            failure_reasons=failure_reasons,
            blocking_issues=blocking_issues,
            project_id=project_id,
            snapshot_id=snapshot.id,
            duration_seconds=duration
        )

        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)

        return result

    # ========================================================================
    # Analytics & Trends
    # ========================================================================

    async def get_debt_trend(
        self,
        days: int = 30,
        project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get debt metrics trend over time"""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        query = select(TechnicalDebtSnapshot).where(
            TechnicalDebtSnapshot.timestamp >= since
        ).order_by(TechnicalDebtSnapshot.timestamp)

        if project_id:
            query = query.where(TechnicalDebtSnapshot.project_id == project_id)

        result = await self.db.execute(query)
        snapshots = result.scalars().all()

        return [
            {
                "timestamp": s.timestamp.isoformat(),
                "total_items": s.total_items,
                "total_principal": s.total_principal,
                "debt_ratio": s.debt_ratio,
                "critical_count": s.critical_count,
                "security_issues": s.security_issues
            }
            for s in snapshots
        ]

    async def get_debt_summary(
        self,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get current debt summary"""
        snapshot = await self._get_latest_snapshot(project_id)

        if not snapshot:
            return {
                "total_items": 0,
                "total_principal": 0.0,
                "total_interest": 0.0,
                "debt_ratio": 0.0,
                "critical_count": 0,
                "high_count": 0,
                "security_issues": 0,
                "items_delta": 0,
                "ratio_delta": 0.0,
                "resolved_last_30_days": 0,
                "last_scan": None,
                "status": "no_data"
            }

        # Get resolution stats
        resolved_query = select(func.count(DebtResolution.id)).where(
            DebtResolution.completed_at >= datetime.now(timezone.utc) - timedelta(days=30)
        )
        resolved_result = await self.db.execute(resolved_query)
        resolved_count = resolved_result.scalar() or 0

        return {
            "total_items": snapshot.total_items,
            "total_principal": snapshot.total_principal,
            "total_interest": snapshot.total_interest,
            "debt_ratio": snapshot.debt_ratio,
            "critical_count": snapshot.critical_count,
            "high_count": snapshot.high_count,
            "security_issues": snapshot.security_issues,
            "items_delta": snapshot.items_delta,
            "ratio_delta": snapshot.ratio_delta,
            "resolved_last_30_days": resolved_count,
            "last_scan": snapshot.timestamp.isoformat() if snapshot.timestamp else None,
            "status": "healthy" if snapshot.debt_ratio < 10 else "warning" if snapshot.debt_ratio < 20 else "critical"
        }


# ============================================================================
# Service Factory
# ============================================================================

def get_technical_debt_service(db: AsyncSession, project_path: str = ".") -> TechnicalDebtService:
    """Factory function to get TechnicalDebtService instance"""
    return TechnicalDebtService(db, project_path)
