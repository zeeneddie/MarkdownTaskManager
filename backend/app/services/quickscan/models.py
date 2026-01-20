"""
Legacy Quickscan Models.

Fase 24 - A1: Data models for 15-minute legacy assessment.
"""

from dataclasses import dataclass, field
from datetime import datetime
from app.utils.datetime_utils import utc_now
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path
import uuid


class Recommendation(Enum):
    """Go/No-Go recommendation for legacy modernization."""
    GO = "go"
    CONDITIONAL = "conditional"
    NO_GO = "no_go"


class RiskLevel(Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModernizationApproach(Enum):
    """Recommended modernization approach."""
    REHOST = "rehost"           # Lift & shift
    REPLATFORM = "replatform"   # Lift & reshape
    REFACTOR = "refactor"       # Re-architect
    REBUILD = "rebuild"         # Rewrite
    REPLACE = "replace"         # Buy COTS


@dataclass
class QuickscanConfig:
    """Configuration for quickscan execution."""
    project_path: Path
    project_name: str = ""
    max_scan_time_seconds: int = 900  # 15 minutes
    include_security_scan: bool = True
    include_dependency_scan: bool = True
    include_complexity_scan: bool = True
    include_quality_scan: bool = True
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "node_modules", "vendor", ".git", "__pycache__", "bin", "obj"
    ])

    def __post_init__(self):
        if isinstance(self.project_path, str):
            self.project_path = Path(self.project_path)
        if not self.project_name:
            self.project_name = self.project_path.name


@dataclass
class TechnologyStack:
    """Detected technology stack information."""
    primary_language: str
    languages: Dict[str, int] = field(default_factory=dict)  # language -> LOC
    frameworks: List[str] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    runtime_platforms: List[str] = field(default_factory=list)
    build_tools: List[str] = field(default_factory=list)

    # Age indicators
    legacy_indicators: List[str] = field(default_factory=list)
    modern_indicators: List[str] = field(default_factory=list)
    estimated_age_years: Optional[int] = None

    # Confidence
    detection_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_language": self.primary_language,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "databases": self.databases,
            "runtime_platforms": self.runtime_platforms,
            "build_tools": self.build_tools,
            "legacy_indicators": self.legacy_indicators,
            "modern_indicators": self.modern_indicators,
            "estimated_age_years": self.estimated_age_years,
            "detection_confidence": self.detection_confidence,
        }


@dataclass
class ComplexityScore:
    """Code complexity analysis results."""
    overall_score: float  # 0-100, higher = more complex

    # Detailed metrics
    cyclomatic_complexity_avg: float = 0.0
    cyclomatic_complexity_max: int = 0
    lines_of_code: int = 0
    files_count: int = 0
    functions_count: int = 0
    classes_count: int = 0

    # Maintainability
    maintainability_index: float = 0.0  # 0-100, higher = better
    technical_debt_hours: float = 0.0

    # Coupling
    coupling_score: float = 0.0
    dependency_depth: int = 0

    # Duplication
    duplication_percentage: float = 0.0
    duplicated_blocks: int = 0

    # Hot spots
    high_complexity_files: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "cyclomatic_complexity_avg": self.cyclomatic_complexity_avg,
            "cyclomatic_complexity_max": self.cyclomatic_complexity_max,
            "lines_of_code": self.lines_of_code,
            "files_count": self.files_count,
            "functions_count": self.functions_count,
            "classes_count": self.classes_count,
            "maintainability_index": self.maintainability_index,
            "technical_debt_hours": self.technical_debt_hours,
            "coupling_score": self.coupling_score,
            "dependency_depth": self.dependency_depth,
            "duplication_percentage": self.duplication_percentage,
            "duplicated_blocks": self.duplicated_blocks,
            "high_complexity_files": self.high_complexity_files[:10],
        }


@dataclass
class SecurityRisk:
    """Individual security risk finding."""
    cwe_id: str
    title: str
    severity: str
    count: int
    locations: List[str] = field(default_factory=list)


@dataclass
class RiskAssessment:
    """Security and risk analysis results."""
    overall_risk_score: float  # 0-100, higher = more risky
    risk_level: RiskLevel = RiskLevel.MEDIUM

    # Security findings
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0

    # Categories
    security_risks: List[SecurityRisk] = field(default_factory=list)
    compliance_gaps: List[str] = field(default_factory=list)

    # Dependencies
    outdated_dependencies: int = 0
    vulnerable_dependencies: int = 0
    total_dependencies: int = 0

    # Documentation
    documentation_coverage: float = 0.0
    test_coverage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_risk_score": self.overall_risk_score,
            "risk_level": self.risk_level.value,
            "critical_findings": self.critical_findings,
            "high_findings": self.high_findings,
            "medium_findings": self.medium_findings,
            "low_findings": self.low_findings,
            "security_risks": [
                {"cwe_id": r.cwe_id, "title": r.title, "severity": r.severity, "count": r.count}
                for r in self.security_risks[:10]
            ],
            "compliance_gaps": self.compliance_gaps,
            "outdated_dependencies": self.outdated_dependencies,
            "vulnerable_dependencies": self.vulnerable_dependencies,
            "total_dependencies": self.total_dependencies,
            "documentation_coverage": self.documentation_coverage,
            "test_coverage": self.test_coverage,
        }


@dataclass
class EffortEstimate:
    """Rough effort estimation for modernization."""
    total_person_months: float
    confidence: float  # 0-1

    # Breakdown
    analysis_months: float = 0.0
    development_months: float = 0.0
    testing_months: float = 0.0
    deployment_months: float = 0.0

    # Ranges
    optimistic_months: float = 0.0
    pessimistic_months: float = 0.0

    # Assumptions
    assumptions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_person_months": self.total_person_months,
            "confidence": self.confidence,
            "analysis_months": self.analysis_months,
            "development_months": self.development_months,
            "testing_months": self.testing_months,
            "deployment_months": self.deployment_months,
            "optimistic_months": self.optimistic_months,
            "pessimistic_months": self.pessimistic_months,
            "assumptions": self.assumptions,
        }


@dataclass
class QuickscanResult:
    """Individual analyzer result."""
    analyzer_name: str
    success: bool
    duration_seconds: float
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class QuickscanReport:
    """Complete quickscan report."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_name: str = ""
    project_path: str = ""

    # Timing
    started_at: datetime = field(default_factory=utc_now)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Core results
    technology_stack: Optional[TechnologyStack] = None
    complexity_score: Optional[ComplexityScore] = None
    risk_assessment: Optional[RiskAssessment] = None
    effort_estimate: Optional[EffortEstimate] = None

    # Recommendation
    recommendation: Recommendation = Recommendation.CONDITIONAL
    recommendation_score: float = 50.0  # 0-100
    recommendation_reasons: List[str] = field(default_factory=list)

    # Suggested approach
    suggested_approach: ModernizationApproach = ModernizationApproach.REFACTOR
    approach_rationale: str = ""

    # Key findings summary
    key_findings: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)

    # Next steps
    recommended_next_steps: List[str] = field(default_factory=list)

    # Analyzer results
    analyzer_results: List[QuickscanResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_name": self.project_name,
            "project_path": self.project_path,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "technology_stack": self.technology_stack.to_dict() if self.technology_stack else None,
            "complexity_score": self.complexity_score.to_dict() if self.complexity_score else None,
            "risk_assessment": self.risk_assessment.to_dict() if self.risk_assessment else None,
            "effort_estimate": self.effort_estimate.to_dict() if self.effort_estimate else None,
            "recommendation": self.recommendation.value,
            "recommendation_score": self.recommendation_score,
            "recommendation_reasons": self.recommendation_reasons,
            "suggested_approach": self.suggested_approach.value,
            "approach_rationale": self.approach_rationale,
            "key_findings": self.key_findings,
            "opportunities": self.opportunities,
            "challenges": self.challenges,
            "recommended_next_steps": self.recommended_next_steps,
        }
