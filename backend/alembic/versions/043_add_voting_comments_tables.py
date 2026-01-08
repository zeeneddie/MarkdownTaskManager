"""Week 90: Portal Voting and Comments System

Revision ID: 043
Revises: 042
Create Date: 2025-12-21

Features:
- Feature request voting (upvote/downvote)
- Threaded comments with mentions
- Vote aggregation and ranking
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '043'
down_revision = '042'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # Feature Request Votes
    # ==========================================================================
    op.create_table(
        'portal_feature_votes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('feature_request_id', UUID(as_uuid=True), sa.ForeignKey('portal_feature_requests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('user_name', sa.String(255), nullable=True),

        # Vote details
        sa.Column('vote_type', sa.String(10), nullable=False),  # 'up' or 'down'
        sa.Column('vote_weight', sa.Integer, default=1),  # Can be weighted for premium users

        # Tracking
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.text('NOW()')),

        # Unique constraint: one vote per user per feature
        sa.UniqueConstraint('feature_request_id', 'user_email', name='uq_feature_vote_user'),
    )

    # ==========================================================================
    # Feature Request Comments (Threaded)
    # ==========================================================================
    op.create_table(
        'portal_feature_comments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('feature_request_id', UUID(as_uuid=True), sa.ForeignKey('portal_feature_requests.id', ondelete='CASCADE'), nullable=False),

        # Comment author
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('user_name', sa.String(255), nullable=True),
        sa.Column('user_role', sa.String(50), nullable=True),  # customer, developer, admin

        # Comment content
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('content_html', sa.Text, nullable=True),  # Rendered markdown

        # Threading
        sa.Column('parent_id', UUID(as_uuid=True), sa.ForeignKey('portal_feature_comments.id', ondelete='CASCADE'), nullable=True),
        sa.Column('thread_depth', sa.Integer, default=0),

        # Mentions (@username)
        sa.Column('mentions', JSONB, nullable=True),  # List of mentioned user emails

        # Status
        sa.Column('is_edited', sa.Boolean, default=False),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('is_pinned', sa.Boolean, default=False),

        # Timestamps
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
    )

    # ==========================================================================
    # Vote Aggregation Cache (for performance)
    # ==========================================================================
    op.create_table(
        'portal_feature_vote_aggregates',
        sa.Column('feature_request_id', UUID(as_uuid=True), sa.ForeignKey('portal_feature_requests.id', ondelete='CASCADE'), primary_key=True),

        # Aggregated counts
        sa.Column('upvotes', sa.Integer, default=0),
        sa.Column('downvotes', sa.Integer, default=0),
        sa.Column('total_votes', sa.Integer, default=0),
        sa.Column('score', sa.Integer, default=0),  # upvotes - downvotes
        sa.Column('weighted_score', sa.Float, default=0.0),  # With time decay and user weight

        # Ranking
        sa.Column('rank_position', sa.Integer, nullable=True),  # Position in ranked list
        sa.Column('hot_score', sa.Float, default=0.0),  # Reddit-style hot ranking

        # Tracking
        sa.Column('last_vote_at', sa.DateTime, nullable=True),
        sa.Column('computed_at', sa.DateTime, server_default=sa.text('NOW()')),
    )

    # ==========================================================================
    # Add vote columns to portal_feature_requests for quick access
    # ==========================================================================
    op.add_column('portal_feature_requests',
        sa.Column('vote_score', sa.Integer, default=0, server_default='0')
    )
    op.add_column('portal_feature_requests',
        sa.Column('comment_count', sa.Integer, default=0, server_default='0')
    )

    # ==========================================================================
    # Create indexes
    # ==========================================================================
    # Votes indexes
    op.create_index('ix_portal_feature_votes_feature', 'portal_feature_votes', ['feature_request_id'])
    op.create_index('ix_portal_feature_votes_user', 'portal_feature_votes', ['user_email'])
    op.create_index('ix_portal_feature_votes_type', 'portal_feature_votes', ['vote_type'])

    # Comments indexes
    op.create_index('ix_portal_feature_comments_feature', 'portal_feature_comments', ['feature_request_id'])
    op.create_index('ix_portal_feature_comments_user', 'portal_feature_comments', ['user_email'])
    op.create_index('ix_portal_feature_comments_parent', 'portal_feature_comments', ['parent_id'])
    op.create_index('ix_portal_feature_comments_created', 'portal_feature_comments', ['created_at'])

    # Aggregates indexes
    op.create_index('ix_portal_vote_aggregates_score', 'portal_feature_vote_aggregates', ['score'])
    op.create_index('ix_portal_vote_aggregates_hot', 'portal_feature_vote_aggregates', ['hot_score'])
    op.create_index('ix_portal_vote_aggregates_rank', 'portal_feature_vote_aggregates', ['rank_position'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_portal_vote_aggregates_rank')
    op.drop_index('ix_portal_vote_aggregates_hot')
    op.drop_index('ix_portal_vote_aggregates_score')
    op.drop_index('ix_portal_feature_comments_created')
    op.drop_index('ix_portal_feature_comments_parent')
    op.drop_index('ix_portal_feature_comments_user')
    op.drop_index('ix_portal_feature_comments_feature')
    op.drop_index('ix_portal_feature_votes_type')
    op.drop_index('ix_portal_feature_votes_user')
    op.drop_index('ix_portal_feature_votes_feature')

    # Drop columns from portal_feature_requests
    op.drop_column('portal_feature_requests', 'comment_count')
    op.drop_column('portal_feature_requests', 'vote_score')

    # Drop tables
    op.drop_table('portal_feature_vote_aggregates')
    op.drop_table('portal_feature_comments')
    op.drop_table('portal_feature_votes')
