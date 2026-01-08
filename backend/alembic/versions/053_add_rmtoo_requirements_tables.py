"""Add rmtoo requirements management tables

Revision ID: 053
Revises: 052
Create Date: 2025-12-27

Week 117: rmtoo Requirements Management Integration

Tables:
- rmtoo_requirements: Individual requirements in rmtoo format
- rmtoo_topics: Topic hierarchy for organizing requirements
- rmtoo_sync_sessions: Track sync operations between MarQed and rmtoo
- rmtoo_exports: Track export operations (PDF, HTML, graphs)
- rmtoo_traceability_links: Links between MarQed entities and rmtoo requirements
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '053_add_rmtoo_requirements_tables'
down_revision = '052_add_hybrid_extraction_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rmtoo Topics - Hierarchical organization (MUST BE CREATED FIRST - referenced by requirements)
    op.create_table(
        'rmtoo_topics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),

        # Topic info
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),

        # Hierarchy
        sa.Column('parent_id', UUID(as_uuid=True), sa.ForeignKey('rmtoo_topics.id', ondelete='SET NULL'), nullable=True),
        sa.Column('level', sa.Integer(), default=0),  # 0 = root
        sa.Column('order_index', sa.Integer(), default=0),  # Order within parent

        # Content
        sa.Column('content', sa.Text(), nullable=True),  # Topic description text

        # Timestamps
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),

        # Unique constraint
        sa.UniqueConstraint('project_id', 'name', name='uq_rmtoo_topic_project_name')
    )

    # Rmtoo Requirements - Individual requirements in rmtoo format
    op.create_table(
        'rmtoo_requirements',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),

        # rmtoo core fields
        sa.Column('name', sa.String(100), nullable=False),  # REQ-BR-001, REQ-FR-002, etc.
        sa.Column('req_type', sa.String(50), nullable=False, default='requirement'),  # requirement, decision, constraint
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),

        # Metadata
        sa.Column('invented_on', sa.Date(), nullable=True),
        sa.Column('invented_by', sa.String(100), nullable=True),
        sa.Column('owner', sa.String(100), nullable=True, default='development'),

        # Status and priority
        sa.Column('status', sa.String(30), nullable=False, default='not done'),  # not done, done, approved
        sa.Column('priority', sa.String(50), nullable=True),  # development:5, customer:3
        sa.Column('effort_estimation', sa.Integer(), nullable=True),  # Story points or hours

        # Organization
        sa.Column('topic', sa.String(100), nullable=True),  # Topic name for grouping
        sa.Column('topic_id', UUID(as_uuid=True), sa.ForeignKey('rmtoo_topics.id', ondelete='SET NULL'), nullable=True),

        # Dependencies (rmtoo "Solved by" field)
        sa.Column('solved_by', JSONB, default=[]),  # List of requirement names
        sa.Column('depends_on', JSONB, default=[]),  # List of requirement names

        # Category for MarQed integration
        sa.Column('category', sa.String(30), nullable=False),  # BR (business rule), FR (functional), NFR, TR (technical), CMP (compliance)

        # Source tracking
        sa.Column('source_type', sa.String(30), nullable=True),  # extracted, manual, imported
        sa.Column('source_file', sa.String(500), nullable=True),  # Original file path
        sa.Column('source_line', sa.Integer(), nullable=True),  # Line number
        sa.Column('extraction_session_id', UUID(as_uuid=True), nullable=True),  # Link to hybrid extraction

        # Confidence and validation
        sa.Column('confidence', sa.Float(), nullable=True),  # 0.0 - 1.0
        sa.Column('validated', sa.Boolean(), default=False),
        sa.Column('validated_by', sa.String(100), nullable=True),
        sa.Column('validated_at', sa.DateTime(), nullable=True),

        # rmtoo file content (cached)
        sa.Column('rmtoo_content', sa.Text(), nullable=True),  # Generated .req file content

        # Timestamps
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),

        # Unique constraint per project
        sa.UniqueConstraint('project_id', 'name', name='uq_rmtoo_req_project_name')
    )

    # Rmtoo Sync Sessions - Track sync operations
    op.create_table(
        'rmtoo_sync_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),

        # Sync info
        sa.Column('direction', sa.String(20), nullable=False),  # db_to_files, files_to_db, bidirectional
        sa.Column('status', sa.String(20), nullable=False, default='pending'),  # pending, running, completed, failed

        # Statistics
        sa.Column('requirements_created', sa.Integer(), default=0),
        sa.Column('requirements_updated', sa.Integer(), default=0),
        sa.Column('requirements_deleted', sa.Integer(), default=0),
        sa.Column('topics_synced', sa.Integer(), default=0),
        sa.Column('conflicts_detected', sa.Integer(), default=0),
        sa.Column('conflicts_resolved', sa.Integer(), default=0),

        # File system
        sa.Column('output_path', sa.String(500), nullable=True),  # Path to rmtoo files
        sa.Column('files_written', JSONB, default=[]),  # List of written file paths

        # Git integration
        sa.Column('git_commit_hash', sa.String(40), nullable=True),
        sa.Column('git_auto_commit', sa.Boolean(), default=False),

        # Error handling
        sa.Column('errors', JSONB, default=[]),
        sa.Column('warnings', JSONB, default=[]),

        # Timing
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow)
    )

    # Rmtoo Exports - Track export operations
    op.create_table(
        'rmtoo_exports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),

        # Export info
        sa.Column('export_type', sa.String(30), nullable=False),  # pdf, html, graph, latex, xml
        sa.Column('status', sa.String(20), nullable=False, default='pending'),

        # Output
        sa.Column('output_path', sa.String(500), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),

        # Options
        sa.Column('include_topics', JSONB, default=[]),  # Which topics to include
        sa.Column('include_categories', JSONB, default=[]),  # Which categories (BR, FR, NFR, etc.)
        sa.Column('graph_type', sa.String(30), nullable=True),  # dependency, hierarchy, traceability

        # Generation
        sa.Column('requirements_included', sa.Integer(), default=0),
        sa.Column('pages_generated', sa.Integer(), nullable=True),  # For PDF

        # Timing
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow)
    )

    # Rmtoo Traceability Links - Links between MarQed entities and rmtoo
    op.create_table(
        'rmtoo_traceability_links',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),

        # Requirement side
        sa.Column('requirement_id', UUID(as_uuid=True), sa.ForeignKey('rmtoo_requirements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requirement_name', sa.String(100), nullable=False),

        # MarQed entity side
        sa.Column('entity_type', sa.String(30), nullable=False),  # epic, feature, story, task, business_rule
        sa.Column('entity_id', sa.String(100), nullable=False),  # ID in MarQed system
        sa.Column('entity_name', sa.String(200), nullable=True),

        # Link type
        sa.Column('link_type', sa.String(30), nullable=False),  # implements, derives_from, tests, conflicts_with

        # Confidence and validation
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('validated', sa.Boolean(), default=False),
        sa.Column('validated_by', sa.String(100), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    )

    # Create indexes
    op.create_index('idx_rmtoo_req_project', 'rmtoo_requirements', ['project_id'])
    op.create_index('idx_rmtoo_req_category', 'rmtoo_requirements', ['category'])
    op.create_index('idx_rmtoo_req_status', 'rmtoo_requirements', ['status'])
    op.create_index('idx_rmtoo_req_topic', 'rmtoo_requirements', ['topic_id'])
    op.create_index('idx_rmtoo_topics_project', 'rmtoo_topics', ['project_id'])
    op.create_index('idx_rmtoo_topics_parent', 'rmtoo_topics', ['parent_id'])
    op.create_index('idx_rmtoo_sync_project', 'rmtoo_sync_sessions', ['project_id'])
    op.create_index('idx_rmtoo_exports_project', 'rmtoo_exports', ['project_id'])
    op.create_index('idx_rmtoo_trace_req', 'rmtoo_traceability_links', ['requirement_id'])
    op.create_index('idx_rmtoo_trace_entity', 'rmtoo_traceability_links', ['entity_type', 'entity_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_rmtoo_trace_entity', 'rmtoo_traceability_links')
    op.drop_index('idx_rmtoo_trace_req', 'rmtoo_traceability_links')
    op.drop_index('idx_rmtoo_exports_project', 'rmtoo_exports')
    op.drop_index('idx_rmtoo_sync_project', 'rmtoo_sync_sessions')
    op.drop_index('idx_rmtoo_topics_parent', 'rmtoo_topics')
    op.drop_index('idx_rmtoo_topics_project', 'rmtoo_topics')
    op.drop_index('idx_rmtoo_req_topic', 'rmtoo_requirements')
    op.drop_index('idx_rmtoo_req_status', 'rmtoo_requirements')
    op.drop_index('idx_rmtoo_req_category', 'rmtoo_requirements')
    op.drop_index('idx_rmtoo_req_project', 'rmtoo_requirements')

    # Drop tables (reverse order of creation)
    op.drop_table('rmtoo_traceability_links')
    op.drop_table('rmtoo_exports')
    op.drop_table('rmtoo_sync_sessions')
    op.drop_table('rmtoo_requirements')  # Drop requirements before topics (foreign key)
    op.drop_table('rmtoo_topics')
