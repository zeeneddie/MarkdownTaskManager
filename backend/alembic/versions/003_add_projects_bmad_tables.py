"""Add projects and BMAD sessions tables

Revision ID: 003
Revises: 002
Create Date: 2025-11-18

This migration adds:
1. projects table - Core project metadata with BMAD/RAG integration
2. bmad_sessions table - Tracking green-paper and brown-paper sessions
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_type', sa.String(20), nullable=False),  # 'greenfield' | 'brownfield'
        sa.Column('project_status', sa.String(20), nullable=False, server_default='draft'),  # 'draft' | 'active' | 'archived'

        # BMAD integration
        sa.Column('bmad_session_id', sa.String(100), nullable=True),  # ChromaDB document ID

        # Quality scan integration (brownfield only)
        sa.Column('quality_scan_id', sa.String(100), nullable=True),  # ChromaDB document ID

        # ChromaDB integration
        sa.Column('chroma_collection_id', sa.String(100), nullable=True),  # Dedicated collection per project

        # Business metadata
        sa.Column('business_goals', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('constraints', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('stakeholders', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Technical metadata
        sa.Column('tech_stack', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('architecture_pattern', sa.String(100), nullable=True),

        # Metrics
        sa.Column('total_story_points', sa.Integer(), nullable=True, default=0),
        sa.Column('completed_story_points', sa.Integer(), nullable=True, default=0),
        sa.Column('estimated_days', sa.Integer(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), onupdate=sa.text('NOW()'), nullable=False),
        sa.Column('activated_at', sa.DateTime(), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.CheckConstraint("project_type IN ('greenfield', 'brownfield')", name='check_project_type'),
        sa.CheckConstraint("project_status IN ('draft', 'active', 'archived')", name='check_project_status'),
    )

    # Create indexes for projects table
    op.create_index('ix_projects_name', 'projects', ['name'])
    op.create_index('ix_projects_type', 'projects', ['project_type'])
    op.create_index('ix_projects_status', 'projects', ['project_status'])
    op.create_index('ix_projects_bmad_session', 'projects', ['bmad_session_id'])
    op.create_index('ix_projects_quality_scan', 'projects', ['quality_scan_id'])

    # Create bmad_sessions table
    op.create_table(
        'bmad_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('session_type', sa.String(20), nullable=False),  # 'green-paper' | 'brown-paper'
        sa.Column('chroma_document_id', sa.String(100), nullable=False),  # Link to ChromaDB

        # Session metadata
        sa.Column('facilitator', sa.String(100), nullable=True),
        sa.Column('participants', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),

        # Session data (summary - full data in ChromaDB)
        sa.Column('session_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.CheckConstraint("session_type IN ('green-paper', 'brown-paper')", name='check_session_type'),
    )

    # Create indexes for bmad_sessions table
    op.create_index('ix_bmad_sessions_project', 'bmad_sessions', ['project_id'])
    op.create_index('ix_bmad_sessions_type', 'bmad_sessions', ['session_type'])
    op.create_index('ix_bmad_sessions_chroma', 'bmad_sessions', ['chroma_document_id'])


def downgrade() -> None:
    # Drop bmad_sessions table
    op.drop_index('ix_bmad_sessions_chroma', table_name='bmad_sessions')
    op.drop_index('ix_bmad_sessions_type', table_name='bmad_sessions')
    op.drop_index('ix_bmad_sessions_project', table_name='bmad_sessions')
    op.drop_table('bmad_sessions')

    # Drop projects table
    op.drop_index('ix_projects_quality_scan', table_name='projects')
    op.drop_index('ix_projects_bmad_session', table_name='projects')
    op.drop_index('ix_projects_status', table_name='projects')
    op.drop_index('ix_projects_type', table_name='projects')
    op.drop_index('ix_projects_name', table_name='projects')
    op.drop_table('projects')
