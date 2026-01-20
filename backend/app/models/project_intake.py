"""
Project Intake Wizard Database Models

Week 145 - Project Intake Wizard

Supports three trajecten:
- Brown Paper: Discovery bestaand systeem → onderhoud of migratie
- Green Paper: Nieuw project vanaf scratch
- Migratie: Transformatie (vereist Brown Paper als voorwaarde)
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.utils.datetime_utils import utc_now
from typing import Optional, Dict, Any, List
from uuid import uuid4
from app.database import Base


# ============================================================
# ENUM CONSTANTS
# ============================================================

class TrajectType:
    """Traject type constants."""
    BROWN_PAPER = "brown_paper"
    GREEN_PAPER = "green_paper"
    MIGRATION = "migration"

    @classmethod
    def all(cls) -> List[str]:
        return [cls.BROWN_PAPER, cls.GREEN_PAPER, cls.MIGRATION]


class MigrationType:
    """Migration type constants."""
    MODERNIZE = "modernize"       # Enkele app moderniseren
    CONSOLIDATE = "consolidate"   # Meerdere apps samenvoegen
    HYBRID = "hybrid"             # Functionaliteit lenen

    @classmethod
    def all(cls) -> List[str]:
        return [cls.MODERNIZE, cls.CONSOLIDATE, cls.HYBRID]


class IntegrationAction:
    """Integration action constants."""
    INCLUDE = "include"   # Meenemen naar target
    LIBRARY = "library"   # Als gedeelde library
    EXCLUDE = "exclude"   # Niet meenemen

    @classmethod
    def all(cls) -> List[str]:
        return [cls.INCLUDE, cls.LIBRARY, cls.EXCLUDE]


class IntakeStatus:
    """Intake status constants."""
    DRAFT = "draft"
    ACTIVE = "active"
    ANALYZING = "analyzing"
    AWAITING_DECISION = "awaiting_decision"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    @classmethod
    def all(cls) -> List[str]:
        return [cls.DRAFT, cls.ACTIVE, cls.ANALYZING, cls.AWAITING_DECISION, cls.COMPLETED, cls.CANCELLED]


class AnalysisTier:
    """Analysis tier constants."""
    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"

    @classmethod
    def all(cls) -> List[str]:
        return [cls.FREE, cls.STANDARD, cls.PREMIUM]


class ExpectedOutcome:
    """Expected outcome constants."""
    INSIGHT_ONLY = "insight_only"
    MAINTENANCE = "maintenance"
    MIGRATION = "migration"
    DUE_DILIGENCE = "due_diligence"

    @classmethod
    def all(cls) -> List[str]:
        return [cls.INSIGHT_ONLY, cls.MAINTENANCE, cls.MIGRATION, cls.DUE_DILIGENCE]


class MigrationStrategy:
    """Migration strategy constants."""
    BIG_BANG = "big_bang"
    MODULE_BY_MODULE = "module_by_module"
    STRANGLER_FIG = "strangler_fig"

    @classmethod
    def all(cls) -> List[str]:
        return [cls.BIG_BANG, cls.MODULE_BY_MODULE, cls.STRANGLER_FIG]


class BrownPaperDecision:
    """Brown paper decision constants."""
    REPORT_ONLY = "report_only"
    MAINTENANCE = "maintenance"
    MIGRATION = "migration"

    @classmethod
    def all(cls) -> List[str]:
        return [cls.REPORT_ONLY, cls.MAINTENANCE, cls.MIGRATION]


class IntakeEventType:
    """Event type constants for audit trail."""
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    SCOPE_CONFIGURED = "scope_configured"
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    DECISION_MADE = "decision_made"
    SOURCES_ADDED = "sources_added"
    INTEGRATIONS_CONFIGURED = "integrations_configured"
    TARGET_CONFIGURED = "target_configured"
    PROJECT_GENERATED = "project_generated"
    MIGRATION_STARTED = "migration_started"
    CANCELLED = "cancelled"


# ============================================================
# MAIN MODEL: ProjectIntake
# ============================================================

class ProjectIntake(Base):
    """
    Main Project Intake table.

    Supports three trajecten:
    - Brown Paper: Discovery bestaand systeem
    - Green Paper: Nieuw project
    - Migration: Transformatie (requires Brown Paper first)
    """
    __tablename__ = "project_intakes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    organization = Column(String(255), nullable=True, index=True)
    contact_person = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # Traject type (required)
    traject_type = Column(
        ENUM('brown_paper', 'green_paper', 'migration', name='traject_type', create_type=False),
        nullable=False,
        index=True
    )

    # Migration specific (NULL for brown/green paper)
    migration_type = Column(
        ENUM('modernize', 'consolidate', 'hybrid', name='migration_type', create_type=False),
        nullable=True
    )

    # Target configuration (for migrations and green paper)
    target_stack = Column(JSONB, nullable=True)  # {backend, frontend, database}
    target_architecture = Column(String(100), nullable=True)

    # Timeline
    start_date = Column(Date, nullable=True)
    target_go_live = Column(Date, nullable=True)
    hard_deadline = Column(Boolean, nullable=False, default=False)

    # Migration strategy
    migration_strategy = Column(
        ENUM('big_bang', 'module_by_module', 'strangler_fig', name='migration_strategy', create_type=False),
        nullable=True
    )
    parallel_run_weeks = Column(Integer, nullable=True)

    # Brown Paper decision (after analysis)
    brown_paper_decision = Column(
        ENUM('report_only', 'maintenance', 'migration', name='brown_paper_decision', create_type=False),
        nullable=True
    )
    decision_date = Column(DateTime, nullable=True)
    decision_by = Column(String(255), nullable=True)
    decision_notes = Column(Text, nullable=True)

    # Link to follow-up migration (if brown paper leads to migration)
    follow_up_migration_id = Column(UUID(as_uuid=True), ForeignKey('project_intakes.id', ondelete='SET NULL'), nullable=True)

    # Status
    status = Column(
        ENUM('draft', 'active', 'analyzing', 'awaiting_decision', 'completed', 'cancelled', name='intake_status', create_type=False),
        nullable=False,
        default=IntakeStatus.DRAFT,
        index=True
    )

    # Generated output references
    generated_project_id = Column(Integer, nullable=True)
    generated_kanban_items = Column(Integer, nullable=True)
    generated_requirements = Column(Integer, nullable=True)

    # Analysis results (for brown paper)
    analysis_results = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=utc_now, index=True)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    completed_at = Column(DateTime, nullable=True)

    # Tracking
    created_by = Column(String(255), nullable=True)
    last_modified_by = Column(String(255), nullable=True)

    # Relationships
    sources = relationship("ProjectIntakeSource", back_populates="intake", cascade="all, delete-orphan")
    integrations = relationship("ProjectIntakeIntegration", back_populates="intake", cascade="all, delete-orphan")
    scope = relationship("ProjectIntakeScope", back_populates="intake", uselist=False, cascade="all, delete-orphan")
    features = relationship("ProjectIntakeFeature", back_populates="intake", cascade="all, delete-orphan")
    events = relationship("ProjectIntakeEvent", back_populates="intake", cascade="all, delete-orphan")

    # Self-referential for follow-up migration
    follow_up_migration = relationship("ProjectIntake", remote_side=[id], foreign_keys=[follow_up_migration_id])

    @property
    def is_brown_paper(self) -> bool:
        return self.traject_type == TrajectType.BROWN_PAPER

    @property
    def is_green_paper(self) -> bool:
        return self.traject_type == TrajectType.GREEN_PAPER

    @property
    def is_migration(self) -> bool:
        return self.traject_type == TrajectType.MIGRATION

    @property
    def can_start_analysis(self) -> bool:
        """Check if Brown Paper analysis can be started."""
        if not self.is_brown_paper:
            return False
        if self.status not in [IntakeStatus.DRAFT, IntakeStatus.ACTIVE]:
            return False
        return self.scope is not None

    @property
    def can_make_decision(self) -> bool:
        """Check if a decision can be made (after analysis)."""
        return self.is_brown_paper and self.status == IntakeStatus.AWAITING_DECISION

    @property
    def can_start_migration(self) -> bool:
        """Check if migration project can be started."""
        if not self.is_migration:
            return False
        if self.status != IntakeStatus.ACTIVE:
            return False
        # Must have at least one source
        return len(self.sources or []) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "name": self.name,
            "organization": self.organization,
            "contact_person": self.contact_person,
            "contact_email": self.contact_email,
            "description": self.description,
            "traject_type": self.traject_type,
            "migration_type": self.migration_type,
            "target_stack": self.target_stack,
            "target_architecture": self.target_architecture,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "target_go_live": self.target_go_live.isoformat() if self.target_go_live else None,
            "hard_deadline": self.hard_deadline,
            "migration_strategy": self.migration_strategy,
            "parallel_run_weeks": self.parallel_run_weeks,
            "brown_paper_decision": self.brown_paper_decision,
            "decision_date": self.decision_date.isoformat() if self.decision_date else None,
            "decision_by": self.decision_by,
            "decision_notes": self.decision_notes,
            "follow_up_migration_id": str(self.follow_up_migration_id) if self.follow_up_migration_id else None,
            "status": self.status,
            "generated_project_id": self.generated_project_id,
            "generated_kanban_items": self.generated_kanban_items,
            "generated_requirements": self.generated_requirements,
            "analysis_results": self.analysis_results,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_by": self.created_by,
            # Computed properties
            "is_brown_paper": self.is_brown_paper,
            "is_green_paper": self.is_green_paper,
            "is_migration": self.is_migration,
            "can_start_analysis": self.can_start_analysis,
            "can_make_decision": self.can_make_decision,
            "can_start_migration": self.can_start_migration,
            # Counts
            "source_count": len(self.sources) if self.sources else 0,
            "integration_count": len(self.integrations) if self.integrations else 0,
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to summary dictionary for list views."""
        return {
            "id": str(self.id),
            "name": self.name,
            "organization": self.organization,
            "traject_type": self.traject_type,
            "migration_type": self.migration_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "source_count": len(self.sources) if self.sources else 0,
        }

    def __repr__(self):
        return f"<ProjectIntake(id={self.id}, name='{self.name}', type='{self.traject_type}', status='{self.status}')>"


# ============================================================
# MODEL: ProjectIntakeSource
# ============================================================

class ProjectIntakeSource(Base):
    """
    Brown Paper sources linked to migrations.

    Each migration can have multiple source systems,
    each linked to a completed Brown Paper session.
    """
    __tablename__ = "project_intake_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    intake_id = Column(UUID(as_uuid=True), ForeignKey('project_intakes.id', ondelete='CASCADE'), nullable=False, index=True)

    # Link to Brown Paper session
    brown_paper_session_id = Column(String(36), ForeignKey('marqed_sessions.id', ondelete='SET NULL'), nullable=True, index=True)

    # System info (denormalized for quick access)
    system_name = Column(String(255), nullable=False, index=True)
    system_path = Column(String(1024), nullable=True)
    repository_url = Column(String(1024), nullable=True)

    # Stats from Brown Paper (cached)
    module_count = Column(Integer, nullable=True)
    loc_count = Column(Integer, nullable=True)
    file_count = Column(Integer, nullable=True)
    quality_score = Column(Integer, nullable=True)  # 0-100
    security_score = Column(Integer, nullable=True)  # 0-100
    tech_stack = Column(String(255), nullable=True)

    # Analysis summary (cached from brown paper)
    analysis_summary = Column(JSONB, nullable=True)

    # Order for display
    display_order = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, nullable=False, default=utc_now)

    # Relationships
    intake = relationship("ProjectIntake", back_populates="sources")
    brown_paper_session = relationship("BMADSession", foreign_keys=[brown_paper_session_id])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "intake_id": str(self.intake_id),
            "brown_paper_session_id": self.brown_paper_session_id,
            "system_name": self.system_name,
            "system_path": self.system_path,
            "repository_url": self.repository_url,
            "module_count": self.module_count,
            "loc_count": self.loc_count,
            "file_count": self.file_count,
            "quality_score": self.quality_score,
            "security_score": self.security_score,
            "tech_stack": self.tech_stack,
            "analysis_summary": self.analysis_summary,
            "display_order": self.display_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<ProjectIntakeSource(id={self.id}, system='{self.system_name}')>"


# ============================================================
# MODEL: ProjectIntakeIntegration
# ============================================================

class ProjectIntakeIntegration(Base):
    """
    Integration decisions for migrations.

    Each integration can be:
    - include: Meenemen naar target
    - library: Als gedeelde library
    - exclude: Niet meenemen
    """
    __tablename__ = "project_intake_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    intake_id = Column(UUID(as_uuid=True), ForeignKey('project_intakes.id', ondelete='CASCADE'), nullable=False, index=True)

    # Integration info
    integration_name = Column(String(255), nullable=False, index=True)
    source_system = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # Decision
    action = Column(
        ENUM('include', 'library', 'exclude', name='integration_action', create_type=False),
        nullable=False,
        default=IntegrationAction.INCLUDE,
        index=True
    )

    # Library configuration (if action = library)
    library_name = Column(String(255), nullable=True)
    library_type = Column(String(50), nullable=True)  # nuget, microservice, shared_db

    # Stats
    file_count = Column(Integer, nullable=True)
    complexity = Column(String(20), nullable=True)  # low, medium, high

    # Notes
    decision_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    intake = relationship("ProjectIntake", back_populates="integrations")

    @property
    def is_library(self) -> bool:
        return self.action == IntegrationAction.LIBRARY

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "intake_id": str(self.intake_id),
            "integration_name": self.integration_name,
            "source_system": self.source_system,
            "description": self.description,
            "action": self.action,
            "library_name": self.library_name,
            "library_type": self.library_type,
            "file_count": self.file_count,
            "complexity": self.complexity,
            "decision_notes": self.decision_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_library": self.is_library,
        }

    def __repr__(self):
        return f"<ProjectIntakeIntegration(id={self.id}, name='{self.integration_name}', action='{self.action}')>"


# ============================================================
# MODEL: ProjectIntakeScope
# ============================================================

class ProjectIntakeScope(Base):
    """
    Brown Paper analysis scope configuration.

    One-to-one relationship with ProjectIntake (only for brown_paper type).
    """
    __tablename__ = "project_intake_scope"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    intake_id = Column(UUID(as_uuid=True), ForeignKey('project_intakes.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    # What to analyze
    analyze_functionality = Column(Boolean, nullable=False, default=True)
    analyze_quality = Column(Boolean, nullable=False, default=True)
    analyze_security = Column(Boolean, nullable=False, default=True)
    analyze_tech_debt = Column(Boolean, nullable=False, default=True)
    analyze_performance = Column(Boolean, nullable=False, default=False)
    analyze_database = Column(Boolean, nullable=False, default=False)
    analyze_integrations = Column(Boolean, nullable=False, default=False)
    analyze_documentation = Column(Boolean, nullable=False, default=False)

    # Analysis tier
    tier = Column(
        ENUM('free', 'standard', 'premium', name='analysis_tier', create_type=False),
        nullable=False,
        default=AnalysisTier.STANDARD
    )

    # Expected outcome
    expected_outcome = Column(
        ENUM('insight_only', 'maintenance', 'migration', 'due_diligence', name='expected_outcome', create_type=False),
        nullable=True
    )

    # System location
    system_path = Column(String(1024), nullable=True)
    repository_url = Column(String(1024), nullable=True)
    branch = Column(String(255), nullable=True, default='main')
    has_local_files = Column(Boolean, nullable=False, default=True)
    has_database_access = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    intake = relationship("ProjectIntake", back_populates="scope")

    @property
    def selected_analyses(self) -> List[str]:
        """Return list of selected analysis types."""
        analyses = []
        if self.analyze_functionality:
            analyses.append("functionality")
        if self.analyze_quality:
            analyses.append("quality")
        if self.analyze_security:
            analyses.append("security")
        if self.analyze_tech_debt:
            analyses.append("tech_debt")
        if self.analyze_performance:
            analyses.append("performance")
        if self.analyze_database:
            analyses.append("database")
        if self.analyze_integrations:
            analyses.append("integrations")
        if self.analyze_documentation:
            analyses.append("documentation")
        return analyses

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "intake_id": str(self.intake_id),
            "analyze_functionality": self.analyze_functionality,
            "analyze_quality": self.analyze_quality,
            "analyze_security": self.analyze_security,
            "analyze_tech_debt": self.analyze_tech_debt,
            "analyze_performance": self.analyze_performance,
            "analyze_database": self.analyze_database,
            "analyze_integrations": self.analyze_integrations,
            "analyze_documentation": self.analyze_documentation,
            "tier": self.tier,
            "expected_outcome": self.expected_outcome,
            "system_path": self.system_path,
            "repository_url": self.repository_url,
            "branch": self.branch,
            "has_local_files": self.has_local_files,
            "has_database_access": self.has_database_access,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "selected_analyses": self.selected_analyses,
        }

    def __repr__(self):
        return f"<ProjectIntakeScope(id={self.id}, tier='{self.tier}')>"


# ============================================================
# MODEL: ProjectIntakeFeature
# ============================================================

class ProjectIntakeFeature(Base):
    """
    Green Paper feature selection.

    Predefined features that can be enabled for new projects.
    """
    __tablename__ = "project_intake_features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    intake_id = Column(UUID(as_uuid=True), ForeignKey('project_intakes.id', ondelete='CASCADE'), nullable=False, index=True)

    # Feature info
    feature_name = Column(String(255), nullable=False, index=True)
    feature_category = Column(String(100), nullable=True)  # core, domain, integration
    enabled = Column(Boolean, nullable=False, default=False, index=True)

    # Configuration
    configuration = Column(JSONB, nullable=True)

    # Display order
    display_order = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, nullable=False, default=utc_now)

    # Relationships
    intake = relationship("ProjectIntake", back_populates="features")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "intake_id": str(self.intake_id),
            "feature_name": self.feature_name,
            "feature_category": self.feature_category,
            "enabled": self.enabled,
            "configuration": self.configuration,
            "display_order": self.display_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<ProjectIntakeFeature(id={self.id}, name='{self.feature_name}', enabled={self.enabled})>"


# ============================================================
# MODEL: ProjectIntakeEvent
# ============================================================

class ProjectIntakeEvent(Base):
    """
    Audit trail for project intake events.

    Tracks all significant events in an intake's lifecycle.
    """
    __tablename__ = "project_intake_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    intake_id = Column(UUID(as_uuid=True), ForeignKey('project_intakes.id', ondelete='CASCADE'), nullable=False, index=True)

    # Event info
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(JSONB, nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=utc_now, index=True)
    created_by = Column(String(255), nullable=True)

    # Relationships
    intake = relationship("ProjectIntake", back_populates="events")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "intake_id": str(self.intake_id),
            "event_type": self.event_type,
            "event_data": self.event_data,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }

    def __repr__(self):
        return f"<ProjectIntakeEvent(id={self.id}, type='{self.event_type}')>"


# ============================================================
# PREDEFINED FEATURES (for Green Paper)
# ============================================================

PREDEFINED_FEATURES = [
    # Core features
    {"name": "authentication", "category": "core", "order": 1},
    {"name": "authorization", "category": "core", "order": 2},
    {"name": "user_management", "category": "core", "order": 3},
    {"name": "audit_logging", "category": "core", "order": 4},

    # Domain features (healthcare)
    {"name": "patient_management", "category": "domain", "order": 10},
    {"name": "epd_dossier", "category": "domain", "order": 11},
    {"name": "calendar_planning", "category": "domain", "order": 12},
    {"name": "billing_claims", "category": "domain", "order": 13},
    {"name": "reporting_bi", "category": "domain", "order": 14},
    {"name": "measurements_clinimetrics", "category": "domain", "order": 15},

    # Generic domain features
    {"name": "workflow_bpm", "category": "domain", "order": 20},
    {"name": "document_management", "category": "domain", "order": 21},
    {"name": "notifications", "category": "domain", "order": 22},
    {"name": "messaging_chat", "category": "domain", "order": 23},

    # Integration features
    {"name": "vecozo", "category": "integration", "order": 30},
    {"name": "digid", "category": "integration", "order": 31},
    {"name": "ideal", "category": "integration", "order": 32},
    {"name": "twinfield", "category": "integration", "order": 33},
    {"name": "office365", "category": "integration", "order": 34},
]
