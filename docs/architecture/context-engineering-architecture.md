# Context Engineering Architecture

**Datum**: 2026-01-08
**Status**: APPROVED
**Owner**: MarQed AI Platform
**Gebaseerd op**: Cole Medin's Top 1% Agentic Engineering + MarQed verbeteringen

---

## Executive Summary

Implementatie van Context Engineering voor token-efficiente agent workflows. References worden on-demand geladen, services worden gebouwd door agents, uitgevoerd als runtime, en verbeterd via agent reviews met quality gates.

---

## 1. Core Principes

### 1.1 Reference-on-Demand

```
FOUT:  Laad alle 50k tokens context bij elke call
GOED:  Laad 2-3 relevante references (max 6k tokens)
```

### 1.2 Build → Execute → Review → Improve

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  BUILD  │───►│ EXECUTE │───►│ REVIEW  │───►│ IMPROVE │
│ (Agent) │    │(Service)│    │ (Agent) │    │ (Agent) │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
     ▲                                            │
     └────────────────────────────────────────────┘
                    (max 3 iteraties)
```

### 1.3 Quality Gates met Thresholds

| Gate | Threshold | Actie bij Fail |
|------|-----------|----------------|
| Score | >= 0.85 | Retry met feedback |
| Critical Issues | == 0 | Blokkeer deploy |
| Max Iterations | <= 3 | Escaleer naar human |

---

## 2. Reference Folder Structuur

```
.claude/
├── commands/                    # Slash commands (bestaand)
│   └── *.md                     # Command definitions
├── reference/                   # ON-DEMAND context (NIEUW)
│   ├── asp-vbscript-patterns.md     # ~2k woorden
│   ├── fastapi-conventions.md       # ~2k woorden
│   ├── testing-patterns.md          # ~2k woorden
│   ├── security-patterns.md         # ~2k woorden
│   ├── stability-analysis.md        # ~2k woorden
│   └── python-best-practices.md     # ~2k woorden
├── examples/                    # Code voorbeelden (NIEUW)
│   ├── service-template.py
│   ├── api-endpoint-template.py
│   └── test-template.py
└── PRD.md                       # Product requirements (optioneel)
```

### 2.1 Reference File Format

```markdown
# [Domain] Best Practices

## Quick Reference
- Bullet points voor snelle lookup

## Patterns

### GOOD Pattern
```python
# Correct voorbeeld
```

### BAD Pattern (Avoid)
```python
# Fout voorbeeld - NIET DOEN
```

## Common Mistakes
1. Mistake + oplossing
2. Mistake + oplossing

## Checklist
- [ ] Item 1
- [ ] Item 2
```

### 2.2 Reference Size Limits

| Metric | Limit | Reden |
|--------|-------|-------|
| Max woorden per file | 2,500 | Token budget |
| Max refs per agent call | 3 | Focus |
| Max totaal tokens refs | 6,000 | Context window |

---

## 3. Reference Selector Service

### 3.1 Architectuur

```python
# backend/app/services/reference_selector_service.py

class ReferenceSelectorService:
    """
    Selecteert relevante references op basis van task context.

    Strategieen:
    1. Keyword matching (snel, basis)
    2. Semantic similarity (nauwkeurig, trager)
    3. Agent-type mapping (voorgedefinieerd)
    """

    REFERENCE_KEYWORDS = {
        "asp-vbscript-patterns": ["asp", "vbscript", "classic", "vb", "adodb"],
        "fastapi-conventions": ["api", "endpoint", "router", "fastapi", "pydantic"],
        "testing-patterns": ["test", "pytest", "coverage", "mock", "fixture"],
        "security-patterns": ["security", "auth", "owasp", "injection", "xss"],
        "stability-analysis": ["leak", "memory", "connection", "stability", "crash"],
        "python-best-practices": ["python", "typing", "async", "dataclass"],
    }

    AGENT_REFERENCES = {
        "Felix": ["fastapi-conventions", "python-best-practices"],
        "Quinn": ["security-patterns", "testing-patterns"],
        "Tessa": ["testing-patterns", "python-best-practices"],
        "Miguel": ["asp-vbscript-patterns", "stability-analysis"],
        "Marcus": ["security-patterns", "stability-analysis"],
    }

    def select_references(
        self,
        task_description: str,
        agent_name: Optional[str] = None,
        max_refs: int = 3,
    ) -> List[str]:
        """Selecteer relevante references."""
        pass

    def load_references(self, ref_names: List[str]) -> str:
        """Laad en concateneer reference content."""
        pass
```

### 3.2 Integration met Agents

```python
# In agent workflow

async def execute_with_context(task: Task, agent: Agent):
    # 1. Selecteer references
    refs = reference_selector.select_references(
        task_description=task.description,
        agent_name=agent.name,
        max_refs=2
    )

    # 2. Laad reference content
    context = reference_selector.load_references(refs)

    # 3. Execute agent met context
    result = await agent.execute(
        task=task,
        additional_context=context
    )

    return result
```

---

## 4. Quality Gate Integration

### 4.1 Review Score Berekening

```python
@dataclass
class ReviewResult:
    score: float              # 0.0 - 1.0
    critical_issues: int      # Blokkers
    warnings: int             # Niet-blokkerend
    suggestions: List[str]    # Verbeteringen
    iteration: int            # Huidige iteratie

    @property
    def passes_gate(self) -> bool:
        return self.score >= 0.85 and self.critical_issues == 0

    @property
    def should_retry(self) -> bool:
        return not self.passes_gate and self.iteration < 3

    @property
    def should_escalate(self) -> bool:
        return not self.passes_gate and self.iteration >= 3
```

### 4.2 Improvement Loop

```python
async def build_with_quality_gate(task: Task) -> ServiceResult:
    iteration = 0

    while iteration < MAX_ITERATIONS:
        iteration += 1

        # Build met references
        result = await build_service(task, iteration)

        # Review met references
        review = await review_service(result, iteration)

        if review.passes_gate:
            return ServiceResult(
                service=result,
                status="APPROVED",
                iterations=iteration
            )

        if review.should_escalate:
            return ServiceResult(
                service=result,
                status="ESCALATED",
                iterations=iteration,
                reason="Max iterations reached"
            )

        # Improve voor volgende iteratie
        task = enhance_task_with_feedback(task, review)

    return ServiceResult(status="FAILED")
```

---

## 5. Periodic Web Analysis

### 5.1 Reference Update Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  WEEKLY REFERENCE UPDATE (Sunday 02:00)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. WebSearch: "Python best practices 2026"                     │
│  2. WebSearch: "FastAPI patterns 2026"                          │
│  3. WebSearch: "OWASP top 10 2026"                              │
│  4. WebSearch: "ASP Classic security 2026"                      │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   EXTRACT    │───►│   COMPARE    │───►│   UPDATE     │       │
│  │   Patterns   │    │   with refs  │    │   if newer   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                  │
│  Output: reference-update-report.md                             │
│  - New patterns found: X                                        │
│  - Updated references: Y                                        │
│  - Requires human review: Z                                     │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 API Endpoint

```python
@router.post("/references/update-check")
async def check_reference_updates(
    domains: List[str] = ["python", "fastapi", "security"]
) -> ReferenceUpdateReport:
    """
    Scan web voor nieuwe best practices.
    Vergelijk met huidige references.
    Genereer update rapport.
    """
    pass

@router.post("/references/apply-updates")
async def apply_reference_updates(
    updates: List[ReferenceUpdate],
    require_review: bool = True
) -> ApplyResult:
    """Apply goedgekeurde updates naar reference files."""
    pass
```

---

## 6. PIV Loop Integration

### 6.1 Plan → Implement → Validate

```
┌─────────────────────────────────────────────────────────────────┐
│                         PIV LOOP                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  PLAN                                                    │    │
│  │  - Load project context                                  │    │
│  │  - Select references (max 3)                             │    │
│  │  - Generate implementation plan                          │    │
│  │  - Identify acceptance criteria                          │    │
│  └────────────────────────┬────────────────────────────────┘    │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  IMPLEMENT                                               │    │
│  │  - Execute plan step-by-step                             │    │
│  │  - Write code following reference patterns               │    │
│  │  - Write tests alongside code                            │    │
│  │  - Commit after each logical unit                        │    │
│  └────────────────────────┬────────────────────────────────┘    │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  VALIDATE                                                │    │
│  │  - Run all tests                                         │    │
│  │  - Check against acceptance criteria                     │    │
│  │  - Agent review with references                          │    │
│  │  - Quality gate evaluation                               │    │
│  │  - If fail: Loop back to PLAN with feedback              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Examples Folder

### 7.1 Doel

Code templates die agents gebruiken als startpunt. Toont:
- Correcte structuur
- Naming conventions
- Import patterns
- Test patterns

### 7.2 Templates

| Template | Doel |
|----------|------|
| `service-template.py` | Service class structuur |
| `api-endpoint-template.py` | Router + endpoints |
| `test-template.py` | pytest fixtures + tests |
| `detector-template.py` | BaseDetector implementatie |
| `model-template.py` | SQLAlchemy + Pydantic |

---

## 8. Implementatie Roadmap

### Fase 23: Context Engineering (Week 147-148)

| Week | Dag | Taak | Uren |
|------|-----|------|------|
| 147 | 1-2 | Reference folder + 6 core refs | 8 |
| 147 | 3 | ReferenceSelector service | 4 |
| 147 | 4 | Examples folder + templates | 4 |
| 147 | 5 | Quality gate integration | 4 |
| 148 | 1-2 | PIV loop commands | 6 |
| 148 | 3 | Web analysis service | 4 |
| 148 | 4 | Agent workflow integration | 4 |
| 148 | 5 | Tests + documentation | 4 |
| **Total** | | | **38** |

---

## 9. Success Metrics

| Metric | Target | Meting |
|--------|--------|--------|
| Token usage per agent call | -40% | Gemiddelde tokens |
| Reference load time | <100ms | P95 latency |
| Quality gate pass rate | >80% first try | Percentage |
| Improvement iterations | <2 avg | Gemiddeld |
| Reference freshness | <7 days | Last update |

---

## 10. DO's en DON'Ts

### DO

- Houd references < 2,500 woorden
- Laad max 3 refs per agent call
- Gebruik GOOD/BAD voorbeelden
- Versie references in git
- Update weekly via web scan
- Escaleer na 3 iteraties

### DON'T

- Laad niet alle refs tegelijk
- Geen refs > 5,000 woorden
- Geen review zonder criteria
- Geen oneindige improve loops
- Geen hardcoded ref selectie
- Geen refs zonder voorbeelden

---

## Related Documents

| Document | Beschrijving |
|----------|--------------|
| [Cole Medin's context-engineering-intro](https://github.com/coleam00/context-engineering-intro) | Originele inspiratie |
| [phases-planned.md](../roadmap/phases-planned.md) | Roadmap met Fase 23 |
| [stability-analysis.md](./asp-stability-analyzer-framework.md) | Voorbeeld domein |

---

*Context Engineering Architecture - MarQed AI Platform*
*Gebaseerd op Cole Medin's Top 1% Agentic Engineering*
