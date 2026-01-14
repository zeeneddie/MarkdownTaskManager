"""
Security Scan Orchestrator.

Coordinates multiple security scanners based on detected languages
and aggregates findings into a unified security report.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Type
from datetime import datetime
from collections import defaultdict

from .models.findings import (
    SecurityFinding, SecurityReport, ScanResult, ScannerType, Severity,
)
from .adapters.base import BaseScanner, ScannerNotAvailableError
from .adapters.opengrep_adapter import OpenGrepAdapter
from .adapters.bandit_adapter import BanditAdapter
from .adapters.gosec_adapter import GosecAdapter
from .adapters.trivy_adapter import TrivyAdapter
from .adapters.asp_scanner import ClassicASPScanner

logger = logging.getLogger(__name__)


# Language detection by file extension
EXTENSION_TO_LANGUAGE = {
    # Python
    ".py": "python", ".pyw": "python",
    # JavaScript/TypeScript
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    # Go
    ".go": "go",
    # Ruby
    ".rb": "ruby", ".erb": "ruby",
    # PHP
    ".php": "php",
    # Java
    ".java": "java",
    # Kotlin
    ".kt": "kotlin", ".kts": "kotlin",
    # Scala
    ".scala": "scala",
    # C#
    ".cs": "csharp",
    # C/C++
    ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp",
    # Rust
    ".rs": "rust",
    # Swift
    ".swift": "swift",
    # Classic ASP
    ".asp": "asp", ".asa": "asp", ".inc": "asp",
    # VBScript
    ".vbs": "vbscript",
    # COBOL
    ".cbl": "cobol", ".cob": "cobol", ".cpy": "cobol",
    # SQL
    ".sql": "sql",
    # Config/IaC
    ".tf": "terraform",
    ".yaml": "yaml", ".yml": "yaml",
    ".json": "json",
    ".xml": "xml",
    ".html": "html", ".htm": "html",
}

# Scanners appropriate for each language
LANGUAGE_SCANNERS: Dict[str, List[Type[BaseScanner]]] = {
    # Languages covered by OpenGrep
    "python": [OpenGrepAdapter, BanditAdapter],
    "javascript": [OpenGrepAdapter],
    "typescript": [OpenGrepAdapter],
    "go": [OpenGrepAdapter, GosecAdapter],
    "java": [OpenGrepAdapter],
    "kotlin": [OpenGrepAdapter],
    "scala": [OpenGrepAdapter],
    "csharp": [OpenGrepAdapter],
    "ruby": [OpenGrepAdapter],
    "php": [OpenGrepAdapter],
    "rust": [OpenGrepAdapter],
    "swift": [OpenGrepAdapter],
    "c": [OpenGrepAdapter],
    "cpp": [OpenGrepAdapter],
    # Legacy languages (custom scanners)
    "asp": [ClassicASPScanner],
    "vbscript": [ClassicASPScanner],
    # Config languages
    "terraform": [OpenGrepAdapter, TrivyAdapter],
    "yaml": [OpenGrepAdapter, TrivyAdapter],
    "json": [OpenGrepAdapter],
    "xml": [OpenGrepAdapter],
    "html": [OpenGrepAdapter],
}


class SecurityScanOrchestrator:
    """
    Orchestrates security scanning across multiple tools.

    Features:
    - Automatic language detection
    - Parallel scanner execution
    - Finding deduplication
    - CWE coverage tracking
    - Unified reporting
    """

    def __init__(
        self,
        enabled_scanners: Optional[Set[ScannerType]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize orchestrator.

        Args:
            enabled_scanners: Set of scanner types to enable (all if None)
            config: Configuration for individual scanners
        """
        self.config = config or {}
        self.enabled_scanners = enabled_scanners

        # Initialize scanners
        self._scanners: Dict[ScannerType, BaseScanner] = {}
        self._initialize_scanners()

    def _initialize_scanners(self):
        """Initialize all available scanners."""
        scanner_classes = [
            (ScannerType.OPENGREP, OpenGrepAdapter),
            (ScannerType.BANDIT, BanditAdapter),
            (ScannerType.GOSEC, GosecAdapter),
            (ScannerType.TRIVY, TrivyAdapter),
            (ScannerType.CUSTOM_ASP, ClassicASPScanner),
        ]

        for scanner_type, scanner_class in scanner_classes:
            if self.enabled_scanners and scanner_type not in self.enabled_scanners:
                continue

            try:
                scanner_config = self.config.get(scanner_type.value, {})
                scanner = scanner_class(**scanner_config) if scanner_config else scanner_class()

                if scanner.is_available():
                    self._scanners[scanner_type] = scanner
                    logger.info(f"Scanner {scanner_type.value} initialized and available")
                else:
                    logger.warning(f"Scanner {scanner_type.value} not available (not installed)")

            except Exception as e:
                logger.error(f"Failed to initialize {scanner_type.value}: {e}")

    def get_available_scanners(self) -> List[ScannerType]:
        """Get list of available scanners."""
        return list(self._scanners.keys())

    def detect_languages(self, target_path: Path) -> Set[str]:
        """
        Detect programming languages in target path.

        Args:
            target_path: Path to scan

        Returns:
            Set of detected language identifiers
        """
        languages = set()

        if target_path.is_file():
            ext = target_path.suffix.lower()
            if ext in EXTENSION_TO_LANGUAGE:
                languages.add(EXTENSION_TO_LANGUAGE[ext])
        else:
            for file_path in target_path.rglob("*"):
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    if ext in EXTENSION_TO_LANGUAGE:
                        languages.add(EXTENSION_TO_LANGUAGE[ext])

        logger.info(f"Detected languages: {languages}")
        return languages

    def select_scanners(self, languages: Set[str]) -> List[BaseScanner]:
        """
        Select appropriate scanners for detected languages.

        Args:
            languages: Set of detected languages

        Returns:
            List of scanner instances to run
        """
        selected = set()

        for language in languages:
            if language in LANGUAGE_SCANNERS:
                for scanner_class in LANGUAGE_SCANNERS[language]:
                    # Find matching scanner instance
                    for scanner_type, scanner in self._scanners.items():
                        if isinstance(scanner, scanner_class):
                            selected.add(scanner_type)

        # Always include Trivy for dependency scanning
        if ScannerType.TRIVY in self._scanners:
            selected.add(ScannerType.TRIVY)

        scanners = [self._scanners[st] for st in selected]
        logger.info(f"Selected scanners: {[s.scanner_type.value for s in scanners]}")

        return scanners

    async def scan(
        self,
        target_path: Path,
        languages: Optional[Set[str]] = None,
        scanners: Optional[List[ScannerType]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> SecurityReport:
        """
        Execute security scan on target.

        Args:
            target_path: Path to scan
            languages: Override language detection (optional)
            scanners: Specific scanners to run (optional)
            config: Scan configuration overrides

        Returns:
            SecurityReport with all findings
        """
        started_at = datetime.utcnow()

        # Detect languages if not provided
        if languages is None:
            languages = self.detect_languages(target_path)

        # Select scanners
        if scanners:
            scanner_instances = [
                self._scanners[st]
                for st in scanners
                if st in self._scanners
            ]
        else:
            scanner_instances = self.select_scanners(languages)

        if not scanner_instances:
            logger.warning("No scanners available for detected languages")
            return SecurityReport(
                project_path=str(target_path),
                scan_results=[],
                started_at=started_at,
                completed_at=datetime.utcnow(),
                languages_detected=languages,
                scanners_used=set(),
            )

        # Run scanners in parallel
        scan_tasks = []
        for scanner in scanner_instances:
            scanner_config = config.get(scanner.scanner_type.value, {}) if config else {}
            task = self._run_scanner(scanner, target_path, scanner_config)
            scan_tasks.append(task)

        results = await asyncio.gather(*scan_tasks, return_exceptions=True)

        # Process results
        scan_results = []
        scanners_used = set()

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Scanner failed: {result}")
                continue
            if isinstance(result, ScanResult):
                scan_results.append(result)
                scanners_used.add(result.scanner)

        completed_at = datetime.utcnow()

        return SecurityReport(
            project_path=str(target_path),
            scan_results=scan_results,
            started_at=started_at,
            completed_at=completed_at,
            languages_detected=languages,
            scanners_used=scanners_used,
        )

    async def _run_scanner(
        self,
        scanner: BaseScanner,
        target_path: Path,
        config: Dict[str, Any],
    ) -> ScanResult:
        """Run a single scanner."""
        logger.info(f"Running scanner: {scanner.scanner_type.value}")
        try:
            return await scanner.scan(target_path, config)
        except ScannerNotAvailableError as e:
            logger.warning(f"Scanner not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Scanner {scanner.scanner_type.value} failed: {e}")
            raise

    async def scan_with_report(
        self,
        target_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run scan and return detailed report dict.

        Useful for API responses and serialization.
        """
        report = await self.scan(target_path, config=config)

        return {
            "project_path": report.project_path,
            "started_at": report.started_at.isoformat(),
            "completed_at": report.completed_at.isoformat(),
            "duration_ms": int((report.completed_at - report.started_at).total_seconds() * 1000),
            "languages_detected": list(report.languages_detected),
            "scanners_used": [s.value for s in report.scanners_used],
            "summary": {
                "total_findings": report.total_findings,
                "critical": report.total_critical,
                "high": report.total_high,
                "by_severity": report.get_severity_summary(),
                "by_scanner": report.get_scanner_summary(),
            },
            "cwe_coverage": {
                "top_25": report.cwe_top_25_coverage,
                "all": report.cwe_coverage,
            },
            "findings": [
                {
                    "id": f.id,
                    "rule_id": f.rule_id,
                    "title": f.title,
                    "description": f.description,
                    "severity": f.severity.value,
                    "scanner": f.scanner.value,
                    "location": {
                        "file": f.location.file_path,
                        "start_line": f.location.start_line,
                        "end_line": f.location.end_line,
                        "snippet": f.location.snippet,
                    },
                    "cwe_ids": f.cwe_ids,
                    "is_cwe_top_25": f.is_cwe_top_25,
                    "category": f.category,
                }
                for f in report.all_findings
            ],
        }


def create_security_orchestrator(
    enabled_scanners: Optional[Set[ScannerType]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> SecurityScanOrchestrator:
    """Factory function to create security orchestrator."""
    return SecurityScanOrchestrator(
        enabled_scanners=enabled_scanners,
        config=config,
    )
