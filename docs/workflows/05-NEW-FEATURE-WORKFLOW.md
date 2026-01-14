# New Feature Workflow (Enhancement Projects)

## Overview

The New Feature workflow guides the addition of features to existing systems through impact analysis, design, and task generation.

**Use Case**: Adding features to existing systems (enhancements)
**API Prefix**: `/api/workflows/new-feature`
**Primary Agents**: Quinn (Quality Analyst), Felix (Feature Architect)

---

## Complete Workflow Steps

### Step 1: Feature Request Intake
**Creates a new feature request**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/workflows/new-feature` |
| **Service** | `NewFeatureService.create_request()` |
| **Agent** | None (system) |
| **Input** | `feature_name`, `description`, `requester`, `priority` |
| **Processing** | Create request, validate against existing features |
| **Output** | `request_id`, `status: pending_analysis` |
| **DB Table** | `items` |

**Request Example**:
```json
{
  "feature_name": "User Export Functionality",
  "description": "Allow users to export their data in CSV/JSON format",
  "requester": "product@company.com",
  "priority": "high"
}
```

---

### Step 2: Impact Analysis
**Quinn agent analyzes impact on existing system**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/workflows/new-feature/{request_id}/analyze` |
| **Service** | `NewFeatureService.analyze_impact()` |
| **Agent** | **Quinn** (Quality Analyst) |
| **LLM Model** | `codellama:7b` |
| **Input** | Feature request, codebase context |
| **Processing** | Dependency analysis, risk assessment, complexity scoring |
| **Output** | `impact_score`, `affected_modules[]`, `risks[]` |
| **DB Table** | `code_analysis` |

**Analysis Output**:
- Impact score (1-10)
- Affected modules and files
- Breaking change assessment
- Security implications
- Performance considerations

---

### Step 3: Risk Assessment
**Quinn agent evaluates risks and dependencies**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/workflows/new-feature/{request_id}/risk` |
| **Service** | `NewFeatureService.assess_risk()` |
| **Agent** | **Quinn** (Quality Analyst) |
| **LLM Model** | `codellama:7b` |
| **Input** | Impact analysis |
| **Processing** | Risk categorization, mitigation strategies |
| **Output** | `risk_level`, `mitigations[]`, `dependencies[]` |
| **DB Table** | `code_analysis` |

**Risk Categories**:
- **Low**: Minor changes, well-isolated
- **Medium**: Multiple modules affected, some dependencies
- **High**: Core system changes, breaking changes possible
- **Critical**: Architecture changes required

---

### Step 4: Architecture Design
**Felix agent designs the feature architecture**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/workflows/new-feature/{request_id}/design` |
| **Service** | `NewFeatureService.design_feature()` |
| **Agent** | **Felix** (Feature Architect) |
| **LLM Model** | `qwen2.5-coder:7b` |
| **Input** | Impact analysis, risk assessment |
| **Processing** | Architecture design, API design, data model changes |
| **Output** | `design_spec`, `api_changes[]`, `data_model_changes[]` |
| **DB Table** | `spec_shaping` |

**Design Output**:
- Component architecture
- API endpoint definitions
- Data model changes
- Integration points
- Migration requirements (if any)

---

### Step 5: Task Generation
**Felix agent generates implementation tasks**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/workflows/new-feature/{request_id}/tasks` |
| **Service** | `TaskGenerationService.generate_from_feature()` |
| **Agent** | **Felix** (Feature Architect) |
| **LLM Model** | `qwen2.5-coder:7b` |
| **Input** | Design specification |
| **Processing** | Epic/Story/Task breakdown |
| **Output** | `epics[]`, `stories[]`, `estimated_points` |
| **DB Table** | `task_hierarchy` |

---

### Step 6: Approval Gate
**User approves or rejects the feature plan**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/workflows/new-feature/{request_id}/approve` |
| **Service** | `NewFeatureService.approve()` |
| **Agent** | None (user decision) |
| **Input** | `action: approve|reject|modify`, `feedback` |
| **Processing** | Update status, create kanban items if approved |
| **Output** | `status`, `kanban_items[]` |
| **DB Table** | `items` |

---

## Database Schema

### Feature Request (in items table)
```sql
-- Feature requests are stored in the items table with type='feature'
INSERT INTO items (id, title, description, type, status, priority, metadata)
VALUES (
    'FEAT-001',
    'User Export Functionality',
    'Allow users to export their data',
    'feature',
    'pending_analysis',
    'high',
    '{"requester": "product@company.com", "impact_score": null}'
);
```

### spec_shaping (Design Storage)
```sql
CREATE TABLE spec_shaping (
    id UUID PRIMARY KEY,
    item_id VARCHAR(50) REFERENCES items(id),
    spec_type VARCHAR(50),  -- 'feature_design', 'api_spec', 'data_model'
    content JSONB,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## Workflow Navigation

### Entry Points
- **From MAINTENANCE ONLY**: Feature additions require an existing project in maintenance
- **Prerequisite**: Project must exist via GREEN_PAPER or BROWN_PAPER → KANBAN → MAINTENANCE
- **Dashboard**: `maintenance-scheduler.html` or `workflow-dashboard.html`
- **API**: `POST /api/workflows/new-feature`

**IMPORTANT:** NEW_FEATURE is NOT a top-level workflow. You cannot start NEW_FEATURE directly from BROWN_PAPER or GREEN_PAPER. A project must first go through KANBAN (implementation) and enter MAINTENANCE phase.

### Output -> Next Workflow

| Output | Dashboard | Next Options |
|--------|-----------|--------------|
| Tasks Generated | kanban-dashboard.html | -> KANBAN (implementation) |
| High Risk Detected | migration-analyzer.html | -> MIGRATION (via MAINTENANCE) |
| Approved | sprint-planning.html | -> KANBAN -> MAINTENANCE |

### Typical Flow
```
GREEN_PAPER/BROWN_PAPER → KANBAN → MAINTENANCE → NEW_FEATURE → KANBAN
                                              ↑              ↓
                                              └──────────────┘
```

### Workflow Hierarchy
```
Level 0 (Intake):     GREEN_PAPER / BROWN_PAPER
                              ↓
Level 1 (Optional):   MIGRATION (legacy modernization)
                              ↓
Level 2 (Build):      KANBAN (implementation)
                              ↓
Level 3 (Lifecycle):  MAINTENANCE
                              ↓
Level 4 (From Maint): BUG / NEW_FEATURE / MIGRATION (restart)
```

---

## Dashboards

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| Workflow Dashboard | `/workflow-dashboard.html` | Feature request tracking |
| Kanban Dashboard | `/kanban-dashboard.html` | Task management |
| Quality Dashboard | `/quality-dashboard.html` | Impact analysis results |

---

## Resume Capability

The New Feature workflow supports resume at any step:

1. **Status Tracking**: `items.status` field
2. **Analysis Caching**: Results stored in `code_analysis`
3. **Design Versioning**: `spec_shaping.version` for iterations

**Resume Query**:
```sql
SELECT i.id, i.status, i.metadata->>'impact_score' as impact
FROM items i
WHERE i.type = 'feature'
AND i.status NOT IN ('completed', 'rejected');
```

---

## Complete API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/workflows/new-feature` | Create feature request |
| GET | `/api/workflows/new-feature/{request_id}` | Get request status |
| POST | `/api/workflows/new-feature/{request_id}/analyze` | Run impact analysis |
| POST | `/api/workflows/new-feature/{request_id}/risk` | Run risk assessment |
| POST | `/api/workflows/new-feature/{request_id}/design` | Generate design |
| POST | `/api/workflows/new-feature/{request_id}/tasks` | Generate tasks |
| POST | `/api/workflows/new-feature/{request_id}/approve` | Approve/reject |
| GET | `/api/workflows/new-feature/{request_id}/export` | Export as Markdown |

---

## Technical Infrastructure

This workflow uses shared infrastructure components. See [99-TECHNICAL-INFRASTRUCTURE.md](./99-TECHNICAL-INFRASTRUCTURE.md) for details.

| Component | Used In Steps |
|-----------|---------------|
| AgentService | 2-5 (Quinn, Felix agents) |
| GraphWorkflowService | 2 (impact analysis) |
| TaskGenerationService | 5 (epic/story generation) |

---

_See also: [Master Overview](./00-WORKFLOW-MASTER-OVERVIEW.md) | [Brown Paper](./02-BROWN-PAPER-WORKFLOW.md) | [Infrastructure](./99-TECHNICAL-INFRASTRUCTURE.md)_
