"""Add Project Intake Wizard Tables

Revision ID: 068
Revises: 067
Create Date: 2026-01-07

Week 145 - Project Intake Wizard

Tables:
- project_intakes: Main intake table for Brown Paper, Green Paper, Migration
- project_intake_sources: Brown Paper sources linked to migrations
- project_intake_integrations: Integration decisions (include/library/exclude)
- project_intake_scope: Brown Paper analysis scope configuration
- project_intake_features: Green Paper feature selection

Trajecten:
- Brown Paper: Discovery bestaand systeem → onderhoud of migratie
- Green Paper: Nieuw project vanaf scratch
- Migratie: Transformatie (vereist Brown Paper als voorwaarde)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '068'
down_revision = '067'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================================
    # ENUM TYPES
    # ============================================================

    # Traject type enum
    op.execute("""
        CREATE TYPE traject_type AS ENUM (
            'brown_paper',
            'green_paper',
            'migration'
        )
    """)

    # Migration type enum
    op.execute("""
        CREATE TYPE migration_type AS ENUM (
            'modernize',
            'consolidate',
            'hybrid'
        )
    """)

    # Integration action enum
    op.execute("""
        CREATE TYPE integration_action AS ENUM (
            'include',
            'library',
            'exclude'
        )
    """)

    # Intake status enum
    op.execute("""
        CREATE TYPE intake_status AS ENUM (
            'draft',
            'active',
            'analyzing',
            'awaiting_decision',
            'completed',
            'cancelled'
        )
    """)

    # Analysis tier enum
    op.execute("""
        CREATE TYPE analysis_tier AS ENUM (
            'free',
            'standard',
            'premium'
        )
    """)

    # Expected outcome enum
    op.execute("""
        CREATE TYPE expected_outcome AS ENUM (
            'insight_only',
            'maintenance',
            'migration',
            'due_diligence'
        )
    """)

    # Migration strategy enum
    op.execute("""
        CREATE TYPE migration_strategy AS ENUM (
            'big_bang',
            'module_by_module',
            'strangler_fig'
        )
    """)

    # Brown paper decision enum
    op.execute("""
        CREATE TYPE brown_paper_decision AS ENUM (
            'report_only',
            'maintenance',
            'migration'
        )
    """)

    # ============================================================
    # MAIN TABLE: project_intakes
    # ============================================================

    op.create_table(
        'project_intakes',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Basic info
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('organization', sa.String(255), nullable=True),
        sa.Column('contact_person', sa.String(255), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('description', sa.Text, nullable=True),

        # Traject type (required)
        sa.Column('traject_type', postgresql.ENUM('brown_paper', 'green_paper', 'migration', name='traject_type', create_type=False), nullable=False),

        # Migration specific (NULL for brown/green paper)
        sa.Column('migration_type', postgresql.ENUM('modernize', 'consolidate', 'hybrid', name='migration_type', create_type=False), nullable=True),

        # Target configuration (for migrations and green paper)
        sa.Column('target_stack', postgresql.JSONB, nullable=True),  # {backend, frontend, database}
        sa.Column('target_architecture', sa.String(100), nullable=True),  # Clean Architecture, DDD, etc.

        # Timeline
        sa.Column('start_date', sa.Date, nullable=True),
        sa.Column('target_go_live', sa.Date, nullable=True),
        sa.Column('hard_deadline', sa.Boolean, nullable=False, server_default='false'),

        # Migration strategy
        sa.Column('migration_strategy', postgresql.ENUM('big_bang', 'module_by_module', 'strangler_fig', name='migration_strategy', create_type=False), nullable=True),
        sa.Column('parallel_run_weeks', sa.Integer, nullable=True),

        # Brown Paper decision (after analysis)
        sa.Column('brown_paper_decision', postgresql.ENUM('report_only', 'maintenance', 'migration', name='brown_paper_decision', create_type=False), nullable=True),
        sa.Column('decision_date', sa.DateTime, nullable=True),
        sa.Column('decision_by', sa.String(255), nullable=True),
        sa.Column('decision_notes', sa.Text, nullable=True),

        # Link to follow-up migration (if brown paper leads to migration)
        sa.Column('follow_up_migration_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Status
        sa.Column('status', postgresql.ENUM('draft', 'active', 'analyzing', 'awaiting_decision', 'completed', 'cancelled', name='intake_status', create_type=False), nullable=False, server_default='draft'),

        # Generated output references
        sa.Column('generated_project_id', sa.Integer, nullable=True),  # Link to projects table after generation
        sa.Column('generated_kanban_items', sa.Integer, nullable=True),  # Count of generated kanban items
        sa.Column('generated_requirements', sa.Integer, nullable=True),  # Count of imported requirements

        # Analysis results (for brown paper)
        sa.Column('analysis_results', postgresql.JSONB, nullable=True),  # Summary of brown paper analysis

        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),

        # Tracking
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('last_modified_by', sa.String(255), nullable=True),
    )

    # Add self-referential foreign key for follow_up_migration
    op.create_foreign_key(
        'fk_project_intakes_follow_up',
        'project_intakes',
        'project_intakes',
        ['follow_up_migration_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Indexes for project_intakes
    op.create_index('ix_project_intakes_name', 'project_intakes', ['name'])
    op.create_index('ix_project_intakes_traject_type', 'project_intakes', ['traject_type'])
    op.create_index('ix_project_intakes_status', 'project_intakes', ['status'])
    op.create_index('ix_project_intakes_created_at', 'project_intakes', ['created_at'])
    op.create_index('ix_project_intakes_organization', 'project_intakes', ['organization'])

    # ============================================================
    # TABLE: project_intake_sources (Brown Paper sources for migrations)
    # ============================================================

    op.create_table(
        'project_intake_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('intake_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('project_intakes.id', ondelete='CASCADE'), nullable=False),

        # Link to Brown Paper session
        sa.Column('brown_paper_session_id', sa.String(36), sa.ForeignKey('bmad_sessions.id', ondelete='SET NULL'), nullable=True),

        # System info (denormalized for quick access)
        sa.Column('system_name', sa.String(255), nullable=False),
        sa.Column('system_path', sa.String(1024), nullable=True),
        sa.Column('repository_url', sa.String(1024), nullable=True),

        # Stats from Brown Paper (cached)
        sa.Column('module_count', sa.Integer, nullable=True),
        sa.Column('loc_count', sa.Integer, nullable=True),
        sa.Column('file_count', sa.Integer, nullable=True),
        sa.Column('quality_score', sa.Integer, nullable=True),  # 0-100
        sa.Column('security_score', sa.Integer, nullable=True),  # 0-100
        sa.Column('tech_stack', sa.String(255), nullable=True),  # e.g., "ASP Classic", ".NET 8"

        # Analysis summary (cached from brown paper)
        sa.Column('analysis_summary', postgresql.JSONB, nullable=True),

        # Order for display
        sa.Column('display_order', sa.Integer, nullable=False, server_default='0'),

        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Indexes for project_intake_sources
    op.create_index('ix_project_intake_sources_intake_id', 'project_intake_sources', ['intake_id'])
    op.create_index('ix_project_intake_sources_brown_paper', 'project_intake_sources', ['brown_paper_session_id'])
    op.create_index('ix_project_intake_sources_system_name', 'project_intake_sources', ['system_name'])

    # ============================================================
    # TABLE: project_intake_integrations (Integration decisions)
    # ============================================================

    op.create_table(
        'project_intake_integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('intake_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('project_intakes.id', ondelete='CASCADE'), nullable=False),

        # Integration info
        sa.Column('integration_name', sa.String(255), nullable=False),  # Vecozo, iJW/iWMO, Digitar, etc.
        sa.Column('source_system', sa.String(255), nullable=True),  # From which source system
        sa.Column('description', sa.Text, nullable=True),

        # Decision
        sa.Column('action', postgresql.ENUM('include', 'library', 'exclude', name='integration_action', create_type=False), nullable=False, server_default='include'),

        # Library configuration (if action = library)
        sa.Column('library_name', sa.String(255), nullable=True),  # e.g., Paramedi.Integration.iJW
        sa.Column('library_type', sa.String(50), nullable=True),  # nuget, microservice, shared_db

        # Stats
        sa.Column('file_count', sa.Integer, nullable=True),
        sa.Column('complexity', sa.String(20), nullable=True),  # low, medium, high

        # Notes
        sa.Column('decision_notes', sa.Text, nullable=True),

        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Indexes for project_intake_integrations
    op.create_index('ix_project_intake_integrations_intake_id', 'project_intake_integrations', ['intake_id'])
    op.create_index('ix_project_intake_integrations_name', 'project_intake_integrations', ['integration_name'])
    op.create_index('ix_project_intake_integrations_action', 'project_intake_integrations', ['action'])

    # ============================================================
    # TABLE: project_intake_scope (Brown Paper analysis scope)
    # ============================================================

    op.create_table(
        'project_intake_scope',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('intake_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('project_intakes.id', ondelete='CASCADE'), nullable=False, unique=True),

        # What to analyze
        sa.Column('analyze_functionality', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('analyze_quality', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('analyze_security', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('analyze_tech_debt', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('analyze_performance', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('analyze_database', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('analyze_integrations', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('analyze_documentation', sa.Boolean, nullable=False, server_default='false'),

        # Analysis tier
        sa.Column('tier', postgresql.ENUM('free', 'standard', 'premium', name='analysis_tier', create_type=False), nullable=False, server_default='standard'),

        # Expected outcome
        sa.Column('expected_outcome', postgresql.ENUM('insight_only', 'maintenance', 'migration', 'due_diligence', name='expected_outcome', create_type=False), nullable=True),

        # System location
        sa.Column('system_path', sa.String(1024), nullable=True),
        sa.Column('repository_url', sa.String(1024), nullable=True),
        sa.Column('branch', sa.String(255), nullable=True, server_default='main'),
        sa.Column('has_local_files', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('has_database_access', sa.Boolean, nullable=False, server_default='false'),

        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Index for project_intake_scope
    op.create_index('ix_project_intake_scope_intake_id', 'project_intake_scope', ['intake_id'])

    # ============================================================
    # TABLE: project_intake_features (Green Paper feature selection)
    # ============================================================

    op.create_table(
        'project_intake_features',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('intake_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('project_intakes.id', ondelete='CASCADE'), nullable=False),

        # Feature info
        sa.Column('feature_name', sa.String(255), nullable=False),  # authentication, user_management, etc.
        sa.Column('feature_category', sa.String(100), nullable=True),  # core, domain, integration
        sa.Column('enabled', sa.Boolean, nullable=False, server_default='false'),

        # Configuration
        sa.Column('configuration', postgresql.JSONB, nullable=True),  # Feature-specific config

        # Display order
        sa.Column('display_order', sa.Integer, nullable=False, server_default='0'),

        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Indexes for project_intake_features
    op.create_index('ix_project_intake_features_intake_id', 'project_intake_features', ['intake_id'])
    op.create_index('ix_project_intake_features_name', 'project_intake_features', ['feature_name'])
    op.create_index('ix_project_intake_features_enabled', 'project_intake_features', ['enabled'])

    # ============================================================
    # TABLE: project_intake_events (Audit trail)
    # ============================================================

    op.create_table(
        'project_intake_events',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('intake_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('project_intakes.id', ondelete='CASCADE'), nullable=False),

        # Event info
        sa.Column('event_type', sa.String(50), nullable=False),  # created, status_changed, analysis_started, etc.
        sa.Column('event_data', postgresql.JSONB, nullable=True),
        sa.Column('old_value', sa.Text, nullable=True),
        sa.Column('new_value', sa.Text, nullable=True),

        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(255), nullable=True),
    )

    # Indexes for project_intake_events
    op.create_index('ix_project_intake_events_intake_id', 'project_intake_events', ['intake_id'])
    op.create_index('ix_project_intake_events_event_type', 'project_intake_events', ['event_type'])
    op.create_index('ix_project_intake_events_created_at', 'project_intake_events', ['created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('project_intake_events')
    op.drop_table('project_intake_features')
    op.drop_table('project_intake_scope')
    op.drop_table('project_intake_integrations')
    op.drop_table('project_intake_sources')

    # Remove foreign key before dropping main table
    op.drop_constraint('fk_project_intakes_follow_up', 'project_intakes', type_='foreignkey')
    op.drop_table('project_intakes')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS brown_paper_decision')
    op.execute('DROP TYPE IF EXISTS migration_strategy')
    op.execute('DROP TYPE IF EXISTS expected_outcome')
    op.execute('DROP TYPE IF EXISTS analysis_tier')
    op.execute('DROP TYPE IF EXISTS intake_status')
    op.execute('DROP TYPE IF EXISTS integration_action')
    op.execute('DROP TYPE IF EXISTS migration_type')
    op.execute('DROP TYPE IF EXISTS traject_type')
