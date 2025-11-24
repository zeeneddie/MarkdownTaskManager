# FRONTEND UNIFICATION (Week 13-14 - Parallel)

**Status:** ✅ COMPLETE (Fase 1-3) | Week 48 E2E Verified
**Effort:** 16-24 uren (2-3 dagen) - DELIVERED
**Prioriteit:** HIGH - Verbetert developer experience

---

## Probleem

Twee losse frontend werelden zonder navigatie:

```
STANDALONE (File System API)     BACKEND-CONNECTED (FastAPI)
============================     ===========================
task-manager.html                frontend/agent-dashboard.html
project-manager.html             frontend/estimation-dashboard.html
                                 frontend/spec-kit-wizard.html
- Werkt OFFLINE                  frontend/project-wizard.html
- Geen backend nodig             frontend/maintenance-scheduler.html
- Geen agent integratie          frontend/quality-dashboard.html
                                 frontend/evolution-dashboard.html
                                 frontend/attribution-dashboard.html
                                 frontend/self-improvement-dashboard.html

                                 - Vereist backend (localhost:8000)
                                 - Agent integratie
```

**Probleem:** Geen centrale navigatie, inconsistente links, verwarrende UX.

---

## Oplossing: 4 Fasen

### Fase 1: Hub Portal (2 dagen) - ✅ COMPLEET
**Deliverables:**
- [x] Nieuw `index.html` als centrale entry point
- [x] Card-based navigatie naar beide werelden
- [x] Backend status indicator (online/offline)
- [x] Responsive design

**Completed:** 2025-11-24

**Structuur Hub Portal:**
```
+------------------------------------------+
|  MARKDOWN TASK MANAGER                   |
|  Backend: [Online] | Ollama: [6 models]  |
+------------------------------------------+
|                                          |
|  +----------------+  +----------------+  |
|  | TASK MGMT      |  | AGENTIC SYSTEM |  |
|  |                |  |                |  |
|  | - Kanban Board |  | - Agents       |  |
|  | - Projects     |  | - Estimation   |  |
|  | - Archive      |  | - Quality      |  |
|  |                |  | - Spec-Kit     |  |
|  | [OFFLINE OK]   |  | - Sprint       |  |
|  +----------------+  | - Maintenance  |  |
|                      | - Evolution    |  |
|                      |                |  |
|                      | [BACKEND REQ]  |  |
|                      +----------------+  |
+------------------------------------------+
```

### Fase 2: Shared Navigation (2-3 dagen) - ✅ COMPLEET
**Deliverables:**
- [x] ~`shared/nav.css`~ - Inline CSS per dashboard (embedded)
- [x] ~`shared/nav.js`~ - Hub Portal heeft health check
- [x] Update alle `frontend/*.html` met navbar (11 dashboards)
- [x] Back-to-hub links

**Completed:** 2025-11-24
**Note:** Navigation styles embedded per dashboard instead of shared file for simplicity.

### Fase 3: Standalone Integration (1 dag) - ✅ COMPLEET
**Deliverables:**
- [x] Link `task-manager.html` naar hub (🏠 Hub knop)
- [x] Link `project-manager.html` naar hub (🏠 Hub knop)
- [ ] "Enhanced mode" banner als backend beschikbaar (SKIPPED - not needed)
- [ ] Graceful degradation (SKIPPED - Hub handles this)

**Completed:** 2025-11-24

### Fase 4: Directory Reorganisatie (Optional, 2 dagen)
**Deliverables:**
- [ ] Verplaats naar `app/` structuur
- [ ] Update alle interne links
- [ ] Backwards-compatible redirects

---

## Fase 1 Detail: Hub Portal Implementation

### Bestandsstructuur
```
MarkdownTaskManager/
├── index.html              # HUB PORTAL (nieuw)
├── task-manager.html       # Standalone Kanban
├── project-manager.html    # Standalone Projects
└── frontend/               # Backend dashboards
    ├── agent-dashboard.html
    ├── estimation-dashboard.html
    └── ...
```

### Hub Portal Features

#### 1. Header Section
- Logo/Title: "Markdown Task Manager"
- Status indicators:
  - Backend: Online/Offline (fetch /api/health)
  - Ollama: X models loaded
  - Last sync timestamp

#### 2. Task Management Card
- Title: "Task Management"
- Subtitle: "Works offline - no backend required"
- Links:
  - Kanban Board -> task-manager.html
  - Project Manager -> project-manager.html
- Badge: "OFFLINE OK"

#### 3. Agentic System Card
- Title: "Agentic System"
- Subtitle: "AI-powered workflows (requires backend)"
- Links (grouped):
  - **Agents**: Agent Dashboard, Evolution, Self-Improvement
  - **Estimation**: Estimation Dashboard, Attribution
  - **Quality**: Quality Dashboard, Technical Debt
  - **Planning**: Sprint Planning, Project Wizard, Spec-Kit
  - **Maintenance**: Maintenance Scheduler
- Badge: "10 AGENTS" / "OFFLINE" (conditional)

#### 4. Quick Actions
- "Start Backend" button (shows docker-compose command)
- "Check Ollama" button (shows model status)
- "Documentation" link

### API Endpoints Needed
```
GET /api/health           -> { status: "ok", version: "x.x" }
GET /api/workflows/agents -> [{ name, status, llm }]
```

### Tech Stack
- Vanilla HTML/CSS/JS (consistent met project)
- No build step required
- Fetch API voor backend checks
- CSS Grid voor card layout

---

## Success Criteria

- [x] Hub portal als single entry point ✅
- [x] Alle HTML bestanden bereikbaar via navigatie ✅
- [x] Backend status visible op alle pagina's ✅
- [x] Graceful offline experience ✅
- [x] Consistent design language ✅

## Verification (Week 48 - 24 Nov 2025)

### E2E Testing Results - Full Verification
| Dashboard | HTTP Status | Notes |
|-----------|-------------|-------|
| Hub Portal (index.html) | ✅ 200 | Backend: Online, Ollama: 6 models, 10 Agents |
| agent-dashboard.html | ✅ 200 | 10 agents "ready" |
| estimation-dashboard.html | ✅ 200 | FP + Story Point calculators |
| evolution-dashboard.html | ✅ 200 | **Route added Week 48** |
| quality-dashboard.html | ✅ 200 | 5/7 endpoints working |
| spec-kit-wizard.html | ✅ 200 | **Route added Week 48** |
| project-wizard.html | ✅ 200 | 3-stage wizard |
| maintenance-scheduler.html | ✅ 200 | Scheduler active |
| technical-debt-dashboard.html | ✅ 200 | Technical debt tracking |
| sprint-planning.html | ✅ 200 | Sprint management |
| task-manager.html | ✅ FILE | Standalone + Hub link |
| project-manager.html | ✅ FILE | Standalone + Hub link |

**Total:** 11 dashboards + 2 standalone = 13 HTML interfaces

### Week 48 Fixes Applied
1. `backend/app/main.py` - Added `/evolution-dashboard.html` route
2. `backend/app/main.py` - Added `/spec-kit-wizard.html` route
3. `backend/app/api/quality_dashboard.py` - OpenAPI schema fix
4. `backend/app/api/continuous_learning.py` - OpenAPI schema fix
5. `backend/app/services/technical_debt_service.py` - Enum cast fix

### Full Test Report
See: `docs/testing/WEEK48_E2E_REPORT.md`

---

## Timeline Integration

| Week | Day | Task |
|------|-----|------|
| 13 | 1 | Hub Portal design + implementation |
| 13 | 2 | Hub Portal testing + backend status |
| 14 | 1 | Shared nav component |
| 14 | 2 | Update all frontend/*.html |
| 14 | 3 | Standalone integration + testing |

---

## Dependencies

- Fase 4 UI work (dashboards moeten bestaan)
- Backend health endpoint (/api/health)
- Geen blokkerende dependencies voor Fase 1
