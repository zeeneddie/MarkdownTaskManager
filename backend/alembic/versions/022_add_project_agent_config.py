"""Add project agent configuration tables

Week 58: Dynamic agent mapping per project for different tech stacks.

Revision ID: 022_project_agent_config
Revises: 021_kanban_retry
Create Date: 2025-12-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '022_project_agent_config'
down_revision: Union[str, None] = '021_kanban_retry'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create project_agent_configs table
    op.create_table(
        'project_agent_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('project_name', sa.String(200), nullable=False),
        sa.Column('tech_stack', sa.String(50), nullable=False, server_default='custom'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('lane_agents', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tag_mappings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('item_type_agents', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('specialist_agents', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('model_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('extra_dod_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('blocking_quality_checks', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('quality_gate_config_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_project_agent_configs_project_id', 'project_agent_configs', ['project_id'])
    op.create_index('ix_project_agent_configs_tech_stack', 'project_agent_configs', ['tech_stack'])

    # Create project_lane_configs table
    op.create_table(
        'project_lane_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lane', sa.String(30), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('automatic_agent_trigger', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('custom_agents', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('dod_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('dod_min_pass_percentage', sa.Float(), nullable=True, server_default='100.0'),
        sa.Column('quality_gate_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('quality_gate_blocking', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('quality_checks', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True, server_default='3'),
        sa.Column('escalate_on_max_retries', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_config_id'], ['project_agent_configs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_project_lane_configs_lane', 'project_lane_configs', ['lane'])
    op.create_index('ix_project_lane_configs_project_config_id', 'project_lane_configs', ['project_config_id'])


def downgrade() -> None:
    op.drop_index('ix_project_lane_configs_project_config_id', table_name='project_lane_configs')
    op.drop_index('ix_project_lane_configs_lane', table_name='project_lane_configs')
    op.drop_table('project_lane_configs')

    op.drop_index('ix_project_agent_configs_tech_stack', table_name='project_agent_configs')
    op.drop_index('ix_project_agent_configs_project_id', table_name='project_agent_configs')
    op.drop_table('project_agent_configs')
