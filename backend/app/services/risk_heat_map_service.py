"""
Risk Heat Map Service (A4 - Fase 24).

Aggregates security findings from all scanners into a visual risk heat map.
Provides risk scoring per file, module, and component.

Author: Claude Code (Week 158)
Date: 2026-01-15
"""

import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple

from .security_scanner.models.findings import (
    SecurityFinding,
    SecurityReport,
    ScanResult,
    ScannerType,
    Severity,
)

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk level classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class RiskCategory(str, Enum):
    """Risk category classification."""
    SECURITY = "security"
    COMPLEXITY = "complexity"
    TECH_DEBT = "tech_debt"
    DEPENDENCY = "dependency"
    COMPLIANCE = "compliance"


@dataclass
class RiskScore:
    """Risk score for a component."""
    raw_score: float  # 0-100
    level: RiskLevel
    factors: Dict[str, float] = field(default_factory=dict)

    @property
    def normalized(self) -> float:
        """Normalized score 0-1."""
        return min(self.raw_score / 100, 1.0)

    @classmethod
    def from_score(cls, score: float) -> "RiskScore":
        """Create RiskScore from raw score."""
        if score >= 80:
            level = RiskLevel.CRITICAL
        elif score >= 60:
            level = RiskLevel.HIGH
        elif score >= 40:
            level = RiskLevel.MEDIUM
        elif score >= 20:
            level = RiskLevel.LOW
        else:
            level = RiskLevel.MINIMAL

        return cls(raw_score=score, level=level)


@dataclass
class FileRisk:
    """Risk assessment for a single file."""
    file_path: str
    risk_score: RiskScore
    finding_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    categories: Set[str] = field(default_factory=set)
    cwe_ids: Set[str] = field(default_factory=set)
    scanners: Set[str] = field(default_factory=set)

    # Location info for visualization
    relative_path: str = ""
    directory: str = ""
    filename: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "file_path": self.file_path,
            "relative_path": self.relative_path,
            "directory": self.directory,
            "filename": self.filename,
            "risk_score": self.risk_score.raw_score,
            "risk_level": self.risk_score.level.value,
            "finding_count": self.finding_count,
            "severity_breakdown": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
            },
            "categories": list(self.categories),
            "cwe_ids": list(self.cwe_ids),
            "scanners": list(self.scanners),
        }


@dataclass
class ModuleRisk:
    """Risk assessment for a module/directory."""
    module_path: str
    module_name: str
    risk_score: RiskScore
    file_count: int
    total_findings: int
    high_risk_files: List[str] = field(default_factory=list)
    files: List[FileRisk] = field(default_factory=list)

    # Aggregated stats
    avg_file_risk: float = 0.0
    max_file_risk: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "module_path": self.module_path,
            "module_name": self.module_name,
            "risk_score": self.risk_score.raw_score,
            "risk_level": self.risk_score.level.value,
            "file_count": self.file_count,
            "total_findings": self.total_findings,
            "high_risk_files": self.high_risk_files,
            "avg_file_risk": self.avg_file_risk,
            "max_file_risk": self.max_file_risk,
            "files": [f.to_dict() for f in self.files],
        }


@dataclass
class HeatMapCell:
    """Single cell in heat map grid."""
    x: int
    y: int
    label: str
    risk_score: float
    risk_level: RiskLevel
    file_count: int
    finding_count: int
    tooltip: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "label": self.label,
            "value": self.risk_score,
            "level": self.risk_level.value,
            "file_count": self.file_count,
            "finding_count": self.finding_count,
            "tooltip": self.tooltip,
        }


@dataclass
class RiskHeatMap:
    """Complete risk heat map data structure."""
    project_path: str
    generated_at: datetime
    overall_risk: RiskScore
    total_files: int
    total_findings: int

    # Risk distribution
    files_by_risk: Dict[str, int] = field(default_factory=dict)
    findings_by_severity: Dict[str, int] = field(default_factory=dict)
    findings_by_category: Dict[str, int] = field(default_factory=dict)
    findings_by_scanner: Dict[str, int] = field(default_factory=dict)

    # Detailed data
    file_risks: List[FileRisk] = field(default_factory=list)
    module_risks: List[ModuleRisk] = field(default_factory=list)
    heat_map_grid: List[HeatMapCell] = field(default_factory=list)

    # Top items
    hotspots: List[FileRisk] = field(default_factory=list)  # Top 10 riskiest files

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API/visualization."""
        return {
            "project_path": self.project_path,
            "generated_at": self.generated_at.isoformat(),
            "summary": {
                "overall_risk_score": self.overall_risk.raw_score,
                "overall_risk_level": self.overall_risk.level.value,
                "total_files": self.total_files,
                "total_findings": self.total_findings,
            },
            "distribution": {
                "by_risk_level": self.files_by_risk,
                "by_severity": self.findings_by_severity,
                "by_category": self.findings_by_category,
                "by_scanner": self.findings_by_scanner,
            },
            "hotspots": [f.to_dict() for f in self.hotspots],
            "modules": [m.to_dict() for m in self.module_risks],
            "heat_map": [c.to_dict() for c in self.heat_map_grid],
        }

    def to_d3_format(self) -> Dict[str, Any]:
        """Convert to D3.js compatible format."""
        return {
            "name": Path(self.project_path).name,
            "children": self._build_d3_tree(),
            "metadata": {
                "generated_at": self.generated_at.isoformat(),
                "overall_risk": self.overall_risk.raw_score,
            },
        }

    def _build_d3_tree(self) -> List[Dict[str, Any]]:
        """Build D3.js treemap hierarchy."""
        # Group files by directory
        tree: Dict[str, Any] = {}

        for file_risk in self.file_risks:
            parts = Path(file_risk.relative_path).parts
            current = tree

            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {"_files": [], "_children": {}}
                current = current[part]["_children"]

            # Add file to its directory
            filename = parts[-1] if parts else file_risk.filename
            if "_files" not in current:
                current["_files"] = []
            current["_files"].append({
                "name": filename,
                "value": file_risk.finding_count or 1,
                "risk": file_risk.risk_score.raw_score,
                "level": file_risk.risk_score.level.value,
            })

        return self._tree_to_d3(tree)

    def _tree_to_d3(self, tree: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert internal tree to D3 format."""
        result = []

        for name, data in tree.items():
            if name.startswith("_"):
                continue

            node = {"name": name}
            children = []

            # Add subdirectories
            if "_children" in data:
                children.extend(self._tree_to_d3(data["_children"]))

            # Add files
            if "_files" in data:
                children.extend(data["_files"])

            if children:
                node["children"] = children
            else:
                node["value"] = 1

            result.append(node)

        return result


# Severity weights for risk calculation
SEVERITY_WEIGHTS = {
    Severity.CRITICAL: 10.0,
    Severity.HIGH: 5.0,
    Severity.MEDIUM: 2.0,
    Severity.LOW: 0.5,
    Severity.INFO: 0.1,
}


class RiskHeatMapService:
    """
    Service for generating risk heat maps from security findings.

    Features:
    - Aggregates findings from multiple scanners
    - Calculates risk scores per file and module
    - Generates heat map visualization data
    - Identifies risk hotspots
    """

    def __init__(
        self,
        severity_weights: Optional[Dict[Severity, float]] = None,
        max_score: float = 100.0,
    ):
        """
        Initialize service.

        Args:
            severity_weights: Custom weights for severity levels
            max_score: Maximum risk score
        """
        self.severity_weights = severity_weights or SEVERITY_WEIGHTS
        self.max_score = max_score

    def generate_heat_map(
        self,
        security_report: SecurityReport,
        project_root: Optional[Path] = None,
    ) -> RiskHeatMap:
        """
        Generate risk heat map from security report.

        Args:
            security_report: Aggregated security report
            project_root: Project root for relative paths

        Returns:
            Complete heat map data
        """
        project_path = security_report.project_path
        if project_root:
            project_path = str(project_root)

        # Get all findings
        all_findings = security_report.all_findings

        # Calculate file risks
        file_risks = self._calculate_file_risks(all_findings, project_path)

        # Calculate module risks
        module_risks = self._calculate_module_risks(file_risks)

        # Calculate overall risk
        overall_risk = self._calculate_overall_risk(file_risks)

        # Generate heat map grid
        heat_map_grid = self._generate_grid(module_risks)

        # Get distributions
        files_by_risk = self._count_by_risk_level(file_risks)
        findings_by_severity = security_report.get_severity_summary()
        findings_by_category = self._count_by_category(all_findings)
        findings_by_scanner = security_report.get_scanner_summary()

        # Get hotspots (top 10 riskiest files)
        hotspots = sorted(
            file_risks,
            key=lambda f: f.risk_score.raw_score,
            reverse=True,
        )[:10]

        return RiskHeatMap(
            project_path=project_path,
            generated_at=datetime.now(timezone.utc),
            overall_risk=overall_risk,
            total_files=len(file_risks),
            total_findings=len(all_findings),
            files_by_risk=files_by_risk,
            findings_by_severity=findings_by_severity,
            findings_by_category=findings_by_category,
            findings_by_scanner=findings_by_scanner,
            file_risks=file_risks,
            module_risks=module_risks,
            heat_map_grid=heat_map_grid,
            hotspots=hotspots,
        )

    def _calculate_file_risks(
        self,
        findings: List[SecurityFinding],
        project_path: str,
    ) -> List[FileRisk]:
        """Calculate risk for each file with findings."""
        # Group findings by file
        findings_by_file: Dict[str, List[SecurityFinding]] = defaultdict(list)

        for finding in findings:
            file_path = finding.location.file_path
            findings_by_file[file_path].append(finding)

        file_risks = []

        for file_path, file_findings in findings_by_file.items():
            # Count by severity
            critical = sum(1 for f in file_findings if f.severity == Severity.CRITICAL)
            high = sum(1 for f in file_findings if f.severity == Severity.HIGH)
            medium = sum(1 for f in file_findings if f.severity == Severity.MEDIUM)
            low = sum(1 for f in file_findings if f.severity == Severity.LOW)

            # Calculate risk score
            raw_score = sum(
                self.severity_weights.get(f.severity, 1.0)
                for f in file_findings
            )

            # Normalize to 0-100 (using log scale for better distribution)
            normalized_score = min(
                (math.log1p(raw_score) / math.log1p(50)) * 100,
                self.max_score,
            )

            risk_score = RiskScore.from_score(normalized_score)
            risk_score.factors = {
                "critical_findings": critical * self.severity_weights[Severity.CRITICAL],
                "high_findings": high * self.severity_weights[Severity.HIGH],
                "medium_findings": medium * self.severity_weights[Severity.MEDIUM],
                "low_findings": low * self.severity_weights[Severity.LOW],
            }

            # Collect metadata
            categories = set(f.category for f in file_findings if f.category)
            cwe_ids = set()
            for f in file_findings:
                cwe_ids.update(f.cwe_ids)
            scanners = set(f.scanner.value for f in file_findings)

            # Calculate relative path
            try:
                relative_path = str(Path(file_path).relative_to(project_path))
            except ValueError:
                relative_path = file_path

            path_obj = Path(file_path)

            file_risks.append(FileRisk(
                file_path=file_path,
                risk_score=risk_score,
                finding_count=len(file_findings),
                critical_count=critical,
                high_count=high,
                medium_count=medium,
                low_count=low,
                categories=categories,
                cwe_ids=cwe_ids,
                scanners=scanners,
                relative_path=relative_path,
                directory=str(path_obj.parent),
                filename=path_obj.name,
            ))

        return file_risks

    def _calculate_module_risks(
        self,
        file_risks: List[FileRisk],
    ) -> List[ModuleRisk]:
        """Calculate risk for each module/directory."""
        # Group by directory
        files_by_module: Dict[str, List[FileRisk]] = defaultdict(list)

        for file_risk in file_risks:
            # Use parent directory as module
            module_path = str(Path(file_risk.file_path).parent)
            files_by_module[module_path].append(file_risk)

        module_risks = []

        for module_path, files in files_by_module.items():
            if not files:
                continue

            # Calculate aggregated score
            total_score = sum(f.risk_score.raw_score for f in files)
            avg_score = total_score / len(files)
            max_score = max(f.risk_score.raw_score for f in files)

            # Use weighted average favoring max
            module_score = (avg_score * 0.4) + (max_score * 0.6)

            # Total findings
            total_findings = sum(f.finding_count for f in files)

            # High risk files
            high_risk = [
                f.filename for f in files
                if f.risk_score.level in (RiskLevel.CRITICAL, RiskLevel.HIGH)
            ]

            module_risks.append(ModuleRisk(
                module_path=module_path,
                module_name=Path(module_path).name or "root",
                risk_score=RiskScore.from_score(module_score),
                file_count=len(files),
                total_findings=total_findings,
                high_risk_files=high_risk[:5],
                files=files,
                avg_file_risk=avg_score,
                max_file_risk=max_score,
            ))

        # Sort by risk score
        module_risks.sort(key=lambda m: m.risk_score.raw_score, reverse=True)

        return module_risks

    def _calculate_overall_risk(self, file_risks: List[FileRisk]) -> RiskScore:
        """Calculate overall project risk."""
        if not file_risks:
            return RiskScore.from_score(0)

        # Weighted average with emphasis on critical files
        total_weight = 0
        weighted_sum = 0

        for file_risk in file_risks:
            # Higher weight for higher risk files
            weight = 1 + (file_risk.risk_score.raw_score / 100)
            weighted_sum += file_risk.risk_score.raw_score * weight
            total_weight += weight

        avg_score = weighted_sum / total_weight if total_weight > 0 else 0

        return RiskScore.from_score(avg_score)

    def _generate_grid(
        self,
        module_risks: List[ModuleRisk],
        max_cells: int = 50,
    ) -> List[HeatMapCell]:
        """Generate heat map grid for visualization."""
        cells = []

        # Create grid based on modules and their files
        for y, module in enumerate(module_risks[:10]):  # Top 10 modules
            for x, file_risk in enumerate(module.files[:5]):  # Top 5 files per module
                cells.append(HeatMapCell(
                    x=x,
                    y=y,
                    label=file_risk.filename,
                    risk_score=file_risk.risk_score.raw_score,
                    risk_level=file_risk.risk_score.level,
                    file_count=1,
                    finding_count=file_risk.finding_count,
                    tooltip=f"{file_risk.relative_path}: {file_risk.finding_count} findings",
                ))

        return cells[:max_cells]

    def _count_by_risk_level(
        self,
        file_risks: List[FileRisk],
    ) -> Dict[str, int]:
        """Count files by risk level."""
        counts = {level.value: 0 for level in RiskLevel}

        for file_risk in file_risks:
            counts[file_risk.risk_score.level.value] += 1

        return counts

    def _count_by_category(
        self,
        findings: List[SecurityFinding],
    ) -> Dict[str, int]:
        """Count findings by category."""
        counts: Dict[str, int] = defaultdict(int)

        for finding in findings:
            category = finding.category or "uncategorized"
            counts[category] += 1

        return dict(counts)

    def generate_summary_report(
        self,
        heat_map: RiskHeatMap,
    ) -> Dict[str, Any]:
        """Generate executive summary report."""
        return {
            "executive_summary": {
                "overall_risk": heat_map.overall_risk.level.value,
                "risk_score": round(heat_map.overall_risk.raw_score, 1),
                "total_files_analyzed": heat_map.total_files,
                "total_findings": heat_map.total_findings,
                "critical_files": heat_map.files_by_risk.get("critical", 0),
                "high_risk_files": heat_map.files_by_risk.get("high", 0),
            },
            "key_findings": {
                "top_3_hotspots": [
                    {
                        "file": h.relative_path,
                        "risk_score": round(h.risk_score.raw_score, 1),
                        "findings": h.finding_count,
                    }
                    for h in heat_map.hotspots[:3]
                ],
                "most_common_issues": sorted(
                    heat_map.findings_by_category.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5],
            },
            "recommendations": self._generate_recommendations(heat_map),
        }

    def _generate_recommendations(
        self,
        heat_map: RiskHeatMap,
    ) -> List[str]:
        """Generate risk-based recommendations."""
        recommendations = []

        # Based on severity distribution
        critical = heat_map.findings_by_severity.get("critical", 0)
        high = heat_map.findings_by_severity.get("high", 0)

        if critical > 0:
            recommendations.append(
                f"URGENT: Address {critical} critical severity findings immediately"
            )

        if high > 5:
            recommendations.append(
                f"HIGH PRIORITY: Review and remediate {high} high severity findings"
            )

        # Based on hotspots
        if heat_map.hotspots:
            top_file = heat_map.hotspots[0]
            if top_file.risk_score.raw_score > 70:
                recommendations.append(
                    f"Focus on {top_file.relative_path} - highest risk file with {top_file.finding_count} findings"
                )

        # Based on categories
        categories = heat_map.findings_by_category
        if categories.get("sql_injection", 0) > 0:
            recommendations.append(
                "Review SQL queries for injection vulnerabilities - use parameterized queries"
            )
        if categories.get("hardcoded_secret", 0) > 0:
            recommendations.append(
                "Remove hardcoded secrets and use environment variables or secret management"
            )

        return recommendations or ["No specific recommendations - risk levels are acceptable"]


def create_risk_heat_map_service() -> RiskHeatMapService:
    """Factory function to create Risk Heat Map service."""
    return RiskHeatMapService()
