"""
Complexity Dashboard Service - Fase 24: A5

Module-level complexity aggregation for BROWN_PAPER and MAINTENANCE workflows.
Builds on existing ComplexityAnalyzer to provide:
- Module/namespace grouping
- Trend tracking
- Dashboard-ready data
- Hotspot identification

Author: Claude Code (Week 140 - Fase 24)
Date: 2026-01-18
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re
import os
from collections import defaultdict

logger = logging.getLogger(__name__)


class ModuleHealthStatus(Enum):
    """Health status for a module based on complexity metrics."""
    HEALTHY = "healthy"           # Avg complexity < 10
    WARNING = "warning"           # Avg complexity 10-20
    AT_RISK = "at_risk"           # Avg complexity 20-30
    CRITICAL = "critical"         # Avg complexity > 30


class TrendDirection(Enum):
    """Trend direction for complexity changes."""
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"


@dataclass
class FileComplexity:
    """Complexity metrics for a single file."""
    file_path: str
    cyclomatic_complexity: int
    cognitive_complexity: int
    lines_of_code: int
    function_count: int
    max_function_complexity: int
    high_complexity_functions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "cognitive_complexity": self.cognitive_complexity,
            "lines_of_code": self.lines_of_code,
            "function_count": self.function_count,
            "max_function_complexity": self.max_function_complexity,
            "high_complexity_functions": self.high_complexity_functions,
        }


@dataclass
class ModuleComplexity:
    """Aggregated complexity metrics for a module/namespace."""
    module_path: str
    module_name: str
    file_count: int
    total_lines: int
    total_cyclomatic: int
    total_cognitive: int
    total_functions: int
    max_file_complexity: int
    max_function_complexity: int
    files: List[FileComplexity] = field(default_factory=list)
    hotspot_files: List[str] = field(default_factory=list)

    @property
    def avg_cyclomatic(self) -> float:
        return self.total_cyclomatic / max(self.file_count, 1)

    @property
    def avg_cognitive(self) -> float:
        return self.total_cognitive / max(self.file_count, 1)

    @property
    def health_status(self) -> ModuleHealthStatus:
        avg = self.avg_cyclomatic
        if avg < 10:
            return ModuleHealthStatus.HEALTHY
        elif avg < 20:
            return ModuleHealthStatus.WARNING
        elif avg < 30:
            return ModuleHealthStatus.AT_RISK
        else:
            return ModuleHealthStatus.CRITICAL

    @property
    def complexity_density(self) -> float:
        """Complexity per 100 lines of code."""
        return (self.total_cyclomatic / max(self.total_lines, 1)) * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_path": self.module_path,
            "module_name": self.module_name,
            "file_count": self.file_count,
            "total_lines": self.total_lines,
            "avg_cyclomatic": round(self.avg_cyclomatic, 2),
            "avg_cognitive": round(self.avg_cognitive, 2),
            "total_functions": self.total_functions,
            "max_file_complexity": self.max_file_complexity,
            "max_function_complexity": self.max_function_complexity,
            "health_status": self.health_status.value,
            "complexity_density": round(self.complexity_density, 2),
            "hotspot_files": self.hotspot_files,
            "files": [f.to_dict() for f in self.files],
        }


@dataclass
class ComplexitySnapshot:
    """Point-in-time complexity snapshot for trend tracking."""
    timestamp: datetime
    total_complexity: int
    avg_complexity: float
    module_count: int
    file_count: int
    hotspot_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_complexity": self.total_complexity,
            "avg_complexity": round(self.avg_complexity, 2),
            "module_count": self.module_count,
            "file_count": self.file_count,
            "hotspot_count": self.hotspot_count,
        }


@dataclass
class ComplexityTrend:
    """Trend analysis based on historical snapshots."""
    direction: TrendDirection
    change_percentage: float
    snapshots: List[ComplexitySnapshot]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction.value,
            "change_percentage": round(self.change_percentage, 2),
            "snapshots": [s.to_dict() for s in self.snapshots],
        }


@dataclass
class ComplexityDashboardResult:
    """Complete complexity dashboard data."""
    scan_timestamp: datetime
    project_path: str
    modules: List[ModuleComplexity]
    summary: Dict[str, Any]
    hotspots: List[Dict[str, Any]]
    distribution: Dict[str, int]
    recommendations: List[str]
    trend: Optional[ComplexityTrend] = None

    def __post_init__(self):
        """Calculate summary statistics."""
        total_files = sum(m.file_count for m in self.modules)
        total_complexity = sum(m.total_cyclomatic for m in self.modules)
        total_lines = sum(m.total_lines for m in self.modules)

        health_counts = defaultdict(int)
        for m in self.modules:
            health_counts[m.health_status.value] += 1

        self.summary = {
            "total_modules": len(self.modules),
            "total_files": total_files,
            "total_lines": total_lines,
            "total_complexity": total_complexity,
            "avg_complexity": round(total_complexity / max(total_files, 1), 2),
            "health_distribution": dict(health_counts),
            "hotspot_count": len(self.hotspots),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scan_timestamp": self.scan_timestamp.isoformat(),
            "project_path": self.project_path,
            "summary": self.summary,
            "modules": [m.to_dict() for m in self.modules],
            "hotspots": self.hotspots,
            "distribution": self.distribution,
            "recommendations": self.recommendations,
            "trend": self.trend.to_dict() if self.trend else None,
        }


class ComplexityDashboardService:
    """
    Provides module-level complexity aggregation for dashboards.

    Integrates with:
    - BROWN_PAPER: Migration complexity assessment
    - MAINTENANCE: Ongoing code health monitoring
    - BUG: Hotspot identification for root cause analysis

    Features:
    - Module/namespace grouping
    - Hotspot identification
    - Trend tracking
    - Actionable recommendations
    """

    # File extensions by language
    LANGUAGE_EXTENSIONS: Dict[str, List[str]] = {
        "python": [".py"],
        "javascript": [".js", ".jsx", ".mjs"],
        "typescript": [".ts", ".tsx"],
        "csharp": [".cs"],
        "java": [".java"],
        "vbnet": [".vb"],
        "sql": [".sql"],
        "asp": [".asp", ".aspx"],
        "go": [".go"],
        "rust": [".rs"],
        "php": [".php"],
        "ruby": [".rb"],
    }

    # Directories to exclude
    EXCLUDED_DIRS = {
        'bin', 'obj', 'node_modules', '.git', '.vs', 'packages',
        'TestResults', 'Debug', 'Release', '.nuget', '__pycache__',
        'bower_components', 'vendor', 'dist', 'build', '.venv', 'venv',
        'coverage', '.idea', '.vscode', 'target', '.pytest_cache',
    }

    # Complexity thresholds
    HOTSPOT_THRESHOLD = 25  # Files with complexity > this are hotspots
    HIGH_FUNCTION_THRESHOLD = 15  # Functions with complexity > this are flagged

    def __init__(self, project_path: Optional[str] = None):
        """
        Initialize the complexity dashboard service.

        Args:
            project_path: Optional root path for analysis
        """
        self.project_path = project_path
        self._history: List[ComplexitySnapshot] = []

    def analyze_project(
        self,
        project_path: Optional[str] = None,
        languages: Optional[List[str]] = None,
        module_depth: int = 2
    ) -> ComplexityDashboardResult:
        """
        Analyze entire project and generate dashboard data.

        Args:
            project_path: Path to analyze (uses self.project_path if not provided)
            languages: Languages to include (all if None)
            module_depth: Directory depth for module grouping (default 2)

        Returns:
            ComplexityDashboardResult with aggregated metrics
        """
        path = Path(project_path or self.project_path)
        if not path.exists():
            raise ValueError(f"Project path does not exist: {path}")

        # Get extensions to analyze
        extensions = self._get_extensions(languages)

        # Analyze all files
        file_metrics: Dict[str, FileComplexity] = {}

        for root, dirs, files in os.walk(path):
            # Filter excluded directories
            dirs[:] = [d for d in dirs if d not in self.EXCLUDED_DIRS]
            root_path = Path(root)

            for filename in files:
                file_path = root_path / filename
                if file_path.suffix.lower() not in extensions:
                    continue

                try:
                    rel_path = str(file_path.relative_to(path))
                    metrics = self._analyze_file(file_path)
                    if metrics:
                        file_metrics[rel_path] = metrics
                except Exception as e:
                    logger.warning(f"Error analyzing {file_path}: {e}")

        # Group into modules
        modules = self._group_into_modules(file_metrics, module_depth)

        # Identify hotspots
        hotspots = self._identify_hotspots(file_metrics)

        # Calculate distribution
        distribution = self._calculate_distribution(file_metrics)

        # Generate recommendations
        recommendations = self._generate_recommendations(modules, hotspots)

        # Create snapshot for trend tracking
        snapshot = self._create_snapshot(modules, hotspots)
        self._history.append(snapshot)

        # Calculate trend if we have history
        trend = self._calculate_trend() if len(self._history) > 1 else None

        return ComplexityDashboardResult(
            scan_timestamp=datetime.now(timezone.utc),
            project_path=str(path),
            modules=modules,
            summary={},  # Will be calculated in __post_init__
            hotspots=hotspots,
            distribution=distribution,
            recommendations=recommendations,
            trend=trend,
        )

    def analyze_files(
        self,
        files: Dict[str, str],
        module_depth: int = 2
    ) -> ComplexityDashboardResult:
        """
        Analyze provided files (for integration with scan services).

        Args:
            files: Dict mapping file paths to content
            module_depth: Directory depth for module grouping

        Returns:
            ComplexityDashboardResult
        """
        file_metrics: Dict[str, FileComplexity] = {}

        for file_path, content in files.items():
            ext = Path(file_path).suffix.lower()
            all_extensions = {ext for exts in self.LANGUAGE_EXTENSIONS.values() for ext in exts}

            if ext not in all_extensions:
                continue

            try:
                metrics = self._analyze_content(content, file_path, ext)
                if metrics:
                    file_metrics[file_path] = metrics
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")

        modules = self._group_into_modules(file_metrics, module_depth)
        hotspots = self._identify_hotspots(file_metrics)
        distribution = self._calculate_distribution(file_metrics)
        recommendations = self._generate_recommendations(modules, hotspots)

        return ComplexityDashboardResult(
            scan_timestamp=datetime.now(timezone.utc),
            project_path="<provided files>",
            modules=modules,
            summary={},
            hotspots=hotspots,
            distribution=distribution,
            recommendations=recommendations,
        )

    def _get_extensions(self, languages: Optional[List[str]] = None) -> set:
        """Get file extensions for specified languages."""
        if languages is None:
            return {ext for exts in self.LANGUAGE_EXTENSIONS.values() for ext in exts}

        extensions = set()
        for lang in languages:
            lang_lower = lang.lower()
            if lang_lower in self.LANGUAGE_EXTENSIONS:
                extensions.update(self.LANGUAGE_EXTENSIONS[lang_lower])

        return extensions if extensions else {
            ext for exts in self.LANGUAGE_EXTENSIONS.values() for ext in exts
        }

    def _analyze_file(self, file_path: Path) -> Optional[FileComplexity]:
        """Analyze a single file from disk."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            return self._analyze_content(content, str(file_path), file_path.suffix.lower())
        except Exception as e:
            logger.debug(f"Could not analyze {file_path}: {e}")
            return None

    def _analyze_content(
        self,
        content: str,
        file_path: str,
        ext: str
    ) -> Optional[FileComplexity]:
        """Analyze content and calculate complexity metrics."""
        lines = content.split('\n')
        loc = len([l for l in lines if l.strip() and not l.strip().startswith(('#', '//', '/*', '*', '--'))])

        # Calculate cyclomatic complexity
        cyclomatic = self._calculate_cyclomatic(content, ext)

        # Calculate cognitive complexity (simplified)
        cognitive = self._calculate_cognitive(content, ext)

        # Count and analyze functions
        functions = self._extract_functions(content, ext)
        function_complexities = [self._calculate_cyclomatic(f['body'], ext) for f in functions]

        high_complexity_funcs = [
            f['name'] for f, c in zip(functions, function_complexities)
            if c > self.HIGH_FUNCTION_THRESHOLD
        ]

        max_func_complexity = max(function_complexities) if function_complexities else 0

        return FileComplexity(
            file_path=file_path,
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cognitive,
            lines_of_code=loc,
            function_count=len(functions),
            max_function_complexity=max_func_complexity,
            high_complexity_functions=high_complexity_funcs,
        )

    def _calculate_cyclomatic(self, content: str, ext: str) -> int:
        """Calculate cyclomatic complexity based on decision points."""
        complexity = 1  # Base complexity

        # Language-specific patterns
        if ext in ['.cs', '.js', '.ts', '.jsx', '.tsx', '.java']:
            patterns = [
                r'\bif\s*\(', r'\belse\s+if\s*\(', r'\bfor\s*\(',
                r'\bforeach\s*\(', r'\bwhile\s*\(', r'\bcase\s+[^:]+:',
                r'\bcatch\s*\(', r'\?\s*[^:]+:', r'&&', r'\|\|',
                r'\bswitch\s*\(',
            ]
        elif ext == '.py':
            patterns = [
                r'\bif\s+', r'\belif\s+', r'\bfor\s+', r'\bwhile\s+',
                r'\bexcept\s*[:\(]', r'\band\b', r'\bor\b',
                r'\bif\s+.*\belse\b',  # Ternary
            ]
        elif ext in ['.vb']:
            patterns = [
                r'\bIf\b', r'\bElseIf\b', r'\bFor\b', r'\bFor\s+Each\b',
                r'\bWhile\b', r'\bDo\s+While\b', r'\bDo\s+Until\b',
                r'\bSelect\s+Case\b', r'\bCase\s+\w+', r'\bCatch\b',
                r'\bAndAlso\b', r'\bOrElse\b',
            ]
        elif ext == '.sql':
            patterns = [
                r'\bIF\b', r'\bELSE\s+IF\b', r'\bWHILE\b',
                r'\bCASE\b', r'\bWHEN\b', r'\bAND\b', r'\bOR\b',
            ]
        elif ext in ['.go']:
            patterns = [
                r'\bif\s+', r'\belse\s+if\s+', r'\bfor\s+',
                r'\bswitch\s+', r'\bcase\s+', r'&&', r'\|\|',
            ]
        elif ext in ['.rs']:
            patterns = [
                r'\bif\s+', r'\belse\s+if\s+', r'\bfor\s+', r'\bwhile\s+',
                r'\bmatch\s+', r'=>', r'&&', r'\|\|',
            ]
        elif ext == '.php':
            patterns = [
                r'\bif\s*\(', r'\belseif\s*\(', r'\bfor\s*\(',
                r'\bforeach\s*\(', r'\bwhile\s*\(', r'\bcase\s+',
                r'\bcatch\s*\(', r'\?\s*:', r'&&', r'\|\|', r'\band\b', r'\bor\b',
            ]
        elif ext in ['.asp', '.aspx']:
            patterns = [
                r'\bIf\b', r'\bElseIf\b', r'\bFor\b', r'\bDo\s+While\b',
                r'\bSelect\s+Case\b', r'\bCase\b', r'\bAnd\b', r'\bOr\b',
            ]
        else:
            patterns = []

        flags = re.IGNORECASE if ext in ['.vb', '.asp', '.aspx', '.sql'] else 0

        for pattern in patterns:
            matches = re.findall(pattern, content, flags)
            complexity += len(matches)

        return complexity

    def _calculate_cognitive(self, content: str, ext: str) -> int:
        """
        Calculate cognitive complexity (simplified).
        Cognitive complexity penalizes nested structures more heavily.
        """
        cognitive = 0
        nesting_level = 0

        # Split into lines for nesting analysis
        lines = content.split('\n')

        for line in lines:
            stripped = line.strip()

            # Count nesting increases
            if ext in ['.py']:
                if re.match(r'^(if|elif|else|for|while|try|except|with)\b', stripped):
                    cognitive += 1 + nesting_level
                if stripped.endswith(':') and any(kw in stripped for kw in ['if', 'for', 'while', 'def', 'class', 'try', 'except', 'with']):
                    nesting_level += 1
            else:
                # C-style languages
                if re.search(r'\b(if|else if|for|foreach|while|switch|catch)\s*\(', stripped):
                    cognitive += 1 + nesting_level
                nesting_level += stripped.count('{')
                nesting_level -= stripped.count('}')
                nesting_level = max(0, nesting_level)

            # Penalize logical operators
            cognitive += len(re.findall(r'&&|\|\||and|or', stripped, re.IGNORECASE))

        return cognitive

    def _extract_functions(self, content: str, ext: str) -> List[Dict[str, Any]]:
        """Extract function/method definitions."""
        functions = []

        if ext == '.py':
            # Python functions
            pattern = r'def\s+(\w+)\s*\([^)]*\):\s*\n((?:(?!\ndef\s|\nclass\s).)*)'
            for match in re.finditer(pattern, content, re.DOTALL):
                functions.append({
                    'name': match.group(1),
                    'body': match.group(0),
                })
        elif ext in ['.js', '.ts', '.jsx', '.tsx']:
            # JavaScript/TypeScript functions
            patterns = [
                r'function\s+(\w+)\s*\([^)]*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
                r'(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
            ]
            for pattern in patterns:
                for match in re.finditer(pattern, content):
                    functions.append({
                        'name': match.group(1),
                        'body': match.group(0),
                    })
        elif ext in ['.cs', '.java']:
            # C#/Java methods
            pattern = r'(?:public|private|protected|internal|static|\s)+\s+\w+\s+(\w+)\s*\([^)]*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
            for match in re.finditer(pattern, content):
                functions.append({
                    'name': match.group(1),
                    'body': match.group(0),
                })

        return functions

    def _group_into_modules(
        self,
        file_metrics: Dict[str, FileComplexity],
        depth: int
    ) -> List[ModuleComplexity]:
        """Group files into modules based on directory structure."""
        module_files: Dict[str, List[FileComplexity]] = defaultdict(list)

        for file_path, metrics in file_metrics.items():
            parts = Path(file_path).parts
            module_path = '/'.join(parts[:min(depth, len(parts) - 1)]) or '.'
            module_files[module_path].append(metrics)

        modules = []
        for module_path, files in sorted(module_files.items()):
            total_cyclomatic = sum(f.cyclomatic_complexity for f in files)
            total_cognitive = sum(f.cognitive_complexity for f in files)
            total_lines = sum(f.lines_of_code for f in files)
            total_functions = sum(f.function_count for f in files)
            max_file = max((f.cyclomatic_complexity for f in files), default=0)
            max_func = max((f.max_function_complexity for f in files), default=0)

            # Identify hotspot files in this module
            hotspot_files = [
                f.file_path for f in files
                if f.cyclomatic_complexity > self.HOTSPOT_THRESHOLD
            ]

            modules.append(ModuleComplexity(
                module_path=module_path,
                module_name=Path(module_path).name or 'root',
                file_count=len(files),
                total_lines=total_lines,
                total_cyclomatic=total_cyclomatic,
                total_cognitive=total_cognitive,
                total_functions=total_functions,
                max_file_complexity=max_file,
                max_function_complexity=max_func,
                files=files,
                hotspot_files=hotspot_files,
            ))

        # Sort by average complexity (worst first)
        modules.sort(key=lambda m: m.avg_cyclomatic, reverse=True)

        return modules

    def _identify_hotspots(
        self,
        file_metrics: Dict[str, FileComplexity]
    ) -> List[Dict[str, Any]]:
        """Identify complexity hotspots."""
        hotspots = []

        for file_path, metrics in file_metrics.items():
            if metrics.cyclomatic_complexity > self.HOTSPOT_THRESHOLD:
                hotspots.append({
                    'file_path': file_path,
                    'cyclomatic_complexity': metrics.cyclomatic_complexity,
                    'cognitive_complexity': metrics.cognitive_complexity,
                    'lines_of_code': metrics.lines_of_code,
                    'high_complexity_functions': metrics.high_complexity_functions,
                    'severity': self._get_hotspot_severity(metrics.cyclomatic_complexity),
                })

        # Sort by complexity (worst first)
        hotspots.sort(key=lambda h: h['cyclomatic_complexity'], reverse=True)

        return hotspots[:20]  # Top 20 hotspots

    def _get_hotspot_severity(self, complexity: int) -> str:
        """Determine hotspot severity."""
        if complexity > 60:
            return 'critical'
        elif complexity > 40:
            return 'high'
        elif complexity > 30:
            return 'medium'
        else:
            return 'low'

    def _calculate_distribution(
        self,
        file_metrics: Dict[str, FileComplexity]
    ) -> Dict[str, int]:
        """Calculate complexity distribution."""
        distribution = {
            '1-5': 0,
            '6-10': 0,
            '11-15': 0,
            '16-20': 0,
            '21-30': 0,
            '31-50': 0,
            '51+': 0,
        }

        for metrics in file_metrics.values():
            c = metrics.cyclomatic_complexity
            if c <= 5:
                distribution['1-5'] += 1
            elif c <= 10:
                distribution['6-10'] += 1
            elif c <= 15:
                distribution['11-15'] += 1
            elif c <= 20:
                distribution['16-20'] += 1
            elif c <= 30:
                distribution['21-30'] += 1
            elif c <= 50:
                distribution['31-50'] += 1
            else:
                distribution['51+'] += 1

        return distribution

    def _generate_recommendations(
        self,
        modules: List[ModuleComplexity],
        hotspots: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Critical modules
        critical_modules = [m for m in modules if m.health_status == ModuleHealthStatus.CRITICAL]
        if critical_modules:
            names = ', '.join(m.module_name for m in critical_modules[:3])
            recommendations.append(
                f"CRITICAL: {len(critical_modules)} module(s) have critical complexity. "
                f"Priority refactoring needed for: {names}"
            )

        # At-risk modules
        at_risk_modules = [m for m in modules if m.health_status == ModuleHealthStatus.AT_RISK]
        if at_risk_modules:
            recommendations.append(
                f"HIGH: {len(at_risk_modules)} module(s) are at-risk. "
                f"Consider decomposition and function extraction."
            )

        # Top hotspots
        critical_hotspots = [h for h in hotspots if h['severity'] == 'critical']
        if critical_hotspots:
            file_names = [Path(h['file_path']).name for h in critical_hotspots[:3]]
            recommendations.append(
                f"HOTSPOTS: {len(critical_hotspots)} file(s) require immediate attention: "
                f"{', '.join(file_names)}"
            )

        # Function-level issues
        all_high_funcs = []
        for m in modules:
            for f in m.files:
                all_high_funcs.extend(f.high_complexity_functions)

        if len(all_high_funcs) > 10:
            recommendations.append(
                f"FUNCTIONS: {len(all_high_funcs)} functions exceed complexity threshold. "
                f"Consider extracting helper methods."
            )

        # General advice based on overall health
        healthy_pct = sum(1 for m in modules if m.health_status == ModuleHealthStatus.HEALTHY) / max(len(modules), 1) * 100
        if healthy_pct < 50:
            recommendations.append(
                f"OVERALL: Only {healthy_pct:.0f}% of modules are healthy. "
                f"Establish complexity budgets for new code."
            )
        elif healthy_pct >= 80:
            recommendations.append(
                f"OVERALL: {healthy_pct:.0f}% of modules are healthy. "
                f"Maintain current practices and monitor hotspots."
            )

        return recommendations if recommendations else [
            "No critical complexity issues detected. Continue monitoring."
        ]

    def _create_snapshot(
        self,
        modules: List[ModuleComplexity],
        hotspots: List[Dict[str, Any]]
    ) -> ComplexitySnapshot:
        """Create a snapshot for trend tracking."""
        total_complexity = sum(m.total_cyclomatic for m in modules)
        total_files = sum(m.file_count for m in modules)

        return ComplexitySnapshot(
            timestamp=datetime.now(timezone.utc),
            total_complexity=total_complexity,
            avg_complexity=total_complexity / max(total_files, 1),
            module_count=len(modules),
            file_count=total_files,
            hotspot_count=len(hotspots),
        )

    def _calculate_trend(self) -> Optional[ComplexityTrend]:
        """Calculate trend from historical snapshots."""
        if len(self._history) < 2:
            return None

        latest = self._history[-1]
        oldest = self._history[0]

        if oldest.avg_complexity == 0:
            return None

        change = ((latest.avg_complexity - oldest.avg_complexity) / oldest.avg_complexity) * 100

        if change < -5:
            direction = TrendDirection.IMPROVING
        elif change > 5:
            direction = TrendDirection.DEGRADING
        else:
            direction = TrendDirection.STABLE

        return ComplexityTrend(
            direction=direction,
            change_percentage=change,
            snapshots=self._history[-10:],  # Last 10 snapshots
        )

    def get_module_details(
        self,
        result: ComplexityDashboardResult,
        module_path: str
    ) -> Optional[ModuleComplexity]:
        """Get detailed metrics for a specific module."""
        for module in result.modules:
            if module.module_path == module_path:
                return module
        return None

    def generate_dashboard_report(self, result: ComplexityDashboardResult) -> str:
        """Generate a text report suitable for dashboards."""
        lines = [
            "=" * 60,
            "COMPLEXITY DASHBOARD REPORT",
            "=" * 60,
            f"Scan Time: {result.scan_timestamp.isoformat()}",
            f"Project: {result.project_path}",
            "",
            "SUMMARY",
            "-" * 40,
            f"Total Modules: {result.summary['total_modules']}",
            f"Total Files: {result.summary['total_files']}",
            f"Total Lines: {result.summary['total_lines']:,}",
            f"Total Complexity: {result.summary['total_complexity']:,}",
            f"Average Complexity: {result.summary['avg_complexity']}",
            f"Hotspots: {result.summary['hotspot_count']}",
            "",
            "HEALTH DISTRIBUTION",
            "-" * 40,
        ]

        health_dist = result.summary.get('health_distribution', {})
        for status, count in sorted(health_dist.items()):
            bar = '#' * min(count, 30)
            lines.append(f"  {status:10} [{bar}] {count}")

        lines.extend([
            "",
            "TOP MODULES BY COMPLEXITY",
            "-" * 40,
        ])

        for module in result.modules[:10]:
            status_icon = {
                ModuleHealthStatus.HEALTHY: "[OK]",
                ModuleHealthStatus.WARNING: "[!]",
                ModuleHealthStatus.AT_RISK: "[!!]",
                ModuleHealthStatus.CRITICAL: "[XXX]",
            }.get(module.health_status, "[-]")

            lines.append(
                f"  {status_icon} {module.module_name:30} "
                f"avg={module.avg_cyclomatic:5.1f} files={module.file_count:3}"
            )

        if result.hotspots:
            lines.extend([
                "",
                "COMPLEXITY HOTSPOTS",
                "-" * 40,
            ])
            for h in result.hotspots[:10]:
                lines.append(
                    f"  [{h['severity'].upper():8}] {Path(h['file_path']).name:30} "
                    f"complexity={h['cyclomatic_complexity']}"
                )

        lines.extend([
            "",
            "RECOMMENDATIONS",
            "-" * 40,
        ])
        for rec in result.recommendations:
            lines.append(f"  - {rec}")

        if result.trend:
            lines.extend([
                "",
                "TREND ANALYSIS",
                "-" * 40,
                f"  Direction: {result.trend.direction.value.upper()}",
                f"  Change: {result.trend.change_percentage:+.1f}%",
            ])

        lines.append("=" * 60)

        return '\n'.join(lines)


# Singleton for service reuse
_dashboard_service: Optional[ComplexityDashboardService] = None


def get_complexity_dashboard_service(
    project_path: Optional[str] = None
) -> ComplexityDashboardService:
    """Get or create the complexity dashboard service."""
    global _dashboard_service
    if _dashboard_service is None or (project_path and _dashboard_service.project_path != project_path):
        _dashboard_service = ComplexityDashboardService(project_path)
    return _dashboard_service
