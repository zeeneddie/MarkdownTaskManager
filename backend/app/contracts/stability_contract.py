# Stability Contract
# Shared interface for stability analysis results
#
# Used by:
# - Brown Paper (creates stability info during analysis)
# - Migration (consumes stability info for risk assessment)
# - Quality (standalone and scheduled stability scans)
#
# Based on: backend/app/services/stability/types.py

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone


class StabilitySeverity(Enum):
    """Severity levels for stability findings."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class StabilityCategoryType(Enum):
    """8 stability analysis categories."""
    ADO_LEAKS = "ado_leaks"
    COM_OBJECTS = "com_objects"
    EXTERNAL_SERVICES = "external_services"
    MEMORY_INTENSIVE = "memory_intensive"
    FILE_HANDLES = "file_handles"
    SESSION_STATE = "session_state"
    EXCEPTION_HANDLING = "exception_handling"
    SQL_PERFORMANCE = "sql_performance"


@dataclass
class StabilityFindingSummary:
    """
    Summary of a single stability finding.
    Lightweight version for contracts (no full code context).
    """
    file_path: str
    line_number: int
    category: str
    severity: str
    description: str
    suggested_fix: str
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "suggested_fix": self.suggested_fix,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StabilityFindingSummary":
        return cls(
            file_path=data.get("file_path", ""),
            line_number=data.get("line_number", 0),
            category=data.get("category", ""),
            severity=data.get("severity", "LOW"),
            description=data.get("description", ""),
            suggested_fix=data.get("suggested_fix", ""),
            confidence=data.get("confidence", 1.0),
        )


@dataclass
class StabilityCategorySummary:
    """Summary of findings for a stability category."""
    category: str
    issues_found: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    @property
    def severity_score(self) -> int:
        """Calculate severity score (higher = worse)."""
        return (
            self.critical_count * 100 +
            self.high_count * 50 +
            self.medium_count * 10 +
            self.low_count * 1
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "issues_found": self.issues_found,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "severity_score": self.severity_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StabilityCategorySummary":
        return cls(
            category=data.get("category", ""),
            issues_found=data.get("issues_found", 0),
            critical_count=data.get("critical_count", 0),
            high_count=data.get("high_count", 0),
            medium_count=data.get("medium_count", 0),
            low_count=data.get("low_count", 0),
        )


@dataclass
class StabilityInfo:
    """
    Complete stability information for a project.
    This is the stability portion of the AnalysisContract.
    """
    overall_score: int = 100  # 0-100
    overall_risk: str = "LOW"  # CRITICAL, HIGH, MEDIUM, LOW
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0

    # Per-category summaries
    categories: Dict[str, StabilityCategorySummary] = field(default_factory=dict)

    # Top findings (limited for contract size)
    top_findings: List[StabilityFindingSummary] = field(default_factory=list)

    # Metadata
    files_scanned: int = 0
    languages_analyzed: List[str] = field(default_factory=list)
    scan_timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "overall_risk": self.overall_risk,
            "total_findings": self.total_findings,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "categories": {k: v.to_dict() for k, v in self.categories.items()},
            "top_findings": [f.to_dict() for f in self.top_findings],
            "files_scanned": self.files_scanned,
            "languages_analyzed": self.languages_analyzed,
            "scan_timestamp": self.scan_timestamp.isoformat() if self.scan_timestamp else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StabilityInfo":
        categories = {}
        for k, v in data.get("categories", {}).items():
            categories[k] = StabilityCategorySummary.from_dict(v)

        top_findings = [
            StabilityFindingSummary.from_dict(f)
            for f in data.get("top_findings", [])
        ]

        scan_ts = data.get("scan_timestamp")
        if scan_ts and isinstance(scan_ts, str):
            scan_ts = datetime.fromisoformat(scan_ts)

        return cls(
            overall_score=data.get("overall_score", 100),
            overall_risk=data.get("overall_risk", "LOW"),
            total_findings=data.get("total_findings", 0),
            critical_count=data.get("critical_count", 0),
            high_count=data.get("high_count", 0),
            categories=categories,
            top_findings=top_findings,
            files_scanned=data.get("files_scanned", 0),
            languages_analyzed=data.get("languages_analyzed", []),
            scan_timestamp=scan_ts,
        )

    @classmethod
    def empty(cls) -> "StabilityInfo":
        """Create empty stability info when no analysis performed."""
        return cls()
