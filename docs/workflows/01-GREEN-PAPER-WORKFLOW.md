# Green Paper Workflow (Greenfield Projects)

## Overview

The Green Paper workflow guides new project creation through a structured 6-question process, generating a project constitution and high-level design specification.

**Use Case**: Starting new systems from scratch (greenfield development)
**API Prefix**: `/api/green-paper`
**Primary Agents**: Peter (Product Owner), Felix (Feature Architect)

---

## Complete Workflow Steps

### Step 1: Session Start
**Creates a new session with 6 questions**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/green-paper/sessions` |
| **Service** | `GreenPaperService.start_session()` |
| **Agent** | None (system) |
| **Input** | `project_id`, `metadata` |
| **Processing** | Create session record, load 6 discovery questions |
| **Output** | `session_id`, `questions[]`, `status: in_progress` |
| **DB Table** | `green_paper_sessions` |

**Request Example**:
```json
{
  "project_id": "EPIC-001",
  "metadata": {
    "initiated_by": "user@example.com",
    "context": "New CRM system"
  }
}
```

**Response Example**:
```json
{
  "session_id": "uuid-xxx",
  "project_id": "EPIC-001",
  "status": "in_progress",
  "current_question": 1,
  "total_questions": 6,
  "questions": [
    {
      "number": 1,
      "text": "What problem are you solving?",
      "is_required": true,
      "max_length": 2000
    }
  ]
}
```

---

### Step 2: Answer Questions (Q1-Q6)
**User submits answers to discovery questions**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/green-paper/sessions/{session_id}/answers` |
| **Service** | `GreenPaperService.submit_answer()` |
| **Agent** | None (user input) |
| **Input** | `question_number`, `answer`, `metadata` |
| **Processing** | Validate answer, store, update progress |
| **Output** | `answer_id`, `progress`, `next_question` |
| **DB Table** | `green_paper_answers` |

**Discovery Questions**:
1. What problem are you solving? (Required)
2. Who is your target user? (Required)
3. What is your unique value proposition? (Required)
4. What are the key features? (Required)
5. What technology constraints exist? (Optional)
6. What is your timeline and budget? (Optional)

---

### Step 3: Generate Constitution
**Peter agent creates project constitution from answers**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/green-paper/sessions/{session_id}/constitution` |
| **Service** | `GreenPaperService.generate_constitution()` |
| **Agent** | **Peter** (Product Owner) |
| **LLM Model** | `deepseek-r1:latest` |
| **Input** | All 6 answers from session |
| **Processing** | LLM generation (1000-1500 words, 7 sections) |
| **Output** | `constitution_id`, `content_json`, `content_markdown` |
| **DB Table** | `green_paper_constitutions` |

**Constitution Sections**:
1. Vision Statement
2. Core Principles
3. Functional Requirements
4. Non-Functional Requirements
5. Constraints & Assumptions
6. Risks & Mitigations
7. Success Criteria

---

### Step 4: Review Constitution
**User approves or rejects the constitution**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/green-paper/constitutions/{constitution_id}/review` |
| **Service** | `GreenPaperService.review_constitution()` |
| **Agent** | None (user decision) |
| **Input** | `action: approve|reject`, `feedback`, `requested_changes` |
| **Processing** | Update status, trigger next step or regeneration |
| **Output** | `status`, `next_step`, `next_actions[]` |
| **DB Table** | `green_paper_constitutions` |

**If Approved**: Proceed to Specification generation
**If Rejected**: Regenerate constitution (max 3 attempts)

---

### Step 5: Generate Specification (HLD)
**Felix agent creates High-Level Design specification**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/green-paper/constitutions/{constitution_id}/specification` |
| **Service** | `GreenPaperService.generate_specification()` |
| **Agent** | **Felix** (Feature Architect) |
| **LLM Model** | `qwen2.5-coder:7b` |
| **Input** | Approved constitution |
| **Processing** | Architecture design, 10-section HLD |
| **Output** | `specification_id`, `content_json`, `content_markdown` |
| **DB Table** | `green_paper_specifications` |

**Specification Sections**:
1. Architecture Overview
2. System Components
3. Data Model
4. API Design
5. Security Architecture
6. Integration Points
7. Deployment Strategy
8. Performance Requirements
9. Monitoring & Observability
10. Technical Risks

---

### Step 6: Generate Epics/Stories/Tasks
**Felix agent breaks down specification into work items**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/task-generation/specifications/{specification_id}/epics` |
| **Service** | `TaskGenerationService.generate_epics()` |
| **Agent** | **Felix** (Feature Architect) |
| **LLM Model** | `qwen2.5-coder:7b` |
| **Input** | Approved specification |
| **Processing** | Hierarchical breakdown: Epic → Feature → Story → Task |
| **Output** | Epic list with estimates |
| **DB Table** | `task_hierarchy` (epics, features, stories, tasks) |

---

## Database Schema

### green_paper_sessions
```sql
CREATE TABLE green_paper_sessions (
    id UUID PRIMARY KEY,
    project_id VARCHAR(50) REFERENCES items(id),
    session_type VARCHAR(50) DEFAULT 'green-paper',
    status VARCHAR(20) DEFAULT 'in_progress',  -- in_progress, completed, abandoned
    current_question INTEGER DEFAULT 1,
    total_questions INTEGER DEFAULT 6,
    progress_percentage INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    completed_at TIMESTAMP,
    generation_metadata JSONB
);
```

### green_paper_answers
```sql
CREATE TABLE green_paper_answers (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES green_paper_sessions(id),
    question_number INTEGER,
    question_text TEXT,
    answer TEXT,
    is_required INTEGER,
    max_length INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    generation_metadata JSONB
);
```

### green_paper_constitutions
```sql
CREATE TABLE green_paper_constitutions (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES green_paper_sessions(id),
    project_id VARCHAR(50) REFERENCES items(id),
    status VARCHAR(20) DEFAULT 'draft',  -- draft, pending_review, approved, rejected
    content_json JSONB,
    content_markdown TEXT,
    word_count INTEGER,
    generated_by VARCHAR(50) DEFAULT 'Peter',
    reviewed_at TIMESTAMP,
    reviewed_by VARCHAR(100),
    review_feedback TEXT,
    generation_attempt INTEGER DEFAULT 1,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    generation_metadata JSONB
);
```

### green_paper_specifications
```sql
CREATE TABLE green_paper_specifications (
    id UUID PRIMARY KEY,
    constitution_id UUID REFERENCES green_paper_constitutions(id),
    project_id VARCHAR(50) REFERENCES items(id),
    status VARCHAR(20) DEFAULT 'draft',
    content_json JSONB,
    content_markdown TEXT,
    generated_by VARCHAR(50) DEFAULT 'Felix',
    reviewed_at TIMESTAMP,
    reviewed_by VARCHAR(100),
    review_feedback TEXT,
    generation_attempt INTEGER DEFAULT 1,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    generation_metadata JSONB
);
```

---

## Dashboards

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| Brown Paper Dashboard | `/brown-paper-dashboard.html` | Session overview, progress |
| Workflow Dashboard | `/workflow-dashboard.html` | Execution monitoring |
| Kanban Dashboard | `/kanban-dashboard.html` | Task management |

---

## Resume Capability

The Green Paper workflow supports full resume after restart:

1. **Session Tracking**: `status` field tracks current phase
2. **Question Progress**: `current_question` tracks answered questions
3. **Constitution Status**: `generation_attempt` for retry tracking
4. **Specification Status**: Same retry mechanism

**Resume Query**:
```sql
SELECT * FROM green_paper_sessions
WHERE project_id = 'PROJECT-001'
AND status = 'in_progress';
```

---

## Error Handling

| Error | HTTP Code | Recovery |
|-------|-----------|----------|
| Session not found | 404 | Create new session |
| Invalid question number | 400 | Check current_question |
| Constitution generation failed | 500 | Retry (max 3 attempts) |
| Specification generation failed | 500 | Retry (max 3 attempts) |
| LLM timeout | 504 | Automatic retry with backoff |

---

## Complete API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/green-paper/sessions` | Start discovery session |
| GET | `/api/green-paper/sessions/{session_id}` | Get session status |
| POST | `/api/green-paper/sessions/{session_id}/answers` | Submit answer |
| GET | `/api/green-paper/sessions/{session_id}/statistics` | Get session stats |
| POST | `/api/green-paper/sessions/{session_id}/constitution` | Generate constitution |
| GET | `/api/green-paper/constitutions/{constitution_id}` | Get constitution |
| POST | `/api/green-paper/constitutions/{constitution_id}/review` | Review constitution |
| POST | `/api/green-paper/constitutions/{constitution_id}/regenerate` | Regenerate constitution |
| POST | `/api/green-paper/constitutions/{constitution_id}/embeddings` | Store in vector DB |
| POST | `/api/green-paper/constitutions/{constitution_id}/specification` | Generate specification |
| GET | `/api/green-paper/specifications/{specification_id}` | Get specification |
| POST | `/api/green-paper/specifications/{specification_id}/review` | Review specification |
| POST | `/api/green-paper/specifications/{specification_id}/regenerate` | Regenerate specification |
| GET | `/api/green-paper/projects/similar` | Search similar projects |
| GET | `/api/green-paper/health` | Health check |

---

## Workflow Navigation

### Entry Point
- **Dashboard**: `project-wizard.html` or `brown-paper-dashboard.html`
- **API**: `POST /api/green-paper/sessions`

### Output → Next Workflow

| Output | Dashboard | Next Options |
|--------|-----------|--------------|
| Specification Complete | kanban-dashboard.html | → MAINTENANCE (ongoing) |
| Epics Generated | kanban-dashboard.html | → Implementation (Phase 4) |

### Typical Flow
```
GREEN_PAPER → kanban-dashboard → MAINTENANCE
                               → BUG (if issues found)
```

---

## Technical Infrastructure

This workflow uses shared infrastructure components. See [99-TECHNICAL-INFRASTRUCTURE.md](./99-TECHNICAL-INFRASTRUCTURE.md) for details.

| Component | Used In Steps |
|-----------|---------------|
| AgentService | 3 (Peter), 5 (Felix), 6 (Felix) |
| ChromaService | 5 (embeddings), search |
| GhostCrew | Security audit (optional) |
| BigAGI | Multi-model validation (optional) |

---

_See also: [Master Overview](./00-WORKFLOW-MASTER-OVERVIEW.md) | [Brown Paper](./02-BROWN-PAPER-WORKFLOW.md) | [Infrastructure](./99-TECHNICAL-INFRASTRUCTURE.md)_
