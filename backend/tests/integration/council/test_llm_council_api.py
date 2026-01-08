"""
Integration Tests for LLM Council REST API

Week 52 Day 5: Tests for all 8 API endpoints with error handling
"""

import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.main import app
from app.models.llm_council import (
    CouncilSession,
    CouncilResponse,
    CouncilReview,
    CouncilDecision
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_session():
    """Create mock council session."""
    session = MagicMock(spec=CouncilSession)
    session.id = uuid4()
    session.question = "What's the best architecture for microservices?"
    session.context = {"requirements": ["scalability"]}
    session.decision_type = "architecture"
    session.agent_id = "felix"
    session.status = "pending"
    session.created_at = datetime.now()
    session.completed_at = None
    session.responses = []
    session.reviews = []
    session.decision = None
    return session


@pytest.fixture
def mock_responses():
    """Create mock council responses."""
    responses = []
    for i, model_name in enumerate(["deepseek-r1:latest", "qwen2.5-coder:7b", "codellama:latest"]):
        response = MagicMock(spec=CouncilResponse)
        response.id = uuid4()
        response.session_id = uuid4()
        response.model_name = model_name
        response.response_text = f"Response from {model_name}"
        response.confidence = 0.8 + (i * 0.05)
        response.reasoning = f"Reasoning from {model_name}"
        response.created_at = datetime.now()
        responses.append(response)
    return responses


@pytest.fixture
def mock_decision():
    """Create mock council decision."""
    decision = MagicMock(spec=CouncilDecision)
    decision.id = uuid4()
    decision.session_id = uuid4()
    decision.chairman_model = "deepseek-r1:latest"
    decision.final_decision = "Use microservices architecture"
    decision.reasoning = "Best for scalability and maintainability"
    decision.confidence = 0.85
    decision.consensus_level = 78.5
    decision.dissenting_opinions = None
    decision.model_weights = {"deepseek-r1:latest": 2.0}
    decision.aggregate_scores = {}
    decision.created_at = datetime.now()
    return decision


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================

class TestCreateSession:
    """Test session creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_session_valid(self, mock_session):
        """Test creating a valid council session."""
        with patch('app.api.llm_council.LLMCouncilService') as mock_service_class:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.create_session = AsyncMock(return_value=mock_session)
            mock_service_class.return_value = mock_service

            # Make request
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/council/sessions",
                    json={
                        "question": "What's the best architecture for microservices?",
                        "context": {"requirements": ["scalability"]},
                        "decision_type": "architecture",
                        "agent_id": "felix"
                    }
                )

            # Verify
            assert response.status_code == 201
            data = response.json()
            assert data["question"] == mock_session.question
            assert data["decision_type"] == "architecture"
            assert data["status"] == "pending"
            assert mock_service.create_session.called

    @pytest.mark.asyncio
    async def test_create_session_invalid_type(self):
        """Test creating session with invalid decision type."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/council/sessions",
                json={
                    "question": "Test question",
                    "context": {},
                    "decision_type": "invalid_type",  # Invalid!
                    "agent_id": "felix"
                }
            )

        # Verify validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_session_question_too_short(self):
        """Test creating session with question too short."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/council/sessions",
                json={
                    "question": "Short",  # Too short (min_length=10)
                    "context": {},
                    "decision_type": "architecture",
                    "agent_id": "felix"
                }
            )

        # Verify validation error
        assert response.status_code == 422


class TestExecuteStages:
    """Test stage execution endpoints."""

    @pytest.mark.asyncio
    async def test_execute_stage_1(self, mock_session, mock_responses):
        """Test executing Stage 1: Query models."""
        session_id = uuid4()

        with patch('app.api.llm_council.LLMCouncilService') as mock_service_class:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.query_all_models = AsyncMock(return_value=mock_responses)
            mock_service_class.return_value = mock_service

            # Make request
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    f"/api/council/sessions/{session_id}/query"
                )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["stage"] == "query_models"
            assert data["status"] == "success"
            assert data["count"] == 3  # 3 mock responses
            mock_service.query_all_models.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_stage_2(self, mock_session):
        """Test executing Stage 2: Peer review."""
        session_id = uuid4()

        # Create mock reviews
        mock_reviews = [
            MagicMock(spec=CouncilReview, id=uuid4())
            for _ in range(6)  # 3 models × 2 reviews each
        ]

        with patch('app.api.llm_council.LLMCouncilService') as mock_service_class:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.peer_review = AsyncMock(return_value=mock_reviews)
            mock_service_class.return_value = mock_service

            # Make request
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    f"/api/council/sessions/{session_id}/review"
                )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["stage"] == "peer_review"
            assert data["status"] == "success"
            assert data["count"] == 6  # 6 reviews
            mock_service.peer_review.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_stage_3(self, mock_session, mock_decision):
        """Test executing Stage 3: Synthesis."""
        session_id = uuid4()

        with patch('app.api.llm_council.LLMCouncilService') as mock_service_class:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.synthesize = AsyncMock(return_value=mock_decision)
            mock_service_class.return_value = mock_service

            # Make request
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    f"/api/council/sessions/{session_id}/synthesize",
                    params={"chairman_model": "deepseek-r1:latest"}
                )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["chairman_model"] == "deepseek-r1:latest"
            assert data["final_decision"] == mock_decision.final_decision
            assert data["confidence"] == mock_decision.confidence
            assert data["consensus_level"] == mock_decision.consensus_level
            assert mock_service.synthesize.called


class TestQuickDecision:
    """Test quick decision endpoint (all stages in one call)."""

    @pytest.mark.asyncio
    async def test_quick_decision_success(self, mock_session, mock_responses, mock_decision):
        """Test successful quick decision execution."""
        with patch('app.api.llm_council.LLMCouncilService') as mock_service_class:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.create_session = AsyncMock(return_value=mock_session)
            mock_service.query_all_models = AsyncMock(return_value=mock_responses)
            mock_service.peer_review = AsyncMock(return_value=[MagicMock() for _ in range(6)])
            mock_service.synthesize = AsyncMock(return_value=mock_decision)
            mock_service_class.return_value = mock_service

            # Make request
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/council/quick",
                    json={
                        "question": "What's the best architecture for microservices?",
                        "context": {"requirements": ["scalability"]},
                        "decision_type": "architecture",
                        "agent_id": "felix",
                        "chairman_model": "deepseek-r1:latest"
                    }
                )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            assert "decision" in data
            assert data["decision"]["final_decision"] == mock_decision.final_decision
            assert data["consensus_level"] == mock_decision.consensus_level
            assert data["response_count"] == 3
            assert data["review_count"] == 6
            assert "consensus" in data["message"].lower()

            # Verify all stages called
            assert mock_service.create_session.called
            assert mock_service.query_all_models.called
            assert mock_service.peer_review.called
            assert mock_service.synthesize.called

    @pytest.mark.asyncio
    async def test_quick_decision_no_responses(self, mock_session):
        """Test quick decision when no models respond."""
        with patch('app.api.llm_council.LLMCouncilService') as mock_service_class:
            # Setup mock service - no responses!
            mock_service = AsyncMock()
            mock_service.create_session = AsyncMock(return_value=mock_session)
            mock_service.query_all_models = AsyncMock(return_value=[])  # Empty!
            mock_service_class.return_value = mock_service

            # Make request
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/council/quick",
                    json={
                        "question": "Test question",
                        "context": {},
                        "decision_type": "architecture",
                        "agent_id": "felix"
                    }
                )

            # Verify error
            assert response.status_code == 500
            data = response.json()
            assert "no models responded" in data["detail"].lower()


class TestGetDecision:
    """Test getting existing decision."""

    @pytest.mark.asyncio
    async def test_get_decision_exists(self, mock_session, mock_decision):
        """Test getting decision that exists."""
        session_id = uuid4()
        mock_session.decision = mock_decision

        with patch('app.api.llm_council.LLMCouncilService') as mock_service_class:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.get_session = AsyncMock(return_value=mock_session)
            mock_service_class.return_value = mock_service

            # Make request
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    f"/api/council/sessions/{session_id}/decision"
                )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["chairman_model"] == mock_decision.chairman_model
            assert data["final_decision"] == mock_decision.final_decision

    @pytest.mark.asyncio
    async def test_get_decision_not_exists(self, mock_session):
        """Test getting decision that doesn't exist yet."""
        session_id = uuid4()
        mock_session.decision = None  # No decision yet!

        with patch('app.api.llm_council.LLMCouncilService') as mock_service_class:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.get_session = AsyncMock(return_value=mock_session)
            mock_service_class.return_value = mock_service

            # Make request
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    f"/api/council/sessions/{session_id}/decision"
                )

            # Verify 404
            assert response.status_code == 404
            data = response.json()
            assert "no decision" in data["detail"].lower()


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_ollama_unavailable(self, mock_session):
        """Test handling when Ollama service is unavailable."""
        session_id = uuid4()

        with patch('app.api.llm_council.LLMCouncilService') as mock_service_class:
            # Setup mock service to raise connection error
            mock_service = AsyncMock()
            mock_service.query_all_models = AsyncMock(
                side_effect=ConnectionError("Ollama service unavailable")
            )
            mock_service_class.return_value = mock_service

            # Make request
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    f"/api/council/sessions/{session_id}/query"
                )

            # Verify error response
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    @pytest.mark.asyncio
    async def test_insufficient_responses(self, mock_session):
        """Test handling when too few models respond."""
        session_id = uuid4()

        # Only 1 response (need at least 2 for meaningful consensus)
        single_response = [MagicMock(spec=CouncilResponse, id=uuid4())]

        with patch('app.api.llm_council.LLMCouncilService') as mock_service_class:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.create_session = AsyncMock(return_value=mock_session)
            mock_service.query_all_models = AsyncMock(return_value=single_response)
            mock_service.peer_review = AsyncMock(return_value=[])
            # Synthesis should fail or return low confidence
            mock_service.synthesize = AsyncMock(
                side_effect=ValueError("Insufficient responses for consensus")
            )
            mock_service_class.return_value = mock_service

            # Make request
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/council/quick",
                    json={
                        "question": "Test question",
                        "context": {},
                        "decision_type": "architecture",
                        "agent_id": "felix"
                    }
                )

            # Verify error or low confidence warning
            assert response.status_code in [400, 500]

    @pytest.mark.asyncio
    async def test_concurrent_stage_execution(self, mock_session):
        """Test that stages cannot be executed concurrently on same session."""
        session_id = uuid4()
        mock_session.status = "reviewing"  # Already in Stage 2

        with patch('app.api.llm_council.LLMCouncilService') as mock_service_class:
            # Setup mock service to raise validation error
            mock_service = AsyncMock()
            mock_service.query_all_models = AsyncMock(
                side_effect=ValueError("Session not in 'pending' status")
            )
            mock_service_class.return_value = mock_service

            # Try to execute Stage 1 while in Stage 2
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    f"/api/council/sessions/{session_id}/query"
                )

            # Verify validation error
            assert response.status_code == 400
            data = response.json()
            assert "status" in data["detail"].lower()


class TestSessionRetrieval:
    """Test session listing and retrieval."""

    @pytest.mark.asyncio
    async def test_list_sessions(self, mock_session):
        """Test listing sessions with filters."""
        mock_sessions = [mock_session, mock_session]

        with patch('app.api.llm_council.LLMCouncilService') as mock_service_class:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.list_sessions = AsyncMock(return_value=mock_sessions)
            mock_service_class.return_value = mock_service

            # Make request
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    "/api/council/sessions",
                    params={
                        "agent_id": "felix",
                        "status_filter": "complete",
                        "page": 1,
                        "page_size": 50
                    }
                )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert "sessions" in data
            assert len(data["sessions"]) == 2
            assert data["page"] == 1
            assert data["page_size"] == 50

    @pytest.mark.asyncio
    async def test_get_session_detail(self, mock_session, mock_responses, mock_decision):
        """Test getting full session detail."""
        session_id = uuid4()
        mock_session.responses = mock_responses
        mock_session.decision = mock_decision

        with patch('app.api.llm_council.LLMCouncilService') as mock_service_class:
            # Setup mock service
            mock_service = AsyncMock()
            mock_service.get_session = AsyncMock(return_value=mock_session)
            mock_service_class.return_value = mock_service

            # Make request
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    f"/api/council/sessions/{session_id}"
                )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert "session" in data
            assert "responses" in data
            assert "decision" in data
            assert len(data["responses"]) == 3
            assert data["decision"]["final_decision"] == mock_decision.final_decision
