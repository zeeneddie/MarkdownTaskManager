"""
Taskchain Orchestrator Service - Week 108 (AO-M-1)

Orchestrate linked subtasks that call each other sequentially.

Based on Gregor Riegler's Augmented Coding Pattern Language:
- Tasks are linked in chains
- Output of one task becomes input for the next
- Automatic error handling and retry
- Progress tracking across chain

Key Features:
- Sequential task execution with dependencies
- Result chaining (output → input)
- Parallel execution for independent tasks
- Error handling with retry and fallback
- Chain visualization and monitoring
"""

import asyncio
import json
import hashlib
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Awaitable, Union
from concurrent.futures import ThreadPoolExecutor


class TaskStatus(str, Enum):
    """Status of a task in the chain."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    WAITING = "waiting"  # Waiting for dependencies


class ChainStatus(str, Enum):
    """Status of the entire chain."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class TaskResult:
    """
    Result of a task execution.

    Contains the output data and execution metadata.
    """
    task_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
        }


@dataclass
class ChainTask:
    """
    A task in the chain.

    Tasks can have dependencies on other tasks,
    and their output can be passed to dependent tasks.
    """
    id: str
    name: str
    handler: Union[Callable, str]  # Callable or handler name
    dependencies: List[str] = field(default_factory=list)
    input_mapping: Dict[str, str] = field(default_factory=dict)  # Maps dependency outputs to inputs
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[TaskResult] = None
    max_retries: int = 3
    retry_delay_ms: int = 1000
    timeout_ms: int = 60000
    skip_on_failure: bool = False  # Skip if dependency fails
    parallel_group: Optional[str] = None  # Tasks in same group run in parallel
    metadata: Dict[str, Any] = field(default_factory=dict)

    def can_run(self, completed_tasks: Dict[str, TaskResult]) -> bool:
        """Check if all dependencies are satisfied."""
        if not self.dependencies:
            return True

        for dep_id in self.dependencies:
            if dep_id not in completed_tasks:
                return False
            if not completed_tasks[dep_id].success and not self.skip_on_failure:
                return False

        return True

    def get_input(self, completed_tasks: Dict[str, TaskResult]) -> Dict[str, Any]:
        """Build input from dependency outputs."""
        if not self.input_mapping:
            # Default: pass all dependency outputs
            return {
                dep_id: completed_tasks[dep_id].output
                for dep_id in self.dependencies
                if dep_id in completed_tasks
            }

        # Custom mapping
        result = {}
        for input_key, source in self.input_mapping.items():
            if '.' in source:
                # Format: "task_id.output_key"
                task_id, output_key = source.split('.', 1)
                if task_id in completed_tasks:
                    output = completed_tasks[task_id].output
                    if isinstance(output, dict) and output_key in output:
                        result[input_key] = output[output_key]
            else:
                # Direct task output
                if source in completed_tasks:
                    result[input_key] = completed_tasks[source].output

        return result


@dataclass
class TaskChain:
    """
    A chain of linked tasks.

    Manages the execution order and result passing
    between tasks in the chain.
    """
    id: str
    name: str
    tasks: List[ChainTask] = field(default_factory=list)
    status: ChainStatus = ChainStatus.IDLE
    results: Dict[str, TaskResult] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def add_task(
        self,
        name: str,
        handler: Union[Callable, str],
        dependencies: Optional[List[str]] = None,
        input_mapping: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> ChainTask:
        """Add a task to the chain."""
        task_id = hashlib.md5(
            f"{self.id}:{name}:{len(self.tasks)}".encode()
        ).hexdigest()[:8]

        task = ChainTask(
            id=task_id,
            name=name,
            handler=handler,
            dependencies=dependencies or [],
            input_mapping=input_mapping or {},
            **kwargs,
        )

        self.tasks.append(task)
        return task

    def get_task(self, task_id: str) -> Optional[ChainTask]:
        """Get a task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_runnable_tasks(self) -> List[ChainTask]:
        """Get tasks that are ready to run."""
        runnable = []
        for task in self.tasks:
            if task.status == TaskStatus.PENDING and task.can_run(self.results):
                runnable.append(task)
        return runnable

    def get_progress(self) -> Dict[str, Any]:
        """Get chain execution progress."""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)
        running = sum(1 for t in self.tasks if t.status == TaskStatus.RUNNING)

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": total - completed - failed - running,
            "percent": (completed / total * 100) if total else 0,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "status": t.status.value,
                    "dependencies": t.dependencies,
                }
                for t in self.tasks
            ],
            "results": {k: v.to_dict() for k, v in self.results.items()},
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "context": self.context,
            "error": self.error,
            "progress": self.get_progress(),
        }


class TaskchainService:
    """
    Taskchain Orchestrator Service.

    Manages execution of linked task chains with:
    - Dependency resolution
    - Result chaining
    - Parallel execution
    - Error handling and retry

    Usage:
        service = TaskchainService()

        # Create a chain
        chain = service.create_chain("my_process")

        # Add tasks with dependencies
        task1 = chain.add_task("fetch_data", fetch_handler)
        task2 = chain.add_task("transform", transform_handler, dependencies=[task1.id])
        task3 = chain.add_task("save", save_handler, dependencies=[task2.id])

        # Execute chain
        result = await service.execute(chain)
    """

    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        max_parallel: int = 5,
        default_timeout_ms: int = 60000,
        default_retries: int = 3,
    ):
        """
        Initialize Taskchain Service.

        Args:
            storage_dir: Directory for chain storage
            max_parallel: Maximum parallel task executions
            default_timeout_ms: Default task timeout
            default_retries: Default retry count
        """
        self.storage_dir = Path(storage_dir) if storage_dir else Path(".taskchains")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.max_parallel = max_parallel
        self.default_timeout_ms = default_timeout_ms
        self.default_retries = default_retries

        # Handler registry
        self._handlers: Dict[str, Callable] = {}

        # Chain cache
        self._chains: Dict[str, TaskChain] = {}

        # Execution hooks
        self._hooks: Dict[str, List[Callable]] = {
            "on_task_start": [],
            "on_task_complete": [],
            "on_task_error": [],
            "on_chain_start": [],
            "on_chain_complete": [],
        }

    # === Handler Registration ===

    def register_handler(
        self,
        name: str,
        handler: Callable,
    ) -> None:
        """
        Register a named handler.

        Args:
            name: Handler name for reference
            handler: The handler function
        """
        self._handlers[name] = handler

    def get_handler(self, name: str) -> Optional[Callable]:
        """Get a registered handler by name."""
        return self._handlers.get(name)

    # === Chain Creation ===

    def create_chain(
        self,
        name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskChain:
        """
        Create a new task chain.

        Args:
            name: Chain name
            context: Initial context data

        Returns:
            The created TaskChain
        """
        chain_id = hashlib.md5(
            f"{name}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:12]

        chain = TaskChain(
            id=chain_id,
            name=name,
            context=context or {},
        )

        self._chains[chain_id] = chain
        return chain

    def get_chain(self, chain_id: str) -> Optional[TaskChain]:
        """Get a chain by ID."""
        return self._chains.get(chain_id)

    # === Chain Execution ===

    async def execute(
        self,
        chain: TaskChain,
        initial_input: Optional[Dict[str, Any]] = None,
    ) -> TaskChain:
        """
        Execute a task chain.

        Args:
            chain: The chain to execute
            initial_input: Initial input for first tasks

        Returns:
            The executed chain with results
        """
        chain.status = ChainStatus.RUNNING
        chain.started_at = datetime.now(timezone.utc)
        chain.context.update(initial_input or {})

        await self._fire_hook("on_chain_start", chain)

        try:
            await self._execute_chain(chain)

            # Determine final status
            failed_tasks = [t for t in chain.tasks if t.status == TaskStatus.FAILED]
            if failed_tasks:
                chain.status = ChainStatus.FAILED
                chain.error = f"{len(failed_tasks)} tasks failed"
            else:
                chain.status = ChainStatus.COMPLETED

        except Exception as e:
            chain.status = ChainStatus.FAILED
            chain.error = str(e)

        chain.completed_at = datetime.now(timezone.utc)
        await self._fire_hook("on_chain_complete", chain)

        self._save_chain(chain)
        return chain

    async def _execute_chain(self, chain: TaskChain) -> None:
        """Execute all tasks in the chain."""
        while True:
            # Get runnable tasks
            runnable = chain.get_runnable_tasks()

            if not runnable:
                # Check if all tasks are done
                pending = [t for t in chain.tasks if t.status == TaskStatus.PENDING]
                if not pending:
                    break

                # Some tasks pending but not runnable - likely dependency failure
                for task in pending:
                    task.status = TaskStatus.SKIPPED
                break

            # Group by parallel group
            groups: Dict[Optional[str], List[ChainTask]] = {}
            for task in runnable:
                group = task.parallel_group
                if group not in groups:
                    groups[group] = []
                groups[group].append(task)

            # Execute each group
            for group_tasks in groups.values():
                if len(group_tasks) == 1:
                    # Single task - execute directly
                    await self._execute_task(chain, group_tasks[0])
                else:
                    # Multiple tasks - execute in parallel
                    await self._execute_parallel(chain, group_tasks)

    async def _execute_task(
        self,
        chain: TaskChain,
        task: ChainTask,
    ) -> TaskResult:
        """Execute a single task."""
        task.status = TaskStatus.RUNNING
        await self._fire_hook("on_task_start", chain, task)

        result = TaskResult(
            task_id=task.id,
            success=False,
            started_at=datetime.now(timezone.utc),
        )

        # Get input from dependencies
        input_data = task.get_input(chain.results)
        input_data.update(chain.context)

        # Get handler
        handler = task.handler
        if isinstance(handler, str):
            handler = self._handlers.get(handler)
            if not handler:
                result.error = f"Handler not found: {task.handler}"
                task.status = TaskStatus.FAILED
                task.result = result
                chain.results[task.id] = result
                await self._fire_hook("on_task_error", chain, task, result)
                return result

        # Execute with retry
        for attempt in range(task.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(handler):
                    output = await asyncio.wait_for(
                        handler(input_data),
                        timeout=task.timeout_ms / 1000,
                    )
                else:
                    # Run sync handler in thread pool
                    loop = asyncio.get_event_loop()
                    output = await loop.run_in_executor(
                        None,
                        lambda: handler(input_data),
                    )

                result.success = True
                result.output = output
                result.retry_count = attempt
                break

            except asyncio.TimeoutError:
                result.error = f"Task timed out after {task.timeout_ms}ms"
                result.retry_count = attempt

            except Exception as e:
                result.error = str(e)
                result.retry_count = attempt

            # Retry delay
            if attempt < task.max_retries:
                await asyncio.sleep(task.retry_delay_ms / 1000)

        result.completed_at = datetime.now(timezone.utc)
        if result.started_at:
            result.duration_ms = int(
                (result.completed_at - result.started_at).total_seconds() * 1000
            )

        # Update task status
        task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
        task.result = result
        chain.results[task.id] = result

        if result.success:
            await self._fire_hook("on_task_complete", chain, task, result)
        else:
            await self._fire_hook("on_task_error", chain, task, result)

        return result

    async def _execute_parallel(
        self,
        chain: TaskChain,
        tasks: List[ChainTask],
    ) -> List[TaskResult]:
        """Execute multiple tasks in parallel."""
        # Limit concurrency
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def run_with_semaphore(task: ChainTask) -> TaskResult:
            async with semaphore:
                return await self._execute_task(chain, task)

        results = await asyncio.gather(
            *[run_with_semaphore(task) for task in tasks],
            return_exceptions=True,
        )

        # Handle any exceptions
        task_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task = tasks[i]
                error_result = TaskResult(
                    task_id=task.id,
                    success=False,
                    error=str(result),
                )
                task.status = TaskStatus.FAILED
                task.result = error_result
                chain.results[task.id] = error_result
                task_results.append(error_result)
            else:
                task_results.append(result)

        return task_results

    # === Chain Control ===

    async def cancel(self, chain: TaskChain) -> None:
        """Cancel a running chain."""
        chain.status = ChainStatus.CANCELLED
        for task in chain.tasks:
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                task.status = TaskStatus.CANCELLED

    async def pause(self, chain: TaskChain) -> None:
        """Pause a running chain."""
        chain.status = ChainStatus.PAUSED

    async def resume(self, chain: TaskChain) -> TaskChain:
        """Resume a paused chain."""
        if chain.status != ChainStatus.PAUSED:
            raise ValueError("Can only resume paused chains")

        chain.status = ChainStatus.RUNNING
        return await self.execute(chain)

    # === Convenience Methods ===

    def build_linear_chain(
        self,
        name: str,
        tasks: List[Dict[str, Any]],
    ) -> TaskChain:
        """
        Build a simple linear chain where each task depends on the previous.

        Args:
            name: Chain name
            tasks: List of task configs with 'name' and 'handler'

        Returns:
            The created chain
        """
        chain = self.create_chain(name)
        prev_id = None

        for task_config in tasks:
            dependencies = [prev_id] if prev_id else []
            task = chain.add_task(
                name=task_config["name"],
                handler=task_config["handler"],
                dependencies=dependencies,
                **{k: v for k, v in task_config.items() if k not in ["name", "handler"]},
            )
            prev_id = task.id

        return chain

    def build_parallel_chain(
        self,
        name: str,
        parallel_tasks: List[Dict[str, Any]],
        final_task: Optional[Dict[str, Any]] = None,
    ) -> TaskChain:
        """
        Build a chain with parallel tasks and optional final aggregation.

        Args:
            name: Chain name
            parallel_tasks: List of tasks to run in parallel
            final_task: Optional task that depends on all parallel tasks

        Returns:
            The created chain
        """
        chain = self.create_chain(name)
        parallel_ids = []

        # Add parallel tasks
        for task_config in parallel_tasks:
            task = chain.add_task(
                name=task_config["name"],
                handler=task_config["handler"],
                parallel_group="parallel",
                **{k: v for k, v in task_config.items() if k not in ["name", "handler"]},
            )
            parallel_ids.append(task.id)

        # Add final aggregation task
        if final_task:
            chain.add_task(
                name=final_task["name"],
                handler=final_task["handler"],
                dependencies=parallel_ids,
                **{k: v for k, v in final_task.items() if k not in ["name", "handler"]},
            )

        return chain

    # === Persistence ===

    def _save_chain(self, chain: TaskChain) -> None:
        """Save chain to file."""
        file_path = self.storage_dir / f"{chain.id}.json"
        with open(file_path, 'w') as f:
            json.dump(chain.to_dict(), f, indent=2)

    def load_chain(self, chain_id: str) -> Optional[TaskChain]:
        """Load chain from file."""
        file_path = self.storage_dir / f"{chain_id}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            # Note: Full deserialization would require handler registration
            return data
        except Exception:
            return None

    # === Hooks ===

    def register_hook(
        self,
        event: str,
        callback: Callable,
    ) -> None:
        """Register an event hook."""
        if event in self._hooks:
            self._hooks[event].append(callback)

    async def _fire_hook(
        self,
        event: str,
        *args,
    ) -> None:
        """Fire all hooks for an event."""
        for callback in self._hooks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args)
                else:
                    callback(*args)
            except Exception:
                pass  # Don't let hook errors break execution

    # === Visualization ===

    def format_chain(self, chain: TaskChain) -> str:
        """Format chain as visual text."""
        lines = [f"# Task Chain: {chain.name}"]
        lines.append(f"Status: {chain.status.value}")
        lines.append("")

        progress = chain.get_progress()
        lines.append(f"Progress: {progress['completed']}/{progress['total']} ({progress['percent']:.1f}%)")
        lines.append("")

        lines.append("## Tasks:")
        for task in chain.tasks:
            status_emoji = {
                TaskStatus.PENDING: "",
                TaskStatus.RUNNING: "",
                TaskStatus.COMPLETED: "",
                TaskStatus.FAILED: "",
                TaskStatus.SKIPPED: "",
                TaskStatus.CANCELLED: "",
            }.get(task.status, "")

            deps = f" (depends: {task.dependencies})" if task.dependencies else ""
            lines.append(f"  {status_emoji} {task.name}{deps}")

            if task.result and task.result.error:
                lines.append(f"      Error: {task.result.error}")

        return '\n'.join(lines)
