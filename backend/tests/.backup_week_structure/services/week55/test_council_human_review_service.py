"""
Unit Tests for Council Human Review Service

Week 55: Tests for 6-phase Human-in-the-Loop Council workflow.
Updated to support async SQLAlchemy service methods.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch

from app.services.council_human_review_service import CouncilHumanReviewService
from app.models.council_human_review import (
    CouncilHumanSession,
    CouncilProviderResponse,
    CouncilPeerReview,
    CouncilConsensus,
    SessionStatus,
    DocumentType,
)


@pytest.fixture
def mock_db_session():
    """Mock async database session with AsyncMock for async operations."""
    mock = MagicMock()
    # Make async operations return AsyncMock
    mock.execute = AsyncMock()
    mock.commit = AsyncMock()
    mock.refresh = AsyncMock()
    mock.add = MagicMock()
    return mock


@pytest.fixture
def council_service(mock_db_session):
    """Create CouncilHumanReviewService with mocked dependencies."""
    with patch('app.services.council_human_review_service.LLMCouncilService'):
        with patch('app.services.council_human_review_service.DocumentSyncService'):
            return CouncilHumanReviewService(mock_db_session, base_path="/tmp/docs")


# ============================================================================
# PHASE 1: SESSION CREATION TESTS
# ============================================================================

class TestPhase1SessionCreation:
    """Test session creation and initialization."""

    @pytest.mark.asyncio
    async def test_create_session(self, council_service, mock_db_session):
        """Test creating a new council session."""
        # Execute
        session = await council_service.create_session(
            document_type="onboarding",
            project_id=1,
            document_name="Developer Onboarding"
        )

        # Verify
        assert mock_db_session.add.called
        mock_db_session.commit.assert_awaited()
        mock_db_session.refresh.assert_awaited()

    @pytest.mark.asyncio
    async def test_create_session_with_custom_providers(self, council_service, mock_db_session):
        """Test creating session with custom provider config."""
        # Setup
        custom_config = {
            "providers": [
                {"name": "ollama/qwen2.5-coder:7b", "role": "generator"},
            ],
            "orchestrator": "ollama/qwen2.5:7b"
        }

        # Execute
        session = await council_service.create_session(
            document_type="architecture",
            providers_config=custom_config
        )

        # Verify
        assert mock_db_session.add.called

    def test_default_providers_config(self, council_service):
        """Test default provider configuration."""
        config = council_service._default_providers_config()

        # Verify
        assert "providers" in config
        assert "orchestrator" in config
        assert len(config["providers"]) >= 3
        assert config["timeout_seconds"] == 120

    @pytest.mark.asyncio
    async def test_start_generation(self, council_service, mock_db_session):
        """Test starting generation phase."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilHumanSession)
        mock_session.providers_config = council_service._default_providers_config()
        mock_session.status = SessionStatus.DRAFT.value

        # Setup mock execute to return session
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_session
        mock_db_session.execute.return_value = mock_result

        # Execute
        responses = await council_service.start_generation(
            session_id,
            prompt="Create developer onboarding docs",
            context={"project": "MarkdownTaskManager"}
        )

        # Verify
        assert mock_session.status == SessionStatus.PEER_REVIEW.value
        mock_db_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_start_generation_session_not_found(self, council_service, mock_db_session):
        """Test generation with non-existent session."""
        # Setup - return None for session lookup
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Execute & Verify
        with pytest.raises(ValueError, match="not found"):
            await council_service.start_generation(uuid4(), "test prompt")


# ============================================================================
# PHASE 2: PEER REVIEW TESTS
# ============================================================================

class TestPhase2PeerReview:
    """Test peer review functionality."""

    @pytest.mark.asyncio
    async def test_start_peer_review(self, council_service, mock_db_session):
        """Test starting peer review phase."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilHumanSession)
        mock_session.status = SessionStatus.GENERATING.value

        mock_responses = [
            MagicMock(spec=CouncilProviderResponse, id=uuid4(), provider_name="ollama/qwen2.5-coder:7b", content="Content 1"),
            MagicMock(spec=CouncilProviderResponse, id=uuid4(), provider_name="claude/sonnet", content="Content 2"),
            MagicMock(spec=CouncilProviderResponse, id=uuid4(), provider_name="codex/gpt-5.1-max", content="Content 3"),
        ]

        # Setup mock execute calls
        call_count = [0]
        def mock_execute_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:  # First call - get session
                result.scalars.return_value.first.return_value = mock_session
            else:  # Second call - get responses
                result.scalars.return_value.all.return_value = mock_responses
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute_side_effect)

        # Execute
        reviews = await council_service.start_peer_review(session_id)

        # Verify
        assert mock_session.status == SessionStatus.ORCHESTRATING.value
        mock_db_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_peer_review_needs_multiple_responses(self, council_service, mock_db_session):
        """Test that peer review requires at least 2 responses."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilHumanSession)
        mock_responses = [
            MagicMock(spec=CouncilProviderResponse, id=uuid4()),
        ]

        call_count = [0]
        def mock_execute_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                result.scalars.return_value.first.return_value = mock_session
            else:
                result.scalars.return_value.all.return_value = mock_responses
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute_side_effect)

        # Execute & Verify
        with pytest.raises(ValueError, match="at least 2"):
            await council_service.start_peer_review(session_id)


# ============================================================================
# PHASE 3: CONSENSUS CREATION TESTS
# ============================================================================

class TestPhase3Consensus:
    """Test consensus creation functionality."""

    @pytest.mark.asyncio
    async def test_create_consensus(self, council_service, mock_db_session):
        """Test creating consensus document."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilHumanSession)
        mock_session.providers_config = {"orchestrator": "claude/sonnet"}
        mock_session.status = SessionStatus.PEER_REVIEW.value

        mock_responses = [
            MagicMock(spec=CouncilProviderResponse, provider_name="ollama", content="Content"),
        ]
        mock_reviews = [
            MagicMock(spec=CouncilPeerReview, reviewed_provider="ollama", score=80, suggestions=["Add tests"]),
        ]

        call_count = [0]
        def mock_execute_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                result.scalars.return_value.first.return_value = mock_session
            elif call_count[0] == 2:
                result.scalars.return_value.all.return_value = mock_responses
            else:
                result.scalars.return_value.all.return_value = mock_reviews
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute_side_effect)

        # Execute
        consensus = await council_service.create_consensus(session_id)

        # Verify
        assert mock_session.status == SessionStatus.HUMAN_REVIEW.value
        assert mock_db_session.add.called
        mock_db_session.commit.assert_awaited()

    def test_generate_orchestrator_notes(self, council_service):
        """Test orchestrator notes generation."""
        # Setup
        mock_reviews = [
            MagicMock(spec=CouncilPeerReview, consensus_contribution="Keep structure"),
            MagicMock(spec=CouncilPeerReview, consensus_contribution="Add examples"),
            MagicMock(spec=CouncilPeerReview, consensus_contribution=None),
        ]

        # Execute
        notes = council_service._generate_orchestrator_notes(mock_reviews)

        # Verify
        assert "Orchestrator Notes" in notes
        assert "Keep structure" in notes
        assert "Add examples" in notes

    def test_collect_suggestions(self, council_service):
        """Test collecting suggestions from reviews."""
        # Setup
        mock_reviews = [
            MagicMock(spec=CouncilPeerReview, suggestions=["Add tests", "Improve docs"]),
            MagicMock(spec=CouncilPeerReview, suggestions=["Add tests", "Add examples"]),
            MagicMock(spec=CouncilPeerReview, suggestions=None),
        ]

        # Execute
        suggestions = council_service._collect_suggestions(mock_reviews)

        # Verify - should deduplicate
        assert "Add tests" in suggestions
        assert "Improve docs" in suggestions
        assert "Add examples" in suggestions


# ============================================================================
# PHASE 4: HUMAN REVIEW TESTS
# ============================================================================

class TestPhase4HumanReview:
    """Test human review functionality."""

    @pytest.mark.asyncio
    async def test_submit_human_feedback(self, council_service, mock_db_session):
        """Test submitting human feedback."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilHumanSession)
        mock_session.status = SessionStatus.HUMAN_REVIEW.value

        mock_consensus = MagicMock(spec=CouncilConsensus)
        mock_consensus.version = 1

        call_count = [0]
        def mock_execute_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                result.scalars.return_value.first.return_value = mock_session
            else:
                result.scalars.return_value.first.return_value = mock_consensus
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute_side_effect)

        # Execute
        result = await council_service.submit_human_feedback(
            session_id,
            feedback={"clarity": "Good but needs more examples"},
            marked_correct={"ollama": ["section 1", "section 2"]},
            conflicts_resolved={"auth_method": "Use OAuth2"},
            additions="Added section on deployment"
        )

        # Verify
        assert mock_consensus.human_feedback is not None
        assert mock_session.status == SessionStatus.FINALIZING.value
        mock_db_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_submit_human_feedback_no_consensus(self, council_service, mock_db_session):
        """Test error when no consensus exists."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilHumanSession)

        call_count = [0]
        def mock_execute_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                result.scalars.return_value.first.return_value = mock_session
            else:
                result.scalars.return_value.first.return_value = None
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute_side_effect)

        # Execute & Verify
        with pytest.raises(ValueError, match="No consensus"):
            await council_service.submit_human_feedback(session_id, feedback={})


# ============================================================================
# PHASE 5: FINAL SYNTHESIS TESTS
# ============================================================================

class TestPhase5Finalization:
    """Test final synthesis functionality."""

    @pytest.mark.asyncio
    async def test_finalize_consensus(self, council_service, mock_db_session):
        """Test finalizing consensus with human feedback."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilHumanSession)
        mock_session.status = SessionStatus.FINALIZING.value
        mock_session.providers_config = {"orchestrator": "claude/sonnet"}

        mock_consensus = MagicMock(spec=CouncilConsensus)
        mock_consensus.version = 1
        mock_consensus.consensus_content = "Original content"
        mock_consensus.human_additions = "Human added this"
        mock_consensus.human_conflicts_resolved = {"issue": "resolution"}
        mock_consensus.human_feedback = {"note": "Looks good"}
        mock_consensus.human_marked_correct = {"provider": ["item1"]}

        call_count = [0]
        def mock_execute_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                result.scalars.return_value.first.return_value = mock_session
            else:
                result.scalars.return_value.first.return_value = mock_consensus
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute_side_effect)

        # Execute
        result = await council_service.finalize_consensus(session_id)

        # Verify - should create new version
        assert mock_db_session.add.called
        mock_db_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_incorporate_human_feedback(self, council_service):
        """Test human feedback incorporation."""
        # Setup
        mock_consensus = MagicMock(spec=CouncilConsensus)
        mock_consensus.consensus_content = "Original content"
        mock_consensus.human_additions = "Human added section"
        mock_consensus.human_conflicts_resolved = {"auth": "Use OAuth2", "db": "Use PostgreSQL"}

        # Execute
        result = await council_service._incorporate_human_feedback(mock_consensus)

        # Verify
        assert "Human Additions" in result
        assert "Human added section" in result
        assert "Resolved Conflicts" in result
        assert "OAuth2" in result


# ============================================================================
# PHASE 6: APPROVAL/REJECTION TESTS
# ============================================================================

class TestPhase6ApprovalRejection:
    """Test approval and rejection functionality."""

    @pytest.mark.asyncio
    async def test_approve_consensus(self, council_service, mock_db_session):
        """Test approving consensus."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilHumanSession)
        mock_session.status = SessionStatus.FINALIZING.value
        mock_session.document_type = "onboarding"

        mock_consensus = MagicMock(spec=CouncilConsensus)
        mock_consensus.version = 2
        mock_consensus.is_approved = False

        call_count = [0]
        def mock_execute_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                result.scalars.return_value.first.return_value = mock_session
            else:
                result.scalars.return_value.first.return_value = mock_consensus
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute_side_effect)

        # Execute
        result = await council_service.approve_consensus(
            session_id,
            approved_by="human_reviewer",
            write_to_file=False,
            git_commit=False
        )

        # Verify
        assert result["status"] == "approved"
        assert result["approved_by"] == "human_reviewer"
        assert mock_consensus.is_approved is True
        assert mock_session.status == SessionStatus.APPROVED.value

    @pytest.mark.asyncio
    async def test_reject_consensus(self, council_service, mock_db_session):
        """Test rejecting consensus."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilHumanSession)
        mock_session.status = SessionStatus.HUMAN_REVIEW.value

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_session
        mock_db_session.execute.return_value = mock_result

        # Execute
        result = await council_service.reject_consensus(
            session_id,
            rejected_by="reviewer",
            reason="Needs more technical depth"
        )

        # Verify
        assert mock_session.status == SessionStatus.REJECTED.value
        assert mock_session.rejected_by == "reviewer"
        assert mock_session.rejection_reason == "Needs more technical depth"


# ============================================================================
# QUERY METHODS TESTS
# ============================================================================

class TestQueryMethods:
    """Test query and listing methods."""

    @pytest.mark.asyncio
    async def test_get_session_details(self, council_service, mock_db_session):
        """Test getting full session details."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilHumanSession)
        mock_session.to_dict.return_value = {"id": str(session_id)}

        mock_responses = [MagicMock(spec=CouncilProviderResponse)]
        mock_responses[0].to_dict.return_value = {"id": "resp1"}

        mock_reviews = [MagicMock(spec=CouncilPeerReview)]
        mock_reviews[0].to_dict.return_value = {"id": "review1"}

        mock_consensus = [MagicMock(spec=CouncilConsensus)]
        mock_consensus[0].to_dict.return_value = {"id": 1}

        call_count = [0]
        def mock_execute_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                result.scalars.return_value.first.return_value = mock_session
            elif call_count[0] == 2:
                result.scalars.return_value.all.return_value = mock_responses
            elif call_count[0] == 3:
                result.scalars.return_value.all.return_value = mock_reviews
            else:
                result.scalars.return_value.all.return_value = mock_consensus
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute_side_effect)

        # Execute
        details = await council_service.get_session_details(session_id)

        # Verify
        assert details is not None
        assert "session" in details
        assert "provider_responses" in details
        assert "peer_reviews" in details
        assert "consensus_versions" in details

    @pytest.mark.asyncio
    async def test_get_session_details_not_found(self, council_service, mock_db_session):
        """Test getting non-existent session details."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await council_service.get_session_details(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_list_sessions(self, council_service, mock_db_session):
        """Test listing sessions with filters."""
        # Setup
        mock_sessions = [
            MagicMock(spec=CouncilHumanSession, status=SessionStatus.APPROVED.value),
            MagicMock(spec=CouncilHumanSession, status=SessionStatus.DRAFT.value),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_sessions
        mock_db_session.execute.return_value = mock_result

        # Execute - with filters
        sessions = await council_service.list_sessions(
            project_id=1,
            status="approved",
            document_type="onboarding",
            limit=10
        )

        # Verify
        mock_db_session.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_session_statistics(self, council_service, mock_db_session):
        """Test getting session statistics."""
        # Setup - mock count query and group by query
        # Service calls: 1) status counts, 2) type counts, 3) total count
        call_count = [0]
        def mock_execute_side_effect(*args, **kwargs):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                # Status counts (first call)
                result.all.return_value = [
                    ("approved", 5),
                    ("draft", 3),
                    ("rejected", 2)
                ]
            elif call_count[0] == 2:
                # Type counts (second call)
                result.all.return_value = [
                    ("onboarding", 6),
                    ("architecture", 4)
                ]
            else:
                # Total count (third call)
                result.scalar.return_value = 10
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute_side_effect)

        # Execute
        stats = await council_service.get_session_statistics()

        # Verify
        assert "total_sessions" in stats
        assert stats["total_sessions"] == 10
        assert "by_status" in stats
        assert "by_document_type" in stats
        assert "approval_rate" in stats


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_generation_handles_provider_errors(self, council_service, mock_db_session):
        """Test that generation continues when a provider fails."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilHumanSession)
        mock_session.providers_config = {
            "providers": [
                {"name": "failing_provider", "role": "generator"},
                {"name": "working_provider", "role": "generator"},
            ]
        }
        mock_session.status = SessionStatus.DRAFT.value

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_session
        mock_db_session.execute.return_value = mock_result

        # Mock _generate_from_provider to fail for one provider
        async def mock_generate(provider_name, prompt, context):
            if "failing" in provider_name:
                raise Exception("Provider unavailable")
            return "Generated content"

        council_service._generate_from_provider = mock_generate

        # Execute
        responses = await council_service.start_generation(session_id, "Test prompt")

        # Verify - should have responses for both (one error, one success)
        assert mock_db_session.add.called

    @pytest.mark.asyncio
    async def test_approval_session_not_found(self, council_service, mock_db_session):
        """Test approval with non-existent session."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not found"):
            await council_service.approve_consensus(uuid4(), "reviewer")

    @pytest.mark.asyncio
    async def test_rejection_session_not_found(self, council_service, mock_db_session):
        """Test rejection with non-existent session."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not found"):
            await council_service.reject_consensus(uuid4(), "reviewer", "reason")
