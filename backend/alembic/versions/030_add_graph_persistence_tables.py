"""Week 75: Add Graph Persistence tables for Code Understanding

Revision ID: 030_graph_persistence
Revises: 029_mcp_proxy
Create Date: 2025-12-16

Tables:
- code_graph_entities: Persistent code entities (classes, functions, modules)
- code_graph_relations: Relationships between entities
- code_graph_snapshots: Graph snapshots for version comparison
- code_graph_impact_cache: Cached impact analysis results
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '030_graph_persistence'
down_revision = '029_mcp_proxy'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Code Graph Entities - persistent code entities
    op.create_table(
        'code_graph_entities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),  # class, function, method, module, import
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('qualified_name', sa.String(500)),  # Full path: module.Class.method
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('start_line', sa.Integer),
        sa.Column('end_line', sa.Integer),
        sa.Column('docstring', sa.Text),
        sa.Column('signature', sa.Text),  # Function/method signature
        sa.Column('entity_data', JSONB, default=dict),  # Additional entity metadata
        sa.Column('metrics', JSONB, default=dict),  # Complexity, lines, etc.
        sa.Column('hash', sa.String(64)),  # Content hash for change detection
        sa.Column('last_synced', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Code Graph Relations - relationships between entities
    op.create_table(
        'code_graph_relations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_entity_id', UUID(as_uuid=True), sa.ForeignKey('code_graph_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_entity_id', UUID(as_uuid=True), sa.ForeignKey('code_graph_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relation_type', sa.String(50), nullable=False),  # imports, extends, calls, uses, contains
        sa.Column('relation_data', JSONB, default=dict),  # Additional relation metadata
        sa.Column('weight', sa.Float, default=1.0),  # Relation strength/importance
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('source_entity_id', 'target_entity_id', 'relation_type', name='uq_entity_relation')
    )

    # Code Graph Snapshots - graph state at points in time
    op.create_table(
        'code_graph_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('snapshot_name', sa.String(100)),  # Optional name (e.g., "before-refactor")
        sa.Column('git_commit', sa.String(40)),  # Associated git commit
        sa.Column('entity_count', sa.Integer, default=0),
        sa.Column('relation_count', sa.Integer, default=0),
        sa.Column('file_count', sa.Integer, default=0),
        sa.Column('summary_stats', JSONB, default=dict),  # Entity type counts, coupling metrics
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Code Graph Impact Cache - cached impact analysis
    op.create_table(
        'code_graph_impact_cache',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('code_graph_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('impact_type', sa.String(50), nullable=False),  # direct, transitive, circular
        sa.Column('affected_entities', JSONB, default=list),  # List of affected entity IDs
        sa.Column('affected_files', JSONB, default=list),  # List of affected file paths
        sa.Column('impact_score', sa.Float),  # Calculated impact score
        sa.Column('depth', sa.Integer),  # Depth in dependency chain
        sa.Column('cache_valid_until', sa.DateTime),  # Cache expiration
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('entity_id', 'impact_type', name='uq_entity_impact')
    )

    # Code Graph Module Coupling - module-level coupling metrics
    op.create_table(
        'code_graph_module_coupling',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_module', sa.String(255), nullable=False),  # Module path
        sa.Column('target_module', sa.String(255), nullable=False),  # Module path
        sa.Column('coupling_count', sa.Integer, default=0),  # Number of connections
        sa.Column('coupling_type', sa.String(50)),  # import, call, inherit
        sa.Column('coupling_data', JSONB, default=dict),  # Detailed coupling info
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('project_id', 'source_module', 'target_module', name='uq_module_coupling')
    )

    # Indexes for performance
    op.create_index('ix_code_graph_entities_project', 'code_graph_entities', ['project_id'])
    op.create_index('ix_code_graph_entities_type', 'code_graph_entities', ['entity_type'])
    op.create_index('ix_code_graph_entities_file', 'code_graph_entities', ['file_path'])
    op.create_index('ix_code_graph_entities_name', 'code_graph_entities', ['name'])
    op.create_index('ix_code_graph_relations_project', 'code_graph_relations', ['project_id'])
    op.create_index('ix_code_graph_relations_source', 'code_graph_relations', ['source_entity_id'])
    op.create_index('ix_code_graph_relations_target', 'code_graph_relations', ['target_entity_id'])
    op.create_index('ix_code_graph_relations_type', 'code_graph_relations', ['relation_type'])
    op.create_index('ix_code_graph_snapshots_project', 'code_graph_snapshots', ['project_id'])
    op.create_index('ix_code_graph_impact_project', 'code_graph_impact_cache', ['project_id'])
    op.create_index('ix_code_graph_coupling_project', 'code_graph_module_coupling', ['project_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_code_graph_coupling_project')
    op.drop_index('ix_code_graph_impact_project')
    op.drop_index('ix_code_graph_snapshots_project')
    op.drop_index('ix_code_graph_relations_type')
    op.drop_index('ix_code_graph_relations_target')
    op.drop_index('ix_code_graph_relations_source')
    op.drop_index('ix_code_graph_relations_project')
    op.drop_index('ix_code_graph_entities_name')
    op.drop_index('ix_code_graph_entities_file')
    op.drop_index('ix_code_graph_entities_type')
    op.drop_index('ix_code_graph_entities_project')

    # Drop tables
    op.drop_table('code_graph_module_coupling')
    op.drop_table('code_graph_impact_cache')
    op.drop_table('code_graph_snapshots')
    op.drop_table('code_graph_relations')
    op.drop_table('code_graph_entities')
