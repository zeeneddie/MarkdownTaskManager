# 9-Lane Kanban System Architecture

**Parent Document:** [ARCHITECTURE.md](../../ARCHITECTURE.md)
**Status:** Week 58 COMPLETE | Week 80 KaibanJS Patterns Added
**Last Updated:** 2025-12-17

---

## Overview

Het 9-Lane Kanban systeem biedt multi-project task management met:
- Project selector met cascading filters
- 9 lanes (backlog → done + human_needed, blocked)
- KaibanJS-inspired automatic lane progression
- Real-time WebSocket updates
- Agent work result chaining

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         KANBAN DASHBOARD                                     │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  FILTERS                                                             │   │
│   │  [Project: HCI-CRS ▼]  [Epic: All ▼]  [Feature: All ▼]             │   │
│   │                                                                      │   │
│   │  Cascading: Project → Epic → Feature                                │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  9 LANES                                                             │   │
│   │                                                                      │   │
│   │  backlog → analysis → design → build → test → in_review → done      │   │
│   │                  + human_needed, blocked (special lanes)             │   │
│   │                                                                      │   │
│   │  Features:                                                           │   │
│   │  • Drag & drop between lanes                                         │   │
│   │  • Story point display per card                                      │   │
│   │  • Epic/Feature badges                                               │   │
│   │  • Agent assignment indicators                                       │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STATS (per selected project)                                        │   │
│   │                                                                      │   │
│   │  Total Items: 17  |  Story Points: 33  |  Blocked: 0                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Lane Configuration

### Standard Lanes (7)

| Lane | Description | Typical Duration |
|------|-------------|------------------|
| `BACKLOG` | Nieuw toegevoegd, nog niet geanalyseerd | - |
| `ANALYSIS` | Quinn/Eliza analyseren requirements | 1-2 uur |
| `DESIGN` | Felix ontwerpt oplossing | 2-4 uur |
| `BUILD` | Felix implementeert code | 4-8 uur |
| `TEST` | Tessa schrijft/runt tests | 2-4 uur |
| `IN_REVIEW` | Quinn doet code review | 1-2 uur |
| `DONE` | Afgerond en gemerged | - |

### Special Lanes (2)

| Lane | Description | Escalation Path |
|------|-------------|-----------------|
| `HUMAN_NEEDED` | Vereist menselijke beslissing | Manual resolution |
| `BLOCKED` | Geblokkeerd door externe dependency | Dependency resolved |

---

## KaibanJS Pattern Implementation (Week 80)

Geadopteerd van [KaibanJS](https://github.com/kaiban-ai/KaibanJS):

### Automatic Lane Progression Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AUTOMATIC LANE PROGRESSION ENGINE                        │
│                                                                              │
│  ┌──────────────┐    ┌────────────────┐    ┌──────────────┐                 │
│  │ Agent Work   │───▶│ Lane Progression│───▶│ WebSocket    │───▶ Dashboard  │
│  │ Completes    │    │ Service        │    │ Broadcast    │                 │
│  └──────────────┘    └────────────────┘    └──────────────┘                 │
│                              │                                               │
│                              ▼                                               │
│                    ┌────────────────┐                                       │
│                    │ Quality Gate   │                                       │
│                    │ Validation     │                                       │
│                    └────────────────┘                                       │
│                              │                                               │
│            ┌─────────────────┼─────────────────┐                            │
│            ▼                 ▼                 ▼                            │
│     ┌──────────┐      ┌──────────┐      ┌──────────┐                       │
│     │ PASS     │      │ FAIL     │      │ ESCALATE │                       │
│     │ → Next   │      │ → Retry  │      │ → Human  │                       │
│     └──────────┘      └──────────┘      └──────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Lane Flow Configuration

| Lane | Agents | Success Gate | Next Lane | Failure Lane |
|------|--------|--------------|-----------|--------------|
| ANALYSIS | Quinn, Eliza | estimation_complete | PLANNED | HUMAN_NEEDED |
| PLANNED | - | sprint_assigned | BUILD | - |
| BUILD | Felix | code_complete | TEST | HUMAN_NEEDED |
| TEST | Tessa | tests_pass | IN_REVIEW | BUILD (retry) |
| IN_REVIEW | Quinn | review_approved | DONE | BUILD |

### Implemented Patterns

| Pattern | Service Method | Description |
|---------|----------------|-------------|
| **Auto-Progression** | `LaneProgressionService.on_agent_complete()` | Agent completes → auto-move |
| **Task Chaining** | `get_previous_results()` | `{taskResult:taskN}` style output passing |
| **Quality Gates** | `_check_quality_gate()` | Per-lane criteria before progression |
| **Retry Tracking** | `_retry_counts` | BUILD↔TEST max 3x before escalation |
| **WebSocket Events** | `_broadcast_lane_change()` | Real-time dashboard updates |

### Retry & Escalation Logic

```python
# Maximum retries before escalation to HUMAN_NEEDED
MAX_RETRIES = {
    "BUILD_TO_TEST": 3,
    "TEST_TO_BUILD": 3,
    "REVIEW_TO_BUILD": 2,
}

# After 3 BUILD↔TEST cycles, escalate
if retry_count >= MAX_RETRIES["BUILD_TO_TEST"]:
    move_to_lane(item, "HUMAN_NEEDED")
    notify_human(f"Item {item.id} stuck in BUILD↔TEST loop")
```

---

## API Endpoints

### Core Kanban Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/kanban/projects` | GET | List projects with item counts |
| `/api/kanban/board` | GET | Get board items (filterable) |
| `/api/kanban/stats` | GET | Get stats for selected project |
| `/api/kanban/epics` | GET | Get epics for filter dropdown |
| `/api/kanban/{id}/move` | PATCH | Move item to different lane |
| `/api/kanban/cards/{type}/{id}` | GET | Get card details |

### Lane Progression Endpoints (Week 80)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/kanban/agents/complete` | POST | Agent work completion + auto-progression |
| `/api/kanban/items/{id}/journey` | GET | Item's complete lane journey |
| `/api/kanban/items/{id}/previous-results` | GET | All previous agent outputs (chaining) |

---

## WebSocket Events

### Real-time Dashboard Updates

```javascript
// WebSocket subscription for live Kanban updates
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.event === 'kanban_item_moved') {
        // Auto-animate card from old lane to new lane
        animateCardMove(data.item_id, data.from_lane, data.to_lane);
        // Show agent badge
        showAgentActivity(data.agent_name);
    }
};
```

### Event Types

| Event | Payload | Trigger |
|-------|---------|---------|
| `kanban_item_moved` | `{item_id, from_lane, to_lane, agent_name}` | Lane change |
| `kanban_item_created` | `{item_id, lane, type}` | New item |
| `kanban_item_blocked` | `{item_id, blocker_reason}` | Item blocked |
| `kanban_agent_working` | `{item_id, agent_name, lane}` | Agent started |

---

## Project Selector

### Database Query

```python
@router.get("/projects")
async def get_projects_for_filter(db: AsyncSession):
    """
    Get list of projects that have items in the Kanban board.
    Returns projects with item counts from stories, tasks, and bugs.

    Response: [
        {"id": "uuid", "name": "HCI-CRS", "item_count": 17},
        {"id": "uuid", "name": "Multi-Stack AI Agent Platform", "item_count": 54}
    ]
    """
```

### Registered Projects

| Project | Type | Items | Story Points | Status |
|---------|------|-------|--------------|--------|
| HCI-CRS | VB.NET/ASP.NET | 17 | 33 | Active |
| Multi-Stack AI Agent Platform | Python/FastAPI | 54 | 126 | Active |
| Klaverjas Competitie | Python/Flask | 12 | 21 | Active |

---

## Dashboard Experience

```
Migration draait → Items bewegen automatisch:

BACKLOG → ANALYSIS → PLANNED → BUILD → TEST → IN_REVIEW → DONE
            ↓           ↓        ↓       ↓         ↓
         (Quinn)     (Paul)   (Felix) (Tessa)   (Quinn)

WebSocket broadcast bij elke lane change → Dashboard auto-updates
```

---

## Related Documents

- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Main architecture overview
- [integration-services.md](./integration-services.md) - CCPM integration
- [quality-gates.md](./quality-gates.md) - Quality gate system
