"""
Software Intake Pydantic Schemas.

Week 158 - Fase 1: SoftwareIntakeService

Complete schema definitions for code-driven software analysis.
These schemas serve as the contract between backend and frontend.

Output Structure:
- summary: Dashboard header KPIs
- findings: Centralized findings with severity/category grouping
- code_metrics: Detailed code analysis
- security: CWE/OWASP security findings
- estimation: Function Points and effort
- architecture: Detected patterns and recommendations
- dependencies: Internal/external dependency analysis
- business_rules: Extracted business logic
- technical_debt: Quantified debt analysis
- eol_analysis: End-of-life component detection
- license_compliance: Open source license risks
- privacy_analysis: GDPR/PII detection
- test_coverage: Test analysis
- api_surface: Exposed API analysis
- performance_hotspots: Performance issues
- skills_assessment: Required skills for modernization
- quick_wins: Low-effort high-impact improvements
- tco_comparison: Total Cost of Ownership analysis
- recommendations: Prioritized action items
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# ENUMS
# =============================================================================

class IntakeStatus(str, Enum):
    """Status of intake analysis."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, Enum):
    """Finding severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingCategory(str, Enum):
    """Categories for findings."""
    SECURITY = "security"
    QUALITY = "quality"
    ARCHITECTURE = "architecture"
    MAINTAINABILITY = "maintainability"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    DOCUMENTATION = "documentation"
    TESTING = "testing"


class Complexity(str, Enum):
    """Complexity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ConfidenceLevel(str, Enum):
    """Confidence levels for estimates."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EOLStatus(str, Enum):
    """End-of-life status."""
    SUPPORTED = "supported"
    DEPRECATED = "deprecated"
    EOL = "eol"
    UNSUPPORTED = "unsupported"


class LicenseRisk(str, Enum):
    """License risk levels."""
    SAFE = "safe"
    REVIEW = "review"
    COPYLEFT = "copyleft"
    UNKNOWN = "unknown"


# =============================================================================
# BASE MODELS
# =============================================================================

class Location(BaseModel):
    """Source code location."""
    file_path: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class SuggestedFix(BaseModel):
    """Suggested fix for a finding."""
    description: str
    code_before: Optional[str] = None
    code_after: Optional[str] = None
    effort_hours: Optional[float] = None
    automated: bool = False


# =============================================================================
# FINDINGS (Centralized)
# =============================================================================

class Finding(BaseModel):
    """Single finding/issue detected during analysis."""
    id: str = Field(..., description="Unique finding ID (e.g., SEC-001, QUAL-023)")
    severity: Severity
    category: FindingCategory
    title: str
    description: str
    location: Optional[Location] = None

    # CWE/OWASP references
    cwe_id: Optional[str] = Field(None, description="CWE identifier (e.g., CWE-89)")
    owasp_category: Optional[str] = Field(None, description="OWASP category (e.g., A03:2021)")

    # Remediation
    remediation: Optional[str] = None
    suggested_fix: Optional[SuggestedFix] = None
    effort_hours: Optional[float] = Field(None, description="Estimated hours to fix")

    # References
    references: List[str] = Field(default_factory=list)

    # Metadata
    confidence: float = Field(0.9, ge=0.0, le=1.0)
    scanner: Optional[str] = Field(None, description="Scanner that detected this")
    first_detected: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FindingSummary(BaseModel):
    """Summary counts for findings."""
    total: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0

    model_config = ConfigDict(from_attributes=True)


class CategoryFindings(BaseModel):
    """Findings grouped by category."""
    count: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    items: List[Finding] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class RoadmapPhase(BaseModel):
    """Phase in the remediation roadmap."""
    phase: int
    title: str
    description: Optional[str] = None
    effort_weeks: float
    findings_addressed: List[str] = Field(default_factory=list, description="Finding IDs addressed")
    risk_reduction_percent: float = Field(..., ge=0, le=100)
    dependencies: List[int] = Field(default_factory=list, description="Phase numbers that must complete first")

    model_config = ConfigDict(from_attributes=True)


class FindingsReport(BaseModel):
    """Centralized findings report - the heart of intake analysis."""
    summary: FindingSummary = Field(default_factory=FindingSummary)

    # Grouped by category
    by_category: Dict[str, CategoryFindings] = Field(
        default_factory=lambda: {cat.value: CategoryFindings() for cat in FindingCategory}
    )

    # Top priority items for executive summary
    top_10_priority: List[Finding] = Field(default_factory=list)

    # Remediation roadmap
    roadmap: List[RoadmapPhase] = Field(default_factory=list)

    # Health score (0-100, higher = healthier)
    health_score: int = Field(50, ge=0, le=100)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SUMMARY
# =============================================================================

class IntakeSummary(BaseModel):
    """Dashboard header summary - quick overview KPIs."""
    total_files: int = 0
    total_loc: int = Field(0, description="Total lines of code")
    total_blank_lines: int = 0
    total_comment_lines: int = 0

    # Detected technologies
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)

    # Primary stack detection
    primary_language: Optional[str] = None
    primary_framework: Optional[str] = None

    # Health indicators
    health_score: int = Field(50, ge=0, le=100, description="Overall health 0-100")
    migration_complexity: Complexity = Complexity.MEDIUM

    # Quick stats
    security_issues_count: int = 0
    quality_issues_count: int = 0
    deprecated_dependencies_count: int = 0

    # Generated code summary (populated after generated code detection phase)
    generated_files_count: int = 0
    generated_loc: int = 0
    generated_percentage: float = Field(
        0.0, ge=0.0, le=100.0,
        description="Percentage of LOC that is generated code"
    )

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# CODE METRICS
# =============================================================================

class LanguageMetrics(BaseModel):
    """Metrics for a single programming language."""
    language: str
    file_count: int = 0
    loc: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    percentage: float = Field(0.0, ge=0, le=100)

    model_config = ConfigDict(from_attributes=True)


class DirectoryMetrics(BaseModel):
    """Metrics for a directory."""
    path: str
    file_count: int = 0
    loc: int = 0
    languages: List[str] = Field(default_factory=list)
    complexity_avg: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ComplexityDistribution(BaseModel):
    """Distribution of code complexity."""
    low: int = Field(0, description="Cyclomatic < 5")
    medium: int = Field(0, description="Cyclomatic 5-10")
    high: int = Field(0, description="Cyclomatic 10-20")
    very_high: int = Field(0, description="Cyclomatic > 20")

    avg_cyclomatic: float = 0.0
    max_cyclomatic: float = 0.0
    avg_cognitive: float = 0.0

    hotspots: List[Location] = Field(default_factory=list, description="Files with highest complexity")

    model_config = ConfigDict(from_attributes=True)


class CodeMetrics(BaseModel):
    """Detailed code analysis metrics."""
    by_language: List[LanguageMetrics] = Field(default_factory=list)
    by_directory: List[DirectoryMetrics] = Field(default_factory=list)

    complexity_distribution: ComplexityDistribution = Field(default_factory=ComplexityDistribution)

    # Duplication
    duplicate_code_percent: float = Field(0.0, ge=0, le=100)
    duplicate_blocks: int = 0
    largest_duplicate_lines: int = 0

    # Code smells (non-security)
    god_classes: List[Location] = Field(default_factory=list)
    long_methods: List[Location] = Field(default_factory=list)
    deep_nesting: List[Location] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SECURITY
# =============================================================================

class OWASPCoverage(BaseModel):
    """OWASP Top 10 coverage analysis."""
    category: str = Field(..., description="e.g., A01:2021-Broken Access Control")
    finding_count: int = 0
    critical_count: int = 0
    covered: bool = Field(False, description="Whether this category was scanned")

    model_config = ConfigDict(from_attributes=True)


class CWECoverage(BaseModel):
    """CWE coverage for a specific weakness."""
    cwe_id: str
    name: str
    finding_count: int = 0
    severity_distribution: Dict[str, int] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class SecurityReport(BaseModel):
    """Security analysis report."""
    risk_score: float = Field(0.0, ge=0, le=100, description="Higher = more risk")

    findings_by_severity: Dict[str, int] = Field(
        default_factory=lambda: {"critical": 0, "high": 0, "medium": 0, "low": 0}
    )

    owasp_coverage: List[OWASPCoverage] = Field(default_factory=list)
    cwe_coverage: List[CWECoverage] = Field(default_factory=list)

    # Top findings for quick view
    top_findings: List[Finding] = Field(default_factory=list, max_length=10)

    # Migration blockers (critical issues that must be fixed)
    migration_blockers: List[Finding] = Field(default_factory=list)

    # Estimated remediation
    estimated_remediation_hours: float = 0.0

    # Scanners used
    scanners_used: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# ESTIMATION (Function Points)
# =============================================================================

class FunctionPointComponent(BaseModel):
    """Individual function point component."""
    name: str
    component_type: str = Field(..., description="EI, EO, EQ, ILF, EIF")
    complexity: Complexity
    unadjusted_fp: float
    file_path: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PhaseEstimate(BaseModel):
    """Effort estimate for a migration phase."""
    phase: str
    description: str
    activities: List[str] = Field(default_factory=list)
    base_hours: float
    risk_buffer_hours: float = 0.0
    total_hours: float
    percentage_of_total: float = Field(0.0, ge=0, le=100)

    model_config = ConfigDict(from_attributes=True)


class EstimationReport(BaseModel):
    """Migration effort estimation report."""
    # Function Points
    function_points_unadjusted: int = 0
    value_adjustment_factor: float = Field(1.0, ge=0.65, le=1.35)
    function_points_adjusted: int = 0

    # Effort
    effort_hours: float = 0.0
    effort_person_days: float = 0.0
    effort_person_months: float = 0.0

    # Phases
    phases: List[PhaseEstimate] = Field(default_factory=list)

    # Confidence
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_factors: List[str] = Field(default_factory=list)

    # Components breakdown
    components_by_type: Dict[str, int] = Field(default_factory=dict)
    top_components: List[FunctionPointComponent] = Field(default_factory=list)

    # Source/target info
    source_stack: Optional[str] = None
    target_stack: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# ARCHITECTURE
# =============================================================================

class DetectedLayer(BaseModel):
    """Detected architectural layer."""
    name: str
    description: str
    directories: List[str] = Field(default_factory=list)
    file_count: int = 0
    loc: int = 0

    model_config = ConfigDict(from_attributes=True)


class ComponentMapping(BaseModel):
    """Mapping from legacy to target component."""
    legacy_component: str
    legacy_type: str
    legacy_location: str
    target_component: str
    target_type: str
    migration_strategy: str
    effort_hours: float = 0.0
    complexity: Complexity = Complexity.MEDIUM

    model_config = ConfigDict(from_attributes=True)


class ArchitectureDecisionRecord(BaseModel):
    """ADR for architecture decisions."""
    id: str
    title: str
    status: str = Field("proposed", description="proposed, accepted, deprecated, superseded")
    context: str
    decision: str
    consequences: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ArchitectureReport(BaseModel):
    """Architecture analysis report."""
    # Detected patterns
    detected_patterns: List[str] = Field(default_factory=list)
    detected_layers: List[DetectedLayer] = Field(default_factory=list)

    # Recommendations
    recommended_pattern: Optional[str] = None
    recommended_strategy: Optional[str] = None

    # Component mapping
    component_mapping: List[ComponentMapping] = Field(default_factory=list)

    # Target stack suggestions
    target_stack_suggestions: List[Dict[str, Any]] = Field(default_factory=list)

    # ADRs
    architecture_decisions: List[ArchitectureDecisionRecord] = Field(default_factory=list)

    # Issues
    architecture_issues: List[Finding] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# DEPENDENCIES
# =============================================================================

class InternalDependency(BaseModel):
    """Internal module dependency."""
    source_module: str
    target_module: str
    dependency_type: str = Field("import", description="import, call, extend")
    coupling_strength: str = Field("normal", description="weak, normal, strong")

    model_config = ConfigDict(from_attributes=True)


class ExternalLibrary(BaseModel):
    """External library/package dependency."""
    name: str
    version: Optional[str] = None
    latest_version: Optional[str] = None
    package_manager: str = Field(..., description="nuget, npm, pip, maven, etc.")

    # Risk assessment
    eol_status: EOLStatus = EOLStatus.SUPPORTED
    eol_date: Optional[str] = None
    license: Optional[str] = None
    license_risk: LicenseRisk = LicenseRisk.SAFE

    # CVE info
    known_vulnerabilities: int = 0
    critical_vulnerabilities: int = 0

    # Usage
    usage_count: int = 0
    direct_dependency: bool = True

    model_config = ConfigDict(from_attributes=True)


class DatabaseConnection(BaseModel):
    """Database connection detected."""
    database_type: str
    connection_string_location: Optional[Location] = None
    tables_referenced: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class APIIntegration(BaseModel):
    """External API integration detected."""
    name: str
    url_pattern: Optional[str] = None
    protocol: str = Field("http", description="http, grpc, soap, etc.")
    locations: List[Location] = Field(default_factory=list)
    authentication_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DependencyReport(BaseModel):
    """Dependency analysis report."""
    # Internal
    internal_dependencies: List[InternalDependency] = Field(default_factory=list)
    circular_dependencies: List[List[str]] = Field(default_factory=list)

    # External
    external_libraries: List[ExternalLibrary] = Field(default_factory=list)
    total_dependencies: int = 0
    outdated_dependencies: int = 0
    vulnerable_dependencies: int = 0

    # Database
    database_connections: List[DatabaseConnection] = Field(default_factory=list)

    # API integrations
    api_integrations: List[APIIntegration] = Field(default_factory=list)

    # Dependency graph (for visualization)
    dependency_graph: Optional[Dict[str, Any]] = Field(None, description="D3.js compatible graph data")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# BUSINESS RULES
# =============================================================================

class ExtractedBusinessRule(BaseModel):
    """Business rule extracted from code."""
    id: str
    name: str
    description: str
    rule_type: str = Field(..., description="validation, calculation, workflow, constraint")

    # Source
    location: Location
    code_snippet: Optional[str] = None

    # Domain
    domain: Optional[str] = None
    entities_involved: List[str] = Field(default_factory=list)

    # Complexity
    complexity: Complexity = Complexity.MEDIUM
    confidence: float = Field(0.8, ge=0, le=1)

    model_config = ConfigDict(from_attributes=True)


class BusinessRulesReport(BaseModel):
    """Business rules extraction report."""
    extracted_count: int = 0

    by_domain: Dict[str, List[ExtractedBusinessRule]] = Field(default_factory=dict)
    by_type: Dict[str, int] = Field(default_factory=dict)

    validation_rules: List[ExtractedBusinessRule] = Field(default_factory=list)
    calculations: List[ExtractedBusinessRule] = Field(default_factory=list)
    workflows: List[ExtractedBusinessRule] = Field(default_factory=list)
    constraints: List[ExtractedBusinessRule] = Field(default_factory=list)

    # Entities detected
    entities: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# TECHNICAL DEBT
# =============================================================================

class DebtCategory(BaseModel):
    """Technical debt by category."""
    category: str
    hours: float = 0.0
    cost_eur: float = 0.0
    finding_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class TechnicalDebtReport(BaseModel):
    """Technical debt quantification report."""
    total_hours: float = 0.0
    total_cost_eur: float = Field(0.0, description="At default rate of 100 EUR/hour")
    hourly_rate_eur: float = 100.0

    by_category: List[DebtCategory] = Field(default_factory=list)

    debt_ratio: float = Field(0.0, ge=0, le=1, description="Debt hours / total development hours")
    debt_trend: Optional[str] = Field(None, description="increasing, stable, decreasing")

    payoff_recommendation: Optional[str] = None
    priority_items: List[str] = Field(default_factory=list, description="Finding IDs to address first")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# EOL ANALYSIS
# =============================================================================

class EOLComponent(BaseModel):
    """Component with EOL information."""
    name: str
    version: Optional[str] = None
    eol_date: Optional[str] = None
    status: EOLStatus
    replacement: Optional[str] = None
    migration_effort_hours: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class EOLAnalysisReport(BaseModel):
    """End-of-life analysis report."""
    critical: List[EOLComponent] = Field(default_factory=list, description="Already EOL/unsupported")
    warning: List[EOLComponent] = Field(default_factory=list, description="EOL within 12 months")
    monitor: List[EOLComponent] = Field(default_factory=list, description="EOL within 24 months")

    total_unsupported_dependencies: int = 0
    security_risk: Severity = Severity.LOW

    recommended_actions: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# LICENSE COMPLIANCE
# =============================================================================

class LicenseIssue(BaseModel):
    """License compliance issue."""
    package: str
    license: str
    risk: LicenseRisk
    description: str
    recommendation: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LicenseComplianceReport(BaseModel):
    """License compliance report."""
    compliant: bool = True

    risks: List[LicenseIssue] = Field(default_factory=list)

    commercial_safe: List[str] = Field(default_factory=list, description="Safe licenses found")
    requires_review: List[str] = Field(default_factory=list, description="Licenses needing legal review")
    copyleft_detected: List[str] = Field(default_factory=list, description="Copyleft licenses")
    unknown_licenses: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# PRIVACY ANALYSIS (GDPR)
# =============================================================================

class PIILocation(BaseModel):
    """Location where PII is processed."""
    location: Location
    data_type: str = Field(..., description="email, phone, address, credit_card, ssn, etc.")
    storage: str = Field(..., description="database, file, log, session, memory")
    encrypted: bool = False

    model_config = ConfigDict(from_attributes=True)


class GDPRRisk(BaseModel):
    """GDPR compliance risk."""
    category: str = Field(..., description="data_retention, logging, consent, transfer, etc.")
    finding: str
    severity: Severity
    recommendation: str

    model_config = ConfigDict(from_attributes=True)


class PrivacyAnalysisReport(BaseModel):
    """GDPR/Privacy analysis report."""
    pii_locations: List[PIILocation] = Field(default_factory=list)

    gdpr_risks: List[GDPRRisk] = Field(default_factory=list)

    dpia_required: bool = Field(False, description="Data Protection Impact Assessment required")

    data_types_found: List[str] = Field(default_factory=list)
    sensitive_data_count: int = 0

    recommendations: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# TEST COVERAGE
# =============================================================================

class TestFile(BaseModel):
    """Detected test file."""
    path: str
    test_type: str = Field(..., description="unit, integration, e2e, performance")
    test_count: int = 0
    framework: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TestCoverageReport(BaseModel):
    """Test coverage analysis report."""
    has_tests: bool = False

    unit_tests: int = 0
    integration_tests: int = 0
    e2e_tests: int = 0
    performance_tests: int = 0

    test_files: List[TestFile] = Field(default_factory=list)

    estimated_coverage_percent: float = Field(0.0, ge=0, le=100)

    test_frameworks_detected: List[str] = Field(default_factory=list)

    untested_critical_paths: List[str] = Field(default_factory=list)

    recommendations: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# API SURFACE
# =============================================================================

class APIEndpoint(BaseModel):
    """Detected API endpoint."""
    path: str
    method: str = "GET"
    authenticated: bool = True
    deprecated: bool = False
    documented: bool = False
    location: Optional[Location] = None

    model_config = ConfigDict(from_attributes=True)


class APISurfaceReport(BaseModel):
    """API surface analysis report."""
    total_endpoints: int = 0
    authenticated: int = 0
    unauthenticated: int = 0
    deprecated: int = 0
    undocumented: int = 0

    endpoints: List[APIEndpoint] = Field(default_factory=list)

    api_versions_detected: List[str] = Field(default_factory=list)

    breaking_change_risks: List[Dict[str, Any]] = Field(default_factory=list)

    recommendations: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# PERFORMANCE HOTSPOTS
# =============================================================================

class PerformanceIssue(BaseModel):
    """Performance issue detected."""
    issue_type: str = Field(..., description="n_plus_one, memory_leak, sync_over_async, etc.")
    severity: Severity
    location: Location
    description: str
    remediation: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PerformanceHotspotsReport(BaseModel):
    """Performance hotspots report."""
    n_plus_one_queries: List[PerformanceIssue] = Field(default_factory=list)
    unbounded_loops: int = 0
    memory_leak_risks: int = 0
    sync_over_async: int = 0

    all_issues: List[PerformanceIssue] = Field(default_factory=list)

    estimated_performance_debt_hours: float = 0.0

    recommendations: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SKILLS ASSESSMENT
# =============================================================================

class SkillGap(BaseModel):
    """Identified skill gap."""
    skill: str
    current_level: str = Field("none", description="none, basic, intermediate, advanced")
    required_level: str = "intermediate"
    training_hours: float = 0.0
    priority: Severity = Severity.MEDIUM

    model_config = ConfigDict(from_attributes=True)


class SkillsAssessmentReport(BaseModel):
    """Skills assessment for modernization."""
    current_stack_skills: List[str] = Field(default_factory=list)
    target_stack_skills: List[str] = Field(default_factory=list)

    skill_gaps: List[SkillGap] = Field(default_factory=list)

    training_hours_estimate: float = 0.0
    training_cost_estimate_eur: float = 0.0

    recommended_training: List[str] = Field(default_factory=list)
    hiring_recommendations: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# QUICK WINS
# =============================================================================

class QuickWin(BaseModel):
    """Quick win - low effort, high impact improvement."""
    title: str
    description: str
    effort_hours: float
    impact: Severity = Field(..., description="Impact level if implemented")
    reduces_risk: List[str] = Field(default_factory=list, description="Risk categories reduced")
    findings_addressed: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# TCO COMPARISON
# =============================================================================

class TCOScenario(BaseModel):
    """Total Cost of Ownership scenario."""
    name: str
    one_time_cost_eur: float = 0.0
    annual_cost_eur: float = 0.0
    five_year_cost_eur: float = 0.0
    risks: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TCOComparisonReport(BaseModel):
    """Total Cost of Ownership comparison."""
    maintain_as_is: TCOScenario
    migrate: TCOScenario

    break_even_years: Optional[float] = None

    recommendation: str = Field(..., description="maintain or migrate")
    recommendation_reason: str

    assumptions: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# RECOMMENDATIONS
# =============================================================================

class Recommendation(BaseModel):
    """Actionable recommendation."""
    id: str
    priority: Severity
    category: FindingCategory
    title: str
    description: str
    effort_hours: Optional[float] = None
    impact: str
    findings_addressed: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# GENERATED CODE REPORT
# =============================================================================

class GeneratedFileInfo(BaseModel):
    """Information about a generated file."""
    file_path: str
    generator_type: str = "unknown"
    detection_method: str = Field(
        "", description="directory, file_pattern, or content_marker"
    )
    matched_pattern: str = ""
    confidence: float = Field(1.0, ge=0.0, le=1.0)

    model_config = ConfigDict(from_attributes=True)


class GeneratedCodeReport(BaseModel):
    """
    Generated Code Analysis Report.

    Identifies auto-generated code to enable proper metric handling:
    - Generated code: Include in SECURITY scans and VOLUME metrics
    - Generated code: EXCLUDE from QUALITY metrics (complexity, duplication, etc.)
    """
    total_files: int = 0
    generated_files: int = 0
    handwritten_files: int = 0
    generated_loc: int = 0
    handwritten_loc: int = 0
    generated_percentage: float = Field(
        0.0, ge=0.0, le=100.0, description="Percentage of files that are generated"
    )

    # Breakdown by generator type
    by_generator_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of files by generator type (vs_designer, wcf_service, etc.)"
    )

    # Breakdown by directory
    by_directory: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of generated files by directory pattern"
    )

    # Breakdown by detection method
    by_detection_method: Dict[str, int] = Field(
        default_factory=dict,
        description="Count by detection method: directory, file_pattern, content_marker"
    )

    # Top generated directories
    top_generated_directories: List[str] = Field(
        default_factory=list,
        description="Top directories containing generated code"
    )

    # Detailed file list (optional, may be truncated)
    generated_file_list: List[GeneratedFileInfo] = Field(
        default_factory=list,
        description="List of generated files (may be limited to first 100)"
    )

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# MAIN INTAKE REPORT
# =============================================================================

class IntakeReport(BaseModel):
    """
    Complete Software Intake Report.

    This is the main output of the SoftwareIntakeService.
    All sections are optional to support incremental analysis.
    """
    # Identification
    id: UUID
    project_path: str
    project_name: Optional[str] = None

    # Timing
    analyzed_at: datetime
    analysis_duration_seconds: Optional[float] = None

    # Status
    status: IntakeStatus = IntakeStatus.COMPLETED
    progress_percent: int = Field(100, ge=0, le=100)
    error_message: Optional[str] = None

    # Core sections
    summary: IntakeSummary = Field(default_factory=IntakeSummary)
    findings: FindingsReport = Field(default_factory=FindingsReport)
    generated_code: Optional[GeneratedCodeReport] = Field(
        None,
        description="Generated code detection results - used for metric filtering"
    )

    # Detailed analysis sections
    code_metrics: Optional[CodeMetrics] = None
    security: Optional[SecurityReport] = None
    estimation: Optional[EstimationReport] = None
    architecture: Optional[ArchitectureReport] = None
    dependencies: Optional[DependencyReport] = None
    business_rules: Optional[BusinessRulesReport] = None

    # Additional analysis sections
    technical_debt: Optional[TechnicalDebtReport] = None
    eol_analysis: Optional[EOLAnalysisReport] = None
    license_compliance: Optional[LicenseComplianceReport] = None
    privacy_analysis: Optional[PrivacyAnalysisReport] = None
    test_coverage: Optional[TestCoverageReport] = None
    api_surface: Optional[APISurfaceReport] = None
    performance_hotspots: Optional[PerformanceHotspotsReport] = None
    skills_assessment: Optional[SkillsAssessmentReport] = None

    # Actionable outputs
    quick_wins: List[QuickWin] = Field(default_factory=list)
    tco_comparison: Optional[TCOComparisonReport] = None
    recommendations: List[Recommendation] = Field(default_factory=list)

    # Metadata
    scanners_used: List[str] = Field(default_factory=list)
    analysis_options: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class IntakeOptions(BaseModel):
    """Options for intake analysis."""
    include_security: bool = True
    include_estimation: bool = True
    include_architecture: bool = True
    include_dependencies: bool = True
    include_business_rules: bool = True
    include_technical_debt: bool = True
    include_eol_analysis: bool = True
    include_license_compliance: bool = True
    include_privacy_analysis: bool = True
    include_test_coverage: bool = True
    include_api_surface: bool = True
    include_performance: bool = True
    include_skills_assessment: bool = True
    include_tco: bool = True

    depth: str = Field("standard", description="quick, standard, deep")

    # Target for TCO/skills analysis
    target_stack: Optional[str] = None
    target_database: Optional[str] = None

    # Custom rates
    hourly_rate_eur: float = 100.0

    model_config = ConfigDict(from_attributes=True)


class IntakeRequest(BaseModel):
    """Request to start intake analysis."""
    project_path: str = Field(..., description="Absolute path to source code")
    project_name: Optional[str] = None
    options: IntakeOptions = Field(default_factory=IntakeOptions)

    model_config = ConfigDict(from_attributes=True)


class IntakeProgressResponse(BaseModel):
    """Progress response during analysis."""
    intake_id: UUID
    status: IntakeStatus
    progress_percent: int = Field(0, ge=0, le=100)
    current_phase: Optional[str] = None
    eta_seconds: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class IntakeListResponse(BaseModel):
    """List of intake analyses."""
    items: List[IntakeReport]
    total: int
    page: int = 1
    page_size: int = 20

    model_config = ConfigDict(from_attributes=True)
