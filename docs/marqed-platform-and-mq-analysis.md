# MarQed Platform & MQ Workflows - Strategische Analyse & Plan van Aanpak

**Datum**: 2026-01-24
**Versie**: 4.3
**Auteurs**: Architect Agent, Analysis Agent, PM Agent
**Status**: Goedgekeurd voor implementatie

---

## Executive Summary

Dit document analyseert hoe de **mq workflows** (CLI-gebaseerde Claude Code workflows) het bestaande **MarQed.ai Platform** (FastAPI backend met 290+ services) kunnen ondersteunen en versterken, inclusief een uitgebreid plan van aanpak en technisch design.

### Strategie

| Aanpak | Aanbeveling | Succes % |
|--------|-------------|----------|
| **Integratie** | **STERK AANBEVOLEN** | 85-90% |
| Uitbreiding | Aanbevolen | 75-80% |
| Vervanging | Niet aanbevolen | 25-35% |

### Kernprincipes

1. **Kwaliteit voorop** - Geen halfbakken features
2. **Eerst valideren, dan uitbreiden** - Sequentieel naar parallel
3. **Platform MOET draaien** - Geen offline fallbacks
4. **CLI + Dashboard** - Geen IDE plugins nodig

---

# DEEL I: ANALYSE

## 1. Huidige Situatie

### 1.1 MarQed.ai Platform (Backend)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MARQED.AI PLATFORM - HUIDIGE STATE                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  INFRASTRUCTUUR                                                          │
│  ├── FastAPI REST API (800+ endpoints)                                  │
│  ├── PostgreSQL + ChromaDB vectorstore                                  │
│  ├── Redis + Celery voor async tasks                                    │
│  └── Docker-based deployment                                            │
│                                                                          │
│  AI & ANALYSE                                                            │
│  ├── 11 AI Agents (Felix, Quinn, Betty, Eliza, Diana, Marcus, etc.)    │
│  ├── Confucius Orchestrator (PIV loop + quality gates)                 │
│  ├── Brown Paper Analysis (legacy assessment)                          │
│  ├── FP Methodology (IFPUG/NESMA)                                      │
│  └── Stability Analysis (8 categories)                                 │
│                                                                          │
│  SECURITY                                                                │
│  ├── CWE Scanner Suite (OpenGrep, Bandit, Trivy, Custom ASP)           │
│  ├── NEN7510/ISO27001/GDPR compliance                                  │
│  └── OWASP Top 10 verificatie                                          │
│                                                                          │
│  VISUALIZATION                                                           │
│  ├── 40 Dashboards                                                      │
│  └── Real-time reporting                                                │
│                                                                          │
│  QUALITY                                                                 │
│  ├── 2700+ tests (97.8% pass rate)                                     │
│  └── 71 database migrations                                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 mq Workflows (CLI)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MQ WORKFLOWS - HUIDIGE STATE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  WORKFLOWS                                                               │
│  ├── marqed-bugfix.sh    (7 fasen, sequentieel)                        │
│  ├── marqed-changes.sh   (6 fasen, parallel mogelijk)                  │
│  ├── marqed-migration.sh (9 fasen, Strangler Fig)                      │
│  └── marqed-analyze.sh   (code analysis)                               │
│                                                                          │
│  AGENTS (Markdown definitie)                                            │
│  ├── architect-agent.md  (solution design, task breakdown)             │
│  ├── pm-agent.md         (progress tracking, bottlenecks)              │
│  ├── security-agent.md   (OWASP, NEN7510, GDPR checks)                │
│  ├── test-agent.md       (testing strategy, coverage)                  │
│  └── scanner-agent.md    (automated scanning)                          │
│                                                                          │
│  INTEGRATIES                                                             │
│  ├── Claude Code Tasks (native, JSON persistence)                      │
│  ├── Vercel Agent Browser (self-validation)                            │
│  └── WBSO rapportage (automatisch)                                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Huidige Capability Gap

| Capability | Platform | mq | Gap |
|------------|----------|-----|-----|
| REST API | 800+ endpoints | Geen | mq mist API |
| CLI Developer UX | Geen | Excellent | Platform mist CLI |
| Database Persistence | PostgreSQL + Chroma | JSON files | mq mist DB |
| Security Scanning | CWE Suite (95%) | Basic OWASP (30%) | mq mist diepgang |
| Code Analysis | 290+ services | Claude-based | Complementair |
| Task Management | Beperkt | Claude Tasks native | Platform kan leren |
| Dashboards | 40 dashboards | Geen | mq mist visualization |
| WBSO Automation | Gedeeltelijk | Volledig | Platform kan leren |

### 1.4 LLM Gebruik & Kostenmodel

#### Architectuur Keuze: CLI-First (Abonnement)

**Beslissing**: Voorkeur voor **Claude Code CLI** (abonnement) boven API (pay-per-use).

| Aspect | CLI (Abonnement) | API (Pay-per-Use) |
|--------|------------------|-------------------|
| **Kosten** | Vast: €20/€100 per maand | Variabel: €15-75 per 1M tokens |
| **Beschikbaarheid** | Max abonnement beschikbaar ✓ | Vereist ANTHROPIC_API_KEY |
| **Kwaliteit** | Identiek model (Opus 4.5) | Identiek model (Opus 4.5) |
| **Rate Limits** | Hoger (Pro/Max tier) | Standaard API limits |
| **Integratie** | Native CLI commando's | HTTP requests nodig |

#### Huidige Implementatie (Onderzocht)

Het platform ondersteunt **hybride** LLM-aanroepen:

```python
# backend/app/services/extraction_llm_adapter.py (regel 706-720)
# CLI-first approach:
if shutil.which("claude"):
    cmd = ["claude", "--print", "--model", cli_model]
    # Gebruikt Claude Code CLI → abonnement
else:
    # Fallback naar API als CLI niet beschikbaar
    # → ANTHROPIC_API_KEY nodig
```

**Status**:
- ✅ CLI ondersteuning ingebouwd (`claude --print --model`)
- ✅ Max abonnement beschikbaar bij klant
- ✅ Geen kwaliteitsverschil tussen CLI en API
- ⚠️ API fallback beschikbaar maar niet primair

#### Aanbeveling

1. **Primair**: Claude Code CLI met Max abonnement (€100/maand)
   - Hogere rate limits
   - Voorspelbare kosten
   - Native integratie met mq workflows

2. **Secundair**: API alleen voor server-side batch processing
   - Waar CLI niet beschikbaar is (headless servers)
   - Voor zeer hoge volumes (>1M tokens/dag)

#### Kwaliteitsoverwegingen

| Scenario | CLI | API | Kwaliteit |
|----------|-----|-----|-----------|
| Interactieve development | ✅ Aanbevolen | ❌ | Identiek |
| mq workflow uitvoering | ✅ Aanbevolen | ⚠️ Fallback | Identiek |
| Batch processing (server) | ⚠️ Als beschikbaar | ✅ | Identiek |
| CI/CD pipelines | ❌ | ✅ Nodig | Identiek |

**Conclusie**: Geen kwaliteitsverschil. Beide gebruiken hetzelfde Opus 4.5 model. Keuze is gebaseerd op beschikbaarheid en kostenoverwegingen.

### 1.5 Synergie Analyse: Hoe Platform en mq Elkaar Versterken

#### Waar past mq in de Architectuur?

mq workflows vormen de **CLI Developer Interface** die het platform miste:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    POSITIONERING MQ IN ARCHITECTUUR                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  DEVELOPER INTERFACE                                                     ││
│  │                                                                          ││
│  │  ┌─────────────────────────┐        ┌─────────────────────────────────┐ ││
│  │  │  HUIDIGE SITUATIE       │        │  MQ WORKFLOWS [NIEUW]           │ ││
│  │  │                         │        │                                  │ ││
│  │  │  • vim/VSCode           │        │  • marqed-bugfix.sh             │ ││
│  │  │  • project.md editten   │        │  • marqed-changes.sh            │ ││
│  │  │  • Hub Portal (browser) │        │  • marqed-migration.sh          │ ││
│  │  │  • Handmatige API calls │        │  • marqed-analyze.sh            │ ││
│  │  │                         │        │                                  │ ││
│  │  │  ❌ Geen CLI workflow   │        │  ✅ Gestructureerde CLI UX      │ ││
│  │  │  ❌ Handmatig tasks     │        │  ✅ Claude Code Tasks native    │ ││
│  │  │  ❌ Geen self-validation│        │  ✅ Vercel Agent Browser        │ ││
│  │  └─────────────────────────┘        └─────────────────────────────────┘ ││
│  │              │                                    │                      ││
│  │              │         SAMEN STERKER              │                      ││
│  │              └──────────────┬─────────────────────┘                      ││
│  │                             │                                            ││
│  │                             ▼                                            ││
│  │              ┌──────────────────────────────┐                            ││
│  │              │   platform-api.sh            │                            ││
│  │              │   (CLI → API Bridge)         │                            ││
│  │              └──────────────┬───────────────┘                            ││
│  └─────────────────────────────┼────────────────────────────────────────────┘│
│                                │                                             │
│                                ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  MARQED.AI PLATFORM (Bestaand - 290+ services)                          ││
│  │                                                                          ││
│  │  mq workflows GEBRUIKEN deze services:                                   ││
│  │  • Brown Paper Service (voor migration.sh)                              ││
│  │  • CWE Scanner Suite (voor bugfix.sh, analyze.sh)                       ││
│  │  • FP Methodology (voor changes.sh)                                     ││
│  │  • Experience Store (voor knowledge lookup)                             ││
│  │  • Deep Extraction Pipeline (voor changes.sh)                           ││
│  │  • Visual Regression (voor self-validation)                             ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Bidirectionele Versterking

**Platform → mq (wat mq KRIJGT)**:

| Platform Capability | mq Workflow | Versterking |
|---------------------|-------------|-------------|
| Brown Paper 6-fase | migration.sh | Diepere legacy analyse dan CLI alleen kan |
| CWE Scanner (95%) | bugfix.sh, analyze.sh | Enterprise-grade security scanning |
| 11 AI Agents | Alle workflows | Gespecialiseerde expertise per taak |
| Experience Store | Alle workflows | Leren van eerdere projecten |
| FP Methodology | changes.sh | Accurate schattingen (IFPUG/NESMA) |
| PostgreSQL + ChromaDB | Alle workflows | Persistente state, vector search |
| 40 Dashboards | Progress Dashboard | Visueel overzicht van CLI werk |

**mq → Platform (wat Platform KRIJGT)**:

| mq Capability | Platform Verbetering | Versterking |
|---------------|----------------------|-------------|
| Claude Code Tasks | Betere task management | Native task tracking die platform mist |
| Vercel Agent Browser | Self-validation | Automatische UI testing |
| CLI Developer UX | Snellere developer flow | Geen browser nodig voor dev work |
| WBSO Automation | Betere R&D rapportage | Automatische WBSO classificatie |
| Gestructureerde fasen | Workflow discipline | 7-9 fasen met validation gates |
| PRD Templates | Consistente input | Gestandaardiseerde requirements |

#### Synergie Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SYNERGIE MATRIX                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                        PLATFORM SERVICES                                     │
│           ┌─────────┬─────────┬─────────┬─────────┬─────────┐               │
│           │ Brown   │ CWE     │ FP      │ Exper.  │ Deep    │               │
│           │ Paper   │ Scanner │ Method  │ Store   │ Extract │               │
│  ┌────────┼─────────┼─────────┼─────────┼─────────┼─────────┤               │
│  │bugfix  │    ○    │   ●●●   │    ○    │   ●●    │    ○    │               │
│  │.sh     │         │ security│         │ similar │         │               │
│  ├────────┼─────────┼─────────┼─────────┼─────────┼─────────┤               │
│  │changes │    ○    │   ●●    │  ●●●    │   ●●    │  ●●●    │               │
│  │.sh     │         │ quality │ estimate│ patterns│ stories │               │
│  ├────────┼─────────┼─────────┼─────────┼─────────┼─────────┤               │
│  │migrat. │  ●●●    │   ●●    │  ●●●    │  ●●●    │  ●●●    │               │
│  │.sh     │ 6-fase  │ legacy  │ effort  │ lessons │ backlog │               │
│  ├────────┼─────────┼─────────┼─────────┼─────────┼─────────┤               │
│  │analyze │   ●●    │  ●●●    │   ●●    │   ●●    │   ●●    │               │
│  │.sh     │ assess  │ audit   │ sizing  │ compare │ extract │               │
│  └────────┴─────────┴─────────┴─────────┴─────────┴─────────┘               │
│                                                                              │
│  Legenda: ●●● = Kritieke integratie | ●● = Sterke integratie | ○ = Optioneel│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Concrete Voorbeeld: Bug Fix Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  VOORBEELD: marqed-bugfix.sh + Platform                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STAP 1: Developer start bugfix                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  $ ./mq/workflows/marqed-bugfix.sh --bug BUG-042                        ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│  STAP 2: mq roept Platform API aan                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  platform-api.sh:                                                        ││
│  │  • lookup_existing_knowledge "sql-injection" "bugfix"                   ││
│  │  • run_security_scan "$codebase" "owasp-top10"                          ││
│  │  • create_workflow "bugfix" "BUG-042" "$codebase"                       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│  STAP 3: Platform Services leveren                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Experience Store:                                                       ││
│  │  → "Vergelijkbare bug in project X, opgelost met parameterized queries" ││
│  │  → "Bekende pitfall: vergeet ook stored procedures te checken"          ││
│  │                                                                          ││
│  │  CWE Scanner:                                                            ││
│  │  → CWE-89: SQL Injection gevonden in auth_service.py:142               ││
│  │  → Severity: CRITICAL                                                    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│  STAP 4: Claude Code (CLI) lost op met context                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  claude --print --model sonnet                                           ││
│  │  → Heeft nu: scanner resultaten + experience store kennis               ││
│  │  → Fix: parameterized queries + stored proc updates                     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│  STAP 5: Self-validation                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Vercel Agent Browser:                                                   ││
│  │  → Test SQL injection attack vectors                                    ││
│  │  → Screenshot evidence                                                   ││
│  │                                                                          ││
│  │  Platform Visual Regression:                                             ││
│  │  → Vergelijk UI voor/na fix                                             ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│  STAP 6: Update Platform                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  platform-api.sh:                                                        ││
│  │  • update_task_status "BUG-042" "completed"                             ││
│  │  • store_experience "sql-injection-fix" "$lessons_learned"              ││
│  │  → Platform leert voor volgende keer!                                   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Gecombineerde Resultaten

| Aspect | Platform Alleen | mq Alleen | Platform + mq |
|--------|-----------------|-----------|---------------|
| Developer UX | Browser-based | CLI-native | CLI + Dashboard |
| Security Scanning | 95% coverage | 30% (basic) | 95% + self-validation |
| Knowledge | Experience Store | Geen persistentie | Store + real-time lookup |
| Task Management | Beperkt | Claude Tasks native | Tasks + DB persistence |
| Estimation | IFPUG/NESMA | Handmatig | Automatisch + historie |
| Self-Validation | Visual Regression | Agent Browser | Beide + combined evidence |
| **Success Rate** | 75-80% | 70-75% | **85-90%** |

**Conclusie**: mq workflows + Platform samen bereiken **94% capability coverage** met **85-90% success rate**.

### 1.6 Bidirectionele Entry Points (Platform als Trigger)

> **Gap geïdentificeerd**: Het huidige ontwerp (v4.0) beschreef alleen CLI → Platform.
> Hieronder de uitbreiding voor Platform → CLI triggering.

#### Twee Entry Points voor Hetzelfde Werk

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    BIDIRECTIONELE ENTRY POINTS                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ENTRY POINT 1: CLI (Developer)                                                  │
│  ═══════════════════════════════                                                 │
│                                                                                  │
│  Terminal:                                                                       │
│  $ mq bugfix --id BUG-042 --codebase ./src                                      │
│       │                                                                          │
│       └──► platform-api.sh ──► Platform Services ──► Result                     │
│                                                                                  │
│  ENTRY POINT 2: Platform Dashboard (Klant/PM)                                    │
│  ═══════════════════════════════════════════════                                 │
│                                                                                  │
│  Browser:                                                                        │
│  Hub Portal → Security Dashboard → "Start Bug Fix" button                       │
│       │                                                                          │
│       └──► POST /api/v2/workflow/trigger ──► workflow-trigger.sh ──► mq bugfix  │
│                                                                                  │
│  BEIDE ENTRY POINTS GEBRUIKEN DEZELFDE:                                          │
│  • Platform services (CWE Scanner, Knowledge, Experience Store)                  │
│  • mq workflow fasen (7 fasen voor bugfix)                                      │
│  • Progress Dashboard (real-time status)                                         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### Flow Integration Matrix: Bugfix Workflows

| Platform Component | mq Bugfix Fase | Integratie Punt | Best of Both |
|-------------------|----------------|-----------------|--------------|
| **Security Dashboard** → CWE Scanner | 1. Bug Reproduction | Pre-scan resultaten als input | Platform scant, mq reproduceert |
| **Quality Dashboard** → Root Cause Analyzer | 2. Root Cause Analysis | `root_cause` field in DB | mq analyseert, Platform toont patterns |
| **Agent Dashboard** → Betty (Bug Agent) | 3. Fix Implementation | Betty suggestions + Claude fix | Platform's Betty adviseert, mq implementeert |
| **Testing Dashboard** → Tessa (Test Agent) | 4. Testing & Validation | Test coverage + results | Platform's Tessa test strategie, mq voert uit |
| **Quality Gates** → Regression Rules | 5. Regression Testing | Pass/fail criteria | Platform definieert gates, mq valideert |
| **Human Review** → Code Review Queue | 6. Code Review | Review assignment | Platform queue, mq prepareert evidence |
| **Codewiki** → Documentation | 7. Documentation | Auto-update codewiki | mq genereert, Platform integreert |

#### Flow Integration Matrix: Changes/New Feature Workflows

| Platform Component | mq Changes Fase | Integratie Punt | Best of Both |
|-------------------|-----------------|-----------------|--------------|
| **Spec Kit Wizard** → Requirements | 1. Requirements Analysis | Shaped spec als input | Platform shaped, mq analyseert |
| **Estimation Dashboard** → FP/NESMA | 2. Effort Estimation | Gecombineerde estimate | Platform historische data + mq LLM |
| **Project Wizard** → Architecture | 3. Solution Design | Felix suggestions | Platform's Felix, mq implementatie |
| **Deep Extraction** → Story Breakdown | 4. Task Breakdown | Hierarchical stories | Platform extractie, mq verfijning |
| **Kanban Dashboard** → Implementation | 5. Implementation | Task sync bidirectioneel | mq Claude Tasks ↔ Platform Kanban |
| **Quality Dashboard** → Test Coverage | 6. Testing | Coverage targets | Platform gates, mq test gen |
| **Brown Paper** → Impact Analysis | 7. Impact Assessment | Change impact score | Platform analyse, mq voorspelling |
| **Human Review** → Final Review | 8. Review & Merge | Approval workflow | Platform queue, mq evidence |

#### Nieuwe API Endpoint: Workflow Trigger

```
POST /api/v2/workflow/trigger
{
    "workflow_type": "BUG",           // BUG | NEW_FEATURE | ENHANCEMENT | MIGRATION
    "trigger_source": "dashboard",     // dashboard | api | scheduled
    "source_item_id": "SEC-VUL-123",   // Security finding, Feature request, etc.
    "target_codebase": "/path/to/repo",
    "additional_context": {
        "security_scan_id": "scan-456",
        "cwe_findings": ["CWE-89", "CWE-79"]
    }
}

Response:
{
    "workflow_id": "WF-2026-01-24-001",
    "mq_command": "mq bugfix --id BUG-042 --codebase /path/to/repo",
    "status": "triggered",
    "dashboard_url": "/dashboard/workflows/WF-2026-01-24-001"
}
```

#### Nieuwe Shell Script: workflow-trigger.sh

```bash
# mq/workflows/common/workflow-trigger.sh
# Called by platform to trigger mq workflows

trigger_mq_workflow() {
    local workflow_type="$1"
    local item_id="$2"
    local codebase="$3"

    case "$workflow_type" in
        "BUG")
            mq bugfix --id "$item_id" --codebase "$codebase" --from-platform
            ;;
        "NEW_FEATURE"|"ENHANCEMENT")
            mq changes --id "$item_id" --codebase "$codebase" --from-platform
            ;;
        "MIGRATION")
            mq migration --id "$item_id" --codebase "$codebase" --from-platform
            ;;
        "QUALITY_AUDIT")
            mq analyze --id "$item_id" --codebase "$codebase" --from-platform
            ;;
    esac
}
```

#### Use Cases voor Platform als Entry Point

| Use Case | Entry Point | Flow |
|----------|-------------|------|
| **Security finding → Bug fix** | Security Dashboard | CWE finding → "Fix Now" → mq bugfix met context |
| **Feature request → Implementation** | Customer Portal (Strapi) | Request → Approval → mq changes |
| **Scheduled maintenance** | Maintenance Scheduler | Cron → workflow-trigger.sh → mq bugfix/analyze |
| **Brown Paper decision** | Brown Paper Dashboard | Decision: "Migrate" → mq migration |
| **Quality gate failure** | Quality Dashboard | Gate fail → "Auto-fix" → mq bugfix |

#### Impact op Bestaande Epics

Dit voegt **1 nieuwe User Story** toe aan **Epic E1 (CLI Bridge)**:

**E1-US4: Platform-to-CLI Trigger**
- `workflow-trigger.sh` script
- `/api/v2/workflow/trigger` endpoint
- `--from-platform` flag in alle mq scripts
- Dashboard "Start Workflow" buttons

**Geschatte extra effort**: 8 uur (1 dag)

### 1.7 Intake Document Structuur (Per Project Queue)

#### Folder Structuur

Elk project heeft zijn eigen intake queue met status tracking:

```
<project-root>/.marqed/intake/
├── bugs/
│   ├── todo/                  # Nieuwe bugs - wachtend op behandeling
│   │   └── BUG-2026-01-24-001.md
│   ├── in-progress/           # Bug wordt nu behandeld door mq workflow
│   └── done/                  # Afgehandelde bugs (archief)
│
├── changes/
│   ├── todo/                  # Nieuwe feature requests
│   ├── in-progress/
│   └── done/
│
├── migrations/
│   ├── todo/                  # Geplande migraties
│   ├── in-progress/
│   └── done/
│
└── analyses/
    ├── todo/                  # Geplande analyses
    ├── in-progress/
    └── done/
```

#### Naamgeving Conventie

| Type | Prefix | Template | Voorbeeld |
|------|--------|----------|-----------|
| Bug Fix | `BUG-` | BUGFIX-TEMPLATE-v2.md | `BUG-2026-01-24-001.md` |
| Change/Feature | `CHANGE-` | CHANGE-TEMPLATE-v2.md | `CHANGE-2026-01-24-001.md` |
| Migration | `MIGRATE-` | MIGRATION-TEMPLATE-v2.md | `MIGRATE-2026-01-24-001.md` |
| Analysis | `ANALYZE-` | ANALYZE-TEMPLATE-v2.md | `ANALYZE-2026-01-24-001.md` |

#### Status Flow

```
┌──────────┐     mq workflow     ┌───────────────┐     workflow     ┌──────────┐
│  todo/   │ ─────start────────► │ in-progress/  │ ────complete───► │  done/   │
└──────────┘                     └───────────────┘                  └──────────┘
     ▲                                                                    │
     │                                                                    │
     └──────────── (handmatig: heropenen indien nodig) ◄──────────────────┘
```

#### CLI Commando's

```bash
# Queue overzicht
mq list                      # Alle types, alleen todo
mq list bugs                 # Alleen bugs in todo/
mq list all --include-done   # Alles inclusief done/

# Start workflow
mq bugfix --next             # Pakt oudste bug uit todo/, verplaatst naar in-progress/
mq bugfix --id BUG-2026-01-24-001  # Specifieke bug

# Nieuw intake document aanmaken
mq new bug                   # Maakt nieuw BUG-*.md in todo/ met template
mq new change                # Maakt nieuw CHANGE-*.md in todo/ met template
```

#### Platform Dashboard Panel

```
┌─────────────────────────────────────────────────────────────────────────┐
│  📥 Intake Queue                                        [+ New Intake]  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  🐛 Bugs                          │  ⏳ 3 todo  │ 🔄 1 in-progress │ ✅ 12 done │
│  ├── BUG-2026-01-24-001 - SQL Injection      [Start Fix]               │
│  ├── BUG-2026-01-24-002 - Timeout issue      [Start Fix]               │
│  └── BUG-2026-01-23-005 - Memory leak        🔄 IN PROGRESS            │
│                                                                          │
│  ✨ Changes                       │  ⏳ 2 todo  │ 🔄 0 in-progress │ ✅ 5 done  │
│  ├── CHANGE-2026-01-24-001 - Dark mode       [Start Feature]           │
│  └── CHANGE-2026-01-24-002 - PDF export      [Start Feature]           │
│                                                                          │
│  🔄 Migrations                    │  ⏳ 0 todo  │ 🔄 0 in-progress │ ✅ 1 done  │
│                                                                          │
│  🔍 Analyses                      │  ⏳ 1 todo  │ 🔄 0 in-progress │ ✅ 3 done  │
│  └── ANALYZE-2026-01-24-001 - Security audit [Run Analysis]            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Geschatte effort**: 12 uur (1.5 dag)

---

## 2. Goedgekeurde Verbeteringen

### 2.1 Overzicht Fasering

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATIE FASERING                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  FASE 1: INGEPLAND VOOR REALISATIE (9 weken)                            │
│  ═══════════════════════════════════════════                            │
│  V1. Progress Dashboard          (2 weken)  - P1 High                   │
│  V2. Tech Stack Knowledge Lookup (3 weken)  - P1 High                   │
│      • Kijkt naar KB over tech stack en problematiek                   │
│      • Wat is geleerd uit eerdere projecten                            │
│      • Wat werkt wel/niet bij deze technologie                         │
│  V3. Self-Validation Enhancement (1 week)   - P2 Medium                 │
│  V4. Foundation + Integration    (3 weken)  - P1 High                   │
│                                                                          │
│  TOEKOMSTIG: NA VALIDATIE FASE 1 (niet ingepland)                       │
│  ═══════════════════════════════════════════════                        │
│  V5. Parallel Execution Coordinator         - P3 Later                  │
│  V6. GitOps Native Integration              - P3 Later                  │
│      → Pas overwegen nadat FASE 1 volledig werkt en gevalideerd is     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 V1: Progress Dashboard (INGEPLAND)

**Probleem**: CLI output alleen, geen visueel overzicht van workflow voortgang

**Oplossing**: Dedicated dashboard in Portal voor mq workflow monitoring

```
┌─────────────────────────────────────────────────────────────────────────┐
│  WORKFLOW PROGRESS DASHBOARD                                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Active Workflows                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ BUG-2026-01-24-001                                                  ││
│  │ Type: Bug Fix | Started: 09:15 | Phase: 3/7                         ││
│  │ Progress: [████████████░░░░░░░░] 60%                                ││
│  │                                                                      ││
│  │ Tasks:                                                               ││
│  │ ✅ Phase 1: Bug Reproduction         (completed 09:25)              ││
│  │ ✅ Phase 2: Root Cause Analysis      (completed 10:15)              ││
│  │ 🔄 Phase 3: Fix Implementation       (in progress)                  ││
│  │ ⏳ Phase 4: Unit Testing             (pending)                      ││
│  │ ⏳ Phase 5: Integration Testing      (pending)                      ││
│  │ ⏳ Phase 6: Code Review              (pending)                      ││
│  │ ⏳ Phase 7: Documentation            (pending)                      ││
│  │                                                                      ││
│  │ Logs: [View Live Logs]  Security: [View Scan Results]              ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│  Completed Today: 3 | In Progress: 2 | Queued: 5                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

| Aspect | Detail |
|--------|--------|
| **Status** | INGEPLAND |
| **Prioriteit** | P1 - High |
| **Effort** | 2 weken |
| **Impact** | Visibility, team collaboration |
| **Note** | Geen IDE plugin nodig - web dashboard is voldoende |

---

### 2.3 V2: Tech Stack Knowledge Lookup (INGEPLAND)

**Probleem**: Elke workflow start from scratch, geen hergebruik van eerdere kennis

**Oplossing**: Bij start van elk project automatisch checken wat er al bekend is over:
- De **tech stack** (ASP Classic, SQL Server, VBScript, etc.)
- De **problematiek** (migration, security, performance)
- **Eerdere projecten** met vergelijkbare stack
- **Wat geleerd is** uit vorige projecten
- **Wat wel/niet werkt** bij deze technologie

**Wat wordt opgezocht:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│  KNOWLEDGE LOOKUP BIJ PROJECT START                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. TECH STACK KENNIS                                                   │
│     • Eerder gebruikte patterns voor deze stack                         │
│     • Bekende valkuilen en hoe te vermijden                            │
│     • Geschatte doorlooptijd op basis van historie                     │
│                                                                          │
│  2. PROJECT HISTORIE                                                     │
│     • Vergelijkbare projecten (via ChromaDB similarity)                │
│     • Uitkomsten: success/partial/failed                               │
│     • Lessons learned per project                                       │
│                                                                          │
│  3. WAT WERKT WEL                                                       │
│     • Bewezen oplossingen                                               │
│     • Effectieve tools en frameworks                                    │
│     • Best practices uit experience store                              │
│                                                                          │
│  4. WAT WERKT NIET                                                      │
│     • Bekende anti-patterns                                             │
│     • Mislukte aanpakken                                               │
│     • Te vermijden tools/frameworks                                    │
│                                                                          │
│  5. AANBEVELINGEN                                                       │
│     • Concrete acties voor dit project                                 │
│     • Waarschuwingen bij kritieke pitfalls                             │
│     • Suggesties voor tooling                                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

| Aspect | Detail |
|--------|--------|
| **Status** | INGEPLAND |
| **Prioriteit** | P1 - High |
| **Effort** | 3 weken |
| **Impact** | 20-40% snellere start, minder herhaalde fouten |
| **Bronnen** | experience_store_service, continuous_learning_service, ChromaDB, project_knowledge |

---

### 2.4 V3: Self-Validation Enhancement (INGEPLAND)

**Probleem**: Vercel Browser doet screenshots, geen diff analysis

**Oplossing**: Koppel bestaande platform services (visual_regression, performance_baseline)

| Aspect | Detail |
|--------|--------|
| **Status** | INGEPLAND |
| **Prioriteit** | P2 - Medium |
| **Effort** | 1 week |
| **Impact** | Betere kwaliteitsborging |

---

## 2.5 Toekomstige Verbeteringen (NIET INGEPLAND)

De volgende verbeteringen worden pas overwogen nadat Fase 1 volledig is gevalideerd.

### V5: Parallel Execution Coordinator

**Probleem**: mq sessions weten niets van elkaar, file locks ontbreken

**Oplossing**: Redis-based coordinator voor cross-session synchronisatie

| Aspect | Detail |
|--------|--------|
| **Status** | NIET INGEPLAND |
| **Prioriteit** | P3 - Later |
| **Effort** | 2 weken |
| **Voorwaarde** | Fase 1 volledig gevalideerd en werkend |
| **Reden** | Eerst zien dat sequentiële workflows 100% werken, dan pas parallel |

### V6: GitOps Native Integration

**Probleem**: Handmatige trigger van workflows, geen CI/CD integratie

**Oplossing**: GitHub Actions / GitLab CI native mq workflow triggers

| Aspect | Detail |
|--------|--------|
| **Status** | NIET INGEPLAND |
| **Prioriteit** | P3 - Later |
| **Effort** | 2 weken |
| **Voorwaarde** | Fase 1 volledig gevalideerd en werkend |
| **Reden** | Vereist eerst stabiele CLI → API integratie |

**Besluit**: We implementeren eerst de basis (dashboard, knowledge lookup, validation). Pas als dit volledig werkt en gevalideerd is, overwegen we parallelle stromen en GitOps integratie.

---

## 3. Afgewezen Voorstellen

### 3.1 IDE Plugin/Integratie

| Aspect | Detail |
|--------|--------|
| **Status** | ❌ AFGEWEZEN |
| **Reden** | Web dashboard + CLI voldoende |
| **Argumenten** | Extra maintenance, CLI werkt overal, geen toegevoegde waarde |
| **Heroverweging** | Nooit |

### 3.2 Offline Mode / Local Fallback

| Aspect | Detail |
|--------|--------|
| **Status** | ❌ AFGEWEZEN |
| **Reden** | Kwaliteit voorop - geen halfbakken functionaliteit |
| **Argumenten** | Platform MOET draaien, offline zou 30% features missen |
| **Heroverweging** | Nooit |

```bash
# Wat we WEL doen: duidelijke foutmelding
check_platform_required() {
    if ! curl -s "${MARQED_API_URL}/health" > /dev/null 2>&1; then
        echo "❌ ERROR: MarQed.ai Platform is niet bereikbaar"
        echo "   Start het platform met: make start"
        exit 1
    fi
}
```

### 3.3 Platform Vervangen door mq

| Aspect | Detail |
|--------|--------|
| **Status** | ❌ STERK AFGEWEZEN |
| **Reden** | Verlies 290+ services, 2700+ tests, jaren werk |
| **Heroverweging** | Nooit |

### 3.4 Real-time Collaboration

| Aspect | Detail |
|--------|--------|
| **Status** | ❌ AFGEWEZEN |
| **Reden** | Over-engineering |
| **Heroverweging** | Nooit |

---

# DEEL II: PLAN VAN AANPAK

## 4. Implementatie Roadmap

### 4.1 Fasering Overzicht

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATIE ROADMAP (9 weken)                       │
│                    + Validatie + Optionele Fase 2                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  FASE 1A: FOUNDATION (Week 1-2)                                         │
│  ════════════════════════════════                                       │
│  ├── Workflow API endpoints ontwerpen en bouwen                         │
│  ├── Task persistence model naar PostgreSQL                             │
│  ├── CLI → API bridge (platform-api.sh)                                │
│  ├── Platform health check in alle mq scripts                          │
│  └── Basis error handling en logging                                    │
│                                                                          │
│  FASE 1B: PROGRESS DASHBOARD (Week 3-4) [V1]                            │
│  ════════════════════════════════════════════                           │
│  ├── Dashboard UI ontwerp en implementatie                              │
│  ├── Real-time workflow status via WebSocket/SSE                       │
│  ├── Task lijst weergave per workflow                                  │
│  ├── Log viewer integratie                                             │
│  └── Security scan results linkage                                     │
│                                                                          │
│  FASE 1C: TECH STACK KNOWLEDGE (Week 5-7) [V2]                          │
│  ════════════════════════════════════════════════                       │
│  ├── TechStackKnowledgeService bouwen                                  │
│  ├── Experience Store koppeling                                        │
│  ├── ChromaDB similarity search                                        │
│  ├── Pitfalls extraction en display                                    │
│  └── CLI integration (knowledge-lookup.sh)                             │
│                                                                          │
│  FASE 1D: SELF-VALIDATION (Week 8) [V3]                                 │
│  ════════════════════════════════════════                               │
│  ├── Visual regression service koppeling                               │
│  ├── Performance baseline integratie                                   │
│  └── Validation results naar dashboard                                 │
│                                                                          │
│  FASE 1E: POLISH & TESTING (Week 9)                                     │
│  ════════════════════════════════════                                   │
│  ├── End-to-end testing alle workflows                                 │
│  ├── Documentation                                                     │
│  ├── Bug fixes                                                         │
│  └── WBSO rapportage validatie                                         │
│                                                                          │
│  ════════════════════════════════════════════════════════════════════  │
│  VALIDATIE CHECKPOINT                                                   │
│  ════════════════════════════════════════════════════════════════════  │
│  • Alle sequentiële workflows werken 100%                              │
│  • Dashboard toont correcte status                                     │
│  • Knowledge lookup geeft relevante resultaten                         │
│  • Self-validation werkt correct                                       │
│  • Geen kritieke bugs                                                  │
│  ════════════════════════════════════════════════════════════════════  │
│                                                                          │
│  FASE 2: PARALLEL COORDINATOR (NA VALIDATIE) [V4]                       │
│  ════════════════════════════════════════════════                       │
│  ├── Alleen starten als Fase 1 100% gevalideerd                        │
│  ├── Redis-based session coordinator                                   │
│  ├── File locking mechanism                                            │
│  ├── Cross-session status sync                                         │
│  └── Multi-session dashboard view                                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Week-voor-Week Planning

#### Week 1: Foundation - API Design

| Dag | Activiteit | Output |
|-----|------------|--------|
| Ma | API endpoint design workshop | OpenAPI spec draft |
| Di | Task persistence model design | SQLAlchemy models |
| Wo | Workflow state machine design | State diagram |
| Do | CLI bridge design | Shell script specs |
| Vr | Review & refinement | Goedgekeurd design |

**Deliverables Week 1:**
- [ ] OpenAPI specificatie voor workflow endpoints
- [ ] Database model voor workflow tasks
- [ ] State machine diagram
- [ ] CLI bridge specificaties

#### Week 2: Foundation - Implementation

| Dag | Activiteit | Output |
|-----|------------|--------|
| Ma | Workflow API endpoints implementeren | Working endpoints |
| Di | Task persistence implementeren | DB integration |
| Wo | platform-api.sh bouwen | CLI bridge |
| Do | Health checks toevoegen aan mq scripts | Updated scripts |
| Vr | Integration testing | Working foundation |

**Deliverables Week 2:**
- [ ] `/api/v2/workflow/*` endpoints werkend
- [ ] Task persistence naar PostgreSQL
- [ ] `mq/workflows/common/platform-api.sh`
- [ ] Health checks in alle workflow scripts

#### Week 3: Progress Dashboard - Backend

| Dag | Activiteit | Output |
|-----|------------|--------|
| Ma | Dashboard data model | Schema |
| Di | WebSocket/SSE setup | Real-time channel |
| Wo | Workflow status aggregation | Status API |
| Do | Log streaming setup | Log endpoint |
| Vr | Testing & bugfixes | Working backend |

**Deliverables Week 3:**
- [ ] Real-time status updates via WebSocket
- [ ] `/api/v2/dashboard/workflows` endpoint
- [ ] Log streaming endpoint

#### Week 4: Progress Dashboard - Frontend

| Dag | Activiteit | Output |
|-----|------------|--------|
| Ma | Dashboard layout & design | Figma/HTML |
| Di | Workflow cards component | React component |
| Wo | Task list component | React component |
| Do | Log viewer integration | Working viewer |
| Vr | Polish & testing | Dashboard MVP |

**Deliverables Week 4:**
- [ ] Workflow Progress Dashboard in Portal
- [ ] Real-time updates werkend
- [ ] Log viewer geïntegreerd

#### Week 5-6: Tech Stack Knowledge - Core

| Dag | Activiteit | Output |
|-----|------------|--------|
| W5 Ma | TechStackKnowledgeService skeleton | Service class |
| W5 Di | Experience Store integration | Search function |
| W5 Wo | ChromaDB similarity search | Vector search |
| W5 Do | Pattern extraction logic | Pattern API |
| W5 Vr | Pitfalls extraction | Pitfalls API |
| W6 Ma | Effort estimation from history | Estimation API |
| W6 Di | CLI integration (knowledge-lookup.sh) | Shell script |
| W6 Wo | Dashboard integration | Knowledge panel |
| W6 Do | Testing met echte data | Validated results |
| W6 Vr | Refinement | Production ready |

**Deliverables Week 5-6:**
- [ ] TechStackKnowledgeService compleet
- [ ] `/api/v2/knowledge/lookup` endpoint
- [ ] `knowledge-lookup.sh` in mq workflows
- [ ] Knowledge panel in dashboard

#### Week 7: Tech Stack Knowledge - Refinement

| Dag | Activiteit | Output |
|-----|------------|--------|
| Ma | UI/UX improvements | Better display |
| Di | Search relevance tuning | Better results |
| Wo | Integration in all 4 workflows | Updated scripts |
| Do | Documentation | User guide |
| Vr | Final testing | Validated |

**Deliverables Week 7:**
- [ ] Knowledge lookup in alle workflows
- [ ] Getuned voor relevante resultaten
- [ ] Documentatie

#### Week 8: Self-Validation Enhancement

| Dag | Activiteit | Output |
|-----|------------|--------|
| Ma | Visual regression koppeling | API integration |
| Di | Performance baseline koppeling | API integration |
| Wo | Validation results naar dashboard | UI component |
| Do | CLI validation commands | Shell functions |
| Vr | Testing | Validated |

**Deliverables Week 8:**
- [ ] Visual regression geïntegreerd
- [ ] Performance baseline geïntegreerd
- [ ] Validation results in dashboard

#### Week 9: Polish & Documentation

| Dag | Activiteit | Output |
|-----|------------|--------|
| Ma | End-to-end testing bugfix workflow | Test report |
| Di | End-to-end testing changes workflow | Test report |
| Wo | End-to-end testing migration workflow | Test report |
| Do | Documentation & user guides | Docs |
| Vr | WBSO rapportage validatie | Final review |

**Deliverables Week 9:**
- [ ] Alle workflows getest end-to-end
- [ ] Documentatie compleet
- [ ] WBSO rapportage gevalideerd

---

## 5. Resource Planning

### 5.1 Team Samenstelling

| Rol | FTE | Weken | Focus |
|-----|-----|-------|-------|
| Backend Developer | 0.5 | 9 | API endpoints, services |
| Frontend Developer | 0.25 | 4 | Progress Dashboard |
| DevOps | 0.25 | 3 | CLI/API bridge, deployment |
| QA | 0.25 | 4 | Integration tests |
| **Totaal** | **1.0 FTE** | **9 weken** | |

### 5.2 Dependencies

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DEPENDENCY GRAPH                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Foundation (W1-2)                                                       │
│       │                                                                  │
│       ├──────────────────┬──────────────────┐                           │
│       │                  │                  │                           │
│       v                  v                  v                           │
│  Dashboard (W3-4)   Knowledge (W5-7)   Validation (W8)                  │
│       │                  │                  │                           │
│       └──────────────────┴──────────────────┘                           │
│                          │                                              │
│                          v                                              │
│                    Polish (W9)                                          │
│                          │                                              │
│                          v                                              │
│               ════════════════════                                      │
│               VALIDATIE CHECKPOINT                                      │
│               ════════════════════                                      │
│                          │                                              │
│                          v (alleen na 100% validatie)                   │
│               Parallel Coordinator                                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# DEEL III: TECHNISCH DESIGN

## 6. Architectuur Design

### 6.1 Geïntegreerde Totaalarchitectuur

De volgende architectuurplaat toont hoe **mq workflows** integreren met het bestaande **MarQed.ai Platform** (uit `.project/ARCHITECTURE.md` v8.6):

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    MARQED.AI GEÏNTEGREERDE ARCHITECTUUR                          │
│                    (Platform v8.6 + mq Workflows v2.0)                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ══════════════════════════════════════════════════════════════════════════════ │
│  LAAG 0: DEVELOPER INTERFACE                                                     │
│  ══════════════════════════════════════════════════════════════════════════════ │
│                                                                                  │
│  ┌──────────────────────────────────┐   ┌──────────────────────────────────────┐│
│  │      DEVELOPER (Jij)             │   │      KLANT (Customer Portal)         ││
│  │  • vim/VSCode editor             │   │  • Feature requests                  ││
│  │  • Terminal (mq workflows)       │   │  • Progress tracking                 ││
│  │  • project.md als source         │   │  • Roadmap view                      ││
│  └───────────────┬──────────────────┘   └───────────────┬──────────────────────┘│
│                  │                                      │                        │
│  ══════════════════════════════════════════════════════════════════════════════ │
│  LAAG 1: CLI & WEB INTERFACE                                                     │
│  ══════════════════════════════════════════════════════════════════════════════ │
│                  │                                      │                        │
│  ┌───────────────▼──────────────────┐   ┌───────────────▼──────────────────────┐│
│  │     mq CLI Layer [NIEUW]         │   │     Web Interfaces                   ││
│  │  ┌──────────┐ ┌──────────┐       │   │  ┌──────────────┐ ┌────────────────┐ ││
│  │  │bugfix.sh │ │changes.sh│       │   │  │ Hub Portal   │ │Customer Portal │ ││
│  │  └────┬─────┘ └────┬─────┘       │   │  │ (40 views)   │ │ (Strapi)       │ ││
│  │  ┌────┴─────┐ ┌────┴─────┐       │   │  └──────────────┘ └────────────────┘ ││
│  │  │migration │ │analyze.sh│       │   │  ┌──────────────────────────────────┐ ││
│  │  └────┬─────┘ └────┬─────┘       │   │  │ Progress Dashboard [NIEUW]       │ ││
│  │       └─────┬──────┘             │   │  │ /dashboard/workflows             │ ││
│  │             │                    │   │  └──────────────────────────────────┘ ││
│  │  ┌──────────▼──────────┐         │   └────────────────────┬─────────────────┘│
│  │  │  platform-api.sh    │         │                        │                  │
│  │  │  (CLI → API Bridge) │─────────┼────────────────────────┘                  │
│  │  └──────────┬──────────┘         │                                           │
│  └─────────────┼────────────────────┘                                           │
│                │                                                                 │
│  ══════════════════════════════════════════════════════════════════════════════ │
│  LAAG 2: API GATEWAY (FastAPI - 700+ endpoints)                                  │
│  ══════════════════════════════════════════════════════════════════════════════ │
│                │                                                                 │
│  ┌─────────────▼───────────────────────────────────────────────────────────────┐│
│  │                         MarQed.ai API Gateway                                ││
│  │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌─────────────────┐  ││
│  │  │Workflow API   │ │Knowledge API  │ │Validation API │ │ Token Context   │  ││
│  │  │/api/v2/workflow│/api/v2/knowledge│/api/v2/validation│ /api/token-context│ ││
│  │  │ [NIEUW]       │ │ [NIEUW]       │ │ [NIEUW]       │ │                 │  ││
│  │  └───────────────┘ └───────────────┘ └───────────────┘ └─────────────────┘  ││
│  │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌─────────────────┐  ││
│  │  │Brown Paper API│ │Extraction API │ │Migration API  │ │ Testing API     │  ││
│  │  │ /api/bmad/*   │ │/api/extraction│ │/api/migration │ │ /api/testing/*  │  ││
│  │  └───────────────┘ └───────────────┘ └───────────────┘ └─────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                │                                                                 │
│  ══════════════════════════════════════════════════════════════════════════════ │
│  LAAG 3: 3-LAAGS AGENT ARCHITECTUUR (11 Core + Stack Templates)                  │
│  ══════════════════════════════════════════════════════════════════════════════ │
│                │                                                                 │
│  ┌─────────────▼───────────────────────────────────────────────────────────────┐│
│  │  CORE AGENTS (11 - Cross-Stack)                                              ││
│  │  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐               ││
│  │  │ Felix │ │ Quinn │ │ Betty │ │ Eliza │ │ Diana │ │ Vicky │               ││
│  │  │ Arch  │ │Quality│ │ Bugs  │ │Estim. │ │ Docs  │ │Design │               ││
│  │  └───────┘ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘               ││
│  │  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐                         ││
│  │  │Marcus │ │ Tessa │ │Miguel │ │ Peter │ │ Paul  │                         ││
│  │  │Maint. │ │ Test  │ │Migrate│ │Product│ │ Plan  │                         ││
│  │  └───────┘ └───────┘ └───────┘ └───────┘ └───────┘                         ││
│  │                                                                              ││
│  │  STACK TEMPLATES: Python | TypeScript | .NET | Java | Go | Rust             ││
│  │  PLATFORM AGENTS: ObservabilityEngineer | PromptEngineer | ContextManager   ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                │                                                                 │
│  ══════════════════════════════════════════════════════════════════════════════ │
│  LAAG 4: BACKEND SERVICES (290+ Services)                                        │
│  ══════════════════════════════════════════════════════════════════════════════ │
│                │                                                                 │
│  ┌─────────────▼───────────────────────────────────────────────────────────────┐│
│  │  ANALYSIS SERVICES                      │  EXTRACTION SERVICES               ││
│  │  ┌─────────────────┐ ┌────────────────┐ │ ┌─────────────────┐ ┌────────────┐││
│  │  │Brown Paper Svc  │ │CWE Scanner     │ │ │Deep Extraction  │ │Hierarchical│││
│  │  │(6-fase enhanced)│ │Suite (95%)     │ │ │Pipeline         │ │Story Extr. │││
│  │  └─────────────────┘ └────────────────┘ │ └─────────────────┘ └────────────┘││
│  │  ┌─────────────────┐ ┌────────────────┐ │ ┌─────────────────┐ ┌────────────┐││
│  │  │FP Methodology   │ │Confucius Orch. │ │ │Business Rule    │ │CiRA Causal │││
│  │  │(IFPUG/NESMA)    │ │(PIV loop)      │ │ │Extractors (12)  │ │Detection   │││
│  │  └─────────────────┘ └────────────────┘ │ └─────────────────┘ └────────────┘││
│  │─────────────────────────────────────────┼────────────────────────────────────││
│  │  KNOWLEDGE SERVICES                     │  TESTING SERVICES                  ││
│  │  ┌─────────────────┐ ┌────────────────┐ │ ┌─────────────────┐ ┌────────────┐││
│  │  │Tech Stack KB    │ │Experience      │ │ │Characterization │ │Visual      │││
│  │  │[NIEUW]          │ │Store           │ │ │Tests (Golden M.)│ │Regression  │││
│  │  └─────────────────┘ └────────────────┘ │ └─────────────────┘ └────────────┘││
│  │  ┌─────────────────┐ ┌────────────────┐ │ ┌─────────────────┐ ┌────────────┐││
│  │  │Continuous       │ │Workflow Task   │ │ │Dual-Run         │ │Performance │││
│  │  │Learning         │ │Store [NIEUW]   │ │ │Comparison       │ │Baseline    │││
│  │  └─────────────────┘ └────────────────┘ │ └─────────────────┘ └────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                │                                                                 │
│  ══════════════════════════════════════════════════════════════════════════════ │
│  LAAG 5: LLM PROVIDER LAYER (CLI-First + 7 API Providers)                        │
│  ══════════════════════════════════════════════════════════════════════════════ │
│                │                                                                 │
│  ┌─────────────▼───────────────────────────────────────────────────────────────┐│
│  │                                                                              ││
│  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  CLI-FIRST (mq Workflows)                    PRIORITEIT: PRIMAIR        │││
│  │  │  ┌────────────────────────────────────────────────────────────────────┐ │││
│  │  │  │  claude --print --model {haiku|sonnet|opus}                        │ │││
│  │  │  │  └─► Max Subscription ($100/maand) - Voorspelbare kosten          │ │││
│  │  │  │  └─► Hogere rate limits                                            │ │││
│  │  │  │  └─► Native integratie met mq workflows                            │ │││
│  │  │  └────────────────────────────────────────────────────────────────────┘ │││
│  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │                                                                              ││
│  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  API PROVIDERS (Platform Services)           PRIORITEIT: SECUNDAIR      │││
│  │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐   │││
│  │  │  │ Ollama     │ │ Groq       │ │ Alibaba    │ │ Google Gemini      │   │││
│  │  │  │ (Local/Free│ │ (Fast 840  │ │ (Qwen 1M   │ │ (Flash/Pro)        │   │││
│  │  │  │ qwen,deep) │ │  TPS)      │ │  context)  │ │                    │   │││
│  │  │  └────────────┘ └────────────┘ └────────────┘ └────────────────────┘   │││
│  │  │  ┌────────────┐ ┌────────────┐ ┌────────────────────────────────────┐   │││
│  │  │  │ OpenAI     │ │ Moonshot   │ │ Anthropic API (Fallback)          │   │││
│  │  │  │ (GPT-5.2   │ │ (Kimi K2   │ │ (Claude Opus 4.5 - pay-per-use)   │   │││
│  │  │  │  Coding)   │ │  1T param) │ │                                    │   │││
│  │  │  └────────────┘ └────────────┘ └────────────────────────────────────┘   │││
│  │  └─────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                │                                                                 │
│  ══════════════════════════════════════════════════════════════════════════════ │
│  LAAG 6: DATA & OBSERVABILITY                                                    │
│  ══════════════════════════════════════════════════════════════════════════════ │
│                │                                                                 │
│  ┌─────────────▼───────────────────────────────────────────────────────────────┐│
│  │  DATABASES                              │  OBSERVABILITY                     ││
│  │  ┌─────────────────┐ ┌────────────────┐ │ ┌─────────────────┐ ┌────────────┐││
│  │  │PostgreSQL       │ │ChromaDB        │ │ │CCTrace          │ │Claude-Mem  │││
│  │  │(198+ tables)    │ │(Vector Store)  │ │ │(thinking blocks)│ │(11 tags)   │││
│  │  │Port: 5433       │ │Port: 8001      │ │ └─────────────────┘ └────────────┘││
│  │  └─────────────────┘ └────────────────┘ │ ┌─────────────────┐ ┌────────────┐││
│  │  ┌─────────────────┐ ┌────────────────┐ │ │Self-Evolution   │ │Token Cache │││
│  │  │Redis            │ │JSON Files      │ │ │(Experience Store│ │Metrics     │││
│  │  │(Celery Queue)   │ │(mq task state) │ │ │5 collections)   │ │            │││
│  │  └─────────────────┘ └────────────────┘ │ └─────────────────┘ └────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Doelarchitectuur (Zoom op mq Integratie)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MQ WORKFLOW INTEGRATIE DETAIL                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      mq CLI Layer (Developer UX)                    │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐ │ │
│  │  │ bugfix.sh   │ │ changes.sh  │ │ migration.sh│ │ analyze.sh   │ │ │
│  │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬───────┘ │ │
│  │         │               │               │               │          │ │
│  │         └───────────────┴───────┬───────┴───────────────┘          │ │
│  │                                 │                                   │ │
│  │                    ┌────────────┴────────────┐                     │ │
│  │                    │   platform-api.sh       │                     │ │
│  │                    │   (CLI → API Bridge)    │                     │ │
│  │                    └────────────┬────────────┘                     │ │
│  └─────────────────────────────────┼──────────────────────────────────┘ │
│                                    │                                    │
│                                    v                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │              MarQed.ai API Gateway (Integration Layer)              ││
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────────────┐ ││
│  │  │ Workflow API    │ │ Knowledge API   │ │ Validation API        │ ││
│  │  │ /api/v2/workflow│ │ /api/v2/knowledge│ │ /api/v2/validation   │ ││
│  │  └────────┬────────┘ └────────┬────────┘ └───────────┬───────────┘ ││
│  │           │                   │                      │             ││
│  │  ┌────────┴───────────────────┴──────────────────────┴───────────┐ ││
│  │  │                    Progress Dashboard                          │ ││
│  │  │                    /dashboard/workflows                        │ ││
│  │  └───────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                    │                                    │
│                                    v                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                  MarQed.ai Platform (Backend Services)              ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  ││
│  │  │ Brown Paper │ │ CWE Scanner │ │ FP Method.  │ │ Confucius    │  ││
│  │  │ Service     │ │ Suite       │ │ Service     │ │ Orchestrator │  ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └──────────────┘  ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  ││
│  │  │ Experience  │ │ Continuous  │ │ Visual      │ │ Performance  │  ││
│  │  │ Store       │ │ Learning    │ │ Regression  │ │ Baseline     │  ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └──────────────┘  ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  ││
│  │  │ Tech Stack  │ │ Workflow    │ │             │ │              │  ││
│  │  │ Knowledge   │ │ Task Store  │ │ PostgreSQL  │ │ ChromaDB     │  ││
│  │  │ [NIEUW]     │ │ [NIEUW]     │ │             │ │              │  ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └──────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Mapping: mq Workflows ↔ Platform Workflows

| mq Workflow | Platform Workflow | Primaire Agents | Backend Services |
|-------------|-------------------|-----------------|------------------|
| `marqed-bugfix.sh` | BUG | Betty → Tessa → Diana | CWE Scanner, Testing Services |
| `marqed-changes.sh` | NEW_FEATURE / ENHANCEMENT | Peter → Felix → Tessa → Diana | Deep Extraction, FP Methodology |
| `marqed-migration.sh` | BROWN_PAPER_ENHANCED + MIGRATION_ENHANCED | Miguel → Peter → Felix → Quinn → Eliza → Diana | Brown Paper (6-fase), 7-fase Migration |
| `marqed-analyze.sh` | QUALITY_AUDIT | Quinn → Felix → Marcus | Hybrid Static-LLM Pipeline, Business Rule Extractors |

### 6.4 Component Design

#### 6.4.1 Workflow API

**Locatie**: `backend/app/api/workflow_integration.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/v2/workflow", tags=["workflow"])

# ════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ════════════════════════════════════════════════════════════════════════

class WorkflowType(str, Enum):
    BUGFIX = "bugfix"
    CHANGES = "changes"
    MIGRATION = "migration"
    ANALYZE = "analyze"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"

class WorkflowCreateRequest(BaseModel):
    workflow_type: WorkflowType
    name: str
    description: Optional[str] = None
    codebase_path: str
    tech_stack: List[str] = []
    prd_content: Optional[str] = None

class WorkflowTaskCreate(BaseModel):
    title: str
    description: str
    phase: int
    estimated_time: Optional[str] = None
    dependencies: List[str] = []

class WorkflowResponse(BaseModel):
    id: str
    workflow_type: WorkflowType
    name: str
    status: str
    created_at: datetime
    tasks: List[TaskResponse]
    progress_percentage: float
    current_phase: int
    total_phases: int

# ════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════

@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowCreateRequest,
    db: Session = Depends(get_db),
    knowledge_service: TechStackKnowledgeService = Depends()
):
    """
    Create a new workflow with automatic knowledge lookup.

    1. Creates workflow record
    2. Looks up existing knowledge for tech stack
    3. Returns workflow with knowledge hints
    """
    # Check existing knowledge
    knowledge = await knowledge_service.find_similar_projects(
        tech_stack=request.tech_stack,
        problem_type=request.workflow_type.value
    )

    # Create workflow
    workflow = WorkflowModel(
        id=generate_workflow_id(request.workflow_type),
        workflow_type=request.workflow_type,
        name=request.name,
        codebase_path=request.codebase_path,
        tech_stack=request.tech_stack,
        knowledge_hints=knowledge.dict() if knowledge else None
    )

    db.add(workflow)
    db.commit()

    return WorkflowResponse.from_orm(workflow)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Get workflow details including all tasks and progress"""
    workflow = db.query(WorkflowModel).filter_by(id=workflow_id).first()
    if not workflow:
        raise HTTPException(404, f"Workflow {workflow_id} not found")
    return WorkflowResponse.from_orm(workflow)


@router.get("/{workflow_id}/tasks", response_model=List[TaskResponse])
async def get_workflow_tasks(workflow_id: str, db: Session = Depends(get_db)):
    """Get all tasks for a workflow"""
    tasks = db.query(WorkflowTaskModel).filter_by(workflow_id=workflow_id).all()
    return [TaskResponse.from_orm(t) for t in tasks]


@router.post("/{workflow_id}/tasks", response_model=TaskResponse)
async def create_task(
    workflow_id: str,
    task: WorkflowTaskCreate,
    db: Session = Depends(get_db)
):
    """Create a new task in workflow"""
    task_model = WorkflowTaskModel(
        workflow_id=workflow_id,
        **task.dict()
    )
    db.add(task_model)
    db.commit()
    return TaskResponse.from_orm(task_model)


@router.patch("/{workflow_id}/tasks/{task_id}")
async def update_task_status(
    workflow_id: str,
    task_id: str,
    status: TaskStatus,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update task status (called from CLI)"""
    task = db.query(WorkflowTaskModel).filter_by(
        workflow_id=workflow_id,
        id=task_id
    ).first()

    if not task:
        raise HTTPException(404, f"Task {task_id} not found")

    task.status = status
    if notes:
        task.notes = notes
    task.updated_at = datetime.utcnow()

    if status == TaskStatus.COMPLETED:
        task.completed_at = datetime.utcnow()

    db.commit()

    # Broadcast status update via WebSocket
    await broadcast_workflow_update(workflow_id)

    return {"status": "updated"}


@router.get("/active", response_model=List[WorkflowResponse])
async def get_active_workflows(db: Session = Depends(get_db)):
    """Get all active (non-completed) workflows for dashboard"""
    workflows = db.query(WorkflowModel).filter(
        WorkflowModel.status.in_(["pending", "in_progress"])
    ).order_by(WorkflowModel.created_at.desc()).all()

    return [WorkflowResponse.from_orm(w) for w in workflows]
```

#### 6.4.2 Tech Stack Knowledge Service

**Locatie**: `backend/app/services/techstack_knowledge_service.py`

```python
from typing import List, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.services.experience_store_service import ExperienceStoreService
from app.services.continuous_learning_service import ContinuousLearningService
from app.services.chroma_service import ChromaService


@dataclass
class KnowledgeResult:
    """Result of knowledge lookup for a tech stack"""
    similar_projects: List[dict]
    known_patterns: List[dict]
    pitfalls: List[dict]
    effort_estimate: Optional[dict]
    recommendations: List[str]


class TechStackKnowledgeService:
    """
    Service that looks up existing knowledge for a given tech stack
    and problem type.

    Bij start van elk project wordt automatisch gecheckt wat er al
    bekend is rondom deze techstack en/of problematiek.
    """

    def __init__(
        self,
        experience_store: ExperienceStoreService,
        learning_service: ContinuousLearningService,
        chroma_service: ChromaService,
        db: Session
    ):
        self.experience_store = experience_store
        self.learning_service = learning_service
        self.chroma = chroma_service
        self.db = db

    async def find_similar_projects(
        self,
        tech_stack: List[str],
        problem_type: str
    ) -> KnowledgeResult:
        """
        Find similar projects and extract relevant knowledge.

        Args:
            tech_stack: List of technologies (e.g., ["ASP Classic", "SQL Server"])
            problem_type: Type of work (e.g., "migration", "bugfix", "security")

        Returns:
            KnowledgeResult with similar projects, patterns, pitfalls, estimates
        """

        # 1. Search experience store for similar tech stacks
        experiences = await self._search_experiences(tech_stack, problem_type)

        # 2. Get learned patterns from continuous learning
        patterns = await self._get_patterns(tech_stack, problem_type)

        # 3. Search ChromaDB for semantically similar projects
        similar_projects = await self._semantic_search(tech_stack, problem_type)

        # 4. Extract pitfalls from past experiences
        pitfalls = self._extract_pitfalls(experiences, similar_projects)

        # 5. Calculate effort estimate based on history
        effort_estimate = self._calculate_effort_estimate(
            experiences,
            similar_projects,
            problem_type
        )

        # 6. Generate recommendations
        recommendations = self._generate_recommendations(
            tech_stack,
            problem_type,
            pitfalls,
            patterns
        )

        return KnowledgeResult(
            similar_projects=similar_projects,
            known_patterns=patterns,
            pitfalls=pitfalls,
            effort_estimate=effort_estimate,
            recommendations=recommendations
        )

    async def _search_experiences(
        self,
        tech_stack: List[str],
        problem_type: str
    ) -> List[dict]:
        """Search experience store for matching experiences"""
        query = {
            "tech_stack": {"$in": tech_stack},
            "problem_type": problem_type
        }
        return await self.experience_store.search(query, limit=10)

    async def _get_patterns(
        self,
        tech_stack: List[str],
        problem_type: str
    ) -> List[dict]:
        """Get learned patterns from continuous learning service"""
        patterns = []
        for tech in tech_stack:
            tech_patterns = await self.learning_service.get_patterns(
                tech,
                problem_type
            )
            patterns.extend(tech_patterns)
        return patterns

    async def _semantic_search(
        self,
        tech_stack: List[str],
        problem_type: str
    ) -> List[dict]:
        """Search ChromaDB for semantically similar projects"""
        query = f"{' '.join(tech_stack)} {problem_type}"

        results = await self.chroma.similarity_search(
            query=query,
            collection="project_knowledge",
            n_results=5
        )

        return [
            {
                "name": r.metadata.get("project_name"),
                "tech_stack": r.metadata.get("tech_stack"),
                "outcome": r.metadata.get("outcome"),
                "duration": r.metadata.get("duration"),
                "lessons": r.metadata.get("lessons_learned"),
                "similarity_score": r.score
            }
            for r in results
        ]

    def _extract_pitfalls(
        self,
        experiences: List[dict],
        similar_projects: List[dict]
    ) -> List[dict]:
        """Extract common pitfalls from past experiences"""
        pitfalls = []

        # From experiences
        for exp in experiences:
            if exp.get("pitfalls"):
                for pitfall in exp["pitfalls"]:
                    pitfalls.append({
                        "description": pitfall["description"],
                        "severity": pitfall.get("severity", "medium"),
                        "mitigation": pitfall.get("mitigation"),
                        "source": f"Experience: {exp.get('project_name')}"
                    })

        # From similar projects
        for proj in similar_projects:
            if proj.get("lessons"):
                for lesson in proj["lessons"]:
                    if lesson.get("type") == "pitfall":
                        pitfalls.append({
                            "description": lesson["description"],
                            "severity": lesson.get("severity", "medium"),
                            "mitigation": lesson.get("mitigation"),
                            "source": f"Project: {proj.get('name')}"
                        })

        # Deduplicate and rank by frequency
        return self._deduplicate_pitfalls(pitfalls)

    def _calculate_effort_estimate(
        self,
        experiences: List[dict],
        similar_projects: List[dict],
        problem_type: str
    ) -> Optional[dict]:
        """Calculate effort estimate based on historical data"""
        durations = []

        for exp in experiences:
            if exp.get("duration_hours"):
                durations.append(exp["duration_hours"])

        for proj in similar_projects:
            if proj.get("duration"):
                durations.append(proj["duration"])

        if not durations:
            return None

        import statistics

        return {
            "min_hours": min(durations),
            "max_hours": max(durations),
            "avg_hours": statistics.mean(durations),
            "median_hours": statistics.median(durations),
            "sample_size": len(durations),
            "confidence": "high" if len(durations) >= 5 else "medium" if len(durations) >= 3 else "low"
        }

    def _generate_recommendations(
        self,
        tech_stack: List[str],
        problem_type: str,
        pitfalls: List[dict],
        patterns: List[dict]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Based on pitfalls
        critical_pitfalls = [p for p in pitfalls if p.get("severity") == "critical"]
        if critical_pitfalls:
            recommendations.append(
                f"⚠️ CRITICAL: {len(critical_pitfalls)} critical pitfalls identified. "
                f"Review before starting."
            )

        # Based on patterns
        if patterns:
            recommendations.append(
                f"📚 {len(patterns)} proven patterns available for this tech stack."
            )

        # Tech-specific recommendations
        if "ASP Classic" in tech_stack:
            recommendations.append(
                "🔧 ASP Classic: Consider using VBScript analyzer for accurate LOC counts."
            )

        if "SQL Server" in tech_stack:
            recommendations.append(
                "🗄️ SQL Server: Run stored procedure analyzer before migration planning."
            )

        return recommendations

    def _deduplicate_pitfalls(self, pitfalls: List[dict]) -> List[dict]:
        """Deduplicate pitfalls and rank by frequency"""
        seen = {}
        for pitfall in pitfalls:
            key = pitfall["description"][:50]  # First 50 chars as key
            if key in seen:
                seen[key]["count"] += 1
            else:
                pitfall["count"] = 1
                seen[key] = pitfall

        # Sort by count (most frequent first) then by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(
            seen.values(),
            key=lambda x: (x["count"] * -1, severity_order.get(x["severity"], 2))
        )
```

#### 6.4.3 CLI Bridge

**Locatie**: `mq/workflows/common/platform-api.sh`

```bash
#!/bin/bash
# platform-api.sh - CLI bridge to MarQed.ai Platform API
# Version 1.0

set -e

# Configuration
MARQED_API_URL="${MARQED_API_URL:-http://localhost:8003}"
MARQED_API_KEY="${MARQED_API_KEY:-}"

# ════════════════════════════════════════════════════════════════════════
# PLATFORM CONNECTION
# ════════════════════════════════════════════════════════════════════════

check_platform_required() {
    echo "🔍 Checking MarQed.ai Platform connection..."

    if ! curl -s --connect-timeout 5 "${MARQED_API_URL}/health" > /dev/null 2>&1; then
        echo ""
        echo "❌ ERROR: MarQed.ai Platform is niet bereikbaar"
        echo ""
        echo "   De mq workflows vereisen een draaiend platform voor:"
        echo "   • Security scanning (CWE Scanner)"
        echo "   • Code analysis (Brown Paper)"
        echo "   • Task persistence (PostgreSQL)"
        echo "   • Knowledge lookup (ChromaDB)"
        echo "   • Progress Dashboard"
        echo ""
        echo "   Start het platform met:"
        echo "   $ make start"
        echo ""
        echo "   Of:"
        echo "   $ ./scripts/marqed-services.sh start"
        echo ""
        exit 1
    fi

    echo "✅ Platform connection OK"
}

# ════════════════════════════════════════════════════════════════════════
# API CALLS
# ════════════════════════════════════════════════════════════════════════

marqed_api_call() {
    local endpoint="$1"
    local method="${2:-GET}"
    local data="$3"

    local auth_header=""
    if [[ -n "${MARQED_API_KEY}" ]]; then
        auth_header="-H \"Authorization: Bearer ${MARQED_API_KEY}\""
    fi

    local response
    if [[ -n "${data}" ]]; then
        response=$(curl -s -X "${method}" \
            -H "Content-Type: application/json" \
            ${auth_header} \
            -d "${data}" \
            "${MARQED_API_URL}${endpoint}")
    else
        response=$(curl -s -X "${method}" \
            -H "Content-Type: application/json" \
            ${auth_header} \
            "${MARQED_API_URL}${endpoint}")
    fi

    echo "${response}"
}

# ════════════════════════════════════════════════════════════════════════
# WORKFLOW MANAGEMENT
# ════════════════════════════════════════════════════════════════════════

create_workflow() {
    local workflow_type="$1"
    local name="$2"
    local codebase_path="$3"
    local tech_stack="$4"  # JSON array

    local data=$(cat <<EOF
{
    "workflow_type": "${workflow_type}",
    "name": "${name}",
    "codebase_path": "${codebase_path}",
    "tech_stack": ${tech_stack:-[]}
}
EOF
)

    marqed_api_call "/api/v2/workflow/" "POST" "${data}"
}

get_workflow() {
    local workflow_id="$1"
    marqed_api_call "/api/v2/workflow/${workflow_id}"
}

update_task_status() {
    local workflow_id="$1"
    local task_id="$2"
    local status="$3"
    local notes="${4:-}"

    local data="{\"status\": \"${status}\""
    if [[ -n "${notes}" ]]; then
        data="${data}, \"notes\": \"${notes}\""
    fi
    data="${data}}"

    marqed_api_call "/api/v2/workflow/${workflow_id}/tasks/${task_id}" "PATCH" "${data}"
}

# ════════════════════════════════════════════════════════════════════════
# KNOWLEDGE LOOKUP
# ════════════════════════════════════════════════════════════════════════

lookup_existing_knowledge() {
    local tech_stack="$1"  # JSON array
    local problem_type="$2"

    echo "🔍 Checking existing knowledge for tech stack..."
    echo ""

    local data=$(cat <<EOF
{
    "tech_stack": ${tech_stack},
    "problem_type": "${problem_type}"
}
EOF
)

    local result=$(marqed_api_call "/api/v2/knowledge/lookup" "POST" "${data}")

    # Parse and display results
    local similar_count=$(echo "${result}" | jq '.similar_projects | length')
    local pitfall_count=$(echo "${result}" | jq '.pitfalls | length')
    local pattern_count=$(echo "${result}" | jq '.known_patterns | length')

    if [[ "${similar_count}" -gt 0 ]]; then
        echo "📚 Found ${similar_count} similar projects!"
        echo ""
        echo "Similar Projects:"
        echo "${result}" | jq -r '.similar_projects[] | "  • \(.name): \(.outcome) (similarity: \(.similarity_score | . * 100 | floor)%)"'
        echo ""
    fi

    if [[ "${pitfall_count}" -gt 0 ]]; then
        echo "⚠️  Known Pitfalls (${pitfall_count}):"
        echo "${result}" | jq -r '.pitfalls[] | "  • [\(.severity | ascii_upcase)] \(.description)"'
        echo ""
    fi

    if [[ "${pattern_count}" -gt 0 ]]; then
        echo "📐 Available Patterns (${pattern_count}):"
        echo "${result}" | jq -r '.known_patterns[:3][] | "  • \(.name): \(.description)"'
        echo ""
    fi

    # Display effort estimate
    local estimate=$(echo "${result}" | jq '.effort_estimate')
    if [[ "${estimate}" != "null" ]]; then
        echo "⏱️  Effort Estimate:"
        echo "   Min: $(echo "${estimate}" | jq -r '.min_hours')h"
        echo "   Max: $(echo "${estimate}" | jq -r '.max_hours')h"
        echo "   Avg: $(echo "${estimate}" | jq -r '.avg_hours | floor')h"
        echo "   Confidence: $(echo "${estimate}" | jq -r '.confidence')"
        echo ""
    fi

    # Display recommendations
    echo "💡 Recommendations:"
    echo "${result}" | jq -r '.recommendations[] | "  \(.)"'
    echo ""

    # Return full result for further processing
    echo "${result}"
}

# ════════════════════════════════════════════════════════════════════════
# SECURITY SCANNING
# ════════════════════════════════════════════════════════════════════════

run_security_scan() {
    local codebase_path="$1"
    local scan_type="${2:-full}"

    echo "🔒 Running security scan via CWE Scanner..."

    local data=$(cat <<EOF
{
    "path": "${codebase_path}",
    "scan_type": "${scan_type}"
}
EOF
)

    marqed_api_call "/api/v2/security/scan" "POST" "${data}"
}

# ════════════════════════════════════════════════════════════════════════
# VALIDATION
# ════════════════════════════════════════════════════════════════════════

run_visual_regression() {
    local workflow_id="$1"
    local screenshot_path="$2"

    echo "📸 Running visual regression check..."

    local data=$(cat <<EOF
{
    "workflow_id": "${workflow_id}",
    "screenshot_path": "${screenshot_path}"
}
EOF
)

    marqed_api_call "/api/v2/validation/visual-regression" "POST" "${data}"
}

run_performance_baseline() {
    local workflow_id="$1"
    local endpoint="$2"

    echo "⚡ Checking performance baseline..."

    local data=$(cat <<EOF
{
    "workflow_id": "${workflow_id}",
    "endpoint": "${endpoint}"
}
EOF
)

    marqed_api_call "/api/v2/validation/performance" "POST" "${data}"
}

# ════════════════════════════════════════════════════════════════════════
# SYNC TASKS TO PLATFORM
# ════════════════════════════════════════════════════════════════════════

sync_tasks_to_platform() {
    local workflow_id="$1"
    local task_file="${HOME}/.claude/tasks/${workflow_id}.json"

    if [[ ! -f "${task_file}" ]]; then
        echo "⚠️  Task file not found: ${task_file}"
        return 1
    fi

    echo "📤 Syncing tasks to platform..."

    local tasks=$(cat "${task_file}")
    marqed_api_call "/api/v2/workflow/${workflow_id}/tasks/bulk" "POST" "${tasks}"

    echo "✅ Tasks synced successfully"
}

# ════════════════════════════════════════════════════════════════════════
# MAIN (for testing)
# ════════════════════════════════════════════════════════════════════════

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "MarQed.ai Platform API Bridge"
    echo "Usage: source this file to use the functions"
    echo ""
    echo "Available functions:"
    echo "  check_platform_required"
    echo "  create_workflow <type> <name> <codebase> [tech_stack]"
    echo "  get_workflow <workflow_id>"
    echo "  update_task_status <workflow_id> <task_id> <status> [notes]"
    echo "  lookup_existing_knowledge <tech_stack> <problem_type>"
    echo "  run_security_scan <codebase_path> [scan_type]"
    echo "  run_visual_regression <workflow_id> <screenshot_path>"
    echo "  run_performance_baseline <workflow_id> <endpoint>"
    echo "  sync_tasks_to_platform <workflow_id>"
fi
```

#### 6.4.4 LLM Provider Architecture

**Locatie**: `backend/app/services/extraction_llm_adapter.py`

De LLM-integratie volgt een **CLI-first** aanpak met API fallback:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LLM PROVIDER ARCHITECTUUR                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    mq Workflows / Platform Services                 │ │
│  │                                                                     │ │
│  │  - marqed-bugfix.sh                                                │ │
│  │  - marqed-changes.sh                                               │ │
│  │  - ExtractionLLMAdapter                                            │ │
│  │  - TechStackKnowledgeService                                       │ │
│  └──────────────────────────────┬─────────────────────────────────────┘ │
│                                 │                                        │
│                                 v                                        │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    LLM Provider Selector                            │ │
│  │                                                                     │ │
│  │  1. Check: shutil.which("claude")                                  │ │
│  │     ├─ FOUND → Claude CLI (Abonnement)                             │ │
│  │     │          └─ cmd = ["claude", "--print", "--model", model]    │ │
│  │     │          └─ Gebruikt Max subscription ($100/maand)           │ │
│  │     │                                                              │ │
│  │     └─ NOT FOUND → API Fallback                                    │ │
│  │                    └─ ANTHROPIC_API_KEY required                   │ │
│  │                    └─ Pay-per-use ($15-75 per 1M tokens)           │ │
│  └──────────────────────────────┬─────────────────────────────────────┘ │
│                                 │                                        │
│                                 v                                        │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    Claude Opus 4.5 Model                            │ │
│  │                                                                     │ │
│  │  ✓ Identieke kwaliteit ongeacht provider                          │ │
│  │  ✓ Hogere rate limits bij Max abonnement                          │ │
│  │  ✓ Voorspelbare kosten met subscription                           │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Configuratie**:

```python
# backend/app/services/extraction_llm_adapter.py

class LLMProviderSelector:
    """
    CLI-first provider selection.

    Bij Max abonnement: ~60% kostenbesparing vs pay-per-use
    bij gemiddeld 50K tokens/dag gebruik.
    """

    def select_provider(self, model: str) -> Tuple[str, callable]:
        # 1. Prefer CLI (subscription)
        if shutil.which("claude"):
            return ("cli", self._call_claude_cli)

        # 2. Fallback to API (pay-per-use)
        if os.getenv("ANTHROPIC_API_KEY"):
            return ("api", self._call_anthropic_api)

        raise LLMProviderError("No LLM provider available")
```

**Model Mapping**:

| Tier | CLI Model | API Model | Use Case |
|------|-----------|-----------|----------|
| Haiku | `haiku` | `claude-3-5-haiku-20241022` | Quick tasks |
| Sonnet | `sonnet` | `claude-3-5-sonnet-20241022` | Standard work |
| Opus | `opus` | `claude-opus-4-5-20251101` | Complex analysis |

---

## 7. Database Design

### 7.1 Workflow Tables

```sql
-- Alembic migration: workflow_integration_tables

-- Workflow hoofdtabel
CREATE TABLE workflow (
    id VARCHAR(50) PRIMARY KEY,              -- e.g., BUG-2026-01-24-001
    workflow_type VARCHAR(20) NOT NULL,       -- bugfix, changes, migration, analyze
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',     -- pending, in_progress, completed, failed
    codebase_path VARCHAR(500),
    tech_stack JSONB DEFAULT '[]',
    knowledge_hints JSONB,                    -- Results from knowledge lookup
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    created_by VARCHAR(100)
);

-- Workflow tasks
CREATE TABLE workflow_task (
    id VARCHAR(50) PRIMARY KEY,
    workflow_id VARCHAR(50) REFERENCES workflow(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    phase INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    estimated_time VARCHAR(20),
    actual_time_minutes INTEGER,
    dependencies JSONB DEFAULT '[]',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Workflow logs (for dashboard)
CREATE TABLE workflow_log (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(50) REFERENCES workflow(id) ON DELETE CASCADE,
    task_id VARCHAR(50),
    level VARCHAR(10) DEFAULT 'info',         -- debug, info, warning, error
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_workflow_status ON workflow(status);
CREATE INDEX idx_workflow_type ON workflow(workflow_type);
CREATE INDEX idx_workflow_created ON workflow(created_at DESC);
CREATE INDEX idx_task_workflow ON workflow_task(workflow_id);
CREATE INDEX idx_task_status ON workflow_task(status);
CREATE INDEX idx_log_workflow ON workflow_log(workflow_id);
CREATE INDEX idx_log_created ON workflow_log(created_at DESC);
```

### 7.2 Knowledge Tables (Extension)

```sql
-- Project knowledge for similarity search
CREATE TABLE project_knowledge (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    tech_stack JSONB NOT NULL,
    problem_type VARCHAR(50),
    outcome VARCHAR(50),                      -- success, partial, failed
    duration_hours INTEGER,
    lessons_learned JSONB DEFAULT '[]',
    pitfalls JSONB DEFAULT '[]',
    patterns_used JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for tech stack search
CREATE INDEX idx_knowledge_tech ON project_knowledge USING GIN(tech_stack);
CREATE INDEX idx_knowledge_type ON project_knowledge(problem_type);
```

---

## 8. Success Criteria

### 8.1 Fase 1 Validatie Checklist

Voordat we naar Fase 2 (Parallel Coordinator) gaan, MOET het volgende gevalideerd zijn:

| # | Criterium | Validatie Methode | Target |
|---|-----------|-------------------|--------|
| 1 | Alle workflows werken sequentieel | E2E test | 100% pass |
| 2 | Dashboard toont correcte status | Manual + automated | Real-time <2s |
| 3 | Knowledge lookup geeft resultaten | Test met bekende stacks | >60% hit rate |
| 4 | Self-validation detecteert regressies | Test met bekende issues | >90% detection |
| 5 | Platform health check werkt | Test offline scenario | Duidelijke error |
| 6 | Task persistence werkt | Kill/resume test | 100% recovery |
| 7 | Geen kritieke bugs | Bug tracking | 0 P1 bugs |
| 8 | Documentation compleet | Review | 100% coverage |

### 8.2 KPI's

| KPI | Target | Meetmethode |
|-----|--------|-------------|
| Workflow Success Rate | >90% | Automated metrics |
| Developer Satisfaction | >4/5 | Survey |
| Security Coverage | >95% | CWE Scanner report |
| Knowledge Reuse Rate | >60% | Lookup hit rate |
| Dashboard Response Time | <2s | Performance monitoring |
| Task Sync Reliability | >99.9% | Error rate tracking |

---

## 9. Risico Register

| ID | Risico | Kans | Impact | Score | Status | Mitigatie |
|----|--------|------|--------|-------|--------|-----------|
| R1 | Platform niet beschikbaar | Low | Critical | 4 | Gemitigeerd | Health check + duidelijke error |
| R2 | Integration complexity | Medium | Medium | 4 | Open | Incrementele aanpak |
| R3 | Knowledge lookup irrelevant | Medium | Low | 3 | Open | Tuning na launch |
| R4 | Dashboard performance | Low | Medium | 2 | Open | WebSocket ipv polling |
| R5 | Fase 1 duurt langer | Medium | Medium | 4 | Open | Buffer in planning |

---

## 10. Appendix

### A. Afgewezen Items (Referentie)

| # | Item | Status | Reden | Heroverweging |
|---|------|--------|-------|---------------|
| 1 | IDE Plugin | ❌ AFGEWEZEN | Dashboard + CLI voldoende | Nooit |
| 2 | Offline Mode | ❌ AFGEWEZEN | Kwaliteit voorop, platform moet draaien | Nooit |
| 3 | Platform Vervanging | ❌ AFGEWEZEN | Verlies 290+ services | Nooit |
| 4 | Real-time Collaboration | ❌ AFGEWEZEN | Over-engineering | Nooit |

### B. Toekomstige Items (Na Fase 1 Validatie)

| # | Item | Status | Voorwaarde |
|---|------|--------|------------|
| 1 | Parallel Execution Coordinator | ⏳ NIET INGEPLAND | Fase 1 100% gevalideerd |
| 2 | GitOps Native Integration | ⏳ NIET INGEPLAND | Fase 1 100% gevalideerd |

### C. Glossary

| Term | Definitie |
|------|-----------|
| mq | MarQed CLI workflows (bash scripts) |
| Platform | MarQed.ai FastAPI backend |
| Workflow | Een bugfix, changes, migration of analyze sessie |
| Task | Een individuele stap binnen een workflow |
| Phase | Een groep gerelateerde tasks |
| Knowledge Lookup | Automatisch zoeken naar eerdere ervaring |

### D. Gerelateerde Documenten

Dit document maakt deel uit van een documentatieset voor de mq + Platform integratie:

| Document | Beschrijving | Locatie |
|----------|--------------|---------|
| **Unified Architecture Diagram** | Geïntegreerd architectuurplaatje met unified entry point voor alle workflows | [`unified-architecture-diagram.md`](./unified-architecture-diagram.md) |
| **Plan van Aanpak** | Gedetailleerd plan met 5 epics, 18 user stories, technische taken per story | [`mq-integration-plan-van-aanpak.md`](./mq-integration-plan-van-aanpak.md) |
| **Roadmap Breakdown** | Week-voor-week planning (Week 146-154), milestones, success metrics | [`mq-integration-roadmap.md`](./mq-integration-roadmap.md) |

#### Document Relaties

```
marqed-platform-and-mq-analysis.md (DIT DOCUMENT)
    │
    ├── Strategische Analyse & Gap Assessment
    ├── Goedgekeurde Verbeteringen (V1-V4)
    ├── Architectuur Design
    └── Database Design
        │
        ├─────────────────────────────────────────────┐
        │                                              │
        v                                              v
unified-architecture-diagram.md              mq-integration-plan-van-aanpak.md
    │                                              │
    ├── Unified Entry Point                        ├── 5 Epics (E1-E5)
    ├── Workflow Type Details                      ├── 18 User Stories
    ├── Frontend <-> Backend Connectie             ├── Technische Taken
    ├── Data Flow Diagrams                         ├── Resource Planning
    └── Complete System Architecture               └── Risico Register
                    │                                       │
                    └───────────────┬───────────────────────┘
                                    │
                                    v
                      mq-integration-roadmap.md
                          │
                          ├── Week 146-154 Planning
                          ├── 5 Milestones (M1-M5)
                          ├── Success Metrics per Milestone
                          └── Agent Allocatie per Week
```

---

**Document Status**: Final v4.3
**Goedgekeurd door**: Architect Agent, Analysis Agent, PM Agent
**Datum**: 2026-01-24
**Next Review**: Na Fase 1 validatie

---

*MarQed.ai Platform Team*
