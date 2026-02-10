# Onboarding Architectuur — Fase 24.9

> **Doel:** Geconsolideerde architectuur voor de nieuwe OnboardingOrchestrator,
> gebouwd op de sterke punten van alle 6 bestaande workflows.
>
> **Input:** [onboarding-workflow-analysis.md](onboarding-workflow-analysis.md) (code-analyse van 2026-02-02)
> **Scope:** Onboarding van bestaande projecten (niet greenfield, niet migration)
> **Datum:** 2026-02-02

---

## 1. Inventaris: Wat behouden we per workflow?

### Workflow A: BrownPaperService (Bottom-Up Code Analyse)

| Sterke punt | Wat precies | Waar in nieuwe architectuur |
|-------------|------------|----------------------------|
| **11-service code analyse** | DependencyGraph, CodeAnalysisAggregator, LayeredAnalysis, FoundationDetection, BackgroundJobDetector, LoadEstimation, DeadCodeDetector, RuntimeAnalysis, CodeCoverageAnalyzer, DataLineage, SIG Quality Metrics | **Module 2: Code Understanding** |
| **Enhanced Analysis Pipeline** | 6-fase pipeline met tier-gating (Phase 1-6) | Individuele modules extraheren, niet als monoliet |
| **Deep Extraction (Phase 4)** | LLM Council multi-perspectief analyse — Felix (architecture), Quinn (quality), Marcus (maintainability). **Uniek** — zit nergens anders volledig | **Module 7: Deep Extraction** (VERPLICHT, niet optioneel) |
| **IFPUG FP Estimation (Phase 5)** | Function Point methodiek met complexity multiplier | **Module 8: Estimation** |
| **BusinessDomainExtractor (W159)** | Domein-extractie op basis van code-structuur | **Module 4: Domain Extraction** |
| **BusinessDrivenStoryGenerator (W159)** | Epics/stories vanuit business-domeinen, bewezen (440 epics E2E) | **Module 6: Story Generation** |
| **Session + DB persistence** | BrownPaperSessionDB, BrownPaperAnalysisDB | Hergebruiken of vervangen door eigen OnboardingSession model |

**Niet overnemen van A:**
- Template-based Constitution (geen LLM, te rigide)
- CRUD-based epic generation (vervangen door W159 BusinessDrivenStoryGenerator)
- Pattern-based domain extraction (vervangen door W159 BusinessDomainExtractor)

---

### Workflow B: MarQedBrownPaperWorkflow (Top-Down Questionnaire)

| Sterke punt | Wat precies | Waar in nieuwe architectuur |
|-------------|------------|----------------------------|
| **Vector DB context (ChromaDB)** | Pre-populatie via `_fetch_vector_context()` — top-10 relevante docs, architecture summary | **Module 1: Input Validation** — standaard AAN |
| **Answer versioning + audit trail** | Elke wijziging opgeslagen met versienummer, event logging, reviewer naam | **Module 1: Input Validation** — compliance |
| **~~Dashboard sync bridge~~** | ~~`_sync_to_brown_paper_tables()`~~ — vervalt, geen backward compatibility nodig | ~~Module 10~~ — niet nodig |
| **Deliverable generation** | Markdown docs in `project/docs/marqed-deliverables/` | **Module 10: Output & Deliverables** |
| **Event logging** | MarQedSessionEventDB — elke actie traceerbaar | Doorheen alle modules |

**Niet overnemen van B:**
- 8-question flow (Q1-Q4 zijn migration-specifiek, niet geschikt voor onboarding)
- Migration Analysis heuristic (keyword-matching zoals "150K+ LOC" — te fragiel)
- Template-based Specification (string concatenatie zonder synthese)
- 8 deprecated `*_sync()` methoden (technische schuld)

---

### Workflow C: BrownPaperOrchestrator (Confucius 7-Stage)

| Sterke punt | Wat precies | Waar in nieuwe architectuur |
|-------------|------------|----------------------------|
| **WorkflowOrchestrator base class** | Quality gates, checkpoints, resume, agent routing, SSE progress streaming, escalation | **Fundament** van de hele OnboardingOrchestrator |
| **WorkflowStage dataclass** | `name`, `agents`, `quality_threshold`, `max_iterations`, `depends_on`, `parallel_agents` | Stage-definitie patroon overnemen 1:1 |
| **Quality gate thresholds** | Per-stage evaluatie met domein-specifieke regels, retry bij te lage score | Elke module krijgt een quality gate |
| **Checkpoint/resume** | Na elke succesvolle stage opslaan, hervatten bij falen | Essentieel voor runs van 30+ minuten |
| **Agent assignments** | Multi-agent stages (Peter+Betty parallel, Felix+Quinn+Marcus parallel) | Verfijnen per module |
| **User Journey Extraction** | Vicky + Peter: personas, workflows, screen flows. **Uniek** — zit niet in A of B | **Module 5: User Journey** |
| **Dependency graph** | Stages declareren expliciet `depends_on`, parallellisatie automatisch | Overnemen voor module-ordering |

**Niet overnemen van C:**
- Deep extraction als optioneel (`required=False`) — moet verplicht worden
- Geen vragenlijst — puur code-driven, mist menselijke context
- Geen Vector DB context

---

### Workflow D: MigrationOrchestrator (Confucius 8-Stage)

| Sterke punt | Wat precies | Waar in nieuwe architectuur |
|-------------|------------|----------------------------|
| **Security Analysis stage** | Quinn + SecurityScanOrchestrator: CWE scanners, OWASP, vulnerability detection, legacy-specifieke findings. **Uniek** — zit niet in A, B, of C | **Module 3: Security Scan** |
| **Quality Review met 0.90 threshold** | Hoogste quality gate in het systeem — eindcontrole op alle output | **Module 11: Quality Review** (0.90 threshold) |
| **Answer validation stage** | Eerste stage valideert completeness van input voordat pipeline start | **Module 1: Input Validation** (threshold 1.0) |
| **Question-driven approach** | Menselijke input als aanvulling op code-analyse | Combineren: 5 onboarding-vragen + code-analyse (hybride) |

**Niet overnemen van D:**
- 8 migration-vragen (legacy → target, niet geschikt voor onboarding)
- Migration wave planning (Paul agent) — migration-specifiek
- Geen code-analyse stage — vertrouwt volledig op menselijke antwoorden

---

### Workflow E: OnboardingWorkflowIntegration (Trigger)

| Sterke punt | Wat precies | Waar in nieuwe architectuur |
|-------------|------------|----------------------------|
| **Auto-trigger bij registratie** | `on_project_registered()` start automatisch analyse | Entry point updaten naar nieuwe OnboardingOrchestrator |

**Niet overnemen van E:**
- Tier-based gating op onboarding — onboarding moet altijd volledig draaien

---

### Workflow F: UnifiedOnboardingService (8-Step Orchestrator)

| Sterke punt | Wat precies | Waar in nieuwe architectuur |
|-------------|------------|----------------------------|
| **Per-step execution** | `execute_step(session_id, step_number)` — elke stap individueel uitvoerbaar | Module-level executie via WorkflowOrchestrator |
| **Per-fase progress** | Step 7 schrijft progress naar DB na elke enhanced fase — goede UX | Progress streaming via SSE (Confucius base) |
| **Auto-registratie** | Step 1 registreert automatisch applicatie als die niet bestaat | **Module 2: Code Understanding** |
| **Reconciliation** | Step 8: vergelijkt bottom-up vs top-down vs enhanced, detecteert blind_spots, phantom_features, confidence_heatmap, fp_deltas, domain_disputes | **Selectief overnemen** — zie sectie 3 |
| **Constitution + Epic persistence** | Step 8 maakt BrownPaperConstitution + BrownPaperEpics aan | **Module 10: Output & Deliverables** |
| **Isolated DB session** | Step 7 gebruikt aparte DB session om timezone bugs te voorkomen | Best practice overnemen |

**Niet overnemen van F:**
- 3x epic-generatie + reconciliation (doe het 1x goed, niet 3x + samenvoegen)
- Geen quality gates — output kwaliteit onbekend
- Geen checkpoint/resume — 45+ min werk verloren bij fout
- Afhankelijkheid op MarQed 8-vragen sessie
- Directe service calls ipv agent orchestratie

---

## 2. Zwakke punten: Wat versterken we?

### 2.1 Geen quality gates (F)

**Probleem:** UnifiedOnboardingService draait 8 stappen zonder enige evaluatie. Output kwaliteit is onbekend tot het einde.

**Versterking:** Elke module krijgt een Confucius quality gate (uit C/D):

| Module | Threshold | Evaluator | Retry |
|--------|-----------|-----------|-------|
| 1. Input Validation | 1.0 | Schema validation | 1x |
| 2. Code Understanding | 0.80 | Coverage metrics (files scanned, LOC > 0) | 2x |
| 3. Security Scan | 0.80 | Scan completeness (scanners run, findings parsed) | 2x |
| 4. Domain Extraction | 0.85 | Domain count > 0, business capabilities present | 3x |
| 5. User Journey | 0.70 | Personas + workflows present (lager: UX is subjectief) | 2x |
| 6. Story Generation | 0.80 | Epics > 0, stories hebben acceptance criteria | 3x |
| 7. Deep Extraction | 0.85 | All 3 perspectives present (arch, quality, maint) | 2x |
| 8. Estimation | 0.75 | FP > 0, confidence > 0.5 | 2x |
| 9. Constitution | 0.80 | All required sections present | 2x |
| 10. Output | 0.80 | Deliverables generated, dashboard synced | 2x |
| 11. Quality Review | 0.90 | Cross-module consistency check | 2x |

---

### 2.2 Geen checkpoint/resume (F)

**Probleem:** Als step 7 faalt (15 min timeout) na step 1-6 (45+ min), moet alles opnieuw.

**Versterking:** WorkflowOrchestrator base class biedt dit al (uit C/D):
- `CheckpointService.save_checkpoint()` na elke succesvolle module
- `resume_from_checkpoint=True` bij herstart
- Idempotente modules — overslaan van reeds voltooide stappen

---

### 2.3 Constitution is template-based (A, F)

**Probleem:** `generate_constitution()` in A is puur template-transformatie. Geen synthese, geen LLM.

**Versterking:** Module 9 wordt LLM Council-assisted:
- Input: alle resultaten van Module 2-8
- LLM synthetiseert een coherent project charter
- Quality gate evalueert completeness (mission, principes, scope, constraints, risico's)
- Fallback: template-based als LLM niet beschikbaar

---

### 2.4 Migration Analysis is keyword-matching (B)

**Probleem:** `run_migration_analysis()` zoekt naar letterlijke strings ("150K+ LOC", "Big Bang") — fragiel en migration-specifiek.

**Versterking:** Vervangen door code-driven complexity scoring in Module 2:
- LOC, cyclomatic complexity, dependency depth → gewogen complexity score
- SIG Quality Metrics (7 dimensies) → automatische risk assessment
- Geen keyword-matching, geen menselijke input nodig voor technische assessment

---

### 2.5 Specification is string-concatenatie (B)

**Probleem:** `generate_specification()` plakt antwoorden achter elkaar. Geen synthese.

**Versterking:** Verplaatst naar Module 9 (Constitution) als LLM-assisted synthese:
- Alle data uit Module 2-8 wordt gecombineerd tot 1 coherent document
- LLM identificeert conflicten en gaten
- Gestructureerde output met executive summary

---

### 2.6 Deep Extraction is optioneel (C)

**Probleem:** In BrownPaperOrchestrator staat deep extraction als `required=False`.

**Versterking:** In OnboardingOrchestrator wordt Deep Extraction **verplicht** (`required=True`):
- Felix (architecture patterns), Quinn (quality issues), Marcus (maintainability)
- Quality gate 0.85 — hoge lat omdat dit de kernwaarde van onboarding is
- Parallel execution van de 3 agents voor snelheid

---

### 2.7 Geen security scan in onboarding (A, B, C, F)

**Probleem:** Security scan zit alleen in MigrationOrchestrator (D). Onboarding mist dit.

**Versterking:** Module 3 (Security Scan) toegevoegd:
- Wrapper rond SecurityScanOrchestrator (Fase 37)
- CWE scanners, OWASP, vulnerability detection
- Zonder legacy-specifieke migration filters (die zijn D-specifiek)
- Quality gate 0.80

---

### 2.8 3x epic-generatie is redundant (F)

**Probleem:** F genereert epics 3 keer (bottom-up, top-down, enhanced) en reconcilt dan. Dit is een workaround.

**Versterking:** 1x epic-generatie, goed gedaan:
- Module 4 (Domain Extraction) → BusinessDomainExtractor (W159)
- Module 6 (Story Generation) → BusinessDrivenStoryGenerator (W159) op basis van Module 4 output
- Quality gate na elk — als kwaliteit onvoldoende is, retry met feedback
- Geen reconciliation nodig als de input goed is

---

## 3. Ontbrekende capabilities: Wat voegen we toe?

### 3.1 Hybride aanpak: Code + Mens (NIEUW)

**Probleem:** Workflow A/C zijn puur code-driven (missen menselijke context). Workflow B/D zijn puur question-driven (missen code-analyse). Geen workflow combineert beide goed.

**Toevoeging:** Module 1 combineert 5 onboarding-vragen met auto-detect:

| Q# | Vraag | Required | Auto-detect | Bron |
|----|-------|----------|-------------|------|
| 1 | Wat is dit project? (naam, organisatie, doel) | Ja | Deels (README parsing) | NIEUW |
| 2 | Welke technologie? (talen, frameworks, DB) | Ja | Volledig (code scan) | Module 2 vult aan |
| 3 | Wat zijn de bekende pijnpunten? | Nee | Nee | Menselijke kennis |
| 4 | Wat zijn de constraints? (compliance, team, budget) | Nee | Nee | Menselijke kennis |
| 5 | Wat wil je uit deze analyse halen? | Nee | Nee | Intentie/doel |

**Principe:** Minimale input vereist (1 verplichte vraag als auto-detect tech stack lukt), maximale output.

---

### 3.2 Vector DB context standaard AAN (VERSTERKT)

**Probleem:** Alleen B gebruikt ChromaDB pre-populatie. Andere workflows missen dit.

**Toevoeging:** Module 1 haalt standaard Vector DB context op:
- Top-10 relevante documenten uit ChromaDB
- Architecture summary als pre-populatie voor alle volgende modules
- Beschikbaar in `context.shared_data["vector_context"]`

---

### 3.3 User Journey Extraction in onboarding (VERPLAATST)

**Probleem:** User Journey zit alleen in C (BrownPaperOrchestrator). F mist dit volledig.

**Toevoeging:** Module 5 als dedicated stage:
- Vicky (UX) + Peter (Product Owner)
- Output: personas, workflows, screen flows
- Quality gate 0.70 (lager — UX is subjectief)
- Input: domeinen uit Module 4

---

### 3.4 Cross-module consistency check (NIEUW)

**Probleem:** Geen enkele workflow valideert of de output van alle modules consistent is.

**Toevoeging:** Module 11 (Quality Review) als eindcontrole:
- Quinn met threshold 0.90 (hoogste gate, overgenomen uit D)
- Controleert:
  - Zijn alle domeinen uit Module 4 gedekt door stories in Module 6?
  - Klopt de FP-schatting met de complexity uit Module 2?
  - Zijn security findings uit Module 3 geadresseerd in stories of risico's?
  - Komt de constitution overeen met de werkelijke analyse?
- Output: consistency rapport met eventuele waarschuwingen

---

### 3.5 Onboarding-specifieke vragen (NIEUW)

**Probleem:** Bestaande vragen (B/D) zijn migration-gericht. Er bestaan geen onboarding-specifieke vragen.

**Toevoeging:** 5 nieuwe vragen (zie 3.1) die passen bij het doel "begrijp dit project" ipv "migreer dit project".

---

### 3.6 LLM-assisted Constitution (NIEUW)

**Probleem:** Constitution in A is template-based. Geen intelligentie.

**Toevoeging:** Module 9 als LLM Council-assisted constitution:
- Input: alle resultaten van Module 2-8
- LLM synthetiseert: mission/vision, principes, scope, constraints, risico's, success criteria
- Multi-perspectief review (architecture + quality + business)
- Wordt als sub-fase dieper uitgewerkt (24.9e)

---

## 4. Geconsolideerde Architectuur

### 4.1 Fundament

```python
class OnboardingOrchestrator(WorkflowOrchestrator):
    """
    Extends: WorkflowOrchestrator (confucius/workflows/base.py)

    Inherits:
    - Quality gates met per-stage thresholds en retry
    - Checkpoint/resume via CheckpointService
    - Agent routing via WorkflowRouter
    - SSE progress streaming via QualityProgressStream
    - Escalation bij uitgeputte iterations
    - Idempotente stage execution
    """

    @property
    def workflow_type(self) -> str:
        return "onboarding"

    def get_stages(self) -> List[WorkflowStage]:
        return [...]  # 11 modules als WorkflowStage definitie

    async def execute_stage(self, stage, context) -> StageResult:
        ...  # Dispatch naar module-specifieke executie
```

### 4.2 Pipeline Overzicht

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OnboardingOrchestrator                             │
│              (extends WorkflowOrchestrator)                           │
│                                                                       │
│  VAN BASE: quality gates | checkpoints | resume | agents | SSE       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │ Module 1: INPUT VALIDATION                                   │     │
│  │ Gate: 1.0 | Agent: - | Timeout: 30s                         │     │
│  │                                                               │     │
│  │ Bron: D (answer validation) + B (Vector DB) + NIEUW (vragen) │     │
│  │                                                               │     │
│  │ • 5 onboarding-vragen (1 verplicht, 4 optioneel)            │     │
│  │ • project_path validatie                                      │     │
│  │ • Vector DB context ophalen (ChromaDB)                       │     │
│  │ • Answer versioning + audit trail                            │     │
│  └──────────────────────────┬──────────────────────────────────┘     │
│                              │                                         │
│  ┌───────────────────────────▼─────────────────────────────────┐     │
│  │ Module 2: CODE UNDERSTANDING                                 │     │
│  │ Gate: 0.80 | Agent: Miguel | Timeout: 600s | Retry: 2x      │     │
│  │                                                               │     │
│  │ Bron: A (11 services + SIG) + F (auto-registratie)           │     │
│  │                                                               │     │
│  │ • 11 analyse services parallel                               │     │
│  │ • SIG Quality Metrics (7 dimensies)                          │     │
│  │ • Auto-registratie als applicatie niet bestaat                │     │
│  │ • Q2 auto-detect (tech stack uit code)                       │     │
│  └──────────┬─────────────────────────────┬────────────────────┘     │
│              │                             │                           │
│    ┌─────────▼──────────┐     ┌───────────▼────────────┐             │
│    │ Module 3: SECURITY │     │ Module 4: DOMAIN       │             │
│    │ SCAN               │     │ EXTRACTION             │             │
│    │ Gate: 0.80         │     │ Gate: 0.85             │             │
│    │ Agent: Quinn       │     │ Agent: Peter, Betty    │             │
│    │ Timeout: 300s      │     │ Timeout: 300s          │             │
│    │ Retry: 2x          │     │ Retry: 3x             │             │
│    │                    │     │                        │             │
│    │ Bron: D (security) │     │ Bron: A (W159 BDE)    │             │
│    │                    │     │                        │             │
│    │ • SecurityScanOrch │     │ • BusinessDomain-     │             │
│    │ • CWE scanners     │     │   Extractor (W159)    │             │
│    │ • OWASP findings   │     │ • Peter: boundaries   │             │
│    │ • Vulnerability det│     │ • Betty: capabilities  │             │
│    └────────────────────┘     └───────────┬────────────┘             │
│                                           │                           │
│                              ┌────────────▼────────────┐             │
│                              │ Module 5: USER JOURNEY  │             │
│                              │ Gate: 0.70              │             │
│                              │ Agent: Vicky, Peter     │             │
│                              │ Timeout: 300s           │             │
│                              │ Retry: 2x              │             │
│                              │                         │             │
│                              │ Bron: C (UJ stage)     │             │
│                              │                         │             │
│                              │ • Personas              │             │
│                              │ • Workflows             │             │
│                              │ • Screen flows          │             │
│                              └────────────┬────────────┘             │
│                                           │                           │
│                              ┌────────────▼────────────┐             │
│                              │ Module 6: STORY         │             │
│                              │ GENERATION              │             │
│                              │ Gate: 0.80              │             │
│                              │ Agent: Peter             │             │
│                              │ Timeout: 600s           │             │
│                              │ Retry: 3x              │             │
│                              │                         │             │
│                              │ Bron: A/B (W159 BDSG)  │             │
│                              │                         │             │
│                              │ • BusinessDrivenStory-  │             │
│                              │   Generator (W159)      │             │
│                              │ • Input: M4 domeinen    │             │
│                              │   + M5 user journeys    │             │
│                              └──────────┬──────────────┘             │
│                              ┌──────────┴──────────┐                 │
│                    ┌─────────▼──────┐   ┌──────────▼────────┐       │
│                    │ Module 7: DEEP │   │ Module 8:         │       │
│                    │ EXTRACTION     │   │ ESTIMATION         │       │
│                    │ Gate: 0.85     │   │ Gate: 0.75         │       │
│                    │ VERPLICHT      │   │ Agent: Eliza       │       │
│                    │ Agent: Felix,  │   │ Timeout: 300s      │       │
│                    │ Quinn, Marcus  │   │ Retry: 2x          │       │
│                    │ Timeout: 600s  │   │                    │       │
│                    │ Retry: 2x     │   │ Bron: A (IFPUG)    │       │
│                    │ PARALLEL       │   │                    │       │
│                    │                │   │ • IFPUG FP         │       │
│                    │ Bron: A (Ph4)  │   │ • Complexity mult. │       │
│                    │ + C (agents)   │   │ • Story estimates   │       │
│                    │                │   │                    │       │
│                    │ • Felix: arch  │   │                    │       │
│                    │ • Quinn: qual  │   │                    │       │
│                    │ • Marcus: maint│   │                    │       │
│                    └────────┬───────┘   └─────────┬──────────┘       │
│                             └──────────┬──────────┘                   │
│                              ┌─────────▼───────────┐                 │
│                              │ Module 9:           │                 │
│                              │ CONSTITUTION        │                 │
│                              │ Gate: 0.80          │                 │
│                              │ Agent: LLM Council  │                 │
│                              │ Timeout: 300s       │                 │
│                              │ Retry: 2x          │                 │
│                              │                     │                 │
│                              │ Bron: NIEUW         │                 │
│                              │                     │                 │
│                              │ • LLM-assisted      │                 │
│                              │   synthese           │                 │
│                              │ • Input: M2-M8 all  │                 │
│                              │ • Mission, scope,   │                 │
│                              │   constraints, risks │                 │
│                              └─────────┬───────────┘                 │
│                              ┌─────────▼───────────┐                 │
│                              │ Module 10: OUTPUT   │                 │
│                              │ & DELIVERABLES      │                 │
│                              │ Gate: 0.80          │                 │
│                              │ Agent: Diana        │                 │
│                              │ Timeout: 300s       │                 │
│                              │ Retry: 2x          │                 │
│                              │                     │                 │
│                              │ Bron: B (docs) +    │                 │
│                              │ F (persistence)     │                 │
│                              │                     │                 │
│                              │ • Markdown docs     │                 │
│                              │ • Constitution DB   │                 │
│                              │ • Epic DB persist   │                 │
│                              │ • Eigen data model  │                 │
│                              └─────────┬───────────┘                 │
│                              ┌─────────▼───────────┐                 │
│                              │ Module 11: QUALITY  │                 │
│                              │ REVIEW              │                 │
│                              │ Gate: 0.90          │                 │
│                              │ Agent: Quinn        │                 │
│                              │ Timeout: 120s       │                 │
│                              │ Retry: 2x          │                 │
│                              │                     │                 │
│                              │ Bron: D (0.90 gate) │                 │
│                              │ + NIEUW (cross-mod) │                 │
│                              │                     │                 │
│                              │ • Cross-module      │                 │
│                              │   consistency        │                 │
│                              │ • Domain coverage   │                 │
│                              │ • FP plausibility   │                 │
│                              │ • Security → stories │                 │
│                              └─────────────────────┘                 │
│                                                                       │
│  CHECKPOINT na elke succesvolle module                                │
│  SSE PROGRESS na elke module start/complete                          │
│  QUALITY GATE na elke module output                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Module Definitie (WorkflowStage)

```python
def get_stages(self) -> List[WorkflowStage]:
    return [
        WorkflowStage(
            name="input_validation",
            description="Validate onboarding input and fetch Vector DB context",
            agents=[],
            required=True,
            quality_threshold=1.0,
            max_iterations=1,
            timeout_seconds=30,
        ),
        WorkflowStage(
            name="code_understanding",
            description="Analyze code structure with 11 services + SIG metrics",
            agents=["Miguel"],
            required=True,
            quality_threshold=0.80,
            max_iterations=2,
            timeout_seconds=600,
            depends_on=["input_validation"],
        ),
        WorkflowStage(
            name="security_scan",
            description="Security vulnerability scan with CWE scanners",
            agents=["Quinn"],
            required=True,
            quality_threshold=0.80,
            max_iterations=2,
            timeout_seconds=300,
            depends_on=["code_understanding"],
        ),
        WorkflowStage(
            name="domain_extraction",
            description="Extract business domains from code analysis",
            agents=["Peter", "Betty"],
            required=True,
            parallel_agents=True,
            quality_threshold=0.85,
            max_iterations=3,
            timeout_seconds=300,
            depends_on=["code_understanding"],
        ),
        WorkflowStage(
            name="user_journey_extraction",
            description="Extract personas, workflows, and screen flows",
            agents=["Vicky", "Peter"],
            required=True,
            quality_threshold=0.70,
            max_iterations=2,
            timeout_seconds=300,
            depends_on=["domain_extraction"],
        ),
        WorkflowStage(
            name="story_generation",
            description="Generate business-driven epics and stories",
            agents=["Peter"],
            required=True,
            quality_threshold=0.80,
            max_iterations=3,
            timeout_seconds=600,
            depends_on=["domain_extraction", "user_journey_extraction"],
        ),
        WorkflowStage(
            name="deep_extraction",
            description="LLM Council multi-perspective deep analysis",
            agents=["Felix", "Quinn", "Marcus"],
            required=True,  # VERPLICHT (was optioneel in C)
            parallel_agents=True,
            quality_threshold=0.85,
            max_iterations=2,
            timeout_seconds=600,
            depends_on=["story_generation"],
        ),
        WorkflowStage(
            name="estimation",
            description="IFPUG Function Point estimation with complexity multiplier",
            agents=["Eliza"],
            required=True,
            quality_threshold=0.75,
            max_iterations=2,
            timeout_seconds=300,
            depends_on=["story_generation"],
        ),
        WorkflowStage(
            name="constitution_generation",
            description="LLM Council-assisted project charter generation",
            agents=[],  # LLM Council, niet agent-driven
            required=True,
            quality_threshold=0.80,
            max_iterations=2,
            timeout_seconds=300,
            depends_on=[
                "code_understanding", "security_scan", "domain_extraction",
                "user_journey_extraction", "story_generation",
                "deep_extraction", "estimation",
            ],
        ),
        WorkflowStage(
            name="output_deliverables",
            description="Generate deliverables, sync to dashboard, persist to DB",
            agents=["Diana"],
            required=True,
            quality_threshold=0.80,
            max_iterations=2,
            timeout_seconds=300,
            depends_on=["constitution_generation"],
        ),
        WorkflowStage(
            name="quality_review",
            description="Final cross-module consistency review",
            agents=["Quinn"],
            required=True,
            quality_threshold=0.90,  # Hoogste gate (uit D)
            max_iterations=2,
            timeout_seconds=120,
            depends_on=["output_deliverables"],
        ),
    ]
```

### 4.4 Dependency Graph met Parallellisatie

```
[1] input_validation
 │
 └──→ [2] code_understanding (Miguel, 600s)
       │
       ├──→ [3] security_scan (Quinn, 300s)          ─┐
       │                                                │ PARALLEL
       └──→ [4] domain_extraction (Peter+Betty, 300s) ─┘
             │
             └──→ [5] user_journey_extraction (Vicky+Peter, 300s)
                   │
                   └──→ [6] story_generation (Peter, 600s)
                         │
                         ├──→ [7] deep_extraction (Felix+Quinn+Marcus, 600s) ─┐
                         │                                                      │ PARALLEL
                         └──→ [8] estimation (Eliza, 300s)                    ─┘
                               │
                               └──→ [9] constitution_generation (LLM Council, 300s)
                                     │
                                     └──→ [10] output_deliverables (Diana, 300s)
                                           │
                                           └──→ [11] quality_review (Quinn, 0.90)
```

**Parallelle paren:**
- Module 3 + 4 (beide afhankelijk van 2, geen onderlinge afhankelijkheid)
- Module 7 + 8 (beide afhankelijk van 6, geen onderlinge afhankelijkheid)

**Geschatte doorlooptijd (sequential):** ~55 min
**Geschatte doorlooptijd (met parallellisatie):** ~45 min

---

## 5. Herkomstmatrix: Elke capability → bron

| Capability | Module | Bron workflow | Status |
|-----------|--------|---------------|--------|
| 5 onboarding-vragen | M1 | **NIEUW** | Ontwerpen |
| Vector DB context (ChromaDB) | M1 | B (`_fetch_vector_context`) | Hergebruiken |
| Answer versioning + audit | M1 | B (MarQedAnswerDB) | Hergebruiken |
| Project path validatie | M1 | D (answer validation) | Adapteren |
| 11-service code analyse | M2 | A (`analyze_application`) | Hergebruiken |
| SIG Quality Metrics | M2 | A (Phase 1) | Hergebruiken |
| Auto-registratie | M2 | F (step 1) | Hergebruiken |
| Security scan | M3 | D (Quinn + SecurityScanOrchestrator) | Hergebruiken, zonder migration filter |
| BusinessDomainExtractor | M4 | A/B (W159) | Hergebruiken |
| Peter: domain boundaries | M4 | C (stage 2) | Hergebruiken |
| Betty: business capabilities | M4 | C (stage 2) | Hergebruiken |
| User Journey Extraction | M5 | C (stage 3, UserJourneyExtractionStage) | Hergebruiken |
| BusinessDrivenStoryGenerator | M6 | A/B (W159) | Hergebruiken |
| Deep Extraction (LLM Council) | M7 | A (Phase 4) + C (stage 5, agents) | Hergebruiken, VERPLICHT maken |
| IFPUG FP Estimation | M8 | A (Phase 5) + B (BrownPaperEstimationService) | Hergebruiken |
| LLM-assisted Constitution | M9 | **NIEUW** (vervangt template uit A) | Ontwerpen |
| ~~Dashboard sync~~ | ~~M10~~ | ~~B (`_sync_to_brown_paper_tables`)~~ | Vervalt — geen backward compatibility nodig |
| Markdown deliverables | M10 | B (`_generate_deliverables`) | Hergebruiken |
| Constitution + Epic DB persist | M10 | F (step 8) | Hergebruiken |
| Cross-module consistency check | M11 | **NIEUW** + D (0.90 threshold) | Ontwerpen |
| Quality gates per module | Alle | C/D (WorkflowOrchestrator) | Automatisch via base class |
| Checkpoint/resume | Alle | C/D (CheckpointService) | Automatisch via base class |
| SSE progress streaming | Alle | C/D (QualityProgressStream) | Automatisch via base class |
| Event logging | Alle | B (MarQedSessionEventDB) | Hergebruiken |
| Isolated DB sessions | M7 | F (step 7 pattern) | Best practice |

**Telling:**
- **Hergebruiken:** 20 capabilities uit bestaande workflows
- **Nieuw ontwerpen:** 3 capabilities (onboarding-vragen, LLM constitution, cross-module check)
- **Automatisch via base class:** 3 capabilities (quality gates, checkpoints, SSE)

---

## 6. Wat we NIET overnemen (en waarom)

| Item | Uit workflow | Reden voor uitsluiting |
|------|-------------|----------------------|
| 8-question migration flow | B, D | Migration-specifiek, niet geschikt voor onboarding |
| Migration Analysis (keyword heuristic) | B | Fragiel (letterlijke string matching), migration-only |
| Template-based Specification | B | String concatenatie zonder synthese — vervangen door M9 |
| 3x epic-generatie + reconciliation | F | Workaround voor niet weten welke methode de beste is. Doe het 1x goed |
| Reconciliation Service | F | Niet nodig als we 1x genereren met quality gates |
| Migration wave planning (Paul agent) | D | Migration-specifiek |
| Phase-based fallback tasks | B | Genereert generieke 4-fase templates |
| Deprecated sync methods | B | 8 `*_sync()` methoden — technische schuld |
| Tier-based gating op onboarding | E | Onboarding moet altijd volledig draaien |
| MarQed 8-vragen als prerequisite | F | Nieuwe onboarding heeft eigen 5-vragen intake |

---

## 7. Reconciliation: Selectief overnemen

De ReconciliationService uit F is conceptueel waardevol maar architecturaal een workaround.

**Wat we WEL overnemen:**
- Het **concept** van blind spot detectie → ingebouwd in Module 11 (Quality Review)
- Quinn controleert of domeinen uit M4 gedekt zijn door stories in M6
- Quinn controleert of security findings uit M3 geadresseerd zijn

**Wat we NIET overnemen:**
- 3 sets epics vergelijken (bottom-up vs top-down vs enhanced)
- `phantom_features` detectie (relevant bij question-driven flow, niet bij code-driven)
- `fp_deltas` tussen methoden (1 methode = geen delta)

**Waarom:** De reconciliation in F bestaat omdat er 3 onafhankelijke epic-generatie methoden draaien. In de nieuwe architectuur is er 1 methode (M4→M6) met quality gates. De cross-module consistency check in M11 vangt de rest op.

---

## 8. Gewenste Output van Onboarding

Na succesvolle onboarding weet het systeem:

| # | Output | Module | Formaat |
|---|--------|--------|---------|
| 1 | **Project metadata** | M1 + M2 | Applicatie record in DB |
| 2 | **Code structuur** | M2 | 11 analyse-rapporten (LOC, complexity, deps, layers, SIG) |
| 3 | **Security posture** | M3 | CWE findings, OWASP violations, vulnerability lijst |
| 4 | **Business domeinen** | M4 | BusinessDomain objecten met capabilities |
| 5 | **User journeys** | M5 | Personas, workflows, screen flows |
| 6 | **Epics & stories** | M6 | BrownPaperEpic records met acceptance criteria |
| 7 | **Diepte-analyse** | M7 | Architecture patterns, quality issues, maintainability |
| 8 | **FP schatting** | M8 | Function Points, effort hours, confidence |
| 9 | **Project charter** | M9 | Constitution met mission, scope, constraints, risico's |
| 10 | **Deliverables** | M10 | Markdown docs + dashboard data |
| 11 | **Kwaliteitsrapport** | M11 | Consistency score, waarschuwingen |

---

## 9. Agent Toewijzing

| Agent | Modules | Rol |
|-------|---------|-----|
| **Miguel** | M2 | Metrics specialist — code understanding |
| **Quinn** | M3, M7, M11 | Security + quality + eindcontrole |
| **Peter** | M4, M5, M6 | Product Owner — domeinen, journeys, stories |
| **Betty** | M4 | Business Analyst — business capabilities |
| **Vicky** | M5 | UX Designer — personas, screen flows |
| **Felix** | M7 | Architecture patterns |
| **Marcus** | M7 | Maintainability assessment |
| **Eliza** | M8 | Estimation specialist |
| **Diana** | M10 | Documentation — deliverables |

**9 van 11 agents** worden ingezet. Niet gebruikt: Paul (migration), Tessa (testing — geen tests in onboarding).

---

## 10. Sub-fasen Planning

| Sub-fase | Modules | Wat bouwen | Nieuwe code | Hergebruik |
|----------|---------|-----------|-------------|------------|
| **24.9a** | M1 + M2 | OnboardingOrchestrator scaffold, Input module, Code Understanding module | `onboarding_orchestrator.py`, `onboarding_intake_service.py` | `analyze_application()`, ChromaDB fetch |
| **24.9b** | M3 + M4 | Security Scan module, Domain Extraction module | Wrapper services | SecurityScanOrchestrator, BusinessDomainExtractor |
| **24.9c** | M5 + M6 | User Journey module, Story Generation module | Wrapper services | UserJourneyExtractionStage, BusinessDrivenStoryGenerator |
| **24.9d** | M7 + M8 | Deep Extraction module (VERPLICHT), Estimation module | Wrapper services | LLM Council, BrownPaperEstimationService |
| **24.9e** | M9 | Constitution via LLM Council | `constitution_service.py` | Template als fallback |
| **24.9f** | M10 + M11 | Output module, Quality Review module | `deliverable_service.py`, quality rules | Dashboard sync, deliverable gen |
| **24.9g** | API + Test | API endpoints, E2E test, entry point update | `api/onboarding.py`, tests | - |

Elke sub-fase levert werkende, testbare functionaliteit op.

---

## 11. Risico's en Mitigatie

| Risico | Impact | Mitigatie |
|--------|--------|----------|
| LLM niet beschikbaar (M9 constitution) | Constitution degradeert | Fallback naar template-based (huidige A methode) |
| Lange doorlooptijd (45 min) | UX probleem | SSE progress streaming + checkpoint/resume |
| Quality gate te streng | Pipeline faalt te vaak | Iteratief thresholds bijstellen na eerste runs |
| brown_paper_service.py (5400 LOC) raakt | Regressie risico | Nieuwe orchestrator roept bestaande services aan, wijzigt ze niet |

---

## 12. Valstrikken: Zelfde naam, andere implementatie — welke kiezen we?

Meerdere workflows hebben capabilities met dezelfde naam maar totaal andere implementaties.
Per capability hieronder de analyse en de keuze voor de nieuwe onboarding.

### 12.1 "Domain Extraction" — 3 incompatibele varianten

| Variant | Locatie | Algoritme | Output kwaliteit |
|---------|---------|-----------|-----------------|
| Basic `_extract_domains()` | A L1653 | Directory namen → use cases | **Slecht** — `{name: "users", use_cases: ["get_user"]}` |
| Generic `_phase2_domain_extraction()` | A L2778 | Dependency graph + exclude foundation | **Matig** — geen business context |
| **Enhanced `_enhanced_domain_extraction()`** | A L2875 | BusinessDomainExtractor (W159) met healthcare patterns, entity tracking | **Goed** — `{name: "Patient Management", entities: [...], patterns: [...]}` |

**Keuze:** Enhanced (BusinessDomainExtractor W159) → **Module 4**
**Waarschuwing:** De basic variant mag NIET per ongeluk aangeroepen worden. De nieuwe orchestrator moet expliciet `BusinessDomainExtractorService` aanroepen, niet de legacy `_extract_domains()`.

### 12.2 "Epic/Story Generation" — 4 totaal verschillende algoritmes

| Variant | Locatie | Story Points | Probleem |
|---------|---------|-------------|----------|
| Naive `generate_epics()` | A L2124 | Vast: 3 (CRUD), 5 (overig) | 100-regel en 10.000-regel functie krijgen dezelfde punten |
| **BusinessDrivenStoryGenerator** | A enhanced L2950 | Dynamisch op basis van code metrics | Beste — bewezen met 440 epics E2E |
| Hierarchical | A L3116 | Tier-afhankelijk (5 niveaus) | Variabel, nuttig als sub-component |
| Hybrid | B L4833 | FP-based met fallback naar templates | Redelijk, maar fallback is zwak |

**Keuze:** BusinessDrivenStoryGenerator (W159) → **Module 6**
**Optioneel:** HierarchicalStoryExtractionService als verrijking voor diepere breakdown (function/class/module/system level).
**Waarschuwing:** De naive `generate_epics()` is NIET acceptabel — negeert code complexity volledig.

### 12.3 "Code Understanding" — Lite vs Deep

| Variant | Locatie | Diepte | Bevat |
|---------|---------|--------|-------|
| Lite `analyze_application()` | A L853 | Shallow | Modules, domains, patterns, stability |
| **Deep `_phase1_code_understanding()`** | A L2493 | Deep | Dependency graph, layers, foundation, bg jobs, SIG metrics, 11 services |

**Keuze:** Deep variant → **Module 2**. 1x draaien, niet 2x zoals F doet (step 1 lite + step 7 deep).
**Waarschuwing:** F draait code analyse TWEE KEER met dezelfde underlying services. Dat is 10 minuten verspilling.

### 12.4 "Constitution" vs "Specification" — Ander doel

| Document | Workflow | Perspectief | Doel | Secties |
|----------|----------|-------------|------|---------|
| **Constitution** | A `generate_constitution()` | Bottom-up (code) | Wat zegt de code over dit project? | Mission, principes, scope, constraints, risico's |
| **Specification** | B `generate_specification()` | Top-down (mens) | Hoe gaan we dit migreren? | Executive summary, current state, target state, migration approach |

**Keuze:** Constitution-concept → **Module 9** (maar dan LLM-assisted ipv template-based).
Specification is migration-specifiek en hoort NIET in onboarding.
**Let op:** Dit zijn NIET dezelfde documenten met een andere naam. Ze hebben een fundamenteel ander perspectief.

### 12.5 "Estimation" — Zelfde basis, maar geheime multiplier

| Variant | Locatie | Basis | Extra |
|---------|---------|-------|-------|
| Basic | B | BrownPaperEstimationService (IFPUG FP) | Geen |
| **Enhanced** | A Phase 5 | BrownPaperEstimationService (IFPUG FP) | **Complexity multiplier** |
| Agent-wrapped | C (Eliza) | Agent roept service aan | Onbekend |

**Complexity multiplier formule (A enhanced):**
```python
if very_high_complexity > 10:  multiplier = 1.5   # +50%
elif high_complexity > 20:     multiplier = 1.3   # +30%
elif high_complexity > 10:     multiplier = 1.15  # +15%
else:                          multiplier = 1.0   # geen correctie
```

**Keuze:** IFPUG FP **met** complexity multiplier → **Module 8**. Zonder multiplier worden complexe codebases structureel onderschat.

### 12.6 "Deep Extraction" — Echt vs Nep

| Variant | Locatie | Methode | Kwaliteit |
|---------|---------|---------|-----------|
| **Nep (gesynthetiseerd)** | A Phase 4 L3172 | Kopieert Phase 3 resultaten, markeert als `source: synthesized_from_phase3` | 0.75 confidence — **nep** |
| **Echt (agent council)** | C stage 5 | Felix + Quinn + Marcus via agent extensions, onafhankelijke LLM analyse | Hoog — echt multi-perspectief |

**Keuze:** C's echte agent council → **Module 7** (VERPLICHT).
**Waarschuwing:** A enhanced's Phase 4 doet ALSOF het deep extraction is, maar synthetiseert alleen uit eerdere resultaten. Dit is de gevaarlijkste valstrik — het label zegt "deep extraction" maar het is een kopie.

### 12.7 "Approval Workflow" — A is kapot

| Aspect | Workflow A | Workflow B |
|--------|-----------|-----------|
| DB persistence | `# TODO` — **niet geïmplementeerd** | `_persist_session_to_db()` ✅ |
| Audit trail | Geen | `MarQedEventType.SESSION_APPROVED` ✅ |
| Status type | BrownPaperStatus (Enum) | String |
| Reviewer tracking | Parameter aanwezig, niet opgeslagen | Opgeslagen in event log ✅ |

**Keuze:** B's patroon → **Module 11** escalation path (DB persistence + audit trail + event logging).
**Waarschuwing:** A's `approve_session()` slaat NIETS op in de database. Goedkeuringen verdwijnen bij restart.

### 12.8 "Security Scan" — Alleen in D

| Workflow | Heeft security scan | Scope |
|----------|-------------------|-------|
| A, B, C, F | Nee | - |
| **D** | Ja | Quinn + SecurityScanOrchestrator, CWE, OWASP |

Geen conflict — er is maar 1 implementatie. Maar het ontbreekt in alle onboarding-workflows. → **Module 3** neemt dit over uit D.

---

## 13. Ongebruikte capabilities die we alsnog toevoegen

Op basis van een brede codebase-scan zijn er bestaande services die relevant zijn voor onboarding maar in geen enkele workflow (A-F) volledig benut worden.

### 13.1 Knowledge Base context (KB1 + KB5) → Module 1 + alle modules

| Service | Locatie | Wat |
|---------|---------|-----|
| `FamousBugsLoader` | `services/knowledge_base/famous_bugs_loader.py` | 32 beroemde bugs (Ariane 5, Therac-25, Y2K) met CWE mappings |
| `PostMortemsLoader` | `services/knowledge_base/post_mortems_loader.py` | 52 post-mortems (GitHub, Stripe, AWS) met root cause |
| `KBContextProvider` | `services/knowledge_base/kb_context_provider.py` | Routeert KB context per agent-rol |

**Toevoegen aan:** Module 1 laadt KB context in `shared_data["kb_context"]`. Agents krijgen rolspecifieke context:
- Quinn (M3, M7, M11): famous bugs met CWE filter + post-mortems
- Felix (M7): post-mortems voor architecture failure patterns
- Marcus (M7): post-mortems voor maintainability lessons

### 13.2 Stability/Resource Leak Detection → Module 3 of Module 7

| Service | Locatie | Wat |
|---------|---------|-----|
| `ResourceLeakDetectorService` | `services/stability/detector_service.py` | Detecteert unclosed file handles, DB connection leaks, memory leaks, transaction leaks |

**Toevoegen aan:** Module 3 (Security Scan) als sub-scan naast CWE/OWASP. Stability issues zijn security-adjacent.

### 13.3 SpecReviewService → Module 9 (Constitution) review mechanisme

| Service | Locatie | Wat |
|---------|---------|-----|
| `SpecReviewService` | `services/spec_review_service.py` | Felix genereert, Quinn reviewt adversarial. Escalatie bij >3 critical issues. |

**Toevoegen aan:** Module 9 als review-mechanisme voor de LLM-generated constitution. Felix+Quinn adversarial review is bewezen patroon.

### 13.4 StageReviewService → Module 11 (Quality Review) multi-model consensus

| Service | Locatie | Wat |
|---------|---------|-----|
| `StageReviewService` | `services/stage_review/stage_review_service.py` | Multi-model LLM council review, consensus calculation, automatic 2nd round |

**Toevoegen aan:** Module 11 als onderliggende engine voor cross-module quality review. Bestaand en bewezen.

### 13.5 CouncilHumanReviewService → Module 11 escalation path

| Service | Locatie | Wat |
|---------|---------|-----|
| `CouncilHumanReviewService` | `services/council_human_review_service.py` | 6-fase council met human-in-the-loop: generation → peer review → consensus → human review → finalize → approve |

**Toevoegen aan:** Module 11 als escalation path wanneer Quinn's automated review borderline scoort (bijv. 0.85-0.89). Menselijke review als vangnet.

### 13.6 Report Generation Services → Module 10 (Output)

| Service | Locatie | Wat |
|---------|---------|-----|
| `LayeredReportingService` | `services/layered_reporting_service.py` | Executive summary, technical deep-dive, improvement backlog, SWOT in HTML/Markdown/JSON |
| `ComplexityDashboardService` | `services/complexity_dashboard_service.py` | Module-level complexity, trends, hotspots, health status |

**Toevoegen aan:** Module 10. Diana gebruikt deze services voor gestructureerde deliverables ipv custom rapport-generatie.

### 13.7 ImpactPreviewService → Module 6 of Module 11 (optioneel)

| Service | Locatie | Wat |
|---------|---------|-----|
| `ImpactPreviewService` | `services/impact_preview_service.py` | Felix analyseert impact per story over 5 dimensies (arch, security, perf, UX, data) |

**Optioneel toevoegen aan:** Module 11 als post-generatie validatie op gegenereerde stories. Niet essentieel voor MVP.

---

## 14. Bijgewerkte Herkomstmatrix (compleet)

| Capability | Module | Bron | Specifieke variant | Status |
|-----------|--------|------|-------------------|--------|
| 5 onboarding-vragen | M1 | **NIEUW** | - | Ontwerpen |
| Vector DB context (ChromaDB) | M1 | B `_fetch_vector_context` | - | Hergebruiken |
| **Knowledge Base context** | M1 | KB1+KB5 `KBContextProvider` | - | **Toevoegen** |
| Answer versioning + audit | M1 | B `MarQedAnswerDB` | - | Hergebruiken |
| Project path validatie | M1 | D answer validation | - | Adapteren |
| Code analyse (11 services + SIG) | M2 | A `_phase1_code_understanding` | **Deep variant** (niet lite) | Hergebruiken |
| Auto-registratie | M2 | F step 1 | - | Hergebruiken |
| Security scan (CWE/OWASP) | M3 | D SecurityScanOrchestrator | Zonder migration filter | Hergebruiken |
| **Stability/resource leak scan** | M3 | `ResourceLeakDetectorService` | - | **Toevoegen** |
| Domain extraction | M4 | A `_enhanced_domain_extraction` | **W159 BusinessDomainExtractor** (niet basic/generic) | Hergebruiken |
| Peter: domain boundaries | M4 | C stage 2 | - | Hergebruiken |
| Betty: business capabilities | M4 | C stage 2 | - | Hergebruiken |
| User Journey Extraction | M5 | C stage 3 `UserJourneyExtractionStage` | - | Hergebruiken |
| Story generation | M6 | A `_generate_business_driven_stories` | **W159 BusinessDrivenStoryGenerator** (niet naive generate_epics) | Hergebruiken |
| Deep Extraction | M7 | C stage 5 agent council | **Echte agent council** (niet A's gesynthetiseerde variant) | Hergebruiken |
| IFPUG FP Estimation | M8 | A Phase 5 | **Met complexity multiplier** (niet zonder) | Hergebruiken |
| LLM-assisted Constitution | M9 | **NIEUW** | - | Ontwerpen |
| **Constitution review** | M9 | `SpecReviewService` | Felix+Quinn adversarial | **Toevoegen** |
| Markdown deliverables | M10 | B `_generate_deliverables` | - | Hergebruiken |
| **Structured reports** | M10 | `LayeredReportingService` | Executive + technical + SWOT | **Toevoegen** |
| Constitution + Epic DB persist | M10 | F step 8 | - | Hergebruiken |
| Cross-module consistency | M11 | **NIEUW** + D 0.90 threshold | - | Ontwerpen |
| **Multi-model consensus** | M11 | `StageReviewService` | Multi-LLM council | **Toevoegen** |
| **Human escalation path** | M11 | `CouncilHumanReviewService` | 6-fase council met human review | **Toevoegen** |
| **Approval workflow** | M11 | B `approve_session` patroon | **B's variant** (met DB + audit, niet A's kapotte variant) | Hergebruiken |
| Quality gates per module | Alle | C/D `WorkflowOrchestrator` | - | Automatisch via base class |
| Checkpoint/resume | Alle | C/D `CheckpointService` | - | Automatisch via base class |
| SSE progress streaming | Alle | C/D `QualityProgressStream` | - | Automatisch via base class |
| Event logging | Alle | B `MarQedSessionEventDB` | - | Hergebruiken |

**Bijgewerkte telling:**
- **Hergebruiken:** 20 capabilities (met expliciete variant-keuze)
- **Nieuw ontwerpen:** 3 capabilities (onboarding-vragen, LLM constitution, cross-module check)
- **Toevoegen uit ongebruikte services:** 7 capabilities (KB context, stability scan, spec review, stage review, human review, structured reports, approval)
- **Automatisch via base class:** 3 capabilities

---

*Architectuur gebaseerd op code-analyse van 6 workflows (~8000 LOC), 12+ aanvullende services, WorkflowOrchestrator base class, en het [onboarding-workflow-analysis.md](onboarding-workflow-analysis.md) analysedocument.*
*Valstrikken-analyse: 8 gevallen van zelfde naam / andere implementatie geïdentificeerd en opgelost.*
