"""Add application registry tables

Revision ID: 017
Revises: 016
Create Date: 2025-11-27

Week 57: Persistent storage for registered applications, components, and stack agents.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '017_app_registry'
down_revision = '016_human_council'
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    # Applications table - skip if exists
    if 'applications' not in existing_tables:
        op.create_table(
            'applications',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('root_path', sa.String(1024), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('application_type', sa.String(50), default='single-project'),
            sa.Column('primary_stacks', sa.JSON(), default=list),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('last_scan_at', sa.DateTime(), nullable=True),
            sa.Column('doc_path', sa.String(1024), nullable=True),
            sa.Column('test_path', sa.String(1024), nullable=True),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_applications_name', 'applications', ['name'])

    # Components table - skip if exists
    if 'components' not in existing_tables:
        op.create_table(
            'components',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('application_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('path', sa.String(1024), nullable=False),
            sa.Column('component_type', sa.String(50), nullable=False),
            sa.Column('stacks', sa.JSON(), default=list),
            sa.Column('file_count', sa.Integer(), default=0),
            sa.Column('line_count', sa.Integer(), default=0),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('last_scan_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['application_id'], ['applications.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_components_application_id', 'components', ['application_id'])

    # Stack Agents table - skip if exists
    if 'stack_agents' not in existing_tables:
        op.create_table(
            'stack_agents',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('application_id', sa.Integer(), nullable=False),
            sa.Column('stack', sa.String(50), nullable=False),
            sa.Column('role', sa.String(50), nullable=False),
            sa.Column('model_preference', sa.String(100), nullable=True),
            sa.Column('prompt_additions', sa.Text(), nullable=True),
            sa.Column('capabilities', sa.JSON(), default=list),
            sa.Column('tasks_completed', sa.Integer(), default=0),
            sa.Column('success_rate', sa.Integer(), default=0),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('last_active_at', sa.DateTime(), nullable=True),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.ForeignKeyConstraint(['application_id'], ['applications.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_stack_agents_application_id', 'stack_agents', ['application_id'])
        op.create_index('ix_stack_agents_stack', 'stack_agents', ['stack'])


def downgrade() -> None:
    op.drop_table('stack_agents')
    op.drop_table('components')
    op.drop_table('applications')
