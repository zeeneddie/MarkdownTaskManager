"""
Quality Scan Service

Orchestrates quality scans using the scanner registry.
Selects appropriate scanners based on project tech stack.
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

from app.scanners.registry import get_scanner_registry
from app.scanners.base import ScanResult, ScanFinding, Severity, FindingType

logger = logging.getLogger(__name__)


class QualityScanService:
    """
    Service for orchestrating quality scans across multiple scanners.

    Automatically selects appropriate scanners based on project tech stack
    and aggregates results into a unified quality report.
    """

    def __init__(self):
        self.registry = get_scanner_registry()

    async def run_scan(
        self,
        project_path: str,
        tech_stack: Optional[List[str]] = None,
        scanner_names: Optional[List[str]] = None,
        scan_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run quality scan on a project.

        Args:
            project_path: Path to the project codebase
            tech_stack: List of detected tech stacks (e.g., ['dotnet', 'csharp'])
            scanner_names: Optional specific scanners to run
            scan_options: Optional scan configuration

        Returns:
            Aggregated scan results with scores and findings
        """
        path = Path(project_path)
        if not path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        # Auto-detect stack if not provided
        if not tech_stack:
            tech_stack = self._detect_tech_stack(path)
            logger.info(f"Auto-detected tech stack: {tech_stack}")

        # Run scans
        scan_results = await self.registry.run_scan(
            project_path=project_path,
            stacks=tech_stack,
            scanner_names=scanner_names
        )

        # Aggregate results
        return self._aggregate_results(scan_results, tech_stack)

    def _detect_tech_stack(self, path: Path) -> List[str]:
        """
        Auto-detect tech stack from project files.

        Simple file-based detection for common patterns.
        """
        stacks = []

        # Python detection
        if list(path.glob("*.py")) or list(path.glob("**/*.py")):
            stacks.append("python")
            if (path / "manage.py").exists() or list(path.glob("**/settings.py")):
                stacks.append("django")
            elif list(path.glob("**/app.py")) or list(path.glob("**/flask_*.py")):
                stacks.append("flask")
            elif list(path.glob("**/main.py")) and (
                list(path.glob("**/routers")) or list(path.glob("**/routes.py"))
            ):
                stacks.append("fastapi")

        # .NET detection
        if list(path.glob("*.csproj")) or list(path.glob("**/*.csproj")):
            stacks.append("dotnet")
            stacks.append("csharp")
        if list(path.glob("*.vbproj")) or list(path.glob("**/*.vbproj")):
            stacks.append("dotnet")
            stacks.append("vbnet")
        if list(path.glob("**/*.aspx")) or list(path.glob("**/*.asp")):
            stacks.append("aspnet")

        # JavaScript/TypeScript detection
        if (path / "package.json").exists():
            stacks.append("node")
        if list(path.glob("**/*.ts")) or list(path.glob("**/*.tsx")):
            stacks.append("typescript")
        if list(path.glob("**/*.js")) or list(path.glob("**/*.jsx")):
            stacks.append("javascript")

        # Java detection
        if list(path.glob("**/*.java")) or (path / "pom.xml").exists():
            stacks.append("java")

        # Go detection
        if (path / "go.mod").exists() or list(path.glob("**/*.go")):
            stacks.append("go")

        # Rust detection
        if (path / "Cargo.toml").exists():
            stacks.append("rust")

        # PHP detection
        if list(path.glob("**/*.php")):
            stacks.append("php")

        # Default to generic if nothing detected
        if not stacks:
            stacks = ["generic"]

        return list(set(stacks))  # Remove duplicates

    def _aggregate_results(
        self,
        scan_results: Dict[str, ScanResult],
        tech_stack: List[str]
    ) -> Dict[str, Any]:
        """
        Aggregate scan results into quality metrics.
        """
        all_findings: List[ScanFinding] = []
        total_files_scanned = 0
        total_loc = 0
        total_code_lines = 0

        scanner_summaries = []

        for scanner_name, result in scan_results.items():
            if result.success:
                all_findings.extend(result.findings or [])

                if result.metrics:
                    total_files_scanned += result.metrics.files_scanned or 0
                    total_loc += result.metrics.lines_of_code or 0
                    total_code_lines += result.metrics.code_lines or 0

                scanner_summaries.append({
                    "scanner": scanner_name,
                    "version": result.scanner_version,
                    "success": True,
                    "findings_count": len(result.findings or []),
                    "duration_ms": (
                        (result.completed_at - result.started_at).total_seconds() * 1000
                        if result.completed_at and result.started_at else None
                    )
                })
            else:
                scanner_summaries.append({
                    "scanner": scanner_name,
                    "version": result.scanner_version,
                    "success": False,
                    "error": result.error_message
                })

        # Calculate scores
        security_findings = [f for f in all_findings if f.finding_type == FindingType.SECURITY]
        quality_findings = [f for f in all_findings if f.finding_type in [
            FindingType.CODE_SMELL, FindingType.COMPLEXITY, FindingType.DUPLICATION
        ]]

        security_score, quality_score, overall_score = self._calculate_scores(
            security_findings, quality_findings, total_code_lines
        )

        # Calculate tech debt days (rough estimate: 30 min per issue)
        tech_debt_days = self._estimate_tech_debt_days(all_findings)

        # Group findings by severity
        violation_groups = self._group_findings_by_type(all_findings)

        return {
            "tech_stack": tech_stack,
            "scanners_used": [s["scanner"] for s in scanner_summaries if s.get("success")],
            "scanner_details": scanner_summaries,
            "metrics": {
                "files_scanned": total_files_scanned,
                "lines_of_code": total_loc,
                "code_lines": total_code_lines
            },
            "scores": {
                "overall": overall_score,
                "security": security_score,
                "quality": quality_score
            },
            "tech_debt_days": tech_debt_days,
            "total_violations": len(all_findings),
            "violations_by_severity": {
                "critical": len([f for f in all_findings if f.severity == Severity.CRITICAL]),
                "high": len([f for f in all_findings if f.severity == Severity.HIGH]),
                "medium": len([f for f in all_findings if f.severity == Severity.MEDIUM]),
                "low": len([f for f in all_findings if f.severity == Severity.LOW]),
                "info": len([f for f in all_findings if f.severity == Severity.INFO])
            },
            "top_violations": violation_groups[:10],  # Top 10 violation types
            "all_findings": [
                {
                    "scanner": f.scanner,
                    "rule_id": f.rule_id,
                    "message": f.message,
                    "severity": f.severity.value,
                    "type": f.finding_type.value,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "recommendation": f.recommendation
                }
                for f in all_findings
            ]
        }

    def _calculate_scores(
        self,
        security_findings: List[ScanFinding],
        quality_findings: List[ScanFinding],
        total_lines: int
    ) -> Tuple[int, int, int]:
        """
        Calculate security, quality, and overall scores.

        Scoring:
        - Start at 100
        - Deduct points based on severity and count
        - Normalize by codebase size
        """
        # Security score calculation
        security_score = 100
        for finding in security_findings:
            if finding.severity == Severity.CRITICAL:
                security_score -= 15
            elif finding.severity == Severity.HIGH:
                security_score -= 8
            elif finding.severity == Severity.MEDIUM:
                security_score -= 3
            elif finding.severity == Severity.LOW:
                security_score -= 1
        security_score = max(0, min(100, security_score))

        # Quality score calculation (consider codebase size)
        quality_score = 100
        # Normalize by lines of code (per 1000 lines)
        loc_factor = max(1, total_lines / 1000) if total_lines > 0 else 1

        for finding in quality_findings:
            if finding.severity == Severity.CRITICAL:
                quality_score -= 10 / loc_factor
            elif finding.severity == Severity.HIGH:
                quality_score -= 5 / loc_factor
            elif finding.severity == Severity.MEDIUM:
                quality_score -= 2 / loc_factor
            elif finding.severity == Severity.LOW:
                quality_score -= 0.5 / loc_factor
        quality_score = max(0, min(100, int(quality_score)))

        # Overall score (weighted average)
        overall_score = int(security_score * 0.4 + quality_score * 0.6)

        return security_score, quality_score, overall_score

    def _estimate_tech_debt_days(self, findings: List[ScanFinding]) -> int:
        """
        Estimate technical debt in developer days.

        Rough estimates:
        - Critical: 2 hours per issue
        - High: 1 hour per issue
        - Medium: 30 min per issue
        - Low: 15 min per issue
        """
        total_minutes = 0
        for finding in findings:
            if finding.severity == Severity.CRITICAL:
                total_minutes += 120
            elif finding.severity == Severity.HIGH:
                total_minutes += 60
            elif finding.severity == Severity.MEDIUM:
                total_minutes += 30
            elif finding.severity == Severity.LOW:
                total_minutes += 15
            else:
                total_minutes += 5

        # Convert to days (8 hour workday)
        return total_minutes // (8 * 60)

    def _group_findings_by_type(
        self,
        findings: List[ScanFinding]
    ) -> List[Dict[str, Any]]:
        """
        Group findings by rule/type for summary.
        """
        groups: Dict[str, Dict[str, Any]] = {}

        for finding in findings:
            key = f"{finding.scanner}:{finding.rule_id}"
            if key not in groups:
                groups[key] = {
                    "type": finding.rule_id,
                    "scanner": finding.scanner,
                    "severity": finding.severity.value,
                    "count": 0,
                    "description": finding.message[:100] if finding.message else ""
                }
            groups[key]["count"] += 1

        # Sort by severity and count
        severity_order = {
            "critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4
        }
        sorted_groups = sorted(
            groups.values(),
            key=lambda x: (severity_order.get(x["severity"], 5), -x["count"])
        )

        return sorted_groups


# Singleton instance
_service: Optional[QualityScanService] = None


def get_quality_scan_service() -> QualityScanService:
    """Get the quality scan service instance"""
    global _service
    if _service is None:
        _service = QualityScanService()
    return _service
