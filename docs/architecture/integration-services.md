# Integration Services Architecture

**Parent Document:** [ARCHITECTURE.md](../../ARCHITECTURE.md)
**Status:** Week 75-79 COMPLETE
**Last Updated:** 2025-12-17

---

## Overview

Dit document beschrijft de integratie services:

1. **Graph Persistence** (Week 75) - Code knowledge graph
2. **CCPM GitHub Integration** (Week 79) - Git worktrees, Issues sync
3. **WorkflowToolIntegration** (Week 79) - Claude-Mem, CCPM, BigAGI across workflows

---

## 1. Graph Persistence Service (Week 75)

### Purpose

Persistent code knowledge graph for impact analysis and dependency tracking.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    GRAPH PERSISTENCE SERVICE                             │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  ENTITY STORAGE (PostgreSQL JSONB)                                   ││
│  │  • Classes, Functions, Modules, Variables                            ││
│  │  • Metadata: file path, line numbers, docstrings                     ││
│  │  • Relationships: imports, calls, inherits, contains                 ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                              │                                           │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  ANALYSIS FEATURES                                                   ││
│  │  • Impact Analysis (WITH RECURSIVE CTEs)                             ││
│  │  • Circular Dependency Detection                                      ││
│  │  • Module Coupling Metrics                                            ││
│  │  • Dead Code Detection                                                ││
│  │  • Graph Export (JSON, DOT format)                                    ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Features

- No external dependencies (Neo4j not needed)
- PostgreSQL JSONB for flexible entity storage
- Recursive CTEs for graph traversal
- Integration with existing KnowledgeGraphService

### Database Schema

```sql
CREATE TABLE code_entities (
    id UUID PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    entity_type VARCHAR(50) NOT NULL,  -- class, function, module, variable
    name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    line_start INTEGER,
    line_end INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE code_relationships (
    id UUID PRIMARY KEY,
    source_entity_id UUID REFERENCES code_entities(id),
    target_entity_id UUID REFERENCES code_entities(id),
    relationship_type VARCHAR(50) NOT NULL,  -- imports, calls, inherits, contains
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/code-graph/entities` | GET | List entities |
| `/api/code-graph/entities/{id}` | GET | Get entity details |
| `/api/code-graph/impact/{entity_id}` | GET | Impact analysis |
| `/api/code-graph/circular` | GET | Detect circular dependencies |
| `/api/code-graph/coupling` | GET | Module coupling metrics |
| `/api/code-graph/export` | GET | Export graph (JSON/DOT) |

---

## 2. CCPM GitHub Integration (Week 79)

### Purpose

Git worktree management, GitHub Issues sync, and PRD decomposition.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CCPM GITHUB INTEGRATION                                │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  GitWorktreeService                                                   ││
│  │  ├── create_worktree(agent_id, base_branch) → WorktreeInfo          ││
│  │  ├── merge_worktree(agent_id, target) → MergeResult                 ││
│  │  ├── cleanup_worktree(agent_id)                                      ││
│  │  └── list_active_worktrees() → List[WorktreeInfo]                   ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                              │                                           │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  GitHubIssuesService                                                  ││
│  │  ├── sync_issues(project_id, direction) - Bidirectional sync        ││
│  │  ├── create_issue_from_task(task_id) → GitHubIssue                  ││
│  │  └── update_task_from_issue(issue_number)                           ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                              │                                           │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  CCPMOrchestrator                                                     ││
│  │  ├── decompose_prd(prd_content) → Epic/Feature/Story/Task           ││
│  │  └── get_next_task(project_id) → TaskRecommendation                 ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### Database Schema

```sql
-- Git worktree tracking
CREATE TABLE git_worktrees (
    id UUID PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    project_id INTEGER REFERENCES projects(id),
    base_branch VARCHAR(255),
    worktree_path VARCHAR(1024),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- GitHub Issues sync
CREATE TABLE github_issues_sync (
    id UUID PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    github_issue_number INTEGER,
    local_task_id UUID,
    sync_direction VARCHAR(20),
    last_synced TIMESTAMP
);

-- PRD decompositions
CREATE TABLE prd_decompositions (
    id UUID PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    prd_content TEXT,
    epic_count INTEGER,
    feature_count INTEGER,
    story_count INTEGER,
    task_count INTEGER,
    decomposition_result JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| Worktree | `/api/ccpm/worktree/create` | POST | Create agent worktree |
| | `/api/ccpm/worktree/merge` | POST | Merge worktree to target |
| | `/api/ccpm/worktree/{id}` | DELETE | Cleanup worktree |
| | `/api/ccpm/worktrees` | GET | List active worktrees |
| Issues | `/api/ccpm/issues/sync` | POST | Sync GitHub issues |
| PRD | `/api/ccpm/prd/decompose` | POST | Decompose PRD |
| Tasks | `/api/ccpm/next-task/{project_id}` | GET | Get next prioritized task |
| Dashboard | `/api/ccpm/dashboard/stats` | GET | Dashboard statistics |
| Health | `/api/ccpm/health` | GET | Service health |

---

## 3. WorkflowToolIntegration Service (Week 79)

### Purpose

Integrate Claude-Mem, CCPM, and BigAGI across all workflow types.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW TOOL INTEGRATION SERVICE                      │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  GREEN_PAPER Integration                                              ││
│  │  ├── Claude-Mem: Session memory for 6 BMAD questions                 ││
│  │  │   └── Auto-tags: #green-paper, #bmad, #business-requirements      ││
│  │  └── CCPM: Constitution → Specification → Epic/Feature/Story/Task    ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  BROWN_PAPER Integration                                              ││
│  │  ├── Claude-Mem: Session memory for 8 BMAD questions                 ││
│  │  │   └── Auto-tags: #brown-paper, #migration, #legacy-analysis       ││
│  │  └── CCPM: Migration analysis → PRD → Epic/Feature/Story/Task        ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  QUALITY_AUDIT Integration                                            ││
│  │  └── BigAGI Beam: Multi-model consensus validation                   ││
│  │      └── Models: claude-3.5-sonnet, grok, mistral (weighted)         ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  Generic Workflow Capture (ALL workflows)                             ││
│  │  ├── Migration: Phase completion observations                        ││
│  │  ├── Bug: Root cause and fix tracking                                ││
│  │  ├── Quality: Scan results capture                                    ││
│  │  └── Cross-workflow context injection                                ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### Token Budget Management

| Workflow Type | Token Budget | Priority Tags |
|---------------|--------------|---------------|
| GREEN_PAPER | 6,000 | decision, architecture, business |
| BROWN_PAPER | 8,000 | migration, legacy, technical-debt |
| MIGRATION | 7,000 | migration, phase, issue |
| BUG | 4,000 | root-cause, fix, regression |
| QUALITY_AUDIT | 5,000 | security, quality, scan |

### Key Methods

```python
class WorkflowToolIntegrationService:
    # GREEN_PAPER Integration
    async def green_paper_session_start(session_id, project_id, title)
    async def green_paper_answer_submitted(session_id, question_number, question_text, answer)
    async def green_paper_specification_approved(project_id, spec_id, spec_content)

    # BROWN_PAPER Integration
    async def brown_paper_session_start(session_id, project_id, title, application_name)
    async def brown_paper_answer_submitted(session_id, question_number, question_text, answer, scan_data)
    async def brown_paper_analysis_approved(project_id, analysis_id, analysis_content)

    # QUALITY_AUDIT Integration
    async def quality_audit_start(session_id, project_id)
    async def quality_audit_complete(session_id, findings)

    # Generic Workflow Capture
    async def workflow_capture_observation(workflow_type, session_id, content, tags, priority)
    async def get_workflow_context(workflow_type, session_id, token_budget)
    async def inject_workflow_context(workflow_type, session_id, base_prompt, token_budget)
```

---

## Tool-Workflow Integration Matrix

### Current State (Week 80)

| Workflow | Claude-Mem | CCPM | BigAGI | GhostCrew | Graph | CodeWiki |
|----------|:----------:|:----:|:------:|:---------:|:-----:|:--------:|
| GREEN_PAPER | ✅ | ✅ | ❌ | ❌ | - | - |
| BROWN_PAPER | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| NEW_FEATURE | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| BUG | ✅ | ❌ | - | ✅ | ❌ | - |
| MAINTENANCE | ✅ | ❌ | - | ✅ | ❌ | ❌ |
| MIGRATION | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| QUALITY_AUDIT | ✅ | - | ✅ | ✅ | ❌ | - |
| QUALITY_IMPROVEMENT | ❌ | - | ✅ | ❌ | ❌ | - |
| TESTING | ✅ | ❌ | - | ❌ | ❌ | ❌ |
| ENHANCEMENT | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| PROJECT_DEFINITION | ✅ | ❌ | ❌ | - | - | - |

**Legenda:** ✅ = Geïntegreerd | ❌ = Ontbreekt | `-` = N/A

### Target State (Week 90)

| Workflow | Claude-Mem | CCPM | BigAGI | GhostCrew | Graph | CodeWiki |
|----------|:----------:|:----:|:------:|:---------:|:-----:|:--------:|
| GREEN_PAPER | ✅ | ✅ | ✅ | ✅ | - | - |
| BROWN_PAPER | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| NEW_FEATURE | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| BUG | ✅ | ✅ | - | ✅ | ✅ | - |
| MAINTENANCE | ✅ | ✅ | - | ✅ | ✅ | ✅ |
| MIGRATION | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| QUALITY_AUDIT | ✅ | - | ✅ | ✅ | ✅ | - |
| QUALITY_IMPROVEMENT | ✅ | - | ✅ | ✅ | ✅ | - |
| TESTING | ✅ | ✅ | - | ✅ | ✅ | ✅ |
| ENHANCEMENT | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PROJECT_DEFINITION | ✅ | ✅ | ✅ | - | - | - |

---

## Related Documents

- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Main architecture overview
- [observability-layer.md](./observability-layer.md) - Claude-Mem details
- [kanban-system.md](./kanban-system.md) - Kanban integration
