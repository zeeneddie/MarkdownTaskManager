"""Add Deep Extraction Pipeline tables for Week 81-87

Revision ID: 036
Revises: 035
Create Date: 2025-12-18

Tables:
- extraction_sessions: Multi-LLM extraction sessions with tier support
- extraction_runs: Re-run capability for tier upgrades
- extraction_llm_results: Per-cycle, per-LLM analysis results
- extraction_enrichments: Cross-enrichment between LLMs
- extraction_consensus: Consensus items with confidence scores
- extraction_conflicts: Conflicts requiring human decision

Also adds:
- extraction_tier to projects table
- function_points fields to task_stories and task_tasks
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = '036'
down_revision = '035'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add extraction_tier to projects table
    op.add_column(
        'projects',
        sa.Column('extraction_tier', sa.String(20), nullable=True, default='FREE')
    )
    # Valid tiers: FREE, BASIC, STANDARD, PROFESSIONAL, PREMIUM

    # Add function points fields to task_stories
    op.add_column(
        'task_stories',
        sa.Column('function_points', sa.Float, nullable=True)
    )
    op.add_column(
        'task_stories',
        sa.Column('fp_complexity', sa.String(20), nullable=True)  # low, average, high
    )
    op.add_column(
        'task_stories',
        sa.Column('fp_type', sa.String(30), nullable=True)  # EI, EO, EQ, ILF, EIF
    )
    op.add_column(
        'task_stories',
        sa.Column('extraction_confidence', sa.Float, nullable=True)  # 0.0-1.0
    )

    # Add function points fields to task_tasks
    op.add_column(
        'task_tasks',
        sa.Column('function_points', sa.Float, nullable=True)
    )
    op.add_column(
        'task_tasks',
        sa.Column('extraction_confidence', sa.Float, nullable=True)
    )

    # =========================================================================
    # EXTRACTION SESSIONS - Main extraction session with tier configuration
    # =========================================================================
    op.create_table(
        'extraction_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('workflow_type', sa.String(30), nullable=False),  # GREEN_PAPER, BROWN_PAPER, etc.
        sa.Column('status', sa.String(20), default='started', index=True),  # started, running, awaiting_review, completed, failed
        sa.Column('current_cycle', sa.Integer, default=1),  # 1-5

        # TIER CONFIGURATION
        sa.Column('tier', sa.String(20), nullable=False, default='FREE'),  # FREE, BASIC, STANDARD, PROFESSIONAL, PREMIUM
        sa.Column('tier_price_usd', sa.Float, nullable=True),  # What customer pays
        sa.Column('tier_cost_estimate', sa.Float, nullable=True),  # Our estimated cost
        sa.Column('tier_confidence_target', sa.Float, nullable=True),  # Expected confidence (0.60-0.95)

        # Input
        sa.Column('source_path', sa.String(500), nullable=True),
        sa.Column('total_files', sa.Integer, nullable=True),
        sa.Column('total_lines', sa.Integer, nullable=True),

        # Progress timestamps
        sa.Column('cycle_1_completed_at', sa.DateTime, nullable=True),
        sa.Column('cycle_2_completed_at', sa.DateTime, nullable=True),
        sa.Column('cycle_3_completed_at', sa.DateTime, nullable=True),
        sa.Column('cycle_4_completed_at', sa.DateTime, nullable=True),  # Human decisions
        sa.Column('cycle_5_completed_at', sa.DateTime, nullable=True),

        # Results
        sa.Column('total_epics', sa.Integer, default=0),
        sa.Column('total_features', sa.Integer, default=0),
        sa.Column('total_stories', sa.Integer, default=0),
        sa.Column('total_tasks', sa.Integer, default=0),
        sa.Column('total_function_points', sa.Float, nullable=True),

        # Confidence tracking
        sa.Column('avg_confidence', sa.Float, nullable=True),
        sa.Column('items_auto_accepted', sa.Integer, default=0),
        sa.Column('items_human_reviewed', sa.Integer, default=0),

        # Cost tracking
        sa.Column('total_tokens_used', sa.Integer, default=0),
        sa.Column('actual_cost_usd', sa.Float, nullable=True),  # What we actually paid
        sa.Column('margin_usd', sa.Float, nullable=True),  # tier_price - actual_cost

        # Timestamps
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )

    # =========================================================================
    # EXTRACTION RUNS - For re-run capability with tier upgrades
    # =========================================================================
    op.create_table(
        'extraction_runs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('extraction_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('run_number', sa.Integer, default=1),

        # Tier for this run
        sa.Column('tier', sa.String(20), nullable=False),
        sa.Column('tier_price_usd', sa.Float, nullable=True),

        # Status
        sa.Column('status', sa.String(20), default='pending'),  # pending, running, completed, failed
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),

        # Link to previous run (for delta calculation)
        sa.Column('previous_run_id', UUID(as_uuid=True), sa.ForeignKey('extraction_runs.id'), nullable=True),

        # Delta from previous run
        sa.Column('delta_epics', sa.Integer, default=0),
        sa.Column('delta_features', sa.Integer, default=0),
        sa.Column('delta_stories', sa.Integer, default=0),
        sa.Column('delta_tasks', sa.Integer, default=0),
        sa.Column('confidence_improvement', sa.Float, default=0.0),

        # Cost
        sa.Column('actual_cost_usd', sa.Float, nullable=True),
        sa.Column('tokens_used', sa.Integer, default=0),

        # Credit applied (if upgrade from previous tier)
        sa.Column('credit_from_previous', sa.Float, default=0.0),
        sa.Column('amount_charged', sa.Float, nullable=True),  # tier_price - credit

        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # =========================================================================
    # EXTRACTION LLM RESULTS - Per-cycle, per-LLM analysis results
    # =========================================================================
    op.create_table(
        'extraction_llm_results',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('extraction_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('run_id', UUID(as_uuid=True), sa.ForeignKey('extraction_runs.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('cycle', sa.Integer, nullable=False),  # 1-5

        # LLM identification
        sa.Column('llm_provider', sa.String(50), nullable=False),  # ollama, anthropic, openai, google, groq, alibaba, moonshot
        sa.Column('llm_model', sa.String(100), nullable=False),  # qwen2.5-coder:7b, gpt-5.2, etc.

        # Analysis type
        sa.Column('analysis_type', sa.String(50), nullable=True),  # architecture, business_logic, security, code_structure

        # Raw output
        sa.Column('raw_output', sa.Text, nullable=True),
        sa.Column('parsed_output', JSONB, nullable=True),

        # Extracted items
        sa.Column('extracted_epics', JSONB, default=[]),
        sa.Column('extracted_features', JSONB, default=[]),
        sa.Column('extracted_stories', JSONB, default=[]),
        sa.Column('extracted_tasks', JSONB, default=[]),

        # Metrics
        sa.Column('tokens_input', sa.Integer, nullable=True),
        sa.Column('tokens_output', sa.Integer, nullable=True),
        sa.Column('latency_ms', sa.Integer, nullable=True),
        sa.Column('cost_usd', sa.Float, nullable=True),

        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # =========================================================================
    # EXTRACTION ENRICHMENTS - Cross-enrichment results from Cycle 2
    # =========================================================================
    op.create_table(
        'extraction_enrichments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('extraction_sessions.id', ondelete='CASCADE'), nullable=False, index=True),

        # Source and reviewer
        sa.Column('source_result_id', UUID(as_uuid=True), sa.ForeignKey('extraction_llm_results.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reviewer_llm', sa.String(100), nullable=False),  # Which LLM reviewed

        # Enrichment
        sa.Column('additions', JSONB, default=[]),  # New items found
        sa.Column('modifications', JSONB, default=[]),  # Suggested changes
        sa.Column('confidence_adjustments', JSONB, nullable=True),  # Per-item confidence changes

        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # =========================================================================
    # EXTRACTION CONSENSUS - Items with consensus scores
    # =========================================================================
    op.create_table(
        'extraction_consensus',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('extraction_sessions.id', ondelete='CASCADE'), nullable=False, index=True),

        # Item identification
        sa.Column('item_type', sa.String(20), nullable=False),  # epic, feature, story, task
        sa.Column('item_title', sa.String(300), nullable=False),
        sa.Column('item_description', sa.Text, nullable=True),

        # Consensus data
        sa.Column('supporting_llms', JSONB, nullable=True),  # Which LLMs agree
        sa.Column('confidence_score', sa.Float, nullable=False),  # 0.0-1.0
        sa.Column('confidence_breakdown', JSONB, nullable=True),  # Per-factor scores

        # Status
        sa.Column('status', sa.String(20), default='pending', index=True),  # pending, auto_accepted, human_review, accepted, rejected
        sa.Column('human_decision', sa.String(20), nullable=True),
        sa.Column('human_feedback', sa.Text, nullable=True),
        sa.Column('decided_at', sa.DateTime, nullable=True),
        sa.Column('decided_by', sa.String(100), nullable=True),

        # Final item reference (after acceptance)
        sa.Column('final_epic_id', UUID(as_uuid=True), sa.ForeignKey('task_epics.id'), nullable=True),
        sa.Column('final_feature_id', UUID(as_uuid=True), sa.ForeignKey('task_features.id'), nullable=True),
        sa.Column('final_story_id', UUID(as_uuid=True), sa.ForeignKey('task_stories.id'), nullable=True),
        sa.Column('final_task_id', UUID(as_uuid=True), sa.ForeignKey('task_tasks.id'), nullable=True),

        # Additional data for item creation
        sa.Column('item_data', JSONB, nullable=True),  # Full extracted data for creating final item

        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # =========================================================================
    # EXTRACTION CONFLICTS - Conflicts requiring human decision
    # =========================================================================
    op.create_table(
        'extraction_conflicts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('extraction_sessions.id', ondelete='CASCADE'), nullable=False, index=True),

        # Conflict identification
        sa.Column('conflict_type', sa.String(50), nullable=False),  # scope, priority, classification, existence, duplicate
        sa.Column('item_type', sa.String(20), nullable=False),  # epic, feature, story, task

        # Competing interpretations (up to 4 LLM views)
        sa.Column('option_a', JSONB, nullable=True),  # LLM A's view
        sa.Column('option_b', JSONB, nullable=True),  # LLM B's view
        sa.Column('option_c', JSONB, nullable=True),  # LLM C's view (optional)
        sa.Column('option_d', JSONB, nullable=True),  # LLM D's view (optional)

        # LLM recommendations
        sa.Column('llm_recommendation', sa.String(20), nullable=True),  # a, b, c, d, merge
        sa.Column('recommendation_reasoning', sa.Text, nullable=True),

        # Human resolution
        sa.Column('status', sa.String(20), default='pending', index=True),  # pending, resolved, skipped
        sa.Column('human_choice', sa.String(20), nullable=True),  # a, b, c, d, merge, custom
        sa.Column('human_custom', JSONB, nullable=True),  # Custom resolution if human_choice = 'custom'
        sa.Column('human_reasoning', sa.Text, nullable=True),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
        sa.Column('resolved_by', sa.String(100), nullable=True),

        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create indexes for efficient queries (only for columns without index=True in table def)
    op.create_index('ix_extraction_sessions_tier', 'extraction_sessions', ['tier'])
    # Note: status indexes are created automatically via index=True in column definition


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_extraction_sessions_tier')

    # Drop tables in reverse order
    op.drop_table('extraction_conflicts')
    op.drop_table('extraction_consensus')
    op.drop_table('extraction_enrichments')
    op.drop_table('extraction_llm_results')
    op.drop_table('extraction_runs')
    op.drop_table('extraction_sessions')

    # Remove columns from task_tasks
    op.drop_column('task_tasks', 'extraction_confidence')
    op.drop_column('task_tasks', 'function_points')

    # Remove columns from task_stories
    op.drop_column('task_stories', 'extraction_confidence')
    op.drop_column('task_stories', 'fp_type')
    op.drop_column('task_stories', 'fp_complexity')
    op.drop_column('task_stories', 'function_points')

    # Remove extraction_tier from projects
    op.drop_column('projects', 'extraction_tier')
