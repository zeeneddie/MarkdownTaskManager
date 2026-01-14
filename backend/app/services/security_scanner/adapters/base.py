"""
Base Scanner Adapter Interface.

Defines the contract that all security scanner adapters must implement,
whether they wrap external CLI tools or are custom implementations.
"""

import asyncio
import logging
import subprocess
import tempfile
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

from ..models.findings import (
    SecurityFinding, ScanResult, Severity, ScannerType, Location, SuggestedFix,
)
from ..parsers.sarif_parser import SarifParser

logger = logging.getLogger(__name__)


class ScannerNotAvailableError(Exception):
    """Raised when scanner binary is not available."""
    pass


class ScannerExecutionError(Exception):
    """Raised when scanner execution fails."""
    pass


class BaseScanner(ABC):
    """
    Abstract base class for all security scanners.

    Scanners can be:
    - External CLI tools that output SARIF (OpenGrep, Bandit, Gosec, etc.)
    - Custom regex-based scanners for legacy languages (ASP, COBOL)
    """

    def __init__(self):
        self._available: Optional[bool] = None

    @property
    @abstractmethod
    def scanner_type(self) -> ScannerType:
        """Return the scanner type identifier."""
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> Set[str]:
        """
        Return set of supported language identifiers.

        Examples: {"python", "javascript", "go", "asp", "cobol"}
        """
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> Set[str]:
        """
        Return set of supported file extensions.

        Examples: {".py", ".js", ".go", ".asp", ".cbl"}
        """
        pass

    @abstractmethod
    async def scan(
        self,
        target_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> ScanResult:
        """
        Execute security scan on target path.

        Args:
            target_path: Path to file or directory to scan
            config: Optional scanner-specific configuration

        Returns:
            ScanResult with all findings
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if scanner is available (binary installed, etc.).

        Returns:
            True if scanner can be used
        """
        pass

    def supports_file(self, file_path: Path) -> bool:
        """Check if scanner supports the given file."""
        return file_path.suffix.lower() in self.supported_extensions

    def get_scanner_version(self) -> Optional[str]:
        """Get scanner version if available."""
        return None


class ExternalCLIScanner(BaseScanner):
    """
    Base class for scanners that wrap external CLI tools.

    These scanners:
    - Execute a CLI binary (opengrep, bandit, gosec, trivy)
    - Capture SARIF output
    - Parse SARIF to SecurityFinding models
    """

    def __init__(self, binary_name: str, timeout_seconds: int = 300):
        """
        Initialize external CLI scanner.

        Args:
            binary_name: Name of the CLI binary (e.g., "opengrep", "bandit")
            timeout_seconds: Maximum execution time
        """
        super().__init__()
        self.binary_name = binary_name
        self.timeout_seconds = timeout_seconds
        self._binary_path: Optional[str] = None
        self._version: Optional[str] = None

    @property
    @abstractmethod
    def sarif_output_args(self) -> List[str]:
        """
        Return CLI arguments to enable SARIF output.

        Examples:
            ["--sarif"]
            ["-f", "sarif"]
            ["--format", "sarif"]
        """
        pass

    @abstractmethod
    def build_command(
        self,
        target_path: Path,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Build the full CLI command.

        Args:
            target_path: Path to scan
            output_path: Path for SARIF output file
            config: Optional configuration

        Returns:
            List of command arguments
        """
        pass

    def is_available(self) -> bool:
        """Check if binary is available in PATH."""
        if self._available is not None:
            return self._available

        self._binary_path = shutil.which(self.binary_name)
        self._available = self._binary_path is not None

        if self._available:
            logger.info(f"Scanner {self.binary_name} found at {self._binary_path}")
        else:
            logger.debug(f"Scanner {self.binary_name} not found in PATH (install if needed)")

        return self._available

    def get_scanner_version(self) -> Optional[str]:
        """Get version of the scanner binary."""
        if self._version:
            return self._version

        if not self.is_available():
            return None

        try:
            result = subprocess.run(
                [self.binary_name, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                self._version = result.stdout.strip().split("\n")[0]
            else:
                # Try -v flag
                result = subprocess.run(
                    [self.binary_name, "-v"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    self._version = result.stdout.strip().split("\n")[0]
        except Exception as e:
            logger.debug(f"Could not get version for {self.binary_name}: {e}")

        return self._version

    async def scan(
        self,
        target_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> ScanResult:
        """Execute CLI scanner and parse SARIF output."""
        if not self.is_available():
            raise ScannerNotAvailableError(
                f"Scanner {self.binary_name} is not available. "
                f"Please install it or add it to PATH."
            )

        started_at = datetime.utcnow()
        errors = []
        warnings = []

        # Create temp file for SARIF output
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".sarif",
            delete=False
        ) as tmp:
            output_path = Path(tmp.name)

        try:
            # Build and execute command
            command = self.build_command(target_path, output_path, config)
            logger.info(f"Executing: {' '.join(command)}")

            # Run async
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout_seconds,
                )
            except asyncio.TimeoutError:
                process.kill()
                raise ScannerExecutionError(
                    f"Scanner {self.binary_name} timed out after {self.timeout_seconds}s"
                )

            # Check for errors (note: many scanners return non-zero when findings exist)
            if stderr:
                stderr_text = stderr.decode("utf-8", errors="replace")
                if "error" in stderr_text.lower():
                    errors.append(stderr_text)
                else:
                    warnings.append(stderr_text)

            # Parse SARIF output
            if not output_path.exists():
                raise ScannerExecutionError(
                    f"Scanner {self.binary_name} did not produce output file"
                )

            parser = SarifParser(self.scanner_type)
            sarif_log = parser.parse_file(output_path)
            findings = parser.to_security_findings(sarif_log)

            # Count scanned files
            files_scanned = self._count_files(target_path)

            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            return ScanResult(
                scanner=self.scanner_type,
                scanner_version=self.get_scanner_version(),
                scan_duration_ms=duration_ms,
                findings=findings,
                files_scanned=files_scanned,
                errors=errors,
                warnings=warnings,
                started_at=started_at,
                completed_at=completed_at,
            )

        finally:
            # Cleanup temp file
            if output_path.exists():
                output_path.unlink()

    def _count_files(self, path: Path) -> int:
        """Count files that would be scanned."""
        if path.is_file():
            return 1

        count = 0
        for ext in self.supported_extensions:
            count += len(list(path.rglob(f"*{ext}")))
        return count


class CustomPatternScanner(BaseScanner):
    """
    Base class for custom regex-based scanners.

    These are used for legacy languages not supported by external tools
    (Classic ASP, COBOL, etc.) and for custom security rules.
    """

    def __init__(self):
        super().__init__()
        self._rules: List[Dict[str, Any]] = []

    @property
    @abstractmethod
    def rules(self) -> List[Dict[str, Any]]:
        """
        Return list of pattern-based rules.

        Each rule should have:
        - id: str - Rule identifier (e.g., "CWE-89-sql-injection")
        - pattern: str - Regex pattern to match
        - severity: Severity - Finding severity
        - title: str - Short title
        - description: str - Detailed description
        - cwe_ids: List[str] - Related CWE IDs
        - fix_suggestion: Optional[str] - How to fix
        """
        pass

    def is_available(self) -> bool:
        """Custom scanners are always available."""
        return True

    async def scan(
        self,
        target_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> ScanResult:
        """Execute pattern-based scan."""
        import re

        started_at = datetime.utcnow()
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
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                lines = content.split("\n")

                for rule in self.rules:
                    pattern = re.compile(rule["pattern"], re.IGNORECASE | re.MULTILINE)

                    for match in pattern.finditer(content):
                        # Calculate line number
                        line_start = content[:match.start()].count("\n") + 1
                        line_end = content[:match.end()].count("\n") + 1

                        # Get snippet
                        snippet_lines = lines[max(0, line_start - 1):min(len(lines), line_end + 2)]
                        snippet = "\n".join(snippet_lines)

                        finding = SecurityFinding(
                            id=f"{self.scanner_type.value}-{rule['id']}-{file_path}:{line_start}",
                            rule_id=rule["id"],
                            title=rule["title"],
                            description=rule["description"],
                            severity=rule["severity"],
                            scanner=self.scanner_type,
                            location=Location(
                                file_path=str(file_path),
                                start_line=line_start,
                                end_line=line_end,
                                snippet=snippet,
                            ),
                            cwe_ids=rule.get("cwe_ids", []),
                            category=rule.get("category"),
                        )

                        # Add fix suggestion if available
                        if rule.get("fix_suggestion"):
                            finding.suggested_fixes.append(
                                SuggestedFix(description=rule["fix_suggestion"])
                            )

                        findings.append(finding)

            except Exception as e:
                errors.append(f"Error scanning {file_path}: {e}")
                logger.error(f"Error scanning {file_path}: {e}")

        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        return ScanResult(
            scanner=self.scanner_type,
            scanner_version="1.0.0",
            scan_duration_ms=duration_ms,
            findings=findings,
            files_scanned=files_scanned,
            errors=errors,
            started_at=started_at,
            completed_at=completed_at,
        )
