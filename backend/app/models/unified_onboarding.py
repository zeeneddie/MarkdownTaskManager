"""
Unified Onboarding Database Models

4e Brown Paper workflow that orchestrates the 3 existing workflows
and adds a Reconciliation step to compare bottom-up vs top-down vs enhanced results.

The reconciled epics/features/stories are stored in the existing brown_paper_epics table
so the dashboard works without changes.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime
import uuid
from app.database import Base


class UnifiedOnboardingSession(Base):
    """
    Unified Onboarding session tracking for the 4th workflow.
    Links MarQed (top-down) and BrownPaper (bottom-up) sessions,
    orchestrates all 8 steps, and stores reconciliation results.
    """
    __tablename__ = "unified_onboarding_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Links to existing sessions
    marqed_session_id = Column(String(36), ForeignKey("marqed_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    brown_paper_session_id = Column(UUID(as_uuid=True), ForeignKey("brown_paper_sessions.id", ondelete="SET NULL"), nullable=True)

    # Project info
    project_name = Column(String(255), nullable=False)
    project_path = Column(String(1024), nullable=True)

    # Status tracking
    # initialized, step_1_running, step_1_done, ..., step_8_running, step_8_done, completed, failed, cancelled
    status = Column(String(30), default="initialized", nullable=False, index=True)
    current_step = Column(Integer, default=0)

    # Step results (JSONB per step)
    step_1_result = Column(JSONB, nullable=True)  # Code scan: modules, patterns, domains
    step_2_result = Column(JSONB, nullable=True)  # 8 vragen validatie
    step_3_result = Column(JSONB, nullable=True)  # Miguel's analyse (verrijkt)
    step_4_result = Column(JSONB, nullable=True)  # Peter's specificatie
    step_5_result = Column(JSONB, nullable=True)  # Felix bottom-up epics
    step_6_result = Column(JSONB, nullable=True)  # Felix top-down epics
    step_7_result = Column(JSONB, nullable=True)  # Enhanced 6-fase resultaten
    step_8_result = Column(JSONB, nullable=True)  # Reconciliation resultaten (alle 7 rapporten)

    # Final output references
    unified_constitution_id = Column(UUID(as_uuid=True), ForeignKey("brown_paper_constitutions.id", ondelete="SET NULL"), nullable=True)

    # Timing
    step_timings = Column(JSONB, default={})  # {"step_1_ms": 5000, "step_2_ms": 100, ...}
    total_duration_ms = Column(Integer, nullable=True)

    # Meta
    tier = Column(String(20), default="ENTERPRISE")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<UnifiedOnboardingSession(id={self.id}, project={self.project_name}, status='{self.status}', step={self.current_step})>"
