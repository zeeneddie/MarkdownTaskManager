# backend/app/models/causality.py
"""
CiRA Causality Detection Models - Week 123

CiRA (Causality in Requirements Artifacts):
- Causal relation detection in requirements
- Dependency graph building
- Test case generation from cause-effect pairs

Based on: arXiv:2101.10766 - REFSQ 2021
Repository: github.com/fischJan/CiRA
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, DateTime, Float,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


# ============== ENUMS ==============

class CausalSessionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CausalSourceType(str, Enum):
    REQUIREMENTS = "requirements"
    STORIES = "stories"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    FEATURES = "features"
    EPICS = "epics"


class CausalRelationType(str, Enum):
    CAUSES = "CAUSES"           # Story A causes Story B
    ENABLES = "ENABLES"         # Story A enables Story B
    BLOCKS = "BLOCKS"           # Story A blocks Story B
    DEPENDS_ON = "DEPENDS_ON"   # Story A depends on Story B


class ExtractionMethod(str, Enum):
    BERT = "bert"
    RULE_BASED = "rule_based"
    HYBRID = "hybrid"
    LLM = "llm"


class TestCaseType(str, Enum):
    POSITIVE = "positive"       # Test that cause leads to effect
    NEGATIVE = "negative"       # Test that without cause, no effect
    BOUNDARY = "boundary"       # Edge case testing


class TestCaseStatus(str, Enum):
    GENERATED = "generated"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    EXECUTED = "executed"


class TestExecutionResult(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GraphType(str, Enum):
    CAUSAL = "causal"
    DEPENDENCY = "dependency"
    IMPACT = "impact"


class GraphFormat(str, Enum):
    JSON = "json"
    GRAPHML = "graphml"
    DOT = "dot"


# ============== CAUSAL MARKER PATTERNS ==============

CAUSAL_MARKERS = [
    "if", "when", "because", "since", "therefore", "hence", "given",
    "where", "whose", "in order to", "in the case of", "due to",
    "needed", "require", "required", "during", "in case of", "while",
    "thus", "as", "except", "forced by", "only for", "within", "after",
    "whenever", "which", "before", "allows", "allow", "unless",
    "prior to", "as long as", "depending on", "depends on", "result in",
    "increases", "lead to", "thereby", "cause", "in the event",
    "once", "in such cases", "throughout", "improve", "to that end",
    "to this end", "so that", "provided that", "on condition that"
]


# ============== SESSION MODEL ==============

class CausalSession(Base):
    """Causal analysis session - metadata for a causality detection run."""
    __tablename__ = "causal_sessions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(Integer, nullable=True, index=True)
    extraction_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)

    # Session info
    name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default=CausalSessionStatus.PENDING.value)

    # Input source
    source_type = Column(String(50), nullable=False, default=CausalSourceType.REQUIREMENTS.value)
    input_count = Column(Integer, nullable=False, default=0)

    # Analysis settings
    model_name = Column(String(100), nullable=False, default="bert-base-cased")
    confidence_threshold = Column(Float, nullable=False, default=0.6)
    use_pos_tags = Column(Boolean, nullable=False, default=False)
    settings = Column(JSONB, nullable=True)

    # Results summary
    causal_count = Column(Integer, nullable=False, default=0)
    non_causal_count = Column(Integer, nullable=False, default=0)
    relation_count = Column(Integer, nullable=False, default=0)
    avg_confidence = Column(Float, nullable=True)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    classifications = relationship("CausalClassification", back_populates="session", cascade="all, delete-orphan")
    relations = relationship("CausalRelation", back_populates="session", cascade="all, delete-orphan")
    dependency_graphs = relationship("CausalDependencyGraph", back_populates="session", cascade="all, delete-orphan")

    def start_processing(self) -> None:
        """Mark session as processing."""
        self.status = CausalSessionStatus.PROCESSING.value
        self.started_at = datetime.now(timezone.utc)

    def complete(self, causal_count: int, non_causal_count: int, relation_count: int, avg_confidence: float) -> None:
        """Mark session as completed with results."""
        self.status = CausalSessionStatus.COMPLETED.value
        self.completed_at = datetime.now(timezone.utc)
        self.causal_count = causal_count
        self.non_causal_count = non_causal_count
        self.relation_count = relation_count
        self.avg_confidence = avg_confidence
        if self.started_at:
            self.processing_time_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)

    def fail(self, error_message: str) -> None:
        """Mark session as failed."""
        self.status = CausalSessionStatus.FAILED.value
        self.completed_at = datetime.now(timezone.utc)
        self.error_message = error_message

    def is_completed(self) -> bool:
        """Check if session is completed."""
        return self.status == CausalSessionStatus.COMPLETED.value

    def get_causal_percentage(self) -> float:
        """Get percentage of causal sentences."""
        total = self.causal_count + self.non_causal_count
        if total == 0:
            return 0.0
        return (self.causal_count / total) * 100


# ============== CLASSIFICATION MODEL ==============

class CausalClassification(Base):
    """Individual sentence classification result."""
    __tablename__ = "causal_classifications"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("causal_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, nullable=True, index=True)

    # Source reference
    source_id = Column(String(100), nullable=True, index=True)
    source_type = Column(String(50), nullable=True)

    # Input
    sentence = Column(Text, nullable=False)
    sentence_index = Column(Integer, nullable=False, default=0)

    # Classification result
    is_causal = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False)
    probability_causal = Column(Float, nullable=False)
    probability_non_causal = Column(Float, nullable=False)

    # CiRA feature annotations
    is_explicit = Column(Boolean, nullable=True)
    is_marked = Column(Boolean, nullable=True)
    is_single_sentence = Column(Boolean, nullable=True)
    has_single_cause = Column(Boolean, nullable=True)
    has_single_effect = Column(Boolean, nullable=True)
    is_event_chain = Column(Boolean, nullable=True)
    markers = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    session = relationship("CausalSession", back_populates="classifications")
    relations = relationship("CausalRelation", back_populates="classification")

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if classification has high confidence."""
        return self.confidence >= threshold

    def get_detected_markers(self) -> List[str]:
        """Get list of detected causal markers."""
        if not self.markers:
            return []
        return self.markers if isinstance(self.markers, list) else []


# ============== RELATION MODEL ==============

class CausalRelation(Base):
    """Extracted cause-effect relation."""
    __tablename__ = "causal_relations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("causal_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    classification_id = Column(PGUUID(as_uuid=True), ForeignKey("causal_classifications.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id = Column(Integer, nullable=True, index=True)

    # Relation type
    relation_type = Column(String(30), nullable=False)
    confidence = Column(Float, nullable=False)

    # Cause side
    cause_source_id = Column(String(100), nullable=True, index=True)
    cause_text = Column(Text, nullable=False)
    cause_entity = Column(String(200), nullable=True)

    # Effect side
    effect_source_id = Column(String(100), nullable=True, index=True)
    effect_text = Column(Text, nullable=False)
    effect_entity = Column(String(200), nullable=True)

    # Extraction details
    causal_marker = Column(String(50), nullable=True)
    extraction_method = Column(String(50), nullable=False, default=ExtractionMethod.BERT.value)
    relation_metadata = Column(JSONB, nullable=True)

    # Validation
    human_validated = Column(Boolean, nullable=False, default=False)
    human_approved = Column(Boolean, nullable=True)
    validation_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    session = relationship("CausalSession", back_populates="relations")
    classification = relationship("CausalClassification", back_populates="relations")
    test_cases = relationship("CausalTestCase", back_populates="relation", cascade="all, delete-orphan")

    def validate(self, approved: bool, notes: Optional[str] = None) -> None:
        """Human validation of the relation."""
        self.human_validated = True
        self.human_approved = approved
        if notes:
            self.validation_notes = notes

    def is_validated(self) -> bool:
        """Check if relation has been validated."""
        return self.human_validated

    def is_approved(self) -> bool:
        """Check if relation is approved."""
        return self.human_validated and self.human_approved == True

    def get_display_type(self) -> str:
        """Get human-readable relation type."""
        type_display = {
            CausalRelationType.CAUSES.value: "causes",
            CausalRelationType.ENABLES.value: "enables",
            CausalRelationType.BLOCKS.value: "blocks",
            CausalRelationType.DEPENDS_ON.value: "depends on",
        }
        return type_display.get(self.relation_type, self.relation_type.lower())


# ============== DEPENDENCY GRAPH MODEL ==============

class CausalDependencyGraph(Base):
    """Serialized causal dependency graph."""
    __tablename__ = "causal_dependency_graphs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("causal_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, nullable=True, index=True)

    # Graph info
    name = Column(String(200), nullable=True)
    graph_type = Column(String(50), nullable=False, default=GraphType.CAUSAL.value)

    # Graph structure
    nodes = Column(JSONB, nullable=False)
    edges = Column(JSONB, nullable=False)
    node_count = Column(Integer, nullable=False, default=0)
    edge_count = Column(Integer, nullable=False, default=0)

    # Analysis results
    critical_path = Column(JSONB, nullable=True)
    root_nodes = Column(JSONB, nullable=True)
    leaf_nodes = Column(JSONB, nullable=True)
    cycles = Column(JSONB, nullable=True)
    topological_order = Column(JSONB, nullable=True)

    # Sprint planning support
    suggested_sprint_order = Column(JSONB, nullable=True)

    # Serialization
    graph_format = Column(String(30), nullable=False, default=GraphFormat.JSON.value)
    serialized_graph = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    session = relationship("CausalSession", back_populates="dependency_graphs")

    def has_cycles(self) -> bool:
        """Check if graph has cycles."""
        return bool(self.cycles)

    def get_root_count(self) -> int:
        """Get number of root nodes (no dependencies)."""
        return len(self.root_nodes) if self.root_nodes else 0

    def get_leaf_count(self) -> int:
        """Get number of leaf nodes (nothing depends on them)."""
        return len(self.leaf_nodes) if self.leaf_nodes else 0

    def get_critical_path_length(self) -> int:
        """Get length of critical path."""
        return len(self.critical_path) if self.critical_path else 0


# ============== TEST CASE MODEL ==============

class CausalTestCase(Base):
    """Generated test case from cause-effect pair."""
    __tablename__ = "causal_test_cases"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    relation_id = Column(PGUUID(as_uuid=True), ForeignKey("causal_relations.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("causal_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, nullable=True, index=True)

    # Test case info
    test_type = Column(String(50), nullable=False)
    test_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Test content
    preconditions = Column(JSONB, nullable=True)
    trigger = Column(Text, nullable=False)
    expected_result = Column(Text, nullable=False)
    test_steps = Column(JSONB, nullable=True)

    # Priority and tags
    priority = Column(String(20), nullable=False, default=TestPriority.MEDIUM.value)
    tags = Column(JSONB, nullable=True)

    # Status
    status = Column(String(30), nullable=False, default=TestCaseStatus.GENERATED.value)
    execution_result = Column(String(30), nullable=True)
    execution_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    executed_at = Column(DateTime, nullable=True)

    # Relationships
    relation = relationship("CausalRelation", back_populates="test_cases")

    def approve(self) -> None:
        """Approve the test case."""
        self.status = TestCaseStatus.APPROVED.value

    def review(self) -> None:
        """Mark test case as reviewed."""
        self.status = TestCaseStatus.REVIEWED.value

    def execute(self, result: str, notes: Optional[str] = None) -> None:
        """Record test execution result."""
        self.status = TestCaseStatus.EXECUTED.value
        self.execution_result = result
        self.execution_notes = notes
        self.executed_at = datetime.now(timezone.utc)

    def is_passed(self) -> bool:
        """Check if test passed."""
        return self.execution_result == TestExecutionResult.PASSED.value

    def is_pending(self) -> bool:
        """Check if test is pending execution."""
        return self.status in [TestCaseStatus.GENERATED.value, TestCaseStatus.REVIEWED.value, TestCaseStatus.APPROVED.value]


# ============== HELPER FUNCTIONS ==============

def detect_causal_markers(text: str) -> List[str]:
    """Detect causal markers in text."""
    text_lower = text.lower()
    detected = []
    for marker in CAUSAL_MARKERS:
        if f" {marker} " in f" {text_lower} ":
            detected.append(marker)
    return detected


def classify_relation_type(cause_text: str, effect_text: str, marker: Optional[str] = None) -> str:
    """Classify the type of causal relation based on context."""
    text = f"{cause_text} {effect_text}".lower()

    # Check for blocking patterns
    if any(word in text for word in ["block", "prevent", "stop", "prohibit", "cannot"]):
        return CausalRelationType.BLOCKS.value

    # Check for enabling patterns
    if any(word in text for word in ["enable", "allow", "permit", "make possible"]):
        return CausalRelationType.ENABLES.value

    # Check for dependency patterns
    if any(word in text for word in ["depend", "require", "need", "prerequisite"]):
        return CausalRelationType.DEPENDS_ON.value

    # Default to CAUSES
    return CausalRelationType.CAUSES.value
