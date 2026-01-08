# Resource Leak Detector Service
# Orchestrates multiple language-specific detectors
#
# Responsibilities:
# - Register language detectors
# - Route files to appropriate detector
# - Aggregate results into StabilityReport
# - Persist findings to database

from typing import List, Dict, Optional, Type
from pathlib import Path
import asyncio
import logging
import time
from datetime import datetime

from sqlalchemy.orm import Session

from .types import (
    StabilityCategory,
    SeverityLevel,
    LeakReport,
    StabilityReport,
    LeakFinding,
)
from .base_detector import BaseResourceLeakDetector

logger = logging.getLogger(__name__)


class ResourceLeakDetectorService:
    """
    Orchestrates resource leak detection across multiple languages.

    Usage:
        service = ResourceLeakDetectorService(db=session)
        service.register_detector(ClassicASPLeakDetector())
        service.register_detector(PHPLeakDetector())

        report = await service.analyze_project(
            project_id=1,
            project_name="FysioOne",
            base_path="/path/to/project"
        )
    """

    def __init__(self, db: Optional[Session] = None):
        """Initialize with optional database session."""
        self.db = db
        self._detectors: List[BaseResourceLeakDetector] = []
        self._extension_map: Dict[str, BaseResourceLeakDetector] = {}

    def register_detector(self, detector: BaseResourceLeakDetector) -> None:
        """
        Register a language-specific detector.

        Args:
            detector: Instance of a detector class
        """
        self._detectors.append(detector)

        # Map extensions to detector
        for ext in detector.get_supported_extensions():
            ext_lower = ext.lower()
            if ext_lower in self._extension_map:
                logger.warning(
                    f"Extension {ext} already registered to "
                    f"{self._extension_map[ext_lower].get_language()}, "
                    f"overwriting with {detector.get_language()}"
                )
            self._extension_map[ext_lower] = detector

        logger.info(
            f"Registered {detector.get_language()} detector for "
            f"{detector.get_supported_extensions()}"
        )

    def get_detector_for_file(self, file_path: str) -> Optional[BaseResourceLeakDetector]:
        """Get the appropriate detector for a file."""
        path = Path(file_path)
        ext = path.suffix.lower()

        return self._extension_map.get(ext)

    def get_registered_languages(self) -> List[str]:
        """Get list of registered language names."""
        return [d.get_language() for d in self._detectors]

    def get_supported_extensions(self) -> List[str]:
        """Get list of all supported extensions."""
        return list(self._extension_map.keys())

    async def analyze_file(
        self,
        file_path: str,
        content: Optional[str] = None,
    ) -> Optional[LeakReport]:
        """
        Analyze a single file for resource leaks.

        Args:
            file_path: Path to the file
            content: Optional file content (if not provided, will be read)

        Returns:
            LeakReport or None if file type not supported
        """
        detector = self.get_detector_for_file(file_path)
        if not detector:
            logger.debug(f"No detector for {file_path}")
            return None

        # Read content if not provided
        if content is None:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Failed to read {file_path}: {e}")
                return None

        # Analyze
        try:
            report = detector.analyze_file(file_path, content)
            return report
        except Exception as e:
            logger.error(f"Analysis failed for {file_path}: {e}")
            return None

    async def analyze_directory(
        self,
        base_path: str,
        recursive: bool = True,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> List[LeakReport]:
        """
        Analyze all supported files in a directory.

        Args:
            base_path: Root directory to scan
            recursive: Whether to scan subdirectories
            include_patterns: Optional glob patterns to include
            exclude_patterns: Optional glob patterns to exclude

        Returns:
            List of LeakReports for analyzed files
        """
        reports = []
        base = Path(base_path)

        if not base.exists():
            logger.error(f"Directory not found: {base_path}")
            return reports

        # Collect files
        files_to_analyze = []
        pattern = "**/*" if recursive else "*"

        for ext in self.get_supported_extensions():
            for file_path in base.glob(f"{pattern}{ext}"):
                # Apply exclude patterns
                if exclude_patterns:
                    skip = False
                    for exclude in exclude_patterns:
                        if file_path.match(exclude):
                            skip = True
                            break
                    if skip:
                        continue

                # Apply include patterns
                if include_patterns:
                    match = False
                    for include in include_patterns:
                        if file_path.match(include):
                            match = True
                            break
                    if not match:
                        continue

                files_to_analyze.append(str(file_path))

        logger.info(f"Found {len(files_to_analyze)} files to analyze")

        # Analyze files (could parallelize with asyncio.gather)
        for file_path in files_to_analyze:
            report = await self.analyze_file(file_path)
            if report:
                reports.append(report)

        return reports

    async def analyze_project(
        self,
        project_id: int,
        project_name: str,
        base_path: str,
        recursive: bool = True,
        exclude_patterns: Optional[List[str]] = None,
    ) -> StabilityReport:
        """
        Analyze an entire project and generate a StabilityReport.

        Args:
            project_id: ID of the project
            project_name: Name of the project
            base_path: Root directory of the project
            recursive: Whether to scan subdirectories
            exclude_patterns: Patterns to exclude

        Returns:
            Complete StabilityReport with all findings
        """
        start_time = time.time()

        # Create report
        report = StabilityReport(
            project_id=project_id,
            project_name=project_name,
        )

        # Analyze directory
        file_reports = await self.analyze_directory(
            base_path=base_path,
            recursive=recursive,
            exclude_patterns=exclude_patterns,
        )

        # Aggregate results
        files_with_issues = set()
        languages_seen = set()

        for file_report in file_reports:
            report.total_files_scanned += 1
            languages_seen.add(file_report.language)

            if file_report.has_leaks:
                files_with_issues.add(file_report.file_path)

                for finding in file_report.findings:
                    report.add_finding(finding)

        report.total_files_with_issues = len(files_with_issues)
        report.languages_analyzed = list(languages_seen)
        report.analysis_time_seconds = time.time() - start_time

        logger.info(
            f"Project analysis complete: {report.total_files_scanned} files, "
            f"{report.total_findings} findings, "
            f"{report.critical_count} critical, "
            f"score: {report.overall_score}"
        )

        # Persist to database if available
        if self.db:
            await self._persist_report(report)

        return report

    async def _persist_report(self, report: StabilityReport) -> None:
        """Persist stability report to database."""
        # TODO: Implement database persistence
        # This will be done after database migration
        pass

    def get_category_summary(
        self,
        report: StabilityReport,
    ) -> Dict[str, Dict]:
        """
        Get summary statistics by category.

        Returns:
            Dict mapping category names to stats
        """
        summary = {}

        for category in StabilityCategory:
            cat_finding = report.categories.get(category)
            if cat_finding:
                summary[category.value] = {
                    "issues_found": cat_finding.issues_found,
                    "critical": cat_finding.critical_count,
                    "high": cat_finding.high_count,
                    "medium": cat_finding.medium_count,
                    "low": cat_finding.low_count,
                    "severity_score": cat_finding.severity_score,
                }
            else:
                summary[category.value] = {
                    "issues_found": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "severity_score": 0,
                }

        return summary

    def get_top_findings(
        self,
        report: StabilityReport,
        limit: int = 10,
    ) -> List[LeakFinding]:
        """
        Get top findings sorted by severity.

        Args:
            report: StabilityReport to extract from
            limit: Maximum number of findings to return

        Returns:
            List of top findings
        """
        # Sort by severity (CRITICAL first, then HIGH, etc.)
        severity_order = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 3,
            SeverityLevel.INFO: 4,
        }

        sorted_findings = sorted(
            report.all_findings,
            key=lambda f: (severity_order.get(f.severity, 5), -f.confidence)
        )

        return sorted_findings[:limit]

    def get_files_with_most_issues(
        self,
        report: StabilityReport,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Get files with the most issues.

        Args:
            report: StabilityReport to extract from
            limit: Maximum number of files to return

        Returns:
            List of dicts with file path and issue count
        """
        file_counts: Dict[str, int] = {}
        file_critical: Dict[str, int] = {}

        for finding in report.all_findings:
            file_counts[finding.file_path] = file_counts.get(finding.file_path, 0) + 1
            if finding.is_critical:
                file_critical[finding.file_path] = file_critical.get(finding.file_path, 0) + 1

        # Sort by critical count, then total count
        sorted_files = sorted(
            file_counts.keys(),
            key=lambda f: (file_critical.get(f, 0), file_counts[f]),
            reverse=True
        )

        return [
            {
                "file_path": f,
                "total_issues": file_counts[f],
                "critical_issues": file_critical.get(f, 0),
            }
            for f in sorted_files[:limit]
        ]


def create_detector_service(db: Optional[Session] = None) -> ResourceLeakDetectorService:
    """
    Factory function to create a fully configured detector service.

    This will register all available detectors.

    Week 143: Core detectors (ADO, COM, File)
    Week 144: Category 3-6 analyzers (External Service, Memory, Session)
    Week 145: Category 7-8 analyzers (Exception, SQL)
    """
    service = ResourceLeakDetectorService(db=db)

    # === Week 143: Classic ASP Core Detectors ===
    try:
        from .detectors.classic_asp_detector import (
            ClassicASPLeakDetector,
            ClassicASPCOMDetector,
            ClassicASPFileDetector,
        )
        service.register_detector(ClassicASPLeakDetector())
        service.register_detector(ClassicASPCOMDetector())
        service.register_detector(ClassicASPFileDetector())
        logger.info("Registered Classic ASP core detectors (ADO, COM, File)")
    except ImportError as e:
        logger.debug(f"Classic ASP detectors not available: {e}")

    # === Week 144-145: Category-Specific Analyzers ===
    # Note: These analyzers have different interfaces but all analyze ASP files
    # They are registered separately and results are converted via to_leak_finding()

    try:
        from .detectors.external_service_analyzer import ExternalServiceAnalyzer
        # External service analyzer uses different interface
        # Will be integrated via analyze_with_all_analyzers method
        logger.info("ExternalServiceAnalyzer available (Category 3)")
    except ImportError as e:
        logger.debug(f"ExternalServiceAnalyzer not available: {e}")

    try:
        from .detectors.memory_analyzer import MemoryAnalyzer
        logger.info("MemoryAnalyzer available (Category 4)")
    except ImportError as e:
        logger.debug(f"MemoryAnalyzer not available: {e}")

    try:
        from .detectors.session_analyzer import SessionAnalyzer
        logger.info("SessionAnalyzer available (Category 6)")
    except ImportError as e:
        logger.debug(f"SessionAnalyzer not available: {e}")

    try:
        from .detectors.exception_analyzer import ExceptionAnalyzer
        logger.info("ExceptionAnalyzer available (Category 7)")
    except ImportError as e:
        logger.debug(f"ExceptionAnalyzer not available: {e}")

    try:
        from .detectors.sql_analyzer import SQLAnalyzer
        logger.info("SQLAnalyzer available (Category 8)")
    except ImportError as e:
        logger.debug(f"SQLAnalyzer not available: {e}")

    # === Future: Other Language Detectors ===
    try:
        from .detectors.php_detector import PHPLeakDetector
        service.register_detector(PHPLeakDetector())
    except ImportError:
        logger.debug("PHPLeakDetector not yet available")

    try:
        from .detectors.dotnet_detector import DotNetLeakDetector
        service.register_detector(DotNetLeakDetector())
    except ImportError:
        logger.debug("DotNetLeakDetector not yet available")

    try:
        from .detectors.java_detector import JavaLeakDetector
        service.register_detector(JavaLeakDetector())
    except ImportError:
        logger.debug("JavaLeakDetector not yet available")

    return service


async def analyze_with_all_analyzers(
    file_path: str,
    content: str,
) -> List[LeakFinding]:
    """
    Analyze a Classic ASP file with all available analyzers.

    This is a convenience function that runs all Category 3-8 analyzers
    and returns unified LeakFinding results.

    Args:
        file_path: Path to the file
        content: File content

    Returns:
        Combined list of LeakFinding from all analyzers
    """
    findings = []

    # Only analyze ASP files
    if not any(file_path.lower().endswith(ext) for ext in ['.asp', '.inc', '.asa']):
        return findings

    # Category 3: External Services
    try:
        from .detectors.external_service_analyzer import ExternalServiceAnalyzer
        analyzer = ExternalServiceAnalyzer()
        for finding in analyzer.analyze(content, file_path):
            findings.append(finding.to_leak_finding())
    except Exception as e:
        logger.error(f"ExternalServiceAnalyzer failed: {e}")

    # Category 4: Memory Intensive
    try:
        from .detectors.memory_analyzer import MemoryAnalyzer
        analyzer = MemoryAnalyzer()
        for finding in analyzer.analyze(content, file_path):
            findings.append(finding.to_leak_finding())
    except Exception as e:
        logger.error(f"MemoryAnalyzer failed: {e}")

    # Category 6: Session State
    try:
        from .detectors.session_analyzer import SessionAnalyzer
        analyzer = SessionAnalyzer()
        for finding in analyzer.analyze(content, file_path):
            findings.append(finding.to_leak_finding())
    except Exception as e:
        logger.error(f"SessionAnalyzer failed: {e}")

    # Category 7: Exception Handling
    try:
        from .detectors.exception_analyzer import ExceptionAnalyzer
        analyzer = ExceptionAnalyzer()
        for finding in analyzer.analyze(content, file_path):
            findings.append(finding.to_leak_finding())
    except Exception as e:
        logger.error(f"ExceptionAnalyzer failed: {e}")

    # Category 8: SQL Performance
    try:
        from .detectors.sql_analyzer import SQLAnalyzer
        analyzer = SQLAnalyzer()
        for finding in analyzer.analyze(content, file_path):
            findings.append(finding.to_leak_finding())
    except Exception as e:
        logger.error(f"SQLAnalyzer failed: {e}")

    return findings
