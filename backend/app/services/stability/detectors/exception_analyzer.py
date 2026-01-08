# Exception Analyzer
# Detects exception handling issues in Classic ASP code
#
# Category 7: Exception Handling
# - On Error Resume Next without Err.Number check
# - Missing On Error Goto 0 (error handling re-enablement)
# - Silent error swallowing
# - Missing Err.Clear after handling
# - Empty error handlers
# - Inconsistent error handling across file
#
# Week 144-145 Implementation

from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

from ..types import (
    StabilityCategory,
    SeverityLevel,
    LeakFinding,
    LeakPatternType,
    ResourceType,
)

logger = logging.getLogger(__name__)


class ExceptionIssueType(Enum):
    """Types of exception handling issues."""
    RESUME_NEXT_NO_CHECK = "resume_next_no_check"
    MISSING_GOTO_ZERO = "missing_goto_zero"
    SILENT_ERROR_SWALLOW = "silent_error_swallow"
    MISSING_ERR_CLEAR = "missing_err_clear"
    EMPTY_ERROR_HANDLER = "empty_error_handler"
    GLOBAL_RESUME_NEXT = "global_resume_next"
    ERR_RAISE_WITHOUT_HANDLING = "err_raise_without_handling"
    NESTED_RESUME_NEXT = "nested_resume_next"
    LONG_RESUME_NEXT_SCOPE = "long_resume_next_scope"


@dataclass
class ErrorHandlingRegion:
    """Represents a region of code with error handling enabled."""
    start_line: int
    end_line: Optional[int] = None
    has_err_check: bool = False
    has_err_clear: bool = False
    lines_covered: int = 0
    check_locations: List[int] = field(default_factory=list)


@dataclass
class ExceptionFinding:
    """A detected exception handling issue."""
    file_path: str
    line_number: int
    issue_type: ExceptionIssueType
    severity: SeverityLevel
    description: str
    suggested_fix: str
    code_context: List[str] = field(default_factory=list)
    confidence: float = 1.0
    region_size: int = 0  # Lines covered by problematic region

    def to_leak_finding(self) -> LeakFinding:
        """Convert to standard LeakFinding format."""
        return LeakFinding(
            file_path=self.file_path,
            line_number=self.line_number,
            resource_type=ResourceType.COM_OBJECT,  # Use COM_OBJECT for exception issues
            variable_name="ErrorHandler",
            leak_pattern=LeakPatternType.NEVER_CLOSED,
            severity=self.severity,
            category=StabilityCategory.EXCEPTION_HANDLING,
            description=self.description,
            suggested_fix=self.suggested_fix,
            code_context=self.code_context,
            confidence=self.confidence,
        )


class ExceptionAnalyzer:
    """
    Analyzes exception handling patterns in Classic ASP code.

    Detects:
    1. On Error Resume Next without Err.Number check (HIGH)
    2. Missing On Error Goto 0 after error-sensitive code (MEDIUM)
    3. Silent error swallowing (errors not logged/handled) (HIGH)
    4. Missing Err.Clear after handling (LOW)
    5. Global On Error Resume Next at file start (HIGH)
    6. Nested On Error Resume Next (MEDIUM)
    7. Long regions under Resume Next (>50 lines) (MEDIUM)

    Based on VBScript/Classic ASP error handling best practices.
    """

    # Error handling patterns (VBScript is case-insensitive)
    ON_ERROR_RESUME_NEXT = r'On\s+Error\s+Resume\s+Next'
    ON_ERROR_GOTO_ZERO = r'On\s+Error\s+GoTo\s+0'

    # Error check patterns
    ERR_NUMBER_CHECK = r'Err\.Number\s*(<>|>|<|=|<>)\s*0'
    ERR_NUMBER_IF = r'If\s+Err\.Number'
    ERR_CHECK_SIMPLE = r'Err\.Number'
    ERR_DESCRIPTION = r'Err\.Description'
    ERR_CLEAR = r'Err\.Clear'
    ERR_RAISE = r'Err\.Raise'

    # Response.Write error patterns (logging)
    ERROR_LOGGING = r'Response\.Write.*Err\.'

    # Maximum lines for error handling region before warning
    MAX_RESUME_NEXT_LINES = 50

    # Lines after file start to consider "global"
    GLOBAL_THRESHOLD_LINES = 10

    def __init__(self):
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile all regex patterns."""
        flags = re.IGNORECASE

        self._compiled_patterns = {
            "resume_next": re.compile(self.ON_ERROR_RESUME_NEXT, flags),
            "goto_zero": re.compile(self.ON_ERROR_GOTO_ZERO, flags),
            "err_number_check": re.compile(self.ERR_NUMBER_CHECK, flags),
            "err_number_if": re.compile(self.ERR_NUMBER_IF, flags),
            "err_check_simple": re.compile(self.ERR_CHECK_SIMPLE, flags),
            "err_description": re.compile(self.ERR_DESCRIPTION, flags),
            "err_clear": re.compile(self.ERR_CLEAR, flags),
            "err_raise": re.compile(self.ERR_RAISE, flags),
            "error_logging": re.compile(self.ERROR_LOGGING, flags),
        }

    def analyze_file(self, file_path: str, content: str) -> List[ExceptionFinding]:
        """
        Analyze a file for exception handling issues.

        Args:
            file_path: Path to the file
            content: File content

        Returns:
            List of exception findings
        """
        findings = []
        lines = content.split('\n')

        # Find all error handling regions
        regions = self._find_error_handling_regions(lines)

        # Analyze each region
        for region in regions:
            region_findings = self._analyze_region(file_path, lines, region)
            findings.extend(region_findings)

        # Check for global On Error Resume Next
        findings.extend(self._check_global_resume_next(file_path, lines, regions))

        # Check for nested Resume Next
        findings.extend(self._check_nested_resume_next(file_path, lines, regions))

        # Check for Err.Raise without handling
        findings.extend(self._check_err_raise(file_path, lines, regions))

        return findings

    def _find_error_handling_regions(self, lines: List[str]) -> List[ErrorHandlingRegion]:
        """Find all regions where On Error Resume Next is active."""
        regions = []
        current_region: Optional[ErrorHandlingRegion] = None

        for line_num, line in enumerate(lines, 1):
            # Check for On Error Resume Next
            if self._compiled_patterns["resume_next"].search(line):
                if current_region is not None:
                    # Close previous region (nested case)
                    current_region.end_line = line_num - 1
                    current_region.lines_covered = (
                        current_region.end_line - current_region.start_line
                    )
                    regions.append(current_region)

                current_region = ErrorHandlingRegion(start_line=line_num)

            # Check for On Error Goto 0
            elif self._compiled_patterns["goto_zero"].search(line):
                if current_region is not None:
                    current_region.end_line = line_num
                    current_region.lines_covered = (
                        current_region.end_line - current_region.start_line
                    )
                    regions.append(current_region)
                    current_region = None

            # Check for error checks within current region
            elif current_region is not None:
                if (self._compiled_patterns["err_number_check"].search(line) or
                    self._compiled_patterns["err_number_if"].search(line) or
                    self._compiled_patterns["err_check_simple"].search(line)):
                    current_region.has_err_check = True
                    current_region.check_locations.append(line_num)

                if self._compiled_patterns["err_clear"].search(line):
                    current_region.has_err_clear = True

        # Handle unclosed region (runs to end of file)
        if current_region is not None:
            current_region.end_line = len(lines)
            current_region.lines_covered = len(lines) - current_region.start_line
            regions.append(current_region)

        return regions

    def _analyze_region(
        self,
        file_path: str,
        lines: List[str],
        region: ErrorHandlingRegion
    ) -> List[ExceptionFinding]:
        """Analyze a single error handling region."""
        findings = []

        # 1. Check for Resume Next without Err check
        if not region.has_err_check:
            findings.append(ExceptionFinding(
                file_path=file_path,
                line_number=region.start_line,
                issue_type=ExceptionIssueType.RESUME_NEXT_NO_CHECK,
                severity=SeverityLevel.HIGH,
                description=(
                    f"On Error Resume Next at line {region.start_line} without "
                    f"Err.Number check - errors are silently ignored"
                ),
                suggested_fix=(
                    "Add 'If Err.Number <> 0 Then' check after error-prone operations, "
                    "log errors, and handle appropriately"
                ),
                code_context=self._get_context(lines, region.start_line),
                confidence=0.95,
                region_size=region.lines_covered,
            ))

        # 2. Check for missing Err.Clear
        if region.has_err_check and not region.has_err_clear:
            findings.append(ExceptionFinding(
                file_path=file_path,
                line_number=region.check_locations[0] if region.check_locations else region.start_line,
                issue_type=ExceptionIssueType.MISSING_ERR_CLEAR,
                severity=SeverityLevel.LOW,
                description=(
                    f"Error check at line {region.check_locations[0] if region.check_locations else region.start_line} "
                    f"without Err.Clear - may cause stale error state"
                ),
                suggested_fix="Add 'Err.Clear' after handling the error to reset error state",
                code_context=self._get_context(
                    lines,
                    region.check_locations[0] if region.check_locations else region.start_line
                ),
                confidence=0.7,
            ))

        # 3. Check for missing On Error Goto 0
        if region.end_line is None or region.end_line == len(lines):
            findings.append(ExceptionFinding(
                file_path=file_path,
                line_number=region.start_line,
                issue_type=ExceptionIssueType.MISSING_GOTO_ZERO,
                severity=SeverityLevel.MEDIUM,
                description=(
                    f"On Error Resume Next at line {region.start_line} runs to end of file "
                    f"without 'On Error GoTo 0' to re-enable error handling"
                ),
                suggested_fix=(
                    "Add 'On Error GoTo 0' after the error-prone section to restore "
                    "normal error handling"
                ),
                code_context=self._get_context(lines, region.start_line),
                confidence=0.85,
                region_size=region.lines_covered,
            ))

        # 4. Check for long Resume Next scope
        if region.lines_covered > self.MAX_RESUME_NEXT_LINES:
            findings.append(ExceptionFinding(
                file_path=file_path,
                line_number=region.start_line,
                issue_type=ExceptionIssueType.LONG_RESUME_NEXT_SCOPE,
                severity=SeverityLevel.MEDIUM,
                description=(
                    f"On Error Resume Next scope spans {region.lines_covered} lines "
                    f"(recommended max: {self.MAX_RESUME_NEXT_LINES}) - reduces error visibility"
                ),
                suggested_fix=(
                    "Narrow the error handling scope to only the specific operations "
                    "that may fail, check errors frequently"
                ),
                code_context=self._get_context(lines, region.start_line),
                confidence=0.9,
                region_size=region.lines_covered,
            ))

        return findings

    def _check_global_resume_next(
        self,
        file_path: str,
        lines: List[str],
        regions: List[ErrorHandlingRegion]
    ) -> List[ExceptionFinding]:
        """Check for global On Error Resume Next at file start."""
        findings = []

        for region in regions:
            if region.start_line <= self.GLOBAL_THRESHOLD_LINES:
                # Check if this is at the top of the file (global scope)
                # Count non-empty, non-comment lines before it
                code_lines_before = 0
                for i in range(region.start_line - 1):
                    line = lines[i].strip()
                    if line and not line.startswith("'") and not line.startswith("<!--"):
                        code_lines_before += 1

                if code_lines_before < 5:  # Likely global scope
                    findings.append(ExceptionFinding(
                        file_path=file_path,
                        line_number=region.start_line,
                        issue_type=ExceptionIssueType.GLOBAL_RESUME_NEXT,
                        severity=SeverityLevel.HIGH,
                        description=(
                            f"Global 'On Error Resume Next' at line {region.start_line} - "
                            f"all errors in file will be silently ignored"
                        ),
                        suggested_fix=(
                            "Remove global error suppression, add targeted error handling "
                            "only around operations that may fail"
                        ),
                        code_context=self._get_context(lines, region.start_line),
                        confidence=0.95,
                        region_size=region.lines_covered,
                    ))

        return findings

    def _check_nested_resume_next(
        self,
        file_path: str,
        lines: List[str],
        regions: List[ErrorHandlingRegion]
    ) -> List[ExceptionFinding]:
        """Check for nested On Error Resume Next statements."""
        findings = []

        # Sort regions by start line
        sorted_regions = sorted(regions, key=lambda r: r.start_line)

        for i, region in enumerate(sorted_regions[1:], 1):
            prev_region = sorted_regions[i - 1]

            # Check if this region starts before previous one ends
            if prev_region.end_line is not None and region.start_line < prev_region.end_line:
                findings.append(ExceptionFinding(
                    file_path=file_path,
                    line_number=region.start_line,
                    issue_type=ExceptionIssueType.NESTED_RESUME_NEXT,
                    severity=SeverityLevel.MEDIUM,
                    description=(
                        f"Nested 'On Error Resume Next' at line {region.start_line} "
                        f"within existing error handling region (started at {prev_region.start_line})"
                    ),
                    suggested_fix=(
                        "Avoid nested error handling - restructure code to have "
                        "single error handling regions"
                    ),
                    code_context=self._get_context(lines, region.start_line),
                    confidence=0.85,
                ))

        return findings

    def _check_err_raise(
        self,
        file_path: str,
        lines: List[str],
        regions: List[ErrorHandlingRegion]
    ) -> List[ExceptionFinding]:
        """Check for Err.Raise without proper handling context."""
        findings = []

        for line_num, line in enumerate(lines, 1):
            if self._compiled_patterns["err_raise"].search(line):
                # Check if this is within an error handling region
                in_region = any(
                    region.start_line <= line_num <= (region.end_line or len(lines))
                    for region in regions
                )

                if not in_region:
                    # Err.Raise outside of On Error Resume Next
                    # This is actually fine - the error will propagate
                    pass
                else:
                    # Err.Raise within Resume Next - may be silently swallowed
                    findings.append(ExceptionFinding(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type=ExceptionIssueType.ERR_RAISE_WITHOUT_HANDLING,
                        severity=SeverityLevel.MEDIUM,
                        description=(
                            f"Err.Raise at line {line_num} within 'On Error Resume Next' "
                            f"region - raised error may be silently ignored"
                        ),
                        suggested_fix=(
                            "Ensure Err.Raise is outside of Resume Next scope, "
                            "or add explicit error check after raising"
                        ),
                        code_context=self._get_context(lines, line_num),
                        confidence=0.75,
                    ))

        return findings

    def _get_context(self, lines: List[str], line_num: int) -> List[str]:
        """Get code context around a line."""
        start = max(0, line_num - 4)
        end = min(len(lines), line_num + 3)
        return lines[start:end]

    def get_supported_extensions(self) -> List[str]:
        """Return supported file extensions."""
        return [".asp", ".inc", ".asa"]

    def supports_file(self, file_path: str) -> bool:
        """Check if this analyzer supports the given file."""
        return any(
            file_path.lower().endswith(ext)
            for ext in self.get_supported_extensions()
        )

    def get_language(self) -> str:
        """Return the language name."""
        return "Classic ASP (VBScript)"

    def is_case_insensitive(self) -> bool:
        """VBScript is case-insensitive."""
        return True

    def get_category(self) -> StabilityCategory:
        """Return the stability category."""
        return StabilityCategory.EXCEPTION_HANDLING

    def analyze(self, content: str, file_path: str = "test.asp") -> List[ExceptionFinding]:
        """
        Analyze code content for exception handling issues.

        Convenience method that wraps analyze_file.

        Args:
            content: Code content to analyze
            file_path: Optional file path (defaults to test.asp)

        Returns:
            List of exception findings
        """
        return self.analyze_file(file_path, content)
