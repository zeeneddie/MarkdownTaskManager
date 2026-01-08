"""Add tier override fields for granular tier selection

Week 87: Tier Override Support
- Add tier override settings to ExtractionSession (allow_epic/feature/story_override)
- Add tier override fields to ExtractionConsensus (tier_override, tier_effective, etc.)
- Add hierarchy tracking (parent_id, hierarchy_path)
- Add expected outcomes (expected_confidence, expected_cost_usd, expected_llm_count)
- Add FP estimation fields (estimated_fp, fp_breakdown)
- Add confidence explanation field

Revision ID: 041
Revises: 040
Create Date: 2024-12-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '041'
down_revision = '040'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========================================================================
    # EXTRACTION_SESSIONS - Add tier override settings
    # ========================================================================
    op.add_column('extraction_sessions',
        sa.Column('allow_epic_override', sa.String(1), nullable=True, server_default='Y'))
    op.add_column('extraction_sessions',
        sa.Column('allow_feature_override', sa.String(1), nullable=True, server_default='Y'))
    op.add_column('extraction_sessions',
        sa.Column('allow_story_override', sa.String(1), nullable=True, server_default='Y'))
    op.add_column('extraction_sessions',
        sa.Column('tier_config_locked', sa.String(1), nullable=True, server_default='N'))

    # ========================================================================
    # EXTRACTION_CONSENSUS - Add tier override and hierarchy fields
    # ========================================================================

    # Hierarchy references
    op.add_column('extraction_consensus',
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('extraction_consensus',
        sa.Column('hierarchy_path', sa.String(500), nullable=True))

    # Tier override fields
    op.add_column('extraction_consensus',
        sa.Column('tier_override', sa.String(20), nullable=True))
    op.add_column('extraction_consensus',
        sa.Column('tier_effective', sa.String(20), nullable=True))
    op.add_column('extraction_consensus',
        sa.Column('tier_locked', sa.String(1), nullable=True, server_default='N'))

    # Expected outcomes
    op.add_column('extraction_consensus',
        sa.Column('expected_confidence', sa.Float(), nullable=True))
    op.add_column('extraction_consensus',
        sa.Column('expected_cost_usd', sa.Float(), nullable=True))
    op.add_column('extraction_consensus',
        sa.Column('expected_llm_count', sa.Integer(), nullable=True))

    # Function Point estimation
    op.add_column('extraction_consensus',
        sa.Column('estimated_fp', sa.Float(), nullable=True))
    op.add_column('extraction_consensus',
        sa.Column('fp_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # Confidence explanation (Week 86)
    op.add_column('extraction_consensus',
        sa.Column('confidence_explanation', sa.Text(), nullable=True))

    # Add indexes for hierarchy queries
    op.create_index('ix_extraction_consensus_parent_id', 'extraction_consensus', ['parent_id'])
    op.create_index('ix_extraction_consensus_hierarchy_path', 'extraction_consensus', ['hierarchy_path'])
    op.create_index('ix_extraction_consensus_tier_effective', 'extraction_consensus', ['tier_effective'])

    # Add foreign key for self-reference
    op.create_foreign_key(
        'fk_extraction_consensus_parent_id',
        'extraction_consensus', 'extraction_consensus',
        ['parent_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop foreign key
    op.drop_constraint('fk_extraction_consensus_parent_id', 'extraction_consensus', type_='foreignkey')

    # Drop indexes
    op.drop_index('ix_extraction_consensus_tier_effective', table_name='extraction_consensus')
    op.drop_index('ix_extraction_consensus_hierarchy_path', table_name='extraction_consensus')
    op.drop_index('ix_extraction_consensus_parent_id', table_name='extraction_consensus')

    # Drop columns from extraction_consensus
    op.drop_column('extraction_consensus', 'confidence_explanation')
    op.drop_column('extraction_consensus', 'fp_breakdown')
    op.drop_column('extraction_consensus', 'estimated_fp')
    op.drop_column('extraction_consensus', 'expected_llm_count')
    op.drop_column('extraction_consensus', 'expected_cost_usd')
    op.drop_column('extraction_consensus', 'expected_confidence')
    op.drop_column('extraction_consensus', 'tier_locked')
    op.drop_column('extraction_consensus', 'tier_effective')
    op.drop_column('extraction_consensus', 'tier_override')
    op.drop_column('extraction_consensus', 'hierarchy_path')
    op.drop_column('extraction_consensus', 'parent_id')

    # Drop columns from extraction_sessions
    op.drop_column('extraction_sessions', 'tier_config_locked')
    op.drop_column('extraction_sessions', 'allow_story_override')
    op.drop_column('extraction_sessions', 'allow_feature_override')
    op.drop_column('extraction_sessions', 'allow_epic_override')
