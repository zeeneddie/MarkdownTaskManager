"""Add technical debt tables

Revision ID: 007
Revises: 006
Create Date: 2025-11-22

Week 18: Basil Integration - Technical Debt Management
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create technical_debt_snapshots table first (referenced by items)
    op.create_table(
        'technical_debt_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('scan_duration_seconds', sa.Float(), nullable=True),
        sa.Column('total_items', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_principal', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('total_interest', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('productive_hours', sa.Float(), server_default='160.0', nullable=True),
        sa.Column('debt_ratio', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('items_by_type', sa.JSON(), nullable=True),
        sa.Column('principal_by_type', sa.JSON(), nullable=True),
        sa.Column('items_by_severity', sa.JSON(), nullable=True),
        sa.Column('critical_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('high_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('medium_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('low_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('code_coverage', sa.Float(), nullable=True),
        sa.Column('code_duplication', sa.Float(), nullable=True),
        sa.Column('security_issues', sa.Integer(), server_default='0', nullable=True),
        sa.Column('outdated_dependencies', sa.Integer(), server_default='0', nullable=True),
        sa.Column('avg_complexity', sa.Float(), nullable=True),
        sa.Column('items_delta', sa.Integer(), server_default='0', nullable=True),
        sa.Column('principal_delta', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('ratio_delta', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('trigger', sa.String(length=50), server_default='scheduled', nullable=True),
        sa.Column('commit_hash', sa.String(length=64), nullable=True),
        sa.Column('branch', sa.String(length=255), nullable=True),
        sa.Column('scanner_versions', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_technical_debt_snapshots_id', 'technical_debt_snapshots', ['id'], unique=False)
    op.create_index('ix_technical_debt_snapshots_timestamp', 'technical_debt_snapshots', ['timestamp'], unique=False)

    # Create technical_debt_items table
    op.create_table(
        'technical_debt_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('debt_type', sa.Enum('code_smell', 'security', 'performance', 'dependency', 'test_gap', 'documentation', 'architecture', 'duplication', 'compatibility', 'accessibility', name='debttype'), nullable=False),
        sa.Column('severity', sa.Enum('critical', 'high', 'medium', 'low', name='debtseverity'), nullable=False),
        sa.Column('status', sa.Enum('open', 'acknowledged', 'planned', 'in_progress', 'resolved', 'wont_fix', 'false_positive', name='debtstatus'), server_default='open', nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('line_start', sa.Integer(), nullable=True),
        sa.Column('line_end', sa.Integer(), nullable=True),
        sa.Column('function_name', sa.String(length=255), nullable=True),
        sa.Column('module_name', sa.String(length=255), nullable=True),
        sa.Column('principal', sa.Float(), server_default='1.0', nullable=True),
        sa.Column('interest_rate', sa.Float(), server_default='0.1', nullable=True),
        sa.Column('detected_by', sa.Enum('scanner_ruff', 'scanner_eslint', 'scanner_bandit', 'scanner_npm_audit', 'scanner_sonar', 'scanner_coverage', 'agent_quinn', 'agent_marcus', 'manual', 'pr_review', name='detectionsource'), nullable=False),
        sa.Column('detection_rule', sa.String(length=255), nullable=True),
        sa.Column('detection_message', sa.Text(), nullable=True),
        sa.Column('first_detected', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('occurrence_count', sa.Integer(), server_default='1', nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(length=100), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolution_commit', sa.String(length=64), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('snapshot_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['snapshot_id'], ['technical_debt_snapshots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_technical_debt_items_id', 'technical_debt_items', ['id'], unique=False)
    op.create_index('ix_technical_debt_items_debt_type', 'technical_debt_items', ['debt_type'], unique=False)
    op.create_index('ix_technical_debt_items_severity', 'technical_debt_items', ['severity'], unique=False)
    op.create_index('ix_technical_debt_items_status', 'technical_debt_items', ['status'], unique=False)

    # Create remediation_plans table
    op.create_table(
        'remediation_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='draft', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('target_date', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('target_debt_ratio', sa.Float(), nullable=True),
        sa.Column('max_effort_hours', sa.Float(), nullable=True),
        sa.Column('priority_types', sa.JSON(), nullable=True),
        sa.Column('item_ids', sa.JSON(), nullable=True),
        sa.Column('total_items', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_effort_hours', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('estimated_interest_saved', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('estimated_ratio_reduction', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('items_completed', sa.Integer(), server_default='0', nullable=True),
        sa.Column('effort_spent_hours', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('actual_interest_saved', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('assigned_agent', sa.String(length=50), server_default='marcus', nullable=True),
        sa.Column('assigned_to', sa.String(length=100), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('snapshot_id', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['snapshot_id'], ['technical_debt_snapshots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_remediation_plans_id', 'remediation_plans', ['id'], unique=False)

    # Create debt_resolutions table
    op.create_table(
        'debt_resolutions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('debt_item_id', sa.Integer(), nullable=False),
        sa.Column('resolution_type', sa.String(length=50), nullable=False),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_by_agent', sa.String(length=50), nullable=True),
        sa.Column('resolved_by_human', sa.String(length=100), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('estimated_hours', sa.Float(), nullable=True),
        sa.Column('actual_hours', sa.Float(), nullable=True),
        sa.Column('commit_hash', sa.String(length=64), nullable=True),
        sa.Column('pr_number', sa.Integer(), nullable=True),
        sa.Column('files_changed', sa.JSON(), nullable=True),
        sa.Column('lines_added', sa.Integer(), server_default='0', nullable=True),
        sa.Column('lines_removed', sa.Integer(), server_default='0', nullable=True),
        sa.Column('verified', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('verified_by', sa.String(length=100), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('interest_eliminated', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('new_issues_introduced', sa.Integer(), server_default='0', nullable=True),
        sa.Column('plan_id', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['debt_item_id'], ['technical_debt_items.id'], ),
        sa.ForeignKeyConstraint(['plan_id'], ['remediation_plans.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_debt_resolutions_id', 'debt_resolutions', ['id'], unique=False)

    # Create quality_gate_results table
    op.create_table(
        'quality_gate_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('trigger', sa.String(length=50), server_default='pr', nullable=True),
        sa.Column('commit_hash', sa.String(length=64), nullable=True),
        sa.Column('branch', sa.String(length=255), nullable=True),
        sa.Column('pr_number', sa.Integer(), nullable=True),
        sa.Column('passed', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('blocked', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('gate_results', sa.JSON(), nullable=True),
        sa.Column('test_score', sa.Float(), nullable=True),
        sa.Column('coverage_score', sa.Float(), nullable=True),
        sa.Column('security_score', sa.Float(), nullable=True),
        sa.Column('debt_ratio_score', sa.Float(), nullable=True),
        sa.Column('failure_reasons', sa.JSON(), nullable=True),
        sa.Column('blocking_issues', sa.JSON(), nullable=True),
        sa.Column('override_approved', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('override_by', sa.String(length=100), nullable=True),
        sa.Column('override_reason', sa.Text(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('snapshot_id', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['snapshot_id'], ['technical_debt_snapshots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_quality_gate_results_id', 'quality_gate_results', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_quality_gate_results_id', table_name='quality_gate_results')
    op.drop_table('quality_gate_results')

    op.drop_index('ix_debt_resolutions_id', table_name='debt_resolutions')
    op.drop_table('debt_resolutions')

    op.drop_index('ix_remediation_plans_id', table_name='remediation_plans')
    op.drop_table('remediation_plans')

    op.drop_index('ix_technical_debt_items_status', table_name='technical_debt_items')
    op.drop_index('ix_technical_debt_items_severity', table_name='technical_debt_items')
    op.drop_index('ix_technical_debt_items_debt_type', table_name='technical_debt_items')
    op.drop_index('ix_technical_debt_items_id', table_name='technical_debt_items')
    op.drop_table('technical_debt_items')

    op.drop_index('ix_technical_debt_snapshots_timestamp', table_name='technical_debt_snapshots')
    op.drop_index('ix_technical_debt_snapshots_id', table_name='technical_debt_snapshots')
    op.drop_table('technical_debt_snapshots')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS debttype')
    op.execute('DROP TYPE IF EXISTS debtseverity')
    op.execute('DROP TYPE IF EXISTS debtstatus')
    op.execute('DROP TYPE IF EXISTS detectionsource')
