# Fase 23.5: Confucius Code Agent Orchestrator Integration (Week 149-154) HIGH PRIORITY

**Goal:** Integrate Confucius Code Agent (CCA) als centrale orchestrator voor alle 11 MarQed agents met hierarchisch geheugen, cross-session learning, en quality gates
**Specification:** [docs/architecture/confucius-orchestrator-integration-plan.md](../../architecture/confucius-orchestrator-integration-plan.md)
**Status:** APPROVED - HIGH PRIORITY
**Origin:** Meta/Harvard CCA Research (December 2025) - State-of-the-art agent scaffolding
**Effort:** 180 uur (~5 weken)

---

## Problem Statement

Huidige agent architectuur heeft kritieke beperkingen:
- **Geen shared memory** - Elke agent laadt context opnieuw (5x token cost)
- **Geen cross-session learning** - Zelfde fouten worden herhaald
- **Manual coordination** - User moet agents handmatig orchestreren
- **Geen quality gates** - Output kwaliteit is inconsistent
- **Context overload** - Irrelevante referenties worden geladen

---

## Solution: Confucius Orchestrator

```
┌─────────────────────────────────────────────────────────────────┐
│                 CONFUCIUS ORCHESTRATOR                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           HIERARCHICAL WORKING MEMORY                    │    │
│  │  session_scope │ entry_scope │ runnable_scope           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           EXTENSION SYSTEM (Agent Wrappers)              │    │
│  │  Felix │ Quinn │ Eliza │ Diana │ Marcus │ Miguel │ ...  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           QUALITY GATES + PIV LOOP                       │    │
│  │  Score ≥ 0.85 │ Max 3 iterations │ Auto-escalation      │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Features

| Feature | Beschrijving | Benefit |
|---------|--------------|---------|
| **Hierarchical Memory** | 3 scopes: session/entry/runnable | 40%+ context reductie |
| **Context Compression** | Adaptive LLM-based summarization | Token cost reduction |
| **Cross-Session Notes** | Problem → Solution → Insights | Learning across tasks |
| **Extension System** | 4 lifecycle hooks per agent | Clean integration |
| **Quality Gates** | Domain-specific scoring rules | Consistent output quality |
| **SSE Streaming** | Real-time progress updates | Better UX |

---

## Week-by-Week Deliverables

| Week | Focus | Hours | Output |
|------|-------|-------|--------|
| **149** | Core SDK Integration | 36 | Orchestrator, extensions base, DB migration |
| **150** | Memory Architecture | 38 | Hierarchical memory, compression, note-taking |
| **151** | Agent Extensions | 44 | 11 agent wrappers, router, tests |
| **152** | Quality Gates | 36 | Evaluator, iteration control, streaming |
| **153-154** | Full Migration | 48 | Workflow integration, optimization, docs |

---

## Agent Extension Mapping

| Agent | Extension | Priority | Capabilities |
|-------|-----------|----------|--------------|
| **Felix** | `FelixExtension` | 1 | Architecture analysis, system design |
| **Quinn** | `QuinnExtension` | 1 | Quality analysis, code review |
| **Marcus** | `MarcusExtension` | 1 | Migration planning, execution |
| **Miguel** | `MiguelExtension` | 2 | Metrics collection, analysis |
| **Eliza** | `ElizaExtension` | 2 | Estimation, FP calculation |
| **Tessa** | `TessaExtension` | 2 | Test generation, coverage |
| **Peter** | `PeterExtension` | 2 | Product backlog, user stories |
| **Betty** | `BettyExtension` | 2 | Business analysis, requirements |
| **Diana** | `DianaExtension` | 3 | Documentation generation |
| **Paul** | `PaulExtension` | 3 | Sprint planning, roadmap |
| **Vicky** | `VickyExtension` | 3 | Validation, verification |

---

## New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/confucius/execute` | POST | Execute task through orchestrator |
| `/api/confucius/execute/stream` | GET | SSE streaming execution |
| `/api/confucius/sessions` | GET/POST | Manage orchestrator sessions |
| `/api/confucius/sessions/{id}/memory` | GET | Get session memory state |
| `/api/confucius/extensions` | GET | List registered extensions |
| `/api/confucius/quality/evaluate` | POST | Manual quality evaluation |
| `/api/confucius/notes` | GET | Get cross-session notes |
| `/api/confucius/notes/search` | POST | Search notes |
| `/api/confucius/metrics` | GET | Orchestrator metrics |

---

## Database Schema (Migration 070)

```sql
-- Confucius Sessions (cross-task memory)
CREATE TABLE confucius_sessions (
    session_id UUID PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    insights JSONB DEFAULT '[]',
    patterns JSONB DEFAULT '[]',
    decisions JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Confucius Entries (per-task memory)
CREATE TABLE confucius_entries (
    entry_id UUID PRIMARY KEY,
    session_id UUID REFERENCES confucius_sessions,
    task TEXT NOT NULL,
    context_summary TEXT,
    results_summary TEXT,
    quality_score FLOAT,
    iterations_used INTEGER DEFAULT 1
);

-- Confucius Notes (cross-session learning)
CREATE TABLE confucius_notes (
    note_id UUID PRIMARY KEY,
    note_type VARCHAR(50) NOT NULL,
    problem TEXT NOT NULL,
    solution TEXT,
    insights JSONB DEFAULT '[]',
    context_tags JSONB DEFAULT '[]',
    quality_score FLOAT
);
```

---

## Success Metrics

| Metric | Baseline | Target |
|--------|----------|--------|
| **Context reduction** | 0% | 40%+ |
| **Quality score avg** | N/A | 0.85+ |
| **First-pass success** | N/A | 70%+ |
| **Cross-session reuse** | 0% | 30%+ |
| **Agent coordination** | Manual | Automatic |

---

## Rollout Strategy

| Week | Rollout % | Features |
|------|-----------|----------|
| 149 | 0% | Testing only |
| 150 | 5% | Memory + compression |
| 151 | 20% | All extensions |
| 152 | 50% | Quality gates |
| 153 | 80% | All workflows |
| 154 | 100% | Full migration |

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| **Fase 21.5** (Workflow Separation) | REQUIRED | AnalysisContract interface |
| **Fase 22** (FP Methodology) | RECOMMENDED | Quality scoring rules |
| **Fase 23** (Context Engineering) | PARALLEL | Shared patterns |
| **Confucius SDK** | PENDING | `github.com/facebook/confucius` |

---

## References

| Source | URL |
|--------|-----|
| arXiv Paper | [arxiv.org/abs/2512.10398](https://arxiv.org/abs/2512.10398) |
| MarkTechPost | [marktechpost.com](https://www.marktechpost.com/2026/01/09/meta-and-harvard-researchers-introduce-the-confucius-code-agent-cca/) |
| Emergent Mind - CCA | [emergentmind.com](https://www.emergentmind.com/topics/confucius-code-agent-cca) |
| Integration Plan | [confucius-orchestrator-integration-plan.md](../../architecture/confucius-orchestrator-integration-plan.md) |

---

← [Back to Overview](../phases-planned.md)
