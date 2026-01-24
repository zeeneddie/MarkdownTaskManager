"""
PHP Modern Analyzer API Routes

Fase 24 GAP B6: PHP Modern Analyzer
REST API endpoints for modern PHP (8.x) codebase analysis.

Endpoints:
- POST /api/php-modern/analyze - Analyze PHP project
- GET /api/php-modern/summary - Get analysis summary
- GET /api/php-modern/php8-features - Get PHP 8.x features
- GET /api/php-modern/enums - Get PHP 8.1 enums
- GET /api/php-modern/attributes - Get PHP 8 attributes
- GET /api/php-modern/composer - Get Composer analysis
- GET /api/php-modern/laravel - Get Laravel modern patterns
- GET /api/php-modern/symfony - Get Symfony modern patterns
- GET /api/php-modern/recommendations - Get migration recommendations

Author: Claude Code (Fase 24 GAP)
Date: 2026-01-24
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.php_modern_analyzer_service import (
    PHPModernAnalyzerService,
    PHPModernAnalysisResult,
)

router = APIRouter(prefix="/api/php-modern", tags=["php-modern-analyzer"])

# Service instance
_analyzer_service = PHPModernAnalyzerService()


# ========== Pydantic Models ==========

class AnalyzeRequest(BaseModel):
    """Request to analyze a PHP project."""
    project_path: str = Field(..., description="Path to the project root")
    include_composer: bool = Field(True, description="Include Composer analysis")
    include_framework_analysis: bool = Field(True, description="Include Laravel/Symfony analysis")


class PHP8FeatureResponse(BaseModel):
    """PHP 8.x feature instance."""
    feature_name: str
    php_version_required: str
    file_path: str
    line_number: int
    code_snippet: str
    description: str


class PHP8EnumResponse(BaseModel):
    """PHP 8.1 enum."""
    enum_name: str
    file_path: str
    backed_type: Optional[str]
    case_count: int
    method_count: int
    implements: List[str]


class PHP8AttributeResponse(BaseModel):
    """PHP 8 attribute."""
    name: str
    arguments: List[str]
    target: str
    file_path: str
    line_number: int


class ReadonlyPropertyResponse(BaseModel):
    """Readonly property."""
    class_name: str
    property_name: str
    property_type: str
    file_path: str
    line_number: int


class ConstructorPromotionResponse(BaseModel):
    """Constructor property promotion."""
    class_name: str
    file_path: str
    promoted_properties: List[Dict[str, str]]


class ComposerPackageResponse(BaseModel):
    """Composer package."""
    name: str
    version_constraint: str
    is_dev_dependency: bool
    is_abandoned: bool
    status: str


class ComposerAnalysisResponse(BaseModel):
    """Composer analysis summary."""
    project_name: Optional[str]
    php_version_required: Optional[str]
    total_packages: int
    dev_packages: int
    abandoned_packages: int
    psr4_compliant: bool
    has_lock_file: bool
    packages: List[ComposerPackageResponse]


class LivewireComponentResponse(BaseModel):
    """Livewire component."""
    component_name: str
    file_path: str
    property_count: int
    action_count: int
    uses_wire_model: bool


class LaravelActionResponse(BaseModel):
    """Laravel Action class."""
    class_name: str
    file_path: str
    as_controller: bool
    as_job: bool
    as_listener: bool


class SymfonyMessengerHandlerResponse(BaseModel):
    """Symfony Messenger handler."""
    handler_class: str
    file_path: str
    handles_message: str
    is_async: bool


class RecommendationResponse(BaseModel):
    """Migration recommendation."""
    category: str
    priority: str
    title: str
    description: str
    benefits: List[str]


class AnalysisSummaryResponse(BaseModel):
    """Analysis summary."""
    php_version_detected: str
    php_version_minimum: str
    framework: str
    framework_version: Optional[str]
    total_files_scanned: int
    total_loc: int
    php8_feature_count: int
    enum_count: int
    attribute_count: int
    readonly_property_count: int
    constructor_promotion_count: int
    livewire_components: int
    laravel_actions: int
    messenger_handlers: int
    modernization_score: int
    recommendation_count: int
    scan_duration_ms: float


# ========== Endpoints ==========

@router.post("/analyze", response_model=AnalysisSummaryResponse)
async def analyze_php_project(request: AnalyzeRequest) -> AnalysisSummaryResponse:
    """
    Analyze a PHP project for modern features.

    Returns a summary including PHP 8.x features, framework patterns,
    Composer analysis, and modernization recommendations.
    """
    try:
        result = await _analyzer_service.analyze(
            project_path=request.project_path,
            include_composer=request.include_composer,
            include_framework_analysis=request.include_framework_analysis
        )

        # Store result for subsequent queries (in-memory for now)
        _analyzer_service._last_result = result

        # Build summary response
        return AnalysisSummaryResponse(
            php_version_detected=result.detected_php_version.value,
            php_version_minimum=result.minimum_php_required.value,
            framework=result.framework.value,
            framework_version=result.framework_version,
            total_files_scanned=result.total_files_scanned,
            total_loc=result.total_loc,
            php8_feature_count=result.php8_feature_count,
            enum_count=len(result.php8_enums),
            attribute_count=len(result.php8_attributes),
            readonly_property_count=len(result.readonly_properties),
            constructor_promotion_count=len(result.constructor_promotions),
            livewire_components=len(result.livewire_components),
            laravel_actions=len(result.laravel_actions),
            messenger_handlers=len(result.messenger_handlers),
            modernization_score=result.modernization_score,
            recommendation_count=len(result.migration_recommendations),
            scan_duration_ms=result.scan_duration_ms
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/php8-features", response_model=List[PHP8FeatureResponse])
async def get_php8_features(
    version: Optional[str] = Query(None, description="Filter by PHP version (e.g., '8.0', '8.1')")
) -> List[PHP8FeatureResponse]:
    """Get all detected PHP 8.x features."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    features = result.php8_features
    if version:
        features = [f for f in features if f.php_version_required == version]

    return [
        PHP8FeatureResponse(
            feature_name=f.feature_name,
            php_version_required=f.php_version_required,
            file_path=f.file_path,
            line_number=f.line_number,
            code_snippet=f.code_snippet,
            description=f.description
        )
        for f in features
    ]


@router.get("/enums", response_model=List[PHP8EnumResponse])
async def get_enums() -> List[PHP8EnumResponse]:
    """Get all detected PHP 8.1 enums."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    return [
        PHP8EnumResponse(
            enum_name=e.enum_name,
            file_path=e.file_path,
            backed_type=e.backed_type,
            case_count=len(e.cases),
            method_count=len(e.methods),
            implements=e.implements
        )
        for e in result.php8_enums
    ]


@router.get("/attributes", response_model=List[PHP8AttributeResponse])
async def get_attributes(
    target: Optional[str] = Query(None, description="Filter by target: 'class', 'method', 'property'")
) -> List[PHP8AttributeResponse]:
    """Get all detected PHP 8 attributes."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    attributes = result.php8_attributes
    if target:
        attributes = [a for a in attributes if a.target == target]

    return [
        PHP8AttributeResponse(
            name=a.name,
            arguments=a.arguments,
            target=a.target,
            file_path=a.file_path,
            line_number=a.line_number
        )
        for a in attributes
    ]


@router.get("/readonly-properties", response_model=List[ReadonlyPropertyResponse])
async def get_readonly_properties() -> List[ReadonlyPropertyResponse]:
    """Get all detected readonly properties."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    return [
        ReadonlyPropertyResponse(
            class_name=p.class_name,
            property_name=p.property_name,
            property_type=p.property_type,
            file_path=p.file_path,
            line_number=p.line_number
        )
        for p in result.readonly_properties
    ]


@router.get("/constructor-promotions", response_model=List[ConstructorPromotionResponse])
async def get_constructor_promotions() -> List[ConstructorPromotionResponse]:
    """Get all detected constructor property promotions."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    return [
        ConstructorPromotionResponse(
            class_name=cp.class_name,
            file_path=cp.file_path,
            promoted_properties=cp.promoted_properties
        )
        for cp in result.constructor_promotions
    ]


@router.get("/composer", response_model=ComposerAnalysisResponse)
async def get_composer_analysis() -> ComposerAnalysisResponse:
    """Get Composer dependency analysis."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    if not result.composer_analysis:
        raise HTTPException(status_code=404, detail="No composer.json found in project")

    ca = result.composer_analysis
    return ComposerAnalysisResponse(
        project_name=ca.project_name,
        php_version_required=ca.php_version_required,
        total_packages=ca.total_packages,
        dev_packages=len(ca.dev_packages),
        abandoned_packages=ca.abandoned_packages,
        psr4_compliant=ca.psr4_compliant,
        has_lock_file=ca.has_lock_file,
        packages=[
            ComposerPackageResponse(
                name=p.name,
                version_constraint=p.version_constraint,
                is_dev_dependency=p.is_dev_dependency,
                is_abandoned=p.is_abandoned,
                status=p.status.value
            )
            for p in ca.packages + ca.dev_packages
        ]
    )


@router.get("/laravel", response_model=Dict[str, Any])
async def get_laravel_patterns() -> Dict[str, Any]:
    """Get Laravel modern patterns (Livewire, Actions, etc.)."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    return {
        "livewire_components": [
            LivewireComponentResponse(
                component_name=c.component_name,
                file_path=c.file_path,
                property_count=len(c.properties),
                action_count=len(c.actions),
                uses_wire_model=c.uses_wire_model
            ).model_dump()
            for c in result.livewire_components
        ],
        "actions": [
            LaravelActionResponse(
                class_name=a.class_name,
                file_path=a.file_path,
                as_controller=a.as_controller,
                as_job=a.as_job,
                as_listener=a.as_listener
            ).model_dump()
            for a in result.laravel_actions
        ],
        "modern_components": [
            {
                "file_path": c.file_path,
                "component_name": c.component_name,
                "component_type": c.component_type,
                "laravel_version": c.laravel_version
            }
            for c in result.laravel_modern_components
        ]
    }


@router.get("/symfony", response_model=Dict[str, Any])
async def get_symfony_patterns() -> Dict[str, Any]:
    """Get Symfony modern patterns (Messenger, Attributes, etc.)."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    return {
        "messenger_handlers": [
            SymfonyMessengerHandlerResponse(
                handler_class=h.handler_class,
                file_path=h.file_path,
                handles_message=h.handles_message,
                is_async=h.is_async
            ).model_dump()
            for h in result.messenger_handlers
        ],
        "modern_components": [
            {
                "file_path": c.file_path,
                "component_name": c.component_name,
                "component_type": c.component_type,
                "symfony_version": c.symfony_version,
                "uses_php_attributes": c.uses_php_attributes
            }
            for c in result.symfony_modern_components
        ]
    }


@router.get("/recommendations", response_model=List[RecommendationResponse])
async def get_recommendations(
    priority: Optional[str] = Query(None, description="Filter by priority: 'high', 'medium', 'low'")
) -> List[RecommendationResponse]:
    """Get migration/modernization recommendations."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    recommendations = result.migration_recommendations
    if priority:
        recommendations = [r for r in recommendations if r.get("priority") == priority]

    return [
        RecommendationResponse(
            category=r.get("category", ""),
            priority=r.get("priority", ""),
            title=r.get("title", ""),
            description=r.get("description", ""),
            benefits=r.get("benefits", [])
        )
        for r in recommendations
    ]


@router.get("/summary")
async def get_analysis_summary() -> Dict[str, Any]:
    """Get a detailed summary of the analysis."""
    result = getattr(_analyzer_service, '_last_result', None)
    if not result:
        raise HTTPException(status_code=400, detail="No analysis available. Run /analyze first.")

    return _analyzer_service.get_summary(result)
