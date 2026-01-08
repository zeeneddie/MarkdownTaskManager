"""Add CodeWiki tables

Revision ID: 025_codewiki
Revises: 024_add_cctrace_observability_tables
Create Date: 2025-12-12

Week 62: Code Understanding Integration
- codewiki_analyses: Repository analysis sessions
- codewiki_modules: Module hierarchy from module_tree.json
- codewiki_diagrams: Generated Mermaid diagrams
- codewiki_agent_contexts: Pre-computed agent contexts
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '025_codewiki'
down_revision = '024'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CodeWiki analysis sessions
    op.create_table(
        'codewiki_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('repository_path', sa.String(500), nullable=False),
        sa.Column('branch', sa.String(100), default='main'),
        sa.Column('languages_detected', sa.JSON(), default=list),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('status_message', sa.Text()),
        sa.Column('progress_percent', sa.Integer(), default=0),
        sa.Column('total_files', sa.Integer(), default=0),
        sa.Column('total_modules', sa.Integer(), default=0),
        sa.Column('total_functions', sa.Integer(), default=0),
        sa.Column('total_classes', sa.Integer(), default=0),
        sa.Column('module_tree_json', sa.JSON()),
        sa.Column('metadata_json', sa.JSON()),
        sa.Column('overview_md', sa.Text()),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('duration_seconds', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_codewiki_analyses_project_id', 'codewiki_analyses', ['project_id'])
    op.create_index('ix_codewiki_analyses_status', 'codewiki_analyses', ['status'])

    # CodeWiki modules (hierarchical)
    op.create_table(
        'codewiki_modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('path', sa.String(500)),
        sa.Column('parent_module_id', sa.Integer(), nullable=True),
        sa.Column('level', sa.Integer(), default=0),
        sa.Column('description', sa.Text()),
        sa.Column('purpose', sa.Text()),
        sa.Column('files', sa.JSON(), default=list),
        sa.Column('file_count', sa.Integer(), default=0),
        sa.Column('function_count', sa.Integer(), default=0),
        sa.Column('class_count', sa.Integer(), default=0),
        sa.Column('line_count', sa.Integer(), default=0),
        sa.Column('dependencies', sa.JSON(), default=list),
        sa.Column('external_dependencies', sa.JSON(), default=list),
        sa.Column('documentation_md', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['analysis_id'], ['codewiki_analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_module_id'], ['codewiki_modules.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_codewiki_modules_analysis_id', 'codewiki_modules', ['analysis_id'])
    op.create_index('ix_codewiki_modules_parent_id', 'codewiki_modules', ['parent_module_id'])
    op.create_index('ix_codewiki_modules_name', 'codewiki_modules', ['name'])

    # CodeWiki diagrams (Mermaid)
    op.create_table(
        'codewiki_diagrams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('diagram_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('mermaid_code', sa.Text(), nullable=False),
        sa.Column('svg_content', sa.Text()),
        sa.Column('png_path', sa.String(500)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['analysis_id'], ['codewiki_analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['module_id'], ['codewiki_modules.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_codewiki_diagrams_analysis_id', 'codewiki_diagrams', ['analysis_id'])
    op.create_index('ix_codewiki_diagrams_type', 'codewiki_diagrams', ['diagram_type'])

    # CodeWiki agent contexts (pre-computed for agents)
    op.create_table(
        'codewiki_agent_contexts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('agent_name', sa.String(50), nullable=False),
        sa.Column('context_type', sa.String(50), nullable=False),
        sa.Column('context_summary', sa.Text()),
        sa.Column('context_details', sa.JSON()),
        sa.Column('times_used', sa.Integer(), default=0),
        sa.Column('last_used_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['analysis_id'], ['codewiki_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_codewiki_agent_contexts_analysis_id', 'codewiki_agent_contexts', ['analysis_id'])
    op.create_index('ix_codewiki_agent_contexts_agent', 'codewiki_agent_contexts', ['agent_name'])
    op.create_index(
        'ix_codewiki_agent_contexts_agent_type',
        'codewiki_agent_contexts',
        ['agent_name', 'context_type']
    )


def downgrade() -> None:
    op.drop_table('codewiki_agent_contexts')
    op.drop_table('codewiki_diagrams')
    op.drop_table('codewiki_modules')
    op.drop_table('codewiki_analyses')
