"""Add Code Analysis Aggregation tables for Week 83

Revision ID: 038
Revises: 037
Create Date: 2025-12-19

Tables:
- code_analysis_aggregations: Unified code analysis results
- code_analysis_technology_profiles: Tech stack profiles
- code_analysis_dependency_profiles: Dependency metrics
- potpie_knowledge_graph_entries: Potpie graph data
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = '038'
down_revision = '037'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # CODE ANALYSIS AGGREGATIONS - Main aggregation results
    # =========================================================================
    op.create_table(
        'code_analysis_aggregations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True, index=True),

        # Source info
        sa.Column('repository_path', sa.String(500), nullable=False),
        sa.Column('branch', sa.String(100), default='main'),
        sa.Column('commit_hash', sa.String(40), nullable=True),  # Git commit for tracking

        # Analysis status
        sa.Column('status', sa.String(20), default='pending', index=True),  # pending, running, completed, failed
        sa.Column('duration_ms', sa.Integer, nullable=True),
        sa.Column('analysis_score', sa.Float, nullable=True),  # 0-100

        # Technology profile (embedded)
        sa.Column('primary_stack', sa.String(50), nullable=True),
        sa.Column('secondary_stacks', JSONB, default=[]),
        sa.Column('database_type', sa.String(50), nullable=True),
        sa.Column('languages', JSONB, default={}),  # {lang: file_count}
        sa.Column('frameworks', JSONB, default=[]),
        sa.Column('total_files', sa.Integer, default=0),
        sa.Column('total_loc', sa.Integer, default=0),

        # Dependency profile (embedded)
        sa.Column('module_count', sa.Integer, default=0),
        sa.Column('edge_count', sa.Integer, default=0),
        sa.Column('circular_dependencies', sa.Integer, default=0),
        sa.Column('entry_points', JSONB, default=[]),
        sa.Column('hub_modules', JSONB, default=[]),
        sa.Column('external_dependencies', sa.Integer, default=0),
        sa.Column('internal_dependencies', sa.Integer, default=0),
        sa.Column('instability_avg', sa.Float, nullable=True),
        sa.Column('coupling_score', sa.Float, nullable=True),

        # Complexity profile (embedded)
        sa.Column('avg_cyclomatic', sa.Float, nullable=True),
        sa.Column('max_cyclomatic', sa.Float, nullable=True),
        sa.Column('total_functions', sa.Integer, default=0),
        sa.Column('high_complexity_count', sa.Integer, default=0),
        sa.Column('complexity_rating', sa.String(20), nullable=True),  # low, medium, high, critical

        # Documentation profile (embedded)
        sa.Column('documented_ratio', sa.Float, nullable=True),
        sa.Column('diagram_count', sa.Integer, default=0),
        sa.Column('readme_exists', sa.Boolean, default=False),
        sa.Column('architecture_detected', sa.Boolean, default=False),

        # Raw data references
        sa.Column('stack_scan_result', JSONB, nullable=True),  # Full ScanResult
        sa.Column('codewiki_analysis_id', sa.Integer, nullable=True),

        # Errors/warnings
        sa.Column('errors', JSONB, default=[]),
        sa.Column('warnings', JSONB, default=[]),

        # Timestamps
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Index for efficient project lookups
    op.create_index(
        'ix_code_analysis_aggregations_project_status',
        'code_analysis_aggregations',
        ['project_id', 'status']
    )

    # =========================================================================
    # POTPIE KNOWLEDGE GRAPH ENTRIES - Extracted knowledge graph nodes
    # =========================================================================
    op.create_table(
        'potpie_knowledge_graph_entries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('aggregation_id', UUID(as_uuid=True),
                  sa.ForeignKey('code_analysis_aggregations.id', ondelete='CASCADE'),
                  nullable=False, index=True),

        # Node identification
        sa.Column('node_type', sa.String(50), nullable=False, index=True),  # file, function, class, module, etc.
        sa.Column('node_name', sa.String(255), nullable=False),
        sa.Column('node_path', sa.String(500), nullable=True),  # Full path in codebase

        # Node metadata
        sa.Column('language', sa.String(30), nullable=True),
        sa.Column('line_start', sa.Integer, nullable=True),
        sa.Column('line_end', sa.Integer, nullable=True),
        sa.Column('complexity', sa.Float, nullable=True),

        # Relationships (stored as JSONB for flexibility)
        sa.Column('imports', JSONB, default=[]),  # What this node imports
        sa.Column('imported_by', JSONB, default=[]),  # What imports this node
        sa.Column('calls', JSONB, default=[]),  # What this node calls
        sa.Column('called_by', JSONB, default=[]),  # What calls this node

        # Documentation
        sa.Column('docstring', sa.Text, nullable=True),
        sa.Column('description', sa.Text, nullable=True),  # LLM-generated description

        # Embedding for semantic search
        sa.Column('embedding_vector', JSONB, nullable=True),  # Vector embedding

        # Timestamps
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Index for node type queries
    op.create_index(
        'ix_potpie_kg_type_name',
        'potpie_knowledge_graph_entries',
        ['node_type', 'node_name']
    )

    # =========================================================================
    # AGGREGATION TO EXTRACTION SESSION LINK
    # =========================================================================
    # Add aggregation_id to extraction_sessions for linking
    op.add_column(
        'extraction_sessions',
        sa.Column('aggregation_id', UUID(as_uuid=True),
                  sa.ForeignKey('code_analysis_aggregations.id', ondelete='SET NULL'),
                  nullable=True)
    )


def downgrade() -> None:
    # Remove FK from extraction_sessions
    op.drop_column('extraction_sessions', 'aggregation_id')

    # Drop tables
    op.drop_index('ix_potpie_kg_type_name', 'potpie_knowledge_graph_entries')
    op.drop_table('potpie_knowledge_graph_entries')

    op.drop_index('ix_code_analysis_aggregations_project_status', 'code_analysis_aggregations')
    op.drop_table('code_analysis_aggregations')
