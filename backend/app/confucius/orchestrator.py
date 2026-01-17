"""
Confucius Code Agent Orchestrator.

Main orchestrator implementing Confucius SDK patterns for MarQed.
Manages hierarchical memory, agent extensions, quality gates,
and cross-session learning.

Based on Meta/Harvard CCA Research (December 2025).
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import asyncio
import logging
import uuid

from .config import ConfuciusConfig
from .memory.types import (
    SessionMemory,
    EntryMemory,
    RunnableMemory,
    RelevantMemory,
)
from .extensions.base import BaseAgentExtension, ExtensionResult

logger = logging.getLogger(__name__)


class OrchestratorState(Enum):
    """Current state of the orchestrator."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    PLANNING = "planning"
    ROUTING = "routing"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    ITERATING = "iterating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExecutionResult:
    """Result of orchestrated execution."""
    success: bool
    output: Dict[str, Any]
    quality_score: float
    iterations_used: int
    extensions_called: List[str]
    memory_state: Dict[str, Any] = field(default_factory=dict)
    notes_generated: List[Dict[str, Any]] = field(default_factory=list)
    execution_time_ms: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)
    entry_id: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "quality_score": self.quality_score,
            "iterations_used": self.iterations_used,
            "extensions_called": self.extensions_called,
            "execution_time_ms": self.execution_time_ms,
            "entry_id": self.entry_id,
            "error": self.error,
        }


@dataclass
class StreamEvent:
    """Event for SSE streaming."""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_sse(self) -> str:
        """Convert to SSE format."""
        import json
        return f"event: {self.type}\ndata: {json.dumps(self.data)}\n\n"


class HierarchicalMemoryManager:
    """
    Manages hierarchical working memory.

    Three scopes:
    1. session_scope: Cross-task insights (permanent)
    2. entry_scope: Per-task summaries (30 days)
    3. runnable_scope: Tool execution outputs (7 days)
    """

    def __init__(self, config: ConfuciusConfig):
        self.config = config
        self._current_session: Optional[SessionMemory] = None
        self._entries: Dict[str, EntryMemory] = {}
        self._runnables: Dict[str, RunnableMemory] = {}
        # TODO: Add repository for persistence

    async def load_session(self, session_id: str, project_id: str) -> SessionMemory:
        """Load existing session or create new one."""
        # TODO: Load from database
        if self._current_session and self._current_session.session_id == session_id:
            return self._current_session

        self._current_session = SessionMemory(
            session_id=session_id,
            project_id=project_id,
        )
        return self._current_session

    async def create_session(self, project_id: str) -> SessionMemory:
        """Create a new session."""
        self._current_session = SessionMemory.create(project_id)
        return self._current_session

    async def create_entry(self, task: str, context: Dict[str, Any]) -> str:
        """Create a new entry for a task."""
        if not self._current_session:
            raise ValueError("No active session. Call load_session() first.")

        entry = EntryMemory.create(
            session_id=self._current_session.session_id,
            task=task,
        )
        entry.context_summary = self._summarize_context(context)
        self._entries[entry.entry_id] = entry

        logger.debug(f"Created entry {entry.entry_id} for task: {task[:50]}...")
        return entry.entry_id

    async def update_runnable(
        self,
        entry_id: str,
        extension_name: str,
        output: Dict[str, Any],
        duration_ms: int,
    ) -> str:
        """Record runnable execution to memory."""
        runnable = RunnableMemory.create(entry_id, extension_name)
        runnable.complete(
            output_data=output,
            output_summary=self._summarize_output(output),
            duration_ms=duration_ms,
            success=not output.get("error"),
            error_message=output.get("error"),
        )

        self._runnables[runnable.runnable_id] = runnable

        # Link to entry
        if entry_id in self._entries:
            self._entries[entry_id].add_runnable(runnable.runnable_id)

        return runnable.runnable_id

    async def complete_entry(
        self,
        entry_id: str,
        quality_score: float,
        results_summary: str,
        extensions_called: List[str],
        iterations_used: int,
    ) -> None:
        """Mark entry as complete."""
        if entry_id in self._entries:
            entry = self._entries[entry_id]
            entry.complete(quality_score, results_summary)
            entry.extensions_called = extensions_called
            entry.iterations_used = iterations_used

    async def get_relevant(
        self,
        task_context: Dict[str, Any],
        extensions: List[str],
    ) -> RelevantMemory:
        """Get relevant memory for current task."""
        relevant = RelevantMemory()

        if self._current_session:
            # Get session-level insights
            relevant.session_insights = self._current_session.insights[
                -self.config.memory.max_session_insights:
            ]
            relevant.session_patterns = self._current_session.patterns[
                -self.config.memory.max_session_patterns:
            ]

            # TODO: Find related entries by semantic similarity
            # For now, return recent entries
            recent_entries = sorted(
                self._entries.values(),
                key=lambda e: e.created_at,
                reverse=True,
            )[:self.config.memory.max_relevant_entries]
            relevant.related_entries = recent_entries

        return relevant

    async def add_insight(self, insight: Dict[str, Any]) -> None:
        """Add insight to session memory."""
        if self._current_session:
            self._current_session.add_insight(insight)

    async def add_pattern(self, pattern: Dict[str, Any]) -> None:
        """Add pattern to session memory."""
        if self._current_session:
            self._current_session.add_pattern(pattern)

    def get_state(self) -> Dict[str, Any]:
        """Get current memory state for debugging."""
        return {
            "session_id": self._current_session.session_id if self._current_session else None,
            "entries_count": len(self._entries),
            "runnables_count": len(self._runnables),
            "insights_count": len(self._current_session.insights) if self._current_session else 0,
            "patterns_count": len(self._current_session.patterns) if self._current_session else 0,
        }

    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """Create summary of context for storage."""
        # TODO: Use LLM for intelligent summarization
        return str(context)[:500]

    def _summarize_output(self, output: Dict[str, Any]) -> str:
        """Create summary of output for storage."""
        return str(output)[:500]


class ExtensionRouter:
    """Routes tasks to appropriate extensions based on matching."""

    def __init__(self, config: ConfuciusConfig):
        self.config = config
        self._extensions: Dict[str, BaseAgentExtension] = {}

    def register(self, extension: BaseAgentExtension) -> None:
        """Register an extension."""
        self._extensions[extension.name] = extension
        logger.info(f"Registered extension: {extension.name}")

    def get_extension(self, name: str) -> Optional[BaseAgentExtension]:
        """Get extension by name."""
        return self._extensions.get(name)

    def list_extensions(self) -> List[str]:
        """List all registered extensions."""
        return list(self._extensions.keys())

    async def route(
        self,
        task: str,
        context: Dict[str, Any],
        requested_extensions: Optional[List[str]] = None,
    ) -> List[BaseAgentExtension]:
        """
        Route task to appropriate extensions.

        Args:
            task: Task description
            context: Context dictionary
            requested_extensions: If specified, only consider these extensions

        Returns:
            List of extensions to invoke, sorted by priority
        """
        candidates = []

        extensions_to_check = (
            [self._extensions[name] for name in requested_extensions if name in self._extensions]
            if requested_extensions
            else list(self._extensions.values())
        )

        for extension in extensions_to_check:
            score = extension.matches_task(task, context)
            if score >= self.config.extensions.min_match_score:
                candidates.append((extension, score))

        # Sort by score (descending) then priority (descending)
        candidates.sort(key=lambda x: (x[1], x[0].priority), reverse=True)

        # Limit to max extensions
        selected = [ext for ext, score in candidates[:self.config.extensions.max_extensions_per_task]]

        logger.debug(f"Routed task to extensions: {[e.name for e in selected]}")
        return selected


class ConfuciusOrchestrator:
    """
    Main orchestrator implementing Confucius SDK patterns for MarQed.

    Manages:
    - Hierarchical working memory (session/entry/runnable scopes)
    - Agent extensions with lifecycle hooks
    - Quality gates and iteration control
    - Cross-session learning via note-taking

    Example usage:
    ```python
    config = ConfuciusConfig.default()
    orchestrator = ConfuciusOrchestrator(config)

    # Register extensions
    orchestrator.register_extension(FelixExtension(felix_service))
    orchestrator.register_extension(QuinnExtension(quinn_service))

    # Execute task
    result = await orchestrator.execute(
        task="Analyze architecture of legacy ASP codebase",
        context={"files": [...], "project_id": "..."},
        project_id="my-project",
    )
    ```
    """

    def __init__(self, config: Optional[ConfuciusConfig] = None):
        self.config = config or ConfuciusConfig.default()
        self.memory = HierarchicalMemoryManager(self.config)
        self.router = ExtensionRouter(self.config)
        self.state = OrchestratorState.IDLE
        self._execution_start: Optional[datetime] = None

    def register_extension(self, extension: BaseAgentExtension) -> None:
        """Register an agent extension with the orchestrator."""
        extension.set_orchestrator(self)
        self.router.register(extension)

    def get_extension(self, name: str) -> Optional[BaseAgentExtension]:
        """Get extension by name."""
        return self.router.get_extension(name)

    def list_extensions(self) -> List[str]:
        """List all registered extensions."""
        return self.router.list_extensions()

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        project_id: str,
        session_id: Optional[str] = None,
        requested_extensions: Optional[List[str]] = None,
    ) -> ExecutionResult:
        """
        Execute a task through the orchestrated pipeline.

        Implements the PIV (Plan-Implement-Validate) loop:
        1. Route task to appropriate extension(s)
        2. Load relevant memory and compress context
        3. Execute extension(s) with lifecycle hooks
        4. Evaluate quality and iterate if needed
        5. Generate notes for cross-session learning

        Args:
            task: Task description
            context: Context dictionary
            project_id: Project identifier
            session_id: Optional session ID to resume
            requested_extensions: Optional list of specific extensions to use

        Returns:
            ExecutionResult with output and metadata
        """
        self._execution_start = datetime.now(timezone.utc)
        self.state = OrchestratorState.INITIALIZING

        try:
            # Initialize session
            if session_id:
                await self.memory.load_session(session_id, project_id)
            else:
                await self.memory.create_session(project_id)

            # Create entry for this task
            entry_id = await self.memory.create_entry(task, context)

            # Route to extensions
            self.state = OrchestratorState.ROUTING
            extensions = await self.router.route(task, context, requested_extensions)

            if not extensions:
                logger.warning(f"No extensions matched task: {task[:50]}...")
                return self._create_error_result(
                    "No extensions matched the task",
                    entry_id=entry_id,
                )

            # Execute with iteration loop
            iteration = 0
            results: Dict[str, Any] = {}
            quality_score = 0.0

            while iteration < self.config.quality.max_iterations:
                iteration += 1
                self.state = OrchestratorState.EXECUTING

                logger.info(f"Executing iteration {iteration} with extensions: {[e.name for e in extensions]}")

                # Prepare context with relevant memory
                enriched_context = await self._prepare_context(context, extensions)

                # Execute extensions
                results = await self._execute_extensions(
                    extensions, task, enriched_context, entry_id
                )

                # Evaluate quality
                self.state = OrchestratorState.EVALUATING
                quality_score = self._evaluate_quality(results, extensions)

                if quality_score >= self.config.quality.default_threshold:
                    break

                # Prepare for retry if needed
                if iteration < self.config.quality.max_iterations:
                    self.state = OrchestratorState.ITERATING
                    context = self._prepare_retry_context(context, results, quality_score)

            # Complete entry
            self.state = OrchestratorState.COMPLETED
            await self.memory.complete_entry(
                entry_id=entry_id,
                quality_score=quality_score,
                results_summary=str(results)[:500],
                extensions_called=[e.name for e in extensions],
                iterations_used=iteration,
            )

            # Generate notes for learning (if quality is good enough)
            notes = []
            if self.config.note_taking.enabled and quality_score >= self.config.note_taking.auto_record_threshold:
                notes = await self._generate_notes(task, results, quality_score)

            return ExecutionResult(
                success=quality_score >= self.config.quality.critical_threshold,
                output=results,
                quality_score=quality_score,
                iterations_used=iteration,
                extensions_called=[e.name for e in extensions],
                memory_state=self.memory.get_state(),
                notes_generated=notes,
                execution_time_ms=self._get_execution_time_ms(),
                entry_id=entry_id,
            )

        except Exception as e:
            logger.error(f"Orchestrator execution failed: {e}")
            self.state = OrchestratorState.FAILED
            return self._create_error_result(str(e))

    async def execute_streaming(
        self,
        task: str,
        context: Dict[str, Any],
        project_id: str,
        session_id: Optional[str] = None,
        requested_extensions: Optional[List[str]] = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Execute with SSE streaming for real-time progress updates.

        Yields StreamEvent objects that can be converted to SSE format.
        """
        self._execution_start = datetime.now(timezone.utc)

        yield StreamEvent("state", {"state": "initializing"})

        try:
            # Initialize session
            if session_id:
                await self.memory.load_session(session_id, project_id)
            else:
                await self.memory.create_session(project_id)

            entry_id = await self.memory.create_entry(task, context)
            yield StreamEvent("entry_created", {"entry_id": entry_id})

            # Route to extensions
            yield StreamEvent("state", {"state": "routing"})
            extensions = await self.router.route(task, context, requested_extensions)

            if not extensions:
                yield StreamEvent("error", {"message": "No extensions matched"})
                return

            yield StreamEvent("extensions_selected", {"extensions": [e.name for e in extensions]})

            # Execute
            iteration = 0
            results: Dict[str, Any] = {}
            quality_score = 0.0

            while iteration < self.config.quality.max_iterations:
                iteration += 1
                yield StreamEvent("iteration_start", {"iteration": iteration})

                enriched_context = await self._prepare_context(context, extensions)

                for extension in extensions:
                    yield StreamEvent("extension_start", {"extension": extension.name})

                    result = await extension.run_full_lifecycle(task, enriched_context, entry_id)
                    results[extension.name] = result.to_dict()

                    yield StreamEvent("extension_complete", {
                        "extension": extension.name,
                        "success": result.success,
                        "duration_ms": result.duration_ms,
                    })

                    # Update memory
                    await self.memory.update_runnable(
                        entry_id, extension.name, result.output, result.duration_ms
                    )

                quality_score = self._evaluate_quality(results, extensions)
                yield StreamEvent("quality_evaluated", {
                    "score": quality_score,
                    "passes": quality_score >= self.config.quality.default_threshold,
                })

                if quality_score >= self.config.quality.default_threshold:
                    break

            # Complete
            await self.memory.complete_entry(
                entry_id, quality_score, str(results)[:500],
                [e.name for e in extensions], iteration
            )

            yield StreamEvent("complete", {
                "success": quality_score >= self.config.quality.critical_threshold,
                "quality_score": quality_score,
                "iterations_used": iteration,
                "entry_id": entry_id,
            })

        except Exception as e:
            yield StreamEvent("error", {"message": str(e)})

    async def _prepare_context(
        self,
        context: Dict[str, Any],
        extensions: List[BaseAgentExtension],
    ) -> Dict[str, Any]:
        """Prepare context with relevant memory."""
        # Get relevant memory
        relevant = await self.memory.get_relevant(
            task_context=context,
            extensions=[e.name for e in extensions],
        )

        # Merge with context
        enriched = {
            **context,
            "memory": relevant.to_context() if not relevant.is_empty() else {},
        }

        # TODO: Apply compression if needed
        return enriched

    async def _execute_extensions(
        self,
        extensions: List[BaseAgentExtension],
        task: str,
        context: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """Execute extensions (sequentially or in parallel)."""
        results = {}

        if self.config.extensions.enable_parallel_execution:
            # Parallel execution
            tasks = [
                self._execute_single_extension(ext, task, context, entry_id)
                for ext in extensions
            ]
            extension_results = await asyncio.gather(*tasks, return_exceptions=True)

            for ext, result in zip(extensions, extension_results):
                if isinstance(result, Exception):
                    results[ext.name] = {"error": str(result)}
                else:
                    results[ext.name] = result.to_dict()
        else:
            # Sequential execution
            for extension in extensions:
                result = await self._execute_single_extension(extension, task, context, entry_id)
                results[extension.name] = result.to_dict()

        return results

    async def _execute_single_extension(
        self,
        extension: BaseAgentExtension,
        task: str,
        context: Dict[str, Any],
        entry_id: str,
    ) -> ExtensionResult:
        """Execute a single extension with timeout."""
        try:
            timeout = min(
                extension.metadata.timeout_seconds,
                self.config.extensions.max_timeout_seconds,
            )

            async with asyncio.timeout(timeout):
                result = await extension.run_full_lifecycle(task, context, entry_id)

            # Record to memory
            await self.memory.update_runnable(
                entry_id,
                extension.name,
                result.output,
                result.duration_ms,
            )

            return result

        except asyncio.TimeoutError:
            logger.warning(f"Extension {extension.name} timed out")
            return ExtensionResult(
                extension_name=extension.name,
                success=False,
                output=extension.get_partial(),
                duration_ms=extension.metadata.timeout_seconds * 1000,
                error="timeout",
            )

    def _evaluate_quality(
        self,
        results: Dict[str, Any],
        extensions: List[BaseAgentExtension],
    ) -> float:
        """
        Evaluate quality of results.

        TODO: Implement domain-specific quality rules.
        For now, return a simple heuristic based on success rate.
        """
        if not results:
            return 0.0

        success_count = sum(
            1 for r in results.values()
            if isinstance(r, dict) and r.get("success", False)
        )

        # Basic quality score based on success rate
        return success_count / len(results) if results else 0.0

    def _prepare_retry_context(
        self,
        original_context: Dict[str, Any],
        results: Dict[str, Any],
        quality_score: float,
    ) -> Dict[str, Any]:
        """Prepare context for retry iteration."""
        return {
            **original_context,
            "_retry": True,
            "_previous_results": results,
            "_previous_quality_score": quality_score,
            "_improvement_hint": f"Previous attempt scored {quality_score:.2f}. Please improve.",
        }

    async def _generate_notes(
        self,
        task: str,
        results: Dict[str, Any],
        quality_score: float,
    ) -> List[Dict[str, Any]]:
        """Generate notes for cross-session learning."""
        # TODO: Implement note generation
        return []

    def _get_execution_time_ms(self) -> int:
        """Get total execution time in milliseconds."""
        if self._execution_start:
            delta = datetime.now(timezone.utc) - self._execution_start
            return int(delta.total_seconds() * 1000)
        return 0

    def _create_error_result(
        self,
        error: str,
        entry_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Create an error result."""
        return ExecutionResult(
            success=False,
            output={},
            quality_score=0.0,
            iterations_used=0,
            extensions_called=[],
            execution_time_ms=self._get_execution_time_ms(),
            entry_id=entry_id,
            error=error,
        )
