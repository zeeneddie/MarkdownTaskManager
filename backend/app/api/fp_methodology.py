# FP Methodology API
# IFPUG CPM 4.3.1 compliant Function Point estimation endpoints
#
# Endpoints:
# - POST /estimate/work-type - Classify work and determine estimation method
# - POST /estimate/enhancement - Calculate Enhancement FP
# - POST /estimate/validate - Validate FP usage for work type
# - GET /estimate/guidance/{work_type} - Get estimation guidance
#
# Architecture: docs/roadmap/phases/fase-22-fp-methodology.md
# Phase: Fase 22 (Week 146-147)

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging

from app.services.fp_methodology import (
    WorkTypeClassifier,
    WorkType,
    WorkTypeClassification,
    EstimationMethod,
    EnhancementFPCalculator,
    EnhancementFPResult,
    FPComponentValidator,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fp", tags=["FP Methodology"])


# === Request/Response Models ===

class WorkTypeClassifyRequest(BaseModel):
    """Request to classify work type."""
    description: str = Field(..., description="Work description to classify")
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context (project type, etc.)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "description": "Brown Paper analyse van ADO leak detection",
                    "context": {"project_type": "analysis"}
                },
                {
                    "description": "Nieuwe bouw klantportaal met React frontend",
                    "context": {"project_type": "development"}
                },
            ]
        }
    }


class WorkTypeClassifyResponse(BaseModel):
    """Response from work type classification."""
    work_type: str
    confidence: float
    fp_applicable: bool
    recommended_method: str
    description: str
    matched_keywords: List[str]
    warnings: List[str]


class EnhancementComponent(BaseModel):
    """A component in an enhancement project."""
    name: str = Field(..., description="Component name")
    type: str = Field(default="EI", description="Component type: EI, EO, EQ")
    complexity: str = Field(default="average", description="Complexity: low, average, high")
    description: str = Field(default="", description="Component description")
    dets: int = Field(default=0, description="Data Element Types")
    ftrs: int = Field(default=0, description="File Types Referenced")
    original_fp: int = Field(default=0, description="Original FP (for deleted components)")


class EnhancementCalculateRequest(BaseModel):
    """Request to calculate Enhancement FP."""
    added: Optional[List[EnhancementComponent]] = Field(
        default=None, description="New functions added"
    )
    changed: Optional[List[EnhancementComponent]] = Field(
        default=None, description="Functions changed (count AFTER change)"
    )
    deleted: Optional[List[EnhancementComponent]] = Field(
        default=None, description="Functions deleted (include original_fp if known)"
    )
    conversion: Optional[List[EnhancementComponent]] = Field(
        default=None, description="One-time conversion functions"
    )
    use_vaf: bool = Field(
        default=False,
        description="Apply VAF (deprecated in CPM 4.3.1)"
    )
    vaf: float = Field(
        default=1.0,
        description="Value Adjustment Factor (0.65-1.35)",
        ge=0.65,
        le=1.35
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "added": [
                        {"name": "CleanupResources()", "type": "EI", "complexity": "low"},
                        {"name": "SafeEnd()", "type": "EI", "complexity": "low"},
                    ],
                    "changed": [
                        {"name": "Declaratie_verzenden", "type": "EI", "complexity": "average"},
                    ],
                    "deleted": [],
                    "use_vaf": False
                }
            ]
        }
    }


class EnhancementCalculateResponse(BaseModel):
    """Response from Enhancement FP calculation."""
    add_fp: float
    change_fp: float
    delete_fp: float
    conversion_fp: float
    total_ufp: float
    total_efp: float
    use_vaf: bool
    vaf: Optional[float]
    component_count: int
    breakdown: Dict[str, int]
    calculated_at: str


class ValidateFPUsageRequest(BaseModel):
    """Request to validate FP usage."""
    description: str = Field(..., description="Work description")
    fp_count: float = Field(..., description="Proposed FP count")


class ValidateFPUsageResponse(BaseModel):
    """Response from FP usage validation."""
    is_valid: bool
    classification: WorkTypeClassifyResponse
    issues: List[str]


class EstimationGuidanceResponse(BaseModel):
    """Estimation guidance for a work type."""
    work_type: str
    description: str
    fp_applicable: bool
    recommended_method: str
    examples: List[str]
    estimation_approach: Dict[str, Any]


# === API Endpoints ===

@router.post(
    "/estimate/work-type",
    response_model=WorkTypeClassifyResponse,
    summary="Classify work type",
    description="""
Classify work to determine the appropriate estimation method.

**NESMA Terminology:**
- **Analyse**: Code review, audit, assessment → NO FP (Time & Materials)
- **Nieuwe bouw**: New software creation → Development FP
- **Verbouw**: Changes to existing software → Enhancement FP
- **Herbouw**: Complete system rebuild → Rebuild FP
- **Onderhoud**: Support, monitoring → Support Hours

**CRITICAL**: Analysis work (audits, reviews, assessments) has NO Function Points!
"""
)
async def classify_work_type(request: WorkTypeClassifyRequest):
    """Classify work type and recommend estimation method."""
    try:
        classifier = WorkTypeClassifier()
        result = classifier.classify(
            description=request.description,
            context=request.context
        )

        return WorkTypeClassifyResponse(
            work_type=result.work_type.value,
            confidence=result.confidence,
            fp_applicable=result.fp_applicable,
            recommended_method=result.recommended_method.value,
            description=result.description,
            matched_keywords=result.matched_keywords,
            warnings=result.warnings,
        )
    except Exception as e:
        logger.error(f"Error classifying work type: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/estimate/enhancement",
    response_model=EnhancementCalculateResponse,
    summary="Calculate Enhancement FP",
    description="""
Calculate Enhancement Function Points for maintenance/fix work.

**IFPUG Enhancement FP Formula:**
`EFP = ADD + CHNG + DEL + CFP`

Where:
- **ADD**: FP of new functions (standard values)
- **CHNG**: FP of changed functions (count AFTER change)
- **DEL**: 40% of original FP for deleted functions
- **CFP**: FP of one-time conversion functions

**Transaction FP Values:**
| Type | Low | Average | High |
|------|-----|---------|------|
| EI   | 3   | 4       | 6    |
| EO   | 4   | 5       | 7    |
| EQ   | 3   | 4       | 6    |
"""
)
async def calculate_enhancement_fp(request: EnhancementCalculateRequest):
    """Calculate Enhancement Function Points."""
    try:
        calculator = EnhancementFPCalculator()

        # Convert Pydantic models to dicts
        added = [c.model_dump() for c in request.added] if request.added else None
        changed = [c.model_dump() for c in request.changed] if request.changed else None
        deleted = [c.model_dump() for c in request.deleted] if request.deleted else None
        conversion = [c.model_dump() for c in request.conversion] if request.conversion else None

        result = calculator.calculate(
            added=added,
            changed=changed,
            deleted=deleted,
            conversion=conversion,
            use_vaf=request.use_vaf,
            vaf=request.vaf,
        )

        return EnhancementCalculateResponse(**result.to_dict())
    except Exception as e:
        logger.error(f"Error calculating Enhancement FP: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/estimate/validate",
    response_model=ValidateFPUsageResponse,
    summary="Validate FP usage",
    description="""
Validate if Function Points should be used for this work.

**Common FP Misuse:**
- Using FP for analysis work (audits, reviews, assessments)
- Using FP for maintenance/support work
- Counting source files as ILF/EIF

**Returns:**
- `is_valid`: Whether FP usage is appropriate
- `classification`: How the work was classified
- `issues`: List of issues found
"""
)
async def validate_fp_usage(request: ValidateFPUsageRequest):
    """Validate if FP should be used for this work."""
    try:
        classifier = WorkTypeClassifier()
        classification = classifier.classify(request.description)
        is_valid, issues = classifier.validate_fp_usage(
            request.description,
            request.fp_count
        )

        return ValidateFPUsageResponse(
            is_valid=is_valid,
            classification=WorkTypeClassifyResponse(
                work_type=classification.work_type.value,
                confidence=classification.confidence,
                fp_applicable=classification.fp_applicable,
                recommended_method=classification.recommended_method.value,
                description=classification.description,
                matched_keywords=classification.matched_keywords,
                warnings=classification.warnings,
            ),
            issues=issues,
        )
    except Exception as e:
        logger.error(f"Error validating FP usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/estimate/guidance/{work_type}",
    response_model=EstimationGuidanceResponse,
    summary="Get estimation guidance",
    description="""
Get detailed estimation guidance for a work type.

**Available Work Types:**
- `analysis` - Analyse (NO FP)
- `development` - Nieuwe bouw (Development FP)
- `enhancement` - Verbouw (Enhancement FP)
- `rebuild` - Herbouw (Rebuild FP)
- `maintenance` - Onderhoud (Support Hours)
"""
)
async def get_estimation_guidance(work_type: str):
    """Get estimation guidance for a work type."""
    try:
        # Validate work type
        try:
            wt = WorkType(work_type.lower())
        except ValueError:
            valid_types = [t.value for t in WorkType]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid work type. Valid types: {valid_types}"
            )

        classifier = WorkTypeClassifier()
        guidance = classifier.get_estimation_guidance(wt)

        return EstimationGuidanceResponse(**guidance)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting estimation guidance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/work-types",
    summary="List all work types",
    description="Get all available work types with their estimation methods."
)
async def list_work_types():
    """List all available work types."""
    classifier = WorkTypeClassifier()
    result = []

    for wt in WorkType:
        guidance = classifier.get_estimation_guidance(wt)
        result.append({
            "work_type": wt.value,
            "description": guidance["description"],
            "fp_applicable": guidance["fp_applicable"],
            "recommended_method": guidance["recommended_method"],
            "examples": guidance["examples"],
        })

    return {
        "work_types": result,
        "nesma_terminology": {
            "analyse": "analysis (NO FP)",
            "nieuwe_bouw": "development",
            "verbouw": "enhancement",
            "herbouw": "rebuild",
            "onderhoud": "maintenance (NO FP)",
        }
    }
