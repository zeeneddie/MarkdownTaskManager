"""
Coupling Analyzer - Module Coupling Analyzer

Week 126: Metrics Layer Integration
Wraps the Quality-Migration-Tools/05-module-coupling-analyzer

Analyzes module dependencies: fan-in, fan-out, instability index.

Instability Index = Ce / (Ce + Ca)
Where:
- Ce = Efferent coupling (dependencies TO other modules)
- Ca = Afferent coupling (dependencies FROM other modules)

5-Star Rating (lower instability = more stable):
- 5 stars: I < 0.3 (stable, low change risk)
- 4 stars: I 0.3-0.4
- 3 stars: I 0.4-0.5
- 2 stars: I 0.5-0.7
- 1 star:  I > 0.7 (unstable, high change propagation)
"""

import sys
import os
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Set
from collections import defaultdict

from ..base import (
    BaseScanner, ScanResult, ScanFinding, ScanMetrics,
    Severity, FindingType
)

logger = logging.getLogger(__name__)

# Path to quality analysis tools (configurable via QUALITY_TOOLS_PATH env var)
QUALITY_TOOLS_PATH = Path(os.environ.get("QUALITY_TOOLS_PATH", str(Path.home() / "Projects" / "Quality-Migration-Tools")))


class CouplingAnalyzer(BaseScanner):
    """
    Module coupling analyzer wrapping module_coupling_analyzer.py.

    Calculates fan-in, fan-out, and instability metrics.
    Supports: C#, VB.NET, JavaScript, TypeScript, SQL
    """

    @property
    def name(self) -> str:
        return "coupling"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supported_stacks(self) -> List[str]:
        return ['dotnet', 'csharp', 'vbnet', 'aspnet', 'javascript', 'typescript']

    @property
    def scanner_type(self) -> str:
        return "coupling"

    def _calculate_rating(self, avg_instability: float) -> int:
        """Calculate 5-star rating based on average instability"""
        if avg_instability < 0.3:
            return 5
        elif avg_instability < 0.4:
            return 4
        elif avg_instability < 0.5:
            return 3
        elif avg_instability < 0.7:
            return 2
        else:
            return 1

    def _get_rating_stars(self, rating: int) -> str:
        """Convert numeric rating to star string"""
        return '★' * rating + '☆' * (5 - rating)

    async def scan(self) -> ScanResult:
        """Execute the coupling analysis"""
        started_at = datetime.now()
        findings: List[ScanFinding] = []

        # Dependencies tracking
        dependencies: Dict[str, Set[str]] = defaultdict(set)  # file -> set of dependencies
        reverse_deps: Dict[str, Set[str]] = defaultdict(set)  # file -> set of dependents

        files_scanned = 0
        total_loc = 0

        # Import patterns by extension
        import_patterns = {
            '.cs': r'^\s*using\s+([\w\.]+)\s*;',
            '.vb': r'^\s*Imports\s+([\w\.]+)\s*$',
            '.js': r'(?:import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]|require\s*\([\'"]([^\'"]+)[\'"]\))',
            '.ts': r'(?:import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]|require\s*\([\'"]([^\'"]+)[\'"]\))',
        }

        excluded_dirs = {
            'bin', 'obj', 'node_modules', '.git', '.vs', 'packages',
            'TestResults', 'Debug', 'Release', '.nuget', '__pycache__',
            'bower_components', 'vendor', 'dist', 'build', '.venv', 'venv'
        }

        # System namespaces to ignore
        system_prefixes = {'System', 'Microsoft', 'Newtonsoft', 'NLog', 'log4net'}

        try:
            for root, dirs, files in os.walk(self.project_path):
                dirs[:] = [d for d in dirs if d not in excluded_dirs]
                root_path = Path(root)

                for filename in files:
                    file_path = root_path / filename
                    ext = file_path.suffix.lower()

                    if ext not in import_patterns:
                        continue

                    files_scanned += 1
                    rel_path = str(file_path.relative_to(self.project_path))

                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            total_loc += len(content.split('\n'))
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")
                        continue

                    # Find imports/dependencies
                    pattern = import_patterns[ext]
                    flags = re.IGNORECASE if ext == '.vb' else 0

                    for match in re.finditer(pattern, content, re.MULTILINE | flags):
                        dep = match.group(1) or (match.group(2) if match.lastindex >= 2 else None)
                        if not dep:
                            continue

                        # Skip system dependencies
                        if any(dep.startswith(prefix) for prefix in system_prefixes):
                            continue

                        # Skip relative path self-references
                        if dep.startswith('.'):
                            continue

                        # Record dependency
                        dependencies[rel_path].add(dep)
                        reverse_deps[dep].add(rel_path)

            # Calculate metrics per module
            module_metrics: List[Dict[str, Any]] = []
            total_instability = 0
            high_coupling_count = 0

            all_modules = set(dependencies.keys()) | set(reverse_deps.keys())

            for module in all_modules:
                ce = len(dependencies.get(module, set()))  # Fan-out (efferent)
                ca = len(reverse_deps.get(module, set()))  # Fan-in (afferent)

                # Instability index
                instability = ce / (ce + ca) if (ce + ca) > 0 else 0

                module_metrics.append({
                    "module": module,
                    "fan_out": ce,
                    "fan_in": ca,
                    "instability": round(instability, 3)
                })

                total_instability += instability

                # Track high coupling
                if ce > 10:
                    high_coupling_count += 1

                    findings.append(ScanFinding(
                        scanner=self.name,
                        rule_id="high-coupling",
                        message=f"Module has high efferent coupling: {ce} dependencies",
                        severity=Severity.MEDIUM if ce < 20 else Severity.HIGH,
                        finding_type=FindingType.ARCHITECTURE,
                        file_path=module,
                        recommendation="Consider reducing dependencies. High coupling makes "
                                      "changes more risky and testing harder.",
                        effort_minutes=ce * 10,
                        metadata={
                            "fan_out": ce,
                            "fan_in": ca,
                            "instability": round(instability, 3)
                        }
                    ))

            # Sort by instability (most unstable first)
            module_metrics.sort(key=lambda x: x['instability'], reverse=True)

            # Calculate averages
            module_count = len(all_modules)
            avg_instability = total_instability / module_count if module_count > 0 else 0
            avg_fan_out = sum(len(deps) for deps in dependencies.values()) / files_scanned if files_scanned > 0 else 0
            avg_fan_in = sum(len(deps) for deps in reverse_deps.values()) / module_count if module_count > 0 else 0

            rating = self._calculate_rating(avg_instability)
            rating_stars = self._get_rating_stars(rating)

            # Build metrics
            metrics = ScanMetrics(
                files_scanned=files_scanned,
                lines_of_code=total_loc,
            )

            metrics.metadata = {
                "rating": rating,
                "rating_stars": rating_stars,
                "total_modules": module_count,
                "total_dependencies": sum(len(deps) for deps in dependencies.values()),
                "average_fan_out": round(avg_fan_out, 2),
                "average_fan_in": round(avg_fan_in, 2),
                "average_instability": round(avg_instability, 3),
                "high_coupling_count": high_coupling_count,
                "most_unstable_modules": module_metrics[:10],
                "dependency_graph": {
                    module: list(deps)
                    for module, deps in list(dependencies.items())[:50]  # Limit size
                }
            }

            completed_at = datetime.now()

            logger.info(
                f"Coupling scan complete: {module_count} modules, "
                f"avg instability: {avg_instability:.3f}, rating: {rating_stars}"
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
            logger.error(f"Coupling scan failed: {e}")
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
            "instability_threshold": 0.5,
            "fan_out_threshold": 10,
            "quality_tools_path": str(QUALITY_TOOLS_PATH),
        }
