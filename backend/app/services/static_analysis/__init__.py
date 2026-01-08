# Static Analysis Package - Fase 15: Hybrid Static-LLM Extraction Pipeline
# Week 97-98: Static Analysis Foundation

from .program_slicer import (
    ProgramSlicer,
    SliceDirection,
    LanguageSupport,
    SliceCriterion,
    ProgramSlice,
    DependencyGraph,
    DependencyNode,
    DependencyEdge,
)
from .variable_classifier import (
    VariableClassifier,
    VariableType,
    ClassifiedVariable,
    VariableClassificationResult,
)
from .business_rule_extractor import (
    BusinessRuleExtractor,
    RuleType,
    BusinessRule,
    RuleExtractionResult,
)
from .nfr_detector import (
    NFRDetector,
    NFRCategory,
    NFRDetection,
    NFRReport,
)
from .compliance_checker import (
    ComplianceChecker,
    ComplianceFramework,
    ComplianceRequirement,
    ComplianceViolation,
    ComplianceReport,
    ComplianceRuleSet,
    NEN7510RuleSet,
    ISO27001RuleSet,
    HIPAARuleSet,
    SOC2RuleSet,
    GDPRRuleSet,
    PCIDSSRuleSet,
)
from .orchestrator import (
    StaticAnalysisOrchestrator,
    StaticAnalysisConfig,
    StaticAnalysisResult,
)

# Week 101: Business Rules Quick Wins
from .domain_vocabulary import (
    DomainVocabularyLoader,
    DomainVocabulary,
    DomainTerm,
    BusinessDomain,
    healthcare_vocabulary,
    finance_vocabulary,
    ecommerce_vocabulary,
)
from .rule_deduplication import (
    RuleDeduplicationService,
    DuplicateType,
    DuplicateMatch,
    DeduplicationResult,
    deduplicate_rules,
    find_rule_duplicates,
)
from .nl_quality_enhancer import (
    NLQualityEnhancer,
    RuleType as NLRuleType,
    EnhancedRule,
    RuleTemplate,
    enhance_rule,
    detect_rule_type,
)
from .rule_completeness_checker import (
    RuleCompletenessChecker,
    BusinessArea,
    CoverageMetric,
    CoverageGap,
    CompletenessReport,
    check_rule_completeness,
    get_coverage_gaps,
)

__all__ = [
    # Program Slicer
    "ProgramSlicer",
    "SliceDirection",
    "LanguageSupport",
    "SliceCriterion",
    "ProgramSlice",
    "DependencyGraph",
    "DependencyNode",
    "DependencyEdge",
    # Variable Classifier
    "VariableClassifier",
    "VariableType",
    "ClassifiedVariable",
    "VariableClassificationResult",
    # Business Rule Extractor
    "BusinessRuleExtractor",
    "RuleType",
    "BusinessRule",
    "RuleExtractionResult",
    # NFR Detector
    "NFRDetector",
    "NFRCategory",
    "NFRDetection",
    "NFRReport",
    # Compliance Checker
    "ComplianceChecker",
    "ComplianceFramework",
    "ComplianceRequirement",
    "ComplianceViolation",
    "ComplianceReport",
    "ComplianceRuleSet",
    "NEN7510RuleSet",
    "ISO27001RuleSet",
    "HIPAARuleSet",
    "SOC2RuleSet",
    "GDPRRuleSet",
    "PCIDSSRuleSet",
    # Orchestrator
    "StaticAnalysisOrchestrator",
    "StaticAnalysisConfig",
    "StaticAnalysisResult",
    # Week 101: Domain Vocabulary
    "DomainVocabularyLoader",
    "DomainVocabulary",
    "DomainTerm",
    "BusinessDomain",
    "healthcare_vocabulary",
    "finance_vocabulary",
    "ecommerce_vocabulary",
    # Week 101: Rule Deduplication
    "RuleDeduplicationService",
    "DuplicateType",
    "DuplicateMatch",
    "DeduplicationResult",
    "deduplicate_rules",
    "find_rule_duplicates",
    # Week 101: NL Quality Enhancer
    "NLQualityEnhancer",
    "NLRuleType",
    "EnhancedRule",
    "RuleTemplate",
    "enhance_rule",
    "detect_rule_type",
    # Week 101: Rule Completeness Checker
    "RuleCompletenessChecker",
    "BusinessArea",
    "CoverageMetric",
    "CoverageGap",
    "CompletenessReport",
    "check_rule_completeness",
    "get_coverage_gaps",
]
