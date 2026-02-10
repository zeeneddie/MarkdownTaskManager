"""
Plane Export Data Contract - Pydantic models consumed by the Plane importer.

This is the data contract between MarQed and any downstream consumer
(Plane importer, Git PR reviewer, AutoForge).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PlanePriority(str, Enum):
    """Plane-compatible priority levels."""
    urgent = "urgent"
    high = "high"
    medium = "medium"
    low = "low"
    none = "none"


class PlaneStatus(str, Enum):
    """Plane-compatible status values."""
    backlog = "backlog"
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    cancelled = "cancelled"


class RelationType(str, Enum):
    """Dependency relation types."""
    blocked_by = "blocked_by"
    blocks = "blocks"
    relates_to = "relates_to"
    duplicate_of = "duplicate_of"


class ExportSourceReference(BaseModel):
    """Reference to source code location."""
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    code_snippet: Optional[str] = None
    element_type: str = "file"


class ExportAcceptanceCriterion(BaseModel):
    """Acceptance criterion for a story."""
    id: str
    description: str
    test_type: str = "functional"
    source_hint: Optional[str] = None


class ExportRelation(BaseModel):
    """Dependency relation between items."""
    source_id: str
    target_id: str
    relation_type: RelationType
    reason: Optional[str] = None


class ExportStory(BaseModel):
    """Plane-compatible story with full MarQed data preserved."""
    id: str
    title: str
    description: str
    feature_id: str
    story_points: int
    complexity: str
    story_type: str
    priority: PlanePriority = PlanePriority.medium
    status: PlaneStatus = PlaneStatus.backlog

    # Rich content (preserved from M8 - not lost like in _epic_to_dict)
    acceptance_criteria: List[ExportAcceptanceCriterion] = Field(default_factory=list)
    source_references: List[ExportSourceReference] = Field(default_factory=list)
    legacy_functionality: Optional[str] = None
    target_implementation: Optional[str] = None
    business_value: Optional[str] = None

    # Dependencies
    blocked_by: List[str] = Field(default_factory=list)
    relations: List[ExportRelation] = Field(default_factory=list)

    # Metadata from Peter enrichment and estimation
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExportFeature(BaseModel):
    """Plane-compatible feature with stories."""
    id: str
    title: str
    description: str
    epic_id: str
    stories: List[ExportStory] = Field(default_factory=list)
    source_modules: List[str] = Field(default_factory=list)
    estimated_story_points: int = 0
    complexity: str = "medium"
    priority: PlanePriority = PlanePriority.medium
    status: PlaneStatus = PlaneStatus.backlog
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExportEpic(BaseModel):
    """Plane-compatible epic with features."""
    id: str
    title: str
    description: str
    domain_name: str
    features: List[ExportFeature] = Field(default_factory=list)
    source_modules: List[str] = Field(default_factory=list)
    estimated_story_points: int = 0
    estimated_weeks: int = 0
    complexity: str = "medium"
    priority: PlanePriority = PlanePriority.medium
    status: PlaneStatus = PlaneStatus.backlog
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExportProjectSummary(BaseModel):
    """Project metadata and aggregated estimation."""
    project_path: str
    project_name: str = ""

    # Aggregated stats
    total_epics: int = 0
    total_features: int = 0
    total_stories: int = 0
    total_story_points: int = 0

    # M9 estimation data
    estimated_weeks_low: int = 0
    estimated_weeks_high: int = 0
    estimated_weeks_likely: int = 0
    unadjusted_fp: float = 0.0
    adjusted_fp: float = 0.0
    total_effort_person_days: float = 0.0
    recommended_team_size: int = 0

    # Confidence
    estimation_confidence: float = 0.0
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class PlaneExportPackage(BaseModel):
    """
    Top-level export container - the data contract between MarQed and Plane.

    Contains everything needed to create a complete project in Plane:
    epics, features, stories with acceptance criteria, source references,
    dependencies, priorities, and estimation data.
    """
    # Metadata
    version: str = "1.0.0"
    exported_at: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    source: str = "marqed"

    # Content
    project_summary: ExportProjectSummary
    epics: List[ExportEpic] = Field(default_factory=list)
    relations: List[ExportRelation] = Field(default_factory=list)

    # Traceability
    stage_versions: Dict[str, str] = Field(default_factory=dict)
    generation_metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}
