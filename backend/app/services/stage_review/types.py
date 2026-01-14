"""
Stage Review Types.

Fase 23.6 Phase 24.1: Data types for stage-based LLM council reviews.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any


class StageType(str, Enum):
    """Development stages that can be reviewed."""
    ARCHITECTURE = "architecture"
    DESIGN = "design"
    ANALYSIS = "analysis"
    PROGRAMMING = "programming"
    TESTING = "testing"
    INFRASTRUCTURE = "infrastructure"


class IssueSeverity(str, Enum):
    """Issue severity levels."""
    CRITICAL = "critical"  # Must fix, blocks approval
    MAJOR = "major"        # Should fix, counts toward threshold
    MINOR = "minor"        # Nice to fix, doesn't block
    SUGGESTION = "suggestion"  # Optional improvement


class IssueCategory(str, Enum):
    """Issue categories."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    CORRECTNESS = "correctness"
    MAINTAINABILITY = "maintainability"
    STYLE = "style"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"


class ReviewStatus(str, Enum):
    """Review session status."""
    PENDING = "pending"
    REVIEWING = "reviewing"
    SECOND_ROUND = "second_round"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class ReviewDecision(str, Enum):
    """Review decision outcomes."""
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ModelRole(str, Enum):
    """Role of a model in the council."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SPECIALIST = "specialist"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class ParsedIssue:
    """Parsed issue from LLM response."""
    severity: IssueSeverity
    category: IssueCategory
    title: str
    description: str
    suggested_fix: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    code_snippet: Optional[str] = None
    model_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "severity": self.severity.value,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "suggested_fix": self.suggested_fix,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "code_snippet": self.code_snippet,
            "model_name": self.model_name,
        }


@dataclass
class ModelReviewResult:
    """Result from a single model's review."""
    model_name: str
    model_role: ModelRole
    issues: List[ParsedIssue]
    review_text: str
    response_time_ms: int
    status: str = "completed"
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_name": self.model_name,
            "model_role": self.model_role.value,
            "issues": [i.to_dict() for i in self.issues],
            "response_time_ms": self.response_time_ms,
            "status": self.status,
            "error_message": self.error_message,
        }


@dataclass
class ConsolidatedIssue:
    """Issue consolidated from multiple model reviews with consensus."""
    severity: IssueSeverity
    category: IssueCategory
    title: str
    description: str
    suggested_fix: Optional[str]
    line_start: Optional[int]
    line_end: Optional[int]
    code_snippet: Optional[str]
    confirmed_by_models: List[str]
    consensus_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "severity": self.severity.value,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "suggested_fix": self.suggested_fix,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "code_snippet": self.code_snippet,
            "confirmed_by_models": self.confirmed_by_models,
            "consensus_score": self.consensus_score,
        }


@dataclass
class ReviewRoundResult:
    """Result of a single review round."""
    round_number: int
    model_reviews: List[ModelReviewResult]
    consolidated_issues: List[ConsolidatedIssue]
    consensus_level: float
    models_responded: int
    models_total: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "round_number": self.round_number,
            "model_reviews": [r.to_dict() for r in self.model_reviews],
            "consolidated_issues": [i.to_dict() for i in self.consolidated_issues],
            "consensus_level": self.consensus_level,
            "models_responded": self.models_responded,
            "models_total": self.models_total,
        }


@dataclass
class ReviewDecisionRecord:
    """Record of a review decision."""
    decision: ReviewDecision
    round_number: int
    total_issues: int
    critical_issues: int
    major_issues: int
    minor_issues: int
    suggestions: int
    consensus_level: float
    decision_reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision": self.decision.value,
            "round_number": self.round_number,
            "total_issues": self.total_issues,
            "critical_issues": self.critical_issues,
            "major_issues": self.major_issues,
            "minor_issues": self.minor_issues,
            "suggestions": self.suggestions,
            "consensus_level": self.consensus_level,
            "decision_reasoning": self.decision_reasoning,
        }


@dataclass
class ReviewResult:
    """Complete result of a stage review."""
    session_id: str
    stage_type: StageType
    decision: ReviewDecision
    approved: bool
    issues: List[ConsolidatedIssue]
    consensus_level: float
    rounds_completed: int
    improved_artifact: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "stage_type": self.stage_type.value,
            "decision": self.decision.value,
            "approved": self.approved,
            "issues": [i.to_dict() for i in self.issues],
            "consensus_level": self.consensus_level,
            "rounds_completed": self.rounds_completed,
            "improved_artifact": self.improved_artifact,
            "metrics": self.metrics,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ReviewSession:
    """Review session tracking."""
    session_id: str
    stage_type: StageType
    artifact_type: str
    artifact_hash: str
    artifact_content: str
    artifact_metadata: Dict[str, Any]
    status: ReviewStatus
    current_round: int
    max_rounds: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# =============================================================================
# CONFIGURATION TYPES
# =============================================================================


@dataclass
class StageCouncilConfig:
    """Configuration for a stage-specific review council."""

    # Model selection
    primary_models: List[str]
    secondary_models: List[str] = field(default_factory=list)
    specialist_model: Optional[str] = None

    # Review criteria (weighted)
    criteria: Dict[str, float] = field(default_factory=dict)

    # Thresholds
    critical_threshold: int = 0  # Max critical issues allowed
    major_threshold: int = 3     # Max major issues allowed
    consensus_minimum: float = 0.6  # Minimum consensus for approval (60%)

    # Second round settings
    enable_second_round: bool = True
    second_round_model: Optional[str] = None
    max_rounds: int = 2

    # Performance settings
    timeout_per_model_seconds: int = 120
    parallel_execution: bool = True

    # Prompt customization
    system_prompt_template: Optional[str] = None
    review_prompt_template: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "primary_models": self.primary_models,
            "secondary_models": self.secondary_models,
            "specialist_model": self.specialist_model,
            "criteria": self.criteria,
            "critical_threshold": self.critical_threshold,
            "major_threshold": self.major_threshold,
            "consensus_minimum": self.consensus_minimum,
            "enable_second_round": self.enable_second_round,
            "second_round_model": self.second_round_model,
            "max_rounds": self.max_rounds,
            "timeout_per_model_seconds": self.timeout_per_model_seconds,
            "parallel_execution": self.parallel_execution,
        }


# =============================================================================
# METRICS TYPES
# =============================================================================


@dataclass
class ModelPerformance:
    """Performance metrics for a model."""
    model_name: str
    avg_response_time_ms: float
    p95_response_time_ms: float
    timeout_rate: float
    avg_issues_found: float
    consensus_alignment: float
    sessions_participated: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_name": self.model_name,
            "avg_response_time_ms": self.avg_response_time_ms,
            "p95_response_time_ms": self.p95_response_time_ms,
            "timeout_rate": self.timeout_rate,
            "avg_issues_found": self.avg_issues_found,
            "consensus_alignment": self.consensus_alignment,
            "sessions_participated": self.sessions_participated,
        }


@dataclass
class StagePerformance:
    """Performance metrics for a stage."""
    stage_type: str
    avg_duration_ms: float
    approval_rate: float
    avg_issues_per_review: float
    second_round_rate: float
    total_reviews: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stage_type": self.stage_type,
            "avg_duration_ms": self.avg_duration_ms,
            "approval_rate": self.approval_rate,
            "avg_issues_per_review": self.avg_issues_per_review,
            "second_round_rate": self.second_round_rate,
            "total_reviews": self.total_reviews,
        }
