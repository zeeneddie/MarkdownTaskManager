# Extraction Services Package - Week 102-106
# Functional Requirements and NFR extraction services

"""
Extraction Services

Week 102 Quick Wins:
- FR-QW-1: Few-Shot Templates per Domain
- FR-QW-2: INVEST Validator
- FR-QW-3: Acceptance Criteria Enhancer
- NFR-QW-1: Quantitative NFR Detector
- NFR-QW-2: NFR Priority Scoring
- NFR-QW-3: Industry Standard NFR Templates

Week 105-106 Medium Improvements:
- BR-M-1: Semantic Rule Analyzer
- BR-M-2: Rule Dependency Detector
- FR-M-1: Traceability Matrix Generator
- NFR-M-1: NFR Architecture Mapper
"""

# FR-QW-1: Few-Shot Templates
from .few_shot_templates import (
    FewShotTemplateLoader,
    FewShotExample,
    DomainTemplateSet,
    ExtractionDomain,
    HEALTHCARE_TEMPLATES,
    FINANCE_TEMPLATES,
    ECOMMERCE_TEMPLATES,
    GENERIC_TEMPLATES,
)

# FR-QW-2: INVEST Validator
from .invest_validator import (
    INVESTValidator,
    INVESTCriterion,
    INVESTIssue,
    IssueSeverity,
    CriterionScore,
    UserStory,
    INVESTValidationResult,
    validate_story,
    quick_score,
    is_invest_compliant,
)

# FR-QW-3: Acceptance Criteria Enhancer
from .acceptance_criteria_enhancer import (
    AcceptanceCriteriaEnhancer,
    ACType,
    ScenarioType,
    GherkinScenario,
    EnhancedAcceptanceCriteria,
    ACEnhancementResult,
    enhance_ac,
    to_gherkin,
    generate_feature_file,
)

# NFR-QW-1: Quantitative NFR Detector
from .quantitative_nfr_detector import (
    QuantitativeNFRDetector,
    NFRCategory,
    MetricUnit,
    ThresholdType,
    QuantitativeMetric,
    QuantitativeNFR,
    NFRDetectionResult,
    detect_nfrs,
    extract_metrics,
    has_quantitative_nfrs,
)

# NFR-QW-2: NFR Priority Scoring
from .nfr_priority_scorer import (
    NFRPriorityScorer,
    NFRInput,
    NFRPriorityResult,
    BulkPriorityResult,
    PriorityTier,
    BusinessDomain,
    RiskLevel,
    ScoringFactor,
    score_nfr,
    prioritize_nfrs,
    get_priority_tier,
)

# NFR-QW-3: Industry Standard NFR Templates
from .industry_nfr_templates import (
    IndustryNFRTemplateLoader,
    IndustryStandard,
    NFRDomain,
    ComplianceLevel,
    NFRTemplate,
    TemplateSet,
    ISO_25010_TEMPLATES,
    HIPAA_TEMPLATES,
    PCI_DSS_TEMPLATES,
    NEN_7510_TEMPLATES,
    GDPR_TEMPLATES,
    get_hipaa_templates,
    get_pci_templates,
    get_gdpr_templates,
    get_iso25010_templates,
    get_nen7510_templates,
    generate_compliance_checklist,
)

# BR-M-1: Semantic Rule Analyzer
from .semantic_rule_analyzer import (
    SemanticRuleAnalyzer,
    LLMRuleEnhancer,
    RuleCategory,
    RuleConfidence,
    ExtractedRule,
    RulePattern,
)

# BR-M-2: Rule Dependency Detector
from .rule_dependency_detector import (
    RuleDependencyDetector,
    DependencyType,
    ConflictSeverity,
    RuleDependency,
    RuleConflict,
    RuleGraph,
)

# FR-M-1: Traceability Matrix Generator
from .traceability_matrix_generator import (
    TraceabilityMatrixGenerator,
    TraceabilityMatrix,
    ArtifactType,
    LinkType,
    CoverageStatus,
    TraceableArtifact,
    TraceLink,
    CoverageReport,
)

# NFR-M-1: NFR Architecture Mapper
from .nfr_architecture_mapper import (
    NFRArchitectureMapper,
    NFRCategory as NFRMappingCategory,
    ArchitecturalPattern,
    ImplementationStatus,
    NFRequirement,
    ArchitecturalComponent,
    NFRMapping,
    NFR_PATTERN_MAPPING,
    PATTERN_CODE_INDICATORS,
)

__all__ = [
    # FR-QW-1: Few-Shot Templates
    "FewShotTemplateLoader",
    "FewShotExample",
    "DomainTemplateSet",
    "ExtractionDomain",
    "HEALTHCARE_TEMPLATES",
    "FINANCE_TEMPLATES",
    "ECOMMERCE_TEMPLATES",
    "GENERIC_TEMPLATES",
    # FR-QW-2: INVEST Validator
    "INVESTValidator",
    "INVESTCriterion",
    "INVESTIssue",
    "IssueSeverity",
    "CriterionScore",
    "UserStory",
    "INVESTValidationResult",
    "validate_story",
    "quick_score",
    "is_invest_compliant",
    # FR-QW-3: Acceptance Criteria Enhancer
    "AcceptanceCriteriaEnhancer",
    "ACType",
    "ScenarioType",
    "GherkinScenario",
    "EnhancedAcceptanceCriteria",
    "ACEnhancementResult",
    "enhance_ac",
    "to_gherkin",
    "generate_feature_file",
    # NFR-QW-1: Quantitative NFR Detector
    "QuantitativeNFRDetector",
    "NFRCategory",
    "MetricUnit",
    "ThresholdType",
    "QuantitativeMetric",
    "QuantitativeNFR",
    "NFRDetectionResult",
    "detect_nfrs",
    "extract_metrics",
    "has_quantitative_nfrs",
    # NFR-QW-2: NFR Priority Scoring
    "NFRPriorityScorer",
    "NFRInput",
    "NFRPriorityResult",
    "BulkPriorityResult",
    "PriorityTier",
    "BusinessDomain",
    "RiskLevel",
    "ScoringFactor",
    "score_nfr",
    "prioritize_nfrs",
    "get_priority_tier",
    # NFR-QW-3: Industry Standard NFR Templates
    "IndustryNFRTemplateLoader",
    "IndustryStandard",
    "NFRDomain",
    "ComplianceLevel",
    "NFRTemplate",
    "TemplateSet",
    "ISO_25010_TEMPLATES",
    "HIPAA_TEMPLATES",
    "PCI_DSS_TEMPLATES",
    "NEN_7510_TEMPLATES",
    "GDPR_TEMPLATES",
    "get_hipaa_templates",
    "get_pci_templates",
    "get_gdpr_templates",
    "get_iso25010_templates",
    "get_nen7510_templates",
    "generate_compliance_checklist",
    # BR-M-1: Semantic Rule Analyzer
    "SemanticRuleAnalyzer",
    "LLMRuleEnhancer",
    "RuleCategory",
    "RuleConfidence",
    "ExtractedRule",
    "RulePattern",
    # BR-M-2: Rule Dependency Detector
    "RuleDependencyDetector",
    "DependencyType",
    "ConflictSeverity",
    "RuleDependency",
    "RuleConflict",
    "RuleGraph",
    # FR-M-1: Traceability Matrix Generator
    "TraceabilityMatrixGenerator",
    "TraceabilityMatrix",
    "ArtifactType",
    "LinkType",
    "CoverageStatus",
    "TraceableArtifact",
    "TraceLink",
    "CoverageReport",
    # NFR-M-1: NFR Architecture Mapper
    "NFRArchitectureMapper",
    "NFRMappingCategory",
    "ArchitecturalPattern",
    "ImplementationStatus",
    "NFRequirement",
    "ArchitecturalComponent",
    "NFRMapping",
    "NFR_PATTERN_MAPPING",
    "PATTERN_CODE_INDICATORS",
]
