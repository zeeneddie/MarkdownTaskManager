# Fase 23: Context Engineering & Reference-on-Demand (Week 147-148)

**Goal:** Implement PIV Loop (Plan-Implement-Validate) with intelligent reference loading and quality gates
**Specification:** [docs/architecture/context-engineering-architecture.md](../../architecture/context-engineering-architecture.md)
**Status:** PLANNED
**Origin:** Cole Medin's Top 1% Agentic Engineering analysis (2026-01-08)
**Reference Structure:** [.claude/reference/](.claude/reference/) + [.claude/examples/](.claude/examples/)

---

## Problem Statement

Current agent workflows load full context regardless of task needs:
- Token waste on irrelevant references
- No quality gates on agent output
- No automatic iteration when quality is insufficient
- Manual review required for all outputs

---

## Solution: PIV Loop with Quality Gates

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        PIV LOOP ARCHITECTURE                                  │
│                                                                               │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│   │   ROUTER    │───▶│  REFERENCE  │───▶│   AGENT     │───▶│   QUALITY   │  │
│   │   SERVICE   │    │  SELECTOR   │    │  EXECUTOR   │    │    GATE     │  │
│   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                  │                  │                  │           │
│         ▼                  ▼                  ▼                  ▼           │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│   │ Task        │    │ Semantic    │    │ PIV Loop    │    │ Threshold   │  │
│   │ Classifier  │    │ Matching    │    │ Iteration   │    │ Checker     │  │
│   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                               │
│   QUALITY GATES:                                                              │
│   ├── Score >= 0.85                                                           │
│   ├── Critical Issues == 0                                                    │
│   ├── Max Iterations == 3                                                     │
│   └── Escalate on failure                                                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Reference Structure (Created)

```
.claude/
├── reference/                    # Small focused docs (~2k words each)
│   ├── asp-vbscript-patterns.md  # Case-insensitive, ADO cleanup
│   ├── fastapi-conventions.md    # Router structure, error handling
│   ├── testing-patterns.md       # 70/20/10 pyramid, fixtures
│   ├── security-patterns.md      # OWASP, SQL injection
│   ├── stability-analysis.md     # 8 categories, leak patterns
│   └── python-best-practices.md  # Type hints, async patterns
│
└── examples/                     # Copy-paste templates
    ├── service-template.py       # ServiceResult pattern
    ├── api-endpoint-template.py  # CRUD operations
    ├── test-template.py          # Fixtures, parameterized
    └── detector-template.py      # BaseResourceLeakDetector
```

---

## Week 147: Core Services

| Task | Hours | Output |
|------|-------|--------|
| `ReferenceSelector` service | 6 | Semantic matching for references |
| `TaskRouter` service | 4 | Route to appropriate agent |
| `QualityGateEvaluator` service | 6 | Score calculation, threshold checking |
| `PIVLoopOrchestrator` service | 6 | Iteration management |
| Unit tests | 6 | 40+ tests |
| **Total** | **28** | |

---

## Week 148: Integration & Web Analysis

| Task | Hours | Output |
|------|-------|--------|
| Agent executor integration | 4 | Connect to existing agents |
| Quality metrics collection | 4 | Track iteration counts, scores |
| Web analysis scheduler | 4 | Weekly best practices scan |
| Reference update workflow | 4 | Human review for new references |
| API endpoints | 4 | `/api/context-engineering/*` |
| Dashboard | 4 | Quality gate statistics |
| E2E tests | 6 | Integration tests |
| **Total** | **30** | |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/context-engineering/analyze` | POST | Analyze task for reference needs |
| `/api/context-engineering/references` | GET | List available references |
| `/api/context-engineering/quality-gates` | GET | Quality gate statistics |
| `/api/context-engineering/iterations/{task_id}` | GET | Get iteration history |
| `/api/context-engineering/web-analysis/trigger` | POST | Trigger web analysis |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Token reduction | 60-80% fewer tokens loaded |
| Quality gate pass rate | >85% on first iteration |
| Max iterations before escalation | ≤3 |
| Reference matching accuracy | >90% |
| Web analysis updates | 2-4 new references/month |

---

## Total Effort: 58 hours (2 weeks)

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Reference files | CREATED | 6 reference files + 4 templates |
| Architecture doc | CREATED | context-engineering-architecture.md |
| Agent system | EXISTS | 11 agents available |

---

← [Back to Overview](../phases-planned.md)
