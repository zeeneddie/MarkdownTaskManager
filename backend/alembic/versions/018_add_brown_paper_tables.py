"""Add Brown Paper tables

Revision ID: 018_brown_paper
Revises: 017_app_registry
Create Date: 2025-11-27

Week 57 Day 2: Brown Paper reverse engineering workflow tables.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '018_brown_paper'
down_revision = '017_app_registry'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Brown Paper Sessions - main workflow tracking
    op.create_table(
        'brown_paper_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('application_name', sa.String(200), nullable=False),
        sa.Column('root_path', sa.String(500), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='scanning'),
        sa.Column('modules_count', sa.Integer(), default=0),
        sa.Column('domains_count', sa.Integer(), default=0),
        sa.Column('classes_count', sa.Integer(), default=0),
        sa.Column('functions_count', sa.Integer(), default=0),
        sa.Column('patterns_detected', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('generation_metadata', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_brown_paper_sessions_application_id', 'brown_paper_sessions', ['application_id'])
    op.create_index('ix_brown_paper_sessions_status', 'brown_paper_sessions', ['status'])

    # Brown Paper Analyses - detailed code analysis results
    op.create_table(
        'brown_paper_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('modules', postgresql.JSONB(), nullable=False, default=[]),
        sa.Column('primary_patterns', postgresql.JSONB(), nullable=False, default=[]),
        sa.Column('doc_insights', postgresql.JSONB(), nullable=False, default=[]),
        sa.Column('readme_summary', sa.Text(), nullable=True),
        sa.Column('domains', postgresql.JSONB(), nullable=False, default=[]),
        sa.Column('analysis_time_ms', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['brown_paper_sessions.id'], ondelete='CASCADE')
    )
    op.create_index('ix_brown_paper_analyses_session_id', 'brown_paper_analyses', ['session_id'])

    # Brown Paper Constitutions - generated project charters
    op.create_table(
        'brown_paper_constitutions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='draft'),
        sa.Column('content_json', postgresql.JSONB(), nullable=False),
        sa.Column('content_markdown', sa.Text(), nullable=True),
        sa.Column('generated_by', sa.String(50), default='BrownPaper'),
        sa.Column('generation_attempt', sa.Integer(), default=1),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', sa.String(100), nullable=True),
        sa.Column('review_feedback', sa.Text(), nullable=True),
        sa.Column('human_refinements', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('generation_metadata', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['brown_paper_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['items.id'], ondelete='SET NULL')
    )
    op.create_index('ix_brown_paper_constitutions_session_id', 'brown_paper_constitutions', ['session_id'])
    op.create_index('ix_brown_paper_constitutions_project_id', 'brown_paper_constitutions', ['project_id'])
    op.create_index('ix_brown_paper_constitutions_status', 'brown_paper_constitutions', ['status'])

    # Brown Paper Epics - generated epics from domains
    op.create_table(
        'brown_paper_epics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('constitution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('epic_number', sa.String(20), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), default=1),
        sa.Column('complexity', sa.String(20), default='medium'),
        sa.Column('source_domain', sa.String(100), nullable=True),
        sa.Column('source_modules', postgresql.JSONB(), nullable=True),
        sa.Column('source_entities', postgresql.JSONB(), nullable=True),
        sa.Column('features', postgresql.JSONB(), nullable=False, default=[]),
        sa.Column('linked_epic_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['constitution_id'], ['brown_paper_constitutions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['linked_epic_id'], ['task_epics.id'], ondelete='SET NULL')
    )
    op.create_index('ix_brown_paper_epics_constitution_id', 'brown_paper_epics', ['constitution_id'])

    # Brown Paper Code Modules - individual module analysis
    op.create_table(
        'brown_paper_code_modules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('path', sa.String(500), nullable=False),
        sa.Column('module_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('classes', postgresql.JSONB(), default=[]),
        sa.Column('functions', postgresql.JSONB(), default=[]),
        sa.Column('dependencies', postgresql.JSONB(), default=[]),
        sa.Column('estimated_complexity', sa.String(20), default='medium'),
        sa.Column('business_domain', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['brown_paper_sessions.id'], ondelete='CASCADE')
    )
    op.create_index('ix_brown_paper_code_modules_session_id', 'brown_paper_code_modules', ['session_id'])

    # Brown Paper Domains - extracted business domains
    op.create_table(
        'brown_paper_domains',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('modules', postgresql.JSONB(), default=[]),
        sa.Column('entities', postgresql.JSONB(), default=[]),
        sa.Column('use_cases', postgresql.JSONB(), default=[]),
        sa.Column('complexity', sa.String(20), default='medium'),
        sa.Column('priority', sa.Integer(), default=1),
        sa.Column('human_description', sa.Text(), nullable=True),
        sa.Column('human_priority', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['brown_paper_sessions.id'], ondelete='CASCADE')
    )
    op.create_index('ix_brown_paper_domains_session_id', 'brown_paper_domains', ['session_id'])


def downgrade() -> None:
    op.drop_index('ix_brown_paper_domains_session_id', table_name='brown_paper_domains')
    op.drop_table('brown_paper_domains')

    op.drop_index('ix_brown_paper_code_modules_session_id', table_name='brown_paper_code_modules')
    op.drop_table('brown_paper_code_modules')

    op.drop_index('ix_brown_paper_epics_constitution_id', table_name='brown_paper_epics')
    op.drop_table('brown_paper_epics')

    op.drop_index('ix_brown_paper_constitutions_status', table_name='brown_paper_constitutions')
    op.drop_index('ix_brown_paper_constitutions_project_id', table_name='brown_paper_constitutions')
    op.drop_index('ix_brown_paper_constitutions_session_id', table_name='brown_paper_constitutions')
    op.drop_table('brown_paper_constitutions')

    op.drop_index('ix_brown_paper_analyses_session_id', table_name='brown_paper_analyses')
    op.drop_table('brown_paper_analyses')

    op.drop_index('ix_brown_paper_sessions_status', table_name='brown_paper_sessions')
    op.drop_index('ix_brown_paper_sessions_application_id', table_name='brown_paper_sessions')
    op.drop_table('brown_paper_sessions')
