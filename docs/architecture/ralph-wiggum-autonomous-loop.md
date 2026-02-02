# Ralph Wiggum Autonomous Loop Architecture

**Status:** PLANNED (Fase 32 — KW15+ [w168+], doorloop Q2)
**Parent:** [Platform Architecture](../unified-architecture-diagram.md)
**Datum:** 2026-02-01

---

## Overzicht

Ralph Wiggum is het autonomous coding framework dat agents onbeheerd laat werken (8+ uur overnight). Het combineert 4 workflow-specifieke operatiemodi met guardrails, circuit breakers en het Quality Harness (Fase 32E) voor betrouwbare autonome uitvoering.

```
+===============================================================================+
|  RALPH WIGGUM AUTONOMOUS LOOP                                                 |
+===============================================================================+
|                                                                               |
|  INPUT                                                                        |
|  +------------------+    +------------------+    +------------------+         |
|  | Task / PRD       |--->| WorkflowType     |--->| PRP Framework    |         |
|  |                  |    | Resolver         |    | (Prompt Eng.)    |         |
|  +------------------+    +------------------+    +------------------+         |
|                                                          |                    |
|          BUGFIX ─────────┐                               |                    |
|          CHANGES ────────┤                               v                    |
|          MIGRATION ──────┤                     +------------------+           |
|          OVERNIGHT ──────┘                     | Workflow-Specific|           |
|                                                | PROMPT           |           |
|                                                +--------+---------+           |
|                                                         |                     |
|                                                         v                     |
|  EXECUTION LOOP                                                               |
|  +-------------------------------------------------------------------+       |
|  |                                                                   |       |
|  |  ┌─► Checkpoint ──► Execute Task ──► Validate ──► Complete? ──┐  |       |
|  |  │                                      │              │  No  │  |       |
|  |  │                                   FAIL              │      │  |       |
|  |  │                                      │              ▼      │  |       |
|  |  │                              Course Correction   Next Task │  |       |
|  |  │                                      │              │      │  |       |
|  |  └──────────────────────────────────────┘              │      │  |       |
|  |                                                     Yes │      │  |       |
|  |                                                        ▼      │  |       |
|  |                                                   Git Commit  │  |       |
|  |                                                   + Memory    │  |       |
|  |                                                   Compress    │  |       |
|  +-------------------------------------------------------------------+       |
|                          │                                                    |
|                          v                                                    |
|  QUALITY HARNESS [FASE 32E]                                                   |
|  +-----------------------+    +----------------+    +------------------+      |
|  | PM Acceptance Gate    |--->| QA Gate        |--->| Progressive      |      |
|  | (Claude review)       |    | (7 axes)       |    | Regression       |      |
|  +-----------------------+    +----------------+    +------------------+      |
|                                                                               |
|  OUTPUT                                                                       |
|  +------------------+    +------------------+    +------------------+         |
|  | Morning Report   |    | Acceptance       |    | Sprint Report    |         |
|  | (Summary)        |    | Registry (DB)    |    | (bij completion) |         |
|  +------------------+    +------------------+    +------------------+         |
|                                                                               |
+===============================================================================+
```

---

## Core Componenten

### RalphLoopService

Autonomous execution loop met configurable iterations.

```
RalphLoopService
    ├── max_iterations: configureerbaar per workflow type
    ├── checkpoint_interval: elke N taken
    ├── token_budget: max tokens per run
    └── cost_limit: max kosten per overnight
```

### GuardrailsService

File-based lesson learning dat cross-context persistent is.

```
.marqed/guardrails.md
    ├── Geleerde lessen uit eerdere runs
    ├── Bekende valkuilen per project type
    ├── Automatisch bijgewerkt na elke fout
    └── Beschikbaar voor volgende Ralph run
```

### CircuitBreaker

Detecteert wanneer de agent vastzit en stopt automatisch.

```
CircuitBreaker
    ├── stuck_detection: dezelfde output 3x achtereen
    ├── cost_limit: budgetoverschrijding
    ├── token_rotation: wissel model bij context overflow
    └── max_failures: configureerbare drempel
```

### CourseCorrectionService

Dead-end detectie en automatische correctie via 5 Whys methodologie.

```
CourseCorrectionService
    ├── Detecteer: geen voortgang na N iteraties
    ├── Analyseer: 5 Whys root cause
    ├── Corrigeer: alternatieve aanpak selecteren
    └── Escaleer: als correctie niet lukt
```

### CompletionDetector

Dual-gate exit logic voor betrouwbare completion detectie.

```
CompletionDetector
    ├── Gate 1: Checkbox tracking (taken in PRD)
    ├── Gate 2: Functionele validatie (tests draaien)
    └── Beide gates moeten slagen voor completion
```

---

## 4 Workflow Modi

Ralph is **niet** een generieke loop — het gedrag verschilt fundamenteel per workflow type.

| Aspect | BUGFIX | CHANGES | MIGRATION | OVERNIGHT |
|--------|--------|---------|-----------|-----------|
| **Focus** | Minimale fix | Feature oplevering | Data + code migratie | Onbeheerd werk |
| **Risk** | Regressie | Scope creep | Data verlies | Kwaliteitsdrift |
| **Iteraties** | Weinig (3-5) | Medium (5-10) | Veel (10-20) | Maximaal |
| **HITL** | Na root cause | Na design | Na elke fase | Avond + ochtend |
| **PM Gate** | Na fix | Na design + voor merge | Na elke fase + data gates | PRP approval + morning |

---

## Dual PM Approval Gate Patroon

Elke workflow heeft twee vaste PM gates plus workflow-specifieke gates:

```
Gate 1 (Na Analyse)                    Gate 2 (Voor Merge)
+---------------------+               +---------------------+
| PM-Agent Review     |               | PM-Agent Review     |
| (Claude Code)       |               | (Claude Code)       |
+----------+----------+               +----------+----------+
           |                                      |
           v                                      v
+---------------------+               +---------------------+
| PM-Human Review     |               | PM-Human Review     |
| (Async, timeout)    |               | (Async, timeout)    |
+---------------------+               +---------------------+

Verdicts: APPROVE | ADJUST | PARK | DEFINITIEF
Timeout: Configureerbaar per workflow type (4h-72h)
Escalatie: Na timeout → auto-escalate
```

→ Volledige specificatie: [fase-32-ralph-wiggum-loop.md](../roadmap/phases/fase-32-ralph-wiggum-loop.md) (sectie "Dual PM Approval Gate")

---

## OVERNIGHT Workflow

Het 5e workflow type, specifiek voor onbeheerd nachtelijk werk.

```
Avond:
    Developer
        │
        │ $ mq overnight --prd requirements.md --budget $25 --codebase ./src
        │
        ├── PRP Framework: Research → Requirements → Blueprint → PROMPT
        ├── Dual PM Gate 1 (PRP Approval — synchroon, avonds)
        │       "PRP + budget OK? Haalbaar overnight?"
        ├── Ralph Loop Start (onbeheerd)
        │       ├── Execute tasks met checkpoints
        │       ├── Guardrails raadplegen
        │       ├── CircuitBreaker monitoring
        │       └── Git commit per milestone
        │
Ochtend:
        ├── Morning Report genereren
        │       ├── Wat is gedaan
        │       ├── Wat is mislukt
        │       ├── Kosten overzicht
        │       └── Architectuurwijzigingen
        ├── Quality Harness (PM Gate + QA Gate + Regression)
        └── Dual PM Gate 2 (Morning Review — asynchroon)
                "Kwaliteit OK? Doorgaan of rollback?"
```

---

## mq Integratie Componenten

| Component | Functie |
|-----------|---------|
| **UnifiedStateManager** | Gedeelde state tussen mq tasks + Ralph |
| **KnowledgeHubService** | TechStack KB + Guardrails + Experience Store |
| **UnifiedValidationPipeline** | 8-fase validatie (Vercel-style + Ralph) |
| **marqed-overnight.sh** | CLI workflow script voor overnight coding |
| **MorningReportGenerator** | Samenvatting van overnight werk |
| **MemoryCompressionService** | Context handoff tussen runs bij token overflow |

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Overnight runtime | 8+ uur stable |
| False completion | < 5% (met Quality Harness: < 3%) |
| Guardrails repeat reduction | 70% minder herhaalde fouten |
| Rollback recovery | < 60 sec |
| Cost per overnight | < $25 gemiddeld |

---

## Gerelateerde Documenten

- [Fase 32 Specificatie](../roadmap/phases/fase-32-ralph-wiggum-loop.md) — Volledige specificatie (3400+ regels)
- [mq Ralph Integration Plan](../mq-ralph-wiggum-integration-plan.md) — mq platform integratie
- [Quality Harness Pipeline](quality-harness-pipeline.md) — PM/QA gates die Ralph output valideren
- [Harness Pluggable Architecture](harness-pluggable-architecture.md) — Plug-and-play agent framework
- [Context Engineering](context-engineering-architecture.md) — Token-efficient agent workflows

---

*Week 162 (2026-02-01) — Fase 32 PLANNED (KW15+, doorloop Q2)*
