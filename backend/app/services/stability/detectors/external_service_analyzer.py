# External Service Analyzer
# Detects external service risks in Classic ASP code
#
# Category 3: External Service Risks
# - Missing timeout configuration
# - No retry logic for transient failures
# - Synchronous blocking calls
# - Missing error handling for external calls
# - Certificate validation disabled
#
# Week 144 Implementation

from typing import List, Dict, Optional
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


class ExternalServiceIssueType(Enum):
    """Types of external service issues."""
    NO_TIMEOUT = "no_timeout"
    SHORT_TIMEOUT = "short_timeout"
    NO_RETRY = "no_retry"
    SYNC_BLOCKING = "sync_blocking"
    NO_ERROR_HANDLING = "no_error_handling"
    SSL_DISABLED = "ssl_disabled"
    HARDCODED_CREDENTIALS = "hardcoded_credentials"
    NO_CONNECTION_REUSE = "no_connection_reuse"


@dataclass
class ExternalServiceCall:
    """Represents an external service call."""
    line_number: int
    service_type: str  # XMLHTTP, WinHttp, WebService, etc.
    variable_name: str
    has_timeout: bool = False
    timeout_value: Optional[int] = None
    has_error_handling: bool = False
    is_async: bool = False
    has_retry: bool = False
    url_pattern: str = ""
    code_snippet: str = ""


@dataclass
class ExternalServiceFinding:
    """A detected external service issue."""
    file_path: str
    line_number: int
    issue_type: ExternalServiceIssueType
    service_type: str
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
            resource_type=ResourceType.HTTP_CONNECTION,
            variable_name=self.variable_name,
            leak_pattern=LeakPatternType.NEVER_CLOSED,  # Reuse pattern for external service issues
            severity=self.severity,
            category=StabilityCategory.EXTERNAL_SERVICES,
            description=self.description,
            suggested_fix=self.suggested_fix,
            code_context=self.code_context,
            confidence=self.confidence,
        )


class ExternalServiceAnalyzer:
    """
    Analyzes external service calls for stability risks.

    Detects:
    1. Missing timeout configuration (HIGH)
    2. Short timeouts that may cause failures (MEDIUM)
    3. No retry logic for transient failures (MEDIUM)
    4. Synchronous blocking calls (MEDIUM)
    5. Missing error handling (HIGH)
    6. SSL/certificate validation disabled (HIGH)
    7. Hardcoded credentials (CRITICAL)
    """

    # Patterns for external service creation
    XMLHTTP_PATTERNS = [
        r'Set\s+(\w+)\s*=\s*(?:Server\.)?CreateObject\s*\(\s*["\']MSXML2\.ServerXMLHTTP["\']',
        r'Set\s+(\w+)\s*=\s*(?:Server\.)?CreateObject\s*\(\s*["\']Microsoft\.XMLHTTP["\']',
        r'Set\s+(\w+)\s*=\s*(?:Server\.)?CreateObject\s*\(\s*["\']MSXML2\.XMLHTTP["\']',
        r'Set\s+(\w+)\s*=\s*(?:Server\.)?CreateObject\s*\(\s*["\']WinHttp\.WinHttpRequest["\']',
    ]

    # Patterns for timeout configuration
    TIMEOUT_PATTERNS = [
        r'(\w+)\.setTimeouts\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)',
        r'(\w+)\.setTimeout\s*\(\s*(\d+)\s*\)',
        r'(\w+)\s*\.\s*(?:resolve|connect|send|receive)Timeout\s*=\s*(\d+)',
    ]

    # Patterns for error handling
    ERROR_HANDLING_PATTERNS = [
        r'On\s+Error\s+Resume\s+Next',
        r'On\s+Error\s+GoTo\s+\w+',
        r'If\s+Err\.Number\s*[<>=!]+',
        r'If\s+Err\s*[<>=!]+',
    ]

    # Patterns for retry logic
    RETRY_PATTERNS = [
        r'retry',
        r'attempt',
        r'maxRetries',
        r'retryCount',
        r'For\s+\w+\s*=.*retry',
    ]

    # Patterns for async calls
    ASYNC_PATTERNS = [
        r'\.Open\s*\(\s*["\'](?:GET|POST|PUT|DELETE)["\']\s*,\s*[^,]+,\s*True\s*\)',
        r'async\s*=\s*True',
    ]

    # Patterns for SSL disabled
    SSL_DISABLED_PATTERNS = [
        r'\.setOption\s*\(\s*2\s*,\s*\d+\s*\)',  # SXH_SERVER_CERT_IGNORE
        r'ServerCertificateFlags\s*=',
        r'CERT_IGNORE',
    ]

    # Patterns for hardcoded credentials
    CREDENTIAL_PATTERNS = [
        r'\.Open\s*\([^)]+,\s*["\'][^"\']+["\']\s*,\s*["\'][^"\']+["\']\s*\)',  # username, password in Open
        r'password\s*=\s*["\'][^"\']+["\']',
        r'apikey\s*=\s*["\'][^"\']+["\']',
        r'Authorization.*Basic\s+[A-Za-z0-9+/=]+',
    ]

    # Recommended timeout values (in ms)
    MIN_RECOMMENDED_TIMEOUT = 5000  # 5 seconds
    MAX_RECOMMENDED_TIMEOUT = 60000  # 60 seconds

    def __init__(self):
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile all regex patterns with case-insensitive flag."""
        flags = re.IGNORECASE

        self._compiled_patterns["xmlhttp"] = [
            re.compile(p, flags) for p in self.XMLHTTP_PATTERNS
        ]
        self._compiled_patterns["timeout"] = [
            re.compile(p, flags) for p in self.TIMEOUT_PATTERNS
        ]
        self._compiled_patterns["error_handling"] = [
            re.compile(p, flags) for p in self.ERROR_HANDLING_PATTERNS
        ]
        self._compiled_patterns["retry"] = [
            re.compile(p, flags) for p in self.RETRY_PATTERNS
        ]
        self._compiled_patterns["async"] = [
            re.compile(p, flags) for p in self.ASYNC_PATTERNS
        ]
        self._compiled_patterns["ssl_disabled"] = [
            re.compile(p, flags) for p in self.SSL_DISABLED_PATTERNS
        ]
        self._compiled_patterns["credentials"] = [
            re.compile(p, flags) for p in self.CREDENTIAL_PATTERNS
        ]

    def analyze_file(self, file_path: str, content: str) -> List[ExternalServiceFinding]:
        """
        Analyze a file for external service risks.

        Args:
            file_path: Path to the file
            content: File content

        Returns:
            List of external service findings
        """
        findings = []
        lines = content.split('\n')

        # Find all external service calls
        service_calls = self._find_service_calls(lines)

        if not service_calls:
            return findings

        # Check for timeouts
        timeouts = self._find_timeouts(lines)

        # Check for error handling
        has_error_handling = self._has_error_handling(content)

        # Check for retry logic
        has_retry = self._has_retry_logic(content)

        # Check for SSL disabled
        ssl_issues = self._find_ssl_issues(lines)

        # Check for hardcoded credentials
        credential_issues = self._find_credential_issues(lines)

        # Analyze each service call
        for call in service_calls:
            # Check timeout
            call_timeout = self._get_timeout_for_call(call.variable_name, timeouts)
            if call_timeout is None:
                findings.append(self._create_no_timeout_finding(file_path, call, lines))
            elif call_timeout < self.MIN_RECOMMENDED_TIMEOUT:
                findings.append(self._create_short_timeout_finding(
                    file_path, call, call_timeout, lines
                ))

            # Check error handling
            if not has_error_handling:
                findings.append(self._create_no_error_handling_finding(
                    file_path, call, lines
                ))

            # Check retry logic
            if not has_retry:
                findings.append(self._create_no_retry_finding(file_path, call, lines))

            # Check async
            if not self._is_async_call(call.variable_name, content):
                findings.append(self._create_sync_blocking_finding(
                    file_path, call, lines
                ))

        # Add SSL issues
        for line_num, snippet in ssl_issues:
            findings.append(ExternalServiceFinding(
                file_path=file_path,
                line_number=line_num,
                issue_type=ExternalServiceIssueType.SSL_DISABLED,
                service_type="XMLHTTP",
                variable_name="",
                severity=SeverityLevel.HIGH,
                description="SSL certificate validation is disabled - vulnerable to MITM attacks",
                suggested_fix="Enable SSL certificate validation or use proper certificate handling",
                code_context=self._get_context(lines, line_num),
            ))

        # Add credential issues
        for line_num, snippet in credential_issues:
            findings.append(ExternalServiceFinding(
                file_path=file_path,
                line_number=line_num,
                issue_type=ExternalServiceIssueType.HARDCODED_CREDENTIALS,
                service_type="XMLHTTP",
                variable_name="",
                severity=SeverityLevel.CRITICAL,
                description="Hardcoded credentials detected - security vulnerability",
                suggested_fix="Use environment variables or secure configuration for credentials",
                code_context=self._get_context(lines, line_num),
            ))

        return findings

    def _find_service_calls(self, lines: List[str]) -> List[ExternalServiceCall]:
        """Find all external service creation calls."""
        calls = []

        for line_num, line in enumerate(lines, 1):
            for pattern in self._compiled_patterns["xmlhttp"]:
                match = pattern.search(line)
                if match:
                    var_name = match.group(1) if match.groups() else "unknown"
                    service_type = "XMLHTTP"
                    if "WinHttp" in line:
                        service_type = "WinHttp"
                    elif "ServerXMLHTTP" in line:
                        service_type = "ServerXMLHTTP"

                    calls.append(ExternalServiceCall(
                        line_number=line_num,
                        service_type=service_type,
                        variable_name=var_name,
                        code_snippet=line.strip(),
                    ))

        return calls

    def _find_timeouts(self, lines: List[str]) -> Dict[str, int]:
        """Find timeout configurations and return variable -> timeout mapping."""
        timeouts = {}

        for line_num, line in enumerate(lines, 1):
            for pattern in self._compiled_patterns["timeout"]:
                match = pattern.search(line)
                if match:
                    var_name = match.group(1)
                    # Get the timeout value (usually the last numeric group)
                    groups = match.groups()
                    if len(groups) >= 2:
                        try:
                            # For setTimeouts, use the send timeout (4th param)
                            # or the first numeric value found
                            timeout_val = int(groups[-1]) if groups[-1].isdigit() else int(groups[1])
                            timeouts[var_name.lower()] = timeout_val
                        except (ValueError, IndexError):
                            pass

        return timeouts

    def _get_timeout_for_call(
        self,
        var_name: str,
        timeouts: Dict[str, int]
    ) -> Optional[int]:
        """Get the timeout configured for a specific variable."""
        return timeouts.get(var_name.lower())

    def _has_error_handling(self, content: str) -> bool:
        """Check if the file has error handling around external calls."""
        for pattern in self._compiled_patterns["error_handling"]:
            if pattern.search(content):
                return True
        return False

    def _has_retry_logic(self, content: str) -> bool:
        """Check if the file has retry logic."""
        for pattern in self._compiled_patterns["retry"]:
            if pattern.search(content):
                return True
        return False

    def _is_async_call(self, var_name: str, content: str) -> bool:
        """Check if the call is asynchronous."""
        # Look for async = True in Open call
        async_pattern = re.compile(
            rf'{var_name}\.Open\s*\([^)]*,\s*True\s*\)',
            re.IGNORECASE
        )
        return bool(async_pattern.search(content))

    def _find_ssl_issues(self, lines: List[str]) -> List[tuple]:
        """Find lines where SSL validation is disabled."""
        issues = []
        for line_num, line in enumerate(lines, 1):
            for pattern in self._compiled_patterns["ssl_disabled"]:
                if pattern.search(line):
                    issues.append((line_num, line.strip()))
        return issues

    def _find_credential_issues(self, lines: List[str]) -> List[tuple]:
        """Find lines with hardcoded credentials."""
        issues = []
        for line_num, line in enumerate(lines, 1):
            for pattern in self._compiled_patterns["credentials"]:
                if pattern.search(line):
                    issues.append((line_num, line.strip()))
        return issues

    def _get_context(self, lines: List[str], line_num: int) -> List[str]:
        """Get code context around a line."""
        start = max(0, line_num - 4)
        end = min(len(lines), line_num + 3)
        return lines[start:end]

    def _create_no_timeout_finding(
        self,
        file_path: str,
        call: ExternalServiceCall,
        lines: List[str]
    ) -> ExternalServiceFinding:
        return ExternalServiceFinding(
            file_path=file_path,
            line_number=call.line_number,
            issue_type=ExternalServiceIssueType.NO_TIMEOUT,
            service_type=call.service_type,
            variable_name=call.variable_name,
            severity=SeverityLevel.HIGH,
            description=f"{call.variable_name} ({call.service_type}) has no timeout configured - can block indefinitely",
            suggested_fix=f"Add timeout: {call.variable_name}.setTimeouts 5000, 5000, 30000, 30000",
            code_context=self._get_context(lines, call.line_number),
        )

    def _create_short_timeout_finding(
        self,
        file_path: str,
        call: ExternalServiceCall,
        timeout_ms: int,
        lines: List[str]
    ) -> ExternalServiceFinding:
        return ExternalServiceFinding(
            file_path=file_path,
            line_number=call.line_number,
            issue_type=ExternalServiceIssueType.SHORT_TIMEOUT,
            service_type=call.service_type,
            variable_name=call.variable_name,
            severity=SeverityLevel.MEDIUM,
            description=f"{call.variable_name} timeout of {timeout_ms}ms may be too short for reliable operation",
            suggested_fix=f"Consider increasing timeout to at least {self.MIN_RECOMMENDED_TIMEOUT}ms",
            code_context=self._get_context(lines, call.line_number),
            confidence=0.8,
        )

    def _create_no_error_handling_finding(
        self,
        file_path: str,
        call: ExternalServiceCall,
        lines: List[str]
    ) -> ExternalServiceFinding:
        return ExternalServiceFinding(
            file_path=file_path,
            line_number=call.line_number,
            issue_type=ExternalServiceIssueType.NO_ERROR_HANDLING,
            service_type=call.service_type,
            variable_name=call.variable_name,
            severity=SeverityLevel.HIGH,
            description=f"No error handling for external call {call.variable_name} - failures will crash the page",
            suggested_fix="Add On Error Resume Next before call and check Err.Number after",
            code_context=self._get_context(lines, call.line_number),
        )

    def _create_no_retry_finding(
        self,
        file_path: str,
        call: ExternalServiceCall,
        lines: List[str]
    ) -> ExternalServiceFinding:
        return ExternalServiceFinding(
            file_path=file_path,
            line_number=call.line_number,
            issue_type=ExternalServiceIssueType.NO_RETRY,
            service_type=call.service_type,
            variable_name=call.variable_name,
            severity=SeverityLevel.MEDIUM,
            description=f"No retry logic for {call.variable_name} - transient failures will cause errors",
            suggested_fix="Implement retry with exponential backoff (3 attempts, 1s/2s/4s delays)",
            code_context=self._get_context(lines, call.line_number),
            confidence=0.7,
        )

    def _create_sync_blocking_finding(
        self,
        file_path: str,
        call: ExternalServiceCall,
        lines: List[str]
    ) -> ExternalServiceFinding:
        return ExternalServiceFinding(
            file_path=file_path,
            line_number=call.line_number,
            issue_type=ExternalServiceIssueType.SYNC_BLOCKING,
            service_type=call.service_type,
            variable_name=call.variable_name,
            severity=SeverityLevel.MEDIUM,
            description=f"{call.variable_name} uses synchronous call - blocks thread until response",
            suggested_fix="Consider async call if ASP allows, or ensure adequate timeout",
            code_context=self._get_context(lines, call.line_number),
            confidence=0.6,
        )

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
        return StabilityCategory.EXTERNAL_SERVICES

    def analyze(self, content: str, file_path: str = "test.asp") -> List[ExternalServiceFinding]:
        """
        Analyze code content for external service issues.

        Convenience method that wraps analyze_file.

        Args:
            content: Code content to analyze
            file_path: Optional file path (defaults to test.asp)

        Returns:
            List of external service findings
        """
        return self.analyze_file(file_path, content)
