# User Journey Extraction Stage - Ontwerp Document

> Ontwerp datum: 2026-01-19
> Status: GEÏMPLEMENTEERD (2026-01-19)
> Auteur: Claude

## 1. Doel

Extraheer end-user workflows, personas en screen flows uit legacy code (Brown Paper) of definieer ze voor nieuwe projecten (Green Paper), met enrichment mogelijkheid voor Migration workflow.

---

## 2. Data Models

### 2.1 Core Models

```python
# backend/app/confucius/models/user_journey.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class PersonaType(Enum):
    """Type eindgebruiker."""
    CUSTOMER = "customer"           # Externe klant
    EMPLOYEE = "employee"           # Interne medewerker
    ADMINISTRATOR = "administrator" # Systeembeheerder
    PARTNER = "partner"             # Externe partner
    GUEST = "guest"                 # Niet-geauthenticeerd
    SYSTEM = "system"               # Geautomatiseerd proces


class JourneyComplexity(Enum):
    """Complexiteit van een user journey."""
    SIMPLE = "simple"       # 1-3 stappen, geen beslissingen
    MODERATE = "moderate"   # 4-7 stappen, enkele beslissingen
    COMPLEX = "complex"     # 8+ stappen, meerdere paden
    CRITICAL = "critical"   # Business-kritisch, hoge impact


class InteractionType(Enum):
    """Type interactie in een journey step."""
    VIEW = "view"           # Alleen bekijken
    INPUT = "input"         # Data invoeren
    SELECT = "select"       # Keuze maken
    CONFIRM = "confirm"     # Bevestigen
    UPLOAD = "upload"       # Bestand uploaden
    DOWNLOAD = "download"   # Bestand downloaden
    NAVIGATE = "navigate"   # Navigeren
    SEARCH = "search"       # Zoeken
    AUTHENTICATE = "authenticate"  # Inloggen/verificatie


@dataclass
class Persona:
    """
    Representeert een type eindgebruiker van het systeem.

    Geëxtraheerd uit:
    - Authorization/role checks in code
    - Login/session management
    - UI componenten per role
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
    confidence: float = 0.0  # 0.0-1.0, hoe zeker zijn we

    # Enrichment (from Migration 8 questions)
    stakeholder_notes: Optional[str] = None
    business_impact: Optional[str] = None


@dataclass
class ScreenInfo:
    """
    Informatie over een scherm/pagina in de applicatie.

    Geëxtraheerd uit:
    - ASPX/HTML/Razor files
    - React/Vue/Angular components
    - Windows Forms/WPF
    """
    id: str
    name: str                           # "CustomerDashboard"
    display_name: str                   # "Klant Overzicht"
    file_path: str                      # "/Views/Customer/Dashboard.aspx"

    # Screen characteristics
    screen_type: str                    # "form", "list", "dashboard", "wizard"
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


@dataclass
class JourneyStep:
    """
    Eén stap in een user journey.
    """
    id: str
    sequence: int                       # Volgorde in journey

    # Action
    action: str                         # "Vul klantgegevens in"
    interaction_type: InteractionType
    actor: str                          # Persona ID of "system"

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


@dataclass
class ErrorPath:
    """
    Alternatief pad bij fout of uitzondering.
    """
    id: str
    trigger_step_id: str                # Waar treedt de fout op
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


@dataclass
class UserJourney:
    """
    Complete user journey van trigger tot completion.

    Een journey beschrijft hoe een persona een specifieke
    taak voltooit in het systeem.
    """
    id: str
    name: str                           # "Nieuwe rekening openen"
    description: str

    # Persona
    persona_id: str
    persona_name: str

    # Journey metadata
    complexity: JourneyComplexity
    business_value: str                 # "high", "medium", "low"
    frequency: str                      # "100x/day", "10x/week"

    # Trigger
    trigger: str                        # "Klant vraagt nieuwe rekening aan"
    trigger_type: str                   # "user_initiated", "scheduled", "event"
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


@dataclass
class ScreenFlow:
    """
    Navigatie flow tussen schermen.
    """
    id: str
    name: str                           # "Onboarding Flow"

    # Screens in flow
    screens: List[str] = field(default_factory=list)  # Screen IDs in volgorde
    transitions: List[Dict[str, Any]] = field(default_factory=list)

    # Flow type
    flow_type: str = "linear"           # "linear", "wizard", "branching"
    entry_points: List[str] = field(default_factory=list)
    exit_points: List[str] = field(default_factory=list)

    # Personas who use this flow
    personas: List[str] = field(default_factory=list)


@dataclass
class RolePermissionMatrix:
    """
    Matrix van rollen en hun permissions.
    """
    roles: List[str]
    permissions: List[str]
    matrix: Dict[str, List[str]]  # role -> [permissions]

    # Screen access
    screen_access: Dict[str, List[str]]  # role -> [screens]

    # Feature access
    feature_access: Dict[str, List[str]]  # role -> [features]

    # Evidence
    evidence: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class UserJourneyExtractionResult:
    """
    Complete resultaat van user journey extraction.
    """
    # Extracted data
    personas: List[Persona]
    journeys: List[UserJourney]
    screens: List[ScreenInfo]
    screen_flows: List[ScreenFlow]
    role_matrix: RolePermissionMatrix

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
    gaps: List[str] = field(default_factory=list)  # Ontbrekende informatie

    # Metadata
    extracted_at: datetime = field(default_factory=datetime.now)
    source_type: str = "code"  # "code", "documentation", "hybrid"
```

---

## 3. Stage Implementatie

### 3.1 User Journey Extraction Stage

```python
# backend/app/confucius/stages/user_journey_extraction.py

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

from ..models.user_journey import (
    Persona, PersonaType, UserJourney, JourneyStep,
    ScreenInfo, ScreenFlow, ErrorPath, JourneyComplexity,
    InteractionType, RolePermissionMatrix, UserJourneyExtractionResult
)
from ..workflows.base import WorkflowContext, StageResult, WorkflowStatus

logger = logging.getLogger(__name__)


class UserJourneyExtractionStage:
    """
    Stage voor het extraheren van user journeys uit code of specificaties.

    Extraction Sources:
    1. UI Components (ASPX, Razor, React, etc.)
    2. Authorization/Role checks
    3. Navigation/Routing
    4. Form handlers & validators
    5. Database user/role tables
    6. API endpoints

    Agents:
    - Vicky: UI/UX analyse, screen flows
    - Peter: Business journeys, persona goals

    Gebruikt door:
    - Brown Paper (bottom-up extraction)
    - Migration (enrichment met 8 vragen)
    - Green Paper (top-down definition)
    """

    def __init__(self):
        self.extractors = []
        self._init_extractors()

    def _init_extractors(self):
        """Initialize tech-stack specific extractors."""
        from .extractors import (
            AspNetExtractor,
            AspClassicExtractor,
            ReactExtractor,
            AngularExtractor,
            WinFormsExtractor,
            DatabaseRoleExtractor,
        )

        self.extractors = [
            AspNetExtractor(),
            AspClassicExtractor(),
            ReactExtractor(),
            AngularExtractor(),
            WinFormsExtractor(),
            DatabaseRoleExtractor(),
        ]

    async def execute(
        self,
        context: WorkflowContext,
        enrichment: Optional[Dict[str, Any]] = None,
    ) -> StageResult:
        """
        Execute user journey extraction.

        Args:
            context: Workflow context met code_analysis en domain data
            enrichment: Optional enrichment data (Migration 8 vragen)

        Returns:
            StageResult met UserJourneyExtractionResult
        """
        started_at = datetime.now(timezone.utc)

        try:
            # Get input data
            code_analysis = context.shared_data.get("code_understanding_result", {})
            domains = context.shared_data.get("domain_extraction_result", {})
            tech_stack = context.shared_data.get("tech_stack", [])

            # Step 1: Extract raw data from code
            raw_extraction = await self._extract_from_code(
                code_analysis, tech_stack
            )

            # Step 2: Use Vicky for UI/UX analysis
            vicky_result = await self._analyze_with_vicky(
                raw_extraction, context
            )

            # Step 3: Use Peter for business journey definition
            peter_result = await self._define_with_peter(
                raw_extraction, vicky_result, domains, context
            )

            # Step 4: Apply enrichment (Migration)
            if enrichment:
                peter_result = self._apply_enrichment(peter_result, enrichment)

            # Step 5: Build final result
            result = self._build_result(
                raw_extraction, vicky_result, peter_result
            )

            # Store in context
            context.shared_data["user_journey_extraction_result"] = result

            return StageResult(
                stage_name="user_journey_extraction",
                status=WorkflowStatus.COMPLETED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                agent_results={
                    "raw_extraction": raw_extraction,
                    "vicky_analysis": vicky_result,
                    "peter_journeys": peter_result,
                    "final_result": result.__dict__,
                },
                quality_score=result.extraction_confidence,
                passed_quality_gate=result.extraction_confidence >= 0.7,
            )

        except Exception as e:
            logger.error(f"User journey extraction failed: {e}")
            return StageResult(
                stage_name="user_journey_extraction",
                status=WorkflowStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                error=str(e),
            )

    async def _extract_from_code(
        self,
        code_analysis: Dict[str, Any],
        tech_stack: List[str],
    ) -> Dict[str, Any]:
        """
        Extract raw user journey data from code analysis.

        Analyseert:
        - Authorization attributes/decorators
        - UI component structure
        - Form handlers
        - Navigation/routing
        - Session management
        """
        raw_data = {
            "roles": [],
            "screens": [],
            "forms": [],
            "navigation": [],
            "auth_checks": [],
            "api_endpoints": [],
            "event_handlers": [],
        }

        files = code_analysis.get("files", [])

        for extractor in self.extractors:
            if extractor.supports_stack(tech_stack):
                extracted = await extractor.extract(files, code_analysis)

                # Merge results
                for key in raw_data:
                    if key in extracted:
                        raw_data[key].extend(extracted[key])

        # Deduplicate
        for key in raw_data:
            if isinstance(raw_data[key], list):
                raw_data[key] = self._deduplicate(raw_data[key])

        return raw_data

    async def _analyze_with_vicky(
        self,
        raw_extraction: Dict[str, Any],
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """
        Vicky analyseert UI/UX patterns en screen flows.
        """
        from ..extensions import WorkflowRouter

        router = context.router or WorkflowRouter()
        extensions = await router.get_extensions_for_agents(["Vicky"])

        result = {
            "personas_from_ui": [],
            "screen_flows": [],
            "ux_patterns": [],
            "accessibility_notes": [],
        }

        vicky = extensions[0] if extensions else None
        if vicky:
            vicky_result = await vicky.run_full_lifecycle(
                task="Analyze UI patterns and extract user personas and screen flows",
                context={
                    "screens": raw_extraction.get("screens", []),
                    "forms": raw_extraction.get("forms", []),
                    "navigation": raw_extraction.get("navigation", []),
                    "roles": raw_extraction.get("roles", []),
                    "vicky_activity": "journey_mapping",
                    "tier": "PROFESSIONAL",
                },
                entry_id=f"{context.workflow_id}-vicky-journey",
            )

            if vicky_result.success:
                result["personas_from_ui"] = vicky_result.output.get("personas", [])
                result["screen_flows"] = vicky_result.output.get("screen_flows", [])
                result["ux_patterns"] = vicky_result.output.get("patterns", [])

        return result

    async def _define_with_peter(
        self,
        raw_extraction: Dict[str, Any],
        vicky_result: Dict[str, Any],
        domains: Dict[str, Any],
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """
        Peter definieert business journeys per persona.
        """
        from ..extensions import WorkflowRouter

        router = context.router or WorkflowRouter()
        extensions = await router.get_extensions_for_agents(["Peter"])

        result = {
            "personas": [],
            "journeys": [],
            "business_processes": [],
        }

        peter = extensions[0] if extensions else None
        if peter:
            peter_result = await peter.run_full_lifecycle(
                task="Define user journeys for each persona based on domains and UI analysis",
                context={
                    "domains": domains.get("domains", []),
                    "business_capabilities": domains.get("business_capabilities", []),
                    "personas_from_ui": vicky_result.get("personas_from_ui", []),
                    "screen_flows": vicky_result.get("screen_flows", []),
                    "roles": raw_extraction.get("roles", []),
                    "api_endpoints": raw_extraction.get("api_endpoints", []),
                    "activity": "user_journeys",
                },
                entry_id=f"{context.workflow_id}-peter-journey",
            )

            if peter_result.success:
                result["personas"] = peter_result.output.get("personas", [])
                result["journeys"] = peter_result.output.get("journeys", [])
                result["business_processes"] = peter_result.output.get(
                    "business_processes", []
                )

        return result

    def _apply_enrichment(
        self,
        peter_result: Dict[str, Any],
        enrichment: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Verrijk journeys met Migration 8-vragen context.

        Enrichment sources:
        - Q5: Why migrate? → Journey improvement priorities
        - Q6: Stakeholders? → Persona business impact
        - Q7: Success criteria? → Journey success metrics
        - Q8: Timeline? → Journey migration priority
        """
        answers = enrichment.get("answers", {})

        # Enrich personas with stakeholder info
        enriched_personas = []
        for persona in peter_result.get("personas", []):
            enriched = {**persona}

            # Match stakeholder to persona
            stakeholders = answers.get("q6_stakeholders", "")
            if persona.get("name", "").lower() in stakeholders.lower():
                enriched["stakeholder_notes"] = stakeholders
                enriched["business_impact"] = "high"

            enriched_personas.append(enriched)

        # Enrich journeys with migration context
        enriched_journeys = []
        for journey in peter_result.get("journeys", []):
            enriched = {**journey}

            # Add migration drivers from Q5
            enriched["migration_notes"] = answers.get("q5_problem_statement", "")

            # Add success criteria from Q7
            success = answers.get("q7_success_criteria", "")
            if success:
                enriched["success_criteria"] = enriched.get("success_criteria", [])
                enriched["success_criteria"].append(f"Migration: {success}")

            # Calculate priority based on Q8 timeline
            timeline = answers.get("q8_timeline", "")
            if "critical" in timeline.lower() or "urgent" in timeline.lower():
                enriched["migration_priority"] = "must_have"
            elif "important" in timeline.lower():
                enriched["migration_priority"] = "should_have"
            else:
                enriched["migration_priority"] = "nice_to_have"

            enriched_journeys.append(enriched)

        return {
            **peter_result,
            "personas": enriched_personas,
            "journeys": enriched_journeys,
        }

    def _build_result(
        self,
        raw_extraction: Dict[str, Any],
        vicky_result: Dict[str, Any],
        peter_result: Dict[str, Any],
    ) -> UserJourneyExtractionResult:
        """Build final UserJourneyExtractionResult."""

        # Build personas
        personas = [
            self._dict_to_persona(p)
            for p in peter_result.get("personas", [])
        ]

        # Build journeys
        journeys = [
            self._dict_to_journey(j)
            for j in peter_result.get("journeys", [])
        ]

        # Build screens
        screens = [
            self._dict_to_screen(s)
            for s in raw_extraction.get("screens", [])
        ]

        # Build screen flows
        screen_flows = [
            self._dict_to_screen_flow(f)
            for f in vicky_result.get("screen_flows", [])
        ]

        # Build role matrix
        role_matrix = self._build_role_matrix(
            raw_extraction.get("roles", []),
            raw_extraction.get("auth_checks", []),
            screens,
        )

        # Calculate statistics
        total_steps = sum(len(j.steps) for j in journeys)

        # Calculate confidence
        confidence = self._calculate_confidence(
            personas, journeys, screens, raw_extraction
        )

        return UserJourneyExtractionResult(
            personas=personas,
            journeys=journeys,
            screens=screens,
            screen_flows=screen_flows,
            role_matrix=role_matrix,
            total_personas=len(personas),
            total_journeys=len(journeys),
            total_screens=len(screens),
            total_steps=total_steps,
            extraction_confidence=confidence,
            coverage_percentage=self._calculate_coverage(raw_extraction),
        )

    def _dict_to_persona(self, data: Dict[str, Any]) -> Persona:
        """Convert dict to Persona dataclass."""
        return Persona(
            id=data.get("id", f"persona_{hash(data.get('name', ''))}"),
            name=data.get("name", "Unknown"),
            type=PersonaType(data.get("type", "customer")),
            role_code=data.get("role_code", data.get("role", "USER")),
            goals=data.get("goals", []),
            pain_points=data.get("pain_points", []),
            technical_proficiency=data.get("technical_proficiency", "medium"),
            usage_frequency=data.get("usage_frequency", "daily"),
            permissions=data.get("permissions", []),
            accessible_screens=data.get("accessible_screens", []),
            accessible_features=data.get("accessible_features", []),
            evidence=data.get("evidence", []),
            confidence=data.get("confidence", 0.7),
            stakeholder_notes=data.get("stakeholder_notes"),
            business_impact=data.get("business_impact"),
        )

    def _dict_to_journey(self, data: Dict[str, Any]) -> UserJourney:
        """Convert dict to UserJourney dataclass."""
        steps = [
            self._dict_to_step(s, i)
            for i, s in enumerate(data.get("steps", []))
        ]

        error_paths = [
            self._dict_to_error_path(e)
            for e in data.get("error_paths", [])
        ]

        return UserJourney(
            id=data.get("id", f"journey_{hash(data.get('name', ''))}"),
            name=data.get("name", "Unknown Journey"),
            description=data.get("description", ""),
            persona_id=data.get("persona_id", ""),
            persona_name=data.get("persona_name", ""),
            complexity=JourneyComplexity(data.get("complexity", "moderate")),
            business_value=data.get("business_value", "medium"),
            frequency=data.get("frequency", "unknown"),
            trigger=data.get("trigger", ""),
            trigger_type=data.get("trigger_type", "user_initiated"),
            preconditions=data.get("preconditions", []),
            steps=steps,
            happy_path=data.get("happy_path", [s.id for s in steps]),
            error_paths=error_paths,
            alternative_paths=data.get("alternative_paths", []),
            screens_involved=data.get("screens_involved", []),
            success_criteria=data.get("success_criteria", []),
            outcome=data.get("outcome", ""),
            estimated_duration_minutes=data.get("estimated_duration_minutes", 5),
            sla_minutes=data.get("sla_minutes"),
            required_integrations=data.get("required_integrations", []),
            required_permissions=data.get("required_permissions", []),
            migration_priority=data.get("migration_priority"),
            migration_notes=data.get("migration_notes"),
            target_improvements=data.get("target_improvements", []),
            evidence=data.get("evidence", []),
            confidence=data.get("confidence", 0.7),
        )

    def _dict_to_step(self, data: Dict[str, Any], sequence: int) -> JourneyStep:
        """Convert dict to JourneyStep dataclass."""
        return JourneyStep(
            id=data.get("id", f"step_{sequence}"),
            sequence=sequence,
            action=data.get("action", ""),
            interaction_type=InteractionType(data.get("interaction_type", "view")),
            actor=data.get("actor", "user"),
            screen_id=data.get("screen_id", ""),
            screen_name=data.get("screen_name", data.get("screen", "")),
            system_action=data.get("system_action"),
            api_calls=data.get("api_calls", []),
            database_operations=data.get("database_operations", []),
            validations=data.get("validations", []),
            business_rules=data.get("business_rules", []),
            next_steps=data.get("next_steps", []),
            conditions=data.get("conditions", {}),
            estimated_duration_seconds=data.get("estimated_duration_seconds", 30),
            code_references=data.get("code_references", []),
        )

    def _dict_to_error_path(self, data: Dict[str, Any]) -> ErrorPath:
        """Convert dict to ErrorPath dataclass."""
        return ErrorPath(
            id=data.get("id", f"error_{hash(data.get('trigger_condition', ''))}"),
            trigger_step_id=data.get("trigger_step_id", ""),
            trigger_condition=data.get("trigger_condition", ""),
            error_type=data.get("error_type", "validation"),
            error_screen_id=data.get("error_screen_id"),
            error_message=data.get("error_message", ""),
            recovery_options=data.get("recovery_options", []),
            can_retry=data.get("can_retry", True),
            data_rollback_required=data.get("data_rollback_required", False),
            notification_required=data.get("notification_required", False),
        )

    def _dict_to_screen(self, data: Dict[str, Any]) -> ScreenInfo:
        """Convert dict to ScreenInfo dataclass."""
        return ScreenInfo(
            id=data.get("id", f"screen_{hash(data.get('name', ''))}"),
            name=data.get("name", "Unknown"),
            display_name=data.get("display_name", data.get("name", "")),
            file_path=data.get("file_path", ""),
            screen_type=data.get("screen_type", "form"),
            requires_auth=data.get("requires_auth", True),
            allowed_roles=data.get("allowed_roles", []),
            forms=data.get("forms", []),
            buttons=data.get("buttons", []),
            data_displays=data.get("data_displays", []),
            navigation_links=data.get("navigation_links", []),
            data_sources=data.get("data_sources", []),
            input_fields=data.get("input_fields", []),
            validations=data.get("validations", []),
            evidence=data.get("evidence", []),
        )

    def _dict_to_screen_flow(self, data: Dict[str, Any]) -> ScreenFlow:
        """Convert dict to ScreenFlow dataclass."""
        return ScreenFlow(
            id=data.get("id", f"flow_{hash(data.get('name', ''))}"),
            name=data.get("name", "Unknown Flow"),
            screens=data.get("screens", []),
            transitions=data.get("transitions", []),
            flow_type=data.get("flow_type", "linear"),
            entry_points=data.get("entry_points", []),
            exit_points=data.get("exit_points", []),
            personas=data.get("personas", []),
        )

    def _build_role_matrix(
        self,
        roles: List[Dict],
        auth_checks: List[Dict],
        screens: List[ScreenInfo],
    ) -> RolePermissionMatrix:
        """Build role-permission matrix from extracted data."""
        role_names = list(set(r.get("name", "") for r in roles if r.get("name")))

        # Extract permissions from auth checks
        permissions = list(set(
            a.get("permission", "")
            for a in auth_checks
            if a.get("permission")
        ))

        # Build matrix
        matrix = {}
        screen_access = {}
        feature_access = {}

        for role in role_names:
            matrix[role] = []
            screen_access[role] = []
            feature_access[role] = []

            # Find permissions for this role
            for check in auth_checks:
                if check.get("role") == role:
                    if check.get("permission"):
                        matrix[role].append(check["permission"])
                    if check.get("screen"):
                        screen_access[role].append(check["screen"])
                    if check.get("feature"):
                        feature_access[role].append(check["feature"])

            # Add screens that allow this role
            for screen in screens:
                if role in screen.allowed_roles:
                    if screen.id not in screen_access[role]:
                        screen_access[role].append(screen.id)

        return RolePermissionMatrix(
            roles=role_names,
            permissions=permissions,
            matrix=matrix,
            screen_access=screen_access,
            feature_access=feature_access,
            evidence=[],
        )

    def _calculate_confidence(
        self,
        personas: List[Persona],
        journeys: List[UserJourney],
        screens: List[ScreenInfo],
        raw_extraction: Dict[str, Any],
    ) -> float:
        """Calculate overall extraction confidence."""
        scores = []

        # Persona confidence
        if personas:
            persona_conf = sum(p.confidence for p in personas) / len(personas)
            scores.append(persona_conf)
        else:
            scores.append(0.0)

        # Journey confidence
        if journeys:
            journey_conf = sum(j.confidence for j in journeys) / len(journeys)
            scores.append(journey_conf)
        else:
            scores.append(0.0)

        # Data completeness
        completeness = 0.0
        if raw_extraction.get("roles"):
            completeness += 0.2
        if raw_extraction.get("screens"):
            completeness += 0.2
        if raw_extraction.get("navigation"):
            completeness += 0.2
        if raw_extraction.get("auth_checks"):
            completeness += 0.2
        if raw_extraction.get("api_endpoints"):
            completeness += 0.2
        scores.append(completeness)

        return sum(scores) / len(scores) if scores else 0.0

    def _calculate_coverage(self, raw_extraction: Dict[str, Any]) -> float:
        """Calculate code coverage percentage."""
        # This would ideally track which files were analyzed
        total_items = sum(len(v) for v in raw_extraction.values() if isinstance(v, list))
        return min(100.0, total_items / 10 * 100)  # Simplified

    def _deduplicate(self, items: List[Dict]) -> List[Dict]:
        """Remove duplicates from list of dicts."""
        seen = set()
        result = []
        for item in items:
            key = item.get("id") or item.get("name") or str(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result
```

---

## 4. Code Extractors

### 4.1 Base Extractor

```python
# backend/app/confucius/stages/extractors/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseJourneyExtractor(ABC):
    """Base class for tech-stack specific journey extractors."""

    @abstractmethod
    def supports_stack(self, tech_stack: List[str]) -> bool:
        """Check if this extractor supports the given tech stack."""
        pass

    @abstractmethod
    async def extract(
        self,
        files: List[Dict[str, Any]],
        code_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Extract user journey data from files.

        Returns:
            Dict with keys: roles, screens, forms, navigation,
                           auth_checks, api_endpoints, event_handlers
        """
        pass

    def _find_files_by_extension(
        self,
        files: List[Dict[str, Any]],
        extensions: List[str],
    ) -> List[Dict[str, Any]]:
        """Filter files by extension."""
        return [
            f for f in files
            if any(f.get("path", "").endswith(ext) for ext in extensions)
        ]

    def _extract_with_pattern(
        self,
        content: str,
        pattern: str,
    ) -> List[str]:
        """Extract matches using regex pattern."""
        import re
        return re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
```

### 4.2 ASP.NET Extractor

```python
# backend/app/confucius/stages/extractors/aspnet_extractor.py

import re
from typing import Dict, Any, List
from .base import BaseJourneyExtractor


class AspNetExtractor(BaseJourneyExtractor):
    """
    Extract user journey data from ASP.NET applications.

    Analyzes:
    - [Authorize] attributes
    - .aspx/.cshtml files for screens
    - Controllers for navigation
    - Web.config for roles
    """

    def supports_stack(self, tech_stack: List[str]) -> bool:
        return any(
            t.lower() in ["aspnet", "asp.net", "dotnet", ".net", "mvc", "razor"]
            for t in tech_stack
        )

    async def extract(
        self,
        files: List[Dict[str, Any]],
        code_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        result = {
            "roles": [],
            "screens": [],
            "forms": [],
            "navigation": [],
            "auth_checks": [],
            "api_endpoints": [],
            "event_handlers": [],
        }

        # Extract from controllers
        controllers = self._find_files_by_extension(
            files, [".cs"]
        )
        for f in controllers:
            if "Controller" in f.get("path", ""):
                self._extract_from_controller(f, result)

        # Extract from views
        views = self._find_files_by_extension(
            files, [".aspx", ".cshtml", ".razor"]
        )
        for f in views:
            self._extract_from_view(f, result)

        # Extract from web.config
        configs = [f for f in files if "web.config" in f.get("path", "").lower()]
        for f in configs:
            self._extract_from_config(f, result)

        return result

    def _extract_from_controller(
        self,
        file: Dict[str, Any],
        result: Dict[str, Any],
    ):
        """Extract from ASP.NET controller."""
        content = file.get("content", "")
        path = file.get("path", "")

        # Extract [Authorize] attributes
        auth_patterns = [
            r'\[Authorize\(Roles\s*=\s*"([^"]+)"\)\]',
            r'\[Authorize\(Policy\s*=\s*"([^"]+)"\)\]',
            r'\[AllowAnonymous\]',
        ]

        for pattern in auth_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match:  # Not AllowAnonymous
                    for role in match.split(","):
                        role = role.strip()
                        result["auth_checks"].append({
                            "role": role,
                            "file": path,
                            "type": "authorize_attribute",
                        })
                        if role not in [r.get("name") for r in result["roles"]]:
                            result["roles"].append({"name": role, "source": path})

        # Extract API endpoints
        endpoint_patterns = [
            r'\[Http(Get|Post|Put|Delete|Patch)\("?([^"\)]*)"?\)\]',
            r'\[Route\("([^"]+)"\)\]',
        ]

        for pattern in endpoint_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                endpoint = match[1] if isinstance(match, tuple) else match
                result["api_endpoints"].append({
                    "path": endpoint,
                    "file": path,
                    "method": match[0] if isinstance(match, tuple) else "GET",
                })

        # Extract action methods as potential screens
        action_pattern = r'public\s+(?:async\s+)?(?:Task<)?(?:IActionResult|ActionResult|ViewResult).*?\s+(\w+)\s*\('
        actions = re.findall(action_pattern, content)
        for action in actions:
            controller_name = path.split("/")[-1].replace("Controller.cs", "")
            result["navigation"].append({
                "from": controller_name,
                "action": action,
                "file": path,
            })

    def _extract_from_view(
        self,
        file: Dict[str, Any],
        result: Dict[str, Any],
    ):
        """Extract from ASP.NET view."""
        content = file.get("content", "")
        path = file.get("path", "")

        # Determine screen name from path
        screen_name = path.split("/")[-1].replace(".aspx", "").replace(".cshtml", "")

        screen = {
            "id": f"screen_{hash(path)}",
            "name": screen_name,
            "file_path": path,
            "screen_type": "form" if "<form" in content.lower() else "view",
            "allowed_roles": [],
            "forms": [],
            "buttons": [],
            "input_fields": [],
        }

        # Extract forms
        form_pattern = r'<form[^>]*action="([^"]*)"[^>]*>'
        forms = re.findall(form_pattern, content, re.IGNORECASE)
        screen["forms"] = [{"action": f} for f in forms]

        # Extract input fields
        input_pattern = r'<input[^>]*(?:name|id)="([^"]*)"[^>]*>'
        inputs = re.findall(input_pattern, content, re.IGNORECASE)
        screen["input_fields"] = [{"name": i} for i in inputs]

        # Extract buttons
        button_pattern = r'<(?:button|input[^>]*type="submit")[^>]*(?:value|>)([^<"]*)'
        buttons = re.findall(button_pattern, content, re.IGNORECASE)
        screen["buttons"] = [{"label": b.strip()} for b in buttons if b.strip()]

        # Extract links for navigation
        link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>'
        links = re.findall(link_pattern, content, re.IGNORECASE)
        screen["navigation_links"] = links

        result["screens"].append(screen)

    def _extract_from_config(
        self,
        file: Dict[str, Any],
        result: Dict[str, Any],
    ):
        """Extract roles from web.config."""
        content = file.get("content", "")

        # Extract role definitions
        role_pattern = r'<add\s+name="(\w+)"[^/]*/>'
        roles = re.findall(role_pattern, content)

        for role in roles:
            if role not in [r.get("name") for r in result["roles"]]:
                result["roles"].append({
                    "name": role,
                    "source": "web.config",
                })

        # Extract authorization rules
        auth_pattern = r'<allow\s+roles="([^"]+)"'
        allowed = re.findall(auth_pattern, content, re.IGNORECASE)
        for roles_str in allowed:
            for role in roles_str.split(","):
                role = role.strip()
                result["auth_checks"].append({
                    "role": role,
                    "type": "config_allow",
                    "file": "web.config",
                })
```

### 4.3 ASP Classic Extractor

```python
# backend/app/confucius/stages/extractors/asp_classic_extractor.py

import re
from typing import Dict, Any, List
from .base import BaseJourneyExtractor


class AspClassicExtractor(BaseJourneyExtractor):
    """
    Extract user journey data from ASP Classic applications.

    Analyzes:
    - Session("UserRole") checks
    - .asp files for screens
    - Include files for navigation
    - Response.Redirect for flows
    """

    def supports_stack(self, tech_stack: List[str]) -> bool:
        return any(
            t.lower() in ["asp", "asp classic", "vbscript", "classic asp"]
            for t in tech_stack
        )

    async def extract(
        self,
        files: List[Dict[str, Any]],
        code_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        result = {
            "roles": [],
            "screens": [],
            "forms": [],
            "navigation": [],
            "auth_checks": [],
            "api_endpoints": [],
            "event_handlers": [],
        }

        asp_files = self._find_files_by_extension(files, [".asp", ".inc"])

        for f in asp_files:
            self._extract_from_asp(f, result)

        return result

    def _extract_from_asp(
        self,
        file: Dict[str, Any],
        result: Dict[str, Any],
    ):
        """Extract from ASP Classic file."""
        content = file.get("content", "")
        path = file.get("path", "")

        # Extract Session role checks
        role_patterns = [
            r'Session\s*\(\s*"(?:User)?Role"\s*\)\s*=\s*"(\w+)"',
            r'Session\s*\(\s*"(?:User)?Type"\s*\)\s*=\s*"(\w+)"',
            r'If\s+Session\s*\(\s*"(?:User)?Role"\s*\)\s*=\s*"(\w+)"',
            r'CheckRole\s*\(\s*"(\w+)"\s*\)',
        ]

        for pattern in role_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for role in matches:
                result["auth_checks"].append({
                    "role": role,
                    "file": path,
                    "type": "session_check",
                })
                if role not in [r.get("name") for r in result["roles"]]:
                    result["roles"].append({"name": role, "source": path})

        # Extract Response.Redirect for navigation
        redirect_pattern = r'Response\.Redirect\s*\(\s*"([^"]+)"'
        redirects = re.findall(redirect_pattern, content, re.IGNORECASE)
        for target in redirects:
            result["navigation"].append({
                "from": path,
                "to": target,
                "type": "redirect",
            })

        # Extract screen info
        screen_name = path.split("/")[-1].replace(".asp", "")

        screen = {
            "id": f"screen_{hash(path)}",
            "name": screen_name,
            "file_path": path,
            "screen_type": self._determine_screen_type(content),
            "forms": [],
            "input_fields": [],
        }

        # Extract forms
        form_pattern = r'<form[^>]*action="([^"]*)"[^>]*method="(\w+)"'
        forms = re.findall(form_pattern, content, re.IGNORECASE)
        screen["forms"] = [{"action": f[0], "method": f[1]} for f in forms]

        # Extract input fields
        input_pattern = r'<input[^>]*name="([^"]*)"'
        inputs = re.findall(input_pattern, content, re.IGNORECASE)
        screen["input_fields"] = [{"name": i} for i in inputs]

        result["screens"].append(screen)

    def _determine_screen_type(self, content: str) -> str:
        """Determine screen type from content."""
        content_lower = content.lower()

        if "<form" in content_lower:
            return "form"
        elif "recordset" in content_lower or "select * from" in content_lower:
            return "list"
        elif "dashboard" in content_lower or "menu" in content_lower:
            return "dashboard"
        else:
            return "view"
```

---

## 5. Integratie met Workflows

### 5.1 Brown Paper Integratie

```python
# In brown_paper.py - voeg stage toe

def get_stages(self) -> List[WorkflowStage]:
    return [
        WorkflowStage(
            name="code_understanding",
            ...
        ),
        WorkflowStage(
            name="domain_extraction",
            ...
        ),
        # NEW: User Journey Extraction
        WorkflowStage(
            name="user_journey_extraction",
            description="Extract end-user workflows, personas, and screen flows",
            agents=["Vicky", "Peter"],
            required=True,
            quality_threshold=0.70,
            max_iterations=2,
            depends_on=["domain_extraction"],
        ),
        WorkflowStage(
            name="story_extraction",
            ...
            depends_on=["user_journey_extraction"],  # Updated dependency
        ),
        # ... rest
    ]

async def _execute_user_journey_extraction(
    self,
    context: WorkflowContext,
) -> Dict[str, Any]:
    """Execute user journey extraction stage."""
    from ..stages.user_journey_extraction import UserJourneyExtractionStage

    stage = UserJourneyExtractionStage()
    result = await stage.execute(context)

    return result.agent_results.get("final_result", {})
```

### 5.2 Migration Integratie (met Enrichment)

```python
# In migration.py - voeg stage toe met enrichment

async def _execute_user_journey_extraction(
    self,
    context: WorkflowContext,
) -> Dict[str, Any]:
    """
    Execute user journey extraction with Migration enrichment.

    Enrichment from 8 questions:
    - Q5: Why migrate? → Journey improvement targets
    - Q6: Stakeholders? → Persona business impact
    - Q7: Success criteria? → Journey KPIs
    - Q8: Timeline? → Priority ranking
    """
    from ..stages.user_journey_extraction import UserJourneyExtractionStage

    # Prepare enrichment from answers
    answers = context.shared_data.get("answers", {})
    enrichment = {
        "answers": answers,
        "migration_context": {
            "target_state": answers.get("q2_migration_target", ""),
            "strategy": answers.get("q3_migration_strategy", ""),
        },
    }

    stage = UserJourneyExtractionStage()
    result = await stage.execute(context, enrichment=enrichment)

    return result.agent_results.get("final_result", {})
```

---

## 6. Output Voorbeeld

### Banking Application Extract

```json
{
  "personas": [
    {
      "id": "persona_retail",
      "name": "Particuliere Klant",
      "type": "customer",
      "role_code": "RETAIL_CUSTOMER",
      "goals": [
        "Saldo bekijken",
        "Betalingen doen",
        "Afschriften downloaden"
      ],
      "pain_points": [
        "Langzame laadtijden",
        "Onduidelijke foutmeldingen"
      ],
      "permissions": ["view_balance", "make_transfer", "download_statements"],
      "accessible_screens": ["Dashboard", "Transfers", "Statements"],
      "confidence": 0.85,
      "stakeholder_notes": "Grootste gebruikersgroep (80%)",
      "business_impact": "high"
    },
    {
      "id": "persona_employee",
      "name": "Bankmedewerker",
      "type": "employee",
      "role_code": "BANK_EMPLOYEE",
      "goals": [
        "Klanten helpen",
        "Rekeningen beheren",
        "Transacties verwerken"
      ],
      "permissions": ["view_all_accounts", "manage_accounts", "process_transactions"],
      "accessible_screens": ["EmployeePortal", "CustomerSearch", "AccountManagement"],
      "confidence": 0.90
    }
  ],

  "journeys": [
    {
      "id": "journey_transfer",
      "name": "Overschrijving doen",
      "description": "Klant maakt een overschrijving naar andere rekening",
      "persona_id": "persona_retail",
      "persona_name": "Particuliere Klant",
      "complexity": "moderate",
      "business_value": "high",
      "frequency": "500x/day",
      "trigger": "Klant wil geld overmaken",
      "trigger_type": "user_initiated",
      "preconditions": ["Gebruiker is ingelogd", "Voldoende saldo"],

      "steps": [
        {
          "id": "step_1",
          "sequence": 0,
          "action": "Selecteer 'Betalen' in menu",
          "interaction_type": "navigate",
          "actor": "persona_retail",
          "screen_id": "screen_dashboard",
          "screen_name": "Dashboard",
          "next_steps": ["step_2"]
        },
        {
          "id": "step_2",
          "sequence": 1,
          "action": "Vul IBAN begunstigde in",
          "interaction_type": "input",
          "actor": "persona_retail",
          "screen_id": "screen_transfer",
          "screen_name": "Overschrijving",
          "validations": ["IBAN format check", "IBAN exists check"],
          "next_steps": ["step_3"]
        },
        {
          "id": "step_3",
          "sequence": 2,
          "action": "Vul bedrag en omschrijving in",
          "interaction_type": "input",
          "actor": "persona_retail",
          "screen_id": "screen_transfer",
          "screen_name": "Overschrijving",
          "validations": ["Bedrag > 0", "Saldo check"],
          "business_rules": ["Max €50.000 per dag"],
          "next_steps": ["step_4"]
        },
        {
          "id": "step_4",
          "sequence": 3,
          "action": "Bevestig met TAN code",
          "interaction_type": "authenticate",
          "actor": "persona_retail",
          "screen_id": "screen_confirm",
          "screen_name": "Bevestiging",
          "system_action": "Verstuur SMS met TAN code",
          "next_steps": ["step_5"]
        },
        {
          "id": "step_5",
          "sequence": 4,
          "action": "Bekijk bevestiging",
          "interaction_type": "view",
          "actor": "persona_retail",
          "screen_id": "screen_success",
          "screen_name": "Succes"
        }
      ],

      "happy_path": ["step_1", "step_2", "step_3", "step_4", "step_5"],

      "error_paths": [
        {
          "id": "error_insufficient",
          "trigger_step_id": "step_3",
          "trigger_condition": "Onvoldoende saldo",
          "error_type": "business_rule",
          "error_message": "Uw saldo is ontoereikend voor deze transactie",
          "recovery_options": ["Pas bedrag aan", "Kies andere rekening"],
          "can_retry": true
        },
        {
          "id": "error_invalid_iban",
          "trigger_step_id": "step_2",
          "trigger_condition": "Ongeldig IBAN",
          "error_type": "validation",
          "error_message": "Het ingevoerde IBAN is niet geldig",
          "recovery_options": ["Corrigeer IBAN"],
          "can_retry": true
        }
      ],

      "screens_involved": ["Dashboard", "Overschrijving", "Bevestiging", "Succes"],
      "success_criteria": ["Transactie is verwerkt", "Bevestigingsmail verzonden"],
      "outcome": "Bedrag is afgeschreven en begunstigde ontvangt geld",
      "estimated_duration_minutes": 3,

      "migration_priority": "must_have",
      "migration_notes": "Core functionaliteit, moet 100% werken bij go-live",
      "target_improvements": [
        "Snellere IBAN validatie",
        "Push notificatie i.p.v. SMS"
      ],

      "confidence": 0.92
    }
  ],

  "screens": [...],
  "screen_flows": [...],
  "role_matrix": {...},

  "total_personas": 4,
  "total_journeys": 12,
  "total_screens": 28,
  "total_steps": 67,
  "extraction_confidence": 0.85
}
```

---

## 7. Test Plan

```python
# tests/unit/confucius/stages/test_user_journey_extraction.py

class TestUserJourneyExtractionStage:
    """Tests for UserJourneyExtractionStage."""

    async def test_extract_personas_from_aspnet(self):
        """Test persona extraction from ASP.NET code."""
        pass

    async def test_extract_journeys_from_navigation(self):
        """Test journey extraction from navigation structure."""
        pass

    async def test_enrichment_with_migration_answers(self):
        """Test enrichment with Migration 8 questions."""
        pass

    async def test_role_matrix_construction(self):
        """Test role-permission matrix building."""
        pass

    async def test_confidence_calculation(self):
        """Test confidence score calculation."""
        pass

    async def test_multiple_tech_stacks(self):
        """Test extraction across multiple tech stacks."""
        pass
```

---

## 8. Implementatie Stappenplan

| Stap | Beschrijving | Geschatte tijd |
|------|--------------|----------------|
| 1 | Data models implementeren | 2 uur |
| 2 | Base extractor + ASP.NET extractor | 3 uur |
| 3 | ASP Classic extractor | 2 uur |
| 4 | UserJourneyExtractionStage | 4 uur |
| 5 | Brown Paper integratie | 1 uur |
| 6 | Migration integratie + enrichment | 2 uur |
| 7 | Unit tests | 3 uur |
| 8 | Integration tests | 2 uur |
| **Totaal** | | **19 uur** |
