# 🚀 Project Recovery Guide - Markdown Task Manager

**Laatst bijgewerkt**: 2025-11-12
**Project**: Agentic Task Management System
**Status**: Fase 1 Compleet ✅ | Fase 2 Starting 🔄

---

## 📋 INHOUDSOPGAVE

1. [Project Overview](#project-overview)
2. [Current Status](#current-status)
3. [Quick Start](#quick-start)
4. [System Architecture](#system-architecture)
5. [File Structure](#file-structure)
6. [Known Issues](#known-issues)
7. [Important Links](#important-links)

---

## PROJECT OVERVIEW

### Wat zijn we aan het bouwen?

Een **AI-powered agentic task management systeem** dat automatisch:
- Repositories analyseert
- Work breakdown structuren genereert (Epic → Feature → Story → Task)
- Effort schat met Function Points en Story Points
- Multi-agent orchestratie uitvoert (8 gespecialiseerde agents)
- Real-time voortgang toont via WebSocket dashboard

### Waarom?

**Probleem:**
- Handmatige repository analyse en planning kost 160 dagen voor 32 repos
- Kosten: €72,000 (32 repos × €2,250/repo)
- Onnauwkeurige estimates (±25%)

**Oplossing:**
- Geautomatiseerde analyse en planning met AI agents
- Tijd: 80 dagen (agent execution + oversight)
- Kosten: €41,400 development + €9,900 execution
- **Besparing: €30,600 (42.5% reductie)**
- Nauwkeurige estimates (±10%)

### Project Goals

1. **Functioneel:**
   - 8 work types supported (NEW_FEATURE, MAINTENANCE, BUG, etc.)
   - Automated work breakdown (Epic → Feature → Story → Task)
   - Intelligent estimation (FP + SP + ML)
   - Real-time dashboard met agent monitoring

2. **Technisch:**
   - FastAPI backend (45+ endpoints)
   - PostgreSQL database (hierarchical schema)
   - KaibanJS agent orchestration
   - Hybrid LLM execution (70% local Ollama, 30% cloud Claude/GPT-4)
   - WebSocket real-time updates

3. **Business:**
   - Migrate 32 repositories
   - €30,600 cost savings
   - ±10% estimation accuracy
   - Break-even after first batch

---

## CURRENT STATUS

### ✅ Wat is COMPLEET (Fase 1 - Week 1-4)

#### Backend (backend/app/)
- **FastAPI Backend**: 45 API endpoints
- **PostgreSQL Database**: Hierarchical schema
- **Models**: Item, Sprint, Project
- **API Endpoints**:
  - `/api/sprints/` - Sprint CRUD
  - `/api/sprints/{id}/items` - Sprint items
  - `/api/sprints/{id}/assign` - Assign item to sprint
  - `/api/sprints/backlog/items` - Backlog items
  - `/api/project/` - Project visualization
  - `/api/health` - Health check
- **Authentication**: JWT tokens
- **Migrations**: Alembic setup
- **Documentation**: Swagger UI at `/api/docs`

#### Frontend (frontend/)
- **Project Viewer** (index.html): 90% compleet
  - Drill-down navigatie: Epics → Features → Stories → Tasks
  - Sidebar met hierarchische navigatie
  - "← Terug" knop om niveau omhoog te gaan
  - Details panel rechts met metadata

- **Sprint Planning** (sprint-planning.html): 100% compleet
  - Backlog sidebar (links)
  - 4 Sprint kolommen (rechts)
  - Drag & Drop functionaliteit
  - Capacity tracking met progress bar
  - Auto-fill met gebalanceerde verdeling:
    - 10% CRITICAL
    - 30% HIGH
    - 40% MEDIUM
    - 20% LOW
  - Create Sprints knop (maakt 4× 2-week sprints)

### 🔄 Wat is IN PROGRESS (Fase 2 - Week 5-8)

**Start Week 5 (18 Nov 2025):**
- KaibanJS agent orchestration
- SuperClaude Framework integration
- Spec-Kit workflow
- Code-Maintenance-Agent

**Zie [fasenplan.md](./fasenplan.md) voor volledige planning**

### 📋 Wat komt daarna?

**Fase 3-9** (Week 9-40):
- Intelligence Layer (FP/SP estimation + ML)
- Real-Time Dashboard (WebSocket + monitoring)
- Quality & Testing (CI/CD + automation)
- Advanced Features (BMAD, Owl, Eigent-AI)
- Migration Pilot (3 repos)
- Full Batch Migration (29 repos)
- Optimization & Learning

**Zie [fasenplan.md](./fasenplan.md) voor complete week-per-week planning**

---

## QUICK START

### 🏁 Start het systeem (5 minuten)

#### 1. Start PostgreSQL
```bash
# Check of postgres draait
pg_isready

# Als niet draait:
sudo systemctl start postgresql
```

#### 2. Start Backend
```bash
cd /home/eddie/Projects/MarkdownTaskManager/backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Verify Backend
Open browser:
- **Health Check**: http://localhost:8000/api/health
- **API Docs**: http://localhost:8000/api/docs

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

#### 4. Open Frontend
- **Project Viewer**: http://localhost:8000/
- **Sprint Planning**: http://localhost:8000/sprint-planning.html

### 🧪 Test the System

#### Test Project Viewer
1. Open http://localhost:8000/
2. Click on Epic in sidebar
3. See Features/Stories in detail panel
4. Test drill-down navigation

#### Test Sprint Planning
1. Open http://localhost:8000/sprint-planning.html
2. Click "🚀 Create Sprints 1-4" (if no sprints exist)
3. Click "⚡ Auto-Fill Sprints"
4. Drag item from Backlog to Sprint column
5. Watch capacity bar update

### 🐛 If Something Goes Wrong

**Backend won't start:**
```bash
# Check virtual environment
source backend/.venv/bin/activate
which python  # Should show .venv path

# Reinstall dependencies
pip install -r requirements.txt
```

**Database errors:**
```bash
# Check PostgreSQL
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -l | grep project_manager

# Recreate if needed
sudo -u postgres psql
CREATE DATABASE project_manager;
\q

# Run migrations
cd backend
alembic upgrade head
```

**Frontend shows no data:**
```bash
# Check backend is running
curl http://localhost:8000/api/health

# Check API returns data
curl http://localhost:8000/api/sprints/

# Check browser console for errors (F12)
```

---

## SYSTEM ARCHITECTURE

### High-Level Overview

```
┌─────────────────────────────────────────────────────┐
│  Frontend (HTML/CSS/JavaScript)                     │
│  ├─ index.html (Project Viewer)                     │
│  └─ sprint-planning.html (Sprint Planning)          │
└─────────────────────────────────────────────────────┘
                        ↓ HTTP/REST
┌─────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                  │
│  ├─ API Layer (45 endpoints)                        │
│  ├─ Business Logic (CRUD operations)                │
│  └─ Data Layer (SQLAlchemy ORM)                     │
└─────────────────────────────────────────────────────┘
                        ↓ SQL
┌─────────────────────────────────────────────────────┐
│  Database (PostgreSQL)                              │
│  ├─ items (hierarchical structure)                  │
│  ├─ sprints (capacity tracking)                     │
│  └─ projects (project metadata)                     │
└─────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- Python 3.11+
- FastAPI 0.104+
- SQLAlchemy 2.0 (async)
- PostgreSQL 15+
- Alembic (migrations)
- Pydantic (validation)
- JWT authentication

**Frontend:**
- Vanilla JavaScript (ES6+)
- HTML5 + CSS3
- Drag & Drop API
- Fetch API for backend calls

**Infrastructure:**
- uvicorn (ASGI server)
- Docker (optional, for PostgreSQL)
- Virtual environment (uv)

**Future (Fase 2-9):**
- KaibanJS (agent orchestration)
- Ollama (local LLM)
- Claude API (cloud LLM)
- Redis (WebSocket pub/sub)
- Celery (task queue)

### Data Model (Fase 1)

```sql
-- Items (hierarchical structure)
items
├─ id: VARCHAR (e.g., "EPIC-001", "STORY-042")
├─ title: VARCHAR
├─ type: ENUM (epic, feature, story, task)
├─ status: ENUM (todo, in_progress, done)
├─ parent_id: VARCHAR (FK → items.id)
├─ sprint_id: INTEGER (FK → sprints.id)
├─ sprint_order: INTEGER
├─ story_points: INTEGER
├─ priority: ENUM (low, medium, high, critical)
├─ created_at: TIMESTAMP
└─ updated_at: TIMESTAMP

-- Sprints
sprints
├─ id: SERIAL
├─ name: VARCHAR (e.g., "Sprint 1")
├─ start_date: DATE
├─ end_date: DATE
├─ capacity: INTEGER (default 50 SP)
├─ total_sp: INTEGER (computed)
├─ status: ENUM (planning, active, completed)
├─ created_at: TIMESTAMP
└─ updated_at: TIMESTAMP
```

---

## FILE STRUCTURE

### Project Directory Layout

```
/home/eddie/Projects/MarkdownTaskManager/
│
├── 📄 README.md                    # Project main documentation
├── 📄 HERSTART_PROJECT.md          # This file - Recovery guide
├── 📄 fasenplan.md                 # Complete week-by-week planning
├── 📄 plan.md                      # Master architecture document
├── 📄 plan_roadmap.md              # HCI EPD project roadmap
│
├── 📁 backend/                     # Backend API
│   ├── app/
│   │   ├── main.py                # FastAPI application entry
│   │   ├── models/
│   │   │   ├── item.py           # Item model
│   │   │   └── sprint.py         # Sprint model
│   │   ├── api/
│   │   │   ├── sprints.py        # Sprint endpoints
│   │   │   └── project.py        # Project endpoints
│   │   ├── crud/
│   │   │   └── item.py           # CRUD operations
│   │   ├── schemas/
│   │   │   └── sprint.py         # Pydantic schemas
│   │   └── database.py           # Database connection
│   ├── alembic/                   # Database migrations
│   ├── .venv/                     # Virtual environment
│   ├── requirements.txt           # Python dependencies
│   └── alembic.ini               # Alembic config
│
├── 📁 frontend/                    # Frontend interfaces
│   ├── index.html                 # Project viewer (90% done)
│   └── sprint-planning.html       # Sprint planning (100% done)
│
├── 📁 Projecten/                   # Markdown data storage
│   └── MarkdownTaskManager/
│       ├── EPIC-001/
│       │   ├── epic.md
│       │   └── FEATURE-001/
│       │       ├── feature.md
│       │       └── STORY-001/
│       │           ├── story.md
│       │           ├── TASK-001.md
│       │           └── TASK-002.md
│       ├── EPIC-002/
│       └── EPIC-003/
│
├── 📁 _backup/                     # Backups (not in git)
├── 📁 example-project/             # Example data
└── 📁 test-project/                # Test data
```

### Important Files

| File | Purpose | Status |
|------|---------|--------|
| `backend/app/main.py` | FastAPI application entry point | ✅ Done |
| `backend/app/models/item.py` | Item model with sprint_id | ✅ Done |
| `backend/app/models/sprint.py` | Sprint model with capacity | ✅ Done |
| `backend/app/api/sprints.py` | Sprint API endpoints | ✅ Done |
| `frontend/index.html` | Project viewer interface | ⚠️ 90% (bug) |
| `frontend/sprint-planning.html` | Sprint planning interface | ✅ Done |
| `fasenplan.md` | Complete project planning | ✅ Done |
| `plan.md` | Master architecture document | ✅ Done |

---

## KNOWN ISSUES

### 🐛 Bug #1: Double-click on Cards (frontend/index.html)

**Status**: 🔴 OPEN
**Priority**: MEDIUM
**Impact**: Drill-down navigation doesn't work consistently

**Probleem:**
- Klikken op epic in sidebar werkt ✅
- Double-click op feature/story cards rechts navigeert niet ❌

**Locatie:**
- File: `frontend/index.html`
- Lines: 807-872
- Function: `renderDetail()` → event handlers voor cards

**Oorzaak:**
```javascript
// Huidige code heeft click + dblclick handlers
// maar drill-down werkt niet consistent
// Waarschijnlijk timing/event conflict
```

**Oplossing opties:**
1. Gebruik alleen single click (niet dblclick)
2. Fix event propagation
3. Gebruik setTimeout tussen click en dblclick

**Workaround:**
Gebruik sidebar navigatie in plaats van double-click op cards

---

## IMPORTANT LINKS

### URLs (when backend is running)

**API:**
- Health Check: http://localhost:8000/api/health
- API Documentation: http://localhost:8000/api/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

**Frontend:**
- Project Viewer: http://localhost:8000/
- Sprint Planning: http://localhost:8000/sprint-planning.html

**Database:**
- Host: localhost
- Port: 5432
- Database: project_manager
- User: user
- Password: password

### Documentation

**Project Docs:**
- **Recovery Guide**: [HERSTART_PROJECT.md](./HERSTART_PROJECT.md) (dit bestand)
- **Fase Planning**: [fasenplan.md](./fasenplan.md) ← **GEBRUIK DIT VOOR PLANNING**
- **Architecture**: [plan.md](./plan.md)
- **HCI EPD Roadmap**: [plan_roadmap.md](./plan_roadmap.md)

**External Docs:**
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- PostgreSQL: https://www.postgresql.org/docs/
- KaibanJS: https://github.com/kaiban-ai/KaibanJS

### Commands Quick Reference

```bash
# Backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database
pg_isready                           # Check if PostgreSQL is running
sudo systemctl start postgresql      # Start PostgreSQL
sudo -u postgres psql -d project_manager  # Connect to database

# Migrations
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Testing
curl http://localhost:8000/api/health
curl http://localhost:8000/api/sprints/
curl http://localhost:8000/api/sprints/1/items
curl -X POST "http://localhost:8000/api/sprints/1/assign?item_id=STORY-001"
```

---

## NEXT STEPS

### Wat te doen nu?

1. **Start systeem**: Volg [Quick Start](#quick-start) hierboven
2. **Check huidige status**: Verifieer dat Fase 1 werkt
3. **Plan volgende week**: Open [fasenplan.md](./fasenplan.md)
4. **Start Fase 2**: Volg Week 5 planning in fasenplan.md

### Week 5 Quick Start (18 Nov 2025)

**Maandag ochtend:**
1. ☕ Team standup + week kickoff
2. 📦 Install KaibanJS: `npm install @kaibanjs/core`
3. 📁 Create `backend/agents/` structure
4. 📖 Read KaibanJS docs (2 hours)
5. ⚙️ Create agent config template

**Voor volledige planning:** Zie [fasenplan.md](./fasenplan.md) Week 5

---

## DEBUG TIPS

### Backend Debug

```bash
# Check backend logs
tail -f backend/app/logs/*.log  # if logging enabled

# Check database connections
sudo -u postgres psql -d project_manager
SELECT count(*) FROM items;
SELECT count(*) FROM sprints;
\q

# Test API directly
curl -v http://localhost:8000/api/health
curl http://localhost:8000/api/sprints/ | jq .
```

### Frontend Debug

1. Open browser DevTools (F12)
2. Check Console tab for JavaScript errors
3. Check Network tab for failed API calls
4. Check Application > Local Storage for data

### Database Debug

```sql
-- Connect to database
sudo -u postgres psql -d project_manager

-- Check tables
\dt

-- Check sprints
SELECT id, name, capacity, total_sp FROM sprints;

-- Check items with sprint
SELECT id, title, sprint_id FROM items WHERE sprint_id IS NOT NULL;

-- Check backlog items
SELECT id, title, priority FROM items WHERE sprint_id IS NULL;

-- Exit
\q
```

---

## SUCCESS CRITERIA

### Fase 1 (Current) - Criteria ✅

- ✅ Backend start zonder errors
- ✅ PostgreSQL draait
- ✅ Health check returns 200 OK
- ✅ API docs accessible
- ✅ Project view laadt data
- ✅ Sprint planning interface werkt
- ✅ Sprints kunnen worden aangemaakt
- ✅ Auto-fill verdeelt items gebalanceerd
- ✅ Drag & drop werkt
- ⚠️ Double-click bug geïdentificeerd (minor)

### Fase 2-9 Success Criteria

**Zie [fasenplan.md](./fasenplan.md) → Success Metrics**

Key targets:
- Estimation accuracy: ±10%
- Migration efficiency: 4 repos/week
- Cost savings: €30,600
- Test coverage: ≥80%
- Agent efficiency: 70% automated

---

## SUPPORT & ESCALATION

### Als je vastloopt

1. **Browser issues**: Check browser console (F12) voor JavaScript errors
2. **API issues**: Check backend logs en `/api/health`
3. **Database issues**: Check PostgreSQL status met `pg_isready`
4. **Frontend not loading**: Herstart backend met uvicorn
5. **Dependencies issues**: Reinstall met `pip install -r requirements.txt`

### Escalation Path

1. Check deze recovery guide
2. Check [fasenplan.md](./fasenplan.md) voor planning vragen
3. Check [plan.md](./plan.md) voor architecture vragen
4. Contact: Eddie (project owner)

---

## DOCUMENT CONTROL

**Version:** 2.0 (Refactored)
**Created:** 2025-11-12
**Last Updated:** 2025-11-12
**Author:** Eddie
**Purpose:** Quick project recovery and startup guide

**Related Documents:**
- [fasenplan.md](./fasenplan.md) - Complete project planning ← **USE THIS**
- [plan.md](./plan.md) - Master architecture
- [plan_roadmap.md](./plan_roadmap.md) - HCI EPD roadmap

**Next Review:** After Fase 2 completion (Week 8)

---

**🎯 Start met [fasenplan.md](./fasenplan.md) voor de volledige week-per-week planning!**

**🚀 Veel succes met Fase 2!**
