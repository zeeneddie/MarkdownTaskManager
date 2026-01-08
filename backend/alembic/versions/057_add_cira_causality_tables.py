"""Add Week 123 CiRA causality detection tables

CiRA Causality Detection (Week 123-125):
- Causal relation detection in requirements
- Dependency graph building
- Test case generation from cause-effect pairs

Based on: CiRA (Causality in Requirements Artifacts)
Paper: arXiv:2101.10766 - REFSQ 2021
Repository: github.com/fischJan/CiRA

Revision ID: 057_add_cira_causality_tables
Revises: 056_add_week121_chatbot_journey_tables
Create Date: 2025-12-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '057_add_cira_causality_tables'
down_revision = '056_add_week121_chatbot_journey_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============== CAUSAL SESSION TABLES ==============

    # Causal analysis sessions - analysis run metadata
    op.create_table(
        'causal_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.Integer, nullable=True, index=True),
        sa.Column('extraction_id', UUID(as_uuid=True), nullable=True, index=True),  # Link to extraction session
        # Session info
        sa.Column('name', sa.String(200), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(30), nullable=False, default='pending'),  # pending, processing, completed, failed
        # Input source
        sa.Column('source_type', sa.String(50), nullable=False, default='requirements'),  # requirements, stories, acceptance_criteria
        sa.Column('input_count', sa.Integer, nullable=False, default=0),  # Number of sentences analyzed
        # Analysis settings
        sa.Column('model_name', sa.String(100), nullable=False, default='bert-base-cased'),
        sa.Column('confidence_threshold', sa.Float, nullable=False, default=0.6),
        sa.Column('use_pos_tags', sa.Boolean, nullable=False, default=False),
        sa.Column('settings', JSONB, nullable=True),  # Additional settings
        # Results summary
        sa.Column('causal_count', sa.Integer, nullable=False, default=0),  # Sentences classified as causal
        sa.Column('non_causal_count', sa.Integer, nullable=False, default=0),
        sa.Column('relation_count', sa.Integer, nullable=False, default=0),  # Relations extracted
        sa.Column('avg_confidence', sa.Float, nullable=True),
        # Timing
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('processing_time_ms', sa.Integer, nullable=True),
        # Error handling
        sa.Column('error_message', sa.Text, nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True, onupdate=sa.func.now()),
    )

    # ============== CAUSAL CLASSIFICATION TABLES ==============

    # Causal classifications - individual sentence classifications
    op.create_table(
        'causal_classifications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('project_id', sa.Integer, nullable=True, index=True),
        # Source reference
        sa.Column('source_id', sa.String(100), nullable=True, index=True),  # Story ID, requirement ID
        sa.Column('source_type', sa.String(50), nullable=True),  # story, feature, acceptance_criteria
        # Input
        sa.Column('sentence', sa.Text, nullable=False),
        sa.Column('sentence_index', sa.Integer, nullable=False, default=0),  # Position in source
        # Classification result
        sa.Column('is_causal', sa.Boolean, nullable=False),
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('probability_causal', sa.Float, nullable=False),
        sa.Column('probability_non_causal', sa.Float, nullable=False),
        # CiRA feature annotations (optional)
        sa.Column('is_explicit', sa.Boolean, nullable=True),  # Explicit causality marker
        sa.Column('is_marked', sa.Boolean, nullable=True),  # Contains cause marker
        sa.Column('is_single_sentence', sa.Boolean, nullable=True),  # Single sentence causality
        sa.Column('has_single_cause', sa.Boolean, nullable=True),
        sa.Column('has_single_effect', sa.Boolean, nullable=True),
        sa.Column('is_event_chain', sa.Boolean, nullable=True),  # Chain of events
        sa.Column('markers', JSONB, nullable=True),  # Detected causal markers (if, when, because, etc.)
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        # Foreign key
        sa.ForeignKeyConstraint(['session_id'], ['causal_sessions.id'], ondelete='CASCADE'),
    )

    # ============== CAUSAL RELATIONS TABLES ==============

    # Causal relations - extracted cause-effect pairs
    op.create_table(
        'causal_relations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('classification_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('project_id', sa.Integer, nullable=True, index=True),
        # Relation type
        sa.Column('relation_type', sa.String(30), nullable=False),  # CAUSES, ENABLES, BLOCKS, DEPENDS_ON
        sa.Column('confidence', sa.Float, nullable=False),
        # Cause side
        sa.Column('cause_source_id', sa.String(100), nullable=True, index=True),  # Story/requirement ID
        sa.Column('cause_text', sa.Text, nullable=False),
        sa.Column('cause_entity', sa.String(200), nullable=True),  # Extracted entity (if applicable)
        # Effect side
        sa.Column('effect_source_id', sa.String(100), nullable=True, index=True),
        sa.Column('effect_text', sa.Text, nullable=False),
        sa.Column('effect_entity', sa.String(200), nullable=True),
        # Extraction details
        sa.Column('causal_marker', sa.String(50), nullable=True),  # The detected marker (if, when, because)
        sa.Column('extraction_method', sa.String(50), nullable=False, default='bert'),  # bert, rule_based, hybrid
        sa.Column('relation_metadata', JSONB, nullable=True),
        # Validation
        sa.Column('human_validated', sa.Boolean, nullable=False, default=False),
        sa.Column('human_approved', sa.Boolean, nullable=True),
        sa.Column('validation_notes', sa.Text, nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        # Foreign keys
        sa.ForeignKeyConstraint(['session_id'], ['causal_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['classification_id'], ['causal_classifications.id'], ondelete='SET NULL'),
    )

    # ============== DEPENDENCY GRAPH TABLES ==============

    # Dependency graphs - serialized graph structures
    op.create_table(
        'causal_dependency_graphs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('project_id', sa.Integer, nullable=True, index=True),
        # Graph info
        sa.Column('name', sa.String(200), nullable=True),
        sa.Column('graph_type', sa.String(50), nullable=False, default='causal'),  # causal, dependency, impact
        # Graph structure
        sa.Column('nodes', JSONB, nullable=False),  # List of node definitions
        sa.Column('edges', JSONB, nullable=False),  # List of edge definitions
        sa.Column('node_count', sa.Integer, nullable=False, default=0),
        sa.Column('edge_count', sa.Integer, nullable=False, default=0),
        # Analysis results
        sa.Column('critical_path', JSONB, nullable=True),  # Longest dependency chain
        sa.Column('root_nodes', JSONB, nullable=True),  # Nodes with no incoming edges
        sa.Column('leaf_nodes', JSONB, nullable=True),  # Nodes with no outgoing edges
        sa.Column('cycles', JSONB, nullable=True),  # Detected cycles (if any)
        sa.Column('topological_order', JSONB, nullable=True),  # Suggested execution order
        # Sprint planning support
        sa.Column('suggested_sprint_order', JSONB, nullable=True),  # Suggested sprint groupings
        # Serialization
        sa.Column('graph_format', sa.String(30), nullable=False, default='json'),  # json, graphml, dot
        sa.Column('serialized_graph', sa.Text, nullable=True),  # Full graph in specified format
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True, onupdate=sa.func.now()),
        # Foreign key
        sa.ForeignKeyConstraint(['session_id'], ['causal_sessions.id'], ondelete='CASCADE'),
    )

    # ============== TEST GENERATION TABLES ==============

    # Causal test cases - generated test scenarios from cause-effect pairs
    op.create_table(
        'causal_test_cases',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('relation_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('project_id', sa.Integer, nullable=True, index=True),
        # Test case info
        sa.Column('test_type', sa.String(50), nullable=False),  # positive, negative, boundary
        sa.Column('test_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        # Test content
        sa.Column('preconditions', JSONB, nullable=True),  # List of preconditions
        sa.Column('trigger', sa.Text, nullable=False),  # The cause action
        sa.Column('expected_result', sa.Text, nullable=False),  # The expected effect
        sa.Column('test_steps', JSONB, nullable=True),  # Detailed steps
        # Priority and tags
        sa.Column('priority', sa.String(20), nullable=False, default='medium'),  # high, medium, low
        sa.Column('tags', JSONB, nullable=True),  # Test tags/categories
        # Status
        sa.Column('status', sa.String(30), nullable=False, default='generated'),  # generated, reviewed, approved, executed
        sa.Column('execution_result', sa.String(30), nullable=True),  # passed, failed, skipped
        sa.Column('execution_notes', sa.Text, nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('executed_at', sa.DateTime, nullable=True),
        # Foreign keys
        sa.ForeignKeyConstraint(['relation_id'], ['causal_relations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['causal_sessions.id'], ondelete='CASCADE'),
    )

    # ============== INDEXES ==============

    # Session indexes
    op.create_index('ix_causal_sessions_status', 'causal_sessions', ['status'])
    op.create_index('ix_causal_sessions_source_type', 'causal_sessions', ['source_type'])

    # Classification indexes
    op.create_index('ix_causal_classifications_is_causal', 'causal_classifications', ['is_causal'])
    op.create_index('ix_causal_classifications_confidence', 'causal_classifications', ['confidence'])

    # Relation indexes
    op.create_index('ix_causal_relations_type', 'causal_relations', ['relation_type'])
    op.create_index('ix_causal_relations_validated', 'causal_relations', ['human_validated'])
    op.create_index('ix_causal_relations_cause_source', 'causal_relations', ['cause_source_id'])
    op.create_index('ix_causal_relations_effect_source', 'causal_relations', ['effect_source_id'])

    # Test case indexes
    op.create_index('ix_causal_test_cases_status', 'causal_test_cases', ['status'])
    op.create_index('ix_causal_test_cases_priority', 'causal_test_cases', ['priority'])

    # Graph indexes
    op.create_index('ix_causal_dependency_graphs_type', 'causal_dependency_graphs', ['graph_type'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_causal_dependency_graphs_type')
    op.drop_index('ix_causal_test_cases_priority')
    op.drop_index('ix_causal_test_cases_status')
    op.drop_index('ix_causal_relations_effect_source')
    op.drop_index('ix_causal_relations_cause_source')
    op.drop_index('ix_causal_relations_validated')
    op.drop_index('ix_causal_relations_type')
    op.drop_index('ix_causal_classifications_confidence')
    op.drop_index('ix_causal_classifications_is_causal')
    op.drop_index('ix_causal_sessions_source_type')
    op.drop_index('ix_causal_sessions_status')

    # Drop tables
    op.drop_table('causal_test_cases')
    op.drop_table('causal_dependency_graphs')
    op.drop_table('causal_relations')
    op.drop_table('causal_classifications')
    op.drop_table('causal_sessions')
