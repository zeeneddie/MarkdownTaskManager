# Fase 64: Self-Evolution Activation

**Status:** PLANNED
**Priority:** P3
**Timeline:** Week 229-234
**Effort:** ~80 uur (~5 weken)
**Dependencies:** Fase 60+61 (metrics infrastructure), LLMCouncilService ✅, AgentEvolutionService ✅ (exists, inactive)
**Source:** [Tracer/BART Gap Analyse](../tracer-bart-gap-analysis.md)

---

## Executive Summary

Activeer en integreer de bestaande `AgentEvolutionService` met Confucius Orchestrator en implementeer Stage Council Reviews bij Constitution en Specification fases. Agents leren van hun fouten en verbeteren autonoom over tijd.

**Het Probleem:**
> `AgentEvolutionService` bestaat al in de codebase maar is niet geactiveerd of geïntegreerd met de Confucius workflow pipeline. LLMCouncilService heeft council review capability maar wordt niet systematisch ingezet bij elke workflow stage.

**De Oplossing:**
```
Workflow Execution ──► Stage Output ──► Council Review ──► Score & Feedback
                                              │
                                              ▼
                                    AgentEvolutionService
                                              │
                              ┌───────────────┼───────────────┐
                              ▼               ▼               ▼
                       Prompt Tuning    Strategy Selection   Pattern Learning
                       (per agent)      (per scenario)       (cross-agent)
```

---

## Taken

### T5.1: AgentEvolutionService Activatie & Confucius Integratie (Hoog)

**Bestanden:** `backend/app/services/agent_evolution_service.py`, `backend/app/confucius/orchestrator.py`
**Effort:** 28 uur

Activeer AgentEvolutionService:
- Review huidige implementatie, identificeer ontbrekende wiring
- Hook in Confucius Orchestrator `on_stage_complete` lifecycle
- Na elke stage: feed output + quality score naar evolution service
- Evolution service analyseert patronen over meerdere runs
- Genereer `LearningTask` items: prompt adjustments, strategy preferences, anti-pattern updates

**Evolution Cycle:**
```
Run 1: Agent output → Quality 0.72 → Learning: "Specification stage needs more concrete examples"
Run 2: Agent output → Quality 0.81 → Learning: "Concrete examples improved quality +12%"
Run 3: Agent output → Quality 0.88 → Learning: "Consolidate: always include examples"
                                              ↓
                                    Permanent Pattern Stored
                                    (injected in future runs)
```

**Metrics vereist (uit Fase 47+48):**
- Per-agent quality scores over tijd
- Per-stage success rates
- PIV iteration counts (minder = beter)
- Cost efficiency trends

### T5.2: Stage Council Review bij Constitution Fase (Hoog)

**Bestanden:** `backend/app/services/llm_council_service.py`
**Effort:** 28 uur

Implementeer multi-model council review specifiek voor Constitution stage:
- Council samenstelling: claude_opus + deepseek_v3 + codex (architecture expertise)
- Review criteria: completeness, consistency, feasibility, security considerations
- Automatic improvement: bij council rejection, pas constitution aan en hersubmit
- Maximum 3 council rounds per constitution
- Council beslissing als OTLP span (Fase 47)

**Review Checklist:**
| Criterium | Gewicht | Beschrijving |
|-----------|---------|-------------|
| Completeness | 25% | Alle vereiste secties aanwezig? |
| Consistency | 25% | Geen tegenstrijdige requirements? |
| Feasibility | 20% | Technisch haalbaar? |
| Security | 15% | Security overwegingen meegenomen? |
| Testability | 15% | Vereisten testbaar geformuleerd? |

### T5.3: Stage Council Review bij Specification + Task Generation (Hoog)

**Bestanden:** Extend: `backend/app/services/llm_council_service.py`
**Effort:** 24 uur

Extend council review naar Specification en Task Generation stages:

**Specification Review:**
- Council: claude_sonnet + qwen_coder + deepseek_v3
- Focus: technical accuracy, API design, data model correctness
- Accept threshold: 80% consensus

**Task Generation Review:**
- Council: qwen_coder + codex + deepseek_v3
- Focus: task granularity, dependencies correct, effort estimates realistic
- Accept threshold: 70% consensus
- Special check: INVEST criteria per story (via bestaande InvestValidatorService)

---

## Resultaat

Na implementatie:
- Agents verbeteren autonoom op basis van historische quality data
- Council reviews op Constitution, Specification, en Task Generation
- Learning tasks worden automatisch gegenereerd en opgeslagen
- Quality scores stijgen meetbaar over meerdere workflow runs
- Permanent patterns gedeeld tussen agents

## Success Criteria

- [ ] AgentEvolutionService actief en genereert learning tasks na elke workflow run
- [ ] Constitution council review: approval rate > 85% na 3 rounds
- [ ] Specification council review: consensus > 80%
- [ ] Meetbare quality score stijging (>5%) na 10+ evolution cycles
- [ ] Learning tasks correct opgeslagen en herbruikt in volgende runs
- [ ] 35+ unit tests

## Voorwaarden

Deze fase heeft de **langste aanloop** van alle Tracer/BART fases:
1. Fase 47 (Observability) moet operationeel zijn voor metrics
2. Fase 48 (Dashboard) moet per-agent quality trends leveren
3. Voldoende workflow runs (50+) nodig voor betrouwbare learning data
4. Fase 23.6 (Stage Council) als basis ✅ al complete

---

*Created: Week 162 (2026-01-31)*
