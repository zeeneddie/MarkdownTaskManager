"""
Estimation History Models for ML Training Data

Stores historical estimation data for machine learning model training:
- Function Point estimates with actuals
- Story Point estimates with actuals
- Project metadata and features

Author: Claude Code (Week 15 Day 5)
Date: 2025-11-21
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, JSON, Text,
    ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


# ============================================================================
# Enums
# ============================================================================

class EstimationType(enum.Enum):
    """Type of estimation performed"""
    FUNCTION_POINTS = "function_points"
    STORY_POINTS = "story_points"
    COMBINED = "combined"


class ProjectComplexity(enum.Enum):
    """Overall project complexity category"""
    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"


class TechStack(enum.Enum):
    """Technology stack categories"""
    WEB_FRONTEND = "web_frontend"
    WEB_BACKEND = "web_backend"
    FULLSTACK = "fullstack"
    MOBILE_NATIVE = "mobile_native"
    MOBILE_HYBRID = "mobile_hybrid"
    API_ONLY = "api_only"
    MICROSERVICES = "microservices"
    DATA_PIPELINE = "data_pipeline"
    ML_AI = "ml_ai"
    EMBEDDED = "embedded"
    OTHER = "other"


# ============================================================================
# Project Metadata Model
# ============================================================================

class EstimationProject(Base):
    """
    Project metadata for estimation tracking.
    Links multiple estimations to a single project for ML correlation.
    """
    __tablename__ = "estimation_projects"

    id = Column(Integer, primary_key=True, index=True)

    # Project identification
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    external_id = Column(String(100), nullable=True, index=True)  # Jira, GitHub, etc.

    # Project characteristics (features for ML)
    tech_stack = Column(String(50), nullable=True)  # Using String for simpler migration
    team_size = Column(Integer, nullable=True)  # Number of developers
    experience_level = Column(Float, nullable=True)  # 1.0-5.0 (junior to expert)
    domain_complexity = Column(Float, nullable=True)  # 1.0-5.0
    has_legacy_integration = Column(Boolean, default=False)
    has_external_apis = Column(Boolean, default=False)
    is_greenfield = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    function_point_estimates = relationship(
        "FunctionPointEstimate",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    story_point_estimates = relationship(
        "StoryPointEstimate",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<EstimationProject(id={self.id}, name='{self.name}')>"


# ============================================================================
# Function Point Estimate Model
# ============================================================================

class FunctionPointEstimate(Base):
    """
    Historical Function Point estimation data.
    Stores both the estimate and (optionally) actual results for ML training.
    """
    __tablename__ = "function_point_estimates"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("estimation_projects.id"), nullable=True)

    # Input features (what was provided for estimation)
    input_project_name = Column(String(255), nullable=False)

    # Component counts (key ML features)
    ilf_count = Column(Integer, default=0)  # Internal Logical Files
    eif_count = Column(Integer, default=0)  # External Interface Files
    ei_count = Column(Integer, default=0)   # External Inputs
    eo_count = Column(Integer, default=0)   # External Outputs
    eq_count = Column(Integer, default=0)   # External Queries

    # Complexity distribution
    low_complexity_count = Column(Integer, default=0)
    average_complexity_count = Column(Integer, default=0)
    high_complexity_count = Column(Integer, default=0)

    # Calculated results
    unadjusted_fp = Column(Integer, nullable=False)
    vaf = Column(Float, default=1.0)  # Value Adjustment Factor
    adjusted_fp = Column(Float, nullable=False)

    # VAF breakdown (optional)
    vaf_applied = Column(Boolean, default=False)
    gsc_ratings = Column(JSON, nullable=True)  # 14 GSC ratings if VAF applied

    # Full request/response for debugging
    full_request = Column(JSON, nullable=True)  # Complete input
    full_response = Column(JSON, nullable=True)  # Complete output

    # Actuals (filled in later for ML training)
    actual_effort_hours = Column(Float, nullable=True)
    actual_person_days = Column(Float, nullable=True)
    actual_duration_days = Column(Integer, nullable=True)  # Calendar days
    actual_team_size = Column(Integer, nullable=True)
    actual_completion_date = Column(DateTime, nullable=True)

    # Derived metrics (for ML validation)
    estimation_accuracy = Column(Float, nullable=True)  # % accuracy vs actual

    # Metadata
    estimated_at = Column(DateTime, default=datetime.utcnow, index=True)
    actuals_recorded_at = Column(DateTime, nullable=True)
    source = Column(String(50), default="api")  # api, ui, import

    # Relationships
    project = relationship("EstimationProject", back_populates="function_point_estimates")

    def __repr__(self):
        return f"<FunctionPointEstimate(id={self.id}, ufp={self.unadjusted_fp}, afp={self.adjusted_fp})>"


# ============================================================================
# Story Point Estimate Model
# ============================================================================

class StoryPointEstimate(Base):
    """
    Historical Story Point estimation data.
    Stores both the estimate and (optionally) actual results for ML training.
    """
    __tablename__ = "story_point_estimates"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("estimation_projects.id"), nullable=True)

    # Input features (what was provided for estimation)
    input_story_title = Column(String(500), nullable=False)
    input_story_description = Column(Text, nullable=True)

    # Complexity factors (1-10 scale, key ML features)
    technical_complexity = Column(Integer, nullable=False)
    business_value = Column(Integer, nullable=False)
    risk_level = Column(Integer, nullable=False)
    uncertainty = Column(Integer, nullable=False)
    dependencies = Column(Integer, nullable=False)

    # PERT inputs (optional)
    pert_optimistic = Column(Float, nullable=True)
    pert_most_likely = Column(Float, nullable=True)
    pert_pessimistic = Column(Float, nullable=True)
    pert_expected = Column(Float, nullable=True)  # Calculated (O + 4M + P) / 6
    pert_std_dev = Column(Float, nullable=True)   # Calculated (P - O) / 6

    # Calculated results
    story_points = Column(Integer, nullable=False)  # Fibonacci: 1,2,3,5,8,13,21
    confidence = Column(Float, nullable=False)  # 0-100%
    confidence_range_low = Column(Integer, nullable=True)
    confidence_range_high = Column(Integer, nullable=True)

    # Risk assessment
    risk_factors = Column(JSON, nullable=True)  # List of identified risks
    recommendations = Column(JSON, nullable=True)  # Suggested actions

    # Full request/response for debugging
    full_request = Column(JSON, nullable=True)
    full_response = Column(JSON, nullable=True)

    # Actuals (filled in later for ML training)
    actual_effort_hours = Column(Float, nullable=True)
    actual_person_days = Column(Float, nullable=True)
    actual_duration_days = Column(Integer, nullable=True)
    actual_story_points = Column(Integer, nullable=True)  # Retrospective assessment
    actual_completion_date = Column(DateTime, nullable=True)

    # Derived metrics
    estimation_accuracy = Column(Float, nullable=True)
    velocity_factor = Column(Float, nullable=True)  # actual_hours / story_points

    # Metadata
    estimated_at = Column(DateTime, default=datetime.utcnow, index=True)
    actuals_recorded_at = Column(DateTime, nullable=True)
    source = Column(String(50), default="api")

    # Relationships
    project = relationship("EstimationProject", back_populates="story_point_estimates")

    def __repr__(self):
        return f"<StoryPointEstimate(id={self.id}, sp={self.story_points}, confidence={self.confidence})>"


# ============================================================================
# ML Model Metadata
# ============================================================================

class MLModelVersion(Base):
    """
    Tracks ML model versions and their performance metrics.
    Used for model selection and A/B testing.
    """
    __tablename__ = "ml_model_versions"

    id = Column(Integer, primary_key=True, index=True)

    # Model identification
    model_name = Column(String(100), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    model_type = Column(String(50), nullable=False)  # linear_regression, random_forest, etc.

    # Training metadata
    training_samples = Column(Integer, nullable=False)
    training_date = Column(DateTime, default=datetime.utcnow)
    features_used = Column(JSON, nullable=False)  # List of feature names
    hyperparameters = Column(JSON, nullable=True)

    # Performance metrics
    mae = Column(Float, nullable=True)  # Mean Absolute Error
    rmse = Column(Float, nullable=True)  # Root Mean Square Error
    r2_score = Column(Float, nullable=True)  # R-squared
    mape = Column(Float, nullable=True)  # Mean Absolute Percentage Error

    # Validation metrics
    cv_scores = Column(JSON, nullable=True)  # Cross-validation scores
    test_mae = Column(Float, nullable=True)
    test_rmse = Column(Float, nullable=True)

    # Model state
    is_active = Column(Boolean, default=False)  # Currently in production
    model_path = Column(String(500), nullable=True)  # Path to serialized model

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)
    deactivated_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<MLModelVersion(id={self.id}, name='{self.model_name}', version='{self.version}')>"
