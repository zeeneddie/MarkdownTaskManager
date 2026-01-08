"""
Interfacing Analyzer - Wrapper for HCI Unit Interfacing Analyzer

Week 126: Metrics Layer Integration
Wraps the HCI-SoftwareKwaliteit-Migratie/tools/04-unit-interfacing-analyzer

Analyzes function/method parameter counts.

5-Star Rating (fewer parameters = better interface design):
- 5 stars: avg < 4 parameters
- 4 stars: avg 4-5 parameters
- 3 stars: avg 5-6 parameters
- 2 stars: avg 6-7 parameters
- 1 star:  avg > 7 parameters
"""

import sys
import os
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

from ..base import (
    BaseScanner, ScanResult, ScanFinding, ScanMetrics,
    Severity, FindingType
)

logger = logging.getLogger(__name__)

# Path to HCI tools
HCI_TOOLS_PATH = Path.home() / "Projects" / "HCI-projecten" / "HCI-SoftwareKwaliteit-Migratie" / "tools"


class InterfacingAnalyzer(BaseScanner):
    """
    Unit interfacing analyzer wrapping HCI unit_interfacing_analyzer.py.

    Analyzes function/method parameter counts for interface quality.
    Supports: C#, VB.NET, SQL, JavaScript, TypeScript
    """

    @property
    def name(self) -> str:
        return "interfacing"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supported_stacks(self) -> List[str]:
        return ['dotnet', 'csharp', 'vbnet', 'aspnet', 'javascript', 'typescript']

    @property
    def scanner_type(self) -> str:
        return "interfacing"

    def _calculate_rating(self, avg_params: float) -> int:
        """Calculate 5-star rating based on average parameter count"""
        if avg_params < 4:
            return 5
        elif avg_params < 5:
            return 4
        elif avg_params < 6:
            return 3
        elif avg_params < 7:
            return 2
        else:
            return 1

    def _get_rating_stars(self, rating: int) -> str:
        """Convert numeric rating to star string"""
        return '★' * rating + '☆' * (5 - rating)

    def _count_parameters(self, signature: str) -> int:
        """
        Count parameters in function signature.

        Based on HCI unit_interfacing_analyzer.py logic.
        """
        # Remove generics
        sig = re.sub(r'<[^>]+>', '', signature)

        # Extract parameter section
        param_match = re.search(r'\(([^)]*)\)', sig)
        if not param_match:
            return 0

        params_str = param_match.group(1).strip()
        if not params_str or params_str.lower() in ['void', '']:
            return 0

        # Split by comma
        params = [p.strip() for p in params_str.split(',') if p.strip()]
        return len(params)

    async def scan(self) -> ScanResult:
        """Execute the interfacing analysis"""
        started_at = datetime.now()
        findings: List[ScanFinding] = []

        files_scanned = 0
        total_loc = 0
        total_functions = 0
        total_params = 0
        param_distribution = {
            '0-2': 0, '3-4': 0, '5-6': 0, '7+': 0
        }
        language_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            'functions': 0, 'total_params': 0
        })

        # File extensions and their patterns
        patterns = {
            '.cs': r'(?:public|private|protected|internal|static|async|virtual|override|abstract)\s+(?:\w+\s+)*(\w+)\s*\(([^)]*)\)',
            '.vb': r'(?:Public|Private|Protected|Friend|Shared|Overrides)\s+(?:Sub|Function)\s+(\w+)\s*\(([^)]*)\)',
            '.js': r'function\s+(\w+)\s*\(([^)]*)\)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>)',
            '.ts': r'function\s+(\w+)\s*\(([^)]*)\)|(?:const|let|var)\s+(\w+)\s*(?::\s*[^=]+)?\s*=',
            '.sql': r'CREATE\s+(?:OR\s+ALTER\s+)?PROCEDURE\s+(\w+)',
        }

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

                    if ext not in patterns:
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

                    # Find functions and analyze parameters
                    pattern = patterns[ext]
                    flags = re.IGNORECASE if ext == '.vb' else 0

                    for match in re.finditer(pattern, content, re.MULTILINE | flags):
                        func_name = match.group(1) or match.group(3) if match.lastindex >= 3 else match.group(1)
                        if not func_name:
                            continue

                        # Count parameters
                        if ext == '.sql':
                            # Count @ symbols for SQL
                            func_start = match.end()
                            func_end = content.find('\nAS', func_start)
                            if func_end == -1:
                                func_end = func_start + 500
                            param_section = content[func_start:func_end]
                            param_count = param_section.count('@')
                        else:
                            param_str = match.group(2) if match.lastindex >= 2 and match.group(2) else ""
                            param_count = self._count_parameters(f"({param_str})")

                        total_functions += 1
                        total_params += param_count

                        # Update distribution
                        if param_count <= 2:
                            param_distribution['0-2'] += 1
                        elif param_count <= 4:
                            param_distribution['3-4'] += 1
                        elif param_count <= 6:
                            param_distribution['5-6'] += 1
                        else:
                            param_distribution['7+'] += 1

                        # Language stats
                        lang = {'.cs': 'C#', '.vb': 'VB.NET', '.js': 'JavaScript',
                                '.ts': 'TypeScript', '.sql': 'SQL'}.get(ext, 'Unknown')
                        language_stats[lang]['functions'] += 1
                        language_stats[lang]['total_params'] += param_count

                        # Generate findings for high parameter counts
                        if param_count > 4:
                            severity = Severity.LOW
                            if param_count > 6:
                                severity = Severity.MEDIUM
                            if param_count > 10:
                                severity = Severity.HIGH

                            findings.append(ScanFinding(
                                scanner=self.name,
                                rule_id="high-parameter-count",
                                message=f"Function '{func_name}' has {param_count} parameters",
                                severity=severity,
                                finding_type=FindingType.CODE_SMELL,
                                file_path=rel_path,
                                line_number=content[:match.start()].count('\n') + 1,
                                recommendation="Consider using a parameter object or builder pattern. "
                                              "Recommended: <= 4 parameters",
                                effort_minutes=15,
                                metadata={
                                    "function_name": func_name,
                                    "parameter_count": param_count,
                                    "language": lang
                                }
                            ))

            # Calculate averages
            avg_params = total_params / total_functions if total_functions > 0 else 0
            rating = self._calculate_rating(avg_params)
            rating_stars = self._get_rating_stars(rating)

            # Calculate percentage above threshold
            above_threshold = param_distribution['5-6'] + param_distribution['7+']
            pct_above_threshold = (above_threshold / total_functions * 100) if total_functions > 0 else 0

            # Build metrics
            metrics = ScanMetrics(
                files_scanned=files_scanned,
                lines_of_code=total_loc,
            )

            metrics.metadata = {
                "rating": rating,
                "rating_stars": rating_stars,
                "total_functions": total_functions,
                "total_parameters": total_params,
                "average_parameters": round(avg_params, 2),
                "param_distribution": param_distribution,
                "pct_above_threshold": round(pct_above_threshold, 2),
                "by_language": {
                    lang: {
                        "functions": stats['functions'],
                        "average_parameters": round(
                            stats['total_params'] / stats['functions'], 2
                        ) if stats['functions'] > 0 else 0
                    }
                    for lang, stats in language_stats.items()
                }
            }

            completed_at = datetime.now()

            logger.info(
                f"Interfacing scan complete: {total_functions} functions, "
                f"avg params: {avg_params:.2f}, rating: {rating_stars}"
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
            logger.error(f"Interfacing scan failed: {e}")
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
            "parameter_threshold": 4,
            "hci_tools_path": str(HCI_TOOLS_PATH),
        }
