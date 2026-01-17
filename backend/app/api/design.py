"""
Design OS API Endpoints (Week 94-95)

API for Design-First methodology:
- Design Tokens: Colors, typography, spacing per project
- Application Shells: Navigation pattern configurations
- Sample Data: Generated mock data with TypeScript interfaces
- UI Specifications: Section specs, user flows, scope definitions
- Screen Wireframes: Wireframe storage with version tracking
- Implementation Prompts: Generated prompts for coding agents

Integrates Vicky agent (Visual Designer) into workflows.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

from app.database import get_db
from app.services.design_os_service import (
    DesignTokenService,
    ApplicationShellService,
    SampleDataGenerationService,
    UISpecificationService,
    VickyAgentService,
    VICKY_AGENT_CONFIG,
    DEFAULT_PRESETS,
)
from app.models.design_os import (
    DesignTier,
    ShellType,
    SpecStatus,
    PromptType,
    PresetCategory,
)

router = APIRouter(prefix="/api/design", tags=["design"])


# ============================================================================
# Pydantic Models
# ============================================================================

class DesignTokensCreate(BaseModel):
    """Create design tokens for a project."""
    project_id: str
    name: str
    tier: str = "STANDARD"
    preset_id: Optional[str] = None
    custom_tokens: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None


class DesignTokensUpdate(BaseModel):
    """Update design tokens."""
    colors: Optional[Dict[str, Any]] = None
    typography: Optional[Dict[str, Any]] = None
    spacing: Optional[Dict[str, Any]] = None
    borders: Optional[Dict[str, Any]] = None
    shadows: Optional[Dict[str, Any]] = None
    breakpoints: Optional[Dict[str, Any]] = None


class ApplicationShellCreate(BaseModel):
    """Create application shell configuration."""
    project_id: str
    name: str
    shell_type: str = "sidebar"
    navigation: Optional[Dict[str, Any]] = None
    layout: Optional[Dict[str, Any]] = None
    header_config: Optional[Dict[str, Any]] = None
    sidebar_config: Optional[Dict[str, Any]] = None
    footer_config: Optional[Dict[str, Any]] = None
    responsive: Optional[Dict[str, Any]] = None
    dark_mode: bool = True
    tier: str = "PROFESSIONAL"


class ApplicationShellUpdate(BaseModel):
    """Update application shell."""
    navigation: Optional[Dict[str, Any]] = None
    layout: Optional[Dict[str, Any]] = None
    header_config: Optional[Dict[str, Any]] = None
    sidebar_config: Optional[Dict[str, Any]] = None
    footer_config: Optional[Dict[str, Any]] = None
    responsive: Optional[Dict[str, Any]] = None
    dark_mode: Optional[bool] = None


class SampleDataCreate(BaseModel):
    """Create sample data for an entity."""
    project_id: str
    entity_name: str
    fields: List[Dict[str, Any]]  # [{name, type, required, constraints}]
    record_count: int = 5
    tier: str = "STANDARD"
    relationships: Optional[List[Dict[str, Any]]] = None
    created_by: Optional[str] = None


class UISpecificationCreate(BaseModel):
    """Create UI specification."""
    project_id: str
    name: str
    section_id: Optional[str] = None
    purpose: Optional[str] = None
    user_problem: Optional[str] = None
    tier: str = "STANDARD"
    created_by: Optional[str] = None


class UserFlowAdd(BaseModel):
    """Add user flow to specification."""
    flow_name: str
    steps: List[str]
    entry_point: Optional[str] = None
    exit_point: Optional[str] = None


class ScopeSet(BaseModel):
    """Set scope boundaries."""
    in_scope: List[str]
    out_of_scope: List[str]


class UIRequirementAdd(BaseModel):
    """Add UI requirement."""
    component: str
    behavior: str
    validation: Optional[str] = None


class WireframeCreate(BaseModel):
    """Create screen wireframe."""
    project_id: str
    spec_id: Optional[str] = None
    name: str
    screen_type: str = "desktop"
    wireframe_svg: Optional[str] = None
    wireframe_structure: Optional[Dict[str, Any]] = None
    annotations: Optional[List[Dict[str, Any]]] = None
    components: Optional[List[Dict[str, Any]]] = None
    tier: str = "PROFESSIONAL"
    created_by: Optional[str] = None


class ImplementationPromptCreate(BaseModel):
    """Create implementation prompt."""
    project_id: str
    section_id: Optional[str] = None
    prompt_type: str
    name: str
    prompt_content: str
    included_context: Optional[Dict[str, Any]] = None
    target_stack: Optional[str] = None
    estimated_complexity: Optional[str] = None
    dependencies: Optional[List[str]] = None
    tier: str = "PREMIUM"


class DesignPhaseConfig(BaseModel):
    """Configuration for running full design phase."""
    section_id: str
    name: str
    purpose: str
    user_problem: Optional[str] = None
    shell_type: str = "sidebar"
    entities: List[Dict[str, Any]] = []
    preset_id: Optional[str] = "minimal"
    navigation: Optional[Dict[str, Any]] = None
    tier: str = "STANDARD"


class DesignPresetCreate(BaseModel):
    """Create a design token preset."""
    name: str
    description: Optional[str] = None
    category: str
    tokens: Dict[str, Any]
    preview_url: Optional[str] = None


# ============================================================================
# Design Tokens Endpoints
# ============================================================================

@router.post("/projects/{project_id}/tokens")
async def create_design_tokens(
    project_id: str,
    data: DesignTokensCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create design tokens for a project."""
    service = DesignTokenService(db)

    # Override project_id from path
    data.project_id = project_id

    tokens = await service.create_tokens(
        project_id=project_id,
        name=data.name,
        tier=data.tier,
        preset_id=data.preset_id,
        custom_tokens=data.custom_tokens,
        created_by=data.created_by
    )

    return {
        "status": "success",
        "message": "Design tokens created",
        "data": tokens.to_dict()
    }


@router.get("/projects/{project_id}/tokens")
async def get_design_tokens(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get design tokens for a project."""
    service = DesignTokenService(db)
    tokens = await service.get_tokens(project_id)

    if not tokens:
        raise HTTPException(status_code=404, detail="Design tokens not found")

    return {
        "status": "success",
        "data": tokens.to_dict()
    }


@router.put("/projects/{project_id}/tokens")
async def update_design_tokens(
    project_id: str,
    data: DesignTokensUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update design tokens for a project."""
    service = DesignTokenService(db)

    updates = data.dict(exclude_unset=True)
    tokens = await service.update_tokens(project_id, updates)

    if not tokens:
        raise HTTPException(status_code=404, detail="Design tokens not found")

    return {
        "status": "success",
        "message": "Design tokens updated",
        "data": tokens.to_dict()
    }


@router.get("/projects/{project_id}/tokens/export")
async def export_design_tokens(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Export design tokens as JSON."""
    service = DesignTokenService(db)
    export_data = await service.export_tokens(project_id)

    if not export_data:
        raise HTTPException(status_code=404, detail="Design tokens not found")

    return export_data


@router.get("/tokens/presets")
async def list_design_presets(db: AsyncSession = Depends(get_db)):
    """List available design token presets."""
    service = DesignTokenService(db)
    presets = await service.get_presets()

    return {
        "status": "success",
        "presets": presets
    }


@router.post("/tokens/presets")
async def create_design_preset(
    data: DesignPresetCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a custom design token preset."""
    from app.models.design_os import DesignTokenPreset

    preset = DesignTokenPreset(
        name=data.name,
        description=data.description,
        category=data.category,
        tokens=data.tokens,
        preview_url=data.preview_url,
        is_system=False
    )

    db.add(preset)
    db.commit()
    db.refresh(preset)

    return {
        "status": "success",
        "message": "Preset created",
        "data": preset.to_dict()
    }


# ============================================================================
# Application Shell Endpoints
# ============================================================================

@router.post("/projects/{project_id}/shell")
async def create_application_shell(
    project_id: str,
    data: ApplicationShellCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create application shell configuration."""
    service = ApplicationShellService(db)

    shell = await service.create_shell(
        project_id=project_id,
        name=data.name,
        shell_type=data.shell_type,
        navigation=data.navigation or {},
        tier=data.tier
    )

    # Update additional config if provided
    if any([data.layout, data.header_config, data.sidebar_config,
            data.footer_config, data.responsive, data.dark_mode is not None]):
        updates = {}
        if data.layout:
            updates["layout"] = data.layout
        if data.header_config:
            updates["header_config"] = data.header_config
        if data.sidebar_config:
            updates["sidebar_config"] = data.sidebar_config
        if data.footer_config:
            updates["footer_config"] = data.footer_config
        if data.responsive:
            updates["responsive"] = data.responsive
        if data.dark_mode is not None:
            updates["dark_mode"] = data.dark_mode

        if updates:
            shell = await service.update_shell(project_id, updates)

    return {
        "status": "success",
        "message": "Application shell created",
        "data": shell.to_dict()
    }


@router.get("/projects/{project_id}/shell")
async def get_application_shell(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get application shell for a project."""
    service = ApplicationShellService(db)
    shell = await service.get_shell(project_id)

    if not shell:
        raise HTTPException(status_code=404, detail="Application shell not found")

    return {
        "status": "success",
        "data": shell.to_dict()
    }


@router.put("/projects/{project_id}/shell")
async def update_application_shell(
    project_id: str,
    data: ApplicationShellUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update application shell configuration."""
    service = ApplicationShellService(db)

    updates = data.dict(exclude_unset=True)
    shell = await service.update_shell(project_id, updates)

    if not shell:
        raise HTTPException(status_code=404, detail="Application shell not found")

    return {
        "status": "success",
        "message": "Application shell updated",
        "data": shell.to_dict()
    }


@router.get("/shell/types")
async def list_shell_types():
    """List available shell types."""
    return {
        "status": "success",
        "types": [
            {"value": "sidebar", "label": "Sidebar Navigation", "description": "Classic sidebar with collapsible menu"},
            {"value": "top_nav", "label": "Top Navigation", "description": "Horizontal navigation bar"},
            {"value": "minimal", "label": "Minimal", "description": "Clean, minimal header only"},
            {"value": "dashboard", "label": "Dashboard", "description": "Dashboard layout with widgets"},
            {"value": "wizard", "label": "Wizard", "description": "Step-by-step wizard flow"},
        ]
    }


# ============================================================================
# Sample Data Endpoints
# ============================================================================

@router.post("/projects/{project_id}/sample-data")
async def create_sample_data(
    project_id: str,
    data: SampleDataCreate,
    db: AsyncSession = Depends(get_db)
):
    """Generate sample data for an entity."""
    service = SampleDataGenerationService(db)

    sample_data = await service.generate_sample_data(
        project_id=project_id,
        entity_name=data.entity_name,
        fields=data.fields,
        record_count=data.record_count,
        tier=data.tier,
        relationships=data.relationships,
        created_by=data.created_by
    )

    return {
        "status": "success",
        "message": f"Generated {len(sample_data.records)} sample records",
        "data": sample_data.to_dict()
    }


@router.get("/projects/{project_id}/sample-data")
async def list_sample_data(
    project_id: str,
    entity_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List sample data sets for a project."""
    service = SampleDataGenerationService(db)
    datasets = await service.get_sample_data(project_id, entity_name)

    return {
        "status": "success",
        "count": len(datasets),
        "data": [ds.to_dict() for ds in datasets]
    }


@router.get("/projects/{project_id}/sample-data/{entity_name}")
async def get_sample_data(
    project_id: str,
    entity_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Get sample data for a specific entity."""
    service = SampleDataGenerationService(db)
    datasets = await service.get_sample_data(project_id, entity_name)

    if not datasets:
        raise HTTPException(status_code=404, detail=f"No sample data found for entity: {entity_name}")

    return {
        "status": "success",
        "data": datasets[0].to_dict()
    }


@router.get("/projects/{project_id}/sample-data/export/typescript")
async def export_sample_data_typescript(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Export all sample data as TypeScript file."""
    service = SampleDataGenerationService(db)
    typescript_content = await service.export_typescript(project_id)

    return {
        "status": "success",
        "content_type": "text/typescript",
        "content": typescript_content
    }


# ============================================================================
# UI Specification Endpoints
# ============================================================================

@router.post("/sections/shape")
async def create_ui_specification(
    data: UISpecificationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a UI specification (Shape Section)."""
    service = UISpecificationService(db)

    spec = await service.create_specification(
        project_id=data.project_id,
        name=data.name,
        section_id=data.section_id,
        purpose=data.purpose,
        user_problem=data.user_problem,
        tier=data.tier,
        created_by=data.created_by
    )

    return {
        "status": "success",
        "message": "UI specification created",
        "data": spec.to_dict()
    }


@router.get("/sections/{spec_id}/spec")
async def get_ui_specification(
    spec_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a UI specification by ID."""
    from app.models.design_os import UISpecification

    spec = db.query(UISpecification).filter(
        UISpecification.id == spec_id
    ).first()

    if not spec:
        raise HTTPException(status_code=404, detail="UI specification not found")

    return {
        "status": "success",
        "data": spec.to_dict()
    }


@router.get("/projects/{project_id}/specs")
async def list_ui_specifications(
    project_id: str,
    section_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List UI specifications for a project."""
    from app.models.design_os import UISpecification

    query = db.query(UISpecification).filter(
        UISpecification.project_id == project_id
    )

    if section_id:
        query = query.filter(UISpecification.section_id == section_id)

    if status:
        query = query.filter(UISpecification.status == status)

    specs = query.order_by(UISpecification.created_at.desc()).all()

    return {
        "status": "success",
        "count": len(specs),
        "data": [spec.to_dict() for spec in specs]
    }


@router.post("/sections/{spec_id}/user-flows")
async def add_user_flow(
    spec_id: str,
    data: UserFlowAdd,
    db: AsyncSession = Depends(get_db)
):
    """Add a user flow to a UI specification."""
    service = UISpecificationService(db)

    spec = await service.add_user_flow(
        spec_id=spec_id,
        flow_name=data.flow_name,
        steps=data.steps,
        entry_point=data.entry_point,
        exit_point=data.exit_point
    )

    if not spec:
        raise HTTPException(status_code=404, detail="UI specification not found")

    return {
        "status": "success",
        "message": "User flow added",
        "data": spec.to_dict()
    }


@router.put("/sections/{spec_id}/scope")
async def set_scope(
    spec_id: str,
    data: ScopeSet,
    db: AsyncSession = Depends(get_db)
):
    """Set scope boundaries for a UI specification."""
    service = UISpecificationService(db)

    spec = await service.set_scope(
        spec_id=spec_id,
        in_scope=data.in_scope,
        out_of_scope=data.out_of_scope
    )

    if not spec:
        raise HTTPException(status_code=404, detail="UI specification not found")

    return {
        "status": "success",
        "message": "Scope updated",
        "data": spec.to_dict()
    }


@router.post("/sections/{spec_id}/requirements")
async def add_ui_requirement(
    spec_id: str,
    data: UIRequirementAdd,
    db: AsyncSession = Depends(get_db)
):
    """Add a UI requirement to a specification."""
    service = UISpecificationService(db)

    spec = await service.add_ui_requirement(
        spec_id=spec_id,
        component=data.component,
        behavior=data.behavior,
        validation=data.validation
    )

    if not spec:
        raise HTTPException(status_code=404, detail="UI specification not found")

    return {
        "status": "success",
        "message": "UI requirement added",
        "data": spec.to_dict()
    }


@router.put("/sections/{spec_id}/status")
async def update_spec_status(
    spec_id: str,
    status: str = Query(..., description="New status: draft, review, approved, implemented"),
    db: AsyncSession = Depends(get_db)
):
    """Update the status of a UI specification."""
    from app.models.design_os import UISpecification

    spec = db.query(UISpecification).filter(
        UISpecification.id == spec_id
    ).first()

    if not spec:
        raise HTTPException(status_code=404, detail="UI specification not found")

    spec.status = status
    spec.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(spec)

    return {
        "status": "success",
        "message": f"Status updated to {status}",
        "data": spec.to_dict()
    }


@router.get("/sections/{spec_id}/export/markdown")
async def export_spec_markdown(
    spec_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Export UI specification as Markdown."""
    service = UISpecificationService(db)
    markdown = await service.export_markdown(spec_id)

    if not markdown:
        raise HTTPException(status_code=404, detail="UI specification not found")

    return {
        "status": "success",
        "content_type": "text/markdown",
        "content": markdown
    }


# ============================================================================
# Wireframe Endpoints
# ============================================================================

@router.post("/wireframes")
async def create_wireframe(
    data: WireframeCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a screen wireframe."""
    from app.models.design_os import ScreenWireframe

    wireframe = ScreenWireframe(
        project_id=data.project_id,
        spec_id=uuid.UUID(data.spec_id) if data.spec_id else None,
        name=data.name,
        screen_type=data.screen_type,
        wireframe_svg=data.wireframe_svg,
        wireframe_structure=data.wireframe_structure or {},
        annotations=data.annotations or [],
        components=data.components or [],
        tier=data.tier,
        created_by=data.created_by
    )

    db.add(wireframe)
    db.commit()
    db.refresh(wireframe)

    return {
        "status": "success",
        "message": "Wireframe created",
        "data": wireframe.to_dict()
    }


@router.get("/wireframes/{wireframe_id}")
async def get_wireframe(
    wireframe_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a wireframe by ID."""
    from app.models.design_os import ScreenWireframe

    wireframe = db.query(ScreenWireframe).filter(
        ScreenWireframe.id == wireframe_id
    ).first()

    if not wireframe:
        raise HTTPException(status_code=404, detail="Wireframe not found")

    return {
        "status": "success",
        "data": wireframe.to_dict()
    }


@router.get("/projects/{project_id}/wireframes")
async def list_wireframes(
    project_id: str,
    spec_id: Optional[str] = None,
    screen_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List wireframes for a project."""
    from app.models.design_os import ScreenWireframe

    query = db.query(ScreenWireframe).filter(
        ScreenWireframe.project_id == project_id
    )

    if spec_id:
        query = query.filter(ScreenWireframe.spec_id == spec_id)

    if screen_type:
        query = query.filter(ScreenWireframe.screen_type == screen_type)

    wireframes = query.order_by(ScreenWireframe.created_at.desc()).all()

    return {
        "status": "success",
        "count": len(wireframes),
        "data": [wf.to_dict() for wf in wireframes]
    }


@router.post("/wireframes/{wireframe_id}/version")
async def create_wireframe_version(
    wireframe_id: str,
    data: WireframeCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new version of a wireframe."""
    from app.models.design_os import ScreenWireframe

    # Get parent wireframe
    parent = db.query(ScreenWireframe).filter(
        ScreenWireframe.id == wireframe_id
    ).first()

    if not parent:
        raise HTTPException(status_code=404, detail="Parent wireframe not found")

    # Create new version
    wireframe = ScreenWireframe(
        project_id=parent.project_id,
        spec_id=parent.spec_id,
        name=data.name or parent.name,
        screen_type=data.screen_type or parent.screen_type,
        wireframe_svg=data.wireframe_svg or parent.wireframe_svg,
        wireframe_structure=data.wireframe_structure or parent.wireframe_structure,
        annotations=data.annotations or parent.annotations,
        components=data.components or parent.components,
        tier=parent.tier,
        version=parent.version + 1,
        parent_version_id=parent.id,
        created_by=data.created_by
    )

    db.add(wireframe)
    db.commit()
    db.refresh(wireframe)

    return {
        "status": "success",
        "message": f"Wireframe version {wireframe.version} created",
        "data": wireframe.to_dict()
    }


# ============================================================================
# Implementation Prompt Endpoints
# ============================================================================

@router.post("/prompts")
async def create_implementation_prompt(
    data: ImplementationPromptCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create an implementation prompt."""
    from app.models.design_os import ImplementationPrompt

    prompt = ImplementationPrompt(
        project_id=data.project_id,
        section_id=data.section_id,
        prompt_type=data.prompt_type,
        name=data.name,
        prompt_content=data.prompt_content,
        included_context=data.included_context or {},
        target_stack=data.target_stack,
        estimated_complexity=data.estimated_complexity,
        dependencies=data.dependencies or [],
        tier=data.tier
    )

    db.add(prompt)
    db.commit()
    db.refresh(prompt)

    return {
        "status": "success",
        "message": "Implementation prompt created",
        "data": prompt.to_dict()
    }


@router.get("/prompts/{prompt_id}")
async def get_implementation_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get an implementation prompt by ID."""
    from app.models.design_os import ImplementationPrompt

    prompt = db.query(ImplementationPrompt).filter(
        ImplementationPrompt.id == prompt_id
    ).first()

    if not prompt:
        raise HTTPException(status_code=404, detail="Implementation prompt not found")

    # Track usage
    prompt.times_used += 1
    prompt.last_used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(prompt)

    return {
        "status": "success",
        "data": prompt.to_dict()
    }


@router.get("/projects/{project_id}/prompts")
async def list_implementation_prompts(
    project_id: str,
    section_id: Optional[str] = None,
    prompt_type: Optional[str] = None,
    target_stack: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List implementation prompts for a project."""
    from app.models.design_os import ImplementationPrompt

    query = db.query(ImplementationPrompt).filter(
        ImplementationPrompt.project_id == project_id
    )

    if section_id:
        query = query.filter(ImplementationPrompt.section_id == section_id)

    if prompt_type:
        query = query.filter(ImplementationPrompt.prompt_type == prompt_type)

    if target_stack:
        query = query.filter(ImplementationPrompt.target_stack == target_stack)

    prompts = query.order_by(ImplementationPrompt.created_at.desc()).all()

    return {
        "status": "success",
        "count": len(prompts),
        "data": [p.to_dict() for p in prompts]
    }


# ============================================================================
# Vicky Agent Endpoints
# ============================================================================

@router.get("/agent/vicky")
async def get_vicky_agent_info():
    """Get information about the Vicky agent."""
    return {
        "status": "success",
        "agent": VICKY_AGENT_CONFIG
    }


@router.get("/agent/vicky/capabilities/{tier}")
async def get_vicky_capabilities(tier: str):
    """Get Vicky's capabilities for a specific tier."""
    service = VickyAgentService(None)  # No DB needed for this
    capabilities = service.get_tier_capabilities(tier)

    return {
        "status": "success",
        "tier": tier,
        "capabilities": capabilities
    }


@router.post("/projects/{project_id}/design-phase")
async def run_design_phase(
    project_id: str,
    config: DesignPhaseConfig,
    db: AsyncSession = Depends(get_db)
):
    """Run a complete design phase for a project section (Vicky workflow)."""
    service = VickyAgentService(db)

    result = await service.run_design_phase(
        project_id=project_id,
        section_id=config.section_id,
        config={
            "name": config.name,
            "purpose": config.purpose,
            "user_problem": config.user_problem,
            "shell_type": config.shell_type,
            "entities": config.entities,
            "preset_id": config.preset_id,
            "navigation": config.navigation,
        },
        tier=config.tier
    )

    return {
        "status": "success",
        "message": "Design phase completed",
        "data": result
    }


@router.post("/projects/{project_id}/shape-section")
async def process_shape_section(
    project_id: str,
    section_id: str,
    name: str,
    purpose: str,
    user_problem: Optional[str] = None,
    tier: str = "STANDARD",
    db: AsyncSession = Depends(get_db)
):
    """Process a Shape Section (first step in Design OS methodology)."""
    service = VickyAgentService(db)

    result = await service.process_shape_section(
        project_id=project_id,
        section_id=section_id,
        name=name,
        purpose=purpose,
        user_problem=user_problem,
        tier=tier
    )

    return {
        "status": "success",
        "message": "Shape section processed",
        "data": result
    }


@router.post("/projects/{project_id}/generate-tokens")
async def generate_design_tokens(
    project_id: str,
    preset: str = "minimal",
    tier: str = "STANDARD",
    db: AsyncSession = Depends(get_db)
):
    """Generate design tokens using Vicky agent."""
    service = VickyAgentService(db)

    result = await service.generate_design_tokens(
        project_id=project_id,
        preset=preset,
        tier=tier
    )

    return {
        "status": "success",
        "message": "Design tokens generated",
        "data": result
    }


@router.post("/projects/{project_id}/generate-shell")
async def generate_application_shell(
    project_id: str,
    shell_type: str = "sidebar",
    navigation: Optional[Dict[str, Any]] = None,
    tier: str = "PROFESSIONAL",
    db: AsyncSession = Depends(get_db)
):
    """Generate application shell using Vicky agent."""
    service = VickyAgentService(db)

    result = await service.generate_application_shell(
        project_id=project_id,
        shell_type=shell_type,
        navigation=navigation or {},
        tier=tier
    )

    return {
        "status": "success",
        "message": "Application shell generated",
        "data": result
    }


@router.post("/projects/{project_id}/generate-sample-data")
async def generate_sample_data_batch(
    project_id: str,
    entities: List[Dict[str, Any]],
    tier: str = "STANDARD",
    db: AsyncSession = Depends(get_db)
):
    """Generate sample data for multiple entities using Vicky agent."""
    service = VickyAgentService(db)

    result = await service.generate_sample_data(
        project_id=project_id,
        entities=entities,
        tier=tier
    )

    return {
        "status": "success",
        "message": f"Generated sample data for {len(entities)} entities",
        "data": result
    }


# ============================================================================
# Export Endpoints
# ============================================================================

@router.post("/projects/{project_id}/export")
async def export_project_design(
    project_id: str,
    include_tokens: bool = True,
    include_shell: bool = True,
    include_sample_data: bool = True,
    include_specs: bool = True,
    include_wireframes: bool = True,
    include_prompts: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Export all design artifacts for a project."""
    result = {"project_id": project_id}

    if include_tokens:
        service = DesignTokenService(db)
        tokens = await service.get_tokens(project_id)
        if tokens:
            result["design_tokens"] = tokens.to_export_json()

    if include_shell:
        service = ApplicationShellService(db)
        shell = await service.get_shell(project_id)
        if shell:
            result["application_shell"] = shell.to_dict()

    if include_sample_data:
        service = SampleDataGenerationService(db)
        datasets = await service.get_sample_data(project_id)
        result["sample_data"] = {ds.entity_name: ds.to_dict() for ds in datasets}

    if include_specs:
        from app.models.design_os import UISpecification
        specs = db.query(UISpecification).filter(
            UISpecification.project_id == project_id
        ).all()
        result["ui_specifications"] = [spec.to_dict() for spec in specs]

    if include_wireframes:
        from app.models.design_os import ScreenWireframe
        wireframes = db.query(ScreenWireframe).filter(
            ScreenWireframe.project_id == project_id
        ).all()
        result["wireframes"] = [wf.to_dict() for wf in wireframes]

    if include_prompts:
        from app.models.design_os import ImplementationPrompt
        prompts = db.query(ImplementationPrompt).filter(
            ImplementationPrompt.project_id == project_id
        ).all()
        result["implementation_prompts"] = [p.to_dict() for p in prompts]

    return {
        "status": "success",
        "message": "Design export complete",
        "data": result
    }


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get("/statistics")
async def get_design_statistics(db: AsyncSession = Depends(get_db)):
    """Get overall design system statistics."""
    from app.models.design_os import (
        DesignTokens, ApplicationShell, SampleDataSet,
        UISpecification, ScreenWireframe, ImplementationPrompt, DesignTokenPreset
    )

    # Count records using async patterns
    design_tokens_count = (await db.execute(select(func.count()).select_from(DesignTokens))).scalar() or 0
    shells_count = (await db.execute(select(func.count()).select_from(ApplicationShell))).scalar() or 0
    sample_data_count = (await db.execute(select(func.count()).select_from(SampleDataSet))).scalar() or 0
    specs_count = (await db.execute(select(func.count()).select_from(UISpecification))).scalar() or 0
    wireframes_count = (await db.execute(select(func.count()).select_from(ScreenWireframe))).scalar() or 0
    prompts_count = (await db.execute(select(func.count()).select_from(ImplementationPrompt))).scalar() or 0
    presets_db_count = (await db.execute(select(func.count()).select_from(DesignTokenPreset))).scalar() or 0

    stats = {
        "design_tokens": design_tokens_count,
        "application_shells": shells_count,
        "sample_data_sets": sample_data_count,
        "ui_specifications": specs_count,
        "screen_wireframes": wireframes_count,
        "implementation_prompts": prompts_count,
        "presets_available": presets_db_count + len(DEFAULT_PRESETS),
    }

    # Specs by status
    specs_by_status = {}
    for status in ["draft", "review", "approved", "implemented"]:
        count_result = await db.execute(
            select(func.count()).select_from(UISpecification).where(UISpecification.status == status)
        )
        specs_by_status[status] = count_result.scalar() or 0
    stats["specs_by_status"] = specs_by_status

    # Prompts by type
    prompts_by_type = {}
    for prompt_type in ["component", "page", "feature", "integration", "api"]:
        count_result = await db.execute(
            select(func.count()).select_from(ImplementationPrompt).where(ImplementationPrompt.prompt_type == prompt_type)
        )
        prompts_by_type[prompt_type] = count_result.scalar() or 0
    stats["prompts_by_type"] = prompts_by_type

    return {
        "status": "success",
        "statistics": stats
    }


@router.get("/projects/{project_id}/statistics")
async def get_project_design_statistics(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get design statistics for a specific project."""
    from app.models.design_os import (
        DesignTokens, ApplicationShell, SampleDataSet,
        UISpecification, ScreenWireframe, ImplementationPrompt
    )

    # Count tokens
    tokens_count = (await db.execute(
        select(func.count()).select_from(DesignTokens).where(DesignTokens.project_id == project_id)
    )).scalar() or 0

    # Count shells
    shells_count = (await db.execute(
        select(func.count()).select_from(ApplicationShell).where(ApplicationShell.project_id == project_id)
    )).scalar() or 0

    # Count sample data
    sample_count = (await db.execute(
        select(func.count()).select_from(SampleDataSet).where(SampleDataSet.project_id == project_id)
    )).scalar() or 0

    # Count specs
    specs_count = (await db.execute(
        select(func.count()).select_from(UISpecification).where(UISpecification.project_id == project_id)
    )).scalar() or 0

    # Count wireframes
    wireframes_count = (await db.execute(
        select(func.count()).select_from(ScreenWireframe).where(ScreenWireframe.project_id == project_id)
    )).scalar() or 0

    # Count prompts
    prompts_count = (await db.execute(
        select(func.count()).select_from(ImplementationPrompt).where(ImplementationPrompt.project_id == project_id)
    )).scalar() or 0

    stats = {
        "project_id": project_id,
        "has_tokens": tokens_count > 0,
        "has_shell": shells_count > 0,
        "sample_data_entities": sample_count,
        "specifications": specs_count,
        "wireframes": wireframes_count,
        "implementation_prompts": prompts_count,
    }

    return {
        "status": "success",
        "statistics": stats
    }


# =============================================================================
# IMPLEMENTATION PROMPT ENDPOINTS (Week 96)
# =============================================================================


@router.post("/projects/{project_id}/prompts/component")
async def generate_component_prompt(
    project_id: str,
    section_id: str,
    component_name: str,
    target_stack: str = "react",
    db: AsyncSession = Depends(get_db)
):
    """Generate an implementation prompt for a component."""
    from app.services.design_os_service import ImplementationPromptService, DesignTokenService

    prompt_service = ImplementationPromptService(db)
    token_service = DesignTokenService(db)

    # Get design tokens if available
    tokens = await token_service.get_tokens(project_id)
    design_tokens = tokens.tokens if tokens else None

    prompt = await prompt_service.generate_component_prompt(
        project_id=project_id,
        section_id=section_id,
        component_name=component_name,
        design_tokens=design_tokens,
        target_stack=target_stack,
    )

    return {
        "status": "success",
        "prompt": prompt.to_dict()
    }


@router.post("/projects/{project_id}/prompts/feature")
async def generate_feature_prompt(
    project_id: str,
    section_id: str,
    feature_name: str,
    description: str,
    components: List[str],
    target_stack: str = "react",
    db: AsyncSession = Depends(get_db)
):
    """Generate an implementation prompt for a feature."""
    from app.services.design_os_service import ImplementationPromptService

    prompt_service = ImplementationPromptService(db)

    prompt = await prompt_service.generate_feature_prompt(
        project_id=project_id,
        section_id=section_id,
        feature_name=feature_name,
        description=description,
        components=components,
        target_stack=target_stack,
    )

    return {
        "status": "success",
        "prompt": prompt.to_dict()
    }


@router.get("/projects/{project_id}/prompts")
async def get_project_prompts(
    project_id: str,
    prompt_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all implementation prompts for a project."""
    from app.services.design_os_service import ImplementationPromptService

    prompt_service = ImplementationPromptService(db)
    prompts = await prompt_service.get_prompts_for_project(project_id, prompt_type)

    return {
        "status": "success",
        "prompts": [p.to_dict() for p in prompts],
        "count": len(prompts)
    }


@router.get("/prompts/{prompt_id}")
async def get_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific implementation prompt."""
    from app.services.design_os_service import ImplementationPromptService

    prompt_service = ImplementationPromptService(db)
    prompt = await prompt_service.get_prompt(prompt_id)

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return {
        "status": "success",
        "prompt": prompt.to_dict()
    }


@router.post("/prompts/{prompt_id}/record-usage")
async def record_prompt_usage(
    prompt_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Record that a prompt was used."""
    from app.services.design_os_service import ImplementationPromptService

    prompt_service = ImplementationPromptService(db)
    await prompt_service.record_prompt_usage(prompt_id)

    return {
        "status": "success",
        "message": "Usage recorded"
    }


# =============================================================================
# WIREFRAME ENDPOINTS (Week 96)
# =============================================================================


@router.post("/projects/{project_id}/wireframes")
async def create_wireframe(
    project_id: str,
    name: str,
    screen_type: str = "desktop",
    spec_id: Optional[str] = None,
    wireframe_structure: Optional[Dict] = None,
    tier: str = "PROFESSIONAL",
    db: AsyncSession = Depends(get_db)
):
    """Create a new wireframe."""
    from app.services.design_os_service import ScreenWireframeService

    wireframe_service = ScreenWireframeService(db)

    wireframe = await wireframe_service.create_wireframe(
        project_id=project_id,
        name=name,
        screen_type=screen_type,
        spec_id=spec_id,
        wireframe_structure=wireframe_structure,
        tier=tier,
    )

    return {
        "status": "success",
        "wireframe": wireframe.to_dict()
    }


@router.get("/projects/{project_id}/wireframes")
async def get_project_wireframes(
    project_id: str,
    screen_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all wireframes for a project."""
    from app.services.design_os_service import ScreenWireframeService

    wireframe_service = ScreenWireframeService(db)
    wireframes = await wireframe_service.get_wireframes_for_project(project_id, screen_type)

    return {
        "status": "success",
        "wireframes": [w.to_dict() for w in wireframes],
        "count": len(wireframes)
    }


@router.get("/wireframes/{wireframe_id}")
async def get_wireframe(
    wireframe_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific wireframe."""
    from app.services.design_os_service import ScreenWireframeService

    wireframe_service = ScreenWireframeService(db)
    wireframe = await wireframe_service.get_wireframe(wireframe_id)

    if not wireframe:
        raise HTTPException(status_code=404, detail="Wireframe not found")

    return {
        "status": "success",
        "wireframe": wireframe.to_dict()
    }


@router.post("/wireframes/{wireframe_id}/version")
async def create_wireframe_version(
    wireframe_id: str,
    wireframe_structure: Optional[Dict] = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a new version of a wireframe."""
    from app.services.design_os_service import ScreenWireframeService

    wireframe_service = ScreenWireframeService(db)

    try:
        new_version = await wireframe_service.create_version(
            wireframe_id=wireframe_id,
            wireframe_structure=wireframe_structure,
        )
        return {
            "status": "success",
            "wireframe": new_version.to_dict(),
            "message": f"Created version {new_version.version}"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/wireframes/{wireframe_id}/history")
async def get_wireframe_history(
    wireframe_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get version history for a wireframe."""
    from app.services.design_os_service import ScreenWireframeService

    wireframe_service = ScreenWireframeService(db)
    history = await wireframe_service.get_version_history(wireframe_id)

    return {
        "status": "success",
        "history": [w.to_dict() for w in history],
        "count": len(history)
    }


@router.post("/wireframes/{wireframe_id}/annotations")
async def add_wireframe_annotation(
    wireframe_id: str,
    x: int,
    y: int,
    text: str,
    annotation_type: str = "note",
    db: AsyncSession = Depends(get_db)
):
    """Add an annotation to a wireframe."""
    from app.services.design_os_service import ScreenWireframeService

    wireframe_service = ScreenWireframeService(db)

    try:
        wireframe = await wireframe_service.add_annotation(
            wireframe_id=wireframe_id,
            x=x,
            y=y,
            text=text,
            annotation_type=annotation_type,
        )
        return {
            "status": "success",
            "wireframe": wireframe.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/wireframes/{wireframe_id}/components")
async def add_wireframe_component(
    wireframe_id: str,
    name: str,
    position: Dict[str, int],
    props: Optional[Dict] = None,
    db: AsyncSession = Depends(get_db)
):
    """Add a component to a wireframe."""
    from app.services.design_os_service import ScreenWireframeService

    wireframe_service = ScreenWireframeService(db)

    try:
        wireframe = await wireframe_service.add_component(
            wireframe_id=wireframe_id,
            name=name,
            position=position,
            props=props,
        )
        return {
            "status": "success",
            "wireframe": wireframe.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/wireframes/{wireframe_id}/responsive")
async def add_responsive_variant(
    wireframe_id: str,
    breakpoint: str,
    variant_structure: Dict,
    db: AsyncSession = Depends(get_db)
):
    """Add a responsive variant to a wireframe."""
    from app.services.design_os_service import ScreenWireframeService

    wireframe_service = ScreenWireframeService(db)

    try:
        wireframe = await wireframe_service.add_responsive_variant(
            wireframe_id=wireframe_id,
            breakpoint=breakpoint,
            variant_structure=variant_structure,
        )
        return {
            "status": "success",
            "wireframe": wireframe.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/wireframes/generate-structure")
async def generate_wireframe_structure(
    screen_name: str,
    layout: str = "sidebar",
):
    """Generate a basic wireframe structure template."""
    from app.services.design_os_service import ScreenWireframeService

    # This is a static method, no db needed
    wireframe_service = ScreenWireframeService(None)
    structure = wireframe_service.generate_basic_wireframe_structure(
        screen_name=screen_name,
        layout=layout,
    )

    return {
        "status": "success",
        "structure": structure
    }


# =============================================================================
# FULL DESIGN EXPORT (Week 96)
# =============================================================================


@router.post("/projects/{project_id}/export/full")
async def export_full_design_package(
    project_id: str,
    target_stack: str = "react",
    include_prompts: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Export complete design package for a project.

    Includes:
    - Design tokens (colors, typography, spacing)
    - Application shell configuration
    - Sample data with TypeScript interfaces
    - UI specifications
    - Wireframes
    - Implementation prompts (optional)
    """
    from app.services.design_os_service import (
        DesignTokenService,
        ApplicationShellService,
        SampleDataGenerationService,
        UISpecificationService,
        ScreenWireframeService,
        ImplementationPromptService,
    )
    from app.models.design_os import (
        DesignTokens, ApplicationShell, SampleDataSet,
        UISpecification, ScreenWireframe, ImplementationPrompt
    )

    export_data = {
        "project_id": project_id,
        "target_stack": target_stack,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": {}
    }

    # 1. Design Tokens
    token_service = DesignTokenService(db)
    tokens = await token_service.get_tokens(project_id)
    if tokens:
        export_data["artifacts"]["design_tokens"] = {
            "preset": tokens.preset_id,
            "tokens": tokens.tokens,
            "tier": tokens.tier
        }

    # 2. Application Shell
    shell_service = ApplicationShellService(db)
    shell = await shell_service.get_shell(project_id)
    if shell:
        export_data["artifacts"]["application_shell"] = {
            "shell_type": shell.shell_type,
            "navigation": shell.navigation,
            "sidebar_config": shell.sidebar_config,
            "header_config": shell.header_config,
            "footer_config": shell.footer_config,
        }

    # 3. Sample Data
    result = await db.execute(
        select(SampleDataSet).where(SampleDataSet.project_id == project_id)
    )
    sample_data_sets = list(result.scalars().all())
    if sample_data_sets:
        export_data["artifacts"]["sample_data"] = {
            "entities": [
                {
                    "name": sd.entity_name,
                    "typescript_interface": sd.typescript_interface,
                    "records": sd.records,
                }
                for sd in sample_data_sets
            ]
        }

    # 4. UI Specifications
    result = await db.execute(
        select(UISpecification).where(UISpecification.project_id == project_id)
    )
    specs = list(result.scalars().all())
    if specs:
        export_data["artifacts"]["ui_specifications"] = [
            {
                "name": spec.name,
                "purpose": spec.purpose,
                "user_flows": spec.user_flows,
                "ui_requirements": spec.ui_requirements,
                "in_scope": spec.in_scope,
                "out_of_scope": spec.out_of_scope,
                "status": spec.status,
            }
            for spec in specs
        ]

    # 5. Wireframes
    result = await db.execute(
        select(ScreenWireframe).where(ScreenWireframe.project_id == project_id)
    )
    wireframes = list(result.scalars().all())
    if wireframes:
        export_data["artifacts"]["wireframes"] = [
            {
                "name": wf.name,
                "screen_type": wf.screen_type,
                "wireframe_structure": wf.wireframe_structure,
                "annotations": wf.annotations,
                "components": wf.components,
                "responsive_variants": wf.responsive_variants,
                "version": wf.version,
            }
            for wf in wireframes
        ]

    # 6. Implementation Prompts (optional)
    if include_prompts:
        result = await db.execute(
            select(ImplementationPrompt).where(ImplementationPrompt.project_id == project_id)
        )
        prompts = list(result.scalars().all())
        if prompts:
            export_data["artifacts"]["implementation_prompts"] = [
                {
                    "name": p.name,
                    "prompt_type": p.prompt_type,
                    "prompt_content": p.prompt_content,
                    "target_stack": p.target_stack,
                    "estimated_complexity": p.estimated_complexity,
                }
                for p in prompts
            ]

    # Generate summary
    export_data["summary"] = {
        "has_design_tokens": "design_tokens" in export_data["artifacts"],
        "has_application_shell": "application_shell" in export_data["artifacts"],
        "sample_data_entities": len(export_data["artifacts"].get("sample_data", {}).get("entities", [])),
        "ui_specifications": len(export_data["artifacts"].get("ui_specifications", [])),
        "wireframes": len(export_data["artifacts"].get("wireframes", [])),
        "implementation_prompts": len(export_data["artifacts"].get("implementation_prompts", [])),
    }

    return {
        "status": "success",
        "export": export_data
    }


@router.post("/projects/{project_id}/export/markdown")
async def export_design_as_markdown(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Export design documentation as Markdown.

    Generates a comprehensive markdown document with all design artifacts.
    """
    from app.services.design_os_service import (
        DesignTokenService,
        ApplicationShellService,
    )
    from app.models.design_os import (
        SampleDataSet, UISpecification, ScreenWireframe
    )
    import json

    md_parts = [
        f"# Design Documentation: {project_id}",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "---",
        "",
    ]

    # 1. Design Tokens
    token_service = DesignTokenService(db)
    tokens = await token_service.get_tokens(project_id)
    if tokens:
        md_parts.extend([
            "## Design Tokens",
            "",
            f"Preset: **{tokens.preset_id}**",
            "",
            "### Colors",
            "",
            "```json",
            json.dumps(tokens.tokens.get("colors", {}), indent=2),
            "```",
            "",
            "### Typography",
            "",
            "```json",
            json.dumps(tokens.tokens.get("typography", {}), indent=2),
            "```",
            "",
        ])

    # 2. Application Shell
    shell_service = ApplicationShellService(db)
    shell = await shell_service.get_shell(project_id)
    if shell:
        md_parts.extend([
            "## Application Shell",
            "",
            f"Type: **{shell.shell_type}**",
            "",
            "### Navigation",
            "",
            "```json",
            json.dumps(shell.navigation, indent=2),
            "```",
            "",
        ])

    # 3. UI Specifications
    result = await db.execute(
        select(UISpecification).where(UISpecification.project_id == project_id)
    )
    specs = list(result.scalars().all())
    if specs:
        md_parts.extend([
            "## UI Specifications",
            "",
        ])
        for spec in specs:
            md_parts.extend([
                f"### {spec.name}",
                "",
                f"**Purpose:** {spec.purpose or 'N/A'}",
                "",
            ])
            if spec.user_flows:
                md_parts.append("**User Flows:**")
                md_parts.append("")
                for flow in spec.user_flows:
                    md_parts.append(f"- {flow.get('name', 'Unnamed')}")
                md_parts.append("")

    # 4. Sample Data
    result = await db.execute(
        select(SampleDataSet).where(SampleDataSet.project_id == project_id)
    )
    sample_data_sets = list(result.scalars().all())
    if sample_data_sets:
        md_parts.extend([
            "## Sample Data Interfaces",
            "",
        ])
        for sd in sample_data_sets:
            md_parts.extend([
                f"### {sd.entity_name}",
                "",
                "```typescript",
                sd.typescript_interface or "// No interface defined",
                "```",
                "",
            ])

    markdown_content = "\n".join(md_parts)

    return {
        "status": "success",
        "markdown": markdown_content,
        "filename": f"design-{project_id}.md"
    }


@router.post("/projects/{project_id}/generate-full-prompt")
async def generate_full_implementation_prompt(
    project_id: str,
    target_stack: str = "react",
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a comprehensive implementation prompt for the entire project design.

    This creates a single prompt that coding agents can use to implement
    the complete design.
    """
    from app.services.design_os_service import (
        DesignTokenService,
        ApplicationShellService,
        ImplementationPromptService,
    )
    from app.models.design_os import SampleDataSet, UISpecification, ScreenWireframe

    # Gather all design data
    token_service = DesignTokenService(db)
    tokens = await token_service.get_tokens(project_id)

    shell_service = ApplicationShellService(db)
    shell = await shell_service.get_shell(project_id)

    result = await db.execute(
        select(SampleDataSet).where(SampleDataSet.project_id == project_id)
    )
    sample_data = list(result.scalars().all())

    result = await db.execute(
        select(UISpecification).where(UISpecification.project_id == project_id)
    )
    specs = list(result.scalars().all())

    result = await db.execute(
        select(ScreenWireframe).where(ScreenWireframe.project_id == project_id)
    )
    wireframes = list(result.scalars().all())

    # Generate the full prompt
    prompt_service = ImplementationPromptService(db)

    prompt = await prompt_service.generate_full_design_prompt(
        project_id=project_id,
        design_tokens=tokens.tokens if tokens else {},
        application_shell=shell.to_dict() if shell else {},
        sample_data={
            "entities": [sd.entity_name for sd in sample_data]
        },
        ui_specs=[spec.to_dict() for spec in specs],
        wireframes=[wf.to_dict() for wf in wireframes],
        target_stack=target_stack,
    )

    return {
        "status": "success",
        "prompt": prompt.to_dict()
    }
