"""
ML Training Service for Estimation Models

Trains machine learning models on historical estimation data to provide
ML-enhanced predictions for Function Points and Story Points.

Features:
- Data preparation from historical estimates
- Multiple model types (Linear Regression, Random Forest, Gradient Boosting)
- Model evaluation with cross-validation
- Model persistence and versioning
- ML-enhanced predictions

Author: Claude Code (Week 16 Day 4)
Date: 2025-11-22
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logger = logging.getLogger(__name__)


# ============================================================================
# Model Configuration
# ============================================================================

MODEL_CONFIGS = {
    "linear": {
        "class": LinearRegression,
        "params": {},
        "description": "Simple linear regression baseline"
    },
    "ridge": {
        "class": Ridge,
        "params": {"alpha": 1.0},
        "description": "L2 regularized linear regression"
    },
    "lasso": {
        "class": Lasso,
        "params": {"alpha": 0.1},
        "description": "L1 regularized linear regression"
    },
    "random_forest": {
        "class": RandomForestRegressor,
        "params": {
            "n_estimators": 100,
            "max_depth": 10,
            "min_samples_split": 5,
            "random_state": 42
        },
        "description": "Random Forest ensemble"
    },
    "gradient_boosting": {
        "class": GradientBoostingRegressor,
        "params": {
            "n_estimators": 100,
            "max_depth": 5,
            "learning_rate": 0.1,
            "random_state": 42
        },
        "description": "Gradient Boosting ensemble"
    }
}

# Feature columns for each model type
FP_FEATURES = [
    "ilf_count", "eif_count", "ei_count", "eo_count", "eq_count",
    "low_complexity", "avg_complexity", "high_complexity",
    "unadjusted_fp", "vaf", "adjusted_fp"
]

SP_FEATURES = [
    "technical_complexity", "business_value", "risk_level",
    "uncertainty", "dependencies", "story_points"
]


# ============================================================================
# Data Classes
# ============================================================================

class TrainingResult:
    """Result of model training"""

    def __init__(
        self,
        model_type: str,
        target: str,
        metrics: Dict[str, float],
        feature_importance: Optional[Dict[str, float]] = None,
        cross_val_scores: Optional[List[float]] = None
    ):
        self.model_type = model_type
        self.target = target
        self.metrics = metrics
        self.feature_importance = feature_importance
        self.cross_val_scores = cross_val_scores
        self.trained_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type,
            "target": self.target,
            "metrics": self.metrics,
            "feature_importance": self.feature_importance,
            "cross_val_scores": self.cross_val_scores,
            "trained_at": self.trained_at.isoformat()
        }


class MLPrediction:
    """ML-enhanced prediction result"""

    def __init__(
        self,
        predicted_value: float,
        confidence_interval: Tuple[float, float],
        model_type: str,
        model_version: str,
        features_used: Dict[str, Any]
    ):
        self.predicted_value = predicted_value
        self.confidence_interval = confidence_interval
        self.model_type = model_type
        self.model_version = model_version
        self.features_used = features_used

    def to_dict(self) -> Dict[str, Any]:
        return {
            "predicted_value": round(self.predicted_value, 2),
            "confidence_interval": {
                "low": round(self.confidence_interval[0], 2),
                "high": round(self.confidence_interval[1], 2)
            },
            "model_type": self.model_type,
            "model_version": self.model_version,
            "features_used": self.features_used
        }


# ============================================================================
# ML Training Service
# ============================================================================

class MLTrainingService:
    """
    Service for training and managing estimation ML models.

    Supports:
    - Function Point → Effort Hours prediction
    - Story Points → Effort Hours prediction
    - Multiple model types with automatic selection
    """

    def __init__(self, models_dir: Optional[str] = None):
        """
        Initialize ML Training Service.

        Args:
            models_dir: Directory to store trained models (default: backend/ml_models/)
        """
        if models_dir is None:
            base_dir = Path(__file__).parent.parent.parent
            models_dir = base_dir / "ml_models"

        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.model_versions: Dict[str, str] = {}

        logger.info(f"ML Training Service initialized. Models dir: {self.models_dir}")

    # =========================================================================
    # Data Preparation
    # =========================================================================

    def prepare_fp_training_data(
        self,
        raw_data: List[Dict[str, Any]]
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare Function Point data for training.

        Args:
            raw_data: List of dicts from EstimationHistoryService.get_fp_training_data()

        Returns:
            Tuple of (features DataFrame, target Series)
        """
        if not raw_data:
            raise ValueError("No training data provided")

        df = pd.DataFrame(raw_data)

        # Handle missing values
        for col in FP_FEATURES:
            if col in df.columns:
                df[col] = df[col].fillna(0)
            else:
                df[col] = 0

        # Extract features and target
        X = df[FP_FEATURES].copy()
        y = df["actual_hours"].copy()

        # Remove any rows with missing target
        mask = ~y.isna()
        X = X[mask]
        y = y[mask]

        logger.info(f"Prepared FP training data: {len(X)} samples, {len(FP_FEATURES)} features")
        return X, y

    def prepare_sp_training_data(
        self,
        raw_data: List[Dict[str, Any]]
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare Story Point data for training.

        Args:
            raw_data: List of dicts from EstimationHistoryService.get_sp_training_data()

        Returns:
            Tuple of (features DataFrame, target Series)
        """
        if not raw_data:
            raise ValueError("No training data provided")

        df = pd.DataFrame(raw_data)

        # Handle missing values
        for col in SP_FEATURES:
            if col in df.columns:
                df[col] = df[col].fillna(0)
            else:
                df[col] = 0

        # Extract features and target
        X = df[SP_FEATURES].copy()
        y = df["actual_hours"].copy()

        # Remove any rows with missing target
        mask = ~y.isna()
        X = X[mask]
        y = y[mask]

        logger.info(f"Prepared SP training data: {len(X)} samples, {len(SP_FEATURES)} features")
        return X, y

    # =========================================================================
    # Model Training
    # =========================================================================

    def train_model(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model_type: str = "random_forest",
        target_name: str = "effort_hours",
        test_size: float = 0.2
    ) -> TrainingResult:
        """
        Train a single model.

        Args:
            X: Feature DataFrame
            y: Target Series
            model_type: Type of model (linear, ridge, random_forest, etc.)
            target_name: Name of the target variable
            test_size: Fraction for test split

        Returns:
            TrainingResult with metrics and feature importance
        """
        if model_type not in MODEL_CONFIGS:
            raise ValueError(f"Unknown model type: {model_type}. Available: {list(MODEL_CONFIGS.keys())}")

        config = MODEL_CONFIGS[model_type]

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train model
        model = config["class"](**config["params"])
        model.fit(X_train_scaled, y_train)

        # Predictions
        y_pred = model.predict(X_test_scaled)

        # Calculate metrics
        metrics = {
            "mae": mean_absolute_error(y_test, y_pred),
            "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
            "r2": r2_score(y_test, y_pred),
            "samples_train": len(X_train),
            "samples_test": len(X_test)
        }

        # Cross-validation scores
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring="neg_mean_absolute_error")
        cv_scores = (-cv_scores).tolist()  # Convert to positive MAE

        # Feature importance (if available)
        feature_importance = None
        if hasattr(model, "feature_importances_"):
            feature_importance = dict(zip(X.columns, model.feature_importances_.tolist()))
        elif hasattr(model, "coef_"):
            feature_importance = dict(zip(X.columns, np.abs(model.coef_).tolist()))

        # Store model and scaler
        model_key = f"{target_name}_{model_type}"
        self.models[model_key] = model
        self.scalers[model_key] = scaler

        logger.info(f"Trained {model_type} model for {target_name}: MAE={metrics['mae']:.2f}, R2={metrics['r2']:.3f}")

        return TrainingResult(
            model_type=model_type,
            target=target_name,
            metrics=metrics,
            feature_importance=feature_importance,
            cross_val_scores=cv_scores
        )

    def train_all_models(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        target_name: str = "effort_hours"
    ) -> Dict[str, TrainingResult]:
        """
        Train all available model types and return results.

        Args:
            X: Feature DataFrame
            y: Target Series
            target_name: Name of the target variable

        Returns:
            Dict of model_type -> TrainingResult
        """
        results = {}

        for model_type in MODEL_CONFIGS.keys():
            try:
                result = self.train_model(X, y, model_type, target_name)
                results[model_type] = result
            except Exception as e:
                logger.error(f"Failed to train {model_type}: {e}")
                continue

        return results

    def select_best_model(
        self,
        results: Dict[str, TrainingResult],
        metric: str = "mae"
    ) -> str:
        """
        Select the best model based on a metric.

        Args:
            results: Dict of model_type -> TrainingResult
            metric: Metric to optimize (mae, rmse, r2)

        Returns:
            Name of best model type
        """
        if not results:
            raise ValueError("No training results to evaluate")

        if metric == "r2":
            # Higher is better for R2
            best = max(results.items(), key=lambda x: x[1].metrics.get(metric, 0))
        else:
            # Lower is better for MAE, RMSE
            best = min(results.items(), key=lambda x: x[1].metrics.get(metric, float('inf')))

        logger.info(f"Best model by {metric}: {best[0]} ({metric}={best[1].metrics.get(metric):.3f})")
        return best[0]

    # =========================================================================
    # Model Persistence
    # =========================================================================

    def save_model(
        self,
        model_key: str,
        version: Optional[str] = None
    ) -> str:
        """
        Save a trained model to disk.

        Args:
            model_key: Key of the model (e.g., "effort_hours_random_forest")
            version: Optional version string (default: timestamp)

        Returns:
            Path to saved model
        """
        if model_key not in self.models:
            raise ValueError(f"Model '{model_key}' not found. Train it first.")

        if version is None:
            version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        model_dir = self.models_dir / model_key / version
        model_dir.mkdir(parents=True, exist_ok=True)

        # Save model
        model_path = model_dir / "model.joblib"
        joblib.dump(self.models[model_key], model_path)

        # Save scaler
        if model_key in self.scalers:
            scaler_path = model_dir / "scaler.joblib"
            joblib.dump(self.scalers[model_key], scaler_path)

        # Save metadata
        metadata = {
            "model_key": model_key,
            "version": version,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "model_type": model_key.split("_")[-1] if "_" in model_key else "unknown"
        }
        metadata_path = model_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # Update current version pointer
        self.model_versions[model_key] = version

        # Also save as "latest"
        latest_dir = self.models_dir / model_key / "latest"
        if latest_dir.exists():
            import shutil
            shutil.rmtree(latest_dir)
        import shutil
        shutil.copytree(model_dir, latest_dir)

        logger.info(f"Saved model {model_key} version {version} to {model_dir}")
        return str(model_path)

    def load_model(
        self,
        model_key: str,
        version: str = "latest"
    ) -> bool:
        """
        Load a trained model from disk.

        Args:
            model_key: Key of the model
            version: Version to load (default: "latest")

        Returns:
            True if loaded successfully
        """
        model_dir = self.models_dir / model_key / version

        if not model_dir.exists():
            logger.warning(f"Model directory not found: {model_dir}")
            return False

        try:
            # Load model
            model_path = model_dir / "model.joblib"
            self.models[model_key] = joblib.load(model_path)

            # Load scaler
            scaler_path = model_dir / "scaler.joblib"
            if scaler_path.exists():
                self.scalers[model_key] = joblib.load(scaler_path)

            # Load metadata
            metadata_path = model_dir / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                self.model_versions[model_key] = metadata.get("version", version)

            logger.info(f"Loaded model {model_key} version {version}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model {model_key}: {e}")
            return False

    def list_saved_models(self) -> List[Dict[str, Any]]:
        """List all saved models."""
        models = []

        for model_dir in self.models_dir.iterdir():
            if not model_dir.is_dir():
                continue

            model_key = model_dir.name

            for version_dir in model_dir.iterdir():
                if not version_dir.is_dir():
                    continue

                version = version_dir.name
                metadata_path = version_dir / "metadata.json"

                if metadata_path.exists():
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                else:
                    metadata = {"model_key": model_key, "version": version}

                models.append({
                    **metadata,
                    "path": str(version_dir)
                })

        return models

    # =========================================================================
    # Predictions
    # =========================================================================

    def predict(
        self,
        model_key: str,
        features: Dict[str, Any]
    ) -> MLPrediction:
        """
        Make a prediction using a trained model.

        Args:
            model_key: Key of the model to use
            features: Dict of feature values

        Returns:
            MLPrediction with predicted value and confidence interval
        """
        if model_key not in self.models:
            # Try to load from disk
            if not self.load_model(model_key):
                raise ValueError(f"Model '{model_key}' not found and could not be loaded")

        model = self.models[model_key]
        scaler = self.scalers.get(model_key)

        # Determine feature columns based on model key
        if "fp" in model_key.lower() or "function" in model_key.lower():
            feature_cols = FP_FEATURES
        else:
            feature_cols = SP_FEATURES

        # Prepare features
        X = pd.DataFrame([features])
        for col in feature_cols:
            if col not in X.columns:
                X[col] = 0
        X = X[feature_cols]

        # Scale features
        if scaler:
            X_scaled = scaler.transform(X)
        else:
            X_scaled = X.values

        # Make prediction
        prediction = model.predict(X_scaled)[0]

        # Estimate confidence interval (rough approximation)
        # For tree-based models, use prediction variance
        if hasattr(model, "estimators_"):
            tree_predictions = [tree.predict(X_scaled)[0] for tree in model.estimators_]
            std = np.std(tree_predictions)
            ci_low = prediction - 1.96 * std
            ci_high = prediction + 1.96 * std
        else:
            # For linear models, use rough 20% margin
            ci_low = prediction * 0.8
            ci_high = prediction * 1.2

        return MLPrediction(
            predicted_value=max(0, prediction),
            confidence_interval=(max(0, ci_low), max(0, ci_high)),
            model_type=model_key.split("_")[-1] if "_" in model_key else "unknown",
            model_version=self.model_versions.get(model_key, "unknown"),
            features_used=features
        )

    def predict_fp_effort(
        self,
        fp_result: Dict[str, Any],
        model_type: str = "random_forest"
    ) -> MLPrediction:
        """
        Predict effort hours from Function Point calculation result.

        Args:
            fp_result: Result from FunctionPointCalculator
            model_type: Type of model to use

        Returns:
            MLPrediction with effort hours estimate
        """
        features = {
            "ilf_count": len(fp_result.get("ilf_results", [])),
            "eif_count": len(fp_result.get("eif_results", [])),
            "ei_count": len(fp_result.get("ei_results", [])),
            "eo_count": len(fp_result.get("eo_results", [])),
            "eq_count": len(fp_result.get("eq_results", [])),
            "low_complexity": fp_result.get("summary", {}).get("complexity_distribution", {}).get("low", 0),
            "avg_complexity": fp_result.get("summary", {}).get("complexity_distribution", {}).get("average", 0),
            "high_complexity": fp_result.get("summary", {}).get("complexity_distribution", {}).get("high", 0),
            "unadjusted_fp": fp_result.get("unadjusted_fp", 0),
            "vaf": fp_result.get("vaf", 1.0),
            "adjusted_fp": fp_result.get("adjusted_fp", 0)
        }

        model_key = f"fp_effort_{model_type}"
        return self.predict(model_key, features)

    def predict_sp_effort(
        self,
        sp_result: Dict[str, Any],
        model_type: str = "random_forest"
    ) -> MLPrediction:
        """
        Predict effort hours from Story Point estimation result.

        Args:
            sp_result: Result from Story Point estimation
            model_type: Type of model to use

        Returns:
            MLPrediction with effort hours estimate
        """
        complexity_factors = sp_result.get("complexity_factors", {})

        features = {
            "technical_complexity": complexity_factors.get("technical_complexity", 5),
            "business_value": complexity_factors.get("business_value", 5),
            "risk_level": complexity_factors.get("risk_level", 5),
            "uncertainty": complexity_factors.get("uncertainty", 5),
            "dependencies": complexity_factors.get("dependencies", 0),
            "story_points": sp_result.get("fibonacci_points", sp_result.get("story_points", 0))
        }

        model_key = f"sp_effort_{model_type}"
        return self.predict(model_key, features)


# ============================================================================
# Utility Functions
# ============================================================================

def create_synthetic_training_data(n_samples: int = 100) -> Dict[str, List[Dict[str, Any]]]:
    """
    Create synthetic training data for testing when real data is not available.

    Args:
        n_samples: Number of samples to generate

    Returns:
        Dict with "fp_data" and "sp_data" lists
    """
    np.random.seed(42)

    # Generate FP data
    fp_data = []
    for _ in range(n_samples):
        ilf = np.random.randint(1, 10)
        eif = np.random.randint(0, 5)
        ei = np.random.randint(2, 15)
        eo = np.random.randint(2, 10)
        eq = np.random.randint(1, 8)

        total_components = ilf + eif + ei + eo + eq
        low = int(total_components * np.random.uniform(0.3, 0.5))
        avg = int(total_components * np.random.uniform(0.3, 0.5))
        high = total_components - low - avg

        # Calculate FP (simplified)
        ufp = ilf * 7 + eif * 5 + ei * 4 + eo * 5 + eq * 4
        vaf = np.random.uniform(0.65, 1.35)
        afp = ufp * vaf

        # Simulate actual hours (with some noise)
        base_hours = afp * np.random.uniform(6, 10)  # 6-10 hours per FP
        noise = np.random.normal(0, base_hours * 0.15)
        actual_hours = max(1, base_hours + noise)

        fp_data.append({
            "ilf_count": ilf,
            "eif_count": eif,
            "ei_count": ei,
            "eo_count": eo,
            "eq_count": eq,
            "low_complexity": low,
            "avg_complexity": avg,
            "high_complexity": high,
            "unadjusted_fp": ufp,
            "vaf": round(vaf, 2),
            "adjusted_fp": round(afp, 2),
            "actual_hours": round(actual_hours, 1)
        })

    # Generate SP data
    sp_data = []
    for _ in range(n_samples):
        tech = np.random.randint(1, 10)
        biz = np.random.randint(1, 10)
        risk = np.random.randint(1, 10)
        unc = np.random.randint(1, 10)
        deps = np.random.randint(0, 5)

        # Fibonacci mapping
        complexity_score = (tech + biz + risk + unc) / 4
        fib_scale = [1, 2, 3, 5, 8, 13, 21]
        sp_index = min(int(complexity_score / 1.5), len(fib_scale) - 1)
        story_points = fib_scale[sp_index]

        # Simulate actual hours
        base_hours = story_points * np.random.uniform(3, 6)  # 3-6 hours per SP
        noise = np.random.normal(0, base_hours * 0.2)
        actual_hours = max(1, base_hours + noise)

        sp_data.append({
            "technical_complexity": tech,
            "business_value": biz,
            "risk_level": risk,
            "uncertainty": unc,
            "dependencies": deps,
            "story_points": story_points,
            "actual_hours": round(actual_hours, 1)
        })

    return {"fp_data": fp_data, "sp_data": sp_data}


# ============================================================================
# Singleton Instance
# ============================================================================

_ml_service: Optional[MLTrainingService] = None


def get_ml_training_service() -> MLTrainingService:
    """Get singleton ML Training Service instance."""
    global _ml_service
    if _ml_service is None:
        _ml_service = MLTrainingService()
    return _ml_service
