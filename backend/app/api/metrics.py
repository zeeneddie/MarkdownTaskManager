"""
Metrics Layer API - Week 126

Endpoints for the HCI-based Metrics Layer scanners.

Features:
- Run 5 quality metrics scans (complexity, interfacing, coupling, balance, duplication)
- Get aggregated quality scores with 5-star ratings
- Compare metrics across projects
- Generate quality reports

Scanners:
- Complexity: Cyclomatic complexity (HCI deep_analyze.py wrapper)
- Interfacing: Parameter count analysis (HCI unit_interfacing_analyzer.py wrapper)
- Coupling: Fan-in/fan-out, instability (HCI module_coupling_analyzer.py wrapper)
- Balance: Gini coefficient (HCI component_balance_analyzer.py wrapper)
- Duplication: Type 1/2/3 clones (HCI code_clone_detector.py wrapper)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import asyncio

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.code_analysis import CodeAnalysisAggregation
from app.models.project import Project

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class MetricRating(BaseModel):
    """5-star rating for a metric."""
    rating: int = Field(..., ge=1, le=5, description="1-5 star rating")
    rating_stars: str = Field(..., description="Star display (e.g., '★★★★☆')")
    value: float = Field(..., description="Raw metric value")
    threshold: str = Field(..., description="Rating threshold description")


class ComplexityMetrics(BaseModel):
    """Complexity scan results."""
    rating: MetricRating
    total_functions: int
    average_complexity: float
    max_complexity: int
    high_complexity_count: int
    complexity_distribution: Dict[str, int]
    by_language: Dict[str, Dict[str, Any]]


class InterfacingMetrics(BaseModel):
    """Interfacing scan results."""
    rating: MetricRating
    total_functions: int
    average_parameters: float
    param_distribution: Dict[str, int]
    pct_above_threshold: float
    by_language: Dict[str, Dict[str, Any]]


class CouplingMetrics(BaseModel):
    """Coupling scan results."""
    rating: MetricRating
    total_modules: int
    total_dependencies: int
    average_fan_out: float
    average_fan_in: float
    average_instability: float
    high_coupling_count: int
    most_unstable_modules: List[Dict[str, Any]]


class BalanceMetrics(BaseModel):
    """Balance scan results."""
    rating: MetricRating
    gini_coefficient: float
    total_components: int
    total_loc: int
    largest_component_pct: float
    top_3_components_pct: float
    god_components: List[Dict[str, Any]]
    components: List[Dict[str, Any]]


class DuplicationMetrics(BaseModel):
    """Duplication scan results."""
    rating: MetricRating
    duplication_percentage: float
    total_blocks: int
    duplicate_blocks: int
    type_1_clones: int
    type_2_clones: int
    type_3_near_miss: int
    sample_type3_pairs: List[Dict[str, Any]]


class FullMetricsReport(BaseModel):
    """Complete metrics report with all 5 dimensions."""
    project_path: str
    scan_started: datetime
    scan_completed: datetime
    duration_ms: int
    overall_rating: float
    overall_stars: str
    complexity: Optional[ComplexityMetrics]
    interfacing: Optional[InterfacingMetrics]
    coupling: Optional[CouplingMetrics]
    balance: Optional[BalanceMetrics]
    duplication: Optional[DuplicationMetrics]
    errors: List[str]


class RunMetricsScanRequest(BaseModel):
    """Request to run metrics scan."""
    project_path: str = Field(..., description="Path to the project to scan")
    scanners: Optional[List[str]] = Field(
        None,
        description="Specific scanners to run. If None, runs all 5."
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_rating_threshold(scanner: str, rating: int) -> str:
    """Get threshold description for a rating."""
    thresholds = {
        "complexity": {
            5: "avg < 10 (excellent)",
            4: "avg 10-15 (good)",
            3: "avg 15-20 (acceptable)",
            2: "avg 20-25 (concerning)",
            1: "avg > 25 (critical)",
        },
        "interfacing": {
            5: "avg < 4 params (excellent)",
            4: "avg 4-5 params (good)",
            3: "avg 5-6 params (acceptable)",
            2: "avg 6-7 params (concerning)",
            1: "avg > 7 params (critical)",
        },
        "coupling": {
            5: "instability < 0.3 (stable)",
            4: "instability 0.3-0.4 (good)",
            3: "instability 0.4-0.5 (acceptable)",
            2: "instability 0.5-0.7 (concerning)",
            1: "instability > 0.7 (unstable)",
        },
        "balance": {
            5: "Gini < 0.3 (well-balanced)",
            4: "Gini 0.3-0.4 (good)",
            3: "Gini 0.4-0.5 (acceptable)",
            2: "Gini 0.5-0.6 (unbalanced)",
            1: "Gini > 0.6 (monolithic risk)",
        },
        "duplication": {
            5: "<= 3% duplication (excellent)",
            4: "3-7% duplication (good)",
            3: "7-10% duplication (acceptable)",
            2: "10-20% duplication (concerning)",
            1: "> 20% duplication (critical)",
        },
    }
    return thresholds.get(scanner, {}).get(rating, "unknown")


async def _run_scanner(scanner_name: str, project_path: str) -> Dict[str, Any]:
    """Run a single scanner and return results."""
    from app.scanners.registry import get_scanner_registry

    registry = get_scanner_registry()
    scanner = registry.get_scanner(scanner_name, project_path)

    if not scanner:
        return {"error": f"Scanner '{scanner_name}' not found or not available"}

    if not scanner.is_available():
        return {"error": f"Scanner '{scanner_name}' is not available"}

    try:
        result = await scanner.scan()
        return {
            "success": result.success,
            "scanner_name": result.scanner_name,
            "metrics": result.metrics.metadata if result.metrics else {},
            "findings_count": len(result.findings) if result.findings else 0,
            "findings": [
                {
                    "rule_id": f.rule_id,
                    "message": f.message,
                    "severity": f.severity.value if hasattr(f.severity, 'value') else str(f.severity),
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                }
                for f in (result.findings or [])[:20]  # Limit to 20 findings
            ],
            "error": result.error_message,
        }
    except Exception as e:
        logger.exception(f"Scanner {scanner_name} failed")
        return {"error": str(e)}


# ============================================================================
# SCAN ENDPOINTS
# ============================================================================

@router.post("/scan", response_model=FullMetricsReport)
async def run_metrics_scan(
    request: RunMetricsScanRequest,
    db: Session = Depends(get_db)
):
    """
    Run a complete metrics scan on a project.

    Executes up to 5 HCI-based quality scanners:
    - complexity: Cyclomatic complexity analysis
    - interfacing: Function parameter count analysis
    - coupling: Module dependency analysis
    - balance: Component size distribution analysis
    - duplication: Code clone detection

    Returns aggregated results with 5-star ratings.
    """
    started_at = datetime.now()
    errors = []

    # Determine which scanners to run
    all_scanners = ["complexity", "interfacing", "coupling", "balance", "duplication"]
    scanners_to_run = request.scanners or all_scanners

    # Validate scanner names
    invalid = set(scanners_to_run) - set(all_scanners)
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scanner names: {invalid}. Valid: {all_scanners}"
        )

    # Run scanners in parallel
    tasks = [_run_scanner(name, request.project_path) for name in scanners_to_run]
    results = await asyncio.gather(*tasks)

    # Map results
    scanner_results = dict(zip(scanners_to_run, results))

    # Process each result
    complexity_metrics = None
    interfacing_metrics = None
    coupling_metrics = None
    balance_metrics = None
    duplication_metrics = None

    ratings = []

    # Process Complexity
    if "complexity" in scanner_results:
        r = scanner_results["complexity"]
        if r.get("error"):
            errors.append(f"complexity: {r['error']}")
        elif r.get("metrics"):
            m = r["metrics"]
            rating = m.get("rating", 3)
            ratings.append(rating)
            complexity_metrics = ComplexityMetrics(
                rating=MetricRating(
                    rating=rating,
                    rating_stars=m.get("rating_stars", "★★★☆☆"),
                    value=m.get("average_complexity", 0),
                    threshold=_get_rating_threshold("complexity", rating),
                ),
                total_functions=m.get("total_functions", 0),
                average_complexity=m.get("average_complexity", 0),
                max_complexity=m.get("max_complexity", 0),
                high_complexity_count=m.get("high_complexity_count", 0),
                complexity_distribution=m.get("complexity_distribution", {}),
                by_language=m.get("by_language", {}),
            )

    # Process Interfacing
    if "interfacing" in scanner_results:
        r = scanner_results["interfacing"]
        if r.get("error"):
            errors.append(f"interfacing: {r['error']}")
        elif r.get("metrics"):
            m = r["metrics"]
            rating = m.get("rating", 3)
            ratings.append(rating)
            interfacing_metrics = InterfacingMetrics(
                rating=MetricRating(
                    rating=rating,
                    rating_stars=m.get("rating_stars", "★★★☆☆"),
                    value=m.get("average_parameters", 0),
                    threshold=_get_rating_threshold("interfacing", rating),
                ),
                total_functions=m.get("total_functions", 0),
                average_parameters=m.get("average_parameters", 0),
                param_distribution=m.get("param_distribution", {}),
                pct_above_threshold=m.get("pct_above_threshold", 0),
                by_language=m.get("by_language", {}),
            )

    # Process Coupling
    if "coupling" in scanner_results:
        r = scanner_results["coupling"]
        if r.get("error"):
            errors.append(f"coupling: {r['error']}")
        elif r.get("metrics"):
            m = r["metrics"]
            rating = m.get("rating", 3)
            ratings.append(rating)
            coupling_metrics = CouplingMetrics(
                rating=MetricRating(
                    rating=rating,
                    rating_stars=m.get("rating_stars", "★★★☆☆"),
                    value=m.get("average_instability", 0),
                    threshold=_get_rating_threshold("coupling", rating),
                ),
                total_modules=m.get("total_modules", 0),
                total_dependencies=m.get("total_dependencies", 0),
                average_fan_out=m.get("average_fan_out", 0),
                average_fan_in=m.get("average_fan_in", 0),
                average_instability=m.get("average_instability", 0),
                high_coupling_count=m.get("high_coupling_count", 0),
                most_unstable_modules=m.get("most_unstable_modules", [])[:10],
            )

    # Process Balance
    if "balance" in scanner_results:
        r = scanner_results["balance"]
        if r.get("error"):
            errors.append(f"balance: {r['error']}")
        elif r.get("metrics"):
            m = r["metrics"]
            rating = m.get("rating", 3)
            ratings.append(rating)
            balance_metrics = BalanceMetrics(
                rating=MetricRating(
                    rating=rating,
                    rating_stars=m.get("rating_stars", "★★★☆☆"),
                    value=m.get("gini_coefficient", 0),
                    threshold=_get_rating_threshold("balance", rating),
                ),
                gini_coefficient=m.get("gini_coefficient", 0),
                total_components=m.get("total_components", 0),
                total_loc=m.get("total_loc", 0),
                largest_component_pct=m.get("largest_component_pct", 0),
                top_3_components_pct=m.get("top_3_components_pct", 0),
                god_components=m.get("god_components", []),
                components=m.get("components", [])[:10],
            )

    # Process Duplication
    if "duplication" in scanner_results:
        r = scanner_results["duplication"]
        if r.get("error"):
            errors.append(f"duplication: {r['error']}")
        elif r.get("metrics"):
            m = r["metrics"]
            rating = m.get("rating", 3)
            ratings.append(rating)
            duplication_metrics = DuplicationMetrics(
                rating=MetricRating(
                    rating=rating,
                    rating_stars=m.get("rating_stars", "★★★☆☆"),
                    value=m.get("duplication_percentage", 0),
                    threshold=_get_rating_threshold("duplication", rating),
                ),
                duplication_percentage=m.get("duplication_percentage", 0),
                total_blocks=m.get("total_blocks", 0),
                duplicate_blocks=m.get("duplicate_blocks", 0),
                type_1_clones=m.get("type_1_clones", 0),
                type_2_clones=m.get("type_2_clones", 0),
                type_3_near_miss=m.get("type_3_near_miss", 0),
                sample_type3_pairs=m.get("sample_type3_pairs", [])[:5],
            )

    # Calculate overall rating
    overall_rating = sum(ratings) / len(ratings) if ratings else 0
    overall_stars = '★' * round(overall_rating) + '☆' * (5 - round(overall_rating))

    completed_at = datetime.now()
    duration_ms = int((completed_at - started_at).total_seconds() * 1000)

    return FullMetricsReport(
        project_path=request.project_path,
        scan_started=started_at,
        scan_completed=completed_at,
        duration_ms=duration_ms,
        overall_rating=round(overall_rating, 2),
        overall_stars=overall_stars,
        complexity=complexity_metrics,
        interfacing=interfacing_metrics,
        coupling=coupling_metrics,
        balance=balance_metrics,
        duplication=duplication_metrics,
        errors=errors,
    )


@router.get("/scan/{scanner_name}")
async def run_single_scanner(
    scanner_name: str,
    project_path: str = Query(..., description="Path to the project to scan"),
):
    """
    Run a single metrics scanner.

    Valid scanners: complexity, interfacing, coupling, balance, duplication
    """
    valid_scanners = ["complexity", "interfacing", "coupling", "balance", "duplication"]
    if scanner_name not in valid_scanners:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scanner: {scanner_name}. Valid: {valid_scanners}"
        )

    result = await _run_scanner(scanner_name, project_path)

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return result


# ============================================================================
# SCANNER INFO ENDPOINTS
# ============================================================================

@router.get("/scanners")
async def list_available_scanners():
    """List all available metrics scanners."""
    from app.scanners.registry import get_scanner_registry

    registry = get_scanner_registry()

    scanners = []
    for name in ["complexity", "interfacing", "coupling", "balance", "duplication"]:
        scanner_class = registry._scanners.get(name)
        if scanner_class:
            # Create a temporary instance to get metadata
            try:
                instance = scanner_class.__new__(scanner_class)
                scanners.append({
                    "name": name,
                    "version": instance.version if hasattr(instance, 'version') else "1.0.0",
                    "scanner_type": instance.scanner_type if hasattr(instance, 'scanner_type') else name,
                    "supported_stacks": instance.supported_stacks if hasattr(instance, 'supported_stacks') else [],
                    "available": True,
                })
            except Exception:
                scanners.append({
                    "name": name,
                    "available": False,
                })
        else:
            scanners.append({
                "name": name,
                "available": False,
            })

    return {
        "total": len(scanners),
        "available": sum(1 for s in scanners if s.get("available")),
        "scanners": scanners,
    }


@router.get("/ratings/thresholds")
async def get_rating_thresholds():
    """Get the 5-star rating thresholds for all metrics."""
    return {
        "complexity": {
            "metric": "Average Cyclomatic Complexity",
            "direction": "lower is better",
            "thresholds": {
                5: {"max": 10, "label": "Excellent"},
                4: {"min": 10, "max": 15, "label": "Good"},
                3: {"min": 15, "max": 20, "label": "Acceptable"},
                2: {"min": 20, "max": 25, "label": "Concerning"},
                1: {"min": 25, "label": "Critical"},
            },
        },
        "interfacing": {
            "metric": "Average Parameters per Function",
            "direction": "lower is better",
            "thresholds": {
                5: {"max": 4, "label": "Excellent"},
                4: {"min": 4, "max": 5, "label": "Good"},
                3: {"min": 5, "max": 6, "label": "Acceptable"},
                2: {"min": 6, "max": 7, "label": "Concerning"},
                1: {"min": 7, "label": "Critical"},
            },
        },
        "coupling": {
            "metric": "Average Instability Index (Ce / (Ce + Ca))",
            "direction": "lower is better (more stable)",
            "thresholds": {
                5: {"max": 0.3, "label": "Stable"},
                4: {"min": 0.3, "max": 0.4, "label": "Good"},
                3: {"min": 0.4, "max": 0.5, "label": "Acceptable"},
                2: {"min": 0.5, "max": 0.7, "label": "Concerning"},
                1: {"min": 0.7, "label": "Unstable"},
            },
        },
        "balance": {
            "metric": "Gini Coefficient (Code Distribution)",
            "direction": "lower is better (more balanced)",
            "thresholds": {
                5: {"max": 0.3, "label": "Well-balanced"},
                4: {"min": 0.3, "max": 0.4, "label": "Good"},
                3: {"min": 0.4, "max": 0.5, "label": "Acceptable"},
                2: {"min": 0.5, "max": 0.6, "label": "Unbalanced"},
                1: {"min": 0.6, "label": "Monolithic Risk"},
            },
        },
        "duplication": {
            "metric": "Duplication Percentage",
            "direction": "lower is better",
            "thresholds": {
                5: {"max": 3, "label": "Excellent"},
                4: {"min": 3, "max": 7, "label": "Good"},
                3: {"min": 7, "max": 10, "label": "Acceptable"},
                2: {"min": 10, "max": 20, "label": "Concerning"},
                1: {"min": 20, "label": "Critical"},
            },
        },
    }


# ============================================================================
# PROJECT METRICS ENDPOINTS
# ============================================================================

@router.post("/project/{project_id}/scan")
async def scan_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    scanners: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Run metrics scan for a registered project.

    Uses the project's repository_path from the database.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get repository path
    repo_path = project.repository_path or project.source_path
    if not repo_path:
        raise HTTPException(
            status_code=400,
            detail="Project has no repository_path configured"
        )

    # Run scan
    request = RunMetricsScanRequest(project_path=repo_path, scanners=scanners)
    return await run_metrics_scan(request, db)


@router.get("/project/{project_id}/history")
async def get_project_metrics_history(
    project_id: int,
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """
    Get metrics history for a project.

    Returns previous scan results stored in code_analysis_aggregations.
    """
    aggregations = db.query(CodeAnalysisAggregation).filter(
        CodeAnalysisAggregation.project_id == project_id,
        CodeAnalysisAggregation.status == "completed"
    ).order_by(
        CodeAnalysisAggregation.created_at.desc()
    ).limit(limit).all()

    return {
        "project_id": project_id,
        "count": len(aggregations),
        "history": [
            {
                "id": str(a.id),
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "analysis_score": a.analysis_score,
                "complexity_rating": a.complexity_rating,
                "avg_cyclomatic": a.avg_cyclomatic,
                "coupling_score": a.coupling_score,
                "total_loc": a.total_loc,
            }
            for a in aggregations
        ],
    }
