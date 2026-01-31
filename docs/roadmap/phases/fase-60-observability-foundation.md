# Fase 60: Observability Foundation (OTLP/Langfuse)

**Status:** PLANNED
**Priority:** P0 (Highest ROI)
**Timeline:** Week 179-182
**Effort:** ~48 uur (~4 weken)
**Dependencies:** Fase 23.5 (Confucius Orchestrator) ✅, CCTraceService ✅
**Source:** [Tracer/BART Gap Analyse](../tracer-bart-gap-analysis.md)

---

## Executive Summary

Bestaande trace data (CCTrace, ObservabilityService) exporteren naar standaard OpenTelemetry (OTLP) formaat en Langfuse voor professionele dashboards, cost tracking, en eval pipelines - zonder bestaande code te vervangen.

**Het Probleem:**
> MarQed tracked al uitgebreid wat agents doen (thinking blocks, tool I/O, state transitions), maar deze data is alleen intern zichtbaar. Geen professionele dashboards, geen cost-per-ticket analyse, geen standaard export.

**De Oplossing:**
```
CCTraceService ──────┐
                     ├──► OTelExporterService ──► OTLP ──► Langfuse
ObservabilityService ┘                                      ├── Traces Dashboard
ConfuciusOrchestrator ──► OTLP Spans                        ├── Cost Analysis
WorkflowOrchestrator ──► OTLP Spans                         └── Eval Pipelines
```

---

## Taken

### T1.1: OpenTelemetry Dependencies (Laag)

**Bestanden:** `backend/requirements.txt`
**Effort:** 2 uur

Toevoegen:
```
opentelemetry-sdk>=1.25.0
opentelemetry-api>=1.25.0
opentelemetry-exporter-otlp>=1.25.0
opentelemetry-instrumentation-fastapi>=0.46b0
```

### T1.2: OTelExporterService (Medium)

**Bestanden:** Nieuw: `backend/app/services/otel_exporter_service.py`, extend: `cctrace_service.py`
**Effort:** 12 uur

Service die CCTrace spans converteert naar OTLP formaat:
- Map CCTrace `thinking_blocks` naar OTLP spans met attributen
- Map `tool_executions` naar child spans met duration, status
- Map `session_id` naar trace context
- Token usage als span attributen (input_tokens, output_tokens, total_tokens)
- Cost berekening als span attributen (cost_usd)
- Provider info (claude, codex, ollama) als resource attributen

**Integration met bestaande CCTraceService:**
- Hook in `CCTraceService` die na elke trace automatisch OTLP export triggert
- Configureerbaar: OTLP aan/uit, endpoint URL, sampling rate

### T1.3: Confucius State Transitions als OTLP Spans (Medium)

**Bestanden:** `backend/app/confucius/orchestrator.py`
**Effort:** 10 uur

Instrumenteer:
- `ConfuciusOrchestrator` state machine transitions als parent spans
- PIV loop iteraties als child spans (iteration number, quality score, strategy used)
- Extension calls als child spans (extension name, duration, result)
- Memory operations (read/write) als events op spans
- `OrchestratorState` transitions als span events

**Span Hierarchy:**
```
confucius.workflow (parent)
├── confucius.stage.constitution (child)
│   ├── confucius.piv.iteration_1
│   │   ├── confucius.extension.check_alignment
│   │   └── confucius.extension.hypothesize
│   └── confucius.piv.iteration_2
├── confucius.stage.specification
└── confucius.stage.task_generation
```

### T1.4: WorkflowOrchestrator Stage Execution Instrumenteren (Medium)

**Bestanden:** `backend/app/confucius/workflows/base.py`
**Effort:** 10 uur

Instrumenteer:
- Stage start/complete als spans (stage name, agent, duration)
- Quality gate evaluaties als span events
- Stage dependencies als span links
- Agent output quality scores als span attributen
- Streaming events correleren met OTLP trace context

### T1.5: Langfuse Self-Hosted Deployment (Laag)

**Bestanden:** `docker-compose.yml`
**Effort:** 6 uur

Toevoegen aan bestaande docker-compose:
```yaml
langfuse:
  image: langfuse/langfuse:latest
  ports:
    - "3100:3000"
  environment:
    - DATABASE_URL=postgresql://...
    - NEXTAUTH_SECRET=...
    - SALT=...
    - TELEMETRY_ENABLED=false
  depends_on:
    - postgres

langfuse-clickhouse:
  image: clickhouse/clickhouse-server:latest
  ports:
    - "8123:8123"
  volumes:
    - langfuse_clickhouse_data:/var/lib/clickhouse
```

### T1.6: OTLP Exporter Configuratie (Laag)

**Bestanden:** `backend/app/confucius/config.py`
**Effort:** 4 uur

Configuratie toevoegen:
```python
class OTelConfig:
    enabled: bool = False
    endpoint: str = "http://localhost:3100"  # Langfuse OTLP endpoint
    service_name: str = "marqed-confucius"
    sampling_rate: float = 1.0  # 100% sampling
    export_batch_size: int = 512
    export_timeout_ms: int = 30000
```

---

## Resultaat

Na implementatie:
- Alle agent traces zichtbaar in Langfuse dashboards
- Cost tracking per LLM call (token usage, provider, model)
- Latency analyse per workflow stage
- PIV loop efficiency metrics (iteraties per convergentie)
- Basis gelegd voor Fase 48 (per-ticket aggregatie) en Fase 52 (drift analyse)

## Success Criteria

- [ ] OTLP spans verschijnen in Langfuse binnen 5 seconden na workflow stage
- [ ] Cost data correct berekend per provider (Claude, Codex, Ollama)
- [ ] Confucius PIV loop iteraties zichtbaar als geneste spans
- [ ] Langfuse dashboard operationeel via docker-compose
- [ ] Geen performance degradatie (< 5% latency overhead)
- [ ] 30+ unit tests voor OTelExporterService

## Synergiewaarde

| Fase | Synergy |
|------|---------|
| **32 (Ralph Wiggum)** | Ralph loop iteraties zichtbaar als traces; cost per autonome run |
| **33 (DevStats)** | Developer metrics gevoed door OTLP trace data |
| **61 (Dashboard)** | Dashboard aggregeert OTLP spans naar per-ticket view |
| **63 (Drift)** | Embedding drift analyse op OTLP trace embeddings |

---

*Created: Week 162 (2026-01-31)*
