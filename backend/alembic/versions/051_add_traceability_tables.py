"""Add traceability tables for Week 113 Phase 4.5

Revision ID: 051_add_traceability_tables
Revises: 050_add_item_kanban_columns
Create Date: 2025-12-27

Week 113: Traceability Implementation
- story_business_rules: Join table linking stories to business rules
- rule_workflows: CRUD workflow groupings of business rules
- traceability_links: Generic traceability links between any entities
- Views for impact analysis and traceability matrix
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '051_add_traceability_tables'
down_revision = '050_add_item_kanban_columns'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Story-Business Rule join table (many-to-many)
    op.create_table(
        'story_business_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('story_id', UUID(as_uuid=True), sa.ForeignKey('task_stories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_id', sa.String(20), sa.ForeignKey('business_rules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('link_type', sa.String(30), nullable=False, server_default='implements'),  # implements, validates, triggers
        sa.Column('confidence', sa.Float(), nullable=True),  # Auto-link confidence
        sa.Column('linked_by', sa.String(50), nullable=True),  # 'auto' or user_id
        sa.Column('link_reason', sa.Text(), nullable=True),  # Why this link exists
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('story_id', 'rule_id', name='uq_story_rule')
    )
    op.create_index('ix_story_business_rules_story_id', 'story_business_rules', ['story_id'])
    op.create_index('ix_story_business_rules_rule_id', 'story_business_rules', ['rule_id'])

    # 2. Feature-Business Rule join table (for direct feature-level rules)
    op.create_table(
        'feature_business_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('feature_id', UUID(as_uuid=True), sa.ForeignKey('task_features.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_id', sa.String(20), sa.ForeignKey('business_rules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('link_type', sa.String(30), nullable=False, server_default='contains'),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('linked_by', sa.String(50), nullable=True),
        sa.Column('link_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('feature_id', 'rule_id', name='uq_feature_rule')
    )
    op.create_index('ix_feature_business_rules_feature_id', 'feature_business_rules', ['feature_id'])
    op.create_index('ix_feature_business_rules_rule_id', 'feature_business_rules', ['rule_id'])

    # 3. Epic-Business Rule join table (for epic-level architectural rules)
    op.create_table(
        'epic_business_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('epic_id', UUID(as_uuid=True), sa.ForeignKey('task_epics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_id', sa.String(20), sa.ForeignKey('business_rules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('link_type', sa.String(30), nullable=False, server_default='governs'),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('linked_by', sa.String(50), nullable=True),
        sa.Column('link_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('epic_id', 'rule_id', name='uq_epic_rule')
    )
    op.create_index('ix_epic_business_rules_epic_id', 'epic_business_rules', ['epic_id'])
    op.create_index('ix_epic_business_rules_rule_id', 'epic_business_rules', ['rule_id'])

    # 4. Rule Workflows - CRUD workflow groupings
    op.create_table(
        'rule_workflows',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),  # e.g., "Afspraak CRUD", "User Authentication"
        sa.Column('workflow_type', sa.String(50), nullable=False),  # CRUD, STATE_MACHINE, APPROVAL, etc.
        sa.Column('entity_name', sa.String(100), nullable=True),  # Primary entity: "Afspraak", "User"
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rule_count', sa.Integer(), default=0),
        sa.Column('operations', JSONB, nullable=True),  # {"create": ["BR-001"], "read": ["BR-002"], ...}
        sa.Column('mermaid_diagram', sa.Text(), nullable=True),  # Auto-generated Mermaid diagram
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rule_workflows_project_id', 'rule_workflows', ['project_id'])
    op.create_index('ix_rule_workflows_workflow_type', 'rule_workflows', ['workflow_type'])

    # 5. Rule Workflow Members - rules in a workflow
    op.create_table(
        'rule_workflow_members',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('workflow_id', sa.Integer(), sa.ForeignKey('rule_workflows.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_id', sa.String(20), sa.ForeignKey('business_rules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('operation', sa.String(30), nullable=True),  # create, read, update, delete, validate, etc.
        sa.Column('sequence_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_id', 'rule_id', name='uq_workflow_rule')
    )
    op.create_index('ix_rule_workflow_members_workflow_id', 'rule_workflow_members', ['workflow_id'])
    op.create_index('ix_rule_workflow_members_rule_id', 'rule_workflow_members', ['rule_id'])

    # 6. Add workflow_id to business_rules for quick lookup
    op.add_column('business_rules',
        sa.Column('workflow_id', sa.Integer(), sa.ForeignKey('rule_workflows.id', ondelete='SET NULL'), nullable=True)
    )
    op.create_index('ix_business_rules_workflow_id', 'business_rules', ['workflow_id'])

    # 7. Add entity_name to business_rules for entity-based grouping
    op.add_column('business_rules',
        sa.Column('entity_name', sa.String(100), nullable=True)
    )
    op.create_index('ix_business_rules_entity_name', 'business_rules', ['entity_name'])

    # 8. Traceability Matrix View (materialized for performance)
    # Note: Executed as raw SQL for view creation
    op.execute("""
        CREATE OR REPLACE VIEW v_traceability_matrix AS
        SELECT
            e.id as epic_id,
            e.title as epic_title,
            f.id as feature_id,
            f.title as feature_title,
            s.id as story_id,
            s.title as story_title,
            br.id as rule_id,
            br.rule_type,
            br.natural_language as rule_description,
            br.confidence as rule_confidence,
            sbr.link_type,
            sbr.linked_by,
            e.project_id
        FROM task_stories s
        LEFT JOIN story_business_rules sbr ON s.id = sbr.story_id
        LEFT JOIN business_rules br ON sbr.rule_id = br.id
        LEFT JOIN task_features f ON s.feature_id = f.id
        LEFT JOIN task_epics e ON f.epic_id = e.id
        WHERE br.id IS NOT NULL
        ORDER BY e.sequence_number, f.sequence_number, s.sequence_number
    """)

    # 9. Rule Impact View - shows what stories/features are affected by a rule change
    op.execute("""
        CREATE OR REPLACE VIEW v_rule_impact AS
        SELECT
            br.id as rule_id,
            br.rule_type,
            br.natural_language as rule_description,
            br.source_file,
            br.entity_name,
            COUNT(DISTINCT sbr.story_id) as story_count,
            COUNT(DISTINCT f.id) as feature_count,
            COUNT(DISTINCT e.id) as epic_count,
            ARRAY_AGG(DISTINCT s.title) as affected_stories,
            ARRAY_AGG(DISTINCT f.title) as affected_features,
            ARRAY_AGG(DISTINCT e.title) as affected_epics
        FROM business_rules br
        LEFT JOIN story_business_rules sbr ON br.id = sbr.rule_id
        LEFT JOIN task_stories s ON sbr.story_id = s.id
        LEFT JOIN task_features f ON s.feature_id = f.id
        LEFT JOIN task_epics e ON f.epic_id = e.id
        GROUP BY br.id, br.rule_type, br.natural_language, br.source_file, br.entity_name
    """)


def downgrade():
    # Drop views first
    op.execute("DROP VIEW IF EXISTS v_rule_impact")
    op.execute("DROP VIEW IF EXISTS v_traceability_matrix")

    # Drop indexes and columns from business_rules
    op.drop_index('ix_business_rules_entity_name', table_name='business_rules')
    op.drop_column('business_rules', 'entity_name')
    op.drop_index('ix_business_rules_workflow_id', table_name='business_rules')
    op.drop_column('business_rules', 'workflow_id')

    # Drop tables in reverse order
    op.drop_table('rule_workflow_members')
    op.drop_table('rule_workflows')
    op.drop_table('epic_business_rules')
    op.drop_table('feature_business_rules')
    op.drop_table('story_business_rules')
