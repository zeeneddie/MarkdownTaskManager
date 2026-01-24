# mq + Platform Integratie - Plan van Aanpak

**Datum**: 2026-01-24
**Versie**: 1.0
**Auteur**: Paul (Project Lead)
**Status**: Goedgekeurd voor implementatie

---

## Executive Summary

Dit plan beschrijft de realisatie van de **mq workflows + MarQed.ai Platform integratie** in 3 fasen over 9 weken, met een optionele Fase 4 na validatie. De integratie combineert de developer-vriendelijke CLI workflows van mq met de krachtige backend services van het MarQed.ai Platform (290+ services, 700+ endpoints).

### Doelstelling

| Aspect | Huidige Situatie | Doelstelling |
|--------|------------------|--------------|
| **Workflow Tracking** | CLI output only | Real-time Dashboard + CLI |
| **Knowledge Reuse** | Start from scratch | 20-40% snellere start door knowledge lookup |
| **Validation** | Basic screenshots | Visual regression + performance baseline |
| **Task Persistence** | JSON files | PostgreSQL + real-time sync |
| **Security Scanning** | Basic OWASP (30%) | CWE Scanner Suite (95%) |

---

## Fasering Overzicht

```
+-----------------------------------------------------------------------------+
|                    IMPLEMENTATIE FASERING (9+ weken)                          |
+-----------------------------------------------------------------------------+
|                                                                               |
|  FASE 1: FOUNDATION (Week 1-3)                                   [E1 + E5]   |
|  ════════════════════════════════════════════════════════════════════════    |
|  ├── E1: Unified Entry Point & CLI Bridge                                    |
|  └── E5: Platform Integration Layer (basis)                                  |
|                                                                               |
|  FASE 2: CORE INTEGRATION (Week 4-7)                             [E2 + E3]   |
|  ════════════════════════════════════════════════════════════════════════    |
|  ├── E2: Progress Dashboard                                                  |
|  └── E3: Tech Stack Knowledge Service                                        |
|                                                                               |
|  FASE 3: ENHANCEMENT (Week 8-9)                                  [E4]        |
|  ════════════════════════════════════════════════════════════════════════    |
|  ├── E4: Self-Validation Enhancement                                         |
|  └── Polish, Testing & Documentation                                         |
|                                                                               |
|  ═══════════════════════════════════════════════════════════════════════════ |
|  VALIDATIE CHECKPOINT                                                         |
|  ═══════════════════════════════════════════════════════════════════════════ |
|                                                                               |
|  FASE 4: TOEKOMST (NA VALIDATIE)                                 [V5 + V6]   |
|  ════════════════════════════════════════════════════════════════════════    |
|  └── Parallel Coordinator + GitOps (alleen na 100% Fase 1-3 validatie)       |
|                                                                               |
+-----------------------------------------------------------------------------+
```

---

# DEEL I: EPICS & USER STORIES

---

## E1: Unified Entry Point & CLI Bridge

**Beschrijving**: Een centrale CLI-naar-API bridge die alle mq workflows verbindt met het MarQed.ai Platform, inclusief health checks en gestandaardiseerde error handling.

**Priority**: P1 - HIGH
**Effort**: 13 Story Points (5 dagen)
**Dependencies**: Geen (start epic)
**Fase**: 1 - Foundation

### User Stories

#### E1-US1: Platform Health Check
**Als** developer
**Wil ik** dat mq workflows automatisch controleren of het platform beschikbaar is
**Zodat** ik een duidelijke foutmelding krijg als de backend niet draait

**Acceptance Criteria**:
- [ ] Health check binnen 5 seconden timeout
- [ ] Duidelijke Nederlandse foutmelding met instructies (`make start`)
- [ ] Check in alle 4 workflow scripts (bugfix, changes, migration, analyze)
- [ ] Exit code 1 bij offline platform

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | `check_platform_required()` functie in platform-api.sh | 2h | Felix |
| 2 | Integratie in marqed-bugfix.sh | 1h | Felix |
| 3 | Integratie in marqed-changes.sh | 1h | Felix |
| 4 | Integratie in marqed-migration.sh | 1h | Felix |
| 5 | Integratie in marqed-analyze.sh | 1h | Felix |
| 6 | Unit tests voor health check | 2h | Tessa |

**Story Points**: 3

---

#### E1-US2: CLI-naar-API Bridge
**Als** mq workflow
**Wil ik** eenvoudig API calls kunnen maken naar het platform
**Zodat** ik platform services kan aanroepen zonder curl commando's te herhalen

**Acceptance Criteria**:
- [ ] `marqed_api_call()` functie voor generieke API calls
- [ ] Automatische authorization header handling
- [ ] JSON response parsing met jq
- [ ] Error handling met duidelijke messages
- [ ] Retry logic (3x met exponential backoff)

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | `marqed_api_call()` functie implementeren | 3h | Felix |
| 2 | Authorization header handling | 1h | Quinn |
| 3 | Error handling en logging | 2h | Felix |
| 4 | Retry logic implementeren | 2h | Felix |
| 5 | Helper functies (create_workflow, update_task, etc.) | 3h | Felix |
| 6 | Integration tests | 2h | Tessa |

**Story Points**: 5

---

#### E1-US3: Workflow Lifecycle Management
**Als** developer
**Wil ik** dat workflows automatisch geregistreerd worden in het platform
**Zodat** ik de status kan volgen in het dashboard

**Acceptance Criteria**:
- [ ] `create_workflow()` bij workflow start
- [ ] `update_task_status()` bij fase-overgangen
- [ ] `complete_workflow()` bij succesvolle afronding
- [ ] Automatische workflow ID generatie (bijv. BUG-2026-01-24-001)

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Workflow lifecycle functies in platform-api.sh | 3h | Felix |
| 2 | Workflow ID generatie logica | 1h | Felix |
| 3 | Integratie in marqed-bugfix.sh workflow stappen | 2h | Felix |
| 4 | Integratie in marqed-changes.sh workflow stappen | 2h | Felix |
| 5 | Integration tests | 2h | Tessa |

**Story Points**: 5

---

## E2: Progress Dashboard

**Beschrijving**: Een real-time web dashboard in de Hub Portal voor het volgen van mq workflow voortgang, inclusief task status, logs en security scan resultaten.

**Priority**: P1 - HIGH
**Effort**: 21 Story Points (8 dagen)
**Dependencies**: E1 (CLI Bridge), E5 (API endpoints)
**Fase**: 2 - Core Integration

### User Stories

#### E2-US1: Workflow Status API
**Als** dashboard
**Wil ik** real-time workflow status kunnen ophalen via API
**Zodat** ik de voortgang kan tonen

**Acceptance Criteria**:
- [ ] GET /api/v2/workflow/active - lijst actieve workflows
- [ ] GET /api/v2/workflow/{id} - workflow details met tasks
- [ ] WebSocket channel voor real-time updates
- [ ] Response tijd < 200ms

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Workflow API router (workflow_integration.py) | 3h | Felix |
| 2 | WorkflowService met CRUD operaties | 4h | Felix |
| 3 | WebSocket/SSE implementatie voor real-time updates | 4h | Felix |
| 4 | SQLAlchemy models (Workflow, WorkflowTask, WorkflowLog) | 3h | Felix |
| 5 | Alembic migration | 1h | Felix |
| 6 | API tests | 3h | Tessa |

**Story Points**: 8

---

#### E2-US2: Dashboard UI - Workflow Overview
**Als** developer
**Wil ik** een visueel overzicht van alle actieve workflows
**Zodat** ik in een oogopslag de status kan zien

**Acceptance Criteria**:
- [ ] Workflow cards met naam, type, fase, percentage complete
- [ ] Progress bar per workflow
- [ ] Status indicators (pending, in_progress, completed, failed)
- [ ] Sorteerbaar op start tijd, type, status
- [ ] Auto-refresh elke 5 seconden OF WebSocket updates

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Dashboard layout HTML/CSS | 3h | Vicky |
| 2 | Workflow card component | 2h | Vicky |
| 3 | Progress bar component | 1h | Vicky |
| 4 | JavaScript voor API calls en updates | 3h | Felix |
| 5 | WebSocket client integratie | 2h | Felix |
| 6 | Responsive design (mobile) | 2h | Vicky |

**Story Points**: 5

---

#### E2-US3: Dashboard UI - Task Details
**Als** developer
**Wil ik** de details van een workflow kunnen bekijken
**Zodat** ik kan zien welke taken afgerond zijn en welke nog lopen

**Acceptance Criteria**:
- [ ] Task lijst per fase met status iconen
- [ ] Tijdstempel per taak (start, complete)
- [ ] Toon geschatte tijd vs werkelijke tijd
- [ ] Klik om task notes te bekijken
- [ ] Collapsible fases

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Task list component | 2h | Vicky |
| 2 | Phase accordion component | 2h | Vicky |
| 3 | Task detail modal/panel | 2h | Vicky |
| 4 | Time display (relative + absolute) | 1h | Vicky |

**Story Points**: 3

---

#### E2-US4: Log Viewer Integratie
**Als** developer
**Wil ik** de logs van een workflow kunnen bekijken in het dashboard
**Zodat** ik kan debuggen zonder naar de terminal te gaan

**Acceptance Criteria**:
- [ ] Real-time log streaming
- [ ] Log level filtering (debug, info, warning, error)
- [ ] Zoekfunctie in logs
- [ ] Download logs als file
- [ ] Syntax highlighting voor code snippets

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Log streaming endpoint | 2h | Felix |
| 2 | Log viewer component met virtualized scrolling | 3h | Vicky |
| 3 | Filter en zoek functionaliteit | 2h | Vicky |
| 4 | Download functie | 1h | Felix |

**Story Points**: 3

---

#### E2-US5: Security Scan Results Link
**Als** developer
**Wil ik** vanuit het dashboard direct naar security scan resultaten kunnen navigeren
**Zodat** ik bevindingen kan reviewen

**Acceptance Criteria**:
- [ ] Link naar CWE Scanner resultaten per workflow
- [ ] Summary badge (X critical, Y high, Z medium findings)
- [ ] Inline preview van top 3 findings
- [ ] Filter op severity

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Security scan API koppeling | 2h | Quinn |
| 2 | Security badge component | 1h | Vicky |
| 3 | Findings preview panel | 2h | Vicky |

**Story Points**: 2

---

## E3: Tech Stack Knowledge Service

**Beschrijving**: Een service die bij project start automatisch bestaande kennis opzoekt over de tech stack, eerdere projecten en bekende valkuilen.

**Priority**: P1 - HIGH
**Effort**: 26 Story Points (10 dagen)
**Dependencies**: E5 (Platform API endpoints)
**Fase**: 2 - Core Integration

### User Stories

#### E3-US1: Similar Projects Search
**Als** mq workflow
**Wil ik** vergelijkbare projecten kunnen vinden
**Zodat** ik kan leren van eerdere ervaringen

**Acceptance Criteria**:
- [ ] ChromaDB similarity search op tech stack + problem type
- [ ] Top 5 meest vergelijkbare projecten retourneren
- [ ] Similarity score per project (0-100%)
- [ ] Project metadata (naam, uitkomst, duur, lessons learned)

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | TechStackKnowledgeService skeleton | 2h | Felix |
| 2 | ChromaDB collection "project_knowledge" setup | 2h | Felix |
| 3 | Similarity search implementatie | 4h | Felix |
| 4 | Project metadata model | 2h | Felix |
| 5 | Unit tests | 3h | Tessa |

**Story Points**: 5

---

#### E3-US2: Experience Store Integration
**Als** TechStackKnowledgeService
**Wil ik** toegang tot de Experience Store
**Zodat** ik geleerde patronen kan ophalen

**Acceptance Criteria**:
- [ ] Koppeling met bestaande ExperienceStoreService
- [ ] Query op tech stack en problem type
- [ ] Pattern extractie met confidence scores
- [ ] Caching voor snelle herhaalde queries

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | ExperienceStoreService dependency injection | 1h | Felix |
| 2 | `_search_experiences()` method | 3h | Felix |
| 3 | Pattern aggregatie logica | 2h | Felix |
| 4 | Redis caching layer | 2h | Felix |
| 5 | Integration tests | 2h | Tessa |

**Story Points**: 5

---

#### E3-US3: Pitfalls Extraction
**Als** developer
**Wil ik** gewaarschuwd worden voor bekende valkuilen
**Zodat** ik dezelfde fouten niet herhaal

**Acceptance Criteria**:
- [ ] Pitfalls extractie uit experiences en similar projects
- [ ] Severity classificatie (critical, high, medium, low)
- [ ] Mitigatie suggesties per pitfall
- [ ] Deduplicatie van vergelijkbare pitfalls
- [ ] Ranking op frequentie en severity

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Pitfall dataclass model | 1h | Felix |
| 2 | `_extract_pitfalls()` method | 3h | Felix |
| 3 | Deduplicatie algoritme | 2h | Felix |
| 4 | Severity-based ranking | 1h | Felix |
| 5 | Unit tests | 2h | Tessa |

**Story Points**: 3

---

#### E3-US4: Effort Estimation from History
**Als** developer
**Wil ik** een effort schatting op basis van historische data
**Zodat** ik realistische verwachtingen heb

**Acceptance Criteria**:
- [ ] Min/max/avg/median uren berekening
- [ ] Confidence level (high/medium/low) gebaseerd op sample size
- [ ] Breakdown per fase indien beschikbaar
- [ ] Vergelijking met FP/SP schattingen

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | `_calculate_effort_estimate()` method | 2h | Eliza |
| 2 | Statistical analysis (mean, median, stddev) | 2h | Eliza |
| 3 | Confidence calculation logic | 1h | Eliza |
| 4 | Unit tests | 2h | Tessa |

**Story Points**: 3

---

#### E3-US5: Knowledge Lookup API Endpoint
**Als** CLI workflow
**Wil ik** een API endpoint om knowledge lookup te doen
**Zodat** ik bij workflow start relevante kennis krijg

**Acceptance Criteria**:
- [ ] POST /api/v2/knowledge/lookup endpoint
- [ ] Input: tech_stack[], problem_type
- [ ] Output: similar_projects, patterns, pitfalls, effort_estimate, recommendations
- [ ] Response tijd < 3 seconden

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Knowledge API router | 2h | Felix |
| 2 | Request/Response schemas | 1h | Felix |
| 3 | Endpoint implementatie | 2h | Felix |
| 4 | Performance optimization | 2h | Felix |
| 5 | API tests | 2h | Tessa |

**Story Points**: 3

---

#### E3-US6: CLI Knowledge Lookup Integration
**Als** developer die mq workflow start
**Wil ik** automatisch een knowledge lookup zien
**Zodat** ik geïnformeerd begin

**Acceptance Criteria**:
- [ ] `lookup_existing_knowledge()` functie in platform-api.sh
- [ ] Formatted output naar terminal (similar projects, pitfalls, estimate)
- [ ] Warnings voor critical pitfalls
- [ ] Integration in alle 4 workflow scripts

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | `lookup_existing_knowledge()` shell functie | 3h | Felix |
| 2 | Terminal formatting met kleuren | 1h | Felix |
| 3 | Integratie in marqed-bugfix.sh | 1h | Felix |
| 4 | Integratie in marqed-changes.sh | 1h | Felix |
| 5 | Integratie in marqed-migration.sh | 1h | Felix |
| 6 | Integratie in marqed-analyze.sh | 1h | Felix |

**Story Points**: 3

---

#### E3-US7: Knowledge Dashboard Panel
**Als** developer
**Wil ik** de knowledge lookup resultaten in het dashboard zien
**Zodat** ik ze kan refereren tijdens het werk

**Acceptance Criteria**:
- [ ] Knowledge panel in workflow detail view
- [ ] Collapsible secties voor similar projects, pitfalls, patterns
- [ ] Effort estimate visualisatie (range bar)
- [ ] Links naar gerelateerde projecten

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Knowledge panel component | 3h | Vicky |
| 2 | Similar projects cards | 2h | Vicky |
| 3 | Pitfalls warning list | 2h | Vicky |
| 4 | Effort estimate visualisatie | 1h | Vicky |

**Story Points**: 4

---

## E4: Self-Validation Enhancement

**Beschrijving**: Verbetering van de huidige Vercel Browser self-validation met visual regression en performance baseline integratie uit het platform.

**Priority**: P2 - MEDIUM
**Effort**: 13 Story Points (5 dagen)
**Dependencies**: E1 (CLI Bridge), E5 (Validation API)
**Fase**: 3 - Enhancement

### User Stories

#### E4-US1: Visual Regression Integration
**Als** mq workflow
**Wil ik** visual regression checks uitvoeren via het platform
**Zodat** ik UI regressies automatisch detecteer

**Acceptance Criteria**:
- [ ] Koppeling met bestaande VisualRegressionService
- [ ] Screenshot comparison met baseline
- [ ] Diff highlighting bij afwijkingen
- [ ] Threshold configureerbaar (bijv. 0.5% verschil)

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Validation API endpoint voor visual regression | 2h | Felix |
| 2 | `run_visual_regression()` shell functie | 2h | Felix |
| 3 | Diff image generatie en opslag | 2h | Tessa |
| 4 | Threshold configuratie | 1h | Felix |
| 5 | Integration tests | 2h | Tessa |

**Story Points**: 5

---

#### E4-US2: Performance Baseline Integration
**Als** mq workflow
**Wil ik** performance checks uitvoeren tegen een baseline
**Zodat** ik performance regressies detecteer

**Acceptance Criteria**:
- [ ] Koppeling met bestaande PerformanceBaselineService
- [ ] Response time vergelijking
- [ ] Throughput vergelijking
- [ ] Alert bij > 10% regressie

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Validation API endpoint voor performance | 2h | Felix |
| 2 | `run_performance_baseline()` shell functie | 2h | Felix |
| 3 | Baseline storage en vergelijking | 2h | Felix |
| 4 | Alert threshold configuratie | 1h | Felix |
| 5 | Integration tests | 2h | Tessa |

**Story Points**: 5

---

#### E4-US3: Validation Results in Dashboard
**Als** developer
**Wil ik** validation resultaten in het dashboard zien
**Zodat** ik snel kan reviewen of er regressies zijn

**Acceptance Criteria**:
- [ ] Validation tab in workflow detail
- [ ] Visual diff viewer met slider
- [ ] Performance metrics vergelijking (before/after)
- [ ] Pass/fail status per check

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Validation tab component | 2h | Vicky |
| 2 | Visual diff slider component | 2h | Vicky |
| 3 | Performance comparison chart | 2h | Vicky |

**Story Points**: 3

---

## E5: Platform Integration Layer

**Beschrijving**: De backend API endpoints en database modellen die de integratie tussen mq CLI en het platform mogelijk maken.

**Priority**: P1 - HIGH
**Effort**: 18 Story Points (7 dagen)
**Dependencies**: Geen (parallel met E1)
**Fase**: 1 - Foundation

### User Stories

#### E5-US1: Workflow Data Models
**Als** platform
**Wil ik** gestructureerde data modellen voor workflows
**Zodat** ik workflow status persistent kan opslaan

**Acceptance Criteria**:
- [ ] Workflow model met alle benodigde velden
- [ ] WorkflowTask model met fase, status, timing
- [ ] WorkflowLog model voor audit trail
- [ ] Foreign key relaties correct
- [ ] Indexes voor performance

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | SQLAlchemy Workflow model | 2h | Felix |
| 2 | SQLAlchemy WorkflowTask model | 2h | Felix |
| 3 | SQLAlchemy WorkflowLog model | 1h | Felix |
| 4 | Alembic migration file | 1h | Felix |
| 5 | Model unit tests | 2h | Tessa |

**Story Points**: 5

---

#### E5-US2: Workflow CRUD Endpoints
**Als** CLI
**Wil ik** workflows kunnen aanmaken, lezen, updaten via API
**Zodat** ik de workflow lifecycle kan beheren

**Acceptance Criteria**:
- [ ] POST /api/v2/workflow/ - create
- [ ] GET /api/v2/workflow/{id} - read
- [ ] PATCH /api/v2/workflow/{id} - update
- [ ] GET /api/v2/workflow/active - list active
- [ ] OpenAPI spec compleet

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Pydantic request/response schemas | 2h | Felix |
| 2 | WorkflowService CRUD methods | 3h | Felix |
| 3 | API router met endpoints | 3h | Felix |
| 4 | API tests | 2h | Tessa |

**Story Points**: 5

---

#### E5-US3: Task Management Endpoints
**Als** CLI
**Wil ik** tasks binnen een workflow kunnen beheren
**Zodat** ik fase-overgangen kan registreren

**Acceptance Criteria**:
- [ ] POST /api/v2/workflow/{id}/tasks - create task
- [ ] GET /api/v2/workflow/{id}/tasks - list tasks
- [ ] PATCH /api/v2/workflow/{id}/tasks/{task_id} - update status
- [ ] POST /api/v2/workflow/{id}/tasks/bulk - bulk create

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Task management endpoints | 3h | Felix |
| 2 | Bulk operations support | 2h | Felix |
| 3 | Task status state machine | 2h | Felix |
| 4 | API tests | 2h | Tessa |

**Story Points**: 5

---

#### E5-US4: Validation API Endpoints
**Als** CLI
**Wil ik** validation services kunnen aanroepen
**Zodat** ik visual en performance checks kan doen

**Acceptance Criteria**:
- [ ] POST /api/v2/validation/visual-regression
- [ ] POST /api/v2/validation/performance
- [ ] GET /api/v2/validation/{workflow_id}/results
- [ ] Koppeling met bestaande services

**Technische Taken**:
| # | Taak | Effort | Agent |
|---|------|--------|-------|
| 1 | Validation API router | 2h | Felix |
| 2 | Service koppeling (VisualRegression, Performance) | 2h | Felix |
| 3 | API tests | 2h | Tessa |

**Story Points**: 3

---

# DEEL II: PLANNING & DEPENDENCIES

---

## Dependency Graph

```
+------------------------------------------------------------------+
|                    EPIC DEPENDENCIES                               |
+------------------------------------------------------------------+
|                                                                    |
|                         E1: CLI Bridge                             |
|                              |                                     |
|                    +---------+---------+                           |
|                    |                   |                           |
|                    v                   v                           |
|            E2: Dashboard        E4: Validation                     |
|                    |                   |                           |
|                    |                   |                           |
|                    v                   |                           |
|            E3: Knowledge               |                           |
|                    |                   |                           |
|                    +--------+----------+                           |
|                             |                                      |
|                             v                                      |
|                    E5: Platform Layer                              |
|                    (parallel met E1)                               |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  LEGENDA:                                                          |
|  ──────► = "hangt af van"                                         |
|  E5 is parallel met E1 (geen dependency)                          |
|                                                                    |
+------------------------------------------------------------------+
```

---

## Week-voor-Week Planning

### Week 1: Foundation - API Design & Models

| Dag | Epic | User Story | Agent(s) | Deliverable |
|-----|------|------------|----------|-------------|
| Ma | E5 | US1 | Felix | SQLAlchemy models ontwerp |
| Di | E5 | US1 | Felix | Alembic migration |
| Wo | E1 | US1 | Felix | Platform health check functie |
| Do | E1 | US2 | Felix, Quinn | CLI bridge basis functies |
| Vr | E5 | US2 | Felix | Workflow CRUD endpoints |

**Deliverables Week 1**:
- [ ] Database models voor workflows (Workflow, WorkflowTask, WorkflowLog)
- [ ] Migration `xxx_add_workflow_tables.py`
- [ ] `platform-api.sh` met health check
- [ ] `/api/v2/workflow/` endpoints (create, read, update)

**Benodigde Agents**: Felix (lead), Quinn (security review)

---

### Week 2: Foundation - CLI Integration

| Dag | Epic | User Story | Agent(s) | Deliverable |
|-----|------|------------|----------|-------------|
| Ma | E1 | US2 | Felix | CLI bridge helper functies |
| Di | E1 | US3 | Felix | Workflow lifecycle functies |
| Wo | E5 | US3 | Felix | Task management endpoints |
| Do | E1 | - | Felix | Integratie in alle workflow scripts |
| Vr | E1, E5 | - | Tessa | Integration tests |

**Deliverables Week 2**:
- [ ] Complete `platform-api.sh` met alle helper functies
- [ ] Workflow integratie in marqed-*.sh scripts
- [ ] `/api/v2/workflow/{id}/tasks` endpoints
- [ ] Integration tests passing

**Benodigde Agents**: Felix (lead), Tessa (testing)

---

### Week 3: Foundation - Polish & Security

| Dag | Epic | User Story | Agent(s) | Deliverable |
|-----|------|------------|----------|-------------|
| Ma | E5 | US4 | Felix | Validation API endpoints |
| Di | E1-E5 | - | Quinn | Security review alle endpoints |
| Wo | E1-E5 | - | Tessa | E2E tests workflow lifecycle |
| Do | E1-E5 | - | Diana | API documentatie |
| Vr | E1-E5 | - | Paul | Fase 1 review & sign-off |

**Deliverables Week 3**:
- [ ] `/api/v2/validation/*` endpoints
- [ ] Security audit rapport (Quinn)
- [ ] E2E test suite voor CLI → API flow
- [ ] API documentatie in OpenAPI/Swagger
- [ ] Fase 1 COMPLETE checkpoint

**Benodigde Agents**: Felix, Quinn, Tessa, Diana, Paul

---

### Week 4: Dashboard - Backend

| Dag | Epic | User Story | Agent(s) | Deliverable |
|-----|------|------------|----------|-------------|
| Ma | E2 | US1 | Felix | Dashboard data aggregation |
| Di | E2 | US1 | Felix | WebSocket setup |
| Wo | E2 | US4 | Felix | Log streaming endpoint |
| Do | E2 | US1 | Felix | Real-time status updates |
| Vr | E2 | - | Tessa | Backend tests |

**Deliverables Week 4**:
- [ ] Dashboard backend endpoints compleet
- [ ] WebSocket channel voor real-time updates
- [ ] Log streaming werkend
- [ ] Backend test coverage > 80%

**Benodigde Agents**: Felix (lead), Tessa (testing)

---

### Week 5: Dashboard - Frontend

| Dag | Epic | User Story | Agent(s) | Deliverable |
|-----|------|------------|----------|-------------|
| Ma | E2 | US2 | Vicky | Dashboard layout |
| Di | E2 | US2, US3 | Vicky | Workflow cards & task list |
| Wo | E2 | US4 | Vicky | Log viewer component |
| Do | E2 | US5 | Vicky, Quinn | Security scan integration |
| Vr | E2 | - | Tessa | Frontend tests |

**Deliverables Week 5**:
- [ ] Progress Dashboard UI compleet
- [ ] Real-time updates werkend
- [ ] Log viewer geïntegreerd
- [ ] Security scan resultaten linkage

**Benodigde Agents**: Vicky (lead), Quinn (security), Tessa (testing)

---

### Week 6: Knowledge Service - Core

| Dag | Epic | User Story | Agent(s) | Deliverable |
|-----|------|------------|----------|-------------|
| Ma | E3 | US1 | Felix | TechStackKnowledgeService |
| Di | E3 | US1 | Felix | ChromaDB similarity search |
| Wo | E3 | US2 | Felix | Experience Store koppeling |
| Do | E3 | US3 | Felix | Pitfalls extraction |
| Vr | E3 | US4 | Eliza | Effort estimation |

**Deliverables Week 6**:
- [ ] TechStackKnowledgeService core methods
- [ ] ChromaDB "project_knowledge" collection
- [ ] Pitfalls extraction werkend
- [ ] Effort estimation met confidence

**Benodigde Agents**: Felix (lead), Eliza (estimation)

---

### Week 7: Knowledge Service - Integration

| Dag | Epic | User Story | Agent(s) | Deliverable |
|-----|------|------------|----------|-------------|
| Ma | E3 | US5 | Felix | Knowledge API endpoint |
| Di | E3 | US6 | Felix | CLI integration |
| Wo | E3 | US7 | Vicky | Dashboard knowledge panel |
| Do | E3 | - | Tessa | Integration tests |
| Vr | E3 | - | Paul | Knowledge service review |

**Deliverables Week 7**:
- [ ] `/api/v2/knowledge/lookup` endpoint
- [ ] `lookup_existing_knowledge()` in alle scripts
- [ ] Knowledge panel in dashboard
- [ ] Integration tests passing

**Benodigde Agents**: Felix, Vicky, Tessa, Paul

---

### Week 8: Self-Validation

| Dag | Epic | User Story | Agent(s) | Deliverable |
|-----|------|------------|----------|-------------|
| Ma | E4 | US1 | Felix, Tessa | Visual regression API |
| Di | E4 | US1 | Felix | CLI visual regression functie |
| Wo | E4 | US2 | Felix | Performance baseline API |
| Do | E4 | US2 | Felix | CLI performance functie |
| Vr | E4 | US3 | Vicky | Validation dashboard tab |

**Deliverables Week 8**:
- [ ] Visual regression via platform werkend
- [ ] Performance baseline checks werkend
- [ ] Validation tab in dashboard
- [ ] CLI functies voor validation

**Benodigde Agents**: Felix, Tessa, Vicky

---

### Week 9: Polish & Documentation

| Dag | Epic | User Story | Agent(s) | Deliverable |
|-----|------|------------|----------|-------------|
| Ma | ALL | - | Tessa | E2E tests bugfix workflow |
| Di | ALL | - | Tessa | E2E tests changes workflow |
| Wo | ALL | - | Tessa | E2E tests migration workflow |
| Do | ALL | - | Diana | User documentation |
| Vr | ALL | - | Paul | Final review & release |

**Deliverables Week 9**:
- [ ] Alle workflows getest E2E
- [ ] Documentatie compleet
- [ ] Bug fixes afgerond
- [ ] WBSO rapportage gevalideerd
- [ ] **RELEASE 1.0**

**Benodigde Agents**: Tessa, Diana, Paul (review), Quinn (final security)

---

## Resource Planning

### Team Samenstelling per Week

| Week | Felix | Quinn | Tessa | Vicky | Eliza | Diana | Paul |
|------|-------|-------|-------|-------|-------|-------|------|
| 1 | 100% | 20% | 20% | - | - | - | - |
| 2 | 100% | - | 40% | - | - | - | - |
| 3 | 60% | 40% | 40% | - | - | 20% | 20% |
| 4 | 100% | - | 40% | - | - | - | - |
| 5 | 20% | 20% | 30% | 100% | - | - | - |
| 6 | 80% | - | 20% | - | 40% | - | - |
| 7 | 60% | - | 40% | 40% | - | - | 20% |
| 8 | 80% | - | 40% | 30% | - | - | - |
| 9 | 20% | 20% | 60% | - | - | 60% | 40% |

### Totale FTE Inzet

| Agent | Rol | Totale Uren | Weken Actief |
|-------|-----|-------------|--------------|
| Felix | Lead Developer | 288h | 1-9 |
| Tessa | Test Engineer | 144h | 1-9 |
| Vicky | UI Developer | 96h | 5, 7, 8 |
| Quinn | Security | 48h | 1, 3, 5, 9 |
| Eliza | Estimation | 16h | 6 |
| Diana | Documentation | 32h | 3, 9 |
| Paul | Project Lead | 32h | 3, 7, 9 |

---

# DEEL III: RISICO'S & MITIGATIES

---

## Risico Register

| ID | Risico | Kans | Impact | Score | Mitigatie |
|----|--------|------|--------|-------|-----------|
| R1 | Platform downtime tijdens development | LOW | MEDIUM | 3 | Health checks, duidelijke errors, development mock mode |
| R2 | ChromaDB performance bij grote datasets | MEDIUM | MEDIUM | 4 | Pagination, query optimization, monitoring |
| R3 | WebSocket connectie verlies | MEDIUM | LOW | 2 | Automatische reconnect, fallback naar polling |
| R4 | Integration complexity CLI ↔ API | MEDIUM | HIGH | 6 | Incrementele aanpak, uitgebreide tests |
| R5 | Knowledge lookup geeft irrelevante resultaten | MEDIUM | MEDIUM | 4 | Tuning na launch, feedback loop, confidence thresholds |
| R6 | Dashboard performance bij veel actieve workflows | LOW | MEDIUM | 3 | Virtualized lists, lazy loading, pagination |
| R7 | Bestaande services incompatibel met nieuwe API | LOW | HIGH | 4 | Backward compatibility, versioned API |
| R8 | Fase 1 duurt langer dan gepland | MEDIUM | MEDIUM | 4 | Buffer in planning, MVP scope, weekly reviews |
| R9 | Security vulnerabilities in nieuwe endpoints | LOW | HIGH | 4 | Quinn security reviews, OWASP checks, pen testing |
| R10 | Dependency conflicts tussen services | LOW | MEDIUM | 3 | Pinned versions, integration tests, staging env |

### Risk Score Matrix

| Score | Actie |
|-------|-------|
| 1-2 | Accept |
| 3-4 | Monitor + Mitigate |
| 5-6 | Prioritize mitigation |
| 7-9 | Immediate action required |

---

## Kritieke Succesfactoren

### Fase 1 Validatie Checklist

Voordat we doorgaan naar Fase 4 (Parallel Coordinator), MOET het volgende gevalideerd zijn:

| # | Criterium | Validatie Methode | Target | Status |
|---|-----------|-------------------|--------|--------|
| 1 | Alle workflows werken sequentieel | E2E test | 100% pass | [ ] |
| 2 | Dashboard toont correcte status | Manual + automated | Real-time <2s | [ ] |
| 3 | Knowledge lookup geeft resultaten | Test met bekende stacks | >60% hit rate | [ ] |
| 4 | Self-validation detecteert regressies | Test met bekende issues | >90% detection | [ ] |
| 5 | Platform health check werkt | Test offline scenario | Duidelijke error | [ ] |
| 6 | Task persistence werkt | Kill/resume test | 100% recovery | [ ] |
| 7 | Geen kritieke bugs | Bug tracking | 0 P1 bugs | [ ] |
| 8 | Documentation compleet | Review | 100% coverage | [ ] |

### KPI's

| KPI | Target | Meetmethode |
|-----|--------|-------------|
| Workflow Success Rate | >90% | Automated metrics |
| Developer Satisfaction | >4/5 | Survey |
| Security Coverage | >95% | CWE Scanner report |
| Knowledge Reuse Rate | >60% | Lookup hit rate |
| Dashboard Response Time | <2s | Performance monitoring |
| Task Sync Reliability | >99.9% | Error rate tracking |

---

# DEEL IV: EFFORT SUMMARY

---

## Story Points per Epic

| Epic | Story Points | Dagen | Prioriteit |
|------|--------------|-------|------------|
| E1: CLI Bridge | 13 SP | 5 | P1 |
| E2: Progress Dashboard | 21 SP | 8 | P1 |
| E3: Tech Stack Knowledge | 26 SP | 10 | P1 |
| E4: Self-Validation | 13 SP | 5 | P2 |
| E5: Platform Integration | 18 SP | 7 | P1 |
| **TOTAAL** | **91 SP** | **35 dagen (7 weken)** | |

*Note: 2 weken buffer voor integratie en onvoorziene zaken = 9 weken totaal*

## Effort per Agent

| Agent | Story Points | Percentage |
|-------|--------------|------------|
| Felix | 58 SP | 64% |
| Tessa | 16 SP | 18% |
| Vicky | 12 SP | 13% |
| Quinn | 3 SP | 3% |
| Eliza | 2 SP | 2% |

---

# APPENDIX

---

## A. File Locaties

### Nieuwe Files (Te Maken)

| File | Locatie | Epic |
|------|---------|------|
| platform-api.sh | `mq/workflows/common/platform-api.sh` | E1 |
| workflow_integration.py | `backend/app/api/workflow_integration.py` | E5 |
| workflow_models.py | `backend/app/models/workflow_models.py` | E5 |
| techstack_knowledge_service.py | `backend/app/services/techstack_knowledge_service.py` | E3 |
| knowledge.py | `backend/app/api/knowledge.py` | E3 |
| validation_integration.py | `backend/app/api/validation_integration.py` | E5 |
| workflow-dashboard.html | `backend/static/dashboards/workflow-dashboard.html` | E2 |
| xxx_add_workflow_tables.py | `backend/alembic/versions/` | E5 |

### Bestaande Files (Te Wijzigen)

| File | Wijziging | Epic |
|------|-----------|------|
| marqed-bugfix.sh | + health check, + workflow registration | E1 |
| marqed-changes.sh | + health check, + workflow registration | E1 |
| marqed-migration.sh | + health check, + workflow registration | E1 |
| marqed-analyze.sh | + health check, + workflow registration | E1 |
| main.py | + include workflow_integration router | E5 |

---

## B. API Endpoints Overzicht

### Workflow API (/api/v2/workflow)

| Method | Endpoint | Beschrijving |
|--------|----------|--------------|
| POST | / | Create workflow |
| GET | /{id} | Get workflow details |
| PATCH | /{id} | Update workflow |
| GET | /active | List active workflows |
| POST | /{id}/tasks | Create task |
| GET | /{id}/tasks | List tasks |
| PATCH | /{id}/tasks/{task_id} | Update task |
| POST | /{id}/tasks/bulk | Bulk create tasks |
| GET | /{id}/logs | Get workflow logs |
| WS | /{id}/stream | WebSocket updates |

### Knowledge API (/api/v2/knowledge)

| Method | Endpoint | Beschrijving |
|--------|----------|--------------|
| POST | /lookup | Knowledge lookup |
| GET | /projects | List known projects |
| GET | /patterns | List known patterns |

### Validation API (/api/v2/validation)

| Method | Endpoint | Beschrijving |
|--------|----------|--------------|
| POST | /visual-regression | Run visual diff |
| POST | /performance | Run performance check |
| GET | /{workflow_id}/results | Get all validation results |

---

## C. Glossary

| Term | Definitie |
|------|-----------|
| **mq** | MarQed CLI workflows (bash scripts in mq/ folder) |
| **Platform** | MarQed.ai FastAPI backend (290+ services) |
| **Workflow** | Een bugfix, changes, migration of analyze sessie |
| **Task** | Een individuele stap binnen een workflow |
| **Phase** | Een groep gerelateerde tasks (bijv. Phase 1: Bug Reproduction) |
| **Knowledge Lookup** | Automatisch zoeken naar eerdere ervaring met tech stack |
| **CLI Bridge** | Shell functies die CLI en API verbinden |
| **Self-Validation** | Automatische checks (visual regression, performance) |

---

**Document Status**: Final v1.0
**Goedgekeurd door**: Paul (Project Lead)
**Datum**: 2026-01-24
**Next Review**: Na Fase 1 completion (Week 3)

---

*MarQed.ai Platform Team*
