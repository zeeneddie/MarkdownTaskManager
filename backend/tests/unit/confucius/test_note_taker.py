"""Unit tests for NoteTaker."""

import pytest
from datetime import datetime
from app.confucius.memory.note_taker import (
    NoteTaker,
    Note,
    NoteType,
    NoteExtraction,
)


class TestNoteType:
    """Tests for NoteType enum."""

    def test_types(self):
        """Test note type values."""
        assert NoteType.SUCCESS.value == "success"
        assert NoteType.FAILURE.value == "failure"
        assert NoteType.INSIGHT.value == "insight"
        assert NoteType.PATTERN.value == "pattern"
        assert NoteType.DECISION.value == "decision"


class TestNote:
    """Tests for Note dataclass."""

    def test_create(self):
        """Test creating a note."""
        note = Note.create(
            note_type=NoteType.SUCCESS,
            problem="How to fix ADO leaks",
            solution="Use Try/Finally with proper cleanup",
            insights=["Always close connections", "Check error paths"],
            context_tags=["ado", "asp", "resource-leak"],
            quality_score=0.92,
        )

        assert note.id is not None
        assert note.type == NoteType.SUCCESS
        assert note.problem == "How to fix ADO leaks"
        assert len(note.insights) == 2
        assert "ado" in note.context_tags

    def test_to_dict(self):
        """Test note serialization."""
        note = Note.create(
            note_type=NoteType.PATTERN,
            problem="ADO connection pattern",
        )

        data = note.to_dict()

        assert data["type"] == "pattern"
        assert "id" in data
        assert "created_at" in data

    def test_to_markdown(self):
        """Test markdown conversion."""
        note = Note.create(
            note_type=NoteType.SUCCESS,
            problem="Fixed memory leak",
            solution="Implemented cleanup routine",
            insights=["Check all paths", "Test edge cases"],
        )

        md = note.to_markdown()

        assert "SUCCESS" in md
        assert "Fixed memory leak" in md
        assert "Check all paths" in md

    def test_matches_context_tags(self):
        """Test context matching by tags."""
        note = Note.create(
            note_type=NoteType.SUCCESS,
            problem="Fixed issue",
            context_tags=["ado", "database"],
        )

        score = note.matches_context({"task": "Analyze ADO connections"})

        assert score > 0  # Should match "ado" tag

    def test_matches_context_problem_text(self):
        """Test context matching by problem text."""
        note = Note.create(
            note_type=NoteType.SUCCESS,
            problem="Fixed database connection leak",
        )

        score = note.matches_context({"task": "Fix connection issues"})

        assert score > 0  # Should match "connection"

    def test_no_match(self):
        """Test when context doesn't match."""
        note = Note.create(
            note_type=NoteType.SUCCESS,
            problem="Fixed UI rendering",
            context_tags=["frontend", "css"],
        )

        score = note.matches_context({"task": "Analyze backend API"})

        # Should have low or no match
        assert score < 0.5


class TestNoteTaker:
    """Tests for NoteTaker."""

    @pytest.fixture
    def note_taker(self):
        """Create a NoteTaker for testing."""
        return NoteTaker(auto_record_threshold=0.7)

    @pytest.mark.asyncio
    async def test_record_success(self, note_taker):
        """Test recording a successful task."""
        note = await note_taker.record(
            task="Fix ADO leak in declaratie.asp",
            result={"findings": 3, "fixes": 3, "solution": "Added cleanup"},
            quality_score=0.92,
        )

        assert note is not None
        assert note.type == NoteType.SUCCESS
        assert note.quality_score == 0.92

    @pytest.mark.asyncio
    async def test_record_below_threshold(self, note_taker):
        """Test that low quality tasks are not recorded."""
        note = await note_taker.record(
            task="Partial analysis",
            result={"incomplete": True},
            quality_score=0.5,  # Below threshold of 0.7
        )

        assert note is None

    @pytest.mark.asyncio
    async def test_record_force(self, note_taker):
        """Test forcing note recording."""
        note = await note_taker.record(
            task="Force record",
            result={},
            quality_score=0.3,
            force=True,
        )

        assert note is not None

    @pytest.mark.asyncio
    async def test_record_failure(self, note_taker):
        """Test recording a failed task."""
        note = await note_taker.record(
            task="Failed analysis",
            result={"error": "Timeout"},
            quality_score=0.3,
            force=True,
        )

        assert note is not None
        assert note.type == NoteType.FAILURE

    @pytest.mark.asyncio
    async def test_record_insight(self, note_taker):
        """Test recording a standalone insight."""
        note = await note_taker.record_insight(
            insight="ADO connections should always be closed in finally blocks",
            context_tags=["ado", "best-practice"],
        )

        assert note.type == NoteType.INSIGHT
        assert "ado" in note.context_tags

    @pytest.mark.asyncio
    async def test_record_pattern(self, note_taker):
        """Test recording a pattern."""
        note = await note_taker.record_pattern(
            pattern_name="Connection Cleanup Pattern",
            pattern_description="Always use Try/Finally for resource cleanup",
            examples=["See declaratie.asp", "See batch.asp"],
        )

        assert note.type == NoteType.PATTERN
        assert note.problem == "Connection Cleanup Pattern"
        assert len(note.insights) == 2

    @pytest.mark.asyncio
    async def test_retrieve_relevant(self, note_taker):
        """Test retrieving relevant notes."""
        # Add some notes with explicit tags for better matching
        await note_taker.record(
            task="Fix ADO connection leak in database layer",
            result={"solution": "Added cleanup", "database": True},
            quality_score=0.9,
        )
        await note_taker.record(
            task="Fix CSS styling issue",
            result={"solution": "Updated styles"},
            quality_score=0.85,
        )

        # Retrieve relevant notes with lower threshold to allow partial matches
        relevant = await note_taker.retrieve_relevant(
            task="Fix database connection issues",
            context={"type": "backend", "database": True},
            min_score=0.1,  # Lower threshold for testing
        )

        # ADO note should be more relevant due to database/connection keywords
        assert len(relevant) > 0

    def test_get_recent_notes(self, note_taker):
        """Test getting recent notes."""
        # Initially empty
        recent = note_taker.get_recent_notes()
        assert len(recent) == 0

    @pytest.mark.asyncio
    async def test_get_notes_summary(self, note_taker):
        """Test getting notes summary."""
        await note_taker.record(
            task="Task 1",
            result={},
            quality_score=0.8,
        )
        await note_taker.record(
            task="Task 2",
            result={},
            quality_score=0.9,
        )

        summary = note_taker.get_notes_summary()

        assert summary["total"] == 2
        assert summary["avg_quality"] > 0.8

    def test_determine_note_type(self, note_taker):
        """Test note type determination."""
        # High quality = success
        assert note_taker._determine_note_type({}, 0.9) == NoteType.SUCCESS

        # Low quality = failure
        assert note_taker._determine_note_type({}, 0.3) == NoteType.FAILURE

        # Pattern keyword
        assert note_taker._determine_note_type({"pattern": "found"}, 0.7) == NoteType.PATTERN

        # Decision keyword
        assert note_taker._determine_note_type({"decision": "made"}, 0.7) == NoteType.DECISION

    def test_extract_tags(self, note_taker):
        """Test tag extraction."""
        tags = note_taker._extract_tags(
            task="Analyze SQL queries in ASP code",
            result={"security": "checked", "performance": "optimized"},
        )

        assert "sql" in tags
        assert "asp" in tags
        assert "security" in tags
        assert "performance" in tags

    def test_extract_keywords(self, note_taker):
        """Test keyword extraction."""
        keywords = note_taker._extract_keywords(
            task="Fix the database connection leak",
            context={"file": "connection.asp"},
        )

        assert "database" in keywords
        assert "connection" in keywords


class TestNoteExtraction:
    """Tests for NoteExtraction dataclass."""

    def test_creation(self):
        """Test creating an extraction."""
        extraction = NoteExtraction(
            problem="Test problem",
            solution="Test solution",
            insights=["Insight 1", "Insight 2"],
            tags=["tag1", "tag2"],
            note_type=NoteType.SUCCESS,
        )

        assert extraction.problem == "Test problem"
        assert len(extraction.insights) == 2
        assert extraction.note_type == NoteType.SUCCESS
