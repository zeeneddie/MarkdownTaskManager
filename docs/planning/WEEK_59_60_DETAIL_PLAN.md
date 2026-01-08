# Week 59-60: Agent OS Integratie - Detail Planning

**Periode:** Week 59-60 (10 werkdagen)
**Doel:** 8 Agent OS concepten toevoegen aan MarQed platform
**Totale Effort:** 19 uur
**Bron:** github.com/zeeneddie/agent-os

---

## Executive Summary

Week 59-60 voegt 8 unieke concepten van Agent OS toe aan ons platform. Dit zijn AANVULLINGEN op bestaande functionaliteit, geen vervangingen. Focus is op:

1. **Standards System** - Codified coding standards per workflow
2. **Spec Verification** - Visuele assets + reusability checks
3. **Workflow Discipline** - Strikte scope + spec shaping
4. **Agent Improvements** - Skill descriptions + quick templates

---

## Week 59: Standards System + Spec Verification

### Dag 1-2: Standards-as-Files System (4 uur)

**Concept:** Coding standards als markdown bestanden die automatisch worden geladen bij elke workflow.

#### Te Maken: `.standards/` folder structuur

```
.standards/
├── global/                         # Altijd geladen (voor alle workflows)
│   ├── git-conventions.md          # Commit messages, branching
│   ├── code-review-checklist.md    # Review criteria
│   ├── naming-conventions.md       # Variabelen, functies, klassen
│   └── documentation-standards.md  # Docstrings, comments
│
├── backend/                        # Geladen bij backend werk
│   ├── python-fastapi.md           # FastAPI patterns, async
│   ├── sqlalchemy-patterns.md      # ORM best practices
│   ├── api-design.md               # REST conventions
│   └── error-handling.md           # Exception patterns
│
├── frontend/                       # Geladen bij frontend werk
│   ├── html-accessibility.md       # WCAG 2.1 rules
│   ├── css-methodology.md          # BEM, utility classes
│   └── javascript-patterns.md      # ES6+, async patterns
│
├── testing/                        # Geladen bij test werk
│   ├── unit-test-patterns.md       # pytest, jest patterns
│   ├── integration-testing.md      # API testing, mocking
│   └── test-coverage-rules.md      # Coverage thresholds
│
├── security/                       # Geladen bij security werk
│   ├── owasp-top-10.md             # Vulnerability prevention
│   ├── input-validation.md         # Sanitization rules
│   └── authentication.md           # Auth patterns
│
└── workflow-specific/              # Per workflow type
    ├── green-paper.md              # BMAD Green Paper rules
    ├── brown-paper.md              # BMAD Brown Paper rules
    └── maintenance.md              # Maintenance workflow rules
```

#### Te Implementeren: StandardsLoaderService

**File:** `backend/app/services/standards_loader_service.py`

```python
class StandardsLoaderService:
    """
    Laadt relevante .standards/ bestanden voor een workflow.

    Workflow → Standards Mapping:
    - GREEN_PAPER:     global/
    - BROWN_PAPER:     global/, backend/, frontend/, security/
    - MAINTENANCE:     global/, backend/, testing/
    - BUG:             global/, testing/
    - NEW_FEATURE:     global/, backend/, frontend/, testing/
    - QUALITY_AUDIT:   global/, security/, testing/
    - TESTING:         global/, testing/
    """

    WORKFLOW_STANDARDS_MAP = {
        "GREEN_PAPER": ["global"],
        "BROWN_PAPER": ["global", "backend", "frontend", "security"],
        "MAINTENANCE": ["global", "backend", "testing"],
        "BUG": ["global", "testing"],
        "NEW_FEATURE": ["global", "backend", "frontend", "testing"],
        "QUALITY_AUDIT": ["global", "security", "testing"],
        "TESTING": ["global", "testing"],
        "MIGRATION": ["global", "backend", "security"],
        "ENHANCEMENT": ["global", "backend", "testing"],
        "QUALITY_IMPROVEMENT": ["global", "testing"],
    }

    async def load_standards_for_workflow(
        self,
        workflow_type: str,
        project_path: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Laad alle relevante standards voor een workflow.

        Returns:
            Dict[category, content] - Gecombineerde standards content
        """
        pass

    async def get_standards_context(
        self,
        workflow_type: str
    ) -> str:
        """
        Genereer een prompt-ready context string met alle standards.
        """
        pass
```

#### API Endpoints (2 new)

```python
# GET /api/standards
# List all available standards categories and files

# GET /api/standards/{workflow_type}
# Get standards context for a specific workflow type
```

#### Integratie Punten

1. **AgentService** - Inject standards in agent prompts
2. **BMADBrownPaperWorkflow** - Load standards voor spec generation
3. **KanbanAgentService** - Standards bij lane transitions

---

### Dag 3: Visuele Asset Validatie (2 uur)

**Concept:** Quality Gates checken of vereiste design assets bestaan.

#### Te Implementeren: VisualAssetValidator

**File:** `backend/app/validators/visual_asset_validator.py`

```python
class VisualAssetValidator:
    """
    Valideert dat vereiste visuele assets aanwezig zijn.

    Checks:
    1. /visuals/ folder bestaat
    2. Minimaal 1 mockup/wireframe per feature
    3. Design tokens file aanwezig (optioneel)
    """

    REQUIRED_STRUCTURE = {
        "visuals": {
            "required": True,
            "description": "Folder voor design assets"
        },
        "visuals/mockups": {
            "required": False,
            "description": "UI mockups"
        },
        "visuals/wireframes": {
            "required": False,
            "description": "Low-fidelity wireframes"
        },
    }

    async def validate_project(
        self,
        project_path: str,
        strict: bool = False
    ) -> ValidationResult:
        """
        Valideer visuele assets voor een project.

        Args:
            project_path: Root path van het project
            strict: Als True, fail als assets ontbreken

        Returns:
            ValidationResult met findings
        """
        pass
```

#### Quality Gate Integratie

Toevoegen aan `kanban_quality_gate_service.py`:

```python
# Nieuwe category: DESIGN
ValidationCategory.DESIGN = "design"

# Nieuwe rules
{
    "category": "design",
    "rule_id": "DESIGN-001",
    "name": "Visuals Folder Exists",
    "description": "Project moet een /visuals/ folder hebben",
    "severity": "warning",
    "blocking": False
},
{
    "category": "design",
    "rule_id": "DESIGN-002",
    "name": "Feature Has Mockup",
    "description": "Elke feature moet minimaal 1 mockup hebben",
    "severity": "info",
    "blocking": False
}
```

---

### Dag 4: Reusability Check (2 uur)

**Concept:** Spec verificatie identificeert herbruikbare componenten.

#### Te Implementeren: ReusabilityAnalyzer

**File:** `backend/app/services/reusability_analyzer_service.py`

```python
class ReusabilityAnalyzer:
    """
    Analyseert specs en code voor herbruikbare componenten.

    Checks:
    1. Duplicate functionaliteit detectie
    2. Shared component kandidaten
    3. Tech debt preventie door early detection
    """

    async def analyze_spec(
        self,
        spec_content: str,
        existing_components: List[str]
    ) -> ReusabilityReport:
        """
        Analyseer een spec voor reusability opportunities.

        Returns:
            ReusabilityReport met:
            - duplicate_candidates: Mogelijk duplicate functionaliteit
            - shared_components: Kandidaten voor shared libs
            - recommendations: Concrete aanbevelingen
        """
        pass

    async def find_similar_features(
        self,
        feature_description: str
    ) -> List[SimilarFeature]:
        """
        Vind gelijkaardige features in bestaande projecten.
        Gebruikt ChromaDB voor semantic search.
        """
        pass
```

#### ChromaDB Collection

Nieuwe collection: `reusable_components`

```python
{
    "id": "comp-001",
    "name": "AuthenticationService",
    "type": "service",
    "description": "JWT-based authentication",
    "used_in_projects": ["project-a", "project-b"],
    "tags": ["auth", "jwt", "security"],
    "embedding": [...]  # Semantic embedding
}
```

---

### Dag 5: Verplichte Visuals Folder (2 uur)

**Concept:** BMAD workflows vereisen design-first aanpak.

#### Te Implementeren: Design-First Enforcement

**Aanpassingen in:** `backend/app/services/brown_paper_service.py`

```python
class BMADBrownPaperWorkflow:

    DESIGN_FIRST_CONFIG = {
        "require_visuals_folder": True,
        "min_mockups_per_feature": 1,
        "allowed_formats": [".png", ".jpg", ".svg", ".figma"],
        "warn_on_missing": True,
        "block_on_missing": False  # Start met warnings
    }

    async def validate_design_first(
        self,
        session_id: str
    ) -> DesignFirstResult:
        """
        Valideer design-first requirements voordat tasks worden gegenereerd.
        """
        pass
```

#### Nieuwe Vraag in BMAD Workflow

Toevoegen aan BMAD_QUESTIONS:

```python
BMAD_QUESTIONS[9] = {
    "question": "Where are the design assets located?",
    "description": "Path to mockups, wireframes, or design system. E.g., /visuals/, /designs/",
    "required": False,
    "min_length": 0,
}
```

---

## Week 60: Workflow Discipline + Agent Improvements

### Dag 6: Strikte Scope Beperking (1 uur)

**Concept:** Agents doen ALLEEN toegewezen taken, geen extra's.

#### Te Implementeren: ScopeEnforcer

**File:** `backend/app/services/scope_enforcer_service.py`

```python
class ScopeEnforcer:
    """
    Zorgt dat agents binnen hun scope blijven.

    Rules:
    1. Agent mag alleen wijzigen wat expliciet is toegewezen
    2. Geen "improvements" buiten scope
    3. Logging van scope violations
    """

    SCOPE_RULES = """
    CRITICAL SCOPE INSTRUCTIONS:

    You are ONLY allowed to work on the following:
    {assigned_tasks}

    DO NOT:
    - Make "improvements" to unrelated code
    - Refactor code that isn't explicitly assigned
    - Add features not in the specification
    - Change configuration outside your scope

    If you notice issues outside your scope:
    - Log them as observations
    - Do NOT fix them automatically
    - Suggest them for future work
    """

    def generate_scope_prompt(
        self,
        assigned_tasks: List[str]
    ) -> str:
        """
        Genereer scope-beperking prompt voor agent.
        """
        pass

    async def validate_changes(
        self,
        assigned_scope: List[str],
        actual_changes: List[str]
    ) -> ScopeValidationResult:
        """
        Valideer of changes binnen scope vallen.
        """
        pass
```

#### Integratie in AgentService

```python
class AgentService:

    async def execute_workflow(self, ...):
        # Inject scope rules in prompt
        scope_prompt = self.scope_enforcer.generate_scope_prompt(
            assigned_tasks=workflow_tasks
        )

        agent_prompt = f"""
        {scope_prompt}

        {original_prompt}
        """
```

---

### Dag 7: Skill Description Rewriting (2 uur)

**Concept:** Betere agent discoverability via automatisch bijgewerkte skill descriptions.

#### Te Implementeren: SkillDescriptionService

**File:** `backend/app/services/skill_description_service.py`

```python
class SkillDescriptionService:
    """
    Houdt agent skill descriptions up-to-date op basis van:
    1. Uitgevoerde taken (success/failure patterns)
    2. Feedback van users
    3. Self-questioning sessions
    """

    async def update_skill_descriptions(
        self,
        agent_id: str
    ) -> UpdatedSkills:
        """
        Analyseer recente agent performance en update descriptions.
        """
        pass

    async def generate_improved_description(
        self,
        agent_id: str,
        recent_successes: List[TaskResult],
        recent_failures: List[TaskResult]
    ) -> str:
        """
        Genereer verbeterde skill description op basis van outcomes.
        """
        pass
```

#### Nieuwe Command: /improve-skills

**API Endpoint:** `POST /api/agents/{agent_id}/improve-skills`

```python
@router.post("/agents/{agent_id}/improve-skills")
async def improve_agent_skills(
    agent_id: str,
    focus: Optional[str] = None,
    workflow: Optional[str] = None
):
    """
    Trigger skill improvement voor een agent.

    Args:
        agent_id: Agent naam (felix, quinn, etc.)
        focus: Focus area (architecture, security, etc.)
        workflow: Specific workflow type
    """
    pass
```

---

### Dag 8-9: Spec Shaping Loop (4 uur)

**Concept:** Iteratieve spec verbetering tot spec voldoet aan criteria.

#### Te Implementeren: SpecShapingService

**File:** `backend/app/services/spec_shaping_service.py`

```python
class SpecShapingService:
    """
    Implementeert een iteratieve spec-verbetering loop:

    1. SHAPE:    Eerste spec versie genereren
    2. VERIFY:   Spec valideren tegen criteria
    3. IMPROVE:  Spec verbeteren op basis van feedback
    4. REPEAT:   Tot spec voldoet of max iterations bereikt
    """

    MAX_ITERATIONS = 3

    VERIFICATION_CRITERIA = {
        "completeness": {
            "has_problem_statement": True,
            "has_user_stories": True,
            "has_acceptance_criteria": True,
            "has_constraints": True,
            "has_success_metrics": True,
        },
        "clarity": {
            "no_ambiguous_terms": True,
            "specific_numbers": True,  # "fast" → "<200ms"
            "defined_scope": True,
        },
        "feasibility": {
            "has_tech_stack": True,
            "has_dependencies": True,
            "has_risk_assessment": True,
        }
    }

    async def shape_spec(
        self,
        initial_input: str,
        context: Dict[str, Any]
    ) -> ShapedSpec:
        """
        Run de complete spec shaping loop.
        """
        spec = await self._generate_initial_spec(initial_input, context)

        for iteration in range(self.MAX_ITERATIONS):
            verification = await self._verify_spec(spec)

            if verification.passes_all:
                return ShapedSpec(
                    content=spec,
                    iterations=iteration + 1,
                    verification=verification
                )

            spec = await self._improve_spec(spec, verification.feedback)

        # Max iterations reached
        return ShapedSpec(
            content=spec,
            iterations=self.MAX_ITERATIONS,
            verification=verification,
            needs_human_review=True
        )

    async def _verify_spec(self, spec: str) -> VerificationResult:
        """Valideer spec tegen criteria."""
        pass

    async def _improve_spec(
        self,
        spec: str,
        feedback: List[str]
    ) -> str:
        """Verbeter spec op basis van feedback."""
        pass
```

#### Integratie in BMAD Workflows

```python
class BMADBrownPaperWorkflow:

    async def generate_specification(self, session_id: str):
        # Use spec shaping instead of one-shot generation
        shaping_service = SpecShapingService()

        shaped_spec = await shaping_service.shape_spec(
            initial_input=session.answers_summary,
            context={
                "project_name": session.project_name,
                "migration_analysis": session.migration_analysis,
            }
        )

        if shaped_spec.needs_human_review:
            session.status = "human_review_needed"

        session.specification = shaped_spec.content
```

---

### Dag 10: Quick Spec Templates (2 uur)

**Concept:** Snelle templates voor veelvoorkomende taken.

#### Te Maken: Quick Spec Templates

**File:** `backend/app/templates/quick_specs/`

```
quick_specs/
├── bug-fix.md
├── enhancement.md
├── maintenance.md
├── hotfix.md
└── refactoring.md
```

#### Bug-Fix Template (Voorbeeld)

```markdown
# Bug Fix Specification

## Bug Details
- **Bug ID:** {{bug_id}}
- **Severity:** {{severity}}
- **Reported By:** {{reporter}}
- **Date Reported:** {{date}}

## Problem Description
{{description}}

## Steps to Reproduce
1. {{step_1}}
2. {{step_2}}
3. {{step_3}}

## Expected Behavior
{{expected}}

## Actual Behavior
{{actual}}

## Root Cause Analysis
{{root_cause}}

## Proposed Fix
{{fix_description}}

## Files to Modify
- {{file_1}}
- {{file_2}}

## Acceptance Criteria
- [ ] Bug no longer reproducible
- [ ] No regression in related functionality
- [ ] Unit tests added for the fix
- [ ] Integration tests pass

## Testing Notes
{{testing_notes}}
```

#### API Endpoints

```python
# GET /api/templates/quick-specs
# List available quick spec templates

# GET /api/templates/quick-specs/{template_type}
# Get template content

# POST /api/templates/quick-specs/{template_type}/fill
# Fill template with provided values
```

---

## Database Changes

### Migration 023: Standards & Spec Shaping

```sql
-- Standards loaded per workflow execution
CREATE TABLE workflow_standards_usage (
    id SERIAL PRIMARY KEY,
    workflow_execution_id UUID NOT NULL,
    workflow_type VARCHAR(50) NOT NULL,
    standards_loaded JSONB NOT NULL,  -- {"global": [...], "backend": [...]}
    loaded_at TIMESTAMP DEFAULT NOW()
);

-- Spec shaping iterations
CREATE TABLE spec_shaping_iterations (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    iteration_number INTEGER NOT NULL,
    spec_content TEXT NOT NULL,
    verification_result JSONB NOT NULL,
    feedback JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent skill updates
CREATE TABLE agent_skill_updates (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    old_description TEXT,
    new_description TEXT NOT NULL,
    trigger_reason VARCHAR(100),  -- 'self_questioning', 'user_feedback', 'performance_analysis'
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Reusable components registry
CREATE TABLE reusable_components (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    component_type VARCHAR(50) NOT NULL,  -- 'service', 'utility', 'pattern'
    description TEXT NOT NULL,
    source_project_id INTEGER REFERENCES projects(id),
    tags JSONB,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Quick spec templates
CREATE TABLE quick_spec_templates (
    id SERIAL PRIMARY KEY,
    template_type VARCHAR(50) NOT NULL UNIQUE,
    template_content TEXT NOT NULL,
    variables JSONB NOT NULL,  -- Required variables
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/standards` | GET | List all standards |
| `/api/standards/{workflow_type}` | GET | Get standards for workflow |
| `/api/standards/validate` | POST | Validate project against standards |
| `/api/validators/visual-assets` | POST | Validate visual assets |
| `/api/validators/reusability` | POST | Check for reusable components |
| `/api/agents/{id}/improve-skills` | POST | Trigger skill improvement |
| `/api/spec-shaping/shape` | POST | Run spec shaping loop |
| `/api/spec-shaping/{session_id}/iterations` | GET | Get shaping iterations |
| `/api/templates/quick-specs` | GET | List quick spec templates |
| `/api/templates/quick-specs/{type}` | GET | Get specific template |
| `/api/templates/quick-specs/{type}/fill` | POST | Fill template |

---

## Deliverables Checklist

### Week 59

- [ ] `.standards/` folder met 15+ markdown bestanden
- [ ] `StandardsLoaderService` met workflow mapping
- [ ] `VisualAssetValidator` met quality gate integratie
- [ ] `ReusabilityAnalyzer` met ChromaDB integratie
- [ ] Design-first enforcement in BMAD workflows
- [ ] 2 API endpoints voor standards

### Week 60

- [ ] `ScopeEnforcer` met prompt injection
- [ ] `SkillDescriptionService` met Self-Evolution integratie
- [ ] `/improve-skills` command
- [ ] `SpecShapingService` met iteratieve loop
- [ ] 5 Quick Spec templates
- [ ] Migration 023
- [ ] 8+ API endpoints

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Standards loaded per workflow | 100% | Logging |
| Spec shaping iterations avg | <2 | Database |
| Scope violations detected | >80% | Validation |
| Skill descriptions updated | 10/week | Agent logs |
| Quick spec usage | >20/week | API logs |
| Visual asset warnings | Tracked | Quality Gates |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Standards te restrictief | Agent output quality drops | Start met warnings, niet blocking |
| Spec shaping te traag | UX impact | Max 3 iterations, cache results |
| Scope enforcement te strict | Missed improvements | Log suggestions, don't block |
| ChromaDB dependency | Service availability | Graceful degradation |

---

## Dependencies

- ChromaDB running (voor reusability search)
- Ollama models beschikbaar
- Frontend dashboard updates (optioneel)

---

*Document aangemaakt: 2025-12-09*
*Laatste update: 2025-12-09*
*Status: PLANNING*
