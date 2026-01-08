"""
Deep Extraction Pipeline Schemas - Week 81-87

Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ExtractionTier(str, Enum):
    FREE = "FREE"
    BASIC = "BASIC"
    STANDARD = "STANDARD"
    PROFESSIONAL = "PROFESSIONAL"
    PREMIUM = "PREMIUM"


class ExtractionStatus(str, Enum):
    STARTED = "started"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ItemType(str, Enum):
    EPIC = "epic"
    FEATURE = "feature"
    STORY = "story"
    TASK = "task"


class ConflictType(str, Enum):
    SCOPE = "scope"
    PRIORITY = "priority"
    CLASSIFICATION = "classification"
    EXISTENCE = "existence"
    DUPLICATE = "duplicate"


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class ExtractionStartRequest(BaseModel):
    """Request to start a new extraction."""
    project_id: int
    source_path: str = Field(..., description="Path to codebase to extract from")
    workflow_type: str = Field(default="GREEN_PAPER", description="GREEN_PAPER, BROWN_PAPER, etc.")
    tier: ExtractionTier = Field(default=ExtractionTier.FREE, description="Customer tier selection")


class ExtractionRerunRequest(BaseModel):
    """Request to re-run extraction with upgraded tier."""
    new_tier: ExtractionTier = Field(..., description="New tier to use (must be higher than current)")


class ConflictResolveRequest(BaseModel):
    """Request to resolve a conflict."""
    choice: str = Field(..., description="a, b, c, d, merge, or custom")
    custom_resolution: Optional[Dict[str, Any]] = Field(None, description="Custom resolution if choice is 'custom'")
    reasoning: Optional[str] = Field(None, description="Optional reasoning for the decision")


class ConsensusDecisionRequest(BaseModel):
    """Request to make decision on a consensus item."""
    decision: str = Field(..., description="accept or reject")
    feedback: Optional[str] = Field(None, description="Optional feedback")


class BulkResolveRequest(BaseModel):
    """Request to resolve multiple conflicts/consensus items."""
    decisions: List[Dict[str, Any]] = Field(..., description="List of {item_id, decision, ...}")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class TierInfo(BaseModel):
    """Tier configuration information."""
    tier: ExtractionTier
    price_usd: float
    confidence_target: float
    llm_count: int
    human_review: bool
    llms: List[str]


class ExtractionSessionResponse(BaseModel):
    """Response for extraction session."""
    id: UUID
    project_id: Optional[int]
    workflow_type: str
    status: ExtractionStatus
    current_cycle: int

    # Tier info
    tier: ExtractionTier
    tier_price_usd: Optional[float]
    tier_confidence_target: Optional[float]

    # Input
    source_path: Optional[str]
    total_files: Optional[int]
    total_lines: Optional[int]

    # Progress
    cycle_progress: Dict[str, Optional[datetime]] = Field(default_factory=dict)

    # Results
    total_epics: int = 0
    total_features: int = 0
    total_stories: int = 0
    total_tasks: int = 0
    total_function_points: Optional[float]

    # Confidence
    avg_confidence: Optional[float]
    items_auto_accepted: int = 0
    items_human_reviewed: int = 0

    # Cost
    actual_cost_usd: Optional[float]
    margin_usd: Optional[float]

    created_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ExtractionRunResponse(BaseModel):
    """Response for extraction run."""
    id: UUID
    session_id: UUID
    run_number: int
    tier: ExtractionTier
    tier_price_usd: Optional[float]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    # Delta from previous
    delta_epics: int = 0
    delta_features: int = 0
    delta_stories: int = 0
    delta_tasks: int = 0
    confidence_improvement: float = 0.0

    # Cost
    actual_cost_usd: Optional[float]
    tokens_used: int = 0
    credit_from_previous: float = 0.0
    amount_charged: Optional[float]

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LLMResultResponse(BaseModel):
    """Response for LLM result."""
    id: UUID
    session_id: UUID
    cycle: int
    llm_provider: str
    llm_model: str
    analysis_type: Optional[str]

    # Extracted counts
    epic_count: int = Field(default=0)
    feature_count: int = Field(default=0)
    story_count: int = Field(default=0)
    task_count: int = Field(default=0)

    # Metrics
    tokens_input: Optional[int]
    tokens_output: Optional[int]
    latency_ms: Optional[int]
    cost_usd: Optional[float]

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsensusItemResponse(BaseModel):
    """Response for consensus item."""
    id: UUID
    session_id: UUID
    item_type: ItemType
    item_title: str
    item_description: Optional[str]

    supporting_llms: Optional[List[str]]
    confidence_score: float
    confidence_breakdown: Optional[Dict[str, float]]

    status: str
    human_decision: Optional[str]
    human_feedback: Optional[str]
    decided_at: Optional[datetime]
    decided_by: Optional[str]

    # Item data for creation
    item_data: Optional[Dict[str, Any]]

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConflictResponse(BaseModel):
    """Response for conflict."""
    id: UUID
    session_id: UUID
    conflict_type: ConflictType
    item_type: ItemType

    # Options
    option_a: Optional[Dict[str, Any]]
    option_b: Optional[Dict[str, Any]]
    option_c: Optional[Dict[str, Any]]
    option_d: Optional[Dict[str, Any]]

    # LLM recommendation
    llm_recommendation: Optional[str]
    recommendation_reasoning: Optional[str]

    # Human resolution
    status: str
    human_choice: Optional[str]
    human_custom: Optional[Dict[str, Any]]
    human_reasoning: Optional[str]
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExtractionProgressResponse(BaseModel):
    """Response for extraction progress."""
    session_id: UUID
    status: ExtractionStatus
    current_cycle: int
    tier: ExtractionTier

    # Cycle completion status
    cycles: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "cycle_1": {"name": "Independent Analysis", "status": "pending", "completed_at": None},
            "cycle_2": {"name": "Cross-Enrichment", "status": "pending", "completed_at": None},
            "cycle_3": {"name": "Conflict Detection", "status": "pending", "completed_at": None},
            "cycle_4": {"name": "Human Decision", "status": "pending", "completed_at": None},
            "cycle_5": {"name": "Final Synthesis", "status": "pending", "completed_at": None},
        }
    )

    # Current stats
    items_found: int = 0
    items_auto_accepted: int = 0
    items_pending_review: int = 0
    conflicts_pending: int = 0
    avg_confidence: Optional[float]

    # Cost so far
    cost_so_far: float = 0.0
    estimated_total_cost: Optional[float]


class ExtractionDeltaResponse(BaseModel):
    """Response for delta between runs."""
    current_run_id: UUID
    previous_run_id: Optional[UUID]
    tier_upgrade: str  # e.g., "FREE -> STANDARD"

    # Delta counts
    new_epics: int = 0
    new_features: int = 0
    new_stories: int = 0
    new_tasks: int = 0

    # Items that were reclassified
    reclassified_items: List[Dict[str, Any]] = Field(default_factory=list)

    # Confidence change
    confidence_before: Optional[float]
    confidence_after: float
    confidence_improvement: float

    # Cost
    amount_charged: float
    credit_applied: float


class ExtractionResultResponse(BaseModel):
    """Final extraction result with full hierarchy."""
    session_id: UUID
    tier: ExtractionTier
    confidence: float

    # Hierarchy
    epics: List[Dict[str, Any]]
    features: List[Dict[str, Any]]
    stories: List[Dict[str, Any]]
    tasks: List[Dict[str, Any]]

    # Function points
    total_function_points: float
    fp_by_epic: Dict[str, float]
    fp_by_complexity: Dict[str, float]

    # Recommendations
    recommended_team_size: int
    estimated_duration_weeks: int

    # Risks
    risks: List[Dict[str, Any]]


# ============================================================================
# LIST/SUMMARY SCHEMAS
# ============================================================================

class ExtractionSessionSummary(BaseModel):
    """Summary for listing sessions."""
    id: UUID
    project_id: Optional[int]
    workflow_type: str
    tier: ExtractionTier
    status: ExtractionStatus
    total_items: int
    avg_confidence: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]


class TierComparisonResponse(BaseModel):
    """Compare all tiers for onboarding."""
    tiers: List[TierInfo]
    recommended: ExtractionTier = ExtractionTier.STANDARD
    estimated_loc: Optional[int]
    estimated_costs: Dict[str, float]  # tier -> cost


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics."""
    total_sessions: int
    sessions_by_status: Dict[str, int]
    sessions_by_tier: Dict[str, int]
    avg_confidence_by_tier: Dict[str, float]
    total_items_extracted: int
    total_cost_usd: float
    total_revenue_usd: float
    margin_percentage: float
