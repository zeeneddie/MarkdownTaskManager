# Onboarding Workflow Analysis — Fase 24.9

> **Doel:** Factuele analyse van alle Brown Paper / onboarding workflows, per workflow de logische stappen,
> en aantekeningen over wat WEL, NIET, of VERBETERD in de nieuwe unified "Onboarding" workflow moet.
>
> **Scope:** Onboarding (niet migration).
> **Bron:** Code-analyse van `brown_paper_service.py`, `confucius/workflows/`, `extraction_integration_service.py`, `schemas/workflow.py`, `models/`.
> **Datum:** 2026-02-02 (Week 162)

---

## Inhoudsopgave

1. [Workflow Inventaris](#1-workflow-inventaris)
2. [Workflow A: BrownPaperService (Oud, Bottom-Up)](#2-workflow-a-brownpaperservice-oud-bottom-up)
3. [Workflow B: MarQedBrownPaperWorkflow (Nieuw, Top-Down)](#3-workflow-b-marqedbrownpaperworkflow-nieuw-top-down)
4. [Workflow C: BrownPaperOrchestrator (Confucius 7-Stage)](#4-workflow-c-brownpaperorchestrator-confucius-7-stage)
5. [Workflow D: MigrationOrchestrator (Confucius 8-Stage)](#5-workflow-d-migrationorchestrator-confucius-8-stage)
6. [Workflow E: OnboardingWorkflowIntegration](#6-workflow-e-onboardingworkflowintegration)
7. [Workflow F: UnifiedOnboardingService (Bestaande Orchestrator)](#7-workflow-f-unifiedonboardingservice-bestaande-orchestrator)
8. [Vergelijkingstabel](#8-vergelijkingstabel)
9. [Entry Point Analyse](#9-entry-point-analyse)
10. [Aanbevelingen & Verbeterpunten](#10-aanbevelingen--verbeterpunten)
11. [Conclusie](#11-conclusie)

---

## 1. Workflow Inventaris

| # | Workflow | Locatie | LOC | Aanpak | Status |
|---|---------|---------|-----|--------|--------|
| A | BrownPaperService | `brown_paper_service.py:277-3411` | ~3100 | Bottom-up code analyse | Actief, legacy |
| B | MarQedBrownPaperWorkflow | `brown_paper_service.py:3516-5410` | ~1900 | Top-down 8-questions | Actief, primary |
| C | BrownPaperOrchestrator | `confucius/workflows/brown_paper.py` | ~470 | Confucius 7-stage agent | Actief, orchestratie |
| D | MigrationOrchestrator | `confucius/workflows/migration.py` | ~480 | Confucius 8-stage agent | Actief, orchestratie |
| E | OnboardingWorkflowIntegration | `extraction_integration_service.py:489` | ~100 | Trigger bij registratie | Actief, entry point |
| **F** | **UnifiedOnboardingService** | `unified_onboarding_service.py` | ~815 | **8-step orchestrator + reconciliation** | **Actief, meest compleet** |

**Relatie:**
- A is de oudste service, doet directe code-analyse (geen questionnaire)
- B bouwt voort op A (hergebruikt Enhanced Analysis Pipeline van A)
- C en D zijn Confucius-wrappers die A of B aansturen via agents + quality gates
- E is een trigger-hook die bij project registratie een analyse start
- **F combineert A + B + Enhanced Pipeline en voegt Reconciliation toe (bottom-up vs top-down vs enhanced)**

---

## 2. Workflow A: BrownPaperService (Oud, Bottom-Up)

**File:** `backend/app/services/brown_paper_service.py:277-3411`

### Logische Stappen

#### Stap 1: Session Aanmaken (Line 304)
- `start_session(application_id, scan_path, tech_stack)`
- Maakt BrownPaperSession dataclass aan
- Slaat op in BrownPaperSessionDB
- **LLM:** Nee | **DB:** Ja

#### Stap 2: Code Analyse (Line 853)
- `analyze_application(session_id, options)`
- 11 analyse-services parallel:
  1. DependencyGraphService (module deps, 12 talen)
  2. CodeAnalysisAggregatorService (LOC, complexity)
  3. LayeredAnalysisService (layers detectie)
  4. FoundationDetectionService (infra modules)
  5. BackgroundJobDetectorService (Week 131)
  6. LoadEstimationService (capacity, Week 131)
  7. DeadCodeDetectorService (Week 132-133)
  8. RuntimeAnalysisService (runtime coverage, Week 132-133)
  9. CodeCoverageAnalyzerService (test coverage, Week 132-133)
  10. DataLineageService (data flow, Week 136-137)
  11. SIG Quality Metrics (7 analyzers, Week 144)
- Slaat op in BrownPaperAnalysisDB
- **LLM:** Indirect (stability analysis) | **DB:** Ja

#### Stap 3: Domain Extraction (Line 1653)
- `_extract_domains(analysis)`
- Heuristiek: directory patterns, class names, imports
- Geen LLM — puur pattern-matching
- Output: BusinessDomain objecten met use cases, entities, priority
- **LLM:** Nee | **DB:** Via BrownPaperAnalysisDB

#### Stap 4: Constitution Generation (Line 1744)
- `generate_constitution(session_id, human_input)`
- Genereert project charter: mission/vision, principes, vereisten, constraints, risico's, scope, success criteria
- Template-based transformatie van analyse resultaten
- **LLM:** Nee | **DB:** Ja (BrownPaperConstitutionDB)

#### Stap 5: Epic Generation (Line 2124)
- `generate_epics(session_id)`
- Per domain -> 1 Epic
- CRUD use cases -> 1 Feature, overige -> aparte Features
- Story points: 3 (CRUD), 5 (overig)
- IDs: EPIC-001, FEAT-001-001
- **LLM:** Nee | **DB:** Ja (BrownPaperEpicDB)

#### Stap 6: Approval (Line 2205)
- `approve_session()` / `reject_session()`
- Status: REVIEW -> APPROVED of REJECTED
- **LLM:** Nee | **DB:** Ja

### Enhanced Analysis Pipeline (Line 2245-3411)

Dit is de 6-fase pipeline die BOVENOP de basis stappen draait:

| Fase | Methode | Line | Wat | LLM |
|------|---------|------|-----|-----|
| 1 | `_phase1_code_understanding` | 2493 | 11 services, SIG metrics | Nee |
| 2a | `_enhanced_domain_extraction` | 2875 | BusinessDomainExtractor (Week 159) | Nee |
| 2b | `_phase2_domain_extraction` | 2778 | Generiek, fallback | Nee |
| 3a | `_generate_business_driven_stories` | 2950 | BusinessDrivenStoryGenerator (Week 159) | Mogelijk |
| 3b | `_phase3_hierarchical_extraction` | 3116 | HierarchicalStoryExtractionService | Onbekend |
| 4 | `_phase4_deep_extraction` | 3172 | LLM Council multi-perspectief | Indirect |
| 5 | `_phase5_estimation` | 3227 | IFPUG FP, complexity multiplier | Nee |
| 6 | `_phase6_output` | 3302 | Consolidatie, summary | Nee |

**Tier-gating:** FREE/BASIC = Fase 1-3, STANDARD = 1-4, PROFESSIONAL = 1-5, PREMIUM = alle 6.

### Oordeel voor Onboarding

| Onderdeel | Oordeel | Reden |
|-----------|---------|-------|
| Session aanmaken | **BEHOUDEN** | Basis, vereenvoudigen |
| 11-service code analyse | **BEHOUDEN** | Kern van onboarding — begrijp de codebase |
| Domain extraction (pattern) | **VERVANGEN** door BusinessDomainExtractor (Week 159) |
| Constitution generation | **HERONTWERPEN** — te template-matig, geen LLM input |
| Epic generation (CRUD-based) | **VERVANGEN** door BusinessDrivenStoryGenerator (Week 159) |
| Phase 4 Deep Extraction | **BEHOUDEN** — uniek, LLM Council perspectief, nergens anders |
| Phase 5 Estimation | **BEHOUDEN** — IFPUG methodiek, complexity multiplier |
| Phase 6 Output | **BEHOUDEN** — aggregatie, kan slimmer |
| Approval workflow | **BEHOUDEN** — vereenvoudigen |

### Rode vlaggen

1. **Code-only approach:** Geen menselijke context. Alles wat de code-analyse niet kan vinden (business regels in hoofd van developers, impliciete constraints) mist.
2. **Geen LLM in basis flow:** Constitution en Epics zijn puur template-based. Kwaliteit is voorspelbaar maar beperkt.
3. **Deep Extraction alleen hier:** Phase 4 met LLM Council zit NIET in Workflow B (MarQed). Dit is een gat.

---

## 3. Workflow B: MarQedBrownPaperWorkflow (Nieuw, Top-Down)

**File:** `backend/app/services/brown_paper_service.py:3516-5410`

### Logische Stappen

#### Stap 1: Session Start (Line 4031)
- `start_session(project_name, project_path, fetch_vector_context)`
- Haalt optioneel Vector DB context op via ChromaService (Week 143)
- Maakt MarQedBrownPaperSession aan
- Slaat op in MarQedSessionDB
- **LLM:** Nee (ChromaDB = vector search, geen generatie) | **DB:** Ja

#### Stap 2: 8 Questions Beantwoorden (Line 4377)

| Q# | Onderwerp | Agent | Required | Min Length |
|----|-----------|-------|----------|------------|
| 1 | Legacy System Description | Miguel | Ja | 50 |
| 2 | Target State Vision | Miguel | Ja | 50 |
| 3 | Migration Strategy | Miguel | Ja | 50 |
| 4 | Data Migration Complexity | Miguel | Ja | 50 |
| 5 | Problem Statement | Peter | Optioneel | - |
| 6 | Stakeholders | Peter | Optioneel | - |
| 7 | Success Criteria | Peter | Optioneel | - |
| 8 | Timeline | Felix | Optioneel | - |

- Per antwoord: validatie lengte, opslaan in session.answers, audit trail (versioning), event log
- `get_current_question_with_context()` voegt Vector DB context toe (relevante docs)
- **LLM:** Nee | **DB:** Ja (MarQedAnswerDB, versioning)

#### Stap 3: Migration Analysis — Miguel (Line 4457)
- `run_migration_analysis(session_id)`
- Heuristiek-based complexity scoring op Q1-Q4 tekst:
  - 150K+ LOC -> +3 punten
  - Microservices target -> +2
  - Big Bang strategie -> +3
  - ETL data migratie -> +2
- Genereert: complexity level, risk register, 4 standaard fasen, technical spikes, go/no-go checkpoints
- **PROBLEEM:** Geen LLM. Keyword-matching. "150K+ LOC" moet letterlijk in het antwoord staan.
- **LLM:** Nee | **DB:** Ja

#### Stap 4: Specification — Peter (Line 4675)
- `generate_specification(session_id)`
- Template-based aggregatie van Q1-Q8 + migration analysis
- Secties: executive summary, current state, target state, migration approach, stakeholders, success criteria, timeline
- **PROBLEEM:** Puur string-concatenatie. Geen synthese, geen LLM.
- **LLM:** Nee | **DB:** Ja

#### Stap 5: Task Generation — Felix (Line 4833)
- `generate_tasks(session_id)`
- Twee paden:
  - **Path A (Week 159):** BusinessDomainExtractor + BusinessDrivenStoryGenerator (code-analyse vereist)
  - **Path B (fallback):** Standaard 4-fase template epics
- FP analyse via BrownPaperEstimationService
- `_quick_code_scan()` voor module discovery
- `_sync_to_brown_paper_tables()` — bridge naar dashboard
- `_generate_deliverables()` — markdown docs
- **LLM:** Mogelijk (in BusinessDomainExtractor/StoryGenerator) | **DB:** Ja

#### Stap 6: Approval (Line 5472)
- `approve_session()` / `reject_session()`
- Status: review -> approved/rejected
- Event logging met reviewer naam
- **LLM:** Nee | **DB:** Ja

### Helpers

| Helper | Line | Wat |
|--------|------|-----|
| `_fetch_vector_context` | 3556 | ChromaDB query, top-10 docs, architecture summary |
| `_quick_code_scan` | 5208 | DependencyGraphService of file-scan fallback |
| `_sync_to_brown_paper_tables` | 5280 | Bridge: MarQed -> BrownPaper dashboard tables |
| `_generate_deliverables` | 4993 | Markdown docs in project/docs/marqed-deliverables/ |
| `_persist_session_to_db` | intern | MarQedSessionDB upsert |
| `_save_answer_version` | intern | MarQedAnswerDB insert met versioning |
| `_log_event` | intern | MarQedSessionEventDB insert |

### Deprecated Methods (verwijderen in v26.0)

8 sync-only methoden (`*_sync()`) die geen DB persistence doen — alleen cache. Allemaal `@deprecated_sync_wrapper`.

### Oordeel voor Onboarding

| Onderdeel | Oordeel | Reden |
|-----------|---------|-------|
| Session + Vector Context | **BEHOUDEN** | Goede pre-populatie, ChromaDB integratie |
| 8-Question flow | **HERONTWERPEN** | Q1-Q4 zijn migration-specifiek, onboarding heeft andere vragen nodig |
| Migration Analysis (heuristic) | **NIET OVERNEMEN** | Te simpel, keyword-matching, migration-specifiek |
| Specification (template) | **HERONTWERPEN** | Goed concept, maar moet LLM-assisted worden |
| Business-Driven Task Gen | **BEHOUDEN** | Week 159, beproefde kwaliteit (440 epics E2E) |
| DB sync bridge | **BEHOUDEN** | Dashboard compatibiliteit |
| Answer versioning + audit | **BEHOUDEN** | Compliance, traceability |
| Deliverable generation | **BEHOUDEN** | Markdown docs nuttig |

### Rode vlaggen

1. **Geen Deep Extraction:** Phase 4 (LLM Council) uit Workflow A ontbreekt volledig.
2. **Migration Analysis is nep-AI:** Keyword matching is fragiel. "150.000 regels code" triggert NIET "150K+ LOC".
3. **Specification heeft geen synthese:** Concateneert antwoorden, combineert ze niet intelligent.
4. **Q1-Q4 zijn migration-only:** Onboarding van een NIEUW project (greenfield) past niet in dit schema.
5. **8 deprecated sync methods:** Technische schuld, verwijderen.

---

## 4. Workflow C: BrownPaperOrchestrator (Confucius 7-Stage)

**File:** `backend/app/confucius/workflows/brown_paper.py`

### Logische Stappen

| Stage | Agent(s) | Quality Gate | Max Iter | Depends On | Parallel |
|-------|----------|-------------|----------|------------|----------|
| 1. code_understanding | Miguel | 0.80 | 2 | - | Nee |
| 2. domain_extraction | Peter, Betty | 0.85 | 3 | 1 | Ja |
| 3. user_journey_extraction | Vicky, Peter | 0.70 | 2 | 2 | Nee |
| 4. story_extraction | Peter | 0.80 | 3 | 3 | Nee |
| 5. deep_extraction | Felix, Quinn, Marcus | 0.85 | 2 | 4 | Ja (optioneel) |
| 6. estimation | Eliza | 0.75 | 2 | 4 | Nee |
| 7. output_consolidation | Diana | 0.80 | 2 | 6 | Nee |

### Stage Details

**1. Code Understanding (Miguel, 600s timeout)**
- Runt: Metrics analyse met dependency graph
- Output: files_scanned, LOC, complexity_score, dependency_graph, layer_analysis, tech_stack

**2. Domain Extraction (Peter + Betty, parallel)**
- Peter: domein boundaries extraheren
- Betty: business capabilities identificeren
- Quality gate 0.85 — hoge lat voor domein-nauwkeurigheid

**3. User Journey Extraction (Vicky + Peter)**
- UserJourneyExtractionStage
- Output: personas, workflows, screen flows
- Quality gate 0.70 — lager want UX is subjectief

**4. Story Extraction (Peter)**
- User stories en epics uit domeinen
- Quality gate 0.80

**5. Deep Extraction (Felix + Quinn + Marcus, parallel, OPTIONEEL)**
- Felix: architecture patterns
- Quinn: quality issues
- Marcus: maintainability assessment
- Quality gate 0.85
- `required=False` — enhancement, geen blocker

**6. Estimation (Eliza)**
- Function Point methodiek
- Quality gate 0.75

**7. Output Consolidation (Diana)**
- Consolideert alle resultaten tot rapport
- Quality gate 0.80

### Infrastructuur (via WorkflowOrchestrator base)

- **Quality Gates:** Elke stage geevalueerd met domain-specifieke regels
- **Retry:** Tot max_iterations met feedback van quality evaluator
- **Checkpoints:** Na elke succesvolle stage, resume mogelijk
- **Escalatie:** Na uitputting van iterations
- **Idempotent:** Overslaan van reeds voltooide stages

### Oordeel voor Onboarding

| Onderdeel | Oordeel | Reden |
|-----------|---------|-------|
| 7-stage pipeline structuur | **BEHOUDEN** | Goede architectuur, quality gates |
| Quality gate thresholds | **BEHOUDEN** | Bewezen effectief |
| Agent assignments | **HERZIEN** | Sommige stages hebben betere agent-matching nodig |
| Deep extraction (optioneel) | **VERPLICHT MAKEN** voor onboarding | Te waardevol om optioneel te zijn |
| User journey extraction | **BEHOUDEN** | Uniek, zit niet in A of B |
| Checkpoint/resume | **BEHOUDEN** | Essentieel voor lange analyses |
| Parallel execution | **BEHOUDEN** | Performance |

### Rode vlaggen

1. **Geen vragenlijst:** Puur code-driven, geen menselijke input vooraf.
2. **Geen Vector DB context:** Gebruikt geen ChromaDB voor pre-populatie.
3. **Deep extraction optioneel:** Moet verplicht zijn voor grondige onboarding.

---

## 5. Workflow D: MigrationOrchestrator (Confucius 8-Stage)

**File:** `backend/app/confucius/workflows/migration.py`

### Logische Stappen

| Stage | Agent(s) | Quality Gate | Max Iter | Depends On | Parallel |
|-------|----------|-------------|----------|------------|----------|
| 1. validate_answers | - | 1.0 | 1 | - | Nee |
| 2. technical_analysis | Miguel | 0.85 | 3 | 1 | Nee |
| 3. security_analysis | Quinn | 0.80 | 2 | 2 | Nee |
| 4. user_journey_extraction | Vicky, Peter | 0.70 | 2 | 3 | Nee |
| 5. generate_specification | Peter, Betty | 0.85 | 3 | 4 | Ja |
| 6. generate_tasks | Felix, Paul | 0.80 | 3 | 5 | Ja |
| 7. estimate_effort | Eliza | 0.75 | 2 | 6 | Nee |
| 8. quality_review | Quinn | 0.90 | 2 | 7 | Nee |

### Unieke Elementen

- **Security Analysis (Fase 37):** Quinn + SecurityScanOrchestrator, legacy-specifieke findings, migration blockers
- **Quality Review (0.90):** Hoogste quality gate in het systeem
- **Paul agent:** Migration wave planning (uniek voor migration)
- **8 questions:** Gekoppeld aan specifieke agents (Q1-Q4 = Miguel, Q5-Q7 = Peter, Q8 = Felix)

### Oordeel voor Onboarding

| Onderdeel | Oordeel | Reden |
|-----------|---------|-------|
| Answer validation stage | **BEHOUDEN** | Goed concept, andere vragen voor onboarding |
| Security analysis | **BEHOUDEN** | Relevant voor onboarding van bestaande projecten |
| Quality review (0.90) | **BEHOUDEN** | Eindcontrole |
| Migration wave planning | **NIET OVERNEMEN** | Migration-specifiek |
| Question-driven approach | **COMBINEREN** met code-analyse (hybride) |

### Rode vlaggen

1. **Puur migration-gericht:** 8 vragen gaan over legacy -> target. Niet geschikt voor onboarding van greenfield.
2. **Geen code-analyse stage:** Vertrouwt volledig op menselijke antwoorden, geen codebase scanning.

---

## 6. Workflow E: OnboardingWorkflowIntegration

**File:** `backend/app/services/extraction_integration_service.py:489`

### Logische Stappen

```python
class OnboardingWorkflowIntegration:
    async def on_project_registered(
        project_id, repository_path, tier="FREE",
        auto_extract=True, auto_import=True
    ) -> Optional[OnboardingExtractionResult]:
```

1. Wordt getriggerd bij project registratie
2. Start automatisch BrownPaperOrchestrator (Workflow C) als `auto_extract=True`
3. Importeert resultaten als `auto_import=True`
4. Tier bepaalt welke fasen draaien (FREE = beperkt, PREMIUM = alles)

### Oordeel voor Onboarding

| Onderdeel | Oordeel | Reden |
|-----------|---------|-------|
| Auto-trigger bij registratie | **BEHOUDEN** | Juiste entry point |
| Tier-based gating | **HERONTWERPEN** | Onboarding moet altijd volledig zijn |
| Koppeling met BrownPaperOrchestrator | **UPDATEN** | Moet naar nieuwe unified onboarding verwijzen |

---

## 7. Workflow F: UnifiedOnboardingService (Bestaande Orchestrator)

**File:** `backend/app/services/unified_onboarding_service.py` (~815 LOC)
**API:** `backend/app/api/unified_onboarding.py` (`/api/brown-paper/unified/`)
**DB Model:** `UnifiedOnboardingSession` met `step_1_result` t/m `step_8_result` (JSONB)

> **BELANGRIJK:** Deze workflow was niet opgenomen in de oorspronkelijke analyse maar is de meest
> complete bestaande poging om alle workflows te combineren. Dit verandert het uitgangspunt.

### Logische Stappen

| Step | Naam | Bron | Timeout | Wat |
|------|------|------|---------|-----|
| 1 | Code Scan | A (`analyze_application`) | 300s | Bottom-up code analyse met auto-registratie |
| 2 | 8 Vragen Validatie | B (session check) | 30s | Controleert of MarQed sessie 8 antwoorden heeft |
| 3 | Miguel's Analyse | B (`run_migration_analysis`) | 300s | Heuristiek complexity scoring + enrichment uit step 1 |
| 4 | Peter's Specificatie | B (`generate_specification`) | 300s | Template-based spec generatie |
| 5 | Felix Bottom-Up | W159 services direct | 600s | BusinessDomainExtractor + StoryGenerator op code |
| 6 | Felix Top-Down | B (`generate_tasks`) | 600s | MarQed task generation (8 antwoorden als basis) |
| 7 | Enhanced 6-Fase | A (`run_enhanced_analysis`) | 900s | Complete Phase 1-6 pipeline met per-fase progress |
| 8 | Reconciliation | `ReconciliationService` | 120s | Vergelijkt 3 epic-sets, detecteert blind spots + phantom features |

### Unieke Elementen

- **Reconciliation (Step 8):** Vergelijkt bottom-up (step 5) vs top-down (step 6) vs enhanced (step 7). Detecteert:
  - `blind_spots`: Domeinen die code-analyse vindt maar vragen missen
  - `phantom_features`: Features in antwoorden die niet in code voorkomen
  - `confidence_heatmap`: Per-domein betrouwbaarheid
  - `fp_deltas`: Verschil in FP schattingen tussen methoden
  - `domain_disputes`: Conflicterende domein-indelingen
- **Per-step execute:** Steps zijn onafhankelijk uitvoerbaar (`execute_step(id, 3)`)
- **Per-fase progress voor Step 7:** Progress callback schrijft naar DB na elke enhanced fase
- **Isolated DB session voor Step 7:** Voorkomt dat timezone bugs de hoofdsessie corrumperen
- **Auto-registratie:** Step 1 registreert automatisch een applicatie als die niet bestaat
- **Constitution + Epic persistence:** Step 8 maakt BrownPaperConstitution + BrownPaperEpics aan

### Wat ontbreekt

| Ontbreekt | Impact |
|-----------|--------|
| **Quality gates** | Geen Confucius-style quality evaluation per step |
| **Checkpoint/resume** | Als step 5 faalt, moet je alles opnieuw draaien |
| **Agent orchestratie** | Geen agents, directe service calls |
| **Security scan** | Niet aanwezig (zit alleen in D) |
| **User Journey extraction** | Niet aanwezig (zit alleen in C) |
| **Deep Extraction als losse stap** | Zit verborgen in step 7 (enhanced) maar niet als expliciete gate |
| **LLM-assisted constitution** | Constitution is nog steeds template-based |
| **Onboarding-specifieke vragen** | Vereist nog steeds de 8 migration-vragen via MarQed |

### Oordeel voor Onboarding

| Onderdeel | Oordeel | Reden |
|-----------|---------|-------|
| 8-step pipeline structuur | **BEHOUDEN als basis** | Beste bestaande compositie |
| Reconciliation | **BEHOUDEN** | Uniek en waardevol — detecteert gaten |
| Per-step execution | **BEHOUDEN** | Flexibel, debugbaar |
| Per-fase progress (step 7) | **BEHOUDEN** | Goede UX voor lange analyses |
| Auto-registratie | **BEHOUDEN** | Vermindert handmatig werk |
| Step 3 (migration analysis) | **HERONTWERPEN** | Keyword heuristic, migration-specifiek |
| Step 4 (specification) | **HERONTWERPEN** | Template-based, moet LLM-assisted |
| Quality gates | **TOEVOEGEN** | Ontbreekt, essentieel |
| Checkpoint/resume | **TOEVOEGEN** | Ontbreekt, essentieel voor lange runs |
| Security scan | **TOEVOEGEN** | Ontbreekt, overnemen uit D |
| User Journey | **TOEVOEGEN** | Ontbreekt, overnemen uit C |

### Rode vlaggen

1. **Geen quality gates:** De grootste zwakte. Elke step draait zonder evaluatie — output kwaliteit is onbekend.
2. **Geen resume:** Als step 7 (15 min timeout) faalt na step 1-6 (45+ min), moet alles opnieuw.
3. **Afhankelijk van MarQed 8-vragen:** Vereist een complete MarQed sessie als prerequisite.
4. **3x epic-generatie is redundant:** Steps 5, 6, en 7 genereren alle drie epics. Reconciliation lost dit op maar het is inefficient.

---

## 8. Vergelijkingstabel (A-F)

### Capabilities per Workflow

| Capability | A (Old BP) | B (MarQed) | C (BP Orch) | D (Mig Orch) | **F (Unified)** | Nodig voor Onboarding |
|-----------|:----------:|:----------:|:-----------:|:------------:|:---------------:|:---------------------:|
| Code analyse (11 services) | Ja | Via A | Via A | Nee | **Ja (step 1+7)** | **JA** |
| SIG Quality Metrics | Ja | Via A | Via A | Nee | **Ja (step 7)** | **JA** |
| Vector DB context | Nee | Ja | Nee | Nee | Via B | **JA** |
| Vragenlijst | Nee | 8Q | Nee | 8Q (validated) | **8Q (via B)** | **JA** (andere vragen) |
| Domain extraction (pattern) | Ja | Via A | Via A | Nee | Via step 7 | Vervangen door Week 159 |
| Business Domain Extraction | Ja (W159) | Ja (W159) | Nee | Nee | **Ja (step 5)** | **JA** |
| User Journey Extraction | Nee | Nee | Ja | Ja | **Nee** | **JA** |
| Deep Extraction (LLM Council) | Ja (Phase 4) | Nee | Ja (optioneel) | Nee | **In step 7** | **JA** |
| FP Estimation (IFPUG) | Ja (Phase 5) | Ja | Ja | Ja | **Ja (step 7)** | **JA** |
| Constitution / Charter | Ja | Via spec | Nee | Nee | **Ja (step 8)** | **JA** (herontwerp) |
| Security Analysis | Nee | Nee | Nee | Ja (Quinn) | **Nee** | **JA** |
| Quality Gates | Nee | Nee | Ja (7 gates) | Ja (8 gates) | **Nee** | **JA** |
| Checkpoint/Resume | Nee | Nee | Ja | Ja | **Nee** | **JA** |
| Agent orchestratie | Nee | Nee | Ja (9 agents) | Ja (8 agents) | **Nee** | **JA** |
| Answer versioning | Nee | Ja | Nee | Nee | Via B | **JA** |
| Dashboard sync | Nee | Ja (W159) | Nee | Nee | **Ja (step 8)** | **JA** |
| Deliverable docs | Nee | Ja | Ja (Diana) | Nee | Nee | **JA** |
| Approval workflow | Ja | Ja | Nee | Ja (0.90 gate) | Nee | **JA** |
| **Reconciliation** | Nee | Nee | Nee | Nee | **Ja (step 8)** | **JA** |
| **Per-step execution** | Nee | Nee | Nee | Nee | **Ja** | **JA** |
| **Per-fase progress** | Nee | Nee | Nee | Nee | **Ja (step 7)** | **JA** |

### Data Persistence per Workflow

| Tabel | A | B | C | D |
|-------|:-:|:-:|:-:|:-:|
| brown_paper_sessions | Ja | Via sync | Via A | Nee |
| brown_paper_analyses | Ja | Nee | Via A | Nee |
| brown_paper_constitutions | Ja | Via sync | Nee | Nee |
| brown_paper_epics | Ja | Via sync | Nee | Nee |
| marqed_sessions | Nee | Ja | Nee | Nee |
| marqed_answers | Nee | Ja (versioned) | Nee | Nee |
| marqed_session_events | Nee | Ja | Nee | Nee |

---

### Onboarding Scope: Wat moet erin?

### Definitie "Onboarding"

Onboarding = een BESTAAND project voor het eerst in het systeem laden, analyseren, en werkbaar maken.
Dit is NIET greenfield (dat is GreenPaper). Dit is NIET migration planning (dat is MigrationOrchestrator).

### Gewenste Output van Onboarding

Na onboarding moet het systeem weten:
1. **Wat is het project?** (naam, pad, tech stack, omvang)
2. **Hoe zit de code in elkaar?** (modules, dependencies, layers, complexity, SIG metrics)
3. **Welke business domeinen bevat het?** (epics, features, stories)
4. **Hoe gebruiken mensen het?** (user journeys, personas, screen flows)
5. **Waar zitten de risico's?** (dead code, security issues, quality findings)
6. **Hoeveel werk is het?** (FP estimate, story points)
7. **Wat is het project charter?** (constitution met principes, scope, constraints)

### Mapping: Bron per Output

| Output | Beste bron | Workflow |
|--------|-----------|----------|
| Project metadata | Vragenlijst Q1-Q2 + code scan | B + A |
| Code structuur (11 services) | Phase 1 code understanding | A |
| SIG Quality Metrics | Phase 1 SIG analyzers | A |
| Business domeinen | BusinessDomainExtractor (W159) | A (enhanced) / B |
| User stories | BusinessDrivenStoryGenerator (W159) | A (enhanced) / B |
| User journeys | UserJourneyExtractionStage | C |
| Deep analysis (LLM Council) | Phase 4 deep extraction | A |
| Security scan | SecurityScanOrchestrator | D |
| FP estimation | BrownPaperEstimationService + Phase 5 | A / B |
| Constitution | generate_constitution + LLM verbetering | A (herontwerp) |
| Quality gates | WorkflowOrchestrator base | C / D |
| Vector DB context | ChromaService fetch | B |
| Dashboard sync | _sync_to_brown_paper_tables | B |

---

## 9. Architectuur: Nieuwe Onboarding Workflow

### Ontwerpprincipes

1. **Separation of concerns:** Elke module doet precies 1 ding
2. **Composable:** Modules zijn onafhankelijk, klein, en herbruikbaar
3. **Toggleable:** Elk blok kan aan/uit gezet worden via configuratie
4. **Quality gates overal:** Na elke module een kwaliteitscheck
5. **Checkpoint/resume:** Na elke succesvolle module, hervat bij falen
6. **Geen duplicatie:** 1 methode per capability, niet 3x epics genereren en dan reconcilen

### Waarom F NIET de basis is

Workflow F (UnifiedOnboardingService) is een "doe alles wat we hebben" aanpak:
- Genereert epics 3x (bottom-up, top-down, enhanced) en reconcilt dan — dat is een workaround voor het niet weten welke methode het beste is
- Geen quality gates — output kwaliteit is onbekend
- Geen resume — 45+ minuten werk verloren bij een fout
- Afhankelijk van MarQed 8-vragen sessie als prerequisite
- Kriskras door alle bestaande services zonder helder eigen ontwerp

**Wat we WEL van F leren:** per-step execution is nuttig, per-fase progress is goede UX, auto-registratie is handig.

### Waarom NIEUW bouwen

De nieuwe onboarding is een **Confucius workflow** (zoals C en D) met:
- `WorkflowOrchestrator` base class → quality gates, checkpoints, resume, agent routing
- Eigen stage definitie → niet copy/paste van bestaande workflows
- Modulaire services → elke stage roept een kleine, gerichte service aan

### Module-architectuur

```
┌─────────────────────────────────────────────────────────────────┐
│                    OnboardingOrchestrator                         │
│              (extends WorkflowOrchestrator)                       │
│                                                                   │
│  Confucius base: quality gates, checkpoints, resume, agents      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Module 1: Input Validation                                      │
│    → onboarding_intake_service.py                                │
│    → 5 vragen + project_path validatie                           │
│    → Vector DB context ophalen                                   │
│                                                                   │
│  Module 2: Code Understanding                                    │
│    → code_scan_service.py                                        │
│    → 11 analyse services + SIG metrics                           │
│    → Auto-registratie als applicatie niet bestaat                 │
│                                                                   │
│  Module 3: Security Scan                                         │
│    → security_scan_service.py (wrapper rond SecurityScanOrch)    │
│    → CWE scanners, OWASP, vulnerability detection                │
│                                                                   │
│  Module 4: Domain Extraction                                     │
│    → domain_extraction_service.py                                │
│    → BusinessDomainExtractor (W159)                              │
│    → 1x extraction, geen duplicatie                              │
│                                                                   │
│  Module 5: User Journey Extraction                               │
│    → user_journey_service.py (wrapper rond UserJourneyStage)     │
│    → Personas, workflows, screen flows                           │
│                                                                   │
│  Module 6: Story Generation                                      │
│    → story_generation_service.py                                 │
│    → BusinessDrivenStoryGenerator (W159)                         │
│    → Input: domeinen uit Module 4                                │
│                                                                   │
│  Module 7: Deep Extraction (VERPLICHT)                           │
│    → deep_extraction_service.py                                  │
│    → LLM Council multi-perspectief analyse                       │
│    → Felix (architecture) + Quinn (quality) + Marcus (maint.)    │
│                                                                   │
│  Module 8: Estimation                                            │
│    → estimation_service.py                                       │
│    → IFPUG FP + complexity multiplier                            │
│                                                                   │
│  Module 9: Constitution Generation (SUB-FASE — later uitwerken)  │
│    → constitution_service.py                                     │
│    → LLM Council assisted (niet template-based)                  │
│    → Input: alle resultaten van Module 2-8                       │
│                                                                   │
│  Module 10: Output & Deliverables                                │
│    → deliverable_service.py                                      │
│    → Dashboard sync, markdown docs, rapport generatie            │
│                                                                   │
│  Module 11: Quality Review                                       │
│    → Confucius quality gate (Quinn, 0.90 threshold)              │
│    → Eindcontrole op alle output                                 │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│  Quality gate na ELKE module (niet alleen aan het eind)          │
│  Checkpoint na elke succesvolle module                            │
│  Per-module progress tracking naar DB                             │
└─────────────────────────────────────────────────────────────────┘
```

### Quality Gates per Module

| Module | Agent(s) | Quality Gate | Max Iter | Depends On |
|--------|----------|-------------|----------|------------|
| 1. Input Validation | - | 1.0 | 1 | - |
| 2. Code Understanding | Miguel | 0.80 | 2 | 1 |
| 3. Security Scan | Quinn | 0.80 | 2 | 2 |
| 4. Domain Extraction | Peter, Betty | 0.85 | 3 | 2 |
| 5. User Journey | Vicky, Peter | 0.70 | 2 | 4 |
| 6. Story Generation | Peter | 0.80 | 3 | 4, 5 |
| 7. Deep Extraction | Felix, Quinn, Marcus | 0.85 | 2 | 6 |
| 8. Estimation | Eliza | 0.75 | 2 | 6 |
| 9. Constitution | LLM Council | 0.80 | 2 | 2-8 (alle) |
| 10. Output & Deliverables | Diana | 0.80 | 2 | 9 |
| 11. Quality Review | Quinn | 0.90 | 2 | 10 |

### Dependency graph

```
[1] Input Validation
 │
 ├──→ [2] Code Understanding
 │     │
 │     ├──→ [3] Security Scan
 │     │
 │     ├──→ [4] Domain Extraction
 │     │     │
 │     │     ├──→ [5] User Journey
 │     │     │
 │     │     └──→ [6] Story Generation (depends on 4 + 5)
 │     │           │
 │     │           ├──→ [7] Deep Extraction
 │     │           │
 │     │           └──→ [8] Estimation
 │     │
 │     └──→ [9] Constitution (depends on 2-8, all results)
 │           │
 │           └──→ [10] Output & Deliverables
 │                 │
 │                 └──→ [11] Quality Review
```

**Parallellisatie mogelijk:** Module 3 en 4 kunnen parallel draaien (beide afhankelijk van 2).
Module 7 en 8 kunnen parallel draaien (beide afhankelijk van 6).

### Onboarding-specifieke vragen (5)

| Q# | Vraag | Required | Auto-detect mogelijk |
|----|-------|----------|---------------------|
| 1 | Wat is dit project? (naam, organisatie, doel) | Ja | Deels (README) |
| 2 | Welke technologie? (talen, frameworks, DB) | Ja | Ja (code scan) |
| 3 | Wat zijn de bekende pijnpunten? | Nee | Nee |
| 4 | Wat zijn de constraints? (compliance, team, budget) | Nee | Nee |
| 5 | Wat wil je uit deze analyse halen? | Nee | Nee |

Q2 kan deels of volledig auto-detected worden uit Module 2 (Code Understanding).
Als auto-detect voldoende is, hoeft de gebruiker maar 1 verplichte vraag te beantwoorden.

---

## 10. Aanbevelingen & Verbeterpunten

### A. Architectuur

1. **Nieuwe OnboardingOrchestrator** bouwen als Confucius workflow met WorkflowOrchestrator base.
   - 11 modules, elk een eigen kleine service
   - Quality gates, checkpoints, resume uit de base class
   - Geen afhankelijkheid op MarQed sessies of BrownPaper sessies

2. **Modulaire services extraheren** uit `brown_paper_service.py` (~5400 LOC). Elk blok:
   - Een enkel, duidelijk gedefinieerd doel
   - Onafhankelijk aan/uit-zetbaar via configuratie
   - Klein genoeg om te testen en te begrijpen
   - Herbruikbaar door Onboarding, Migration, en GreenPaper
   - **LATER uitvoeren** — dit is een kwaliteitsverbetering, plannen als aparte fase

3. **Bestaande workflows laten staan:**
   - A (BrownPaperService): Legacy, wordt bron voor extractie van modulaire services
   - B (MarQedBrownPaperWorkflow): Blijft voor migration use case
   - C (BrownPaperOrchestrator): Referentie-architectuur voor quality gates
   - D (MigrationOrchestrator): Referentie + bron voor security scan module
   - E (OnboardingWorkflowIntegration): Entry point updaten naar nieuwe orchestrator
   - F (UnifiedOnboardingService): Deprecaten zodra nieuwe onboarding werkt

### B. Inhoudelijk

4. **5 onboarding-vragen** (zie tabel hierboven) — lage drempel, code-analyse doet het zware werk.

5. **Deep Extraction verplicht** — niet optioneel zoals in C. LLM Council perspectief is essentieel.

6. **Security scan standaard** — vanuit D, zonder legacy-specifieke filter.

7. **Constitution via LLM Council** — sub-fase, later dieper uitwerken wanneer we zover zijn.

8. **Migration Analysis NIET overnemen** — dat is een apart workflow. Onboarding produceert de data die migration later nodig heeft.

### C. Technisch

9. **Deprecated sync methods verwijderen** in v26.0 cleanup.

10. **Vector DB context standaard AAN** bij elke analyse.

11. **Answer versioning behouden** — compliance waarde.

12. **Dashboard sync behouden** — backward compatibility met bestaande UI.

### D. Wat NIET overnemen

| Item | Reden |
|------|-------|
| F's 3x epic-generatie + reconciliation | Doe het 1x goed ipv 3x en samenvoegen |
| 8-question migration flow | Migration-specifiek |
| Migration Analysis (keyword heuristic) | Te simpel, migration-only |
| Phase-based fallback tasks | Genereert generieke templates |
| Deprecated sync methods | Technische schuld |
| Tier-based gating op onboarding | Onboarding moet altijd volledig zijn |
| Paul agent (wave planning) | Migration-specifiek |

---

## 11. Sub-fasen

Fase 24.9 wordt opgesplitst in kleinere, onafhankelijk leverbare sub-fasen:

| Sub-fase | Wat | Dependencies | Omvang |
|----------|-----|-------------|--------|
| **24.9a** | OnboardingOrchestrator scaffold + Module 1 (Input) + Module 2 (Code Understanding) | Geen | Klein — base class + 2 modules |
| **24.9b** | Module 3 (Security) + Module 4 (Domain Extraction) | 24.9a | Klein — 2 modules, services bestaan al |
| **24.9c** | Module 5 (User Journey) + Module 6 (Story Generation) | 24.9b | Klein — 2 modules, services bestaan al |
| **24.9d** | Module 7 (Deep Extraction) + Module 8 (Estimation) | 24.9c | Medium — deep extraction integratie |
| **24.9e** | Module 9 (Constitution via LLM Council) | 24.9d | Medium — nieuw ontwerp, LLM integratie |
| **24.9f** | Module 10 (Output) + Module 11 (Quality Review) | 24.9e | Klein — consolidatie + eindgate |
| **24.9g** | API endpoints + E2E test + Dashboard sync | 24.9f | Klein — integratie |

Elke sub-fase is onafhankelijk testbaar en levert werkende functionaliteit op.

---

## 12. Conclusie

De nieuwe onboarding wordt **niet** gebouwd op Workflow F. F is een nuttige verkenning geweest
maar het ontwerp (3x dupliceren + reconcilen) is geen fundament voor productiekwaliteit.

In plaats daarvan bouwen we een **nieuwe OnboardingOrchestrator** als Confucius workflow met:
- 11 modulaire services, elk met een enkel doel
- Quality gates na elke module
- Checkpoint/resume
- 5 laagdrempelige onboarding-vragen
- Geen duplicatie — 1 methode per capability

De bestaande services (code scan, domain extraction, story generation, estimation, security scan)
worden hergebruikt als modulaire blokken. Geen nieuwe logica nodig, wel nieuwe compositie.

De LLM Council constitution (Module 9) wordt als aparte sub-fase dieper uitgewerkt.

---

*Analyse uitgevoerd op basis van code-inspectie van brown_paper_service.py (~5400 LOC), unified_onboarding_service.py (~815 LOC), confucius/workflows/ (~1000 LOC), extraction_integration_service.py, unified_onboarding.py, schemas/workflow.py, en models/*
*Geupdate na gebruikersfeedback: nieuw bouwen met separation of concerns, niet F uitbreiden*
