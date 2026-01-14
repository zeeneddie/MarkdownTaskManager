# Fase 20: Brown Paper Enhanced (Week 128-129) COMPLETE

**Goal:** Integration of all available deep analysis services in BrownPaperService for complete legacy code analysis.
**Specification:** [docs/architecture/brown-paper-enhanced.md](../../architecture/brown-paper-enhanced.md)
**Status:** COMPLETE
**Origin:** Week 125 HCI-CRS Afspraak module analysis

---

## Problem Statement

BrownPaperService has its own simple regex-based analysis while 5 rich analysis services were developed in parallel:

```
BrownPaperService (CURRENT):
├── application_registry_service  ✅ (metadata)
├── brown_paper_estimation_service ✅ (FP/SP)
└── OWN regex analysis            ⚠️ (duplication)

AVAILABLE BUT NOT USED:
├── CodeAnalysisAggregatorService ❌ (complexity, coupling, cohesion)
├── DeepExtractionService         ❌ (multi-LLM council, INVEST)
├── HierarchicalStoryExtractionService ❌ (multi-level, CiRA)
├── LayeredAnalysisService        ❌ (VBScript, SWOT, stored procs)
└── DependencyGraphService        ❌ (graph structure, circular deps)
```

---

## 6-Phase Enhanced Workflow

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                    BROWN PAPER ENHANCED WORKFLOW                                │
│                                                                                 │
│  PHASE 1: CODE UNDERSTANDING                                                    │
│  ┌─────────────────┬─────────────────┬─────────────────┐                       │
│  │ DependencyGraph │ CodeAnalysis    │ LayeredAnalysis │                       │
│  │ Service         │ Aggregator      │ Service         │                       │
│  ├─────────────────┼─────────────────┼─────────────────┤                       │
│  │ • Graph struct  │ • Complexity    │ • VBScript      │                       │
│  │ • Circular deps │ • Coupling      │ • Stored procs  │                       │
│  │ • Fan-in/out    │ • Cohesion      │ • ASP patterns  │                       │
│  └─────────────────┴─────────────────┴─────────────────┘                       │
│                             │                                                   │
│  PHASE 2: DOMAIN EXTRACTION │ Agent: Peter (Product Owner)                      │
│  ┌──────────────────────────┴───────────────────────────────┐                  │
│  │ • Identify business domains from code patterns           │                  │
│  │ • Map to CAFCR categories                                │                  │
│  │ • Determine module boundaries                            │                  │
│  │ • Extract business rules (hybrid extractors)             │                  │
│  └──────────────────────────┬───────────────────────────────┘                  │
│                             │                                                   │
│  PHASE 3: HIERARCHICAL EXTRACTION │ Agent: Felix (Architect)                   │
│  ┌──────────────────────────┴───────────────────────────────┐                  │
│  │ HierarchicalStoryExtractionService:                      │                  │
│  │ • System-level → Epic                                    │                  │
│  │ • Module-level → Feature                                 │                  │
│  │ • Class-level → User Story                               │                  │
│  │ • Function-level → Task                                  │                  │
│  │ • CiRA causality relations                               │                  │
│  └──────────────────────────┬───────────────────────────────┘                  │
│                             │                                                   │
│  PHASE 4: DEEP EXTRACTION   │ Agent: Quinn (Quality) + LLM Council             │
│  ┌──────────────────────────┴───────────────────────────────┐                  │
│  │ DeepExtractionService:                                   │                  │
│  │ • Multi-tier LLM analysis (tier-aware)                   │                  │
│  │ • INVEST validation per story                            │                  │
│  │ • Conflict detection across extractors                   │                  │
│  │ • Confidence scoring                                     │                  │
│  └──────────────────────────┬───────────────────────────────┘                  │
│                             │                                                   │
│  PHASE 5: ESTIMATION        │ Agent: Eliza (Estimation)                        │
│  ┌──────────────────────────┴───────────────────────────────┐                  │
│  │ brown_paper_estimation_service (existing):               │                  │
│  │ • Function Points (IFPUG)                                │                  │
│  │ • Story Points                                           │                  │
│  │ • Effort estimation                                      │                  │
│  │ • Risk assessment (enhanced with complexity metrics)     │                  │
│  └──────────────────────────┬───────────────────────────────┘                  │
│                             │                                                   │
│  PHASE 6: OUTPUT            │ Agent: Diana (Documentation)                     │
│  ┌──────────────────────────┴───────────────────────────────┐                  │
│  │ Consolidated Output:                                     │                  │
│  │ • Dependency graph visualization data                    │                  │
│  │ • Epic/Feature/Story hierarchy                           │                  │
│  │ • Traceability matrix                                    │                  │
│  │ • Migration roadmap                                      │                  │
│  │ • Risk register                                          │                  │
│  │ • Estimation breakdown                                   │                  │
│  └──────────────────────────────────────────────────────────┘                  │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Assignments

| Phase | Primary Agent | Supporting Agents | Output |
|-------|---------------|-------------------|--------|
| **1. Code Understanding** | Miguel | Quinn | Metrics, graphs, patterns |
| **2. Domain Extraction** | Peter | Miguel | Business domains, CAFCR mapping |
| **3. Hierarchical Extraction** | Felix | Peter | Epic/Feature/Story/Task |
| **4. Deep Extraction** | Quinn | LLM Council | Validated, conflict-free backlog |
| **5. Estimation** | Eliza | Paul | FP, SP, effort, risk |
| **6. Output** | Diana | All | Consolidated documentation |

---

## Tier-Aware Analysis

| Tier | Services Used | Confidence Target |
|------|---------------|-------------------|
| **FREE** | DependencyGraph + CodeAnalysis (Ollama) | 60% |
| **BASIC** | + LayeredAnalysis (Groq, Qwen) | 70% |
| **STANDARD** | + HierarchicalExtraction (Gemini) | 80% |
| **PROFESSIONAL** | + DeepExtraction (GPT-5.2) | 90% |
| **PREMIUM** | + Human Review + Opus synthesis | 95% |

---

## Deliverables

### Week 128

| Component | Location | Description |
|-----------|----------|-------------|
| **BrownPaperService refactor** | `brown_paper_service.py` | Add service imports, orchestration |
| **Phase 1 Integration** | `brown_paper_service.py` | DependencyGraph + CodeAnalysis calls |
| **Phase 2-3 Integration** | `brown_paper_service.py` | Hierarchical extraction calls |
| **Unit Tests** | `tests/services/week128/` | 30+ tests |

### Week 129

| Component | Location | Description |
|-----------|----------|-------------|
| **Phase 4 Integration** | `brown_paper_service.py` | DeepExtraction + LLM Council |
| **Phase 5-6 Integration** | `brown_paper_service.py` | Estimation enhancement, output consolidation |
| **API Updates** | `brown_paper.py` | New endpoints for enhanced analysis |
| **Dashboard Updates** | `frontend/` | Visualization for enhanced output |
| **Integration Tests** | `tests/services/week129/` | E2E workflow tests |

---

## New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/brown-paper/bmad/{id}/enhanced-analyze` | POST | Full 6-phase analysis |
| `/api/brown-paper/bmad/{id}/dependency-graph` | GET | Graph visualization data |
| `/api/brown-paper/bmad/{id}/hierarchy` | GET | Epic/Feature/Story tree |
| `/api/brown-paper/bmad/{id}/conflicts` | GET | Detected conflicts |
| `/api/brown-paper/bmad/{id}/metrics` | GET | Code quality metrics |

---

## Success Criteria

| Criterion | Target |
|-----------|--------|
| **Service Integration** | 5 services connected |
| **Agent Coverage** | 6 agents in workflow |
| **Confidence Increase** | +20% vs current |
| **New Endpoints** | 5 new API endpoints |
| **Tests** | 60+ unit/integration tests |

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Fase 18 (CiRA) | COMPLETE | CiRA relations in hierarchical extraction |
| Fase 19 (Metrics) | COMPLETE | 5 HCI metrics analyzers with 5-star ratings |
| DeepExtractionService | EXISTS | Ready for integration |
| HierarchicalStoryExtractionService | EXISTS | Ready for integration |

---

← [Back to Overview](../phases-planned.md)
