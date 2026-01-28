# Extraction Workflows - Complete Documentation

**Datum**: 2026-01-28
**Status**: ACTIEF
**Versie**: 1.0

---

## 1. Overzicht

De Extraction module bevat services voor het extraheren van business logica, user stories, en requirements uit code.

| Service | Doel | Key Features |
|---------|------|--------------|
| **DeepExtractionService** | 6-cycle LLM council extraction | Multi-provider consensus |
| **HierarchicalStoryExtractionService** | Hiërarchische story extractie | Epics → Features → Stories → Tasks |
| **ExtractionIntegrationService** | Kanban & onboarding integratie | Import naar projecten |
| **UILayerExtractionService** | UI component mapping | Legacy → Modern mapping |
| **ExtractionLLMAdapter** | LLM provider abstraction | Tier-based provider selection |

---

## 2. Architectuur

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTRACTION ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     API LAYER                                ││
│  │  /api/deep-extraction  /api/hierarchical-extraction          ││
│  │  /api/hybrid-extraction /api/migration/{id}/ui-extraction    ││
│  └──────────────────────────┬──────────────────────────────────┘│
│                             │                                    │
│  ┌──────────────────────────┼──────────────────────────────────┐│
│  │                          ▼                                   ││
│  │  ┌────────────────────────────────────────────────────────┐ ││
│  │  │            DeepExtractionService (Main)                │ ││
│  │  │  • 6-cycle extraction pipeline                         │ ││
│  │  │  • LLM Council consensus building                      │ ││
│  │  │  • Conflict detection & resolution                     │ ││
│  │  └────────────┬───────────────────────┬───────────────────┘ ││
│  │               │                       │                      ││
│  │               ▼                       ▼                      ││
│  │  ┌────────────────────┐  ┌────────────────────────────────┐ ││
│  │  │   Hierarchical     │  │   ExtractionLLMAdapter         │ ││
│  │  │   StoryExtraction  │  │   (Multi-provider)             │ ││
│  │  │   Service          │  │   ├─ Ollama (FREE)             │ ││
│  │  │   • 4-level output │  │   ├─ Groq (BASIC)              │ ││
│  │  │   • CiRA relations │  │   ├─ Gemini (STANDARD)         │ ││
│  │  └─────────┬──────────┘  │   ├─ OpenAI (PROFESSIONAL)     │ ││
│  │            │             │   └─ Anthropic (PREMIUM)       │ ││
│  │            │             └────────────────────────────────┘ ││
│  │            │                                                 ││
│  │            ▼                                                 ││
│  │  ┌────────────────────────────────────────────────────────┐ ││
│  │  │         ExtractionIntegrationService                   │ ││
│  │  │  • Kanban board import                                 │ ││
│  │  │  • Project onboarding                                  │ ││
│  │  │  • Requirements linking                                │ ││
│  │  └────────────────────────────────────────────────────────┘ ││
│  │                                                              ││
│  │  ┌────────────────────────────────────────────────────────┐ ││
│  │  │           UILayerExtractionService                     │ ││
│  │  │  • Legacy UI component detection                       │ ││
│  │  │  • Modern framework mapping                            │ ││
│  │  │  • Design token extraction                             │ ││
│  │  └────────────────────────────────────────────────────────┘ ││
│  │                                                              ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Deep Extraction Pipeline (6 Cycles)

De kern van de extractie is een 6-cycle pipeline met LLM Council consensus:

```
┌─────────────────────────────────────────────────────────────────┐
│                  DEEP EXTRACTION 6-CYCLE PIPELINE                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [INPUT] source_path, tech_stack, tier (FREE/BASIC/STANDARD/    │
│          PROFESSIONAL/PREMIUM)                                   │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ CYCLE 0: INITIALIZATION                                      ││
│  │ • Chunk source code into analyzable units                    ││
│  │ • Select providers based on tier                             ││
│  │ • Initialize extraction context                              ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ CYCLE 1: INDEPENDENT ANALYSIS                                ││
│  │ • Each LLM analyzes independently                            ││
│  │ • Extract: business_logic, code_structure, architecture      ││
│  │ • Providers run in parallel                                  ││
│  │ • Output: Initial findings per provider                      ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ CYCLE 2: CROSS-ENRICHMENT                                    ││
│  │ • LLMs see each other's findings                             ││
│  │ • Identify gaps and contradictions                           ││
│  │ • Add missing insights                                       ││
│  │ • Output: Enriched findings                                  ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ CYCLE 3: CONFLICT DETECTION                                  ││
│  │ • Compare all findings                                       ││
│  │ • Detect: priority conflicts, complexity conflicts           ││
│  │ • Flag items needing human review                            ││
│  │ • Output: Conflict report                                    ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ CYCLE 4: CONSENSUS BUILDING                                  ││
│  │ • Synthesize findings into consensus                         ││
│  │ • Calculate confidence scores                                ││
│  │ • Auto-accept high-confidence items                          ││
│  │ • Output: Consensus items                                    ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ CYCLE 5: HUMAN REVIEW (Conditional)                          ││
│  │ • Present conflicts for human decision                       ││
│  │ • Accept/reject/modify suggestions                           ││
│  │ • Record decisions for learning                              ││
│  │ • Output: Final validated items                              ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ CYCLE 6: OUTPUT CONSOLIDATION                                ││
│  │ • Generate final report                                      ││
│  │ • Structure: Epics → Features → Stories → Tasks              ││
│  │ • Include: confidence scores, source references              ││
│  │ • Output: ExtractionResult                                   ││
│  └─────────────────────────────────────────────────────────────┘│
│     │                                                            │
│     ▼                                                            │
│  [OUTPUT] ExtractionResult with:                                │
│    • epics[], features[], stories[], tasks[]                    │
│    • confidence_scores                                          │
│    • conflicts_resolved, human_review_items                     │
│    • cost_usd, tokens_used                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Tier Configuration

| Tier | Prijs | Providers | Confidence Target | Max Cycles |
|------|-------|-----------|-------------------|------------|
| **FREE** | $0 | Ollama (3 models) | 60% | 3 |
| **BASIC** | $5 | Ollama + Groq | 70% | 4 |
| **STANDARD** | $15 | + Gemini | 80% | 5 |
| **PROFESSIONAL** | $50 | + OpenAI | 90% | 6 |
| **PREMIUM** | $150 | + Anthropic | 95% | 6 |

### Provider Mapping per Tier

```python
TIER_PROVIDERS = {
    ExtractionTier.FREE: [
        "ollama/qwen2.5-coder:7b",
        "ollama/codellama:13b",
        "ollama/deepseek-coder:6.7b"
    ],
    ExtractionTier.BASIC: [
        ...FREE providers,
        "groq/llama-3.1-70b-versatile",
        "groq/mixtral-8x7b-32768"
    ],
    ExtractionTier.STANDARD: [
        ...BASIC providers,
        "gemini/gemini-1.5-flash",
        "gemini/gemini-1.5-pro"
    ],
    ExtractionTier.PROFESSIONAL: [
        ...STANDARD providers,
        "openai/gpt-4o",
        "openai/gpt-4o-mini"
    ],
    ExtractionTier.PREMIUM: [
        ...PROFESSIONAL providers,
        "anthropic/claude-3-5-sonnet",
        "anthropic/claude-3-5-haiku"
    ]
}
```

---

## 5. Hierarchical Story Extraction

Extraheert een hiërarchische structuur uit code:

```
┌─────────────────────────────────────────────────────────────────┐
│            HIERARCHICAL EXTRACTION OUTPUT                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  System Level (Project Overview)                                │
│       │                                                          │
│       └── EPIC: [Business Domain]                               │
│              │                                                   │
│              ├── FEATURE: [Capability]                          │
│              │      │                                            │
│              │      ├── STORY: [User Requirement]               │
│              │      │      │                                     │
│              │      │      ├── TASK: [Implementation Step]      │
│              │      │      └── TASK: [Implementation Step]      │
│              │      │                                            │
│              │      └── STORY: [User Requirement]               │
│              │             └── TASK: [Implementation Step]      │
│              │                                                   │
│              └── FEATURE: [Capability]                          │
│                     └── STORY: [User Requirement]               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Extraction Levels

| Level | Output | Source Analysis |
|-------|--------|-----------------|
| **System** | Project overview | Full codebase scan |
| **Module** | Epics per domain | Directory/namespace clustering |
| **Class** | Features per module | Class/interface analysis |
| **Function** | Stories/tasks per feature | Method/function extraction |

### CiRA Integration

De Hierarchical Extraction integreert met CiRA (Causal Relation Analysis):

```python
CausalDependencyInfo:
    cause: str           # Triggering story/feature
    effect: str          # Dependent story/feature
    confidence: float    # Relation confidence (0-1)
    type: str           # "enables", "blocks", "requires"
```

---

## 6. UI Layer Extraction

Extraheert UI componenten uit legacy code en mapt naar moderne frameworks:

### Supported Legacy UI Types

| Type | Extensions | Components Detected |
|------|------------|---------------------|
| **WebForms** | .aspx, .ascx, .master | GridView, FormView, Repeater |
| **Classic ASP** | .asp | Form elements, tables |
| **WPF/XAML** | .xaml | Controls, layouts |
| **Razor** | .cshtml, .vbhtml | Components, partials |

### Modern Framework Mapping

```
┌─────────────────────────────────────────────────────────────────┐
│                 UI COMPONENT MAPPING                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LEGACY (WebForms)              MODERN (React)                  │
│  ─────────────────              ────────────────                 │
│  GridView         ──────────▶   DataGrid / AG-Grid              │
│  FormView         ──────────▶   React Hook Form                 │
│  DropDownList     ──────────▶   Select / Combobox               │
│  TextBox          ──────────▶   Input                           │
│  Button           ──────────▶   Button                          │
│  Panel            ──────────▶   Card / Box                      │
│  Repeater         ──────────▶   List / Map                      │
│  Calendar         ──────────▶   DatePicker                      │
│  TreeView         ──────────▶   Tree                            │
│  Menu             ──────────▶   Navigation / Menu               │
│                                                                  │
│  Complexity Assessment:                                         │
│  ├─ Trivial: Direct 1:1 mapping                                │
│  ├─ Low: Minor adjustments needed                               │
│  ├─ Medium: Component restructuring                             │
│  └─ High: Complete reimplementation                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Design Token Extraction

```python
DesignToken:
    name: str           # "primary-color", "spacing-md"
    type: DesignTokenType  # COLOR, SPACING, TYPOGRAPHY, etc.
    value: str          # "#1976d2", "16px"
    source_file: str    # Where token was found
```

---

## 7. API Endpoints

### Deep Extraction

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/deep-extraction/sessions` | Start nieuwe extractie sessie |
| GET | `/api/deep-extraction/sessions/{id}` | Haal sessie status op |
| POST | `/api/deep-extraction/sessions/{id}/run` | Start extractie run |
| GET | `/api/deep-extraction/sessions/{id}/conflicts` | Haal conflicts op |
| POST | `/api/deep-extraction/sessions/{id}/resolve` | Resolve conflict |

### Hierarchical Extraction

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/hierarchical-extraction/extract` | Start extractie |
| GET | `/api/hierarchical-extraction/{id}/status` | Haal status op |
| GET | `/api/hierarchical-extraction/{id}/results` | Haal resultaten op |
| POST | `/api/hierarchical-extraction/{id}/export` | Export naar format |

### Hybrid Extraction

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/hybrid-extraction/analyze` | Combineer deep + hierarchical |
| GET | `/api/hybrid-extraction/{id}/report` | Genereer rapport |

### UI Extraction (via Migration)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/migration/{id}/ui-extraction/extract` | Extract UI components |
| POST | `/api/migration/{id}/ui-extraction/design-tokens` | Extract design tokens |
| POST | `/api/migration/{id}/ui-extraction/component-mappings` | Generate mappings |
| GET | `/api/migration/{id}/ui-extraction/report` | Get UI report |

---

## 8. Test Coverage

### 8.1 Bestaande Unit Tests

| Test File | Coverage | Status |
|-----------|----------|--------|
| `tests/unit/extraction/test_deep_extraction_cycles.py` | Cycles 1-2 | ✅ ACTIEF |
| `tests/unit/extraction/test_deep_extraction_cycles_3_5.py` | Cycles 3-5 | ✅ ACTIEF |
| `tests/unit/extraction/test_deep_extraction_cycle0.py` | Initialization | ✅ ACTIEF |
| `tests/unit/extraction/test_hierarchical_story_extraction.py` | 4-level extraction | ✅ ACTIEF |
| `tests/unit/extraction/test_extraction_integration.py` | Kanban import | ✅ ACTIEF |
| `tests/unit/extraction/test_llm_extraction.py` | LLM adapter | ✅ ACTIEF |
| `tests/unit/extraction/test_business_logic_extraction.py` | Business rules | ✅ ACTIEF |
| `tests/unit/extraction/test_requirements_extraction.py` | Requirements | ✅ ACTIEF |

### 8.2 Bestaande Integration Tests

| Test File | Coverage | Status |
|-----------|----------|--------|
| `tests/integration/extraction/test_deep_extraction_api.py` | API endpoints | ✅ ACTIEF |
| `tests/integration/extraction/test_hybrid_extraction_api.py` | Combined extraction | ✅ ACTIEF |
| `tests/integration/extraction/test_extraction_with_existing_components.py` | Existing code | ✅ ACTIEF |

### 8.3 Test Gaps (Te Implementeren)

#### Unit Tests Nodig:

| Test | Prioriteit | Reden |
|------|------------|-------|
| `test_ui_layer_extraction.py` | HOOG | UI component mapping |
| `test_design_token_extraction.py` | MEDIUM | Design tokens |
| `test_cycle_6_output.py` | HOOG | Output consolidation |
| `test_tier_provider_selector.py` | MEDIUM | Provider selection logic |

#### Integration Tests Nodig:

| Test | Prioriteit | Reden |
|------|------------|-------|
| `test_deep_extraction_full_pipeline.py` | HOOG | Complete 6-cycle E2E |
| `test_extraction_to_kanban_flow.py` | HOOG | Kanban import E2E |
| `test_extraction_multi_provider.py` | MEDIUM | Multi-LLM consensus |
| `test_extraction_error_recovery.py` | MEDIUM | Error handling |

---

## 9. Dependencies

### Shared Services

```
Extraction Services
       │
       ├── LLMCouncilService (consensus building)
       ├── TierProviderSelector (LLM selection)
       ├── CiRAAnalyzerService (causal relations)
       ├── CodeChunkingService (code splitting)
       ├── INVESTValidatorService (story validation)
       └── KanbanService (import destination)
```

### External Dependencies

| Dependency | Purpose | Tier Required |
|------------|---------|---------------|
| Ollama | Local LLM execution | FREE+ |
| Groq API | Fast cloud inference | BASIC+ |
| Google AI (Gemini) | Large context | STANDARD+ |
| OpenAI API | GPT-4o models | PROFESSIONAL+ |
| Anthropic API | Claude models | PREMIUM |

---

## 10. Integration met Brown Paper

De Extraction services worden aangeroepen vanuit de Brown Paper workflow:

```
Brown Paper Workflow
       │
       ├── Phase 3: Hierarchical Extraction
       │      └── HierarchicalStoryExtractionService
       │
       ├── Phase 4: Deep Extraction
       │      └── DeepExtractionService (6 cycles)
       │
       └── Phase 5: Estimation
              └── Uses extraction results
```

---

## 11. Volgende Stappen

### Taak #8: Unit Tests Extraction Services

- [ ] `test_ui_layer_extraction.py`
- [ ] `test_design_token_extraction.py`
- [ ] `test_cycle_6_output.py`
- [ ] `test_tier_provider_selector.py`
- [ ] `test_component_mapping.py`

### Taak #9: Integration Tests Extraction Workflows

- [ ] `test_deep_extraction_full_pipeline.py`
- [ ] `test_extraction_to_kanban_flow.py`
- [ ] `test_extraction_multi_provider.py`
- [ ] `test_extraction_error_recovery.py`
- [ ] `test_brown_paper_extraction_integration.py`

---

## 12. Changelog

| Datum | Versie | Wijziging |
|-------|--------|-----------|
| 2026-01-28 | 1.0 | Initiële documentatie |
