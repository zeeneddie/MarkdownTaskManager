# Tracer/BART vs MarQed: Gap Analyse & Verbeterplan

**Status:** PLAN VAN AANPAK
**Created:** Week 162 (2026-01-31)
**Priority:** P0-P3 (gefaseerd over 5 nieuwe roadmap fases)
**Source:** OpenClaw video analyse - Tracer (Epic Mode) + BART Simpson orchestratie

---

## Quick Navigation

| Document | Content |
|----------|---------|
| **This file** | Gap analyse, strategische conclusies, roadmap mapping |
| [fase-60-observability-foundation.md](phases/fase-60-observability-foundation.md) | P0: OTLP/Langfuse integratie |
| [fase-61-progress-dashboard.md](phases/fase-61-progress-dashboard.md) | P1: Real-time voortgangsdashboard |
| [fase-62-conversational-intake.md](phases/fase-62-conversational-intake.md) | P1: Chat-based requirements gathering |
| [fase-63-statistical-drift-detection.md](phases/fase-63-statistical-drift-detection.md) | P2: Embedding-based drift detectie |
| [fase-64-self-evolution-activation.md](phases/fase-64-self-evolution-activation.md) | P3: Agent zelfverbetering |

---

## 1. Achtergrond

Uit de video over OpenClaw worden twee concepten beschreven:
1. **Tracer (Epic Mode)**: Beschrijf wat je wilt bouwen -> follow-up vragen -> specs & tickets automatisch genereren -> voortgang per ticket tracken
2. **BART Simpson**: Slimme orchestratie die real-time monitort wat agents doen en corrigeert bij afdwaling (drift), in plaats van blind loops te herhalen

---

## 2. GAP ANALYSE: Wat heeft MarQed al?

### Tracer Epic Mode vs MarQed

| Tracer Feature | MarQed Equivalent | Status |
|---|---|---|
| "Vertel wat je wilt bouwen" | `SpecShapingService`, `SoftwareIntakeService` | **BESTAAT** |
| Follow-up vragen stellen | `SpecShapingService.CheckCategory` validaties | **GEDEELTELIJK** - geen chat-interface |
| Specs auto-genereren | Peter (Constitution) + Felix (Specification) pipeline | **BESTAAT** |
| Tickets/epics/stories genereren | `IntakeToBacklogService` - complete epic/feature/story hierarchy | **BESTAAT** |
| Quick templates | `QuickSpecService` - 4 templates (bug, enhancement, refactoring, hotfix) | **BESTAAT** |
| Voortgang per ticket tracken | 9-Lane Kanban + SSE Streaming (20+ event types) | **BESTAAT** (backend) |
| Visuele sidebar/dashboard | Geen frontend consumer voor SSE events | **ONTBREEKT** -> Fase 61 |
| **Conversationele chat-loop** | Niet aanwezig als user-facing interface | **ONTBREEKT** -> Fase 62 |

**Conclusie**: MarQed heeft ~80% van Epic Mode. Gaps: conversationele chat-interface en visueel voortgangsdashboard.

### BART Simpson vs MarQed

| BART Feature | MarQed Equivalent | Status |
|---|---|---|
| Track wat agents doen | `CCTraceService` (thinking blocks, tool I/O) + `ObservabilityService` | **BESTAAT** |
| Drift detectie | `CheckAlignmentService` (4 DriftTypes, alignment scoring) | **BESTAAT** |
| Agents corrigeren bij drift | Confucius PIV loop met 5 ImprovementStrategies | **BESTAAT** |
| Verwachte uitkomst vooraf valideren | `HypothesizeService` (expected outcome + recovery actions) | **BESTAAT** |
| Anti-pattern detectie | `AntiPatternDetector` (9 patronen, Gold Plating/Scope Creep blocking) | **BESTAAT** |
| Scope creep preventie | `RefactorGuardService` (change scope validation) | **BESTAAT** |
| Strategie wisselen (niet blind retries) | PIV `AGENT_SWITCH` + `DECOMPOSITION` + `CONTEXT_ENRICHMENT` | **BESTAAT** |
| Retry met escalatie | Kanban max 3 retries BUILD<->TEST, dan HUMAN_NEEDED lane | **BESTAAT** |
| Export naar observability tools | Geen OpenTelemetry/Langfuse integratie | **ONTBREEKT** -> Fase 60 |
| Kosten per ticket | `ObservabilityService` tracked globaal, niet per ticket | **GEDEELTELIJK** -> Fase 61 |
| Statistische drift detectie | Keyword-based, geen embedding drift | **ONTBREEKT** -> Fase 63 |

**Conclusie**: MarQed's BART-equivalent is **completer dan wat Tracer biedt**. De Confucius Orchestrator + alignment services + anti-pattern detection + hypothesis verificatie overtreffen BART Simpson. Gaps: externe observability export, per-ticket kosten, en statistische drift.

---

## 3. Open Source Alternatieven (2025-2026)

### Aanbevolen voor Integratie

| Tool | Wat het doet | Fase | Aanbeveling |
|---|---|---|---|
| **Langfuse** (MIT, self-hosted) | LLM observability, traces, evals, cost tracking, prompt management. Nu op ClickHouse + OpenTelemetry | **47** | **P0 - Integreren**. MarQed's traces exporteren via OTLP |
| **OpenTelemetry SDK** | Standaard tracing/metrics protocol (OTLP) | **47** | **P0 - Basis**. Adapter voor bestaande CCTrace/Observability data |
| **Arize Phoenix** (open-source) | AI observability, embedding drift detection, LLM evaluators | **52** | **P2 - Optioneel**. Complementeert ThinkingPatternStore |

### Niet Aanbevolen (al overtroffen door MarQed)

| Tool | Reden om NIET te adopteren |
|---|---|
| **LangGraph** | Confucius Orchestrator heeft al state machine, checkpoints, streaming, PIV loop |
| **CrewAI** | MarQed heeft al 11 role-based agents met gestructureerde delegatie |
| **AutoGen** | Conversational patterns nuttig als inspiratie, maar geen integratie nodig |
| **Sweep AI** | `IntakeToBacklogService` is al uitgebreider |

---

## 4. Roadmap Mapping: 5 Nieuwe Fases

### Prioriteit & Timing Analyse

De 5 verbetergebieden zijn als nieuwe fases op de roadmap geplaatst op basis van:
- **Prioriteit** (P0-P3)
- **Dependencies** op bestaande en geplande fases
- **Synergiewaarde** met aangrenzende roadmap items
- **Huidige roadmap capaciteit** per periode

### Roadmap Plaatsing

```
HUIDIGE ROADMAP (met Tracer/BART integratie):

Week 159-168: Fase 41 - Injection Vulnerability Scanners      🔴 NEXT (ongewijzigd)
Week 169-176: Fase 42 - Advanced FN Detection                 (ongewijzigd)
Week 177-180: Fase 43 - Zero-Complaints Strategy              (ongewijzigd)
Week 177-181: Fase 34 - Advanced Error Detectors               (ongewijzigd)

Week 179-182: ★ Fase 60 - Observability Foundation (OTLP/Langfuse)   🆕 P0
              │  Dependencies: Fase 23.5 ✅, CCTraceService ✅
              │  Synergy: Fundament voor Fase 32, 33, 48
              │
Week 183-188: Fase 32 - Ralph Wiggum Loop                     (ongewijzigd, profiteert van 47)
Week 183-188: ★ Fase 61 - Progress Dashboard & Per-Ticket Cost  🆕 P1
              │  Dependencies: Fase 60, SSE streaming ✅
              │  Synergy: Ralph progress tracking, DevStats data
              │
Week 185-192: Fase 37 - Security Agent Integration             (ongewijzigd)
Week 187-192: Fase 33 - DevStats Dashboard                    (ongewijzigd, profiteert van 47+48)
Week 185-200: Fase 25 - Core Platform Enhancement             (ongewijzigd)

Week 193-198: ★ Fase 62 - Conversational Intake (Epic Mode)    🆕 P1
              │  Dependencies: SpecShapingService ✅, IntakeToBacklogService ✅
              │  Synergy: Ralph PRP generation kan vanuit chat intake voeden
              │
Week 201-214: Fase 26 - AI & Automation                       (ongewijzigd)

Week 207-212: ★ Fase 63 - Statistical Drift Detection          🆕 P2
              │  Dependencies: Fase 60, ThinkingPatternStore ✅, CheckAlignmentService ✅
              │  Synergy: Versterkt Confucius drift detectie met embeddings
              │
Week 215-224: Fase 27 - Testing Excellence                    (ongewijzigd)
Week 225-236: Fase 28 - Advanced Integrations                 (ongewijzigd)

Week 229-234: ★ Fase 64 - Self-Evolution Activation            🆕 P3
              │  Dependencies: Fase 60+48 (metrics), LLMCouncilService ✅
              │  Synergy: AgentEvolutionService bestaat al, moet geactiveerd worden
              │
Week 237-254: Fase GAP-29 - Innovation & Scale                (ongewijzigd)
```

### Dependency Graph

```
                    ┌──────────────────────┐
                    │  Fase 23.5 Confucius  │
                    │     ✅ COMPLETE       │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼─────────────────┐
              │                │                  │
              ▼                ▼                  ▼
     ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
     │  Fase 31    │  │  Fase 23.6   │  │  CCTrace     │
     │  CWE Scan   │  │  Council     │  │  Service     │
     │  ✅ DONE    │  │  ✅ DONE     │  │  ✅ EXISTS   │
     └─────────────┘  └──────────────┘  └──────┬───────┘
                                               │
                                               ▼
                                    ┌──────────────────┐
                                    │  ★ Fase 60       │
                                    │  Observability   │
                                    │  Foundation (P0) │
                                    │  Week 179-182    │
                                    └────────┬─────────┘
                                             │
                    ┌────────────────────────┼─────────────────┐
                    │                        │                 │
                    ▼                        ▼                 ▼
           ┌──────────────┐       ┌──────────────┐   ┌──────────────┐
           │  ★ Fase 61   │       │  Fase 32     │   │  Fase 33     │
           │  Progress    │       │  Ralph Loop  │   │  DevStats    │
           │  Dashboard   │       │  Week 183    │   │  Week 187    │
           │  Week 183    │       └──────────────┘   └──────────────┘
           └──────┬───────┘
                  │
                  ├──────────────────────┐
                  ▼                      ▼
         ┌──────────────┐       ┌──────────────┐
         │  ★ Fase 63   │       │  ★ Fase 64   │
         │  Statistical  │       │  Self-Evolut │
         │  Drift (P2)  │       │  (P3)        │
         │  Week 207    │       │  Week 229    │
         └──────────────┘       └──────────────┘

         ┌──────────────┐
         │  SpecShaping  │
         │  Service ✅   │
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │  ★ Fase 62   │
         │  Conversa-   │
         │  tional (P1) │
         │  Week 193    │
         └──────────────┘
```

### Rationale per Plaatsing

| Fase | Week | Waarom hier? |
|------|------|-------------|
| **47** | 179-182 | **Voor Ralph (32) en DevStats (33)**. Observability is fundament: als Ralph autonome loops draait, moeten traces zichtbaar zijn in Langfuse. Parallel met Fase 43/34 (andere scope). |
| **48** | 183-188 | **Naast Ralph (32)**. Ralph genereert progress events die het dashboard consumeert. DevStats (33) bouwt voort op per-ticket cost data uit Fase 61. |
| **49** | 193-198 | **Na Ralph, binnen Fase 25 periode**. Chat interface is onafhankelijk van observability stack. Past bij Core Platform Enhancement (Fase 25). Ralph PRP-generatie kan later vanuit chat intake gevoed worden. |
| **52** | 207-212 | **Binnen Fase 26 AI & Automation**. Embedding-based drift is AI-heavy work dat past bij de AI & Automation periode. Profiteert van observability data uit Fase 60. |
| **53** | 229-234 | **Binnen Fase 28 Advanced Integrations**. Laagste prioriteit (P3). AgentEvolutionService bestaat al maar is niet geactiveerd. Heeft volledige metrics stack (47+48) nodig voor effectieve self-learning. |

---

## 5. Effort Summary (Nieuwe Fases)

| Fase | Titel | Effort | Weken | Prioriteit | Items |
|------|-------|--------|-------|------------|-------|
| **47** | Observability Foundation | ~48 uur | 4 | P0 | 6 taken (T1.1-T1.6) |
| **48** | Progress Dashboard | ~64 uur | 5 | P1 | 6 taken (T2.1-T2.6) |
| **49** | Conversational Intake | ~80 uur | 5 | P1 | 5 taken (T3.1-T3.5) |
| **52** | Statistical Drift Detection | ~72 uur | 5 | P2 | 3 taken (T4.1-T4.3) |
| **53** | Self-Evolution Activation | ~80 uur | 5 | P3 | 3 taken (T5.1-T5.3) |
| | **Totaal** | **~344 uur** | **~24 weken** | | **23 taken** |

---

## 6. Strategische Conclusies

1. **MarQed is verder dan Tracer/BART op backend-niveau.** Confucius Orchestrator met PIV loops, 5 improvement strategies, hypothesis verificatie, en 9 anti-pattern detectors overtreffen wat in de video beschreven wordt.

2. **De grootste gap is presentatie, niet logica.** MarQed mist: (a) OTLP export voor observability dashboards, (b) een visueel real-time voortgangsdashboard, (c) een conversationele chat interface.

3. **Langfuse integratie is de hoogste ROI.** OTLP export toevoegen aan bestaande traces geeft direct professionele dashboards, cost analysis, en eval pipelines - zonder bestaande code te vervangen.

4. **Niet LangGraph of CrewAI adopteren.** MarQed's Confucius Orchestrator biedt al gelijkwaardige of superieure orchestratie.

5. **Fase 32 (Ralph Wiggum Loop) complementeert dit plan.** Observability (47) moet vóór Ralph landen; Progress Dashboard (48) parallel met Ralph.

6. **Self-Evolution (53) heeft de langste aanloop.** Het benodigde metrics fundament (47+48) moet eerst stabiel zijn.

---

## 7. Verificatie per Fase

| Fase | Verificatie |
|------|------------|
| **47** | Langfuse dashboard openen, workflow uitvoeren, verifieer traces met spans en cost data |
| **48** | Progress dashboard API aanroepen tijdens workflow execution, verifieer SSE events per ticket |
| **49** | Chat sessie starten via WebSocket, 3-5 berichten uitwisselen, verifieer ticket generatie |
| **52** | Agent workflow uitvoeren met bekende drift, verifieer `StatisticalDriftDetector` alert |
| **53** | Meerdere workflows uitvoeren, verifieer `AgentEvolutionService` learning tasks |

---

## 8. Kritieke Bestanden (Bestaand)

| Bestand | Regels | Relevant voor |
|---------|--------|---------------|
| `backend/app/confucius/orchestrator.py` | ~704 | Fase 60 (spans), 52 (drift hooks) |
| `backend/app/services/cctrace_service.py` | ~300 | Fase 60 (OTLP adapter) |
| `backend/app/confucius/quality/streaming.py` | ~437 | Fase 61 (SSE aggregatie) |
| `backend/app/services/spec_shaping_service.py` | ~400 | Fase 62 (chat basis) |
| `backend/app/services/intake_to_backlog_service.py` | ~500 | Fase 62 (ticket generatie) |
| `backend/app/services/orchestration/check_alignment_service.py` | ~300 | Fase 63 (drift extend) |
| `backend/app/services/observability_service.py` | ~400 | Fase 60+48 (cost tagging) |
| `backend/app/services/thinking_pattern_store.py` | ~300 | Fase 63 (embedding drift) |
| `backend/app/services/agent_evolution_service.py` | ~400 | Fase 64 (activatie) |
| `backend/app/services/llm_council_service.py` | ~500 | Fase 64 (council review) |
| `docker-compose.yml` | ~200 | Fase 60 (Langfuse deployment) |

---

*Created: Week 162 (2026-01-31)*
*Author: Claude Code*
