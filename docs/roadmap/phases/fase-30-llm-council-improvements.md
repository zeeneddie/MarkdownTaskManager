# Fase 30: LLM Council Improvements (Week 233-235)

**Goal:** Optimalisatie van de bestaande LLM Council implementatie met streaming, timeouts, en performance tracking
**Specification:** [docs/architecture/llm-council-improvements-plan.md](../../architecture/llm-council-improvements-plan.md)
**Status:** PLANNED
**Priority:** LOW (niet urgent - huidige implementatie is functioneel)
**Origin:** Analyse van externe repos (sage2, llm-council, lm-council, llm-council-plus)

---

## Problem Statement

De huidige LLM Council implementatie is functioneel compleet maar mist optimalisaties:
- Geen real-time feedback tijdens deliberation (30-60s stilte)
- Eén globale timeout (traag model blokkeert alles)
- Statische model weights (geen data-driven optimalisatie)
- Geen actuele informatie voor tech-vragen

---

## Solution Overview

| Verbetering | Impact | Effort |
|-------------|--------|--------|
| **SSE Streaming** | 10x betere perceived UX | 20 uur |
| **Stage Timeouts** | 40-60% sneller in edge cases | 14 uur |
| **Performance Tracking** | Data-driven model weights | 26 uur |
| **Web Search Enrichment** | Actuele informatie | 12 uur |

---

## Week-by-Week Deliverables

| Week | Focus | Hours | Output |
|------|-------|-------|--------|
| **233** | Streaming & Timeouts | 28 | SSE streaming, stage-level timeouts, graceful degradation |
| **234** | Performance Tracking | 26 | Metrics DB, leaderboard API, dashboard |
| **235** | Web Enrichment | 18 | Context enrichment, integration tests, docs |

---

## New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/council/{session_id}/stream` | GET | SSE streaming endpoint |
| `/api/council/performance/metrics` | GET | All model metrics |
| `/api/council/performance/leaderboard/{use_case}` | GET | Leaderboard per use case |
| `/api/council/performance/weights/recommended` | GET | Recommended weights |
| `/api/council/config/timeouts` | GET/PUT | Timeout configuration |

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Perceived response time | 30-60s waiting | <5s first token |
| Edge case latency | 60s+ timeout | <30s graceful |
| Weight accuracy | Static assumed | Data-driven |

---

## Total Effort: 72 hours (~2 weeks)

---

## Dependencies

| Dependency | Status |
|------------|--------|
| `sse-starlette` | TO INSTALL |
| Web search service | EXISTS |
| LLM Council | EXISTS |

---

← [Back to Overview](../phases-planned.md)
