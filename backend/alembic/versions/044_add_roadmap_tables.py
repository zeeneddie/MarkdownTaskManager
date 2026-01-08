"""Week 90: Portal Roadmap System

Revision ID: 044
Revises: 043
Create Date: 2025-12-21

Features:
- Release planning and grouping
- Roadmap items with drag-drop ordering
- Public roadmap sharing
- Timeline visualization support
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '044'
down_revision = '043'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # Releases Table
    # ==========================================================================
    op.create_table(
        'portal_releases',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),

        # Release info
        sa.Column('name', sa.String(100), nullable=False),  # e.g., "v1.0", "Q1 2025"
        sa.Column('version', sa.String(50), nullable=True),  # Semantic version
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('color', sa.String(7), nullable=True),  # Hex color for UI

        # Timeline
        sa.Column('target_date', sa.Date, nullable=True),
        sa.Column('actual_date', sa.Date, nullable=True),
        sa.Column('start_date', sa.Date, nullable=True),

        # Status
        sa.Column('status', sa.String(30), default='planned'),
        # planned, in_progress, released, cancelled

        # Ordering
        sa.Column('display_order', sa.Integer, default=0),

        # Timestamps
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.text('NOW()')),
        sa.Column('released_at', sa.DateTime, nullable=True),
    )

    # ==========================================================================
    # Analysis Queue (Backlog items pending agent analysis)
    # ==========================================================================
    op.create_table(
        'portal_analysis_queue',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('item_id', sa.String(50), sa.ForeignKey('items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),

        # Queue metadata
        sa.Column('priority', sa.Integer, default=0),  # Higher = more urgent
        sa.Column('requested_by', sa.String(100), nullable=True),
        sa.Column('requested_at', sa.DateTime, server_default=sa.text('NOW()')),

        # Analysis status
        sa.Column('status', sa.String(30), default='pending'),
        # pending, analyzing, completed, failed

        # Analysis results
        sa.Column('analyzed_at', sa.DateTime, nullable=True),
        sa.Column('analyzed_by', sa.String(100), nullable=True),  # Agent name
        sa.Column('analysis_result', JSONB, nullable=True),  # Agent output

        # Timestamps
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.text('NOW()')),

        # Unique: one queue entry per item
        sa.UniqueConstraint('item_id', name='uq_analysis_queue_item'),
    )

    # ==========================================================================
    # Roadmap Items (Only analyzed items can be added)
    # ==========================================================================
    op.create_table(
        'portal_roadmap_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        # Primary link: backlog items (epic, feature, story, task)
        sa.Column('item_id', sa.String(50), sa.ForeignKey('items.id', ondelete='CASCADE'), nullable=True),
        # Optional link: portal feature requests
        sa.Column('feature_request_id', UUID(as_uuid=True), sa.ForeignKey('portal_feature_requests.id', ondelete='CASCADE'), nullable=True),
        # Link to analysis queue entry (proves item was analyzed)
        sa.Column('analysis_queue_id', UUID(as_uuid=True), sa.ForeignKey('portal_analysis_queue.id', ondelete='SET NULL'), nullable=True),
        sa.Column('release_id', UUID(as_uuid=True), sa.ForeignKey('portal_releases.id', ondelete='SET NULL'), nullable=True),

        # Positioning within release
        sa.Column('display_order', sa.Integer, default=0),
        sa.Column('lane', sa.String(50), nullable=True),  # For kanban-style view

        # Status overrides (for roadmap-specific status)
        sa.Column('roadmap_status', sa.String(30), nullable=True),
        # backlog, planned, in_progress, completed, cancelled

        # Effort estimation for timeline
        sa.Column('estimated_days', sa.Integer, nullable=True),
        sa.Column('progress_percent', sa.Integer, default=0),

        # Dependencies
        sa.Column('depends_on', JSONB, nullable=True),  # List of item_ids

        # Notes for roadmap view
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('tags', JSONB, nullable=True),  # e.g., ["critical", "customer-requested"]

        # Timestamps
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.text('NOW()')),

        # Unique: one roadmap item per backlog item
        sa.UniqueConstraint('item_id', name='uq_roadmap_item_backlog'),
        # Unique: one roadmap item per feature request
        sa.UniqueConstraint('feature_request_id', name='uq_roadmap_item_feature'),
    )

    # ==========================================================================
    # Public Roadmaps (Shareable URLs)
    # ==========================================================================
    op.create_table(
        'portal_public_roadmaps',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),

        # Sharing
        sa.Column('slug', sa.String(100), unique=True, nullable=False),  # URL-friendly identifier
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # Visibility settings
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('show_completed', sa.Boolean, default=True),
        sa.Column('show_cancelled', sa.Boolean, default=False),
        sa.Column('show_dates', sa.Boolean, default=True),
        sa.Column('show_progress', sa.Boolean, default=True),
        sa.Column('show_votes', sa.Boolean, default=True),

        # Filtering
        sa.Column('included_releases', JSONB, nullable=True),  # List of release IDs to show
        sa.Column('excluded_statuses', JSONB, nullable=True),  # Statuses to hide

        # Customization
        sa.Column('theme', sa.String(20), default='light'),  # light, dark, auto
        sa.Column('custom_css', sa.Text, nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('header_color', sa.String(7), nullable=True),

        # Analytics
        sa.Column('view_count', sa.Integer, default=0),
        sa.Column('last_viewed_at', sa.DateTime, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.text('NOW()')),
    )

    # ==========================================================================
    # Create indexes
    # ==========================================================================
    # Releases indexes
    op.create_index('ix_portal_releases_project', 'portal_releases', ['project_id'])
    op.create_index('ix_portal_releases_status', 'portal_releases', ['status'])
    op.create_index('ix_portal_releases_target_date', 'portal_releases', ['target_date'])
    op.create_index('ix_portal_releases_order', 'portal_releases', ['display_order'])

    # Analysis queue indexes
    op.create_index('ix_portal_analysis_queue_item', 'portal_analysis_queue', ['item_id'])
    op.create_index('ix_portal_analysis_queue_project', 'portal_analysis_queue', ['project_id'])
    op.create_index('ix_portal_analysis_queue_status', 'portal_analysis_queue', ['status'])
    op.create_index('ix_portal_analysis_queue_priority', 'portal_analysis_queue', ['priority'])

    # Roadmap items indexes
    op.create_index('ix_portal_roadmap_items_item', 'portal_roadmap_items', ['item_id'])
    op.create_index('ix_portal_roadmap_items_feature', 'portal_roadmap_items', ['feature_request_id'])
    op.create_index('ix_portal_roadmap_items_analysis', 'portal_roadmap_items', ['analysis_queue_id'])
    op.create_index('ix_portal_roadmap_items_release', 'portal_roadmap_items', ['release_id'])
    op.create_index('ix_portal_roadmap_items_status', 'portal_roadmap_items', ['roadmap_status'])
    op.create_index('ix_portal_roadmap_items_order', 'portal_roadmap_items', ['display_order'])

    # Public roadmaps indexes
    op.create_index('ix_portal_public_roadmaps_slug', 'portal_public_roadmaps', ['slug'])
    op.create_index('ix_portal_public_roadmaps_project', 'portal_public_roadmaps', ['project_id'])
    op.create_index('ix_portal_public_roadmaps_active', 'portal_public_roadmaps', ['is_active'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_portal_public_roadmaps_active')
    op.drop_index('ix_portal_public_roadmaps_project')
    op.drop_index('ix_portal_public_roadmaps_slug')
    op.drop_index('ix_portal_roadmap_items_order')
    op.drop_index('ix_portal_roadmap_items_status')
    op.drop_index('ix_portal_roadmap_items_release')
    op.drop_index('ix_portal_roadmap_items_analysis')
    op.drop_index('ix_portal_roadmap_items_feature')
    op.drop_index('ix_portal_roadmap_items_item')
    op.drop_index('ix_portal_analysis_queue_priority')
    op.drop_index('ix_portal_analysis_queue_status')
    op.drop_index('ix_portal_analysis_queue_project')
    op.drop_index('ix_portal_analysis_queue_item')
    op.drop_index('ix_portal_releases_order')
    op.drop_index('ix_portal_releases_target_date')
    op.drop_index('ix_portal_releases_status')
    op.drop_index('ix_portal_releases_project')

    # Drop tables (order matters due to foreign keys)
    op.drop_table('portal_public_roadmaps')
    op.drop_table('portal_roadmap_items')
    op.drop_table('portal_analysis_queue')
    op.drop_table('portal_releases')
