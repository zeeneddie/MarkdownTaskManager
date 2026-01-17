"""
Design OS Models (Week 94-95)

SQLAlchemy models for Design-First methodology:
- DesignTokens: Color, typography, spacing per project
- ApplicationShell: Navigation pattern configurations
- SampleDataSet: Generated mock data with TypeScript interfaces
- UISpecification: Section specs, user flows, scope definitions
- ScreenWireframe: Wireframe storage with version tracking
- ImplementationPrompt: Generated prompts for coding agents
- DesignTokenPreset: Reusable token libraries
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class DesignTier(str, enum.Enum):
    """Design output tiers matching extraction tiers."""
    FREE = "FREE"
    BASIC = "BASIC"
    STANDARD = "STANDARD"
    PROFESSIONAL = "PROFESSIONAL"
    PREMIUM = "PREMIUM"


class ShellType(str, enum.Enum):
    """Application shell types."""
    SIDEBAR = "sidebar"
    TOP_NAV = "top_nav"
    MINIMAL = "minimal"
    DASHBOARD = "dashboard"
    WIZARD = "wizard"


class SpecStatus(str, enum.Enum):
    """UI specification status."""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"


class PromptType(str, enum.Enum):
    """Implementation prompt types."""
    COMPONENT = "component"
    PAGE = "page"
    FEATURE = "feature"
    INTEGRATION = "integration"
    API = "api"
    FULL_PROJECT = "full_project"


class PresetCategory(str, enum.Enum):
    """Design token preset categories."""
    MINIMAL = "minimal"
    CORPORATE = "corporate"
    CREATIVE = "creative"
    DASHBOARD = "dashboard"
    ECOMMERCE = "e-commerce"
    SAAS = "saas"


class DesignTokens(Base):
    """Design tokens per project - colors, typography, spacing."""
    __tablename__ = "design_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(String(100), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    version = Column(String(50), default="1.0.0")

    # Color tokens
    colors = Column(JSONB, default={})  # {primary, secondary, accent, neutral, semantic}

    # Typography tokens
    typography = Column(JSONB, default={})  # {fontFamily, fontSize, fontWeight, lineHeight}

    # Spacing tokens
    spacing = Column(JSONB, default={})  # {xs, sm, md, lg, xl, 2xl}

    # Border/radius tokens
    borders = Column(JSONB, default={})  # {radius, width, style}

    # Shadow tokens
    shadows = Column(JSONB, default={})  # {sm, md, lg, xl}

    # Breakpoints
    breakpoints = Column(JSONB, default={})  # {mobile, tablet, desktop, wide}

    # Tier that generated this
    tier = Column(String(20), default=DesignTier.STANDARD.value)

    # Preset used (if any)
    preset_id = Column(String(100), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "project_id": self.project_id,
            "name": self.name,
            "version": self.version,
            "colors": self.colors,
            "typography": self.typography,
            "spacing": self.spacing,
            "borders": self.borders,
            "shadows": self.shadows,
            "breakpoints": self.breakpoints,
            "tier": self.tier,
            "preset_id": self.preset_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }

    def to_export_json(self):
        """Export as design-tokens.json format."""
        return {
            "version": self.version,
            "colors": self.colors,
            "typography": self.typography,
            "spacing": self.spacing,
            "borders": self.borders,
            "shadows": self.shadows,
            "breakpoints": self.breakpoints,
        }


class ApplicationShell(Base):
    """Application shell - navigation pattern configurations."""
    __tablename__ = "application_shells"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(String(100), nullable=False, index=True)
    name = Column(String(200), nullable=False)

    # Shell type
    shell_type = Column(String(50), nullable=False)

    # Navigation structure
    navigation = Column(JSONB, default={})  # {items, groups, icons}

    # Layout configuration
    layout = Column(JSONB, default={})  # {header, sidebar, footer, content}

    # Header configuration
    header_config = Column(JSONB, default={})  # {logo, search, actions, user_menu}

    # Sidebar configuration
    sidebar_config = Column(JSONB, default={})  # {width, collapsible, position}

    # Footer configuration
    footer_config = Column(JSONB, default={})  # {links, copyright, social}

    # Responsive behavior
    responsive = Column(JSONB, default={})  # {mobile_nav, breakpoints}

    # Dark mode support
    dark_mode = Column(Boolean, default=True)

    # Tier
    tier = Column(String(20), default=DesignTier.PROFESSIONAL.value)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "project_id": self.project_id,
            "name": self.name,
            "shell_type": self.shell_type,
            "navigation": self.navigation,
            "layout": self.layout,
            "header_config": self.header_config,
            "sidebar_config": self.sidebar_config,
            "footer_config": self.footer_config,
            "responsive": self.responsive,
            "dark_mode": self.dark_mode,
            "tier": self.tier,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SampleDataSet(Base):
    """Sample data sets - generated mock data with TypeScript interfaces."""
    __tablename__ = "sample_data_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(String(100), nullable=False, index=True)
    entity_name = Column(String(200), nullable=False)  # e.g., "User", "Product"

    # TypeScript interface definition
    typescript_interface = Column(Text, nullable=True)

    # Generated sample records (5-10 realistic)
    records = Column(JSONB, default=[])

    # Record count
    record_count = Column(Integer, default=5)

    # Data generation config
    generation_config = Column(JSONB, default={})  # {locale, seed, constraints}

    # Related entities
    relationships = Column(JSONB, default=[])  # [{entity, type, foreign_key}]

    # Tier
    tier = Column(String(20), default=DesignTier.STANDARD.value)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "project_id": self.project_id,
            "entity_name": self.entity_name,
            "typescript_interface": self.typescript_interface,
            "records": self.records,
            "record_count": self.record_count,
            "generation_config": self.generation_config,
            "relationships": self.relationships,
            "tier": self.tier,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_typescript_file(self):
        """Export as sample-data.ts format."""
        lines = []
        if self.typescript_interface:
            lines.append(self.typescript_interface)
            lines.append("")
        lines.append(f"export const {self.entity_name.lower()}Data: {self.entity_name}[] = {self.records};")
        return "\n".join(lines)


class UISpecification(Base):
    """UI specifications - section specs, user flows, scope definitions."""
    __tablename__ = "ui_specifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(String(100), nullable=False, index=True)
    section_id = Column(String(100), nullable=True, index=True)  # epic/feature/story ID
    name = Column(String(200), nullable=False)

    # Shape section (Design OS methodology)
    purpose = Column(Text, nullable=True)  # What is this section for?
    user_problem = Column(Text, nullable=True)  # What problem does it solve?

    # User flows
    user_flows = Column(JSONB, default=[])  # [{name, steps, entry_point, exit_point}]

    # UI requirements
    ui_requirements = Column(JSONB, default=[])  # [{component, behavior, validation}]

    # Scope boundaries
    in_scope = Column(JSONB, default=[])  # Features included
    out_of_scope = Column(JSONB, default=[])  # Features explicitly excluded

    # Information architecture
    information_architecture = Column(JSONB, default={})  # {hierarchy, navigation, content_types}

    # Interaction patterns
    interactions = Column(JSONB, default=[])  # [{trigger, action, feedback}]

    # Accessibility requirements
    accessibility = Column(JSONB, default={})  # {wcag_level, keyboard_nav, screen_reader}

    # Tier
    tier = Column(String(20), default=DesignTier.STANDARD.value)

    # Status
    status = Column(String(50), default=SpecStatus.DRAFT.value)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)

    # Relationships
    wireframes = relationship("ScreenWireframe", back_populates="specification")

    def to_dict(self):
        return {
            "id": str(self.id),
            "project_id": self.project_id,
            "section_id": self.section_id,
            "name": self.name,
            "purpose": self.purpose,
            "user_problem": self.user_problem,
            "user_flows": self.user_flows,
            "ui_requirements": self.ui_requirements,
            "in_scope": self.in_scope,
            "out_of_scope": self.out_of_scope,
            "information_architecture": self.information_architecture,
            "interactions": self.interactions,
            "accessibility": self.accessibility,
            "tier": self.tier,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_markdown(self):
        """Export as ui-spec.md format."""
        lines = [
            f"# {self.name}",
            "",
            "## Purpose",
            self.purpose or "_Not defined_",
            "",
            "## User Problem",
            self.user_problem or "_Not defined_",
            "",
            "## Scope",
            "",
            "### In Scope",
        ]
        for item in (self.in_scope or []):
            lines.append(f"- {item}")
        lines.extend([
            "",
            "### Out of Scope",
        ])
        for item in (self.out_of_scope or []):
            lines.append(f"- {item}")
        lines.extend([
            "",
            "## User Flows",
            "",
        ])
        for flow in (self.user_flows or []):
            lines.append(f"### {flow.get('name', 'Unnamed Flow')}")
            for i, step in enumerate(flow.get('steps', []), 1):
                lines.append(f"{i}. {step}")
            lines.append("")

        return "\n".join(lines)


class ScreenWireframe(Base):
    """Screen wireframes - wireframe storage with version tracking."""
    __tablename__ = "screen_wireframes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(String(100), nullable=False, index=True)
    spec_id = Column(UUID(as_uuid=True), ForeignKey('ui_specifications.id'), nullable=True)
    name = Column(String(200), nullable=False)

    # Screen type
    screen_type = Column(String(50), default="desktop")

    # Wireframe content
    wireframe_svg = Column(Text, nullable=True)
    wireframe_structure = Column(JSONB, default={})  # Structured wireframe data

    # Annotations
    annotations = Column(JSONB, default=[])  # [{x, y, text, type}]

    # Component references
    components = Column(JSONB, default=[])  # [{name, position, props}]

    # Responsive variants
    responsive_variants = Column(JSONB, default={})  # {tablet: {...}, mobile: {...}}

    # Version tracking
    version = Column(Integer, default=1)
    parent_version_id = Column(UUID(as_uuid=True), nullable=True)

    # Tier
    tier = Column(String(20), default=DesignTier.PROFESSIONAL.value)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)

    # Relationships
    specification = relationship("UISpecification", back_populates="wireframes")

    def to_dict(self):
        return {
            "id": str(self.id),
            "project_id": self.project_id,
            "spec_id": str(self.spec_id) if self.spec_id else None,
            "name": self.name,
            "screen_type": self.screen_type,
            "wireframe_svg": self.wireframe_svg,
            "wireframe_structure": self.wireframe_structure,
            "annotations": self.annotations,
            "components": self.components,
            "responsive_variants": self.responsive_variants,
            "version": self.version,
            "tier": self.tier,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ImplementationPrompt(Base):
    """Implementation prompts - generated prompts for coding agents."""
    __tablename__ = "implementation_prompts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(String(100), nullable=False, index=True)
    section_id = Column(String(100), nullable=True, index=True)

    # Prompt type
    prompt_type = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)

    # The generated prompt
    prompt_content = Column(Text, nullable=False)

    # Context included
    included_context = Column(JSONB, default={})  # {design_tokens, sample_data, ui_spec, wireframe}

    # Target framework/stack
    target_stack = Column(String(100), nullable=True)  # react, vue, angular, etc.

    # Complexity estimate
    estimated_complexity = Column(String(20), nullable=True)  # simple, moderate, complex

    # Dependencies
    dependencies = Column(JSONB, default=[])  # Other prompts/components needed first

    # Tier
    tier = Column(String(20), default=DesignTier.PREMIUM.value)

    # Usage tracking
    times_used = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "project_id": self.project_id,
            "section_id": self.section_id,
            "prompt_type": self.prompt_type,
            "name": self.name,
            "prompt_content": self.prompt_content,
            "included_context": self.included_context,
            "target_stack": self.target_stack,
            "estimated_complexity": self.estimated_complexity,
            "dependencies": self.dependencies,
            "tier": self.tier,
            "times_used": self.times_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DesignTokenPreset(Base):
    """Design token presets - reusable token libraries."""
    __tablename__ = "design_token_presets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Preset category
    category = Column(String(50), nullable=False)

    # Full token set
    tokens = Column(JSONB, nullable=False)

    # Preview/thumbnail
    preview_url = Column(String(500), nullable=True)

    # Usage count
    usage_count = Column(Integer, default=0)

    # Is system preset (not deletable)
    is_system = Column(Boolean, default=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "tokens": self.tokens,
            "preview_url": self.preview_url,
            "usage_count": self.usage_count,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
