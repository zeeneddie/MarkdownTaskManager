"""
Spec Verification API - Agent OS Verification Endpoints

Week 59-60: Implements 4 Agent OS verification concepts:
1. Visual asset validation
2. Reusability check
3. Mandatory visuals folder
4. Strict scope limitation

Based on patterns from github.com/zeeneddie/agent-os
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

from app.services.spec_verification_service import (
    SpecVerificationService,
    VerificationLevel,
    VerificationCategory
)

router = APIRouter(prefix="/api/spec-verification", tags=["Spec Verification"])

# Initialize service
verification_service = SpecVerificationService()


class VerifySpecRequest(BaseModel):
    """Request to verify a specification."""
    spec_content: str
    project_path: Optional[str] = None
    level: str = "standard"  # lenient, standard, strict


class CreateVisualsFolderRequest(BaseModel):
    """Request to create visuals folder structure."""
    project_path: str


class VerifyProjectRequest(BaseModel):
    """Request to verify project structure."""
    project_path: str
    level: str = "standard"


@router.post("/verify")
async def verify_spec(request: VerifySpecRequest) -> Dict[str, Any]:
    """
    Verify a specification against Agent OS quality standards.

    Runs 4 types of checks:
    1. **Visual Assets**: Does the spec have diagrams/screenshots?
    2. **Reusability**: Does it promote reusable patterns?
    3. **Scope**: Are boundaries clearly defined?
    4. **Structure**: Does the project have required folders?

    Args:
        request: Specification content and options

    Returns:
        Detailed verification results with scores and suggestions

    Example:
        POST /api/spec-verification/verify
        {
            "spec_content": "# Feature Spec\\n\\n## Scope\\n...",
            "project_path": "/path/to/project",
            "level": "standard"
        }
    """
    try:
        level = VerificationLevel(request.level)
    except ValueError:
        level = VerificationLevel.STANDARD

    result = verification_service.verify_spec(
        spec_content=request.spec_content,
        project_path=request.project_path,
        level=level
    )

    return verification_service.get_verification_summary(result)


@router.post("/verify-visual-assets")
async def verify_visual_assets(
    spec_content: str,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verify visual asset requirements only.

    Checks:
    - Image references in spec (markdown images)
    - Diagram mentions (architecture, flowchart, etc.)
    - Embedded diagrams (mermaid, plantuml)
    - Visual files in project

    Returns:
        Visual asset verification results
    """
    result = verification_service.verify_spec(
        spec_content=spec_content,
        project_path=project_path
    )

    # Filter to visual asset checks only
    visual_checks = [
        {
            "name": c.name,
            "passed": c.passed,
            "severity": c.severity,
            "message": c.message,
            "suggestion": c.suggestion
        }
        for c in result.checks
        if c.category == VerificationCategory.VISUAL_ASSETS
    ]

    passed = sum(1 for c in visual_checks if c["passed"])

    return {
        "category": "visual_assets",
        "passed": passed == len(visual_checks),
        "score": round(passed / len(visual_checks) * 100, 1) if visual_checks else 100,
        "checks": visual_checks
    }


@router.post("/verify-reusability")
async def verify_reusability(spec_content: str) -> Dict[str, Any]:
    """
    Verify reusability patterns in specification.

    Checks for:
    - Positive patterns: interface, factory, dependency injection
    - Anti-patterns: hardcoded, magic numbers, workarounds
    - Configuration strategy
    - Testing approach

    Returns:
        Reusability verification results
    """
    result = verification_service.verify_spec(spec_content=spec_content)

    # Filter to reusability checks only
    reuse_checks = [
        {
            "name": c.name,
            "passed": c.passed,
            "severity": c.severity,
            "message": c.message,
            "suggestion": c.suggestion,
            "details": c.details
        }
        for c in result.checks
        if c.category == VerificationCategory.REUSABILITY
    ]

    passed = sum(1 for c in reuse_checks if c["passed"])

    return {
        "category": "reusability",
        "passed": passed == len(reuse_checks),
        "score": round(passed / len(reuse_checks) * 100, 1) if reuse_checks else 100,
        "checks": reuse_checks
    }


@router.post("/verify-scope")
async def verify_scope(spec_content: str) -> Dict[str, Any]:
    """
    Verify scope definition and boundaries.

    Checks for:
    - Explicit scope section
    - In-scope items defined
    - Out-of-scope items defined
    - Scope creep risk indicators
    - Acceptance criteria

    Returns:
        Scope verification results
    """
    result = verification_service.verify_spec(spec_content=spec_content)

    # Filter to scope checks only
    scope_checks = [
        {
            "name": c.name,
            "passed": c.passed,
            "severity": c.severity,
            "message": c.message,
            "suggestion": c.suggestion,
            "details": c.details
        }
        for c in result.checks
        if c.category == VerificationCategory.SCOPE
    ]

    passed = sum(1 for c in scope_checks if c["passed"])

    return {
        "category": "scope",
        "passed": passed == len(scope_checks),
        "score": round(passed / len(scope_checks) * 100, 1) if scope_checks else 100,
        "checks": scope_checks
    }


@router.post("/verify-structure")
async def verify_structure(request: VerifyProjectRequest) -> Dict[str, Any]:
    """
    Verify project folder structure.

    Checks for:
    - Documentation folder (doc/ or docs/)
    - Visuals folder (doc/visuals/)
    - README file

    Args:
        request: Project path and verification level

    Returns:
        Structure verification results
    """
    # Use empty spec content to only run structure checks
    result = verification_service.verify_spec(
        spec_content="",
        project_path=request.project_path
    )

    # Filter to structure checks only
    structure_checks = [
        {
            "name": c.name,
            "passed": c.passed,
            "severity": c.severity,
            "message": c.message,
            "suggestion": c.suggestion
        }
        for c in result.checks
        if c.category == VerificationCategory.STRUCTURE
    ]

    passed = sum(1 for c in structure_checks if c["passed"])

    return {
        "category": "structure",
        "passed": passed == len(structure_checks),
        "score": round(passed / len(structure_checks) * 100, 1) if structure_checks else 100,
        "checks": structure_checks,
        "project_path": request.project_path
    }


@router.post("/create-visuals-folder")
async def create_visuals_folder(request: CreateVisualsFolderRequest) -> Dict[str, Any]:
    """
    Create the mandatory visuals folder structure.

    Creates:
    - doc/ (if not exists)
    - doc/visuals/
    - doc/visuals/diagrams/
    - doc/visuals/screenshots/
    - doc/visuals/mockups/
    - doc/visuals/README.md

    Args:
        request: Project path

    Returns:
        List of created paths
    """
    try:
        result = verification_service.create_visuals_folder(request.project_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/levels")
async def list_verification_levels() -> List[Dict[str, str]]:
    """
    List available verification strictness levels.

    Returns:
        List of levels with descriptions
    """
    return [
        {
            "value": "lenient",
            "label": "Lenient",
            "description": "Warnings only, no blocking errors"
        },
        {
            "value": "standard",
            "label": "Standard",
            "description": "Balanced checks, some requirements"
        },
        {
            "value": "strict",
            "label": "Strict",
            "description": "All requirements enforced"
        }
    ]


@router.get("/categories")
async def list_verification_categories() -> List[Dict[str, Any]]:
    """
    List verification categories and their checks.

    Returns:
        Categories with check descriptions
    """
    return [
        {
            "category": "visual_assets",
            "name": "Visual Assets",
            "description": "Diagrams, screenshots, and visual documentation",
            "checks": [
                "has_visual_references",
                "has_diagram_mention",
                "has_embedded_diagrams",
                "has_visual_files"
            ]
        },
        {
            "category": "reusability",
            "name": "Reusability",
            "description": "Code patterns and maintainability",
            "checks": [
                "reusability_patterns",
                "no_antipatterns",
                "configurable_design",
                "testable_design"
            ]
        },
        {
            "category": "scope",
            "name": "Scope",
            "description": "Boundaries and acceptance criteria",
            "checks": [
                "has_scope_section",
                "has_in_scope",
                "has_out_scope",
                "scope_creep_risk",
                "has_acceptance_criteria"
            ]
        },
        {
            "category": "structure",
            "name": "Structure",
            "description": "Project folder organization",
            "checks": [
                "has_doc_folder",
                "has_visuals_folder",
                "has_readme"
            ]
        }
    ]
