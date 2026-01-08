# Multi-Stack Platform Architecture

**Status:** Week 54-58 PLANNED
**Vision:** Transform single-project system into multi-stack platform
**Impact:** Support multiple projects with different tech-stacks

---

## Design Filosofie

**"One Platform, Many Stacks"** - The platform must:
1. Support multiple projects simultaneously
2. Provide stack-specific agents for each technology
3. Monitor agent behavior and decisions (observability)
4. Continuously improve prompts (meta-prompting)
5. Route tasks to optimal models (cost/quality balance)

---

## Architecture Overview

```
+---------------------------------------------------------------------+
|                    MULTI-STACK PLATFORM                              |
|                                                                      |
|  +---------------------------------------------------------------+  |
|  |              LAAG 1: CORE AGENTS (10 - Cross-Stack)            |  |
|  |                                                                |  |
|  |  Felix (Architecture)     Quinn (Quality)      Betty (Bugs)    |  |
|  |  Eliza (Estimation)       Diana (Docs)         Marcus (Maint)  |  |
|  |  Tessa (Testing)          Miguel (Migration)   Peter (PO)      |  |
|  |  Paul (Project Lead)                                           |  |
|  +---------------------------------------------------------------+  |
|                              |                                       |
|  +---------------------------------------------------------------+  |
|  |         LAAG 2: STACK AGENT TEMPLATES (Per Project)            |  |
|  |                                                                |  |
|  |  Python:      BackendDev_py, CodeRev_py, SecAudit_py,         |  |
|  |               Tester_py                                        |  |
|  |                                                                |  |
|  |  JavaScript:  BackendDev_js, FrontendDev_js, CodeRev_js,      |  |
|  |               SecAudit_js, Tester_js                           |  |
|  |                                                                |  |
|  |  Go:          BackendDev_go, CodeRev_go, SecAudit_go,         |  |
|  |               Tester_go                                        |  |
|  |                                                                |  |
|  |  Rust:        BackendDev_rs, CodeRev_rs, SecAudit_rs,         |  |
|  |               Tester_rs                                        |  |
|  +---------------------------------------------------------------+  |
|                              |                                       |
|  +---------------------------------------------------------------+  |
|  |           LAAG 3: PLATFORM AGENTS (Meta-niveau)                |  |
|  |                                                                |  |
|  |  ObservabilityEngineer    - Agent behavior monitoring          |  |
|  |  PromptEngineer           - Meta-prompting, optimization       |  |
|  |  IncidentResponder        - Cross-project incident handling    |  |
|  |  ContextManager           - Cross-agent state management       |  |
|  +---------------------------------------------------------------+  |
|                              |                                       |
|  +---------------------------------------------------------------+  |
|  |              PROVIDER REGISTRY (Multi-LLM Routing)             |  |
|  |                                                                |  |
|  |  Ollama (Local):  qwen2.5-coder, deepseek-r1, codellama       |  |
|  |  Claude CLI:      Haiku (fast), Sonnet (balanced), Opus       |  |
|  +---------------------------------------------------------------+  |
+---------------------------------------------------------------------+
```

---

## Provider Registry (Multi-LLM Abstractie)

### LLM Provider Model

```python
class LLMProvider(BaseModel):
    id: UUID
    name: str                    # "ollama", "claude", "openai"
    tier: str                    # "free", "fast", "balanced", "deep"
    cost_input_per_m: float      # Cost per million input tokens
    cost_output_per_m: float     # Cost per million output tokens
    is_active: bool
    config: Dict[str, Any]       # Model-specific settings
    created_at: datetime

# Database table
CREATE TABLE llm_providers (
    id UUID PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    tier VARCHAR(20) NOT NULL,
    cost_input_per_m DECIMAL(10,4),
    cost_output_per_m DECIMAL(10,4),
    is_active BOOLEAN DEFAULT true,
    config JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Model Routing Strategy

| Model | Tier | Cost (Input/Output) | Use Case |
|-------|------|---------------------|----------|
| Ollama (local) | Free | $0 / $0 | Simple tasks, privacy, offline |
| Claude Haiku | Fast | $1 / $5 per M | Quick fixes, bulk generation |
| Claude Sonnet | Balanced | $3 / $15 per M | Daily work, most tasks |
| Claude Opus | Deep | $15 / $75 per M | Architecture, security, complex |

```python
# Task-to-Model Router
class ModelRouter:
    TASK_ROUTING = {
        "simple_generation": "ollama/qwen2.5-coder:7b",
        "quick_fix": "claude/haiku",
        "code_review": "claude/sonnet",
        "standard_work": "claude/sonnet",
        "architecture": "claude/opus",
        "security_audit": "claude/opus",
        "complex_analysis": "claude/opus",
    }

    async def route(self, task: Task, budget: Budget = None) -> str:
        """Route task to optimal model based on complexity and budget."""
        base_model = self.TASK_ROUTING.get(task.type, "claude/sonnet")

        if budget and budget.remaining < self.get_cost(base_model):
            return self._downgrade_model(base_model)

        return base_model
```

---

## Stack Agent Factory

### Template-Based Instantiation

```python
# Stack Agent Templates
STACK_TEMPLATES = {
    "BackendDev": {
        "python": {
            "prompt_additions": "Expert in FastAPI, Django, SQLAlchemy, SOLID principles",
            "model_preference": "qwen2.5-coder:7b",
            "capabilities": ["api_design", "database", "async", "testing"],
        },
        "javascript": {
            "prompt_additions": "Expert in Node.js, Express, TypeORM, ES6+",
            "model_preference": "qwen2.5-coder:7b",
            "capabilities": ["api_design", "database", "async", "testing"],
        },
        "go": {
            "prompt_additions": "Expert in Go, Gin, GORM, goroutines",
            "model_preference": "deepseek-coder",
            "capabilities": ["api_design", "database", "concurrency", "testing"],
        },
    },
    "CodeReviewer": {
        "python": {
            "prompt_additions": "PEP8, mypy, black, pytest, security focus",
            "model_preference": "deepseek-r1",
            "capabilities": ["code_quality", "security", "performance"],
        },
        # ... other stacks
    },
    # ... other roles
}

class StackAgentFactory:
    def create_agent(self, stack: str, role: str, project_id: UUID) -> StackAgent:
        """Create stack-specific agent from template."""
        template = STACK_TEMPLATES[role][stack]

        return StackAgent(
            name=f"{role}_{stack}",
            stack=stack,
            project_id=project_id,
            base_prompt=self._build_prompt(role, template),
            model=template["model_preference"],
            capabilities=template["capabilities"],
        )
```

### Stack Detection

```python
class StackDetector:
    """Detect project tech-stack from files and configuration."""

    INDICATORS = {
        "python": ["requirements.txt", "pyproject.toml", "setup.py", "*.py"],
        "javascript": ["package.json", "*.js", "*.ts", "node_modules"],
        "go": ["go.mod", "go.sum", "*.go"],
        "rust": ["Cargo.toml", "*.rs"],
    }

    async def detect(self, project_path: str) -> List[str]:
        """Return list of detected stacks in order of confidence."""
        scores = {}
        for stack, indicators in self.INDICATORS.items():
            score = await self._calculate_score(project_path, indicators)
            if score > 0:
                scores[stack] = score

        return sorted(scores.keys(), key=lambda s: scores[s], reverse=True)
```

---

## Observability System (Agent Behavior Monitoring)

### Purpose

Monitor what agents do, why they make decisions, and how well they perform.

### Database Schema

```sql
-- Agent action logging
CREATE TABLE agent_actions (
    id SERIAL PRIMARY KEY,
    task_id UUID NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    input_summary TEXT,
    output_summary TEXT,
    decision_rationale TEXT,
    model_used VARCHAR(50),
    token_input INTEGER,
    token_output INTEGER,
    duration_ms INTEGER,
    success BOOLEAN,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Decision tracing
CREATE TABLE decision_traces (
    id SERIAL PRIMARY KEY,
    task_id UUID NOT NULL,
    sequence_number INTEGER NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    decision_point VARCHAR(100),
    options JSONB,
    selected_option VARCHAR(100),
    selection_rationale TEXT,
    outcome VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Daily performance aggregates
CREATE TABLE agent_performance_daily (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    total_actions INTEGER,
    successful_actions INTEGER,
    avg_duration_ms INTEGER,
    total_tokens INTEGER,
    total_cost_cents INTEGER,
    UNIQUE(agent_id, date)
);
```

### Observability Dashboard

**Features:**
- Real-time agent activity stream
- Decision trace visualization
- Performance metrics per agent
- Cost tracking and budget alerts
- Pattern detection (successful vs failed approaches)

### API Endpoints

```
GET  /api/observability/actions                 # Recent agent actions
GET  /api/observability/actions/{agent_id}      # Agent-specific actions
GET  /api/observability/decisions/{task_id}     # Decision trace for task
GET  /api/observability/performance/daily       # Daily aggregates
GET  /api/observability/performance/{agent_id}  # Agent performance
GET  /api/observability/patterns                # Detected patterns
POST /api/observability/actions                 # Log new action
POST /api/observability/decisions               # Log decision point
```

---

## PromptEngineer + Meta-Prompting

### Purpose

Continuously improve agent prompts based on performance data.

### Meta-Prompting Flow

```
Task Arrival -> PromptEngineer Intercept -> Enhanced Prompt -> Execute -> Feedback Loop
```

### Implementation

```python
class PromptEngineer:
    """Continuous improvement of agent prompts via meta-prompting."""

    async def intercept_task(self, task: Task, agent: Agent) -> EnhancedPrompt:
        """Enhance prompt based on context and historical performance."""
        # Get agent's recent performance
        metrics = await self.get_agent_metrics(agent.id)

        # Get relevant patterns from experience store
        patterns = await self.get_successful_patterns(agent.id, task.context)

        # Generate enhanced prompt
        enhanced = await self.enhance_prompt(
            original_prompt=agent.base_prompt,
            task_context=task.context,
            performance_insights=metrics,
            proven_patterns=patterns,
        )

        return enhanced

    async def evaluate_and_update(self, task_result: TaskResult):
        """A/B test prompt variations and roll out improvements."""
        if task_result.success:
            await self.store_successful_pattern(task_result)
        else:
            await self.analyze_failure(task_result)

    async def run_prompt_ab_test(self, agent_id: str, variations: List[str]):
        """A/B test different prompt variations."""
        experiment = await self.ab_service.create_experiment(
            agent_id=agent_id,
            feature_name="prompt_variation",
            variants=[
                {"name": "control", "prompt": variations[0], "is_control": True},
                {"name": "treatment", "prompt": variations[1], "is_control": False},
            ]
        )
        return experiment
```

### Prompt Optimization Triggers

| Trigger | Action |
|---------|--------|
| Agent success rate < 70% | Analyze failures, suggest improvements |
| New successful pattern detected | Update prompt template |
| Consistent feedback pattern | Add clarification to prompt |
| High token usage | Optimize prompt for conciseness |

---

## Betty Enhancement (ErrorDetective Merge)

### New Capabilities

```python
class EnhancedBetty(BugHunter):
    """Betty + ErrorDetective capabilities."""

    # Original Betty capabilities
    async def reproduce_bug(self, bug: Bug) -> ReproductionResult: ...
    async def find_root_cause(self, bug: Bug) -> RootCause: ...
    async def suggest_fix(self, root_cause: RootCause) -> Fix: ...

    # NEW: ErrorDetective capabilities
    async def debug_distributed_system(self, traces: List[Trace]) -> DistributedDebugResult:
        """Debug across multiple services."""
        ...

    async def analyze_cascading_failure(self, failure: Failure) -> CascadeAnalysis:
        """Find source of cascading failures."""
        ...

    async def aggregate_logs(self, log_sources: List[LogSource]) -> AggregatedLogs:
        """Aggregate logs from multiple sources."""
        ...

    async def temporal_analysis(self, events: List[Event]) -> TemporalAnalysis:
        """Analyze time-based patterns in errors."""
        ...

    async def cross_service_correlation(self, error: Error) -> CorrelationResult:
        """Correlate error across services."""
        ...

    async def detect_anomaly(self, metrics: Metrics) -> AnomalyDetection:
        """Detect anomalous behavior patterns."""
        ...
```

---

## Implementation Roadmap

### Week 54-55: Foundation
- Provider Registry implementation
- Claude CLI Integration
- Model Router
- Database migrations (4 tables)
- Basic Observability
- Observability Dashboard
- Betty Enhancement (+ ErrorDetective)
- Quinn Enhancement (+ 3-phase methodology)
- Standards System

### Week 56-57: Stack Support
- Stack Agent Factory
- Python Stack Agents
- JavaScript Stack Agents
- Stack Detection
- PromptEngineer Agent
- Prompt A/B Testing
- Integration Testing

### Week 58: Polish
- Cost Tracking
- Performance Optimization
- Documentation
- Go-Live Prep

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Stack template complexity | High | Start with 2 stacks, grow organically |
| Observability overhead | Medium | Configurable log level |
| Meta-prompting latency | Medium | Cache enhanced prompts |
| Claude costs | High | Strict budget controls, Ollama fallback |

---

**Related Documents:**
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - Main architecture overview
- [Self-Evolution Layer](./self-evolution.md) - Agent learning
- [A/B Testing Framework](./ab-testing.md) - Experimentation
- [LLM Council](./llm-council.md) - Multi-model decisions
