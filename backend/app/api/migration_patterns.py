# backend/app/api/migration_patterns.py
"""
Database Migration Patterns API - Fase 24 GAP Item D4 (Week 159)

Endpoints for database migration pattern catalog:
- List available migration patterns
- Get pattern details
- Get pattern recommendations
- Assess pattern risk

This API provides access to the centralized database migration
pattern catalog for informed migration strategy decisions.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

from app.services.database_migration_pattern_service import (
    DatabaseMigrationPatternService,
    MigrationPatternType,
    DataVolumeCategory,
    DowntimeRequirement,
    RiskLevel,
)

router = APIRouter(prefix="/api/migration-patterns", tags=["Migration Patterns"])

# Initialize service
_pattern_service = DatabaseMigrationPatternService()


# =============================================================================
# Request/Response Models
# =============================================================================

class PatternRecommendationRequest(BaseModel):
    """Request for pattern recommendations."""
    data_volume: str = Field(
        ...,
        description="Data volume category: small, medium, large, very_large"
    )
    downtime_requirement: str = Field(
        ...,
        description="Downtime tolerance: zero, minimal, short, extended"
    )
    scenario_description: str = Field(
        ...,
        description="Free-text description of the migration scenario"
    )
    source_db_type: Optional[str] = Field(
        None,
        description="Source database type (e.g., Oracle, SQL Server)"
    )
    target_db_type: Optional[str] = Field(
        None,
        description="Target database type (e.g., PostgreSQL)"
    )
    team_size: Optional[int] = Field(
        None,
        ge=1,
        description="Available team size for the migration"
    )
    max_duration_weeks: Optional[float] = Field(
        None,
        gt=0,
        description="Maximum acceptable duration in weeks"
    )


class PatternRiskAssessmentRequest(BaseModel):
    """Request for pattern risk assessment."""
    pattern_type: str = Field(
        ...,
        description="Pattern type to assess"
    )
    data_volume: str = Field(
        ...,
        description="Data volume category: small, medium, large, very_large"
    )
    has_downtime_window: bool = Field(
        ...,
        description="Whether a maintenance window is available"
    )
    team_experience_level: str = Field(
        ...,
        description="Team experience: junior, mid, senior, expert"
    )
    critical_data: bool = Field(
        False,
        description="Whether data is business-critical"
    )
    regulatory_requirements: bool = Field(
        False,
        description="Whether compliance requirements apply"
    )


class PatternSummaryResponse(BaseModel):
    """Summary of a migration pattern."""
    type: str
    name: str
    description: str
    complexity: int
    typical_weeks: float
    team_size: int
    zero_downtime: bool
    risk_count: int


class PatternDetailResponse(BaseModel):
    """Detailed migration pattern response."""
    pattern_type: str
    name: str
    description: str
    suitable_data_volumes: List[str]
    suitable_downtime_requirements: List[str]
    suitable_scenarios: List[str]
    prerequisites: List[Dict[str, Any]]
    phases: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    complexity_score: int
    recommended_team_size: int
    typical_duration_weeks: float
    related_patterns: List[str]
    tools_supported: List[str]
    database_types_supported: List[str]


class RecommendationResponse(BaseModel):
    """Pattern recommendation response."""
    pattern_type: str
    pattern_name: str
    score: float
    reasons: List[str]
    warnings: List[str]
    alternatives: List[str]


class RiskAssessmentResponse(BaseModel):
    """Risk assessment response."""
    pattern_type: str
    overall_risk_level: str
    risk_score: int
    identified_risks: List[Dict[str, Any]]
    mitigations_required: List[str]
    go_no_go_recommendation: str


# =============================================================================
# API Endpoints
# =============================================================================

@router.get("/", response_model=Dict[str, Any])
async def get_patterns_summary() -> Dict[str, Any]:
    """
    Get summary of all available migration patterns.

    Returns catalog statistics and pattern overview.
    """
    return _pattern_service.get_pattern_summary()


@router.get("/list", response_model=List[PatternSummaryResponse])
async def list_patterns(
    zero_downtime_only: bool = Query(
        False,
        description="Filter to only patterns supporting zero downtime"
    ),
    max_complexity: Optional[int] = Query(
        None,
        ge=1,
        le=10,
        description="Maximum complexity score (1-10)"
    )
) -> List[PatternSummaryResponse]:
    """
    List all available migration patterns.

    Optional filters for zero-downtime support and complexity.
    """
    patterns = _pattern_service.list_patterns()

    result = []
    for p in patterns:
        # Apply filters
        if zero_downtime_only:
            if DowntimeRequirement.ZERO not in p.suitable_downtime_requirements:
                continue

        if max_complexity and p.complexity_score > max_complexity:
            continue

        result.append(PatternSummaryResponse(
            type=p.pattern_type.value,
            name=p.name,
            description=p.description[:200] + "..." if len(p.description) > 200 else p.description,
            complexity=p.complexity_score,
            typical_weeks=p.typical_duration_weeks,
            team_size=p.recommended_team_size,
            zero_downtime=DowntimeRequirement.ZERO in p.suitable_downtime_requirements,
            risk_count=len(p.risks)
        ))

    return result


@router.get("/types", response_model=List[str])
async def get_pattern_types() -> List[str]:
    """
    Get all available pattern type identifiers.

    Use these values when querying specific patterns.
    """
    return [pt.value for pt in MigrationPatternType]


@router.get("/{pattern_type}", response_model=PatternDetailResponse)
async def get_pattern(pattern_type: str) -> PatternDetailResponse:
    """
    Get detailed information about a specific migration pattern.

    Args:
        pattern_type: Pattern type identifier (e.g., 'dual_write', 'cdc_sync')
    """
    try:
        pt = MigrationPatternType(pattern_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pattern type: {pattern_type}. "
                   f"Valid types: {[p.value for p in MigrationPatternType]}"
        )

    pattern = _pattern_service.get_pattern(pt)
    if not pattern:
        raise HTTPException(status_code=404, detail=f"Pattern not found: {pattern_type}")

    return PatternDetailResponse(
        pattern_type=pattern.pattern_type.value,
        name=pattern.name,
        description=pattern.description,
        suitable_data_volumes=[dv.value for dv in pattern.suitable_data_volumes],
        suitable_downtime_requirements=[dr.value for dr in pattern.suitable_downtime_requirements],
        suitable_scenarios=pattern.suitable_scenarios,
        prerequisites=[
            {
                "name": p.name,
                "description": p.description,
                "is_required": p.is_required
            }
            for p in pattern.prerequisites
        ],
        phases=[
            {
                "order": ph.order,
                "name": ph.name,
                "description": ph.description,
                "estimated_effort_hours": ph.estimated_effort_hours,
                "rollback_possible": ph.rollback_possible
            }
            for ph in pattern.phases
        ],
        risks=[
            {
                "name": r.name,
                "description": r.description,
                "level": r.level.value,
                "mitigation": r.mitigation
            }
            for r in pattern.risks
        ],
        complexity_score=pattern.complexity_score,
        recommended_team_size=pattern.recommended_team_size,
        typical_duration_weeks=pattern.typical_duration_weeks,
        related_patterns=[rp.value for rp in pattern.related_patterns],
        tools_supported=pattern.tools_supported,
        database_types_supported=pattern.database_types_supported
    )


@router.post("/recommend", response_model=List[RecommendationResponse])
async def recommend_patterns(
    request: PatternRecommendationRequest
) -> List[RecommendationResponse]:
    """
    Get pattern recommendations for a migration scenario.

    Analyzes the provided scenario and returns ranked recommendations
    with scores, reasons, and warnings.
    """
    # Validate and convert enums
    try:
        data_volume = DataVolumeCategory(request.data_volume)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data_volume: {request.data_volume}. "
                   f"Valid values: {[dv.value for dv in DataVolumeCategory]}"
        )

    try:
        downtime_req = DowntimeRequirement(request.downtime_requirement)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid downtime_requirement: {request.downtime_requirement}. "
                   f"Valid values: {[dr.value for dr in DowntimeRequirement]}"
        )

    recommendations = _pattern_service.recommend_pattern(
        data_volume=data_volume,
        downtime_requirement=downtime_req,
        scenario_description=request.scenario_description,
        source_db_type=request.source_db_type,
        target_db_type=request.target_db_type,
        team_size=request.team_size,
        max_duration_weeks=request.max_duration_weeks
    )

    return [
        RecommendationResponse(
            pattern_type=r.pattern.pattern_type.value,
            pattern_name=r.pattern.name,
            score=r.score,
            reasons=r.reasons,
            warnings=r.warnings,
            alternatives=[a.value for a in r.alternatives]
        )
        for r in recommendations
    ]


@router.post("/assess-risk", response_model=RiskAssessmentResponse)
async def assess_pattern_risk(
    request: PatternRiskAssessmentRequest
) -> RiskAssessmentResponse:
    """
    Assess the risk of applying a pattern to a specific scenario.

    Returns comprehensive risk analysis with mitigations and
    go/no-go recommendation.
    """
    # Validate pattern type
    try:
        pattern_type = MigrationPatternType(request.pattern_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pattern_type: {request.pattern_type}. "
                   f"Valid types: {[p.value for p in MigrationPatternType]}"
        )

    # Validate data volume
    try:
        data_volume = DataVolumeCategory(request.data_volume)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data_volume: {request.data_volume}. "
                   f"Valid values: {[dv.value for dv in DataVolumeCategory]}"
        )

    # Validate experience level
    valid_experience = ["junior", "mid", "senior", "expert"]
    if request.team_experience_level not in valid_experience:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid team_experience_level: {request.team_experience_level}. "
                   f"Valid values: {valid_experience}"
        )

    assessment = _pattern_service.assess_pattern_risk(
        pattern_type=pattern_type,
        data_volume=data_volume,
        has_downtime_window=request.has_downtime_window,
        team_experience_level=request.team_experience_level,
        critical_data=request.critical_data,
        regulatory_requirements=request.regulatory_requirements
    )

    if not assessment:
        raise HTTPException(status_code=404, detail=f"Pattern not found: {request.pattern_type}")

    return RiskAssessmentResponse(
        pattern_type=assessment.pattern_type.value,
        overall_risk_level=assessment.overall_risk_level.value,
        risk_score=assessment.risk_score,
        identified_risks=[
            {
                "name": r.name,
                "description": r.description,
                "level": r.level.value,
                "mitigation": r.mitigation
            }
            for r in assessment.identified_risks
        ],
        mitigations_required=assessment.mitigations_required,
        go_no_go_recommendation=assessment.go_no_go_recommendation
    )


@router.get("/scenario/{scenario_type}", response_model=List[PatternSummaryResponse])
async def get_patterns_for_scenario(
    scenario_type: str,
    data_volume: str = Query("medium", description="Data volume category"),
    downtime: str = Query("minimal", description="Downtime requirement")
) -> List[PatternSummaryResponse]:
    """
    Get patterns suitable for common migration scenarios.

    Scenario types:
    - cloud_migration: Moving to cloud databases
    - version_upgrade: Major database version upgrades
    - schema_evolution: Schema changes without full migration
    - platform_change: Cross-platform migrations (e.g., Oracle to PostgreSQL)
    - data_warehouse: Data warehouse/analytics migrations
    """
    # Map scenario types to keywords
    scenario_keywords = {
        "cloud_migration": ["cloud", "platform", "aws", "azure", "gcp"],
        "version_upgrade": ["upgrade", "version", "major"],
        "schema_evolution": ["schema", "column", "table", "restructur"],
        "platform_change": ["cross", "platform", "oracle", "postgresql", "mysql", "sqlserver"],
        "data_warehouse": ["warehouse", "analytics", "bigquery", "snowflake", "archiv"]
    }

    keywords = scenario_keywords.get(scenario_type)
    if not keywords:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario_type: {scenario_type}. "
                   f"Valid types: {list(scenario_keywords.keys())}"
        )

    try:
        dv = DataVolumeCategory(data_volume)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data_volume: {data_volume}"
        )

    try:
        dr = DowntimeRequirement(downtime)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid downtime: {downtime}"
        )

    patterns = _pattern_service.get_patterns_for_scenario(
        data_volume=dv,
        downtime_requirement=dr,
        scenario_keywords=keywords
    )

    return [
        PatternSummaryResponse(
            type=p.pattern_type.value,
            name=p.name,
            description=p.description[:200] + "..." if len(p.description) > 200 else p.description,
            complexity=p.complexity_score,
            typical_weeks=p.typical_duration_weeks,
            team_size=p.recommended_team_size,
            zero_downtime=DowntimeRequirement.ZERO in p.suitable_downtime_requirements,
            risk_count=len(p.risks)
        )
        for p in patterns
    ]
