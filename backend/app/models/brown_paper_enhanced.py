"""
Brown Paper Enhanced Models - Fase 20 (Week 128-129)

6-Phase deep analysis workflow models for legacy/migration projects.
INTEGRATION: Uses existing types from services, only adds orchestration types.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from enum import Enum

# Import existing types from services (re-export for convenience)
if TYPE_CHECKING:
    from app.services.dependency_graph_service import DependencyGraphResult
    from app.services.code_analysis_aggregator_service import AggregatedAnalysis
    from app.services.hierarchical_story_extraction_service import HierarchicalExtractionResult


class EnhancedAnalysisTier(str, Enum):
    """Extraction tier determines which phases and LLMs are used."""
    FREE = "FREE"           # Phase 1 only (Ollama)
    BASIC = "BASIC"         # Phase 1-2 (+ Groq, Qwen)
    STANDARD = "STANDARD"   # Phase 1-3 (+ Gemini)
    PROFESSIONAL = "PROFESSIONAL"  # Phase 1-5 (+ GPT-5.2)
    PREMIUM = "PREMIUM"     # Phase 1-6 (+ Opus, Human Review)


class EnhancedAnalysisPhase(str, Enum):
    """The 6 phases of enhanced analysis."""
    CODE_UNDERSTANDING = "code_understanding"       # Phase 1
    DOMAIN_EXTRACTION = "domain_extraction"         # Phase 2
    HIERARCHICAL_EXTRACTION = "hierarchical_extraction"  # Phase 3
    DEEP_EXTRACTION = "deep_extraction"             # Phase 4
    ESTIMATION = "estimation"                       # Phase 5
    OUTPUT = "output"                               # Phase 6


@dataclass
class EnhancedAnalysisOptions:
    """Configuration options for enhanced analysis."""
    skip_vbscript: bool = False
    include_cira: bool = True
    generate_tests: bool = True
    include_swot: bool = True
    max_files_per_phase: int = 500
    # Week 159: Business Logic Extraction - PVA Implementation
    use_business_logic_extraction: bool = True  # Use enhanced domain extraction & story generation


@dataclass
class EnhancedAnalysisRequest:
    """Request to start enhanced analysis."""
    tier: EnhancedAnalysisTier = EnhancedAnalysisTier.STANDARD
    include_phases: List[int] = field(default_factory=lambda: [1, 2, 3, 4, 5, 6])
    options: EnhancedAnalysisOptions = field(default_factory=EnhancedAnalysisOptions)


# Phase 1: Code Understanding - USES EXISTING TYPES
# - DependencyGraphResult from dependency_graph_service
# - AggregatedAnalysis from code_analysis_aggregator_service
# - LayeredAnalysisService returns dict

@dataclass
class Phase1Result:
    """Phase 1: Combined code understanding results using existing service types."""
    dependency_graph: Optional[Dict[str, Any]] = None  # DependencyGraphResult.to_dict()
    code_analysis: Optional[Dict[str, Any]] = None     # AggregatedAnalysis.to_dict()
    layered_analysis: Optional[Dict[str, Any]] = None  # LayeredAnalysisService result
    foundation: Optional[Dict[str, Any]] = None        # FoundationDetectionResult.to_dict()
    # Week 131 additions
    background_jobs: Optional[Dict[str, Any]] = None   # BackgroundJobDetectionResult.to_dict()
    load_estimation: Optional[Dict[str, Any]] = None   # LoadEstimationResult.to_dict()
    # Week 132-133 additions (Fase 22: Dead Code & Runtime Analysis)
    dead_code_analysis: Optional[Dict[str, Any]] = None   # DeadCodeAnalysisResult.to_dict()
    runtime_analysis: Optional[Dict[str, Any]] = None     # RuntimeAnalysisResult.to_dict()
    coverage_analysis: Optional[Dict[str, Any]] = None    # CodeCoverageResult.to_dict()
    # Week 136-137 additions (Fase 24: Data Architecture)
    data_lineage_result: Optional[Dict[str, Any]] = None  # DataLineageResult.to_dict()
    erd_generation_result: Optional[Dict[str, Any]] = None  # ERDGeneratorResult.to_dict()
    # Week 144 additions: SIG Top 10 Quality Metrics
    sig_metrics: Optional[Dict[str, Any]] = None  # SIG Top 10 ratings + findings
    duration_ms: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)


# Phase 2: Domain Extraction - Peter agent extracts domains
@dataclass
class Phase2Result:
    """Phase 2: Domain extraction results."""
    domains: List[Dict[str, Any]] = field(default_factory=list)
    module_boundaries: Dict[str, List[str]] = field(default_factory=dict)
    business_rules_count: int = 0
    cafcr_mapping: Dict[str, List[str]] = field(default_factory=dict)
    duration_ms: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)


# Phase 3: Hierarchical Extraction - USES HierarchicalExtractionResult
@dataclass
class Phase3Result:
    """Phase 3: Hierarchical extraction - wraps HierarchicalExtractionResult."""
    extraction_result: Optional[Dict[str, Any]] = None  # HierarchicalExtractionResult
    causal_relations: List[Dict[str, Any]] = field(default_factory=list)
    duration_ms: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)


# Phase 4: Deep Extraction - USES DeepExtractionService
@dataclass
class Phase4Result:
    """Phase 4: Deep extraction with LLM Council."""
    deep_extraction_result: Optional[Dict[str, Any]] = None  # DeepExtractionService result
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    consensus_confidence: float = 0.0
    human_review_needed: int = 0
    duration_ms: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)


# Phase 5: Estimation - USES brown_paper_estimation_service
@dataclass
class Phase5Result:
    """Phase 5: Enhanced estimation results."""
    estimation_result: Optional[Dict[str, Any]] = None  # brown_paper_estimation_service result
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    complexity_multiplier: float = 1.0
    duration_ms: int = 0
    success: bool = True
    errors: List[str] = field(default_factory=list)


# Phase 6: Output consolidation
@dataclass
class EnhancedAnalysisSummary:
    """Summary statistics for enhanced analysis."""
    epics: int = 0
    features: int = 0
    stories: int = 0
    tasks: int = 0
    total_fp: int = 0
    total_sp: int = 0
    estimated_hours: float = 0.0
    confidence: float = 0.0


@dataclass
class EnhancedAnalysisResponse:
    """Phase 6: Complete enhanced analysis response."""
    session_id: str
    status: str  # completed, partial, failed
    tier: EnhancedAnalysisTier
    phases_completed: List[int] = field(default_factory=list)
    confidence: float = 0.0
    summary: EnhancedAnalysisSummary = field(default_factory=EnhancedAnalysisSummary)

    # Phase results (using dicts from existing services)
    phase1_result: Optional[Phase1Result] = None
    phase2_result: Optional[Phase2Result] = None
    phase3_result: Optional[Phase3Result] = None
    phase4_result: Optional[Phase4Result] = None
    phase5_result: Optional[Phase5Result] = None

    # Output links
    dependency_graph_url: Optional[str] = None
    hierarchy_url: Optional[str] = None
    metrics_url: Optional[str] = None
    conflicts_url: Optional[str] = None

    # Timing
    total_duration_ms: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Errors
    errors: List[str] = field(default_factory=list)


# Tier configuration
TIER_PHASES = {
    EnhancedAnalysisTier.FREE: [1],
    EnhancedAnalysisTier.BASIC: [1, 2],
    EnhancedAnalysisTier.STANDARD: [1, 2, 3],
    EnhancedAnalysisTier.PROFESSIONAL: [1, 2, 3, 4, 5],
    EnhancedAnalysisTier.PREMIUM: [1, 2, 3, 4, 5, 6],
}

TIER_CONFIDENCE_TARGETS = {
    EnhancedAnalysisTier.FREE: 0.60,
    EnhancedAnalysisTier.BASIC: 0.70,
    EnhancedAnalysisTier.STANDARD: 0.80,
    EnhancedAnalysisTier.PROFESSIONAL: 0.90,
    EnhancedAnalysisTier.PREMIUM: 0.95,
}

# LLM providers per tier
TIER_PROVIDERS = {
    EnhancedAnalysisTier.FREE: ["ollama"],
    EnhancedAnalysisTier.BASIC: ["ollama", "groq", "qwen"],
    EnhancedAnalysisTier.STANDARD: ["ollama", "groq", "qwen", "gemini"],
    EnhancedAnalysisTier.PROFESSIONAL: ["ollama", "groq", "qwen", "gemini", "openai"],
    EnhancedAnalysisTier.PREMIUM: ["ollama", "groq", "qwen", "gemini", "openai", "anthropic"],
}
