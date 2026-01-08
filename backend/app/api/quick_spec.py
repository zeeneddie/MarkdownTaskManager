"""
Quick Spec API - Fast spec generation from templates

Week 60: Quick Spec Templates API
Endpoints for quick spec template management and generation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

from app.services.quick_spec_service import QuickSpecService

router = APIRouter(prefix="/quick-specs", tags=["Quick Specs"])

# Initialize service
quick_spec_service = QuickSpecService()


class GenerateSpecRequest(BaseModel):
    """Request to generate a spec from template."""
    template_type: str
    fields: Dict[str, str]


class ValidateFieldsRequest(BaseModel):
    """Request to validate fields against a template."""
    template_type: str
    fields: Dict[str, str]


@router.get("/templates")
async def list_templates() -> List[Dict[str, Any]]:
    """
    List all available quick spec templates.

    Returns:
        List of template metadata including:
        - type: Template type identifier
        - name: Human-readable name
        - description: What the template is for
        - estimated_time: Typical time to complete
        - required_fields: Fields that must be provided
        - optional_fields: Fields that can be provided
    """
    return quick_spec_service.list_templates()


@router.get("/templates/{template_type}")
async def get_template(template_type: str) -> Dict[str, Any]:
    """
    Get a specific template by type.

    Args:
        template_type: One of: bug_fix, enhancement, refactoring, hotfix

    Returns:
        Template details including the template content
    """
    template = quick_spec_service.get_template(template_type)
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found: {template_type}"
        )
    return template


@router.post("/generate")
async def generate_spec(request: GenerateSpecRequest) -> Dict[str, Any]:
    """
    Generate a spec document from a template.

    Args:
        request: Contains template_type and fields to fill in

    Returns:
        Generated spec document with metadata

    Example:
        POST /api/quick-specs/generate
        {
            "template_type": "bug_fix",
            "fields": {
                "title": "Login button not working",
                "reproduction_steps": "1. Go to login page\\n2. Click login",
                "expected_behavior": "Login form should submit",
                "actual_behavior": "Nothing happens"
            }
        }
    """
    try:
        return quick_spec_service.generate_spec(
            template_type=request.template_type,
            fields=request.fields
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate")
async def validate_fields(request: ValidateFieldsRequest) -> Dict[str, Any]:
    """
    Validate fields against a template without generating.

    Useful for form validation before submission.

    Args:
        request: Contains template_type and fields to validate

    Returns:
        Validation result with any issues:
        - valid: Boolean indicating if all required fields are present
        - missing_required: List of missing required field names
        - extra_fields: List of fields not in the template
    """
    return quick_spec_service.validate_fields(
        template_type=request.template_type,
        fields=request.fields
    )


@router.get("/types")
async def list_template_types() -> List[Dict[str, str]]:
    """
    List available template types with brief descriptions.

    Returns:
        List of template types for dropdowns/selectors
    """
    return [
        {"value": "bug_fix", "label": "Bug Fix", "icon": "🐛"},
        {"value": "enhancement", "label": "Enhancement", "icon": "✨"},
        {"value": "refactoring", "label": "Refactoring", "icon": "🔧"},
        {"value": "hotfix", "label": "Hotfix", "icon": "🚨"},
    ]
