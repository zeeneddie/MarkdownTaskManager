# Session Analyzer
# Detects session state issues in Classic ASP code
#
# Category 6: Session State Issues
# - Large objects in Session variables
# - Missing Session timeout configuration
# - Session reliance without timeout awareness
# - Global.asa Session_OnEnd issues
# - Session state in web farm scenarios
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


class SessionIssueType(Enum):
    """Types of session state issues."""
    LARGE_OBJECT = "large_object"
    COM_OBJECT_STORED = "com_object_stored"
    RECORDSET_STORED = "recordset_stored"
    NO_TIMEOUT_CHECK = "no_timeout_check"
    SENSITIVE_DATA = "sensitive_data"
    EXCESSIVE_SESSION_USE = "excessive_session_use"
    SESSION_IN_LOOP = "session_in_loop"
    NO_SESSION_ONEND_CLEANUP = "no_session_onend_cleanup"
    APPLICATION_AS_SESSION = "application_as_session"


@dataclass
class SessionOperation:
    """Represents a session operation."""
    line_number: int
    operation_type: str  # 'read', 'write', 'abandon'
    variable_name: str
    value_type: str = "unknown"  # 'object', 'primitive', 'array'
    code_snippet: str = ""


@dataclass
class SessionFinding:
    """A detected session issue."""
    file_path: str
    line_number: int
    issue_type: SessionIssueType
    variable_name: str
    severity: SeverityLevel
    description: str
    suggested_fix: str
    code_context: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_leak_finding(self) -> LeakFinding:
        """Convert to standard LeakFinding format."""
        return LeakFinding(
            file_path=self.file_path,
            line_number=self.line_number,
            resource_type=ResourceType.SESSION_OBJECT,
            variable_name=self.variable_name,
            leak_pattern=LeakPatternType.NEVER_CLOSED,
            severity=self.severity,
            category=StabilityCategory.SESSION_STATE,
            description=self.description,
            suggested_fix=self.suggested_fix,
            code_context=self.code_context,
            confidence=self.confidence,
        )


class SessionAnalyzer:
    """
    Analyzes code for session state issues that may cause stability problems.

    Detects:
    1. COM/ADO objects stored in Session (HIGH - can't serialize in web farm)
    2. Large objects stored in Session (HIGH)
    3. Recordsets stored in Session (HIGH)
    4. Sensitive data in Session without encryption (MEDIUM)
    5. Excessive Session variable usage (MEDIUM)
    6. Session access in loops (LOW)
    7. Application variables used as user state (MEDIUM)
    """

    # Session write patterns
    SESSION_WRITE_PATTERNS = [
        r'Session\s*\(\s*["\'](\w+)["\']\s*\)\s*=\s*(.+)',
        r'Session\.Contents\s*\(\s*["\'](\w+)["\']\s*\)\s*=\s*(.+)',
        r'Session\s*\(\s*["\'](\w+)["\']\s*\)\s*=',
    ]

    # Session read patterns
    SESSION_READ_PATTERNS = [
        r'=\s*Session\s*\(\s*["\'](\w+)["\']\s*\)',
        r'Session\s*\(\s*["\'](\w+)["\']\s*\)',
    ]

    # COM object indicators in value
    COM_OBJECT_INDICATORS = [
        r'=\s*Server\.CreateObject\s*\(',
        r'=\s*CreateObject\s*\(',
        r'=\s*(\w+)\.CreateObject\s*\(',
    ]

    # Recordset indicators
    RECORDSET_INDICATORS = [
        r'=\s*(\w+)\.Execute\s*\(',  # Connection.Execute returns recordset
        r'=\s*(\w+)\.Open\s*\(',
        r'ADODB\.Recordset',
    ]

    # Large object indicators
    LARGE_OBJECT_INDICATORS = [
        r'=\s*(\w+)\.GetRows\b',
        r'=\s*Response\.BinaryRead\b',
        r'=\s*(\w+)\.Read\s*\(',
        r'=\s*(\w+)\.GetString\b',
    ]

    # Sensitive data patterns (variable names)
    SENSITIVE_PATTERNS = [
        r'password',
        r'creditcard',
        r'ssn',
        r'socialsecurity',
        r'bsn',
        r'cardnumber',
        r'cvv',
        r'secret',
        r'apikey',
        r'token',
        r'pin',
    ]

    # Application variable patterns
    APPLICATION_PATTERNS = [
        r'Application\s*\(\s*["\'](\w+)["\']\s*\)\s*=',
        r'Application\.Contents\s*\(\s*["\'](\w+)["\']\s*\)\s*=',
    ]

    # User-specific indicators in Application variables
    USER_SPECIFIC_INDICATORS = [
        r'user',
        r'userid',
        r'user_id',
        r'username',
        r'profile',
        r'cart',
        r'basket',
        r'preference',
    ]

    # Loop patterns
    LOOP_PATTERNS = [
        r'\bDo\s+While\b',
        r'\bDo\s+Until\b',
        r'\bFor\s+Each\b',
        r'\bFor\s+\w+\s*=',
    ]

    LOOP_END_PATTERNS = [
        r'\bLoop\b',
        r'\bNext\b',
    ]

    # Maximum recommended Session variables per file
    MAX_SESSION_VARS_WARNING = 10
    MAX_SESSION_VARS_ERROR = 20

    def __init__(self):
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile all regex patterns."""
        flags = re.IGNORECASE

        self._compiled_patterns["session_write"] = [
            re.compile(p, flags) for p in self.SESSION_WRITE_PATTERNS
        ]
        self._compiled_patterns["session_read"] = [
            re.compile(p, flags) for p in self.SESSION_READ_PATTERNS
        ]
        self._compiled_patterns["com_object"] = [
            re.compile(p, flags) for p in self.COM_OBJECT_INDICATORS
        ]
        self._compiled_patterns["recordset"] = [
            re.compile(p, flags) for p in self.RECORDSET_INDICATORS
        ]
        self._compiled_patterns["large_object"] = [
            re.compile(p, flags) for p in self.LARGE_OBJECT_INDICATORS
        ]
        self._compiled_patterns["sensitive"] = [
            re.compile(p, flags) for p in self.SENSITIVE_PATTERNS
        ]
        self._compiled_patterns["application"] = [
            re.compile(p, flags) for p in self.APPLICATION_PATTERNS
        ]
        self._compiled_patterns["user_specific"] = [
            re.compile(p, flags) for p in self.USER_SPECIFIC_INDICATORS
        ]
        self._compiled_patterns["loop_start"] = [
            re.compile(p, flags) for p in self.LOOP_PATTERNS
        ]
        self._compiled_patterns["loop_end"] = [
            re.compile(p, flags) for p in self.LOOP_END_PATTERNS
        ]

    def analyze_file(self, file_path: str, content: str) -> List[SessionFinding]:
        """
        Analyze a file for session state issues.

        Args:
            file_path: Path to the file
            content: File content

        Returns:
            List of session findings
        """
        findings = []
        lines = content.split('\n')

        # Track session operations
        session_writes = self._find_session_writes(lines)
        session_reads = self._find_session_reads(lines)

        # Track loop regions
        loop_regions = self._find_loop_regions(lines)

        # Track unique session variables
        unique_vars: Set[str] = set()
        for op in session_writes + session_reads:
            unique_vars.add(op.variable_name.lower())

        # 1. Check for COM objects in Session
        findings.extend(self._check_com_objects(file_path, lines, session_writes))

        # 2. Check for Recordsets in Session
        findings.extend(self._check_recordsets(file_path, lines, session_writes))

        # 3. Check for large objects in Session
        findings.extend(self._check_large_objects(file_path, lines, session_writes))

        # 4. Check for sensitive data
        findings.extend(self._check_sensitive_data(file_path, session_writes, lines))

        # 5. Check for excessive Session usage
        findings.extend(self._check_excessive_usage(
            file_path, unique_vars, session_writes, lines
        ))

        # 6. Check for Session access in loops
        findings.extend(self._check_session_in_loops(
            file_path, lines, session_writes + session_reads, loop_regions
        ))

        # 7. Check for Application used as Session
        findings.extend(self._check_application_as_session(file_path, lines))

        return findings

    def _find_session_writes(self, lines: List[str]) -> List[SessionOperation]:
        """Find all Session write operations."""
        operations = []

        for line_num, line in enumerate(lines, 1):
            for pattern in self._compiled_patterns["session_write"]:
                match = pattern.search(line)
                if match:
                    var_name = match.group(1)
                    value = match.group(2) if len(match.groups()) > 1 else ""

                    # Determine value type
                    value_type = self._determine_value_type(value, line)

                    operations.append(SessionOperation(
                        line_number=line_num,
                        operation_type="write",
                        variable_name=var_name,
                        value_type=value_type,
                        code_snippet=line.strip(),
                    ))

        return operations

    def _find_session_reads(self, lines: List[str]) -> List[SessionOperation]:
        """Find all Session read operations."""
        operations = []

        for line_num, line in enumerate(lines, 1):
            for pattern in self._compiled_patterns["session_read"]:
                match = pattern.search(line)
                if match:
                    var_name = match.group(1)
                    operations.append(SessionOperation(
                        line_number=line_num,
                        operation_type="read",
                        variable_name=var_name,
                        code_snippet=line.strip(),
                    ))

        return operations

    def _determine_value_type(self, value: str, full_line: str) -> str:
        """Determine the type of value being stored."""
        # Check for COM object
        for pattern in self._compiled_patterns["com_object"]:
            if pattern.search(full_line):
                return "com_object"

        # Check for recordset
        for pattern in self._compiled_patterns["recordset"]:
            if pattern.search(full_line):
                return "recordset"

        # Check for large object
        for pattern in self._compiled_patterns["large_object"]:
            if pattern.search(full_line):
                return "large_object"

        # Default
        return "unknown"

    def _find_loop_regions(self, lines: List[str]) -> List[tuple]:
        """Find start and end lines of loops."""
        regions = []
        loop_starts = []

        for line_num, line in enumerate(lines, 1):
            for pattern in self._compiled_patterns["loop_start"]:
                if pattern.search(line):
                    loop_starts.append(line_num)
                    break

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

    def _check_com_objects(
        self,
        file_path: str,
        lines: List[str],
        session_writes: List[SessionOperation]
    ) -> List[SessionFinding]:
        """Check for COM objects stored in Session."""
        findings = []

        for op in session_writes:
            if op.value_type == "com_object":
                findings.append(SessionFinding(
                    file_path=file_path,
                    line_number=op.line_number,
                    issue_type=SessionIssueType.COM_OBJECT_STORED,
                    variable_name=op.variable_name,
                    severity=SeverityLevel.HIGH,
                    description=f"COM object stored in Session('{op.variable_name}') - can't serialize in web farm, causes memory issues",
                    suggested_fix="Store only primitive values or IDs in Session, recreate objects on each request",
                    code_context=self._get_context(lines, op.line_number),
                ))

        return findings

    def _check_recordsets(
        self,
        file_path: str,
        lines: List[str],
        session_writes: List[SessionOperation]
    ) -> List[SessionFinding]:
        """Check for Recordsets stored in Session."""
        findings = []

        for op in session_writes:
            if op.value_type == "recordset":
                findings.append(SessionFinding(
                    file_path=file_path,
                    line_number=op.line_number,
                    issue_type=SessionIssueType.RECORDSET_STORED,
                    variable_name=op.variable_name,
                    severity=SeverityLevel.HIGH,
                    description=f"Recordset stored in Session('{op.variable_name}') - holds database connection and memory",
                    suggested_fix="Use GetRows() to convert to array or GetString() for display data, store IDs only",
                    code_context=self._get_context(lines, op.line_number),
                ))

        return findings

    def _check_large_objects(
        self,
        file_path: str,
        lines: List[str],
        session_writes: List[SessionOperation]
    ) -> List[SessionFinding]:
        """Check for large objects stored in Session."""
        findings = []

        for op in session_writes:
            if op.value_type == "large_object":
                findings.append(SessionFinding(
                    file_path=file_path,
                    line_number=op.line_number,
                    issue_type=SessionIssueType.LARGE_OBJECT,
                    variable_name=op.variable_name,
                    severity=SeverityLevel.HIGH,
                    description=f"Large data object stored in Session('{op.variable_name}') - consumes memory per user",
                    suggested_fix="Store data in database or cache, keep only references in Session",
                    code_context=self._get_context(lines, op.line_number),
                ))

        return findings

    def _check_sensitive_data(
        self,
        file_path: str,
        session_writes: List[SessionOperation],
        lines: List[str]
    ) -> List[SessionFinding]:
        """Check for sensitive data stored in Session."""
        findings = []

        for op in session_writes:
            var_lower = op.variable_name.lower()
            for pattern in self._compiled_patterns["sensitive"]:
                if pattern.search(var_lower):
                    findings.append(SessionFinding(
                        file_path=file_path,
                        line_number=op.line_number,
                        issue_type=SessionIssueType.SENSITIVE_DATA,
                        variable_name=op.variable_name,
                        severity=SeverityLevel.MEDIUM,
                        description=f"Potentially sensitive data in Session('{op.variable_name}') - stored in server memory",
                        suggested_fix="Encrypt sensitive data before storing, or use secure token reference",
                        code_context=self._get_context(lines, op.line_number),
                        confidence=0.8,
                    ))
                    break

        return findings

    def _check_excessive_usage(
        self,
        file_path: str,
        unique_vars: Set[str],
        session_writes: List[SessionOperation],
        lines: List[str]
    ) -> List[SessionFinding]:
        """Check for excessive Session variable usage."""
        findings = []
        var_count = len(unique_vars)

        if var_count >= self.MAX_SESSION_VARS_ERROR:
            # Find first session operation for line number
            line_num = session_writes[0].line_number if session_writes else 1
            findings.append(SessionFinding(
                file_path=file_path,
                line_number=line_num,
                issue_type=SessionIssueType.EXCESSIVE_SESSION_USE,
                variable_name=f"{var_count} variables",
                severity=SeverityLevel.HIGH,
                description=f"Excessive Session usage: {var_count} unique variables in this file",
                suggested_fix="Consider grouping related values into objects, use database for large datasets",
                code_context=self._get_context(lines, line_num),
            ))
        elif var_count >= self.MAX_SESSION_VARS_WARNING:
            line_num = session_writes[0].line_number if session_writes else 1
            findings.append(SessionFinding(
                file_path=file_path,
                line_number=line_num,
                issue_type=SessionIssueType.EXCESSIVE_SESSION_USE,
                variable_name=f"{var_count} variables",
                severity=SeverityLevel.MEDIUM,
                description=f"High Session usage: {var_count} unique variables - consider consolidation",
                suggested_fix="Group related Session variables into a single object",
                code_context=self._get_context(lines, line_num),
                confidence=0.7,
            ))

        return findings

    def _check_session_in_loops(
        self,
        file_path: str,
        lines: List[str],
        session_ops: List[SessionOperation],
        loop_regions: List[tuple]
    ) -> List[SessionFinding]:
        """Check for Session access inside loops."""
        findings = []
        reported_vars: Set[str] = set()

        for op in session_ops:
            if not self._is_in_loop(op.line_number, loop_regions):
                continue

            if op.variable_name.lower() in reported_vars:
                continue
            reported_vars.add(op.variable_name.lower())

            findings.append(SessionFinding(
                file_path=file_path,
                line_number=op.line_number,
                issue_type=SessionIssueType.SESSION_IN_LOOP,
                variable_name=op.variable_name,
                severity=SeverityLevel.LOW,
                description=f"Session('{op.variable_name}') accessed inside loop - performance overhead",
                suggested_fix="Cache Session value in local variable before loop",
                code_context=self._get_context(lines, op.line_number),
                confidence=0.8,
            ))

        return findings

    def _check_application_as_session(
        self,
        file_path: str,
        lines: List[str]
    ) -> List[SessionFinding]:
        """Check for Application variables used to store user-specific data."""
        findings = []

        for line_num, line in enumerate(lines, 1):
            for pattern in self._compiled_patterns["application"]:
                match = pattern.search(line)
                if match:
                    var_name = match.group(1)
                    var_lower = var_name.lower()

                    # Check if variable name suggests user-specific data
                    for user_pattern in self._compiled_patterns["user_specific"]:
                        if user_pattern.search(var_lower):
                            findings.append(SessionFinding(
                                file_path=file_path,
                                line_number=line_num,
                                issue_type=SessionIssueType.APPLICATION_AS_SESSION,
                                variable_name=var_name,
                                severity=SeverityLevel.MEDIUM,
                                description=f"Application('{var_name}') appears to store user-specific data - shared across all users!",
                                suggested_fix="Use Session() for user-specific data, Application() is global",
                                code_context=self._get_context(lines, line_num),
                                confidence=0.7,
                            ))
                            break

        return findings

    def get_supported_extensions(self) -> List[str]:
        """Return supported file extensions."""
        return [".asp", ".inc", ".asa"]

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
        return StabilityCategory.SESSION_STATE

    def analyze(self, content: str, file_path: str = "test.asp") -> List[SessionFinding]:
        """
        Analyze code content for session issues.

        Convenience method that wraps analyze_file.

        Args:
            content: Code content to analyze
            file_path: Optional file path (defaults to test.asp)

        Returns:
            List of session findings
        """
        return self.analyze_file(file_path, content)
