"""
StateMachine as Tool Service

Week 108 - AO-M-2: State transitions as MCP tool commands.

Based on Gregor Riegler's Augmented Coding Pattern Language:
- State machines exposed as tool invocations
- Agents can query state and trigger transitions
- Full transition history with rollback capability
- MCP-compatible tool definitions
- Guard conditions and side effects

Example usage:
    service = StateMachineToolService()

    # Define a workflow state machine
    machine = service.create_machine(
        name="feature_workflow",
        initial_state="backlog",
        states=["backlog", "analysis", "design", "implementation", "review", "done"],
        transitions=[
            {"from": "backlog", "to": "analysis", "trigger": "start_analysis"},
            {"from": "analysis", "to": "design", "trigger": "approve_analysis"},
            {"from": "design", "to": "implementation", "trigger": "start_coding"},
            {"from": "implementation", "to": "review", "trigger": "submit_review"},
            {"from": "review", "to": "implementation", "trigger": "request_changes"},
            {"from": "review", "to": "done", "trigger": "approve"},
        ]
    )

    # Get MCP tool definitions
    tools = service.get_mcp_tools(machine.id)

    # Execute transition via tool call
    result = await service.execute_tool(
        machine_id=machine.id,
        tool_name="trigger_start_analysis",
        context={"agent": "Peter", "reason": "Requirements complete"}
    )
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, Awaitable
from pathlib import Path
import json
import uuid
import asyncio


class TransitionResult(Enum):
    """Result of a state transition attempt."""
    SUCCESS = "success"
    GUARD_FAILED = "guard_failed"
    INVALID_TRANSITION = "invalid_transition"
    MACHINE_NOT_FOUND = "machine_not_found"
    ALREADY_IN_STATE = "already_in_state"
    SIDE_EFFECT_FAILED = "side_effect_failed"


@dataclass
class TransitionGuard:
    """Guard condition for a transition."""
    name: str
    description: str
    condition: Callable[[Dict[str, Any]], bool]
    error_message: str = "Guard condition not met"

    def check(self, context: Dict[str, Any]) -> bool:
        """Check if guard condition is satisfied."""
        try:
            return self.condition(context)
        except Exception:
            return False


@dataclass
class SideEffect:
    """Side effect to execute on transition."""
    name: str
    description: str
    action: Callable[[Dict[str, Any]], Awaitable[Any]]
    rollback: Optional[Callable[[Dict[str, Any]], Awaitable[Any]]] = None
    required: bool = True


@dataclass
class StateTransition:
    """Definition of a state transition."""
    from_state: str
    to_state: str
    trigger: str
    description: str = ""
    guards: List[TransitionGuard] = field(default_factory=list)
    side_effects: List[SideEffect] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransitionHistory:
    """Record of a completed transition."""
    id: str
    timestamp: datetime
    from_state: str
    to_state: str
    trigger: str
    context: Dict[str, Any]
    result: TransitionResult
    error_message: Optional[str] = None
    side_effect_results: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "from_state": self.from_state,
            "to_state": self.to_state,
            "trigger": self.trigger,
            "context": self.context,
            "result": self.result.value,
            "error_message": self.error_message,
            "side_effect_results": self.side_effect_results
        }


@dataclass
class MCPToolDefinition:
    """MCP-compatible tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
            "metadata": self.metadata
        }


@dataclass
class StateMachine:
    """State machine definition."""
    id: str
    name: str
    description: str
    initial_state: str
    current_state: str
    states: List[str]
    transitions: List[StateTransition]
    context: Dict[str, Any]
    history: List[TransitionHistory]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_available_transitions(self) -> List[StateTransition]:
        """Get transitions available from current state."""
        return [t for t in self.transitions if t.from_state == self.current_state]

    def get_transition(self, trigger: str) -> Optional[StateTransition]:
        """Get transition by trigger name from current state."""
        for t in self.transitions:
            if t.from_state == self.current_state and t.trigger == trigger:
                return t
        return None

    def can_transition(self, trigger: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if transition is possible."""
        transition = self.get_transition(trigger)
        if not transition:
            return False

        ctx = {**self.context, **(context or {})}
        for guard in transition.guards:
            if not guard.check(ctx):
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "initial_state": self.initial_state,
            "current_state": self.current_state,
            "states": self.states,
            "transitions": [
                {
                    "from_state": t.from_state,
                    "to_state": t.to_state,
                    "trigger": t.trigger,
                    "description": t.description,
                    "guards": [g.name for g in t.guards],
                    "side_effects": [s.name for s in t.side_effects],
                    "metadata": t.metadata
                }
                for t in self.transitions
            ],
            "context": self.context,
            "history": [h.to_dict() for h in self.history],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }

    def to_mermaid(self) -> str:
        """Generate Mermaid state diagram."""
        lines = ["stateDiagram-v2"]
        lines.append(f"    [*] --> {self.initial_state}")

        for transition in self.transitions:
            label = transition.trigger
            if transition.guards:
                label += f" [{', '.join(g.name for g in transition.guards)}]"
            lines.append(f"    {transition.from_state} --> {transition.to_state}: {label}")

        # Mark current state
        lines.append(f"    note right of {self.current_state}: CURRENT")

        return "\n".join(lines)

    def to_xstate(self) -> Dict[str, Any]:
        """
        Generate XState JSON format for modern frontend state management.

        XState is a popular JavaScript/TypeScript state machine library.
        This export format is compatible with XState v5.

        Returns:
            Dict with XState machine configuration
        """
        states_dict: Dict[str, Any] = {}

        for state_name in self.states:
            state_def: Dict[str, Any] = {}

            # Find transitions from this state
            state_transitions = [t for t in self.transitions if t.from_state == state_name]

            if state_transitions:
                on_dict: Dict[str, Any] = {}
                for trans in state_transitions:
                    trans_def: Dict[str, Any] = {"target": trans.to_state}

                    # Add guards if present
                    if trans.guards:
                        guard_names = [g.name for g in trans.guards]
                        if len(guard_names) == 1:
                            trans_def["guard"] = guard_names[0]
                        else:
                            trans_def["guard"] = {"type": "and", "guards": guard_names}

                    # Add actions (side effects) if present
                    if trans.side_effects:
                        trans_def["actions"] = [s.name for s in trans.side_effects]

                    on_dict[trans.trigger] = trans_def

                state_def["on"] = on_dict

            states_dict[state_name] = state_def if state_def else {}

        return {
            "id": self.name,
            "initial": self.initial_state,
            "context": self.context,
            "states": states_dict
        }


class StateMachineToolService:
    """
    Service for managing state machines as MCP tools.

    Provides:
    - State machine creation and management
    - MCP tool generation for transitions
    - Transition execution with guards and side effects
    - History tracking and rollback
    - Persistence to file system
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(".agent_memory/statemachines")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.machines: Dict[str, StateMachine] = {}
        self.registered_guards: Dict[str, TransitionGuard] = {}
        self.registered_side_effects: Dict[str, SideEffect] = {}
        self._load_machines()

    def _load_machines(self) -> None:
        """Load machines from storage."""
        for file_path in self.storage_path.glob("*.json"):
            try:
                data = json.loads(file_path.read_text())
                machine = self._machine_from_dict(data)
                self.machines[machine.id] = machine
            except Exception:
                pass

    def _machine_from_dict(self, data: Dict[str, Any]) -> StateMachine:
        """Reconstruct machine from dictionary."""
        transitions = []
        for t in data.get("transitions", []):
            guards = [self.registered_guards.get(g) for g in t.get("guards", []) if g in self.registered_guards]
            side_effects = [self.registered_side_effects.get(s) for s in t.get("side_effects", []) if s in self.registered_side_effects]
            transitions.append(StateTransition(
                from_state=t["from_state"],
                to_state=t["to_state"],
                trigger=t["trigger"],
                description=t.get("description", ""),
                guards=[g for g in guards if g],
                side_effects=[s for s in side_effects if s],
                metadata=t.get("metadata", {})
            ))

        history = [
            TransitionHistory(
                id=h["id"],
                timestamp=datetime.fromisoformat(h["timestamp"]),
                from_state=h["from_state"],
                to_state=h["to_state"],
                trigger=h["trigger"],
                context=h["context"],
                result=TransitionResult(h["result"]),
                error_message=h.get("error_message"),
                side_effect_results=h.get("side_effect_results", {})
            )
            for h in data.get("history", [])
        ]

        return StateMachine(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            initial_state=data["initial_state"],
            current_state=data["current_state"],
            states=data["states"],
            transitions=transitions,
            context=data.get("context", {}),
            history=history,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {})
        )

    def _save_machine(self, machine: StateMachine) -> None:
        """Persist machine to storage."""
        file_path = self.storage_path / f"{machine.id}.json"
        file_path.write_text(json.dumps(machine.to_dict(), indent=2, default=str))

    def register_guard(self, guard: TransitionGuard) -> None:
        """Register a reusable guard condition."""
        self.registered_guards[guard.name] = guard

    def register_side_effect(self, side_effect: SideEffect) -> None:
        """Register a reusable side effect."""
        self.registered_side_effects[side_effect.name] = side_effect

    def create_machine(
        self,
        name: str,
        initial_state: str,
        states: List[str],
        transitions: List[Dict[str, Any]],
        description: str = "",
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StateMachine:
        """
        Create a new state machine.

        Args:
            name: Machine name
            initial_state: Starting state
            states: List of valid states
            transitions: List of transition definitions
            description: Machine description
            context: Initial context data
            metadata: Additional metadata

        Returns:
            Created StateMachine instance
        """
        if initial_state not in states:
            raise ValueError(f"Initial state '{initial_state}' not in states list")

        parsed_transitions = []
        for t in transitions:
            from_state = t["from"]
            to_state = t["to"]

            if from_state not in states:
                raise ValueError(f"From state '{from_state}' not in states list")
            if to_state not in states:
                raise ValueError(f"To state '{to_state}' not in states list")

            guards = []
            for guard_name in t.get("guards", []):
                if guard_name in self.registered_guards:
                    guards.append(self.registered_guards[guard_name])

            side_effects = []
            for effect_name in t.get("side_effects", []):
                if effect_name in self.registered_side_effects:
                    side_effects.append(self.registered_side_effects[effect_name])

            parsed_transitions.append(StateTransition(
                from_state=from_state,
                to_state=to_state,
                trigger=t["trigger"],
                description=t.get("description", ""),
                guards=guards,
                side_effects=side_effects,
                metadata=t.get("metadata", {})
            ))

        now = datetime.now()
        machine = StateMachine(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            initial_state=initial_state,
            current_state=initial_state,
            states=states,
            transitions=parsed_transitions,
            context=context or {},
            history=[],
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )

        self.machines[machine.id] = machine
        self._save_machine(machine)
        return machine

    def get_machine(self, machine_id: str) -> Optional[StateMachine]:
        """Get machine by ID."""
        return self.machines.get(machine_id)

    def get_machine_by_name(self, name: str) -> Optional[StateMachine]:
        """Get machine by name."""
        for machine in self.machines.values():
            if machine.name == name:
                return machine
        return None

    def list_machines(self) -> List[StateMachine]:
        """List all machines."""
        return list(self.machines.values())

    def delete_machine(self, machine_id: str) -> bool:
        """Delete a machine."""
        if machine_id in self.machines:
            del self.machines[machine_id]
            file_path = self.storage_path / f"{machine_id}.json"
            if file_path.exists():
                file_path.unlink()
            return True
        return False

    async def execute_transition(
        self,
        machine_id: str,
        trigger: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TransitionHistory:
        """
        Execute a state transition.

        Args:
            machine_id: Machine ID
            trigger: Transition trigger name
            context: Additional context for transition

        Returns:
            TransitionHistory record
        """
        machine = self.get_machine(machine_id)
        if not machine:
            return TransitionHistory(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                from_state="unknown",
                to_state="unknown",
                trigger=trigger,
                context=context or {},
                result=TransitionResult.MACHINE_NOT_FOUND,
                error_message=f"Machine '{machine_id}' not found"
            )

        transition = machine.get_transition(trigger)
        if not transition:
            return TransitionHistory(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                from_state=machine.current_state,
                to_state=machine.current_state,
                trigger=trigger,
                context=context or {},
                result=TransitionResult.INVALID_TRANSITION,
                error_message=f"No transition '{trigger}' from state '{machine.current_state}'"
            )

        if machine.current_state == transition.to_state:
            return TransitionHistory(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                from_state=machine.current_state,
                to_state=transition.to_state,
                trigger=trigger,
                context=context or {},
                result=TransitionResult.ALREADY_IN_STATE,
                error_message=f"Already in state '{transition.to_state}'"
            )

        # Merge contexts
        full_context = {**machine.context, **(context or {})}

        # Check guards
        for guard in transition.guards:
            if not guard.check(full_context):
                return TransitionHistory(
                    id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    from_state=machine.current_state,
                    to_state=transition.to_state,
                    trigger=trigger,
                    context=full_context,
                    result=TransitionResult.GUARD_FAILED,
                    error_message=f"Guard '{guard.name}' failed: {guard.error_message}"
                )

        # Execute side effects
        side_effect_results = {}
        executed_effects = []

        for effect in transition.side_effects:
            try:
                result = await effect.action(full_context)
                side_effect_results[effect.name] = {"success": True, "result": result}
                executed_effects.append(effect)
            except Exception as e:
                side_effect_results[effect.name] = {"success": False, "error": str(e)}

                if effect.required:
                    # Rollback executed effects
                    for executed in reversed(executed_effects):
                        if executed.rollback:
                            try:
                                await executed.rollback(full_context)
                            except Exception:
                                pass

                    return TransitionHistory(
                        id=str(uuid.uuid4()),
                        timestamp=datetime.now(),
                        from_state=machine.current_state,
                        to_state=transition.to_state,
                        trigger=trigger,
                        context=full_context,
                        result=TransitionResult.SIDE_EFFECT_FAILED,
                        error_message=f"Side effect '{effect.name}' failed: {str(e)}",
                        side_effect_results=side_effect_results
                    )

        # Perform transition
        old_state = machine.current_state
        machine.current_state = transition.to_state
        machine.updated_at = datetime.now()

        history = TransitionHistory(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            from_state=old_state,
            to_state=transition.to_state,
            trigger=trigger,
            context=full_context,
            result=TransitionResult.SUCCESS,
            side_effect_results=side_effect_results
        )

        machine.history.append(history)
        self._save_machine(machine)

        return history

    async def rollback_transition(
        self,
        machine_id: str,
        history_id: str
    ) -> Optional[TransitionHistory]:
        """
        Rollback to a previous state.

        Args:
            machine_id: Machine ID
            history_id: History entry to rollback to

        Returns:
            New history entry for rollback
        """
        machine = self.get_machine(machine_id)
        if not machine:
            return None

        # Find the history entry
        target_entry = None
        target_index = -1
        for i, entry in enumerate(machine.history):
            if entry.id == history_id:
                target_entry = entry
                target_index = i
                break

        if not target_entry:
            return None

        # Rollback to the from_state of that entry
        old_state = machine.current_state
        machine.current_state = target_entry.from_state
        machine.updated_at = datetime.now()

        # Remove history after this point
        machine.history = machine.history[:target_index]

        rollback_history = TransitionHistory(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            from_state=old_state,
            to_state=target_entry.from_state,
            trigger="rollback",
            context={"rollback_to": history_id},
            result=TransitionResult.SUCCESS
        )

        machine.history.append(rollback_history)
        self._save_machine(machine)

        return rollback_history

    def get_mcp_tools(self, machine_id: str) -> List[MCPToolDefinition]:
        """
        Generate MCP tool definitions for a machine's transitions.

        Args:
            machine_id: Machine ID

        Returns:
            List of MCP tool definitions
        """
        machine = self.get_machine(machine_id)
        if not machine:
            return []

        tools = []

        # Tool to get current state
        tools.append(MCPToolDefinition(
            name=f"sm_{machine.name}_get_state",
            description=f"Get current state of {machine.name} state machine",
            input_schema={
                "type": "object",
                "properties": {},
                "required": []
            },
            metadata={"machine_id": machine_id, "operation": "get_state"}
        ))

        # Tool to list available transitions
        tools.append(MCPToolDefinition(
            name=f"sm_{machine.name}_list_transitions",
            description=f"List available transitions from current state of {machine.name}",
            input_schema={
                "type": "object",
                "properties": {},
                "required": []
            },
            metadata={"machine_id": machine_id, "operation": "list_transitions"}
        ))

        # Tools for each transition trigger
        seen_triggers = set()
        for transition in machine.transitions:
            if transition.trigger in seen_triggers:
                continue
            seen_triggers.add(transition.trigger)

            description = transition.description or f"Trigger '{transition.trigger}' transition"
            if transition.guards:
                description += f" (guards: {', '.join(g.name for g in transition.guards)})"

            tools.append(MCPToolDefinition(
                name=f"sm_{machine.name}_trigger_{transition.trigger}",
                description=description,
                input_schema={
                    "type": "object",
                    "properties": {
                        "context": {
                            "type": "object",
                            "description": "Additional context for the transition"
                        }
                    },
                    "required": []
                },
                metadata={
                    "machine_id": machine_id,
                    "operation": "trigger",
                    "trigger": transition.trigger
                }
            ))

        # Tool to rollback
        tools.append(MCPToolDefinition(
            name=f"sm_{machine.name}_rollback",
            description=f"Rollback {machine.name} to a previous state",
            input_schema={
                "type": "object",
                "properties": {
                    "history_id": {
                        "type": "string",
                        "description": "History entry ID to rollback to"
                    }
                },
                "required": ["history_id"]
            },
            metadata={"machine_id": machine_id, "operation": "rollback"}
        ))

        return tools

    async def execute_tool(
        self,
        machine_id: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an MCP tool call for a state machine.

        Args:
            machine_id: Machine ID
            tool_name: Tool name to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        machine = self.get_machine(machine_id)
        if not machine:
            return {"error": f"Machine '{machine_id}' not found"}

        args = arguments or {}

        # Parse tool name to determine operation
        prefix = f"sm_{machine.name}_"
        if not tool_name.startswith(prefix):
            return {"error": f"Invalid tool name for machine '{machine.name}'"}

        operation = tool_name[len(prefix):]

        if operation == "get_state":
            return {
                "current_state": machine.current_state,
                "available_transitions": [
                    {"trigger": t.trigger, "to_state": t.to_state}
                    for t in machine.get_available_transitions()
                ]
            }

        elif operation == "list_transitions":
            return {
                "transitions": [
                    {
                        "trigger": t.trigger,
                        "to_state": t.to_state,
                        "description": t.description,
                        "guards": [g.name for g in t.guards],
                        "can_execute": machine.can_transition(t.trigger, args.get("context"))
                    }
                    for t in machine.get_available_transitions()
                ]
            }

        elif operation.startswith("trigger_"):
            trigger = operation[len("trigger_"):]
            result = await self.execute_transition(
                machine_id=machine_id,
                trigger=trigger,
                context=args.get("context")
            )
            return result.to_dict()

        elif operation == "rollback":
            history_id = args.get("history_id")
            if not history_id:
                return {"error": "history_id is required"}

            result = await self.rollback_transition(machine_id, history_id)
            if result:
                return result.to_dict()
            return {"error": "Rollback failed"}

        return {"error": f"Unknown operation '{operation}'"}

    def get_machine_markdown(self, machine_id: str) -> str:
        """
        Generate markdown documentation for a machine.

        Args:
            machine_id: Machine ID

        Returns:
            Markdown string
        """
        machine = self.get_machine(machine_id)
        if not machine:
            return f"Machine '{machine_id}' not found"

        lines = [
            f"# State Machine: {machine.name}",
            "",
            machine.description if machine.description else "*No description*",
            "",
            "## Current State",
            "",
            f"**{machine.current_state}**",
            "",
            "## State Diagram",
            "",
            "```mermaid",
            machine.to_mermaid(),
            "```",
            "",
            "## States",
            "",
        ]

        for state in machine.states:
            marker = " (current)" if state == machine.current_state else ""
            lines.append(f"- `{state}`{marker}")

        lines.extend([
            "",
            "## Transitions",
            "",
            "| From | To | Trigger | Guards |",
            "|------|-----|---------|--------|"
        ])

        for t in machine.transitions:
            guards = ", ".join(g.name for g in t.guards) if t.guards else "-"
            lines.append(f"| {t.from_state} | {t.to_state} | {t.trigger} | {guards} |")

        lines.extend([
            "",
            "## Available Actions",
            ""
        ])

        for t in machine.get_available_transitions():
            can_execute = machine.can_transition(t.trigger)
            status = "ready" if can_execute else "blocked"
            lines.append(f"- `{t.trigger}` -> `{t.to_state}` ({status})")

        if machine.history:
            lines.extend([
                "",
                "## Recent History",
                "",
                "| Time | From | To | Trigger | Result |",
                "|------|------|-----|---------|--------|"
            ])

            for h in machine.history[-10:]:
                time_str = h.timestamp.strftime("%H:%M:%S")
                lines.append(f"| {time_str} | {h.from_state} | {h.to_state} | {h.trigger} | {h.result.value} |")

        return "\n".join(lines)


# Predefined workflow state machines
def create_feature_workflow_machine(service: StateMachineToolService) -> StateMachine:
    """Create a standard feature development workflow machine."""
    return service.create_machine(
        name="feature_workflow",
        description="Standard feature development workflow from backlog to deployment",
        initial_state="backlog",
        states=[
            "backlog",
            "analysis",
            "design",
            "implementation",
            "code_review",
            "testing",
            "staging",
            "production",
            "done"
        ],
        transitions=[
            {"from": "backlog", "to": "analysis", "trigger": "start_analysis", "description": "Begin requirements analysis"},
            {"from": "analysis", "to": "design", "trigger": "complete_analysis", "description": "Analysis approved, begin design"},
            {"from": "analysis", "to": "backlog", "trigger": "reject_analysis", "description": "Analysis rejected, return to backlog"},
            {"from": "design", "to": "implementation", "trigger": "approve_design", "description": "Design approved, begin coding"},
            {"from": "design", "to": "analysis", "trigger": "revise_design", "description": "Design needs revision"},
            {"from": "implementation", "to": "code_review", "trigger": "submit_for_review", "description": "Code ready for review"},
            {"from": "code_review", "to": "implementation", "trigger": "request_changes", "description": "Reviewer requests changes"},
            {"from": "code_review", "to": "testing", "trigger": "approve_code", "description": "Code approved, begin testing"},
            {"from": "testing", "to": "implementation", "trigger": "tests_failed", "description": "Tests failed, fix issues"},
            {"from": "testing", "to": "staging", "trigger": "tests_passed", "description": "Tests passed, deploy to staging"},
            {"from": "staging", "to": "testing", "trigger": "staging_issues", "description": "Issues found in staging"},
            {"from": "staging", "to": "production", "trigger": "approve_staging", "description": "Staging approved, deploy to production"},
            {"from": "production", "to": "done", "trigger": "verify_production", "description": "Production verified, feature complete"},
        ]
    )


def create_bug_workflow_machine(service: StateMachineToolService) -> StateMachine:
    """Create a bug tracking workflow machine."""
    return service.create_machine(
        name="bug_workflow",
        description="Bug tracking and resolution workflow",
        initial_state="reported",
        states=[
            "reported",
            "triaged",
            "investigating",
            "fix_in_progress",
            "fix_review",
            "testing",
            "verified",
            "closed",
            "wont_fix"
        ],
        transitions=[
            {"from": "reported", "to": "triaged", "trigger": "triage", "description": "Bug triaged and prioritized"},
            {"from": "reported", "to": "wont_fix", "trigger": "reject", "description": "Not a bug or won't fix"},
            {"from": "triaged", "to": "investigating", "trigger": "start_investigation", "description": "Begin investigation"},
            {"from": "investigating", "to": "fix_in_progress", "trigger": "found_root_cause", "description": "Root cause found, begin fix"},
            {"from": "investigating", "to": "wont_fix", "trigger": "cannot_reproduce", "description": "Cannot reproduce"},
            {"from": "fix_in_progress", "to": "fix_review", "trigger": "submit_fix", "description": "Fix ready for review"},
            {"from": "fix_review", "to": "fix_in_progress", "trigger": "fix_rejected", "description": "Fix rejected"},
            {"from": "fix_review", "to": "testing", "trigger": "fix_approved", "description": "Fix approved, begin testing"},
            {"from": "testing", "to": "fix_in_progress", "trigger": "regression_found", "description": "Fix caused regression"},
            {"from": "testing", "to": "verified", "trigger": "tests_passed", "description": "Fix verified"},
            {"from": "verified", "to": "closed", "trigger": "close", "description": "Bug closed"},
        ]
    )


def create_sprint_workflow_machine(service: StateMachineToolService) -> StateMachine:
    """Create a sprint management workflow machine."""
    return service.create_machine(
        name="sprint_workflow",
        description="Sprint planning and execution workflow",
        initial_state="planning",
        states=[
            "planning",
            "committed",
            "in_progress",
            "review",
            "retrospective",
            "completed"
        ],
        transitions=[
            {"from": "planning", "to": "committed", "trigger": "commit_sprint", "description": "Sprint backlog committed"},
            {"from": "committed", "to": "in_progress", "trigger": "start_sprint", "description": "Sprint started"},
            {"from": "in_progress", "to": "review", "trigger": "end_sprint", "description": "Sprint ended, begin review"},
            {"from": "review", "to": "retrospective", "trigger": "complete_review", "description": "Review complete"},
            {"from": "retrospective", "to": "completed", "trigger": "complete_retro", "description": "Retrospective complete"},
            {"from": "completed", "to": "planning", "trigger": "start_next_sprint", "description": "Begin next sprint planning"},
        ]
    )
