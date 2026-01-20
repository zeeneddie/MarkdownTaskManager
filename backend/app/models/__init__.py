# Models package

from app.models.user import User
from app.models.item import Item
from app.models.sprint import Sprint
from app.models.project import Project
from app.models.task_hierarchy import Epic, Feature, Story, Task
from app.models.green_paper import GreenPaperSession, Answer, Constitution, Specification
from app.models.estimation_history import EstimationProject, FunctionPointEstimate, StoryPointEstimate, MLModelVersion
from app.models.technical_debt import TechnicalDebtItem, TechnicalDebtSnapshot, RemediationPlan, DebtResolution, QualityGateResult
from app.models.attribution import TaskOutcome, Attribution, AttributionFeedback, QualityGateStats
from app.models.task_generation import TrainingTask, TrainingTaskResult, SkillGap, TrainingSession
from app.models.quality_gate_config import (
    QualityGateConfig,
    QualityCategoryConfig,
    QualityCheckConfig,
    QualityWorkflowRules,
    QualityConfigHistory,
    Severity,
    ChangeType,
    EntityType
)
from app.models.ab_testing import Experiment, ExperimentVariant, ExperimentResult
from app.models.observability import LLMProvider, AgentAction, DecisionTrace, AgentPerformanceDaily
from app.models.cctrace import ThinkingBlock, ToolExecution, MessageRelationship, SessionExport, BudgetConfig
from app.models.council_human_review import (
    CouncilHumanSession,
    CouncilProviderResponse,
    CouncilPeerReview,
    CouncilConsensus,
    DocumentVersion,
    SessionStatus,
    DocumentType
)
from app.models.application import Application, Component, StackAgent
from app.models.customer import Customer, ProjectApplication
from app.models.marqed_session import (
    MarQedSession,
    MarQedAnswer,
    MarQedSessionEvent,
    MarQedSessionStatus,
    MarQedWorkflowType,
    MarQedEventType,
)
from app.models.bug import Bug, BugComment, BugSeverity, BugStatus
from app.models.kanban_retry import KanbanRetryLog, KanbanAgentAction, RetryResult
from app.models.project_agent_config import (
    ProjectAgentConfig,
    ProjectLaneConfig,
    TechStack,
    STACK_TEMPLATES
)
from app.models.codewiki import (
    CodeWikiAnalysis,
    CodeWikiAnalysisStatus,
    CodeWikiModule,
    CodeWikiDiagram,
    DiagramType,
    CodeWikiAgentContext
)
from app.models.rl_training import (
    RLEnvironment,
    RLTrainingRun,
    RLEpisode,
    RLPolicy,
    RLReward,
    RLAgentPerformance,
    RLStepTransition
)
from app.models.migration_analysis import (
    MigrationAnalysis,
    MigrationModule,
    MigrationDBSchema,
    LegacyPattern,
    DBCompatibilityIssue,
    MigrationRecommendation,
    FPBreakdown,
    RiskAssessment
)
from app.models.project_assessment import (
    ProjectAssessment,
    MigrationPlan,
    AssessmentPhase
)
from app.models.mcp_proxy import (
    MCPServer,
    MCPToolRegistry,
    MCPToolExecution,
    MCPTokenSavings
)
from app.models.code_graph import (
    CodeGraphEntity,
    CodeGraphRelation,
    CodeGraphSnapshot,
    CodeGraphImpactCache,
    CodeGraphModuleCoupling
)
from app.models.claude_mem import (
    ClaudeMemSession,
    ClaudeMemObservation,
    ClaudeMemSummary,
    ClaudeMemSearchIndex,
    ClaudeMemContextWindow
)
from app.models.layered_analysis import (
    LayeredAnalysisSession,
    VBScriptAnalysis,
    StoredProcedureAnalysis,
    SWOTAnalysis,
    ImprovementItem,
    AnalysisReport
)
from app.models.browser_automation import (
    PlaywriterSession,
    PlaywriterExecution,
    PlaywriterTab,
    BigAGIValidation,
    BigAGIResponse,
    BigAGIConsensus,
    BrowserType,
    SessionStatus as PlaywriterSessionStatus,
    ExecutionStatus,
    ValidationStatus,
    ConsensusMethod,
    ConsensusRecommendation
)
from app.models.ccpm import (
    GitWorktree,
    GitHubIssueSync,
    PRDDecomposition,
    TaskRecommendation,
    WorktreeStatus,
    MergeStatus,
    SyncDirection,
    SyncStatus,
    DecompositionStatus,
    RecommendationStatus
)
from app.models.ghostcrew import (
    GhostCrewScan,
    SecurityFinding,
    ShadowPattern,
    VulnerabilityLearning,
    ComplianceCheck,
    SecurityKnowledge
)
from app.models.deep_extraction import (
    ExtractionSession,
    ExtractionRun,
    ExtractionLLMResult,
    ExtractionEnrichment,
    ExtractionConsensus,
    ExtractionConflict,
    ExtractionTier,
    ExtractionStatus,
    RunStatus,
    ConsensusStatus,
    ConflictType,
    ConflictStatus,
    ItemType,
    AnalysisType,
    TIER_CONFIG
)
from app.models.code_analysis import (
    CodeAnalysisAggregation,
    PotpieKnowledgeGraphEntry
)
from app.models.hierarchical_extraction import (
    HierarchicalExtractionSession,
    ExtractedStoryItem,
    ExtractionHierarchyRelation,
    ExtractionLevelMetrics,
    ExtractionLevel,
    StoryItemType,
    StoryConfidenceLevel,
    ExtractionSessionStatus
)
from app.models.graph_workflow import (
    PortalFeatureRequest,
    GraphAnalysisCache,
    WorkflowGraphIntegration,
    ANALYSIS_TYPES,
    WORKFLOW_GRAPH_INTEGRATIONS,
    FEATURE_REQUEST_STATUSES,
    WORK_TYPES
)
from app.models.portal_voting import (
    PortalFeatureVote,
    PortalFeatureComment,
    PortalFeatureVoteAggregate
)
from app.models.portal_roadmap import (
    PortalAnalysisQueue,
    PortalRelease,
    PortalRoadmapItem,
    PortalPublicRoadmap,
    ANALYSIS_STATUSES,
    RELEASE_STATUSES,
    ROADMAP_ITEM_STATUSES
)
from app.models.design_os import (
    DesignTokens,
    ApplicationShell,
    SampleDataSet,
    UISpecification,
    ScreenWireframe,
    ImplementationPrompt,
    DesignTokenPreset,
    DesignTier,
    ShellType,
    SpecStatus,
    PromptType,
    PresetCategory,
)
from app.models.static_analysis import (
    StaticAnalysisResult,
    BusinessRule,
    NFRDetection,
    ComplianceViolation,
    VariableClassification,
    ProgramSlice,
    StaticAnalysisConflict,
)
from app.models.devops_analysis import (
    RepositoryAnalysis,
    HotSpot,
    ContributorAnalysis,
    PRPattern,
    CIPipelineAnalysis,
    IssueCorrelation,
    RepositoryInsight,
    RepositoryPlatform,
    AnalysisDepth,
)
from app.models.traceability import (
    StoryBusinessRule,
    FeatureBusinessRule,
    EpicBusinessRule,
    RuleWorkflow,
    RuleWorkflowMember,
    LinkType,
    WorkflowType,
    CRUDOperation,
    TraceabilityMatrixRow,
    RuleImpact,
    TraceabilitySummary,
)
from app.models.hybrid_extraction import (
    HybridExtractionSession,
    HybridExtractedRule,
    HybridWorkflowCorrelation,
    HybridEntityMapping,
    ExtractionStatus as HybridExtractionStatus,
    ExtractionTier as HybridExtractionTier,
    RuleType,
    ExtractionMethod,
    WorkflowType as HybridWorkflowType,
    EntityType as HybridEntityType,
)
from app.models.rmtoo import (
    RmtooRequirement,
    RmtooTopic,
    RmtooSyncSession,
    RmtooExport,
    RmtooTraceabilityLink,
    RequirementType,
    RequirementStatus,
    RequirementCategory,
    SourceType,
    SyncDirection as RmtooSyncDirection,
    SyncStatus as RmtooSyncStatus,
    ExportType,
    LinkType as RmtooLinkType,
)
from app.models.portal_enhancements import (
    BoostAllowance,
    PriorityBoost,
    FeatureDuplicate,
    FeatureImpactPreview,
    CustomerTier,
    BoostStatus,
    DuplicateStatus,
    ImpactLevel,
    RiskLevel,
)
from app.models.engagement import (
    # Feedback Loop
    FeatureFeedback,
    FeedbackRequest,
    FeedbackType,
    FeedbackStatus,
    Sentiment,
    FeedbackRequestStatus,
    # Gamification
    BadgeDefinition,
    UserBadge,
    UserLevel,
    UserPointsHistory,
    BadgeCategory,
    BadgeTier,
    CriteriaType,
    ActionType,
    # Personalized Dashboard
    DashboardPreferences,
    FeatureRecommendation,
    RecommendationType,
    RecommendationStatus,
    # Constants
    LEVEL_DEFINITIONS,
    POINT_VALUES,
    DEFAULT_BADGES,
)
from app.models.chatbot_journey import (
    ChatSession,
    ChatMessage,
    JourneyEvent,
    JourneyFunnel,
    JourneyFunnelSnapshot,
    ChatSessionStatus,
    ChatRole,
    ChatContentType,
    ChatIntent,
    ChatAgent,
    ChatActionType,
    EventCategory,
    DeviceType,
    INTENT_PATTERNS,
    EVENT_TYPES,
    AGENT_TEMPLATES,
)
from app.models.causality import (
    CausalSession,
    CausalClassification,
    CausalRelation,
    CausalDependencyGraph,
    CausalTestCase,
    CausalSessionStatus,
    CausalSourceType,
    CausalRelationType,
    ExtractionMethod as CausalExtractionMethod,
    TestCaseType,
    TestCaseStatus,
    TestExecutionResult,
    TestPriority,
    GraphType,
    GraphFormat,
    CAUSAL_MARKERS,
    detect_causal_markers,
    classify_relation_type,
)
from app.models.research import (
    # SQLAlchemy Models
    BackgroundJobModel,
    LoadEstimationModel,
    DocumentationRuleModel,
    # Enums
    JobType,
    TriggerType,
    DetectionMethod,
    ResourceIntensity,
    SessionMode,
    CapacityBottleneck,
    RuleType as DocumentationRuleType,
    # Dataclasses
    BackgroundJob,
    BackgroundJobDetectionResult,
    ConnectionPoolConfig,
    SessionStateConfig,
    QueryComplexityMetrics,
    LoadEstimationResult,
    DocumentationRule,
    DocumentationExtractionResult,
)
from app.models.dead_code import (
    # SQLAlchemy Models
    DeadCodeAnalysisModel,
    DeadCodeItemModel,
    RuntimeAnalysisModel,
    CodeCoverageAnalysisModel,
    # Enums
    DeadCodeItemType,
    DetectionMethod as DeadCodeDetectionMethod,
    RemovalRisk,
    SuggestedAction,
    AnalysisType as DeadCodeAnalysisType,
    APMProvider,
    CoverageSource,
    # Dataclasses
    DeadCodeItem,
    DeadCodeAnalysisResult,
    RuntimeAnalysisResult,
    FileCoverage,
    CodeCoverageResult,
    # Constants
    LANGUAGE_EXTENSIONS,
    TOOL_CONFIDENCE,
)
from app.models.testing import (
    # SQLAlchemy Models
    CharacterizationTestModel,
    CharacterizationTestRunModel,
    VisualRegressionTestModel,
    VisualRegressionRunModel,
    DualRunComparisonModel,
    DualRunRequestModel,
    TestingExcellenceSummaryModel,
    # Enums
    TestStatus as TestingTestStatus,
    TestType as TestingTestType,
    ConfidenceLevel as TestingConfidenceLevel,
    OutputFormat as TestingOutputFormat,
    DiffType,
    ScreenshotTool,
    # Dataclasses
    TestInput,
    CharacterizationTestResult,
    ComparisonResult,
    FieldDifference,
    DualRunResult,
    DiffRegion,
    VisualRegressionResult,
    TestingExcellenceSummary,
)
from app.models.data_architecture import (
    # SQLAlchemy Models
    DataLineageSession,
    DataLineageFieldMapping,
    ERDDiagramModel,
    CDCSessionModel,
    JourneyRecordingModel,
    JourneyComparisonModel,
    JourneyOverrideRuleModel,
    # Enums
    LineageNodeType,
    LineageEdgeType,
    ERDOutputFormat,
    JourneyStepType,
    JourneyMatchStatus,
    CDCMode,
    CDCEventType,
    TransformationType,
    # Dataclasses
    LineageNode,
    LineageEdge,
    LineageGraph,
    ImpactAnalysisResult,
    FieldMapping,
    ERDColumn,
    ERDRelationship,
    ERDTable,
    ERDDiagram,
    JourneyStep,
    JourneyStepComparison,
    JourneyComparisonResult,
    JourneyRecording,
    JourneyOverrideRule,
    CDCTableConfig,
    CDCEvent,
    CDCSyncStats,
    CDCSession,
)
from app.models.decision_table import (
    # Enums
    HitPolicy,
    ConditionOperator,
    DecisionTableOutputFormat,
    # Dataclasses
    InputColumn,
    OutputColumn,
    ConditionEntry,
    ActionEntry,
    DecisionRule,
    DecisionTable,
    DecisionTableStatistics,
    DecisionTableExtractionResult,
)
from app.models.authorization_matrix import (
    # Enums
    PermissionType,
    RoleLevel,
    ResourceType,
    ConflictType as AuthConflictType,
    AuthorizationMatrixOutputFormat,
    # Dataclasses
    ExtractedRole,
    ExtractedPermission,
    ExtractedResource,
    RolePermissionMapping,
    AuthorizationConflict,
    AuthorizationMatrix,
    AuthorizationMatrixStatistics,
    AuthorizationExtractionResult,
)
from app.models.project_intake import (
    # SQLAlchemy Models
    ProjectIntake,
    ProjectIntakeSource,
    ProjectIntakeIntegration,
    ProjectIntakeScope,
    ProjectIntakeFeature,
    ProjectIntakeEvent,
    # Enum Constants
    TrajectType,
    MigrationType,
    IntegrationAction,
    IntakeStatus,
    AnalysisTier,
    ExpectedOutcome,
    MigrationStrategy,
    BrownPaperDecision,
    IntakeEventType,
    # Predefined data
    PREDEFINED_FEATURES,
)
from app.models.stability import (
    StabilityScan,
    StabilityFinding,
    StabilityMetric,
    StabilityCategorySummary,
)

__all__ = [
    # User
    "User",
    # Items
    "Item",
    # Sprint
    "Sprint",
    # Project
    "Project",
    # Task Hierarchy
    "Epic", "Feature", "Story", "Task",
    # Green Paper
    "GreenPaperSession", "Answer", "Constitution", "Specification",
    # Estimation
    "EstimationProject", "FunctionPointEstimate", "StoryPointEstimate", "MLModelVersion",
    # Technical Debt
    "TechnicalDebtItem", "TechnicalDebtSnapshot", "RemediationPlan", "DebtResolution", "QualityGateResult",
    # Attribution
    "TaskOutcome", "Attribution", "AttributionFeedback", "QualityGateStats",
    # Task Generation
    "TrainingTask", "TrainingTaskResult", "SkillGap", "TrainingSession",
    # Quality Gate Config
    "QualityGateConfig", "QualityCategoryConfig", "QualityCheckConfig",
    "QualityWorkflowRules", "QualityConfigHistory",
    "Severity", "ChangeType", "EntityType",
    # A/B Testing
    "Experiment", "ExperimentVariant", "ExperimentResult",
    # Observability
    "LLMProvider", "AgentAction", "DecisionTrace", "AgentPerformanceDaily",
    # CCTrace (Week 61)
    "ThinkingBlock", "ToolExecution", "MessageRelationship", "SessionExport", "BudgetConfig",
    # Council Human Review (Week 55)
    "CouncilHumanSession", "CouncilProviderResponse", "CouncilPeerReview",
    "CouncilConsensus", "DocumentVersion", "SessionStatus", "DocumentType",
    # Application Registry (Week 57)
    "Application", "Component", "StackAgent",
    # Customer Hierarchy (Week 143 - Fase 28)
    "Customer", "ProjectApplication",
    # Bug Tracking (Week 58)
    "Bug", "BugComment", "BugSeverity", "BugStatus",
    # Kanban Retry Tracking (Week 58)
    "KanbanRetryLog", "KanbanAgentAction", "RetryResult",
    # Project Agent Config (Week 58)
    "ProjectAgentConfig", "ProjectLaneConfig", "TechStack", "STACK_TEMPLATES",
    # CodeWiki (Week 62)
    "CodeWikiAnalysis", "CodeWikiAnalysisStatus", "CodeWikiModule",
    "CodeWikiDiagram", "DiagramType", "CodeWikiAgentContext",
    # RL Training (Week 64)
    "RLEnvironment", "RLTrainingRun", "RLEpisode", "RLPolicy",
    "RLReward", "RLAgentPerformance", "RLStepTransition",
    # MigrationAnalyzer (Week 65)
    "MigrationAnalysis", "MigrationModule", "MigrationDBSchema",
    "LegacyPattern", "DBCompatibilityIssue", "MigrationRecommendation",
    "FPBreakdown", "RiskAssessment",
    # Project Assessment (Week 69)
    "ProjectAssessment", "MigrationPlan", "AssessmentPhase",
    # MCP Proxy (Week 71)
    "MCPServer", "MCPToolRegistry", "MCPToolExecution", "MCPTokenSavings",
    # Code Graph (Week 75)
    "CodeGraphEntity", "CodeGraphRelation", "CodeGraphSnapshot",
    "CodeGraphImpactCache", "CodeGraphModuleCoupling",
    # Claude-Mem (Week 76)
    "ClaudeMemSession", "ClaudeMemObservation", "ClaudeMemSummary",
    "ClaudeMemSearchIndex", "ClaudeMemContextWindow",
    # Layered Analysis (Week 77)
    "LayeredAnalysisSession", "VBScriptAnalysis", "StoredProcedureAnalysis",
    "SWOTAnalysis", "ImprovementItem", "AnalysisReport",
    # Browser Automation (Week 78)
    "PlaywriterSession", "PlaywriterExecution", "PlaywriterTab",
    "BigAGIValidation", "BigAGIResponse", "BigAGIConsensus",
    "BrowserType", "PlaywriterSessionStatus", "ExecutionStatus",
    "ValidationStatus", "ConsensusMethod", "ConsensusRecommendation",
    # CCPM (Week 79)
    "GitWorktree", "GitHubIssueSync", "PRDDecomposition", "TaskRecommendation",
    "WorktreeStatus", "MergeStatus", "SyncDirection", "SyncStatus",
    "DecompositionStatus", "RecommendationStatus",
    # GhostCrew Security (Week 80-82)
    "GhostCrewScan", "SecurityFinding", "ShadowPattern", "VulnerabilityLearning",
    "ComplianceCheck", "SecurityKnowledge",
    # Deep Extraction Pipeline (Week 81-87)
    "ExtractionSession", "ExtractionRun", "ExtractionLLMResult",
    "ExtractionEnrichment", "ExtractionConsensus", "ExtractionConflict",
    "ExtractionTier", "ExtractionStatus", "RunStatus", "ConsensusStatus",
    "ConflictType", "ConflictStatus", "ItemType", "AnalysisType", "TIER_CONFIG",
    # Code Analysis Aggregation (Week 83)
    "CodeAnalysisAggregation", "PotpieKnowledgeGraphEntry",
    # Hierarchical Story Extraction (Week 84)
    "HierarchicalExtractionSession", "ExtractedStoryItem",
    "ExtractionHierarchyRelation", "ExtractionLevelMetrics",
    "ExtractionLevel", "StoryItemType", "StoryConfidenceLevel", "ExtractionSessionStatus",
    # Graph Workflow Integration (Week 88)
    "PortalFeatureRequest", "GraphAnalysisCache", "WorkflowGraphIntegration",
    "ANALYSIS_TYPES", "WORKFLOW_GRAPH_INTEGRATIONS", "FEATURE_REQUEST_STATUSES", "WORK_TYPES",
    # Portal Voting & Comments (Week 90)
    "PortalFeatureVote", "PortalFeatureComment", "PortalFeatureVoteAggregate",
    # Portal Roadmap (Week 90)
    "PortalAnalysisQueue", "PortalRelease", "PortalRoadmapItem", "PortalPublicRoadmap",
    "ANALYSIS_STATUSES", "RELEASE_STATUSES", "ROADMAP_ITEM_STATUSES",
    # Design OS (Week 94-95)
    "DesignTokens", "ApplicationShell", "SampleDataSet", "UISpecification",
    "ScreenWireframe", "ImplementationPrompt", "DesignTokenPreset",
    "DesignTier", "ShellType", "SpecStatus", "PromptType", "PresetCategory",
    # Static Analysis (Week 97-98 - Fase 15)
    "StaticAnalysisResult", "BusinessRule", "NFRDetection",
    "ComplianceViolation", "VariableClassification", "ProgramSlice",
    "StaticAnalysisConflict",
    # Traceability (Week 113 - Phase 4.5)
    "StoryBusinessRule", "FeatureBusinessRule", "EpicBusinessRule",
    "RuleWorkflow", "RuleWorkflowMember",
    "LinkType", "WorkflowType", "CRUDOperation",
    "TraceabilityMatrixRow", "RuleImpact", "TraceabilitySummary",
    # Hybrid Business Rule Extraction (Week 111-114 - Phase 5)
    "HybridExtractionSession", "HybridExtractedRule",
    "HybridWorkflowCorrelation", "HybridEntityMapping",
    "HybridExtractionStatus", "HybridExtractionTier",
    "RuleType", "ExtractionMethod",
    "HybridWorkflowType", "HybridEntityType",
    # rmtoo Requirements Management (Week 117)
    "RmtooRequirement", "RmtooTopic", "RmtooSyncSession",
    "RmtooExport", "RmtooTraceabilityLink",
    "RequirementType", "RequirementStatus", "RequirementCategory",
    "SourceType", "RmtooSyncDirection", "RmtooSyncStatus",
    "ExportType", "RmtooLinkType",
    # Client Portal 2.0 Phase 3: Engagement (Week 119-120)
    "FeatureFeedback", "FeedbackRequest",
    "FeedbackType", "FeedbackStatus", "Sentiment", "FeedbackRequestStatus",
    "BadgeDefinition", "UserBadge", "UserLevel", "UserPointsHistory",
    "BadgeCategory", "BadgeTier", "CriteriaType", "ActionType",
    "DashboardPreferences", "FeatureRecommendation",
    "RecommendationType", "RecommendationStatus",
    "LEVEL_DEFINITIONS", "POINT_VALUES", "DEFAULT_BADGES",
    # Client Portal 2.0 Phase 4: Chatbot & Journey (Week 121)
    "ChatSession", "ChatMessage", "JourneyEvent", "JourneyFunnel", "JourneyFunnelSnapshot",
    "ChatSessionStatus", "ChatRole", "ChatContentType", "ChatIntent", "ChatAgent",
    "ChatActionType", "EventCategory", "DeviceType",
    "INTENT_PATTERNS", "EVENT_TYPES", "AGENT_TEMPLATES",
    # CiRA Causality Detection (Week 123-125)
    "CausalSession", "CausalClassification", "CausalRelation",
    "CausalDependencyGraph", "CausalTestCase",
    "CausalSessionStatus", "CausalSourceType", "CausalRelationType",
    "CausalExtractionMethod", "TestCaseType", "TestCaseStatus",
    "TestExecutionResult", "TestPriority", "GraphType", "GraphFormat",
    "CAUSAL_MARKERS", "detect_causal_markers", "classify_relation_type",
    # Week 131 Research Services (Background Jobs, Load Estimation, Documentation Rules)
    "BackgroundJobModel", "LoadEstimationModel", "DocumentationRuleModel",
    "JobType", "TriggerType", "DetectionMethod", "ResourceIntensity",
    "SessionMode", "CapacityBottleneck", "DocumentationRuleType",
    "BackgroundJob", "BackgroundJobDetectionResult",
    "ConnectionPoolConfig", "SessionStateConfig", "QueryComplexityMetrics",
    "LoadEstimationResult", "DocumentationRule", "DocumentationExtractionResult",
    # Week 132-133 Dead Code & Runtime Analysis (Fase 22)
    "DeadCodeAnalysisModel", "DeadCodeItemModel", "RuntimeAnalysisModel", "CodeCoverageAnalysisModel",
    "DeadCodeItemType", "DeadCodeDetectionMethod", "RemovalRisk", "SuggestedAction",
    "DeadCodeAnalysisType", "APMProvider", "CoverageSource",
    "DeadCodeItem", "DeadCodeAnalysisResult", "RuntimeAnalysisResult",
    "FileCoverage", "CodeCoverageResult",
    "LANGUAGE_EXTENSIONS", "TOOL_CONFIDENCE",
    # Week 134 Testing Excellence (Fase 23)
    "CharacterizationTestModel", "CharacterizationTestRunModel",
    "VisualRegressionTestModel", "VisualRegressionRunModel",
    "DualRunComparisonModel", "DualRunRequestModel", "TestingExcellenceSummaryModel",
    "TestingTestStatus", "TestingTestType", "TestingConfidenceLevel", "TestingOutputFormat",
    "DiffType", "ScreenshotTool",
    "TestInput", "CharacterizationTestResult", "ComparisonResult", "FieldDifference",
    "DualRunResult", "DiffRegion", "VisualRegressionResult", "TestingExcellenceSummary",
    # Data Architecture (Fase 24)
    "DataLineageSession", "DataLineageFieldMapping",
    "ERDDiagramModel", "CDCSessionModel",
    "JourneyRecordingModel", "JourneyComparisonModel", "JourneyOverrideRuleModel",
    "LineageNodeType", "LineageEdgeType", "ERDOutputFormat",
    "JourneyStepType", "JourneyMatchStatus", "CDCMode", "CDCEventType", "TransformationType",
    "LineageNode", "LineageEdge", "LineageGraph", "ImpactAnalysisResult", "FieldMapping",
    "ERDColumn", "ERDRelationship", "ERDTable", "ERDDiagram",
    "JourneyStep", "JourneyStepComparison", "JourneyComparisonResult",
    "JourneyRecording", "JourneyOverrideRule",
    "CDCTableConfig", "CDCEvent", "CDCSyncStats", "CDCSession",
    # Decision Table Extraction (Fase 25)
    "HitPolicy", "ConditionOperator", "DecisionTableOutputFormat",
    "InputColumn", "OutputColumn", "ConditionEntry", "ActionEntry",
    "DecisionRule", "DecisionTable", "DecisionTableStatistics", "DecisionTableExtractionResult",
    # Authorization Matrix Extraction (Fase 25)
    "PermissionType", "RoleLevel", "ResourceType", "AuthConflictType", "AuthorizationMatrixOutputFormat",
    "ExtractedRole", "ExtractedPermission", "ExtractedResource",
    "RolePermissionMapping", "AuthorizationConflict",
    "AuthorizationMatrix", "AuthorizationMatrixStatistics", "AuthorizationExtractionResult",
    # Project Intake Wizard (Week 145)
    "ProjectIntake", "ProjectIntakeSource", "ProjectIntakeIntegration",
    "ProjectIntakeScope", "ProjectIntakeFeature", "ProjectIntakeEvent",
    "TrajectType", "MigrationType", "IntegrationAction", "IntakeStatus",
    "AnalysisTier", "ExpectedOutcome", "MigrationStrategy", "BrownPaperDecision",
    "IntakeEventType", "PREDEFINED_FEATURES",
    # Stability Analysis (Fase 21 - Week 143-146)
    "StabilityScan", "StabilityFinding", "StabilityMetric", "StabilityCategorySummary",
]
