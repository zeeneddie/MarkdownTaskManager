"""Initial multi-tenant schema with RLS policies.

Revision ID: 001_initial_multitenant
Revises:
Create Date: 2026-01-15
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "001_initial_multitenant"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==========================================================================
    # TENANTS TABLE
    # ==========================================================================
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("subdomain", sa.String(63), unique=True, nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "suspended", "pending", "cancelled", name="tenant_status"),
            default="pending",
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column(
            "subscription_tier",
            sa.Enum("free", "starter", "professional", "enterprise", name="subscription_tier"),
            default="free",
            nullable=False,
        ),
        sa.Column("monthly_fp_allocation", sa.Integer(), default=0, nullable=False),
        sa.Column("fp_overage_allowed", sa.Boolean(), default=False, nullable=False),
        sa.Column("primary_email", sa.String(255), nullable=True),
        sa.Column("billing_email", sa.String(255), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), default={}, nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tenants_subdomain", "tenants", ["subdomain"])

    # ==========================================================================
    # TENANT SETTINGS TABLE
    # ==========================================================================
    op.create_table(
        "tenant_settings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("primary_color", sa.String(7), default="#3B82F6", nullable=False),
        sa.Column("secondary_color", sa.String(7), default="#10B981", nullable=False),
        sa.Column("custom_css", sa.Text(), nullable=True),
        sa.Column("features_enabled", sa.JSON(), default={}, nullable=False),
        sa.Column("email_notifications", sa.Boolean(), default=True, nullable=False),
        sa.Column("slack_webhook_url", sa.String(500), nullable=True),
        sa.Column("main_backend_project_ids", sa.JSON(), default=[], nullable=False),
        sa.Column("sla_response_hours", sa.Integer(), default=24, nullable=False),
        sa.Column("sla_resolution_hours", sa.Integer(), default=72, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ==========================================================================
    # USERS TABLE
    # ==========================================================================
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("is_superuser", sa.Boolean(), default=False, nullable=False),
        sa.Column("email_verified", sa.Boolean(), default=False, nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "failed_login_attempts",
            sa.Enum("0", "1", "2", "3", "4", "5", name="failed_login_attempts_enum"),
            default="0",
            nullable=False,
        ),
        sa.Column("preferences", sa.JSON(), default={}, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ==========================================================================
    # TENANT USERS (Association) TABLE
    # ==========================================================================
    op.create_table(
        "tenant_users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum("viewer", "submitter", "approver", "manager", "admin", name="user_role"),
            default="viewer",
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("epic_permissions", sa.JSON(), default={}, nullable=False),
        sa.Column("feature_permissions", sa.JSON(), default={}, nullable=False),
        sa.Column("invited_by_id", sa.String(36), nullable=True),
        sa.Column("invited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_user"),
    )
    op.create_index("ix_tenant_users_tenant_id", "tenant_users", ["tenant_id"])
    op.create_index("ix_tenant_users_user_id", "tenant_users", ["user_id"])

    # ==========================================================================
    # PROJECTS TABLE
    # ==========================================================================
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("draft", "active", "on_hold", "completed", "archived", name="project_status"),
            default="draft",
            nullable=False,
        ),
        sa.Column(
            "project_type",
            sa.Enum("greenfield", "brownfield", "migration", "maintenance", name="project_type"),
            default="brownfield",
            nullable=False,
        ),
        sa.Column("total_fp_estimated", sa.Float(), default=0.0, nullable=False),
        sa.Column("total_fp_consumed", sa.Float(), default=0.0, nullable=False),
        sa.Column("current_sprint_fp", sa.Float(), default=0.0, nullable=False),
        sa.Column("completion_percentage", sa.Float(), default=0.0, nullable=False),
        sa.Column("stories_total", sa.Integer(), default=0, nullable=False),
        sa.Column("stories_completed", sa.Integer(), default=0, nullable=False),
        sa.Column("main_backend_session_id", sa.String(36), nullable=True),
        sa.Column("brown_paper_session_id", sa.String(36), nullable=True),
        sa.Column("analysis_contract_id", sa.String(36), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("target_completion_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tech_stack", sa.JSON(), default=[], nullable=False),
        sa.Column("metadata", sa.JSON(), default={}, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_projects_tenant_id", "projects", ["tenant_id"])

    # ==========================================================================
    # PROJECT REPOSITORIES TABLE
    # ==========================================================================
    op.create_table(
        "project_repositories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("clone_path", sa.String(500), nullable=True),
        sa.Column("repository_type", sa.String(50), default="git", nullable=False),
        sa.Column("default_branch", sa.String(100), default="main", nullable=False),
        sa.Column("last_analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_commit_hash", sa.String(40), nullable=True),
        sa.Column("total_files", sa.Integer(), default=0, nullable=False),
        sa.Column("total_loc", sa.Integer(), default=0, nullable=False),
        sa.Column("languages", sa.JSON(), default={}, nullable=False),
        sa.Column("metadata", sa.JSON(), default={}, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_project_repositories_tenant_id", "project_repositories", ["tenant_id"])
    op.create_index("ix_project_repositories_project_id", "project_repositories", ["project_id"])

    # ==========================================================================
    # ROW-LEVEL SECURITY POLICIES
    # ==========================================================================

    # Enable RLS on tenant-scoped tables
    op.execute("ALTER TABLE projects ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE project_repositories ENABLE ROW LEVEL SECURITY")

    # Create RLS policies for projects
    op.execute("""
        CREATE POLICY projects_tenant_isolation ON projects
        FOR ALL
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
    """)

    # Create RLS policies for project_repositories
    op.execute("""
        CREATE POLICY project_repositories_tenant_isolation ON project_repositories
        FOR ALL
        USING (tenant_id = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
    """)

    # Grant usage to application user (adjust username as needed)
    # op.execute("GRANT ALL ON ALL TABLES IN SCHEMA public TO marqed_app")


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS projects_tenant_isolation ON projects")
    op.execute("DROP POLICY IF EXISTS project_repositories_tenant_isolation ON project_repositories")

    # Disable RLS
    op.execute("ALTER TABLE projects DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE project_repositories DISABLE ROW LEVEL SECURITY")

    # Drop tables in reverse order
    op.drop_table("project_repositories")
    op.drop_table("projects")
    op.drop_table("tenant_users")
    op.drop_table("users")
    op.drop_table("tenant_settings")
    op.drop_table("tenants")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS project_type")
    op.execute("DROP TYPE IF EXISTS project_status")
    op.execute("DROP TYPE IF EXISTS user_role")
    op.execute("DROP TYPE IF EXISTS failed_login_attempts_enum")
    op.execute("DROP TYPE IF EXISTS subscription_tier")
    op.execute("DROP TYPE IF EXISTS tenant_status")
