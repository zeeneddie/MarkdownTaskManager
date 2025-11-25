"""add_ab_testing_tables

Revision ID: 846bf79a97f4
Revises: 010
Create Date: 2025-11-25 10:39:53.508161

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '846bf79a97f4'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create experiments table
    op.create_table(
        'experiments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', sa.String(50), nullable=False, index=True),
        sa.Column('feature_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='DRAFT'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('winner_variant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED')",
            name='check_experiment_status'
        )
    )
    op.create_index('idx_experiment_agent_status', 'experiments', ['agent_id', 'status'])

    # Create experiment_variants table
    op.create_table(
        'experiment_variants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('variant_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('traffic_percentage', sa.Float(), nullable=False),
        sa.Column('config_json', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('is_control', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            'traffic_percentage >= 0 AND traffic_percentage <= 100',
            name='check_traffic_percentage'
        )
    )
    op.create_index('idx_variant_experiment', 'experiment_variants', ['experiment_id'])

    # Add foreign key for winner_variant_id (self-referential to experiment_variants)
    op.create_foreign_key(
        'fk_experiments_winner_variant',
        'experiments',
        'experiment_variants',
        ['winner_variant_id'],
        ['id']
    )

    # Create experiment_results table
    op.create_table(
        'experiment_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('task_id', sa.String(100), nullable=False, index=True),
        sa.Column('work_type', sa.String(50), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('metrics_json', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'), index=True),
        sa.ForeignKeyConstraint(['variant_id'], ['experiment_variants.id'], ondelete='CASCADE')
    )
    op.create_index('idx_result_variant_created', 'experiment_results', ['variant_id', 'created_at'])
    op.create_index('idx_result_task', 'experiment_results', ['task_id'])


def downgrade() -> None:
    # Drop in reverse order
    op.drop_table('experiment_results')
    op.drop_constraint('fk_experiments_winner_variant', 'experiments', type_='foreignkey')
    op.drop_table('experiment_variants')
    op.drop_table('experiments')
