# Fase 29: mq Workflow Integration Roadmap

**Versie**: 1.2
**Status**: APPROVED
**Eigenaar**: Peter (Product Owner)
**Periode**: Week 146-154 (9 weken)
**Effort**: ~380 uur (1.05 FTE equivalent) *(+8 uur bidirectionele triggers, +12 uur intake queue system)*

---

## Executive Summary

Deze fase integreert de **mq CLI workflows** (marqed-bugfix, marqed-changes, marqed-migration, marqed-analyze) met het **MarQed.ai Platform**, waardoor developers een unified experience krijgen met:

- Real-time Progress Dashboard
- Tech Stack Knowledge Lookup (leren van eerdere projecten)
- Self-Validation met visual regression en performance baselines
- CLI-to-API Bridge voor platform services
- **Bidirectionele Entry Points** (CLI → Platform én Platform → CLI)
- **Intake Queue System** met status tracking (todo → in-progress → done)

---

## Milestones Overzicht

| Milestone | Week | Deliverable | Success Metric |
|-----------|------|-------------|----------------|
| **M1** | 148 | CLI Bridge werkend | 100% API calls succesvol |
| **M2** | 150 | Progress Dashboard live | Real-time updates <2s latency |
| **M3** | 152 | Tech Stack KB operationeel | >60% hit rate op knowledge lookup |
| **M4** | 153 | Self-Validation geintegreerd | >90% regression detection |
| **M5** | 154 | Full integration complete | E2E tests 100% pass |

---

## Week-by-Week Breakdown

### Week 146: Foundation - API Design

**Focus**: Ontwerp van workflow API endpoints, data models én **intake document structuur**

| Dag | Activiteit | Deliverable |
|-----|------------|-------------|
| Ma | API endpoint design workshop met Architect Agent | OpenAPI spec draft |
| Di | Task persistence model design (SQLAlchemy) | Database models: `workflow`, `workflow_task`, `workflow_log` |
| Wo | Workflow state machine design | State diagram (pending -> in_progress -> completed/failed) |
| Do | CLI bridge architecture design + **Intake folder structuur** | Shell script specs + Intake design |
| Vr | Review & refinement met Felix | Goedgekeurd design document |

**Deliverables Week 146**:
- [ ] OpenAPI specificatie `/api/v2/workflow/*` (12 endpoints)
- [ ] SQLAlchemy models voor workflow persistence
- [ ] State machine diagram (Mermaid)
- [ ] CLI bridge specs (`platform-api.sh`)
- [ ] **Intake Document Structuur Design** ⭐ NIEUW:
  - [ ] Folder structuur: `.marqed/intake/{bugs,changes,migrations,analyses}/{todo,in-progress,done}/`
  - [ ] Naamgeving conventie: `{TYPE}-YYYY-MM-DD-NNN.md`
  - [ ] Status flow: `todo/ → in-progress/ → done/`

**Dependencies**: Geen (startweek)

---

### Week 147: Foundation - Implementation

**Focus**: Implementatie van core API, CLI bridge, Platform-to-CLI trigger én **Intake Queue System**

| Dag | Activiteit | Deliverable |
|-----|------------|-------------|
| Ma | Workflow API endpoints implementeren | `backend/app/api/workflow_integration.py` |
| Di | Task persistence + **Intake folder init** | Alembic migration + `.marqed/intake/` structuur |
| Wo | `platform-api.sh` bouwen + **`mq list` command** | CLI-to-API bridge + queue overzicht |
| Do | **Bidirectionele trigger**: `workflow-trigger.sh` + trigger endpoint | Platform → CLI triggering |
| Vr | Health checks + `--from-platform` + **auto-move intake** + Integration testing | 35+ unit tests passing |

**Deliverables Week 147**:
- [ ] `/api/v2/workflow/` - Create workflow
- [ ] `/api/v2/workflow/{id}` - Get workflow
- [ ] `/api/v2/workflow/{id}/tasks` - Task CRUD
- [ ] `/api/v2/workflow/active` - Dashboard feed
- [ ] **`/api/v2/workflow/trigger`** - Platform-to-CLI trigger endpoint ⭐
- [ ] `platform-api.sh` - CLI-to-API bridge
- [ ] **`workflow-trigger.sh`** - Platform triggers mq workflows ⭐
- [ ] `--from-platform` flag in alle 4 mq workflow scripts ⭐
- [ ] Health checks in alle 4 workflow scripts
- [ ] **Intake Queue System** ⭐ NIEUW:
  - [ ] `init_intake_folders()` - Maakt `.marqed/intake/{type}/{status}/` structuur
  - [ ] `mq list [bugs|changes|migrations|analyses|all]` - CLI queue overzicht
  - [ ] `mq bugfix --next` / `mq changes --next` - Pakt oudste uit todo/
  - [ ] Auto-move: `todo/ → in-progress/` bij workflow start
  - [ ] Auto-move: `in-progress/ → done/` bij workflow complete

**Dependencies**: Week 146 design complete

---

### Week 148: Progress Dashboard - Backend (M1 Checkpoint)

**Focus**: Real-time status updates en log streaming

| Dag | Activiteit | Deliverable |
|-----|------------|-------------|
| Ma | Dashboard data model finaliseren | Extended schema |
| Di | WebSocket/SSE setup voor real-time updates | `/api/v2/workflow/stream` |
| Wo | Workflow status aggregation service | `WorkflowDashboardService` |
| Do | Log streaming endpoint | `/api/v2/workflow/{id}/logs/stream` |
| Vr | Testing & M1 validation | CLI Bridge 100% werkend |

**Deliverables Week 148**:
- [ ] Real-time status updates via Server-Sent Events
- [ ] `/api/v2/dashboard/workflows` - Active workflows feed
- [ ] Log streaming endpoint met filtering
- [ ] **M1 MILESTONE**: CLI Bridge 100% API calls succesvol

**Success Metrics M1**:
| Metric | Target | Actual |
|--------|--------|--------|
| API call success rate | 100% | - |
| Response time p95 | <500ms | - |
| Error handling coverage | 100% | - |

**Dependencies**: Week 147 API complete

---

### Week 149: Progress Dashboard - Frontend

**Focus**: Dashboard UI implementatie in Portal

| Dag | Activiteit | Deliverable |
|-----|------------|-------------|
| Ma | Dashboard layout & wireframe design | Figma mockup |
| Di | Workflow cards component | React component `<WorkflowCard>` |
| Wo | Task list component met progress bars | React component `<TaskList>` |
| Do | Log viewer integration | React component `<LogViewer>` |
| Vr | Polish, animations & testing | Dashboard MVP live |

**Deliverables Week 149**:
- [ ] `/dashboard/workflows` route in Portal
- [ ] `<WorkflowCard>` - Shows workflow status, progress %, phase
- [ ] `<TaskList>` - Expandable task list per workflow
- [ ] `<LogViewer>` - Real-time log streaming
- [ ] SSE connection handling met reconnect logic

**Dependencies**: Week 148 backend complete

---

### Week 150: Progress Dashboard - Polish (M2 Checkpoint)

**Focus**: Dashboard verfijning, **workflow trigger buttons**, **Intake Queue Panel** en M2 validatie

| Dag | Activiteit | Deliverable |
|-----|------------|-------------|
| Ma | Security scan results linkage + **"Fix Now" buttons** | Scan findings → mq bugfix trigger |
| Di | Performance optimization + **Intake Queue Panel** | Virtualized lists + queue overzicht |
| Wo | Mobile responsive design | Responsive breakpoints |
| Do | **"Start Workflow" buttons** in alle relevante dashboards | Platform → CLI entry points |
| Vr | M2 validation & user testing | Dashboard live en gevalideerd |

**Deliverables Week 150**:
- [ ] Security scan results gelinkt aan workflows
- [ ] **"Fix Now" button** in Security Dashboard → triggers `mq bugfix` ⭐
- [ ] **"Start Feature" button** in Feature Request view → triggers `mq changes` ⭐
- [ ] **"Start Migration" button** in Brown Paper Dashboard → triggers `mq migration` ⭐
- [ ] **"Run Analysis" button** in Quality Dashboard → triggers `mq analyze` ⭐
- [ ] **Intake Queue Dashboard Panel** ⭐ NIEUW:
  - [ ] Overzicht per type (bugs/changes/migrations/analyses)
  - [ ] Status badges (todo/in-progress/done counts)
  - [ ] "New Intake" buttons → opent template in editor
  - [ ] File upload → plaatst in juiste `todo/` folder
  - [ ] Platform ↔ `.marqed/intake/` folder sync
- [ ] Performance: smooth scrolling met 100+ workflows
- [ ] Mobile responsive (tablet + phone views)
- [ ] **M2 MILESTONE**: Progress Dashboard live met bidirectionele triggers + Intake Queue

**Success Metrics M2**:
| Metric | Target | Actual |
|--------|--------|--------|
| Real-time update latency | <2s | - |
| Dashboard load time | <1s | - |
| Concurrent workflows displayed | 50+ | - |
| User satisfaction (internal) | >4/5 | - |
| **Platform → CLI trigger success rate** | 100% | - | ⭐
| **Workflow buttons functional** | 4/4 dashboards | - | ⭐
| **Intake queue sync accuracy** | 100% | - | ⭐ NIEUW

**Dependencies**: Week 149 frontend MVP

---

### Week 151: Tech Stack Knowledge - Core

**Focus**: TechStackKnowledgeService bouwen

| Dag | Activiteit | Deliverable |
|-----|------------|-------------|
| Ma | Service skeleton + interfaces | `techstack_knowledge_service.py` |
| Di | Experience Store integration | Search in `experience_store_service` |
| Wo | ChromaDB similarity search | Vector search in `project_knowledge` collection |
| Do | Pattern extraction logic | Extract patterns from past projects |
| Vr | Pitfalls extraction | Extract wat NIET werkte |

**Deliverables Week 151**:
- [ ] `TechStackKnowledgeService` class
- [ ] `find_similar_projects()` method
- [ ] ChromaDB collection: `project_knowledge`
- [ ] Pitfalls database seeded met 50+ entries
- [ ] `/api/v2/knowledge/lookup` endpoint

**Dependencies**: ChromaDB operational (existing)

---

### Week 152: Tech Stack Knowledge - Integration (M3 Checkpoint)

**Focus**: CLI integration en dashboard panel

| Dag | Activiteit | Deliverable |
|-----|------------|-------------|
| Ma | Effort estimation from history | `calculate_effort_estimate()` |
| Di | CLI integration (`knowledge-lookup.sh`) | Shell function voor mq workflows |
| Wo | Dashboard knowledge panel | `<KnowledgePanel>` component |
| Do | Testing met echte project data | Validated results |
| Vr | M3 validation | Knowledge lookup >60% hit rate |

**Deliverables Week 152**:
- [ ] `knowledge-lookup.sh` in mq workflows
- [ ] Effort estimates met confidence levels
- [ ] Knowledge panel in Progress Dashboard
- [ ] Seeded knowledge base (10+ projecten)
- [ ] **M3 MILESTONE**: Tech Stack KB operationeel

**Success Metrics M3**:
| Metric | Target | Actual |
|--------|--------|--------|
| Knowledge hit rate | >60% | - |
| Similar project recall | >3 per lookup | - |
| Pitfall detection | >5 relevant | - |
| Effort estimate accuracy | +/- 30% | - |

**Dependencies**: Week 151 core service

---

### Week 153: Self-Validation Enhancement (M4 Checkpoint)

**Focus**: Visual regression en performance baseline integratie

| Dag | Activiteit | Deliverable |
|-----|------------|-------------|
| Ma | Visual regression service koppeling | API adapter voor existing service |
| Di | Performance baseline integratie | Baseline comparison logic |
| Wo | Validation results naar dashboard | `<ValidationResults>` component |
| Do | CLI validation commands | `run_visual_regression()`, `run_performance_baseline()` |
| Vr | M4 validation | >90% regression detection |

**Deliverables Week 153**:
- [ ] `/api/v2/validation/visual-regression` endpoint
- [ ] `/api/v2/validation/performance` endpoint
- [ ] Validation results in dashboard
- [ ] CLI functions in `platform-api.sh`
- [ ] **M4 MILESTONE**: Self-Validation geintegreerd

**Success Metrics M4**:
| Metric | Target | Actual |
|--------|--------|--------|
| Visual regression detection | >90% | - |
| Performance regression detection | >85% | - |
| False positive rate | <10% | - |
| Validation time | <30s | - |

**Dependencies**: Week 152 complete, existing validation services

---

### Week 154: Polish & Full Integration (M5 Final)

**Focus**: End-to-end testing en documentatie

| Dag | Activiteit | Deliverable |
|-----|------------|-------------|
| Ma | E2E test: marqed-bugfix workflow | Test report |
| Di | E2E test: marqed-changes workflow | Test report |
| Wo | E2E test: marqed-migration workflow | Test report |
| Do | Documentation & user guides | Complete docs |
| Vr | M5 validation & release | Full integration complete |

**Deliverables Week 154**:
- [ ] E2E tests voor alle 4 workflows
- [ ] User documentation in `docs/mq-workflows/`
- [ ] WBSO rapportage validatie
- [ ] Release notes
- [ ] **M5 MILESTONE**: Full integration complete

**Success Metrics M5**:
| Metric | Target | Actual |
|--------|--------|--------|
| E2E test pass rate | 100% | - |
| Documentation coverage | 100% | - |
| Known bugs | 0 P1, <5 P2 | - |
| User acceptance | Sign-off | - |

**Dependencies**: Weeks 146-153 complete

---

## Resource Allocation

### Team Samenstelling

| Rol | Effort | Weken | Focus Area |
|-----|--------|-------|------------|
| Backend Developer | 0.5 FTE | 9 | API, Services, Database |
| Frontend Developer | 0.25 FTE | 4 | Dashboard UI (Week 149-152) |
| DevOps | 0.15 FTE | 3 | CLI Bridge, Deployment |
| QA | 0.1 FTE | 4 | Integration & E2E Tests |
| **Totaal** | **1.0 FTE** | **9 weken** | |

### Agent Allocatie per Week

| Week | Primaire Agent | Secundaire Agents | Focus |
|------|----------------|-------------------|-------|
| 146 | Felix (Architect) | Peter (Product) | API Design |
| 147 | Backend Dev | Tessa (Test) | Implementation |
| 148 | Backend Dev | Felix | Real-time Backend |
| 149 | Vicky (Design) | Frontend Dev | Dashboard UI |
| 150 | Frontend Dev | Quinn (Quality) | Dashboard Polish |
| 151 | Backend Dev | Diana (Docs) | Knowledge Service |
| 152 | Backend Dev | Miguel (Migration) | Knowledge Integration |
| 153 | Backend Dev | Tessa (Test) | Validation |
| 154 | QA Lead | Diana (Docs) | E2E & Docs |

### Effort per Week (uren)

| Week | Backend | Frontend | DevOps | QA | Total |
|------|---------|----------|--------|-----|-------|
| 146 | 24 | 0 | 8 | 0 | 32 |
| 147 | 32 | 0 | 8 | 0 | 40 |
| 148 | 32 | 0 | 4 | 4 | 40 |
| 149 | 8 | 32 | 0 | 0 | 40 |
| 150 | 8 | 24 | 0 | 8 | 40 |
| 151 | 32 | 0 | 0 | 8 | 40 |
| 152 | 24 | 8 | 4 | 4 | 40 |
| 153 | 24 | 8 | 0 | 8 | 40 |
| 154 | 8 | 0 | 0 | 32 | 40 |
| **Total** | **192** | **72** | **24** | **64** | **352** |

---

## Dependency Graph

```
Week 146: API Design
    │
    v
Week 147: Implementation ────────────────────────────┐
    │                                                 │
    v                                                 │
Week 148: Dashboard Backend (M1)                     │
    │                                                 │
    ├─────────────────┐                              │
    v                 v                              │
Week 149: Frontend   Week 151: Knowledge Core        │
    │                     │                          │
    v                     v                          │
Week 150: Polish (M2)    Week 152: Knowledge (M3)   │
    │                     │                          │
    └──────────┬──────────┘                          │
               │                                      │
               v                                      │
        Week 153: Self-Validation (M4) <─────────────┘
               │
               v
        Week 154: Full Integration (M5)
               │
               v
        ════════════════════════
        VALIDATIE CHECKPOINT
        ════════════════════════
               │
               v
        Fase 2: Parallel Coordinator
        (NIET INGEPLAND - NA VALIDATIE)
```

---

## Success Metrics Summary

### Overall Phase Success Criteria

| Category | Metric | Target | Validation Method |
|----------|--------|--------|-------------------|
| **Reliability** | Workflow success rate | >90% | Automated metrics |
| **Performance** | Dashboard latency | <2s | Performance monitoring |
| **Usability** | Developer satisfaction | >4/5 | Survey (Week 155) |
| **Coverage** | Security scan coverage | >95% | CWE Scanner report |
| **Efficiency** | Knowledge reuse rate | >60% | Lookup hit rate |
| **Quality** | P1 bugs at release | 0 | Bug tracking |

### Milestone Success Criteria

#### M1: CLI Bridge (Week 148)
- [ ] 100% API calls succesvol
- [ ] Response time p95 <500ms
- [ ] Error handling coverage 100%
- [ ] Health check blocks workflow als platform down

#### M2: Progress Dashboard (Week 150)
- [ ] Real-time updates <2s latency
- [ ] 50+ concurrent workflows supported
- [ ] Mobile responsive
- [ ] WCAG 2.1 AA compliant

#### M3: Tech Stack KB (Week 152)
- [ ] >60% hit rate op lookups
- [ ] Effort estimates binnen +/-30%
- [ ] 50+ pitfalls in database
- [ ] 10+ project histories seeded

#### M4: Self-Validation (Week 153)
- [ ] >90% visual regression detection
- [ ] >85% performance regression detection
- [ ] <10% false positive rate
- [ ] Validation time <30s

#### M5: Full Integration (Week 154)
- [ ] E2E tests 100% pass
- [ ] Documentation 100% complete
- [ ] 0 P1 bugs, <5 P2 bugs
- [ ] User acceptance sign-off

---

## Risk Register

| ID | Risico | Kans | Impact | Score | Mitigatie |
|----|--------|------|--------|-------|-----------|
| R1 | Platform downtime tijdens integratie | Low | High | 3 | Health check + clear error messages |
| R2 | ChromaDB performance issues | Medium | Medium | 4 | Index optimization, caching |
| R3 | Knowledge lookup niet relevant | Medium | Low | 3 | Tuning na launch, feedback loop |
| R4 | Dashboard WebSocket stability | Low | Medium | 2 | SSE fallback, reconnect logic |
| R5 | Fase duurt langer dan 9 weken | Medium | Medium | 4 | Week 154 als buffer, scope management |
| R6 | Frontend developer niet beschikbaar | Low | High | 3 | Backend dev kan basis UI maken |

---

## Post-Integration: Toekomstige Fases

Na succesvolle validatie van Fase 29 (alle milestones gehaald):

### Fase 30: Parallel Execution Coordinator (NIET INGEPLAND)
- Redis-based session coordinator
- File locking mechanism
- Cross-session status sync
- **Voorwaarde**: Fase 29 M5 100% gevalideerd

### Fase 31: GitOps Native Integration (NIET INGEPLAND)
- GitHub Actions workflow triggers
- GitLab CI integration
- Automated workflow dispatch
- **Voorwaarde**: Fase 29 + 30 gevalideerd

---

## Appendix A: API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/workflow/` | POST | Create workflow |
| `/api/v2/workflow/{id}` | GET | Get workflow |
| `/api/v2/workflow/{id}` | PATCH | Update workflow |
| `/api/v2/workflow/{id}/tasks` | GET | List tasks |
| `/api/v2/workflow/{id}/tasks` | POST | Create task |
| `/api/v2/workflow/{id}/tasks/{tid}` | PATCH | Update task |
| `/api/v2/workflow/{id}/logs` | GET | Get logs |
| `/api/v2/workflow/{id}/logs/stream` | GET | Stream logs (SSE) |
| `/api/v2/workflow/active` | GET | List active workflows |
| `/api/v2/workflow/stream` | GET | Stream all updates (SSE) |
| **`/api/v2/workflow/trigger`** | **POST** | **Platform → CLI trigger (bidirectioneel)** ⭐ |
| `/api/v2/knowledge/lookup` | POST | Tech stack lookup |
| `/api/v2/validation/visual-regression` | POST | Run visual check |
| `/api/v2/validation/performance` | POST | Run perf check |

---

## Appendix B: Database Tables

```sql
-- workflow (main table)
-- workflow_task (tasks per workflow)
-- workflow_log (logs per workflow)
-- project_knowledge (knowledge base)
```

Zie `docs/marqed-platform-and-mq-analysis.md` voor volledige schema definitie.

---

## Appendix C: CLI Bridge Functions

```bash
# mq/workflows/common/platform-api.sh (CLI → Platform)
check_platform_required()      # Verify platform is running
create_workflow()              # Create new workflow
get_workflow()                 # Get workflow status
update_task_status()           # Update task in workflow
lookup_existing_knowledge()    # Query tech stack KB
run_security_scan()            # Trigger CWE scan
run_visual_regression()        # Visual diff check
run_performance_baseline()     # Performance check
sync_tasks_to_platform()       # Sync Claude tasks to DB

# mq/workflows/common/workflow-trigger.sh (Platform → CLI) ⭐
trigger_mq_workflow()          # Main dispatcher (calls appropriate mq script)
trigger_bugfix()               # Trigger mq bugfix --from-platform
trigger_changes()              # Trigger mq changes --from-platform
trigger_migration()            # Trigger mq migration --from-platform
trigger_analyze()              # Trigger mq analyze --from-platform

# mq/workflows/common/intake-queue.sh (Intake Document Management) ⭐ NIEUW
init_intake_folders()          # Maakt .marqed/intake/{type}/{status}/ structuur
list_intake_queue()            # mq list [bugs|changes|migrations|analyses|all]
get_next_intake()              # Pakt oudste document uit todo/
move_to_in_progress()          # Verplaatst intake naar in-progress/
move_to_done()                 # Verplaatst intake naar done/
sync_intake_to_platform()      # Synct lokale intake naar platform DB
```

## Appendix D: Intake Document Structuur

```
<project-root>/.marqed/intake/
├── bugs/
│   ├── todo/                  # Nieuwe bugs - wachtend op behandeling
│   │   └── BUG-YYYY-MM-DD-NNN.md
│   ├── in-progress/           # Bug wordt nu behandeld
│   └── done/                  # Afgehandelde bugs
├── changes/
│   ├── todo/
│   ├── in-progress/
│   └── done/
├── migrations/
│   ├── todo/
│   ├── in-progress/
│   └── done/
└── analyses/
    ├── todo/
    ├── in-progress/
    └── done/
```

**Naamgeving**: `{TYPE}-{YYYY-MM-DD}-{NNN}.md`
- `BUG-2026-01-24-001.md`
- `CHANGE-2026-01-24-001.md`
- `MIGRATE-2026-01-24-001.md`
- `ANALYZE-2026-01-24-001.md`

---

**Document Status**: APPROVED
**Auteur**: Peter (Product Owner)
**Review**: Felix (Architect), Quinn (Quality)
**Datum**: 2026-01-24
**Volgende Review**: Week 148 (M1 Checkpoint)

---

*MarQed.ai Platform - mq Workflow Integration*
