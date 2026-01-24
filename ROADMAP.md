# MarQed Platform Roadmap

**Project:** MarQed AI Agent Software Platform
**Last Updated:** Week 159 (2026-01-24)
**Total Phases:** 50 | **Timeline:** Week 144-250

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
├── Fase 24.6: Restartable Workflows ✅ COMPLETE (Week 158)
├── Fase 24.8: Epic Generation Fix ✅ COMPLETE (Week 158)
├── Fase 24.7: Async Database Persistence ✅ COMPLETE (Week 159)
├── Fase 29: Quality-Functionality Impact Mapping ✅ COMPLETE (Week 156-157)
├── Fase 31: CWE Security Scanner Suite ✅ COMPLETE (Week 157)
└── Fase 24-A1: Legacy Quickscan ✅ COMPLETE (Week 157)

WEEK 157-244: GAP ANALYSIS IMPLEMENTATION (IN PROGRESS)
├── Fase 24: Quick Wins & Foundation (15 items) 🔄 13/15 DONE (A1+K3+D1+D2+K1+K2+A4+E1+J1+K4+A2+A3+D4) ← OPEN: B5,B6
├── Fase 25: Core Platform Enhancement (18 items)
├── Fase 26: AI & Automation (12 items)
├── Fase 27: Testing Excellence (8 items)
├── Fase 28: Advanced Integrations (10 items)
├── Fase GAP-29: Innovation & Scale (9 items)
├── Fase 32: Ralph Wiggum Autonomous Loop (Week 175-180) 🆕
├── Fase 33: DevStats Developer Metrics (Week 179-184) 🆕
├── Fase 43: Zero-Complaints Green Paper & Maintenance (Week 177-184) 🆕
├── Fase 44: AI Code Complaints Strategy (Week 185-192) 🆕
├── Fase 45: Reverse Traceability Service (Week 193-200) 🆕
├── Fase 46: User Workflow Documentation (Week 201-208) 🆕
├── Fase 47: LRM Integration Foundation (Week 209-216) 🆕
├── Fase 48: LRM Software Intake Enhancement (Week 217-224) 🆕
├── Fase 49: LRM Advanced Workflows (Week 225-232) 🆕
└── Fase 50: LRM Autonomous Operations (Week 233-240) 🆕
```

---

## Current Focus (Week 158-159)

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

### IMMEDIATE: Restartable Workflows + Brown Paper Test

| Task | Status | Details |
|------|--------|---------|
| **Fase 24.6 Restartable Workflows** | ✅ COMPLETE | Generic checkpoint/resume system for all workflows |
| **Fase 24.7 Async Refactoring** | ✅ COMPLETE | BrownPaperService + MarQedBrownPaperWorkflow async-first |
| **Brown Paper HCI-CRS Test** | 🔄 IN PROGRESS | Test workflow op /opt/projecten/hci-crs met lokale Ollama LLMs |

**Doel:** Validate Brown Paper workflow end-to-end met HCI-CRS legacy applicatie (793K LOC, ASP Classic/VBScript)

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
| **Fase 31 CWE Security Scanner** | ✅ COMPLETE | Multi-scanner suite, 288+ findings on HCI-CRS |
| **Fase 24-A1 Legacy Quickscan** | ✅ COMPLETE | 15-min assessment, Go/No-Go recommendation |
| **Fase 23.6 Stage Council Review** | ✅ COMPLETE | Multi-model LLM reviews per stage |
| **Fase 29 Quality Impact Mapping** | ✅ COMPLETE | Quality-to-functionality linking |
| **Fase 23.5 Confucius Orchestrator** | ✅ COMPLETE | 4 workflow orchestrators, PIV loop |
| **Fase 23 Context Engineering** | ✅ COMPLETE | 60-80% token reduction |
| **Test Suite** | ✅ COMPLETE | 2,700+ tests, 97.8% pass rate |
| **Fase 24 GAP Items** | 🔄 13/15 | Open: B5 (ASP.NET Core), B6 (PHP) |

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

## Fase 24 GAP Items Status (12/15 Complete)

### ✅ Completed (12 items)

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

### 🔴 Open (2 items)

| Item | Beschrijving | ROI | Effort | Priority |
|------|-------------|-----|--------|----------|
| **B5** | ASP.NET Core Analyzer | 4.8 | 4 weken | HIGH |
| **B6** | PHP Analyzer | 4.8 | 4 weken | MEDIUM |

**Next Priority:** B5 (ASP.NET Core Analyzer) - Highest ROI of remaining items

---

## GAP Analysis Phases (Week 151-232)

### Phase Summary

| Fase | Focus | Items | Weken | Key Deliverables |
|------|-------|-------|-------|------------------|
| **24** | Quick Wins | 15 (13✅/2🔴) | 12 | Legacy Quickscan, Secret Detection, Migration Patterns |
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

## Fase 32: Ralph Wiggum Autonomous Loop (Week 175-180)

**Status:** PLANNED
**Priority:** HIGH (ROI 8.5)
**Effort:** 160 uur (~5 weken)

Implementatie van de Ralph Wiggum techniek voor autonomous overnight coding met iteratieve loops en git-based state management.

| Component | Description |
|-----------|-------------|
| **RalphLoopService** | Autonomous execution loop met configurable iterations |
| **GuardrailsService** | File-based lesson learning (.marqed/guardrails.md) |
| **CompletionDetector** | Dual-gate exit logic, checkbox tracking |
| **CircuitBreaker** | Stuck detection, cost limits, token rotation |
| **CourseCorrectionService** | Dead-end detection, 5 Whys methodology |

**Production Harness (Cole Medin):**

| Component | Description |
|-----------|-------------|
| **InitializationAgent** | Context gathering before work starts |
| **StructuredProgressTracker** | Rich metrics beyond "files changed" |
| **StageApprovalWorkflow** | Human approval between stages |
| **RollbackService** | Git reset, regression testing |
| **MemoryCompressionService** | Context handoff between runs |
| **MultiPhaseValidationPipeline** | 8-phase validation (syntax → docs) |

**Key Features:**
- Overnight autonomous coding (uren onbeheerd draaien)
- Git als geheugen (fresh context bij token overflow)
- Guardrails file voor cross-context learning
- Human-in-loop approval at stage boundaries
- Error recovery with automated rollback

See: [docs/roadmap/phases/fase-32-ralph-wiggum-loop.md](docs/roadmap/phases/fase-32-ralph-wiggum-loop.md)

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
| [phases-planned.md](docs/roadmap/phases-planned.md) | Fase 22-33 details |
| [phases-completed.md](docs/roadmap/phases-completed.md) | Fase 1-21 archive |
| [gap-analysis-complete-roadmap.md](docs/roadmap/gap-analysis-complete-roadmap.md) | Full 75-item specs |
| [workflow-separation-plan.md](docs/architecture/workflow-separation-plan.md) | Brown Paper/Migration/Quality separation |
| [fase-32-ralph-wiggum-loop.md](docs/roadmap/phases/fase-32-ralph-wiggum-loop.md) | Ralph Wiggum autonomous loop |
| [fase-33-devstats-dashboard.md](docs/roadmap/phases/fase-33-devstats-dashboard.md) | DevStats developer metrics |
| [GREEN-PAPER-MAINTENANCE-ZERO-COMPLAINTS-PLAN.md](docs/plans/GREEN-PAPER-MAINTENANCE-ZERO-COMPLAINTS-PLAN.md) | 🆕 Fase 43: Zero-Complaints Strategy |
| [fase-44-ai-code-complaints-strategy.md](docs/roadmap/phases/fase-44-ai-code-complaints-strategy.md) | 🆕 Fase 44: AI Code Complaints Strategy |
| [fase-45-reverse-traceability-service.md](docs/roadmap/phases/fase-45-reverse-traceability-service.md) | 🆕 Fase 45: Reverse Traceability Service |
| [fase-46-user-workflow-documentation.md](docs/roadmap/phases/fase-46-user-workflow-documentation.md) | 🆕 Fase 46: User Workflow Documentation |
| [LRM-INTEGRATION-IMPLEMENTATION-PLAN.md](backend/docs/plans/LRM-INTEGRATION-IMPLEMENTATION-PLAN.md) | 🆕 Fase 47-50: LRM Integration Master Plan |

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
| **Ralph Wiggum Loop (Fase 32)** | 178 | Autonomous agent execution, guardrails, overnight coding |
| **DevStats Dashboard (Fase 33)** | 184 | Git contribution analytics, release tracking, bus factor |
| **Zero-Complaints Strategy (Fase 43)** | 184 | Zero critical complaints, <5% minor, schema hardening, quality metrics |
| **AI Code Complaints Strategy (Fase 44)** | 185-192 | 3x improvement over industry AI code metrics |
| **Reverse Traceability Service (Fase 45)** | 193-200 | Code→Requirements pipeline, DB opslag, requirements docs, >=80% coverage |
| **User Workflow Documentation (Fase 46)** | 201-208 | ASCII schermen, user workflows, persona detection, >=85% accuracy |
| **LRM Foundation (Fase 47)** | 209-216 | Three-tier LRM service, state management, API endpoints |
| **LRM Intake Enhancement (Fase 48)** | 217-224 | 60% false positive reduction, scan correlation, recommendations |
| **LRM Advanced Workflows (Fase 49)** | 225-232 | Maintenance planner, bug analyzer, requirements generator |
| **LRM Autonomous Operations (Fase 50)** | 233-240 | Overnight batch processing, Ralph integration, quality gates |
| **COBOL Support** | 185 | B1 Analyzer complete |
| **LLM Collaboration** | 195 | B12 Framework active |
| **Full Platform** | 250 | All 85+ items complete |

---

*Generated: Week 159 (2026-01-24)*
