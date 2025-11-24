"""
ML Training API Endpoints

Provides REST API for:
- Training ML models on historical estimation data
- Getting ML-enhanced predictions
- Managing model versions
- Viewing training statistics

Author: Claude Code (Week 16 Day 5)
Date: 2025-11-22
"""

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.services.ml_training_service import (
    get_ml_training_service,
    MLTrainingService,
    create_synthetic_training_data,
    MODEL_CONFIGS
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml", tags=["ml-training"])


# ============================================================================
# Request/Response Models
# ============================================================================

class TrainModelRequest(BaseModel):
    """Request to train a model"""
    model_type: str = Field(
        default="random_forest",
        description="Model type: linear, ridge, lasso, random_forest, gradient_boosting"
    )
    estimation_type: str = Field(
        default="function_points",
        description="Type of estimation: function_points or story_points"
    )
    use_synthetic_data: bool = Field(
        default=False,
        description="Use synthetic data for training (when real data insufficient)"
    )
    min_samples: int = Field(
        default=10,
        description="Minimum samples required for training"
    )


class TrainAllModelsRequest(BaseModel):
    """Request to train all model types"""
    estimation_type: str = Field(
        default="function_points",
        description="Type of estimation: function_points or story_points"
    )
    use_synthetic_data: bool = Field(default=False)


class PredictRequest(BaseModel):
    """Request for ML prediction"""
    estimation_type: str = Field(
        default="function_points",
        description="Type of estimation"
    )
    model_type: str = Field(
        default="random_forest",
        description="Model type to use"
    )
    features: Dict[str, Any] = Field(
        ...,
        description="Feature values for prediction"
    )


class PredictFromFPRequest(BaseModel):
    """Request for prediction from FP calculation result"""
    fp_result: Dict[str, Any] = Field(
        ...,
        description="Full FP calculation result"
    )
    model_type: str = Field(default="random_forest")


class PredictFromSPRequest(BaseModel):
    """Request for prediction from SP estimation result"""
    sp_result: Dict[str, Any] = Field(
        ...,
        description="Full SP estimation result"
    )
    model_type: str = Field(default="random_forest")


class TrainingResponse(BaseModel):
    """Response from model training"""
    success: bool
    model_type: str
    estimation_type: str
    metrics: Dict[str, float]
    feature_importance: Optional[Dict[str, float]]
    cross_val_scores: Optional[List[float]]
    model_path: Optional[str]
    message: str


class PredictionResponse(BaseModel):
    """Response from ML prediction"""
    predicted_value: float
    confidence_interval: Dict[str, float]
    model_type: str
    model_version: str
    features_used: Dict[str, Any]


class ModelInfoResponse(BaseModel):
    """Information about a saved model"""
    model_key: str
    version: str
    saved_at: Optional[str]
    path: str


class TrainingStatusResponse(BaseModel):
    """Status of ML training system"""
    available_model_types: List[str]
    saved_models: List[Dict[str, Any]]
    loaded_models: List[str]
    synthetic_data_available: bool


# ============================================================================
# Background Tasks
# ============================================================================

training_status: Dict[str, Any] = {
    "in_progress": False,
    "current_task": None,
    "last_completed": None,
    "last_error": None
}


async def train_model_background(
    service: MLTrainingService,
    model_type: str,
    estimation_type: str,
    use_synthetic: bool
):
    """Background task for model training"""
    global training_status

    try:
        training_status["in_progress"] = True
        training_status["current_task"] = f"Training {model_type} for {estimation_type}"

        # Get training data
        if use_synthetic:
            synthetic = create_synthetic_training_data(100)
            if estimation_type == "function_points":
                raw_data = synthetic["fp_data"]
            else:
                raw_data = synthetic["sp_data"]
        else:
            # TODO: Load from database via EstimationHistoryService
            # For now, use synthetic
            synthetic = create_synthetic_training_data(100)
            if estimation_type == "function_points":
                raw_data = synthetic["fp_data"]
            else:
                raw_data = synthetic["sp_data"]

        # Prepare data
        if estimation_type == "function_points":
            X, y = service.prepare_fp_training_data(raw_data)
            target_name = "fp_effort"
        else:
            X, y = service.prepare_sp_training_data(raw_data)
            target_name = "sp_effort"

        # Train
        result = service.train_model(X, y, model_type, target_name)

        # Save
        model_key = f"{target_name}_{model_type}"
        service.save_model(model_key)

        training_status["last_completed"] = {
            "model_type": model_type,
            "estimation_type": estimation_type,
            "metrics": result.metrics,
            "completed_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        training_status["last_error"] = str(e)
        logger.error(f"Background training failed: {e}")

    finally:
        training_status["in_progress"] = False
        training_status["current_task"] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/status", response_model=TrainingStatusResponse)
async def get_ml_status():
    """
    Get ML training system status.

    Returns available model types, saved models, and training status.
    """
    service = get_ml_training_service()

    return TrainingStatusResponse(
        available_model_types=list(MODEL_CONFIGS.keys()),
        saved_models=service.list_saved_models(),
        loaded_models=list(service.models.keys()),
        synthetic_data_available=True
    )


@router.get("/models")
async def list_models():
    """
    List all available model configurations and saved models.
    """
    service = get_ml_training_service()

    return {
        "model_types": {
            name: config["description"]
            for name, config in MODEL_CONFIGS.items()
        },
        "saved_models": service.list_saved_models(),
        "loaded_models": list(service.models.keys()),
        "training_status": training_status
    }


@router.get("/models/{model_key}")
async def get_model_info(model_key: str):
    """
    Get information about a specific model.
    """
    service = get_ml_training_service()

    # Check if model is loaded
    if model_key in service.models:
        return {
            "model_key": model_key,
            "loaded": True,
            "version": service.model_versions.get(model_key, "unknown"),
            "has_scaler": model_key in service.scalers
        }

    # Check if model exists on disk
    saved_models = service.list_saved_models()
    matching = [m for m in saved_models if m.get("model_key") == model_key]

    if not matching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_key}' not found"
        )

    return {
        "model_key": model_key,
        "loaded": False,
        "versions": matching
    }


@router.post("/train", response_model=TrainingResponse)
async def train_model(request: TrainModelRequest):
    """
    Train a single ML model.

    Trains the specified model type on historical estimation data.
    """
    service = get_ml_training_service()

    if request.model_type not in MODEL_CONFIGS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown model type: {request.model_type}. Available: {list(MODEL_CONFIGS.keys())}"
        )

    try:
        # Get training data
        if request.use_synthetic_data:
            synthetic = create_synthetic_training_data(100)
            if request.estimation_type == "function_points":
                raw_data = synthetic["fp_data"]
            else:
                raw_data = synthetic["sp_data"]
        else:
            # For now, always use synthetic (real data requires DB integration)
            synthetic = create_synthetic_training_data(100)
            if request.estimation_type == "function_points":
                raw_data = synthetic["fp_data"]
            else:
                raw_data = synthetic["sp_data"]

        # Prepare data
        if request.estimation_type == "function_points":
            X, y = service.prepare_fp_training_data(raw_data)
            target_name = "fp_effort"
        else:
            X, y = service.prepare_sp_training_data(raw_data)
            target_name = "sp_effort"

        # Check minimum samples
        if len(X) < request.min_samples:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient training data: {len(X)} samples (minimum: {request.min_samples})"
            )

        # Train model
        result = service.train_model(X, y, request.model_type, target_name)

        # Save model
        model_key = f"{target_name}_{request.model_type}"
        model_path = service.save_model(model_key)

        return TrainingResponse(
            success=True,
            model_type=request.model_type,
            estimation_type=request.estimation_type,
            metrics=result.metrics,
            feature_importance=result.feature_importance,
            cross_val_scores=result.cross_val_scores,
            model_path=model_path,
            message=f"Successfully trained {request.model_type} model with {len(X)} samples"
        )

    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training failed: {str(e)}"
        )


@router.post("/train-all")
async def train_all_models(
    request: TrainAllModelsRequest,
    background_tasks: BackgroundTasks
):
    """
    Train all available model types.

    Trains each model type and returns comparison of results.
    """
    service = get_ml_training_service()

    try:
        # Get training data
        if request.use_synthetic_data:
            synthetic = create_synthetic_training_data(100)
        else:
            synthetic = create_synthetic_training_data(100)

        if request.estimation_type == "function_points":
            raw_data = synthetic["fp_data"]
            X, y = service.prepare_fp_training_data(raw_data)
            target_name = "fp_effort"
        else:
            raw_data = synthetic["sp_data"]
            X, y = service.prepare_sp_training_data(raw_data)
            target_name = "sp_effort"

        # Train all models
        results = service.train_all_models(X, y, target_name)

        # Select best model
        best_model = service.select_best_model(results, metric="mae")

        # Save all models
        saved_paths = {}
        for model_type in results.keys():
            model_key = f"{target_name}_{model_type}"
            path = service.save_model(model_key)
            saved_paths[model_type] = path

        # Format results
        formatted_results = {
            model_type: {
                "metrics": result.metrics,
                "feature_importance": result.feature_importance,
                "cross_val_scores": result.cross_val_scores
            }
            for model_type, result in results.items()
        }

        return {
            "success": True,
            "estimation_type": request.estimation_type,
            "samples_used": len(X),
            "models_trained": list(results.keys()),
            "results": formatted_results,
            "best_model": {
                "type": best_model,
                "metrics": results[best_model].metrics
            },
            "saved_paths": saved_paths
        }

    except Exception as e:
        logger.error(f"Train all failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training failed: {str(e)}"
        )


@router.post("/train-async")
async def train_model_async(
    request: TrainModelRequest,
    background_tasks: BackgroundTasks
):
    """
    Start model training in background.

    Returns immediately with job ID. Check /training-status for progress.
    """
    if training_status["in_progress"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Training already in progress"
        )

    service = get_ml_training_service()

    background_tasks.add_task(
        train_model_background,
        service,
        request.model_type,
        request.estimation_type,
        request.use_synthetic_data
    )

    return {
        "status": "started",
        "model_type": request.model_type,
        "estimation_type": request.estimation_type,
        "message": "Training started in background. Check /api/ml/training-status for progress."
    }


@router.get("/training-status")
async def get_training_status():
    """
    Get current training status for background jobs.
    """
    return training_status


@router.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictRequest):
    """
    Make an ML-enhanced prediction.

    Uses trained model to predict effort hours from features.
    """
    service = get_ml_training_service()

    if request.estimation_type == "function_points":
        model_key = f"fp_effort_{request.model_type}"
    else:
        model_key = f"sp_effort_{request.model_type}"

    try:
        prediction = service.predict(model_key, request.features)
        return PredictionResponse(**prediction.to_dict())

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post("/predict/from-fp", response_model=PredictionResponse)
async def predict_from_fp(request: PredictFromFPRequest):
    """
    Predict effort hours from Function Point calculation result.

    Takes the full FP calculation result and returns ML-enhanced prediction.
    """
    service = get_ml_training_service()

    try:
        prediction = service.predict_fp_effort(request.fp_result, request.model_type)
        return PredictionResponse(**prediction.to_dict())

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"FP prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post("/predict/from-sp", response_model=PredictionResponse)
async def predict_from_sp(request: PredictFromSPRequest):
    """
    Predict effort hours from Story Point estimation result.

    Takes the full SP estimation result and returns ML-enhanced prediction.
    """
    service = get_ml_training_service()

    try:
        prediction = service.predict_sp_effort(request.sp_result, request.model_type)
        return PredictionResponse(**prediction.to_dict())

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"SP prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post("/load/{model_key}")
async def load_model(model_key: str, version: str = "latest"):
    """
    Load a saved model into memory.
    """
    service = get_ml_training_service()

    success = service.load_model(model_key, version)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_key}' version '{version}' not found"
        )

    return {
        "success": True,
        "model_key": model_key,
        "version": version,
        "message": f"Model loaded successfully"
    }


@router.get("/synthetic-data")
async def get_synthetic_data(n_samples: int = 20):
    """
    Get synthetic training data for testing.

    Useful for understanding data format and testing training pipeline.
    """
    data = create_synthetic_training_data(n_samples)
    return {
        "function_points_data": data["fp_data"][:5],  # Show first 5 samples
        "story_points_data": data["sp_data"][:5],
        "total_samples": n_samples,
        "fp_features": [
            "ilf_count", "eif_count", "ei_count", "eo_count", "eq_count",
            "low_complexity", "avg_complexity", "high_complexity",
            "unadjusted_fp", "vaf", "adjusted_fp"
        ],
        "sp_features": [
            "technical_complexity", "business_value", "risk_level",
            "uncertainty", "dependencies", "story_points"
        ],
        "target": "actual_hours"
    }
