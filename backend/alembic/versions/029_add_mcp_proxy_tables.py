"""Week 71: Add MCP Proxy tables for token optimization

Revision ID: 029_mcp_proxy
Revises: 028_project_assessment
Create Date: 2025-12-15

Tables:
- mcp_servers: MCP server configurations
- mcp_tool_registry: Available tools per server
- mcp_tool_executions: Tool execution history
- mcp_token_savings: Token savings tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '029_mcp_proxy'
down_revision = '028_project_assessment'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # MCP Servers configuration
    op.create_table(
        'mcp_servers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('server_type', sa.String(50), nullable=False),  # stdio, http, docker
        sa.Column('command', sa.String(500)),  # Command to start server
        sa.Column('args', JSONB, default=list),  # Command arguments
        sa.Column('env_vars', JSONB, default=dict),  # Environment variables
        sa.Column('docker_image', sa.String(200)),  # Docker image if containerized
        sa.Column('docker_config', JSONB, default=dict),  # Docker configuration
        sa.Column('security_level', sa.String(20), default='standard'),  # standard, isolated, quarantine
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('health_status', sa.String(20), default='unknown'),  # healthy, unhealthy, unknown
        sa.Column('last_health_check', sa.DateTime),
        sa.Column('priority', sa.Integer, default=100),  # Lower = higher priority
        sa.Column('config', JSONB, default=dict),  # Additional configuration
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # MCP Tool Registry - available tools per server
    op.create_table(
        'mcp_tool_registry',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('server_id', UUID(as_uuid=True), sa.ForeignKey('mcp_servers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tool_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('input_schema', JSONB),  # JSON Schema for input
        sa.Column('category', sa.String(50)),  # file, code, search, browser, etc.
        sa.Column('tags', JSONB, default=list),  # Semantic tags for search
        sa.Column('embedding', JSONB),  # Vector embedding for semantic search
        sa.Column('success_rate', sa.Float, default=1.0),  # Historical success rate
        sa.Column('avg_latency_ms', sa.Integer),  # Average execution time
        sa.Column('total_executions', sa.Integer, default=0),
        sa.Column('is_enabled', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('server_id', 'tool_name', name='uq_server_tool')
    )

    # MCP Tool Executions - execution history
    op.create_table(
        'mcp_tool_executions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tool_id', UUID(as_uuid=True), sa.ForeignKey('mcp_tool_registry.id', ondelete='CASCADE'), nullable=False),
        sa.Column('server_id', UUID(as_uuid=True), sa.ForeignKey('mcp_servers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_id', sa.String(50)),  # Which agent triggered this
        sa.Column('task_id', UUID(as_uuid=True)),  # Associated task
        sa.Column('input_params', JSONB),  # Input parameters
        sa.Column('output_result', JSONB),  # Output result
        sa.Column('input_tokens', sa.Integer),  # Token count for input
        sa.Column('output_tokens', sa.Integer),  # Token count for output
        sa.Column('tokens_saved', sa.Integer),  # Tokens saved via optimization
        sa.Column('latency_ms', sa.Integer),  # Execution time
        sa.Column('status', sa.String(20)),  # success, failed, timeout
        sa.Column('error_message', sa.Text),
        sa.Column('was_cached', sa.Boolean, default=False),
        sa.Column('cache_key', sa.String(64)),  # Hash for caching
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # MCP Token Savings - aggregated token savings
    op.create_table(
        'mcp_token_savings',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('server_id', UUID(as_uuid=True), sa.ForeignKey('mcp_servers.id', ondelete='CASCADE')),
        sa.Column('agent_id', sa.String(50)),
        sa.Column('total_executions', sa.Integer, default=0),
        sa.Column('total_input_tokens', sa.Integer, default=0),
        sa.Column('total_output_tokens', sa.Integer, default=0),
        sa.Column('total_tokens_saved', sa.Integer, default=0),
        sa.Column('cache_hits', sa.Integer, default=0),
        sa.Column('cache_misses', sa.Integer, default=0),
        sa.Column('avg_latency_ms', sa.Integer),
        sa.Column('success_rate', sa.Float),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('date', 'server_id', 'agent_id', name='uq_daily_savings')
    )

    # Indexes for performance
    op.create_index('ix_mcp_tool_executions_created', 'mcp_tool_executions', ['created_at'])
    op.create_index('ix_mcp_tool_executions_agent', 'mcp_tool_executions', ['agent_id'])
    op.create_index('ix_mcp_tool_executions_status', 'mcp_tool_executions', ['status'])
    op.create_index('ix_mcp_tool_registry_category', 'mcp_tool_registry', ['category'])
    op.create_index('ix_mcp_token_savings_date', 'mcp_token_savings', ['date'])


def downgrade() -> None:
    op.drop_index('ix_mcp_token_savings_date')
    op.drop_index('ix_mcp_tool_registry_category')
    op.drop_index('ix_mcp_tool_executions_status')
    op.drop_index('ix_mcp_tool_executions_agent')
    op.drop_index('ix_mcp_tool_executions_created')
    op.drop_table('mcp_token_savings')
    op.drop_table('mcp_tool_executions')
    op.drop_table('mcp_tool_registry')
    op.drop_table('mcp_servers')
