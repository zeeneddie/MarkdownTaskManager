"""
.NET Volume and Duplication Scanners

Analyzes .NET codebases (C#, VB.NET, ASP.NET) for:
- Code volume metrics (LOC, files, complexity)
- Code duplication detection
- File type breakdown
"""

import os
import csv
import hashlib
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
import logging

from ..base import (
    BaseScanner, ScanResult, ScanFinding, ScanMetrics,
    Severity, FindingType
)

logger = logging.getLogger(__name__)


class DotNetVolumeScanner(BaseScanner):
    """
    Volume analyzer for .NET codebases.

    Counts lines of code, blank lines, comments, and generates statistics
    by file type and module.
    """

    # File extensions to analyze
    EXTENSIONS = {
        '.asp': 'ASP Classic',
        '.aspx': 'ASP.NET WebForms',
        '.ascx': 'ASP.NET User Control',
        '.master': 'ASP.NET Master Page',
        '.cs': 'C#',
        '.vb': 'VB.NET',
        '.sql': 'SQL',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.css': 'CSS',
        '.html': 'HTML',
        '.xml': 'XML',
        '.config': 'Config',
        '.json': 'JSON',
        '.cshtml': 'Razor View',
        '.vbhtml': 'VB Razor View',
        '.xaml': 'XAML'
    }

    # Directories to exclude
    EXCLUDED_DIRS = {
        'bin', 'obj', 'node_modules', '.git', '.vs', 'packages',
        'TestResults', 'Debug', 'Release', '.nuget', '__pycache__',
        'bower_components', 'vendor'
    }

    @property
    def name(self) -> str:
        return "dotnet-volume"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supported_stacks(self) -> List[str]:
        return ['dotnet', 'csharp', 'vbnet', 'aspnet']

    @property
    def scanner_type(self) -> str:
        return "volume"

    def _should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded"""
        parts = path.parts
        return any(excluded in parts for excluded in self.EXCLUDED_DIRS)

    def _count_lines(self, file_path: Path) -> Tuple[int, int, int, int]:
        """Count different types of lines in a file"""
        total = blank = comment = code = 0

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                in_block_comment = False

                for line in f:
                    total += 1
                    stripped = line.strip()

                    if not stripped:
                        blank += 1
                        continue

                    # Block comment detection
                    if '/*' in stripped or '<!--' in stripped:
                        in_block_comment = True

                    if in_block_comment:
                        comment += 1
                        if '*/' in stripped or '-->' in stripped:
                            in_block_comment = False
                        continue

                    # Single line comments
                    if (stripped.startswith('//') or
                        stripped.startswith("'") or  # VB comment
                        stripped.startswith('--') or  # SQL comment
                        stripped.startswith('#')):
                        comment += 1
                        continue

                    code += 1

        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")

        return total, blank, comment, code

    async def scan(self) -> ScanResult:
        """Execute the volume scan"""
        started_at = datetime.now()
        findings: List[ScanFinding] = []

        # Statistics collection
        stats = defaultdict(lambda: {
            'count': 0,
            'total_lines': 0,
            'code_lines': 0,
            'blank_lines': 0,
            'comment_lines': 0
        })

        module_stats = defaultdict(lambda: defaultdict(lambda: {
            'count': 0,
            'total_lines': 0,
            'code_lines': 0
        }))

        files_scanned = 0
        total_loc = 0
        total_blank = 0
        total_comments = 0
        total_code = 0

        try:
            for root, dirs, files in os.walk(self.project_path):
                # Filter excluded directories
                dirs[:] = [d for d in dirs if d not in self.EXCLUDED_DIRS]

                root_path = Path(root)
                if self._should_exclude(root_path):
                    continue

                # Get module name (first level directory)
                rel_path = root_path.relative_to(self.project_path)
                module = rel_path.parts[0] if rel_path.parts else 'root'

                for filename in files:
                    file_path = root_path / filename
                    ext = file_path.suffix.lower()

                    if ext not in self.EXTENSIONS:
                        continue

                    file_type = self.EXTENSIONS[ext]
                    total, blank, comment, code = self._count_lines(file_path)

                    # Update statistics
                    stats[file_type]['count'] += 1
                    stats[file_type]['total_lines'] += total
                    stats[file_type]['code_lines'] += code
                    stats[file_type]['blank_lines'] += blank
                    stats[file_type]['comment_lines'] += comment

                    module_stats[module][file_type]['count'] += 1
                    module_stats[module][file_type]['total_lines'] += total
                    module_stats[module][file_type]['code_lines'] += code

                    files_scanned += 1
                    total_loc += total
                    total_blank += blank
                    total_comments += comment
                    total_code += code

                    # Generate findings for large files
                    if code > 500:
                        findings.append(ScanFinding(
                            scanner=self.name,
                            rule_id="large-file",
                            message=f"Large file with {code} lines of code",
                            severity=Severity.LOW if code < 1000 else Severity.MEDIUM,
                            finding_type=FindingType.CODE_SMELL,
                            file_path=str(file_path.relative_to(self.project_path)),
                            recommendation="Consider splitting into smaller files"
                        ))

            # Build metrics
            metrics = ScanMetrics(
                files_scanned=files_scanned,
                lines_of_code=total_loc,
                blank_lines=total_blank,
                comment_lines=total_comments,
                code_lines=total_code,
                file_type_breakdown={k: v['count'] for k, v in stats.items()},
                module_breakdown={
                    mod: {ft: data for ft, data in types.items()}
                    for mod, types in module_stats.items()
                }
            )

            completed_at = datetime.now()

            return ScanResult(
                scanner_name=self.name,
                scanner_version=self.version,
                stack="dotnet",
                project_path=str(self.project_path),
                started_at=started_at,
                completed_at=completed_at,
                success=True,
                findings=findings,
                metrics=metrics
            )

        except Exception as e:
            logger.error(f"Volume scan failed: {e}")
            return ScanResult(
                scanner_name=self.name,
                scanner_version=self.version,
                stack="dotnet",
                project_path=str(self.project_path),
                started_at=started_at,
                completed_at=datetime.now(),
                success=False,
                error_message=str(e)
            )


class DotNetDuplicationScanner(BaseScanner):
    """
    Code duplication detector for .NET codebases.

    Uses simple hash-based detection to find duplicated code blocks.
    """

    # Minimum lines for a duplicate block
    MIN_DUPLICATE_LINES = 6

    @property
    def name(self) -> str:
        return "dotnet-duplication"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supported_stacks(self) -> List[str]:
        return ['dotnet', 'csharp', 'vbnet', 'aspnet']

    @property
    def scanner_type(self) -> str:
        return "duplication"

    def _get_code_blocks(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """Extract code blocks from a file"""
        blocks = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            # Use sliding window for block detection
            for i in range(len(lines) - self.MIN_DUPLICATE_LINES + 1):
                block = ''.join(lines[i:i + self.MIN_DUPLICATE_LINES])
                # Normalize whitespace
                normalized = ' '.join(block.split())
                if len(normalized) > 50:  # Skip trivial blocks
                    block_hash = hashlib.md5(normalized.encode()).hexdigest()
                    blocks.append((i + 1, block_hash, normalized[:100]))

        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")

        return blocks

    async def scan(self) -> ScanResult:
        """Execute the duplication scan"""
        started_at = datetime.now()
        findings: List[ScanFinding] = []

        # Hash to locations mapping
        hash_locations: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        total_blocks = 0
        files_scanned = 0

        extensions = {'.cs', '.vb', '.aspx', '.ascx', '.js', '.ts'}

        try:
            for root, dirs, files in os.walk(self.project_path):
                dirs[:] = [d for d in dirs if d not in {'bin', 'obj', 'node_modules', '.git', 'packages'}]

                for filename in files:
                    file_path = Path(root) / filename
                    if file_path.suffix.lower() not in extensions:
                        continue

                    files_scanned += 1
                    blocks = self._get_code_blocks(file_path)
                    total_blocks += len(blocks)

                    rel_path = str(file_path.relative_to(self.project_path))
                    for line_num, block_hash, _ in blocks:
                        hash_locations[block_hash].append((rel_path, line_num))

            # Find duplicates
            duplicate_count = 0
            duplicate_blocks = 0

            for block_hash, locations in hash_locations.items():
                if len(locations) > 1:
                    duplicate_count += 1
                    duplicate_blocks += len(locations)

                    # Create finding for first occurrence
                    first_file, first_line = locations[0]
                    other_locations = [f"{f}:{l}" for f, l in locations[1:]]

                    findings.append(ScanFinding(
                        scanner=self.name,
                        rule_id="duplicate-code",
                        message=f"Duplicated code block found in {len(locations)} locations",
                        severity=Severity.MEDIUM if len(locations) > 3 else Severity.LOW,
                        finding_type=FindingType.DUPLICATION,
                        file_path=first_file,
                        line_number=first_line,
                        recommendation=f"Extract common code to shared method/class",
                        metadata={
                            "duplicate_locations": other_locations[:10],  # Limit to 10
                            "total_occurrences": len(locations)
                        }
                    ))

            # Calculate duplication percentage
            duplication_pct = (duplicate_blocks / total_blocks * 100) if total_blocks > 0 else 0

            metrics = ScanMetrics(
                files_scanned=files_scanned,
                duplication_percentage=round(duplication_pct, 2)
            )
            metrics.metadata = {
                "total_blocks": total_blocks,
                "duplicate_blocks": duplicate_blocks,
                "unique_duplicates": duplicate_count
            }

            return ScanResult(
                scanner_name=self.name,
                scanner_version=self.version,
                stack="dotnet",
                project_path=str(self.project_path),
                started_at=started_at,
                completed_at=datetime.now(),
                success=True,
                findings=findings,
                metrics=metrics
            )

        except Exception as e:
            logger.error(f"Duplication scan failed: {e}")
            return ScanResult(
                scanner_name=self.name,
                scanner_version=self.version,
                stack="dotnet",
                project_path=str(self.project_path),
                started_at=started_at,
                completed_at=datetime.now(),
                success=False,
                error_message=str(e)
            )
