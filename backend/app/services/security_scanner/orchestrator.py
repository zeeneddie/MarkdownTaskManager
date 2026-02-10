"""
Security Scan Orchestrator.

Coordinates multiple security scanners based on detected languages
and aggregates findings into a unified security report.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Type
from datetime import datetime, timezone
from collections import defaultdict

from .models.findings import (
    SecurityFinding, SecurityReport, ScanResult, ScannerType, Severity,
)
from .adapters.base import BaseScanner, ScannerNotAvailableError, CustomPatternScanner
from .adapters.opengrep_adapter import OpenGrepAdapter
from .adapters.bandit_adapter import BanditAdapter
from .adapters.gosec_adapter import GosecAdapter
from .adapters.trivy_adapter import TrivyAdapter
from .adapters.asp_scanner import ClassicASPScanner
from .adapters.secret_scanner import SecretScanner
from .adapters.owasp_scanner import OWASPScanner
from .adapters.generic_security_scanner import GenericSecurityScanner
from .adapters.code_quality_scanner import CodeQualityScanner
# Fase 36: Logic & Crypto Scanners
from .adapters.crypto_error_detector import CryptoErrorDetector
from .adapters.control_flow_logic_detector import ControlFlowLogicDetector
from .adapters.boolean_logic_detector import BooleanLogicDetector
# Fase 38: Memory Safety & Concurrency Scanners
from .adapters.memory_safety_detector import MemorySafetyDetector
from .adapters.concurrency_error_detector import ConcurrencyErrorDetector
# Fase 39: Web Security & Path Security Scanners
from .adapters.web_security_detector import WebSecurityDetector
from .adapters.path_security_detector import PathSecurityDetector
# Fase 41: Injection Vulnerability Scanners
from .adapters.injection_detector import InjectionDetector
from .adapters.auth_logic_detector import AuthLogicDetector
# Fase 42: Advanced False Negative Detection
from .adapters.obfuscation_detector import ObfuscationDetector
from .adapters.dynamic_feature_detector import DynamicFeatureDetector
from .adapters.framework_security_plugin import FrameworkSecurityPlugin
from .adapters.ast_taint_tracker import ASTTaintTracker

logger = logging.getLogger(__name__)


# Language detection by file extension
EXTENSION_TO_LANGUAGE = {
    # Python
    ".py": "python", ".pyw": "python", ".pyx": "python",
    # JavaScript/TypeScript
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".vue": "javascript", ".svelte": "javascript",
    # Go
    ".go": "go",
    # Ruby
    ".rb": "ruby", ".erb": "ruby", ".rake": "ruby", ".gemspec": "ruby",
    # PHP
    ".php": "php", ".phtml": "php", ".php3": "php", ".php4": "php", ".php5": "php",
    # Java
    ".java": "java", ".jsp": "java", ".jspx": "java",
    # Kotlin
    ".kt": "kotlin", ".kts": "kotlin",
    # Scala
    ".scala": "scala", ".sc": "scala",
    # C#
    ".cs": "csharp", ".cshtml": "csharp", ".razor": "csharp",
    # VB.NET
    ".vb": "vbnet", ".aspx": "vbnet", ".ascx": "vbnet", ".asmx": "vbnet", ".ashx": "vbnet",
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
# SecretScanner, OWASPScanner, GenericSecurityScanner, CodeQualityScanner, Fase 36, 38, 39, 41 scanners are included for relevant languages
LANGUAGE_SCANNERS: Dict[str, List[Type[BaseScanner]]] = {
    # Languages covered by OpenGrep + Generic Security Scanner + Code Quality Scanner + Fase 36 + Fase 38 + Fase 39 + Fase 41 Scanners
    "python": [OpenGrepAdapter, BanditAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner, CodeQualityScanner, CryptoErrorDetector, ControlFlowLogicDetector, BooleanLogicDetector, ConcurrencyErrorDetector, WebSecurityDetector, PathSecurityDetector, InjectionDetector, AuthLogicDetector, ObfuscationDetector, DynamicFeatureDetector, FrameworkSecurityPlugin, ASTTaintTracker],
    "javascript": [OpenGrepAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner, CodeQualityScanner, CryptoErrorDetector, ControlFlowLogicDetector, BooleanLogicDetector, WebSecurityDetector, PathSecurityDetector, InjectionDetector, AuthLogicDetector, ObfuscationDetector, DynamicFeatureDetector, FrameworkSecurityPlugin, ASTTaintTracker],
    "typescript": [OpenGrepAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner, CodeQualityScanner, CryptoErrorDetector, ControlFlowLogicDetector, BooleanLogicDetector, WebSecurityDetector, PathSecurityDetector, InjectionDetector, AuthLogicDetector, ObfuscationDetector, DynamicFeatureDetector, FrameworkSecurityPlugin, ASTTaintTracker],
    "go": [OpenGrepAdapter, GosecAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner, CryptoErrorDetector, ControlFlowLogicDetector, BooleanLogicDetector, ConcurrencyErrorDetector, PathSecurityDetector, InjectionDetector, AuthLogicDetector, ASTTaintTracker],
    "java": [OpenGrepAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner, CodeQualityScanner, CryptoErrorDetector, ControlFlowLogicDetector, BooleanLogicDetector, ConcurrencyErrorDetector, WebSecurityDetector, PathSecurityDetector, InjectionDetector, AuthLogicDetector, ObfuscationDetector, DynamicFeatureDetector, FrameworkSecurityPlugin, ASTTaintTracker],
    "kotlin": [OpenGrepAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner],
    "scala": [OpenGrepAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner],
    "csharp": [OpenGrepAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner, CodeQualityScanner, CryptoErrorDetector, ControlFlowLogicDetector, BooleanLogicDetector, WebSecurityDetector, PathSecurityDetector, InjectionDetector, AuthLogicDetector, FrameworkSecurityPlugin, ASTTaintTracker],
    "ruby": [OpenGrepAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner, CryptoErrorDetector, ControlFlowLogicDetector, BooleanLogicDetector, WebSecurityDetector, PathSecurityDetector, InjectionDetector, AuthLogicDetector, FrameworkSecurityPlugin, ASTTaintTracker],
    "php": [OpenGrepAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner, CryptoErrorDetector, ControlFlowLogicDetector, BooleanLogicDetector, WebSecurityDetector, PathSecurityDetector, InjectionDetector, AuthLogicDetector, ASTTaintTracker],
    "rust": [OpenGrepAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner, MemorySafetyDetector],
    "swift": [OpenGrepAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner],
    "c": [OpenGrepAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner, CryptoErrorDetector, ControlFlowLogicDetector, BooleanLogicDetector, MemorySafetyDetector, ConcurrencyErrorDetector, PathSecurityDetector, InjectionDetector],
    "cpp": [OpenGrepAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner, CryptoErrorDetector, ControlFlowLogicDetector, BooleanLogicDetector, MemorySafetyDetector, ConcurrencyErrorDetector, PathSecurityDetector, InjectionDetector],
    # VB.NET (new - for .aspx, .vb files)
    "vbnet": [ClassicASPScanner, SecretScanner, OWASPScanner, GenericSecurityScanner, CodeQualityScanner],
    # Legacy languages (custom scanners)
    "asp": [ClassicASPScanner, SecretScanner, OWASPScanner, GenericSecurityScanner],
    "vbscript": [ClassicASPScanner, SecretScanner, OWASPScanner, GenericSecurityScanner],
    # Config languages (high priority for secrets)
    "terraform": [OpenGrepAdapter, TrivyAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner],
    "yaml": [OpenGrepAdapter, TrivyAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner],
    "json": [OpenGrepAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner],
    "xml": [OpenGrepAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner],
    "html": [OpenGrepAdapter, SecretScanner, OWASPScanner, GenericSecurityScanner],
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
        self._progress_callback = None
        self._file_progress_callback = None

        # Initialize scanners
        self._scanners: Dict[ScannerType, BaseScanner] = {}
        self._initialize_scanners()

    def set_progress_callback(self, callback):
        """
        Set callback for scanner progress updates.

        Callback signature: callback(current: int, total: int, scanner_name: str)
        """
        self._progress_callback = callback

    def set_file_progress_callback(self, callback):
        """
        Set callback for per-file progress updates within pattern scanners.

        Callback signature: callback(current_file: int, total_files: int, file_path: str, scanner_name: str)

        This provides granular progress for scanners that process files one-by-one.
        """
        self._file_progress_callback = callback

    def _initialize_scanners(self):
        """Initialize all available scanners."""
        scanner_classes = [
            (ScannerType.OPENGREP, OpenGrepAdapter),
            (ScannerType.BANDIT, BanditAdapter),
            (ScannerType.GOSEC, GosecAdapter),
            (ScannerType.TRIVY, TrivyAdapter),
            (ScannerType.CUSTOM_ASP, ClassicASPScanner),
            (ScannerType.SECRET_SCANNER, SecretScanner),  # K3: Secret Detection
            (ScannerType.OWASP_SCANNER, OWASPScanner),  # K1: OWASP Top 10
            (ScannerType.GENERIC_SECURITY, GenericSecurityScanner),  # CVD-2025-001: Generic multi-language
            (ScannerType.CODE_QUALITY, CodeQualityScanner),  # Code quality: Common programming mistakes
            # Fase 36: Logic & Crypto Scanners
            (ScannerType.CRYPTO_ERROR, CryptoErrorDetector),  # Cryptographic vulnerability detection
            (ScannerType.CONTROL_FLOW_LOGIC, ControlFlowLogicDetector),  # Control flow and logic errors
            (ScannerType.BOOLEAN_LOGIC, BooleanLogicDetector),  # Boolean logic and comparison errors
            # Fase 38: Memory Safety & Concurrency Scanners
            (ScannerType.MEMORY_SAFETY, MemorySafetyDetector),  # Buffer overflow, use-after-free (CWE-787, 416, 125, 119)
            (ScannerType.CONCURRENCY_ERROR, ConcurrencyErrorDetector),  # Race conditions, deadlock (CWE-362)
            # Fase 39: Web Security & Path Security Scanners
            (ScannerType.WEB_SECURITY, WebSecurityDetector),  # Prototype pollution, CSV injection, invalid quantity (CWE-1321, 1236, 1284)
            (ScannerType.PATH_SECURITY, PathSecurityDetector),  # DLL hijack, unquoted path, ReDoS (CWE-427, 428, 1333)
            # Fase 41: Injection Vulnerability Scanners
            (ScannerType.INJECTION, InjectionDetector),  # XSS, SQLi, CMDi, Path, Deser, SSRF, XXE, SSTI, LDAP, NoSQL, CSRF, Upload
            (ScannerType.AUTH_LOGIC, AuthLogicDetector),  # Auth, AuthZ (CWE-862, 863, 287, 269, 306, 20)
            # Fase 42: Advanced False Negative Detection
            (ScannerType.OBFUSCATION, ObfuscationDetector),  # Obfuscation/deobfuscation detection
            (ScannerType.DYNAMIC_FEATURE, DynamicFeatureDetector),  # Dynamic language features (CWE-94, 470)
            (ScannerType.FRAMEWORK_SECURITY, FrameworkSecurityPlugin),  # Framework-specific security patterns
            (ScannerType.AST_TAINT, ASTTaintTracker),  # Cross-function taint tracking (CWE-89, 79, 78, 22)
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
                    logger.debug(f"Scanner {scanner_type.value} not available (install when needed)")

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
        timeout_per_scanner: int = 120,  # 2 minutes per scanner
        total_timeout: int = 600,  # 10 minutes total max
    ) -> SecurityReport:
        """
        Execute security scan on target.

        Args:
            target_path: Path to scan
            languages: Override language detection (optional)
            scanners: Specific scanners to run (optional)
            config: Scan configuration overrides
            timeout_per_scanner: Max seconds per individual scanner (default 120)
            total_timeout: Max seconds for entire scan operation (default 600)

        Returns:
            SecurityReport with all findings
        """
        started_at = datetime.now(timezone.utc)

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
                completed_at=datetime.now(timezone.utc),
                languages_detected=languages,
                scanners_used=set(),
            )

        # Run scanners SEQUENTIALLY for better progress tracking and timeout control
        # (Parallel execution blocks on synchronous file I/O, preventing timeouts)
        results = []
        total_scanners = len(scanner_instances)

        for idx, scanner in enumerate(scanner_instances):
            scanner_name = scanner.scanner_type.value
            scanner_config = config.get(scanner_name, {}) if config else {}

            # Emit progress callback if provided
            if hasattr(self, '_progress_callback') and self._progress_callback:
                self._progress_callback(idx, total_scanners, scanner_name)

            logger.info(f"[SCAN PROGRESS] {idx + 1}/{total_scanners}: {scanner_name}")

            try:
                result = await self._run_scanner(
                    scanner, target_path, scanner_config,
                    timeout_seconds=timeout_per_scanner
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Scanner {scanner_name} failed: {e}")
                results.append(e)

            # Check total timeout (0 = no timeout)
            if total_timeout > 0:
                elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
                if elapsed > total_timeout:
                    logger.warning(
                        f"Security scan total timeout ({total_timeout}s) exceeded after "
                        f"{idx + 1}/{total_scanners} scanners - returning partial results"
                    )
                    break

        # Final progress update
        if hasattr(self, '_progress_callback') and self._progress_callback:
            self._progress_callback(len(results), total_scanners, "complete")

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

        completed_at = datetime.now(timezone.utc)

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
        timeout_seconds: int = 120,  # Default 2 minutes per scanner, 0 = no timeout
    ) -> ScanResult:
        """Run a single scanner with optional timeout protection and file-level progress."""
        import time
        scanner_name = scanner.scanner_type.value
        timeout_info = f"timeout: {timeout_seconds}s" if timeout_seconds > 0 else "no timeout"
        logger.info(f"[SCANNER] Starting: {scanner_name} ({timeout_info})")
        start_time = time.time()

        # Set up file-level progress callback for pattern-based scanners
        if isinstance(scanner, CustomPatternScanner) and self._file_progress_callback:
            def file_progress(current: int, total: int, file_path: str):
                try:
                    self._file_progress_callback(current, total, file_path, scanner_name)
                except Exception as e:
                    logger.debug(f"File progress callback error: {e}")

            scanner.set_file_progress_callback(file_progress)

        async def run_scan_with_timeout():
            """Run scan with proper timeout handling for both sync and async code."""
            try:
                # If timeout is 0, run without timeout wrapper
                if timeout_seconds <= 0:
                    return await scanner.scan(target_path, config)
                # With await asyncio.sleep(0) in scan loop, this now works!
                return await asyncio.wait_for(
                    scanner.scan(target_path, config),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                # Cancel the scanner if it supports cancellation
                if isinstance(scanner, CustomPatternScanner):
                    scanner.cancel()
                raise
            except Exception:
                raise

        try:
            result = await run_scan_with_timeout()
            elapsed = time.time() - start_time
            findings_count = len(result.findings) if result else 0
            logger.info(
                f"[SCANNER] Completed: {scanner_name} | "
                f"{elapsed:.1f}s | {findings_count} findings"
            )
            return result
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            logger.warning(
                f"[SCANNER] Timeout: {scanner_name} after {elapsed:.1f}s "
                f"(limit: {timeout_seconds}s) - returning partial results"
            )
            # Return empty result instead of failing entire scan
            from .models.findings import ScanResult
            return ScanResult(
                scanner=scanner.scanner_type,
                scanner_version=None,
                scan_duration_ms=int(elapsed * 1000),
                findings=[],
                files_scanned=0,
                errors=[f"Scanner timed out after {timeout_seconds}s"],
            )
        except ScannerNotAvailableError as e:
            logger.warning(f"[SCANNER] Not available: {scanner_name} - {e}")
            raise
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[SCANNER] Failed: {scanner_name} after {elapsed:.1f}s - {e}")
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
