# Fase 32E: Quality Harness — Autonomous Quality Assurance Pipeline

**Status:** PLANNED
**Priority:** CRITICAL (Quality Foundation)
**Timeline:** KW27-30 (Week 191-194)
**Effort:** 120 uur (~4 weken)
**Dependencies:** Fase 32A-32D (Ralph Wiggum Loop), Fase 31 (CWE Security Scanner), Fase 23.5 (Confucius Orchestrator)

---

## Executive Summary

Fase 32E voegt een **kwaliteitsharnas** toe aan de Ralph Wiggum autonomous loop. Waar 32A-32D de motor bouwen (autonome uitvoering, guardrails, PRP, checkpoints), bouwt 32E de **remmen, navigatie en co-piloot**: twee onafhankelijke review-agents (PM + QA) die elke micro-deliverable inhoudelijk en kwalitatief toetsen voordat de loop verder gaat.

**Het probleem dat we oplossen:**
> De huidige `validation.sh` doet alleen mechanische checks: "bestaat het bestand?" en "draait pytest?". Niemand toetst of wat gebouwd is ook daadwerkelijk is wat de PRD vroeg. En als later iets nieuws wordt gebouwd, wordt niet gecontroleerd of eerder opgeleverde functionaliteit nog steeds werkt.

**De oplossing:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FASE 32E: QUALITY HARNESS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐            │
│  │ MICRO-         │    │ DUAL REVIEW    │    │ PROGRESSIVE    │            │
│  │ DECOMPOSITION  │ →  │ GATES          │ →  │ REGRESSION     │            │
│  │                │    │                │    │                │            │
│  │ PRD → kleinste │    │ PM Agent:      │    │ Na elke        │            │
│  │ toetsbare      │    │  "Is dit wat   │    │ acceptatie:    │            │
│  │ eenheden       │    │   gevraagd     │    │ ALLE eerdere   │            │
│  │                │    │   is?"         │    │ tests opnieuw  │            │
│  │ Elk met:       │    │                │    │                │            │
│  │ - ID           │    │ QA Agent:      │    │ Bij sprint-    │            │
│  │ - Criterium    │    │  "Voldoet dit  │    │ einde: full    │            │
│  │ - Test         │    │   aan          │    │ regression     │            │
│  │ - Dependency   │    │   kwaliteit?"  │    │ + rapport      │            │
│  └────────────────┘    └────────────────┘    └────────────────┘            │
│                                                                              │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐            │
│  │ CONTRACT       │    │ DEPENDENCY     │    │ TRACEABILITY   │            │
│  │ VERIFICATION   │    │ IMPACT SCAN    │    │ MATRIX         │            │
│  │                │    │                │    │                │            │
│  │ API/DB         │    │ Blast radius   │    │ PRD → code →   │            │
│  │ interfaces     │    │ per wijziging  │    │ test mapping   │            │
│  │ intact?        │    │                │    │ per sprint     │            │
│  └────────────────┘    └────────────────┘    └────────────────┘            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Kernprincipe: Micro-Deliverable Architectuur

**Alles wordt opgebroken in de kleinst mogelijke toetsbare eenheid.**

Niet "implementeer OAuth login" maar:
```
MD-001: Gebruiker ziet inlogknop op landing page
MD-002: Klik op inlogknop opent provider selectie modal
MD-003: Selectie van Google triggert OAuth redirect
MD-004: Succesvolle callback schrijft session token
MD-005: Session token wordt gevalideerd bij API calls
MD-006: Ongeldige token geeft 401 response
MD-007: Token verloopt na configureerbare TTL
```

Elke micro-deliverable doorloopt de volledige quality pipeline. Dit betekent meer cycles, maar elke cycle is klein, snel en verifieerbaar.

---

## Quality Pipeline — Per Micro-Deliverable

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    QUALITY PIPELINE PER MICRO-DELIVERABLE                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [Agent bouwt micro-deliverable]                                             │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────┐                                                     │
│  │ 1. PM ACCEPTANCE    │ ← "Is dit wat de PRD vroeg?"                        │
│  │    GATE             │   Inhoudelijke toetsing tegen micro-deliverable     │
│  │                     │   acceptatiecriteria                                │
│  └──────────┬──────────┘                                                     │
│        ACCEPT│    │REJECT → terug naar agent met PM feedback                │
│             ▼                                                                │
│  ┌─────────────────────┐                                                     │
│  │ 2. QA GATE:         │ ← Linting, complexity, dead code, patterns         │
│  │    CODE QUALITY     │   pylint/eslint score >= threshold                  │
│  └──────────┬──────────┘                                                     │
│         PASS│    │FAIL → terug naar agent met QA feedback                   │
│             ▼                                                                │
│  ┌─────────────────────┐                                                     │
│  │ 3. QA GATE:         │ ← CWE Scanner (Fase 31), dependency audit          │
│  │    SECURITY         │   Injection patterns, credential exposure           │
│  └──────────┬──────────┘                                                     │
│         PASS│    │FAIL → HARD STOP, terug met security finding              │
│             ▼                                                                │
│  ┌─────────────────────┐                                                     │
│  │ 4. QA GATE:         │ ← pytest/jest, coverage >= 80% (target 95%)        │
│  │    TESTS+COVERAGE   │   Alle bestaande tests moeten ook slagen           │
│  └──────────┬──────────┘                                                     │
│         PASS│    │FAIL → terug naar agent met specifieke failures           │
│             ▼                                                                │
│  ┌─────────────────────┐                                                     │
│  │ 5. QA GATE:         │ ← Geen regressie in response time/memory           │
│  │    PERFORMANCE      │   Benchmark vergelijking pre/post                  │
│  └──────────┬──────────┘                                                     │
│         PASS│    │WARN → log, niet blokkeren tenzij >20% degradatie         │
│             ▼                                                                │
│  ┌─────────────────────┐                                                     │
│  │ 6. CONTRACT         │ ← API signatures, DB schemas, interfaces           │
│  │    VERIFICATION     │   Backward compatibility check                     │
│  └──────────┬──────────┘                                                     │
│         PASS│    │FAIL → terug, breaking change niet toegestaan             │
│             ▼                                                                │
│  ┌─────────────────────┐                                                     │
│  │ 7. DEPENDENCY       │ ← Welke modules raakt deze wijziging?              │
│  │    IMPACT SCAN      │   Verborgen regressie buiten scope detecteren      │
│  └──────────┬──────────┘                                                     │
│         PASS│    │WARN → extra regression scope toevoegen                   │
│             ▼                                                                │
│  ┌─────────────────────┐                                                     │
│  │ 8. PROGRESSIVE      │ ← ALLE eerder geaccepteerde tests opnieuw          │
│  │    REGRESSION       │   Groeit per deliverable                           │
│  └──────────┬──────────┘                                                     │
│         PASS│    │FAIL → HARD STOP, regressie oplossen voor verder          │
│             ▼                                                                │
│  ┌─────────────────────┐                                                     │
│  │ 9. ACCEPTANCE       │ ← Registreer micro-deliverable als geaccepteerd    │
│  │    REGISTRY         │   Link naar PRD requirement ID                     │
│  │                     │   Voeg tests toe aan regressie-suite               │
│  └──────────┬──────────┘                                                     │
│             ▼                                                                │
│  [Volgende micro-deliverable]                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Sprint Completion Gate

Aan het einde van elke sprint draait een afsluitende validatie:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SPRINT COMPLETION GATE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [Alle micro-deliverables van sprint ACCEPTED]                               │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────┐                                                     │
│  │ 10. FULL REGRESSION │ ← Alles, inclusief vorige sprints                   │
│  │     SUITE           │   Hele projectbrede test suite                      │
│  └──────────┬──────────┘                                                     │
│             ▼                                                                │
│  ┌─────────────────────┐                                                     │
│  │ 11. COVERAGE REPORT │ ← Totaaloverzicht coverage gaps                     │
│  │                     │   Per module, per feature, per sprint               │
│  │                     │   Target: 80% minimum, 95% streef                  │
│  └──────────┬──────────┘                                                     │
│             ▼                                                                │
│  ┌─────────────────────┐                                                     │
│  │ 12. TRACEABILITY    │ ← PRD requirement → micro-deliverable → test        │
│  │     MATRIX          │   Welke requirements zijn gedekt?                  │
│  │                     │   Welke hebben geen test?                          │
│  └──────────┬──────────┘                                                     │
│             ▼                                                                │
│  ┌─────────────────────┐                                                     │
│  │ 13. DEAD CODE       │ ← Ongebruikte code, imports, endpoints             │
│  │     DETECTION       │   Per sprint opruimen, niet ophopen                │
│  └──────────┬──────────┘                                                     │
│             ▼                                                                │
│  ┌─────────────────────┐                                                     │
│  │ 14. SPRINT          │ ← Samenvatting voor stakeholders                    │
│  │     ACCEPTANCE      │   Coverage %, regressie status, security findings  │
│  │     REPORT          │   Traceability gaps, performance baseline          │
│  └──────────┬──────────┘                                                     │
│             ▼                                                                │
│  [Sprint DONE of BLOCKED met specifieke issues]                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Specificaties

### 1. Micro-Decomposition Engine

**Script:** `mq/workflows/common/micro-decompose.sh`

**Doel:** Breek PRD requirements automatisch op in micro-deliverables.

**Input:** PRD file (markdown met requirements)
**Output:** `micro-deliverables.json` met gestructureerde eenheden

**Schema per micro-deliverable:**
```json
{
  "id": "MD-001",
  "prd_requirement_id": "REQ-003",
  "title": "Gebruiker ziet inlogknop op landing page",
  "acceptance_criteria": [
    "Button met tekst 'Inloggen' is zichtbaar op /",
    "Button heeft correct aria-label voor accessibility",
    "Button is klikbaar en heeft hover state"
  ],
  "expected_tests": [
    "test_login_button_visible",
    "test_login_button_accessible",
    "test_login_button_clickable"
  ],
  "dependencies": [],
  "category": "functional",
  "estimated_complexity": "low",
  "security_relevant": false,
  "performance_relevant": false
}
```

**Werkwijze:**
1. Lees PRD en identificeer requirements
2. Start Claude Code sessie in decomposition-modus
3. Claude breekt elke requirement op in kleinste toetsbare eenheden
4. Elke eenheid krijgt een ID, criteria, verwachte tests, dependencies
5. Output wordt opgeslagen als `micro-deliverables.json`
6. Dependency graph wordt gevalideerd (geen circulaire dependencies)

**Decomposition-regels:**
- Een micro-deliverable is NOOIT groter dan 1 component/functie/endpoint
- Elk criterium moet in <5 minuten handmatig verifieerbaar zijn
- Elke eenheid moet onafhankelijk testbaar zijn (met mocks voor dependencies)
- Maximaal 3 acceptatiecriteria per micro-deliverable
- Bij twijfel: opsplitsen in kleinere eenheden

---

### 2. PM Acceptance Gate

**Script:** `mq/workflows/common/pm-acceptance-gate.sh`

**Doel:** Onafhankelijke inhoudelijke toetsing van een micro-deliverable tegen PRD criteria.

**Kernprincipe:** De PM Gate is NIET de bouwer. Het is een aparte Claude Code invocatie die alleen de PRD criteria kent en de diff/output beoordeelt. Separation of concerns.

**Invoer:**
- Micro-deliverable specificatie (uit `micro-deliverables.json`)
- Git diff van de wijzigingen
- Test output (als beschikbaar)
- Bestaande codebase context (relevante bestanden)

**Prompt template:**
```markdown
## PM Acceptance Review

Je bent een Product Manager die beoordeelt of een opgeleverde wijziging voldoet
aan de gestelde acceptatiecriteria. Je bent NIET de bouwer — je bent de reviewer.

### Micro-Deliverable
- ID: {md_id}
- Titel: {md_title}
- Acceptatiecriteria:
{acceptance_criteria}

### Wijzigingen
{git_diff}

### Test Output
{test_output}

### Beoordeling
Geef per acceptatiecriterium:
- VOLDOET / VOLDOET NIET / ONDUIDELIJK
- Korte onderbouwing (1 zin)

### Verdict
- ACCEPT: Alle criteria voldoen
- REJECT: Een of meer criteria voldoen niet
  - Geef specifieke feedback per falend criterium
  - Geef concrete suggestie voor verbetering

Output als JSON:
{
  "verdict": "ACCEPT|REJECT",
  "criteria_results": [...],
  "feedback": "...",
  "confidence": 0.0-1.0
}
```

**Gedrag bij REJECT:**
- Feedback wordt meegegeven aan de bouw-agent
- Telt als retry (max 3 per micro-deliverable)
- Na 3 retries: escalatie naar human reviewer
- REJECT reden wordt gelogd in acceptance registry

**Verdictdrempels:**
- `confidence >= 0.8`: verdict wordt geaccepteerd
- `confidence < 0.8`: extra validatie (dubbele invocatie of human review)

---

### 3. QA Gate

**Script:** `mq/workflows/common/qa-gate.sh`

**Doel:** Automatische kwaliteitscontrole op 4 assen: code quality, security, tests+coverage, performance.

#### 3a. Code Quality Check

**Tools:** pylint, flake8, eslint, complexity checker (radon/lizard)
**Thresholds:**
| Metric | Minimum | Target |
|--------|---------|--------|
| Pylint score | 7.0/10 | 9.0/10 |
| Cyclomatic complexity per functie | < 15 | < 10 |
| Dead imports | 0 | 0 |
| Unused variables | 0 | 0 |
| Type annotations (Python) | 80% | 95% |

**Output:** `qa-code-quality.json` met scores per file en overall

#### 3b. Security Check

**Tools:** CWE Scanner (Fase 31), bandit, safety, trivy (als Docker)
**Checks:**
- Geen nieuwe CWE findings boven MEDIUM severity
- Geen hardcoded credentials/tokens
- Geen SQL injection patterns
- Geen XSS vectors
- Dependency vulnerabilities check
- SARIF output voor integratie met dashboard

**Gedrag:** Security FAIL is een **HARD STOP**. Geen doorgang totdat alle findings zijn opgelost.

#### 3c. Test + Coverage Check

**Tools:** pytest + coverage.py / jest + istanbul
**Thresholds:**
| Metric | Minimum (hard gate) | Target (soft gate) |
|--------|--------------------|--------------------|
| Test pass rate | 100% | 100% |
| Line coverage (nieuwe code) | 80% | 95% |
| Branch coverage (nieuwe code) | 70% | 85% |
| Line coverage (totaal project) | 80% | 95% |
| Mutation testing survival | - | < 40% (stretch) |

**Berekening:** Coverage wordt gemeten over de **gewijzigde bestanden**, niet het hele project. Totale projectcoverage is een sprint-level metric.

**Coverage tracking:**
```json
{
  "micro_deliverable_id": "MD-001",
  "files_changed": ["auth/login.py", "auth/tests/test_login.py"],
  "coverage": {
    "line_coverage": 92.3,
    "branch_coverage": 85.1,
    "new_code_coverage": 95.0,
    "uncovered_lines": [45, 67, 89]
  },
  "tests": {
    "total": 12,
    "passed": 12,
    "failed": 0,
    "skipped": 0
  }
}
```

#### 3d. Performance Check

**Tools:** pytest-benchmark, custom timing checks, memory profiler
**Checks:**
- Geen response time regressie > 10% op geraakte endpoints
- Geen geheugengebruik toename > 15%
- Geen N+1 query patterns (als database betrokken)
- Baseline wordt opgeslagen per sprint voor vergelijking

**Gedrag:**
- Degradatie < 10%: PASS
- Degradatie 10-20%: WARN (log, niet blokkeren)
- Degradatie > 20%: FAIL (blokkeren)

---

### 4. Contract Verification

**Script:** Onderdeel van `qa-gate.sh`

**Doel:** Controleer dat API signatures, database schemas en interfaces backward-compatible blijven.

**Checks:**
- API endpoints: geen verwijderde routes, geen gewijzigde response schemas zonder versioning
- Database: migraties zijn reversibel (up + down), geen data verlies
- Interfaces: geen breaking changes in geexporteerde functies/klassen
- AnalysisContract (v2 API): contract integriteit behouden

**Werkwijze:**
1. Extraheer huidige API schema (OpenAPI/swagger)
2. Vergelijk met baseline schema (opgeslagen per sprint)
3. Detecteer breaking changes
4. Bij breaking change: FAIL tenzij expliciet als breaking change gemarkeerd in micro-deliverable

---

### 5. Dependency Impact Scan

**Script:** Onderdeel van `qa-gate.sh`

**Doel:** Bepaal de blast radius van een wijziging.

**Werkwijze:**
1. Analyseer gewijzigde bestanden
2. Vind alle importers/consumers van gewijzigde modules
3. Bereken impact score: hoeveel modules worden geraakt?
4. Als impact > threshold: voeg extra regression scope toe

**Impact scoring:**
| Impact | Beschrijving | Actie |
|--------|-------------|-------|
| LOW (1-3 modules) | Lokale wijziging | Standaard regression |
| MEDIUM (4-10 modules) | Cross-module impact | Uitgebreide regression |
| HIGH (>10 modules) | Architecturele impact | Full regression + human review |

---

### 6. Progressive Regression Runner

**Script:** `mq/workflows/common/regression-runner.sh`

**Doel:** Na elke geaccepteerde micro-deliverable alle eerder geaccepteerde tests opnieuw draaien.

**Acceptance Registry:** `acceptance-registry.json`
```json
{
  "sprint_id": "sprint-2026-KW27",
  "micro_deliverables": [
    {
      "id": "MD-001",
      "accepted_at": "2026-07-01T10:30:00Z",
      "tests": ["test_login_button_visible", "test_login_button_accessible"],
      "coverage": 92.3,
      "prd_requirement_id": "REQ-003",
      "git_commit": "abc123"
    }
  ],
  "regression_history": [
    {
      "run_at": "2026-07-01T11:00:00Z",
      "trigger": "MD-002 accepted",
      "tests_run": 5,
      "tests_passed": 5,
      "tests_failed": 0,
      "duration_seconds": 45
    }
  ],
  "previous_sprints": ["sprint-2026-KW26", "sprint-2026-KW25"]
}
```

**Regressie groei:**
```
MD-001 geaccepteerd → draai tests van MD-001 (5 tests)
MD-002 geaccepteerd → draai tests van MD-001 + MD-002 (12 tests)
MD-003 geaccepteerd → draai tests van MD-001 + MD-002 + MD-003 (20 tests)
...
MD-015 geaccepteerd → draai tests van MD-001..MD-015 (180 tests)
```

**Sprint-einde regressie:**
- Alle tests van huidige sprint
- Alle tests van vorige sprints (uit `previous_sprints`)
- Volledige project test suite

**Bij regressie failure:** HARD STOP. De micro-deliverable die de regressie veroorzaakte moet worden gerepareerd voordat de loop verder gaat.

---

### 7. Sprint Acceptance Report

**Script:** Onderdeel van `regression-runner.sh`

**Output:** `sprint-acceptance-report.md`

**Inhoud:**
```markdown
# Sprint Acceptance Report — KW27

## Summary
- Micro-deliverables: 15/15 accepted
- Test coverage: 91.3% (target: 95%)
- Security findings: 0 HIGH, 1 MEDIUM (resolved)
- Performance: no regressions detected
- Full regression: 342/342 tests passed

## Traceability Matrix
| PRD Requirement | Micro-Deliverables | Tests | Coverage |
|-----------------|-------------------|-------|----------|
| REQ-001 | MD-001, MD-002 | 12 | 95.2% |
| REQ-002 | MD-003, MD-004, MD-005 | 18 | 89.1% |
| REQ-003 | MD-006..MD-010 | 31 | 93.7% |

## Coverage Gaps
- REQ-004: Branch coverage 72% (under 80% minimum)
- auth/token_refresh.py: lines 45-67 uncovered

## Regression History
- Progressive regressions run: 15
- Full sprint regression: 1
- Cross-sprint regression: 1
- Total test executions: 2,340

## Quality Metrics
- Avg pylint score: 8.7/10
- Avg cyclomatic complexity: 6.2
- Dead code removed: 3 functions, 12 imports
- Contract breaks: 0
```

---

## Integratie in Ralph Loop

### Aanpassing loop-core.sh

De quality pipeline wordt geintegreerd als stappen in de bestaande Ralph loop:

```bash
# Bestaande Ralph Loop flow (32A-32D):
# while (!complete && iterations < max) {
#     inject(guardrails + progress)
#     result = execute(PROMPT.md)           # Agent bouwt
#     commit(changes)
#     evaluate(completion_criteria)
# }

# Nieuwe flow met Quality Harness (32E):
# while (!complete && iterations < max) {
#     inject(guardrails + progress)
#     task = get_next_micro_deliverable()   # ← NIEUW: uit micro-deliverables.json
#     result = execute(task.prompt)          # Agent bouwt 1 micro-deliverable
#     commit(changes)
#
#     # ── QUALITY PIPELINE START ──
#     pm_result = pm_acceptance_gate(task, diff)           # ← NIEUW
#     if (pm_result == REJECT) { continue with feedback }
#
#     qa_result = qa_gate(diff)                            # ← NIEUW
#     if (qa_result == FAIL) { continue with feedback }
#
#     regression_result = progressive_regression()          # ← NIEUW
#     if (regression_result == FAIL) { HARD STOP }
#
#     register_acceptance(task)                             # ← NIEUW
#     # ── QUALITY PIPELINE END ──
#
#     evaluate(completion_criteria)
# }
#
# sprint_completion_gate()                                  # ← NIEUW: aan het einde
```

### Aanpassing validation.sh

De bestaande `validate_criterion()` functie (die nu alleen file-existence checkt) wordt aangevuld met een semantische validatie-modus die de PM Gate aanroept voor inhoudelijke toetsing.

---

## Relatie met Bestaande Fase 32 Componenten

| Fase 32 Component | Relatie met 32E |
|---|---|
| **Dual PM Approval Gate** (al gespecificeerd) | 32E implementeert dit als `pm-acceptance-gate.sh` op micro-deliverable niveau, niet alleen op fase-niveau |
| **MultiPhaseValidationPipeline** (8-fase) | 32E vervangt de mechanische checks met inhoudelijke PM+QA gates |
| **GuardrailsService** | 32E voedt guardrails met QA findings (geleerde lessen) |
| **CompletionDetector** | 32E verrijkt completion met acceptance registry data |
| **CircuitBreaker** | 32E voegt HARD STOP triggers toe (security, regression failure) |
| **RollbackService** | 32E triggert rollback bij regressie failure |

---

## Configuratie per Workflow Type

De Quality Harness past zich aan per Ralph workflow type:

| Check | BUGFIX | CHANGES | MIGRATION | OVERNIGHT |
|-------|--------|---------|-----------|-----------|
| PM Gate | Alleen fix vs root cause | Volledig per micro-deliverable | Per migratiefase | Morning review |
| QA Code Quality | Minimaal (alleen gewijzigde code) | Volledig | Volledig | Volledig |
| QA Security | Focus op fix scope | Volledig CWE scan | HOOG: volledige scan per fase | Volledig |
| Coverage minimum | 90% (fix + regressietest) | 80% (target 95%) | 80% per migratiefase | 80% (target 95%) |
| Performance check | Alleen geraakte endpoints | Volledig | Vergelijking oud vs nieuw systeem | Volledig |
| Contract verification | N/A (fix mag niet breken) | Volledig | Migratie-specifiek (data parity) | Volledig |
| Progressive regression | Focused op bug area | Volledig groeiend | Per migratiefase groeiend | Volledig |
| Sprint completion gate | N/A (bugfix = 1 sprint) | Volledig | Per migratie milestone | Volledig |

---

## Acceptance Registry — Database Schema

```sql
CREATE TABLE acceptance_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id TEXT NOT NULL,
    micro_deliverable_id TEXT NOT NULL UNIQUE,
    prd_requirement_id TEXT NOT NULL,
    title TEXT NOT NULL,

    -- PM Gate
    pm_verdict TEXT CHECK(pm_verdict IN ('ACCEPT', 'REJECT', 'ESCALATED')),
    pm_confidence REAL,
    pm_feedback TEXT,
    pm_retries INTEGER DEFAULT 0,

    -- QA Gate
    qa_code_quality_score REAL,
    qa_security_findings INTEGER DEFAULT 0,
    qa_security_highest_severity TEXT,
    qa_test_pass_rate REAL,
    qa_line_coverage REAL,
    qa_branch_coverage REAL,
    qa_performance_status TEXT CHECK(qa_performance_status IN ('PASS', 'WARN', 'FAIL')),

    -- Contract + Impact
    contract_status TEXT CHECK(contract_status IN ('PASS', 'FAIL', 'N/A')),
    dependency_impact TEXT CHECK(dependency_impact IN ('LOW', 'MEDIUM', 'HIGH')),
    affected_modules TEXT, -- JSON array

    -- Regression
    regression_tests_run INTEGER,
    regression_tests_passed INTEGER,
    regression_duration_seconds REAL,

    -- Traceability
    git_commit TEXT,
    files_changed TEXT, -- JSON array
    tests_added TEXT, -- JSON array

    -- Timestamps
    accepted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE regression_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id TEXT NOT NULL,
    trigger_deliverable_id TEXT NOT NULL,
    trigger_type TEXT CHECK(trigger_type IN ('progressive', 'sprint_completion', 'cross_sprint')),
    tests_run INTEGER,
    tests_passed INTEGER,
    tests_failed INTEGER,
    failures TEXT, -- JSON array of failed test names
    duration_seconds REAL,
    run_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trigger_deliverable_id) REFERENCES acceptance_registry(micro_deliverable_id)
);

CREATE TABLE sprint_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id TEXT NOT NULL UNIQUE,
    total_deliverables INTEGER,
    accepted_deliverables INTEGER,
    total_coverage REAL,
    total_tests INTEGER,
    security_findings_resolved INTEGER,
    performance_regressions INTEGER,
    contract_breaks INTEGER,
    dead_code_removed INTEGER,
    report_markdown TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_registry_sprint ON acceptance_registry(sprint_id);
CREATE INDEX idx_registry_prd ON acceptance_registry(prd_requirement_id);
CREATE INDEX idx_regression_sprint ON regression_history(sprint_id);
```

---

## KW Planning (Week 191-194)

### KW27 (Week 191): Micro-Decomposition + PM Gate

**Deliverables:**
- `mq/workflows/common/micro-decompose.sh` — PRD decomposition engine
- `mq/workflows/common/pm-acceptance-gate.sh` — PM agent review gate
- `acceptance-registry.json` schema + SQLite init
- Micro-deliverable JSON schema definitie
- PM prompt template geoptimaliseerd en getest
- Integratie test: PRD → decompose → build 1 deliverable → PM review

**Effort:** 30 uur

### KW28 (Week 192): QA Gate (4 assen)

**Deliverables:**
- `mq/workflows/common/qa-gate.sh` — Unified QA gate met 4 sub-checks
- Code quality checker (pylint/eslint + complexity + dead code)
- Security checker (CWE Scanner Fase 31 integratie + dependency audit)
- Test + coverage enforcer (80% hard gate, 95% target)
- Performance baseline + regression detector
- Contract verification (API schema + DB migration checks)
- Integratie test: build deliverable → QA pipeline → verdicts

**Effort:** 40 uur

### KW29 (Week 193): Progressive Regression + Impact Scan

**Deliverables:**
- `mq/workflows/common/regression-runner.sh` — Progressive + sprint regression
- Acceptance registry SQLite database + CRUD operaties
- Dependency impact scanner
- Regressie groei mechanisme (per-deliverable accumulation)
- Sprint-einde full regression suite
- Cross-sprint regression (met previous_sprints)
- Integratie test: 5 deliverables → groeiende regressie → sprint completion

**Effort:** 30 uur

### KW30 (Week 194): Traceability + Sprint Reports + Loop Integratie

**Deliverables:**
- Traceability matrix generator (PRD → deliverable → test)
- Dead code detection (per sprint)
- Sprint acceptance report generator
- Updates aan `loop-core.sh` — quality pipeline integratie
- Updates aan `validation.sh` — semantische validatie modus
- E2E test: volledige sprint cyclus door Ralph loop met quality harness
- Documentatie updates

**Effort:** 20 uur

---

## Success Criteria

| Metric | Target |
|--------|--------|
| PM Gate false acceptance rate | < 5% |
| QA Gate catch rate (bekende issues) | > 90% |
| Progressive regression coverage | 100% (alle geaccepteerde tests) |
| Sprint coverage (nieuw code) | >= 80% (target 95%) |
| Security findings doorgelaten | 0 HIGH, 0 CRITICAL |
| Contract breaks doorgelaten | 0 |
| Mean time per quality pipeline run | < 3 minuten (exclusief full regression) |
| Sprint completion gate duration | < 15 minuten |
| Traceability coverage | 100% requirements gelinkt aan tests |

---

## Risico's en Mitigatie

| Risico | Impact | Mitigatie |
|--------|--------|----------|
| Pipeline te traag (veel cycles) | Agents wachten lang | Parallel execution van QA sub-checks, caching van baseline data |
| PM Gate hallucineert ACCEPT | Foute code door | Confidence threshold + steekproef human review |
| Progressive regression te lang bij grote sprints | Sprint vertraagd | Smart regression: alleen geraakte test suites, niet alles |
| Coverage target 95% onhaalbaar | Frustratie, workarounds | 80% hard gate, 95% soft target met tracking |
| LLM kosten per PM review | Budget overschrijding | Gebruik Max plan (geen API kosten), cache prompts |

---

## Documentatie Verwijzingen

| Document | Beschrijving |
|----------|-------------|
| [fase-32-ralph-wiggum-loop.md](fase-32-ralph-wiggum-loop.md) | Ralph Loop + Dual PM Gate spec (32A-32D) |
| [mq-ralph-wiggum-integration-plan.md](../../mq-ralph-wiggum-integration-plan.md) | mq + Ralph integratie plan |
| [fase-31-cwe-security-scanners.md](fase-31-cwe-security-scanners.md) | CWE Scanner Suite (security gate dependency) |

---

## Changelog

| Datum | Wijziging |
|-------|-----------|
| 2026-02-01 | Initieel document — Fase 32E specificatie |
