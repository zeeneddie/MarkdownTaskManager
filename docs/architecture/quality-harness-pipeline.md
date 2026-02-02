# Quality Harness Pipeline Architecture

**Status:** PLANNED (Fase 32E — KW27-30 [w191-194])
**Parent:** [Platform Architecture](../unified-architecture-diagram.md)
**Datum:** 2026-02-01

---

## Overzicht

De Quality Harness Pipeline valideert elke micro-deliverable onafhankelijk via drie gates (PM, QA, Regression) voordat deze als ACCEPT wordt geregistreerd. Dit elimineert false completions en maakt overnight runs betrouwbaar en meetbaar.

```
+===============================================================================+
|  QUALITY HARNESS PIPELINE (per micro-deliverable)                             |
+===============================================================================+
|                                                                               |
|  PRD ──► DECOMPOSE ──► BUILD ──► PM GATE ──► QA GATE ──► REGRESSION ──► REG. |
|          (micro-       (Ralph    (Claude     (7 axes)    (progressive)  (SQLite|
|           deliverables) Loop)     review)                               DB)   |
|                           ▲          │           │            │                |
|                           │       REJECT      REJECT        FAIL              |
|                           └──────────┴───────────┴────────────┘               |
|                                                                               |
+===============================================================================+
```

---

## Component Architectuur

### 1. Micro-Decompose Engine

**Script:** `mq/workflows/common/micro-decompose.sh`

Breekt PRD op in kleinste toetsbare eenheden via Claude Code.

```
decompose_prd()
    │
    ├── Lees PRD bestand
    ├── Bouw decomposition prompt (regels + JSON schema)
    ├── claude -p "${prompt}" --output-format json
    ├── Parse JSON → micro_deliverables[]
    ├── validate_dependencies() → DFS cycle detection (Python)
    └── Schrijf output naar micro-deliverables.json

Elke micro-deliverable bevat:
    ├── id: "MD-001"
    ├── prd_requirement_id: "REQ-001"
    ├── title: beschrijving
    ├── acceptance_criteria: [max 3, toetsbaar]
    ├── expected_tests: [testnamen]
    ├── dependencies: ["MD-000", ...]
    ├── category: functional|api|data|security|performance|ui|integration|documentation
    ├── estimated_complexity: low|medium|high
    ├── security_relevant: bool
    └── performance_relevant: bool
```

**Hulpfuncties:**
- `get_next_micro_deliverable()` — Eerste deliverable met alle dependencies ACCEPT
- `get_decomposition_progress()` — JSON met total/accepted/remaining/percent

### 2. PM Acceptance Gate

**Script:** `mq/workflows/common/pm-acceptance-gate.sh`

Onafhankelijke PM review: een **aparte** Claude Code invocatie (niet de bouwer) die de diff beoordeelt tegen PRD acceptatiecriteria.

```
pm_acceptance_review()
    │
    ├── Extract micro-deliverable spec uit JSON
    ├── git diff HEAD~1 (wijzigingen ophalen)
    ├── Lees test output (.marqed/test-output.txt)
    ├── build_pm_prompt() → gestructureerde review prompt
    ├── run_pm_review() → claude -p "${prompt}" --output-format json
    ├── Parse verdict: ACCEPT / REJECT
    ├── Check confidence ≥ 0.8
    ├── log_pm_review() → SQLite pm_reviews tabel
    │
    ├── ACCEPT (confidence ≥ 0.8) → return 0
    ├── REJECT → store_pm_feedback() → return 1 (terug naar build)
    └── ESCALATED (max 3 retries) → return 2
```

**Review output:**
```json
{
  "verdict": "ACCEPT|REJECT",
  "criteria_results": [
    {"criterion": "...", "status": "VOLDOET|VOLDOET_NIET|ONDUIDELIJK", "reasoning": "..."}
  ],
  "feedback": "Samenvatting",
  "confidence": 0.0-1.0,
  "improvements": ["suggestie 1", "suggestie 2"]
}
```

### 3. QA Gate

**Script:** `mq/workflows/common/qa-gate.sh`

7-assige kwaliteitscontrole met configureerbare thresholds.

```
qa_full_gate()
    │
    ├── 1. qa_check_code_quality()
    │       ├── pylint score (hard gate: ≥ 7.0, target: ≥ 8.5)
    │       ├── radon complexity (max cyclomatic: 15)
    │       └── autoflake dead imports
    │
    ├── 2. qa_check_security()          ◄── HARD STOP op HIGH/CRITICAL
    │       ├── bandit scan
    │       ├── Credential pattern detection (API keys, passwords)
    │       ├── SQL injection patterns
    │       └── safety dependency audit
    │
    ├── 3. qa_check_tests_coverage()
    │       ├── pytest execution
    │       ├── coverage run (hard gate: ≥ 80%, target: ≥ 95%)
    │       └── Branch coverage tracking
    │
    ├── 4. qa_check_performance()
    │       ├── Benchmark comparison vs baseline
    │       ├── WARN threshold: 10% degradatie
    │       └── FAIL threshold: 20% degradatie
    │
    ├── 5. qa_check_contracts()
    │       ├── API route signature changes
    │       └── DB migration reversibility
    │
    ├── 6. qa_check_dependency_impact()
    │       ├── Import analysis (wie importeert gewijzigde modules)
    │       └── Impact: LOW (<4 dependents) | MEDIUM (4-10) | HIGH (>10)
    │
    └── 7. qa_check_dead_code()
            ├── autoflake (unused imports)
            └── vulture (unreachable code)
```

### 4. Progressive Regression Runner

**Script:** `mq/workflows/common/regression-runner.sh`

Na elke geaccepteerde micro-deliverable worden **alle** eerder geaccepteerde tests opnieuw gedraaid.

```
run_progressive_regression()
    │
    ├── Query acceptance_registry → alle ACCEPT deliverables
    ├── Verzamel tests_added van elke deliverable
    ├── Voer volledige test suite uit
    ├── log_regression() → SQLite regression_history
    │
    ├── 100% pass → return 0
    └── Failure → HARD STOP, return 1

run_sprint_regression()
    │
    ├── Volledige project test suite (pytest)
    ├── Coverage report genereren
    ├── generate_sprint_report() → Markdown rapport met:
    │       ├── Sprint samenvatting
    │       ├── Deliverable status overzicht
    │       ├── Coverage rapport
    │       ├── Security samenvatting
    │       ├── Regressie historie
    │       └── Traceability matrix (MD-ID → Tests → Status)
    └── Opslaan in sprint_reports tabel
```

---

## Acceptance Registry (SQLite)

Centrale database voor tracking en traceability.

```
acceptance_registry
    ├── sprint_id, micro_deliverable_id, prd_requirement_id
    ├── pm_verdict, pm_confidence, pm_feedback, pm_retries
    ├── qa_code_quality_score, qa_security_findings
    ├── qa_test_pass_rate, qa_line_coverage, qa_branch_coverage
    ├── qa_performance_status, contract_status
    ├── dependency_impact, affected_modules
    ├── regression_tests_run, regression_tests_passed
    ├── git_commit, files_changed, tests_added
    └── accepted_at

pm_reviews
    ├── micro_deliverable_id, verdict, confidence
    ├── feedback, retry_count, reviewed_at

qa_reviews
    ├── micro_deliverable_id, check_type, status
    ├── score, details, reviewed_at

regression_history
    ├── sprint_id, trigger_deliverable_id, trigger_type
    ├── tests_run, tests_passed, tests_failed
    ├── failures, duration_seconds, run_at

sprint_reports
    ├── sprint_id, total_deliverables, accepted_deliverables
    ├── total_coverage, total_tests
    ├── security_findings_resolved, performance_regressions
    ├── contract_breaks, dead_code_removed
    └── report_markdown
```

---

## Quality Thresholds

| Check | Hard Gate | Target | HARD STOP |
|-------|-----------|--------|-----------|
| PM Confidence | ≥ 0.8 | ≥ 0.95 | Nee (retry tot max 3) |
| Code Quality (pylint) | ≥ 7.0/10 | ≥ 8.5/10 | Nee |
| Security HIGH/CRITICAL | 0 findings | 0 findings | **Ja** |
| Test Coverage (line) | ≥ 80% | ≥ 95% | Nee |
| Performance Degradatie | < 20% | < 5% | Bij > 20% |
| Progressive Regression | 100% pass | 100% pass | **Ja** |

---

## Configuratie per Workflow Type

| Setting | BUGFIX | CHANGES | MIGRATION | OVERNIGHT |
|---------|--------|---------|-----------|-----------|
| PM retries | 2 | 3 | 3 | 3 |
| Coverage hard gate | 70% | 80% | 80% | 80% |
| Security gate | Ja | Ja | **Strict** | Ja |
| Performance gate | Nee | Ja | Ja | Ja |
| Contract check | Nee | Ja | **Strict** | Ja |
| Sprint regression | Na fix | Na sprint | Na fase | Na sprint |

---

## Verwachte Impact

| Metric | Huidige situatie | Na implementatie |
|--------|-----------------|-----------------|
| False completion rate | 15-20% | < 3% |
| Overnight reliability | ~60% | > 90% |
| Coverage tracking | Geen | Per-deliverable |
| PRD traceability | Handmatig | Geautomatiseerd |
| Security regressions | Onbekend | 0 (hard stop) |

---

## Gerelateerde Documenten

- [Fase 32E Specificatie](../roadmap/phases/fase-32e-quality-harness.md) — Volledige specificatie
- [Fase 32 Ralph Wiggum](../roadmap/phases/fase-32-ralph-wiggum-loop.md) — Autonomous loop (consumer van quality harness)
- [Security Scanner Pipeline](security-scanner-pipeline.md) — Security check details
- [Quality Gates](quality-gates.md) — Bestaande 42-regel quality gates

---

*Week 162 (2026-02-01) — Fase 32E PLANNED (KW27-30)*
