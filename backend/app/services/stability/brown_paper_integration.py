# Brown Paper Stability Integration
# Integrates Resource Leak Detection with Brown Paper workflow
#
# Week 145-146: Connects stability analysis to Brown Paper sessions
# for comprehensive legacy code assessment.
#
# Flow:
# 1. BrownPaperService runs code structure analysis
# 2. StabilityIntegration runs resource leak detection on same codebase
# 3. Results are merged into BrownPaperAnalysis for unified reporting

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timezone

from .detector_service import (
    ResourceLeakDetectorService,
    create_detector_service,
    analyze_with_all_analyzers,
)
from .types import (
    StabilityReport,
    StabilityCategory,
    LeakFinding,
    SeverityLevel,
)

logger = logging.getLogger(__name__)


@dataclass
class StabilityIntegrationResult:
    """Result of stability analysis for Brown Paper integration."""

    # Core metrics
    total_files_scanned: int = 0
    files_with_issues: int = 0
    total_findings: int = 0

    # Severity breakdown
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # Category breakdown
    category_breakdown: Dict[str, int] = field(default_factory=dict)

    # Overall score (0-100, higher = more stable)
    stability_score: int = 100

    # Risk level for Brown Paper assessment
    risk_level: str = "low"  # low, medium, high, critical

    # Top issues for prioritization
    top_issues: List[Dict[str, Any]] = field(default_factory=list)

    # Files requiring most attention
    hotspot_files: List[Dict[str, Any]] = field(default_factory=list)

    # Languages analyzed
    languages: List[str] = field(default_factory=list)

    # Analysis metadata
    analysis_time_ms: int = 0
    analyzed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_files_scanned": self.total_files_scanned,
            "files_with_issues": self.files_with_issues,
            "total_findings": self.total_findings,
            "severity_breakdown": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
            },
            "category_breakdown": self.category_breakdown,
            "stability_score": self.stability_score,
            "risk_level": self.risk_level,
            "top_issues": self.top_issues,
            "hotspot_files": self.hotspot_files,
            "languages": self.languages,
            "analysis_time_ms": self.analysis_time_ms,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
        }


class BrownPaperStabilityIntegration:
    """
    Integrates stability analysis with Brown Paper workflow.

    Usage:
        integration = BrownPaperStabilityIntegration()
        result = await integration.analyze_for_brown_paper(
            project_path="/path/to/legacy/project",
            project_name="LegacyApp"
        )

        # Merge into Brown Paper analysis
        brown_paper_analysis.stability = result.to_dict()
    """

    def __init__(self):
        """Initialize with detector service."""
        self._detector_service: Optional[ResourceLeakDetectorService] = None

    def _get_detector_service(self) -> ResourceLeakDetectorService:
        """Lazy load detector service."""
        if self._detector_service is None:
            self._detector_service = create_detector_service()
        return self._detector_service

    async def analyze_for_brown_paper(
        self,
        project_path: str,
        project_name: str,
        project_id: int = 0,
        exclude_patterns: Optional[List[str]] = None,
    ) -> StabilityIntegrationResult:
        """
        Run stability analysis for Brown Paper integration.

        Args:
            project_path: Root path of the project
            project_name: Name of the project
            project_id: Optional project ID
            exclude_patterns: Patterns to exclude from analysis

        Returns:
            StabilityIntegrationResult with aggregated findings
        """
        import time
        start_time = time.time()

        # Default exclude patterns for common non-source directories
        if exclude_patterns is None:
            exclude_patterns = [
                "**/node_modules/**",
                "**/.venv/**",
                "**/venv/**",
                "**/__pycache__/**",
                "**/.git/**",
                "**/dist/**",
                "**/build/**",
            ]

        detector = self._get_detector_service()

        # Check if we have any detectors registered
        if not detector.get_registered_languages():
            logger.warning("No stability detectors registered")
            return StabilityIntegrationResult(
                analyzed_at=datetime.now(timezone.utc),
                analysis_time_ms=int((time.time() - start_time) * 1000),
            )

        logger.info(f"Starting stability analysis for Brown Paper: {project_name}")
        logger.info(f"Registered languages: {detector.get_registered_languages()}")

        try:
            # Run full project analysis
            stability_report = await detector.analyze_project(
                project_id=project_id,
                project_name=project_name,
                base_path=project_path,
                recursive=True,
                exclude_patterns=exclude_patterns,
            )

            # Convert to integration result
            result = self._convert_report_to_result(stability_report)
            result.analysis_time_ms = int((time.time() - start_time) * 1000)
            result.analyzed_at = datetime.now(timezone.utc)

            logger.info(
                f"Stability analysis complete: {result.total_findings} findings, "
                f"score: {result.stability_score}, risk: {result.risk_level}"
            )

            return result

        except Exception as e:
            logger.error(f"Stability analysis failed: {e}", exc_info=True)
            return StabilityIntegrationResult(
                analyzed_at=datetime.now(timezone.utc),
                analysis_time_ms=int((time.time() - start_time) * 1000),
            )

    def _convert_report_to_result(
        self,
        report: StabilityReport
    ) -> StabilityIntegrationResult:
        """Convert StabilityReport to StabilityIntegrationResult."""

        # Build category breakdown
        category_breakdown = {}
        for category in StabilityCategory:
            cat_finding = report.categories.get(category)
            if cat_finding and cat_finding.issues_found > 0:
                category_breakdown[category.value] = cat_finding.issues_found

        # Calculate risk level based on findings
        risk_level = self._calculate_risk_level(
            report.critical_count,
            report.high_count,
            report.medium_count,
            report.total_findings,
        )

        # Get top issues sorted by severity
        top_issues = self._get_top_issues(report, limit=10)

        # Get hotspot files
        hotspot_files = self._get_hotspot_files(report, limit=10)

        return StabilityIntegrationResult(
            total_files_scanned=report.total_files_scanned,
            files_with_issues=report.total_files_with_issues,
            total_findings=report.total_findings,
            critical_count=report.critical_count,
            high_count=report.high_count,
            medium_count=report.medium_count,
            low_count=report.low_count,
            category_breakdown=category_breakdown,
            stability_score=report.overall_score,
            risk_level=risk_level,
            top_issues=top_issues,
            hotspot_files=hotspot_files,
            languages=report.languages_analyzed,
        )

    def _calculate_risk_level(
        self,
        critical: int,
        high: int,
        medium: int,
        total: int,
    ) -> str:
        """Calculate risk level for Brown Paper assessment."""
        if critical >= 5 or (critical >= 2 and high >= 10):
            return "critical"
        elif critical >= 1 or high >= 10:
            return "high"
        elif high >= 3 or medium >= 15:
            return "medium"
        else:
            return "low"

    def _get_top_issues(
        self,
        report: StabilityReport,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top issues sorted by severity."""
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

        return [
            {
                "file_path": f.file_path,
                "line_number": f.line_number,
                "category": f.category.value if f.category else "unknown",
                "severity": f.severity.value,
                "description": f.description,
                "suggested_fix": f.suggested_fix,
            }
            for f in sorted_findings[:limit]
        ]

    def _get_hotspot_files(
        self,
        report: StabilityReport,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get files with the most issues."""
        file_counts: Dict[str, int] = {}
        file_critical: Dict[str, int] = {}
        file_categories: Dict[str, set] = {}

        for finding in report.all_findings:
            file_counts[finding.file_path] = file_counts.get(finding.file_path, 0) + 1

            if finding.is_critical:
                file_critical[finding.file_path] = file_critical.get(finding.file_path, 0) + 1

            if finding.file_path not in file_categories:
                file_categories[finding.file_path] = set()
            if finding.category:
                file_categories[finding.file_path].add(finding.category.value)

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
                "categories": list(file_categories.get(f, set())),
            }
            for f in sorted_files[:limit]
        ]

    async def analyze_asp_file_comprehensive(
        self,
        file_path: str,
        content: str,
    ) -> List[Dict[str, Any]]:
        """
        Run all analyzers on a single ASP file.

        This is useful for getting detailed analysis of specific files
        during Brown Paper review.

        Args:
            file_path: Path to the file
            content: File content

        Returns:
            List of findings as dictionaries
        """
        findings = await analyze_with_all_analyzers(file_path, content)

        return [
            {
                "file_path": f.file_path,
                "line_number": f.line_number,
                "category": f.category.value if f.category else "unknown",
                "severity": f.severity.value,
                "description": f.description,
                "suggested_fix": f.suggested_fix,
                "confidence": f.confidence,
                "code_context": f.code_context,
            }
            for f in findings
        ]


# Module-level singleton
_integration_instance: Optional[BrownPaperStabilityIntegration] = None


def get_brown_paper_stability_integration() -> BrownPaperStabilityIntegration:
    """Get or create the Brown Paper stability integration singleton."""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = BrownPaperStabilityIntegration()
    return _integration_instance
