"""
Python Scanners

Implements scanners for Python codebases:
- RuffScanner: Fast Python linter (replaces flake8, pylint)
- BanditScanner: Security vulnerability scanner
- RadonScanner: Cyclomatic complexity analyzer
"""

import subprocess
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import shutil

from ..base import (
    BaseScanner, ScanResult, ScanFinding, ScanMetrics,
    Severity, FindingType
)

logger = logging.getLogger(__name__)


class RuffScanner(BaseScanner):
    """
    Ruff - An extremely fast Python linter.

    Replaces Flake8, isort, pyupgrade, and many other tools.
    """

    # Ruff severity mapping
    SEVERITY_MAP = {
        'E': Severity.HIGH,      # Error
        'W': Severity.MEDIUM,    # Warning
        'F': Severity.HIGH,      # Pyflakes
        'C': Severity.LOW,       # Convention
        'I': Severity.LOW,       # Import sorting
        'N': Severity.LOW,       # Naming
        'D': Severity.LOW,       # Docstring
        'UP': Severity.LOW,      # Pyupgrade
        'B': Severity.MEDIUM,    # Bugbear
        'A': Severity.LOW,       # Builtins
        'COM': Severity.LOW,     # Commas
        'S': Severity.HIGH,      # Security (bandit rules)
    }

    @property
    def name(self) -> str:
        return "ruff"

    @property
    def version(self) -> str:
        try:
            result = subprocess.run(
                ['ruff', '--version'],
                capture_output=True,
                text=True
            )
            return result.stdout.strip().replace('ruff ', '')
        except Exception:
            return "unknown"

    @property
    def supported_stacks(self) -> List[str]:
        return ['python', 'django', 'flask', 'fastapi']

    @property
    def scanner_type(self) -> str:
        return "linter"

    def is_available(self) -> bool:
        return shutil.which('ruff') is not None

    def _get_severity(self, code: str) -> Severity:
        """Map ruff error code to severity"""
        for prefix, severity in self.SEVERITY_MAP.items():
            if code.startswith(prefix):
                return severity
        return Severity.MEDIUM

    async def scan(self) -> ScanResult:
        """Execute ruff scan"""
        started_at = datetime.now()
        findings: List[ScanFinding] = []

        if not self.is_available():
            return ScanResult(
                scanner_name=self.name,
                scanner_version=self.version,
                stack="python",
                project_path=str(self.project_path),
                started_at=started_at,
                completed_at=datetime.now(),
                success=False,
                error_message="ruff is not installed"
            )

        try:
            result = subprocess.run(
                ['ruff', 'check', '--output-format=json', str(self.project_path)],
                capture_output=True,
                text=True,
                cwd=str(self.project_path)
            )

            # Parse output
            if result.stdout:
                issues = json.loads(result.stdout)
                for issue in issues:
                    findings.append(ScanFinding(
                        scanner=self.name,
                        rule_id=issue.get('code', 'unknown'),
                        message=issue.get('message', ''),
                        severity=self._get_severity(issue.get('code', '')),
                        finding_type=FindingType.CODE_SMELL if not issue.get('code', '').startswith('S') else FindingType.SECURITY,
                        file_path=issue.get('filename', ''),
                        line_number=issue.get('location', {}).get('row'),
                        column=issue.get('location', {}).get('column'),
                        end_line=issue.get('end_location', {}).get('row'),
                        end_column=issue.get('end_location', {}).get('column')
                    ))

            return ScanResult(
                scanner_name=self.name,
                scanner_version=self.version,
                stack="python",
                project_path=str(self.project_path),
                started_at=started_at,
                completed_at=datetime.now(),
                success=True,
                findings=findings
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ruff output: {e}")
            return ScanResult(
                scanner_name=self.name,
                scanner_version=self.version,
                stack="python",
                project_path=str(self.project_path),
                started_at=started_at,
                completed_at=datetime.now(),
                success=False,
                error_message=f"Failed to parse ruff output: {e}"
            )
        except Exception as e:
            logger.error(f"Ruff scan failed: {e}")
            return ScanResult(
                scanner_name=self.name,
                scanner_version=self.version,
                stack="python",
                project_path=str(self.project_path),
                started_at=started_at,
                completed_at=datetime.now(),
                success=False,
                error_message=str(e)
            )


class BanditScanner(BaseScanner):
    """
    Bandit - Python security linter.

    Finds common security issues in Python code.
    """

    SEVERITY_MAP = {
        'HIGH': Severity.CRITICAL,
        'MEDIUM': Severity.HIGH,
        'LOW': Severity.MEDIUM
    }

    @property
    def name(self) -> str:
        return "bandit"

    @property
    def version(self) -> str:
        try:
            result = subprocess.run(
                ['bandit', '--version'],
                capture_output=True,
                text=True
            )
            # Parse "bandit 1.7.5"
            return result.stdout.strip().split()[-1]
        except Exception:
            return "unknown"

    @property
    def supported_stacks(self) -> List[str]:
        return ['python', 'django', 'flask', 'fastapi']

    @property
    def scanner_type(self) -> str:
        return "security"

    def is_available(self) -> bool:
        return shutil.which('bandit') is not None

    async def scan(self) -> ScanResult:
        """Execute bandit scan"""
        started_at = datetime.now()
        findings: List[ScanFinding] = []

        if not self.is_available():
            return ScanResult(
                scanner_name=self.name,
                scanner_version=self.version,
                stack="python",
                project_path=str(self.project_path),
                started_at=started_at,
                completed_at=datetime.now(),
                success=False,
                error_message="bandit is not installed"
            )

        try:
            result = subprocess.run(
                ['bandit', '-r', '-f', 'json', str(self.project_path)],
                capture_output=True,
                text=True,
                cwd=str(self.project_path)
            )

            # Parse output
            if result.stdout:
                data = json.loads(result.stdout)

                for issue in data.get('results', []):
                    findings.append(ScanFinding(
                        scanner=self.name,
                        rule_id=issue.get('test_id', 'unknown'),
                        message=issue.get('issue_text', ''),
                        severity=self.SEVERITY_MAP.get(issue.get('issue_severity', ''), Severity.MEDIUM),
                        finding_type=FindingType.SECURITY,
                        file_path=issue.get('filename', ''),
                        line_number=issue.get('line_number'),
                        code_snippet=issue.get('code', ''),
                        metadata={
                            'confidence': issue.get('issue_confidence'),
                            'cwe': issue.get('issue_cwe', {})
                        }
                    ))

            return ScanResult(
                scanner_name=self.name,
                scanner_version=self.version,
                stack="python",
                project_path=str(self.project_path),
                started_at=started_at,
                completed_at=datetime.now(),
                success=True,
                findings=findings
            )

        except Exception as e:
            logger.error(f"Bandit scan failed: {e}")
            return ScanResult(
                scanner_name=self.name,
                scanner_version=self.version,
                stack="python",
                project_path=str(self.project_path),
                started_at=started_at,
                completed_at=datetime.now(),
                success=False,
                error_message=str(e)
            )


class RadonScanner(BaseScanner):
    """
    Radon - Python complexity analyzer.

    Computes Cyclomatic Complexity of Python source code.
    """

    COMPLEXITY_THRESHOLDS = {
        'A': Severity.INFO,      # 1-5: Simple
        'B': Severity.LOW,       # 6-10: Slightly complex
        'C': Severity.MEDIUM,    # 11-20: More complex
        'D': Severity.HIGH,      # 21-30: High complexity
        'E': Severity.HIGH,      # 31-40: Very high complexity
        'F': Severity.CRITICAL   # 41+: Extremely complex
    }

    @property
    def name(self) -> str:
        return "radon"

    @property
    def version(self) -> str:
        try:
            result = subprocess.run(
                ['radon', '--version'],
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    @property
    def supported_stacks(self) -> List[str]:
        return ['python', 'django', 'flask', 'fastapi']

    @property
    def scanner_type(self) -> str:
        return "complexity"

    def is_available(self) -> bool:
        return shutil.which('radon') is not None

    async def scan(self) -> ScanResult:
        """Execute radon complexity scan"""
        started_at = datetime.now()
        findings: List[ScanFinding] = []
        total_complexity = 0
        function_count = 0

        if not self.is_available():
            return ScanResult(
                scanner_name=self.name,
                scanner_version=self.version,
                stack="python",
                project_path=str(self.project_path),
                started_at=started_at,
                completed_at=datetime.now(),
                success=False,
                error_message="radon is not installed"
            )

        try:
            result = subprocess.run(
                ['radon', 'cc', '-j', '-a', str(self.project_path)],
                capture_output=True,
                text=True,
                cwd=str(self.project_path)
            )

            if result.stdout:
                data = json.loads(result.stdout)

                for filepath, functions in data.items():
                    if isinstance(functions, list):
                        for func in functions:
                            complexity = func.get('complexity', 0)
                            rank = func.get('rank', 'A')

                            total_complexity += complexity
                            function_count += 1

                            # Only report issues for C rank and above
                            if rank in ['C', 'D', 'E', 'F']:
                                findings.append(ScanFinding(
                                    scanner=self.name,
                                    rule_id=f"complexity-{rank}",
                                    message=f"Function '{func.get('name')}' has high complexity ({complexity})",
                                    severity=self.COMPLEXITY_THRESHOLDS.get(rank, Severity.MEDIUM),
                                    finding_type=FindingType.COMPLEXITY,
                                    file_path=filepath,
                                    line_number=func.get('lineno'),
                                    recommendation="Consider refactoring into smaller functions",
                                    metadata={
                                        'function_name': func.get('name'),
                                        'complexity_score': complexity,
                                        'rank': rank
                                    }
                                ))

            avg_complexity = total_complexity / function_count if function_count > 0 else 0

            metrics = ScanMetrics(
                complexity_average=round(avg_complexity, 2)
            )

            return ScanResult(
                scanner_name=self.name,
                scanner_version=self.version,
                stack="python",
                project_path=str(self.project_path),
                started_at=started_at,
                completed_at=datetime.now(),
                success=True,
                findings=findings,
                metrics=metrics
            )

        except Exception as e:
            logger.error(f"Radon scan failed: {e}")
            return ScanResult(
                scanner_name=self.name,
                scanner_version=self.version,
                stack="python",
                project_path=str(self.project_path),
                started_at=started_at,
                completed_at=datetime.now(),
                success=False,
                error_message=str(e)
            )
