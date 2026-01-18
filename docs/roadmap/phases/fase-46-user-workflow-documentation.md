# Fase 46: User Workflow Documentation

**Status:** PLANNED
**Priority:** HIGH (ROI 7.0)
**Effort:** 140 uur (~4-5 weken)
**Timeline:** Week 201-208
**Dependencies:** Fase 45 (Reverse Traceability Service)

---

## Executive Summary

Automatische documentatie van **user workflows** door applicaties heen, inclusief:
- ASCII schermafbeeldingen per stap
- Menu opties en keuzemogelijkheden
- Navigatiepaden door de applicatie
- Per gebruikerstype (persona) de beschikbare workflows

### Toepassingsgebieden

| Modus | Beschrijving | Use Case |
|-------|--------------|----------|
| **Brown Paper** | Extract workflows uit legacy code | Begrip van bestaande systemen |
| **Standalone** | Analyse van willekeurige source repo | Externe project documentatie |
| **Green Paper** | Genereer workflow specs voor nieuwe features | Design documentatie |
| **Runtime** | Capture workflows vanuit UI tests | Actuele gebruikerspaden |

---

## Probleemstelling

### Huidige Situatie

```
PROBLEEM: Geen gestructureerde workflow documentatie

┌─────────────────────────────────────────────────────────────┐
│  Legacy Applicatie                                          │
│                                                             │
│  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐             │
│  │Screen│───►│Screen│───►│Screen│───►│Screen│             │
│  │  A   │    │  B   │    │  C   │    │  D   │             │
│  └──────┘    └──────┘    └──────┘    └──────┘             │
│      │           │           │           │                  │
│      ▼           ▼           ▼           ▼                  │
│   Menu?       Menu?       Menu?       Menu?                 │
│   Keuzes?     Keuzes?     Keuzes?     Keuzes?              │
│   Users?      Users?      Users?      Users?                │
│                                                             │
│  ✗ ONBEKEND: Welke gebruikers welke paden volgen           │
│  ✗ ONBEKEND: Welke keuzes leiden naar welke schermen       │
│  ✗ ONBEKEND: Hoe zien de schermen eruit                    │
└─────────────────────────────────────────────────────────────┘
```

### Gewenste Situatie

```
OPLOSSING: Gestructureerde Workflow Documentatie

┌─────────────────────────────────────────────────────────────┐
│  WORKFLOW: Administrator - Gebruiker Aanmaken               │
│  Persona: Administrator | Stappen: 5 | Geschatte tijd: 3min │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STAP 1: Dashboard                                          │
│  ┌───────────────────────────────────────────┐             │
│  │  ╔═════════════════════════════════════╗  │             │
│  │  ║  MarQed Dashboard        [Logout]   ║  │             │
│  │  ╠═════════════════════════════════════╣  │             │
│  │  ║  Menu:                              ║  │             │
│  │  ║  [1] Gebruikers                     ║◄─┼── Keuze     │
│  │  ║  [2] Projecten                      ║  │             │
│  │  ║  [3] Rapporten                      ║  │             │
│  │  ╚═════════════════════════════════════╝  │             │
│  └───────────────────────────────────────────┘             │
│  Keuzes: [1]→Stap 2 | [2]→Workflow B | [3]→Workflow C      │
│                                                             │
│  STAP 2: Gebruikersbeheer                                   │
│  ┌───────────────────────────────────────────┐             │
│  │  ╔═════════════════════════════════════╗  │             │
│  │  ║  Gebruikersbeheer                   ║  │             │
│  │  ╠═════════════════════════════════════╣  │             │
│  │  ║  [Nieuwe Gebruiker]  [Zoeken]       ║◄─┼── Actie     │
│  │  ║                                     ║  │             │
│  │  ║  Naam        Email        Status    ║  │             │
│  │  ║  Jan Jansen  jan@...     Actief     ║  │             │
│  │  ║  ...                                ║  │             │
│  │  ╚═════════════════════════════════════╝  │             │
│  └───────────────────────────────────────────┘             │
│  Acties: [Nieuwe Gebruiker]→Stap 3 | [Zoeken]→Stap 2a      │
│                                                             │
│  ... (Stap 3, 4, 5)                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Modellen

### User Workflow Models

```python
# backend/app/models/user_workflow.py

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base


class UserPersona(Base):
    """
    Gebruikerspersona geïdentificeerd in de applicatie.
    """
    __tablename__ = "user_personas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Koppeling (één van deze gevuld)
    project_id = Column(String(50), ForeignKey("items.id"), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("reverse_traceability_sessions.id"), nullable=True, index=True)

    # Persona details
    name = Column(String(100), nullable=False)  # "Administrator", "End User", "Guest"
    description = Column(Text, nullable=True)
    role_level = Column(String(50), nullable=True)  # admin, power_user, standard, guest
    permissions = Column(JSONB, default=[])  # ["read", "write", "delete", "admin"]

    # Source detection
    detected_from = Column(String(50), nullable=False, default="code")
    # code, database, documentation, manual
    source_files = Column(JSONB, default=[])  # Files where this persona was detected
    confidence = Column(Float, default=0.5)

    # Statistics
    workflow_count = Column(Integer, default=0)
    screen_access_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    workflows = relationship("UserWorkflow", back_populates="persona", cascade="all, delete-orphan")


class UserWorkflow(Base):
    """
    Een gebruikersworkflow door de applicatie.
    """
    __tablename__ = "user_workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("user_personas.id", ondelete="CASCADE"), nullable=False, index=True)

    # Koppeling (één van deze gevuld)
    project_id = Column(String(50), ForeignKey("items.id"), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("reverse_traceability_sessions.id"), nullable=True, index=True)

    # Workflow identification
    identifier = Column(String(50), nullable=False)  # "WF-ADMIN-001"
    name = Column(String(200), nullable=False)  # "Gebruiker Aanmaken"
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # "User Management", "Reporting"

    # Workflow metadata
    estimated_duration_minutes = Column(Integer, nullable=True)
    complexity = Column(String(20), default="medium")  # simple, medium, complex
    frequency = Column(String(50), nullable=True)  # daily, weekly, monthly, rarely
    priority = Column(String(20), default="medium")

    # Starting point
    entry_point = Column(String(200), nullable=True)  # "Dashboard", "Login"
    entry_url = Column(String(500), nullable=True)  # "/dashboard"

    # Linked requirements
    linked_epic_id = Column(UUID(as_uuid=True), ForeignKey("task_epics.id"), nullable=True)
    linked_feature_id = Column(UUID(as_uuid=True), ForeignKey("task_features.id"), nullable=True)
    linked_stories = Column(JSONB, default=[])  # Story IDs this workflow relates to

    # Statistics
    step_count = Column(Integer, default=0)
    decision_points = Column(Integer, default=0)  # Number of choices/branches

    # Status
    is_complete = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    persona = relationship("UserPersona", back_populates="workflows")
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStep.sequence_number")


class WorkflowStep(Base):
    """
    Een stap in een gebruikersworkflow.
    """
    __tablename__ = "workflow_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("user_workflows.id", ondelete="CASCADE"), nullable=False, index=True)

    # Step identification
    sequence_number = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)  # "Dashboard", "User Form"
    description = Column(Text, nullable=True)

    # Screen representation
    screen_name = Column(String(200), nullable=True)
    screen_url = Column(String(500), nullable=True)  # "/users/new"
    screen_ascii = Column(Text, nullable=True)  # ASCII representation of the screen

    # Screen elements (for ASCII generation)
    screen_elements = Column(JSONB, default={})
    # {
    #   "title": "Gebruiker Aanmaken",
    #   "fields": [{"name": "email", "type": "input", "required": true}],
    #   "buttons": [{"label": "Opslaan", "action": "submit"}, {"label": "Annuleren", "action": "cancel"}],
    #   "menu_items": [{"label": "Dashboard", "shortcut": "1", "target": "dashboard"}]
    # }

    # User actions available at this step
    available_actions = Column(JSONB, default=[])
    # [
    #   {"action": "click", "element": "Opslaan", "leads_to": "step_5", "description": "Gebruiker opslaan"},
    #   {"action": "click", "element": "Annuleren", "leads_to": "step_2", "description": "Terug naar overzicht"}
    # ]

    # Menu options at this step
    menu_options = Column(JSONB, default=[])
    # [
    #   {"key": "1", "label": "Gebruikers", "leads_to": "workflow_users"},
    #   {"key": "2", "label": "Projecten", "leads_to": "workflow_projects"}
    # ]

    # Step type
    step_type = Column(String(50), default="screen")
    # screen, decision, action, wait, external_system, end

    # Decision point (if step_type == "decision")
    is_decision_point = Column(Boolean, default=False)
    decision_options = Column(JSONB, default=[])
    # [{"condition": "email_valid", "true_step": 4, "false_step": 3}]

    # Source code mapping
    source_files = Column(JSONB, default=[])  # ["views/users/create.py:45"]
    source_functions = Column(JSONB, default=[])  # ["render_create_form", "validate_user"]
    source_templates = Column(JSONB, default=[])  # ["templates/users/create.html"]

    # Linked to requirements
    linked_story_id = Column(UUID(as_uuid=True), ForeignKey("task_stories.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    workflow = relationship("UserWorkflow", back_populates="steps")


class WorkflowTransition(Base):
    """
    Transitie tussen workflow stappen (edges in de flow graph).
    """
    __tablename__ = "workflow_transitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("user_workflows.id", ondelete="CASCADE"), nullable=False, index=True)

    # From/To
    from_step_id = Column(UUID(as_uuid=True), ForeignKey("workflow_steps.id", ondelete="CASCADE"), nullable=False, index=True)
    to_step_id = Column(UUID(as_uuid=True), ForeignKey("workflow_steps.id", ondelete="CASCADE"), nullable=False, index=True)

    # Transition details
    trigger = Column(String(200), nullable=False)  # "click_save", "menu_1", "form_submit"
    label = Column(String(200), nullable=True)  # "Opslaan", "Naar Gebruikers"
    condition = Column(Text, nullable=True)  # "user.is_valid"

    # Transition type
    transition_type = Column(String(50), default="action")
    # action, navigation, conditional, error, external

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    from_step = relationship("WorkflowStep", foreign_keys=[from_step_id])
    to_step = relationship("WorkflowStep", foreign_keys=[to_step_id])
```

---

## Services

### 1. Workflow Extractor Service

```python
# backend/app/services/workflow/workflow_extractor_service.py

class WorkflowExtractorService:
    """
    Extraheert user workflows uit code analyse.

    Detectie methoden:
    1. Route analysis - URL patterns → screens
    2. Template analysis - HTML/Jinja templates → screen elements
    3. Authorization decorators → persona detection
    4. Form submissions → actions and transitions
    5. Navigation patterns → menu options
    """

    async def extract_workflows_from_code(
        self,
        session_id: str,
        code_paths: List[str],
        options: Optional[Dict[str, Any]] = None,
    ) -> WorkflowExtractionResult:
        """
        Extract all workflows from code analysis.

        Steps:
        1. Detect personas (from auth decorators, role checks)
        2. Detect screens (from routes, templates)
        3. Detect actions (from form handlers, buttons)
        4. Build workflow graphs
        5. Generate ASCII representations
        """
        pass

    async def detect_personas(
        self,
        code_elements: List[CodeElement],
    ) -> List[UserPersona]:
        """
        Detect user personas from:
        - @login_required, @admin_required decorators
        - role checks in code
        - database user tables
        - documentation
        """
        pass

    async def detect_screens(
        self,
        code_elements: List[CodeElement],
    ) -> List[ScreenDefinition]:
        """
        Detect screens from:
        - Route handlers (Flask, FastAPI, Django)
        - Template files
        - React/Vue components
        """
        pass

    async def build_workflow_graph(
        self,
        persona: UserPersona,
        screens: List[ScreenDefinition],
        actions: List[ActionDefinition],
    ) -> UserWorkflow:
        """Build workflow graph for a persona."""
        pass


class ASCIIScreenGenerator:
    """
    Genereert ASCII representaties van schermen.
    """

    SCREEN_TEMPLATES = {
        "form": '''
╔═══════════════════════════════════════════════════════════╗
║  {title}                                                   ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
{fields}
║                                                           ║
║  {buttons}                                                ║
╚═══════════════════════════════════════════════════════════╝
''',
        "list": '''
╔═══════════════════════════════════════════════════════════╗
║  {title}                          {actions}               ║
╠═══════════════════════════════════════════════════════════╣
║  {headers}                                                ║
╠───────────────────────────────────────────────────────────╣
{rows}
╚═══════════════════════════════════════════════════════════╝
''',
        "dashboard": '''
╔═══════════════════════════════════════════════════════════╗
║  {title}                                    [{user}]      ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  Menu:                                                    ║
{menu_items}
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
'''
    }

    def generate_screen_ascii(
        self,
        step: WorkflowStep,
    ) -> str:
        """Generate ASCII representation of a screen."""
        pass

    def generate_field_line(
        self,
        field: Dict[str, Any],
    ) -> str:
        """Generate ASCII for a form field."""
        # Example: ║  Email:     [________________________]  *    ║
        pass

    def generate_menu_line(
        self,
        item: Dict[str, Any],
    ) -> str:
        """Generate ASCII for a menu item."""
        # Example: ║  [1] Gebruikers                                ║
        pass
```

### 2. Workflow Document Generator

```python
# backend/app/services/workflow/workflow_document_generator.py

class WorkflowDocumentGenerator:
    """
    Genereert workflow documentatie.

    Output formaten:
    - Markdown met ASCII schermen
    - HTML met interactieve flow
    - PDF met print-ready layout
    - Mermaid diagrams
    """

    async def generate_workflow_document(
        self,
        workflow_id: str,
        format: str = "markdown",
        include_ascii_screens: bool = True,
        include_flow_diagram: bool = True,
    ) -> WorkflowDocument:
        """Generate complete workflow documentation."""
        pass

    def generate_mermaid_flowchart(
        self,
        workflow: UserWorkflow,
    ) -> str:
        """Generate Mermaid flowchart for workflow."""
        # flowchart TD
        #     A[Dashboard] -->|Click Users| B[User List]
        #     B -->|Click New| C[Create Form]
        #     C -->|Submit| D{Valid?}
        #     D -->|Yes| E[Success]
        #     D -->|No| C
        pass

    def generate_all_persona_workflows(
        self,
        session_id: str,
    ) -> Dict[str, List[WorkflowDocument]]:
        """Generate documentation for all personas and their workflows."""
        pass
```

---

## ASCII Screen Examples

### Login Screen
```
╔═══════════════════════════════════════════════════════════╗
║                    MARQED LOGIN                           ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  Email:        [________________________________]         ║
║                                                           ║
║  Wachtwoord:   [________________________________]         ║
║                                                           ║
║  [ ] Onthoud mij                                          ║
║                                                           ║
║  [    INLOGGEN    ]        [Wachtwoord vergeten?]        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Acties:
  [INLOGGEN] ────────► Dashboard (indien geldig)
                   └─► Login Error (indien ongeldig)
  [Wachtwoord vergeten?] ─► Wachtwoord Reset Flow
```

### Dashboard with Menu
```
╔═══════════════════════════════════════════════════════════╗
║  MarQed Dashboard                        [Admin ▼][Logout]║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  Welkom terug, Jan Jansen                                 ║
║                                                           ║
║  ┌─ Hoofdmenu ──────────────────────────────────────────┐ ║
║  │                                                       │ ║
║  │  [1] 👥 Gebruikersbeheer                             │ ║
║  │  [2] 📁 Projecten                                    │ ║
║  │  [3] 📊 Rapporten                                    │ ║
║  │  [4] ⚙️  Instellingen                                │ ║
║  │                                                       │ ║
║  └───────────────────────────────────────────────────────┘ ║
║                                                           ║
║  Recente Activiteit:                                      ║
║  • Project "HCI-CRS" analyse voltooid (2 uur geleden)    ║
║  • Nieuwe gebruiker toegevoegd (gisteren)                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Menu Navigatie:
  [1] ──► Gebruikersbeheer (Workflow: User Management)
  [2] ──► Projectoverzicht (Workflow: Project Management)
  [3] ──► Rapportage Dashboard (Workflow: Reporting)
  [4] ──► Systeeminstellingen (Workflow: Settings)
```

### Form Screen
```
╔═══════════════════════════════════════════════════════════╗
║  Nieuwe Gebruiker Aanmaken                    [✕ Sluiten] ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  Persoonlijke Gegevens                                    ║
║  ─────────────────────                                    ║
║  Voornaam:      [Jan                    ] *               ║
║  Achternaam:    [Jansen                 ] *               ║
║  Email:         [jan.jansen@example.com ] *               ║
║                                                           ║
║  Account Instellingen                                     ║
║  ────────────────────                                     ║
║  Rol:           [Administrator      ▼   ] *               ║
║                 ┌─────────────────────┐                   ║
║                 │ Administrator       │                   ║
║                 │ Power User          │                   ║
║                 │ Standaard Gebruiker │                   ║
║                 │ Gast                │                   ║
║                 └─────────────────────┘                   ║
║  Actief:        [✓] Account direct activeren              ║
║                                                           ║
║  [  Annuleren  ]                    [  Gebruiker Opslaan ]║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Acties:
  [Gebruiker Opslaan] ──► Validatie
                          ├─► Succes: Gebruikerslijst + melding
                          └─► Fout: Toon validatiefouten
  [Annuleren] ──► Gebruikerslijst (zonder wijzigingen)
  [✕ Sluiten] ──► Dashboard
```

### List Screen with Actions
```
╔═══════════════════════════════════════════════════════════╗
║  Gebruikersbeheer              [+ Nieuwe Gebruiker][🔍]   ║
╠═══════════════════════════════════════════════════════════╣
║  Naam              Email                  Rol      Status ║
╠───────────────────────────────────────────────────────────╣
║  Jan Jansen        jan@example.com        Admin    ● Act  ║
║  [Bewerk] [Verwijder]                                     ║
╠───────────────────────────────────────────────────────────╣
║  Piet Pietersen    piet@example.com       User     ● Act  ║
║  [Bewerk] [Verwijder]                                     ║
╠───────────────────────────────────────────────────────────╣
║  Anna de Vries     anna@example.com       Guest    ○ Inac ║
║  [Bewerk] [Verwijder] [Activeer]                          ║
╠───────────────────────────────────────────────────────────╣
║                                                           ║
║  Pagina 1 van 3    [◄ Vorige] [1] [2] [3] [Volgende ►]   ║
╚═══════════════════════════════════════════════════════════╝

Acties:
  [+ Nieuwe Gebruiker] ──► Gebruiker Aanmaken Form
  [🔍] ──► Zoekfilter uitklappen
  [Bewerk] ──► Gebruiker Bewerken Form
  [Verwijder] ──► Bevestigingsdialoog
  [Activeer] ──► Account activeren (alleen bij inactief)
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/workflows/extract` | Extract workflows from code |
| `GET` | `/api/workflows/{session_id}` | Get all workflows for session |
| `GET` | `/api/workflows/{session_id}/personas` | Get detected personas |
| `GET` | `/api/workflows/{id}` | Get single workflow with steps |
| `GET` | `/api/workflows/{id}/ascii` | Get ASCII representation |
| `GET` | `/api/workflows/{id}/mermaid` | Get Mermaid diagram |
| `POST` | `/api/workflows/{id}/document` | Generate workflow document |
| `PUT` | `/api/workflows/steps/{id}` | Update step (manual refinement) |
| `POST` | `/api/workflows/{id}/verify` | Mark workflow as verified |

---

## Implementation Phases

### Phase 1: Database Models & Core Extraction (Week 201-203) - 50 uur

| Task | Hours | Deliverable |
|------|-------|-------------|
| Database models (4 tabellen) | 12 | Alembic migrations |
| WorkflowExtractorService | 20 | Route, template, auth detection |
| Persona detection | 10 | Role-based persona extraction |
| Unit tests | 8 | 30+ tests |

### Phase 2: ASCII Screen Generation (Week 204-205) - 40 uur

| Task | Hours | Deliverable |
|------|-------|-------------|
| ASCIIScreenGenerator | 20 | Screen templates, element rendering |
| Screen element detection | 12 | Forms, menus, lists, buttons |
| Integration with extraction | 8 | Auto-generate ASCII from code |

### Phase 3: Document Generation (Week 206-207) - 30 uur

| Task | Hours | Deliverable |
|------|-------|-------------|
| WorkflowDocumentGenerator | 16 | Markdown, HTML output |
| Mermaid diagram generation | 8 | Flow visualizations |
| Export to PDF/DOCX | 6 | Print-ready formats |

### Phase 4: API & Integration (Week 208) - 20 uur

| Task | Hours | Deliverable |
|------|-------|-------------|
| API endpoints | 8 | 9 REST endpoints |
| Brown Paper integration | 6 | Optional workflow extraction |
| Documentation | 4 | API docs, examples |
| Integration tests | 2 | E2E tests |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Persona Detection Accuracy | >= 85% | Correct personas identified |
| Screen Detection Coverage | >= 80% | Screens detected vs actual |
| Workflow Completeness | >= 75% | Full paths captured |
| ASCII Readability | >= 90% | Human review acceptance |
| Processing Time | < 3 min | Per application analysis |

---

## Integration Points

### Brown Paper Integration
```python
# In BrownPaperService.run_enhanced_analysis():

if options.include_workflow_documentation:
    workflow_service = get_workflow_extractor_service(self.db)

    workflows = await workflow_service.extract_workflows_from_code(
        session_id=session_id,
        code_paths=analysis.module_paths,
    )

    result.user_workflows = workflows
    result.personas = workflows.personas
```

### Fase 45 Integration
```python
# In ReverseTraceabilityService:

if options.include_user_workflows:
    # Link generated requirements to workflows
    for requirement in generated_requirements:
        workflows = self._find_related_workflows(requirement)
        requirement.linked_workflows = workflows
```

---

## References

- [Fase 45: Reverse Traceability Service](./fase-45-reverse-traceability-service.md)
- [Brown Paper Service](../../backend/app/services/brown_paper_service.py)
- [Task Hierarchy Models](../../backend/app/models/task_hierarchy.py)

---

*Created: Week 158 (2026-01-18)*
