# Base Resource Leak Detector
# Abstract base class for language-specific leak detectors
#
# Implements:
# - Case-insensitive pattern matching (configurable)
# - State machine tracking for resource lifecycle
# - Wrapper function analysis
# - Include file resolution (for ASP)
# - Reopen pattern detection (from FysioOne audit)

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
import re
import logging
import time

from .types import (
    ResourceType,
    ResourceState,
    LeakPatternType,
    StabilityCategory,
    SeverityLevel,
    ResourceOperation,
    LeakFinding,
    LeakReport,
)

logger = logging.getLogger(__name__)


@dataclass
class ResourceTracker:
    """
    Tracks the state of a single resource through its lifecycle.

    State machine:
    CREATED → OPENED → CLOSED → REOPENED → CLOSED
                ↓          ↓
            RELEASED   RELEASED

    Leak detection:
    - End at CREATED/OPENED → NEVER_CLOSED
    - End at REOPENED → REOPEN_LEAK
    - RELEASED without CLOSED → SET_WITHOUT_CLOSE
    """
    variable_name: str
    resource_type: ResourceType
    state: ResourceState = ResourceState.CREATED
    created_line: int = 0
    opened_line: int = 0
    closed_line: int = 0
    released_line: int = 0
    in_loop: bool = False
    in_function: str = ""
    via_wrapper: bool = False
    reopen_count: int = 0

    def open(self, line: int) -> None:
        """Transition to OPENED or REOPENED state."""
        if self.state == ResourceState.CLOSED:
            self.state = ResourceState.REOPENED
            self.reopen_count += 1
        else:
            self.state = ResourceState.OPENED
        self.opened_line = line

    def close(self, line: int) -> None:
        """Transition to CLOSED state."""
        self.state = ResourceState.CLOSED
        self.closed_line = line

    def release(self, line: int) -> None:
        """Transition to RELEASED state (Set = Nothing)."""
        self.released_line = line
        self.state = ResourceState.RELEASED

    @property
    def is_leaking(self) -> bool:
        """Check if resource is in a leaking state."""
        return self.state in [
            ResourceState.CREATED,
            ResourceState.OPENED,
            ResourceState.REOPENED,
        ]

    @property
    def is_set_without_close(self) -> bool:
        """Check if released without being closed."""
        return (
            self.state == ResourceState.RELEASED and
            self.closed_line == 0
        )

    def get_leak_pattern(self) -> Optional[LeakPatternType]:
        """Determine the leak pattern type."""
        if self.state == ResourceState.REOPENED:
            return LeakPatternType.REOPEN_LEAK
        if self.is_set_without_close:
            return LeakPatternType.SET_WITHOUT_CLOSE
        if self.in_loop and self.is_leaking:
            return LeakPatternType.LOOP_LEAK
        if self.in_function and self.is_leaking:
            return LeakPatternType.FUNCTION_LEAK
        if self.is_leaking:
            return LeakPatternType.NEVER_CLOSED
        return None


class BaseResourceLeakDetector(ABC):
    """
    Abstract base class for language-specific leak detectors.

    Subclasses must implement:
    - get_supported_extensions() → List[str]
    - get_language() → str
    - get_open_patterns() → Dict[ResourceType, List[str]]
    - get_close_patterns() → Dict[ResourceType, List[str]]

    Optional overrides:
    - is_case_insensitive() → bool (default: False)
    - get_release_patterns() → Dict[ResourceType, List[str]]
    - get_wrapper_functions() → Dict[str, str] (wrapper → wrapped_call)
    - get_loop_patterns() → List[str]
    - get_function_patterns() → List[str]
    - get_early_exit_patterns() → List[str]
    """

    def __init__(self):
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        self._resource_trackers: Dict[str, ResourceTracker] = {}
        self._wrapper_map: Dict[str, str] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile all regex patterns with appropriate flags."""
        flags = re.IGNORECASE if self.is_case_insensitive() else 0

        # Compile open patterns
        for resource_type, patterns in self.get_open_patterns().items():
            key = f"open_{resource_type.value}"
            self._compiled_patterns[key] = [
                re.compile(p, flags) for p in patterns
            ]

        # Compile close patterns
        for resource_type, patterns in self.get_close_patterns().items():
            key = f"close_{resource_type.value}"
            self._compiled_patterns[key] = [
                re.compile(p, flags) for p in patterns
            ]

        # Compile release patterns (Set = Nothing)
        for resource_type, patterns in self.get_release_patterns().items():
            key = f"release_{resource_type.value}"
            self._compiled_patterns[key] = [
                re.compile(p, flags) for p in patterns
            ]

        # Compile structural patterns
        self._compiled_patterns["loop"] = [
            re.compile(p, flags) for p in self.get_loop_patterns()
        ]
        self._compiled_patterns["function"] = [
            re.compile(p, flags) for p in self.get_function_patterns()
        ]
        self._compiled_patterns["early_exit"] = [
            re.compile(p, flags) for p in self.get_early_exit_patterns()
        ]

        # Store wrapper function mappings
        self._wrapper_map = self.get_wrapper_functions()

    # === Abstract Methods (MUST implement) ===

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions (e.g., ['.asp', '.inc'])."""
        pass

    @abstractmethod
    def get_language(self) -> str:
        """Return language name (e.g., 'Classic ASP')."""
        pass

    @abstractmethod
    def get_open_patterns(self) -> Dict[ResourceType, List[str]]:
        """
        Return regex patterns for resource opening.

        Pattern must capture variable name in group 1.

        Example:
            {
                ResourceType.DATABASE_CONNECTION: [
                    r'Set\s+(\w+)\s*=\s*CreateCusCon\(',
                    r'Set\s+(\w+)\s*=\s*Server\.CreateObject\("ADODB\.Connection"\)',
                ],
                ResourceType.RECORDSET: [
                    r'Set\s+(\w+)\s*=\s*CreateRecordset\(',
                ],
            }
        """
        pass

    @abstractmethod
    def get_close_patterns(self) -> Dict[ResourceType, List[str]]:
        """
        Return regex patterns for resource closing.

        Pattern must capture variable name in group 1.

        Example:
            {
                ResourceType.DATABASE_CONNECTION: [
                    r'(\w+)\.Close\b',
                    r'Call\s+TryCloseConnection\((\w+)\)',
                ],
            }
        """
        pass

    # === Optional Methods (CAN override) ===

    def is_case_insensitive(self) -> bool:
        """Override to True for case-insensitive languages (VBScript, SQL)."""
        return False

    def get_release_patterns(self) -> Dict[ResourceType, List[str]]:
        """
        Return patterns for releasing resources (e.g., Set = Nothing).

        Override for languages with explicit release patterns.
        """
        return {}

    def get_wrapper_functions(self) -> Dict[str, str]:
        """
        Return mapping of wrapper functions to their wrapped operations.

        Example:
            {
                "CreateCusCon": "ADODB.Connection",
                "CreateRecordset": "ADODB.Recordset",
            }
        """
        return {}

    def get_loop_patterns(self) -> List[str]:
        """Return patterns that indicate loop structures."""
        return []

    def get_function_patterns(self) -> List[str]:
        """Return patterns that indicate function/method definitions."""
        return []

    def get_early_exit_patterns(self) -> List[str]:
        """Return patterns that indicate early exit (Response.End, return, etc.)."""
        return []

    def get_category(self) -> StabilityCategory:
        """Return the stability category this detector belongs to."""
        return StabilityCategory.ADO_LEAKS

    # === Main Analysis Method ===

    def analyze_file(self, file_path: str, content: str) -> LeakReport:
        """
        Analyze a file for resource leaks.

        Steps:
        1. Find all open operations
        2. Find all close operations
        3. Find all release operations
        4. Track resource state through file
        5. Detect leaks based on final states
        6. Apply severity prioritization
        """
        start_time = time.time()

        # Reset trackers
        self._resource_trackers.clear()

        # Parse file
        lines = content.split('\n')
        opens = self._find_opens(lines)
        closes = self._find_closes(lines)
        releases = self._find_releases(lines)

        # Track state through file
        self._track_resource_states(lines, opens, closes, releases)

        # Detect leaks
        findings = self._detect_leaks(file_path, lines)

        # Calculate analysis time
        analysis_time_ms = int((time.time() - start_time) * 1000)

        return LeakReport(
            file_path=file_path,
            language=self.get_language(),
            opens=opens,
            closes=closes,
            findings=findings,
            analysis_time_ms=analysis_time_ms,
        )

    def _find_opens(self, lines: List[str]) -> List[ResourceOperation]:
        """Find all resource open operations."""
        operations = []
        current_loop = False
        current_function = ""

        for line_num, line in enumerate(lines, 1):
            # Track loop context
            for pattern in self._compiled_patterns.get("loop", []):
                if pattern.search(line):
                    current_loop = True

            # Track function context
            for pattern in self._compiled_patterns.get("function", []):
                match = pattern.search(line)
                if match:
                    current_function = match.group(1) if match.groups() else "anonymous"

            # Find opens
            for resource_type in ResourceType:
                key = f"open_{resource_type.value}"
                patterns = self._compiled_patterns.get(key, [])

                for pattern in patterns:
                    match = pattern.search(line)
                    if match:
                        var_name = match.group(1) if match.groups() else "unknown"

                        # Check if via wrapper
                        via_wrapper = False
                        wrapper_name = ""
                        for wrapper, wrapped in self._wrapper_map.items():
                            if wrapper.lower() in line.lower():
                                via_wrapper = True
                                wrapper_name = wrapper
                                break

                        op = ResourceOperation(
                            line_number=line_num,
                            operation_type="open",
                            resource_type=resource_type,
                            variable_name=var_name,
                            in_loop=current_loop,
                            in_function=current_function,
                            via_wrapper=via_wrapper,
                            wrapper_name=wrapper_name,
                            code_snippet=line.strip(),
                        )
                        operations.append(op)

                        # Create tracker
                        tracker = ResourceTracker(
                            variable_name=var_name,
                            resource_type=resource_type,
                            created_line=line_num,
                            in_loop=current_loop,
                            in_function=current_function,
                            via_wrapper=via_wrapper,
                        )
                        tracker.open(line_num)
                        self._resource_trackers[var_name.lower()] = tracker

        return operations

    def _find_closes(self, lines: List[str]) -> List[ResourceOperation]:
        """Find all resource close operations."""
        operations = []

        for line_num, line in enumerate(lines, 1):
            for resource_type in ResourceType:
                key = f"close_{resource_type.value}"
                patterns = self._compiled_patterns.get(key, [])

                for pattern in patterns:
                    match = pattern.search(line)
                    if match:
                        var_name = match.group(1) if match.groups() else "unknown"
                        operations.append(ResourceOperation(
                            line_number=line_num,
                            operation_type="close",
                            resource_type=resource_type,
                            variable_name=var_name,
                            code_snippet=line.strip(),
                        ))

        return operations

    def _find_releases(self, lines: List[str]) -> List[ResourceOperation]:
        """Find all resource release operations (Set = Nothing)."""
        operations = []

        for line_num, line in enumerate(lines, 1):
            for resource_type in ResourceType:
                key = f"release_{resource_type.value}"
                patterns = self._compiled_patterns.get(key, [])

                for pattern in patterns:
                    match = pattern.search(line)
                    if match:
                        var_name = match.group(1) if match.groups() else "unknown"
                        operations.append(ResourceOperation(
                            line_number=line_num,
                            operation_type="release",
                            resource_type=resource_type,
                            variable_name=var_name,
                            code_snippet=line.strip(),
                        ))

        return operations

    def _track_resource_states(
        self,
        lines: List[str],
        opens: List[ResourceOperation],
        closes: List[ResourceOperation],
        releases: List[ResourceOperation],
    ) -> None:
        """Track resource state transitions through the file."""
        # Apply close operations
        for close_op in closes:
            var_key = close_op.variable_name.lower()
            if var_key in self._resource_trackers:
                self._resource_trackers[var_key].close(close_op.line_number)

        # Apply release operations
        for release_op in releases:
            var_key = release_op.variable_name.lower()
            if var_key in self._resource_trackers:
                self._resource_trackers[var_key].release(release_op.line_number)

    def _detect_leaks(
        self,
        file_path: str,
        lines: List[str],
    ) -> List[LeakFinding]:
        """Detect leaks based on tracked resource states."""
        findings = []

        for var_name, tracker in self._resource_trackers.items():
            leak_pattern = tracker.get_leak_pattern()

            if leak_pattern:
                severity = self._calculate_severity(tracker, leak_pattern)
                description = self._generate_description(tracker, leak_pattern)
                suggested_fix = self._generate_fix_suggestion(tracker, leak_pattern)

                # Get code context (3 lines before and after)
                leak_line = tracker.opened_line or tracker.created_line
                start = max(0, leak_line - 4)
                end = min(len(lines), leak_line + 3)
                code_context = lines[start:end]

                finding = LeakFinding(
                    file_path=file_path,
                    line_number=leak_line,
                    resource_type=tracker.resource_type,
                    variable_name=tracker.variable_name,
                    leak_pattern=leak_pattern,
                    severity=severity,
                    category=self.get_category(),
                    description=description,
                    suggested_fix=suggested_fix,
                    code_context=code_context,
                    confidence=self._calculate_confidence(tracker),
                )
                findings.append(finding)

        return findings

    def _calculate_severity(
        self,
        tracker: ResourceTracker,
        pattern: LeakPatternType,
    ) -> SeverityLevel:
        """
        Calculate severity based on resource type and pattern.

        Priority (from FysioOne audit):
        1. Connection leaks = CRITICAL (pool exhaustion)
        2. Loop leaks = CRITICAL (multiplicative)
        3. Recordset leaks = HIGH
        4. Reopen leaks = HIGH
        5. Other patterns = MEDIUM
        """
        # Connection leaks are always critical
        if tracker.resource_type == ResourceType.DATABASE_CONNECTION:
            return SeverityLevel.CRITICAL

        # Loop leaks are critical (multiplier effect)
        if pattern == LeakPatternType.LOOP_LEAK:
            return SeverityLevel.CRITICAL

        # Recordset and COM leaks are high
        if tracker.resource_type in [ResourceType.RECORDSET, ResourceType.COM_OBJECT]:
            return SeverityLevel.HIGH

        # Reopen pattern is high (from audit)
        if pattern == LeakPatternType.REOPEN_LEAK:
            return SeverityLevel.HIGH

        # Set without close is high
        if pattern == LeakPatternType.SET_WITHOUT_CLOSE:
            return SeverityLevel.HIGH

        return SeverityLevel.MEDIUM

    def _calculate_confidence(self, tracker: ResourceTracker) -> float:
        """Calculate confidence score for the finding."""
        confidence = 1.0

        # Lower confidence for wrapper functions (might handle cleanup internally)
        if tracker.via_wrapper:
            confidence -= 0.1

        # Higher confidence for explicit creates
        if not tracker.via_wrapper:
            confidence = min(1.0, confidence + 0.1)

        return confidence

    def _generate_description(
        self,
        tracker: ResourceTracker,
        pattern: LeakPatternType,
    ) -> str:
        """Generate human-readable description of the leak."""
        var = tracker.variable_name
        resource = tracker.resource_type.value.replace("_", " ")

        descriptions = {
            LeakPatternType.NEVER_CLOSED: f"{var} ({resource}) opened at line {tracker.opened_line} but never closed",
            LeakPatternType.LOOP_LEAK: f"{var} ({resource}) created in loop without per-iteration cleanup - causes {tracker.reopen_count or 'N'} leaks per iteration",
            LeakPatternType.FUNCTION_LEAK: f"{var} ({resource}) opened in function '{tracker.in_function}' without cleanup before return",
            LeakPatternType.REOPEN_LEAK: f"{var} ({resource}) reopened at line {tracker.opened_line} after close without final close",
            LeakPatternType.SET_WITHOUT_CLOSE: f"{var} ({resource}) released with Set = Nothing at line {tracker.released_line} without calling .Close() first",
            LeakPatternType.EARLY_EXIT_LEAK: f"{var} ({resource}) may leak on early exit path",
            LeakPatternType.CONDITIONAL_LEAK: f"{var} ({resource}) close may be skipped due to conditional logic",
        }

        return descriptions.get(pattern, f"{var} ({resource}) potential leak detected")

    def _generate_fix_suggestion(
        self,
        tracker: ResourceTracker,
        pattern: LeakPatternType,
    ) -> str:
        """Generate fix suggestion based on pattern."""
        var = tracker.variable_name

        suggestions = {
            LeakPatternType.NEVER_CLOSED: f"Add {var}.Close() before end of scope or Set {var} = Nothing",
            LeakPatternType.LOOP_LEAK: f"Move {var}.Close() inside the loop before the next iteration, or use CleanupResources helper",
            LeakPatternType.FUNCTION_LEAK: f"Add cleanup in finally block or before all return statements",
            LeakPatternType.REOPEN_LEAK: f"Add {var}.Close() after the second Open() call, or use SafeEnd helper",
            LeakPatternType.SET_WITHOUT_CLOSE: f"Add {var}.Close() BEFORE Set {var} = Nothing",
            LeakPatternType.EARLY_EXIT_LEAK: f"Use SafeRedirect/SafeEnd helper that ensures cleanup before exit",
            LeakPatternType.CONDITIONAL_LEAK: f"Ensure {var}.Close() is called in all conditional branches",
        }

        return suggestions.get(pattern, f"Ensure proper cleanup of {var}")

    def supports_file(self, file_path: str) -> bool:
        """Check if this detector supports the given file."""
        for ext in self.get_supported_extensions():
            if file_path.lower().endswith(ext.lower()):
                return True
        return False
