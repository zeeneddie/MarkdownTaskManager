# mq + Ralph Wiggum Integratie Plan

**Datum**: 2026-01-24
**Versie**: 1.0
**Status**: Draft - Ter Review
**Auteur**: Claude Code (Week 159)

---

## Executive Summary

Dit plan beschrijft de integratie van **mq CLI workflows** met het **Ralph Wiggum autonomous coding** systeem. De integratie combineert de developer-vriendelijke workflow structuur van mq met de overnight autonomous capabilities van Ralph Wiggum.

### Doelstelling

| Aspect | Huidige Situatie | Na Integratie |
|--------|------------------|---------------|
| **Overnight Coding** | Niet mogelijk | 8+ uur onbeheerd |
| **Context Management** | Fresh per sessie | Persistent + compression |
| **Error Recovery** | Manual developer | Automatisch + rollback |
| **Knowledge Reuse** | Platform lookup | + Guardrails accumulation |
| **Workflow Types** | 3 (bug, change, migration) | 4 (+overnight) |

### ROI

| Metric | Huidige Waarde | Verwachte Verbetering |
|--------|----------------|----------------------|
| Developer productiviteit | Baseline | +40% (overnight work) |
| Complex feature doorlooptijd | 40-80 uur | 20-40 uur |
| Context switch overhead | 30 min/dag | 5 min/dag |
| Failed iterations | 15-20% | 5-10% |

---

## Architectuur Overzicht

### Unified Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         mq + RALPH UNIFIED SYSTEM                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    CLI LAYER (mq)                                 │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐    │   │
│  │  │ marqed-    │ │ marqed-    │ │ marqed-    │ │ marqed-    │    │   │
│  │  │ bugfix.sh  │ │ changes.sh │ │ migration  │ │ overnight  │    │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └─────┬──────┘    │   │
│  │        │              │              │              │ NEW        │   │
│  └────────┼──────────────┼──────────────┼──────────────┼────────────┘   │
│           │              │              │              │                 │
│           ▼              ▼              ▼              ▼                 │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                  ORCHESTRATION LAYER                              │   │
│  │  ┌─────────────────────────┐  ┌─────────────────────────────┐    │   │
│  │  │   mq Task Coordinator   │  │   Ralph Loop Controller     │    │   │
│  │  │   (existing)            │◄─►│   (new)                     │    │   │
│  │  └─────────────────────────┘  └─────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                   SHARED SERVICES LAYER                           │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │   │
│  │  │  Unified     │ │  Knowledge   │ │  Validation  │              │   │
│  │  │  State Mgr   │ │  Service     │ │  Pipeline    │              │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘              │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │   │
│  │  │  Checkpoint  │ │  Guardrails  │ │  Memory      │              │   │
│  │  │  Service     │ │  Service     │ │  Compression │              │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                   PLATFORM LAYER (MarQed.ai)                      │   │
│  │  290+ services, 700+ endpoints, PostgreSQL, ChromaDB              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Mapping

| mq Component | Ralph Component | Unified Component |
|--------------|-----------------|-------------------|
| Task JSON | State File | **UnifiedStateManager** |
| Platform API | - | **PlatformBridge** |
| - | GuardrailsService | **GuardrailsService** |
| - | MemoryCompression | **MemoryCompressionService** |
| Vercel Browser | MultiPhaseValidation | **UnifiedValidationPipeline** |
| TechStackKnowledge | Archive/Learnings | **KnowledgeHubService** |
| - | CircuitBreaker | **CircuitBreakerService** |
| - | RollbackService | **CheckpointService** |
| prd-to-tasks.sh | PRP Framework | **PRPGeneratorService** |

---

## Implementatie Fases

### Fase Overzicht

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATIE ROADMAP (16 weken)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  FASE 1: FOUNDATION (Week 1-4)                                    80h   │
│  ══════════════════════════════════════════════════════════════════     │
│  ├── Unified State Manager                                              │
│  ├── Guardrails Service (standalone)                                    │
│  └── Basic Ralph Loop (CLI)                                             │
│                                                                          │
│  FASE 2: RALPH CORE (Week 5-8)                                   120h   │
│  ══════════════════════════════════════════════════════════════════     │
│  ├── PRP Generator Service                                              │
│  ├── Circuit Breaker + Rollback                                         │
│  ├── Memory Compression                                                 │
│  └── Completion Detection                                               │
│                                                                          │
│  FASE 3: MQ INTEGRATION (Week 9-12)                               80h   │
│  ══════════════════════════════════════════════════════════════════     │
│  ├── marqed-overnight.sh workflow                                       │
│  ├── Knowledge Hub (merge services)                                     │
│  ├── Unified Validation Pipeline                                        │
│  └── Platform Bridge                                                    │
│                                                                          │
│  FASE 4: PRODUCTION (Week 13-16)                                  80h   │
│  ══════════════════════════════════════════════════════════════════     │
│  ├── Dashboard Integration                                              │
│  ├── E2E Testing                                                        │
│  ├── Documentation                                                      │
│  └── Production Hardening                                               │
│                                                                          │
│  ═══════════════════════════════════════════════════════════════════    │
│  TOTAAL: 360 uur (~9 weken FTE)                                         │
│  ═══════════════════════════════════════════════════════════════════    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# DEEL I: EPICS & USER STORIES

---

## E1: Unified State Manager

**Beschrijving**: Een gedeelde state management layer die zowel mq task JSON als Ralph state files ondersteunt, met bidirectionele synchronisatie.

**Priority**: P0 - CRITICAL (Foundation)
**Effort**: 34 Story Points (13 dagen)
**Dependencies**: Geen (start epic)
**Fase**: 1 - Foundation

### User Stories

#### E1-US1: State Format Unification
**Als** workflow systeem
**Wil ik** een unified state format
**Zodat** mq en Ralph dezelfde state kunnen lezen/schrijven

**Acceptance Criteria**:
- [ ] Unified state schema die beide formats ondersteunt
- [ ] Backward compatible met bestaande mq task JSON
- [ ] Support voor Ralph-specifieke velden (iteration, guardrails_ref)
- [ ] JSON Schema validation

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Design unified state schema | 4h | Felix |
| 2 | Implement UnifiedState dataclass | 3h | Felix |
| 3 | mq task JSON adapter | 4h | Felix |
| 4 | Ralph state file adapter | 4h | Felix |
| 5 | Bidirectional sync logic | 6h | Felix |
| 6 | Unit tests | 4h | Tessa |

**Story Points**: 13

---

#### E1-US2: State Persistence Layer
**Als** workflow
**Wil ik** state persistent opslaan
**Zodat** ik kan herstarten na crashes of context overflow

**Acceptance Criteria**:
- [ ] File-based persistence (JSON + Markdown)
- [ ] PostgreSQL persistence (optioneel)
- [ ] Atomic writes (no corruption)
- [ ] Auto-recovery bij startup

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | File persistence service | 4h | Felix |
| 2 | PostgreSQL persistence service | 6h | Felix |
| 3 | Atomic write implementation | 3h | Felix |
| 4 | Recovery logic | 4h | Felix |
| 5 | Integration tests | 4h | Tessa |

**Story Points**: 13

---

#### E1-US3: State API Endpoints
**Als** dashboard
**Wil ik** state via API kunnen ophalen
**Zodat** ik real-time voortgang kan tonen

**Acceptance Criteria**:
- [ ] GET /api/v2/state/{workflow_id} - volledige state
- [ ] GET /api/v2/state/{workflow_id}/summary - compact overzicht
- [ ] WebSocket channel voor updates
- [ ] Response tijd < 100ms

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | State API router | 3h | Felix |
| 2 | Summary generation | 2h | Felix |
| 3 | WebSocket updates | 4h | Felix |
| 4 | API tests | 3h | Tessa |

**Story Points**: 8

---

## E2: Guardrails Service

**Beschrijving**: File-based lesson learning systeem dat kennis accumuleert across context windows en workflows.

**Priority**: P0 - CRITICAL (Foundation)
**Effort**: 21 Story Points (8 dagen)
**Dependencies**: E1 (State Manager)
**Fase**: 1 - Foundation

### User Stories

#### E2-US1: Guardrails File Management
**Als** Ralph loop
**Wil ik** een guardrails file kunnen lezen en schrijven
**Zodat** ik leer van eerdere fouten

**Acceptance Criteria**:
- [ ] `.marqed/guardrails.md` file format
- [ ] Categorie-gebaseerde organisatie
- [ ] Token limit management (max 2000 tokens)
- [ ] Automatic pruning van oude/irrelevante lessons

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | GuardrailsService class | 4h | Felix |
| 2 | Markdown parser/writer | 3h | Felix |
| 3 | Category management | 2h | Felix |
| 4 | Token counting + pruning | 3h | Felix |
| 5 | Unit tests | 3h | Tessa |

**Story Points**: 8

---

#### E2-US2: Lesson Extraction
**Als** workflow
**Wil ik** automatisch lessons extraheren uit failures
**Zodat** guardrails groeien zonder manual input

**Acceptance Criteria**:
- [ ] Error pattern detection
- [ ] Lesson generation via LLM
- [ ] Deduplicatie van vergelijkbare lessons
- [ ] Confidence scoring

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Error pattern detector | 4h | Felix |
| 2 | LLM lesson generator | 4h | Felix |
| 3 | Deduplication logic | 3h | Felix |
| 4 | Integration tests | 3h | Tessa |

**Story Points**: 8

---

#### E2-US3: Guardrails Injection
**Als** agent
**Wil ik** guardrails automatisch in mijn context krijgen
**Zodat** ik dezelfde fouten niet herhaal

**Acceptance Criteria**:
- [ ] Auto-inject bij iteration start
- [ ] Relevance filtering (alleen relevante lessons)
- [ ] Priority ordering (critical first)
- [ ] Context budget aware

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Injection service | 3h | Felix |
| 2 | Relevance filtering | 3h | Felix |
| 3 | Priority sorting | 2h | Felix |
| 4 | Unit tests | 2h | Tessa |

**Story Points**: 5

---

## E3: Ralph Loop Core

**Beschrijving**: De core autonomous execution loop met iteration management, completion detection, en circuit breakers.

**Priority**: P0 - CRITICAL
**Effort**: 42 Story Points (16 dagen)
**Dependencies**: E1, E2
**Fase**: 2 - Ralph Core

### User Stories

#### E3-US1: Basic Loop Execution
**Als** developer
**Wil ik** een autonomous loop kunnen starten
**Zodat** taken automatisch worden uitgevoerd

**Acceptance Criteria**:
- [ ] `ralph start --plan plan.md --max-iterations 20`
- [ ] Iteration tracking
- [ ] Git commit per iteration
- [ ] Progress logging

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | RalphLoopService skeleton | 4h | Felix |
| 2 | Iteration management | 4h | Felix |
| 3 | Git integration | 4h | Felix |
| 4 | Progress logging | 3h | Felix |
| 5 | CLI interface | 3h | Felix |
| 6 | Unit tests | 4h | Tessa |

**Story Points**: 13

---

#### E3-US2: Completion Detection
**Als** loop
**Wil ik** weten wanneer het werk klaar is
**Zodat** ik niet onnodig doorga

**Acceptance Criteria**:
- [ ] Dual-gate logic (criteria + exit signal)
- [ ] Task checkbox tracking
- [ ] Validation pass verification
- [ ] Confidence scoring

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | CompletionDetector class | 4h | Felix |
| 2 | Criteria evaluation | 3h | Felix |
| 3 | Exit signal parsing | 2h | Felix |
| 4 | Confidence calculation | 3h | Felix |
| 5 | Unit tests | 3h | Tessa |

**Story Points**: 8

---

#### E3-US3: Circuit Breaker
**Als** systeem
**Wil ik** runaway loops stoppen
**Zodat** kosten en resources beperkt blijven

**Acceptance Criteria**:
- [ ] Max iterations limit
- [ ] No-progress detection (N iterations zonder vooruitgang)
- [ ] Same-error detection (M keer dezelfde fout)
- [ ] Cost limit ($X max)
- [ ] Token limit (80K rotation)

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | CircuitBreaker class | 4h | Felix |
| 2 | Progress tracking | 3h | Felix |
| 3 | Error pattern matching | 3h | Felix |
| 4 | Cost tracking integration | 3h | Felix |
| 5 | Unit tests | 3h | Tessa |

**Story Points**: 8

---

#### E3-US4: Checkpoint & Rollback
**Als** loop
**Wil ik** kunnen terugkeren naar een vorige staat
**Zodat** ik kan herstellen van fouten

**Acceptance Criteria**:
- [ ] Checkpoint creation per N iterations
- [ ] Git-based rollback (soft/hard/selective)
- [ ] Regression test na rollback
- [ ] Checkpoint metadata storage

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | CheckpointService class | 4h | Felix |
| 2 | Git rollback strategies | 6h | Felix |
| 3 | Regression test runner | 4h | Tessa |
| 4 | Metadata persistence | 3h | Felix |
| 5 | Integration tests | 4h | Tessa |

**Story Points**: 13

---

## E4: PRP Generator Service

**Beschrijving**: Automatische generatie van engineered prompts via het PRP (Product Requirements Prompt) framework.

**Priority**: P1 - HIGH
**Effort**: 34 Story Points (13 dagen)
**Dependencies**: E1
**Fase**: 2 - Ralph Core

### User Stories

#### E4-US1: Codebase Research
**Als** PRP generator
**Wil ik** de codebase analyseren
**Zodat** ik relevante patterns en conventions vind

**Acceptance Criteria**:
- [ ] Pattern detection (file:line references)
- [ ] Convention extraction
- [ ] Similar implementation search
- [ ] Dependency mapping

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | CodebaseResearcher class | 4h | Felix |
| 2 | Pattern detector | 6h | Felix |
| 3 | Convention extractor | 4h | Felix |
| 4 | Similarity search (CodeRAG) | 4h | Felix |
| 5 | Unit tests | 4h | Tessa |

**Story Points**: 13

---

#### E4-US2: Requirements Generation
**Als** PRP generator
**Wil ik** success criteria genereren
**Zodat** completion verifieerbaar is

**Acceptance Criteria**:
- [ ] Machine-verifiable criteria
- [ ] Verification commands (npm test, etc.)
- [ ] Edge case identification
- [ ] Test requirements

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | RequirementsGenerator class | 4h | Felix |
| 2 | Criteria generation logic | 4h | Felix |
| 3 | Verification command mapping | 3h | Felix |
| 4 | Unit tests | 3h | Tessa |

**Story Points**: 8

---

#### E4-US3: Plan Generation
**Als** PRP generator
**Wil ik** een executable plan genereren
**Zodat** Ralph weet wat te doen

**Acceptance Criteria**:
- [ ] Atomic tasks met VALIDATE commands
- [ ] MIRROR references (pattern sources)
- [ ] GOTCHA warnings
- [ ] Dependency ordering

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | PlanGenerator class | 4h | Felix |
| 2 | Task atomization | 4h | Felix |
| 3 | Dependency resolution | 3h | Felix |
| 4 | Plan markdown formatter | 2h | Felix |
| 5 | Unit tests | 3h | Tessa |

**Story Points**: 8

---

#### E4-US4: Prompt Engineering
**Als** PRP generator
**Wil ik** een optimale prompt produceren
**Zodat** de agent effectief werkt

**Acceptance Criteria**:
- [ ] Context-aware prompt building
- [ ] Token budget optimization
- [ ] Guardrails injection
- [ ] Quality score estimation

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | PromptEngineer class | 3h | Felix |
| 2 | Context optimization | 3h | Felix |
| 3 | Quality scoring | 2h | Felix |
| 4 | Unit tests | 2h | Tessa |

**Story Points**: 5

---

## E5: Memory Compression Service

**Beschrijving**: Context handoff tussen agent runs met intelligente compressie voor token efficiency.

**Priority**: P1 - HIGH
**Effort**: 21 Story Points (8 dagen)
**Dependencies**: E1, E2
**Fase**: 2 - Ralph Core

### User Stories

#### E5-US1: Context Analysis
**Als** compression service
**Wil ik** context token usage analyseren
**Zodat** ik weet wanneer compressie nodig is

**Acceptance Criteria**:
- [ ] Token counting per context section
- [ ] Threshold detection (70% capacity)
- [ ] Essential vs. compressible classification
- [ ] Compression recommendations

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | ContextAnalyzer class | 4h | Felix |
| 2 | Token counter | 2h | Felix |
| 3 | Classification logic | 3h | Felix |
| 4 | Unit tests | 2h | Tessa |

**Story Points**: 8

---

#### E5-US2: Compression Engine
**Als** compression service
**Wil ik** context intelligent comprimeren
**Zodat** essentiële informatie behouden blijft

**Acceptance Criteria**:
- [ ] Keep: critical decisions, blockers, guardrails
- [ ] Summarize: completed work, patterns
- [ ] Discard: verbose logs, redundant context
- [ ] 95% essential information retention

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | CompressionEngine class | 4h | Felix |
| 2 | LLM summarization | 4h | Felix |
| 3 | Information retention validation | 3h | Felix |
| 4 | Unit tests | 3h | Tessa |

**Story Points**: 8

---

#### E5-US3: Handoff Generation
**Als** loop
**Wil ik** een handoff package voor de volgende run
**Zodat** context naadloos doorgaat

**Acceptance Criteria**:
- [ ] Continuation prompt generation
- [ ] Essential state packaging
- [ ] Checkpoint reference
- [ ] Resume instructions

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | HandoffGenerator class | 3h | Felix |
| 2 | Continuation prompt template | 2h | Felix |
| 3 | State packaging | 2h | Felix |
| 4 | Unit tests | 2h | Tessa |

**Story Points**: 5

---

## E6: mq Overnight Workflow

**Beschrijving**: Nieuwe mq workflow (`marqed-overnight.sh`) die Ralph integreert voor overnight autonomous coding.

**Priority**: P1 - HIGH
**Effort**: 26 Story Points (10 dagen)
**Dependencies**: E1-E5
**Fase**: 3 - mq Integration

### User Stories

#### E6-US1: Overnight Workflow Script
**Als** developer
**Wil ik** `marqed-overnight.sh` kunnen draaien
**Zodat** ik overnight autonomous coding krijg

**Acceptance Criteria**:
- [ ] `marqed-overnight.sh --init --task OVERNIGHT-001`
- [ ] PRD template voor overnight tasks
- [ ] Integration met Ralph loop
- [ ] Platform health check

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | marqed-overnight.sh script | 6h | Felix |
| 2 | OVERNIGHT-TEMPLATE.md | 2h | Felix |
| 3 | prompt-overnight.md | 2h | Felix |
| 4 | Ralph integration | 4h | Felix |
| 5 | Integration tests | 3h | Tessa |

**Story Points**: 8

---

#### E6-US2: Overnight Configuration
**Als** developer
**Wil ik** overnight runs configureren
**Zodat** ik controle heb over costs en scope

**Acceptance Criteria**:
- [ ] Max iterations configuratie
- [ ] Cost limit configuratie
- [ ] Approval gates configuratie
- [ ] Notification settings

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Configuration schema | 2h | Felix |
| 2 | settings-overnight.json | 2h | Felix |
| 3 | Validation logic | 2h | Felix |
| 4 | Unit tests | 2h | Tessa |

**Story Points**: 5

---

#### E6-US3: Morning Report
**Als** developer
**Wil ik** 's ochtends een rapport van overnight work
**Zodat** ik weet wat er gebeurd is

**Acceptance Criteria**:
- [ ] Summary van voltooide tasks
- [ ] Lijst van open blockers
- [ ] Cost overzicht
- [ ] Quality metrics
- [ ] Aanbevelingen voor follow-up

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | MorningReportGenerator class | 4h | Felix |
| 2 | Report template | 2h | Felix |
| 3 | Email/Slack notification | 3h | Felix |
| 4 | Unit tests | 2h | Tessa |

**Story Points**: 8

---

#### E6-US4: Existing Workflow Enhancement
**Als** developer
**Wil ik** bestaande workflows kunnen upgraden naar overnight
**Zodat** ik mid-project kan switchen

**Acceptance Criteria**:
- [ ] `marqed-changes.sh --overnight` flag
- [ ] `marqed-migration.sh --overnight-phase X` flag
- [ ] State migration van mq → Ralph format
- [ ] Seamless continuation

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | --overnight flag in changes.sh | 3h | Felix |
| 2 | --overnight-phase in migration.sh | 3h | Felix |
| 3 | State migration utility | 4h | Felix |
| 4 | Integration tests | 3h | Tessa |

**Story Points**: 5

---

## E7: Knowledge Hub Service

**Beschrijving**: Unified knowledge service die mq TechStackKnowledge, Ralph Guardrails, en Platform Experience Store combineert.

**Priority**: P1 - HIGH
**Effort**: 26 Story Points (10 dagen)
**Dependencies**: E2, Platform services
**Fase**: 3 - mq Integration

### User Stories

#### E7-US1: Knowledge Aggregation
**Als** workflow
**Wil ik** alle kennis uit één service halen
**Zodat** ik niet meerdere services hoef aan te roepen

**Acceptance Criteria**:
- [ ] Unified query interface
- [ ] Aggregates: TechStackKnowledge + Guardrails + ExperienceStore
- [ ] Relevance ranking
- [ ] Caching layer

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | KnowledgeHubService class | 4h | Felix |
| 2 | TechStackKnowledge adapter | 3h | Felix |
| 3 | Guardrails adapter | 2h | Felix |
| 4 | ExperienceStore adapter | 3h | Felix |
| 5 | Aggregation logic | 4h | Felix |
| 6 | Unit tests | 3h | Tessa |

**Story Points**: 13

---

#### E7-US2: Knowledge API
**Als** CLI
**Wil ik** knowledge via API ophalen
**Zodat** scripts het kunnen gebruiken

**Acceptance Criteria**:
- [ ] POST /api/v2/knowledge/query
- [ ] GET /api/v2/knowledge/guardrails/{project}
- [ ] GET /api/v2/knowledge/similar/{tech_stack}
- [ ] Response tijd < 2s

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Knowledge API router | 3h | Felix |
| 2 | Query endpoint | 3h | Felix |
| 3 | Guardrails endpoint | 2h | Felix |
| 4 | Similar projects endpoint | 2h | Felix |
| 5 | API tests | 3h | Tessa |

**Story Points**: 8

---

#### E7-US3: Knowledge Learning
**Als** workflow
**Wil ik** nieuwe kennis automatisch opslaan
**Zodat** de knowledge base groeit

**Acceptance Criteria**:
- [ ] Auto-extract lessons from failures
- [ ] Auto-extract patterns from successes
- [ ] Deduplication
- [ ] Quality scoring

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | KnowledgeLearner class | 3h | Felix |
| 2 | Success pattern extractor | 3h | Felix |
| 3 | Failure lesson extractor | 3h | Felix |
| 4 | Quality scoring | 2h | Felix |
| 5 | Unit tests | 2h | Tessa |

**Story Points**: 5

---

## E8: Unified Validation Pipeline

**Beschrijving**: Gecombineerde validation pipeline die mq Vercel Browser en Ralph MultiPhaseValidation verenigt.

**Priority**: P1 - HIGH
**Effort**: 26 Story Points (10 dagen)
**Dependencies**: E1, E3
**Fase**: 3 - mq Integration

### User Stories

#### E8-US1: Pipeline Configuration
**Als** workflow
**Wil ik** de validation pipeline configureren
**Zodat** ik relevante checks krijg

**Acceptance Criteria**:
- [ ] Phase enable/disable
- [ ] Threshold configuration
- [ ] Blocking vs. non-blocking phases
- [ ] Custom validation commands

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | ValidationConfig class | 3h | Felix |
| 2 | Phase configuration | 2h | Felix |
| 3 | Threshold management | 2h | Felix |
| 4 | Unit tests | 2h | Tessa |

**Story Points**: 5

---

#### E8-US2: 8-Phase Validation
**Als** workflow
**Wil ik** uitgebreide validation
**Zodat** alle aspecten gecheckt worden

**Acceptance Criteria**:
- [ ] Syntax validation
- [ ] Type checking
- [ ] Linting
- [ ] Unit tests
- [ ] Integration tests
- [ ] Security scan
- [ ] Performance check
- [ ] Documentation check

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | UnifiedValidationPipeline class | 4h | Felix |
| 2 | Syntax/Type/Lint phases | 4h | Felix |
| 3 | Test phases | 3h | Felix |
| 4 | Security phase (CWE Scanner) | 3h | Quinn |
| 5 | Performance phase | 3h | Felix |
| 6 | Documentation phase | 2h | Felix |
| 7 | Integration tests | 4h | Tessa |

**Story Points**: 13

---

#### E8-US3: Browser Validation Integration
**Als** workflow
**Wil ik** browser validation in de pipeline
**Zodat** UI changes gevalideerd worden

**Acceptance Criteria**:
- [ ] Vercel Browser integration
- [ ] Visual regression detection
- [ ] Screenshot capture
- [ ] Diff generation

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | BrowserValidationPhase class | 4h | Felix |
| 2 | Visual regression logic | 4h | Tessa |
| 3 | Screenshot management | 2h | Felix |
| 4 | Diff generation | 3h | Felix |
| 5 | Integration tests | 3h | Tessa |

**Story Points**: 8

---

## E9: Dashboard Integration

**Beschrijving**: Dashboard UI voor het monitoren van overnight runs, guardrails, en unified state.

**Priority**: P2 - MEDIUM
**Effort**: 26 Story Points (10 dagen)
**Dependencies**: E1, E6, E7
**Fase**: 4 - Production

### User Stories

#### E9-US1: Overnight Monitor
**Als** developer
**Wil ik** overnight runs monitoren via dashboard
**Zodat** ik de voortgang kan volgen

**Acceptance Criteria**:
- [ ] Real-time iteration progress
- [ ] Cost tracking
- [ ] Guardrails viewer
- [ ] Blocker alerts

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Overnight monitor page | 4h | Vicky |
| 2 | Progress visualization | 3h | Vicky |
| 3 | Cost chart | 2h | Vicky |
| 4 | WebSocket integration | 3h | Felix |
| 5 | Unit tests | 2h | Tessa |

**Story Points**: 8

---

#### E9-US2: Guardrails Manager
**Als** developer
**Wil ik** guardrails beheren via dashboard
**Zodat** ik lessons kan reviewen en aanpassen

**Acceptance Criteria**:
- [ ] Guardrails list per project
- [ ] Lesson detail view
- [ ] Add/edit/delete lessons
- [ ] Export/import

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Guardrails manager page | 4h | Vicky |
| 2 | CRUD operations | 3h | Vicky |
| 3 | Export/import | 2h | Felix |
| 4 | Unit tests | 2h | Tessa |

**Story Points**: 8

---

#### E9-US3: Morning Report View
**Als** developer
**Wil ik** morning reports in dashboard bekijken
**Zodat** ik snel kan zien wat overnight gebeurd is

**Acceptance Criteria**:
- [ ] Report history list
- [ ] Detailed report view
- [ ] Task drill-down
- [ ] Action items

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Morning report page | 4h | Vicky |
| 2 | Report detail component | 3h | Vicky |
| 3 | Task drill-down | 3h | Vicky |
| 4 | Action items | 2h | Vicky |
| 5 | Unit tests | 2h | Tessa |

**Story Points**: 10

---

# DEEL II: TECHNICAL SPECIFICATIONS

---

## Unified State Schema

```python
@dataclass
class UnifiedWorkflowState:
    """Unified state for mq and Ralph workflows."""

    # Core identity
    workflow_id: str                    # e.g., "OVERNIGHT-001"
    workflow_type: WorkflowType         # BUGFIX, CHANGES, MIGRATION, OVERNIGHT
    created_at: datetime
    updated_at: datetime

    # mq compatibility
    task_list_id: str                   # Maps to CLAUDE_CODE_TASK_LIST_ID
    tasks: List[UnifiedTask]

    # Ralph fields
    iteration: int = 0
    max_iterations: int = 20
    state_file_path: Optional[Path] = None
    guardrails_ref: Optional[str] = None

    # Shared
    status: WorkflowStatus              # PENDING, IN_PROGRESS, COMPLETED, FAILED, PAUSED
    progress_percentage: float = 0.0

    # Metadata
    project_path: str
    config: Dict[str, Any] = field(default_factory=dict)

    # Cost tracking
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    cost_limit_usd: float = 50.0

    # Checkpoints
    checkpoints: List[Checkpoint] = field(default_factory=list)
    last_good_checkpoint: Optional[str] = None


@dataclass
class UnifiedTask:
    """Task that works for both mq and Ralph."""

    # Core
    id: str
    title: str
    description: str
    status: TaskStatus                  # PENDING, IN_PROGRESS, COMPLETED, BLOCKED, SKIPPED

    # mq fields
    priority: str = "MEDIUM"
    dependencies: List[str] = field(default_factory=list)
    can_parallelize: bool = False
    estimated_time: str = ""

    # Ralph fields
    validation_command: Optional[str] = None
    mirror_reference: Optional[str] = None  # file:line pattern source
    gotcha: Optional[str] = None

    # Shared
    notes: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    session_id: Optional[str] = None    # For parallel execution
```

---

## Directory Structure

```
.marqed/
├── state/
│   ├── OVERNIGHT-001.json          # Unified state
│   └── OVERNIGHT-001.state.md      # Ralph state file (human-readable)
├── guardrails/
│   ├── global.md                   # Global guardrails
│   └── project-xyz.md              # Project-specific guardrails
├── checkpoints/
│   └── OVERNIGHT-001/
│       ├── checkpoint-001.json
│       └── checkpoint-002.json
├── archives/
│   └── 2026-01-24_OVERNIGHT-001/
│       ├── state.md
│       ├── plan.md
│       ├── learnings.md
│       └── report.md
├── reports/
│   └── morning/
│       └── 2026-01-25_OVERNIGHT-001.md
└── config/
    ├── settings-overnight.json
    └── validation-config.json
```

---

## API Endpoints Overview

### State API (`/api/v2/state`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /state/{workflow_id} | Get full state |
| GET | /state/{workflow_id}/summary | Get summary |
| PATCH | /state/{workflow_id} | Update state |
| POST | /state/{workflow_id}/checkpoint | Create checkpoint |
| POST | /state/{workflow_id}/rollback | Rollback to checkpoint |
| WS | /state/{workflow_id}/stream | Real-time updates |

### Ralph API (`/api/v2/ralph`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /ralph/start | Start Ralph loop |
| GET | /ralph/{id}/status | Get loop status |
| POST | /ralph/{id}/stop | Stop loop |
| POST | /ralph/{id}/pause | Pause loop |
| POST | /ralph/{id}/resume | Resume loop |
| GET | /ralph/{id}/iterations | Get iteration history |

### Knowledge API (`/api/v2/knowledge`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /knowledge/query | Unified knowledge query |
| GET | /knowledge/guardrails/{project} | Get project guardrails |
| POST | /knowledge/guardrails/{project} | Add guardrail lesson |
| GET | /knowledge/similar | Find similar projects |

### Validation API (`/api/v2/validation`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /validation/run | Run validation pipeline |
| GET | /validation/{workflow_id}/results | Get validation results |
| POST | /validation/visual-regression | Run visual regression |
| POST | /validation/performance | Run performance check |

---

## CLI Commands

### New Commands

```bash
# Start overnight workflow
marqed-overnight.sh --init --task OVERNIGHT-001

# Start overnight execution
marqed-overnight.sh --task OVERNIGHT-001 --max-iterations 30 --cost-limit 25

# Check morning report
marqed-overnight.sh --report OVERNIGHT-001

# Pause overnight (if still running)
marqed-overnight.sh --pause OVERNIGHT-001

# Resume overnight
marqed-overnight.sh --resume OVERNIGHT-001

# View guardrails
marqed-guardrails.sh --list --project my-project

# Add guardrail
marqed-guardrails.sh --add --project my-project --lesson "Always check null" --category "validation"

# Upgrade existing workflow to overnight
marqed-changes.sh --task CHANGE-123 --overnight
```

### Environment Variables

```bash
# Required
export MARQED_PROJECT_PATH="/path/to/project"
export CLAUDE_CODE_TASK_LIST_ID="OVERNIGHT-001"

# Optional
export MARQED_OVERNIGHT_MAX_ITERATIONS=20
export MARQED_OVERNIGHT_COST_LIMIT=50
export MARQED_GUARDRAILS_PATH=".marqed/guardrails/global.md"
export MARQED_CHECKPOINT_INTERVAL=5  # Create checkpoint every N iterations
```

---

# DEEL III: PLANNING & RESOURCES

---

## Week-by-Week Schedule

### Week 1-2: Foundation - State & Guardrails

| Week | Epic | Stories | Lead | Support |
|------|------|---------|------|---------|
| 1 | E1 | US1, US2 | Felix | Tessa |
| 2 | E1, E2 | US3, US1, US2 | Felix | Tessa |

**Deliverables**:
- [ ] UnifiedStateManager complete
- [ ] GuardrailsService complete
- [ ] API endpoints for state

### Week 3-4: Foundation - Basic Loop

| Week | Epic | Stories | Lead | Support |
|------|------|---------|------|---------|
| 3 | E2, E3 | US3, US1 | Felix | Tessa |
| 4 | E3 | US2, US3 | Felix | Tessa |

**Deliverables**:
- [ ] Basic Ralph loop working
- [ ] Completion detection
- [ ] Circuit breaker

### Week 5-6: Ralph Core - Advanced

| Week | Epic | Stories | Lead | Support |
|------|------|---------|------|---------|
| 5 | E3, E4 | US4, US1 | Felix | Tessa |
| 6 | E4 | US2, US3, US4 | Felix | Tessa |

**Deliverables**:
- [ ] Checkpoint & rollback
- [ ] PRP Generator complete
- [ ] Prompt engineering

### Week 7-8: Ralph Core - Memory

| Week | Epic | Stories | Lead | Support |
|------|------|---------|------|---------|
| 7 | E5 | US1, US2 | Felix | Tessa |
| 8 | E5 | US3 + integration | Felix | Tessa |

**Deliverables**:
- [ ] Memory compression
- [ ] Context handoff
- [ ] Full Ralph loop E2E test

### Week 9-10: mq Integration

| Week | Epic | Stories | Lead | Support |
|------|------|---------|------|---------|
| 9 | E6 | US1, US2 | Felix | Tessa |
| 10 | E6, E7 | US3, US4, US1 | Felix | Tessa |

**Deliverables**:
- [ ] marqed-overnight.sh
- [ ] Morning reports
- [ ] Knowledge Hub basics

### Week 11-12: mq Integration - Validation

| Week | Epic | Stories | Lead | Support |
|------|------|---------|------|---------|
| 11 | E7, E8 | US2, US3, US1 | Felix | Quinn |
| 12 | E8 | US2, US3 | Felix | Tessa, Quinn |

**Deliverables**:
- [ ] Knowledge API complete
- [ ] Unified validation pipeline
- [ ] Browser validation integrated

### Week 13-14: Production - Dashboard

| Week | Epic | Stories | Lead | Support |
|------|------|---------|------|---------|
| 13 | E9 | US1, US2 | Vicky | Felix |
| 14 | E9 | US3 | Vicky | Felix |

**Deliverables**:
- [ ] Overnight monitor dashboard
- [ ] Guardrails manager
- [ ] Morning report view

### Week 15-16: Production - Hardening

| Week | Focus | Activities | Lead |
|------|-------|------------|------|
| 15 | E2E Testing | Full workflow tests | Tessa |
| 16 | Documentation & Release | Docs, examples, release | Diana, Paul |

**Deliverables**:
- [ ] E2E test suite
- [ ] Performance optimization
- [ ] Documentation complete
- [ ] Release 1.0

---

## Resource Allocation

### Team per Week

| Week | Felix | Tessa | Vicky | Quinn | Diana | Paul |
|------|-------|-------|-------|-------|-------|------|
| 1 | 100% | 30% | - | - | - | - |
| 2 | 100% | 30% | - | - | - | - |
| 3 | 100% | 30% | - | - | - | - |
| 4 | 100% | 30% | - | - | - | - |
| 5 | 100% | 30% | - | - | - | - |
| 6 | 100% | 30% | - | - | - | - |
| 7 | 100% | 30% | - | - | - | - |
| 8 | 100% | 40% | - | - | - | - |
| 9 | 100% | 30% | - | - | - | - |
| 10 | 100% | 30% | - | - | - | - |
| 11 | 80% | 30% | - | 40% | - | - |
| 12 | 80% | 40% | - | 30% | - | - |
| 13 | 30% | 20% | 100% | - | - | - |
| 14 | 30% | 20% | 100% | - | - | - |
| 15 | 20% | 80% | 20% | 20% | - | 20% |
| 16 | 20% | 30% | - | - | 80% | 40% |

### Total Effort

| Agent | Uren | Weken |
|-------|------|-------|
| Felix | 288h | 16 |
| Tessa | 96h | 16 |
| Vicky | 64h | 4 |
| Quinn | 32h | 3 |
| Diana | 32h | 1 |
| Paul | 24h | 2 |
| **Totaal** | **536h** | - |

---

# DEEL IV: SUCCESS CRITERIA & RISKS

---

## Success Criteria

### Functional Requirements

- [ ] Overnight workflow runs 8+ uur onbeheerd
- [ ] Max 5% false completion detections
- [ ] Guardrails reduceren herhaalde fouten met 70%
- [ ] Rollback recovery time < 60 seconden
- [ ] Context compression behoudt 95% essentiële informatie

### Performance Metrics

| Metric | Target |
|--------|--------|
| Iteration latency | < 60s average |
| Token efficiency | 80K rotation |
| Cost per overnight run | < $25 average |
| Dashboard load time | < 2s |
| API response time | < 200ms |

### Integration Requirements

- [ ] Bestaande mq workflows blijven werken (backward compatible)
- [ ] Unified state werkt voor alle workflow types
- [ ] Knowledge Hub aggregeert alle bronnen correct
- [ ] Dashboard toont real-time updates

### Quality Gates

- [ ] 100+ unit tests passing
- [ ] 90%+ code coverage op nieuwe services
- [ ] 0 critical security issues (Quinn review)
- [ ] E2E tests voor alle workflows
- [ ] Documentation coverage 100%

---

## Risk Register

| ID | Risk | Kans | Impact | Score | Mitigatie |
|----|------|------|--------|-------|-----------|
| R1 | Overnight run crashes mid-execution | MEDIUM | HIGH | 6 | Checkpoint elke 5 iterations, auto-resume |
| R2 | Cost overrun overnight | MEDIUM | MEDIUM | 4 | Hard cost limits, circuit breaker |
| R3 | Context pollution after many iterations | MEDIUM | HIGH | 6 | Memory compression, 80K token rotation |
| R4 | Guardrails worden te groot | LOW | MEDIUM | 3 | Token limit (2000), auto-pruning |
| R5 | mq backward compatibility broken | LOW | HIGH | 4 | Adapter pattern, extensive testing |
| R6 | State corruption bij crash | MEDIUM | HIGH | 6 | Atomic writes, journaling |
| R7 | Knowledge Hub geeft irrelevante results | MEDIUM | MEDIUM | 4 | Relevance scoring, feedback loop |
| R8 | PRP generator maakt slechte prompts | MEDIUM | MEDIUM | 4 | Quality scoring, human review optie |
| R9 | Validation pipeline te langzaam | LOW | MEDIUM | 3 | Parallel phases, caching |
| R10 | Dashboard WebSocket connection drops | LOW | LOW | 2 | Auto-reconnect, fallback polling |

---

## Validation Checkpoint

### Fase 1 Exit Criteria (Week 4)

- [ ] UnifiedStateManager werkt voor mq tasks
- [ ] GuardrailsService kan lessons lezen/schrijven
- [ ] Basic Ralph loop draait 10 iterations
- [ ] State API endpoints functioneel

### Fase 2 Exit Criteria (Week 8)

- [ ] Completion detection accurate (>95%)
- [ ] Circuit breaker stopt runaway loops
- [ ] Checkpoints werken, rollback succesvol
- [ ] Memory compression behoudt context
- [ ] PRP genereert valid plans

### Fase 3 Exit Criteria (Week 12)

- [ ] marqed-overnight.sh werkt E2E
- [ ] Morning reports genereren correct
- [ ] Knowledge Hub aggregeert alle bronnen
- [ ] Unified validation pipeline alle 8 phases
- [ ] Bestaande mq workflows ongewijzigd

### Fase 4 Exit Criteria (Week 16)

- [ ] Dashboard volledig functioneel
- [ ] Overnight run 8+ uur succesvol
- [ ] Alle E2E tests passing
- [ ] Documentation complete
- [ ] Ready for production

---

## Glossary

| Term | Definitie |
|------|-----------|
| **mq** | MarQed CLI workflows (bash scripts) |
| **Ralph Loop** | Autonomous iteration loop tot completion |
| **PRP** | Product Requirements Prompt - auto-generated prompt |
| **Guardrails** | Geaccumuleerde lessons learned in markdown |
| **Circuit Breaker** | Safety mechanism dat runaway loops stopt |
| **Checkpoint** | Git-based recovery point |
| **Memory Compression** | Context handoff met summarization |
| **Overnight** | Unattended execution (8+ uur) |
| **Morning Report** | Summary van overnight work |
| **Knowledge Hub** | Unified service voor all knowledge sources |

---

## References

| Document | Locatie |
|----------|---------|
| mq Integration Plan | `docs/mq-integration-plan-van-aanpak.md` |
| Ralph Wiggum Fase 32 | `docs/roadmap/phases/fase-32-ralph-wiggum-loop.md` |
| mq README | `mq/docs/README.md` |
| mq Workflows | `mq/docs/WORKFLOWS.md` |
| Platform Analysis | `docs/marqed-platform-and-mq-analysis.md` |

---

**Document Status**: Draft v1.0
**Review Required**: Paul (Project Lead), Felix (Tech Lead)
**Next Review**: Week 160
**Target Start**: Week 161

---

*MarQed.ai Platform Team*
