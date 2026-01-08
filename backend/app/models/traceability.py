# backend/app/models/traceability.py
"""
Week 113: Traceability Models

Links business rules to epic/feature/story hierarchy for:
- Impact analysis: "Which stories are affected if BR-042 changes?"
- Compliance: "Prove all authorization rules are tested"
- Migration: "Which rules must migrate to new system?"

Tables:
- story_business_rules: Story ↔ BusinessRule (many-to-many)
- feature_business_rules: Feature ↔ BusinessRule (many-to-many)
- epic_business_rules: Epic ↔ BusinessRule (many-to-many)
- rule_workflows: CRUD workflow groupings
- rule_workflow_members: Rules in a workflow
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    ForeignKey, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


# =============================================================================
# ENUMS
# =============================================================================

class LinkType(str, Enum):
    """How a business rule relates to a work item."""
    IMPLEMENTS = "implements"   # Story implements this rule
    VALIDATES = "validates"     # Story validates/tests this rule
    TRIGGERS = "triggers"       # Story triggers this rule
    CONTAINS = "contains"       # Feature contains this rule
    GOVERNS = "governs"         # Epic governs this rule
    DEPENDS_ON = "depends_on"   # Work item depends on this rule


class WorkflowType(str, Enum):
    """Types of business rule workflows."""
    CRUD = "CRUD"                     # Create/Read/Update/Delete
    STATE_MACHINE = "STATE_MACHINE"   # State transitions
    APPROVAL = "APPROVAL"             # Approval/rejection flows
    SCHEDULING = "SCHEDULING"         # Date/time scheduling
    NOTIFICATION = "NOTIFICATION"     # Alert/email/SMS
    INTEGRATION = "INTEGRATION"       # External API/service
    VALIDATION = "VALIDATION"         # Input validation
    AUTHORIZATION = "AUTHORIZATION"   # Permission checks


class CRUDOperation(str, Enum):
    """CRUD operations for workflow classification."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    VALIDATE = "validate"
    AUTHORIZE = "authorize"


# =============================================================================
# MODELS
# =============================================================================

class StoryBusinessRule(Base):
    """
    Many-to-many join between User Stories and Business Rules.

    A story can implement multiple business rules.
    A business rule can be implemented by multiple stories.
    """
    __tablename__ = 'story_business_rules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    story_id = Column(UUID(as_uuid=True), ForeignKey('task_stories.id', ondelete='CASCADE'), nullable=False, index=True)
    rule_id = Column(String(20), ForeignKey('business_rules.id', ondelete='CASCADE'), nullable=False, index=True)

    # Link metadata
    link_type = Column(String(30), nullable=False, default=LinkType.IMPLEMENTS.value)
    confidence = Column(Float, nullable=True)  # Auto-link confidence (0.0-1.0)
    linked_by = Column(String(50), nullable=True)  # 'auto', 'peter', 'user_xyz'
    link_reason = Column(Text, nullable=True)  # Why this link was created

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    story = relationship("Story", foreign_keys=[story_id])
    rule = relationship("BusinessRule", foreign_keys=[rule_id])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'story_id': str(self.story_id),
            'rule_id': self.rule_id,
            'link_type': self.link_type,
            'confidence': self.confidence,
            'linked_by': self.linked_by,
            'link_reason': self.link_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class FeatureBusinessRule(Base):
    """
    Many-to-many join between Features and Business Rules.

    For rules that apply at the feature level (cross-story).
    """
    __tablename__ = 'feature_business_rules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    feature_id = Column(UUID(as_uuid=True), ForeignKey('task_features.id', ondelete='CASCADE'), nullable=False, index=True)
    rule_id = Column(String(20), ForeignKey('business_rules.id', ondelete='CASCADE'), nullable=False, index=True)

    link_type = Column(String(30), nullable=False, default=LinkType.CONTAINS.value)
    confidence = Column(Float, nullable=True)
    linked_by = Column(String(50), nullable=True)
    link_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    feature = relationship("Feature", foreign_keys=[feature_id])
    rule = relationship("BusinessRule", foreign_keys=[rule_id])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'feature_id': str(self.feature_id),
            'rule_id': self.rule_id,
            'link_type': self.link_type,
            'confidence': self.confidence,
            'linked_by': self.linked_by,
        }


class EpicBusinessRule(Base):
    """
    Many-to-many join between Epics and Business Rules.

    For architectural/governance rules at the epic level.
    """
    __tablename__ = 'epic_business_rules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    epic_id = Column(UUID(as_uuid=True), ForeignKey('task_epics.id', ondelete='CASCADE'), nullable=False, index=True)
    rule_id = Column(String(20), ForeignKey('business_rules.id', ondelete='CASCADE'), nullable=False, index=True)

    link_type = Column(String(30), nullable=False, default=LinkType.GOVERNS.value)
    confidence = Column(Float, nullable=True)
    linked_by = Column(String(50), nullable=True)
    link_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    epic = relationship("Epic", foreign_keys=[epic_id])
    rule = relationship("BusinessRule", foreign_keys=[rule_id])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'epic_id': str(self.epic_id),
            'rule_id': self.rule_id,
            'link_type': self.link_type,
            'confidence': self.confidence,
            'linked_by': self.linked_by,
        }


class RuleWorkflow(Base):
    """
    CRUD Workflow grouping of business rules.

    Groups related rules like "Afspraak CRUD" containing:
    - BR-001: Create afspraak authorization
    - BR-015: Read afspraak scheduling
    - BR-042: Update afspraak data_access
    - BR-099: Delete afspraak validation
    """
    __tablename__ = 'rule_workflows'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)

    # Workflow identification
    name = Column(String(200), nullable=False)  # "Afspraak CRUD", "User Authentication"
    workflow_type = Column(String(50), nullable=False, default=WorkflowType.CRUD.value, index=True)
    entity_name = Column(String(100), nullable=True)  # Primary entity: "Afspraak", "User"
    description = Column(Text, nullable=True)

    # Statistics
    rule_count = Column(Integer, default=0)

    # Operations breakdown (JSONB for flexibility)
    # {"create": ["BR-001", "BR-005"], "read": ["BR-002"], "update": ["BR-003"], "delete": ["BR-004"]}
    operations = Column(JSONB, nullable=True)

    # Auto-generated Mermaid diagram for visualization
    mermaid_diagram = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    members = relationship("RuleWorkflowMember", back_populates="workflow", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'workflow_type': self.workflow_type,
            'entity_name': self.entity_name,
            'description': self.description,
            'rule_count': self.rule_count,
            'operations': self.operations,
            'mermaid_diagram': self.mermaid_diagram,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def generate_mermaid(self) -> str:
        """Generate Mermaid flowchart for this workflow."""
        if self.workflow_type == WorkflowType.CRUD.value and self.operations:
            lines = ["flowchart LR"]
            ops = self.operations

            # Define nodes for each operation
            if ops.get('create'):
                lines.append(f"    CREATE[Create {self.entity_name}]")
            if ops.get('read'):
                lines.append(f"    READ[Read {self.entity_name}]")
            if ops.get('update'):
                lines.append(f"    UPDATE[Update {self.entity_name}]")
            if ops.get('delete'):
                lines.append(f"    DELETE[Delete {self.entity_name}]")

            # Add validation if present
            if ops.get('validate'):
                lines.append(f"    VALIDATE{{Validate}}")
                for op in ['create', 'update']:
                    if ops.get(op):
                        lines.append(f"    {op.upper()} --> VALIDATE")

            return "\n".join(lines)
        return ""


class RuleWorkflowMember(Base):
    """
    Membership of a business rule in a workflow.

    Tracks which rules belong to which workflows and their role.
    """
    __tablename__ = 'rule_workflow_members'

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(Integer, ForeignKey('rule_workflows.id', ondelete='CASCADE'), nullable=False, index=True)
    rule_id = Column(String(20), ForeignKey('business_rules.id', ondelete='CASCADE'), nullable=False, index=True)

    # Role in the workflow
    operation = Column(String(30), nullable=True)  # create, read, update, delete, validate, authorize
    sequence_order = Column(Integer, nullable=True)  # Order within the workflow

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    workflow = relationship("RuleWorkflow", back_populates="members")
    rule = relationship("BusinessRule", foreign_keys=[rule_id])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'rule_id': self.rule_id,
            'operation': self.operation,
            'sequence_order': self.sequence_order,
        }


# =============================================================================
# HELPER DATACLASSES (not ORM models)
# =============================================================================

from dataclasses import dataclass, field


@dataclass
class TraceabilityMatrixRow:
    """Single row in the traceability matrix."""
    epic_id: Optional[str] = None
    epic_title: Optional[str] = None
    feature_id: Optional[str] = None
    feature_title: Optional[str] = None
    story_id: Optional[str] = None
    story_title: Optional[str] = None
    rule_id: Optional[str] = None
    rule_type: Optional[str] = None
    rule_description: Optional[str] = None
    rule_confidence: Optional[float] = None
    link_type: Optional[str] = None
    linked_by: Optional[str] = None


@dataclass
class RuleImpact:
    """Impact analysis for a single business rule."""
    rule_id: str
    rule_type: str
    rule_description: str
    source_file: Optional[str] = None
    entity_name: Optional[str] = None
    story_count: int = 0
    feature_count: int = 0
    epic_count: int = 0
    affected_stories: List[str] = field(default_factory=list)
    affected_features: List[str] = field(default_factory=list)
    affected_epics: List[str] = field(default_factory=list)


@dataclass
class TraceabilitySummary:
    """Summary statistics for traceability."""
    total_rules: int = 0
    linked_rules: int = 0
    unlinked_rules: int = 0
    total_stories: int = 0
    stories_with_rules: int = 0
    stories_without_rules: int = 0
    avg_rules_per_story: float = 0.0
    workflows_detected: int = 0
    coverage_percentage: float = 0.0  # % of rules linked to stories
