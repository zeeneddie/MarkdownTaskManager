"""
Full HATEOAG Orchestrator

Week 109 - AO-L-1: Complete HATEOAG implementation with all services integrated.

Based on Gregor Riegler's Augmented Coding Pattern Language:
- HATEOAG (Hypertext as Engine of Agent Guidance) - Meta-framework
- Integrates all orchestration services
- Full workflow execution with navigation
- State management and persistence
- Memory and hypothesis tracking
- Guard enforcement and validation

This is the unified orchestrator that brings together:
- HATEOAGService (navigation)
- CrossContextMemoryService (persistence)
- StateIndicatorService (progress)
- HypothesizeService (validation)
- TaskchainService (execution)
- StateMachineToolService (state transitions)
- ProcessFileService (process definitions)
- RefactorGuardService (scope protection)
- TrialRunService (dry runs)

Example usage:
    orchestrator = HATEOAGOrchestrator()

    # Load a process and execute with full orchestration
    session = await orchestrator.create_session(
        process_id="feature_workflow",
        context={"feature_name": "user-auth"},
        agent="Felix"
    )

    # Execute with hypothesis validation
    while orchestrator.has_next(session.id):
        # Get current step with navigation options
        step = orchestrator.get_current_step(session.id)
        print(f"Step: {step.title}")
        print(f"Available actions: {step.available_links}")

        # Execute with dry run first
        trial_result = await orchestrator.trial_step(session.id)
        if trial_result.can_proceed:
            result = await orchestrator.execute_step(session.id)

    # Get session report
    report = orchestrator.get_session_report(session.id)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, Awaitable, Set
from pathlib import Path
import json
import uuid
import asyncio

# Import all orchestration services
from .hateoag_service import HATEOAGService, NavigationLink, ProcessNode, NodeStatus
from .cross_context_memory_service import CrossContextMemoryService, MemoryScope
from .state_indicator_service import StateIndicatorService, ProcessState, StatePhase
from .hypothesize_service import HypothesizeService, Hypothesis, HypothesisStatus
from .taskchain_service import TaskchainService, TaskChain, ChainTask, TaskStatus
from .statemachine_tool_service import StateMachineToolService, StateMachine
from .process_file_service import ProcessFileService, ProcessDefinition, ProcessStep, NavigationType
from .refactor_guard_service import RefactorGuardService, ChangeScope
from .trial_run_service import TrialRunService, TrialRun, TrialRunResult


class SessionStatus(Enum):
    """Status of an orchestration session."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepExecutionMode(Enum):
    """Mode for step execution."""
    AUTOMATIC = "automatic"     # Execute without confirmation
    CONFIRM = "confirm"         # Require confirmation
    TRIAL_FIRST = "trial_first" # Dry run before actual
    MANUAL = "manual"           # Manual execution only


@dataclass
class StepResult:
    """Result of executing a step."""
    step_id: str
    success: bool
    output: Any
    error: Optional[str] = None
    duration_ms: float = 0
    hypothesis_verified: bool = True
    trial_run: Optional[TrialRunResult] = None
    next_steps: List[NavigationLink] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "success": self.success,
            "output": str(self.output)[:500] if self.output else None,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "hypothesis_verified": self.hypothesis_verified,
            "trial_run": self.trial_run.to_dict() if self.trial_run else None,
            "next_steps": [{"type": n.nav_type.value, "target": n.target, "label": n.label} for n in self.next_steps],
            "metadata": self.metadata
        }


@dataclass
class SessionCheckpoint:
    """Checkpoint for session recovery."""
    id: str
    session_id: str
    step_id: str
    timestamp: datetime
    state: Dict[str, Any]
    memory_snapshot: Dict[str, Any]
    can_resume: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "step_id": self.step_id,
            "timestamp": self.timestamp.isoformat(),
            "state": self.state,
            "memory_snapshot": self.memory_snapshot,
            "can_resume": self.can_resume
        }


@dataclass
class OrchestratorSession:
    """A HATEOAG orchestration session."""
    id: str
    process_id: str
    process: ProcessDefinition
    agent: str
    created_at: datetime
    updated_at: datetime
    status: SessionStatus
    current_step_id: str
    execution_mode: StepExecutionMode
    context: Dict[str, Any]
    step_results: List[StepResult]
    checkpoints: List[SessionCheckpoint]
    hypotheses: List[Hypothesis]
    state_machine_id: Optional[str] = None
    task_chain_id: Optional[str] = None
    scope_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "process_id": self.process_id,
            "agent": self.agent,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.value,
            "current_step_id": self.current_step_id,
            "execution_mode": self.execution_mode.value,
            "context": self.context,
            "step_results": [r.to_dict() for r in self.step_results],
            "checkpoints": [c.to_dict() for c in self.checkpoints],
            "hypotheses_count": len(self.hypotheses),
            "state_machine_id": self.state_machine_id,
            "task_chain_id": self.task_chain_id,
            "scope_id": self.scope_id,
            "metadata": self.metadata
        }


class HATEOAGOrchestrator:
    """
    Full HATEOAG Orchestrator.

    Integrates all orchestration services into a unified workflow engine.
    Provides:
    - Session management
    - Process execution with navigation
    - State and memory persistence
    - Hypothesis validation
    - Trial runs and guard enforcement
    - Checkpoint recovery
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(".agent_memory/orchestrator")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize all sub-services
        self.hateoag = HATEOAGService(self.storage_path / "hateoag")
        self.memory = CrossContextMemoryService(self.storage_path / "memory")
        self.state = StateIndicatorService(self.storage_path / "state")
        self.hypothesis = HypothesizeService(self.storage_path / "hypothesis")
        self.taskchain = TaskchainService(self.storage_path / "taskchain")
        self.statemachine = StateMachineToolService(self.storage_path / "statemachine")
        self.process = ProcessFileService(self.storage_path / "process")
        self.guard = RefactorGuardService(self.storage_path / "guard")
        self.trial = TrialRunService(self.storage_path / "trial")

        # Session storage
        self.sessions: Dict[str, OrchestratorSession] = {}
        self._load_sessions()

        # Step handlers
        self.step_handlers: Dict[str, Callable] = {}

    def _load_sessions(self) -> None:
        """Load sessions from storage."""
        sessions_file = self.storage_path / "sessions.json"
        if sessions_file.exists():
            try:
                data = json.loads(sessions_file.read_text())
                for session_data in data.get("sessions", []):
                    session = self._session_from_dict(session_data)
                    self.sessions[session.id] = session
            except Exception:
                pass

    def _save_sessions(self) -> None:
        """Save sessions to storage."""
        sessions_file = self.storage_path / "sessions.json"
        data = {
            "sessions": [s.to_dict() for s in self.sessions.values()]
        }
        sessions_file.write_text(json.dumps(data, indent=2, default=str))

    def _session_from_dict(self, data: Dict[str, Any]) -> OrchestratorSession:
        """Reconstruct session from dict."""
        process = self.process.get(data["process_id"])

        return OrchestratorSession(
            id=data["id"],
            process_id=data["process_id"],
            process=process,
            agent=data["agent"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            status=SessionStatus(data["status"]),
            current_step_id=data["current_step_id"],
            execution_mode=StepExecutionMode(data["execution_mode"]),
            context=data.get("context", {}),
            step_results=[],  # Results are transient
            checkpoints=[],   # Would need full reconstruction
            hypotheses=[],    # Would need full reconstruction
            state_machine_id=data.get("state_machine_id"),
            task_chain_id=data.get("task_chain_id"),
            scope_id=data.get("scope_id"),
            metadata=data.get("metadata", {})
        )

    def register_step_handler(self, step_type: str, handler: Callable) -> None:
        """Register a handler for a step type."""
        self.step_handlers[step_type] = handler

    async def create_session(
        self,
        process_id: str,
        agent: str,
        context: Optional[Dict[str, Any]] = None,
        execution_mode: str = "trial_first",
        create_scope: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> OrchestratorSession:
        """
        Create a new orchestration session.

        Args:
            process_id: Process to execute
            agent: Agent name
            context: Initial context
            execution_mode: Execution mode
            create_scope: Create refactor guard scope
            metadata: Additional metadata

        Returns:
            Created OrchestratorSession
        """
        process = self.process.get(process_id)
        if not process:
            raise ValueError(f"Process '{process_id}' not found")

        now = datetime.now()
        session_id = str(uuid.uuid4())

        # Create state machine for process
        sm = self.statemachine.create_machine(
            name=f"session_{session_id[:8]}",
            description=f"State machine for {process.metadata.name}",
            initial_state=process.entry_step,
            states=process.get_step_ids(),
            transitions=[
                {
                    "from": step.id,
                    "to": nav.target,
                    "trigger": nav.label.lower().replace(" ", "_"),
                    "description": nav.label
                }
                for step in process.steps
                for nav in step.navigation
                if nav.nav_type not in [NavigationType.END, NavigationType.CALL]
            ]
        )

        # Create task chain
        chain = self.taskchain.create_chain(
            name=f"session_{session_id[:8]}",
            context=context
        )

        # Create scope if requested
        scope_id = None
        if create_scope:
            scope = self.guard.create_scope(
                task_id=session_id,
                task_description=f"Orchestrator session for {process.metadata.name}",
                max_files_changed=50,
                max_lines_changed=5000
            )
            scope_id = scope.id

        # Initialize memory for session
        self.memory.set(
            key=f"session:{session_id}",
            value={
                "process_id": process_id,
                "agent": agent,
                "started_at": now.isoformat()
            },
            scope=MemoryScope.SESSION
        )

        # Create process state
        process_state = self.state.create_process(
            process_id=session_id,
            total_steps=len(process.steps),
            description=process.metadata.description
        )

        session = OrchestratorSession(
            id=session_id,
            process_id=process_id,
            process=process,
            agent=agent,
            created_at=now,
            updated_at=now,
            status=SessionStatus.CREATED,
            current_step_id=process.entry_step,
            execution_mode=StepExecutionMode(execution_mode),
            context=context or {},
            step_results=[],
            checkpoints=[],
            hypotheses=[],
            state_machine_id=sm.id,
            task_chain_id=chain.id,
            scope_id=scope_id,
            metadata=metadata or {}
        )

        self.sessions[session.id] = session
        self._save_sessions()

        return session

    def get_session(self, session_id: str) -> Optional[OrchestratorSession]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def get_current_step(self, session_id: str) -> Optional[ProcessStep]:
        """Get current step for a session."""
        session = self.get_session(session_id)
        if not session:
            return None
        return session.process.get_step(session.current_step_id)

    def get_available_navigation(self, session_id: str) -> List[NavigationLink]:
        """Get available navigation options from current step."""
        session = self.get_session(session_id)
        if not session:
            return []

        step = session.process.get_step(session.current_step_id)
        if not step:
            return []

        # Filter navigation based on conditions
        available = []
        for nav in step.navigation:
            if nav.condition:
                # Evaluate condition against context
                if self._evaluate_condition(nav.condition, session.context):
                    available.append(nav)
            else:
                available.append(nav)

        return available

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a navigation condition."""
        # Simple condition evaluation
        condition_lower = condition.lower()

        # Check for boolean context values
        for key, value in context.items():
            if key.lower() in condition_lower:
                if isinstance(value, bool):
                    if value and "complete" in condition_lower:
                        return True
                    if not value and "fail" in condition_lower:
                        return True

        # Check for status indicators
        if "success" in condition_lower or "complete" in condition_lower:
            return context.get("last_success", True)
        if "fail" in condition_lower or "error" in condition_lower:
            return not context.get("last_success", True)

        # Default to True for unknown conditions
        return True

    def has_next(self, session_id: str) -> bool:
        """Check if session has more steps."""
        session = self.get_session(session_id)
        if not session:
            return False

        if session.status in [SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.CANCELLED]:
            return False

        step = session.process.get_step(session.current_step_id)
        if not step:
            return False

        # Check if current step is an exit step with only END navigation
        has_non_end_nav = any(
            nav.nav_type != NavigationType.END
            for nav in step.navigation
        )

        return has_non_end_nav or session.current_step_id not in session.process.exit_steps

    async def create_checkpoint(self, session_id: str) -> Optional[SessionCheckpoint]:
        """Create a checkpoint for session recovery."""
        session = self.get_session(session_id)
        if not session:
            return None

        # Capture current state
        state = {
            "current_step_id": session.current_step_id,
            "context": session.context.copy(),
            "status": session.status.value,
            "step_count": len(session.step_results)
        }

        # Capture memory snapshot
        memory_snapshot = self.memory.get_all(scope=MemoryScope.SESSION)

        checkpoint = SessionCheckpoint(
            id=str(uuid.uuid4()),
            session_id=session_id,
            step_id=session.current_step_id,
            timestamp=datetime.now(),
            state=state,
            memory_snapshot=memory_snapshot
        )

        session.checkpoints.append(checkpoint)
        self._save_sessions()

        return checkpoint

    async def restore_checkpoint(self, session_id: str, checkpoint_id: str) -> bool:
        """Restore session from checkpoint."""
        session = self.get_session(session_id)
        if not session:
            return False

        checkpoint = None
        for cp in session.checkpoints:
            if cp.id == checkpoint_id:
                checkpoint = cp
                break

        if not checkpoint or not checkpoint.can_resume:
            return False

        # Restore state
        session.current_step_id = checkpoint.state["current_step_id"]
        session.context = checkpoint.state["context"]
        session.status = SessionStatus(checkpoint.state["status"])

        # Restore memory
        for key, value in checkpoint.memory_snapshot.items():
            self.memory.set(key, value, scope=MemoryScope.SESSION)

        session.updated_at = datetime.now()
        self._save_sessions()

        return True

    async def trial_step(self, session_id: str) -> Optional[TrialRunResult]:
        """
        Execute trial run for current step.

        Returns:
            TrialRunResult or None
        """
        session = self.get_session(session_id)
        if not session:
            return None

        step = session.process.get_step(session.current_step_id)
        if not step:
            return None

        # Create trial with step actions
        trial_actions = []
        for action in step.actions:
            trial_actions.append({
                "type": action.tool or "custom",
                "description": action.description,
                "params": action.tool_args
            })

        trial = self.trial.create_trial(
            name=f"Trial: {step.title}",
            description=step.description,
            actions=trial_actions,
            context=session.context
        )

        # Execute dry run
        result = await self.trial.execute_dry_run(trial.id)

        return result

    async def execute_step(
        self,
        session_id: str,
        navigation_choice: Optional[str] = None
    ) -> StepResult:
        """
        Execute current step and advance.

        Args:
            session_id: Session ID
            navigation_choice: Optional navigation label to follow

        Returns:
            StepResult
        """
        session = self.get_session(session_id)
        if not session:
            return StepResult(
                step_id="unknown",
                success=False,
                output=None,
                error="Session not found"
            )

        step = session.process.get_step(session.current_step_id)
        if not step:
            return StepResult(
                step_id=session.current_step_id,
                success=False,
                output=None,
                error="Step not found"
            )

        # Update session status
        session.status = SessionStatus.RUNNING
        session.updated_at = datetime.now()

        # Create checkpoint if step is a checkpoint
        if step.is_checkpoint:
            await self.create_checkpoint(session_id)

        # Update state indicator
        self.state.advance_step(
            process_id=session_id,
            step_label=step.title,
            phase=StatePhase.ACTIVE
        )

        # Create hypothesis for step
        hypothesis = self.hypothesis.create_hypothesis(
            description=f"Step '{step.title}' will complete successfully",
            expected_outcomes=[
                {"description": step.expected_output or "Step completes", "probability": 0.8}
            ],
            context=session.context
        )
        session.hypotheses.append(hypothesis)

        # Execute step actions
        start_time = datetime.now()
        success = True
        output = None
        error = None
        trial_result = None

        try:
            # Trial run first if in that mode
            if session.execution_mode == StepExecutionMode.TRIAL_FIRST:
                trial_result = await self.trial_step(session_id)
                if trial_result and not trial_result.can_proceed:
                    success = False
                    error = "Trial run failed: " + (trial_result.issues[0].description if trial_result.issues else "Unknown")

            if success:
                # Check scope guard
                if session.scope_id:
                    for action in step.actions:
                        if action.tool:
                            check = self.guard.check_change(
                                scope_id=session.scope_id,
                                file_path=action.tool_args.get("path", ""),
                                operation=action.tool or "custom",
                                description=action.description
                            )
                            if not check.allowed:
                                success = False
                                error = f"Guard blocked: {check.reason}"
                                break

            if success:
                # Execute actions
                action_outputs = []
                for action in step.actions:
                    if action.tool and action.tool in self.step_handlers:
                        handler = self.step_handlers[action.tool]
                        result = await handler(action, session.context)
                        action_outputs.append(result)
                    else:
                        action_outputs.append({"action": action.description, "simulated": True})

                output = action_outputs

        except Exception as e:
            success = False
            error = str(e)

        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        # Verify hypothesis
        self.hypothesis.verify(
            hypothesis_id=hypothesis.id,
            actual_outcome={"success": success, "output": str(output)[:200] if output else None},
            method="execution"
        )

        # Update context
        session.context["last_success"] = success
        session.context["last_output"] = output

        # Get available navigation
        available_nav = self.get_available_navigation(session_id)

        # Determine next step
        next_step_id = None
        if success and available_nav:
            if navigation_choice:
                # Find matching navigation
                for nav in available_nav:
                    if nav.label.lower() == navigation_choice.lower():
                        next_step_id = nav.target
                        break
            else:
                # Use first available navigation
                for nav in available_nav:
                    if nav.nav_type == NavigationType.NEXT:
                        next_step_id = nav.target
                        break
                if not next_step_id and available_nav:
                    next_step_id = available_nav[0].target

        # Create step result
        result = StepResult(
            step_id=step.id,
            success=success,
            output=output,
            error=error,
            duration_ms=duration_ms,
            hypothesis_verified=hypothesis.status == HypothesisStatus.VERIFIED,
            trial_run=trial_result,
            next_steps=available_nav
        )

        session.step_results.append(result)

        # Update state
        self.state.advance_step(
            process_id=session_id,
            step_label=step.title,
            phase=StatePhase.COMPLETE if success else StatePhase.ERROR
        )

        # Advance to next step or complete
        if next_step_id:
            session.current_step_id = next_step_id
            # Trigger state machine transition
            if session.state_machine_id:
                sm = self.statemachine.get_machine(session.state_machine_id)
                if sm:
                    for trans in sm.transitions:
                        if trans.from_state == step.id and trans.to_state == next_step_id:
                            await self.statemachine.execute_transition(
                                sm.id,
                                trans.trigger,
                                session.context
                            )
                            break
        else:
            # Check if we're at an exit step
            if step.id in session.process.exit_steps or any(n.nav_type == NavigationType.END for n in step.navigation):
                session.status = SessionStatus.COMPLETED if success else SessionStatus.FAILED
            else:
                session.status = SessionStatus.WAITING

        session.updated_at = datetime.now()
        self._save_sessions()

        # Store in memory
        self.memory.set(
            key=f"step_result:{session_id}:{step.id}",
            value=result.to_dict(),
            scope=MemoryScope.TASK
        )

        return result

    async def run_to_completion(
        self,
        session_id: str,
        max_steps: int = 100
    ) -> List[StepResult]:
        """
        Run session to completion.

        Args:
            session_id: Session ID
            max_steps: Maximum steps to execute

        Returns:
            List of StepResults
        """
        results = []
        steps_executed = 0

        while self.has_next(session_id) and steps_executed < max_steps:
            result = await self.execute_step(session_id)
            results.append(result)
            steps_executed += 1

            if not result.success:
                break

        return results

    def pause_session(self, session_id: str) -> bool:
        """Pause a running session."""
        session = self.get_session(session_id)
        if not session:
            return False

        if session.status == SessionStatus.RUNNING:
            session.status = SessionStatus.PAUSED
            session.updated_at = datetime.now()
            self._save_sessions()
            return True
        return False

    def resume_session(self, session_id: str) -> bool:
        """Resume a paused session."""
        session = self.get_session(session_id)
        if not session:
            return False

        if session.status == SessionStatus.PAUSED:
            session.status = SessionStatus.RUNNING
            session.updated_at = datetime.now()
            self._save_sessions()
            return True
        return False

    def cancel_session(self, session_id: str) -> bool:
        """Cancel a session."""
        session = self.get_session(session_id)
        if not session:
            return False

        if session.status not in [SessionStatus.COMPLETED, SessionStatus.CANCELLED]:
            session.status = SessionStatus.CANCELLED
            session.updated_at = datetime.now()

            # Close scope
            if session.scope_id:
                self.guard.close_scope(session.scope_id)

            self._save_sessions()
            return True
        return False

    def get_session_report(self, session_id: str) -> str:
        """Generate markdown report for session."""
        session = self.get_session(session_id)
        if not session:
            return f"Session '{session_id}' not found"

        status_icons = {
            SessionStatus.CREATED: "",
            SessionStatus.RUNNING: "",
            SessionStatus.PAUSED: "",
            SessionStatus.WAITING: "",
            SessionStatus.COMPLETED: "",
            SessionStatus.FAILED: "",
            SessionStatus.CANCELLED: ""
        }

        lines = [
            f"# Session Report {status_icons.get(session.status, '')}",
            "",
            f"**Process**: {session.process.metadata.name}",
            f"**Agent**: {session.agent}",
            f"**Status**: {session.status.value}",
            f"**Started**: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Updated**: {session.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Progress",
            "",
            self.state.format_progress(session_id),
            "",
            "## Steps Executed",
            ""
        ]

        for result in session.step_results:
            icon = "" if result.success else ""
            lines.append(f"### {icon} {result.step_id}")
            if result.error:
                lines.append(f"**Error**: {result.error}")
            lines.append(f"**Duration**: {result.duration_ms:.2f}ms")
            if result.next_steps:
                lines.append(f"**Next options**: {', '.join(n.label for n in result.next_steps)}")
            lines.append("")

        if session.hypotheses:
            lines.extend([
                "## Hypotheses",
                ""
            ])
            verified = sum(1 for h in session.hypotheses if h.status == HypothesisStatus.VERIFIED)
            total = len(session.hypotheses)
            lines.append(f"**Verified**: {verified}/{total}")
            lines.append("")

        if session.checkpoints:
            lines.extend([
                "## Checkpoints",
                ""
            ])
            for cp in session.checkpoints:
                lines.append(f"- {cp.timestamp.strftime('%H:%M:%S')} - Step: {cp.step_id}")
            lines.append("")

        # Add scope summary if available
        if session.scope_id:
            scope = self.guard.get_scope(session.scope_id)
            if scope:
                lines.extend([
                    "## Scope Guard",
                    "",
                    f"**Files changed**: {len(scope.files_changed)} / {scope.max_files_changed}",
                    f"**Lines changed**: {scope.lines_changed} / {scope.max_lines_changed}",
                    f"**Violations**: {len(scope.violations)}",
                    ""
                ])

        return "\n".join(lines)

    def list_sessions(
        self,
        agent: Optional[str] = None,
        status: Optional[SessionStatus] = None
    ) -> List[OrchestratorSession]:
        """List sessions with optional filters."""
        sessions = list(self.sessions.values())

        if agent:
            sessions = [s for s in sessions if s.agent == agent]
        if status:
            sessions = [s for s in sessions if s.status == status]

        return sorted(sessions, key=lambda s: s.created_at, reverse=True)

    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        sessions = list(self.sessions.values())

        by_status = {}
        for s in sessions:
            by_status[s.status.value] = by_status.get(s.status.value, 0) + 1

        total_steps = sum(len(s.step_results) for s in sessions)
        successful_steps = sum(
            sum(1 for r in s.step_results if r.success)
            for s in sessions
        )

        return {
            "total_sessions": len(sessions),
            "by_status": by_status,
            "total_steps_executed": total_steps,
            "successful_steps": successful_steps,
            "success_rate": (successful_steps / total_steps * 100) if total_steps > 0 else 0,
            "active_sessions": len([s for s in sessions if s.status == SessionStatus.RUNNING])
        }
