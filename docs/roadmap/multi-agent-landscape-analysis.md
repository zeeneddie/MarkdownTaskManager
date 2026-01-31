# Multi-Agent Orchestration Landscape vs MarQed: Analyse & Advies

**Status:** STRATEGISCH ADVIES
**Created:** Week 162 (2026-01-31)
**Source:** Reddit post r/ClaudeAI over multi-agent orchestration tools + 48 comments
**Priority:** Informatief - geen nieuwe fases nodig

---

## Quick Navigation

| Sectie | Content |
|--------|---------|
| [1. Geanalyseerde Tools](#1-geanalyseerde-tools) | Overzicht van 10 tools in 3 tiers |
| [2. Kritieke Inzichten](#2-kritieke-inzichten-uit-comments) | Kernboodschappen uit Reddit comments |
| [3. Gap Analyse](#3-gap-analyse-marqed-vs-deze-tools) | Wat MarQed heeft en mist |
| [4. Advies](#4-advies) | A: Niet adopteren, B: Monitoren, C: Overwegen, D: Actiepunten |
| [5. Strategische Conclusie](#5-strategische-conclusie) | MarQed's positie in het landschap |
| [6. Roadmap Impact](#6-roadmap-impact) | Kleine toevoegingen aan bestaande fases |

---

## 1. Geanalyseerde Tools

### Tier 1: Orchestration Engines

| Tool | Stars | Wat het doet | Status |
|------|-------|-------------|--------|
| **CodeMachine CLI** | 2.2k | Meta-orchestrator bovenop Claude Code/Codex/OpenCode. Spec -> workflow -> parallel agents. File-based memory met SQLite. | Pre-production (eigen disclaimer). Interessant architectuur-concept. |
| **Claude Flow** | 13.4k | Queen-led swarm model met SPARC methodology, 60+ agents, RuVector DB. | V3 alpha, gebruikers rapporteren dat het niet werkt (GitHub #958). Veel marketing, weinig werkende code. |
| **Swarms** | 5.7k | 8 orchestratie-patronen (sequential, concurrent, graph, mixture). Python. | **Ernstige geloofwaardigheidsproblemen**: name-squatting, crypto-token scam ($SWARMS), niet-werkende code. Vermijden. |
| **npcpy** | 1.2k | AI agents als "NPCs" met personas. Flask REST API deployment. | Research-oriented, klein, geen MCP support. |

### Tier 2: Spec-Driven Development

| Tool | Stars | Wat het doet | Status |
|------|-------|-------------|--------|
| **SpecKit** (GitHub official) | 66.5k | 4-fase SDD: Specify -> Plan -> Tasks -> Implement. 20+ AI agents supported. | Meest volwassen. GitHub-backed. Geen dependency tracking. |
| **OpenSpec** | 21.2k | Lightweight spec layer. Artifact graph tracked state. "Fluid not rigid." | Actief maintained (v1.1.1, jan 2026). Goed concept. |
| **TaskMaster** | 25.2k | PRD -> structured dependency-aware tasks. MCP integration. | Meest praktisch. 1M+ npm downloads. Building "Hamster" (multiplayer). |

### Tier 3: Context Management

| Tool | Stars | Wat het doet | Status |
|------|-------|-------------|--------|
| **Context-Engine** (m1rl0k) | 305 | MCP retrieval stack. Semantic code chunks (5-50 lines). Qdrant + Redis. | BUSL license (restrictief). Zware infra. Niet production-ready. |
| **AugmentCode CE** | SaaS | Cloud-hosted semantic code index als MCP server. | Proprietary. Privacy-concern (code op hun servers). Gratis introductie maar vendor lock-in. |

---

## 2. Kritieke Inzichten uit Comments

### De slimste commentaar: "Context management IS the whole multi-agent game"

> "At the end of the day it's about getting the right stuff in your context. Claude Code can do that very well, especially if you give it the right tools. Multi agent sounds tempting, but it's a lot more work to make sure that every agent has the understanding they need." - farox

### De nuchtere commentaar: "Less scaffolding as models improve"

> "You need less and less scaffolding as the models get better. I've tried a lot of these multi agent persona approaches and they're all kinda overly complex" - das_war_ein_Befehl

### De fundamentele kritiek op swarms

Een technische analyse (jsulmont.github.io) identificeert structurele problemen:

- **Geen shared decision register**: Agent A kiest een library, Agent B weet dat niet
- **Non-persistent intent**: Context verdwijnt na elke task
- **Geen enforcement authority**: Geen agent kan andermans werk afwijzen
- **Scaling amplifies incoherence**: Meer agents = meer drift, duplicatie, contradictie

### De praktische stem: "All you need is good Claude.md + plan + status file"

> "I gave each of those tools a spin... none of them improved the output compared to normal well written prompt." - Natrium83

---

## 3. Gap Analyse: MarQed vs Deze Tools

### Wat MarQed AL HEEFT (en de meeste tools NIET)

| Capability | MarQed Implementation | Tools die dit missen |
|-----------|----------------------|---------------------|
| **Shared decision register** | Confucius OrchestratorState (8 states) + HierarchicalMemory (3 scopes) | Swarms, Claude Flow, CodeMachine |
| **Enforcement authority** | PIV loop + AntiPatternDetector (9 patterns) + RefactorGuardService | Alle tools |
| **Persistent intent** | Session-scope memory (permanent) + Entry-scope (30 dagen) + Runnable (7 dagen) | Alle tools behalve Context-Engine |
| **Drift detectie & correctie** | CheckAlignmentService (4 DriftTypes) + 5 ImprovementStrategies | Geen enkele tool |
| **Spec -> Code pipeline** | SpecShapingService -> Peter (Constitution) -> Felix (Specification) -> IntakeToBacklogService | SpecKit/OpenSpec (alleen spec, geen execution) |
| **Quality gates per stage** | WorkflowStage met quality_threshold, max_iterations, parallel agents | CodeMachine (basic), Claude Flow (claims) |
| **Domain-aware task generation** | BusinessDomainExtractor + BusinessDrivenStoryGenerator | TaskMaster (generic PRD parsing) |
| **12 specialized agents** | Felix, Quinn, Peter, Eliza, Betty, Diana, Paul, Miguel, Marcus, Tessa, Vicky + Stage Review | Claude Flow claimt 60+ maar werkt niet |
| **Extension router met scoring** | Dynamic task-to-agent matching (0.0-1.0) met threshold en priority | CodeMachine (static assignment) |
| **Checkpoint/Resume** | Restartable workflows met checkpoint systeem (Fase 24.6) | CodeMachine (basic) |
| **29 orchestration services** | HATEOAG, Taskchain, SemanticZoom, LoopCondition, FeedbackLoop, CrossContextMemory, etc. | Geen equivalent |

### Wat MarQed MIST (maar deze tools WEL hebben)

| Gap | Tool die het heeft | Relevantie voor MarQed | Aanbeveling |
|-----|-------------------|----------------------|-------------|
| **Extern model orchestratie** (Claude+Codex+Gemini parallel) | CodeMachine | Laag - MarQed gebruikt al LLMCouncilService met multi-model | Niet nodig |
| **Spec-first methodology formalisering** | SpecKit, OpenSpec | Medium - MarQed heeft SpecShaping maar geen formele SDD workflow | Inspiratie, geen adoptie |
| **PRD -> dependency-aware task lists** | TaskMaster | Medium - IntakeToBacklogService doet dit al, maar TaskMaster's dependency graph is eleganter | Inspiratie voor Fase 62 |
| **Semantic code indexing als MCP** | AugmentCode, Context-Engine | Medium-Hoog - MarQed's context_optimizer.py + reference_selector.py doen dit intern, maar niet als MCP server | **Overweeg** MCP exposure |
| **Multiplayer/collaborative planning** | TaskMaster Hamster | Laag - MarQed is single-user platform | Niet relevant nu |
| **Visual swarm topologies** | Swarms (einsum notation) | Laag - Confucius heeft al state machine met routing | Niet nodig |

---

## 4. Advies

### A. NIET ADOPTEREN (geen meerwaarde boven MarQed)

| Tool | Reden |
|------|-------|
| **Swarms** | Geloofwaardigheidsproblemen, crypto-scam, niet-werkende code. MarQed's Confucius is al superieur. |
| **Claude Flow** | V3 alpha werkt niet (GitHub #958). Marketing > realiteit. MarQed's orchestration is stabieler. |
| **npcpy** | Te klein, geen MCP, research-only. Geen meerwaarde. |
| **Context-Engine** (m1rl0k) | BUSL license, zware infra, 305 stars. MarQed's eigen context stack is al beter geintegreerd. |
| **CodeMachine CLI** | Interessant concept maar pre-production, single maintainer. MarQed doet hetzelfde intern. |

### B. MONITOREN (nuttige concepten, niet adopteren)

| Tool | Wat te monitoren | Waarom |
|------|-----------------|--------|
| **SpecKit** (GitHub) | SDD methodology, slash command patterns | GitHub-backed, 66.5k stars. De 4-fase SDD aanpak (Specify->Plan->Tasks->Implement) is een goede formalisering van wat MarQed al doet. Kan inspiratie zijn voor Fase 62 (Conversational Intake). |
| **OpenSpec** | Artifact graph concept, "fluid not rigid" philosophy | De state tracking via artifact graphs is elegant. MarQed's SpecShapingService zou een vergelijkbare state graph kunnen krijgen. |
| **TaskMaster** | Dependency-aware task decomposition, Hamster multiplayer | 25k stars, 1M npm downloads. De dependency graph aanpak voor tasks is beter geformaliseerd dan MarQed's IntakeToBacklogService. De "Hamster" multiplayer richting is interessant als MarQed ooit multi-user wordt. |

### C. OVERWEGEN VOOR INTEGRATIE (1 item)

| Tool | Actie | Fase | Rationale |
|------|-------|------|-----------|
| **AugmentCode Context Engine MCP** | Evalueer als aanvulling op MarQed's eigen context stack | Na Fase 60 | AugmentCode's semantic indexing is indrukwekkend (89-94% relevance). Het is gratis, read-only, en SOC 2 compliant. **Risico**: vendor lock-in en privacy (code op hun servers). **Alternatief**: MarQed's eigen `context_optimizer.py` + `reference_selector.py` exposeren als MCP server - dit is waarschijnlijk de betere route. |

### D. CONCRETE ACTIEPUNTEN VOOR MARQED

#### D1. MarQed Context Stack als MCP Server (Nieuw idee uit analyse)

**Wat**: Exposeer MarQed's bestaande context management (ContextOptimizer, ReferenceSelector, ReferenceRegistry) als MCP server, zodat externe AI tools (Claude Code, Cursor, etc.) MarQed's codebase-kennis kunnen benutten.

**Waarom**: Dit is precies wat AugmentCode en Context-Engine doen, maar dan met MarQed's eigen data en zonder vendor lock-in. De Reddit comments bevestigen: "context management IS the whole multi-agent game."

**Wanneer**: Kan als onderdeel van Fase 60 (Observability Foundation) of als klein apart item.

#### D2. Formaliseer MarQed's SDD Workflow (Inspiratie uit SpecKit)

**Wat**: Documenteer en formaliseer MarQed's spec-driven pipeline als een benoemde methodology:

```
MarQed SDD Pipeline:
1. INTAKE:      ConversationalIntake / SoftwareIntake -> requirements
2. SHAPE:       SpecShapingService -> validated spec (5 quality categories)
3. CONSTITUTE:  Peter agent -> constitution document
4. SPECIFY:     Felix agent -> technical specification
5. GENERATE:    IntakeToBacklogService -> epic/feature/story hierarchy
6. EXECUTE:     Confucius Orchestrator -> PIV loop -> quality gates
```

**Waarom**: MarQed heeft dit al, maar het is niet als coherente methodology gedocumenteerd. SpecKit (66.5k stars) bewijst dat er enorme vraag is naar geformaliseerde SDD. MarQed's pipeline is completer maar minder zichtbaar.

**Wanneer**: Documentatie-taak, kan direct.

#### D3. Dependency Graph voor Generated Tasks (Inspiratie uit TaskMaster)

**Wat**: Voeg expliciete dependency tracking toe aan IntakeToBacklogService's gegenereerde stories. Elke GeneratedStory krijgt een `depends_on: List[str]` veld.

**Waarom**: TaskMaster's key feature is dependency-aware task sequencing. MarQed genereert al epics/features/stories maar zonder expliciete dependencies. Dit zou de kwaliteit van gegenereerde backlogs verhogen.

**Wanneer**: Kan mee in Fase 62 (Conversational Intake) of als kleine enhancement.

---

## 5. Strategische Conclusie

### MarQed's Positie in het Landschap

```
TOOL LANDSCAPE (jan 2026):

ORCHESTRATION LAYER:
  Swarms ---------- broken, crypto scam
  Claude Flow ----- V3 alpha, not working
  CodeMachine ----- interesting but pre-production
  * MarQed -------- PRODUCTION: Confucius + PIV + 12 agents + 29 services

SPEC LAYER:
  SpecKit ---------- GitHub-backed, 66.5k stars, methodology focus
  OpenSpec --------- Lightweight, artifact graph
  TaskMaster ------- PRD->tasks, dependency graphs, 25k stars
  * MarQed -------- SpecShaping + Peter + Felix + IntakeToBacklog (completer pipeline)

CONTEXT LAYER:
  AugmentCode ----- Best-in-class semantic indexing (proprietary, SaaS)
  Context-Engine -- OSS maar BUSL license, heavy infra
  * MarQed -------- ContextOptimizer + ReferenceSelector + HierarchicalMemory (intern)

OBSERVABILITY:
  Langfuse --------- OSS, OTLP, self-hosted <- REEDS GEPLAND (Fase 60)
  * MarQed -------- CCTraceService + ObservabilityService (intern, geen export)
```

### Kernboodschap

**MarQed is technisch verder dan alle genoemde OSS tools op orchestration en spec-to-code niveau.** De Reddit post en comments bevestigen dat:

1. Multi-agent orchestratie is de juiste richting (maar de meeste tools zijn nog niet productie-ready)
2. Context management is het echte probleem (MarQed lost dit al op met HierarchicalMemory)
3. De fundamentele kritiek op swarms (geen shared state, no enforcement) geldt NIET voor MarQed (Confucius heeft dit)
4. De markt wil geformaliseerde methodologies (SpecKit 66.5k stars) - MarQed heeft de techniek maar niet de marketing

**Grootste kans**: MarQed's bestaande capabilities beter documenteren en exposeren (MCP server, formele methodology naam). De techniek is er, de zichtbaarheid niet.

---

## 6. Roadmap Impact

### Geen nieuwe fases nodig

De analyse levert **geen nieuwe fases** op. De bestaande roadmap (incl. Fase 60-64 uit Tracer/BART analyse) dekt alles al:

| Gevonden gap | Gedekt door |
|-------------|-------------|
| Observability/export | Fase 60 (OTLP/Langfuse) |
| Progress dashboard | Fase 61 (Dashboard) |
| Conversational intake (SpecKit/OpenSpec equivalent) | Fase 62 (Epic Mode) |
| Statistical drift (beter dan Arize Phoenix) | Fase 63 (Drift Detection) |
| Self-evolution | Fase 64 (Evolution Activation) |

### Kleine toevoegingen aan bestaande fases

| Item | Toevoegen aan | Effort |
|------|--------------|--------|
| D1: MCP Server voor MarQed Context | Fase 60 of nieuw klein item | 16-24h |
| D2: SDD Methodology documentatie | Documentatie (geen fase) | 4-8h |
| D3: Task dependency graphs | Fase 62 | 8-12h |

---

## 7. Verificatie

Dit document bevat:
- [x] Tool vergelijkingstabellen (10 tools in 3 tiers)
- [x] MarQed positie-analyse (capabilities die MarQed heeft en mist)
- [x] Concrete aanbevelingen (A: niet adopteren, B: monitoren, C: overwegen, D: actiepunten)
- [x] Roadmap impact assessment (geen nieuwe fases, 3 kleine toevoegingen)
- [x] Strategisch advies met onderbouwing uit Reddit comments

### Gerelateerde documenten

- [Tracer/BART Gap Analyse](tracer-bart-gap-analysis.md) - Eerdere analyse die Fase 60-64 definieerde
- [Gap Analyse Complete Roadmap](gap-analysis-complete-roadmap.md) - Volledige roadmap overzicht
