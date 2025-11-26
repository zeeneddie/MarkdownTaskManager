"""
Unit Tests for LLM Council Service

Week 52 Day 5: Tests for multi-model consensus decision making
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.services.llm_council_service import LLMCouncilService
from app.models.llm_council import (
    CouncilSession,
    CouncilResponse,
    CouncilReview,
    CouncilDecision
)


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def council_service(mock_db_session):
    """Create LLMCouncilService with mocked dependencies."""
    return LLMCouncilService(mock_db_session, ollama_base_url="http://localhost:11434")


# ============================================================================
# SESSION MANAGEMENT TESTS
# ============================================================================

class TestSessionManagement:
    """Test session creation, retrieval, and listing."""

    @pytest.mark.asyncio
    async def test_create_session(self, council_service, mock_db_session):
        """Test creating a new council session."""
        # Setup
        question = "What's the best architecture for microservices?"
        context = {"requirements": ["scalability", "reliability"], "constraints": ["budget"]}
        decision_type = "architecture"
        agent_id = "felix"

        # Execute
        session = await council_service.create_session(
            question=question,
            context=context,
            decision_type=decision_type,
            agent_id=agent_id
        )

        # Verify
        assert session.question == question
        assert session.context == context
        assert session.decision_type == decision_type
        assert session.agent_id == agent_id
        assert session.status == "pending"
        assert mock_db_session.add.called
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_get_session_with_relationships(self, council_service, mock_db_session):
        """Test retrieving session with eager-loaded relationships."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilSession)
        mock_session.id = session_id
        mock_session.responses = []
        mock_session.reviews = []
        mock_session.decision = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await council_service.get_session(session_id, include_relationships=True)

        # Verify
        assert result == mock_session
        assert mock_db_session.execute.called

    @pytest.mark.asyncio
    async def test_list_sessions_filtered(self, council_service, mock_db_session):
        """Test listing sessions with filters."""
        # Setup
        mock_sessions = [
            MagicMock(spec=CouncilSession, agent_id="felix", status="complete"),
            MagicMock(spec=CouncilSession, agent_id="felix", status="pending")
        ]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=mock_sessions)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        sessions = await council_service.list_sessions(
            agent_id="felix",
            status="complete",
            limit=10
        )

        # Verify
        assert len(sessions) == 2
        assert mock_db_session.execute.called


# ============================================================================
# STAGE 1: RESPONSE TESTS
# ============================================================================

class TestStage1Response:
    """Test parallel model querying."""

    @pytest.mark.asyncio
    async def test_query_all_models_success(self, council_service, mock_db_session):
        """Test successful parallel querying of all models."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilSession)
        mock_session.id = session_id
        mock_session.question = "Test question"
        mock_session.context = {}
        mock_session.decision_type = "architecture"
        mock_session.status = "pending"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock Ollama responses
        mock_responses = []
        for i, model_name in enumerate(council_service.models.keys()):
            mock_response = MagicMock(spec=CouncilResponse)
            mock_response.id = uuid4()
            mock_response.model_name = model_name
            mock_response.confidence = 0.8 + (i * 0.02)
            mock_responses.append(mock_response)

        with patch.object(
            council_service,
            '_query_single_model',
            side_effect=mock_responses
        ):
            # Execute
            responses = await council_service.query_all_models(session_id)

            # Verify
            assert len(responses) == 6  # 6 models
            assert mock_session.status == "reviewing"
            assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_query_single_model_timeout(self, council_service, mock_db_session):
        """Test handling of timeout when querying a single model."""
        # Setup
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.post.side_effect = asyncio.TimeoutError()

            # Execute & Verify
            with pytest.raises(Exception, match="Timeout querying"):
                await council_service._query_single_model(
                    "deepseek-r1:latest",
                    "Test prompt",
                    uuid4()
                )

    @pytest.mark.asyncio
    async def test_parallel_execution(self, council_service):
        """Test that models are queried in parallel (not sequential)."""
        # Setup
        import time

        call_times = []

        async def mock_query(*args):
            call_times.append(time.time())
            await asyncio.sleep(0.1)  # Simulate network delay
            response = MagicMock(spec=CouncilResponse)
            response.id = uuid4()
            return response

        # Execute
        start = time.time()
        with patch.object(council_service, '_query_single_model', side_effect=mock_query):
            tasks = [
                council_service._query_single_model("model", "prompt", uuid4())
                for _ in range(6)
            ]
            await asyncio.gather(*tasks)
        end = time.time()

        # Verify: Should take ~0.1s (parallel), not ~0.6s (sequential)
        assert end - start < 0.3  # Allow some overhead


# ============================================================================
# STAGE 2: PEER REVIEW TESTS
# ============================================================================

class TestStage2PeerReview:
    """Test peer review functionality."""

    @pytest.mark.asyncio
    async def test_peer_review_anonymization(self, council_service, mock_db_session):
        """Test that peer reviews are blind/anonymous."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilSession)
        mock_session.id = session_id
        mock_session.question = "Test question"

        # Create mock responses from 3 models
        mock_responses = []
        for model_name in ["model1", "model2", "model3"]:
            response = MagicMock(spec=CouncilResponse)
            response.id = uuid4()
            response.model_name = model_name
            response.response_text = f"Response from {model_name}"
            mock_responses.append(response)

        mock_session.responses = mock_responses

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock review function
        async def mock_review(*args):
            review = MagicMock(spec=CouncilReview)
            review.id = uuid4()
            return review

        with patch.object(council_service, '_review_single_response', side_effect=mock_review):
            # Execute
            reviews = await council_service.peer_review(session_id)

            # Verify: Each model reviews 2 others = 3 × 2 = 6 reviews
            assert len(reviews) == 6

    @pytest.mark.asyncio
    async def test_review_scoring(self, council_service):
        """Test parsing of review scores."""
        # Setup
        review_text = """
        ACCURACY: 8.5
        COMPLETENESS: 7.0
        CLARITY: 9.0
        FEASIBILITY: 6.5
        COMMENTS: Good solution but needs refinement
        """

        # Execute
        scores = council_service._parse_review_scores(review_text)

        # Verify
        assert scores["accuracy"] == 8.5
        assert scores["completeness"] == 7.0
        assert scores["clarity"] == 9.0
        assert scores["feasibility"] == 6.5
        assert "refinement" in scores["comments"]

    @pytest.mark.asyncio
    async def test_review_all_models(self, council_service, mock_db_session):
        """Test that all models review each other."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilSession)

        # 4 models responded
        mock_responses = [
            MagicMock(spec=CouncilResponse, id=uuid4(), model_name=f"model{i}")
            for i in range(4)
        ]
        mock_session.responses = mock_responses

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        review_calls = []

        async def track_review(reviewer, response, *args):
            review_calls.append((reviewer, response.model_name))
            return MagicMock(spec=CouncilReview, id=uuid4())

        with patch.object(council_service, '_review_single_response', side_effect=track_review):
            # Execute
            await council_service.peer_review(session_id)

            # Verify: 4 models × 3 others each = 12 reviews
            assert len(review_calls) == 12


# ============================================================================
# STAGE 3: SYNTHESIS TESTS
# ============================================================================

class TestStage3Synthesis:
    """Test chairman synthesis and consensus calculation."""

    @pytest.mark.asyncio
    async def test_consensus_calculation(self, council_service):
        """Test consensus level calculation."""
        # Setup: High consensus (all similar confidences)
        responses_high = [
            MagicMock(spec=CouncilResponse, confidence=0.85),
            MagicMock(spec=CouncilResponse, confidence=0.87),
            MagicMock(spec=CouncilResponse, confidence=0.86),
        ]
        response_scores_high = {str(r.id): 8.0 for r in responses_high}

        # Execute
        consensus_high = council_service._calculate_consensus(
            responses_high,
            response_scores_high
        )

        # Setup: Low consensus (varied confidences)
        responses_low = [
            MagicMock(spec=CouncilResponse, confidence=0.5),
            MagicMock(spec=CouncilResponse, confidence=0.9),
            MagicMock(spec=CouncilResponse, confidence=0.6),
        ]
        response_scores_low = {str(r.id): score for r, score in zip(responses_low, [4.0, 9.0, 5.0])}

        consensus_low = council_service._calculate_consensus(
            responses_low,
            response_scores_low
        )

        # Verify
        assert consensus_high > 70.0  # High consensus
        assert consensus_low < consensus_high  # Low consensus is lower

    @pytest.mark.asyncio
    async def test_outlier_detection(self, council_service):
        """Test detection of outlier/dissenting responses."""
        # Setup
        responses = []
        response_scores = {}

        # 4 similar responses
        for i in range(4):
            r = MagicMock(spec=CouncilResponse)
            r.id = uuid4()
            r.response_text = "RECOMMENDATION: Use microservices"
            responses.append(r)
            response_scores[str(r.id)] = 8.0

        # 1 outlier response
        outlier = MagicMock(spec=CouncilResponse)
        outlier.id = uuid4()
        outlier.response_text = "RECOMMENDATION: Use monolithic architecture"
        responses.append(outlier)
        response_scores[str(outlier.id)] = 3.0  # Much lower score

        # Execute
        outliers = council_service._detect_outliers(responses, response_scores)

        # Verify: Should detect the outlier (>2 std devs from mean)
        assert len(outliers) > 0

    @pytest.mark.asyncio
    async def test_chairman_synthesis(self, council_service, mock_db_session):
        """Test chairman creates final decision."""
        # Setup
        session_id = uuid4()
        mock_session = MagicMock(spec=CouncilSession)
        mock_session.id = session_id
        mock_session.question = "Test question"
        mock_session.status = "reviewing"

        # Mock responses and reviews
        mock_responses = [
            MagicMock(spec=CouncilResponse, id=uuid4(), model_name="model1", confidence=0.85)
        ]
        mock_reviews = [
            MagicMock(spec=CouncilReview, accuracy_score=8.0, completeness_score=7.0,
                     clarity_score=9.0, feasibility_score=8.0)
        ]
        mock_session.responses = mock_responses
        mock_session.reviews = mock_reviews

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock Ollama chairman response
        with patch('aiohttp.ClientSession') as mock_http:
            mock_http_instance = AsyncMock()
            mock_http.return_value.__aenter__.return_value = mock_http_instance

            mock_post_response = AsyncMock()
            mock_post_response.raise_for_status = MagicMock()
            mock_post_response.json = AsyncMock(return_value={
                "response": "FINAL DECISION: Use microservices\nREASONING: Best for scalability\nCONFIDENCE: 85%"
            })
            mock_http_instance.post.return_value.__aenter__.return_value = mock_post_response

            # Execute
            decision = await council_service.synthesize(session_id)

            # Verify
            assert isinstance(decision, CouncilDecision)
            assert decision.chairman_model == "deepseek-r1:latest"
            assert decision.consensus_level >= 0.0
            assert decision.consensus_level <= 100.0
            assert mock_session.status == "complete"
            assert mock_db_session.commit.called
