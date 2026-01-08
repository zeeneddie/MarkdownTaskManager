"""
Integration tests for BMAD Session Flow

Week 143 - Fase 28: Data Architecture Enhancement
Tests the complete BMAD session lifecycle using in-memory workflow.
"""

import pytest
from datetime import datetime, timezone

from app.services.brown_paper_service import (
    BMADBrownPaperWorkflow,
    BMADBrownPaperSession,
)


class TestBMADSessionLifecycleInMemory:
    """Test BMAD session lifecycle using in-memory operations."""

    @pytest.fixture
    def workflow(self):
        """Create BMADBrownPaperWorkflow instance."""
        return BMADBrownPaperWorkflow()

    def test_create_session_sync(self, workflow):
        """Test creating a new BMAD session (sync version)."""
        session = workflow.start_session(
            project_name="Test Project",
            project_path="/test/path"
        )

        assert session is not None
        assert session.project_name == "Test Project"
        assert session.project_path == "/test/path"
        assert session.status == "questions"
        assert session.current_question == 1
        assert session.answers == {}

    def test_get_session_after_create(self, workflow):
        """Test getting session after creation."""
        session = workflow.start_session(
            project_name="Get Test",
            project_path="/test/get"
        )

        retrieved = workflow.get_session(session.id)

        assert retrieved is not None
        assert retrieved.id == session.id
        assert retrieved.project_name == "Get Test"

    def test_list_sessions(self, workflow):
        """Test listing all sessions."""
        # Create multiple sessions
        session1 = workflow.start_session("Project 1", "/path/1")
        session2 = workflow.start_session("Project 2", "/path/2")
        session3 = workflow.start_session("Project 3", "/path/3")

        sessions = workflow.list_sessions()

        assert len(sessions) >= 3
        session_ids = [s.id for s in sessions]
        assert session1.id in session_ids
        assert session2.id in session_ids
        assert session3.id in session_ids

    def test_submit_answer_sync(self, workflow):
        """Test submitting answer using sync method."""
        session = workflow.start_session("Answer Test", "/test/answer")

        # Submit answer to question 1 (min_length varies by question)
        # Question 1 requires min 100 chars
        answer_text = "This is a comprehensive answer about the system context that provides enough detail to meet the minimum requirements for question 1."
        result = workflow.submit_answer(session.id, answer_text)

        assert result is not None
        assert "success" in result and result["success"] is True
        assert result["answered_question"] == 1

        # Verify session updated
        updated_session = workflow.get_session(session.id)
        assert updated_session.current_question == 2

    def test_submit_answer_returns_error_when_too_short(self, workflow):
        """Test that too short answers return error."""
        session = workflow.start_session("Short Answer Test", "/test/short")

        # Question 1 requires min 100 chars
        result = workflow.submit_answer(session.id, "Too short")

        assert "error" in result
        assert "Answer too short" in result["error"]

    def test_submit_answer_to_nonexistent_session(self, workflow):
        """Test submitting answer to nonexistent session returns error."""
        result = workflow.submit_answer("nonexistent-id", "Some answer")

        assert "error" in result
        assert "Session not found" in result["error"]

    def test_complete_all_questions_sync(self, workflow):
        """Test completing all 8 BMAD questions."""
        session = workflow.start_session("Complete Test", "/test/complete")

        # Answer all 8 questions with sufficient length
        for q_num in range(1, 9):
            long_answer = f"This is a comprehensive answer to question {q_num}. " * 10
            result = workflow.submit_answer(session.id, long_answer)
            assert "success" in result and result["success"] is True
            assert result["answered_question"] == q_num

        # Verify final state
        final_session = workflow.get_session(session.id)
        assert len(final_session.answers) == 8
        # After Q8, status becomes "analyzing"
        assert final_session.status == "analyzing"


class TestBMADSessionModel:
    """Test BMADBrownPaperSession model."""

    def test_session_creation_with_all_fields(self):
        """Test creating session with all fields."""
        now = datetime.now(timezone.utc)
        session = BMADBrownPaperSession(
            id="test-id",
            project_name="Test",
            project_path="/test",
            status="questions",
            current_question=1,
            answers={},
            migration_analysis=None,
            specification=None,
            tasks=None,
            created_at=now,
            updated_at=now
        )

        assert session.id == "test-id"
        assert session.project_name == "Test"
        assert session.status == "questions"

    def test_session_with_answers(self):
        """Test session with answers dict."""
        now = datetime.now(timezone.utc)
        session = BMADBrownPaperSession(
            id="test-id",
            project_name="Test",
            project_path="/test",
            status="questions",
            current_question=3,
            answers={1: "Answer 1", 2: "Answer 2"},
            migration_analysis=None,
            specification=None,
            tasks=None,
            created_at=now,
            updated_at=now
        )

        assert len(session.answers) == 2
        assert session.current_question == 3


class TestBMADSessionEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def workflow(self):
        """Create BMADBrownPaperWorkflow instance."""
        return BMADBrownPaperWorkflow()

    def test_get_nonexistent_session(self, workflow):
        """Test getting session that doesn't exist."""
        result = workflow.get_session("nonexistent-id")
        assert result is None

    def test_approve_nonexistent_session(self, workflow):
        """Test approving nonexistent session returns False."""
        result = workflow.approve_session("nonexistent-id")
        assert result is False

    def test_reject_nonexistent_session(self, workflow):
        """Test rejecting nonexistent session returns False."""
        result = workflow.reject_session("nonexistent-id", "Reason")
        assert result is False

    def test_multiple_sessions_isolation(self, workflow):
        """Test that multiple sessions are isolated."""
        session1 = workflow.start_session("Isolation 1", "/path/1")
        session2 = workflow.start_session("Isolation 2", "/path/2")

        # Answer different questions in each (with sufficient length)
        long_answer = "This is a comprehensive answer with sufficient length. " * 10
        workflow.submit_answer(session1.id, long_answer + " Session 1")
        workflow.submit_answer(session2.id, long_answer + " Session 2")
        workflow.submit_answer(session2.id, long_answer + " Session 2 Q2")

        # Verify isolation
        s1 = workflow.get_session(session1.id)
        s2 = workflow.get_session(session2.id)

        assert s1.current_question == 2
        assert s2.current_question == 3
        assert len(s1.answers) == 1
        assert len(s2.answers) == 2


class TestBMADSessionProgressTracking:
    """Test session progress tracking."""

    @pytest.fixture
    def workflow(self):
        """Create BMADBrownPaperWorkflow instance."""
        return BMADBrownPaperWorkflow()

    def test_progress_increases_with_answers(self, workflow):
        """Test that progress increases as answers are submitted."""
        session = workflow.start_session("Progress Test", "/test/progress")
        session_id = session.id

        assert session.current_question == 1

        # Submit 5 answers
        for i in range(1, 6):
            long_answer = f"This is answer {i} with sufficient length. " * 10
            result = workflow.submit_answer(session_id, long_answer)
            assert "success" in result and result["success"] is True

            # Check session state
            updated = workflow.get_session(session_id)
            assert updated.current_question == i + 1
            assert len(updated.answers) == i

    def test_status_changes_after_all_questions(self, workflow):
        """Test status changes to 'analyzing' after all questions."""
        session = workflow.start_session("Status Test", "/test/status")
        session_id = session.id

        # Complete all questions
        for i in range(1, 9):
            long_answer = f"This is answer {i} with sufficient length. " * 10
            workflow.submit_answer(session_id, long_answer)

        # Status should change to "analyzing"
        final = workflow.get_session(session_id)
        assert final.status == "analyzing"


class TestBMADSessionApprovalRejection:
    """Test session approval and rejection."""

    @pytest.fixture
    def workflow(self):
        """Create BMADBrownPaperWorkflow instance."""
        return BMADBrownPaperWorkflow()

    def test_cannot_approve_non_review_session(self, workflow):
        """Test that sessions not in 'review' status cannot be approved."""
        session = workflow.start_session("Approve Test", "/test/approve")

        # Session starts in "questions" status, not "review"
        result = workflow.approve_session(session.id)

        # Should return False because status is not "review"
        assert result is False

    def test_reject_any_session(self, workflow):
        """Test that any session can be rejected."""
        session = workflow.start_session("Reject Test", "/test/reject")

        # Reject should work regardless of current status
        result = workflow.reject_session(session.id, "Project cancelled")

        assert result is True
        rejected = workflow.get_session(session.id)
        assert rejected.status == "rejected"
        assert rejected.error_message == "Project cancelled"

