"""
Orchestration Services Package - Week 107-116

Agent Orchestration patterns based on Gregor Riegler's Pattern Language:
Source: https://gregorriegler.com/2025/07/12/augmented-coding-pattern-language.html

Week 107 - Quick Wins:
- HATEOAG Navigation Framework (AO-QW-1)
- Cross-Context Memory Service (AO-QW-2)
- State Indicator Pattern (AO-QW-3)
- Hypothesize Pattern (AO-QW-4)

Week 108 - Medium Improvements:
- Taskchain Orchestrator (AO-M-1)
- StateMachine as Tool (AO-M-2)
- Process File Standard (AO-M-3)
- Refactor Guard (AO-M-4)
- Trial Run Validation (AO-M-5)

Week 109 - Large Improvements:
- Full HATEOAG Implementation (AO-L-1)
- Loop & Condition Engine (AO-L-2)

Week 110 - Anti-Pattern Quality Gates:
- Anti-Pattern detectors (AP-1 to AP-9)

Week 111 - Missing Patterns (Quick Wins):
- Check Alignment Service (MP-QW-1)
- Active Partner Service (MP-QW-2)
- Chunking Service (MP-L-1)

Week 115-116 - Missing Patterns (Gregor Riegler):
- Feedback Loop Autonomy (MP-QW-3)
- Happy to Delete Mindset (MP-QW-4)
- Canary in the Code Mine (MP-QW-5)
- Constrained Tests DSL (MP-QW-6)
- Context Markers (MP-QW-7)
- Stop & Recovery (MP-QW-8)
- Feedback Flip (MP-M-1)
- Habit Hooks (MP-M-2)
- Semantic Zoom (MP-M-3)
- Instruction Sandwich (MP-M-4)
- Playgrounds (MP-M-5)
- All Paths Prototyping (MP-L-2)
"""

# Week 107 - Quick Wins
from .hateoag_service import HATEOAGService, NavigationLink, ProcessNode
from .cross_context_memory_service import CrossContextMemoryService, MemoryScope
from .state_indicator_service import StateIndicatorService, ProcessState
from .hypothesize_service import HypothesizeService, Hypothesis

# Week 108 - Medium Improvements
from .taskchain_service import TaskchainService, TaskChain, ChainTask
from .statemachine_tool_service import StateMachineToolService, StateMachine, StateTransition
from .process_file_service import ProcessFileService, ProcessDefinition, ProcessStep
from .refactor_guard_service import RefactorGuardService, ChangeScope, ChangeCheckResult
from .trial_run_service import TrialRunService, TrialRun, TrialRunResult

# Week 109 - Large Improvements
from .hateoag_orchestrator import HATEOAGOrchestrator, OrchestratorSession, StepResult
from .loop_condition_engine import LoopConditionEngine, ControlConstruct, ExecutionResult

# Week 110 - Anti-Pattern Quality Gates
from .antipattern_detector import AntiPatternDetector, AntiPatternType, AnalysisResult

# Week 111 - Missing Patterns (Quick Wins)
from .check_alignment_service import (
    CheckAlignmentService,
    AlignmentLevel,
    DriftType,
    AlignmentCheck,
    AlignmentSession,
    DriftReport,
)
from .active_partner_service import (
    ActivePartnerService,
    DecisionType,
    CollaborationMode,
    HandoffReason,
    DecisionPoint,
    CollaborationSession,
    CollaborationReport,
)
from .chunking_service import (
    ChunkingService,
    ChunkStrategy,
    ChunkStatus,
    ChunkType,
    Chunk,
    ChunkSession,
    ChunkingConfig,
    ReassemblyResult,
)

# Week 115-116 - Missing Patterns (Gregor Riegler)
from .feedback_loop_service import (
    FeedbackLoopService,
    FeedbackLoop,
    SuccessCriterion,
    CriterionType,
    LoopStatus,
    LoopProgress,
)
from .happy_delete_service import (
    HappyDeleteService,
    IterationTracker,
    ProductivityLevel,
    RestartType,
    RestartRecommendation,
)
from .canary_service import (
    CanaryService,
    CanarySignal,
    SignalType,
    RefactoringCandidate,
    RefactoringType,
    CodeHealthReport,
)
from .constrained_tests_service import (
    ConstrainedTestsService,
    TestSpecification,
    TestRule,
    RuleType,
    ValidationResult,
    GeneratedTest,
    CoverageReport,
)
from .context_markers_service import (
    ContextMarkersService,
    ContextMarker,
    MarkerType,
    ContextState,
    MarkerChange,
)
from .stop_recovery_service import (
    StopRecoveryService,
    StopEvent,
    StopReason,
    RecoveryType,
    RecoveryOption,
    RecoveryResult,
)

# Week 116 - Medium Improvements (Gregor Riegler)
from .feedback_flip_service import (
    FeedbackFlipService,
    FlipMode,
    FlipSession,
    Evaluation,
    Finding,
    FindingSeverity,
    FindingCategory,
    EvaluationSummary,
)
from .habit_hooks_service import (
    HabitHooksService,
    HabitHook,
    HookTrigger,
    HookAction,
    HookCondition,
    HookExecution,
    HookStatus,
    ActionType,
)
from .semantic_zoom_service import (
    SemanticZoomService,
    ZoomLevel,
    ZoomView,
    ZoomChild,
    ZoomSession,
    ContentType,
)
from .instruction_sandwich_service import (
    InstructionSandwichService,
    InstructionSet,
    Instruction,
    Reminder,
    SandwichContext,
    RepetitionStrategy,
    InstructionPriority,
    ReminderPosition,
)
from .playgrounds_service import (
    PlaygroundsService,
    Playground,
    PlaygroundStatus,
    IsolationType,
    DiffReport,
    MergeResult,
    ExperimentResult,
    ExecutionResult as PlaygroundExecutionResult,
)

# Week 116 - Large Improvements (Gregor Riegler)
from .all_paths_service import (
    AllPathsService,
    PrototypingSession,
    Variation,
    VariationStatus,
    SessionStatus,
    ComparisonReport,
    Learning,
    EvaluationCriterion as AllPathsCriterion,
    EvaluatorType,
    TestResults,
)

# Week 116 - Phase 5: Business Rule Workflow Integration
from .business_rule_workflow_integration import (
    BusinessRuleWorkflowIntegration,
    RuleExtractionContext,
    WorkflowIntegrationResult,
    get_rule_context_for_agent,
    is_rule_integrated_workflow,
    RULE_INTEGRATED_WORKFLOWS,
)

__all__ = [
    # Week 107 - HATEOAG
    "HATEOAGService",
    "NavigationLink",
    "ProcessNode",
    # Week 107 - Cross-Context Memory
    "CrossContextMemoryService",
    "MemoryScope",
    # Week 107 - State Indicator
    "StateIndicatorService",
    "ProcessState",
    # Week 107 - Hypothesize
    "HypothesizeService",
    "Hypothesis",
    # Week 108 - Taskchain
    "TaskchainService",
    "TaskChain",
    "ChainTask",
    # Week 108 - StateMachine
    "StateMachineToolService",
    "StateMachine",
    "StateTransition",
    # Week 108 - Process File
    "ProcessFileService",
    "ProcessDefinition",
    "ProcessStep",
    # Week 108 - Refactor Guard
    "RefactorGuardService",
    "ChangeScope",
    "ChangeCheckResult",
    # Week 108 - Trial Run
    "TrialRunService",
    "TrialRun",
    "TrialRunResult",
    # Week 109 - HATEOAG Orchestrator
    "HATEOAGOrchestrator",
    "OrchestratorSession",
    "StepResult",
    # Week 109 - Loop & Condition
    "LoopConditionEngine",
    "ControlConstruct",
    "ExecutionResult",
    # Week 110 - Anti-Pattern Detector
    "AntiPatternDetector",
    "AntiPatternType",
    "AnalysisResult",
    # Week 111 - Check Alignment
    "CheckAlignmentService",
    "AlignmentLevel",
    "DriftType",
    "AlignmentCheck",
    "AlignmentSession",
    "DriftReport",
    # Week 111 - Active Partner
    "ActivePartnerService",
    "DecisionType",
    "CollaborationMode",
    "HandoffReason",
    "DecisionPoint",
    "CollaborationSession",
    "CollaborationReport",
    # Week 111 - Chunking
    "ChunkingService",
    "ChunkStrategy",
    "ChunkStatus",
    "ChunkType",
    "Chunk",
    "ChunkSession",
    "ChunkingConfig",
    "ReassemblyResult",
    # Week 115 - Feedback Loop Autonomy
    "FeedbackLoopService",
    "FeedbackLoop",
    "SuccessCriterion",
    "CriterionType",
    "LoopStatus",
    "LoopProgress",
    # Week 115 - Happy to Delete
    "HappyDeleteService",
    "IterationTracker",
    "ProductivityLevel",
    "RestartType",
    "RestartRecommendation",
    # Week 115 - Canary in the Code Mine
    "CanaryService",
    "CanarySignal",
    "SignalType",
    "RefactoringCandidate",
    "RefactoringType",
    "CodeHealthReport",
    # Week 115 - Constrained Tests DSL
    "ConstrainedTestsService",
    "TestSpecification",
    "TestRule",
    "RuleType",
    "ValidationResult",
    "GeneratedTest",
    "CoverageReport",
    # Week 115 - Context Markers
    "ContextMarkersService",
    "ContextMarker",
    "MarkerType",
    "ContextState",
    "MarkerChange",
    # Week 115 - Stop & Recovery
    "StopRecoveryService",
    "StopEvent",
    "StopReason",
    "RecoveryType",
    "RecoveryOption",
    "RecoveryResult",
    # Week 116 - Feedback Flip
    "FeedbackFlipService",
    "FlipMode",
    "FlipSession",
    "Evaluation",
    "Finding",
    "FindingSeverity",
    "FindingCategory",
    "EvaluationSummary",
    # Week 116 - Habit Hooks
    "HabitHooksService",
    "HabitHook",
    "HookTrigger",
    "HookAction",
    "HookCondition",
    "HookExecution",
    "HookStatus",
    "ActionType",
    # Week 116 - Semantic Zoom
    "SemanticZoomService",
    "ZoomLevel",
    "ZoomView",
    "ZoomChild",
    "ZoomSession",
    "ContentType",
    # Week 116 - Instruction Sandwich
    "InstructionSandwichService",
    "InstructionSet",
    "Instruction",
    "Reminder",
    "SandwichContext",
    "RepetitionStrategy",
    "InstructionPriority",
    "ReminderPosition",
    # Week 116 - Playgrounds
    "PlaygroundsService",
    "Playground",
    "PlaygroundStatus",
    "IsolationType",
    "DiffReport",
    "MergeResult",
    "ExperimentResult",
    "PlaygroundExecutionResult",
    # Week 116 - All Paths Prototyping
    "AllPathsService",
    "PrototypingSession",
    "Variation",
    "VariationStatus",
    "SessionStatus",
    "ComparisonReport",
    "Learning",
    "AllPathsCriterion",
    "EvaluatorType",
    "TestResults",
    # Week 116 - Phase 5: Business Rule Workflow Integration
    "BusinessRuleWorkflowIntegration",
    "RuleExtractionContext",
    "WorkflowIntegrationResult",
    "get_rule_context_for_agent",
    "is_rule_integrated_workflow",
    "RULE_INTEGRATED_WORKFLOWS",
]
