"""
Workflow Checkpoint Database Models

Week 158 - Fase 24.6: Restartable Workflows

Generic checkpoint/resume system for all MarQed workflow types:
- Brown Paper (7 stages)
- Migration (8 stages)
- Green Paper (7 stages)
- Quality (5 stages)
"""

from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field
from app.database import Base


class CheckpointStatus(str, Enum):
    """Checkpoint status constants."""
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowCheckpoint(Base):
    """
    Workflow checkpoint for restartable workflows.

    Stores the complete state of a workflow execution at each stage,
    enabling resume from failure and idempotent stage execution.
    """
    __tablename__ = "workflow_checkpoints"

    id = Column(String(36), primary_key=True)  # UUID as string
    session_id = Column(String(36), nullable=False, index=True)
    workflow_type = Column(String(50), nullable=False)  # brown_paper, migration, green_paper, quality
    workflow_id = Column(String(36), nullable=False, index=True)

    # Progress tracking
    current_stage = Column(String(100), nullable=True)
    completed_stages = Column(JSONB, nullable=False, default=list)
    stage_results = Column(JSONB, nullable=False, default=dict)

    # Context preservation
    shared_data = Column(JSONB, nullable=False, default=dict)
    input_data = Column(JSONB, nullable=False, default=dict)
    checkpoint_metadata = Column("metadata", JSONB, nullable=True)  # "metadata" is reserved in SQLAlchemy

    # Error tracking
    last_error = Column(Text, nullable=True)
    error_stage = Column(String(100), nullable=True)
    error_context = Column(JSONB, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)

    # Versioning & status
    checkpoint_version = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False, default=CheckpointStatus.RUNNING.value, index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=False)
    last_checkpoint_at = Column(DateTime, nullable=True)

    @property
    def can_resume(self) -> bool:
        """Check if checkpoint can be resumed."""
        return self.status in [CheckpointStatus.RUNNING.value, CheckpointStatus.PAUSED.value, CheckpointStatus.FAILED.value]

    @property
    def resume_stage(self) -> Optional[str]:
        """Get the stage to resume from."""
        if self.status == CheckpointStatus.FAILED.value and self.error_stage:
            return self.error_stage
        return self.current_stage

    @property
    def stages_completed_count(self) -> int:
        """Count of completed stages."""
        return len(self.completed_stages) if self.completed_stages else 0

    @property
    def has_error(self) -> bool:
        """Check if checkpoint has an error."""
        return self.last_error is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "workflow_type": self.workflow_type,
            "workflow_id": self.workflow_id,
            "current_stage": self.current_stage,
            "completed_stages": self.completed_stages,
            "stage_results": self.stage_results,
            "shared_data": self.shared_data,
            "input_data": self.input_data,
            "metadata": self.checkpoint_metadata,
            "last_error": self.last_error,
            "error_stage": self.error_stage,
            "error_context": self.error_context,
            "retry_count": self.retry_count,
            "checkpoint_version": self.checkpoint_version,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_checkpoint_at": self.last_checkpoint_at.isoformat() if self.last_checkpoint_at else None,
            "can_resume": self.can_resume,
            "resume_stage": self.resume_stage,
            "stages_completed_count": self.stages_completed_count,
            "has_error": self.has_error,
        }

    def __repr__(self):
        return f"<WorkflowCheckpoint(id={self.id}, workflow={self.workflow_type}, status='{self.status}', stage={self.current_stage})>"


# Pydantic models for API

class CheckpointCreate(BaseModel):
    """Request model for creating a checkpoint."""
    session_id: str
    workflow_type: str
    workflow_id: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None


class CheckpointUpdate(BaseModel):
    """Request model for updating a checkpoint."""
    current_stage: Optional[str] = None
    completed_stages: Optional[List[str]] = None
    stage_results: Optional[Dict[str, Any]] = None
    shared_data: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class CheckpointResponse(BaseModel):
    """Response model for checkpoint data."""
    id: str
    session_id: str
    workflow_type: str
    workflow_id: str
    current_stage: Optional[str]
    completed_stages: List[str]
    stage_results: Dict[str, Any]
    shared_data: Dict[str, Any]
    input_data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]]
    last_error: Optional[str]
    error_stage: Optional[str]
    error_context: Optional[Dict[str, Any]]
    retry_count: int
    checkpoint_version: int
    status: str
    created_at: Optional[str]
    updated_at: Optional[str]
    started_at: Optional[str]
    last_checkpoint_at: Optional[str]
    can_resume: bool
    resume_stage: Optional[str]
    stages_completed_count: int
    has_error: bool

    model_config = {"from_attributes": True}


class CheckpointStatusResponse(BaseModel):
    """Compact status response for workflow status endpoint."""
    workflow_id: str
    workflow_type: str
    status: str
    current_stage: Optional[str]
    stages_completed: int
    can_resume: bool
    resume_stage: Optional[str]
    has_error: bool
    last_error: Optional[str]
    retry_count: int
    started_at: Optional[str]
    last_checkpoint_at: Optional[str]


class ResumeRequest(BaseModel):
    """Request model for resuming a workflow."""
    skip_failed_stage: bool = False
    override_input: Optional[Dict[str, Any]] = None


class ResumeResponse(BaseModel):
    """Response model for resume operation."""
    success: bool
    message: str
    checkpoint_id: str
    resume_from_stage: Optional[str]
    workflow_id: str
