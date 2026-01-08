# backend/tests/api/week124/test_causality_model_api.py
"""
API Tests for BERT Model Management - Week 124

Tests:
- GET /api/causality/model/status
- POST /api/causality/model/load
- POST /api/causality/model/fine-tune
- POST /api/causality/model/calibrate
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

from app.main import app


@pytest.fixture
def mock_cira_service():
    """Mock the CiRA service."""
    with patch("app.api.causality.CiRAService") as mock:
        instance = mock.return_value
        instance.get_model_status = AsyncMock(return_value={
            "is_loaded": False,
            "model_name": "bert-base-cased",
            "model_path": None,
            "device": "cpu",
            "temperature": 1.0,
            "max_length": 128,
            "batch_size": 16,
            "metadata": None,
            "config": {
                "CIRA_ENABLED": True,
                "CIRA_USE_BERT": True,
                "CIRA_USE_POS_TAGS": False,
                "CIRA_CONFIDENCE_THRESHOLD": 0.6,
            }
        })
        instance.ensure_model_loaded = AsyncMock()
        instance.fine_tune_model = AsyncMock(return_value={
            "epochs": 3,
            "final_train_accuracy": 0.85,
            "final_val_accuracy": 0.82,
            "best_val_accuracy": 0.83,
            "f1_score": 0.80,
            "saved_to": "/tmp/model"
        })
        instance.calibrate_confidence = AsyncMock(return_value={
            "optimal_temperature": 1.5,
            "calibration_samples": 100,
            "project_id": 1
        })
        yield instance


class TestModelStatusEndpoint:
    """Test GET /api/causality/model/status endpoint."""

    @pytest.mark.asyncio
    async def test_get_model_status(self, mock_cira_service):
        """Test getting model status."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/causality/model/status")

        assert response.status_code == 200
        data = response.json()
        assert "is_loaded" in data
        assert "model_name" in data
        assert "device" in data
        assert "config" in data

    @pytest.mark.asyncio
    async def test_model_status_fields(self, mock_cira_service):
        """Test that model status contains all expected fields."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/causality/model/status")

        data = response.json()

        expected_fields = [
            "is_loaded", "model_name", "model_path", "device",
            "temperature", "max_length", "batch_size", "metadata", "config"
        ]

        for field in expected_fields:
            assert field in data, f"Missing field: {field}"


class TestModelLoadEndpoint:
    """Test POST /api/causality/model/load endpoint."""

    @pytest.mark.asyncio
    async def test_load_model(self, mock_cira_service):
        """Test loading the model."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/causality/model/load")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_load_model_calls_service(self, mock_cira_service):
        """Test that load endpoint calls service method."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            await client.post("/api/causality/model/load")

        mock_cira_service.ensure_model_loaded.assert_called_once()


class TestFineTuneEndpoint:
    """Test POST /api/causality/model/fine-tune endpoint."""

    @pytest.mark.asyncio
    async def test_fine_tune_success(self, mock_cira_service):
        """Test successful fine-tuning."""
        request_data = {
            "project_id": 1,
            "use_validated_only": True,
            "epochs": 3,
            "learning_rate": 2e-5
        }

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/causality/model/fine-tune",
                json=request_data
            )

        assert response.status_code == 200
        data = response.json()
        assert data["epochs"] == 3
        assert "final_train_accuracy" in data
        assert "final_val_accuracy" in data
        assert "f1_score" in data

    @pytest.mark.asyncio
    async def test_fine_tune_validation(self, mock_cira_service):
        """Test fine-tune request validation."""
        # Invalid epochs
        request_data = {
            "project_id": 1,
            "epochs": 20  # Max is 10
        }

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/causality/model/fine-tune",
                json=request_data
            )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_fine_tune_insufficient_data(self, mock_cira_service):
        """Test fine-tuning with insufficient data."""
        mock_cira_service.fine_tune_model = AsyncMock(
            side_effect=ValueError("Not enough training data")
        )

        request_data = {
            "project_id": 1,
            "epochs": 3
        }

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/causality/model/fine-tune",
                json=request_data
            )

        assert response.status_code == 400
        assert "Not enough training data" in response.json()["detail"]


class TestCalibrateEndpoint:
    """Test POST /api/causality/model/calibrate endpoint."""

    @pytest.mark.asyncio
    async def test_calibrate_success(self, mock_cira_service):
        """Test successful calibration."""
        request_data = {"project_id": 1}

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/causality/model/calibrate",
                json=request_data
            )

        assert response.status_code == 200
        data = response.json()
        assert "optimal_temperature" in data
        assert "calibration_samples" in data
        assert data["project_id"] == 1

    @pytest.mark.asyncio
    async def test_calibrate_insufficient_data(self, mock_cira_service):
        """Test calibration with insufficient data."""
        mock_cira_service.calibrate_confidence = AsyncMock(
            side_effect=ValueError("Not enough data for calibration")
        )

        request_data = {"project_id": 1}

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/causality/model/calibrate",
                json=request_data
            )

        assert response.status_code == 400
        assert "Not enough data" in response.json()["detail"]


class TestCausalMarkersEndpoint:
    """Test GET /api/causality/causal-markers endpoint."""

    @pytest.mark.asyncio
    async def test_get_causal_markers(self):
        """Test getting causal markers."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/causality/causal-markers")

        assert response.status_code == 200
        data = response.json()
        assert "markers" in data
        assert "total" in data
        assert isinstance(data["markers"], list)
        assert data["total"] == len(data["markers"])

    @pytest.mark.asyncio
    async def test_markers_content(self):
        """Test that markers contain expected keywords."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/causality/causal-markers")

        markers = response.json()["markers"]

        # Check for common causal markers
        expected = ["if", "when", "because", "therefore", "causes"]
        for marker in expected:
            assert marker in markers, f"Missing expected marker: {marker}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
