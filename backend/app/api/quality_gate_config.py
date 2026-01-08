"""
Quality Gates Configuration API

REST API endpoints for configuring quality gates:
- GET/PUT full configuration
- PATCH category/check/workflow settings
- POST reset to defaults
- GET configuration history

Author: Claude Code (Week 49 Day 2)
Date: 2025-11-24
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
import uuid

from app.database import get_db
from app.models.quality_gate_config import (
    QualityGateConfig,
    QualityCategoryConfig,
    QualityCheckConfig,
    QualityWorkflowRules,
    QualityConfigHistory,
    Severity,
    ChangeType,
    EntityType
)


router = APIRouter(prefix="/api/quality/config", tags=["Quality Gates Config"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class CheckConfigSchema(BaseModel):
    """Individual check configuration"""
    check_id: str
    check_name: Optional[str] = None
    category_id: str
    enabled: bool = True
    severity: str = "medium"
    threshold_value: Optional[float] = None
    threshold_type: Optional[str] = None
    description: Optional[str] = None
    fix_suggestion: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CategoryConfigSchema(BaseModel):
    """Category configuration with checks"""
    category_id: str
    category_name: Optional[str] = None
    enabled: bool = True
    target_score: int = Field(default=80, ge=0, le=100, description="Target quality score 0-100")
    weight: float = Field(default=1.0, ge=0.0, le=10.0, description="Category weight 0-10")
    checks: Optional[List[CheckConfigSchema]] = []

    model_config = ConfigDict(from_attributes=True)


class WorkflowRulesSchema(BaseModel):
    """Workflow-specific rules"""
    workflow_type: str
    blocking_severities: List[str] = ["critical"]
    required_coverage: int = Field(default=80, ge=0, le=100, description="Required test coverage 0-100")
    e2e_required: bool = False
    regression_required: bool = False
    documentation_required: bool = False
    max_iterations: int = Field(default=3, ge=1, le=10, description="Max validation iterations 1-10")
    stop_on_first_failure: bool = True

    model_config = ConfigDict(from_attributes=True)


class FullConfigSchema(BaseModel):
    """Full quality gates configuration"""
    id: Optional[str] = None
    name: str = "default"
    description: Optional[str] = None
    is_active: bool = True
    categories: List[CategoryConfigSchema] = []
    workflow_rules: List[WorkflowRulesSchema] = []

    model_config = ConfigDict(from_attributes=True)


class CategoryUpdateSchema(BaseModel):
    """Update schema for category"""
    enabled: Optional[bool] = None
    target_score: Optional[int] = Field(default=None, ge=0, le=100)
    weight: Optional[float] = Field(default=None, ge=0.0, le=10.0)


class CheckUpdateSchema(BaseModel):
    """Update schema for check"""
    enabled: Optional[bool] = None
    severity: Optional[str] = None
    threshold_value: Optional[float] = None


class WorkflowUpdateSchema(BaseModel):
    """Update schema for workflow rules"""
    blocking_severities: Optional[List[str]] = None
    required_coverage: Optional[int] = Field(default=None, ge=0, le=100)
    e2e_required: Optional[bool] = None
    regression_required: Optional[bool] = None
    documentation_required: Optional[bool] = None
    max_iterations: Optional[int] = Field(default=None, ge=1, le=10)
    stop_on_first_failure: Optional[bool] = None


class HistoryEntrySchema(BaseModel):
    """Configuration change history entry"""
    id: str
    changed_at: datetime
    changed_by: Optional[str]
    change_type: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    old_value: Optional[Dict] = None
    new_value: Optional[Dict] = None
    comment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConfigResponse(BaseModel):
    """Standard response with config"""
    message: str
    config: Optional[FullConfigSchema] = None


class ValidationResponse(BaseModel):
    """Validation result"""
    valid: bool
    warnings: List[str] = []
    errors: List[str] = []


# ============================================================================
# Default Configuration Data
# ============================================================================

DEFAULT_CATEGORIES = [
    {"category_id": "sig-top-10", "category_name": "SIG-TOP-10 Maintainability", "target_score": 90},
    {"category_id": "solid", "category_name": "SOLID Principles", "target_score": 85},
    {"category_id": "grasp", "category_name": "GRASP Patterns", "target_score": 85},
    {"category_id": "tdd", "category_name": "Test-Driven Development", "target_score": 80},
    {"category_id": "testing-patterns", "category_name": "Testing Patterns", "target_score": 80},
    {"category_id": "design-patterns", "category_name": "Design Patterns", "target_score": 85},
    {"category_id": "clean-code", "category_name": "Clean Code", "target_score": 85},
    {"category_id": "law-of-demeter", "category_name": "Law of Demeter", "target_score": 90},
]

DEFAULT_WORKFLOW_RULES = [
    {"workflow_type": "NEW_FEATURE", "blocking_severities": ["critical", "high"], "required_coverage": 80},
    {"workflow_type": "MAINTENANCE", "blocking_severities": ["critical"], "required_coverage": 70},
    {"workflow_type": "BUG", "blocking_severities": ["critical"], "required_coverage": 70, "regression_required": True},
    {"workflow_type": "QUALITY_AUDIT", "blocking_severities": [], "required_coverage": 0},
    {"workflow_type": "MIGRATION", "blocking_severities": ["critical"], "required_coverage": 65, "e2e_required": True},
    {"workflow_type": "REFACTORING", "blocking_severities": ["critical", "high", "medium"], "required_coverage": 85},
    {"workflow_type": "DOCUMENTATION", "blocking_severities": [], "required_coverage": 0},
    {"workflow_type": "HOTFIX", "blocking_severities": ["critical"], "required_coverage": 60},
]


# ============================================================================
# Helper Functions
# ============================================================================

async def get_or_create_config(db: AsyncSession, project_id: Optional[int] = None) -> QualityGateConfig:
    """Get existing config or create default one"""
    query = select(QualityGateConfig).where(
        QualityGateConfig.project_id == project_id,
        QualityGateConfig.is_active == True
    )
    result = await db.execute(query)
    config = result.scalar_one_or_none()

    if not config:
        # Create default config
        config = QualityGateConfig(
            project_id=project_id,
            name="default",
            is_active=True
        )
        db.add(config)
        await db.flush()

        # Add default categories
        for cat_data in DEFAULT_CATEGORIES:
            category = QualityCategoryConfig(
                config_id=config.id,
                **cat_data
            )
            db.add(category)

        # Add default workflow rules
        for rule_data in DEFAULT_WORKFLOW_RULES:
            rule = QualityWorkflowRules(
                config_id=config.id,
                **rule_data
            )
            db.add(rule)

        await db.commit()
        await db.refresh(config)

    return config


async def log_change(
    db: AsyncSession,
    config_id: uuid.UUID,
    change_type: ChangeType,
    entity_type: Optional[EntityType] = None,
    entity_id: Optional[str] = None,
    old_value: Optional[Dict] = None,
    new_value: Optional[Dict] = None,
    changed_by: Optional[str] = None,
    comment: Optional[str] = None
):
    """Log a configuration change"""
    history = QualityConfigHistory(
        config_id=config_id,
        change_type=change_type.value,  # Use .value for string column
        entity_type=entity_type.value if entity_type else None,  # Use .value for string column
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        changed_by=changed_by,
        comment=comment
    )
    db.add(history)


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("", response_model=FullConfigSchema)
async def get_config(
    project_id: Optional[int] = Query(None, description="Project ID (null for global)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current quality gates configuration.

    Returns categories, checks, and workflow rules.
    Creates default config if none exists.
    """
    config = await get_or_create_config(db, project_id)

    # Load relationships
    query = select(QualityGateConfig).where(
        QualityGateConfig.id == config.id
    ).options(
        selectinload(QualityGateConfig.categories),
        selectinload(QualityGateConfig.checks),
        selectinload(QualityGateConfig.workflow_rules)
    )
    result = await db.execute(query)
    config = result.scalar_one()

    # Build response
    categories_dict = {}
    for cat in config.categories:
        categories_dict[cat.category_id] = CategoryConfigSchema(
            category_id=cat.category_id,
            category_name=cat.category_name,
            enabled=cat.enabled,
            target_score=cat.target_score,
            weight=cat.weight,
            checks=[]
        )

    # Add checks to categories
    for check in config.checks:
        if check.category_id in categories_dict:
            categories_dict[check.category_id].checks.append(
                CheckConfigSchema(
                    check_id=check.check_id,
                    check_name=check.check_name,
                    category_id=check.category_id,
                    enabled=check.enabled,
                    severity=check.severity.value if check.severity else "medium",
                    threshold_value=check.threshold_value,
                    threshold_type=check.threshold_type,
                    description=check.description,
                    fix_suggestion=check.fix_suggestion
                )
            )

    workflow_rules = [
        WorkflowRulesSchema(
            workflow_type=rule.workflow_type,
            blocking_severities=rule.blocking_severities or ["critical"],
            required_coverage=rule.required_coverage,
            e2e_required=rule.e2e_required,
            regression_required=rule.regression_required,
            documentation_required=rule.documentation_required,
            max_iterations=rule.max_iterations,
            stop_on_first_failure=rule.stop_on_first_failure
        )
        for rule in config.workflow_rules
    ]

    return FullConfigSchema(
        id=str(config.id),
        name=config.name,
        description=config.description,
        is_active=config.is_active,
        categories=list(categories_dict.values()),
        workflow_rules=workflow_rules
    )


@router.put("", response_model=ConfigResponse)
async def update_config(
    config_data: FullConfigSchema,
    project_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Update full quality gates configuration.

    Replaces all categories and workflow rules.
    """
    config = await get_or_create_config(db, project_id)

    # Store old config for history
    old_config = await get_config(project_id, db)

    # Delete existing categories, checks, workflow rules
    await db.execute(delete(QualityCategoryConfig).where(
        QualityCategoryConfig.config_id == config.id
    ))
    await db.execute(delete(QualityCheckConfig).where(
        QualityCheckConfig.config_id == config.id
    ))
    await db.execute(delete(QualityWorkflowRules).where(
        QualityWorkflowRules.config_id == config.id
    ))

    # Add new categories and checks
    for cat_data in config_data.categories:
        category = QualityCategoryConfig(
            config_id=config.id,
            category_id=cat_data.category_id,
            category_name=cat_data.category_name,
            enabled=cat_data.enabled,
            target_score=cat_data.target_score,
            weight=cat_data.weight
        )
        db.add(category)

        for check_data in cat_data.checks or []:
            check = QualityCheckConfig(
                config_id=config.id,
                check_id=check_data.check_id,
                check_name=check_data.check_name,
                category_id=check_data.category_id,
                enabled=check_data.enabled,
                severity=Severity(check_data.severity) if check_data.severity else Severity.MEDIUM,
                threshold_value=check_data.threshold_value,
                threshold_type=check_data.threshold_type,
                description=check_data.description,
                fix_suggestion=check_data.fix_suggestion
            )
            db.add(check)

    # Add new workflow rules
    for rule_data in config_data.workflow_rules:
        rule = QualityWorkflowRules(
            config_id=config.id,
            workflow_type=rule_data.workflow_type,
            blocking_severities=rule_data.blocking_severities,
            required_coverage=rule_data.required_coverage,
            e2e_required=rule_data.e2e_required,
            regression_required=rule_data.regression_required,
            documentation_required=rule_data.documentation_required,
            max_iterations=rule_data.max_iterations,
            stop_on_first_failure=rule_data.stop_on_first_failure
        )
        db.add(rule)

    # Update config metadata
    config.name = config_data.name
    config.description = config_data.description

    # Log change
    await log_change(
        db, config.id, ChangeType.CREATE,
        EntityType.CONFIG, str(config.id),
        old_value=old_config.dict() if old_config else None,
        new_value=config_data.dict()
    )

    await db.commit()

    return ConfigResponse(
        message="Configuration updated successfully",
        config=config_data
    )


@router.patch("/category/{category_id}", response_model=ConfigResponse)
async def update_category(
    category_id: str,
    update_data: CategoryUpdateSchema,
    project_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Update a single category's settings."""
    config = await get_or_create_config(db, project_id)

    query = select(QualityCategoryConfig).where(
        QualityCategoryConfig.config_id == config.id,
        QualityCategoryConfig.category_id == category_id
    )
    result = await db.execute(query)
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail=f"Category '{category_id}' not found")

    old_value = {
        "enabled": category.enabled,
        "target_score": category.target_score,
        "weight": category.weight
    }

    # Update fields
    if update_data.enabled is not None:
        category.enabled = update_data.enabled
    if update_data.target_score is not None:
        category.target_score = update_data.target_score
    if update_data.weight is not None:
        category.weight = update_data.weight

    new_value = {
        "enabled": category.enabled,
        "target_score": category.target_score,
        "weight": category.weight
    }

    await log_change(
        db, config.id, ChangeType.CATEGORY_UPDATE,
        EntityType.CATEGORY, category_id,
        old_value=old_value, new_value=new_value
    )

    await db.commit()

    return ConfigResponse(message=f"Category '{category_id}' updated successfully")


@router.patch("/check/{check_id}", response_model=ConfigResponse)
async def update_check(
    check_id: str,
    update_data: CheckUpdateSchema,
    project_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Update a single check's settings."""
    config = await get_or_create_config(db, project_id)

    query = select(QualityCheckConfig).where(
        QualityCheckConfig.config_id == config.id,
        QualityCheckConfig.check_id == check_id
    )
    result = await db.execute(query)
    check = result.scalar_one_or_none()

    if not check:
        raise HTTPException(status_code=404, detail=f"Check '{check_id}' not found")

    old_value = {
        "enabled": check.enabled,
        "severity": check.severity.value if check.severity else None,
        "threshold_value": check.threshold_value
    }

    if update_data.enabled is not None:
        check.enabled = update_data.enabled
    if update_data.severity is not None:
        check.severity = Severity(update_data.severity)
    if update_data.threshold_value is not None:
        check.threshold_value = update_data.threshold_value

    new_value = {
        "enabled": check.enabled,
        "severity": check.severity.value if check.severity else None,
        "threshold_value": check.threshold_value
    }

    await log_change(
        db, config.id, ChangeType.CHECK_UPDATE,
        EntityType.CHECK, check_id,
        old_value=old_value, new_value=new_value
    )

    await db.commit()

    return ConfigResponse(message=f"Check '{check_id}' updated successfully")


@router.patch("/workflow/{workflow_type}", response_model=ConfigResponse)
async def update_workflow(
    workflow_type: str,
    update_data: WorkflowUpdateSchema,
    project_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Update workflow-specific rules."""
    config = await get_or_create_config(db, project_id)

    query = select(QualityWorkflowRules).where(
        QualityWorkflowRules.config_id == config.id,
        QualityWorkflowRules.workflow_type == workflow_type
    )
    result = await db.execute(query)
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_type}' not found")

    old_value = {
        "blocking_severities": rule.blocking_severities,
        "required_coverage": rule.required_coverage,
        "e2e_required": rule.e2e_required,
        "regression_required": rule.regression_required,
        "max_iterations": rule.max_iterations
    }

    if update_data.blocking_severities is not None:
        rule.blocking_severities = update_data.blocking_severities
    if update_data.required_coverage is not None:
        rule.required_coverage = update_data.required_coverage
    if update_data.e2e_required is not None:
        rule.e2e_required = update_data.e2e_required
    if update_data.regression_required is not None:
        rule.regression_required = update_data.regression_required
    if update_data.documentation_required is not None:
        rule.documentation_required = update_data.documentation_required
    if update_data.max_iterations is not None:
        rule.max_iterations = update_data.max_iterations
    if update_data.stop_on_first_failure is not None:
        rule.stop_on_first_failure = update_data.stop_on_first_failure

    new_value = {
        "blocking_severities": rule.blocking_severities,
        "required_coverage": rule.required_coverage,
        "e2e_required": rule.e2e_required,
        "regression_required": rule.regression_required,
        "max_iterations": rule.max_iterations
    }

    await log_change(
        db, config.id, ChangeType.WORKFLOW_UPDATE,
        EntityType.WORKFLOW, workflow_type,
        old_value=old_value, new_value=new_value
    )

    await db.commit()

    return ConfigResponse(message=f"Workflow '{workflow_type}' rules updated successfully")


@router.post("/reset", response_model=ConfigResponse)
async def reset_config(
    project_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Reset configuration to defaults."""
    config = await get_or_create_config(db, project_id)

    # Delete existing config data
    await db.execute(delete(QualityCategoryConfig).where(
        QualityCategoryConfig.config_id == config.id
    ))
    await db.execute(delete(QualityCheckConfig).where(
        QualityCheckConfig.config_id == config.id
    ))
    await db.execute(delete(QualityWorkflowRules).where(
        QualityWorkflowRules.config_id == config.id
    ))

    # Add default categories
    for cat_data in DEFAULT_CATEGORIES:
        category = QualityCategoryConfig(config_id=config.id, **cat_data)
        db.add(category)

    # Add default workflow rules
    for rule_data in DEFAULT_WORKFLOW_RULES:
        rule = QualityWorkflowRules(config_id=config.id, **rule_data)
        db.add(rule)

    await log_change(
        db, config.id, ChangeType.RESET,
        comment="Reset to default configuration"
    )

    await db.commit()

    # Get fresh config
    new_config = await get_config(project_id, db)

    return ConfigResponse(
        message="Configuration reset to defaults",
        config=new_config
    )


@router.get("/history", response_model=List[HistoryEntrySchema])
async def get_history(
    project_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Get configuration change history."""
    config = await get_or_create_config(db, project_id)

    query = select(QualityConfigHistory).where(
        QualityConfigHistory.config_id == config.id
    ).order_by(QualityConfigHistory.changed_at.desc()).limit(limit)

    result = await db.execute(query)
    history = result.scalars().all()

    return [
        HistoryEntrySchema(
            id=str(entry.id),
            changed_at=entry.changed_at,
            changed_by=entry.changed_by,
            change_type=entry.change_type or "unknown",  # Already a string
            entity_type=entry.entity_type,  # Already a string or None
            entity_id=entry.entity_id,
            old_value=entry.old_value,
            new_value=entry.new_value,
            comment=entry.comment
        )
        for entry in history
    ]


@router.post("/validate", response_model=ValidationResponse)
async def validate_config(
    config_data: FullConfigSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate configuration before saving.

    Checks for:
    - Coverage thresholds
    - Blocking severity combinations
    - Category consistency
    """
    warnings = []
    errors = []

    # Validate categories
    for cat in config_data.categories:
        if cat.target_score < 50:
            warnings.append(f"Low target score ({cat.target_score}%) for category '{cat.category_id}'")
        if cat.target_score > 100:
            errors.append(f"Invalid target score ({cat.target_score}%) for category '{cat.category_id}'")

    # Validate workflow rules
    for rule in config_data.workflow_rules:
        if rule.required_coverage < 50 and rule.workflow_type in ["NEW_FEATURE", "REFACTORING"]:
            warnings.append(
                f"Low coverage threshold ({rule.required_coverage}%) for {rule.workflow_type} may reduce code quality"
            )
        if rule.max_iterations < 1:
            errors.append(f"max_iterations must be at least 1 for workflow '{rule.workflow_type}'")
        if not rule.blocking_severities and rule.workflow_type in ["NEW_FEATURE", "BUG"]:
            warnings.append(f"No blocking severities for {rule.workflow_type} - all issues will be warnings only")

    return ValidationResponse(
        valid=len(errors) == 0,
        warnings=warnings,
        errors=errors
    )
