"""Add Fase 24 Data Architecture tables

Revision ID: 064
Revises: 063
Create Date: 2026-01-01

Tables:
- data_lineage_sessions: Track data flow from specs to code
- data_lineage_field_mappings: Legacy to new field mappings
- erd_diagrams: Generated ERD diagrams
- cdc_sessions: Change Data Capture sessions
- journey_recordings: Recorded user journeys
- journey_comparisons: Comparison results
- journey_override_rules: Eddie's approved overrides
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '064'
down_revision = '063'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Data Lineage Sessions
    op.create_table(
        'data_lineage_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=True),
        sa.Column('brown_paper_session_id', sa.String(36), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('node_count', sa.Integer, default=0),
        sa.Column('edge_count', sa.Integer, default=0),
        sa.Column('field_mapping_count', sa.Integer, default=0),
        sa.Column('graph_data', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_data_lineage_sessions_project', 'data_lineage_sessions', ['project_id'])
    op.create_index('ix_data_lineage_sessions_brown_paper', 'data_lineage_sessions', ['brown_paper_session_id'])

    # Data Lineage Field Mappings
    op.create_table(
        'data_lineage_field_mappings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('data_lineage_sessions.id'), nullable=False),
        sa.Column('legacy_table', sa.String(255), nullable=False),
        sa.Column('legacy_field', sa.String(255), nullable=False),
        sa.Column('legacy_type', sa.String(100), nullable=False),
        sa.Column('new_table', sa.String(255), nullable=False),
        sa.Column('new_field', sa.String(255), nullable=False),
        sa.Column('new_type', sa.String(100), nullable=False),
        sa.Column('transformation_type', sa.String(50), nullable=False),
        sa.Column('transformation_rule', sa.Text, nullable=True),
        sa.Column('nullable_legacy', sa.Boolean, default=True),
        sa.Column('nullable_new', sa.Boolean, default=True),
        sa.Column('default_value', sa.String(255), nullable=True),
        sa.Column('validation_rule', sa.Text, nullable=True),
        sa.Column('confidence', sa.Float, default=1.0),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_field_mappings_session', 'data_lineage_field_mappings', ['session_id'])
    op.create_index('ix_field_mappings_legacy_table', 'data_lineage_field_mappings', ['legacy_table'])
    op.create_index('ix_field_mappings_new_table', 'data_lineage_field_mappings', ['new_table'])

    # ERD Diagrams
    op.create_table(
        'erd_diagrams',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=True),
        sa.Column('brown_paper_session_id', sa.String(36), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('diagram_type', sa.String(50), default='target'),
        sa.Column('table_count', sa.Integer, default=0),
        sa.Column('relationship_count', sa.Integer, default=0),
        sa.Column('diagram_data', sa.JSON, nullable=True),
        sa.Column('mermaid_output', sa.Text, nullable=True),
        sa.Column('plantuml_output', sa.Text, nullable=True),
        sa.Column('bounded_contexts', sa.JSON, nullable=True),
        sa.Column('normalization_level', sa.String(10), default='3NF'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_erd_diagrams_project', 'erd_diagrams', ['project_id'])

    # CDC Sessions
    op.create_table(
        'cdc_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('source_connection_name', sa.String(255), nullable=False),
        sa.Column('target_connection_name', sa.String(255), nullable=False),
        sa.Column('mode', sa.String(50), default='shadow'),
        sa.Column('status', sa.String(50), default='initialized'),
        sa.Column('table_count', sa.Integer, default=0),
        sa.Column('events_processed', sa.Integer, default=0),
        sa.Column('events_failed', sa.Integer, default=0),
        sa.Column('last_sync_at', sa.DateTime, nullable=True),
        sa.Column('config', sa.JSON, nullable=True),
        sa.Column('stats', sa.JSON, nullable=True),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('stopped_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_cdc_sessions_project', 'cdc_sessions', ['project_id'])
    op.create_index('ix_cdc_sessions_status', 'cdc_sessions', ['status'])

    # Journey Recordings
    op.create_table(
        'journey_recordings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('system', sa.String(50), nullable=False),  # legacy, new
        sa.Column('base_url', sa.String(500), nullable=False),
        sa.Column('step_count', sa.Integer, default=0),
        sa.Column('total_duration_ms', sa.Integer, default=0),
        sa.Column('steps_data', sa.JSON, nullable=True),
        sa.Column('recorded_by', sa.String(255), nullable=True),
        sa.Column('recorded_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_journey_recordings_project', 'journey_recordings', ['project_id'])
    op.create_index('ix_journey_recordings_system', 'journey_recordings', ['system'])
    op.create_index('ix_journey_recordings_name', 'journey_recordings', ['name'])

    # Journey Comparisons
    op.create_table(
        'journey_comparisons',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=True),
        sa.Column('journey_name', sa.String(255), nullable=False),
        sa.Column('legacy_recording_id', sa.String(36), sa.ForeignKey('journey_recordings.id'), nullable=False),
        sa.Column('new_recording_id', sa.String(36), sa.ForeignKey('journey_recordings.id'), nullable=False),
        sa.Column('total_steps', sa.Integer, default=0),
        sa.Column('matching_steps', sa.Integer, default=0),
        sa.Column('mismatching_steps', sa.Integer, default=0),
        sa.Column('overridden_steps', sa.Integer, default=0),
        sa.Column('overall_match_percentage', sa.Float, default=0.0),
        sa.Column('visual_match_percentage', sa.Float, default=0.0),
        sa.Column('data_match_percentage', sa.Float, default=0.0),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('comparison_data', sa.JSON, nullable=True),
        sa.Column('compared_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_journey_comparisons_project', 'journey_comparisons', ['project_id'])
    op.create_index('ix_journey_comparisons_status', 'journey_comparisons', ['status'])

    # Journey Override Rules
    op.create_table(
        'journey_override_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=True),
        sa.Column('journey_name', sa.String(255), nullable=False),
        sa.Column('step_number', sa.Integer, nullable=True),
        sa.Column('override_type', sa.String(100), nullable=False),
        sa.Column('legacy_behavior', sa.Text, nullable=False),
        sa.Column('new_behavior', sa.Text, nullable=False),
        sa.Column('reason', sa.Text, nullable=False),
        sa.Column('approved_by', sa.String(255), nullable=False),
        sa.Column('approved_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_override_rules_project', 'journey_override_rules', ['project_id'])
    op.create_index('ix_override_rules_journey', 'journey_override_rules', ['journey_name'])
    op.create_index('ix_override_rules_active', 'journey_override_rules', ['active'])


def downgrade() -> None:
    op.drop_table('journey_override_rules')
    op.drop_table('journey_comparisons')
    op.drop_table('journey_recordings')
    op.drop_table('cdc_sessions')
    op.drop_table('erd_diagrams')
    op.drop_table('data_lineage_field_mappings')
    op.drop_table('data_lineage_sessions')
