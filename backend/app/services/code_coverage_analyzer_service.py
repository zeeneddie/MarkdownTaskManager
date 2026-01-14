"""
CodeCoverageAnalyzerService - Week 132-133

Unified code coverage analysis across multiple test frameworks.

Agent: Tessa (Test Engineer)
"""
import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.models.dead_code import (
    CodeCoverageResult,
    CoverageSource,
    FileCoverage,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Coverage File Patterns
# ============================================================================

COVERAGE_FILE_PATTERNS = {
    CoverageSource.JEST: [
        "coverage/coverage-final.json",
        "coverage/coverage-summary.json",
    ],
    CoverageSource.ISTANBUL: [
        "coverage/coverage-final.json",
        ".nyc_output/coverage.json",
    ],
    CoverageSource.PYTEST_COV: [
        ".coverage",
        "coverage.json",
        "htmlcov/status.json",
    ],
    CoverageSource.COVERLET: [
        "coverage.cobertura.xml",
        "coverage.opencover.xml",
    ],
    CoverageSource.DOTCOVER: [
        "dotCover.Output.xml",
        "coverage-report.xml",
    ],
    CoverageSource.JACOCO: [
        "target/site/jacoco/jacoco.xml",
        "build/reports/jacoco/test/jacocoTestReport.xml",
    ],
}

LCOV_PATTERNS = ["lcov.info", "coverage/lcov.info", "coverage.lcov"]


@dataclass
class CoverageThresholds:
    """Coverage thresholds for quality gates."""
    line_coverage: float = 80.0
    branch_coverage: float = 70.0
    function_coverage: float = 80.0


class CodeCoverageAnalyzerService:
    """
    Unified code coverage analysis service.

    Supports:
    - Jest/Istanbul (JavaScript/TypeScript)
    - pytest-cov (Python)
    - Coverlet/dotCover (.NET)
    - JaCoCo (Java)
    - LCOV format (multiple languages)
    """

    def __init__(self, thresholds: Optional[CoverageThresholds] = None):
        self._thresholds = thresholds or CoverageThresholds()

    def analyze(
        self,
        project_path: Path,
        coverage_source: Optional[CoverageSource] = None,
        include_file_details: bool = True,
    ) -> CodeCoverageResult:
        """
        Analyze code coverage for a project.

        Args:
            project_path: Path to the project
            coverage_source: Specific source to use (auto-detect if None)
            include_file_details: Include per-file coverage details

        Returns:
            CodeCoverageResult with analysis
        """
        start_time = time.time()

        result = CodeCoverageResult(
            project_path=str(project_path),
            coverage_source=coverage_source or CoverageSource.MANUAL,
        )

        if not project_path.exists():
            result.success = False
            result.errors.append(f"Project path does not exist: {project_path}")
            return result

        try:
            # Auto-detect coverage source if not specified
            if coverage_source is None:
                coverage_source, coverage_file = self._detect_coverage_source(project_path)
                result.coverage_source = coverage_source
            else:
                coverage_file = self._find_coverage_file(project_path, coverage_source)

            if coverage_file is None:
                result.success = False
                result.errors.append(
                    "No coverage data found. Run tests with coverage enabled."
                )
                return result

            # Parse coverage data
            self._parse_coverage(result, coverage_file, coverage_source, include_file_details)

            # Calculate percentages
            if result.total_lines > 0:
                result.line_coverage_percentage = (
                    result.covered_lines / result.total_lines * 100
                )
            if result.total_branches > 0:
                result.branch_coverage_percentage = (
                    result.covered_branches / result.total_branches * 100
                )
            if result.total_functions > 0:
                result.function_coverage_percentage = (
                    result.covered_functions / result.total_functions * 100
                )

            # Identify uncovered files (0% coverage)
            result.uncovered_files = [
                fc.file_path for fc in result.file_coverage
                if fc.line_coverage == 0.0
            ]

            # Identify critical uncovered code
            result.critical_uncovered = self._identify_critical_uncovered(result)

        except Exception as e:
            logger.error(f"Coverage analysis failed: {e}")
            result.success = False
            result.errors.append(str(e))

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    def _detect_coverage_source(
        self, project_path: Path
    ) -> Tuple[CoverageSource, Optional[Path]]:
        """Auto-detect coverage source and file."""
        # Check for LCOV first (common format)
        for pattern in LCOV_PATTERNS:
            for path in project_path.rglob(pattern):
                return CoverageSource.ISTANBUL, path

        # Check for specific coverage tools
        for source, patterns in COVERAGE_FILE_PATTERNS.items():
            for pattern in patterns:
                for path in project_path.rglob(pattern):
                    return source, path

        return CoverageSource.MANUAL, None

    def _find_coverage_file(
        self, project_path: Path, source: CoverageSource
    ) -> Optional[Path]:
        """Find coverage file for specific source."""
        patterns = COVERAGE_FILE_PATTERNS.get(source, [])

        for pattern in patterns:
            for path in project_path.rglob(pattern):
                return path

        # Also check LCOV
        for pattern in LCOV_PATTERNS:
            for path in project_path.rglob(pattern):
                return path

        return None

    def _parse_coverage(
        self,
        result: CodeCoverageResult,
        coverage_file: Path,
        source: CoverageSource,
        include_file_details: bool,
    ):
        """Parse coverage file based on source type."""
        if coverage_file.suffix == ".json":
            self._parse_json_coverage(result, coverage_file, include_file_details)
        elif coverage_file.suffix == ".xml":
            self._parse_xml_coverage(result, coverage_file, source, include_file_details)
        elif coverage_file.name in LCOV_PATTERNS or "lcov" in coverage_file.name.lower():
            self._parse_lcov_coverage(result, coverage_file, include_file_details)
        elif coverage_file.name == ".coverage":
            self._parse_python_coverage(result, coverage_file, include_file_details)
        else:
            result.errors.append(f"Unknown coverage file format: {coverage_file.name}")

    def _parse_json_coverage(
        self, result: CodeCoverageResult, coverage_file: Path, include_file_details: bool
    ):
        """Parse Istanbul/Jest JSON coverage format."""
        try:
            data = json.loads(coverage_file.read_text())

            # Check if this is a summary file
            if "total" in data:
                self._parse_coverage_summary(result, data)
                return

            # Full coverage data
            for file_path, file_data in data.items():
                if not isinstance(file_data, dict):
                    continue

                # Line coverage
                line_map = file_data.get("statementMap", {})
                line_hits = file_data.get("s", {})

                total_lines = len(line_map)
                covered_lines = len([h for h in line_hits.values() if h > 0])

                result.total_lines += total_lines
                result.covered_lines += covered_lines
                result.uncovered_lines += total_lines - covered_lines

                # Branch coverage
                branch_map = file_data.get("branchMap", {})
                branch_hits = file_data.get("b", {})

                for branch_id, hits in branch_hits.items():
                    if isinstance(hits, list):
                        result.total_branches += len(hits)
                        result.covered_branches += len([h for h in hits if h > 0])
                    else:
                        result.total_branches += 1
                        if hits > 0:
                            result.covered_branches += 1

                # Function coverage
                fn_map = file_data.get("fnMap", {})
                fn_hits = file_data.get("f", {})

                result.total_functions += len(fn_map)
                result.covered_functions += len([h for h in fn_hits.values() if h > 0])

                # Per-file details
                if include_file_details:
                    fc = FileCoverage(
                        file_path=file_path,
                        total_lines=total_lines,
                        covered_lines=covered_lines,
                        uncovered_lines=total_lines - covered_lines,
                        line_coverage=(
                            covered_lines / total_lines * 100 if total_lines > 0 else 0
                        ),
                        total_functions=len(fn_map),
                        covered_functions=len([h for h in fn_hits.values() if h > 0]),
                        function_coverage=(
                            len([h for h in fn_hits.values() if h > 0]) / len(fn_map) * 100
                            if fn_map else 0
                        ),
                        uncovered_line_numbers=[
                            line_map.get(str(lid), {}).get("start", {}).get("line", 0)
                            for lid, hits in line_hits.items()
                            if hits == 0
                        ],
                    )
                    result.file_coverage.append(fc)

        except Exception as e:
            result.errors.append(f"Error parsing JSON coverage: {e}")

    def _parse_coverage_summary(self, result: CodeCoverageResult, data: Dict[str, Any]):
        """Parse coverage summary format."""
        total = data.get("total", {})

        lines = total.get("lines", {})
        result.total_lines = lines.get("total", 0)
        result.covered_lines = lines.get("covered", 0)
        result.uncovered_lines = result.total_lines - result.covered_lines

        branches = total.get("branches", {})
        result.total_branches = branches.get("total", 0)
        result.covered_branches = branches.get("covered", 0)

        functions = total.get("functions", {})
        result.total_functions = functions.get("total", 0)
        result.covered_functions = functions.get("covered", 0)

    def _parse_xml_coverage(
        self,
        result: CodeCoverageResult,
        coverage_file: Path,
        source: CoverageSource,
        include_file_details: bool,
    ):
        """Parse XML coverage format (Cobertura, JaCoCo, etc.)."""
        try:
            tree = ET.parse(coverage_file)
            root = tree.getroot()

            # Cobertura format
            if root.tag == "coverage":
                self._parse_cobertura_xml(result, root, include_file_details)
            # JaCoCo format
            elif root.tag == "report":
                self._parse_jacoco_xml(result, root, include_file_details)
            # OpenCover format
            elif root.tag == "CoverageSession":
                self._parse_opencover_xml(result, root, include_file_details)
            else:
                result.errors.append(f"Unknown XML coverage format: {root.tag}")

        except Exception as e:
            result.errors.append(f"Error parsing XML coverage: {e}")

    def _parse_cobertura_xml(
        self, result: CodeCoverageResult, root: ET.Element, include_file_details: bool
    ):
        """Parse Cobertura XML format."""
        # Overall stats from root attributes
        result.line_coverage_percentage = float(root.get("line-rate", 0)) * 100
        result.branch_coverage_percentage = float(root.get("branch-rate", 0)) * 100

        for package in root.findall(".//package"):
            for cls in package.findall("classes/class"):
                filename = cls.get("filename", "")

                lines = cls.findall("lines/line")
                total_lines = len(lines)
                covered_lines = len([l for l in lines if int(l.get("hits", 0)) > 0])

                result.total_lines += total_lines
                result.covered_lines += covered_lines
                result.uncovered_lines += total_lines - covered_lines

                # Branch info from line attributes
                for line in lines:
                    if line.get("branch") == "true":
                        condition_coverage = line.get("condition-coverage", "")
                        match = re.search(r"(\d+)/(\d+)", condition_coverage)
                        if match:
                            result.covered_branches += int(match.group(1))
                            result.total_branches += int(match.group(2))

                # Method count
                methods = cls.findall("methods/method")
                result.total_functions += len(methods)
                result.covered_functions += len([
                    m for m in methods
                    if any(int(l.get("hits", 0)) > 0 for l in m.findall("lines/line"))
                ])

                if include_file_details:
                    fc = FileCoverage(
                        file_path=filename,
                        total_lines=total_lines,
                        covered_lines=covered_lines,
                        uncovered_lines=total_lines - covered_lines,
                        line_coverage=(
                            covered_lines / total_lines * 100 if total_lines > 0 else 0
                        ),
                    )
                    result.file_coverage.append(fc)

    def _parse_jacoco_xml(
        self, result: CodeCoverageResult, root: ET.Element, include_file_details: bool
    ):
        """Parse JaCoCo XML format."""
        for counter in root.findall(".//counter"):
            counter_type = counter.get("type")
            covered = int(counter.get("covered", 0))
            missed = int(counter.get("missed", 0))

            if counter_type == "LINE":
                result.total_lines += covered + missed
                result.covered_lines += covered
                result.uncovered_lines += missed
            elif counter_type == "BRANCH":
                result.total_branches += covered + missed
                result.covered_branches += covered
            elif counter_type == "METHOD":
                result.total_functions += covered + missed
                result.covered_functions += covered

    def _parse_opencover_xml(
        self, result: CodeCoverageResult, root: ET.Element, include_file_details: bool
    ):
        """Parse OpenCover XML format."""
        for module in root.findall(".//Module"):
            for cls in module.findall(".//Class"):
                for method in cls.findall("Methods/Method"):
                    result.total_functions += 1

                    # Check if method was visited
                    visited = method.get("visited", "false") == "true"
                    if visited:
                        result.covered_functions += 1

                    # Line coverage
                    for seq_point in method.findall("SequencePoints/SequencePoint"):
                        result.total_lines += 1
                        if int(seq_point.get("vc", 0)) > 0:
                            result.covered_lines += 1
                        else:
                            result.uncovered_lines += 1

                    # Branch coverage
                    for branch_point in method.findall("BranchPoints/BranchPoint"):
                        result.total_branches += 1
                        if int(branch_point.get("vc", 0)) > 0:
                            result.covered_branches += 1

    def _parse_lcov_coverage(
        self, result: CodeCoverageResult, coverage_file: Path, include_file_details: bool
    ):
        """Parse LCOV format coverage data."""
        try:
            content = coverage_file.read_text()
            current_file = None
            current_fc = None

            for line in content.split("\n"):
                line = line.strip()

                if line.startswith("SF:"):
                    current_file = line[3:]
                    if include_file_details:
                        current_fc = FileCoverage(file_path=current_file)

                elif line.startswith("LF:"):
                    total = int(line[3:])
                    result.total_lines += total
                    if current_fc:
                        current_fc.total_lines = total

                elif line.startswith("LH:"):
                    covered = int(line[3:])
                    result.covered_lines += covered
                    if current_fc:
                        current_fc.covered_lines = covered
                        current_fc.uncovered_lines = current_fc.total_lines - covered

                elif line.startswith("BRF:"):
                    result.total_branches += int(line[4:])
                    if current_fc:
                        current_fc.total_branches = int(line[4:])

                elif line.startswith("BRH:"):
                    result.covered_branches += int(line[4:])
                    if current_fc:
                        current_fc.covered_branches = int(line[4:])

                elif line.startswith("FNF:"):
                    result.total_functions += int(line[4:])
                    if current_fc:
                        current_fc.total_functions = int(line[4:])

                elif line.startswith("FNH:"):
                    result.covered_functions += int(line[4:])
                    if current_fc:
                        current_fc.covered_functions = int(line[4:])

                elif line.startswith("DA:"):
                    # Line data: DA:line_number,execution_count
                    parts = line[3:].split(",")
                    if len(parts) >= 2 and current_fc:
                        if int(parts[1]) == 0:
                            current_fc.uncovered_line_numbers.append(int(parts[0]))

                elif line == "end_of_record":
                    if current_fc and include_file_details:
                        if current_fc.total_lines > 0:
                            current_fc.line_coverage = (
                                current_fc.covered_lines / current_fc.total_lines * 100
                            )
                        result.file_coverage.append(current_fc)
                    current_fc = None

            result.uncovered_lines = result.total_lines - result.covered_lines

        except Exception as e:
            result.errors.append(f"Error parsing LCOV coverage: {e}")

    def _parse_python_coverage(
        self, result: CodeCoverageResult, coverage_file: Path, include_file_details: bool
    ):
        """Parse Python .coverage file (SQLite format)."""
        try:
            import sqlite3

            conn = sqlite3.connect(str(coverage_file))
            cursor = conn.cursor()

            # Get file data
            cursor.execute("SELECT id, path FROM file")
            files = {row[0]: row[1] for row in cursor.fetchall()}

            for file_id, file_path in files.items():
                cursor.execute(
                    "SELECT numbits FROM line_bits WHERE file_id = ?",
                    (file_id,)
                )
                row = cursor.fetchone()

                if row:
                    # numbits is a blob encoding which lines are covered
                    # This is a simplified version - actual parsing is complex
                    pass

            conn.close()

        except ImportError:
            # Fall back to coverage.py's JSON export
            json_file = coverage_file.parent / "coverage.json"
            if json_file.exists():
                self._parse_json_coverage(result, json_file, include_file_details)
            else:
                result.errors.append(
                    "Python coverage SQLite format requires 'coverage' package. "
                    "Run 'coverage json' to export to JSON format."
                )
        except Exception as e:
            result.errors.append(f"Error parsing Python coverage: {e}")

    def _identify_critical_uncovered(
        self, result: CodeCoverageResult
    ) -> List[Dict[str, Any]]:
        """Identify critical uncovered code patterns."""
        critical = []

        for fc in result.file_coverage:
            # Large files with low coverage
            if fc.total_lines > 100 and fc.line_coverage < 50:
                critical.append({
                    "file": fc.file_path,
                    "reason": "Large file with low coverage",
                    "lines": fc.total_lines,
                    "coverage": fc.line_coverage,
                    "priority": "high",
                })

            # Files with 0% coverage
            if fc.line_coverage == 0 and fc.total_lines > 10:
                critical.append({
                    "file": fc.file_path,
                    "reason": "No test coverage",
                    "lines": fc.total_lines,
                    "coverage": 0,
                    "priority": "critical",
                })

            # Files with many uncovered lines in a row (dead branches)
            if len(fc.uncovered_line_numbers) > 20:
                # Check for consecutive uncovered lines
                consecutive = 0
                max_consecutive = 0
                prev_line = 0

                for line_num in sorted(fc.uncovered_line_numbers):
                    if line_num == prev_line + 1:
                        consecutive += 1
                    else:
                        consecutive = 1
                    max_consecutive = max(max_consecutive, consecutive)
                    prev_line = line_num

                if max_consecutive > 10:
                    critical.append({
                        "file": fc.file_path,
                        "reason": f"Large uncovered block ({max_consecutive} lines)",
                        "lines": fc.total_lines,
                        "coverage": fc.line_coverage,
                        "priority": "medium",
                    })

        return critical

    def check_thresholds(self, result: CodeCoverageResult) -> Dict[str, Any]:
        """
        Check if coverage meets thresholds.

        Returns:
            Dict with pass/fail status and details
        """
        checks = {
            "line_coverage": {
                "actual": result.line_coverage_percentage,
                "threshold": self._thresholds.line_coverage,
                "passed": result.line_coverage_percentage >= self._thresholds.line_coverage,
            },
            "branch_coverage": {
                "actual": result.branch_coverage_percentage,
                "threshold": self._thresholds.branch_coverage,
                "passed": result.branch_coverage_percentage >= self._thresholds.branch_coverage,
            },
            "function_coverage": {
                "actual": result.function_coverage_percentage,
                "threshold": self._thresholds.function_coverage,
                "passed": result.function_coverage_percentage >= self._thresholds.function_coverage,
            },
        }

        all_passed = all(c["passed"] for c in checks.values())

        return {
            "passed": all_passed,
            "checks": checks,
            "message": "All coverage thresholds met" if all_passed else "Coverage below threshold",
        }

    def compare_coverage(
        self, current: CodeCoverageResult, previous: CodeCoverageResult
    ) -> Dict[str, Any]:
        """
        Compare two coverage results.

        Returns:
            Dict with coverage diff and trends
        """
        return {
            "line_coverage_diff": (
                current.line_coverage_percentage - previous.line_coverage_percentage
            ),
            "branch_coverage_diff": (
                current.branch_coverage_percentage - previous.branch_coverage_percentage
            ),
            "function_coverage_diff": (
                current.function_coverage_percentage - previous.function_coverage_percentage
            ),
            "total_lines_diff": current.total_lines - previous.total_lines,
            "covered_lines_diff": current.covered_lines - previous.covered_lines,
            "improved": (
                current.line_coverage_percentage > previous.line_coverage_percentage
            ),
            "regression": (
                current.line_coverage_percentage < previous.line_coverage_percentage - 1.0
            ),
        }
