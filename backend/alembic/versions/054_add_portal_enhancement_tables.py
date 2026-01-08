"""Add portal enhancement tables for Week 118

Revision ID: 054_add_portal_enhancement_tables
Revises: 053_add_rmtoo_requirements_tables
Create Date: 2025-12-27

Week 118: Client Portal 2.0 Phase 2 - Transparency & Control

Tables:
- priority_boosts: Track when customers use priority boost
- boost_allowances: Monthly boost allowance per customer
- feature_duplicates: Track detected duplicate features
- feature_impact_previews: Felix impact analysis cache
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime
import uuid


# revision identifiers, used by Alembic.
revision = '054_add_portal_enhancement_tables'
down_revision = '053_add_rmtoo_requirements_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # BOOST ALLOWANCES - Monthly quota per customer
    # =========================================================================
    op.create_table(
        'boost_allowances',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('customer_id', sa.String(100), nullable=False, index=True),

        # Allowance period
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),

        # Quota
        sa.Column('total_boosts', sa.Integer(), default=1),  # Boosts allowed per period
        sa.Column('used_boosts', sa.Integer(), default=0),
        sa.Column('remaining_boosts', sa.Integer(), default=1),

        # Premium customers get more
        sa.Column('tier', sa.String(20), default='standard'),  # standard, premium, enterprise

        # Timestamps
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),

        # Unique per customer per period
        sa.UniqueConstraint('customer_id', 'period_start', name='uq_boost_allowance_customer_period')
    )

    # =========================================================================
    # PRIORITY BOOSTS - Individual boost usage
    # =========================================================================
    op.create_table(
        'priority_boosts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('allowance_id', UUID(as_uuid=True), sa.ForeignKey('boost_allowances.id', ondelete='CASCADE'), nullable=False),

        # What was boosted
        sa.Column('feature_request_id', sa.Integer(), nullable=False, index=True),
        sa.Column('feature_title', sa.String(200), nullable=True),

        # Boost details
        sa.Column('customer_id', sa.String(100), nullable=False, index=True),
        sa.Column('reason', sa.Text(), nullable=True),  # Why customer boosted

        # Priority change
        sa.Column('original_priority', sa.String(20), nullable=True),  # P1, P2, P3, etc.
        sa.Column('boosted_priority', sa.String(20), nullable=True),
        sa.Column('priority_delta', sa.Integer(), default=1),  # How many levels boosted

        # Effect tracking
        sa.Column('status', sa.String(20), default='active'),  # active, expired, completed
        sa.Column('expires_at', sa.DateTime(), nullable=True),  # Boost expires after X days
        sa.Column('completed_at', sa.DateTime(), nullable=True),  # When feature was delivered

        # Timestamps
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
    )

    # =========================================================================
    # FEATURE DUPLICATES - Detected similar features
    # =========================================================================
    op.create_table(
        'feature_duplicates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),

        # Original feature
        sa.Column('source_feature_id', sa.Integer(), nullable=False, index=True),
        sa.Column('source_title', sa.String(200), nullable=True),
        sa.Column('source_description', sa.Text(), nullable=True),

        # Duplicate candidate
        sa.Column('duplicate_feature_id', sa.Integer(), nullable=False, index=True),
        sa.Column('duplicate_title', sa.String(200), nullable=True),
        sa.Column('duplicate_description', sa.Text(), nullable=True),

        # Similarity metrics
        sa.Column('similarity_score', sa.Float(), nullable=False),  # 0.0 - 1.0
        sa.Column('detection_method', sa.String(30), default='chromadb'),  # chromadb, tfidf, llm
        sa.Column('embedding_model', sa.String(50), nullable=True),

        # Matching details
        sa.Column('matching_keywords', JSONB, default=[]),
        sa.Column('matching_entities', JSONB, default=[]),

        # Resolution
        sa.Column('status', sa.String(20), default='pending'),  # pending, confirmed, rejected, merged
        sa.Column('resolved_by', sa.String(100), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('merge_target_id', sa.Integer(), nullable=True),  # If merged, which feature survived

        # Timestamps
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),

        # Prevent duplicate detection entries
        sa.UniqueConstraint('source_feature_id', 'duplicate_feature_id', name='uq_duplicate_pair')
    )

    # =========================================================================
    # FEATURE IMPACT PREVIEWS - Felix analysis cache
    # =========================================================================
    op.create_table(
        'feature_impact_previews',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('feature_request_id', sa.Integer(), nullable=False, index=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),

        # Analysis metadata
        sa.Column('analyzer_agent', sa.String(30), default='felix'),
        sa.Column('analysis_version', sa.String(20), default='1.0'),

        # Impact categories
        sa.Column('architecture_impact', sa.String(20), nullable=True),  # none, low, medium, high, critical
        sa.Column('security_impact', sa.String(20), nullable=True),
        sa.Column('performance_impact', sa.String(20), nullable=True),
        sa.Column('ux_impact', sa.String(20), nullable=True),
        sa.Column('data_impact', sa.String(20), nullable=True),

        # Overall assessment
        sa.Column('overall_impact', sa.String(20), default='medium'),
        sa.Column('risk_level', sa.String(20), default='low'),  # low, medium, high
        sa.Column('complexity_score', sa.Integer(), nullable=True),  # 1-10

        # Detailed analysis
        sa.Column('affected_components', JSONB, default=[]),  # List of affected modules/services
        sa.Column('affected_apis', JSONB, default=[]),  # List of affected API endpoints
        sa.Column('dependencies', JSONB, default=[]),  # Required changes/dependencies
        sa.Column('breaking_changes', JSONB, default=[]),  # List of breaking changes

        # Recommendations
        sa.Column('implementation_approach', sa.Text(), nullable=True),
        sa.Column('recommended_priority', sa.String(20), nullable=True),
        sa.Column('estimated_effort_hours', sa.Integer(), nullable=True),
        sa.Column('suggested_sprint', sa.String(50), nullable=True),

        # Warnings and notes
        sa.Column('warnings', JSONB, default=[]),
        sa.Column('notes', sa.Text(), nullable=True),

        # LLM details
        sa.Column('llm_provider', sa.String(30), nullable=True),
        sa.Column('llm_model', sa.String(50), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),

        # Cache management
        sa.Column('is_stale', sa.Boolean(), default=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),
    )

    # Create indexes
    op.create_index('idx_boost_allowances_customer', 'boost_allowances', ['customer_id'])
    op.create_index('idx_boost_allowances_period', 'boost_allowances', ['period_start', 'period_end'])
    op.create_index('idx_priority_boosts_customer', 'priority_boosts', ['customer_id'])
    op.create_index('idx_priority_boosts_feature', 'priority_boosts', ['feature_request_id'])
    op.create_index('idx_priority_boosts_status', 'priority_boosts', ['status'])
    op.create_index('idx_feature_duplicates_source', 'feature_duplicates', ['source_feature_id'])
    op.create_index('idx_feature_duplicates_status', 'feature_duplicates', ['status'])
    op.create_index('idx_feature_duplicates_score', 'feature_duplicates', ['similarity_score'])
    op.create_index('idx_impact_previews_feature', 'feature_impact_previews', ['feature_request_id'])
    op.create_index('idx_impact_previews_stale', 'feature_impact_previews', ['is_stale'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_impact_previews_stale', 'feature_impact_previews')
    op.drop_index('idx_impact_previews_feature', 'feature_impact_previews')
    op.drop_index('idx_feature_duplicates_score', 'feature_duplicates')
    op.drop_index('idx_feature_duplicates_status', 'feature_duplicates')
    op.drop_index('idx_feature_duplicates_source', 'feature_duplicates')
    op.drop_index('idx_priority_boosts_status', 'priority_boosts')
    op.drop_index('idx_priority_boosts_feature', 'priority_boosts')
    op.drop_index('idx_priority_boosts_customer', 'priority_boosts')
    op.drop_index('idx_boost_allowances_period', 'boost_allowances')
    op.drop_index('idx_boost_allowances_customer', 'boost_allowances')

    # Drop tables (reverse order)
    op.drop_table('feature_impact_previews')
    op.drop_table('feature_duplicates')
    op.drop_table('priority_boosts')
    op.drop_table('boost_allowances')
