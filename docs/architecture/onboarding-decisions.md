# OnboardingWorkflow — Beslissingslog

> **Doel:** Systematisch documenteren welke capabilities we overnemen, niet overnemen, of herontwerpen.
> **Methode:** Beginnen bij meest uitgebreide workflow (F), daarna A-E voor aanvullingen.
> **Datum gestart:** 2026-02-03

---

## Legenda

| Symbool | Betekenis |
|---------|-----------|
| ✅ | **OPNEMEN** — Nemen we over |
| ❌ | **NIET OPNEMEN** — Bewust weglaten |
| 🔄 | **HERONTWERPEN** — Concept overnemen, implementatie anders |
| ⚠️ | **VALSTRIK** — Zelfde naam, andere implementatie |

---

## Workflow F: UnifiedOnboardingService

**Bestand:** `backend/app/services/unified_onboarding_service.py`
**LOC:** 815
**Beschrijving:** 8-step orchestrator die A+B+enhanced combineert met reconciliation

---

### F.1 Session Management

| Item | Beslissing | Reden |
|------|------------|-------|
| `UnifiedOnboardingSession` DB model | 🔄 | Eigen `OnboardingSession` model maken, niet afhankelijk van MarQed |
| `start()` met `marqed_session_id` vereist | ❌ | Nieuwe workflow heeft eigen intake, geen MarQed prerequisite |
| `get_session()` | ✅ | Standaard CRUD, hergebruiken |
| `get_status()` met step details | ✅ | Goede UX, per-step voortgang |

**Actie:** Nieuw `OnboardingSession` model ontwerpen met:
- Geen `marqed_session_id` als required
- Wel `project_path` als required
- 5 onboarding-vragen opslag (niet 8 migration-vragen)

---

### F.2 Step Execution Infrastructure

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `execute_step(unified_id, step)` | L157 | ✅ | Per-step uitvoerbaar is waardevol voor debugging |
| `execute_all()` | L237 | ✅ | Convenience method |
| Step timeouts (30s-1200s) | L185-188 | ✅ | Goede defaults, overnemen |
| Error handling met rollback | L224-235 | ✅ | Robuust patroon |
| `_save_step_result()` | L764 | ✅ | Persistence per step |
| `_save_step_timing()` | L770 | ✅ | Performance tracking |
| `_summarize_result()` | L785 | ✅ | API response formatting |

**Opmerking:** Dit is goed, maar mist:
- ❌ Quality gates (geen evaluatie van output kwaliteit)
- ❌ Checkpoint/resume (geen hervatting na crash)
- ❌ Agent orchestratie (directe service calls)

**Actie:** WorkflowOrchestrator base class gebruiken voor quality gates + checkpoints.

---

### F.3 Step 1: Code Scan

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `_step_1_code_scan()` | L302-366 | 🔄 | Concept goed, maar roept `analyze_application()` aan (lite variant) |
| Auto-registratie applicatie | L323-337 | ✅ | Handig, minder handmatig werk |
| BrownPaperSession aanmaken | L349-351 | ❌ | Nieuwe workflow gebruikt eigen session, niet BrownPaper |
| `analyze_application()` aanroep | L355 | ⚠️ **VALSTRIK** | Dit is de LITE variant, niet de DEEP variant |

**Valstrik F.3.1:** `analyze_application()` vs `_phase1_code_understanding()`
- `analyze_application()` (L853 in A) = shallow scan
- `_phase1_code_understanding()` (L2493 in A) = deep scan met 11 services + SIG

**Beslissing:** 🔄 Herontwerpen — Direct `_phase1_code_understanding()` aanroepen of equivalent.

---

### F.4 Step 2: 8 Vragen Validatie

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `_step_2_validate_questions()` | L368-391 | ❌ | Migration-specifieke 8-vragen, niet voor onboarding |
| MarQed session vereist | L370-372 | ❌ | Nieuwe workflow is onafhankelijk van MarQed |
| Answer counting/validation | L374-389 | 🔄 | Patroon hergebruiken voor onze 5 vragen |

**Actie:** Eigen intake validatie met 5 onboarding-vragen.

---

### F.5 Step 3: Migration Analysis (Miguel)

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `_step_3_migration_analysis()` | L393-424 | ❌ | Migration-specifiek, keyword heuristic |
| `run_migration_analysis()` aanroep | L404 | ❌ | Keyword matching ("150K+ LOC") is fragiel |
| Enrichment met code scan | L407-413 | ✅ | Goed idee, output van stap 1 gebruiken in latere stappen |

**Actie:** Geen migration analysis in onboarding. Code-driven complexity scoring komt uit Module 2 (code understanding).

---

### F.6 Step 4: Specification (Peter)

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `_step_4_specification()` | L426-441 | ❌ | Template-based string concatenatie |
| `generate_specification()` aanroep | L436 | ❌ | Geen synthese, puur concateneren |

**Actie:** Vervangen door Module 9 (Constitution via LLM Council) — echte synthese.

---

### F.7 Step 5: Epics Bottom-Up (Felix)

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `_step_5_epics_bottom_up()` | L443-499 | ✅ | Goede aanpak: code → domains → stories |
| `BusinessDomainExtractorService` | L460-465 | ✅ | W159, bewezen kwaliteit |
| `BusinessDrivenStoryGeneratorService` | L468-471 | ✅ | W159, bewezen kwaliteit |
| Epic dict normalisatie | L476-488 | ✅ | Handige formatting |

**Actie:** Overnemen als Module 4 (Domain Extraction) + Module 6 (Story Generation).

---

### F.8 Step 6: Epics Top-Down (Felix)

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `_step_6_epics_top_down()` | L501-525 | ❌ | Genereert 2e set epics voor reconciliation |
| `generate_tasks()` aanroep | L507 | ❌ | MarQed-afhankelijk, top-down op basis van 8-vragen |

**Reden voor ❌:** We genereren epics 1x goed (Module 6), niet 3x en dan reconcilen.

---

### F.9 Step 7: Enhanced 6-Fase

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `_step_7_enhanced_analysis()` | L527-663 | 🔄 | Waardevolle pipeline, maar als monoliet |
| Per-fase progress callback | L570-599 | ✅ | Goede UX, progress naar DB schrijven |
| Isolated DB session | L602-614 | ✅ | Best practice voor lange operaties |
| 15 min timeout | L552 | ✅ | Realistisch voor LLM operaties |
| `run_enhanced_analysis()` aanroep | L604-608 | ⚠️ **VALSTRIK** | Dit is de HELE 6-fase pipeline als monoliet |

**Valstrik F.9.1:** Enhanced analysis is Phase 1-6 als één blok
- Phase 1: Code Understanding (dupliceert Step 1!)
- Phase 2: Domain Extraction (dupliceert Step 5!)
- Phase 3: Hierarchical Extraction
- Phase 4: Deep Extraction (LLM Council)
- Phase 5: Estimation
- Phase 6: Output

**Probleem:** F draait code analyse en domain extraction DRIE KEER:
1. Step 1 (code scan)
2. Step 5 (bottom-up)
3. Step 7 Phase 1-2 (enhanced)

**Beslissing:** 🔄 Herontwerpen — Individuele fasen extraheren als losse modules, niet als monoliet.

**Actie:**
- Phase 4 (Deep Extraction) → Module 7 (VERPLICHT, niet optioneel)
- Phase 5 (Estimation) → Module 8
- Phase 1-2-3 → Niet dupliceren, we hebben al Module 2 en Module 4

---

### F.10 Step 8: Reconciliation

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `_step_8_reconciliation()` | L665-758 | 🔄 | Concept waardevol, implementatie is workaround |
| `ReconciliationService.reconcile()` | L697-705 | ❌ | Vergelijkt 3 epic-sets — maar we genereren er maar 1 |
| Blind spots detectie | concept | ✅ | Verplaatsen naar Module 11 (Quality Review) |
| Phantom features detectie | concept | ❌ | Relevant bij question-driven, niet bij code-driven |
| FP deltas | concept | ❌ | 1 methode = geen delta |
| Constitution aanmaken | L728-739 | 🔄 | Goed, maar content is leeg. Moet LLM-assisted worden |
| Epics opslaan naar DB | L743-747 | ✅ | Persistence patroon overnemen |

**Actie:**
- Blind spot detectie → Module 11 (Quinn controleert: zijn alle domeinen gedekt door stories?)
- Constitution → Module 9 (LLM-assisted, niet leeg object)
- Epic persistence → Module 10 (Output)

---

## Samenvatting Workflow F

### Wat we overnemen (✅)

| Capability | Nieuwe Module | Bron (F) |
|------------|---------------|----------|
| Per-step execution | Infra | `execute_step()` |
| Step timeouts | Infra | L185-188 |
| Error handling + rollback | Infra | L224-235 |
| Auto-registratie applicatie | M2 | L323-337 |
| BusinessDomainExtractor | M4 | L460-465 |
| BusinessDrivenStoryGenerator | M6 | L468-471 |
| Per-fase progress callback | M7 | L570-599 |
| Isolated DB session | M7 | L602-614 |
| Epic persistence | M10 | L743-747 |

### Wat we NIET overnemen (❌)

| Item | Reden |
|------|-------|
| MarQed session als prerequisite | Eigen intake |
| 8-vragen validatie | Migration-specifiek |
| Migration analysis (Miguel) | Keyword heuristic, migration-only |
| Specification (Peter) | Template-based, geen synthese |
| Step 6 top-down epics | 3x genereren + reconcilen is workaround |
| ReconciliationService | Niet nodig als we 1x goed genereren |
| Phantom features detectie | Question-driven concept |
| FP deltas | 1 methode = geen delta |

### Wat we herontwerpen (🔄)

| Item | Wat anders |
|------|------------|
| Session model | Eigen `OnboardingSession`, geen MarQed dependency |
| Step 1 code scan | Deep variant (`_phase1_code_understanding`), niet lite |
| Step 7 enhanced | Losse modules, niet monoliet |
| Constitution | LLM-assisted synthese, niet leeg object |
| Blind spot detectie | In Module 11 (Quality Review), niet apart |

### Valstrikken gedetecteerd (⚠️)

| # | Naam | Probleem | Keuze |
|---|------|----------|-------|
| F.3.1 | Code Scan | `analyze_application()` = lite | Gebruik deep variant |
| F.9.1 | Enhanced Analysis | 6-fase monoliet, dupliceert Step 1+5 | Extraheer individuele fasen |

---

## Workflow A: BrownPaperService

**Bestand:** `backend/app/services/brown_paper_service.py`
**LOC:** ~3100 (L277-3411)
**Beschrijving:** Bottom-up code analyse met 11 services en 6-fase enhanced pipeline

---

### A.1 Wat voegt A toe dat F niet heeft?

| Capability | Locatie | Beslissing | Reden |
|------------|---------|------------|-------|
| **11-service code understanding** | L2493-2700 | ✅ | Dit is de DEEP variant die F mist |
| Stability Analysis | L894-908 | ✅ | Resource leak detectie, stability score |
| Knowledge Base Context (KB) | L910-924 | ✅ | Agent-specifieke context (betty, diana, marcus) |
| Multi-language scanning | L982-1002 | ✅ | Python, TS/JS, VB.NET, C#, ASP.NET |
| Complexity multiplier in estimation | L3247-3258 | ✅ | Cruciaal voor accurate schattingen |

---

### A.2 De 11 Services (Phase 1 Code Understanding)

| # | Service | Locatie | Beslissing | Wat doet het |
|---|---------|---------|------------|--------------|
| 1 | DependencyGraphService | L2509-2516 | ✅ | Module dependencies, 12 talen |
| 2 | CodeAnalysisAggregatorService | L2519-2534 | ✅ | LOC, complexity metrics |
| 3 | LayeredAnalysisService | L2537-2556 | ✅ | Layer detectie (presentation, domain, etc.) |
| 4 | FoundationDetectionService | L2559-2577 | ✅ | Infra/foundation modules identificeren |
| 5 | BackgroundJobDetectorService | L2580-2592 | ✅ | Scheduled jobs, workers (Week 131) |
| 6 | LoadEstimationService | L2595-2607 | ✅ | Concurrent users, bottlenecks (Week 131) |
| 7 | DeadCodeDetectorService | L2610-2622 | ✅ | Ongebruikte code (Week 132-133) |
| 8 | RuntimeAnalysisService | L2625-2637 | ✅ | Runtime coverage (Week 132-133) |
| 9 | CodeCoverageAnalyzerService | L2640-2652 | ✅ | Test coverage (Week 132-133) |
| 10 | DataLineageService | (verderop) | ✅ | Data flow tracking (Week 136-137) |
| 11 | SIG Quality Metrics | (verderop) | ✅ | 7 kwaliteitsdimensies (Week 144) |

**Actie:** Alle 11 services overnemen in Module 2 (Code Understanding).

---

### A.3 Valstrikken in A

#### ⚠️ A.3.1 Phase 4 Deep Extraction is NEP

**Locatie:** L3172-3225

```python
# For adhoc analysis, we synthesize results from Phase 3
result.deep_extraction_result = {
    'source': 'synthesized_from_phase3',
    ...
}
result.consensus_confidence = 0.75  # Hardcoded!
```

**Probleem:** Phase 4 doet GEEN echte LLM Council analyse. Het kopieert alleen Phase 3 resultaten en markeert ze als "gesynthetiseerd".

**Beslissing:** ❌ **NIET OVERNEMEN** — We hebben de ECHTE deep extraction nodig uit Workflow C (BrownPaperOrchestrator) met Felix + Quinn + Marcus agents.

---

#### ⚠️ A.3.2 `approve_session()` is KAPOT

**Locatie:** L2205-2221

```python
async def approve_session(self, session_id: str, reviewer: str) -> bool:
    ...
    session.status = BrownPaperStatus.APPROVED
    # TODO: Persist to database and link to Green Paper models  <-- NOOIT GEÏMPLEMENTEERD!
    return True
```

**Probleem:** Goedkeuringen worden NIET opgeslagen in de database. Bij restart is alles weg.

**Beslissing:** ❌ **NIET OVERNEMEN** — Gebruik het approval patroon uit Workflow B (MarQedBrownPaperWorkflow) dat WEL naar DB persists.

---

#### ⚠️ A.3.3 `generate_epics()` is NAÏEF

**Locatie:** L2124-2199

```python
# CRUD operations get fixed 3 story points
{"title": uc, "points": 3} for uc in crud_cases

# Other use cases get fixed 5 story points
{"title": use_case, "points": 5}
```

**Probleem:** Een 100-regel CRUD functie krijgt dezelfde 3 punten als een 10.000-regel CRUD functie. Complexity wordt volledig genegeerd.

**Beslissing:** ❌ **NIET OVERNEMEN** — Gebruik `BusinessDrivenStoryGeneratorService` (W159) die WEL complexity meeneemt.

---

### A.4 Complexity Multiplier (✅ OVERNEMEN)

**Locatie:** L3247-3258

```python
complexity_multiplier = 1.0
if very_high > 10:
    complexity_multiplier = 1.5   # +50%
elif high_complexity > 20:
    complexity_multiplier = 1.3   # +30%
elif high_complexity > 10:
    complexity_multiplier = 1.15  # +15%
```

**Beslissing:** ✅ **OVERNEMEN** in Module 8 (Estimation). Zonder multiplier worden complexe codebases onderschat.

---

### A.5 `analyze_application()` vs `_phase1_code_understanding()`

| Aspect | `analyze_application()` (L853) | `_phase1_code_understanding()` (L2493) |
|--------|-------------------------------|---------------------------------------|
| Services | Basis scan + stability + KB | **11 services** |
| Depth | Shallow | **Deep** |
| SIG Metrics | Nee | **Ja** |
| Dead Code | Nee | **Ja** |
| Background Jobs | Nee | **Ja** |
| Load Estimation | Nee | **Ja** |

**Beslissing:** Module 2 gebruikt `_phase1_code_understanding()` logica (de 11 services), niet `analyze_application()`.

---

## Samenvatting Workflow A

### Wat we overnemen (✅)

| Capability | Nieuwe Module | Bron (A) |
|------------|---------------|----------|
| 11-service code understanding | M2 | L2493-2700 |
| DependencyGraphService | M2 | L2509-2516 |
| CodeAnalysisAggregatorService | M2 | L2519-2534 |
| LayeredAnalysisService | M2 | L2537-2556 |
| FoundationDetectionService | M2 | L2559-2577 |
| BackgroundJobDetectorService | M2 | L2580-2592 |
| LoadEstimationService | M2 | L2595-2607 |
| DeadCodeDetectorService | M2 | L2610-2622 |
| RuntimeAnalysisService | M2 | L2625-2637 |
| CodeCoverageAnalyzerService | M2 | L2640-2652 |
| DataLineageService | M2 | (verderop) |
| SIG Quality Metrics | M2 | (verderop) |
| Stability Analysis | M2 of M3 | L894-908 |
| Knowledge Base Context | M1 | L910-924 |
| Complexity multiplier | M8 | L3247-3258 |
| Multi-language scanning | M2 | L982-1002 |

### Wat we NIET overnemen (❌)

| Item | Reden |
|------|-------|
| Phase 4 Deep Extraction | **NEP** — synthetiseert alleen Phase 3 |
| `approve_session()` | **KAPOT** — slaat niet op naar DB |
| `generate_epics()` | **NAÏEF** — vaste story points, negeert complexity |
| `analyze_application()` als geheel | Shallow variant, gebruiken we niet |

### Valstrikken gedetecteerd (⚠️)

| # | Naam | Probleem | Keuze |
|---|------|----------|-------|
| A.3.1 | Phase 4 Deep Extraction | Synthetiseert Phase 3, geen echte LLM | Gebruik C's echte agent council |
| A.3.2 | `approve_session()` | TODO: persist to DB — nooit gedaan | Gebruik B's patroon |
| A.3.3 | `generate_epics()` | Vaste 3/5 story points | Gebruik W159 BusinessDrivenStoryGenerator |

---

---

## Workflow C: BrownPaperOrchestrator

**Bestand:** `backend/app/confucius/workflows/brown_paper.py`
**LOC:** ~477
**Beschrijving:** Confucius 7-stage workflow met agents en quality gates

---

### C.1 Wat voegt C toe?

| Capability | Locatie | Beslissing | Reden |
|------------|---------|------------|-------|
| **WorkflowOrchestrator base** | L34 | ✅ | Quality gates, checkpoints, resume gratis |
| **ECHTE Deep Extraction** | L335-390 | ✅ | Felix + Quinn + Marcus met `run_full_lifecycle()` |
| **User Journey Extraction** | L282-296 | ✅ | **UNIEK** — zit niet in A, B, of F! |
| **7 WorkflowStage definities** | L64-133 | ✅ | Duidelijke stage-structuur met thresholds |
| **Agent routing** | L201-228 | ✅ | `get_agents_for_stage()` + extensions |
| **Parallel agents** | L81, L110 | ✅ | `parallel_agents=True` voor snelheid |

---

### C.2 De 7 Stages

| # | Stage | Agents | Threshold | Required | Timeout |
|---|-------|--------|-----------|----------|---------|
| 1 | code_understanding | Miguel | 0.80 | ✅ | 600s |
| 2 | domain_extraction | Peter, Betty (parallel) | 0.85 | ✅ | 300s |
| 3 | user_journey_extraction | Vicky, Peter | 0.70 | ✅ | 300s |
| 4 | story_extraction | Peter | 0.80 | ✅ | 300s |
| 5 | deep_extraction | Felix, Quinn, Marcus (parallel) | 0.85 | ❌ **OPTIONEEL** | 300s |
| 6 | estimation | Eliza | 0.75 | ✅ | 300s |
| 7 | output_consolidation | Diana | 0.80 | ✅ | 300s |

---

### C.3 ECHTE Deep Extraction (✅ OVERNEMEN)

**Locatie:** L335-390

```python
async def _execute_deep_extraction(self, context) -> Dict:
    extensions = await self.get_agents_for_stage(
        WorkflowStage("deep_extraction", "", ["Felix", "Quinn", "Marcus"]),
        context,
    )

    for ext in extensions:
        if ext.name == "Felix":
            felix_result = await ext.run_full_lifecycle(
                task="Analyze architecture patterns in legacy code",
                ...
            )
            results["architecture_insights"] = felix_result.output

        elif ext.name == "Quinn":
            quinn_result = await ext.run_full_lifecycle(
                task="Review code quality and identify issues",
                ...
            )
            results["quality_findings"] = quinn_result.output.get("findings", [])

        elif ext.name == "Marcus":
            marcus_result = await ext.run_full_lifecycle(
                task="Assess maintainability and technical debt",
                ...
            )
            results["maintenance_recommendations"] = marcus_result.output.get("recommendations", [])
```

**Dit is ECHT** — roept `run_full_lifecycle()` aan op elke agent. Geen synthese.

**Vergelijking met A:**

| Aspect | A (Phase 4) | C (deep_extraction) |
|--------|-------------|---------------------|
| Methode | Kopieert Phase 3 | Roept agents aan |
| Confidence | Hardcoded 0.75 | Van quality gate |
| Felix | ❌ | ✅ Architecture patterns |
| Quinn | ❌ | ✅ Quality findings |
| Marcus | ❌ | ✅ Maintainability |

**Beslissing:** ✅ **OVERNEMEN** — Dit is de echte deep extraction voor Module 7.

---

### C.4 User Journey Extraction (✅ OVERNEMEN)

**Locatie:** L282-296

```python
async def _execute_user_journey_extraction(self, context) -> Dict:
    from ..stages.user_journey_extraction import UserJourneyExtractionStage

    stage = UserJourneyExtractionStage()
    stage_result = await stage.execute(context)
    return stage_result.agent_results.get("final_result", {})
```

**UNIEK** — Vicky (UX) + Peter (Product Owner) extraheren:
- Personas
- Workflows
- Screen flows

Dit zit **niet** in A, B, of F.

**Beslissing:** ✅ **OVERNEMEN** als Module 5 (User Journey).

---

### C.5 Valstrik in C

#### ⚠️ C.5.1 Deep Extraction is OPTIONEEL

**Locatie:** L105-114

```python
WorkflowStage(
    name="deep_extraction",
    ...
    required=False,  # ← PROBLEEM!
)
```

**Probleem:** Deep extraction kan worden overgeslagen. Voor onboarding is dit te waardevol.

**Beslissing:** 🔄 **HERONTWERPEN** — In OnboardingWorkflow wordt deep extraction `required=True`.

---

### C.6 Wat C NIET heeft

| Ontbreekt | Impact |
|-----------|--------|
| Vector DB context | Geen ChromaDB pre-populatie |
| Vragenlijst/intake | Puur code-driven, mist menselijke context |
| Security scan | Geen CWE/OWASP analyse |
| 11-service code understanding | Alleen agents, niet de deep services uit A |

**Conclusie:** C levert de agent orchestratie en echte deep extraction. A levert de 11 services. We combineren beide.

---

## Samenvatting Workflow C

### Wat we overnemen (✅)

| Capability | Nieuwe Module | Bron (C) |
|------------|---------------|----------|
| WorkflowOrchestrator base class | Fundament | L34 |
| WorkflowStage definitie patroon | Alle modules | L64-133 |
| Quality thresholds per stage | Alle modules | L72, L82, etc. |
| Agent routing via extensions | Alle modules | L201-228 |
| Parallel agents execution | M4, M7 | L81, L110 |
| **ECHTE Deep Extraction** | M7 | L335-390 |
| **User Journey Extraction** | M5 | L282-296 |
| UserJourneyExtractionStage | M5 | Import L287 |

### Wat we herontwerpen (🔄)

| Item | Wat anders |
|------|------------|
| deep_extraction stage | `required=True` (niet False) |

### Valstrikken gedetecteerd (⚠️)

| # | Naam | Probleem | Keuze |
|---|------|----------|-------|
| C.5.1 | Deep Extraction optioneel | `required=False` | Maak verplicht in OnboardingWorkflow |

---

---

## Workflow D: MigrationOrchestrator

**Bestand:** `backend/app/confucius/workflows/migration.py`
**LOC:** ~694
**Beschrijving:** Confucius 8-stage workflow voor migration planning

---

### D.1 Wat voegt D toe?

| Capability | Locatie | Beslissing | Reden |
|------------|---------|------------|-------|
| **Security Analysis** | L318-430 | ✅ | **UNIEK** — SecurityScanOrchestrator + Quinn |
| **Quality Review 0.90** | L629-681 | ✅ | Hoogste threshold, eindcontrole |
| **Input validation stage** | L257-276 | ✅ | Goede praktijk: valideer voordat je begint |
| Paul agent (wave planning) | L574-588 | ❌ | Migration-specifiek |
| 8 migration questions | L34-83 | ❌ | Migration-specifiek |

---

### D.2 De 8 Stages

| # | Stage | Agents | Threshold | Required |
|---|-------|--------|-----------|----------|
| 1 | validate_answers | - | **1.0** | ✅ |
| 2 | technical_analysis | Miguel | 0.85 | ✅ |
| 3 | **security_analysis** | Quinn | 0.80 | ✅ |
| 4 | user_journey_extraction | Vicky, Peter | 0.70 | ✅ |
| 5 | generate_specification | Peter, Betty | 0.85 | ✅ |
| 6 | generate_tasks | Felix, Paul | 0.80 | ✅ |
| 7 | estimate_effort | Eliza | 0.75 | ✅ |
| 8 | **quality_review** | Quinn | **0.90** | ✅ |

---

### D.3 Security Analysis (✅ OVERNEMEN)

**Locatie:** L318-430

```python
async def _execute_security_analysis(self, context) -> Dict:
    from app.services.security_scanner import create_security_orchestrator

    orchestrator = create_security_orchestrator()
    report = await orchestrator.scan(Path(source_path))

    # Separates legacy vs modern findings
    legacy_findings = [f for f in report.all_findings if f.scanner.value in legacy_scanners]

    results = {
        "findings": [...],
        "summary": {
            "total_findings": report.total_findings,
            "critical": report.total_critical,
            "high": report.total_high,
            "cwe_top_25_coverage": list(report.cwe_top_25_coverage.keys()),
        },
        "migration_blockers": [f for f in findings if f.severity.value == "critical"],
    }

    # Quinn reviews
    quinn_result = await quinn.run_full_lifecycle(
        task="Review security findings for migration planning",
        ...
    )
    results["quinn_recommendations"] = quinn_result.output.get("recommendations", [])
```

**UNIEK** — Alleen D heeft security scanning. A, B, C, F hebben dit niet.

**Beslissing:** ✅ **OVERNEMEN** als Module 3 (Security Scan), zonder migration-specifieke filters.

---

### D.4 Quality Review 0.90 (✅ OVERNEMEN)

**Locatie:** L629-681

```python
WorkflowStage(
    name="quality_review",
    agents=["Quinn"],
    quality_threshold=0.90,  # HOOGSTE in het systeem
)

async def _execute_quality_review(self, context) -> Dict:
    all_results = {
        "technical_analysis": ...,
        "security_analysis": ...,
        "user_journeys": ...,
        "specification": ...,
        "tasks": ...,
        "estimation": ...,
    }

    quinn_result = await quinn.run_full_lifecycle(
        task="Review migration plan quality and completeness",
        context={"all_results": all_results, "review_type": "quality_gate"},
    )

    results["approval_status"] = "approved" if score >= 0.85 else "needs_work"
```

**Beslissing:** ✅ **OVERNEMEN** als Module 11 (Quality Review) met 0.90 threshold.

---

### D.5 Input Validation (✅ OVERNEMEN)

**Locatie:** L257-276

```python
WorkflowStage(
    name="validate_answers",
    agents=[],
    quality_threshold=1.0,  # Must pass
    max_iterations=1,
)

async def _validate_answers(self, context) -> Dict:
    answers = context.shared_data.get("answers", {})

    missing = [q["id"] for q in QUESTIONS if q["id"] not in answers]
    if missing:
        raise ValueError(f"Missing answers: {missing}")
```

**Beslissing:** ✅ **OVERNEMEN** als Module 1 (Input Validation) met threshold 1.0.

---

### D.6 Wat we NIET overnemen

| Item | Locatie | Reden |
|------|---------|-------|
| 8 migration questions | L34-83 | Migration-specifiek (legacy→target, strategy, data migration) |
| Paul agent | L574-588 | Migration wave planning — niet voor onboarding |
| `migration_blockers` concept | L396-405 | Migration-specifiek |
| `migration_waves` | L550, L586 | Migration-specifiek |

---

## Samenvatting Workflow D

### Wat we overnemen (✅)

| Capability | Nieuwe Module | Bron (D) |
|------------|---------------|----------|
| **Security Analysis** | M3 | L318-430 |
| SecurityScanOrchestrator | M3 | L344-346 |
| Legacy vs modern findings split | M3 | L352-360 |
| Quinn security recommendations | M3 | L412-428 |
| **Quality Review 0.90** | M11 | L629-681 |
| Cross-module review | M11 | L635-650 |
| Approval status logic | M11 | L678-679 |
| **Input Validation** | M1 | L257-276 |
| Threshold 1.0 (must pass) | M1 | L125 |

### Wat we NIET overnemen (❌)

| Item | Reden |
|------|-------|
| 8 migration questions | Migration-specifiek |
| Paul agent | Wave planning is migration-only |
| Migration blockers | Migration-specifiek |
| Migration waves | Migration-specifiek |

---

## Workflow B: MarQedBrownPaperWorkflow

**Bestand:** `backend/app/services/brown_paper_service.py` (L3516-5410)
**LOC:** ~1900
**Beschrijving:** 8-vragen workflow met Vector DB context, answer versioning, en deliverable generation

---

### B.1 Vector DB Context Integration

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `_fetch_vector_context()` | L3556-3644 | ✅ | Haalt relevante context op uit ChromaDB voor betere antwoorden |
| Architecture summary ophalen | L3565-3585 | ✅ | Geeft overzicht van project structuur |
| Relevant docs ophalen | L3590-3610 | ✅ | Top-N relevante documenten |
| Code locations ophalen | L3615-3640 | ✅ | Waar in de code specifieke functionaliteit zit |
| Pre-population bij session start | L4060-4064 | ✅ | Context beschikbaar voordat gebruiker vragen beantwoordt |

**Actie:** Vector DB context integreren in intake fase voor betere vraag-suggesties.

---

### B.2 Database Persistence (Werkend!)

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `_persist_session_to_db()` | L3659-3728 | ✅ | **WERKT** — Slaat alles op inclusief JSON fields |
| `_load_session_from_db()` | L3729-3785 | ✅ | Volledige reconstructie van session |
| `MarQedSessionDB` model | L3661 | ✅ | Bruikbaar als referentie voor ons model |
| JSON serialisatie answers | L3705-3710 | ✅ | Flexibele opslag |

**⚠️ VALSTRIK B.2.1:** `approve_session` in A (L2205) heeft `# TODO: Persist to database` en werkt NIET.
`_persist_session_to_db` in B WERKT wel.

**Beslissing:** ✅ **OVERNEMEN** — B's persistence patroon gebruiken, niet A's.

---

### B.3 Answer Versioning + Audit Trail

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `_save_answer_version()` | L3805-3837 | ✅ | Houdt alle versies van antwoorden bij |
| `MarQedAnswerDB` model | L3812 | ✅ | Answer versioning tabel |
| `is_current` flag | L3825 | ✅ | Weet welke versie actief is |
| `get_answer_history()` | L3839-3866 | ✅ | Kan alle versies opvragen per vraag |
| `_log_event()` | L3787-3803 | ✅ | Full audit trail in `MarQedEventDB` |
| `MarQedEventType` enum | L3791 | ✅ | Gestructureerde event types |

**Actie:** Answer versioning overnemen voor 5 onboarding vragen.

---

### B.4 Session Lifecycle Management

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `start_session()` async | L4031-4104 | ✅ | Async met DB persistence |
| `resume_session()` | L3868-3913 | ✅ | Hervat bestaande sessie met validation |
| `cancel_session()` | L3942-3969 | ✅ | Nette cancellation met reason logging |
| `get_session_status()` | L3915-3940 | ✅ | Gedetailleerde status met progress % |
| Non-resumable check | L3891-3894 | ✅ | Voorkomt resume van completed/cancelled |

**Actie:** Lifecycle methods overnemen voor onze OnboardingSession.

---

### B.5 Question Flow (8 Migration Questions)

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `MARQED_QUESTIONS` constant | L3516+ | ❌ | 8 migration-specifieke vragen |
| `get_current_question()` | L4237-4260 | 🔄 | Patroon overnemen voor 5 onboarding vragen |
| `get_current_question_with_context()` | L4262-4288 | ✅ | Combineert vraag met Vector DB context |
| `submit_answer()` | L4377-4451 | 🔄 | Patroon overnemen, eigen vragen |
| Answer validation (min_length, required) | L4328-4332 | ✅ | Goede validatie |

**Actie:** Question flow herontwerpen voor 5 onboarding vragen:
1. Wat is het primaire doel van deze applicatie?
2. Wie zijn de belangrijkste gebruikers?
3. Wat zijn de kritieke business processen?
4. Welke integraties bestaan er?
5. Wat zijn de belangrijkste pijnpunten?

---

### B.6 Task Generation (Week 159 Enhanced)

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `generate_tasks()` | L4833-4991 | ✅ | Combineert FP estimation + business extraction |
| `BusinessDomainExtractor` (W159) | L4893-4898 | ✅ | Enhanced domain extraction |
| `BusinessDrivenStoryGenerator` (W159) | L4904-4905 | ✅ | Business-driven story generation |
| Fallback to phase-based | L4929-4932 | ✅ | Graceful degradation |
| `_convert_business_stories_to_tasks()` | L5020-5118 | ✅ | Converteert naar Epic/Feature/Story |
| `_generate_phase_based_tasks()` | L5120-5192 | ✅ | Fallback generator |

**⚠️ VALSTRIK B.6.1:** Er zijn 4 varianten van epic generation:
1. A's `generate_epics()` (L2124) — NAÏEF, fixed 3/5 SP
2. B's `_generate_phase_based_tasks()` (L5120) — Fallback, keyword-based
3. B's `_convert_business_stories_to_tasks()` (L5020) — W159 BusinessDriven
4. C's `QuinnEpicGenerator` (L367) — Agent-based via Confucius

**Beslissing:** ✅ **OVERNEMEN** — B's Week 159 BusinessDriven variant met fallback.

---

### B.7 Deliverable Generation

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `_generate_deliverables()` | L4993-5018 | ✅ | Genereert markdown naar project/docs/ |
| `BrownPaperDeliverableService` | L5000 | ✅ | Aparte service voor file generation |
| Output naar `docs/marqed-deliverables/` | L5007 | 🔄 | Pad aanpassen naar `docs/onboarding/` |
| Includes enhanced_analysis | L5010-5011 | ✅ | Volledige context in deliverables |

**Actie:** Deliverable service hergebruiken met eigen templates.

---

### B.8 Database Sync (Dashboard Compatibility)

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `_sync_to_brown_paper_tables()` | L4979-4983 | ✅ | Sync naar brown_paper_epics voor dashboard |
| Error handling met fallback | L4980-4983 | ✅ | Niet-blokkerend |

**Actie:** Eigen sync naar onboarding_* tabellen voor dashboard.

---

## Samenvatting Workflow B

### Wat we overnemen (✅)

| Capability | Nieuwe Module | Bron (B) |
|------------|---------------|----------|
| **Vector DB Context** | M2 Intake | L3556-3644 |
| Pre-population | M2 | L4060-4064 |
| **DB Persistence (werkend!)** | Core | L3659-3728 |
| Session lifecycle | Core | L3868-3969 |
| **Answer Versioning** | Core | L3805-3837 |
| Audit trail (events) | Core | L3787-3803 |
| **Question with context** | M2 | L4262-4288 |
| **Task Generation W159** | M8 | L4833-4991 |
| BusinessDomainExtractor | M8 | L4893-4898 |
| BusinessDrivenStoryGenerator | M8 | L4904-4905 |
| **Deliverable Generation** | M10 | L4993-5018 |

### Wat we NIET overnemen (❌)

| Item | Reden |
|------|-------|
| 8 migration questions | Migration-specifiek |
| `start_session_sync()` (deprecated) | Verouderd, async only |
| `submit_answer_sync()` (deprecated) | Verouderd, async only |

### Valstrikken geïdentificeerd

| Valstrik | Keuze |
|----------|-------|
| A's `approve_session` vs B's `_persist_session_to_db` | B (werkt) |
| A's `generate_epics` (fixed SP) vs B's W159 variant | B (W159) |

---

## Workflow E: OnboardingWorkflowIntegration

**Bestand:** `backend/app/services/extraction_integration_service.py` (L489-562)
**LOC:** ~75
**Beschrijving:** Thin wrapper / hook voor project registration flow

---

### E.1 Project Registration Hook

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `OnboardingWorkflowIntegration` class | L489-548 | 🔄 | Concept goed, maar te simpel |
| `on_project_registered()` | L501-548 | ✅ | Hook patroon is nuttig |
| `auto_extract` parameter | L506 | ✅ | Opt-in extraction |
| `auto_import` parameter | L507 | ✅ | Opt-in kanban import |
| Delegates to `ExtractionIntegrationService` | L529-535 | ✅ | Single responsibility |
| Success/failure logging | L537-546 | ✅ | Basic observability |

---

### E.2 Factory Functions

| Item | Locatie | Beslissing | Reden |
|------|---------|------------|-------|
| `get_onboarding_integration()` | L560-562 | ✅ | Clean factory pattern |
| Dependency injection via db param | L497-498 | ✅ | Testbaar |

---

## Samenvatting Workflow E

### Wat we overnemen (✅)

| Capability | Nieuwe Module | Bron (E) |
|------------|---------------|----------|
| Hook pattern | Events | L501-548 |
| Auto-extract flag | Config | L506 |
| Factory function | Core | L560-562 |

### Wat we NIET overnemen (❌)

| Item | Reden |
|------|-------|
| Direct kanban import | Te simpel, geen quality gate |
| Simple wrapper | We willen rijkere orchestratie |

---

## Alle Workflows Geanalyseerd — Consolidatie

Nu alle 6 workflows (A, B, C, D, E, F) zijn geanalyseerd, hier de complete capability matrix:

### Code Understanding (11 services)

| Service | A | B | C | D | E | F | OnboardingWorkflow |
|---------|---|---|---|---|---|---|-------------------|
| DependencyGraph | ✅ | - | - | - | - | ⚠️ | ✅ van A |
| CodeAnalysis | ✅ | - | - | - | - | ⚠️ | ✅ van A |
| LayeredAnalysis | ✅ | - | - | - | - | ⚠️ | ✅ van A |
| FoundationDetection | ✅ | - | - | - | - | ⚠️ | ✅ van A |
| BackgroundJobDetector | ✅ | - | - | - | - | - | ✅ van A |
| LoadEstimation | ✅ | - | - | - | - | - | ✅ van A |
| DeadCodeDetector | ✅ | - | - | - | - | - | ✅ van A |
| RuntimeAnalysis | ✅ | - | - | - | - | - | ✅ van A |
| CodeCoverageAnalyzer | ✅ | - | - | - | - | - | ✅ van A |
| DataLineage | ✅ | - | - | - | - | - | ✅ van A |
| SIG Quality Metrics | ✅ | - | - | - | - | - | ✅ van A |

### Infrastructure

| Capability | A | B | C | D | E | F | OnboardingWorkflow | Bron |
|------------|---|---|---|---|---|---|-------------------|------|
| Quality Gates | - | - | ✅ | ✅ | - | - | ✅ | C/D |
| Checkpoints/Resume | - | - | ✅ | ✅ | - | - | ✅ | C/D |
| Agent Orchestration | - | - | ✅ | ✅ | - | - | ✅ | C/D |
| DB Persistence | ⚠️ | ✅ | - | - | - | - | ✅ | B |
| Answer Versioning | - | ✅ | - | - | - | - | ✅ | B |
| Vector DB Context | - | ✅ | - | - | - | - | ✅ | B |

### Generation

| Capability | A | B | C | D | E | F | OnboardingWorkflow | Bron |
|------------|---|---|---|---|---|---|-------------------|------|
| Domain Extraction W159 | - | ✅ | - | - | - | - | ✅ | B |
| Story Generation W159 | - | ✅ | - | - | - | - | ✅ | B |
| User Journey Extraction | - | - | ✅ | - | - | - | ✅ | C |
| Deep Extraction (real) | - | - | ✅ | - | - | - | ✅ | C |
| Security Analysis | - | - | - | ✅ | - | - | ✅ | D |

### Speciale Capabilities

| Capability | A | B | C | D | E | F | OnboardingWorkflow | Bron |
|------------|---|---|---|---|---|---|-------------------|------|
| FP Estimation (IFPUG) | - | ✅ | - | - | - | - | ✅ | B |
| Deliverable Generation | - | ✅ | - | - | - | - | ✅ | B |
| Input Validation (1.0) | - | - | - | ✅ | - | - | ✅ | D |
| Final Review (0.90) | - | - | - | ✅ | - | - | ✅ | D |
| Hook Pattern | - | - | - | - | ✅ | - | ✅ | E |

---

## Geïdentificeerde Valstrikken (Totaal)

| # | Valstrik | Workflow | Keuze |
|---|----------|----------|-------|
| 1 | `_phase4_deep_extraction` is NEP | A | ❌ Skip, gebruik C's variant |
| 2 | `approve_session` heeft TODO, werkt niet | A | ❌ Gebruik B's persistence |
| 3 | `generate_epics` fixed 3/5 SP | A | ❌ Gebruik B's W159 variant |
| 4 | `analyze_application()` is LITE variant | F | ⚠️ Gebruik A's deep variant |
| 5 | `deep_extraction` required=False | C | 🔧 Fix naar required=True |
| 6 | Domain Extraction heeft 3 varianten | A/B | ✅ B's W159 variant |
| 7 | Epic Generation heeft 4 varianten | A/B/C | ✅ B's W159 variant |

---

## Volgende Stap: Bouwen

Met alle workflows geanalyseerd en capabilities geïnventariseerd, kunnen we nu de **OnboardingWorkflow** incrementeel gaan bouwen:

### Bouwvolgorde (Module per Module)

1. **M1: Input Validation** — Threshold 1.0, 5 vragen validatie
2. **M2: Intake + Vector DB** — Questions with context
3. **M3: Code Understanding** — 11 services van A
4. **M4: Deep Extraction** — C's echte variant (Felix+Quinn+Marcus)
5. **M5: User Journey** — C's Vicky+Peter
6. **M6: Security Analysis** — D's SecurityScanOrchestrator
7. **M7: Domain Extraction** — B's W159 BusinessDomainExtractor
8. **M8: Story Generation** — B's W159 BusinessDrivenStoryGenerator
9. **M9: FP Estimation** — B's IFPUG integration
10. **M10: Deliverable Generation** — B's markdown output
11. **M11: Final Review** — D's 0.90 threshold

### Test Protocol per Module

Per module, test op alle 3 projecten:
- `/opt/projecten/hci-crs` (9,922 files, 560MB)
- `/opt/projecten/paramedi/FRM` (6,710 files, 191MB)
- `/opt/projecten/paramedi/FysioOne-Classic` (2,235 files, 100MB)

**Criteria per module:**
- Geen errors op alle 3 projecten
- Output is valide (JSON schema, markdown format)
- Performance acceptabel (<5 min voor grootste project)

---

## Module Bouw Status

### M1: Input Validation ✅ COMPLEET

**Datum:** 2026-02-03
**Bestand:** `backend/app/confucius/workflows/onboarding.py`
**Tests:** `backend/tests/standalone_onboarding_m1_test.py`

**Geïmplementeerd:**
- `OnboardingOrchestrator` class met `workflow_type = "onboarding"`
- `ONBOARDING_QUESTIONS` — 5 vragen (4 required, 1 optional)
- `OnboardingValidationResult` dataclass met quality_score
- `validate_input` stage met threshold 1.0
- Factory function `get_onboarding_orchestrator()`

**Test resultaten:**
```
✓ test_questions_defined PASSED
✓ test_valid_input_passes PASSED
✓ test_partial_answers_passes PASSED
✓ test_missing_required_fails PASSED
✓ test_missing_project_path_fails PASSED
✓ test_nonexistent_path_fails PASSED
✓ test_answer_too_short_fails PASSED
✓ test_quality_score_calculation PASSED

Reference Projects:
✓ hci-crs PASSED
✓ FRM PASSED
✓ FysioOne-Classic PASSED
```

**Volgende:** M3: Code Understanding (11 services)

---

### M2: Intake + Vector DB Context ✅ COMPLEET

**Datum:** 2026-02-03
**Bestand:** `backend/app/confucius/workflows/onboarding.py`
**Tests:** `backend/tests/standalone_onboarding_m2_test.py`

**Geïmplementeerd:**
- `IntakeContextResult` dataclass met quality_score berekening
- `intake_context` stage met threshold 0.70 (graceful degradation)
- `_fetch_intake_context()` method
- `_get_chroma_service()` lazy initialization
- Code location extraction met regex patterns
- Deduplicatie van code locations

**Quality Score Berekening:**
- 1.0: Architecture summary + 5+ docs
- 0.85: Docs maar geen architecture summary
- 0.70: Geen ChromaDB (graceful degradation)

**Test resultaten:**
```
✓ test_graceful_degradation_no_chroma PASSED
✓ test_rich_context_full_score PASSED
✓ test_partial_context_reduced_score PASSED
✓ test_empty_context_minimum_score PASSED
✓ test_code_location_extraction PASSED
✓ test_code_location_deduplication PASSED
✓ test_result_to_dict PASSED
✓ test_quality_threshold_met PASSED

Reference Projects (Graceful Degradation):
✓ hci-crs PASSED
✓ FRM PASSED
✓ FysioOne-Classic PASSED
```

**Volgende:** M4: Deep Extraction (Felix+Quinn+Marcus)

---

### M3: Code Understanding (11 services) ✅ COMPLEET

**Datum:** 2026-02-03
**Bestand:** `backend/app/confucius/workflows/onboarding.py`
**Tests:** `backend/tests/standalone_onboarding_m3_test.py`

**Geïmplementeerd:**
- `CodeUnderstandingResult` dataclass met service tracking
- `code_understanding` stage met threshold 0.50
- `_execute_code_understanding()` method
- `_run_sig_quality_analysis()` helper
- 11 services met graceful degradation

**Services:**
1. DependencyGraphService
2. CodeAnalysisAggregatorService (DB-skip)
3. LayeredAnalysisService (DB-skip)
4. FoundationDetectionService
5. BackgroundJobDetectorService
6. LoadEstimationService
7. DeadCodeDetectorService
8. RuntimeAnalysisService
9. CodeCoverageAnalyzerService
10. DataLineageService (DB-skip)
11. SIG Quality Metrics

**Quality Score Berekening:**
- 1.0: 11/11 services
- 0.85: 8+ services
- 0.75: 5+ services
- 0.60: 3+ services
- 0.50: minimum (threshold)

**Test resultaten:**
```
M3 Standalone:
✓ test_quality_score_calculation PASSED
✓ test_simulated_execution PASSED
✓ test_nonexistent_path PASSED
✓ test_quality_threshold_met PASSED
✓ test_to_dict_serialization PASSED

Reference Projects:
✓ hci-crs: 11/11 services, score 1.0
✓ FRM: 11/11 services, score 1.0
✓ FysioOne-Classic: 11/11 services, score 1.0

Integration (M1→M2→M3):
✓ hci-crs: M1=1.0, M2=0.7, M3=1.0 PASSED
✓ FRM: M1=1.0, M2=0.7, M3=1.0 PASSED
✓ FysioOne-Classic: M1=1.0, M2=0.7, M3=1.0 PASSED
```

**Volgende:** M4: Deep Extraction (Felix+Quinn+Marcus)

---

*Log bijgewerkt: 2026-02-03*
