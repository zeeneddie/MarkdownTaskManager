"""Add harness framework tables

Week 91: Agent Harness Framework
- context_snapshots: Version tracking for agent context
- constraint_audit_log: Audit trail for constraint checks
- agent_system_contexts: Persisted system contexts
- harness_config: Runtime configuration

Revision ID: 045_harness
Revises: 044_add_roadmap_tables
Create Date: 2025-12-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '045'
down_revision = '044'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Context Snapshots - Immutable snapshots for versioning
    op.create_table(
        'context_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('content_hash', sa.String(64), nullable=False, index=True),
        sa.Column('agent_id', sa.String(50), nullable=False, index=True),
        sa.Column('session_id', sa.String(100), nullable=False, index=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('system_context', JSONB, nullable=True),
        sa.Column('task_context', JSONB, nullable=True),
        sa.Column('memory_context', JSONB, nullable=True),
        sa.Column('token_count', sa.Integer, nullable=False, default=0),
        sa.Column('parent_version_id', UUID(as_uuid=True), nullable=True),
        sa.Column('extra_metadata', JSONB, nullable=True, default={}),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Self-referential FK for parent version
    op.create_foreign_key(
        'fk_context_snapshot_parent',
        'context_snapshots', 'context_snapshots',
        ['parent_version_id'], ['id'],
        ondelete='SET NULL'
    )

    # Index for fast lookup by content hash (deduplication)
    op.create_index(
        'idx_context_snapshots_hash',
        'context_snapshots',
        ['content_hash']
    )

    # Index for session history
    op.create_index(
        'idx_context_snapshots_session_time',
        'context_snapshots',
        ['session_id', 'timestamp']
    )

    # Constraint Audit Log - Compliance trail
    op.create_table(
        'constraint_audit_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('audit_id', sa.String(20), nullable=False, index=True),
        sa.Column('agent_id', sa.String(50), nullable=False, index=True),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('action_params', JSONB, nullable=True),
        sa.Column('result', sa.String(20), nullable=False),  # ALLOWED, DENIED, APPROVAL_REQUIRED
        sa.Column('severity', sa.String(20), nullable=False),  # BLOCK, WARN, AUDIT, APPROVE
        sa.Column('reason', sa.Text, nullable=True),
        sa.Column('matched_rules', JSONB, nullable=True, default=[]),
        sa.Column('context', JSONB, nullable=True),
        sa.Column('requires_approval', sa.Boolean, nullable=False, default=False),
        sa.Column('approved_by', sa.String(100), nullable=True),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Index for compliance queries
    op.create_index(
        'idx_audit_log_agent_time',
        'constraint_audit_log',
        ['agent_id', 'created_at']
    )

    op.create_index(
        'idx_audit_log_result',
        'constraint_audit_log',
        ['result', 'created_at']
    )

    # Agent System Contexts - Persisted system contexts
    op.create_table(
        'agent_system_contexts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', sa.String(50), nullable=False, unique=True),
        sa.Column('role', sa.String(100), nullable=False),
        sa.Column('capabilities', JSONB, nullable=False, default=[]),
        sa.Column('rules', JSONB, nullable=False, default=[]),
        sa.Column('ethics', JSONB, nullable=False, default=[]),
        sa.Column('llm_model', sa.String(100), nullable=True),
        sa.Column('extra_config', JSONB, nullable=True, default={}),
        sa.Column('token_count', sa.Integer, nullable=False, default=0),
        sa.Column('version', sa.Integer, nullable=False, default=1),
        sa.Column('active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Index for active agents
    op.create_index(
        'idx_agent_contexts_active',
        'agent_system_contexts',
        ['active', 'agent_id']
    )

    # Context-Action Links - Link snapshots to actions for audit
    op.create_table(
        'context_action_links',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('context_snapshot_id', UUID(as_uuid=True), nullable=False),
        sa.Column('action_id', sa.String(100), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_foreign_key(
        'fk_context_action_snapshot',
        'context_action_links', 'context_snapshots',
        ['context_snapshot_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_index(
        'idx_context_action_snapshot',
        'context_action_links',
        ['context_snapshot_id']
    )

    op.create_index(
        'idx_context_action_id',
        'context_action_links',
        ['action_id']
    )

    # Harness Configuration - Runtime config storage
    op.create_table(
        'harness_config',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('config_type', sa.String(50), nullable=False),  # constraints, context, tools, versioning
        sa.Column('config_name', sa.String(100), nullable=False),
        sa.Column('config_data', JSONB, nullable=False, default={}),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('active', sa.Boolean, nullable=False, default=True),
        sa.Column('priority', sa.Integer, nullable=False, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Unique constraint for config type + name
    op.create_unique_constraint(
        'uq_harness_config_type_name',
        'harness_config',
        ['config_type', 'config_name']
    )

    op.create_index(
        'idx_harness_config_type_active',
        'harness_config',
        ['config_type', 'active']
    )


def downgrade() -> None:
    op.drop_table('harness_config')
    op.drop_table('context_action_links')
    op.drop_table('agent_system_contexts')
    op.drop_table('constraint_audit_log')
    op.drop_table('context_snapshots')
