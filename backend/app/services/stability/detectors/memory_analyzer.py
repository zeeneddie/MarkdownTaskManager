# Memory Analyzer
# Detects memory-intensive operations in Classic ASP code
#
# Category 4: Memory Intensive Operations
# - PDF generation without cleanup
# - Large array allocations
# - String concatenation in loops
# - Excessive Session/Application variable storage
# - Binary data handling
#
# Week 144 Implementation

from typing import List, Dict, Optional, Set
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


class MemoryIssueType(Enum):
    """Types of memory issues."""
    PDF_NO_CLEAR = "pdf_no_clear"
    LARGE_ARRAY = "large_array"
    STRING_CONCAT_LOOP = "string_concat_loop"
    BINARY_STREAM_LEAK = "binary_stream_leak"
    SESSION_LARGE_OBJECT = "session_large_object"
    APPLICATION_LARGE_OBJECT = "application_large_object"
    REDIM_IN_LOOP = "redim_in_loop"
    RECORDSET_GETROWS = "recordset_getrows"
    UNBOUNDED_COLLECTION = "unbounded_collection"


@dataclass
class MemoryOperation:
    """Represents a memory-intensive operation."""
    line_number: int
    operation_type: MemoryIssueType
    variable_name: str
    in_loop: bool = False
    estimated_impact: str = "unknown"  # low, medium, high
    code_snippet: str = ""


@dataclass
class MemoryFinding:
    """A detected memory issue."""
    file_path: str
    line_number: int
    issue_type: MemoryIssueType
    variable_name: str
    severity: SeverityLevel
    description: str
    suggested_fix: str
    code_context: List[str] = field(default_factory=list)
    confidence: float = 1.0
    estimated_memory_impact: str = "unknown"

    def to_leak_finding(self) -> LeakFinding:
        """Convert to standard LeakFinding format."""
        return LeakFinding(
            file_path=self.file_path,
            line_number=self.line_number,
            resource_type=ResourceType.STREAM,  # Use stream for memory issues
            variable_name=self.variable_name,
            leak_pattern=LeakPatternType.NEVER_CLOSED,
            severity=self.severity,
            category=StabilityCategory.MEMORY_INTENSIVE,
            description=self.description,
            suggested_fix=self.suggested_fix,
            code_context=self.code_context,
            confidence=self.confidence,
        )


class MemoryAnalyzer:
    """
    Analyzes code for memory-intensive operations that may cause stability issues.

    Detects:
    1. PDF generation without Clear/ClearData (HIGH)
    2. Large array allocations without cleanup (MEDIUM)
    3. String concatenation in loops (MEDIUM)
    4. Binary stream handling without close (HIGH)
    5. Large objects stored in Session/Application (HIGH)
    6. ReDim Preserve in loops (HIGH - causes memory fragmentation)
    7. GetRows on large recordsets (MEDIUM)
    8. Unbounded collection growth (MEDIUM)
    """

    # PDF patterns
    PDF_CREATE_PATTERNS = [
        r'Set\s+(\w+)\s*=\s*(?:Server\.)?CreateObject\s*\(\s*["\']ABCpdf\d*\.Doc["\']\s*\)',
        r'Set\s+(\w+)\s*=\s*(?:Server\.)?CreateObject\s*\(\s*["\']PDFCreator["\']\s*\)',
    ]

    PDF_CLEANUP_PATTERNS = [
        r'(\w+)\.Clear\b',
        r'(\w+)\.ClearData\b',
        r'Set\s+(\w+)\s*=\s*Nothing\b',
    ]

    # Array patterns
    LARGE_ARRAY_PATTERNS = [
        r'Dim\s+(\w+)\s*\(\s*(\d+)\s*\)',  # Dim arr(1000)
        r'ReDim\s+(\w+)\s*\(\s*(\d+)\s*\)',  # ReDim arr(1000)
    ]

    REDIM_PRESERVE_PATTERN = r'ReDim\s+Preserve\s+(\w+)\s*\('

    # String concatenation patterns
    STRING_CONCAT_PATTERNS = [
        r'(\w+)\s*=\s*\1\s*[&+]',  # str = str & "..."
        r'(\w+)\s*=\s*\1\s*&\s*["\']',
    ]

    # Loop patterns
    LOOP_PATTERNS = [
        r'\bDo\s+While\b',
        r'\bDo\s+Until\b',
        r'\bWhile\b',
        r'\bFor\s+Each\b',
        r'\bFor\s+\w+\s*=',
    ]

    LOOP_END_PATTERNS = [
        r'\bLoop\b',
        r'\bNext\b',
        r'\bWend\b',
    ]

    # Binary stream patterns
    BINARY_PATTERNS = [
        r'Set\s+(\w+)\s*=\s*(?:Server\.)?CreateObject\s*\(\s*["\']ADODB\.Stream["\']\s*\)',
        r'(\w+)\.Type\s*=\s*1',  # adTypeBinary = 1
        r'(\w+)\.LoadFromFile\b',
        r'(\w+)\.Read\s*\(',
    ]

    # Session/Application storage patterns
    SESSION_PATTERNS = [
        r'Session\s*\(\s*["\'](\w+)["\']\s*\)\s*=',
        r'Session\.Contents\s*\(\s*["\'](\w+)["\']\s*\)\s*=',
    ]

    APPLICATION_PATTERNS = [
        r'Application\s*\(\s*["\'](\w+)["\']\s*\)\s*=',
        r'Application\.Contents\s*\(\s*["\'](\w+)["\']\s*\)\s*=',
    ]

    # Large object indicators (assigned to Session/Application)
    LARGE_OBJECT_INDICATORS = [
        r'=\s*(\w+)\.GetRows\b',  # Full recordset as array
        r'=\s*Response\.BinaryRead\b',
        r'=\s*(\w+)\.Read\s*\(',  # Stream read
    ]

    # GetRows patterns
    GETROWS_PATTERN = r'(\w+)\s*=\s*(\w+)\.GetRows\b'

    # Dictionary/Collection growth
    COLLECTION_ADD_PATTERN = r'(\w+)\.Add\s*\('
    DICTIONARY_ADD_PATTERN = r'(\w+)\s*\(\s*["\'][^"\']+["\']\s*\)\s*='

    # Thresholds
    LARGE_ARRAY_THRESHOLD = 1000
    VERY_LARGE_ARRAY_THRESHOLD = 10000

    def __init__(self):
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile all regex patterns."""
        flags = re.IGNORECASE

        self._compiled_patterns["pdf_create"] = [
            re.compile(p, flags) for p in self.PDF_CREATE_PATTERNS
        ]
        self._compiled_patterns["pdf_cleanup"] = [
            re.compile(p, flags) for p in self.PDF_CLEANUP_PATTERNS
        ]
        self._compiled_patterns["large_array"] = [
            re.compile(p, flags) for p in self.LARGE_ARRAY_PATTERNS
        ]
        self._compiled_patterns["redim_preserve"] = [
            re.compile(self.REDIM_PRESERVE_PATTERN, flags)
        ]
        self._compiled_patterns["string_concat"] = [
            re.compile(p, flags) for p in self.STRING_CONCAT_PATTERNS
        ]
        self._compiled_patterns["loop_start"] = [
            re.compile(p, flags) for p in self.LOOP_PATTERNS
        ]
        self._compiled_patterns["loop_end"] = [
            re.compile(p, flags) for p in self.LOOP_END_PATTERNS
        ]
        self._compiled_patterns["binary"] = [
            re.compile(p, flags) for p in self.BINARY_PATTERNS
        ]
        self._compiled_patterns["session"] = [
            re.compile(p, flags) for p in self.SESSION_PATTERNS
        ]
        self._compiled_patterns["application"] = [
            re.compile(p, flags) for p in self.APPLICATION_PATTERNS
        ]
        self._compiled_patterns["getrows"] = [
            re.compile(self.GETROWS_PATTERN, flags)
        ]
        self._compiled_patterns["collection_add"] = [
            re.compile(self.COLLECTION_ADD_PATTERN, flags)
        ]

    def analyze_file(self, file_path: str, content: str) -> List[MemoryFinding]:
        """
        Analyze a file for memory-intensive operations.

        Args:
            file_path: Path to the file
            content: File content

        Returns:
            List of memory findings
        """
        findings = []
        lines = content.split('\n')

        # Track loop regions
        loop_regions = self._find_loop_regions(lines)

        # 1. Check PDF operations
        findings.extend(self._check_pdf_operations(file_path, lines, content))

        # 2. Check large array allocations
        findings.extend(self._check_large_arrays(file_path, lines))

        # 3. Check string concatenation in loops
        findings.extend(self._check_string_concat_in_loops(
            file_path, lines, loop_regions
        ))

        # 4. Check ReDim Preserve in loops
        findings.extend(self._check_redim_in_loops(
            file_path, lines, loop_regions
        ))

        # 5. Check binary stream handling
        findings.extend(self._check_binary_streams(file_path, lines, content))

        # 6. Check Session/Application large objects
        findings.extend(self._check_session_storage(file_path, lines, content))

        # 7. Check GetRows on potentially large recordsets
        findings.extend(self._check_getrows(file_path, lines, loop_regions))

        # 8. Check unbounded collection growth in loops
        findings.extend(self._check_collection_growth(
            file_path, lines, loop_regions
        ))

        return findings

    def _find_loop_regions(self, lines: List[str]) -> List[tuple]:
        """Find start and end lines of loops."""
        regions = []
        loop_starts = []

        for line_num, line in enumerate(lines, 1):
            # Check for loop start
            for pattern in self._compiled_patterns["loop_start"]:
                if pattern.search(line):
                    loop_starts.append(line_num)
                    break

            # Check for loop end
            for pattern in self._compiled_patterns["loop_end"]:
                if pattern.search(line) and loop_starts:
                    start = loop_starts.pop()
                    regions.append((start, line_num))
                    break

        return regions

    def _is_in_loop(self, line_num: int, loop_regions: List[tuple]) -> bool:
        """Check if a line is inside a loop."""
        for start, end in loop_regions:
            if start <= line_num <= end:
                return True
        return False

    def _get_context(self, lines: List[str], line_num: int) -> List[str]:
        """Get code context around a line."""
        start = max(0, line_num - 4)
        end = min(len(lines), line_num + 3)
        return lines[start:end]

    def _check_pdf_operations(
        self,
        file_path: str,
        lines: List[str],
        content: str
    ) -> List[MemoryFinding]:
        """Check for PDF operations without proper cleanup."""
        findings = []
        pdf_vars: Dict[str, int] = {}  # var_name -> creation line

        # Find PDF creations
        for line_num, line in enumerate(lines, 1):
            for pattern in self._compiled_patterns["pdf_create"]:
                match = pattern.search(line)
                if match:
                    var_name = match.group(1)
                    pdf_vars[var_name.lower()] = line_num

        # Check for cleanup
        cleaned_vars: Set[str] = set()
        for pattern in self._compiled_patterns["pdf_cleanup"]:
            for match in pattern.finditer(content):
                var_name = match.group(1)
                cleaned_vars.add(var_name.lower())

        # Report uncleaned PDFs
        for var_name, line_num in pdf_vars.items():
            if var_name not in cleaned_vars:
                findings.append(MemoryFinding(
                    file_path=file_path,
                    line_number=line_num,
                    issue_type=MemoryIssueType.PDF_NO_CLEAR,
                    variable_name=var_name,
                    severity=SeverityLevel.HIGH,
                    description=f"PDF object '{var_name}' created without Clear() - can cause memory buildup",
                    suggested_fix=f"Add {var_name}.Clear() after PDF operations complete",
                    code_context=self._get_context(lines, line_num),
                    estimated_memory_impact="high",
                ))

        return findings

    def _check_large_arrays(
        self,
        file_path: str,
        lines: List[str]
    ) -> List[MemoryFinding]:
        """Check for large array allocations."""
        findings = []

        for line_num, line in enumerate(lines, 1):
            for pattern in self._compiled_patterns["large_array"]:
                match = pattern.search(line)
                if match:
                    var_name = match.group(1)
                    try:
                        size = int(match.group(2))
                    except (ValueError, IndexError):
                        continue

                    if size >= self.VERY_LARGE_ARRAY_THRESHOLD:
                        findings.append(MemoryFinding(
                            file_path=file_path,
                            line_number=line_num,
                            issue_type=MemoryIssueType.LARGE_ARRAY,
                            variable_name=var_name,
                            severity=SeverityLevel.HIGH,
                            description=f"Very large array '{var_name}' with {size} elements - high memory usage",
                            suggested_fix="Consider processing data in batches or using database cursors",
                            code_context=self._get_context(lines, line_num),
                            estimated_memory_impact="high",
                        ))
                    elif size >= self.LARGE_ARRAY_THRESHOLD:
                        findings.append(MemoryFinding(
                            file_path=file_path,
                            line_number=line_num,
                            issue_type=MemoryIssueType.LARGE_ARRAY,
                            variable_name=var_name,
                            severity=SeverityLevel.MEDIUM,
                            description=f"Large array '{var_name}' with {size} elements",
                            suggested_fix="Monitor memory usage and consider cleanup after use",
                            code_context=self._get_context(lines, line_num),
                            confidence=0.8,
                            estimated_memory_impact="medium",
                        ))

        return findings

    def _check_string_concat_in_loops(
        self,
        file_path: str,
        lines: List[str],
        loop_regions: List[tuple]
    ) -> List[MemoryFinding]:
        """Check for string concatenation inside loops."""
        findings = []
        reported_vars: Set[str] = set()

        for line_num, line in enumerate(lines, 1):
            if not self._is_in_loop(line_num, loop_regions):
                continue

            for pattern in self._compiled_patterns["string_concat"]:
                match = pattern.search(line)
                if match:
                    var_name = match.group(1)
                    if var_name.lower() in reported_vars:
                        continue
                    reported_vars.add(var_name.lower())

                    findings.append(MemoryFinding(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type=MemoryIssueType.STRING_CONCAT_LOOP,
                        variable_name=var_name,
                        severity=SeverityLevel.MEDIUM,
                        description=f"String concatenation of '{var_name}' inside loop - creates many temporary strings",
                        suggested_fix="Use StringBuilder pattern or array Join() for better performance",
                        code_context=self._get_context(lines, line_num),
                        estimated_memory_impact="medium",
                    ))

        return findings

    def _check_redim_in_loops(
        self,
        file_path: str,
        lines: List[str],
        loop_regions: List[tuple]
    ) -> List[MemoryFinding]:
        """Check for ReDim Preserve inside loops."""
        findings = []

        for line_num, line in enumerate(lines, 1):
            if not self._is_in_loop(line_num, loop_regions):
                continue

            for pattern in self._compiled_patterns["redim_preserve"]:
                match = pattern.search(line)
                if match:
                    var_name = match.group(1)
                    findings.append(MemoryFinding(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type=MemoryIssueType.REDIM_IN_LOOP,
                        variable_name=var_name,
                        severity=SeverityLevel.HIGH,
                        description=f"ReDim Preserve '{var_name}' inside loop - causes memory fragmentation and slow performance",
                        suggested_fix="Pre-allocate array size or use Dictionary/Collection instead",
                        code_context=self._get_context(lines, line_num),
                        estimated_memory_impact="high",
                    ))

        return findings

    def _check_binary_streams(
        self,
        file_path: str,
        lines: List[str],
        content: str
    ) -> List[MemoryFinding]:
        """Check for binary stream handling without proper cleanup."""
        findings = []
        stream_vars: Dict[str, int] = {}

        # Find binary stream creations
        for line_num, line in enumerate(lines, 1):
            for pattern in self._compiled_patterns["binary"]:
                match = pattern.search(line)
                if match and "CreateObject" in line:
                    var_name = match.group(1)
                    stream_vars[var_name.lower()] = line_num

        # Check for Close()
        close_pattern = re.compile(r'(\w+)\.Close\b', re.IGNORECASE)
        closed_vars: Set[str] = set()
        for match in close_pattern.finditer(content):
            closed_vars.add(match.group(1).lower())

        # Report unclosed streams
        for var_name, line_num in stream_vars.items():
            if var_name not in closed_vars:
                findings.append(MemoryFinding(
                    file_path=file_path,
                    line_number=line_num,
                    issue_type=MemoryIssueType.BINARY_STREAM_LEAK,
                    variable_name=var_name,
                    severity=SeverityLevel.HIGH,
                    description=f"Binary stream '{var_name}' not closed - can hold large amounts of memory",
                    suggested_fix=f"Add {var_name}.Close() after binary operations complete",
                    code_context=self._get_context(lines, line_num),
                    estimated_memory_impact="high",
                ))

        return findings

    def _check_session_storage(
        self,
        file_path: str,
        lines: List[str],
        content: str
    ) -> List[MemoryFinding]:
        """Check for large objects stored in Session/Application."""
        findings = []

        # Check Session storage
        for line_num, line in enumerate(lines, 1):
            for pattern in self._compiled_patterns["session"]:
                match = pattern.search(line)
                if match:
                    var_name = match.group(1)
                    # Check if storing large object
                    for indicator in self.LARGE_OBJECT_INDICATORS:
                        if re.search(indicator, line, re.IGNORECASE):
                            findings.append(MemoryFinding(
                                file_path=file_path,
                                line_number=line_num,
                                issue_type=MemoryIssueType.SESSION_LARGE_OBJECT,
                                variable_name=var_name,
                                severity=SeverityLevel.HIGH,
                                description=f"Large object stored in Session('{var_name}') - consumes memory per user session",
                                suggested_fix="Store only IDs/keys in Session, retrieve data on demand",
                                code_context=self._get_context(lines, line_num),
                                estimated_memory_impact="high",
                            ))
                            break

        # Check Application storage
        for line_num, line in enumerate(lines, 1):
            for pattern in self._compiled_patterns["application"]:
                match = pattern.search(line)
                if match:
                    var_name = match.group(1)
                    for indicator in self.LARGE_OBJECT_INDICATORS:
                        if re.search(indicator, line, re.IGNORECASE):
                            findings.append(MemoryFinding(
                                file_path=file_path,
                                line_number=line_num,
                                issue_type=MemoryIssueType.APPLICATION_LARGE_OBJECT,
                                variable_name=var_name,
                                severity=SeverityLevel.HIGH,
                                description=f"Large object stored in Application('{var_name}') - shared across all users",
                                suggested_fix="Use database or cache with proper expiration instead",
                                code_context=self._get_context(lines, line_num),
                                estimated_memory_impact="high",
                            ))
                            break

        return findings

    def _check_getrows(
        self,
        file_path: str,
        lines: List[str],
        loop_regions: List[tuple]
    ) -> List[MemoryFinding]:
        """Check for GetRows on potentially large recordsets."""
        findings = []

        for line_num, line in enumerate(lines, 1):
            for pattern in self._compiled_patterns["getrows"]:
                match = pattern.search(line)
                if match:
                    array_var = match.group(1)
                    rs_var = match.group(2)

                    # Higher severity if inside a loop
                    in_loop = self._is_in_loop(line_num, loop_regions)
                    severity = SeverityLevel.HIGH if in_loop else SeverityLevel.MEDIUM

                    findings.append(MemoryFinding(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type=MemoryIssueType.RECORDSET_GETROWS,
                        variable_name=array_var,
                        severity=severity,
                        description=f"GetRows() on '{rs_var}' loads entire result set into memory{' (inside loop!)' if in_loop else ''}",
                        suggested_fix="Use pagination or process records one at a time for large datasets",
                        code_context=self._get_context(lines, line_num),
                        confidence=0.7 if not in_loop else 0.9,
                        estimated_memory_impact="high" if in_loop else "medium",
                    ))

        return findings

    def _check_collection_growth(
        self,
        file_path: str,
        lines: List[str],
        loop_regions: List[tuple]
    ) -> List[MemoryFinding]:
        """Check for unbounded collection growth inside loops."""
        findings = []
        reported_vars: Set[str] = set()

        for line_num, line in enumerate(lines, 1):
            if not self._is_in_loop(line_num, loop_regions):
                continue

            for pattern in self._compiled_patterns["collection_add"]:
                match = pattern.search(line)
                if match:
                    var_name = match.group(1)
                    if var_name.lower() in reported_vars:
                        continue
                    reported_vars.add(var_name.lower())

                    findings.append(MemoryFinding(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type=MemoryIssueType.UNBOUNDED_COLLECTION,
                        variable_name=var_name,
                        severity=SeverityLevel.MEDIUM,
                        description=f"Collection '{var_name}' growing inside loop - may consume excessive memory",
                        suggested_fix="Ensure collection size is bounded or implement cleanup strategy",
                        code_context=self._get_context(lines, line_num),
                        confidence=0.7,
                        estimated_memory_impact="medium",
                    ))

        return findings

    def get_supported_extensions(self) -> List[str]:
        """Return supported file extensions."""
        return [".asp", ".inc"]

    def supports_file(self, file_path: str) -> bool:
        """Check if this analyzer supports the given file."""
        return any(file_path.lower().endswith(ext) for ext in self.get_supported_extensions())

    def get_language(self) -> str:
        """Return the language name."""
        return "Classic ASP (VBScript)"

    def is_case_insensitive(self) -> bool:
        """VBScript is case-insensitive."""
        return True

    def get_category(self) -> StabilityCategory:
        """Return the stability category."""
        return StabilityCategory.MEMORY_INTENSIVE

    def analyze(self, content: str, file_path: str = "test.asp") -> List[MemoryFinding]:
        """
        Analyze code content for memory issues.

        Convenience method that wraps analyze_file.

        Args:
            content: Code content to analyze
            file_path: Optional file path (defaults to test.asp)

        Returns:
            List of memory findings
        """
        return self.analyze_file(file_path, content)
