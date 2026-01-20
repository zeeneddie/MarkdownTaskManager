# Quality Contract
# Interfaces for quality scanning, scheduling, and gate evaluation
#
# Used by:
# - Quality standalone scans (Mode 1)
# - Brown Paper integrated scans (Mode 2)
# - Scheduled periodic scans (Mode 3)
#
# Architecture: docs/architecture/workflow-separation-plan.md
# Phase: Fase 21.5 (Week 145-146)

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from app.utils.datetime_utils import utc_now
import uuid


class ScheduleType(Enum):
    """Types of quality scan schedules."""
    DAILY = "daily"
    WEEKLY = "weekly"
    INTERVAL = "interval"
    ON_COMMIT = "on_commit"
    MANUAL = "manual"


class QualityGateStatus(Enum):
    """Quality gate evaluation status."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class QualitySeverity(Enum):
    """Severity levels for quality violations."""
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


@dataclass
class QualityRuleViolation:
    """A single quality rule violation."""
    rule_id: str
    rule_name: str
    severity: str
    file_path: str
    line_number: int = 0
    message: str = ""
    suggestion: str = ""
    category: str = ""  # security, performance, maintainability, etc.

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "message": self.message,
            "suggestion": self.suggestion,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityRuleViolation":
        return cls(
            rule_id=data.get("rule_id", ""),
            rule_name=data.get("rule_name", ""),
            severity=data.get("severity", "minor"),
            file_path=data.get("file_path", ""),
            line_number=data.get("line_number", 0),
            message=data.get("message", ""),
            suggestion=data.get("suggestion", ""),
            category=data.get("category", ""),
        )


@dataclass
class QualityScanResult:
    """
    Result of a quality scan.
    Independent of Brown Paper or Migration.
    """
    scan_id: str
    project_id: str
    project_path: str

    # Scores
    overall_score: int = 100  # 0-100
    security_score: int = 100
    performance_score: int = 100
    maintainability_score: int = 100
    reliability_score: int = 100

    # Violation counts
    blocker_count: int = 0
    critical_count: int = 0
    major_count: int = 0
    minor_count: int = 0

    # Violations (limited for size)
    violations: List[QualityRuleViolation] = field(default_factory=list)

    # Metadata
    files_scanned: int = 0
    rules_evaluated: int = 0
    scan_duration_seconds: float = 0.0
    scan_timestamp: datetime = field(default_factory=utc_now)

    # Source info
    schedule_id: Optional[str] = None
    triggered_by: str = "manual"  # manual, schedule, integration

    @property
    def total_violations(self) -> int:
        return self.blocker_count + self.critical_count + self.major_count + self.minor_count

    @property
    def has_blockers(self) -> bool:
        return self.blocker_count > 0

    @property
    def is_passing(self) -> bool:
        return self.blocker_count == 0 and self.critical_count == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "project_id": self.project_id,
            "project_path": self.project_path,
            "overall_score": self.overall_score,
            "security_score": self.security_score,
            "performance_score": self.performance_score,
            "maintainability_score": self.maintainability_score,
            "reliability_score": self.reliability_score,
            "blocker_count": self.blocker_count,
            "critical_count": self.critical_count,
            "major_count": self.major_count,
            "minor_count": self.minor_count,
            "total_violations": self.total_violations,
            "violations": [v.to_dict() for v in self.violations],
            "files_scanned": self.files_scanned,
            "rules_evaluated": self.rules_evaluated,
            "scan_duration_seconds": self.scan_duration_seconds,
            "scan_timestamp": self.scan_timestamp.isoformat(),
            "schedule_id": self.schedule_id,
            "triggered_by": self.triggered_by,
            "is_passing": self.is_passing,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityScanResult":
        violations = [
            QualityRuleViolation.from_dict(v)
            for v in data.get("violations", [])
        ]

        scan_ts = data.get("scan_timestamp")
        if scan_ts and isinstance(scan_ts, str):
            scan_ts = datetime.fromisoformat(scan_ts.replace("Z", "+00:00"))
        else:
            scan_ts = datetime.now(timezone.utc)

        return cls(
            scan_id=data.get("scan_id", str(uuid.uuid4())),
            project_id=data.get("project_id", ""),
            project_path=data.get("project_path", ""),
            overall_score=data.get("overall_score", 100),
            security_score=data.get("security_score", 100),
            performance_score=data.get("performance_score", 100),
            maintainability_score=data.get("maintainability_score", 100),
            reliability_score=data.get("reliability_score", 100),
            blocker_count=data.get("blocker_count", 0),
            critical_count=data.get("critical_count", 0),
            major_count=data.get("major_count", 0),
            minor_count=data.get("minor_count", 0),
            violations=violations,
            files_scanned=data.get("files_scanned", 0),
            rules_evaluated=data.get("rules_evaluated", 0),
            scan_duration_seconds=data.get("scan_duration_seconds", 0.0),
            scan_timestamp=scan_ts,
            schedule_id=data.get("schedule_id"),
            triggered_by=data.get("triggered_by", "manual"),
        )


@dataclass
class QualityGateResult:
    """Result of a quality gate evaluation."""
    project_id: str
    gate_name: str
    status: QualityGateStatus
    score: int
    threshold: int

    # Individual gate checks
    checks: List[Dict[str, Any]] = field(default_factory=list)

    # Blocking issues
    blocking_issues: List[str] = field(default_factory=list)

    # Metadata
    evaluated_at: datetime = field(default_factory=utc_now)
    scan_id: Optional[str] = None

    @property
    def is_passed(self) -> bool:
        return self.status == QualityGateStatus.PASSED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "gate_name": self.gate_name,
            "status": self.status.value,
            "score": self.score,
            "threshold": self.threshold,
            "checks": self.checks,
            "blocking_issues": self.blocking_issues,
            "evaluated_at": self.evaluated_at.isoformat(),
            "scan_id": self.scan_id,
            "is_passed": self.is_passed,
        }


@dataclass
class QualitySchedule:
    """Configuration for scheduled quality scans."""
    schedule_id: str
    project_id: str
    schedule_type: ScheduleType
    enabled: bool = True

    # Schedule configuration
    hour: int = 2  # Hour of day (0-23) for daily/weekly
    day_of_week: str = "mon"  # For weekly schedules
    interval_hours: int = 24  # For interval schedules

    # Focus areas (optional filters)
    focus_areas: List[str] = field(default_factory=list)  # security, performance, etc.

    # Metadata
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    last_scan_id: Optional[str] = None
    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schedule_id": self.schedule_id,
            "project_id": self.project_id,
            "schedule_type": self.schedule_type.value,
            "enabled": self.enabled,
            "hour": self.hour,
            "day_of_week": self.day_of_week,
            "interval_hours": self.interval_hours,
            "focus_areas": self.focus_areas,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "last_scan_id": self.last_scan_id,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualitySchedule":
        schedule_type_str = data.get("schedule_type", "daily")
        try:
            schedule_type = ScheduleType(schedule_type_str)
        except ValueError:
            schedule_type = ScheduleType.DAILY

        def parse_dt(val):
            if val and isinstance(val, str):
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
            return val

        return cls(
            schedule_id=data.get("schedule_id", str(uuid.uuid4())),
            project_id=data.get("project_id", ""),
            schedule_type=schedule_type,
            enabled=data.get("enabled", True),
            hour=data.get("hour", 2),
            day_of_week=data.get("day_of_week", "mon"),
            interval_hours=data.get("interval_hours", 24),
            focus_areas=data.get("focus_areas", []),
            next_run_at=parse_dt(data.get("next_run_at")),
            last_run_at=parse_dt(data.get("last_run_at")),
            last_scan_id=data.get("last_scan_id"),
            created_at=parse_dt(data.get("created_at")) or datetime.now(timezone.utc),
        )

    @classmethod
    def create_daily(cls, project_id: str, hour: int = 2) -> "QualitySchedule":
        """Create a daily schedule."""
        return cls(
            schedule_id=str(uuid.uuid4()),
            project_id=project_id,
            schedule_type=ScheduleType.DAILY,
            hour=hour,
        )

    @classmethod
    def create_weekly(cls, project_id: str, day: str = "mon", hour: int = 2) -> "QualitySchedule":
        """Create a weekly schedule."""
        return cls(
            schedule_id=str(uuid.uuid4()),
            project_id=project_id,
            schedule_type=ScheduleType.WEEKLY,
            day_of_week=day,
            hour=hour,
        )

    @classmethod
    def create_interval(cls, project_id: str, hours: int = 24) -> "QualitySchedule":
        """Create an interval schedule."""
        return cls(
            schedule_id=str(uuid.uuid4()),
            project_id=project_id,
            schedule_type=ScheduleType.INTERVAL,
            interval_hours=hours,
        )


@dataclass
class QualityContract:
    """
    Contract for quality validation.
    Can be used standalone or integrated with AnalysisContract.
    """
    quality_id: str
    project_id: str
    project_path: str

    # Latest scan result
    latest_scan: Optional[QualityScanResult] = None

    # Quality gate status
    gate_result: Optional[QualityGateResult] = None

    # Schedule info
    schedule: Optional[QualitySchedule] = None

    # Historical data (limited)
    scan_history: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quality_id": self.quality_id,
            "project_id": self.project_id,
            "project_path": self.project_path,
            "latest_scan": self.latest_scan.to_dict() if self.latest_scan else None,
            "gate_result": self.gate_result.to_dict() if self.gate_result else None,
            "schedule": self.schedule.to_dict() if self.schedule else None,
            "scan_history": self.scan_history,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def create_new(cls, project_id: str, project_path: str) -> "QualityContract":
        """Factory method to create a new quality contract."""
        return cls(
            quality_id=str(uuid.uuid4()),
            project_id=project_id,
            project_path=project_path,
        )
