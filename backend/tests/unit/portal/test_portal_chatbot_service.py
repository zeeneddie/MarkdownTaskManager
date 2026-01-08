# backend/tests/services/week121/test_portal_chatbot_service.py
"""
Tests for Portal Chatbot Service - Week 121

Tests conversational interface with Peter/Diana agents.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.chatbot_journey import (
    ChatSession, ChatMessage, ChatSessionStatus, ChatRole,
    ChatIntent, ChatAgent, INTENT_PATTERNS
)
from app.services.portal_chatbot_service import PortalChatbotService


class TestIntentPatternMatching:
    """Test intent pattern matching without LLM."""

    def test_status_query_patterns(self):
        """Test status query intent detection."""
        service = PortalChatbotService(MagicMock())

        test_cases = [
            ("Wat is de status van #123?", ChatIntent.STATUS_QUERY.value),
            ("Waar staat mijn feature?", ChatIntent.STATUS_QUERY.value),
            ("Voortgang van feature 456", ChatIntent.STATUS_QUERY.value),
            ("Progress van mijn request", ChatIntent.STATUS_QUERY.value),
        ]

        for message, expected_intent in test_cases:
            intent, confidence = service._pattern_match_intent(message)
            assert intent == expected_intent, f"Failed for: {message}"
            assert confidence > 0.5

    def test_eta_query_patterns(self):
        """Test ETA query intent detection."""
        service = PortalChatbotService(MagicMock())

        test_cases = [
            ("Wanneer is mijn feature klaar?", ChatIntent.ETA_QUERY.value),
            ("How long until #123?", ChatIntent.ETA_QUERY.value),
            ("Hoe lang duurt het nog?", ChatIntent.ETA_QUERY.value),
            ("Deadline voor feature 456?", ChatIntent.ETA_QUERY.value),
        ]

        for message, expected_intent in test_cases:
            intent, confidence = service._pattern_match_intent(message)
            assert intent == expected_intent, f"Failed for: {message}"

    def test_new_request_patterns(self):
        """Test new request intent detection."""
        service = PortalChatbotService(MagicMock())

        test_cases = [
            ("Ik wil een nieuwe feature", ChatIntent.NEW_REQUEST.value),
            ("I want to add dark mode", ChatIntent.NEW_REQUEST.value),
            ("Ik zou graag een export functie", ChatIntent.NEW_REQUEST.value),
            ("Nieuwe feature aanvragen", ChatIntent.NEW_REQUEST.value),
        ]

        for message, expected_intent in test_cases:
            intent, confidence = service._pattern_match_intent(message)
            assert intent == expected_intent, f"Failed for: {message}"

    def test_help_patterns(self):
        """Test help intent detection."""
        service = PortalChatbotService(MagicMock())

        test_cases = [
            ("Help me please", ChatIntent.HELP.value),
            ("Hulp nodig", ChatIntent.HELP.value),
            ("Hoe werkt dit?", ChatIntent.HELP.value),
            ("Wat kan ik hier doen?", ChatIntent.HELP.value),
        ]

        for message, expected_intent in test_cases:
            intent, confidence = service._pattern_match_intent(message)
            assert intent == expected_intent, f"Failed for: {message}"

    def test_general_fallback(self):
        """Test general intent for unmatched messages."""
        service = PortalChatbotService(MagicMock())

        intent, confidence = service._pattern_match_intent("Random unrelated text xyz")
        assert intent == ChatIntent.GENERAL.value
        assert confidence < 0.5


class TestEntityExtraction:
    """Test entity extraction from messages."""

    def test_extract_feature_id_with_hash(self):
        """Test extraction of feature ID with # prefix."""
        service = PortalChatbotService(MagicMock())

        entities = service._extract_entities("Status van #123?", ChatIntent.STATUS_QUERY.value)
        assert entities.get("feature_id") == 123

    def test_extract_feature_id_with_word(self):
        """Test extraction of feature ID with 'feature' word."""
        service = PortalChatbotService(MagicMock())

        entities = service._extract_entities("Update on feature 456", ChatIntent.STATUS_QUERY.value)
        assert entities.get("feature_id") == 456

    def test_extract_quoted_title(self):
        """Test extraction of quoted feature title."""
        service = PortalChatbotService(MagicMock())

        entities = service._extract_entities('Status van "dark mode toggle"?', ChatIntent.STATUS_QUERY.value)
        assert entities.get("feature_title") == "dark mode toggle"

    def test_no_entities(self):
        """Test no entity extraction for plain messages."""
        service = PortalChatbotService(MagicMock())

        entities = service._extract_entities("Help me please", ChatIntent.HELP.value)
        assert "feature_id" not in entities
        assert "feature_title" not in entities


class TestChatSessionManagement:
    """Test chat session CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_session(self, mock_db_session):
        """Test creating a new chat session."""
        service = PortalChatbotService(mock_db_session)

        session = await service.create_session(
            customer_id="customer-123",
            project_id=1,
        )

        assert session.customer_id == "customer-123"
        assert session.project_id == 1
        assert session.status == ChatSessionStatus.ACTIVE.value
        assert session.primary_agent == ChatAgent.PETER.value
        assert ChatAgent.PETER.value in session.agents_involved
        assert session.message_count == 0
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_session(self, mock_db_session):
        """Test closing a chat session."""
        # Create a mock session
        mock_session = ChatSession(
            id=uuid4(),
            customer_id="customer-123",
            status=ChatSessionStatus.ACTIVE.value,
            primary_agent=ChatAgent.PETER.value,
        )

        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_session)
        ))

        service = PortalChatbotService(mock_db_session)
        session = await service.close_session(mock_session.id, rating=5)

        assert session.status == ChatSessionStatus.CLOSED.value
        assert session.satisfaction_rating == 5
        assert session.closed_at is not None


class TestAgentRouting:
    """Test routing to appropriate agents."""

    @pytest.mark.asyncio
    async def test_status_query_routes_to_diana(self, mock_db_session):
        """Test status query routes to Diana for friendly response."""
        service = PortalChatbotService(mock_db_session)

        agent, response, action_type, action_data = await service._handle_status_query(
            message="Status van #123",
            entities={"feature_id": 123},
            feature_context={"title": "Dark Mode", "status": "testing"},
        )

        assert agent == ChatAgent.DIANA.value
        assert action_type == "show_status"
        assert action_data["feature_id"] == 123

    @pytest.mark.asyncio
    async def test_eta_query_routes_to_eliza(self, mock_db_session):
        """Test ETA query mentions Eliza for estimation."""
        service = PortalChatbotService(mock_db_session)

        agent, response, action_type, action_data = await service._handle_eta_query(
            message="Wanneer is feature klaar?",
            entities={},
            feature_context=None,
        )

        assert agent == ChatAgent.ELIZA.value

    @pytest.mark.asyncio
    async def test_new_request_routes_to_peter(self, mock_db_session):
        """Test new request routes to Peter for classification."""
        service = PortalChatbotService(mock_db_session)

        agent, response, action_type, action_data = await service._handle_new_request(
            message="Ik wil een nieuwe feature",
        )

        assert agent == ChatAgent.PETER.value
        assert action_type == "start_request"

    @pytest.mark.asyncio
    async def test_help_routes_to_diana(self, mock_db_session):
        """Test help request routes to Diana for documentation."""
        service = PortalChatbotService(mock_db_session)

        agent, response, action_type, action_data = await service._handle_help(
            message="Help me please",
        )

        assert agent == ChatAgent.DIANA.value
        assert "Feature Requests" in response
        assert "Informatie" in response


class TestChatStats:
    """Test chatbot statistics."""

    @pytest.mark.asyncio
    async def test_get_stats_empty(self, mock_db_session):
        """Test stats with no sessions."""
        mock_db_session.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        ))

        service = PortalChatbotService(mock_db_session)
        stats = await service.get_chatbot_stats()

        assert stats["total_sessions"] == 0
        assert stats["active_sessions"] == 0
        assert stats["total_messages"] == 0
        assert stats["avg_messages_per_session"] == 0


# ============== FIXTURES ==============

@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    return session
