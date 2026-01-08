"""
Design OS Services (Week 94-96)

Core services for Design-First methodology:
- DesignTokenService: Color, typography, spacing management
- ApplicationShellService: Navigation pattern configurations
- SampleDataGenerationService: Mock data with TypeScript interfaces
- UISpecificationService: Section specs, user flows, scope definitions
- VickyAgentService: Vicky agent orchestration
- ImplementationPromptService: Ready-to-use prompts for coding agents (Week 96)
- ScreenWireframeService: Wireframe storage with version tracking (Week 96)

Tier-aware output:
- FREE: Basic wireframes, minimal tokens
- BASIC: + Color palette, typography
- STANDARD: + Full design tokens, sample data
- PROFESSIONAL: + Application shell, screen specs
- PREMIUM: + Design review, implementation prompts
"""

import json
import logging
import random
import string
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.design_os import (
    DesignTokens,
    ApplicationShell,
    SampleDataSet,
    UISpecification,
    ScreenWireframe,
    ImplementationPrompt,
    DesignTokenPreset,
    DesignTier,
    ShellType,
    SpecStatus,
    PromptType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DEFAULT DESIGN TOKEN PRESETS
# =============================================================================

DEFAULT_PRESETS = {
    "minimal": {
        "name": "Minimal Light",
        "description": "Clean, minimal design with plenty of whitespace",
        "category": "minimal",
        "tokens": {
            "colors": {
                "primary": {"50": "#f0f9ff", "500": "#3b82f6", "900": "#1e3a8a"},
                "secondary": {"50": "#f8fafc", "500": "#64748b", "900": "#0f172a"},
                "accent": {"500": "#10b981"},
                "neutral": {"100": "#f1f5f9", "500": "#64748b", "900": "#0f172a"},
                "semantic": {
                    "success": "#10b981",
                    "warning": "#f59e0b",
                    "error": "#ef4444",
                    "info": "#3b82f6"
                }
            },
            "typography": {
                "fontFamily": {
                    "sans": "Inter, system-ui, sans-serif",
                    "mono": "JetBrains Mono, monospace"
                },
                "fontSize": {
                    "xs": "0.75rem", "sm": "0.875rem", "base": "1rem",
                    "lg": "1.125rem", "xl": "1.25rem", "2xl": "1.5rem",
                    "3xl": "1.875rem", "4xl": "2.25rem"
                },
                "fontWeight": {
                    "normal": "400", "medium": "500", "semibold": "600", "bold": "700"
                },
                "lineHeight": {
                    "tight": "1.25", "normal": "1.5", "relaxed": "1.75"
                }
            },
            "spacing": {
                "xs": "0.25rem", "sm": "0.5rem", "md": "1rem",
                "lg": "1.5rem", "xl": "2rem", "2xl": "3rem"
            },
            "borders": {
                "radius": {"sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem", "full": "9999px"},
                "width": {"thin": "1px", "medium": "2px", "thick": "4px"}
            },
            "shadows": {
                "sm": "0 1px 2px rgba(0,0,0,0.05)",
                "md": "0 4px 6px rgba(0,0,0,0.1)",
                "lg": "0 10px 15px rgba(0,0,0,0.1)"
            },
            "breakpoints": {
                "mobile": "640px", "tablet": "768px", "desktop": "1024px", "wide": "1280px"
            }
        }
    },
    "dashboard": {
        "name": "Dashboard Pro",
        "description": "Professional dashboard with data visualization focus",
        "category": "dashboard",
        "tokens": {
            "colors": {
                "primary": {"50": "#eff6ff", "500": "#3b82f6", "900": "#1e40af"},
                "secondary": {"50": "#f8fafc", "500": "#475569", "900": "#0f172a"},
                "accent": {"500": "#8b5cf6"},
                "neutral": {"100": "#f1f5f9", "200": "#e2e8f0", "500": "#64748b", "800": "#1e293b", "900": "#0f172a"},
                "semantic": {
                    "success": "#22c55e", "warning": "#eab308", "error": "#ef4444", "info": "#06b6d4"
                },
                "chart": {
                    "1": "#3b82f6", "2": "#8b5cf6", "3": "#ec4899",
                    "4": "#14b8a6", "5": "#f97316", "6": "#84cc16"
                }
            },
            "typography": {
                "fontFamily": {
                    "sans": "Inter, system-ui, sans-serif",
                    "mono": "Fira Code, monospace"
                },
                "fontSize": {
                    "xs": "0.75rem", "sm": "0.875rem", "base": "1rem",
                    "lg": "1.125rem", "xl": "1.25rem", "2xl": "1.5rem"
                }
            },
            "spacing": {
                "xs": "0.25rem", "sm": "0.5rem", "md": "1rem", "lg": "1.5rem", "xl": "2rem"
            },
            "borders": {
                "radius": {"sm": "0.25rem", "md": "0.5rem", "lg": "0.75rem"}
            },
            "shadows": {
                "card": "0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)",
                "elevated": "0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23)"
            },
            "breakpoints": {
                "mobile": "640px", "tablet": "768px", "desktop": "1024px", "wide": "1440px"
            }
        }
    },
    "saas": {
        "name": "SaaS Modern",
        "description": "Modern SaaS application with vibrant accents",
        "category": "saas",
        "tokens": {
            "colors": {
                "primary": {"50": "#faf5ff", "500": "#a855f7", "900": "#581c87"},
                "secondary": {"50": "#f0fdf4", "500": "#22c55e", "900": "#14532d"},
                "accent": {"500": "#f97316"},
                "neutral": {"100": "#f5f5f5", "500": "#737373", "900": "#171717"},
                "semantic": {
                    "success": "#22c55e", "warning": "#f59e0b", "error": "#dc2626", "info": "#0ea5e9"
                }
            },
            "typography": {
                "fontFamily": {
                    "sans": "Plus Jakarta Sans, system-ui, sans-serif",
                    "mono": "IBM Plex Mono, monospace"
                }
            },
            "spacing": {
                "xs": "0.25rem", "sm": "0.5rem", "md": "1rem", "lg": "1.5rem", "xl": "2rem", "2xl": "4rem"
            },
            "borders": {
                "radius": {"sm": "0.5rem", "md": "0.75rem", "lg": "1rem", "xl": "1.5rem"}
            },
            "shadows": {
                "sm": "0 2px 4px rgba(0,0,0,0.06)",
                "md": "0 4px 8px rgba(0,0,0,0.08)",
                "lg": "0 8px 16px rgba(0,0,0,0.12)",
                "glow": "0 0 20px rgba(168, 85, 247, 0.35)"
            }
        }
    }
}


# =============================================================================
# DESIGN TOKEN SERVICE
# =============================================================================

class DesignTokenService:
    """Service for managing design tokens per project."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_tokens(
        self,
        project_id: str,
        name: str,
        tier: str = "STANDARD",
        preset_id: Optional[str] = None,
        custom_tokens: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
    ) -> DesignTokens:
        """Create design tokens for a project."""
        # Start with preset or minimal tokens
        tokens = {}
        if preset_id and preset_id in DEFAULT_PRESETS:
            tokens = DEFAULT_PRESETS[preset_id]["tokens"].copy()
        elif custom_tokens:
            tokens = custom_tokens

        # Apply tier restrictions
        tokens = self._apply_tier_restrictions(tokens, tier)

        design_tokens = DesignTokens(
            project_id=project_id,
            name=name,
            colors=tokens.get("colors", {}),
            typography=tokens.get("typography", {}),
            spacing=tokens.get("spacing", {}),
            borders=tokens.get("borders", {}),
            shadows=tokens.get("shadows", {}),
            breakpoints=tokens.get("breakpoints", {}),
            tier=tier,
            preset_id=preset_id,
            created_by=created_by,
        )

        self.db.add(design_tokens)
        await self.db.commit()
        await self.db.refresh(design_tokens)

        return design_tokens

    def _apply_tier_restrictions(self, tokens: Dict[str, Any], tier: str) -> Dict[str, Any]:
        """Apply tier-based restrictions to tokens."""
        if tier == "FREE":
            # Only basic colors and spacing
            return {
                "colors": {"primary": tokens.get("colors", {}).get("primary", {})},
                "spacing": tokens.get("spacing", {}),
            }
        elif tier == "BASIC":
            # Colors + typography
            return {
                "colors": tokens.get("colors", {}),
                "typography": tokens.get("typography", {}),
                "spacing": tokens.get("spacing", {}),
            }
        # STANDARD and above get full tokens
        return tokens

    async def get_tokens(self, project_id: str) -> Optional[DesignTokens]:
        """Get design tokens for a project."""
        result = await self.db.execute(
            select(DesignTokens).where(DesignTokens.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def update_tokens(
        self,
        project_id: str,
        updates: Dict[str, Any]
    ) -> Optional[DesignTokens]:
        """Update design tokens for a project."""
        tokens = await self.get_tokens(project_id)
        if not tokens:
            return None

        for key, value in updates.items():
            if hasattr(tokens, key):
                setattr(tokens, key, value)

        tokens.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(tokens)

        return tokens

    async def get_presets(self) -> List[Dict[str, Any]]:
        """Get available design token presets."""
        return [
            {
                "id": key,
                "name": preset["name"],
                "description": preset["description"],
                "category": preset["category"],
            }
            for key, preset in DEFAULT_PRESETS.items()
        ]

    async def export_tokens(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Export tokens as design-tokens.json format."""
        tokens = await self.get_tokens(project_id)
        if not tokens:
            return None
        return tokens.to_export_json()


# =============================================================================
# APPLICATION SHELL SERVICE
# =============================================================================

class ApplicationShellService:
    """Service for managing application shell configurations."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_shell(
        self,
        project_id: str,
        name: str,
        shell_type: str,
        navigation: Optional[Dict[str, Any]] = None,
        tier: str = "PROFESSIONAL",
    ) -> ApplicationShell:
        """Create an application shell configuration."""
        # Default navigation based on shell type
        default_nav = self._get_default_navigation(shell_type)

        shell = ApplicationShell(
            project_id=project_id,
            name=name,
            shell_type=shell_type,
            navigation=navigation or default_nav,
            layout=self._get_default_layout(shell_type),
            header_config=self._get_default_header(shell_type),
            sidebar_config=self._get_default_sidebar(shell_type),
            footer_config={},
            responsive={"mobile_nav": "drawer", "breakpoint": "768px"},
            dark_mode=True,
            tier=tier,
        )

        self.db.add(shell)
        await self.db.commit()
        await self.db.refresh(shell)

        return shell

    def _get_default_navigation(self, shell_type: str) -> Dict[str, Any]:
        """Get default navigation structure for shell type."""
        if shell_type == "sidebar":
            return {
                "items": [
                    {"label": "Dashboard", "icon": "home", "path": "/"},
                    {"label": "Projects", "icon": "folder", "path": "/projects"},
                    {"label": "Settings", "icon": "settings", "path": "/settings"},
                ],
                "groups": [
                    {"label": "Main", "items": ["Dashboard", "Projects"]},
                    {"label": "System", "items": ["Settings"]},
                ]
            }
        elif shell_type == "top_nav":
            return {
                "items": [
                    {"label": "Home", "path": "/"},
                    {"label": "Features", "path": "/features"},
                    {"label": "Pricing", "path": "/pricing"},
                    {"label": "Contact", "path": "/contact"},
                ]
            }
        return {"items": []}

    def _get_default_layout(self, shell_type: str) -> Dict[str, Any]:
        """Get default layout configuration."""
        if shell_type == "sidebar":
            return {"sidebar": True, "header": True, "footer": False, "content_padding": True}
        elif shell_type == "top_nav":
            return {"sidebar": False, "header": True, "footer": True, "content_padding": True}
        elif shell_type == "dashboard":
            return {"sidebar": True, "header": True, "footer": False, "content_padding": False}
        return {"sidebar": False, "header": True, "footer": False}

    def _get_default_header(self, shell_type: str) -> Dict[str, Any]:
        """Get default header configuration."""
        return {
            "logo": {"position": "left", "type": "text"},
            "search": shell_type == "dashboard",
            "actions": ["notifications", "user_menu"],
            "user_menu": {"avatar": True, "dropdown": True}
        }

    def _get_default_sidebar(self, shell_type: str) -> Dict[str, Any]:
        """Get default sidebar configuration."""
        if shell_type in ("sidebar", "dashboard"):
            return {
                "width": "256px",
                "collapsible": True,
                "collapsed_width": "64px",
                "position": "left"
            }
        return {}

    async def get_shell(self, project_id: str) -> Optional[ApplicationShell]:
        """Get application shell for a project."""
        result = await self.db.execute(
            select(ApplicationShell).where(ApplicationShell.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def update_shell(
        self,
        project_id: str,
        updates: Dict[str, Any]
    ) -> Optional[ApplicationShell]:
        """Update application shell."""
        shell = await self.get_shell(project_id)
        if not shell:
            return None

        for key, value in updates.items():
            if hasattr(shell, key):
                setattr(shell, key, value)

        shell.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(shell)

        return shell


# =============================================================================
# SAMPLE DATA GENERATION SERVICE
# =============================================================================

class SampleDataGenerationService:
    """Service for generating realistic mock data with TypeScript interfaces."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def generate_sample_data(
        self,
        project_id: str,
        entity_name: str,
        fields: List[Dict[str, Any]],
        record_count: int = 5,
        tier: str = "STANDARD",
        relationships: Optional[List[Dict[str, Any]]] = None,
        created_by: Optional[str] = None,
    ) -> SampleDataSet:
        """Generate sample data for an entity."""
        # Generate TypeScript interface
        ts_interface = self._generate_typescript_interface(entity_name, fields)

        # Generate records
        records = self._generate_records(fields, record_count)

        sample_data = SampleDataSet(
            project_id=project_id,
            entity_name=entity_name,
            typescript_interface=ts_interface,
            records=records,
            record_count=record_count,
            generation_config={"fields": fields},
            relationships=relationships or [],
            tier=tier,
            created_by=created_by,
        )

        self.db.add(sample_data)
        await self.db.commit()
        await self.db.refresh(sample_data)

        return sample_data

    def _generate_typescript_interface(
        self,
        entity_name: str,
        fields: List[Dict[str, Any]]
    ) -> str:
        """Generate TypeScript interface from field definitions."""
        lines = [f"export interface {entity_name} {{"]

        for field in fields:
            name = field["name"]
            ts_type = self._get_ts_type(field.get("type", "string"))
            optional = "?" if field.get("optional", False) else ""
            lines.append(f"  {name}{optional}: {ts_type};")

        lines.append("}")
        return "\n".join(lines)

    def _get_ts_type(self, field_type: str) -> str:
        """Map field type to TypeScript type."""
        type_map = {
            "string": "string",
            "number": "number",
            "integer": "number",
            "boolean": "boolean",
            "date": "Date",
            "datetime": "Date",
            "email": "string",
            "uuid": "string",
            "array": "any[]",
            "object": "Record<string, any>",
        }
        return type_map.get(field_type, "any")

    def _generate_records(
        self,
        fields: List[Dict[str, Any]],
        count: int
    ) -> List[Dict[str, Any]]:
        """Generate realistic sample records."""
        records = []

        for i in range(count):
            record = {}
            for field in fields:
                record[field["name"]] = self._generate_field_value(field, i)
            records.append(record)

        return records

    def _generate_field_value(self, field: Dict[str, Any], index: int) -> Any:
        """Generate a realistic value for a field."""
        field_type = field.get("type", "string")
        field_name = field.get("name", "").lower()

        # Name-based generation
        if "email" in field_name:
            return f"user{index + 1}@example.com"
        elif "name" in field_name and "first" in field_name:
            names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
            return names[index % len(names)]
        elif "name" in field_name and "last" in field_name:
            names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller"]
            return names[index % len(names)]
        elif "name" in field_name:
            return f"Item {index + 1}"
        elif "id" in field_name:
            return str(uuid.uuid4())
        elif "date" in field_name or "created" in field_name:
            return datetime.utcnow().isoformat()
        elif "status" in field_name:
            statuses = ["active", "pending", "completed", "archived"]
            return statuses[index % len(statuses)]
        elif "price" in field_name or "amount" in field_name:
            return round(random.uniform(10, 1000), 2)
        elif "count" in field_name or "quantity" in field_name:
            return random.randint(1, 100)

        # Type-based generation
        if field_type == "string":
            return f"Sample {field.get('name', 'value')} {index + 1}"
        elif field_type in ("number", "integer"):
            return random.randint(1, 1000)
        elif field_type == "boolean":
            return random.choice([True, False])
        elif field_type == "email":
            return f"user{index + 1}@example.com"
        elif field_type == "uuid":
            return str(uuid.uuid4())

        return f"value_{index + 1}"

    async def get_sample_data(
        self,
        project_id: str,
        entity_name: Optional[str] = None
    ) -> List[SampleDataSet]:
        """Get sample data for a project."""
        query = select(SampleDataSet).where(SampleDataSet.project_id == project_id)
        if entity_name:
            query = query.where(SampleDataSet.entity_name == entity_name)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def export_typescript(self, project_id: str) -> str:
        """Export all sample data as TypeScript file."""
        data_sets = await self.get_sample_data(project_id)

        lines = ["// Generated Sample Data", "// Auto-generated by MarQed Design OS", ""]

        for ds in data_sets:
            lines.append(ds.typescript_interface)
            lines.append("")
            lines.append(f"export const {ds.entity_name.lower()}Data: {ds.entity_name}[] = {json.dumps(ds.records, indent=2, default=str)};")
            lines.append("")

        return "\n".join(lines)


# =============================================================================
# UI SPECIFICATION SERVICE
# =============================================================================

class UISpecificationService:
    """Service for managing UI specifications."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_specification(
        self,
        project_id: str,
        name: str,
        section_id: Optional[str] = None,
        purpose: Optional[str] = None,
        user_problem: Optional[str] = None,
        tier: str = "STANDARD",
        created_by: Optional[str] = None,
    ) -> UISpecification:
        """Create a UI specification."""
        spec = UISpecification(
            project_id=project_id,
            section_id=section_id,
            name=name,
            purpose=purpose,
            user_problem=user_problem,
            user_flows=[],
            ui_requirements=[],
            in_scope=[],
            out_of_scope=[],
            information_architecture={},
            interactions=[],
            accessibility={"wcag_level": "AA", "keyboard_nav": True},
            tier=tier,
            status=SpecStatus.DRAFT.value,
            created_by=created_by,
        )

        self.db.add(spec)
        await self.db.commit()
        await self.db.refresh(spec)

        return spec

    async def add_user_flow(
        self,
        spec_id: str,
        flow_name: str,
        steps: List[str],
        entry_point: Optional[str] = None,
        exit_point: Optional[str] = None,
    ) -> UISpecification:
        """Add a user flow to a specification."""
        result = await self.db.execute(
            select(UISpecification).where(UISpecification.id == spec_id)
        )
        spec = result.scalar_one_or_none()
        if not spec:
            raise ValueError(f"Specification not found: {spec_id}")

        flow = {
            "name": flow_name,
            "steps": steps,
            "entry_point": entry_point,
            "exit_point": exit_point,
        }

        flows = spec.user_flows or []
        flows.append(flow)
        spec.user_flows = flows
        spec.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(spec)

        return spec

    async def set_scope(
        self,
        spec_id: str,
        in_scope: List[str],
        out_of_scope: List[str],
    ) -> UISpecification:
        """Set scope boundaries for a specification."""
        result = await self.db.execute(
            select(UISpecification).where(UISpecification.id == spec_id)
        )
        spec = result.scalar_one_or_none()
        if not spec:
            raise ValueError(f"Specification not found: {spec_id}")

        spec.in_scope = in_scope
        spec.out_of_scope = out_of_scope
        spec.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(spec)

        return spec

    async def add_ui_requirement(
        self,
        spec_id: str,
        component: str,
        behavior: str,
        validation: Optional[str] = None,
    ) -> UISpecification:
        """Add a UI requirement to a specification."""
        result = await self.db.execute(
            select(UISpecification).where(UISpecification.id == spec_id)
        )
        spec = result.scalar_one_or_none()
        if not spec:
            raise ValueError(f"Specification not found: {spec_id}")

        requirement = {
            "component": component,
            "behavior": behavior,
            "validation": validation,
        }

        requirements = spec.ui_requirements or []
        requirements.append(requirement)
        spec.ui_requirements = requirements
        spec.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(spec)

        return spec

    async def get_specification(self, spec_id: str) -> Optional[UISpecification]:
        """Get a UI specification by ID."""
        result = await self.db.execute(
            select(UISpecification).where(UISpecification.id == spec_id)
        )
        return result.scalar_one_or_none()

    async def get_project_specifications(
        self,
        project_id: str
    ) -> List[UISpecification]:
        """Get all specifications for a project."""
        result = await self.db.execute(
            select(UISpecification).where(UISpecification.project_id == project_id)
        )
        return result.scalars().all()

    async def update_status(
        self,
        spec_id: str,
        status: str
    ) -> Optional[UISpecification]:
        """Update specification status."""
        spec = await self.get_specification(spec_id)
        if not spec:
            return None

        spec.status = status
        spec.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(spec)

        return spec

    async def export_markdown(self, spec_id: str) -> Optional[str]:
        """Export specification as Markdown."""
        spec = await self.get_specification(spec_id)
        if not spec:
            return None
        return spec.to_markdown()


# =============================================================================
# VICKY AGENT SERVICE
# =============================================================================

class VickyAgentService:
    """
    Vicky Agent - Visual Designer

    Orchestrates design-first workflow:
    1. Shape section (purpose, user flows, scope)
    2. Design tokens (colors, typography, spacing)
    3. Sample data (TypeScript interfaces, mock records)
    4. Screen specs (wireframes, responsive design)

    Position in workflow: Between Peter (Product) and Felix (Architecture)
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.token_service = DesignTokenService(db_session)
        self.shell_service = ApplicationShellService(db_session)
        self.sample_data_service = SampleDataGenerationService(db_session)
        self.spec_service = UISpecificationService(db_session)

    async def process_shape_section(
        self,
        project_id: str,
        section_id: str,
        name: str,
        purpose: str,
        user_problem: str,
        tier: str = "STANDARD",
    ) -> Dict[str, Any]:
        """
        Process shape section - first step in Design OS.

        Creates UI specification with purpose, problem statement,
        and prepares for user flow definition.
        """
        spec = await self.spec_service.create_specification(
            project_id=project_id,
            section_id=section_id,
            name=name,
            purpose=purpose,
            user_problem=user_problem,
            tier=tier,
            created_by="vicky",
        )

        return {
            "status": "success",
            "spec_id": str(spec.id),
            "message": f"Shape section created for '{name}'",
            "next_step": "Define user flows",
        }

    async def generate_design_tokens(
        self,
        project_id: str,
        preset: str = "minimal",
        tier: str = "STANDARD",
    ) -> Dict[str, Any]:
        """Generate design tokens for a project."""
        tokens = await self.token_service.create_tokens(
            project_id=project_id,
            name=f"{project_id} Design Tokens",
            tier=tier,
            preset_id=preset,
            created_by="vicky",
        )

        return {
            "status": "success",
            "tokens_id": str(tokens.id),
            "preset_used": preset,
            "tier": tier,
            "message": "Design tokens generated",
        }

    async def generate_application_shell(
        self,
        project_id: str,
        shell_type: str = "sidebar",
        navigation: Optional[List[Dict[str, Any]]] = None,
        tier: str = "PROFESSIONAL",
    ) -> Dict[str, Any]:
        """Generate application shell configuration."""
        if tier not in ["PROFESSIONAL", "PREMIUM"]:
            return {
                "status": "skipped",
                "message": "Application shell requires PROFESSIONAL tier or higher",
            }

        shell = await self.shell_service.create_shell(
            project_id=project_id,
            name=f"{project_id} Shell",
            shell_type=shell_type,
            navigation={"items": navigation} if navigation else None,
            tier=tier,
        )

        return {
            "status": "success",
            "shell_id": str(shell.id),
            "shell_type": shell_type,
            "message": "Application shell generated",
        }

    async def generate_sample_data(
        self,
        project_id: str,
        entities: List[Dict[str, Any]],
        tier: str = "STANDARD",
    ) -> Dict[str, Any]:
        """Generate sample data for multiple entities."""
        if tier == "FREE":
            return {
                "status": "skipped",
                "message": "Sample data requires BASIC tier or higher",
            }

        results = []
        for entity in entities:
            sample = await self.sample_data_service.generate_sample_data(
                project_id=project_id,
                entity_name=entity["name"],
                fields=entity.get("fields", []),
                record_count=entity.get("record_count", 5),
                tier=tier,
                created_by="vicky",
            )
            results.append({
                "entity": entity["name"],
                "sample_id": str(sample.id),
                "records": sample.record_count,
            })

        return {
            "status": "success",
            "entities_generated": len(results),
            "results": results,
            "message": "Sample data generated",
        }

    async def run_design_phase(
        self,
        project_id: str,
        section_id: str,
        config: Dict[str, Any],
        tier: str = "STANDARD",
    ) -> Dict[str, Any]:
        """
        Run complete design phase for a section.

        This is the main orchestration method that runs all design steps
        based on the tier level.
        """
        results = {
            "project_id": project_id,
            "section_id": section_id,
            "tier": tier,
            "steps": [],
        }

        # Step 1: Shape Section (all tiers)
        if config.get("shape"):
            shape_result = await self.process_shape_section(
                project_id=project_id,
                section_id=section_id,
                name=config["shape"].get("name", section_id),
                purpose=config["shape"].get("purpose", ""),
                user_problem=config["shape"].get("user_problem", ""),
                tier=tier,
            )
            results["steps"].append({"name": "shape_section", **shape_result})

        # Step 2: Design Tokens (BASIC+)
        if tier != "FREE":
            tokens_result = await self.generate_design_tokens(
                project_id=project_id,
                preset=config.get("preset", "minimal"),
                tier=tier,
            )
            results["steps"].append({"name": "design_tokens", **tokens_result})

        # Step 3: Sample Data (STANDARD+)
        if tier in ["STANDARD", "PROFESSIONAL", "PREMIUM"] and config.get("entities"):
            sample_result = await self.generate_sample_data(
                project_id=project_id,
                entities=config["entities"],
                tier=tier,
            )
            results["steps"].append({"name": "sample_data", **sample_result})

        # Step 4: Application Shell (PROFESSIONAL+)
        if tier in ["PROFESSIONAL", "PREMIUM"] and config.get("shell"):
            shell_result = await self.generate_application_shell(
                project_id=project_id,
                shell_type=config["shell"].get("type", "sidebar"),
                navigation=config["shell"].get("navigation"),
                tier=tier,
            )
            results["steps"].append({"name": "application_shell", **shell_result})

        results["status"] = "complete"
        results["message"] = f"Design phase complete ({len(results['steps'])} steps)"

        return results

    def get_tier_capabilities(self, tier: str) -> Dict[str, bool]:
        """Get capabilities available for a tier."""
        return {
            "shape_section": True,  # All tiers
            "basic_wireframes": True,  # All tiers
            "color_palette": tier != "FREE",
            "typography": tier != "FREE",
            "full_design_tokens": tier in ["STANDARD", "PROFESSIONAL", "PREMIUM"],
            "sample_data": tier in ["STANDARD", "PROFESSIONAL", "PREMIUM"],
            "application_shell": tier in ["PROFESSIONAL", "PREMIUM"],
            "screen_specs": tier in ["PROFESSIONAL", "PREMIUM"],
            "design_review": tier == "PREMIUM",
            "implementation_prompts": tier == "PREMIUM",
        }


# =============================================================================
# IMPLEMENTATION PROMPT SERVICE (Week 96)
# =============================================================================


class ImplementationPromptService:
    """Service for generating implementation prompts for coding agents."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_prompt(
        self,
        project_id: str,
        name: str,
        prompt_type: str,
        prompt_content: str,
        section_id: Optional[str] = None,
        target_stack: Optional[str] = None,
        included_context: Optional[Dict[str, Any]] = None,
        estimated_complexity: str = "moderate",
        dependencies: Optional[List[str]] = None,
        tier: str = "PREMIUM",
    ) -> ImplementationPrompt:
        """Create an implementation prompt."""
        prompt = ImplementationPrompt(
            project_id=project_id,
            section_id=section_id,
            name=name,
            prompt_type=prompt_type,
            prompt_content=prompt_content,
            target_stack=target_stack,
            included_context=included_context or {},
            estimated_complexity=estimated_complexity,
            dependencies=dependencies or [],
            tier=tier,
        )

        self.db.add(prompt)
        await self.db.commit()
        await self.db.refresh(prompt)

        return prompt

    async def get_prompt(self, prompt_id: str) -> Optional[ImplementationPrompt]:
        """Get an implementation prompt by ID."""
        result = await self.db.execute(
            select(ImplementationPrompt).where(ImplementationPrompt.id == prompt_id)
        )
        return result.scalar_one_or_none()

    async def get_prompts_for_project(
        self,
        project_id: str,
        prompt_type: Optional[str] = None,
    ) -> List[ImplementationPrompt]:
        """Get all prompts for a project."""
        query = select(ImplementationPrompt).where(
            ImplementationPrompt.project_id == project_id
        )
        if prompt_type:
            query = query.where(ImplementationPrompt.prompt_type == prompt_type)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def generate_component_prompt(
        self,
        project_id: str,
        section_id: str,
        component_name: str,
        design_tokens: Optional[Dict] = None,
        sample_data: Optional[Dict] = None,
        ui_spec: Optional[Dict] = None,
        target_stack: str = "react",
    ) -> ImplementationPrompt:
        """Generate a component implementation prompt."""
        # Build the prompt content
        prompt_parts = [
            f"# Component: {component_name}",
            "",
            "## Task",
            f"Implement the {component_name} component based on the following specifications.",
            "",
        ]

        # Add design tokens context
        if design_tokens:
            prompt_parts.extend([
                "## Design Tokens",
                "```json",
                json.dumps(design_tokens, indent=2),
                "```",
                "",
            ])

        # Add sample data context
        if sample_data:
            prompt_parts.extend([
                "## Sample Data",
                "```typescript",
                sample_data.get("typescript_interface", "// No interface defined"),
                "```",
                "",
                "### Example Records",
                "```json",
                json.dumps(sample_data.get("records", [])[:3], indent=2),
                "```",
                "",
            ])

        # Add UI spec context
        if ui_spec:
            prompt_parts.extend([
                "## UI Requirements",
                "",
            ])
            for req in ui_spec.get("ui_requirements", []):
                prompt_parts.append(f"- **{req.get('component')}**: {req.get('behavior')}")
            prompt_parts.append("")

            if ui_spec.get("user_flows"):
                prompt_parts.extend([
                    "## User Flows",
                    "",
                ])
                for flow in ui_spec["user_flows"]:
                    prompt_parts.append(f"### {flow.get('name')}")
                    for i, step in enumerate(flow.get("steps", []), 1):
                        prompt_parts.append(f"{i}. {step}")
                    prompt_parts.append("")

        # Add implementation guidelines
        prompt_parts.extend([
            "## Implementation Guidelines",
            "",
            f"- Target framework: {target_stack}",
            "- Use design tokens for all styling",
            "- TypeScript types are mandatory",
            "- Include accessibility attributes (ARIA)",
            "- Implement responsive design for mobile/tablet/desktop",
            "- Add proper error handling and loading states",
            "",
            "## Deliverables",
            "",
            f"1. `{component_name}.tsx` - Main component file",
            f"2. `{component_name}.test.tsx` - Unit tests",
            f"3. `{component_name}.stories.tsx` - Storybook stories (optional)",
        ])

        prompt_content = "\n".join(prompt_parts)

        return await self.create_prompt(
            project_id=project_id,
            section_id=section_id,
            name=f"{component_name} Component",
            prompt_type=PromptType.COMPONENT.value,
            prompt_content=prompt_content,
            target_stack=target_stack,
            included_context={
                "design_tokens": design_tokens is not None,
                "sample_data": sample_data is not None,
                "ui_spec": ui_spec is not None,
            },
            estimated_complexity="moderate",
        )

    async def generate_feature_prompt(
        self,
        project_id: str,
        section_id: str,
        feature_name: str,
        description: str,
        components: List[str],
        api_endpoints: Optional[List[Dict]] = None,
        target_stack: str = "react",
    ) -> ImplementationPrompt:
        """Generate a feature implementation prompt."""
        prompt_parts = [
            f"# Feature: {feature_name}",
            "",
            "## Description",
            description,
            "",
            "## Components",
            "",
        ]

        for comp in components:
            prompt_parts.append(f"- [ ] {comp}")

        if api_endpoints:
            prompt_parts.extend([
                "",
                "## API Endpoints",
                "",
            ])
            for endpoint in api_endpoints:
                prompt_parts.append(
                    f"- `{endpoint.get('method', 'GET')} {endpoint.get('path')}` - {endpoint.get('description', '')}"
                )

        prompt_parts.extend([
            "",
            "## Implementation Order",
            "",
            "1. Create TypeScript interfaces for all data types",
            "2. Implement API service layer",
            "3. Build UI components (bottom-up)",
            "4. Integrate components with state management",
            "5. Add routing configuration",
            "6. Write tests",
            "",
            f"## Target Stack: {target_stack}",
        ])

        prompt_content = "\n".join(prompt_parts)

        return await self.create_prompt(
            project_id=project_id,
            section_id=section_id,
            name=f"{feature_name} Feature",
            prompt_type=PromptType.FEATURE.value,
            prompt_content=prompt_content,
            target_stack=target_stack,
            included_context={"components": components, "api_endpoints": api_endpoints},
            estimated_complexity="complex",
            dependencies=components,
        )

    async def generate_full_design_prompt(
        self,
        project_id: str,
        design_tokens: Dict,
        application_shell: Dict,
        sample_data: Dict,
        ui_specs: List[Dict],
        wireframes: List[Dict],
        target_stack: str = "react",
    ) -> ImplementationPrompt:
        """Generate a complete design implementation prompt."""
        prompt_parts = [
            "# Complete Design Implementation",
            "",
            f"## Project: {project_id}",
            "",
            "---",
            "",
            "## 1. Design Tokens",
            "",
            "Apply these design tokens globally:",
            "",
            "```json",
            json.dumps(design_tokens, indent=2)[:2000],  # Limit size
            "```",
            "",
            "## 2. Application Shell",
            "",
            f"Shell type: **{application_shell.get('shell_type', 'sidebar')}**",
            "",
        ]

        if application_shell.get("navigation"):
            prompt_parts.extend([
                "### Navigation Structure",
                "",
                "```json",
                json.dumps(application_shell.get("navigation", {}), indent=2),
                "```",
                "",
            ])

        prompt_parts.extend([
            "## 3. Screens to Implement",
            "",
        ])

        for spec in ui_specs:
            prompt_parts.extend([
                f"### {spec.get('name', 'Screen')}",
                "",
                f"Purpose: {spec.get('purpose', 'N/A')}",
                "",
            ])

        prompt_parts.extend([
            "## 4. Sample Data Entities",
            "",
        ])

        for entity in sample_data.get("entities", []):
            prompt_parts.append(f"- {entity}")

        prompt_parts.extend([
            "",
            "## 5. Implementation Checklist",
            "",
            "- [ ] Set up project with design tokens",
            "- [ ] Implement application shell/layout",
            "- [ ] Create shared components",
            "- [ ] Build feature screens",
            "- [ ] Add routing",
            "- [ ] Integrate with backend APIs",
            "- [ ] Write comprehensive tests",
            "- [ ] Review accessibility",
            "- [ ] Test responsive behavior",
        ])

        prompt_content = "\n".join(prompt_parts)

        return await self.create_prompt(
            project_id=project_id,
            name="Complete Design Implementation",
            prompt_type=PromptType.FULL_PROJECT.value,
            prompt_content=prompt_content,
            target_stack=target_stack,
            included_context={
                "design_tokens": True,
                "application_shell": True,
                "sample_data": True,
                "ui_specs": len(ui_specs),
                "wireframes": len(wireframes),
            },
            estimated_complexity="complex",
        )

    async def record_prompt_usage(self, prompt_id: str) -> None:
        """Record that a prompt was used."""
        result = await self.db.execute(
            select(ImplementationPrompt).where(ImplementationPrompt.id == prompt_id)
        )
        prompt = result.scalar_one_or_none()
        if prompt:
            prompt.times_used += 1
            prompt.last_used_at = datetime.utcnow()
            await self.db.commit()


# =============================================================================
# SCREEN WIREFRAME SERVICE (Week 96)
# =============================================================================


class ScreenWireframeService:
    """Service for managing screen wireframes with version tracking."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_wireframe(
        self,
        project_id: str,
        name: str,
        screen_type: str = "desktop",
        spec_id: Optional[str] = None,
        wireframe_svg: Optional[str] = None,
        wireframe_structure: Optional[Dict] = None,
        annotations: Optional[List[Dict]] = None,
        components: Optional[List[Dict]] = None,
        responsive_variants: Optional[Dict] = None,
        tier: str = "PROFESSIONAL",
        created_by: Optional[str] = None,
    ) -> ScreenWireframe:
        """Create a new wireframe."""
        wireframe = ScreenWireframe(
            project_id=project_id,
            name=name,
            screen_type=screen_type,
            spec_id=spec_id,
            wireframe_svg=wireframe_svg,
            wireframe_structure=wireframe_structure or {},
            annotations=annotations or [],
            components=components or [],
            responsive_variants=responsive_variants or {},
            tier=tier,
            created_by=created_by,
        )

        self.db.add(wireframe)
        await self.db.commit()
        await self.db.refresh(wireframe)

        return wireframe

    async def get_wireframe(self, wireframe_id: str) -> Optional[ScreenWireframe]:
        """Get a wireframe by ID."""
        result = await self.db.execute(
            select(ScreenWireframe).where(ScreenWireframe.id == wireframe_id)
        )
        return result.scalar_one_or_none()

    async def get_wireframes_for_project(
        self,
        project_id: str,
        screen_type: Optional[str] = None,
    ) -> List[ScreenWireframe]:
        """Get all wireframes for a project."""
        query = select(ScreenWireframe).where(
            ScreenWireframe.project_id == project_id
        )
        if screen_type:
            query = query.where(ScreenWireframe.screen_type == screen_type)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_version(
        self,
        wireframe_id: str,
        wireframe_svg: Optional[str] = None,
        wireframe_structure: Optional[Dict] = None,
        annotations: Optional[List[Dict]] = None,
    ) -> ScreenWireframe:
        """Create a new version of a wireframe."""
        # Get the original
        result = await self.db.execute(
            select(ScreenWireframe).where(ScreenWireframe.id == wireframe_id)
        )
        original = result.scalar_one_or_none()
        if not original:
            raise ValueError(f"Wireframe not found: {wireframe_id}")

        # Create new version
        new_wireframe = ScreenWireframe(
            project_id=original.project_id,
            name=original.name,
            screen_type=original.screen_type,
            spec_id=original.spec_id,
            wireframe_svg=wireframe_svg or original.wireframe_svg,
            wireframe_structure=wireframe_structure or original.wireframe_structure,
            annotations=annotations or original.annotations,
            components=original.components,
            responsive_variants=original.responsive_variants,
            tier=original.tier,
            version=original.version + 1,
            parent_version_id=original.id,
            created_by=original.created_by,
        )

        self.db.add(new_wireframe)
        await self.db.commit()
        await self.db.refresh(new_wireframe)

        return new_wireframe

    async def add_annotation(
        self,
        wireframe_id: str,
        x: int,
        y: int,
        text: str,
        annotation_type: str = "note",
    ) -> ScreenWireframe:
        """Add an annotation to a wireframe."""
        result = await self.db.execute(
            select(ScreenWireframe).where(ScreenWireframe.id == wireframe_id)
        )
        wireframe = result.scalar_one_or_none()
        if not wireframe:
            raise ValueError(f"Wireframe not found: {wireframe_id}")

        annotation = {
            "x": x,
            "y": y,
            "text": text,
            "type": annotation_type,
        }

        annotations = wireframe.annotations or []
        annotations.append(annotation)
        wireframe.annotations = annotations

        await self.db.commit()
        await self.db.refresh(wireframe)

        return wireframe

    async def add_component(
        self,
        wireframe_id: str,
        name: str,
        position: Dict[str, int],
        props: Optional[Dict] = None,
    ) -> ScreenWireframe:
        """Add a component to a wireframe."""
        result = await self.db.execute(
            select(ScreenWireframe).where(ScreenWireframe.id == wireframe_id)
        )
        wireframe = result.scalar_one_or_none()
        if not wireframe:
            raise ValueError(f"Wireframe not found: {wireframe_id}")

        component = {
            "name": name,
            "position": position,
            "props": props or {},
        }

        components = wireframe.components or []
        components.append(component)
        wireframe.components = components

        await self.db.commit()
        await self.db.refresh(wireframe)

        return wireframe

    async def add_responsive_variant(
        self,
        wireframe_id: str,
        breakpoint: str,
        variant_structure: Dict,
    ) -> ScreenWireframe:
        """Add a responsive variant to a wireframe."""
        result = await self.db.execute(
            select(ScreenWireframe).where(ScreenWireframe.id == wireframe_id)
        )
        wireframe = result.scalar_one_or_none()
        if not wireframe:
            raise ValueError(f"Wireframe not found: {wireframe_id}")

        variants = wireframe.responsive_variants or {}
        variants[breakpoint] = variant_structure
        wireframe.responsive_variants = variants

        await self.db.commit()
        await self.db.refresh(wireframe)

        return wireframe

    async def get_version_history(
        self,
        wireframe_id: str,
    ) -> List[ScreenWireframe]:
        """Get version history for a wireframe."""
        result = await self.db.execute(
            select(ScreenWireframe).where(ScreenWireframe.id == wireframe_id)
        )
        current = result.scalar_one_or_none()
        if not current:
            return []

        history = [current]

        # Walk back through parent versions
        while current.parent_version_id:
            result = await self.db.execute(
                select(ScreenWireframe).where(
                    ScreenWireframe.id == current.parent_version_id
                )
            )
            parent = result.scalar_one_or_none()
            if parent:
                history.append(parent)
                current = parent
            else:
                break

        return list(reversed(history))

    def generate_basic_wireframe_structure(
        self,
        screen_name: str,
        layout: str = "sidebar",
        sections: Optional[List[str]] = None,
    ) -> Dict:
        """Generate a basic wireframe structure."""
        sections = sections or ["header", "main", "sidebar", "footer"]

        structure = {
            "name": screen_name,
            "layout": layout,
            "sections": {},
        }

        if layout == "sidebar":
            structure["sections"] = {
                "sidebar": {"width": 250, "position": "left"},
                "header": {"height": 60},
                "main": {"flex": 1},
                "footer": {"height": 40, "optional": True},
            }
        elif layout == "top_nav":
            structure["sections"] = {
                "navbar": {"height": 60, "fixed": True},
                "main": {"flex": 1, "marginTop": 60},
                "footer": {"height": 40, "optional": True},
            }
        elif layout == "minimal":
            structure["sections"] = {
                "main": {"flex": 1, "maxWidth": 800, "centered": True},
            }
        elif layout == "dashboard":
            structure["sections"] = {
                "sidebar": {"width": 250, "position": "left"},
                "header": {"height": 60},
                "widgets": {"grid": True, "columns": 3},
                "main": {"flex": 1},
            }
        elif layout == "wizard":
            structure["sections"] = {
                "header": {"height": 80, "stepIndicator": True},
                "main": {"flex": 1, "maxWidth": 600, "centered": True},
                "footer": {"height": 60, "navigation": True},
            }

        return structure


# =============================================================================
# AGENT CONFIGURATION
# =============================================================================

VICKY_AGENT_CONFIG = {
    "name": "Vicky",
    "role": "Visual Designer",
    "llm": "mistral",
    "description": "Design-first workflow integration with design tokens, application shells, sample data, and UI specifications",
    "specialties": [
        "Design tokens",
        "Application shell",
        "Screen specs",
        "Wireframes",
        "Sample data generation",
        "UI/UX specifications",
    ],
    "tier_aware": True,
    "position_in_workflow": "Between Peter (Product) and Felix (Architecture)",
    "workflows": [
        "GREEN_PAPER",
        "BROWN_PAPER",
        "NEW_FEATURE",
        "ENHANCEMENT",
    ],
}
