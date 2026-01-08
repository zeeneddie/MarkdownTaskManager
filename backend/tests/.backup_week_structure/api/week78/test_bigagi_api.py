"""
Tests for BigAGI Beam API - Week 78

Tests REST API endpoints for multi-model validation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone
from httpx import AsyncClient

from app.models.browser_automation import (
    BigAGIValidation,
    BigAGIResponse,
    BigAGIConsensus,
    ValidationStatus,
    ConsensusMethod,
    ConsensusRecommendation
)
from app.services.bigagi_beam_service import ValidationResult


class TestBigAGIAPIValidation:
    """Tests for validation session endpoints."""

    @pytest.mark.asyncio
    async def test_create_validation(self, test_client, mock_db_session):
        """Test POST /api/bigagi/validations"""
        with patch('app.api.bigagi.BigAGIBeamService') as MockService:
            mock_service = MockService.return_value
            mock_service.create_validation = AsyncMock(return_value=BigAGIValidation(
                id=uuid4(),
                task="What database should we use?",
                primary_response="PostgreSQL is recommended...",
                primary_model="claude-3-sonnet",
                validation_models=[{"name": "qwen", "provider": "ollama", "weight": 1.0}],
                status=ValidationStatus.PENDING.value,
                metadata={},
                created_at=datetime.now(timezone.utc)
            ))

            response = await test_client.post(
                "/api/bigagi/validations",
                json={
                    "task": "What database should we use?",
                    "primary_response": "PostgreSQL is recommended...",
                    "primary_model": "claude-3-sonnet"
                }
            )

            assert response.status_code == 201
            data = response.json()
            assert "PostgreSQL" in data["primary_response"]
            assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_validation_with_custom_models(self, test_client, mock_db_session):
        """Test creating validation with custom validator models."""
        with patch('app.api.bigagi.BigAGIBeamService') as MockService:
            mock_service = MockService.return_value
            mock_service.create_validation = AsyncMock(return_value=BigAGIValidation(
                id=uuid4(),
                task="Review code",
                primary_response="Looks good",
                primary_model="test",
                validation_models=[
                    {"name": "gpt-4", "provider": "openai", "weight": 2.0}
                ],
                status=ValidationStatus.PENDING.value,
                metadata={},
                created_at=datetime.now(timezone.utc)
            ))

            response = await test_client.post(
                "/api/bigagi/validations",
                json={
                    "task": "Review code",
                    "primary_response": "Looks good",
                    "primary_model": "test",
                    "validation_models": [
                        {"name": "gpt-4", "provider": "openai", "weight": 2.0}
                    ]
                }
            )

            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_list_validations(self, test_client, mock_db_session):
        """Test GET /api/bigagi/validations"""
        with patch('app.api.bigagi.BigAGIBeamService') as MockService:
            mock_service = MockService.return_value
            mock_service.list_validations = AsyncMock(return_value=[
                BigAGIValidation(
                    id=uuid4(),
                    task="Task 1",
                    primary_response="Response 1",
                    primary_model="model1",
                    validation_models=[],
                    status=ValidationStatus.COMPLETED.value,
                    consensus_score=0.85,
                    consensus_reached=True,
                    metadata={},
                    created_at=datetime.now(timezone.utc)
                ),
                BigAGIValidation(
                    id=uuid4(),
                    task="Task 2",
                    primary_response="Response 2",
                    primary_model="model2",
                    validation_models=[],
                    status=ValidationStatus.PENDING.value,
                    metadata={},
                    created_at=datetime.now(timezone.utc)
                )
            ])

            response = await test_client.get("/api/bigagi/validations")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_validation(self, test_client, mock_db_session):
        """Test GET /api/bigagi/validations/{id}"""
        validation_id = uuid4()

        with patch('app.api.bigagi.BigAGIBeamService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_validation = AsyncMock(return_value=BigAGIValidation(
                id=validation_id,
                task="Test task",
                primary_response="Test response",
                primary_model="test",
                validation_models=[],
                status=ValidationStatus.PENDING.value,
                metadata={},
                created_at=datetime.now(timezone.utc)
            ))

            response = await test_client.get(f"/api/bigagi/validations/{validation_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["task"] == "Test task"

    @pytest.mark.asyncio
    async def test_get_validation_not_found(self, test_client, mock_db_session):
        """Test getting non-existent validation."""
        with patch('app.api.bigagi.BigAGIBeamService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_validation = AsyncMock(return_value=None)

            response = await test_client.get(f"/api/bigagi/validations/{uuid4()}")

            assert response.status_code == 404


class TestBigAGIAPIRunValidation:
    """Tests for running validation."""

    @pytest.mark.asyncio
    async def test_run_validation(self, test_client, mock_db_session):
        """Test POST /api/bigagi/validations/{id}/run"""
        validation_id = uuid4()

        with patch('app.api.bigagi.BigAGIBeamService') as MockService:
            mock_service = MockService.return_value
            mock_service.run_validation = AsyncMock(return_value=ValidationResult(
                validation_id=validation_id,
                consensus_reached=True,
                consensus_score=0.85,
                recommendation="accept",
                final_answer="Validated answer",
                key_agreements=["All models agree on accuracy"],
                key_disagreements=[],
                model_responses={
                    "model1": {"response": "...", "confidence": 0.9, "agreement_score": 0.85}
                }
            ))

            response = await test_client.post(
                f"/api/bigagi/validations/{validation_id}/run",
                json={"consensus_method": "weighted"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["consensus_reached"] is True
            assert data["consensus_score"] == 0.85
            assert data["recommendation"] == "accept"

    @pytest.mark.asyncio
    async def test_run_validation_majority_method(self, test_client, mock_db_session):
        """Test running validation with majority consensus method."""
        validation_id = uuid4()

        with patch('app.api.bigagi.BigAGIBeamService') as MockService:
            mock_service = MockService.return_value
            mock_service.run_validation = AsyncMock(return_value=ValidationResult(
                validation_id=validation_id,
                consensus_reached=True,
                consensus_score=0.75,
                recommendation="review",
                final_answer=None,
                key_agreements=[],
                key_disagreements=[],
                model_responses={}
            ))

            response = await test_client.post(
                f"/api/bigagi/validations/{validation_id}/run",
                json={"consensus_method": "majority"}
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_run_validation_not_found(self, test_client, mock_db_session):
        """Test running non-existent validation."""
        with patch('app.api.bigagi.BigAGIBeamService') as MockService:
            mock_service = MockService.return_value
            mock_service.run_validation = AsyncMock(
                side_effect=ValueError("Validation not found")
            )

            response = await test_client.post(
                f"/api/bigagi/validations/{uuid4()}/run",
                json={"consensus_method": "weighted"}
            )

            assert response.status_code == 404


class TestBigAGIAPIResponses:
    """Tests for response retrieval."""

    @pytest.mark.asyncio
    async def test_get_validation_responses(self, test_client, mock_db_session):
        """Test GET /api/bigagi/validations/{id}/responses"""
        validation_id = uuid4()

        mock_validation = BigAGIValidation(
            id=validation_id,
            task="Test",
            primary_response="Test",
            primary_model="test",
            validation_models=[],
            status=ValidationStatus.COMPLETED.value,
            metadata={},
            created_at=datetime.now(timezone.utc)
        )
        mock_validation.responses = [
            BigAGIResponse(
                id=uuid4(),
                validation_id=validation_id,
                model="qwen2.5-coder:7b",
                provider="ollama",
                response="I agree with this response...",
                confidence=0.85,
                agreement_score=0.8,
                tokens_used=500,
                latency_ms=1200,
                created_at=datetime.now(timezone.utc)
            )
        ]

        with patch('app.api.bigagi.BigAGIBeamService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_validation = AsyncMock(return_value=mock_validation)

            response = await test_client.get(
                f"/api/bigagi/validations/{validation_id}/responses"
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["model"] == "qwen2.5-coder:7b"
            assert data[0]["agreement_score"] == 0.8


class TestBigAGIAPIConsensus:
    """Tests for consensus retrieval."""

    @pytest.mark.asyncio
    async def test_get_validation_consensus(self, test_client, mock_db_session):
        """Test GET /api/bigagi/validations/{id}/consensus"""
        validation_id = uuid4()

        mock_validation = BigAGIValidation(
            id=validation_id,
            task="Test",
            primary_response="Test",
            primary_model="test",
            validation_models=[],
            status=ValidationStatus.COMPLETED.value,
            metadata={},
            created_at=datetime.now(timezone.utc)
        )
        mock_validation.consensus = BigAGIConsensus(
            id=uuid4(),
            validation_id=validation_id,
            method="weighted",
            agreement_matrix={"primary": {"model1": 0.85}},
            key_agreements=["Accuracy confirmed"],
            key_disagreements=[],
            synthesis="The response is validated.",
            confidence=0.85,
            recommendation="accept",
            created_at=datetime.now(timezone.utc)
        )
        mock_validation.responses = []

        with patch('app.api.bigagi.BigAGIBeamService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_validation = AsyncMock(return_value=mock_validation)

            response = await test_client.get(
                f"/api/bigagi/validations/{validation_id}/consensus"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["method"] == "weighted"
            assert data["confidence"] == 0.85
            assert data["recommendation"] == "accept"

    @pytest.mark.asyncio
    async def test_get_consensus_not_calculated(self, test_client, mock_db_session):
        """Test getting consensus when not yet calculated."""
        validation_id = uuid4()

        mock_validation = BigAGIValidation(
            id=validation_id,
            task="Test",
            primary_response="Test",
            primary_model="test",
            validation_models=[],
            status=ValidationStatus.PENDING.value,
            metadata={},
            created_at=datetime.now(timezone.utc)
        )
        mock_validation.consensus = None
        mock_validation.responses = []

        with patch('app.api.bigagi.BigAGIBeamService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_validation = AsyncMock(return_value=mock_validation)

            response = await test_client.get(
                f"/api/bigagi/validations/{validation_id}/consensus"
            )

            assert response.status_code == 404


class TestBigAGIAPIQuickValidate:
    """Tests for quick validation endpoint."""

    @pytest.mark.asyncio
    async def test_quick_validate(self, test_client, mock_db_session):
        """Test POST /api/bigagi/validate"""
        with patch('app.api.bigagi.BigAGIBeamService') as MockService:
            mock_service = MockService.return_value
            mock_service.quick_validate = AsyncMock(return_value={
                "valid": True,
                "score": 0.85,
                "recommendation": "accept",
                "key_issues": []
            })

            response = await test_client.post(
                "/api/bigagi/validate",
                json={
                    "task": "Is this correct?",
                    "response": "Yes, this is correct.",
                    "model_used": "claude-3-sonnet"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["score"] == 0.85


class TestBigAGIAPICouncilIntegration:
    """Tests for LLM Council integration."""

    @pytest.mark.asyncio
    async def test_cross_validate_council(self, test_client, mock_db_session):
        """Test POST /api/bigagi/cross-validate-council"""
        council_session_id = uuid4()

        with patch('app.api.bigagi.BigAGIBeamService') as MockService:
            mock_service = MockService.return_value
            mock_service.cross_validate_council = AsyncMock(return_value={
                "council_session_id": str(council_session_id),
                "validation_id": str(uuid4()),
                "council_consensus": 0.85,
                "beam_consensus": 0.82,
                "beam_recommendation": "accept",
                "cross_validation_passed": True
            })

            response = await test_client.post(
                "/api/bigagi/cross-validate-council",
                json={"council_session_id": str(council_session_id)}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["cross_validation_passed"] is True


class TestBigAGIAPIStats:
    """Tests for statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_stats(self, test_client, mock_db_session):
        """Test GET /api/bigagi/stats"""
        with patch('app.api.bigagi.BigAGIBeamService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_validation_stats = AsyncMock(return_value={
                "total_validations": 100,
                "by_status": {"pending": 5, "completed": 90, "failed": 5},
                "average_consensus_score": 0.78,
                "consensus_reached_rate": 0.85,
                "threshold": 0.7
            })

            response = await test_client.get("/api/bigagi/stats")

            assert response.status_code == 200
            data = response.json()
            assert data["total_validations"] == 100
            assert data["consensus_reached_rate"] == 0.85

    @pytest.mark.asyncio
    async def test_get_consensus_methods(self, test_client, mock_db_session):
        """Test GET /api/bigagi/consensus-methods"""
        response = await test_client.get("/api/bigagi/consensus-methods")

        assert response.status_code == 200
        data = response.json()
        assert "methods" in data
        assert len(data["methods"]) == 3
        assert any(m["name"] == "majority" for m in data["methods"])
        assert any(m["name"] == "weighted" for m in data["methods"])
        assert any(m["name"] == "unanimous" for m in data["methods"])

    @pytest.mark.asyncio
    async def test_get_default_validators(self, test_client, mock_db_session):
        """Test GET /api/bigagi/default-validators"""
        response = await test_client.get("/api/bigagi/default-validators")

        assert response.status_code == 200
        data = response.json()
        assert "validators" in data
        assert len(data["validators"]) > 0
