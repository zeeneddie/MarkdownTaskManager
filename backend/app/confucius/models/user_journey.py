"""
User Journey Data Models.

Models for extracting and representing end-user workflows, personas,
and screen flows from legacy code or new specifications.

Used by:
- Brown Paper workflow (bottom-up extraction)
- Migration workflow (enrichment with 8 questions)
- Green Paper workflow (top-down definition)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class PersonaType(Enum):
    """Type of end-user."""

    CUSTOMER = "customer"           # External customer
    EMPLOYEE = "employee"           # Internal employee
    ADMINISTRATOR = "administrator"  # System administrator
    PARTNER = "partner"             # External partner
    GUEST = "guest"                 # Unauthenticated user
    SYSTEM = "system"               # Automated process


class JourneyComplexity(Enum):
    """Complexity level of a user journey."""

    SIMPLE = "simple"       # 1-3 steps, no decisions
    MODERATE = "moderate"   # 4-7 steps, some decisions
    COMPLEX = "complex"     # 8+ steps, multiple paths
    CRITICAL = "critical"   # Business-critical, high impact


class InteractionType(Enum):
    """Type of interaction in a journey step."""

    VIEW = "view"           # View only
    INPUT = "input"         # Data entry
    SELECT = "select"       # Make a choice
    CONFIRM = "confirm"     # Confirm action
    UPLOAD = "upload"       # Upload file
    DOWNLOAD = "download"   # Download file
    NAVIGATE = "navigate"   # Navigate
    SEARCH = "search"       # Search
    AUTHENTICATE = "authenticate"  # Login/verification


@dataclass
class Persona:
    """
    Represents a type of end-user of the system.

    Extracted from:
    - Authorization/role checks in code
    - Login/session management
    - UI components per role
    - User tables in database
    """

    id: str
    name: str                           # "Particuliere Klant"
    type: PersonaType
    role_code: str                      # "CUSTOMER", "ADMIN"

    # Characteristics
    goals: List[str] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)
    technical_proficiency: str = "medium"  # low, medium, high
    usage_frequency: str = "daily"         # daily, weekly, monthly, rarely

    # Extracted from code
    permissions: List[str] = field(default_factory=list)
    accessible_screens: List[str] = field(default_factory=list)
    accessible_features: List[str] = field(default_factory=list)

    # Source tracking
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0  # 0.0-1.0, how certain we are

    # Enrichment (from Migration 8 questions)
    stakeholder_notes: Optional[str] = None
    business_impact: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "role_code": self.role_code,
            "goals": self.goals,
            "pain_points": self.pain_points,
            "technical_proficiency": self.technical_proficiency,
            "usage_frequency": self.usage_frequency,
            "permissions": self.permissions,
            "accessible_screens": self.accessible_screens,
            "accessible_features": self.accessible_features,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "stakeholder_notes": self.stakeholder_notes,
            "business_impact": self.business_impact,
        }


@dataclass
class ScreenInfo:
    """
    Information about a screen/page in the application.

    Extracted from:
    - ASPX/HTML/Razor files
    - React/Vue/Angular components
    - Windows Forms/WPF
    """

    id: str
    name: str                           # "CustomerDashboard"
    display_name: str                   # "Klant Overzicht"
    file_path: str                      # "/Views/Customer/Dashboard.aspx"

    # Screen characteristics
    screen_type: str = "form"           # "form", "list", "dashboard", "wizard"
    requires_auth: bool = True
    allowed_roles: List[str] = field(default_factory=list)

    # UI elements
    forms: List[Dict[str, Any]] = field(default_factory=list)
    buttons: List[Dict[str, Any]] = field(default_factory=list)
    data_displays: List[Dict[str, Any]] = field(default_factory=list)
    navigation_links: List[str] = field(default_factory=list)

    # Data interactions
    data_sources: List[str] = field(default_factory=list)  # API calls, DB queries
    input_fields: List[Dict[str, Any]] = field(default_factory=list)
    validations: List[str] = field(default_factory=list)

    # Evidence
    evidence: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "file_path": self.file_path,
            "screen_type": self.screen_type,
            "requires_auth": self.requires_auth,
            "allowed_roles": self.allowed_roles,
            "forms": self.forms,
            "buttons": self.buttons,
            "data_displays": self.data_displays,
            "navigation_links": self.navigation_links,
            "data_sources": self.data_sources,
            "input_fields": self.input_fields,
            "validations": self.validations,
            "evidence": self.evidence,
        }


@dataclass
class JourneyStep:
    """
    One step in a user journey.
    """

    id: str
    sequence: int                       # Order in journey

    # Action
    action: str                         # "Vul klantgegevens in"
    interaction_type: InteractionType
    actor: str                          # Persona ID or "system"

    # Screen
    screen_id: str
    screen_name: str

    # System behavior
    system_action: Optional[str] = None     # "Valideer BSN bij RDW"
    api_calls: List[str] = field(default_factory=list)
    database_operations: List[str] = field(default_factory=list)

    # Validations & business rules
    validations: List[str] = field(default_factory=list)
    business_rules: List[str] = field(default_factory=list)

    # Flow control
    next_steps: List[str] = field(default_factory=list)  # Step IDs
    conditions: Dict[str, str] = field(default_factory=dict)  # condition -> next_step

    # Timing
    estimated_duration_seconds: int = 30

    # Evidence from code
    code_references: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "sequence": self.sequence,
            "action": self.action,
            "interaction_type": self.interaction_type.value,
            "actor": self.actor,
            "screen_id": self.screen_id,
            "screen_name": self.screen_name,
            "system_action": self.system_action,
            "api_calls": self.api_calls,
            "database_operations": self.database_operations,
            "validations": self.validations,
            "business_rules": self.business_rules,
            "next_steps": self.next_steps,
            "conditions": self.conditions,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "code_references": self.code_references,
        }


@dataclass
class ErrorPath:
    """
    Alternative path on error or exception.
    """

    id: str
    trigger_step_id: str                # Where error occurs
    trigger_condition: str              # "Onvoldoende saldo"

    # Error handling
    error_type: str                     # "validation", "business_rule", "system"
    error_screen_id: Optional[str] = None
    error_message: str = ""

    # Recovery
    recovery_options: List[str] = field(default_factory=list)
    can_retry: bool = True

    # Impact
    data_rollback_required: bool = False
    notification_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "trigger_step_id": self.trigger_step_id,
            "trigger_condition": self.trigger_condition,
            "error_type": self.error_type,
            "error_screen_id": self.error_screen_id,
            "error_message": self.error_message,
            "recovery_options": self.recovery_options,
            "can_retry": self.can_retry,
            "data_rollback_required": self.data_rollback_required,
            "notification_required": self.notification_required,
        }


@dataclass
class UserJourney:
    """
    Complete user journey from trigger to completion.

    A journey describes how a persona completes a specific
    task in the system.
    """

    id: str
    name: str                           # "Nieuwe rekening openen"
    description: str

    # Persona
    persona_id: str
    persona_name: str

    # Journey metadata
    complexity: JourneyComplexity
    business_value: str = "medium"      # "high", "medium", "low"
    frequency: str = "unknown"          # "100x/day", "10x/week"

    # Trigger
    trigger: str = ""                   # "Klant vraagt nieuwe rekening aan"
    trigger_type: str = "user_initiated"  # "user_initiated", "scheduled", "event"
    preconditions: List[str] = field(default_factory=list)

    # Steps
    steps: List[JourneyStep] = field(default_factory=list)
    happy_path: List[str] = field(default_factory=list)  # Step IDs

    # Alternative paths
    error_paths: List[ErrorPath] = field(default_factory=list)
    alternative_paths: List[Dict[str, Any]] = field(default_factory=list)

    # Screens involved
    screens_involved: List[str] = field(default_factory=list)

    # Completion
    success_criteria: List[str] = field(default_factory=list)
    outcome: str = ""                   # "Rekening is aangemaakt en actief"

    # Timing
    estimated_duration_minutes: int = 5
    sla_minutes: Optional[int] = None

    # Dependencies
    required_integrations: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)

    # Migration enrichment
    migration_priority: Optional[str] = None  # "must_have", "should_have", "nice_to_have"
    migration_notes: Optional[str] = None
    target_improvements: List[str] = field(default_factory=list)

    # Evidence
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "persona_id": self.persona_id,
            "persona_name": self.persona_name,
            "complexity": self.complexity.value,
            "business_value": self.business_value,
            "frequency": self.frequency,
            "trigger": self.trigger,
            "trigger_type": self.trigger_type,
            "preconditions": self.preconditions,
            "steps": [s.to_dict() for s in self.steps],
            "happy_path": self.happy_path,
            "error_paths": [e.to_dict() for e in self.error_paths],
            "alternative_paths": self.alternative_paths,
            "screens_involved": self.screens_involved,
            "success_criteria": self.success_criteria,
            "outcome": self.outcome,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "sla_minutes": self.sla_minutes,
            "required_integrations": self.required_integrations,
            "required_permissions": self.required_permissions,
            "migration_priority": self.migration_priority,
            "migration_notes": self.migration_notes,
            "target_improvements": self.target_improvements,
            "evidence": self.evidence,
            "confidence": self.confidence,
        }


@dataclass
class ScreenFlow:
    """
    Navigation flow between screens.
    """

    id: str
    name: str                           # "Onboarding Flow"

    # Screens in flow
    screens: List[str] = field(default_factory=list)  # Screen IDs in order
    transitions: List[Dict[str, Any]] = field(default_factory=list)

    # Flow type
    flow_type: str = "linear"           # "linear", "wizard", "branching"
    entry_points: List[str] = field(default_factory=list)
    exit_points: List[str] = field(default_factory=list)

    # Personas who use this flow
    personas: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "screens": self.screens,
            "transitions": self.transitions,
            "flow_type": self.flow_type,
            "entry_points": self.entry_points,
            "exit_points": self.exit_points,
            "personas": self.personas,
        }


@dataclass
class RolePermissionMatrix:
    """
    Matrix of roles and their permissions.
    """

    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    matrix: Dict[str, List[str]] = field(default_factory=dict)  # role -> [permissions]

    # Screen access
    screen_access: Dict[str, List[str]] = field(default_factory=dict)  # role -> [screens]

    # Feature access
    feature_access: Dict[str, List[str]] = field(default_factory=dict)  # role -> [features]

    # Evidence
    evidence: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "roles": self.roles,
            "permissions": self.permissions,
            "matrix": self.matrix,
            "screen_access": self.screen_access,
            "feature_access": self.feature_access,
            "evidence": self.evidence,
        }


@dataclass
class UserJourneyExtractionResult:
    """
    Complete result of user journey extraction.
    """

    # Extracted data
    personas: List[Persona] = field(default_factory=list)
    journeys: List[UserJourney] = field(default_factory=list)
    screens: List[ScreenInfo] = field(default_factory=list)
    screen_flows: List[ScreenFlow] = field(default_factory=list)
    role_matrix: Optional[RolePermissionMatrix] = None

    # Statistics
    total_personas: int = 0
    total_journeys: int = 0
    total_screens: int = 0
    total_steps: int = 0

    # Quality metrics
    extraction_confidence: float = 0.0
    coverage_percentage: float = 0.0  # % of code covered

    # Warnings
    warnings: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)  # Missing information

    # Metadata
    extracted_at: datetime = field(default_factory=datetime.now)
    source_type: str = "code"  # "code", "documentation", "hybrid"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "personas": [p.to_dict() for p in self.personas],
            "journeys": [j.to_dict() for j in self.journeys],
            "screens": [s.to_dict() for s in self.screens],
            "screen_flows": [f.to_dict() for f in self.screen_flows],
            "role_matrix": self.role_matrix.to_dict() if self.role_matrix else None,
            "total_personas": self.total_personas,
            "total_journeys": self.total_journeys,
            "total_screens": self.total_screens,
            "total_steps": self.total_steps,
            "extraction_confidence": self.extraction_confidence,
            "coverage_percentage": self.coverage_percentage,
            "warnings": self.warnings,
            "gaps": self.gaps,
            "extracted_at": self.extracted_at.isoformat(),
            "source_type": self.source_type,
        }
