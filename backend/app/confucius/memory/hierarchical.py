"""
Hierarchical Memory System for Confucius orchestrator.

Implements the three-scope memory architecture:
1. session_scope: Cross-task insights (permanent)
2. entry_scope: Per-task summaries (30 days)
3. runnable_scope: Tool execution outputs (7 days)

Features:
- Semantic relevance scoring
- Automatic summarization
- Cross-session persistence
- Context compression
- Efficient retrieval
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ..config import ConfuciusConfig
from .types import (
    SessionMemory,
    EntryMemory,
    RunnableMemory,
    RelevantMemory,
)
from .repository import MemoryRepository
from .compressor import ContextCompressor, CompressionResult
from .note_taker import NoteTaker

logger = logging.getLogger(__name__)


class HierarchicalMemory:
    """
    Full hierarchical working memory implementation.

    Three scopes:
    1. session_scope: All-time insights across tasks
    2. entry_scope: Per-task summaries
    3. runnable_scope: Tool execution outputs

    Example:
    ```python
    memory = HierarchicalMemory(config, repository)

    # Load or create session
    await memory.load_session(session_id, project_id)

    # Create entry for task
    entry_id = await memory.create_entry(task, context)

    # Record extension executions
    await memory.update_runnable(entry_id, "Felix", output, duration)

    # Get relevant memory for new task
    relevant = await memory.get_relevant(task_context, ["Felix", "Quinn"])

    # Complete entry
    await memory.complete_entry(entry_id, 0.92, "Analysis complete", ["Felix"], 1)
    ```
    """

    def __init__(
        self,
        config: ConfuciusConfig,
        repository: Optional[MemoryRepository] = None,
        compressor: Optional[ContextCompressor] = None,
        note_taker: Optional[NoteTaker] = None,
    ):
        """
        Initialize hierarchical memory.

        Args:
            config: Confucius configuration
            repository: Database repository (optional, uses in-memory if None)
            compressor: Context compressor (optional)
            note_taker: Note taker (optional)
        """
        self.config = config
        self.repository = repository
        self.compressor = compressor or ContextCompressor()
        self.note_taker = note_taker or NoteTaker(repository=repository)

        # In-memory caches
        self._current_session: Optional[SessionMemory] = None
        self._entries: Dict[str, EntryMemory] = {}
        self._runnables: Dict[str, RunnableMemory] = {}

    # ==================== SESSION OPERATIONS ====================

    async def load_session(
        self,
        session_id: str,
        project_id: str,
    ) -> SessionMemory:
        """
        Load existing session or create new one.

        Args:
            session_id: Session ID to load
            project_id: Project ID for new session

        Returns:
            Loaded or created SessionMemory
        """
        # Try to load from repository
        if self.repository:
            session = await self.repository.get_session(session_id)
            if session:
                self._current_session = session
                logger.info(f"Loaded session {session_id} with {len(session.insights)} insights")
                return session

        # Create new session
        return await self.create_session(project_id, session_id)

    async def create_session(
        self,
        project_id: str,
        session_id: Optional[str] = None,
    ) -> SessionMemory:
        """
        Create a new session.

        Args:
            project_id: Project identifier
            session_id: Optional specific session ID

        Returns:
            Created SessionMemory
        """
        if session_id:
            session = SessionMemory(
                session_id=session_id,
                project_id=project_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        else:
            session = SessionMemory.create(project_id)

        self._current_session = session

        # Persist if repository available
        if self.repository:
            await self.repository.save_session(session)

        logger.info(f"Created new session {session.session_id} for project {project_id}")
        return session

    @property
    def current_session(self) -> Optional[SessionMemory]:
        """Get current session."""
        return self._current_session

    # ==================== ENTRY OPERATIONS ====================

    async def create_entry(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Create a new entry for a task.

        Args:
            task: Task description
            context: Task context

        Returns:
            Entry ID

        Raises:
            ValueError: If no active session
        """
        if not self._current_session:
            raise ValueError("No active session. Call load_session() first.")

        entry = EntryMemory.create(
            session_id=self._current_session.session_id,
            task=task,
        )
        entry.context_summary = self._summarize_context(context)

        self._entries[entry.entry_id] = entry

        # Persist if repository available
        if self.repository:
            await self.repository.save_entry(entry)

        logger.debug(f"Created entry {entry.entry_id} for task: {task[:50]}...")
        return entry.entry_id

    async def complete_entry(
        self,
        entry_id: str,
        quality_score: float,
        results_summary: str,
        extensions_called: List[str],
        iterations_used: int,
    ) -> None:
        """
        Mark entry as complete.

        Args:
            entry_id: Entry ID
            quality_score: Final quality score
            results_summary: Summary of results
            extensions_called: List of extensions used
            iterations_used: Number of iterations
        """
        if entry_id not in self._entries:
            logger.warning(f"Entry {entry_id} not found in memory")
            return

        entry = self._entries[entry_id]
        entry.complete(quality_score, results_summary)
        entry.extensions_called = extensions_called
        entry.iterations_used = iterations_used

        # Persist if repository available
        if self.repository:
            await self.repository.save_entry(entry)

        # Record note if quality is good
        if self.note_taker and quality_score >= self.note_taker.auto_record_threshold:
            await self.note_taker.record(
                task=entry.task,
                result={"summary": results_summary, "extensions": extensions_called},
                quality_score=quality_score,
                session_id=entry.session_id,
            )

        logger.debug(f"Completed entry {entry_id} with quality {quality_score:.2f}")

    def get_entry(self, entry_id: str) -> Optional[EntryMemory]:
        """Get entry by ID."""
        return self._entries.get(entry_id)

    # ==================== RUNNABLE OPERATIONS ====================

    async def update_runnable(
        self,
        entry_id: str,
        extension_name: str,
        output: Dict[str, Any],
        duration_ms: int,
    ) -> str:
        """
        Record runnable execution to memory.

        Args:
            entry_id: Parent entry ID
            extension_name: Extension that executed
            output: Execution output
            duration_ms: Execution duration in ms

        Returns:
            Runnable ID
        """
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

        # Persist if repository available
        if self.repository:
            await self.repository.save_runnable(runnable)

        logger.debug(f"Recorded runnable {runnable.runnable_id} for {extension_name}")
        return runnable.runnable_id

    # ==================== RETRIEVAL OPERATIONS ====================

    async def get_relevant(
        self,
        task_context: Dict[str, Any],
        extensions: List[str],
    ) -> RelevantMemory:
        """
        Get relevant memory for current task.

        Args:
            task_context: Current task context
            extensions: Extensions that will be used

        Returns:
            RelevantMemory containing relevant insights, patterns, and entries
        """
        relevant = RelevantMemory()

        if not self._current_session:
            return relevant

        # Get session-level insights (most recent)
        relevant.session_insights = self._current_session.insights[
            -self.config.memory.max_session_insights:
        ]
        relevant.session_patterns = self._current_session.patterns[
            -self.config.memory.max_session_patterns:
        ]

        # Find related entries
        if self.repository:
            related = await self.repository.find_related_entries(
                session_id=self._current_session.session_id,
                task_context=task_context,
                limit=self.config.memory.max_relevant_entries,
            )
            relevant.related_entries = related
        else:
            # Use in-memory entries
            completed_entries = [
                e for e in self._entries.values()
                if e.completed_at and e.quality_score >= 0.5
            ]
            # Sort by quality and take most recent
            completed_entries.sort(
                key=lambda e: (e.quality_score, e.created_at),
                reverse=True,
            )
            relevant.related_entries = completed_entries[:self.config.memory.max_relevant_entries]

        # Get relevant notes
        if self.note_taker:
            notes = await self.note_taker.retrieve_relevant(
                task=str(task_context.get("task", "")),
                context=task_context,
                limit=5,
            )
            for note in notes:
                if note.insights:
                    relevant.session_insights.extend(
                        [{"from_note": note.id, "insight": i} for i in note.insights[:2]]
                    )

        return relevant

    async def get_compressed_context(
        self,
        context: Dict[str, Any],
        target_tokens: int,
        preserve_keys: Optional[List[str]] = None,
    ) -> CompressionResult:
        """
        Get compressed version of context.

        Args:
            context: Original context
            target_tokens: Target token count
            preserve_keys: Keys to always preserve

        Returns:
            CompressionResult with compressed context
        """
        return await self.compressor.compress(
            context=context,
            target_tokens=target_tokens,
            preserve_keys=preserve_keys,
        )

    # ==================== INSIGHT OPERATIONS ====================

    async def add_insight(self, insight: Dict[str, Any]) -> None:
        """
        Add insight to session memory.

        Args:
            insight: Insight dictionary with type, detail, etc.
        """
        if not self._current_session:
            logger.warning("No active session for adding insight")
            return

        self._current_session.add_insight(insight)

        # Persist if repository available
        if self.repository:
            await self.repository.save_session(self._current_session)

    async def add_pattern(self, pattern: Dict[str, Any]) -> None:
        """
        Add pattern to session memory.

        Args:
            pattern: Pattern dictionary with name, description, examples, etc.
        """
        if not self._current_session:
            logger.warning("No active session for adding pattern")
            return

        self._current_session.add_pattern(pattern)

        # Record as note for cross-session learning
        if self.note_taker:
            await self.note_taker.record_pattern(
                pattern_name=pattern.get("name", "Unknown pattern"),
                pattern_description=pattern.get("description", ""),
                examples=pattern.get("examples", []),
                session_id=self._current_session.session_id,
            )

        # Persist if repository available
        if self.repository:
            await self.repository.save_session(self._current_session)

    async def add_decision(self, decision: Dict[str, Any]) -> None:
        """
        Add decision to session memory.

        Args:
            decision: Decision dictionary with choice, rationale, etc.
        """
        if not self._current_session:
            logger.warning("No active session for adding decision")
            return

        self._current_session.add_decision(decision)

        # Persist if repository available
        if self.repository:
            await self.repository.save_session(self._current_session)

    # ==================== STATE OPERATIONS ====================

    def get_state(self) -> Dict[str, Any]:
        """Get current memory state for debugging."""
        return {
            "session_id": self._current_session.session_id if self._current_session else None,
            "project_id": self._current_session.project_id if self._current_session else None,
            "entries_count": len(self._entries),
            "runnables_count": len(self._runnables),
            "insights_count": len(self._current_session.insights) if self._current_session else 0,
            "patterns_count": len(self._current_session.patterns) if self._current_session else 0,
            "decisions_count": len(self._current_session.decisions) if self._current_session else 0,
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics including database counts."""
        state = self.get_state()

        if self.repository:
            db_stats = await self.repository.get_stats()
            state["database"] = db_stats

        if self.note_taker:
            state["notes"] = self.note_taker.get_notes_summary()

        return state

    # ==================== CLEANUP OPERATIONS ====================

    async def cleanup_old_data(self) -> Dict[str, int]:
        """
        Clean up old entries and runnables based on retention settings.

        Returns:
            Dictionary with counts of deleted items
        """
        deleted = {"entries": 0, "runnables": 0}

        if self.repository:
            deleted["entries"] = await self.repository.cleanup_old_entries(
                retention_days=self.config.memory.entry_retention_days
            )
            deleted["runnables"] = await self.repository.cleanup_old_runnables(
                retention_days=self.config.memory.runnable_retention_days
            )

        return deleted

    def clear_cache(self) -> None:
        """Clear in-memory caches."""
        self._entries.clear()
        self._runnables.clear()
        logger.info("Cleared memory caches")

    # ==================== HELPER METHODS ====================

    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """Create summary of context for storage."""
        # Simple summarization for now
        # TODO: Use LLM for intelligent summarization
        keys = list(context.keys())
        return f"Context with {len(keys)} keys: {', '.join(keys[:5])}{'...' if len(keys) > 5 else ''}"

    def _summarize_output(self, output: Dict[str, Any]) -> str:
        """Create summary of output for storage."""
        if "error" in output:
            return f"Error: {output['error']}"

        keys = list(output.keys())
        return f"Output with {len(keys)} keys: {', '.join(keys[:5])}{'...' if len(keys) > 5 else ''}"
