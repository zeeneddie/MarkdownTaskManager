"""Add Design OS tables (Week 94-95)

Revision ID: 046
Revises: 045
Create Date: 2024-12-23

Tables for Design-First methodology:
- design_tokens: Color, typography, spacing per project
- application_shells: Navigation pattern configurations
- sample_data_sets: Generated mock data with TypeScript interfaces
- ui_specifications: Section specs, user flows, scope definitions
- screen_wireframes: Wireframe storage with version tracking
- implementation_prompts: Generated prompts for coding agents
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime

# revision identifiers
revision = '046'
down_revision = '045'
branch_labels = None
depends_on = None


def upgrade():
    # Design Tokens - per-project color, typography, spacing
    op.create_table(
        'design_tokens',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.String(100), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('version', sa.String(50), default='1.0.0'),

        # Color tokens
        sa.Column('colors', JSONB, default={}),  # {primary, secondary, accent, neutral, semantic}

        # Typography tokens
        sa.Column('typography', JSONB, default={}),  # {fontFamily, fontSize, fontWeight, lineHeight}

        # Spacing tokens
        sa.Column('spacing', JSONB, default={}),  # {xs, sm, md, lg, xl, 2xl}

        # Border/radius tokens
        sa.Column('borders', JSONB, default={}),  # {radius, width, style}

        # Shadow tokens
        sa.Column('shadows', JSONB, default={}),  # {sm, md, lg, xl}

        # Breakpoints
        sa.Column('breakpoints', JSONB, default={}),  # {mobile, tablet, desktop, wide}

        # Tier that generated this
        sa.Column('tier', sa.String(20), default='STANDARD'),

        # Preset used (if any)
        sa.Column('preset_id', sa.String(100), nullable=True),

        # Metadata
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('created_by', sa.String(100), nullable=True),  # agent_id or user
    )

    # Application Shells - navigation pattern configurations
    op.create_table(
        'application_shells',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.String(100), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),

        # Shell type: sidebar, top_nav, minimal, dashboard, wizard
        sa.Column('shell_type', sa.String(50), nullable=False),

        # Navigation structure
        sa.Column('navigation', JSONB, default={}),  # {items, groups, icons}

        # Layout configuration
        sa.Column('layout', JSONB, default={}),  # {header, sidebar, footer, content}

        # Header configuration
        sa.Column('header_config', JSONB, default={}),  # {logo, search, actions, user_menu}

        # Sidebar configuration
        sa.Column('sidebar_config', JSONB, default={}),  # {width, collapsible, position}

        # Footer configuration
        sa.Column('footer_config', JSONB, default={}),  # {links, copyright, social}

        # Responsive behavior
        sa.Column('responsive', JSONB, default={}),  # {mobile_nav, breakpoints}

        # Dark mode support
        sa.Column('dark_mode', sa.Boolean, default=True),

        # Tier
        sa.Column('tier', sa.String(20), default='PROFESSIONAL'),

        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    )

    # Sample Data Sets - generated mock data
    op.create_table(
        'sample_data_sets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.String(100), nullable=False, index=True),
        sa.Column('entity_name', sa.String(200), nullable=False),  # e.g., "User", "Product"

        # TypeScript interface definition
        sa.Column('typescript_interface', sa.Text, nullable=True),

        # Generated sample records (5-10 realistic)
        sa.Column('records', JSONB, default=[]),

        # Record count
        sa.Column('record_count', sa.Integer, default=5),

        # Data generation config
        sa.Column('generation_config', JSONB, default={}),  # {locale, seed, constraints}

        # Related entities
        sa.Column('relationships', JSONB, default=[]),  # [{entity, type, foreign_key}]

        # Tier
        sa.Column('tier', sa.String(20), default='STANDARD'),

        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('created_by', sa.String(100), nullable=True),
    )

    # UI Specifications - section specs, user flows, scope
    op.create_table(
        'ui_specifications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.String(100), nullable=False, index=True),
        sa.Column('section_id', sa.String(100), nullable=True, index=True),  # epic/feature/story ID
        sa.Column('name', sa.String(200), nullable=False),

        # Shape section (Design OS methodology)
        sa.Column('purpose', sa.Text, nullable=True),  # What is this section for?
        sa.Column('user_problem', sa.Text, nullable=True),  # What problem does it solve?

        # User flows
        sa.Column('user_flows', JSONB, default=[]),  # [{name, steps, entry_point, exit_point}]

        # UI requirements
        sa.Column('ui_requirements', JSONB, default=[]),  # [{component, behavior, validation}]

        # Scope boundaries
        sa.Column('in_scope', JSONB, default=[]),  # Features included
        sa.Column('out_of_scope', JSONB, default=[]),  # Features explicitly excluded

        # Information architecture
        sa.Column('information_architecture', JSONB, default={}),  # {hierarchy, navigation, content_types}

        # Interaction patterns
        sa.Column('interactions', JSONB, default=[]),  # [{trigger, action, feedback}]

        # Accessibility requirements
        sa.Column('accessibility', JSONB, default={}),  # {wcag_level, keyboard_nav, screen_reader}

        # Tier
        sa.Column('tier', sa.String(20), default='STANDARD'),

        # Status
        sa.Column('status', sa.String(50), default='draft'),  # draft, review, approved

        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('created_by', sa.String(100), nullable=True),
    )

    # Screen Wireframes - wireframe storage with versioning
    op.create_table(
        'screen_wireframes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.String(100), nullable=False, index=True),
        sa.Column('spec_id', UUID(as_uuid=True), sa.ForeignKey('ui_specifications.id'), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),

        # Screen type: desktop, tablet, mobile
        sa.Column('screen_type', sa.String(50), default='desktop'),

        # Wireframe content (SVG or structured)
        sa.Column('wireframe_svg', sa.Text, nullable=True),
        sa.Column('wireframe_structure', JSONB, default={}),  # Structured wireframe data

        # Annotations
        sa.Column('annotations', JSONB, default=[]),  # [{x, y, text, type}]

        # Component references
        sa.Column('components', JSONB, default=[]),  # [{name, position, props}]

        # Responsive variants
        sa.Column('responsive_variants', JSONB, default={}),  # {tablet: {...}, mobile: {...}}

        # Version tracking
        sa.Column('version', sa.Integer, default=1),
        sa.Column('parent_version_id', UUID(as_uuid=True), nullable=True),

        # Tier
        sa.Column('tier', sa.String(20), default='PROFESSIONAL'),

        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('created_by', sa.String(100), nullable=True),
    )

    # Implementation Prompts - generated prompts for coding agents
    op.create_table(
        'implementation_prompts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.String(100), nullable=False, index=True),
        sa.Column('section_id', sa.String(100), nullable=True, index=True),

        # Prompt type: component, page, feature, integration
        sa.Column('prompt_type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),

        # The generated prompt
        sa.Column('prompt_content', sa.Text, nullable=False),

        # Context included
        sa.Column('included_context', JSONB, default={}),  # {design_tokens, sample_data, ui_spec, wireframe}

        # Target framework/stack
        sa.Column('target_stack', sa.String(100), nullable=True),  # react, vue, angular, etc.

        # Complexity estimate
        sa.Column('estimated_complexity', sa.String(20), nullable=True),  # simple, moderate, complex

        # Dependencies
        sa.Column('dependencies', JSONB, default=[]),  # Other prompts/components needed first

        # Tier
        sa.Column('tier', sa.String(20), default='PREMIUM'),

        # Usage tracking
        sa.Column('times_used', sa.Integer, default=0),
        sa.Column('last_used_at', sa.DateTime, nullable=True),

        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
    )

    # Design Token Presets - reusable token libraries
    op.create_table(
        'design_token_presets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(200), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),

        # Preset category: minimal, corporate, creative, dashboard, e-commerce
        sa.Column('category', sa.String(50), nullable=False),

        # Full token set
        sa.Column('tokens', JSONB, nullable=False),

        # Preview/thumbnail
        sa.Column('preview_url', sa.String(500), nullable=True),

        # Usage count
        sa.Column('usage_count', sa.Integer, default=0),

        # Is system preset (not deletable)
        sa.Column('is_system', sa.Boolean, default=False),

        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
    )

    # Create indexes
    op.create_index('idx_design_tokens_project', 'design_tokens', ['project_id'])
    op.create_index('idx_app_shells_project', 'application_shells', ['project_id'])
    op.create_index('idx_sample_data_project_entity', 'sample_data_sets', ['project_id', 'entity_name'])
    op.create_index('idx_ui_specs_project_section', 'ui_specifications', ['project_id', 'section_id'])
    op.create_index('idx_wireframes_spec', 'screen_wireframes', ['spec_id'])
    op.create_index('idx_impl_prompts_project', 'implementation_prompts', ['project_id', 'section_id'])


def downgrade():
    op.drop_index('idx_impl_prompts_project')
    op.drop_index('idx_wireframes_spec')
    op.drop_index('idx_ui_specs_project_section')
    op.drop_index('idx_sample_data_project_entity')
    op.drop_index('idx_app_shells_project')
    op.drop_index('idx_design_tokens_project')

    op.drop_table('design_token_presets')
    op.drop_table('implementation_prompts')
    op.drop_table('screen_wireframes')
    op.drop_table('ui_specifications')
    op.drop_table('sample_data_sets')
    op.drop_table('application_shells')
    op.drop_table('design_tokens')
