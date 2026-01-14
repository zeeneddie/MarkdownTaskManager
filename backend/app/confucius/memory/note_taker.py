"""
Note-Taking System for Confucius orchestrator.

Provides cross-session learning through structured note-taking:
- Records successful solutions for reuse
- Captures failure cases for avoidance
- Extracts insights for context enrichment
- Identifies patterns for recognition
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class NoteType(Enum):
    """Types of learning notes."""
    SUCCESS = "success"      # Successful solution to record
    FAILURE = "failure"      # Failed attempt to avoid
    INSIGHT = "insight"      # General insight learned
    PATTERN = "pattern"      # Recognized pattern
    DECISION = "decision"    # Decision made with rationale


@dataclass
class Note:
    """A structured note for cross-session learning."""
    id: str
    type: NoteType
    problem: str
    solution: Optional[str]
    insights: List[str]
    context_tags: List[str]
    quality_score: float
    session_id: Optional[str]
    created_at: datetime

    @classmethod
    def create(
        cls,
        note_type: NoteType,
        problem: str,
        solution: Optional[str] = None,
        insights: Optional[List[str]] = None,
        context_tags: Optional[List[str]] = None,
        quality_score: float = 0.0,
        session_id: Optional[str] = None,
    ) -> "Note":
        """Create a new note."""
        return cls(
            id=str(uuid.uuid4()),
            type=note_type,
            problem=problem,
            solution=solution,
            insights=insights or [],
            context_tags=context_tags or [],
            quality_score=quality_score,
            session_id=session_id,
            created_at=datetime.utcnow(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "problem": self.problem,
            "solution": self.solution,
            "insights": self.insights,
            "context_tags": self.context_tags,
            "quality_score": self.quality_score,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
        }

    def to_markdown(self) -> str:
        """Convert note to Markdown format for display."""
        md = f"""## {self.type.value.upper()}: {self.problem[:50]}{"..." if len(self.problem) > 50 else ""}

**Problem:** {self.problem}

**Solution:** {self.solution or "N/A"}

**Insights:**
{chr(10).join(f"- {insight}" for insight in self.insights) if self.insights else "- None recorded"}

**Tags:** {", ".join(self.context_tags) if self.context_tags else "None"}

**Quality Score:** {self.quality_score:.2f}

---
"""
        return md

    def matches_context(self, context: Dict[str, Any]) -> float:
        """
        Calculate how well this note matches a given context.

        Returns score from 0.0 to 1.0.
        """
        context_str = str(context).lower()
        score = 0.0

        # Check tag matches
        for tag in self.context_tags:
            if tag.lower() in context_str:
                score += 0.2

        # Check problem text overlap
        problem_words = set(self.problem.lower().split())
        context_words = set(context_str.split())
        overlap = len(problem_words & context_words)
        if problem_words:
            score += (overlap / len(problem_words)) * 0.3

        # Boost by quality score
        score += self.quality_score * 0.2

        return min(score, 1.0)


@dataclass
class NoteExtraction:
    """Extracted information from a task result."""
    problem: str
    solution: Optional[str]
    insights: List[str]
    tags: List[str]
    note_type: NoteType


class NoteTaker:
    """
    Cross-session learning via structured note-taking.

    Records:
    - Successful solutions (for reuse)
    - Failure cases (for avoidance)
    - Insights (for context enrichment)
    - Patterns (for recognition)
    - Decisions (for consistency)

    Usage:
    ```python
    note_taker = NoteTaker(llm_service)

    # Record after task completion
    note = await note_taker.record(
        task="Analyze ADO leaks in declaratie.asp",
        result={"findings": [...], "fixes": [...]},
        quality_score=0.92,
    )

    # Retrieve relevant notes for new task
    relevant = await note_taker.retrieve_relevant(
        task="Find resource leaks in batch processing",
        context={"files": ["batch.asp"]},
    )
    ```
    """

    def __init__(
        self,
        repository: Optional[Any] = None,
        llm_service: Optional[Any] = None,
        auto_record_threshold: float = 0.7,
    ):
        """
        Initialize NoteTaker.

        Args:
            repository: MemoryRepository for persistence (optional)
            llm_service: LLM service for extraction (optional)
            auto_record_threshold: Min quality to auto-record notes
        """
        self.repository = repository
        self.llm_service = llm_service
        self.auto_record_threshold = auto_record_threshold
        self._recent_notes: List[Note] = []
        self._cache: Dict[str, List[Note]] = {}

    async def record(
        self,
        task: str,
        result: Dict[str, Any],
        quality_score: float,
        session_id: Optional[str] = None,
        force: bool = False,
    ) -> Optional[Note]:
        """
        Record a task execution as a note.

        Args:
            task: Task description
            result: Execution result
            quality_score: Quality score achieved
            session_id: Optional session ID to link
            force: Force recording even if below threshold

        Returns:
            Created note or None if not recorded
        """
        # Check if should record
        if not force and quality_score < self.auto_record_threshold:
            logger.debug(f"Skipping note recording: quality {quality_score} < threshold {self.auto_record_threshold}")
            return None

        # Extract structured information
        extraction = await self._extract_note_content(task, result, quality_score)

        # Create note
        note = Note.create(
            note_type=extraction.note_type,
            problem=extraction.problem,
            solution=extraction.solution,
            insights=extraction.insights,
            context_tags=extraction.tags,
            quality_score=quality_score,
            session_id=session_id,
        )

        # Persist if repository available
        if self.repository:
            await self.repository.save_note(
                note_type=note.type.value,
                problem=note.problem,
                solution=note.solution,
                insights=note.insights,
                context_tags=note.context_tags,
                quality_score=note.quality_score,
                session_id=session_id,
            )

        # Add to recent notes
        self._recent_notes.append(note)
        if len(self._recent_notes) > 100:
            self._recent_notes = self._recent_notes[-100:]

        logger.info(f"Recorded {note.type.value} note: {note.problem[:50]}...")
        return note

    async def retrieve_relevant(
        self,
        task: str,
        context: Dict[str, Any],
        limit: int = 5,
        min_score: float = 0.3,
    ) -> List[Note]:
        """
        Retrieve notes relevant to current task.

        Args:
            task: Current task description
            context: Task context
            limit: Maximum notes to return
            min_score: Minimum relevance score

        Returns:
            List of relevant notes sorted by relevance
        """
        # Extract keywords
        keywords = self._extract_keywords(task, context)

        # Search in repository if available
        if self.repository:
            db_notes = await self.repository.search_notes(
                keywords=keywords,
                min_quality=0.5,
                limit=limit * 2,
            )
            # Convert to Note objects
            notes = [self._db_note_to_note(n) for n in db_notes]
        else:
            notes = self._recent_notes.copy()

        # Score and filter by relevance
        scored = []
        combined_context = {"task": task, **context}

        for note in notes:
            score = note.matches_context(combined_context)
            if score >= min_score:
                scored.append((note, score))

        # Sort by score and return top N
        scored.sort(key=lambda x: x[1], reverse=True)
        return [note for note, _ in scored[:limit]]

    async def record_insight(
        self,
        insight: str,
        context_tags: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> Note:
        """Record a standalone insight."""
        note = Note.create(
            note_type=NoteType.INSIGHT,
            problem=insight,
            context_tags=context_tags or [],
            quality_score=0.8,
            session_id=session_id,
        )

        self._recent_notes.append(note)

        if self.repository:
            await self.repository.save_note(
                note_type=note.type.value,
                problem=note.problem,
                insights=[insight],
                context_tags=note.context_tags,
                quality_score=note.quality_score,
                session_id=session_id,
            )

        return note

    async def record_pattern(
        self,
        pattern_name: str,
        pattern_description: str,
        examples: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> Note:
        """Record a recognized pattern."""
        note = Note.create(
            note_type=NoteType.PATTERN,
            problem=pattern_name,
            solution=pattern_description,
            insights=examples or [],
            quality_score=0.9,
            session_id=session_id,
        )

        self._recent_notes.append(note)

        if self.repository:
            await self.repository.save_note(
                note_type=note.type.value,
                problem=note.problem,
                solution=note.solution,
                insights=note.insights,
                quality_score=note.quality_score,
                session_id=session_id,
            )

        return note

    def get_recent_notes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently recorded notes as dictionaries."""
        return [
            {
                "id": n.id,
                "type": n.type.value,
                "problem": n.problem[:100],
                "quality_score": n.quality_score,
                "created_at": n.created_at.isoformat(),
            }
            for n in self._recent_notes[-limit:]
        ]

    def get_notes_summary(self) -> Dict[str, Any]:
        """Get summary of recorded notes."""
        by_type = {}
        for note in self._recent_notes:
            by_type[note.type.value] = by_type.get(note.type.value, 0) + 1

        return {
            "total": len(self._recent_notes),
            "by_type": by_type,
            "avg_quality": (
                sum(n.quality_score for n in self._recent_notes) / len(self._recent_notes)
                if self._recent_notes else 0.0
            ),
        }

    async def _extract_note_content(
        self,
        task: str,
        result: Dict[str, Any],
        quality_score: float,
    ) -> NoteExtraction:
        """Extract structured note content from task and result."""
        # Determine note type
        note_type = self._determine_note_type(result, quality_score)

        # Try LLM extraction if available
        if self.llm_service:
            try:
                return await self._llm_extract(task, result, note_type)
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}")

        # Fallback to rule-based extraction
        return self._rule_based_extract(task, result, note_type)

    def _determine_note_type(
        self,
        result: Dict[str, Any],
        quality_score: float,
    ) -> NoteType:
        """Determine appropriate note type from result and quality."""
        result_str = str(result).lower()

        if quality_score >= 0.85:
            return NoteType.SUCCESS
        elif quality_score < 0.5:
            return NoteType.FAILURE
        elif "pattern" in result_str:
            return NoteType.PATTERN
        elif "decision" in result_str:
            return NoteType.DECISION
        else:
            return NoteType.INSIGHT

    async def _llm_extract(
        self,
        task: str,
        result: Dict[str, Any],
        note_type: NoteType,
    ) -> NoteExtraction:
        """Use LLM to extract note content."""
        prompt = f"""Extract a structured learning note from this task execution.

Task: {task}

Result: {str(result)[:2000]}

Note Type: {note_type.value}

Return a JSON object with:
- problem: What problem was being solved? (1-2 sentences)
- solution: What solution was applied? (1-2 sentences, or null if failed)
- insights: List of 2-3 key insights learned
- tags: List of context tags (e.g., "ado-leaks", "asp", "batch-processing")

JSON:"""

        response = await self.llm_service.generate_json(prompt)

        return NoteExtraction(
            problem=response.get("problem", task),
            solution=response.get("solution"),
            insights=response.get("insights", []),
            tags=response.get("tags", []),
            note_type=note_type,
        )

    def _rule_based_extract(
        self,
        task: str,
        result: Dict[str, Any],
        note_type: NoteType,
    ) -> NoteExtraction:
        """Rule-based extraction fallback."""
        # Extract problem from task
        problem = task

        # Extract solution from result
        solution = None
        if note_type == NoteType.SUCCESS:
            if "solution" in result:
                solution = str(result["solution"])[:500]
            elif "output" in result:
                solution = str(result["output"])[:500]
            elif "result" in result:
                solution = str(result["result"])[:500]

        # Extract insights
        insights = []
        if "insights" in result:
            result_insights = result["insights"]
            if isinstance(result_insights, list):
                insights = result_insights[:3]
        elif "findings" in result:
            findings_val = result.get("findings", [])
            if isinstance(findings_val, list):
                insights = [str(f)[:200] for f in findings_val[:3]]

        # Extract tags from task and result
        tags = self._extract_tags(task, result)

        return NoteExtraction(
            problem=problem,
            solution=solution,
            insights=insights,
            tags=tags,
            note_type=note_type,
        )

    def _extract_tags(self, task: str, result: Dict[str, Any]) -> List[str]:
        """Extract context tags from task and result."""
        tags = set()
        text = f"{task} {str(result)}".lower()

        # Technology tags
        tech_keywords = {
            "asp": "asp",
            "ado": "ado",
            "sql": "sql",
            "javascript": "javascript",
            "css": "css",
            "html": "html",
            "api": "api",
            "database": "database",
        }

        for keyword, tag in tech_keywords.items():
            if keyword in text:
                tags.add(tag)

        # Domain tags
        domain_keywords = {
            "leak": "resource-leak",
            "security": "security",
            "performance": "performance",
            "architecture": "architecture",
            "migration": "migration",
            "quality": "quality",
            "test": "testing",
        }

        for keyword, tag in domain_keywords.items():
            if keyword in text:
                tags.add(tag)

        return list(tags)[:10]

    def _extract_keywords(self, task: str, context: Dict[str, Any]) -> List[str]:
        """Extract keywords for note search."""
        text = f"{task} {str(context)}".lower()
        words = text.split()

        # Filter to meaningful words
        keywords = [
            w for w in words
            if len(w) > 3 and w.isalpha()
        ]

        return list(set(keywords))[:15]

    def _db_note_to_note(self, db_note: Any) -> Note:
        """Convert database note to Note object."""
        return Note(
            id=str(db_note.note_id),
            type=NoteType(db_note.note_type),
            problem=db_note.problem,
            solution=db_note.solution,
            insights=db_note.insights or [],
            context_tags=db_note.context_tags or [],
            quality_score=db_note.quality_score or 0.0,
            session_id=str(db_note.session_id) if db_note.session_id else None,
            created_at=db_note.created_at,
        )
