# Dependency Matrix & Service Map

**Datum**: 2026-01-28
**Status**: ACTIEF
**Versie**: 1.0

---

## 1. Top-Level Service Dependencies

### 1.1 Brown Paper Service Dependencies

```
BrownPaperService (188KB)
├── ChromaService                      [persistence - vector DB]
├── ApplicationRegistryService         [project registry]
├── BrownPaperEstimationService       [function point estimation]
├── DependencyGraphService            [code dependency analysis]
├── CodeAnalysisAggregatorService     [multi-analyzer aggregation]
├── LayeredAnalysisService            [architecture layer detection]
├── HierarchicalStoryExtractionService [story extraction]
├── DeepExtractionService             [6-cycle LLM extraction]
└── BrownPaperIntegration             [stability helpers]
```

### 1.2 Deep Extraction Service Dependencies

```
DeepExtractionService
├── TierProviderSelector              [LLM provider selection]
├── ExtractionLLMAdapter              [LLM abstraction layer]
├── StaticAnalysisOrchestrator        [code analysis]
└── ConflictDetectorService           [conflict resolution]
```

### 1.3 Hierarchical Extraction Dependencies

```
HierarchicalStoryExtractionService
├── CodeAnalysisAggregatorService     [code metrics]
└── CiRAService                       [causal relation analysis]
```

---

## 2. Dependency Matrix (Services × Services)

| Service | BP | DE | HE | DG | CA | LA | EI | UI | QG |
|---------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **BrownPaperService (BP)** | - | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | ✓ |
| **DeepExtractionService (DE)** | - | - | - | - | - | - | - | - | - |
| **HierarchicalExtractionService (HE)** | - | - | - | - | ✓ | - | - | - | - |
| **DependencyGraphService (DG)** | - | - | - | - | - | - | - | - | - |
| **CodeAnalysisAggregatorService (CA)** | - | - | - | ✓ | - | - | - | - | - |
| **LayeredAnalysisService (LA)** | - | - | - | - | ✓ | - | - | - | - |
| **ExtractionIntegrationService (EI)** | - | ✓ | ✓ | - | - | - | - | - | - |
| **UILayerExtractionService (UI)** | - | - | - | - | - | - | - | - | - |
| **QualityGateService (QG)** | - | - | - | - | - | - | - | - | - |

**Legend**: ✓ = depends on

---

## 3. Workflow Dependencies

### 3.1 Brown Paper Workflow → Services

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BROWN PAPER SERVICE MAP                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    BrownPaperService (Main)                         │    │
│  │                         (188 KB)                                    │    │
│  └───────────────────────────────┬────────────────────────────────────┘    │
│                                  │                                          │
│       ┌────────────┬─────────────┼─────────────┬────────────┐              │
│       │            │             │             │            │              │
│       ▼            ▼             ▼             ▼            ▼              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │Dependency│  │  Code   │  │ Layered │  │Hierarch │  │  Deep   │         │
│  │  Graph  │  │Analysis │  │Analysis │  │ Story   │  │Extract  │         │
│  │ Service │  │Aggregator│  │ Service │  │Extract. │  │ Service │         │
│  │  (40KB) │  │ (45KB)  │  │ (35KB)  │  │ (52KB)  │  │ (85KB)  │         │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘         │
│       │            │            │            │            │              │
│       │            │            │            │            │              │
│       └────────────┴────────────┴────────────┴────────────┘              │
│                                  │                                          │
│                                  ▼                                          │
│                    ┌────────────────────────────┐                          │
│                    │    BrownPaperEstimation    │                          │
│                    │        Service (16KB)      │                          │
│                    └────────────────────────────┘                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Extraction Workflow → Services

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       EXTRACTION SERVICE MAP                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                  DeepExtractionService (Main)                       │    │
│  │                         (85 KB)                                     │    │
│  └───────────────────────────────┬────────────────────────────────────┘    │
│                                  │                                          │
│            ┌─────────────────────┼─────────────────────┐                   │
│            │                     │                     │                   │
│            ▼                     ▼                     ▼                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐        │
│  │ TierProvider     │  │ ExtractionLLM    │  │ ConflictDetector │        │
│  │ Selector         │  │ Adapter          │  │ Service          │        │
│  │                  │  │                  │  │                  │        │
│  │ • FREE tier      │  │ • Ollama         │  │ • Priority       │        │
│  │ • BASIC tier     │  │ • Groq           │  │ • Complexity     │        │
│  │ • STANDARD tier  │  │ • Gemini         │  │ • Consensus      │        │
│  │ • PROFESSIONAL   │  │ • OpenAI         │  │                  │        │
│  │ • PREMIUM tier   │  │ • Anthropic      │  │                  │        │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘        │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │              HierarchicalStoryExtractionService                     │    │
│  │                         (52 KB)                                     │    │
│  └───────────────────────────────┬────────────────────────────────────┘    │
│                                  │                                          │
│            ┌─────────────────────┴─────────────────────┐                   │
│            ▼                                           ▼                   │
│  ┌──────────────────┐                       ┌──────────────────┐          │
│  │ CodeAnalysis     │                       │ CiRAService      │          │
│  │ Aggregator       │                       │ (Causal          │          │
│  │ Service          │                       │  Relations)      │          │
│  └──────────────────┘                       └──────────────────┘          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Cross-Workflow Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CROSS-WORKFLOW DEPENDENCY GRAPH                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                          ┌─────────────────┐                                │
│                          │  API Endpoints  │                                │
│                          └────────┬────────┘                                │
│                                   │                                          │
│       ┌───────────────────────────┼───────────────────────────┐            │
│       │                           │                           │            │
│       ▼                           ▼                           ▼            │
│  ┌─────────┐               ┌─────────┐               ┌─────────┐          │
│  │ Brown   │◄──────────────│Migration│               │ Quality │          │
│  │ Paper   │               │Workflow │               │Workflow │          │
│  │Workflow │               │         │               │         │          │
│  └────┬────┘               └────┬────┘               └────┬────┘          │
│       │                         │                         │                │
│       │   ┌─────────────────────┴──────────────────┐     │                │
│       │   │                                        │     │                │
│       ▼   ▼                                        ▼     ▼                │
│  ┌──────────────┐                            ┌──────────────┐             │
│  │ Extraction   │                            │ Code Analysis│             │
│  │ Services     │                            │ Services     │             │
│  │              │                            │              │             │
│  │ ├─ Deep      │                            │ ├─ Dependency│             │
│  │ ├─ Hierarch. │◄───────────────────────────│ ├─ Aggregator│             │
│  │ └─ UI Layer  │                            │ └─ Layered   │             │
│  └──────────────┘                            └──────────────┘             │
│         │                                          │                       │
│         │                                          │                       │
│         └────────────────────┬─────────────────────┘                       │
│                              │                                              │
│                              ▼                                              │
│                    ┌──────────────────┐                                    │
│                    │   LLM Services   │                                    │
│                    │                  │                                    │
│                    │ ├─ LLM Council   │                                    │
│                    │ ├─ Ollama        │                                    │
│                    │ └─ Cloud APIs    │                                    │
│                    └──────────────────┘                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Shared Services Matrix

Services die door meerdere workflows worden gebruikt:

| Shared Service | Brown Paper | Migration | Green Paper | Quality | Kanban |
|----------------|:-----------:|:---------:|:-----------:|:-------:|:------:|
| **DependencyGraphService** | ✓ | ✓ | - | ✓ | - |
| **CodeAnalysisAggregatorService** | ✓ | ✓ | - | ✓ | - |
| **QualityGateService** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **INVESTValidatorService** | ✓ | ✓ | ✓ | - | ✓ |
| **AgentService** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **ChromaService** | ✓ | ✓ | ✓ | - | ✓ |
| **LLMCouncilService** | ✓ | - | - | - | - |
| **CiRAService** | ✓ | ✓ | - | - | - |

---

## 6. Database Dependencies

### Tables per Workflow

| Table | Brown Paper | Migration | Green Paper | Extraction |
|-------|:-----------:|:---------:|:-----------:|:----------:|
| `marqed_sessions` | ✓ | - | - | - |
| `marqed_answers` | ✓ | - | - | - |
| `migration_sessions` | - | ✓ | - | - |
| `green_paper_sessions` | - | - | ✓ | - |
| `extraction_sessions` | ✓ | - | - | ✓ |
| `extraction_results` | ✓ | - | - | ✓ |
| `workflow_contexts` | ✓ | ✓ | ✓ | - |
| `quality_scans` | ✓ | ✓ | - | - |
| `agent_tasks` | ✓ | ✓ | ✓ | - |

---

## 7. External API Dependencies

| External Service | Services Using It | Purpose |
|-----------------|-------------------|---------|
| **Ollama** | All extraction, agents | Local LLM inference |
| **Groq** | DeepExtraction (BASIC+) | Fast cloud inference |
| **Google AI** | DeepExtraction (STANDARD+) | Gemini models |
| **OpenAI** | DeepExtraction (PROFESSIONAL+) | GPT-4 models |
| **Anthropic** | DeepExtraction (PREMIUM) | Claude models |
| **ChromaDB** | BrownPaper, Search | Vector storage |
| **PostgreSQL** | All services | Primary database |
| **Redis** | Session, Cache | Caching |

---

## 8. Test Coverage Dependencies

### Unit Test → Service Mapping

| Test File | Services Covered |
|-----------|-----------------|
| `test_workflow_orchestrators.py` | All 4 orchestrators |
| `test_deep_extraction_cycles.py` | DeepExtractionService, TierProviderSelector |
| `test_hierarchical_story_extraction.py` | HierarchicalStoryExtractionService |
| `test_extraction_integration.py` | ExtractionIntegrationService |
| `test_brown_paper_enhanced.py` | BrownPaperService phases |

### Integration Test → Workflow Mapping

| Test File | Workflows Covered |
|-----------|------------------|
| `test_brown_paper_full_workflow.py` | Brown Paper E2E |
| `test_deep_extraction_full_pipeline.py` | Extraction 6-cycle |
| `test_restartable_workflows.py` | All workflows (recovery) |

---

## 9. Risk Analysis

### High-Impact Shared Services

Services waar wijzigingen meerdere workflows kunnen beïnvloeden:

| Service | Impact Score | Reason |
|---------|:------------:|--------|
| **QualityGateService** | 🔴 HIGH | Used by all workflows |
| **AgentService** | 🔴 HIGH | Used by all workflows |
| **CodeAnalysisAggregatorService** | 🟠 MEDIUM | Used by analysis workflows |
| **DependencyGraphService** | 🟠 MEDIUM | Used by analysis workflows |
| **ChromaService** | 🟡 LOW | Isolated vector storage |

### Recommended Testing Order

1. **Unit tests** voor shared services eerst
2. **Integration tests** per workflow
3. **Cross-workflow tests** voor gedeelde dependencies

---

## 10. Changelog

| Datum | Versie | Wijziging |
|-------|--------|-----------|
| 2026-01-28 | 1.0 | Initiële documentatie |
