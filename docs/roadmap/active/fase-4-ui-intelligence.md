# FASE 4: UI + INTELLIGENCE LAYER (Week 13-16)

**Status:** ACTIEF
**Periode:** 9 december 2025 - 5 januari 2026
**Effort:** 80 uren (40h UI + 40h estimation)
**Strategie:** 50/50 split - elke week 2-3 dagen UI + 2-3 dagen backend

---

## Doel

UI voor bestaande features + Intelligence Layer integratie.

**Key Principle:** Altijd kunnen testen wat we opleveren!

---

## Week 13: Agent Dashboard + Function Points

### Dag 1-2: UI PRIORITEIT
**Focus:** Agent Dashboard (Vanilla JS + HTML)

**Tasks:**
- [ ] Create `frontend/agent-dashboard.html` (8h)
  - 10 agent status cards
  - Workflow execution form
  - Results display
  - Statistics dashboard
  - Live status polling (3 sec)
- [ ] Integrate with existing APIs (2h)
- [ ] Test all 9 work types via UI (2h)

**APIs:**
- `GET /api/workflows/agents`
- `POST /api/workflows/analyze`
- `GET /api/workflows/statistics`

**Deliverable:** `agent-dashboard.html` (~600 lines)

### Dag 3-5: BACKEND FEATURE
**Focus:** Function Point Calculator (IFPUG)

**Tasks:**
- [ ] Study IFPUG methodology (4h)
- [ ] Create `backend/estimation/function_points.py` (8h)
- [ ] Create API endpoint `POST /api/estimation/function-points` (2h)
- [ ] Test with historical data (2h)

**Deliverable:** Function Point Calculator (~400 lines)

---

## Week 14: Spec-Kit Wizard + Story Points

### Dag 1-3: UI PRIORITEIT
**Focus:** Spec-Kit Workflow Wizard

**Tasks:**
- [ ] Create `frontend/spec-kit-wizard.html` (12h)
  - Stage 1: Constitution Form
  - Stage 2: Specification Form
  - Stage 3: Tasks Form
  - Complete Workflow Option
- [ ] Styling & UX (4h)

**Deliverable:** `spec-kit-wizard.html` (~800 lines)

### Dag 4-5: BACKEND FEATURE
**Focus:** Story Point Estimator

**Tasks:**
- [ ] Design Fibonacci mapping algorithm (4h)
- [ ] Create `backend/estimation/story_points.py` (8h)
- [ ] Create API endpoint (2h)
- [ ] Test with sample stories (2h)

**Deliverable:** Story Point Estimator (~300 lines)

---

## Week 15: Maintenance Scheduler + Estimation UI

### Dag 1-2: UI PRIORITEIT
**Focus:** Maintenance Scheduler Interface

**Tasks:**
- [ ] Create `frontend/maintenance-scheduler.html` (10h)
  - Tab 1: Daily Scans
  - Tab 2: Weekly Scans
  - Tab 3: Interval Scans
  - Active Jobs List

### Dag 3-5: BACKEND FEATURE
**Focus:** Estimation Dashboard UI

**Tasks:**
- [ ] Create `frontend/estimation-dashboard.html` (12h)
  - Function Points calculator form
  - Story Points calculator form
  - Combined estimation view
  - Historical comparison

---

## Week 16: Project Wizard + ML Training

### Dag 1-3: UI PRIORITEIT
**Focus:** Project Wizard

**Tasks:**
- [ ] Create `frontend/project-wizard.html` (12h)
  - Step 1: Project basics
  - Step 2: Tech stack selection
  - Step 3: Team configuration
  - Step 4: Generate structure

### Dag 4-5: BACKEND FEATURE
**Focus:** ML Training Pipeline UI

**Tasks:**
- [ ] Training data viewer
- [ ] Model metrics dashboard
- [ ] Prediction accuracy tracking

---

## Week 16 Checkpoint: Demo Readiness

### What You Can Demo After Week 16

| Feature | UI | Backend | Status |
|---------|-----|---------|--------|
| Agent Dashboard | agent-dashboard.html | /api/workflows | Ready |
| Spec-Kit Wizard | spec-kit-wizard.html | /api/spec-kit | Ready |
| Maintenance Scheduler | maintenance-scheduler.html | /api/scheduler | Ready |
| Estimation Dashboard | estimation-dashboard.html | /api/estimation | Ready |
| Project Wizard | project-wizard.html | /api/project | Ready |

---

## Success Criteria

- [ ] All 5 dashboards functional
- [ ] Function Points calculator working
- [ ] Story Points estimator working
- [ ] ML model trained and validated
- [ ] Can demo end-to-end workflow via browser
