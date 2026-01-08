"""Add CCTrace observability tables

Week 61: Enhanced Observability (CCTrace Integration) + Cost Management

New tables:
- thinking_blocks: LLM reasoning capture (multi-provider)
- tool_executions: Complete tool I/O (no truncation)
- message_relationships: Parent-child conversation threading
- session_exports: Export audit trail
- budget_configs: Budget management settings

Extended:
- agent_actions: Add token_cache_creation, token_cache_read, message_id

Revision ID: 024
Revises: 023
Create Date: 2025-12-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers
revision = '024'
down_revision = '023'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Thinking Blocks Table - LLM reasoning capture
    op.create_table(
        'thinking_blocks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('action_id', sa.Integer(), sa.ForeignKey('agent_actions.id', ondelete='CASCADE'), nullable=True),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('message_id', UUID(as_uuid=True), nullable=False),
        sa.Column('parent_message_id', UUID(as_uuid=True), nullable=True),
        sa.Column('provider', sa.String(30), nullable=False),  # claude, codex, ollama
        sa.Column('block_type', sa.String(30), nullable=False),  # thinking, reasoning, cot
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=True),  # SHA-256 for verification
        sa.Column('signature', sa.String(256), nullable=True),  # Claude native signature
        sa.Column('token_count', sa.Integer(), default=0),
        sa.Column('sequence_number', sa.Integer(), default=0),  # Order within message
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_thinking_blocks_session', 'thinking_blocks', ['session_id'])
    op.create_index('ix_thinking_blocks_action', 'thinking_blocks', ['action_id'])
    op.create_index('ix_thinking_blocks_provider', 'thinking_blocks', ['provider'])
    op.create_index('ix_thinking_blocks_message', 'thinking_blocks', ['message_id'])

    # 2. Tool Executions Table - Complete tool I/O (no truncation)
    op.create_table(
        'tool_executions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('action_id', sa.Integer(), sa.ForeignKey('agent_actions.id', ondelete='CASCADE'), nullable=True),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('message_id', UUID(as_uuid=True), nullable=False),
        sa.Column('tool_name', sa.String(100), nullable=False),
        sa.Column('tool_type', sa.String(50), nullable=True),  # read, write, bash, search, etc.
        sa.Column('input_full', JSONB, nullable=False),  # Complete input (no truncation)
        sa.Column('output_full', JSONB, nullable=True),  # Complete output (no truncation)
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(30), default='pending'),  # pending, success, error, timeout
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('response_code', sa.Integer(), nullable=True),
        sa.Column('byte_count_input', sa.Integer(), default=0),
        sa.Column('byte_count_output', sa.Integer(), default=0),
        sa.Column('duration_ms', sa.Integer(), default=0),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('extra_data', JSONB, default=dict),
    )
    op.create_index('ix_tool_executions_session', 'tool_executions', ['session_id'])
    op.create_index('ix_tool_executions_action', 'tool_executions', ['action_id'])
    op.create_index('ix_tool_executions_tool', 'tool_executions', ['tool_name'])
    op.create_index('ix_tool_executions_message', 'tool_executions', ['message_id'])

    # 3. Message Relationships Table - Conversation threading
    op.create_table(
        'message_relationships',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('message_id', UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('parent_message_id', UUID(as_uuid=True), nullable=True),
        sa.Column('role', sa.String(20), nullable=False),  # user, assistant, system
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('provider', sa.String(30), nullable=True),
        sa.Column('content_summary', sa.Text(), nullable=True),  # First 500 chars
        sa.Column('has_thinking_blocks', sa.Boolean(), default=False),
        sa.Column('has_tool_calls', sa.Boolean(), default=False),
        sa.Column('token_input', sa.Integer(), default=0),
        sa.Column('token_output', sa.Integer(), default=0),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_message_relationships_session', 'message_relationships', ['session_id'])
    op.create_index('ix_message_relationships_parent', 'message_relationships', ['parent_message_id'])

    # 4. Session Exports Table - Export audit trail
    op.create_table(
        'session_exports',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('export_format', sa.String(20), nullable=False),  # markdown, json, xml, jsonl
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('message_count', sa.Integer(), default=0),
        sa.Column('thinking_block_count', sa.Integer(), default=0),
        sa.Column('tool_execution_count', sa.Integer(), default=0),
        sa.Column('total_tokens', sa.Integer(), default=0),
        sa.Column('total_cost_cents', sa.Numeric(10, 4), default=0),
        sa.Column('include_thinking', sa.Boolean(), default=True),
        sa.Column('include_tools', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_by', sa.String(100), nullable=True),
    )
    op.create_index('ix_session_exports_session', 'session_exports', ['session_id'])

    # 5. Budget Configs Table - Cost management settings
    op.create_table(
        'budget_configs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('budget_type', sa.String(30), nullable=False),  # daily, monthly, project
        sa.Column('budget_cents', sa.Integer(), nullable=False),
        sa.Column('warning_threshold', sa.Numeric(3, 2), default=0.80),  # 80%
        sa.Column('cutoff_threshold', sa.Numeric(3, 2), default=1.00),  # 100%
        sa.Column('fallback_enabled', sa.Boolean(), default=True),
        sa.Column('fallback_chain', JSONB, default=list),  # ["opus", "sonnet", "ollama"]
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # 6. Extend agent_actions with token cache fields
    op.add_column('agent_actions', sa.Column('token_cache_creation', sa.Integer(), default=0))
    op.add_column('agent_actions', sa.Column('token_cache_read', sa.Integer(), default=0))
    op.add_column('agent_actions', sa.Column('message_id', UUID(as_uuid=True), nullable=True))
    op.add_column('agent_actions', sa.Column('parent_message_id', UUID(as_uuid=True), nullable=True))


def downgrade() -> None:
    # Remove new columns from agent_actions
    op.drop_column('agent_actions', 'parent_message_id')
    op.drop_column('agent_actions', 'message_id')
    op.drop_column('agent_actions', 'token_cache_read')
    op.drop_column('agent_actions', 'token_cache_creation')

    # Drop tables in reverse order
    op.drop_table('budget_configs')
    op.drop_table('session_exports')
    op.drop_table('message_relationships')
    op.drop_table('tool_executions')
    op.drop_table('thinking_blocks')
