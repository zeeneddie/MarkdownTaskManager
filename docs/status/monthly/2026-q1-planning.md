# Q1 2026 - Planning & Roadmap

**Periode:** 2026-01-01 tot 2026-04-30
**Weken:** 99-102+
**Status:** PLANNED

---

## Overzicht

Q1 2026 focust op de voltooiing van de Hybrid Static-LLM Extraction Pipeline (Fase 15b) met conflict detection, human review UI, en volledige compliance integratie.

---

## Fase 15b: Pipeline Integration (Week 99-102)

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HYBRID STATIC-LLM EXTRACTION PIPELINE                     │
│                                                                              │
│  CYCLE 0: STATIC ANALYSIS (80% Coverage - Week 97-98 COMPLETE ✅)           │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  ProgramSlicer → VariableClassifier → BusinessRuleExtractor →           ││
│  │  NFRDetector → ComplianceChecker                                        ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                              │                                               │
│                              ▼                                               │
│  CYCLES 1-5: LLM ENRICHMENT (Week 99-102 PLANNED)                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Static results als context → LLM valideert/verrijkt                    ││
│  │  ConflictDetector (72.5% threshold) → Human Review UI                   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Week 99-100: Pipeline Integration

### Deliverables

| Component | Beschrijving | Days |
|-----------|--------------|------|
| Cycle 0 Integration | Static analysis in DeepExtractionService | 2 |
| ConflictDetector | 72.5% confidence threshold | 2 |
| Tier Structure Update | FREE tier removal | 1 |

### Conflict Detection Rules

| Type | Condition | Action |
|------|-----------|--------|
| **Confidence Threshold** | LLM confidence < 72.5% | Human Review |
| **Explicit Disagreement** | Static & LLM disagree | Human Review |
| **Classification Change** | Epic→Feature change | Human Review |
| **Item Removal** | LLM removes static item | Human Review |

---

## Week 101: Compliance Library

### Deliverables

| Component | Beschrijving | Days |
|-----------|--------------|------|
| NEN7510 Full | Dutch healthcare expansion | 1 |
| ISO27001 Full | Information security expansion | 1 |
| HIPAA Full | US healthcare expansion | 1 |
| Project Settings UI | Compliance framework selection | 2 |

### Database Schema

| Table | Purpose |
|-------|---------|
| `compliance_frameworks` | Framework configurations |
| `compliance_rules` | Per-framework rules |
| `compliance_violations` | Detected violations |
| `compliance_exceptions` | Approved exceptions |

---

## Week 102: Hierarchy Completion

### Deliverables

| Component | Beschrijving | Days |
|-----------|--------------|------|
| Mid-Level Requirements | Gap filling | 2 |
| Business Goals Layer | Top-level extraction | 2 |
| CAFCR Mapping | Full view integration | 1 |

### CAFCR Views

| View | Level | Description |
|------|-------|-------------|
| Customer | Business | User needs, business goals |
| Application | System | Features, capabilities |
| Functional | Detailed | User stories, acceptance criteria |
| Conceptual | Technical | Architecture, design |
| Realization | Code | Implementation details |

---

## Updated Tier Structure (Post-Week 99)

| Tier | Static Analysis | LLM Providers | Human Review | Price (50K LOC) |
|------|-----------------|---------------|--------------|-----------------|
| ~~FREE~~ | ~~N/A~~ | ~~3 Ollama~~ | ~~No~~ | ~~$0~~ |
| **BASIC** | Full Cycle 0 | 3 (Ollama) | No | €5 |
| **STANDARD** | Full Cycle 0 | 5 (+Groq, Qwen) | Optional | €25 |
| **PROFESSIONAL** | Full Cycle 0 | 7 (+Gemini, GPT) | Included | €75 |
| **PREMIUM** | Full Cycle 0 | 10 (+Opus, Moonshot) | Included | €150 |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Static coverage | ≥80% business rules |
| Conflict rate | ≤15% |
| Human review reduction | ≥30% |
| NFR detection | 8/8 categories |
| Compliance automation | ≥70% checks |

---

## Key Milestones

| Date | Milestone |
|------|-----------|
| 2026-01-15 | ConflictDetector complete |
| 2026-02-01 | Human Review UI live |
| 2026-02-15 | Compliance Library complete |
| 2026-03-01 | CAFCR Mapping complete |
| 2026-04-01 | Fase 15b fully complete |

---

## Dependencies

| Dependency | Status | Required For |
|------------|--------|--------------|
| Static Analysis Foundation | ✅ COMPLETE | Pipeline Integration |
| GitHub/DevOps Analysis | ✅ COMPLETE | Hot spot prioritization |
| Deep Extraction Pipeline | ✅ COMPLETE | LLM enrichment cycles |
| Agent Harness Framework | ✅ COMPLETE | Constraint management |

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM API rate limits | Medium | Provider fallback chains |
| Human review bottleneck | High | Queue management, priorities |
| Compliance framework gaps | Medium | Iterative expansion |
| Performance at scale | Medium | Caching, async processing |

---

**Zie ook:**
- [December 2025](./2025-12-december.md)
- [Hybrid Static-LLM Pipeline Spec](../../architecture/hybrid-static-llm-pipeline.md)
