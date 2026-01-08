# Week 55 Status: Human-in-the-Loop Council

**Datum**: 2025-11-26 (Started)
**Focus**: Human validation in Council workflow + Dashboard UIs
**Track**: Multi-Stack Platform Week 2
**Status**: COMPLETE

---

## Week 55 Progress

| Day | Focus | Output | Status |
|-----|-------|--------|--------|
| 1 | Frontend | Council Human Review Dashboard (`frontend/council-human-review.html`) | DONE |
| 1 | Route Setup | Added frontend routes to main.py | DONE |
| 1 | Model Fix | Fixed `metadata` column naming (SQLAlchemy reserved word) | DONE |
| 2 | E2E Testing | DocumentSyncService E2E tests | DONE |
| 3 | Full Workflow | Council + Observability E2E tests | DONE |

---

## Week 55 Deliverables

| Deliverable | Location | Status |
|-------------|----------|--------|
| Council Human Review UI | `frontend/council-human-review.html` | DONE |
| Navigation Update | Added Council Review link to `frontend/index.html` | DONE |
| Frontend Routes | `app/main.py` - council-human-review.html + observability-dashboard.html | DONE |
| Model Fix | `app/models/council_human_review.py` - `extra_data` alias for `metadata` column | DONE |

---

## 6-Phase Human-in-the-Loop Workflow

```
1. Provider Generation -> 2. Peer Review -> 3. Orchestrator Synthesis
                                              |
                    4. Human Review (checkboxes, conflicts, missing info)
                                              |
            5. Final Synthesis (LLM incorporates human feedback)
                                              |
                6. Storage & Sync (MD files + DB + Git commit)
```

---

## New Database Tables (Week 55)

```sql
-- Council sessie tracking
CREATE TABLE council_sessions (
    id UUID PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    document_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    approved_by VARCHAR(100)
);

-- Council consensus met versioning
CREATE TABLE council_consensus (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES council_sessions(id),
    version INTEGER DEFAULT 1,
    consensus_content TEXT NOT NULL,
    human_feedback JSONB,
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Document versies (MD files synced)
CREATE TABLE document_versions (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    document_path VARCHAR(500) NOT NULL,
    version INTEGER DEFAULT 1,
    content TEXT NOT NULL,
    council_session_id UUID REFERENCES council_sessions(id),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## New API Endpoints (Week 55)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/council/sessions` | POST | Start nieuwe council sessie |
| `/api/council/sessions/{id}` | GET | Haal sessie details op |
| `/api/council/sessions/{id}/consensus` | GET | Haal consensus document op |
| `/api/council/sessions/{id}/review` | POST | Submit human review |
| `/api/council/sessions/{id}/approve` | POST | Approve & finalize document |
| `/api/council/sessions/{id}/reject` | POST | Reject met reden |

---

**Zie ook**:
- [Week 54 Status](./week-54-status.md) - Provider Registry
- [Project Documentation Standard](../architecture/project-documentation-standard.md)
