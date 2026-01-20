"""
Complexity Analyzer - Unit Complexity Analyzer

Week 126: Metrics Layer Integration
Wraps the Quality-Migration-Tools/03-unit-complexity-analyzer

5-Star Rating (lower is better - simpler code is more maintainable):
- 5 stars: avg < 10 (simple, excellent maintainability)
- 4 stars: avg 10-15 (moderate complexity)
- 3 stars: avg 15-20 (complex, refactor recommended)
- 2 stars: avg 20-25 (high risk)
- 1 star:  avg > 25 (critical, immediate action needed)
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..base import (
    BaseScanner, ScanResult, ScanFinding, ScanMetrics,
    Severity, FindingType
)

logger = logging.getLogger(__name__)

# Path to quality analysis tools (configurable via QUALITY_TOOLS_PATH env var)
QUALITY_TOOLS_PATH = Path(os.environ.get("QUALITY_TOOLS_PATH", str(Path.home() / "Projects" / "Quality-Migration-Tools")))


class ComplexityAnalyzer(BaseScanner):
    """
    Cyclomatic complexity analyzer wrapping deep_analyze.py.

    Supports: C#, VB.NET, SQL, JavaScript, TypeScript, ASP
    """

    @property
    def name(self) -> str:
        return "complexity"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supported_stacks(self) -> List[str]:
        return ['dotnet', 'csharp', 'vbnet', 'aspnet', 'python', 'javascript', 'typescript']

    @property
    def scanner_type(self) -> str:
        return "complexity"

    def _calculate_rating(self, avg_complexity: float) -> int:
        """Calculate 5-star rating based on average complexity"""
        if avg_complexity < 10:
            return 5
        elif avg_complexity < 15:
            return 4
        elif avg_complexity < 20:
            return 3
        elif avg_complexity < 25:
            return 2
        else:
            return 1

    def _get_rating_stars(self, rating: int) -> str:
        """Convert numeric rating to star string"""
        return '★' * rating + '☆' * (5 - rating)

    def _import_quality_analyzer(self):
        """Import the quality analyzer module"""
        complexity_path = QUALITY_TOOLS_PATH / "03-unit-complexity-analyzer"

        if not complexity_path.exists():
            raise ImportError(f"Complexity analyzer not found at {complexity_path}")

        # Add quality tools to path
        if str(QUALITY_TOOLS_PATH) not in sys.path:
            sys.path.insert(0, str(QUALITY_TOOLS_PATH))
        if str(complexity_path) not in sys.path:
            sys.path.insert(0, str(complexity_path))

        try:
            from deep_analyze import BaseFileAnalyzer, FileMetrics
            return BaseFileAnalyzer, FileMetrics
        except ImportError as e:
            logger.warning(f"Could not import quality analyzer: {e}")
            return None, None

    async def scan(self) -> ScanResult:
        """Execute the complexity analysis using quality tools"""
        started_at = datetime.now()
        findings: List[ScanFinding] = []

        # Try to import quality analyzer
        BaseFileAnalyzer, FileMetrics = self._import_quality_analyzer()

        files_scanned = 0
        total_loc = 0
        total_complexity = 0
        function_count = 0
        max_complexity = 0
        complexity_distribution = {
            '1-5': 0, '6-10': 0, '11-15': 0,
            '16-20': 0, '21-30': 0, '31+': 0
        }

        # File extensions to analyze
        extensions = {'.cs', '.vb', '.sql', '.js', '.ts', '.asp', '.aspx', '.py'}
        excluded_dirs = {
            'bin', 'obj', 'node_modules', '.git', '.vs', 'packages',
            'TestResults', 'Debug', 'Release', '.nuget', '__pycache__',
            'bower_components', 'vendor', 'dist', 'build', '.venv', 'venv'
        }

        try:
            for root, dirs, files in os.walk(self.project_path):
                # Filter excluded directories
                dirs[:] = [d for d in dirs if d not in excluded_dirs]

                root_path = Path(root)

                for filename in files:
                    file_path = root_path / filename
                    ext = file_path.suffix.lower()

                    if ext not in extensions:
                        continue

                    files_scanned += 1
                    rel_path = str(file_path.relative_to(self.project_path))

                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = content.split('\n')
                            total_loc += len(lines)
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")
                        continue

                    # Calculate complexity using simplified method
                    # (same logic as quality tools)
                    file_complexity = self._calculate_file_complexity(content, ext)

                    if file_complexity > 0:
                        function_count += 1
                        total_complexity += file_complexity
                        max_complexity = max(max_complexity, file_complexity)

                        # Update distribution
                        if file_complexity <= 5:
                            complexity_distribution['1-5'] += 1
                        elif file_complexity <= 10:
                            complexity_distribution['6-10'] += 1
                        elif file_complexity <= 15:
                            complexity_distribution['11-15'] += 1
                        elif file_complexity <= 20:
                            complexity_distribution['16-20'] += 1
                        elif file_complexity <= 30:
                            complexity_distribution['21-30'] += 1
                        else:
                            complexity_distribution['31+'] += 1

                        # Generate findings for high complexity files
                        if file_complexity > 15:
                            severity = Severity.LOW
                            if file_complexity > 25:
                                severity = Severity.MEDIUM
                            if file_complexity > 40:
                                severity = Severity.HIGH
                            if file_complexity > 60:
                                severity = Severity.CRITICAL

                            findings.append(ScanFinding(
                                scanner=self.name,
                                rule_id="high-complexity",
                                message=f"File has high cyclomatic complexity: {file_complexity}",
                                severity=severity,
                                finding_type=FindingType.COMPLEXITY,
                                file_path=rel_path,
                                recommendation=f"Consider refactoring to reduce complexity below 15. "
                                              f"Current: {file_complexity}",
                                effort_minutes=file_complexity * 3,
                                metadata={
                                    "complexity": file_complexity,
                                    "lines_of_code": len(lines)
                                }
                            ))

            # Calculate averages
            avg_complexity = total_complexity / function_count if function_count > 0 else 0
            rating = self._calculate_rating(avg_complexity)
            rating_stars = self._get_rating_stars(rating)

            # Build metrics
            metrics = ScanMetrics(
                files_scanned=files_scanned,
                lines_of_code=total_loc,
                complexity_average=round(avg_complexity, 2)
            )

            # Extended metadata
            metrics.metadata = {
                "rating": rating,
                "rating_stars": rating_stars,
                "total_functions": function_count,
                "total_complexity": total_complexity,
                "average_complexity": round(avg_complexity, 2),
                "max_complexity": max_complexity,
                "complexity_distribution": complexity_distribution,
                "quality_tools_available": BaseFileAnalyzer is not None
            }

            completed_at = datetime.now()

            logger.info(
                f"Complexity scan complete: {files_scanned} files, "
                f"avg complexity: {avg_complexity:.2f}, rating: {rating_stars}"
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
            logger.error(f"Complexity scan failed: {e}")
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

    def _calculate_file_complexity(self, content: str, ext: str) -> int:
        """
        Calculate cyclomatic complexity for a file.

        Based on deep_analyze.py logic:
        Counts decision points: if, else if, for, foreach, while, case, catch, &&, ||, ?:
        """
        import re

        complexity = 1  # Base complexity

        # Language-specific patterns
        if ext in ['.cs', '.js', '.ts', '.aspx']:
            patterns = [
                r'\bif\s*\(',
                r'\belse\s+if\s*\(',
                r'\bfor\s*\(',
                r'\bforeach\s*\(',
                r'\bwhile\s*\(',
                r'\bcase\s+[^:]+:',
                r'\bcatch\s*\(',
                r'\?\s*[^:]+:',  # Ternary
                r'&&',
                r'\|\|',
            ]
        elif ext == '.vb':
            patterns = [
                r'\bIf\b',
                r'\bElseIf\b',
                r'\bFor\b',
                r'\bFor\s+Each\b',
                r'\bWhile\b',
                r'\bDo\s+While\b',
                r'\bDo\s+Until\b',
                r'\bSelect\s+Case\b',
                r'\bCase\s+\w+',
                r'\bCatch\b',
                r'\bAndAlso\b',
                r'\bOrElse\b',
            ]
        elif ext == '.sql':
            patterns = [
                r'\bIF\b',
                r'\bELSE\s+IF\b',
                r'\bWHILE\b',
                r'\bCASE\b',
                r'\bWHEN\b',
                r'\bAND\b',
                r'\bOR\b',
            ]
        elif ext == '.py':
            patterns = [
                r'\bif\s+',
                r'\belif\s+',
                r'\bfor\s+',
                r'\bwhile\s+',
                r'\bexcept\s*[:\(]',
                r'\band\b',
                r'\bor\b',
            ]
        elif ext == '.asp':
            patterns = [
                r'\bIf\b',
                r'\bElseIf\b',
                r'\bFor\b',
                r'\bDo\s+While\b',
                r'\bSelect\s+Case\b',
                r'\bCase\b',
                r'\bAnd\b',
                r'\bOr\b',
            ]
        else:
            patterns = []

        flags = re.IGNORECASE if ext in ['.vb', '.asp', '.sql'] else 0

        for pattern in patterns:
            matches = re.findall(pattern, content, flags)
            complexity += len(matches)

        return complexity

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "complexity_threshold": 10,
            "quality_tools_path": str(QUALITY_TOOLS_PATH),
        }
