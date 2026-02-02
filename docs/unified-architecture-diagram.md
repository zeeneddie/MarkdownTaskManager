# MarQed.ai Platform Architecture

**Auteur**: Felix (Feature Architect)
**Datum**: 2026-02-01
**Versie**: 2.0
**Status**: Goedgekeurd

---

## Systeem Overzicht

MarQed.ai is een multi-stack AI agent platform voor geautomatiseerde softwareontwikkeling, migratie en kwaliteitsborging.

| Metric | Waarde |
|--------|--------|
| **API Endpoints** | 800+ (incl. v2 API + Confucius) |
| **Backend Services** | 290+ |
| **Core Agents** | 11 (cross-stack) |
| **Workflow Types** | 5 (BUGFIX, CHANGES, MIGRATION, ANALYZE, OVERNIGHT) |
| **Tests** | 2.700+ (97,8% pass rate) |
| **Database Migraties** | 75 (Alembic) |
| **Dashboards** | 40 |
| **LLM Providers** | 7 (CLI-first: Claude, + Ollama, Groq, Alibaba, Gemini, OpenAI, Anthropic API) |
| **Security Scanners** | CWE Suite + Injection + FN Detection (96% Top 25 coverage) |
| **Compliance Frameworks** | 6 (NEN7510, ISO27001, GDPR, HIPAA, SOC2, PCI-DSS) |

---

## 6-Lagen Architectuur

```
+===============================================================================================+
|                                                                                               |
|                    MARQED.AI UNIFIED PLATFORM ARCHITECTURE                                    |
|                    Week 162 (2026-02-01)                                                       |
|                                                                                               |
+===============================================================================================+
|                                                                                               |
|  LAAG 0: GEBRUIKERSINTERFACE                                                                  |
|  ===========================                                                                  |
|                                                                                               |
|  +---------------------------+              +------------------------------------------+      |
|  |  DEVELOPER (Terminal)     |              |  KLANT (Browser)                         |      |
|  |                           |              |                                          |      |
|  |  $ mq bugfix              |              |  Hub Portal (40 dashboards)              |      |
|  |  $ mq changes             |              |  Customer Portal (Feature Requests)      |      |
|  |  $ mq migration           |              |  Progress Dashboard (Real-time)          |      |
|  |  $ mq analyze             |              |                                          |      |
|  |  $ mq overnight  [FASE32] |              |                                          |      |
|  +------------|--------------+              +------------------|-----------------------+      |
|               |                                                |                              |
+===============|================================================|==============================+
|               |                                                |                              |
|  LAAG 1: CLI & WEB LAYER                                                                      |
|  =======================                                                                      |
|               |                                                |                              |
|  +------------v--------------+              +------------------v-----------------------+      |
|  |  mq CLI LAYER             |              |  WEB LAYER                               |      |
|  +---------------------------+              +------------------------------------------+      |
|  |  marqed-bugfix.sh         |              |  Hub Portal (localhost:8000/)             |      |
|  |  marqed-changes.sh        |              |  Customer Portal (Strapi CMS)            |      |
|  |  marqed-migration.sh      |              |  Progress Dashboard [V1]                 |      |
|  |  marqed-analyze.sh        |              |                                          |      |
|  |  marqed-overnight.sh [32] |              |                                          |      |
|  |         |                 |              +------------------+-----------------------+      |
|  |  +------v------+          |                                 |                              |
|  |  | platform-   |          |                                 |                              |
|  |  | api.sh      |          |                                 |                              |
|  |  +------+------+          |                                 |                              |
|  +---------|--|--------------+                                 |                              |
|            |  +------------------------------------------------+                              |
|            |                           |                                                      |
+============|===========================|======================================================+
|            |                           |                                                      |
|  LAAG 2: API GATEWAY (FastAPI - 800+ endpoints)                                               |
|  ==============================================                                               |
|            |                           |                                                      |
|  +---------v---------------------------v-----------------------------------------------+      |
|  |                           MarQed.ai API Gateway                                     |      |
|  |                           localhost:8000/api/                                       |      |
|  +-------------------------------------------------------------------------------------+      |
|  |                                                                                      |     |
|  |  WORKFLOW API    | KNOWLEDGE API  | VALIDATION API | SECURITY API  | EXTRACTION API  |     |
|  |  POST workflow/  | POST lookup    | POST visual-   | POST scan     | POST start      |     |
|  |  GET  status     | GET  patterns  |   regression   | GET  report   | POST extract    |     |
|  |  PATCH tasks     |                | POST perf.     |               |                 |     |
|  |                                                                                      |     |
|  +-------------------------------------------------------------------------------------+      |
|                          |                                                                    |
+==========================|====================================================================+
|                          |                                                                    |
|  LAAG 3: AGENT ARCHITECTUUR (11 Core + Stack Templates)                                       |
|  ======================================================                                       |
|                          |                                                                    |
|  +-----------------------------------------------------------------------+                    |
|  |  CORE AGENTS                                                          |                    |
|  |  +--------+  +--------+  +--------+  +--------+  +--------+          |                    |
|  |  | Felix  |  | Quinn  |  | Betty  |  | Eliza  |  | Diana  |          |                    |
|  |  | Arch.  |  | Quality|  | Bugs   |  | Estim. |  | Docs   |          |                    |
|  |  +--------+  +--------+  +--------+  +--------+  +--------+          |                    |
|  |  +--------+  +--------+  +--------+  +--------+  +--------+          |                    |
|  |  | Marcus |  | Tessa  |  | Miguel |  | Peter  |  | Paul   |          |                    |
|  |  | Maint. |  | Test   |  | Migrate|  | Product|  | Plan   |          |                    |
|  |  +--------+  +--------+  +--------+  +--------+  +--------+          |                    |
|  |  + Vicky (Visual Designer)                                            |                    |
|  |                                                                       |                    |
|  |  ORCHESTRATION                                                        |                    |
|  |  +--------------------+  +--------------------+  +------------------+ |                    |
|  |  | Confucius          |  | Ralph Wiggum Loop  |  | Quality Harness  | |                    |
|  |  | Orchestrator       |  | (Autonomous/       |  | PM Gate + QA     | |                    |
|  |  | (Central Routing)  |  |  Overnight) [F32]  |  | Gate [F32E]      | |                    |
|  |  +--------------------+  +--------------------+  +------------------+ |                    |
|  |                                                                       |                    |
|  |  STACK TEMPLATES: Python | TypeScript | .NET | Java | Go | Rust       |                    |
|  +-----------------------------------------------------------------------+                    |
|                          |                                                                    |
+==========================|====================================================================+
|                          |                                                                    |
|  LAAG 4: BACKEND SERVICES (290+ Services)                                                     |
|  ========================================                                                     |
|                          |                                                                    |
|  +-----------------------------------------------------------------------+                    |
|  |                                                                       |                    |
|  |  ANALYSIS            | EXTRACTION           | KNOWLEDGE              |                    |
|  |  Brown Paper (6-fase)| Deep Extraction      | Tech Stack KB          |                    |
|  |  CWE Scanner Suite   | Hierarchical Story   | Experience Store       |                    |
|  |  FP Methodology      | Business Rules (12x) | Continuous Learning    |                    |
|  |  Confucius Orch.     | CiRA Causality       | Workflow Task Store    |                    |
|  |  Stability (8 cat)   | Static Analysis      |                        |                    |
|  |  DevOps Analysis (7) | NFR Detector          |                        |                    |
|  |                      |                       |                        |                    |
|  |  TESTING             | VALIDATION            | MIGRATION              |                    |
|  |  Characterization    | Visual Regression     | Migration Enhanced     |                    |
|  |  Dual-Run Comparison | Performance Baseline  | Strangler Fig          |                    |
|  |  Code Coverage       | Quality Gates (42)    | Library Mapping        |                    |
|  |  Dead Code Detector  | Compliance (6 fw)     | Data Lineage           |                    |
|  |                      |                       |                        |                    |
|  |  SECURITY [F31-42]   | QUALITY HARNESS [32E] |                        |                    |
|  |  CWE Top 25 (96%)   | PM Acceptance Gate    |                        |                    |
|  |  Injection (13 cat) | QA Gate (7 axes)      |                        |                    |
|  |  FN Detection (4 sc)| Progressive Regression|                        |                    |
|  |  Taint Tracking     | Micro-Decompose       |                        |                    |
|  |                      |                       |                        |                    |
|  +-----------------------------------------------------------------------+                    |
|                          |                                                                    |
+==========================|====================================================================+
|                          |                                                                    |
|  LAAG 5: LLM PROVIDER LAYER (CLI-First + 7 API Providers)                                    |
|  ========================================================                                    |
|                          |                                                                    |
|  +-----------------------------------------------------------------------+                    |
|  |  CLI-FIRST (mq Workflows)                     PRIORITEIT: PRIMAIR    |                    |
|  |  +--------------------------------------------------------------------+                   |
|  |  |  claude --print --model {haiku|sonnet|opus}                        |                   |
|  |  |  Max Subscription = voorspelbare kosten, hogere rate limits        |                   |
|  |  +--------------------------------------------------------------------+                   |
|  |                                                                       |                    |
|  |  API PROVIDERS (Platform Services)            PRIORITEIT: SECUNDAIR   |                    |
|  |  +--------+  +--------+  +--------+  +--------+  +--------+          |                    |
|  |  | Ollama |  | Groq   |  | Alibaba|  | Gemini |  | OpenAI |          |                    |
|  |  | (Local)|  | (Fast) |  | (Qwen) |  | (Google|  | (GPT)  |          |                    |
|  |  +--------+  +--------+  +--------+  +--------+  +--------+          |                    |
|  |  + Anthropic API (Fallback)                                           |                    |
|  +-----------------------------------------------------------------------+                    |
|                          |                                                                    |
+==========================|====================================================================+
|                          |                                                                    |
|  LAAG 6: DATA & OBSERVABILITY                                                                 |
|  ============================                                                                 |
|                          |                                                                    |
|  +-----------------------------------------------------------------------+                    |
|  |                                                                       |                    |
|  |  DATABASES                          | OBSERVABILITY                   |                    |
|  |  PostgreSQL (75 migraties)          | CCTrace (thinking blocks)       |                    |
|  |  ChromaDB (Vector Store)            | OTLP/Langfuse [FASE 60]        |                    |
|  |  Redis (Celery Queue)               | Self-Evolution (5 collections)  |                    |
|  |  JSON Files (~/.marqed/ task state) | Token Cache Metrics             |                    |
|  |  SQLite (Acceptance Registry) [32E] | Claude-Mem (11 auto-tags)       |                    |
|  |                                                                       |                    |
|  +-----------------------------------------------------------------------+                    |
|                                                                                               |
+===============================================================================================+
```

---

## Workflow Types

| # | Workflow | Script | Fasen | Patroon | Primaire Agents |
|---|---------|--------|-------|---------|-----------------|
| 1 | **BUGFIX** | `marqed-bugfix.sh` | 7 | Sequentieel | Betty → Quinn → Felix → Tessa → Diana |
| 2 | **CHANGES** | `marqed-changes.sh` | 8 | Parallel optioneel | Peter → Felix → Tessa → Quinn → Diana |
| 3 | **MIGRATION** | `marqed-migration.sh` | 9 | Strangler Fig | Miguel → Peter → Felix → Quinn → Diana |
| 4 | **ANALYZE** | `marqed-analyze.sh` | 6 | Quick/Standard/Deep | Quinn → Felix → Peter → Diana |
| 5 | **OVERNIGHT** | `marqed-overnight.sh` | Autonomous | Ralph Wiggum Loop | PRP → Ralph Loop → Morning Report |

→ Details: [Workflow Architecture](architecture/workflow-architecture.md)

---

## Quality Pipeline

Elke micro-deliverable doorloopt een quality pipeline voordat deze als ACCEPT wordt geregistreerd:

```
PRD ──► Micro-Decompose ──► Build (Ralph Loop) ──► PM Gate ──► QA Gate ──► Regression ──► ACCEPT
                                                      │            │            │
                                                   REJECT       REJECT      FAIL
                                                      │            │            │
                                                      └────────────┴────────────┘
                                                                   │
                                                            Terug naar Build
```

| Gate | Functie | Hard Gate |
|------|---------|-----------|
| **PM Acceptance Gate** | Review diff vs PRD acceptatiecriteria | Confidence ≥ 0.8 |
| **QA Gate — Code Quality** | pylint score | ≥ 7.0/10 |
| **QA Gate — Security** | HIGH/CRITICAL findings | 0 findings |
| **QA Gate — Tests + Coverage** | pytest + coverage | ≥ 80% (target 95%) |
| **QA Gate — Performance** | Benchmark degradatie | < 20% |
| **QA Gate — Contracts** | API/DB backward compat | PASS |
| **QA Gate — Dependencies** | Blast radius analyse | LOW/MEDIUM |
| **QA Gate — Dead Code** | Ongebruikte imports/code | Geen nieuwe |
| **Progressive Regression** | Alle eerder geaccepteerde tests | 100% pass |

→ Details: [Quality Harness Pipeline](architecture/quality-harness-pipeline.md)
→ Specificatie: [Fase 32E](roadmap/phases/fase-32e-quality-harness.md)

---

## Security Scanner Pipeline

```
Source Code ──► CWE Scanner Suite ──► Injection Scanners ──► FN Detection ──► Report
                    (Fase 31)            (Fase 41)            (Fase 42)
                  OpenGrep/Bandit       13 categorieën        AST Taint Tracking
                  Trivy/Custom ASP      79 regels             4 scanners
                  288 findings          484 tests             468 tests
                                        96% Top 25           FN: 5% → <2%
```

Geplande uitbreidingen:
- **Fase 34**: Advanced Error Detectors (Deadlock + Performance)
- **Fase 35**: Data Integrity Scanners (Race Conditions + Resource Lifecycle)
- **Fase 36**: Logic & Crypto Scanner (Crypto + Control Flow + Boolean)
- **Fase 37**: Security Agent Integration (6 touchpoints, 130 tests)
- **Fase 38-40**: Memory Safety, ML Novel Vulnerability, Hybrid FP Reduction

→ Details: [Security Scanner Pipeline](architecture/security-scanner-pipeline.md)

---

## Sub-Architectuur Documenten

### Core Platform

| Document | Domein | Status |
|----------|--------|--------|
| [Quality Gates](architecture/quality-gates.md) | 42 validatieregels, CI/CD integratie | COMPLETE |
| [LLM Council](architecture/llm-council.md) | Multi-model besluitvorming, voting | COMPLETE |
| [Provider Registry](architecture/provider-registry.md) | 7 LLM providers, routing, fallback | COMPLETE |
| [Kanban System](architecture/kanban-system.md) | 9-lane kanban, markdown-first | COMPLETE |
| [Observability Layer](architecture/observability-layer.md) | CCTrace, metrics, monitoring | COMPLETE |
| [Standards System](architecture/standards-system.md) | Agent OS, coding standards | COMPLETE |
| [Validation Framework](architecture/validation-framework.md) | 8-fase validation pipeline | PLANNED |
| [Context Engineering](architecture/context-engineering-architecture.md) | Token-efficient agent workflows, PIV loop | COMPLETE |

### Agent & Orchestration

| Document | Domein | Status |
|----------|--------|--------|
| [Confucius Orchestrator](architecture/confucius-orchestrator-integration-plan.md) | Central agent routing, task dispatch | COMPLETE |
| [Harness Pluggable Architecture](architecture/harness-pluggable-architecture.md) | Plug-and-play agent framework | COMPLETE |
| [AI Dream Team Strategy](architecture/ai-dream-team-multi-model-strategy.md) | Multi-model routing, specialisatie | COMPLETE |
| [Ralph Wiggum Autonomous Loop](architecture/ralph-wiggum-autonomous-loop.md) | Overnight coding, guardrails, circuit breaker | PLANNED |
| [Stage-Based Council Review](architecture/stage-based-council-review-plan.md) | Auto-review per development stage | COMPLETE |
| [Council Human Loop](architecture/council-human-loop.md) | Human-in-the-loop approval | COMPLETE |

### Quality & Security

| Document | Domein | Status |
|----------|--------|--------|
| [Quality Harness Pipeline](architecture/quality-harness-pipeline.md) | PM Gate, QA Gate, regression, micro-decompose | PLANNED |
| [Security Scanner Pipeline](architecture/security-scanner-pipeline.md) | CWE Suite, injection, FN detection | COMPLETE |
| [Quality Assessment CI/CD](architecture/quality-assessment-cicd.md) | CI/CD quality pipeline integratie | COMPLETE |
| [Quality-Functionality Impact Mapping](architecture/quality-functionality-impact-mapping.md) | Quality → functionaliteit linking | COMPLETE |
| [GhostCrew Security](architecture/ghostcrew-security.md) | Security system architectuur | COMPLETE |

### Extraction & Analysis

| Document | Domein | Status |
|----------|--------|--------|
| [Deep Extraction Pipeline](architecture/deep-extraction-pipeline.md) | Multi-LLM code analyse | COMPLETE |
| [Hybrid Static-LLM Pipeline](architecture/hybrid-static-llm-pipeline.md) | Regex + AST + LLM combined | COMPLETE |
| [Brown Paper Enhanced](architecture/brown-paper-enhanced.md) | 6-fase deep analysis | COMPLETE |
| [CiRA Causality Detection](architecture/cira-causality-detection.md) | Requirements causality analysis | COMPLETE |
| [Multi-Language Business Rule Extractors](architecture/multi-language-business-rule-extractors.md) | 12 taal-specifieke extractors | PLANNED |
| [ASP Stability Analyzer](architecture/asp-stability-analyzer-framework.md) | ASP.NET applicatie analyse | COMPLETE |

### Migration

| Document | Domein | Status |
|----------|--------|--------|
| [Migration Enhanced](architecture/migration-enhanced.md) | 7-fase migratie executie | COMPLETE |
| [Migration Framework v2](architecture/migration-framework-v2-technical-spec.md) | Platform integratie spec | COMPLETE |
| [Migration Analyzer](architecture/migration-analyzer-specification.md) | Multi-agent analyse systeem | COMPLETE |
| [Migration Strategy](architecture/migration_strategy_explained.md) | Rebuild-from-specs aanpak | COMPLETE |
| [Blue-Green Deployment](architecture/blue-green-deployment-strategy.md) | Zero-downtime deployment | COMPLETE |

### Client Portal & Workflows

| Document | Domein | Status |
|----------|--------|--------|
| [Client Portal](architecture/client-portal.md) | Klantportaal architectuur | COMPLETE |
| [Client Portal Vision](architecture/client-portal-vision.md) | Complete visie document (v3.0) | COMPLETE |
| [Project Workflows](architecture/project-workflows-standard.md) | Gestandaardiseerde workflows | COMPLETE |
| [Workflow Separation](architecture/workflow-separation-plan.md) | Brown Paper / Migration / Quality scheiding | COMPLETE |
| [Design OS Integration](architecture/design-os-integration.md) | Design-first workflow enhancement | COMPLETE |

### Data & Learning

| Document | Domein | Status |
|----------|--------|--------|
| [Self-Evolution](architecture/self-evolution.md) | Self-evolution architectuur | PLANNED |
| [Continuous Evolution](architecture/continuous-evolution.md) | Continue verbetering systeem | COMPLETE |
| [A/B Testing](architecture/ab-testing.md) | A/B testing framework | COMPLETE |
| [Metrics Layer](architecture/metrics-layer-integration.md) | Metrics integratie specificatie | COMPLETE |
| [LRM Platform Integration](architecture/lrm-platform-integration.md) | LRM service integratie research | RESEARCH |

---

## Workflow ↔ Service Mapping

| mq Workflow | Platform Workflow Type | Backend Services |
|-------------|------------------------|------------------|
| `marqed-bugfix.sh` | BUG | CWE Scanner, Testing Services, Quality Gates |
| `marqed-changes.sh` | NEW_FEATURE / ENHANCEMENT | Deep Extraction, FP Methodology, Hierarchical Story |
| `marqed-migration.sh` | BROWN_PAPER + MIGRATION | Brown Paper (6-fase), Business Rules (12x), Migration Enhanced, Dual-Run, Data Lineage |
| `marqed-analyze.sh` | QUALITY_AUDIT | Hybrid Static-LLM, CWE Suite (96%), Compliance (6 fw), DevOps Analysis, CiRA |
| `marqed-overnight.sh` | OVERNIGHT | Ralph Loop, Quality Harness, PM Gate, QA Gate, Progressive Regression |

---

## Data Flow Voorbeeld — Bugfix Request

```
Developer
    │
    │ $ mq bugfix --id BUG-001 --codebase ./src
    │
    v
marqed-bugfix.sh
    │
    ├─► platform-api.sh ──► /health (check platform)
    │
    ├─► platform-api.sh ──► POST /api/v2/workflow/ (create workflow)
    │                              │
    │                              v
    │                        WorkflowService ──► PostgreSQL
    │
    ├─► platform-api.sh ──► POST /api/v2/knowledge/lookup
    │                              │
    │                              v
    │                        TechStackKB ──► ChromaDB (similar projects, pitfalls)
    │
    ├─► Claude Code (per fase) ──► claude --print --model {model}
    │       │
    │       └─► platform-api.sh ──► PATCH /api/v2/workflow/{id}/tasks/{tid}
    │                                      │
    │                                      v
    │                                WebSocket ──► Progress Dashboard (real-time)
    │
    ├─► platform-api.sh ──► POST /api/v2/security/scan
    │                              │
    │                              v
    │                        CWE Scanner Suite (OpenGrep, Bandit, Trivy)
    │
    └─► platform-api.sh ──► POST /api/v2/validation/visual-regression
                                   │
                                   v
                             VisualRegressionService ──► Completion
```

---

## CLI Bridge Functions (platform-api.sh)

```bash
# Connection
check_platform_required()       # Verify platform is running

# Workflow
create_workflow()               # Create new workflow
get_workflow()                  # Get workflow status
update_task_status()            # Update task progress
sync_tasks_to_platform()        # Sync Claude tasks to DB

# Knowledge
lookup_existing_knowledge()     # Find similar projects

# Security
run_security_scan()             # Trigger CWE Scanner

# Validation
run_visual_regression()         # Visual diff check
run_performance_baseline()      # Performance check
```

---

*Felix — Feature Architect, MarQed.ai Platform Team*
*Versie 2.0 — Week 162 (2026-02-01)*
*Vorige versie: 1.0 (2026-01-24)*
