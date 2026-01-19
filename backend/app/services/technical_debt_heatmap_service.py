"""
Technical Debt Heatmap Service (E7 - Fase 24).

Combines TechnicalDebtService metrics with heatmap visualization.
Provides visual heat map showing technical debt per module/file.

Metrics weighted as per gap-analysis:
- Cyclomatic Complexity: 25%
- Code Duplication: 20%
- Test Coverage: 20%
- Dependency Count: 15%
- Age Since Last Change: 10%
- Bug History: 10%

Author: Claude Code (Week 158)
Date: 2026-01-19
"""

import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple

logger = logging.getLogger(__name__)


class DebtLevel(str, Enum):
    """Technical debt level classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class DebtCategory(str, Enum):
    """Technical debt category."""
    COMPLEXITY = "complexity"
    DUPLICATION = "duplication"
    TEST_COVERAGE = "test_coverage"
    DEPENDENCIES = "dependencies"
    STALENESS = "staleness"
    BUG_HISTORY = "bug_history"


# Metric weights as per gap-analysis specification
METRIC_WEIGHTS = {
    DebtCategory.COMPLEXITY: 0.25,
    DebtCategory.DUPLICATION: 0.20,
    DebtCategory.TEST_COVERAGE: 0.20,
    DebtCategory.DEPENDENCIES: 0.15,
    DebtCategory.STALENESS: 0.10,
    DebtCategory.BUG_HISTORY: 0.10,
}


@dataclass
class DebtScore:
    """Debt score for a component."""
    raw_score: float  # 0-100
    level: DebtLevel
    factors: Dict[str, float] = field(default_factory=dict)

    @property
    def normalized(self) -> float:
        """Normalized score 0-1."""
        return min(self.raw_score / 100, 1.0)

    @classmethod
    def from_score(cls, score: float) -> "DebtScore":
        """Create DebtScore from raw score."""
        if score >= 80:
            level = DebtLevel.CRITICAL
        elif score >= 60:
            level = DebtLevel.HIGH
        elif score >= 40:
            level = DebtLevel.MEDIUM
        elif score >= 20:
            level = DebtLevel.LOW
        else:
            level = DebtLevel.MINIMAL

        return cls(raw_score=score, level=level)


@dataclass
class FileDebtMetrics:
    """Technical debt metrics for a single file."""
    file_path: str
    relative_path: str
    filename: str

    # Raw metrics
    cyclomatic_complexity: float = 0.0
    duplication_percentage: float = 0.0
    test_coverage_percentage: float = 100.0  # Default to covered
    dependency_count: int = 0
    days_since_change: int = 0
    bug_count: int = 0

    # Normalized scores (0-100)
    complexity_score: float = 0.0
    duplication_score: float = 0.0
    coverage_score: float = 0.0
    dependency_score: float = 0.0
    staleness_score: float = 0.0
    bug_score: float = 0.0

    # Calculated debt
    debt_score: Optional[DebtScore] = None

    # Additional metadata
    lines_of_code: int = 0
    language: str = ""

    def calculate_scores(self) -> None:
        """Calculate normalized scores from raw metrics."""
        # Complexity: 0-50 mapped to 0-100 (higher is worse)
        self.complexity_score = min(self.cyclomatic_complexity * 2, 100)

        # Duplication: 0-100% mapped to 0-100 (higher is worse)
        self.duplication_score = self.duplication_percentage

        # Coverage: inverted (0% coverage = 100 debt score)
        self.coverage_score = 100 - self.test_coverage_percentage

        # Dependencies: 0-50 mapped to 0-100 (higher is worse)
        self.dependency_score = min(self.dependency_count * 2, 100)

        # Staleness: 0-365 days mapped to 0-100 (older is worse)
        self.staleness_score = min(self.days_since_change / 3.65, 100)

        # Bugs: 0-10 mapped to 0-100 (more bugs is worse)
        self.bug_score = min(self.bug_count * 10, 100)

        # Calculate weighted total
        weighted_score = (
            self.complexity_score * METRIC_WEIGHTS[DebtCategory.COMPLEXITY] +
            self.duplication_score * METRIC_WEIGHTS[DebtCategory.DUPLICATION] +
            self.coverage_score * METRIC_WEIGHTS[DebtCategory.TEST_COVERAGE] +
            self.dependency_score * METRIC_WEIGHTS[DebtCategory.DEPENDENCIES] +
            self.staleness_score * METRIC_WEIGHTS[DebtCategory.STALENESS] +
            self.bug_score * METRIC_WEIGHTS[DebtCategory.BUG_HISTORY]
        )

        self.debt_score = DebtScore.from_score(weighted_score)
        self.debt_score.factors = {
            "complexity": self.complexity_score,
            "duplication": self.duplication_score,
            "coverage": self.coverage_score,
            "dependencies": self.dependency_score,
            "staleness": self.staleness_score,
            "bugs": self.bug_score,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "file_path": self.file_path,
            "relative_path": self.relative_path,
            "filename": self.filename,
            "debt_score": self.debt_score.raw_score if self.debt_score else 0,
            "debt_level": self.debt_score.level.value if self.debt_score else "minimal",
            "lines_of_code": self.lines_of_code,
            "language": self.language,
            "metrics": {
                "cyclomatic_complexity": self.cyclomatic_complexity,
                "duplication_percentage": self.duplication_percentage,
                "test_coverage_percentage": self.test_coverage_percentage,
                "dependency_count": self.dependency_count,
                "days_since_change": self.days_since_change,
                "bug_count": self.bug_count,
            },
            "scores": {
                "complexity": self.complexity_score,
                "duplication": self.duplication_score,
                "coverage": self.coverage_score,
                "dependencies": self.dependency_score,
                "staleness": self.staleness_score,
                "bugs": self.bug_score,
            },
            "factors": self.debt_score.factors if self.debt_score else {},
        }


@dataclass
class ModuleDebtMetrics:
    """Technical debt metrics for a module/directory."""
    module_path: str
    module_name: str
    debt_score: DebtScore
    file_count: int
    total_loc: int

    # Aggregated metrics
    avg_complexity: float = 0.0
    avg_duplication: float = 0.0
    avg_coverage: float = 0.0
    total_dependencies: int = 0
    avg_staleness: float = 0.0
    total_bugs: int = 0

    # Child data
    high_debt_files: List[str] = field(default_factory=list)
    files: List[FileDebtMetrics] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "module_path": self.module_path,
            "module_name": self.module_name,
            "debt_score": self.debt_score.raw_score,
            "debt_level": self.debt_score.level.value,
            "file_count": self.file_count,
            "total_loc": self.total_loc,
            "aggregated_metrics": {
                "avg_complexity": round(self.avg_complexity, 2),
                "avg_duplication": round(self.avg_duplication, 2),
                "avg_coverage": round(self.avg_coverage, 2),
                "total_dependencies": self.total_dependencies,
                "avg_staleness_days": round(self.avg_staleness, 1),
                "total_bugs": self.total_bugs,
            },
            "high_debt_files": self.high_debt_files[:5],
            "files": [f.to_dict() for f in self.files],
        }


@dataclass
class HeatMapCell:
    """Single cell in technical debt heat map grid."""
    x: int
    y: int
    label: str
    debt_score: float
    debt_level: DebtLevel
    file_count: int
    total_loc: int
    tooltip: str = ""
    dominant_issue: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "label": self.label,
            "value": self.debt_score,
            "level": self.debt_level.value,
            "file_count": self.file_count,
            "total_loc": self.total_loc,
            "tooltip": self.tooltip,
            "dominant_issue": self.dominant_issue,
        }


@dataclass
class TechnicalDebtHeatMap:
    """Complete technical debt heat map."""
    project_path: str
    generated_at: datetime
    overall_debt: DebtScore
    total_files: int
    total_loc: int

    # Distribution by debt level
    files_by_debt_level: Dict[str, int] = field(default_factory=dict)

    # Distribution by category
    debt_by_category: Dict[str, float] = field(default_factory=dict)

    # Detailed data
    file_metrics: List[FileDebtMetrics] = field(default_factory=list)
    module_metrics: List[ModuleDebtMetrics] = field(default_factory=list)
    heat_map_grid: List[HeatMapCell] = field(default_factory=list)

    # Hotspots
    hotspots: List[FileDebtMetrics] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API/visualization."""
        return {
            "project_path": self.project_path,
            "generated_at": self.generated_at.isoformat(),
            "summary": {
                "overall_debt_score": round(self.overall_debt.raw_score, 1),
                "overall_debt_level": self.overall_debt.level.value,
                "total_files": self.total_files,
                "total_loc": self.total_loc,
            },
            "distribution": {
                "by_debt_level": self.files_by_debt_level,
                "by_category": {k: round(v, 1) for k, v in self.debt_by_category.items()},
            },
            "hotspots": [f.to_dict() for f in self.hotspots[:10]],
            "modules": [m.to_dict() for m in self.module_metrics],
            "heat_map": [c.to_dict() for c in self.heat_map_grid],
        }

    def to_d3_treemap(self) -> Dict[str, Any]:
        """Convert to D3.js treemap format."""
        return {
            "name": Path(self.project_path).name,
            "children": self._build_treemap_hierarchy(),
            "metadata": {
                "generated_at": self.generated_at.isoformat(),
                "overall_debt": self.overall_debt.raw_score,
                "metric_weights": {k.value: v for k, v in METRIC_WEIGHTS.items()},
            },
        }

    def _build_treemap_hierarchy(self) -> List[Dict[str, Any]]:
        """Build D3.js treemap hierarchy from modules."""
        children = []

        for module in self.module_metrics:
            module_node = {
                "name": module.module_name,
                "debt_score": module.debt_score.raw_score,
                "debt_level": module.debt_score.level.value,
                "children": [
                    {
                        "name": f.filename,
                        "value": f.lines_of_code or 1,
                        "debt_score": f.debt_score.raw_score if f.debt_score else 0,
                        "debt_level": f.debt_score.level.value if f.debt_score else "minimal",
                    }
                    for f in module.files
                ],
            }
            children.append(module_node)

        return children


class TechnicalDebtHeatMapService:
    """
    Service for generating technical debt heat maps.

    Combines multiple debt metrics into a visual heat map:
    - Cyclomatic complexity (25%)
    - Code duplication (20%)
    - Test coverage (20%)
    - Dependency count (15%)
    - Staleness (10%)
    - Bug history (10%)
    """

    def __init__(
        self,
        metric_weights: Optional[Dict[DebtCategory, float]] = None,
    ):
        """
        Initialize service.

        Args:
            metric_weights: Custom weights for debt categories (must sum to 1.0)
        """
        self.metric_weights = metric_weights or METRIC_WEIGHTS

        # Validate weights sum to 1.0
        total = sum(self.metric_weights.values())
        if abs(total - 1.0) > 0.001:
            logger.warning(f"Metric weights sum to {total}, normalizing...")
            self.metric_weights = {
                k: v / total for k, v in self.metric_weights.items()
            }

    def generate_heat_map(
        self,
        file_metrics: List[Dict[str, Any]],
        project_path: str = "",
    ) -> TechnicalDebtHeatMap:
        """
        Generate technical debt heat map from file metrics.

        Args:
            file_metrics: List of dicts with metrics per file:
                - file_path: str
                - cyclomatic_complexity: float
                - duplication_percentage: float
                - test_coverage_percentage: float
                - dependency_count: int
                - days_since_change: int
                - bug_count: int
                - lines_of_code: int (optional)
                - language: str (optional)
            project_path: Project root path for relative paths

        Returns:
            Complete heat map data
        """
        # Convert to FileDebtMetrics and calculate scores
        debt_files = []

        for metrics in file_metrics:
            file_path = metrics.get("file_path", "")
            try:
                relative_path = str(Path(file_path).relative_to(project_path)) if project_path else file_path
            except ValueError:
                relative_path = file_path

            file_debt = FileDebtMetrics(
                file_path=file_path,
                relative_path=relative_path,
                filename=Path(file_path).name,
                cyclomatic_complexity=metrics.get("cyclomatic_complexity", 0),
                duplication_percentage=metrics.get("duplication_percentage", 0),
                test_coverage_percentage=metrics.get("test_coverage_percentage", 100),
                dependency_count=metrics.get("dependency_count", 0),
                days_since_change=metrics.get("days_since_change", 0),
                bug_count=metrics.get("bug_count", 0),
                lines_of_code=metrics.get("lines_of_code", 0),
                language=metrics.get("language", ""),
            )

            file_debt.calculate_scores()
            debt_files.append(file_debt)

        # Calculate module metrics
        module_metrics = self._calculate_module_metrics(debt_files)

        # Calculate overall debt
        overall_debt = self._calculate_overall_debt(debt_files)

        # Generate heat map grid
        heat_map_grid = self._generate_grid(module_metrics)

        # Get distributions
        files_by_level = self._count_by_debt_level(debt_files)
        debt_by_category = self._calculate_category_averages(debt_files)

        # Get hotspots (top 10 highest debt files)
        hotspots = sorted(
            debt_files,
            key=lambda f: f.debt_score.raw_score if f.debt_score else 0,
            reverse=True,
        )[:10]

        return TechnicalDebtHeatMap(
            project_path=project_path,
            generated_at=datetime.now(timezone.utc),
            overall_debt=overall_debt,
            total_files=len(debt_files),
            total_loc=sum(f.lines_of_code for f in debt_files),
            files_by_debt_level=files_by_level,
            debt_by_category=debt_by_category,
            file_metrics=debt_files,
            module_metrics=module_metrics,
            heat_map_grid=heat_map_grid,
            hotspots=hotspots,
        )

    def _calculate_module_metrics(
        self,
        file_metrics: List[FileDebtMetrics],
    ) -> List[ModuleDebtMetrics]:
        """Calculate debt metrics per module/directory."""
        # Group by directory
        files_by_module: Dict[str, List[FileDebtMetrics]] = defaultdict(list)

        for file_metric in file_metrics:
            module_path = str(Path(file_metric.file_path).parent)
            files_by_module[module_path].append(file_metric)

        module_metrics = []

        for module_path, files in files_by_module.items():
            if not files:
                continue

            # Calculate aggregated metrics
            avg_complexity = sum(f.cyclomatic_complexity for f in files) / len(files)
            avg_duplication = sum(f.duplication_percentage for f in files) / len(files)
            avg_coverage = sum(f.test_coverage_percentage for f in files) / len(files)
            total_deps = sum(f.dependency_count for f in files)
            avg_staleness = sum(f.days_since_change for f in files) / len(files)
            total_bugs = sum(f.bug_count for f in files)

            # Calculate module debt score (weighted average of file scores)
            file_scores = [f.debt_score.raw_score for f in files if f.debt_score]
            if file_scores:
                # Use weighted average favoring worst files
                max_score = max(file_scores)
                avg_score = sum(file_scores) / len(file_scores)
                module_score = (avg_score * 0.4) + (max_score * 0.6)
            else:
                module_score = 0

            # High debt files
            high_debt = [
                f.filename for f in files
                if f.debt_score and f.debt_score.level in (DebtLevel.CRITICAL, DebtLevel.HIGH)
            ]

            module_metrics.append(ModuleDebtMetrics(
                module_path=module_path,
                module_name=Path(module_path).name or "root",
                debt_score=DebtScore.from_score(module_score),
                file_count=len(files),
                total_loc=sum(f.lines_of_code for f in files),
                avg_complexity=avg_complexity,
                avg_duplication=avg_duplication,
                avg_coverage=avg_coverage,
                total_dependencies=total_deps,
                avg_staleness=avg_staleness,
                total_bugs=total_bugs,
                high_debt_files=high_debt[:5],
                files=files,
            ))

        # Sort by debt score descending
        module_metrics.sort(key=lambda m: m.debt_score.raw_score, reverse=True)

        return module_metrics

    def _calculate_overall_debt(
        self,
        file_metrics: List[FileDebtMetrics],
    ) -> DebtScore:
        """Calculate overall project debt score."""
        if not file_metrics:
            return DebtScore.from_score(0)

        # Weighted average with higher weight for higher debt files
        total_weight = 0
        weighted_sum = 0

        for file_metric in file_metrics:
            if file_metric.debt_score:
                weight = 1 + (file_metric.debt_score.raw_score / 100)
                weighted_sum += file_metric.debt_score.raw_score * weight
                total_weight += weight

        avg_score = weighted_sum / total_weight if total_weight > 0 else 0

        return DebtScore.from_score(avg_score)

    def _generate_grid(
        self,
        module_metrics: List[ModuleDebtMetrics],
        max_cells: int = 50,
    ) -> List[HeatMapCell]:
        """Generate heat map grid for visualization."""
        cells = []

        for y, module in enumerate(module_metrics[:10]):  # Top 10 modules
            for x, file_metric in enumerate(module.files[:5]):  # Top 5 files per module
                # Find dominant issue
                if file_metric.debt_score and file_metric.debt_score.factors:
                    factors = file_metric.debt_score.factors
                    dominant = max(factors.items(), key=lambda x: x[1])
                    dominant_issue = dominant[0]
                else:
                    dominant_issue = "unknown"

                cells.append(HeatMapCell(
                    x=x,
                    y=y,
                    label=file_metric.filename,
                    debt_score=file_metric.debt_score.raw_score if file_metric.debt_score else 0,
                    debt_level=file_metric.debt_score.level if file_metric.debt_score else DebtLevel.MINIMAL,
                    file_count=1,
                    total_loc=file_metric.lines_of_code,
                    tooltip=f"{file_metric.relative_path}: {file_metric.debt_score.raw_score:.1f} debt score" if file_metric.debt_score else "",
                    dominant_issue=dominant_issue,
                ))

        return cells[:max_cells]

    def _count_by_debt_level(
        self,
        file_metrics: List[FileDebtMetrics],
    ) -> Dict[str, int]:
        """Count files by debt level."""
        counts = {level.value: 0 for level in DebtLevel}

        for file_metric in file_metrics:
            if file_metric.debt_score:
                counts[file_metric.debt_score.level.value] += 1

        return counts

    def _calculate_category_averages(
        self,
        file_metrics: List[FileDebtMetrics],
    ) -> Dict[str, float]:
        """Calculate average debt by category."""
        if not file_metrics:
            return {cat.value: 0.0 for cat in DebtCategory}

        totals = {
            DebtCategory.COMPLEXITY.value: sum(f.complexity_score for f in file_metrics),
            DebtCategory.DUPLICATION.value: sum(f.duplication_score for f in file_metrics),
            DebtCategory.TEST_COVERAGE.value: sum(f.coverage_score for f in file_metrics),
            DebtCategory.DEPENDENCIES.value: sum(f.dependency_score for f in file_metrics),
            DebtCategory.STALENESS.value: sum(f.staleness_score for f in file_metrics),
            DebtCategory.BUG_HISTORY.value: sum(f.bug_score for f in file_metrics),
        }

        count = len(file_metrics)
        return {k: v / count for k, v in totals.items()}

    def generate_summary_report(
        self,
        heat_map: TechnicalDebtHeatMap,
    ) -> Dict[str, Any]:
        """Generate executive summary report."""
        # Find dominant issue category
        category_avgs = heat_map.debt_by_category
        dominant_category = max(category_avgs.items(), key=lambda x: x[1]) if category_avgs else ("unknown", 0)

        return {
            "executive_summary": {
                "overall_debt_level": heat_map.overall_debt.level.value,
                "debt_score": round(heat_map.overall_debt.raw_score, 1),
                "total_files_analyzed": heat_map.total_files,
                "total_lines_of_code": heat_map.total_loc,
                "critical_files": heat_map.files_by_debt_level.get("critical", 0),
                "high_debt_files": heat_map.files_by_debt_level.get("high", 0),
            },
            "key_findings": {
                "dominant_issue": dominant_category[0],
                "dominant_issue_score": round(dominant_category[1], 1),
                "top_3_hotspots": [
                    {
                        "file": h.relative_path,
                        "debt_score": round(h.debt_score.raw_score, 1) if h.debt_score else 0,
                        "dominant_factor": max(
                            h.debt_score.factors.items(),
                            key=lambda x: x[1]
                        )[0] if h.debt_score and h.debt_score.factors else "unknown",
                    }
                    for h in heat_map.hotspots[:3]
                ],
            },
            "recommendations": self._generate_recommendations(heat_map),
            "metric_breakdown": {
                cat.value: {
                    "weight": f"{METRIC_WEIGHTS[cat]*100:.0f}%",
                    "avg_score": round(category_avgs.get(cat.value, 0), 1),
                }
                for cat in DebtCategory
            },
        }

    def _generate_recommendations(
        self,
        heat_map: TechnicalDebtHeatMap,
    ) -> List[str]:
        """Generate debt-based recommendations."""
        recommendations = []
        category_avgs = heat_map.debt_by_category

        # Based on category scores
        if category_avgs.get(DebtCategory.COMPLEXITY.value, 0) > 60:
            recommendations.append(
                "HIGH COMPLEXITY: Refactor complex methods with cyclomatic complexity > 15. "
                "Consider extracting smaller functions and reducing nested conditionals."
            )

        if category_avgs.get(DebtCategory.DUPLICATION.value, 0) > 50:
            recommendations.append(
                "CODE DUPLICATION: Extract duplicated code into shared utilities. "
                "Consider using the DRY principle and creating reusable modules."
            )

        if category_avgs.get(DebtCategory.TEST_COVERAGE.value, 0) > 60:
            recommendations.append(
                "LOW TEST COVERAGE: Increase test coverage, prioritizing critical business logic. "
                "Aim for 80%+ coverage on core modules."
            )

        if category_avgs.get(DebtCategory.DEPENDENCIES.value, 0) > 50:
            recommendations.append(
                "HIGH DEPENDENCY COUNT: Review module dependencies and reduce coupling. "
                "Consider dependency injection and interface-based design."
            )

        if category_avgs.get(DebtCategory.STALENESS.value, 0) > 50:
            recommendations.append(
                "STALE CODE: Review dormant code for potential removal or modernization. "
                "Code unchanged for 6+ months may need security updates."
            )

        if category_avgs.get(DebtCategory.BUG_HISTORY.value, 0) > 30:
            recommendations.append(
                "BUG HOTSPOTS: Focus testing and refactoring on files with high bug history. "
                "These areas are likely to have more defects."
            )

        # Based on hotspots
        if heat_map.hotspots:
            top_file = heat_map.hotspots[0]
            if top_file.debt_score and top_file.debt_score.raw_score > 70:
                recommendations.append(
                    f"PRIORITY: Address {top_file.relative_path} - "
                    f"highest debt score ({top_file.debt_score.raw_score:.1f})"
                )

        return recommendations or ["Technical debt levels are acceptable - maintain current practices"]


def create_technical_debt_heatmap_service() -> TechnicalDebtHeatMapService:
    """Factory function to create Technical Debt Heatmap service."""
    return TechnicalDebtHeatMapService()
