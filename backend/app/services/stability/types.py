# Stability Analysis Types
# Enums and Dataclasses for Resource Leak Detection
#
# Based on:
# - docs/architecture/asp-stability-analyzer-framework.md
# - docs/architecture/resource-leak-detection-framework.md
# - FysioOne Audit learnings (2026-01-06)

from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


# === Enums ===

class ResourceType(Enum):
    """Types of resources that can leak."""
    DATABASE_CONNECTION = "database_connection"
    RECORDSET = "recordset"
    FILE_HANDLE = "file_handle"
    HTTP_CONNECTION = "http_connection"
    COM_OBJECT = "com_object"
    STREAM = "stream"
    PDF_DOCUMENT = "pdf_document"
    XML_DOCUMENT = "xml_document"
    SESSION_OBJECT = "session_object"


class LeakPatternType(Enum):
    """
    Patterns of resource leaks.

    Based on FysioOne Audit learnings:
    - REOPEN_LEAK: Open→Close→Open without final close (new!)
    - SET_WITHOUT_CLOSE: Only Set = Nothing without .Close() (new!)
    """
    NEVER_CLOSED = "never_closed"
    LOOP_LEAK = "loop_leak"
    FUNCTION_LEAK = "function_leak"
    EARLY_EXIT_LEAK = "early_exit_leak"
    CONDITIONAL_LEAK = "conditional_leak"
    REOPEN_LEAK = "reopen_leak"  # ⚠️ From peer review
    SET_WITHOUT_CLOSE = "set_without_close"  # ⚠️ From peer review


class StabilityCategory(Enum):
    """
    8 stability analysis categories.

    Priority order for severity:
    1. ADO_LEAKS (Connection > Recordset)
    2. COM_OBJECTS
    3. EXTERNAL_SERVICES
    4. MEMORY_INTENSIVE
    5. FILE_HANDLES
    6. SESSION_STATE
    7. EXCEPTION_HANDLING
    8. SQL_PERFORMANCE
    """
    ADO_LEAKS = "ado_leaks"
    COM_OBJECTS = "com_objects"
    EXTERNAL_SERVICES = "external_services"
    MEMORY_INTENSIVE = "memory_intensive"
    FILE_HANDLES = "file_handles"
    SESSION_STATE = "session_state"
    EXCEPTION_HANDLING = "exception_handling"
    SQL_PERFORMANCE = "sql_performance"


class SeverityLevel(Enum):
    """Severity levels for findings."""
    CRITICAL = "CRITICAL"  # Connection leaks, loop leaks
    HIGH = "HIGH"          # Recordset leaks, COM objects
    MEDIUM = "MEDIUM"      # File handles, memory issues
    LOW = "LOW"            # Session issues, minor patterns
    INFO = "INFO"          # Informational findings


# === Resource State Machine ===

class ResourceState(Enum):
    """
    State machine for tracking resource lifecycle.

    Transitions:
    - CREATED → OPENED (via .Open())
    - OPENED → CLOSED (via .Close())
    - CLOSED → REOPENED (via .Open() again)
    - REOPENED → CLOSED (via .Close())
    - Any → RELEASED (via Set = Nothing)

    Leak conditions:
    - CREATED/OPENED at end of scope → NEVER_CLOSED
    - REOPENED at end of scope → REOPEN_LEAK
    - RELEASED without CLOSED → SET_WITHOUT_CLOSE
    """
    CREATED = "created"
    OPENED = "opened"
    CLOSED = "closed"
    REOPENED = "reopened"
    RELEASED = "released"


# === Data Classes ===

@dataclass
class ResourceOperation:
    """A single resource operation (open or close)."""
    line_number: int
    operation_type: str  # 'open', 'close', 'release', 'create'
    resource_type: ResourceType
    variable_name: str
    in_loop: bool = False
    in_function: str = ""
    via_wrapper: bool = False
    wrapper_name: str = ""
    code_snippet: str = ""
    state: ResourceState = ResourceState.CREATED


@dataclass
class LeakFinding:
    """A detected resource leak."""
    file_path: str
    line_number: int
    resource_type: ResourceType
    variable_name: str
    leak_pattern: LeakPatternType
    severity: SeverityLevel
    category: StabilityCategory
    description: str
    suggested_fix: str
    code_context: List[str] = field(default_factory=list)
    confidence: float = 1.0  # 0.0 - 1.0

    @property
    def is_critical(self) -> bool:
        return self.severity == SeverityLevel.CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "resource_type": self.resource_type.value,
            "variable_name": self.variable_name,
            "leak_pattern": self.leak_pattern.value,
            "severity": self.severity.value,
            "category": self.category.value,
            "description": self.description,
            "suggested_fix": self.suggested_fix,
            "code_context": self.code_context,
            "confidence": self.confidence,
        }


@dataclass
class LeakReport:
    """Complete leak detection report for a single file."""
    file_path: str
    language: str
    scan_timestamp: datetime = field(default_factory=datetime.now)
    opens: List[ResourceOperation] = field(default_factory=list)
    closes: List[ResourceOperation] = field(default_factory=list)
    findings: List[LeakFinding] = field(default_factory=list)
    analysis_time_ms: int = 0

    @property
    def has_leaks(self) -> bool:
        return len(self.findings) > 0

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SeverityLevel.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SeverityLevel.HIGH)

    @property
    def total_opens(self) -> int:
        return len(self.opens)

    @property
    def total_closes(self) -> int:
        return len(self.closes)

    @property
    def leak_rate(self) -> float:
        """Percentage of opens without corresponding closes."""
        if self.total_opens == 0:
            return 0.0
        return (self.total_opens - self.total_closes) / self.total_opens * 100


@dataclass
class CategoryFinding:
    """Findings for a specific stability category."""
    category: StabilityCategory
    findings: List[LeakFinding] = field(default_factory=list)
    files_analyzed: int = 0
    issues_found: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    @property
    def has_issues(self) -> bool:
        return self.issues_found > 0

    @property
    def severity_score(self) -> int:
        """Calculate severity score (higher = worse)."""
        return (
            self.critical_count * 100 +
            self.high_count * 50 +
            self.medium_count * 10 +
            self.low_count * 1
        )


@dataclass
class StabilityReport:
    """
    Complete stability analysis report for a project.

    Covers all 8 stability categories:
    1. ADO Leaks (Connection/Recordset)
    2. COM Objects (XMLHTTP, PDF, XMLDOM)
    3. External Services (Timeout, Retry)
    4. Memory Intensive (PDF gen, arrays)
    5. File Handles (FSO, TextStream)
    6. Session State (Size, timeout)
    7. Exception Handling (On Error)
    8. SQL Performance (N+1, deadlocks)
    """
    project_id: int
    project_name: str
    scan_timestamp: datetime = field(default_factory=datetime.now)
    total_files_scanned: int = 0
    total_files_with_issues: int = 0

    # Category-level findings
    categories: Dict[StabilityCategory, CategoryFinding] = field(default_factory=dict)

    # Aggregated metrics
    overall_score: int = 100  # 0-100, starts at 100, decremented by issues
    overall_risk: SeverityLevel = SeverityLevel.LOW

    # All findings (for detailed export)
    all_findings: List[LeakFinding] = field(default_factory=list)

    # Analysis metadata
    analysis_time_seconds: float = 0.0
    languages_analyzed: List[str] = field(default_factory=list)

    def add_finding(self, finding: LeakFinding) -> None:
        """Add a finding to the report."""
        self.all_findings.append(finding)

        # Update category stats
        if finding.category not in self.categories:
            self.categories[finding.category] = CategoryFinding(category=finding.category)

        cat = self.categories[finding.category]
        cat.findings.append(finding)
        cat.issues_found += 1

        if finding.severity == SeverityLevel.CRITICAL:
            cat.critical_count += 1
            self.overall_score -= 10
        elif finding.severity == SeverityLevel.HIGH:
            cat.high_count += 1
            self.overall_score -= 5
        elif finding.severity == SeverityLevel.MEDIUM:
            cat.medium_count += 1
            self.overall_score -= 2
        else:
            cat.low_count += 1
            self.overall_score -= 1

        # Ensure score doesn't go below 0
        self.overall_score = max(0, self.overall_score)

        # Update overall risk level
        self._update_risk_level()

    def _update_risk_level(self) -> None:
        """Update overall risk level based on findings."""
        critical_total = sum(c.critical_count for c in self.categories.values())
        high_total = sum(c.high_count for c in self.categories.values())

        if critical_total > 0:
            self.overall_risk = SeverityLevel.CRITICAL
        elif high_total > 5:
            self.overall_risk = SeverityLevel.HIGH
        elif high_total > 0:
            self.overall_risk = SeverityLevel.MEDIUM
        else:
            self.overall_risk = SeverityLevel.LOW

    @property
    def total_findings(self) -> int:
        return len(self.all_findings)

    @property
    def critical_count(self) -> int:
        return sum(c.critical_count for c in self.categories.values())

    @property
    def high_count(self) -> int:
        return sum(c.high_count for c in self.categories.values())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "scan_timestamp": self.scan_timestamp.isoformat(),
            "total_files_scanned": self.total_files_scanned,
            "total_files_with_issues": self.total_files_with_issues,
            "overall_score": self.overall_score,
            "overall_risk": self.overall_risk.value,
            "total_findings": self.total_findings,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "languages_analyzed": self.languages_analyzed,
            "analysis_time_seconds": self.analysis_time_seconds,
            "categories": {
                cat.value: {
                    "issues_found": cf.issues_found,
                    "critical_count": cf.critical_count,
                    "high_count": cf.high_count,
                    "medium_count": cf.medium_count,
                    "low_count": cf.low_count,
                    "severity_score": cf.severity_score,
                }
                for cat, cf in self.categories.items()
            },
        }
