"""
Function Point Estimation API

Week 57: Brown Paper FP/SP analysis endpoints.
Provides automatic IFPUG Function Point analysis for existing code.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from app.services.brown_paper_estimation_service import (
    get_brown_paper_estimation_service,
    BrownPaperEstimationService,
    FPAnalysisResult,
    ComponentType,
    Complexity,
)

router = APIRouter(prefix="/api/fp-estimation", tags=["Function Points"])


# ============================================================================
# Request/Response Models
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Request to analyze a directory for FP estimation."""
    path: str
    extensions: Optional[List[str]] = None
    recursive: bool = True
    confidence_threshold: float = 0.7


class ComponentResponse(BaseModel):
    """Single FP component."""
    name: str
    type: str
    complexity: str
    fp: int
    confidence: float
    source_file: Optional[str] = None
    source_line: Optional[int] = None


class AnalysisResponse(BaseModel):
    """Complete FP analysis response."""
    path: str
    total_ufp: int
    total_afp: int
    estimated_sp: int
    vaf: float
    confidence_score: float
    component_count: int
    by_type: Dict[str, Any]
    low_confidence_items: List[Dict[str, Any]]
    requires_review: bool
    analysis_timestamp: str


class QuickEstimateResponse(BaseModel):
    """Quick FP/SP estimate response."""
    path: str
    function_points: int
    story_points: int
    confidence: float
    component_summary: Dict[str, int]


class MethodologyResponse(BaseModel):
    """FP methodology information."""
    standard: str
    version: str
    component_types: Dict[str, Dict[str, int]]
    complexity_levels: List[str]
    vaf_range: Dict[str, float]
    sp_conversion_ratio: float


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_directory(request: AnalyzeRequest):
    """
    Analyze a directory for Function Points.

    Performs IFPUG CPM 4.3.1 analysis on source code to identify:
    - ILF (Internal Logical Files)
    - EIF (External Interface Files)
    - EI (External Inputs)
    - EO (External Outputs)
    - EQ (External Inquiries)

    Returns FP count, estimated Story Points, and confidence score.
    """
    path = Path(request.path)

    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")

    if not path.is_dir():
        raise HTTPException(status_code=400, detail="Path must be a directory")

    service = get_brown_paper_estimation_service()

    # Override confidence threshold if specified
    if request.confidence_threshold != service.confidence_threshold:
        service = BrownPaperEstimationService(
            confidence_threshold=request.confidence_threshold
        )

    result = service.analyze_directory(
        directory=path,
        extensions=request.extensions,
        recursive=request.recursive,
    )

    return AnalysisResponse(
        path=str(path),
        total_ufp=result.total_ufp,
        total_afp=result.total_afp,
        estimated_sp=result.estimated_sp,
        vaf=round(result.vaf, 2),
        confidence_score=round(result.confidence_score * 100, 1),
        component_count=len(result.components),
        by_type=result.to_dict()["by_type"],
        low_confidence_items=result.low_confidence_items,
        requires_review=len(result.low_confidence_items) > 0,
        analysis_timestamp=result.analysis_timestamp.isoformat(),
    )


@router.get("/quick", response_model=QuickEstimateResponse)
async def quick_estimate(
    path: str = Query(..., description="Directory path to analyze"),
    recursive: bool = Query(True, description="Include subdirectories"),
):
    """
    Quick FP/SP estimate without detailed breakdown.

    Faster analysis for getting approximate estimates.
    Use /analyze for detailed component breakdown.
    """
    directory = Path(path)

    if not directory.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")

    if not directory.is_dir():
        raise HTTPException(status_code=400, detail="Path must be a directory")

    service = get_brown_paper_estimation_service()
    result = service.analyze_directory(directory, recursive=recursive)

    # Count components by type
    summary = {}
    for comp_type in ComponentType:
        summary[comp_type.value] = len([
            c for c in result.components
            if c.component_type == comp_type
        ])

    return QuickEstimateResponse(
        path=str(directory),
        function_points=result.total_afp,
        story_points=result.estimated_sp,
        confidence=round(result.confidence_score * 100, 1),
        component_summary=summary,
    )


@router.get("/file/{file_path:path}", response_model=List[ComponentResponse])
async def analyze_file(file_path: str):
    """
    Analyze a single file for FP components.

    Returns list of detected FP components with complexity and confidence.
    """
    path = Path(file_path)

    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    if not path.is_file():
        raise HTTPException(status_code=400, detail="Path must be a file")

    service = get_brown_paper_estimation_service()
    components = service.analyze_file(path)

    return [
        ComponentResponse(
            name=c.name,
            type=c.component_type.value,
            complexity=c.complexity.value,
            fp=c.fp_value,
            confidence=round(c.confidence * 100, 1),
            source_file=c.source_file,
            source_line=c.source_line,
        )
        for c in components
    ]


@router.get("/methodology", response_model=MethodologyResponse)
async def get_methodology():
    """
    Get FP methodology information.

    Returns IFPUG CPM 4.3.1 component types, complexity levels, and weights.
    """
    from app.services.brown_paper_estimation_service import FP_VALUES

    component_weights = {}
    for comp_type in ComponentType:
        component_weights[comp_type.value] = {
            level.value: FP_VALUES[comp_type][level]
            for level in Complexity
        }

    return MethodologyResponse(
        standard="IFPUG",
        version="CPM 4.3.1",
        component_types=component_weights,
        complexity_levels=[c.value for c in Complexity],
        vaf_range={"min": 0.65, "max": 1.35},
        sp_conversion_ratio=0.19,  # Conservative for legacy code
    )


@router.post("/batch")
async def batch_analyze(paths: List[str]):
    """
    Analyze multiple directories in batch.

    Returns aggregated FP/SP estimates for all paths.
    """
    service = get_brown_paper_estimation_service()
    results = []
    total_fp = 0
    total_sp = 0

    for path_str in paths:
        path = Path(path_str)
        if not path.exists() or not path.is_dir():
            results.append({
                "path": path_str,
                "error": "Path not found or not a directory",
            })
            continue

        result = service.analyze_directory(path)
        results.append({
            "path": path_str,
            "function_points": result.total_afp,
            "story_points": result.estimated_sp,
            "confidence": round(result.confidence_score * 100, 1),
            "components": len(result.components),
        })
        total_fp += result.total_afp
        total_sp += result.estimated_sp

    return {
        "paths_analyzed": len([r for r in results if "error" not in r]),
        "total_function_points": total_fp,
        "total_story_points": total_sp,
        "results": results,
    }


@router.get("/complexity-indicators")
async def get_complexity_indicators():
    """
    Get complexity detection patterns.

    Returns the patterns used to determine component complexity.
    """
    from app.services.brown_paper_estimation_service import BrownPaperEstimationService

    service = BrownPaperEstimationService()

    return {
        "high_complexity_indicators": service.COMPLEXITY_INDICATORS["high"],
        "low_complexity_indicators": service.COMPLEXITY_INDICATORS["low"],
        "default_complexity": "Average",
    }


@router.get("/patterns")
async def get_detection_patterns():
    """
    Get FP component detection patterns.

    Returns the regex patterns used to detect each component type.
    """
    from app.services.brown_paper_estimation_service import BrownPaperEstimationService

    service = BrownPaperEstimationService()

    patterns = {}
    for comp_type, pattern_list in service.PATTERNS.items():
        patterns[comp_type] = [
            {"pattern": pattern, "description": desc}
            for pattern, desc in pattern_list
        ]

    return patterns


# ============================================================================
# Week 143: Vector DB Context Endpoints
# ============================================================================

@router.get("/vector-context/{estimation_type}")
async def get_estimation_vector_context(
    estimation_type: str,
    tech_stack: Optional[str] = None,
    project_id: int = 1000
):
    """
    Get Vector DB context for estimation calibration.

    **Estimation Types**:
    - `fp`: Function Point estimation context
    - `sp`: Story Point estimation context

    **Returns**:
    - Similar estimates from knowledge base
    - Complexity patterns
    - Calibration hints
    - Tech stack specific context
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.services.estimation_history_service import EstimationHistoryService
    from app.config import settings

    valid_types = ["fp", "sp"]
    if estimation_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid estimation_type. Must be one of: {valid_types}"
        )

    try:
        # Create async session
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            service = EstimationHistoryService(session, project_id=project_id)
            context = service.get_estimation_context(estimation_type, tech_stack)

            if not context:
                return {
                    "status": "no_context",
                    "message": "No relevant context found in Vector DB",
                    "estimation_type": estimation_type,
                    "context": None
                }

            return {
                "status": "success",
                "estimation_type": estimation_type,
                "tech_stack": tech_stack,
                "project_id": project_id,
                "context": context,
                "total_items": sum(len(v) for v in context.values() if isinstance(v, list))
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch estimation context: {str(e)}"
        )
