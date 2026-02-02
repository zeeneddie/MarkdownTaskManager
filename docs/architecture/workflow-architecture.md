# Workflow Architecture — mq CLI Workflows

**Status:** ACTIVE (4 workflows) + PLANNED (OVERNIGHT)
**Parent:** [Platform Architecture](../unified-architecture-diagram.md)
**Datum:** 2026-02-01

---

## Overzicht

Het mq CLI systeem biedt 5 workflow types, elk met eigen fasen, agent-toewijzing en risk profile. Alle workflows delen een common layer (loop-core, validation, progress tracking) en worden aangestuurd via `platform-api.sh` als bridge naar de backend.

```
$ mq {bugfix|changes|migration|analyze|overnight}
         │
         v
+-------------------+
| marqed-{type}.sh  |
+-------------------+
         │
         ├── source common/loop-core.sh        (checkpoints, task sync)
         ├── source common/validation.sh        (fase validatie)
         ├── source common/progress-tracking.sh (voortgang)
         │
         ├── platform-api.sh                    (CLI → API bridge)
         │       ├── create_workflow()
         │       ├── update_task_status()
         │       ├── lookup_existing_knowledge()
         │       └── run_security_scan()
         │
         └── claude --print --model {model}     (per fase)
```

---

## Workflow Types

### 1. BUGFIX (`marqed-bugfix.sh`)

**7 fasen — Sequentieel — Focus: minimale fix, geen regressie**

| Fase | Agent(s) | Duur | Functie |
|------|----------|------|---------|
| 1. Bug Reproduction | Betty | 1-2h | Reproduceer de bug met test case |
| 2. Root Cause Analysis | Betty + Quinn | 2-4h | Identificeer oorzaak |
| 3. Fix Implementation | Felix + Marcus | 2-6h | Minimale fix implementeren |
| 4. Unit Testing | Tessa | 1-2h | Tests voor de fix |
| 5. Integration Testing | Tessa + Quinn | 1-2h | Geen side effects |
| 6. Code Review | Quinn | 0.5-1h | Kwaliteitscontrole |
| 7. Documentation | Diana | 0.5-1h | Changelog / release notes |

**Platform Services:** CWE Scanner, Testing Services, Quality Gates

### 2. CHANGES (`marqed-changes.sh`)

**8 fasen — Parallel optioneel — Focus: feature oplevering**

| Fase | Agent(s) | Duur | Functie |
|------|----------|------|---------|
| 1. Requirements Analysis | Peter | 2-4h | PRD analyse, stories genereren |
| 2. Design & Architecture | Felix + Vicky | 3-6h | Technisch ontwerp |
| 3. Implementation | Felix + Marcus | 8-24h | Code schrijven |
| 4. Unit Testing | Tessa | 2-4h | Unit tests |
| 5. Integration Testing | Tessa + Quinn | 2-4h | Integratie tests |
| 6. Documentation | Diana | 1-2h | API docs, user docs |
| 7. Code Review | Quinn | 1-2h | Quality review |
| 8. Deployment Preparation | Paul | 1-2h | Release voorbereiding |

**Platform Services:** Deep Extraction, FP Methodology, Hierarchical Story Extraction, Quality Gates

### 3. MIGRATION (`marqed-migration.sh`)

**9 fasen — Strangler Fig Pattern — Focus: data + code migratie**

| Fase | Agent(s) | Duur | Functie |
|------|----------|------|---------|
| 1. Analysis & Planning | Miguel + Peter | 8h | Migratieplan, risk matrix |
| 2. Infrastructure Setup | Felix | 4h | Target omgeving opzetten |
| 3. Database Migration | Miguel | 24h | Schema + data migratie |
| 4. Core Application Migration | Miguel + Felix | 120h | Code migratie |
| 5. Testing & Validation | Tessa + Quinn | 40h | Functionele + data validatie |
| 6. Security & Compliance | Quinn | 24h | Security audit |
| 7. Performance Optimization | Felix + Eliza | 16h | Performance tuning |
| 8. Documentation | Diana | 8h | Migratiedocumentatie |
| 9. Deployment Preparation | Paul | 8h | Cutover planning |

**Platform Services:** Brown Paper (6-fase), Business Rule Extractors (12x), Migration Enhanced (7-fase), Dual-Run Comparison, Data Lineage

### 4. ANALYZE (`marqed-analyze.sh`)

**6 fasen — Quick/Standard/Deep modes — Focus: code analyse**

| Fase | Agent(s) | Duur | Functie |
|------|----------|------|---------|
| 1. Tech Stack Detection | Miguel | Auto | Framework/taal detectie |
| 2. Automated Analysis | Quinn + Felix | Varies | Static analysis tools |
| 3. Deep Code Analysis | Quinn | Varies | Architectuur, complexiteit |
| 4. Security & Compliance | Quinn | Varies | CWE + compliance scan |
| 5. Prioritize Findings | Peter + Eliza | 2-4h | Prioritering op impact |
| 6. Generate Reports | Diana | 1-2h | Analyse rapport |

**Output opties:**
- A. Analysis Report (default)
- B. Generate Migration PRD (`--generate-migration-prd`)
- C. Create Backlog PRDs (`--create-backlog`)

**Platform Services:** Hybrid Static-LLM Pipeline, CWE Suite (96%), Compliance (6 frameworks), DevOps Analysis (7 svc), CiRA Causality

### 5. OVERNIGHT (`marqed-overnight.sh`) [FASE 32]

**Autonomous — Ralph Wiggum Loop — Focus: onbeheerd nachtwerk**

| Stap | Timing | Functie |
|------|--------|---------|
| PRP Framework | Avond | Research → Requirements → Blueprint → PROMPT |
| PM Gate 1 | Avond (synchroon) | PRP + budget goedkeuring |
| Ralph Loop | Nacht (8+ uur) | Autonomous execution met checkpoints |
| Morning Report | Ochtend | Samenvatting, kosten, architectuurwijzigingen |
| Quality Harness | Ochtend | PM Gate + QA Gate + Progressive Regression |
| PM Gate 2 | Ochtend (asynchroon) | Kwaliteitsreview, doorgaan of rollback |

**Platform Services:** Ralph Loop, Quality Harness, PM Gate, QA Gate, Progressive Regression, GuardrailsService

→ Details: [Ralph Wiggum Architecture](ralph-wiggum-autonomous-loop.md)

---

## Common Layer

### loop-core.sh

| Functie | Beschrijving |
|---------|-------------|
| `check_tasks_complete()` | Controleert of alle taken in een fase klaar zijn |
| `get_next_task()` | Bepaalt volgende taak op basis van volgorde + dependencies |
| `save_checkpoint()` | Slaat workflow state op voor resume |
| `load_checkpoint()` | Hervat workflow na onderbreking |
| `diagnose_failure()` | Analyseert waarom een fase faalde |
| `spawn_parallel_sessions()` | Start parallelle Claude sessies (CHANGES workflow) |
| `sync_tasks_to_prd()` | Synchroniseert taakstatus terug naar PRD |

### validation.sh

Mechanische validatie per fase (bestandsbestaan, test counts, recente commits).

> **Let op:** Huidige validatie is puur mechanisch. Semantische validatie (PRD match) wordt toegevoegd via het Quality Harness (Fase 32E).

### progress-tracking.sh

Voortgangsregistratie per fase en taak, inclusief tijdregistratie.

---

## Gerelateerde Documenten

- [Platform Architecture](../unified-architecture-diagram.md) — High-level overzicht
- [Ralph Wiggum Architecture](ralph-wiggum-autonomous-loop.md) — OVERNIGHT workflow details
- [Quality Harness Pipeline](quality-harness-pipeline.md) — PM/QA gates na elke deliverable
- [Workflow Separation Plan](workflow-separation-plan.md) — Brown Paper / Migration / Quality scheiding
- [Project Workflows Standard](project-workflows-standard.md) — Gestandaardiseerde workflow patronen

---

*Week 162 (2026-02-01)*
