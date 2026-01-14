# Technical Infrastructure

## Overview

This document describes the shared technical infrastructure used by all workflows. Changes here affect multiple workflows - update once, apply everywhere.

---

## Core Services

### AgentService
**Purpose**: Python→LLM bridge for all agent execution

```python
# Used by all workflows that invoke agents
response = await agent_service.execute_agent(
    agent_name="Peter",
    prompt=constitution_prompt,
    model="deepseek-r1:latest"
)
```

| Method | Purpose | Used By |
|--------|---------|---------|
| `execute_agent()` | Execute named agent with prompt | GREEN_PAPER, BROWN_PAPER, Migration, all |
| `generate_with_model()` | Direct LLM call | Deep Extraction, Estimation |

**DB Table**: `workflow_executions` (execution logs)

---

### GraphWorkflowService
**Purpose**: Code dependency analysis and impact assessment

| Method | Purpose | Used By |
|--------|---------|---------|
| `analyze_impact()` | Find affected files for change | MAINTENANCE, NEW_FEATURE |
| `get_coupling()` | Calculate coupling score | BROWN_PAPER Phase 1 |
| `build_dependency_graph()` | Create file dependency map | BROWN_PAPER Phase 1 |

**DB Table**: `code_graph`

---

### CCPMWorkflowIntegrationService
**Purpose**: Git worktree isolation for parallel development

| Method | Purpose | Used By |
|--------|---------|---------|
| `create_worktree()` | Isolated branch workspace | All implementation workflows |
| `merge_worktree()` | Merge back to main | All implementation workflows |

**DB Table**: `ccpm`

---

### WorkflowToolIntegrationService
**Purpose**: External tool integrations

| Integration | Tools | Purpose | Used By |
|-------------|-------|---------|---------|
| Claude-Mem | Memory API | Agent session memory | All agent workflows |
| BigAGI | Beam validation | Multi-model consensus | BROWN_PAPER Phase 4 |
| GhostCrew | Security scans | Vulnerability detection | GREEN_PAPER, QUALITY_AUDIT |

**DB Tables**: `claude_mem`, `ghostcrew_results`

---

### ChromaService
**Purpose**: Vector database for semantic search

| Method | Purpose | Used By |
|--------|---------|---------|
| `store_embeddings()` | Store document vectors | GREEN_PAPER (constitution) |
| `search_similar()` | Find similar projects | GREEN_PAPER, BROWN_PAPER |

**DB**: ChromaDB (external, port 8001)

---

## Infrastructure per Workflow

| Workflow | AgentService | GraphWorkflow | CCPM | ChromaService | External Tools |
|----------|:------------:|:-------------:|:----:|:-------------:|:--------------:|
| GREEN_PAPER | ✓ | - | - | ✓ | GhostCrew, BigAGI |
| BROWN_PAPER | ✓ | ✓ | - | ✓ | BigAGI (Council) |
| Migration | ✓ | ✓ | - | - | - |
| NEW_FEATURE | ✓ | ✓ | ✓ | - | GhostCrew |
| MAINTENANCE | ✓ | ✓ | ✓ | - | - |
| BUG | ✓ | - | ✓ | - | - |
| QUALITY_AUDIT | ✓ | ✓ | - | - | GhostCrew |

---

## Agent Execution Flow

```
Workflow Step (e.g., "Generate Constitution")
                |
                v
+-------------------------------+
| Service Layer                 |
| (GreenPaperService, etc.)     |
+---------------+---------------+
                |
                v
+-------------------------------+
| AgentService                  |  <-- THIS DOCUMENT
| execute_agent(name, prompt)   |
+---------------+---------------+
                |
      +---------+---------+
      |                   |
      v                   v
+----------+      +---------------+
| Ollama   |      | External Tools|
| (LLM)    |      | (optional)    |
+----------+      +---------------+
      |                   |
      +---------+---------+
                |
                v
+-------------------------------+
| Response + DB Persistence     |
+-------------------------------+
```

---

## Configuration

| Component | Config Location | Default |
|-----------|-----------------|---------|
| Ollama URL | `OLLAMA_URL` env | http://localhost:11434 |
| ChromaDB URL | `CHROMA_URL` env | http://localhost:8001 |
| Default Model | `DEFAULT_LLM` env | deepseek-r1:latest |

---

## Related Documents

Referenced by:
- [01-GREEN-PAPER-WORKFLOW.md](./01-GREEN-PAPER-WORKFLOW.md) - Steps 3, 5, 6
- [02-BROWN-PAPER-WORKFLOW.md](./02-BROWN-PAPER-WORKFLOW.md) - Steps 3-10
- [03-MIGRATION-WORKFLOW.md](./03-MIGRATION-WORKFLOW.md) - Steps 2-14
- [04-QUALITY-TREND-WORKFLOW.md](./04-QUALITY-TREND-WORKFLOW.md) - Steps 2-4
- [05-NEW-FEATURE-WORKFLOW.md](./05-NEW-FEATURE-WORKFLOW.md) - Steps 2-5
- [06-MAINTENANCE-DEBUG-WORKFLOWS.md](./06-MAINTENANCE-DEBUG-WORKFLOWS.md) - All agent steps
- [00-WORKFLOW-MASTER-OVERVIEW.md](./00-WORKFLOW-MASTER-OVERVIEW.md) - Overview document

---

_Infrastructure changes affect all workflows - test thoroughly before deployment._
