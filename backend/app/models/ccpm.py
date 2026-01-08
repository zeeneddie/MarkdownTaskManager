"""
CCPM Models - Week 79

SQLAlchemy models for:
- Git Worktrees: Parallel agent workspaces
- GitHub Issues Sync: Bidirectional synchronization
- PRD Decompositions: Product Requirements Document breakdown
- Task Recommendations: Intelligent task prioritization
"""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, func, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from enum import Enum
import uuid

from app.database import Base


class WorktreeStatus(str, Enum):
    """Git worktree status."""
    ACTIVE = "active"
    MERGED = "merged"
    ABANDONED = "abandoned"
    CONFLICT = "conflict"


class MergeStatus(str, Enum):
    """Merge operation status."""
    PENDING = "pending"
    MERGED = "merged"
    CONFLICT = "conflict"
    REJECTED = "rejected"


class SyncDirection(str, Enum):
    """GitHub sync direction."""
    GITHUB_TO_LOCAL = "github_to_local"
    LOCAL_TO_GITHUB = "local_to_github"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(str, Enum):
    """GitHub sync status."""
    SYNCED = "synced"
    PENDING = "pending"
    CONFLICT = "conflict"
    ERROR = "error"


class DecompositionStatus(str, Enum):
    """PRD decomposition status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RecommendationStatus(str, Enum):
    """Task recommendation status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"


class GitWorktree(Base):
    """Parallel agent workspace using git worktrees."""
    __tablename__ = "git_worktrees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    agent_id = Column(String(100), nullable=False)  # Agent using this worktree
    worktree_path = Column(String(500), nullable=False)  # Local filesystem path
    base_branch = Column(String(200), nullable=False)  # e.g., main, develop
    work_branch = Column(String(200), nullable=False)  # Agent's working branch
    status = Column(String(50), default=WorktreeStatus.ACTIVE.value)
    commit_count = Column(Integer, default=0)
    files_changed = Column(Integer, default=0)
    last_commit_sha = Column(String(40), nullable=True)
    last_commit_message = Column(Text, nullable=True)
    merge_status = Column(String(50), nullable=True)
    merge_target = Column(String(200), nullable=True)
    merged_at = Column(DateTime, nullable=True)
    merged_by = Column(String(100), nullable=True)
    worktree_metadata = Column(JSONB, default={})
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="worktrees")


class GitHubIssueSync(Base):
    """Bidirectional GitHub issue synchronization."""
    __tablename__ = "github_issues_sync"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    github_repo = Column(String(200), nullable=False)  # owner/repo format
    github_issue_number = Column(Integer, nullable=False)
    github_issue_id = Column(BigInteger, nullable=True)  # GitHub's internal ID
    local_task_id = Column(UUID(as_uuid=True), nullable=True)  # Link to local task
    local_task_type = Column(String(50), nullable=True)  # epic, feature, story, task
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=True)
    state = Column(String(20), nullable=False)  # open, closed
    labels = Column(JSONB, default=[])
    assignees = Column(JSONB, default=[])
    milestone = Column(String(200), nullable=True)
    github_url = Column(String(500), nullable=True)
    sync_direction = Column(String(20), default=SyncDirection.BIDIRECTIONAL.value)
    last_synced_at = Column(DateTime, nullable=True)
    github_updated_at = Column(DateTime, nullable=True)
    local_updated_at = Column(DateTime, nullable=True)
    sync_status = Column(String(50), default=SyncStatus.SYNCED.value)
    sync_error = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="github_issues")


class PRDDecomposition(Base):
    """Product Requirements Document decomposition into tasks."""
    __tablename__ = "prd_decompositions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(500), nullable=False)
    prd_content = Column(Text, nullable=False)  # Original PRD text
    prd_hash = Column(String(64), nullable=True)  # SHA256 hash for change detection
    status = Column(String(50), default=DecompositionStatus.PENDING.value)
    epics_count = Column(Integer, default=0)
    features_count = Column(Integer, default=0)
    stories_count = Column(Integer, default=0)
    tasks_count = Column(Integer, default=0)
    total_story_points = Column(Integer, nullable=True)
    total_function_points = Column(Float, nullable=True)
    decomposition_result = Column(JSONB, default={})  # Full hierarchical breakdown
    agent_used = Column(String(100), nullable=True)  # Which agent performed decomposition
    llm_model = Column(String(100), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="prd_decompositions")


class TaskRecommendation(Base):
    """Intelligent task prioritization recommendation."""
    __tablename__ = "task_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    task_id = Column(UUID(as_uuid=True), nullable=True)  # Recommended task
    task_type = Column(String(50), nullable=True)
    task_title = Column(String(500), nullable=False)
    priority_score = Column(Float, nullable=False)  # 0-100 priority score
    reasoning = Column(Text, nullable=True)  # Why this task is recommended
    factors = Column(JSONB, default={})  # Breakdown of scoring factors
    dependencies_met = Column(Boolean, default=True)
    blocked_by = Column(JSONB, default=[])  # List of blocking task IDs
    recommended_agent = Column(String(100), nullable=True)  # Best agent for this task
    estimated_effort_hours = Column(Float, nullable=True)
    impact_score = Column(Float, nullable=True)  # Business impact
    urgency_score = Column(Float, nullable=True)  # Time sensitivity
    complexity_score = Column(Float, nullable=True)  # Technical complexity
    status = Column(String(50), default=RecommendationStatus.PENDING.value)
    accepted_at = Column(DateTime, nullable=True)
    accepted_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)  # Recommendation validity

    # Relationships
    project = relationship("Project", back_populates="task_recommendations")
