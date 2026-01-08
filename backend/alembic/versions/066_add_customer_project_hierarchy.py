"""Add Customer/Project/Application Hierarchy

Revision ID: 066
Revises: 065
Create Date: 2026-01-02

Week 143 - Fase 28: Data Architecture Enhancement

Tables:
- customers: Customer entities (top of hierarchy)
- project_applications: N:M link between projects and applications

Columns:
- projects.customer_id: FK to customers table
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '066'
down_revision = '065'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('contact_name', sa.String(255), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('tier', sa.String(20), nullable=False, server_default='FREE'),
        sa.Column('billing_email', sa.String(255), nullable=True),
        sa.Column('external_id', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Create indexes for customers
    op.create_index('ix_customers_name', 'customers', ['name'])
    op.create_index('ix_customers_contact_email', 'customers', ['contact_email'])
    op.create_index('ix_customers_external_id', 'customers', ['external_id'])
    op.create_index('ix_customers_tier', 'customers', ['tier'])

    # Create project_applications link table (N:M)
    op.create_table(
        'project_applications',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.Integer, nullable=False),
        sa.Column('application_id', sa.Integer, nullable=False),
        sa.Column('role', sa.String(50), nullable=True),
        sa.Column('impact_level', sa.String(20), nullable=True),
        sa.Column('linked_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('project_id', 'application_id', name='uq_project_application'),
    )

    # Create indexes for project_applications
    op.create_index('ix_project_applications_project_id', 'project_applications', ['project_id'])
    op.create_index('ix_project_applications_application_id', 'project_applications', ['application_id'])

    # Add customer_id column to projects table
    op.add_column('projects', sa.Column('customer_id', sa.Integer, nullable=True))

    # Create foreign key from projects to customers
    op.create_foreign_key(
        'fk_projects_customer_id',
        'projects',
        'customers',
        ['customer_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Create index for projects.customer_id
    op.create_index('ix_projects_customer_id', 'projects', ['customer_id'])


def downgrade() -> None:
    # Drop index and FK from projects
    op.drop_index('ix_projects_customer_id', table_name='projects')
    op.drop_constraint('fk_projects_customer_id', 'projects', type_='foreignkey')
    op.drop_column('projects', 'customer_id')

    # Drop project_applications table
    op.drop_index('ix_project_applications_application_id', table_name='project_applications')
    op.drop_index('ix_project_applications_project_id', table_name='project_applications')
    op.drop_table('project_applications')

    # Drop customers table
    op.drop_index('ix_customers_tier', table_name='customers')
    op.drop_index('ix_customers_external_id', table_name='customers')
    op.drop_index('ix_customers_contact_email', table_name='customers')
    op.drop_index('ix_customers_name', table_name='customers')
    op.drop_table('customers')
