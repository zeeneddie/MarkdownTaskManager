"""
Deep Extraction Pipeline Models - Week 81-87

Multi-LLM code analysis with 5 customer tiers (FREE to PREMIUM).
Supports re-run capability for tier upgrades with delta tracking.

Tables:
- ExtractionSession: Main extraction session with tier configuration
- ExtractionRun: Individual extraction runs (for re-run/upgrade flow)
- ExtractionLLMResult: Per-cycle, per-LLM analysis results
- ExtractionEnrichment: Cross-enrichment between LLMs (Cycle 2)
- ExtractionConsensus: Items with consensus scores
- ExtractionConflict: Conflicts requiring human decision
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum

from app.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class ExtractionTier(str, Enum):
    """
    Customer extraction tiers with different LLM configurations and pricing.

    Week 99 Update:
    - FREE tier DEPRECATED - all tiers now include static analysis (Cycle 0)
    - Pricing in EUR per 50K LOC
    - All tiers include full static analysis foundation (80% coverage baseline)
    """
    FREE = "FREE"              # DEPRECATED Week 99 - Use BASIC instead
    BASIC = "BASIC"            # €5, 70% confidence, 3 LLMs + Static Analysis
    STANDARD = "STANDARD"      # €25, 80% confidence, 5 LLMs + Static Analysis
    PROFESSIONAL = "PROFESSIONAL"  # €75, 90% confidence, 7 LLMs + Human Review
    PREMIUM = "PREMIUM"        # €150, 95% confidence, 10 LLMs + Human Review


class ExtractionStatus(str, Enum):
    """Extraction session status."""
    STARTED = "started"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_review"  # Cycle 4 - waiting for human decisions
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunStatus(str, Enum):
    """Individual extraction run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ConsensusStatus(str, Enum):
    """Consensus item status."""
    PENDING = "pending"
    AUTO_ACCEPTED = "auto_accepted"   # Confidence >= 80%
    HUMAN_REVIEW = "human_review"     # Confidence < 80% or conflict
    ACCEPTED = "accepted"             # Human accepted
    REJECTED = "rejected"             # Human rejected


class ConflictType(str, Enum):
    """Types of conflicts between LLM outputs."""
    SCOPE = "scope"              # Disagreement on scope/size
    PRIORITY = "priority"        # Disagreement on priority
    CLASSIFICATION = "classification"  # Different item type (epic vs feature)
    EXISTENCE = "existence"      # Should this item exist?
    DUPLICATE = "duplicate"      # Potential duplicate detection


class ConflictStatus(str, Enum):
    """Conflict resolution status."""
    PENDING = "pending"
    RESOLVED = "resolved"
    SKIPPED = "skipped"


class ItemType(str, Enum):
    """Extracted item types."""
    EPIC = "epic"
    FEATURE = "feature"
    STORY = "story"
    TASK = "task"


class AnalysisType(str, Enum):
    """LLM analysis specialization types (Cycle 1)."""
    ARCHITECTURE = "architecture"      # Qwen-Coder
    BUSINESS_LOGIC = "business_logic"  # DeepSeek-R1
    SECURITY = "security"              # CodeLlama
    CODE_STRUCTURE = "code_structure"  # Codex-CLI


# ============================================================================
# TIER CONFIGURATION - Week 117 Updated (Logarithmic Pricing)
# ============================================================================
# Week 117: Refactored to logarithmic pricing with 3x multiplier per tier:
#   BASIC: €5 (base) → STANDARD: €15 (3x) → PROFESSIONAL: €45 (3x) → PREMIUM: €135 (3x)
# Previous degressive pricing: €5 → €25 (5x) → €75 (3x) → €150 (2x)

TIER_PRICE_MULTIPLIER = 3.0  # Logarithmic scale multiplier

TIER_CONFIG = {
    # FREE tier DEPRECATED in Week 99 - kept for backwards compatibility but will warn
    ExtractionTier.FREE: {
        "price_eur": 0.0,
        "price_usd": 0.0,  # Legacy field
        "confidence_target": 0.60,
        "llm_count": 3,
        "human_review": False,
        "static_analysis": False,  # No static analysis in FREE tier
        "deprecated": True,  # Week 99: FREE tier deprecated
        "deprecation_message": "FREE tier removed in Week 99. Please use BASIC tier (€5) which includes static analysis.",
        "llms": ["ollama/qwen2.5-coder:7b", "ollama/deepseek-r1", "ollama/codellama"],
    },
    ExtractionTier.BASIC: {
        "price_eur": 5.0,       # Base price
        "price_usd": 5.0,       # Legacy field
        "confidence_target": 0.70,
        "llm_count": 3,         # 3 Ollama LLMs
        "human_review": False,
        "static_analysis": True,  # Week 99: Full Cycle 0
        "llms": ["ollama/qwen2.5-coder:7b", "ollama/deepseek-r1", "ollama/codellama"],
    },
    ExtractionTier.STANDARD: {
        "price_eur": 15.0,      # Week 117: €15 (3x BASIC) - was €25
        "price_usd": 15.0,      # Legacy field
        "confidence_target": 0.80,
        "llm_count": 5,         # +Groq, Qwen
        "human_review": False,  # Optional
        "static_analysis": True,  # Week 99: Full Cycle 0
        "llms": ["ollama/qwen2.5-coder:7b", "ollama/deepseek-r1", "ollama/codellama",
                 "groq/llama-3.1-8b", "alibaba/qwen-turbo"],
    },
    ExtractionTier.PROFESSIONAL: {
        "price_eur": 45.0,      # Week 117: €45 (3x STANDARD) - was €75
        "price_usd": 45.0,      # Legacy field
        "confidence_target": 0.90,
        "llm_count": 7,         # +Gemini
        "human_review": True,   # Included
        "static_analysis": True,  # Week 99: Full Cycle 0
        "llms": ["ollama/qwen2.5-coder:7b", "ollama/deepseek-r1", "ollama/codellama",
                 "groq/llama-3.1-8b", "alibaba/qwen-turbo",
                 "google/gemini-2.0-flash-lite", "google/gemini-2.5-flash"],
    },
    ExtractionTier.PREMIUM: {
        "price_eur": 135.0,     # Week 117: €135 (3x PROFESSIONAL) - was €150
        "price_usd": 135.0,     # Legacy field
        "confidence_target": 0.95,
        "llm_count": 10,        # Full stack: all providers
        "human_review": True,   # Included
        "static_analysis": True,  # Week 99: Full Cycle 0
        "llms": ["ollama/qwen2.5-coder:7b", "ollama/deepseek-r1", "ollama/codellama",
                 "groq/llama-3.1-8b", "alibaba/qwen-turbo",
                 "google/gemini-2.0-flash-lite", "google/gemini-2.5-flash",
                 "google/gemini-2.5-pro", "openai/gpt-5.2",
                 "anthropic/claude-opus-4.5"],
    },
}

# Helper to check if tier includes static analysis (Week 99)
def tier_includes_static_analysis(tier: ExtractionTier) -> bool:
    """Check if tier includes static analysis (Cycle 0)."""
    return TIER_CONFIG.get(tier, {}).get("static_analysis", False)

# Helper to check if tier is deprecated (Week 99)
def is_tier_deprecated(tier: ExtractionTier) -> bool:
    """Check if tier is deprecated."""
    return TIER_CONFIG.get(tier, {}).get("deprecated", False)


# ============================================================================
# MODELS
# ============================================================================

class ExtractionSession(Base):
    """
    Main extraction session tracking tier, cycles, and results.

    A session represents a complete extraction pipeline run for a project.
    Each session can have multiple runs (for tier upgrades/re-runs).
    """
    __tablename__ = "extraction_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=True, index=True)
    workflow_type = Column(String(30), nullable=False)  # GREEN_PAPER, BROWN_PAPER, etc.
    status = Column(String(20), default=ExtractionStatus.STARTED.value, index=True)
    current_cycle = Column(Integer, default=1)  # 1-5

    # TIER CONFIGURATION
    tier = Column(String(20), nullable=False, default=ExtractionTier.FREE.value)
    tier_price_usd = Column(Float, nullable=True)
    tier_cost_estimate = Column(Float, nullable=True)
    tier_confidence_target = Column(Float, nullable=True)

    # TIER OVERRIDE SETTINGS (Week 87) - Granular tier selection
    allow_epic_override = Column(String(1), default='Y')  # Y/N
    allow_feature_override = Column(String(1), default='Y')  # Y/N
    allow_story_override = Column(String(1), default='Y')  # Y/N
    tier_config_locked = Column(String(1), default='N')  # Y/N - lock all tier changes

    # Input
    source_path = Column(String(500), nullable=True)
    total_files = Column(Integer, nullable=True)
    total_lines = Column(Integer, nullable=True)

    # Progress timestamps (Cycle 0-5, Week 100 added Cycle 0)
    cycle_0_completed_at = Column(DateTime, nullable=True)  # Week 100: Static Analysis
    cycle_1_completed_at = Column(DateTime, nullable=True)
    cycle_2_completed_at = Column(DateTime, nullable=True)
    cycle_3_completed_at = Column(DateTime, nullable=True)
    cycle_4_completed_at = Column(DateTime, nullable=True)
    cycle_5_completed_at = Column(DateTime, nullable=True)

    # Week 100: Static Analysis (Cycle 0) metrics
    static_analysis_id = Column(String(100), nullable=True)
    static_domain_coverage = Column(Float, nullable=True)
    static_nfr_coverage = Column(Float, nullable=True)
    static_compliance_score = Column(Float, nullable=True)
    static_business_rules_count = Column(Integer, default=0)
    static_nfr_count = Column(Integer, default=0)
    static_compliance_violations_count = Column(Integer, default=0)
    static_high_confidence_count = Column(Integer, default=0)
    static_low_confidence_count = Column(Integer, default=0)

    # Week 100: Conflict tracking summary
    total_conflicts = Column(Integer, default=0)
    conflicts_auto_resolved = Column(Integer, default=0)
    conflicts_pending_review = Column(Integer, default=0)
    conflicts_human_resolved = Column(Integer, default=0)

    # Results
    total_epics = Column(Integer, default=0)
    total_features = Column(Integer, default=0)
    total_stories = Column(Integer, default=0)
    total_tasks = Column(Integer, default=0)
    total_function_points = Column(Float, nullable=True)

    # Confidence tracking
    avg_confidence = Column(Float, nullable=True)
    items_auto_accepted = Column(Integer, default=0)
    items_human_reviewed = Column(Integer, default=0)

    # Cost tracking
    total_tokens_used = Column(Integer, default=0)
    actual_cost_usd = Column(Float, nullable=True)
    margin_usd = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    runs = relationship("ExtractionRun", back_populates="session", cascade="all, delete-orphan")
    llm_results = relationship("ExtractionLLMResult", back_populates="session", cascade="all, delete-orphan")
    enrichments = relationship("ExtractionEnrichment", back_populates="session", cascade="all, delete-orphan")
    consensus_items = relationship("ExtractionConsensus", back_populates="session", cascade="all, delete-orphan")
    conflicts = relationship("ExtractionConflict", back_populates="session", cascade="all, delete-orphan")
    static_llm_conflicts = relationship("StaticLLMConflict", back_populates="session", cascade="all, delete-orphan")  # Week 100

    def __repr__(self):
        return f"<ExtractionSession(id={self.id}, tier={self.tier}, status={self.status}, cycle={self.current_cycle})>"

    def get_tier_config(self):
        """Get configuration for current tier."""
        return TIER_CONFIG.get(ExtractionTier(self.tier), TIER_CONFIG[ExtractionTier.FREE])


class ExtractionRun(Base):
    """
    Individual extraction run within a session.

    Supports re-run capability: when a user upgrades their tier,
    a new run is created with delta tracking from the previous run.
    """
    __tablename__ = "extraction_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey('extraction_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    run_number = Column(Integer, default=1)

    # Tier for this run
    tier = Column(String(20), nullable=False)
    tier_price_usd = Column(Float, nullable=True)

    # Status
    status = Column(String(20), default=RunStatus.PENDING.value)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Link to previous run (for delta calculation)
    previous_run_id = Column(UUID(as_uuid=True), ForeignKey('extraction_runs.id'), nullable=True)

    # Delta from previous run
    delta_epics = Column(Integer, default=0)
    delta_features = Column(Integer, default=0)
    delta_stories = Column(Integer, default=0)
    delta_tasks = Column(Integer, default=0)
    confidence_improvement = Column(Float, default=0.0)

    # Cost
    actual_cost_usd = Column(Float, nullable=True)
    tokens_used = Column(Integer, default=0)

    # Credit applied (if upgrade from previous tier)
    credit_from_previous = Column(Float, default=0.0)
    amount_charged = Column(Float, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    # Relationships
    session = relationship("ExtractionSession", back_populates="runs")
    previous_run = relationship("ExtractionRun", remote_side=[id], foreign_keys=[previous_run_id])
    llm_results = relationship("ExtractionLLMResult", back_populates="run")

    def __repr__(self):
        return f"<ExtractionRun(id={self.id}, run_number={self.run_number}, tier={self.tier}, status={self.status})>"


class ExtractionLLMResult(Base):
    """
    Per-cycle, per-LLM analysis results.

    Stores the raw and parsed output from each LLM in each cycle,
    along with extracted items and cost metrics.
    """
    __tablename__ = "extraction_llm_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('extraction_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    run_id = Column(UUID(as_uuid=True), ForeignKey('extraction_runs.id', ondelete='CASCADE'), nullable=True, index=True)
    cycle = Column(Integer, nullable=False)  # 1-5

    # LLM identification
    llm_provider = Column(String(50), nullable=False)  # ollama, anthropic, openai, google, groq, alibaba, moonshot
    llm_model = Column(String(100), nullable=False)  # qwen2.5-coder:7b, gpt-5.2, etc.

    # Analysis type (Cycle 1)
    analysis_type = Column(String(50), nullable=True)  # architecture, business_logic, security, code_structure

    # Raw output
    raw_output = Column(Text, nullable=True)
    parsed_output = Column(JSONB, nullable=True)

    # Extracted items
    extracted_epics = Column(JSONB, default=[])
    extracted_features = Column(JSONB, default=[])
    extracted_stories = Column(JSONB, default=[])
    extracted_tasks = Column(JSONB, default=[])

    # Metrics
    tokens_input = Column(Integer, nullable=True)
    tokens_output = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    # Relationships
    session = relationship("ExtractionSession", back_populates="llm_results")
    run = relationship("ExtractionRun", back_populates="llm_results")
    enrichments_received = relationship("ExtractionEnrichment", back_populates="source_result", foreign_keys="ExtractionEnrichment.source_result_id")

    def __repr__(self):
        return f"<ExtractionLLMResult(id={self.id}, cycle={self.cycle}, provider={self.llm_provider}, model={self.llm_model})>"


class ExtractionEnrichment(Base):
    """
    Cross-enrichment results from Cycle 2.

    Each LLM reviews another's output and suggests additions/modifications.
    """
    __tablename__ = "extraction_enrichments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('extraction_sessions.id', ondelete='CASCADE'), nullable=False, index=True)

    # Source and reviewer
    source_result_id = Column(UUID(as_uuid=True), ForeignKey('extraction_llm_results.id', ondelete='CASCADE'), nullable=False)
    reviewer_llm = Column(String(100), nullable=False)

    # Enrichment
    additions = Column(JSONB, default=[])  # New items found
    modifications = Column(JSONB, default=[])  # Suggested changes
    confidence_adjustments = Column(JSONB, nullable=True)  # Per-item confidence changes

    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    # Relationships
    session = relationship("ExtractionSession", back_populates="enrichments")
    source_result = relationship("ExtractionLLMResult", back_populates="enrichments_received", foreign_keys=[source_result_id])

    def __repr__(self):
        return f"<ExtractionEnrichment(id={self.id}, reviewer={self.reviewer_llm})>"


class ExtractionConsensus(Base):
    """
    Items with consensus scores from Cycle 3.

    Items with confidence >= 80% are auto-accepted.
    Items with lower confidence go to human review (Cycle 4).

    Week 87: Added tier override support for granular tier selection
    at epic, feature, and story level.
    """
    __tablename__ = "extraction_consensus"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('extraction_sessions.id', ondelete='CASCADE'), nullable=False, index=True)

    # Item identification
    item_type = Column(String(20), nullable=False)  # epic, feature, story, task
    item_title = Column(String(300), nullable=False)
    item_description = Column(Text, nullable=True)

    # Hierarchy references (for tier inheritance)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('extraction_consensus.id'), nullable=True, index=True)
    hierarchy_path = Column(String(500), nullable=True)  # e.g., "EPIC-001/FEAT-002/STORY-003"

    # Consensus data
    supporting_llms = Column(JSONB, nullable=True)  # Which LLMs agree
    confidence_score = Column(Float, nullable=False)  # 0.0-1.0
    confidence_breakdown = Column(JSONB, nullable=True)  # Per-factor scores

    # TIER OVERRIDE (Week 87) - Granular tier selection
    tier_override = Column(String(20), nullable=True)  # None = inherit from parent/session
    tier_effective = Column(String(20), nullable=True)  # Calculated: override or inherited
    tier_locked = Column(String(1), default='N')  # Y/N - prevents child override changes

    # EXPECTED OUTCOMES (Week 87) - Per-item predictions
    expected_confidence = Column(Float, nullable=True)  # Predicted confidence for this tier
    expected_cost_usd = Column(Float, nullable=True)  # Predicted extraction cost
    expected_llm_count = Column(Integer, nullable=True)  # Number of LLMs for this tier

    # Function Point estimation
    estimated_fp = Column(Float, nullable=True)  # IFPUG function points
    fp_breakdown = Column(JSONB, nullable=True)  # {ilf, eif, ei, eo, eq}

    # Confidence explanation (Week 86)
    confidence_explanation = Column(Text, nullable=True)  # Why confidence is X%

    # Status
    status = Column(String(20), default=ConsensusStatus.PENDING.value, index=True)
    human_decision = Column(String(20), nullable=True)
    human_feedback = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(String(100), nullable=True)

    # Final item reference (after acceptance)
    final_epic_id = Column(UUID(as_uuid=True), ForeignKey('task_epics.id'), nullable=True)
    final_feature_id = Column(UUID(as_uuid=True), ForeignKey('task_features.id'), nullable=True)
    final_story_id = Column(UUID(as_uuid=True), ForeignKey('task_stories.id'), nullable=True)
    final_task_id = Column(UUID(as_uuid=True), ForeignKey('task_tasks.id'), nullable=True)

    # Additional data for item creation
    item_data = Column(JSONB, nullable=True)  # Full extracted data

    # Week 100: Static Analysis linkage
    source_conflict_id = Column(UUID(as_uuid=True), ForeignKey('static_llm_conflicts.id', ondelete='SET NULL'), nullable=True)
    from_static_analysis = Column(String(1), default='N')  # Y/N - indicates item originated from static analysis

    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    # Self-referential relationship for hierarchy
    children = relationship("ExtractionConsensus", backref="parent", remote_side=[id], foreign_keys=[parent_id])

    # Relationships
    session = relationship("ExtractionSession", back_populates="consensus_items")

    def __repr__(self):
        return f"<ExtractionConsensus(id={self.id}, type={self.item_type}, confidence={self.confidence_score:.2f}, status={self.status})>"


class ExtractionConflict(Base):
    """
    Conflicts requiring human decision (Cycle 4).

    When LLMs disagree significantly, the conflict is surfaced
    for human resolution with all options presented.
    """
    __tablename__ = "extraction_conflicts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('extraction_sessions.id', ondelete='CASCADE'), nullable=False, index=True)

    # Conflict identification
    conflict_type = Column(String(50), nullable=False)  # scope, priority, classification, existence, duplicate
    item_type = Column(String(20), nullable=False)  # epic, feature, story, task

    # Competing interpretations (up to 4 LLM views)
    option_a = Column(JSONB, nullable=True)
    option_b = Column(JSONB, nullable=True)
    option_c = Column(JSONB, nullable=True)
    option_d = Column(JSONB, nullable=True)

    # LLM recommendations
    llm_recommendation = Column(String(20), nullable=True)  # a, b, c, d, merge
    recommendation_reasoning = Column(Text, nullable=True)

    # Human resolution
    status = Column(String(20), default=ConflictStatus.PENDING.value, index=True)
    human_choice = Column(String(20), nullable=True)  # a, b, c, d, merge, custom
    human_custom = Column(JSONB, nullable=True)  # Custom resolution
    human_reasoning = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    # Relationships
    session = relationship("ExtractionSession", back_populates="conflicts")

    def __repr__(self):
        return f"<ExtractionConflict(id={self.id}, type={self.conflict_type}, status={self.status})>"


# ============================================================================
# WEEK 100 - STATIC-LLM CONFLICT TRACKING
# ============================================================================

class StaticLLMConflictType(str, Enum):
    """Types of conflicts between Static Analysis and LLM results (Week 100)."""
    CONFIDENCE_THRESHOLD = "confidence_threshold"  # LLM confidence < 72.5%
    EXPLICIT_DISAGREEMENT = "explicit_disagreement"  # Static & LLM disagree
    CLASSIFICATION_CHANGE = "classification_change"  # Type changed
    ITEM_REMOVAL = "item_removal"  # LLM removes static item
    PRIORITY_MISMATCH = "priority_mismatch"  # Different priorities
    SCOPE_EXPANSION = "scope_expansion"  # LLM significantly expands scope
    SCOPE_REDUCTION = "scope_reduction"  # LLM significantly reduces scope


class StaticLLMConflictSeverity(str, Enum):
    """Severity levels for Static-LLM conflicts (Week 100)."""
    LOW = "low"  # Auto-resolvable
    MEDIUM = "medium"  # Needs review but not blocking
    HIGH = "high"  # Blocking, requires human decision
    CRITICAL = "critical"  # Data integrity issue


class StaticLLMConflictStatus(str, Enum):
    """Status of Static-LLM conflict resolution (Week 100)."""
    PENDING = "pending"
    AUTO_RESOLVED = "auto_resolved"
    HUMAN_REVIEW = "human_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class StaticLLMConflictResolution(str, Enum):
    """How a Static-LLM conflict was resolved (Week 100)."""
    AUTO_ACCEPTED_STATIC = "auto_accepted_static"
    AUTO_ACCEPTED_LLM = "auto_accepted_llm"
    HUMAN_SELECTED_STATIC = "human_selected_static"
    HUMAN_SELECTED_LLM = "human_selected_llm"
    HUMAN_MERGED = "human_merged"
    HUMAN_REJECTED_BOTH = "human_rejected_both"


class StaticLLMConflict(Base):
    """
    Week 100 - Conflicts between Static Analysis (Cycle 0) and LLM results.

    Tracks conflicts detected when comparing deterministic static analysis
    findings with LLM extraction results. Uses 72.5% confidence threshold.

    Key threshold: 72.5%
    - Below threshold: LLM result needs human review
    - Static analysis provides baseline for comparison
    """
    __tablename__ = "static_llm_conflicts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('extraction_sessions.id', ondelete='CASCADE'), nullable=False, index=True)

    # Item identification
    item_id = Column(String(100), nullable=False, index=True)
    item_type = Column(String(50), nullable=True)  # business_rule, nfr, compliance, etc.

    # Conflict classification
    conflict_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, default=StaticLLMConflictSeverity.MEDIUM.value)

    # Static Analysis side
    static_classification = Column(String(100), nullable=True)
    static_confidence = Column(Float, nullable=True)
    static_data = Column(JSONB, nullable=True)
    static_source_file = Column(String(500), nullable=True)
    static_source_line = Column(Integer, nullable=True)

    # LLM Analysis side
    llm_classification = Column(String(100), nullable=True)
    llm_confidence = Column(Float, nullable=True)
    llm_data = Column(JSONB, nullable=True)
    llm_provider = Column(String(100), nullable=True)
    llm_model = Column(String(100), nullable=True)

    # Conflict details
    description = Column(Text, nullable=True)
    impact_assessment = Column(Text, nullable=True)
    recommendations = Column(JSONB, nullable=True)  # List of recommendations

    # Resolution
    status = Column(String(20), nullable=False, default=StaticLLMConflictStatus.PENDING.value, index=True)
    resolution = Column(String(50), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)  # "system" or user_id
    resolution_notes = Column(Text, nullable=True)

    # Final value (merged or selected)
    final_value = Column(JSONB, nullable=True)
    final_classification = Column(String(100), nullable=True)
    final_confidence = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    # Relationships
    session = relationship("ExtractionSession", back_populates="static_llm_conflicts")
    resolution_history = relationship("ConflictResolutionHistory", back_populates="conflict", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StaticLLMConflict(id={self.id}, type={self.conflict_type}, severity={self.severity}, status={self.status})>"


class ConflictResolutionHistory(Base):
    """
    Week 100 - Audit trail for conflict resolution actions.

    Tracks all actions taken on Static-LLM conflicts for compliance
    and debugging purposes.
    """
    __tablename__ = "conflict_resolution_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conflict_id = Column(UUID(as_uuid=True), ForeignKey('static_llm_conflicts.id', ondelete='CASCADE'), nullable=False, index=True)

    # Action details
    action = Column(String(50), nullable=False)  # created, viewed, assigned, resolved, reopened, escalated
    action_by = Column(String(100), nullable=False)  # "system" or user_id
    action_data = Column(JSONB, nullable=True)  # Additional action context

    # Before/after state
    previous_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=True)
    previous_resolution = Column(String(50), nullable=True)
    new_resolution = Column(String(50), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    # Relationships
    conflict = relationship("StaticLLMConflict", back_populates="resolution_history")

    def __repr__(self):
        return f"<ConflictResolutionHistory(id={self.id}, action={self.action}, by={self.action_by})>"
