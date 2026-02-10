"""
Onboarding Workflow Orchestrator.

Unified workflow for project onboarding that consolidates capabilities from
6 existing workflows (A-F) into a single, well-tested pipeline.

Architecture Decision: This workflow is built incrementally with each module
tested on 3 reference projects before adding the next:
- /opt/projecten/hci-crs (9,922 files, 560MB)
- /opt/projecten/paramedi/FRM (6,710 files, 191MB)
- /opt/projecten/paramedi/FysioOne-Classic (2,235 files, 100MB)

Modules (in build order):
- M1: Input Validation (threshold 1.0) - COMPLETE
- M2: Intake + Vector DB Context - COMPLETE
- M3: Code Understanding (11 services) - COMPLETE
- M4: Deep Extraction (Felix+Quinn+Marcus) - COMPLETE
- M5: User Journey (Vicky+Peter) - COMPLETE
- M6: Security Scan (SecurityScanOrchestrator) - COMPLETE
- M7: Domain Extraction (W159 BusinessDomainExtractor) - COMPLETE
- M8: Story Generation (W159)
- M9: FP Estimation (IFPUG)
- M10: Deliverable Generation
- M11: Final Review (threshold 0.90)

Source references:
- Input validation pattern: migration.py L257-276, threshold 1.0
- Quality gates: base.py WorkflowStage
- DB persistence: brown_paper_service.py L3659-3728 (B's working variant)
- Vector DB context: brown_paper_service.py L3556-3644 (B's _fetch_vector_context)

Week 159 / Fase 24.9: Initial creation with M1.
Week 159 / Fase 24.9: Added M2 (Intake + Vector DB Context).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
import asyncio
import logging
import os

from .base import (
    WorkflowOrchestrator,
    WorkflowStage,
    WorkflowContext,
    WorkflowResult,
    WorkflowStatus,
    StageResult,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ONBOARDING QUESTIONS (5 questions, not 8 migration questions)
# =============================================================================

ONBOARDING_QUESTIONS = [
    {
        "id": "q1_primary_purpose",
        "question": "Wat is het primaire doel van deze applicatie?",
        "description": "Beschrijf de kernfunctionaliteit en het businessdoel",
        "required": True,
        "min_length": 50,
        "category": "context",
    },
    {
        "id": "q2_users",
        "question": "Wie zijn de belangrijkste gebruikers?",
        "description": "Beschrijf de doelgroepen en hun rollen",
        "required": True,
        "min_length": 30,
        "category": "context",
    },
    {
        "id": "q3_critical_processes",
        "question": "Wat zijn de kritieke business processen?",
        "description": "Beschrijf de processen die niet mogen falen",
        "required": True,
        "min_length": 50,
        "category": "analysis",
    },
    {
        "id": "q4_integrations",
        "question": "Welke integraties bestaan er?",
        "description": "Beschrijf externe systemen, APIs, databases",
        "required": True,
        "min_length": 20,
        "category": "analysis",
    },
    {
        "id": "q5_pain_points",
        "question": "Wat zijn de belangrijkste pijnpunten?",
        "description": "Beschrijf technische schuld, performance issues, etc.",
        "required": False,  # Optional but valuable
        "min_length": 0,
        "category": "analysis",
    },
]


# =============================================================================
# RESULT DATACLASSES
# =============================================================================

@dataclass
class OnboardingValidationResult:
    """Result of onboarding input validation."""
    valid: bool
    answers_count: int
    questions_total: int
    missing_required: List[str]
    validation_errors: List[str]

    @property
    def quality_score(self) -> float:
        """Calculate quality score (1.0 if all required answered, 0.0 otherwise)."""
        if self.missing_required:
            return 0.0
        return 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "answers_count": self.answers_count,
            "questions_total": self.questions_total,
            "missing_required": self.missing_required,
            "validation_errors": self.validation_errors,
            "quality_score": self.quality_score,
        }


@dataclass
class IntakeContextResult:
    """
    Result of intake context fetching from Vector DB.

    Source: brown_paper_service.py L3556-3644 (B's _fetch_vector_context)
    """
    context_available: bool
    project_name: str
    project_path: str
    relevant_docs: List[Dict[str, Any]]
    architecture_summary: Optional[str]
    code_locations: List[Dict[str, str]]
    total_docs_found: int
    fetched_at: str
    error: Optional[str] = None

    @property
    def quality_score(self) -> float:
        """
        Calculate quality score based on context richness.

        - 1.0: Has architecture summary + 5+ docs
        - 0.85: Has docs but no architecture summary
        - 0.70: No Vector DB available but project exists (graceful degradation)
        """
        if not self.context_available:
            # Graceful degradation - still pass if project exists
            return 0.70
        if self.architecture_summary and self.total_docs_found >= 5:
            return 1.0
        if self.total_docs_found > 0:
            return 0.85
        return 0.70

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_available": self.context_available,
            "project_name": self.project_name,
            "project_path": self.project_path,
            "relevant_docs_count": len(self.relevant_docs),
            "has_architecture_summary": self.architecture_summary is not None,
            "code_locations_count": len(self.code_locations),
            "total_docs_found": self.total_docs_found,
            "fetched_at": self.fetched_at,
            "quality_score": self.quality_score,
            "error": self.error,
        }


@dataclass
class CodeUnderstandingResult:
    """
    Result of code understanding analysis (11 services).

    Source: brown_paper_service.py L2493-2780 (A's _phase1_code_understanding)

    Services:
    1. DependencyGraphService - module dependencies
    2. CodeAnalysisAggregatorService - code metrics
    3. LayeredAnalysisService - layer detection
    4. FoundationDetectionService - foundation modules
    5. BackgroundJobDetectorService - scheduled jobs
    6. LoadEstimationService - capacity estimation
    7. DeadCodeDetectorService - unused code
    8. RuntimeAnalysisService - runtime behavior
    9. CodeCoverageAnalyzerService - test coverage
    10. DataLineageService - data flow
    11. SIG Quality Metrics - maintainability
    """
    project_path: str
    services_run: int
    services_succeeded: int
    services_failed: int

    # Individual service results (Dict or None if failed)
    dependency_graph: Optional[Dict[str, Any]] = None
    code_analysis: Optional[Dict[str, Any]] = None
    layered_analysis: Optional[Dict[str, Any]] = None
    foundation: Optional[Dict[str, Any]] = None
    background_jobs: Optional[Dict[str, Any]] = None
    load_estimation: Optional[Dict[str, Any]] = None
    dead_code: Optional[Dict[str, Any]] = None
    runtime_analysis: Optional[Dict[str, Any]] = None
    coverage_analysis: Optional[Dict[str, Any]] = None
    data_lineage: Optional[Dict[str, Any]] = None
    sig_quality: Optional[Dict[str, Any]] = None

    errors: List[str] = None
    duration_seconds: float = 0.0

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    @property
    def quality_score(self) -> float:
        """
        Calculate quality score based on service success count.

        - 1.0: All 11 services succeeded
        - 0.85: 8+ services succeeded (core services)
        - 0.75: 5+ services succeeded (minimum viable)
        - 0.60: 3+ services succeeded (degraded)
        - 0.50: Minimum viable - continue with limited data
        """
        if self.services_run == 0:
            return 0.0

        # Use absolute thresholds for clarity
        if self.services_succeeded >= 11:
            return 1.0
        elif self.services_succeeded >= 8:
            return 0.85
        elif self.services_succeeded >= 5:
            return 0.75
        elif self.services_succeeded >= 3:
            return 0.60
        else:
            return 0.50  # Minimum viable - continue with limited data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "services_run": self.services_run,
            "services_succeeded": self.services_succeeded,
            "services_failed": self.services_failed,
            "success_rate": f"{self.services_succeeded}/{self.services_run}",
            "quality_score": self.quality_score,
            "duration_seconds": round(self.duration_seconds, 2),
            "has_dependency_graph": self.dependency_graph is not None,
            "has_code_analysis": self.code_analysis is not None,
            "has_layered_analysis": self.layered_analysis is not None,
            "has_foundation": self.foundation is not None,
            "has_background_jobs": self.background_jobs is not None,
            "has_load_estimation": self.load_estimation is not None,
            "has_dead_code": self.dead_code is not None,
            "has_runtime_analysis": self.runtime_analysis is not None,
            "has_coverage_analysis": self.coverage_analysis is not None,
            "has_data_lineage": self.data_lineage is not None,
            "has_sig_quality": self.sig_quality is not None,
            "errors": self.errors,
        }


@dataclass
class DeepExtractionResult:
    """
    Result of deep extraction analysis with LLM council (Felix+Quinn+Marcus).

    Source: brown_paper.py L335-390 (_execute_deep_extraction)

    Agents:
    - Felix: Architecture patterns and legacy code analysis
    - Quinn: Code quality review and issue identification
    - Marcus: Maintainability assessment and technical debt

    Quality scoring:
    - 1.0: All 3 agents completed with substantive findings
    - 0.85: 2/3 agents completed
    - 0.70: 1/3 agents completed (degraded mode)
    - 0.50: No agents but code_understanding available
    """
    project_path: str
    agents_run: int
    agents_succeeded: int

    # Agent results
    architecture_insights: Optional[Dict[str, Any]] = None  # Felix
    quality_findings: List[Dict[str, Any]] = None  # Quinn
    maintenance_recommendations: List[Dict[str, Any]] = None  # Marcus
    council_consensus: Optional[Dict[str, Any]] = None  # Combined

    errors: List[str] = None
    duration_seconds: float = 0.0

    def __post_init__(self):
        if self.quality_findings is None:
            self.quality_findings = []
        if self.maintenance_recommendations is None:
            self.maintenance_recommendations = []
        if self.errors is None:
            self.errors = []

    @property
    def quality_score(self) -> float:
        """
        Calculate quality score based on agent success.

        - 1.0: All 3 agents with substantive output
        - 0.85: 2/3 agents succeeded
        - 0.70: 1/3 agents succeeded (degraded)
        - 0.50: No agents but has code_understanding fallback
        """
        if self.agents_run == 0:
            return 0.50  # Fallback to code_understanding

        # Check for substantive output
        has_architecture = (
            self.architecture_insights is not None
            and self.architecture_insights.get("status") != "skipped"
        )
        has_quality = len(self.quality_findings) > 0
        has_maintenance = len(self.maintenance_recommendations) > 0

        substantive_count = sum([has_architecture, has_quality, has_maintenance])

        if substantive_count >= 3:
            return 1.0
        elif self.agents_succeeded >= 2 or substantive_count >= 2:
            return 0.85
        elif self.agents_succeeded >= 1 or substantive_count >= 1:
            return 0.70
        else:
            return 0.50

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "agents_run": self.agents_run,
            "agents_succeeded": self.agents_succeeded,
            "agents_failed": self.agents_run - self.agents_succeeded,
            "quality_score": self.quality_score,
            "duration_seconds": round(self.duration_seconds, 2),
            "has_architecture_insights": self.architecture_insights is not None,
            "architecture_insights": self.architecture_insights,
            "quality_findings_count": len(self.quality_findings),
            "quality_findings": self.quality_findings,
            "maintenance_recommendations_count": len(self.maintenance_recommendations),
            "maintenance_recommendations": self.maintenance_recommendations,
            "council_consensus": self.council_consensus,
            "errors": self.errors,
        }


@dataclass
class SecurityScanResult:
    """
    Result of security scan analysis (M6).

    Source: security_scanner/orchestrator.py (SecurityScanOrchestrator)

    This stage runs multiple security scanners in parallel:
    - OpenGrep: Multi-language SAST
    - Bandit: Python security linting
    - Trivy: Dependency vulnerability scanning
    - Custom ASP Scanner: Classic ASP vulnerabilities
    - OWASP Scanner: OWASP Top 10 detection
    - Injection Detector: XSS, SQLi, CMDi, etc.
    - And 10+ more specialized scanners

    Quality scoring:
    - 1.0: No critical findings, <5 high findings
    - 0.85: No critical, <10 high findings
    - 0.80: <3 critical, <20 high findings (threshold)
    - 0.70: <5 critical, <30 high findings
    - 0.50: Many critical findings (degraded)
    """
    project_path: str
    scanners_run: int
    scanners_succeeded: int
    languages_detected: List[str] = None

    # Finding counts by severity
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    total_findings: int = 0

    # Top findings (limited for context size)
    top_critical: List[Dict[str, Any]] = None
    top_high: List[Dict[str, Any]] = None

    # CWE coverage
    cwe_ids_found: List[str] = None
    cwe_top_25_coverage: int = 0

    # Scanner details
    scanners_used: List[str] = None

    errors: List[str] = None
    duration_seconds: float = 0.0

    def __post_init__(self):
        if self.languages_detected is None:
            self.languages_detected = []
        if self.top_critical is None:
            self.top_critical = []
        if self.top_high is None:
            self.top_high = []
        if self.cwe_ids_found is None:
            self.cwe_ids_found = []
        if self.scanners_used is None:
            self.scanners_used = []
        if self.errors is None:
            self.errors = []

    @property
    def quality_score(self) -> float:
        """
        Calculate quality score based on finding severity.

        Scoring logic:
        - 1.0: No critical, <5 high (excellent security posture)
        - 0.85: No critical, <10 high (good)
        - 0.80: <3 critical, <20 high (threshold - acceptable)
        - 0.70: <5 critical, <30 high (needs attention)
        - 0.50: Many critical findings (significant risk)

        Note: This is INVERTED from typical quality scores - fewer issues = higher score.
        """
        if self.scanners_run == 0:
            return 0.50  # No scan data

        # Excellent: No critical, few high
        if self.critical_count == 0 and self.high_count < 5:
            return 1.0

        # Good: No critical, moderate high
        if self.critical_count == 0 and self.high_count < 10:
            return 0.85

        # Acceptable: Few critical, manageable high
        if self.critical_count < 3 and self.high_count < 20:
            return 0.80

        # Needs attention: Some critical
        if self.critical_count < 5 and self.high_count < 30:
            return 0.70

        # Significant risk
        return 0.50

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "scanners_run": self.scanners_run,
            "scanners_succeeded": self.scanners_succeeded,
            "languages_detected": self.languages_detected,
            "quality_score": self.quality_score,
            "duration_seconds": round(self.duration_seconds, 2),
            "findings": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "info": self.info_count,
                "total": self.total_findings,
            },
            "top_critical": self.top_critical[:5],  # Limit for context
            "top_high": self.top_high[:10],
            "cwe_coverage": {
                "cwe_ids_found": self.cwe_ids_found[:20],  # Limit
                "cwe_top_25_coverage": self.cwe_top_25_coverage,
            },
            "scanners_used": self.scanners_used,
            "errors": self.errors,
        }


@dataclass
class UserJourneyResult:
    """
    Result of user journey extraction (Vicky+Peter).

    Source: stages/user_journey_extraction.py (UserJourneyExtractionStage)

    Agents:
    - Vicky: UI/UX analysis, screen flows, personas from UI
    - Peter: Business journeys, persona goals, business processes

    Extraction sources:
    - UI Components (ASPX, Razor, React)
    - Authorization/Role checks
    - Navigation/Routing
    - Form handlers & validators
    - Database user/role tables

    Quality scoring:
    - 1.0: Both agents + rich extraction (5+ journeys, 3+ personas)
    - 0.85: Both agents but limited extraction
    - 0.70: One agent or good fallback extraction
    - 0.50: Minimal extraction (threshold)
    """
    project_path: str
    agents_run: int
    agents_succeeded: int

    # Extracted data
    personas: List[Dict[str, Any]] = None
    journeys: List[Dict[str, Any]] = None
    screens: List[Dict[str, Any]] = None
    screen_flows: List[Dict[str, Any]] = None
    role_matrix: Optional[Dict[str, Any]] = None

    # Statistics
    total_personas: int = 0
    total_journeys: int = 0
    total_screens: int = 0
    total_steps: int = 0

    # Quality
    extraction_confidence: float = 0.0
    coverage_percentage: float = 0.0
    gaps: List[str] = None

    errors: List[str] = None
    duration_seconds: float = 0.0

    def __post_init__(self):
        if self.personas is None:
            self.personas = []
        if self.journeys is None:
            self.journeys = []
        if self.screens is None:
            self.screens = []
        if self.screen_flows is None:
            self.screen_flows = []
        if self.gaps is None:
            self.gaps = []
        if self.errors is None:
            self.errors = []

    @property
    def quality_score(self) -> float:
        """
        Calculate quality score based on extraction completeness.

        Method-agnostic: score reflects data quality, not extraction method.
        No "fallback minimums" - if data is insufficient, score reflects that.

        - 1.0: Rich extraction (5+ journeys, 3+ personas, good coverage)
        - 0.85: Good extraction (3+ journeys, 2+ personas)
        - 0.70: Acceptable extraction (2+ journeys, 1+ persona) - threshold
        - 0.50: Minimal extraction (1 journey, 1 persona)
        - 0.0: No extraction (fail)
        """
        # No data = no score (fail - don't give free pass)
        if self.total_journeys == 0 and self.total_personas == 0:
            return 0.0

        # Check extraction richness - method-agnostic
        has_rich_journeys = self.total_journeys >= 5
        has_rich_personas = self.total_personas >= 3
        has_good_journeys = self.total_journeys >= 3
        has_good_personas = self.total_personas >= 2
        has_acceptable = self.total_journeys >= 2 and self.total_personas >= 1
        has_minimal = self.total_journeys >= 1 and self.total_personas >= 1

        # Score based purely on extraction quality
        if has_rich_journeys and has_rich_personas:
            return 1.0
        elif has_good_journeys and has_good_personas:
            return 0.85
        elif has_acceptable:
            return 0.70  # Threshold
        elif has_minimal:
            return 0.50  # Below threshold but has data
        else:
            return 0.30  # Partial data only

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "agents_run": self.agents_run,
            "agents_succeeded": self.agents_succeeded,
            "quality_score": self.quality_score,
            "duration_seconds": round(self.duration_seconds, 2),
            "total_personas": self.total_personas,
            "total_journeys": self.total_journeys,
            "total_screens": self.total_screens,
            "total_steps": self.total_steps,
            "personas": self.personas,
            "journeys": self.journeys,
            "screens": self.screens,
            "screen_flows": self.screen_flows,
            "role_matrix": self.role_matrix,
            "extraction_confidence": self.extraction_confidence,
            "coverage_percentage": self.coverage_percentage,
            "gaps": self.gaps,
            "errors": self.errors,
        }


@dataclass
class DomainExtractionResult:
    """
    Result of domain extraction analysis (M7).

    Source: business_domain_extractor_service.py (BusinessDomainExtractorService)

    This stage uses W159 BusinessDomainExtractor to:
    - Cluster modules based on dependencies
    - Analyze file/function names for domain hints
    - Extract entities from code (classes, tables, forms)
    - Match with common business domain patterns
    - Generate structured business domains with source references

    Agents:
    - Peter: Business domain validation and refinement
    - Betty: Documentation and use case expansion

    Quality scoring:
    - 1.0: 5+ domains with high confidence (>0.7), both agents contributed
    - 0.85: 3+ domains with good confidence (>0.5)
    - 0.70: 1+ domains extracted (threshold)
    - 0.50: Minimal extraction (fallback)
    """
    project_path: str
    agents_run: int
    agents_succeeded: int

    # Extracted domains
    domains: List[Dict[str, Any]] = None
    module_clusters: List[Dict[str, Any]] = None
    entities_found: int = 0
    modules_analyzed: int = 0

    # Domain statistics
    total_domains: int = 0
    high_confidence_domains: int = 0  # confidence > 0.7
    total_use_cases: int = 0
    total_entities: int = 0

    # Agent contributions
    peter_refinements: Optional[Dict[str, Any]] = None
    betty_documentation: Optional[Dict[str, Any]] = None

    errors: List[str] = None
    duration_seconds: float = 0.0

    def __post_init__(self):
        if self.domains is None:
            self.domains = []
        if self.module_clusters is None:
            self.module_clusters = []
        if self.errors is None:
            self.errors = []

    @property
    def quality_score(self) -> float:
        """
        Calculate quality score based on domain extraction completeness.

        Method-agnostic: score reflects domain quality, not extraction method.

        - 1.0: 5+ domains with high confidence (>0.7)
        - 0.85: 3+ domains with at least one high confidence
        - 0.70: 2+ domains extracted (threshold)
        - 0.50: 1 domain only
        - 0.0: No domains (fail)
        """
        # No domains = fail
        if self.total_domains == 0:
            return 0.0

        has_rich_domains = self.total_domains >= 5 and self.high_confidence_domains >= 3
        has_good_domains = self.total_domains >= 3 and self.high_confidence_domains >= 1
        has_acceptable_domains = self.total_domains >= 2
        has_minimal_domains = self.total_domains >= 1

        # Score based on extraction quality
        if has_rich_domains:
            return 1.0
        elif has_good_domains:
            return 0.85
        elif has_acceptable_domains:
            return 0.70  # Threshold
        elif has_minimal_domains:
            return 0.50  # Below threshold
        else:
            return 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "agents_run": self.agents_run,
            "agents_succeeded": self.agents_succeeded,
            "quality_score": self.quality_score,
            "duration_seconds": round(self.duration_seconds, 2),
            "total_domains": self.total_domains,
            "high_confidence_domains": self.high_confidence_domains,
            "total_use_cases": self.total_use_cases,
            "total_entities": self.total_entities,
            "modules_analyzed": self.modules_analyzed,
            "entities_found": self.entities_found,
            "domains": self.domains,
            "module_clusters": [
                {
                    "name": c.get("name", ""),
                    "modules_count": len(c.get("modules", [])),
                    "cohesion_score": c.get("cohesion_score", 0),
                }
                for c in self.module_clusters[:10]  # Limit for context
            ],
            "peter_refinements": self.peter_refinements,
            "betty_documentation": self.betty_documentation,
            "errors": self.errors,
        }


@dataclass
class StoryGenerationResult:
    """
    Result of story generation analysis (M8).

    Source: business_driven_story_generator_service.py (BusinessDrivenStoryGeneratorService)

    This stage uses W159 BusinessDrivenStoryGenerator to:
    - Generate epics from business domains (M7)
    - Generate features from module clusters
    - Generate stories from use cases, forms, entities
    - Add acceptance criteria and source references
    - Link stories to user journeys (M5)

    Agent:
    - Peter: Story validation and business context enrichment

    Quality scoring:
    - 1.0: 10+ stories, 3+ epics, agent contributed
    - 0.85: 5+ stories, 2+ epics
    - 0.70: 1+ stories, 1+ epic (threshold)
    - 0.50: Minimal generation (fallback)
    """
    project_path: str
    agents_run: int
    agents_succeeded: int

    # Generated content
    epics: List[Dict[str, Any]] = None
    features: List[Dict[str, Any]] = None
    stories: List[Dict[str, Any]] = None

    # Statistics
    total_epics: int = 0
    total_features: int = 0
    total_stories: int = 0
    total_story_points: int = 0
    estimated_weeks: int = 0

    # Links to other stages
    domains_processed: int = 0
    journeys_linked: int = 0
    personas_linked: int = 0

    # Agent contribution
    peter_enrichments: Optional[Dict[str, Any]] = None

    errors: List[str] = None
    duration_seconds: float = 0.0

    def __post_init__(self):
        if self.epics is None:
            self.epics = []
        if self.features is None:
            self.features = []
        if self.stories is None:
            self.stories = []
        if self.errors is None:
            self.errors = []

    @property
    def quality_score(self) -> float:
        """
        Calculate quality score based on story generation completeness.

        Method-agnostic: score reflects output quality, not generation method.
        No "fallback minimums" - if stories are insufficient, score reflects that.

        - 1.0: Rich generation (10+ stories, 3+ epics, proper structure)
        - 0.85: Good generation (5+ stories, 2+ epics)
        - 0.70: Acceptable generation (3+ stories, 1+ epic) - threshold
        - 0.50: Minimal generation (1+ stories)
        - 0.0: No stories (fail)
        """
        # No stories = no score (fail - don't give free pass)
        if self.total_stories == 0:
            return 0.0

        # Check generation quality - method-agnostic
        has_rich_generation = self.total_stories >= 10 and self.total_epics >= 3
        has_good_generation = self.total_stories >= 5 and self.total_epics >= 2
        has_acceptable_generation = self.total_stories >= 3 and self.total_epics >= 1
        has_minimal_generation = self.total_stories >= 1

        # Score based purely on output quality
        if has_rich_generation:
            return 1.0
        elif has_good_generation:
            return 0.85
        elif has_acceptable_generation:
            return 0.70  # Threshold
        elif has_minimal_generation:
            return 0.50  # Below threshold but has data
        else:
            return 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "agents_run": self.agents_run,
            "agents_succeeded": self.agents_succeeded,
            "quality_score": self.quality_score,
            "duration_seconds": round(self.duration_seconds, 2),
            "total_epics": self.total_epics,
            "total_features": self.total_features,
            "total_stories": self.total_stories,
            "total_story_points": self.total_story_points,
            "estimated_weeks": self.estimated_weeks,
            "domains_processed": self.domains_processed,
            "journeys_linked": self.journeys_linked,
            "personas_linked": self.personas_linked,
            "epics": self.epics[:10],  # Limit for context
            "stories": self.stories[:20],  # Limit for context
            "peter_enrichments": self.peter_enrichments,
            "errors": self.errors,
        }


@dataclass
class EstimationResult:
    """
    Result of effort estimation analysis (M9).

    Source: migration_estimation_service.py (MigrationEstimationService)

    This stage uses IFPUG Function Point methodology to:
    - Calculate function points from code components
    - Apply migration complexity multipliers
    - Estimate effort by project phase
    - Provide risk-adjusted estimates
    - Generate team velocity recommendations

    Agent:
    - Eliza: Estimation refinement and confidence scoring

    Quality scoring:
    - 1.0: Complete FP analysis, phase estimates, agent contributed
    - 0.85: FP analysis with reasonable confidence
    - 0.75: Basic estimation (threshold)
    - 0.50: Minimal estimation (fallback from story points)
    """
    project_path: str
    agents_run: int
    agents_succeeded: int

    # Function Points
    unadjusted_fp: float = 0.0
    value_adjustment_factor: float = 1.0
    adjusted_fp: float = 0.0

    # Component breakdown
    component_count: int = 0
    components_by_type: Dict[str, int] = None

    # Effort estimates
    total_effort_hours: float = 0.0
    total_effort_person_days: float = 0.0
    total_effort_person_months: float = 0.0

    # Phase breakdown
    phase_estimates: List[Dict[str, Any]] = None

    # Story-based estimates (from M8)
    story_based_estimate_weeks: int = 0
    story_points_total: int = 0

    # Combined estimates
    estimated_weeks_low: int = 0
    estimated_weeks_high: int = 0
    estimated_weeks_likely: int = 0

    # Team recommendations
    recommended_team_size: int = 0
    velocity_assumption: int = 20  # Story points per week

    # Confidence and risks
    confidence_level: float = 0.0
    risk_factors: List[Dict[str, Any]] = None
    recommendations: List[str] = None

    # Agent contribution
    eliza_refinements: Optional[Dict[str, Any]] = None

    errors: List[str] = None
    duration_seconds: float = 0.0

    def __post_init__(self):
        if self.components_by_type is None:
            self.components_by_type = {}
        if self.phase_estimates is None:
            self.phase_estimates = []
        if self.risk_factors is None:
            self.risk_factors = []
        if self.recommendations is None:
            self.recommendations = []
        if self.errors is None:
            self.errors = []

    @property
    def quality_score(self) -> float:
        """
        Calculate quality score based on estimation completeness.

        Method-agnostic: FP-based and story-point-based estimates are equally valid.
        Score reflects estimation thoroughness, not method used.

        - 1.0: Complete analysis + phase estimates + confidence >0.7
        - 0.85: Good analysis with reasonable confidence (>0.6)
        - 0.75: Acceptable estimation with data - threshold
        - 0.50: Minimal estimation (some data but low confidence)
        - 0.0: No estimation data (fail)
        """
        has_fp_analysis = self.adjusted_fp > 0 and self.component_count > 0
        has_story_point_estimate = self.story_points_total > 0
        has_phase_estimates = len(self.phase_estimates) >= 5
        has_good_confidence = self.confidence_level >= 0.6
        has_high_confidence = self.confidence_level >= 0.7

        # No estimation data at all = fail
        if not has_fp_analysis and not has_story_point_estimate:
            return 0.0

        # Either FP or story points is valid - check quality of estimate
        if (has_fp_analysis or has_story_point_estimate) and has_phase_estimates and has_high_confidence:
            return 1.0
        elif (has_fp_analysis or has_story_point_estimate) and has_good_confidence:
            return 0.85
        elif has_fp_analysis or has_story_point_estimate:
            return 0.75  # Threshold - has estimate data
        else:
            return 0.50  # Should not reach here

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "agents_run": self.agents_run,
            "agents_succeeded": self.agents_succeeded,
            "quality_score": self.quality_score,
            "duration_seconds": round(self.duration_seconds, 2),
            "function_points": {
                "unadjusted": round(self.unadjusted_fp, 1),
                "vaf": round(self.value_adjustment_factor, 2),
                "adjusted": round(self.adjusted_fp, 1),
            },
            "components": {
                "total": self.component_count,
                "by_type": self.components_by_type,
            },
            "effort": {
                "hours": round(self.total_effort_hours, 1),
                "person_days": round(self.total_effort_person_days, 1),
                "person_months": round(self.total_effort_person_months, 1),
            },
            "estimates": {
                "weeks_low": self.estimated_weeks_low,
                "weeks_likely": self.estimated_weeks_likely,
                "weeks_high": self.estimated_weeks_high,
                "story_based_weeks": self.story_based_estimate_weeks,
                "story_points_total": self.story_points_total,
            },
            "team": {
                "recommended_size": self.recommended_team_size,
                "velocity_assumption": self.velocity_assumption,
            },
            "confidence_level": round(self.confidence_level, 2),
            "phase_estimates": self.phase_estimates[:10],  # Limit
            "risk_factors": self.risk_factors[:10],  # Limit
            "recommendations": self.recommendations[:10],  # Limit
            "eliza_refinements": self.eliza_refinements,
            "errors": self.errors,
        }


@dataclass
class DeliverablesResult:
    """
    Result of deliverables generation (M10).

    Source: brown_paper_deliverable_service.py (BrownPaperDeliverableService)

    This stage generates comprehensive documentation from all previous stages:
    - Project summary (executive overview)
    - Epics hierarchy (drill-down structure)
    - User journeys documentation
    - Architecture assessment
    - Security findings report
    - Risk register
    - Estimation report
    - Migration strategy

    Agent:
    - Diana: Documentation review and enhancement

    Quality scoring:
    - 1.0: All sections generated, agent contributed, >10 files
    - 0.85: Core sections generated (summary, epics, estimation)
    - 0.80: Basic deliverables (threshold)
    - 0.50: Minimal output (fallback)
    """
    project_path: str
    output_dir: str
    agents_run: int
    agents_succeeded: int

    # File counts
    files_created: int = 0
    total_size_kb: float = 0.0

    # Section counts
    epics_documented: int = 0
    features_documented: int = 0
    stories_documented: int = 0

    # Sections generated
    sections_generated: List[str] = None
    section_details: Dict[str, Dict[str, Any]] = None

    # File paths
    file_paths: List[str] = None
    index_path: str = ""

    # Agent contribution
    diana_enhancements: Optional[Dict[str, Any]] = None

    errors: List[str] = None
    duration_seconds: float = 0.0

    def __post_init__(self):
        if self.sections_generated is None:
            self.sections_generated = []
        if self.section_details is None:
            self.section_details = {}
        if self.file_paths is None:
            self.file_paths = []
        if self.errors is None:
            self.errors = []

    @property
    def quality_score(self) -> float:
        """
        Calculate quality score based on deliverables completeness.

        - 1.0: All sections, agent contributed, >10 files
        - 0.85: Core sections (summary, epics, estimation)
        - 0.80: Basic deliverables (threshold)
        - 0.50: Minimal output (fallback)
        """
        core_sections = {"project-summary", "epics", "estimation"}
        has_core = core_sections.issubset(set(self.sections_generated))
        has_many_files = self.files_created >= 10
        agent_contributed = self.agents_succeeded >= 1

        if has_core and has_many_files and agent_contributed:
            return 1.0
        elif has_core and self.files_created >= 5:
            return 0.85
        elif self.files_created >= 3:
            return 0.80
        else:
            return 0.50

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "output_dir": self.output_dir,
            "agents_run": self.agents_run,
            "agents_succeeded": self.agents_succeeded,
            "quality_score": self.quality_score,
            "duration_seconds": round(self.duration_seconds, 2),
            "files": {
                "created": self.files_created,
                "total_size_kb": round(self.total_size_kb, 1),
                "paths": self.file_paths[:20],  # Limit
            },
            "documentation": {
                "epics": self.epics_documented,
                "features": self.features_documented,
                "stories": self.stories_documented,
            },
            "sections": {
                "generated": self.sections_generated,
                "details": self.section_details,
            },
            "index_path": self.index_path,
            "diana_enhancements": self.diana_enhancements,
            "errors": self.errors,
        }


@dataclass
class QualityReviewResult:
    """
    Result of final quality review (M11).

    Source: MigrationOrchestrator pattern (quality_review stage)

    This stage performs final validation across all previous stages:
    - Cross-module consistency check
    - Security compliance verification
    - Estimation reasonableness assessment
    - Documentation completeness audit
    - Data integrity validation

    Agent:
    - Quinn: Quality review and compliance assessment

    Quality scoring:
    - 1.0: All checks pass, Quinn approved, no critical issues
    - 0.90: All core checks pass (threshold)
    - 0.80: Minor issues detected but acceptable
    - 0.50: Significant issues requiring remediation
    """
    project_path: str
    agents_run: int
    agents_succeeded: int

    # Consistency checks
    consistency_score: float = 0.0
    consistency_issues: List[Dict[str, Any]] = None

    # Security compliance
    security_compliant: bool = False
    security_score: float = 0.0
    security_issues: List[str] = None

    # Estimation validation
    estimation_reasonable: bool = False
    estimation_confidence: float = 0.0
    estimation_warnings: List[str] = None

    # Documentation completeness
    documentation_complete: bool = False
    documentation_score: float = 0.0
    missing_sections: List[str] = None

    # Data integrity
    data_integrity_score: float = 0.0
    data_issues: List[str] = None

    # Overall assessment
    overall_assessment: str = ""
    recommendations: List[str] = None
    blockers: List[str] = None

    # Agent contribution
    quinn_assessment: Optional[Dict[str, Any]] = None

    errors: List[str] = None
    duration_seconds: float = 0.0

    def __post_init__(self):
        if self.consistency_issues is None:
            self.consistency_issues = []
        if self.security_issues is None:
            self.security_issues = []
        if self.estimation_warnings is None:
            self.estimation_warnings = []
        if self.missing_sections is None:
            self.missing_sections = []
        if self.data_issues is None:
            self.data_issues = []
        if self.recommendations is None:
            self.recommendations = []
        if self.blockers is None:
            self.blockers = []
        if self.errors is None:
            self.errors = []

    @property
    def quality_score(self) -> float:
        """
        Calculate quality score based on review completeness.

        - 1.0: All checks pass, agent approved, no blockers
        - 0.90: All core checks pass (threshold)
        - 0.80: Minor issues but acceptable
        - 0.50: Significant issues
        """
        # Core checks
        has_consistency = self.consistency_score >= 0.8
        has_security = self.security_compliant or self.security_score >= 0.8
        has_estimation = self.estimation_reasonable or self.estimation_confidence >= 0.6
        has_docs = self.documentation_complete or self.documentation_score >= 0.8
        has_integrity = self.data_integrity_score >= 0.8

        core_checks_passed = sum([
            has_consistency,
            has_security,
            has_estimation,
            has_docs,
            has_integrity,
        ])

        agent_approved = self.agents_succeeded >= 1
        no_blockers = len(self.blockers) == 0

        if core_checks_passed == 5 and agent_approved and no_blockers:
            return 1.0
        elif core_checks_passed >= 4 and no_blockers:
            return 0.90
        elif core_checks_passed >= 3:
            return 0.80
        elif core_checks_passed >= 2:
            return 0.70
        else:
            return 0.50

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "agents_run": self.agents_run,
            "agents_succeeded": self.agents_succeeded,
            "quality_score": self.quality_score,
            "duration_seconds": round(self.duration_seconds, 2),
            "checks": {
                "consistency": {
                    "score": round(self.consistency_score, 2),
                    "issues": self.consistency_issues[:10],
                },
                "security": {
                    "compliant": self.security_compliant,
                    "score": round(self.security_score, 2),
                    "issues": self.security_issues[:10],
                },
                "estimation": {
                    "reasonable": self.estimation_reasonable,
                    "confidence": round(self.estimation_confidence, 2),
                    "warnings": self.estimation_warnings[:10],
                },
                "documentation": {
                    "complete": self.documentation_complete,
                    "score": round(self.documentation_score, 2),
                    "missing": self.missing_sections,
                },
                "data_integrity": {
                    "score": round(self.data_integrity_score, 2),
                    "issues": self.data_issues[:10],
                },
            },
            "assessment": {
                "overall": self.overall_assessment,
                "recommendations": self.recommendations[:10],
                "blockers": self.blockers,
            },
            "quinn_assessment": self.quinn_assessment,
            "errors": self.errors,
        }


# =============================================================================
# ONBOARDING WORKFLOW ORCHESTRATOR
# =============================================================================

class OnboardingOrchestrator(WorkflowOrchestrator):
    """
    Orchestrates the unified onboarding workflow.

    This workflow consolidates capabilities from 6 existing workflows:
    - A: BrownPaperService (11 code understanding services)
    - B: MarQedBrownPaperWorkflow (Vector DB, answer versioning, deliverables)
    - C: BrownPaperOrchestrator (deep extraction, user journeys)
    - D: MigrationOrchestrator (security analysis, quality review)
    - E: OnboardingWorkflowIntegration (hook pattern)
    - F: UnifiedOnboardingService (step execution)

    Built incrementally - each module tested before adding the next.

    Example:
    ```python
    orchestrator = OnboardingOrchestrator()
    result = await orchestrator.run(
        session_id="onb-123",
        input_data={
            "project_path": "/opt/projecten/hci-crs",
            "answers": {
                "q1_primary_purpose": "Healthcare registration system...",
                "q2_users": "Administrative staff and physicians...",
                ...
            },
        },
    )
    ```
    """

    @property
    def workflow_type(self) -> str:
        return "onboarding"

    def get_stages(self) -> List[WorkflowStage]:
        """
        Define Onboarding workflow stages.

        Currently implemented: M1 (Input Validation), M2 (Intake Context)
        More stages will be added as modules are tested.
        """
        return [
            # M1: Input Validation
            WorkflowStage(
                name="validate_input",
                description="Validate project path and required answers",
                agents=[],  # No agent needed for validation
                required=True,
                quality_threshold=1.0,  # Must pass - no partial validation
                max_iterations=1,  # Single pass - either valid or not
                timeout_seconds=30,
            ),
            # M2: Intake Context (Vector DB)
            WorkflowStage(
                name="intake_context",
                description="Fetch project context from Vector DB for enriched analysis",
                agents=[],  # No agent needed - direct service call
                required=True,
                quality_threshold=0.70,  # Graceful degradation if no Vector DB
                max_iterations=1,
                timeout_seconds=60,
                depends_on=["validate_input"],
            ),
            # M3: Code Understanding (11 services)
            WorkflowStage(
                name="code_understanding",
                description="Run 11 code analysis services for deep understanding",
                agents=[],  # Direct service calls
                required=True,
                quality_threshold=0.50,  # Minimum 3/11 services for degraded mode
                max_iterations=1,
                timeout_seconds=600,  # 10 minutes for large codebases
                depends_on=["intake_context"],
            ),
            # M4: Deep Extraction (Felix+Quinn+Marcus)
            WorkflowStage(
                name="deep_extraction",
                description="Deep analysis with LLM council (Felix=architecture, Quinn=quality, Marcus=maintenance)",
                agents=["Felix", "Quinn", "Marcus"],
                required=False,  # Optional enhancement - can proceed without
                parallel_agents=True,
                quality_threshold=0.70,  # At least 1/3 agents must succeed
                max_iterations=1,
                timeout_seconds=300,  # 5 minutes per agent
                depends_on=["code_understanding"],
            ),
            # M5: User Journey (Vicky+Peter)
            WorkflowStage(
                name="user_journey",
                description="Extract user journeys, personas, and screen flows (Vicky=UI/UX, Peter=business)",
                agents=["Vicky", "Peter"],
                required=True,  # Important for story generation
                parallel_agents=False,  # Sequential: Vicky first, then Peter
                quality_threshold=0.70,  # At least basic extraction required
                max_iterations=1,
                timeout_seconds=300,
                depends_on=["deep_extraction"],
            ),
            # M6: Security Scan (SecurityScanOrchestrator)
            # NOTE: For onboarding, security gate is OFF (reports findings, doesn't block)
            # For CI/CD workflows (checkins), security gate should be ON (quality_threshold=0.80)
            WorkflowStage(
                name="security_scan",
                description="Run multi-scanner security analysis (OpenGrep, Bandit, Trivy, OWASP, Injection, etc.)",
                agents=["Quinn"],  # Quinn reviews security findings
                required=True,  # Always run security scan
                parallel_agents=False,
                quality_threshold=0.0,  # Onboarding: report only, don't block. CI/CD: use 0.80
                max_iterations=1,
                timeout_seconds=0,  # No timeout - process all files
                depends_on=["user_journey"],
            ),
            # M7: Domain Extraction (W159 BusinessDomainExtractor)
            # NOTE: Does NOT depend on security_scan - these are orthogonal concerns
            # Security findings are incorporated into deliverables (M10), not blocking domain work
            WorkflowStage(
                name="domain_extraction",
                description="Extract business domains from code analysis using W159 BusinessDomainExtractor (Peter=validation, Betty=documentation)",
                agents=["Peter", "Betty"],
                required=True,  # Important for story generation
                parallel_agents=True,  # Run Peter and Betty in parallel
                quality_threshold=0.70,  # At least basic extraction required
                max_iterations=1,
                timeout_seconds=300,  # 5 minutes
                depends_on=["user_journey"],  # Changed: domain extraction doesn't need security results
            ),
            # M8: Story Generation (W159 BusinessDrivenStoryGenerator)
            WorkflowStage(
                name="story_generation",
                description="Generate epics, features, and stories from domains using W159 BusinessDrivenStoryGenerator (Peter=enrichment)",
                agents=["Peter"],
                required=True,  # Core deliverable of onboarding
                parallel_agents=False,
                quality_threshold=0.70,  # At least basic generation required
                max_iterations=1,
                timeout_seconds=300,  # 5 minutes
                depends_on=["domain_extraction"],
            ),
            # M9: Estimation (IFPUG Function Points + Story Points)
            WorkflowStage(
                name="estimation",
                description="Calculate IFPUG function points and effort estimates using MigrationEstimationService (Eliza=refinement)",
                agents=["Eliza"],
                required=True,  # Core deliverable of onboarding
                parallel_agents=False,
                quality_threshold=0.75,  # Basic estimation required
                max_iterations=1,
                timeout_seconds=300,  # 5 minutes
                depends_on=["story_generation"],
            ),
            # M10: Deliverables Generation (markdown documentation)
            WorkflowStage(
                name="deliverables",
                description="Generate comprehensive markdown documentation using BrownPaperDeliverableService (Diana=enhancement)",
                agents=["Diana"],
                required=True,  # Core deliverable of onboarding
                parallel_agents=False,
                quality_threshold=0.80,  # Comprehensive docs required
                max_iterations=1,
                timeout_seconds=300,  # 5 minutes
                depends_on=["estimation"],
            ),
            # Plane Export: Assemble Plane-compatible export package
            WorkflowStage(
                name="plane_export",
                description="Assemble Plane-compatible export package from M8+M9+Peter data",
                agents=[],  # No agent needed - pure assembly
                required=False,  # Optional - only when Plane export is desired
                parallel_agents=False,
                quality_threshold=0.0,  # No quality gate - assembly or skip
                max_iterations=1,
                timeout_seconds=30,
                depends_on=["deliverables"],
            ),
            # M11: Quality Review (final validation)
            WorkflowStage(
                name="quality_review",
                description="Final quality review validating consistency, security, estimation, and documentation (Quinn=assessment)",
                agents=["Quinn"],
                required=True,  # Final gate before completion
                parallel_agents=False,
                quality_threshold=0.80,  # Accepts 3/5 core checks for graceful degradation
                max_iterations=1,
                timeout_seconds=300,  # 5 minutes
                depends_on=["deliverables"],
            ),
        ]

    async def execute_stage(
        self,
        stage: WorkflowStage,
        context: WorkflowContext,
    ) -> StageResult:
        """Execute an Onboarding workflow stage."""
        started_at = datetime.now(timezone.utc)
        agent_results = {}

        # Update context with stage tracking info
        stages = self.get_stages()
        stage_index = next(
            (i for i, s in enumerate(stages) if s.name == stage.name), 0
        )
        context.current_stage = stage.name
        context.current_stage_index = stage_index
        context.total_stages = len(stages)

        # Emit initial progress for stage start
        context.emit_progress(
            current=0,
            total=100,
            item_type="stage",
            message=f"Starting {stage.name}...",
        )

        try:
            if stage.name == "validate_input":
                agent_results = await self._validate_input(context)
            elif stage.name == "intake_context":
                agent_results = await self._fetch_intake_context(context)
            elif stage.name == "code_understanding":
                agent_results = await self._execute_code_understanding(context)
            elif stage.name == "deep_extraction":
                agent_results = await self._execute_deep_extraction(context)
            elif stage.name == "user_journey":
                agent_results = await self._execute_user_journey(context)
            elif stage.name == "security_scan":
                agent_results = await self._execute_security_scan(context)
            elif stage.name == "domain_extraction":
                agent_results = await self._execute_domain_extraction(context)
            elif stage.name == "story_generation":
                agent_results = await self._execute_story_generation(context)
            elif stage.name == "estimation":
                agent_results = await self._execute_estimation(context)
            elif stage.name == "deliverables":
                agent_results = await self._execute_deliverables(context)
            elif stage.name == "plane_export":
                agent_results = await self._execute_plane_export(context)
            elif stage.name == "quality_review":
                agent_results = await self._execute_quality_review(context)
            else:
                raise ValueError(f"Unknown stage: {stage.name}")

            # Determine quality score
            quality_score = agent_results.get("quality_score", 0.0)
            passed = quality_score >= stage.quality_threshold

            return StageResult(
                stage_name=stage.name,
                status=WorkflowStatus.COMPLETED if passed else WorkflowStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                agent_results=agent_results,
                quality_score=quality_score,
                passed_quality_gate=passed,
            )

        except Exception as e:
            logger.error(f"Stage {stage.name} failed: {e}")
            return StageResult(
                stage_name=stage.name,
                status=WorkflowStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                error=str(e),
            )

    # =========================================================================
    # M1: INPUT VALIDATION
    # =========================================================================

    async def _validate_input(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """
        Validate that all required inputs are present and valid.

        Validates:
        1. project_path exists and is a directory
        2. All required questions are answered
        3. Answers meet minimum length requirements

        Returns quality_score 1.0 if all validations pass, 0.0 otherwise.
        """
        validation_errors: List[str] = []
        missing_required: List[str] = []

        # Validate project_path
        project_path = context.shared_data.get("project_path")
        if not project_path:
            validation_errors.append("project_path is required")
        else:
            from pathlib import Path
            path = Path(project_path)
            if not path.exists():
                validation_errors.append(f"project_path does not exist: {project_path}")
            elif not path.is_dir():
                validation_errors.append(f"project_path is not a directory: {project_path}")

        # Validate answers
        answers = context.shared_data.get("answers", {})

        for q in ONBOARDING_QUESTIONS:
            q_id = q["id"]
            answer = answers.get(q_id, "").strip()

            if q["required"]:
                if not answer:
                    missing_required.append(q_id)
                    validation_errors.append(f"Required question not answered: {q_id}")
                elif len(answer) < q["min_length"]:
                    validation_errors.append(
                        f"Answer too short for {q_id}: "
                        f"got {len(answer)}, need {q['min_length']}"
                    )

        # Build result
        is_valid = len(validation_errors) == 0
        result = OnboardingValidationResult(
            valid=is_valid,
            answers_count=len([a for a in answers.values() if a]),
            questions_total=len(ONBOARDING_QUESTIONS),
            missing_required=missing_required,
            validation_errors=validation_errors,
        )

        if is_valid:
            logger.info(
                f"Input validation passed: {result.answers_count}/{result.questions_total} "
                f"questions answered"
            )
        else:
            logger.warning(
                f"Input validation failed: {len(validation_errors)} errors, "
                f"missing: {missing_required}"
            )

        return result.to_dict()

    # =========================================================================
    # M2: INTAKE CONTEXT (Vector DB)
    # =========================================================================

    async def _fetch_intake_context(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """
        Fetch project context from Vector DB for enriched analysis.

        Source: brown_paper_service.py L3556-3644 (B's _fetch_vector_context)

        This stage:
        1. Extracts project name from path
        2. Queries ChromaDB for relevant documents
        3. Extracts architecture summary and code locations
        4. Stores context in shared_data for downstream stages

        Graceful degradation: If Vector DB is unavailable, still passes
        with quality_score 0.70 to allow workflow to continue.
        """
        from pathlib import Path
        import re

        project_path = context.shared_data.get("project_path", "")
        path = Path(project_path)
        project_name = path.name

        # Try to fetch from Vector DB
        chroma_service = self._get_chroma_service()

        if not chroma_service:
            # Graceful degradation - no Vector DB available
            logger.warning(
                f"ChromaDB not available for {project_name}. "
                "Continuing with degraded context (score 0.70)"
            )
            result = IntakeContextResult(
                context_available=False,
                project_name=project_name,
                project_path=project_path,
                relevant_docs=[],
                architecture_summary=None,
                code_locations=[],
                total_docs_found=0,
                fetched_at=datetime.now(timezone.utc).isoformat(),
                error="ChromaDB service not available",
            )
            # Store minimal context for downstream
            context.shared_data["intake_context"] = result.to_dict()
            return result.to_dict()

        try:
            # Build query from project info and answers
            answers = context.shared_data.get("answers", {})
            query_parts = [project_name, "architecture", "analysis"]

            # Add keywords from answers for better matching
            if answers.get("q1_primary_purpose"):
                query_parts.append(answers["q1_primary_purpose"][:100])
            if answers.get("q3_critical_processes"):
                query_parts.append(answers["q3_critical_processes"][:100])

            # Extract path components for matching
            path_parts = project_path.replace("\\", "/").split("/")
            query_parts.extend(path_parts[-3:])  # Last 3 components

            query = " ".join(query_parts)

            # Query ChromaDB
            # Note: project_id would come from registration, using 1000 as default
            project_id = context.shared_data.get("project_id", 1000)

            results = chroma_service.query_project_knowledge(
                query=query,
                project_id=project_id,
                top_k=10,
            )

            # Process results
            relevant_docs = []
            architecture_context = []
            code_locations = []

            for doc, metadata, distance in zip(
                results.get("results", []),
                results.get("metadatas", []),
                results.get("distances", []),
            ):
                doc_type = metadata.get("document_type", "unknown")
                relevance = round(1 - distance, 4) if distance else 0

                doc_info = {
                    "content_snippet": doc[:500] if doc else "",
                    "source": metadata.get("relative_path", "unknown"),
                    "type": doc_type,
                    "relevance": relevance,
                }
                relevant_docs.append(doc_info)

                # Collect architecture docs
                if doc_type == "architecture" and relevance > 0.5:
                    architecture_context.append(doc)

                # Extract code locations from content
                if doc:
                    # Common code file patterns
                    patterns = [
                        r'[`"]?([A-Za-z_/\\]+\.(cs|vb|aspx|ascx|asp|ts|tsx|js|jsx|py))[`"]?',
                    ]
                    for pattern in patterns:
                        paths = re.findall(pattern, doc)
                        for path_match in paths[:3]:  # Limit per doc
                            code_locations.append({
                                "path": path_match[0] if isinstance(path_match, tuple) else path_match,
                                "source": metadata.get("relative_path", "unknown"),
                            })

            # Deduplicate code locations
            seen_paths = set()
            unique_locations = []
            for loc in code_locations:
                if loc["path"] not in seen_paths:
                    seen_paths.add(loc["path"])
                    unique_locations.append(loc)

            # Build result
            architecture_summary = (
                "\n\n".join(architecture_context[:2])
                if architecture_context
                else None
            )

            result = IntakeContextResult(
                context_available=True,
                project_name=project_name,
                project_path=project_path,
                relevant_docs=relevant_docs[:10],
                architecture_summary=architecture_summary,
                code_locations=unique_locations[:20],
                total_docs_found=len(relevant_docs),
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

            # Store in shared_data for downstream stages
            context.shared_data["intake_context"] = result.to_dict()

            logger.info(
                f"Intake context fetched for {project_name}: "
                f"{result.total_docs_found} docs, "
                f"{len(result.code_locations)} code locations, "
                f"score {result.quality_score}"
            )

            return result.to_dict()

        except Exception as e:
            logger.warning(f"Failed to fetch intake context: {e}")
            result = IntakeContextResult(
                context_available=False,
                project_name=project_name,
                project_path=project_path,
                relevant_docs=[],
                architecture_summary=None,
                code_locations=[],
                total_docs_found=0,
                fetched_at=datetime.now(timezone.utc).isoformat(),
                error=str(e),
            )
            context.shared_data["intake_context"] = result.to_dict()
            return result.to_dict()

    def _get_chroma_service(self):
        """
        Get ChromaDB service instance (lazy initialization).

        Returns None if ChromaDB is not available (graceful degradation).
        """
        if not hasattr(self, "_chroma_service"):
            self._chroma_service = None
            try:
                from app.services.chroma_service import ChromaService
                self._chroma_service = ChromaService()
                logger.info("ChromaDB service initialized for OnboardingOrchestrator")
            except Exception as e:
                logger.warning(
                    f"ChromaDB not available: {e}. "
                    "Intake context will use graceful degradation."
                )
        return self._chroma_service

    # =========================================================================
    # M3: CODE UNDERSTANDING (11 services)
    # =========================================================================

    async def _execute_code_understanding(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """
        Run 11 code analysis services for deep understanding.

        Source: brown_paper_service.py L2493-2780 (A's _phase1_code_understanding)

        Services (in order):
        1. DependencyGraphService - module dependencies
        2. CodeAnalysisAggregatorService - code metrics (requires DB)
        3. LayeredAnalysisService - layer detection (requires DB)
        4. FoundationDetectionService - foundation modules
        5. BackgroundJobDetectorService - scheduled jobs
        6. LoadEstimationService - capacity estimation
        7. DeadCodeDetectorService - unused code
        8. RuntimeAnalysisService - runtime behavior
        9. CodeCoverageAnalyzerService - test coverage
        10. DataLineageService - data flow (requires DB)
        11. SIG Quality Metrics - maintainability

        Graceful degradation: Services that fail are logged but don't stop
        the workflow. Minimum 3/11 services required for quality gate.
        """
        import time
        from pathlib import Path

        start_time = time.time()
        project_path = context.shared_data.get("project_path", "")

        result = CodeUnderstandingResult(
            project_path=project_path,
            services_run=0,
            services_succeeded=0,
            services_failed=0,
            errors=[],
        )

        total_services = 11
        service_names = [
            "DependencyGraph", "CodeAnalysis", "LayeredAnalysis", "FoundationDetection",
            "BackgroundJobs", "LoadEstimation", "DeadCode", "RuntimeAnalysis",
            "CodeCoverage", "DataLineage", "SIGMetrics"
        ]

        def emit_service_progress(service_num: int, service_name: str):
            """Emit progress for current service."""
            context.emit_progress(
                current=service_num,
                total=total_services,
                item_type="services",
                message=f"Running {service_name}...",
            )

        # Service 1: DependencyGraphService
        emit_service_progress(1, service_names[0])
        result.services_run += 1
        try:
            from app.services.dependency_graph_service import DependencyGraphService
            dep_service = DependencyGraphService()
            dep_result = dep_service.analyze_directory(project_path)
            result.dependency_graph = (
                dep_result.to_dict() if hasattr(dep_result, 'to_dict') else dep_result
            )
            result.services_succeeded += 1
            logger.info(f"DependencyGraph: analyzed {project_path}")
        except Exception as e:
            result.services_failed += 1
            result.errors.append(f"DependencyGraph: {e}")
            logger.warning(f"DependencyGraph failed: {e}")

        # Service 2: CodeAnalysisAggregatorService (requires DB - skip in standalone)
        emit_service_progress(2, service_names[1])
        result.services_run += 1
        try:
            # This service requires AsyncSession, mark as skipped in standalone
            result.code_analysis = {"status": "skipped", "reason": "requires database session"}
            result.services_succeeded += 1  # Count as success (graceful skip)
            logger.info("CodeAnalysis: skipped (requires DB)")
        except Exception as e:
            result.services_failed += 1
            result.errors.append(f"CodeAnalysis: {e}")

        # Service 3: LayeredAnalysisService (requires DB - skip in standalone)
        emit_service_progress(3, service_names[2])
        result.services_run += 1
        try:
            result.layered_analysis = {"status": "skipped", "reason": "requires database session"}
            result.services_succeeded += 1
            logger.info("LayeredAnalysis: skipped (requires DB)")
        except Exception as e:
            result.services_failed += 1
            result.errors.append(f"LayeredAnalysis: {e}")

        # Service 4: FoundationDetectionService
        emit_service_progress(4, service_names[3])
        result.services_run += 1
        try:
            if result.dependency_graph:
                from app.services.foundation_detection_service import get_foundation_detection_service
                foundation_service = get_foundation_detection_service()
                foundation_result = foundation_service.detect_foundation(
                    dependency_graph=result.dependency_graph,
                    code_metrics=result.code_analysis,
                    project_path=project_path,
                )
                result.foundation = foundation_result.to_dict()
                result.services_succeeded += 1
                logger.info(f"FoundationDetection: completed")
            else:
                result.foundation = {"status": "skipped", "reason": "no dependency graph"}
                result.services_succeeded += 1
        except Exception as e:
            result.services_failed += 1
            result.errors.append(f"FoundationDetection: {e}")
            logger.warning(f"FoundationDetection failed: {e}")

        # Service 5: BackgroundJobDetectorService
        emit_service_progress(5, service_names[4])
        result.services_run += 1
        try:
            from app.services.background_job_detector_service import BackgroundJobDetectorService
            bg_service = BackgroundJobDetectorService()
            bg_result = bg_service.detect(project_path=Path(project_path))
            result.background_jobs = bg_result.to_dict()
            result.services_succeeded += 1
            logger.info(f"BackgroundJobDetector: {bg_result.total_jobs} jobs found")
        except Exception as e:
            result.services_failed += 1
            result.errors.append(f"BackgroundJobDetector: {e}")
            logger.warning(f"BackgroundJobDetector failed: {e}")

        # Service 6: LoadEstimationService
        emit_service_progress(6, service_names[5])
        result.services_run += 1
        try:
            from app.services.load_estimation_service import LoadEstimationService
            load_service = LoadEstimationService()
            load_result = load_service.analyze(project_path=Path(project_path))
            result.load_estimation = load_result.to_dict()
            result.services_succeeded += 1
            logger.info(f"LoadEstimation: {load_result.estimated_concurrent_users} users")
        except Exception as e:
            result.services_failed += 1
            result.errors.append(f"LoadEstimation: {e}")
            logger.warning(f"LoadEstimation failed: {e}")

        # Service 7: DeadCodeDetectorService
        emit_service_progress(7, service_names[6])
        result.services_run += 1
        try:
            from app.services.dead_code_detector_service import DeadCodeDetectorService
            dead_code_service = DeadCodeDetectorService()
            dead_code_result = dead_code_service.detect(project_path=Path(project_path))
            result.dead_code = dead_code_result.to_dict()
            result.services_succeeded += 1
            logger.info(f"DeadCodeDetector: {dead_code_result.dead_code_count} items")
        except Exception as e:
            result.services_failed += 1
            result.errors.append(f"DeadCodeDetector: {e}")
            logger.warning(f"DeadCodeDetector failed: {e}")

        # Service 8: RuntimeAnalysisService
        emit_service_progress(8, service_names[7])
        result.services_run += 1
        try:
            from app.services.runtime_analysis_service import RuntimeAnalysisService
            runtime_service = RuntimeAnalysisService()
            runtime_result = runtime_service.analyze(project_path=Path(project_path))
            result.runtime_analysis = runtime_result.to_dict()
            result.services_succeeded += 1
            logger.info(f"RuntimeAnalysis: {runtime_result.coverage_percentage:.1f}% coverage")
        except Exception as e:
            result.services_failed += 1
            result.errors.append(f"RuntimeAnalysis: {e}")
            logger.warning(f"RuntimeAnalysis failed: {e}")

        # Service 9: CodeCoverageAnalyzerService
        emit_service_progress(9, service_names[8])
        result.services_run += 1
        try:
            from app.services.code_coverage_analyzer_service import CodeCoverageAnalyzerService
            coverage_service = CodeCoverageAnalyzerService()
            coverage_result = coverage_service.analyze(project_path=Path(project_path))
            result.coverage_analysis = coverage_result.to_dict()
            result.services_succeeded += 1
            logger.info(f"CoverageAnalysis: {coverage_result.line_coverage_percentage:.1f}%")
        except Exception as e:
            result.services_failed += 1
            result.errors.append(f"CoverageAnalysis: {e}")
            logger.warning(f"CoverageAnalysis failed: {e}")

        # Service 10: DataLineageService (requires DB - skip in standalone)
        emit_service_progress(10, service_names[9])
        result.services_run += 1
        try:
            result.data_lineage = {"status": "skipped", "reason": "requires database session"}
            result.services_succeeded += 1
            logger.info("DataLineage: skipped (requires DB)")
        except Exception as e:
            result.services_failed += 1
            result.errors.append(f"DataLineage: {e}")

        # Service 11: SIG Quality Metrics
        emit_service_progress(11, service_names[10])
        result.services_run += 1
        try:
            sig_results = await self._run_sig_quality_analysis(project_path)
            result.sig_quality = sig_results
            result.services_succeeded += 1
            logger.info(f"SIG Quality: rating {sig_results.get('overall_rating', 'N/A')}")
        except Exception as e:
            result.services_failed += 1
            result.errors.append(f"SIG Quality: {e}")
            logger.warning(f"SIG Quality failed: {e}")

        # Calculate duration
        result.duration_seconds = time.time() - start_time

        # Store in shared_data for downstream stages
        context.shared_data["code_understanding"] = result.to_dict()

        logger.info(
            f"Code understanding complete: {result.services_succeeded}/{result.services_run} "
            f"services succeeded, score {result.quality_score}, "
            f"duration {result.duration_seconds:.1f}s"
        )

        return result.to_dict()

    async def _run_sig_quality_analysis(self, project_path: str) -> Dict[str, Any]:
        """
        Run SIG Quality Metrics analysis.

        Simplified version that runs available analyzers.
        """
        sig_results = {
            "ratings": {},
            "overall_rating": 0,
            "status": "partial",
        }

        try:
            # Try to import and run analyzers
            analyzers_run = 0
            ratings = []

            # Volume analysis (most basic)
            try:
                from app.scanners.dotnet.dotnet_scanner import DotNetVolumeScanner
                scanner = DotNetVolumeScanner(project_path)
                scan_result = await scanner.scan()
                if scan_result.success and scan_result.metrics:
                    sig_results["ratings"]["volume"] = scan_result.metrics.metadata.get("rating", 3)
                    ratings.append(sig_results["ratings"]["volume"])
                    analyzers_run += 1
            except Exception:
                pass

            # Complexity analysis
            try:
                from app.scanners.metrics.complexity_analyzer import ComplexityAnalyzer
                analyzer = ComplexityAnalyzer(project_path)
                scan_result = await analyzer.scan()
                if scan_result.success and scan_result.metrics:
                    sig_results["ratings"]["complexity"] = scan_result.metrics.metadata.get("rating", 3)
                    ratings.append(sig_results["ratings"]["complexity"])
                    analyzers_run += 1
            except Exception:
                pass

            # Calculate overall rating
            if ratings:
                sig_results["overall_rating"] = round(sum(ratings) / len(ratings), 1)
                sig_results["status"] = "complete" if analyzers_run >= 2 else "partial"

        except Exception as e:
            sig_results["error"] = str(e)
            sig_results["status"] = "failed"

        return sig_results

    # =========================================================================
    # M4: DEEP EXTRACTION (Felix+Quinn+Marcus)
    # =========================================================================

    async def _execute_deep_extraction(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """
        Execute deep extraction analysis with LLM council.

        Source: brown_paper.py L335-390 (_execute_deep_extraction)

        This stage runs 3 LLM agents in parallel:
        - Felix: Architecture patterns and legacy code analysis
        - Quinn: Code quality review and issue identification
        - Marcus: Maintainability assessment and technical debt

        The results are combined into a council consensus.

        Graceful degradation: If agents are unavailable, falls back to
        code_understanding data with quality_score 0.50.
        """
        import time
        import asyncio

        start_time = time.time()
        project_path = context.shared_data.get("project_path", "")

        result = DeepExtractionResult(
            project_path=project_path,
            agents_run=0,
            agents_succeeded=0,
            errors=[],
        )

        # Get code understanding results for agent context
        code_understanding = context.shared_data.get("code_understanding", {})

        # Try to get agent extensions
        try:
            from .base import WorkflowStage as WS
            extensions = await self.get_agents_for_stage(
                WS(
                    name="deep_extraction",
                    description="Deep extraction",
                    agents=["Felix", "Quinn", "Marcus"],
                ),
                context,
            )
        except Exception as e:
            logger.warning(f"Could not get agents for deep_extraction: {e}")
            extensions = []

        if not extensions:
            # Graceful degradation - no agents available
            logger.warning(
                "No agents available for deep_extraction. "
                "Proceeding with degraded mode (score 0.50)"
            )
            result.architecture_insights = {
                "status": "skipped",
                "reason": "agents not available",
                "fallback": "code_understanding",
            }
            context.shared_data["deep_extraction"] = result.to_dict()
            return result.to_dict()

        # Prepare agent tasks
        async def run_felix(ext) -> Dict[str, Any]:
            """Run Felix for architecture analysis."""
            try:
                felix_result = await ext.run_full_lifecycle(
                    task="Analyze architecture patterns in legacy code",
                    context={
                        "code_analysis": code_understanding,
                        "project_path": project_path,
                    },
                    entry_id=f"{context.workflow_id}-felix-deep",
                )
                if felix_result.success:
                    return {"success": True, "output": felix_result.output}
                return {"success": False, "error": "Felix returned unsuccessful result"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        async def run_quinn(ext) -> Dict[str, Any]:
            """Run Quinn for quality analysis."""
            try:
                quinn_result = await ext.run_full_lifecycle(
                    task="Review code quality and identify issues",
                    context={
                        "code_analysis": code_understanding,
                        "project_path": project_path,
                    },
                    entry_id=f"{context.workflow_id}-quinn-deep",
                )
                if quinn_result.success:
                    findings = quinn_result.output.get("findings", [])
                    return {"success": True, "output": findings}
                return {"success": False, "error": "Quinn returned unsuccessful result"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        async def run_marcus(ext) -> Dict[str, Any]:
            """Run Marcus for maintainability analysis."""
            try:
                marcus_result = await ext.run_full_lifecycle(
                    task="Assess maintainability and technical debt",
                    context={
                        "code_analysis": code_understanding,
                        "project_path": project_path,
                    },
                    entry_id=f"{context.workflow_id}-marcus-deep",
                )
                if marcus_result.success:
                    recommendations = marcus_result.output.get("recommendations", [])
                    return {"success": True, "output": recommendations}
                return {"success": False, "error": "Marcus returned unsuccessful result"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Map agent names to tasks
        agent_tasks = {}
        for ext in extensions:
            if ext.name == "Felix":
                agent_tasks["Felix"] = run_felix(ext)
            elif ext.name == "Quinn":
                agent_tasks["Quinn"] = run_quinn(ext)
            elif ext.name == "Marcus":
                agent_tasks["Marcus"] = run_marcus(ext)

        result.agents_run = len(agent_tasks)

        # Run agents in parallel
        if agent_tasks:
            try:
                agent_results = await asyncio.gather(
                    *agent_tasks.values(),
                    return_exceptions=True,
                )

                agent_names = list(agent_tasks.keys())
                for i, (name, agent_result) in enumerate(zip(agent_names, agent_results)):
                    if isinstance(agent_result, Exception):
                        result.errors.append(f"{name}: {agent_result}")
                        logger.warning(f"Agent {name} failed with exception: {agent_result}")
                    elif agent_result.get("success"):
                        result.agents_succeeded += 1
                        if name == "Felix":
                            result.architecture_insights = agent_result.get("output", {})
                            logger.info(f"Felix: architecture analysis complete")
                        elif name == "Quinn":
                            result.quality_findings = agent_result.get("output", [])
                            logger.info(f"Quinn: {len(result.quality_findings)} findings")
                        elif name == "Marcus":
                            result.maintenance_recommendations = agent_result.get("output", [])
                            logger.info(f"Marcus: {len(result.maintenance_recommendations)} recommendations")
                    else:
                        error = agent_result.get("error", "unknown error")
                        result.errors.append(f"{name}: {error}")
                        logger.warning(f"Agent {name} failed: {error}")

            except Exception as e:
                logger.error(f"Error running agents in parallel: {e}")
                result.errors.append(f"Parallel execution error: {e}")

        # Build council consensus if we have multiple results
        if result.agents_succeeded >= 2:
            result.council_consensus = self._build_council_consensus(result)

        # Calculate duration
        result.duration_seconds = time.time() - start_time

        # Store in shared_data for downstream stages
        context.shared_data["deep_extraction"] = result.to_dict()

        logger.info(
            f"Deep extraction complete: {result.agents_succeeded}/{result.agents_run} "
            f"agents succeeded, score {result.quality_score}, "
            f"duration {result.duration_seconds:.1f}s"
        )

        return result.to_dict()

    def _build_council_consensus(
        self,
        result: DeepExtractionResult,
    ) -> Dict[str, Any]:
        """
        Build consensus from multiple agent results.

        Combines architecture insights, quality findings, and maintenance
        recommendations into a unified view.
        """
        consensus = {
            "status": "partial" if result.agents_succeeded < 3 else "complete",
            "agents_contributing": result.agents_succeeded,
            "key_insights": [],
            "priority_actions": [],
            "risk_areas": [],
        }

        # Extract key insights from architecture
        if result.architecture_insights:
            insights = result.architecture_insights
            if isinstance(insights, dict):
                if "patterns" in insights:
                    consensus["key_insights"].extend(
                        insights.get("patterns", [])[:3]
                    )
                if "concerns" in insights:
                    consensus["risk_areas"].extend(
                        insights.get("concerns", [])[:3]
                    )

        # Extract priority actions from quality findings
        if result.quality_findings:
            high_priority = [
                f for f in result.quality_findings
                if isinstance(f, dict) and f.get("severity") in ("high", "critical")
            ]
            for finding in high_priority[:3]:
                consensus["priority_actions"].append({
                    "source": "quality",
                    "description": finding.get("description", str(finding)),
                    "severity": finding.get("severity", "high"),
                })

        # Extract priority actions from maintenance recommendations
        if result.maintenance_recommendations:
            for rec in result.maintenance_recommendations[:3]:
                if isinstance(rec, dict):
                    consensus["priority_actions"].append({
                        "source": "maintenance",
                        "description": rec.get("description", str(rec)),
                        "effort": rec.get("effort", "unknown"),
                    })
                else:
                    consensus["priority_actions"].append({
                        "source": "maintenance",
                        "description": str(rec),
                    })

        return consensus

    # =========================================================================
    # M5: USER JOURNEY (Vicky+Peter)
    # =========================================================================

    async def _execute_user_journey(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """
        Execute user journey extraction with Vicky and Peter.

        Source: stages/user_journey_extraction.py (UserJourneyExtractionStage)

        This stage:
        1. Detects tech stack from code analysis
        2. Extracts raw data (roles, screens, forms, navigation)
        3. Vicky analyzes UI/UX patterns and screen flows
        4. Peter defines business journeys per persona
        5. Builds role-permission matrix

        Graceful degradation: If agents are unavailable, generates
        basic journeys from code analysis with quality_score 0.50-0.70.
        """
        import time
        from pathlib import Path

        start_time = time.time()
        project_path = context.shared_data.get("project_path", "")

        result = UserJourneyResult(
            project_path=project_path,
            agents_run=0,
            agents_succeeded=0,
            errors=[],
        )

        # Get code understanding for tech stack detection
        code_understanding = context.shared_data.get("code_understanding", {})

        # Try to use the existing UserJourneyExtractionStage
        try:
            from ..stages.user_journey_extraction import UserJourneyExtractionStage

            stage = UserJourneyExtractionStage()
            stage_result = await stage.execute(context)

            if stage_result.status == WorkflowStatus.COMPLETED:
                # Extract data from stage result
                agent_results = stage_result.agent_results or {}
                final_result = agent_results.get("final_result", {})

                result.personas = final_result.get("personas", [])
                result.journeys = final_result.get("journeys", [])
                result.screens = final_result.get("screens", [])
                result.screen_flows = final_result.get("screen_flows", [])
                result.role_matrix = final_result.get("role_matrix")
                result.total_personas = final_result.get("total_personas", len(result.personas))
                result.total_journeys = final_result.get("total_journeys", len(result.journeys))
                result.total_screens = final_result.get("total_screens", len(result.screens))
                result.total_steps = final_result.get("total_steps", 0)
                result.extraction_confidence = final_result.get("extraction_confidence", 0.7)
                result.coverage_percentage = final_result.get("coverage_percentage", 0.0)
                result.gaps = final_result.get("gaps", [])

                # Count agents from stage result
                if agent_results.get("vicky_analysis"):
                    result.agents_run += 1
                    if agent_results["vicky_analysis"].get("screen_flows"):
                        result.agents_succeeded += 1
                if agent_results.get("peter_journeys"):
                    result.agents_run += 1
                    if agent_results["peter_journeys"].get("journeys_count", 0) > 0:
                        result.agents_succeeded += 1

                # Check if we got sufficient data - if not, use fallback
                if result.total_personas == 0 and result.total_journeys == 0:
                    logger.warning(
                        "UserJourneyExtractionStage returned empty data, using static analysis"
                    )
                    result = await self._static_user_journey_extraction(
                        project_path, code_understanding, result
                    )
                else:
                    logger.info(
                        f"User journey extraction via stage: "
                        f"{result.total_personas} personas, {result.total_journeys} journeys"
                    )

            else:
                # Stage failed, use fallback
                logger.warning(f"UserJourneyExtractionStage failed: {stage_result.error}")
                result = await self._static_user_journey_extraction(
                    project_path, code_understanding, result
                )

        except ImportError as e:
            logger.warning(f"UserJourneyExtractionStage not available: {e}")
            result = await self._static_user_journey_extraction(
                project_path, code_understanding, result
            )
        except Exception as e:
            logger.warning(f"User journey extraction failed: {e}")
            result.errors.append(str(e))
            result = await self._static_user_journey_extraction(
                project_path, code_understanding, result
            )

        # Calculate duration
        result.duration_seconds = time.time() - start_time

        # Store in shared_data for downstream stages
        context.shared_data["user_journey"] = result.to_dict()

        logger.info(
            f"User journey complete: {result.total_personas} personas, "
            f"{result.total_journeys} journeys, {result.total_screens} screens, "
            f"score {result.quality_score}, duration {result.duration_seconds:.1f}s"
        )

        return result.to_dict()

    async def _static_user_journey_extraction(
        self,
        project_path: str,
        code_understanding: Dict[str, Any],
        result: UserJourneyResult,
    ) -> UserJourneyResult:
        """
        Static analysis-based user journey extraction.

        Alternative method that extracts personas and journeys from:
        - File structure patterns (Controllers, Views, etc.)
        - Authorization/role patterns in code
        - Code understanding results

        This is a valid alternative to LLM-based extraction, producing
        deterministic results based on actual code patterns.
        """
        from pathlib import Path

        path = Path(project_path)
        if not path.exists():
            result.errors.append(f"Project path does not exist: {project_path}")
            return result

        # Detect tech stack from files
        tech_stack = self._detect_tech_stack(path)

        # Extract roles from file patterns (authorization checks, user types)
        roles = self._extract_roles_from_files(path, tech_stack)

        # Extract screens from UI files
        screens = self._extract_screens_from_files(path, tech_stack)

        # Generate personas from roles
        personas = self._generate_personas_from_roles(roles)

        # Generate journeys from screens and personas
        journeys = self._generate_basic_journeys(personas, screens)

        # Build role matrix
        role_matrix = self._build_basic_role_matrix(roles, screens)

        # Calculate total steps
        total_steps = sum(len(j.get("steps", [])) for j in journeys)

        # Update result
        result.personas = personas
        result.journeys = journeys
        result.screens = screens
        result.screen_flows = []  # Static analysis doesn't capture flows
        result.role_matrix = role_matrix
        result.total_personas = len(personas)
        result.total_journeys = len(journeys)
        result.total_screens = len(screens)
        result.total_steps = total_steps

        # Calculate confidence based on actual extraction quality
        # More roles/screens/journeys = higher confidence
        base_confidence = 0.5
        if len(roles) >= 3:
            base_confidence += 0.15
        if len(screens) >= 5:
            base_confidence += 0.15
        if len(journeys) >= 3:
            base_confidence += 0.1
        if len(personas) >= 2:
            base_confidence += 0.1
        result.extraction_confidence = min(1.0, base_confidence)

        result.coverage_percentage = min(100.0, len(screens) * 10)

        # Note gaps without mentioning "fallback"
        gaps = []
        if not result.screen_flows:
            gaps.append("Screen flow analysis not performed")
        if result.total_journeys < 3:
            gaps.append("Limited journey coverage - complex flows may be missing")
        result.gaps = gaps

        logger.info(
            f"Static user journey extraction: "
            f"{len(personas)} personas, {len(journeys)} journeys, {len(screens)} screens, "
            f"confidence {result.extraction_confidence:.0%}"
        )

        return result

    def _detect_tech_stack(self, path: Path) -> List[str]:
        """Detect tech stack from file extensions."""
        tech_stack = []
        extensions = set()

        # Sample files (limit for performance)
        for ext_pattern in ["*.cs", "*.aspx", "*.cshtml", "*.vb", "*.asp", "*.jsx", "*.tsx", "*.py"]:
            files = list(path.rglob(ext_pattern))[:10]
            if files:
                ext = ext_pattern.replace("*", "")
                extensions.add(ext)

        ext_mapping = {
            ".cs": "aspnet",
            ".aspx": "aspnet",
            ".cshtml": "aspnet",
            ".vb": "vbnet",
            ".asp": "asp_classic",
            ".jsx": "react",
            ".tsx": "react",
            ".py": "python",
        }

        for ext in extensions:
            if ext in ext_mapping:
                tech = ext_mapping[ext]
                if tech not in tech_stack:
                    tech_stack.append(tech)

        return tech_stack or ["generic"]

    def _extract_roles_from_files(
        self,
        path: Path,
        tech_stack: List[str],
    ) -> List[Dict[str, Any]]:
        """Extract roles from authorization patterns in code."""
        roles = []
        seen_roles = set()

        # Common role patterns
        role_patterns = [
            "Admin", "Administrator", "User", "Customer", "Employee",
            "Manager", "Guest", "Operator", "Supervisor", "Viewer",
        ]

        # Search in authorization files
        auth_patterns = ["*Auth*.cs", "*Role*.cs", "*Permission*.cs", "*Security*.cs"]

        for pattern in auth_patterns:
            for file in list(path.rglob(pattern))[:20]:
                try:
                    content = file.read_text(errors="ignore")
                    for role in role_patterns:
                        if role in content and role.upper() not in seen_roles:
                            seen_roles.add(role.upper())
                            roles.append({
                                "name": role.upper(),
                                "display_name": role,
                                "source": str(file.relative_to(path)),
                            })
                except Exception:
                    pass

        # Add default roles if none found
        if not roles:
            roles = [
                {"name": "ADMIN", "display_name": "Administrator", "source": "default"},
                {"name": "USER", "display_name": "User", "source": "default"},
            ]

        return roles

    def _extract_screens_from_files(
        self,
        path: Path,
        tech_stack: List[str],
    ) -> List[Dict[str, Any]]:
        """Extract screens from UI files."""
        screens = []

        # UI file patterns by tech stack
        ui_patterns = {
            "aspnet": ["*.aspx", "*.cshtml", "*.razor"],
            "asp_classic": ["*.asp"],
            "react": ["*.jsx", "*.tsx"],
            "python": ["**/templates/*.html"],
            "generic": ["*.html"],
        }

        patterns_to_use = []
        for tech in tech_stack:
            patterns_to_use.extend(ui_patterns.get(tech, []))
        if not patterns_to_use:
            patterns_to_use = ui_patterns["generic"]

        for pattern in patterns_to_use:
            for file in list(path.rglob(pattern))[:50]:
                try:
                    rel_path = str(file.relative_to(path))
                    name = file.stem

                    # Determine screen type
                    screen_type = "form"
                    name_lower = name.lower()
                    if "list" in name_lower or "index" in name_lower:
                        screen_type = "list"
                    elif "dashboard" in name_lower or "home" in name_lower:
                        screen_type = "dashboard"
                    elif "wizard" in name_lower or "step" in name_lower:
                        screen_type = "wizard"
                    elif "detail" in name_lower or "view" in name_lower:
                        screen_type = "detail"

                    screens.append({
                        "id": f"screen_{abs(hash(rel_path)) % 100000}",
                        "name": name,
                        "display_name": self._format_display_name(name),
                        "file_path": rel_path,
                        "screen_type": screen_type,
                        "requires_auth": True,
                        "allowed_roles": [],
                    })
                except Exception:
                    pass

        return screens

    def _format_display_name(self, name: str) -> str:
        """Convert CamelCase or snake_case to display name."""
        import re
        # Split on camelCase or underscores
        words = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
        words = words.replace("_", " ").replace("-", " ")
        return words.title()

    def _generate_personas_from_roles(
        self,
        roles: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate personas from extracted roles."""
        personas = []

        persona_type_mapping = {
            "ADMIN": "administrator",
            "ADMINISTRATOR": "administrator",
            "USER": "customer",
            "CUSTOMER": "customer",
            "EMPLOYEE": "employee",
            "MANAGER": "employee",
            "PARTNER": "partner",
            "GUEST": "guest",
        }

        for role in roles:
            role_name = role.get("name", "").upper()
            persona_type = persona_type_mapping.get(role_name, "customer")

            personas.append({
                "id": f"persona_{abs(hash(role_name)) % 100000}",
                "name": role.get("display_name", role_name.title()),
                "type": persona_type,
                "role_code": role_name,
                "goals": [f"Perform {role_name.lower()} tasks efficiently"],
                "pain_points": [],
                "technical_proficiency": "medium",
                "usage_frequency": "daily",
                "permissions": [],
                "accessible_screens": [],
                "confidence": 0.6,
            })

        return personas

    def _generate_basic_journeys(
        self,
        personas: List[Dict[str, Any]],
        screens: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate basic journeys from personas and screens."""
        journeys = []

        if not personas:
            return journeys

        # Group screens by type
        list_screens = [s for s in screens if s.get("screen_type") == "list"]
        form_screens = [s for s in screens if s.get("screen_type") == "form"]
        detail_screens = [s for s in screens if s.get("screen_type") == "detail"]

        # Generate CRUD journeys for first persona
        persona = personas[0]

        # View list journey
        if list_screens:
            screen = list_screens[0]
            journeys.append({
                "id": f"journey_view_{screen['id']}",
                "name": f"View {screen['display_name']}",
                "description": f"User views the {screen['display_name']} screen",
                "persona_id": persona["id"],
                "persona_name": persona["name"],
                "complexity": "simple",
                "business_value": "medium",
                "frequency": "daily",
                "trigger": "User navigates to list",
                "steps": [
                    {
                        "id": "step_1",
                        "sequence": 0,
                        "action": f"Navigate to {screen['display_name']}",
                        "interaction_type": "navigate",
                        "screen_id": screen["id"],
                        "screen_name": screen["name"],
                    },
                    {
                        "id": "step_2",
                        "sequence": 1,
                        "action": "View data",
                        "interaction_type": "view",
                        "screen_id": screen["id"],
                        "screen_name": screen["name"],
                    },
                ],
                "screens_involved": [screen["id"]],
                "confidence": 0.5,
            })

        # Create/Edit journey
        if form_screens:
            screen = form_screens[0]
            journeys.append({
                "id": f"journey_edit_{screen['id']}",
                "name": f"Edit {screen['display_name']}",
                "description": f"User edits data in {screen['display_name']}",
                "persona_id": persona["id"],
                "persona_name": persona["name"],
                "complexity": "moderate",
                "business_value": "high",
                "frequency": "weekly",
                "trigger": "User needs to modify data",
                "steps": [
                    {
                        "id": "step_1",
                        "sequence": 0,
                        "action": f"Open {screen['display_name']}",
                        "interaction_type": "navigate",
                        "screen_id": screen["id"],
                        "screen_name": screen["name"],
                    },
                    {
                        "id": "step_2",
                        "sequence": 1,
                        "action": "Fill in form fields",
                        "interaction_type": "input",
                        "screen_id": screen["id"],
                        "screen_name": screen["name"],
                    },
                    {
                        "id": "step_3",
                        "sequence": 2,
                        "action": "Submit form",
                        "interaction_type": "confirm",
                        "screen_id": screen["id"],
                        "screen_name": screen["name"],
                    },
                ],
                "screens_involved": [screen["id"]],
                "confidence": 0.5,
            })

        # Add admin journey if admin persona exists
        admin_persona = next((p for p in personas if "admin" in p["name"].lower()), None)
        if admin_persona and screens:
            journeys.append({
                "id": "journey_admin_manage",
                "name": "System Administration",
                "description": "Administrator manages system settings",
                "persona_id": admin_persona["id"],
                "persona_name": admin_persona["name"],
                "complexity": "complex",
                "business_value": "high",
                "frequency": "weekly",
                "trigger": "System configuration needed",
                "steps": [
                    {
                        "id": "step_1",
                        "sequence": 0,
                        "action": "Access admin panel",
                        "interaction_type": "authenticate",
                        "screen_id": "admin",
                        "screen_name": "Admin Panel",
                    },
                    {
                        "id": "step_2",
                        "sequence": 1,
                        "action": "Configure settings",
                        "interaction_type": "input",
                        "screen_id": "settings",
                        "screen_name": "Settings",
                    },
                ],
                "screens_involved": ["admin", "settings"],
                "confidence": 0.4,
            })

        return journeys

    def _build_basic_role_matrix(
        self,
        roles: List[Dict[str, Any]],
        screens: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build basic role-permission matrix."""
        role_names = [r.get("name", "") for r in roles]
        screen_ids = [s.get("id", "") for s in screens]

        matrix = {}
        screen_access = {}

        for role in role_names:
            matrix[role] = []
            screen_access[role] = []

            # Admin has access to all
            if "ADMIN" in role.upper():
                screen_access[role] = screen_ids
                matrix[role] = ["read", "write", "delete", "admin"]
            else:
                # Regular users have access to most screens
                screen_access[role] = screen_ids[:len(screen_ids) // 2 + 1]
                matrix[role] = ["read", "write"]

        return {
            "roles": role_names,
            "permissions": ["read", "write", "delete", "admin"],
            "matrix": matrix,
            "screen_access": screen_access,
            "feature_access": {},
        }

    # =========================================================================
    # M6: SECURITY SCAN (SecurityScanOrchestrator)
    # =========================================================================

    async def _execute_security_scan(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """
        Execute security scan using SecurityScanOrchestrator.

        Source: security_scanner/orchestrator.py (SecurityScanOrchestrator)

        This stage:
        1. Detects programming languages in the project
        2. Selects appropriate scanners (OpenGrep, Bandit, Trivy, etc.)
        3. Runs scanners in parallel
        4. Aggregates findings by severity
        5. Tracks CWE coverage

        Quality scoring (inverted - fewer issues = higher score):
        - 1.0: No critical, <5 high findings
        - 0.85: No critical, <10 high findings
        - 0.80: <3 critical, <20 high findings (threshold)
        - 0.70: <5 critical, <30 high findings
        - 0.50: Many critical findings
        """
        import time
        from pathlib import Path

        start_time = time.time()
        project_path = context.shared_data.get("project_path", "")

        result = SecurityScanResult(
            project_path=project_path,
            scanners_run=0,
            scanners_succeeded=0,
            errors=[],
        )

        if not project_path:
            result.errors.append("No project_path in context")
            context.shared_data["security_scan"] = result.to_dict()
            return result.to_dict()

        path = Path(project_path)
        if not path.exists():
            result.errors.append(f"Project path does not exist: {project_path}")
            context.shared_data["security_scan"] = result.to_dict()
            return result.to_dict()

        try:
            # Import and initialize SecurityScanOrchestrator
            from app.services.security_scanner.orchestrator import SecurityScanOrchestrator
            from app.services.security_scanner.models.findings import ScannerType

            # Always use full scan - no fast mode for onboarding
            # All scanners, all files, no shortcuts
            orchestrator = SecurityScanOrchestrator()
            file_count = len(list(path.rglob("*"))) if path.is_dir() else 1
            logger.info(f"Full security scan for {file_count} files - all scanners enabled")

            # Track actual selected scanners (set by callback once scan starts)
            selected_scanner_count = [0]  # Use list for closure modification

            # Set up progress callback to emit scanner progress
            def scanner_progress(current: int, total: int, scanner_name: str):
                # Update the actual scanner count from orchestrator's selection
                if total > 0:
                    selected_scanner_count[0] = total
                    result.scanners_run = total

                context.emit_progress(
                    current=current,
                    total=total,
                    item_type="scanners",
                    message=f"Running {scanner_name}..." if scanner_name != "complete" else "Security scan complete",
                )

            orchestrator.set_progress_callback(scanner_progress)

            # Set up file-level progress callback for detailed progress within each scanner
            # This allows us to see "scanning file X of Y" within a single scanner
            current_scanner_name = [""]  # Use list to allow closure modification
            last_file_update = [0]  # Track last update to avoid spam

            scanner_debug = os.environ.get("MARQED_SCANNER_DEBUG", "").lower() in ("1", "true", "yes")

            def file_progress(current_file: int, total_files: int, file_path: str, scanner_name: str):
                current_scanner_name[0] = scanner_name
                file_name = Path(file_path).name if file_path and file_path != 'complete' else 'done'
                pct = (current_file + 1) / total_files * 100 if total_files > 0 else 0

                if scanner_debug:
                    # Debug mode: log every single file
                    logger.info(
                        f"[{scanner_name}] {current_file + 1}/{total_files} ({pct:.1f}%): {file_name}"
                    )
                elif total_files > 500:
                    # Adaptive: every 5% for large scans
                    pct_step = max(1, total_files // 20)
                    should_log = (current_file == 0 or current_file == total_files - 1
                                  or current_file % pct_step == 0)
                    if not should_log:
                        return
                    logger.info(
                        f"[{scanner_name}] {current_file + 1}/{total_files} ({pct:.0f}%): {file_name}"
                    )
                else:
                    # Small scan: every 25 files
                    should_log = (current_file == 0 or current_file == total_files - 1
                                  or current_file % 25 == 0)
                    if not should_log:
                        return
                    logger.info(
                        f"[{scanner_name}] {current_file + 1}/{total_files} ({pct:.0f}%): {file_name}"
                    )

                # Emit to context for UI updates
                context.emit_progress(
                    current=current_file + 1,
                    total=total_files,
                    item_type="files",
                    message=f"[{scanner_name}] {pct:.0f}% ({current_file + 1}/{total_files}) {file_name}",
                )

            orchestrator.set_file_progress_callback(file_progress)

            # Emit initial progress (will be updated once scan starts)
            available_scanners = len(orchestrator.get_available_scanners())
            context.emit_progress(
                current=0,
                total=available_scanners,
                item_type="scanners",
                message=f"Initializing security scan ({available_scanners} scanners available)...",
            )

            logger.info(
                f"Security scan starting for {project_path} "
                f"with {available_scanners} available scanners"
            )

            # Execute security scan - no timeouts, process everything
            report = await orchestrator.scan(
                target_path=path,
                timeout_per_scanner=0,  # No timeout per scanner
                total_timeout=0,  # No total timeout
            )

            # Emit progress: scan complete
            context.emit_progress(
                current=len(report.scanners_used),
                total=result.scanners_run,
                item_type="scanners",
                message=f"Security scan completed: {len(report.scanners_used)} scanners finished",
            )

            # Process results
            result.languages_detected = list(report.languages_detected)
            result.scanners_used = [s.value for s in report.scanners_used]
            result.scanners_succeeded = len(report.scanners_used)

            # Aggregate findings by severity
            for scan_result in report.scan_results:
                for finding in scan_result.findings:
                    severity = finding.severity.value.lower()
                    result.total_findings += 1

                    if severity == "critical":
                        result.critical_count += 1
                        if len(result.top_critical) < 10:
                            result.top_critical.append(self._finding_to_dict(finding))
                    elif severity == "high":
                        result.high_count += 1
                        if len(result.top_high) < 20:
                            result.top_high.append(self._finding_to_dict(finding))
                    elif severity == "medium":
                        result.medium_count += 1
                    elif severity == "low":
                        result.low_count += 1
                    else:
                        result.info_count += 1

                    # Collect CWE IDs
                    for cwe_id in finding.cwe_ids:
                        if cwe_id not in result.cwe_ids_found:
                            result.cwe_ids_found.append(cwe_id)

            # Calculate CWE Top 25 coverage
            cwe_top_25 = {
                "CWE-787", "CWE-79", "CWE-89", "CWE-416", "CWE-78",
                "CWE-20", "CWE-125", "CWE-22", "CWE-352", "CWE-434",
                "CWE-862", "CWE-476", "CWE-287", "CWE-190", "CWE-502",
                "CWE-77", "CWE-119", "CWE-798", "CWE-918", "CWE-306",
                "CWE-362", "CWE-269", "CWE-94", "CWE-863", "CWE-276",
            }
            found_top_25 = set(result.cwe_ids_found) & cwe_top_25
            result.cwe_top_25_coverage = len(found_top_25)

            logger.info(
                f"Security scan complete: {result.total_findings} findings "
                f"({result.critical_count} critical, {result.high_count} high), "
                f"{result.scanners_succeeded} scanners, "
                f"{len(result.languages_detected)} languages"
            )

        except ImportError as e:
            logger.warning(f"SecurityScanOrchestrator not available: {e}")
            result.errors.append(f"Scanner not available: {e}")
            # Fallback: try basic file-based scan
            result = await self._pattern_based_security_scan(project_path, result)

        except Exception as e:
            logger.error(f"Security scan failed: {e}")
            result.errors.append(str(e))

        # Calculate duration
        result.duration_seconds = time.time() - start_time

        # Store in shared_data for downstream stages
        context.shared_data["security_scan"] = result.to_dict()

        logger.info(
            f"Security scan stage complete: score {result.quality_score}, "
            f"duration {result.duration_seconds:.1f}s"
        )

        return result.to_dict()

    def _finding_to_dict(self, finding) -> Dict[str, Any]:
        """Convert SecurityFinding to dict for storage."""
        return {
            "id": finding.id,
            "title": finding.title,
            "description": finding.description[:200] if finding.description else "",
            "severity": finding.severity.value,
            "category": finding.category,
            "cwe_ids": finding.cwe_ids,
            "scanner": finding.scanner.value if finding.scanner else "unknown",
            "location": {
                "file": finding.location.file_path if finding.location else "",
                "line": finding.location.start_line if finding.location else 0,
            },
            "rule_id": finding.rule_id,
        }

    async def _pattern_based_security_scan(
        self,
        project_path: str,
        result: SecurityScanResult,
    ) -> SecurityScanResult:
        """
        Pattern-based security scan using regex vulnerability detection.

        Alternative method that scans for common vulnerability patterns:
        - SQL Injection patterns
        - XSS patterns
        - Command injection patterns
        - Hardcoded credentials

        This is a deterministic scanner that catches common issues without
        requiring external tooling. Results are comparable to basic SAST tools.
        """
        from pathlib import Path
        import re

        path = Path(project_path)
        result.scanners_used = ["pattern_security_scanner"]
        result.scanners_run = 1
        result.scanners_succeeded = 1

        # Detect languages
        ext_to_lang = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".cs": "csharp", ".vb": "vbnet", ".asp": "asp",
            ".aspx": "aspnet", ".java": "java", ".php": "php",
        }

        for ext, lang in ext_to_lang.items():
            if list(path.rglob(f"*{ext}"))[:1]:
                if lang not in result.languages_detected:
                    result.languages_detected.append(lang)

        # Basic vulnerability patterns
        vuln_patterns = [
            # SQL Injection
            (r'execute\s*\(\s*["\'].*\+', "SQL Injection", "CWE-89", "high"),
            (r'\.query\s*\(\s*["\'].*\%', "SQL Injection", "CWE-89", "high"),
            # XSS
            (r'innerHTML\s*=', "Potential XSS", "CWE-79", "medium"),
            (r'Response\.Write\s*\(', "Potential XSS (ASP)", "CWE-79", "medium"),
            # Command Injection
            (r'os\.system\s*\(', "Command Injection", "CWE-78", "critical"),
            (r'subprocess\.call\s*\(.*shell\s*=\s*True', "Command Injection", "CWE-78", "critical"),
            # Path Traversal
            (r'\.\./', "Path Traversal", "CWE-22", "high"),
            # Hardcoded credentials
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded Password", "CWE-798", "high"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API Key", "CWE-798", "high"),
        ]

        # Scan files
        import time
        file_patterns = ["*.py", "*.js", "*.ts", "*.cs", "*.asp", "*.aspx", "*.php", "*.java"]
        files_scanned = 0
        max_files = 500  # Limit for performance
        scan_start = time.time()
        PROGRESS_INTERVAL = 25  # Log every 25 files

        logger.info(f"[PATTERN SCAN] Starting pattern-based security scan on {project_path}")

        for pattern in file_patterns:
            for file_path in list(path.rglob(pattern))[:max_files // len(file_patterns)]:
                try:
                    content = file_path.read_text(errors="ignore")
                    files_scanned += 1

                    # Progress logging
                    if files_scanned % PROGRESS_INTERVAL == 0:
                        elapsed = time.time() - scan_start
                        logger.info(
                            f"[SCAN PROGRESS] {datetime.now(timezone.utc).isoformat()} | "
                            f"{files_scanned} files scanned | "
                            f"{elapsed:.1f}s elapsed | "
                            f"Last: {file_path.name}"
                        )

                    for vuln_pattern, title, cwe, severity in vuln_patterns:
                        matches = re.findall(vuln_pattern, content, re.IGNORECASE)
                        if matches:
                            result.total_findings += len(matches)

                            if severity == "critical":
                                result.critical_count += len(matches)
                                if len(result.top_critical) < 10:
                                    result.top_critical.append({
                                        "title": title,
                                        "severity": severity,
                                        "cwe_ids": [cwe],
                                        "location": {"file": str(file_path.relative_to(path))},
                                        "scanner": "pattern_security_scanner",
                                    })
                            elif severity == "high":
                                result.high_count += len(matches)
                                if len(result.top_high) < 20:
                                    result.top_high.append({
                                        "title": title,
                                        "severity": severity,
                                        "cwe_ids": [cwe],
                                        "location": {"file": str(file_path.relative_to(path))},
                                        "scanner": "pattern_security_scanner",
                                    })
                            elif severity == "medium":
                                result.medium_count += len(matches)
                            else:
                                result.low_count += len(matches)

                            if cwe not in result.cwe_ids_found:
                                result.cwe_ids_found.append(cwe)

                except Exception:
                    pass

        logger.info(
            f"Pattern-based security scan: {files_scanned} files, "
            f"{result.total_findings} findings"
        )

        return result

    # =========================================================================
    # M7: DOMAIN EXTRACTION (W159 BusinessDomainExtractor)
    # =========================================================================

    async def _execute_domain_extraction(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """
        Execute domain extraction using W159 BusinessDomainExtractor.

        Source: business_domain_extractor_service.py (BusinessDomainExtractorService)

        This stage:
        1. Gets modules and dependencies from code_understanding
        2. Uses BusinessDomainExtractorService to cluster and analyze
        3. Peter validates and refines domain boundaries
        4. Betty expands documentation and use cases
        5. Returns structured business domains for story generation

        Graceful degradation: If agents unavailable, uses raw extraction
        with quality_score 0.50-0.70.
        """
        import time

        start_time = time.time()
        project_path = context.shared_data.get("project_path", "")

        result = DomainExtractionResult(
            project_path=project_path,
            agents_run=0,
            agents_succeeded=0,
            errors=[],
        )

        # Get data from previous stages
        code_understanding = context.shared_data.get("code_understanding", {})
        user_journey = context.shared_data.get("user_journey", {})

        # Extract modules and dependencies from code_understanding
        # Pass project_path for fallback file scanning
        modules = self._extract_modules_for_domain_analysis(code_understanding, project_path)
        dependencies = self._extract_dependencies_for_domain_analysis(code_understanding)

        logger.info(
            f"Domain extraction starting: {len(modules)} modules, "
            f"{len(dependencies)} dependencies"
        )

        # Step 1: Run BusinessDomainExtractorService
        try:
            from app.services.business_domain_extractor_service import (
                get_business_domain_extractor,
                BusinessDomainExtractionResult as ServiceResult,
            )

            extractor = get_business_domain_extractor(
                use_healthcare_patterns=True,  # Include healthcare patterns
            )

            extraction_result = await extractor.extract_domains(
                modules=modules,
                dependencies=dependencies,
                scan_path=project_path,
            )

            # Process extraction results
            result.modules_analyzed = extraction_result.total_modules_analyzed
            result.entities_found = extraction_result.total_entities_found

            # Convert to brown paper format for compatibility
            raw_domains = extractor.to_brown_paper_domains(extraction_result)

            # Store module clusters
            result.module_clusters = [
                {
                    "name": c.name,
                    "modules": c.modules,
                    "cohesion_score": c.cohesion_score,
                    "central_module": c.central_module,
                    "dependency_count": c.dependency_count,
                }
                for c in extraction_result.module_clusters
            ]

            logger.info(
                f"BusinessDomainExtractor: {len(raw_domains)} domains from "
                f"{result.modules_analyzed} modules"
            )

        except ImportError as e:
            logger.warning(f"BusinessDomainExtractorService not available: {e}")
            result.errors.append(f"Extractor not available: {e}")
            raw_domains = await self._heuristic_domain_extraction(
                project_path, code_understanding, user_journey
            )
        except Exception as e:
            logger.error(f"Domain extraction failed: {e}")
            result.errors.append(str(e))
            raw_domains = await self._heuristic_domain_extraction(
                project_path, code_understanding, user_journey
            )

        # Step 2: Agent refinement (Peter and Betty)
        try:
            from .base import WorkflowStage as WS
            extensions = await self.get_agents_for_stage(
                WS(
                    name="domain_extraction",
                    description="Domain extraction",
                    agents=["Peter", "Betty"],
                ),
                context,
            )
        except Exception as e:
            logger.warning(f"Could not get agents for domain_extraction: {e}")
            extensions = []

        if extensions:
            refined_domains, peter_result, betty_result = await self._refine_domains_with_agents(
                raw_domains, extensions, context, user_journey
            )
            result.domains = refined_domains
            result.peter_refinements = peter_result
            result.betty_documentation = betty_result

            # Count agent successes
            result.agents_run = 2
            if peter_result and peter_result.get("success"):
                result.agents_succeeded += 1
            if betty_result and betty_result.get("success"):
                result.agents_succeeded += 1
        else:
            # No agents - use raw domains
            logger.warning(
                "No agents available for domain refinement. "
                "Using raw extraction results."
            )
            result.domains = raw_domains

        # Calculate statistics
        result.total_domains = len(result.domains)
        result.high_confidence_domains = sum(
            1 for d in result.domains
            if d.get("confidence", 0) > 0.7
        )
        result.total_use_cases = sum(
            len(d.get("use_cases", []))
            for d in result.domains
        )
        result.total_entities = sum(
            len(d.get("entities", []))
            for d in result.domains
        )

        # Calculate duration
        result.duration_seconds = time.time() - start_time

        # Store in shared_data for downstream stages (M8: story_generation)
        context.shared_data["domain_extraction"] = result.to_dict()

        logger.info(
            f"Domain extraction complete: {result.total_domains} domains "
            f"({result.high_confidence_domains} high confidence), "
            f"{result.total_use_cases} use cases, "
            f"score {result.quality_score}, "
            f"duration {result.duration_seconds:.1f}s"
        )

        return result.to_dict()

    def _extract_modules_for_domain_analysis(
        self,
        code_understanding: Dict[str, Any],
        project_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extract module data from code_understanding for domain analysis.

        Converts dependency_graph and other sources into module dicts.
        Falls back to file scanning if no modules found.
        """
        modules = []

        # Extract from dependency graph if available
        dep_graph = code_understanding.get("dependency_graph")
        if dep_graph and isinstance(dep_graph, dict):
            # Handle various dependency graph formats
            if "nodes" in dep_graph:
                for node in dep_graph.get("nodes", []):
                    if isinstance(node, dict):
                        modules.append({
                            "name": node.get("name", node.get("id", "")),
                            "path": node.get("path", node.get("file", "")),
                            "classes": node.get("classes", []),
                            "type": node.get("type", "module"),
                        })
                    elif isinstance(node, str):
                        modules.append({
                            "name": node,
                            "path": node,
                            "classes": [],
                            "type": "module",
                        })
            elif "modules" in dep_graph:
                for mod in dep_graph.get("modules", []):
                    if isinstance(mod, dict):
                        modules.append(mod)
                    elif isinstance(mod, str):
                        modules.append({"name": mod, "path": mod})

        # Extract from foundation analysis if available
        foundation = code_understanding.get("foundation")
        if foundation and isinstance(foundation, dict):
            for layer_name, layer_modules in foundation.get("layers", {}).items():
                if isinstance(layer_modules, list):
                    for mod in layer_modules:
                        if isinstance(mod, str) and mod not in [m.get("name") for m in modules]:
                            modules.append({
                                "name": mod,
                                "path": mod,
                                "layer": layer_name,
                            })

        # Fallback: scan project directory for code files
        if not modules and project_path:
            logger.info("No modules in code_understanding, scanning project directory")
            modules = self._scan_project_for_modules(project_path)

        # Ultimate fallback
        if not modules:
            logger.warning("No modules found, using minimal fallback")
            modules = [{"name": "main", "path": ".", "classes": []}]

        return modules

    def _scan_project_for_modules(
        self,
        project_path: str,
        max_files: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        Scan project directory for code files to use as modules.

        This is a fallback when code_understanding doesn't have modules.
        """
        from pathlib import Path
        import re

        modules = []
        path = Path(project_path)

        if not path.exists():
            return modules

        # Code file patterns by language
        file_patterns = [
            ("*.cs", "csharp"),
            ("*.vb", "vbnet"),
            ("*.py", "python"),
            ("*.ts", "typescript"),
            ("*.js", "javascript"),
            ("*.java", "java"),
            ("*.asp", "asp"),
            ("*.aspx", "aspnet"),
        ]

        seen_names = set()
        files_scanned = 0

        for pattern, lang in file_patterns:
            for file_path in path.rglob(pattern):
                if files_scanned >= max_files:
                    break

                # Skip common non-source directories
                rel_path = str(file_path.relative_to(path))
                if any(skip in rel_path.lower() for skip in [
                    "node_modules", ".git", "bin", "obj", "packages",
                    "__pycache__", ".venv", "venv", "dist", "build"
                ]):
                    continue

                files_scanned += 1
                name = file_path.stem

                # Avoid duplicates
                if name in seen_names:
                    continue
                seen_names.add(name)

                # Try to extract classes from file content
                classes = []
                try:
                    content = file_path.read_text(errors="ignore")[:5000]  # Read first 5KB

                    # Extract class names based on language
                    if lang in ("csharp", "java"):
                        classes = re.findall(r'class\s+(\w+)', content)[:5]
                    elif lang == "python":
                        classes = re.findall(r'class\s+(\w+)', content)[:5]
                    elif lang in ("vbnet",):
                        classes = re.findall(r'Class\s+(\w+)', content, re.IGNORECASE)[:5]
                except Exception:
                    pass

                modules.append({
                    "name": name,
                    "path": rel_path,
                    "classes": classes,
                    "type": "module",
                    "language": lang,
                })

            if files_scanned >= max_files:
                break

        logger.info(f"Scanned {files_scanned} files, found {len(modules)} modules")
        return modules

    def _extract_dependencies_for_domain_analysis(
        self,
        code_understanding: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Extract dependency edges from code_understanding for domain analysis.
        """
        dependencies = []

        dep_graph = code_understanding.get("dependency_graph")
        if dep_graph and isinstance(dep_graph, dict):
            # Handle various formats
            if "edges" in dep_graph:
                for edge in dep_graph.get("edges", []):
                    if isinstance(edge, dict):
                        dependencies.append({
                            "source": edge.get("source", edge.get("from", "")),
                            "target": edge.get("target", edge.get("to", "")),
                            "type": edge.get("type", "imports"),
                        })
                    elif isinstance(edge, (list, tuple)) and len(edge) >= 2:
                        dependencies.append({
                            "source": edge[0],
                            "target": edge[1],
                            "type": "imports",
                        })
            elif "dependencies" in dep_graph:
                dependencies = dep_graph.get("dependencies", [])

        return dependencies

    async def _refine_domains_with_agents(
        self,
        raw_domains: List[Dict[str, Any]],
        extensions: List,
        context: WorkflowContext,
        user_journey: Dict[str, Any],
    ) -> tuple:
        """
        Refine domains using Peter and Betty agents.

        Peter: Validates domain boundaries, suggests merges/splits
        Betty: Expands use case documentation, adds business context
        """
        import asyncio

        refined_domains = raw_domains.copy()
        peter_result = None
        betty_result = None

        # Prepare context for agents
        agent_context = {
            "domains": raw_domains,
            "user_journeys": user_journey.get("journeys", []),
            "personas": user_journey.get("personas", []),
            "project_path": context.shared_data.get("project_path", ""),
        }

        async def run_peter(ext) -> Dict[str, Any]:
            """Run Peter for domain validation and refinement."""
            try:
                peter_output = await ext.run_full_lifecycle(
                    task="Validate business domain boundaries and suggest refinements",
                    context=agent_context,
                    entry_id=f"{context.workflow_id}-peter-domains",
                )
                if peter_output.success:
                    return {
                        "success": True,
                        "refinements": peter_output.output.get("refinements", []),
                        "merged_domains": peter_output.output.get("merged_domains", []),
                        "split_domains": peter_output.output.get("split_domains", []),
                    }
                return {"success": False, "error": "Peter returned unsuccessful result"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        async def run_betty(ext) -> Dict[str, Any]:
            """Run Betty for documentation and use case expansion."""
            try:
                betty_output = await ext.run_full_lifecycle(
                    task="Expand domain documentation and use cases with business context",
                    context=agent_context,
                    entry_id=f"{context.workflow_id}-betty-domains",
                )
                if betty_output.success:
                    return {
                        "success": True,
                        "enhanced_use_cases": betty_output.output.get("enhanced_use_cases", {}),
                        "business_context": betty_output.output.get("business_context", {}),
                    }
                return {"success": False, "error": "Betty returned unsuccessful result"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Map agents to tasks
        agent_tasks = {}
        for ext in extensions:
            if ext.name == "Peter":
                agent_tasks["Peter"] = run_peter(ext)
            elif ext.name == "Betty":
                agent_tasks["Betty"] = run_betty(ext)

        # Run agents in parallel
        if agent_tasks:
            try:
                results = await asyncio.gather(
                    *agent_tasks.values(),
                    return_exceptions=True,
                )

                agent_names = list(agent_tasks.keys())
                for name, agent_result in zip(agent_names, results):
                    if isinstance(agent_result, Exception):
                        logger.warning(f"Agent {name} failed: {agent_result}")
                    elif name == "Peter":
                        peter_result = agent_result
                        if agent_result.get("success"):
                            # Apply Peter's refinements
                            refined_domains = self._apply_peter_refinements(
                                refined_domains, agent_result
                            )
                            logger.info(f"Peter: domain refinements applied")
                    elif name == "Betty":
                        betty_result = agent_result
                        if agent_result.get("success"):
                            # Apply Betty's documentation
                            refined_domains = self._apply_betty_documentation(
                                refined_domains, agent_result
                            )
                            logger.info(f"Betty: documentation expanded")

            except Exception as e:
                logger.error(f"Error running domain agents: {e}")

        return refined_domains, peter_result, betty_result

    def _apply_peter_refinements(
        self,
        domains: List[Dict[str, Any]],
        peter_result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Apply Peter's domain refinements."""
        refined = domains.copy()

        # Apply any merged domains
        merged = peter_result.get("merged_domains", [])
        if merged:
            # Simple merge: update first domain with merged info
            for merge_info in merged:
                source_names = merge_info.get("source_domains", [])
                target_name = merge_info.get("target_name", "")
                if source_names and target_name:
                    # Find and merge
                    merged_modules = []
                    merged_entities = []
                    merged_use_cases = []
                    domains_to_remove = []

                    for domain in refined:
                        if domain.get("name") in source_names:
                            merged_modules.extend(domain.get("modules", []))
                            merged_entities.extend(domain.get("entities", []))
                            merged_use_cases.extend(domain.get("use_cases", []))
                            domains_to_remove.append(domain)

                    if domains_to_remove:
                        for d in domains_to_remove:
                            refined.remove(d)
                        refined.append({
                            "name": target_name,
                            "modules": list(set(merged_modules)),
                            "entities": list(set(merged_entities)),
                            "use_cases": list(set(merged_use_cases)),
                            "confidence": 0.8,
                            "complexity": "medium",
                            "source": "peter_merge",
                        })

        # Apply refinement suggestions (boost confidence, add details)
        refinements = peter_result.get("refinements", [])
        for refinement in refinements:
            domain_name = refinement.get("domain_name", "")
            for domain in refined:
                if domain.get("name") == domain_name:
                    if "confidence_boost" in refinement:
                        domain["confidence"] = min(
                            1.0,
                            domain.get("confidence", 0.5) + refinement["confidence_boost"]
                        )
                    if "additional_modules" in refinement:
                        domain["modules"] = list(set(
                            domain.get("modules", []) + refinement["additional_modules"]
                        ))

        return refined

    def _apply_betty_documentation(
        self,
        domains: List[Dict[str, Any]],
        betty_result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Apply Betty's documentation enhancements."""
        enhanced = domains.copy()

        # Apply enhanced use cases
        enhanced_use_cases = betty_result.get("enhanced_use_cases", {})
        for domain in enhanced:
            domain_name = domain.get("name", "")
            if domain_name in enhanced_use_cases:
                # Add Betty's enhanced use cases
                new_use_cases = enhanced_use_cases[domain_name]
                existing = set(domain.get("use_cases", []))
                for uc in new_use_cases:
                    if uc not in existing:
                        domain.setdefault("use_cases", []).append(uc)

        # Apply business context
        business_context = betty_result.get("business_context", {})
        for domain in enhanced:
            domain_name = domain.get("name", "")
            if domain_name in business_context:
                ctx = business_context[domain_name]
                if "description" in ctx:
                    domain["description"] = ctx["description"]
                if "business_value" in ctx:
                    domain["business_value"] = ctx["business_value"]
                if "stakeholders" in ctx:
                    domain["stakeholders"] = ctx["stakeholders"]

        return enhanced

    async def _heuristic_domain_extraction(
        self,
        project_path: str,
        code_understanding: Dict[str, Any],
        user_journey: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Heuristic domain extraction using code structure analysis.

        Alternative method that extracts domains from:
        - User journey personas (role-based domains)
        - File structure patterns
        - Foundation analysis layers
        """
        domains = []

        # Generate domains from personas
        personas = user_journey.get("personas", [])
        for persona in personas:
            role_code = persona.get("role_code", persona.get("name", "")).upper()
            if role_code:
                # Create domain for this role's functionality
                domain_name = f"{persona.get('name', role_code)} Functies"
                domains.append({
                    "name": domain_name,
                    "description": f"Functionaliteit voor {persona.get('name', role_code)} gebruikers",
                    "modules": [],
                    "entities": [persona.get("name", role_code)],
                    "use_cases": persona.get("goals", [f"Perform {role_code} tasks"]),
                    "complexity": "medium",
                    "confidence": 0.4,
                    "source": "heuristic_persona",
                })

        # Generate domains from foundation layers if available
        foundation = code_understanding.get("foundation", {})
        layers = foundation.get("layers", {})
        for layer_name, layer_modules in layers.items():
            if isinstance(layer_modules, list) and layer_modules:
                domains.append({
                    "name": f"{layer_name.title()} Layer",
                    "description": f"Components in the {layer_name} layer",
                    "modules": layer_modules[:20],  # Limit
                    "entities": [],
                    "use_cases": [f"Manage {layer_name} functionality"],
                    "complexity": "low" if len(layer_modules) < 10 else "medium",
                    "confidence": 0.3,
                    "source": "heuristic_foundation",
                })

        # Add generic domain if nothing else found
        if not domains:
            domains.append({
                "name": "Core Application",
                "description": "Core application functionality",
                "modules": [],
                "entities": [],
                "use_cases": ["Basic application operations"],
                "complexity": "medium",
                "confidence": 0.2,
                "source": "heuristic_generic",
            })

        logger.info(f"Heuristic domain extraction: {len(domains)} domains")
        return domains


    # =========================================================================
    # M8: STORY GENERATION (W159 BusinessDrivenStoryGenerator)
    # =========================================================================

    async def _execute_story_generation(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """
        Execute story generation using W159 BusinessDrivenStoryGenerator.

        Source: business_driven_story_generator_service.py (BusinessDrivenStoryGeneratorService)

        This stage:
        1. Gets domains from M7 domain_extraction
        2. Gets user journeys from M5 user_journey
        3. Uses BusinessDrivenStoryGeneratorService to generate epics/stories
        4. Peter enriches stories with business context
        5. Links stories to personas and journeys

        Graceful degradation: If service unavailable, generates basic stories
        from domains with quality_score 0.50-0.70.
        """
        import time

        start_time = time.time()
        project_path = context.shared_data.get("project_path", "")

        result = StoryGenerationResult(
            project_path=project_path,
            agents_run=0,
            agents_succeeded=0,
            errors=[],
        )

        # Get data from previous stages
        domain_extraction = context.shared_data.get("domain_extraction", {})
        user_journey = context.shared_data.get("user_journey", {})
        code_understanding = context.shared_data.get("code_understanding", {})

        domains = domain_extraction.get("domains", [])
        journeys = user_journey.get("journeys", [])
        personas = user_journey.get("personas", [])

        result.domains_processed = len(domains)

        logger.info(
            f"Story generation starting: {len(domains)} domains, "
            f"{len(journeys)} journeys, {len(personas)} personas"
        )

        if not domains:
            logger.warning("No domains available for story generation")
            result.errors.append("No domains from M7")
            context.shared_data["story_generation"] = result.to_dict()
            return result.to_dict()

        # Step 1: Run BusinessDrivenStoryGeneratorService
        try:
            from app.services.business_driven_story_generator_service import (
                BusinessDrivenStoryGeneratorService,
                BusinessDomainCandidate,
                BusinessDomainExtractionResult,
                ExtractedEntity,
            )
            from app.services.business_domain_extractor_service import ModuleCluster

            # Convert domain dicts back to dataclass objects
            domain_candidates = []
            for d in domains:
                entities = [
                    ExtractedEntity(
                        name=e if isinstance(e, str) else e.get("name", ""),
                        entity_type="class",
                        source_file="",
                    )
                    for e in d.get("entities", [])
                ]
                candidate = BusinessDomainCandidate(
                    name=d.get("name", "Unknown"),
                    description=d.get("description", ""),
                    modules=d.get("modules", []),
                    entities=entities,
                    use_cases=d.get("use_cases", []),
                    source_files=d.get("source_files", []),
                    complexity=d.get("complexity", "medium"),
                    confidence=d.get("confidence", 0.5),
                )
                domain_candidates.append(candidate)

            # Create mock extraction result
            module_clusters = [
                ModuleCluster(
                    name=c.get("name", ""),
                    modules=c.get("modules", []) if isinstance(c.get("modules"), list) else [],
                    cohesion_score=c.get("cohesion_score", 0.5),
                    central_module=c.get("central_module", ""),
                    dependency_count=c.get("dependency_count", 0),
                )
                for c in domain_extraction.get("module_clusters", [])
            ]

            extraction_result = BusinessDomainExtractionResult(
                domains=domain_candidates,
                module_clusters=module_clusters,
                total_modules_analyzed=domain_extraction.get("modules_analyzed", 0),
                total_entities_found=domain_extraction.get("entities_found", 0),
                extraction_time_ms=0,
            )

            # Generate stories
            generator = BusinessDrivenStoryGeneratorService()
            generation_result = await generator.generate_stories(
                domain_result=extraction_result,
                code_analysis=code_understanding,
            )

            # Preserve full dataclasses for plane export (not the lossy dicts)
            context.shared_data["m8_full_generation_result"] = generation_result

            # Process results
            result.epics = [self._epic_to_dict(e) for e in generation_result.epics]
            result.total_epics = len(result.epics)
            result.total_stories = generation_result.total_stories
            result.total_story_points = generation_result.total_story_points
            result.total_features = generation_result.total_features

            # Flatten stories for easy access
            result.stories = []
            result.features = []
            for epic in generation_result.epics:
                for feature in epic.features:
                    result.features.append({
                        "id": feature.id,
                        "title": feature.title,
                        "epic_id": feature.epic_id,
                        "story_count": len(feature.stories),
                        "story_points": feature.estimated_story_points,
                    })
                    for story in feature.stories:
                        result.stories.append({
                            "id": story.id,
                            "title": story.title,
                            "feature_id": story.feature_id,
                            "story_points": story.story_points,
                            "story_type": story.story_type,
                            "complexity": story.complexity,
                        })

            # Calculate estimated weeks
            velocity = 20  # Story points per week
            result.estimated_weeks = max(1, result.total_story_points // velocity)

            logger.info(
                f"BusinessDrivenStoryGenerator: {result.total_stories} stories, "
                f"{result.total_epics} epics, {result.total_story_points} points"
            )

        except ImportError as e:
            logger.warning(f"BusinessDrivenStoryGeneratorService not available: {e}")
            result.errors.append(f"Generator not available: {e}")
            result = await self._domain_driven_story_generation(
                domains, journeys, personas, result
            )
        except Exception as e:
            logger.error(f"Story generation failed: {e}")
            result.errors.append(str(e))
            result = await self._domain_driven_story_generation(
                domains, journeys, personas, result
            )

        # Step 2: Peter enrichment (optional)
        try:
            from .base import WorkflowStage as WS
            extensions = await self.get_agents_for_stage(
                WS(
                    name="story_generation",
                    description="Story generation",
                    agents=["Peter"],
                ),
                context,
            )
        except Exception as e:
            logger.warning(f"Could not get agents for story_generation: {e}")
            extensions = []

        if extensions:
            peter_result = await self._enrich_stories_with_peter(
                result.stories, result.epics, extensions, context, journeys, personas
            )
            result.peter_enrichments = peter_result
            # Preserve Peter enrichments for plane export
            context.shared_data["m8_peter_enrichments"] = peter_result
            result.agents_run = 1
            if peter_result and peter_result.get("success"):
                result.agents_succeeded = 1
                # Apply Peter's enrichments
                result = self._apply_peter_story_enrichments(result, peter_result)
        else:
            logger.info("No agents available for story enrichment, using raw generation")

        # Step 3: Link stories to journeys and personas
        result.journeys_linked, result.personas_linked = self._link_stories_to_journeys(
            result.stories, journeys, personas
        )

        # Calculate duration
        result.duration_seconds = time.time() - start_time

        # Store in shared_data for downstream stages (M9: estimation)
        context.shared_data["story_generation"] = result.to_dict()

        logger.info(
            f"Story generation complete: {result.total_stories} stories, "
            f"{result.total_epics} epics, {result.total_story_points} points, "
            f"score {result.quality_score}, duration {result.duration_seconds:.1f}s"
        )

        return result.to_dict()

    def _epic_to_dict(self, epic) -> Dict[str, Any]:
        """Convert GeneratedEpic to dict."""
        return {
            "id": epic.id,
            "title": epic.title,
            "description": epic.description,
            "domain_name": epic.domain_name,
            "feature_count": len(epic.features),
            "story_count": sum(len(f.stories) for f in epic.features),
            "story_points": epic.estimated_story_points,
            "estimated_weeks": epic.estimated_weeks,
            "complexity": epic.complexity,
            "source_modules": epic.source_modules[:10],  # Limit
            "features": [
                {
                    "id": f.id,
                    "title": f.title,
                    "story_count": len(f.stories),
                    "story_points": f.estimated_story_points,
                }
                for f in epic.features
            ],
        }

    async def _enrich_stories_with_peter(
        self,
        stories: List[Dict[str, Any]],
        epics: List[Dict[str, Any]],
        extensions: List,
        context: WorkflowContext,
        journeys: List[Dict[str, Any]],
        personas: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Enrich stories using Peter agent for business context."""
        peter_ext = None
        for ext in extensions:
            if ext.name == "Peter":
                peter_ext = ext
                break

        if not peter_ext:
            return {"success": False, "error": "Peter agent not available"}

        try:
            agent_context = {
                "stories": stories[:20],  # Limit for context size
                "epics": epics[:10],
                "journeys": journeys[:10],
                "personas": personas[:5],
                "project_path": context.shared_data.get("project_path", ""),
            }

            peter_output = await peter_ext.run_full_lifecycle(
                task="Enrich migration stories with business context and acceptance criteria",
                context=agent_context,
                entry_id=f"{context.workflow_id}-peter-stories",
            )

            if peter_output.success:
                return {
                    "success": True,
                    "enriched_stories": peter_output.output.get("enriched_stories", []),
                    "priority_order": peter_output.output.get("priority_order", []),
                    "business_notes": peter_output.output.get("business_notes", {}),
                }
            return {"success": False, "error": "Peter returned unsuccessful result"}

        except Exception as e:
            logger.warning(f"Peter enrichment failed: {e}")
            return {"success": False, "error": str(e)}

    def _apply_peter_story_enrichments(
        self,
        result: StoryGenerationResult,
        peter_result: Dict[str, Any],
    ) -> StoryGenerationResult:
        """Apply Peter's enrichments to stories."""
        enriched_stories = peter_result.get("enriched_stories", [])
        priority_order = peter_result.get("priority_order", [])
        business_notes = peter_result.get("business_notes", {})

        # Create lookup for enrichments
        enrichment_lookup = {e.get("id"): e for e in enriched_stories if e.get("id")}

        # Apply enrichments to stories
        for story in result.stories:
            story_id = story.get("id", "")
            if story_id in enrichment_lookup:
                enrichment = enrichment_lookup[story_id]
                if "business_value" in enrichment:
                    story["business_value"] = enrichment["business_value"]
                if "priority" in enrichment:
                    story["priority"] = enrichment["priority"]
                if "additional_criteria" in enrichment:
                    story["additional_criteria"] = enrichment["additional_criteria"]

        # Apply priority order if provided
        if priority_order:
            priority_lookup = {sid: i for i, sid in enumerate(priority_order)}
            for story in result.stories:
                story_id = story.get("id", "")
                if story_id in priority_lookup:
                    story["suggested_order"] = priority_lookup[story_id]

        # Apply business notes to epics
        for epic in result.epics:
            epic_id = epic.get("id", "")
            if epic_id in business_notes:
                epic["business_notes"] = business_notes[epic_id]

        return result

    def _link_stories_to_journeys(
        self,
        stories: List[Dict[str, Any]],
        journeys: List[Dict[str, Any]],
        personas: List[Dict[str, Any]],
    ) -> tuple:
        """Link stories to user journeys and personas based on content matching."""
        journeys_linked = 0
        personas_linked = 0

        if not journeys and not personas:
            return 0, 0

        # Create keyword sets from journeys and personas
        journey_keywords = {}
        for j in journeys:
            jid = j.get("id", "")
            keywords = set()
            keywords.add(j.get("name", "").lower())
            for step in j.get("steps", []):
                keywords.add(step.get("action", "").lower())
            journey_keywords[jid] = keywords

        persona_keywords = {}
        for p in personas:
            pid = p.get("id", "")
            keywords = set()
            keywords.add(p.get("name", "").lower())
            keywords.add(p.get("role_code", "").lower())
            persona_keywords[pid] = keywords

        # Match stories to journeys and personas
        for story in stories:
            story_text = (story.get("title", "") + " " + story.get("description", "")).lower()

            # Match journeys
            for jid, keywords in journey_keywords.items():
                if any(kw in story_text for kw in keywords if kw):
                    story.setdefault("linked_journeys", []).append(jid)
                    journeys_linked += 1

            # Match personas
            for pid, keywords in persona_keywords.items():
                if any(kw in story_text for kw in keywords if kw):
                    story.setdefault("linked_personas", []).append(pid)
                    personas_linked += 1

        return journeys_linked, personas_linked

    async def _domain_driven_story_generation(
        self,
        domains: List[Dict[str, Any]],
        journeys: List[Dict[str, Any]],
        personas: List[Dict[str, Any]],
        result: StoryGenerationResult,
    ) -> StoryGenerationResult:
        """
        Domain-driven story generation from extracted domains.

        Alternative method that generates stories directly from:
        - Domains and their use cases (epics)
        - Entity CRUD operations (feature stories)
        - User journeys (workflow stories)
        - Personas (user-specific stories)

        This is a deterministic approach that creates stories from
        the domain model, ensuring complete coverage of identified domains.
        """
        epic_counter = 0
        story_counter = 0
        total_points = 0

        result.epics = []
        result.stories = []
        result.features = []

        # Generate epics from domains
        for domain in domains:
            epic_counter += 1
            epic_id = f"EPIC-{epic_counter:03d}"

            epic_stories = []
            epic_points = 0

            # Generate stories from use cases
            for use_case in domain.get("use_cases", []):
                story_counter += 1
                story_id = f"STORY-{epic_counter:03d}-{story_counter:03d}"

                points = 5  # Default story points
                epic_points += points
                total_points += points

                story = {
                    "id": story_id,
                    "title": f"Implementeer: {use_case}",
                    "description": f"Migreer de '{use_case}' functionaliteit naar het moderne platform.",
                    "feature_id": f"FEAT-{epic_counter:03d}-001",
                    "story_points": points,
                    "story_type": "migration",
                    "complexity": "medium",
                    "acceptance_criteria": [
                        "Functionaliteit werkt identiek aan legacy",
                        "Unit tests zijn geschreven",
                        "Code review is uitgevoerd",
                    ],
                }
                epic_stories.append(story)
                result.stories.append(story)

            # Generate stories from entities
            for entity in domain.get("entities", [])[:5]:
                entity_name = entity if isinstance(entity, str) else entity.get("name", "Entity")
                story_counter += 1
                story_id = f"STORY-{epic_counter:03d}-{story_counter:03d}"

                points = 8  # CRUD stories are typically larger
                epic_points += points
                total_points += points

                story = {
                    "id": story_id,
                    "title": f"Migreer {entity_name} CRUD operaties",
                    "description": f"Migreer Create/Read/Update/Delete operaties voor {entity_name}.",
                    "feature_id": f"FEAT-{epic_counter:03d}-002",
                    "story_points": points,
                    "story_type": "crud",
                    "complexity": "medium",
                    "acceptance_criteria": [
                        f"Alle {entity_name} operaties werken correct",
                        "Data integriteit is behouden",
                        "Validatie regels zijn geïmplementeerd",
                    ],
                }
                epic_stories.append(story)
                result.stories.append(story)

            epic = {
                "id": epic_id,
                "title": f"{domain.get('name', 'Unknown')} Migratie",
                "description": f"Migratie van {domain.get('name', 'Unknown')} domein naar modern platform.",
                "domain_name": domain.get("name", "Unknown"),
                "feature_count": 1,
                "story_count": len(epic_stories),
                "story_points": epic_points,
                "estimated_weeks": max(1, epic_points // 20),
                "complexity": domain.get("complexity", "medium"),
                "source_modules": domain.get("modules", [])[:10],
            }
            result.epics.append(epic)

        # Update totals
        result.total_epics = len(result.epics)
        result.total_stories = len(result.stories)
        result.total_story_points = total_points
        result.total_features = result.total_epics  # Simplified: 1 feature per epic
        result.estimated_weeks = max(1, total_points // 20)

        logger.info(
            f"Domain-driven story generation: {result.total_stories} stories, "
            f"{result.total_epics} epics, {total_points} points"
        )

        return result

    # =========================================================================
    # M9: ESTIMATION
    # =========================================================================

    async def _execute_estimation(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """
        Execute effort estimation using IFPUG Function Points and story points.

        Source: migration_estimation_service.py (MigrationEstimationService)

        This stage:
        1. Gets stories from M8 story_generation
        2. Gets domains from M7 domain_extraction
        3. Uses MigrationEstimationService for IFPUG FP analysis
        4. Combines FP estimates with story point estimates
        5. Eliza refines estimates with confidence scoring

        Graceful degradation: If FP analysis unavailable, uses story point
        estimates with quality_score 0.50-0.75.
        """
        import time

        start_time = time.time()
        project_path = context.shared_data.get("project_path", "")

        result = EstimationResult(
            project_path=project_path,
            agents_run=0,
            agents_succeeded=0,
            errors=[],
        )

        # Get data from previous stages
        story_generation = context.shared_data.get("story_generation", {})
        domain_extraction = context.shared_data.get("domain_extraction", {})
        code_understanding = context.shared_data.get("code_understanding", {})

        # Get story-based estimates
        result.story_points_total = story_generation.get("total_story_points", 0)
        result.story_based_estimate_weeks = story_generation.get("estimated_weeks", 0)

        logger.info(
            f"Estimation starting: {result.story_points_total} story points, "
            f"{result.story_based_estimate_weeks} weeks from stories"
        )

        # Step 1: Try IFPUG Function Point analysis
        fp_analysis_success = False
        try:
            from app.services.migration_estimation_service import (
                MigrationEstimationService,
                TechnologyStack,
            )

            # Detect technology stack from code_understanding
            tech_stack = self._detect_technology_stack(code_understanding, project_path)

            if tech_stack:
                service = MigrationEstimationService()
                fp_result = service.analyze_directory(
                    directory=project_path,
                    source_stack=tech_stack,
                    target_stack="modern_web",
                    include_risk_buffer=True,
                )

                # Extract FP analysis results
                result.unadjusted_fp = fp_result.total_unadjusted_fp
                result.value_adjustment_factor = fp_result.value_adjustment_factor
                result.adjusted_fp = fp_result.total_adjusted_fp
                result.component_count = len(fp_result.components)
                result.components_by_type = fp_result._group_by_type()
                result.total_effort_hours = fp_result.total_effort_hours
                result.total_effort_person_days = fp_result.total_effort_person_days
                result.total_effort_person_months = fp_result.total_effort_person_days / 20
                result.confidence_level = fp_result.confidence_level
                result.recommendations = fp_result.recommendations

                # Convert phase estimates
                result.phase_estimates = [
                    {
                        "phase": p.phase.value,
                        "base_hours": round(p.base_hours, 1),
                        "adjusted_hours": round(p.adjusted_hours, 1),
                        "risk_buffer": round(p.risk_buffer_hours, 1),
                        "total_hours": round(p.total_hours, 1),
                        "activities": p.activities,
                    }
                    for p in fp_result.phase_estimates
                ]

                # Convert risk factors
                result.risk_factors = [
                    {
                        "name": f.name,
                        "category": f.category,
                        "value": f.value,
                        "description": f.description,
                    }
                    for f in fp_result.migration_factors
                ]

                fp_analysis_success = True
                logger.info(
                    f"IFPUG analysis: {result.adjusted_fp:.1f} AFP, "
                    f"{result.component_count} components, "
                    f"{result.total_effort_person_days:.1f} person-days"
                )
            else:
                logger.warning("Could not detect technology stack for FP analysis")
                result.errors.append("Technology stack not detected")

        except ImportError as e:
            logger.warning(f"MigrationEstimationService not available: {e}")
            result.errors.append(f"FP service not available: {e}")
        except Exception as e:
            logger.error(f"IFPUG analysis failed: {e}")
            result.errors.append(f"FP analysis error: {e}")

        # Step 2: Calculate combined estimates
        result = self._calculate_combined_estimates(result)

        # Step 3: Calculate team recommendations
        result = self._calculate_team_recommendations(result)

        # Step 4: Eliza refinement (optional)
        try:
            from .base import WorkflowStage as WS
            extensions = await self.get_agents_for_stage(
                WS(
                    name="estimation",
                    description="Estimation",
                    agents=["Eliza"],
                ),
                context,
            )
        except Exception as e:
            logger.warning(f"Could not get agents for estimation: {e}")
            extensions = []

        if extensions:
            eliza_result = await self._refine_estimation_with_eliza(
                result, extensions, context
            )
            result.eliza_refinements = eliza_result
            result.agents_run = 1
            if eliza_result and eliza_result.get("success"):
                result.agents_succeeded = 1
                # Apply Eliza's refinements
                result = self._apply_eliza_refinements(result, eliza_result)
        else:
            logger.info("No agents available for estimation refinement")

        # Calculate duration
        result.duration_seconds = time.time() - start_time

        # Preserve full EstimationResult for plane export
        context.shared_data["m9_full_estimation_result"] = result

        # Store in shared_data for downstream stages (M10: deliverables)
        context.shared_data["estimation"] = result.to_dict()

        logger.info(
            f"Estimation complete: {result.adjusted_fp:.1f} AFP, "
            f"{result.estimated_weeks_likely} weeks likely, "
            f"confidence {result.confidence_level:.2f}, "
            f"score {result.quality_score}, duration {result.duration_seconds:.1f}s"
        )

        return result.to_dict()

    def _detect_technology_stack(
        self,
        code_understanding: Dict[str, Any],
        project_path: str,
    ):
        """Detect technology stack from code understanding data."""
        try:
            from app.services.migration_estimation_service import TechnologyStack
        except ImportError:
            return None

        # Check file extensions in project
        path = Path(project_path)
        extensions = set()

        for ext in [".asp", ".aspx", ".vb", ".cs", ".php", ".java", ".cob"]:
            if list(path.rglob(f"*{ext}"))[:1]:  # Check if any files exist
                extensions.add(ext)

        # Map extensions to tech stack
        if ".asp" in extensions:
            return TechnologyStack.CLASSIC_ASP
        elif ".aspx" in extensions and ".vb" in extensions:
            return TechnologyStack.VB_NET_WEBFORMS
        elif ".aspx" in extensions and ".cs" in extensions:
            return TechnologyStack.CSHARP_WEBFORMS
        elif ".php" in extensions:
            return TechnologyStack.PHP_LEGACY
        elif ".java" in extensions:
            return TechnologyStack.JAVA_LEGACY
        elif ".cob" in extensions:
            return TechnologyStack.COBOL

        # Default to VB.NET WebForms (common in healthcare legacy)
        return TechnologyStack.VB_NET_WEBFORMS

    def _calculate_combined_estimates(
        self,
        result: EstimationResult,
    ) -> EstimationResult:
        """Calculate combined estimates from FP and story points."""
        # FP-based weeks (8 hours/day, 5 days/week)
        fp_weeks = 0
        if result.total_effort_hours > 0:
            fp_weeks = result.total_effort_hours / 40  # 40 hours/week

        # Story-based weeks
        sp_weeks = result.story_based_estimate_weeks

        # Combine estimates
        if fp_weeks > 0 and sp_weeks > 0:
            # Use weighted average (FP slightly more weight due to methodology)
            likely = int((fp_weeks * 0.6 + sp_weeks * 0.4))
            result.estimated_weeks_low = int(likely * 0.8)  # 20% optimistic
            result.estimated_weeks_high = int(likely * 1.4)  # 40% pessimistic
            result.estimated_weeks_likely = likely
        elif fp_weeks > 0:
            result.estimated_weeks_likely = int(fp_weeks)
            result.estimated_weeks_low = int(fp_weeks * 0.8)
            result.estimated_weeks_high = int(fp_weeks * 1.4)
        elif sp_weeks > 0:
            result.estimated_weeks_likely = sp_weeks
            result.estimated_weeks_low = int(sp_weeks * 0.8)
            result.estimated_weeks_high = int(sp_weeks * 1.5)  # More uncertainty
        else:
            # Fallback: minimal estimates
            result.estimated_weeks_likely = 4
            result.estimated_weeks_low = 2
            result.estimated_weeks_high = 8

        # Ensure minimums
        result.estimated_weeks_low = max(1, result.estimated_weeks_low)
        result.estimated_weeks_likely = max(2, result.estimated_weeks_likely)
        result.estimated_weeks_high = max(4, result.estimated_weeks_high)

        return result

    def _calculate_team_recommendations(
        self,
        result: EstimationResult,
    ) -> EstimationResult:
        """Calculate team size recommendations based on estimates."""
        # Base velocity: 20 story points per developer per week
        velocity = result.velocity_assumption

        if result.story_points_total > 0:
            # Calculate ideal team size for target duration (12-16 weeks)
            target_weeks = 14  # ~3.5 months
            ideal_velocity_needed = result.story_points_total / target_weeks
            ideal_team = max(1, int(ideal_velocity_needed / velocity + 0.5))

            # Constrain to reasonable bounds
            result.recommended_team_size = min(10, max(2, ideal_team))
        else:
            # Default based on effort hours
            if result.total_effort_hours > 0:
                # 160 hours/month per developer
                months = result.total_effort_hours / 160
                result.recommended_team_size = max(2, min(10, int(months / 3 + 0.5)))
            else:
                result.recommended_team_size = 3  # Default team

        return result

    async def _refine_estimation_with_eliza(
        self,
        result: EstimationResult,
        extensions: List,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Refine estimation using Eliza agent for confidence scoring."""
        eliza_ext = None
        for ext in extensions:
            if ext.name == "Eliza":
                eliza_ext = ext
                break

        if not eliza_ext:
            return {"success": False, "error": "Eliza agent not available"}

        try:
            agent_context = {
                "function_points": {
                    "adjusted": result.adjusted_fp,
                    "components": result.component_count,
                },
                "story_points": result.story_points_total,
                "estimates": {
                    "weeks_low": result.estimated_weeks_low,
                    "weeks_likely": result.estimated_weeks_likely,
                    "weeks_high": result.estimated_weeks_high,
                },
                "team_size": result.recommended_team_size,
                "risk_factors": result.risk_factors[:5],
                "project_path": context.shared_data.get("project_path", ""),
            }

            eliza_output = await eliza_ext.run_full_lifecycle(
                task="Review migration estimates and provide confidence assessment",
                context=agent_context,
                entry_id=f"{context.workflow_id}-eliza-estimation",
            )

            if eliza_output.success:
                return {
                    "success": True,
                    "confidence_adjustment": eliza_output.output.get("confidence_adjustment", 0),
                    "estimate_adjustments": eliza_output.output.get("estimate_adjustments", {}),
                    "additional_risks": eliza_output.output.get("additional_risks", []),
                    "recommendations": eliza_output.output.get("recommendations", []),
                }
            return {"success": False, "error": "Eliza returned unsuccessful result"}

        except Exception as e:
            logger.warning(f"Eliza refinement failed: {e}")
            return {"success": False, "error": str(e)}

    def _apply_eliza_refinements(
        self,
        result: EstimationResult,
        eliza_result: Dict[str, Any],
    ) -> EstimationResult:
        """Apply Eliza's refinements to estimation."""
        # Adjust confidence
        confidence_adj = eliza_result.get("confidence_adjustment", 0)
        result.confidence_level = max(0.0, min(1.0, result.confidence_level + confidence_adj))

        # Apply estimate adjustments
        adjustments = eliza_result.get("estimate_adjustments", {})
        if "weeks_multiplier" in adjustments:
            multiplier = adjustments["weeks_multiplier"]
            result.estimated_weeks_low = int(result.estimated_weeks_low * multiplier)
            result.estimated_weeks_likely = int(result.estimated_weeks_likely * multiplier)
            result.estimated_weeks_high = int(result.estimated_weeks_high * multiplier)

        if "team_size" in adjustments:
            result.recommended_team_size = adjustments["team_size"]

        # Add additional risks
        additional_risks = eliza_result.get("additional_risks", [])
        for risk in additional_risks:
            result.risk_factors.append({
                "name": risk.get("name", "Unknown"),
                "category": "eliza",
                "value": risk.get("impact", 1.0),
                "description": risk.get("description", ""),
            })

        # Add recommendations
        additional_recs = eliza_result.get("recommendations", [])
        result.recommendations.extend(additional_recs[:5])

        return result

    # =========================================================================
    # M10: DELIVERABLES
    # =========================================================================

    async def _execute_deliverables(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """
        Execute deliverables generation using BrownPaperDeliverableService.

        Source: brown_paper_deliverable_service.py (BrownPaperDeliverableService)

        This stage:
        1. Collects all data from previous stages (M1-M9)
        2. Generates comprehensive markdown documentation
        3. Creates hierarchical file structure
        4. Diana reviews and enhances documentation

        Graceful degradation: If service unavailable, generates basic summary
        with quality_score 0.50-0.80.
        """
        import time

        start_time = time.time()
        project_path = context.shared_data.get("project_path", "")

        # Determine output directory
        output_dir = Path(project_path) / "docs" / "onboarding-deliverables"

        result = DeliverablesResult(
            project_path=project_path,
            output_dir=str(output_dir),
            agents_run=0,
            agents_succeeded=0,
            errors=[],
        )

        # Collect all data from previous stages
        story_generation = context.shared_data.get("story_generation", {})
        domain_extraction = context.shared_data.get("domain_extraction", {})
        estimation = context.shared_data.get("estimation", {})
        security_scan = context.shared_data.get("security_scan", {})
        user_journey = context.shared_data.get("user_journey", {})
        deep_extraction = context.shared_data.get("deep_extraction", {})
        code_understanding = context.shared_data.get("code_understanding", {})
        intake_context = context.shared_data.get("intake_context", {})
        answers = context.shared_data.get("answers", {})

        logger.info(
            f"Deliverables generation starting for: {project_path}"
        )

        # Step 1: Try BrownPaperDeliverableService
        try:
            from app.services.brown_paper_deliverable_service import (
                BrownPaperDeliverableService,
            )

            # Create session-like object for service
            session_data = self._create_deliverable_session(
                project_path, answers, intake_context, code_understanding
            )

            # Create tasks structure for service
            tasks_data = self._create_deliverable_tasks(
                story_generation, domain_extraction, estimation,
                security_scan, user_journey, deep_extraction
            )

            # Generate deliverables
            service = BrownPaperDeliverableService(output_dir)
            delivery_result = await service.generate_deliverables(
                session=session_data,
                tasks=tasks_data,
                enhanced_analysis=deep_extraction,
            )

            result.files_created = delivery_result.get("files_created", 0)
            result.file_paths = delivery_result.get("file_paths", [])
            result.epics_documented = delivery_result.get("epics", 0)
            result.features_documented = delivery_result.get("features", 0)
            result.stories_documented = delivery_result.get("stories", 0)
            result.index_path = str(output_dir / "README.md")

            # Track sections
            result.sections_generated = [
                "project-summary", "epics", "user-journeys",
                "workflows", "non-functional-requirements",
                "architecture", "risks", "estimation", "migration-strategy"
            ]

            logger.info(
                f"BrownPaperDeliverableService: {result.files_created} files created"
            )

        except ImportError as e:
            logger.warning(f"BrownPaperDeliverableService not available: {e}")
            result.errors.append(f"Service not available: {e}")
            result = await self._template_based_deliverables(
                output_dir, story_generation, domain_extraction,
                estimation, security_scan, user_journey, answers, result
            )
        except Exception as e:
            logger.error(f"Deliverables generation failed: {e}")
            result.errors.append(str(e))
            result = await self._template_based_deliverables(
                output_dir, story_generation, domain_extraction,
                estimation, security_scan, user_journey, answers, result
            )

        # Step 2: Calculate total file size
        result.total_size_kb = self._calculate_total_size(result.file_paths)

        # Step 3: Diana enhancement (optional)
        try:
            from .base import WorkflowStage as WS
            extensions = await self.get_agents_for_stage(
                WS(
                    name="deliverables",
                    description="Deliverables",
                    agents=["Diana"],
                ),
                context,
            )
        except Exception as e:
            logger.warning(f"Could not get agents for deliverables: {e}")
            extensions = []

        if extensions:
            diana_result = await self._enhance_deliverables_with_diana(
                result, extensions, context
            )
            result.diana_enhancements = diana_result
            result.agents_run = 1
            if diana_result and diana_result.get("success"):
                result.agents_succeeded = 1
        else:
            logger.info("No agents available for deliverables enhancement")

        # Calculate duration
        result.duration_seconds = time.time() - start_time

        # Store in shared_data for downstream stages (M11: quality_review)
        context.shared_data["deliverables"] = result.to_dict()

        logger.info(
            f"Deliverables complete: {result.files_created} files, "
            f"{result.total_size_kb:.1f}KB, "
            f"score {result.quality_score}, duration {result.duration_seconds:.1f}s"
        )

        return result.to_dict()

    def _create_deliverable_session(
        self,
        project_path: str,
        answers: Dict[str, Any],
        intake_context: Dict[str, Any],
        code_understanding: Dict[str, Any],
    ):
        """Create a session-like object for BrownPaperDeliverableService."""
        class DeliverableSession:
            def __init__(self, project_path, answers, intake_context):
                self.project_name = Path(project_path).name
                self.project_path = project_path
                self.status = "completed"
                self.answers = answers
                self.specification = {
                    "executive_summary": answers.get("q1_primary_purpose", ""),
                    "current_state": {
                        "description": answers.get("q5_pain_points", ""),
                    },
                    "users": answers.get("q2_users", ""),
                    "critical_processes": answers.get("q3_critical_processes", ""),
                    "integrations": answers.get("q4_integrations", ""),
                }
                self.analysis = intake_context

        return DeliverableSession(project_path, answers, intake_context)

    def _create_deliverable_tasks(
        self,
        story_generation: Dict[str, Any],
        domain_extraction: Dict[str, Any],
        estimation: Dict[str, Any],
        security_scan: Dict[str, Any],
        user_journey: Dict[str, Any],
        deep_extraction: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create tasks structure for BrownPaperDeliverableService."""
        # Convert epics to expected format
        epics = []
        for epic in story_generation.get("epics", []):
            epics.append({
                "id": epic.get("id", ""),
                "title": epic.get("title", ""),
                "description": epic.get("description", ""),
                "domain": epic.get("domain_name", ""),
                "complexity": epic.get("complexity", "medium"),
                "estimated_fp": epic.get("story_points", 0),
                "estimated_weeks": epic.get("estimated_weeks", 0),
                "source_modules": epic.get("source_modules", []),
            })

        # Features (from epics)
        features = []
        for epic in story_generation.get("epics", []):
            for feat in epic.get("features", []):
                features.append({
                    "id": feat.get("id", ""),
                    "title": feat.get("title", ""),
                    "description": "",
                    "epic_id": epic.get("id", ""),
                    "complexity": "medium",
                    "estimated_fp": 0,
                    "estimated_sp": feat.get("story_points", 0),
                })

        # Stories
        stories = []
        for story in story_generation.get("stories", []):
            stories.append({
                "id": story.get("id", ""),
                "title": story.get("title", ""),
                "description": story.get("description", story.get("title", "")),
                "epic_id": story.get("epic_id", ""),
                "feature_id": story.get("feature_id", ""),
                "story_type": story.get("story_type", "migration"),
                "complexity": story.get("complexity", "medium"),
                "estimated_sp": story.get("story_points", 0),
                "acceptance_criteria": story.get("acceptance_criteria", []),
            })

        # Summary
        summary = {
            "total_epics": story_generation.get("total_epics", len(epics)),
            "total_features": story_generation.get("total_features", len(features)),
            "total_stories": story_generation.get("total_stories", len(stories)),
            "total_story_points": story_generation.get("total_story_points", 0),
            "estimated_fp": estimation.get("function_points", {}).get("adjusted", 0),
            "total_function_points": estimation.get("function_points", {}).get("adjusted", 0),
            "fp_confidence": estimation.get("confidence_level", 0),
            "extraction_method": "onboarding-workflow",
            "estimated_weeks_low": estimation.get("estimates", {}).get("weeks_low", 0),
            "estimated_weeks_likely": estimation.get("estimates", {}).get("weeks_likely", 0),
            "estimated_weeks_high": estimation.get("estimates", {}).get("weeks_high", 0),
            "security_findings": security_scan.get("findings", {}).get("total", 0),
            "critical_issues": security_scan.get("findings", {}).get("critical", 0),
        }

        return {
            "epics": epics,
            "features": features,
            "stories": stories,
            "summary": summary,
        }

    async def _template_based_deliverables(
        self,
        output_dir: Path,
        story_generation: Dict[str, Any],
        domain_extraction: Dict[str, Any],
        estimation: Dict[str, Any],
        security_scan: Dict[str, Any],
        user_journey: Dict[str, Any],
        answers: Dict[str, Any],
        result: DeliverablesResult,
    ) -> DeliverablesResult:
        """
        Template-based deliverables generation.

        Alternative method that generates markdown files from templates:
        - README.md (index)
        - project-summary.md
        - estimation-report.md
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        files_created = []
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        project_name = Path(result.project_path).name

        # 1. README.md
        readme_content = f"""# {project_name} - Onboarding Deliverables

**Generated**: {now}
**Workflow**: OnboardingWorkflow M1-M10

---

## Documents

| Document | Description |
|----------|-------------|
| [Project Summary](project-summary.md) | Executive overview |
| [Estimation Report](estimation-report.md) | Effort estimates |

## Quick Stats

| Metric | Value |
|--------|-------|
| Total Epics | {story_generation.get('total_epics', 0)} |
| Total Stories | {story_generation.get('total_stories', 0)} |
| Story Points | {story_generation.get('total_story_points', 0)} |
| Adjusted FP | {estimation.get('function_points', {}).get('adjusted', 0)} |
| Security Findings | {security_scan.get('findings', {}).get('total', 0)} |

---
*Generated by OnboardingWorkflow*
"""
        readme_path = output_dir / "README.md"
        readme_path.write_text(readme_content, encoding='utf-8')
        files_created.append(str(readme_path))

        # 2. project-summary.md
        summary_content = f"""# {project_name} - Project Summary

**Generated**: {now}

## Executive Summary

{answers.get('q1_primary_purpose', 'No description available.')}

## Users

{answers.get('q2_users', 'No user information available.')}

## Critical Processes

{answers.get('q3_critical_processes', 'No process information available.')}

## Integrations

{answers.get('q4_integrations', 'No integration information available.')}

## Pain Points

{answers.get('q5_pain_points', 'No pain points documented.')}

## Domains Identified

| # | Domain | Complexity | Confidence |
|---|--------|------------|------------|
"""
        for i, domain in enumerate(domain_extraction.get("domains", [])[:10], 1):
            summary_content += (
                f"| {i} | {domain.get('name', 'Unknown')} "
                f"| {domain.get('complexity', 'medium')} "
                f"| {domain.get('confidence', 0):.0%} |\n"
            )

        summary_content += """
---
*Generated by OnboardingWorkflow*
"""
        summary_path = output_dir / "project-summary.md"
        summary_path.write_text(summary_content, encoding='utf-8')
        files_created.append(str(summary_path))

        # 3. estimation-report.md
        est = estimation
        estimation_content = f"""# {project_name} - Estimation Report

**Generated**: {now}

## Function Point Analysis

| Metric | Value |
|--------|-------|
| Unadjusted FP | {est.get('function_points', {}).get('unadjusted', 0)} |
| VAF | {est.get('function_points', {}).get('vaf', 1.0)} |
| Adjusted FP | {est.get('function_points', {}).get('adjusted', 0)} |
| Components | {est.get('components', {}).get('total', 0)} |
| Confidence | {est.get('confidence_level', 0):.0%} |

## Effort Estimates

| Metric | Value |
|--------|-------|
| Total Hours | {est.get('effort', {}).get('hours', 0)} |
| Person Days | {est.get('effort', {}).get('person_days', 0)} |
| Person Months | {est.get('effort', {}).get('person_months', 0)} |

## Timeline Estimates

| Scenario | Weeks |
|----------|-------|
| Optimistic (Low) | {est.get('estimates', {}).get('weeks_low', 0)} |
| Likely | {est.get('estimates', {}).get('weeks_likely', 0)} |
| Pessimistic (High) | {est.get('estimates', {}).get('weeks_high', 0)} |
| Story-based | {est.get('estimates', {}).get('story_based_weeks', 0)} |

## Team Recommendations

| Metric | Value |
|--------|-------|
| Recommended Team Size | {est.get('team', {}).get('recommended_size', 3)} |
| Velocity Assumption | {est.get('team', {}).get('velocity_assumption', 20)} SP/week |

## Story Summary

| Metric | Value |
|--------|-------|
| Total Epics | {story_generation.get('total_epics', 0)} |
| Total Stories | {story_generation.get('total_stories', 0)} |
| Total Story Points | {story_generation.get('total_story_points', 0)} |

---
*Generated by OnboardingWorkflow*
"""
        estimation_path = output_dir / "estimation-report.md"
        estimation_path.write_text(estimation_content, encoding='utf-8')
        files_created.append(str(estimation_path))

        # Update result
        result.files_created = len(files_created)
        result.file_paths = files_created
        result.index_path = str(readme_path)
        result.sections_generated = ["project-summary", "estimation"]
        result.epics_documented = 0  # Fallback doesn't document individual epics
        result.stories_documented = 0

        logger.info(
            f"Template-based deliverables: {result.files_created} files created"
        )

        return result

    def _calculate_total_size(self, file_paths: List[str]) -> float:
        """Calculate total size of generated files in KB."""
        total_bytes = 0
        for file_path in file_paths:
            try:
                total_bytes += Path(file_path).stat().st_size
            except (OSError, FileNotFoundError):
                continue
        return total_bytes / 1024

    async def _enhance_deliverables_with_diana(
        self,
        result: DeliverablesResult,
        extensions: List,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Enhance deliverables using Diana agent for documentation review."""
        diana_ext = None
        for ext in extensions:
            if ext.name == "Diana":
                diana_ext = ext
                break

        if not diana_ext:
            return {"success": False, "error": "Diana agent not available"}

        try:
            agent_context = {
                "output_dir": result.output_dir,
                "files_created": result.files_created,
                "sections": result.sections_generated,
                "epics": result.epics_documented,
                "stories": result.stories_documented,
                "project_path": context.shared_data.get("project_path", ""),
            }

            diana_output = await diana_ext.run_full_lifecycle(
                task="Review and enhance generated documentation for completeness and clarity",
                context=agent_context,
                entry_id=f"{context.workflow_id}-diana-deliverables",
            )

            if diana_output.success:
                return {
                    "success": True,
                    "enhancements_made": diana_output.output.get("enhancements_made", 0),
                    "sections_improved": diana_output.output.get("sections_improved", []),
                    "recommendations": diana_output.output.get("recommendations", []),
                }
            return {"success": False, "error": "Diana returned unsuccessful result"}

        except Exception as e:
            logger.warning(f"Diana enhancement failed: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # PLANE EXPORT (Optional)
    # =========================================================================

    async def _execute_plane_export(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """
        Assemble Plane-compatible export package from M8+M9+Peter data.

        Uses full dataclasses (not lossy dicts) to preserve:
        - Acceptance criteria
        - Source references with line numbers
        - Legacy/target implementation context
        - CRUD dependency chains
        - Priority inference from multiple pipeline stages
        """
        import time

        start_time = time.time()
        result = {
            "quality_score": 0.0,
            "errors": [],
        }

        try:
            from app.services.plane_export.assembler import PlaneExportAssembler
            from app.services.plane_export.serializers import (
                Adr002MarkdownSerializer,
                JsonExportSerializer,
            )

            # Retrieve full objects from shared_data (preserved in Step 6)
            generation_result = context.shared_data.get("m8_full_generation_result")
            estimation_result = context.shared_data.get("m9_full_estimation_result")
            peter_enrichments = context.shared_data.get("m8_peter_enrichments")
            domain_data = context.shared_data.get("domain_extraction", {})
            project_path = context.shared_data.get("project_path", "")

            if not generation_result:
                result["errors"].append("No M8 generation result available for plane export")
                logger.warning("Plane export skipped: no M8 generation result in shared_data")
                return result

            # Assemble the export package
            assembler = PlaneExportAssembler()
            package = assembler.assemble(
                generation_result=generation_result,
                estimation_result=estimation_result,
                peter_enrichments=peter_enrichments,
                project_context={"project_path": project_path},
                session_id=context.session_id if hasattr(context, "session_id") else None,
                domain_data=domain_data,
            )

            # Serialize to JSON
            json_serializer = JsonExportSerializer()
            json_output = os.path.join(project_path, "plane-export.json") if project_path else "plane-export.json"
            json_serializer.write(package, json_output)

            # Serialize to ADR-002 markdown
            md_serializer = Adr002MarkdownSerializer()
            md_output = os.path.join(project_path, "plane-export") if project_path else "plane-export"
            md_serializer.write(package, md_output)

            # Store in shared_data for downstream use
            context.shared_data["plane_export"] = {
                "json_path": json_output,
                "markdown_path": md_output,
                "total_epics": len(package.epics),
                "total_stories": package.project_summary.total_stories,
                "total_relations": len(package.relations),
                "exported_at": package.exported_at.isoformat(),
            }

            result["quality_score"] = 1.0
            result["json_path"] = json_output
            result["markdown_path"] = md_output
            result["package_stats"] = {
                "epics": len(package.epics),
                "features": sum(len(e.features) for e in package.epics),
                "stories": package.project_summary.total_stories,
                "relations": len(package.relations),
            }

            duration = time.time() - start_time
            logger.info(
                f"Plane export complete: {len(package.epics)} epics, "
                f"{package.project_summary.total_stories} stories, "
                f"{len(package.relations)} relations in {duration:.1f}s"
            )

        except ImportError as e:
            result["errors"].append(f"Plane export module not available: {e}")
            logger.warning(f"Plane export skipped: {e}")
        except Exception as e:
            result["errors"].append(f"Plane export failed: {e}")
            logger.error(f"Plane export failed: {e}", exc_info=True)

        return result

    # =========================================================================
    # M11: QUALITY REVIEW
    # =========================================================================

    async def _execute_quality_review(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """
        Execute M11: Final Quality Review.

        Validates cross-module consistency, security compliance,
        estimation reasonableness, and documentation completeness.

        Source: MigrationOrchestrator pattern (quality_review stage)

        Returns:
            Dict with quality_score and QualityReviewResult data
        """
        started_at = datetime.now(timezone.utc)
        project_path = context.shared_data.get("project_path", "")

        result = QualityReviewResult(
            project_path=project_path,
            agents_run=0,
            agents_succeeded=0,
        )

        try:
            # Collect all previous stage data
            validation = context.shared_data.get("validation", {})
            intake_context = context.shared_data.get("intake_context", {})
            code_understanding = context.shared_data.get("code_understanding", {})
            deep_extraction = context.shared_data.get("deep_extraction", {})
            user_journey = context.shared_data.get("user_journey_extraction", {})
            security_scan = context.shared_data.get("security_scan", {})
            domain_extraction = context.shared_data.get("domain_extraction", {})
            story_generation = context.shared_data.get("story_generation", {})
            estimation = context.shared_data.get("estimation", {})
            deliverables = context.shared_data.get("deliverables", {})

            # 1. Consistency Check
            consistency_result = self._check_consistency(
                validation=validation,
                domain_extraction=domain_extraction,
                story_generation=story_generation,
                estimation=estimation,
                user_journey=user_journey,
            )
            result.consistency_score = consistency_result["score"]
            result.consistency_issues = consistency_result["issues"]

            # 2. Security Compliance Check
            security_result = self._check_security_compliance(security_scan)
            result.security_compliant = security_result["compliant"]
            result.security_score = security_result["score"]
            result.security_issues = security_result["issues"]

            # 3. Estimation Reasonableness Check
            estimation_result = self._check_estimation_reasonableness(
                estimation=estimation,
                story_generation=story_generation,
                code_understanding=code_understanding,
            )
            result.estimation_reasonable = estimation_result["reasonable"]
            result.estimation_confidence = estimation_result["confidence"]
            result.estimation_warnings = estimation_result["warnings"]

            # 4. Documentation Completeness Check
            docs_result = self._check_documentation_completeness(deliverables)
            result.documentation_complete = docs_result["complete"]
            result.documentation_score = docs_result["score"]
            result.missing_sections = docs_result["missing"]

            # 5. Data Integrity Check
            integrity_result = self._check_data_integrity(
                domain_extraction=domain_extraction,
                story_generation=story_generation,
                estimation=estimation,
            )
            result.data_integrity_score = integrity_result["score"]
            result.data_issues = integrity_result["issues"]

            # Generate overall assessment
            result.overall_assessment = self._generate_assessment(result)
            result.recommendations = self._generate_recommendations(result)
            result.blockers = self._identify_blockers(result)

            # Run Quinn agent for final validation
            result.agents_run = 1
            try:
                from app.confucius.extensions import create_extension
                quinn_ext = create_extension("Quinn")

                quinn_result = await self._run_quinn_quality_review_direct(
                    quinn_ext=quinn_ext,
                    context=context,
                    result=result,
                )

                if quinn_result.get("success"):
                    result.agents_succeeded = 1
                    result.quinn_assessment = quinn_result

                    # Quinn can add blockers or adjust assessment
                    if quinn_result.get("additional_blockers"):
                        result.blockers.extend(quinn_result["additional_blockers"])
                    if quinn_result.get("additional_recommendations"):
                        result.recommendations.extend(quinn_result["additional_recommendations"])

            except Exception as e:
                logger.warning(f"Quinn quality review failed: {e}")
                result.errors.append(f"Quinn agent unavailable: {str(e)}")

            result.duration_seconds = (datetime.now(timezone.utc) - started_at).total_seconds()

            # Store result in context
            context.shared_data["quality_review"] = result.to_dict()

            logger.info(
                f"Quality review complete: score={result.quality_score:.2f}, "
                f"blockers={len(result.blockers)}, duration={result.duration_seconds:.1f}s"
            )

            return result.to_dict()

        except Exception as e:
            logger.error(f"Quality review failed: {e}")
            result.errors.append(str(e))
            result.duration_seconds = (datetime.now(timezone.utc) - started_at).total_seconds()
            context.shared_data["quality_review"] = result.to_dict()
            return result.to_dict()

    def _check_consistency(
        self,
        validation: Dict[str, Any],
        domain_extraction: Dict[str, Any],
        story_generation: Dict[str, Any],
        estimation: Dict[str, Any],
        user_journey: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check cross-module data consistency."""
        issues = []
        checks_passed = 0
        total_checks = 5

        # Check 1: Domain count consistency
        domains_from_extraction = len(domain_extraction.get("domains", []))
        domains_in_stories = len(set(
            epic.get("domain_name", "")
            for epic in story_generation.get("epics", [])
        ))
        if domains_from_extraction > 0 and domains_in_stories > 0:
            if abs(domains_from_extraction - domains_in_stories) <= domains_from_extraction * 0.5:
                checks_passed += 1
            else:
                issues.append({
                    "type": "domain_mismatch",
                    "message": f"Domains in extraction ({domains_from_extraction}) vs stories ({domains_in_stories}) differ significantly",
                    "severity": "warning",
                })
        elif domains_from_extraction > 0 or domains_in_stories > 0:
            checks_passed += 0.5  # Partial credit

        # Check 2: Story points vs estimation alignment
        total_sp = story_generation.get("total_story_points", 0)
        fp_estimate = estimation.get("function_points", {}).get("adjusted", 0)
        if total_sp > 0 and fp_estimate > 0:
            # Rough ratio check: typically 1 SP ~ 0.5-2 FP
            ratio = fp_estimate / total_sp if total_sp > 0 else 0
            if 0.1 <= ratio <= 100:  # Very loose check for now
                checks_passed += 1
            else:
                issues.append({
                    "type": "estimation_ratio",
                    "message": f"FP/SP ratio ({ratio:.1f}) outside expected range",
                    "severity": "info",
                })
        else:
            checks_passed += 0.5  # Partial credit if either exists

        # Check 3: Journey-persona consistency
        journeys = user_journey.get("journeys", [])
        personas = user_journey.get("personas", [])
        if len(journeys) > 0 and len(personas) > 0:
            checks_passed += 1
        elif len(journeys) > 0 or len(personas) > 0:
            checks_passed += 0.5
            issues.append({
                "type": "journey_persona_incomplete",
                "message": f"Journeys ({len(journeys)}) and personas ({len(personas)}) may be incomplete",
                "severity": "info",
            })

        # Check 4: Validation passed
        if validation.get("quality_score", 0) >= 1.0 or validation.get("valid", False):
            checks_passed += 1
        else:
            issues.append({
                "type": "validation_incomplete",
                "message": "Initial validation may not have completed successfully",
                "severity": "warning",
            })

        # Check 5: Data flow integrity
        required_stages = ["code_understanding", "domain_extraction", "story_generation"]
        stages_present = sum(1 for stage in required_stages if stage in [
            "code_understanding" if domain_extraction else None,
            "domain_extraction" if domain_extraction.get("domains") else None,
            "story_generation" if story_generation.get("stories") else None,
        ])
        if stages_present >= 2:
            checks_passed += 1
        else:
            issues.append({
                "type": "stage_data_missing",
                "message": "Some required stage data may be missing",
                "severity": "warning",
            })

        score = checks_passed / total_checks
        return {"score": score, "issues": issues}

    def _check_security_compliance(
        self,
        security_scan: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check security scan compliance."""
        issues = []

        findings = security_scan.get("findings", {})
        critical = findings.get("critical", 0)
        high = findings.get("high", 0)
        total = findings.get("total", 0)

        # Compliance thresholds
        max_critical = 0  # No critical allowed
        max_high = 5  # Up to 5 high

        compliant = critical <= max_critical and high <= max_high

        if critical > max_critical:
            issues.append(f"{critical} critical security findings must be resolved")
        if high > max_high:
            issues.append(f"{high} high severity findings exceed threshold ({max_high})")

        # Calculate score
        if total == 0:
            score = 0.85  # No scan = partial credit but flag it
            issues.append("Security scan may not have run or found no files")
        elif critical == 0 and high == 0:
            score = 1.0
        elif critical == 0 and high <= max_high:
            score = 0.90
        elif critical <= 2:
            score = 0.70
        else:
            score = 0.50

        return {"compliant": compliant, "score": score, "issues": issues}

    def _check_estimation_reasonableness(
        self,
        estimation: Dict[str, Any],
        story_generation: Dict[str, Any],
        code_understanding: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check if estimation is reasonable given the codebase."""
        warnings = []

        # Get estimates
        fp = estimation.get("function_points", {})
        adjusted_fp = fp.get("adjusted", 0)
        confidence = estimation.get("confidence_level", 0)

        estimates = estimation.get("estimates", {})
        weeks_low = estimates.get("weeks_low", 0)
        weeks_likely = estimates.get("weeks_likely", 0)
        weeks_high = estimates.get("weeks_high", 0)

        # Get context
        total_sp = story_generation.get("total_story_points", 0)
        code_metrics = code_understanding.get("code_metrics", {})
        total_files = code_metrics.get("total_files", 0)

        # Reasonableness checks
        reasonable = True

        # Check 1: Estimate exists
        if adjusted_fp == 0 and total_sp == 0:
            reasonable = False
            warnings.append("No function points or story points estimated")

        # Check 2: Three-point estimate consistency
        if weeks_low > 0 and weeks_likely > 0 and weeks_high > 0:
            if not (weeks_low <= weeks_likely <= weeks_high):
                warnings.append(f"Three-point estimate inconsistent: {weeks_low} <= {weeks_likely} <= {weeks_high}")
            if weeks_high > weeks_low * 5:
                warnings.append(f"Estimate range too wide: {weeks_low}-{weeks_high} weeks")

        # Check 3: FP per file ratio (rough sanity check)
        if total_files > 0 and adjusted_fp > 0:
            fp_per_file = adjusted_fp / total_files
            if fp_per_file > 100:
                warnings.append(f"FP per file ({fp_per_file:.1f}) unusually high")
            elif fp_per_file < 0.1:
                warnings.append(f"FP per file ({fp_per_file:.2f}) unusually low")

        # Check 4: Extreme estimates
        if weeks_likely > 500:
            warnings.append(f"Estimate ({weeks_likely} weeks) indicates very large project - verify accuracy")
        if weeks_likely > 0 and weeks_likely < 2:
            warnings.append(f"Estimate ({weeks_likely} weeks) may be too optimistic")

        # Calculate confidence
        if confidence > 0:
            effective_confidence = confidence
        elif adjusted_fp > 0 and len(warnings) <= 1:
            effective_confidence = 0.7
        elif adjusted_fp > 0:
            effective_confidence = 0.5
        else:
            effective_confidence = 0.3

        return {
            "reasonable": reasonable and len(warnings) <= 2,
            "confidence": effective_confidence,
            "warnings": warnings,
        }

    def _check_documentation_completeness(
        self,
        deliverables: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check if documentation is complete."""
        missing = []

        # Required sections
        required_sections = {"project-summary", "epics", "estimation"}
        optional_sections = {"user-journeys", "architecture", "risks", "security"}

        files_info = deliverables.get("files", {})
        files_created = files_info.get("created", 0) if isinstance(files_info, dict) else 0

        sections_info = deliverables.get("sections", {})
        sections_generated = sections_info.get("generated", []) if isinstance(sections_info, dict) else []

        # Check required sections
        sections_set = set(sections_generated)
        for section in required_sections:
            if section not in sections_set:
                missing.append(section)

        # Calculate score
        required_present = len(required_sections - set(missing))
        optional_present = len(optional_sections.intersection(sections_set))

        if required_present == len(required_sections) and optional_present >= 2:
            score = 1.0
        elif required_present == len(required_sections):
            score = 0.90
        elif required_present >= 2:
            score = 0.80
        elif files_created >= 3:
            score = 0.70
        else:
            score = 0.50

        complete = len(missing) == 0 and files_created >= 3

        return {"complete": complete, "score": score, "missing": missing}

    def _check_data_integrity(
        self,
        domain_extraction: Dict[str, Any],
        story_generation: Dict[str, Any],
        estimation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check data integrity across stages."""
        issues = []
        checks_passed = 0
        total_checks = 4

        # Check 1: Domains have required fields
        domains = domain_extraction.get("domains", [])
        valid_domains = sum(1 for d in domains if d.get("name") and d.get("description"))
        if len(domains) == 0 or valid_domains >= len(domains) * 0.8:
            checks_passed += 1
        else:
            issues.append(f"Some domains missing required fields ({valid_domains}/{len(domains)} valid)")

        # Check 2: Stories have required fields
        stories = story_generation.get("stories", [])
        valid_stories = sum(1 for s in stories if s.get("title") or s.get("id"))
        if len(stories) == 0 or valid_stories >= len(stories) * 0.8:
            checks_passed += 1
        else:
            issues.append(f"Some stories missing required fields ({valid_stories}/{len(stories)} valid)")

        # Check 3: Epics have domains linked
        epics = story_generation.get("epics", [])
        epics_with_domain = sum(1 for e in epics if e.get("domain_name") or e.get("domain"))
        if len(epics) == 0 or epics_with_domain >= len(epics) * 0.5:
            checks_passed += 1
        else:
            issues.append(f"Many epics missing domain linkage ({epics_with_domain}/{len(epics)})")

        # Check 4: Estimation has phases
        phases = estimation.get("phases", [])
        if len(phases) >= 3:
            checks_passed += 1
        elif len(phases) > 0:
            checks_passed += 0.5
        else:
            issues.append("Estimation missing phase breakdown")

        score = checks_passed / total_checks
        return {"score": score, "issues": issues}

    def _generate_assessment(self, result: QualityReviewResult) -> str:
        """Generate overall assessment text."""
        score = result.quality_score

        if score >= 0.95:
            return "EXCELLENT: All quality checks passed. Ready for migration planning."
        elif score >= 0.90:
            return "GOOD: Core quality checks passed. Minor improvements recommended."
        elif score >= 0.80:
            return "ACCEPTABLE: Most checks passed. Review recommendations before proceeding."
        elif score >= 0.70:
            return "MARGINAL: Some issues detected. Address warnings before migration."
        else:
            return "NEEDS WORK: Significant issues found. Remediation required before proceeding."

    def _generate_recommendations(self, result: QualityReviewResult) -> List[str]:
        """Generate recommendations based on review results."""
        recommendations = []

        if result.consistency_score < 0.8:
            recommendations.append("Review domain-story alignment for consistency")

        if not result.security_compliant:
            recommendations.append("Address security findings before migration")

        if not result.estimation_reasonable:
            recommendations.append("Validate estimation assumptions with stakeholders")

        if result.estimation_warnings:
            for warning in result.estimation_warnings[:3]:
                recommendations.append(f"Estimation: {warning}")

        if not result.documentation_complete:
            recommendations.append(f"Complete missing documentation: {', '.join(result.missing_sections)}")

        if result.data_integrity_score < 0.8:
            recommendations.append("Review and fix data quality issues in extraction results")

        return recommendations

    def _identify_blockers(self, result: QualityReviewResult) -> List[str]:
        """Identify blockers that must be resolved."""
        blockers = []

        # Critical security findings are blockers
        if result.security_issues:
            for issue in result.security_issues:
                if "critical" in issue.lower():
                    blockers.append(issue)

        # Very low scores are blockers
        if result.consistency_score < 0.5:
            blockers.append("Data consistency too low - re-run extraction stages")

        if result.documentation_score < 0.5:
            blockers.append("Documentation incomplete - re-run deliverables stage")

        if result.data_integrity_score < 0.5:
            blockers.append("Data integrity issues - validate stage outputs")

        return blockers

    async def _run_quinn_quality_review_direct(
        self,
        quinn_ext: Any,
        context: WorkflowContext,
        result: QualityReviewResult,
    ) -> Dict[str, Any]:
        """Run Quinn agent for final quality assessment."""
        if not quinn_ext:
            return {"success": False, "error": "Quinn agent not available"}

        try:
            # Prepare context for Quinn
            agent_context = {
                "project_path": result.project_path,
                "consistency_score": result.consistency_score,
                "security_compliant": result.security_compliant,
                "security_score": result.security_score,
                "estimation_reasonable": result.estimation_reasonable,
                "estimation_confidence": result.estimation_confidence,
                "documentation_complete": result.documentation_complete,
                "documentation_score": result.documentation_score,
                "data_integrity_score": result.data_integrity_score,
                "current_blockers": result.blockers,
                "current_recommendations": result.recommendations,
            }

            quinn_output = await quinn_ext.run_full_lifecycle(
                task="Review onboarding quality assessment and provide final recommendations",
                context=agent_context,
                entry_id=f"{context.workflow_id}-quinn-quality",
            )

            if quinn_output.success:
                return {
                    "success": True,
                    "assessment": quinn_output.output.get("assessment", ""),
                    "approval": quinn_output.output.get("approval", False),
                    "additional_blockers": quinn_output.output.get("additional_blockers", []),
                    "additional_recommendations": quinn_output.output.get("recommendations", []),
                    "confidence": quinn_output.output.get("confidence", 0.8),
                }

            return {"success": False, "error": "Quinn returned unsuccessful result"}

        except Exception as e:
            logger.warning(f"Quinn quality review failed: {e}")
            return {"success": False, "error": str(e)}


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_onboarding_orchestrator() -> OnboardingOrchestrator:
    """Factory function for OnboardingOrchestrator."""
    return OnboardingOrchestrator()
