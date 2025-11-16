# Agent Integration Guide

**Project:** Markdown Task Manager - Agentic System
**Version:** 1.0
**Date:** 2025-11-13
**Status:** Week 5 Day 2 - Integration Planning

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Agent Workflow Patterns](#agent-workflow-patterns)
3. [Work Type Routing](#work-type-routing)
4. [Example Workflows](#example-workflows)
5. [FastAPI Integration](#fastapi-integration)
6. [Environment Setup](#environment-setup)
7. [Testing Strategy](#testing-strategy)

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────┐
│  User Request (Frontend)                                │
│  "Add OAuth2 authentication"                            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  FastAPI Backend                                        │
│  POST /api/workflows/analyze                            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Work Type Router                                       │
│  Classifies: NEW_FEATURE                                │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  KaibanJS Orchestrator                                  │
│  ├─ Create Team with relevant agents                    │
│  ├─ Create Task with description                        │
│  └─ Execute workflow (sequential/parallel)              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Agent Team Execution                                   │
│  ├─ Felix (Feature Architect) - Analyze & breakdown     │
│  ├─ Eliza (Estimation Engine) - Calculate estimates     │
│  ├─ Tessa (Test Engineer) - Generate test plan          │
│  ├─ Quinn (Quality Inspector) - Review design           │
│  └─ Diana (Documentation Writer) - Create docs          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Result Processing                                      │
│  ├─ Store in PostgreSQL (Epic, Features, Stories)       │
│  ├─ Broadcast via WebSocket (real-time updates)         │
│  └─ Return to frontend                                  │
└─────────────────────────────────────────────────────────┘
```

### Component Interaction

```typescript
// 1. User request comes in
POST /api/workflows/analyze
{
  "description": "Add OAuth2 authentication",
  "type": "NEW_FEATURE"
}

// 2. Work Type Router classifies (Week 8)
const workType = classifyWorkType(request)  // -> NEW_FEATURE

// 3. KaibanJS creates appropriate team
const team = createTeamForWorkType(workType)
// team = [Felix, Eliza, Tessa, Quinn, Diana]

// 4. Create and execute task
const task = new Task({
  description: request.description,
  expectedOutput: "Complete work breakdown with estimates"
})

const result = await team.start(task)

// 5. Store and return result
await storeInDatabase(result)
await broadcastViaWebSocket(result)
return result
```

---

## Agent Workflow Patterns

### Pattern 1: Sequential Workflow

**Use case:** Each agent needs previous agent's output

```typescript
// Example: NEW_FEATURE workflow
const sequentialTeam = new Team({
  name: 'Feature Analysis Team',
  agents: [
    agents.featureArchitect,      // 1. Analyze & breakdown
    agents.estimationEngine,       // 2. Calculate estimates
    agents.testEngineer,           // 3. Generate tests
    agents.qualityInspector,       // 4. Review quality
    agents.documentationWriter     // 5. Create docs
  ],
  tasks: [task],
  process: 'sequential'  // One at a time, in order
})

await sequentialTeam.start()
```

**Execution:**
```
Felix → Eliza → Tessa → Quinn → Diana
  |       |       |       |       |
  v       v       v       v       v
Spec  Estimates Tests  Review  Docs
```

### Pattern 2: Parallel Workflow

**Use case:** Multiple independent analyses

```typescript
// Example: QUALITY_AUDIT workflow
const parallelTeam = new Team({
  name: 'Quality Audit Team',
  agents: [
    agents.qualityInspector,       // Security audit
    agents.maintenanceSpecialist,  // Tech debt scan
    agents.testEngineer            // Coverage analysis
  ],
  tasks: [auditTask],
  process: 'parallel'  // All at same time
})

await parallelTeam.start()
```

**Execution:**
```
        Quinn (Security)
        /
Input →  Marcus (Tech Debt)  → Aggregate Results
        \
        Tessa (Coverage)
```

### Pattern 3: Hybrid Workflow

**Use case:** Some parallel, then sequential

```typescript
// Example: MIGRATION workflow
const hybridWorkflow = async (migrationRequest) => {
  // Phase 1: Parallel assessment
  const assessmentTeam = new Team({
    agents: [
      agents.migrationArchitect,     // Migration planning
      agents.qualityInspector,       // Risk assessment
      agents.estimationEngine        // Effort estimation
    ],
    process: 'parallel'
  })

  const assessment = await assessmentTeam.start(assessmentTask)

  // Phase 2: Sequential execution
  const executionTeam = new Team({
    agents: [
      agents.migrationArchitect,     // Execute migration
      agents.testEngineer,           // Validate migration
      agents.documentationWriter     // Document changes
    ],
    process: 'sequential'
  })

  const result = await executionTeam.start(executionTask)
  return result
}
```

---

## Work Type Routing

### Work Type → Agent Team Mapping

```typescript
const WORK_TYPE_TEAMS = {
  NEW_FEATURE: {
    agents: ['featureArchitect', 'estimationEngine', 'testEngineer', 'qualityInspector', 'documentationWriter'],
    process: 'sequential',
    workflow: 'spec_kit_pipeline'
  },

  MAINTENANCE: {
    agents: ['maintenanceSpecialist', 'qualityInspector', 'testEngineer', 'estimationEngine'],
    process: 'sequential',
    workflow: 'code_maintenance_6_stage'
  },

  QUALITY_AUDIT: {
    agents: ['qualityInspector', 'maintenanceSpecialist', 'testEngineer'],
    process: 'parallel',
    workflow: 'superclaude_audit'
  },

  BUG: {
    agents: ['bugHunter', 'testEngineer', 'documentationWriter'],
    process: 'sequential',
    workflow: 'bug_fix_5_stage'
  },

  ENHANCEMENT: {
    agents: ['featureArchitect', 'maintenanceSpecialist', 'estimationEngine', 'testEngineer'],
    process: 'sequential',
    workflow: 'enhancement_hybrid'
  },

  MIGRATION: {
    agents: ['migrationArchitect', 'qualityInspector', 'estimationEngine', 'testEngineer', 'documentationWriter'],
    process: 'hybrid',  // Parallel assessment, then sequential execution
    workflow: 'migration_5_stage'
  },

  QUALITY_IMPROVEMENT: {
    agents: ['qualityInspector', 'maintenanceSpecialist', 'testEngineer', 'estimationEngine'],
    process: 'sequential',
    workflow: 'quality_improvement_5_stage'
  },

  TESTING: {
    agents: ['testEngineer', 'qualityInspector', 'documentationWriter'],
    process: 'sequential',
    workflow: 'test_generation_4_track'
  }
}

function createTeamForWorkType(workType: string) {
  const config = WORK_TYPE_TEAMS[workType]
  const agentInstances = config.agents.map(name => agents[name])

  return new Team({
    name: `${workType} Team`,
    agents: agentInstances,
    process: config.process
  })
}
```

---

## Example Workflows

### Example 1: NEW_FEATURE - OAuth2 Authentication

```typescript
import { agents, createTeamForWorkType } from './backend/agents'
import { Task } from 'kaibanjs'

async function analyzeNewFeature(description: string) {
  // 1. Create team
  const team = createTeamForWorkType('NEW_FEATURE')

  // 2. Create task
  const task = new Task({
    description: `Analyze and break down this feature: ${description}`,
    expectedOutput: `
      - Complete work breakdown (Epic → Features → Stories → Tasks)
      - Story point estimates for all items
      - Test strategy with coverage plan
      - Quality review findings
      - Technical documentation
    `
  })

  // 3. Execute (sequential)
  console.log('Starting feature analysis...')
  const result = await team.start(task)

  // 4. Extract outputs
  return {
    workBreakdown: result.agents.featureArchitect.output,
    estimates: result.agents.estimationEngine.output,
    testPlan: result.agents.testEngineer.output,
    qualityReview: result.agents.qualityInspector.output,
    documentation: result.agents.documentationWriter.output
  }
}

// Usage
const result = await analyzeNewFeature('Add OAuth2 authentication with Google, GitHub, Microsoft')
```

### Example 2: BUG - Login 500 Error

```typescript
async function analyzeBug(bugReport: BugReport) {
  const team = new Team({
    agents: [
      agents.bugHunter,
      agents.testEngineer,
      agents.documentationWriter
    ],
    process: 'sequential'
  })

  const task = new Task({
    description: `
      Bug Report:
      Title: ${bugReport.title}
      Steps: ${bugReport.reproduction_steps.join('\n')}
      Stack Trace: ${bugReport.stack_trace}

      Please:
      1. Identify root cause
      2. Suggest fix with code changes
      3. Create regression test
      4. Document the fix
    `,
    expectedOutput: 'Root cause analysis, fix implementation, test, documentation'
  })

  const result = await team.start(task)

  return {
    rootCause: result.agents.bugHunter.output.root_cause,
    fix: result.agents.bugHunter.output.fix,
    test: result.agents.testEngineer.output.regression_test,
    documentation: result.agents.documentationWriter.output
  }
}
```

### Example 3: QUALITY_AUDIT - Pre-Release Check

```typescript
async function runQualityAudit(scope: string) {
  // Parallel execution for speed
  const team = new Team({
    agents: [
      agents.qualityInspector,
      agents.maintenanceSpecialist,
      agents.testEngineer
    ],
    process: 'parallel'
  })

  const task = new Task({
    description: `Audit ${scope} for:
      - Security vulnerabilities (OWASP)
      - Performance issues
      - Code quality (complexity, duplication)
      - Technical debt
      - Test coverage gaps
    `,
    expectedOutput: 'Comprehensive quality report'
  })

  const result = await team.start(task)

  // Aggregate parallel results
  return {
    securityFindings: result.agents.qualityInspector.output.security,
    performanceFindings: result.agents.qualityInspector.output.performance,
    technicalDebt: result.agents.maintenanceSpecialist.output,
    testCoverage: result.agents.testEngineer.output
  }
}
```

---

## FastAPI Integration

### Backend Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── workflows.py      # NEW: Agent workflow endpoints
│   │   ├── agents.py          # NEW: Agent management
│   │   └── sprints.py         # Existing
│   ├── services/
│   │   ├── agent_service.py   # NEW: Agent orchestration
│   │   └── work_type_router.py # NEW: Work type classification
│   └── main.py
└── agents/                     # KaibanJS TypeScript
    ├── configs/
    ├── workflows/
    └── index.ts
```

### API Endpoints (Week 5 Day 4)

```python
# backend/app/api/workflows.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.agent_service import AgentService

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

class WorkflowRequest(BaseModel):
    description: str
    work_type: str
    context: dict = {}

@router.post("/analyze")
async def analyze_workflow(request: WorkflowRequest):
    """
    Analyze work request using appropriate agent team
    """
    try:
        agent_service = AgentService()
        result = await agent_service.execute_workflow(
            work_type=request.work_type,
            description=request.description,
            context=request.context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/work-types")
async def get_work_types():
    """
    Get available work types
    """
    return {
        "work_types": [
            "NEW_FEATURE",
            "MAINTENANCE",
            "QUALITY_AUDIT",
            "BUG",
            "ENHANCEMENT",
            "MIGRATION",
            "QUALITY_IMPROVEMENT",
            "TESTING"
        ]
    }

@router.get("/agents")
async def get_agents():
    """
    Get available agents and their status
    """
    agent_service = AgentService()
    return agent_service.get_agent_status()
```

### Agent Service (Python ↔ TypeScript Bridge)

```python
# backend/app/services/agent_service.py
import subprocess
import json
from typing import Dict, Any

class AgentService:
    def __init__(self):
        self.agents_path = "backend/agents"

    async def execute_workflow(
        self,
        work_type: str,
        description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute agent workflow by calling TypeScript via subprocess
        """

        # Prepare input
        input_data = {
            "work_type": work_type,
            "description": description,
            "context": context
        }

        # Call TypeScript agent system
        process = subprocess.Popen(
            ['node', f'{self.agents_path}/dist/index.js'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(input=json.dumps(input_data))

        if process.returncode != 0:
            raise Exception(f"Agent execution failed: {stderr}")

        # Parse result
        result = json.loads(stdout)
        return result

    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of all agents
        """
        # TODO: Implement agent health check
        return {
            "agents": [
                {"name": "Felix", "status": "ready", "provider": "claude"},
                {"name": "Marcus", "status": "ready", "provider": "ollama"},
                {"name": "Quinn", "status": "ready", "provider": "claude"},
                {"name": "Betty", "status": "ready", "provider": "ollama"},
                {"name": "Eliza", "status": "ready", "provider": "ollama"},
                {"name": "Tessa", "status": "ready", "provider": "ollama"},
                {"name": "Miguel", "status": "ready", "provider": "openai"},
                {"name": "Diana", "status": "ready", "provider": "ollama"}
            ]
        }
```

### Alternative: Celery Task Queue (Recommended for Production)

```python
# backend/app/tasks/agent_tasks.py
from celery import Celery
import subprocess
import json

celery_app = Celery('tasks', broker='redis://localhost:6379/0')

@celery_app.task
def execute_agent_workflow(work_type: str, description: str, context: dict):
    """
    Execute agent workflow as async Celery task
    """
    # Call TypeScript agents
    process = subprocess.Popen(
        ['node', 'backend/agents/dist/index.js'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )

    input_data = json.dumps({
        "work_type": work_type,
        "description": description,
        "context": context
    })

    stdout, _ = process.communicate(input=input_data)
    result = json.loads(stdout)

    return result

# Usage in API
@router.post("/analyze-async")
async def analyze_workflow_async(request: WorkflowRequest):
    """
    Analyze work request asynchronously
    """
    task = execute_agent_workflow.delay(
        work_type=request.work_type,
        description=request.description,
        context=request.context
    )

    return {
        "task_id": task.id,
        "status": "processing"
    }

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Get async task status
    """
    task = celery_app.AsyncResult(task_id)

    if task.ready():
        return {
            "status": "completed",
            "result": task.result
        }
    else:
        return {
            "status": "processing"
        }
```

---

## Environment Setup

### Required Environment Variables

```bash
# .env file (backend/agents/.env)

# Cloud LLM API Keys
ANTHROPIC_API_KEY=sk-ant-xxx...
OPENAI_API_KEY=sk-xxx...

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Model Selection (can be changed per agent)
CLAUDE_MODEL=claude-sonnet-4-5
GPT4_MODEL=gpt-4-turbo
OLLAMA_MODEL=llama3.1:8b

# Agent Configuration
AGENT_TIMEOUT=300  # seconds
AGENT_MAX_RETRIES=3
```

### Installation Steps

```bash
# 1. Install Node dependencies
cd backend/agents
npm install

# 2. Build TypeScript
npm run build

# 3. Setup Python dependencies (for FastAPI integration)
cd ../..
pip install celery redis

# 4. Start Redis (for Celery)
docker run -d -p 6379:6379 redis:alpine

# 5. Start Celery worker
celery -A app.tasks.agent_tasks worker --loglevel=info

# 6. Verify Ollama is running
ollama list
# Should show: llama3.1:8b (will download when home)
```

---

## Testing Strategy

### Unit Tests

```typescript
// backend/agents/tests/agents.test.ts
import { agents } from '../configs/agents'

describe('Agent Configuration', () => {
  test('All agents are properly configured', () => {
    expect(agents.featureArchitect).toBeDefined()
    expect(agents.featureArchitect.name).toBe('Felix')
    expect(agents.featureArchitect.llmConfig.provider).toBe('anthropic')
  })

  test('Local agents use Ollama', () => {
    expect(agents.maintenanceSpecialist.llmConfig.provider).toBe('ollama')
    expect(agents.bugHunter.llmConfig.provider).toBe('ollama')
  })
})
```

### Integration Tests

```python
# backend/tests/test_agent_service.py
import pytest
from app.services.agent_service import AgentService

@pytest.mark.asyncio
async def test_execute_new_feature_workflow():
    service = AgentService()
    result = await service.execute_workflow(
        work_type="NEW_FEATURE",
        description="Add user login",
        context={}
    )

    assert result is not None
    assert 'workBreakdown' in result
    assert 'estimates' in result
```

### End-to-End Tests

```python
# Test complete flow: API → Agents → Database
@pytest.mark.asyncio
async def test_complete_feature_analysis_flow(client):
    response = await client.post("/api/workflows/analyze", json={
        "work_type": "NEW_FEATURE",
        "description": "Add OAuth2 authentication",
        "context": {}
    })

    assert response.status_code == 200
    data = response.json()

    # Verify Epic was created
    epic = await get_epic_by_id(data['epic']['id'])
    assert epic is not None
    assert epic.title == "OAuth2 Authentication System"
```

---

## Performance Considerations

### Execution Time Estimates

| Work Type | Agent Count | Process | Estimated Time |
|-----------|-------------|---------|----------------|
| NEW_FEATURE | 5 agents | Sequential | 2-5 minutes |
| MAINTENANCE | 4 agents | Sequential | 1-3 minutes |
| QUALITY_AUDIT | 3 agents | Parallel | 1-2 minutes |
| BUG | 3 agents | Sequential | 1-2 minutes |
| MIGRATION | 5 agents | Hybrid | 3-7 minutes |

### Optimization Strategies

1. **Use Local LLMs for bulk work** (70% of tasks)
   - Faster (no network latency)
   - Cheaper (no API costs)
   - Privacy (data stays local)

2. **Parallel execution when possible**
   - Quality audits
   - Multi-dimensional analysis

3. **Caching agent outputs**
   - Cache similar feature analyses
   - Reuse estimation models

4. **Async task queue (Celery)**
   - Non-blocking API responses
   - Better scalability
   - Retry capability

---

## Troubleshooting

### Common Issues

**Issue 1: Ollama not responding**
```bash
# Check Ollama status
systemctl status ollama

# Restart Ollama
systemctl restart ollama

# Test connection
curl http://localhost:11434/api/version
```

**Issue 2: TypeScript compilation errors**
```bash
# Clean build
cd backend/agents
rm -rf dist/
npm run build
```

**Issue 3: Agent timeout**
```bash
# Increase timeout in .env
AGENT_TIMEOUT=600  # 10 minutes
```

**Issue 4: API key not found**
```bash
# Verify .env file
cat backend/agents/.env | grep API_KEY

# Reload environment
source backend/agents/.env
```

---

## Next Steps

### Week 5 Day 3 (Tomorrow)
- Implement KaibanBoard configuration
- Create task routing logic
- Test sequential workflow

### Week 5 Day 4 (Thursday)
- Create FastAPI endpoints
- Setup Celery + Redis
- Test Python ↔ TypeScript bridge

### Week 5 Day 5 (Friday)
- Write integration tests
- Document workflows
- Sprint review & demo

### When Home (Better Network)
- Download Llama 3.1 8B: `ollama pull llama3.1:8b`
- Test all local agents
- Benchmark performance

---

**Document Version:** 1.0
**Last Updated:** 2025-11-13
**Status:** Complete - Ready for Day 3
