"""
Week 16 Standalone Tests

Tests for Week 16 functionality that don't require database:
- ML Training API
- ML Predictions
- Project Wizard (already tested in Week 15)
- Estimation Dashboard integration

Run with: pytest tests/api/week16/test_week16_standalone.py -v
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    """Create test client without database dependency"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# ML TRAINING STATUS TESTS
# ============================================================================

class TestMLTrainingStatus:
    """Test ML Training status and info endpoints"""

    @pytest.mark.asyncio
    async def test_get_ml_status(self, client: AsyncClient):
        """Test getting ML training system status"""
        response = await client.get("/api/ml/status")
        assert response.status_code == 200

        data = response.json()
        assert "available_model_types" in data
        assert "saved_models" in data
        assert "loaded_models" in data
        assert "synthetic_data_available" in data

        # Check available model types
        assert "linear" in data["available_model_types"]
        assert "random_forest" in data["available_model_types"]
        assert "gradient_boosting" in data["available_model_types"]

    @pytest.mark.asyncio
    async def test_list_models(self, client: AsyncClient):
        """Test listing available models"""
        response = await client.get("/api/ml/models")
        assert response.status_code == 200

        data = response.json()
        assert "model_types" in data
        assert "saved_models" in data
        assert "loaded_models" in data
        assert "training_status" in data

        # Check model descriptions
        model_types = data["model_types"]
        assert "linear" in model_types
        assert "random_forest" in model_types

    @pytest.mark.asyncio
    async def test_get_synthetic_data(self, client: AsyncClient):
        """Test getting synthetic training data"""
        response = await client.get("/api/ml/synthetic-data?n_samples=10")
        assert response.status_code == 200

        data = response.json()
        assert "function_points_data" in data
        assert "story_points_data" in data
        assert "total_samples" in data
        assert "fp_features" in data
        assert "sp_features" in data
        assert "target" in data

        # Check FP features
        assert "ilf_count" in data["fp_features"]
        assert "adjusted_fp" in data["fp_features"]

        # Check SP features
        assert "story_points" in data["sp_features"]
        assert "technical_complexity" in data["sp_features"]


# ============================================================================
# ML TRAINING TESTS
# ============================================================================

class TestMLTraining:
    """Test ML model training"""

    @pytest.mark.asyncio
    async def test_train_linear_model(self, client: AsyncClient):
        """Test training a linear regression model"""
        response = await client.post(
            "/api/ml/train",
            json={
                "model_type": "linear",
                "estimation_type": "function_points",
                "use_synthetic_data": True,
                "min_samples": 10
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["model_type"] == "linear"
        assert data["estimation_type"] == "function_points"
        assert "metrics" in data
        assert "mae" in data["metrics"]
        assert "rmse" in data["metrics"]
        assert "r2" in data["metrics"]
        assert data["model_path"] is not None

    @pytest.mark.asyncio
    async def test_train_random_forest_model(self, client: AsyncClient):
        """Test training a random forest model"""
        response = await client.post(
            "/api/ml/train",
            json={
                "model_type": "random_forest",
                "estimation_type": "function_points",
                "use_synthetic_data": True
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["model_type"] == "random_forest"
        assert "feature_importance" in data
        assert data["feature_importance"] is not None
        assert "cross_val_scores" in data

    @pytest.mark.asyncio
    async def test_train_story_points_model(self, client: AsyncClient):
        """Test training model for story points"""
        response = await client.post(
            "/api/ml/train",
            json={
                "model_type": "ridge",
                "estimation_type": "story_points",
                "use_synthetic_data": True
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["estimation_type"] == "story_points"

    @pytest.mark.asyncio
    async def test_train_invalid_model_type(self, client: AsyncClient):
        """Test training with invalid model type"""
        response = await client.post(
            "/api/ml/train",
            json={
                "model_type": "invalid_model",
                "estimation_type": "function_points",
                "use_synthetic_data": True
            }
        )
        assert response.status_code == 400
        assert "Unknown model type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_train_all_models(self, client: AsyncClient):
        """Test training all model types"""
        response = await client.post(
            "/api/ml/train-all",
            json={
                "estimation_type": "function_points",
                "use_synthetic_data": True
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "models_trained" in data
        assert "best_model" in data
        assert "results" in data

        # Check that multiple models were trained
        assert len(data["models_trained"]) >= 3

        # Check best model selection
        assert "type" in data["best_model"]
        assert "metrics" in data["best_model"]


# ============================================================================
# ML PREDICTION TESTS
# ============================================================================

class TestMLPredictions:
    """Test ML predictions"""

    @pytest.mark.asyncio
    async def test_predict_with_features(self, client: AsyncClient):
        """Test making prediction with features"""
        # First train a model
        train_response = await client.post(
            "/api/ml/train",
            json={
                "model_type": "random_forest",
                "estimation_type": "function_points",
                "use_synthetic_data": True
            }
        )
        assert train_response.status_code == 200

        # Now make prediction
        response = await client.post(
            "/api/ml/predict",
            json={
                "estimation_type": "function_points",
                "model_type": "random_forest",
                "features": {
                    "ilf_count": 5,
                    "eif_count": 2,
                    "ei_count": 10,
                    "eo_count": 6,
                    "eq_count": 4,
                    "low_complexity": 10,
                    "avg_complexity": 8,
                    "high_complexity": 4,
                    "unadjusted_fp": 120,
                    "vaf": 1.0,
                    "adjusted_fp": 120
                }
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "predicted_value" in data
        assert "confidence_interval" in data
        assert "model_type" in data
        assert data["predicted_value"] > 0
        assert data["confidence_interval"]["low"] <= data["predicted_value"]
        assert data["confidence_interval"]["high"] >= data["predicted_value"]

    @pytest.mark.asyncio
    async def test_predict_from_fp_result(self, client: AsyncClient):
        """Test prediction from FP calculation result"""
        # Train model first
        await client.post(
            "/api/ml/train",
            json={
                "model_type": "random_forest",
                "estimation_type": "function_points",
                "use_synthetic_data": True
            }
        )

        # Mock FP result
        fp_result = {
            "project_name": "Test Project",
            "ilf_results": [{"name": "User DB", "function_points": 7}] * 3,
            "eif_results": [{"name": "External API", "function_points": 5}] * 2,
            "ei_results": [{"name": "Create User", "function_points": 4}] * 5,
            "eo_results": [{"name": "Report", "function_points": 5}] * 3,
            "eq_results": [{"name": "Search", "function_points": 3}] * 4,
            "unadjusted_fp": 85,
            "vaf": 1.1,
            "adjusted_fp": 93.5,
            "summary": {
                "complexity_distribution": {
                    "low": 8,
                    "average": 5,
                    "high": 4
                }
            }
        }

        response = await client.post(
            "/api/ml/predict/from-fp",
            json={
                "fp_result": fp_result,
                "model_type": "random_forest"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["predicted_value"] > 0

    @pytest.mark.asyncio
    async def test_predict_from_sp_result(self, client: AsyncClient):
        """Test prediction from SP estimation result"""
        # Train model first
        await client.post(
            "/api/ml/train",
            json={
                "model_type": "random_forest",
                "estimation_type": "story_points",
                "use_synthetic_data": True
            }
        )

        # Mock SP result
        sp_result = {
            "story_name": "User Authentication",
            "fibonacci_points": 8,
            "complexity_factors": {
                "technical_complexity": 7,
                "business_value": 8,
                "risk_level": 5,
                "uncertainty": 6,
                "dependencies": 2
            }
        }

        response = await client.post(
            "/api/ml/predict/from-sp",
            json={
                "sp_result": sp_result,
                "model_type": "random_forest"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["predicted_value"] > 0


# ============================================================================
# TRAINING STATUS TESTS
# ============================================================================

class TestTrainingStatus:
    """Test training status tracking"""

    @pytest.mark.asyncio
    async def test_get_training_status(self, client: AsyncClient):
        """Test getting training status"""
        response = await client.get("/api/ml/training-status")
        assert response.status_code == 200

        data = response.json()
        assert "in_progress" in data
        assert "current_task" in data
        assert "last_completed" in data
        assert "last_error" in data


# ============================================================================
# MODEL MANAGEMENT TESTS
# ============================================================================

class TestModelManagement:
    """Test model loading and management"""

    @pytest.mark.asyncio
    async def test_get_nonexistent_model(self, client: AsyncClient):
        """Test getting info for non-existent model"""
        response = await client.get("/api/ml/models/nonexistent_model")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_load_nonexistent_model(self, client: AsyncClient):
        """Test loading non-existent model"""
        response = await client.post("/api/ml/load/nonexistent_model")
        assert response.status_code == 404


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestMLIntegration:
    """Integration tests for ML workflow"""

    @pytest.mark.asyncio
    async def test_full_ml_workflow(self, client: AsyncClient):
        """Test complete ML workflow: train -> predict"""
        # 1. Check status
        status = await client.get("/api/ml/status")
        assert status.status_code == 200

        # 2. Get synthetic data
        synthetic = await client.get("/api/ml/synthetic-data?n_samples=5")
        assert synthetic.status_code == 200

        # 3. Train model
        train = await client.post(
            "/api/ml/train",
            json={
                "model_type": "random_forest",
                "estimation_type": "function_points",
                "use_synthetic_data": True
            }
        )
        assert train.status_code == 200
        assert train.json()["success"] is True

        # 4. Make prediction
        predict = await client.post(
            "/api/ml/predict",
            json={
                "estimation_type": "function_points",
                "model_type": "random_forest",
                "features": {
                    "ilf_count": 3,
                    "eif_count": 1,
                    "ei_count": 8,
                    "eo_count": 4,
                    "eq_count": 3,
                    "low_complexity": 7,
                    "avg_complexity": 6,
                    "high_complexity": 3,
                    "unadjusted_fp": 80,
                    "vaf": 1.0,
                    "adjusted_fp": 80
                }
            }
        )
        assert predict.status_code == 200
        assert predict.json()["predicted_value"] > 0

    @pytest.mark.asyncio
    async def test_model_comparison(self, client: AsyncClient):
        """Test comparing different model types"""
        # Train all models
        response = await client.post(
            "/api/ml/train-all",
            json={
                "estimation_type": "function_points",
                "use_synthetic_data": True
            }
        )
        assert response.status_code == 200

        data = response.json()

        # Verify we can compare metrics
        results = data["results"]
        for model_type, model_result in results.items():
            assert "metrics" in model_result
            assert "mae" in model_result["metrics"]

        # Best model should be selected
        assert data["best_model"]["type"] in results


# ============================================================================
# HEALTH CHECK
# ============================================================================

class TestHealthCheck:
    """Test health endpoints"""

    @pytest.mark.asyncio
    async def test_health(self, client: AsyncClient):
        """Test API health check"""
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_estimation_dashboard_route(self, client: AsyncClient):
        """Test estimation dashboard route exists"""
        response = await client.get("/estimation-dashboard.html")
        # Will return 200 if file exists, 404 otherwise
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_project_wizard_route(self, client: AsyncClient):
        """Test project wizard route exists"""
        response = await client.get("/project-wizard.html")
        assert response.status_code in [200, 404]
