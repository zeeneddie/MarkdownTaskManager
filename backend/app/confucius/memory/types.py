"""
Memory types for Confucius hierarchical working memory.

Based on the CCA paper's three-scope memory architecture:
- session_scope: Cross-task insights
- entry_scope: Per-task summaries
- runnable_scope: Tool execution outputs
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from app.utils.datetime_utils import utc_now
from enum import Enum
import uuid


class MemoryScope(Enum):
    """Memory scope levels in the hierarchy."""
    SESSION = "session"    # Cross-task insights (permanent)
    ENTRY = "entry"        # Per-task summaries (30 days)
    RUNNABLE = "runnable"  # Tool execution outputs (7 days)


@dataclass
class MemoryNode:
    """A single memory node in the hierarchy."""
    id: str
    scope: MemoryScope
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    relevance_score: float = 1.0
    compressed: bool = False

    @classmethod
    def create(
        cls,
        scope: MemoryScope,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None,
    ) -> "MemoryNode":
        """Factory method to create a new memory node."""
        return cls(
            id=str(uuid.uuid4()),
            scope=scope,
            content=content,
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
            parent_id=parent_id,
        )


@dataclass
class SessionMemory:
    """
    Session-level memory (cross-task, permanent).

    Stores:
    - Insights learned across tasks
    - Patterns recognized in the codebase
    - Architectural decisions made
    - User preferences
    """
    session_id: str
    project_id: str
    insights: List[Dict[str, Any]] = field(default_factory=list)
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    @classmethod
    def create(cls, project_id: str) -> "SessionMemory":
        """Create a new session memory."""
        return cls(
            session_id=str(uuid.uuid4()),
            project_id=project_id,
        )

    def add_insight(self, insight: Dict[str, Any]) -> None:
        """Add an insight to session memory."""
        self.insights.append({
            **insight,
            "added_at": datetime.now(timezone.utc).isoformat(),
        })
        self.updated_at = datetime.now(timezone.utc)

    def add_pattern(self, pattern: Dict[str, Any]) -> None:
        """Add a pattern to session memory."""
        self.patterns.append({
            **pattern,
            "added_at": datetime.now(timezone.utc).isoformat(),
        })
        self.updated_at = datetime.now(timezone.utc)

    def add_decision(self, decision: Dict[str, Any]) -> None:
        """Add a decision to session memory."""
        self.decisions.append({
            **decision,
            "added_at": datetime.now(timezone.utc).isoformat(),
        })
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "insights": self.insights,
            "patterns": self.patterns,
            "decisions": self.decisions,
            "preferences": self.preferences,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class EntryMemory:
    """
    Entry-level memory (per-task, 30 days retention).

    Stores:
    - Task description
    - Context summary
    - Results summary
    - Quality score
    - Links to runnable memories
    """
    entry_id: str
    session_id: str
    task: str
    context_summary: str = ""
    results_summary: str = ""
    quality_score: float = 0.0
    iterations_used: int = 1
    extensions_called: List[str] = field(default_factory=list)
    runnable_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    completed_at: Optional[datetime] = None

    @classmethod
    def create(cls, session_id: str, task: str) -> "EntryMemory":
        """Create a new entry memory."""
        return cls(
            entry_id=str(uuid.uuid4()),
            session_id=session_id,
            task=task,
        )

    def complete(self, quality_score: float, results_summary: str) -> None:
        """Mark entry as complete."""
        self.quality_score = quality_score
        self.results_summary = results_summary
        self.completed_at = datetime.now(timezone.utc)

    def add_runnable(self, runnable_id: str) -> None:
        """Link a runnable memory to this entry."""
        self.runnable_ids.append(runnable_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "entry_id": self.entry_id,
            "session_id": self.session_id,
            "task": self.task,
            "context_summary": self.context_summary,
            "results_summary": self.results_summary,
            "quality_score": self.quality_score,
            "iterations_used": self.iterations_used,
            "extensions_called": self.extensions_called,
            "runnable_ids": self.runnable_ids,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class RunnableMemory:
    """
    Runnable-level memory (per-extension call, 7 days retention).

    Stores:
    - Extension name
    - Input/output summaries
    - Execution duration
    - Success status
    """
    runnable_id: str
    entry_id: str
    extension_name: str
    input_summary: str = ""
    output_summary: str = ""
    output_data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0
    success: bool = True
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=utc_now)

    @classmethod
    def create(cls, entry_id: str, extension_name: str) -> "RunnableMemory":
        """Create a new runnable memory."""
        return cls(
            runnable_id=str(uuid.uuid4()),
            entry_id=entry_id,
            extension_name=extension_name,
        )

    def complete(
        self,
        output_data: Dict[str, Any],
        output_summary: str,
        duration_ms: int,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """Complete the runnable with results."""
        self.output_data = output_data
        self.output_summary = output_summary
        self.duration_ms = duration_ms
        self.success = success
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "runnable_id": self.runnable_id,
            "entry_id": self.entry_id,
            "extension_name": self.extension_name,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "output_data": self.output_data,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class RelevantMemory:
    """Container for relevant memory retrieved for a task."""
    session_insights: List[Dict[str, Any]] = field(default_factory=list)
    session_patterns: List[Dict[str, Any]] = field(default_factory=list)
    related_entries: List[EntryMemory] = field(default_factory=list)
    related_runnables: List[RunnableMemory] = field(default_factory=list)

    def to_context(self) -> Dict[str, Any]:
        """Convert to context dict for LLM."""
        return {
            "previous_insights": self.session_insights[-10:],
            "known_patterns": self.session_patterns[-5:],
            "related_tasks": [
                {"task": e.task, "result": e.results_summary, "score": e.quality_score}
                for e in self.related_entries[-3:]
            ],
        }

    def is_empty(self) -> bool:
        """Check if no relevant memory was found."""
        return (
            not self.session_insights
            and not self.session_patterns
            and not self.related_entries
        )
