"""
Duplication Analyzer - Code Clone Detector

Week 126: Metrics Layer Integration
Wraps the Quality-Migration-Tools/02-duplication-detector

Supports Type 1, 2, 3 clone detection:
- Type 1: Exact clones (identical code, whitespace ignored)
- Type 2: Renamed clones (same structure, different identifiers)
- Type 3: Near-miss clones (70% similarity threshold)

5-Star Rating (lower duplication = better):
- 5 stars: <= 3% duplication
- 4 stars: 3-7% duplication
- 3 stars: 7-10% duplication
- 2 stars: 10-20% duplication
- 1 star:  > 20% duplication
"""

import sys
import os
import re
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
from difflib import SequenceMatcher

from ..base import (
    BaseScanner, ScanResult, ScanFinding, ScanMetrics,
    Severity, FindingType
)

logger = logging.getLogger(__name__)

# Path to quality analysis tools (configurable via QUALITY_TOOLS_PATH env var)
QUALITY_TOOLS_PATH = Path(os.environ.get("QUALITY_TOOLS_PATH", str(Path.home() / "Projects" / "Quality-Migration-Tools")))


class DuplicationAnalyzer(BaseScanner):
    """
    Code duplication analyzer wrapping code_clone_detector.py.

    Detects Type 1, 2, and 3 code clones.
    Supports: C#, VB.NET, SQL, JavaScript, TypeScript, ASP
    """

    # Minimum block size for clone detection
    MIN_BLOCK_SIZE = 6

    @property
    def name(self) -> str:
        return "duplication"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supported_stacks(self) -> List[str]:
        return ['dotnet', 'csharp', 'vbnet', 'aspnet', 'javascript', 'typescript']

    @property
    def scanner_type(self) -> str:
        return "duplication"

    def _calculate_rating(self, duplication_pct: float) -> int:
        """Calculate 5-star rating based on duplication percentage"""
        if duplication_pct <= 3:
            return 5
        elif duplication_pct <= 7:
            return 4
        elif duplication_pct <= 10:
            return 3
        elif duplication_pct <= 20:
            return 2
        else:
            return 1

    def _get_rating_stars(self, rating: int) -> str:
        """Convert numeric rating to star string"""
        return '★' * rating + '☆' * (5 - rating)

    def _is_comment_only(self, line: str) -> bool:
        """Check if line is only a comment"""
        line = line.strip()
        return (line.startswith('//') or
                line.startswith('/*') or
                line.startswith('*') or
                line.startswith("'") or  # VB comment
                line.startswith('--') or  # SQL comment
                line.startswith('#'))

    def _normalize_for_hashing(self, lines: List[str]) -> str:
        """Normalize code block for hash-based comparison (Type 1)"""
        normalized = []
        for line in lines:
            stripped = line.strip()
            if stripped and not self._is_comment_only(stripped):
                normalized.append(stripped)
        return '\n'.join(normalized)

    def _normalize_identifiers(self, code: str) -> str:
        """Normalize identifiers for Type 2 detection"""
        # Replace identifiers with placeholders
        # This is a simplified version - full tool has more sophisticated logic
        normalized = re.sub(r'\b[a-z_][a-zA-Z0-9_]*\b', 'ID', code)
        normalized = re.sub(r'\b[A-Z][a-zA-Z0-9_]*\b', 'TYPE', normalized)
        normalized = re.sub(r'\b\d+\b', 'NUM', normalized)
        normalized = re.sub(r'"[^"]*"', 'STR', normalized)
        normalized = re.sub(r"'[^']*'", 'STR', normalized)
        return normalized

    def _similarity(self, a: str, b: str) -> float:
        """Calculate similarity ratio between two strings (Type 3)"""
        return SequenceMatcher(None, a, b).ratio()

    async def scan(self) -> ScanResult:
        """Execute the duplication analysis"""
        started_at = datetime.now()
        findings: List[ScanFinding] = []

        # Clone tracking
        type1_clones: Dict[str, List[Dict]] = defaultdict(list)  # hash -> [locations]
        type2_clones: Dict[str, List[Dict]] = defaultdict(list)
        type3_pairs: List[Dict] = []  # Near-miss pairs

        files_scanned = 0
        total_loc = 0
        total_blocks = 0
        duplicate_blocks = 0

        extensions = {'.cs', '.vb', '.sql', '.js', '.ts', '.asp', '.aspx'}
        excluded_dirs = {
            'bin', 'obj', 'node_modules', '.git', '.vs', 'packages',
            'TestResults', 'Debug', 'Release', '.nuget', '__pycache__',
            'bower_components', 'vendor', 'dist', 'build', '.venv', 'venv'
        }

        # Store all code blocks for Type 3 comparison
        all_blocks: List[Dict] = []

        try:
            for root, dirs, files in os.walk(self.project_path):
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
                            lines = f.readlines()
                            total_loc += len(lines)
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")
                        continue

                    # Analyze blocks
                    if len(lines) < self.MIN_BLOCK_SIZE:
                        continue

                    for i in range(len(lines) - self.MIN_BLOCK_SIZE + 1):
                        block_lines = lines[i:i + self.MIN_BLOCK_SIZE]
                        total_blocks += 1

                        # Type 1: Exact clone
                        normalized = self._normalize_for_hashing(block_lines)
                        if not normalized or len(normalized) < 50:
                            continue

                        block_hash = hashlib.sha256(normalized.encode()).hexdigest()
                        type1_clones[block_hash].append({
                            'file': rel_path,
                            'start_line': i + 1,
                            'end_line': i + self.MIN_BLOCK_SIZE,
                            'content': ''.join(block_lines[:3]) + '...'  # Preview
                        })

                        # Type 2: Renamed clone
                        normalized_ids = self._normalize_identifiers(normalized)
                        id_hash = hashlib.sha256(normalized_ids.encode()).hexdigest()
                        type2_clones[id_hash].append({
                            'file': rel_path,
                            'start_line': i + 1,
                            'end_line': i + self.MIN_BLOCK_SIZE,
                        })

                        # Store for Type 3 (limited to prevent O(n^2) explosion)
                        if len(all_blocks) < 1000:
                            all_blocks.append({
                                'file': rel_path,
                                'start_line': i + 1,
                                'content': normalized,
                                'hash': block_hash
                            })

            # Count duplicates (Type 1)
            type1_count = 0
            for block_hash, locations in type1_clones.items():
                if len(locations) > 1:
                    type1_count += 1
                    duplicate_blocks += len(locations)

                    # Create finding
                    first = locations[0]
                    other_locations = [f"{l['file']}:{l['start_line']}" for l in locations[1:]]

                    findings.append(ScanFinding(
                        scanner=self.name,
                        rule_id="type-1-clone",
                        message=f"Exact code clone found in {len(locations)} locations",
                        severity=Severity.MEDIUM if len(locations) > 3 else Severity.LOW,
                        finding_type=FindingType.DUPLICATION,
                        file_path=first['file'],
                        line_number=first['start_line'],
                        end_line=first['end_line'],
                        recommendation="Extract common code to shared method or class",
                        effort_minutes=15,
                        metadata={
                            "clone_type": "Type 1 (Exact)",
                            "locations": other_locations[:10],
                            "total_occurrences": len(locations)
                        }
                    ))

            # Count Type 2 clones (only those not already caught by Type 1)
            type2_count = 0
            type1_hashes = set(h for h, locs in type1_clones.items() if len(locs) > 1)

            for id_hash, locations in type2_clones.items():
                if len(locations) > 1:
                    # Check if this is a Type 1 clone (skip if so)
                    sample_file = locations[0]['file']
                    is_type1 = False
                    for block in all_blocks:
                        if block['file'] == sample_file and block['hash'] in type1_hashes:
                            is_type1 = True
                            break

                    if not is_type1:
                        type2_count += 1

                        first = locations[0]
                        findings.append(ScanFinding(
                            scanner=self.name,
                            rule_id="type-2-clone",
                            message=f"Renamed code clone (same structure) found in {len(locations)} locations",
                            severity=Severity.LOW,
                            finding_type=FindingType.DUPLICATION,
                            file_path=first['file'],
                            line_number=first['start_line'],
                            recommendation="Consider extracting common logic with parameterization",
                            effort_minutes=20,
                            metadata={
                                "clone_type": "Type 2 (Renamed)",
                                "total_occurrences": len(locations)
                            }
                        ))

            # Type 3: Near-miss clones (sample-based to avoid O(n^2))
            type3_count = 0
            checked_pairs: Set[Tuple[str, str]] = set()

            for i, block_a in enumerate(all_blocks[:500]):  # Limit for performance
                for block_b in all_blocks[i+1:i+100]:  # Only compare nearby blocks
                    if block_a['hash'] == block_b['hash']:
                        continue  # Already a Type 1 clone

                    pair_key = (block_a['hash'], block_b['hash'])
                    if pair_key in checked_pairs:
                        continue
                    checked_pairs.add(pair_key)

                    similarity = self._similarity(block_a['content'], block_b['content'])
                    if 0.7 <= similarity < 1.0:
                        type3_count += 1
                        type3_pairs.append({
                            'file_a': block_a['file'],
                            'line_a': block_a['start_line'],
                            'file_b': block_b['file'],
                            'line_b': block_b['start_line'],
                            'similarity': round(similarity * 100, 1)
                        })

            # Calculate duplication percentage
            duplication_pct = (duplicate_blocks / total_blocks * 100) if total_blocks > 0 else 0
            rating = self._calculate_rating(duplication_pct)
            rating_stars = self._get_rating_stars(rating)

            # Build metrics
            metrics = ScanMetrics(
                files_scanned=files_scanned,
                lines_of_code=total_loc,
                duplication_percentage=round(duplication_pct, 2)
            )

            metrics.metadata = {
                "rating": rating,
                "rating_stars": rating_stars,
                "total_blocks": total_blocks,
                "duplicate_blocks": duplicate_blocks,
                "duplication_percentage": round(duplication_pct, 2),
                "type_1_clones": type1_count,
                "type_2_clones": type2_count,
                "type_3_near_miss": type3_count,
                "clone_distribution": {
                    "type_1_exact": type1_count,
                    "type_2_renamed": type2_count,
                    "type_3_similar": type3_count
                },
                "sample_type3_pairs": type3_pairs[:10]  # Top 10 near-misses
            }

            completed_at = datetime.now()

            logger.info(
                f"Duplication scan complete: {duplication_pct:.2f}% duplication, "
                f"Type1: {type1_count}, Type2: {type2_count}, Type3: {type3_count}, "
                f"rating: {rating_stars}"
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
            logger.error(f"Duplication scan failed: {e}")
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
            "duplication_threshold": 5,  # percentage
            "min_block_size": self.MIN_BLOCK_SIZE,
            "type3_similarity_threshold": 0.7,
            "quality_tools_path": str(QUALITY_TOOLS_PATH),
        }
