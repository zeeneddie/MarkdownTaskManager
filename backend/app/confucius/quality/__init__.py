"""
Confucius Quality Gate System.

Evaluates agent output against domain-specific quality rules:
- Completeness: All required fields present
- Accuracy: Correct and error-free output
- Relevance: Appropriate for the task
- Actionability: Provides actionable insights
- Consistency: Consistent with context
- Clarity: Clear and understandable
- Coverage: Comprehensive coverage of scope

Components:
- QualityGateEvaluator: Evaluates output against rules
- IterationController: Manages PIV loop with quality gates
- EscalationService: Handles failed quality gates
- Quality Rules: Domain-specific scoring rules
"""

from .rules import (
    # Enums
    QualityDimension,
    Severity,
    # Data classes
    RuleViolation,
    RuleResult,
    DomainRuleSet,
    # Base class
    QualityRule,
    # Generic rules
    CompletenessRule,
    NonEmptyOutputRule,
    SuccessStatusRule,
    NoErrorsRule,
    # Architecture rules
    ArchitectureDecisionRule,
    ComponentMappingRule,
    # Quality rules
    CriticalIssuesRule,
    QualityScoreThresholdRule,
    # Estimation rules
    EstimationConfidenceRule,
    WorkTypeValidRule,
    # Domain functions
    get_rules_for_domain,
    get_general_rules,
    get_architecture_rules,
    get_quality_rules,
    get_estimation_rules,
    get_documentation_rules,
    get_testing_rules,
    # Registry
    DOMAIN_RULE_SETS,
)

from .evaluator import (
    GateDecision,
    DimensionScore,
    EvaluationResult,
    QualityGateEvaluator,
    create_evaluator,
)

from .iteration import (
    IterationStatus,
    ImprovementStrategy,
    IterationAttempt,
    IterationContext,
    IterationController,
    create_iteration_controller,
)

from .escalation import (
    EscalationType,
    EscalationPriority,
    EscalationTicket,
    EscalationDecision,
    EscalationService,
    create_escalation_service,
)

from .streaming import (
    StreamEventType,
    StreamEvent,
    QualityProgressStream,
    QualityProgressContext,
    get_global_stream,
    reset_global_stream,
)


__all__ = [
    # Rules - Enums
    "QualityDimension",
    "Severity",
    # Rules - Data classes
    "RuleViolation",
    "RuleResult",
    "DomainRuleSet",
    # Rules - Base class
    "QualityRule",
    # Rules - Generic
    "CompletenessRule",
    "NonEmptyOutputRule",
    "SuccessStatusRule",
    "NoErrorsRule",
    # Rules - Architecture
    "ArchitectureDecisionRule",
    "ComponentMappingRule",
    # Rules - Quality
    "CriticalIssuesRule",
    "QualityScoreThresholdRule",
    # Rules - Estimation
    "EstimationConfidenceRule",
    "WorkTypeValidRule",
    # Rules - Functions
    "get_rules_for_domain",
    "get_general_rules",
    "get_architecture_rules",
    "get_quality_rules",
    "get_estimation_rules",
    "get_documentation_rules",
    "get_testing_rules",
    "DOMAIN_RULE_SETS",
    # Evaluator
    "GateDecision",
    "DimensionScore",
    "EvaluationResult",
    "QualityGateEvaluator",
    "create_evaluator",
    # Iteration
    "IterationStatus",
    "ImprovementStrategy",
    "IterationAttempt",
    "IterationContext",
    "IterationController",
    "create_iteration_controller",
    # Escalation
    "EscalationType",
    "EscalationPriority",
    "EscalationTicket",
    "EscalationDecision",
    "EscalationService",
    "create_escalation_service",
    # Streaming
    "StreamEventType",
    "StreamEvent",
    "QualityProgressStream",
    "QualityProgressContext",
    "get_global_stream",
    "reset_global_stream",
]
