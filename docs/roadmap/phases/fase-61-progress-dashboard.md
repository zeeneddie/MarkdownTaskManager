# Fase 61: Progress Dashboard & Per-Ticket Cost Tracking

**Status:** PLANNED
**Priority:** P1
**Timeline:** Week 183-188
**Effort:** ~64 uur (~5 weken)
**Dependencies:** Fase 60 (Observability Foundation), SSE Streaming ✅
**Source:** [Tracer/BART Gap Analyse](../tracer-bart-gap-analysis.md)

---

## Executive Summary

Real-time voortgang per ticket zichtbaar maken (Tracer sidebar equivalent). Combineert bestaande SSE events, OTLP trace data uit Fase 47, en per-ticket cost aggregatie tot een visueel dashboard.

**Het Probleem:**
> MarQed heeft 20+ SSE event types en volledige 9-lane Kanban backend, maar geen visuele consumer. Gebruikers zien niet wat er real-time gebeurt per ticket.

**De Oplossing:**
```
SSE Events (streaming.py) ──────┐
                                ├──► ProgressDashboardService ──► WebSocket ──► Dashboard UI
CCTrace + OTLP (Fase 47) ──────┤                                                ├── Agent Timeline (Gantt)
                                │                                                ├── Per-Ticket Cost
ObservabilityService ───────────┘                                                ├── Quality Score Trend
                                                                                 └── Lane Progression
```

---

## Taken

### T2.1: ProgressDashboardService (Medium)

**Bestanden:** Nieuw: `backend/app/services/progress_dashboard_service.py`, extend: `streaming.py`
**Effort:** 14 uur

Service die SSE events aggregeert naar per-ticket state:
- Consumeer bestaande `StreamEvent` types uit `streaming.py`
- Aggregeer naar per-ticket progress model: current stage, current agent, quality score, elapsed time
- Maintain in-memory ticket state map (ticket_id -> TicketProgress)
- Emit dashboard-specifieke events naar WebSocket clients
- Historical snapshots opslaan voor trend analyse

**TicketProgress Model:**
```python
@dataclass
class TicketProgress:
    ticket_id: str
    title: str
    current_lane: str       # 9-lane Kanban position
    current_stage: str      # Confucius workflow stage
    current_agent: str      # Active agent name
    quality_score: float    # Latest quality score
    cost_usd: float         # Accumulated cost
    tokens_used: int        # Total tokens
    started_at: datetime
    elapsed_seconds: float
    piv_iterations: int     # PIV loop count
    retries: int            # BUILD<->TEST retries
    events: List[ProgressEvent]  # Recent events timeline
```

### T2.2: Per-Ticket Cost Tagging in CCTrace (Laag)

**Bestanden:** `backend/app/services/cctrace_service.py`
**Effort:** 6 uur

Extend CCTraceService met ticket_id tagging:
- Voeg `ticket_id` parameter toe aan trace calls
- Tag OTLP spans met ticket_id attributen
- Aggregeer cost per ticket_id in ObservabilityService

### T2.3: Ticket-Level Cost Aggregatie Endpoint (Laag)

**Bestanden:** `backend/app/services/observability_service.py`, `backend/app/api/observability.py`
**Effort:** 8 uur

Nieuwe endpoints:
- `GET /api/observability/cost/ticket/{ticket_id}` - Cost breakdown per ticket
- `GET /api/observability/cost/workflow/{workflow_id}` - Cost per workflow
- `GET /api/observability/cost/agent/{agent_id}` - Cost per agent

Response model:
```json
{
  "ticket_id": "T-123",
  "total_cost_usd": 1.45,
  "breakdown": {
    "claude_opus": { "calls": 3, "tokens": 45000, "cost": 0.90 },
    "deepseek_v3": { "calls": 5, "tokens": 30000, "cost": 0.15 },
    "qwen_coder": { "calls": 2, "tokens": 20000, "cost": 0.40 }
  },
  "by_stage": {
    "constitution": 0.45,
    "specification": 0.30,
    "task_generation": 0.70
  }
}
```

### T2.4: WebSocket Endpoint voor Real-Time Progress (Medium)

**Bestanden:** Nieuw: `backend/app/api/progress_dashboard.py`
**Effort:** 12 uur

WebSocket endpoint die ProgressDashboardService events naar clients streamt:
- `ws://host/ws/progress/{workflow_id}` - Per-workflow stream
- `ws://host/ws/progress/all` - All active workflows
- JSON message format met event type, ticket state, delta updates
- Connection management: heartbeat, reconnect, backpressure
- Authentication via query parameter token

### T2.5: Agent Execution Timeline API (Medium)

**Bestanden:** Extend: `backend/app/confucius/workflows/base.py`, nieuw endpoint
**Effort:** 12 uur

Gantt-achtige timeline data per ticket:
- `GET /api/progress/timeline/{ticket_id}` - Agent execution timeline
- Response bevat per-agent time blocks met start, end, stage, result
- Inclusief quality score per block en PIV iterations

```json
{
  "ticket_id": "T-123",
  "timeline": [
    { "agent": "Peter", "stage": "constitution", "start": "...", "end": "...", "duration_ms": 5400, "quality": 0.85, "piv_iterations": 2 },
    { "agent": "Felix", "stage": "specification", "start": "...", "end": "...", "duration_ms": 3200, "quality": 0.92, "piv_iterations": 1 }
  ],
  "total_duration_ms": 25000,
  "agents_involved": 6
}
```

### T2.6: Frontend Dashboard Pagina (Medium)

**Bestanden:** Nieuw: `frontend/progress-dashboard.html`
**Effort:** 12 uur

HTML dashboard pagina (bestaand frontend pattern volgen):
- Real-time ticket cards met lane, agent, quality score
- Agent timeline visualisatie (horizontale Gantt bars)
- Cost breakdown donut chart
- Quality trend lijn chart
- Auto-refresh via WebSocket
- Responsive layout voor desktop en tablet

---

## Resultaat

Na implementatie:
- Real-time zichtbaarheid van welke agent wat doet per ticket
- Kosten per ticket, per agent, per stage
- Visuele timeline van agent executie (Gantt-achtig)
- Quality score trends over tijd
- Basis voor Ralph Wiggum progress monitoring (Fase 32)

## Success Criteria

- [ ] Dashboard toont real-time ticket progress binnen 1 seconde van SSE event
- [ ] Per-ticket cost correct berekend en geaggregeerd
- [ ] WebSocket verbinding stabiel voor 8+ uur (Ralph-compatible)
- [ ] Agent timeline API retourneert Gantt-data voor voltooide workflows
- [ ] Frontend dashboard bruikbaar op desktop (1920x1080+)
- [ ] 35+ unit tests voor ProgressDashboardService

---

*Created: Week 162 (2026-01-31)*
