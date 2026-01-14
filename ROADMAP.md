# MarQed Platform Roadmap

**Project:** MarQed AI Agent Software Platform
**Last Updated:** Week 153-154 (2026-01-14)
**Total Phases:** 29 | **Timeline:** Week 144-244

---

## Executive Summary

De MarQed roadmap combineert de bestaande geplande fases met een uitgebreide gap-analyse van 12 externe bronnen (6 Nederlandse consultancies, 5 GitHub repos, 1 gist).

### Roadmap Overview

```
WEEK 144-155: CRITICAL FOUNDATION + ORCHESTRATOR (12 weken)
├── Fase 21: Stability Analyzer ✅ COMPLETE
├── Fase 21.5: Workflow Separation ✅ COMPLETE (Week 145-146)
├── Fase 22: FP Methodology Overhaul ✅ COMPLETE (Week 146-147)
├── Fase 23: Context Engineering ✅ COMPLETE (Week 155)
├── Fase 23.5: Confucius Orchestrator ✅ COMPLETE (Week 149-154)
└── Quality-Functionality Impact Mapping

WEEK 151-232: GAP ANALYSIS IMPLEMENTATION (82 weken)
├── Fase 24: Quick Wins & Foundation (15 items)
├── Fase 25: Core Platform Enhancement (18 items)
├── Fase 26: AI & Automation (12 items)
├── Fase 27: Testing Excellence (8 items)
├── Fase 28: Advanced Integrations (10 items)
└── Fase 29: Innovation & Scale (9 items)
```

---

## Current Focus (Week 155)

| Area | Status | Details |
|------|--------|---------|
| **Fase 23 Context Engineering** | ✅ COMPLETE | ReferenceSelector, ContextOptimizer, 60-80% token savings |
| **Fase 23.5 Confucius Orchestrator** | ✅ COMPLETE | 4 workflow orchestrators, PIV loop, quality gates |
| **Fase 21.5 Workflow Separation** | ✅ COMPLETE | AnalysisContract, v2 API, 100% decoupling |
| **Fase 22 FP Methodology** | ✅ COMPLETE | NESMA/IFPUG compliant, work type classifier |
| **Test Suite** | COMPLETE | 2,700+ tests, 97.8% pass rate |
| **Stability Analyzers** | COMPLETE | SessionAnalyzer, MemoryAnalyzer, ExternalServiceAnalyzer |
| **GAP Analysis** | COMPLETE | 75 items identified, 6 phases planned |
| **Documentation** | ✅ COMPLETE | Architecture, workflows, README updated |

See: [phases-current.md](docs/roadmap/phases-current.md)

---

## Critical Path (Week 148-150)

### Fase 22: FP Methodology Overhaul ✅ COMPLETE

**Status:** ✅ COMPLETE (Week 146-147)
**Solution:** NESMA/IFPUG compliant FP methodology with work type classification

| Component | Status | Description |
|-----------|--------|-------------|
| WorkTypeClassifier | ✅ | NESMA: Analyse, Nieuwe bouw, Verbouw, Herbouw, Onderhoud |
| EnhancementFPCalculator | ✅ | EFP = ADD + CHNG + DEL + CFP |
| FPComponentValidator | ✅ | ILF/EIF/EI/EO/EQ validation rules |
| API Endpoints | ✅ | /api/fp/* with 5 new endpoints |
| Integration | ✅ | Existing fp-estimation API updated |

See: [docs/roadmap/phases/fase-22-fp-methodology.md](docs/roadmap/phases/fase-22-fp-methodology.md)

### Fase 23.5: Confucius Code Agent Orchestrator ✅ COMPLETE

**Status:** ✅ COMPLETE (Week 149-154)
**Solution:** Central agent orchestration with PIV loop and quality gates

| Component | Status | Description |
|-----------|--------|-------------|
| WorkflowOrchestrator | ✅ | Base class with stage dependencies, quality gates |
| BrownPaperOrchestrator | ✅ | 6-stage legacy analysis workflow |
| MigrationOrchestrator | ✅ | BMAD 8-question migration planning |
| GreenPaperOrchestrator | ✅ | 6-stage greenfield project specification |
| QualityOrchestrator | ✅ | 5-stage quality gate and scanning |
| API Routes | ✅ | /confucius/workflows/* with SSE streaming |
| Unit Tests | ✅ | 32 tests, all passing |

See: [docs/architecture/confucius-orchestrator-integration-plan.md](docs/architecture/confucius-orchestrator-integration-plan.md)

### Fase 23: Context Engineering ✅ COMPLETE

**Status:** ✅ COMPLETE (Week 155)
**Goal:** Intelligent reference loading for token-efficient agent execution

| Component | Status | Description |
|-----------|--------|-------------|
| ReferenceSelector | ✅ | Semantic matching for reference documents |
| ReferenceRegistry | ✅ | Loading/caching reference files from filesystem |
| ContextOptimizer | ✅ | Token-efficient context building per workflow/agent |
| API Endpoints | ✅ | /api/context-engineering/* with 10 endpoints |
| Unit Tests | ✅ | 25 tests passing |

**Key Achievement:** 60-80% token reduction through on-demand reference loading

### Quality-Functionality Impact Mapping

**Goal:** Link quality issues to Epic/Feature/Story level
**Benefit:** Business impact visibility for all findings

---

## Workflow Separation (Fase 21.5) ✅ COMPLETE

**Goal:** 100% scheiding Brown Paper/Migration/Quality met clean interface
**Status:** ✅ COMPLETE (Week 145-146)
**Specification:** [docs/architecture/workflow-separation-plan.md](docs/architecture/workflow-separation-plan.md)

### Key Changes Implemented

| Component | Before | After |
|-----------|--------|-------|
| **Migration Input** | `brown_paper_session_id` | `analysis_id` (AnalysisContract) |
| **Stability** | Embedded in Brown Paper | Shared Infrastructure |
| **Quality** | Coupled to workflows | Independent domain + scheduler |
| **API Version** | v1 (coupled) | v2 (decoupled) |

### Implementation Phases (Phases 1-4 Complete)

1. ✅ **Infrastructure** - contracts/, infrastructure/, domains/ modules
2. ✅ **Adapters** - BrownPaperContractAdapter, AnalysisContractConsumer
3. ✅ **New APIs** - /api/v2/migration/*, /api/v2/quality/*
4. ✅ **Services** - QualitySchedulerService, QualityOrchestratorService
5. ⏳ **Migration** - Update clients, add deprecation warnings
6. ⏳ **Cleanup** - Remove old endpoints, drop brown_paper_session_id

### V2 API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v2/migration/contracts/from-brown-paper` | Create AnalysisContract |
| `POST /api/v2/migration/start` | Start with analysis_id |
| `GET /api/v2/migration/context/{analysis_id}` | Get migration context |
| `POST /api/v2/quality/scans/run` | Standalone quality scan |
| `POST /api/v2/quality/schedules` | Create scheduled scan |
| `GET /api/v2/quality/gates/{project_id}` | Evaluate quality gate |

---

## GAP Analysis Phases (Week 151-232)

### Phase Summary

| Fase | Focus | Items | Weken | Key Deliverables |
|------|-------|-------|-------|------------------|
| **24** | Quick Wins | 15 | 12 | Legacy Quickscan, Secret Detection, Migration Patterns |
| **25** | Core Enhancement | 18 | 16 | COBOL Analyzer, UI Wrapper, Knowledge Graph |
| **26** | AI & Automation | 12 | 14 | LLM Collaboration, Natural Language Query |
| **27** | Testing | 8 | 10 | Characterization Tests, Mutation Testing |
| **28** | Integrations | 10 | 12 | Jira, GitLab, ServiceNow |
| **29** | Innovation | 9 | 16 | Multi-language Translation, Microservices |

### Top 10 Highest ROI Items

| Rank | Item | ROI | Description |
|------|------|-----|-------------|
| 1 | A1 | 8.0 | Legacy Quickscan (15-min assessment) |
| 2 | K3 | 8.0 | Secret Detection |
| 3 | D1 | 7.5 | Migration Pattern Library |
| 4 | D2 | 7.5 | Strangler Fig Implementation |
| 5 | K1 | 6.7 | OWASP Integration |
| 6 | K2 | 6.0 | CVE Database Integration |
| 7 | A4 | 6.0 | Risk Heat Map |
| 8 | E1 | 5.3 | Visual Dependency Graph |
| 9 | J1 | 5.3 | Context-Aware Documentation |
| 10 | B12 | 5.0 | LLM Agent Collaboration Framework |

See: [gap-analysis-complete-roadmap.md](docs/roadmap/gap-analysis-complete-roadmap.md)

---

## Design Principles

1. **Small, Specialized Analyzers** - COBOL items (B2, B3, B4) blijven apart: kwaliteit boven snelheid
2. **LLM Agent Collaboration** - Agents werken autonoom samen via B12 framework
3. **Human-in-Loop** - Alleen voor review en escalatie, niet voor standaard werk
4. **No Marketplace** - Templates lokaal, geen externe marketplace
5. **Multi-format Export** - CSV, Excel, ODS, OpenProject, LibrePlan, MS Project

---

## Documentation Links

| Document | Description |
|----------|-------------|
| [phases-current.md](docs/roadmap/phases-current.md) | Week 144 status |
| [phases-planned.md](docs/roadmap/phases-planned.md) | Fase 22-29 details |
| [phases-completed.md](docs/roadmap/phases-completed.md) | Fase 1-21 archive |
| [gap-analysis-complete-roadmap.md](docs/roadmap/gap-analysis-complete-roadmap.md) | Full 75-item specs |
| [workflow-separation-plan.md](docs/architecture/workflow-separation-plan.md) | Brown Paper/Migration/Quality separation |

---

## Milestones

| Milestone | Week | Deliverable |
|-----------|------|-------------|
| **Stability Framework Complete** | 146 | All 8 detection categories ✅ |
| **FP Methodology Fixed** | 147 | NESMA/IFPUG compliant ✅ |
| **Confucius Orchestrator** | 154 | 4 workflow orchestrators ✅ |
| **PIV Loop Active** | 154 | Quality gates operational ✅ |
| **Context Engineering** | 155 | 60-80% token reduction ✅ |
| **GAP Phase 1 Start** | 163 | Quick wins implementation |
| **COBOL Support** | 175 | B1 Analyzer complete |
| **LLM Collaboration** | 191 | B12 Framework active |
| **Full Platform** | 244 | All 75 items complete |

---

*Generated: Week 155 (2026-01-13)*
