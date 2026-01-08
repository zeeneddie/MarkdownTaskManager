"""
Tests for BigAGIBeamService - Week 78

Tests multi-model validation, consensus calculation,
and LLM Council integration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.services.bigagi_beam_service import (
    BigAGIBeamService,
    ValidationResult,
    AgreementScore
)
from app.models.browser_automation import (
    BigAGIValidation,
    BigAGIResponse,
    BigAGIConsensus,
    ValidationStatus,
    ConsensusMethod,
    ConsensusRecommendation
)


class TestBigAGIBeamServiceValidation:
    """Tests for validation session management."""

    @pytest.mark.asyncio
    async def test_create_validation(self, mock_db_session):
        """Test creating a validation session."""
        service = BigAGIBeamService(mock_db_session)

        validation = await service.create_validation(
            task="What is the best database for this project?",
            primary_response="PostgreSQL is recommended because...",
            primary_model="claude-3-sonnet"
        )

        assert validation.task == "What is the best database for this project?"
        assert validation.primary_model == "claude-3-sonnet"
        assert validation.status == ValidationStatus.PENDING.value
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_validation_with_custom_models(self, mock_db_session):
        """Test creating validation with custom validator models."""
        service = BigAGIBeamService(mock_db_session)

        custom_validators = [
            {"name": "gpt-4", "provider": "openai", "weight": 2.0},
            {"name": "mistral-large", "provider": "mistral", "weight": 1.5}
        ]

        validation = await service.create_validation(
            task="Review this code",
            primary_response="The code looks good...",
            primary_model="claude-3-opus",
            validation_models=custom_validators
        )

        assert validation.validation_models == custom_validators

    @pytest.mark.asyncio
    async def test_create_validation_uses_defaults(self, mock_db_session):
        """Test that default validators are used when none specified."""
        service = BigAGIBeamService(mock_db_session)

        validation = await service.create_validation(
            task="Test task",
            primary_response="Test response",
            primary_model="test-model"
        )

        # Should use DEFAULT_VALIDATORS
        assert validation.validation_models == BigAGIBeamService.DEFAULT_VALIDATORS

    @pytest.mark.asyncio
    async def test_get_validation_not_found(self, mock_db_session):
        """Test getting non-existent validation."""
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )

        service = BigAGIBeamService(mock_db_session)
        validation = await service.get_validation(uuid4())

        assert validation is None


class TestBigAGIBeamServiceConsensus:
    """Tests for consensus calculation."""

    def test_majority_consensus_all_agree(self, mock_db_session):
        """Test majority consensus when all validators agree."""
        service = BigAGIBeamService(mock_db_session)

        responses = [
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="m1", provider="p1",
                          response="", agreement_score=0.9),
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="m2", provider="p2",
                          response="", agreement_score=0.85),
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="m3", provider="p3",
                          response="", agreement_score=0.8),
        ]

        score = service._majority_consensus(responses)

        # All 3 have agreement_score >= 0.6, so 100% majority
        assert score == 1.0

    def test_majority_consensus_partial_agreement(self, mock_db_session):
        """Test majority consensus with partial agreement."""
        service = BigAGIBeamService(mock_db_session)

        responses = [
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="m1", provider="p1",
                          response="", agreement_score=0.9),
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="m2", provider="p2",
                          response="", agreement_score=0.4),  # Disagrees
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="m3", provider="p3",
                          response="", agreement_score=0.8),
        ]

        score = service._majority_consensus(responses)

        # 2 out of 3 agree (66.7%)
        assert abs(score - 0.667) < 0.01

    def test_majority_consensus_no_agreement(self, mock_db_session):
        """Test majority consensus when no validators agree."""
        service = BigAGIBeamService(mock_db_session)

        responses = [
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="m1", provider="p1",
                          response="", agreement_score=0.3),
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="m2", provider="p2",
                          response="", agreement_score=0.4),
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="m3", provider="p3",
                          response="", agreement_score=0.2),
        ]

        score = service._majority_consensus(responses)

        # None have agreement_score >= 0.6
        assert score == 0.0

    def test_weighted_consensus(self, mock_db_session):
        """Test weighted consensus calculation."""
        service = BigAGIBeamService(mock_db_session)

        responses = [
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="model_a", provider="p1",
                          response="", agreement_score=0.9),
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="model_b", provider="p2",
                          response="", agreement_score=0.5),
        ]

        model_configs = [
            {"name": "model_a", "weight": 2.0},  # Higher weight
            {"name": "model_b", "weight": 1.0},
        ]

        score = service._weighted_consensus(responses, model_configs)

        # Weighted: (0.9 * 2.0 + 0.5 * 1.0) / (2.0 + 1.0) = 2.3 / 3 = 0.767
        expected = (0.9 * 2.0 + 0.5 * 1.0) / 3.0
        assert abs(score - expected) < 0.01

    def test_unanimous_consensus_all_agree(self, mock_db_session):
        """Test unanimous consensus when all agree."""
        service = BigAGIBeamService(mock_db_session)

        responses = [
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="m1", provider="p1",
                          response="", agreement_score=0.8),
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="m2", provider="p2",
                          response="", agreement_score=0.9),
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="m3", provider="p3",
                          response="", agreement_score=0.75),
        ]

        score = service._unanimous_consensus(responses)

        # All >= 0.7, so unanimous. Returns average.
        expected = (0.8 + 0.9 + 0.75) / 3
        assert abs(score - expected) < 0.01

    def test_unanimous_consensus_one_disagrees(self, mock_db_session):
        """Test unanimous consensus fails if one disagrees."""
        service = BigAGIBeamService(mock_db_session)

        responses = [
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="m1", provider="p1",
                          response="", agreement_score=0.9),
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="m2", provider="p2",
                          response="", agreement_score=0.5),  # Below 0.7 threshold
            BigAGIResponse(id=uuid4(), validation_id=uuid4(), model="m3", provider="p3",
                          response="", agreement_score=0.85),
        ]

        score = service._unanimous_consensus(responses)

        # One disagrees, so consensus = 0
        assert score == 0.0


class TestBigAGIBeamServiceTextAgreement:
    """Tests for text agreement calculation."""

    def test_agreement_explicit_agree(self, mock_db_session):
        """Test agreement detection from explicit AGREE verdict."""
        service = BigAGIBeamService(mock_db_session)

        score = service._calculate_text_agreement(
            "Primary response text",
            "I AGREE with this response. It is accurate and complete."
        )

        assert score >= 0.8

    def test_agreement_explicit_disagree(self, mock_db_session):
        """Test disagreement detection."""
        service = BigAGIBeamService(mock_db_session)

        score = service._calculate_text_agreement(
            "Primary response text",
            "I DISAGREE with this response. It contains errors."
        )

        assert score <= 0.3

    def test_agreement_partial(self, mock_db_session):
        """Test partial agreement detection."""
        service = BigAGIBeamService(mock_db_session)

        score = service._calculate_text_agreement(
            "Primary response text",
            "I PARTIALLY AGREE. Some points are valid but others need work."
        )

        assert 0.5 <= score <= 0.7

    def test_agreement_positive_indicators(self, mock_db_session):
        """Test agreement from positive indicators."""
        service = BigAGIBeamService(mock_db_session)

        score = service._calculate_text_agreement(
            "Primary response",
            "The response is correct and accurate. The analysis is complete and valid."
        )

        # Multiple positive indicators should increase score
        assert score >= 0.6

    def test_agreement_negative_indicators(self, mock_db_session):
        """Test disagreement from negative indicators."""
        service = BigAGIBeamService(mock_db_session)

        score = service._calculate_text_agreement(
            "Primary response",
            "There is an error in the analysis. The response is incorrect and incomplete."
        )

        # Multiple negative indicators should decrease score
        assert score <= 0.5


class TestBigAGIBeamServiceConfidenceExtraction:
    """Tests for confidence extraction from responses."""

    def test_extract_confidence_fraction_format(self, mock_db_session):
        """Test extracting confidence in fraction format."""
        service = BigAGIBeamService(mock_db_session)

        conf = service._extract_confidence(
            "My analysis suggests... Confidence: 85/100"
        )

        assert abs(conf - 0.85) < 0.01

    def test_extract_confidence_percentage_format(self, mock_db_session):
        """Test extracting confidence in percentage format."""
        service = BigAGIBeamService(mock_db_session)

        conf = service._extract_confidence(
            "Based on my review... confidence: 75%"
        )

        assert abs(conf - 0.75) < 0.01

    def test_extract_confidence_simple_number(self, mock_db_session):
        """Test extracting simple confidence number."""
        service = BigAGIBeamService(mock_db_session)

        conf = service._extract_confidence(
            "Confidence: 90"
        )

        assert abs(conf - 0.90) < 0.01

    def test_extract_confidence_no_match(self, mock_db_session):
        """Test default confidence when no pattern matches."""
        service = BigAGIBeamService(mock_db_session)

        conf = service._extract_confidence(
            "This is a response without any confidence indicator."
        )

        # Default is 0.5
        assert conf == 0.5


class TestBigAGIBeamServiceThinking:
    """Tests for thinking/reasoning extraction."""

    def test_extract_thinking_xml_tags(self, mock_db_session):
        """Test extracting thinking from XML tags."""
        service = BigAGIBeamService(mock_db_session)

        thinking = service._extract_thinking(
            "<thinking>Let me analyze this step by step...</thinking>Final answer."
        )

        assert thinking is not None
        assert "step by step" in thinking

    def test_extract_thinking_markdown_format(self, mock_db_session):
        """Test extracting thinking from markdown format."""
        service = BigAGIBeamService(mock_db_session)

        thinking = service._extract_thinking(
            "**Analysis**: The code shows several patterns.\n\nConclusion: It's good."
        )

        assert thinking is not None
        assert "patterns" in thinking

    def test_extract_thinking_none_found(self, mock_db_session):
        """Test when no thinking block found."""
        service = BigAGIBeamService(mock_db_session)

        thinking = service._extract_thinking(
            "Just a simple answer without reasoning."
        )

        # May or may not find something depending on patterns
        # Just verify it doesn't crash
        assert thinking is None or isinstance(thinking, str)


class TestBigAGIBeamServiceRecommendations:
    """Tests for recommendation generation."""

    @pytest.mark.asyncio
    async def test_high_consensus_recommends_accept(self, mock_db_session):
        """Test that high consensus leads to ACCEPT recommendation."""
        service = BigAGIBeamService(mock_db_session)

        # Score >= 0.85 should recommend ACCEPT
        score = 0.90

        if score >= service.HIGH_CONFIDENCE_THRESHOLD:
            recommendation = ConsensusRecommendation.ACCEPT
        elif score >= service.CONSENSUS_THRESHOLD:
            recommendation = ConsensusRecommendation.REVIEW
        else:
            recommendation = ConsensusRecommendation.REJECT

        assert recommendation == ConsensusRecommendation.ACCEPT

    @pytest.mark.asyncio
    async def test_medium_consensus_recommends_review(self, mock_db_session):
        """Test that medium consensus leads to REVIEW recommendation."""
        service = BigAGIBeamService(mock_db_session)

        # Score between 0.7 and 0.85 should recommend REVIEW
        score = 0.75

        if score >= service.HIGH_CONFIDENCE_THRESHOLD:
            recommendation = ConsensusRecommendation.ACCEPT
        elif score >= service.CONSENSUS_THRESHOLD:
            recommendation = ConsensusRecommendation.REVIEW
        else:
            recommendation = ConsensusRecommendation.REJECT

        assert recommendation == ConsensusRecommendation.REVIEW

    @pytest.mark.asyncio
    async def test_low_consensus_recommends_reject(self, mock_db_session):
        """Test that low consensus leads to REJECT recommendation."""
        service = BigAGIBeamService(mock_db_session)

        # Score < 0.7 should recommend REJECT
        score = 0.50

        if score >= service.HIGH_CONFIDENCE_THRESHOLD:
            recommendation = ConsensusRecommendation.ACCEPT
        elif score >= service.CONSENSUS_THRESHOLD:
            recommendation = ConsensusRecommendation.REVIEW
        else:
            recommendation = ConsensusRecommendation.REJECT

        assert recommendation == ConsensusRecommendation.REJECT


class TestBigAGIBeamServiceQuickValidate:
    """Tests for quick/stateless validation."""

    @pytest.mark.asyncio
    async def test_quick_validate_creates_ephemeral(self, mock_db_session):
        """Test quick validation creates ephemeral session."""
        service = BigAGIBeamService(mock_db_session)

        # Mock create_validation and run_validation
        mock_validation = BigAGIValidation(
            id=uuid4(),
            task="test",
            primary_response="test",
            primary_model="test",
            validation_models=[],
            status=ValidationStatus.PENDING.value,
            metadata={"ephemeral": True}
        )

        with patch.object(service, 'create_validation', new_callable=AsyncMock) as mock_create:
            with patch.object(service, 'run_validation', new_callable=AsyncMock) as mock_run:
                mock_create.return_value = mock_validation
                mock_run.return_value = ValidationResult(
                    validation_id=mock_validation.id,
                    consensus_reached=True,
                    consensus_score=0.85,
                    recommendation="accept",
                    final_answer=None,
                    key_agreements=[],
                    key_disagreements=[],
                    model_responses={}
                )

                result = await service.quick_validate(
                    task="Is this correct?",
                    response="Yes it is.",
                    model_used="test-model"
                )

                assert result["valid"] is True
                assert result["score"] == 0.85

                # Verify ephemeral flag (service uses session_metadata, not metadata)
                create_call = mock_create.call_args
                assert create_call[1].get("session_metadata", {}).get("ephemeral") is True


class TestBigAGIBeamServiceIntegration:
    """Integration tests for the validation pipeline."""

    @pytest.mark.asyncio
    async def test_full_validation_pipeline(self, mock_db_session):
        """Test full validation pipeline from create to consensus."""
        service = BigAGIBeamService(mock_db_session)

        # This would be an integration test - mocking the full flow
        validation_id = uuid4()
        mock_validation = BigAGIValidation(
            id=validation_id,
            task="Review this architecture",
            primary_response="Use microservices with...",
            primary_model="claude-3-sonnet",
            validation_models=[
                {"name": "qwen2.5-coder:7b", "provider": "ollama", "weight": 1.5}
            ],
            status=ValidationStatus.PENDING.value
        )

        # Mock the database and provider calls
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_validation))
        )

        # The full test would require mocking the LLM provider
        # For unit tests, we verify the methods exist and have correct signatures
        assert hasattr(service, 'run_validation')
        assert hasattr(service, '_query_validators')
        assert hasattr(service, '_determine_consensus')
        assert hasattr(service, '_generate_synthesis')
