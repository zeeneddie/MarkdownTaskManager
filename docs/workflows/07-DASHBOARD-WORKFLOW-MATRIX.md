# Dashboard to Workflow Matrix

## Entry Point Dashboards

These dashboards serve as **workflow entry points** where users begin their journey:

| Dashboard | Workflow Start | Next Dashboards |
|-----------|----------------|-----------------|
| `project-wizard.html` | GREEN_PAPER | → brown-paper-dashboard → kanban |
| `brown-paper-dashboard.html` | GREEN_PAPER, BROWN_PAPER | → deep-extraction, migration-analyzer, kanban |
| `migration-analyzer.html` | MIGRATION | → migration-progress → kanban |
| `maintenance-scheduler.html` | MAINTENANCE | → technical-debt, quality, kanban |
| `kanban-dashboard.html` | Implementation (all) | → maintenance-scheduler (loop) |

---

## Complete Dashboard Mapping

| Dashboard | File | Primary Workflow(s) | Data Source Tables | API Endpoints |
|-----------|------|---------------------|-------------------|---------------|
| **Project Management** |
| Kanban Dashboard | kanban-dashboard.html | All | items, task_hierarchy | /api/kanban |
| Sprint Planning | sprint-planning.html | Implementation | sprint, items | /api/sprints |
| Project Wizard | project-wizard.html | GREEN_PAPER | green_paper_sessions | /api/green-paper |
| Project Intake | project-intake.html | All | items | /api/project-intake |
| Applications | applications.html | All | application_registry | /api/applications |
| **Workflow Dashboards** |
| Brown Paper | brown-paper-dashboard.html | GREEN_PAPER, BROWN_PAPER | green_paper_sessions, brown_paper_sessions | /api/green-paper, /api/brown-paper |
| Workflow Dashboard | workflow-dashboard.html | All | workflow_executions | /api/workflow-dashboard |
| Deep Extraction | deep-extraction.html | BROWN_PAPER | deep_extraction | /api/deep-extraction |
| Migration Analyzer | migration-analyzer.html | Migration | bmad_sessions | /api/brown-paper/bmad |
| Migration Progress | migration-progress-dashboard.html | Migration | bmad_sessions | /api/migration |
| **Quality & Analysis** |
| Quality Dashboard | quality-dashboard.html | QUALITY_AUDIT | code_analysis, quality_gates | /api/quality |
| Security Dashboard | security-dashboard.html | All | security, ghostcrew_results | /api/security |
| Technical Debt | technical-debt-dashboard.html | MAINTENANCE | technical_debt | /api/debt |
| Weak Spots | weak-spots-dashboard.html | MAINTENANCE | code_analysis | /api/quality |
| Code Analysis | codewiki-dashboard.html | All | codewiki | /api/codewiki |
| **Estimation** |
| Estimation Dashboard | estimation-dashboard.html | BROWN_PAPER | estimation_history, fp_estimation | /api/estimation |
| **Agent & AI** |
| Agent Dashboard | agent-dashboard.html | All | agents, agent_execution | /api/agents |
| Evolution Dashboard | evolution-dashboard.html | All | agent_evolution, ab_testing | /api/evolution |
| LLM Council | llm-council-dashboard.html | All | council_decisions | /api/llm-council |
| Human Review | human-review-dashboard.html | All | council_human_review | /api/council-human-review |
| Council Human Review | council-human-review.html | All | council_human_review | /api/council-human-review |
| **Configuration** |
| Quality Gates Config | quality-gates-config.html | All | quality_gate_config | /api/quality-gates |
| Standards Browser | standards-browser.html | All | standards | /api/standards |
| Spec Kit Wizard | spec-kit-wizard.html | Planning | spec_shaping | /api/spec-shaping |
| **Observability** |
| Observability | observability-dashboard.html | All | observability, metrics | /api/observability |
| Maintenance Scheduler | maintenance-scheduler.html | MAINTENANCE | scheduled_tasks | /api/scheduler |

---

## Dashboard Categories

### Workflow Execution (7 dashboards)
- brown-paper-dashboard.html
- workflow-dashboard.html
- deep-extraction.html
- migration-analyzer.html
- migration-progress-dashboard.html
- project-wizard.html
- project-intake.html

### Quality & Security (5 dashboards)
- quality-dashboard.html
- security-dashboard.html
- technical-debt-dashboard.html
- weak-spots-dashboard.html
- codewiki-dashboard.html

### Agent & AI (5 dashboards)
- agent-dashboard.html
- evolution-dashboard.html
- llm-council-dashboard.html
- human-review-dashboard.html
- council-human-review.html

### Project Management (4 dashboards)
- kanban-dashboard.html
- sprint-planning.html
- applications.html
- estimation-dashboard.html

### Configuration (3 dashboards)
- quality-gates-config.html
- standards-browser.html
- spec-kit-wizard.html

---

## Data Flow by Workflow

### GREEN_PAPER Flow
```
green_paper_sessions → green_paper_answers → green_paper_constitutions → green_paper_specifications → task_hierarchy
        |                                                                                                    |
        v                                                                                                    v
brown-paper-dashboard.html                                                                      kanban-dashboard.html
```

### BROWN_PAPER Flow
```
brown_paper_sessions → brown_paper_analyses → brown_paper_domains → deep_extraction → estimation_history
        |                                            |                     |                  |
        v                                            v                     v                  v
brown-paper-dashboard.html              deep-extraction.html    deep-extraction.html   estimation-dashboard.html
```

### MAINTENANCE Flow
```
technical_debt → code_analysis → quality_gates → scheduled_tasks
      |               |               |               |
      v               v               v               v
technical-debt-dashboard  quality-dashboard  quality-gates-config  maintenance-scheduler
```

---

## API Endpoint Coverage

| API Prefix | Dashboard Count | Primary Dashboards |
|------------|-----------------|-------------------|
| /api/green-paper | 2 | brown-paper-dashboard, project-wizard |
| /api/brown-paper | 3 | brown-paper-dashboard, deep-extraction, migration-analyzer |
| /api/kanban | 2 | kanban-dashboard, sprint-planning |
| /api/quality | 4 | quality-dashboard, weak-spots, technical-debt, code-analysis |
| /api/estimation | 1 | estimation-dashboard |
| /api/security | 1 | security-dashboard |
| /api/agents | 2 | agent-dashboard, evolution-dashboard |

---

## Dashboard Navigation Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DASHBOARD NAVIGATION                             │
│                                                                          │
│  ENTRY POINTS                        PROCESS                  OUTPUT    │
│  ═══════════                        ═══════                   ══════    │
│                                                                          │
│  project-wizard.html ──┐                                                 │
│                        ├──► brown-paper-dashboard ──► kanban-dashboard  │
│  brown-paper-dashboard ┘            │                       │           │
│                                     │                       │           │
│                                     ▼                       │           │
│                        deep-extraction.html                 │           │
│                        estimation-dashboard.html            │           │
│                                     │                       │           │
│                                     ▼                       │           │
│                        migration-analyzer.html              │           │
│                        migration-progress.html              │           │
│                                     │                       │           │
│                                     └───────────────────────┤           │
│                                                             │           │
│                                                             ▼           │
│                                           maintenance-scheduler.html    │
│                                           technical-debt-dashboard      │
│                                           quality-dashboard             │
│                                                             │           │
│                                                             │           │
│                        (lifecycle restart) ◄────────────────┘           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

_See also: [Master Overview](./00-WORKFLOW-MASTER-OVERVIEW.md) | [Infrastructure](./99-TECHNICAL-INFRASTRUCTURE.md)_
