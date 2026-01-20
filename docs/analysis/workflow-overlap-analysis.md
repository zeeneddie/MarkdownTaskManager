# Workflow Overlap Analyse: Migration vs Brown Paper

> Analyse datum: 2026-01-19

## 1. Stage Vergelijking Matrix

### Migration Workflow Stages
| Stage | Agents | Input | Output |
|-------|--------|-------|--------|
| `generate_specification` | Peter, Betty | answers (8 vragen), technical_analysis | constitution, problem_statement, user_stories, user_personas, business_requirements, success_criteria, business_case |
| `generate_tasks` | Felix, Paul | specification | epics, features, stories, tasks, migration_waves, architecture_decisions |

### Brown Paper Workflow Stages
| Stage | Agents | Input | Output |
|-------|--------|-------|--------|
| `domain_extraction` | Peter, Betty | code_analysis | domains, domain_boundaries, business_capabilities |
| `story_extraction` | Peter | domains | epics, stories, story_count |
| `deep_extraction` | Felix, Quinn, Marcus | stories, code_analysis | architecture_insights, quality_findings, maintenance_recommendations, council_consensus |

---

## 2. Overlap Analyse

### 2.1 generate_specification vs domain_extraction

| Aspect | Migration: generate_specification | Brown Paper: domain_extraction | Overlap |
|--------|-----------------------------------|-------------------------------|---------|
| **Agents** | Peter, Betty | Peter, Betty | **100%** |
| **Peter Activity** | `activity: "constitution"` | `activity: "domain_extraction"` | Verschilt |
| **Betty Activity** | `analysis_type: "requirements"` | Geen specifieke activity | Verschilt |
| **Input Source** | User answers (top-down) | Code analysis (bottom-up) | **0%** |
| **Output: Stories** | user_stories | Geen | Migration heeft meer |
| **Output: Domains** | Geen | domains, domain_boundaries | Brown Paper heeft meer |
| **Output: Business** | business_case, business_requirements | business_capabilities | ~50% overlap |

**Conclusie**: Zelfde agents, VERSCHILLENDE input bronnen en doelen.

---

### 2.2 generate_tasks vs story_extraction + deep_extraction

| Aspect | Migration: generate_tasks | Brown Paper: story_extraction | Brown Paper: deep_extraction | Overlap |
|--------|--------------------------|------------------------------|------------------------------|---------|
| **Agents** | Felix, Paul | Peter | Felix, Quinn, Marcus | Gedeeltelijk |
| **Epic/Story Output** | epics, features, stories | epics, stories | Geen | **80%** |
| **Architecture** | architecture_decisions | Geen | architecture_insights | ~60% |
| **Quality** | Geen | Geen | quality_findings | Uniek BP |
| **Maintenance** | Geen | Geen | maintenance_recommendations | Uniek BP |
| **Planning** | migration_waves, tasks | Geen | Geen | Uniek MIG |

**Conclusie**: Significante overlap in epic/story generatie, maar Brown Paper heeft diepere analyse.

---

## 3. Functionele Overlap Score

```
┌─────────────────────────────────────────────────────────────────┐
│                    OVERLAP MATRIX                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Migration                    Brown Paper                       │
│  ──────────                   ───────────                       │
│                                                                 │
│  generate_specification  ←──30%──→  domain_extraction           │
│         │                              │                        │
│         │ (agents overlap,             │ (agents overlap,       │
│         │  different input)            │  code-based input)     │
│         ▼                              ▼                        │
│  generate_tasks          ←──70%──→  story_extraction            │
│         │                              │                        │
│         │                              ▼                        │
│         └────────────────←──40%──→  deep_extraction             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Overlap Percentages:
- **generate_specification ↔ domain_extraction**: 30% (zelfde agents, andere input)
- **generate_tasks ↔ story_extraction**: 70% (beide genereren epics/stories)
- **generate_tasks ↔ deep_extraction**: 40% (architecture overlap)

---

## 4. Output Kwaliteit Vergelijking

### 4.1 Welke levert de meest verfijnde output?

| Criterium | Migration Workflow | Brown Paper Workflow | Winnaar |
|-----------|-------------------|---------------------|---------|
| **Story Detail** | Basic stories van user answers | Stories van code + domain analyse | **Brown Paper** |
| **Architecture Insight** | High-level decisions | Deep insights + quality + maintenance | **Brown Paper** |
| **Business Context** | Sterk (8 vragen) | Matig (afgeleid van code) | **Migration** |
| **Technical Accuracy** | Gebaseerd op user input | Gebaseerd op echte code | **Brown Paper** |
| **Planning Detail** | migration_waves, tasks | Alleen epics/stories | **Migration** |
| **Quality Analysis** | Geen | quality_findings, council review | **Brown Paper** |

### 4.2 Conclusie Verfijning

**Brown Paper levert meer verfijnde technische output** omdat:
1. Input is de **daadwerkelijke code** (niet user assumptions)
2. **LLM Council** (Felix, Quinn, Marcus) doet multi-perspectief review
3. **Quality findings** en **maintenance recommendations** zijn uniek
4. **Domain extraction** is evidence-based

**Migration levert betere business context** omdat:
1. **8 strategische vragen** geven complete business picture
2. **Stakeholder analysis** en **success criteria** zijn expliciet
3. **Migration waves** zijn planning-specifiek

---

## 5. Probleem: Dubbele Functionaliteit

### Huidige Situatie
```
Migration Workflow                    Brown Paper Workflow
─────────────────                    ────────────────────
    │                                      │
    ▼                                      ▼
┌──────────────────┐              ┌──────────────────┐
│ generate_        │              │ domain_          │
│ specification    │──OVERLAP──→  │ extraction       │
│ (Peter, Betty)   │              │ (Peter, Betty)   │
└──────────────────┘              └──────────────────┘
    │                                      │
    ▼                                      ▼
┌──────────────────┐              ┌──────────────────┐
│ generate_tasks   │              │ story_extraction │
│ (Felix, Paul)    │──OVERLAP──→  │ (Peter)          │
└──────────────────┘              └──────────────────┘
                                          │
                                          ▼
                                  ┌──────────────────┐
                                  │ deep_extraction  │
                                  │ (Felix,Quinn,    │
                                  │  Marcus)         │
                                  └──────────────────┘
```

### Problemen
1. **Code duplicatie** in agent calls (Peter, Betty, Felix)
2. **Inconsistente output** structuren
3. **Geen hergebruik** van Brown Paper's diepere analyse in Migration
4. **Maintenance burden** - wijzigingen moeten op 2 plekken

---

## 6. ADVIES: Consolidatie Strategie

### Optie A: Unified Extraction Service (AANBEVOLEN)

Maak een **gedeelde ExtractionService** die beide workflows gebruiken:

```python
class UnifiedExtractionService:
    """
    Unified extraction pipeline for both Migration and Brown Paper workflows.

    Modes:
    - TOP_DOWN: Migration (user answers → specification)
    - BOTTOM_UP: Brown Paper (code → domains → stories)
    - HYBRID: Combine both for maximum refinement
    """

    async def extract_domains(
        self,
        mode: ExtractionMode,
        code_analysis: Optional[Dict] = None,  # Bottom-up
        user_answers: Optional[Dict] = None,   # Top-down
    ) -> DomainExtractionResult:
        """Single domain extraction used by both workflows."""
        pass

    async def generate_stories(
        self,
        domains: List[Domain],
        context: StoryContext,
    ) -> StoryGenerationResult:
        """Single story generation used by both workflows."""
        pass

    async def deep_analysis(
        self,
        stories: List[Story],
        code_analysis: Optional[Dict] = None,
    ) -> DeepAnalysisResult:
        """Optional deep analysis (Brown Paper adds value here)."""
        pass
```

### Optie B: Brown Paper als Foundation

Migration workflow **hergebruikt** Brown Paper stages:

```python
class MigrationOrchestrator(WorkflowOrchestrator):

    async def _execute_specification(self, context):
        # 1. Eerst Brown Paper's domain extraction (als code beschikbaar)
        if context.has_legacy_code:
            bp_orchestrator = BrownPaperOrchestrator()
            domain_result = await bp_orchestrator._execute_domain_extraction(context)
            story_result = await bp_orchestrator._execute_story_extraction(context)

            # 2. Verrijk met user answers
            enriched = self._enrich_with_answers(
                domain_result,
                story_result,
                context.answers
            )
            return enriched
        else:
            # Fallback naar pure top-down
            return await self._execute_pure_specification(context)
```

### Optie C: Shared Stage Library

Extraheer stages naar een gedeelde library:

```
backend/app/confucius/
├── workflows/
│   ├── brown_paper.py      # Orchestration only
│   ├── migration.py        # Orchestration only
│   └── quality.py
├── stages/                  # NEW: Shared stages
│   ├── __init__.py
│   ├── domain_extraction.py    # Used by BP + MIG
│   ├── story_generation.py     # Used by BP + MIG
│   ├── deep_analysis.py        # Used by BP, optional for MIG
│   ├── estimation.py           # Used by BP + MIG
│   └── specification.py        # MIG-specific
└── extensions/
```

---

## 7. Aanbevolen Implementatie

### Fase 1: Shared Story Generation (Quick Win)

```python
# backend/app/confucius/stages/story_generation.py

class StoryGenerationStage:
    """
    Shared stage for epic/story generation.
    Used by both Migration and Brown Paper workflows.
    """

    def __init__(self, agents: List[str] = None):
        self.agents = agents or ["Peter"]

    async def execute(
        self,
        context: WorkflowContext,
        source: Literal["domains", "specification"],
    ) -> StoryGenerationResult:
        """
        Generate stories from either:
        - domains (Brown Paper path)
        - specification (Migration path)
        """
        if source == "domains":
            input_data = context.shared_data.get("domain_extraction_result", {})
            activity = "stories"
        else:
            input_data = context.shared_data.get("generate_specification_result", {})
            activity = "constitution"

        # Same Peter call, different context
        peter_result = await self._call_peter(input_data, activity, context)

        return StoryGenerationResult(
            epics=peter_result.get("epics", []),
            stories=peter_result.get("stories", []),
            story_count=len(peter_result.get("stories", [])),
            source=source,
        )
```

### Fase 2: Add Deep Analysis to Migration (Value Add)

Migration kan profiteren van Brown Paper's deep_extraction:

```python
# In migration.py, add optional stage

WorkflowStage(
    name="deep_analysis",  # NEW
    description="Optional deep analysis with LLM council",
    agents=["Felix", "Quinn", "Marcus"],
    required=False,  # Optional enhancement
    quality_threshold=0.85,
    depends_on=["generate_tasks"],
),
```

### Fase 3: Unified Domain Model

```python
# backend/app/confucius/models/extraction.py

@dataclass
class Domain:
    id: str
    name: str
    description: str
    boundaries: Dict[str, Any]
    capabilities: List[str]
    source: Literal["code_analysis", "user_answers", "hybrid"]

@dataclass
class Story:
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    domain_id: str
    confidence: float  # Higher for code-based extraction
    source: Literal["brown_paper", "migration", "hybrid"]
```

---

## 8. Impact Analyse

### Als we consolideren:

| Metric | Voor | Na | Verbetering |
|--------|------|-----|-------------|
| Lines of Code | ~800 | ~500 | -37% |
| Agent Calls | 6 duplicate | 3 shared | -50% |
| Test Coverage | 2 test suites | 1 unified | +maintainability |
| Feature Parity | Inconsistent | Consistent | +quality |

### Risico's:
1. **Breaking changes** in bestaande API's
2. **Test refactoring** nodig
3. **Migratie** van bestaande workflow data

---

## 9. Conclusie & Aanbeveling

### Antwoord op de vragen:

1. **Hoeveel overlap?**
   - ~50% functionele overlap
   - 70% overlap in story generation
   - 100% agent overlap (Peter, Betty, Felix)

2. **Welke levert meest verfijnde output?**
   - **Brown Paper** voor technische accuraatheid (code-based)
   - **Migration** voor business context (user-driven)
   - **Ideaal**: Combinatie van beide

3. **Beste oplossing?**

   **AANBEVELING: Optie A - Unified Extraction Service**

   Omdat:
   - Elimineert 50% code duplicatie
   - Maakt HYBRID mode mogelijk (beste van beide)
   - Consistent output format
   - Eén plek voor verbeteringen
   - Brown Paper's deep_extraction wordt optioneel voor Migration

### Prioriteit:
1. **Nu**: Shared StoryGenerationStage (quick win, 2-4 uur)
2. **Sprint 2**: Unified Domain Model (4-8 uur)
3. **Sprint 3**: Full UnifiedExtractionService (16-24 uur)
