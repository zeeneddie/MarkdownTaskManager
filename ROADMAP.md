# MarQed Platform Roadmap

**Project:** MarQed AI Agent Software Platform
**Last Updated:** Week 162 (2026-02-02)
**Total Phases:** 69 | **Timeline:** Week 144-254

---

## Executive Summary

De MarQed roadmap combineert de bestaande geplande fases met een uitgebreide gap-analyse van 12 externe bronnen (6 Nederlandse consultancies, 5 GitHub repos, 1 gist).

### Roadmap Overview

```
WEEK 144-158: CRITICAL FOUNDATION + ORCHESTRATOR + SECURITY ✅ COMPLETE
├── Fase 21: Stability Analyzer ✅ COMPLETE
├── Fase 21.5: Workflow Separation ✅ COMPLETE (Week 145-146)
├── Fase 22: FP Methodology Overhaul ✅ COMPLETE (Week 146-147)
├── Fase 23: Context Engineering ✅ COMPLETE (Week 155)
├── Fase 23.5: Confucius Orchestrator ✅ COMPLETE (Week 149-154)
├── Fase 23.6: Stage Council Review ✅ COMPLETE (Week 157)
├── Fase 24.5: LLM Resilience & Streaming ✅ COMPLETE (Week 155)
├── Fase 24.6: Restartable Workflows ✅ COMPLETE (Week 158)
├── Fase 24.7: Async Database Persistence ✅ COMPLETE (Week 159)
├── Fase 24.8: Epic Generation Fix ✅ COMPLETE (Week 158)
├── Fase 24-A1: Legacy Quickscan ✅ COMPLETE (Week 157)
├── Fase 24-KB: Knowledge Base Integration ✅ COMPLETE (Week 158) (KB1+KB5 done, KB2-KB4 merged)
├── Fase 29: Quality-Functionality Impact Mapping ✅ COMPLETE (Week 156-157)
├── Fase 31: CWE Security Scanner Suite ✅ COMPLETE (Week 157)
├── Fase 41: Injection Vulnerability Scanners ✅ COMPLETE (Week 158) (484 tests, 108 rules)
└── Fase 42: Advanced False Negative Detection ✅ COMPLETE (Week 158) (468 tests, 4 scanners)

WEEK 159-162: BUSINESS DOMAIN EXTRACTION ✅ DONE
└── Fase 24.10: Business-Driven Epic Generation (Week 159-162) ✅ 100% COMPLETE
    ├── BusinessDomainExtractor integratie ✅ COMPLETE
    ├── BusinessDrivenStoryGenerator integratie ✅ COMPLETE
    ├── MarQed workflow integratie ✅ COMPLETE
    ├── Dashboard sync ✅ COMPLETE (datetime fix + dataclass fix)
    └── HCI-CRS E2E validatie ✅ COMPLETE (440 epics, 2383 FP, 20099 SP)

WEEK 157-244: GAP ANALYSIS IMPLEMENTATION (IN PROGRESS)
├── Fase 24: Quick Wins & Foundation (15 items) ✅ 15/15 COMPLETE (A1+K3+D1+D2+K1+K2+A4+E1+J1+K4+A2+A3+D4+B5+B6)
├── Fase 24.9: Brown Paper Workflow Refactoring (Week 160-162) 🆕 HIGH PRIORITY
├── Fase 24.10: Business-Driven Epic Generation (Week 159-162) ✅ 100% COMPLETE
├── Fase 25: Core Platform Enhancement (18 items)
├── Fase 26: AI & Automation (12 items)
├── Fase 27: Testing Excellence (8 items)
├── Fase 28: Advanced Integrations (10 items)
├── Fase GAP-29: Innovation & Scale (9 items)
├── Fase 30: LLM Council Improvements (Week 233-235) 🆕
├── Fase 32: Ralph Wiggum + mq Integration + Cole Medin (Week 175-190) 🆕 UPDATED
├── Fase 32E: Quality Harness - PM/QA Gates + Visual Verification + Sec-Context (KW27-30 [w191-194]) 🆕 UPDATED
├── Fase 33: DevStats Developer Metrics (Week 179-184) 🆕
├── Fase 34: Advanced Error Detectors (KW6-7 [w159-160]) 🆕
├── Fase 35: Data Integrity Scanners (KW8-9 [w161-162]) 🆕
├── Fase 36: Logic & Crypto Scanner (KW10-14 [w163-167]) 🆕
├── Fase 37: Security Scanner Agent Integration (KW12-18 [w165-171]) 🆕
├── Fase 38: Memory Safety Scanner (after Fase 37) 🆕
├── Fase 39: ML-Based Novel Vulnerability Detection (after Fase 42) 🆕
├── Fase 40: Hybrid False Positive Reduction (after Fase 39) 🆕
├── Fase 43: Zero-Complaints Green Paper & Maintenance (Week 177-184) 🆕
├── Fase 44: AI Code Complaints Strategy (Week 185-192) 🆕
├── Fase 45: Reverse Traceability Service (Week 193-200) 🆕
├── Fase 46: User Workflow Documentation (Week 201-208) 🆕
├── Fase 47: LRM Integration Foundation (Week 209-216) 🆕
├── Fase 48: LRM Software Intake Enhancement (Week 217-224) 🆕
├── Fase 49: LRM Advanced Workflows (Week 225-232) 🆕
├── Fase 50: LRM Autonomous Operations (Week 233-240) 🆕
├── Fase 51: Klant Template Service - Multi-Tenant Platform (Week 195-206) 🆕
├── ★ Fase 60: Observability Foundation - OTLP/Langfuse (Week 179-182) 🆕 P0
├── ★ Fase 61: Progress Dashboard & Per-Ticket Cost (Week 183-188) 🆕 P1
├── ★ Fase 62: Conversational Intake - Epic Mode (Week 193-198) 🆕 P1
├── ★ Fase 63: Statistical Drift Detection (Week 207-212) 🆕 P2
├── ★ Fase 64: Self-Evolution Activation (Week 229-234) 🆕 P3
└── ★ Fase 65: External Repo Intelligence - Drift/Kea/Octopus/Sec-Context (Week TBD) 🆕
```

---

## Current Focus (Week 162)

### 🔄 IN PROGRESS: Brown Paper Workflow met Business Domain Extraction

**Priority:** HIGH (Core workflow enhancement)
**Status:** 🔄 80% COMPLETE
**Effort:** ~16 uur

**Doel:** MarQed Brown Paper workflow integreren met Business Domain Extraction voor business-driven epics ipv phase-based epics.

**Wat is gedaan:**
| Component | Status | Beschrijving |
|-----------|--------|--------------|
| BusinessDomainExtractor integratie | ✅ | `generate_tasks()` roept nu `BusinessDomainExtractorService` aan |
| BusinessDrivenStoryGenerator integratie | ✅ | Genereert epics/features/stories vanuit business domains |
| `_quick_code_scan()` method | ✅ | Haalt modules en dependencies op voor domain extraction |
| `_convert_business_stories_to_tasks()` | ✅ | Converteert GeneratedEpic/Feature/Story naar MarQed formaat |
| `_sync_to_brown_paper_tables()` | ✅ | Sync naar brown_paper_* tables voor dashboard |
| Playwright automation script | ✅ | `frontend/playwright-brown-paper.js` met 8 antwoorden >100 woorden |
| DateTime timezone fixes | ✅ | Naive UTC datetimes voor TIMESTAMP WITHOUT TIME ZONE columns |
| JSON serialization fixes | ✅ | MarQedAnswer objects worden nu correct geserialiseerd |

**Wat nog moet:**
| Task | Status | Beschrijving |
|------|--------|--------------|
| Backend restart & test | ✅ | Alle code changes geladen en E2E workflow getest |
| Database sync verificatie | ✅ | 100 epics in brown_paper_epics, 1 session, 1 constitution |
| Dashboard integratie test | ✅ | Sessions API retourneert data met modules/domains counts |
| FP/SP columns toevoegen | ⏳ | Optioneel: dedicated columns voor total_function_points, total_story_points |

**Files gewijzigd:**
- `backend/app/services/brown_paper_service.py` - Business extraction integratie
- `backend/app/models/application.py` - Datetime fixes
- `backend/app/models/brown_paper.py` - Datetime fixes
- `frontend/playwright-brown-paper.js` - Uitgebreide antwoorden >100 woorden

**Output voorbeeld (business-driven):**
```
Epics by domain (6632 total):
├── Patiënt Beheer - 1200 epics
├── Behandelplan & Diagnose - 980 epics
├── Agenda & Planning - 850 epics
├── Declaraties & Facturatie - 1100 epics
├── Praktijkbeheer - 750 epics
└── Rapportages & Analytics - 650 epics
```

---

### ✅ COMPLETED: Epic Generation Fix - Journey-Based Epic Detection

**Priority:** HIGH (Blocking for accurate backlog generation)
**Status:** ✅ COMPLETE (Week 158)
**Effort:** ~8 uur
**Documentation:**
- [`backend/docs/EPIC_GENERATION_FIX.md`](backend/docs/EPIC_GENERATION_FIX.md)
- [`backend/docs/plans/FASE-24.8-EPIC-GENERATION-FIX-COMPLETED.md`](backend/docs/plans/FASE-24.8-EPIC-GENERATION-FIX-COMPLETED.md)

**Oplossing Geïmplementeerd:**
- Created `CombinedEpicSearcher` - combines journey-based + folder-based detection
- Created `JourneyBasedEpicSearcher` - scans screens, navigation, buttons, messages
- Created `GenericEpicSearcher` - folder-based fallback for infrastructure
- Modified `IntakeToBacklogService` to use CombinedEpicSearcher
- Modified `BrownPaperService` with optional enhancement method

**Nieuwe Module:** `backend/app/services/epic_searchers/`
```
epic_searchers/
├── __init__.py
├── models.py              # DetectedScreen, DetectedJourney, DetectedEpic
├── journey_epic_searcher.py    # Journey-based detection
├── generic_epic_searcher.py    # Folder-based detection
└── combined_epic_searcher.py   # Combined approach
```

**Output Voorbeeld:**
```
BUSINESS EPICS (from User Journeys):
├── Dossier (12 screens, 8 journeys) - Actions: [Zoeken, Opslaan, Verwijderen]
├── Afspraken (8 screens, 5 journeys) - Actions: [Inplannen, Annuleren]
└── Beheer (15 screens, 6 journeys)

INFRASTRUCTURE EPICS (from Folder Structure):
├── CRS Libraries
├── API Layer
└── Database
```

---

### ✅ COMPLETED: Async Database Persistence Refactoring (Fase 24.7)

**Priority:** CRITICAL (Prerequisite for all persistence)
**Status:** ✅ COMPLETE (Week 159)
**Effort:** ~18 uur

**Oplossing Geïmplementeerd:** Async-first architectuur met deprecated sync wrappers.

| Component | Status | Changes |
|-----------|--------|---------|
| BrownPaperService | ✅ | `get_session()`, `list_sessions()` → async-first |
| MarQedBrownPaperWorkflow | ✅ | 12 methods refactored to async-first |
| API Routes | ✅ | All `*_async()` calls updated |
| Tests | ✅ | 17/17 passing, deprecation warnings active |

**Pattern Toegepast:**
```python
# Async-first with deprecated sync wrapper
async def start_session(self, ...) -> Session:
    """Primary async implementation."""
    ...

@deprecated_sync_wrapper("start_session", "26.0")
def start_session_sync(self, ...) -> Session:
    """DEPRECATED: Use start_session() instead."""
    return self._sessions.get(...)  # Cache-only
```

**Success Criteria:** ✅ All met
- ✅ Alle workflow methods zijn async-first
- ✅ Sync wrappers met deprecation warnings (v26.0 removal)
- ✅ Geen code duplicatie
- ✅ Alle tests groen (17/17)

---

### IMMEDIATE: Brown Paper Business Domain Extraction Test

| Task | Status | Details |
|------|--------|---------|
| **Fase 24.6 Restartable Workflows** | ✅ COMPLETE | Generic checkpoint/resume system for all workflows |
| **Fase 24.7 Async Refactoring** | ✅ COMPLETE | BrownPaperService + MarQedBrownPaperWorkflow async-first |
| **Business Domain Extraction** | ✅ COMPLETE | `BusinessDomainExtractorService` + `BusinessDrivenStoryGeneratorService` |
| **MarQed Integration** | ✅ COMPLETE | `generate_tasks()` gebruikt nu business extraction |
| **Dashboard Sync** | 🔄 IN PROGRESS | `_sync_to_brown_paper_tables()` - laatste bugs fixen |
| **Playwright Automation** | ✅ COMPLETE | 8 vragen met >100 woorden antwoorden |

**Doel:** Validate Brown Paper workflow end-to-end met HCI-CRS legacy applicatie, business-driven epics genereren

**Configuratie:**
- Path: `/opt/projecten/hci-crs`
- LLM Provider: Ollama (lokaal)
- Models: qwen2.5-coder:7b, qwen2.5:7b, deepseek-r1:7b, mistral:latest
- VBScript Analyse: Enabled (`skip_vbscript: false`)

**Endpoints:**
- Start: `POST /api/brown-paper/bmad/start`
- Answer: `POST /api/brown-paper/bmad/{session_id}/answer`
- Analyze: `POST /api/brown-paper/bmad/{session_id}/enhanced-analyze`

---

### Completed This Week (Week 159)

| Area | Status | Details |
|------|--------|---------|
| **Fase 24 GAP D4** | ✅ COMPLETE | Database Migration Pattern Catalog with 8 patterns, recommendations, risk assessment |
| **Fase 24.7 Async Refactoring** | ✅ COMPLETE | BrownPaperService + MarQedBrownPaperWorkflow async-first |
| **Fase 24.6 Restartable Workflows** | ✅ COMPLETE | Checkpoint/resume system for all workflow types |
| **Fase 24 GAP Items** | ✅ 15/15 | COMPLETE (B5+B6 done Week 159) |
| **Business Domain Extraction** | ✅ COMPLETE | `BusinessDomainExtractorService` geïntegreerd in MarQed workflow |
| **Business Story Generation** | ✅ COMPLETE | `BusinessDrivenStoryGeneratorService` genereert epics/features/stories |
| **Playwright Automation** | ✅ COMPLETE | `frontend/playwright-brown-paper.js` met >100 woorden antwoorden |

### In Progress (Week 159)

| Area | Status | Details |
|------|--------|---------|
| **Dashboard Sync** | ✅ COMPLETE | `_sync_to_brown_paper_tables()` — datetime fix + dataclass fix |
| **HCI-CRS E2E Test** | ✅ COMPLETE | 440 epics, 2383 FP, 20099 SP, DB sync verified |

### Previously Completed

| Area | Status | Details |
|------|--------|---------|
| **Fase 42 Advanced FN Detection** | ✅ COMPLETE | 4 scanners, 468 tests, ~272 rules |
| **Fase 41 Injection Scanners** | ✅ COMPLETE | 484 tests, 108 rules, 13 categories |
| **Fase 31 CWE Security Scanner** | ✅ COMPLETE | Multi-scanner suite, 288+ findings on HCI-CRS |
| **Fase 24-KB Knowledge Base** | ✅ COMPLETE | KB1+KB5 done, KB2-KB4 merged into scanners |
| **Fase 24-A1 Legacy Quickscan** | ✅ COMPLETE | 15-min assessment, Go/No-Go recommendation |
| **Fase 23.6 Stage Council Review** | ✅ COMPLETE | Multi-model LLM reviews per stage |
| **Fase 29 Quality Impact Mapping** | ✅ COMPLETE | Quality-to-functionality linking |
| **Fase 23.5 Confucius Orchestrator** | ✅ COMPLETE | 4 workflow orchestrators, PIV loop |
| **Fase 23 Context Engineering** | ✅ COMPLETE | 60-80% token reduction |
| **Test Suite** | ✅ COMPLETE | 2,700+ tests, 97.8% pass rate |

See: [phases-current.md](docs/roadmap/phases-current.md)

---

## Critical Path (Week 148-157)

### Fase 31: CWE Security Scanner Suite ✅ COMPLETE

**Status:** ✅ COMPLETE (Week 157)
**Solution:** Multi-scanner security suite with SARIF output

| Component | Status | Description |
|-----------|--------|-------------|
| SecurityOrchestrator | ✅ | Multi-scanner orchestration |
| Custom ASP Scanner | ✅ | CWE-89 SQL injection, XSS, path traversal |
| OpenGrep Adapter | ✅ | 30+ languages, LGPL 2.1 licensed |
| Bandit/Trivy Adapters | ✅ | Python and dependency scanning |
| API Endpoints | ✅ | /api/security-scanner/* (12 endpoints) |

See: [docs/roadmap/phases/fase-31-cwe-security-scanners.md](docs/roadmap/phases/fase-31-cwe-security-scanners.md)

### Fase 24-A1: Legacy Quickscan ✅ COMPLETE

**Status:** ✅ COMPLETE (Week 157)
**Solution:** 15-minute automated legacy assessment with Go/No-Go recommendation

| Component | Status | Description |
|-----------|--------|-------------|
| TechnologyDetector | ✅ | Multi-language detection with LOC |
| ComplexityAnalyzer | ✅ | Cyclomatic complexity, tech debt |
| SecurityAnalyzer | ✅ | Integration with Fase 31 scanner |
| EffortEstimator | ✅ | Person-months with ranges |
| LegacyQuickscanService | ✅ | Parallel async orchestration |
| API Endpoints | ✅ | /api/quickscan/* (4 endpoints) |

**Real-world test:** HCI-CRS FysioOne-Classic → NO_GO (418K LOC, 1569 PM estimate)

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

### Fase 41: Injection Vulnerability Scanners ✅ COMPLETE

**Status:** ✅ COMPLETE (Week 158)
**Solution:** Complete CWE Top 25 injection coverage with 108 rules across 13 categories

| Component | Status | Description |
|-----------|--------|-------------|
| InjectionDetector | ✅ | XSS, SQLi, CMDi, Path Traversal, Deserialization, SSRF |
| AuthLogicDetector | ✅ | 6 CWEs, 29 rules, context-aware detection |
| Extended Tests (T1-T3) | ✅ | 274 injection tests + 123 auth logic tests |
| FN Hunting Suite | ✅ | 57 tests (43 pass, 14 xfail known limitations) |
| Integration Tests | ✅ | 30 multi-scanner orchestrator tests |

**Total:** 484 tests (470 passed, 14 xfailed, 0 failures)

See: [docs/roadmap/phases/fase-41-injection-vulnerability-scanners.md](docs/roadmap/phases/fase-41-injection-vulnerability-scanners.md)

### Fase 42: Advanced False Negative Detection ✅ COMPLETE

**Status:** ✅ COMPLETE (Week 158)
**Solution:** 4 advanced scanners targeting remaining false negatives with ~272 rules

| Component | Status | Description |
|-----------|--------|-------------|
| ASTTaintTracker | ✅ | AST-based taint tracking for complex data flows (40% FN) |
| DynamicFeatureDetector | ✅ | Heuristic detection for dynamic language features (25% FN) |
| FrameworkSecurityPlugin | ✅ | Framework-specific security patterns (20% FN) |
| ObfuscationDetector | ✅ | Deobfuscation + entropy analysis (10% FN) |

**Total:** 468 tests, 28 xfailed, 4 new scanners

See: [docs/roadmap/phases/fase-42-advanced-fn-detection.md](docs/roadmap/phases/fase-42-advanced-fn-detection.md)

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

## Fase 24 GAP Items Status ✅ 15/15 COMPLETE

### ✅ All Completed

| Item | Beschrijving | ROI | Week |
|------|-------------|-----|------|
| A1 | Legacy Quickscan (15-min assessment) | 8.0 | 157 |
| K3 | Secret Detection | 8.0 | 157 |
| D1 | Migration Pattern Library | 7.5 | 157 |
| D2 | Strangler Fig Pattern | 7.5 | 157 |
| K1 | OWASP Integration | 6.7 | 158 |
| K2 | CVE Database Integration | 6.0 | 158 |
| A4 | Risk Heat Map | 6.0 | 158 |
| E1 | Visual Dependency Graph | 5.3 | 158 |
| J1 | Context-Aware Documentation | 5.3 | 158 |
| K4 | Compliance Mapping (Security Debt) | 5.0 | 157 |
| A2 | Fixed-Price Templates | 4.5 | 157 |
| A3 | Architecture Assessment Matrix | 4.5 | 157 |
| D4 | Database Migration Patterns | 5.0 | 159 |
| **B5** | ASP.NET Core Analyzer | 4.8 | 159 |
| **B6** | PHP Modern Analyzer (8.x features) | 4.8 | 159 |

**Fase 24 Complete!** Alle 15 Quick Wins zijn geïmplementeerd.

---

## Fase 24.10: Business-Driven Epic Generation (Week 159-162) ✅ COMPLETE

**Status:** ✅ 100% COMPLETE (Week 162, 2026-02-02)
**Priority:** CRITICAL (Blocking for HCI-CRS analysis)
**Effort:** ~16 uur (realized)
**Dependencies:** BusinessDomainExtractorService, BusinessDrivenStoryGeneratorService

### Problem Statement

De huidige MarQed workflow genereerde "phase-based" epics zoals:
- "Phase 1: Foundation"
- "Phase 2: Core Migration"
- "Phase 3: Integration"

Dit is **niet business-driven** en geeft geen inzicht in de werkelijke business domeinen van de applicatie.

### Solution: Business Domain Extraction

Integreer `BusinessDomainExtractorService` en `BusinessDrivenStoryGeneratorService` in de MarQed `generate_tasks()` methode.

### Implementation Status

| Component | Status | File |
|-----------|--------|------|
| `_quick_code_scan()` | ✅ COMPLETE | `brown_paper_service.py` |
| `BusinessDomainExtractor` call | ✅ COMPLETE | `brown_paper_service.py:5126-5138` |
| `BusinessDrivenStoryGenerator` call | ✅ COMPLETE | `brown_paper_service.py:5140-5145` |
| `_convert_business_stories_to_tasks()` | ✅ COMPLETE | `brown_paper_service.py:5168-5198` |
| `_sync_to_brown_paper_tables()` | ✅ COMPLETE | `brown_paper_service.py:5200-5310` |
| Datetime timezone fixes | ✅ COMPLETE | `application.py`, `brown_paper.py` |
| JSON serialization fixes | ✅ COMPLETE | `brown_paper_service.py:5260-5270` |
| Backend restart & E2E test | ✅ COMPLETE | 440 epics, 100 in DB, sessions API OK |

### E2E Resultaten (Week 162)

| Metric | Waarde |
|--------|--------|
| Business domains gedetecteerd | 440 |
| Epics in DB (top-100) | 100 |
| Features | 494 |
| Stories | 1.711 |
| Function Points | 2.383 |
| Story Points | 20.099 |
| Extraction method | `business_driven` |
| Top epics | Patiënt Beheer (148 FP), Declaraties & Facturatie (405 FP), Behandelplan & Diagnose (290 FP) |

### Output Transformation

```
BEFORE (Phase-Based):                    AFTER (Business-Driven):
┌─────────────────────────┐              ┌─────────────────────────┐
│ Phase 1: Foundation     │              │ Patiënt Beheer          │
│ Phase 2: Core Migration │      →       │ Behandelplan & Diagnose │
│ Phase 3: Integration    │              │ Agenda & Planning       │
│ Phase 4: Testing        │              │ Declaraties & Facturatie│
│ Phase 5: Deployment     │              │ Praktijkbeheer          │
└─────────────────────────┘              └─────────────────────────┘
```

### Completed (Week 162, 2026-02-02)

1. ✅ Backend restarted met datetime + dataclass fixes
2. ✅ E2E test: session → 8 answers → analysis → specification → tasks
3. ✅ DB sync: 1 session, 1 constitution, 100 epics in brown_paper_* tables
4. ✅ Sessions API: GET /api/brown-paper/sessions retourneert data correct

---

## Fase 24.9: Brown Paper Workflow Refactoring (Week 160-162) 🆕

**Status:** PLANNED
**Priority:** HIGH (User feedback from Brown Paper test)
**Effort:** ~40 uur (~1-2 weken)
**Dependencies:** Brown Paper HCI-CRS test completion

### Problem Statement

De huidige Brown Paper workflow is te migratie-gefocust. De 8 BMAD vragen bevatten:
- Vraag 2: Target state (migratie)
- Vraag 3: Migration strategy (migratie)
- Vraag 4: Data migration (migratie)

Dit hoort niet bij **onboarding/analyse** maar bij **migration planning**.

### Solution: Workflow Separation

```
HUIDIGE SITUATIE (1 gemengde workflow):
┌─────────────────────────────────────────────────┐
│  Brown Paper Workflow (8 vragen)                │
│  - Analyse vragen (Q1, Q6-Q8)                   │
│  - Migratie vragen (Q2-Q5) ← NIET GEWENST      │
└─────────────────────────────────────────────────┘

GEWENSTE SITUATIE (2 gescheiden workflows):
┌─────────────────────────────────────────────────┐
│  1. ONBOARDING WORKFLOW (Brown Paper)           │
│     - Applicatie beschrijving                   │
│     - Business domains                          │
│     - Technische complexiteit                   │
│     - Risico's & technische schuld             │
│     - Team & resources (huidige situatie)       │
│     Output: Application Profile                 │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  2. MIGRATION PLANNING WORKFLOW (Optioneel)     │
│     - Target state                              │
│     - Migration strategy                        │
│     - Data migration approach                   │
│     - Testing strategy                          │
│     - Success criteria                          │
│     Output: Migration Plan                      │
└─────────────────────────────────────────────────┘
```

### Implementation Tasks

| Task | Description | Effort |
|------|-------------|--------|
| **1. Refactor BMAD Questions** | Split 8 questions into 2 sets (onboarding vs migration) | 8h |
| **2. Create OnboardingWorkflow** | New workflow class for pure analysis | 12h |
| **3. Update MigrationWorkflow** | Takes OnboardingResult as input | 8h |
| **4. Merge Duplicate Workflows** | Consolidate 2 existing Brown Paper implementations | 8h |
| **5. Update API Endpoints** | `/marqed/onboard` + `/marqed/migrate` | 4h |

### New Question Sets

**Onboarding Workflow (5 vragen):**
1. Describe the current application (stack, size, age, deployment)
2. What are the main business domains/modules?
3. What is the current technical state? (quality, test coverage, documentation)
4. What are the known issues and technical debt?
5. What team/resources are currently available?

**Migration Planning Workflow (5 vragen):**
1. What is the target state after migration?
2. What migration strategy will be used?
3. How will data be migrated?
4. What is the testing strategy?
5. What are the success criteria?

### Success Criteria

| Metric | Target |
|--------|--------|
| Workflow separation | 100% - no migration questions in onboarding |
| Single Brown Paper implementation | Merge 2 → 1 |
| API backward compatibility | Existing clients work |
| Test coverage | ≥80% for new code |

---

## GAP Analysis Phases (Week 151-232)

### Phase Summary

| Fase | Focus | Items | Weken | Key Deliverables |
|------|-------|-------|-------|------------------|
| **24** | Quick Wins | 15 ✅ COMPLETE | 12 | Legacy Quickscan, Secret Detection, Migration Patterns, B5+B6 Analyzers |
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

## Fase 32: Ralph Wiggum Autonomous Loop + mq Integration (Week 175-190)

**Status:** PLANNED
**Priority:** HIGH (ROI 8.5)
**Effort:** 576 uur (~17 weken) - inclusief mq integratie + Cole Medin verbeteringen
**Dependencies:** Fase 23.5 (Confucius Orchestrator), mq workflows
**Benchmark:** [your-claude-engineer](https://github.com/zeeneddie/your-claude-engineer) (Cole Medin harness)

### Overview

Implementatie van de Ralph Wiggum techniek voor autonomous overnight coding, **volledig geïntegreerd met mq CLI workflows**. Verrijkt met inzichten uit Cole Medin's Claude Agent SDK harness (fresh-context-per-iteratie, security sandbox, visual verification).

```
┌─────────────────────────────────────────────────────────────┐
│  mq + RALPH UNIFIED SYSTEM                                  │
├─────────────────────────────────────────────────────────────┤
│  CLI: marqed-bugfix | marqed-changes | marqed-overnight     │
│                                          ↑ NEW              │
├─────────────────────────────────────────────────────────────┤
│  Shared: UnifiedState | KnowledgeHub | ValidationPipeline   │
├─────────────────────────────────────────────────────────────┤
│  Ralph: Loop | Guardrails | Checkpoints | MemoryCompression │
├─────────────────────────────────────────────────────────────┤
│  Security: BashAllowlist | BlockedPatterns | SandboxHooks    │
│  Prompts:  Markdown-driven agent prompts (externalized)     │
└─────────────────────────────────────────────────────────────┘
```

### Vergelijking: Confucius vs Claude Agent SDK (Cole Medin)

**Conclusie:** Confucius is superieur voor MarQed's use case. De Claude Agent SDK is niet geschikt als vervanging maar levert 3 concrete verbeteringen.

| Aspect | Claude Agent SDK (Cole) | Confucius (MarQed) | Winnaar |
|--------|------------------------|-------------------|---------|
| **Routing** | LLM beslist (prompt-driven) | Code-driven (scored algorithm) | **Confucius** — deterministisch, voorspelbaar |
| **Quality gates** | Geen (LLM beoordeelt zichzelf) | Domain-specifieke rules + thresholds | **Confucius** — onmisbaar voor overnight |
| **Retry logic** | Geen built-in | PIV loop met feedback enrichment | **Confucius** — automatische kwaliteitsverbetering |
| **Memory** | Geen (fresh per sessie) | 3-tier hierarchisch (session/entry/runnable) | **Confucius** — essentieel voor multi-week trajecten |
| **Kosten** | LLM tokens voor routing | 0 tokens voor routing (code) | **Confucius** — goedkoper |
| **Agent count** | Max 4-5 sub-agents | 12 agents met auto-selection | **Confucius** — schaalbaarder |
| **Debugging** | Black box (LLM decisions) | Structured audit trail | **Confucius** — productie-waardig |
| **Fresh context** | Elke iteratie nieuw | Niet expliciet | **Cole** — overnemen in Ralph loop |
| **Security sandbox** | Bash allowlist + hooks | Niet geïmplementeerd | **Cole** — overnemen als security-hooks.sh |
| **Prompt management** | Extern (markdown files) | Intern (Python code) | **Cole** — overnemen als prompt externalisatie |

**Waarom NIET de Claude Agent SDK adopteren:**
1. LLM-based routing is onbetrouwbaar voor overnight runs (verkeerde agent om 3 uur 's nachts = catastrofe)
2. Geen quality gates = "false completion" probleem (15-20% bij Cole, <3% bij MarQed met Fase 32E)
3. Geen persistent memory = ongeschikt voor multi-week HCI-CRS trajecten (1569 PM)
4. MarQed's 12-agent ecosysteem past niet in SDK's simpele sub-agent model

**Wat WEL overnemen (3 verbeteringen):**
1. **Fresh context per micro-deliverable** — voorkomt context bloat in overnight runs
2. **Security sandbox** — bash allowlist + blocked patterns voor agent veiligheid
3. **Markdown-driven prompts** — externaliseer agent system prompts voor onderhoudbaarheid

### Implementation Fases

| Fase | Weken | Focus | Effort |
|------|-------|-------|--------|
| **32A: Foundation** | 175-178 | Unified State, Guardrails, Basic Loop, **Security Sandbox**, **Prompt Externalisatie** | 96h (+16h) |
| **32B: Ralph Core** | 179-182 | PRP Generator, Circuit Breaker, Memory, **Fresh Context Pattern** | 128h (+8h) |
| **32C: mq Integration** | 183-186 | overnight.sh, Knowledge Hub, Validation | 80h |
| **32D: Production** | 187-190 | Dashboard, E2E Testing, Docs | 80h |

### Ralph Core Components

| Component | Description |
|-----------|-------------|
| **RalphLoopService** | Autonomous execution loop met configurable iterations |
| **GuardrailsService** | File-based lesson learning (.marqed/guardrails.md) |
| **CompletionDetector** | Dual-gate exit logic, checkbox tracking |
| **CircuitBreaker** | Stuck detection, cost limits, token rotation |
| **CourseCorrectionService** | Dead-end detection, 5 Whys methodology |

### mq Integration Components

| Component | Description |
|-----------|-------------|
| **UnifiedStateManager** | Shared state voor mq tasks + Ralph |
| **KnowledgeHubService** | TechStack + Guardrails + Experience Store |
| **UnifiedValidationPipeline** | 8-phase validation (Vercel + Ralph) |
| **marqed-overnight.sh** | Nieuwe CLI workflow voor overnight coding |
| **MorningReportGenerator** | Summary van overnight werk |

### Production Harness (geïnspireerd door Cole Medin)

| Component | Description | Bron |
|-----------|-------------|------|
| **InitializationAgent** | Context gathering before work starts | Cole |
| **StructuredProgressTracker** | Rich metrics beyond "files changed" | Cole |
| **StageApprovalWorkflow** | Human approval between stages | Cole |
| **RollbackService** | Git reset, regression testing | Cole |
| **MemoryCompressionService** | Context handoff between runs | Cole |
| **MultiPhaseValidationPipeline** | 8-phase validation (syntax → docs) | Cole |

### 🆕 Cole Medin Verbeteringen (3 items)

#### Verbetering 1: Fresh Context per Micro-Deliverable (Fase 32B)

Elke micro-deliverable krijgt een verse agent context. State leeft in PostgreSQL, niet in het context window. Voorkomt context bloat tijdens overnight runs.

```
Ralph Loop (Fresh Context Pattern):
┌─────────────────────────────────────────┐
│ WHILE not all deliverables done:        │
│   1. CREATE fresh agent context         │
│   2. READ state from PostgreSQL         │
│   3. Regression test (bestaand werk)    │
│   4. Pick next micro-deliverable        │
│   5. Implement (1 deliverable only)     │
│   6. PM Gate → QA Gate → Regression     │
│   7. Commit + update state in DB        │
│   8. DESTROY context                    │
│   9. Sleep 3s → loop                    │
└─────────────────────────────────────────┘
```

**Verschil met Cole:** Cole gebruikt lokale `.linear_project.json` + Linear API als state. MarQed gebruikt PostgreSQL + Confucius memory — robuuster en querybaar. Cole's pattern van "elke sessie = verse client" wordt overgenomen, maar MarQed's state backend is superieur.

#### Verbetering 2: Security Sandbox voor Agent Bash (Fase 32A)

Bash allowlist die gevaarlijke commando's blokkeert. Voorkomt destructieve acties door agents tijdens overnight runs.

```
mq/workflows/common/security-hooks.sh (NIEUW):
┌─────────────────────────────────────────┐
│ ALLOWED_COMMANDS:                       │
│   python, pytest, alembic, pip          │
│   npm, node, npx, git                   │
│   ls, cat, grep, find, wc, head, tail   │
│   mkdir, cp, mv, touch                  │
│                                         │
│ BLOCKED_PATTERNS:                       │
│   rm -rf /*, DROP DATABASE,             │
│   git push --force main,               │
│   git reset --hard,                     │
│   chmod 777, curl | bash,              │
│   eval, exec (ongevalideerd)            │
│                                         │
│ EXTRA VALIDATION:                       │
│   rm → alleen in project directory      │
│   git push → alleen feature branches    │
│   pip install → alleen requirements.txt │
└─────────────────────────────────────────┘
```

#### Verbetering 3: Markdown-Driven Agent Prompts (Fase 32A)

Externaliseer Confucius agent system prompts naar markdown files. Maakt het mogelijk om agent gedrag te tweaken zonder code deployment.

```
backend/app/confucius/prompts/ (NIEUW):
├── felix_architect.md          # System prompt Felix
├── quinn_quality.md            # System prompt Quinn
├── peter_product.md            # System prompt Peter
├── betty_business.md           # System prompt Betty
├── diana_documentation.md      # System prompt Diana
├── tessa_testing.md            # System prompt Tessa
├── miguel_metrics.md           # System prompt Miguel
├── marcus_maintenance.md       # System prompt Marcus
├── vicky_design.md             # System prompt Vicky
├── eliza_estimation.md         # System prompt Eliza
├── paul_planning.md            # System prompt Paul
├── ralph_orchestrator.md       # Ralph loop orchestrator
├── ralph_continuation.md       # Continuation task per iteratie
├── ralph_initializer.md        # Initializer task (eerste run)
└── stage_review.md             # Stage council review prompt
```

**Voordelen:**
- Agent gedrag tweaken zonder code deployment
- Git diff op prompt changes (versioning)
- PM/non-developer kan agent prompts reviewen
- A/B testing van prompt varianten

### Bestaande mq Capabilities (reeds geïmplementeerd)

De volgende capabilities zijn **al gebouwd** in de mq workflow scripts en hoeven alleen geactiveerd te worden in de Ralph loop:

| Capability | Implementatie | Status |
|------------|--------------|--------|
| **Auto-continue loop** | `loop-core.sh`: checkpoint-based resume, `--resume` flag | ✅ Gebouwd |
| **One-deliverable-at-a-time** | `micro-decompose.sh`: dependency graph, sequential enforcement | ✅ Gebouwd |
| **Progressive regression** | `regression-runner.sh`: accumulated test suite per deliverable | ✅ Gebouwd |
| **Parallel sessions** | `spawn-parallel-sessions.sh`: N concurrent Claude Code sessions | ✅ Gebouwd |
| **PM dual-gate** | `pm-acceptance-gate.sh`: AI + Human approval, async timeout | ✅ Gebouwd |
| **QA 9-axis validation** | `qa-gate.sh`: code, security, tests, performance, contracts, deps, dead code, visual verification, AI anti-pattern pre-check | ✅ Gebouwd (7 assen) + 🆕 Planned (as 8-9) |
| **Course correction** | `loop-core.sh`: stuck detection, 5 Whys, alternative approaches | ✅ Gebouwd |
| **Progress monitoring** | `monitor-tasks.sh` + `progress-tracking.sh`: real-time ASCII charts | ✅ Gebouwd |

### Key Features

- **Overnight autonomous coding** (8+ uur onbeheerd)
- **Fresh context per micro-deliverable** (voorkomt context bloat) 🆕
- **Security sandbox** (bash allowlist + blocked patterns) 🆕
- **Markdown-driven agent prompts** (externalized, versionable) 🆕
- **Git als geheugen** (fresh context bij token overflow)
- **Guardrails file** voor cross-context learning
- **mq compatibility** (unified state, shared knowledge)
- **marqed-overnight.sh** nieuwe workflow
- **Morning reports** met overnight summary
- **Human-in-loop** approval at stage boundaries
- **Error recovery** with automated rollback

### Success Criteria

| Metric | Target |
|--------|--------|
| Overnight runtime | 8+ uur stable |
| False completion | < 5% |
| Guardrails repeat reduction | 70% |
| Rollback recovery | < 60 sec |
| Cost per overnight | < $25 avg |
| Security violations blocked | 100% |
| Prompt change deploy time | 0 sec (no redeploy) |

### Documentation

| Document | Description |
|----------|-------------|
| [fase-32-ralph-wiggum-loop.md](docs/roadmap/phases/fase-32-ralph-wiggum-loop.md) | Ralph standalone spec |
| [mq-ralph-wiggum-integration-plan.md](docs/mq-ralph-wiggum-integration-plan.md) | 🆕 Full integration plan |
| [mq-integration-plan-van-aanpak.md](docs/mq-integration-plan-van-aanpak.md) | mq Platform integration |
| [fase-32e-quality-harness.md](docs/roadmap/phases/fase-32e-quality-harness.md) | 🆕 Quality Harness (PM/QA Gates) |
| [your-claude-engineer analysis](https://github.com/zeeneddie/your-claude-engineer) | 🆕 Cole Medin benchmark referentie |

---

## Fase 32E: Quality Harness - PM/QA Acceptance Gates (KW27-30 [w191-194])

**Status:** PLANNED
**Priority:** HIGH (ROI 9.0)
**Effort:** 144 uur (~4.5 weken) - inclusief Visual Verification Gate
**Dependencies:** Fase 32D (Ralph Production), mq workflows

### Overview

Quality assurance pipeline die elke micro-deliverable onafhankelijk valideert via PM Acceptance Gate + QA Gate + **Visual Verification** + Progressive Regression, zodat overnight runs betrouwbaar en meetbaar worden.

```
┌─────────────────────────────────────────────────────────────┐
│  QUALITY HARNESS PIPELINE (per micro-deliverable)           │
├─────────────────────────────────────────────────────────────┤
│  1. PRD Decomposition → Micro-Deliverables                  │
│  2. Build (bestaande Ralph loop, fresh context)             │
│  3. PM Acceptance Gate (Claude Code review vs PRD criteria) │
│  4. QA Gate (9-assig: +visual verification +sec-context) 🆕  │
│  5. Progressive Regression (alle eerder geaccepteerde tests)│
│  6. Accept → Registry of REJECT → terug naar Build          │
├─────────────────────────────────────────────────────────────┤
│  Sprint Completion: Full Regression + Coverage + Report     │
└─────────────────────────────────────────────────────────────┘
```

### Components

| Component | Description |
|-----------|-------------|
| **micro-decompose.sh** | PRD → micro-deliverables met dependency graph |
| **pm-acceptance-gate.sh** | Onafhankelijke PM review via Claude Code |
| **qa-gate.sh** | **9-assige** kwaliteitscontrole (code, security, tests, performance, contracts, dependencies, dead code, **visual verification**, **AI security anti-pattern pre-check**) |
| **regression-runner.sh** | Progressive + sprint-level regressie |
| **Acceptance Registry** | SQLite DB voor tracking en traceability |
| **security-hooks.sh** | 🆕 Bash allowlist + blocked patterns (Fase 32A) |

### 🆕 Visual Verification Gate (8e as, geïnspireerd door Cole Medin) + AI Security Anti-Pattern Pre-Check (9e as, Fase 65M)

Cole Medin's harness eist **screenshot evidence** via Playwright MCP voordat een issue "done" mag zijn. Dit wordt de 8e as van `qa-gate.sh`.

```
qa-gate.sh 9 assen:
┌─────────────────────────────────────────────────────────────┐
│  As 1: Code Quality (pylint/ruff)         ≥ 7.0/10         │
│  As 2: Security (CWE scanners)            0 HIGH/CRITICAL   │
│  As 3: Test Coverage (line)               ≥ 80%             │
│  As 4: Performance Degradation            < 20%             │
│  As 5: API Contract Compliance            100%              │
│  As 6: Dependency Audit                   0 vulnerabilities  │
│  As 7: Dead Code Detection                < 5% increase     │
│  As 8: Visual Verification 🆕             (nieuw)           │
│         ├── Playwright screenshot capture                    │
│         ├── Visual diff vs baseline (pixel threshold < 5%)  │
│         ├── Console error check (0 JS errors)               │
│         ├── Accessibility audit (axe-core, WCAG 2.1 AA)    │
│         └── Screenshot stored as evidence in Registry       │
│  As 9: AI Security Anti-Pattern Pre-Check 🆕 (Fase 65M)    │
│         ├── Top-10 AI anti-patterns regex scan (<1 sec)     │
│         ├── Hardcoded secrets detection                      │
│         ├── String concatenation SQL detection               │
│         ├── Raw HTML output detection                        │
│         └── CWE referenties per gevonden anti-pattern        │
└─────────────────────────────────────────────────────────────┘
```

**Implementatie:**
- Playwright MCP server toevoegen aan Ralph agent configuratie
- Per deliverable met UI-component: automatische screenshot
- Vergelijking met baseline screenshot (visual regression)
- Accessibility scan via axe-core
- Evidence opslaan in Acceptance Registry SQLite DB
- **Alleen voor deliverables met UI-component** (API-only deliverables overslaan)

**Playwright MCP configuratie:**
```json
{
  "playwright": {
    "command": "npx",
    "args": ["-y", "@playwright/mcp@latest"],
    "tools": ["navigate", "snapshot", "click", "type", "screenshot"]
  }
}
```

### Quality Thresholds

| Check | Hard Gate | Target |
|-------|-----------|--------|
| Test Coverage (line) | ≥ 80% | ≥ 95% |
| Code Quality (pylint) | ≥ 7.0/10 | ≥ 8.5/10 |
| Security (HIGH/CRITICAL) | 0 findings | 0 findings |
| Performance Degradation | < 20% | < 5% |
| PM Confidence | ≥ 0.8 | ≥ 0.95 |
| Visual Diff (pixel) | < 10% | < 5% |
| Console Errors | 0 | 0 |
| Accessibility (axe-core) | 0 critical | WCAG 2.1 AA |
| AI Anti-Pattern (sec-context) | 0 findings | 0 findings |

### Expected Impact

| Metric | Before | After |
|--------|--------|-------|
| False completion rate | 15-20% | < 3% |
| Overnight reliability | ~60% | > 90% |
| Coverage tracking | none | per-deliverable |
| PRD traceability | manual | automated |
| UI regression detection | none | automated (Playwright) |
| Security violations | possible | blocked (sandbox) |

### Documentation

| Document | Description |
|----------|-------------|
| [fase-32e-quality-harness.md](docs/roadmap/phases/fase-32e-quality-harness.md) | Full specification |

---

## Fase 51: Klant Template Service - Multi-Tenant Platform (Week 195-206)

**Status:** PLANNED
**Priority:** HIGH (ROI 8.0)
**Effort:** 312 uur (~10-12 weken met buffer)
**Dependencies:** Fase 32 (Ralph Wiggum), Fase 23.5 (Confucius Orchestrator)

### Overview

Transformeert MarQed.ai naar een **multi-tenant AI coding platform** met per-klant domeinen en per-applicatie omgevingen met tech-stack specifieke tooling.

```
┌─────────────────────────────────────────────────────────────────┐
│  KLANT TEMPLATE SERVICE ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────┤
│  TEMPLATES:  klant-template | 8x applicatie-templates           │
│              (python, dotnet, legacy-asp, js, ts, go, java, php)│
├─────────────────────────────────────────────────────────────────┤
│  CONTEXT:    Platform → Klant → Applicatie → Project            │
│              (4-layer inheritance, merged context)              │
├─────────────────────────────────────────────────────────────────┤
│  SCANNERS:   34+ scanners auto-configured per tech-stack        │
├─────────────────────────────────────────────────────────────────┤
│  AGENTS:     Derek (DevOps) + Isaac (Infra Audit) 🆕            │
├─────────────────────────────────────────────────────────────────┤
│  WORKFLOW:   DEPLOYMENT (6-phase) 🆕                            │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation Phases

| Phase | Weken | Focus | Effort |
|-------|-------|-------|--------|
| **51A: Foundation** | 191-193 | Templates, KlantTemplateService, ContextInheritance | 80h |
| **51B: Scanners** | 194-195 | ScannerConfigService, 8 stack presets | 56h |
| **51C: Onboarding** | 196-197 | API endpoints, database models, workflows | 64h |
| **51D: VibeCoding** | 198-199 | 6 document templates, agent integration | 48h |
| **51E: Agents** | 200-202 | Derek, Isaac agents, DEPLOYMENT workflow | 64h |

### Key Components

| Component | Type | Description |
|-----------|------|-------------|
| **KlantTemplateService** | Service | Klant domein provisioning |
| **ApplicatieTemplateService** | Service | App omgeving met tech-stack detection |
| **ContextInheritanceService** | Service | 4-layer context merging |
| **ScannerConfigService** | Service | Per-stack scanner auto-configuration |
| **DerekAgent** | Agent | DevOps/Deployment specialist (NIEUW) |
| **IsaacAgent** | Agent | Infrastructure Auditor (NIEUW) |
| **DEPLOYMENT** | Workflow | 6-phase deployment pipeline (NIEUW) |

### New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/klanten/onboard` | POST | Start klant onboarding |
| `/api/v2/klanten/{id}/applicaties/onboard` | POST | Start app onboarding |
| `/api/v2/klanten/{id}/applicaties/{app_id}/context` | GET | Get merged context |
| `/api/v2/klanten/{id}/applicaties/{app_id}/scanners` | GET | Get active scanners |

### Success Criteria

| Metric | Target |
|--------|--------|
| Klant onboarding tijd | < 15 min (van 2-4 uur) |
| Applicatie onboarding tijd | < 10 min |
| Context inheritance accuracy | 100% |
| Scanner auto-configuration | 100% per stack |

### Documentation

| Document | Description |
|----------|-------------|
| [fase-51-klant-template-service.md](docs/roadmap/phases/fase-51-klant-template-service.md) | Full specification |

---

## Fase 30: LLM Council Improvements (Week 233-235)

**Status:** PLANNED
**Priority:** MEDIUM
**Effort:** 72 uur (~2 weken)
**Dependencies:** Fase 23.5 ✅ (Confucius Orchestrator)

Verbeteringen aan het multi-model LLM Council systeem voor betere consensus en kwaliteitsreviews.

See: [docs/roadmap/phases/fase-30-llm-council-improvements.md](docs/roadmap/phases/fase-30-llm-council-improvements.md)

---

## Fase 33: DevStats Developer Metrics (Week 179-184)

**Status:** PLANNED
**Priority:** MEDIUM-HIGH (ROI 7.0)
**Effort:** 152 uur (~4-5 weken)

Developer contribution analytics dashboard gebaseerd op CNCF DevStats en GrimoireLab concepten.

| Component | Description |
|-----------|-------------|
| **GitDataCollector** | GitHub/GitLab API integration |
| **ContributionAnalyzer** | Per-developer, per-release statistics |
| **BusFactorCalculator** | Code ownership risk analysis |
| **ReleaseCorrelator** | Contributions per release/sprint |
| **D3Visualizations** | Heatmaps, charts, contribution graphs |

**Key Metrics:**
- Contribution frequency per developer over time
- Release impact (% bijdrage per release)
- PR cycle time (open → merge duration)
- Bus factor (kennisconcentratie risico)
- Code churn (lines added/removed ratio)

See: [docs/roadmap/phases/fase-33-devstats-dashboard.md](docs/roadmap/phases/fase-33-devstats-dashboard.md)

---

## Security Scanner Pipeline (Fase 34-40)

De security scanner pipeline bouwt voort op Fase 31 (CWE Scanner Suite), Fase 41 (Injection Scanners) en Fase 42 (Advanced FN Detection). Chronologische implementatie volgens Q1 2026 sprint calendar.

### Fase 34: Advanced Error Detectors (KW6-7 [w159-160])

**Status:** PLANNED
**Priority:** HIGH
**Dependencies:** Fase 31 ✅

See: [docs/roadmap/phases/fase-34-advanced-error-detectors.md](docs/roadmap/phases/fase-34-advanced-error-detectors.md)

### Fase 35: Data Integrity Scanners (KW8-9 [w161-162])

**Status:** PLANNED
**Priority:** HIGH
**Dependencies:** Fase 34

See: [docs/roadmap/phases/fase-35-data-integrity-scanners.md](docs/roadmap/phases/fase-35-data-integrity-scanners.md)

### Fase 36: Logic & Crypto Scanner (KW10-14 [w163-167])

**Status:** PLANNED
**Priority:** HIGH
**Effort:** ~72 uur
**Dependencies:** Fase 35

| Module | Effort | Description |
|--------|--------|-------------|
| CryptoErrorDetector | 24h | Hardcoded secrets, weak algorithms, timing attacks, cert validation |
| ControlFlowLogicDetector | 24h | Loop errors, if/else analysis, switch/case, exception handling |
| BooleanLogicDetector | 24h | Operator confusion, precedence, tautology/contradiction detection |

See: [docs/roadmap/phases/fase-36-logic-crypto-scanner.md](docs/roadmap/phases/fase-36-logic-crypto-scanner.md)

### Fase 37: Security Scanner Agent Integration (KW12-18 [w165-171])

**Status:** PLANNED
**Priority:** HIGH
**Dependencies:** Fase 31 ✅ (Fase 34-36 nice-to-have)

See: [docs/roadmap/phases/fase-37-security-agent-integration.md](docs/roadmap/phases/fase-37-security-agent-integration.md)

### Fase 38: Memory Safety Scanner

**Status:** PLANNED
**Dependencies:** Fase 37

| Scanner | Rules | Description |
|---------|-------|-------------|
| MemorySafetyDetector | 16 | Buffer overflow, use-after-free, double-free, null deref |
| ConcurrencyErrorDetector | 8 | Race conditions, deadlocks, thread safety |

See: [docs/roadmap/phases/fase-38-memory-safety-scanner.md](docs/roadmap/phases/fase-38-memory-safety-scanner.md)

### Fase 39: ML-Based Novel Vulnerability Detection

**Status:** PLANNED
**Dependencies:** Fase 42 ✅
**Note:** Hernummerd van origineel Fase 50 (ML-Novel) om conflict met Fase 50 (LRM Autonomous Operations) op te lossen.

| Component | Description |
|-----------|-------------|
| GitHub Vulnerability Crawler | Continuous learning from real vulnerabilities |
| CVE/NVD Monitor | Real-time vulnerability feed |
| Model Training Pipeline | Pre-computed embeddings, batch ML analysis |

See: [docs/roadmap/phases/fase-50-ml-novel-vulnerability-detection.md](docs/roadmap/phases/fase-50-ml-novel-vulnerability-detection.md) *(wordt hernoemd naar fase-39)*

### Fase 40: Hybrid False Positive Reduction

**Status:** PLANNED
**Dependencies:** Fase 39

| Component | Description |
|-----------|-------------|
| HeuristicFilter | Rule-based pre-filtering of findings |
| ML Confidence Scoring | Statistical model for finding validation |
| Hybrid Pipeline | Combined heuristic + ML reduction |

See: [docs/roadmap/phases/fase-40-hybrid-false-positive-reduction.md](docs/roadmap/phases/fase-40-hybrid-false-positive-reduction.md)

---

## Fase 44: AI Code Complaints Strategy (Week 185-192)

**Status:** PLANNED
**Priority:** CRITICAL (ROI 9.0)
**Effort:** 200 uur (~6-7 weken)

Research reveals AI-generated code has 1.7x more problems than human code, with 51% containing security vulnerabilities. This fase implements systematic countermeasures using MarQed's agent ecosystem.

| Component | Description |
|-----------|-------------|
| **AIComplaintDashboard** | Track metrics vs industry baselines (CodeRabbit, IEEE, Qodo) |
| **ContextPreservationService** | ADR tracking across code generations |
| **RealTimeQualityFeedback** | During-generation validation pipeline |
| **AutomatedFixGenerator** | Security vulnerability auto-fixes with confidence scoring |
| **LearningSystem** | Track patterns causing issues, continuous improvement |
| **GuardrailsPipeline** | 6-layer guardrails: CodeGen, Security, Architecture, Debt, Context, LLM |

**6 Attack Categories:**

| Category | Agent Assignment | Target |
|----------|------------------|--------|
| Quality & Correctness | Quinn + LLM Council | < 0.5x human issues |
| Security Vulnerabilities | Quinn + 21 Detectors | < 10% vulnerable |
| Architecture Problems | Felix + Anti-Pattern | >= 85% alignment |
| Technical Debt | Marcus + Clean Code | <= 3% duplication |
| Context & Understanding | Felix + Diana | ADR tracking |
| Productivity Paradox | Quinn + Tessa | < 5% incident rate |

**Success Metrics:**

| Metric | Industry AI | MarQed Target |
|--------|-------------|---------------|
| Major Issues/100 LOC | 1.7x human | < 0.5x human |
| Security Finding Rate | 51% | < 10% |
| SQL Injection Rate | 36% | < 1% |
| Architecture Alignment | Unknown | >= 85% |
| Test Coverage | Variable | >= 80% |
| Incident Rate per PR | 23.5% | < 5% |

See: [docs/roadmap/phases/fase-44-ai-code-complaints-strategy.md](docs/roadmap/phases/fase-44-ai-code-complaints-strategy.md)

---

## Fase 45: Reverse Traceability Service (Week 193-200)

**Status:** PLANNED
**Priority:** HIGH (ROI 7.5)
**Effort:** 160 uur (~5 weken)

Unified Code-to-Requirements reverse traceability service die bestaande services orkestreert om de vraag te beantwoorden: "Welke requirements implementeert deze code?"

| Component | Description |
|-----------|-------------|
| **ReverseTraceabilityService** | Centrale orchestratie van rule extraction, deep extraction, requirement generatie |
| **RequirementGenerator** | Business rules → User Stories transformatie met templates |
| **Database Models** | 4 nieuwe tabellen: sessions, requirements, links, documents |
| **RequirementsDocumentGenerator** | SRS en User Stories document generatie (PDF/DOCX/HTML) |
| **TraceabilityMatrix Integration** | Bidirectionele code ↔ requirement links |
| **Brown Paper Integration** | Optionele fase 6 in enhanced analysis |
| **Standalone Support** | Analyse van willekeurige source repo (zonder project) |

**Pipeline:**

```
Code → BusinessRuleExtractor → DeepExtraction → RequirementGenerator → TraceabilityMatrix
                ↓                     ↓                    ↓                    ↓
           IF-THEN rules        6-cycle hybrid      User Stories         Bidirectional
           Validation           Static+LLM          Acceptance           Links + Metrics
           Authorization        analysis            Criteria
```

**Identified Gaps (Addressed):**

| Gap | Solution |
|-----|----------|
| Brown Paper ↔ TraceabilityMatrix niet geintegreerd | Unified service met Brown Paper hooks |
| Business Rules extracted maar niet gelinkt | RequirementGenerator met rule→story links |
| Geen reverse traceability workflow | Dedicated `/api/reverse-traceability/*` endpoints |
| DeepExtraction niet verbonden aan requirements | Pipeline orchestratie in ReverseTraceabilityService |

**Success Metrics:**

| Metric | Target |
|--------|--------|
| Traceability Coverage | >= 80% code linked |
| Rule-to-Requirement Linking | >= 90% rules linked |
| Requirement Generation Accuracy | >= 75% human acceptance |
| Processing Time | < 5 min per 10K LOC |

See: [docs/roadmap/phases/fase-45-reverse-traceability-service.md](docs/roadmap/phases/fase-45-reverse-traceability-service.md)

---

## Fase 46: User Workflow Documentation (Week 201-208)

**Status:** PLANNED
**Priority:** HIGH (ROI 7.0)
**Effort:** 140 uur (~4-5 weken)

Automatische documentatie van user workflows door applicaties heen, met ASCII schermafbeeldingen, menu opties en navigatiepaden per gebruikerstype.

| Component | Description |
|-----------|-------------|
| **WorkflowExtractorService** | Extract workflows uit routes, templates, auth decorators |
| **ASCIIScreenGenerator** | Genereer ASCII representaties van schermen |
| **UserPersona Detection** | Detecteer gebruikerstypen uit code (admin, user, guest) |
| **WorkflowDocumentGenerator** | Markdown/HTML/PDF documentatie met flow diagrams |
| **Mermaid Integration** | Visuele flowcharts van gebruikerspaden |

**Workflow Documentatie Voorbeeld:**

```
WORKFLOW: Administrator - Gebruiker Aanmaken
Persona: Administrator | Stappen: 5 | Geschatte tijd: 3 min

STAP 1: Dashboard
┌───────────────────────────────────────────┐
│  ╔═══════════════════════════════════╗    │
│  ║  Menu:                            ║    │
│  ║  [1] Gebruikers  ◄── Keuze        ║    │
│  ║  [2] Projecten                    ║    │
│  ╚═══════════════════════════════════╝    │
└───────────────────────────────────────────┘
Keuzes: [1]→Stap 2 | [2]→Workflow B

STAP 2: Gebruikersbeheer
┌───────────────────────────────────────────┐
│  [Nieuwe Gebruiker] [Zoeken]              │
│  ─────────────────────────────            │
│  Jan Jansen    jan@...    [Bewerk]        │
└───────────────────────────────────────────┘
Acties: [Nieuwe Gebruiker]→Stap 3
```

**Success Metrics:**

| Metric | Target |
|--------|--------|
| Persona Detection Accuracy | >= 85% |
| Screen Detection Coverage | >= 80% |
| Workflow Completeness | >= 75% |
| ASCII Readability | >= 90% |

See: [docs/roadmap/phases/fase-46-user-workflow-documentation.md](docs/roadmap/phases/fase-46-user-workflow-documentation.md)

---

## Fase 47-50: LRM (Large Reasoning Model) Integration (Week 209-240)

**Status:** PLANNED
**Priority:** HIGH (ROI 9.0)
**Total Effort:** 480 uur (~12 weken)
**Documentation:** [backend/docs/plans/LRM-INTEGRATION-IMPLEMENTATION-PLAN.md](backend/docs/plans/LRM-INTEGRATION-IMPLEMENTATION-PLAN.md)

Integratie van het LRM (Large Reasoning Model) framework - een three-tier Claude-gebaseerd reasoning systeem voor complexe analyse taken.

### LRM Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  TIER 1: ROOT MODEL (Claude Opus 4.5)                           │
│  • Orchestration & synthesis, high-level reasoning              │
├─────────────────────────────────────────────────────────────────┤
│  TIER 2: SUB-LLM (Claude Haiku)                                 │
│  • Chunk-level analysis, pattern detection, fast processing     │
├─────────────────────────────────────────────────────────────────┤
│  TIER 3: PERSISTENT STATE (Python REPL + Redis/PostgreSQL)      │
│  • Context management, state persistence, memory compression    │
└─────────────────────────────────────────────────────────────────┘
```

### Fase 47: LRM Integration Foundation (Week 209-216)

**Effort:** 120 uur (~4 weken)

| Component | Description |
|-----------|-------------|
| **LRMService** | Core three-tier orchestration service |
| **LRMStateManager** | State persistence via Redis + PostgreSQL |
| **LRMChunkingService** | Smart content chunking with overlap |
| **LRMCostTracker** | Token usage tracking, budget alerts |
| **LRMPromptTemplates** | Versioned prompt templates per use case |
| **API Endpoints** | `/api/lrm/*` REST + SSE streaming (8 endpoints) |

### Fase 48: LRM Software Intake Enhancement (Week 217-224)

**Effort:** 140 uur (~4-5 weken)

| Component | Description |
|-----------|-------------|
| **LRMIntakeValidator** | Validate and correlate scan findings |
| **LRMSecurityAnalyzer** | Deep security analysis with cross-reference |
| **LRMTechDebtEvaluator** | Multi-level tech debt assessment |
| **LRMRecommendationEngine** | Prioritized remediation suggestions |
| **False Positive Reduction** | 60-80% reduction via LRM correlation |

### Fase 49: LRM Advanced Workflows (Week 225-232)

**Effort:** 120 uur (~4 weken)

| Component | Description |
|-----------|-------------|
| **LRMMaintenancePlanner** | Multi-level maintenance prioritization |
| **LRMBugAnalyzer** | Root cause analysis for bugs |
| **LRMRequirementsGenerator** | Code-to-requirements reverse engineering |
| **LRMCodeReviewer** | Deep code review with cross-file context |
| **LRMDocumentationGenerator** | Context-aware documentation generation |

### Fase 50: LRM Autonomous Operations (Week 233-240)

**Effort:** 100 uur (~3 weken)

| Component | Description |
|-----------|-------------|
| **LRMAutonomousScheduler** | Schedule overnight LRM analyses |
| **LRMBatchProcessor** | Process multiple projects in batch |
| **LRMQualityGate** | Automated go/no-go decisions |
| **LRMAlertingService** | Smart alerts on significant findings |
| **Ralph Wiggum Integration** | LRM as reasoning engine for Ralph |

### LRM Success Metrics

| Metric | Target |
|--------|--------|
| False Positive Reduction | >= 60% |
| Finding Correlation Accuracy | >= 85% |
| Human Acceptance of Recommendations | >= 80% |
| Processing Time per 100K LOC | < 15 minutes |
| Cost per 100K LOC Analysis | < $10 |
| Overnight Success Rate | >= 95% |

### LRM Cost Optimization Strategy

```
TIER 1 (Free/Cheap): Static analysis + Ollama pre-screening → Filter 60-70%
TIER 2 (Low Cost): Haiku chunk analysis → Handle 80-90% remaining
TIER 3 (High Value): Opus synthesis → Only 10-20% of processing

RESULT: 80-90% cost reduction vs. Opus-only approach
```

---

## Fase 60-64: Tracer/BART Gap Analysis Implementation (Week 179-234)

**Status:** PLANNED
**Priority:** P0-P3 (gefaseerd)
**Total Effort:** 344 uur (~24 weken)
**Source:** [Tracer/BART Gap Analyse](docs/roadmap/tracer-bart-gap-analysis.md)

Gap analyse van OpenClaw Tracer (Epic Mode) en BART Simpson concepten vs MarQed. MarQed heeft ~80% van Tracer en overtreft BART op backend-niveau. De 5 nieuwe fases adresseren presentatie-gaps.

### Fase 60: Observability Foundation - OTLP/Langfuse (Week 179-182) ★ P0

**Effort:** ~48 uur | **Dependencies:** Fase 23.5 ✅, CCTraceService ✅

| Component | Description |
|-----------|-------------|
| **OTelExporterService** | CCTrace spans → OTLP format adapter |
| **Confucius Span Instrumentation** | State transitions als OTLP spans |
| **Langfuse Deployment** | Self-hosted via Docker Compose |
| **Workflow Stage Instrumentation** | Per-stage traces met token/cost data |

### Fase 61: Progress Dashboard & Per-Ticket Cost (Week 183-188) ★ P1

**Effort:** ~64 uur | **Dependencies:** Fase 60, SSE Streaming ✅

| Component | Description |
|-----------|-------------|
| **ProgressDashboardService** | SSE events aggregeren naar per-ticket state |
| **Per-ticket Cost Tagging** | CCTrace met ticket-level cost tracking |
| **WebSocket Dashboard API** | Real-time workflow voortgang endpoint |
| **Agent Timeline API** | Gantt-achtige execution timeline data |

### Fase 62: Conversational Intake - Epic Mode (Week 193-198) ★ P1

**Effort:** ~80 uur | **Dependencies:** SpecShapingService ✅, IntakeToBacklogService ✅

| Component | Description |
|-----------|-------------|
| **ConversationalIntakeService** | Chat state machine (8 states) |
| **Domain Follow-up Templates** | Per-domein vraag templates (Web, API, Migration, Mobile) |
| **WebSocket Chat API** | Real-time chat endpoint met sessie management |
| **Context Memory** | HierarchicalMemoryManager extensie voor chat |

### Fase 63: Statistical Drift Detection (Week 207-212) ★ P2

**Effort:** ~72 uur | **Dependencies:** Fase 60, ThinkingPatternStore ✅, CheckAlignmentService ✅

| Component | Description |
|-----------|-------------|
| **Arize Phoenix Integration** | Embedding drift analyse met lokale evaluator |
| **StatisticalDriftDetector** | Cosine distance + KL divergence + centroid drift |
| **Confucius Drift Hooks** | Automatische PIV trigger bij embedding drift |

### Fase 64: Self-Evolution Activation (Week 229-234) ★ P3

**Effort:** ~80 uur | **Dependencies:** Fase 60+61, LLMCouncilService ✅, AgentEvolutionService ✅

| Component | Description |
|-----------|-------------|
| **AgentEvolutionService Activatie** | Hook in Confucius `on_stage_complete` lifecycle |
| **Constitution Council Review** | Multi-model council bij Constitution stage |
| **Specification Council Review** | Council review bij Specification + Task Generation |

### Tracer/BART Strategic Conclusions

1. **MarQed overtreft BART Simpson** - Confucius + PIV + 5 strategies + 9 anti-patterns > BART
2. **Grootste gap is presentatie** - OTLP export, dashboard, chat interface ontbreken
3. **Langfuse = hoogste ROI** - gratis dashboards via OTLP export
4. **Niet LangGraph/CrewAI adopteren** - Confucius is al superieur

See: [tracer-bart-gap-analysis.md](docs/roadmap/tracer-bart-gap-analysis.md)

---

## Fase 65: External Repo Intelligence — Drift/Kea/Octopus/Sec-Context (Week TBD)

**Status:** PLANNED
**Priority:** MEDIUM-HIGH
**Effort:** 170 uur (~5 weken)
**Dependencies:** Fase 23.5 ✅ (Confucius), Fase 30 (LLM Council), Fase 32E (Quality Harness)
**Source:** Gap analyse van 4 externe repos: [Drift](https://github.com/drift), [Kea-Research](https://github.com/kea-research), [Claude-Octopus](https://github.com/claude-octopus), [Sec-Context](https://github.com/sec-context)

### Overview

Bundelt micro-improvements uit 4 externe repo's in één fase. Geen grote architectuurwijzigingen — elk sub-item is een zelfstandige toevoeging aan bestaande services.

```
┌─────────────────────────────────────────────────────────────┐
│  FASE 65: EXTERNAL REPO INTELLIGENCE                         │
├─────────────────────────────────────────────────────────────┤
│  DRIFT (65A-65F):  Convention detection, call graph,         │
│                    confidence decay, corrections loop,       │
│                    test topology, memory consolidation       │
├─────────────────────────────────────────────────────────────┤
│  KEA (65G-65I):    Atomic fact extraction, SP synthesizer,   │
│                    MoA refinement step                       │
├─────────────────────────────────────────────────────────────┤
│  OCTOPUS (65J-65L): Workflow advisor, adversarial council,   │
│                     PRD scoring rubric                       │
├─────────────────────────────────────────────────────────────┤
│  SEC-CONTEXT (65M): Security anti-pattern guard              │
│                     (preventief + detectief + correctief)    │
└─────────────────────────────────────────────────────────────┘
```

### Sub-items

| ID | Bron | Beschrijving | Effort | Integreert met |
|----|------|-------------|--------|----------------|
| **65A** | Drift | Convention Detector Service (4 categorieën: API, Auth, Data-access, Error-handling) | 16h | Brown Paper Service |
| **65B** | Drift | Function-Level Call Graph (build + dead code + impact analysis) | 32h | dependency_graph_service + program_slicer |
| **65C** | Drift | Confidence Decay op Knowledge Base patterns | 8h | kb_context_provider (ChromaDB) |
| **65D** | Drift | Learning from Corrections (council feedback loop) | 12h | llm_council_service |
| **65E** | Drift | Test Topology Mapping (test-to-code mapping, multi-language) | 24h | Brown Paper analysis + regression-runner.sh |
| **65F** | Drift | Episodic-to-Semantic Memory Consolidation | 16h | HierarchicalMemoryManager |
| **65G** | Kea | Atomic Fact Extraction + Cross-Model Fact Verification | 12h | llm_council_service |
| **65H** | Kea | Surprisingly Popular Synthesizer Selection (dynamische chairman) | 8h | llm_council_service |
| **65I** | Kea | Optionele MoA Refinement Step (configureerbaar) | 10h | llm_council_service |
| **65J** | Octopus | Workflow Intent Advisor (adviserend, niet directief) | 8h | Confucius Orchestrator |
| **65K** | Octopus | Adversarial Council Member Role (devil's advocate) | 8h | llm_council_service |
| **65L** | Octopus | PRD Scoring Rubric (100-punt) voor PM Gate | 6h | Fase 32E pm-acceptance-gate.sh |
| **65M** | Sec-Context | Security Anti-Pattern Guard voor code-genererende agents | 10h | Confucius agent prompts + qa-gate.sh |

### 65A: Convention Detector Service (Drift) — 16h

Detecteert CODE-level conventies in legacy codebases: API route structuur, auth middleware patterns, data-access patterns, error handling patterns. Nul overlap met antipattern_detector.py (die PROCES anti-patterns detecteert). Voedt betere migration planning bij Brown Paper onboarding.

**Scope:** 4 categorieën, regex-based (geen AST/semantic), per-file output met confidence score.
**File:** Nieuw: `backend/app/services/convention_detector_service.py`

### 65B: Function-Level Call Graph (Drift) — 32h

Vult de ontbrekende laag tussen module-level (dependency_graph_service) en variable-level (program_slicer): welke functies roepen welke functies aan? Dode functies? Blast radius bij wijziging?

**Scope:** 3 capabilities: (1) call graph bouwen, (2) dode functie detectie, (3) change impact analysis.
**File:** Nieuw: `backend/app/services/call_graph_service.py`

### 65C: Confidence Decay op Knowledge Base — 8h

Half-life model voor KB patterns zodat verouderde patronen automatisch minder gewicht krijgen.
**File:** `backend/app/services/kb_context_provider.py` (wijzigen)

### 65D: Learning from Corrections — 12h

Council feedback loop: wanneer een council response gecorrigeerd wordt, leert het systeem van de correctie voor toekomstige sessies.
**File:** `backend/app/services/llm_council_service.py` (wijzigen)

### 65E: Test Topology Mapping — 24h

Test-to-code mapping: welke tests dekken welke code? Multi-language support. Integreert met Brown Paper analyse en regression-runner.sh.
**File:** Nieuw: `backend/app/services/test_topology_service.py`

### 65F: Episodic-to-Semantic Memory Consolidation — 16h

Automatische consolidatie van episodische herinneringen (individuele events) naar semantische kennis (patronen, regels).
**File:** `backend/app/services/hierarchical_memory_manager.py` (wijzigen)

### 65G: Atomic Fact Extraction + Fact Verification (Kea) — 12h

Breekt LLM Council responses op in 3-10 atomaire feiten. Evaluatoren markeren per-feit consensus/dispute. De synthesizer weet exact welke claims consensus hebben en welke betwist worden — ipv verstopt in een overall score.

**Implementatie:** Wijzig prompt format in Stage 1 (`atomic_facts[]`), Stage 2 peer review (`consensus_facts[]`, `flagged_facts[]`), Stage 3 synthesis (adresseer geflagde feiten).
**File:** `backend/app/services/llm_council_service.py` (wijzigen, ~3 methods)

### 65H: Surprisingly Popular Synthesizer Selection (Kea) — 8h

Dynamische chairman selectie ipv vast deepseek-r1. Elke evaluator geeft `predicted_winner`. SP score = werkelijke stemmen − voorspelde stemmen. Model dat "verrassend populair" is wint. Borda count als tiebreaker.

**File:** `backend/app/services/llm_council_service.py` (wijzigen, 1 nieuwe method `_select_synthesizer()`)

### 65I: Optionele MoA Refinement Step (Kea) — 10h

Extra stap tussen Response en Peer Review waar modellen elkaars antwoorden zien en hun eigen antwoord verbeteren. +6 LLM calls per sessie. Configureerbaar: default UIT voor snelle queries, AAN voor kritische architectuur-beslissingen.

**File:** `backend/app/services/llm_council_service.py` (wijzigen, 1 nieuwe stage)

### 65J: Workflow Intent Advisor (Octopus) — 8h

ADVISERENDE checker die suggereert of een ander workflow type beter past. NIET directief — HQ MarQed-assistent maakt de uiteindelijke keuze. Uitschakelbaar via config (`enable_workflow_advisor: true/false`).

```
┌─────────────────────────────────────────┐
│ HQ MarQed-Assistent (directief)         │
│   → Kiest workflow type                 │
│   → Kan 65J raadplegen (optioneel)      │
│   → Kan 65J uitschakelen                │
├─────────────────────────────────────────┤
│ 65J Workflow Advisor (adviserend)        │
│   → "Suggestie: Migration past beter"   │
│   → Alleen actief als HQ het vraagt     │
│   → Uitschakelbaar via config           │
└─────────────────────────────────────────┘
```

**File:** Nieuw: `backend/app/confucius/workflow_advisor.py`

### 65K: Adversarial Council Member (Octopus) — 8h

Eén council member krijgt de "devil's advocate" rol: argumenteer TEGEN opkomende consensus. Voorkomt groupthink. Score weegt 0.5x (voorkomt dat contrarian altijd wint).

**File:** `backend/app/services/llm_council_service.py` + `stage_council_config.py`

### 65L: PRD Scoring Rubric (Octopus) — 6h

100-punt scoring rubric met categorieën (completeness, testability, clarity, feasibility, security) voor de PM Acceptance Gate. Vervangt "PM Confidence >= 0.8" met rigoureuze, reproduceerbare scoring.

**File:** `mq/workflows/common/pm-acceptance-gate.sh` (wijzigen)

### 65M: Security Anti-Pattern Guard (Sec-Context) — 10h

Preventieve laag tegen AI-specifieke security anti-patterns (25+, met CWE referenties). Drie integratiepunten:

```
Integratiepunten:
┌─────────────────────────────────────────────────────────────┐
│ PREVENTIEF (bij generatie):                                  │
│   → Agent system prompts bevatten sec-context referentie    │
│   → Ralph guardrails.md bevat top-10 anti-patterns          │
├─────────────────────────────────────────────────────────────┤
│ DETECTIEF (na generatie):                                    │
│   → QA Gate as 9: snelle AI-antipattern pre-check           │
│   → Bestaande 21+ CWE scanners (diepere analyse)           │
├─────────────────────────────────────────────────────────────┤
│ CORRECTIEF (bij council review):                             │
│   → LLM Council peer review checkt tegen anti-patterns      │
│   → Adversarial member (65K) zoekt specifiek naar deze      │
└─────────────────────────────────────────────────────────────┘
```

**Files:**
- `backend/app/confucius/prompts/security_context.md` (nieuw, subset van BREADTH.md)
- `mq/workflows/common/qa-gate.sh` (wijzigen, as 9 toevoegen)
- `.marqed/guardrails.md` (wijzigen, top-10 regels)

### Afgewezen items (met onderbouwing)

| Item | Bron | Reden afwijzing |
|------|------|-----------------|
| Security Convention Detectors | Drift | 21+ CWE scanners + OWASP K1 + 65M dekken dit al. Conventie-detectie = framing verschil, niet inhoud. 16h voor marginale waarde. |
| 9 Memory Types | Drift | Confucius 3-tier + 65C (decay) + 65F (consolidation) geeft kernvoordelen zonder 9-tier complexiteit. Te granulair voor MarQed use case. |
| Double Diamond Workflow | Octopus | MarQed's 4 workflow types ZIJN domain-specifieke Diamond implementaties. 65J lost routing op. |
| 29-Persona Pattern | Octopus | MarQed's 11 agents zijn architectureel superieur (quality gates, PIV, state). Nuttige concepten al geëxtraheerd als 65K. |
| 75% Consensus Threshold | Octopus | MarQed's consensus is wiskundig geavanceerder (StdDev-normalized, outlier detectie, model weights). Flat 75% = downgrade. |
| Staggered Provider Execution | Kea | MarQed gebruikt lokale Ollama. Geen rate limits. Fase 47 LRM plant staggering voor cloud providers. |
| MCP als interface | Drift | Directe Python service calls zijn sneller, type-safe, testbaar. MCP voegt latency en foutgevoeligheid toe zonder voordeel. |

### Success Criteria

| Metric | Target |
|--------|--------|
| Convention detection accuracy (65A) | >= 80% per categorie |
| Call graph completeness (65B) | >= 90% functions mapped |
| Fact-level consensus visibility (65G) | Per-feit consensus/dispute zichtbaar |
| SP synthesizer selection (65H) | Betere synthese dan vast chairman |
| Security anti-pattern catch rate (65M) | >= 80% top-10 AI anti-patterns |
| Total effort | 170h |

### Documentation

| Document | Description |
|----------|-------------|
| [fase-65-external-repo-intelligence.md](docs/roadmap/phases/fase-65-external-repo-intelligence.md) | Full specification |

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
| [phases-current.md](docs/roadmap/phases-current.md) | KW5 [w158] status |
| [phases-planned.md](docs/roadmap/phases-planned.md) | Fase 22+ details & Q1 2026 sprint calendar |
| [phases-completed.md](docs/roadmap/phases-completed.md) | Fase 1-21 archive |
| [gap-analysis-complete-roadmap.md](docs/roadmap/gap-analysis-complete-roadmap.md) | Full 75-item specs |
| [workflow-separation-plan.md](docs/architecture/workflow-separation-plan.md) | Brown Paper/Migration/Quality separation |
| [fase-30-llm-council-improvements.md](docs/roadmap/phases/fase-30-llm-council-improvements.md) | Fase 30: LLM Council Improvements |
| [fase-32-ralph-wiggum-loop.md](docs/roadmap/phases/fase-32-ralph-wiggum-loop.md) | Ralph Wiggum autonomous loop |
| [fase-32e-quality-harness.md](docs/roadmap/phases/fase-32e-quality-harness.md) | 🆕 Quality Harness PM/QA Gates |
| [mq-ralph-wiggum-integration-plan.md](docs/mq-ralph-wiggum-integration-plan.md) | Fase 32: mq + Ralph Integration (536h) |
| [fase-33-devstats-dashboard.md](docs/roadmap/phases/fase-33-devstats-dashboard.md) | DevStats developer metrics |
| [fase-34-advanced-error-detectors.md](docs/roadmap/phases/fase-34-advanced-error-detectors.md) | Fase 34: Advanced Error Detectors |
| [fase-35-data-integrity-scanners.md](docs/roadmap/phases/fase-35-data-integrity-scanners.md) | Fase 35: Data Integrity Scanners |
| [fase-36-logic-crypto-scanner.md](docs/roadmap/phases/fase-36-logic-crypto-scanner.md) | Fase 36: Logic & Crypto Scanner |
| [fase-37-security-agent-integration.md](docs/roadmap/phases/fase-37-security-agent-integration.md) | Fase 37: Security Scanner Agent Integration |
| [fase-38-memory-safety-scanner.md](docs/roadmap/phases/fase-38-memory-safety-scanner.md) | Fase 38: Memory Safety Scanner |
| [fase-40-hybrid-false-positive-reduction.md](docs/roadmap/phases/fase-40-hybrid-false-positive-reduction.md) | Fase 40: Hybrid False Positive Reduction |
| [fase-41-injection-vulnerability-scanners.md](docs/roadmap/phases/fase-41-injection-vulnerability-scanners.md) | Fase 41: Injection Vulnerability Scanners ✅ |
| [fase-42-advanced-fn-detection.md](docs/roadmap/phases/fase-42-advanced-fn-detection.md) | Fase 42: Advanced False Negative Detection ✅ |
| [GREEN-PAPER-MAINTENANCE-ZERO-COMPLAINTS-PLAN.md](docs/plans/GREEN-PAPER-MAINTENANCE-ZERO-COMPLAINTS-PLAN.md) | Fase 43: Zero-Complaints Strategy |
| [fase-44-ai-code-complaints-strategy.md](docs/roadmap/phases/fase-44-ai-code-complaints-strategy.md) | Fase 44: AI Code Complaints Strategy |
| [fase-45-reverse-traceability-service.md](docs/roadmap/phases/fase-45-reverse-traceability-service.md) | Fase 45: Reverse Traceability Service |
| [fase-46-user-workflow-documentation.md](docs/roadmap/phases/fase-46-user-workflow-documentation.md) | Fase 46: User Workflow Documentation |
| [LRM-INTEGRATION-IMPLEMENTATION-PLAN.md](backend/docs/plans/LRM-INTEGRATION-IMPLEMENTATION-PLAN.md) | Fase 47-50: LRM Integration Master Plan |
| [fase-50-ml-novel-vulnerability-detection.md](docs/roadmap/phases/fase-50-ml-novel-vulnerability-detection.md) | Fase 39 (hernummerd): ML-Based Novel Vulnerability Detection |
| [tracer-bart-gap-analysis.md](docs/roadmap/tracer-bart-gap-analysis.md) | ★ Fase 60-64: Tracer/BART Gap Analyse & Verbeterplan |
| [fase-60-observability-foundation.md](docs/roadmap/phases/fase-60-observability-foundation.md) | ★ Fase 60: OTLP/Langfuse Observability Foundation |
| [fase-61-progress-dashboard.md](docs/roadmap/phases/fase-61-progress-dashboard.md) | ★ Fase 61: Progress Dashboard & Per-Ticket Cost |
| [fase-62-conversational-intake.md](docs/roadmap/phases/fase-62-conversational-intake.md) | ★ Fase 62: Conversational Intake (Epic Mode) |
| [fase-63-statistical-drift-detection.md](docs/roadmap/phases/fase-63-statistical-drift-detection.md) | ★ Fase 63: Statistical Drift Detection |
| [fase-64-self-evolution-activation.md](docs/roadmap/phases/fase-64-self-evolution-activation.md) | ★ Fase 64: Self-Evolution Activation |
| [fase-65-external-repo-intelligence.md](docs/roadmap/phases/fase-65-external-repo-intelligence.md) | ★ Fase 65: External Repo Intelligence (Drift/Kea/Octopus/Sec-Context) |

---

## Milestones

| Milestone | Week | Deliverable |
|-----------|------|-------------|
| **Stability Framework Complete** | 146 | All 8 detection categories ✅ |
| **FP Methodology Fixed** | 147 | NESMA/IFPUG compliant ✅ |
| **Confucius Orchestrator** | 154 | 4 workflow orchestrators ✅ |
| **PIV Loop Active** | 154 | Quality gates operational ✅ |
| **Context Engineering** | 155 | 60-80% token reduction ✅ |
| **Stage Council Review** | 157 | Multi-model LLM reviews ✅ |
| **Quality Impact Mapping** | 157 | Quality-to-functionality linking ✅ |
| **CWE Security Scanner** | 157 | Multi-scanner suite (288+ findings) ✅ |
| **Legacy Quickscan (A1)** | 157 | 15-min Go/No-Go assessment ✅ |
| **OWASP Integration (K1)** | 158 | 30+ patterns, all 10 categories, 39 tests ✅ |
| **CVE Database (K2)** | 158 | NVD/OSV integration, CVSS scoring, 30 tests ✅ |
| **Risk Heat Map (A4)** | 158 | D3.js format, severity aggregation, 30 tests ✅ |
| **Visual Dependency Graph (E1)** | 158 | D3.js/Cytoscape/DOT/Mermaid, 35 tests ✅ |
| **Context-Aware Docs (J1)** | 158 | AST parsing, multi-format export, 34 tests ✅ |
| **Secret Detection (K3)** | 157 | 50+ patterns, entropy detection ✅ |
| **Injection Vulnerability Scanners (Fase 41)** | 158 | 484 tests, 108 rules, 13 categories ✅ |
| **Advanced FN Detection (Fase 42)** | 158 | 4 scanners, 468 tests, ~272 rules ✅ |
| **Knowledge Base Integration (Fase 24-KB)** | 158 | KB1+KB5 done, KB2-KB4 merged ✅ |
| **Advanced Error Detectors (Fase 34)** | 159-160 | KW6-7, error detection pipeline |
| **Data Integrity Scanners (Fase 35)** | 161-162 | KW8-9, data integrity validation |
| **Logic & Crypto Scanner (Fase 36)** | 163-167 | KW10-14, crypto + logic error detection |
| **Security Agent Integration (Fase 37)** | 165-171 | KW12-18, agent ↔ scanner integration |
| **Memory Safety Scanner (Fase 38)** | post-37 | Buffer overflow, concurrency errors |
| **ML Novel Vulnerability (Fase 39)** | post-42 | ML-based novel pattern detection |
| **Hybrid FP Reduction (Fase 40)** | post-39 | Heuristic + ML false positive reduction |
| **Ralph Wiggum + mq Integration + Cole Medin (Fase 32)** | 175-190 | Autonomous overnight coding, mq integration, guardrails, morning reports, **fresh context pattern, security sandbox, markdown prompts** |
| **Quality Harness PM/QA Gates + Visual Verification (Fase 32E)** | 191-194 | PM Acceptance Gate, **9-axis QA Gate (+Playwright visual verification +AI anti-pattern pre-check)**, progressive regression, micro-deliverables |
| **DevStats Dashboard (Fase 33)** | 179-184 | Git contribution analytics, release tracking, bus factor |
| **Zero-Complaints Strategy (Fase 43)** | 177-184 | Zero critical complaints, <5% minor, schema hardening, quality metrics |
| **AI Code Complaints Strategy (Fase 44)** | 185-192 | 3x improvement over industry AI code metrics |
| **Reverse Traceability Service (Fase 45)** | 193-200 | Code→Requirements pipeline, DB opslag, requirements docs, >=80% coverage |
| **User Workflow Documentation (Fase 46)** | 201-208 | ASCII schermen, user workflows, persona detection, >=85% accuracy |
| **LRM Foundation (Fase 47)** | 209-216 | Three-tier LRM service, state management, API endpoints |
| **LRM Intake Enhancement (Fase 48)** | 217-224 | 60% false positive reduction, scan correlation, recommendations |
| **LRM Advanced Workflows (Fase 49)** | 225-232 | Maintenance planner, bug analyzer, requirements generator |
| **LRM Autonomous Operations (Fase 50)** | 233-240 | Overnight batch processing, Ralph integration, quality gates |
| **★ Observability Foundation (Fase 60)** | 179-182 | OTLP/Langfuse traces, cost tracking, span instrumentation |
| **★ Progress Dashboard (Fase 61)** | 183-188 | Real-time per-ticket voortgang, cost tagging, agent timeline |
| **★ Conversational Intake (Fase 62)** | 193-198 | Chat-based requirements, domain templates, auto-ticket generatie |
| **★ Statistical Drift Detection (Fase 63)** | 207-212 | Embedding drift, cosine/KL/centroid, PIV auto-trigger |
| **★ Self-Evolution Activation (Fase 64)** | 229-234 | AgentEvolution activatie, council reviews, pattern learning |
| **★ External Repo Intelligence (Fase 65)** | TBD | Convention detection, call graph, LLM Council upgrades (SP, atomic facts, adversarial), sec-context guard |
| **LLM Council Improvements (Fase 30)** | 233-235 | Multi-model consensus improvements |
| **COBOL Support** | 185 | B1 Analyzer complete |
| **LLM Collaboration** | 195 | B12 Framework active |
| **Full Platform** | 254 | All 85+ items complete |

---

*Updated: Week 162 (2026-02-02) - Fase 24.10 Business-Driven Epic Generation 100% afgerond: datetime fix + dataclass fix, E2E verified (440 epics, 2383 FP, 20099 SP, DB sync OK). Fase 65 toegevoegd: External Repo Intelligence (Drift/Kea/Octopus/Sec-Context) met 13 sub-items (65A-65M), 170h effort. QA Gate uitgebreid van 8→9 assen (as 9: AI security anti-pattern pre-check via sec-context). 7 items afgewezen met onderbouwing. Fase 32/32E verrijkt met Cole Medin your-claude-engineer benchmark analyse.*
