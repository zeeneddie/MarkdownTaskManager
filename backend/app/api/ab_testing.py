"""
A/B Testing REST API

Endpoints for experiment management, traffic allocation,
result tracking, and statistical analysis.
"""

from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.ab_testing_service import ABTestingService


# ========== PYDANTIC SCHEMAS ==========

class VariantCreateRequest(BaseModel):
    """Request schema for creating an experiment variant."""

    variant_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    traffic_percentage: float = Field(..., ge=0, le=100)
    config_json: Dict = Field(default_factory=dict)
    is_control: bool = Field(default=False)

    class Config:
        json_schema_extra = {
            "example": {
                "variant_name": "control",
                "description": "Baseline configuration",
                "traffic_percentage": 50.0,
                "config_json": {"timeout": 30, "retries": 3},
                "is_control": True
            }
        }


class ExperimentCreateRequest(BaseModel):
    """Request schema for creating an A/B test experiment."""

    agent_id: str = Field(..., min_length=1, max_length=50)
    feature_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    variants: List[VariantCreateRequest] = Field(..., min_items=2)

    @field_validator("variants")
    @classmethod
    def validate_variants(cls, variants: List[VariantCreateRequest]) -> List[VariantCreateRequest]:
        """Validate variants configuration."""
        # Check traffic percentages sum to 100
        total_traffic = sum(v.traffic_percentage for v in variants)
        if abs(total_traffic - 100.0) > 0.01:
            raise ValueError(
                f"Traffic percentages must sum to 100, got {total_traffic}"
            )

        # Check exactly one control
        control_count = sum(1 for v in variants if v.is_control)
        if control_count != 1:
            raise ValueError(
                f"Exactly one control variant required, got {control_count}"
            )

        return variants

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "felix",
                "feature_name": "async_processing",
                "description": "Test async vs sync processing for feature generation",
                "variants": [
                    {
                        "variant_name": "control",
                        "traffic_percentage": 50.0,
                        "config_json": {"mode": "sync"},
                        "is_control": True
                    },
                    {
                        "variant_name": "async_variant",
                        "traffic_percentage": 50.0,
                        "config_json": {"mode": "async"},
                        "is_control": False
                    }
                ]
            }
        }


class CompleteExperimentRequest(BaseModel):
    """Request schema for completing an experiment."""

    winner_variant_id: UUID

    class Config:
        json_schema_extra = {
            "example": {
                "winner_variant_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class LogResultRequest(BaseModel):
    """Request schema for logging an experiment result."""

    variant_id: UUID
    task_id: str = Field(..., min_length=1, max_length=100)
    work_type: Optional[str] = Field(None, max_length=50)
    success: bool
    metrics: Dict = Field(default_factory=dict)
    error_message: Optional[str] = Field(None, max_length=2000)

    class Config:
        json_schema_extra = {
            "example": {
                "variant_id": "123e4567-e89b-12d3-a456-426614174000",
                "task_id": "task_12345",
                "work_type": "NEW_FEATURE",
                "success": True,
                "metrics": {
                    "success_rate": 0.95,
                    "execution_time_ms": 1500,
                    "code_quality_score": 8.5,
                    "retry_count": 0
                }
            }
        }


class VariantResponse(BaseModel):
    """Response schema for experiment variant."""

    id: str
    experiment_id: str
    variant_name: str
    description: Optional[str]
    traffic_percentage: float
    config_json: Dict
    is_control: bool
    created_at: str

    class Config:
        from_attributes = True


class ExperimentResponse(BaseModel):
    """Response schema for experiment."""

    id: str
    agent_id: str
    feature_name: str
    description: Optional[str]
    status: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    winner_variant_id: Optional[str]
    variants: List[VariantResponse]

    class Config:
        from_attributes = True


class ExperimentResultResponse(BaseModel):
    """Response schema for experiment result."""

    id: str
    variant_id: str
    task_id: str
    work_type: Optional[str]
    success: bool
    metrics_json: Dict
    error_message: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class AnalysisResponse(BaseModel):
    """Response schema for experiment analysis."""

    experiment_id: str
    variant_statistics: Dict
    p_value: Optional[float]
    recommended_winner: Optional[str]
    consensus_level: float
    min_samples_reached: bool

    class Config:
        json_schema_extra = {
            "example": {
                "experiment_id": "123e4567-e89b-12d3-a456-426614174000",
                "variant_statistics": {
                    "variant_a_id": {
                        "variant_name": "control",
                        "sample_size": 150,
                        "success_rate": 0.85,
                        "confidence_interval": {"lower": 0.79, "upper": 0.91}
                    },
                    "variant_b_id": {
                        "variant_name": "async_variant",
                        "sample_size": 150,
                        "success_rate": 0.92,
                        "confidence_interval": {"lower": 0.87, "upper": 0.97}
                    }
                },
                "p_value": 0.012,
                "recommended_winner": "variant_b_id",
                "consensus_level": 0.988,
                "min_samples_reached": True
            }
        }


class TrafficAllocationResponse(BaseModel):
    """Response schema for traffic allocation."""

    variant_id: str
    variant_name: str
    config_json: Dict

    class Config:
        json_schema_extra = {
            "example": {
                "variant_id": "123e4567-e89b-12d3-a456-426614174000",
                "variant_name": "async_variant",
                "config_json": {"mode": "async"}
            }
        }


# ========== API ROUTER ==========

router = APIRouter(
    prefix="/api/evolution",
    tags=["A/B Testing"]
)


async def get_ab_testing_service(
    db: AsyncSession = Depends(get_db)
) -> ABTestingService:
    """Dependency injection for ABTestingService."""
    return ABTestingService(db)


@router.post(
    "/experiments",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_experiment(
    request: ExperimentCreateRequest,
    service: ABTestingService = Depends(get_ab_testing_service)
):
    """
    Create a new A/B test experiment.

    Creates an experiment with multiple variants for testing
    different configurations of an agent feature.

    **Requirements:**
    - At least 2 variants
    - Traffic percentages must sum to 100
    - Exactly one control variant

    **Returns:**
    - Created experiment with all variants
    """
    try:
        variants_data = [v.model_dump() for v in request.variants]

        experiment = await service.create_experiment(
            agent_id=request.agent_id,
            feature_name=request.feature_name,
            description=request.description,
            variants=variants_data
        )

        return ExperimentResponse(
            id=str(experiment.id),
            agent_id=experiment.agent_id,
            feature_name=experiment.feature_name,
            description=experiment.description,
            status=experiment.status,
            created_at=experiment.created_at.isoformat(),
            started_at=experiment.started_at.isoformat() if experiment.started_at else None,
            completed_at=experiment.completed_at.isoformat() if experiment.completed_at else None,
            winner_variant_id=str(experiment.winner_variant_id) if experiment.winner_variant_id else None,
            variants=[
                VariantResponse(
                    id=str(v.id),
                    experiment_id=str(v.experiment_id),
                    variant_name=v.variant_name,
                    description=v.description,
                    traffic_percentage=v.traffic_percentage,
                    config_json=v.config_json,
                    is_control=v.is_control,
                    created_at=v.created_at.isoformat()
                )
                for v in experiment.variants
            ]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/experiments", response_model=List[ExperimentResponse])
async def list_experiments(
    agent_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    service: ABTestingService = Depends(get_ab_testing_service)
):
    """
    List experiments with optional filters.

    **Filters:**
    - `agent_id`: Filter by agent (e.g., "felix", "marcus")
    - `status_filter`: Filter by status (DRAFT, ACTIVE, PAUSED, COMPLETED, CANCELLED)

    **Returns:**
    - List of experiments, newest first
    """
    experiments = await service.list_experiments(
        agent_id=agent_id,
        status=status_filter
    )

    return [
        ExperimentResponse(
            id=str(exp.id),
            agent_id=exp.agent_id,
            feature_name=exp.feature_name,
            description=exp.description,
            status=exp.status,
            created_at=exp.created_at.isoformat(),
            started_at=exp.started_at.isoformat() if exp.started_at else None,
            completed_at=exp.completed_at.isoformat() if exp.completed_at else None,
            winner_variant_id=str(exp.winner_variant_id) if exp.winner_variant_id else None,
            variants=[
                VariantResponse(
                    id=str(v.id),
                    experiment_id=str(v.experiment_id),
                    variant_name=v.variant_name,
                    description=v.description,
                    traffic_percentage=v.traffic_percentage,
                    config_json=v.config_json,
                    is_control=v.is_control,
                    created_at=v.created_at.isoformat()
                )
                for v in exp.variants
            ]
        )
        for exp in experiments
    ]


@router.get("/experiments/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: UUID,
    service: ABTestingService = Depends(get_ab_testing_service)
):
    """
    Get experiment by ID.

    **Returns:**
    - Experiment with all variants
    """
    experiment = await service.get_experiment(experiment_id)

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found"
        )

    return ExperimentResponse(
        id=str(experiment.id),
        agent_id=experiment.agent_id,
        feature_name=experiment.feature_name,
        description=experiment.description,
        status=experiment.status,
        created_at=experiment.created_at.isoformat(),
        started_at=experiment.started_at.isoformat() if experiment.started_at else None,
        completed_at=experiment.completed_at.isoformat() if experiment.completed_at else None,
        winner_variant_id=str(experiment.winner_variant_id) if experiment.winner_variant_id else None,
        variants=[
            VariantResponse(
                id=str(v.id),
                experiment_id=str(v.experiment_id),
                variant_name=v.variant_name,
                description=v.description,
                traffic_percentage=v.traffic_percentage,
                config_json=v.config_json,
                is_control=v.is_control,
                created_at=v.created_at.isoformat()
            )
            for v in experiment.variants
        ]
    )


@router.put("/experiments/{experiment_id}/start", response_model=ExperimentResponse)
async def start_experiment(
    experiment_id: UUID,
    service: ABTestingService = Depends(get_ab_testing_service)
):
    """
    Start an experiment (DRAFT → ACTIVE).

    Once started, traffic will be allocated and results tracked.

    **Returns:**
    - Updated experiment
    """
    try:
        experiment = await service.start_experiment(experiment_id)

        return ExperimentResponse(
            id=str(experiment.id),
            agent_id=experiment.agent_id,
            feature_name=experiment.feature_name,
            description=experiment.description,
            status=experiment.status,
            created_at=experiment.created_at.isoformat(),
            started_at=experiment.started_at.isoformat() if experiment.started_at else None,
            completed_at=experiment.completed_at.isoformat() if experiment.completed_at else None,
            winner_variant_id=str(experiment.winner_variant_id) if experiment.winner_variant_id else None,
            variants=[
                VariantResponse(
                    id=str(v.id),
                    experiment_id=str(v.experiment_id),
                    variant_name=v.variant_name,
                    description=v.description,
                    traffic_percentage=v.traffic_percentage,
                    config_json=v.config_json,
                    is_control=v.is_control,
                    created_at=v.created_at.isoformat()
                )
                for v in experiment.variants
            ]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/experiments/{experiment_id}/pause", response_model=ExperimentResponse)
async def pause_experiment(
    experiment_id: UUID,
    service: ABTestingService = Depends(get_ab_testing_service)
):
    """
    Pause an active experiment (ACTIVE → PAUSED).

    Temporarily stops traffic allocation while preserving results.

    **Returns:**
    - Updated experiment
    """
    try:
        experiment = await service.pause_experiment(experiment_id)

        return ExperimentResponse(
            id=str(experiment.id),
            agent_id=experiment.agent_id,
            feature_name=experiment.feature_name,
            description=experiment.description,
            status=experiment.status,
            created_at=experiment.created_at.isoformat(),
            started_at=experiment.started_at.isoformat() if experiment.started_at else None,
            completed_at=experiment.completed_at.isoformat() if experiment.completed_at else None,
            winner_variant_id=str(experiment.winner_variant_id) if experiment.winner_variant_id else None,
            variants=[
                VariantResponse(
                    id=str(v.id),
                    experiment_id=str(v.experiment_id),
                    variant_name=v.variant_name,
                    description=v.description,
                    traffic_percentage=v.traffic_percentage,
                    config_json=v.config_json,
                    is_control=v.is_control,
                    created_at=v.created_at.isoformat()
                )
                for v in experiment.variants
            ]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/experiments/{experiment_id}/complete", response_model=ExperimentResponse)
async def complete_experiment(
    experiment_id: UUID,
    request: CompleteExperimentRequest,
    service: ABTestingService = Depends(get_ab_testing_service)
):
    """
    Complete an experiment and declare winner (ACTIVE/PAUSED → COMPLETED).

    **Returns:**
    - Updated experiment with winner declared
    """
    try:
        experiment = await service.complete_experiment(
            experiment_id=experiment_id,
            winner_variant_id=request.winner_variant_id
        )

        return ExperimentResponse(
            id=str(experiment.id),
            agent_id=experiment.agent_id,
            feature_name=experiment.feature_name,
            description=experiment.description,
            status=experiment.status,
            created_at=experiment.created_at.isoformat(),
            started_at=experiment.started_at.isoformat() if experiment.started_at else None,
            completed_at=experiment.completed_at.isoformat() if experiment.completed_at else None,
            winner_variant_id=str(experiment.winner_variant_id) if experiment.winner_variant_id else None,
            variants=[
                VariantResponse(
                    id=str(v.id),
                    experiment_id=str(v.experiment_id),
                    variant_name=v.variant_name,
                    description=v.description,
                    traffic_percentage=v.traffic_percentage,
                    config_json=v.config_json,
                    is_control=v.is_control,
                    created_at=v.created_at.isoformat()
                )
                for v in experiment.variants
            ]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/experiments/{experiment_id}/results", response_model=ExperimentResultResponse)
async def log_result(
    experiment_id: UUID,
    request: LogResultRequest,
    service: ABTestingService = Depends(get_ab_testing_service)
):
    """
    Log a result from a variant execution.

    **Returns:**
    - Created result record
    """
    try:
        result = await service.log_result(
            variant_id=request.variant_id,
            task_id=request.task_id,
            success=request.success,
            metrics=request.metrics,
            work_type=request.work_type,
            error_message=request.error_message
        )

        return ExperimentResultResponse(
            id=str(result.id),
            variant_id=str(result.variant_id),
            task_id=result.task_id,
            work_type=result.work_type,
            success=result.success,
            metrics_json=result.metrics_json,
            error_message=result.error_message,
            created_at=result.created_at.isoformat()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log result: {str(e)}"
        )


@router.get("/experiments/{experiment_id}/analysis", response_model=AnalysisResponse)
async def analyze_experiment(
    experiment_id: UUID,
    service: ABTestingService = Depends(get_ab_testing_service)
):
    """
    Perform statistical analysis on experiment results.

    Calculates:
    - Sample size per variant
    - Success rate per variant
    - Confidence intervals (95%)
    - P-value (t-test)
    - Recommended winner (if statistically significant)
    - Consensus level (confidence in winner)

    **Returns:**
    - Complete statistical analysis
    """
    try:
        analysis = await service.analyze_experiment(experiment_id)
        return AnalysisResponse(**analysis)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/experiments/{experiment_id}/allocate", response_model=TrafficAllocationResponse)
async def allocate_traffic(
    experiment_id: UUID,
    task_id: str,
    service: ABTestingService = Depends(get_ab_testing_service)
):
    """
    Allocate a task to a variant.

    Uses deterministic sticky assignment - same task always gets same variant.

    **Returns:**
    - Assigned variant with configuration
    """
    try:
        variant = await service.allocate_traffic(
            experiment_id=experiment_id,
            task_id=task_id
        )

        return TrafficAllocationResponse(
            variant_id=str(variant.id),
            variant_name=variant.variant_name,
            config_json=variant.config_json
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
