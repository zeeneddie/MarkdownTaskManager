"""
Types and dataclasses for Quality Impact Mapping.

Fase 29: Data structures for linking quality issues to functionality impact.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any


class IssueType(str, Enum):
    """Types of quality issues."""
    SECURITY = "security"
    PRIVACY = "privacy"
    PERFORMANCE = "performance"
    MEMORY_LEAK = "memory_leak"
    RESOURCE_LEAK = "resource_leak"
    DUPLICATION = "duplication"
    ERROR_HANDLING = "error_handling"
    CODE_SMELL = "code_smell"
    DEPRECATED = "deprecated"


class ImpactSeverity(str, Enum):
    """Severity levels for impact assessment."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RegulatoryRisk(str, Enum):
    """Regulatory compliance risks."""
    GDPR = "GDPR"
    WGBO = "WGBO"  # Dutch healthcare law
    NEN7510 = "NEN7510"  # Dutch healthcare security standard
    HIPAA = "HIPAA"
    PCI_DSS = "PCI_DSS"
    SOX = "SOX"
    ISO27001 = "ISO27001"


@dataclass
class QualityIssue:
    """A quality issue detected in the codebase."""
    issue_id: str
    issue_type: IssueType
    severity: ImpactSeverity
    location: Dict[str, Any]  # {"file": str, "line": int, "function": str}
    description: str
    recommendation: str
    cwe_id: Optional[str] = None
    data_exposed: List[str] = field(default_factory=list)
    source_scanner: str = ""
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "location": self.location,
            "description": self.description,
            "recommendation": self.recommendation,
            "cwe_id": self.cwe_id,
            "data_exposed": self.data_exposed,
            "source_scanner": self.source_scanner,
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass
class FunctionalityImpact:
    """Impact of a quality issue on functionality."""
    epic_id: Optional[str] = None
    epic_name: Optional[str] = None
    feature_id: Optional[str] = None
    feature_name: Optional[str] = None
    story_id: Optional[str] = None
    story_name: Optional[str] = None
    users_affected_daily: int = 0
    business_process: str = ""
    regulatory_risks: List[RegulatoryRisk] = field(default_factory=list)
    business_impact_description: str = ""
    financial_risk_estimate: str = ""
    confidence_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "epic": {
                "id": self.epic_id,
                "name": self.epic_name,
            },
            "feature": {
                "id": self.feature_id,
                "name": self.feature_name,
            },
            "story": {
                "id": self.story_id,
                "name": self.story_name,
            },
            "users_affected_daily": self.users_affected_daily,
            "business_process": self.business_process,
            "regulatory_risks": [r.value for r in self.regulatory_risks],
            "business_impact": self.business_impact_description,
            "financial_risk": self.financial_risk_estimate,
            "confidence_score": round(self.confidence_score, 2),
        }


@dataclass
class QualityImpactMapping:
    """Complete mapping of a quality issue to its functionality impact."""
    issue: QualityIssue
    impact: FunctionalityImpact
    impact_score: float = 0.0
    priority_rank: int = 0
    mapped_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue": self.issue.to_dict(),
            "impact": self.impact.to_dict(),
            "impact_score": round(self.impact_score, 2),
            "priority_rank": self.priority_rank,
            "mapped_at": self.mapped_at.isoformat(),
        }


@dataclass
class ImpactSummary:
    """Summary of quality impact for a functionality unit (Epic/Feature/Story)."""
    entity_type: str  # "epic", "feature", "story"
    entity_id: str
    entity_name: str
    health_score: float  # 0-100
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    total_issues: int = 0
    top_issues: List[QualityImpactMapping] = field(default_factory=list)
    regulatory_risks: List[RegulatoryRisk] = field(default_factory=list)
    estimated_users_affected: int = 0
    estimated_daily_risk: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "health_score": round(self.health_score, 1),
            "issues_by_severity": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
            },
            "total_issues": self.total_issues,
            "top_issues": [m.to_dict() for m in self.top_issues[:5]],
            "regulatory_risks": [r.value for r in self.regulatory_risks],
            "estimated_users_affected": self.estimated_users_affected,
            "estimated_daily_risk": self.estimated_daily_risk,
        }


@dataclass
class ProjectImpactReport:
    """Complete quality impact report for a project."""
    project_id: str
    project_name: str
    analysis_timestamp: datetime
    overall_health_score: float
    total_mappings: int
    mappings_by_severity: Dict[str, int]
    mappings_by_type: Dict[str, int]
    epic_summaries: List[ImpactSummary] = field(default_factory=list)
    feature_summaries: List[ImpactSummary] = field(default_factory=list)
    critical_issues: List[QualityImpactMapping] = field(default_factory=list)
    unmapped_issues: List[QualityIssue] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "overall_health_score": round(self.overall_health_score, 1),
            "total_mappings": self.total_mappings,
            "mappings_by_severity": self.mappings_by_severity,
            "mappings_by_type": self.mappings_by_type,
            "epic_summaries": [s.to_dict() for s in self.epic_summaries],
            "feature_summaries": [s.to_dict() for s in self.feature_summaries[:10]],
            "critical_issues": [m.to_dict() for m in self.critical_issues],
            "unmapped_issues_count": len(self.unmapped_issues),
        }
