"""
Orchestration API - Week 111 Integration Sprint

API endpoints for Agent Orchestration services (Week 107-111):
- HATEOAG Navigation
- Cross-Context Memory
- State Indicators
- Hypothesize Pattern
- Taskchain Orchestration
- StateMachine as Tool
- Process File Management
- Refactor Guard
- Trial Run Validation
- Loop & Condition Engine
- Anti-Pattern Detection
- Check Alignment (Week 111)
- Active Partner (Week 111)
- Chunking (Week 111)
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID
import logging

# Import orchestration services
from app.services.orchestration import (
    # Week 107 - Quick Wins
    HATEOAGService, NavigationLink, ProcessNode,
    CrossContextMemoryService, MemoryScope,
    StateIndicatorService, ProcessState,
    HypothesizeService, Hypothesis,
    # Week 108 - Medium
    TaskchainService, TaskChain, ChainTask,
    StateMachineToolService, StateMachine, StateTransition,
    ProcessFileService, ProcessDefinition, ProcessStep,
    RefactorGuardService, ChangeScope, ChangeCheckResult,
    TrialRunService, TrialRun, TrialRunResult,
    # Week 109 - Large
    HATEOAGOrchestrator, OrchestratorSession, StepResult,
    LoopConditionEngine, ControlConstruct, ExecutionResult,
    # Week 110 - Anti-Patterns
    AntiPatternDetector, AntiPatternType, AnalysisResult,
    # Week 111 - Missing Patterns
    CheckAlignmentService, AlignmentLevel, DriftType, AlignmentCheck, DriftReport,
    ActivePartnerService, DecisionType, CollaborationMode, HandoffReason, DecisionPoint, CollaborationReport,
    ChunkingService, ChunkStrategy, ChunkStatus, Chunk, ChunkSession, ChunkingConfig,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/orchestration", tags=["orchestration"])

# =============================================================================
# Pydantic Models
# =============================================================================

class MemoryScopeEnum(str, Enum):
    SESSION = "session"
    TASK = "task"
    PROJECT = "project"
    GLOBAL = "global"


class MemoryEntry(BaseModel):
    key: str
    value: Any
    scope: MemoryScopeEnum = MemoryScopeEnum.SESSION
    project_id: Optional[str] = None


class HypothesisRequest(BaseModel):
    action: str = Field(..., description="The action to be performed")
    context: Dict[str, Any] = Field(default_factory=dict)
    expected_outcomes: List[str] = Field(default_factory=list)


class HypothesisResponse(BaseModel):
    hypothesis_id: str
    action: str
    expected_outcomes: List[str]
    verification_steps: List[str]
    recovery_action: str
    created_at: datetime


class TaskchainRequest(BaseModel):
    name: str
    description: str
    tasks: List[Dict[str, Any]]
    project_id: Optional[str] = None


class StateMachineRequest(BaseModel):
    name: str
    states: List[str]
    initial_state: str
    transitions: List[Dict[str, Any]]


class TransitionRequest(BaseModel):
    machine_id: str
    event: str
    context: Dict[str, Any] = Field(default_factory=dict)


class ProcessFileRequest(BaseModel):
    content: str = Field(..., description="Markdown process file content")


class RefactorGuardRequest(BaseModel):
    original_code: str
    modified_code: str
    allowed_scope: Dict[str, Any] = Field(default_factory=dict)


class TrialRunRequest(BaseModel):
    actions: List[Dict[str, Any]]
    dry_run: bool = True


class LoopRequest(BaseModel):
    construct_type: str  # for_each, while, until, if_else
    condition: str
    body: List[Dict[str, Any]]
    context: Dict[str, Any] = Field(default_factory=dict)


class AntiPatternRequest(BaseModel):
    content: str
    content_type: str = "code"  # code, requirements, design, documentation
    patterns_to_check: Optional[List[str]] = None


class SessionRequest(BaseModel):
    process_id: str
    project_id: Optional[str] = None
    initial_context: Dict[str, Any] = Field(default_factory=dict)


class StepExecutionRequest(BaseModel):
    session_id: str
    step_id: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Service Instances (Singleton pattern)
# =============================================================================

_hateoag_service: Optional[HATEOAGService] = None
_memory_service: Optional[CrossContextMemoryService] = None
_state_service: Optional[StateIndicatorService] = None
_hypothesize_service: Optional[HypothesizeService] = None
_taskchain_service: Optional[TaskchainService] = None
_statemachine_service: Optional[StateMachineToolService] = None
_process_service: Optional[ProcessFileService] = None
_refactor_guard: Optional[RefactorGuardService] = None
_trial_run_service: Optional[TrialRunService] = None
_orchestrator: Optional[HATEOAGOrchestrator] = None
_loop_engine: Optional[LoopConditionEngine] = None
_antipattern_detector: Optional[AntiPatternDetector] = None


def get_hateoag_service() -> HATEOAGService:
    global _hateoag_service
    if _hateoag_service is None:
        _hateoag_service = HATEOAGService()
    return _hateoag_service


def get_memory_service() -> CrossContextMemoryService:
    global _memory_service
    if _memory_service is None:
        _memory_service = CrossContextMemoryService()
    return _memory_service


def get_state_service() -> StateIndicatorService:
    global _state_service
    if _state_service is None:
        _state_service = StateIndicatorService()
    return _state_service


def get_hypothesize_service() -> HypothesizeService:
    global _hypothesize_service
    if _hypothesize_service is None:
        _hypothesize_service = HypothesizeService()
    return _hypothesize_service


def get_taskchain_service() -> TaskchainService:
    global _taskchain_service
    if _taskchain_service is None:
        _taskchain_service = TaskchainService()
    return _taskchain_service


def get_statemachine_service() -> StateMachineToolService:
    global _statemachine_service
    if _statemachine_service is None:
        _statemachine_service = StateMachineToolService()
    return _statemachine_service


def get_process_service() -> ProcessFileService:
    global _process_service
    if _process_service is None:
        _process_service = ProcessFileService()
    return _process_service


def get_refactor_guard() -> RefactorGuardService:
    global _refactor_guard
    if _refactor_guard is None:
        _refactor_guard = RefactorGuardService()
    return _refactor_guard


def get_trial_run_service() -> TrialRunService:
    global _trial_run_service
    if _trial_run_service is None:
        _trial_run_service = TrialRunService()
    return _trial_run_service


def get_orchestrator() -> HATEOAGOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = HATEOAGOrchestrator()
    return _orchestrator


def get_loop_engine() -> LoopConditionEngine:
    global _loop_engine
    if _loop_engine is None:
        _loop_engine = LoopConditionEngine()
    return _loop_engine


def get_antipattern_detector() -> AntiPatternDetector:
    global _antipattern_detector
    if _antipattern_detector is None:
        _antipattern_detector = AntiPatternDetector()
    return _antipattern_detector


# =============================================================================
# HATEOAG Navigation Endpoints
# =============================================================================

@router.get("/hateoag/processes")
async def list_processes(
    service: HATEOAGService = Depends(get_hateoag_service)
):
    """List all available HATEOAG processes."""
    processes = service.list_processes()
    return {"processes": processes, "count": len(processes)}


@router.get("/hateoag/processes/{process_id}")
async def get_process(
    process_id: str,
    service: HATEOAGService = Depends(get_hateoag_service)
):
    """Get a specific process definition."""
    process = service.get_process(process_id)
    if not process:
        raise HTTPException(status_code=404, detail=f"Process {process_id} not found")
    return process


@router.get("/hateoag/processes/{process_id}/navigation")
async def get_navigation_links(
    process_id: str,
    current_step: Optional[str] = None,
    service: HATEOAGService = Depends(get_hateoag_service)
):
    """Get navigation links for a process step."""
    links = service.get_navigation_links(process_id, current_step)
    return {"links": links, "current_step": current_step}


# =============================================================================
# Cross-Context Memory Endpoints
# =============================================================================

@router.post("/memory")
async def save_memory(
    entry: MemoryEntry,
    service: CrossContextMemoryService = Depends(get_memory_service)
):
    """Save a value to cross-context memory."""
    scope = MemoryScope[entry.scope.upper()]
    service.save_state(entry.key, entry.value, scope, entry.project_id)
    return {"status": "saved", "key": entry.key, "scope": entry.scope}


@router.get("/memory/{key}")
async def get_memory(
    key: str,
    scope: MemoryScopeEnum = Query(MemoryScopeEnum.SESSION),
    project_id: Optional[str] = None,
    service: CrossContextMemoryService = Depends(get_memory_service)
):
    """Retrieve a value from cross-context memory."""
    memory_scope = MemoryScope[scope.upper()]
    value = service.load_state(key, memory_scope, project_id)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Key {key} not found in {scope} scope")
    return {"key": key, "value": value, "scope": scope}


@router.get("/memory")
async def list_memory(
    scope: MemoryScopeEnum = Query(MemoryScopeEnum.SESSION),
    project_id: Optional[str] = None,
    service: CrossContextMemoryService = Depends(get_memory_service)
):
    """List all keys in a memory scope."""
    memory_scope = MemoryScope[scope.upper()]
    keys = service.list_keys(memory_scope, project_id)
    return {"scope": scope, "keys": keys, "count": len(keys)}


@router.delete("/memory/{key}")
async def delete_memory(
    key: str,
    scope: MemoryScopeEnum = Query(MemoryScopeEnum.SESSION),
    project_id: Optional[str] = None,
    service: CrossContextMemoryService = Depends(get_memory_service)
):
    """Delete a value from cross-context memory."""
    memory_scope = MemoryScope[scope.upper()]
    service.delete_state(key, memory_scope, project_id)
    return {"status": "deleted", "key": key, "scope": scope}


# =============================================================================
# State Indicator Endpoints
# =============================================================================

@router.get("/state/{process_id}")
async def get_state(
    process_id: str,
    service: StateIndicatorService = Depends(get_state_service)
):
    """Get current state indicators for a process."""
    state = service.get_state(process_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"No state found for process {process_id}")
    return state


@router.post("/state/{process_id}/transition")
async def transition_state(
    process_id: str,
    new_state: str,
    service: StateIndicatorService = Depends(get_state_service)
):
    """Transition process to a new state."""
    result = service.transition(process_id, new_state)
    return result


@router.get("/state/{process_id}/progress")
async def get_progress(
    process_id: str,
    service: StateIndicatorService = Depends(get_state_service)
):
    """Get progress visualization for a process."""
    progress = service.get_progress_visualization(process_id)
    return progress


# =============================================================================
# Hypothesize Pattern Endpoints
# =============================================================================

@router.post("/hypothesize")
async def create_hypothesis(
    request: HypothesisRequest,
    service: HypothesizeService = Depends(get_hypothesize_service)
):
    """Create a hypothesis before performing an action."""
    hypothesis = service.create_hypothesis(
        action=request.action,
        context=request.context,
        expected_outcomes=request.expected_outcomes
    )
    return {
        "hypothesis_id": hypothesis.id,
        "action": hypothesis.action,
        "expected_outcomes": hypothesis.expected_outcomes,
        "verification_steps": hypothesis.verification_steps,
        "recovery_action": hypothesis.recovery_action,
        "created_at": hypothesis.created_at.isoformat()
    }


@router.post("/hypothesize/{hypothesis_id}/verify")
async def verify_hypothesis(
    hypothesis_id: str,
    actual_outcomes: List[str],
    service: HypothesizeService = Depends(get_hypothesize_service)
):
    """Verify a hypothesis against actual outcomes."""
    result = service.verify_hypothesis(hypothesis_id, actual_outcomes)
    return result


@router.get("/hypothesize/{hypothesis_id}")
async def get_hypothesis(
    hypothesis_id: str,
    service: HypothesizeService = Depends(get_hypothesize_service)
):
    """Get a hypothesis by ID."""
    hypothesis = service.get_hypothesis(hypothesis_id)
    if not hypothesis:
        raise HTTPException(status_code=404, detail=f"Hypothesis {hypothesis_id} not found")
    return hypothesis


# =============================================================================
# Taskchain Orchestration Endpoints
# =============================================================================

@router.post("/taskchain")
async def create_taskchain(
    request: TaskchainRequest,
    service: TaskchainService = Depends(get_taskchain_service)
):
    """Create a new task chain."""
    chain = service.create_chain(
        name=request.name,
        description=request.description,
        tasks=request.tasks,
        project_id=request.project_id
    )
    return {"chain_id": chain.id, "name": chain.name, "task_count": len(chain.tasks)}


@router.get("/taskchain/{chain_id}")
async def get_taskchain(
    chain_id: str,
    service: TaskchainService = Depends(get_taskchain_service)
):
    """Get a task chain by ID."""
    chain = service.get_chain(chain_id)
    if not chain:
        raise HTTPException(status_code=404, detail=f"Chain {chain_id} not found")
    return chain


@router.post("/taskchain/{chain_id}/execute")
async def execute_taskchain(
    chain_id: str,
    initial_input: Dict[str, Any] = None,
    service: TaskchainService = Depends(get_taskchain_service)
):
    """Execute a task chain."""
    result = await service.execute_chain(chain_id, initial_input or {})
    return result


@router.get("/taskchain/{chain_id}/status")
async def get_taskchain_status(
    chain_id: str,
    service: TaskchainService = Depends(get_taskchain_service)
):
    """Get execution status of a task chain."""
    status = service.get_chain_status(chain_id)
    return status


# =============================================================================
# StateMachine as Tool Endpoints
# =============================================================================

@router.post("/statemachine")
async def create_statemachine(
    request: StateMachineRequest,
    service: StateMachineToolService = Depends(get_statemachine_service)
):
    """Create a new state machine."""
    machine = service.create_machine(
        name=request.name,
        states=request.states,
        initial_state=request.initial_state,
        transitions=request.transitions
    )
    return {"machine_id": machine.id, "name": machine.name, "current_state": machine.current_state}


@router.get("/statemachine/{machine_id}")
async def get_statemachine(
    machine_id: str,
    service: StateMachineToolService = Depends(get_statemachine_service)
):
    """Get a state machine by ID."""
    machine = service.get_machine(machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
    return machine


@router.post("/statemachine/transition")
async def execute_transition(
    request: TransitionRequest,
    service: StateMachineToolService = Depends(get_statemachine_service)
):
    """Execute a state transition."""
    result = service.transition(request.machine_id, request.event, request.context)
    return result


@router.get("/statemachine/{machine_id}/mcp-tools")
async def get_mcp_tools(
    machine_id: str,
    service: StateMachineToolService = Depends(get_statemachine_service)
):
    """Get MCP tool definitions for a state machine."""
    tools = service.get_mcp_tools(machine_id)
    return {"machine_id": machine_id, "tools": tools}


@router.get("/statemachine/templates")
async def list_statemachine_templates(
    service: StateMachineToolService = Depends(get_statemachine_service)
):
    """List available state machine templates."""
    templates = service.list_templates()
    return {"templates": templates}


@router.post("/statemachine/from-template/{template_name}")
async def create_from_template(
    template_name: str,
    service: StateMachineToolService = Depends(get_statemachine_service)
):
    """Create a state machine from a predefined template."""
    machine = service.create_from_template(template_name)
    if not machine:
        raise HTTPException(status_code=404, detail=f"Template {template_name} not found")
    return {"machine_id": machine.id, "name": machine.name, "template": template_name}


# =============================================================================
# Process File Endpoints
# =============================================================================

@router.post("/process/parse")
async def parse_process_file(
    request: ProcessFileRequest,
    service: ProcessFileService = Depends(get_process_service)
):
    """Parse a markdown process file."""
    definition = service.parse(request.content)
    return definition


@router.post("/process/validate")
async def validate_process_file(
    request: ProcessFileRequest,
    service: ProcessFileService = Depends(get_process_service)
):
    """Validate a process file definition."""
    result = service.validate(request.content)
    return result


@router.get("/process/templates")
async def list_process_templates(
    service: ProcessFileService = Depends(get_process_service)
):
    """List available process file templates."""
    templates = service.list_templates()
    return {"templates": templates}


@router.get("/process/templates/{template_name}")
async def get_process_template(
    template_name: str,
    service: ProcessFileService = Depends(get_process_service)
):
    """Get a specific process file template."""
    template = service.get_template(template_name)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_name} not found")
    return {"name": template_name, "content": template}


# =============================================================================
# Refactor Guard Endpoints
# =============================================================================

@router.post("/refactor-guard/check")
async def check_refactor(
    request: RefactorGuardRequest,
    service: RefactorGuardService = Depends(get_refactor_guard)
):
    """Check if code changes are within allowed scope."""
    result = service.check_changes(
        original=request.original_code,
        modified=request.modified_code,
        allowed_scope=request.allowed_scope
    )
    return result


@router.post("/refactor-guard/scope")
async def create_scope(
    scope: Dict[str, Any],
    service: RefactorGuardService = Depends(get_refactor_guard)
):
    """Create a new change scope definition."""
    scope_id = service.create_scope(scope)
    return {"scope_id": scope_id, "status": "created"}


@router.get("/refactor-guard/patterns")
async def list_scope_patterns(
    service: RefactorGuardService = Depends(get_refactor_guard)
):
    """List available scope creep and refactoring patterns."""
    patterns = service.list_patterns()
    return patterns


# =============================================================================
# Trial Run Endpoints
# =============================================================================

@router.post("/trial-run")
async def create_trial_run(
    request: TrialRunRequest,
    service: TrialRunService = Depends(get_trial_run_service)
):
    """Create and optionally execute a trial run."""
    trial = service.create_trial(request.actions)
    if request.dry_run:
        result = await service.execute_dry_run(trial.id)
    else:
        result = await service.execute(trial.id)
    return result


@router.get("/trial-run/{trial_id}")
async def get_trial_run(
    trial_id: str,
    service: TrialRunService = Depends(get_trial_run_service)
):
    """Get a trial run by ID."""
    trial = service.get_trial(trial_id)
    if not trial:
        raise HTTPException(status_code=404, detail=f"Trial {trial_id} not found")
    return trial


@router.post("/trial-run/{trial_id}/compare")
async def compare_trial_runs(
    trial_id: str,
    other_trial_id: str,
    service: TrialRunService = Depends(get_trial_run_service)
):
    """Compare results of two trial runs."""
    comparison = service.compare_trials(trial_id, other_trial_id)
    return comparison


# =============================================================================
# HATEOAG Orchestrator Endpoints (Full Integration)
# =============================================================================

@router.post("/sessions")
async def create_session(
    request: SessionRequest,
    orchestrator: HATEOAGOrchestrator = Depends(get_orchestrator)
):
    """Create a new orchestrator session."""
    session = orchestrator.create_session(
        process_id=request.process_id,
        project_id=request.project_id,
        initial_context=request.initial_context
    )
    return {
        "session_id": session.id,
        "process_id": session.process_id,
        "status": session.status,
        "current_step": session.current_step
    }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    orchestrator: HATEOAGOrchestrator = Depends(get_orchestrator)
):
    """Get session details."""
    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return session


@router.post("/sessions/{session_id}/step")
async def execute_step(
    session_id: str,
    request: StepExecutionRequest,
    orchestrator: HATEOAGOrchestrator = Depends(get_orchestrator)
):
    """Execute the next step in a session."""
    result = await orchestrator.execute_step(
        session_id=session_id,
        step_id=request.step_id,
        input_data=request.input_data
    )
    return result


@router.get("/sessions/{session_id}/navigation")
async def get_session_navigation(
    session_id: str,
    orchestrator: HATEOAGOrchestrator = Depends(get_orchestrator)
):
    """Get available navigation options for current session state."""
    navigation = orchestrator.get_navigation(session_id)
    return navigation


@router.post("/sessions/{session_id}/checkpoint")
async def create_checkpoint(
    session_id: str,
    orchestrator: HATEOAGOrchestrator = Depends(get_orchestrator)
):
    """Create a checkpoint for the current session state."""
    checkpoint = orchestrator.create_checkpoint(session_id)
    return checkpoint


@router.post("/sessions/{session_id}/restore/{checkpoint_id}")
async def restore_checkpoint(
    session_id: str,
    checkpoint_id: str,
    orchestrator: HATEOAGOrchestrator = Depends(get_orchestrator)
):
    """Restore a session to a previous checkpoint."""
    result = orchestrator.restore_checkpoint(session_id, checkpoint_id)
    return result


# =============================================================================
# Loop & Condition Engine Endpoints
# =============================================================================

@router.post("/loop/execute")
async def execute_loop(
    request: LoopRequest,
    engine: LoopConditionEngine = Depends(get_loop_engine)
):
    """Execute a loop or conditional construct."""
    result = await engine.execute(
        construct_type=request.construct_type,
        condition=request.condition,
        body=request.body,
        context=request.context
    )
    return result


@router.post("/loop/evaluate-condition")
async def evaluate_condition(
    condition: str,
    context: Dict[str, Any],
    engine: LoopConditionEngine = Depends(get_loop_engine)
):
    """Evaluate a condition expression."""
    result = engine.evaluate_condition(condition, context)
    return {"condition": condition, "result": result}


@router.get("/loop/constructs")
async def list_constructs(
    engine: LoopConditionEngine = Depends(get_loop_engine)
):
    """List available control constructs."""
    constructs = engine.list_constructs()
    return {"constructs": constructs}


# =============================================================================
# Anti-Pattern Detection Endpoints
# =============================================================================

@router.post("/antipattern/analyze")
async def analyze_antipatterns(
    request: AntiPatternRequest,
    detector: AntiPatternDetector = Depends(get_antipattern_detector)
):
    """Analyze content for anti-patterns."""
    result = detector.analyze(
        content=request.content,
        content_type=request.content_type,
        patterns=request.patterns_to_check
    )
    return result


@router.get("/antipattern/types")
async def list_antipattern_types(
    detector: AntiPatternDetector = Depends(get_antipattern_detector)
):
    """List all detectable anti-pattern types."""
    types = detector.list_pattern_types()
    return {"types": types}


@router.get("/antipattern/types/{pattern_type}")
async def get_antipattern_info(
    pattern_type: str,
    detector: AntiPatternDetector = Depends(get_antipattern_detector)
):
    """Get detailed information about a specific anti-pattern."""
    info = detector.get_pattern_info(pattern_type)
    if not info:
        raise HTTPException(status_code=404, detail=f"Pattern type {pattern_type} not found")
    return info


@router.post("/antipattern/report")
async def generate_antipattern_report(
    request: AntiPatternRequest,
    format: str = Query("markdown", enum=["markdown", "json", "html"]),
    detector: AntiPatternDetector = Depends(get_antipattern_detector)
):
    """Generate a detailed anti-pattern analysis report."""
    result = detector.analyze(
        content=request.content,
        content_type=request.content_type,
        patterns=request.patterns_to_check
    )
    report = detector.generate_report(result, format)
    return {"format": format, "report": report}


# =============================================================================
# Health & Statistics
# =============================================================================

@router.get("/health")
async def health_check():
    """Health check for orchestration services."""
    return {
        "status": "healthy",
        "services": {
            "hateoag": "available",
            "memory": "available",
            "state": "available",
            "hypothesize": "available",
            "taskchain": "available",
            "statemachine": "available",
            "process": "available",
            "refactor_guard": "available",
            "trial_run": "available",
            "orchestrator": "available",
            "loop_engine": "available",
            "antipattern": "available"
        },
        "version": "1.0.0",
        "week": "107-110"
    }


@router.get("/statistics")
async def get_statistics(
    orchestrator: HATEOAGOrchestrator = Depends(get_orchestrator),
    detector: AntiPatternDetector = Depends(get_antipattern_detector)
):
    """Get usage statistics for orchestration services."""
    return {
        "sessions": orchestrator.get_statistics(),
        "antipatterns_detected": detector.get_statistics(),
        "timestamp": datetime.now().isoformat()
    }


# =============================================================================
# Week 111 - Check Alignment Service
# =============================================================================

# Service singleton
_alignment_service: Optional[CheckAlignmentService] = None

def get_alignment_service() -> CheckAlignmentService:
    global _alignment_service
    if _alignment_service is None:
        _alignment_service = CheckAlignmentService()
    return _alignment_service


class AlignmentCheckRequest(BaseModel):
    goal: str = Field(..., description="The high-level objective")
    proposed_action: str = Field(..., description="What the agent intends to do")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    sub_goals: Optional[List[str]] = Field(default=None, description="Sub-goals for the task")


class AlignmentSessionRequest(BaseModel):
    goal: str = Field(..., description="The high-level objective for the session")
    sub_goals: Optional[List[str]] = Field(default=None, description="Sub-goals for the task")


class RecordActionRequest(BaseModel):
    action: str = Field(..., description="The action taken")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Action context")


@router.post("/alignment/check")
async def check_alignment(
    request: AlignmentCheckRequest,
    service: CheckAlignmentService = Depends(get_alignment_service)
):
    """Check if a proposed action aligns with the stated goal."""
    result = service.check_action_alignment(
        goal=request.goal,
        proposed_action=request.proposed_action,
        context=request.context,
        sub_goals=request.sub_goals,
    )
    return {
        "alignment_score": result.alignment_score,
        "level": result.level.value,
        "is_aligned": result.is_aligned,
        "reasoning": result.reasoning,
        "suggestions": result.suggestions,
        "drift_type": result.drift_type.value if result.drift_type else None,
    }


@router.post("/alignment/sessions")
async def create_alignment_session(
    request: AlignmentSessionRequest,
    service: CheckAlignmentService = Depends(get_alignment_service)
):
    """Create a new alignment tracking session."""
    session = service.create_session(
        goal=request.goal,
        sub_goals=request.sub_goals,
    )
    return {
        "session_id": str(session.id),
        "goal": session.goal,
        "sub_goals": session.sub_goals,
        "created_at": session.created_at.isoformat(),
    }


@router.post("/alignment/sessions/{session_id}/actions")
async def record_alignment_action(
    session_id: UUID,
    request: RecordActionRequest,
    service: CheckAlignmentService = Depends(get_alignment_service)
):
    """Record an action and check its alignment with session goal."""
    try:
        result = service.record_action(
            session_id=session_id,
            action=request.action,
            context=request.context,
        )
        return {
            "alignment_score": result.alignment_score,
            "level": result.level.value,
            "is_aligned": result.is_aligned,
            "suggestions": result.suggestions,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/alignment/sessions/{session_id}/drift")
async def analyze_alignment_drift(
    session_id: UUID,
    service: CheckAlignmentService = Depends(get_alignment_service)
):
    """Analyze a session for goal drift."""
    try:
        report = service.analyze_drift(session_id)
        return {
            "session_id": str(report.session_id),
            "total_actions": report.total_actions,
            "aligned_actions": report.aligned_actions,
            "misaligned_actions": report.misaligned_actions,
            "average_alignment": report.average_alignment,
            "drift_types": [dt.value for dt in report.drift_types],
            "drift_severity": report.drift_severity,
            "recommendations": report.recommendations,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Week 111 - Active Partner Service
# =============================================================================

_partner_service: Optional[ActivePartnerService] = None

def get_partner_service() -> ActivePartnerService:
    global _partner_service
    if _partner_service is None:
        _partner_service = ActivePartnerService()
    return _partner_service


class CollaborationSessionRequest(BaseModel):
    task: str = Field(..., description="The task being worked on")
    user_id: str = Field(..., description="ID of the human partner")
    initial_mode: Optional[str] = Field(default="active", description="Starting collaboration mode")


class DecisionRequest(BaseModel):
    question: str = Field(..., description="The question to answer")
    options: List[str] = Field(..., description="List of options")
    handoff_reason: Optional[str] = Field(default="decision_required", description="Why human input is needed")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    ai_recommendation: Optional[str] = Field(default=None, description="AI's recommended option")
    ai_reasoning: Optional[str] = Field(default=None, description="AI's reasoning")


class RecordDecisionRequest(BaseModel):
    selected_option: str = Field(..., description="The option selected by human")
    reasoning: Optional[str] = Field(default=None, description="Human's reasoning")


class FeedbackRequest(BaseModel):
    feedback_type: str = Field(..., description="Type of feedback")
    content: str = Field(..., description="The feedback content")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


@router.post("/partner/sessions")
async def create_collaboration_session(
    request: CollaborationSessionRequest,
    service: ActivePartnerService = Depends(get_partner_service)
):
    """Start a new collaboration session."""
    mode = CollaborationMode(request.initial_mode) if request.initial_mode else CollaborationMode.ACTIVE
    session = service.start_session(
        task=request.task,
        user_id=request.user_id,
        initial_mode=mode,
    )
    return {
        "session_id": str(session.id),
        "task": session.task,
        "mode": session.mode.value,
        "created_at": session.created_at.isoformat(),
    }


@router.post("/partner/sessions/{session_id}/decisions")
async def request_decision(
    session_id: UUID,
    request: DecisionRequest,
    service: ActivePartnerService = Depends(get_partner_service)
):
    """Request a decision from the human partner."""
    try:
        reason = HandoffReason(request.handoff_reason) if request.handoff_reason else HandoffReason.DECISION_REQUIRED
        decision = service.request_decision(
            session_id=session_id,
            question=request.question,
            options=request.options,
            handoff_reason=reason,
            context=request.context,
            ai_recommendation=request.ai_recommendation,
            ai_reasoning=request.ai_reasoning,
        )
        return {
            "decision_id": str(decision.id),
            "question": decision.question,
            "decision_type": decision.decision_type.value,
            "options": [{"label": o.label, "description": o.description} for o in decision.options],
            "ai_recommendation": decision.ai_recommendation,
            "status": decision.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/partner/decisions/{decision_id}")
async def record_decision(
    decision_id: UUID,
    request: RecordDecisionRequest,
    service: ActivePartnerService = Depends(get_partner_service)
):
    """Record a human decision."""
    try:
        decision = service.record_decision(
            decision_id=decision_id,
            selected_option=request.selected_option,
            reasoning=request.reasoning,
        )
        return {
            "decision_id": str(decision.id),
            "selected_option": decision.selected_option,
            "status": decision.status,
            "decided_at": decision.decided_at.isoformat() if decision.decided_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/partner/sessions/{session_id}/pending")
async def get_pending_decisions(
    session_id: UUID,
    service: ActivePartnerService = Depends(get_partner_service)
):
    """Get all pending decisions for a session."""
    decisions = service.get_pending_decisions(session_id)
    return {
        "pending_count": len(decisions),
        "decisions": [
            {
                "decision_id": str(d.id),
                "question": d.question,
                "options": [o.label for o in d.options],
                "ai_recommendation": d.ai_recommendation,
            }
            for d in decisions
        ]
    }


@router.get("/partner/sessions/{session_id}/report")
async def get_collaboration_report(
    session_id: UUID,
    service: ActivePartnerService = Depends(get_partner_service)
):
    """Generate a collaboration effectiveness report."""
    try:
        report = service.generate_report(session_id)
        return {
            "session_id": str(report.session_id),
            "task": report.task,
            "duration_minutes": report.duration_minutes,
            "total_decisions": report.total_decisions,
            "human_decisions": report.human_decisions,
            "ai_decisions": report.ai_decisions,
            "ai_recommendation_acceptance_rate": report.ai_recommendation_acceptance_rate,
            "override_rate": report.override_rate,
            "pending_decisions": report.pending_decisions,
            "collaboration_score": report.collaboration_score,
            "recommendations": report.recommendations,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Week 111 - Chunking Service
# =============================================================================

_chunking_service: Optional[ChunkingService] = None

def get_chunking_service() -> ChunkingService:
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService()
    return _chunking_service


class ChunkTextRequest(BaseModel):
    text: str = Field(..., description="The text to chunk")
    strategy: Optional[str] = Field(default="size_based", description="Chunking strategy")
    max_size: Optional[int] = Field(default=4000, description="Max tokens/chars per chunk")
    overlap: Optional[int] = Field(default=100, description="Overlap between chunks")
    source: Optional[str] = Field(default="text", description="Source identifier")


class ChunkFilesRequest(BaseModel):
    file_paths: List[str] = Field(..., description="List of file paths to chunk")
    strategy: Optional[str] = Field(default="semantic", description="Chunking strategy")
    max_size: Optional[int] = Field(default=4000, description="Max size per chunk")


class MarkChunkRequest(BaseModel):
    result: Optional[Any] = Field(default=None, description="Processing result")
    error: Optional[str] = Field(default=None, description="Error message if failed")


@router.post("/chunking/text")
async def chunk_text(
    request: ChunkTextRequest,
    service: ChunkingService = Depends(get_chunking_service)
):
    """Chunk text content."""
    strategy = ChunkStrategy(request.strategy) if request.strategy else ChunkStrategy.SIZE_BASED
    config = ChunkingConfig(
        max_size=request.max_size or 4000,
        overlap=request.overlap or 100,
    )
    session = service.chunk_text(
        text=request.text,
        strategy=strategy,
        config=config,
        source=request.source or "text",
    )
    return {
        "session_id": str(session.id),
        "total_chunks": session.total_chunks,
        "strategy": session.strategy.value,
        "chunks": [
            {
                "chunk_id": str(c.id),
                "index": c.index,
                "content_length": len(c.content),
                "content_preview": c.content[:100] + "..." if len(c.content) > 100 else c.content,
            }
            for c in session.chunks
        ]
    }


@router.get("/chunking/sessions/{session_id}")
async def get_chunk_session(
    session_id: UUID,
    service: ChunkingService = Depends(get_chunking_service)
):
    """Get a chunking session by ID."""
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": str(session.id),
        "source": session.source,
        "strategy": session.strategy.value,
        "total_chunks": session.total_chunks,
        "completed": session.completed_chunks,
        "failed": session.failed_chunks,
    }


@router.get("/chunking/sessions/{session_id}/progress")
async def get_chunking_progress(
    session_id: UUID,
    service: ChunkingService = Depends(get_chunking_service)
):
    """Get progress for a chunking session."""
    return service.get_progress(session_id)


@router.get("/chunking/sessions/{session_id}/next")
async def get_next_chunk(
    session_id: UUID,
    service: ChunkingService = Depends(get_chunking_service)
):
    """Get the next pending chunk to process."""
    chunk = service.get_next_chunk(session_id)
    if not chunk:
        return {"chunk": None, "message": "No pending chunks"}
    return {
        "chunk_id": str(chunk.id),
        "index": chunk.index,
        "content": chunk.content,
        "chunk_type": chunk.chunk_type.value,
        "metadata": chunk.metadata,
    }


@router.post("/chunking/chunks/{chunk_id}/complete")
async def mark_chunk_completed(
    chunk_id: UUID,
    request: MarkChunkRequest,
    service: ChunkingService = Depends(get_chunking_service)
):
    """Mark a chunk as completed or failed."""
    try:
        if request.error:
            service.mark_failed(chunk_id, request.error)
            return {"status": "failed", "error": request.error}
        else:
            service.mark_completed(chunk_id, request.result)
            return {"status": "completed"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/chunking/sessions/{session_id}/reassemble")
async def reassemble_chunks(
    session_id: UUID,
    service: ChunkingService = Depends(get_chunking_service)
):
    """Reassemble chunk results into final output."""
    try:
        result = service.reassemble(session_id)
        return {
            "session_id": str(result.session_id),
            "total_chunks": result.total_chunks,
            "successful_chunks": result.successful_chunks,
            "failed_chunks": result.failed_chunks,
            "result_type": type(result.combined_result).__name__,
            "metadata": result.metadata,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
