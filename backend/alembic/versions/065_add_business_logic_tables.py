"""Add Fase 25 Business Logic Extraction tables

Revision ID: 065
Revises: 064
Create Date: 2026-01-01

Tables:
- decision_table_sessions: Track decision table extraction sessions
- decision_tables: Extracted decision tables
- decision_table_rules: Rules within decision tables
- state_machine_sessions: Track state machine extraction sessions
- state_machines: Extracted state machines
- state_machine_states: States within state machines
- state_machine_transitions: Transitions between states
- authorization_matrix_sessions: Track authorization matrix extraction sessions
- authorization_matrices: Extracted authorization matrices
- authorization_roles: Extracted roles
- authorization_permissions: Extracted permissions
- authorization_resources: Extracted resources
- authorization_mappings: Role-permission-resource mappings
- authorization_conflicts: Detected authorization conflicts
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '065'
down_revision = '064'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Decision Table Sessions
    op.create_table(
        'decision_table_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('total_files_scanned', sa.Integer, default=0),
        sa.Column('files_with_tables', sa.Integer, default=0),
        sa.Column('total_tables_extracted', sa.Integer, default=0),
        sa.Column('total_rules_extracted', sa.Integer, default=0),
        sa.Column('average_confidence', sa.Float, default=0.0),
        sa.Column('language', sa.String(50), nullable=True),
        sa.Column('warnings', sa.JSON, nullable=True),
        sa.Column('errors', sa.JSON, nullable=True),
        sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('duration_seconds', sa.Float, default=0.0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_decision_table_sessions_project', 'decision_table_sessions', ['project_id'])
    op.create_index('ix_decision_table_sessions_status', 'decision_table_sessions', ['status'])

    # Decision Tables
    op.create_table(
        'decision_tables',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('decision_table_sessions.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('source_file', sa.String(500), nullable=True),
        sa.Column('source_line', sa.Integer, nullable=True),
        sa.Column('source_code', sa.Text, nullable=True),
        sa.Column('hit_policy', sa.String(50), default='unique'),
        sa.Column('inputs', sa.JSON, nullable=True),  # List of InputColumn
        sa.Column('outputs', sa.JSON, nullable=True),  # List of OutputColumn
        sa.Column('confidence', sa.Float, default=1.0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_decision_tables_session', 'decision_tables', ['session_id'])
    op.create_index('ix_decision_tables_name', 'decision_tables', ['name'])

    # Decision Table Rules
    op.create_table(
        'decision_table_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('table_id', sa.String(36), sa.ForeignKey('decision_tables.id'), nullable=False),
        sa.Column('rule_number', sa.Integer, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('conditions', sa.JSON, nullable=True),  # List of ConditionEntry
        sa.Column('actions', sa.JSON, nullable=True),  # List of ActionEntry
        sa.Column('annotation', sa.Text, nullable=True),
        sa.Column('priority', sa.Integer, default=0),
        sa.Column('source_code', sa.Text, nullable=True),
        sa.Column('confidence', sa.Float, default=1.0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_decision_table_rules_table', 'decision_table_rules', ['table_id'])
    op.create_index('ix_decision_table_rules_number', 'decision_table_rules', ['rule_number'])

    # State Machine Sessions
    op.create_table(
        'state_machine_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('total_files_scanned', sa.Integer, default=0),
        sa.Column('files_with_machines', sa.Integer, default=0),
        sa.Column('total_machines_extracted', sa.Integer, default=0),
        sa.Column('average_confidence', sa.Float, default=0.0),
        sa.Column('language', sa.String(50), nullable=True),
        sa.Column('warnings', sa.JSON, nullable=True),
        sa.Column('errors', sa.JSON, nullable=True),
        sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('duration_seconds', sa.Float, default=0.0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_state_machine_sessions_project', 'state_machine_sessions', ['project_id'])
    op.create_index('ix_state_machine_sessions_status', 'state_machine_sessions', ['status'])

    # State Machines
    op.create_table(
        'state_machines',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('state_machine_sessions.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('source_file', sa.String(500), nullable=True),
        sa.Column('source_line', sa.Integer, nullable=True),
        sa.Column('source_code', sa.Text, nullable=True),
        sa.Column('pattern_type', sa.String(50), nullable=True),  # enum, string, design_pattern, etc.
        sa.Column('initial_state', sa.String(255), nullable=True),
        sa.Column('context_data', sa.JSON, nullable=True),
        sa.Column('confidence', sa.Float, default=1.0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_state_machines_session', 'state_machines', ['session_id'])
    op.create_index('ix_state_machines_name', 'state_machines', ['name'])

    # State Machine States
    op.create_table(
        'state_machine_states',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('machine_id', sa.String(36), sa.ForeignKey('state_machines.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_initial', sa.Boolean, default=False),
        sa.Column('is_final', sa.Boolean, default=False),
        sa.Column('entry_actions', sa.JSON, nullable=True),
        sa.Column('exit_actions', sa.JSON, nullable=True),
        sa.Column('state_data', sa.JSON, nullable=True),
        sa.Column('source_code', sa.Text, nullable=True),
        sa.Column('confidence', sa.Float, default=1.0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_state_machine_states_machine', 'state_machine_states', ['machine_id'])
    op.create_index('ix_state_machine_states_name', 'state_machine_states', ['name'])

    # State Machine Transitions
    op.create_table(
        'state_machine_transitions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('machine_id', sa.String(36), sa.ForeignKey('state_machines.id'), nullable=False),
        sa.Column('from_state', sa.String(255), nullable=False),
        sa.Column('to_state', sa.String(255), nullable=False),
        sa.Column('event_name', sa.String(255), nullable=True),
        sa.Column('guard_condition', sa.Text, nullable=True),
        sa.Column('actions', sa.JSON, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('source_code', sa.Text, nullable=True),
        sa.Column('confidence', sa.Float, default=1.0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_state_machine_transitions_machine', 'state_machine_transitions', ['machine_id'])
    op.create_index('ix_state_machine_transitions_from', 'state_machine_transitions', ['from_state'])
    op.create_index('ix_state_machine_transitions_to', 'state_machine_transitions', ['to_state'])

    # Authorization Matrix Sessions
    op.create_table(
        'authorization_matrix_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('total_files_scanned', sa.Integer, default=0),
        sa.Column('files_with_auth', sa.Integer, default=0),
        sa.Column('average_confidence', sa.Float, default=0.0),
        sa.Column('language', sa.String(50), nullable=True),
        sa.Column('warnings', sa.JSON, nullable=True),
        sa.Column('errors', sa.JSON, nullable=True),
        sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('duration_seconds', sa.Float, default=0.0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_authorization_matrix_sessions_project', 'authorization_matrix_sessions', ['project_id'])
    op.create_index('ix_authorization_matrix_sessions_status', 'authorization_matrix_sessions', ['status'])

    # Authorization Matrices
    op.create_table(
        'authorization_matrices',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('authorization_matrix_sessions.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('source_files', sa.JSON, nullable=True),
        sa.Column('statistics', sa.JSON, nullable=True),  # AuthorizationMatrixStatistics
        sa.Column('confidence', sa.Float, default=1.0),
        sa.Column('extracted_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_authorization_matrices_session', 'authorization_matrices', ['session_id'])

    # Authorization Roles
    op.create_table(
        'authorization_roles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('matrix_id', sa.String(36), sa.ForeignKey('authorization_matrices.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('level', sa.String(50), nullable=True),  # RoleLevel enum
        sa.Column('parent_role', sa.String(255), nullable=True),
        sa.Column('inherited_permissions', sa.JSON, nullable=True),
        sa.Column('source_file', sa.String(500), nullable=True),
        sa.Column('source_line', sa.Integer, nullable=True),
        sa.Column('source_code', sa.Text, nullable=True),
        sa.Column('confidence', sa.Float, default=1.0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_authorization_roles_matrix', 'authorization_roles', ['matrix_id'])
    op.create_index('ix_authorization_roles_name', 'authorization_roles', ['name'])
    op.create_index('ix_authorization_roles_level', 'authorization_roles', ['level'])

    # Authorization Permissions
    op.create_table(
        'authorization_permissions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('matrix_id', sa.String(36), sa.ForeignKey('authorization_matrices.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('permission_type', sa.String(50), nullable=True),  # PermissionType enum
        sa.Column('resource_id', sa.String(36), nullable=True),
        sa.Column('source_file', sa.String(500), nullable=True),
        sa.Column('source_line', sa.Integer, nullable=True),
        sa.Column('source_code', sa.Text, nullable=True),
        sa.Column('confidence', sa.Float, default=1.0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_authorization_permissions_matrix', 'authorization_permissions', ['matrix_id'])
    op.create_index('ix_authorization_permissions_name', 'authorization_permissions', ['name'])
    op.create_index('ix_authorization_permissions_type', 'authorization_permissions', ['permission_type'])

    # Authorization Resources
    op.create_table(
        'authorization_resources',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('matrix_id', sa.String(36), sa.ForeignKey('authorization_matrices.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('resource_type', sa.String(50), nullable=True),  # ResourceType enum
        sa.Column('path', sa.String(500), nullable=True),
        sa.Column('parent_resource', sa.String(255), nullable=True),
        sa.Column('required_permissions', sa.JSON, nullable=True),
        sa.Column('source_file', sa.String(500), nullable=True),
        sa.Column('source_line', sa.Integer, nullable=True),
        sa.Column('source_code', sa.Text, nullable=True),
        sa.Column('confidence', sa.Float, default=1.0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_authorization_resources_matrix', 'authorization_resources', ['matrix_id'])
    op.create_index('ix_authorization_resources_name', 'authorization_resources', ['name'])
    op.create_index('ix_authorization_resources_type', 'authorization_resources', ['resource_type'])

    # Authorization Mappings (Role-Permission-Resource)
    op.create_table(
        'authorization_mappings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('matrix_id', sa.String(36), sa.ForeignKey('authorization_matrices.id'), nullable=False),
        sa.Column('role_id', sa.String(36), nullable=False),
        sa.Column('permission_id', sa.String(36), nullable=False),
        sa.Column('resource_id', sa.String(36), nullable=True),
        sa.Column('is_granted', sa.Boolean, default=True),
        sa.Column('condition', sa.Text, nullable=True),
        sa.Column('source_file', sa.String(500), nullable=True),
        sa.Column('source_line', sa.Integer, nullable=True),
        sa.Column('source_code', sa.Text, nullable=True),
        sa.Column('confidence', sa.Float, default=1.0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_authorization_mappings_matrix', 'authorization_mappings', ['matrix_id'])
    op.create_index('ix_authorization_mappings_role', 'authorization_mappings', ['role_id'])
    op.create_index('ix_authorization_mappings_permission', 'authorization_mappings', ['permission_id'])
    op.create_index('ix_authorization_mappings_resource', 'authorization_mappings', ['resource_id'])

    # Authorization Conflicts
    op.create_table(
        'authorization_conflicts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('matrix_id', sa.String(36), sa.ForeignKey('authorization_matrices.id'), nullable=False),
        sa.Column('conflict_type', sa.String(50), nullable=False),  # ConflictType enum
        sa.Column('severity', sa.String(20), default='medium'),  # low, medium, high, critical
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('affected_roles', sa.JSON, nullable=True),
        sa.Column('affected_permissions', sa.JSON, nullable=True),
        sa.Column('affected_resources', sa.JSON, nullable=True),
        sa.Column('source_file', sa.String(500), nullable=True),
        sa.Column('source_line', sa.Integer, nullable=True),
        sa.Column('recommendation', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_authorization_conflicts_matrix', 'authorization_conflicts', ['matrix_id'])
    op.create_index('ix_authorization_conflicts_type', 'authorization_conflicts', ['conflict_type'])
    op.create_index('ix_authorization_conflicts_severity', 'authorization_conflicts', ['severity'])


def downgrade() -> None:
    # Drop tables in reverse order due to foreign key constraints
    op.drop_table('authorization_conflicts')
    op.drop_table('authorization_mappings')
    op.drop_table('authorization_resources')
    op.drop_table('authorization_permissions')
    op.drop_table('authorization_roles')
    op.drop_table('authorization_matrices')
    op.drop_table('authorization_matrix_sessions')
    op.drop_table('state_machine_transitions')
    op.drop_table('state_machine_states')
    op.drop_table('state_machines')
    op.drop_table('state_machine_sessions')
    op.drop_table('decision_table_rules')
    op.drop_table('decision_tables')
    op.drop_table('decision_table_sessions')
