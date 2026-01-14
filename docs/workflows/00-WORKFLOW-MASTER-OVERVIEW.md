# MarQed AI Agent Platform - Workflow Master Overview

## Platform Statistics

| Category | Count |
|----------|-------|
| AI Agents | 11 |
| Workflows | 15+ |
| API Endpoints | 720+ |
| Dashboards | 40 |
| LLM Providers | 7 |
| Database Tables | 65+ |

---

## Domain Architecture (v2)

**Specification:** [workflow-separation-plan.md](../architecture/workflow-separation-plan.md)

```
              +-------------------------+
              |  Shared Infrastructure  |
              |  (Stability, Metrics)   |
              +-----------+-------------+
                          |
    +---------------------+---------------------+
    |                     |                     |
    v                     v                     v
+--------+          +----------+          +---------+
| BROWN  |          | MIGRATION|          | QUALITY |
| PAPER  |          | (Exec)   |          | (Valid) |
| Domain |          | Domain   |          | Domain  |
+--------+          +----------+          +---------+
    |                     |                     |
    +----------+----------+----------+----------+
               |                     |
               v                     v
    +-------------------------------------+
    |       ANALYSIS CONTRACT             |
    | { analysis_id, domains, modules,    |
    |   stability, epics, business_rules }|
    +-------------------------------------+
```

### Domain Responsibilities

| Domain | Responsibility | API Version |
|--------|----------------|-------------|
| **Brown Paper** | Code analysis, domain extraction, constitution | v1 + v2 |
| **Migration** | 7-phase execution, agent orchestration | v2 (analysis_id) |
| **Quality** | Validation, periodic scans, 42 rules | v2 (independent) |

### Quality Flow: 3 Execution Modes

| Mode | Trigger | Use Case |
|------|---------|----------|
| **Standalone** | `/api/v2/quality/scans/run` | Direct scan on any project |
| **Integrated** | Brown Paper Phase 1 | Automatic stability analysis |
| **Scheduled** | `/api/v2/quality/schedules` | Daily/weekly audit scans |

---

## Software Lifecycle Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SOFTWARE LIFECYCLE                                     │
│                                                                                  │
│    ┌──────────────┐         ┌──────────────┐                                    │
│    │ GREEN PAPER  │         │ BROWN PAPER  │                                    │
│    │ (nieuwbouw)  │         │ (bestaand)   │                                    │
│    │              │         │              │                                    │
│    │ Entry:       │         │ Entry:       │                                    │
│    │ project-     │         │ brown-paper- │                                    │
│    │ wizard.html  │         │ dashboard    │                                    │
│    └──────┬───────┘         └──────┬───────┘                                    │
│           │                        │                                            │
│           │                        ├────────────────┐                           │
│           │                        │                │                           │
│           │                        v                v                           │
│           │              ┌──────────────┐  ┌──────────────┐                     │
│           │              │  MIGRATION   │  │   Direct     │                     │
│           │              │ (migratie)   │  │   naar       │                     │
│           │              │              │  │   KANBAN     │                     │
│           │              │ Entry:       │  │              │                     │
│           │              │ migration-   │  │ (geen legacy │                     │
│           │              │ analyzer     │  │  migratie)   │                     │
│           │              └──────┬───────┘  └──────┬───────┘                     │
│           │                     │                 │                             │
│           └─────────────────────┼─────────────────┘                             │
│                                 │                                               │
│                                 v                                               │
│                       ┌──────────────────┐                                      │
│                       │      KANBAN      │                                      │
│                       │  (implementatie) │                                      │
│                       └────────┬─────────┘                                      │
│                                │                                                │
│                                v                                                │
│                       ┌──────────────────┐                                      │
│                       │   MAINTENANCE    │◄───────────────────┐                 │
│                       │   (onderhoud)    │                    │                 │
│                       │                  │                    │                 │
│                       │ Entry:           │                    │                 │
│                       │ maintenance-     │                    │                 │
│                       │ scheduler        │                    │                 │
│                       └────────┬─────────┘                    │                 │
│                                │                              │                 │
│              ┌─────────────────┼─────────────────┐            │                 │
│              │                 │                 │            │                 │
│              v                 v                 v            │                 │
│        ┌──────────┐    ┌─────────────┐   ┌──────────┐        │                 │
│        │   BUG    │    │ NEW_FEATURE │   │ MIGRATION│        │                 │
│        │ (defect) │    │(verbetering)│   │(herstart)│        │                 │
│        └────┬─────┘    └──────┬──────┘   └────┬─────┘        │                 │
│             │                 │               │              │                 │
│             └─────────────────┴───────────────┘              │                 │
│                               │                              │                 │
│                               └──────────────────────────────┘                 │
│                                       (terug naar KANBAN)                      │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Workflow Decision Tree

```
                          +------------------+
                          |   PROJECT TYPE   |
                          +--------+---------+
                                   |
         +----------+--------------+-------------+----------+
         |          |              |             |          |
    +----v----+ +---v---+    +-----v-----+ +-----v-----+ +--v---+
    |GREENFIELD| |LEGACY |    |ENHANCEMENT| |MAINTENANCE| | BUG  |
    |(nieuwbouw)|(bestaand)|   |(verbetering)|(onderhoud)| |(fout)|
    +----+----+ +---+---+    +-----+-----+ +-----+-----+ +--+---+
         |          |              |             |          |
         v          v              v             v          v
    GREEN_PAPER  BROWN_PAPER   NEW_FEATURE   MAINTENANCE   BUG
    Workflow     Workflow      Workflow      Workflow    Workflow
```

---

## Workflow Categories

### 1. Greenfield Projects (GREEN_PAPER)
**Use Case**: New systems from scratch
**Entry Point**: `/api/green-paper/sessions`

```
User Vision
    |
    v
+-------------------+     +-------------------+     +-------------------+
| 6 Discovery Qs    | --> | Peter: Constitution| --> | Felix: HLD Spec   |
| (What/Why/How)    |     | (deepseek-r1)     |     | (qwen2.5-coder)   |
+-------------------+     +-------------------+     +-------------------+
                                                            |
                                                            v
                                              +-------------------+
                                              | Epics/Stories/Tasks|
                                              | (Task Generation)  |
                                              +-------------------+
```

### 2. Brownfield Projects (BROWN_PAPER)
**Use Case**: Existing systems analysis
**Entry Point**: `/api/brown-paper/sessions`

```
Existing Code
    |
    v
+-------------------+     +-------------------+     +-------------------+
| 6-Phase Analysis  | --> | Hierarchical      | --> | Deep Extraction   |
| (Dependency,Code) |     | Extraction        |     | (LLM Council)     |
+-------------------+     +-------------------+     +-------------------+
                                                            |
                                                            v
                                              +-------------------+
                                              | Estimation (Eliza)|
                                              | FP/SP Analysis    |
                                              +-------------------+
```

### 3. Migration Projects
**Use Case**: Legacy modernization
**Entry Point**: `/api/brown-paper/bmad/start`

```
Legacy System
    |
    v
+-------------------+     +-------------------+     +-------------------+
| 8 Migration Qs    | --> | Miguel: Analysis  | --> | Peter: Spec       |
| (Current/Target)  |     | (Risk Assessment) |     | (Migration Plan)  |
+-------------------+     +-------------------+     +-------------------+
                                                            |
                                                            v
                                              +-------------------+
                                              | Felix: Tasks      |
                                              | (Migration Epics) |
                                              +-------------------+
```

### 4. Maintenance (MAINTENANCE)
**Use Case**: Technical debt, updates, refactoring
**Entry Point**: `/api/workflows/maintenance`
**Prerequisite**: Project must exist (via GREEN_PAPER or BROWN_PAPER → KANBAN)

```
Maintenance Request
    |
    v
+-------------------+     +-------------------+     +-------------------+
| Marcus: Scan      | --> | Quinn: Quality    | --> | Task Assignment   |
| (Debt Detection)  |     | (Review)          |     | (Prioritized)     |
+-------------------+     +-------------------+     +-------------------+
```

**From MAINTENANCE, choose:**
- **BUG**: Defect resolution
- **NEW_FEATURE**: Add functionality to existing project
- **MIGRATION**: Restart lifecycle (legacy modernization)

### 5. Enhancement/Features (NEW_FEATURE)
**Use Case**: Adding features to existing systems
**Entry Point**: From MAINTENANCE only (`/api/workflows/new-feature`)
**Prerequisite**: Project must be in MAINTENANCE phase

```
From MAINTENANCE
    |
    v
+-------------------+     +-------------------+     +-------------------+
| Quinn: Analysis   | --> | Felix: Design     | --> | Task Generation   |
| (Impact, Risk)    |     | (Architecture)    |     | (Epics/Stories)   |
+-------------------+     +-------------------+     +-------------------+
                                                            |
                                                            v
                                              +-------------------+
                                              | Back to KANBAN    |
                                              +-------------------+
```

### 6. Bug Fixing (BUG)
**Use Case**: Defect resolution
**Entry Point**: `/api/workflows/bug`

```
Bug Report
    |
    v
+-------------------+     +-------------------+     +-------------------+
| Betty: Triage     | --> | Tessa: Test       | --> | Fix + Verify      |
| (Root Cause)      |     | (Reproduce)       |     | (Regression)      |
+-------------------+     +-------------------+     +-------------------+
```

---

## Agent Overview

| Agent | Role | Primary Model | Workflows |
|-------|------|---------------|-----------|
| **Peter** | Product Owner | deepseek-r1:latest | GREEN_PAPER, BROWN_PAPER, Migration |
| **Felix** | Feature Architect | qwen2.5-coder:7b | Task Generation, Architecture |
| **Quinn** | Quality Analyst | codellama:7b | Quality, Security Review |
| **Betty** | Bug Hunter | mistral:7b | BUG, Triage |
| **Eliza** | Estimator | deepseek-r1:latest | FP/SP Estimation |
| **Diana** | Documentation | qwen2.5-coder:7b | Reports, Docs |
| **Marcus** | Maintenance | codellama:7b | Tech Debt, Refactoring |
| **Tessa** | Test Architect | qwen2.5-coder:7b | Testing, QA |
| **Miguel** | Migration Specialist | deepseek-r1:latest | Legacy Analysis |
| **Paul** | Project Manager | mistral:7b | Planning, Coordination |
| **Vicky** | UX Designer | qwen2.5-coder:7b | UI/UX, Design |

---

## Database Persistence Matrix

| Workflow | Session Table | Results Storage | Resume Support |
|----------|---------------|-----------------|----------------|
| GREEN_PAPER | green_paper_sessions | green_paper_answers, constitutions, specifications | Yes (status tracking) |
| BROWN_PAPER | brown_paper_sessions | brown_paper_analyses, domains, epics | Yes (6-phase cached) |
| Migration | bmad_sessions | JSONB (answers, analysis, spec, tasks) | Yes (can_resume) |
| NEW_FEATURE | items | spec_shaping, task_hierarchy | Yes |
| MAINTENANCE | items | technical_debt, code_analysis | Yes |
| BUG | items | bug table | Yes |

---

## API Prefix Summary

| Workflow | API Prefix | Primary Routes |
|----------|------------|----------------|
| Green Paper | `/api/green-paper` | sessions, answers, constitutions, specifications |
| Brown Paper | `/api/brown-paper` | sessions, analyze, constitution, epics |
| Task Generation | `/api/task-generation` | specifications/{id}/epics, hierarchy |
| Kanban | `/api/kanban` | items, lanes, filters |
| Estimation | `/api/estimation` | fp-analysis, story-points |
| Quality | `/api/quality` | gates, evaluation, metrics |

---

## Dashboard to Workflow Mapping

| Dashboard | Primary Workflow | Data Sources |
|-----------|------------------|--------------|
| brown-paper-dashboard.html | GREEN_PAPER, BROWN_PAPER | green_paper_sessions, brown_paper_sessions |
| kanban-dashboard.html | All | items, task_hierarchy |
| estimation-dashboard.html | BROWN_PAPER | estimation_history, fp_estimation |
| quality-dashboard.html | MAINTENANCE | code_analysis, quality_gates |
| migration-analyzer.html | Migration | bmad_sessions, migration_* |
| deep-extraction.html | BROWN_PAPER | deep_extraction, hierarchical_extraction |
| workflow-dashboard.html | All | workflow_executions |
| security-dashboard.html | All | ghostcrew_results, security |
| evolution-dashboard.html | All | agent_evolution, ab_testing |

---

## Development Methodology & Track Selection

The platform follows a 4-phase development methodology. Choose the right **track** based on project size:

### Scale-Adaptive Tracks

| Track | Story Count | Flow | Use Case |
|-------|-------------|------|----------|
| **Quick Flow** | 1-15 | tech-spec → Implementation | Bug fixes, simple changes |
| **Standard** | 10-50+ | PRD → Architecture → Epics → Implementation | Products, platforms |
| **Enterprise** | 30+ | PRD → Extended Solutioning → Implementation | Complex enterprise systems |

### Development Phases

| Phase | Purpose | Workflows | When to Skip |
|-------|---------|-----------|--------------|
| **Phase 1: Analysis** | Strategic discovery | brainstorm, research, product-brief | Clear requirements exist |
| **Phase 2: Planning** | Define what to build | workflow-init, prd, tech-spec, ux-design | Never (required) |
| **Phase 3: Solutioning** | Define how to build | architecture, create-epics-stories, impl-readiness | Quick Flow track |
| **Phase 4: Implementation** | Build the solution | sprint-planning, dev-story, code-review | Never (required) |

### Gate Check Criteria (Phase 3 → 4)

| Result | Meaning | Action |
|--------|---------|--------|
| **PASS** | All requirements covered, no conflicts | Proceed to implementation |
| **CONCERNS** | Minor gaps identified | Proceed with caution, document risks |
| **FAIL** | Critical issues found | Block until resolved |

### Phase Integration Flow
```
Phase 1: Analysis          Phase 2: Planning         Phase 3: Solutioning      Phase 4: Implementation
+------------------+       +------------------+      +------------------+       +------------------+
| brainstorm       |  -->  | workflow-init    | -->  | architecture     |  -->  | sprint-planning  |
| research         |       | tech-spec/prd    |      | create-epics     |       | dev-story        |
| product-brief    |       | create-ux-design |      | impl-readiness   |       | code-review      |
+------------------+       +------------------+      +------------------+       +------------------+
     (Optional)                (Required)          (Standard/Enterprise)          (Required)
```

---

## Quick Start

### Start a Green Paper Session
```bash
POST /api/green-paper/sessions
{
  "project_id": "PROJECT-001",
  "metadata": {"initiated_by": "user"}
}
```

### Start a Brown Paper Session
```bash
POST /api/brown-paper/sessions
{
  "application_id": "APP-001"
}
```

### Start a Migration Analysis
```bash
POST /api/brown-paper/bmad/start
{
  "project_name": "Legacy App",
  "project_path": "/path/to/code"
}
```

---

## Document Index

| Document | Description |
|----------|-------------|
| [01-GREEN-PAPER-WORKFLOW.md](./01-GREEN-PAPER-WORKFLOW.md) | Greenfield project workflow |
| [02-BROWN-PAPER-WORKFLOW.md](./02-BROWN-PAPER-WORKFLOW.md) | Brownfield analysis workflow |
| [03-MIGRATION-WORKFLOW.md](./03-MIGRATION-WORKFLOW.md) | Legacy modernization workflow |
| [04-QUALITY-TREND-WORKFLOW.md](./04-QUALITY-TREND-WORKFLOW.md) | Periodic quality monitoring (ROADMAP) |
| [05-NEW-FEATURE-WORKFLOW.md](./05-NEW-FEATURE-WORKFLOW.md) | Enhancement workflow |
| [06-MAINTENANCE-DEBUG-WORKFLOWS.md](./06-MAINTENANCE-DEBUG-WORKFLOWS.md) | Maintenance and debugging |
| [07-DASHBOARD-WORKFLOW-MATRIX.md](./07-DASHBOARD-WORKFLOW-MATRIX.md) | Dashboard mapping |
| [99-TECHNICAL-INFRASTRUCTURE.md](./99-TECHNICAL-INFRASTRUCTURE.md) | Shared infrastructure (DRY reference) |

---

## LLM Providers

| Provider | Models | Use Case |
|----------|--------|----------|
| Ollama | deepseek-r1, qwen2.5-coder, codellama, mistral | Primary (local) |
| Groq | llama2-70b, mixtral | Fast inference |
| OpenAI | gpt-4, gpt-3.5-turbo | Fallback |
| Anthropic | claude-3-opus, claude-3-sonnet | Complex reasoning |
| Gemini | gemini-pro | Multimodal |
| Qwen | qwen-72b | Code generation |
| Moonshot | moonshot-v1 | Chinese content |

---

_Last updated: 2026-01-09_
