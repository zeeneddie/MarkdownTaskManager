"""Add observability tables for agent monitoring

Revision ID: 015
Revises: 014_add_projects_table
Create Date: 2025-11-26

Week 54: Provider Registry & Observability Foundation
- llm_providers: Provider configuration and status
- agent_actions: Log every agent action for monitoring
- decision_traces: Track decision points for debugging
- agent_performance_daily: Aggregated performance metrics
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision = '015_add_observability_tables'
down_revision = '014_add_projects_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create observability tables."""

    # 1. LLM Providers Configuration
    op.create_table(
        'llm_providers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('display_name', sa.String(100)),
        sa.Column('provider_type', sa.String(30), nullable=False),  # ollama, codex, claude
        sa.Column('tier', sa.String(20), nullable=False),  # free, fast, balanced, deep
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('cost_input_per_m', sa.Numeric(10, 4), default=0),  # $ per million tokens
        sa.Column('cost_output_per_m', sa.Numeric(10, 4), default=0),
        sa.Column('is_local', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('config', JSONB, default=dict),  # Provider-specific settings
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create index on provider_type and tier for routing queries
    op.create_index('ix_llm_providers_type_tier', 'llm_providers', ['provider_type', 'tier'])

    # 2. Agent Actions Log (Observability)
    op.create_table(
        'agent_actions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('task_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('session_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('agent_id', sa.String(50), nullable=False, index=True),
        sa.Column('action_type', sa.String(50), nullable=False),  # generate, review, estimate, etc.
        sa.Column('provider', sa.String(30)),  # ollama, codex, claude
        sa.Column('model', sa.String(100)),  # Specific model used
        sa.Column('input_summary', sa.Text()),  # Truncated input for logging
        sa.Column('output_summary', sa.Text()),  # Truncated output for logging
        sa.Column('decision_rationale', sa.Text()),  # Why this action was taken
        sa.Column('token_input', sa.Integer(), default=0),
        sa.Column('token_output', sa.Integer(), default=0),
        sa.Column('duration_ms', sa.Integer(), default=0),
        sa.Column('cost_cents', sa.Numeric(10, 4), default=0),
        sa.Column('success', sa.Boolean(), default=True),
        sa.Column('error', sa.Text()),  # Error message if failed
        sa.Column('confidence_score', sa.Numeric(3, 2)),  # 0.00 - 1.00
        sa.Column('extra_data', JSONB, default=dict),  # Additional context
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), index=True),
    )

    # Create indexes for common queries
    op.create_index('ix_agent_actions_created_at_agent', 'agent_actions', ['created_at', 'agent_id'])
    op.create_index('ix_agent_actions_provider', 'agent_actions', ['provider'])

    # 3. Decision Traces (Debugging)
    op.create_table(
        'decision_traces',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('task_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('session_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('sequence_number', sa.Integer(), nullable=False),  # Order within task
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('decision_point', sa.String(100), nullable=False),  # e.g., "model_selection", "quality_gate"
        sa.Column('options', JSONB),  # Available options considered
        sa.Column('selected_option', sa.String(100)),  # What was chosen
        sa.Column('selection_rationale', sa.Text()),  # Why this option
        sa.Column('outcome', sa.String(50)),  # success, failure, skipped
        sa.Column('outcome_details', JSONB),  # Additional outcome info
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Create composite index for task-based queries
    op.create_index('ix_decision_traces_task_seq', 'decision_traces', ['task_id', 'sequence_number'])

    # 4. Agent Performance Daily Aggregates
    op.create_table(
        'agent_performance_daily',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('provider', sa.String(30)),  # Optional: breakdown by provider
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_actions', sa.Integer(), default=0),
        sa.Column('successful_actions', sa.Integer(), default=0),
        sa.Column('failed_actions', sa.Integer(), default=0),
        sa.Column('avg_duration_ms', sa.Integer(), default=0),
        sa.Column('total_tokens_input', sa.Integer(), default=0),
        sa.Column('total_tokens_output', sa.Integer(), default=0),
        sa.Column('total_cost_cents', sa.Numeric(10, 2), default=0),
        sa.Column('avg_confidence', sa.Numeric(3, 2)),  # Average confidence score
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Unique constraint on agent_id + provider + date
    op.create_unique_constraint(
        'uq_agent_performance_daily_agent_provider_date',
        'agent_performance_daily',
        ['agent_id', 'provider', 'date']
    )

    # Create index for date range queries
    op.create_index('ix_agent_performance_daily_date', 'agent_performance_daily', ['date'])

    # 5. Seed default providers
    op.execute("""
        INSERT INTO llm_providers (name, display_name, provider_type, tier, model, cost_input_per_m, cost_output_per_m, is_local, is_active, config)
        VALUES
            ('ollama_qwen', 'Ollama Qwen 2.5 Coder', 'ollama', 'free', 'qwen2.5-coder:7b', 0, 0, true, true, '{"base_url": "http://localhost:11434"}'),
            ('ollama_deepseek', 'Ollama DeepSeek R1', 'ollama', 'free', 'deepseek-r1:latest', 0, 0, true, true, '{"base_url": "http://localhost:11434"}'),
            ('ollama_codellama', 'Ollama CodeLlama', 'ollama', 'free', 'codellama:latest', 0, 0, true, true, '{"base_url": "http://localhost:11434"}'),
            ('ollama_mistral', 'Ollama Mistral', 'ollama', 'free', 'mistral:latest', 0, 0, true, true, '{"base_url": "http://localhost:11434"}'),
            ('codex_max', 'Codex GPT-5.1 Max', 'codex', 'deep', 'gpt-5.1-codex-max', 15, 60, false, true, '{"reasoning_effort": "medium", "sandbox_mode": "read-only"}'),
            ('claude_haiku', 'Claude Haiku', 'claude', 'fast', 'haiku', 1, 5, false, true, '{}'),
            ('claude_sonnet', 'Claude Sonnet', 'claude', 'balanced', 'sonnet', 3, 15, false, true, '{}'),
            ('claude_opus', 'Claude Opus', 'claude', 'deep', 'opus', 15, 75, false, true, '{}')
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    """Drop observability tables."""
    op.drop_table('agent_performance_daily')
    op.drop_table('decision_traces')
    op.drop_table('agent_actions')
    op.drop_table('llm_providers')
