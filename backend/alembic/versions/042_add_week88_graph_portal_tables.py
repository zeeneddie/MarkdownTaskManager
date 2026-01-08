"""Week 88: Graph Workflow Integration + Portal Feature Requests

Revision ID: 042
Revises: 041
Create Date: 2025-12-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '042'
down_revision = '041'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Portal Feature Requests table
    op.create_table(
        'portal_feature_requests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('external_id', sa.String(100), nullable=True),  # ID from external portal
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('user_name', sa.String(255), nullable=True),
        sa.Column('organization', sa.String(255), nullable=True),

        # Request details
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('priority', sa.String(20), default='medium'),  # low, medium, high, critical
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('attachments', JSONB, nullable=True),

        # Classification (by Peter agent)
        sa.Column('work_type', sa.String(50), nullable=True),  # GREEN_PAPER, BROWN_PAPER, BUG, etc.
        sa.Column('classification_confidence', sa.Float, nullable=True),
        sa.Column('classification_reasoning', sa.Text, nullable=True),
        sa.Column('classified_at', sa.DateTime, nullable=True),
        sa.Column('classified_by', sa.String(50), nullable=True),  # 'peter_agent' or user

        # Epic/Feature mapping
        sa.Column('mapped_project_id', sa.Integer, sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('mapped_epic_id', sa.String(100), nullable=True),
        sa.Column('mapped_feature_id', sa.String(100), nullable=True),
        sa.Column('mapping_confidence', sa.Float, nullable=True),
        sa.Column('mapping_suggestions', JSONB, nullable=True),

        # Status tracking
        sa.Column('status', sa.String(50), default='submitted'),
        # submitted -> analyzing -> classified -> planned -> in_progress -> testing -> done
        sa.Column('kanban_item_id', sa.Integer, nullable=True),
        sa.Column('sprint_id', sa.Integer, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )

    # Graph Analysis Cache table
    op.create_table(
        'graph_analysis_cache',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id'), nullable=False),

        # Analysis type and scope
        sa.Column('analysis_type', sa.String(50), nullable=False),
        # impact_analysis, dependency_check, coupling_metrics, test_coverage_map, enhancement_scope
        sa.Column('entity_id', sa.String(200), nullable=True),  # Optional specific entity
        sa.Column('entity_type', sa.String(50), nullable=True),  # class, function, module, file

        # Results
        sa.Column('result', JSONB, nullable=False),
        sa.Column('metrics', JSONB, nullable=True),

        # Caching
        sa.Column('computed_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('cache_hit_count', sa.Integer, default=0),
    )

    # Workflow Graph Integration tracking
    op.create_table(
        'workflow_graph_integrations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('workflow_type', sa.String(50), nullable=False),
        sa.Column('workflow_session_id', sa.String(100), nullable=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id'), nullable=True),

        # Integration details
        sa.Column('integration_type', sa.String(50), nullable=False),
        # graph_impact, graph_dependency, graph_coupling, graph_test_map, graph_scope
        sa.Column('input_data', JSONB, nullable=True),
        sa.Column('output_data', JSONB, nullable=True),

        # Status
        sa.Column('status', sa.String(30), default='pending'),
        sa.Column('error_message', sa.Text, nullable=True),

        # Timing
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('duration_ms', sa.Integer, nullable=True),

        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
    )

    # Create indexes
    op.create_index('ix_portal_feature_requests_status', 'portal_feature_requests', ['status'])
    op.create_index('ix_portal_feature_requests_user_email', 'portal_feature_requests', ['user_email'])
    op.create_index('ix_portal_feature_requests_work_type', 'portal_feature_requests', ['work_type'])
    op.create_index('ix_portal_feature_requests_mapped_project', 'portal_feature_requests', ['mapped_project_id'])

    op.create_index('ix_graph_analysis_cache_project', 'graph_analysis_cache', ['project_id'])
    op.create_index('ix_graph_analysis_cache_type', 'graph_analysis_cache', ['analysis_type'])
    op.create_index('ix_graph_analysis_cache_expires', 'graph_analysis_cache', ['expires_at'])

    op.create_index('ix_workflow_graph_integrations_workflow', 'workflow_graph_integrations', ['workflow_type'])
    op.create_index('ix_workflow_graph_integrations_project', 'workflow_graph_integrations', ['project_id'])


def downgrade() -> None:
    op.drop_index('ix_workflow_graph_integrations_project')
    op.drop_index('ix_workflow_graph_integrations_workflow')
    op.drop_index('ix_graph_analysis_cache_expires')
    op.drop_index('ix_graph_analysis_cache_type')
    op.drop_index('ix_graph_analysis_cache_project')
    op.drop_index('ix_portal_feature_requests_mapped_project')
    op.drop_index('ix_portal_feature_requests_work_type')
    op.drop_index('ix_portal_feature_requests_user_email')
    op.drop_index('ix_portal_feature_requests_status')

    op.drop_table('workflow_graph_integrations')
    op.drop_table('graph_analysis_cache')
    op.drop_table('portal_feature_requests')
