"""Add Week 121 chatbot and journey analytics tables

Client Portal 2.0 Phase 4: Advanced Features
- Conversational Interface (chat_sessions, chat_messages)
- Customer Journey Analytics (journey_events, journey_funnels)

Revision ID: 056_add_week121_chatbot_journey_tables
Revises: 055_add_engagement_system_tables
Create Date: 2025-12-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '056_add_week121_chatbot_journey_tables'
down_revision = '055_add_engagement_system_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============== CONVERSATIONAL INTERFACE TABLES ==============

    # Chat sessions - conversation sessions with the chatbot
    op.create_table(
        'chat_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', sa.String(100), nullable=False, index=True),
        sa.Column('project_id', sa.Integer, nullable=True, index=True),
        # Session info
        sa.Column('title', sa.String(200), nullable=True),  # Auto-generated from first message
        sa.Column('status', sa.String(30), nullable=False, default='active'),  # active, closed, archived
        # Agent assignment
        sa.Column('primary_agent', sa.String(50), nullable=False, default='peter'),  # peter, diana, felix
        sa.Column('agents_involved', JSONB, nullable=True, default=[]),  # List of agents that participated
        # Context
        sa.Column('context', JSONB, nullable=True),  # Session context for LLM
        sa.Column('feature_ids_mentioned', JSONB, nullable=True, default=[]),  # Feature IDs discussed
        # Stats
        sa.Column('message_count', sa.Integer, nullable=False, default=0),
        sa.Column('resolved', sa.Boolean, nullable=False, default=False),
        sa.Column('satisfaction_rating', sa.Integer, nullable=True),  # 1-5 post-session rating
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('last_message_at', sa.DateTime, nullable=True),
        sa.Column('closed_at', sa.DateTime, nullable=True),
    )

    # Chat messages - individual messages in a session
    op.create_table(
        'chat_messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('customer_id', sa.String(100), nullable=False, index=True),
        # Message content
        sa.Column('role', sa.String(20), nullable=False),  # user, assistant, system
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('content_type', sa.String(30), nullable=False, default='text'),  # text, action, card
        # Agent info (for assistant messages)
        sa.Column('agent', sa.String(50), nullable=True),  # peter, diana, felix, etc.
        sa.Column('agent_reasoning', sa.Text, nullable=True),  # Why agent gave this response
        # Intent detection
        sa.Column('detected_intent', sa.String(50), nullable=True),  # status_query, eta_query, new_request, etc.
        sa.Column('intent_confidence', sa.Float, nullable=True),
        sa.Column('entities', JSONB, nullable=True),  # Extracted entities (feature_id, date, etc.)
        # Actions
        sa.Column('action_type', sa.String(50), nullable=True),  # start_request, show_status, redirect
        sa.Column('action_data', JSONB, nullable=True),  # Action parameters
        sa.Column('action_executed', sa.Boolean, nullable=False, default=False),
        # Feedback
        sa.Column('helpful', sa.Boolean, nullable=True),  # User feedback on message
        sa.Column('feedback_text', sa.Text, nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        # Foreign key
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
    )

    # ============== JOURNEY ANALYTICS TABLES ==============

    # Journey events - individual events in customer journey
    op.create_table(
        'journey_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', sa.String(100), nullable=False, index=True),
        sa.Column('session_id', sa.String(100), nullable=True, index=True),  # Browser/app session
        sa.Column('project_id', sa.Integer, nullable=True, index=True),
        # Event details
        sa.Column('event_type', sa.String(50), nullable=False, index=True),
        sa.Column('event_category', sa.String(30), nullable=False, default='interaction'),  # navigation, interaction, conversion, milestone
        sa.Column('event_data', JSONB, nullable=True),
        # Page/context
        sa.Column('page_path', sa.String(500), nullable=True),
        sa.Column('referrer', sa.String(500), nullable=True),
        # Feature context
        sa.Column('feature_id', sa.Integer, nullable=True, index=True),
        sa.Column('feature_status', sa.String(30), nullable=True),
        # User agent / device
        sa.Column('device_type', sa.String(20), nullable=True),  # desktop, mobile, tablet
        sa.Column('browser', sa.String(50), nullable=True),
        # Timestamps
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Journey funnels - funnel definitions for analysis
    op.create_table(
        'journey_funnels',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),
        # Funnel definition
        sa.Column('steps', JSONB, nullable=False),  # Ordered list of step definitions
        sa.Column('goal_event', sa.String(50), nullable=False),  # Final conversion event
        # Analysis window
        sa.Column('window_days', sa.Integer, nullable=False, default=30),
        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True, onupdate=sa.func.now()),
    )

    # Journey funnel snapshots - periodic funnel analysis results
    op.create_table(
        'journey_funnel_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('funnel_id', UUID(as_uuid=True), nullable=False, index=True),
        # Analysis period
        sa.Column('period_start', sa.DateTime, nullable=False),
        sa.Column('period_end', sa.DateTime, nullable=False),
        # Results
        sa.Column('step_counts', JSONB, nullable=False),  # Count per step
        sa.Column('conversion_rates', JSONB, nullable=False),  # Rate per step
        sa.Column('drop_off_rates', JSONB, nullable=False),  # Drop-off per step
        sa.Column('overall_conversion', sa.Float, nullable=False),
        sa.Column('avg_time_to_convert', sa.Float, nullable=True),  # Hours
        # Insights
        sa.Column('bottleneck_step', sa.String(100), nullable=True),
        sa.Column('insights', JSONB, nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        # Foreign key
        sa.ForeignKeyConstraint(['funnel_id'], ['journey_funnels.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('ix_chat_sessions_status', 'chat_sessions', ['status'])
    op.create_index('ix_chat_sessions_last_message', 'chat_sessions', ['last_message_at'])
    op.create_index('ix_chat_messages_created', 'chat_messages', ['created_at'])
    op.create_index('ix_chat_messages_intent', 'chat_messages', ['detected_intent'])
    op.create_index('ix_journey_events_timestamp', 'journey_events', ['timestamp'])
    op.create_index('ix_journey_events_category', 'journey_events', ['event_category'])
    op.create_index('ix_journey_funnel_snapshots_period', 'journey_funnel_snapshots', ['period_start', 'period_end'])

    # Insert default funnel definitions
    op.execute("""
        INSERT INTO journey_funnels (id, name, description, steps, goal_event, window_days, is_active)
        VALUES
        (
            gen_random_uuid(),
            'feature_request_funnel',
            'Track feature request submission process',
            '[
                {"name": "portal_visit", "event_type": "portal_visit"},
                {"name": "feature_view", "event_type": "feature_view"},
                {"name": "create_start", "event_type": "feature_create_start"},
                {"name": "create_submit", "event_type": "feature_create_submit"}
            ]'::jsonb,
            'feature_create_submit',
            30,
            true
        ),
        (
            gen_random_uuid(),
            'feature_to_release_funnel',
            'Track feature from request to release',
            '[
                {"name": "submitted", "event_type": "feature_submitted"},
                {"name": "analyzed", "event_type": "feature_analyzed"},
                {"name": "sprint_assigned", "event_type": "feature_sprint_assigned"},
                {"name": "development", "event_type": "feature_in_development"},
                {"name": "testing", "event_type": "feature_testing"},
                {"name": "released", "event_type": "feature_released"}
            ]'::jsonb,
            'feature_released',
            90,
            true
        ),
        (
            gen_random_uuid(),
            'feedback_collection_funnel',
            'Track feedback collection after release',
            '[
                {"name": "released", "event_type": "feature_released"},
                {"name": "feedback_requested", "event_type": "feedback_requested"},
                {"name": "feedback_opened", "event_type": "feedback_opened"},
                {"name": "feedback_submitted", "event_type": "feedback_submitted"}
            ]'::jsonb,
            'feedback_submitted',
            14,
            true
        )
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_journey_funnel_snapshots_period')
    op.drop_index('ix_journey_events_category')
    op.drop_index('ix_journey_events_timestamp')
    op.drop_index('ix_chat_messages_intent')
    op.drop_index('ix_chat_messages_created')
    op.drop_index('ix_chat_sessions_last_message')
    op.drop_index('ix_chat_sessions_status')

    # Drop tables
    op.drop_table('journey_funnel_snapshots')
    op.drop_table('journey_funnels')
    op.drop_table('journey_events')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
