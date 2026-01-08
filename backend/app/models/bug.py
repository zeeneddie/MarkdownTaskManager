"""
Bug Model - Issue Tracking

Standalone bugs that can be tracked on the Kanban board alongside Stories and Tasks.
Bugs can optionally be linked to a Project, Epic, or Feature.

Status Flow: draft → analysis → planned → in_progress → in_review → done
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class BugSeverity:
    """Bug severity levels"""
    CRITICAL = "critical"  # System down, data loss
    HIGH = "high"          # Major feature broken
    MEDIUM = "medium"      # Feature impaired
    LOW = "low"            # Minor issue


class BugStatus:
    """Bug lifecycle status"""
    DRAFT = "draft"              # Just reported, unconfirmed
    CONFIRMED = "confirmed"      # Reproducible, awaiting analysis
    ANALYSIS = "analysis"        # Being analyzed/estimated
    PLANNED = "planned"          # Ready for sprint
    IN_PROGRESS = "in_progress"  # Being fixed
    IN_REVIEW = "in_review"      # Fix in code review
    TESTING = "testing"          # QA validation
    DONE = "done"                # Fixed and verified
    WONT_FIX = "wont_fix"        # Declined
    DUPLICATE = "duplicate"      # Already tracked elsewhere


class Bug(Base):
    """
    Bug: Defect or issue report that needs investigation and fixing.

    Standalone item (not nested under Story) because bugs:
    - Can be reported at any time
    - May not fit neatly into existing user stories
    - Need their own lifecycle (confirm → analyze → fix → verify)

    Shows on Kanban board in appropriate lane based on status.
    """
    __tablename__ = "bugs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Bug identification
    bug_number = Column(String(20), nullable=False, unique=True, index=True)  # BUG-001
    title = Column(String(300), nullable=False, index=True)
    description = Column(Text, nullable=False)

    # Status & Priority
    status = Column(String(20), nullable=False, default=BugStatus.DRAFT, index=True)
    severity = Column(String(20), nullable=False, default=BugSeverity.MEDIUM)
    priority = Column(String(20), nullable=False, default="medium")  # For sprint planning

    # Categorization
    category = Column(String(50), nullable=True)  # "Backend", "Frontend", "Database", etc.
    component = Column(String(100), nullable=True)  # Specific module/component
    tags = Column(JSONB, nullable=True)  # ["security", "performance", "ux"]

    # Reproduction
    reproduction_steps = Column(Text, nullable=True)
    expected_behavior = Column(Text, nullable=True)
    actual_behavior = Column(Text, nullable=True)
    environment = Column(JSONB, nullable=True)  # {"browser": "Chrome", "os": "Windows", "version": "1.2.3"}

    # Technical Analysis
    root_cause = Column(Text, nullable=True)
    affected_files = Column(JSONB, nullable=True)  # ["src/module.py", "tests/test_module.py"]
    related_bugs = Column(JSONB, nullable=True)  # ["BUG-002", "BUG-005"]

    # Estimation (filled during Analysis phase)
    story_points = Column(Integer, nullable=True)  # Fibonacci: 1, 2, 3, 5, 8
    function_points = Column(Integer, nullable=True)  # IFPUG function points
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)

    # Acceptance Criteria
    acceptance_criteria = Column(JSONB, nullable=True)  # [{"criterion": "...", "met": false}]

    # Linking (optional - bugs can be standalone)
    project_id = Column(String(50), ForeignKey("items.id", ondelete="SET NULL"), nullable=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True)
    epic_id = Column(UUID(as_uuid=True), ForeignKey("task_epics.id", ondelete="SET NULL"), nullable=True)
    feature_id = Column(UUID(as_uuid=True), ForeignKey("task_features.id", ondelete="SET NULL"), nullable=True)

    # Assignment
    reporter = Column(String(100), nullable=True)  # Who reported
    assigned_to = Column(String(100), nullable=True)  # Developer assigned
    reviewer = Column(String(100), nullable=True)  # Code reviewer

    # Blocking
    is_blocked = Column(Boolean, default=False)
    blocked_reason = Column(Text, nullable=True)
    blocking_bugs = Column(JSONB, nullable=True)  # Bug IDs this bug blocks

    # Git Integration
    branch_name = Column(String(200), nullable=True)
    commit_sha = Column(String(40), nullable=True)
    pull_request_url = Column(String(500), nullable=True)

    # Source (where bug was found)
    source = Column(String(50), nullable=True)  # "user_report", "automated_test", "code_review", "production"
    source_reference = Column(String(500), nullable=True)  # URL or ticket reference

    # Dates
    reported_at = Column(DateTime, default=lambda: datetime.utcnow())
    confirmed_at = Column(DateTime, nullable=True)
    analysis_started_at = Column(DateTime, nullable=True)
    analysis_completed_at = Column(DateTime, nullable=True)
    fix_started_at = Column(DateTime, nullable=True)
    fixed_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    # Import metadata (for bugs imported from markdown)
    imported_from = Column(String(500), nullable=True)  # Original file path
    extra_metadata = Column("metadata", JSONB, nullable=True)

    def __repr__(self):
        return f"<Bug(id={self.id}, number='{self.bug_number}', title='{self.title[:40]}', status='{self.status}')>"


class BugComment(Base):
    """Comments/updates on a bug"""
    __tablename__ = "bug_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bug_id = Column(UUID(as_uuid=True), ForeignKey("bugs.id", ondelete="CASCADE"), nullable=False, index=True)

    author = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    comment_type = Column(String(20), default="comment")  # "comment", "status_change", "assignment", "analysis"

    # For status changes
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    # Relationship
    bug = relationship("Bug", backref="comments")

    def __repr__(self):
        return f"<BugComment(bug={self.bug_id}, author='{self.author}', type='{self.comment_type}')>"
