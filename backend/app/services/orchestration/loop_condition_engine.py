"""
Loop & Condition Engine

Week 109 - AO-L-2: Loop and conditional execution in workflows.

Based on Gregor Riegler's Augmented Coding Pattern Language:
- For-each loops over collections
- While loops with conditions
- Until loops (do-until)
- Conditional branching (if/else/elif)
- Switch/case patterns
- Loop control (break, continue, retry)
- Nested loops and conditions
- Guard clauses

Example usage:
    engine = LoopConditionEngine()

    # Create a for-each loop
    loop = engine.create_foreach(
        name="process_files",
        collection_expr="context.files",
        item_var="file",
        body=[
            {"type": "action", "action": "validate_file", "args": {"path": "${file}"}},
            {"type": "action", "action": "process_file", "args": {"path": "${file}"}}
        ]
    )

    # Create a conditional
    condition = engine.create_condition(
        name="check_auth",
        if_expr="context.user.is_authenticated",
        then_block=[...],
        else_block=[...]
    )

    # Execute with context
    result = await engine.execute(loop.id, context={"files": ["a.py", "b.py"]})
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, Awaitable, Union
from pathlib import Path
import json
import uuid
import re
import operator


class ConstructType(Enum):
    """Type of control flow construct."""
    FOREACH = "foreach"
    WHILE = "while"
    UNTIL = "until"
    REPEAT = "repeat"
    IF = "if"
    SWITCH = "switch"
    TRY = "try"
    SEQUENCE = "sequence"
    PARALLEL = "parallel"


class LoopControl(Enum):
    """Loop control signals."""
    CONTINUE = "continue"
    BREAK = "break"
    RETRY = "retry"
    RETURN = "return"


class ExecutionStatus(Enum):
    """Status of execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BROKEN = "broken"  # Exited via break


@dataclass
class IterationResult:
    """Result of a single iteration."""
    index: int
    item: Any
    success: bool
    output: Any
    error: Optional[str] = None
    duration_ms: float = 0
    control_signal: Optional[LoopControl] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "item": str(self.item)[:100] if self.item else None,
            "success": self.success,
            "output": str(self.output)[:200] if self.output else None,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "control_signal": self.control_signal.value if self.control_signal else None
        }


@dataclass
class BranchResult:
    """Result of evaluating a branch."""
    branch_name: str
    condition: str
    evaluated_to: bool
    executed: bool
    output: Any = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch_name": self.branch_name,
            "condition": self.condition,
            "evaluated_to": self.evaluated_to,
            "executed": self.executed,
            "output": str(self.output)[:200] if self.output else None,
            "error": self.error
        }


@dataclass
class ExecutionResult:
    """Result of executing a construct."""
    construct_id: str
    construct_type: ConstructType
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime]
    total_iterations: int
    successful_iterations: int
    iteration_results: List[IterationResult]
    branch_results: List[BranchResult]
    final_output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "construct_id": self.construct_id,
            "construct_type": self.construct_type.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_iterations": self.total_iterations,
            "successful_iterations": self.successful_iterations,
            "iteration_results": [r.to_dict() for r in self.iteration_results],
            "branch_results": [b.to_dict() for b in self.branch_results],
            "final_output": str(self.final_output)[:500] if self.final_output else None,
            "error": self.error,
            "metadata": self.metadata
        }


@dataclass
class ActionBlock:
    """An action to execute."""
    action_type: str
    action_name: str
    args: Dict[str, Any]
    output_var: Optional[str] = None
    on_error: str = "fail"  # fail, skip, retry

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.action_type,
            "action": self.action_name,
            "args": self.args,
            "output_var": self.output_var,
            "on_error": self.on_error
        }


@dataclass
class ConditionBranch:
    """A branch in a conditional construct."""
    name: str
    condition: str  # Expression to evaluate
    body: List[Union[ActionBlock, 'ControlConstruct']]
    is_default: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "condition": self.condition,
            "body": [b.to_dict() for b in self.body],
            "is_default": self.is_default
        }


@dataclass
class ControlConstruct:
    """A control flow construct (loop or condition)."""
    id: str
    name: str
    construct_type: ConstructType
    created_at: datetime

    # For loops
    collection_expr: Optional[str] = None
    item_var: Optional[str] = None
    index_var: Optional[str] = None
    condition_expr: Optional[str] = None
    max_iterations: int = 1000
    body: List[Union[ActionBlock, 'ControlConstruct']] = field(default_factory=list)

    # For conditions
    branches: List[ConditionBranch] = field(default_factory=list)

    # For repeat
    count: int = 1

    # For try
    catch_block: List[ActionBlock] = field(default_factory=list)
    finally_block: List[ActionBlock] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.construct_type.value,
            "created_at": self.created_at.isoformat(),
            "collection_expr": self.collection_expr,
            "item_var": self.item_var,
            "index_var": self.index_var,
            "condition_expr": self.condition_expr,
            "max_iterations": self.max_iterations,
            "body": [b.to_dict() for b in self.body],
            "branches": [b.to_dict() for b in self.branches],
            "count": self.count,
            "metadata": self.metadata
        }


class ExpressionEvaluator:
    """Evaluates expressions against a context."""

    # Safe operators
    OPERATORS = {
        "==": operator.eq,
        "!=": operator.ne,
        "<": operator.lt,
        "<=": operator.le,
        ">": operator.gt,
        ">=": operator.ge,
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.truediv,
        "%": operator.mod,
        "and": lambda a, b: a and b,
        "or": lambda a, b: a or b,
        "not": lambda a: not a,
        "in": lambda a, b: a in b,
        "not in": lambda a, b: a not in b,
    }

    @classmethod
    def evaluate(cls, expr: str, context: Dict[str, Any]) -> Any:
        """
        Safely evaluate an expression.

        Supports:
        - Variable access: context.user.name, ${var}
        - Comparisons: ==, !=, <, <=, >, >=
        - Boolean: and, or, not
        - Arithmetic: +, -, *, /, %
        - Membership: in, not in
        - Literals: True, False, None, numbers, strings
        """
        if not expr:
            return None

        expr = expr.strip()

        # Handle variable substitution ${var}
        expr = cls._substitute_vars(expr, context)

        # Handle dot notation (context.user.name)
        if expr.startswith("context."):
            return cls._resolve_path(expr[8:], context)

        # Handle boolean literals
        if expr.lower() == "true":
            return True
        if expr.lower() == "false":
            return False
        if expr.lower() == "none":
            return None

        # Handle numeric literals
        try:
            if "." in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass

        # Handle string literals
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]

        # Handle comparisons and logical operators
        for op_str, op_func in cls.OPERATORS.items():
            if f" {op_str} " in expr:
                parts = expr.split(f" {op_str} ", 1)
                if len(parts) == 2:
                    left = cls.evaluate(parts[0].strip(), context)
                    right = cls.evaluate(parts[1].strip(), context)
                    return op_func(left, right)

        # Handle 'not' prefix
        if expr.startswith("not "):
            return not cls.evaluate(expr[4:].strip(), context)

        # Try as variable name
        if expr in context:
            return context[expr]

        # Try as nested path
        return cls._resolve_path(expr, context)

    @classmethod
    def _substitute_vars(cls, expr: str, context: Dict[str, Any]) -> str:
        """Substitute ${var} patterns."""
        pattern = r'\$\{([^}]+)\}'

        def replace(match):
            path = match.group(1)
            value = cls._resolve_path(path, context)
            return str(value) if value is not None else ""

        return re.sub(pattern, replace, expr)

    @classmethod
    def _resolve_path(cls, path: str, context: Dict[str, Any]) -> Any:
        """Resolve a dot-notation path."""
        parts = path.split(".")
        current = context

        for part in parts:
            # Handle array indexing
            array_match = re.match(r"(\w+)\[(\d+)\]", part)
            if array_match:
                name = array_match.group(1)
                index = int(array_match.group(2))
                if isinstance(current, dict) and name in current:
                    current = current[name]
                    if isinstance(current, list) and 0 <= index < len(current):
                        current = current[index]
                    else:
                        return None
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                return None

            if current is None:
                return None

        return current


class LoopConditionEngine:
    """
    Engine for loop and conditional execution.

    Provides:
    - For-each loops
    - While/until loops
    - Repeat loops
    - If/elif/else conditions
    - Switch/case patterns
    - Try/catch/finally
    - Loop control (break, continue, retry)
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(".agent_memory/loops")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.constructs: Dict[str, ControlConstruct] = {}
        self.action_handlers: Dict[str, Callable] = {}
        self.evaluator = ExpressionEvaluator()
        self._load_constructs()

    def _load_constructs(self) -> None:
        """Load constructs from storage."""
        for file_path in self.storage_path.glob("*.json"):
            try:
                data = json.loads(file_path.read_text())
                construct = self._construct_from_dict(data)
                self.constructs[construct.id] = construct
            except Exception:
                pass

    def _construct_from_dict(self, data: Dict[str, Any]) -> ControlConstruct:
        """Reconstruct from dictionary."""
        body = []
        for item in data.get("body", []):
            if item.get("type") == "action":
                body.append(ActionBlock(
                    action_type=item["type"],
                    action_name=item.get("action", ""),
                    args=item.get("args", {}),
                    output_var=item.get("output_var"),
                    on_error=item.get("on_error", "fail")
                ))
            else:
                body.append(self._construct_from_dict(item))

        branches = [
            ConditionBranch(
                name=b["name"],
                condition=b["condition"],
                body=[
                    ActionBlock(
                        action_type=a["type"],
                        action_name=a.get("action", ""),
                        args=a.get("args", {}),
                        output_var=a.get("output_var"),
                        on_error=a.get("on_error", "fail")
                    )
                    for a in b.get("body", [])
                ],
                is_default=b.get("is_default", False)
            )
            for b in data.get("branches", [])
        ]

        return ControlConstruct(
            id=data["id"],
            name=data["name"],
            construct_type=ConstructType(data["type"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            collection_expr=data.get("collection_expr"),
            item_var=data.get("item_var"),
            index_var=data.get("index_var"),
            condition_expr=data.get("condition_expr"),
            max_iterations=data.get("max_iterations", 1000),
            body=body,
            branches=branches,
            count=data.get("count", 1),
            metadata=data.get("metadata", {})
        )

    def _save_construct(self, construct: ControlConstruct) -> None:
        """Persist construct to storage."""
        file_path = self.storage_path / f"{construct.id}.json"
        file_path.write_text(json.dumps(construct.to_dict(), indent=2, default=str))

    def register_action_handler(self, action_name: str, handler: Callable) -> None:
        """Register a handler for an action."""
        self.action_handlers[action_name] = handler

    def create_foreach(
        self,
        name: str,
        collection_expr: str,
        item_var: str,
        body: List[Dict[str, Any]],
        index_var: Optional[str] = None,
        max_iterations: int = 1000
    ) -> ControlConstruct:
        """Create a for-each loop."""
        parsed_body = self._parse_body(body)

        construct = ControlConstruct(
            id=str(uuid.uuid4()),
            name=name,
            construct_type=ConstructType.FOREACH,
            created_at=datetime.now(),
            collection_expr=collection_expr,
            item_var=item_var,
            index_var=index_var,
            max_iterations=max_iterations,
            body=parsed_body
        )

        self.constructs[construct.id] = construct
        self._save_construct(construct)
        return construct

    def create_while(
        self,
        name: str,
        condition_expr: str,
        body: List[Dict[str, Any]],
        max_iterations: int = 1000
    ) -> ControlConstruct:
        """Create a while loop."""
        parsed_body = self._parse_body(body)

        construct = ControlConstruct(
            id=str(uuid.uuid4()),
            name=name,
            construct_type=ConstructType.WHILE,
            created_at=datetime.now(),
            condition_expr=condition_expr,
            max_iterations=max_iterations,
            body=parsed_body
        )

        self.constructs[construct.id] = construct
        self._save_construct(construct)
        return construct

    def create_until(
        self,
        name: str,
        condition_expr: str,
        body: List[Dict[str, Any]],
        max_iterations: int = 1000
    ) -> ControlConstruct:
        """Create an until loop (do-until, executes at least once)."""
        parsed_body = self._parse_body(body)

        construct = ControlConstruct(
            id=str(uuid.uuid4()),
            name=name,
            construct_type=ConstructType.UNTIL,
            created_at=datetime.now(),
            condition_expr=condition_expr,
            max_iterations=max_iterations,
            body=parsed_body
        )

        self.constructs[construct.id] = construct
        self._save_construct(construct)
        return construct

    def create_repeat(
        self,
        name: str,
        count: int,
        body: List[Dict[str, Any]]
    ) -> ControlConstruct:
        """Create a repeat loop (fixed iterations)."""
        parsed_body = self._parse_body(body)

        construct = ControlConstruct(
            id=str(uuid.uuid4()),
            name=name,
            construct_type=ConstructType.REPEAT,
            created_at=datetime.now(),
            count=count,
            body=parsed_body
        )

        self.constructs[construct.id] = construct
        self._save_construct(construct)
        return construct

    def create_condition(
        self,
        name: str,
        if_expr: str,
        then_block: List[Dict[str, Any]],
        else_block: Optional[List[Dict[str, Any]]] = None,
        elif_branches: Optional[List[Dict[str, Any]]] = None
    ) -> ControlConstruct:
        """Create an if/else condition."""
        branches = [
            ConditionBranch(
                name="if",
                condition=if_expr,
                body=self._parse_body(then_block)
            )
        ]

        if elif_branches:
            for i, branch in enumerate(elif_branches):
                branches.append(ConditionBranch(
                    name=f"elif_{i}",
                    condition=branch.get("condition", "false"),
                    body=self._parse_body(branch.get("body", []))
                ))

        if else_block:
            branches.append(ConditionBranch(
                name="else",
                condition="true",
                body=self._parse_body(else_block),
                is_default=True
            ))

        construct = ControlConstruct(
            id=str(uuid.uuid4()),
            name=name,
            construct_type=ConstructType.IF,
            created_at=datetime.now(),
            branches=branches
        )

        self.constructs[construct.id] = construct
        self._save_construct(construct)
        return construct

    def create_switch(
        self,
        name: str,
        switch_expr: str,
        cases: List[Dict[str, Any]],
        default_block: Optional[List[Dict[str, Any]]] = None
    ) -> ControlConstruct:
        """Create a switch/case construct."""
        branches = []

        for case in cases:
            case_value = case.get("value")
            branches.append(ConditionBranch(
                name=f"case_{case_value}",
                condition=f"{switch_expr} == {case_value}",
                body=self._parse_body(case.get("body", []))
            ))

        if default_block:
            branches.append(ConditionBranch(
                name="default",
                condition="true",
                body=self._parse_body(default_block),
                is_default=True
            ))

        construct = ControlConstruct(
            id=str(uuid.uuid4()),
            name=name,
            construct_type=ConstructType.SWITCH,
            created_at=datetime.now(),
            condition_expr=switch_expr,
            branches=branches
        )

        self.constructs[construct.id] = construct
        self._save_construct(construct)
        return construct

    def _parse_body(self, body_data: List[Dict[str, Any]]) -> List[Union[ActionBlock, ControlConstruct]]:
        """Parse body items into ActionBlock or ControlConstruct."""
        parsed = []
        for item in body_data:
            if item.get("type") == "action":
                parsed.append(ActionBlock(
                    action_type=item["type"],
                    action_name=item.get("action", ""),
                    args=item.get("args", {}),
                    output_var=item.get("output_var"),
                    on_error=item.get("on_error", "fail")
                ))
            elif item.get("type") in ["foreach", "while", "until", "repeat", "if", "switch"]:
                # Nested construct - would need full parsing
                parsed.append(self._construct_from_dict(item))
        return parsed

    def get_construct(self, construct_id: str) -> Optional[ControlConstruct]:
        """Get construct by ID."""
        return self.constructs.get(construct_id)

    async def execute(
        self,
        construct_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute a control construct.

        Args:
            construct_id: Construct ID
            context: Execution context

        Returns:
            ExecutionResult
        """
        construct = self.get_construct(construct_id)
        if not construct:
            return ExecutionResult(
                construct_id=construct_id,
                construct_type=ConstructType.SEQUENCE,
                status=ExecutionStatus.FAILED,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                total_iterations=0,
                successful_iterations=0,
                iteration_results=[],
                branch_results=[],
                final_output=None,
                error=f"Construct '{construct_id}' not found"
            )

        ctx = context or {}

        if construct.construct_type == ConstructType.FOREACH:
            return await self._execute_foreach(construct, ctx)
        elif construct.construct_type == ConstructType.WHILE:
            return await self._execute_while(construct, ctx)
        elif construct.construct_type == ConstructType.UNTIL:
            return await self._execute_until(construct, ctx)
        elif construct.construct_type == ConstructType.REPEAT:
            return await self._execute_repeat(construct, ctx)
        elif construct.construct_type in [ConstructType.IF, ConstructType.SWITCH]:
            return await self._execute_condition(construct, ctx)
        else:
            return await self._execute_sequence(construct, ctx)

    async def _execute_foreach(
        self,
        construct: ControlConstruct,
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a for-each loop."""
        started_at = datetime.now()
        iteration_results = []

        # Get collection
        collection = self.evaluator.evaluate(construct.collection_expr or "", context)
        if not isinstance(collection, (list, tuple, set)):
            return ExecutionResult(
                construct_id=construct.id,
                construct_type=construct.construct_type,
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(),
                total_iterations=0,
                successful_iterations=0,
                iteration_results=[],
                branch_results=[],
                final_output=None,
                error=f"Collection expression did not evaluate to iterable: {construct.collection_expr}"
            )

        collection = list(collection)[:construct.max_iterations]
        successful = 0
        final_output = []

        for index, item in enumerate(collection):
            iter_start = datetime.now()

            # Update context with loop variables
            loop_context = context.copy()
            loop_context[construct.item_var] = item
            if construct.index_var:
                loop_context[construct.index_var] = index

            # Execute body
            success = True
            output = None
            error = None
            control_signal = None

            try:
                output = await self._execute_body(construct.body, loop_context)
                final_output.append(output)

                # Check for control signals
                if isinstance(output, dict):
                    if output.get("_control") == "break":
                        control_signal = LoopControl.BREAK
                    elif output.get("_control") == "continue":
                        control_signal = LoopControl.CONTINUE

            except Exception as e:
                success = False
                error = str(e)

            iter_end = datetime.now()
            duration_ms = (iter_end - iter_start).total_seconds() * 1000

            result = IterationResult(
                index=index,
                item=item,
                success=success,
                output=output,
                error=error,
                duration_ms=duration_ms,
                control_signal=control_signal
            )
            iteration_results.append(result)

            if success:
                successful += 1

            if control_signal == LoopControl.BREAK:
                break

        return ExecutionResult(
            construct_id=construct.id,
            construct_type=construct.construct_type,
            status=ExecutionStatus.COMPLETED if successful == len(collection) else ExecutionStatus.COMPLETED,
            started_at=started_at,
            completed_at=datetime.now(),
            total_iterations=len(collection),
            successful_iterations=successful,
            iteration_results=iteration_results,
            branch_results=[],
            final_output=final_output
        )

    async def _execute_while(
        self,
        construct: ControlConstruct,
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a while loop."""
        started_at = datetime.now()
        iteration_results = []
        successful = 0
        final_output = []
        iteration = 0

        while iteration < construct.max_iterations:
            # Check condition
            condition_result = self.evaluator.evaluate(construct.condition_expr or "false", context)
            if not condition_result:
                break

            iter_start = datetime.now()
            loop_context = context.copy()

            success = True
            output = None
            error = None
            control_signal = None

            try:
                output = await self._execute_body(construct.body, loop_context)
                final_output.append(output)

                # Update context with body results
                if isinstance(output, dict):
                    context.update(output.get("_context", {}))
                    if output.get("_control") == "break":
                        control_signal = LoopControl.BREAK

            except Exception as e:
                success = False
                error = str(e)

            iter_end = datetime.now()
            duration_ms = (iter_end - iter_start).total_seconds() * 1000

            result = IterationResult(
                index=iteration,
                item=None,
                success=success,
                output=output,
                error=error,
                duration_ms=duration_ms,
                control_signal=control_signal
            )
            iteration_results.append(result)

            if success:
                successful += 1

            if control_signal == LoopControl.BREAK:
                break

            iteration += 1

        return ExecutionResult(
            construct_id=construct.id,
            construct_type=construct.construct_type,
            status=ExecutionStatus.COMPLETED,
            started_at=started_at,
            completed_at=datetime.now(),
            total_iterations=iteration,
            successful_iterations=successful,
            iteration_results=iteration_results,
            branch_results=[],
            final_output=final_output
        )

    async def _execute_until(
        self,
        construct: ControlConstruct,
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute an until loop (do-until)."""
        started_at = datetime.now()
        iteration_results = []
        successful = 0
        final_output = []
        iteration = 0

        while iteration < construct.max_iterations:
            iter_start = datetime.now()
            loop_context = context.copy()

            success = True
            output = None
            error = None
            control_signal = None

            try:
                output = await self._execute_body(construct.body, loop_context)
                final_output.append(output)

                if isinstance(output, dict):
                    context.update(output.get("_context", {}))
                    if output.get("_control") == "break":
                        control_signal = LoopControl.BREAK

            except Exception as e:
                success = False
                error = str(e)

            iter_end = datetime.now()
            duration_ms = (iter_end - iter_start).total_seconds() * 1000

            result = IterationResult(
                index=iteration,
                item=None,
                success=success,
                output=output,
                error=error,
                duration_ms=duration_ms,
                control_signal=control_signal
            )
            iteration_results.append(result)

            if success:
                successful += 1

            if control_signal == LoopControl.BREAK:
                break

            # Check condition AFTER execution (do-until)
            condition_result = self.evaluator.evaluate(construct.condition_expr or "true", context)
            if condition_result:
                break

            iteration += 1

        return ExecutionResult(
            construct_id=construct.id,
            construct_type=construct.construct_type,
            status=ExecutionStatus.COMPLETED,
            started_at=started_at,
            completed_at=datetime.now(),
            total_iterations=iteration + 1,
            successful_iterations=successful,
            iteration_results=iteration_results,
            branch_results=[],
            final_output=final_output
        )

    async def _execute_repeat(
        self,
        construct: ControlConstruct,
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a repeat loop."""
        started_at = datetime.now()
        iteration_results = []
        successful = 0
        final_output = []

        for i in range(construct.count):
            iter_start = datetime.now()
            loop_context = context.copy()
            loop_context["_iteration"] = i

            success = True
            output = None
            error = None

            try:
                output = await self._execute_body(construct.body, loop_context)
                final_output.append(output)
            except Exception as e:
                success = False
                error = str(e)

            iter_end = datetime.now()
            duration_ms = (iter_end - iter_start).total_seconds() * 1000

            result = IterationResult(
                index=i,
                item=i,
                success=success,
                output=output,
                error=error,
                duration_ms=duration_ms
            )
            iteration_results.append(result)

            if success:
                successful += 1

        return ExecutionResult(
            construct_id=construct.id,
            construct_type=construct.construct_type,
            status=ExecutionStatus.COMPLETED,
            started_at=started_at,
            completed_at=datetime.now(),
            total_iterations=construct.count,
            successful_iterations=successful,
            iteration_results=iteration_results,
            branch_results=[],
            final_output=final_output
        )

    async def _execute_condition(
        self,
        construct: ControlConstruct,
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a conditional (if/switch)."""
        started_at = datetime.now()
        branch_results = []
        final_output = None
        executed_branch = None

        for branch in construct.branches:
            condition_result = self.evaluator.evaluate(branch.condition, context)

            branch_result = BranchResult(
                branch_name=branch.name,
                condition=branch.condition,
                evaluated_to=bool(condition_result),
                executed=False
            )

            if condition_result and executed_branch is None:
                branch_result.executed = True
                executed_branch = branch

                try:
                    final_output = await self._execute_body(branch.body, context)
                    branch_result.output = final_output
                except Exception as e:
                    branch_result.error = str(e)

            branch_results.append(branch_result)

        return ExecutionResult(
            construct_id=construct.id,
            construct_type=construct.construct_type,
            status=ExecutionStatus.COMPLETED,
            started_at=started_at,
            completed_at=datetime.now(),
            total_iterations=1,
            successful_iterations=1 if executed_branch else 0,
            iteration_results=[],
            branch_results=branch_results,
            final_output=final_output
        )

    async def _execute_sequence(
        self,
        construct: ControlConstruct,
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a sequence of actions."""
        started_at = datetime.now()
        outputs = []

        for item in construct.body:
            output = await self._execute_body([item], context)
            outputs.append(output)

        return ExecutionResult(
            construct_id=construct.id,
            construct_type=construct.construct_type,
            status=ExecutionStatus.COMPLETED,
            started_at=started_at,
            completed_at=datetime.now(),
            total_iterations=len(construct.body),
            successful_iterations=len(construct.body),
            iteration_results=[],
            branch_results=[],
            final_output=outputs
        )

    async def _execute_body(
        self,
        body: List[Union[ActionBlock, ControlConstruct]],
        context: Dict[str, Any]
    ) -> Any:
        """Execute a body of actions/constructs."""
        outputs = []

        for item in body:
            if isinstance(item, ActionBlock):
                # Substitute variables in args
                resolved_args = {}
                for key, value in item.args.items():
                    if isinstance(value, str):
                        resolved_args[key] = self.evaluator._substitute_vars(value, context)
                    else:
                        resolved_args[key] = value

                # Execute action
                if item.action_name in self.action_handlers:
                    handler = self.action_handlers[item.action_name]
                    try:
                        result = await handler(resolved_args, context)
                        if item.output_var:
                            context[item.output_var] = result
                        outputs.append(result)
                    except Exception as e:
                        if item.on_error == "fail":
                            raise
                        elif item.on_error == "skip":
                            outputs.append(None)
                        elif item.on_error == "retry":
                            # Simple retry
                            try:
                                result = await handler(resolved_args, context)
                                outputs.append(result)
                            except Exception:
                                raise
                else:
                    outputs.append({"action": item.action_name, "args": resolved_args, "simulated": True})

            elif isinstance(item, ControlConstruct):
                # Nested construct
                result = await self.execute(item.id, context)
                outputs.append(result.final_output)

        return outputs[0] if len(outputs) == 1 else outputs
