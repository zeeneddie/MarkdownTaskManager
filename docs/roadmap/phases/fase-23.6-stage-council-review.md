# Fase 23.6: Stage-Based LLM Council Review System (Week 157-162) QUALITY FIRST

**Goal:** Automatische LLM Council review bij elke development stage met second round capability voor artifact improvement
**Specification:** [docs/architecture/stage-based-council-review-plan.md](../../architecture/stage-based-council-review-plan.md)
**Status:** APPROVED - QUALITY FOCUS
**Origin:** User request - LLM Council review bij elke stage (architecture, design, analysis, programming, testing, infrastructure)
**Effort:** 120 uur (~4 weken)
**Prerequisite:** Fase 23.5 (Confucius Code Agent Integration)

---

## Problem Statement

Huidige kwaliteitsborging heeft kritieke beperkingen:
- **Handmatige reviews** - Developer moet expliciet om review vragen
- **Single-model** - Geen consensus van meerdere perspectieven
- **Geen automatische verbetering** - Issues worden gedetecteerd maar niet gefixed
- **Stage-agnostisch** - Geen stage-specifieke criteria (architecture vs code)
- **Geen iteratie** - Eenmalige check, geen second round

---

## Solution: Stage-Based Council Review

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                    STAGE-BASED COUNCIL REVIEW SYSTEM                           │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  DEVELOPMENT STAGE                       COUNCIL REVIEW                         │
│  ══════════════════                     ════════════════                        │
│  ┌────────────────┐                    ┌─────────────────────┐                 │
│  │ Architecture   │───completed───────►│ Architecture Council │                │
│  │ Design         │                    │ (Claude+DeepSeek+Codex)│               │
│  │ Analysis       │                    └──────────┬──────────┘                 │
│  │ Programming    │                               │                            │
│  │ Testing        │                    ┌──────────▼──────────┐                 │
│  │ Infrastructure │                    │  Issues < Threshold? │                │
│  └────────────────┘                    └──────────┬──────────┘                 │
│                                                   │                            │
│                         ┌────────YES─────────────┴─────────NO────────┐        │
│                         │                                            │        │
│                         ▼                                            ▼        │
│              ┌─────────────────┐                      ┌─────────────────┐     │
│              │ ✓ APPROVED      │                      │ SECOND ROUND    │     │
│              └─────────────────┘                      │ Auto-Improve    │     │
│                                                       │ + Re-Review     │     │
│                                                       └────────┬────────┘     │
│                                                                │              │
│                                                                ▼              │
│                                                     ┌─────────────────┐       │
│                                                     │ Improved Output │       │
│                                                     └─────────────────┘       │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

| Feature | Beschrijving | Benefit |
|---------|--------------|---------|
| **Stage-Specific Councils** | Optimale model mix per stage | Betere review kwaliteit |
| **Issue Classification** | Critical/Major/Minor/Suggestion | Intelligente threshold |
| **Consensus-Based** | Alleen issues die 50%+ modellen zien | Minder false positives |
| **Automatic Improvement** | LLM fixt issues automatisch | Geen handmatige fixes |
| **Second Round** | Re-review na verbetering | Iteratieve kwaliteit |
| **Performance Tracking** | Model/stage metrics | Data-driven tuning |

---

## Stage Council Configurations

| Stage | Primary Models | Threshold | Consensus |
|-------|----------------|-----------|-----------|
| **Architecture** | Claude Opus, DeepSeek V3, Codex | 0 critical, 2 major | 70% |
| **Design** | Claude Sonnet, Qwen Coder, DeepSeek | 0 critical, 3 major | 60% |
| **Analysis** | DeepSeek V3, Claude Sonnet, Falcon | 0 critical, 3 major | 60% |
| **Programming** | Qwen Coder, Codex, DeepSeek | 0 critical, 2 major | 60% |
| **Testing** | DeepSeek, Qwen Coder, Claude | 0 critical, 2 major | 60% |
| **Infrastructure** | Claude Opus, DeepSeek, Codex | 0 critical, 1 major | 75% |

---

## Phased Implementation

| Fase | Week | Focus | Hours | Deliverable |
|------|------|-------|-------|-------------|
| **24.1** | 157-158 | Foundation | 30 | StageReviewService, Issue Classification, DB Schema |
| **24.2** | 159-160 | Intelligence | 35 | Second Round, ArtifactImprovementService |
| **24.3** | 160-161 | Integration | 30 | Confucius Extension, All Stages, API |
| **24.4** | 161-162 | Optimization | 25 | Performance Tracking, Auto-Tuning |

---

## New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stage-review/review` | POST | Submit artifact for stage review |
| `/api/stage-review/sessions/{id}` | GET | Get review session details |
| `/api/stage-review/performance/models` | GET | Model performance metrics |
| `/api/stage-review/performance/stages` | GET | Stage performance metrics |
| `/api/stage-review/config/{stage_type}` | GET | Get stage configuration |

---

## Database Schema (Migration 071)

- `stage_review_sessions` - Review session tracking
- `stage_model_reviews` - Individual model reviews
- `stage_review_issues` - Detected issues with consensus
- `stage_review_decisions` - Round decisions
- `stage_improved_artifacts` - Improved artifacts (second round)
- `stage_review_metrics` - Performance metrics

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Review Accuracy** | >90% | Issues found vs post-release bugs |
| **Second Round Effectiveness** | >70% | Reviews passing after improvement |
| **Consensus Correlation** | >0.8 | Consensus vs actual quality |
| **Performance** | <3 min | Average review duration |
| **Stage Coverage** | 100% | All stages with active reviews |

---

## Integration with Confucius PIV Loop

```python
# StageReviewExtension hooks into on_post lifecycle
class StageReviewExtension(BaseAgentExtension):
    async def on_post(self, context, result, metadata):
        # Automatically triggers stage review
        review_result = await self.review_service.review_artifact(
            stage_type=metadata.get("stage_type"),
            artifact=metadata.get("artifact")
        )

        if not review_result.approved:
            return {
                "should_retry": True,
                "improved_artifact": review_result.improved_artifact
            }
```

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| **Fase 23.5** (Confucius Orchestrator) | REQUIRED | PIV Loop integration |
| **LLM Council** | EXISTS | Base council implementation |
| **Multi-Model Strategy** | PLANNED | Model routing configuration |

---

## References

| Source | Description |
|--------|-------------|
| [stage-based-council-review-plan.md](../../architecture/stage-based-council-review-plan.md) | Full implementation plan |
| [llm-council-improvements-plan.md](../../architecture/llm-council-improvements-plan.md) | Base council enhancements |
| [confucius-orchestrator-integration-plan.md](../../architecture/confucius-orchestrator-integration-plan.md) | Orchestrator integration |

---

← [Back to Overview](../phases-planned.md)
