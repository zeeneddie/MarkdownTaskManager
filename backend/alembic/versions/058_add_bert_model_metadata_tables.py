"""Add BERT model metadata tables for Week 124

Revision ID: 058_add_bert_model_metadata
Revises: 057_add_cira_causality_tables
Create Date: 2024-12-29

Week 124: Full BERT Integration
- Stores fine-tuned model metadata
- Tracks training history
- Enables per-project model configuration
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '058_add_bert_model_metadata'
down_revision = '057_add_cira_causality_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create bert_model_metadata table
    op.create_table(
        'bert_model_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('model_name', sa.String(200), nullable=False),
        sa.Column('base_model', sa.String(200), nullable=False, default='bert-base-cased'),
        sa.Column('model_path', sa.String(500), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('precision', sa.Float(), nullable=True),
        sa.Column('recall', sa.Float(), nullable=True),
        sa.Column('training_samples', sa.Integer(), nullable=True),
        sa.Column('validation_samples', sa.Integer(), nullable=True),
        sa.Column('epochs_trained', sa.Integer(), nullable=True),
        sa.Column('learning_rate', sa.Float(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True, default=1.0),
        sa.Column('config', postgresql.JSONB(), nullable=True),
        sa.Column('training_history', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create index for project lookup
    op.create_index('ix_bert_model_metadata_project_id', 'bert_model_metadata', ['project_id'])
    op.create_index('ix_bert_model_metadata_status', 'bert_model_metadata', ['status'])

    # Create bert_training_runs table
    op.create_table(
        'bert_training_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bert_model_metadata.id'), nullable=False),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('run_type', sa.String(50), nullable=False),  # fine_tune, calibrate
        sa.Column('status', sa.String(50), nullable=False, default='running'),
        sa.Column('started_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('epochs', sa.Integer(), nullable=True),
        sa.Column('learning_rate', sa.Float(), nullable=True),
        sa.Column('train_samples', sa.Integer(), nullable=True),
        sa.Column('val_samples', sa.Integer(), nullable=True),
        sa.Column('train_accuracy', sa.Float(), nullable=True),
        sa.Column('val_accuracy', sa.Float(), nullable=True),
        sa.Column('train_loss', sa.Float(), nullable=True),
        sa.Column('val_loss', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('optimal_temperature', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('config', postgresql.JSONB(), nullable=True),
        sa.Column('metrics_history', postgresql.JSONB(), nullable=True),
    )

    # Create indexes
    op.create_index('ix_bert_training_runs_model_id', 'bert_training_runs', ['model_id'])
    op.create_index('ix_bert_training_runs_project_id', 'bert_training_runs', ['project_id'])
    op.create_index('ix_bert_training_runs_status', 'bert_training_runs', ['status'])

    # Add model_id column to causal_sessions for tracking which model was used
    op.add_column(
        'causal_sessions',
        sa.Column('model_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        'causal_sessions',
        sa.Column('extraction_method', sa.String(50), nullable=True, default='rule_based')
    )


def downgrade() -> None:
    # Remove columns from causal_sessions
    op.drop_column('causal_sessions', 'extraction_method')
    op.drop_column('causal_sessions', 'model_id')

    # Drop bert_training_runs
    op.drop_index('ix_bert_training_runs_status')
    op.drop_index('ix_bert_training_runs_project_id')
    op.drop_index('ix_bert_training_runs_model_id')
    op.drop_table('bert_training_runs')

    # Drop bert_model_metadata
    op.drop_index('ix_bert_model_metadata_status')
    op.drop_index('ix_bert_model_metadata_project_id')
    op.drop_table('bert_model_metadata')
