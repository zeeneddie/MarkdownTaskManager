# Migration Workflow (Legacy Modernization)

## Overview

The Migration workflow guides legacy system modernization through an 8-question interview process, generating migration analysis, specifications, and task breakdowns.

**Use Case**: Modernizing legacy systems (migration projects)
**API Prefix**: `/api/brown-paper/bmad` (v1), `/api/v2/migration` (v2)
**Primary Agents**: Miguel (Migration), Peter (Product Owner), Felix (Architect)

---

## Domain Architecture (v2)

**Specification:** [workflow-separation-plan.md](../architecture/workflow-separation-plan.md)

Migration is the **Execution Domain** - 100% separated from Brown Paper. Receives input via `AnalysisContract`.

```
+-------------------+                 +-------------------+
|    BROWN PAPER    |                 |     MIGRATION     |
|  (Analysis)       |                 |   (Execution)     |
|                   |                 |                   |
| Creates:          | -- Contract --> | Consumes:         |
| AnalysisContract  |                 | AnalysisContract  |
+-------------------+                 +-------------------+
```

### API v2 Changes (Breaking)

| Old (v1) | New (v2) |
|----------|----------|
| `POST /api/migration/start` with `brown_paper_session_id` | `POST /api/v2/migration/start` with `analysis_id` |

**New Flow:**
1. Complete Brown Paper analysis
2. Create contract: `POST /api/v2/migration/contracts/from-brown-paper`
3. Start migration: `POST /api/v2/migration/start` with `analysis_id`

**Legacy Endpoint (Deprecated):**
`POST /api/migration/start/legacy` - Auto-creates contract for backwards compatibility

---

## Complete Workflow Steps

### Step 1: Start Migration Session
**Creates a new migration session**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/brown-paper/bmad/start` |
| **Service** | `BrownPaperService.start_bmad_session()` |
| **Agent** | None (system) |
| **Input** | `project_name`, `project_path` |
| **Processing** | Create session, load 8 migration questions |
| **Output** | `session_id`, `first_question`, `status: started` |
| **DB Table** | `bmad_sessions` |

**Request Example**:
```json
{
  "project_name": "Legacy CRM Migration",
  "project_path": "/path/to/legacy/system"
}
```

---

### Step 2-5: Answer Questions Q1-Q4 (Miguel Agent)
**Technical migration questions**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/brown-paper/bmad/{session_id}/answer` |
| **Service** | `BrownPaperService.submit_bmad_answer()` |
| **Agent** | **Miguel** (Migration Specialist) |
| **Input** | `answer` text |
| **Processing** | Validate, store, provide next question |
| **Output** | `answer_stored`, `next_question` |
| **DB Table** | `bmad_sessions.answers` (JSONB) |

**Questions 1-4 (Technical)**:
1. What is the current technology stack? (Languages, frameworks, databases)
2. What are the major pain points in the current system?
3. What data needs to be migrated? (Volumes, formats, relationships)
4. What integrations exist with external systems?

---

### Step 6-8: Answer Questions Q5-Q7 (Peter Agent)
**Business migration questions**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/brown-paper/bmad/{session_id}/answer` |
| **Service** | `BrownPaperService.submit_bmad_answer()` |
| **Agent** | **Peter** (Product Owner) |
| **Input** | `answer` text |
| **Processing** | Validate, store, provide next question |
| **Output** | `answer_stored`, `next_question` |
| **DB Table** | `bmad_sessions.answers` (JSONB) |

**Questions 5-7 (Business)**:
5. What is the target technology stack?
6. What business processes must continue during migration?
7. What compliance/regulatory requirements apply?

---

### Step 9: Answer Question Q8 (Felix Agent)
**Architecture question**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/brown-paper/bmad/{session_id}/answer` |
| **Service** | `BrownPaperService.submit_bmad_answer()` |
| **Agent** | **Felix** (Feature Architect) |
| **Input** | `answer` text |
| **Processing** | Validate, store, mark session complete |
| **Output** | `all_questions_answered: true`, `ready_for_analysis` |
| **DB Table** | `bmad_sessions.answers` (JSONB) |

**Question 8 (Architecture)**:
8. What is the target architecture pattern? (Microservices, modular monolith, etc.)

---

### Step 10: Migration Analysis
**Miguel agent analyzes migration complexity**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/brown-paper/bmad/{session_id}/analyze` |
| **Service** | `BrownPaperService.analyze_bmad()` |
| **Agent** | **Miguel** (Migration Specialist) |
| **LLM Model** | `deepseek-r1:latest` |
| **Input** | All 8 answers |
| **Processing** | Complexity scoring, risk identification, dependency mapping |
| **Output** | `complexity_score`, `risks[]`, `dependencies[]` |
| **DB Table** | `bmad_sessions.migration_analysis` (JSONB) |

**Analysis Output**:
- Migration complexity score (1-10)
- Risk assessment matrix
- Dependency analysis
- Estimated timeline
- Resource requirements

---

### Step 11: Generate Migration Specification
**Peter agent creates migration plan specification**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/brown-paper/bmad/{session_id}/specification` |
| **Service** | `BrownPaperService.generate_bmad_spec()` |
| **Agent** | **Peter** (Product Owner) |
| **LLM Model** | `deepseek-r1:latest` |
| **Input** | Migration analysis |
| **Processing** | Specification generation |
| **Output** | `specification_id`, `content_json`, `content_markdown` |
| **DB Table** | `bmad_sessions.specification` (JSONB) |

---

### Step 12: Generate Migration Tasks
**Felix agent breaks down into migration epics/tasks**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/brown-paper/bmad/{session_id}/tasks` |
| **Service** | `BrownPaperService.generate_bmad_tasks()` |
| **Agent** | **Felix** (Feature Architect) |
| **LLM Model** | `qwen2.5-coder:7b` |
| **Input** | Specification |
| **Processing** | Task breakdown with migration phases |
| **Output** | `epics[]`, `stories[]`, `migration_phases[]` |
| **DB Table** | `bmad_sessions.tasks` (JSONB) |

---

### Step 13: Enhanced Analysis (Optional)
**Full 6-phase code analysis**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/brown-paper/bmad/{session_id}/enhanced-analyze` |
| **Service** | `BrownPaperService` |
| **Agent** | All (LLM Council) |
| **Input** | `project_path` |
| **Processing** | 6-phase Brown Paper analysis |
| **Output** | Full analysis results |
| **DB Table** | `bmad_sessions.enhanced_analysis` (JSONB) |

---

### Step 14: Export Migration Plan
**Export complete migration plan as Markdown**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `GET /api/brown-paper/bmad/{session_id}/export` |
| **Service** | `BrownPaperService.export_bmad()` |
| **Agent** | None (formatting) |
| **Input** | Session data |
| **Processing** | Markdown export |
| **Output** | `PROJECT_CONSTITUTION.md` file |
| **DB Table** | None (file export) |

---

## Database Schema

### bmad_sessions
```sql
CREATE TABLE bmad_sessions (
    id UUID PRIMARY KEY,
    project_name VARCHAR(200),
    project_path TEXT,
    status VARCHAR(20),  -- started, questions_complete, analyzed, specified, tasked

    -- All data stored as JSONB for flexibility
    answers JSONB,  -- {q1: "...", q2: "...", ...q8: "..."}
    migration_analysis JSONB,  -- Analysis results
    specification JSONB,  -- Generated specification
    tasks JSONB,  -- Generated tasks/epics
    enhanced_analysis JSONB,  -- Optional 6-phase results

    -- Tracking
    current_question INTEGER DEFAULT 1,
    questions_completed BOOLEAN DEFAULT FALSE,
    can_resume BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Audit
    event_log JSONB  -- Array of all events for audit trail
);
```

---

## 8-Question Flow

```
Q1-Q4: Technical (Miguel)           Q5-Q7: Business (Peter)      Q8: Architecture (Felix)
+-------------------------+         +------------------------+   +----------------------+
| Q1: Current Stack       |   -->   | Q5: Target Stack       |-->| Q8: Target Pattern   |
| Q2: Pain Points         |         | Q6: Business Continuity|   | (Microservices/etc)  |
| Q3: Data Migration      |         | Q7: Compliance/Regs    |   +----------------------+
| Q4: External Integrations|         +------------------------+            |
+-------------------------+                                                v
                                                                   Analysis → Spec → Tasks
```

---

## Dashboards

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| Brown Paper Dashboard | `/brown-paper-dashboard.html` | Session overview |
| Migration Analyzer | `/migration-analyzer.html` | Detailed migration analysis |
| Migration Progress | `/migration-progress-dashboard.html` | Execution tracking |

---

## Resume Capability

The Migration workflow has robust resume support:

1. **Question Tracking**: `current_question` field
2. **can_resume Flag**: Explicit resume capability
3. **Event Log**: Full audit trail in JSONB
4. **Answer Versioning**: Previous answers preserved

**Check Resume Status**:
```sql
SELECT id, project_name, current_question, can_resume,
       jsonb_array_length(answers) as answered_count
FROM bmad_sessions
WHERE status != 'completed';
```

---

## Complete API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/brown-paper/bmad/start` | Start migration session |
| GET | `/api/brown-paper/bmad/{session_id}` | Get session status |
| POST | `/api/brown-paper/bmad/{session_id}/answer` | Submit answer |
| GET | `/api/brown-paper/bmad/{session_id}/questions` | Get all questions |
| POST | `/api/brown-paper/bmad/{session_id}/analyze` | Run migration analysis |
| POST | `/api/brown-paper/bmad/{session_id}/specification` | Generate specification |
| POST | `/api/brown-paper/bmad/{session_id}/tasks` | Generate tasks |
| POST | `/api/brown-paper/bmad/{session_id}/enhanced-analyze` | Run 6-phase analysis |
| GET | `/api/brown-paper/bmad/{session_id}/export` | Export as Markdown |

---

## Migration Phases (Generated Output)

The task generation creates migration-specific phases:

1. **Assessment Phase**: Code analysis, dependency mapping
2. **Planning Phase**: Architecture design, timeline creation
3. **Foundation Phase**: Core infrastructure, CI/CD setup
4. **Data Migration Phase**: Schema migration, data transfer
5. **Application Migration Phase**: Feature-by-feature migration
6. **Integration Phase**: External system reconnection
7. **Testing Phase**: Regression, performance testing
8. **Cutover Phase**: Go-live, rollback procedures
9. **Decommission Phase**: Legacy shutdown, cleanup

---

## Workflow Navigation

### Entry Points
- **From BROWN_PAPER**: After analysis shows legacy modernization is needed
- **From MAINTENANCE**: When technical debt requires full system migration
- **Dashboard**: `migration-analyzer.html`
- **API**: `POST /api/brown-paper/bmad/start`

### Output → Next Workflow

| Output | Dashboard | Next Options |
|--------|-----------|--------------|
| Migration Tasks | migration-progress-dashboard.html | → Track implementation |
| Export Complete | kanban-dashboard.html | → MAINTENANCE (ongoing) |

### Typical Flow
```
BROWN_PAPER → MIGRATION → kanban-dashboard → MAINTENANCE
                       ↑                           │
                       └───────────────────────────┘
                         (lifecycle restart)
```

---

## Technical Infrastructure

This workflow uses shared infrastructure components. See [99-TECHNICAL-INFRASTRUCTURE.md](./99-TECHNICAL-INFRASTRUCTURE.md) for details.

| Component | Used In Steps |
|-----------|---------------|
| AgentService | 2-9 (Miguel, Peter, Felix agents) |
| GraphWorkflowService | 10, 13 (dependency analysis) |

---

_See also: [Master Overview](./00-WORKFLOW-MASTER-OVERVIEW.md) | [Brown Paper](./02-BROWN-PAPER-WORKFLOW.md) | [Infrastructure](./99-TECHNICAL-INFRASTRUCTURE.md)_
