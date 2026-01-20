"""
Balance Analyzer - Component Balance Analyzer

Week 126: Metrics Layer Integration
Wraps the Quality-Migration-Tools/06-component-balance-analyzer

Analyzes code distribution across components using Gini coefficient.

A well-balanced codebase has code distributed across multiple focused components
rather than concentrated in one or two large "God components".

5-Star Rating (lower Gini = better balance):
- 5 stars: Gini < 0.3 (well-balanced)
- 4 stars: Gini 0.3-0.4
- 3 stars: Gini 0.4-0.5
- 2 stars: Gini 0.5-0.6
- 1 star:  Gini > 0.6 (unbalanced, monolithic risk)
"""

import sys
import os
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

from ..base import (
    BaseScanner, ScanResult, ScanFinding, ScanMetrics,
    Severity, FindingType
)

logger = logging.getLogger(__name__)

# Path to quality analysis tools (configurable via QUALITY_TOOLS_PATH env var)
QUALITY_TOOLS_PATH = Path(os.environ.get("QUALITY_TOOLS_PATH", str(Path.home() / "Projects" / "Quality-Migration-Tools")))


class BalanceAnalyzer(BaseScanner):
    """
    Component balance analyzer wrapping component_balance_analyzer.py.

    Uses Gini coefficient to measure code distribution.
    Supports: C#, VB.NET, SQL, JavaScript, TypeScript
    """

    @property
    def name(self) -> str:
        return "balance"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supported_stacks(self) -> List[str]:
        return ['dotnet', 'csharp', 'vbnet', 'aspnet', 'javascript', 'typescript']

    @property
    def scanner_type(self) -> str:
        return "balance"

    def _calculate_rating(self, gini: float) -> int:
        """Calculate 5-star rating based on Gini coefficient"""
        if gini < 0.3:
            return 5
        elif gini < 0.4:
            return 4
        elif gini < 0.5:
            return 3
        elif gini < 0.6:
            return 2
        else:
            return 1

    def _get_rating_stars(self, rating: int) -> str:
        """Convert numeric rating to star string"""
        return '★' * rating + '☆' * (5 - rating)

    def _calculate_gini(self, values: List[int]) -> float:
        """
        Calculate Gini coefficient for distribution inequality.

        Gini = 0: Perfect equality (all components same size)
        Gini = 1: Perfect inequality (one component has everything)
        """
        if not values or sum(values) == 0:
            return 0.0

        n = len(values)
        if n == 1:
            return 0.0

        # Sort values
        sorted_values = sorted(values)
        cumulative = 0
        sum_of_products = 0

        for i, value in enumerate(sorted_values, 1):
            cumulative += value
            sum_of_products += i * value

        # Gini formula
        mean = sum(values) / n
        if mean == 0:
            return 0.0

        gini = (2 * sum_of_products) / (n * sum(values)) - (n + 1) / n
        return max(0, min(1, gini))  # Clamp to [0, 1]

    def _count_loc(self, file_path: Path) -> int:
        """Count lines of code in a file (excluding comments and blank lines)"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return 0

        ext = file_path.suffix.lower()

        # Remove comments based on language
        if ext in ['.cs', '.js', '.ts']:
            content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        elif ext == '.vb':
            content = re.sub(r"'.*$", '', content, flags=re.MULTILINE)
        elif ext == '.sql':
            content = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

        # Count non-blank lines
        lines = [line.strip() for line in content.split('\n')]
        return sum(1 for line in lines if line)

    def _get_component_name(self, file_path: Path, root_path: Path) -> str:
        """Determine component name from file path"""
        try:
            relative_path = file_path.relative_to(root_path)
            parts = relative_path.parts

            if len(parts) == 1:
                return "Root"

            # First directory is the component
            component = parts[0]

            # Skip build/dependency folders
            if component.lower() in {'bin', 'obj', 'packages', 'node_modules', '.git', '.vs'}:
                return None

            return component
        except ValueError:
            return "External"

    async def scan(self) -> ScanResult:
        """Execute the balance analysis"""
        started_at = datetime.now()
        findings: List[ScanFinding] = []

        # Component tracking: {name: {'loc': int, 'files': int, 'languages': set}}
        components: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'loc': 0, 'files': 0, 'languages': set()
        })

        files_scanned = 0
        total_loc = 0

        extensions = {'.cs', '.vb', '.sql', '.js', '.ts'}
        excluded_dirs = {
            'bin', 'obj', 'node_modules', '.git', '.vs', 'packages',
            'TestResults', 'Debug', 'Release', '.nuget', '__pycache__',
            'bower_components', 'vendor', 'dist', 'build', '.venv', 'venv'
        }

        try:
            for root, dirs, files in os.walk(self.project_path):
                dirs[:] = [d for d in dirs if d not in excluded_dirs]
                root_path = Path(root)

                for filename in files:
                    file_path = root_path / filename
                    ext = file_path.suffix.lower()

                    if ext not in extensions:
                        continue

                    component_name = self._get_component_name(file_path, self.project_path)
                    if component_name is None:
                        continue

                    loc = self._count_loc(file_path)
                    if loc == 0:
                        continue

                    files_scanned += 1
                    total_loc += loc

                    components[component_name]['loc'] += loc
                    components[component_name]['files'] += 1
                    components[component_name]['languages'].add(ext)

            # Calculate metrics
            component_locs = [c['loc'] for c in components.values()]
            gini = self._calculate_gini(component_locs)
            rating = self._calculate_rating(gini)
            rating_stars = self._get_rating_stars(rating)

            # Find "God components" (> 30% of codebase)
            god_components = []
            for name, data in components.items():
                pct = (data['loc'] / total_loc * 100) if total_loc > 0 else 0
                if pct > 30:
                    god_components.append({
                        "name": name,
                        "loc": data['loc'],
                        "percentage": round(pct, 2)
                    })

                    findings.append(ScanFinding(
                        scanner=self.name,
                        rule_id="god-component",
                        message=f"Component '{name}' contains {pct:.1f}% of codebase ({data['loc']:,} LOC)",
                        severity=Severity.MEDIUM if pct < 50 else Severity.HIGH,
                        finding_type=FindingType.ARCHITECTURE,
                        file_path=name,
                        recommendation="Consider breaking down this component into smaller, "
                                      "more focused modules. Target: < 30% of codebase per component.",
                        effort_minutes=data['loc'] // 100,  # Rough estimate
                        metadata={
                            "loc": data['loc'],
                            "percentage": round(pct, 2),
                            "files": data['files']
                        }
                    ))

            # Sort components by size
            sorted_components = sorted(
                [
                    {
                        "name": name,
                        "loc": data['loc'],
                        "files": data['files'],
                        "percentage": round((data['loc'] / total_loc * 100) if total_loc > 0 else 0, 2),
                        "languages": list(data['languages'])
                    }
                    for name, data in components.items()
                ],
                key=lambda x: x['loc'],
                reverse=True
            )

            # Calculate top-3 concentration
            top_3_pct = sum(c['percentage'] for c in sorted_components[:3])

            # Build metrics
            metrics = ScanMetrics(
                files_scanned=files_scanned,
                lines_of_code=total_loc,
            )

            metrics.metadata = {
                "rating": rating,
                "rating_stars": rating_stars,
                "gini_coefficient": round(gini, 3),
                "total_components": len(components),
                "total_loc": total_loc,
                "largest_component_pct": sorted_components[0]['percentage'] if sorted_components else 0,
                "top_3_components_pct": round(top_3_pct, 2),
                "god_components": god_components,
                "components": sorted_components[:20]  # Top 20 only
            }

            completed_at = datetime.now()

            logger.info(
                f"Balance scan complete: {len(components)} components, "
                f"Gini: {gini:.3f}, rating: {rating_stars}"
            )

            return ScanResult(
                scanner_name=self.name,
                scanner_version=self.version,
                stack="multi",
                project_path=str(self.project_path),
                started_at=started_at,
                completed_at=completed_at,
                success=True,
                findings=findings,
                metrics=metrics
            )

        except Exception as e:
            logger.error(f"Balance scan failed: {e}")
            return ScanResult(
                scanner_name=self.name,
                scanner_version=self.version,
                stack="multi",
                project_path=str(self.project_path),
                started_at=started_at,
                completed_at=datetime.now(),
                success=False,
                error_message=str(e)
            )

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "gini_threshold": 0.5,
            "god_component_threshold": 30,  # percentage
            "quality_tools_path": str(QUALITY_TOOLS_PATH),
        }
