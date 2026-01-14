# Brown Paper Workflow (Brownfield Projects)

## Overview

The Brown Paper workflow analyzes existing codebases through a 6-phase analysis pipeline, extracting architecture, dependencies, and generating epic/story breakdowns for modernization or enhancement.

**Use Case**: Analyzing existing systems (brownfield development)
**API Prefix**: `/api/brown-paper`
**Primary Agents**: Multiple (Council-based extraction)

---

## Domain Architecture (v2)

**Specification:** [workflow-separation-plan.md](../architecture/workflow-separation-plan.md)

Brown Paper is the **Analysis Domain** - 100% separated from Migration. Output is an `AnalysisContract` that Migration consumes.

```
+-------------------+                 +-------------------+
|    BROWN PAPER    |                 |     MIGRATION     |
|  (Analysis)       |                 |   (Execution)     |
|                   |                 |                   |
| Creates:          | -- Contract --> | Consumes:         |
| AnalysisContract  |                 | AnalysisContract  |
+-------------------+                 +-------------------+
```

**New Flow (v2):**
1. Brown Paper creates analysis -> `AnalysisContract`
2. Contract stored via `/api/v2/migration/contracts/from-brown-paper`
3. Migration starts with `analysis_id` (NOT `brown_paper_session_id`)

**Quality Integration:**
- Quality scans run automatically during Brown Paper Phase 1
- Results stored in `AnalysisContract.stability`

---

## Complete Workflow Steps

### Step 1: Session Start
**Creates a new analysis session**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/brown-paper/sessions` |
| **Service** | `BrownPaperService.start_session()` |
| **Agent** | None (system) |
| **Input** | `application_id`, `project_path` |
| **Processing** | Create session, prepare analysis context |
| **Output** | `session_id`, `status: created` |
| **DB Table** | `brown_paper_sessions` |

**Request Example**:
```json
{
  "application_id": "APP-001",
  "project_path": "/path/to/codebase"
}
```

---

### Step 2: Basic Analysis
**Initial code structure scan**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/brown-paper/sessions/{session_id}/analyze` |
| **Service** | `BrownPaperService.analyze()` |
| **Agent** | None (static analysis) |
| **Input** | `session_id` |
| **Processing** | File scan, module detection, pattern matching |
| **Output** | `modules[]`, `patterns[]`, `statistics` |
| **DB Table** | `brown_paper_analyses` |

---

### Step 3: Enhanced Analysis Phase 1 (Foundation)
**Deep code analysis with dependency mapping**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/brown-paper/sessions/{session_id}/enhanced-analyze` |
| **Service** | `BrownPaperService.run_phase_1()` |
| **Agent** | None (static + AST analysis) |
| **Input** | `project_path` |
| **Processing** | DependencyGraph, CodeAnalysis, Foundation metrics |
| **Output** | `dependency_graph`, `code_metrics`, `coupling_analysis` |
| **DB Table** | `brown_paper_sessions.enhanced_analysis` (JSONB) |

**Phase 1 Components**:
- File dependency graph
- Import/export analysis
- Code complexity metrics
- Cyclomatic complexity
- Lines of code statistics

---

### Step 4: Enhanced Analysis Phase 2 (Domains)
**Business domain extraction**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | (continues from Phase 1) |
| **Service** | `BrownPaperService.run_phase_2()` |
| **Agent** | None (pattern matching) |
| **Input** | Phase 1 results |
| **Processing** | Domain extraction, bounded context identification |
| **Output** | `domains[]`, `bounded_contexts[]` |
| **DB Table** | `brown_paper_domains` |

---

### Step 5: Enhanced Analysis Phase 3 (Hierarchy)
**Epic/Feature/Story extraction**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | (continues) |
| **Service** | `HierarchicalExtractionService` |
| **Agent** | None (template-based) |
| **Input** | Domains from Phase 2 |
| **Processing** | Few-shot extraction, hierarchy building |
| **Output** | `epics[]`, `features[]`, `stories[]` |
| **DB Table** | `brown_paper_epics` |

---

### Step 6: Enhanced Analysis Phase 4 (Deep Extraction)
**LLM Council for consensus-based story refinement**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | (continues) |
| **Service** | `DeepExtractionService` |
| **Agent** | **LLM Council** (multiple models) |
| **LLM Models** | Multiple (consensus voting) |
| **Input** | Hierarchy from Phase 3 |
| **Processing** | Multi-model extraction, INVEST validation, consensus |
| **Output** | `validated_stories[]`, `consensus_scores` |
| **DB Table** | `deep_extraction` |

**Council Models**:
- deepseek-r1:latest
- qwen2.5-coder:7b
- codellama:7b
- mistral:7b

---

### Step 7: Enhanced Analysis Phase 5 (Estimation)
**Function Point and Story Point estimation**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | (continues) |
| **Service** | `BrownPaperEstimationService` |
| **Agent** | **Eliza** (Estimator) |
| **LLM Model** | `deepseek-r1:latest` |
| **Input** | All previous phases |
| **Processing** | IFPUG FP Analysis, complexity scoring |
| **Output** | `function_points`, `story_points`, `effort_estimate` |
| **DB Table** | `estimation_history` |

**Estimation Output**:
- External Inputs (EI)
- External Outputs (EO)
- External Inquiries (EQ)
- Internal Logical Files (ILF)
- External Interface Files (EIF)
- Unadjusted Function Points (UFP)
- Value Adjustment Factor (VAF)
- Adjusted Function Points (AFP)

---

### Step 8: Enhanced Analysis Phase 6 (Output)
**Final consolidation and summary**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | (continues) |
| **Service** | `BrownPaperService` |
| **Agent** | None (aggregation) |
| **Input** | All phases |
| **Processing** | Consolidation, report generation |
| **Output** | `summary`, `recommendations[]` |
| **DB Table** | `brown_paper_sessions` |

---

### Step 9: Generate Constitution (Optional)
**Peter agent creates project constitution from analysis**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/brown-paper/sessions/{session_id}/constitution` |
| **Service** | `BrownPaperService.generate_constitution()` |
| **Agent** | **Peter** (Product Owner) |
| **LLM Model** | `deepseek-r1:latest` |
| **Input** | Analysis results |
| **Processing** | Constitution generation |
| **Output** | `constitution_id`, `content_json`, `content_markdown` |
| **DB Table** | `brown_paper_constitutions` |

---

### Step 10: Generate Epics (Optional)
**Felix agent generates implementation epics**

| Aspect | Details |
|--------|---------|
| **API Endpoint** | `POST /api/brown-paper/sessions/{session_id}/epics` |
| **Service** | `BrownPaperService.generate_epics()` |
| **Agent** | **Felix** (Feature Architect) |
| **LLM Model** | `qwen2.5-coder:7b` |
| **Input** | Constitution |
| **Processing** | Epic breakdown |
| **Output** | `epics[]` with estimates |
| **DB Table** | `brown_paper_epics` |

---

## Database Schema

### brown_paper_sessions
```sql
CREATE TABLE brown_paper_sessions (
    id UUID PRIMARY KEY,
    application_id VARCHAR(50),
    project_path TEXT,
    status VARCHAR(20),  -- created, analyzing, completed, failed
    enhanced_analysis JSONB,  -- 6-phase results cached here
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### brown_paper_analyses
```sql
CREATE TABLE brown_paper_analyses (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES brown_paper_sessions(id),
    analysis_type VARCHAR(50),
    results JSONB,
    created_at TIMESTAMP
);
```

### brown_paper_domains
```sql
CREATE TABLE brown_paper_domains (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES brown_paper_sessions(id),
    domain_name VARCHAR(200),
    bounded_context TEXT,
    modules JSONB,
    created_at TIMESTAMP
);
```

### brown_paper_epics
```sql
CREATE TABLE brown_paper_epics (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES brown_paper_sessions(id),
    title VARCHAR(500),
    description TEXT,
    acceptance_criteria JSONB,
    story_points INTEGER,
    priority VARCHAR(10),
    status VARCHAR(20),
    created_at TIMESTAMP
);
```

### deep_extraction
```sql
CREATE TABLE deep_extraction (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES brown_paper_sessions(id),
    extraction_type VARCHAR(50),
    model_responses JSONB,  -- Individual model outputs
    consensus_result JSONB,  -- Final consensus
    confidence_score FLOAT,
    created_at TIMESTAMP
);
```

---

## Dashboards

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| Brown Paper Dashboard | `/brown-paper-dashboard.html` | Session overview, 6-phase progress |
| Deep Extraction | `/deep-extraction.html` | LLM Council results |
| Estimation Dashboard | `/estimation-dashboard.html` | FP/SP analysis |
| Kanban Dashboard | `/kanban-dashboard.html` | Epic/Story management |

---

## Resume Capability

The Brown Paper workflow supports full resume:

1. **Session Status**: `status` field tracks current phase
2. **Phase Caching**: Results stored in `enhanced_analysis` JSONB
3. **Incremental Processing**: Each phase can be re-run independently

**Resume Query**:
```sql
SELECT id, status, enhanced_analysis->>'current_phase' as phase
FROM brown_paper_sessions
WHERE application_id = 'APP-001';
```

---

## Complete API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/brown-paper/sessions` | Start analysis session |
| GET | `/api/brown-paper/sessions/{session_id}` | Get session status |
| POST | `/api/brown-paper/sessions/{session_id}/analyze` | Run basic analysis |
| POST | `/api/brown-paper/sessions/{session_id}/enhanced-analyze` | Run 6-phase analysis |
| GET | `/api/brown-paper/sessions/{session_id}/results` | Get analysis results |
| POST | `/api/brown-paper/sessions/{session_id}/constitution` | Generate constitution |
| POST | `/api/brown-paper/sessions/{session_id}/epics` | Generate epics |
| GET | `/api/brown-paper/sessions/{session_id}/estimation` | Get estimation |

---

## 6-Phase Analysis Pipeline

```
Phase 1: Foundation          Phase 2: Domains           Phase 3: Hierarchy
+-------------------+        +-------------------+      +-------------------+
| - Dependency Graph|   -->  | - Domain Extract  |  --> | - Epic Extraction |
| - Code Metrics    |        | - Bounded Context |      | - Feature Extract |
| - Coupling Score  |        | - Module Mapping  |      | - Story Extract   |
+-------------------+        +-------------------+      +-------------------+
                                                               |
                                                               v
Phase 6: Output              Phase 5: Estimation        Phase 4: Deep Extract
+-------------------+        +-------------------+      +-------------------+
| - Final Report    |   <--  | - IFPUG FP        |  <-- | - LLM Council    |
| - Recommendations |        | - Story Points    |      | - INVEST Valid   |
| - Risk Assessment |        | - Effort Estimate |      | - Consensus      |
+-------------------+        +-------------------+      +-------------------+
```

---

## Workflow Navigation

### Entry Point
- **Dashboard**: `brown-paper-dashboard.html`
- **API**: `POST /api/brown-paper/sessions`

### Output → Next Workflow

| Output | Dashboard | Next Options |
|--------|-----------|--------------|
| Analysis Complete | deep-extraction.html | → MIGRATION (if legacy modernization needed) |
| Estimation Complete | estimation-dashboard.html | → KANBAN (implementation) |
| Epics Generated | kanban-dashboard.html | → KANBAN → MAINTENANCE |

### Typical Flow
```
BROWN_PAPER → MIGRATION (optional) → KANBAN → MAINTENANCE
                                              ↓
                                   ┌──────────┼──────────┐
                                   ↓          ↓          ↓
                                  BUG    NEW_FEATURE  MIGRATION
                                              ↓
                                           KANBAN
```

**Note:** NEW_FEATURE is only accessible from MAINTENANCE phase, not directly from BROWN_PAPER.

---

## Technical Infrastructure

This workflow uses shared infrastructure components. See [99-TECHNICAL-INFRASTRUCTURE.md](./99-TECHNICAL-INFRASTRUCTURE.md) for details.

| Component | Used In Steps |
|-----------|---------------|
| AgentService | 6 (LLM Council), 7 (Eliza), 9 (Peter), 10 (Felix) |
| GraphWorkflowService | 3 (dependency graph), 4 (coupling) |
| ChromaService | Search, embeddings |
| BigAGI | 6 (multi-model consensus) |

---

_See also: [Master Overview](./00-WORKFLOW-MASTER-OVERVIEW.md) | [Green Paper](./01-GREEN-PAPER-WORKFLOW.md) | [Infrastructure](./99-TECHNICAL-INFRASTRUCTURE.md)_
