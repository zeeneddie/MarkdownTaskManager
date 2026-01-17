"""
Memory Repository for Confucius orchestrator.

Provides database persistence for hierarchical memory:
- Sessions (permanent)
- Entries (30 days)
- Runnables (7 days)
- Notes (permanent)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import uuid
import logging

from app.models.confucius import (
    ConfuciusSession,
    ConfuciusEntry,
    ConfuciusRunnable,
    ConfuciusNote,
)
from .types import (
    SessionMemory,
    EntryMemory,
    RunnableMemory,
)

logger = logging.getLogger(__name__)


class MemoryRepository:
    """
    Repository for Confucius memory persistence.

    Handles CRUD operations and cleanup for all memory scopes.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== SESSION OPERATIONS ====================

    async def get_session(self, session_id: str) -> Optional[SessionMemory]:
        """Get session by ID."""
        result = await self.db.execute(
            select(ConfuciusSession).where(
                ConfuciusSession.session_id == uuid.UUID(session_id)
            )
        )
        db_session = result.scalar_one_or_none()

        if db_session:
            return self._db_to_session_memory(db_session)
        return None

    async def get_session_by_project(self, project_id: str) -> Optional[SessionMemory]:
        """Get most recent session for a project."""
        result = await self.db.execute(
            select(ConfuciusSession)
            .where(ConfuciusSession.project_id == project_id)
            .order_by(ConfuciusSession.updated_at.desc())
            .limit(1)
        )
        db_session = result.scalar_one_or_none()

        if db_session:
            return self._db_to_session_memory(db_session)
        return None

    async def save_session(self, session: SessionMemory) -> SessionMemory:
        """Save or update a session."""
        # Check if exists
        result = await self.db.execute(
            select(ConfuciusSession).where(
                ConfuciusSession.session_id == uuid.UUID(session.session_id)
            )
        )
        db_session = result.scalar_one_or_none()

        if db_session:
            # Update existing
            db_session.insights = session.insights
            db_session.patterns = session.patterns
            db_session.decisions = session.decisions
            db_session.preferences = session.preferences
            db_session.updated_at = datetime.now(timezone.utc)
        else:
            # Create new
            db_session = ConfuciusSession(
                session_id=uuid.UUID(session.session_id),
                project_id=session.project_id,
                insights=session.insights,
                patterns=session.patterns,
                decisions=session.decisions,
                preferences=session.preferences,
                created_at=session.created_at,
                updated_at=session.updated_at,
            )
            self.db.add(db_session)

        await self.db.commit()
        await self.db.refresh(db_session)

        return self._db_to_session_memory(db_session)

    async def list_sessions(
        self,
        project_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[SessionMemory]:
        """List sessions, optionally filtered by project."""
        query = select(ConfuciusSession).order_by(ConfuciusSession.updated_at.desc())

        if project_id:
            query = query.where(ConfuciusSession.project_id == project_id)

        query = query.limit(limit)
        result = await self.db.execute(query)

        return [self._db_to_session_memory(s) for s in result.scalars().all()]

    # ==================== ENTRY OPERATIONS ====================

    async def get_entry(self, entry_id: str) -> Optional[EntryMemory]:
        """Get entry by ID."""
        result = await self.db.execute(
            select(ConfuciusEntry).where(
                ConfuciusEntry.entry_id == uuid.UUID(entry_id)
            )
        )
        db_entry = result.scalar_one_or_none()

        if db_entry:
            return self._db_to_entry_memory(db_entry)
        return None

    async def save_entry(self, entry: EntryMemory) -> EntryMemory:
        """Save or update an entry."""
        result = await self.db.execute(
            select(ConfuciusEntry).where(
                ConfuciusEntry.entry_id == uuid.UUID(entry.entry_id)
            )
        )
        db_entry = result.scalar_one_or_none()

        if db_entry:
            # Update existing
            db_entry.task = entry.task
            db_entry.context_summary = entry.context_summary
            db_entry.results_summary = entry.results_summary
            db_entry.quality_score = entry.quality_score
            db_entry.iterations_used = entry.iterations_used
            db_entry.extensions_called = entry.extensions_called
            db_entry.metadata = entry.metadata
            db_entry.completed_at = entry.completed_at
        else:
            # Create new
            db_entry = ConfuciusEntry(
                entry_id=uuid.UUID(entry.entry_id),
                session_id=uuid.UUID(entry.session_id),
                task=entry.task,
                context_summary=entry.context_summary,
                results_summary=entry.results_summary,
                quality_score=entry.quality_score,
                iterations_used=entry.iterations_used,
                extensions_called=entry.extensions_called,
                metadata=entry.metadata,
                created_at=entry.created_at,
                completed_at=entry.completed_at,
            )
            self.db.add(db_entry)

        await self.db.commit()
        await self.db.refresh(db_entry)

        return self._db_to_entry_memory(db_entry)

    async def find_related_entries(
        self,
        session_id: str,
        task_context: Dict[str, Any],
        limit: int = 5,
    ) -> List[EntryMemory]:
        """
        Find entries related to the current task context.

        Uses basic text matching for now. Can be enhanced with
        semantic similarity using embeddings.
        """
        # Extract keywords from task context
        task_text = str(task_context).lower()

        # Get recent entries from session
        result = await self.db.execute(
            select(ConfuciusEntry)
            .where(ConfuciusEntry.session_id == uuid.UUID(session_id))
            .where(ConfuciusEntry.completed_at.isnot(None))
            .order_by(ConfuciusEntry.quality_score.desc())
            .limit(limit * 2)  # Get more, then filter
        )

        entries = []
        for db_entry in result.scalars().all():
            # Basic relevance scoring
            entry_text = f"{db_entry.task} {db_entry.context_summary}".lower()
            if any(word in entry_text for word in task_text.split()[:10]):
                entries.append(self._db_to_entry_memory(db_entry))

            if len(entries) >= limit:
                break

        # If not enough matches, return recent high-quality entries
        if len(entries) < limit:
            result = await self.db.execute(
                select(ConfuciusEntry)
                .where(ConfuciusEntry.session_id == uuid.UUID(session_id))
                .where(ConfuciusEntry.quality_score >= 0.7)
                .order_by(ConfuciusEntry.created_at.desc())
                .limit(limit - len(entries))
            )
            for db_entry in result.scalars().all():
                entry = self._db_to_entry_memory(db_entry)
                if entry.entry_id not in [e.entry_id for e in entries]:
                    entries.append(entry)

        return entries

    async def list_entries(
        self,
        session_id: str,
        min_quality: Optional[float] = None,
        limit: int = 20,
    ) -> List[EntryMemory]:
        """List entries for a session."""
        query = (
            select(ConfuciusEntry)
            .where(ConfuciusEntry.session_id == uuid.UUID(session_id))
            .order_by(ConfuciusEntry.created_at.desc())
        )

        if min_quality is not None:
            query = query.where(ConfuciusEntry.quality_score >= min_quality)

        query = query.limit(limit)
        result = await self.db.execute(query)

        return [self._db_to_entry_memory(e) for e in result.scalars().all()]

    # ==================== RUNNABLE OPERATIONS ====================

    async def save_runnable(self, runnable: RunnableMemory) -> RunnableMemory:
        """Save a runnable execution record."""
        db_runnable = ConfuciusRunnable(
            runnable_id=uuid.UUID(runnable.runnable_id),
            entry_id=uuid.UUID(runnable.entry_id),
            extension_name=runnable.extension_name,
            input_summary=runnable.input_summary,
            output_summary=runnable.output_summary,
            output_data=runnable.output_data,
            duration_ms=runnable.duration_ms,
            success=runnable.success,
            error_message=runnable.error_message,
            created_at=runnable.created_at,
        )
        self.db.add(db_runnable)
        await self.db.commit()
        await self.db.refresh(db_runnable)

        return runnable

    async def get_runnables_for_entry(self, entry_id: str) -> List[RunnableMemory]:
        """Get all runnables for an entry."""
        result = await self.db.execute(
            select(ConfuciusRunnable)
            .where(ConfuciusRunnable.entry_id == uuid.UUID(entry_id))
            .order_by(ConfuciusRunnable.created_at)
        )

        return [self._db_to_runnable_memory(r) for r in result.scalars().all()]

    # ==================== NOTE OPERATIONS ====================

    async def save_note(
        self,
        note_type: str,
        problem: str,
        solution: Optional[str] = None,
        insights: Optional[List[str]] = None,
        context_tags: Optional[List[str]] = None,
        quality_score: float = 0.0,
        session_id: Optional[str] = None,
    ) -> ConfuciusNote:
        """Save a learning note."""
        db_note = ConfuciusNote(
            note_id=uuid.uuid4(),
            session_id=uuid.UUID(session_id) if session_id else None,
            note_type=note_type,
            problem=problem,
            solution=solution,
            insights=insights or [],
            context_tags=context_tags or [],
            quality_score=quality_score,
        )
        self.db.add(db_note)
        await self.db.commit()
        await self.db.refresh(db_note)

        return db_note

    async def search_notes(
        self,
        keywords: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        note_type: Optional[str] = None,
        min_quality: Optional[float] = None,
        limit: int = 10,
    ) -> List[ConfuciusNote]:
        """Search notes by various criteria."""
        query = select(ConfuciusNote).order_by(ConfuciusNote.quality_score.desc())

        conditions = []

        if note_type:
            conditions.append(ConfuciusNote.note_type == note_type)

        if min_quality is not None:
            conditions.append(ConfuciusNote.quality_score >= min_quality)

        if keywords:
            # Search in problem and solution text
            keyword_conditions = []
            for kw in keywords:
                keyword_conditions.append(
                    or_(
                        ConfuciusNote.problem.ilike(f"%{kw}%"),
                        ConfuciusNote.solution.ilike(f"%{kw}%"),
                    )
                )
            if keyword_conditions:
                conditions.append(or_(*keyword_conditions))

        if tags:
            # Search in context_tags array
            for tag in tags:
                conditions.append(
                    ConfuciusNote.context_tags.contains([tag])
                )

        if conditions:
            query = query.where(and_(*conditions))

        query = query.limit(limit)
        result = await self.db.execute(query)

        return list(result.scalars().all())

    # ==================== CLEANUP OPERATIONS ====================

    async def cleanup_old_entries(self, retention_days: int = 30) -> int:
        """Delete entries older than retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

        result = await self.db.execute(
            delete(ConfuciusEntry).where(ConfuciusEntry.created_at < cutoff)
        )
        await self.db.commit()

        deleted = result.rowcount
        logger.info(f"Cleaned up {deleted} old entries (>{retention_days} days)")
        return deleted

    async def cleanup_old_runnables(self, retention_days: int = 7) -> int:
        """Delete runnables older than retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

        result = await self.db.execute(
            delete(ConfuciusRunnable).where(ConfuciusRunnable.created_at < cutoff)
        )
        await self.db.commit()

        deleted = result.rowcount
        logger.info(f"Cleaned up {deleted} old runnables (>{retention_days} days)")
        return deleted

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        session_count = await self.db.execute(
            select(func.count()).select_from(ConfuciusSession)
        )
        entry_count = await self.db.execute(
            select(func.count()).select_from(ConfuciusEntry)
        )
        runnable_count = await self.db.execute(
            select(func.count()).select_from(ConfuciusRunnable)
        )
        note_count = await self.db.execute(
            select(func.count()).select_from(ConfuciusNote)
        )

        return {
            "sessions": session_count.scalar(),
            "entries": entry_count.scalar(),
            "runnables": runnable_count.scalar(),
            "notes": note_count.scalar(),
        }

    # ==================== CONVERTERS ====================

    def _db_to_session_memory(self, db_session: ConfuciusSession) -> SessionMemory:
        """Convert DB model to SessionMemory dataclass."""
        return SessionMemory(
            session_id=str(db_session.session_id),
            project_id=db_session.project_id,
            insights=db_session.insights or [],
            patterns=db_session.patterns or [],
            decisions=db_session.decisions or [],
            preferences=db_session.preferences or {},
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
        )

    def _db_to_entry_memory(self, db_entry: ConfuciusEntry) -> EntryMemory:
        """Convert DB model to EntryMemory dataclass."""
        return EntryMemory(
            entry_id=str(db_entry.entry_id),
            session_id=str(db_entry.session_id),
            task=db_entry.task,
            context_summary=db_entry.context_summary or "",
            results_summary=db_entry.results_summary or "",
            quality_score=db_entry.quality_score or 0.0,
            iterations_used=db_entry.iterations_used or 1,
            extensions_called=db_entry.extensions_called or [],
            metadata=db_entry.metadata or {},
            created_at=db_entry.created_at,
            completed_at=db_entry.completed_at,
        )

    def _db_to_runnable_memory(self, db_runnable: ConfuciusRunnable) -> RunnableMemory:
        """Convert DB model to RunnableMemory dataclass."""
        return RunnableMemory(
            runnable_id=str(db_runnable.runnable_id),
            entry_id=str(db_runnable.entry_id),
            extension_name=db_runnable.extension_name,
            input_summary=db_runnable.input_summary or "",
            output_summary=db_runnable.output_summary or "",
            output_data=db_runnable.output_data or {},
            duration_ms=db_runnable.duration_ms or 0,
            success=db_runnable.success,
            error_message=db_runnable.error_message,
            created_at=db_runnable.created_at,
        )
