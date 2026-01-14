"""
Comments Analyzer - Code Comments Ratio Analysis

Week 129: Metrics Layer Integration - SIG TOP 10 Metric #9
Calculates comment ratio (comments / (comments + code)) with 5-star quality rating.

5-Star Rating (higher is better - more comments = better documentation):
- 5 stars: ratio >= 20% (excellent documentation)
- 4 stars: ratio 15-20% (good documentation)
- 3 stars: ratio 10-15% (moderate documentation)
- 2 stars: ratio 5-10% (poor documentation)
- 1 star:  ratio < 5% (minimal documentation)

Based on SIG Maintainability Model recommendations.
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from ..base import (
    BaseScanner, ScanResult, ScanFinding, ScanMetrics,
    Severity, FindingType
)

logger = logging.getLogger(__name__)


class CommentsAnalyzer(BaseScanner):
    """
    Code Comments analyzer measuring documentation ratio.

    Supports: C#, VB.NET, SQL, JavaScript, TypeScript, ASP, Python
    """

    @property
    def name(self) -> str:
        return "comments"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supported_stacks(self) -> List[str]:
        return ['dotnet', 'csharp', 'vbnet', 'aspnet', 'python', 'javascript', 'typescript']

    @property
    def scanner_type(self) -> str:
        return "comments"

    def _calculate_rating(self, comment_ratio: float) -> int:
        """
        Calculate 5-star rating based on comment ratio percentage.

        Higher ratio = better documentation = higher rating.
        """
        if comment_ratio >= 20.0:
            return 5
        elif comment_ratio >= 15.0:
            return 4
        elif comment_ratio >= 10.0:
            return 3
        elif comment_ratio >= 5.0:
            return 2
        else:
            return 1

    def _get_rating_stars(self, rating: int) -> str:
        """Convert numeric rating to star string"""
        return '★' * rating + '☆' * (5 - rating)

    def _count_lines(self, file_path: Path, ext: str) -> Dict[str, int]:
        """
        Count different types of lines in a file.

        Returns dict with: total, blank, comment, code
        """
        total = 0
        blank = 0
        comment = 0
        code = 0

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                in_block_comment = False

                for line in f:
                    total += 1
                    stripped = line.strip()

                    # Blank line
                    if not stripped:
                        blank += 1
                        continue

                    # Block comment detection based on language
                    if ext in ['.cs', '.js', '.ts', '.aspx', '.asp']:
                        # C-style block comments /* */
                        if '/*' in stripped:
                            in_block_comment = True
                        if in_block_comment:
                            comment += 1
                            if '*/' in stripped:
                                in_block_comment = False
                            continue
                        # Single line comments
                        if stripped.startswith('//'):
                            comment += 1
                            continue

                    elif ext in ['.html', '.xml', '.config']:
                        # HTML/XML comments <!-- -->
                        if '<!--' in stripped:
                            in_block_comment = True
                        if in_block_comment:
                            comment += 1
                            if '-->' in stripped:
                                in_block_comment = False
                            continue

                    elif ext == '.py':
                        # Python: # comments and ''' """ docstrings
                        if stripped.startswith('#'):
                            comment += 1
                            continue
                        # Simplified docstring detection
                        if '"""' in stripped or "'''" in stripped:
                            comment += 1
                            continue

                    elif ext == '.vb':
                        # VB.NET: ' comments
                        if stripped.startswith("'"):
                            comment += 1
                            continue

                    elif ext == '.sql':
                        # SQL: -- comments and /* */ blocks
                        if '/*' in stripped:
                            in_block_comment = True
                        if in_block_comment:
                            comment += 1
                            if '*/' in stripped:
                                in_block_comment = False
                            continue
                        if stripped.startswith('--'):
                            comment += 1
                            continue

                    # Otherwise it's code
                    code += 1

        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")

        return {
            'total': total,
            'blank': blank,
            'comment': comment,
            'code': code
        }

    async def scan(self) -> ScanResult:
        """Execute the comments analysis"""
        started_at = datetime.now()
        findings: List[ScanFinding] = []

        files_scanned = 0
        total_code_lines = 0
        total_comment_lines = 0
        total_blank_lines = 0
        total_lines = 0

        # Per-file tracking for findings
        file_stats: List[Dict[str, Any]] = []

        # File extensions to analyze
        extensions = {'.cs', '.vb', '.sql', '.js', '.ts', '.asp', '.aspx', '.py', '.html', '.xml', '.config'}
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

                    # Count lines
                    counts = self._count_lines(file_path, ext)

                    total_lines += counts['total']
                    total_code_lines += counts['code']
                    total_comment_lines += counts['comment']
                    total_blank_lines += counts['blank']

                    # Calculate per-file ratio
                    file_effective_lines = counts['code'] + counts['comment']
                    if file_effective_lines > 0:
                        file_ratio = (counts['comment'] / file_effective_lines) * 100
                    else:
                        file_ratio = 0

                    file_stats.append({
                        'path': rel_path,
                        'code': counts['code'],
                        'comment': counts['comment'],
                        'ratio': file_ratio,
                        'total': counts['total']
                    })

                    # Generate findings for poorly documented files (ratio < 5% and > 100 lines)
                    if file_ratio < 5.0 and counts['code'] > 100:
                        severity = Severity.LOW
                        if counts['code'] > 500:
                            severity = Severity.MEDIUM
                        if counts['code'] > 1000:
                            severity = Severity.HIGH

                        findings.append(ScanFinding(
                            scanner=self.name,
                            rule_id="low-comment-ratio",
                            message=f"File has low comment ratio: {file_ratio:.1f}% ({counts['comment']} comments / {counts['code']} code lines)",
                            severity=severity,
                            finding_type=FindingType.DOCUMENTATION,
                            file_path=rel_path,
                            recommendation=f"Consider adding documentation comments. "
                                          f"Target: at least 10% comment ratio ({int(counts['code'] * 0.1)} comment lines)",
                            effort_minutes=int(counts['code'] * 0.05),  # ~3 min per 60 lines
                            metadata={
                                "comment_lines": counts['comment'],
                                "code_lines": counts['code'],
                                "comment_ratio": round(file_ratio, 2)
                            }
                        ))

            # Calculate overall ratio
            effective_lines = total_code_lines + total_comment_lines
            if effective_lines > 0:
                overall_ratio = (total_comment_lines / effective_lines) * 100
            else:
                overall_ratio = 0

            rating = self._calculate_rating(overall_ratio)
            rating_stars = self._get_rating_stars(rating)

            # Find files with lowest comment ratios
            worst_files = sorted(file_stats, key=lambda x: x['ratio'])[:10]

            # Build metrics
            metrics = ScanMetrics(
                files_scanned=files_scanned,
                lines_of_code=total_lines,
                code_lines=total_code_lines,
                comment_lines=total_comment_lines,
                blank_lines=total_blank_lines
            )

            # Extended metadata
            metrics.metadata = {
                "rating": rating,
                "rating_stars": rating_stars,
                "comment_ratio_percentage": round(overall_ratio, 2),
                "total_effective_lines": effective_lines,
                "well_documented_files": sum(1 for f in file_stats if f['ratio'] >= 10),
                "poorly_documented_files": sum(1 for f in file_stats if f['ratio'] < 5 and f['code'] > 100),
                "worst_files": worst_files
            }

            completed_at = datetime.now()

            logger.info(
                f"Comments scan complete: {files_scanned} files, "
                f"comment ratio: {overall_ratio:.2f}%, rating: {rating_stars}"
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
            logger.error(f"Comments scan failed: {e}")
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
            "min_ratio_threshold": 10.0,  # Minimum acceptable comment ratio
            "min_lines_for_finding": 100,  # Only flag files > this many lines
        }
