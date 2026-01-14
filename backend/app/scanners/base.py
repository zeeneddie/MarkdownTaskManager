"""
Base Scanner Classes

Defines the interface for all quality scanners.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from pathlib import Path
from datetime import datetime


class Severity(Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingType(Enum):
    """Types of quality findings"""
    CODE_SMELL = "code_smell"
    BUG = "bug"
    VULNERABILITY = "vulnerability"
    SECURITY = "security"
    DUPLICATION = "duplication"
    COMPLEXITY = "complexity"
    COVERAGE = "coverage"
    STYLE = "style"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"
    DEPENDENCY = "dependency"
    TEST_GAP = "test_gap"
    COMPATIBILITY = "compatibility"
    ACCESSIBILITY = "accessibility"


@dataclass
class ScanFinding:
    """A single finding from a scanner"""
    scanner: str
    rule_id: str
    message: str
    severity: Severity
    finding_type: FindingType
    file_path: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: Optional[str] = None
    effort_minutes: int = 5  # Estimated fix time
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scanner": self.scanner,
            "rule_id": self.rule_id,
            "message": self.message,
            "severity": self.severity.value,
            "finding_type": self.finding_type.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "code_snippet": self.code_snippet,
            "recommendation": self.recommendation,
            "effort_minutes": self.effort_minutes,
            "tags": self.tags,
            "metadata": self.metadata
        }


@dataclass
class ScanMetrics:
    """Metrics collected during scan"""
    files_scanned: int = 0
    lines_of_code: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    code_lines: int = 0
    complexity_average: Optional[float] = None
    duplication_percentage: Optional[float] = None
    test_coverage: Optional[float] = None
    file_type_breakdown: Dict[str, int] = field(default_factory=dict)
    module_breakdown: Dict[str, Dict[str, int]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files_scanned": self.files_scanned,
            "lines_of_code": self.lines_of_code,
            "blank_lines": self.blank_lines,
            "comment_lines": self.comment_lines,
            "code_lines": self.code_lines,
            "complexity_average": self.complexity_average,
            "duplication_percentage": self.duplication_percentage,
            "test_coverage": self.test_coverage,
            "file_type_breakdown": self.file_type_breakdown,
            "module_breakdown": self.module_breakdown,
            "metadata": self.metadata
        }


@dataclass
class ScanResult:
    """Complete result from a scanner run"""
    scanner_name: str
    scanner_version: str
    stack: str
    project_path: str
    started_at: datetime
    completed_at: datetime
    success: bool
    findings: List[ScanFinding] = field(default_factory=list)
    metrics: ScanMetrics = field(default_factory=ScanMetrics)
    error_message: Optional[str] = None

    @property
    def duration_seconds(self) -> float:
        return (self.completed_at - self.started_at).total_seconds()

    @property
    def findings_by_severity(self) -> Dict[str, int]:
        counts = {s.value: 0 for s in Severity}
        for f in self.findings:
            counts[f.severity.value] += 1
        return counts

    @property
    def total_findings(self) -> int:
        return len(self.findings)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scanner_name": self.scanner_name,
            "scanner_version": self.scanner_version,
            "stack": self.stack,
            "project_path": self.project_path,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "duration_seconds": self.duration_seconds,
            "success": self.success,
            "total_findings": self.total_findings,
            "findings_by_severity": self.findings_by_severity,
            "findings": [f.to_dict() for f in self.findings],
            "metrics": self.metrics.to_dict(),
            "error_message": self.error_message
        }


class BaseScanner(ABC):
    """Abstract base class for all scanners"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)

    @property
    @abstractmethod
    def name(self) -> str:
        """Scanner name"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Scanner version"""
        pass

    @property
    @abstractmethod
    def supported_stacks(self) -> List[str]:
        """List of supported tech stacks (e.g., ['python'], ['dotnet', 'csharp'])"""
        pass

    @property
    @abstractmethod
    def scanner_type(self) -> str:
        """Type of scanner (e.g., 'linter', 'security', 'volume', 'duplication')"""
        pass

    @abstractmethod
    async def scan(self) -> ScanResult:
        """Execute the scan and return results"""
        pass

    def is_available(self) -> bool:
        """Check if the scanner is available (tools installed, etc.)"""
        return True

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for this scanner"""
        return {}
